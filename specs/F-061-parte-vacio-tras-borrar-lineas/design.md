<!-- specs/F-061-parte-vacio-tras-borrar-lineas/design.md -->
# F-061 · Un parte que se queda sin líneas no puede seguir activo — diseño técnico

## 1. Encaje y límite de servicio

**sv4** lleva el ciclo de vida del parte en el portal: ahí está la causa y el arreglo.
**sv3** es el único que deduplica por sha256: la red de seguridad (R11–R13) solo cabe ahí.
Nada de sv1, sv2, sv5 ni Sigrid; sin DDL (`orm_models.py` intacto). La congelación (lista
cerrada) solo se **usa** (`_separar_congeladas`, `vive_fuera`). «Parte vacío»: DA7.

## 2. Lo que hay hoy (`dev` 843ff13)

sv4, `infrastructure/database/parte_repository.py`:

| Camino | Qué hace con el parte |
|---|---|
| `soft_delete_registro` (:4055) | marca la línea; **no mira el parte** ⇒ activo y vacío |
| `soft_delete_worker` (:4127) | manda a la papelera los que se vacían, pero **sin bloqueo** (carrera) |
| `soft_delete_obra` / `delete_document` | mandan el parte entero a la papelera (bien) |
| `_deshacer_creadas` (:3384, F-049) | marca líneas; no mira el parte (hoy casi imposible vaciarlo) |
| `vaciar_papelera` (:4239) | `session.delete` de las líneas sueltas; **no mira el parte** ⇒ activo con 0 filas |
| `restore_registro` (:4068) | devuelve el parte si estaba en la papelera (bien) |
| `restore_document` (:4212) | solo el parte: si se vació por borrado, **vuelve activo y vacío** |
| `list_partes` (:1564) | cuenta empleados y horas de **todas** las filas, también las de la papelera |

El borrado en bloque (`app.js`, `doBorrar`) lanza N `POST …/delete` a la vez (`Promise.all`):
de ahí R3. En sv3, `get_by_sha256` (`sqlalchemy_parte_repository.py:850`) filtra solo
`is_active` y el pipeline (`:152`) descarta la reingesta; el índice
`ux_parte_documents_sha256_active` es único parcial `WHERE is_active`, así que insertar sin
retirar antes el vacío choca. Hay partes que **nacen vacíos** (sv3 guarda sin empleados).

## 3. Ficheros

**sv4** (`services/partes-front/`)

| Fichero | Cambio |
|---|---|
| `application/services/parte_vacio.py` (**nuevo**) | §4.1: motivos, excepción y predicados puros |
| `infrastructure/database/parte_repository.py` | §4.2: bloqueo, vaciado, caminos de §2, `ParteRow.sin_lineas` |
| `interface_adapters/web/app.py` | `api_registro_delete` devuelve R1; restaurar captura `DuplicadoActivoError` (409) |
| `static/app.js` | §4.3 |
| `templates/partes_list.html` | insignia «Sin líneas» (`badge warn`) si `p.sin_lineas` (R10) |
| `limpiar_partes_vacios.py` (**nuevo**, raíz de sv4) | §4.5 |
| `tests/test_f061_*.py` (**nuevos**) | §6 |

**sv3** (`services/partes-persistencia/`)

| Fichero | Cambio |
|---|---|
| `domain/models/parte_records.py` | `ExistingParte` + `registros_vivos: int \| None = None`, `aprobado: bool = False`; excepción `ParteYaNoVacio` |
| `domain/ports/parte_repository.py` | `save_parte(..., reemplaza_vacio: str \| None = None)` |
| `infrastructure/database/sqlalchemy_parte_repository.py` | §4.4 |
| `application/pipelines/persist_parte_pipeline.py` | decisión de dedup (§4.4) y docstring del paso 2 |
| `tests/test_f061_*.py` (**nuevos**) | §6 |

**Documentación**: `docs/ARCHITECTURE.md` (semántica 8 y «Herramientas de consola») y
`C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (fila `source_sha256`: «ni uno vacío»).

**No se tocan**: `orm_models.py` (sv3, sv4), `congelacion.py` (sv4), `recurso_conciliador.py`
y `_deactivate_same_day_obra` (sv3), `hard_delete_*`, `soft_delete_obra`, `delete_document`,
`crear_parte_manual`, `guardar_celda`, sv1, sv2 y sv5.

## 4. Funciones

### 4.1 `application/services/parte_vacio.py` (application, puro)

- `PARTES_SIGRID_PROTEGIDOS = frozenset({"PT26/00373", "PT26/00375", "PT26/00376"})`.
- `MOTIVO_DUPLICADO_ACTIVO = "Ya hay un parte activo del mismo PDF (se volvió a leer).
  Restaurar este crearía un duplicado: elimínalo de la papelera o borra antes el otro."`
- `class DuplicadoActivoError(Exception)` con `motivo`; no hereda de `CongeladoError`.
- `motivo_exclusion_limpieza(*, aprobado, estados, partes_sigrid) -> str | None`:
  `"aprobado"`, `"vive_fuera"` (`vive_fuera(e)` o `encolado`) o `"protegido"`, en ese orden.
- `categoria_vacio(*, filas: int, manual: bool, empleados_leidos: int) -> str` (R15) y
  `empleados_leidos(raw_extraction_json: str | None) -> int`: `len(data.empleados)` si es
  lista; JSON inválido o ausente ⇒ 0, sin lanzar.

### 4.2 `ParteReviewRepository` (infrastructure)

- **`_sql_bloqueo_documentos(ids) -> Select`** (estático): `select(ParteDocumentOrm)
  .where(id.in_(ids)).order_by(ParteDocumentOrm.id).with_for_update()`. Aparte para testear
  el SQL compilado; `_bloquear_documentos(session, ids)` lo ejecuta. En SQLite el
  `FOR UPDATE` desaparece al compilar: es lo esperado.
- **`_a_papelera_si_vacios(session, ids, *, ahora, by) -> list[str]`**: `flush`; cada parte
  activo sin ninguna línea viva (`select … limit(1)`, como hoy en `soft_delete_worker`) va a
  la papelera; devuelve los ids. Único sitio de sv4 que escribe la regla.
- **`borrar_linea(*, registro_id, by) -> dict`** (nuevo): línea inexistente o ya borrada ⇒
  `{"ok": False}`; si no, bloquea su parte **antes** de las guardas (`_exigir_reg_editable`,
  `_exigir_sin_recalculo`, como hoy), marca la línea, `_a_papelera_si_vacios`, `commit` y
  devuelve `{"ok": True, "documento_a_papelera": bool, "document_id": id}`.
  `soft_delete_registro` queda como `return self.borrar_linea(...)["ok"]` (8 usos en tests).
- **`soft_delete_worker`**: selecciona las líneas, bloquea sus partes por `id`, **vuelve a
  leer** las candidatas (pudieron cambiar mientras esperaba), separa congeladas, marca y
  `_a_papelera_si_vacios`. Bloquear el parte antes de tocar líneas, igual que `borrar_linea`,
  evita el abrazo mortal. Devuelve lo mismo que hoy.
- **`_deshacer_creadas`**: al final, `_a_papelera_si_vacios` sobre los partes de las
  creadas (R2). Sin bloqueo nuevo.
- **`vaciar_papelera`**: guarda los `document_id` de las líneas sueltas que borra y después
  `_a_papelera_si_vacios` sobre ellos; añade `documentos_a_papelera: int` (R5).
- **`restore_registro` / `restore_document`**: antes de escribir, si el parte no está activo
  y hay otro activo con el mismo `source_sha256`, `DuplicadoActivoError` (R8).
  `restore_document` restaura además todas sus líneas de la papelera si ninguna está viva (R7).
- **`list_partes`**: empleados, `num_registros` y horas solo con líneas vivas, y
  `sin_lineas = not vivas` (campo nuevo de `ParteRow`, defecto `False`) (R10).
- **`partes_vacios_activos() -> list[dict]`** (solo `SELECT`) y
  **`vacios_a_papelera(document_ids, *, by) -> dict`** (bloquea por `id`, recomprueba que
  sigue activo, vacío y sin exclusión, y usa `_a_papelera_si_vacios`;
  `{"a_papelera": n, "saltados": m}`): los usa el script de §4.5.

### 4.3 Portal (`static/app.js`, `app.py`)

- `.line-del`: si `d.documento_a_papelera`, avisa «El parte se ha quedado sin líneas y ha
  ido a la papelera.» y, si la página es `/partes/<document_id>`, va a `/partes`; si no,
  recarga. `doBorrar` (bloque) lee el JSON de cada respuesta y aplica lo mismo.
- `[data-restore-doc]` y `[data-restore-line]`: con `d.error`, `alert(d.error)`. Vaciar: con
  `d.documentos_a_papelera`, avisa de que N partes se quedaron sin líneas y siguen en la
  papelera.
- `app.py`: los dos restaurar capturan `DuplicadoActivoError` ⇒ 409 `{"ok": false, "error"}`;
  `api_registro_delete` devuelve el dict de `borrar_linea` (el 409 de congelación sigue
  llegando por su manejador global).

### 4.4 sv3 · deduplicación

- `get_by_sha256` rellena `registros_vivos` (`deleted_at_utc IS NULL`) y `aprobado`; sigue
  devolviendo solo partes activos.
- Pipeline, si hay `existing`: con `registros_vivos == 0` y no aprobado, INFO
  «`[persist-parte] sha256=… ya existe pero el parte está vacío (document_id=…): se
  reemplaza.`» y sigue con `reemplaza_vacio=existing.document_id`; si no, dedup como hoy. Si
  `save_parte` lanza `ParteYaNoVacio`, devuelve el `already_existed` de hoy sin conciliar (R13).
- `save_parte(..., reemplaza_vacio)`: al principio de su sesión, `select … with_for_update`
  del parte; si no existe, no está activo, tiene alguna línea viva o está aprobado ⇒
  `ParteYaNoVacio` sin escribir. Si no, papelera (`deleted_by="sv3-reingesta"`),
  `session.flush()` **antes** de crear el `ParteDocumentOrm` nuevo, e INFO `[parte-repo]
  reingesta: parte vacío <viejo> a la papelera, nuevo <nuevo>`. El resto (incluido
  `_deactivate_same_day_obra`) no cambia.

### 4.5 `limpiar_partes_vacios.py` (script de consola de sv4; uso en §9 M2)

- Conexión: `create_engine(settings.database_url)` + `sessionmaker` en una clase mínima con
  `create_session()`. **Sin `SessionFactory`**, que crea la base y entra en la de
  administración del servidor compartido (R18).
- Informe: en PostgreSQL, `SET TRANSACTION READ ONLY`; `partes_vacios_activos()` con
  `categoria_vacio` y `motivo_exclusion_limpieza`; escribe
  `logs/limpieza_partes_vacios_<AAAAMMDD-HHMM>.md` y `.csv`.
- `--ejecutar --esperados N`: si los candidatos no son N, código 2 sin escribir; si lo son,
  `vacios_a_papelera(ids, by="F-061-limpieza")` y lo imprime (script: `print` permitido).

## 5. SQL

Sin `.sql`, DDL ni tablas: ORM sobre la base `partes`. Nuevo: `FOR UPDATE` de filas de
`parte_documents` (nada de servidor) y la consulta de vacíos (la de la M0 de §9).

## 6. Tests (sin red ni BBDD; SQLite en memoria con `dobles.py`; `test_f061_rN_…`)

**sv4** (`services/partes-front/tests/`):
- `test_f061_borrado.py`: **R1** (última línea ⇒ papelera con actor y dict; con vivas
  ⇒ `false`; también por `TestClient`); **R2** (persona con congeladas ⇒ activo; persona o
  `_deshacer_creadas` que vacían ⇒ papelera); **R3** (`_sql_bloqueo_documentos` compilado en
  `postgresql` lleva `FOR UPDATE` y `ORDER BY parte_documents.id`; espía en `borrar_linea` y
  `soft_delete_worker`; dos borrados seguidos ⇒ papelera); **R4** (regresión).
- `test_f061_papelera.py`: **R5** (vaciar con un parte de líneas todas sueltas ⇒
  `documentos_a_papelera` = 1, parte inactivo con `deleted_at_utc`, sin `SAWarning` como
  F-010 R11); **R6–R8** (restaurar línea; parte vaciado ⇒ líneas vivas; otro activo con el
  mismo sha ⇒ 409 y nada escrito).
- `test_f061_portal.py`: **R9** (`app.js` maneja `documento_a_papelera`; `node --check`
  en la verificación); **R10** (`list_partes` cuenta solo vivas y `sin_lineas`; la plantilla
  pinta «Sin líneas»).
- `test_f061_limpieza.py`: **R14–R18** (categorías; las tres exclusiones; `--esperados`
  distinto ⇒ código 2 y nada escrito; `--ejecutar` sin `--esperados` ⇒ error de uso;
  ejecución ⇒ papelera con `F-061-limpieza` y ningún `DELETE`, con `before_cursor_execute`;
  no importa `SessionFactory`; el CSV no lleva nombres) y funciones puras de §4.1.

**sv3** (`services/partes-persistencia/tests/`):
- `test_f061_dedup_vacio.py`: **R11–R13** con el repositorio falso del pipeline (vacío
  ⇒ `reemplaza_vacio`; con vivas o aprobado ⇒ `already_existed`; `ParteYaNoVacio` ⇒
  `already_existed`) y con el repositorio real sobre SQLite (viejo en papelera con
  `sv3-reingesta`, nuevo activo y, por `before_cursor_execute`, el `UPDATE parte_documents`
  **antes** del `INSERT INTO parte_documents`).

**R19–R20**: tarea de límite (`git diff --stat dev`) y reviewer, no pytest.

## 7. Riesgos y decisiones

- **Abrazo mortal**: todo camino bloquea el parte antes de tocar líneas; varios, por `id`.
- **Restaurar contra el índice único**: ya podía pasar y F-061 lo hace más probable; R8 da
  un 409 legible en vez de un 500.
- **Parte nacido vacío y reentregado** (at-least-once): sv3 manda el primero a la papelera y
  guarda otro igual. Ruido, nada perdido; raro, se acepta.
- **`list_partes` cambia cifras** con líneas en la papelera: es corrección (semántica 3). Si
  un test viejo contaba con lo anterior, `blocked` y se consulta, sin tocarlo.
- **Vaciar deja partes en la papelera** (R5): red de seguridad, solo para partes previos.
- **El script escribe en producción**: lee por defecto, exige `--esperados`, recomprueba
  bajo bloqueo y lo autoriza el humano (§9).

## 8. Despliegue

**sv3 → sv4** (`redeploy_partes.ps1 -Solo svX`), a petición del humano. Sin variables ni
interruptor; rollback = imagen anterior (lo escrito es papelera lógica).

## 9. Verificación manual (base `partes`, nunca el servidor `psql-albaranes-rs9k2`)

**M0 · líder, antes de implementar, SOLO LECTURA**: partes vacíos de hoy por categoría y
exclusión, y restaurables que hoy chocarían.

```sql
BEGIN TRANSACTION READ ONLY;
WITH d AS (
  SELECT pd.id, COUNT(r.id) AS filas,
         COUNT(r.id) FILTER (WHERE r.deleted_at_utc IS NULL) AS vivas,
         COUNT(r.id) FILTER (WHERE lower(r.sigrid_estado) IN ('registrado','dedicacion','encolado')) AS fuera,
         COUNT(r.id) FILTER (WHERE r.sigrid_parte_cod IN ('PT26/00373','PT26/00375','PT26/00376')) AS protegidas
  FROM parte_documents pd LEFT JOIN parte_registros r ON r.document_id = pd.id
  WHERE pd.is_active GROUP BY pd.id)
SELECT CASE WHEN d.filas > 0 THEN 'todas_en_papelera'
            WHEN pd.source_mime_type = 'manual' THEN 'sin_filas_manual'
            WHEN jsonb_typeof(pd.raw_extraction_json::jsonb -> 'data' -> 'empleados') = 'array'
             AND jsonb_array_length(pd.raw_extraction_json::jsonb -> 'data' -> 'empleados') > 0
            THEN 'sin_filas_leidos' ELSE 'sin_filas_nada_leido' END AS categoria,
       pd.approved, d.fuera > 0 AS vive_fuera, d.protegidas > 0 AS protegido,
       COUNT(*) AS partes, MIN(pd.created_at_utc) AS primero, MAX(pd.created_at_utc) AS ultimo
FROM d JOIN parte_documents pd ON pd.id = d.id
WHERE d.vivas = 0 GROUP BY 1, 2, 3, 4 ORDER BY 1, 2, 3, 4;
SELECT COUNT(*) AS restaurables_que_chocarian
FROM parte_documents p JOIN parte_documents a
  ON a.source_sha256 = p.source_sha256 AND a.is_active AND a.id <> p.id
WHERE NOT p.is_active AND p.deleted_at_utc IS NOT NULL;
ROLLBACK;
```

Agregados (sin ids) a `progress/current.md`; algún aprobado o protegido ⇒ aviso antes de T1.

**M1 · humano, tras desplegar**: parte manual de prueba (obra 0404, día sin nada en
Sigrid, dos líneas): borrar una (sigue), la otra (aviso, `/partes`, papelera), restaurar el
parte (vuelve con las dos), borrarlo y vaciar. Sin registrar; PT26/00373/75/76 intactos.

**M2 · limpieza, autorizada por el humano de forma literal**, desde `services/partes-front`
con su `.env`: `../../.venv/Scripts/python.exe limpiar_partes_vacios.py` (informe en `logs/`)
y, leído, `… limpiar_partes_vacios.py --ejecutar --esperados <N>`; se repite la M0.

## 10. Decisiones abiertas

| DA | Tema | Opciones | Recomendación |
|---|---|---|---|
| DA1 | Parte que se queda sin líneas vivas | A) a la papelera de documento, como ya hace el borrado por persona. B) desactivarlo (`is_active=false` sin `deleted_at_utc`, como el reemplazo de sv3): invisible, sin restaurar desde el portal. C) dejarlo activo y que solo sv3 lo ignore | **A**: visible y recuperable (semántica 8); era ya la intención del código (`soft_delete_worker`, `restore_registro`) |
| DA2 | Restaurar | A) restaurar una línea devuelve el parte (como hoy); restaurar un parte vaciado devuelve también sus líneas; con otro activo del mismo sha, 409. B) restaurar el parte, solo el parte | **A**: con B, restaurar recrea el parte activo y vacío |
| DA3 | Vaciar la papelera | A) el parte que se queda sin filas va a la papelera y se avisa. B) borrarlo físicamente en la misma pasada. C) nada | **A**: no añade borrado físico y con R1 casi nunca ocurre |
| DA4 | Los existentes (36 el 2026-10-25) | A) script de sv4: informe y `--ejecutar --esperados N` a la papelera, con exclusiones. B) `UPDATE` a mano del líder. C) dejarlos | **A**, con las cuatro categorías: el informe las separa y el humano fija N; si quiere dejar fuera `sin_filas_nada_leido`, se añade un filtro |
| DA5 | Portal | A) contar solo vivas en `/partes` e insignia «Sin líneas». B) además, aviso en la cabecera con el número. C) nada | **A**: tras R1 y la limpieza casi no habrá; B es papeleo para un caso residual |
| DA6 | sv3 ante un parte vacío con el mismo sha | A) mandarlo a la papelera y guardar el nuevo, en la misma transacción. B) desactivarlo sin papelera. C) no tocar sv3 | **A**: la reingesta no depende de que el portal lo haya hecho bien; B esconde sus líneas en un parte invisible |
| DA7 | «Parte vacío» en dos servicios | A) definición única en ARCHITECTURE semántica 8; cada servicio la expresa como consulta (como los filtros `is_active` / `deleted_at_utc IS NULL` que ya repiten); no entra en la lista cerrada. B) entra en la lista cerrada con test gemelo | **A**: es un predicado del esquema compartido, no lógica de negocio |
| DA8 | Rigor | A) `estandar`. B) `critico` | **A**: papelera lógica, sin Sigrid ni cambios de servidor; la escritura en producción (M2) va por un script que lee por defecto y autoriza el humano |
