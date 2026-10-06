<!-- specs/F-032-sesame-festivos-produccion/tasks.md -->
# F-032 · Activar Sesame en producción — Tareas

Rama: **`feature/F-032-sesame-festivos-produccion`** (ya creada). Un commit
**local** por tarea, `F-032 Tn: …`, por rutas explícitas (nunca `git add -A`).
Sin push ni PR. Rigor **`estandar`**: fase RED con traza en
`progress/impl_F-032.md`, cobertura de líneas cambiadas ≥ umbral, mutación
muestreada (20, semilla fija) con supervivientes documentados.

Reglas que no se negocian:
- No se empieza sin el visto bueno del humano a DA1–DA10 (design §8).
- Los agentes no tocan el repositorio `sesame-api` ni su `.env`, no despliegan,
  no crean secretos, roles ni Container Apps: eso es §7 (humano).
- Tests sin red ni BBDD: `httpx.MockTransport`, repositorio falso.
- Los dos `sesame_api_client.py` se cambian en el mismo commit y quedan
  idénticos salvo el docstring de módulo (R8).

- [ ] T1: Tests rojos del cliente en `services/partes-persistencia/tests/test_f032_cliente_minimo.py` y `services/partes-front/tests/test_f032_cliente_minimo.py`: R1 (defecto 0 no controla), R2 (menos del mínimo ⇒ `CalendarioIncompletoError`, mensaje con año y recuento sin DNI; exactamente el mínimo pasa; festivos de otro año no cuentan), R3 (por defecto incompleto), R4 (404 y sin `por_defecto` ⇒ `None`)  |  Verificación: traza RED en `progress/impl_F-032.md`
- [ ] T2: `CalendarioIncompletoError`, `festivos_minimos` y `_exigir_minimo` en los dos `infrastructure/sesame/sesame_api_client.py` (design §5.1)  |  Verificación: T1 en verde y suites de sv3 y sv4 en verde
- [ ] T3: Guardián `tests/test_f032_sesame_cliente_gemelos.py` (R8): compara los dos módulos sin su docstring y falla con el nombre de la función que difiere; comprobar que se pone rojo alterando una copia en local (sin commitear la alteración)  |  Verificación: `pytest tests/test_f032_sesame_cliente_gemelos.py` en verde
- [ ] T4: Tests rojos de settings y cableado: R5 en sv3 (`construir_calendario` pasa el mínimo; log con `festivos_minimos=` y sin la clave, R29; negativo ⇒ `ValidationError`) y sv4 (`build_app` con dobles, patrón de los tests de wiring de F-003); R9 (`validar_datos_sesame.py` construye el cliente sin mínimo)  |  Verificación: traza RED
- [ ] T5: `sesame_festivos_minimos` en los dos `config/settings.py` y paso al cliente en sv3 `interface_adapters/api/app.py::construir_calendario` y sv4 `interface_adapters/web/app.py::build_app` (design §5.2)  |  Verificación: T4 en verde
- [ ] T6: Tests de cascada con calendario incompleto: sv3 `test_f032_calendario_incompleto.py` (R6: `SesameCalendarioLaboral` + cliente con `MockTransport` ⇒ respaldo JSON, `consumir_degradacion()` verdadero, sin llamada a `calendarios-festivos`; con caché caducada previa ⇒ la reutiliza) y sv4 (R7: `CalendarioProvider` ⇒ `dia(...).fiable` falso y `fiable_para` falso)  |  Verificación: `pytest` de ambos ficheros en verde (caracterización: deben pasar sin tocar los adaptadores; si no, PARAR)
- [ ] T7: Test `test_f032_r24_recalculo.py` en sv3 (R24–R25): conciliador con calendario falso que convierte un martes en festivo; línea no congelada ⇒ ordinarias a extra; línea de parte aprobado o `registrado`/`encolado`/`dedicacion` ⇒ intacta y sin marca; y al revés (deja de ser festivo ⇒ vuelve a ordinarias)  |  Verificación: `pytest services/partes-persistencia/tests/test_f032_r24_recalculo.py` en verde (caracterización del comportamiento existente)
- [ ] T8: Tests rojos de la herramienta `test_f032_contraste.py`: R10 (solo-Sesame, solo-respaldo, L–V, por defecto), R11 (`INCOMPLETO`), R12 (precedencia `--base-url` > entorno; sin `--impacto` no se construye repositorio), R13 (nombres de fichero, BOM y `;`, salida 0), R14 (sin configuración o listado fallido ⇒ código ≠ 0 sin ficheros), R15 (clasificación con `esta_congelado` importado, 404 ⇒ por defecto), R16 (recuentos por año, obra × mes, clase y sentido; años sin calendario; Markdown sin nombres), R17 (DNI fallido ⇒ fila de error y sigue), R18 (solo `GET`; el repositorio falso solo expone `fetch_registros_para_recurso`)  |  Verificación: traza RED
- [ ] T9: `services/partes-persistencia/contrastar_festivos_sesame.py` (design §5.3)  |  Verificación: T8 en verde
- [ ] T10: Test estático `tests/test_f032_infra_sesame.py` (R19–R23): `add_sesame_partes.ps1` toca `ca-sv3-persistencia` y `ca-sv4-front`, usa `keyvaultref:` + `identityref:` y `secretref:sesame-key`, fija las cinco variables, valida URL y secreto antes del primer `containerapp`, `-Quitar` con `--remove-env-vars` de las cinco; `create_capps_partes.ps1` y `create_sv4_front.ps1` llevan `SESAME_FESTIVOS_MINIMOS`; ningún `.ps1` versionado con URL de sesame-api ni claves; CRLF y sin BOM  |  Verificación: traza RED
- [ ] T11: `infra/add_sesame_partes.ps1` (design §5.4) y bloques Sesame de `create_capps_partes.ps1`, `create_sv4_front.ps1` y `00_vars_partes.ps1`  |  Verificación: T10 en verde y `powershell -NoProfile -Command "[System.Management.Automation.Language.Parser]::ParseFile('infra/add_sesame_partes.ps1',[ref]$null,[ref]$e); $e"` sin errores
- [ ] T12: Documentación: `docs/ARCHITECTURE.md` (herramientas de consola: contraste), `infra/README_partes.md` (encender/apagar Sesame) y `azure-apps/partes.md` (R27: 5.3 bis «listo para encender», variable nueva, script, calendario incompleto, precondiciones P0–P5, enlace a `sesame-api.md`; commit en el repo `azure-apps`, sin push)  |  Verificación: revisión del reviewer contra R27–R28; `git -C ../azure-apps log -1`
- [ ] T13: Cobertura y mutación muestreada (estándar) sobre los ficheros cambiados; supervivientes analizados en `progress/impl_F-032.md`  |  Verificación: `bash harness/init.sh` (sección de mutación) y `progress/mutacion_F-032.md`
- [ ] T14: M1 despliegue de sesame-api (tras P0–P2)  |  Verificación: MANUAL (humano), design §7 M1
- [ ] T15: M2 contraste y M3 impacto de 2026; RRHH corrige lo `INCOMPLETO`  |  Verificación: MANUAL (humano), `python contrastar_festivos_sesame.py --ano 2026 [--impacto]` desde `services/partes-persistencia`
- [ ] T16: M4 redespliegue apagado, M5 encendido, M6 portal, M7 apagado de prueba  |  Verificación: MANUAL (humano), design §7 M4–M7; al encender, actualizar el estado en `azure-apps/partes.md`
- [ ] T17: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
