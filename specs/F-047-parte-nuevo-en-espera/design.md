<!-- specs/F-047-parte-nuevo-en-espera/design.md -->
# F-047 · Parte nuevo «en espera» hasta que sv3 lo reparta — Diseño

## 1. Encaje, límite de servicio y rigor

- **sv3**: al guardar un parte nuevo escribe el «pedido» (id = el del
  documento) en la misma transacción y, tras conciliar, el «terminado» con el
  adaptador de F-043: es el único que sabe cuándo acaba ese reparto.
- **sv4**: deduce el motivo (`nuevo` o `recalculo`), pinta el listado, ajusta
  los textos y excluye de la aprobación los partes en espera. La guarda 409,
  las vistas y el sondeo de F-043 ya funcionan por estado y no cambian.
- **Sin lógica duplicada** (DA5): sv3 escribe y sv4 interpreta; la convención
  «pedido = id ⇒ parte nuevo» la vigila un test de contrato de la raíz (R25).
  La lista cerrada de `CLAUDE.md` **no crece**.
- **Rigor crítico**: worker de producción (`q-persistencia`), base `partes`
  del servidor compartido y una guarda nueva en la aprobación hacia Sigrid.

## 2. Esquema (`orm_models.py`, las dos copias)

**Sin columnas ni DDL nuevos** (DA4). Cambia solo, igual en las dos copias, el
comentario del bloque «Seguimiento del recalculo (F-043)»: el pedido lo escribe
sv4 (uuid4) **o sv3 al guardar un parte nuevo (F-047, mismo commit, `id` del
documento ⇒ motivo `nuevo`)**; los `# sv4` del pedido pasan a `# sv4 / sv3 (F-047)`.

## 3. sv3 (`services/partes-persistencia/`)

**`domain/ports/parte_repository.py`**: `save_parte(..., recalculo_pedido_id:
str | None = None)` (R9).

**`infrastructure/database/sqlalchemy_parte_repository.py`** (`save_parte`): con
`recalculo_pedido_id`, el `ParteDocumentOrm` nace con ese id y
`recalculo_pedido_at_utc` = `now_iso` (la hora de `created_at_utc`), en el mismo
`session.add` + `commit` (R1); sin él, NULL (R2). `_deactivate_same_day_obra` y
`get_by_sha256` **no cambian** (R3, R8).

**`application/pipelines/persist_parte_pipeline.py`**:

- `__init__` gana `recalculo_seguimiento: Any = None` (duck-typing:
  `.marcar_terminado(document_id, peticion_id) -> bool`), como los conciliadores.
- `run`: `seguido = self._recurso_conciliador is not None and
  self._recalculo_seguimiento is not None`; `save_parte(...,
  recalculo_pedido_id=document_id if seguido else None)` (R1, R2).
- `_conciliar_recursos_safely()` devuelve `bool` (True si `conciliar_todos` no
  lanzó; False sin conciliador o si lanzó, también la `TimeoutError` del candado
  de F-046), con sus WARNING/INFO de hoy. `_conciliar_partidas_safely` igual.
- Tras las dos conciliaciones: `if seguido and repartido:
  self._marcar_parte_nuevo(document_id)` (R4, R5).
- `_marcar_parte_nuevo(document_id)`: `marcar_terminado(document_id,
  document_id)` → INFO de R6; `except Exception` → WARNING `[persist-parte] no
  se pudo marcar el parte nuevo document_id=%s (%s): sv4 lo dara por
  vencido.` (`type(exc).__name__`), sin propagar (R6).
- Docstring del módulo: paso 7, «marca el parte nuevo como repartido (F-047)».

**`interface_adapters/api/app.py`**: crea `SqlAlchemyRecalculoSeguimiento(
session_factory)` **antes** de `PersistPartePipeline` y pasa esa instancia al
pipeline (`recalculo_seguimiento=`) y a `app.state.recalculo_seguimiento` (R10).

**`infrastructure/database/recalculo_seguimiento.py`**: solo el docstring del
módulo («el pedido lo escribe sv4 o, en un parte nuevo, la ingesta de sv3»);
el código no cambia. **Por qué es correcto (R7)**: la marca es el UPDATE
condicional **por pedido** (F-049 R41): con pedido = id solo toca ese parte; si
sv4 escribe otro pedido (recálculo o celda de F-049) durante la conciliación,
la ingesta no marca y lo marcará esa pasada. Sin relojes comparados.

## 4. sv4 · servidor (`services/partes-front/`)

**`application/services/seguimiento_recalculo.py`**: `MOTIVO_NUEVO = "nuevo"`,
`MOTIVO_RECALCULO = "recalculo"` y `motivo_espera(document_id: str | None,
pedido_id: str | None) -> str` (R11). `MOTIVO_RECALCULANDO` y
`RecalculandoError` **no cambian** (DA6).

**`infrastructure/database/parte_repository.py`** (`ParteReviewRepository`):

- `motivos_espera(ids: Iterable[str] | None) -> dict[str, str]` (R12): una
  `select` de `id`, `is_active` y las tres columnas de `estado_seguimiento`; con
  `ids`, `id IN ids` (ignora None y repetidos; vacío ⇒ `{}` sin consultar); con
  None, `is_active` y `recalculo_pedido_id IS NOT NULL AND (recalculo_terminado_id
  IS NULL OR recalculo_terminado_id != recalculo_pedido_id)`. Filtra en Python
  los activos `pendiente` (`_ahora_utc()`) y les pone `motivo_espera`.
- `approve_document`: en el `if doc is not None` que ya tiene (F-046),
  `_exigir_sin_recalculo(doc)` **después** de la comprobación de reparto y
  antes de `_set_approval` (R16). `unapprove_document` y `_set_approval` igual.
- `lineas_para_registro` (R17): constantes `EXCLUIDA_RECALCULANDO =
  "recalculando"` y `MOTIVO_EXCLUIDA_RECALCULANDO` (texto de R17); tras leer
  `regs`, `en_espera = set(self.motivos_espera({r.document_id for r in
  regs}))` (una consulta); en el bucle, **después** de `dedicacion` y de
  `reparto_pendiente` (F-046) y **antes** de la incompatibilidad, una línea de
  `en_espera` suma en `excluidas[EXCLUIDA_RECALCULANDO]` (`get(…, 0) + 1`), va
  al detalle con ese motivo y no viaja.
- `documentos_en_espera`, `estados_recalculo` y `_exigir_sin_recalculo` **no
  cambian**: la guarda 409 ya cubre al parte nuevo por estado (R15).

**`interface_adapters/web/app.py`**:

- `obra_detail`, `trabajador_detail`, `parte_detail`: sacan `recalculando`
  (hoy dentro del dict) a una variable y añaden `nuevos = {d for d, m in
  repository.motivos_espera(recalculando).items() if m == MOTIVO_NUEVO} if
  recalculando else set()` (R13); sin espera, ni una consulta más.
- `partes_list`: `espera = repository.motivos_espera(None)`; `recalculando =
  set(espera)` y `nuevos` al contexto (R14).
- Ruta `approve_document`: su `except RepartoPendienteError` (F-046) pasa a
  `except CongeladoError as exc: return _redirect(back, exc.motivo)` (cubre
  las dos guardas), como `unapprove_document`. `_actor(request)` sigue en 20.
- `_motivo_sin_lineas`: «N en espera de reparto (pulsa Actualizar cuando
  termine)» si `excluidas.get("recalculando")` (R17).

## 5. sv4 · portal

**Plantillas**: en `obra_detail.html`, `trabajador_detail.html` y `parte_detail.html`,
junto al `data-recalculando="1"` actual, `data-recalculo-motivo="nuevo"` si
`document_id in nuevos` y la marca `procesando…` (no `recalculando…`) (R13).
`parte_detail.html`: `data-parte-acciones data-document-id="…"` en
`.action-bar` (R18). `partes_list.html`: el `<tr>` gana `data-document-id`,
`data-fecha="{{ p.fecha or '' }}"` y, en espera, `data-recalculando="1"` (+
motivo) y la marca en la celda de estado (R14).

**`static/app.js`**. **Restricción dura**: los tests de F-042/F-043 montan un
programa node con una lista **fija** de funciones (`F043_ESPERA`, `ESPERA`) y
con las líneas `^  var (RECALCULO_|VISTA_|recalculo)\w* = `. Por eso: **ninguna
función nueva** en esa cadena; el estado nuevo, en **una sola línea** `var
recalculoMotivos = {};`; todo lo demás dentro de las funciones existentes.

- `textoAvisoRecalculo(tipo, fecha, motivo)`: con `motivo === "nuevo"`, los
  textos de R19–R21 (`terminado`: «Parte nuevo del D procesado: horas
  repartidas.»); en otro caso, los de F-043 sin tocar una coma.
- `avisoRecalculo(docId, tipo, fecha)`: misma firma; pasa `recalculoMotivos[docId]`.
- `ponerEnEspera(docId, motivo)`: `recalculoMotivos[docId] = motivo || ""`;
  marca «procesando…» si `nuevo`, si no «recalculando…». `wireFechaInput` la
  sigue llamando sin motivo: un cambio de fecha sobre un parte nuevo pasa a
  `recalculo` (R22).
- `contenedoresEspera(docId)`: el selector gana
  `[data-parte-acciones][data-document-id="…"]` (R18); `marcarEspera` ya sale
  sin hacer nada si no hay `td` ni `.fecha-edit`.
- `aplicarEstadoRecalculo`: en `terminado`, «procesado · pulsa Actualizar» si `nuevo` (R20).
- `esperasDeLaPagina`: lee `data-recalculo-motivo` del primer contenedor de
  cada documento y llama a `ponerEnEspera(docId, motivo)` (R19).
- **No cambian**: `soltarEspera`, `vigilarRecalculo`, `sondearRecalculo`,
  `actualizarVista`, `restaurarVista`, `accionPorEstado`, `estadoRecalculo`,
  `wireUndo` (R23); F-064 fija la huella de `restaurarVista` y
  `actualizarVista`. **`styles.css`** tampoco (marca y fila atenuada existen).

## 6. Tests (sin red ni BBDD real; datos sintéticos)

- `services/partes-persistencia/tests/test_f047_parte_nuevo_sv3.py`: pipeline
  con dobles (repositorio que guarda los kwargs; conciliadores y seguimiento que
  apuntan eventos) para R1–R6 y el orden `save → partidas → recurso → marcar`;
  `save_parte` real sobre la `fabrica` SQLite de F-043 (R1, R8, y R7 con un pedido
  escrito entre guardado y marca); R10 como `test_f043_r33_build_app_…`.
- `services/partes-front/tests/test_f047_parte_nuevo_sv4.py`
  (`FabricaSesionSqlite` y `sembrar_parte` de `tests/dobles.py`; ayudantes de
  `test_f043_alcance_y_seguimiento`): R11–R12 con reloj fijo y borde de 600 s;
  R13–R14 sobre el HTML (parte nuevo «procesando…», otro de F-043, otro sin espera);
  R15 en dos métodos; R16 (redirige con el motivo y `approved` sigue False);
  R17 (claves exactas con y sin espera); R18 (barra y dos `data-parte-contenido`).
- `…/tests/test_f047_portal_parte_nuevo.py`: R19–R23 con node (doble de DOM y
  extractores de `test_f043_portal_fecha`; `skipif` sin node).
- `tests/test_f047_contrato_parte_nuevo.py` (raíz): R24 (copias idénticas, las
  4 columnas de F-043 y ninguna más con prefijo `recalculo`) y R25 por AST.

## 7. Ficheros que NO se tocan

sv3: `despacho.py`, `mensajes.py`, `main_worker.py`, `recurso_conciliador.py`,
`partida_conciliador.py`, `pareja_extra.py` y el código de
`recalculo_seguimiento.py`. sv4: `congelacion.py`, `recalculo_publisher.py`,
`update_parte_fecha`, `undo_last`, `_DOC_UNDO_FIELDS`, `estados_recalculo`,
`documentos_en_espera`, `GET /api/recalculo` (ni claves nuevas) y
`styles.css`. sv1, sv2, sv5; `infra/`; `CLAUDE.md`. **Todos los tests
existentes** (uno roto ⇒ `blocked`, DA8).

## 8. Despliegue

Sin variables, roles, infra ni DDL nuevos. **Orden sv4 → sv3** (con sv3 antes,
espera con textos de F-043 y sin la exclusión de la aprobación).
`azure-apps/partes.md`: commit local en ese repositorio.

## 9. Riesgos y alternativas

- **R-a · Espera más larga**: la marca nace al guardar (tras el arranque en
  frío, SharePoint y hasta 300 s de candado, DA13); a los 10 min vence.
- **R-b · Caída entre guardado y marca**: la reentrega cae en el dedup, que no
  concilia; vence a los 10 min. **Pasa ya hoy**; F-047 lo hace visible (DA9).
  **R-c**: partes encadenados, cada uno se marca con su propia pasada.
- **R-d · Acciones masivas** (`/conciliacion`, reasignar, borrar por
  obra/persona) no miran la espera: hueco heredado de F-043 R-g (DA7).
- **R-e · Merge** con F-057 (`spec_ready`: pedido del editor de celda) y lo
  que entre antes en `app.js`, `parte_repository.py` o el pipeline.
- **Descartadas**: HTTP o mensaje sv3→sv4 (la base ya es el canal); UPDATE tras
  guardar (ventana sin marca); columna de motivo (DA4); recargar sola.

## 10. Verificación MANUAL (humano; solo lectura salvo el despliegue)

M1 (portal), M2 (SQL de la base `partes`) y M3 (Log Analytics de sv3, que
además vuelve a medir la espera): detalle y comandos en `tasks.md` T13.

## 11. Decisiones abiertas (cada una con su recomendación)

DA1–DA10 aprobadas el 2026-10-14; **DA11–DA13 = A** decididas por el humano el
2026-10-30 (literal: «ok» a «F-047: A, A, A»; contexto en
`progress/explore_F-047_revalidacion.md`).

- **DA1 · Quién genera el pedido y dónde se marca.** **A (recomendada)**: el
  pipeline usa como pedido el `document_id` que ya genera (uuid4, 36
  caracteres) y `save_parte` lo escribe en el mismo commit: ninguna ventana
  sin marca y el motivo se deduce sin columna. B: un uuid4 aparte (no
  distingue el motivo sin columna). C: UPDATE tras el guardado (ventana sin
  marca). Reingestas: un sha256 repetido no guarda ni marca; el documento que
  se desactiva por reemplazo sale `no_existe` y el portal lo suelta.
- **DA2 · Si la conciliación de la ingesta falla, no se marca y NO se propaga
  (recomendada)**, al contrario que F-042 R15/F-043 R29: allí la pasada era
  el trabajo del mensaje; aquí el trabajo es guardar, y propagar haría que la
  reentrega cayera en el dedup sin conciliar (mismo resultado, 5 min después,
  con ruido y riesgo de poison). El parte vence a los 10 min con el aviso de
  R21. El fallo de **partidas** no impide la marca (lo que se espera es el
  reparto de horas; recargar no lo arregla). Alternativa: exigir las dos.
- **DA3 · La aprobación excluye los partes en espera de los dos motivos
  (recomendada; revisa F-043 DA12)**: sv3 no reparte lo aprobado ni lo
  encolado, así que aprobar en la espera deja las horas sin repartir para
  siempre. Solo sv4: el payload hacia sv5 no cambia. Alternativas: B, solo los
  partes nuevos; C, no bloquear (como F-043).
- **DA4 · Sin columnas nuevas (recomendada)**: motivo = «pedido = id»,
  documentado en `orm_models.py`. Alternativa: columna `recalculo_motivo`.
- **DA5 · La lista cerrada de `CLAUDE.md` no crece (recomendada)**: sv3
  escribe la convención, solo sv4 la interpreta; la vigila un test de contrato.
- **DA6 · Textos distintos para el parte nuevo** (marca y tarjeta, R19–R21;
  el humano puede reescribirlos). El **409 mantiene** el texto de F-043, que
  fija un test de F-043 y vale para los dos motivos.
- **DA7 · Dónde se ve el aviso**: obra, trabajador y detalle (ya los pinta
  F-043) y el listado `/partes` con marca y sondeo (R14), porque enseña las
  horas sin repartir. **Fuera (recomendado)**: `/obras`, `/trabajadores`
  (agregadas) y `/conciliacion` (acciones masivas, R-d; feature aparte).
- **DA8 · Tests existentes: no cambia ninguno**. Lo garantizan el JS de §5
  (respeta los extractores), que las vistas sigan llamando una vez a
  `documentos_en_espera` y que la marca de F-043 quede idéntica para el
  motivo `recalculo`. `test_f017_punto_unico` sigue con 20 `_actor(request)`.
  El comentario de `test_f043_r35_…` («sv3 nunca escribe el pedido») habla del
  adaptador, que sigue sin escribirlo: pasa y no se toca.
- **DA9 · Reentrega tras caída entre guardado y marca: fuera (recomendado)**.
  Alternativa: que el dedup vuelva a conciliar y marque un existente con su
  pedido sin terminar (toca el dedup de producción por un caso que ya existe).
- **DA10 · Botones del detalle** (fuera de `[data-parte-contenido]`).
  **Recomendado**: `data-parte-acciones` + `contenedoresEspera`, además de la
  guarda del servidor (R16). Alternativa: solo el servidor (motivo por redirección).
- **DA11 · Matriz de la obra (F-049)**: la celda en espera enseña lo sin repartir
  y el editor se abre (guardar da 409). **A (elegida)**: fuera, como DA7.
- **DA12 · Sin obra o sin fecha (F-054)**: también esperaría (fecha editable,
  obra con 409). **A (elegida)**: misma regla para todos. B: sin pedido si
  `motivos_cabecera(parte)` no está vacía (R1–R2 ganan esa condición).
- **DA13 · Candado de F-046**: la pasada lo espera hasta 300 s; sin él, sin
  marca (R5) y vence a los 600 s. **A (elegida, aplicada a R19)**: R19 dice «(suele tardar menos
  de 1 min; con más partes en cola, unos minutos)». B: R19 tal cual.
