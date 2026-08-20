# Verificación del esquema de la base `partes` tras el despliegue del 2026-08-20

- **Fecha**: 2026-08-20
- **Despliegue verificado**: sv3 + sv4 desde `dev`, revisión `r20260820000737`
  (2026-08-20 00:10). Lleva F-015 (tabla `empleado_jornada`), F-016
  (pantalla `/admin/jornadas`, sin cambios de schema) y el DDL pendiente de
  F-010, que sv3/sv4 aplican al arrancar.
- **Alcance**: solo lectura. No se ha ejecutado ni un DDL, INSERT, UPDATE o
  DELETE, ni se ha tocado nada a nivel del servidor compartido.

## 0. VEREDICTO FINAL

**BLOQUEADO — verificación contra la base real NO realizada.**

El PostgreSQL compartido `psql-albaranes-rs9k2` tiene acceso público
habilitado pero con lista blanca de IP, y **la IP pública del puesto desde el
que se ejecuta esta verificación no figura en ninguna regla de firewall del
servidor**. La conexión termina en `connection timeout expired`, que es el
síntoma típico del *drop* silencioso del firewall de Azure PostgreSQL.

Siguiendo la instrucción explícita del encargo y la regla dura de
`CLAUDE.md` («el PostgreSQL `psql-albaranes-rs9k2` es COMPARTIDO: prohibido
tocar nada a nivel de servidor»), **no se ha creado ninguna regla de
firewall** y se ha parado ahí.

Lo que **sí** se ha podido verificar (sin base de datos) sale **CONFORME**,
sin ninguna discrepancia:

| Comprobación | Resultado |
|---|---|
| `empleado_jornada` declarada con 19 columnas en el ORM | ✅ |
| Las DOS copias de `orm_models.py` (sv3 y sv4) byte-idénticas | ✅ |
| El DDL generado emite exactamente 137 sentencias | ✅ (coincide con el log de arranque de sv4) |
| Índice `ix_empleado_jornada_dni_norm` declarado | ✅ |
| Guardián `tests/test_f010_orm_models_gemelos.py` con las 5 tablas y las 19 columnas literales | ✅ |

Queda **PENDIENTE** el contraste físico base ↔ ORM. Ver §6 con el SQL exacto,
listo para ejecutarse en cuanto el puesto tenga acceso.

---

## 1. Fuente de verdad: qué debe existir

### 1.1 `empleado_jornada` según `specs/F-015-jornada-semanal-candef/design.md` §6

19 columnas. Contrastadas una a una con la declaración real de
`EmpleadoJornadaOrm` en las dos copias de `infrastructure/database/orm_models.py`
(leída por reflexión de SQLAlchemy, no a ojo):

| # | Columna | Tipo (ORM) | NULL | `server_default` | Spec §6 | ORM = Spec |
|---|---|---|---|---|---|---|
| 1 | `id` | INTEGER | NO (PK) | — | Integer PK autoincrement | ✅ |
| 2 | `dni_norm` | VARCHAR(32) | NO | `''` (centinela) | String(32) NOT NULL, `index=True` | ✅ |
| 3 | `jornada_semanal` | FLOAT | SÍ | — | Float NULL | ✅ |
| 4 | `h_lun` | FLOAT | SÍ | — | Float NULL | ✅ |
| 5 | `h_mar` | FLOAT | SÍ | — | Float NULL | ✅ |
| 6 | `h_mie` | FLOAT | SÍ | — | Float NULL | ✅ |
| 7 | `h_jue` | FLOAT | SÍ | — | Float NULL | ✅ |
| 8 | `h_vie` | FLOAT | SÍ | — | Float NULL | ✅ |
| 9 | `h_sab` | FLOAT | SÍ | — | Float NULL | ✅ |
| 10 | `h_dom` | FLOAT | SÍ | — | Float NULL | ✅ |
| 11 | `desde` | VARCHAR(16) | NO | `'1900-01-01'` | String(16) NOT NULL, ISO inclusivo | ✅ |
| 12 | `hasta` | VARCHAR(16) | SÍ | — | String(16) NULL, ISO exclusivo | ✅ |
| 13 | `origen` | VARCHAR(16) | NO | `'manual'` | String(16) NOT NULL, sd `manual` | ✅ |
| 14 | `nota` | VARCHAR(255) | SÍ | — | String(255) NULL | ✅ |
| 15 | `is_active` | BOOLEAN | NO | `true` | Boolean NOT NULL, sd `true` | ✅ |
| 16 | `created_at_utc` | VARCHAR(40) | NO | `'1970-01-01T00:00:00Z'` | String(40) NOT NULL | ✅ |
| 17 | `created_by` | VARCHAR(120) | SÍ | — | String(120) NULL | ✅ |
| 18 | `updated_at_utc` | VARCHAR(40) | SÍ | — | String(40) NULL | ✅ |
| 19 | `updated_by` | VARCHAR(120) | SÍ | — | String(120) NULL | ✅ |

Los `server_default` de `dni_norm`, `desde` y `created_at_utc` no están en la
tabla de la spec pero **sí son coherentes con ella**: la spec exige
`server_default` para toda columna `NOT NULL` (§6, párrafo tras la tabla),
porque el DDL complementario las añade con `ALTER TABLE … ADD COLUMN` y un
`NOT NULL` sin default reventaría el arranque sobre una tabla con filas.
Los tres son centinelas que no casan con ningún dato real.

**Índice esperado**: `ix_empleado_jornada_dni_norm` sobre `(dni_norm)`, **no
único**. Confirmado en el ORM.

**Clave primaria esperada**: `empleado_jornada_pkey` sobre `(id)`.

**Restricciones CHECK esperadas: NINGUNA.** Es un punto que conviene dejar
claro porque el encargo preguntaba por CHECKs de horas 0–24 y `desde<hasta`:
la spec de F-015 §6 dice literalmente que esas reglas de negocio (al menos
`S` o patrón, sin solapes de vigencia por `dni_norm`, horas 0–24) **se
validan en aplicación y son de F-016 (R27)**, no en la base. Así que
encontrar cero CHECKs en `empleado_jornada` es lo CONFORME; encontrar
alguno sería la sorpresa.

**Unicidad**: la spec **no** pide índice único en `empleado_jornada`. El no
solapamiento de vigencias por `dni_norm` se valida en aplicación (F-016).
El único índice único del schema sigue siendo el parcial de F-010,
`ux_parte_documents_sha256_active ON parte_documents (source_sha256) WHERE is_active`.

### 1.2 Nota: incoherencia interna de la spec (16 vs 19)

`specs/F-015-jornada-semanal-candef/design.md` §8, en la lista de
verificaciones manuales, dice «`\d empleado_jornada` en la base `partes`
mostrando las **16** columnas». La tabla normativa de §6 del mismo documento
declara **19**, y 19 es lo que implementa el ORM, lo que fija el guardián y
lo que cuadra con el número de sentencias del arranque (§3).

**Es una errata del texto de §8**, no un defecto del código. Se anota aquí
para que nadie la use como criterio de aceptación. El número correcto es
**19**.

### 1.3 F-010: qué eran M1 y M2

Contra lo que sugería el encargo, F-010 **no tiene «migraciones M1/M2» que
añadan columnas**. `M1`, `M2` y `M3` son las tres *verificaciones manuales*
que la feature dejó pendientes de una base real
(`specs/F-010-resincronizar-orm-models/tasks.md` §«Verificaciones MANUAL»,
`progress/impl_F-010.md` §6, `progress/review_F-010.md`):

- **M1 — «el único cambio físico es el índice»**. F-010 resincronizó los dos
  `orm_models.py` con la base **tal y como ya era**; el único cambio físico
  que introduce en PostgreSQL es el índice
  **`ix_parte_registros_deleted_at_utc`**, que el ORM declaraba y la base no
  tenía. Criterio de M1:
  - `pg_indexes` de `parte_registros` debe listar exactamente
    `ix_parte_registros_deleted_at_utc`, `ix_parte_registros_document_id`,
    `ix_parte_registros_empleado_ide` y `parte_registros_pkey`.
  - El nº de columnas por tabla **no cambia**: `empleado_alias` 7,
    `parte_documents` 47, `parte_registros` 56, `undo_log` 7.
  - El reviewer recomendó ampliar la consulta a
    `tablename IN ('parte_documents','parte_registros')`, para cubrir también
    `ix_parte_documents_source_sha256` (el otro índice que el generador emite
    y que el DDL a mano de sv3 nunca creaba; se esperaba no-op).
- **M2 — «el arranque no revienta»**: `initialize()` termina sin excepción en
  los dos servicios y loguea el **mismo** número de sentencias
  complementarias en ambos.
- **M3 — despliegue**: orden sv3 antes que sv4; el DDL es idempotente, así
  que el orden no es crítico.

M2 y M3 **ya están verificados por el despliegue de anoche** (§3). M1 es
justamente lo que sigue pendiente por el bloqueo de firewall.

---

## 2. Contraste sv3 ↔ sv4 de `orm_models.py`: CONFORME ✅

Éste es el defecto que F-010 vino a arreglar, y hoy está sano:

- `services/partes-persistencia/infrastructure/database/orm_models.py`
- `services/partes-front/infrastructure/database/orm_models.py`

**`diff` vacío y mismo hash MD5** (`5587db8a…`): las dos copias son
**byte-idénticas**, que es exactamente lo que exige el guardián
`tests/test_f010_orm_models_gemelos.py`.

El guardián declara además, de forma literal:

- `TABLAS` = `empleado_alias`, `empleado_jornada`, `parte_documents`,
  `parte_registros`, `undo_log` — **cinco** tablas, con `empleado_jornada`
  ya incorporada por F-015 (R29).
- `COLUMNAS_EMPLEADO_JORNADA` con **las 19 columnas en orden de
  declaración**, comentada como «Las 19 columnas de `empleado_jornada`
  (F-015)».

Recuento de columnas declaradas en el ORM, por tabla:

| Tabla | Columnas en el ORM | Índices declarados |
|---|---|---|
| `empleado_alias` | 7 | — |
| `empleado_jornada` | **19** | `ix_empleado_jornada_dni_norm` |
| `parte_documents` | 47 | `ix_parte_documents_source_sha256` |
| `parte_registros` | 56 | `ix_parte_registros_deleted_at_utc`, `ix_parte_registros_document_id`, `ix_parte_registros_empleado_ide` |
| `undo_log` | 7 | — |

Coincide, columna a columna, con los recuentos que F-010 fijó como criterio
de M1 (7 / 47 / 56 / 7) más la tabla nueva de F-015.

---

## 3. Evidencia indirecta del despliegue: las 137 sentencias

`ddl_complementario()` se ha ejecutado **en local, como función pura** (no
abre ninguna conexión: compila contra el dialecto PostgreSQL) sobre el ORM
de sv3:

```
TOTAL sentencias: 137
de ellas, de `empleado_jornada`: 19
columnas declaradas en `empleado_jornada`: 19
```

El log de arranque de sv4 de anoche dijo **«esquema inicializado (137
sentencias complementarias)»**. Cuadra con la aritmética esperada:

- F-010 dejó el generador en **118** sentencias (número recalculado por el
  reviewer en `progress/review_F-010.md`).
- F-015 añade `empleado_jornada`: **18** `ALTER TABLE … ADD COLUMN IF NOT
  EXISTS` (las 19 columnas menos la PK `id`, que el generador salta) **+ 1**
  `CREATE INDEX IF NOT EXISTS ix_empleado_jornada_dni_norm` = **19**.
- 118 + 19 = **137**. ✅

Esto es una confirmación **fuerte pero indirecta**: prueba que el código
desplegado es el que declara las 19 columnas y el índice, y que `initialize()`
recorrió las 137 sentencias sin excepción (M2 ✅ en el entorno real). **No
prueba** que PostgreSQL las aplicara con el resultado esperado — de ahí que
el contraste físico siga siendo necesario.

También queda cubierto **M3**: el despliegue de anoche llevó sv3 y sv4, y
ambos ejecutan el mismo DDL idempotente.

---

## 4. Contraste base ↔ ORM: PENDIENTE

| Comprobación | Estado |
|---|---|
| Columnas reales de `empleado_jornada` (19 esperadas) | ⏸ PENDIENTE (sin acceso) |
| Índice `ix_empleado_jornada_dni_norm` sobre `(dni_norm)` | ⏸ PENDIENTE |
| PK `empleado_jornada_pkey` sobre `(id)` | ⏸ PENDIENTE |
| Ausencia de CHECKs (lo esperado, ver §1.1) | ⏸ PENDIENTE |
| `SELECT count(*) FROM empleado_jornada` (esperado 0) | ⏸ PENDIENTE |
| M1 · `ix_parte_registros_deleted_at_utc` presente | ⏸ PENDIENTE |
| M1 · recuentos 7 / 47 / 56 / 7 sin cambios | ⏸ PENDIENTE |

**Ninguna de estas comprobaciones ha fallado: no se han podido ejecutar.**

---

## 5. Motivo del bloqueo

1. Los ficheros locales no versionados de sv3 y sv4 (`.env`) apuntan a un
   PostgreSQL **de desarrollo en el propio puesto**, no al servidor de Azure:
   no sirven para esta verificación.
2. La credencial real de la base vive en el **Key Vault de partes**
   (secreto `PG-PASSWORD`), como declara `infra/create_capps_partes.ps1`.
   Se pudo leer con la sesión de `az` ya iniciada. **No se ha escrito en
   ningún fichero ni se ha mostrado por pantalla.**
3. El servidor tiene `publicNetworkAccess = Enabled`, estado `Ready`,
   PostgreSQL 16, y una lista blanca de reglas de firewall. **La IP pública
   del puesto no está en ninguna de ellas.** Resultado:
   `connection timeout expired`.
4. Se paró ahí. **No se ha creado ninguna regla de firewall** ni se ha
   modificado nada del servidor compartido, conforme a la instrucción del
   encargo y a la regla dura de `CLAUDE.md`.

Para desbloquear, el humano tiene que **añadir una regla de firewall para la
IP pública actual del puesto** en `psql-albaranes-rs9k2` (es la operación
rutinaria que ya se hace a diario para `datamart`, con reglas del tipo
`datamart-puesto-pgris-<fecha>`). La IP concreta se le ha dado por chat: no
se escribe aquí porque este fichero se versiona.

---

## 6. SQL exacto, listo para ejecutar cuando haya acceso

Todo `SELECT`. Ejecutar sobre la base **`partes`** (no sobre `postgres`).

```sql
-- 1) Las 19 columnas de empleado_jornada
SELECT ordinal_position, column_name, data_type,
       character_maximum_length, is_nullable, column_default
  FROM information_schema.columns
 WHERE table_schema='public' AND table_name='empleado_jornada'
 ORDER BY ordinal_position;
-- Esperado: 19 filas, en el orden de la tabla de §1.1.

-- 2) Recuento de columnas por tabla (cubre M1 de F-010)
SELECT table_name, count(*)
  FROM information_schema.columns
 WHERE table_schema='public'
 GROUP BY 1 ORDER BY 1;
-- Esperado: empleado_alias 7 | empleado_jornada 19 | parte_documents 47
--           parte_registros 56 | undo_log 7

-- 3) Indices (M1 ampliado segun la observacion 1 del reviewer de F-010)
SELECT tablename, indexname, indexdef
  FROM pg_indexes
 WHERE schemaname='public'
 ORDER BY tablename, indexname;
-- Esperado, entre otros:
--   empleado_jornada  ix_empleado_jornada_dni_norm  (dni_norm), NO unico
--   empleado_jornada  empleado_jornada_pkey         (id)
--   parte_registros   ix_parte_registros_deleted_at_utc   <- el de F-010
--   parte_registros   ix_parte_registros_document_id
--   parte_registros   ix_parte_registros_empleado_ide
--   parte_registros   parte_registros_pkey
--   parte_documents   ix_parte_documents_source_sha256
--   parte_documents   ux_parte_documents_sha256_active  (UNIQUE ... WHERE is_active)

-- 4) Restricciones
SELECT t.relname, c.conname, c.contype, pg_get_constraintdef(c.oid)
  FROM pg_constraint c
  JOIN pg_class t ON t.oid = c.conrelid
  JOIN pg_namespace n ON n.oid = t.relnamespace
 WHERE n.nspname='public'
 ORDER BY t.relname, c.conname;
-- Esperado en empleado_jornada: SOLO la PK. CERO CHECK (§1.1).

-- 5) La tabla nace vacia
SELECT count(*) FROM empleado_jornada;
-- Esperado: 0

-- 6) Si hubiera filas, mirarlas SIN DNI completo (dato personal)
SELECT id, left(dni_norm,2)||'***' AS dni, jornada_semanal,
       h_lun,h_mar,h_mie,h_jue,h_vie,h_sab,h_dom,
       desde, hasta, origen, is_active
  FROM empleado_jornada ORDER BY id;
```

Recomendación de higiene para quien las ejecute: abrir la sesión con
`SET default_transaction_read_only = on;` antes de nada, para que un error de
dedo no pueda escribir.

---

## 7. Qué NO se ha hecho

- No se ha ejecutado ningún DDL, `INSERT`, `UPDATE` ni `DELETE`.
- No se ha creado, modificado ni borrado ninguna regla de firewall.
- No se ha tocado nada a nivel del servidor `psql-albaranes-rs9k2`.
- No se ha escrito ninguna credencial, cadena de conexión, IP, id de
  suscripción/tenant ni DNI en este fichero.
- No se ha desplegado nada ni se ha modificado código del repositorio.
