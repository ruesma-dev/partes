<!-- specs/F-063-consulta-obra-rapida/requirements.md -->
# F-063 · Consulta de existencia de obra que use el índice (sv2) — Requisitos

**Servicio tocado: solo sv2** (`services/partes-api`; ficheros en `design.md` §4). Rigor
**estándar**: cambia una consulta de **lectura** a sigrid-api; no escribe en Sigrid ni en
`partes`, no toca nada compartido a nivel de servidor ni cambia el entorno de Azure.

**Petición del humano del 2026-10-25**, literal: «1a», a la opción del líder: «Corrección
pequeña: una consulta que use el índice, que baja a unos 0,1 s. Por ejemplo, buscar por
`con.cod LIKE '%<clave>'` y normalizar en Python, o una lista de variantes con ceros. El
spec-author decide cuál y que no se pierdan los códigos con guiones o espacios. Después se
despliega sv2.»

**Contexto** (`design.md` §2): la consulta de obra de F-058 (`_SQL_EXISTE_OBRA`) calcula la
clave fila a fila sobre `con.cod` (`CROSS APPLY`, `REPLACE`, `PATINDEX`, `COLLATE`) y tarda
12–16 s en sigrid-api; con el tope `OBRA_EXISTE_TIMEOUT_S` = 5 s, la M1 de F-058 dio
`ReadTimeout` en las 8 consultas. Un `LIKE` sobre `con.cod` sin funciones tarda ~0,1 s.
F-058 está en `dev` **sin desplegar**; sv2 no se despliega hasta cerrar esta feature.

## Glosario

- **Clave de obra**: la de F-058, **sin cambios**: el código sin acentos, en mayúsculas y sin
  blancos ni guiones; si queda solo de dígitos, sin ceros a la izquierda (`clave_obra`).
- **Obra**: una fila de `obr ⨝ con` (`obr.ide = con.ide`), de cualquier empresa y también de
  baja, como en F-058.
- **Existe (verdad)**: hay al menos una obra cuya `clave_obra(con.cod)` es igual a la clave
  pedida. Es la semántica de F-058 y la vara de medir de toda esta feature.
- **Patrón de la clave**: el patrón `LIKE` de T-SQL que genera `patron_like(clave)`
  (`design.md` §5.2): `%`, y tras cada carácter de la clave su clase de variantes y otro `%`.
- **Candidatos**: los `con.cod` distintos de las obras que casan con el patrón. Son un
  **superconjunto** de los códigos con esa clave; el filtro exacto se hace en Python.

## Requisitos

### La consulta (sigrid-api)

- **R1.** La consulta de obra debe ser una sola `sql/read` de la forma `SELECT DISTINCT
  con.cod ... FROM obr JOIN con ON obr.ide = con.ide WHERE con.cod LIKE ?` (texto exacto en
  `design.md` §6): **sin funciones ni `COLLATE` sobre `con.cod`**, sin `CROSS APPLY`, sin
  `TOP` y sin filtro de empresa ni de baja.
- **R2.** El único parámetro debe ser el patrón de la clave; ni la clave ni el patrón deben
  aparecer concatenados en el texto SQL.
- **R3.** La consulta debe pedir el `max_rows` del cliente (`SIGRID_API_MAX_ROWS`), nunca un
  literal (F-038, guardián `tests/test_f038_lectores_sigrid.py` sin tocar), con el tope
  `timeout_s` del argumento como hoy. `truncated: true`, un 4xx/5xx u `ok: false` deben seguir
  lanzando (los recoge `ComprobadorObra` como «no se sabe», F-058 R9).

### El patrón (superconjunto garantizado)

- **R4.** Para todo código `C` con `clave_obra(C)` no vacía, `C` debe casar con
  `patron_like(clave_obra(C))` bajo `LIKE` que **no** distingue mayúsculas pero **sí**
  acentos (el caso más exigente). Incluye códigos con blancos, guiones, tabuladores o espacio
  duro en cualquier posición, ceros a la izquierda, minúsculas, letras acentuadas, `Ñ`/`ñ`,
  `Ç`/`ç` y los volados `ª`, `º`, `¹`, `²`, `³`.
- **R5.** Cada carácter de la clave cuya forma `clave_obra` sea la de otros caracteres de
  U+00A0–U+017F debe ir como clase `[...]` con él, su minúscula y esas variantes (p. ej. `A` ⇒
  `[...]` con `A`, `a`, `Á`, `á`, `À`, `ª`...); si no tiene variantes ni minúscula distinta,
  va tal cual.
- **R6.** Los caracteres especiales de `LIKE` en la clave (`%`, `_`, `[`) deben ir escapados
  como literales (`[%]`, `[_]`, `[[]`): el patrón de `"A_1"` no casa con `"AX1"`.
- **R7.** SI la clave es vacía, ENTONCES `patron_like` debe lanzar `ValueError` (nunca un `%`
  suelto que traiga todas las obras). `ComprobadorObra` ya no consulta con clave vacía.

### El filtro (resultado exacto)

- **R8.** `existe_obra(clave)` debe devolver `True` si y solo si algún candidato tiene
  `clave_obra(candidato) == clave`. Candidatos de otra clave (`"1692"`, `"6920"`, `"69-12"`
  para la clave `"692"`) o nulos no cuentan: sin ninguno exacto, `False`.
- **R9.** La clave debe calcularse con **una sola función** a los dos lados (la del código
  leído y la de cada candidato): `es_vacio` y `clave_obra` pasan a la capa de dominio sin
  cambiar su comportamiento, y `application/services/relectura_cabecera.py` las sigue
  exponiendo con el mismo nombre (tests de F-058 que las importan, sin tocar).
- **R10.** Para los códigos `"692"`, `"0692"`, `"00692"`, `"06-92"`, `"06 92"`, `" 0-6 9-2 "`
  y `"06 92"` (candidatos de la clave `"692"`), `existe_obra("692")` debe dar `True`; para
  `"a-12"`, `"Á 12"` y `"A12"`, `existe_obra("A12")` debe dar `True`.

### Lo que no cambia

- **R11.** No deben cambiar: el puerto `ExistenciaObraPort` (`existe_obra(clave, *,
  timeout_s) -> bool`), `ComprobadorObra` y su log `[obra-sigrid] document_id=… resultado=…
  ms=…` (las consultas de M4 de F-058 siguen valiendo), el pipeline, `Settings` ni
  `OBRA_EXISTE_TIMEOUT_S` (5 s, DA12 de F-058), ni `fetch_tipos_hora`.
- **R12.** sv1, sv3, sv4, sv5, los `orm_models.py`, `parte_models.py`, `prompts.yaml`, `infra/`
  y la lista `LECTORES_ESPERADOS` de F-038 no deben cambiar (comprobable con `git diff dev`).
  De los tests de F-058 solo cambian las aserciones del texto SQL que esta feature sustituye
  (`design.md` §7).

### Documentación

- **R13.** `docs/ARCHITECTURE.md` (punto 18) y `azure-apps/partes.md` (§3.2, que hoy dice
  `SELECT TOP 1`) deben contar la consulta nueva: `LIKE` parametrizado sobre `con.cod` sin
  funciones, candidatos distintos y filtro exacto con la misma clave en sv2.

## Verificación manual (líder, solo lectura; comandos en `design.md` §9)

- **M-EQ** (antes de desplegar, base `ruesma`): todas las obras de Sigrid casan con el patrón
  de su propia clave (cero fallos, comprobado en lotes por `ide`), con recuento de códigos con
  blancos, guiones o caracteres fuera de `[0-9A-Za-z]`; y la consulta vieja y la nueva dan lo
  mismo en hasta 7 claves (las de códigos con separadores y dos simples).
- **M-T** (antes de desplegar, base `ruesma`): 60 consultas reales con el cliente de la rama:
  coinciden 60 de 60 con la verdad, cero errores, y mediana y máximo dentro de la puerta de
  DA3 (recomendada: mediana ≤ 0,5 s y máximo ≤ 2 s).
- **Despliegue de sv2** (lo pide el humano: «Después se despliega sv2») y, tras él, las M2 y
  M4 pendientes de F-058 (tiempos de `[obra-sigrid]` en Log Analytics).

**Fuera de alcance**: cambiar la semántica de la clave; caché o lista de obras en memoria
(DA10 = B de F-058); índices, vistas o columnas en Sigrid; la conciliación de sv3; cambiar el
tope `OBRA_EXISTE_TIMEOUT_S` (DA5).
