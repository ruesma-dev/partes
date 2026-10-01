<!-- progress/mutacion_F-021.md -->
# F-021 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-021` el 2026-10-01 18:00.

## Alcance

Origen del diff: **rama** (`c115f73339fb23b05feddddc71522711b908e6f2` .. `feature/F-021-cuenta-analitica-sigrid`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-transfer/application/pipelines/registro_pipeline.py` | 52 |
| `services/partes-transfer/application/services/cuenta_analitica.py` | 96 |
| `services/partes-transfer/domain/models/registro_models.py` | 13 |
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | 46 |
| `services/partes-transfer/prueba_escritura_sigrid.py` | 6 |
| **Total** | **213** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 35 |
| Mutantes evaluados | 35 |
| Muertos | 33 |
| Supervivientes | 2 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 79.3 s |
| SHA de HEAD medido | `b038943bab598f5ae7ecf4de8a11757218580683` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-021_1s_485pb/wk_0/services/partes-transfer` | 11.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-021_1s_485pb/wk_1/services/partes-transfer` | 11.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-021_1s_485pb/wk_2/services/partes-transfer` | 11.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-021_1s_485pb/wk_3/services/partes-transfer` | 11.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-021_1s_485pb/wk_4/services/partes-transfer` | 11.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-021_1s_485pb/wk_5/services/partes-transfer` | 11.5 |
| Media por mutante evaluado (s) | 2.3 |
| Timeout efectivo por mutante (s) | 600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 600 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-transfer/application/pipelines/registro_pipeline.py:216` [entero]

- Original: `horas.get(int(a.recurso_ide or 0), []), a.hora_ide)`
- Mutado:   `horas.get(int(a.recurso_ide or 1), []), a.hora_ide)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-transfer/domain/models/registro_models.py:76` [booleano]

- Original: `defecto: bool = False`
- Mutado:   `defecto: bool = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

