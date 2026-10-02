<!-- progress/review_F-028.md -->
Revisión completa (pasada 1) · `git diff dev..HEAD` (base `ab74d17`, HEAD `18d9c07`)

# F-028 · Detalle de obra y de trabajador a todo el ancho — Review

- **Veredicto:** APPROVED (con observaciones, ninguna bloqueante)
- **Nivel de rigor:** `estandar`, declarado en `harness/features.json`. Exige
  RED en los requisitos centrales, cobertura de lo cambiado y mutación. Las dos
  últimas son **N/A justificadas por lenguaje** (ver C4 bis).
- `sdd: false`: contrato = descripción + 4 `acceptance`. Sin `tasks.md`.

## Verificación ejecutada por el reviewer

- `bash harness/init.sh` (tal cual): **ENTORNO LISTO**, exit 0. Raíz `419
  passed, 1 skipped`; sv1–sv5 en verde (sv4 por caché); `PUERTA COBERTURA: N/A
  (F-028 no cambia líneas Python de producción frente a dev)`; `PUERTA TAMAÑO`
  impl 140/220. Avisos previos: ruff 557 (deuda), F-014 `blocked`, infra sin tests.
- Como sv4 salió de caché, suite de sv4 **re-ejecutada sin caché** en el árbol
  real: `1548 passed, 1 warning in 202.26s`. Tests de F-028: 13 passed.
- `git status` limpio tras todo (salvo este informe).

## Alcance del diff

Solo sv4 y solo lo previsto: `base.html`, `obra_detail.html`,
`trabajador_detail.html`, `styles.css:77`, `tests/test_f028_ancho_detalle.py`,
más papeleo. Bloque y clase no se usan en ningún otro sitio (grep `services/`).

## Revisión técnica pedida por el líder

- **Topbar sin cambios:** `base.html:14` sigue `<div class="container topbar-inner">`;
  el bloque solo está en el div del `<main>`. Ojo: la topbar seguirá centrada a
  1500 px mientras el detalle va a todo el ancho; es lo que pide el acceptance 3.
- **Listados:** el bloque es vacío por defecto ⇒ `class="container"` literal en
  `/obras`, `/trabajadores`, `/partes` (y en el resto de páginas).
- **Cascada:** `.container--ancho` (0,1,0) va después de `.container` (0,1,0)
  ⇒ pisa `width`; hereda `margin: 0 auto`. No hay otra regla `.container` en el
  fichero (ni en media queries), `styles.css` es la única hoja propia.
- **Otros topes que limiten el detalle:** ninguno. `.panel` (sin ancho),
  `.matrix-scroll` y `.table-scroll` (solo `overflow-x:auto`), `.matrix` (ancho
  natural), `.table` (`width:100%`), `.stat-grid`, `.page-header`, `.cal-*`,
  `.day-filter-bar`, `.sel-tools`: sin `max-width`. Los `max-width` existentes
  son internos (`.mx-name` 260, `.mx-cat` 110, combos, modales). Sin estilos
  inline en las dos plantillas.
- **JS de la tabla de líneas** (`app.js:1817-1834`, columnas redimensionables):
  fija `th.style.width` al ancho medido o al **guardado en localStorage**,
  `table-layout:fixed`, `width = suma de columnas` y `min-width:100%`. Con el
  contenedor más ancho, la tabla rellena el 100 % y no hay scroll salvo que la
  suma guardada lo supere. Ver observación O2.

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros base presentes.
**C2** [x] una sola `in_progress` (F-028) · [x] rama `feature/F-028-ancho-detalle`
· [x] `current.md` describe F-028; la sección de F-025 que sigue ahí son sus
verificaciones manuales pendientes (práctica vigente del repo, no resto de
sesión) · [x] features `done` con resumen en history (sin cambios aquí).
**C3** [x] hexagonal: solo plantillas/CSS del adaptador web y un test ·
[x] primera línea con ruta en `styles.css` y en el test. Las plantillas
tocadas no la llevan, pero ya no la llevaban (solo `admin_jornadas.html` la
tiene): deuda previa, no introducida, ver O3 · [x] sin prints, TODOs, secretos
ni dependencias nuevas · [x] trampas de dominio (empleado≠recurso,
incidencias, schema duplicado): N/A, la feature no toca dominio, registro ni ORM.
**C3 bis** N/A: no toca `docs/referencia/`.
**C4** [x] cada acceptance con test trazable `test_f028_rN_*` (tabla abajo), en
verde · [x] sin red ni BBDD (SQLite en memoria, `TestClient`) · [x] M1 manual
listado en `current.md` con los pasos exactos (es visual: no hay comando).
**C4 bis**
- [x] `rigor: estandar` declarado.
- [x] **Fase RED**: traza real pegada en `impl_F-028.md` §4 (4 failed / 9
  passed; los 9 son de no regresión, correcto que pasen antes). Reproducida por
  el reviewer en copia aislada (abajo).
- [x] **Cobertura**: N/A con motivo impreso por `init.sh` (ninguna línea Python
  de producción cambiada).
- [x] **Mutación**: N/A **justificado por lenguaje**. Recalculado:
  `harness.alcance.alcance_de_feature('F-028')` → `lineas={}`. Prueba de
  control del cero: `generar_mutantes` sobre el fichero de test (sin exclusión)
  da 16 mutantes ⇒ el generador funciona; sobre `styles.css` y `base.html` da
  0 ⇒ el cero es por diseño (solo muta Python), no generador roto ni informe
  falso. Sin `progress/mutacion_F-028.md` porque la herramienta sale con
  alcance vacío antes de escribirlo.
- N/A muertos comprobados / tiempo / cabecera NO VÁLIDA / RM1 / RM2: no hay
  campaña automática que verificar (alcance vacío, motivo arriba).
- N/A RM5 (nivel `estandar`) · N/A RM6 (no se quitó ninguna guarda) · N/A
  supervivientes con análisis (no hay).
- [x] **Campaña manual sustituta**: el «sustituto» que declara el implementer
  (los 4 tests RED) **no basta por sí solo** como campaña manual: está descrito
  con palabras, sin tabla original→mutado (O1). No bloquea porque la puerta es
  N/A por lenguaje, y porque el reviewer la ha ejecutado reproduciblemente
  (tabla siguiente).
- [x] «Evidencias» con los cuatro números (workers N/A: no hubo campaña).
- [x] Ningún N/A sin justificar en este bloque.
**C4 ter** N/A: `init.sh` no señala rutas sensibles tocadas.
**C5** N/A `tasks.md` (sdd=false; commits `F-028 T1/T2` y `F-028: ...`) ·
[x] sin temporales sin trackear · [x] `features.json` en `in_progress`, coherente.

## Campaña manual del reviewer (copia aislada vía `git archive HEAD`, scratchpad)

Comando por fila: `python -m pytest tests/test_f028_ancho_detalle.py -q -p no:cacheprovider`
sobre `services/partes-front` de la copia, restaurando el original entre filas.

| # | Fichero | Original → mutado | Resultado |
|---|---|---|---|
| M1 | styles.css:77 | `.container--ancho { width: calc(100% - 32px); }` → (línea borrada) | MUERTO, 2 fallos |
| M2 | obra_detail.html:4 | `{% block container_class %} container--ancho{% endblock %}` → (borrada) | MUERTO, 1 |
| M3 | trabajador_detail.html:4 | ídem → (borrada) | MUERTO, 1 |
| M4 | styles.css:77 | `width: calc(100% - 32px);` → `width: min(1500px, calc(100% - 32px));` | MUERTO, 1 |
| M5 | styles.css:77 | `width: calc(100% - 32px); }` → `width: calc(100% - 32px); max-width: 1500px; }` | MUERTO, 1 |
| M6 | styles.css | regla `.container--ancho` movida antes de `.container` | MUERTO, 1 |
| M7 | base.html:45 | `{% block container_class %}{% endblock %}` → `{% block container_class %} container--ancho{% endblock %}` | MUERTO, 3 |
| M8 | base.html:14 | `class="container topbar-inner"` → `class="container{% block container_class %}{% endblock %} topbar-inner"` | MUERTO, 10 (bloque duplicado ⇒ 500) |
| M9 | styles.css:75 | `width: min(1500px, calc(100% - 32px))` → `width: calc(100% - 32px)` | MUERTO, 1 |

9/9 muertos, 0 supervivientes. La RED del implementer queda reproducida (M1–M3).

## Cobertura acceptance → test

| Acceptance | Tests |
|---|---|
| 1 · detalle con clase ancha, sin tope | `test_f028_r1_detalle_contenedor_main_con_clase_ancha` (obra, trabajador), `test_f028_r1_css_clase_ancha_sin_tope`, `test_f028_r1_css_clase_ancha_despues_de_container` |
| 2 · listados con tope 1500 | `test_f028_r2_listado_contenedor_main_sin_clase_ancha` (3 URLs), `test_f028_r2_css_container_conserva_tope_1500` |
| 3 · topbar sin cambios | `test_f028_r3_topbar_sin_cambios` (5 URLs) |
| 4 · suite sv4 en verde | suite completa: 1548 passed (reviewer, sin caché) |

## Observaciones (no bloqueantes)

- **O1.** El «sustituto» de mutación del informe es un párrafo, no una campaña:
  en futuras features de solo plantillas/CSS, o se declara N/A por lenguaje a
  secas con el alcance vacío, o se trae la tabla original→mutado.
- **O2.** Usuarios con anchos de columna guardados en localStorage (de cuando
  el contenedor medía 1500 px) verán la tabla de líneas estirada por
  `min-width:100%`, no scroll; si hubieran ensanchado columnas por encima del
  nuevo ancho, seguirán teniendo scroll (doble clic en la manija lo reajusta).
  Conviene tenerlo en cuenta en M1.
- **O3.** Las plantillas no llevan la ruta en la primera línea (deuda previa).
- **O4.** El CSS en navegador no tiene arnés: M1 (manual) es la única prueba.

**Automejora (propuesta, no aplicada):** en `CHECKPOINTS.md` C4 bis, prever
el caso «proyecto Python, feature sin líneas Python de producción»: mutación
N/A por lenguaje con `harness.alcance` vacío como evidencia (hoy solo se
contempla «proyecto no Python» y se resuelve por analogía).
