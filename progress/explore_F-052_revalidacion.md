# F-052 · Revalidación de la spec contra el código actual (2026-11-01)

Spec-author, en `partes-wt-f052` (rama `feature/F-052-sincronizar-con-sigrid`,
`dev` 69af0f5 fusionado en 0be3ef7). Spec escrita el 2026-10-20 y nunca
aprobada; desde entonces entraron en `dev`, entre otras, F-034, F-038, F-043,
F-046, F-047, F-049, F-050, F-053, F-054, F-055, F-056, F-060–F-062 y F-064.
Resultado: **16 cambios mecánicos** y **7 decisiones nuevas (DA11–DA17)**;
DA9 superada. **El 2026-11-02 el humano aprobó la spec** (§6 y §7). Sin código tocado. Sin lecturas de Sigrid ni de
producción (M1 sigue siendo del humano).

## 1. Lo que se ha contrastado y sigue igual

sv5 (`services/partes-transfer/`):
- `sigrid_write_client.py`: `_read` (truncated ⇒ `RuntimeError`, base de
  `SIGRID_API_DATABASE`, por defecto `ruesma`), `synckey_de`,
  `LOTE_COMPROBACION` = 200, `ENLACES_HMORES` y `_expr_enlazada()`,
  `lineas_por_synckey`, `lineas_por_ide`, `partes_por_ide`,
  `estados_de_partes`. Ninguna sentencia `DELETE` (F-053).
- `interface_adapters/api/app.py`: `POST /api/registro/comprobar` (`def`, sin
  lock, 422/502 como dice la spec): el patrón de la ruta nueva sigue valiendo.
- `config/settings.py`: pydantic con `Field(alias=…)`; `SIGRID_API_TIMEOUT_S`
  60 s por defecto (encaja con el umbral de 60 s de M1).
- `LineaSigrid` (`registro_models.py`) existe; `LineaSincronizar` sigue siendo
  nueva.
sv4 (`services/partes-front/`):
- `ComprobacionSigrid.comprobar_ids(ids, *, origen, forzar)`: `origen` solo se
  registra en el log; la lista `ORIGENES_COMPROBACION` (`vista-obra`,
  `vista-trabajador`, `boton`) solo filtra la ruta `/api/sigrid/comprobar`.
  Llamarla en proceso con `origen="sincronizar"` es válido (R10).
- `registro_ids_de_obra(clave, period_key, mode)`, `registro_ids_de_trabajador`
  (todos sus meses), `_actor(request)`, `_exigir_reg_editable`,
  `_exigir_sin_recalculo(doc)`, `registros_con_reparto(ids)`,
  `aplicar_comprobacion_sigrid` (CAS por `sigrid_hmores_ide`),
  `borrar_linea`, `restore_registro` (409 `DuplicadoActivoError`, F-061),
  `transfer_client._post` / `comprobar`.
- Vistas `/obras/{obra_key}` y `/trabajadores/{worker_key}` con `period` y
  `modo`; botón «Comprobar en Sigrid» en `obra_detail.html` (l. 28) y
  `trabajador_detail.html` (l. 37): el sitio del botón nuevo existe.
- `congelacion.py` y `recurso_conciliador.py` (gemelos): no se tocan (R28).
Raíz: `test_f038_lectores_sigrid.py` (lista cerrada: el cliente de sv5 ya
está), `test_f024_borrado_no_congela_gemelos.py`, `test_f010_orm_models_gemelos.py`.
Documentos: `azure-apps/partes.md` describe `/api/registro/comprobar` (l. 138
y 763): ahí irá el endpoint nuevo; `sigrid_api.md` §6.4 y §6.7 siguen.

## 2. Cambios mecánicos aplicados (16)

Lista completa en `tasks.md` «Revalidación 2026-11-01». Los de más peso:
1. F-050 ya está en `dev` (cabecera de requirements, T1).
2. R15: obra sin `obra_ide` = `cod-`, `nom-`, `sin-obra` (`obra_key_for_registro`).
3. R21: `_exigir_sin_recalculo` cubre ya el parte nuevo de F-047.
4. R24: el 409 de `restore_registro` (F-061) vuelve como descartado.
5. `_validar_ambito` es un cierre de `app.py` que exige 1–5000 ids y textos de
   aprobación: sirve a `/aplicar`, no a `/api/sincronizar` (sin ids).
6. `period_bounds(año, mes, modo)` + `parse_period_key`.
7. `enlazada` con `_expr_enlazada()` (la comparten reajuste, choques y racha).
8. Guardián de lectores de F-038: no cambia (mismo fichero). El cambio de
   `_read` que había aquí se retiró con DA11 (§6): `_read` no se toca.
9. Motivo de recálculo en `tests/test_f052_contrato_motivos.py` (precedente
   F-049) en vez de la parametrización de F-042.
10. Semántica nueva = 22 (la 18 es F-054).
11. H1 resuelto por F-053 (también `MOTIVO_LINEA_REGISTRADA`); H2 por F-038.
12. DA9 superada.

## 3. Decisiones abiertas nuevas (design §8)

- **DA11 · lectura tras F-038**. DECIDIDA (§6); la recomendación A
  (`PAGINA_FILAS` = 5000) fue rechazada.
- **DA12 · synckeys `partes:<id>:ciz` (F-062) y `partes:franquicia:<id>`
  (F-056)**. Empiezan por `partes:`; `registro_de_synckey` (sv5,
  `racha_ciz.py`) devuelve None para las dos. Con la spec, el CIZ hermano
  saldría `solo_sigrid_nuestra` (con `restaurar`) o mal casado, y la línea de
  franquicia sin `registro_id`. Rec. **A**: orígenes `ciz` y `franquicia` en
  sv5 y una clase informativa `solo_sigrid_auxiliar` en sv4 (12 clases).
- **DA13 · líneas a 0 fuera del portal (F-053)**. Las ajenas/manuales pisadas
  ya no desaparecen: quedan `can = 0`. Rec. **A**: marca `a_cero` (no `CI*`),
  ocultas por defecto con contador.
- **DA14 · `omitido` sin pareja según motivo**. Motivos de sv5 hoy:
  `parte_no_abierto`, `pisada_no_anulada` (sv5 pide reaprobar),
  `fecha_no_valida` (F-055), `fin_movido`/`intermedio`/`ciz_en_parte_cerrado`
  (F-060), `incidencia_en_sigrid`, `linea_enlazada` (F-053), `parte_cerrado`
  (F-031). Rec. **A**: las dos reaprobables ⇒ `pendiente`; el resto
  `no_viaja` con nota.
- **DA15 · `traer_de_sigrid` frente a F-046/F-049**. La pasada de sv3 reparte
  por (recurso, día) entre obras: cambiar una congelada mueve el residual de
  otras obras (lo que motivó el pedido compartido de F-049). Y el registro
  bloquea con `ESTADOS_BLOQUEAN` (incluye `rechazado`), no solo los dos de R21.
  Rec. **A**: `_pedir_recalculo_compartido` + `ESTADOS_BLOQUEAN`.
- **DA16 · parte reemplazado por la reingesta de sv3** (`deleted_by` NULL):
  sus `partes:<id>` en Sigrid saldrían `no_existe`. Rec. **A**: `donde =
  parte_reemplazado`, informativo. El parte retirado de F-061 no necesita
  valor propio: sus líneas ya están en la papelera.
- **DA17 · partir**. DECIDIDA (§6): una sola; la recomendación A fue rechazada.
  Texto original: con DA11–DA16, design queda en 225/250 y requirements en
  128/150, con 30 requisitos, 12 clases, panel JS y una escritura sobre líneas
  congeladas en rigor crítico. Rec. **A**: F-052 = lectura + comparación +
  panel informativo (DA1 = B, rigor estándar); las acciones hacia el portal
  (R16–R25, DA3, DA15) en una feature crítica nueva, después de M2.

## 4. DA1–DA10 revisadas

- DA1: sigue en A (DA17: una sola feature).
- DA2, DA4, DA5, DA6, DA7, DA10: siguen sin cambios (F-024 sigue siendo
  dueña del synckey en sv5; F-018 no ha llegado).
- DA3: sigue (solo horas).
- DA8: sigue en crítico.
- DA9: **superada** (F-050 y F-049 en `dev`; el humano lanzó F-052).
- Clases de R8: las líneas anuladas por F-053 caben en `anulada_en_sigrid`
  (cambio mecánico de §3); partes cerrados de F-034 no cambian la
  clasificación (`parte_est` ya viaja, R2) y solo importarán a la feature que
  escriba en Sigrid; F-055 entra en DA14; `reparto_pendiente` y partes en
  espera en R21/DA15; la franquicia en DA12.

## 5. Verificaciones

- M1 no se ha hecho (solo lectura en Sigrid, la deja la spec al humano antes
  de implementar): dimensiona el tope, si sigue, y mide el tiempo.
- Topes y portero: `bash harness/init.sh` en verde en el worktree.

## 6. Decisiones del humano (2026-11-02)

Literal: «recuerda que la api lee hasta 500k, no 5k lineas. se pagina a partir
de ahi-da17, en una sola». Las demás DA (DA2–DA7, DA10, DA12–DA16) siguen
pendientes.

- **DA11**: sv5 lee hasta el límite real, `self._max_rows`
  (`SIGRID_API_MAX_ROWS`, 500.000, `MAX_ROWS_DEFECTO`) y solo pagina a partir
  de ahí. Fuera `PAGINA_FILAS` y `SINCRONIZAR_PAGINA`. Tocados R3, R4, design
  §5, §7 y §10, M1, T1, T2, T3.
  - **Por qué sin `+ 1`** (leído en `sigrid-api`): `sql_query_guard.py` rechaza
    `max_rows > max_allowed_rows`, así que 500.001 no se puede pedir; y
    `sql_server_repository.py` hace `fetchmany(max_rows + 1)`, con `truncated`
    solo si hay más filas que `max_rows`. Con `FETCH NEXT` = `max_rows`, una
    página justa no es error y `_read` sirve tal cual: «página llena» es la
    señal de seguir (`sigrid_api.md` §6.4). Por eso se retira el cambio
    mecánico de `_read` (de 17 a 16).
  - **Tiempo**: lo que limita es el corte de 230 s, no las filas. R4 lo recoge
    (corte = 502 sin parciales) y §10 suma los pasos dentro de los 150 s.
  - **`SINCRONIZAR_MAX_LINEAS`: duda de entonces, resuelta en §7.** Acota dos cosas
    distintas: el total de líneas de R3 («periodo demasiado grande») y
    `registro_ids` de R1/R6. El 5000 por defecto se ha quitado de design:
    reintroducía como tope funcional la cifra que el humano acaba de
    descartar, y la spec ya lo dejaba a M1. Opciones: (a) retirarlo de R3 y
    que el límite sea el tiempo, conservando solo una cota de `registro_ids`
    para el 422; (b) mantenerlo con un valor mayor tras M1. Se traslada al
    líder.
- **DA17**: una sola feature, R1–R30 y rigor crítico; DA1 = A y DA8 = crítico
  se quedan. Entre B y C se resolvió después por B (§7).

## 7. Aprobación y M1 (2026-11-02)

Transmitida por el líder: el humano respondió «si» a «Si dices "sí", apruebo
las tres de la tabla y todas esas con la recomendación».

- **Aprobadas**: DA1 = A, DA2–DA7 = A, DA8 = crítico, DA10 = A, DA12–DA16 = A.
  Aplicadas al texto: glosario y R2 (`ciz`, `franquicia`, `ajuste_id`), R8
  (clase 12, `a_cero`), R11 (DA14), R12 (`parte_reemplazado`), R21
  (`ESTADOS_BLOQUEAN`), R23 (compartido); design §2–§6 y T5, T6, T9, T10.
  DA15 necesita `documentos_de_los_dias(pares)`: `otras_de_celda` va por celda.
- **`SINCRONIZAR_MAX_LINEAS` retirado**: sale de R1, R3 y R6, de T3 y de §9. El
  límite es el corte de 230 s (R4). Queda solo **`SINCRONIZAR_MAX_REGISTRO_IDS`
  = 3000** (422, R6): 15 lotes de 200 a 7,9 s (M1) son unos 119 s, más unos 5 s
  de la lectura, dentro de los 150 s de sv4→sv5; y es 8 veces las 371 líneas de
  la obra mayor. El 7,9 s es una sola medición.
- **DA17 = B**: tareas renumeradas. T6 y T7 quedan en lectura y comparación, con
  `POST /api/sincronizar` para que M2 se pueda ejecutar; **T8 es el punto de
  control**; T9–T10 son lo que era la parte de aplicar de T6–T8; T11–T17 son las
  antiguas T9–T15. M2 es manual y sin panel: lee la respuesta JSON.
- **M1 (líder)**: en `design.md` §9. Se queda `WHERE h.obride = ?`; se quita de
  §7 la variante por `hmo`. Salvedad: M2 con obras con líneas del portal.
- **Aclaración en M2**: con `POST /api/sincronizar`, R10 puede pasar líneas a
  `borrado_sigrid` en la base `partes` a la que apunte el sv4 local; es lo mismo
  que hace F-024 al abrir la vista, pero M2 ya no es «ninguna escritura» a secas.
