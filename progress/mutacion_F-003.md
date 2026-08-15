<!-- progress/mutacion_F-003.md -->
# F-003 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-003` el 2026-08-15 22:12.

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
| `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py` | 211 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 33 |
| `services/partes-persistencia/infrastructure/sesame/__init__.py` | 1 |
| `services/partes-persistencia/infrastructure/sesame/sesame_api_client.py` | 210 |
| `services/partes-persistencia/interface_adapters/api/app.py` | 43 |
| **Total** | **1533** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 211 |
| Mutantes evaluados | 211 |
| Muertos | 154 |
| Supervivientes | 57 |
| Timeouts | 0 |
| Tiempo total | 467.3 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/calendario_provider.py:61` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-front/application/services/calendario_provider.py:70` [booleano]

- Original: `fiable: bool = True`
- Mutado:   `fiable: bool = False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/partes-front/application/services/calendario_provider.py:84` [entero]

- Original: `ttl_seconds: int = 21600,`
- Mutado:   `ttl_seconds: int = 21601,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/partes-front/application/services/calendario_provider.py:222` [logico]

- Original: `_LOG_PREFIX, dni_norm or "(sin dni)", ano,`
- Mutado:   `_LOG_PREFIX, dni_norm and "(sin dni)", ano,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/partes-front/application/services/calendario_provider.py:230` [logico]

- Original: `_LOG_PREFIX, dni_norm or "(sin dni)", ano, len(mapa), fuente,`
- Mutado:   `_LOG_PREFIX, dni_norm and "(sin dni)", ano, len(mapa), fuente,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/partes-front/application/services/calendario_provider.py:249` [logico]

- Original: `_LOG_PREFIX, exc, dni_norm or "(sin dni)", ano,`
- Mutado:   `_LOG_PREFIX, exc, dni_norm and "(sin dni)", ano,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/partes-front/application/services/calendario_provider.py:255` [logico]

- Original: `_LOG_PREFIX, exc, dni_norm or "(sin dni)", ano,`
- Mutado:   `_LOG_PREFIX, exc, dni_norm and "(sin dni)", ano,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/partes-front/application/services/calendario_provider.py:263` [comparacion]

- Original: `if self._ttl <= 0:`
- Mutado:   `if self._ttl < 0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/partes-front/application/services/calendario_provider.py:263` [entero]

- Original: `if self._ttl <= 0:`
- Mutado:   `if self._ttl <= 1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/partes-front/application/services/calendario_provider.py:269` [comparacion]

- Original: `if (self._reloj() - entrada[0]) >= self._ttl:`
- Mutado:   `if (self._reloj() - entrada[0]) > self._ttl:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/partes-front/application/services/jornada_resolver.py:32` [logico]

- Original: `if candef is None or candef == "":`
- Mutado:   `if candef is None and candef == "":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/partes-front/infrastructure/database/parte_repository.py:1388` [entero]

- Original: `reg.sigrid_motivo = (motivo_ok or None) and motivo_ok[:255]`
- Mutado:   `reg.sigrid_motivo = (motivo_ok or None) and motivo_ok[:256]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/partes-front/infrastructure/database/parte_repository.py:1407` [logico]

- Original: `reg.sigrid_motivo = (motivo_ok or None) and motivo_ok[:255]`
- Mutado:   `reg.sigrid_motivo = (motivo_ok and None) and motivo_ok[:255]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/partes-front/infrastructure/database/parte_repository.py:1407` [entero]

- Original: `reg.sigrid_motivo = (motivo_ok or None) and motivo_ok[:255]`
- Mutado:   `reg.sigrid_motivo = (motivo_ok or None) and motivo_ok[:256]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/partes-front/infrastructure/sesame/sesame_api_client.py:46` [entero]

- Original: `_MAX_CUERPO = 300`
- Mutado:   `_MAX_CUERPO = 301`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/partes-front/infrastructure/sesame/sesame_api_client.py:49` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/partes-front/infrastructure/sesame/sesame_api_client.py:56` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/partes-front/infrastructure/sesame/sesame_api_client.py:153` [entero]

- Original: `transport = self._transport or httpx.HTTPTransport(retries=1)`
- Mutado:   `transport = self._transport or httpx.HTTPTransport(retries=2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `services/partes-front/infrastructure/sesame/sesame_api_client.py:164` [logico]

- Original: `texto = (response.text or "")[:_MAX_CUERPO]`
- Mutado:   `texto = (response.text and "")[:_MAX_CUERPO]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `services/partes-front/infrastructure/sesame/sesame_api_client.py:170` [comparacion]

- Original: `if status >= 400:`
- Mutado:   `if status > 400:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `services/partes-front/infrastructure/sesame/sesame_api_client.py:170` [entero]

- Original: `if status >= 400:`
- Mutado:   `if status >= 401:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `services/partes-front/infrastructure/sesame/sesame_api_client.py:180` [booleano]

- Original: `if not isinstance(cuerpo, dict) or not cuerpo.get("ok", False):`
- Mutado:   `if not isinstance(cuerpo, dict) or not cuerpo.get("ok", True):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `services/partes-front/interface_adapters/web/app.py:332` [logico]

- Original: `len(settings.sesame_api_key or ""),`
- Mutado:   `len(settings.sesame_api_key and ""),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 24. `services/partes-front/interface_adapters/web/app.py:546` [logico]

- Original: `if _d.in_period and _d.date_iso`
- Mutado:   `if _d.in_period or _d.date_iso`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 25. `services/partes-front/interface_adapters/web/app.py:1085` [booleano]

- Original: `@app.get("/api/calendario", include_in_schema=False)`
- Mutado:   `@app.get("/api/calendario", include_in_schema=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 26. `services/partes-front/interface_adapters/web/app.py:1100` [entero]

- Original: `d1 = date.fromisoformat(str(desde)[:10])`
- Mutado:   `d1 = date.fromisoformat(str(desde)[:11])`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 27. `services/partes-front/interface_adapters/web/app.py:1101` [entero]

- Original: `d2 = date.fromisoformat(str(hasta)[:10])`
- Mutado:   `d2 = date.fromisoformat(str(hasta)[:11])`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 28. `services/partes-front/interface_adapters/web/app.py:1104` [booleano]

- Original: `{"ok": False, "error": "desde/hasta deben ser YYYY-MM-DD"},`
- Mutado:   `{"ok": True, "error": "desde/hasta deben ser YYYY-MM-DD"},`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 29. `services/partes-front/interface_adapters/web/app.py:1108` [booleano]

- Original: `{"ok": False, "error": "hasta no puede ser anterior a desde"},`
- Mutado:   `{"ok": True, "error": "hasta no puede ser anterior a desde"},`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 30. `services/partes-front/interface_adapters/web/app.py:1113` [booleano]

- Original: `{"ok": False,`
- Mutado:   `{"ok": True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 31. `services/partes-front/interface_adapters/web/app.py:1501` [comparacion]

- Original: `if abs(float(linea.get("horas") or 0.0)) <= 1e-9:`
- Mutado:   `if abs(float(linea.get("horas") or 0.0)) < 1e-9:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 32. `services/partes-front/interface_adapters/web/app.py:1563` [booleano]

- Original: `sin_sesame: bool = False) -> None:`
- Mutado:   `sin_sesame: bool = True) -> None:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 33. `services/partes-front/interface_adapters/web/app.py:1599` [booleano]

- Original: `{"ok": False, "error": MOTIVO_BLOQUEO_SESAME,`
- Mutado:   `{"ok": True, "error": MOTIVO_BLOQUEO_SESAME,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 34. `services/partes-front/interface_adapters/web/app.py:1603` [logico]

- Original: `if degradado and forzar:`
- Mutado:   `if degradado or forzar:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 35. `services/partes-front/interface_adapters/web/app.py:1607` [logico]

- Original: `settings.default_reviewer or "(sin usuario)",`
- Mutado:   `settings.default_reviewer and "(sin usuario)",`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 36. `services/partes-front/interface_adapters/web/app.py:1646` [booleano]

- Original: `{"ok": False,`
- Mutado:   `{"ok": True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 37. `services/partes-persistencia/application/services/jornada_resolver.py:25` [logico]

- Original: `if candef is None or candef == "":`
- Mutado:   `if candef is None and candef == "":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 38. `services/partes-persistencia/application/services/recurso_conciliador.py:409` [entero]

- Original: `return 0`
- Mutado:   `return 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 39. `services/partes-persistencia/application/services/recurso_conciliador.py:416` [entero]

- Original: `return 0`
- Mutado:   `return 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 40. `services/partes-persistencia/application/services/recurso_conciliador.py:419` [entero]

- Original: `"para revision (%s).", len(docs), ", ".join(docs[:10]),`
- Mutado:   `"para revision (%s).", len(docs), ", ".join(docs[:11]),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 41. `services/partes-persistencia/application/services/recurso_conciliador.py:428` [entero]

- Original: `return 0`
- Mutado:   `return 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 42. `services/partes-persistencia/config/settings.py:125` [entero]

- Original: `sesame_cache_ttl_s: int = Field(21600, alias="SESAME_CACHE_TTL_S")`
- Mutado:   `sesame_cache_ttl_s: int = Field(21601, alias="SESAME_CACHE_TTL_S")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 43. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:60` [entero]

- Original: `ttl_seconds: int = 21600,`
- Mutado:   `ttl_seconds: int = 21601,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 44. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:71` [booleano]

- Original: `self._degradado = False`
- Mutado:   `self._degradado = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 45. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:86` [entero]

- Original: `d = _dt.date.fromisoformat(str(fecha_iso)[:10])`
- Mutado:   `d = _dt.date.fromisoformat(str(fecha_iso)[:11])`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 46. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:104` [booleano]

- Original: `festivos, degradado = None, True`
- Mutado:   `festivos, degradado = None, False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 47. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:163` [logico]

- Original: `_LOG_PREFIX, dni_norm or "(sin dni)", ano,`
- Mutado:   `_LOG_PREFIX, dni_norm and "(sin dni)", ano,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 48. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:171` [logico]

- Original: `_LOG_PREFIX, dni_norm or "(sin dni)", ano, len(mapa),`
- Mutado:   `_LOG_PREFIX, dni_norm and "(sin dni)", ano, len(mapa),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 49. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:190` [logico]

- Original: `"revision.", _LOG_PREFIX, exc, dni_norm or "(sin dni)", ano,`
- Mutado:   `"revision.", _LOG_PREFIX, exc, dni_norm and "(sin dni)", ano,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 50. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:196` [logico]

- Original: `"revision.", _LOG_PREFIX, exc, dni_norm or "(sin dni)", ano,`
- Mutado:   `"revision.", _LOG_PREFIX, exc, dni_norm and "(sin dni)", ano,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 51. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:201` [comparacion]

- Original: `if self._ttl <= 0:`
- Mutado:   `if self._ttl < 0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 52. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:201` [entero]

- Original: `if self._ttl <= 0:`
- Mutado:   `if self._ttl <= 1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 53. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:205` [aritmetico]

- Original: `if entrada is None or (self._reloj() - entrada[0]) >= self._ttl:`
- Mutado:   `if entrada is None or (self._reloj() + entrada[0]) >= self._ttl:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 54. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:205` [comparacion]

- Original: `if entrada is None or (self._reloj() - entrada[0]) >= self._ttl:`
- Mutado:   `if entrada is None or (self._reloj() - entrada[0]) > self._ttl:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 55. `services/partes-persistencia/infrastructure/sesame/sesame_api_client.py:50` [entero]

- Original: `_MAX_CUERPO = 300`
- Mutado:   `_MAX_CUERPO = 301`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 56. `services/partes-persistencia/infrastructure/sesame/sesame_api_client.py:60` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 57. `services/partes-persistencia/interface_adapters/api/app.py:77` [logico]

- Original: `settings.sesame_api_base_url, len(settings.sesame_api_key or ""),`
- Mutado:   `settings.sesame_api_base_url, len(settings.sesame_api_key and ""),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

