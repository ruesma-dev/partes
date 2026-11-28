<!-- progress/mutacion_F-085.md -->
# F-085 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-085 --workers 3` el 2026-11-28 05:43.

## Alcance

Origen del diff: **rama** (`b5e935b52a5a679612c5b210093127daeb8e0946` .. `feature/F-085-codigo-de-incidencia-convierte-la-linea`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/partes-front/application/services/clase_hora.py` | 26 | 5 |
| `services/partes-front/application/services/conversion_clase.py` | 110 | 28 |
| `services/partes-front/application/services/racha_incidencia.py` | 26 | 11 |
| `services/partes-front/config/settings.py` | 7 | 1 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 119 | 24 |
| `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` | 4 | 0 — sin mutantes |
| `services/partes-front/interface_adapters/web/app.py` | 43 | 13 |
| `services/partes-persistencia/application/services/recurso_conciliador.py` | 35 | 11 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 8 | 0 — sin mutantes |
| `services/partes-transfer/application/pipelines/registro_pipeline.py` | 79 | 37 |
| `services/partes-transfer/application/services/racha_ciz.py` | 95 | 28 |
| `services/partes-transfer/application/services/reglas_registro.py` | 24 | 12 |
| `services/partes-transfer/config/settings.py` | 6 | 1 |
| `services/partes-transfer/domain/models/registro_models.py` | 13 | 1 |
| **Total** | **595** | **172** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 172 |
| Mutantes evaluados | 100 |
| Muertos | 91 |
| Supervivientes | 9 (todos medidos: sin mapa no se poda) |
| Timeouts | 0 |
| Indeterminados | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 14416.3 s |
| SHA de HEAD medido | `7bf0a638c5b40c82460d6309855aab8bee69e4bf` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-085__fzraboi/wk_0/services/partes-front` | 854.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-085__fzraboi/wk_0/services/partes-persistencia` | 56.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-085__fzraboi/wk_0/services/partes-transfer` | 43.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-085__fzraboi/wk_1/services/partes-front` | 856.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-085__fzraboi/wk_1/services/partes-persistencia` | 55.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-085__fzraboi/wk_1/services/partes-transfer` | 43.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-085__fzraboi/wk_2/services/partes-front` | 854.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-085__fzraboi/wk_2/services/partes-persistencia` | 57.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-085__fzraboi/wk_2/services/partes-transfer` | 43.3 |
| Media por mutante evaluado (s) | 144.2 |
| Timeout efectivo por mutante (s) | 1713 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 600 |
| Workers | 3 |
| Un mutante por línea | sí — 172 generados → 110 candidatos, uno por línea |
| Muestreo | sí — 100 de 110 candidatos, semilla `20261030`, nivel `critico`; tope: 60 % de 110 candidatos, acotado a [100, 300] |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 366.9 (100 mutantes) |

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/conversion_clase.py:78` [veracidad]

- Original: `return clase.letra if clase is not None else None`
- Mutado:   `return clase.letra if clase else None`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-front/application/services/conversion_clase.py:89` [veracidad]

- Original: `if error is not None:`
- Mutado:   `if error:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/partes-front/infrastructure/database/parte_repository.py:748` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/partes-front/infrastructure/database/parte_repository.py:2644` [booleano]

- Original: `mover_inicio: bool = False,`
- Mutado:   `mover_inicio: bool = True,`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/partes-front/infrastructure/database/parte_repository.py:3388` [veracidad]

- Original: `if clase.error is not None:`
- Mutado:   `if clase.error:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/partes-front/infrastructure/database/parte_repository.py:3410` [negacion]

- Original: `elif clase.es_incidencia:`
- Mutado:   `elif not clase.es_incidencia:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/partes-transfer/application/services/racha_ciz.py:106` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/partes-transfer/application/services/racha_ciz.py:324` [veracidad]

- Original: `if previo is None:`
- Mutado:   `if not previo:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/partes-transfer/application/services/racha_ciz.py:327` [veracidad]

- Original: `cod = parte.cod if parte is not None else None`
- Mutado:   `cod = parte.cod if parte else None`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

## No muertos: código de salida

| Fichero:línea | Operador | Veredicto | Código |
|---|---|---|---|
| `services/partes-front/application/services/conversion_clase.py:78` | veracidad | superviviente | 0 |
| `services/partes-front/application/services/conversion_clase.py:89` | veracidad | superviviente | 0 |
| `services/partes-front/infrastructure/database/parte_repository.py:748` | booleano | superviviente | 0 |
| `services/partes-front/infrastructure/database/parte_repository.py:2644` | booleano | superviviente | 0 |
| `services/partes-front/infrastructure/database/parte_repository.py:3388` | veracidad | superviviente | 0 |
| `services/partes-front/infrastructure/database/parte_repository.py:3410` | negacion | superviviente | 0 |
| `services/partes-transfer/application/services/racha_ciz.py:106` | booleano | superviviente | 0 |
| `services/partes-transfer/application/services/racha_ciz.py:324` | veracidad | superviviente | 0 |
| `services/partes-transfer/application/services/racha_ciz.py:327` | veracidad | superviviente | 0 |

## Ficheros sin mutantes

Cada uno tiene líneas en alcance y el generador no ha sacado de ellas ni un mutante: la campaña no las ha juzgado. Declara por qué no hay nada que mutar (solo declaraciones, cadenas, imports) o qué test de la fase RED cubre el cambio. El reviewer hace la prueba de control (`generar_mutantes` sin exclusión de alcance) y ninguna declaración puede quedarse en `PENDIENTE` al cerrar la feature.

### `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` — 4 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` — 8 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

