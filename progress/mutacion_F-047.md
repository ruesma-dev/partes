<!-- progress/mutacion_F-047.md -->
# F-047 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-047` el 2026-10-31 02:38.

## Alcance

Origen del diff: **rama** (`75816f24fc5ef8b0f526e2d8383dc4ebde68e453` .. `feature/F-047-parte-nuevo-en-espera`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/seguimiento_recalculo.py` | 17 |
| `services/partes-front/infrastructure/database/orm_models.py` | 5 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 71 |
| `services/partes-front/interface_adapters/web/app.py` | 35 |
| `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py` | 55 |
| `services/partes-persistencia/domain/ports/parte_repository.py` | 4 |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | 5 |
| `services/partes-persistencia/infrastructure/database/recalculo_seguimiento.py` | 2 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 6 |
| `services/partes-persistencia/interface_adapters/api/app.py` | 5 |
| **Total** | **205** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 32 |
| Mutantes evaluados | 32 |
| Muertos | 32 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 4543.2 s |
| SHA de HEAD medido | `a7b3f4d567b447b98e0c14c5e25d5888b7904be4` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-047_0awq8but/wk_0/services/partes-front` | 657.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-047_0awq8but/wk_0/services/partes-persistencia` | 30.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-047_0awq8but/wk_1/services/partes-front` | 657.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-047_0awq8but/wk_1/services/partes-persistencia` | 30.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-047_0awq8but/wk_2/services/partes-front` | 658.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-047_0awq8but/wk_2/services/partes-persistencia` | 30.2 |
| Media por mutante evaluado (s) | 142.0 |
| Timeout efectivo por mutante (s) | 1317 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 600 |
| Workers | 3 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

