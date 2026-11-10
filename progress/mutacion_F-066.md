<!-- progress/mutacion_F-066.md -->
# F-066 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-066` el 2026-11-06 16:57.

## Alcance

Origen del diff: **rama** (`0d8fc14732e497743b04fc93ab46410301ea5b88` .. `feature/F-066-selector-hora-por-prefijo-he`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/clase_hora.py` | 78 |
| `services/partes-front/application/services/franquicia.py` | 7 |
| `services/partes-front/application/services/sincronizacion.py` | 8 |
| `services/partes-front/application/services/tipo_hora_catalog.py` | 5 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 7 |
| `services/partes-front/infrastructure/sigrid/sigrid_lookup_client.py` | 24 |
| `services/partes-front/interface_adapters/web/app.py` | 9 |
| **Total** | **138** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 21 |
| Mutantes evaluados | 21 |
| Muertos | 18 |
| Supervivientes | 3 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 10220.6 s |
| SHA de HEAD medido | `2bc2ef0e8481f17523ef91e4c41bc9d65df0b653` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-066_8g00ij04/wk_0/services/partes-front` | 2714.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-066_8g00ij04/wk_1/services/partes-front` | 2734.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-066_8g00ij04/wk_2/services/partes-front` | 2779.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-066_8g00ij04/wk_3/services/partes-front` | 2710.5 |
| Media por mutante evaluado (s) | 486.7 |
| Timeout efectivo por mutante (s) | 5558 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 600 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/infrastructure/sigrid/sigrid_lookup_client.py:238` [entero]

- Original: `omitidos = 0`
- Mutado:   `omitidos = 1`

#### Análisis (implementer, 2026-11-06)

> Por qué ningún test lo caza: `omitidos` solo alimenta el log `tipos_hora -> N filas (M
> excluidas)` y ningún test leía ese log. Hueco real, no equivalente.
> Decisión: test nuevo `test_f066_r7_log_cuenta_excluidas` (`caplog`, 0, 1 y 2 excluidas);
> mutante aplicado a mano ⇒ el test falla (traza en `progress/impl_F-066.md`).

### 2. `services/partes-front/infrastructure/sigrid/sigrid_lookup_client.py:247` [aritmetico]

- Original: `omitidos += 1`
- Mutado:   `omitidos -= 1`

#### Análisis (implementer, 2026-11-06)

> Por qué ningún test lo caza: `omitidos` solo alimenta el log `tipos_hora -> N filas (M
> excluidas)` y ningún test leía ese log. Hueco real, no equivalente.
> Decisión: test nuevo `test_f066_r7_log_cuenta_excluidas` (`caplog`, 0, 1 y 2 excluidas);
> mutante aplicado a mano ⇒ el test falla (traza en `progress/impl_F-066.md`).

### 3. `services/partes-front/infrastructure/sigrid/sigrid_lookup_client.py:247` [entero]

- Original: `omitidos += 1`
- Mutado:   `omitidos += 2`

#### Análisis (implementer, 2026-11-06)

> Por qué ningún test lo caza: `omitidos` solo alimenta el log `tipos_hora -> N filas (M
> excluidas)` y ningún test leía ese log. Hueco real, no equivalente.
> Decisión: test nuevo `test_f066_r7_log_cuenta_excluidas` (`caplog`, 0, 1 y 2 excluidas);
> mutante aplicado a mano ⇒ el test falla (traza en `progress/impl_F-066.md`).

