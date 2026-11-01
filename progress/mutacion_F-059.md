<!-- progress/mutacion_F-059.md -->
# F-059 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-059` el 2026-10-23 17:49.

## Alcance

Origen del diff: **rama** (`2170f821ad98efd950ae5df8d6bcc4d0d8f0c3ae` .. `feature/F-059-pagina-como-imagen-derecha`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-api/application/pipelines/extract_parte_pipeline.py` | 95 |
| `services/partes-api/config/settings.py` | 34 |
| `services/partes-api/domain/models/conversion_adjunto.py` | 42 |
| `services/partes-api/domain/ports/conversor_pagina.py` | 16 |
| `services/partes-api/infrastructure/document/pagina_pdf_imagen.py` | 149 |
| `services/partes-api/infrastructure/llm/openai_responses_client.py` | 11 |
| `services/partes-api/interface_adapters/api/app.py` | 19 |
| **Total** | **366** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 49 |
| Mutantes evaluados | 20 |
| Muertos | 17 |
| Supervivientes | 3 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 42.2 s |
| SHA de HEAD medido | `319d9514eaa959f3bd0f46a5547212f3cd340cb6` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-059_k5kwj0eo/wk_0/services/partes-api` | 6.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-059_k5kwj0eo/wk_1/services/partes-api` | 6.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-059_k5kwj0eo/wk_2/services/partes-api` | 6.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-059_k5kwj0eo/wk_3/services/partes-api` | 6.3 |
| Media por mutante evaluado (s) | 2.1 |
| Timeout efectivo por mutante (s) | 300 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 300 |
| Workers | 4 |
| Muestreo | sí — 20 de 49 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-api/infrastructure/document/pagina_pdf_imagen.py:146` [comparacion]

- Original: `if any(abs(real - esperado) > TOLERANCIA_PT for real, esperado in ajustes):`
- Mutado:   `if any(abs(real - esperado) >= TOLERANCIA_PT for real, esperado in ajustes):`

#### Análisis (implementer, 2026-10-23)

> Por qué ningún test lo caza: los casos «dentro de tolerancia» se quedaban en 0,9 pt
> (`300.9 0 0 199.1 0.9 -0.9`) y los de fuera en 2 pt; nadie probaba el borde. El borde es
> alcanzable y exacto en float: con valores enteros (`301` frente a una MediaBox de `300`)
> `abs(301.0 - 300.0)` es `1.0` exacto. R9 dice «tolerancia 1 pt»: el borde es dentro.
> Decisión: **hueco real, test nuevo.** Dos casos en
> `test_f059_r9_dentro_de_las_tolerancias_si_aplica`: `tolerancia-1pt-exacta-ancho`
> (`301 0 0 200 0 0 cm`) y `tolerancia-1pt-exacta-alto-y-origen` (`300 0 0 199 -1 1 cm`).
> Con el mutante aplicado a mano: `2 failed, 5 passed`; sin él, `7 passed`.

### 2. `services/partes-api/infrastructure/document/pagina_pdf_imagen.py:149` [comparacion]

- Original: `return abs(proporcion_px / (a / d) - 1) <= TOLERANCIA_PROPORCION`
- Mutado:   `return abs(proporcion_px / (a / d) - 1) < TOLERANCIA_PROPORCION`

#### Análisis (implementer, 2026-10-23)

> Por qué ningún test lo caza: la igualdad `abs(q - 1) == 0.02` es **inalcanzable** en
> coma flotante, así que `<=` y `<` dan lo mismo para cualquier entrada.
> Demostración: (1) si `q` (el cociente ya redondeado) está en [0,5, 2], `q - 1` es exacta
> (lema de Sterbenz) y vale un múltiplo de 2^-53 (q en [0,5, 1)) o de 2^-52 (q en [1, 2]);
> (2) el double `0.02` es `5764607523034235 / 2^58`, numerador impar: su bit más bajo es
> 2^-58, no es múltiplo de 2^-53; (3) fuera de [0,5, 2], `abs(q - 1) >= 0.5`, lejos del 0,02.
> Ejemplo: los doubles vecinos de 1,02 dan `0.019999999999999796`, `0.020000000000000018` y
> `0.02000000000000024`; los de 0,98, `0.02000000000000013`, `0.020000000000000018` y
> `0.019999999999999907`. Ninguno es `0.02` (script en el scratchpad de la sesión,
> `frontera_002.py`; `as_integer_ratio()` y `Fraction` lo confirman).
> Decisión: **mutante equivalente.** Sin test: no hay entrada que lo distinga. Los dos lados
> del 2 % ya los fijan `proporcion-1.96pc`/`proporcion-1.7pc-ancha` (dentro) y
> `proporcion-2.4pc` (fuera).

### 3. `services/partes-api/interface_adapters/api/app.py:144` [logico]

- Original: `sorted(proveedores_imagen) or "(ninguno)",`
- Mutado:   `sorted(proveedores_imagen) and "(ninguno)",`

#### Análisis (implementer, 2026-10-23)

> Por qué ningún test lo caza: solo cambia el texto del INFO de wiring y ningún test lo
> leía. No es cosmético: es la constancia en Log Analytics de qué lista quedó activa tras
> desplegar o tras apagar `PAGINA_COMO_IMAGEN` (DA3, T10). Con el mutante, encendido diría
> `proveedores=(ninguno)` y apagado `proveedores=[]`: justo al revés de lo que se busca.
> Decisión: **hueco real, test nuevo.** En `test_f059_config.py`, con `caplog`:
> `test_f059_r20_el_log_de_wiring_nombra_los_proveedores` (`proveedores=['openai']`) y
> `test_f059_r20_el_log_de_wiring_apagado_dice_ninguno` (`proveedores=(ninguno)`). Con el
> mutante aplicado a mano: `2 failed`; sin él, en verde.

