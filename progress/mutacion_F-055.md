<!-- progress/mutacion_F-055.md -->
# F-055 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-055` el 2026-11-01 00:56.

## Alcance

Origen del diff: **rama** (`14b3cd52ce301a3bd21f83c1309a44b900a1c813` .. `feature/F-055-sv5-omite-lineas-sin-fecha`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-transfer/application/pipelines/registro_pipeline.py` | 32 |
| `services/partes-transfer/application/services/fecha_linea.py` | 56 |
| `services/partes-transfer/domain/models/registro_models.py` | 5 |
| `services/partes-transfer/interface_adapters/api/app.py` | 3 |
| **Total** | **96** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 28 |
| Mutantes evaluados | 28 |
| Muertos | 26 |
| Supervivientes | 2 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 215.7 s |
| SHA de HEAD medido | `c7f846bcb205c0b081453a5a7e85515977dae8c8` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_56cnthnc/wk_0/services/partes-transfer` | 25.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_56cnthnc/wk_1/services/partes-transfer` | 25.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-055_56cnthnc/wk_2/services/partes-transfer` | 27.3 |
| Media por mutante evaluado (s) | 7.7 |
| Timeout efectivo por mutante (s) | 600 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 600 |
| Workers | 3 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-transfer/domain/models/registro_models.py:42` [entero]

- Original: `return int(self.fecha_int or 0) // 10000`
- Mutado:   `return int(self.fecha_int or 1) // 10000`

#### Análisis (líder, 2026-11-01)

> **Equivalente.** El `or` solo actúa con `fecha_int` falsy (`None` o `0`); entonces el original
> da `int(0) // 10000 = 0` y el mutante `int(1) // 10000 = 0`. Mismo `ano` para toda entrada;
> ningún test puede distinguirlos. Sin test nuevo.

### 2. `services/partes-transfer/domain/models/registro_models.py:46` [entero]

- Original: `return (int(self.fecha_int or 0) // 100) % 100`
- Mutado:   `return (int(self.fecha_int or 1) // 100) % 100`

#### Análisis (líder, 2026-11-01)

> **Equivalente.** Con `fecha_int` falsy el original da `(0 // 100) % 100 = 0` y el mutante
> `(1 // 100) % 100 = 0`; con cualquier otro valor el `or` no actúa. Mismo `mes` para toda
> entrada. Sin test nuevo.

