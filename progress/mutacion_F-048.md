<!-- progress/mutacion_F-048.md -->
# F-048 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-048` el 2026-10-16 01:23.

## Alcance

Origen del diff: **rama** (`dc034684d39b64ddfb505ec2afedcfd0506d171e` .. `feature/F-048-solo-extras-en-laborable-como-jornada`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/infrastructure/database/orm_models.py` | 3 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 5 |
| `services/partes-persistencia/application/services/parte_normalizer.py` | 30 |
| `services/partes-persistencia/domain/models/parte_records.py` | 3 |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | 3 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 1 |
| **Total** | **45** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 11 |
| Mutantes evaluados | 11 |
| Muertos | 11 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 235.4 s |
| SHA de HEAD medido | `8b616b3a9de45144d0ddc9c8d48b5cbf9ab9bdde` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_sw85f7ed/wk_0/services/partes-persistencia` | 57.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_sw85f7ed/wk_1/services/partes-persistencia` | 53.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_sw85f7ed/wk_2/services/partes-persistencia` | 58.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_sw85f7ed/wk_3/services/partes-persistencia` | 52.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_sw85f7ed/wk_4/services/partes-persistencia` | 51.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_sw85f7ed/wk_5/services/partes-persistencia` | 56.7 |
| Media por mutante evaluado (s) | 21.4 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

