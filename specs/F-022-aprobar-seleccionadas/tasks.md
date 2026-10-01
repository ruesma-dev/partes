<!-- specs/F-022-aprobar-seleccionadas/tasks.md -->
# F-022 · Aprobar solo las líneas seleccionadas — Tareas

Rama: **`feature/F-022-aprobar-seleccionadas`**. Un commit **local** por tarea,
`F-022 Tn: …`, por rutas explícitas (nunca `git add -A`). Sin push ni PR.
Rigor **`critico`** (DA14): fase RED con traza en `progress/impl_F-022.md`
para **R10, R11, R12, R14, R15, R17, R18, R19, R21, R22, R23, R24, R31 y
R32**; cobertura de líneas cambiadas ≥ umbral; campaña de mutación
**completa** con **0 supervivientes** sin test o justificación aceptada por el
humano.

Reglas que no se negocian:

- **DA1–DA18 aprobadas el 2026-10-01; DA19 (listado) según la recomendación
  de `design.md` §8** salvo que el humano diga otra cosa: si cambia, se
  reescriben R23–R28 antes de T6.
- **Ningún test toca red, Sigrid ni PostgreSQL**: SQLite en memoria
  (`tests/dobles.py`, `sembrar_parte` con varios `document_id`, obras y
  personas) y dobles de sv5, publisher y calendario como en
  `test_f024_borrado_sigrid.py` y `test_f003_r23_bloqueo_registro.py`.
  Valores sintéticos; ni nombres ni DNIs reales.
- **Ni una escritura en Sigrid** desde local salvo M2–M7 en modo pruebas.
- Tests de sv4: `cd services/partes-front && ../../.venv/Scripts/python.exe -m pytest -q <ficheros>`.

- [x] T1: Inventariar los tests de sv4 que comparen el dict entero de `lineas_para_registro` o la forma de las respuestas de `/api/aprobar/*`, o que posten lotes de varias obras o `pisar_claves`, y anotarlos en `progress/impl_F-022.md`  |  Verificación: lista en el informe; ningún fichero de código modificado
- [x] T2: Tests de repositorio (`registro_ids_de_trabajador`; `grupos` de `lineas_para_registro`: solo líneas que viajan, un grupo por obra en orden de clave, obra y `estado_previo` del grupo, `[]` sin líneas; `excluidas_detalle` con estado y parte) en rojo con traza; implementar en `parte_repository.py` y adaptar `test_f024_r22_payload_repo_sin_ids` con nota  |  Verificación: `pytest tests/test_f022_aprobar_seleccion.py -k repo tests/test_f024_borrado_sigrid.py` en verde
- [x] T3: Tests puros de `reparto_obras.py` para `repartir_claves` (R19), `agregar_preflight` (R16, R17) y `agregar_ejecucion` (R22: todos bien, parcial, bloqueado) en rojo; implementarlos  |  Verificación: `pytest tests/test_f022_reparto_obras.py -k "claves or agregar"` en verde
- [x] T4: Tests puros de `listado_grupo` y `totales` (R23 columnas y orden; R24 cada `estado`: conflicto, omitida, ya_registrada, nuevo, reaprobacion por cada estado previo, no_se_registra; código, partida, recurso y horas de la acción de sv5 frente a los de la línea; incidencia con 0 h; R25 horas solo de lo que se escribe) en rojo; implementarlos  |  Verificación: `pytest tests/test_f022_reparto_obras.py -k "listado or totales"` en verde
- [x] T5: Tests de `ambito` (R10 obra y persona; R11 id de otra obra, periodo, persona, papelera o inexistente → 422 `fuera_de_ambito` sin sv5, sin publicar ni marcar; R12 vista desconocida, clave ausente, ids vacíos, 5001 ids; R13 sin `ambito` como hoy) en rojo; implementar `_validar_ambito` en `_preparar_registro`  |  Verificación: `pytest tests/test_f022_aprobar_seleccion.py -k ambito` en verde
- [x] T6: Tests de preflight por grupo (R14 dos obras → dos llamadas a sv5, cada una con su `obra` y solo sus líneas; R15 once obras → 422; R16 planos idénticos a hoy con un grupo; R17 grupo fallido y el otro sigue; R18 Sesame no fiable solo en un grupo; R23–R26 `listado`, `totales`, `excluidas_detalle` y `umbral_plegado` en la respuesta; R31 avisos y bloqueo solo de lo pedido) en rojo; implementar en `app.py` y `APROBACION_MAX_OBRAS` en `settings.py`  |  Verificación: `pytest tests/test_f022_aprobar_seleccion.py -k preflight` en verde
- [x] T7: Tests de ejecutar por grupo (R19 claves repartidas y 422 sin prefijo con varios grupos; R22 orden, traza por grupo, un grupo `ok:false` deja en `error` solo sus líneas, `parcial`; R18 bloqueado sin override no se ejecuta, todos bloqueados → 422 de hoy, override `[SIN-SESAME]` solo en los bloqueados) en rojo; implementar  |  Verificación: `pytest tests/test_f022_aprobar_seleccion.py -k ejecutar` en verde
- [x] T8: Tests de encolar por grupo (R20 una publicación por grupo con su obra, `encolado` por grupo, `peticiones` y `registro_ids`; R21 fallo al publicar un grupo → `error_cola` sin marcar, todos → 502 sin marcas; sin publisher → síncrono por grupo; R32 lo no pedido conserva `sigrid_estado` y `sigrid_motivo`; R33 claves de cada payload y publicación = `obra, lineas, pisar_claves, usuario`, sin listado) en rojo; implementar  |  Verificación: `pytest tests/test_f022_aprobar_seleccion.py -k encolar` en verde
- [x] T9: Tests de HTML (R1 casilla `sel-linea` con `data-registro-id` en cada fila de obra y persona, también congelada; `data-sel-visibles`, `data-sel-ninguna`, contador; `#aprobar-todo` con `data-vista` y `data-obra-key/period/mode` o `data-worker-key`; R9 `aprobar-linea` intactos) en rojo; cambiar las dos plantillas  |  Verificación: `pytest tests/test_f022_vistas_seleccion.py -k vista` en verde y parseo Jinja2 de las dos plantillas
- [x] T10: `static/app.js` y `styles.css` según design §5.4: selección (R1–R5), botón (R6–R8), modal con alcance, total, `<details>` por obra plegados por encima de `umbral_plegado`, tabla del listado con cabecera fija, conflictos y errores fuera del pliegue, «Excluidas (N)» y ocultas (R26–R28), confirmación y resultado por grupo (R29, R30); estáticos mínimos (R4, R8, R9, prefijo de claves y uso de `grupos[].listado`) en `test_f022_vistas_seleccion.py -k js`  |  Verificación: `node --check services/partes-front/static/app.js` y `pytest tests/test_f022_vistas_seleccion.py` en verde; navegador MANUAL (humano, design §9 M2–M7)
- [x] T11: `docs/ARCHITECTURE.md` (semánticas 5 y 10, ≤ 8 líneas netas)  |  Verificación: lectura del reviewer contra design §4
- [x] T12: `C:\Users\pgris\PycharmProjects\azure-apps\partes.md`: selección explícita y una petición `q-transfer` por obra; commit local en ese repositorio, sin push  |  Verificación: `git -C C:/Users/pgris/PycharmProjects/azure-apps log -1` muestra el commit
- [ ] T13: Suite completa de sv4, suite de sv5 (sin cambios) y tests de raíz en verde (R34), con la lista de T1 adaptada y anotada  |  Verificación: salida de los tres comandos pegada en `progress/impl_F-022.md`
- [ ] T14: Cobertura de líneas cambiadas y campaña de mutación completa sobre `reparto_obras.py`, `app.py` y `parte_repository.py` en `progress/mutacion_F-022.md`, con cada superviviente muerto por un test o justificado para el humano  |  Verificación: informe con SHA de HEAD y 0 supervivientes sin resolver
- [ ] T15: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida en verde; pendientes MANUAL (M1–M8 de design §9 y la parte de navegador de T10) anotados en `progress/current.md`
