<!-- progress/mutacion_F-002.md -->
# F-002 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-002` el 2026-08-13 17:46.

## Alcance

Origen del diff: **rama** (`3c2c6806a04e89f9a04fa88fb1e238dfad0d9d85` .. `feature/F-002-cola-q-transfer`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/config/settings.py` | 27 |
| `services/partes-front/infrastructure/azure/__init__.py` | 2 |
| `services/partes-front/infrastructure/azure/blob_cliente.py` | 70 |
| `services/partes-front/infrastructure/azure/cola_cliente.py` | 200 |
| `services/partes-front/infrastructure/azure/credenciales.py` | 68 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 94 |
| `services/partes-front/infrastructure/transfer/resultado_sigrid.py` | 41 |
| `services/partes-front/infrastructure/transfer/transfer_queue_publisher.py` | 57 |
| `services/partes-front/interface_adapters/web/app.py` | 157 |
| `services/partes-front/interface_adapters/workers/__init__.py` | 6 |
| `services/partes-front/interface_adapters/workers/resultado_consumer.py` | 79 |
| `services/partes-front/main.py` | 79 |
| `services/partes-transfer/application/pipelines/registro_pipeline.py` | 90 |
| `services/partes-transfer/config/settings.py` | 41 |
| `services/partes-transfer/domain/models/registro_models.py` | 20 |
| `services/partes-transfer/infrastructure/azure/__init__.py` | 2 |
| `services/partes-transfer/infrastructure/azure/blob_cliente.py` | 70 |
| `services/partes-transfer/infrastructure/azure/cola_cliente.py` | 138 |
| `services/partes-transfer/infrastructure/azure/credenciales.py` | 68 |
| `services/partes-transfer/interface_adapters/api/app.py` | 27 |
| `services/partes-transfer/interface_adapters/queue/__init__.py` | 6 |
| `services/partes-transfer/interface_adapters/queue/transfer_consumer.py` | 176 |
| `services/partes-transfer/interface_adapters/resultado_json.py` | 29 |
| `services/partes-transfer/main.py` | 83 |
| **Total** | **1630** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 132 |
| Mutantes evaluados | 132 |
| Muertos | 126 |
| Supervivientes | 0 |
| Timeouts | 6 |
| Tiempo total | 1139.5 s |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Timeouts

- `services/partes-front/infrastructure/azure/cola_cliente.py:68` services/partes-front/infrastructure/azure/cola_cliente.py:68 [booleano] self._stop = True -> self._stop = False
- `services/partes-front/infrastructure/azure/cola_cliente.py:159` services/partes-front/infrastructure/azure/cola_cliente.py:159 [booleano] self._stop = True -> self._stop = False
- `services/partes-front/infrastructure/azure/cola_cliente.py:198` services/partes-front/infrastructure/azure/cola_cliente.py:198 [not] if not got and not self._stop: -> if not got and self._stop:
- `services/partes-transfer/infrastructure/azure/cola_cliente.py:65` services/partes-transfer/infrastructure/azure/cola_cliente.py:65 [booleano] self._stop = True -> self._stop = False
- `services/partes-transfer/infrastructure/azure/cola_cliente.py:97` services/partes-transfer/infrastructure/azure/cola_cliente.py:97 [booleano] self._stop = True -> self._stop = False
- `services/partes-transfer/infrastructure/azure/cola_cliente.py:136` services/partes-transfer/infrastructure/azure/cola_cliente.py:136 [not] if not got and not self._stop: -> if not got and self._stop:

