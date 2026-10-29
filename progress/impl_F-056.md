<!-- progress/impl_F-056.md -->
# F-056 · Franquicia de extras — informe del implementer (T1–T19, T17b, T23–T25, T27 y mutación)

**Estado: T1–T19, T17b, T23–T25 (DA29–DA31: campo extendido) y T27 (DA32: obra del recurso)
hechas y en verde**, más las observaciones 1, 2, 4, 5 y 7 de la review. Sin T21–T22.

## Aprobaciones literales del humano

- 2026-10-23: «a a todo, actualzia backlog para que refleje lo que tien spec y estado real de todo»
  ⇒ DA1–DA20 = A.
- 2026-10-27 (DA2, DA17, DA20 enmendadas; DA21–DA27 en A): «puedes arrancar, pero el nombre del campo
  y tipo todavia no lo sabemos hasta que no se cree».
- 2026-10-27, DA28 (la vista decide «Ajustar»/«Recalcular»): «a»; tras ver la enmienda: «si».
- 2026-10-28 (test intermitente de F-019 que invalidó la campaña): «a» (arreglarlo en el test).
- 2026-10-29, a DA29–DA31: «da29, recuerda coger el ide del recurso filtrado por empresa, el mismo dni
  de recurso puede estar en 2 empresas. lo demas ok». Tras enseñarle la enmienda (R47, R48,
  `FRANQUICIA_CAMPO_EXT`, T23–T26): «si».
- 2026-10-29, observación 6 del reviewer: «sobre la 6, la A» (DA32). Tras ver DA32 y su punto abierto
  («A (recomiendo): Dejar el día como está: es de la persona, como ya decidimos en DA6. Solo cambia la
  obra.»): «a». Por eso `_dia_ajuste` NO cambia.

## Commits (uno por tarea o bloque)

T1–T7 eec694c…5f65009 · T8 e3d3d0d · T9 1377890 · T10 ef0f5b0 · T11 c8cddc8 · T12 a7576a2 ·
T13 bb8ba15 · T14 77e82af · T15 133885a · T16 494f9ef · T17 c294f86 · T18 5dd9a60 · T17b bed7c94 ·
F-019 06065ea · mutación 138dc9f, 8f465d3, ca0545b, 7487f85, e3da705, 9ae3fa5 · T19 21bdadf
(`azure-apps` 58bce5e) · T23 62cc269 · T24 d66d605 · T27 17cefc3 · T25 d2f6fd6 (`azure-apps` e32f089, corrige
58bce5e; los dos de `azure-apps`, locales). Detalle: `git log --oneline 39aef7b..HEAD`.

## Ficheros tocados

- **sv5**: `registro_models.py`, `services/franquicia.py`, `pipelines/franquicia_pipeline.py`,
  `settings.py`, `sigrid_write_client.py`, `api/app.py`, `main.py`, `tests/dobles.py`, `test_f056_*`.
- **ORM** sv4 y sv3 (idénticos) `orm_models.py`; sv3 `tests/test_f056_orm_franquicia.py`.
- **sv4**: `services/franquicia.py` (nuevo, puro), `parte_repository.py`, `transfer_client.py`,
  `web/app.py`, `trabajador_detail.html`, `app.js`, `styles.css`, `test_f056_{orm,franquicia,
  decisiones,vista}.py` y `test_f019_bandeja.py` (solo el reloj). **Raíz**: guardianes F-010 y F-015
  y `test_f056_contrato_franquicia.py`. **Docs** (T19, rehechos en T25): `ARCHITECTURE.md`,
  `partes-proyecto.md`, `azure-apps/partes.md`.

## Decisiones de diseño y desviaciones (justificadas en `progress/current.md`)

1. **T23, `COD_EXT_RE` termina en `\Z`, no en `$`** (en Python `$` admite un salto de línea final).
   El `cod` va siempre como parámetro: el filtro solo detecta un ajuste mal puesto. Sin import
   local en el cliente (ya no valida nada: no interpola).
2. **T23, `valores_campo_ext` hace `LEFT JOIN` desde `con` de tip 33** (design §4): devuelve
   `reside -> [valn]` solo de las filas con `extide`, así «recurso que no es `con` de tip 33 ⇒
   `invalida`» se conserva. `motivo_definicion` acepta `camtip` como texto `"1"` (`int()`); un
   `camtip` no convertible es motivo, no excepción.
3. **sv5**: un recurso pedido que no está en `res` es `invalida` (nunca X = 0). En
   `comprobar`/`ejecutar` un fallo al leer la DEFINICIÓN es `no_disponible` ⇒ `no_editable` (R42);
   `franquicias()` lo propaga (502 en `/recursos`, design §6). Caché del «sí» por `cod` (otro `cod`
   se vuelve a mirar), que se olvida si falla la lectura de valores. `leer_valor` no cambia
   (design §4): con `valn` entero, el redondeo a dos decimales ya no actúa.
4. **Disparador (DA7 = A)**: candidato nuevo solo con una línea del DÍA DE AJUSTE de un recurso
   `activa` (o `invalida`, informa); un ajuste vivo sale con cualquier línea del periodo (R10).
5. **Estados** (`decidir_ajuste`): `ajustar` (sin fila o desde `rechazado`) y `recalcular` (desde
   `aplicado`/`decidido`/`error`) ⇒ `decidido`; `no_ajustar` sin fila ⇒ `rechazado`; `mantener` no
   toca; el resto, 409 (`AjusteCambiadoError`, subclase de `CongeladoError`).
6. **Orden en `ejecutar`/`encolar`**: se VALIDAN las franquicias (422; 409 por R12 o R6), luego los
   repartos de F-046, luego se GUARDAN las decisiones (CAS) y luego las líneas: un 422/409 no deja
   nada escrito. Las claves válidas salen de las líneas pedidas (`recurso_fechas_de`, nuevo).
7. **Preflight consultivo** (R14): un fallo propio sale como `aviso`, no 500. Una llamada a
   `/recursos` (en lotes de 500, tope de R40).
8. **`aplicar`** solo desde `decidido`/`error` (409 si no); 404 si no existe; 409 con líneas
   `encolado` (R18). Sin respuesta de sv5 ⇒ `error` sin pisar E/A/X (R19).
9. **Portal**: cada candidato lleva `registro_ids` (el modal manda cada decisión UNA vez con sus
   líneas); «Registrar» deshabilitado hasta decidir (R13); `aplicarFranquicias` tras el registro y
   aviso si la X usada difiere (DA22). La vista (modo nómina) enseña X usada/actual, E, A y estado.
10. **Guardianes**: `test_f017_punto_unico` a 19 `_actor(request)` (20 tras T17b); «Aplicar» no
   recarga (F-043): `location.reload` sigue en 23.
11. **T17b (DA28, R45, R46)**: una decisión se comprueba en `fq._decision(d)` (modal y
   `fq.decision_vista`, limitada a `ajustar`/`recalcular`) y el plan en `_plan_franquicia` (R6–R8,
   R12), sin duplicar. `POST /api/franquicia/decidir`: 503 sin sv5; 422 formato o sin líneas del
   recurso en el periodo; 409 por el plan o el CAS; no llama a sv5. F-017: 20 `_actor(request)`.

## Fase RED (trazas reales; comandos tal cual)

T1–T6 (sv5 base): trazas en `git show 6d777c4:progress/impl_F-056.md` (`ImportError` de los
módulos nuevos y 38 × `TypeError: build_app() got an unexpected keyword argument 'franquicia'`).

T8–T11 (columna de `res`, sustituida en T23): trazas en `git show dd197b7:progress/impl_F-056.md`
(`ImportError` de `EstadoFranquicias`; `AttributeError` de `franquicia_campo_res`,
`tipo_columna_res`, `valores_campo_res` y `franquicias`; rutas en 404).

T12–T16: trazas en `git show dd197b7:progress/impl_F-056.md` (`ImportError` de
`FranquiciaAjusteOrm` y del módulo `franquicia` de sv4; `AttributeError` de `decidir_ajuste`,
`franquicia_recursos` y `franquicia_ejecutar`; `KeyError: 'franquicias'`; rutas en 404).
T17 — `python -m pytest tests/test_f056_vista.py -q -p no:cacheprovider`
```
5 E   AssertionError: app.js no define TEXTO_DECISION_FRANQUICIA
1 E   assert 'franquiciasHtml(pf.franquicias)' in '\n  function aprobar(peticion, contexto) {...'
1 E   assert 'franquicia-ajuste' in '<!DOCTYPE html>...'          1 E   KeyError: 'registro_ids'
11 failed, 12 passed, 1 warning in 13.15s
```
T18 — el contrato verifica código ya escrito, así que no puede fallar «antes»; en su lugar,
**prueba de sensibilidad**: sv4 manda la X a propósito (`payload_franquicia` + `"franquicia"`),
se lanza `python -m pytest tests/test_f056_contrato_franquicia.py -q -p no:cacheprovider` y se revierte:
```
E   AssertionError: assert 'franquicia' not in {'ajuste_id': 0, 'recurso_ide': 502, ...}
E   Extra items in the left set: 'franquicia'
FAILED tests/test_f056_contrato_franquicia.py::test_f056_r41_sv4_no_manda_la_x
FAILED tests/test_f056_contrato_franquicia.py::test_f056_r36_ninguna_clave_de_sv4_se_pierde_en_sv5
```
T17b — `python -m pytest tests/test_f056_vista.py tests/test_f056_franquicia.py tests/test_f056_decisiones.py tests/test_f017_punto_unico.py -q -p no:cacheprovider`
```
13 E  + where 404 = <Response [404 Not Found]>.status_code
12 E   AttributeError: module 'application.services.franquicia' has no attribute 'decision_vista'
 7 E   assert 404 == 422          3 E   assert (404 == 409)          2 E   KeyError: 'ajuste'
32 failed, 165 passed, 1 skipped, 1 warning in 100.18s
```
Ya en verde: T8 133 · T9 52 · T10 52 · T11 60 · T12 30 + 5 · T13 63 · T14 32 · T15 58 · T16 76 ·
T17 23 · T18 5 · T17b 255 passed, 1 skipped (`node --check` y parseo Jinja2 OK).

T23 — `python -m pytest -q -p no:cacheprovider tests/test_f056_franquicia.py tests/test_f056_cliente.py
tests/test_f056_pipeline.py tests/test_f056_api.py tests/test_f002_settings_y_app.py` (sv5), tests
primero y código viejo: `99 failed, 225 passed, 1 warning in 54.07s`. Los centrales, con `--tb=line`:
```
FAILED tests/test_f056_pipeline.py::test_f056_r47_el_cod_10_de_tip_42_nunca_da_x
E   AssertionError: assert ('apagada' == 'no_disponible'
FAILED tests/test_f056_pipeline.py::test_f056_r48_mismo_dni_dos_empresas_usa_la_del_recurso_pedido
E   assert [] == [501]
4 E   AttributeError: module 'application.services.franquicia' has no attribute 'lectura_de'
E   AttributeError: module 'application.services.franquicia' has no attribute 'motivo_definicion'
E   AttributeError: 'SigridWriteClient' object has no attribute 'valores_campo_ext'. Did you mean: 'valores_campo_res'?
8 failed in 1.20s
```
Ya en verde: los mismos cinco ficheros, `324 passed, 1 warning in 15.76s`; sv5 entera 1485 passed.
T27 — `python -m pytest -q -p no:cacheprovider --tb=line tests/test_f056_franquicia.py
tests/test_f056_decisiones.py tests/test_f056_vista.py -k da32` (sv4), tests primero:
```
E   AttributeError: module 'application.services.franquicia' has no attribute 'lineas_del_recurso'
E   AssertionError: assert (501, {'ide':...00'}, '02.02') == (501, {'ide':...00'}, '01.01')
E   AssertionError: assert (501, 2026101...200', '02.02') == (501, 2026101...100', '01.01')
3 failed, 228 deselected, 1 warning in 11.96s
```
(preflight y `decidir` proponían la obra 0200 del otro recurso). Ya en verde: 231 passed.
T24 — solo textos y dos tests de R48 en sv4 que vigilan lo que ya se cumplía (design §4: «Comprobado
(R48)»): no hay fallo «antes» posible; pasan contra el código sin cambios de lógica.

## Mutación: análisis de la campaña completa (3ba3403, sobre 06065ea)

513 mutantes: 403 muertos, 102 supervivientes y 8 timeouts. El análisis de cada uno vive en
`progress/mutacion_F-056.md` (por qué ningún test lo cazaba, decisión y tabla de verificación a
mano: con el mutante aplicado, su fichero de tests sale con 1; sin él, con 0).

| Fichero | Superv. | Test nuevo | Equivalente (propuesto) |
|---|---|---|---|
| sv4 `web/app.py` | 31 | 30 | 1 |
| sv3 `orm_models.py` | 22 | 22 | 0 |
| sv4 `services/franquicia.py` | 16 | 14 | 2 |
| sv5 `franquicia_pipeline.py` | 13 | 6 | 7 |
| sv4 `parte_repository.py` | 9 | 7 | 2 |
| sv5 `services/franquicia.py` | 7 | 6 | 1 |
| sv5 `api/app.py` · `registro_pipeline.py` | 3 · 1 | 3 · 0 | 0 · 1 |
| **Total** | **102** | **88** | **14** |

- sv3 (22): el guardián de la raíz solo corre en `init.sh`; sv3 gana su test de la tabla.
- Equivalentes (14, **propuestos; los acepta el humano**): `getattr` con defecto que `Settings`
  siempre define, `or 0`/`or 1` sin 0 ni 1 posibles, `<=` frente a `<` en valores ya descartados,
  lotes en un `set`... Justificación de cada uno en el informe de mutación.
- Timeouts (8): ninguno cuelga (expresiones sin bucle; lentitud con 4 workers). Dos (t1 redondeo,
  t3 recurso 0) no los cazaba nadie: test nuevo. Sin producción tocada; campaña no relanzada.
- Tras T23 (supervivientes de sv5 #79–#102): ninguno estaba en el código quitado (`CAMPO_RE`, tipo
  de columna, `valores_campo_res`). Sus expresiones siguen igual (solo se desplazan las líneas) y
  los 15 tests que los matan siguen en la suite y en verde; T26 los reanaliza.

## Ficheros de producción cambiados por T23, T24 y T27 (para `--ficheros` de la mutación)

- **T27 (sv4)**: `application/services/franquicia.py` (`lineas_del_recurso`, nueva) e
  `interface_adapters/web/app.py` (`_propuesta`). Observación 4: solo docstrings de las dos
  `orm_models.py` (siguen byte-idénticas) y de sv5 `domain/models/registro_models.py`.

- **T23 (sv5)**: `application/services/franquicia.py`, `application/pipelines/franquicia_pipeline.py`,
  `config/settings.py`, `infrastructure/sigrid/sigrid_write_client.py`,
  `interface_adapters/api/app.py`, `main.py` y `domain/models/registro_models.py` (solo docstring).
- **T24 (solo comentarios)**: sv4 `application/services/franquicia.py`,
  `infrastructure/database/parte_repository.py`, `interface_adapters/web/app.py` y las dos
  `infrastructure/database/orm_models.py` (sv4 y sv3, byte-idénticas, `cmp` sin diferencias).
- T25, solo documentación: `grep -n "CAMPO_RES"` en los tres documentos, nada; `grep -rn "CAMPO_RES"
  services/`, solo `tests/test_f002_settings_y_app.py` (prueba que la variable vieja no enciende nada).

## Pendiente y fuera del alcance

- Mutación de las líneas de T27: la lanza el líder. **T21** (M2–M4, humano) y **T22**: no son de
  este encargo.
- Con `FRANQUICIA_CAMPO_EXT` vacío (defecto), sv5 responde `apagada` y el portal no enseña nada.
- `ruff`: sin avisos nuevos (I001 y `RUF100` de `# noqa: BLE001` ya estaban).
- **Fuera de F-056 (2026-10-28):** reloj de `test_f019_r13_otro_contenido_sube_la_version`, arreglado
  solo en el test (06065ea). Mismo patrón, sin arreglar: `test_f019_portal.py:342`.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests F-056 sv5 (5 ficheros) | 289 passed en 7,64 s |
| Tests F-056 sv4 (`orm`, `franquicia`, `decisiones`, `vista`) | 188 passed en 49,86 s (tras T17b) |
| Raíz (contrato + guardianes del ORM) | 35 passed en 41,94 s |
| Suites enteras sin caché (2026-10-29, tras T23–T25) | `python -m pytest -q -p no:cacheprovider` desde cada servicio: sv5 1485 passed en 39,10 s; sv4 3220 passed, 1 skipped, 2 warnings en 1250,85 s |
| `bash harness/init.sh` (2026-10-29, tras T23–T25) | **ENTORNO LISTO**. Raíz 529 passed, 3 skipped (176,0 s); sv3 2345 passed (74,5 s); sv4 3220 passed, 1 skipped (1218,0 s); sv5 1485 passed (61,1 s); sv1 y sv2 de caché |
| Cobertura de líneas cambiadas | PUERTA COBERTURA: **99,0 %** (1045/1056, umbral 80 %, nivel crítico) |
| Tamaño | PUERTA TAMAÑO: requirements 150/150, design 250/250, impl 218/220 |
| Mutación | campaña 3ba3403 (4 workers): 513 mutantes, 403 muertos, 102 supervivientes y 8 timeouts. Tras el análisis, 88 supervivientes y 2 timeouts los mata un test nuevo; 14 son equivalentes, aceptados por el humano el 2026-10-29 («si») (`progress/mutacion_F-056.md`). T26 (e3dff2f): 23 mutantes, 23 muertos |
| JS y plantilla | `node --check static/app.js` OK; parseo Jinja2 de `trabajador_detail.html` OK; las funciones del modal se EJECUTAN con node en `test_f056_vista.py` |
