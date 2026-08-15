<!-- progress/mutacion_F-003.md -->
# F-003 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-003` el 2026-08-15 22:47.

## Alcance

Origen del diff: **rama** (`43a35fe95a28cd250f0cc24950a878a61bc6b49d` .. `feature/F-003-sesame-festivos-jornada`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/calendario_provider.py` | 275 |
| `services/partes-front/application/services/jornada_resolver.py` | 51 |
| `services/partes-front/config/settings.py` | 30 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 13 |
| `services/partes-front/infrastructure/sesame/__init__.py` | 1 |
| `services/partes-front/infrastructure/sesame/sesame_api_client.py` | 206 |
| `services/partes-front/infrastructure/transfer/resultado_sigrid.py` | 16 |
| `services/partes-front/interface_adapters/web/app.py` | 288 |
| `services/partes-persistencia/application/services/jornada_resolver.py` | 44 |
| `services/partes-persistencia/application/services/recurso_conciliador.py` | 80 |
| `services/partes-persistencia/config/settings.py` | 26 |
| `services/partes-persistencia/domain/ports/parte_repository.py` | 5 |
| `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py` | 215 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 33 |
| `services/partes-persistencia/infrastructure/sesame/__init__.py` | 1 |
| `services/partes-persistencia/infrastructure/sesame/sesame_api_client.py` | 210 |
| `services/partes-persistencia/interface_adapters/api/app.py` | 43 |
| **Total** | **1537** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 211 |
| Mutantes evaluados | 211 |
| Muertos | 185 |
| Supervivientes | 26 |
| Timeouts | 0 |
| Tiempo total | 437.4 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/calendario_provider.py:84` [entero]

- Original: `ttl_seconds: int = 21600,`
- Mutado:   `ttl_seconds: int = 21601,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-front/application/services/calendario_provider.py:222` [logico]

- Original: `_LOG_PREFIX, dni_norm or "(sin dni)", ano,`
- Mutado:   `_LOG_PREFIX, dni_norm and "(sin dni)", ano,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/partes-front/application/services/calendario_provider.py:230` [logico]

- Original: `_LOG_PREFIX, dni_norm or "(sin dni)", ano, len(mapa), fuente,`
- Mutado:   `_LOG_PREFIX, dni_norm and "(sin dni)", ano, len(mapa), fuente,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/partes-front/application/services/calendario_provider.py:249` [logico]

- Original: `_LOG_PREFIX, exc, dni_norm or "(sin dni)", ano,`
- Mutado:   `_LOG_PREFIX, exc, dni_norm and "(sin dni)", ano,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/partes-front/application/services/calendario_provider.py:255` [logico]

- Original: `_LOG_PREFIX, exc, dni_norm or "(sin dni)", ano,`
- Mutado:   `_LOG_PREFIX, exc, dni_norm and "(sin dni)", ano,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/partes-front/application/services/calendario_provider.py:263` [comparacion]

- Original: `if self._ttl <= 0:`
- Mutado:   `if self._ttl < 0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/partes-front/application/services/jornada_resolver.py:32` [logico]

- Original: `if candef is None or candef == "":`
- Mutado:   `if candef is None and candef == "":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/partes-front/infrastructure/database/parte_repository.py:1388` [entero]

- Original: `reg.sigrid_motivo = (motivo_ok or None) and motivo_ok[:255]`
- Mutado:   `reg.sigrid_motivo = (motivo_ok or None) and motivo_ok[:256]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/partes-front/infrastructure/database/parte_repository.py:1407` [entero]

- Original: `reg.sigrid_motivo = (motivo_ok or None) and motivo_ok[:255]`
- Mutado:   `reg.sigrid_motivo = (motivo_ok or None) and motivo_ok[:256]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/partes-front/infrastructure/sesame/sesame_api_client.py:46` [entero]

- Original: `_MAX_CUERPO = 300`
- Mutado:   `_MAX_CUERPO = 301`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/partes-front/infrastructure/sesame/sesame_api_client.py:153` [entero]

- Original: `transport = self._transport or httpx.HTTPTransport(retries=1)`
- Mutado:   `transport = self._transport or httpx.HTTPTransport(retries=2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/partes-front/interface_adapters/web/app.py:1085` [booleano]

- Original: `@app.get("/api/calendario", include_in_schema=False)`
- Mutado:   `@app.get("/api/calendario", include_in_schema=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/partes-front/interface_adapters/web/app.py:1501` [comparacion]

- Original: `if abs(float(linea.get("horas") or 0.0)) <= 1e-9:`
- Mutado:   `if abs(float(linea.get("horas") or 0.0)) < 1e-9:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/partes-front/interface_adapters/web/app.py:1603` [logico]

- Original: `if degradado and forzar:`
- Mutado:   `if degradado or forzar:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/partes-front/interface_adapters/web/app.py:1607` [logico]

- Original: `settings.default_reviewer or "(sin usuario)",`
- Mutado:   `settings.default_reviewer and "(sin usuario)",`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/partes-persistencia/application/services/jornada_resolver.py:25` [logico]

- Original: `if candef is None or candef == "":`
- Mutado:   `if candef is None and candef == "":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/partes-persistencia/application/services/recurso_conciliador.py:419` [entero]

- Original: `"para revision (%s).", len(docs), ", ".join(docs[:10]),`
- Mutado:   `"para revision (%s).", len(docs), ", ".join(docs[:11]),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/partes-persistencia/config/settings.py:125` [entero]

- Original: `sesame_cache_ttl_s: int = Field(21600, alias="SESAME_CACHE_TTL_S")`
- Mutado:   `sesame_cache_ttl_s: int = Field(21601, alias="SESAME_CACHE_TTL_S")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:60` [entero]

- Original: `ttl_seconds: int = 21600,`
- Mutado:   `ttl_seconds: int = 21601,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:167` [logico]

- Original: `_LOG_PREFIX, dni_norm or "(sin dni)", ano,`
- Mutado:   `_LOG_PREFIX, dni_norm and "(sin dni)", ano,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:175` [logico]

- Original: `_LOG_PREFIX, dni_norm or "(sin dni)", ano, len(mapa),`
- Mutado:   `_LOG_PREFIX, dni_norm and "(sin dni)", ano, len(mapa),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:194` [logico]

- Original: `"revision.", _LOG_PREFIX, exc, dni_norm or "(sin dni)", ano,`
- Mutado:   `"revision.", _LOG_PREFIX, exc, dni_norm and "(sin dni)", ano,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:200` [logico]

- Original: `"revision.", _LOG_PREFIX, exc, dni_norm or "(sin dni)", ano,`
- Mutado:   `"revision.", _LOG_PREFIX, exc, dni_norm and "(sin dni)", ano,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 24. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:205` [comparacion]

- Original: `if self._ttl <= 0:`
- Mutado:   `if self._ttl < 0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 25. `services/partes-persistencia/infrastructure/sesame/sesame_api_client.py:50` [entero]

- Original: `_MAX_CUERPO = 300`
- Mutado:   `_MAX_CUERPO = 301`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 26. `services/partes-persistencia/infrastructure/sesame/sesame_api_client.py:60` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

