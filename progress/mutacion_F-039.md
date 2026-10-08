<!-- progress/mutacion_F-039.md -->
# F-039 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-039` el 2026-10-08 13:53.

## Alcance

Origen del diff: **rama** (`3b6790fd7cd061e42c60ad16e9dbc7b09b8819d4` .. `feature/F-039-nombre-empresa-en-combos`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/empresas.py` | 8 |
| `services/partes-front/interface_adapters/web/app.py` | 13 |
| **Total** | **21** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 3 |
| Mutantes evaluados | 3 |
| Muertos | 1 |
| Supervivientes | 2 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1505.7 s |
| SHA de HEAD medido | `409cb1c9abef9d666dc5978cd054d8697c1c7d60` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-039_n962t546/wk_0/services/partes-front` | 487.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-039_n962t546/wk_1/services/partes-front` | 487.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-039_n962t546/wk_2/services/partes-front` | 497.2 |
| Media por mutante evaluado (s) | 501.9 |
| Timeout efectivo por mutante (s) | 995 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 3 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/interface_adapters/web/app.py:1344` [aritmetico]

- Original: `"dni": e.dni, "score": round(sc * 100), "empresa": e.empresa,`
- Mutado:   `"dni": e.dni, "score": round(sc // 100), "empresa": e.empresa,`

#### Análisis

> Por qué ningún test lo caza: el cálculo de `score` es anterior a F-039
> (búsqueda manual de Conciliar); la línea entró en el alcance solo porque
> F-039 le añadió una coma para colgar `empresa_nombre`. Ningún test de sv4
> comprobaba el valor del `score`, solo su presencia (`test_f039_r12_…`
> compara claves). Hueco real, no equivalente: `sc // 100` da 0 siempre.
> Decisión: **test nuevo** `test_f039_r12_buscar_score_intacto` (R12: «no
> cambia ningún otro campo»): coincidencia exacta ⇒ `score == 100`, el resto
> entre 0 y 100. Comprobado a mano aplicando el mutante: `assert 0 == 100`,
> 1 failed. La campaña no se relanza (regla del arnés: medir-tapar-medir).

### 2. `services/partes-front/interface_adapters/web/app.py:1344` [entero]

- Original: `"dni": e.dni, "score": round(sc * 100), "empresa": e.empresa,`
- Mutado:   `"dni": e.dni, "score": round(sc * 101), "empresa": e.empresa,`

#### Análisis

> Por qué ningún test lo caza: mismo motivo que el 1 (línea preexistente,
> en alcance por la coma; nadie comprobaba el valor). Hueco real: el `score`
> pasaría de 100 a 101 para una coincidencia exacta.
> Decisión: **test nuevo**, el mismo `test_f039_r12_buscar_score_intacto`.
> Comprobado a mano aplicando el mutante: `assert 101 == 100`, 1 failed.

