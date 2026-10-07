<!-- progress/review_F-035.md -->
Revisión completa (pasada 1): `git diff dev...163320d` (rama `feature/F-035-selector-recursos-por-empresa`, merge-base `6e56244`)

# F-035 · Review

**Veredicto: CHANGES_REQUESTED**

**Rigor:** `estandar` (declarado): fase RED, cobertura ≥ 80 % y mutación con
supervivientes analizados. RM5 N/A por nivel.

## Motivo del rechazo (uno, bloqueante)

**Bug JS en «Nuevo parte» (R17/R19, regresión).** En `static/app.js`, el callback
de selección del combo de trabajador de `wireNuevoParte` renombró su parámetro
de `e` a `r`, pero quedan tres usos de `e` (l. 1581, 1583, 1584: `e.categoria`,
`e.jornada_sugerida` ×2). `e` no existe en ningún ámbito envolvente (callback,
`wireNuevoParte`, IIFE de l. 85 en `"use strict"`; el único `var e` está en
otro IIFE, l. 26). Reproducido con node aislando el callback:
`ReferenceError: e is not defined`, después de escribir los hidden
(`emp-reside = 903`) y **antes** de categoría, jornada sugerida, recarga del
calendario y `updateBtn()`. Efecto: todo parte creado a mano queda **sin
categoría** (campo `readonly` que «viene del trabajador»), sin jornada
sugerida, con el calendario del trabajador anterior y sin reevaluar «Crear».
`node --check` no lo ve y `test_f035_r17_r19_js_…` solo cuenta cadenas. El
modal (`wireAddLine`) usa `r.` y está bien.

## Qué se ejecutó (resultado real)

- `bash harness/init.sh`: **ENTORNO LISTO**, exit 0. Raíz 446 passed, 1 skipped;
  sv1–sv5 verdes por caché; **COBERTURA [OK] 96,9 % (187/193)**; **TAMAÑO OK**
  (142/150, 248/250, 207/220). Avisos previos (F-014/F-032, ruff 623, infra).
- Suite sv4 **sin caché** (`-p no:cacheprovider -x`): **1764 passed** en 582,8 s.
- **Fase RED reproducida**: copia `git archive 91b80db` (antes de T3) con
  `test_f035_repositorio.py` de HEAD → **15 failed, 10 passed**, como el informe.
- **Mutación, recálculo puro**: `alcance_de_feature` = 454 líneas (107+67+109+171),
  `generar_mutantes` = **69**; el sorteo con semilla `20260820` reproduce los
  20 evaluados, y los 3 supervivientes y 6 timeouts existen tal cual.
  **Campaña no reejecutada: 5973,8 s según el informe** (> 60 s).
- **RM4 en copia** (`git archive HEAD`, scratchpad): `sigrid_lookup_client.py:358`
  `and`→`or` → 1 failed; `app.py:1191` `ok False`→`True` → 2 failed. Los dos
  tests añadidos tras la campaña matan lo que dicen.
- Choques con F-036 y `dev` simulados con `git merge-tree` (árbol intacto).

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base.
- **C2** [x] una `in_progress` · [x] rama correcta · [x] `current.md` con F-035
  arriba (arrastra otras features: práctica del repo ya aceptada) · [x] `done`
  en `history.md`.
- **C3** [x] hexagonal (dominio intacto; `recurso_catalog` importa de
  infraestructura igual que `EmpleadoCatalog`) · [x] ruta en primera línea ·
  [x] sin prints/TODOs/secretos/dependencias · [ ] **reglas de dominio en la
  UI**: el bug rompe el alta manual. Empleado ≠ recurso: bien (`empleado_reside`
  = `res.ide`, recurso soltado F-023 R42, sv3/sv5 intactos).
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [ ] R17/R19 trazables y verdes pero **sin test del comportamiento
  roto** (cambio 2) · [x] sin red ni BBDD · [ ] T9 MANUAL no está en
  `progress/current.md` con su comando exacto (sí en `tasks.md`/impl).
- **C4 bis** [x] `rigor` declarado · [x] fase RED real (T1–T5 + R16) · [x]
  cobertura [OK] · [x] totales recalculados · [x] muertos: > 60 s, recálculo +
  RM4 · [x] coste por mutante 5973,8 × 6 ÷ 20 ≈ 1792 s (> 1 s) · [x] sin «NO
  VÁLIDA», base rota 0 · [x] **RM1** SHA `35fcfe4`; después solo cambian
  tests, docs y progress, nada del alcance · [x] **RM2** 298,7 × 6 ≈ 1792 s vs
  base ~1470 s (timeouts de 1200 s): coherente · [x] **RM3** ningún
  equivalente muerto; el equivalente `recurso_catalog.py:73` es cierto
  (`time.time()`: `now - 0` nunca < 600) · RM5 N/A (estándar) · [x] **RM6** no
  se quitó defensa · N/A campaña manual · [x] supervivientes analizados (acepto
  `top_n` y `alias_ok`, previos, sin test) · [x] «Evidencias» con 6 workers.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [ ] T9 `[ ]` (MANUAL del humano: no imputable) · [x] commits
  `F-035 Tn:` · [x] árbol limpio · [x] `features.json` en `in_progress`.

## Cobertura requisito → test (`test_f035_*`)

| R | Tests |
|---|---|
| R1–R4 | `r1_una_consulta_paginada…`, `r1_encadena_paginas`, `r2_*` ×5, `r3_sin_dni…`, `r4_solo_clase_persona…` |
| R5–R6 | `r5_*` (catálogo ×4, endpoint ×4), `r6_*` ×2 |
| R7–R10 | `r7_*` ×2, `r8_*` ×3, `r9_buscar_por_empresa`, `r10_*` + `r10_r11_r21_js_…` |
| R11–R16 | `r11_recurso_desconocido_404…`, `r12_*`, `r13_*`, `r13_r14_*`/`r21_r14_*`, `r15_*` ×9, `r16_*` ×2 |
| R17–R19 | `r17_r18_*` (HTML), `r17_r19_js_…` (texto: **no cubre el callback**), `r19_*` ×5 |
| R20–R24 | `r20_*` ×2, `r21_*` ×3, suite sv4 + excepción F-016, raíz `r23_…`, diff de docs |

## Alcance y decisiones del humano (verificado)

- Solo sv4 + `CLAUDE.md`, `ARCHITECTURE.md`, guardián raíz F-023 y la línea
  del guardián F-016 (opción a). sv3, sv5, schema, `_SQL_EMPLEADOS` y
  `/api/sigrid/empleados` intactos. `styles.css` (2 reglas) fuera de design §2:
  menor y declarado.
- `res.cla = 1`, empresa `rescon.emp`, alta F-023 a hoy, en SQL; sin DNI no
  se ofrece; DNI guardado con ficha `emp.dni` y, vacío, el del recurso (R12);
  sin ficha `res.cif`. DA1 (`fijarEmpresa` bloquea con obra), DA2 y la
  desviación `_METODOS_CASADO_SIN_FICHA` cumplidas.
- Conciliar (servidor + búsqueda con `empresa`), Nuevo parte y modal
  (`/api/sigrid/recursos` + selector), detalle de obra (filtrado por
  `data-empresa` = empresa de la ficha de obra) y «Reasignar a…» ofrecen
  recursos persona y envían `recurso_ide`/`reside`.

## Choques previsibles al mergear con F-036 y `dev`

1. **F-035 sobre `dev` (con F-037)**: conflicto solo en `BACKLOG.md`
   (regenerar) y `progress/current.md`.
2. **`ARCHITECTURE.md` semántica 12: conflicto seguro.** F-036 reescribe la
   frase F-030 que F-035 amplía: dejar el texto de F-036 + la frase de F-035
   con el DNI en el orden de F-036 (`emp.dni`, vacío `res.cif`).
3. **`CLAUDE.md`: auto-merge textual, choque semántico.** F-036 da de alta
   `res.cla = 1` duplicado en sv3/sv5 con guardián
   `tests/test_f036_recurso_persona_gemelos.py`; `_SQL_RECURSOS_ACTIVOS` de sv4
   es una **tercera copia** que ni esa entrada ni ese guardián cubren. Quien
   mergee segundo añade sv4 a la entrada y una comprobación al guardián.
4. `features.json`, `BACKLOG.md`, `current.md`: conflictos triviales.
5. Semántica compatible: F-036 no cambia `METODOS_RECURSO` de sv3 y su
   conciliador confirma `empleado_reside`, lo que deja F-035 en `recurso_manual`.

## Cambios requeridos

1. `services/partes-front/static/app.js` l. 1581, 1583 y 1584: `e.categoria` →
   `r.categoria` y `e.jornada_sugerida` → `r.jornada_sugerida` (las dos).
2. Test de no regresión en `test_f035_vistas.py` que vigile el ámbito, no
   cadenas: aislar el callback de `"emp-combo"` (de `_comboSimple("emp-combo"`
   a `deLaEmpresaDe(selEmpresa)`) y comprobar que no usa `e.` y sí
   `r.categoria`/`r.jornada_sugerida`, o ejecutarlo con `node` y un `document`
   falso (`skip` con motivo si falta node). Pegar su fallo con el código actual.
3. `progress/current.md`: añadir T9 con su comando exacto
   (`python services/partes-front/main.py`, `.env` local, Ctrl+F5) y las tres
   comprobaciones.

## Observaciones (no bloquean; para el líder/humano)

- **Orden del DNI ofrecido**: R2 muestra/busca `res.cif` y, vacío, `emp.dni`;
  lo **guardado** con ficha ya es `emp.dni` primero (R12), como F-036 y como lo
  formula el líder. Unificar exigiría cambiar R2 y `fetch_recursos_activos`.
- `_poner_trabajador` no limpia `recurso_manual` al reasignar luego a una
  ficha (sigue casada por `empleado_ide`; solo engaña la etiqueta).
- `azure-apps/partes.md` §3.3 enumera los métodos que el portal da por
  casados: valorar añadir `recurso_manual`.
- `/api/sigrid/recursos`: con Sigrid caído en la primera carga responde
  `ok: true, items: []` (el catálogo traga el fallo por R6), no `ok: false`.
