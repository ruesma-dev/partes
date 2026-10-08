Revisión completa (pasada 1): `git diff dev...79176fb` (base `3b6790f`).

# F-039 · Review

**Veredicto: CHANGES_REQUESTED** (pasada 1). Un único `[ ]`, documental: la
verificación MANUAL M1 no está en `progress/current.md` con su procedimiento
exacto (C4). El código, los tests y las puertas están bien; ver «Cambios
requeridos».

**Nivel de rigor:** `estandar`, declarado en `harness/features.json`. Exige
fase RED, cobertura ≥ 80 % de lo cambiado y campaña de mutación con
supervivientes analizados (RM5 N/A por nivel).

## Qué se verificó (por mí, no leído del informe)

- `bash harness/init.sh` desde el worktree (PATH con el `.venv` del repo
  principal): **ENTORNO LISTO, exit 0**; raíz 461 passed / 3 skipped;
  PUERTA COBERTURA [OK] 100,0 % (6/6); PUERTA TAMAÑO [OK] (71/150, 117/250,
  140/220). sv4 salió por caché de árbol, así que la suite de sv4 la
  reejecuté entera sin caché: **1796 passed, 1 skipped** en 388,6 s.
- Tests de F-039 y los dos ajenos enmendados: `68 passed` (incluye los tres de
  node, que **no** se saltan: node v24.14.1 presente). `node --check
  static/app.js` OK.
- **Solo sv4**: el diff de producción toca `application/services/empresas.py`,
  `interface_adapters/web/app.py` y `static/app.js`; el resto es `tests/` de
  sv4, spec, `progress/`, `features.json` y `BACKLOG.md`. Nada en sv1/2/3/5,
  plantillas, `orm_models.py` ni infra.
- **El dict no se copia a JS**: `app.js` no contiene «Ruesma» ni «Porsan»
  (R10, test); la única fuente es `NOMBRES_EMPRESA` vía
  `nombre_empresa_o_vacio`, usada en los cuatro endpoints y en
  `_candidato_con_empresa` (R11, con test que sustituye la función y ve
  cambiar API y Conciliar a la vez).
- **Todos los sitios que pintaban «empresa N»**: barrido de `static/` y
  `templates/` (`grep -ni empresa` sin los usos de filtrado). El único
  literal « · empresa » era `empresaSufijo`; sus 7 llamadas (`obraLabel`,
  `recLabel`, búsqueda manual l. 761, combos de «+ Nuevo parte» y «+ Añadir
  línea» vía `obraLabel`/`recLabel`) se alimentan solo de
  `/api/sigrid/obras`, `/api/sigrid/recursos` y `/api/conciliacion/buscar`,
  que ya mandan `empresa_nombre`. Quedan «Empresa N» solo en `fijarEmpresa`
  (l. 240) y `conciliacion.html` l. 65, que por construcción solo pintan
  números sin nombre (design §2, fuera de alcance correcto). `data-obra-label`
  nunca llevó empresa.
- **El JS se ejecuta de verdad**: R6–R8 extraen `empresaSufijo` de `app.js` y
  la corren con `node -e` (no solo texto). Para cubrir el riesgo de F-035
  (ReferenceError en el ensamblado) comprobé además: (a) `empresaSufijo` y
  todos sus llamadores viven en la misma IIFE (l. 85–2692); (b) prueba ad hoc
  en una copia en mi scratchpad (no versionada): JSON real de los tres
  endpoints vía `TestClient` → `obraLabel`, `recLabel` y la etiqueta de la
  búsqueda manual ejecutados en node → «070 · Obra 0 · Ruesma», «MO/0001 ·
  PERSONA 1 RECURSO · Porsan», «… · Empresa 5», sin empresa sin sufijo;
  ninguna etiqueta contiene «empresa ».
- **Enmienda R12 (opción A)**: los dos tests ajenos solo añaden
  `empresa_nombre` a lo esperado (diff de 1 y de 6 líneas, nada más).

## Mutación (C4 bis)

- **Recálculo puro** con `harness.alcance.alcance_de_feature` +
  `harness.mutacion.generar_mutantes`: 21 líneas (8 `empresas.py` + 13
  `app.py`) y **3 mutantes**, idénticos al informe; los 2 supervivientes
  existen con el mismo operador y texto (`app.py:1344` `round(sc * 100)` →
  `round(sc // 100)` [aritmetico] y → `round(sc * 101)` [entero]).
- **Campaña no reejecutada: 1505,7 s (≈ 25 min) según el informe** (> 60 s).
- **RM4** sobre una copia de sv4 en mi scratchpad: con cada superviviente
  aplicado, `test_f039_r12_buscar_score_intacto` falla (1 failed, 22 passed);
  con el muerto (`empresas.py:31` `is None` → `is not None`), 13 failed. El
  árbol de trabajo no se tocó.
- **RM1** SHA medido `409cb1c`; desde ahí solo cambian `tests/`, `progress/`,
  `tasks.md` y `BACKLOG.md`: el alcance de producción es el revisado.
- **RM2** coherente: 3 × 501,9 = 1505,7 s; W = 3; `media × W` ≈ 1506 s/mutante
  frente a base ≈ 490 s: más lento, no más rápido; ningún salto a la baja.
- **RM3** el muerto no es equivalente (invierte la guarda: cambia la salida).
  **RM6** no se quitó código defensivo (los supervivientes se mataron con un
  test). Sin «⚠ CAMPAÑA NO VÁLIDA», «Sin veredicto» 0. Supervivientes con
  análisis completo (hueco real preexistente, test nuevo).

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base.
- **C2** [x] una sola `in_progress` (F-039) · [x] rama
  `feature/F-039-nombre-empresa-en-combos` · [x] `current.md` con F-039
  arriba (arrastra otras features: práctica del repo ya aceptada en F-035/36)
  · [x] las `done` tienen resumen en `history.md` (el de F-039 lo escribe el
  líder al cerrar, como en F-035/F-037).
- **C3** [x] hexagonal: la función nueva es pura en `application/services/`,
  el adaptador web solo la llama · [x] primera línea con ruta (test nuevo
  incluido) · [x] sin prints, TODOs, secretos ni dependencias nuevas · [x]
  reglas de dominio: no toca registro, incidencias ni schema.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] cada R1–R12 con test `test_f039_rN_*` en verde (tabla abajo) ·
  [x] sin red ni BBDD (Sigrid simulado, SQLite en memoria, node local) ·
  **[ ] M1 no está en `current.md` con su procedimiento exacto**: solo «y M1
  (humano)». Vive en `tasks.md` e `impl_F-039.md`, pero el checkpoint pide
  `current.md` (mismo motivo que el cambio 3 de F-035 y la pasada 1 de
  F-036/F-037).
- **C4 bis** [x] `rigor` declarado · [x] fase RED con trazas reales (T1: 16
  failed/1 passed; T2: 3 failed/2 passed; score: 2 mutantes a mano) · [x]
  cobertura [OK] 100 % · [x] totales recalculados · [x] muertos: > 60 s →
  recálculo + RM4 (dicho arriba) · [x] coste por mutante ≈ 1506 s · [x] sin
  «NO VÁLIDA», base rota 0 · [x] RM1 · [x] RM2 · RM5 N/A (estándar,
  justificado por nivel) · [x] RM6 · N/A campaña manual (la automática dio 3
  mutantes) · [x] supervivientes analizados · [x] «Evidencias» con los
  cuatro números y workers.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T1–T4 `[x]` con commit `F-039 Tn:` (M1 `[ ]` es la MANUAL del
  humano, como en F-030/F-031/F-035) · [x] árbol limpio · [x]
  `features.json` en `in_progress` (pasa a `done` con el APPROVED).

## Cobertura requisito → test (`services/partes-front/tests/test_f039_nombre_empresa.py`)

| R | Test(s) |
|---|---|
| R1 | `test_f039_r1_obras_lleva_empresa_nombre`, `..._r12_obras_resto_de_campos_intacto` |
| R2 | `test_f039_r2_recursos_lleva_empresa_nombre`, `..._r2_recursos_filtrados_por_empresa` |
| R3 | `test_f039_r3_buscar_lleva_empresa_nombre` |
| R4 | `test_f039_r4_empleados_lleva_empresa_nombre` |
| R5 | `test_f039_r5_nombre_empresa_o_vacio` (×5, con 0), `..._r5_empresa_sin_nombre_es_empresa_n` |
| R6–R8 | `test_f039_r6/r7/r8_empresa_sufijo_*` (node) |
| R9 | `test_f039_r9_combos_usan_empresa_sufijo` |
| R10 | `test_f039_r10_app_js_sin_nombres` |
| R11 | `test_f039_r11_candidatos_conciliar_con_nombre`, `..._r11_misma_funcion_que_los_endpoints` |
| R12 | `test_f039_r12_resto_de_campos_intacto` (×3), `..._r12_buscar_score_intacto`, enmendados `test_f015_r26_sin_fecha_…`, `test_f023_r40_endpoint_obras_…` |

## Cambios requeridos

1. `progress/current.md`, bloque «F-039»: añadir la verificación **M1 ·
   MANUAL (humano)** con su procedimiento exacto, como en `tasks.md`: tras
   desplegar sv4 (`infra/redeploy_partes.ps1`, lo pide el humano), Ctrl+F5
   en el portal; Conciliar → búsqueda manual muestra «· Ruesma»/«· Porsan»
   (no «empresa N»), y lo mismo en los combos de obra y trabajador de
   «+ Nuevo parte» y «+ Añadir línea». Sin tocar código ni tests.

## Observaciones (no bloquean)

- «Evidencias» dice `--workers 6`; el informe de mutación registra 3 (no
  lanza más workers que mutantes). Conviene decir el efectivo.
- R6–R8 ejecutan `empresaSufijo` aislada; aquí basta (llamadores sin cambios,
  misma IIFE, prueba ad hoc arriba).

**Automejora (propuesta, no aplicada)**: cuarta feature rechazada solo por
MANUAL fuera de `current.md` (F-035/36/37/39): que `implementer.md` (todos
los niveles) exija copiarlas allí con su procedimiento, o que `init.sh` avise.
