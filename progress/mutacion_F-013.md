<!-- progress/mutacion_F-013.md -->
# F-013 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-013` el 2026-08-17 22:33.

## Alcance

Origen del diff: **rama** (`da7293da005993dee235011b5ac2197b929d6a6d` .. `feature/F-013-informe-validacion-sesame`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/validar_datos_sesame.py` | 573 |
| **Total** | **573** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 74 |
| Mutantes evaluados | 74 |
| Muertos | 71 |
| Supervivientes | 3 |
| Timeouts | 0 |
| Tiempo total | 379.3 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/validar_datos_sesame.py:374` [entero]

- Original: `transporte = transport or httpx.HTTPTransport(retries=1)`
- Mutado:   `transporte = transport or httpx.HTTPTransport(retries=2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-front/validar_datos_sesame.py:384` [comparacion]

- Original: `if respuesta.status_code >= 400:`
- Mutado:   `if respuesta.status_code > 400:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/partes-front/validar_datos_sesame.py:384` [entero]

- Original: `if respuesta.status_code >= 400:`
- Mutado:   `if respuesta.status_code >= 401:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

