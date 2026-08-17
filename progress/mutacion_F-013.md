<!-- progress/mutacion_F-013.md -->
# F-013 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-013` el 2026-08-17 22:24.

## Alcance

Origen del diff: **rama** (`da7293da005993dee235011b5ac2197b929d6a6d` .. `feature/F-013-informe-validacion-sesame`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/validar_datos_sesame.py` | 573 |
| **Total** | **573** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 74 |
| Mutantes evaluados | 74 |
| Muertos | 52 |
| Supervivientes | 22 |
| Timeouts | 0 |
| Tiempo total | 403.0 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/validar_datos_sesame.py:91` [entero]

- Original: `_MAX_CUERPO = 300`
- Mutado:   `_MAX_CUERPO = 301`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-front/validar_datos_sesame.py:97` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/partes-front/validar_datos_sesame.py:111` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/partes-front/validar_datos_sesame.py:122` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/partes-front/validar_datos_sesame.py:156` [logico]

- Original: `if valor is not None and str(valor).strip():`
- Mutado:   `if valor is not None or str(valor).strip():`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/partes-front/validar_datos_sesame.py:178` [logico]

- Original: `estado = str(empleado.get("estado") or DESCONOCIDO)`
- Mutado:   `estado = str(empleado.get("estado") and DESCONOCIDO)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/partes-front/validar_datos_sesame.py:184` [booleano]

- Original: `festivos_ok=False, jornada=None,`
- Mutado:   `festivos_ok=True, jornada=None,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/partes-front/validar_datos_sesame.py:334` [not]

- Original: `if not dist:`
- Mutado:   `if dist:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/partes-front/validar_datos_sesame.py:339` [comparacion]

- Original: `f"{'es' if cuantos != 1 else ''}")`
- Mutado:   `f"{'es' if cuantos == 1 else ''}")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/partes-front/validar_datos_sesame.py:339` [entero]

- Original: `f"{'es' if cuantos != 1 else ''}")`
- Mutado:   `f"{'es' if cuantos != 2 else ''}")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/partes-front/validar_datos_sesame.py:374` [entero]

- Original: `transporte = transport or httpx.HTTPTransport(retries=1)`
- Mutado:   `transporte = transport or httpx.HTTPTransport(retries=2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/partes-front/validar_datos_sesame.py:383` [logico]

- Original: `texto = (respuesta.text or "")[:_MAX_CUERPO]`
- Mutado:   `texto = (respuesta.text and "")[:_MAX_CUERPO]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/partes-front/validar_datos_sesame.py:384` [comparacion]

- Original: `if respuesta.status_code >= 400:`
- Mutado:   `if respuesta.status_code > 400:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/partes-front/validar_datos_sesame.py:384` [entero]

- Original: `if respuesta.status_code >= 400:`
- Mutado:   `if respuesta.status_code >= 401:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/partes-front/validar_datos_sesame.py:395` [booleano]

- Original: `if not isinstance(cuerpo, dict) or not cuerpo.get("ok", False):`
- Mutado:   `if not isinstance(cuerpo, dict) or not cuerpo.get("ok", True):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/partes-front/validar_datos_sesame.py:428` [booleano]

- Original: `salida.mkdir(parents=True, exist_ok=True)`
- Mutado:   `salida.mkdir(parents=False, exist_ok=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/partes-front/validar_datos_sesame.py:445` [logico]

- Original: `if not linea or linea.startswith("#") or "=" not in linea:`
- Mutado:   `if not linea and linea.startswith("#") or "=" not in linea:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/partes-front/validar_datos_sesame.py:447` [entero]

- Original: `clave, valor = linea.split("=", 1)`
- Mutado:   `clave, valor = linea.split("=", 2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `services/partes-front/validar_datos_sesame.py:490` [logico]

- Original: `or os.environ.get("SESAME_API_BASE_URL")`
- Mutado:   `and os.environ.get("SESAME_API_BASE_URL")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `services/partes-front/validar_datos_sesame.py:521` [entero]

- Original: `return 2`
- Mutado:   `return 3`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `services/partes-front/validar_datos_sesame.py:528` [entero]

- Original: `return 2`
- Mutado:   `return 3`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `services/partes-front/validar_datos_sesame.py:542` [entero]

- Original: `return 1`
- Mutado:   `return 2`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

