<!-- progress/review_F-048.md -->
Revisión incremental desde 1bf221c (pasada 2) — delta `1bf221c..5127956`. F-048.

**Veredicto: APPROVED** (los tres cambios requeridos de la pasada 1, resueltos y verificados).

**Rigor** `critico` (declarado en `features.json`): fase RED con traza, cobertura ≥ 80 %,
mutación completa con 0 supervivientes sin justificar y MANUAL con su comando.

## Pasada 2 · qué cambió en el delta

Solo `parte_normalizer.py` (bucle de `horas_extra_leidas`), `test_f048_normalizer.py`
(+2 tests, 4 casos), `progress/impl_F-048.md` y `progress/mutacion_F-048.md`. Ninguna
firma pública, fichero movido ni otra parte de lo aprobado en la pasada 1 se ve
afectada: el alcance de mutación crece de 45 a 48 líneas, todas en el mismo bloque.

- **Cambio requerido 1** [x]: `leidas = round(min(p_horas, acumulado − ord_leidas), 2)`
  (criterio del conciliador) y `None` si queda ≤ 0. `horas`, bucle de partidas, R3 y R5
  intactos (la suite de sv3 entera sigue en verde, incluidos los 6 casos de R3).
  Reproducido por el reviewer el caso de la pasada 1 (4,3 / 5 / P1 2,1 · P2 2,2 · P3):
  ahora `[None, None, 5.0]` (antes P2 8,88e-16 y P3 5,000000000000001).
- **Cambio requerido 2** [x]: `test_f048_r2_sin_residuo_de_coma_flotante` con los tres
  casos de la tabla del hallazgo y `test_f048_r2_la_traza_va_a_dos_decimales`
  (4 + 1,234 ⇒ 1,23; `horas` sigue 5,234). **RED real** en `impl_F-048.md` §«Pasada 2»:
  `3 failed` con los tres valores con residuo, y el del mutante `round(…, 3)` aplicado a
  mano (`assert 1.234 == 1.23`).
- **Cambio requerido 3** [x]: campaña repetida e init.sh en verde (abajo).
- Nota de juicio: redondear a 2 decimales hace que, con extras leídas de 3 decimales, la
  traza difiera del papel en < 0,01 h. Es el mismo criterio que aplica el conciliador a
  `horas` y `extra_auto`; la columna es solo traza. Aceptable.

## init.sh y suites (reviewer, 2026-10-16, pasada 2)

- `bash harness/init.sh` ⇒ **ENTORNO LISTO**, exit 0. Raíz 487 passed / 3 skipped
  (179 s); sv1–sv5 en verde (por caché; el delta no toca sv4 ni sv1/sv2/sv5).
  `PUERTA COBERTURA: 100.0% de 16 líneas cambiadas (16/16, umbral 80%, nivel critico)`.
  `PUERTA TAMAÑO` dentro de topes (impl 213/220). Avisos previos ajenos (features
  `blocked`, ruff de deuda previa, `infra` sin tests).
- sv3 completa sin caché: **1451 passed** (29,6 s).

## Mutación (C4 bis, pasada 2)

- Informe de la herramienta; sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0;
  línea base en los 6 worktrees (42,0–44,2 s). 12 mutantes, **12 muertos**, 0
  supervivientes, 0 timeouts, 199,2 s.
- **Recálculo independiente (puro)** con `harness.alcance.alcance_de_feature("F-048")` +
  `harness.mutacion.generar_mutantes`: 6 ficheros, **48 líneas**, **12 mutantes** (todos
  en `parte_normalizer.py`; el nuevo es `round(…, 2)`→`round(…, 3)`) ⇒ coincide.
- **Campaña no reejecutada: 199,2 s según el informe** (> 60 s): recálculo puro + RM1–RM6.
- Coste por mutante = 199,2 × 6 ÷ 12 ≈ 100 s (> 1 s). **RM2**: media 16,6 s × 6 ≈ 100 s
  frente a línea base ~43 s: coherente (6 suites compitiendo; el total incluye la base).
- **RM1**: SHA medido `72b1c7f…`; de ahí a HEAD (`5127956`) solo cambian
  `progress/impl_F-048.md` y `progress/mutacion_F-048.md` ⇒ alcance medido = revisado.
- **RM3**: ninguno de los 12 es equivalente; el nuevo (`round(…, 3)`) lo mata
  `test_f048_r2_la_traza_va_a_dos_decimales`. La campaña intermedia sobre `6166ab1`
  (1 superviviente, ese mismo) queda superada por el test y declarada en el informe.
- **RM5** N/A: 0 supervivientes, ningún equivalente. **RM6** N/A: no se quitó ninguna guarda.

## Lo aprobado en la pasada 1 (dado por bueno, no releído)

Detalle completo en el commit `99309f9` de este fichero. En síntesis: diff de producción
= design §3; R19 (diff vacío de conciliador, `reparto_ponderado`, `pareja_extra`,
`jornada_resolver` x2, `congelacion`, sv1/sv2/sv5, `infra/`, `static/`); ORM gemelo
idéntico (`cmp`); los clones de `ParteRegistroOrm` no copian la columna; los **nueve
guardianes 56→57** solo cambian cuenta, lista y docstrings (opción A del humano); la
aclaración del humano sobre DA2 la cubre
`test_f048_r9_r11_exactamente_dos_lineas_…[caso-1|caso-2|4+2]` (2 líneas activas: una
`normal` y una `extra_auto`, 0 `extra` explícitas); R25 en ARCHITECTURE,
`partes-proyecto.md` y `azure-apps` `2cf42ec`.

## Checkpoints (estado tras la pasada 2)

- **C1** [x] init.sh exit 0 · [x] ficheros base del arnés.
- **C2** [x] una sola `in_progress` en la rama (F-046 en su worktree, excepción del
  humano anotada) · [x] rama `feature/F-048-…` · [x] `current.md`: la sección F-048 es
  la sesión activa; los bloques de F-045 vienen de `dev` dc03468, limpieza del líder al
  cerrar · [x] `history.md` sin cambios pendientes.
- **C3** [x] hexagonal · [x] primera línea con ruta · [x] sin prints, TODOs, secretos
  ni dependencias nuevas · [x] trampas: empleado≠recurso no se toca; incidencias
  intactas (R5); ORM duplicado en las dos copias, idéntico.
- **C3 bis** [x] cabecera de `partes-proyecto.md` intacta · [x] sin originales PDF/ofimática
  (`git log --diff-filter=A`) · [x] barrido (pasada 1) de las líneas añadidas en
  `docs/referencia/`: correo, IPv4, GUID, `password|passwd|secret|token|api_key|
  AccountKey|SharedAccess|Bearer|-----BEGIN` ⇒ 0 coincidencias; el delta no toca
  `docs/` · [x] nada redactado.
- **C4** [x] cada requisito con test trazable y en verde (R2 y R22 ya con el caso de
  coma flotante) · [x] sin red ni BBDD real · [x] M1–M5 en `current.md`.
- **C4 bis** [x] rigor declarado · [x] fase RED (pasada 1 y pasada 2) · [x] cobertura
  100 % · [x] mutación verificada · [x] sin cabecera de campaña no válida · [x] RM1 ·
  [x] RM2 · [x] RM5 N/A justificado · [x] RM6 N/A justificado · [x] campaña manual N/A
  (la automática dio 12) · [x] 0 supervivientes · [x] «Evidencias» con los cuatro
  números y los workers (actualizadas en la pasada 2).
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json` (solo el `.ejemplo`).
- **C5** [x] T1–T10 `[x]` con su commit `F-048 Tn:` (más los commits de la pasada 2);
  T0 aplazada por decisión del humano (anotada en `tasks.md` y `current.md`): riesgo de
  fusión conocido, no defecto; hay que hacerla y repasar init.sh antes de `done` ·
  [x] árbol limpio · [x] `features.json` en `in_progress`, coherente.

## Cobertura requisito → test

Los 72 tests `test_f048_*` (5 + 32 + 23 + 12) llevan el requisito en el nombre.
R1–R5, R7: `test_f048_normalizer.py` (tabla de design §7 entera y, en R2, el caso de
coma flotante y los 2 decimales); R6, R24: `test_f048_esquema.py`; R8–R18:
`test_f048_conciliar.py`; R22–R23: `test_f048_traza_portal.py`; R19: diff vacío +
gemelos F-024, F-015 R19, F-010; R20: por construcción + M1; R21:
`test_f010_orm_models_gemelos.py`; R25: lectura + `test_documentos_del_arnes.py`.

## Cambios requeridos

Ninguno.

## Antes de `done` (no bloquea esta revisión)

- T0: fusionar `dev` con F-046/F-047 cuando estén, resolver los conflictos previstos
  (`orm_models.py` x2, `save_parte`) y repasar init.sh; si la fusión cambia código del
  alcance, la campaña de mutación se repite (RM1).
- MANUAL del humano M1–M5 (`current.md`), despliegue de sv3 y sv4 a petición suya.

**Automejora** (propuesta, no aplicada): que `specs/SPECS.md` pida fijar el redondeo de
todo campo `Float` derivado por resta o acumulado; aquí lo cazó la revisión, no la spec.
