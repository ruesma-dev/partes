<!-- progress/review_F-085.md -->
Revisión completa (pasada 1, principal) · `git diff dev...HEAD` (merge-base b5e935b) · HEAD 33663c4

# F-085 · Review (pasada principal)

**Veredicto: CHANGES_REQUESTED** (2 cambios; el resto en verde). SHA revisado: `33663c4`; no hay
SHA aprobado todavía. La pasada 2 será incremental desde 33663c4.

**Nivel de rigor: `critico`** (declarado en `features.json`). Exige fase RED, cobertura ≥ 90 % de
lo cambiado, mutación con 0 supervivientes sin justificar y RM1–RM7. Mutación (T9, T14), RM1–RM6
y la capa e2e quedan **«pendiente: pasada de evidencias»**. El diff no toca
`harness/rigor.local.json`.

## C1 — Arnés en verde
- [x] `ARNES_SIN_CACHE=1 bash harness/init.sh` ⇒ **exit 0 a la primera, sin flakies**, con el venv del
  proyecto (`VIRTUAL_ENV`, porque la copia no tiene `.venv`). Raíz `2553 passed, 50 skipped`
  (1357 s); sv1 74, sv2 579, sv3 2989, sv4 4254, sv5 1988, todos en verde y sin caché.
  `PUERTA COBERTURA: 100.0% (219/219)`, `PUERTA TAMAÑO` dentro, `CAPA E2E: N/A (ningún servicio
  declara el bloque e2e)`, `ENTORNO LISTO`. Avisos: deuda previa de ruff y `coverage.json` no escrito.
- [x] Están los ficheros del arnés.

## C2 — Estado coherente
- [x] Una sola feature activa (F-085, `in_review`). Rama `feature/F-085-…`. `current.md` es de esta
  sesión. Prioridad: F-085 venía comprometida por el humano.
- [x] Las `done` tienen su resumen en history: no se ha tocado.

## C3 — Arquitectura y convenciones
- [x] Hexagonal: `conversion_clase.py` y `racha_ciz.decidir_inicio` son puros, en `application/`. La
  E/S está en el repositorio y el pipeline. Sin imports de infraestructura en el dominio.
- [x] Primera línea con la ruta en todos los ficheros nuevos. Sin `print`, sin secretos. El
  `console.log` está en el arnés node del test de R13. El trabajador se cita por id de recurso.
- [ ] **Reglas de dominio / R1**: `parte_repository.py:2550` decide «¿es el fin?» con
  `if cod and cod != "CIZ":` (`_fin_movido`), fuera de `clase_hora.py`. R1: «ningún otro fichero
  de sv4 decide es CI*». El test de fuente `test_f085_r1_nadie_mas_decide_es_ci` prohíbe
  `== "CIZ"` pero no `!= "CIZ"`, y por eso pasa en verde con la violación. → Cambio 1.
- [x] LÍMITE DE SERVICIO: no hay copia nueva entre servicios. `es_codigo_ci` (sv5, incluye `CIZ`:
  es la guarda) y `es_codigo_incidencia` (sv4, lo excluye: no se elige) tienen semántica distinta.
  Cada una sustituye la regla de prefijo que ya tenía su servicio (`HoraRecurso.es_incidencia`).
  No hace falta tocar la lista cerrada de `CLAUDE.md`. `congelacion.py`, `orm_models.py` y
  `pareja_extra.py` siguen intactos.

## C3 bis / C3 ter
- N/A: no entra ningún documento de fuera ni se registra ninguna conversación nueva. La cita
  literal del humano va con su fecha (2026-11-27).

## C3 quater — Ecosistema
- [x] `azure-apps`: `761c28e` (A) y `60d7f70` (B). Solo tocan `partes.md`, en commits aparte, con
  los SHA en `impl_F-085.md`. Su contenido cuadra con la «Frontera» de design §9. **Ojo**:
  `origin/main` ya está en `60d7f70`; el reflog dice «update by push» el 2026-11-27 a las 18:21,
  después de los commits (16:54) y del informe («sin push»). No consta quién lo subió. El líder
  tiene que confirmar con el humano que fue él: si lo hizo un agente, se ha roto la regla dura.

## C4 — Verificación real
- [x] Cada requisito tiene su test `test_f085_rN_*` y todos pasan. Tabla abajo.
- [x] Los unit tests no tocan red: SQLite en memoria, `SigridFake` y el cliente real con
  `_post_sql_read` sustituido.
- [x] M1, M2, M3 y M5 están en `current.md` con su comando exacto. M0 está hecha
  (`manual_F-085.md`). M4 queda fuera por D15.
- [x] Dobles: `SigridConCi` hereda de `SigridLookupFalso` (que hereda del cliente real) y su
  `_post_sql_read` tiene la firma del original (`sigrid_lookup_client.py:562`). El repositorio no
  tiene comprobación automática de dobles; los he cruzado a mano.
- [ ] **R8 «con selección múltiple, cada línea según R2–R7»** no se cumple con la cola configurada
  (la de producción) cuando varias líneas son del mismo parte. Lo explica la desviación 4
  (→ Cambio 2).

## C4 bis — Rigor
- [x] `rigor: critico` declarado.
- [x] Fase RED con la salida real: el ImportError de T1, T10 y T12, y los recuentos de fallos con
  su `AssertionError` de T1/T3, T6, T7, T10 y T12.
- [x] Cobertura 100 % de lo cambiado (219/219, umbral 90 %).
- Mutación, RM1–RM6 y supervivientes: **pendiente: pasada de evidencias** (T9, T14).
- [x] RM7, adelantado en las dos puertas de orden que se pueden mover, sobre copias del scratchpad
  y nunca en el árbol:
  - (a) sv5: bajar la guarda R19 por debajo de `_decidir_mensual` ⇒
    `test_f085_r19_antes_que_los_mensuales` FALLA (1 failed, 44 passed; sin mutar, 45 passed).
  - (b) sv4: poner el 400 de R5/R6 detrás de `repository.set_registro_hora` ⇒ los 2
    `test_f085_r5_r6_endpoint_400_sin_tocar` FALLAN.
  - El orden de la parte B (una sola lectura y mover en vez del `INSERT`) lo vigilan R21 y R30a con
    el `SigridFake` espiado.
- [x] «Evidencias»: están las cifras, con la mutación «sin medir» (le toca a la campaña) y la fila
  de la capa e2e. Capa e2e N/A: ningún servicio declara el bloque, según `init.sh`.

## C4 ter
- N/A: no hay `harness/rutas_sensibles.json` y `init.sh` no ha señalado rutas sensibles.

## C5 — Cierre
- [x] T1–T8 y T10–T13 en `[x]`, con un commit `F-085 Tn:` cada una. T18 también en `[x]`.
- N/A (justificado): T9 y T14 son la campaña del líder, después de este APPROVED. T15–T17 son
  MANUAL del humano.
- [x] El árbol queda limpio (`git status` vacío). `features.json` = `in_review`.

## Lo que pidió el líder
- **R27 (apagado = `dev`)**: [x].
  - sv5 apagado: `previos` vacío ⇒ `pedidas` es la lista de antes. Siguen igual el
    `if not fines and not previos` y `hmoides`, y el log del CIZ (mismo texto).
    `test_f085_pipeline_r27_apagado_como_la_base` compara sentencias y lecturas con la base. Los
    tests de F-083 R13/R15 no se han tocado.
  - sv4 apagado: `clave=None` ⇒ `aviso_desordenada` hace lo de antes. `_fin_movido` no depende
    del interruptor, pero solo escoge `inicio_movido` si la escrita trae `movida_de` con un código
    distinto de CIZ, y eso solo pasa con `MOVER_INICIO` en sv5. Ninguna sentencia nueva es `DELETE`.
- **Tests enmendados**: los cinco están justificados y no relajan nada.
  - `f066_r14`: R14 revocado; ahora afirma la vuelta a horas por R4.
  - `f066_r18`: su tercera fila es una incidencia, y con R4 pasa a `extra` por el código 7 (HEOF).
  - `f017`: un `_actor(request)` más, el del recálculo de R11.
  - `f043`: una recarga más, la de R13.
  - `f037 r9`: una clave más, la de R17.
  - Las filas de `f066_r13`/`r17` con CI* no existían y no se han tocado, como decía design §6.
- **Desviaciones 1–3 y 5**: aceptables.
  - 1: decidir la clase dentro de la transacción quita una carrera.
  - 3: `extra_auto=False` evita que sv3 borre la línea convertida; deshacer lo restaura (test r2).
- **Desviación 4 (409 en varias líneas del mismo parte)**: NO es aceptable sin una decisión del
  humano (Cambio 2).

## Cobertura requisito → test (todos en verde)
| R | Test(s) |
|---|---|
| R1 | `r1_es_codigo_incidencia`, `r1_es_codigo_fin`, `r1_constantes`, `r1_nadie_mas_decide_es_ci` (incompleto: Cambio 1) |
| R2–R4 | `r2_puro_forma_canonica`, `r2_repo_*`, `r3_puro/repo_*`, `r4_puro/repo_vuelta_atras` |
| R5–R6 | `r5_puro_ciz_error`, `r6_puro_sin_letra_error`, `r5_r6_repo_error_no_toca`, `r5_r6_endpoint_400_sin_tocar` |
| R7 | `r7_puro_*`, `r7_repo_caracterizacion`, `r7_repo_sin_tabla_y_sin_ci_como_f066` |
| R8 | `r8_guardas`, `r8_sin_sigrid_503`, `r8_recalculando_409`, `r8_varias_lineas_*` (sin cola), `r8_mismo_parte_con_cola_espera_al_recalculo` |
| R9 | `r9_r11_convertir_responde_y_pide_recalculo`, `r9_sin_cambio_de_clase_*`, `r9_respuesta_sin_codigo_como_f066` |
| R10 | `r10_undo_fields_*`, `r10_repo_deshacer_registro_clase`, `r10_deshacer_*_otras_obras_del_dia`, `r10_r11_deshacer_por_el_endpoint` |
| R11 | `r11_cola_caida_el_cambio_queda`, `r11_sin_cola`, `r11_deshacer_registro_hora_no_pide`, `r11_constantes_de_motivo` |
| R12 | sv3 `r12_es_miembro_*`, `r12_la_extra_automatica_*_se_borra`, `r12_extra_explicita_o_congelada_se_queda` |
| R13 | `r13_js_recarga_con_clase_cambiada`, `r13_js_sin_cambio_*`, `r13_js_varias_con_alguna_cambiada` |
| R14 | `r14_convertida_se_pinta_y_viaja_como_incidencia`, `r14_plantillas_pintan_por_es_incidencia` |
| R15–R18 | sv3 `r15_*` (4), `r16_*` (2), `r17_fetch_trae_hora_match_method`, `r18_*` (2) |
| R19–R20 | sv5 `r19_*` (10), `r20_*` (2) |
| R21–R27 | sv5 `puro_r21..r27_*`, `pipeline_r21..r27_*` (R24 dentro de `pipeline_r30a`, línea 258) |
| R28–R29 | sv4 `r28_*` (4), `r29_*` (5), `settings_mover_inicio_*`, `app_pasa_mover_inicio` |
| R30–R32 | sv5 `pipeline_r30a`, `pipeline_r30b`, `pipeline_r31`, `pipeline_r32_*` (2) |
| R33 | raíz `tests/test_f085_documentacion.py` (4) |
| R34 | MANUAL (humano): M1, M2, M3 y M5 pendientes; M0 hecha; M4 fuera (D15) |

## Cambios requeridos
1. **R1, `services/partes-front/infrastructure/database/parte_repository.py:2550`**
   (`_fin_movido`): cambiar `cod and cod != "CIZ"` por `es_codigo_fin` de `clase_hora.py`, por
   ejemplo `cod and not es_codigo_fin(cod)`. Ampliar `prohibido` en
   `tests/test_f085_conversion.py:118` con `'!= "CIZ"'` y `"!= 'CIZ'"`, para que el test de fuente
   habría cazado este caso. El comportamiento no cambia y deben seguir en verde `r28_*`.
2. **R8 y design §2 frente a la desviación 4**: hoy, con la cola configurada, elegir un CI* para
   N líneas seleccionadas de un mismo parte convierte una sola. Las demás dan 409 (F-043 R38),
   porque la primera ha dejado el parte en espera. Además:
   - es **no determinista**: `Promise.all` lanza los PATCH a la vez y alguno puede pasar la guarda
     antes de que el primero marque el recálculo;
   - en ese fallo parcial, `app.js` (`onChange`, `.catch`) **no recarga** aunque una línea ya haya
     cambiado de clase, y la pantalla se queda desfasada (R13).

   Es un caso real: una huelga (H, CIH, `dia_completo`) afecta a toda una cuadrilla en el mismo
   parte. Design §2 daba por hecho que cada PATCH se guardaba y que F-049 agrupaba los pedidos. El
   único test de selección múltiple que sale bien corre `sin_cola=True`, una configuración que no
   es la de producción. Por CLAUDE.md («la propuesta era incompleta ⇒ para y vuelve a proponer»),
   el líder lo lleva al humano y se hace UNA de estas dos:
   - (a) convertir la selección en una sola petición y una sola transacción, con un único
     recálculo compartido, como `/api/empleado/reasignar` con `registro_ids`, más su test con cola;
   - (b) que el humano acepte la limitación, con su OK literal en `progress/` y R8/design §2
     enmendados.

   Con (a) o con (b), `onChange` tiene que recargar o avisar de qué líneas fallaron cuando hay un
   fallo parcial, con su test node.

## Observaciones (no bloquean)
- **D14 (enmendar F-081 R3)** no consta en ningún sitio que sobreviva. La spec de F-081 vive solo
  en su rama (`db01b37`), y su entrada en `features.json` dice «sin spec». Conviene anotar la
  enmienda en esa rama o en su entrada para que no se pierda.
- **D8**: `manual` también lo ponen el alta manual (`parte_repository.py:2083`) y el clon de celda
  (F-049), y la reasignación de recurso (F-035) no lo borra. Desde F-085, sv3 ya no le impone el
  código del recurso nuevo a una línea así. Es lo que decidió el humano en (a); vale la pena
  mirarlo en M1.
- `HoraRecurso.es_incidencia` ahora también quita los espacios de los lados. Solo cambia algo para
  un `cod` con espacios a la izquierda, y es inocuo.

## Automejora (propuesta, no aplicada)
- En `CHECKPOINTS.md` C4, añadir: «un requisito de selección múltiple o concurrencia que solo
  tenga un test con la cola, o el colaborador, apagado no está demostrado para la configuración
  de producción». En F-085 el único test verde de la selección múltiple era `sin_cola=True`.
