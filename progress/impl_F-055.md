<!-- progress/impl_F-055.md -->
# F-055 · Informe del implementer (2026-11-01)

Rama `feature/F-055-sv5-omite-lineas-sin-fecha`, worktree `partes-wt-f055`. Rigor **crítico**.
T1–T9 y T13 hechas; T10 (campaña de mutación completa) **preparada, la lanza el líder**; T11
(M2/M2b) y T12 (M3) son del líder/humano.

## Decisiones del humano aplicadas

- Spec aprobada el 2026-11-01 (literal «si» a «¿Apruebas la spec con las recomendaciones?»):
  DA1–DA11 con la recomendación (DA8 superada; DA10 = A, `DIAS_FUTURO` = 62; DA11 = A).
  Registrado en `design.md` §11 (encabezado de la sección).
- M1 del líder (2026-11-01, solo lectura) anotada en `design.md` §9: 15 `sin_fecha` sin estado,
  ninguna `anterior`/`posterior`, Sigrid 0 y 0 ⇒ constantes de DA2/DA10 sin cambios.

## Qué cambió (todo sv5 salvo documentación)

- **Nuevo** `services/partes-transfer/application/services/fecha_linea.py`: `MOTIVO_FECHA_NO_VALIDA`,
  `FECHA_MINIMA` = 20260101, `DIAS_FUTURO` = 62 y `motivo_fecha_no_valida(fecha_int, *, hoy)`
  (orden: no entero/booleano/≤ 0 ⇒ «la linea no tiene fecha»; `date()` lanza ⇒ «<valor> no es
  una fecha del calendario»; < mínima ⇒ anterior; > hoy + 62 ⇒ posterior). Fechas del motivo
  con `dd/mm/aaaa` rellenadas a cero a mano (no `strftime`, que en Windows no rellena años < 1000).
- `application/pipelines/registro_pipeline.py`: `_hoy()` estático (UTC); **paso 2a** en
  `preparar` justo tras `_con_empresa`: `por_fecha`, WARNING `[registro] obra=%s lineas sin
  fecha valida=%s registro_ids=%s` (ids ordenados, sin nombres ni DNIs), `validas`;
  `con_recurso`, `sin_recurso` y `horas_de_recursos` salen de `validas`; `ReglasRegistro` recibe
  `{**omisiones, **por_fecha}` y `decidir` corre sobre todas. El WARNING de 2c sigue contando
  solo `omisiones` (las del recurso). Docstring de cabecera con el paso 2a.
- `domain/models/registro_models.py`: `LineaEntrada.fecha_int: Optional[int] = None` y
  `ano`/`mes` con `int(self.fecha_int or 0)`. `PeticionFranquicia` (mismas propiedades) **no**
  se toca: no está en la spec y `FranquiciaIn` ya rechaza `null`.
- `interface_adapters/api/app.py`: `LineaIn.fecha_int: Optional[int] = None`. `FranquiciaIn`
  no se toca.
- `docs/ARCHITECTURE.md` semántica 6: el texto de design §10.
- `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (commit local **8913f8e** en
  `azure-apps`, sin push): punto 6 de §3.5 (motivo, `fecha_int` admite `null`, reajuste y
  franquicia `no_editable`) y «Nota a `porcentajes` (F-055, informativa)».
- Papeleo: `design.md` §9/§11, `tasks.md`, `harness/features.json` (`in_progress`),
  `BACKLOG.md` regenerado, `progress/current.md`.

Tests nuevos (sv5): `tests/test_f055_fecha_linea.py` (34), `tests/test_f055_pipeline_fecha.py`
(23), `tests/test_f055_canales.py` (12). **Ningún test existente modificado** (R12).

## Commits (rama de la feature)

`5fc86d2` T1 · `cb6d17e` T2 · `8d3a551` T3 · `180813f` T4 · `e5e5c53` T5 · `c12c90b` T6–T7
(T7 es solo verificación: la suite completa se corrió con el código de T6) · `cbf7d31` T8 ·
`7a06954` T9 (marca; el cambio vive en `azure-apps` 8913f8e) · el último, este informe.

## Desviaciones y notas de diseño

- Sin desviaciones de la spec. Detalles finos:
  - `horas_de_recursos` se sigue llamando aunque `validas` no tenga recursos (lista vacía): el
    cliente real devuelve `{}` sin consultar (`if not ides: return {}`), así que no hay lectura
    a Sigrid y el comportamiento de hoy con líneas sin recurso no cambia (R12). El test R5 lo
    fija: toda llamada llega vacía.
  - R10: la extra nueva del reajuste con fecha **no nula y no válida** (20261340, 20160315) pasa
    por `preparar` y sale `no registrable (omitir: fecha_no_valida: …)`; con nulo/0 sigue «sin
    decision» (F-046 sin cambios).
  - R15 (franquicia) se protege solo vía `preparar` (DA11 A): `veredicto` da `no_editable`; sus
    lecturas consultivas (E y partes del mes) siguen; no hay escritura ni alta.
  - En T6 se corrigió un test propio de T4 (`r6_mezcla`): `caplog` acumulaba los WARNING de las
    ejecuciones de referencia; se limpia antes de la ejecución medida. No afecta a la lógica.

## Fase RED (trazas reales)

**T2** — `cd services/partes-transfer && python -m pytest tests/test_f055_fecha_linea.py`:
```
tests\test_f055_fecha_linea.py:13: in <module>
    from application.services import fecha_linea
E   ImportError: cannot import name 'fecha_linea' from 'application.services' (C:\Users\pgris\PycharmProjects\partes-wt-f055\services\partes-transfer\application\services\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_f055_fecha_linea.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
============================== 1 error in 0.43s ===============================
```
Tras T3: `34 passed in 0.28s`.

**T4** — `python -m pytest tests/test_f055_pipeline_fecha.py tests/test_f055_canales.py -q
--tb=line -p no:warnings` (con T3 hecho, sin T5/T6):
```
E   AssertionError: assert ('escribir', None) == ('omitir', 'f... y reaprueba')          # r3_preflight_omite
E   AssertionError: assert [('escribir',...ribir', None)] == [('omitir', '...y reaprueba')]   # r3_no_synckey
E   AssertionError: assert (True and [{'registro_i...: 'CIV', ...}] == []               # r3_racha_y_hermano
E   AssertionError: assert ('omitir', 'e...te en Sigrid') == ('omitir', 'f... y reaprueba')   # r4 no_existe
E   AssertionError: assert ('omitir', 'e...obra destino') == ('omitir', 'f... y reaprueba')   # r4 otra_empresa
E   AssertionError: assert ('escribir', None) == ('omitir', 'f... y reaprueba')          # r4 baja
E   AssertionError: assert ('omitir', 'sin horas') == ('omitir', 'f... y reaprueba')     # r4 sin_horas
E   AssertionError: assert [{'registro_i...mes': 'MENC'}] == []                          # r4 mensual -> dedicacion
E   AssertionError: assert ([['00000000T']] == []                                        # r5 recursos_por_dni pedido
E   AssertionError: assert (True, [{'reg...], [], 0, ...) == (True, [{'reg...], [], 0, ...)   # r6 mezcla
E   AssertionError: assert (True is True and [{'registro_i... 'HL01', ...}] == []        # r7 escribe la linea 0
tests\test_f055_pipeline_fecha.py:227: assert (not True)                                # r10 reajuste editable
E   AssertionError: assert [] == ['[registro] ...o_ids=[3, 7]']                          # r11 sin WARNING
E   AssertionError: {"detail":[{"type":"int_type","loc":["body","lineas",1,"fecha_int"],"msg":"Input should be a valid integer","input":null}]}   # r9 HTTP null -> 422
E   AssertionError: {"detail":[{"type":"missing","loc":["body","lineas",1,"fecha_int"],"msg":"Field required", ...}]}                              # r9 HTTP ausente -> 422
TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'   # r9 cola null / ano_mes
E   TypeError: LineaEntrada.__init__() missing 1 required positional argument: 'fecha_int'           # r9 cola ausente / _a_dominio
31 failed, 4 passed in 3.08s
```
(Fallan también, por la misma causa, r15 franquicia posterior ×2 —se escribía—, r1_pipeline_usa_hoy
y r8 ×3. Los 4 que pasaban en RED son de caracterización: r11 sin inválidas, r15 hoy+30 ×2 y
r9 con fecha.) Tras T5 + T6: `69 passed in 3.14s` (los tres ficheros F-055).

## Verificación

- Suite de sv5 tras T6: `cd services/partes-transfer && python -m pytest -q -p no:warnings` ⇒
  **1554 passed in 17.18s** (1519 anteriores + 35 de pipeline/canales; antes de T6, sin los
  dos ficheros RED, 1519 passed).
- R13: `git diff dev --stat -- services/partes-front services/partes-persistencia
  services/partes-email services/partes-api infra` ⇒ **vacío**.
- `python -m harness.tamano --feature F-055` ⇒ `PUERTA TAMAÑO: F-055 dentro de los topes
  (requirements 106/150, design 249/250)`.
- `ruff`: los tres ficheros de test nuevos con imports ordenados; el resto del árbol de sv5 trae
  avisos previos (RUF100, I001 en `transfer_consumer.py`) que no son de esta feature.
- `bash harness/init.sh` (2026-11-01, desde el worktree, código final): **ENTORNO LISTO**, exit 0.
  Raíz `537 passed, 3 skipped in 145.59s`; sv1–sv3 y sv5 en verde (caché), sv4 `3307 passed,
  1 skipped in 992.59s`; `PUERTA COBERTURA: 100.0% de 44 líneas cambiadas cubiertas (44/44,
  umbral 80%, nivel critico)`; `PUERTA TAMAÑO: … impl 142/220`. Avisos previos ajenos: una
  feature `blocked` en el backlog, ruff 909 avisos de deuda, infra sin tests.

## Pendiente (fuera del implementer)

- **T10 · campaña de mutación completa** (la lanza el líder), desde el worktree:
  ```
  cd C:\Users\pgris\PycharmProjects\partes-wt-f055
  python -m harness.mutacion --feature F-055 --base dev --rama feature/F-055-sv5-omite-lineas-sin-fecha --max-mutantes 0
  ```
  Alcance esperado: `fecha_linea.py` y las líneas cambiadas de `registro_pipeline.py`,
  `registro_models.py` y `app.py`. Informe en `progress/mutacion_F-055.md`; los supervivientes
  se analizan ahí (rigor crítico: 0 sin justificar). Mutantes previsiblemente **equivalentes**
  a vigilar: `fecha_int or 0` en `ano`/`mes` (con `None` el paso 2a ya la omitió, pero
  `test_f055_r9_ano_mes_con_none` los mata); el `isinstance(.., bool)` (lo mata `True`/`False`).
- **T11 · M2/M2b** (sv5 local en modo pruebas, design §9) y **T12 · M3** tras
  `redeploy_partes.ps1 -Solo sv5` (lo pide el humano).
- Revisión del reviewer contra `CHECKPOINTS.md`.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (sv5) | 1554 passed, 0 failed (69 de F-055) |
| Tiempo de la suite de sv5 | 17,18 s |
| Cobertura de líneas cambiadas | **100,0 %** (44/44, `PUERTA COBERTURA` de `init.sh`) |
| Mutantes generados / supervivientes | **pendiente**: la campaña completa la lanza el líder (comando arriba); `progress/mutacion_F-055.md` |
| `bash harness/init.sh` | ENTORNO LISTO (exit 0) |
