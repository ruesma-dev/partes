<!-- progress/mutacion_F-025.md -->
# F-025 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-025` el 2026-10-02 10:14.

## Alcance

Origen del diff: **rama** (`07c40bab3b835f85937feaa028344d008ec3ef33` .. `feature/F-025-incidencia-vs-extra`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/incidencias_horas.py` | 234 |
| `services/partes-front/application/services/reparto_obras.py` | 3 |
| `services/partes-front/config/settings.py` | 8 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 155 |
| `services/partes-front/interface_adapters/web/app.py` | 66 |
| **Total** | **466** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 70 |
| Mutantes evaluados | 20 |
| Muertos | 14 |
| Supervivientes | 6 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1861.6 s |
| SHA de HEAD medido | `a8e0b221bfa3cd788adee5684ef488e8542ad9d9` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-025_s_3xte1t/wk_0/services/partes-front` | 534.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-025_s_3xte1t/wk_1/services/partes-front` | 535.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-025_s_3xte1t/wk_2/services/partes-front` | 537.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-025_s_3xte1t/wk_3/services/partes-front` | 533.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-025_s_3xte1t/wk_4/services/partes-front` | 538.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-025_s_3xte1t/wk_5/services/partes-front` | 533.1 |
| Media por mutante evaluado (s) | 93.1 |
| Timeout efectivo por mutante (s) | 600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 600 |
| Workers | 6 |
| Muestreo | sí — 20 de 70 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/incidencias_horas.py:152` [entero]

- Original: `redondeado = round(valor, 2)`
- Mutado:   `redondeado = round(valor, 3)`

#### Análisis

> Por qué ningún test lo caza: todas las horas de los tests tenían como mucho
> un decimal, así que redondear a 2 o a 3 daba el mismo texto. Hueco real
> (el motivo es texto que lee Administración).
> Decisión: **test nuevo** `test_f025_r6_las_horas_del_motivo_van_con_dos_decimales`
> (1.234 h ⇒ «1.23 h extra»). Aplicado a mano el mutante: `1 failed, 12 passed`.

### 2. `services/partes-front/application/services/incidencias_horas.py:185` [comparacion]

- Original: `if linea.es_extra and valor > _EPSILON:`
- Mutado:   `if linea.es_extra and valor >= _EPSILON:`

#### Análisis

> Por qué ningún test lo caza: **mutante equivalente**. La rama solo se
> alcanza dentro de `if abs(valor) > _EPSILON`, así que `valor` nunca vale
> exactamente `_EPSILON` ahí: para todo `valor` que llega, `valor > ε` y
> `valor >= ε` dan lo mismo (un valor positivo que pasa el `abs` es > ε; uno
> negativo falla los dos).
> Decisión: **equivalente justificado**; sin test. Aplicado a mano: `13 passed`.

### 3. `services/partes-front/infrastructure/database/parte_repository.py:555` [logico]

- Original: `and nueva.nivel == NIVEL_BLOQUEO`
- Mutado:   `or nueva.nivel == NIVEL_BLOQUEO`

#### Análisis

> Por qué ningún test lo caza: `_peor` solo se ejercitaba desde la matriz de
> obra, donde todas las líneas de una celda son de la misma persona y día y
> llevan el MISMO nivel, así que nunca comparaba un aviso con un bloqueo.
> Puede ocurrir de verdad (misma clave de trabajador `emp-<ide>` con una
> línea con DNI y otra sin él ⇒ dos «personas»). Hueco real.
> Decisión: **test nuevo** `test_f025_r15_peor_nivel_gana_el_bloqueo_en_cualquier_orden`
> (unitario de `_peor`). Aplicado a mano: `1 failed, 33 passed`.

### 4. `services/partes-front/infrastructure/database/parte_repository.py:555` [comparacion]

- Original: `and nueva.nivel == NIVEL_BLOQUEO`
- Mutado:   `and nueva.nivel != NIVEL_BLOQUEO`

#### Análisis

> Por qué ningún test lo caza: el mismo motivo que el anterior (nunca se
> comparaban niveles distintos dentro de una celda).
> Decisión: **test nuevo** (el mismo,
> `test_f025_r15_peor_nivel_gana_el_bloqueo_en_cualquier_orden`): con el
> mutante, `_peor(bloqueo, aviso)` devuelve el aviso. Aplicado a mano:
> `1 failed, 33 passed`.

### 5. `services/partes-front/infrastructure/database/parte_repository.py:1475` [comparacion]

- Original: `and _is_extra(r) and (r.horas or 0.0) > 0.0):`
- Mutado:   `and _is_extra(r) and (r.horas or 0.0) >= 0.0):`

#### Análisis

> Por qué ningún test lo caza: en los días en aviso de los tests todas las
> extras eran positivas; una extra a 0 h en ese día se listaría como aviso.
> Hueco real (R11: «una entrada por línea extra en aviso con horas > 0»).
> Decisión: **test nuevo** `test_f025_r11_repo_aviso_solo_lista_extras_positivas`
> (AT + extras de 2, 0 y −1 h ⇒ solo la de 2). Aplicado a mano:
> `1 failed, 33 passed`.

### 6. `services/partes-front/infrastructure/database/parte_repository.py:1478` [entero]

- Original: `"nombre": lineas[-1]["nombre"], "horas": r.horas,`
- Mutado:   `"nombre": lineas[-2]["nombre"], "horas": r.horas,`

#### Análisis

> Por qué ningún test lo caza: en los tests la línea anterior en `lineas`
> era siempre de la misma persona, con el mismo nombre. Hueco real.
> Decisión: **test nuevo** `test_f025_r11_repo_aviso_de_la_unica_linea_pedida`
> (la extra en aviso es la única línea que viaja: con `[-2]` revienta con
> `IndexError`, y su nombre es el suyo). Aplicado a mano: `1 failed, 33 passed`.


## Resumen del implementer

6 supervivientes de 20 evaluados: **5 con test nuevo** (cada mutante aplicado
a mano hace fallar su test) y **1 equivalente justificado** (`>=` frente a
`>` tras el filtro `abs(valor) > ε`). Ninguno queda sin resolver.
