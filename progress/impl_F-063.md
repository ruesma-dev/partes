<!-- progress/impl_F-063.md -->
# F-063 · Informe del implementer — consulta de obra de sv2 que usa el índice

Rama `feature/F-063-consulta-obra-rapida` (worktree `partes-wt-f063`), spec aaef420.
Aprobación del humano (2026-10-25, literal): «f63 ok a todo» ⇒ DA1–DA5 = A. Rigor estándar.
Implementado 2026-10-25/26 (con un corte por límite de uso a mitad de T1, retomado sin pérdida).

## Qué cambió

La consulta de existencia de obra de F-058 (`existe_obra`, 12–16 s en sigrid-api, `ReadTimeout`
con el tope de 5 s) pasa a:

```sql
SELECT DISTINCT con.cod AS codigo
FROM obr JOIN con ON obr.ide = con.ide
WHERE con.cod LIKE ?
```

con un único parámetro, `patron_like(clave)` = `%` y, tras cada carácter de la clave, su clase
de variantes y otro `%` (`"692"` ⇒ `%6%9%[2²]%`). Trae un superconjunto (todo código de esa
clave contiene sus caracteres en orden) y `existe_obra` cuenta solo el candidato cuya
`clave_obra` es exactamente la clave, con la MISMA función que calcula la clave del código leído.

Commits (uno por tarea): 11aef31 T1 · 8259f35 T2 · e1ecb22 T3 · 329ed20 T4 · 2f7e5a5 T5 ·
7fe2ab9 T7 (+ el de este informe). `azure-apps`: a5f739e (T6, solo `partes.md`).

## Ficheros tocados (`git diff --stat dev`, T7)

| Fichero | Cambio |
|---|---|
| `services/partes-api/domain/models/clave_obra.py` | NUEVO: `es_vacio` y `clave_obra` movidas tal cual (mismo cuerpo y docstring) |
| `services/partes-api/application/services/relectura_cabecera.py` | borra las dos definiciones y las importa del dominio (siguen accesibles con el mismo nombre) |
| `services/partes-api/application/services/obra_sigrid.py` | solo el `import` de `clave_obra` |
| `services/partes-api/infrastructure/sigrid/sigrid_lookup_client.py` | `_ESPECIALES_LIKE`, `_tabla_variantes`/`_VARIANTES`, `_clase`, `patron_like`; `_SQL_EXISTE_OBRA` nuevo; `existe_obra` filtra; docstrings |
| `services/partes-api/tests/test_f063_consulta_obra.py` | NUEVO: 89 tests (emulador de `LIKE` y R1–R10, R12) |
| `services/partes-api/tests/test_f058_obra_sigrid.py` | solo `test_f058_r7_existe_obra_parametrizada`: `parameters == [patron_like(CLAVE)]` y `"LIKE ?"` en lugar de `"TOP 1"` (+ el import) |
| `docs/ARCHITECTURE.md` | punto 20 (ver desviaciones): la consulta nueva |
| `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` | §3.2: `SELECT TOP 1` ⇒ `LIKE` parametrizado + filtro exacto en sv2 |
| `harness/features.json`, `BACKLOG.md`, `progress/current.md`, `specs/.../tasks.md` | estado, aprobación literal, tareas marcadas |

No cambian (R11, R12): `ExistenciaObraPort`, `ComprobadorObra` y su log `[obra-sigrid]`, el
pipeline, `Settings`, `OBRA_EXISTE_TIMEOUT_S` (5 s), `fetch_tipos_hora`, `_post_sql_read`
(sigue pidiendo el `max_rows` del cliente y `truncated` lanza), sv1/sv3/sv4/sv5, `infra/`,
`prompts.yaml`, `parte_models.py`, `LECTORES_ESPERADOS` de F-038.

## Decisiones de diseño

- **Tabla de variantes** (`_tabla_variantes`, calculada una vez al importar): cada carácter
  alfanumérico de U+00A0–U+017F cuya `clave_obra` es UN carácter alfanumérico se apunta bajo esa
  base. `_clase(c)`: especial de `LIKE` ⇒ su escape (`[%]`, `[_]`, `[[]`); si no,
  `{c, c.lower()} ∪ variantes`, un elemento ⇒ `c` tal cual, si no `[...]` ordenado. Dentro de
  los corchetes solo hay letras y dígitos (nunca `^`, `-`, `]`). Patrón de 24 `A` = 577
  caracteres (tope de `LIKE`: 8.000 bytes).
- **Clave vacía**: `patron_like("")` lanza `ValueError`, así que `existe_obra("")` lanza antes
  de llamar a sigrid-api (test `test_f063_r7_clave_vacia_no_consulta`); `ComprobadorObra` ya no
  consultaba con clave vacía.
- `existe_obra`: `any(clave_obra(row[0]) == clave for row in rows if row)`: filas vacías y
  `None` no cuentan (`clave_obra(None) == ""` ≠ clave no vacía).

## Desviaciones respecto a la spec (también en `progress/current.md`)

1. `docs/ARCHITECTURE.md`: la frase de la consulta está en el **punto 20** (F-058), no en el
   18 que cita la spec (el 18 es F-054). Se actualizó el 20; el diff solo toca esa frase.
2. **Bases no ASCII en la tabla**: `design.md` §5.2 decía «letra o dígito ASCII»; R5 pide
   la clase para todo carácter cuya forma `clave_obra` sea la de otros del rango. Caso real:
   `µ` (U+00B5) tiene la clave `Μ` (griega); con la tabla solo ASCII, un código con `µ` no casaría
   con su patrón. Se generaliza a letra o dígito único; las clases de las bases ASCII no
   cambian. Test: `test_f063_r5_letra_no_latina_con_variante_del_rango`.
3. **Emulador de `LIKE` por programación dinámica**, no `re.fullmatch` (§7): compilar miles de
   clases Unicode con `re.IGNORECASE` llevaba el corpus a 12 s (perfilado: `_optimize_charset`).
   Misma semántica (no distingue mayúsculas, sí acentos), con sus propios tests; el fichero
   entero tarda ~2–3 s. Comprobado que el corpus **sabe fallar**: con un `patron_like` ingenuo
   sin clases (`%6%9%2%`), `test_f063_r4_corpus_aleatorio_casa_con_su_patron` falla.
4. T2: los tests de R9/R12 no pueden correr hasta T3 (el fichero importa `patron_like` en la
   cabecera). En T2 se verificó a mano la identidad (`relectura_cabecera.clave_obra is
   domain.models.clave_obra.clave_obra`, ídem `es_vacio` y `obra_sigrid`) y los 118 tests de
   F-058 en verde sin tocarlos; desde T3, los tests de R9/R12 en verde.
5. `test_f058_r7_existe_obra_pide_el_max_rows_del_cliente` conserva su docstring «el `TOP 1`
   acota la respuesta», ya inexacto: §7 limita el cambio a las aserciones de otro test. Lo decide
   el reviewer.

## Fase RED (trazas reales)

**T1** — tests escritos antes que el código:

```
$ cd services/partes-api && python -m pytest tests/test_f063_consulta_obra.py
collected 0 items / 1 error
______________ ERROR collecting tests/test_f063_consulta_obra.py ______________
tests\test_f063_consulta_obra.py:28: in <module>
    from domain.models import clave_obra as modulo_clave
E   ImportError: cannot import name 'clave_obra' from 'domain.models' (unknown location)
ERROR tests/test_f063_consulta_obra.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
============================== 1 error in 0.39s ===============================
```

**Antes de T4** (con T2 y T3 hechos; la consulta y `existe_obra` aún eran las de F-058), los
requisitos centrales R1/R2, R7 y R8 en rojo por comportamiento, no por import:

```
$ python -m pytest tests/test_f063_consulta_obra.py -q -k "r1 or r8 or r7_clave_vacia_no_consulta"
E       AssertionError: assert ['692'] == ['%6%9%[2²]%']
E         At index 0 diff: '692' != '%6%9%[2²]%'
E       Failed: DID NOT RAISE ValueError
E       AssertionError: assert True is False
E        +  where True = existe_obra('692', timeout_s=5.0)
   (… la misma aserción en los demás casos de R8, y con existe_obra('A12', …))
FAILED tests/test_f063_consulta_obra.py::test_f063_r1_r2_un_like_parametrizado_sin_funciones
FAILED tests/test_f063_consulta_obra.py::test_f063_r7_clave_vacia_no_consulta
FAILED tests/test_f063_consulta_obra.py::test_f063_r8_sin_candidato_exacto_es_false[filas0..filas5]
FAILED tests/test_f063_consulta_obra.py::test_f063_r8_letras_de_otra_clave_no_cuentan
9 failed, 80 passed
```

(`["1692"]`, `["6920"]`, `["69-12"]`, `[None]`… daban `True` con el `len(rows) >= 1` de F-058.)
Tras T4: `89 passed`.

## Verificación ejecutada (resultado real)

- `python -m pytest tests/test_f063_consulta_obra.py` (sv2): **89 passed in 1.96s**.
- `python -m pytest` de sv2: **420 passed, 1 warning in 11.39s** (el aviso es el
  `StarletteDeprecationWarning` de `fastapi.testclient`, previo: también está en `dev`).
- `python -m pytest tests/test_f058_relectura_cabecera.py tests/test_f058_obra_sigrid.py`
  (en T2, sin tocarlos): **118 passed**.
- `python -m pytest tests/test_f038_lectores_sigrid.py` desde la raíz: **24 passed**.
- `python -m ruff check` de los ficheros tocados (desde la raíz): **All checks passed!**
- `git diff --stat dev` (T7): solo los ficheros de §4 más `docs/`, `specs/`, `progress/`,
  `harness/features.json` y `BACKLOG.md`.
- `bash harness/init.sh`: **ENTORNO LISTO** (raíz 522 passed / 3 skipped; sv2 420 passed;
  `PUERTA COBERTURA: 100.0% de 43 líneas cambiadas cubiertas`; `PUERTA TAMAÑO` dentro).

## Medición del líder en sigrid-api (solo lectura, 2026-10-25)

Con `SELECT DISTINCT con.cod FROM obr JOIN con ON obr.ide = con.ide WHERE con.cod LIKE ?`:
`%6%9%2%` 123 ms (1 fila), `%6%7%8%` 93 ms, `%9%9%9%9%9%` 111 ms (0 filas), `%1%` 103 ms
(353 filas), `%0%` 108 ms (822 filas). La primera llamada en frío a sigrid-api (`SELECT 1`)
tardó 4,5 s: M-T lleva una consulta de calentamiento aparte. Frente a 12–16 s de la de F-058.

## Pendiente (no lo ejecuta el implementer)

- **T8 · mutación** (la lanza el líder): `python -m harness.mutacion --feature F-063` desde la
  raíz del worktree ⇒ `progress/mutacion_F-063.md`, con el análisis de cada superviviente.
- **T9 · M-EQ y T10 · M-T** (líder, solo lectura, `ruesma`): script fuera del repo, probado en
  seco con dobles (M-EQ OK y M-T 60/60 sobre datos inventados), comando exacto en
  `progress/current.md`. Sus agregados van a la sección siguiente. Fallo ⇒ `blocked`.
- **T12** (humano): tras el APPROVED y la fusión, pedir el despliegue de sv2; después M2/M4 de
  F-058.

## Fuera de alcance

Cambiar la semántica de la clave; caché o lista de obras en memoria; índices, vistas o columnas
en Sigrid; la conciliación de sv3; el tope `OBRA_EXISTE_TIMEOUT_S` (sigue en 5 s, DA5).
Límite conocido (`design.md` §5.2): un carácter cuya clave son varios (`ß` ⇒ `SS`, `Ŀ`, `½`) no
casa con su clase; M-EQ lo cuenta (`con_caracter_de_clave_multiple`) y lo detectaría.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | sv2: 420 passed (89 de F-063); raíz: 522 passed, 3 skipped; F-038: 24 passed |
| Cobertura de las líneas cambiadas | **100,0 %** (43/43, umbral 80 %, `PUERTA COBERTURA` de `init.sh`) |
| Mutantes generados / supervivientes | **PENDIENTE del líder** (T8): `python -m harness.mutacion --feature F-063` ⇒ `progress/mutacion_F-063.md` |
| Tiempo de la suite | sv2: 11,39 s (44,98 s con cobertura dentro de `init.sh`); `test_f063_consulta_obra.py`: 1,96 s |
| M-EQ (T9) | PENDIENTE del líder |
| M-T (T10) | PENDIENTE del líder |
