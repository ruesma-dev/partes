<!-- specs/F-052-sincronizar-con-sigrid/design.md -->
# F-052 · Sincronizar con Sigrid — Diseño

## 1. Límite de servicio y lo que se reutiliza

| Servicio | Qué hace en F-052 | Por qué ahí |
|---|---|---|
| **sv5** `partes-transfer` | `POST /api/sincronizar/leer`: lee `hmores` del ámbito y periodo y por synckey; devuelve `origen` y `registro_id` | Es el dueño del synckey y de la lectura de `hmores` (F-024: «sv4 no lee Sigrid ni conoce el formato del synckey»). Solo lectura, sin lock |
| **sv4** `partes-front` | Botón, comparación pura, panel de resultado, `POST /api/sincronizar` y `/aplicar` | Dueño de la base `partes`, de la congelación y del actor (F-017) |

No se tocan sv1, sv2, sv3 ni el ORM. Ninguna lógica se copia entre servicios: sv5 solo lee y
etiqueta el origen; la comparación vive **una vez**, en sv4. La lista cerrada de duplicación de
`CLAUDE.md` no crece. Ninguna responsabilidad nueva cae fuera de partes: **no** se propone
microservicio aparte (la lectura cabe en el contrato sv4↔sv5 por HTTP interno que ya existe).

**Reutiliza** (sin cambiarlo): la comprobación F-024 completa (`ComprobacionSigrid` de sv4,
que llama a sv5 `/api/registro/comprobar`; el respaldo por `hmores_ide` y la transición a
`borrado_sigrid`, R10); `_validar_ambito` de F-022 (cierre de `app.py`: exige 1–
`MAX_IDS_APROBACION` ids, así que solo lo usa `/aplicar`) y los ids de vista
`registro_ids_de_obra` / `registro_ids_de_trabajador` (R18); `_actor(request)` (R22); el
pedido compartido de F-049, `_pedir_recalculo_compartido` (R23, DA15); `parse_period_key` + `period_bounds(año, mes, modo)`
(`calendar_builder.py`) para el rango; las guardas `_exigir_sin_recalculo(doc)` (F-043/F-047)
y `registros_con_reparto(ids)` (F-046, R21); `borrar_linea`, `restore_registro` y el modal de
aprobar con `ambito`/`incluir_borradas` (R24); `_expr_enlazada()` del cliente de sv5 (F-046/
F-053) para `enlazada`; el patrón de paginación de `sigrid_api.md` §6.4 (DA11).

**No reutiliza, a propósito**: la pantalla «Conciliar» (`/conciliacion`, F-039) es el casado
de **trabajadores** sin identificar, no de líneas contra Sigrid; para no confundirlas el botón
se llama «Sincronizar con Sigrid» y las acciones llevan su verbo propio (§4). El cliente de
maestros de sv4 (`sigrid_lookup_client.py`) no lee `hmores` y sigue sin hacerlo.

**Nuevo**: la lectura por ámbito de sv5, la clasificación en 12 clases, el panel y la acción
`traer_de_sigrid`, que es la única escritura nueva sobre líneas congeladas (R20, §6).

## 2. Flujo

```
botón «Sincronizar con Sigrid» (vista obra o persona, periodo visible)
  -> sv4 POST /api/sincronizar {ambito:{vista, obra_key|worker_key, period, mode}}
       1. ámbito -> (obra_ide | recurso_ide), desde/hasta = period_bounds(*parse_period_key(period), mode)
       2. repo.lineas_para_sincronizar(ámbito, desde, hasta)        [base partes, lectura]
       3. sv5 POST /api/sincronizar/leer {obra_ide|recurso_ide, desde, hasta, registro_ids}
       4. sincronizacion.clasificar(portal, sigrid)                   [puro]
       5. registrado sin pareja -> ComprobacionSigrid.comprobar_ids(forzar)  [F-024, R10]
       6. repo.donde_estan(ids de solo_sigrid_nuestra)                [R12]
  <- {ok, periodo, leido_at, recuento, items[]}   (efímero, R14)

panel: filtros por clase, casillas, «todas las de esta clase», botón por acción
  -> confirmación (R17) -> POST /api/sincronizar/aplicar {accion, ambito, items[{id, firma}]}
       valida ámbito (F-022) -> repite 2-6 -> aplica solo firma igual -> recálculo compartido (F-049)
  <- {aplicados, descartados[], recalculo} -> el panel vuelve a sincronizar (R25)
```

## 3. Clases (R8) con ejemplos

Ejemplos sintéticos: obra 0686, periodo natural 10/2026, recurso R1; ids ficticios.

| Clase | Cuándo | Ejemplo |
|---|---|---|
| `igual` | Casada, sin diferencias (puede llevar nota de código de hora) | 501: 8 h ordinaria, partida P1 en los dos |
| `distinta` | Casada, portal `registrado`, ≥ 1 diferencia (R9) | 502: portal 8 h, Sigrid 6 h (Administración la editó) |
| `anulada_en_sigrid` | Casada, portal `registrado` con horas ≠ 0, Sigrid `can = 0` | 503: 2 h extra en el portal, Sigrid la dejó a 0 (Administración o el pisado de F-053) |
| `borrada_en_sigrid` | Portal `registrado`/`borrado_sigrid` y F-024 confirma que no está | 504: Administración la borró a mano |
| `en_sigrid_sin_registrar` | Casada; estado del portal vacío, `omitido`, `error`, `conflicto` o `borrado_sigrid` | 505: `error` por timeout de sv5, pero sí se escribió |
| `pendiente` | Sin pareja; estado vacío, `error`, `conflicto` u `omitido` por `parte_no_abierto` / `pisada_no_anulada` (DA14) | 506: aún no aprobada |
| `no_viaja` | `dedicacion` (siempre) u otro `omitido` sin pareja, con el motivo como nota (prefijo de `sigrid_motivo`, como agrupa el modal) | 507: extra de un mensual omitida por las reglas |
| `en_vuelo` | `encolado` (no se compara) | 508: petición en `q-transfer` |
| `solo_sigrid_nuestra` | `partes:<id>` sin línea del portal en el ámbito; `donde` (R12) | `partes:509`, la 509 está en la papelera |
| `solo_sigrid_ajena` | Synckey de otro espacio (`porcentajes:`…) | `porcentajes:77`, dedicación del mensual |
| `solo_sigrid_manual` | Sin synckey | Línea de R1 del 14/10, 8 h, metida a mano |
| `solo_sigrid_auxiliar` | Origen `ciz` o `franquicia` (DA12): nuestra, sin línea propia en el portal; no se compara | `partes:505:ciz`, CIZ hermano de un inicio |

Una incidencia intermedia de racha (semántica 4) es `omitido` ⇒ `no_viaja`: verla «solo en el
portal» es correcto. Una diferencia de fecha u obra (110: el portal dice 15/10 y Sigrid 16/10)
es `distinta` informativa: esta entrega no mueve líneas (DA3).

## 4. Acciones por clase (R16)

| Clase | Acción E1 (hacia el portal) | Qué escribe | Fuera de E1 (DA1) |
|---|---|---|---|
| `distinta` (campos DA3) | `traer_de_sigrid` | horas (y DA3) ← Sigrid; motivo; recálculo | `llevar_a_sigrid` (reajuste F-046) |
| `anulada_en_sigrid` | `traer_de_sigrid` | horas = 0 | — |
| `en_sigrid_sin_registrar` | `marcar_registrada` | estado y referencias (R19) | — |
| `borrada_en_sigrid` | `a_papelera` · `reaprobar` | rutas existentes (R24) | — |
| `pendiente` | `reaprobar` (= aprobar) | modal existente | — |
| `solo_sigrid_nuestra` `papelera` | `restaurar` | ruta existente | `poner_a_cero_en_sigrid` |
| `solo_sigrid_manual` | — (informativa) | — | `importar_al_portal` |
| `solo_sigrid_ajena`, `solo_sigrid_auxiliar`, `igual`, `no_viaja`, `en_vuelo` | — | — | nunca (la ajena es de dedicación) |

**ID8 · `restaurar` sin la validación de ámbito de F-022 — añadido en T10 (64188c0), PENDIENTE DE RATIFICAR POR EL HUMANO** (se aparta de R18, que pide validar el ámbito «como F-022»): una línea en la papelera no está en los ids de la vista, así que `_validar_ambito` haría imposible el `restaurar` de R24. Su pertenencia al ámbito la prueba el re-sync de `aplicar`: un id que no sale en él da 422 a toda la petición sin escribir, y `acciones_de` solo ofrece `restaurar` a una `solo_sigrid_nuestra` con `donde == "papelera"` y no `repetida`. Tests: `test_f052_r24_aplicar_restaurar_desde_la_papelera`, `test_f052_r18_id_ajeno_al_ambito_422_sin_tocar_nada` y `test_f052_r24_restaurar_fuera_de_la_papelera_no_aplica`.

## 5. Ficheros

**sv5 — crear**: `tests/test_f052_leer_sincronizar.py` (cliente con `httpx` simulado),
`tests/test_f052_api_sincronizar.py` (TestClient). **Modificar**:
- `infrastructure/sigrid/sigrid_write_client.py`: `lineas_sincronizar(*, obra_ide | recurso_ide,
  desde, hasta)` (DA11, §7) y `lineas_sincronizar_por_synckey(claves)` (lotes de
  `LOTE_COMPROBACION`), con un SQL de columnas común (§7); `origen_de(synckey) -> (origen,
  registro_id | None, ajuste_id | None)`, junto a `synckey_ciz_de` y `synckey_franquicia`, con test
  de que coincide con `registro_de_synckey` (DA12).
- `domain/models/registro_models.py`: dataclass `LineaSincronizar` (campos de R2).
- `_read` no cambia: ya pide `self._max_rows` (`SIGRID_API_MAX_ROWS`). El guardián de F-038
  (`tests/test_f038_lectores_sigrid.py`) tampoco: mismo fichero lector y ningún literal.
- `interface_adapters/api/app.py`: `SincronizarIn` (validación de R6) y la ruta (`def`, como
  `comprobar`); `config/settings.py`: `SINCRONIZAR_MAX_REGISTRO_IDS` (3000: unos 15 lotes × 7,9 s de M1 ≈ 2 min,
  dentro de los 150 s, y 8 veces la obra mayor). Sin tope de líneas ni variable de página (DA11).

**sv4 — crear**:
- `application/services/sincronizacion.py` (puro): `LineaPortal`, `LineaSigridSync`,
  `Diferencia`, `ItemSync`; `clasificar(portal, sigrid) -> list[ItemSync]`; `firma(item) ->
  str` (sha256 de JSON canónico, 16 hex); `ACCIONES_POR_CLASE`; `resumen(items)`.
- `application/services/sincronizar_ambito.py`: `SincronizadorAmbito` (orquesta §2 con el
  repositorio, el cliente de sv5 y `ComprobacionSigrid` inyectados; candado por ámbito en
  proceso, R29) y `aplicar(accion, ambito, items, actor)`.
- Tests: `tests/test_f052_clasificar.py`, `test_f052_sincronizar_ambito.py`,
  `test_f052_repositorio.py` (SQLite), `test_f052_endpoints.py`, `test_f052_vistas.py` y
  `test_f052_panel_js.py` (node, como F-022).

**sv4 — modificar**:
- `infrastructure/transfer/transfer_client.py`: `sincronizar_leer(payload, *, timeout_s)`.
- `infrastructure/database/parte_repository.py`: `lineas_para_sincronizar(...)`,
  `donde_estan(ids)`, `aplicar_marcar_registrada(...)`, `aplicar_traer_de_sigrid(...)` (§6).
- `infrastructure/persistencia/recalculo_publisher.py`: `MOTIVO_SINCRONIZAR = "sincronizar"`. El
  repositorio gana `documentos_de_los_dias(pares)` por (recurso, fecha): `otras_de_celda` va por celda.
- `interface_adapters/web/app.py`: payloads, `POST /api/sincronizar` y
  `/api/sincronizar/aplicar`, composición; `config/settings.py`: `SINCRONIZAR_TIMEOUT_S` (150,
  < 230 del balanceador), `SINCRONIZAR_SECO` (DA18, `true`) y `SINCRONIZAR_MAX_ITEMS_ACCION` (500).
- `templates/obra_detail.html`, `templates/trabajador_detail.html`: botón junto a «Comprobar en
  Sigrid» (deshabilitado con motivo, R15) y contenedor del panel; `static/app.js` (panel,
  filtros, selección, confirmación, `esc()` en todo lo pintado) y `static/styles.css`.

**Raíz**: `tests/test_f052_contrato_motivos.py` (como `test_f049_contrato_motivos.py`: sv3
clasifica `MOTIVO_SINCRONIZAR` como recálculo). **Documentación**: `docs/ARCHITECTURE.md` (doble
canal: la ruta nueva; semántica 10: la excepción de R20; semántica 22 nueva, resumen de F-052) y
`azure-apps/partes.md` (endpoint de sv5, rutas y variables de sv4), en el mismo trabajo.

**No se tocan**: `congelacion.py` (sv4) y `recurso_conciliador.py` (sv3) —R28, gemelos de
F-024—; `comprobacion_sigrid.py` y `comprobacion_lineas.py` (se llaman, no se cambian);
`registro_pipeline.py`, `reajuste_pipeline.py`, `franquicia_pipeline.py`, `racha_ciz.py`,
`pisado.py`, `estado_parte.py`, `cuenta_analitica.py` (copias en `porcentajes`); en sv4
`reparto_aviso.py`, `seguimiento_recalculo.py`, `edicion_celda.py`; `orm_models.py` (ninguna columna nueva); `sigrid_lookup_client.py`;
sv1, sv2, sv3.

## 6. Escrituras en la base `partes` (sv4)

- `aplicar_marcar_registrada(items, actor, ahora)`: una transacción; por id `SELECT … FOR
  UPDATE`, CAS: sigue activa, mismo `sigrid_estado` y mismo `sigrid_hmores_ide` que al
  clasificar; escribe R19. Una línea `registrado` queda congelada desde ese momento.
- `aplicar_traer_de_sigrid(items, campos, actor, ahora)`: CAS por línea sobre `sigrid_estado =
  'registrado'` y los valores del portal que vio el usuario; descarta (R21) si
  `_exigir_sin_recalculo(reg.document)` lo prohíbe o el id está en `registros_con_reparto`. Escribe
  `horas` (y, con DA3 B/C, `partida_*` / `hora_*`), `sigrid_motivo` (R22). **No** pasa por
  `_exigir_reg_editable`: es la excepción controlada de R20, como la materialización de F-046
  en sv3. `horas_orig` no se toca (sv3 no recalcula lo congelado, semántica 3).
  Sin `undo_log`: deshacer una línea `registrado` ya lo prohíbe la congelación, y la vuelta
  atrás es volver a sincronizar.
- Después de la transacción, UN pedido compartido con esos documentos y los de otras obras del
  mismo recurso y día (R23, DA15).

## 7. SQL nuevo (sv5, vía `/api/sql/read`, base `ruesma`)

```sql
SELECT h.ide, h.hmoide, pc.cod AS parte_cod, pc.est AS parte_est, h.obride,
       oc.cod AS obra_cod, h.reside, h.fec, h.horide, a.cod AS hora_cod, a.ext AS hora_ext,
       h.paride, p.cod AS partida_cod, h.can, h.tot, h.synckey,
       CASE WHEN <_expr_enlazada()> THEN 1 ELSE 0 END AS enlazada
FROM hmores h
LEFT JOIN con pc ON pc.ide = h.hmoide   LEFT JOIN con oc ON oc.ide = h.obride
LEFT JOIN auxhor a ON a.ide = h.horide  LEFT JOIN obrparpar p ON p.ide = h.paride
WHERE h.obride = ? AND h.fec BETWEEN ? AND ?          -- ámbito persona: h.reside = ?
ORDER BY h.ide OFFSET ? ROWS FETCH NEXT ? ROWS ONLY   -- FETCH = max_rows = self._max_rows
```

Página = el límite real (DA11): `FETCH NEXT` y `max_rows` valen los dos `self._max_rows` (500.000);
hay otra lectura solo si la página viene llena. Sin `+ 1`: sigrid-api rechaza `max_rows` por
encima de `MAX_ALLOWED_ROWS`, y `truncated` solo salta con más filas que `max_rows`, así que una
página justa no es error (`sql_server_repository.py`, `fetchmany(max_rows + 1)`).

Por synckey: mismo `SELECT`/`FROM` con `WHERE h.synckey IN (…)` en lotes de `LOTE_COMPROBACION` (200), sin paginar
(agregado acotado, `sigrid_api.md` §6.7). `truncated` ⇒ excepción (R3). Se queda `WHERE h.obride = ?`
(M1, §9). Sin esquema nuevo en PostgreSQL.

## 8. Decisiones (aprobadas)

**Aprobadas por el humano el 2026-11-02**, transmitido por el líder (literal: «si» a «Si dices
"sí", apruebo las tres de la tabla y todas esas con la recomendación»): DA1 = A, DA2–DA7 = A,
DA8 = crítico, DA10 = A, DA12–DA16 = A, DA17 = B y DA11 como consta. DA9 superada. DA18 = A,
aprobada por el humano el 2026-11-03 (literal: «si» a la opción A del líder). La columna de
recomendación se conserva como razón. Detalle en `progress/explore_F-052_revalidacion.md`.

| DA | Pregunta | Alternativas | Recomendación |
|---|---|---|---|
| DA1 | Alcance de esta entrega | **A**) comparar + acciones hacia el portal (§4); escribir en Sigrid en otra feature · B) solo comparar, sin acciones · C) todo, incluido `llevar_a_sigrid`, `poner_a_cero_en_sigrid` e `importar_al_portal` | **A**: la lectura y la comparación son la base de todo y no escriben en el ERP; la escritura reutilizará el reajuste F-046 (`UPDATE can`, nunca `DELETE`) y merece su propia spec crítica |
| DA2 | Periodo | **A**) el visible (nómina 16→15 o natural), tope 62 días · B) mes natural siempre · C) rango libre | **A**: es lo que el usuario ve; en nómina son dos partes `hmo` y se leen igual |
| DA3 | Qué trae `traer_de_sigrid` | **A**) solo horas · B) horas + partida · C) horas + partida + clase de hora | **A**: las horas son lo que Administración corrige y sv3 sabe repartir; partida y clase quedan informativas hasta ver M1/M2 |
| DA4 | Qué se compara | **A**) R9 (horas, clase de hora, partida, recurso, fecha, obra; código como nota) · B) solo horas y fecha (como F-024) | **A**: la petición pide «línea a línea» |
| DA5 | ¿Se guarda el resultado? | **A**) efímero, se recalcula en cada aplicar (firma) · B) tabla `sincronizacion` en la base `partes` (esquema, dos ORM) | **A**: sin esquema ni datos que caduquen; aplicar relee Sigrid (unos segundos) y no se fía del navegador |
| DA6 | «Marcar revisada» (ocultar una diferencia aceptada) | **A**) no en E1 · B) con tabla nueva | **A**: necesita estado persistente (DA5 B); se valora en la feature posterior |
| DA7 | Traza del actor | **A**) `sigrid_motivo` + `sigrid_registrado_by` + log INFO · B) `undo_log` con `actor` (adelanta F-018) · C) tabla de auditoría | **A**: sin esquema; la auditoría general es F-018 |
| DA8 | Rigor | **crítico** · estándar | **crítico**: escribe en líneas congeladas de producción (nómina y coste) |
| DA9 | Sitio en la cola (hoy F-050 → F-049 → F-014 → F-047) | A) F-050 → F-049 → **F-052** → F-014 → F-047 · B) justo tras F-050 · C) al final | **SUPERADA** (2026-11-01): F-050 y F-049 ya están en `dev`; el humano la lanzó como siguiente |
| DA10 | Lectura de `hmores` | **A**) en sv5 (dueño del synckey) · B) en el cliente de maestros de sv4 | **A**: B rompe la frontera de F-024 y duplicaría el formato del synckey |
| DA11 | Lectura tras F-038 | **DECIDIDA por el humano el 2026-11-02** (literal: «recuerda que la api lee hasta 500k, no 5k lineas. se pagina a partir de ahi»): sv5 pide hasta el límite real (`SIGRID_API_MAX_ROWS`, `self._max_rows`, 500.000) y solo pagina a partir de ahí (§7). Sin `PAGINA_FILAS` ni `SINCRONIZAR_PAGINA`; `truncated` sigue siendo error | Sin tope de líneas (aprobado el 2026-11-02): el límite es el corte de 230 s (R4); solo queda `SINCRONIZAR_MAX_REGISTRO_IDS` (422, R6) |
| DA12 | Synckeys nuevas que empiezan por `partes:`: `partes:<id>:ciz` (CIZ hermano, F-062) y `partes:franquicia:<id>` (F-056) | **A**) `origen` ∈ `partes`, `ciz`, `franquicia`, `ajena`, `manual` (`registro_id` en partes y ciz, `ajuste_id` en franquicia); `origen_de` junto a `synckey_ciz_de`/`synckey_franquicia` con test de que coincide con `registro_de_synckey`; sv4 añade UNA clase informativa `solo_sigrid_auxiliar` (12 clases), sin acciones ni comparación · B) tratarlas como `solo_sigrid_ajena` · C) el CIZ como nota del ítem de su inicio y la franquicia aparte | **A**: no son ajenas ni huérfanas; sin esto el CIZ saldría `solo_sigrid_nuestra` con `restaurar` y la franquicia sin `registro_id` |
| DA13 | Líneas a 0 fuera del portal: desde F-053 las ajenas o manuales pisadas quedan `can = 0` en vez de desaparecer | **A**) se clasifican igual con la marca `a_cero` (`can = 0` y código no `CI*`); el panel las oculta por defecto con «n a 0 h» · B) sin distinción · C) sv5 no las devuelve | **A**: no esconde lo que Administración ve (C) ni inunda el panel (B) |
| DA14 | `omitido` sin pareja según su motivo (F-034, F-053, F-055, F-060) | **A**) `parte_no_abierto` y `pisada_no_anulada` (sv5 pide reaprobar) ⇒ `pendiente` con `reaprobar`; el resto (`fecha_no_valida`, `fin_movido`, `incidencia_en_sigrid`, `linea_enlazada`, `parte_cerrado`, reglas) ⇒ `no_viaja` con el motivo como nota (prefijo de `sigrid_motivo`, como agrupa el modal) · B) todo `no_viaja` (R11 tal cual) | **A**: son las dos que el propio sv5 manda reaprobar; en `no_viaja` se esconderían |
| DA15 | `traer_de_sigrid` frente a F-046/F-049: recálculo y repartos que descartan | **A**) pedido compartido de F-049 (`_pedir_recalculo_compartido`) con los partes tocados y los de otras obras del mismo recurso y día, y descarte con `ESTADOS_BLOQUEAN` (`pendiente`, `aplicando`, `rechazado`, como el registro) · B) `_pedir_recalculo_seguido` por documento y solo `pendiente`/`aplicando` · C) F-042 sin seguimiento (texto literal de R23) | **A**: la pasada reparte por (recurso, día) entre obras y una congelada que cambia mueve el residual de las otras; es lo que hizo F-049 por la misma razón |
| DA16 | `donde` de `solo_sigrid_nuestra` (R12): parte desactivado por la reingesta de sv3 (`deleted_by` NULL) | **A**) valor nuevo `parte_reemplazado`, informativo (las líneas del parte retirado de F-061 ya están en la papelera: `papelera` + `restaurar`) · B) como estaba (`no_existe`) | **A**: un PDF reprocesado deja las viejas en Sigrid y las nuevas `pendiente` (duplicado): es justo lo que hay que ver |
| DA17 | Tamaño: ¿una feature o dos? | **DECIDIDA: B**, una sola feature (literal: «da17, en una sola»; el punto de control, aprobado el 2026-11-02): R1–R30, acciones hacia el portal, rigor crítico, con **punto de control obligatorio** tras la lectura y la comparación (T8): M2 sobre datos reales antes de implementar las acciones | DA1 = A y DA8 = crítico se quedan |
| DA18 | ¿Escribe R10 en la base `partes` al comparar mientras se hace M2? | **A**) modo seco: `SINCRONIZAR_SECO` (sv4, `true` por defecto) ⇒ `POST /api/sincronizar` no llama a `comprobar_ids`: pide a sv5 solo el veredicto (`/api/registro/comprobar`, lectura) y devuelve `seco: true` y `marcaria_borrado_sigrid` · B) escribir como F-024 | **APROBADA A** (humano, 2026-11-03). Variable de entorno y no campo de la petición: un sv4 local sin ella no puede escribir aunque el navegador pida otra cosa; fuera de seco hay que poner `false` a propósito (tras T8), y R10 escribe como F-024 |

**ID10 · `aplicar` y el seco — añadido en T10 (64188c0), PENDIENTE DE RATIFICAR POR EL HUMANO** (no forma parte de la DA18 aprobada el 2026-11-03; lo sacó de su celda la review 1): `aplicar` (acción explícita y confirmada, R17–R18) **no** depende del seco; este solo gobierna la escritura implícita de R10, también en la relectura de `aplicar`. Consecuencia: en seco, una `borrada_en_sigrid` aún `registrado` no se puede llevar a la papelera (está congelada) y vuelve descartada con el motivo de F-004. Tests: `test_f052_da18_aplicar_no_depende_del_modo_seco` y `test_f052_r10_fuera_de_seco_la_firma_ve_lo_que_quedo_escrito`.

## 9. Verificaciones manuales (humano)

- **M1 HECHA (líder, 2026-11-02, solo lectura, `/api/sql/read` sobre `ruesma`, SELECT de §7; mes
  01–31/10/2026, nómina 16/09–15/10/2026)**: obra mayor del mes: 244 líneas en 5,4 s y 371 en
  4,8 s en nómina (370 sin synckey, 1 `porcentajes:`); recurso con 11 obras: 11 en 0,7 s y 23 en
  0,8 s; lote de 200 synckeys: 7,9 s; `truncated` nunca. Ninguna pasa de 60 s: se queda
  `WHERE h.obride = ?`; la variante por `hmo` da las mismas 371 filas en 0,9 s (una sola medición)
  y se descarta. En la práctica nunca se pagina. **Salvedad**: esas obras y recursos no tienen
  líneas `partes:`; el volumen no cambia, pero M2 debe elegir obras con líneas del portal.
- **M2 · PUNTO DE CONTROL OBLIGATORIO (DA17 = B, T8; tras lectura y comparación, antes de las
  acciones que escriben en líneas congeladas; local, con `POST /api/sincronizar`)**: sincronizar 2
  obras y 2 personas reales **con líneas del portal** y revisar a mano 10 ítems de clases distintas
  contra Sigrid; ninguna escritura en Sigrid ni en `partes`: sv4 en **modo seco** (DA18), R10 solo
  informa (`marcaria_borrado_sigrid`). Si las clases no cuadran, se para y se vuelve a proponer.
- **M3 (local, modo pruebas, obra 0404)**: con líneas `PRUEBA-IA` editadas a mano en Sigrid
  (horas cambiadas, una a 0), `traer_de_sigrid` y `marcar_registrada` en la base `partes` local;
  limpiar con `prueba_escritura_sigrid.py`.
- **M4 (tras desplegar)**: una sincronización en producción por un usuario real y comprobar `sigrid_motivo`/actor de una acción aplicada.

## 10. Riesgos y hallazgos

- **Volumen y tiempo**: una obra × nómina son «cientos de líneas» (§ doble canal). El límite real
  no son las filas sino el tiempo: cada lectura tiene `SIGRID_API_TIMEOUT_S` (60 s, ≤ 200) y el
  balanceador corta a los 230 s. sv4→sv5 (150 s) queda por debajo, pero suma lectura por ámbito,
  lotes por synckey y comprobación F-024; un corte es error sin parciales (R4, R13). M1: 5 s la
  obra mayor y 7,9 s cada lote de 200; `SINCRONIZAR_MAX_REGISTRO_IDS` lo acota.
- **Obra 0404 de pruebas**: sus `partes:<id>` vienen de bases locales y pueden chocar con ids reales; en ese ámbito el panel avisa de que `solo_sigrid_nuestra` no es fiable.
- **H1 RESUELTO por F-053**: el pisado es `stmt_anular_linea` (`UPDATE can = 0, tot = 0`), el
  cliente de sv5 no tiene `DELETE` y `MOTIVO_LINEA_REGISTRADA` dice «En Sigrid no se borran
  líneas». Efecto aquí: una línea del portal pisada sale `anulada_en_sigrid` (§3). **H2 RESUELTO por
  F-038**: `ARCHITECTURE.md` ya dice 500.000 filas por petición.
- **H-M2-1 (M2, 2026-11-03; corregido)**: la clase de hora de Sigrid es **extra si su código
  empieza por `HE`** (`es_hora_extra` en `sincronizacion.py`), como sv5 (`HoraRecurso.es_extra`) y
  `fetch_dnis_sin_extra`: `auxhor.ext` vale 0 en las 7 `HE*` y daba 152 `distinta` falsas. Sin
  código no se compara la clase. `hora_ext` sigue en el contrato de sv5 (R2), solo informativo. El
  portal sigue con `_is_extra` (el `tipo_hora` que sv5 usa para elegir `HE`/`HL`).
- **Despliegue**: sv5 antes que sv4 (orden seguro); sin sv5 nuevo, sv4 responde 502 al botón.
