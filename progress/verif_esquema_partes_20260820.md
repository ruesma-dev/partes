# Verificación del esquema de la base `partes` tras el despliegue del 2026-08-20

- **Fecha**: 2026-08-20
- **Despliegue verificado**: sv3 + sv4 desde `dev`, revisión `r20260820000737`
  (2026-08-20 00:10). Lleva F-015 (tabla `empleado_jornada`), F-016
  (pantalla `/admin/jornadas`, sin cambios de schema) y el DDL pendiente de
  F-010, que sv3/sv4 aplican al arrancar.
- **Base consultada**: `partes` en `psql-albaranes-rs9k2`, PostgreSQL 16.14.
- **Alcance**: SOLO LECTURA. Ni un DDL, `INSERT`, `UPDATE` o `DELETE`; la
  sesión se abrió con `SET default_transaction_read_only = on`. No se ha
  tocado nada a nivel del servidor compartido.

---

## 0. VEREDICTO FINAL: **CONFORME**

**El esquema de la base coincide exactamente con lo que declaran las dos
copias de `orm_models.py` y con lo que exige la spec de F-015. Cero
discrepancias.**

| Comprobación | Resultado |
|---|---|
| `empleado_jornada` existe con **19 columnas** | ✅ 19/19, nombre, tipo, nullabilidad y `DEFAULT` correctos |
| Índice `ix_empleado_jornada_dni_norm` sobre `(dni_norm)`, no único | ✅ existe |
| PK `empleado_jornada_pkey` sobre `(id)` con secuencia | ✅ existe |
| CHECKs en `empleado_jornada` | ✅ **ninguno — que es lo correcto** (§2.3) |
| F-010 M1 · `ix_parte_registros_deleted_at_utc` | ✅ existe |
| F-010 M1 · recuentos 7 / 47 / 56 / 7 sin cambios | ✅ exactos |
| Base ↔ ORM sv3 ↔ ORM sv4 | ✅ los tres coinciden |
| Filas de prueba de F-016 (`origen`, `created_by`, coherencia) | ✅ conformes |
| **R7 de F-016 · `hasta` exclusivo (`+1 día`)** | ✅ **VERIFICADO en producción** (§5.3) |
| R12 de F-016 · sin solapes entre filas activas del mismo DNI | ✅ sin violación: solo una fila activa (§5.4) |

Un apunte que **no es un defecto** pero conviene que conste: **errata en la
spec de F-015**, `design.md` §8 habla de «las 16 columnas». Son **19**. Ver
§2.4.

---

## 1. Corrección: por qué falló el primer intento de conexión

En un primer intento la conexión terminó en `connection timeout expired` y
**este informe lo atribuyó al firewall del servidor, dando la verificación
por bloqueada. Esa conclusión se emitió con evidencia insuficiente y se
corrige aquí.** Lo que se comprobó después, desde el mismo puesto:

- **TCP al 5432 funciona**: conexión cruda al `…postgres.database.azure.com`
  en 0,01 s (y `Test-NetConnection` → `TcpTestSucceeded: True`).
- **La conexión real funciona**: `psycopg` conecta a la base `partes` con el
  admin del servidor, tanto con `sslmode=require` como con `prefer`, en
  0,1 s.

Sobre el estado del firewall, los hechos, sin interpretarlos: el listado de
`az postgres flexible-server firewall-rule list` ejecutado en el primer
intento devolvió **8 reglas**, ninguna cubriendo la IP pública del puesto; el
mismo comando, ejecutado después, devuelve **9 reglas**, e incluye una
llamada `datamart-puesto-pgris` que sí la cubre. Entre ambos listados algo
cambió (regla añadida, o un listado servido de caché). **No se ha creado ni
modificado ninguna regla desde esta verificación**, ni en el intento fallido
ni después.

La lección operativa, que es lo que vale: **un timeout no basta para acusar
al firewall**. Antes de concluirlo hay que probar el TCP crudo al puerto y
comparar la IP contra las reglas en el mismo momento. Todo lo demás de este
informe se ha ejecutado ya contra la base real.

Parámetros usados (sin contraseña): host
`psql-albaranes-rs9k2.postgres.database.azure.com`, puerto `5432`, base
`partes`, usuario = admin del servidor, `sslmode=require`. La credencial se
leyó del **Key Vault de partes** (secreto `PG-PASSWORD`); los `.env` locales
de sv3/sv4 no sirven porque apuntan a un PostgreSQL de desarrollo del propio
puesto.

---

## 2. `empleado_jornada`: columna a columna

19 columnas esperadas (tabla normativa de
`specs/F-015-jornada-semanal-candef/design.md` §6, implementadas por
`EmpleadoJornadaOrm`) contra 19 encontradas en `information_schema.columns`.

| # | Columna | Tipo real | NULL | `DEFAULT` real | Esperado (ORM/spec) | |
|---|---|---|---|---|---|---|
| 1 | `id` | `integer` | NO | `nextval('empleado_jornada_id_seq')` | Integer PK autoincrement | ✅ |
| 2 | `dni_norm` | `varchar(32)` | NO | `''` | String(32) NOT NULL, sd `''` | ✅ |
| 3 | `jornada_semanal` | `double precision` | SÍ | — | Float NULL | ✅ |
| 4 | `h_lun` | `double precision` | SÍ | — | Float NULL | ✅ |
| 5 | `h_mar` | `double precision` | SÍ | — | Float NULL | ✅ |
| 6 | `h_mie` | `double precision` | SÍ | — | Float NULL | ✅ |
| 7 | `h_jue` | `double precision` | SÍ | — | Float NULL | ✅ |
| 8 | `h_vie` | `double precision` | SÍ | — | Float NULL | ✅ |
| 9 | `h_sab` | `double precision` | SÍ | — | Float NULL | ✅ |
| 10 | `h_dom` | `double precision` | SÍ | — | Float NULL | ✅ |
| 11 | `desde` | `varchar(16)` | NO | `'1900-01-01'` | String(16) NOT NULL, sd centinela | ✅ |
| 12 | `hasta` | `varchar(16)` | SÍ | — | String(16) NULL | ✅ |
| 13 | `origen` | `varchar(16)` | NO | `'manual'` | String(16) NOT NULL, sd `manual` | ✅ |
| 14 | `nota` | `varchar(255)` | SÍ | — | String(255) NULL | ✅ |
| 15 | `is_active` | `boolean` | NO | `true` | Boolean NOT NULL, sd `true` | ✅ |
| 16 | `created_at_utc` | `varchar(40)` | NO | `'1970-01-01T00:00:00Z'` | String(40) NOT NULL, sd centinela | ✅ |
| 17 | `created_by` | `varchar(120)` | SÍ | — | String(120) NULL | ✅ |
| 18 | `updated_at_utc` | `varchar(40)` | SÍ | — | String(40) NULL | ✅ |
| 19 | `updated_by` | `varchar(120)` | SÍ | — | String(120) NULL | ✅ |

**19 columnas encontradas / 19 esperadas.** El **orden ordinal** también
coincide con el de declaración del ORM y con el que fija literalmente el
guardián `tests/test_f010_orm_models_gemelos.py`
(`COLUMNAS_EMPLEADO_JORNADA`).

`Float` de SQLAlchemy se materializa como `double precision`: es la
correspondencia normal del dialecto PostgreSQL, no una desviación.

### 2.1 Índices

```
empleado_jornada | empleado_jornada_pkey         | UNIQUE INDEX ... btree (id)
empleado_jornada | ix_empleado_jornada_dni_norm  | INDEX ... btree (dni_norm)
```

- `ix_empleado_jornada_dni_norm` **existe**, sobre `(dni_norm)`, **no
  único** — exactamente lo que declara el ORM (`index=True`). ✅
- PK sobre `(id)` respaldada por índice único, con secuencia
  `empleado_jornada_id_seq`. ✅

### 2.2 Restricciones

Las únicas restricciones de `empleado_jornada` son la PK:

```
empleado_jornada | empleado_jornada_pkey | p | PRIMARY KEY (id)
```

Cero CHECK, cero UNIQUE adicional, cero FK.

### 2.3 Por qué la ausencia de CHECKs es lo CONFORME

Es el punto que más fácilmente se lee al revés. La spec de F-015 §6 dice
literalmente que las restricciones de negocio —al menos `S` o patrón, sin
solapes de vigencia por `dni_norm`, horas 0–24— **se validan en aplicación y
son de F-016 (R8, R9, R10, R11, R12)**, no en la base. Encontrar cero CHECKs
es lo esperado; encontrar alguno sería la sorpresa. Lo mismo con la
unicidad: la spec **no** pide índice único en `empleado_jornada`.

Comprobado además que los datos reales respetan esas reglas aunque la base no
las imponga (§5.2).

### 2.4 Errata de la spec: 16 vs 19 columnas

`specs/F-015-jornada-semanal-candef/design.md` §8, en la lista de
verificaciones manuales, dice «`\d empleado_jornada` … mostrando las **16**
columnas». La tabla normativa de §6 del mismo documento declara **19**, y 19
es lo que implementa el ORM, lo que fija el guardián, lo que cuadra con el
número de sentencias del arranque (§4) y **lo que hay en la base**.

**Es una errata del texto de §8**, no un defecto del código. Se anota para
que nadie la use como criterio de aceptación. El número correcto es **19**.

---

## 3. F-010: qué eran M1/M2 y cómo han quedado

Conviene aclararlo porque induce a error: F-010 **no tiene «migraciones
M1/M2»**. `M1`, `M2` y `M3` son las tres *verificaciones manuales* que la
feature dejó pendientes de una base real
(`specs/F-010-resincronizar-orm-models/tasks.md`, `progress/impl_F-010.md`
§6, `progress/review_F-010.md`). F-010 resincronizó los dos `orm_models.py`
con la base **tal y como ya era**; su único cambio físico previsto era un
índice.

### M1 · «el único cambio físico es el índice» — ✅ VERIFICADO

Índices reales de `parte_registros` y `parte_documents`:

```
parte_registros  | ix_parte_registros_deleted_at_utc | btree (deleted_at_utc)   <- el de F-010
parte_registros  | ix_parte_registros_document_id    | btree (document_id)
parte_registros  | ix_parte_registros_empleado_ide   | btree (empleado_ide)
parte_registros  | parte_registros_pkey              | UNIQUE btree (id)
parte_documents  | ix_parte_documents_source_sha256  | btree (source_sha256)
parte_documents  | parte_documents_pkey              | UNIQUE btree (id)
parte_documents  | ux_parte_documents_sha256_active  | UNIQUE btree (source_sha256) WHERE is_active
```

- **`ix_parte_registros_deleted_at_utc` está presente** ✅ — era el único
  índice que el ORM declaraba y la base no tenía.
- La lista de `parte_registros` es **exactamente** la que M1 exigía.
- Cubierta también la **observación 1 del reviewer de F-010** (ampliar M1 a
  `parte_documents`): `ix_parte_documents_source_sha256` existe, y el índice
  único parcial `ux_parte_documents_sha256_active` sigue en pie con su
  `WHERE is_active`. ✅

Recuento de columnas por tabla:

| Tabla | Real | Esperado M1 | ORM | |
|---|---|---|---|---|
| `empleado_alias` | 7 | 7 | 7 | ✅ |
| `empleado_jornada` | **19** | (nueva, F-015) | 19 | ✅ |
| `parte_documents` | 47 | 47 | 47 | ✅ |
| `parte_registros` | 56 | 56 | 56 | ✅ |
| `undo_log` | 7 | 7 | 7 | ✅ |

**Ninguna tabla ganó ni perdió columnas**: F-015 solo añadió la tabla nueva,
como exigía R21 de su spec. La base tiene **exactamente esas cinco tablas**,
ni una más.

### M2 · «el arranque no revienta» — ✅ VERIFICADO

El log de arranque de sv4 dijo «esquema inicializado (**137** sentencias
complementarias)», sin excepción en `initialize()`. Ver §4.

### M3 · despliegue — ✅ VERIFICADO

El despliegue de anoche llevó sv3 y sv4; ambos ejecutan el mismo DDL
idempotente, así que el orden no era crítico. El estado final de la base lo
confirma.

Restricciones del resto del schema, sin novedad:

```
empleado_alias  | empleado_alias_pkey              | p | PRIMARY KEY (nombre_norm)
parte_documents | parte_documents_pkey             | p | PRIMARY KEY (id)
parte_registros | parte_registros_document_id_fkey | f | FOREIGN KEY (document_id) REFERENCES parte_documents(id)
parte_registros | parte_registros_pkey             | p | PRIMARY KEY (id)
undo_log        | undo_log_pkey                    | p | PRIMARY KEY (id)
```

La FK `parte_registros.document_id` sigue **sin** `ON DELETE CASCADE`, tal
como F-010 dejó dicho que quedaba fuera de alcance. ✅

---

## 4. Contraste base ↔ ORM sv3 ↔ ORM sv4: **los tres coinciden** ✅

Éste es el defecto que F-010 vino a arreglar. Hoy está sano en los tres
vértices:

1. **sv3 ↔ sv4**: `services/partes-persistencia/…/orm_models.py` y
   `services/partes-front/…/orm_models.py` tienen **`diff` vacío y el mismo
   MD5** (`5587db8a…`): son **byte-idénticas**, que es lo que exige el
   guardián `tests/test_f010_orm_models_gemelos.py`.
2. **ORM ↔ base**: las 19 columnas de `empleado_jornada` (nombre, orden,
   tipo, nullabilidad, `DEFAULT`), los índices de las cinco tablas y los
   recuentos 7/19/47/56/7 coinciden **sin una sola diferencia**.
3. **Aritmética del arranque**, como control cruzado independiente:
   `ddl_complementario()`, ejecutada en local como función pura, emite **137
   sentencias**, de ellas **19** de `empleado_jornada` (18 `ALTER TABLE …
   ADD COLUMN IF NOT EXISTS` — las 19 columnas menos la PK, que el generador
   salta — más 1 `CREATE INDEX`). F-010 dejó el generador en **118**
   sentencias; 118 + 19 = **137**, que es justo lo que logueó sv4 al
   arrancar. ✅

El guardián declara además `TABLAS` con las **cinco** tablas
(`empleado_alias`, `empleado_jornada`, `parte_documents`, `parte_registros`,
`undo_log`) — R29 de F-015 — y coinciden una a una con las de la base.

---

## 5. Filas de prueba creadas hoy desde `/admin/jornadas`

`SELECT count(*) FROM empleado_jornada` → **7 filas**.

**No se ha modificado ni borrado ninguna.** Los DNI reales van enmascarados:
son datos personales y este fichero se versiona. El DNI `00000000T` de las
filas 5–7 es **ficticio**, creado a propósito para la prueba de R7, y por eso
puede aparecer entero.

| id | DNI | `jornada_semanal` | patrón | `desde` | `hasta` | `origen` | `nota` | `is_active` | `created_by` | `updated_by` |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `50…` | 48.0 | ninguno (7 NULL) | 2026-08-01 | **NULL** | `manual` | `prueba F-016` | `false` | NULL | NULL |
| 2 | `28…` | 42.0 | ninguno (7 NULL) | 2026-08-20 | **NULL** | `manual` | — | `false` | NULL | NULL |
| 3 | `28…` | 42.0 | ninguno (7 NULL) | 2026-08-01 | **NULL** | `manual` | — | `false` | NULL | NULL |
| 4 | `28…` | 42.0 | ninguno (7 NULL) | 2024-07-01 | **NULL** | `manual` | — | `false` | NULL | NULL |
| 5 | `00000000T` | 40.0 | ninguno (7 NULL) | 2026-07-01 | **NULL** | `manual` | `prueba R7` | `false` | NULL | NULL |
| 6 | `00000000T` | 40.0 | ninguno (7 NULL) | 2026-07-01 | **2026-08-21** | `manual` | `prueba r7` | `false` | NULL | NULL |
| 7 | `00000000T` | 40.0 | ninguno (7 NULL) | 2026-07-01 | **2026-08-01** | `manual` | `prueba buena r7` | **`true`** | NULL | NULL |

Todas llevan `created_at_utc` real de hoy (altas entre las 08:52 y las 11:31
UTC). Las seis primeras están ya desactivadas, con su `updated_at_utc`
sellado; la 7 es la **única activa** y, coherentemente, es la única con
`updated_at_utc` a NULL: nunca se ha modificado desde su alta.

### 5.1 Comprobaciones pedidas

| Comprobación | Resultado |
|---|---|
| `origen = 'manual'` en todas | ✅ las 7 |
| `is_active` | ✅ coherente: 6 en `false` porque el humano las desactivó por la pantalla (papelera lógica, semántica 8) y la 7 en `true`. El `DEFAULT true` de la columna es correcto; el `false` es un `UPDATE` deliberado de la UI, no un fallo |
| `created_by` **NULL** (por `DEFAULT_REVIEWER` no configurada en sv4) | ✅ las 7 a NULL, como se esperaba |
| `updated_by` | ✅ las 7 a NULL, coherente con lo anterior (mismo helper `_actor(request)`, R13) |
| `created_at_utc` / `updated_at_utc` sellados | ✅ ISO-8601 con offset UTC; `updated_at_utc` solo en las que se han tocado |
| Patrón coherente | ✅ o los siete valores o ninguno (R8): las 7 usan solo `jornada_semanal`, con los 7 `h_*` a NULL |
| `dni_norm` normalizado (R18) | ✅ sin separadores y en mayúsculas en las 7 |

### 5.2 Reglas de negocio que la base no impone pero los datos respetan

- **Solapes de vigencia por `dni_norm` entre filas activas** (R12):
  **ninguno**. Analizado en detalle en §5.4, porque las tres filas del DNI
  ficticio sí se solapan en el calendario.
- **Horas fuera de rango** (R9/R10): **0 filas**. `jornada_semanal` 40, 42 y
  48 son valores plausibles y dentro de rango.
- **`desde` bien formado**: las 7 en ISO `YYYY-MM-DD`, ninguna con el
  centinela `1900-01-01`.

### 5.3 R7 (`hasta` exclusivo): **VERIFICADO EN PRODUCCIÓN** ✅

R7 de F-016 exige que la pantalla hable en **último día incluido** y la base
guarde el **exclusivo** (`hasta = último día incluido + 1 día`), y que «sin
fecha de fin» equivalga a `hasta = NULL` en los dos sentidos.

Las filas 5, 6 y 7 (DNI ficticio `00000000T`) cierran las dos mitades del
requisito. Aplicando a cada una el mismo cálculo que hace
`ultimo_dia_incluido_de_fila` al pintar (`hasta − 1 día`):

| id | `desde` en base | `hasta` en base (exclusivo) | Lo que pinta la pantalla | Veredicto |
|---|---|---|---|---|
| 5 | `2026-07-01` | `NULL` | `2026-07-01 … sin fin` | ✅ mitad NULL de R7 |
| 6 | `2026-07-01` | **`2026-08-21`** | `2026-07-01 … 2026-08-20` | ✅ **coincide con lo observado en pantalla** |
| 7 | `2026-07-01` | **`2026-08-01`** | `2026-07-01 … 2026-07-31` | ✅ el caso canónico de la spec |

**Fila 6 — la prueba decisiva.** La pantalla la pintaba
`2026-07-01 … 2026-08-20` y en la base `hasta` vale **exactamente
`2026-08-21`**: un día más que el último día incluido. Es justo el valor que
R7 exige. No es `2026-08-20` (que sería guardar el inclusivo, sin
conversión), ni `2026-07-31`, ni `2026-08-01`. **La conversión «+1 día»
funciona.**

**Fila 7 — el caso que planeábamos.** `hasta = '2026-08-01'` para un último
día incluido `2026-07-31`: el criterio literal de aceptación que escribe la
spec en R7. ✅

**`desde` sin desplazamiento.** Las tres filas guardan `desde =
'2026-07-01'`, **tal cual se escribió**, sin corrimiento de un día ni
conversión de zona horaria. Era el segundo defecto posible y no aparece. Se
sostiene porque `desde` y `hasta` son `varchar(16)` con la fecha ISO literal,
no `date` ni `timestamp`: no hay ninguna capa que pueda reinterpretarlos en
otro huso. Las cuatro filas anteriores (1–4) lo confirman también, con
`desde` en 2024 y 2026 sin desviación.

**Conclusión: R7 queda verificado en el entorno desplegado**, en sus dos
sentidos —«sin fin» ⇒ `NULL`, y último día incluido ⇒ `+1 día`— y con la
garantía adicional de que `desde` no sufre desplazamiento.

### 5.4 R12 (sin solapes por DNI): **no hay violación** ✅

Las tres filas del DNI ficticio `00000000T` **se solapan en el calendario**:
las tres arrancan el `2026-07-01` y cubren julio. R12 no prohíbe eso: prohíbe
que dos filas **activas** del mismo `dni_norm` se solapen. Y ahí el estado es
correcto:

| id | vigencia | `is_active` |
|---|---|---|
| 5 | 2026-07-01 → sin fin | `false` |
| 6 | 2026-07-01 → 2026-08-21 (excl.) | `false` |
| 7 | 2026-07-01 → 2026-08-01 (excl.) | **`true`** |

**Solo una está activa.** La consulta de solapes entre filas activas devuelve
**cero pares**. No hay hallazgo.

La cronología de las marcas de auditoría explica por qué el validador nunca
llegó a tener que rechazar nada — el humano fue desactivando cada fila antes
de crear la siguiente:

```
11:28:11  alta   id 5
11:29:22  baja   id 5      <- desactivada ANTES de crear la 6
11:30:05  alta   id 6
11:31:16  baja   id 6      <- desactivada ANTES de crear la 7
11:31:42  alta   id 7      (unica activa)
```

Entre la baja de la 6 y el alta de la 7 pasaron 26 segundos, así que **el alta
de la 7 no debía ser rechazada**: en ese instante no había ninguna otra fila
activa de ese DNI con la que solapar. El comportamiento observado es el
correcto.

Matiz honesto sobre el alcance: de esto **no se deduce que el validador de
solapes funcione**, solo que no se ha disparado ningún falso positivo. La
rama de rechazo (409) de R12 no ha quedado ejercitada en producción; sí la
cubren los tests `test_f016_r12_solape`
(`tests/test_f016_validacion_jornada_admin.py` en unidad y
`tests/test_f016_endpoints_admin_jornadas.py` por HTTP). Para probarla en
pantalla habría que intentar dar de alta una segunda fila del mismo DNI con
vigencias solapadas **sin desactivar la primera** y comprobar que la pantalla
la rechaza. Queda anotado en §7 como opcional.

En el código la conversión está donde R7 manda —solo en la capa web:
`services/partes-front/interface_adapters/web/app.py` usa
`ultimo_dia_incluido_de_fila(...)` al pintar y hace la conversión inversa al
guardar— y la cubre el test `test_f016_r7_hasta_exclusivo`
(`tests/test_f016_validacion_jornada_admin.py`), con el par ida-y-vuelta
estable para 366 fechas consecutivas. Lo que falta es la comprobación
**manual en el entorno desplegado**, no la del código.

---

## 6. SQL de solo lectura utilizado

Todo `SELECT`, sobre la base **`partes`**. Recomendación de higiene: abrir la
sesión con `SET default_transaction_read_only = on;` antes de nada.

```sql
-- 1) Las 19 columnas de empleado_jornada
SELECT ordinal_position, column_name, data_type,
       character_maximum_length, is_nullable, column_default
  FROM information_schema.columns
 WHERE table_schema='public' AND table_name='empleado_jornada'
 ORDER BY ordinal_position;

-- 2) Recuento de columnas por tabla (M1 de F-010)
SELECT table_name, count(*) FROM information_schema.columns
 WHERE table_schema='public' GROUP BY 1 ORDER BY 1;

-- 3) Indices (M1 ampliado segun la observacion 1 del reviewer de F-010)
SELECT tablename, indexname, indexdef FROM pg_indexes
 WHERE schemaname='public' ORDER BY tablename, indexname;

-- 4) Restricciones
SELECT t.relname, c.conname, c.contype, pg_get_constraintdef(c.oid)
  FROM pg_constraint c
  JOIN pg_class t ON t.oid=c.conrelid
  JOIN pg_namespace n ON n.oid=t.relnamespace
 WHERE n.nspname='public' AND t.relkind='r'
 ORDER BY t.relname, c.conname;

-- 5) Filas, con el DNI SIEMPRE enmascarado (dato personal)
SELECT count(*) FROM empleado_jornada;
SELECT id, left(dni_norm,2)||'...' AS dni, jornada_semanal,
       h_lun,h_mar,h_mie,h_jue,h_vie,h_sab,h_dom,
       desde, hasta, origen, nota, is_active,
       created_at_utc, created_by, updated_at_utc, updated_by
  FROM empleado_jornada ORDER BY id;

-- 6) R7 de F-016: `hasta` es EXCLUSIVO. La columna `ultimo_dia_incluido`
--    debe coincidir con la fecha que se escribio en la pantalla.
SELECT id, desde, hasta AS hasta_exclusivo,
       CASE WHEN hasta IS NULL THEN 'sin fin'
            ELSE to_char(to_date(hasta,'YYYY-MM-DD') - 1,'YYYY-MM-DD')
       END AS ultimo_dia_incluido_en_pantalla,
       CASE WHEN hasta IS NULL THEN NULL
            ELSE (to_date(hasta,'YYYY-MM-DD') > to_date(desde,'YYYY-MM-DD'))
       END AS desde_menor_que_hasta
  FROM empleado_jornada ORDER BY id;

-- 7) R12: solapes de vigencia por DNI entre filas ACTIVAS (debe salir vacio)
SELECT a.id, b.id
  FROM empleado_jornada a JOIN empleado_jornada b
    ON a.dni_norm=b.dni_norm AND a.id<b.id
 WHERE a.is_active AND b.is_active
   AND a.desde < coalesce(b.hasta,'9999-12-31')
   AND b.desde < coalesce(a.hasta,'9999-12-31');

-- 8) R9/R10: horas fuera de rango (debe salir 0)
SELECT count(*) FROM empleado_jornada
 WHERE (jornada_semanal IS NOT NULL AND (jornada_semanal<0 OR jornada_semanal>168))
    OR h_lun<0 OR h_lun>24 OR h_mar<0 OR h_mar>24 OR h_mie<0 OR h_mie>24
    OR h_jue<0 OR h_jue>24 OR h_vie<0 OR h_vie>24 OR h_sab<0 OR h_sab>24
    OR h_dom<0 OR h_dom>24;
```

---

## 7. Qué queda pendiente

**Todas las comprobaciones de este encargo están cerradas.** Queda:

1. **Errata de `design.md` §8 de F-015** (§2.4): «16 columnas» debería decir
   «19». Corrección documental de una línea.
2. **Opcional, no bloqueante — rama de rechazo de R12** (§5.4): intentar en
   `/admin/jornadas` un alta solapada con una fila **activa** del mismo DNI y
   comprobar que la pantalla la rechaza (409). Está cubierta por tests, pero
   no se ha ejercitado en el entorno desplegado.
3. **Limpieza de las filas de prueba**, cuando el humano lo decida: 7 filas de
   prueba en `empleado_jornada`, seis ya inactivas y la id 7 activa con DNI
   ficticio `00000000T`. No estorban al cómputo (el DNI no casa con ningún
   trabajador real), pero conviene no dejarlas ahí indefinidamente. **Las
   borra o desactiva el humano por la pantalla, no un agente.**

---

## 8. Qué NO se ha hecho

- No se ha ejecutado ningún DDL, `INSERT`, `UPDATE` ni `DELETE`.
- **No se ha tocado ninguna de las 7 filas de prueba**: las crea, desactiva y
  borra el humano por la pantalla.
- No se ha creado, modificado ni borrado ninguna regla de firewall, ni antes
  ni después del intento fallido.
- No se ha tocado nada a nivel del servidor `psql-albaranes-rs9k2`.
- No se ha escrito ninguna credencial, cadena de conexión, IP, id de
  suscripción/tenant ni DNI completo en este fichero.
- No se ha modificado código del repositorio ni se ha desplegado nada.
