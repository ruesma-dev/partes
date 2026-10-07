<!-- progress/mutacion_F-033.md -->
# F-033 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-033` el 2026-10-07 13:47.

## Alcance

Origen del diff: **rama** (`e54908ac84c6fd191d16dc3720bd1d8c076b8c5f` .. `feature/F-033-columna-empresa`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/empresas.py` | 52 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 31 |
| **Total** | **83** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 12 |
| Mutantes evaluados | 12 |
| Muertos | 10 |
| Supervivientes | 2 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1295.7 s |
| SHA de HEAD medido | `ea0ba9e5b69744f3730e5eea935f49426646e204` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-033_m9tub34p/wk_0/services/partes-front` | 304.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-033_m9tub34p/wk_1/services/partes-front` | 305.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-033_m9tub34p/wk_2/services/partes-front` | 302.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-033_m9tub34p/wk_3/services/partes-front` | 302.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-033_m9tub34p/wk_4/services/partes-front` | 302.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-033_m9tub34p/wk_5/services/partes-front` | 303.0 |
| Media por mutante evaluado (s) | 108.0 |
| Timeout efectivo por mutante (s) | 600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 600 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/infrastructure/database/parte_repository.py:1028` [entero]

- Original: `r.empresas[0] if r.empresas else 10**9,`
- Mutado:   `r.empresas[0] if r.empresas else 11**9,`

#### Análisis

> Por qué ningún test lo caza: `10**9` es solo un centinela «mayor que
> cualquier número de empresa» para mandar detrás las gemelas sin empresa
> (R7). `11**9` (2 357 947 691) sigue siendo mayor que cualquier número de
> empresa de Sigrid (hoy 1 y 28; el campo es un entero pequeño), así que el
> orden resultante es idéntico para toda entrada posible.
> Decisión: **mutante equivalente**. `test_f033_r7_orden_gemelas` sí caza
> la mutación que importa (el índice `[0]`→`[1]` y el `or`→`and`, ambos
> muertos). Sin test nuevo.

### 2. `services/partes-front/infrastructure/database/parte_repository.py:1028` [entero]

- Original: `r.empresas[0] if r.empresas else 10**9,`
- Mutado:   `r.empresas[0] if r.empresas else 10**10,`

#### Análisis

> Por qué ningún test lo caza: `10**9` es solo un centinela «mayor que
> cualquier número de empresa» para mandar detrás las gemelas sin empresa
> (R7). `10**10` sigue siendo mayor que cualquier número de
> empresa de Sigrid (hoy 1 y 28; el campo es un entero pequeño), así que el
> orden resultante es idéntico para toda entrada posible.
> Decisión: **mutante equivalente**. `test_f033_r7_orden_gemelas` sí caza
> la mutación que importa (el índice `[0]`→`[1]` y el `or`→`and`, ambos
> muertos). Sin test nuevo.

