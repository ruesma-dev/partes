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

**Reutiliza** (sin cambiarlo): la comprobación F-024 completa (`ComprobacionSigrid`,
`/api/registro/comprobar`, el respaldo por `hmores_ide` y la transición a `borrado_sigrid`,
R10); `_validar_ambito` de F-022 y los ids de vista `registro_ids_de_obra` /
`registro_ids_de_trabajador` (R18); `_actor(request)` (R22); el publicador de recálculo de
F-042 (R23); `period_bounds` (`calendar_builder.py`) para el rango; las guardas
`_exigir_sin_recalculo` (F-043) y la marca de reparto pendiente (F-046, R21); papelera,
restaurar y el modal de aprobar con `ambito`/`incluir_borradas` (R24); `ENLACES_HMORES` de
F-046 para `enlazada`; el patrón de paginación de `sigrid_api.md` §6.4.

**No reutiliza, a propósito**: la pantalla «Conciliar» (`/conciliacion`, F-039) es el casado
de **trabajadores** sin identificar, no de líneas contra Sigrid; para no confundirlas el botón
se llama «Sincronizar con Sigrid» y las acciones llevan su verbo propio (§4). El cliente de
maestros de sv4 (`sigrid_lookup_client.py`) no lee `hmores` y sigue sin hacerlo.

**Nuevo**: la lectura por ámbito de sv5, la clasificación en 11 clases, el panel y la acción
`traer_de_sigrid`, que es la única escritura nueva sobre líneas congeladas (R20, §6).

## 2. Flujo

```
botón «Sincronizar con Sigrid» (vista obra o persona, periodo visible)
  -> sv4 POST /api/sincronizar {ambito:{vista, obra_key|worker_key, period, mode}}
       1. ámbito -> (obra_ide | recurso_ide), desde/hasta = period_bounds(period, mode)
       2. repo.lineas_para_sincronizar(ámbito, desde, hasta)        [base partes, lectura]
       3. sv5 POST /api/sincronizar/leer {obra_ide|recurso_ide, desde, hasta, registro_ids}
       4. sincronizacion.clasificar(portal, sigrid)                   [puro]
       5. registrado sin pareja -> ComprobacionSigrid.comprobar_ids(forzar)  [F-024, R10]
       6. repo.donde_estan(ids de solo_sigrid_nuestra)                [R12]
  <- {ok, periodo, leido_at, recuento, items[]}   (efímero, R14)

panel: filtros por clase, casillas, «todas las de esta clase», botón por acción
  -> confirmación (R17) -> POST /api/sincronizar/aplicar {accion, ambito, items[{id, firma}]}
       valida ámbito (F-022) -> repite 2-6 -> aplica solo firma igual -> recálculo (F-042)
  <- {aplicados, descartados[], recalculo} -> el panel vuelve a sincronizar (R25)
```

## 3. Clases (R8) con ejemplos

Ejemplos sintéticos: obra 0686, periodo natural 10/2026, recurso R1; ids ficticios.

| Clase | Cuándo | Ejemplo |
|---|---|---|
| `igual` | Casada, sin diferencias (puede llevar nota de código de hora) | 501: 8 h ordinaria, partida P1 en los dos |
| `distinta` | Casada, portal `registrado`, ≥ 1 diferencia (R9) | 502: portal 8 h, Sigrid 6 h (Administración la editó) |
| `anulada_en_sigrid` | Casada, portal `registrado` con horas ≠ 0, Sigrid `can = 0` | 503: 2 h extra en el portal, Sigrid la dejó a 0 |
| `borrada_en_sigrid` | Portal `registrado`/`borrado_sigrid` y F-024 confirma que no está | 504: Administración la borró a mano |
| `en_sigrid_sin_registrar` | Casada; estado del portal vacío, `omitido`, `error`, `conflicto` o `borrado_sigrid` | 505: `error` por timeout de sv5, pero sí se escribió |
| `pendiente` | Sin pareja; estado vacío, `error` o `conflicto` | 506: aún no aprobada |
| `no_viaja` | `dedicacion` (siempre) u `omitido` sin pareja | 507: extra de un mensual omitida por las reglas |
| `en_vuelo` | `encolado` (no se compara) | 508: petición en `q-transfer` |
| `solo_sigrid_nuestra` | `partes:<id>` sin línea del portal en el ámbito; `donde` (R12) | `partes:509`, la 509 está en la papelera |
| `solo_sigrid_ajena` | Synckey de otro espacio (`porcentajes:`…) | `porcentajes:77`, dedicación del mensual |
| `solo_sigrid_manual` | Sin synckey | Línea de R1 del 14/10, 8 h, metida a mano |

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
| `solo_sigrid_ajena`, `igual`, `no_viaja`, `en_vuelo` | — | — | nunca (la ajena es de dedicación) |

## 5. Ficheros

**sv5 — crear**: `tests/test_f052_leer_sincronizar.py` (cliente con `httpx` simulado),
`tests/test_f052_api_sincronizar.py` (TestClient). **Modificar**:
- `infrastructure/sigrid/sigrid_write_client.py`: `lineas_sincronizar(*, obra_ide | recurso_ide,
  desde, hasta, pagina, tope)` (paginado) y `lineas_sincronizar_por_synckey(claves)` (lotes de
  `LOTE_COMPROBACION`), con un SQL de columnas común (§7); `origen_de(synckey) -> (origen,
  registro_id | None)`, junto a `synckey_de`.
- `domain/models/registro_models.py`: dataclass `LineaSincronizar` (campos de R2).
- `interface_adapters/api/app.py`: `SincronizarIn` (validación de R6) y la ruta (`def`, como
  `comprobar`); `config/settings.py`: `SINCRONIZAR_PAGINA` (1000) y `SINCRONIZAR_MAX_LINEAS`
  (5000).

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
- `infrastructure/persistencia/recalculo_publisher.py`: `MOTIVO_SINCRONIZAR = "sincronizar"`.
- `interface_adapters/web/app.py`: payloads, `POST /api/sincronizar` y
  `/api/sincronizar/aplicar`, composición; `config/settings.py`: `SINCRONIZAR_TIMEOUT_S` (150,
  < 230 del balanceador) y `SINCRONIZAR_MAX_ITEMS_ACCION` (500).
- `templates/obra_detail.html`, `templates/trabajador_detail.html`: botón junto a «Comprobar en
  Sigrid» (deshabilitado con motivo, R15) y contenedor del panel; `static/app.js` (panel,
  filtros, selección, confirmación, `esc()` en todo lo pintado) y `static/styles.css`.

**Raíz**: `tests/test_f042_contrato_recalculo.py` añade `MOTIVO_SINCRONIZAR` a su
parametrización. **Documentación**: `docs/ARCHITECTURE.md` (doble canal: la ruta nueva;
semántica 10: la excepción de R20; semántica 18 nueva, resumen de F-052) y
`azure-apps/partes.md` (endpoint de sv5, rutas y variables de sv4), en el mismo trabajo.

**No se tocan**: `congelacion.py` (sv4) y `recurso_conciliador.py` (sv3) —R28, gemelos de
F-024—; `comprobacion_sigrid.py` y `comprobacion_lineas.py` (se llaman, no se cambian);
`registro_pipeline.py`, `reajuste_pipeline.py`, `estado_parte.py`, `cuenta_analitica.py`
(copias en `porcentajes`); `orm_models.py` (ninguna columna nueva); `sigrid_lookup_client.py`;
sv1, sv2, sv3.

## 6. Escrituras en la base `partes` (sv4)

- `aplicar_marcar_registrada(items, actor, ahora)`: una transacción; por id `SELECT … FOR
  UPDATE`, CAS: sigue activa, mismo `sigrid_estado` y mismo `sigrid_hmores_ide` que al
  clasificar; escribe R19. Una línea `registrado` queda congelada desde ese momento.
- `aplicar_traer_de_sigrid(items, campos, actor, ahora)`: CAS por línea sobre `sigrid_estado =
  'registrado'` y los valores del portal que vio el usuario; descarta (R21) si
  `_exigir_sin_recalculo` lo prohíbe o el día tiene reparto `pendiente`/`aplicando`. Escribe
  `horas` (y, con DA3 B/C, `partida_*` / `hora_*`), `sigrid_motivo` (R22). **No** pasa por
  `_exigir_reg_editable`: es la excepción controlada de R20, como la materialización de F-046
  en sv3. `horas_orig` no se toca (sv3 no recalcula lo congelado, semántica 3).
  Sin `undo_log`: deshacer una línea `registrado` ya lo prohíbe la congelación, y la vuelta
  atrás es volver a sincronizar.
- Después de la transacción, un mensaje de recálculo por documento (R23).

## 7. SQL nuevo (sv5, vía `/api/sql/read`, base `ruesma`)

```sql
SELECT h.ide, h.hmoide, pc.cod AS parte_cod, pc.est AS parte_est, h.obride,
       oc.cod AS obra_cod, h.reside, h.fec, h.horide, a.cod AS hora_cod, a.ext AS hora_ext,
       h.paride, p.cod AS partida_cod, h.can, h.tot, h.synckey,
       CASE WHEN <ENLACES_HMORES <> 0> THEN 1 ELSE 0 END AS enlazada
FROM hmores h
LEFT JOIN con pc ON pc.ide = h.hmoide   LEFT JOIN con oc ON oc.ide = h.obride
LEFT JOIN auxhor a ON a.ide = h.horide  LEFT JOIN obrparpar p ON p.ide = h.paride
WHERE h.obride = ? AND h.fec BETWEEN ? AND ?          -- ámbito persona: h.reside = ?
ORDER BY h.ide OFFSET ? ROWS FETCH NEXT ? ROWS ONLY   -- max_rows = pagina + 1
```

Por synckey: mismo `SELECT`/`FROM` con `WHERE h.synckey IN (…)` en lotes de 200, sin paginar
(agregado acotado, `sigrid_api.md` §6.7). `truncated` ⇒ excepción (R3). Si M1 mide que filtrar
por `h.obride` no usa índice y tarda, la variante es `h.hmoide IN (SELECT ide FROM hmo WHERE
obride = ? AND ano/mes del periodo)`, que cubre las líneas en partes de obra (semántica 5);
decide M1, no se implementan las dos. Sin esquema nuevo en PostgreSQL.

## 8. Decisiones abiertas (para el humano)

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
| DA9 | Sitio en la cola (hoy F-050 → F-049 → F-014 → F-047) | A) F-050 → F-049 → **F-052** → F-014 → F-047 · B) justo tras F-050 · C) al final | **A**: necesita F-050; F-049 toca la misma vista de obra y conviene no cruzar ramas en `app.js` |
| DA10 | Lectura de `hmores` | **A**) en sv5 (dueño del synckey) · B) en el cliente de maestros de sv4 | **A**: B rompe la frontera de F-024 y duplicaría el formato del synckey |

## 9. Verificaciones manuales (humano)

- **M1 (antes de implementar, solo lectura, `/api/sql/read` sobre `ruesma`)**: para la obra con
  más líneas del último mes y para un recurso con varias obras, `SELECT COUNT(*)`, `MIN/MAX(ide)`
  y tiempo de las dos formas del `WHERE` de §7 en mes natural y en periodo de nómina; cuántas
  son `partes:`, `porcentajes:` y sin synckey. Dimensiona `SINCRONIZAR_MAX_LINEAS`, la página y
  la forma del filtro; si alguna pasa de 60 s, `blocked` y se replantea.
- **M2 (tras implementar, local contra producción en solo lectura)**: sincronizar 2 obras y 2
  personas reales y revisar a mano 10 ítems de clases distintas contra Sigrid; ninguna escritura.
- **M3 (local, modo pruebas, obra 0404)**: con líneas `PRUEBA-IA` editadas a mano en Sigrid
  (horas cambiadas, una a 0), `traer_de_sigrid` y `marcar_registrada` en la base `partes` local;
  limpiar con `prueba_escritura_sigrid.py`.
- **M4 (tras desplegar)**: una sincronización en producción por un usuario real y comprobar
  `sigrid_motivo`/actor de una acción aplicada.

## 10. Riesgos y hallazgos

- **Volumen**: una obra × nómina son «cientos de líneas» (§ doble canal); el tope y la página
  salen de M1. El timeout de sv4→sv5 (150 s) queda por debajo del corte de 230 s.
- **Obra 0404 de pruebas**: sus `partes:<id>` vienen de bases locales y pueden chocar con ids
  reales; en ese ámbito el panel avisa de que `solo_sigrid_nuestra` no es fiable.
- **H1 (fuera de alcance, propuesto como feature aparte)**: la regla «en Sigrid no se borra»
  choca con dos cosas que ya existen: el pisado de conflictos de sv5 hace `DELETE`
  (`stmt_borrar_linea` en el paso 9 de `registro_pipeline.py`) y el candado de una línea
  registrada (`MOTIVO_LINEA_REGISTRADA`) dice «borra la línea en Sigrid». F-052 no lo cambia.
- **Despliegue**: sv5 antes que sv4 (orden seguro); sin sv5 nuevo, sv4 responde 502 al botón.
