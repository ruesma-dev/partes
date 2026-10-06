<!-- specs/F-031-asiento-analitico/design.md -->
# F-031 · Diseño técnico

Datos (solo lectura, agregados): `progress/spec_F-031.md`, anexo §D1–§D11.
v4 (2026-10-05): complementario (DA1/DA2) y cuenta del recurso (DA6). **v5
(2026-10-06): alta protegida y dependencia con `porcentajes` (§13).**

## 1. Cómo contabiliza Sigrid un parte (lo que NO hay que construir)

Estados (`conest` tipo 35): 1 En registro, 3 Cerrado, 10 Imputado.
«Contabilizar parte» (Administración) lo pone en Imputado y crea **un**
asiento tipo 32 (mismo resumen y fecha): Debe = Σ `hmores.tot` por
`hmores.caaide` (las de 0 no), Haber por `res.caaconide` (§D2–§D4). Falla
**dónde** escribe sv5 (no miraba `con.est`) y, a veces, **qué cuenta** (§2).
Administración ya hace complementarios como un parte más (§D11; 7 en 2024–26).

## 2. La cuenta: recurso primero, partida de respaldo (DA6, medido)

Líneas 2026, empresa 1 (partida solo si `C[ID]`): partida y recurso coinciden
17.149 (6,88 M€); distintas 1.013 (0,57 M€) y la línea lleva **siempre** la
del recurso; partida sin cuenta 5.313; **recurso sin cuenta 544 (= partida
478, otra 66)**; ninguno 39. F-021 no cambia; solo si el recurso no da
subcuenta se usa la de la partida si es de coste. `C[ID]` es regla sobre el
texto (la `subcuenta()` de F-021): fuera `CP` («a CP no van nunca») e `INGR`.

## 3–4. Servicios, encaje y límite (ningún paso nuevo fuera de sv5)

- **sv5**: única escritora del monorepo; elige parte y cuenta leyendo Sigrid
  (no se fía del portal). `preparar` (fuera del lock): paso 4b + respaldo de
  partida. `_evaluar` (dentro del lock): pasos 5 y 7 con todos los partes del
  periodo. `_registrar_bajo_lock`: paso 8, alta protegida (§13).
- **sv4**: solo pinta `partes[].complementario/aviso` y `caa_nota`. Ni sv3,
  ni base `partes`, ni ORM, ni sigrid-api, ni servicio nuevo (DA4).
- **Fuera del monorepo**: `porcentajes` (dedicacion-transfer, F-037) escribe
  en el MISMO parte de Sigrid con copias literales de `estado_parte.py` y
  `cuenta_analitica.py`; el lock de cada uno es solo de su proceso (§13).

## 5–6. Ficheros

Crear: `.../application/services/estado_parte.py` (§7.1; cabecera R48),
`services/partes-transfer/comprobar_asiento_analitico.py` (§7.5); tests
`services/partes-transfer/tests/test_f031_{estado_parte,cuenta_partida,
pipeline_estado,pipeline_cuenta_partida,cliente_partes,comprobar_asiento,
cliente_alta,pipeline_alta}.py` y sv4 `tests/test_f031_preflight_avisos.py`.

Modificar (`...` = `services/partes-transfer`):
- `.../domain/models/registro_models.py`: `ParteSigrid`, `PartidaCuenta`
  (frozen); `ParteDestino` + `estado`, `complementario`, `cerrados`,
  `del_periodo`, `aviso`; `AccionLinea` + `caa_origen`, `caa_nota`.
- `.../application/services/cuenta_analitica.py`: §7.2 y docstring (R7 de
  F-021 matizada); cabecera de dependencia (R48, §13).
- `.../infrastructure/sigrid/sigrid_write_client.py`: `partes_del_periodo` y
  `partidas_de_lineas` (§9); **v5**: `stmts_crear_parte` con el alta
  protegida (§13). `partes_existentes` y `lineas_existentes` NO cambian.
- `.../application/pipelines/registro_pipeline.py`: `_resolver_cuentas`
  (§7.3), pasos 5, 7 y 8 (§7.4), **v5** `_crear_parte` (§13), docstring.
- `.../config/settings.py`: `EST_PARTE_CERRADO` (3), `EST_PARTE_IMPUTADO` (10).
- `.../tests/dobles.py` (solo crece): partidas, `partes_del_periodo`,
  `partidas_de_lineas`, fallos inyectables, `SettingsFake` 1/3/10; **v5**
  alta protegida opcional (§13).
- `services/partes-front/static/app.js`: `resumenHtml` rotula
  «complementario» y pinta `esc(p.aviso)`; `notasCuentaHtml` (R29).
- Docs: `docs/ARCHITECTURE.md` (semántica 16 y la de F-021 matizada;
  herramienta), `docs/referencia/partes-proyecto.md` §3.5 y
  `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (commit local).

## 7. Clases y funciones

### 7.1 `application/services/estado_parte.py` (pura)

```python
MOTIVO_PARTE_CERRADO = "parte_cerrado"
def elegir_parte(ano, mes, partes: list[ParteSigrid], *, est_registro) -> ParteDestino
def nombre_estado(est, *, est_cerrado, est_imputado) -> str
def aviso_de_parte(p: ParteDestino, nombres: dict[str, str]) -> str | None
def motivo_choque(cod: str, estado: str) -> str
```

- `elegir_parte`: `del_periodo` en orden `ide` desc; `cerrados` = códigos con
  `est != est_registro`; elegido = primero En registro (`existe`, `ide`,
  `cod`, `estado`); si no hay, `existe=False`. `complementario = bool(cerrados)`.
- `aviso_de_parte`: complementario ⇒ «el parte PT26/00004 (Imputado) de
  01/2026 esta cerrado: las lineas van al parte complementario PT26/00350
  (se creara | ya existe, en registro)»; si no, `None` (R18).
- `motivo_choque` ⇒ `parte_cerrado: ya hay horas de ese recurso, dia y tipo
  en el parte X (Cerrado); no se registran` (R11). Sin nombres.

### 7.2 `cuenta_analitica` (pura, F-021 ampliada)

```python
SUBCUENTAS_COSTE_PARTIDA = ("CI", "CD")
@dataclass(frozen=True)
class OrigenSubcuenta: sub: str | None; origen: str | None; nota: str | None
def subcuenta_de_partida(caa_cod: str | None) -> str | None
def origen_subcuenta(horas, horide, partida: PartidaCuenta | None) -> OrigenSubcuenta
```

`subcuenta_de_linea` (F-021) da sub ⇒ `(sub, "recurso", None)` sin mirar la
partida (R20); si no, y `subcuenta_de_partida(partida.caa_cod)` ⇒ `(sub,
"partida", nota)` (R21); si no ⇒ `(None, None, None)` (R22).
`resolver_cuenta` (F-021) no cambia: recibe la `sub` elegida.

### 7.3 `RegistroPipeline._resolver_cuentas` (paso 4b)

Sub del recurso por acción; las que no tienen y traen `paride` ⇒ una
`partidas_de_lineas` (sin `try`, R24); `origen_subcuenta`; una
`cuentas_de_centro` con todas las `sub` (R25); `resolver_cuenta`; INFO
`origen cuenta obra=… recurso= partida= ninguna=` (R26).

### 7.4 `RegistroPipeline._evaluar` y `_registrar_bajo_lock`

- Paso 5: por periodo, `partes_del_periodo` → `elegir_parte`; si `not
  existe`, `cod = siguiente_cod_pt(...)`; `aviso_de_parte`; INFO (R19).
- Paso 7: `lineas_existentes` de **cada** parte de `del_periodo`. Choque
  ajeno en un cerrado ⇒ `omitir` con `motivo_choque`, `caa_ide = 0`, resto
  `caa_*` a `None` (R11, R14); si no, choques en En registro ⇒ `Conflicto`
  con el `parte_cod` donde viven (R12); `pisar_claves` solo ve estos (R13).
- Paso 8: si `not existe`, `_crear_parte` (§13). Paso 9 inserta solo en el
  parte usado (R5).

### 7.5 `comprobar_asiento_analitico.py` (consola, raíz de sv5)

`argparse`, `Settings()`, `SigridWriteClient` (solo `_read`). Pura:
`comparar(lineas_por_cuenta, debe_por_cuenta, n_asientos) -> str` (0,01).
Del Haber, solo el total (R37). JSON: `asdict` ya lleva los campos nuevos.

## 8. Decisiones (humano)

- **DA1/DA2 → parte complementario** (2026-10-05, sustituye a «reabrir»).
  Literal: «juan ha dicho que si hay modificar un parte ya cerrado se hace
  con complementario». «Cerrado» = todo lo que **no** está En registro
  (CONFIRMADO el 2026-10-06: «aprobado, se refiere a lo que no este en
  registro»); vive solo en el predicado de `elegir_parte`.
- **DA3 → fuera** (borrador a Juan hecho). **DA4 → no**: sv5 no contabiliza
  ni cambia estados. **DA5, DA7, DA8 → aprobadas**.
- **DA6 → la cuenta sale del recurso** (v4). Literal: «correcto la cuenta
  analitica sale del recurso no de la partida». Respaldo: partida `C[ID]`
  solo si el recurso no tiene cuenta (R21). Retiradas R17–R19 de la v3.
- **F-021**: R7 matizado por R21; ningún `test_f021_*` cambia.
- **DA9 (v5, 2026-10-06) → alta protegida**. Literal: «si, amplia la spec» y
  «lo de no pisarse con porcentajes vale para una insercion normal no solo
  complementaria». Diseño en §13.

## 9. SQL de lectura (Sigrid; ningún SQL de PostgreSQL)

`partes_del_periodo(obra_ide, ano, mes)`: la consulta de `partes_existentes`
con `con.est AS est` (una por periodo, `ORDER BY hmo.ide DESC`; `_read`
convierte `truncated` en excepción).

`partidas_de_lineas(parides)`: `SELECT p.ide, p.cod, pc.cod AS caacod FROM
obrparpar p LEFT JOIN con pc ON pc.ide = p.caaide AND ISNULL(p.caaide, 0)
<> 0 WHERE p.ide IN (?, …)` (una por petición). Herramienta: partes con
`con.res`/`con.fec`, `hmores` por parte y cuenta, `apa` del asiento.

## 10. Fase RED exigible (traza en `progress/impl_F-031.md`)

En rojo contra el código anterior a cada bloque: R1, R2, R3, R5, R11, R12,
R13, R17, R18, R21, R23, R24, R28, R29, R36 (v4); **R41, R42, R43, R44,
R45, R46, R47** (v5, contra HEAD `7276ff3`). En verde antes de tocar: R4,
R6, R8, R10, R20, R22, R27, R32, R33; **R40** (ya hay una sola función de
alta, paso 8) como caracterización.

## 11. Verificaciones manuales (humano)

- **M0.** Hecho (2026-10-06): «cerrado» = no En registro.
- **M1 (solo lectura).** `cd services/partes-transfer && ../../.venv/Scripts/python.exe comprobar_asiento_analitico.py --empresa 1 --obra 0696 --ano 2026 --mes 1`
  ⇒ PT26/00004 Imputado, ANA26/00017, `cuadra`.
- **M2 (solo lectura).** `--obra 0404 --ano 2026 --mes 7` ⇒ PT26/00296 en
  registro, 0 líneas, sin asiento.
- **M3 (producción, sin escribir).** Modal de una obra con agosto Cerrado y
  **cancelar** ⇒ «complementario», código nuevo y aviso.
- **M4 (modo pruebas, 0404, si el humano lo autoriza).** PT26/00296 Cerrado,
  aprobar ⇒ complementario En registro; limpiar con `prueba_escritura_sigrid.py`.
- **M5.** Primer complementario contabilizado: M1 ⇒ `cuadra` en ambos.
- **M6 (v5, solo lectura, tras desplegar sv5 y dedicacion-transfer).** Por
  obra y mes con líneas de ambos: la herramienta de M1 lista **un** parte En
  registro; en los logs de sv5, `[registro] alta … propio|otro servicio`.

## 12. Despliegue, lo que no se toca y riesgos

- `redeploy_partes.ps1 -Solo sv5` y luego `-Solo sv4` (aditivo, R30; sin
  variables obligatorias). Rollback: imagen anterior. Lo lanza el humano.
- No se tocan: `reglas_registro.py`, `coherencia_recurso.py`, `api/app.py`,
  `comprobacion_lineas.py`, `resultado_json.py`, `transfer_consumer.py`,
  `prueba_escritura_sigrid.py`, `test_f021_*`, sv1–sv3, `infra/`, `CLAUDE.md`.
- Fuera: asientos y estados (DA4); contrapartida (DA3); los 31 asientos que
  no cuadran; recalcular líneas ya escritas; Porsan; código de `porcentajes`.
- Riesgos: carrera con un «Contabilizar» (aceptado; M1 la detecta); un
  `lineas_existentes` por parte del mes; los de §13.

## 13. Alta protegida y dependencia con `porcentajes` (v5; R40–R49)

**Dónde se crea hoy.** Un solo sitio: el paso 8 de `_registrar_bajo_lock`
(`registro_pipeline.py`) crea el primer parte del mes (R4) y el
complementario (R3) con `stmts_crear_parte` + una relectura que exige el
código propuesto. R40 ya se cumple en estructura; se extrae a
`_crear_parte(p, destino, desc) -> None` sin cambiar a quién se llama.

**Sentencias (R41, R42).** `stmts_crear_parte` (misma firma, sigue
devolviendo `[con, hmo]` para un único `escribir`) pasa a ser **texto y
orden de parámetros idénticos** a `porcentajes/services/dedicacion-transfer/
infrastructure/sigrid/sigrid_write_client.py::stmts_crear_parte` (rama
`feature/F-037-asiento-analitico-obra`, `40b9feb`): `INSERT INTO con … SELECT
x.n, … FROM (SELECT ISNULL(MAX(ide),0)+1 AS n FROM con WITH (UPDLOCK,
HOLDLOCK)) x WHERE NOT EXISTS (con c … cod, emp, tip) AND NOT EXISTS (hmo h
JOIN con r … obride, ano, mes, reside 0, tip, est En registro)`, cuatro
`WITH (UPDLOCK, HOLDLOCK)`; parámetros `[emp, tip, est, cod, desc[:128],
fec, cod, emp, tip, obride, ano, mes, tip, est]`. El `hmo` añade `AND NOT
EXISTS (SELECT 1 FROM hmo h WHERE h.ide = con.ide)`. Diferencia admitida:
la obra sin empresa sigue dando `TypeError` aquí (F-023 R35, test vigente)
y `ValueError` allí; no se toca. El test fija el SQL como literal.

**Pipeline (R43–R46).** `_crear_parte`: `cod = p.cod or siguiente_cod_pt`;
hasta 2 intentos: `n = escribir(stmts_crear_parte(...))`; `leido =
elegir_parte(ano, mes, partes_del_periodo(...), est_registro)`; si
`leido.existe` ⇒ `p.existe/ide/cod/estado` del leído, `p.creado = n > 0 and
leido.cod == cod`, INFO `[registro] alta obra=… periodo=… cod=… intento=…
parte=propio|otro servicio` y fin; si no y es el primer intento ⇒ `cod =
siguiente_cod_pt(...)`. Tras dos ⇒ `RuntimeError` con obra, periodo y
código, antes del paso 9 (R45). El `aviso` no se recalcula (es el texto del
preflight); `cod`/`ide` del resultado sí son los del parte usado.

**Doble (`dobles.py`, solo crece).** `SigridFake(alta_protegida=False)`:
opcional para no vaciar los guardas de carrera de F-002 (el doble no se
sincroniza a propósito). Activa: `crear_parte` no inserta (y `escribir`
devuelve 0) si el código existe en la empresa o hay un parte En registro de
la obra y mes. `al_alta: list[dict]`: partes que «el otro servicio» crea
justo antes del primer alta (R47); `altas`: cada intento.

**Tests ajenos que cambian (DA10, pide visto bueno del humano).**
`test_f023_escritura_empresa.py`: `r32` compara la lista completa de
parámetros del `con` ⇒ pasa a `[:6]`; `r34` exige que el SQL del `hmo`
termine en `… AND emp = ?` ⇒ pasa a contenerlo. Mismo sentido (empresa de
la obra, filtro por empresa), sin más cambios. Propios de F-031: el R9 de
`test_f031_pipeline_estado.py` (`cod_al_crear`) se reescribe a R43/R45.

**Dependencia (R48, R49).** Cabecera de `estado_parte.py` y
`cuenta_analitica.py` y docstring de `stmts_crear_parte`; `ARCHITECTURE.md`
(semántica 16) y `azure-apps/partes.md` («qué se rompe si cambia» de §3.5).
**No** entra en la lista cerrada de `CLAUDE.md` (es entre repositorios).
**Consecuencia (DA11):** tocar la cabecera cambia los bytes y pone en rojo
`porcentajes/.../test_f037_copias_partes.py::…ref_vigilada` (compara con
esta rama) hasta que `porcentajes` recopie y mueva `COMMIT_COPIADO`; su
design §12 lo prevé («texto, se recopia»). Es el «aviso en el mismo
trabajo»: se anota en `progress/current.md` y en el informe; no se edita
`porcentajes` desde aquí.

**Riesgo aceptado.** Las líneas que el otro servicio ya hubiera metido en el
parte usado no entran en el paso 7 (evaluado antes del alta): segundos.
