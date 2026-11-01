<!-- progress/mutacion_F-053.md -->
# F-053 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-053` el 2026-10-21 08:37.

## Alcance

Origen del diff: **rama** (`12e1f2399a26da6b1323506a0942f3da44447180` .. `feature/F-053-pisar-sin-borrar`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/congelacion.py` | 5 |
| `services/partes-front/application/services/reparto_obras.py` | 2 |
| `services/partes-front/infrastructure/transfer/transfer_queue_publisher.py` | 3 |
| `services/partes-front/interface_adapters/web/app.py` | 3 |
| `services/partes-transfer/application/pipelines/registro_pipeline.py` | 108 |
| `services/partes-transfer/application/services/parte_abierto.py` | 32 |
| `services/partes-transfer/application/services/pisado.py` | 106 |
| `services/partes-transfer/domain/models/registro_models.py` | 5 |
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | 44 |
| `services/partes-transfer/interface_adapters/queue/transfer_consumer.py` | 4 |
| `services/partes-transfer/interface_adapters/resultado_json.py` | 2 |
| **Total** | **314** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 57 |
| Mutantes evaluados | 57 |
| Muertos | 57 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1017.8 s |
| SHA de HEAD medido | `dcf427ac7ed83632b8ee21a18c52c49efb75c0a1` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-053_6y_7vgat/wk_0/services/partes-front` | 437.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-053_6y_7vgat/wk_0/services/partes-transfer` | 9.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-053_6y_7vgat/wk_1/services/partes-front` | 436.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-053_6y_7vgat/wk_1/services/partes-transfer` | 9.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-053_6y_7vgat/wk_2/services/partes-transfer` | 24.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-053_6y_7vgat/wk_3/services/partes-transfer` | 23.5 |
| Media por mutante evaluado (s) | 17.9 |
| Timeout efectivo por mutante (s) | 875 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 300 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

