<!-- progress/review_F-042.md -->
Revisión completa (pasada 1) · `git diff dev...HEAD` con `dev` = `824d01c`, HEAD = `49efbca`

# F-042 · Revisión · recalcular el reparto normal/extra al cambiar la fecha

**Veredicto: APPROVED** (APROBADO).

**Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura de
lo cambiado ≥ 80 %, mutación completa con 0 supervivientes y verificaciones MANUAL con comando exacto.

## Lo que se ejecutó (resultados reales, 2026-10-09)

- `bash harness/init.sh` en el worktree: **ENTORNO LISTO**, exit 0. Raíz 472 passed, 3 skipped;
  `PUERTA COBERTURA: 100.0% de 105 líneas cambiadas (umbral 80%, nivel critico)`; `PUERTA TAMAÑO`
  dentro (design 250/250). Avisos previos: ruff (deuda), features blocked F-014/F-032, infra sin tests.
- Como init.sh tiró de caché para los servicios, reejecuté las suites enteras sin caché: sv3
  **1.147 passed**; sv4 **1.879 passed, 1 skipped** (305 s); sv2 8 passed. node v24.14.1 instalado, así que los tests
  de R11 corren de verdad (el skip de sv4 es `test_f017_punto_unico.py:235`, «sv4 no tiene capa domain», ajeno a F-042).

## Mutación (C4 bis)

- **Recálculo independiente** (`harness.alcance.alcance_de_feature` + `generar_mutantes`): 10
  ficheros, **333 líneas**, **13 mutantes**, coinciden fichero a fichero con el informe.
- **Campaña no reejecutada**: «Tiempo total» 1.674,7 s (> 60 s). Vale el recálculo puro + RM1–RM6
  + la reproducción manual de abajo.
- **Coste por mutante** = 1.674,7 × 6 ÷ 13 = **773 s** ≥ línea base sv4 (546–548 s): coherente.
- **RM1**: SHA medido `13ee0fc…`; de ahí a HEAD solo cambian `progress/impl_F-042.md`,
  `progress/mutacion_F-042.md` y `tasks.md` (`git diff --stat 13ee0fc..HEAD`). Alcance vigente.
- **RM2**: media 128,8 s × 6 workers = 773 s frente a base 548 s; 13 × 128,8 = 1.674 s. Sin saltos.
- **RM3**: repasé los 13; ninguno es equivalente (cada uno cambia una salida observable: estado
  `recalculo`, publicar o no, `ok`, clase del mensaje). Ningún equivalente sale muerto.
- **RM4 · reproducción manual** (copia `git archive HEAD` en mi scratchpad; `mutar.py` sustituye el
  texto exacto, ejecuta los tests del módulo y restaura). Base: sv3 38 passed, sv4 46 passed.

| # | Fichero:línea | Original → mutado | Tests | Resultado |
|---|---|---|---|---|
| 1 | sv3 `mensajes.py:46` (del informe) | `if tipo is None:` → `if tipo is not None:` | despacho | **21 failed** |
| 2 | sv4 `app.py:1484` (del informe) | `res.get("action") == "parte_fecha"` → `!=` | recalculo_fecha | **4 failed** |
| 3 | sv3 `despacho.py` (extra) | `res = …conciliar_todos()` → envuelto en `try/except: res=None` | despacho | 1 failed (R15) |
| 4 | sv3 `main_worker.py` (extra) | `recurso_conciliador=app.state.recurso_conciliador` → `=None` | despacho | 1 failed (R18) |
| 5 | sv3 `despacho.py` (extra) | `"document.pdf")` → `"documento.pdf")` (ingesta movida) | despacho | 1 failed (R13) |
| 6 | sv4 publisher (extra) | `_GRAVEDAD` con `SIN_COLA` antes que `FALLO` | recalculo_fecha | 1 failed |
| 7 | sv4 `app.py` undo (extra) | `motivo=MOTIVO_DESHACER_FECHA` → `MOTIVO_CAMBIO_FECHA` | recalculo_fecha | 2 failed |
| 8 | sv4 `app.py` (extra) | publicar ANTES de `update_parte_fecha` | recalculo_fecha | 10 failed |
| 9 | sv4 publisher (extra) | WARNING sin `type(exc).__name__` | recalculo_fecha | 2 failed |
| 10 | sv4 `app.js` (extra) | quitar `alert(estadoRecalculo("fallo")[0])` del deshacer | recalculo_fecha | 1 failed (node) |
| 11 | sv4 `app.js` (extra) | aviso de `fallo` con clase `saved` en vez de `error` | recalculo_fecha | 1 failed (node) |
| 12 | sv4 `parte_repository.py` (extra) | `undo_last` con `document_ids` vacío | recalculo_fecha | 4 failed |

- **Contrato de la raíz (R22) rompe de verdad si divergen** (mismas condiciones, `tests/test_f042_contrato_recalculo.py`):
  `TIPO_RECALCULAR = "recalculo"` en sv4 → 7 failed; clave `"tipo"`→`"kind"` en sv4 → 6 failed;
  sv3 discrimina por `payload.get("clase")` → 6 failed; sv2 emite `"tipo": "ingesta"` → 1 failed.
- **RM5**: N/A justificado: no hay supervivientes ni equivalentes declarados.
- **RM6**: N/A justificado: el diff no quita ninguna guarda; las `is None` nuevas siguen en su sitio.
- Informe sin «⚠ CAMPAÑA NO VÁLIDA», «Sin veredicto (base rota)» = 0, línea base corrida y declarada.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros del arnés presentes.
- **C2** [x] una sola `in_progress` (F-042) · [x] rama `feature/F-042-…` · [x] `current.md`
  coherente (sección F-042 arriba; lo demás son pendientes de despliegue de features anteriores, la
  convención del repo aceptada en F-040) · [x] las `done` tienen su resumen en `history.md` (sin cambios).
- **C3** [x] hexagonal: sv3 `workers/` en `interface_adapters`, publisher en `infrastructure` de sv4;
  `recurso_conciliador.py`, `pareja_extra.py`, `application/` y `orm_models.py` sin tocar ·
  [x] primera línea con ruta en todos los ficheros nuevos · [x] sin `print`, sin secretos, sin
  dependencias nuevas (los dos módulos del contrato solo stdlib, lo vigila un test) · [x] trampas:
  ni recurso/empleado, ni incidencias, ni esquema se tocan. **Límite de servicio**: sv4 solo pide;
  el reparto sigue en sv3 (`conciliar_todos` sin lógica nueva). **Lista cerrada**: el par
  `recalculo_publisher.py`/`mensajes.py` es contrato de transporte atado por test (DA6 aprobada).
- **C3 bis** (toca `docs/referencia/partes-proyecto.md`): [x] cabecera de origen y fecha ya presente ·
  [x] ningún PDF/ofimática añadido (`git log --diff-filter=A dev..HEAD` sin `.pdf/.docx/.xlsx/.pptx`) ·
  [x] barrido sobre las líneas añadidas con patrones de correo, IPv4, GUID, `key|token|secret|password|
  pwd|AccountKey|sig=` y base64 ≥ 32: **0 coincidencias** · [x] nada redactado (N/A el anotarlo).
- **C4** [x] R1–R22 con tests `test_f042_rN_*`, todos verdes (tabla abajo); R23 es documental ·
  [x] sin red ni BBDD real (SQLite en memoria y dobles) · [x] M1–M3 en `progress/current.md` con
  SQL, `redeploy_partes.ps1 -Solo sv3/-Solo sv4`, `az monitor log-analytics query` y
  `az storage message peek` copy-paste.
- **C4 bis** [x] rigor declarado · [x] fase RED con trazas reales de T1–T7 (T3 y T7 en copia aislada,
  como pide C4 bis para tests que nacen verdes) · [x] cobertura 100 % · [x] mutación verificada ·
  [x] muertos comprobados (12 a mano) · [x] coste por mutante coherente · [x] sin cabecera de campaña
  no válida · [x] RM1 · [x] RM2 · [x] RM5 N/A justificado · [x] RM6 N/A justificado · [x] campaña
  manual: N/A, la automática dio 13 · [x] 0 supervivientes · [x] «Evidencias» con los cuatro números
  y workers (6) · [x] ningún N/A sin motivo.
- **C4 ter** N/A: el repo no declara `harness/rutas_sensibles.json`.
- **C5** [x] T1–T13 `[x]` con commit `F-042 Tn:` cada una · [x] árbol limpio, sin temporales ·
  [x] `features.json` en `in_progress` (pasa a `done` tras este APPROVED, lo hace el líder).

**Tests existentes**: el único tocado es `test_f017_punto_unico.py` (15 → 17 `_actor(request)` y su
docstring), la opción A del humano. `git diff dev...HEAD --name-status` sobre todas las carpetas de
tests: el resto son `A` (nuevos). sv1, sv2, sv5, `infra/`, `CLAUDE.md` y `main.py` de sv4 sin cambios.

## Puntos pedidos, uno a uno

- **sv3 · ingesta intacta**: `_ingerir` es el cuerpo viejo de `main_worker.handler` línea a línea,
  con `CONTENEDOR_*` pasados como parámetros (mutante 5 lo vigila). Mensaje sin `tipo` o `tipo: null`
  ⇒ ingesta. `ColaCliente.consumir` (reintento, `max_dequeue`, poison) sin tocar.
- **sv3 · recálculo**: solo `conciliar_todos()`, sin `try/except` (DA3, mutante 3); sin Sigrid,
  WARNING y consumido (R17).
- **sv4 · fecha guardada aunque falle la cola**: `pedir_recalculo` nunca lanza y se llama tras el
  `commit` de `update_parte_fecha`; R2 lo prueba leyendo la fecha desde otra sesión al publicar.
- **sv4 · deshacer**: publica solo si `ok` y `action == "parte_fecha"` (R7/R8, mutante 2 y 12).
- **JS**: R11 ejecuta las funciones reales de `app.js` con node (DOM y `fetch` falsos) y `node --check`.
- **Sin nombres ni DNIs reales**: solo DNIs sintéticos `0000000xX`, actores `revisor@ejemplo`.
- **azure-apps**: `be02869` toca solo `partes.md`; contenido correcto y sin secretos.

## Cobertura requisito → test

| Req. | Test(s) |
|---|---|
| R1 | `test_f042_r1_guardar_la_fecha_pide_el_recalculo`, `…_mensaje_recalculo_es_el_del_contrato`, `…_la_hora_del_mensaje_va_en_utc` |
| R2 | `test_f042_r2_se_publica_despues_de_confirmar_la_fecha` |
| R3 | `test_f042_r3_si_la_cola_falla_la_fecha_queda_guardada`, `…_pedir_recalculo_nunca_lanza` |
| R4–R6 | `test_f042_r4_sin_cola_guarda_y_lo_dice`; `r5_fecha_invalida…`, `r5_parte_inexistente…`, `r5_parte_congelado_no_publica`; `r6_volver_a_guardar_la_misma_fecha_publica` |
| R7 | `test_f042_r7_deshacer_la_fecha_pide_el_recalculo`, `…_con_la_cola_caida_avisa`, `…_sin_cola`, `…_peor_estado` |
| R8 | `test_f042_r8_deshacer_otra_accion_no_publica`, `…_sin_nada_que_deshacer…`, `…_un_undo_fallido…` |
| R9–R10 | `test_f042_r9_undo_last_devuelve_la_accion_y_los_documentos` (+2); `r10_el_publisher_se_monta_sobre_cola_cliente` (+2) |
| R11 | `test_f042_r11_tras_guardar_pinta_el_estado…`, `…_tras_deshacer_con_fallo…`, `…_app_js_es_sintacticamente_valido` |
| R12–R17 | `test_f042_r12_*` (5), `r13_*` (4), `r14_*` (2), `r15_si_la_pasada_falla_el_handler_propaga`, `r16_desconocido_se_propaga_sin_tocar_nada`, `r17_sin_conciliador_avisa_y_da_el_mensaje_por_bueno` |
| R18 | `test_f042_r18_build_app_expone_el_conciliador` (+2, incluido `main_worker.main()` real) |
| R19 | `test_f042_r19_el_recalculo_deja_el_reparto_del_jueves` (oráculo: el mismo parte ingerido en jueves) |
| R20–R21 | `test_f042_r20_las_congeladas_no_cambian_y_cuentan` (×4 estados); `r21_dos_recalculos_dejan_lo_mismo_que_uno` |
| R22 | `tests/test_f042_contrato_recalculo.py` (11) |
| R23 | Documental: leídos `ARCHITECTURE.md`, `partes-proyecto.md` y `azure-apps/partes.md`; correctos |

## Observaciones (no bloquean)

1. `ColaCliente.enviar` de sv4 registra `peticion_id=None` con cada recálculo (pensado para
   `q-transfer`). Ruido de log; la traza útil la da el INFO `[recalculo] pedido …` del publisher.
2. El contrato de la raíz ata `tipo` y su valor, no los nombres `document_id`/`motivo`/
   `solicitado_por`, que sv3 solo lee para el log. Renombrarlos en sv4 no rompería ningún test, pero
   tampoco el comportamiento.
3. ruff marca 15 avisos de estilo en los ficheros nuevos (UP035, I001, RUF100, PLW1510, RUF012) y una
   línea de más de 79 en el docstring de `build_app`. Deuda menor, coherente con el aviso global.
4. El generador produce pocos mutantes (13 en 333 líneas) en un rigor crítico; los 12 manuales de
   arriba cubren los huecos importantes. Propuesta para el arnés (no aplicada): que
   `harness/mutacion.py` mute también constantes de cadena de módulo y el orden de tuplas.

## Cambios requeridos

Ninguno.
