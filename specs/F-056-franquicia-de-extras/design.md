<!-- specs/F-056-franquicia-de-extras/design.md -->
# F-056 · Franquicia de extras — Diseño

## 1. Encaje, límite de servicio y rigor

- **sv5** es el único que escribe en Sigrid y el único que lee `hmores`: calcula E y A (la
  fórmula vive solo aquí, DA15), da de alta la línea de ajuste y la edita. **sv4** guarda la
  configuración y la decisión humana, calcula periodo, día de ajuste y obra (necesita el
  calendario de Sesame y las líneas de `partes`, que sv5 no tiene) y orquesta por HTTP
  síncrono (edita horas ya registradas: nunca por cola, como pisar y F-046).
- **sv3 no cambia**: el ajuste no es una fila de `parte_registros`, así que no entra en el
  reparto ponderado (F-045), ni en incidencias (F-025), ni en el editor de celda (F-049), ni en
  la congelación. Solo recibe la copia del ORM (la base es una, semántica 7).
- **Lista cerrada de `CLAUDE.md`: no crece** (DA18). No hay lógica gemela: el periodo y el día
  solo en sv4; E, A y la exclusión de choques solo en sv5. Las dos tablas van en el ORM, que
  ya está en la lista.
- **Rigor crítico**: escritura nueva en el ERP de producción que cambia horas de nómina y coste
  de obra, y edición posterior de esa línea.

## 2. Hallazgos en el código y M1 (2026-10-23)

- **H1** · «Mes de nómina» ya existe en sv4: `calendar_builder.MODE_NOMINA` = 16 del mes
  anterior → 15 (etiqueta: mes del 15). El registro en Sigrid es por mes natural (semántica 5):
  el periodo cruza dos partes `hmo` por obra, y el ajuste cae en el del mes del día de ajuste.
- **H2** · Choques (`pisado.choques`, `ReajustePipeline._choques`): recurso + día + `horide`,
  sin mirar partida, y `mias` = solo las synckeys de la petición. Una línea `HE*` de ajuste en el
  mismo día y obra que la extra del día **chocaría**: el preflight ofrecería pisar la extra real
  (a 0) o la del ajuste ⇒ R31 las excluye por prefijo de synckey.
- **H3** · `stmt_insert_linea` y `stmt_actualizar_linea` (F-046) sirven tal cual: el alta lleva
  synckey arbitraria, guarda de parte abierto y `MAX(ide)+1`; la edición, `WHERE` optimista, sin
  enlaces y guarda. `lineas_para_reajuste([sk])` ya lee `can`, `pre`, `hmoide` y `enlazada`.
- **H4** · `RegistroPipeline.preparar` (obra destino, modo pruebas, verificación F-023, reglas y
  cuenta F-021) prepara la extra del ajuste como en F-046; `_crear_parte` es la única alta.
- **H5** · M1 (solo lectura, `sql/read` contra `ruesma`, agregados sin nombres ni DNIs):
  - recursos persona de alta con `reshor`: 142 sin `HE*` y 138 con **exactamente uno**; ninguno
    con dos ni con precios `HE*` distintos ⇒ el código y el precio no son ambiguos (DA5);
  - las `HE*` se **enlazan a nómina** al procesarla (`emprccide`/`empdpreide`/`empabside`):
    ene–may 2026 ~70 %, jun 40 %, jul–oct 0 % ⇒ tras la nómina el ajuste ya no se edita (DA9);
  - Administración ya escribe a mano `HE*` negativas con `tex` «Ajuste…» (2–3 al mes, días 15 y
    16), ninguna de franquicia: confirma el corte 15/16 y el uso de `tex` (DA13);
  - nuestras líneas `partes:%`: 446, en 14 partes, todos En registro; ninguna enlazada.
- **H6** · `prueba_escritura_sigrid.py limpiar` borra por `tex = 'PRUEBA-IA'` exacto ⇒ en
  pruebas el `tex` del ajuste es la marca (R32), no el texto de producción.

## 3. Flujo y estados (`franquicia_ajuste.estado`)

```
preflight: bloque consultivo (sv5 comprobar) ──► modal: Ajustar | No ajustar | Recalcular | Mantener
ejecutar/encolar ─ajustar|recalcular─► decidido ─aplicar(sv5 ok)─► aplicado ─recalcular─► decidido
                 └no_ajustar─► rechazado ─Ajustar (vista)─► decidido    aplicar(ko)─► error ─aplicar─► …
```

- Las líneas de la aprobación viajan como siempre (sin exclusiones nuevas, DA12). El modal, al
  terminar el registro (síncrono: con la respuesta; asíncrono: cuando el sondeo de F-024 ya no
  ve `encolado` en esos ids), llama a `aplicar` de cada fila decidida y pinta el resultado. Si
  el humano cierra antes, la fila queda `decidido` y la vista de trabajador ofrece «Aplicar».
- sv5 `ejecutar`, bajo el lock: `preparar` la extra (fuera del lock, datos maestros) → lee E y
  la línea por synckey → A → `crear` / `actualizar` / `ya_aplicado` / `sin_ajuste` /
  `no_editable` → escribe (una sentencia; el alta del parte, si falta, antes) → relee.

## 4. Ficheros

### sv5 (`services/partes-transfer`)

- **Crear `application/services/franquicia.py`** (puro): `ajuste_objetivo(extras: float,
  franquicia: float) -> float` (A del glosario: `−min(E, X)` si `E > 0`, si no 0, 2 dec.);
  `veredicto(linea: LineaSigrid | None, est_parte: int | None, objetivo: float, *, est_registro:
  int, accion: AccionLinea | None) -> VeredictoFranquicia` (R24–R30); `texto_ajuste(periodo,
  objetivo, franquicia) -> str`; `MOTIVO_*` literales sin tildes (como el resto de sv5); `TOL =
  0.001`.
- **Crear `application/pipelines/franquicia_pipeline.py`**: `FranquiciaPipeline(*, cliente,
  settings, registro: RegistroPipeline)`; `lock` = `registro.lock`; `comprobar(p:
  PeticionFranquicia) -> ResultadoFranquicia` (sin lock); `ejecutar(p, usuario) ->
  ResultadoFranquicia` (lock, §3). El parte: `elegir_parte` sobre `partes_del_periodo` de la
  obra destino y mes del día; si no existe, `registro.asegurar_parte(...)`.
- **`domain/models/registro_models.py`**: `PREFIJO_FRANQUICIA = "partes:franquicia:"`,
  `es_synckey_franquicia(sk) -> bool`; dataclasses `PeticionFranquicia` (los campos de §6),
  `VeredictoFranquicia(accion, motivo)` y `ResultadoFranquicia` (los de la respuesta de §6).
- **`application/services/pisado.py`**: `choques` descarta `es_synckey_franquicia(ls.synckey)`
  (R31); sigue importando solo de `domain`.
- **`application/pipelines/reajuste_pipeline.py`**: `_choques` descarta las mismas (R31).
- **`application/pipelines/registro_pipeline.py`**: SOLO se añade `asegurar_parte(p, destino)`,
  público, que delega en `_crear_parte` con la descripción de siempre (marca en pruebas).
- **`infrastructure/sigrid/sigrid_write_client.py`** (solo métodos nuevos): `synckey_franquicia(
  ajuste_id) -> str`; `extras_del_periodo(reside, inicio, fin, excluir: str) -> float`: `SELECT
  ISNULL(SUM(h.can), 0) FROM hmores h JOIN auxhor a ON a.ide = h.horide WHERE h.reside = ? AND
  h.fec BETWEEN ? AND ? AND a.cod LIKE 'HE%' AND ISNULL(h.synckey, '') <> ?`.
- **`interface_adapters/api/app.py`**: `FranquiciaIn` (pydantic, §6) y los dos endpoints
  (`def`, como el reajuste; 502 si falla una lectura o la escritura: «no se sabe», el reintento
  es seguro); `_franquicia_a_dict`; `build_app(..., franquicia=None)` (sin pipeline ⇒ 503).
  **`main.py`**: `FranquiciaPipeline` sobre el `RegistroPipeline` compartido (un solo lock).
- **`tests/dobles.py`**: `SigridFake` con `extras_del_periodo` y líneas con synckey de ajuste.

### sv4 (`services/partes-front`)

- **Crear `application/services/franquicia.py`** (puro): `periodo_de(d) -> Periodo(clave
  'YYYY-MM', inicio, fin)` sobre `calendar_builder`; `dia_de_ajuste(periodo, jornada_de:
  Callable[[date], float]) -> date | None` (R5); `elegir_obra(lineas_dia, lineas_periodo) ->
  (obra, partida) | None` (R7); `candidatos(lineas, filas, vigente_de) -> list[Candidato]` (R9–
  R12, con `motivo` si no se puede); `extras_pendientes(grupos_evaluados, recurso, periodo)`;
  `bloque_franquicias(candidatos, veredictos) -> list[dict]`; `validar_decisiones(crudo,
  claves_validas)`; `payload_franquicia(fila) -> dict`; `ESTADOS`, `DECISIONES`.
- **Crear `application/services/franquicia_admin.py`** (puro, como `jornada_admin.py`):
  `normalizar_franquicia(datos)`, `validar_franquicia(entrada)` y solape (reusa
  `validar_vigencia`, `buscar_solape` y la conversión del «último día incluido»).
- **`infrastructure/database/orm_models.py`** y su copia de sv3: `EmpleadoFranquiciaOrm`,
  `FranquiciaAjusteOrm` (§5).
- **`infrastructure/database/parte_repository.py`**: `list_franquicias_admin`,
  `guardar_franquicia`, `desactivar_franquicia` (R2); `franquicia_vigente(dni_norm, d)` (R3);
  `lineas_trabajador_periodo(recurso_ide, inicio, fin)` (activas, con obra, partida, horas, tipo
  y `sigrid_estado`; R7, R18); `ajustes_de(claves)`; `decidir_ajuste(clave, decision, datos, *,
  actor)` (alta con el índice único o `UPDATE … WHERE id = ? AND estado = ?`; si no, 409);
  `encolados_de(recurso_ide, inicio, fin)` (R18) y `cerrar_ajuste(id, *, ok, sv5, error, actor)`.
- **`infrastructure/transfer/transfer_client.py`**: `franquicia_comprobar`, `franquicia_ejecutar`.
- **`interface_adapters/web/app.py`**: preflight con `franquicias` (R9–R14; sv5 `comprobar` por
  candidato, con el timeout de la comprobación de F-024); `ejecutar` y `encolar` procesan
  `franquicias` ANTES de los grupos (R15, R16); `POST /api/franquicia/{id}/aplicar` (R17–R19);
  contexto del ajuste en la vista de trabajador (R20); rutas de la sección de
  `/admin/jornadas` con `_exigir_admin_jornadas` (R2). Actor solo de `_actor(request)`.
- **`templates/admin_jornadas.html`** (sección), **`templates/trabajador_detail.html`** (bloque),
  **`static/app.js`** (`franquiciasHtml`, `decisionesFranquicia`, `aplicarFranquicias` tras el
  resultado y el sondeo; «Registrar» deshabilitado sin decisión, R13), **`static/styles.css`**.

### Raíz y documentación

- `tests/test_f010_orm_models_gemelos.py` y `tests/test_f015_r29_guardian_cinco_tablas.py`:
  `TABLAS` a nueve y columnas literales de las dos tablas (únicas enmiendas). Nuevo
  `tests/test_f056_contrato_franquicia.py` (R36). Docs de R35; `azure-apps` con commit local,
  sin push.

### Lo que NO se toca

sv3 salvo la copia del ORM (`recurso_conciliador.py`, `reparto_ponderado.py`,
`reajuste_reparto.py`, los dos `jornada_resolver.py`); `congelacion.py`, `esta_congelado`;
`lineas_para_registro` y `incidencias_horas.py`; `estado_parte.py`, `cuenta_analitica.py` y
`stmts_crear_parte` (copias literales en `porcentajes`); `stmt_insert_linea`,
`stmt_actualizar_linea`, `stmt_anular_linea` (se reutilizan sin cambio); `ReglasRegistro`; el
contrato de `q-transfer` y `resultado_consumer.py`; F-024 (`comprobacion_lineas.py`); `undo_log`;
`dedicacion_bandeja`; sv1, sv2, `infra/`, `CLAUDE.md`.

## 5. Esquema (base `partes`, sin fichero `NN_*.sql`)

Lo crean `create_all` y `ddl_complementario()` al arrancar sv3 y sv4. Toda `NOT NULL` con
`server_default` (como `dedicacion_bandeja`).

- **`empleado_franquicia`** (como `empleado_jornada`, que ya guarda `dni_norm`): `id` PK;
  `dni_norm` String(32) NOT NULL `''`, índice; `horas` Float NOT NULL `'0'`; `desde` String(16)
  NOT NULL `'1900-01-01'`; `hasta` String(16) (exclusivo); `nota` String(255); `is_active`
  Boolean NOT NULL `true`; `created_at_utc` String(40) NOT NULL `'1970-01-01T00:00:00Z'`,
  `created_by`, `updated_at_utc`, `updated_by`.
- **`franquicia_ajuste`** (sin nombres ni DNIs: el trabajador es su `recurso_ide`): `id` PK (su
  synckey es `partes:franquicia:<id>`); `recurso_ide` Integer NOT NULL `'0'`; `periodo`
  String(7) NOT NULL `''`; índice ÚNICO `ux_franquicia_ajuste_periodo (recurso_ide, periodo)`;
  `fecha_int`, `obra_ide` Integer NOT NULL `'0'`; `obra_codigo`, `partida_cod` String(32);
  `partida_ide` Integer; `franquicia` Float NOT NULL `'0'`; `extras` y `ajuste` Float (lo último
  de sv5); `estado` String(16) NOT NULL `'decidido'` (índice); `decision` String(16);
  `hmores_ide`, `hmoide` Integer; `parte_cod` String(32); `resultado` Text; `error`
  String(255); `decidido_por`, `aplicado_por` String(120); `decidido_at_utc`,
  `aplicado_at_utc` String(64); `creado_at_utc`, `actualizado_at_utc` String(64) NOT NULL `''`.
  Constantes en el ORM: `ESTADOS_FRANQUICIA` y una por estado.

## 6. Contrato sv4 → sv5 (`/api/franquicia/comprobar` y `/ejecutar`)

Entrada (`FranquiciaIn`): `ajuste_id` (≥ 0), `recurso_ide` (≥ 1), `franquicia` (≥ 0), `periodo`
(`YYYY-MM`), `inicio`, `fin`, `fecha_int` (YYYYMMDD, inicio ≤ fecha ≤ fin), `obra` `{ide,
codigo}`, `partida_ide`, `partida_cod`, `extras_pendientes` (0; solo lo usa comprobar), `usuario`.
En el preflight aún no hay fila: sv4 manda `ajuste_id` de la fila si existe y, si no, un
centinela `0` que solo `comprobar` admite (no hay línea que buscar; `ejecutar` con 0 ⇒ 422).

Respuesta: `ok`, `accion` (`crear` | `actualizar` | `ya_aplicado` | `sin_ajuste` |
`no_editable`), `extras` (E), `objetivo` (A), `actual` (`can` en Sigrid o null), `hmores_ide`,
`hmoide`, `parte_cod`, `parte_estado`, `complementario`, `hora_codigo`, `pre`, `motivo`,
`escrita`, `forzada_pruebas`, `error`. `tex` de producción (sin nombres): `Ajuste franquicia
extras <periodo>: <A> h (franquicia <X> h)`.

## 7. Decisiones abiertas (las aprueba el humano)

| DA | Pregunta | Alternativas | Recomendación |
|---|---|---|---|
| DA1 | ¿Dónde se guarda X? | **A** tabla nueva `empleado_franquicia` por DNI con vigencia. B columna en `empleado_jornada` (mezcla jornada y franquicia; F-016 R8 exige jornada o patrón; sv3 la lee). C campo de Sigrid (M1: no existe; habría que crearlo allí). D YAML versionado (llevaría DNIs al repositorio: prohibido). | A |
| DA2 | ¿X es mensual y de qué mes? | **A** por mes de nómina (16 → 15), X fija por periodo y vigencia para cambiarla. B mes natural. C anual. | A («mes nómina» en la petición; H1, H5) |
| DA3 | ¿Qué extras cuentan? | **A** Σ neta de `HE*` en Sigrid del recurso en el periodo: todas las obras, partes de cualquier estado, manuales de Administración, reajustes F-046 y pisados F-053 incluidos; sin el propio ajuste. B lo de `partes` (no ve lo manual ni lo omitido). C solo las positivas. | A (lo que se paga es lo de Sigrid; con E ≤ 0 no hay ajuste) |
| DA4 | Varias obras el día de ajuste: ¿dónde va la línea? | **A** una línea en la obra de más horas ese día (R7). B una línea por obra, en proporción a sus extras del periodo (más justo para el coste por obra; varias líneas y más casos). C la obra de más extras del periodo. | A («una linea de ajuste») |
| DA5 | Tipo de hora y precio | **A** el `HE*` que las reglas dan a una extra del recurso y su `pre` de `reshor`; `tot = can × pre`, cuenta F-021 (M1: nadie tiene dos). B precio 0 (solo horas; el coste de obra no bajaría). C código propio de ajuste en `auxhor`/`reshor` (lo tendría que crear Administración en cada recurso). | A |
| DA6 | ¿Qué es «el último laborable»? | **A** el último día del periodo con `jornada_dia` > 0 (calendario Sesame F-003, festivos y `empleado_jornada` F-015/F-016). B último L–V no festivo. C último día con líneas. | A (misma verdad que el cómputo de extras) |
| DA7 | ¿Qué dispara el aviso? | **A** la aprobación incluye una línea del trabajador en el día de ajuste (R9), o ya hay ajuste del periodo (R10); además, «Ajustar» en la vista de trabajador. B cualquier aprobación de líneas del periodo. C solo la vista de trabajador. | A |
| DA8 | Se registra el último día antes que otros, o hay cambios después | **A** el ajuste es una línea viva: cada aprobación posterior del trabajador y periodo enseña «antes → después» y pide «Recalcular» o «Mantener»; la vista tiene «Recalcular»; se edita con `UPDATE` (a 0, nunca borrar). B recalcular solo, sin preguntar. C una sola vez y no se toca. | A |
| DA9 | Parte cerrado o línea enlazada (tras la nómina, H5) | **A** no se edita: el aviso lo dice con el motivo y se regulariza en Sigrid. B una segunda línea de diferencia en el complementario (synckey nueva; F-046 DA10 lo descartó por lo mismo). | A |
| DA10 | Pantalla y momento | **A** aviso en el modal de aprobar (obra y trabajador); la decisión viaja con «Registrar» y el ajuste se aplica al terminar el registro (§3). B lo aplica solo el consumidor de `q-transfer-result` (hilo sin petición ni actor, más acoplado). C solo desde la vista de trabajador. | A |
| DA11 | ¿Se puede rechazar? | **A** sí: «No ajustar» deja `rechazado`, sin preguntar más ese periodo; reversible con «Ajustar» en la vista. B no. | A |
| DA12 | ¿Sin decisión se bloquea? | **A** el modal exige decidir (R13) pero el servidor no excluye líneas: el ajuste siempre puede hacerse después. B como F-046: las líneas del día de ajuste no viajan sin decisión (otra exclusión en `lineas_para_registro`). | A |
| DA13 | ¿Qué ve Administración en Sigrid? | **A** una `HE*` negativa el día de ajuste en el parte de la obra, con `tex` explicativo (§6), como sus ajustes manuales (H5). B la misma línea sin `tex`. | A |
| DA14 | ¿Cómo se identifica la línea? | **A** synckey `partes:franquicia:<id>` y exclusión en choques (R31). B código de hora propio (DA5 C). C fila en `parte_registros` con `partes:<registro_id>` (la vería sv3 en el reparto, F-025, F-049 y la congelación). | A |
| DA15 | ¿Quién calcula E y A? | **A** sv5, contra Sigrid y bajo el lock; sv4 solo pinta. B sv4 con `partes` (duplicaría la fórmula para el aviso y no ve lo manual). | A |
| DA16 | Varios recursos en el periodo, sin `HE*`, mensuales F-019 | **A** no se ajusta y se avisa (R12); un mensual con `HE*` (capataz) sí se ajusta. B un ajuste por recurso. | A |
| DA17 | ¿Interruptor? | **A** no: la tabla vacía es el apagado (nadie tiene franquicia hasta que se da de alta). B `FRANQUICIA_EXTRAS` en sv4. | A |
| DA18 | ¿Crece la lista cerrada de `CLAUDE.md`? | **A** no (§1). B sí, si el humano ve el periodo de nómina como regla compartida. | A |
| DA19 | Pantalla de configuración | **A** sección en `/admin/jornadas` con el mismo permiso y validación (R2). B carga por SQL a mano y pantalla en otra feature (como F-015 → F-016). | A |
| DA20 | ¿Una feature o dos? | **A** una, en dos bloques: sv5 (T1–T7, verificable sola en la 0404) y sv4 (T8–T16). B partir: F-056 sv5 + aviso, F-058 la pantalla de DA19. | A; si falta contexto, cortar tras T7 |

## 8. Riesgos

- **R-a · Escritura nueva en producción** que baja horas de nómina. Mitigan: decisión humana
  por trabajador y periodo, `comprobar` previo, lock, `WHERE` optimista, relectura, M2 en la
  0404 antes de dar de alta la primera franquicia real.
- **R-b · Choque con la extra del día** (H2): sin R31, pisar pondría a 0 una extra real; lo
  vigilan tests en los dos `_choques`.
- **R-c · Orden asíncrono**: si se aplica antes de que lleguen las líneas, E sale corto; R18 lo
  impide y el aviso posterior lo recalcula (DA8).
- **R-d · Nómina procesada**: la línea queda enlazada y no se edita (DA9); cambios posteriores
  se regularizan a mano en Sigrid.
- **R-e · `porcentajes`**: no escribe `HE*` ni comparte esta synckey; no hay aviso que dar.
  `comprobar_asiento_analitico.py` contará el ajuste como línea nuestra (`partes:%`): correcto.
- **R-f · Despliegue**: sv5 → sv4 (sv4 nuevo con sv5 viejo: el bloque sale con el error de sv5
  y nada se escribe). Tamaño (DA20).

## 9. Tests (sin red ni BBDD; sintéticos, sin nombres ni DNIs)

sv5: `test_f056_franquicia.py` (fórmula y veredictos, R24–R30; propiedades: A ∈ [−X, 0],
E ≤ 0 ⇒ 0), `test_f056_pipeline.py` (R22–R33 con `SigridFake`: alta, edición, a 0 sin
`DELETE`, idempotencia, parte cerrado, enlazada, relectura, modo pruebas, lock compartido),
`test_f056_cliente.py` (SQL exacto de `extras_del_periodo`), `test_f056_choques.py` (R31 en
los dos `_choques` y en el preflight de registro), `test_f056_api.py`. sv4:
`test_f056_franquicia.py` (periodo, día con festivos, patrón y Sesame no fiable, obra y
desempates, candidatos, bloque), `test_f056_admin.py` (R2), `test_f056_decisiones.py` (R15–
R19 con SQLite de `dobles.py`, CAS con dos llamadas, 409 por `encolado`), `test_f056_vista.py`
(R20), `test_f056_orm.py`; `node --check`. Raíz: guardianes (R34) y contrato (R36). Cualquier
otro test existente que falle ⇒ `blocked`.

## 10. Verificación MANUAL (humano)

- **M1 · HECHA** (spec-author, 2026-10-23, solo lectura de `sql/read`; resultados en H5).
- **M2** (escritura, sv5 local con `OBRA_PRUEBAS_FORZAR=true`, recurso de pruebas de F-034, un
  mes sin partes de la 0404 y distinto de 10/2026; `ajuste_id` sintético ≥ 990560001):
  (a) registrar dos extras de 3 h en dos días del periodo; (b) `comprobar` con X = 8 ⇒ E = 6,
  A = −6, `crear`; (c) `ejecutar` ⇒ línea `HE*` −6 con `tex` `PRUEBA-IA` y synckey
  `partes:franquicia:990560001`; (d) repetir ⇒ `ya_aplicado`; (e) registrar otra extra de 4 h
  el día de ajuste ⇒ sin conflicto con el ajuste (R31); (f) `ejecutar` ⇒ E = 10, A = −8,
  `actualizar` (`UPDATE`, sin `DELETE` en la consola); (g) X = 0 ⇒ `can = 0`, `tot = 0`;
  (h) `prueba_escritura_sigrid.py limpiar`, `limpiar --ejecutar` y `verificar`.
- **M3** tras desplegar sv5 → sv4: `SELECT count(*) FROM franquicia_ajuste` ⇒ 0 y
  `SELECT count(*) FROM empleado_franquicia` ⇒ 0 (`PGOPTIONS='-c
  default_transaction_read_only=on'`).
- **M4** (producción, la decide y la hace el humano): alta de la primera franquicia real en la
  pantalla, aprobar su día de ajuste y comprobar en Sigrid la línea y su `tex`.
