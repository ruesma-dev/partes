<!-- progress/explore_F-047_revalidacion.md -->
# F-047 · Revalidación de la spec contra el código actual (2026-10-30)

Spec-author, en `partes-wt-f047` (rama `feature/F-047-parte-nuevo-en-espera`,
`dev` 75816f2 fusionado en 795a546). Spec aprobada el 2026-10-14 (DA1–DA10);
desde entonces entraron en `dev` F-046, F-048…F-054, F-056, F-058…F-064.
Resultado: **13 cambios mecánicos** y **3 decisiones abiertas nuevas
(DA11–DA13)**. Sin código tocado. Topes: requirements 150/150, design 250/250
(`python -m harness.tamano --feature F-047` en verde).

## 1. Causa y cifra (punto 3 del encargo)

- **La causa sigue cierta.** `PersistPartePipeline.run`
  (`services/partes-persistencia/application/pipelines/persist_parte_pipeline.py`)
  llama a `save_parte` (que hace `session.add` + `commit` y registra
  `[parte-repo] guardado`) y **después** a `_conciliar_partidas_safely()` y
  `_conciliar_recursos_safely()`. Las dos siguen siendo *best-effort*
  (WARNING y se consume el mensaje); el dedup por sha256 sigue saliendo antes
  de guardar sin conciliar.
- **F-048 agrava el síntoma, no lo cambia:** la ingesta suma la extra leída a
  la ordinaria de su fila y el reparto la vuelve a partir; hasta que concilia,
  el portal enseña 10 donde irá 8+2 (el ejemplo de la spec es exacto).
- **La cifra de 20–40 s no se ha vuelto a medir** (sin acceso a Log Analytics
  en esta sesión). Factor nuevo: desde F-046 (commit del 2026-10-14, el mismo
  día que la spec, en otra rama) `RecursoConciliador.conciliar_todos` corre
  bajo `candado_pasada` (`pg_try_advisory_lock`, backoff hasta
  `CANDADO_CONCILIAR_ESPERA_S` = 300 s; sin candado, `TimeoutError`). Con otra
  pasada en curso (otra réplica, un recálculo de F-042/F-043 o un pedido
  compartido de F-049) la espera puede pasar de 1 min ⇒ **DA13**. M3 (T13)
  queda como la nueva medición: la diferencia entre `[parte-repo] guardado` y
  `parte nuevo repartido … marcado=True`.

## 2. Referencias comprobadas que siguen igual

sv3: puerto `save_parte` (mismos kwargs), `save_parte` con `now_iso`,
`_deactivate_same_day_obra`, `get_by_sha256` (solo activos: un parte retirado
por F-061 deja reingerir y el nuevo llevará su pedido), `build_app` crea el
pipeline antes de `app.state.recalculo_seguimiento`, `SqlAlchemyRecalculoSeguimiento`
(`pedido_actual`, `marcar_terminado(document_id, peticion_id) -> bool`),
`despacho.py`, `main_worker.py`, `PersistParteResult`, fixture `fabrica` y
`test_f043_r33_build_app_expone_el_seguimiento`.
sv4: `seguimiento_recalculo.py` (estados, `ESPERA_MAX_S`, `MOTIVO_RECALCULANDO`,
`RecalculandoError`), `_exigir_sin_recalculo`, `estados_recalculo`,
`documentos_en_espera`, `_ahora_utc`, `lineas_para_registro`,
`_motivo_sin_lineas`, `unapprove_document`, `_set_approval`, las cuatro vistas,
las cuatro plantillas (`data-recalculando`, `recalculando-marca`,
`data-parte-contenido` ×2, `.action-bar`), y en `app.js` las 16 funciones que
nombra design §5 con sus firmas de F-043, las cinco `var` de la línea fija y
los extractores `F043_ESPERA` / `ESPERA`. Raíz: `test_f010_orm_models_gemelos`,
`test_f043_contrato_seguimiento`, `test_documentos_del_arnes`; las dos copias
de `orm_models.py` siguen byte-idénticas y el bloque «Seguimiento del
recalculo (F-043)» existe. Anclas de T10/T11 (`ARCHITECTURE.md` semánticas 3,
7 y 10; `partes-proyecto.md` §5.1 y «El parte en espera»; `azure-apps/partes.md`
nota de F-043 y fila de columnas) existen. `harness.mutacion` acepta
`--feature --workers --timeout`.

## 3. Cambios mecánicos aplicados (13)

1. design §3 `recalculo_seguimiento.py`: desde F-049 (R41) `marcar_terminado`
   filtra **por pedido**, no por documento; con pedido = id solo toca ese
   parte, así que R7 vale igual. Su docstring ya nombra F-047 (lo escribió
   F-049): solo cambia el del módulo.
2. design §3 pipeline: la `TimeoutError` del candado de F-046 es una excepción
   más de `conciliar_todos` ⇒ cae en R5 (sin marca, WARNING, sin propagar).
3. design §4 `approve_document`: ya carga el documento para la guarda de
   reparto de F-046 (`RepartoPendienteError`); la de espera va en ese mismo
   bloque, **detrás** (la regla de F-043: la guarda de espera va detrás de la
   de congelación; `RepartoPendienteError` es `CongeladoError`).
4. design §4 ruta `approve_document`: ya tiene `except RepartoPendienteError`;
   pasa a `except CongeladoError` (cubre las dos).
5. design §4 `lineas_para_registro`: hoy el orden es `dedicacion` →
   `reparto_pendiente` (F-046) → incompatibilidad; la exclusión nueva va
   después de `reparto_pendiente` y antes de la incompatibilidad (cumple lo
   aprobado: «después de `dedicacion` y antes de la incompatibilidad»).
6. design §4 vistas: `recalculando` se calcula dentro del dict de contexto;
   hay que sacarlo a una variable para pasárselo a `motivos_espera`.
7. design §4 y DA8: `test_f017_punto_unico` exige **20** `_actor(request)`
   (no 17); F-047 no añade ninguno.
8. design §5: F-064 fija con huella sha256 `restaurarVista`, `actualizarVista`
   (y `VISTA_CLAVE`); F-047 ya no los tocaba. T8 corre `test_f064_filtros_js.py`.
9. design §6: `FabricaSesionSqlite` y `sembrar_parte` viven en
   `services/partes-front/tests/dobles.py`.
10. design §9 R-e: F-044/F-045/F-046 ya están en `dev`; el riesgo de merge es
    F-057 (`spec_ready`, toca el pedido del editor de celda).
11. design §10 → T13: M1–M3 pasan enteros a T13 (con el SQL de M2 y la
    medición de M3) para dejar sitio a DA11–DA13 sin pasar el tope.
12. tasks T3, T4, T6, T7, T8: se añaden a la verificación los tests existentes
    que hoy tocan el mismo código (sv3: `test_f048_conciliar`,
    `test_f051_lectura_dudosa`, `test_f054_revision_cabecera`,
    `test_f049_pedido_compartido`; sv4: `test_f046_aprobar_documento`,
    `test_f046_aplicar`, `test_f025_aprobacion`, `test_f024_borrado_sigrid`,
    `test_f060_aprobacion_racha`, `test_f062_inicio_con_ciz`,
    `test_f004_endpoints_congelados`, `test_f061_portal`,
    `test_f064_clave_usuario`, `test_f050_vistas`, `test_f064_filtros_js`,
    `test_f049_editor_js`).
13. tasks T13: `redeploy_partes.ps1` fija el orden sv2 → sv3 → sv5 → sv4 → sv1
    aunque se pasen juntos; para sv4 → sv3 hacen falta **dos llamadas**.

Además: requirements.md anota la revalidación en el Contexto y en la cabecera;
tasks.md gana el apartado «Revalidación 2026-10-30» y el «Visto bueno previo»
pide ahora DA11–DA13.

## 4. Decisiones abiertas nuevas (design §11)

- **DA11 · Matriz «Horas por día» de la obra (F-049).** La matriz no marca la
  espera (tampoco en F-043): la celda de un parte nuevo enseña las horas sin
  repartir (es justo donde se ve «10» en vez de «8+2») y el doble clic abre el
  editor; guardar da 409 (`guardar_celda` llama a `_exigir_sin_recalculo`,
  F-049 R15, con el texto de F-043). **A (recomendada)**: fuera de F-047, como
  las vistas agregadas (DA7): no hay daño y la fila de la tabla de abajo sí se
  marca. B: `data-recalculando` en la celda y el editor no se abre; toca
  `obra_detail.html` y el JS del editor de F-049, con riesgo de romper
  `test_f049_editor_js.py` (DA8). Si se quiere B, mejor feature aparte.
- **DA12 · Parte nuevo sin obra o sin fecha (F-054).** Va a revisión y, con
  F-047, también esperaría. Sin fecha no hay día que repartir (el aviso
  «se están repartiendo sus horas» no es exacto, aunque la pasada sí resuelve
  el recurso). Durante la espera la fecha se puede cambiar (F-043) pero la obra
  da 409. **A (recomendada)**: la misma regla para todos (la espera es corta y
  hay una condición menos que probar). B: no escribir el pedido si
  `motivos_cabecera(parte)` no está vacía (R1/R2 ganan esa condición y sus
  tests; el parte se corrige al momento).
- **DA13 · Candado de F-046 y el texto de R19.** Ver §1. El comportamiento ya
  queda cubierto por R5 (timeout ⇒ sin marca ⇒ vence a los 600 s; 300 s de
  candado caben dentro). Lo que cambia es la promesa del aviso. **A
  (recomendada)**: R19 dice «(suele tardar menos de 1 min; con más partes en
  cola, unos minutos)». B: R19 tal cual (DA6 ya dice que el humano puede
  reescribir los textos).

## 5. Comprobado sin conflicto (no necesita decisión)

- **F-050 «misma fila»**: la espera es por documento (`tr[data-document-id]`);
  agrupar filas por la clave de F-050 no cambia qué contenedores se marcan.
- **F-061 parte retirado / vacío**: `motivos_espera(None)` filtra `is_active`;
  un retirado no sale. Borrar la última línea de un parte en espera ya da 409
  (F-043). Un parte ingerido sin líneas esperaría unos segundos: inocuo.
- **F-056 franquicia en el modal**: el preflight evalúa `preparado.grupos`,
  que salen de `lineas_para_registro` **después** de las exclusiones; la
  exclusión de R17 deja fuera las líneas en espera también para las extras
  pendientes de la franquicia. La propuesta (`lineas_trabajador_periodo`) lee
  de la base, incluidas líneas en espera, pero es consultiva.
- **F-046 aplicar reparto**: `iniciar_aplicacion` ya llama a
  `documentos_en_espera` y rechaza si algún parte del día espera: cubre al
  parte nuevo sin tocar nada.
- **F-049 pedido compartido sobre un parte nuevo**: si una celda de otra obra
  le escribe su uuid4 mientras la ingesta concilia, el motivo pasa a
  `recalculo` en el servidor; la ingesta no marca y marca la pasada de F-049
  (R7). La página ya cargada conserva el texto «nuevo» (memoria del JS).
- **Riesgo heredado de F-043 (sin cambio)**: si Sigrid falla para una obra,
  `_pasada` hace `continue` sin excepción; la pasada «acaba bien» y el parte se
  marcaría «procesado» con esas líneas sin repartir. Igual que el recálculo de
  F-043 hoy; no es nuevo de F-047.

## 6. Ficheros tocados

- `specs/F-047-parte-nuevo-en-espera/requirements.md`, `design.md`, `tasks.md`.
- `progress/explore_F-047_revalidacion.md` (este) y `progress/current.md`.
