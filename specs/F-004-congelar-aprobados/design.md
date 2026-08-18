<!-- specs/F-004-congelar-aprobados/design.md -->
# F-004 · Congelar registros aprobados — Diseño técnico

## Límite de servicio

Toca **solo sv4** (`services/partes-front`). Justificación:

- sv5 no necesita nada: su idempotencia por synckey
  (`partes:{registro_id}`, `sigrid_write_client.synckey_de`) ya impide
  duplicar al reaprobar, y es justo lo que hace necesaria la congelación
  aquí (ver «Hechos del código» abajo).
- sv3 no edita líneas existentes aprobadas: crea líneas en la ingesta y
  escribe columnas de conciliación de líneas nuevas. Fuera de alcance.
- `azure-apps/partes.md` NO cambia: los endpoints tocados son APIs
  internas del portal consumidas solo por su propio JS; el contrato
  sv4↔sv5 y lo expuesto/consumido entre proyectos no varía.

## Hechos del código que condicionan el diseño

1. **La aprobación es a nivel de DOCUMENTO.** Solo
   `parte_documents.approved/approved_by/approved_at_utc` existe en el ORM
   de sv4 (y en el de sv3). `partes-proyecto.md` §5.2 lista `approved*`
   también en `parte_registros`, pero NINGUNA de las dos copias de
   `orm_models.py` la tiene: discrepancia de documentación a resolver en
   F-010, no aquí. La granularidad por línea nos la da gratis
   `sigrid_estado`.
2. **Editar una línea `registrado` no se arregla reaprobando.** El
   synckey es estable por `registro_id`: al reaprobar, sv5 la marca
   `ya_registrado («no se duplica»)` y NO actualiza valores en Sigrid
   (paso 6 de `registro_pipeline._evaluar`). Una edición local de una
   línea registrada desincroniza para siempre salvo intervención en
   Sigrid. Por eso `registrado` congela DURO, y desaprobar el documento
   no lo levanta.
3. **`encolado` = petición en vuelo**: sv5 leerá esas líneas de la BBDD…
   no: sv5 recibe el payload por blob, pero el RESULTADO volverá y pisará
   `sigrid_*`; además la línea puede quedar `registrado` segundos después
   de una edición local ya divergente. Carrera real → congela duro y
   además bloquea la desaprobación (R10).
4. **`omitido`/`error`/`conflicto` NO están en Sigrid** y editarlas es
   precisamente el camino de arreglo (asignar código de hora a una
   omitida, corregir datos de un error, resolver un conflicto). Editables
   si el documento no está aprobado.
5. Los flags necesarios ya viajan a las plantillas: `RegistroView` lleva
   `parte_aprobado` y `sigrid_estado`; la matriz lleva `regs` como JSON
   por celda (`get_obra`/vista trabajador en `parte_repository.py`).

## Ficheros a crear

| Ruta | Contenido |
|---|---|
| `services/partes-front/application/services/congelacion.py` | La regla (capa application, pura, sin BBDD ni FastAPI): `motivo_congelacion_linea(*, doc_aprobado: bool, sigrid_estado: str \| None) -> str \| None`; `motivo_congelacion_documento(*, aprobado: bool, estados_lineas: Iterable[str \| None]) -> str \| None`; constantes `ESTADOS_CONGELANTES = ("encolado", "registrado")`; excepción `CongeladoError(Exception)` con atributo `motivo`. |
| `services/partes-front/tests/test_f004_congelacion_reglas.py` | Matriz de R1/R2 contra las funciones puras. |
| `services/partes-front/tests/test_f004_endpoints_congelados.py` | R3–R13 vía `TestClient` + SQLite en memoria. |
| `services/partes-front/tests/test_f004_vistas_candado.py` | R14/R15/R17 sobre el HTML renderizado. |

## Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `services/partes-front/infrastructure/database/parte_repository.py` | (a) Guardas: `update_registro`, `set_registro_hora`, `set_registro_partida`, `soft_delete_registro`, `crear_extra_desde`, `update_parte_fecha`, `update_parte_obra`, `delete_document`, `unapprove_document` lanzan `CongeladoError` según R1/R2/R10 (leyendo `reg.document.approved` / estados de líneas en la misma sesión). (b) `backfill_empleado` y los tres `reassign_empleado_*` filtran congeladas de `affected` y devuelven además el nº excluido. (c) `undo_last` omite snapshots de registros/documentos hoy congelados y devuelve `omitidos`. (d) `hard_delete_registro`/`hard_delete_document` lanzan `CongeladoError` si hay línea `registrado`; `vaciar_papelera`, `soft_delete_obra` y `soft_delete_worker` omiten y devuelven recuento. (e) `_registro_view` añade `congelado: bool` y `congelado_motivo: str \| None` a `RegistroView` (misma función de decisión); los dicts `regs` de la matriz añaden `"c": 1` si congelada. `ParteDetail` gana `congelado_doc: str \| None` (motivo de R2) para parte_detail. |
| `services/partes-front/interface_adapters/web/app.py` | `@app.exception_handler(CongeladoError)` → 409 `{ok: false, congelado: true, error: motivo}` para las APIs JSON. Los dos flujos de formulario (`/documents/{id}/delete`, `/documents/{id}/unapprove`) capturan `CongeladoError` explícitamente y redirigen con el motivo como `message` (R7/R10). `/api/empleado/reasignar` y `/api/conciliacion/confirmar` propagan `congeladas` en la respuesta. `/api/undo` propaga `omitidos`. |
| `services/partes-front/templates/parte_detail.html` | Banner si `parte.approved` (R17); `disabled` en fecha/obra/horas/combos; ocultar `line-del` y «+ Añadir línea»; candado por línea congelada. |
| `services/partes-front/templates/obra_detail.html` | Candado + `disabled` + sin aspa en filas con `r.congelado` (tooltip `r.congelado_motivo`); la celda de la matriz no cambia de HTML (el flag va en `regs`). |
| `services/partes-front/templates/trabajador_detail.html` | Ídem obra_detail (tabla de líneas y matriz). |
| `services/partes-front/static/app.js` | (a) No cablear editores sobre inputs `disabled`/filas congeladas. (b) En el popup de celda de la matriz, filas con `r.c` se pintan solo-lectura; si todas congeladas, sin botón Guardar ni fila «Extra» nueva (R15). (c) Los manejadores de error de `wireHorasInput`, `wireFechaInput`, combos y `line-del` leen el cuerpo del 409 y muestran `error` (tooltip/`setStatus`/alert) en vez del genérico (R16). |
| `services/partes-front/static/styles.css` | Estilo mínimo del candado/fila congelada (si hace falta más que `disabled`). |

## Ficheros que NO se tocan (y podrían tentar)

- `infrastructure/database/orm_models.py` — **ni la copia de sv4 ni la de
  sv3**: sin cambios de schema (decisión 4 más abajo). La resincronización
  es F-010.
- `services/partes-persistencia/**` y `services/partes-transfer/**`.
- `infrastructure/transfer/resultado_sigrid.py` y
  `marcar_registros_encolado`/`marcar_registros_sigrid`: son escrituras
  del SISTEMA (traza del registro), no ediciones de usuario; la guarda no
  se les aplica jamás (bloquearlas rompería R18).
- Endpoints de aprobación/registro (`/api/aprobar/*`), reencolado poison,
  `restore_registro`/`restore_document` (restaurar de papelera no es
  editar contenido congelado), `crear_parte_manual`, `approve_document`.
- `harness/`, `infra/`, `CHECKPOINTS.md`.

## Decisiones (con alternativas descartadas)

### D1 · Qué estados congelan — la matriz de R1

`approved` (doc), `encolado` y `registrado` congelan; `omitido`, `error`,
`conflicto` y NULL no. Razones en «Hechos» 2–4.
**Descartado**: congelar también `conflicto`/`error` — impediría el flujo
natural de arreglo (editar y reintentar), que hoy es la única salida de
esos estados. **Descartado**: congelar solo `approved` — dejaría editable
una línea registrada de un documento nunca aprobado formalmente (el flujo
por obra×mes registra sin pasar por el approve del documento), que es el
caso más peligroso.

### D2 · Dónde se aplica — servidor manda, UI refleja

La guarda vive en el REPOSITORIO (todas las mutaciones pasan por él),
formulada en `application/services/congelacion.py` para que sea pura y
testable y para que vistas y guardas usen la misma decisión (R1). El
servidor responde 409 con motivo; la UI deshabilita y muestra candados,
pero es cosmética: una petición a pelo (curl) se para igual.
**Descartado**: solo deshabilitar la UI (papel mojado, lo dice el
enunciado). **Descartado**: middleware HTTP genérico por ruta — las reglas
dependen de datos (estado de la línea), no de la URL, y acabaría
duplicando lecturas; en el repositorio la comprobación va dentro de la
misma sesión/transacción que la mutación, sin TOCTOU.
**Descartado**: capa `domain/` — sv4 no tiene paquete domain (hexagonal
sin dominio propio); `application/services/` es donde viven sus reglas
(jornada_resolver, text_match…).

### D3 · La desaprobación explícita

- Ya existe `POST /documents/{id}/unapprove` («Marcar pendiente» en
  parte_detail): ESA es la desaprobación explícita. No se crea endpoint
  nuevo.
- Con líneas `encolado`: desaprobación RECHAZADA (R10) hasta que llegue el
  resultado de `q-transfer-result`.
- Con líneas `registrado`: desaprobación PERMITIDA (hace falta para
  corregir las líneas no registradas del mismo parte), pero las
  registradas siguen congeladas (R11). El candado de esas líneas explica:
  «Registrada en Sigrid (parte PT…, línea …). Corregirla exige actuar en
  Sigrid: si se elimina allí la línea, al reaprobar se escribirá con los
  valores nuevos (synckey)». Eso es exactamente lo que hace el pipeline:
  synckey ausente en Sigrid ⇒ se escribe de nuevo.
- **Descartado**: endpoint «desvincular de Sigrid» que limpie `sigrid_*`
  por línea — perdería la única referencia local (`sigrid_hmores_ide`,
  `sigrid_parte_cod`) sin conseguir nada: con el synckey aún en Sigrid,
  reaprobar seguiría sin actualizar valores (Hecho 2). Si algún día se
  quiere «anular en Sigrid desde el portal» (borrar la `hmores` vía sv5),
  es una feature nueva con su propia spec — fuera de F-004.
- **Papelera de un documento con líneas registradas**: bloqueada (R2+R7,
  y R12 para el hard-delete). **Descartado** permitirla con aviso: un
  documento oculto en el portal con horas vivas en Sigrid es la
  desincronización silenciosa que esta feature viene a impedir.

### D4 · Sin cambios de schema

`parte_documents.approved*` + `parte_registros.sigrid_estado` bastan para
toda la matriz. No se añade `approved` por línea ni columna de bloqueo.
Beneficios: no se toca `orm_models.py` (duplicado Y desincronizado,
F-010 pendiente), no hay `ALTER TABLE`, el rollback es puro código.
**Para el humano**: si en el futuro se quiere aprobación POR LÍNEA (el
§5.2 del documento maestro la insinúa), es decisión de producto aparte;
esta feature no la necesita.

### D5 · Undo y ediciones masivas: omitir y contar, no abortar

`undo_last`, reasignaciones y borrados masivos tocan N filas: abortar todo
por UNA congelada haría inutilizables esas herramientas en cuanto hubiera
un mes registrado. Se actualizan las libres, se omiten las congeladas y se
devuelve el recuento (R8/R9/R13). **Descartado** el todo-o-nada; también
**descartado** omitir en silencio (ocultaría al usuario que su acción fue
parcial).

## Riesgos

- **app.js y plantillas son grandes y sin tests JS**: el cambio de UI se
  limita a añadir atributos/clases y a leer el cuerpo del 409 en catch ya
  existentes; verificación `node --check` + parseo Jinja2 + revisión
  manual del humano (Ctrl+F5).
- **Datos históricos**: líneas ya registradas antes de F-004 con ediciones
  posteriores pueden estar ya desincronizadas; la feature congela desde su
  despliegue, no repara el pasado (fuera de alcance).
- **`only_pending` en /partes** usa `approved` de documento para filtrar;
  no se toca.

## Fuera de alcance

- Propagar ediciones a Sigrid (update/delete de `hmores` desde el portal).
- Aprobación por línea y roles/permisos (F-008).
- Resincronizar `orm_models.py` (F-010) o corregir §5.2 del documento
  maestro (se anota en progress para el humano).
- Cualquier cambio en sv3/sv5 o en infra.

## SQL

No aplica: sin schema nuevo ni ficheros SQL.
