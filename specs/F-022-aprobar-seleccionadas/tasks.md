<!-- specs/F-022-aprobar-seleccionadas/tasks.md -->
# F-022 · Aprobar solo las líneas seleccionadas — Tareas

Rama: **`feature/F-022-aprobar-seleccionadas`** (ya creada desde `dev`). Un
commit **local** por tarea, `F-022 Tn: …`, por rutas explícitas (nunca
`git add -A`). Sin push ni PR. Rigor **`estandar`**: fase RED con traza en
`progress/impl_F-022.md` para **R13, R14, R15, R17, R19 y R20**; cobertura de
líneas cambiadas ≥ umbral; mutación muestreada (20, semilla de `rigor.json`).

Reglas que no se negocian:

- **No empezar sin DA1–DA14 aprobadas** (`design.md` §8). Si DA1, DA2, DA7 u
  DA8 cambian, se reescriben R7–R9, R14 o R17 antes de seguir.
- **Ningún test toca red, Sigrid ni PostgreSQL**: SQLite en memoria
  (`tests/dobles.py`, `sembrar_parte` con varios `document_id`/obras/personas)
  y dobles de sv5 y publisher como en `test_f024_borrado_sigrid.py`. Valores
  sintéticos; ni nombres ni DNIs reales.
- **Ni una escritura en Sigrid** desde local salvo M2–M6 en modo pruebas.
- Tests de sv4: `cd services/partes-front && ../../.venv/Scripts/python.exe -m pytest -q <ficheros>`.

- [ ] T1: Inventariar los tests de sv4 que posten a `/api/aprobar/*` lotes de varias obras o comparen el dict entero de `lineas_para_registro`, y anotarlos en `progress/impl_F-022.md`  |  Verificación: lista en el informe; ningún fichero de código modificado
- [ ] T2: Tests de repositorio (`registro_ids_de_trabajador`: ids de la tabla de persona, `[]` si no existe; clave `obras` de `lineas_para_registro`: solo líneas que viajan, una entrada por obra, `[]` sin líneas) en rojo con traza; implementar en `parte_repository.py` y adaptar `test_f024_r22_payload_repo_sin_ids` con nota  |  Verificación: `pytest tests/test_f022_aprobar_seleccion.py -k repo tests/test_f024_borrado_sigrid.py` en verde
- [ ] T3: Tests de la guardia de una obra (R17: 422 con `obras` en preflight, encolar y ejecutar, con y sin `ambito`, incluido `obra_key` heredado; ni sv5 ni publisher llamados; una obra con excluidas de otra sigue pasando) en rojo; implementar en `_payload_registro`  |  Verificación: `pytest tests/test_f022_aprobar_seleccion.py -k una_obra` en verde
- [ ] T4: Tests de `ambito` (R13 obra y trabajador; R14 id de otra obra, de otro periodo, de otra persona, en papelera e inexistente → 422 `fuera_de_ambito` sin sv5, sin publicar y sin `encolado`; R15 vista desconocida, clave ausente, ids vacíos y 5001 ids → 422; R18 sin `ambito` como hoy) en rojo; implementar `_validar_ambito`, `VISTAS_AMBITO` y `MAX_IDS_APROBACION`  |  Verificación: `pytest tests/test_f022_aprobar_seleccion.py -k ambito` en verde
- [ ] T5: Tests de lo que cuenta (R16 `excluidas` solo de lo pedido; R19 payload de sv5 con solo lo pedido, `avisos_calendario` solo de esas líneas, DNI no fiable fuera de la selección no bloquea y dentro sí; R20 encolar un subconjunto: solo esos a `encolado` y en `registro_ids`, el resto conserva `sigrid_estado` y `sigrid_motivo`; R21 claves del payload de sv5 y de la cola = `obra, lineas, pisar_claves, usuario`) en rojo; ajustar lo que falte  |  Verificación: `pytest tests/test_f022_aprobar_seleccion.py -k "cuenta or subconjunto or forma"` en verde
- [ ] T6: Tests de HTML (R1 casilla `sel-linea` con `data-registro-id` en cada fila de obra y de persona, también congelada; botones `data-sel-visibles`, `data-sel-ninguna`, contador; `#aprobar-todo` con `data-vista` y `data-obra-key/period/mode` o `data-worker-key`; R12 los `aprobar-linea` intactos) en rojo; cambiar `obra_detail.html` y `trabajador_detail.html`  |  Verificación: `pytest tests/test_f022_vistas_seleccion.py -k vista` en verde y parseo Jinja2 de las dos plantillas
- [ ] T7: `static/app.js` y `styles.css` según design §5.3 (`PartidaSel` global con `visible`, casillas ↔ selección, rango solo visibles, seleccionar visibles/quitar, contador con ocultas, `_filterCellText` sin la casilla, evento `lineas:cambio`, `conjuntoAprobacion`, texto/`disabled`/`title` del botón, `{registro_ids, ambito}` y alcance en el modal, «Aprobar seleccionadas» en `.bulk-bar`); tests estáticos mínimos de R5, R10 y R12 en `test_f022_vistas_seleccion.py -k js`  |  Verificación: `node --check services/partes-front/static/app.js` y `pytest tests/test_f022_vistas_seleccion.py` en verde; navegador MANUAL (humano, design §9 M2–M6)
- [ ] T8: `docs/ARCHITECTURE.md` (semánticas 5 y 10, ≤ 6 líneas netas)  |  Verificación: lectura del reviewer contra design §4
- [ ] T9: `C:\Users\pgris\PycharmProjects\azure-apps\partes.md`: las líneas de «Aprobar todo»/«Aprobar visibles» pasan a selección explícita y regla de una obra; commit local en ese repositorio, sin push  |  Verificación: `git -C C:/Users/pgris/PycharmProjects/azure-apps log -1` muestra el commit
- [ ] T10: Suite completa de sv4 y tests de raíz en verde (R22), con la lista de T1 adaptada y anotada  |  Verificación: salida de los dos comandos pegada en `progress/impl_F-022.md`
- [ ] T11: Cobertura de líneas cambiadas y campaña de mutación muestreada sobre `app.py` y `parte_repository.py` en `progress/mutacion_F-022.md`, con cada superviviente analizado  |  Verificación: informe con SHA de HEAD y supervivientes justificados o muertos
- [ ] T12: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida en verde; pendientes MANUAL (M1–M6 de design §9 y la parte de navegador de T7) anotados en `progress/current.md`
