<!-- progress/mutacion_F-019.md -->
# F-019 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-019` el 2026-10-02 23:16.

## Alcance

Origen del diff: **rama** (`b9b3b81b82ed5c737aee3cb7ca6a8c0e8cdf0e24` .. `feature/F-019-mensuales-a-dedicacion`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/congelacion.py` | 58 |
| `services/partes-front/application/services/reparto_obras.py` | 4 |
| `services/partes-front/infrastructure/database/orm_models.py` | 97 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 147 |
| `services/partes-front/infrastructure/transfer/resultado_sigrid.py` | 10 |
| `services/partes-front/interface_adapters/web/app.py` | 26 |
| `services/partes-front/interface_adapters/workers/resultado_consumer.py` | 10 |
| `services/partes-front/main.py` | 10 |
| `services/partes-persistencia/application/services/recurso_conciliador.py` | 4 |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | 97 |
| `services/partes-transfer/application/pipelines/registro_pipeline.py` | 24 |
| `services/partes-transfer/application/services/reglas_registro.py` | 58 |
| `services/partes-transfer/config/settings.py` | 8 |
| `services/partes-transfer/domain/models/registro_models.py` | 17 |
| `services/partes-transfer/interface_adapters/api/app.py` | 8 |
| `services/partes-transfer/interface_adapters/queue/transfer_consumer.py` | 1 |
| `services/partes-transfer/interface_adapters/resultado_json.py` | 2 |
| **Total** | **581** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 126 |
| Mutantes evaluados | 126 |
| Muertos | 125 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 6794.5 s |
| SHA de HEAD medido | `47c0b6467fb4d1331f147bd10727449dfa7e5f8f` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-019_wbw6b92m/wk_0/services/partes-front` | 1091.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-019_wbw6b92m/wk_0/services/partes-persistencia` | 30.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-019_wbw6b92m/wk_0/services/partes-transfer` | 25.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-019_wbw6b92m/wk_1/services/partes-front` | 1082.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-019_wbw6b92m/wk_1/services/partes-persistencia` | 29.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-019_wbw6b92m/wk_1/services/partes-transfer` | 30.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-019_wbw6b92m/wk_2/services/partes-front` | 1090.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-019_wbw6b92m/wk_2/services/partes-persistencia` | 32.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-019_wbw6b92m/wk_2/services/partes-transfer` | 25.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-019_wbw6b92m/wk_3/services/partes-front` | 1084.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-019_wbw6b92m/wk_3/services/partes-persistencia` | 27.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-019_wbw6b92m/wk_3/services/partes-transfer` | 27.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-019_wbw6b92m/wk_4/services/partes-front` | 1082.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-019_wbw6b92m/wk_4/services/partes-persistencia` | 30.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-019_wbw6b92m/wk_4/services/partes-transfer` | 30.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-019_wbw6b92m/wk_5/services/partes-front` | 1090.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-019_wbw6b92m/wk_5/services/partes-persistencia` | 36.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-019_wbw6b92m/wk_5/services/partes-transfer` | 25.3 |
| Media por mutante evaluado (s) | 53.9 |
| Timeout efectivo por mutante (s) | 600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 600 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/interface_adapters/web/app.py:2329` [booleano]

- Original: `@app.post("/api/dedicacion/retirar", include_in_schema=False)`
- Mutado:   `@app.post("/api/dedicacion/retirar", include_in_schema=True)`

#### Análisis

**Hueco real, cerrado con un test nuevo.** Ningún test miraba
`/openapi.json`: publicar la ruta en el esquema no cambia su
comportamiento, pero rompe la norma del portal (todas sus rutas de
escritura van con `include_in_schema=False`). Test nuevo
`test_f019_r21_la_ruta_no_se_publica_en_el_esquema` (sv4,
`tests/test_f019_portal.py`). Verificado a mano aplicando el mutante:
`1 failed` (`'/api/dedicacion/retirar' not in {... '/api/dedicacion/retirar' ...}`);
con el original, `1 passed`.

> Detalle: `progress/impl_F-019.md`, §5.

