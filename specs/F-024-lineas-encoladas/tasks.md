<!-- specs/F-024-lineas-encoladas/tasks.md -->
# F-024 · Líneas borradas en Sigrid y estado «encolado» — Tareas

Rama: **`feature/F-024-lineas-encoladas`** (ya creada). Un commit **local** por
tarea, `F-024 Tn: …`, por rutas explícitas (nunca `git add -A`). Sin push ni
PR. Rigor **`critico`**: fase RED con traza en `progress/impl_F-024.md` para
**R1, R2, R3, R4, R8, R10, R11, R13, R14, R15, R17, R18, R19, R22 y R28**;
cobertura de líneas cambiadas ≥ umbral; campaña de mutación **completa** con
**0 supervivientes** sin test o justificación aceptada por el humano.

Reglas que no se negocian:

- **No empezar sin DA1–DA15 aprobadas** (`design.md` §8). Si DA7 o DA5
  cambian, se reescriben R22–R25 o R6 antes de seguir.
- **Ningún test toca red, Sigrid ni PostgreSQL**: `httpx` simulado, dobles
  del cliente de sv5 y SQLite en memoria. Sin nombres, DNIs ni `ide` reales
  de recursos en tests e informes (valores sintéticos).
- **Ni una escritura en Sigrid** desde local, tampoco en modo pruebas: esta
  feature solo lee.
- Comando de tests por servicio: `cd services/<svc> && ../../.venv/Scripts/python.exe -m pytest -q <ficheros>`.

- [x] T1: Inventariar los tests de F-002, F-003, F-004 y F-017 que dependen de que el payload incluya líneas `registrado`, de `MOTIVO_LINEA_REGISTRADA` o de la respuesta de `/api/aprobar/encolar`, y anotarlos en `progress/impl_F-024.md`  |  Verificación: lista en el informe; ningún fichero de código modificado
- [x] T2: Tests de `clasificar` (R2–R6, tablas de casos: acierto por synckey, respaldo por ide válido, ide reutilizado, cabecera borrada, diferencias con y sin incidencia) en rojo con traza; implementar `comprobacion_lineas.py` (design §5.1)  |  Verificación: `pytest tests/test_f024_comprobacion.py -k clasificar` en sv5 en verde
- [x] T3: Tests del cliente de sv5 (`lineas_por_ide`, `partes_por_ide`: lotes de 200, `max_rows` 1000, `truncated` ⇒ excepción; R7, R8) en rojo; implementar en `sigrid_write_client.py`  |  Verificación: `pytest tests/test_f024_comprobacion.py -k cliente` en verde
- [x] T4: Tests de `ComprobadorLineas.comprobar` (dedupe, lecturas por ide solo para fallos, excepción sube) y del endpoint `POST /api/registro/comprobar` (R1, R8, R9: un veredicto por id, 422 con 0 o 501 líneas, 502 sin veredictos, ninguna llamada a `escribir`, responde con el lock tomado por otro hilo); implementar en `app.py` y `main.py`  |  Verificación: `pytest tests/test_f024_comprobacion.py` y suite completa de sv5 en verde (incluida `test_f002_r11_sin_postgresql.py`)
- [x] T5: Tests de congelación y de `ESTADOS_EN_VUELO` (R13 en sv4, R15, R16) en rojo; cambiar `congelacion.py` y `ESTADOS_EN_VUELO` en `parte_repository.py`  |  Verificación: `pytest tests/test_f024_borrado_sigrid.py -k "congel or vuelo or motivo"` en sv4 en verde
- [ ] T6: Guardián de raíz `tests/test_f024_borrado_no_congela_gemelos.py` (R13: sv3 y sv4 en subprocesos con `cwd` en su servicio)  |  Verificación: `.venv/Scripts/python.exe -m pytest -q tests/test_f024_borrado_no_congela_gemelos.py` en verde, y en rojo si se añade `borrado_sigrid` a `ESTADOS_CONGELADOS` de sv3 en una copia aislada (anotarlo)
- [ ] T7: Tests de `registrados_para_comprobar`, `aplicar_comprobacion_sigrid` (R10, R11, R12: CAS por estado y por `hmores_ide`, campos conservados, motivo con parte, línea y fecha) y `recuento_estados` (R28) sobre SQLite en rojo; implementar en `parte_repository.py`  |  Verificación: `pytest tests/test_f024_borrado_sigrid.py -k repo` en verde
- [ ] T8: Tests de `RegistroComprobaciones` con reloj inyectado (R19: dentro del TTL no repite, `forzar` lo salta, sella al reservar aunque el lote falle, purga caducadas, seguro con dos hilos) en rojo; implementarlo en `comprobacion_sigrid.py`  |  Verificación: `pytest tests/test_f024_comprobar_y_estado.py -k recientes` en verde, sin `sleep` real
- [ ] T9: Tests de `ComprobacionSigrid` (R14 lote fallido o veredicto ausente no aplica y para, R17 lotes de 500 y `timeout_s` pasado al cliente, `recientes` en la respuesta, R21 log con origen) con un doble de `TransferClient`; implementar `ComprobacionSigrid`, `TransferClient.comprobar(payload, *, timeout_s)` y las tres variables `COMPROBACION_SIGRID_*`  |  Verificación: `pytest tests/test_f024_comprobar_y_estado.py -k servicio` en verde
- [ ] T10: Tests de `lineas_para_registro(incluir_borradas)` y de preflight/encolar/ejecutar (R22 `excluidas`, R23 422 con el motivo, R27 `registro_ids`) en rojo; cambiar `parte_repository.py` y `_payload_registro`/`aprobar_encolar` en `app.py`; adaptar los tests inventariados en T1  |  Verificación: `pytest tests/test_f024_borrado_sigrid.py -k payload` y suites de F-002, F-003 y F-017 de sv4 en verde
- [ ] T11: Tests de los endpoints `POST /api/sigrid/comprobar` (R17: 503 sin sv5, 422 con 0 o 5001 ids, solo `registrado`, `forzar`, `origen` en el log; R18: servir `/obras/{key}` y `/trabajadores/{key}` no llama al doble de sv5) y `POST /api/aprobar/estado` (R28: recuento, 422 con 0 o 5001 ids, no escribe) en rojo; implementarlos en `app.py`  |  Verificación: `pytest tests/test_f024_comprobar_y_estado.py -k endpoint` en verde
- [ ] T12: Tests de HTML (R24 insignia, tooltip con el motivo, «Reaprobar» con `data-incluir-borradas`, aviso de cabecera; R26 botón y `data-sigrid-estado`; R30 tooltip de `encolado`) en rojo; cambiar `obra_detail.html`, `trabajador_detail.html` y el contexto de las dos vistas  |  Verificación: `pytest tests/test_f024_borrado_sigrid.py -k vista` en verde y parseo Jinja2 de las dos plantillas
- [ ] T13: `static/app.js` (+ `styles.css` si hace falta): `comprobarVista()` al cargar obra y persona con aviso de borradas y nota discreta de fallo (R18, R20, design §5.3), sondeo del modal sin `reload()` prematuro (R29), aviso de la vista con «Actualizar» (R30), casilla de borradas en el modal masivo (R25), botón «Comprobar en Sigrid» con modal de resultado (R26), `incluir_borradas` en «Reaprobar»  |  Verificación: `node --check services/partes-front/static/app.js`; comprobación en navegador como MANUAL (humano, design §9 M5)
- [ ] T14: `docs/ARCHITECTURE.md` (semánticas 5 y 10, tercer uso del HTTP sv4↔sv5; ≤ 12 líneas netas)  |  Verificación: lectura del reviewer contra design §4 y §8
- [ ] T15: `C:\Users\pgris\PycharmProjects\azure-apps\partes.md`: endpoint `POST /api/registro/comprobar`, estado `borrado_sigrid`, comprobación al abrir obra/persona y variables `COMPROBACION_SIGRID_*` de sv4; commit local en ese repositorio, sin push  |  Verificación: `git -C ../azure-apps log -1` muestra el commit
- [ ] T16: Suites completas de sv3, sv4 y sv5 y tests de raíz en verde (R32)  |  Verificación: salida de los cuatro comandos pegada en `progress/impl_F-024.md`
- [ ] T17: Cobertura de líneas cambiadas y campaña de mutación completa sobre los ficheros de sv4 y sv5 tocados, en `progress/mutacion_F-024.md`, con cada superviviente matado por un test nuevo o justificado para el humano  |  Verificación: informe con 0 supervivientes sin resolver
- [ ] T18: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida en verde; pendientes MANUAL (M1–M5 de design §9 y T13) anotados en `progress/current.md`
