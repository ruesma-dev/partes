<!-- specs/F-059-pagina-como-imagen-derecha/tasks.md -->
# F-059 · La IA no lee bien el PDF con /Rotate: la página va ya derecha — tareas

> Antes de T1, el humano resuelve DA1–DA4 (`design.md` §7). Con otra respuesta
> que la recomendada, se ajustan los defectos de T6 y se anota en
> `progress/impl_F-059.md`. Cada tarea = un commit `F-059 Tn: ...`.

- [x] T1: Instalar Pillow en el `.venv` de la raíz (`python -m pip install "Pillow>=10.0"`) y añadir `pypdf>=4.2` y `Pillow>=10.0` a `infra/manifests/sv2/requirements.txt`  |  Verificación: `python -c "import PIL, pypdf"` sin error; `git diff dev -- infra/manifests/sv2/requirements.txt` solo añade esas dos líneas
- [x] T2: Escribir `services/partes-api/tests/f059_pdf_sinteticos.py` y `tests/test_f059_conversor.py` (R1–R10, `design.md` §8) y verlos en ROJO  |  Verificación: `cd services/partes-api && python -m pytest tests/test_f059_conversor.py` falla por el módulo ausente (traza RED en impl)
- [ ] T3: Crear `domain/models/conversion_adjunto.py`, `domain/ports/conversor_pagina.py` e `infrastructure/document/pagina_pdf_imagen.py` según `design.md` §4 bis y §5  |  Verificación: `python -m pytest tests/test_f059_conversor.py` en verde
- [ ] T4: Escribir `tests/test_f059_pipeline.py` (R11–R19) y verlo en ROJO  |  Verificación: `python -m pytest tests/test_f059_pipeline.py` falla (traza RED en impl)
- [ ] T5: Añadir `conversor`, `proveedores_imagen`, `_preparar_para_ia` y `meta.adjunto_ia` a `application/pipelines/extract_parte_pipeline.py` (`design.md` §6)  |  Verificación: `python -m pytest tests/test_f059_pipeline.py tests/test_f023_empresa_membrete.py tests/test_f051_esquema.py tests/test_f051_prompt.py` en verde
- [ ] T6: Escribir `tests/test_f059_config.py` (R20–R22, R24), verlo en ROJO y después añadir `PAGINA_COMO_IMAGEN`, `PAGINA_COMO_IMAGEN_PROVEEDORES` y `OPENAI_IMAGE_DETAIL` a `config/settings.py`, `image_detail` a `openai_responses_client.py` y el cableado en `interface_adapters/api/app.py`  |  Verificación: `cd services/partes-api && python -m pytest` en verde (traza RED en impl)
- [ ] T7: Documentar la semántica 19 en `docs/ARCHITECTURE.md` y actualizar la fila de sv2 de `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (qué manda a la IA, variables nuevas, dependencias), con commit local en ese repositorio  |  Verificación: revisión del reviewer; `python -m harness.tamano --feature F-059` en verde
- [ ] T8: Campaña de mutación muestreada (rigor `estandar`) sobre `infrastructure/document/pagina_pdf_imagen.py` y `application/pipelines/extract_parte_pipeline.py`; supervivientes analizados en `progress/impl_F-059.md`  |  Verificación: `python -m harness.mutacion` con el nivel de `harness/rigor.json`
- [ ] T9: M0–M3 en el banco del líder con el código de la rama (`design.md` §9); tablas sin nombres ni DNIs en `progress/banco_F-059.md`  |  Verificación: MANUAL (líder): M0 22/22 `convertida`; M1 12/12; M2 4/4; M3 sin regresión frente a PDF. Si no, `blocked`
- [ ] T10: M4 tras desplegar sv2 (`redeploy_partes.ps1 -Solo sv2`, lo lanza el humano): `meta.adjunto_ia.conversion` de las ingestas nuevas  |  Verificación: MANUAL (humano), SELECT de solo lectura sobre `raw_extraction_json` en la base `partes`
- [ ] T11: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida «ENTORNO LISTO»
