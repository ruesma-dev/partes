<!-- progress/mutacion_F-003.md -->
# F-003 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-003` el 2026-08-15 22:41.

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
| Supervivientes | 10 |
| Timeouts | 16 |
| Tiempo total | 669.5 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/calendario_provider.py:230` [logico]

- Original: `_LOG_PREFIX, dni_norm or "(sin dni)", ano, len(mapa), fuente,`
- Mutado:   `_LOG_PREFIX, dni_norm and "(sin dni)", ano, len(mapa), fuente,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-front/application/services/calendario_provider.py:249` [logico]

- Original: `_LOG_PREFIX, exc, dni_norm or "(sin dni)", ano,`
- Mutado:   `_LOG_PREFIX, exc, dni_norm and "(sin dni)", ano,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/partes-front/application/services/calendario_provider.py:255` [logico]

- Original: `_LOG_PREFIX, exc, dni_norm or "(sin dni)", ano,`
- Mutado:   `_LOG_PREFIX, exc, dni_norm and "(sin dni)", ano,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/partes-front/application/services/calendario_provider.py:263` [comparacion]

- Original: `if self._ttl <= 0:`
- Mutado:   `if self._ttl < 0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/partes-front/application/services/jornada_resolver.py:32` [logico]

- Original: `if candef is None or candef == "":`
- Mutado:   `if candef is None and candef == "":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/partes-front/infrastructure/database/parte_repository.py:1388` [entero]

- Original: `reg.sigrid_motivo = (motivo_ok or None) and motivo_ok[:255]`
- Mutado:   `reg.sigrid_motivo = (motivo_ok or None) and motivo_ok[:256]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/partes-front/infrastructure/database/parte_repository.py:1407` [entero]

- Original: `reg.sigrid_motivo = (motivo_ok or None) and motivo_ok[:255]`
- Mutado:   `reg.sigrid_motivo = (motivo_ok or None) and motivo_ok[:256]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/partes-front/infrastructure/sesame/sesame_api_client.py:46` [entero]

- Original: `_MAX_CUERPO = 300`
- Mutado:   `_MAX_CUERPO = 301`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/partes-front/infrastructure/sesame/sesame_api_client.py:153` [entero]

- Original: `transport = self._transport or httpx.HTTPTransport(retries=1)`
- Mutado:   `transport = self._transport or httpx.HTTPTransport(retries=2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/partes-front/interface_adapters/web/app.py:1085` [booleano]

- Original: `@app.get("/api/calendario", include_in_schema=False)`
- Mutado:   `@app.get("/api/calendario", include_in_schema=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

## Timeouts

- `services/partes-front/application/services/calendario_provider.py:61` services/partes-front/application/services/calendario_provider.py:61 [booleano] @dataclass(frozen=True) -> @dataclass(frozen=False)
- `services/partes-front/application/services/calendario_provider.py:70` services/partes-front/application/services/calendario_provider.py:70 [booleano] fiable: bool = True -> fiable: bool = False
- `services/partes-front/application/services/calendario_provider.py:84` services/partes-front/application/services/calendario_provider.py:84 [entero] ttl_seconds: int = 21600, -> ttl_seconds: int = 21601,
- `services/partes-front/application/services/calendario_provider.py:117` services/partes-front/application/services/calendario_provider.py:117 [comparacion] fin_de_semana = d.weekday() >= 5 -> fin_de_semana = d.weekday() > 5
- `services/partes-front/application/services/calendario_provider.py:117` services/partes-front/application/services/calendario_provider.py:117 [entero] fin_de_semana = d.weekday() >= 5 -> fin_de_semana = d.weekday() >= 6
- `services/partes-front/application/services/calendario_provider.py:121` services/partes-front/application/services/calendario_provider.py:121 [logico] laborable=not (fin_de_semana or festivo), -> laborable=not (fin_de_semana and festivo),
- `services/partes-front/application/services/calendario_provider.py:136` services/partes-front/application/services/calendario_provider.py:136 [logico] if self._cliente is None or not dni_norm: -> if self._cliente is None and not dni_norm:
- `services/partes-front/application/services/calendario_provider.py:136` services/partes-front/application/services/calendario_provider.py:136 [not] if self._cliente is None or not dni_norm: -> if self._cliente is None or dni_norm:
- `services/partes-front/application/services/calendario_provider.py:141` services/partes-front/application/services/calendario_provider.py:141 [entero] return vigente[0]  # type: ignore[return-value] -> return vigente[1]  # type: ignore[return-value]
- `services/partes-front/application/services/calendario_provider.py:170` services/partes-front/application/services/calendario_provider.py:170 [entero] if self._resolver(clave[0], clave[1])[1] not in FUENTES_FIABLES: -> if self._resolver(clave[1], clave[1])[1] not in FUENTES_FIABLES:
- `services/partes-front/application/services/calendario_provider.py:170` services/partes-front/application/services/calendario_provider.py:170 [entero] if self._resolver(clave[0], clave[1])[1] not in FUENTES_FIABLES: -> if self._resolver(clave[0], clave[2])[1] not in FUENTES_FIABLES:
- `services/partes-front/application/services/calendario_provider.py:170` services/partes-front/application/services/calendario_provider.py:170 [entero] if self._resolver(clave[0], clave[1])[1] not in FUENTES_FIABLES: -> if self._resolver(clave[0], clave[1])[2] not in FUENTES_FIABLES:
- `services/partes-front/application/services/calendario_provider.py:186` services/partes-front/application/services/calendario_provider.py:186 [logico] return (valor or FESTIVO_SIN_NOMBRE), fuente   # type: ignore[return-value] -> return (valor and FESTIVO_SIN_NOMBRE), fuente   # type: ignore[return-value]
- `services/partes-front/application/services/calendario_provider.py:222` services/partes-front/application/services/calendario_provider.py:222 [logico] _LOG_PREFIX, dni_norm or "(sin dni)", ano, -> _LOG_PREFIX, dni_norm and "(sin dni)", ano,
- `services/partes-front/application/services/calendario_provider.py:251` services/partes-front/application/services/calendario_provider.py:251 [entero] return entrada[1], "stale"      # type: ignore[return-value] -> return entrada[2], "stale"      # type: ignore[return-value]
- `services/partes-front/application/services/calendario_provider.py:269` services/partes-front/application/services/calendario_provider.py:269 [entero] if (self._reloj() - entrada[0]) >= self._ttl: -> if (self._reloj() - entrada[1]) >= self._ttl:

