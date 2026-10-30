<!-- progress/mutacion_F-056_da32.md -->
# F-056 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-056` el 2026-10-30 10:31.

## Alcance

Origen del diff: **rama** (`3b3711375384dce8d11138e5b75e571320181bfb` .. `feature/F-056-franquicia-de-extras`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/franquicia.py` | 10 |
| `services/partes-front/infrastructure/database/orm_models.py` | 3 |
| `services/partes-front/interface_adapters/web/app.py` | 5 |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | 3 |
| `services/partes-transfer/domain/models/registro_models.py` | 4 |
| **Total** | **25** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 4 |
| Mutantes evaluados | 4 |
| Muertos | 3 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 3800.9 s |
| SHA de HEAD medido | `2e910d166bbf141eb96341830d64e2aca75ac5d1` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-056_g397b1je/wk_0/services/partes-front` | 964.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-056_g397b1je/wk_1/services/partes-front` | 969.2 |
| Media por mutante evaluado (s) | 950.2 |
| Timeout efectivo por mutante (s) | 1939 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 600 |
| Workers | 2 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/franquicia.py:192` [entero]

- Original: `return [x for x in lineas if int(x.get("recurso_ide") or 0) == rec]`
- Mutado:   `return [x for x in lineas if int(x.get("recurso_ide") or 1) == rec]`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: el test de `lineas_del_recurso` pedía el recurso 501; con él, una línea sin recurso vale 0 o 1 y queda fuera igual. Solo se distingue pidiendo el recurso 1, y ningún test lo hacía. No es equivalente: con el mutante, una línea con `recurso_ide` None entra en las del recurso 1 y podría elegir la obra de su ajuste.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_franquicia.py::test_f056_da32_linea_sin_recurso_no_es_del_recurso_1`. Verificado a mano con `sys.executable -m pytest -q -p no:cacheprovider --tb=line tests/test_f056_franquicia.py` desde `services/partes-front`: con el mutante, exit 1 (1 failed, 81 passed in 1.14s, `AssertionError: assert [{'registro_i...00000T', ...}] == []`); sin él, exit 0 (82 passed in 0.62s). La campaña no se ha relanzado.

