<!-- specs/F-061-parte-vacio-tras-borrar-lineas/design.md -->
# F-061 · Un parte que se queda sin líneas no puede seguir activo — diseño técnico

## 1. Encaje y límite de servicio

**sv4** lleva el ciclo de vida del parte en el portal: ahí está la causa y el arreglo. Con
el parte retirado (`is_active = false`) el sha256 queda libre y sv3 reingiere sin cambios
(DA6). Nada de sv1, sv2, sv3, sv5 ni Sigrid; sin DDL (`orm_models.py` intacto). La
congelación (lista cerrada) solo se **usa** (`_separar_congeladas`, `vive_fuera`).

## 2. Lo que hay hoy (`dev` 843ff13)

sv4, `infrastructure/database/parte_repository.py`:

| Camino | Qué hace con el parte |
|---|---|
| `soft_delete_registro` (:4055) | marca la línea; **no mira el parte** ⇒ activo y vacío |
| `soft_delete_worker` (:4127) | manda a la **papelera de partes** los que se vacían, **sin bloqueo** (carrera) |
| `soft_delete_obra` / `delete_document` | mandan el parte entero a la papelera de partes (no cambia) |
| `_deshacer_creadas` (:3384, F-049) | marca líneas; no mira el parte |
| `vaciar_papelera` (:4239) | `session.delete` de las líneas sueltas; **no mira el parte** ⇒ activo con 0 filas |
| `hard_delete_registro` (:4084) | borra la línea; no mira el parte |
| `restore_registro` (:4068) | devuelve el parte solo si estaba en la papelera de partes (`deleted_at_utc`) |
| `restore_document` (:4212) | solo el parte: si se vació, **vuelve activo y vacío**; sha repetido ⇒ 500 por el índice |
| `list_papelera` (:4170) | «líneas sueltas» = líneas borradas de partes con `deleted_at_utc IS NULL`: **ya incluye** las de un parte retirado (R5 sin cambio de consulta) |
| `list_partes` (:1564) | cuenta empleados y horas de **todas** las filas, también las de la papelera |

El borrado en bloque (`app.js`, `doBorrar`) lanza N `POST …/delete` a la vez (`Promise.all`):
de ahí R3. El índice `ux_parte_documents_sha256_active` es único parcial `WHERE is_active`.
La única FK a `parte_documents` es la de `parte_registros`, y `undo_last` salta los partes
que ya no existen (`session.get` ⇒ `None` ⇒ `continue`): borrar un parte sin filas no deja
referencias rotas.

## 3. Ficheros (todos en `services/partes-front/`)

| Fichero | Cambio |
|---|---|
| `application/services/parte_vacio.py` (**nuevo**) | §4.1: marca, motivos, excepción y predicados puros |
| `infrastructure/database/parte_repository.py` | §4.2: bloqueo, retirar, borrar sin filas, restaurar, `ParteRow.sin_lineas`, métodos del script |
| `interface_adapters/web/app.py` | `api_registro_delete` devuelve R1; los dos restaurar capturan `DuplicadoActivoError` (409) |
| `static/app.js` | §4.3 |
| `templates/partes_list.html` | insignia «Sin líneas» (`badge warn`) si `p.sin_lineas` (R13) |
| `limpiar_partes_vacios.py` (**nuevo**, raíz de sv4) | §4.4 |
| `tests/test_f061_*.py` (**nuevos**) | §6 |

**Docs**: `docs/ARCHITECTURE.md` (semántica 8, «Herramientas de consola») y
`C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (filas `source_sha256` y papelera).

**No se tocan**: sv3 entero (incluidos `get_by_sha256` y `_deactivate_same_day_obra`),
`orm_models.py`, `congelacion.py`, `soft_delete_obra`, `delete_document`,
`hard_delete_document`, `crear_parte_manual`, `guardar_celda`, sv1, sv2 y sv5.

## 4. Funciones

### 4.1 `application/services/parte_vacio.py` (application, puro)

- `MARCA_RETIRADO = "sin-lineas"`. `marca_retirado(actor: str | None) -> str` devuelve
  `"sin-lineas"`, o `"sin-lineas · <actor>"` recortado a 255 caracteres.
  `es_retirado(*, is_active, deleted_at_utc, deleted_by) -> bool`: no activo, sin
  `deleted_at_utc` y `deleted_by` que empieza por la marca. Distingue al retirado del parte
  desactivado por el reemplazo de sv3 (`_deactivate_same_day_obra`), que deja `deleted_by`
  a `NULL` (DA7).
- `PARTES_SIGRID_PROTEGIDOS = frozenset({"PT26/00373", "PT26/00375", "PT26/00376"})`.
- `MOTIVO_DUPLICADO_ACTIVO = "Ya hay un parte activo del mismo PDF (se volvió a procesar).
  Restaurar esto crearía un duplicado: elimínalo de la papelera."`.
  `class DuplicadoActivoError(Exception)`, con `motivo`. No hereda de `CongeladoError`.
- `motivo_exclusion_limpieza(*, aprobado, estados, partes_sigrid) -> str | None`. Devuelve
  `"aprobado"`, `"vive_fuera"` (`vive_fuera(e)` o `encolado`) o `"protegido"`, en ese orden.
- `categoria_vacio(*, filas, manual, empleados_leidos) -> str` (R15).
- `empleados_leidos(raw_extraction_json) -> int`: `len(data.empleados)` si es una lista.
  Con el JSON inválido o ausente da 0, sin lanzar.

### 4.2 `ParteReviewRepository` (infrastructure)

- **`_sql_bloqueo_documentos(ids) -> Select`** (estático): `select(ParteDocumentOrm)
  .where(id.in_(ids)).order_by(ParteDocumentOrm.id).with_for_update()`. Va aparte para
  poder testear el SQL compilado. `_bloquear_documentos(session, ids)` lo ejecuta. En SQLite
  el `FOR UPDATE` desaparece al compilar, y es lo esperado.
- **`_retirar_si_vacios(session, ids, *, by) -> list[str]`**. Hace `flush`. Cada parte
  activo sin ninguna línea viva pasa a `is_active = False` y
  `deleted_by = marca_retirado(by)`; `deleted_at_utc` sigue en `NULL`. Devuelve los ids. Es
  el único sitio que escribe la regla.
- **`_borrar_retirados_sin_filas(session, ids=None) -> int`**. Hace `flush` y
  `session.delete` de cada parte retirado (`es_retirado`) sin ninguna fila. Con `ids=None`
  barre todos; si no, solo esos. Es el único sitio del borrado físico decidido por el humano
  (R9–R11): un parte con filas o no retirado nunca entra.
- **`borrar_linea(*, registro_id, by) -> dict`** (nuevo).
  1. Si la línea no existe o ya está borrada, devuelve `{"ok": False}`.
  2. Bloquea su parte **antes** de las guardas, que siguen como hoy
     (`_exigir_reg_editable`, `_exigir_sin_recalculo`).
  3. Marca la línea, llama a `_retirar_si_vacios` y hace `commit`.
  4. Devuelve `{"ok": True, "parte_retirado": bool, "document_id": id}`.

  `soft_delete_registro` queda como `return self.borrar_linea(...)["ok"]`: tiene 8 usos en
  tests.
- **`soft_delete_worker`**. Selecciona las líneas y bloquea sus partes por `id`. Después
  **vuelve a leer** las candidatas, porque pudieron cambiar mientras esperaba. Separa las
  congeladas, marca el resto y llama a `_retirar_si_vacios`, que sustituye a su bloque actual
  «a papelera». Bloquear el parte antes de tocar líneas, como hace `borrar_linea`, evita el
  abrazo mortal. Devuelve lo mismo que hoy.
- **`_deshacer_creadas`**: al final, `_retirar_si_vacios` sobre los partes de las creadas
  (R2).
- **`restore_registro`**.
  1. Si el parte está retirado o en la papelera de partes y existe otro parte activo con el
     mismo `source_sha256`, lanza `DuplicadoActivoError` antes de escribir (R7).
  2. Restaura la línea.
  3. Si el parte estaba retirado, lo devuelve: `is_active = True` y `deleted_by = None`
     (R6). La rama actual de la papelera de partes no cambia.
- **`restore_document`**: la misma comprobación de sha (R7). Si el parte no tiene ninguna
  línea viva, restaura además todas sus líneas de la papelera (R8): es el legado del
  `soft_delete_worker` anterior.
- **`hard_delete_registro`**: tras borrar, llama a `_borrar_retirados_sin_filas(session,
  [document_id])` (R10).
- **`vaciar_papelera`**: tras su bucle actual, `partes_borrados =
  _borrar_retirados_sin_filas(session)`, el barrido global (R9). La clave se añade al
  resultado.
- **`list_partes`**: empleados, `num_registros` y horas solo con las líneas vivas.
  `sin_lineas = not vivas` es un campo nuevo de `ParteRow`, con defecto `False` (R13).
- **Para el script** (§4.4):
  - `partes_vacios_activos() -> list[dict]`: solo `SELECT`.
  - `limpiar_vacios(document_ids, *, by) -> dict`: bloquea por `id` y recomprueba que cada
    parte sigue activo, vacío y sin exclusión. Si lo cumple, llama a `_retirar_si_vacios` y
    luego a `_borrar_retirados_sin_filas(ids)`: el parte sin filas acaba borrado y el que
    tiene filas, retirado. Devuelve `{"borrados", "retirados", "saltados"}`.

### 4.3 Portal (`static/app.js`, `app.py`)

- **`.line-del`**: si `d.parte_retirado`, enseña el aviso de R12. Si la página es
  `/partes/<document_id>`, va a `/partes`; si no, recarga. **`doBorrar`** lee el JSON de
  cada respuesta y aplica lo mismo.
- **`[data-restore-doc]` y `[data-restore-line]`**: con `d.error`, `alert(d.error)`.
- **Vaciar**: el aviso de hoy no cambia (`omitidos`). `partes_borrados` no se enseña: el
  parte ya no se veía.
- **`app.py`**:
  - Los dos endpoints de restaurar capturan `DuplicadoActivoError` y devuelven 409
    `{"ok": false, "error"}`.
  - `api_registro_delete` devuelve el dict de `borrar_linea`.
  - El 409 de congelación sigue llegando por su manejador global.

### 4.4 `limpiar_partes_vacios.py` (script de consola de sv4; uso en §9 M2)

- **Conexión**: `create_engine(settings.database_url)` + `sessionmaker`, en una clase mínima
  con `create_session()`. **Sin `SessionFactory`**, que crea la base y entra en la de
  administración del servidor compartido (R18).
- **Informe**: en PostgreSQL, `SET TRANSACTION READ ONLY`. Usa `partes_vacios_activos()`
  con `categoria_vacio`, la acción prevista y `motivo_exclusion_limpieza`, y escribe
  `logs/limpieza_partes_vacios_<AAAAMMDD-HHMM>.md` y `.csv`.
- **`--ejecutar --esperados N`**: si los candidatos no son N, sale con código 2 sin
  escribir. Si lo son, llama a `limpiar_vacios(ids, by="F-061-limpieza")` e imprime el
  resultado (es un script: `print` permitido).

## 5. SQL

Sin `.sql`, DDL ni tablas: ORM sobre la base `partes`. Lo nuevo:
- `FOR UPDATE` sobre filas de `parte_documents` (nada a nivel de servidor);
- `DELETE` de filas de `parte_documents` sin filas hijas, solo para los partes retirados;
- la consulta de vacíos, la de la M0 de §9.

## 6. Tests (sin red ni BBDD; SQLite en memoria con `dobles.py`; `test_f061_rN_…`)

- **`tests/test_f061_borrado.py`**:
  - **R1**: la última línea retira el parte (inactivo, sin `deleted_at_utc`, con la marca) y
    devuelve el dict. Con líneas vivas, `false`. También por `TestClient`.
  - **R2**: persona con congeladas ⇒ el parte sigue activo. Persona o `_deshacer_creadas`
    que lo vacían ⇒ retirado.
  - **R3**: `_sql_bloqueo_documentos` compilado en `postgresql` lleva `FOR UPDATE` y
    `ORDER BY parte_documents.id`. Espía en `borrar_linea` y `soft_delete_worker`. Dos
    borrados seguidos ⇒ retirado.
  - **R4**: obra y «Borrar parte» siguen a la papelera de partes (regresión).
- **`tests/test_f061_papelera.py`**:
  - **R5**: `list_papelera` lista las líneas de un parte retirado y no el parte.
  - **R6–R8**: restaurar una línea devuelve el parte; otro activo con el mismo sha ⇒ 409 y
    nada escrito (línea y parte); restaurar un parte sin vivas devuelve sus líneas.
  - **R9–R11**: vaciar borra el retirado sin filas (`partes_borrados`), sin `SAWarning` como
    F-010 R11. Un retirado con una fila `registrado` omitida sigue. No borra un parte de la
    papelera de partes, ni uno activo vacío, ni uno desactivado por sv3 (`deleted_by NULL`).
    «Eliminar» la última fila de un retirado borra el parte.
- **`tests/test_f061_portal.py`**:
  - **R12**: `app.js` maneja `parte_retirado`, con `node --check` en la verificación.
  - **R13**: `list_partes` cuenta solo las vivas y pone `sin_lineas`; la plantilla pinta
    «Sin líneas».
- **`tests/test_f061_limpieza.py`**:
  - **R14–R18**: las categorías y la acción prevista; las tres exclusiones; `--esperados`
    distinto ⇒ código 2 y nada escrito; `--ejecutar` sin `--esperados` ⇒ error de uso. La
    ejecución borra el parte sin filas y retira el que tiene filas, con la marca
    `F-061-limpieza`, y no lanza ningún `DELETE` sobre `parte_registros`
    (`before_cursor_execute`). No importa `SessionFactory` y el CSV no lleva nombres.
  - Las funciones puras de §4.1.
- **R19–R20**: tarea de límite (`git diff --stat dev`) y reviewer, no pytest.

## 7. Riesgos y decisiones

- **Abrazo mortal**: todo camino bloquea el parte antes de tocar líneas (varios, por `id`).
- **Restaurar con el sha ya reprocesado**: es el caso esperable, porque retirar libera el
  sha para eso. R7 responde con un 409 legible, en vez del 500 del índice, y la línea vieja
  se elimina desde la papelera.
- **La marca vive en `deleted_by`** sin `deleted_at_utc`: no hace falta DDL. Un parte
  desactivado por sv3 (`deleted_by NULL`) nunca se confunde con un retirado y nunca se borra
  (DA7).
- **El borrado físico es irreversible**: solo afecta a partes retirados y sin ninguna fila,
  por decisión del humano. Lo que se pierde es la fila del documento (su lectura IA y sus
  metadatos); el PDF sigue en SharePoint y en el buzón, y se puede reprocesar.
- **`list_partes` cambia cifras** con líneas en la papelera: es corrección (semántica 3); si
  un test viejo contaba con lo anterior, `blocked` y se consulta, sin tocarlo.
- **El script escribe en producción**: lee por defecto, exige `--esperados`, recomprueba
  bajo bloqueo y lo autoriza el humano (§9).

## 8. Despliegue

Solo **sv4** (`redeploy_partes.ps1 -Solo sv4`), a petición del humano; sin variables ni
interruptor; rollback = imagen anterior (lo borrado físicamente no vuelve).

## 9. Verificación manual (base `partes`, nunca el servidor `psql-albaranes-rs9k2`)

**M0 · HECHA por el líder el 2026-10-26** (solo lectura; consulta en `design.md` §9 del
commit `02da480`):

| Categoría | Partes | Fechas | Aprobado / vive fuera / protegido |
|---|---|---|---|
| `sin_filas_leidos` | 29 | 2026-07-15 a 2026-10-22 | ninguno |
| `sin_filas_nada_leido` | 1 | 2026-07-16 | ninguno |
| `todas_en_papelera` | 0 | — | — |

`restaurables_que_chocarian` = 0. Los 30 son `borrar` según la regla.

**M1 · humano, tras desplegar.** Parte manual de prueba (obra 0404, día sin nada en Sigrid,
dos líneas): (1) borrar una ⇒ sigue; (2) borrar la otra ⇒ aviso, `/partes`, el parte no sale
ni en `/partes` ni en «Partes borrados» y sus dos líneas sí en «Líneas sueltas»; (3)
restaurar una ⇒ el parte vuelve con ella; (4) borrarla y vaciar. El líder comprueba en solo lectura `SELECT count(*) FROM parte_documents WHERE id =
'<id>'` ⇒ 0. No se registra nada en Sigrid, y PT26/00373, 00375 y 00376 quedan intactos.

**M2 · limpieza, autorizada por el humano de forma literal.** Desde `services/partes-front`
y con su `.env`:
1. `../../.venv/Scripts/python.exe limpiar_partes_vacios.py` deja el informe en `logs/`.
   Hoy esperaría 30 `borrar`.
2. Una vez leído, `… limpiar_partes_vacios.py --ejecutar --esperados <N>`.
3. Se repite la M0: 0 candidatos no excluidos.

## 10. Decisiones

| DA | Tema | Estado | Decisión / recomendación |
|---|---|---|---|
| DA1 | Parte que se queda sin líneas vivas | **Decidida por el humano** (2026-10-26): «el parte como entidad no hace falta que vaya a paperlera porque es confuso. habra una logica que borre el parte en si, al quedarse sin lineas»; opción «Oculto y luego borrado» | Se **retira**: inactivo, sin `deleted_at_utc`, con marca. No sale en `/partes` ni en la papelera de partes. Libera el sha. Vale para el borrado de líneas, de persona y el deshacer de celda. Obra y «Borrar parte» no cambian (R4) |
| DA2 | Restaurar | **Decidida por el humano** («Si se restaura una de sus líneas, el parte vuelve») | Restaurar una línea devuelve el parte retirado. Con otro activo del mismo sha, 409 sin escribir (R7). `restore_document` devuelve las líneas si no tiene vivas (R8) |
| DA3 | Vaciar la papelera | **Decidida por el humano** («Cuando se vacía la papelera y no le queda ninguna fila, el parte se borra de verdad») | Borrado **físico** del parte retirado sin filas, al vaciar y al «Eliminar» su última fila (R9–R11). Es el único borrado físico nuevo |
| DA4 | Los existentes (M0: 30) | **Decidida por el humano**: «Lo mismo que la regla»; el script lo lanza el humano | Script con informe y `--ejecutar --esperados N`: borra el parte sin filas y retira el que tiene filas. Excluye aprobados, los que viven fuera y PT26/00373, 00375 y 00376 |
| DA5 | Portal | Abierta | **A** (recomendada): contar solo las vivas en `/partes` e insignia «Sin líneas». B: además, un aviso en la cabecera. C: nada |
| DA6 | ¿Tocar la deduplicación de sv3? | Abierta | **A** (recomendada): no. El parte retirado ya no bloquea, y los 30 se limpian. Solo queda el parte que **nace** vacío, que se quita con «Borrar parte». B: que sv3 trate un activo vacío como inexistente (otro servicio y otro despliegue para un caso residual) |
| DA7 | Cómo se reconoce un parte retirado | Abierta | **A** (recomendada): marca `sin-lineas` en `deleted_by` con `deleted_at_utc NULL`, sin DDL. B: una columna nueva en `orm_models.py` de sv3 y sv4 (lista cerrada, DDL). C: sin marca, «inactivo y sin vivas»; se confunde con el reemplazo de sv3 |
| DA8 | Rigor | Abierta | **A** (recomendada): `estandar`. Aunque hay borrado físico, se limita a partes retirados sin filas, no toca Sigrid ni el servidor, y la limpieza la autoriza el humano. B: `critico` |
