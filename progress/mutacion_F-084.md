<!-- progress/mutacion_F-084.md -->
# F-084 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-084 --workers 3` el 2026-11-27 09:00.

## Alcance

Origen del diff: **rama** (`d11d228b2194b520e5249a55c6b3b91b555e3190` .. `feature/F-084-partes-con-problemas`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/partes-front/application/services/partes_con_problemas.py` | 289 | 75 |
| `services/partes-front/infrastructure/database/orm_models.py` | 6 | 2 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 217 | 83 |
| `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` | 3 | 0 — sin mutantes |
| `services/partes-front/interface_adapters/web/app.py` | 101 | 32 |
| `services/partes-front/interface_adapters/web/identidad.py` | 7 | 0 — sin mutantes |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | 6 | 2 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 17 | 4 |
| **Total** | **646** | **198** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 198 |
| Mutantes evaluados | 27 (+ 73 veredictos reutilizados) |
| Muertos | 93 |
| Supervivientes | 7 (todos medidos: sin mapa no se poda) |
| Timeouts | 0 |
| Indeterminados | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 7109.1 s |
| SHA de HEAD medido | `6ef7b5e4cd4c70359134a8cbc9a80e2d36d748aa` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-084_ntx2erad/wk_0/services/partes-front` | 624.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-084_ntx2erad/wk_1/services/partes-front` | 623.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-084_ntx2erad/wk_2/services/partes-front` | 643.8 |
| Media por mutante evaluado (s) | 263.3 |
| Timeout efectivo por mutante (s) | 1288 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 600 |
| Workers | 3 |
| Un mutante por línea | sí — 198 generados → 131 candidatos, uno por línea |
| Muestreo | sí — 100 de 131 candidatos, semilla `20261030`, nivel `critico`; tope: 60 % de 131 candidatos, acotado a [100, 300] |
| Modo | incremental desde `8474ce964ec3f257d5e304c9a617e1942f1675c4` — 73 reutilizados, 18 reevaluados, 9 de control |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 627.8 (27 mutantes) |

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/partes_con_problemas.py:144` [veracidad]

- Original: `return fecha_int is not None and fecha_int > 0`
- Mutado:   `return fecha_int and fecha_int > 0`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-front/application/services/partes_con_problemas.py:174` [veracidad]

- Original: `if recibido is None:`
- Mutado:   `if not recibido:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/partes-front/application/services/partes_con_problemas.py:244` [veracidad]

- Original: `if sustituto is None:`
- Mutado:   `if not sustituto:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/partes-front/infrastructure/database/parte_repository.py:4910` [veracidad]

- Original: `if motivo is None:`
- Mutado:   `if not motivo:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/partes-front/infrastructure/database/parte_repository.py:5035` [veracidad]

- Original: `if motivo is not None:`
- Mutado:   `if motivo:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/partes-front/interface_adapters/web/app.py:2284` [veracidad]

- Original: `if parsed is None:`
- Mutado:   `if not parsed:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/partes-front/interface_adapters/web/app.py:2300` [veracidad]

- Original: `if res is None:`
- Mutado:   `if not res:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

## No muertos: código de salida

| Fichero:línea | Operador | Veredicto | Código |
|---|---|---|---|
| `services/partes-front/application/services/partes_con_problemas.py:144` | veracidad | superviviente | 0 |
| `services/partes-front/application/services/partes_con_problemas.py:174` | veracidad | superviviente | 0 |
| `services/partes-front/application/services/partes_con_problemas.py:244` | veracidad | superviviente | 0 |
| `services/partes-front/infrastructure/database/parte_repository.py:4910` | veracidad | superviviente | 0 |
| `services/partes-front/infrastructure/database/parte_repository.py:5035` | veracidad | superviviente | 0 |
| `services/partes-front/interface_adapters/web/app.py:2284` | veracidad | superviviente | 0 |
| `services/partes-front/interface_adapters/web/app.py:2300` | veracidad | superviviente | 0 |

## Ficheros sin mutantes

Cada uno tiene líneas en alcance y el generador no ha sacado de ellas ni un mutante: la campaña no las ha juzgado. Declara por qué no hay nada que mutar (solo declaraciones, cadenas, imports) o qué test de la fase RED cubre el cambio. El reviewer hace la prueba de control (`generar_mutantes` sin exclusión de alcance) y ninguna declaración puede quedarse en `PENDIENTE` al cerrar la feature.

### `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` — 3 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/partes-front/interface_adapters/web/identidad.py` — 7 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

