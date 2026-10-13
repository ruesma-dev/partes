<!-- progress/review_F-043.md -->
Revisión completa (pasada 1) · `git diff dev...HEAD` hasta `53585b1`

# F-043 · Review

- **Veredicto: APPROVED** · **Rigor:** `critico` (declarado): C1–C5, C3 bis, RED,
  cobertura ≥ 80 %, mutación con 0 supervivientes sin resolver, RM1–RM6 y MANUAL.

## Ejecuciones propias (worktree `partes-wt-f043`, 2026-10-13)

- `bash harness/init.sh` → exit 0, **ENTORNO LISTO**. Raíz 487 passed, 3 skipped;
  `PUERTA COBERTURA` [OK] 99,4 % (160/161, umbral 80 %); `PUERTA TAMAÑO` [OK].
- init.sh sirvió sv1–sv5 de caché: relancé a mano sv3 **1.180 passed** y sv4 **2.068 passed, 1 skipped** (268 s). `node --check` en verde (test propio).
- Árbol limpio tras todo (`git status` vacío).

## Puntos pedidos por el coordinador

- **Tests existentes intactos:** `git diff dev...HEAD --name-status -- '*tests*'` da
  solo `A` salvo `M test_f042_recalculo_fecha.py`. Su diff toca solo el doble de DOM
  (`activeElement`, `confirm`, respuesta del alcance, funciones extraídas) y dos
  aserciones permitidas por la enmienda A (temporizador `timer:5000` con `pedido` y
  orden alcance→PATCH). `TEXTO_PEDIDO/FALLO/SIN_COLA` y «✓ Guardado» **sin tocar**.
- **`orm_models.py`:** `cmp` → idénticas; 4 columnas nullables, fuera de deshacer.
- **Protocolo pedido/terminado:** sv4 `update_parte_fecha` (commit) → `marcar_recalculo_pedido`
  (commit) → publicar; si `fallo`, `anular_recalculo_pedido` con `WHERE pedido = :pid`.
  sv3 `_recalcular`: `pedido_actual` → `conciliar_todos()` **sin try** → `marcar_terminado`
  con `WHERE id = :doc AND recalculo_pedido_id = :pid`. Si la pasada lanza, no se marca
  y se propaga (`test_f043_r29_*`). Razonado también el desorden: un mensaje viejo lee
  el pedido *actual*, cuya confirmación es posterior a la fecha nueva, así que marcarlo
  es correcto; uno que leyó un pedido anterior no marca (`test_f043_r32_ciclo_real_*`,
  con el adaptador real sobre SQLite).
- **409 del parte en espera:** `_exigir_sin_recalculo(doc)` va detrás de las 7 guardas
  de F-004 (grep: 8 llamadas a `_exigir_*_editable`, 7 con la guarda nueva y
  `update_parte_fecha` sin ella); `undo_last` no usa guardas. Comprueba solo el
  documento de la línea: `test_f043_r38_otro_parte_se_edita_mientras_uno_espera`. Fecha
  y deshacer pasan (`r38_la_fecha_*`, `r38_deshacer_*`). Vence a los 600 s
  (`r38_el_parte_vuelve_a_editarse_al_vencer`, borde en `test_f043_estado_*`). El 409
  sale por el manejador de `CongeladoError` de F-004 con `{ok, congelado, error}`.
- **Nada recarga solo:** `location.reload` pasa de 22 (dev) a 23; el único nuevo está
  en `actualizarVista`, que solo cuelga del botón «Actualizar». El sondeo
  (`setTimeout` encadenado, 5 s) nunca recarga ni toca foco. «Actualizar» guarda URL,
  scroll de ventana, `.table-scroll`/`.matrix-scroll` y `.col-filter`; `restaurarVista`
  corre después de `wireColumnFilters` y reaplica con evento `input` (tests R21).
- **Enmienda (resto del portal usable):** `ponerEnEspera` solo toca
  `tr[data-document-id=X]` y `[data-parte-contenido][data-document-id=X]`; tarjeta no
  modal (`role=status`); «Seleccionar visibles» salta las filas en espera; test
  `r18_poner_en_espera_solo_ese_parte` comprueba que el otro parte queda libre.
- **`azure-apps/partes.md`:** commit local `61d1688`, solo ese fichero (§4.1 + nota).

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros base presentes.
**C2** [x] una sola `in_progress` (F-043) · [x] rama `feature/F-043-…` · [x] `current.md`:
F-043 + la sección de F-042 que se conserva por sus MANUAL pendientes (ya estaba en
dev; práctica del repo) · [x] las `done` tienen resumen en `history.md` (init.sh).
**C3** [x] hexagonal: `seguimiento_recalculo.py` puro (test AST lo vigila); adaptadores
en `infrastructure/` · [x] primera línea con ruta en los ficheros nuevos · [x] sin
prints/console.log/secretos/dependencias nuevas · [x] trampas: (1) y (2) no se tocan;
(3) esquema cambiado en las dos copias, idénticas. LÍMITE DE SERVICIO: nada se
duplica; la lista cerrada de `CLAUDE.md` no crece; `congelacion.py` sin cambios.
**C3 bis** (modifica `docs/referencia/partes-proyecto.md`): [N/A] cabecera de documento
nuevo — no hay documento nuevo, solo se edita uno existente · [x] sin PDF/ofimática
(`git log dev..HEAD --diff-filter=A` filtrado por extensión: vacío) · [x] barrido
propio sobre las 42 líneas añadidas en `docs/` y sobre el commit de azure-apps,
patrones: correo `\S+@\S+\.[a-z]{2,}`, IPv4, GUID, `password|secret|token|apikey|
AccountKey|SharedAccess|sig=|Bearer|-----BEGIN`, base64 ≥ 32, DNI `\d{8}[A-Z]` → 0
coincidencias · [N/A] nada redactado (no hacía falta).
**C4** [x] trazabilidad completa (tabla abajo), todo en verde · [x] sin red ni BBDD real
(SQLite en memoria, dobles, node con DOM mínimo) · [x] M1–M4 y el despliegue sv3→sv4
en `current.md` con SQL/órdenes exactas.
**C4 bis**
- [x] `rigor: critico` declarado.
- [x] Fase RED: trazas reales T1–T9 en `impl_F-043.md` (T8 contra copia con el
  `wireFechaInput` de F-042; versión larga en `7c9eecf`).
- [x] Cobertura [OK] 99,4 %.
- [x] Mutación recalculada por mí (`alcance_de_feature` + `generar_mutantes`): 9
  ficheros, **436 líneas, 60 mutantes** = informe. Supervivientes muestreados (#3
  `orm_models.py:101 String(36)→String(37)` [entero], #6 `app.py:1935
  include_in_schema False→True` [booleano]) existen con mismo operador y texto.
- [x] Muertos: «Tiempo total» 4.014,8 s > 60 s ⇒ **campaña no reejecutada** (67 min
  según el informe); recálculo puro + RM1–RM6 + RM4 abajo.
- [x] Coste por mutante 4.014,8 × 6 ÷ 60 = **401 s**. Sin «CAMPAÑA NO VÁLIDA»; base
  rota = 0; línea base medida en los 6 workers.
- [x] RM1: SHA medido `d8d51a5…`; `git diff --stat d8d51a5..HEAD` solo toca tests,
  `progress/` y `tasks.md`: ningún fichero del alcance cambió después.
- [x] RM2: media 66,9 s × 6 = 401 s frente a base sv4 446 s; total = 60 × 66,9.
- [x] RM3 (criterio): recorrí los 50 muertos; ninguno equivalente. Comprobado aparte
  que `synchronize_session=True` (3 mutantes) lanza `ArgumentError` en SQLAlchemy
  2.0.52: muerte legítima.
- [x] RM4 (copia en scratchpad, `git archive HEAD`): reaplicados los supervivientes #3
  (sv3 y sv4) y #6 ⇒ los tests nuevos fallan (2 y 1 failed); muertos de control
  `recalculo_seguimiento.py:58 == → !=` (7 failed) y `parte_repository.py:742 == → !=`
  (45 failed).
- [N/A] RM5: ningún equivalente declarado. [N/A] RM6: no se quitó ninguna guarda (tras
  la campaña solo entraron tests). [N/A] Campaña manual: la automática dio 60.
- [x] 10/10 supervivientes analizados, ninguno `PENDIENTE`; todos cazados por 5 tests
  nuevos ⇒ 0 sin resolver, no hace falta aceptación del humano.
- [x] «Evidencias» con los cuatro números y los 6 workers.
**C4 ter** [N/A] el repo no tiene `harness/rutas_sensibles.json`.
**C5** [x] T1–T15 `[x]`; 14 commits `F-043 Tn:` (T13 y T14 comparten uno,
`4cbb059`, que nombra las dos: trazable, lo anoto) · [x] sin temporales · [x]
`features.json` en `in_progress` con `rigor` y `acceptance` enmendados.

## Cobertura requisito → test (sv4 `tests/test_f043_*`, sv3 `test_f043_seguimiento_sv3`, raíz `tests/test_f043_contrato_seguimiento`)

| Req. | Tests |
|---|---|
| R1 | `r1_la_cabecera_dice_fecha_del_parte`, `r1_cada_fecha_edit_lo_explica` |
| R2–R4 | `r2_alcance_*` (5), `r3_*_404` (2), `r4_alcance_no_escribe_nada` |
| R5–R11 | `r5_*` (5), `r6_fmt_fecha_es`, `r6_r7_texto_*`, `r7_*` (2), `r8_*`, `r9_*`, `r10_*` (2), `r11_*` (2) |
| R12–R16 | `r12_*` (8, incl. «confirmada antes de publicar»), `r13_*` (3), `r14_*` (4), `r15_*` (2), `r16_*` (sv4 y raíz) |
| R17 | `r17_*` (9) + `estado_*` (8) |
| R18–R26, R40 | `r18_*` (9), `r19_r40_*`, `r20_*`, `r21_*` (6), `r22_*`, `r23_*` (5), `r24_*`, `r25_*`, `r26_*` |
| R27–R33 | `r27_*`, `r28_*`, `r29_*`, `r30_*` (2), `r31_*` (6), `r32_*` (4), `r33_*` (3) |
| R34–R35 | `r34_*` (raíz ×4, DDL sv3 y sv4), `r35_*` (2) |
| R36 | lectura: `ARCHITECTURE.md` (sem. 3, 7, 10), `partes-proyecto.md`, azure-apps `61d1688` |
| R37–R39 | `r37_*` (7), `r38_*` (6 + 7 del repositorio), `r39_*` (3 + 7) |

**Cambios requeridos:** ninguno.

## Observaciones para el humano (no bloquean; la spec las deja fuera o así lo aprobó)

1. **Ediciones en bloque sin la guarda 409.** R38 cubre solo lo que pasa por
   `_exigir_*_editable`. `reassign_empleado_by_registro_ids/_by_leido/_by_worker_key`
   (`app.py:1449-1473`) y `soft_delete_obra/_worker` (`app.py:3083, 3094`) filtran la
   congelación con `_separar_congeladas` y **no** miran la espera: otra pestaña o una
   selección hecha antes pueden reasignar o borrar líneas del parte a mitad de pasada.
   Es la clase de riesgo R-g (anterior a F-043, ya fuera de alcance). Propuesta:
   meterlo en F-044 (que ya debe llamar a `_exigir_sin_recalculo`) o en una feature
   aparte.
2. **Deshacer encadenado.** `undo_last` es LIFO global: el primer «Deshacer» revierte la
   fecha y pide otra pasada, pero un segundo clic puede revertir una edición anterior
   de **ese** parte mientras sigue en espera, sin pedir recálculo. DA11 lo permite;
   la justificación de DA11 («pide su propia pasada») solo vale para `parte_fecha`.
3. `getattr` en `main_worker.py` (T3): validado por el coordinador, cubierto por R33.
4. Pendiente: despliegue sv3 → sv4 y M1–M4 (los lanza el humano).

**Automejora (propuesta, no aplicada)** a `reviewer.md`: si una spec define una guarda
por «lo que pase por X», listar los métodos mutantes del agregado que NO pasan por X
(aquí destapó la observación 1).
