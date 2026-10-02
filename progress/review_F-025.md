<!-- progress/review_F-025.md -->
Revisión completa (pasada 1): `git diff faca290..HEAD` (HEAD `fc01b3f`).

# F-025 · Incidencia y horas el mismo día — Review

**Veredicto: APPROVED**

**Nivel de rigor:** `estandar`, declarado en `features.json`. Exige C1–C5,
C3 bis, tests trazables, fase RED de los centrales, cobertura ≥ 80 % de lo
cambiado y mutación muestreada con los supervivientes analizados.

## Verificación ejecutada por el reviewer

- `bash harness/init.sh`: **ENTORNO LISTO**; raíz `419 passed, 1 skipped`;
  `PUERTA COBERTURA: 100.0% de 204 líneas cambiadas`; tamaño en los topes;
  ruff 557 = deuda previa.
- sv4 salió de caché en `init.sh`; relanzada sin caché: `1535 passed, 1
  warning in 240.92s`. F-025 suelta: `107 passed`. `node --check` OK.
- Producción sin cambios desde la campaña: `a8e0b22..HEAD` solo toca tests,
  `progress/` y `tasks.md`. `git status` limpio.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros del arnés. **C2** [x] una sola
  `in_progress` · [x] rama · [x] `current.md` con F-025 arriba (resto
  histórico, como antes; O5) · [x] las 16 `done` en `history.md`.
- **C3** [x] hexagonal: `incidencias_horas.py` es puro, en application · [x]
  ruta en la 1.ª línea de los 6 ficheros nuevos (YAML incluido) · [x] sin
  `print`/`console.log`/TODO ni secretos. PyYAML llega por
  `uvicorn[standard]` (`pyyaml>=5.1; extra == 'standard'`), como preveía
  design §5.3 · [x] trampas: el payload no cambia (R14), `_rol_incidencia`/CIZ
  intactos, sin schema (`orm_models.py` fuera del diff).
- **C3 bis** [x] solo se modifica `partes-proyecto.md`, que conserva su
  cabecera · [x] `git log --diff-filter=A`: ni pdf ni ofimática · [x] barrido
  de las líneas añadidas (docs/referencia y todo el diff) con estos patrones:
  correo, IPv4, `10.x`/`192.168.`, GUID,
  `password|secret|token|api_key|AccountKey|SharedAccess|Bearer|-----BEGIN`
  y base64 de 40 caracteres o más. **0 coincidencias** · [x] nada que
  redactar.
- **C4** [x] trazabilidad (tabla) · [x] sin red ni BBDD (SQLite en memoria,
  `TestClient`, dobles de sv5/publisher/calendario, node, datos
  sintéticos) · [x] M1–M5 en `current.md` (T12/T13), con los pasos en
  `impl_F-025.md` §6 y la consulta en design §9. Es el mismo patrón que se
  aceptó en F-022/F-024.
- **C4 bis** [x] rigor declarado · [x] **fase RED** con salida real para los
  11 que exige `tasks.md` (R2, R3, R5, R6, R7, R9–R13, R18). R7 se probó
  contra una variante ingenua, que es lo correcto en un requisito negativo
  · [x] **cobertura** `[OK]` 100 % · [x] **mutación** recalculada de forma
  independiente y en puro sobre `07c40ba..a8e0b22`: 466 líneas (234/3/8/155/66)
  y **70 mutantes**, idénticos al informe. Rehice el sorteo con la semilla
  `20260820`: salen los mismos 20 y los 6 supervivientes, con el mismo
  operador y el mismo texto original→mutado · [x] **campaña no
  reejecutada**: 31 min según el informe (1861,6 s, por encima de 60 s);
  vale el recálculo más RM1–RM6 · [x] coste por mutante 1861,6 × 6 ÷ 20 =
  558 s · [x] sin «CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0;
  línea base en los 6 worktrees (533–539 s) · [x] **RM1**: SHA `a8e0b22`;
  lo posterior no toca el alcance · [x] **RM2**: media 93,1 × 6 = 559 s
  frente a una base de ~535 s, y 20 × 93,1 = total · [x] **RM3**: revisé
  los 14 muertos y ninguno es equivalente · N/A **RM5** por rigor
  `estandar`. El equivalente (`valor >= ε` tras `abs(valor) > ε`) tiene
  justificación escrita y es correcta · [x] **RM6**: no se quitó código;
  5 tests nuevos y producción intacta (`9c52389`) · N/A campaña manual,
  porque la automática dio 70 · [x] 6 de 6 analizados · [x] «Evidencias»
  con los 4 números y los workers (6) · [x] ningún N/A sin motivo.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T1–T11, T14 `[x]` con commit `F-025 Tn:`; T12/T13 MANUAL
  abiertas (como F-022/F-024) · [x] sin temporales · [x] `features.json` ok.

## Lo que se pidió mirar

- **F-022/F-024:** la exclusión va DESPUÉS de las de F-024 (R13, con
  `registrado` y `borrado_sigrid`), en `excluidas_detalle` con
  `estado: "incompatible"` y su motivo. La clave `incompatible` solo aparece
  si es > 0. No se tocó ningún test de F-022/F-024 y siguen en verde.
- **Día-trabajador cruzando obras:** `_activas_de_fechas` lee todas las
  líneas activas de las fechas pedidas, en lotes y de cualquier obra y
  estado. Persona = DNI normalizado o clave de trabajador. Hay tests con
  otra obra, línea no pedida, otro casado y lotes.
- **Ninguna ruta deja pasar un bloqueo:** preflight, ejecutar y encolar (con
  cola y sin ella) pasan por `_preparar_registro` →
  `lineas_para_registro(..., incidencias=tabla)`. Hay test de cada una y de
  los tres overrides. El 422 sin llamar a sv5 se comprueba en las tres.
- **Registrado intacto:** sin escrituras nuevas (`estados_sigrid` antes y
  después). **Escape:** todo por `esc()` (test con `<script>` y `&`); el
  detalle y el 422 ya escapaban, Jinja2 autoescapa los `title`.
- **DA1:** la tabla se carga lo primero en `build_app`; hay tests para una
  ruta inexistente, un YAML roto y una letra de menos. El YAML entra en la
  imagen (robocopy del servicio + `COPY . .`).

## Desviaciones del implementer (las tres, aceptadas)

1. **Design §5.4**: los avisos se pintan juntos en `aprobar()`, no en
   `grupoHtml`. R19 se cumple (listados, escapados y fuera del pliegue). El
   motivo es real: los tests de F-022 ejecutan `grupoHtml` con una lista
   cerrada de funciones. Coste en O2.
2. Ruta relativa a la raíz del servicio. 3. R2 más estricto («nada en silencio»).

## Cobertura requisito → test (`services/partes-front/tests/test_f025_*`)

| Req | Tests |
|---|---|
| R1–R3 | `tabla::r1_*` (5), `r2_*` (7 tipos + 3 de arranque), `r3_*` (4) |
| R4–R8 | `deteccion::r4_*` (3), `r5_*` (4), `r6_*` (3), `r7_*`, `r8_*`; `aprobacion::r4_persona…`, `r9_repo_la_persona_es_el_dni…` |
| R9 | `aprobacion::r9_repo_*` (5), `r9_preflight_…`, `r9_ejecutar_…`, `r9_encolar_*` (2) |
| R10 | `r10_todo_excluido_es_422…` (×3 rutas), `r10_solo_incompatibles…` |
| R11–R14 | `r11_*` (6) · `r12_repo_…`, `r12_ningun_override…` (×4) · `r13_*` (2) · `r14_*` (2) |
| R15–R18 | `vistas::r15_*`, `r16_*`, `r17_*`, `r18_*` (repo y HTML); `aprobacion::r15_peor_nivel…` |
| R19 · R20 | `vistas::r19_js_*` (5) · `vistas::r20_crear_y_editar…` |
| R21 · R22 | El diff solo toca sv4 y docs; congelación, jornada_resolver, `_rol_incidencia` y ORM fuera |
| R23 | `aprobacion::r23_repo_sin_tabla…`, `vistas::r23_repo_vistas_sin_tabla…` |
| R24 | Leído: ARCHITECTURE sem. 14; `partes-proyecto.md` §4.1 (H = huelga, CIH, con enlace) y §3.4 |

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean)

1. **azure-apps.** `INCIDENCIAS_PATH` es variable nueva de sv4 y una tabla
   mal hecha impide arrancar. `azure-apps/partes.md` §5.6 lista las
   opcionales de sv4 y F-023 documentó el análogo de sv3. Design §1
   (aprobado) dice «no cambia», pero CLAUDE.md nombra las variables de
   entorno. Recomiendo una línea en §5.6 y otra en §3.4 antes del merge; lo
   decide el humano, como en F-020.
2. Los avisos agregados del modal no nombran la obra.
3. `/api/admin/poison/reencolar` reenvía payloads ya hechos sin pasar por
   la exclusión (fuera de R9; raro: conflicto surgido tras encolar).
4. `lineas_para_registro` no filtra el documento activo en su consulta
   principal (de antes): esa línea, pedida por id suelto, no entra en la
   detección. No es «línea» para la spec y con `ambito` no se puede pedir.
5. `current.md` perdió su 1.ª línea `<!-- progress/current.md -->` y
   arrastra sesiones cerradas (de antes). 6. Avisos con `horas > 0.0` y
   detección con `> 1e-9`: difieren solo en extras despreciables.

## Automejora propuesta (no aplicada)

`CHECKPOINTS.md` C3: «Si la feature añade o cambia una variable de entorno,
un endpoint o una tabla, `azure-apps/<proyecto>.md` está al día o la review
dice por qué no». CLAUDE.md lo exige, ningún checkbox lo recorre y los
precedentes no coinciden (F-020 observación, F-023 documentado).
