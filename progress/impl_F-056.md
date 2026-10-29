<!-- progress/impl_F-056.md -->
# F-056 · Franquicia de extras — informe del implementer (T1–T19, T17b y análisis de la mutación)

**Estado: T1–T19 y T17b hechas y en verde; los 102 supervivientes y 8 timeouts de la mutación
analizados** (§ Mutación). Sin T20–T22. Rama `feature/F-056-franquicia-de-extras`; sin push.

## Aprobaciones literales del humano

- 2026-10-23: «a a todo, actualzia backlog para que refleje lo que tien spec y estado real de todo»
  ⇒ DA1–DA20 = A.
- 2026-10-27 (DA2, DA17, DA20 enmendadas; DA21–DA27 en A): «puedes arrancar, pero el nombre del campo
  y tipo todavia no lo sabemos hasta que no se cree». Por eso ningún test ni código usa un nombre de
  columna real (los tests usan `FranqInventada`) y `FRANQUICIA_CAMPO_RES` es vacío por defecto
  (= apagada). `TIPOS_NUMERICOS` son los 9 de design §4 (sin `bigint`). M1b y M2 no se han intentado.
- 2026-10-27, DA28 (la vista decide «Ajustar»/«Recalcular»): «a»; tras ver la enmienda: «si».
- 2026-10-28 (test intermitente de F-019 que invalidó la campaña): «a» (arreglarlo en el test).

## Commits (uno por tarea o bloque)

T1–T7 eec694c…5f65009 · T8 e3d3d0d · T9 1377890 · T10 ef0f5b0 · T11 c8cddc8 · T12 a7576a2 ·
T13 bb8ba15 · T14 77e82af · T15 133885a · T16 494f9ef · T17 c294f86 · T18 5dd9a60 · T17b bed7c94 ·
F-019 06065ea · mutación 138dc9f, 8f465d3, ca0545b, 7487f85, e3da705, 9ae3fa5 · T19 21bdadf
(`azure-apps` 58bce5e, local). Detalle: `git log --oneline 39aef7b..HEAD`.

## Ficheros tocados

- **sv5**: `registro_models.py`, `services/franquicia.py`, `pipelines/franquicia_pipeline.py`,
  `settings.py`, `sigrid_write_client.py`, `api/app.py`, `main.py`, `tests/dobles.py`, `test_f056_*`.
- **ORM** sv4 y sv3 (idénticos) `orm_models.py`; sv3 `tests/test_f056_orm_franquicia.py`.
- **sv4**: `services/franquicia.py` (nuevo, puro), `parte_repository.py`, `transfer_client.py`,
  `web/app.py`, `trabajador_detail.html`, `app.js`, `styles.css`, `test_f056_{orm,franquicia,
  decisiones,vista}.py` y `test_f019_bandeja.py` (solo el reloj). **Raíz**: guardianes F-010 y F-015
  y `test_f056_contrato_franquicia.py`. **Docs** (T19): `ARCHITECTURE.md`, `partes-proyecto.md`,
  `azure-apps/partes.md`.

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
11. **T17b (DA28, R45, R46)**: una decisión se comprueba en `fq._decision(d)` (modal y
   `fq.decision_vista`, limitada a `ajustar`/`recalcular`) y el plan en `_plan_franquicia` (R6–R8,
   R12), sin duplicar. `POST /api/franquicia/decidir`: 503 sin sv5; 422 formato o sin líneas del
   recurso en el periodo; 409 por el plan o el CAS; no llama a sv5. F-017: 20 `_actor(request)`.

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

- sv3 (22): en la campaña no los cubría nada: el guardián byte a byte de la raíz solo corre en
  `init.sh` y sv3 no usa la tabla. sv3 gana su test de la tabla, como F-019 con la bandeja.
- Equivalentes (14, **propuestos; los acepta el humano**): `getattr` con defecto que `Settings`
  siempre define, `or 0`/`or 1` sin 0 ni 1 posibles, `<=` frente a `<` en valores ya descartados,
  lotes en un `set`... Justificación de cada uno en el informe de mutación.
- Timeouts (8): ninguno cuelga (expresiones sin bucle; lentitud con 4 workers). Dos (t1 redondeo,
  t3 recurso 0) no los cazaba nadie: test nuevo. Sin producción tocada; campaña no relanzada.

## Pendiente y fuera del alcance

- **Cambio de alcance (2026-10-29, líder):** el campo es un campo extendido (`defext`/`conext`),
  no de `res`. El aviso llegó con el análisis de sv5 (ca0545b) y T19 (21bdadf; `azure-apps` 58bce5e)
  ya commiteados: se dejan tal cual, describen `res.<campo>` y pueden cambiar con la enmienda.
- **T20**: que el humano acepte o rechace los 14 equivalentes (si rechaza alguno, test o cambio).
  **T21** (M1b, M2–M4, humano) y **T22** no son de este encargo.
- Con `FRANQUICIA_CAMPO_RES` vacío (defecto), sv5 responde `apagada` y el portal no enseña nada; la
  vista de trabajador hace una llamada a `/recursos` por carga en modo nómina.
- `ruff`: sin avisos nuevos (I001 y `RUF100` de `# noqa: BLE001` ya estaban).
- **Fuera de F-056 (2026-10-28):** reloj de `test_f019_r13_otro_contenido_sube_la_version`, arreglado
  solo en el test (06065ea). Mismo patrón, sin arreglar: `test_f019_portal.py:342`.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests F-056 sv5 (5 ficheros) | 289 passed en 7,64 s |
| Tests F-056 sv4 (`orm`, `franquicia`, `decisiones`, `vista`) | 188 passed en 49,86 s (tras T17b) |
| Raíz (contrato + guardianes del ORM) | 35 passed en 41,94 s |
| Suites enteras sin caché (2026-10-29, tras los tests de mutación) | `python -m pytest -q -p no:cacheprovider` desde cada servicio: sv4 3218 passed, 1 skipped, 2 warnings en 488,43 s; sv3 2345 passed en 23,74 s; sv5 1480 passed en 22,65 s |
| `bash harness/init.sh` (2026-10-29) | **ENTORNO LISTO**. Raíz 529 passed, 3 skipped (116,2 s); sv3 2345 passed (41,3 s); sv4 3218 passed, 1 skipped (1047,6 s); sv5 1480 passed (36,3 s); sv1 y sv2 de caché |
| Cobertura de líneas cambiadas | PUERTA COBERTURA: **98,9 %** (1029/1040, umbral 80 %, nivel crítico) |
| Tamaño | PUERTA TAMAÑO: requirements 150/150, design 248/250, impl 218/220 |
| Mutación | campaña 3ba3403: 513 mutantes, 403 muertos, 102 supervivientes y 8 timeouts. Tras el análisis, 88 supervivientes y 2 timeouts los mata un test nuevo; 14 son candidatos a equivalente, pendientes del humano (`progress/mutacion_F-056.md`) |
| JS y plantilla | `node --check static/app.js` OK; parseo Jinja2 de `trabajador_detail.html` OK; las funciones del modal se EJECUTAN con node en `test_f056_vista.py` |
