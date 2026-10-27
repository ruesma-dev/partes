<!-- progress/impl_F-056.md -->
# F-056 · Franquicia de extras — informe del implementer (T1–T18 y T17b)

**Estado: T1–T18 y T17b hechas y en verde.** El hueco de R20 (no había ruta para decidir desde la
vista) lo resolvió el humano con DA28 = A (enmienda a3e16fb) y se implementó en T17b.
T19–T22 no son de este encargo. Rama `feature/F-056-franquicia-de-extras`
(worktree `partes-wt-f056`). Nada en `dev`/`main`, sin push y sin tocar Sigrid ni bases reales.

## Aprobaciones literales del humano

- 2026-10-23: «a a todo, actualzia backlog para que refleje lo que tien spec y estado real de todo»
  ⇒ DA1–DA20 = A.
- 2026-10-27 (aprueba DA2, DA17 y DA20 enmendadas y DA21–DA27 en A): «puedes arrancar, pero el
  nombre del campo y tipo todavia no lo sabemos hasta que no se cree».
  Consecuencia en el código: ningún test ni código depende de un nombre de columna real (los
  tests usan nombres inventados, p. ej. `FranqInventada`); `FRANQUICIA_CAMPO_RES` vacío por
  defecto (= franquicia apagada); `TIPOS_NUMERICOS` = los 9 tipos de design §4 (sin `bigint`).
  M1b y M2 no se han intentado.
- 2026-10-27, DA28 (la vista decide «Ajustar»/«Recalcular»): «a» (opción A: ruta nueva «decidir» y
  luego aplicar). Tras enseñarle la enmienda (R45, R46, DA28, T17b): «si».

## Commits (uno por tarea)

| Tarea | Commit | Qué |
|---|---|---|
| T1–T7 | eec694c…5f65009 | sv5 base: dominio, fórmula, R31 en choques, cliente, pipeline, API (antes de la enmienda) |
| T8 | e3d3d0d | sv5 dominio y puro de la enmienda: `CAMPO_RE`, `TIPOS_NUMERICOS`, `leer_valor`, estados, `texto_ajuste` sin cifras |
| T9 | 1377890 | `FRANQUICIA_CAMPO_RES`, `tipo_columna_res`, `valores_campo_res` (lotes, nombre validado antes de leer) |
| T10 | ef0f5b0 | `FranquiciaPipeline.franquicias()`, X leída por sv5 (sin lock en comprobar, bajo el lock en ejecutar), R42 |
| T11 | c8cddc8 | `/api/franquicia/recursos`, `FranquiciaIn` sin X, `/health`, cableado en `main.py` |
| T12 | a7576a2 | `franquicia_ajuste` en las dos copias del ORM (byte-idénticas) y guardianes a OCHO tablas |
| T13 | bb8ba15 | sv4 puro `application/services/franquicia.py`: periodo, día, obra, candidatos (DA7), bloque, validación, payload |
| T14 | 77e82af | repositorio (`decidir_ajuste` CAS, `cerrar_ajuste`, `ajustes_de`, `lineas_trabajador_periodo`…) y `TransferClient` |
| T15 | 133885a | preflight con `/recursos` y bloque `franquicias`; decisiones en `ejecutar`/`encolar` |
| T16 | 494f9ef | `POST /api/franquicia/{id}/aplicar` y contexto de la vista de trabajador |
| T17 | c294f86 | `app.js`, `trabajador_detail.html`, `styles.css` |
| T18 | 5dd9a60 | contrato raíz `tests/test_f056_contrato_franquicia.py` y suites enteras |
| T17b | bed7c94 | DA28: `POST /api/franquicia/decidir`, botones «Ajustar»/«Recalcular» y `decidirDesdeVista` (tras desbloquear en 43ad418) |

## Ficheros tocados (enmienda y sv4)

- **sv5** (`services/partes-transfer/`): `domain/models/registro_models.py`,
  `application/services/franquicia.py`, `application/pipelines/franquicia_pipeline.py`,
  `config/settings.py`, `infrastructure/sigrid/sigrid_write_client.py`,
  `interface_adapters/api/app.py`, `main.py`, `tests/dobles.py` y `tests/test_f056_*.py`.
- **ORM** (sv4 y sv3, idénticos): `infrastructure/database/orm_models.py`.
- **sv4** (`services/partes-front/`): `application/services/franquicia.py` (nuevo, puro),
  `infrastructure/database/parte_repository.py`, `infrastructure/transfer/transfer_client.py`,
  `interface_adapters/web/app.py`, `templates/trabajador_detail.html`, `static/app.js`,
  `static/styles.css`; tests `test_f056_orm.py`, `test_f056_franquicia.py`,
  `test_f056_decisiones.py`, `test_f056_vista.py`.
- **Raíz**: `tests/test_f010_orm_models_gemelos.py`, `tests/test_f015_r29_guardian_cinco_tablas.py`,
  `tests/test_f056_contrato_franquicia.py` (nuevo).

## Decisiones de diseño y desviaciones (justificadas en `progress/current.md`)

1. **`CAMPO_RE` termina en `\Z`, no en `$`**: en Python `$` admite un salto de línea final
   (`"campo\n"` pasaba). Misma regla, sin ese hueco.
2. **Import local de `CAMPO_RE`** dentro de `valores_campo_res` (ciclo `franquicia` → `pisado` →
   cliente). El cliente rechaza un nombre inválido ANTES de leer nada.
3. **sv5**: un recurso pedido que no está en `res` es `invalida` (nunca X = 0). En
   `comprobar`/`ejecutar` un fallo al leer el TIPO es `no_disponible` ⇒ `no_editable` (R42);
   `franquicias()` lo propaga (502 en `/recursos`, design §6). Caché del «sí» de la columna, que se
   olvida si falla la lectura de valores. X de exactamente 0,001 se clasifica `activa` con X 0,0
   (redondeo a 2 decimales): **lo señalo al reviewer**.
4. **Disparador (DA7 = A)**: candidato nuevo solo si la aprobación trae una línea del DÍA DE
   AJUSTE de un recurso con franquicia `activa` (o `invalida`, solo informa); un ajuste vivo
   (`aplicado`/`decidido`/`error`) sale con cualquier línea del periodo (R10); `rechazado` informa.
5. **Máquina de estados** (`decidir_ajuste`): `ajustar` (sin fila o desde `rechazado`) y
   `recalcular` (desde `aplicado`/`decidido`/`error`) ⇒ `decidido`; `no_ajustar` sin fila ⇒
   `rechazado` (repetirlo no hace nada); `mantener` no toca; el resto, 409 (`AjusteCambiadoError`,
   subclase de `CongeladoError`, que la web ya traduce a 409).
6. **Orden en `ejecutar`/`encolar`**: se VALIDAN las franquicias primero (422 formato, ámbito o
   clave ajena; 409 si `ajustar`/`recalcular` con extras de varios recursos, R12, o `ajustar` sin
   día ni obra, R6), luego los repartos de F-046, luego se GUARDAN las decisiones (CAS) y luego las
   líneas. Así un 422/409 de validación no deja nada escrito. Las claves válidas salen de las
   líneas pedidas, también las ya registradas (`recurso_fechas_de`, nuevo).
7. **Preflight consultivo** (R14): cualquier fallo propio del aviso sale como `aviso`, no 500.
   Una sola llamada a `/recursos` (en lotes de 500 si hiciera falta, tope de R40).
8. **`aplicar`** solo desde `decidido`/`error` (409 si no, sin sv5); 404 si no existe; con líneas
   `encolado` 409 «espera a que termine el registro» (R18). Sin respuesta de sv5 ⇒ `error` sin
   pisar E/A/X; se reintenta (R19). 200 con `ok` falso cuando sv5 dice que no.
9. **Portal**: cada candidato lleva `registro_ids` para que el modal mande cada decisión UNA vez
   con la llamada (síncrona o cola) que lleva sus líneas (`franquiciasPara`). «Registrar» se
   deshabilita hasta decidir (R13). Tras el registro, `aplicarFranquicias` aplica cada ajuste
   decidido (síncrono: ya; cola: cuando el sondeo de F-024 acaba) y avisa si la X usada difiere de
   la del aviso (DA22). La vista (solo modo nómina) enseña X usada/actual, E, A, día, obra, parte,
   estado y autor, con «Aplicar» para `decidido`/`error`.
10. **Guardianes existentes** (salieron en la suite de sv4 de T18): `test_f017_punto_unico` pasa de
   18 a **19** `_actor(request)` (la de `aplicar`, que R21 exige; docstring ampliado). F-043 (R19,
   R40) prohíbe recargas nuevas: «Aplicar» desde la vista NO recarga; el modal ofrece el botón
   «Actualizar» de siempre (`botonActualizar`), así que `location.reload` sigue en 23.
11. **T17b (DA28, R45, R46)**: sin duplicar lógica, la comprobación de UNA decisión sale de
   `validar_decisiones` a `fq._decision(d)` (la usan el modal y `fq.decision_vista`, que además
   limita a `DECISIONES_VISTA = (ajustar, recalcular)`), y el cuerpo del bucle de
   `_planes_franquicia` sale a `_plan_franquicia(rec, per, decision, lineas_de, filas)` (R6–R8,
   R12). `POST /api/franquicia/decidir`: 503 sin sv5 configurado; 422 formato/decisión o sin líneas
   activas de ESE recurso en el periodo; 409 por `_plan_franquicia` o por el CAS de
   `decidir_ajuste` (sin cambios); sin llamar a sv5; `{ok: true, ajuste}`. La vista pinta
   «Ajustar»/«Recalcular» según `acciones`; `decidirDesdeVista` confirma, decide, aplica el `id`
   devuelto y enseña el resultado con «Actualizar» (sin recarga nueva). F-017: 20 `_actor(request)`.

## Fase RED (trazas reales; comandos tal cual)

T1–T6 (sv5 base): trazas en `git show 6d777c4:progress/impl_F-056.md` (`ImportError` de los
módulos nuevos y 38 × `TypeError: build_app() got an unexpected keyword argument 'franquicia'`).

T8 — `python -m pytest tests/test_f056_franquicia.py -q -p no:cacheprovider` (sv5)
```
E   ImportError: cannot import name 'EstadoFranquicias' from 'domain.models.registro_models'
1 error in 0.88s
```
T9 — `python -m pytest tests/test_f056_cliente.py tests/test_f002_settings_y_app.py -q -p no:cacheprovider`
```
5 E   AttributeError: 'Settings' object has no attribute 'franquicia_campo_res'
9 E   AttributeError: 'SigridWriteClient' object has no attribute 'valores_campo_res'
2 E   AttributeError: 'SigridWriteClient' object has no attribute 'tipo_columna_res'
23 failed, 29 passed, 1 warning in 5.82s
```
T10 — `python -m pytest tests/test_f056_pipeline.py -q -p no:cacheprovider`
```
33 E   AttributeError: 'PeticionFranquicia' object has no attribute 'franquicia'
15 E   AttributeError: 'FranquiciaPipeline' object has no attribute 'franquicias'
48 failed, 4 passed in 5.42s
```
T11 — `python -m pytest tests/test_f056_api.py -q -p no:cacheprovider`
```
15 E  + where 404 = <Response [404 Not Found]>.status_code
 8 E  assert 404 == 422          6 E  assert 422 == 200
35 failed, 25 passed, 1 warning in 8.93s
```
T12 — raíz `python -m pytest tests/test_f010_orm_models_gemelos.py tests/test_f015_r29_guardian_cinco_tablas.py -q -p no:cacheprovider`
y sv4 `python -m pytest tests/test_f056_orm.py -q -p no:cacheprovider`
```
FAILED tests/test_f010_orm_models_gemelos.py::test_f056_r34_franquicia_ajuste_declara_sus_columnas_literales
3 failed, 27 passed in 21.63s
E   ImportError: cannot import name 'FranquiciaAjusteOrm' from 'infrastructure.database.orm_models'
```
T13 — `python -m pytest tests/test_f056_franquicia.py -q -p no:cacheprovider` (sv4)
```
E   ImportError: cannot import name 'franquicia' from 'application.services' (unknown location)
```
T14 — `python -m pytest tests/test_f056_decisiones.py -k "repositorio or cliente" -q -p no:cacheprovider`
```
17 E   AttributeError: 'ParteReviewRepository' object has no attribute 'decidir_ajuste'
 4 E   AttributeError: 'TransferClient' object has no attribute 'franquicia_recursos'
 4 E   AttributeError: 'TransferClient' object has no attribute 'franquicia_ejecutar'
32 failed in 4.68s
```
T15 — `python -m pytest tests/test_f056_decisiones.py -k "preflight or ejecutar or encolar" -q -p no:cacheprovider`
```
11 E   KeyError: 'franquicias'
 4 E   assert 200 == 422          2 E   assert 200 == 409
21 failed, 9 passed, 28 deselected, 1 warning in 18.89s
```
T16 — `python -m pytest tests/test_f056_decisiones.py -k aplicar tests/test_f056_vista.py -q -p no:cacheprovider`
y `python -m pytest tests/test_f056_vista.py -q -p no:cacheprovider`
```
5 E  + where 404 = <Response [404 Not Found]>.status_code      1 E   KeyError: 'ajuste'
8 failed, 1 passed, 67 deselected, 1 warning in 9.06s
10 E   KeyError: 'franquicia'
1 E   AttributeError: module 'application.services.franquicia' has no attribute 'vista_franquicia'
11 failed, 1 warning in 10.59s
```
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
Ya en verde: T8 133 · T9 52 · T10 52 · T11 60 (sv5 entera 1458) · T12 30 + 5 · T13 63 · T14 32 ·
T15 58 · T16 76 · T17 23 (`node --check` y parseo Jinja2 OK) · T18 5 · T17b 255 passed, 1 skipped
(con `test_f043_portal_fecha.py`; `node --check` OK).

## Pendiente y fuera del alcance

- El hueco de R20 quedó resuelto por DA28 = A (T17b). Si `decidir` va bien y `aplicar` falla, la
  fila queda `decidido`/`error` y la vista ofrece «Aplicar» (como tras el modal).
- **T19** (docs y `azure-apps`), **T20** (mutación, la lanza el líder), **T21** (M1b, M2–M4,
  humano) y **T22**: no son de este encargo.
- Con `FRANQUICIA_CAMPO_RES` vacío (defecto) sv5 responde `apagada` y el portal no enseña nada; la
  vista de trabajador hace una llamada a `/recursos` por carga en modo nómina.
- `ruff`: ficheros nuevos limpios; `app.py` de sv4 pasa de 10 a 15 `RUF100` respecto de la base de
  la rama, todos del patrón `# noqa: BLE001` que ya usa el fichero; `parte_repository.py`, igual.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests F-056 sv5 (5 ficheros) | 289 passed en 7,64 s |
| Tests F-056 sv4 (`orm`, `franquicia`, `decisiones`, `vista`) | 188 passed en 49,86 s (tras T17b) |
| Raíz (contrato + guardianes del ORM) | 35 passed en 41,94 s |
| Suite sv4 entera sin caché (tras T17b) | `python -m pytest -q -p no:cacheprovider`: 3175 passed, 1 skipped, 2 warnings en 821,67 s |
| `bash harness/init.sh` (2026-10-27, tras T17b) | **ENTORNO LISTO**. Raíz 529 passed, 3 skipped (159,5 s); sv4 3175 passed, 1 skipped (1144,2 s); sv3, sv5, sv1 y sv2 «de caché» (árboles sin cambios desde su último verde: sv3 2340 passed y sv5 1458 passed en el init de T18) |
| Cobertura de líneas cambiadas | PUERTA COBERTURA: **98,6 %** (1025/1040, umbral 80 %, nivel crítico) |
| Tamaño | PUERTA TAMAÑO: requirements 150/150, design 248/250, impl 214/220 |
| Mutación | no lanzada por el implementer: es T20 y la lanza el líder (`python -m harness.mutacion --feature F-056`) |
| JS y plantilla | `node --check static/app.js` OK; parseo Jinja2 de `trabajador_detail.html` OK; las funciones del modal se EJECUTAN con node en `test_f056_vista.py` |
