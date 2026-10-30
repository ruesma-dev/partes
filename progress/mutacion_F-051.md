<!-- progress/mutacion_F-051.md -->
# F-051 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-051` el 2026-10-19 13:28.

## Alcance

Origen del diff: **rama** (`85826a227defbe7e4051667ccec998fef9ab52a1` .. `feature/F-051-extraccion-fila-a-fila`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-api/domain/models/parte_models.py` | 8 |
| `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py` | 4 |
| `services/partes-persistencia/application/services/lectura_dudosa.py` | 102 |
| `services/partes-persistencia/application/services/parte_normalizer.py` | 21 |
| `services/partes-persistencia/config/settings.py` | 8 |
| `services/partes-persistencia/domain/models/parte_records.py` | 17 |
| `services/partes-persistencia/interface_adapters/api/app.py` | 2 |
| **Total** | **162** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 31 |
| Mutantes evaluados | 20 |
| Muertos | 17 |
| Supervivientes | 3 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 207.0 s |
| SHA de HEAD medido | `b06420b21abb3c1dbc99df6f6ca8455decf626ed` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-051_5wf8llx4/wk_0/services/partes-persistencia` | 26.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-051_5wf8llx4/wk_1/services/partes-persistencia` | 27.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-051_5wf8llx4/wk_2/services/partes-persistencia` | 26.3 |
| Media por mutante evaluado (s) | 10.4 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 3 |
| Muestreo | sí — 20 de 31 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-persistencia/application/services/lectura_dudosa.py:32` [logico]

- Original: `if value is None or value == "":`
- Mutado:   `if value is None and value == "":`

#### Análisis (implementer, 2026-10-19)

> Por qué ningún test lo caza: es **equivalente**. Con `and`, el atajo no se toma
> nunca, pero los dos valores que cubría acaban igual: `None` cae en
> `float(None)` → `TypeError` → `None`, y `""` cae en `"".strip()` → `float("")` →
> `ValueError` → `None`. Ninguna entrada distingue original y mutante.
> Decisión: **mutante equivalente**, sin test (el atajo es solo legibilidad, igual
> que en `_opt_float` del normalizer).

### 2. `services/partes-persistencia/application/services/lectura_dudosa.py:73` [entero]

- Original: `return tuple(sorted(filas, key=lambda n: (n is None, n or 0)))`
- Mutado:   `return tuple(sorted(filas, key=lambda n: (n is None, n or 1)))`

#### Análisis (implementer, 2026-10-19)

> Por qué ningún test lo caza: hueco real pero estrecho. La clave `n or 1` solo
> difiere de `n or 0` para la fila `0` (que empata con la `1` y conserva el orden
> de entrada); el papel numera 1..14 y ningún test usaba un 0.
> Decisión: **test nuevo** `test_f051_r14_una_fila_cero_se_ordena_antes_que_la_uno`.
> Comprobado a mano con el mutante aplicado: `assert {'tabla_dispersa': (1, 0)} ==
> {'tabla_dispersa': (0, 1)}` → `1 failed, 43 passed`. Campaña no relanzada.

### 3. `services/partes-persistencia/domain/models/parte_records.py:113` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (implementer, 2026-10-19)

> Por qué ningún test lo caza: ningún código actual reasigna ni hashea un
> `MotivoLectura`, así que hoy es equivalente en comportamiento; pero `frozen` es
> decisión de diseño (`design.md` §4 bis: valor inmutable) y sin test se perdería
> en silencio.
> Decisión: **test nuevo** `test_f051_r15_el_motivo_es_inmutable_y_hashable`.
> Comprobado a mano con el mutante aplicado: `Failed: DID NOT RAISE AttributeError`
> → `1 failed, 43 passed`. Campaña no relanzada.

