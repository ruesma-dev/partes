<!-- progress/mutacion_F-042.md -->
# F-042 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-042` el 2026-10-09 12:03.

## Alcance

Origen del diff: **rama** (`824d01cafd03a226a7cc84b1d95528f87dc56867` .. `feature/F-042-recalcular-extras-al-cambiar-fecha`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/config/settings.py` | 6 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 9 |
| `services/partes-front/infrastructure/persistencia/__init__.py` | 1 |
| `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` | 112 |
| `services/partes-front/interface_adapters/web/app.py` | 41 |
| `services/partes-persistencia/interface_adapters/api/app.py` | 3 |
| `services/partes-persistencia/interface_adapters/workers/__init__.py` | 1 |
| `services/partes-persistencia/interface_adapters/workers/despacho.py` | 92 |
| `services/partes-persistencia/interface_adapters/workers/mensajes.py` | 50 |
| `services/partes-persistencia/main_worker.py` | 18 |
| **Total** | **333** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 13 |
| Mutantes evaluados | 13 |
| Muertos | 13 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1674.7 s |
| SHA de HEAD medido | `13ee0fc50d3358852c57baa7be4a34fcbaea80d3` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-042_g5xcfuy7/wk_0/services/partes-front` | 548.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-042_g5xcfuy7/wk_0/services/partes-persistencia` | 22.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-042_g5xcfuy7/wk_1/services/partes-front` | 546.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-042_g5xcfuy7/wk_2/services/partes-front` | 545.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-042_g5xcfuy7/wk_2/services/partes-persistencia` | 23.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-042_g5xcfuy7/wk_3/services/partes-front` | 546.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-042_g5xcfuy7/wk_3/services/partes-persistencia` | 22.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-042_g5xcfuy7/wk_4/services/partes-front` | 546.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-042_g5xcfuy7/wk_4/services/partes-persistencia` | 27.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-042_g5xcfuy7/wk_5/services/partes-front` | 548.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-042_g5xcfuy7/wk_5/services/partes-persistencia` | 22.8 |
| Media por mutante evaluado (s) | 128.8 |
| Timeout efectivo por mutante (s) | 600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 600 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

