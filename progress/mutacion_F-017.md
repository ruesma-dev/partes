<!-- progress/mutacion_F-017.md -->
# F-017 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-017` el 2026-08-20 16:53.

## Alcance

Origen del diff: **rama** (`4ca131c1f13f953e7f5811b5cf9075ff0ab17ece` .. `feature/F-017-identidad-easy-auth`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/interface_adapters/web/app.py` | 143 |
| `services/partes-front/interface_adapters/web/identidad.py` | 257 |
| **Total** | **400** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 31 |
| Mutantes evaluados | 31 |
| Muertos | 30 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Tiempo total | 468.2 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/interface_adapters/web/identidad.py:117` [booleano]

- Original: `crudo = base64.b64decode(token, validate=True)`
- Mutado:   `crudo = base64.b64decode(token, validate=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

