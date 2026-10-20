<!-- progress/review_F-050.md -->
Revisión completa (pasada 1), `git diff dev...HEAD` con dev `ff2ed8e` y HEAD `95a5f69`.

# F-050 · Misma fila para el mismo trabajador — review

- **Veredicto: APPROVED**
- **Nivel de rigor:** `estandar` (declarado en `features.json`): fase RED, cobertura de lo
  cambiado ≥ 80 % y mutación muestreada (20 de 35, semilla `20260820`) con supervivientes
  analizados. RM5 N/A (solo `critico`).
- **Fuera del veredicto:** despliegue de sv4 y M2–M6 (humano), listadas en
  `progress/current.md` con el comando de despliegue. M1 ya medida por el líder.

## Verificación ejecutada por el reviewer

- **`bash harness/init.sh`** tal cual sobre `95a5f69`: exit 0, «ENTORNO LISTO»; raíz `493 passed, 3 skipped`; sv4 `2348 passed, 1 skipped` (26 min); avisos previos (F-032 `blocked`, ruff 736).
- **Alcance y mutantes recalculados** (cálculo puro, `harness.alcance.alcance_de_feature`
  + `harness.mutacion.generar_mutantes`): 2 ficheros, **163 líneas** (153 de
  `parte_repository.py`, 10 de `app.py`), **35 generados**; la muestra con
  `random.Random(20260820).sample(…, 20)` reproduce la numeración del informe: #7, #9,
  #11 y #16 supervivientes y #12, #13, #20 timeouts, con el mismo operador y el mismo
  texto original → mutado. Coincide.
- **Campaña no reejecutada: 14175,8 s (3 h 56 min) según el informe**; vale el recálculo
  puro + RM1–RM6 + RM4 (abajo).
- **RM4, sobre una copia en el scratchpad** (`git archive HEAD services/partes-front`,
  árbol de trabajo intacto): base `test_f050_portal.py` + `test_f050_alta_manual.py`
  `41 passed`; **#13** (`== 1` → `== 2`, l.1123) ⇒ `9 failed` en `test_f050_portal.py`;
  **#20** (`+` → `-`, `app.py` l.873) ⇒ `4 failed` (`TypeError`); **#16** (`is not None`
  → `is None`, l.3804) ⇒ `1 failed`,
  `test_f050_r16_con_ficha_y_recurso_hereda_de_su_rec` (`(5, …) == (4, …)`). Las tres
  cifras coinciden con el informe.
- **R21/R22 con `git diff`:** el `--stat` de sv1/sv2/sv3/sv5, `infra/`, `CLAUDE.md`, ambas
  `orm_models.py`, `application/` y `infrastructure/sigrid/` de sv4, `obra_detail.html`,
  `parte_detail.html` y `tests/` raíz sale **vacío**; en `services/partes-front/tests` 5 `A`
  (los `test_f050_*`) y 24 `M`; `git diff -U0` de las 24 `M` revisado línea a línea: solo
  literales `emp-N` → `rec-R`, el parámetro `recurso_ide` de `sembrar_parte` /
  `test_f025_aprobacion.sembrar`, el 502 de la persona B, el 602 de f019 `publicado` y la
  `clave` opcional de f035 `_asignar`: exactamente T2 ampliada por el humano. Ninguna
  aserción cambia de sentido. `test_f033_columna_empresa.py` intacto.
- **Lista cerrada del `CLAUDE.md`:** no crece (sin tocar; nada duplicado en sv3/sv5).
- **Datos personales:** barrido de DNIs (`[0-9]{8}[A-Z]`, NIE), correos, IPs y GUID en
  tests nuevos, spec y `progress/`: solo sintéticos (`12345678Z`, «Persona Diez»…).
- **Ortografía:** spec, informes, `ARCHITECTURE.md` y textos visibles con tildes; los
  comentarios de código van sin ellas, estilo de esos ficheros (`linea` 144 frente a
  `línea` 1 en `parte_repository.py` de `dev`). Commits: observación 2.

## Revisión del diseño frente al código

- `_clave_trabajador` (R1–R2): `rec-` exige `casada and recurso is not None`; si no,
  `emp-`, `nom-` y `sin-trabajador` byte a byte como antes (R3, contrastado en el test con
  una copia literal de la función de `dc03468`). `worker_key_for_registro` delega con
  `esta_casado` y `recurso_ide` antes que `empleado_reside`.
- `get_parte`/`list_partes` (R4, R6, R7) ya usan la clave única; el test R4 vigila por
  `inspect.getsource` que no queden las dos variantes a mano y que solo `_clave_trabajador`
  arme `emp-`/`nom-`/`sin-trabajador` de trabajador.
- `crear_parte_manual` (R16–R18): la clave de la línea nueva usa el mismo
  `recurso = empleado_reside` que se escribe en `recurso_ide` y `casada` = ficha o
  `recurso_manual`, coherente con `esta_casado` de la línea guardada. Fila y leído una vez
  por día, compartidos por la incidencia y los tipos. Resto de campos idéntico (R18).
- R14/R15: `clave_actual_de_clave_antigua` filtra con la regla anterior exacta
  (`casada=False`, `recurso=None`), solo `GET`, 307 conservando la query; POST sin
  compatibilidad (R13). Decisión del implementer (una línea con ficha no cuenta para una
  `nom-` antigua) más fiel a R14 que el atajo de design §3, y fijada por test.
- R19/R20: `data-emp-ide` = ficha de la línea más reciente, `data-emp-reside` solo con
  `rec-`; `setLock` deja de vaciar el `reside`; `verHrefNuevoParte` coherente con la clave
  que tendrán las líneas (con ficha y recurso, `rec-`; solo ficha, `emp-`).
- R23–R26: `_empresa_por_recurso` extraída sin cambio de `list_obras`; empresa con la regla
  de F-033 sobre datos ya cargados; orden `(casada, nombre, menor empresa o 10**9)`.

## Checkpoints

- **C1** [x] `init.sh` exit 0 · [x] ficheros base presentes.
- **C2** [x] solo F-050 `in_progress` · [x] rama `feature/F-050-…` · [x] `current.md`:
  sección F-050 arriba; el resto es el registro acumulado de pendientes que ya había en
  `dev` (2544 líneas; mismo criterio que las reviews de F-046, F-048 y F-051) · [x] las
  `done` siguen en `history.md` (F-050 aún no lo es).
- **C3** [x] hexagonal · [x] primera línea con ruta en los cinco tests nuevos y en los
  ficheros tocados · [x] sin prints, TODOs, secretos ni dependencias nuevas · [x] trampas:
  (1) empleado ≠ recurso: la clave pasa a ser el RECURSO, justo lo que pide la trampa, y
  sigue arrastrando ficha y recurso; (2) incidencias: el alta de incidencia comparte fila,
  sin tocar horas ni CI/CIZ; (3) ORM duplicado: no se toca.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] R1–R26 trazados y en verde (tabla abajo; R21–R22 por `git diff`, hecho aquí)
  · [x] sin red ni PostgreSQL (SQLite de `tests/dobles.py`, TestClient, `node`; doble de
  Sigrid que falla si se le llama en R26) · [x] despliegue y M2–M6 en `current.md`.
- **C4 bis** [x] rigor declarado (`estandar`) · [x] RED con trazas reales en T1, T3–T8 y
  T11 · [x] cobertura `[OK]` 100 % (60/60) · [x] informe de mutación verificado (alcance 163, 35
  generados, muestra reproducida) · [x] muertos: >60 s, recálculo puro + RM4, dicho arriba
  · [x] coste por mutante 14175,8 × 1 ÷ 20 = 708,8 s · [x] sin «⚠ CAMPAÑA NO VÁLIDA» y
  «Sin veredicto (base rota)» = 0 · [x] **RM1** medido en `04613e6`; de ahí a HEAD solo
  cambian `progress/`, `BACKLOG.md`, `features.json`, `tasks.md` y un test nuevo, ningún
  fichero del alcance · [x] **RM2** W = 1, media × W = 708,8 s frente a base 519,6 s y
  20 × 708,8 = 14176 s: coherente (por encima de la base por 3 timeouts de 1040 s y
  supervivientes que corren la suite entera) · [x] **RM3** ningún equivalente sale muerto:
  los 13 muertos (#1–#6, #8, #10, #14, #15, #17–#19) cambian comportamiento observable ·
  N/A **RM5** (nivel `estandar`; basta la justificación escrita, presente para #7, #9,
  #11) · [x] **RM6** no se quitó ninguna guarda: #16 se mató con un test nuevo · N/A
  campaña manual (la automática generó 35) · [x] 4 supervivientes analizados, ninguno
  `PENDIENTE` · [x] «Evidencias» con tests, cobertura, mutantes, tiempo de suite y
  `--workers 1`.
- **C4 ter** N/A: el repo no declara `harness/rutas_sensibles.json`.
- **C5** [x] T1–T13 `[x]`; commit `F-050 Tn:` de T1–T11 (T2 y T7 en dos, explicado). T12
  (anotar en `current.md`) va en `28e7aac` y T13 (ejecutar `init.sh`) no deja fichero:
  explicado en `impl` · [x] árbol limpio tras `init.sh` (solo este informe sin trackear) · [x] `features.json` en
  `in_progress`, a la espera del merge y de M2–M6.

## Cobertura requisito → test (`services/partes-front/tests/`)

| Req | Test(s) |
|---|---|
| R1–R3 | `test_f050_clave.py`: `test_f050_r1_*` (8), `r2_no_casada_con_recurso_no_da_rec`, `r3_no_casadas_igual_que_antes` (tabla 10 × 4) |
| R4, R11 | `test_f050_r4_*` (2), `test_f050_r11_*` (3) |
| R5–R10 | `test_f050_vistas.py`: `r5_*` (4: E1, E8), `r6_*` (4), `r7_*`, `r8_*` (2), `r9_*` (3: E9, E10), `r10_*` (3) |
| R12, R13 | `test_f050_r12_*` (4: reasignar, papelera, ámbito), `test_f050_r13_*` (2) |
| R14, R15 | `test_f050_portal.py`: `r14_*` (6, 307 con query), `r15_*` (2, 404) |
| R16–R18 | `test_f050_alta_manual.py`: `r16_*` (5, con el nuevo de ficha y recurso), `r17_*` (6), `r18_*` |
| R19, R20 | `test_f050_portal.py`: `r19_*` (4), `r20_*` (2, `node`) |
| R21, R22 | `git diff` de este informe (T10) |
| R23–R26 | `test_f050_empresa.py`: `r23_*` (2), `r24_*` (2), `r25_*`, `r26_*` (3) |

## Cambios requeridos: ninguno.

## Observaciones (no bloquean)

1. **Cabecera de una `rec-` con líneas mixtas.** `list_workers` y `get_worker` toman
   nombre, código y DNI de la primera línea del grupo; en una `rec-` que junta una línea
   con ficha y otra sin ella (E8), si la primera es la de la IA sin ficha la cabecera
   puede enseñar el leído y no el nombre de Sigrid. No lo pide la spec; a mirar en M2/M6.
2. **Mensajes de commit sin tildes** en `28e7aac` («campana de mutacion», que además dice
   otra cosa), `cbb3eb8` («decision») y `12e4092` («semantica»). Ya están en la rama; no
   merece reescribir historia, pero conviene cuidarlo.
3. `progress/propuesta_T2_F-050.diff` queda versionado como rastro de la decisión del
   humano sobre T2; puede borrarse al cerrar si se prefiere. #9: de acuerdo, sin cambio.

## Automejora propuesta (no aplicada)

1. **`CHECKPOINTS.md` C5**: admitir explícitamente que una tarea sin artefacto propio
   (ejecutar `init.sh`, anotar pendientes) vaya en el commit de otra tarea si el informe
   lo dice; hoy cada reviewer lo justifica por su cuenta.
2. **`reviewer.md`, RM4**: dejar como receta `git archive HEAD services/<svc> | tar -x`
   en el scratchpad (copia aislada en segundos, sin tocar el árbol).
