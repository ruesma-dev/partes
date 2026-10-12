<!-- specs/F-043-fecha-del-parte-confirmar-y-recargar/design.md -->
# F-043 · Fecha del parte: rótulo, confirmación y recarga — Diseño

## 1. Encaje, límite de servicio y rigor

- **sv4** (portal): rótulo, alcance, confirmación, marca de «pedido», endpoint
  de estado, sondeo y recarga. **sv3**: solo deja la marca de «terminado» tras
  la pasada que ya hace (F-042). El reparto sigue siendo exclusivo de sv3; sv4
  no recalcula nada. sv1, sv2 y sv5 no cambian.
- **Sin lógica duplicada**: sv4 escribe el pedido y decide el estado; sv3 copia
  el pedido que leyó a «terminado». Son dos mitades de un protocolo sobre la
  base compartida, como `sigrid_estado`; la lista cerrada de `CLAUDE.md` no
  crece. La única copia es la de siempre: `orm_models.py` (sv3 y sv4).
- **Contrato de mensaje intacto**: no se añade `peticion_id` al mensaje (DA2).
- **Rigor crítico**: toca el worker de producción de `q-persistencia`, el esquema
  de la base `partes` (servidor compartido, DDL al arrancar) y la puerta por la
  que un parte cambia de día. `estandar` bastaría para el JS (la mutación del
  arnés es solo Python), pero no para el handler de sv3 ni el DDL.

## 2. Esquema (`orm_models.py`, las dos copias, byte-idénticas)

En `ParteDocumentOrm`, tras el bloque «Dia del parte», un bloque «Seguimiento
del recalculo (F-043)» con comentario de quién escribe cada columna:

```python
recalculo_pedido_id: Mapped[str | None] = mapped_column(String(36))        # sv4
recalculo_pedido_at_utc: Mapped[str | None] = mapped_column(String(64))    # sv4
recalculo_terminado_id: Mapped[str | None] = mapped_column(String(36))     # sv3
recalculo_terminado_at_utc: Mapped[str | None] = mapped_column(String(64)) # sv3
```

Nullables, sin índice (se leen por PK); las genera `ddl_complementario()`, sin
SQL a mano. Los guardianes de F-010/F-015 no listan las columnas de
`parte_documents`: ninguno cambia. Tabla nueva descartada (DA1-B).

## 3. sv4 · servidor (`services/partes-front/`)

**Crear** `application/services/seguimiento_recalculo.py` (sin dependencias):
`ESTADO_PENDIENTE`, `ESTADO_TERMINADO`, `ESTADO_SIN_SEGUIMIENTO` y
`estado_seguimiento(pedido_id: str | None, terminado_id: str | None) -> str`
(glosario). Única definición de «pendiente».

**Modificar** `infrastructure/database/parte_repository.py`
(`ParteReviewRepository`), cuatro métodos nuevos, nada más:

- `alcance_parte(document_id) -> dict | None` — `{document_id, fecha,
  trabajadores, lineas}`; None si no existe o `is_active` es falso. Reutiliza
  `worker_key_for_registro`. Solo lectura (R2–R4).
- `marcar_recalculo_pedido(document_id, *, peticion_id: str, ahora_utc: str)
  -> bool` — UPDATE de las dos columnas de sv4 con commit; False si no existe.
  Sin guarda de congelación (no es edición de usuario) y sin `undo_log`.
- `anular_recalculo_pedido(document_id, *, peticion_id: str) -> None` — pone a
  NULL las dos columnas de sv4 `WHERE recalculo_pedido_id = :peticion_id` (R13).
- `estado_recalculo(document_id) -> dict | None` — `{estado, pedido_at_utc,
  terminado_at_utc}` con `estado_seguimiento`; None si no existe (R17).

`_DOC_UNDO_FIELDS` y `update_parte_fecha` **no cambian** (R34).

**Modificar** `interface_adapters/web/app.py`:

- Closure `_pedir_recalculo_seguido(document_id, motivo, solicitado_por) -> str`
  dentro de `build_app`: con `recalculo_publisher` no nulo, `pid =
  str(uuid4())` y `repository.marcar_recalculo_pedido(...)` (excepción ⇒
  WARNING `[recalculo] no se pudo marcar … document_id=%s (%s)` y sin marca);
  luego `pedir_recalculo(...)` de F-042 sin cambios; si devuelve `fallo` y hubo
  marca, `anular_recalculo_pedido` (excepción ⇒ WARNING). Devuelve el estado de
  F-042 (R12–R16).
- `patch_parte_fecha` y `undo_apply` llaman a `_pedir_recalculo_seguido` en vez
  de a `pedir_recalculo`, con el mismo `solicitado_por` que ya calculan: el
  recuento de `_actor(request)` sigue en **17**
  (`test_f017_punto_unico.py`). Respuestas sin claves nuevas (R16).
- `GET /api/partes/{document_id}/alcance` y `GET /api/partes/{document_id}/
  recalculo` (`include_in_schema=False`): 404 con `None`; `{"ok": True, ...}`.

## 4. sv4 · portal (`static/app.js`, plantillas, `static/styles.css`)

**Plantillas** (R1): `obra_detail.html` y `trabajador_detail.html` — `<th title="…">Fecha
del parte</th>` y `title`/`aria-label` en el `.fecha-edit`; `parte_detail.html`, en `#fechaEdit`.

**`app.js`**, en el IIFE principal (el de `wireFechaInput` y `wireUndo`), con
funciones puras a dos espacios de sangría (así las extrae y ejecuta con node el
test, como `empresaSufijo` en F-039):

- Constantes `RECALCULO_SONDEO_MS = 5000`, `RECALCULO_MAX_MS = 300000`,
  `RECALCULO_CLAVE = "partes.recalculo.espera"`.
- `fmtFechaEs(iso)` ⇒ `dd/mm/aaaa` (o el texto tal cual si no es ISO).
- `textoConfirmacionFecha(alcance, vieja, nueva)` ⇒ textos de R6/R7.
- `decisionEspera(estados, transcurridoMs, editando)` ⇒ `"desaparecido"` si
  algún estado es `no_existe`; `"sin_seguimiento"` si alguno lo es;
  `"recargar"`/`"ofrecer"` (según `editando`) si todos son `terminado`;
  `"agotado"` si `transcurridoMs >= RECALCULO_MAX_MS`; si no, `"seguir"`. Un
  `error` cuenta como `pendiente` (R19–R23).
- `esperaReanudable(guardado, ahoraMs, idsEnPagina)` ⇒ `{ids, desde}` o `null`
  (R25: objeto válido, no vencido, algún id en la página).
- `estaEditando()` (glosario; no pura) y `avisoRecalculo(texto, clase, boton)`:
  crea o reutiliza `#recalculo-aviso` (`role="status"`, al final de `body`).
- `esperarRecalculo(ids, desde)`: guarda la espera (try/catch), pinta R18,
  sondea `GET /api/partes/{id}/recalculo` de cada id cada
  `RECALCULO_SONDEO_MS` (404 ⇒ `no_existe`; red/5xx ⇒ `error`) y aplica
  `decisionEspera`; al acabar borra la espera, salvo en `ofrecer`, que sigue.
  **Punto de entrada para F-044.**
- `reanudarRecalculo()` en `DOMContentLoaded`: lee la espera (try/catch),
  `esperaReanudable` con los `[data-document-id]` de la página y, si procede,
  `esperarRecalculo`.
- `wireFechaInput` reescrito: `guardada` = valor inicial (también en
  `data-fecha-guardada`); disparo de R5 con bandera `ocupado` (R11);
  `fetch(alcance)` ⇒ `confirm(textoConfirmacionFecha(...))`; cancelar ⇒ valor
  guardado (R8); PATCH como hoy; éxito ⇒ nueva `guardada` en él y en hermanos
  (R10), `estadoRecalculo` de F-042 en `data-status` y, con `pedido`,
  `esperarRecalculo([docId], Date.now())`; con `fallo`, `avisoRecalculo` fijo
  (R24); error ⇒ valor guardado + motivo (R9).
- `wireUndo`: con `res.ok`, `res.recalculo === "pedido"` y `res.document_ids`,
  guarda la espera antes del `reload` (R26). El `alert` de `fallo` sigue.
- `estadoRecalculo` y sus textos **no cambian** (los vigila F-042 R11).
- **`styles.css`**: `.recalculo-aviso` (fija abajo a la derecha, tokens de `.alert`, `info`/`error`).

## 5. sv3 (`services/partes-persistencia/`)

**Crear** `infrastructure/database/recalculo_seguimiento.py`:
`SqlAlchemyRecalculoSeguimiento(session_factory, reloj=<utc now ISO>)` con
`pedido_actual(document_id) -> str | None` (SELECT por PK; None si no existe)
y `marcar_terminado(document_id, peticion_id) -> bool` (`UPDATE parte_documents
SET recalculo_terminado_id = :pid, recalculo_terminado_at_utc = :ahora WHERE id
= :doc AND recalculo_pedido_id = :pid`; True si tocó una fila). Aparte del
repositorio grande, como `SqlAlchemyJornadaRepository`.

**Modificar**

- `interface_adapters/workers/despacho.py`: `construir_handler(...,
  recalculo_seguimiento: Any = None)`. En `_recalcular`, tras la guarda de
  R17 de F-042: `pedido = _leer_pedido(...)` (None sin seguimiento, sin
  `document_id` de texto o si lanza, con WARNING); `res =
  conciliar_todos()` **sin try** (F-042 R15); INFO de siempre; si `pedido`,
  `_marcar(...)` (WARNING si lanza; INFO `[sv3-worker] recalculo terminado
  document_id=%s marcado=%s`). Docstring: el seguimiento.
- `interface_adapters/api/app.py`: `app.state.recalculo_seguimiento =
  SqlAlchemyRecalculoSeguimiento(session_factory)` junto a F-042 (R33).
- `main_worker.py`: `recalculo_seguimiento=app.state.recalculo_seguimiento`.

**Por qué es correcto (R32)**: sv4 confirma el pedido antes de publicar; sv3 lo
lee antes de la pasada, así que la pasada (READ COMMITTED, sesiones nuevas) ve
la fecha nueva. Si entra un pedido más nuevo, el UPDATE condicional no lo pisa
y queda pendiente hasta su mensaje. Desorden o reentrega: cada mensaje solo
marca lo que leyó antes de su pasada. Sin relojes comparados.

## 6. Tests (sin red ni BBDD real; datos sintéticos)

- `services/partes-front/tests/test_f043_alcance_y_seguimiento.py` —
  `build_app` sobre `FabricaSesionSqlite` y la `ColaFake` de F-042 (importada
  de `tests.test_f042_recalculo_fecha`): R2–R4, R12–R17 (R12 con una cola que,
  al enviar, lee la marca desde otra sesión; R14 con un repositorio que lanza;
  R16 compara claves con F-042), `estado_seguimiento` y el recuento de
  `_actor(request)`.
- `services/partes-front/tests/test_f043_portal_fecha.py` — R1 (Jinja parse +
  atributos), R5–R11 y R18–R26: funciones puras **ejecutadas con node**
  (patrón de `test_f039_nombre_empresa.py`, `skipif` sin node) y el cableado
  leído de `app.js` (URLs, `window.confirm` en `wireFechaInput`,
  `RECALCULO_CLAVE` en `wireUndo`, `reanudarRecalculo` en `DOMContentLoaded`,
  textos de F-042 intactos) + `node --check`.
- `services/partes-persistencia/tests/test_f043_seguimiento_sv3.py` —
  adaptador sobre `FabricaSesionSqlite`: marca solo con el pedido vigente
  (R28, R32) e idempotencia; handler con dobles que anotan el orden (lectura
  antes de la pasada, R27; sin marca si la pasada lanza, R29; WARNING y sin
  relanzar, R30; F-042 intacto sin seguimiento, R31); R33 por AST como F-042.
- `tests/test_f043_contrato_seguimiento.py` (raíz) — R35 por AST/texto: las 4
  columnas nullables en las dos copias, los nombres en el adaptador de sv3 y en
  el repositorio de sv4, `_DOC_UNDO_FIELDS` sin ellas, y el `mensaje_recalculo`
  de F-042 sin claves nuevas.

## 7. Ficheros que NO se tocan

`update_parte_fecha`, `undo_last`, `_DOC_UNDO_FIELDS` y las guardas de
congelación de sv4; `recalculo_publisher.py` (sv4) y `mensajes.py` (sv3): el
contrato de F-042 no cambia; `recurso_conciliador.py`, `pareja_extra.py` y
`sqlalchemy_parte_repository.py` de sv3; `congelacion.py`, `cola_cliente.py`
(las dos), `main.py` de sv4; `services/partes-api/`, `partes-transfer/`,
`partes-email/`; `infra/`; `CLAUDE.md`; **todos los tests existentes** (si uno
se rompe ⇒ `blocked`, sin enmiendas previstas: R16 existe para que los de
F-042 sigan pasando tal cual).

## 8. Despliegue

- Sin variables, roles ni infra nuevos; las columnas las crea el DDL de arranque.
- **Orden sv3 → sv4** (el de siempre). Con sv4 antes, un sv3 viejo no marca y
  el portal agota los 5 min con el aviso de R21: inútil, pero inocuo.
- `azure-apps/partes.md` (§4.1 y nota F-042): commit local en ese repositorio.

## 9. Riesgos y alternativas

- **R-a · Recarga con trabajo a medias**: la evita «editando» (R20); el portal
  guarda cada campo al cambiarlo, así que sin foco no hay nada a medias.
- **R-b · Marca de sv4 fallida con un pedido viejo ya terminado**: el estado
  dice `terminado` y recarga antes de tiempo. Exige un UPDATE fallido justo
  tras el commit de la fecha; queda el WARNING.
- **R-c · Pasada parcial**: si Sigrid falla a mitad, `conciliar_todos` salta la
  obra sin error y sv3 marca igual; es lo de hoy (F-042 §8 R-d).
- **R-d · Reintento de sv3**: un recálculo fallido reaparece a los 300 s
  (`COLA_VISIBILITY_S`): pasa los 5 min y el portal muestra R21.
- **R-e · `change` al teclear**: los Chromium disparan `change` en cada segmento
  válido; de ahí DA3. Verificación M2.
- **R-f · Choques de merge con F-044** (`app.js`, plantillas,
  `features.json`, `current.md`): mejor integrar F-043 antes.
- **Descartadas**: sv4 llama a sv3 por HTTP (en Azure es solo worker); DA1-B/C/D.

## 10. Punto de contacto con F-044 (mover una sola línea)

F-044 **no** cambia `.fecha-edit` (sigue siendo la fecha del parte) y añade su
acción aparte. Reutiliza: `_pedir_recalculo_seguido` por cada documento
afectado, `esperarRecalculo(ids, Date.now())` en el portal (varios ids ya
soportados), `fmtFechaEs` y el idioma `window.confirm`, y
`GET /api/partes/{id}/alcance` si necesita contar.

## 11. Verificación MANUAL (humano; solo lectura salvo el despliegue)

- **M1 · tras desplegar sv3 y luego sv4**: `SELECT column_name FROM information_schema.columns
  WHERE table_name = 'parte_documents' AND column_name LIKE 'recalculo%';` ⇒ 4 filas.
- **M2 · portal (Chrome/Edge)**, un parte sin congelar, vista de obra: teclear
  la fecha no abre un diálogo por tecla; al salir del campo sale el texto con
  sus N trabajadores; Cancelar deja la fecha vieja; Aceptar ⇒ aviso y, a los
  1–2 min, recarga sola con el reparto nuevo. Igual en detalle del parte.
- **M3 · base `partes`**: `SELECT recalculo_pedido_id, recalculo_pedido_at_utc,
  recalculo_terminado_id, recalculo_terminado_at_utc FROM parte_documents WHERE
  id = '<id>';` ⇒ ids iguales y la diferencia de horas = lo que tardó sv3.
- **M4 · deshacer** ese cambio ⇒ tras recargar, el aviso sigue y vuelve a
  recargar al terminar.

## 12. Decisiones abiertas (con recomendación)

- **DA1 · Cómo sabe sv4 que sv3 terminó.** A) marca en `parte_documents`,
  sondeada por un GET ligero (**recomendada**); B) tabla nueva (7.ª tabla:
  enmendar los guardianes de F-010/F-015); C) longitud aproximada de la cola
  (sin cambios en sv3 ni esquema, pero cuenta mensajes de otros partes y la
  poison parece éxito); D) recarga a los 90 s (sin garantía).
- **DA2 · sv3 marca el pedido que leyó antes de la pasada**, no un id que viaje
  en el mensaje (**recomendada**): el id en el mensaje obligaría a enmendar
  `test_f042_r1` (mensaje exacto) y el `PublisherSelectivo` de F-042.
- **DA3 · Disparo**: `change` sin foco, `blur` o Enter (**recomendada**) frente
  a `change` siempre (un diálogo por tecla al escribir la fecha).
- **DA4 · Confirmar también en el detalle del parte** (**recomendada**: mueve
  a todos igual); alternativa, solo en las filas.
- **DA5 · Rótulo**: cabecera «Fecha del parte» + `title` + `aria-label`
  (**recomendada**); alternativas, solo `title`, o cambiar el input de la fila
  por un botón «Cambiar fecha del parte…».
- **DA6 · Recarga automática** salvo «editando» (botón); sondeo 5 s, plazo 5 min (**recomendada**).
- **DA7 · Si sv3 no puede marcar**, WARNING y mensaje consumido (**recomendada**);
  relanzar repetiría la pasada entera por una marca de UI.
- **DA8 · Deshacer también espera y recarga** vía `sessionStorage`
  (**recomendada**); alternativa, solo el `alert` de F-042.
- **DA9 · Tras un error del PATCH, el input vuelve a la fecha guardada**
  (**recomendada**; hoy se queda con la que no se guardó).
