<!-- specs/F-031-asiento-analitico/design.md -->
# F-031 · Diseño técnico

Datos (solo lectura, agregados): `progress/spec_F-031.md`, anexo §D1–§D11.
Versión 4 (2026-10-05): complementario (DA1/DA2) y cuenta del recurso (DA6).

## 1. Cómo contabiliza Sigrid un parte (lo que NO hay que construir)

Estados del parte (tipo 35, `conest`): 1 En registro, 3 Cerrado, 10
Imputado. «Contabilizar parte» (Administración, por lotes) lo pone en
Imputado y crea **un** asiento analítico (tipo 32, mismo resumen y fecha):
Debe = Σ `hmores.tot` por `hmores.caaide` (las de 0 no entran), Haber por
`res.caaconide` (§D2–§D4). Falla **dónde** escribe sv5 (`partes_existentes`
no mira `con.est` y mete líneas en partes cerrados) y, en un caso marginal,
**qué cuenta** pone (recurso sin cuenta con partida de coste; §2).

Complementario (§D11): Administración ya los hace como un parte más de la
obra y mes (`PT..`, `Parte <obra>`); 7 casos 2024–26.

## 2. La cuenta: recurso primero, partida de respaldo (DA6, medido)

Líneas 2026, empresa 1 (cuenta de la partida solo si es `C[ID]`), medido por
el líder: partida y ficha del recurso coinciden 17.149 (6,88 M€); distintas
1.013 (0,57 M€) y la línea lleva **siempre** la del recurso (la de la
partida, 0); partida sin cuenta 5.313 (= recurso 5.297); **recurso sin
cuenta 544 (= partida 478, otra 66)**; ninguno 39. Por tanto: F-021 no
cambia, y solo cuando el recurso no da subcuenta se usa la de la partida si
es de coste. `C[ID]` es una regla sobre el texto de la subcuenta (la misma
`subcuenta()` de F-021): no hace falta el árbol `cag` ni `tipcos`, y deja
fuera `CP` («a CP no van nunca», humano) e `INGR`.

## 3–4. Servicios, encaje y límite (ningún paso nuevo fuera de sv5)

- **sv5**: única escritora; elige parte y cuenta. Lee estados y partidas en
  Sigrid (no se fía del portal, como F-023). `preparar` (fuera del lock):
  paso 4b de F-021 + respaldo de partida. `_evaluar` (dentro del lock):
  pasos 5 y 7 con todos los partes del periodo. `_registrar_bajo_lock`:
  paso 8 relee por código.
- **sv4**: solo pinta `partes[].complementario/aviso` y `caa_nota`. Ni sv3,
  ni base `partes`, ni ORM, ni sigrid-api, ni servicio nuevo (DA4).

## 5. Ficheros a crear

- `services/partes-transfer/application/services/estado_parte.py` (§7.1) y
  `services/partes-transfer/comprobar_asiento_analitico.py` (§7.5).
- Tests en `services/partes-transfer/tests/`: `test_f031_{estado_parte,
  cuenta_partida,pipeline_estado,pipeline_cuenta_partida,cliente_partes,
  comprobar_asiento}.py`; sv4: `tests/test_f031_preflight_avisos.py`.

## 6. Ficheros a modificar

- `services/partes-transfer/domain/models/registro_models.py`: `ParteSigrid`
  (frozen: `ide`, `cod`, `est`); `PartidaCuenta` (frozen: `ide`, `cod`,
  `caa_cod`); `ParteDestino` + `estado: Optional[int]`, `complementario:
  bool = False`, `cerrados: list[str]`, `del_periodo: list[ParteSigrid]`
  (`default_factory=list`), `aviso: Optional[str]`; `AccionLinea` +
  `caa_origen`, `caa_nota` (`Optional[str] = None`).
- `.../application/services/cuenta_analitica.py`: `subcuenta_de_partida` y
  `origen_subcuenta` (§7.2) y docstring (R7 de F-021 matizada). Lo demás,
  intacto.
- `.../infrastructure/sigrid/sigrid_write_client.py`: `partes_del_periodo`
  y `partidas_de_lineas` (§9). `partes_existentes`, `stmts_crear_parte` y
  `lineas_existentes` NO cambian.
- `.../application/pipelines/registro_pipeline.py`: `_resolver_cuentas`
  (§7.3), pasos 5, 7 y 8 (§7.4), docstring de pasos.
- `.../config/settings.py`: `est_parte_cerrado` (`EST_PARTE_CERRADO`, 3) y
  `est_parte_imputado` (`EST_PARTE_IMPUTADO`, 10), solo para los textos;
  `est_parte_activo` ya existe. El pipeline usa `getattr(..., 1/3/10)`
  como `mensuales_a_dedicacion` (F-019 DA8).
- `services/partes-transfer/tests/dobles.py` (solo crece): `SigridFake` con
  `partidas=None` (→ `{}`), `partes_del_periodo` (`p.get("est", 1)`, orden
  `ide` desc), `partidas_de_lineas` + `partidas_leidas`; `partes_existentes`
  devuelve el de mayor `ide` como el SQL real; `SettingsFake` con 1/3/10.
- `services/partes-front/static/app.js`: `resumenHtml` rotula
  «complementario» y pinta `esc(p.aviso)` en cada parte; añade
  `notasCuentaHtml(pf.acciones)` (R29); `avisosCuentaHtml` (F-021) intacto.
- Docs (R39): `docs/ARCHITECTURE.md` (semántica 16 nueva y la de F-021
  matizada; herramienta en «Herramientas de consola»),
  `docs/referencia/partes-proyecto.md` §3.5 y
  `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` §3.5 (commit local).

## 7. Clases y funciones

### 7.1 `application/services/estado_parte.py` (pura)

```python
MOTIVO_PARTE_CERRADO = "parte_cerrado"
def elegir_parte(ano, mes, partes: list[ParteSigrid], *, est_registro) -> ParteDestino
def nombre_estado(est, *, est_cerrado, est_imputado) -> str
def aviso_de_parte(p: ParteDestino, nombres: dict[str, str]) -> str | None
def motivo_choque(cod: str, estado: str) -> str
```

- `elegir_parte`: `del_periodo` = partes en orden `ide` desc; `cerrados` =
  códigos con `est != est_registro`. Elegido = primero En registro ⇒
  `existe=True`, `ide`, `cod`, `estado`. Ninguno En registro ⇒ `existe=False`
  (código lo pone el pipeline). `complementario = bool(cerrados)`.
- `aviso_de_parte`: complementario ⇒ «el parte PT26/00004 (Imputado) de
  01/2026 está cerrado: las líneas van al parte complementario PT26/00350
  (se creará | ya existe, en registro)»; si no, `None` (R18).
- `motivo_choque` ⇒ `parte_cerrado: ya hay horas de ese recurso, día y tipo
  en el parte X (Cerrado); no se registran` (R11). Sin nombres.

### 7.2 `cuenta_analitica` (pura, F-021 ampliada)

```python
SUBCUENTAS_COSTE_PARTIDA = ("CI", "CD")
@dataclass(frozen=True)
class OrigenSubcuenta: sub: str | None; origen: str | None; nota: str | None
def subcuenta_de_partida(caa_cod: str | None) -> str | None
def origen_subcuenta(horas: list[HoraRecurso], horide: int | None,
                     partida: PartidaCuenta | None) -> OrigenSubcuenta
```

- `subcuenta_de_partida`: `subcuenta(caa_cod)` si empieza (mayúsculas) por
  `CI` o `CD`; si no, `None`.
- `origen_subcuenta`: `sub = subcuenta_de_linea(horas, horide)` (F-021 R1–
  R2) ⇒ `(sub, "recurso", None)` sin mirar la partida (R20). Si no, y
  `subcuenta_de_partida(partida.caa_cod)` ⇒ `(sub, "partida", nota)` con
  nota «el recurso no tiene cuenta para esa hora: se usa la de la partida
  `<cod>` (.`<sub>`)» (R21). Si no ⇒ `(None, None, None)` (R22).
- `resolver_cuenta` (F-021) no cambia: recibe la `sub` elegida.

### 7.3 `RegistroPipeline._resolver_cuentas` (paso 4b)

Sub del recurso por acción; las que no tienen y traen `paride` ⇒
`partidas = self._cli.partidas_de_lineas(parides)` (una vez, sin `try`,
R24); `origen_subcuenta` por acción; `cuentas_de_centro` una vez con todas
las `sub` (R25); `resolver_cuenta`; copia `caa_*`, `caa_origen`, `caa_nota`.
INFO de F-021 R18 igual; nuevo `origen cuenta obra=… recurso= partida= ninguna=` (R26).

### 7.4 `RegistroPipeline._evaluar` y `_registrar_bajo_lock`

- Paso 5: por periodo, `partes_del_periodo` → `elegir_parte`; si `not
  existe`, `cod = siguiente_cod_pt(...)` como hoy; `aviso_de_parte`. INFO
  de R19.
- Paso 6 (synckey, global) sin cambios: R10 ya se cumple.
- Paso 7: por periodo con `escribir`, `lineas_existentes` de **cada** parte
  de `del_periodo` (hoy solo el elegido; un parte nuevo no tiene líneas).
  Choque con línea ajena de un parte cerrado ⇒ `omitir` con `motivo_choque`,
  `caa_ide = 0`, resto de `caa_*` a `None` (R11, R14). Si no, choques en
  partes En registro ⇒ `Conflicto` como hoy, `parte_cod` del parte donde
  viven (R12). `pisar_claves` solo ve estos (R13).
- Paso 8: crea el parte si `not existe` (complementario o primero) con
  `stmts_crear_parte` de hoy; relee con `partes_del_periodo` y toma el de
  `cod` propuesto y En registro; si no ⇒ `RuntimeError` antes del paso 9
  (R9). Paso 9 inserta solo en el elegido (R5).

### 7.5 `comprobar_asiento_analitico.py` (consola, raíz de sv5)

`argparse`, `Settings()`, `SigridWriteClient` (solo `_read`). Pura:
`comparar(lineas_por_cuenta, debe_por_cuenta, n_asientos) -> str`
(tolerancia 0,01). Del Haber, solo el total (R37). Lista también los
complementarios del periodo (cada parte con su estado).

### 7.6 JSON: `asdict` de `ParteDestino`/`AccionLinea` ya viaja; los campos nuevos salen solos.

## 8. Decisiones (humano, 2026-10-05)

Respuesta inicial: «1 reabrir, 2, si, 3, prepara un borrador para juan, 4
no. … ok a lo demas». Revisada el mismo día (v4):

- **DA1/DA2 → parte complementario** (sustituye a «reabrir» y a «escribir en
  Cerrados»). Humano, literal: «juan ha dicho que si hay modificar un parte
  ya cerrado se hace con complementario». **Interpretación del líder
  (CONFIRMADA por el humano el 2026-10-06: «aprobado, se refiere a lo que no este en registro»):** «cerrado» = cualquier parte del
  mes que **no** esté En registro (Cerrado o Imputado). sv5 nunca escribe en
  él: usa un parte En registro de la obra y mes (reutiliza el complementario
  si existe; si no, lo crea con el esquema de hoy) sin tocar el original;
  los duplicados se miran en todos los partes del periodo; una línea que
  choca con horas de un parte cerrado se omite (DA5). Si el humano dijera
  que «cerrado» es solo Imputado, cambia un único punto: el predicado
  En registro de `elegir_parte` (y R2/R3/R11).
- **DA3 → fuera** (borrador a Juan hecho; 2 recursos sin contrapartida).
  **DA4 → no**: sv5 no contabiliza ni cambia estados. **DA5, DA7, DA8 →
  aprobadas** (omitir con motivo; estados como ajustes; herramienta).
- **DA6 → la cuenta sale del recurso** (v4, revierte la v3 «la partida
  manda»). Humano, literal: «correcto la cuenta analitica sale del recurso
  no de la partida». Medido en §2. Respaldo: partida `C[ID]` solo si el
  recurso no tiene cuenta (R21). Se retiran R17–R19 de la v3 y DA6-e (ya
  no aplica: con cuenta del recurso, la partida sin cuenta no importa).

**Qué cambia en F-021.** R7 («la partida no interviene») queda matizado por
R21. **Ningún test de F-021 cambia de aserción**: ninguna línea de
`test_f021_*` (sv5 y sv4) lleva `partida_ide` en el pipeline (solo
`test_f021_cliente_cuenta.py` pasa `paride` al `INSERT`, que no cambia), y
`SigridFake` sin `partidas` devuelve `{}`. Cambian el docstring de
`cuenta_analitica.py`, `dobles.py` (crece) y la doc de F-021 en
`ARCHITECTURE.md`. Si un test de F-021 se pone rojo, se para.

## 9. SQL (solo lecturas de Sigrid; ningún SQL de PostgreSQL)

`partes_del_periodo(obra_ide, ano, mes) -> list[ParteSigrid]` (una por
periodo; `_read` ya convierte `truncated` en excepción):

```sql
SELECT hmo.ide AS ide, con.cod AS cod, con.est AS est FROM hmo
JOIN con ON con.ide = hmo.ide
WHERE hmo.obride = ? AND hmo.ano = ? AND hmo.mes = ?
  AND ISNULL(hmo.reside, 0) = 0 AND con.tip = ? ORDER BY hmo.ide DESC
```

`partidas_de_lineas(parides) -> dict[int, PartidaCuenta]` (una por petición):

```sql
SELECT p.ide AS ide, p.cod AS cod, pc.cod AS caacod FROM obrparpar p
LEFT JOIN con pc ON pc.ide = p.caaide AND ISNULL(p.caaide, 0) <> 0
WHERE p.ide IN (?, …)
```

Herramienta: partes del periodo (con `con.res`, `con.fec`); `hmores` por
parte y cuenta (`SUM(tot)`, `COUNT(*)`, las `partes:%`); `apa` del asiento
(tipo 32, misma `emp`, `res`, `fec`) por cuenta. `truncated` ⇒ excepción.

## 10. Fase RED exigible (traza en `progress/impl_F-031.md`)

En rojo contra el código de hoy: R1, R2 y R3 (parte cerrado de mayor `ide`
⇒ complementario), R5, R9 (relee otro código), R11, R12 (choque en otro parte En
registro), R13, R17, R18, **R21** (respaldo de partida), R23, R24, R28,
R29, R36. En verde antes de tocar nada: R4, R6 (un solo parte En
registro), R8, R10, **R20** (el recurso manda aunque la partida tenga otra
cuenta), R22, **R27** (suite F-021 intacta), R32, R33.

## 11. Verificaciones manuales (humano)

- **M0.** Hecho: el humano confirmó «cerrado» = no En registro el 2026-10-06 (§8); vive en `elegir_parte`.
- **M1 (solo lectura).** `cd services/partes-transfer && ../../.venv/Scripts/python.exe comprobar_asiento_analitico.py --empresa 1 --obra 0696 --ano 2026 --mes 1`
  ⇒ PT26/00004 Imputado, ANA26/00017, `cuadra`.
- **M2 (solo lectura).** `--obra 0404 --ano 2026 --mes 7` ⇒ PT26/00296 en
  registro, 0 líneas, sin asiento.
- **M3 (producción, sin escribir).** Modal de una obra con líneas de agosto
  (partes Cerrados) y **cancelar**: «complementario», código nuevo y aviso.
- **M4 (modo pruebas, obra 0404).** Con PT26/00296 pasado a Cerrado por
  Administración, aprobar ⇒ complementario nuevo En registro; limpiar con
  `prueba_escritura_sigrid.py`. Solo si el humano lo autoriza.
- **M5.** Primer complementario contabilizado: M1 ⇒ `cuadra` en ambos.

## 12. Despliegue, lo que no se toca y riesgos

- `redeploy_partes.ps1 -Solo sv5` y luego `-Solo sv4` (aditivo, R30; sin
  variables obligatorias). Rollback: imagen anterior. Lo lanza el humano.
- No se tocan: `reglas_registro.py`, `coherencia_recurso.py`,
  `comprobacion_lineas.py`, `resultado_json.py`, `api/app.py`,
  `transfer_consumer.py`, `prueba_escritura_sigrid.py`, `test_f021_*`,
  `partida_catalog.py`, sv1–sv3, `orm_models.py`, `infra/`.
- Fuera: asientos y estados (DA4); contrapartida (DA3); los 31 asientos que
  no cuadran; recalcular líneas ya escritas; Porsan.
- Riesgos: carrera con un «Contabilizar» (aceptado; M1 la detecta);
  «cerrado» sin confirmar (M0); un `lineas_existentes` por parte del mes.
