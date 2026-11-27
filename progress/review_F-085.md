<!-- progress/review_F-085.md -->
Revisión completa (pasada 1, principal) · `git diff dev...HEAD` (merge-base b5e935b) · HEAD 33663c4

# F-085 · Review (pasada principal)

**Veredicto: CHANGES_REQUESTED** (2 cambios). SHA revisado `33663c4`, sin aprobar; la pasada 2 va desde él.

**Nivel de rigor: `critico`** (declarado en `features.json`). Exige fase RED, cobertura ≥ 90 % de
lo cambiado, mutación con 0 supervivientes sin justificar y RM1–RM7. Mutación (T9, T14), RM1–RM6
y la capa e2e quedan **«pendiente: pasada de evidencias»**. El diff no toca
`harness/rigor.local.json`.

## C1 — Arnés en verde
- [x] `ARNES_SIN_CACHE=1 bash harness/init.sh` ⇒ **exit 0 a la primera, sin flakies**, con el venv
  del proyecto (`VIRTUAL_ENV`: la copia no tiene `.venv`). Raíz `2553 passed, 50 skipped`
  (1357 s); sv1 74, sv2 579, sv3 2989, sv4 4254, sv5 1988, todos en verde y sin caché.
  `PUERTA COBERTURA: 100.0% (219/219)`, `PUERTA TAMAÑO` dentro, `CAPA E2E: N/A (ningún servicio
  declara el bloque e2e)`, `ENTORNO LISTO`. Avisos: deuda previa de ruff; `coverage.json` no escrito.

## C2 — Estado coherente
- [x] Una sola activa (F-085, `in_review`), en su rama, con `current.md` de esta sesión, cogida
  por prioridad (la comprometió el humano). No se toca ninguna `done`.

## C3 — Arquitectura y convenciones
- [x] Hexagonal: `conversion_clase.py` y `racha_ciz.decidir_inicio` son puros, en `application/`.
  La E/S queda en el repositorio y el pipeline.
- [x] Primera línea con la ruta en todos los ficheros nuevos. Sin `print` ni secretos (el
  `console.log` es del arnés node del test de R13). El trabajador se cita por id de recurso.
- [ ] **Reglas de dominio / R1**: `parte_repository.py:2550` (`_fin_movido`) decide «¿es el fin?»
  con `if cod and cod != "CIZ":`, fuera de `clase_hora.py`. R1: «ningún otro fichero de sv4
  decide es CI*». El test de fuente `test_f085_r1_nadie_mas_decide_es_ci` prohíbe `== "CIZ"` pero
  no `!= "CIZ"`, y por eso pasa en verde con la violación. → Cambio 1.
- [x] LÍMITE DE SERVICIO: no hay copia nueva entre servicios. `es_codigo_ci` (sv5, incluye `CIZ`
  porque es la guarda) y `es_codigo_incidencia` (sv4, lo excluye porque no se elige) tienen
  semántica distinta y sustituyen cada una la regla de prefijo que ya tenía su servicio. La lista
  cerrada de `CLAUDE.md` no cambia; `congelacion.py`, `orm_models.py` y `pareja_extra.py` siguen
  intactos.

## C3 bis / C3 ter / C4 ter
- N/A: no entra ningún documento de fuera ni se registra ninguna conversación nueva (la cita del
  humano va con su fecha), y no hay `harness/rutas_sensibles.json`.

## C3 quater — Ecosistema
- [x] `azure-apps`: `761c28e` (A) y `60d7f70` (B). Solo tocan `partes.md`, en commits aparte, con
  los SHA en `impl_F-085.md`, y cuadran con design §9. **Ojo**: `origin/main` ya está en
  `60d7f70`. El reflog dice «update by push» el 2026-11-27 a las 18:21, después de los commits
  (16:54) y del informe («sin push»), y no consta quién lo subió. El líder lo confirma con el
  humano: si fue un agente, se ha roto la regla dura.

## C4 — Verificación real
- [x] Cada R tiene su test `test_f085_rN_*` y todos pasan (tabla abajo). Sin red: SQLite en
  memoria, `SigridFake` y el cliente real con `_post_sql_read` sustituido.
- [x] M1, M2, M3 y M5 en `current.md` con su comando exacto. M0 hecha (`manual_F-085.md`), M4 fuera
  (D15).
- [x] Dobles: `SigridConCi` hereda de `SigridLookupFalso` (que hereda del cliente real) y su
  `_post_sql_read` tiene la firma del original (`sigrid_lookup_client.py:562`). Cruzado a mano:
  el repositorio no tiene comprobación automática.
- [ ] **R8 «con selección múltiple, cada línea según R2–R7»** no se cumple con la cola de
  producción cuando las líneas son del mismo parte (desviación 4) → Cambio 2.

## C4 bis — Rigor
- [x] `rigor: critico`. Fase RED con la salida real: el ImportError de T1, T10 y T12, y los
  recuentos con su `AssertionError` de T1/T3, T6, T7, T10 y T12. Cobertura 100 % (umbral 90 %).
- Mutación, RM1–RM6 y supervivientes: **pendiente: pasada de evidencias** (T9, T14).
- [x] RM7 adelantado, sobre copias del scratchpad y nunca en el árbol:
  - sv5: bajar la guarda R19 por debajo de `_decidir_mensual` ⇒ FALLA
    `test_f085_r19_antes_que_los_mensuales` (sin mutar, 45 passed).
  - sv4: poner el 400 de R5/R6 detrás de `repository.set_registro_hora` ⇒ FALLAN los 2
    `r5_r6_endpoint_400_sin_tocar`.
  - El orden de la parte B (una sola lectura; mover en vez de `INSERT`) lo vigilan R21 y R30a.
- [x] «Evidencias» completas (la mutación «sin medir», le toca a la campaña; capa e2e N/A).

## C5 — Cierre
- [x] T1–T8, T10–T13 y T18 en `[x]`, con un commit `F-085 Tn:` cada una. N/A justificado: T9 y T14
  son la campaña del líder, después del APPROVED; T15–T17 son MANUAL del humano. Árbol limpio;
  `features.json` = `in_review`.

## Lo que pidió el líder
- **R27 (apagado = `dev`)**: [x].
  - sv5: `previos` vacío ⇒ `pedidas`, la condición de salida, `hmoides` y el log del CIZ son los
    de antes. `test_f085_pipeline_r27_apagado_como_la_base` compara sentencias y lecturas, y los
    tests de F-083 no se han tocado.
  - sv4: `clave=None` ⇒ `aviso_desordenada` hace lo de antes. `_fin_movido` escoge
    `inicio_movido` solo si llega un `movida_de` con código distinto de CIZ, cosa que solo produce
    sv5 con `MOVER_INICIO`. Ninguna sentencia nueva es `DELETE`.
- **Tests enmendados**: justificados por la spec y sin relajar nada.
  - `f066_r14`: R14 revocado; ahora afirma R4.
  - `f066_r18`: su tercera fila es una incidencia, y con R4 pasa a `extra` por el código 7.
  - `f017` +1 `_actor(request)` (R11); `f043` +1 recarga (R13); `f037 r9` +1 clave (R17).
- **Desviaciones**: la 1 (la clase se decide dentro de la transacción), la 2, la 3 (`extra_auto=False`;
  deshacer lo restaura) y la 5 son aceptables. La 4 no lo es sin decisión del humano (Cambio 2).

## Cobertura requisito → test (todos en verde)
| R | Test(s) |
|---|---|
| R1 | `r1_es_codigo_incidencia`, `r1_es_codigo_fin`, `r1_constantes`, `r1_nadie_mas_decide_es_ci` (incompleto: Cambio 1) |
| R2–R7 | `r2..r7_puro_*`, `r2..r4_repo_*`, `r5_r6_repo_error_no_toca`, `r5_r6_endpoint_400_sin_tocar`, `r7_repo_caracterizacion` |
| R8 | `r8_guardas`, `r8_sin_sigrid_503`, `r8_recalculando_409`, `r8_varias_lineas_*` (sin cola), `r8_mismo_parte_con_cola_*` |
| R9–R11 | `r9_*` (3), `r10_*` (4), `r10_r11_deshacer_por_el_endpoint`, `r11_*` (4) |
| R12, R15–R18 | sv3 `r12_*` (3), `r15_*` (4), `r16_*` (2), `r17_fetch_*`, `r18_*` (2) |
| R13–R14 | `r13_js_*` (3), `r14_convertida_*`, `r14_plantillas_*` |
| R19–R20 | sv5 `r19_*` (10), `r20_*` (2) |
| R21–R27, R30–R32 | sv5 `puro_r21..r27_*`, `pipeline_r21..r32_*` (R24 en `pipeline_r30a`, línea 258) |
| R28–R29 | sv4 `r28_*` (4), `r29_*` (5), `settings_mover_inicio_*`, `app_pasa_mover_inicio` |
| R33 / R34 | raíz `test_f085_documentacion.py` (4) / MANUAL: M1, M2, M3 y M5 pendientes |

## Cambios requeridos
1. **R1, `services/partes-front/infrastructure/database/parte_repository.py:2550`**: cambiar
   `cod and cod != "CIZ"` por `cod and not es_codigo_fin(cod)` (de `clase_hora.py`). Ampliar
   `prohibido` en `tests/test_f085_conversion.py:118` con `'!= "CIZ"'` y `"!= 'CIZ'"`. El
   comportamiento no cambia y deben seguir en verde `r28_*`.
2. **R8 y design §2 frente a la desviación 4**: con la cola configurada, elegir un CI* para N
   líneas seleccionadas de un mismo parte convierte una sola. Las demás dan 409 (F-043 R38), porque
   la primera ha dejado el parte en espera. Además:
   - es **no determinista**: `Promise.all` lanza los PATCH a la vez y alguno puede pasar la guarda
     antes de que se marque el recálculo;
   - en el fallo parcial, `onChange` (el `.catch` de `app.js`) **no recarga** aunque una línea ya
     haya cambiado de clase, y la pantalla se queda desfasada (R13).

   Es un caso real: una huelga (CIH, `dia_completo`) afecta a toda una cuadrilla del mismo parte.
   Design §2 daba por hecho que todos los PATCH se guardaban y que F-049 agrupaba los pedidos, y el
   único test de selección múltiple que sale bien corre `sin_cola=True`. Por CLAUDE.md («la
   propuesta era incompleta ⇒ para y vuelve a proponer»), el líder lo lleva al humano y se hace
   UNA de estas dos:
   - (a) la selección como una sola petición y una sola transacción, con un único recálculo
     compartido (como `/api/empleado/reasignar` con `registro_ids`), con su test con cola;
   - (b) el OK literal del humano a la limitación en `progress/`, con R8 y design §2 enmendados.

   En los dos casos, `onChange` tiene que recargar o decir qué líneas fallaron cuando hay un fallo
   parcial, con su test node.

## Observaciones (no bloquean)
- **D14 (enmendar F-081 R3)** no consta en ningún sitio que sobreviva. La spec de F-081 vive solo
  en su rama (`db01b37`) y su entrada en `features.json` dice «sin spec». Conviene anotarla allí.
- **D8**: `manual` también lo ponen el alta manual (`parte_repository.py:2083`) y el clon de celda
  (F-049), y la reasignación de recurso (F-035) no lo borra. sv3 ya no le impone el código del
  recurso nuevo. Lo decidió el humano en (a); vale la pena verlo en M1.

**Automejora (propuesta, no aplicada)**: en `CHECKPOINTS.md` C4, «un requisito de selección
múltiple cuyo único test corre con la cola apagada no está demostrado en producción».
