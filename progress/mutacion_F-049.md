<!-- progress/mutacion_F-049.md -->
# F-049 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-049` el 2026-10-23 03:32.

## Alcance

Origen del diff: **rama** (`2bfeab74f3d57461b4750519e23362cf05948303` .. `feature/F-049-editor-calendario-normal-y-extra`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/edicion_celda.py` | 208 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 361 |
| `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` | 3 |
| `services/partes-front/interface_adapters/web/app.py` | 189 |
| `services/partes-persistencia/infrastructure/database/recalculo_seguimiento.py` | 14 |
| **Total** | **775** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 164 |
| Mutantes evaluados | 164 |
| Muertos | 162 |
| Supervivientes | 2 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 44292.9 s |
| SHA de HEAD medido | `4f73add1cb3b1a62ed4e7ac048158f81a287393d` |
| Línea base (s) — `services/partes-front` | 413.9 |
| Línea base (s) — `services/partes-persistencia` | 37.0 |
| Media por mutante evaluado (s) | 270.1 |
| Timeout efectivo por mutante (s) | 828 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 300 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/infrastructure/database/parte_repository.py:3229` [comparacion]

- Original: `if reg is not None:`
- Mutado:   `if reg is None:`

#### Análisis (implementer, 2026-10-23): hueco real, test nuevo

> Por qué ningún test lo caza: en `_deshacer_creadas` el bucle sobre
> `payload["registros"]` mete en `regs` las líneas del snapshot para calcular
> la celda y sus afectadas (R26, R38). Todos los tests de deshacer con
> afectadas no vacías (`test_f049_r26_r27_deshacer_e12_…`) creaban una línea
> nueva, y las `creadas` ya bastan para encontrar la celda; los que solo
> editaban tenían afectadas `[]`. Con el mutante, un deshacer que solo edita
> se queda sin `regs` y devuelve `afectadas == []`, que nadie comprobaba.
> `document_ids` no lo delata porque también sale del snapshot.
> Decisión: hueco real. Test nuevo
> `test_f049_r26_r38_deshacer_sin_creadas_da_las_afectadas` (E12 que solo
> edita, sin creadas; deshacer da `[AFECTADA_X]`). Mutante aplicado a mano:
> `E       AssertionError: assert [] == [{'obra_key':...lada': False}]` ·
> `1 failed`; revertido, `97 passed` en `test_f049_guardar_celda.py`.

### 2. `services/partes-front/interface_adapters/web/app.py:2245` [logico]

- Original: `if sigrid_client is None or not reside:`
- Mutado:   `if sigrid_client is None and not reside:`

#### Análisis (implementer, 2026-10-23): hueco real, test nuevo

> Por qué ningún test lo caza: los tests de R21 cubrían Sigrid sin configurar
> (`sigrid_client is None`, ahí `and` y `or` acaban igual: la llamada sobre
> `None` lanza `AttributeError`, el `except` la captura y devuelve `None`) y
> recurso presente. Faltaba la celda con plantilla y SIN recurso (clave
> `emp-`, ficha sin `recurso_ide` ni `empleado_reside`): con el mutante se
> consulta `fetch_hora_extra_recurso(None)` y la extra nueva se crea con el
> código que devuelva Sigrid, que no es del recurso.
> Decisión: hueco real. Test nuevo
> `test_f049_r21_extra_nueva_sin_recurso_no_pregunta_a_sigrid` (comprueba
> `reside None` en el contexto, extra creada sin código y Sigrid sin
> llamadas). Mutante aplicado a mano:
> `E       AssertionError: assert ('extra', 1.5, 31, 'HE01') == ('extra', 1.5, None, None)` ·
> `1 failed`; revertido, `97 passed`.


## Cierre (implementer)

Los 2 supervivientes eran huecos reales y los mata un test nuevo cada uno
(comprobado aplicando el mutante a mano y revirtiéndolo). No se relanzó la
campaña completa (44.292,9 s). **0 supervivientes sin resolver.**
