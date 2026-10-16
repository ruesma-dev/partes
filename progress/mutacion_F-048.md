<!-- progress/mutacion_F-048.md -->
# F-048 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-048` el 2026-10-16 01:46.

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
| Muertos | 12 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 199.2 s |
| SHA de HEAD medido | `72b1c7f90522a7dd322581edc6a02891043e2eeb` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_9a6s1xhr/wk_0/services/partes-persistencia` | 43.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_9a6s1xhr/wk_1/services/partes-persistencia` | 42.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_9a6s1xhr/wk_2/services/partes-persistencia` | 42.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_9a6s1xhr/wk_3/services/partes-persistencia` | 43.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_9a6s1xhr/wk_4/services/partes-persistencia` | 44.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_9a6s1xhr/wk_5/services/partes-persistencia` | 43.0 |
| Media por mutante evaluado (s) | 16.6 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

