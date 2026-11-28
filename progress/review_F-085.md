<!-- progress/review_F-085.md -->
Revisión incremental desde 33663c4 (pasada 2, principal) · delta `33663c4..05e25f6`

# F-085 · Review (pasada principal)

**Veredicto: APPROVED** · **SHA aprobado: `05e25f6`**. Sobre él, el líder lanza la campaña
(T9, T14), y la pasada de evidencias revisa el delta.
Pasada 1 (33663c4): CHANGES_REQUESTED con 2 cambios (R1 en `_fin_movido`; R8 con la selección
múltiple de un mismo parte). El resto quedó en verde y se da por bueno (resumen abajo).

**Nivel de rigor: `critico`** (declarado). Exige fase RED, cobertura ≥ 90 % de lo cambiado,
mutación con 0 supervivientes sin justificar y RM1–RM7. Mutación, RM1–RM6 y supervivientes quedan
**«pendiente: pasada de evidencias»**. Capa e2e N/A: ningún servicio declara el bloque. El diff no
toca `harness/rigor.local.json`.

## C1 — `init.sh` (pasada 2)
- [x] 1.ª ejecución de `ARNES_SIN_CACHE=1 bash harness/init.sh`: todos los servicios en verde
  **sin caché** (sv1 74, sv2 579, sv3 2989, sv4 4259, sv5 1988). La raíz cayó **solo** en el
  inestable conocido `tests/test_f059_ejecucion.py::test_f059_r9_timeout_mata_el_arbol_y_no_es_rojo`
  (`assert not _vivo(nieto)`; `1 failed, 1571 passed`).
- [x] 2.ª ejecución, con caché como se permite al repetir: **exit 0**. Raíz `2553 passed, 50
  skipped` (1283 s). La caché de los servicios es la del verde sin caché que acababa de ver.
  `PUERTA COBERTURA: 100.0% (220/220)`, `PUERTA TAMAÑO` dentro (impl 218/220), `CAPA E2E: N/A` y
  `ENTORNO LISTO`.

## Delta de la pasada 2
**Cambio 1 (R1)**, a37ef7f: [x].
- `_fin_movido` usa `cod and not es_codigo_fin(cod)`; el comportamiento no cambia.
- `prohibido` gana `'!= "CIZ"'` y `"!= 'CIZ'"`, con RED real (`AssertionError:
  ('infrastructure/database/parte_repository.py', '!= "CIZ"')`); `r28_*` sigue en verde.
- Lo que deja el grep es de otras features: `sincronizacion.py` (F-052) e `incidencias_horas.py`
  (F-025). Bien que no se haya tocado.

**Cambio 2 (D16 = (b))**, 5bca774 + 091a44d + df4706d: [x].
- La cita literal con su fecha («,1 b», humano, 2026-11-27) está en dos sitios que sobreviven:
  design §12 (fila D16) y `current.md` (punto 5).
- R8, R13 y design §2 están enmendados en ese sentido, y también la semántica 3 de
  `ARCHITECTURE.md`, que vigila `test_f085_documentacion.py`.
- `onChange` resuelve cada PATCH por separado:
  - fallo parcial en una selección: `alert` «N de M línea(s) no se han guardado», agrupado por el
    texto del servidor y con los ids de las líneas, y recarga si alguna se guardó;
  - si fallan todas: aviso, marca de error y sin recarga;
  - con una sola línea, como en `dev`. Cumple R13 enmendado (y recarga aunque solo cambie el código).
- **¿Puede quedarse la pantalla desfasada?** No veo ningún camino.
  - Si sale bien cualquier petición, recarga y pinta el estado del servidor, sea cual sea la
    concurrencia de `Promise.all`.
  - Si no sale bien ninguna, el servidor no ha cambiado.
  - Que con concurrencia pasen varias antes de marcarse la espera es benigno: cada una pide su
    recálculo, y el docstring del test lo dice.
  - Queda fuera el caso genérico de una respuesta perdida en la red con el guardado hecho.
- **Datos personales**: solo ids de línea y los textos del servidor (el 409 de F-043 y los motivos
  de F-004), los mismos que hoy van al `title`. El `alert` ya lo usa F-004 (`app.js` 1127, 1246).
- **Los tests de servidor demuestran R8 enmendado, no solo lo caracterizan.**
  - `r8_mismo_parte_con_cola_de_una_en_una`, con 3 líneas y cola: la 1.ª se convierte; cada una
    de las demás da 409 con `MOTIVO_RECALCULANDO`, sin tocar la fila ni el deshacer; queda un solo
    `registro_clase` y un solo recálculo.
  - `r8_partes_distintos_del_mismo_dia_con_cola`: se convierten las dos, con dos `registro_clase`
    y dos recálculos (`p-1`, `p-2`).
  - Que no haya RED de servidor está justificado: D16 acepta el comportamiento que había. El RED
    de JS es real: 3 failed porque no existía el `alert`.
- Tests node `r13_d16_*` (4): fallo parcial, motivos distintos, todas fallan y una sola.
- **F-047 R23**: el test cuenta las funciones con nombre de `app.js`. El implementer lo puso en
  verde haciendo local el ayudante (`var … = function`), sin tocar F-047 y diciéndolo en el
  comentario. No relaja ningún test: las huellas y el recuento de F-043 siguen intactos. El hueco
  que deja va en Automejora.

**Estado y notas del líder**: 4a08747 (`in_progress` → `in_review`). D14 queda anotada en la
entrada de F-081 de `features.json` (`pendiente`): con eso queda atendida la observación de la
pasada 1.

## Checkpoints (pasada 1 + 2)
- C1 [x] (arriba).
- C2 [x]: una sola activa (F-085, `in_review`), en su rama, y `current.md` de esta sesión.
- C3 [x]:
  - hexagonal: `conversion_clase.py` y `racha_ciz.decidir_inicio` son puros;
  - ruta en la primera línea; sin `print` ni secretos; trabajador por id de recurso;
  - R1 cumplido desde a37ef7f;
  - LÍMITE DE SERVICIO: `es_codigo_ci` (sv5, incluye `CIZ`) y `es_codigo_incidencia` (sv4, lo
    excluye) tienen semántica distinta y no son gemelas; la lista cerrada no cambia.
- C3 bis / C3 ter / C4 ter: N/A. No entra ningún documento de fuera, no se registra ninguna
  conversación nueva (las citas van con fecha) y no hay `rutas_sensibles.json`.
- C3 quater [x]: `azure-apps` `761c28e` y `60d7f70`, solo `partes.md`, en commits aparte y fieles a
  design §9. D16 no hace falta en `partes.md`, que no describe la selección múltiple.
  **Abierta para el líder**: `origin/main` ya está en `60d7f70` (push del 2026-11-27 a las 18:21)
  y el humano aún no ha confirmado que lo hizo él.
- C4 [x]:
  - cada R tiene su test (tabla) y todos pasan; sin red;
  - en `current.md`, M1 (con el paso D16), M2, M3 y M5 con su comando; M0 hecha; M4 fuera (D15);
  - dobles cruzados a mano: `SigridConCi` tiene la firma de `_post_sql_read` del cliente real.
- C4 bis:
  - [x] fase RED con salida real (pasada 1 y ciclo 1) y cobertura del 100 %;
  - [x] RM7 adelantado en la pasada 1, en copias del scratchpad: bajar la guarda R19 por debajo de
    los mensuales ⇒ rojo; llevar el 400 de R5/R6 detrás de la escritura ⇒ rojo. El delta no toca
    esas puertas;
  - mutación, RM1–RM6 y supervivientes: pendiente: pasada de evidencias.
- C5 [x]:
  - T1–T8, T10–T13 y T18 `[x]`, con su commit `F-085 Tn:` más los del ciclo 1;
  - N/A justificado: T9 y T14 son la campaña del líder, después de este APPROVED; T15–T17 son
    MANUAL del humano;
  - árbol limpio; `features.json` = `in_review`.

## Pasada 1, resumida (sigue válida)
- R27 [x]: apagado, sv5 lee y escribe como en `dev`, y sv4 también (`clave=None`). `inicio_movido`
  solo aparece con un `movida_de` que no sea CIZ, y eso solo lo produce sv5 con `MOVER_INICIO`.
  Ninguna sentencia nueva es `DELETE`.
- Tests ajenos enmendados, todos justificados:
  - `f066_r14`: revocado, ahora afirma R4;
  - `f066_r18`: por R4;
  - `f017`: +1 `_actor` (R11);
  - `f043`: +1 recarga (R13);
  - `f037 r9`: +1 clave (R17).
- Desviaciones 1, 2, 3 y 5 aceptables; la 4 queda resuelta con D16.

## Cobertura requisito → test (todos en verde)
| R | Test(s) |
|---|---|
| R1 | `r1_es_codigo_incidencia`, `r1_es_codigo_fin`, `r1_constantes`, `r1_nadie_mas_decide_es_ci` |
| R2–R7 | `r2..r7_puro_*`, `r2..r4_repo_*`, `r5_r6_repo_error_no_toca`, `r5_r6_endpoint_400_sin_tocar`, `r7_repo_caracterizacion` |
| R8 | `r8_guardas`, `r8_sin_sigrid_503`, `r8_recalculando_409`, `r8_varias_lineas_*`, `r8_mismo_parte_con_cola_de_una_en_una`, `r8_partes_distintos_del_mismo_dia_con_cola` |
| R9–R11 | `r9_*` (3), `r10_*` (4), `r10_r11_deshacer_por_el_endpoint`, `r11_*` (4) |
| R12, R15–R18 | sv3 `r12_*` (3), `r15_*` (4), `r16_*` (2), `r17_fetch_*`, `r18_*` (2) |
| R13–R14 | `r13_js_*` (3), `r13_d16_*` (4), `r14_convertida_*`, `r14_plantillas_*` |
| R19–R20 | sv5 `r19_*` (10), `r20_*` (2) |
| R21–R27, R30–R32 | sv5 `puro_r21..r27_*`, `pipeline_r21..r32_*` (R24 en `pipeline_r30a`) |
| R28–R29 | sv4 `r28_*` (4), `r29_*` (5), `settings_mover_inicio_*`, `app_pasa_mover_inicio` |
| R33 / R34 | raíz `test_f085_documentacion.py` (4) / MANUAL: M1, M2, M3 y M5 pendientes |

## Observaciones (no bloquean)
- Push de `azure-apps`: falta que el humano confirme que fue él (líder).
- El aviso D16 nombra las líneas por id. Si la tabla no enseña el id, se reconocen tras la recarga
  (se ve cuál cambió). A mirar en M1.
- D8: el alta manual y el clon de celda también ponen `manual`, y la reasignación de recurso no lo
  borra; sv3 ya no les impone el código del recurso nuevo. Lo decidió el humano; a mirar en M1.

**Automejora (propuesta, no aplicada)**:
- En `CHECKPOINTS.md` C4: «un requisito de selección múltiple cuyo único test corre con la cola
  apagada no está demostrado en producción».
- Que `test_f047_r23` cuente también las funciones asignadas a una variable (`var x = function`),
  para que no se escape una nueva solo con cambiar la sintaxis.
