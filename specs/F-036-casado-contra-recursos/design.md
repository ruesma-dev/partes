<!-- specs/F-036-casado-contra-recursos/design.md -->
# F-036 · sv3: casar el trabajador leído contra los recursos persona — Diseño

## 1. Encaje y límite de servicio

- **sv3** es quien casa (ingesta) y quien elige el recurso de cada línea
  (conciliador). Las dos cosas pasan a mirar la **misma** lista: los recursos
  persona del `IndicePersonas` que ya carga `SigridMatcherProvider` (F-023).
  El casado elige recurso; el conciliador lo confirma con `elegir_recurso`
  usando el `empleado_reside` guardado como preferido (R15). No hay lectura
  nueva de Sigrid: una columna más (`res.cla`) en la lectura paginada de hoy.
- **sv5** solo gana `res.cla = 1` en `recursos_por_dni`: es la otra mitad de
  la elección por DNI de la lista cerrada (`elegir_recurso` sv3 /
  `elegir_por_dni` sv5, «mismos candidatos»). Ya usa los dos caminos de DNI
  (`emp.dni` vía `res.conide` y `res.cif`): el respaldo «si no hay DNI en el
  recurso, el de la ficha» **ya existe** en sv5 y no se toca su verificación.
- **sv4 no cambia**: los métodos de una línea sin ficha (`recurso_dni`,
  `recurso_nombre`) ya están en su `METODOS_RECURSO` (F-030), así que la cola
  de Conciliar y `esta_casado` funcionan igual. F-035 cambia sus selectores en
  paralelo (ver §8, DA1 y DA3, alineación).
- Ninguna responsabilidad nueva fuera de sv3; nada se copia a otro servicio
  salvo la condición `cla = 1` (DA3, entra en la lista cerrada con guardián).

## 2. Ficheros

Bajo `services/partes-persistencia/` salvo indicación.

| Acción | Ruta | Cambio |
|---|---|---|
| Modificar | `domain/models/sigrid_models.py` | `RecursoRow.cla: int \| None = None` |
| Modificar | `infrastructure/sigrid/sigrid_api_client.py` | `res.cla AS cla` en `_SQL_RECURSOS` y mapeo en `fetch_recursos` (R1) |
| Modificar | `application/services/seleccion_sigrid.py` | `CLA_PERSONA`, filtro persona, `dni_de_recurso`, `ficha_enlazada`, `candidatos_nombre`, `casar_por_dni`; fuera `fichas_candidatas` (§3) |
| Crear | `application/services/casado_recurso.py` | `casar_trabajador` puro (§4) |
| Modificar | `application/services/empleado_matcher.py` | `match_nombre` sobre candidatos por persona (§4) |
| Modificar | `application/services/sigrid_matcher_provider.py` | fuera `Matchers.recursos` e import; INFO de R3 |
| Borrar | `application/services/fichas_de_recurso.py` | R17 |
| Modificar | `application/pipelines/persist_parte_pipeline.py` | `_casar_trabajador` delega en `casar_trabajador`; fuera `_de_recurso` y `_casar_alias`; docstring |
| Modificar | `domain/models/parte_records.py` | comentario de `EmpleadoMatch.method` |
| Crear | `application/services/medicion_casado.py` | núcleo puro de la herramienta (§5) |
| Crear | `medir_casado_recursos.py` | herramienta de consola de solo lectura (§5) |
| Crear/adaptar | `tests/test_f036_*.py` y los de F-023/F-030 afectados | §7 |
| Modificar | `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | `AND res.cla = 1` en las dos ramas de `recursos_por_dni` (R18) |
| Crear | `services/partes-transfer/tests/test_f036_recursos_por_dni_persona.py` | R18 |
| Crear | `tests/test_f036_recurso_persona_gemelos.py` (raíz) | guardián R19 |
| Modificar | `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/referencia/partes-proyecto.md` (§3.3, §4.6, §7), `azure-apps/partes.md` | R29 (§6) |

**No se tocan**: `recurso_conciliador.py` (recibe el filtro a través del
índice), `de_alta`, `esta_congelado`/`ESTADOS_CONGELADOS`, `jornada_resolver.py`,
`text_match.py`, `orm_models.py` (sin cambio de schema), `sqlalchemy_parte_repository.py`,
todo sv4 (incluidos `congelacion.py` y `parte_repository.py`), sv5
`coherencia_recurso.py` y `registro_pipeline.py`, sv1, sv2.

## 3. `IndicePersonas` (sv3, application)

```python
CLA_PERSONA = 1

def es_persona(r: RecursoRow) -> bool:            # r.cla == CLA_PERSONA
class IndicePersonas:
    def dni_de_recurso(self, r: RecursoRow) -> str          # DA1, normalizado; "" si no hay
    def ficha_enlazada(self, r: RecursoRow) -> EmpleadoRow | None   # por res.conide
    def candidatos_nombre(self, empresa: int | None, fecha: int) -> list[RecursoRow]
    def casar_por_dni(self, dni: str | None, empresa: int | None, fecha: int) -> ResolucionRecurso
```

- **Filtro persona (R2)**: en `__init__`, `_recursos_por_conide` y
  `_recursos_por_cif` se llenan solo con `es_persona(r)`. Así `_recursos_de`,
  `elegir_recurso` y `empresas_con_recurso` quedan filtrados sin tocar su
  código; `_recursos`, `recurso()` y `recursos` siguen con todos (el
  conciliador pisa categoría y hora por ide).
- `dni_de_recurso`: `normalize_dni(ficha.dni)` si hay ficha enlazada y no es
  vacío; si no, `normalize_dni(r.cif)` (DA1).
- `candidatos_nombre` (R3, R10): persona, `de_alta(r.fecbaj, fecha)`, empresa
  (o cualquiera si `None`) y `dni_de_recurso(r) != ""`.
- `casar_por_dni` (R4–R5): `f = elegir_ficha(dni, empresa, fecha)`; si es `ok`,
  `elegir_recurso(dni, f.ide, ficha(f.ide).reside, empresa, fecha)`; si no,
  `elegir_recurso(dni, None, None, empresa, fecha)`. Es exactamente el
  desempate que hoy hacen ingesta + conciliador juntos.
- Se borra `fichas_candidatas` (sin uso tras F-036). `elegir_ficha` se queda
  (lo usa `casar_por_dni`).

## 4. Casado (sv3, application)

`application/services/casado_recurso.py`:

```python
def casar_trabajador(*, dni_leido: str | None, nombre_leido: str | None,
                     alias: dict | None, indice: IndicePersonas,
                     matcher: EmpleadoMatcher, empresa: int | None,
                     fecha: int) -> EmpleadoMatch
```

1. **DNI** (R4–R6): si `dni_leido`, `res = indice.casar_por_dni(...)`. `ok` ⇒
   `_a_match(recurso, 1.0, "dni")`; `ambiguo|solo_baja|otra_empresa` ⇒
   `EmpleadoMatch(method=f"dni_{motivo}")` y fin; `desconocido` ⇒ sigue.
2. **Alias** (R8): si `alias`, DNI = `alias["dni"]` o, vacío, el de
   `indice.ficha(alias["ide"])`. Sin DNI ⇒ `alias_no_valido`. `casar_por_dni`:
   `ok` ⇒ `_a_match(recurso, 1.0, "alias")`; `desconocido` ⇒ `alias_no_valido`;
   otro ⇒ `dni_<motivo>`.
3. **Nombre** (R10–R12): `cands = indice.candidatos_nombre(empresa, fecha)`;
   `persona, score, metodo = matcher.match_nombre(nombre=nombre_leido,
   candidatos=[(dni_de_recurso(r), (r.nombre, ficha_enlazada(r).nombre))])`.
   Sin persona ⇒ `EmpleadoMatch(method=metodo)` (`none`/`nombre_ambiguo`). Con
   persona, `casar_por_dni(persona, empresa, fecha)`: `ok` ⇒
   `_a_match(recurso, score, "nombre")`; si no ⇒ `nombre_ambiguo`.

`_a_match(r, score, paso)` (R13–R14): con ficha enlazada `f` ⇒ `ide=f.ide,
codigo=f.codigo, nombre=f.nombre, method=paso`; sin ella ⇒ `ide=None,
codigo=r.codigo, nombre=r.nombre, method="recurso_dni"` si `paso == "dni"` y
`"recurso_nombre"` en otro caso. En los dos: `dni=dni_de_recurso(r)` (canónico)
y `reside=r.ide`.

`EmpleadoMatcher.match_nombre(*, nombre, candidatos: list[tuple[str,
tuple[str | None, ...]]]) -> tuple[str | None, float, str]`: puntuación de
cada candidato = `max(name_similarity(nombre, n) for n in nombres if n)`;
agrupa por persona (máximo de sus recursos); mejor < umbral ⇒ `(None, 0,
"none")`; otra persona con puntuación ≥ mejor ⇒ `(None, 0, "nombre_ambiguo")`;
si no, `(persona, round(mejor, 4), "nombre")`. Se quita `to_match` y `_persona`
(sin uso). `Matchers.empleado` sigue llevando el umbral.

`persist_parte_pipeline._casar_trabajador` queda en: buscar alias solo si hace
falta (sin DNI o `desconocido`: el alias se consulta en la base, como hoy) y
llamar a `casar_trabajador`. Para no consultar la base cuando el DNI ya decide,
`casar_trabajador` recibe `alias` como **callable** perezoso
(`Callable[[], dict | None]`). La caché por `dni|nombre` del bucle no cambia;
`candidatos_nombre` se calcula como mucho una vez por parte (memo local por
`(empresa, fecha)`). `_compute_review_required` y `METODOS_RECURSO` no cambian.

## 5. Herramienta de impacto (solo lectura)

`application/services/medicion_casado.py` (puro, R28):

```python
@dataclass(frozen=True)
class LineaMedida:            # lo que el script lee de la base, sin más
    registro_id: int; document_id: str; empresa: int | None; obra_ide: int | None
    fecha_int: int | None; dni_leido: str | None; nombre_leido: str | None
    empleado_ide: int | None; empleado_dni: str | None; empleado_reside: int | None
    empleado_match_method: str | None; recurso_ide: int | None; congelada: bool

def medir_maestro(indice, recursos, hoy) -> list[dict]            # R24, una fila por empresa
def medir_lineas(lineas, indice, matcher, aliases, hoy) -> list[dict]  # R25-R26, una fila por línea
def resumir(filas) -> dict[str, int]
```

- R25: `elegir_recurso(empleado_dni, empleado_ide, empleado_reside, empresa
  de la obra o del parte, fecha)` frente a `recurso_ide`: `igual`, `cambia`,
  `pierde`, `gana`.
- R26: `casar_trabajador` con `dni_leido`, `nombre_leido` y el alias de
  `aliases` frente a lo guardado: `igual` (mismo `empleado_dni` y `reside`),
  `otra_persona`, `casado_nuevo`, `pierde_casado`. Congeladas: `congelada`.
- `medir_maestro`: de alta a `hoy`, por `empresa`: `persona`, `sin_dni`,
  `dni_solo_ficha` (cif vacío, ficha con DNI), `cif_distinto_ficha` (DA1),
  `mo_no_persona` (`codigo` empieza por `MO/` y `cla != 1`).

`medir_casado_recursos.py` (raíz de sv3, docstring con USO): lee `.env` con
`config/settings.py`; carga los maestros con `SigridApiClient` (las lecturas
paginadas de siempre) y, con una sesión de solo lectura, un SELECT de
`parte_registros` ⨝ `parte_documents` activos y otro de `empleado_alias`; la
congelación con `esta_congelado`. Escribe `logs/medicion_casado_<YYYYMMDD-HHMM>.md`
(resumen y tabla por empresa) y `.csv` (una fila por línea: ids, empresa,
`recurso`/`casado` y su valor), UTF-8 BOM y `;`. Sin nombres ni DNIs (R27).
Se registra en `docs/ARCHITECTURE.md` › Herramientas de consola.

## 6. Documentación (R29)

- `ARCHITECTURE.md` semántica 2: «recurso persona (`res.cla = 1`); el casado
  elige recurso». Semántica 12: sustituir la frase F-030 por la de F-036
  (casado contra recursos persona de la empresa del parte, DNI del recurso,
  qué se guarda). Herramientas de consola: la nueva.
- `partes-proyecto.md` §3.3, §4.6 y §7: mismo cambio, sin repetir el detalle.
- `CLAUDE.md`, lista cerrada: el criterio `res.cla = 1` de sv3
  (`IndicePersonas`, `CLA_PERSONA`) y sv5 (`recursos_por_dni`), vigilado por
  `tests/test_f036_recurso_persona_gemelos.py` (DA3).
- `azure-apps/partes.md`, viñetas Empleado y Recurso; commit local allí.

## 7. Tests (sin red ni PostgreSQL; datos sintéticos)

| Fichero | Cubre |
|---|---|
| `tests/test_f036_maestro.py` | R1 (SQL y mapeo con `_post_sql_read` parcheado), R2, R3 |
| `tests/test_f036_seleccion.py` | `dni_de_recurso`, `ficha_enlazada`, `candidatos_nombre`, `casar_por_dni` (R4, R5, R7) |
| `tests/test_f036_casado.py` | `casar_trabajador`: R4–R14 por tabla de casos |
| `tests/test_f036_pipeline.py` | pipeline con dobles: R6 (alias perezoso), R13, R14, R15 (casado + `conciliar_todos` dan el mismo recurso), R16, R17 (sin `fichas_de_recurso` ni `Matchers.recursos`) |
| `tests/test_f036_medicion.py` | R24–R28 |
| `tests/test_f036_caracterizacion.py` | R20, R21 (en verde antes de tocar nada) |
| sv5 `tests/test_f036_recursos_por_dni_persona.py` | R18 (SQL capturado) |
| raíz `tests/test_f036_recurso_persona_gemelos.py` | R19 (AST/texto, sin importar) |

R9: `git diff` vacío sobre sv4 (tasks). R22: test de que el pipeline no toca
partes ya guardados (el casado solo corre en `_match` de un parte nuevo).
Adaptaciones declaradas: fixtures `RecursoRow` de F-023/F-030 ganan `cla=1`
(helper en `tests/dobles.py`); se borran los tests de `fichas_de_recurso`,
`Matchers.recursos` y `fichas_candidatas`; los de comportamiento de F-030 que
sigan valiendo se reescriben contra `casar_trabajador`; un test de F-023 cuyo
resultado cambie a propósito (R7) se adapta y se lista en `impl_F-036.md`.

## 8. Riesgos y decisiones

- **Cambio de comportamiento buscado**: quien tiene ficha en una empresa y
  recurso persona en otra casa en la segunda (R7). **Cambio colateral**: un
  DNI con dos recursos persona en la empresa sin desempate pasa de «casado sin
  recurso» a «sin casar» (`dni_ambiguo`) y cae en la cola de Conciliar. Nada
  se elige al azar, como siempre. La herramienta cuenta cuántos.
- **`MO/` con `cla != 1`** dejan de casar (F-030 los aceptaba): lo cuenta
  `mo_no_persona` antes de desplegar.
- **Recálculo al desplegar**: cada mensaje de sv3 recorre todas las líneas
  activas no congeladas; con R2, su `recurso_ide` puede cambiar o perderse.
  R25 lo predice. Las congeladas no cambian (R21). Orden: sv3 → sv5.
- **Respaldo F-030 retirado** en vez de mantener dos caminos: el recurso sin
  ficha es ahora un candidato más, y el alias deja de estar limitado a fichas.
- **Alias sin ficha ⇒ `recurso_nombre`** (y no un método nuevo): evita tocar
  sv4 mientras F-035 cambia el mismo `METODOS_RECURSO`. Se pierde distinguir
  alias de nombre en esas líneas; el `score` 1.0 lo delata.
- **Nombre del recurso y de la ficha** puntúan los dos (máximo): nadie que
  hoy casa por el nombre de su ficha deja de hacerlo por usar `con.res`.
- **F-035** (paralela): guarda la misma forma (R13/R14 ≈ sus R12/R13). Hay
  que alinear el criterio de persona (DA3) y el DNI (DA1). Las dos tocan
  `CLAUDE.md` y la semántica 12: conflicto de merge trivial.

## 9. Decisiones abiertas (para el humano)

- **DA1. DNI del recurso cuando `res.cif` y el `emp.dni` de su ficha existen y
  difieren.** El casado acepta los dos (se busca por ambos); solo cambia cuál
  se guarda. Recomendado: **`emp.dni` y, si está vacío, `res.cif`**, la regla
  con la que sv5 verifica (`datos_recursos`) y la de F-035: cero cambios en
  sv5. La literal («`res.cif` y, si no hay, la ficha») obliga a invertir sv5 y
  F-035, y las líneas ya guardadas con el DNI de la ficha fallarían la
  verificación. Solo difieren si los dos datos discrepan: lo cuenta
  `cif_distinto_ficha`.
- **DA2. Re-casar lo ya ingerido.** Recomendado: **no**; solo partes nuevos, y
  lo que quede se arregla en Conciliar (F-035). La herramienta dice cuántas
  líneas cambiarían. Alternativa: una herramienta con `--aplicar` (otra
  feature, escribe en `partes`).
- **DA3. Criterio común de «recurso persona» = `res.cla = 1`** en sv3, sv5
  (R18, guardián R19, nueva entrada en la lista cerrada de `CLAUDE.md`) y en
  F-035, cuyo DA4 propone «`MO/` o con ficha». Recomendado: `cla = 1` en los
  tres (el de `porcentajes`); alternativa: «`MO/` o con ficha» en sv3/sv5.
