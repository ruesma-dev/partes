<!-- specs/F-058-relectura-cabecera-gemini/tasks.md -->
# F-058 · Relectura de la cabecera vacía con Gemini — tareas

> Antes de T1, el humano resuelve DA1–DA8 (`design.md` §10); las tareas suponen la
> recomendación. Si DA5 = B, T5 cambia el valor por defecto a `false` y M0 incluye el
> `az containerapp update` que ejecuta el humano. Cada tarea = un commit `F-058 Tn: ...`,
> con rutas explícitas. Las rutas sin prefijo son de `services/partes-api/`.

- [ ] T1: Escribir los tests puros de `tests/test_f058_relectura_cabecera.py` (R2–R4: `es_vacio`, `cabecera_vacia`, `necesita_relectura`, `relectura_util`) y verlos en ROJO  |  Verificación: `cd services/partes-api && python -m pytest tests/test_f058_relectura_cabecera.py` falla por el módulo ausente (traza RED en `progress/impl_F-058.md`)
- [ ] T2: Crear `application/services/relectura_cabecera.py` según `design.md` §4.1  |  Verificación: los tests puros de T1 en verde
- [ ] T3: Añadir a `tests/test_f058_relectura_cabecera.py` los tests del pipeline con dobles (R1, R5–R14, casos de `design.md` §7) y verlos en ROJO  |  Verificación: `python -m pytest tests/test_f058_relectura_cabecera.py` falla en los casos del pipeline (traza RED)
- [ ] T4: Implementar la relectura en `application/pipelines/extract_parte_pipeline.py` (kwarg `relectura_provider`, `_releer_cabecera`, `_envelope` desde `data`) y `ParteExtractionService.model_name` en `application/services/parte_extraction_service.py` (§4.2, §4.3)  |  Verificación: `python -m pytest` de sv2 en verde, con `test_f023_*` y `test_f051_*` sin tocar
- [ ] T5: Escribir `tests/test_f058_settings_wiring.py` (R15–R18: `Settings` con `_env_file=None`, `build_app` con SDK falsos en `sys.modules`, `/health` con `TestClient`) y verlo en ROJO  |  Verificación: `python -m pytest tests/test_f058_settings_wiring.py` falla (traza RED)
- [ ] T6: Añadir `RELECTURA_CABECERA`, `RELECTURA_CABECERA_PROVIDER`, `relectura_cabecera_activa` y `relectura_cabecera_motivo_inactiva` a `config/settings.py` (§5) y el cableado, el log y `/health` a `interface_adapters/api/app.py` (§6)  |  Verificación: `python -m pytest` de sv2 en verde
- [ ] T7: Actualizar los docstrings que dicen «un solo proveedor» / «Gemini primario» (`config/settings.py`, `parte_extraction_service.py`, `extract_parte_pipeline.py`, `main_worker.py`)  |  Verificación: revisión del reviewer; `python -m pytest` de sv2 en verde
- [ ] T8: Documentar en `docs/ARCHITECTURE.md` el punto 18 (relectura de la cabecera, F-058, sv2) y la línea «Google Gemini (sv2)» de «Acceso a datos»  |  Verificación: revisión del reviewer; `python -m harness.tamano --feature F-058` en verde
- [ ] T9: Actualizar el comentario de sv2 en `infra/create_capps_partes.ps1` (l. 38–39; sin BOM y CRLF, sin variables nuevas)  |  Verificación: `git diff dev -- infra/create_capps_partes.ps1` solo cambia comentarios; encoding comprobado con `file infra/create_capps_partes.ps1`
- [ ] T10: Actualizar `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (fila de sv2, l. 927, y §3.2): sv2 consume Gemini para la relectura; commit local en ese repositorio con ruta explícita  |  Verificación: `git -C C:\Users\pgris\PycharmProjects\azure-apps log -1 --stat` muestra solo `partes.md`
- [ ] T11: Campaña de mutación muestreada (rigor `estandar`) y análisis de supervivientes en `progress/impl_F-058.md`  |  Verificación: `python -m harness.mutacion --feature F-058` con el nivel de `harness/rigor.json`, supervivientes documentados
- [ ] T12: M0 · comprobar en solo lectura el entorno de `ca-sv2-extraccion` (`design.md` §9)  |  Verificación: MANUAL (humano o líder), comando `az containerapp show` de §9; si falta Gemini, `blocked`
- [ ] T13: M1 · pipeline de la rama sobre las 6 páginas sin cabecera y las 2 de control, sin escrituras  |  Verificación: MANUAL (humano o líder), §9; esperado 6/6 `aplicada` con filas idénticas y control sin relectura
- [ ] T14: M2 · tras desplegar sv2 (lo pide el humano), recuento de `meta.relectura_cabecera.resultado` en las ingestas nuevas  |  Verificación: MANUAL (humano), SELECT de §9 en transacción READ ONLY
- [ ] T15: M3 · los 6 documentos ya guardados según la DA8 (por defecto, corrección en el portal)  |  Verificación: MANUAL (humano); la alternativa B solo con autorización expresa y el SELECT previo de §9
- [ ] T16: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida «ENTORNO LISTO»
