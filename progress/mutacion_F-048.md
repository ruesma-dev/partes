<!-- progress/mutacion_F-048.md -->
# F-048 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-048` el 2026-10-16 01:42.

## Alcance

Origen del diff: **rama** (`dc034684d39b64ddfb505ec2afedcfd0506d171e` .. `feature/F-048-solo-extras-en-laborable-como-jornada`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/infrastructure/database/orm_models.py` | 3 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 5 |
| `services/partes-persistencia/application/services/parte_normalizer.py` | 33 |
| `services/partes-persistencia/domain/models/parte_records.py` | 3 |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | 3 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 1 |
| **Total** | **48** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 12 |
| Mutantes evaluados | 12 |
| Muertos | 11 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 206.4 s |
| SHA de HEAD medido | `6166ab157ba19d3ec87003651d2659e33fbe94d1` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_0qrndbuo/wk_0/services/partes-persistencia` | 52.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_0qrndbuo/wk_1/services/partes-persistencia` | 50.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_0qrndbuo/wk_2/services/partes-persistencia` | 49.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_0qrndbuo/wk_3/services/partes-persistencia` | 48.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_0qrndbuo/wk_4/services/partes-persistencia` | 49.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_0qrndbuo/wk_5/services/partes-persistencia` | 49.2 |
| Media por mutante evaluado (s) | 17.2 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-persistencia/application/services/parte_normalizer.py:294` [entero]

- Original: `leidas = (round(min(p_horas, acumulado - ord_leidas), 2)`
- Mutado:   `leidas = (round(min(p_horas, acumulado - ord_leidas), 3)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

