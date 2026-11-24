<!-- progress/review_F-083.md -->
Revisión de evidencias desde 7402199 · `git diff 7402199..14d6d5d` (HEAD 14d6d5d, pasada 2)

# Review F-083 · Una racha de incidencia solo lleva CIZ en su último día

**Veredicto: APPROVED** (pasada de evidencias). **SHA aprobado: 14d6d5d.**
Pasada principal: APPROVED sobre 7402199 (c25a504). Allí: RED reproducida sobre `dev`, 8
mutaciones a mano muertas, R1–R22 trazados, desviación de R22 aceptada y cobertura 100 % (31/31).

**Nivel de rigor: `critico`** (declarado). Exige mutación (uno por línea, 60 % acotado a
[100, 300]), cero supervivientes sin aceptación escrita del humano, RM1–RM7 y MANUAL. El delta
no toca `harness/rigor.local.json`.

## Delta revisado

- **Código de producción: 0 líneas.** En `services/` solo cambia
  `tests/test_f083_ciz_solo_fin_de_racha.py` (+11 líneas, el test del encargo). Desde el SHA
  medido (9784e0e) tampoco cambia producción.
- O1 y O2 de la principal, resueltos: `features.json` y `BACKLOG.md` dicen «D1–D8 decididas», y la
  cabecera de `current.md` dice `in_review`. En `tasks.md`, T6 está `[x]`.

## Lo que ejecuté yo

- **`ARNES_SIN_CACHE=1 bash harness/init.sh` sobre 14d6d5d: exit 0, `ENTORNO LISTO`**, sin caché.
  - Raíz: 2549 passed y 50 skipped. sv1: 74. sv2: 579. sv3: 2954. sv4: 4017 passed, 1 skipped.
    **sv5: 1888 passed, 1 skipped** (+1, el test nuevo).
  - `PUERTA COBERTURA: 100.0% de 31 líneas (31/31, umbral 90%)`.
  - `PUERTA TAMAÑO` OK (144/150, 249/250, impl 190/220). `CARRIL` N/A. `CAPA E2E: N/A`.
- **Recálculo puro** (`harness.alcance` y `generar_mutantes`): 100 líneas (`registro_pipeline.py`
  20 y `racha_ciz.py` 80), **25 mutantes** (2 + 23) y **19 líneas distintas**.
  - `seleccionar` con la regla y la semilla 20261030 del JSON da 19 candidatos y tope 100.
  - **Los 19 elegidos coinciden uno a uno con los 19 evaluados del JSON**: fichero, línea,
    columna, operador y texto.
- Los 2 supervivientes existen como mutantes reales de operador `veracidad`:
  - `racha_ciz.py:189`: `if ultima is not None:` → `if ultima:`.
  - `:196`: `if sigue is not None:` → `if sigue:`.
- **Campaña no reejecutada: 176,4 s según el informe (> 60 s).** En su lugar, RM4 sobre una copia
  de sv5 en mi scratchpad (`git archive HEAD`), con el intérprete del `.venv`.
  - Control sin mutar: 1 failed y 1773 passed. El único fallo es
    `test_f002_r11…manifiesto_de_sv5`, que busca `infra/`, y la copia no lo trae: es del entorno.
  - S189 y S196: **1 failed**, el mismo del control. Sobreviven de verdad.
  - Muertos muestreados:
    - `:90`, `sin_ciz` por defecto `True`: **10 failed**;
    - `:134`, `cod or` → `cod and`: **4 failed**;
    - `:165`, `max` → `min`: **5 failed**.

## Mutación y RM1–RM7

- [x] **Informe generado por la herramienta**, sin «⚠ CAMPAÑA NO VÁLIDA». «Sin veredicto (base
  rota)» es 0, la línea base está medida en los 4 workers (24,3 s) y hay 0 timeouts e
  indeterminados.
- [x] **Totales verificados** (arriba). Sin muestreo: 19 ≤ tope 100, como dice el informe.
- [x] **Coste por mutante**: 176,4 × 4 ÷ 19 = **37,1 s**, por encima de 1 s y del orden de la base.
- [x] **RM1**: el SHA medido es 9784e0e (completo). Hasta HEAD solo cambian un test, `progress/` y
  `specs/`: el alcance medido es el que reviso.
- [x] **RM2**: media 9,3 s × 4 workers = 37,2 s, frente a 24,3 s de base. Con la suite entera, 24,7
  s. No hay salto de orden de magnitud.
- [x] **RM3**: ninguno de los 17 muertos es equivalente.
  - Revisados: `:152`, `:160`, `:162`, `:201`, `:163`, `:165`, `:188`, `:195`, `:236`, `:239`,
    `:197`, `:200`, `:90`, `:134` y los del pipeline `:628` y `:652`.
  - Todos cambian la decisión, el motivo o el WARNING.
- [x] **RM5** (muestra de UNO): elegí el **#2 (`:196`)** y ejecuté además el script entero.
  - `cd services/partes-transfer && python ../../progress/equivalentes_F-083.py` en el árbol:
    **exit 0**, con las dos líneas «equivalente».
  - Controles negativos, todos en la copia:
    - #1 → `if False:` (el del informe): **exit 1**, «caso 4 (list)». El informe dice «caso 5»,
      contando desde 1.
    - **#2 → `if sigue is None:`** (mío): **exit 1**, `AttributeError` en `decidir_fin`.
    - `LineaSigrid` con un `__bool__` falso (mío): **exit 1**, «LineaSigrid define [...]».
  - Mi juicio coincide: `ultima_posterior` solo devuelve `None` o una `LineaSigrid`, y esa
    dataclass no tiene `__bool__` ni `__len__`. Veracidad e `is not None` son la misma condición.
- [x] **RM6**: no se quitó ninguna guarda, y T6 no cambió producción.
- [x] **RM7: aplicada, no N/A.** Corrijo mi criterio de la principal.
  - El requisito central (R2, R8) es una **puerta antes de escribir**: el paso 6 bis omite el
    `fin` o el hermano antes de los conflictos y de `escribir`.
  - Dos mutaciones a mano de `registro_pipeline.py` en la copia, con F-083 sin `-x` y sv5 entera:
  - **A · bajar la puerta un paso**, detrás del paso 7 (conflictos, `_lineas_existentes`).
    - F-083: **79 passed**.
    - sv5: **2 failed**, el del control y `test_f062_r11_propia_ya_existe_sin_hermano`.
    - La suite la caza, pero **solo una suite vecina** (ver H1).
  - **B · bajarla por debajo de `escribir`**, quitándola de `_evaluar`.
    - F-083: **10 failed**: R13 (caso 0730), R14, R15, R16, R17, R10, R11 y R12 ×2.
    - sv5: 50 failed.
  - Copia restaurada y comparada con `diff -q`. El árbol de trabajo no se tocó.
- [x] **Supervivientes**: 2, con análisis completo y **aceptación escrita del humano**.
  - Literal: «acepto ñas 2 equivalentes», el 2026-11-24, registrado en 14d6d5d.
  - Ninguno en `PENDIENTE`; los mutantes a mano de RM7 murieron todos.
- [x] **Encargo de la principal**: `test_f083_puro_r2_con_un_iterador`, reproducido en la copia.
  - Con `candidatas = list(candidatas)`: **1 passed**.
  - Sin ella: **1 failed** (`assert ('crear' == 'intermedio'`). El fichero F-083 entero da
    **1 failed, 78 passed**: solo lo caza ese test. Copia restaurada.
- [x] **Podados**: no hay (selección apagada); sin campaña manual. **RM4**: arriba.
- [x] **«Evidencias»** del `impl`: tests, cobertura, mutantes y tiempo. Los workers no constan en
  el `impl`, pero sí en la fila «Workers» (4) del informe generado (ver O1).
- [x] **Capa e2e**: N/A (`CAPA E2E: N/A`, ningún servicio la declara). sv4 está intacto.

## Checkpoints (cierre)

- **C1** [x] `init.sh` sin caché y exit 0 · [x] ficheros del arnés presentes.
- **C2** [x] una sola activa (F-083, `in_review`) · [x] prioridad 1 · [x] rama de la feature ·
  [x] `current.md` de la sesión activa (con restos, O2) · [x] `history.md`: no aplica hasta `done`.
- **C3** [x] el delta no toca producción. El test nuevo sigue el estilo del fichero, sin `print`
  ni secretos.
- **C3 bis** [x] el delta no trae documentos de fuera. **C3 ter** [x] la aceptación va literal y
  con fecha. **C3 quater** [x] sin cambios desde la principal (5078dc0, sin push).
- **C4** [x] R1–R22 en verde (79 tests F-083) · [x] sin red ni BBDD · [x] MANUAL: M0 hecha.
  **M1–M4 quedan pendientes por el flujo** (T7, tras el merge y antes de desplegar sv5; M1 y M3
  autorizadas el 2026-11-24). No bloquean esta pasada.
- **C4 bis** [x] todo lo de arriba; rigor, RED y cobertura los marcó la principal.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] commits de T1–T6 y T8 · T7 `[ ]` **por el flujo** (MANUAL tras el merge) ·
  [x] `git status` limpio antes y después · [x] `features.json` en `in_review`.

## Hallazgo (no bloquea)

- **H1 (RM7, suite vecina)**: con la puerta bajada detrás de los conflictos, ningún test de F-083
  cae. La caza solo F-062.
  - El orden es de F-060 y F-083 no lo mueve. La escritura sigue protegida: la mutación B da 10
    fallos propios.
  - Pero un `fin` omitido por F-083 pasaría por la lectura de conflictos y podría ofrecerse como
    conflicto.
  - Propuesta, a criterio del humano: un test de F-083 con un parte del periodo con líneas, que
    compare las lecturas exactas del caso 0730.

## Observaciones (para el líder)

- **O1** Añadir a «Evidencias» del `impl` los **4 workers** de la campaña (C4 bis).
- **O2** `current.md` arrastra restos: el título «F-083 · in_progress» y «Pendiente: …
  aceptación de los 2 equivalentes», que ya están aceptados. El docstring de
  `progress/equivalentes_F-083.py` sigue diciendo «pendiente».
- **O3–O5 de la principal siguen en pie**:
  - copiar los comandos de M1–M4 a `current.md` antes de T7;
  - quitar «sin desplegar» de `azure-apps/partes.md` tras desplegar;
  - M1–M3 antes de desplegar sv5 (`MOVER_CIZ` encendido).

## Automejora (propuesta, no aplicada)

- `reviewer.md`, RM7: decir que también entra una feature cuyo requisito central es **omitir una
  escritura**, no solo «la puerta va antes de X». Aquí la principal y el implementer la vimos N/A,
  y la mutación A mostró que la feature no ve sola el orden respecto de los conflictos.
