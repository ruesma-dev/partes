<!-- progress/mutacion_F-077.md -->
# F-077 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-077 --workers 3` el 2026-11-19 13:18.

## Alcance

Origen del diff: **rama** (`9925fa12022a54c080f0609aaf0748b3c8b44a63` .. `feature/F-077-sesame-directo-sin-pasarela`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/partes-front/application/services/calendario_provider.py` | 14 | 3 |
| `services/partes-front/config/logging_config.py` | 2 | 0 — sin mutantes |
| `services/partes-front/config/settings.py` | 15 | 1 |
| `services/partes-front/interface_adapters/web/app.py` | 13 | 0 — sin mutantes |
| `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py` | 1 | 0 — sin mutantes |
| `services/partes-persistencia/application/services/refresco_festivos.py` | 3 | 0 — sin mutantes |
| `services/partes-persistencia/config/logging_config.py` | 3 | 0 — sin mutantes |
| `services/partes-persistencia/config/settings.py` | 24 | 9 |
| `services/partes-persistencia/contrastar_festivos_sesame.py` | 51 | 11 |
| `services/partes-persistencia/infrastructure/calendario/tabla_calendario_laboral.py` | 1 | 0 — sin mutantes |
| `services/partes-persistencia/infrastructure/sesame/festivos_sesame_hr.py` | 131 | 31 |
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py` | 284 | 85 |
| `services/partes-persistencia/interface_adapters/api/app.py` | 23 | 1 |
| **Total** | **565** | **141** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 141 |
| Mutantes evaluados | 85 |
| Muertos | 73 |
| Supervivientes | 12 (todos medidos: sin mapa no se poda) |
| Timeouts | 0 |
| Indeterminados | 0 |
| Timeouts repasados en serie | 1 — 1 con veredicto tras el repaso, 0 en timeout todavía |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 7791.3 s |
| SHA de HEAD medido | `11d32fc3ce0071bbac53be70ea35cd8b924c9af7` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-077_tu009n26/wk_0/services/partes-front` | 840.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-077_tu009n26/wk_0/services/partes-persistencia` | 51.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-077_tu009n26/wk_1/services/partes-front` | 848.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-077_tu009n26/wk_1/services/partes-persistencia` | 51.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-077_tu009n26/wk_2/services/partes-front` | 839.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-077_tu009n26/wk_2/services/partes-persistencia` | 53.4 |
| Media por mutante evaluado (s) | 91.7 |
| Timeout efectivo por mutante (s) | 1697 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 600 |
| Workers | 3 |
| Un mutante por línea | sí — 141 generados → 85 candidatos, uno por línea |
| Muestreo | no: campaña completa (85 candidatos ≤ tope 100 del nivel `critico`) |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 66.7 (86 mutantes) |

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-persistencia/config/settings.py:181` [entero]

- Original: `sesame_timeout_s: float = Field(10.0, alias="SESAME_TIMEOUT_S", gt=0)`
- Mutado:   `sesame_timeout_s: float = Field(10.0, alias="SESAME_TIMEOUT_S", gt=1)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-persistencia/infrastructure/sesame/festivos_sesame_hr.py:75` [veracidad]

- Original: `if empleado is None:`
- Mutado:   `if not empleado:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/partes-persistencia/infrastructure/sesame/festivos_sesame_hr.py:86` [veracidad]

- Original: `if (self._corte_hasta is not None`
- Mutado:   `if (self._corte_hasta`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/partes-persistencia/infrastructure/sesame/festivos_sesame_hr.py:115` [veracidad]

- Original: `if previo is None:`
- Mutado:   `if not previo:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:57` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:64` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:72` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:90` [entero]

- Original: `tope_filas: int = 20_000,`
- Mutado:   `tope_filas: int = 20001,`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:107` [entero]

- Original: `self.ultimas_paginas = 0`
- Mutado:   `self.ultimas_paginas = 1`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:160` [veracidad]

- Original: `if dias is None:`
- Mutado:   `if not dias:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:182` [veracidad]

- Original: `if cuerpo is None:`
- Mutado:   `if not cuerpo:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:262` [aritmetico]

- Original: `return float(1 + intento)`
- Mutado:   `return float(1 - intento)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

## No muertos: código de salida

| Fichero:línea | Operador | Veredicto | Código |
|---|---|---|---|
| `services/partes-persistencia/config/settings.py:181` | entero | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/festivos_sesame_hr.py:75` | veracidad | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/festivos_sesame_hr.py:86` | veracidad | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/festivos_sesame_hr.py:115` | veracidad | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:57` | booleano | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:64` | booleano | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:72` | booleano | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:90` | entero | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:107` | entero | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:160` | veracidad | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:182` | veracidad | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:262` | aritmetico | superviviente | 0 |

## Ficheros sin mutantes

Cada uno tiene líneas en alcance y el generador no ha sacado de ellas ni un mutante: la campaña no las ha juzgado. Declara por qué no hay nada que mutar (solo declaraciones, cadenas, imports) o qué test de la fase RED cubre el cambio. El reviewer hace la prueba de control (`generar_mutantes` sin exclusión de alcance) y ninguna declaración puede quedarse en `PENDIENTE` al cerrar la feature.

### `services/partes-front/config/logging_config.py` — 2 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/partes-front/interface_adapters/web/app.py` — 13 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py` — 1 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/partes-persistencia/application/services/refresco_festivos.py` — 3 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/partes-persistencia/config/logging_config.py` — 3 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/partes-persistencia/infrastructure/calendario/tabla_calendario_laboral.py` — 1 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

