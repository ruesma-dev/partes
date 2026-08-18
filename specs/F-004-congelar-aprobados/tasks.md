<!-- specs/F-004-congelar-aprobados/tasks.md -->
# F-004 · Congelar registros aprobados — Tareas

Rama: `feature/F-004-congelar-aprobados`. Un commit por tarea
(`F-004 Tn: ...`). Tests SIEMPRE sin red ni BBDD (SQLite en memoria,
`Settings(_env_file=None)`, patrón `tests/dobles.py` de sv4; ampliar
`sembrar_registros` o añadir un sembrador con `approved`/`sigrid_estado`
parametrizables).

- [x] T1: Crear `application/services/congelacion.py` (funciones puras,
      constantes, `CongeladoError`) con su test de matriz.
      | Verificación: `python -m pytest services/partes-front/tests/test_f004_congelacion_reglas.py` en verde (R1, R2); fase RED primero (el test de la matriz falla sin el módulo).

- [x] T2: Guardas de LÍNEA en `parte_repository.py` (`update_registro`,
      `set_registro_hora`, `set_registro_partida`, `soft_delete_registro`,
      `crear_extra_desde`) + `@app.exception_handler(CongeladoError)` →
      409 JSON en `app.py`.
      | Verificación: tests R3, R4, R5 en `test_f004_endpoints_congelados.py`: cada endpoint responde 409 con `congelado: true` y la BBDD queda intacta; los mismos endpoints sobre línea libre siguen funcionando.

- [x] T3: Guardas de DOCUMENTO (`update_parte_fecha`, `update_parte_obra`,
      `delete_document`, `unapprove_document`) + redirects con mensaje en
      los flujos de formulario.
      | Verificación: tests R6, R7, R10, R11: fecha/obra→409 con doc congelado; delete de doc congelado no borra y redirige con motivo; unapprove con línea `encolado` rechaza; unapprove sin líneas en vuelo libera las no registradas y las `registrado` siguen congeladas.

- [x] T4: Reasignación/conciliación de empleado excluye congeladas
      (`backfill_empleado`, `reassign_empleado_by_*` + respuesta
      `congeladas` en `/api/empleado/reasignar` y
      `/api/conciliacion/confirmar`) y `undo_last` omite snapshots
      congelados (+ `omitidos` en `/api/undo`).
      | Verificación: tests R8, R9: mezcla de líneas libres y congeladas → solo las libres cambian y el recuento excluido llega en la respuesta; un undo cuyo snapshot toca una línea hoy `registrado` no la muta.

- [x] T5: Hard-delete y masivos: `hard_delete_registro`/`hard_delete_document`
      lanzan `CongeladoError` si hay línea `registrado`; `vaciar_papelera`,
      `soft_delete_obra`, `soft_delete_worker` omiten congelados y
      devuelven recuento (respuestas de los endpoints incluidas).
      | Verificación: tests R12, R13: hard-delete de línea `registrado` → 409 y sigue en BBDD; vaciar papelera y borrados masivos dejan intactos los congelados y reportan cuántos.

- [x] T6: Flags a las vistas: `RegistroView.congelado`/`congelado_motivo`,
      `ParteDetail.congelado_doc`, flag `"c"` en los `regs` de la matriz;
      plantillas `parte_detail.html`, `obra_detail.html`,
      `trabajador_detail.html` con candado, `disabled`, aspa oculta y
      banner de parte aprobado.
      | Verificación: tests R14, R15 (flag en `regs`), R17 en `test_f004_vistas_candado.py` sobre el HTML de `TestClient` (presencia de `disabled`/candado/banner en línea congelada; ausencia en línea libre); parseo Jinja2 de las tres plantillas.

- [ ] T7: `static/app.js`: no cablear editores en filas congeladas, popup
      de matriz con filas `c` en solo-lectura (sin Guardar/extra si todas),
      y los catch de edición muestran el `error` del 409 en vez del
      genérico. Retoque mínimo de `styles.css` si hace falta.
      | Verificación: `node --check services/partes-front/static/app.js` + MANUAL (humano): en el navegador (Ctrl+F5), editar una línea registrada muestra el motivo; celda de matriz congelada no ofrece guardar; parte aprobado sale bloqueado con banner.

- [ ] T8: No regresión + cierre: suites completas de sv4 (F-002/F-003
      incluidas) y del monorepo; anotar en `progress/` y actualizar
      `progress/current.md`.
      | Verificación: `bash harness/init.sh` en verde.

Verificación MANUAL final (humano, entorno real): con sv4+sv5 en local
contra la BBDD real (modo pruebas de Sigrid), aprobar un parte, comprobar
candados; encolar una obra×mes y comprobar que las líneas `encolado` no se
pueden editar ni desaprobar hasta llegar el resultado; sobre una línea
`registrado`, comprobar 409 con motivo y que el flujo Aprobar/↻/Revisar
sigue operativo.
