<!-- specs/F-047-parte-nuevo-en-espera/tasks.md -->
# F-047 · Parte nuevo «en espera» hasta que sv3 lo reparta — Tareas

## Condiciones de trabajo

- **Rama y worktree**: `feature/F-047-parte-nuevo-en-espera`, en `partes-wt-f047`.
- **Commits**: uno **local** por tarea (`F-047 Tn: …`), añadiendo por rutas
  explícitas (nunca `git add -A`). Sin push ni PR.
- **Rigor crítico**: fase RED con su traza en `progress/impl_F-047.md` para
  R1–R25; cobertura de las líneas cambiadas ≥ umbral; mutación **completa**
  con 0 supervivientes sin test o sin justificación aceptada.
- **Visto bueno previo**: no se empieza sin el del humano a las DA1–DA10
  (`design.md` §11).
- **Cuándo bloquear**: si una tarea obliga a tocar un fichero de `design.md`
  §7 o un test existente, la feature pasa a `blocked` y se consulta (DA8).
- **Datos**: ningún test toca red, Azure, Sigrid ni PostgreSQL. Datos
  sintéticos, sin nombres ni DNIs.
- **Python**: `C:/Users/pgris/PycharmProjects/partes/.venv/Scripts/python.exe`.
  Los tests de un servicio se lanzan desde su carpeta con `-m pytest -q
  <ficheros>`.

## Tareas

- [ ] T1: Test raíz R24 en rojo y comentario del bloque de seguimiento en las dos copias de `orm_models.py` (design §2, byte-idénticas, sin columnas)  |  Verificación: `pytest tests/test_f047_contrato_parte_nuevo.py tests/test_f043_contrato_seguimiento.py tests/test_f010_orm_models_gemelos.py` (raíz) en verde
- [ ] T2: Tests sv3 de `save_parte` (R1, R2, R8, R9) en rojo; parámetro en el puerto y en `sqlalchemy_parte_repository.py`  |  Verificación: `pytest tests/test_f047_parte_nuevo_sv3.py -k "save_parte"` en verde (desde `services/partes-persistencia`)
- [ ] T3: Tests sv3 del pipeline (R3–R7) en rojo; `recalculo_seguimiento` en `PersistPartePipeline`, `_conciliar_recursos_safely` devolviendo `bool` y `_marcar_parte_nuevo`  |  Verificación: `pytest tests/test_f047_parte_nuevo_sv3.py tests/test_f023_pipeline_match.py tests/test_f036_pipeline.py tests/test_f030_casado_recurso.py tests/test_f030_dni_canonico.py` en verde
- [ ] T4: Test R10 en rojo; `interface_adapters/api/app.py` comparte el adaptador con el pipeline, y docstring de `recalculo_seguimiento.py`  |  Verificación: `pytest tests/test_f047_parte_nuevo_sv3.py tests/test_f043_seguimiento_sv3.py tests/test_f042_despacho.py` y suite completa de sv3 en verde
- [ ] T5: Tests sv4 R11–R12 y raíz R25 en rojo; `MOTIVO_NUEVO`, `MOTIVO_RECALCULO` y `motivo_espera` en `seguimiento_recalculo.py`, y `motivos_espera` en el repositorio  |  Verificación: `pytest tests/test_f047_parte_nuevo_sv4.py -k "r11 or r12"` en verde (desde `services/partes-front`) y `pytest tests/test_f047_contrato_parte_nuevo.py` (raíz) en verde
- [ ] T6: Tests R15–R17 en rojo; guarda en `approve_document` (repositorio y ruta), exclusión `recalculando` en `lineas_para_registro` y texto en `_motivo_sin_lineas`  |  Verificación: `pytest tests/test_f047_parte_nuevo_sv4.py tests/test_f022_aprobar_seleccion.py tests/test_f019_portal.py tests/test_f017_aprobacion_firmada.py tests/test_f017_punto_unico.py tests/test_f043_guarda_espera.py` en verde
- [ ] T7: Tests R13, R14 y R18 en rojo; `nuevos` y `recalculando` en el contexto de las cuatro vistas, `data-recalculo-motivo` y la marca «procesando…» en las tres plantillas de detalle, filas de `partes_list.html` y `data-parte-acciones` en `parte_detail.html`  |  Verificación: `pytest tests/test_f047_parte_nuevo_sv4.py tests/test_f043_alcance_y_seguimiento.py tests/test_f028_ancho_detalle.py` en verde
- [ ] T8: Tests (node) R19–R23 en rojo; `var recalculoMotivos = {};` en una línea y los cambios de design §5 en `textoAvisoRecalculo`, `avisoRecalculo`, `ponerEnEspera`, `contenedoresEspera`, `aplicarEstadoRecalculo` y `esperasDeLaPagina`, sin funciones nuevas  |  Verificación: `pytest tests/test_f047_portal_parte_nuevo.py tests/test_f043_portal_fecha.py tests/test_f042_recalculo_fecha.py` en verde y `node --check static/app.js`
- [ ] T9: Comprobar lo que no se toca (design §7)  |  Verificación: `git diff dev --stat -- services/partes-api services/partes-transfer services/partes-email infra CLAUDE.md services/partes-persistencia/interface_adapters/workers services/partes-persistencia/main_worker.py services/partes-persistencia/application/services services/partes-front/application/services/congelacion.py services/partes-front/infrastructure/persistencia services/partes-front/static/styles.css` vacío; `git diff dev --name-status -- services/partes-front/tests services/partes-persistencia/tests tests` solo con líneas `A`
- [ ] T10: Documentación R26: `docs/ARCHITECTURE.md` (semánticas 3, 7 y 10) y `docs/referencia/partes-proyecto.md` (§5, fila «Seguimiento del recálculo», y «El parte en espera»)  |  Verificación: lectura del reviewer; `pytest tests/test_documentos_del_arnes.py` (raíz) en verde
- [ ] T11: `C:/Users/pgris/PycharmProjects/azure-apps/partes.md` (nota de F-043 y fila de las columnas: sv3 también escribe el pedido de un parte nuevo; la aprobación excluye los partes en espera), commit local en ese repositorio (sin push)  |  Verificación: `git -C C:/Users/pgris/PycharmProjects/azure-apps log -1 --stat` muestra solo `partes.md`
- [ ] T12: Cobertura de las líneas cambiadas y campaña de mutación completa `python -m harness.mutacion --feature F-047 --workers 6 --timeout 600` en `progress/mutacion_F-047.md`; cada superviviente matado por un test o justificado para el humano  |  Verificación: informe con 0 supervivientes sin resolver
- [ ] T13: Anotar en `progress/current.md` el despliegue (sv4 → sv3, lo pide el humano) y M1–M3 de `design.md` §10 como pendientes  |  Verificación: MANUAL (humano) — tras `.\redeploy_partes.ps1 -Solo sv4` y `-Solo sv3` desde `infra/`: M1 (portal: parte recién escaneado «procesando…», resto usable, tarjeta «Actualizar» con horas repartidas), M2 (SQL: `id` = `recalculo_pedido_id` = `recalculo_terminado_id`), M3 (Log Analytics: `guardado` y `parte nuevo repartido … marcado=True`)
- [ ] T14: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida en verde
