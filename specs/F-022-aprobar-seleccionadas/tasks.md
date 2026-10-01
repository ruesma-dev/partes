<!-- specs/F-022-aprobar-seleccionadas/tasks.md -->
# F-022 · Aprobar solo las líneas seleccionadas — Tareas

Rama: **`feature/F-022-aprobar-seleccionadas`**. Un commit **local** por tarea,
`F-022 Tn: …`, por rutas explícitas (nunca `git add -A`). Sin push ni PR.
Rigor recomendado **`critico`** (DA14; lo fija el líder en `features.json` al
aprobarse): fase RED con traza en `progress/impl_F-022.md` para **R13, R14,
R15, R17, R18, R20, R21, R22, R24, R25, R29 y R30**; cobertura de líneas
cambiadas ≥ umbral; campaña de mutación **completa** con **0 supervivientes**
sin test o justificación aceptada por el humano. Si se queda en `estandar`,
la campaña es la muestreada de `rigor.json`.

Reglas que no se negocian:

- **No empezar sin DA1–DA18 aprobadas** (`design.md` §8). Si DA1, DA2, DA7,
  DA8 o DA16 cambian, se reescriben R7–R9, R14 o R17–R28 antes de seguir.
- **Ningún test toca red, Sigrid ni PostgreSQL**: SQLite en memoria
  (`tests/dobles.py`, `sembrar_parte` con varios `document_id`, obras y
  personas) y dobles de sv5, publisher y calendario como en
  `test_f024_borrado_sigrid.py` y `test_f003_r23_bloqueo_registro.py`.
  Valores sintéticos; ni nombres ni DNIs reales.
- **Ni una escritura en Sigrid** desde local salvo M2–M6 en modo pruebas.
- Tests de sv4: `cd services/partes-front && ../../.venv/Scripts/python.exe -m pytest -q <ficheros>`.

- [ ] T1: Inventariar los tests de sv4 que comparen el dict entero de `lineas_para_registro` o la forma de las respuestas de `/api/aprobar/*`, o que posten lotes de varias obras o `pisar_claves`, y anotarlos en `progress/impl_F-022.md`  |  Verificación: lista en el informe; ningún fichero de código modificado
- [ ] T2: Tests de repositorio (`registro_ids_de_trabajador`; `grupos` de `lineas_para_registro`: solo líneas que viajan, un grupo por obra en orden de clave, obra del grupo de sus líneas, `[]` sin líneas) en rojo con traza; implementar en `parte_repository.py` y adaptar `test_f024_r22_payload_repo_sin_ids` con nota  |  Verificación: `pytest tests/test_f022_aprobar_seleccion.py -k repo tests/test_f024_borrado_sigrid.py` en verde
- [ ] T3: Tests puros de `reparto_obras.py` (R22 `repartir_claves` con prefijo, sin prefijo y un grupo, sin prefijo y varios → None, grupo desconocido; R19/R20 `agregar_preflight` con uno, varios y uno fallido; R25 `agregar_ejecucion` con todos bien, parcial y bloqueado) en rojo; implementar  |  Verificación: `pytest tests/test_f022_reparto_obras.py` en verde
- [ ] T4: Tests de `ambito` (R13 obra y persona; R14 id de otra obra, periodo, persona, papelera o inexistente → 422 `fuera_de_ambito` sin sv5, sin publicar ni marcar; R15 vista desconocida, clave ausente, ids vacíos, 5001 ids; R16 sin `ambito` como hoy) en rojo; implementar `_validar_ambito` en `_preparar_registro`  |  Verificación: `pytest tests/test_f022_aprobar_seleccion.py -k ambito` en verde
- [ ] T5: Tests de preflight por grupo (R17 dos obras → dos llamadas a sv5, cada una con su `obra` y solo sus líneas; R18 once obras → 422 sin sv5; R19 planos idénticos a hoy con un grupo; R20 un grupo con `ok:false` y el otro sigue; R21 Sesame no fiable solo en un grupo bloquea solo ese; R29 avisos solo de lo pedido) en rojo; implementar en `app.py` y `APROBACION_MAX_OBRAS` en `settings.py`  |  Verificación: `pytest tests/test_f022_aprobar_seleccion.py -k preflight` en verde
- [ ] T6: Tests de ejecutar por grupo (R22 claves repartidas y 422 sin prefijo con varios grupos; R25 grupos en orden, traza por grupo, un grupo `ok:false` deja en `error` solo sus líneas, `parcial`; R21 bloqueado sin override no se ejecuta y todos bloqueados → 422 de hoy, con override `[SIN-SESAME]` solo en los bloqueados) en rojo; implementar  |  Verificación: `pytest tests/test_f022_aprobar_seleccion.py -k ejecutar` en verde
- [ ] T7: Tests de encolar por grupo (R23 una publicación por grupo con su obra, `encolado` por grupo, `peticiones` y `registro_ids`; R24 publicar falla en un grupo → `error_cola` sin marcar sus líneas y el resto sigue, todos fallan → 502 sin marcas; sin publisher → síncrono por grupo; R30 lo no pedido conserva `sigrid_estado` y `sigrid_motivo`; R31 claves de cada payload y de cada publicación = `obra, lineas, pisar_claves, usuario`) en rojo; implementar  |  Verificación: `pytest tests/test_f022_aprobar_seleccion.py -k encolar` en verde
- [ ] T8: Tests de HTML (R1 casilla `sel-linea` con `data-registro-id` en cada fila de obra y persona, también congelada; `data-sel-visibles`, `data-sel-ninguna`, contador; `#aprobar-todo` con `data-vista` y `data-obra-key/period/mode` o `data-worker-key`; R12 `aprobar-linea` intactos) en rojo; cambiar las dos plantillas  |  Verificación: `pytest tests/test_f022_vistas_seleccion.py -k vista` en verde y parseo Jinja2 de las dos plantillas
- [ ] T9: `static/app.js` y `styles.css` según design §5.4 (selección global con casillas y visibles, contador, `lineas:cambio`, botón dinámico, `{registro_ids, ambito}`, modal por obra con total, claves `<grupo>::<clave>`, confirmación partida entre `ejecutar` y `encolar`, resultado y sondeo por grupo, obras sin registrar); estáticos mínimos de R5, R10, R12 y del prefijo de claves en `test_f022_vistas_seleccion.py -k js`  |  Verificación: `node --check services/partes-front/static/app.js` y `pytest tests/test_f022_vistas_seleccion.py` en verde; navegador MANUAL (humano, design §9 M2–M6)
- [ ] T10: `docs/ARCHITECTURE.md` (semánticas 5 y 10, ≤ 8 líneas netas)  |  Verificación: lectura del reviewer contra design §4
- [ ] T11: `C:\Users\pgris\PycharmProjects\azure-apps\partes.md`: selección explícita y una petición `q-transfer` por obra; commit local en ese repositorio, sin push  |  Verificación: `git -C C:/Users/pgris/PycharmProjects/azure-apps log -1` muestra el commit
- [ ] T12: Suite completa de sv4, suite de sv5 (sin cambios) y tests de raíz en verde (R32), con la lista de T1 adaptada y anotada  |  Verificación: salida de los tres comandos pegada en `progress/impl_F-022.md`
- [ ] T13: Cobertura de líneas cambiadas y campaña de mutación (completa si `critico`) sobre `reparto_obras.py`, `app.py` y `parte_repository.py` en `progress/mutacion_F-022.md`, con cada superviviente muerto o justificado  |  Verificación: informe con SHA de HEAD y 0 supervivientes sin resolver
- [ ] T14: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida en verde; pendientes MANUAL (M1–M7 de design §9 y la parte de navegador de T9) anotados en `progress/current.md`
