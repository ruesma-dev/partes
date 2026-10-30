<!-- specs/F-047-parte-nuevo-en-espera/tasks.md -->
# F-047 · Parte nuevo «en espera» hasta que sv3 lo reparta — Tareas

## Condiciones de trabajo

- **Rama y worktree**: `feature/F-047-parte-nuevo-en-espera`, en `partes-wt-f047`.
- **Commits**: uno **local** por tarea (`F-047 Tn: …`), añadiendo por rutas
  explícitas (nunca `git add -A`). Sin push ni PR.
- **Rigor crítico**: fase RED con su traza en `progress/impl_F-047.md` para
  R1–R25; cobertura de las líneas cambiadas ≥ umbral; mutación **completa**
  con 0 supervivientes sin test o sin justificación aceptada.
- **Visto bueno previo**: DA1–DA10 aprobadas el 2026-10-14; DA11–DA13 = A
  aprobadas el 2026-10-30 (literal: «ok»; `design.md` §11).
- **Cuándo bloquear**: si una tarea obliga a tocar un fichero de `design.md`
  §7 o un test existente, la feature pasa a `blocked` y se consulta (DA8).
- **Datos**: ningún test toca red, Azure, Sigrid ni PostgreSQL. Datos
  sintéticos, sin nombres ni DNIs.
- **Python**: `C:/Users/pgris/PycharmProjects/partes/.venv/Scripts/python.exe`.
  Los tests de un servicio se lanzan desde su carpeta con `-m pytest -q
  <ficheros>`.

## Tareas

- [x] T1: Test raíz R24 en rojo y comentario del bloque de seguimiento en las dos copias de `orm_models.py` (design §2, byte-idénticas, sin columnas)  |  Verificación: `pytest tests/test_f047_contrato_parte_nuevo.py tests/test_f043_contrato_seguimiento.py tests/test_f010_orm_models_gemelos.py` (raíz) en verde
- [x] T2: Tests sv3 de `save_parte` (R1, R2, R8, R9) en rojo; parámetro en el puerto y en `sqlalchemy_parte_repository.py`  |  Verificación: `pytest tests/test_f047_parte_nuevo_sv3.py -k "save_parte"` en verde (desde `services/partes-persistencia`)
- [x] T3: Tests sv3 del pipeline (R3–R7) en rojo; `recalculo_seguimiento` en `PersistPartePipeline`, `_conciliar_recursos_safely` devolviendo `bool` y `_marcar_parte_nuevo`  |  Verificación: `pytest tests/test_f047_parte_nuevo_sv3.py tests/test_f023_pipeline_match.py tests/test_f036_pipeline.py tests/test_f030_casado_recurso.py tests/test_f030_dni_canonico.py tests/test_f051_lectura_dudosa.py tests/test_f054_revision_cabecera.py tests/test_f048_conciliar.py` en verde
- [x] T4: Test R10 en rojo; `interface_adapters/api/app.py` comparte el adaptador con el pipeline, y docstring de `recalculo_seguimiento.py`  |  Verificación: `pytest tests/test_f047_parte_nuevo_sv3.py tests/test_f043_seguimiento_sv3.py tests/test_f042_despacho.py tests/test_f049_pedido_compartido.py` y suite completa de sv3 en verde
- [x] T5: Tests sv4 R11–R12 y raíz R25 en rojo; `MOTIVO_NUEVO`, `MOTIVO_RECALCULO` y `motivo_espera` en `seguimiento_recalculo.py`, y `motivos_espera` en el repositorio  |  Verificación: `pytest tests/test_f047_parte_nuevo_sv4.py -k "r11 or r12"` en verde (desde `services/partes-front`) y `pytest tests/test_f047_contrato_parte_nuevo.py` (raíz) en verde
- [ ] T6: Tests R15–R17 en rojo; guarda en `approve_document` (repositorio y ruta), exclusión `recalculando` en `lineas_para_registro` y texto en `_motivo_sin_lineas`  |  Verificación: `pytest tests/test_f047_parte_nuevo_sv4.py tests/test_f022_aprobar_seleccion.py tests/test_f019_portal.py tests/test_f017_aprobacion_firmada.py tests/test_f017_punto_unico.py tests/test_f043_guarda_espera.py tests/test_f046_aprobar_documento.py tests/test_f046_aplicar.py tests/test_f025_aprobacion.py tests/test_f024_borrado_sigrid.py tests/test_f060_aprobacion_racha.py tests/test_f062_inicio_con_ciz.py tests/test_f004_endpoints_congelados.py` en verde
- [ ] T7: Tests R13, R14 y R18 en rojo; `nuevos` y `recalculando` en el contexto de las cuatro vistas, `data-recalculo-motivo` y la marca «procesando…» en las tres plantillas de detalle, filas de `partes_list.html` y `data-parte-acciones` en `parte_detail.html`  |  Verificación: `pytest tests/test_f047_parte_nuevo_sv4.py tests/test_f043_alcance_y_seguimiento.py tests/test_f028_ancho_detalle.py tests/test_f061_portal.py tests/test_f064_clave_usuario.py tests/test_f050_vistas.py` en verde
- [ ] T8: Tests (node) R19–R23 en rojo; `var recalculoMotivos = {};` en una línea y los cambios de design §5 en `textoAvisoRecalculo`, `avisoRecalculo`, `ponerEnEspera`, `contenedoresEspera`, `aplicarEstadoRecalculo` y `esperasDeLaPagina`, sin funciones nuevas  |  Verificación: `pytest tests/test_f047_portal_parte_nuevo.py tests/test_f043_portal_fecha.py tests/test_f042_recalculo_fecha.py tests/test_f064_filtros_js.py tests/test_f049_editor_js.py` en verde y `node --check static/app.js`
- [ ] T9: Comprobar lo que no se toca (design §7)  |  Verificación: `git diff dev --stat -- services/partes-api services/partes-transfer services/partes-email infra CLAUDE.md services/partes-persistencia/interface_adapters/workers services/partes-persistencia/main_worker.py services/partes-persistencia/application/services services/partes-front/application/services/congelacion.py services/partes-front/infrastructure/persistencia services/partes-front/static/styles.css` vacío; `git diff dev --name-status -- services/partes-front/tests services/partes-persistencia/tests tests` solo con líneas `A`
- [ ] T10: Documentación R26: `docs/ARCHITECTURE.md` (semánticas 3, 7 y 10) y `docs/referencia/partes-proyecto.md` (§5, fila «Seguimiento del recálculo», y «El parte en espera»)  |  Verificación: lectura del reviewer; `pytest tests/test_documentos_del_arnes.py` (raíz) en verde
- [ ] T11: `C:/Users/pgris/PycharmProjects/azure-apps/partes.md` (nota de F-043 y fila de las columnas: sv3 también escribe el pedido de un parte nuevo; la aprobación excluye los partes en espera), commit local en ese repositorio (sin push)  |  Verificación: `git -C C:/Users/pgris/PycharmProjects/azure-apps log -1 --stat` muestra solo `partes.md`
- [ ] T12: Cobertura de las líneas cambiadas y campaña de mutación completa `python -m harness.mutacion --feature F-047 --workers 6 --timeout 600` en `progress/mutacion_F-047.md`; cada superviviente matado por un test o justificado para el humano  |  Verificación: informe con 0 supervivientes sin resolver
- [ ] T13: Anotar en `progress/current.md` el despliegue (sv4 → sv3, lo pide el humano) y M1–M3 como pendientes  |  Verificación: MANUAL (humano) — en DOS llamadas desde `infra/`, primero `.\redeploy_partes.ps1 -Solo sv4` y después `-Solo sv3` (juntas, el script fija sv3 antes que sv4): M1 (portal, parte escaneado de prueba: en los primeros segundos su obra dice «procesando…» y no se edita, el resto sí; al terminar, «Actualizar» ⇒ horas repartidas), M2 (base `partes`, solo lectura: `SELECT id, recalculo_pedido_id, recalculo_terminado_id FROM parte_documents WHERE id = '<id de M1>';` ⇒ los tres iguales), M3 (Log Analytics de sv3: `[parte-repo] guardado` y `parte nuevo repartido … marcado=True` del mismo `document_id`; la diferencia de horas entre ambas es la espera real y revalida la cifra de 20–40 s)
- [ ] T14: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida en verde

## Revalidación 2026-10-30 (contra `dev` 75816f2, merge 795a546)

Cambios **mecánicos** (mismo comportamiento aprobado; detalle en
`progress/explore_F-047_revalidacion.md`):

- design §3: `marcar_terminado` filtra por pedido desde F-049 (R41); con pedido = id sigue tocando solo ese parte (R7 igual). Su docstring ya nombra F-047: solo cambia el del módulo.
- design §3: `conciliar_todos` corre bajo el candado de F-046; su `TimeoutError` es una excepción más ⇒ R5.
- design §4: `approve_document` ya carga el documento (F-046): la guarda va en ese bloque, detrás de la del reparto.
- design §4: la ruta ya tiene `except RepartoPendienteError`; pasa a `except CongeladoError` (cubre las dos).
- design §4: `lineas_para_registro` tiene ya `reparto_pendiente` (F-046) entre `dedicacion` y la incompatibilidad; la exclusión nueva va detrás de él.
- design §4: las vistas calculan `recalculando` dentro del dict de contexto; se saca a una variable.
- design §4 y DA8: `_actor(request)` cuenta 20 (no 17).
- design §5: F-064 fija la huella de `restaurarVista` y `actualizarVista` (que F-047 no toca); T8 corre `test_f064_filtros_js.py`.
- design §6: `FabricaSesionSqlite` y `sembrar_parte` viven en `tests/dobles.py` de sv4.
- design §9 R-e: F-044/F-045/F-046 ya están en `dev`; el riesgo de merge es F-057 (`spec_ready`).
- design §10 → T13 (M1–M3 enteros allí; M3 vuelve a medir la espera).
- T3, T4, T6, T7 y T8: añadidos los tests existentes que hoy tocan el mismo código (F-046, F-048, F-049, F-050, F-051, F-054, F-060–F-062, F-064).
- T13: dos llamadas a `redeploy_partes.ps1` (el script ordena sv3 antes que sv4).

**Decisiones abiertas nuevas**: DA11 (matriz de la obra, F-049), DA12 (parte sin obra o sin fecha, F-054) y DA13 (candado de F-046 y texto de R19), en `design.md` §11.
