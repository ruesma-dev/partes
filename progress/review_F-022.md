<!-- progress/review_F-022.md -->
Revisión completa (pasada 1) · diff `e103892..HEAD` (HEAD `44a0332`); alcance de mutación desde `a6c3427` (merge-base con dev)

# F-022 · Aprobar solo las líneas seleccionadas — Review

**Veredicto: APPROVED.** Seis observaciones NO bloqueantes (O1–O6, al final).
El cierre sigue condicionado a M1–M8 (MANUAL del humano).

**Rigor:** `critico` (declarado). Exige RED en R10–R12, R14, R15, R17–R19,
R21–R24, R31 y R32; cobertura ≥ 80 %; mutación completa con 0 supervivientes
sin resolver; MANUAL con comando exacto.

## Lo que decide en qué obra caen las horas (verificado en código y tests)

1. **Una petición = una obra.** Las líneas se agrupan por
   `obra_key_for_registro` y la obra de cada grupo sale de SUS líneas.
   `_payload_grupo` manda solo `grupo.lineas` con `grupo.obra`. Ninguna ruta
   (preflight, ejecutar, encolar con o sin cola) mezcla obras. Tests:
   `r14_preflight_una_llamada…`, `r22_ejecutar_obras_en_orden…` (cada línea
   con el `PT-` de SU obra) y `r20_encolar_una_publicacion_por_obra`.
2. **El resultado se aplica por grupo.** `_trazar` y
   `marcar_registros_encolado` reciben `grupo.registro_ids`. Un `ok:false` o
   una excepción dejan en `error` solo las líneas de esa obra. Un grupo
   bloqueado por Sesame no se traza. Si falla la publicación, `error_cola` sin
   marcas; si fallan todas, 502 (`r21_*`, `r22_*`).
3. **Claves de pisar.** `<grupo>::<clave>` va a su grupo; un grupo
   desconocido se ignora; sin prefijo y con varias obras, 422 en los tres
   endpoints. Una misma clave en dos obras viaja con prefijos distintos y el
   listado cruza solo con el preflight de SU grupo (`r19_*`, en lo puro y por
   endpoint). En el JS, `claveConGrupo`, `clavesDe` y `planEnvio` usan el
   mismo prefijo.
4. **Ámbito.** `_validar_ambito` va antes de leer líneas, contra
   `registro_ids_de_obra(clave, period, mode)` o `registro_ids_de_trabajador`.
   Un id ajeno da 422 `fuera_de_ambito` sin llamar a sv5, publicar ni marcar
   (`r11_*`: 3 endpoints × 5 casos). R12 cubre el tope 5000/5001. F-024 queda
   intacto: `registrado` siempre excluida y `borrado_sigrid` salvo casilla
   (`r13_*`, `r26_*`, `r31_*`).
5. **sv5 sin cambios** (`git diff a6c3427..HEAD -- services/partes-transfer`
   vacío) y el payload con su forma de siempre (`r33_*`). Solo cambia
   `services/partes-front`; ni la lista cerrada de duplicación ni
   `orm_models.py`.
6. **Modal.** Listado, totales y `excluidas_detalle` los da el servidor; el
   JS los pinta con `esc`. El aviso de F-021 se mantiene por grupo
   (`test_f021_y_f022_js…`). El sondeo de F-024 pasa a ser por grupo y
   conserva el respaldo `vigilarEncoladas`. No quedan referencias a las
   funciones retiradas. `node --check` OK.

**Desviaciones §3:** acepto las once. 3.1 y 3.6 endurecen la validación.
3.3 se aparta de la letra de R22 (ver O2). 3.7 evita que un 422 tape un
resultado válido. 3.9 cumple RM6: el invariante está en el origen,
`int(r.fecha_int or 0)` en `parte_repository.py:1341`, y `_tipo` solo
devuelve los tres tipos de `ORDEN_TIPOS`.

## Verificación (resultado real)

- `bash harness/init.sh`: **ENTORNO LISTO**, exit 0. Raíz `419 passed,
  1 skipped`. `PUERTA COBERTURA: 100.0% de 282 líneas cambiadas cubiertas`.
  sv1–sv5 en verde (caché).
- sv4 completa, ejecutada por mí sin caché: **`1428 passed in 137.39s`**.
  Árbol limpio.

## Mutación (verificación independiente)

- **Recálculo puro** (`alcance_de_feature` + `generar_mutantes`): 4 ficheros,
  **594 líneas, 143 mutantes** (81/3/10/49). Coincide con el informe. Los 3
  supervivientes existen con el mismo operador y texto: `reparto_obras.py:84`
  y `parte_repository.py:509` (`or 0→1`), y `app.py:1844` (`False→True`).
- **Campaña no reejecutada**: el informe declara 4506,2 s (75 min) > 60 s.
  Me quedo en el recálculo más RM1–RM6.
- **RM1:** medida sobre `2524bf9…`. Lo que cambió después
  (`git diff --stat 2524bf9..HEAD`) no toca Python de producción: solo
  `app.js`, tests y `progress/`.
- **RM2:** media 31,5 s × 6 workers = 189 s por mutante, frente a una línea
  base de ~303 s. Encaja con `-x` y 140/143 muertos;
  143 × 31,5 ≈ 4506. Sin «CAMPAÑA NO VÁLIDA» y con «Sin veredicto» = 0. El
  timeout se fijó a mano en 600 s, por debajo del derivado (~612 s), pero
  con 0 timeouts no influye.
- **RM3:** no hay equivalentes declarados ni veo ninguno entre los muertos.
  **RM4:** los 3 supervivientes, aplicados en una copia del scratchpad, dan
  **1, 1 y 9 failed**, como declara el informe. **RM5:** N/A (no hay
  equivalentes). **RM6:** ver 3.9.

## Checkpoints

- **C1** [x] init.sh con exit 0 · [x] ficheros base. **C2** [x] una sola `in_progress` · [x] rama de la feature · [x]
  `current.md` con F-022 al frente y los MANUAL. El resto del fichero es deuda
  previa, ya aceptada en F-021, F-023 y F-024 · [x] `history.md` (F-022 aún no
  está `done`).
- **C3** [x] hexagonal: `reparto_obras.py` en application, puro · [x]
  primera línea con la ruta · [x] sin prints, secretos ni dependencias nuevas
  · [x] trampas: el listado lleva `recurso_ide`, la incidencia lleva el código
  y el `can` de sv5, y el esquema no cambia.
- **C3 bis** N/A: no toca `docs/referencia/` (comprobado con `git diff`).
- **C4** [x] trazabilidad (tabla), todo en verde · [x] sin red ni BBDD:
  SQLite, dobles, `node` local y datos sintéticos · [x] M1–M8 en
  `current.md`, con comando exacto en `impl_F-022.md` §7 (mismo criterio que
  en F-024).
- **C4 bis** [x] rigor · [x] RED con trazas reales en `red_F-022.log` para
  todos los centrales **salvo R32** (O1). La aporto yo con una rotura
  deliberada en una copia aislada: con `ambito`, aprobar toda la vista en vez
  de lo pedido. Resultado: `FAILED …r32_ejecutar_lo_no_pedido_no_cambia`,
  `FAILED …r32_encolar_lo_no_pedido_conserva_estado_y_motivo`,
  `FAILED …r10_ambito_obra_sigue_solo_con_los_pedidos`, `3 failed, 3 passed`
  · [x] cobertura 100 % · [x] mutación verificada · [x] RM1, RM2, RM6 · RM5 N/A
  justificado · [x] 0 supervivientes sin resolver · [x] «Evidencias» con los
  cuatro números y 6 workers.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T1–T15 en `[x]`, con commit por tarea (T12 en azure-apps,
  `fdc6e1d`, sin push; T13–T15 juntas) · [x] árbol limpio · [x]
  `features.json` coherente.

## Cobertura: requisito → test

| Req. | Tests |
|---|---|
| R1–R9 | `vistas_seleccion`: `r1_vista_*`, `r2_js_*`, `r3_vista_*`, `r4_js_*`, `r5_js_*`, `r6_js_*`, `r6_r7_js_texto_motivo…` (node, 6 casos), `r8_*`, `r9_*` |
| R10–R13 | `r10_*` (6), `r11_*` (2, parametrizados), `r12_*` (4), `r13_*` (3) |
| R14–R22 | `r14_*` (8), `r15_*` (5), `r16_*` (5), `r17_*` (6), `r18_*` (8), `r19_*` (12), `r20_*` (5), `r21_*` (4), `r22_*` (9) |
| R23–R29 | `r23_*` (9), `r24_*` (7), `r25_*` (4), `r26_*` (6), `r27_js_*`, `r28_*` (2), `r29_js_*` (3, node) |
| R30 | solo JS: `node --check` + M5 (O3) |
| R31–R34 | `r31_*` (2), `r32_*` (2), `r33_*` (3), `r34_vista_las_plantillas_parsean` + suites de sv4 en verde |

## Observaciones para el humano (no bloquean)

- **O1 · RED de R32:** el implementer la despachó con una frase; la sustituye
  mi rotura de C4 bis. Automejora: adjuntar siempre esa rotura deliberada
  cuando un requisito central ya pase antes de existir el código.
- **O2 · `parcial`:** si fallan todas las obras sale `ok:false, parcial:false`
  (3.3), y la letra de R22 pedía `true`. Es una línea; el JS no lo lee.
- **O3 · R30 sin test `r30`:** el resultado y el sondeo por obra son solo JS,
  que la spec manda a MANUAL (como F-024 R29); lo cubre M5.
- **O4 · Escape heredado:** `resumenHtml`, `conflictosHtml`,
  `avisosCalendarioHtml` y `resultadoHtml` (anteriores a F-022) pintan sin
  `esc` `nombre`, `motivo` y `cod`, y esos nombres pueden venir del OCR de un
  PDF recibido por correo. Propongo una feature pequeña.
- **O5 · Pisar por obra:** una obra a la que se le desmarcan todas sus claves
  vuelve a la cola (inocuo por synckey). Además, `sondearGrupos` mete
  `g.clave` sin escapar en un `querySelector`.
- **O6 · Excepción de sv5 en `ejecutar`:** antes daba 500 sin marcas; ahora
  deja `error` en esa obra (es lo que pide R22). Reaprobar es idempotente.
