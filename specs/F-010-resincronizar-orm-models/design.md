<!-- specs/F-010-resincronizar-orm-models/design.md -->
# F-010 · Saneamiento: resincronizar `orm_models.py` entre sv3 y sv4 — Diseño

## 1. Servicios tocados y por qué (LÍMITE DE SERVICIO)

| Zona | Por qué |
|---|---|
| **sv3** `services/partes-persistencia` | Dueño de una de las dos copias toleradas de `orm_models.py` y de su `initialize()` (`sqlalchemy_parte_repository.py`). |
| **sv4** `services/partes-front` | Dueño de la otra copia y de su `initialize()` (`parte_repository.py`); además, R11 (cascadas en `hard_delete_document`/`vaciar_papelera`). |
| **Raíz** `tests/` | El guardián de gemelos: es una propiedad del monorepo (dos servicios), no de uno; la suite de la raíz ya valida estructura (`test_estructura_monorepo.py`) y `init.sh` la ejecuta siempre. |
| `docs/`, `azure-apps/partes.md` | Corrección documental (R12). |

No hay lógica nueva de dominio ni ninguna responsabilidad que pida un
servicio nuevo. La duplicación de `orm_models.py` **no crece** (sigue siendo
la lista cerrada del `CLAUDE.md`); al contrario, se hace verificable. La
función `ddl_complementario()` vive DENTRO de `orm_models.py` precisamente
para no crear una nueva pieza duplicada fuera de la lista cerrada: queda
cubierta por el mismo guardián.

## 2. Hechos del código que condicionan el diseño

1. **La BBDD real es la unión de las dos copias.** Comprobado en solo
   lectura (`information_schema.columns`, `pg_indexes`, `pg_constraint`)
   el 2026-08-18: 4 tablas; `parte_registros` tiene las 56 columnas de la
   unión con los tipos que declara el ORM (VARCHAR(n) / double precision /
   integer / boolean / text), sin nada de más ni de menos. Único desajuste
   ORM→BBDD: falta el índice `ix_parte_registros_deleted_at_utc` que ambas
   copias declaran (`index=True`). Tablas pequeñas (41 documentos, 104
   registros, 9 undo, 0 alias). PostgreSQL 16.
2. **Ninguna copia contiene nada que la BBDD no tenga.** Por tanto la
   resincronización es puramente declarativa: no hace falta ninguna
   sentencia que cambie datos ni columnas existentes.
3. **`create_all` no añade columnas ni índices a tablas ya existentes.**
   Por eso cada servicio arrastra su lista de `ALTER … ADD COLUMN IF NOT
   EXISTS`, escrita a mano y desincronizada: la de sv3 no cubre `sigrid_*`
   ni `deleted_*`; la de sv4 no cubre `horas_orig`/`extra_auto`. La forma
   de que no vuelva a pasar es **no escribirla a mano**: derivarla del
   ORM.
4. **sv3 no lee `sigrid_*` ni `undo_log`; sv4 no lee `horas_orig` ni
   `extra_auto`** (grep sin resultados en el otro servicio). La divergencia
   es inofensiva en runtime hoy: por eso lleva meses sin romper nada y por
   eso hay que arreglarla ahora, antes de que F-015 (`EmpleadoJornadaOrm` en
   las dos copias) y F-012 D7 (sv3 excluirá del re-split lo
   `registrado`/`encolado`, es decir, **sv3 leerá `sigrid_estado`**) la
   conviertan en un fallo real.
5. **Puntos de arranque que inicializan schema:** sv3
   `interface_adapters/api/app.py::build_app` → `repository.initialize()`
   (lo usan `main.py` y `main_worker.py`); sv4 `main.py` y
   `interface_adapters/web/app.py` → `repository.initialize()`. En tests
   nadie llama a `initialize()`: los dobles usan `Base.metadata.create_all`
   sobre SQLite (`services/partes-front/tests/dobles.py::FabricaSesionSqlite`,
   `services/partes-persistencia/tests/test_f003_r26_review_required.py`).
   SQLite no admite `ADD COLUMN IF NOT EXISTS`, así que `initialize()` se
   prueba con un `engine` doble que graba sentencias.
6. **Los 3 `SAWarning` de F-004** (`DELETE … expected to delete 1 row(s); 0
   were matched`) están reproducidos y diagnosticados: `_tiene_linea_registrada(doc)`
   carga `doc.registros` en la sesión; el `session.execute(delete(ParteRegistroOrm)…)`
   masivo los borra en SQL; después `session.delete(doc)` dispara la
   cascada `all, delete-orphan` sobre los objetos aún cargados y SQLAlchemy
   emite un `DELETE` por fila que no encuentra nada. Se arregla quitando el
   `DELETE` masivo (la cascada ya borra las líneas). Es código de sv4, no
   schema; se incluye porque el reviewer de F-004 lo dejó anotado para
   F-010 (decisión D4).
7. **Guardianes previos que se imitan:** F-002 R11
   (`services/partes-transfer/tests/test_f002_r11_sin_postgresql.py`,
   propiedad negativa comprobada con `ast`) y F-003 R8
   (`test_f003_r8_el_cliente_de_sv3_es_gemelo_del_de_sv4`, compara el
   fuente de las clases contra el fichero gemelo con `inspect.getsource`).
   Para `orm_models.py` se puede exigir más: **byte-idéntico**, porque la
   ruta relativa (primera línea) y el docstring pueden ser los mismos.

## 3. Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `services/partes-persistencia/infrastructure/database/orm_models.py` | Contenido canónico (§6.1): añade el bloque `sigrid_*` (7 columnas, mismo sitio que en sv4: tras `parte_estado`, antes del bloque «CODIGO DE HORA»), la clase `UndoLogOrm`, `ddl_complementario()`, `DDL_EXTRA_POSTGRES`; docstring «cuatro tablas». |
| `services/partes-front/infrastructure/database/orm_models.py` | Se sustituye por el MISMO contenido (byte-idéntico): gana `horas_orig`, `extra_auto`, los comentarios de sv3, `ddl_complementario()`, `DDL_EXTRA_POSTGRES`. |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | `initialize()` ejecuta `ddl_complementario()`; se borran `_DDL_PARTIAL_UNIQUE` y `_DDL_ALTERS`. Import de `ddl_complementario` desde `orm_models`. Nada más del fichero cambia. |
| `services/partes-front/infrastructure/database/parte_repository.py` | `initialize()` ejecuta `ddl_complementario()` (mismo `try/except` → `True/False`); se borran los `ALTER`, `CREATE TABLE IF NOT EXISTS empleado_alias/undo_log` y el parche `undo_log.actor` a mano. `hard_delete_document` y `vaciar_papelera`: quitar los `session.execute(delete(ParteRegistroOrm).where(document_id == …))` (R11); el import `delete` de sqlalchemy se conserva si lo usan otros métodos (comprobar). |
| `docs/ARCHITECTURE.md` | Punto 7 de «Semántica de dominio»: cuatro tablas, copias byte-idénticas con guardián en `tests/`, DDL complementario generado del ORM y aplicado por sv3 y sv4. |
| `docs/referencia/partes-proyecto.md` | §5 (cabecera «Tres tablas», §5.1 `confianza_pct`, §5.2 filas Identidad/Trabajador leído/Fecha/Aprobación-papelera, nuevo §5.4 `undo_log`; renumerar «Datos que NO están» a §5.5) + nota de corrección con fecha en la cabecera del documento (D5). |
| `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` | §4, misma corrección (repositorio aparte; commit local allí, sin push: es un repo local por decisión del humano). |

## 4. Ficheros a crear

| Fichero | Contenido |
|---|---|
| `tests/test_f010_orm_models_gemelos.py` | Guardián R1–R4: `RUTAS = (sv3, sv4)`; `_cargar(ruta, nombre)` con `importlib.util.spec_from_file_location`; `_huella(metadata) -> dict` (tabla → columna → `{tipo: str(col.type.compile(dialect=postgresql.dialect())), nullable, pk, server_default: texto o None, index, unique}` + `indices: {nombre: (columnas, unique)}`); tests R1 (bytes + `difflib.unified_diff` en el mensaje), R2 (huellas iguales; mensaje con `set` simétrico de diferencias), R3 (copias en `tmp_path` alteradas → la comparación falla nombrando el elemento), R4 (56 columnas literales en `parte_registros`, 4 tablas, atributos clave). |
| `services/partes-persistencia/tests/test_f010_r6_ddl_complementario.py` | R6, R9, R10 sobre `Base.metadata` real y sobre un `MetaData` de juguete. |
| `services/partes-persistencia/tests/test_f010_r7_initialize_sv3.py` | R7 con `SessionFactory` doble (`engine` grabador; `Base.metadata.create_all` parcheado con `monkeypatch` para registrar la llamada). |
| `services/partes-front/tests/test_f010_r8_initialize_sv4.py` | R8: mismo doble; caso de fallo → `False`. |
| `services/partes-front/tests/test_f010_r11_borrado_sin_sawarning.py` | R11: `warnings.simplefilter("error", SAWarning)`; usa `dobles.FabricaSesionSqlite` + `sembrar_registros`. |

## 5. Ficheros que NO se tocan

- `CLAUDE.md` (la lista cerrada de duplicación tolerada no cambia),
  `CHECKPOINTS.md`, `harness/*`, `specs/SPECS.md`.
- `services/partes-front/tests/dobles.py` (se reutiliza tal cual; si hace
  falta un sembrador con documento en papelera, se define en el test).
- Cualquier fichero de sv1, sv2, sv5 e `infra/` (incluidos los
  manifiestos: no hay variable de entorno nueva).
- `application/`, `domain/`, `interface_adapters/` de sv3 y sv4: no cambia
  ningún lector ni escritor de columnas; solo declaración y arranque.
- Los `.env` / `.env.example`.
- La FK `parte_registros.document_id` y el índice único parcial: se
  conservan tal cual (el índice pasa a `DDL_EXTRA_POSTGRES` con el mismo
  texto).

## 6. Clases y funciones (capa `infrastructure` en ambos servicios)

### 6.1 `orm_models.py` (contenido canónico, byte-idéntico)

Orden y contenido:

1. Cabecera `# infrastructure/database/orm_models.py` + docstring del
   módulo (texto de sv3 ampliado: «cuatro tablas», `undo_log` la escribe
   sv4; explica que el DDL complementario se genera aquí y por qué las dos
   copias deben ser byte-idénticas: guardián `tests/test_f010_*`).
2. Imports: los actuales + `from sqlalchemy import MetaData` +
   `from sqlalchemy.dialects import postgresql` +
   `from sqlalchemy.schema import CreateColumn, CreateIndex`.
3. `Base`, `ParteDocumentOrm` (sin cambios), `ParteRegistroOrm` = la de
   sv3 (comentarios incluidos) + el bloque de sv4:

   ```python
   # --- Traza del REGISTRO en Sigrid (la escribe sv4 al aprobar / al
   # volcar q-transfer-result; sv5 hace la escritura real en el ERP;
   # sv3 la lee para no recomputar lo registrado/encolado — F-012 D7). --- #
   sigrid_estado: Mapped[str | None] = mapped_column(String(16))
   sigrid_registrado_at_utc: Mapped[str | None] = mapped_column(String(64))
   sigrid_registrado_by: Mapped[str | None] = mapped_column(String(255))
   sigrid_hmoide: Mapped[int | None] = mapped_column(Integer)
   sigrid_hmores_ide: Mapped[int | None] = mapped_column(Integer)
   sigrid_parte_cod: Mapped[str | None] = mapped_column(String(64))
   sigrid_motivo: Mapped[str | None] = mapped_column(String(255))
   ```

   colocado, como en sv4, entre `parte_estado` y el bloque «CODIGO DE HORA»
   (el orden de declaración no afecta a la BBDD existente; se elige el de
   sv4 para minimizar el diff de la copia que más lectores tiene).
   `EmpleadoAliasOrm` sin cambios. `UndoLogOrm` = la de sv4 tal cual (sin
   `server_default` en `undone`: la BBDD real no lo tiene, y el ORM
   describe la BBDD).
4. Constante y función:

   ```python
   #: DDL PostgreSQL que el ORM no sabe expresar de forma portable y que
   #: ambos servicios aplican al arrancar (idempotente por IF NOT EXISTS).
   DDL_EXTRA_POSTGRES: tuple[str, ...] = (
       "CREATE UNIQUE INDEX IF NOT EXISTS ux_parte_documents_sha256_active "
       "ON parte_documents (source_sha256) WHERE is_active",
   )

   def ddl_complementario(metadata: MetaData = Base.metadata) -> tuple[str, ...]:
       """DDL idempotente que completa tablas YA existentes tras
       `create_all` (que no añade columnas ni índices a una tabla creada):
       un ADD COLUMN IF NOT EXISTS por columna no primaria, un CREATE INDEX
       IF NOT EXISTS por índice declarado y `DDL_EXTRA_POSTGRES`. Función
       pura: compila contra el dialecto PostgreSQL sin conexión. Se genera
       del ORM para que no exista una segunda lista, escrita a mano, que
       pueda divergir (F-010)."""
       dialecto = postgresql.dialect()
       sentencias: list[str] = []
       for tabla in sorted(metadata.tables.values(), key=lambda t: t.name):
           for columna in tabla.columns:
               if columna.primary_key:
                   continue
               definicion = str(CreateColumn(columna).compile(dialect=dialecto))
               sentencias.append(
                   f"ALTER TABLE {tabla.name} ADD COLUMN IF NOT EXISTS {definicion}")
           for indice in sorted(tabla.indexes, key=lambda i: i.name):
               sentencias.append(
                   str(CreateIndex(indice, if_not_exists=True).compile(dialect=dialecto)))
       sentencias.extend(DDL_EXTRA_POSTGRES)
       return tuple(sentencias)
   ```

   Comprobado en el venv (SQLAlchemy 2.0.52): `CreateColumn` compila
   `extra_auto BOOLEAN DEFAULT 'false' NOT NULL`, `horas_orig FLOAT`,
   `sigrid_estado VARCHAR(16)`, `sharepoint_url TEXT`; `CreateIndex(…,
   if_not_exists=True)` compila `CREATE INDEX IF NOT EXISTS
   ix_parte_registros_deleted_at_utc ON parte_registros (deleted_at_utc)`.
   `FLOAT` sin precisión es `double precision` en PostgreSQL y `DEFAULT
   'false'` es válido para `boolean`; en columnas ya existentes la
   sentencia es un no-op, así que la equivalencia solo importa para
   columnas futuras.

   Sobre las columnas `NOT NULL` sin `server_default` (`document_id`,
   `line_index`, `created_at_utc`, `action`, …): son de la creación
   original de cada tabla y siempre existen ⇒ no-op. Si en el futuro
   alguien añade una columna `NOT NULL` sin default a una tabla con filas,
   el `ALTER` fallará **en voz alta** al arrancar (PostgreSQL rechaza), que
   es lo deseable frente a un default inventado; el docstring lo avisa.

### 6.2 `SqlAlchemyParteRepository.initialize()` (sv3)

```python
def initialize(self) -> None:
    engine = self._session_factory.engine
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        for ddl in ddl_complementario():
            connection.execute(text(ddl))
    logger.info("[parte-repo] esquema inicializado (%s sentencias complementarias).", n)
```

### 6.3 `ParteReviewRepository.initialize()` (sv4)

Mismo cuerpo dentro del `try/except Exception` actual (`return True` /
`logger.exception(...)` + `return False`). Desaparecen ~80 líneas de DDL a
mano.

### 6.4 `hard_delete_document` / `vaciar_papelera` (sv4, R11)

Quitar el `session.execute(delete(ParteRegistroOrm).where(...))` que
precede a `session.delete(doc)` en ambos métodos. La relación
`ParteDocumentOrm.registros` tiene `cascade="all, delete-orphan"`: al
borrar el documento SQLAlchemy carga (si no lo estaban) y borra sus líneas.
Coste: un `DELETE` por línea en vez de uno masivo; un parte tiene decenas
de líneas y la papelera se vacía a mano; irrelevante. La rama de líneas
sueltas de `vaciar_papelera` (`session.delete(r)`) no cambia.

### 6.5 Guardián (raíz `tests/`)

Puro sistema de ficheros + SQLAlchemy sin conexión: cumple «sin red ni
BBDD». Carga cada copia como módulo independiente por ruta (cada una
define su propio `Base`, no colisionan). La huella semántica compila el
tipo al dialecto PostgreSQL para que `String(64)` ≠ `String(65)` y
`Float` ≠ `Integer` salgan como texto legible. R3 demuestra que el
guardián muerde alterando copias en `tmp_path` (misma técnica que
`test_estructura_monorepo.py`: nunca se toca el árbol real). Esto es
además la **fase RED exigible por CHECKPOINTS** cuando el entregable es el
propio test; y R1/R2 tienen además una RED natural: **hoy fallan** contra
el árbol real porque las copias divergen (traza para `impl_F-010.md`).

## 7. SQL

No hay ficheros `NN_nombre.sql`: el schema de `partes` lo gestiona el ORM
(`create_all`) más el DDL complementario de arranque, y así sigue. Todo el
SQL que emite F-010 es el generado por `ddl_complementario()` (§6.1), todo
`IF NOT EXISTS`, contra la base `partes` únicamente. **Cambio físico
esperado en la BBDD real al desplegar:** solo `CREATE INDEX IF NOT EXISTS
ix_parte_registros_deleted_at_utc` (D3). Todo lo demás es no-op.

## 8. Riesgos y decisiones

### Decisiones tomadas (con alternativas descartadas)

- **D1 · Copia canónica = la UNIÓN, no una de las dos.** Ninguna copia es
  «la buena»: sv3 tiene lo que escribe sv3 y sv4 lo que escribe sv4, y la
  BBDD real tiene ambas cosas. Se toma como base textual la de sv3
  (comentarios más ricos) y se le injerta el bloque `sigrid_*` y
  `UndoLogOrm` de sv4. Descartado «sv4 manda» (perdería los comentarios
  que explican quién escribe cada bloque) y «sv3 manda» (perdería
  `UndoLogOrm`, que sv4 usa).
- **D2 · DDL complementario generado del ORM, dentro de `orm_models.py`.**
  Alternativa descartada: una tupla a mano idéntica en los dos servicios
  (seguiría siendo una segunda declaración que puede olvidarse: es
  exactamente lo que ha pasado). Alternativa descartada: Alembic (una
  herramienta y una carpeta de migraciones para 4 tablas de ~100 filas, y
  otra pieza duplicada o compartida entre sv3 y sv4). Riesgo del
  generador: que compile algo distinto de lo que se escribiría a mano —
  mitigado con R6 (aserciones literales sobre las sentencias) y con que
  sobre columnas existentes es no-op.
- **D3 · El índice `ix_parte_registros_deleted_at_utc` se crea** (vía el
  generador) en vez de quitar `index=True` del ORM. Motivo: el ORM debe
  describir la BBDD y ambas copias ya lo declaran; `deleted_at_utc` se
  filtra en la papelera (sv4) y en las exclusiones de conciliación (sv3);
  tabla de 104 filas ⇒ creación instantánea, sin bloqueo apreciable, en la
  base `partes` (nada a nivel de servidor). **Requiere el visto bueno del
  humano** por ser el único cambio físico en el PostgreSQL compartido; si
  lo rechaza, la alternativa es quitar `index=True` en las dos copias (y R6
  deja de esperar ese `CREATE INDEX`).
- **D4 · R11 (SAWarning) se incluye** como higiene mínima de sv4 porque el
  reviewer de F-004 lo dejó explícitamente para F-010, el diagnóstico está
  hecho y el arreglo son dos borrados de líneas sin tocar schema (la
  alternativa «`ondelete=CASCADE` + `passive_deletes`» sí tocaría la FK
  real: descartada). Si el humano prefiere sacarlo, se elimina T6 y R11 sin
  afectar al resto.
- **D5 · Corrección documental en `partes-proyecto.md` §5 y
  `azure-apps/partes.md` §4.** Es el documento maestro del humano: se
  corrige **en el sitio** (no una nota al pie), añadiendo a la cabecera una
  línea «Corregido el 2026-08-XX por F-010: §5 (esquema real de la BBDD)».
  Alternativa descartada: dejar la descripción errónea con un aviso (un
  documento que parece vigente y no lo es hace más daño que no tenerlo —
  regla del `CLAUDE.md`). Aplica C3 bis (barrido de datos sensibles: la
  corrección no añade ninguno). **Requiere el visto bueno del humano** por
  ser su documento.
- **D6 · Sin cambio de comportamiento ante fallo de `initialize()`**: sv3
  sigue propagando (el worker no arranca con schema roto) y sv4 sigue
  devolviendo `False` (el portal enseña «tablas no listas»). Unificarlo es
  otra feature.
- **D7 · Los tests de `initialize()` usan un `engine` doble**, no SQLite,
  porque SQLite no acepta `ADD COLUMN IF NOT EXISTS`. Se comprueba la
  secuencia de sentencias, que es lo que importa; la ejecución real contra
  PostgreSQL es la verificación MANUAL del humano (arranque local de sv3 y
  sv4 y consulta de `pg_indexes`).

### Riesgos

- **Orden de columnas distinto entre ORM y BBDD.** Irrelevante: SQLAlchemy
  nombra columnas en cada sentencia; el orden físico de la tabla no cambia.
- **Mutación (rigor `estandar`).** Los mutantes en `orm_models.py` de una
  copia los mata R1 (byte-idéntico); los del generador, R6/R9/R10; los de
  `initialize()`, R7/R8; los de los borrados, R11 + los tests R12/R18 de
  F-004. Posibles supervivientes triviales: cambios en textos de `logger`
  (documentar).
- **Cobertura de líneas cambiadas por servicio.** El generador vive en las
  dos copias; en sv3 lo cubren R6/R7 y en sv4 R8 (que ejecuta
  `ddl_complementario()` de la copia de sv4). Las líneas de declaración
  del ORM se ejecutan al importar el módulo (cualquier test de cada
  servicio).
- **F-015 después de F-010.** F-015 añadirá `EmpleadoJornadaOrm` a las dos
  copias: con F-010, la tabla nueva la crea `create_all` en el servicio
  que arranque primero, sus columnas quedan cubiertas por el generador sin
  escribir DDL y el guardián obliga a tocar las dos copias. Es lo que D6
  de F-012 pedía.

## 9. Decisiones abiertas que debe validar el humano

1. **D3** — ¿Se crea el índice `ix_parte_registros_deleted_at_utc` en la
   BBDD real (único cambio físico de F-010; tabla de 104 filas) o se quita
   `index=True` del ORM? Recomendación: crearlo.
2. **D4** — ¿Se incluye R11 (arreglo de los `SAWarning` en
   `hard_delete_document`/`vaciar_papelera`, solo código sv4)?
   Recomendación: sí.
3. **D5** — ¿Se corrige en el sitio §5 de `docs/referencia/partes-proyecto.md`
   (documento del humano) y §4 de `azure-apps/partes.md`, con línea de
   corrección en la cabecera? Recomendación: sí.
4. **D2** — ¿Conforme con generar el DDL complementario desde el ORM
   (función en `orm_models.py`) en vez de mantener una lista a mano
   idéntica en los dos servicios? Recomendación: generar.

Todo lo demás (D1, D6, D7) son decisiones de diseño sin impacto fuera del
código y no necesitan validación expresa.

## 10. Encaje en `docs/ARCHITECTURE.md`

Refuerza el punto 7 («Schema PostgreSQL duplicado a propósito») sin
cambiar la arquitectura: sigue sin haber librería compartida, los servicios
siguen acoplados solo por la BBDD, y la duplicación tolerada pasa de ser
una promesa a ser una propiedad verificada por `init.sh`. Hexagonal
respetada: todo lo tocado es `infrastructure/database/` más tests y docs.
