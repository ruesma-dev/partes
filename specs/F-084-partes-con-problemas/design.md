<!-- specs/F-084-partes-con-problemas/design.md -->
# F-084 · Pestaña de partes con problemas — diseño técnico

**Rigor: `critico`** (propuesto, D9). Disparador 2 de «Niveles de rigor» (`CHECKPOINTS.md`):
**escribe en producción y en un recurso compartido**. Cambia el worker de sv3
(`q-persistencia`) que decide qué partes quedan activos y añade dos columnas a
`parte_documents` en la base `partes` del servidor compartido `psql-albaranes-rs9k2` (DDL de
arranque de sv3 y sv4). Mismo criterio que F-043 y F-047. Si el humano elige D1 (c), sin sv3
ni DDL, bastaría `estandar`.

## 1. Encaje y límite de servicio

- **sv3** (`services/partes-persistencia/`): solo el **rastro** del reemplazo (R1–R3). Es el
  único que sabe a quién sustituye cada parte nuevo. La regla no cambia (R2, R4).
- **sv4** (`services/partes-front/`): clasificación, pestaña, contador, recuperar y deshacer.
  Corregir obra y fecha de un activo, ver el PDF y descartar ya existen y se reutilizan.
- **Esquema**: las dos copias de `orm_models.py` (gemelas, en la lista cerrada de
  `CLAUDE.md`). La lista **no crece**: sv3 escribe las columnas y sv4 las lee, y no se copia
  lógica. La pista retroactiva de R8 no es la regla de sv3: es más laxa (sin trabajador) y solo
  se muestra en pantalla.
- El choque de R19 lo decide sv4 con su propia clave de trabajador (`worker_key_for_registro`,
  F-050), no con `_emp_signals` de sv3: es una guarda del portal contra horas dobles, no el
  reemplazo. Puede discrepar del criterio de sv3 en casos raros (§10).
- sv1, sv2 y sv5 no cambian. No se toca Sigrid. No hay variables de entorno nuevas.

## 2. Lo que hay hoy (`dev` 0b2ff00)

| Pieza | Dónde | Qué hace |
|---|---|---|
| Reemplazo | sv3 `sqlalchemy_parte_repository.py:1145-1204` (`_deactivate_same_day_obra`), llamado en `save_parte` :1226 | activos con la misma `fecha_int`, la misma obra (código casado o número leído) y alguna señal de trabajador común (`_emp_signals`: ide, DNI, nombre) ⇒ `is_active = False`. Salvo F-072 por entrada. No mira `email_id`, ni si el viejo está aprobado o en Sigrid. Solo deja un INFO |
| Retirado F-061 | sv4 `parte_vacio.py` (`es_retirado`, `MARCA_RETIRADO`), `_retirar_si_vacios` :4905 | el otro `is_active = false` con `deleted_at_utc` NULL: `deleted_by` = `sin-lineas[ · actor]` |
| Papelera | `list_papelera` :5150, `delete_document` :4842, `restore_document` :5192 | solo con `deleted_at_utc`; el sustituido no sale ni en «Líneas sueltas» (sus líneas siguen vivas) |
| Detalle | `get_parte` :1791 | `None` si inactivo ⇒ `/partes/{id}` da 404 |
| PDF | `get_sharepoint_ref` :4098, ruta `/partes/{id}/preview` (`app.py:2089`) | no filtra `is_active`: ya sirve el PDF de un inactivo |
| Fecha | `update_parte_fecha` :4116 + `PATCH /api/partes/{id}/fecha` (`app.py:2188`) | guarda F-004, `undo_log` `parte_fecha`, recálculo seguido; no mira `is_active` |
| Deshacer | `_record_undo` :3583 (no rellena `UndoLogOrm.actor`), `undo_last` :3816, `POST /api/undo` (`app.py:1727`) | snapshots de `_DOC_UNDO_FIELDS` (fecha y obra) y de líneas |
| sha256 | `_exigir_sin_duplicado_activo` :4966 | índice único parcial `WHERE is_active` |
| Aviso | `#poison-aviso` en `base.html` + `app.js` (~5879) | contador por JS con `/api/admin/poison` (solo colas de sv5) |
| Fallos sv2/sv3 | `cola_cliente.py` de sv2 y sv3 | agotados los reintentos, el mensaje va a `<cola>-poison`; **nada en la base** |

Los 21 «sin sustituto posterior» del líder son retirados de F-061 (fuera, R9) o partes cuyo
sustituto cambió luego de fecha u obra o se borró: `desactivado_sin_rastro`, y cuentan.

## 3. Esquema (`orm_models.py`, las dos copias, byte-idénticas)

En `ParteDocumentOrm`, tras el bloque «Soft-delete»:

```python
# --- Reemplazo de sv3 (F-084) --- #
# sv3 los escribe al desactivar un parte por el de otro documento (mismo
# dia, obra y trabajador); sv4 solo los lee. Nullables: los anteriores, NULL.
sustituido_por_id: Mapped[str | None] = mapped_column(String(36))   # sv3
sustituido_at_utc: Mapped[str | None] = mapped_column(String(64))   # sv3
```

Sin índice (hoy 112 inactivos). `ddl_complementario()` genera los dos `ADD COLUMN IF NOT
EXISTS` sin cambios de código; nullable sin defecto es un cambio de catálogo en PostgreSQL,
sin reescribir la tabla. Solo la base `partes`. No entran en `_DOC_UNDO_FIELDS`.

## 4. sv3 · `sqlalchemy_parte_repository.py`

`_deactivate_same_day_obra(session, parte, exclude_id, email_id=None)`: donde hoy hace
`old.is_active = False`, además `old.sustituido_por_id = exclude_id` y
`old.sustituido_at_utc = <ahora UTC ISO>`. Si `email_id` (el del correo del parte nuevo) no
está vacío y es igual a `old.email_id`, WARNING de R3:
`"[parte-repo] reemplazo del mismo envio: %s sustituye a %s (fecha_int=%s obra=%s)"`.
`save_parte` le pasa `_as_str(email.get("id"))`. El resto, igual.

## 5. sv4 · módulo puro `application/services/partes_con_problemas.py`

Sin BBDD, ORM ni FastAPI, como `parte_vacio.py`. Trabaja con datos simples:

```python
MOTIVO_SIN_OBRA = "sin_obra"; MOTIVO_SIN_FECHA = "sin_fecha"
MOTIVO_FECHA_FUTURA = "fecha_futura"
MOTIVO_FECHA_POSTERIOR_CORREO = "fecha_posterior_al_correo"
MOTIVO_SIN_LINEAS = "sin_lineas"
MOTIVO_SUSTITUIDO_MISMO_ENVIO = "sustituido_mismo_envio"
MOTIVO_SUSTITUIDO = "sustituido"
MOTIVO_SIN_RASTRO = "desactivado_sin_rastro"
ORDEN_MOTIVOS: tuple[str, ...]   # el de R6 y R7, los que cuentan primero
NO_CUENTAN = frozenset({MOTIVO_SUSTITUIDO})
TEXTOS: dict[str, str]           # rótulo para la pantalla

@dataclass(frozen=True)
class DocProblema:               # lo que el repositorio le pasa
    id: str; is_active: bool; deleted_at_utc: str | None; deleted_by: str | None
    fecha_int: int | None; obra_ide: int | None; obra_codigo: str | None
    obra_numero_leido: str | None; email_id: str | None
    email_received_datetime: str | None; created_at_utc: str
    sustituido_por_id: str | None; lineas_vivas: int; es_futuro: bool

def es_sustituido(d: DocProblema) -> bool            # R7/R9: inactivo, sin papelera, no retirado
def motivos_activo(d: DocProblema) -> tuple[str, ...]  # R6
def fecha_posterior_al_correo(fecha_int, recibido_iso) -> bool  # R6, margen de 1 día
def elegir_sustituto(d, por_id: dict[str, DocProblema],
                     activos: Iterable[DocProblema]) -> DocProblema | None   # R8
def motivo_sustituido(d, sustituto: DocProblema | None) -> str  # R7
def mismo_envio(a, b) -> bool                        # email_id igual y no vacío
def cuenta_para_aviso(motivos: Iterable[str]) -> bool   # R10
```

`es_futuro` lo calcula el repositorio con `_doc_es_futuro`, que ya existe: no se copia.
`es_sustituido` usa `es_retirado` de `parte_vacio.py`.

## 6. sv4 · repositorio (`infrastructure/database/parte_repository.py`)

- `list_partes_con_problemas() -> list[dict]` (R6–R11): UNA consulta de los documentos sin
  `deleted_at_utc`, con `selectinload(registros)`. Cada uno pasa a `DocProblema`. Los activos
  van por `motivos_activo`; los sustituidos, por `elegir_sustituto` + `motivo_sustituido`.
  Devuelve filas con los campos de R11 (`num_trabajadores` por `worker_key_for_registro` de las
  líneas vivas, horas como en `list_partes`, `congelado` = `_motivo_congelado_doc`, `tiene_pdf`
  como en `list_unmatched_workers`, y `sustituto` {id, fecha, obra, activo} o `None`), en el
  orden de `ORDEN_MOTIVOS` y, dentro, por fecha descendente.
- `resumen_problemas() -> dict` (R10, R25): `{total, por_motivo}` sobre la misma lista. Una
  sola fuente: la pestaña y el contador no pueden discrepar.
- `recuperar_parte(*, document_id, fecha_iso=None, fecha_int=None, actor=None) -> dict`
  (R17, R19–R22, R24): bloquea el documento (`_bloquear_documentos`). Comprueba, en este orden:
  existe (404); `es_sustituido` (si no, `NoRecuperableError` con motivo); con fecha,
  `_exigir_doc_editable`; `_exigir_sin_recalculo`; `_exigir_sin_duplicado_activo`;
  `_choques(session, doc, fecha_int_final)` ⇒ `ChoqueRecuperarError(partes)`. Después aplica
  la fecha (documento y líneas), `is_active = True` y
  `_record_undo(action="parte_recuperar", documents=[snap], registros=[snaps],
  reactivados=[id], actor=actor)`. Commit. INFO de R24.
  Devuelve `{"document_id", "fecha"}`.
- `_choques(...)`: activos con la misma `fecha_int` y la misma obra (`obra_ide` si los dos lo
  tienen; si no, `obra_codigo`, y si no, `obra_numero_leido`) cuyas claves de trabajador de
  líneas vivas se cruzan con las suyas. Su resultado es una lista `[{id, fecha, obra}]`.
- `_record_undo` gana dos kwargs opcionales: `reactivados` (entra en el payload solo si se
  pasa, como `creadas`) y `actor` (va a `UndoLogOrm.actor`, que hoy nadie rellena). Las demás
  acciones no cambian.
- `undo_last`: con `action == "parte_recuperar"`, tras los snapshots, cada id de
  `reactivados` que siga activo y no congelado vuelve a `is_active = False` (los congelados
  cuentan en `omitidos`). `document_ids` ya los devuelve (R23).
- Excepciones nuevas (en el módulo de §5): `NoRecuperableError(motivo)` y
  `ChoqueRecuperarError(partes)`, las dos con `.motivo`.

## 7. sv4 · rutas (`interface_adapters/web/app.py`, todas `include_in_schema=False`)

| Método | Ruta | Respuesta |
|---|---|---|
| GET | `/problemas` | HTML, `problemas.html` (R11–R16) |
| GET | `/api/problemas/resumen` | `{ok, total, por_motivo}`; si falla, `{ok: false, total: 0}` con 200 y WARNING |
| POST | `/api/partes/{id}/recuperar` | 200 `{ok, document_id, fecha, recalculo}`; 400 fecha no válida (`_parse_fecha_to_iso_int`); 404; 409 `{ok: false, error, partes?}` para `NoRecuperableError`, `ChoqueRecuperarError`, `CongeladoError` (incluye `RecalculandoError`) y `DuplicadoActivoError` |

Tras un 200, `_pedir_recalculo_seguido(id, MOTIVO_RECUPERAR_PARTE, _actor(request))` (R18).
En `undo_apply`, la rama de `parte_fecha` pasa a cubrir también `parte_recuperar`, con
`MOTIVO_DESHACER_RECUPERAR` (R23). En `infrastructure/persistencia/recalculo_publisher.py`:
`MOTIVO_RECUPERAR_PARTE = "recuperar_parte"` y
`MOTIVO_DESHACER_RECUPERAR = "deshacer_recuperar_parte"`. Solo traza: sv3 hace la misma pasada.

«Descartar» no es ruta nueva: un `<form method="post" action="/documents/{id}/delete">` con
`back=/problemas`. `delete_document` (`app.py:4002`) ya redirige a `back` con su mensaje y
traduce el `CongeladoError` (R26).

## 8. sv4 · plantillas y JS

- `templates/problemas.html` (nuevo, `extends "base.html"`): cabecera con el total; una sección
  por motivo con su rótulo (`TEXTOS`); por fila, lo de R11, «Ver PDF» con `data-parte-pdf`
  (visor de `wirePdfModal`, R12), enlace al detalle (R13) o los botones `data-recuperar` y el
  formulario de descartar (R14); vacío (R15). Sin DNIs (R16): solo nombres, como Conciliar.
- `templates/base.html`: enlace «Problemas» entre «Conciliar» y «Partes», con
  `<span class="nav-badge" id="problemas-badge" hidden>` (R25).
- `static/app.js`: (1) `wireProblemasBadge()` pide `/api/problemas/resumen` al cargar y pinta
  el número si `total > 0`; un fallo se traga (R25). (2) `[data-recuperar]`: pregunta la
  fecha (campo con la actual; vacío = sin cambio) y confirma; hace POST; si es 409 con
  `partes`, enseña el error y los partes con su enlace; si es 200, recarga con mensaje y
  avisa si `recalculo` es `fallo`. (3) `_undoActionLabel`: `parte_recuperar: "Recuperar parte"`.
- `static/styles.css`: `.nav-badge` (como `.poison-badge`) y las insignias de motivo.

## 9. Ficheros

**Crear**
- `services/partes-front/application/services/partes_con_problemas.py`
- `services/partes-front/templates/problemas.html`
- `services/partes-persistencia/tests/test_f084_rastro_reemplazo.py` (R1–R5)
- `services/partes-front/tests/test_f084_clasificacion.py` (R6–R10, unit)
- `services/partes-front/tests/test_f084_recuperar.py` (R17, R19–R24, repositorio SQLite)
- `services/partes-front/tests/test_f084_portal.py` (R11–R16, R18, R25, R26, TestClient)

**Modificar**
- `services/partes-persistencia/infrastructure/database/orm_models.py` y
  `services/partes-front/infrastructure/database/orm_models.py`: §3, iguales.
- `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py`: §4.
- `services/partes-front/infrastructure/database/parte_repository.py`: §6.
- `services/partes-front/interface_adapters/web/app.py`: §7.
- `services/partes-front/infrastructure/persistencia/recalculo_publisher.py`: dos motivos.
- `services/partes-front/templates/base.html`, `static/app.js`, `static/styles.css`: §8.
- `tests/test_f010_orm_models_gemelos.py` y `services/*/tests/test_f010_r6_ddl_*`: solo si
  enumeran las columnas de `parte_documents` (comprobarlo en T1).
- `docs/ARCHITECTURE.md` (semántica 7 y 8: columnas y pestaña) y `azure-apps/partes.md` (§11).

**No se tocan**: la condición del reemplazo (`_emp_signals`, `_misma_entrada`) ni el dedup
por sha256 de sv3; `congelacion.py` ni `recurso_conciliador.py` (gemelos); `parte_vacio.py`
(solo se usa); `get_parte` y `/partes/{id}` (el inactivo sigue en 404); `list_papelera`,
`restore_document` y `delete_document`; `PATCH …/fecha` y `PATCH …/obra`; `/conciliacion`;
sv1, sv2, sv5; `infra/` (el DDL lo aplica el arranque).

## 10. Riesgos y alternativas descartadas

- **Dos criterios de «mismo trabajador»**: sv3 usa ide, DNI o nombre; R19 usa la clave del
  portal. Si discrepan, recuperar puede dejar dos partes del mismo día y obra con el mismo
  trabajador. Mitigación: la clave del portal es la que agrupa la matriz, así que el doble se
  ve en la celda. Llamar a sv3 para decidirlo (cola, asíncrono) se descarta por complejo.
- **Sustitución de un parte aprobado o en Sigrid** (D10): hoy pasa y F-084 no lo cambia. El
  nuevo puede aprobarse y escribirse otra vez (las synckeys van por línea). La pestaña lo hace
  visible con la insignia. Si el líder encuentra casos, va a feature aparte, de sv3 y crítica.
- **Contador en cada página**: `resumen_problemas` carga los ~640 documentos con sus líneas,
  como `/partes`; va por JS, asíncrono. Si pesa, se cachea en una feature aparte.
- **Descartada** D2 (b), «no sustituir entre páginas del mismo envío»: dejaría dos partes
  activos con el mismo trabajador y día. sv3 los sumaría para el exceso de jornada (extras
  falsas) hasta que alguien los mirase. Con (a) no cambia lo activo y nada se pierde en silencio.
- **Descartado** guardar el motivo en `deleted_by` (D1 (b), como F-061): sin DDL, pero obliga
  a una convención de texto compartida entre sv3 y sv4 y a analizarla. La columna es explícita.
## 11. Frontera

**¿Cruza la frontera del proyecto? Sí.** Cambia el **esquema** de la base `partes` (dos
columnas nullables en `parte_documents`), que vive en el servidor compartido
`psql-albaranes-rs9k2`. No se toca nada a nivel de servidor. Hay **tres rutas nuevas del
portal** y dos motivos nuevos en el mensaje `recalcular` sv4 → sv3 (`q-persistencia`), solo de
traza. Se actualiza `C:\Users\pgris\PycharmProjects\azure-apps\partes.md`: §3.3 (rastro del
reemplazo), §3.4 (pestaña y rutas), §4.1 (fila nueva «Reemplazo de sv3 (F-084)» y la nota de
«Papelera»), §4.5 (`parte_recuperar`, `actor`) y la lista de motivos de recálculo. Va en un
commit aparte en `azure-apps`, con `pull --rebase` antes y sin push. Ni Sigrid ni sigrid-api
cambian.

## 12. Verificación manual (humano, tras desplegar sv3 y sv4)

- **M1** (solo lectura): `SELECT column_name FROM information_schema.columns WHERE table_name
  = 'parte_documents' AND column_name LIKE 'sustituido%';` ⇒ 2 filas.
- **M2** (portal): `/problemas` lista `5c1a9b04` como `sustituido_mismo_envio` con `89f17181`
  de sustituto, y el contador = `total` de `/api/problemas/resumen`.
- **M3** (con OK expreso del humano): «Recuperar» `5c1a9b04` con 25/11/2026; si existe el
  reenvío del 25/11, 409 nombrándolo; entonces «Descartar» y verlo en la papelera.

## 13. Decisiones

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| D1 Rastro del reemplazo | (a) sv3 escribe `sustituido_por_id` y `sustituido_at_utc` (2 columnas nullables); (b) marca `sustituido · <id>` en `deleted_by`, sin DDL; (c) nada en sv3: sv4 lo deduce siempre | (a) | |
| D2 Páginas del mismo envío | (a) se sigue sustituyendo y se avisa (pestaña, contador, WARNING); (b) no se sustituye: los dos activos y el nuevo a revisión; (c) no se sustituye y se desactiva el nuevo | (a) | |
| D3 Qué cuenta en el aviso | (a) todo menos `sustituido` (los reenvíos se listan sin contar); (b) todo | (a) | |
| D4 Retroactivo | (a) sí: los anteriores a F-084 salen por la pista de R8; (b) solo los sustituidos desde el despliegue | (a) | |
| D5 Fecha dudosa | (a) `sin_fecha` + `fecha_futura` + `fecha_posterior_al_correo`; (b) sin la última | (a) | |
| D6 Recuperar con choque | (a) 409: corregir la fecha o descartar antes el otro; (b) recuperar igual, con aviso; (c) intercambiar (desactivar al otro) | (a) | |
| D7 Páginas que no llegan a la base (poison de `q-extraccion` y `q-persistencia`) | (a) feature aparte (contador y reencolado como el de F-002); (b) dentro de F-084 | (a) | |
| D8 Recuperar en «Deshacer» | (a) sí, acción `parte_recuperar` con actor; (b) no: el inverso es descartar | (a) | |
| D9 Rigor | (a) `critico` (disparador 2); (b) `estandar` (solo si D1 = c) | (a) | |
| D10 Sustituir un parte aprobado o en Sigrid | (a) fuera: insignia en la pestaña y feature aparte si hay casos; (b) dentro: sv3 no lo sustituye | (a) | |
