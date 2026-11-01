<!-- specs/F-063-consulta-obra-rapida/design.md -->
# F-063 · Consulta de existencia de obra que use el índice — diseño técnico

## 1. Encaje y límite de servicio

- **Solo sv2**: la consulta de obra es de F-058 y vive en sv2
  (`SigridLookupClient.existe_obra`, `ComprobadorObra`). Sigue siendo una lectura por
  sigrid-api contra la base `ruesma`; no es la conciliación de sv3 y la lista cerrada de
  duplicados de `CLAUDE.md` **no crece** (la clave de obra no se copia a otro servicio).
- **Sigrid no se toca**: nada de índices, vistas ni columnas calculadas (solo lecturas por
  sigrid-api). La mejora sale de escribir el filtro sin funciones sobre `con.cod`.

## 2. Lo que hay hoy (`dev` bbc3172) y lo medido

- `_SQL_EXISTE_OBRA` (`services/partes-api/infrastructure/sigrid/sigrid_lookup_client.py`)
  calcula la clave sobre cada `con.cod` con `CROSS APPLY` + `REPLACE` + `PATINDEX` +
  `SUBSTRING` y compara con `COLLATE Latin1_General_CI_AI = ?`; `TOP 1`; `max_rows` del
  cliente (F-038); `truncated` lanza. `con` es la tabla genérica de conceptos de Sigrid (toda
  entidad tiene fila; `con.cod` «Texto de 24»); `obr` son sus propiedades de obra.
- Medido por el líder en sigrid-api (solo lectura, `ruesma`, 2026-10-25): consulta actual
  **12–16 s** (claves 692, 678 y 99999), también con `OPTION (FORCE ORDER)` (13 s); `SELECT 1`
  79 ms; `COUNT(*)` de `obr ⨝ con` 112 ms; `con.cod IN (5 variantes con ceros)` 110–124 ms;
  `con.cod LIKE '%692'` **101 ms**. Lectura: el coste no es el `JOIN` sino evaluar las
  funciones sobre `con.cod`; un predicado simple sobre la columna deja al optimizador el plan
  barato.
- La intercalación de Sigrid es CI (`azure-apps/sigrid_api.md`); si distingue acentos no
  está documentado: el diseño no depende de ello (§5.2).

## 3. Estrategia elegida (DA1 = A) y alternativas

**A (elegida): `LIKE` con comodín entre cada carácter + filtro exacto en Python.** Para la
clave `K = k1…kn` el patrón es `%c1%c2%…%cn%` (`ci` = `ki` o su clase de variantes). Todo
código cuya clave es `K` contiene los caracteres de `K` en orden, con cualquier cosa entre
ellos (blancos, guiones, ceros a la izquierda, espacio duro, marcas de acento), así que **casa
siempre**: la consulta trae un superconjunto y `clave_obra` sobre cada candidato da el
resultado exacto. No se pierden códigos con guiones, espacios o letras, por construcción.
La misma `clave_obra` calcula la clave del código leído y la de cada candidato, así que la
semántica es exactamente la del glosario de F-058 (más fiel que el SQL de hoy, que solo
quitaba `' '` y `'-'`).

Descartadas:
- **B · lista de variantes con ceros (`IN`)**: busca por índice, pero solo cubre ceros a la
  izquierda; `"06-92"`, `"0 692"` o `"6-92"` se pierden salvo generar la combinatoria de
  separadores (inviable con 24 caracteres). Incumple lo que pidió el humano.
- **C · `IN` primero y `LIKE` de respaldo**: dos consultas en el caso «no existe» (el que
  dispara la relectura) y más código para ganar ~10 ms.
- **D · `LIKE '%<clave>'`** (el medido): pierde `"6-92"`, `"06 92"` y `"692-"`.
- **E · `con.tip = 11` u otro filtro extra**: no está verificado que toda obra lo cumpla;
  podría perder obras. No hace falta para el tiempo.

## 4. Ficheros (sin prefijo: `services/partes-api/`)

**A crear**:
- `domain/models/clave_obra.py`: `es_vacio` y `clave_obra`, movidas tal cual desde
  `application/services/relectura_cabecera.py` (§5.1, DA2 = A).
- `tests/test_f063_consulta_obra.py` (§7).

**A modificar**:
- `application/services/relectura_cabecera.py`: borra las dos definiciones e importa
  `es_vacio` y `clave_obra` de `domain.models.clave_obra` (siguen accesibles con el mismo
  nombre; el resto del módulo no cambia).
- `application/services/obra_sigrid.py`: solo el `import` de `clave_obra` (desde el dominio).
- `infrastructure/sigrid/sigrid_lookup_client.py`: `_SQL_EXISTE_OBRA` nuevo (§6),
  `patron_like` y su tabla de variantes (§5.2), `existe_obra` filtra (§5.3); docstrings.
- `tests/test_f058_obra_sigrid.py`: solo las aserciones del SQL que cambia (§7).
- Fuera de sv2: `docs/ARCHITECTURE.md` (punto 18, la frase de la consulta) y
  `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (§3.2: `SELECT TOP 1` ⇒ `LIKE` +
  filtro), con commit local allí.

**NO se tocan**: `domain/ports/existencia_obra_port.py`, el cuerpo de `ComprobadorObra` y su
log, `extract_parte_pipeline.py`, `config/settings.py` (`OBRA_EXISTE_TIMEOUT_S` sigue en 5 s),
`interface_adapters/api/app.py`, `main_worker.py`, `prompts.yaml`, `parte_models.py`,
`fetch_tipos_hora`, `tests/test_f058_relectura_cabecera.py`, `tests/test_f058_prompt.py`,
`tests/test_f058_settings_wiring.py`, `tests/test_f038_lectores_sigrid.py` (el lector sigue
siendo el mismo fichero); sv1, sv3, sv4, sv5, `infra/`; ni `azure-apps/sigrid_api.md`.

## 5. Funciones

### 5.1 `domain/models/clave_obra.py` (domain, puro, sin dependencias)

`es_vacio(valor: object) -> bool` y `clave_obra(codigo: object) -> str`, **mismo cuerpo y
docstring** que hoy (NFKD sin marcas, `upper`, sin blancos (`split`) ni `-`; si `isdigit()`,
`lstrip("0") or "0"`; `""` si vacío). Motivo: la clave es una regla de dominio y la necesitan
application (`ComprobadorObra`, relectura) e infrastructure (el filtro de §5.3); la
infraestructura no importa de application.

### 5.2 `patron_like` (infrastructure, `sigrid_lookup_client.py`)

```python
_ESPECIALES_LIKE = {"%": "[%]", "_": "[_]", "[": "[[]"}

def _tabla_variantes() -> dict[str, frozenset[str]]:
    # Para cada carácter de U+00A0–U+017F cuya clave_obra es UNA letra o dígito ASCII,
    # lo apunta bajo esa base: "A" -> {ª, À, Á, …, à, á, …}, "N" -> {Ñ, ñ, Ń, …},
    # "2" -> {²}, "O" -> {º, Ò, …}. Se calcula una vez al importar (_VARIANTES).

def _clase(c: str) -> str:
    # Especial de LIKE -> su escape; si no, {c, c.lower()} | _VARIANTES.get(c, ∅):
    # un solo elemento -> c tal cual; si no, "[" + "".join(sorted(...)) + "]".

def patron_like(clave: str) -> str:
    """'%' + ''.join(_clase(c) + '%' for c in clave); ValueError si clave == ''."""
```

Ejemplos: `"692"` ⇒ `%6%9%[2²]%`; `"A_1"` ⇒ `%[Aaª…]%[_]%[1¹]%`. La clase incluye la
minúscula y las letras acentuadas, así que el superconjunto se cumple **tanto si la
intercalación distingue acentos y mayúsculas como si no**; si no los distingue, la clase es
redundante pero inocua. Dentro de `[...]` solo van letras y dígitos (ni `^`, `-` ni `]`). El
patrón de una clave de 24 caracteres ronda las 650 posiciones (tope de `LIKE`: 8.000 bytes).
Prototipado por el spec-author (fuera del repo): los 13 ejemplos de R10 y 20.000 códigos
aleatorios (dígitos, letras con y sin acento, blancos, guiones, espacio duro, `²`, `º`, `/`,
`.`, `_`, `%`) casan todos con el patrón de su clave bajo `LIKE` CI y AS emulado.

Límite conocido: un carácter cuya `clave_obra` son **varios** caracteres (`ß` ⇒ `SS`, `½`,
`™`) no casa con su clase; no es de esperar en un código de obra y M-EQ lo detectaría en
cualquier obra real (§9).

### 5.3 `SigridLookupClient.existe_obra` (infrastructure)

```python
def existe_obra(self, clave: str, *, timeout_s: float) -> bool:
    _, rows = self._post_sql_read(sql=_SQL_EXISTE_OBRA, parameters=[patron_like(clave)],
                                  label="existe_obra", timeout_s=timeout_s)
    return any(clave_obra(row[0]) == clave for row in rows if row)
```

Firma, contrato del puerto, tope y errores como hoy (R11). `_post_sql_read` no cambia: pide el
`max_rows` del cliente y `truncated` lanza (R3). Sin `TOP`: cortaría el superconjunto antes
del filtro. `DISTINCT` deja una fila por código (el mismo código en varias empresas).

## 6. SQL (lectura por sigrid-api; ningún fichero `.sql`, ninguna capa de `partes`)

```sql
SELECT DISTINCT con.cod AS codigo
FROM obr JOIN con ON obr.ide = con.ide
WHERE con.cod LIKE ?
```

Base `ruesma` (la de `SIGRID_API_DATABASE`), parámetro = `patron_like(clave)`. Tablas: `obr`
y `con` de Sigrid, solo lectura. Número de filas: las obras cuyo código contiene los
caracteres de la clave en orden; con claves de un carácter (`"1"`) pueden ser muchas — M-T
mide ese peor caso. Si sigrid-api tipa el parámetro como `nvarchar` y `con.cod` es `varchar`,
hay conversión implícita de la columna: por eso M-T mide **con el parámetro**, como lo manda
sv2, y no con el literal.

## 7. Tests (sin red ni BBDD; `test_f063_rN_...`; fixtures inventadas)

`tests/test_f063_consulta_obra.py`:
- Emulador `_like(cadena, patron)` de `LIKE` de T-SQL (`%`, `_`, `[...]`) a `re.fullmatch`
  con `IGNORECASE` y `DOTALL`, **sin** ignorar acentos (el caso más exigente), con sus
  propios tests (`_like("AX1", "%A%[_]%1%")` es `False`, `_like("AX1", "%A%_%1%")` es
  `True`, `_like("á", "%a%")` es `False`).
- R4: los códigos de R10 y un corpus aleatorio con semilla fija (`random.Random(63)`,
  ≥ 5.000 códigos del alfabeto de §5.2) casan con `patron_like(clave_obra(c))`.
- R5–R7: clases de `A`, `N`, `2`, `O` (con `ª`, `Ñ`, `²`, `º`), un dígito sin variantes va tal
  cual, escapes de `%`, `_`, `[` (`"A_1"` no casa con `"AX1"`), `ValueError` con `""`.
- R1–R3 con `httpx.MockTransport` (como `test_f058_obra_sigrid.py`): `parameters ==
  [patron_like(clave)]`, ni la clave ni el patrón en el SQL, un solo `?`, `LIKE ?` presente y
  ausentes `CROSS APPLY`, `COLLATE`, `TOP`, `REPLACE`, `PATINDEX`, `SUBSTRING`, `emp` y
  `fecbaj`; `DISTINCT` presente; `max_rows` del cliente; `truncated` ⇒ `RuntimeError`.
- R8, R10: `existe_obra` con filas inventadas: candidatos exactos ⇒ `True`; solo `"1692"`,
  `"6920"`, `"69-12"` o `None` ⇒ `False`; sin filas ⇒ `False`.
- R9: `domain.models.clave_obra.clave_obra is relectura_cabecera.clave_obra` (y `es_vacio`),
  y `obra_sigrid` y `sigrid_lookup_client` usan esa misma función (identidad de objeto).
- R12: `domain/models/clave_obra.py` no importa nada de `application` ni de
  `infrastructure` (AST).

`tests/test_f058_obra_sigrid.py` (aserciones que F-063 sustituye, nada más):
`test_f058_r7_existe_obra_parametrizada` deja de exigir `"TOP 1"` y `parameters == [CLAVE]`
(pasa a `[patron_like(CLAVE)]`); su respuesta inventada `["09999"]` sigue dando `True`. El
resto del fichero, sin cambios.

## 8. Riesgos y decisiones

- **El tiempo es empírico**: los 101 ms son de `LIKE '%692'` con literal; el patrón con
  comodines y clases, el `DISTINCT` y el parámetro pueden cambiarlo. M-T es la puerta (DA3):
  si no la pasa, `blocked` y decide el humano (opciones: quitar `DISTINCT`, C de §3).
- **Claves cortas**: `"1"` puede traer miles de candidatos; siguen lejos de 500.000 y del
  `truncated`, pero suman transferencia. M-T las incluye.
- **Carga en producción**: igual que F-058, una consulta por página con obra (dos como mucho),
  ahora de ~0,1 s en lugar de ~13 s.
- **Mover `clave_obra` al dominio** (DA2 = A): cambia dos `import` y deja intactos el puerto,
  `ComprobadorObra` y casi todos los tests de F-058. B (el puerto devuelve candidatos y filtra
  `ComprobadorObra`) cambia el contrato y los dobles de dos ficheros de tests de F-058.
- **Equivalencia**: si M-EQ da cero fallos, para **toda** obra de Sigrid su código casa con el
  patrón de su clave, luego `existe_obra(K)` es `True` para toda clave existente; y para una
  clave inexistente el filtro exacto da `False` siempre. Con eso el resultado es el de la
  verdad (§9) para todas las obras, no para una muestra.

## 9. Verificación manual (líder, solo lectura, script fuera del repo, base `ruesma`)

El script importa `patron_like`, `clave_obra`, `SigridLookupClient` y `ComprobadorObra` del
worktree de la rama; credenciales de sigrid-api solo en el proceso; sin escrituras; en el
informe, solo agregados (sin listar códigos).

- **M-EQ · equivalencia exhaustiva**:
  1. `SELECT obr.ide AS ide, con.cod AS codigo FROM obr JOIN con ON obr.ide = con.ide WHERE
     con.cod IS NOT NULL` (sin `truncated`). Anota N obras, claves distintas, códigos con
     blancos o guiones, con ceros a la izquierda y con caracteres fuera de `[0-9A-Za-z -]`
     (por categoría Unicode).
  2. En lotes de ≤ 500 obras: `SELECT v.ide FROM (VALUES (?, ?), …) AS v(ide, pat) JOIN con
     ON con.ide = v.ide WHERE NOT (con.cod LIKE v.pat)` con `pat = patron_like(clave_obra(
     codigo))` ⇒ **cero filas** en todos los lotes. El primer lote lleva además un par
     trampa (`ide` real con `pat = 'ZZZ[_]NO%'`) que **debe** volver: el control sabe fallar.
     Si sigrid-api rechazara `VALUES`, una a una con `SELECT con.cod FROM con WHERE con.ide = ?
     AND NOT (con.cod LIKE ?)`.
  3. Vieja contra nueva: hasta 5 claves de códigos con blancos o guiones (si los hay) y 2
     simples, con el SQL de `dev` (F-058 `design.md` §4.3) y con `existe_obra` de la rama ⇒
     mismo resultado (la vieja tarda ~15 s cada una).
  Va a `progress/impl_F-063.md`. Cualquier fallo en 2 o 3 ⇒ `blocked`.
- **M-T · tiempos** (tras M-EQ): `ComprobadorObra(client=SigridLookupClient(...),
  timeout_s=5)` de la rama, una consulta tras otra: una de calentamiento (aparte) y 60
  medidas: 40 claves al azar de las existentes (semilla 63), `"0"` a `"4"`, hasta 10 claves
  de códigos con letras o separadores y 5 inexistentes (que no estén entre las claves de M-EQ).
  Informe: coincidencias con la verdad de M-EQ (60 de 60), errores (0), mediana, p95 y máximo
  de `ms`, y el máximo de candidatos (contando filas con el cliente). Puerta: DA3.
- **Después**: el humano pide desplegar sv2 (`redeploy_partes.ps1`; ningún agente lo lanza) y
  siguen las M2 y M4 de F-058 (T19 y T20 de su `tasks.md`); M4 lee el mismo
  `[obra-sigrid] … ms=…`.

## 10. Decisiones abiertas

| DA | Tema | Opciones | Recomendación |
|---|---|---|---|
| DA1 | Estrategia de la consulta | A) `LIKE` con `%` entre caracteres + filtro exacto en Python. B) variantes de ceros con `IN`. C) `IN` y `LIKE` de respaldo. (§3) | **A**: único superconjunto garantizado (no pierde guiones, espacios ni letras) con una consulta |
| DA2 | Dónde vive la clave | A) `es_vacio`/`clave_obra` al dominio; filtra el cliente, puerto intacto. B) el puerto devuelve candidatos y filtra `ComprobadorObra` | **A**: menos cambio y una sola función a los dos lados |
| DA3 | Puerta de tiempos (M-T) | A) mediana ≤ 0,5 s, máximo ≤ 2 s (40 % del tope), 0 errores y 60/60. B) solo «todas < 5 s» | **A**: holgura real frente a arranques en frío y reintentos de `httpx`. **Enmendada (humano, 2026-10-26, literal «a»)**: la puerta se mide sobre la consulta con la conexión reutilizada (mediana 92 ms, obra 0 con 822 candidatos 122 ms); desde local cada llamada abre TLS nueva (~1,1 s, igual que `SELECT 1`). Los tiempos reales se vigilan con la M4 de F-058 tras desplegar; reutilizar la conexión en sv2, otra feature si M4 lo pide |
| DA4 | Equivalencia (M-EQ) | A) exhaustiva por `ide` en lotes + 7 claves contra la consulta vieja. B) solo la muestra de M-T | **A**: el humano pidió «idéntico para todas las obras»; son N/500 lecturas baratas |
| DA5 | Tope `OBRA_EXISTE_TIMEOUT_S` | A) sigue en 5 s (DA12 de F-058) y se revisa con M4. B) bajarlo ahora | **A**: sin datos de producción no hay base para moverlo |
