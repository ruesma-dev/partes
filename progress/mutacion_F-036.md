<!-- progress/mutacion_F-036.md -->
# F-036 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-036` el 2026-10-07 20:08.

## Alcance

Origen del diff: **rama** (`6e56244ac08b5565bfb18afd45e63c8d7fbb0280` .. `feature/F-036-casado-contra-recursos`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py` | 38 |
| `services/partes-persistencia/application/services/casado_recurso.py` | 129 |
| `services/partes-persistencia/application/services/empleado_matcher.py` | 41 |
| `services/partes-persistencia/application/services/medicion_casado.py` | 234 |
| `services/partes-persistencia/application/services/seleccion_sigrid.py` | 53 |
| `services/partes-persistencia/application/services/sigrid_matcher_provider.py` | 19 |
| `services/partes-persistencia/domain/models/parte_records.py` | 6 |
| `services/partes-persistencia/domain/models/sigrid_models.py` | 3 |
| `services/partes-persistencia/infrastructure/sigrid/sigrid_api_client.py` | 5 |
| `services/partes-persistencia/medir_casado_recursos.py` | 189 |
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | 7 |
| **Total** | **724** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 113 |
| Mutantes evaluados | 113 |
| Muertos | 103 |
| Supervivientes | 10 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 959.0 s |
| SHA de HEAD medido | `7e06e5e023e167443abdf6756cb4f2bf4b0c22fb` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-036_ryzluufa/wk_0/services/partes-persistencia` | 55.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-036_ryzluufa/wk_1/services/partes-persistencia` | 53.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-036_ryzluufa/wk_2/services/partes-persistencia` | 57.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-036_ryzluufa/wk_3/services/partes-persistencia` | 59.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-036_ryzluufa/wk_4/services/partes-persistencia` | 53.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-036_ryzluufa/wk_5/services/partes-persistencia` | 53.2 |
| Media por mutante evaluado (s) | 8.5 |
| Timeout efectivo por mutante (s) | 600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 600 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-persistencia/application/services/casado_recurso.py:128` [entero]

- Original: `score=round(score, 4), method=metodo,`
- Mutado:   `score=round(score, 5), method=metodo,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-persistencia/application/services/empleado_matcher.py:65` [entero]

- Original: `return ganadora, round(mejor, 4), "nombre"`
- Mutado:   `return ganadora, round(mejor, 5), "nombre"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/partes-persistencia/application/services/medicion_casado.py:51` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/partes-persistencia/application/services/medicion_casado.py:95` [logico]

- Original: `orden = sorted(por_empresa, key=lambda e: (e is None, e or 0))`
- Mutado:   `orden = sorted(por_empresa, key=lambda e: (e is None, e and 0))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/partes-persistencia/application/services/medicion_casado.py:95` [entero]

- Original: `orden = sorted(por_empresa, key=lambda e: (e is None, e or 0))`
- Mutado:   `orden = sorted(por_empresa, key=lambda e: (e is None, e or 1))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/partes-persistencia/application/services/medicion_casado.py:226` [aritmetico]

- Original: `"|---" * (len(COLUMNAS_MAESTRO) + 1) + "|",`
- Mutado:   `"|---" * (len(COLUMNAS_MAESTRO) - 1) + "|",`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/partes-persistencia/application/services/medicion_casado.py:226` [entero]

- Original: `"|---" * (len(COLUMNAS_MAESTRO) + 1) + "|",`
- Mutado:   `"|---" * (len(COLUMNAS_MAESTRO) + 2) + "|",`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/partes-persistencia/application/services/sigrid_matcher_provider.py:123` [not]

- Original: `sin_dni = sum(1 for r in personas if not indice.dni_de_recurso(r))`
- Mutado:   `sin_dni = sum(1 for r in personas if indice.dni_de_recurso(r))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/partes-persistencia/medir_casado_recursos.py:148` [booleano]

- Original: `carpeta.mkdir(parents=True, exist_ok=True)`
- Mutado:   `carpeta.mkdir(parents=False, exist_ok=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/partes-persistencia/medir_casado_recursos.py:189` [entero]

- Original: `sys.exit(main(sys.argv[1:]))`
- Mutado:   `sys.exit(main(sys.argv[2:]))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

