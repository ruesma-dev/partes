<!-- specs/F-031-asiento-analitico/design.md -->
# F-031 · Diseño técnico

Datos (solo lectura, agregados): `progress/spec_F-031.md`, anexo §D1–§D10.
Versión 3 (2026-10-05): DA6 según la aclaración del humano (§8).

## 1. Cómo contabiliza Sigrid un parte (lo que NO hay que construir)

Estados del parte (tipo 35): 1 En registro, 3 Cerrado, 10 Imputado.
«Contabilizar parte» (Administración, por lotes) lo pone en Imputado y crea
**un** asiento analítico (tipo 32, mismo resumen y fecha): Debe = Σ
`hmores.tot` por `hmores.caaide` (las de 0 no entran), Haber por
`res.caaconide` (§D2–§D4). «Contabilizar» se puede deshacer (humano): así se
**reabre** un parte. Falla **dónde** escribe sv5 (`partes_existentes` no
mira `con.est`) y **qué cuenta** pone (F-021: la del recurso; DA6).

## 2. La partida y el árbol analítico (dato para DA6, §D9–§D10)

- Árbol del centro (`cag`): `C` → `CD`, `CI` (… **CIMO mano de obra
  indirecta** …), `CP`; `I` → `IN` (`INGR..`). La rama de una cuenta es su
  grupo de nivel 2; **cuenta de coste** = rama `CD`, `CI` o `CP`.
- `obrparpar.caaide` es la **única** cuenta analítica de la partida: ni
  `proide`→`pro.gaside`, ni `parcoside`, ni `cosindide`, ni capítulos padre
  ni `cen.gaside` dan otra en las partidas con horas (§D10).
- Líneas 2026 (empresa 1) por partida: CI con cuenta CI 18.595; CI sin
  cuenta 2.811; CD sin cuenta 1.404 o solo `INGR` 575; CP (`CP00..`) 562,
  tecleadas en Sigrid (sv3 y el portal sugieren CI/CD; a mano, cualquiera).

Regla (DA6): **cuenta de coste de la partida ⇒ esa**; sin ella, DA6-e (R18).

## 3–4. Servicios, encaje y límite (ningún paso nuevo fuera de sv5)

- **sv5**: única escritora; elige parte y cuenta. Lee la partida en Sigrid
  (no se fía del portal, como F-023) por un campo estructural (rama `cag`
  de su cuenta): no copia el clasificador de `partida_catalog.py`.
  `preparar` (fuera del lock): paso 4b de F-021 + partidas. `_evaluar`
  (dentro del lock): paso 5 con estado y paso 6 bis nuevo.
- **sv4**: solo pinta `partes[].aviso` y `caa_nota`. Ni sv3, ni base
  `partes`, ni ORM, ni sigrid-api, ni servicio nuevo (DA1, DA4).

## 5. Ficheros a crear

- `services/partes-transfer/application/services/estado_parte.py` (§7.1) y
  `services/partes-transfer/comprobar_asiento_analitico.py` (§7.5).
- Tests en `services/partes-transfer/tests/`: `test_f031_{estado_parte,
  cuenta_partida,pipeline_estado,pipeline_cuenta_partida,cliente_partes,
  comprobar_asiento}.py`; sv4: `tests/test_f031_preflight_avisos.py`.

## 6. Ficheros a modificar

- `services/partes-transfer/domain/models/registro_models.py`: `ParteSigrid`
  (frozen: `ide`, `cod`, `est`); `PartidaCuenta` (frozen: `ide`, `cod`,
  `caa_cod`, `rama`); `ParteDestino` + `estado`, `contabilizados`,
  `contabilizados_ide` (`default_factory=list`), `aviso`; `AccionLinea` +
  `caa_origen` y `caa_nota` (`Optional[str] = None`).
- `.../application/services/cuenta_analitica.py`: `origen_subcuenta` (§7.2)
  y docstring (R7 de F-021 sustituida). Lo demás, intacto.
- `.../infrastructure/sigrid/sigrid_write_client.py`: `partes_del_periodo`
  y `partidas_de_lineas` (§9). `partes_existentes` NO cambia (paso 8).
- `.../application/pipelines/registro_pipeline.py`: `_resolver_cuentas`
  (§7.3), pasos 5 y 6 bis (§7.4), docstring de pasos.
- `.../config/settings.py`: `est_parte_imputado` (`EST_PARTE_IMPUTADO`, 10),
  `est_parte_cerrado` (`EST_PARTE_CERRADO`, 3); el pipeline usa `getattr(...,
  10/3)` como `mensuales_a_dedicacion` (F-019 DA8).
- `services/partes-transfer/tests/dobles.py` (solo crece): `SigridFake` con
  `partidas=None` (→ `{}`), `partes_del_periodo` (`p.get("est", 1)`),
  `partidas_de_lineas`, `partidas_leidas`; `partes_existentes` devuelve el
  de mayor `ide` como el SQL real; `SettingsFake` con 10/3.
- `services/partes-front/static/app.js`: `resumenHtml` pinta `esc(p.aviso)`
  tras cada parte y añade `notasCuentaHtml(pf.acciones)` (R27);
  `avisosCuentaHtml` (F-021) no cambia.
- Docs (R37): `docs/ARCHITECTURE.md` (semántica 16 nueva y la de F-021
  corregida; herramienta en «Herramientas de consola»),
  `docs/referencia/partes-proyecto.md` §3.5 y
  `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` §3.5 (commit local).

## 7. Clases y funciones

### 7.1 `application/services/estado_parte.py` (pura)

```python
MOTIVO_PARTE_CONTABILIZADO = "parte_contabilizado"
def elegir_parte(ano, mes, partes: list[ParteSigrid], *, est_imputado) -> ParteDestino
def aviso_de_parte(p, retenidas: int, *, est_imputado, est_cerrado) -> str | None
def motivo_reabrir(cod: str, ano: int, mes: int) -> str
def motivo_choque(cod: str) -> str
```

- `elegir_parte`: orden `ide` desc; el primero no Imputado es el elegido;
  los Imputados, a `contabilizados(_ide)`. Todos Imputados: el de mayor
  `ide`, solo para informar (R3–R4). Sin partes: como hoy (R6).
- `aviso_de_parte`: Imputado ⇒ «el parte X de MM/AAAA está contabilizado: N
  línea(s) no se registran hasta que Administración lo reabra en Sigrid»;
  Cerrado ⇒ texto de R5; resto ⇒ `None`.
- Motivos con prefijo `parte_contabilizado: `: `motivo_reabrir` (pide
  reabrir en Sigrid y volver a aprobar) y `motivo_choque` (ya hay horas de
  ese recurso, día y tipo en el parte X, contabilizado).

### 7.2 `cuenta_analitica.origen_subcuenta` (pura, F-021 ampliada)

```python
RAMAS_COSTE = frozenset({"CD", "CI", "CP"})
@dataclass(frozen=True)
class OrigenSubcuenta: sub: str | None; origen: str | None; nota: str | None
def origen_subcuenta(paride: int, partidas: dict[int, PartidaCuenta],
                     horas: list[HoraRecurso], horide: int | None) -> OrigenSubcuenta
```

- R17/R19: partida conocida, `rama in RAMAS_COSTE` y `subcuenta(caa_cod)` ⇒
  `(sub, "partida", None)`. Sin mirar `tipcos` ni el recurso.
- Si no, `sub = subcuenta_de_linea(horas, horide)` (F-021 R1–R2): sin `sub`
  ⇒ `(None, None, None)` (R20); con `sub` ⇒ `(sub, "recurso", nota)`. Nota
  (con el código de la partida, nunca nombres): sin partida, partida no
  encontrada, partida sin cuenta, partida con cuenta de ingresos (R18).
- DA6-e vive solo aquí: si el humano elige otra salida, cambia esta rama.
- `resolver_cuenta` (F-021) no cambia: recibe la `sub` elegida.

### 7.3 `RegistroPipeline._resolver_cuentas` (paso 4b)

Si alguna `escribir` tiene `paride`, `partidas = self._cli.partidas_de_lineas
(parides)` (sin `try`, R22). `origen_subcuenta` por acción;
`cuentas_de_centro` una vez con todas las `sub` (R23); `resolver_cuenta`;
copia `caa_*`, `caa_origen`, `caa_nota`. INFO de F-021 R18 igual; INFO
nuevo `[registro] origen cuenta obra=… partida=n recurso=n sin=n` y el
recuento por tipo de nota (R24).

### 7.4 `RegistroPipeline._evaluar`

- Paso 5: `partes_del_periodo` → `elegir_parte`; si `not existe`, `cod =
  siguiente_cod_pt(...)` como hoy. INFO de R16.
- Paso 6 (synckey) sin cambios: lo nuestro sigue `ya_registrado` (R11).
- Paso 6 bis: elegido Imputado ⇒ toda `escribir` del periodo a `omitir` con
  `motivo_reabrir` (R3). Si no, por cada `contabilizados_ide`,
  `lineas_existentes(...)`: choque (recurso, día, `horide`) con línea sin su
  synckey ⇒ `omitir` con `motivo_choque` (R9). En ambos, `caa_ide = 0` y
  el resto de `caa_*` a `None` (R12). Luego `p.aviso = aviso_de_parte(...)`.
- Pasos 7 y 8: solo quedan `escribir` de periodos con elegido no Imputado:
  `pisar_claves` no toca un Imputado y no se crea parte por uno (R4, R10).

### 7.5 `comprobar_asiento_analitico.py` (consola, raíz de sv5)

`argparse`, `Settings()`, `SigridWriteClient` (solo `_read`). Pura:
`comparar(lineas_por_cuenta, debe_por_cuenta, n_asientos) -> str`
(tolerancia 0,01). Del Haber, solo el total (R35).

### 7.6 Contrato JSON: `asdict` de `ParteDestino` y `AccionLinea` ya viaja
en preflight y resultado; los campos nuevos aparecen solos.

## 8. Decisiones (APROBADAS por el humano, 2026-10-05)

Respuesta del humano, literal: «1 reabrir, 2, si, 3, prepara un borrador
para juan, 4 no. 6 en funcion de la partida elegida en el front o
automaticamente. Si cuelga de CI o de CD dicha partida. ok a lo demas». Así:

- **DA1 → reabrir.** Periodo todo Imputado: **no** hay parte complementario;
  las líneas se omiten con «reabrir en Sigrid» (R3) y entran normales al
  reaprobar tras la reapertura (R8). Reabrir y recontabilizar, Administración
  en Sigrid. Si queda un parte no Imputado en el periodo, van a él (R2).
- **DA2 → sí.** Se escribe en partes Cerrados, con aviso (R5).
- **DA3 → fuera de alcance**, pendiente de Juan (borrador del líder).
  Corregido: **2 recursos** sin contrapartida, no 3 (206 líneas, 12.169 €).
- **DA4 → no.** sv5 no contabiliza, no escribe asientos ni cambia estados.
- **DA5, DA7, DA8 → aprobadas** como se recomendaron (omitir con motivo;
  estados como ajustes 10/3; herramienta de comprobación).
- **DA6 → la cuenta es la de la partida del portal** (versión 3; sustituye
  a la v2). Humano, 2026-10-05, literal: «lo de las partidas esta
  funcionando bien. se asignan automaticamente si no hay partida indicada en
  el parte. si lo hay para un recurso indicada en el parte total o
  parcialmente, esas horas van a esa partida que puede ser cualquiera (por
  ejemplo mano de obra de ladrillos). a CP no van nunca. la cuenta a la que
  debe ir es siempre la que queda indicada en el front no te lies. en el
  front ya se esta casando perfectamente. si el administrativo lo quiere
  cambiar lo hace. la partida que se ha indicado ahi es a donde debe
  vincularse el coste». Sin rama CI/CD ni nota «pendiente» (R17, R19); CP,
  si aparece, es una partida más. Preguntas a Juan sobre CD/CP/oficio: fuera.
- **DA6-e (ABIERTA, humano).** Partida sin cuenta o solo con `INGR..` (CI
  2.811, CD 1.979 líneas en 2026; §2, §D10). Provisional (R18): la del
  recurso (F-021) con nota, como hizo Administración a mano con las 4.790.
  Pregunta: «¿qué cuenta lleva una línea imputada a una partida que solo
  tiene cuenta de ingresos o ninguna?». Si responde antes de T6, se ajusta.

**Qué cambia en F-021.** R7 y su DA5 («la partida no interviene») quedan
sustituidas por R17–R19. **Ningún test de F-021 cambia de aserción**:
ninguna línea de `test_f021_*.py` (sv5 y sv4) lleva `partida_ide`: todas
caen en R18 (sin partida), la regla de F-021; `caa_aviso`, `caa_motivo` y
el INFO de F-021 R18 no cambian. Cambian el docstring de
`cuenta_analitica.py`, `dobles.py` (crece) y la doc de F-021 en
`ARCHITECTURE.md`. Si un test de F-021 se pone rojo, se para.

## 9. SQL (solo lecturas de Sigrid; ningún SQL de PostgreSQL)

`partes_del_periodo` (una por periodo):

```sql
SELECT hmo.ide AS ide, con.cod AS cod, con.est AS est FROM hmo
JOIN con ON con.ide = hmo.ide
WHERE hmo.obride = ? AND hmo.ano = ? AND hmo.mes = ?
  AND ISNULL(hmo.reside, 0) = 0 AND con.tip = ? ORDER BY hmo.ide DESC
```

`partidas_de_lineas` (una por petición; `rama = subcuenta(ramacod)`):

```sql
SELECT p.ide AS ide, p.cod AS cod, pc.cod AS caacod, gc.cod AS ramacod
FROM obrparpar p
LEFT JOIN caa pa ON pa.ide = p.caaide AND ISNULL(p.caaide, 0) <> 0
LEFT JOIN con pc ON pc.ide = pa.ide
LEFT JOIN cag g1 ON g1.ide = pa.padide
LEFT JOIN con gc ON gc.ide = g1.padide
WHERE p.ide IN (?, …)
```

Herramienta: partes del periodo (con `con.res`, `con.fec`); `hmores` por
parte y cuenta (`SUM(tot)`, `COUNT(*)`, las `partes:%`); `apa` del asiento
(tipo 32, misma `emp`, `res`, `fec`) por cuenta. `truncated` ⇒ excepción.

## 10. Fase RED exigible (traza en `progress/impl_F-031.md`)

En rojo contra el código de hoy: R2, R3, R4, R5, R9, R10, R15, **R17**
(la partida manda sobre el recurso), R18 (nota), R19 (CD y CP con cuenta
de coste), R21, R26, R27, R34. En verde
antes de tocar nada: R6, R11, R20, **R25** (suite F-021 intacta), R30, R31.

## 11. Verificaciones manuales (humano)

- **M0.** El humano responde DA6-e y Juan, DA3. No bloquea empezar: R18
  es provisional y vive solo en `origen_subcuenta`.
- **M1 (solo lectura).** `cd services/partes-transfer && ../../.venv/Scripts/python.exe comprobar_asiento_analitico.py --empresa 1 --obra 0696 --ano 2026 --mes 1`
  ⇒ PT26/00004 Imputado, ANA26/00017, `cuadra`.
- **M2 (solo lectura).** `--obra 0404 --ano 2026 --mes 7` ⇒ PT26/00296 en
  registro, 0 líneas, sin asiento.
- **M3 (producción, sin escribir).** Modal de una obra con líneas de agosto
  y **cancelar**: aviso de Cerrado; `caa_cod` = cuenta de la partida.
- **M4.** Primer parte contabilizado con líneas de sv5: M1 ⇒ `cuadra`.

## 12. Despliegue, lo que no se toca y riesgos

- `redeploy_partes.ps1 -Solo sv5` y luego `-Solo sv4` (campos aditivos,
  R28; sin variables nuevas). Rollback: imagen anterior. Lo lanza el humano.
- No se tocan: `reglas_registro.py`, `coherencia_recurso.py`,
  `comprobacion_lineas.py`, `resultado_json.py`, `api/app.py`,
  `transfer_consumer.py`, `prueba_escritura_sigrid.py`, `test_f021_*`,
  `partida_catalog.py`, sv1–sv3, `orm_models.py`, `infra/`.
- Fuera: asientos y estados (DA4); contrapartida (DA3); los 31 asientos que
  no cuadran; recalcular líneas ya escritas; Porsan.
- Riesgos: carrera de segundos con un «Contabilizar» (aceptado; M1 la
  detecta); líneas retenidas si se contabiliza antes de aprobar (DA1); la
  partida del portal decide ahora la cuenta (un error de partida es
  contable; se ve en `caa_cod` del preflight); parte↔asiento sin clave.
