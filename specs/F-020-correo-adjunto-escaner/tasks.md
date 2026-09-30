<!-- specs/F-020-correo-adjunto-escaner/tasks.md -->
# F-020 · sv1: correos adjuntos encadenados hasta el PDF — Tareas

Rama: **`feature/F-020-correo-adjunto-escaner`** (ya creada; no se crea otra).
Un commit **local** por tarea, `F-020 Tn: …`, por rutas explícitas (nunca
`git add -A`). Sin `git push` ni PR. Rigor **`estandar`**: fase RED con traza
en `progress/impl_F-020.md` para **R1, R10, R17 y R20**, cobertura de líneas
cambiadas ≥ umbral y campaña de mutación muestreada con supervivientes
analizados.

Reglas que no se negocian:

- **Solo `services/partes-email/`** y la subsección de `docs/ARCHITECTURE.md`.
  Nada de sv2/sv3/sv4/sv5/`infra/`: si parece necesario, `blocked` y parar.
- **Ningún test toca red ni Graph**; los `.eml` se construyen en el test. Ni
  datos reales (direcciones, nombres, DNIs, PDFs del buzón) en tests ni informes.
- **La sonda ya está hecha** (`progress/explore_F-020_sonda.md`): no se vuelve
  a llamar a Graph desde el implementer.
- Prerrequisito **D1** (`design.md` §9): `pypdf` instalado en el `.venv` de la
  raíz con autorización del humano. Si no lo está al empezar: `blocked`.

- [x] T1: Comprobar el prerrequisito D1 y crear `tests/conftest.py`, `tests/eml_sinteticos.py` y `tests/dobles.py` (design §8)  |  Verificación: `cd services/partes-email && ../../.venv/Scripts/python.exe -m pytest -q` recoge 0 tests sin error de importación
- [x] T2: Modelos de dominio `CorreoEmbebido`, `PdfEmbebido`, `ExtraccionCorreoAdjunto` y puerto `extractor_correo_adjunto.py` (design §6.1–6.2), con su test `test_f020_r17_to_context_*` en `test_f020_extractor_mime.py`  |  Verificación: `pytest tests/test_f020_extractor_mime.py -k to_context` en verde
- [x] T3: Tests del extractor (R7–R13) en rojo, con traza RED de R10  |  Verificación: `pytest tests/test_f020_extractor_mime.py` falla por ausencia de `MimePdfExtractor`
- [x] T4: Implementar `infrastructure/document/mime_pdf_extractor.py` (design §6.2)  |  Verificación: `pytest tests/test_f020_extractor_mime.py` en verde
- [x] T5: Test de no regresión del contexto de PDF directo (R18) sobre el código ACTUAL, antes de tocar el pipeline; construye el pipeline por un helper de `tests/dobles.py` (en T7 solo cambia el helper, no el test)  |  Verificación: `pytest tests/test_f020_contexto_pdf_directo.py` en verde contra `polling_pipeline.py` sin modificar
- [ ] T6: Tests de clasificación y de pipeline (R1–R6, R14–R17, R19–R24) en rojo, con traza RED de R1, R17 y R20  |  Verificación: `pytest tests/test_f020_clasificacion_adjuntos.py tests/test_f020_pipeline_correo_adjunto.py` falla por los motivos esperados
- [ ] T7: Modificar `polling_pipeline.py` (design §6.3) y el docstring de `mailbox_client.py`  |  Verificación: T5 y T6 en verde
- [ ] T8: Test de cableado (R25) y cambio de `main.py` (design §6.4)  |  Verificación: `pytest tests/test_f020_wiring_main.py` en verde
- [ ] T9: Subsección «Ingesta de sv1: correos adjuntos (F-020)» en `docs/ARCHITECTURE.md` (≤ 10 líneas)  |  Verificación: lectura del reviewer contra design §6.3
- [ ] T10: Cobertura y campaña de mutación de la feature; supervivientes analizados en `progress/impl_F-020.md`  |  Verificación: `python -m harness.mutacion` según `harness/rigor.json` (nivel estandar)
- [ ] T11: Anotar en `progress/current.md` la verificación MANUAL de design §10 (reprocesar un correo del escáner tras desplegar) como pendiente del humano  |  Verificación: MANUAL (humano) — mover un correo de `Errores` a la carpeta origen, marcarlo no leído y comprobar logs de `ca-sv1-poller`, `Procesados` y el parte en el portal
- [ ] T12: Ejecutar `bash harness/init.sh` en verde, con la línea «servicio sv1-email (services/partes-email): pytest en verde» (R26)  |  Verificación: `bash harness/init.sh`
