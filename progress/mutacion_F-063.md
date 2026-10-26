<!-- progress/mutacion_F-063.md -->
# F-063 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-063` el 2026-10-26 08:03.

## Alcance

Origen del diff: **rama** (`bbc3172722b680f78a4cbd15a0980ef121ba1596` .. `feature/F-063-consulta-obra-rapida`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-api/application/services/obra_sigrid.py` | 1 |
| `services/partes-api/application/services/relectura_cabecera.py` | 4 |
| `services/partes-api/domain/models/clave_obra.py` | 35 |
| `services/partes-api/infrastructure/sigrid/sigrid_lookup_client.py` | 81 |
| **Total** | **121** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 23 |
| Mutantes evaluados | 20 |
| Muertos | 16 |
| Supervivientes | 4 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 191.2 s |
| SHA de HEAD medido | `a00a501ff509eee8b05894b3a8277729f2d04c2c` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-063_bx5g_vbr/wk_0/services/partes-api` | 25.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-063_bx5g_vbr/wk_1/services/partes-api` | 26.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-063_bx5g_vbr/wk_2/services/partes-api` | 25.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-063_bx5g_vbr/wk_3/services/partes-api` | 26.1 |
| Media por mutante evaluado (s) | 9.6 |
| Timeout efectivo por mutante (s) | 300 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 300 |
| Workers | 4 |
| Muestreo | sí — 20 de 23 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-api/infrastructure/sigrid/sigrid_lookup_client.py:70` [entero]

- Original: `_RANGO_VARIANTES = range(0x00A0, 0x0180)`
- Mutado:   `_RANGO_VARIANTES = range(161, 0x0180)`

#### Análisis (implementer, 2026-10-26)

> Por qué ningún test lo caza: el único punto que el mutante deja fuera es U+00A0 (espacio duro), y `clave_obra(" ")` es `""` (es un blanco: lo quita `split`), así que el original tampoco lo apunta en la tabla (`len(base) == 1` falla). `_VARIANTES` sale idéntica: comprobado calculando la tabla con los dos rangos (cero diferencias) y `_clase` de U+0021–U+2FFF igual carácter a carácter.
> Decisión: **mutante equivalente**. No hay entrada observable que lo distinga; el rango arranca en U+00A0 porque R5 lo define así, no porque ese punto aporte variantes.

### 2. `services/partes-api/infrastructure/sigrid/sigrid_lookup_client.py:70` [entero]

- Original: `_RANGO_VARIANTES = range(0x00A0, 0x0180)`
- Mutado:   `_RANGO_VARIANTES = range(0x00A0, 385)`

#### Análisis (implementer, 2026-10-26)

> Por qué ningún test lo caza: añade U+0180 (`ƀ`), cuya clave es `Ƀ` (U+0243), y la tabla gana la entrada `Ƀ → {ƀ}`. `_clase("Ƀ")` ya incluía `ƀ` como minúscula de `Ƀ`, así que ningún patrón cambia (comprobado: `_clase` de U+0021–U+2FFF igual); ningún test miraba la tabla en sí.
> Decisión: **muerto con test nuevo** `test_f063_r5_tabla_de_variantes_solo_del_rango_y_alfanumerica` (invariante de R5: toda variante es de U+00A0–U+017F). Con el mutante aplicado a mano: `AssertionError: ƀ`, 1 failed / 90 passed; sin él, 91 passed.

### 3. `services/partes-api/infrastructure/sigrid/sigrid_lookup_client.py:86` [logico]

- Original: `if len(base) == 1 and base.isalnum() and caracter.isalnum():`
- Mutado:   `if len(base) == 1 or base.isalnum() and caracter.isalnum():`

#### Análisis (implementer, 2026-10-26)

> Por qué ningún test lo caza: con `or` entran signos con clave de un carácter que es él mismo (`¡ ¢ £ ° ± · × ÷`, guion blando…) y, por `base.isalnum() and caracter.isalnum()`, bases de varios caracteres (`SS ← ß`, `IJ ← Ĳĳ`, `ʼN ← ŉ`). Son entradas muertas: los signos solo se apuntan a sí mismos (su clase sigue siendo el carácter tal cual) y `_clase` nunca busca una base de dos caracteres. Ningún patrón cambia (comprobado en U+0021–U+2FFF), pero la tabla deja de cumplir el contrato de §5.2 («dentro de `[...]` solo letras y dígitos»), que un cambio futuro podría romper sin aviso.
> Decisión: **muerto con test nuevo** `test_f063_r5_tabla_de_variantes_solo_del_rango_y_alfanumerica` (toda base es UNA letra o dígito y toda variante es letra o dígito con esa clave). Con el mutante: `AssertionError: ¡`, 1 failed / 90 passed.

### 4. `services/partes-api/infrastructure/sigrid/sigrid_lookup_client.py:86` [logico]

- Original: `if len(base) == 1 and base.isalnum() and caracter.isalnum():`
- Mutado:   `if len(base) == 1 and base.isalnum() or caracter.isalnum():`

#### Análisis (implementer, 2026-10-26)

> Por qué ningún test lo caza: con `or caracter.isalnum()` entran letras y números cuya clave son varios caracteres (`1⁄4 ← ¼`, `1⁄2 ← ½`, `3⁄4 ← ¾`, `SS ← ß`, `IJ ← Ĳĳ`, `L· ← Ŀŀ`, `ʼN ← ŉ`). `_clase` solo busca bases de un carácter, así que esas entradas no cambian ningún patrón (comprobado en U+0021–U+2FFF); son peso muerto en la tabla.
> Decisión: **muerto con el mismo test nuevo** (toda base es de un solo carácter). Con el mutante: `AssertionError: 1⁄4`, 1 failed / 90 passed.

## Resumen del análisis (implementer, 2026-10-26)

| # | Línea | Mutante | Decisión |
|---|---|---|---|
| 1 | `:70` | `range(161, 0x0180)` | equivalente (U+00A0 tiene clave vacía) |
| 2 | `:70` | `range(0x00A0, 385)` | muerto con test nuevo |
| 3 | `:86` | `len(base) == 1 or …` | muerto con test nuevo |
| 4 | `:86` | `… isalnum() or caracter.isalnum()` | muerto con test nuevo |

Tests nuevos (`services/partes-api/tests/test_f063_consulta_obra.py`):
`test_f063_r5_tabla_de_variantes_solo_del_rango_y_alfanumerica` (el que mata 2, 3 y 4) y
`test_f063_r5_tabla_de_variantes_completa` (R5: toda letra o dígito del rango con clave de una
letra o dígito está en su clase; no mata ninguno de los cuatro, deja escrita la otra mitad del
contrato). Comprobado aplicando cada mutante a mano sobre el fichero (sin relanzar la campaña):
el 1 sigue con 91 passed, el 2, el 3 y el 4 caen con 1 failed / 90 passed. Resultado: 16 + 3 =
**19 de 20 muertos, 1 equivalente justificado**.
