<!-- specs/F-010-resincronizar-orm-models/requirements.md -->
# F-010 · Saneamiento: resincronizar `orm_models.py` entre sv3 y sv4 — Requisitos (EARS)

Alcance: la duplicación tolerada de `infrastructure/database/orm_models.py`
(sv3 `services/partes-persistencia` y sv4 `services/partes-front`) está
desincronizada y el DDL complementario de arranque («`ALTER TABLE … ADD
COLUMN IF NOT EXISTS`») está escrito a mano y distinto en cada servicio.
F-010 deja las dos copias **byte-idénticas** y fieles al schema real de la
BBDD `partes`, hace que el DDL complementario **se derive del propio ORM**
(no puede volver a divergir) y añade un **guardián** que falla si las copias
se separan. Es prerrequisito de F-015 (D6 de F-012), que añadirá
`EmpleadoJornadaOrm` a las dos copias.

Servicios tocados: **sv3 y sv4** (los dos dueños de la duplicación
tolerada; quien toca una copia cambia las dos) y la suite de la **raíz del
monorepo** (`tests/`, donde vive el guardián: es una propiedad del
monorepo, no de un servicio). Ningún cambio en sv1, sv2, sv5 ni infra.

Vocabulario: «copia» = uno de los dos `orm_models.py`; «DDL
complementario» = las sentencias idempotentes que cada servicio ejecuta
al arrancar después de `Base.metadata.create_all()` para completar tablas
que ya existían.

## Estado real hoy (hechos verificados el 2026-08-18, base `partes` en solo lectura)

- BBDD real: **cuatro** tablas (`parte_documents` 47 col., `parte_registros`
  56 col., `empleado_alias` 7 col., `undo_log` 7 col.). La UNIÓN de las dos
  copias del ORM coincide columna a columna con la BBDD (nombres, tipos,
  nullable, defaults). Ninguna copia contiene nada que no exista en la BBDD.
- sv3 declara `horas_orig`, `extra_auto` (que sv4 no declara); sv4 declara
  las 7 `sigrid_*` y `UndoLogOrm` (que sv3 no declara). Los comentarios de
  `parte_registros` difieren (sv3 más ricos).
- Las dos copias declaran `deleted_at_utc` de `parte_registros` con
  `index=True`, pero el índice `ix_parte_registros_deleted_at_utc` **no
  existe** en la BBDD (la columna entró por `ALTER TABLE` y `create_all`
  no crea índices sobre tablas ya existentes).
- El DDL complementario de sv3 (`_DDL_ALTERS`) no cubre `sigrid_*` ni
  `deleted_*`; el de sv4 no cubre `horas_orig`/`extra_auto`. Además sv4
  crea a mano `empleado_alias` y `undo_log` con `CREATE TABLE IF NOT
  EXISTS` aunque `create_all` ya lo hace.
- `docs/referencia/partes-proyecto.md` §5 y `azure-apps/partes.md` §4
  describen columnas de `parte_registros` que no existen (`approved*`,
  `is_active`, `page_number`, `created_at_utc`, `created_by`,
  `nombre_norm`), un índice en `fecha_int` que no existe, `confianza_pct`
  en `parte_documents` (no existe; existe `firma_confianza_pct`) y «tres
  tablas» (son cuatro).

## Copias gemelas

- **R1** (ubicuo). El sistema debe mantener las dos copias de
  `orm_models.py` **byte-idénticas** (mismo contenido; la primera línea
  —el comentario de ruta relativa— coincide en ambas porque la ruta
  relativa al servicio es la misma).
  *Test:* `test_f010_r1_las_dos_copias_son_byte_identicas` (en
  `tests/test_f010_orm_models_gemelos.py`) lee los dos ficheros
  y exige igualdad; si difieren, el mensaje de fallo enseña el `unified
  diff`.
- **R2** (ubicuo). El sistema debe mantener las dos copias
  **semánticamente equivalentes**: mismo conjunto de tablas
  (`__tablename__`), y por tabla mismas columnas con el mismo tipo
  (compilado al dialecto PostgreSQL), `nullable`, `primary_key`,
  `server_default`, `index` y `unique`; y mismos índices declarados.
  *Test:* `test_f010_r2_las_dos_copias_declaran_el_mismo_schema` (mismo
  fichero) carga cada copia por
  ruta con `importlib` (módulos independientes, cada uno con su `Base`),
  normaliza `Base.metadata` a un diccionario comparable y exige igualdad;
  el mensaje de fallo enumera qué tabla/columna/atributo difiere. R2 es
  el diagnóstico legible; R1 la barrera final (R1 implica R2, no al revés).
- **R3** (comportamiento no deseado). SI una copia declara una columna,
  un tipo, un nullable, un default, un índice o una tabla que la otra no
  declara, ENTONCES la suite de la raíz (`bash harness/init.sh`) debe
  fallar con un mensaje que nombre el elemento divergente.
  *Test:* `test_f010_r3_el_guardian_detecta_una_copia_alterada`
  (parametrizado, mismo fichero) copia las
  dos copias a un directorio temporal, altera UNA (añade una columna;
  cambia `String(64)` por `String(65)`; quita `index=True`; quita una
  clase) y comprueba que la comparación de R2 **falla** nombrando el
  elemento. Nunca toca el árbol real.

## Contenido canónico tras la resincronización

- **R4** (ubicuo). El sistema debe declarar en AMBAS copias la unión de lo
  que hoy declara cada una y nada más: `ParteDocumentOrm` (47 columnas, sin
  cambios), `ParteRegistroOrm` con `horas_orig`, `extra_auto` **y** las 7
  `sigrid_*` (56 columnas), `EmpleadoAliasOrm` (sin cambios) y `UndoLogOrm`
  (7 columnas). Ningún tipo, nullable, default ni `__tablename__` cambia
  respecto a lo que hoy declara la copia que ya tenía la columna.
  *Test:* `test_f010_r4_el_orm_canonico_tiene_las_cuatro_tablas_y_56_columnas`
  (mismo fichero) comprueba sobre la
  copia de sv3 (y por R1 sobre la de sv4) que las cuatro tablas existen y
  que `parte_registros` tiene exactamente las 56 columnas esperadas
  (lista literal en el test) con `horas_orig` Float nullable, `extra_auto`
  Boolean NOT NULL server_default `false`, `sigrid_estado` String(16),
  `sigrid_hmoide` Integer, etc.
- **R5** (ubicuo). El sistema debe conservar en las dos copias los
  comentarios de conciliación de sv3 (los más ricos: quién escribe y quién
  lee cada bloque) y el bloque de traza Sigrid de sv4; el docstring del
  módulo debe decir «cuatro tablas» y nombrar `undo_log` (solo la escribe
  sv4).
  *Test:* cubierto por R1 (contenido idéntico) más revisión del reviewer
  (C3); no se testea el texto de un comentario.

## DDL complementario derivado del ORM

- **R6** (ubicuo). El sistema debe exponer en `orm_models.py` (las dos
  copias) una función pura `ddl_complementario(metadata=Base.metadata) ->
  tuple[str, ...]` que, sin conexión alguna, devuelva en orden
  determinista: para cada tabla (orden alfabético) y cada columna **no
  primaria** (orden de declaración) una sentencia `ALTER TABLE <tabla> ADD
  COLUMN IF NOT EXISTS <columna compilada al dialecto PostgreSQL>` (tipo,
  `NOT NULL` y `DEFAULT` según la declaración); para cada índice declarado
  (`index=True`, orden alfabético por nombre) un `CREATE INDEX IF NOT
  EXISTS …` compilado; y por último las sentencias de la constante
  `DDL_EXTRA_POSTGRES` (hoy solo el índice único parcial
  `ux_parte_documents_sha256_active … WHERE is_active`).
  *Tests:* `services/partes-persistencia/tests/test_f010_r6_ddl_complementario.py`
  (y por R1 vale para sv4): (a) sobre `Base.metadata` real, contiene
  `ALTER TABLE parte_registros ADD COLUMN IF NOT EXISTS extra_auto BOOLEAN
  DEFAULT 'false' NOT NULL`, `… sigrid_estado VARCHAR(16)`, `… horas_orig
  FLOAT`, `ALTER TABLE undo_log ADD COLUMN IF NOT EXISTS actor
  VARCHAR(120)`, `CREATE INDEX IF NOT EXISTS ix_parte_registros_deleted_at_utc
  ON parte_registros (deleted_at_utc)` y el índice parcial; (b) NO contiene
  ninguna sentencia para columnas primarias (`id`, `nombre_norm`); (c)
  sobre un `MetaData` de juguete de dos tablas, el orden y el conteo son
  exactamente los esperados (`len == columnas no PK + índices +
  len(DDL_EXTRA_POSTGRES)`); (d) toda sentencia contiene `IF NOT EXISTS`
  (idempotencia por construcción).
- **R7** (dirigido por evento). CUANDO sv3 ejecuta
  `SqlAlchemyParteRepository.initialize()`, el sistema debe ejecutar
  `Base.metadata.create_all(engine)` y después, en UNA transacción, cada
  sentencia de `ddl_complementario()` en ese orden; la tupla `_DDL_ALTERS`
  y la constante `_DDL_PARTIAL_UNIQUE` escritas a mano desaparecen de
  `sqlalchemy_parte_repository.py`.
  *Test:* `services/partes-persistencia/tests/test_f010_r7_initialize_sv3.py`
  con un `SessionFactory` doble cuyo `engine` graba las sentencias
  ejecutadas (sin BBDD): las sentencias grabadas son exactamente
  `ddl_complementario()`, en orden, y `create_all` se invocó antes.
- **R8** (dirigido por evento). CUANDO sv4 ejecuta
  `ParteReviewRepository.initialize()`, el sistema debe hacer lo mismo que
  R7 (mismo generador, mismo orden) y conservar su contrato actual: devuelve
  `True` si todo fue bien y `False` (con `logger.exception`) si algo falla;
  los `ALTER`, `CREATE TABLE IF NOT EXISTS empleado_alias/undo_log` y el
  parche de `undo_log.actor` escritos a mano desaparecen de
  `parte_repository.py`.
  *Test:* `services/partes-front/tests/test_f010_r8_initialize_sv4.py`:
  mismo doble que R7; además, un `engine` cuyo `begin()` lanza → devuelve
  `False` sin propagar.
- **R9** (ubicuo). El sistema debe garantizar que el DDL complementario
  cubre TODA columna no primaria de TODA tabla del ORM: no puede existir
  una columna declarada en `orm_models.py` sin su `ADD COLUMN IF NOT
  EXISTS` (es la propiedad que hoy incumplen las dos listas a mano).
  *Test:* `test_f010_r9_toda_columna_tiene_su_alter` (en el fichero de
  R6): para cada tabla y columna no PK de `Base.metadata`, existe una
  sentencia que empieza por `ALTER TABLE <tabla> ADD COLUMN IF NOT EXISTS
  <columna> `.

## Efecto sobre la BBDD real (solo lo idempotente)

- **R10** (comportamiento no deseado). SI el DDL complementario se ejecuta
  contra una BBDD que ya tiene todas las columnas, ENTONCES el sistema NO
  debe modificar ninguna columna existente (ni tipo, ni nullable, ni
  default): todas las sentencias son `IF NOT EXISTS`, y ninguna es `ALTER
  COLUMN`, `DROP`, `RENAME` ni `CREATE TABLE` sin `IF NOT EXISTS`.
  *Test:* `test_f010_r10_ddl_solo_aditivo` (en el fichero de R6): ninguna
  sentencia contiene `ALTER COLUMN`, `DROP `, `RENAME `, `TRUNCATE`,
  `DELETE `, `UPDATE `; todas contienen `IF NOT EXISTS`.
  *MANUAL (humano):* el único cambio físico esperado en la BBDD `partes`
  al desplegar F-010 es la creación del índice
  `ix_parte_registros_deleted_at_utc` (tabla de 104 filas; instantáneo).
  Ver decisión D3 en `design.md` y el comando en `tasks.md`.

## Higiene colateral en sv4 (cascadas del ORM)

- **R11** (dirigido por evento). CUANDO sv4 ejecuta `hard_delete_document`
  o `vaciar_papelera`, el sistema debe borrar las líneas del documento por
  la **cascada del ORM** (`session.delete(doc)` con `cascade="all,
  delete-orphan"`), sin el `DELETE` masivo previo, de modo que no se emita
  ningún `SAWarning: DELETE statement … 0 were matched` y el resultado
  (documento y líneas borrados; congelados omitidos según F-004 R12) sea el
  mismo. Es una corrección de código en el repositorio de sv4, no de
  schema; el motivo del aviso es que el `DELETE` masivo borra filas que la
  sesión ya tiene cargadas (por `_tiene_linea_registrada`) y la cascada
  intenta borrarlas de nuevo.
  *Test:* `services/partes-front/tests/test_f010_r11_borrado_sin_sawarning.py`:
  con `warnings.simplefilter("error", SAWarning)` activo, `hard_delete_document`
  y `vaciar_papelera` sobre datos sembrados (SQLite, `tests/dobles.py`)
  terminan sin excepción y dejan la BBDD como esperan los tests R12/R18 de
  F-004 (que siguen en verde). Fase RED real: hoy el test falla con la
  traza del `SAWarning`.

## Documentación

- **R12** (ubicuo). El sistema debe describir en `docs/ARCHITECTURE.md`
  (punto 7 de la semántica de dominio) que son **cuatro** tablas
  (`undo_log` solo la escribe sv4), que las dos copias son byte-idénticas
  con guardián en `tests/`, y que el DDL complementario se genera del ORM
  y lo aplican **sv3 y sv4** al arrancar. Y debe corregir §5 de
  `docs/referencia/partes-proyecto.md` y §4 de `azure-apps/partes.md`
  (columnas inexistentes, índices, número de tablas, `undo_log`), dejando
  constancia de la corrección y su fecha en la cabecera del documento
  maestro (según decisión D5).
  *Test:* sin test automático (documental); lo verifica el reviewer (C3 y
  C3 bis: barrido de datos sensibles sobre `docs/referencia/`).

## Fuera de alcance (explícito)

- Cambiar tipos, nombres o nullabilidad de ninguna columna existente;
  añadir columnas nuevas (`EmpleadoJornadaOrm` es F-015); borrar columnas.
- Migraciones con herramienta (Alembic) o cambios a nivel de servidor del
  PostgreSQL compartido.
- Alterar la FK `parte_registros.document_id` (por ejemplo `ON DELETE
  CASCADE` + `passive_deletes`): sería una migración de constraint sobre
  la BBDD real; la cascada del ORM basta (R11).
- Unificar el comportamiento ante fallo de `initialize()` (sv3 propaga,
  sv4 devuelve `False`): se conserva tal cual.
- Cualquier cambio en sv1, sv2, sv5 o `infra/`.
