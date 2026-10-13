<!-- progress/mutacion_F-043.md -->
# F-043 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-043` el 2026-10-13 16:32.

## Alcance

Origen del diff: **rama** (`3d7882d355871bba6e26c1b533ebf364eafe5e51` .. `feature/F-043-fecha-del-parte-confirmar-y-recargar`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/seguimiento_recalculo.py` | 82 |
| `services/partes-front/infrastructure/database/orm_models.py` | 10 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 137 |
| `services/partes-front/interface_adapters/web/app.py` | 77 |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | 10 |
| `services/partes-persistencia/infrastructure/database/recalculo_seguimiento.py` | 63 |
| `services/partes-persistencia/interface_adapters/api/app.py` | 6 |
| `services/partes-persistencia/interface_adapters/workers/despacho.py` | 45 |
| `services/partes-persistencia/main_worker.py` | 6 |
| **Total** | **436** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 60 |
| Mutantes evaluados | 60 |
| Muertos | 50 |
| Supervivientes | 10 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 4014.8 s |
| SHA de HEAD medido | `d8d51a5848ab1df4ce196ae3edc018dc05caddfd` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_0qkr5x1r/wk_0/services/partes-front` | 446.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_0qkr5x1r/wk_0/services/partes-persistencia` | 23.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_0qkr5x1r/wk_1/services/partes-front` | 444.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_0qkr5x1r/wk_1/services/partes-persistencia` | 24.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_0qkr5x1r/wk_2/services/partes-front` | 446.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_0qkr5x1r/wk_2/services/partes-persistencia` | 23.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_0qkr5x1r/wk_3/services/partes-front` | 447.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_0qkr5x1r/wk_3/services/partes-persistencia` | 23.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_0qkr5x1r/wk_4/services/partes-front` | 446.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_0qkr5x1r/wk_4/services/partes-persistencia` | 23.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_0qkr5x1r/wk_5/services/partes-front` | 445.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_0qkr5x1r/wk_5/services/partes-persistencia` | 24.2 |
| Media por mutante evaluado (s) | 66.9 |
| Timeout efectivo por mutante (s) | 600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 600 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/infrastructure/database/orm_models.py:99` [entero]

- Original: `recalculo_pedido_id: Mapped[str | None] = mapped_column(String(36))        # sv4`
- Mutado:   `recalculo_pedido_id: Mapped[str | None] = mapped_column(String(37))        # sv4`

#### Análisis (implementer, 2026-10-13)

> Por qué ningún test lo caza: **hueco real de la suite de sv4**. La
> longitud la comprueban el test de la raíz `tests/test_f043_contrato_seguimiento.py`
> (R34) y el guardián byte-idéntico de F-010, pero la campaña de un fichero
> de sv4 solo corre la suite de sv4, y ningún test de esa suite miraba
> el DDL de las columnas nuevas.
> Decisión: **test nuevo** `services/partes-front/tests/test_f043_alcance_y_seguimiento.py::test_f043_r34_el_ddl_de_sv4_trae_las_cuatro_columnas`
> (parametrizado por columna: exige `VARCHAR(36|64)` en `ddl_complementario()`
> de la copia del servicio, patrón de `test_f010_r6_..._sv4`). Comprobado a
> mano aplicando el mutante: **muerto** (1 failed, 3 passed).

### 2. `services/partes-front/infrastructure/database/orm_models.py:100` [entero]

- Original: `recalculo_pedido_at_utc: Mapped[str | None] = mapped_column(String(64))    # sv4`
- Mutado:   `recalculo_pedido_at_utc: Mapped[str | None] = mapped_column(String(65))    # sv4`

#### Análisis (implementer, 2026-10-13)

> Por qué ningún test lo caza: **hueco real de la suite de sv4**. La
> longitud la comprueban el test de la raíz `tests/test_f043_contrato_seguimiento.py`
> (R34) y el guardián byte-idéntico de F-010, pero la campaña de un fichero
> de sv4 solo corre la suite de sv4, y ningún test de esa suite miraba
> el DDL de las columnas nuevas.
> Decisión: **test nuevo** `services/partes-front/tests/test_f043_alcance_y_seguimiento.py::test_f043_r34_el_ddl_de_sv4_trae_las_cuatro_columnas`
> (parametrizado por columna: exige `VARCHAR(36|64)` en `ddl_complementario()`
> de la copia del servicio, patrón de `test_f010_r6_..._sv4`). Comprobado a
> mano aplicando el mutante: **muerto** (1 failed, 3 passed).

### 3. `services/partes-front/infrastructure/database/orm_models.py:101` [entero]

- Original: `recalculo_terminado_id: Mapped[str | None] = mapped_column(String(36))     # sv3`
- Mutado:   `recalculo_terminado_id: Mapped[str | None] = mapped_column(String(37))     # sv3`

#### Análisis (implementer, 2026-10-13)

> Por qué ningún test lo caza: **hueco real de la suite de sv4**. La
> longitud la comprueban el test de la raíz `tests/test_f043_contrato_seguimiento.py`
> (R34) y el guardián byte-idéntico de F-010, pero la campaña de un fichero
> de sv4 solo corre la suite de sv4, y ningún test de esa suite miraba
> el DDL de las columnas nuevas.
> Decisión: **test nuevo** `services/partes-front/tests/test_f043_alcance_y_seguimiento.py::test_f043_r34_el_ddl_de_sv4_trae_las_cuatro_columnas`
> (parametrizado por columna: exige `VARCHAR(36|64)` en `ddl_complementario()`
> de la copia del servicio, patrón de `test_f010_r6_..._sv4`). Comprobado a
> mano aplicando el mutante: **muerto** (1 failed, 3 passed).

### 4. `services/partes-front/infrastructure/database/orm_models.py:102` [entero]

- Original: `recalculo_terminado_at_utc: Mapped[str | None] = mapped_column(String(64)) # sv3`
- Mutado:   `recalculo_terminado_at_utc: Mapped[str | None] = mapped_column(String(65)) # sv3`

#### Análisis (implementer, 2026-10-13)

> Por qué ningún test lo caza: **hueco real de la suite de sv4**. La
> longitud la comprueban el test de la raíz `tests/test_f043_contrato_seguimiento.py`
> (R34) y el guardián byte-idéntico de F-010, pero la campaña de un fichero
> de sv4 solo corre la suite de sv4, y ningún test de esa suite miraba
> el DDL de las columnas nuevas.
> Decisión: **test nuevo** `services/partes-front/tests/test_f043_alcance_y_seguimiento.py::test_f043_r34_el_ddl_de_sv4_trae_las_cuatro_columnas`
> (parametrizado por columna: exige `VARCHAR(36|64)` en `ddl_complementario()`
> de la copia del servicio, patrón de `test_f010_r6_..._sv4`). Comprobado a
> mano aplicando el mutante: **muerto** (1 failed, 3 passed).

### 5. `services/partes-front/interface_adapters/web/app.py:1926` [booleano]

- Original: `@app.get("/api/partes/{document_id}/alcance", include_in_schema=False)`
- Mutado:   `@app.get("/api/partes/{document_id}/alcance", include_in_schema=True)`

#### Análisis (implementer, 2026-10-13)

> Por qué ningún test lo caza: **hueco real**: ningún test miraba el
> esquema OpenAPI; el endpoint responde igual con o sin `include_in_schema`.
> Design §3 lo pide fuera del esquema (interno del portal, como el resto de
> `/api/...`).
> Decisión: **test nuevo** `services/partes-front/tests/test_f043_alcance_y_seguimiento.py::test_f043_r2_r17_los_endpoints_no_salen_en_el_esquema`
> (`app.openapi()["paths"]` no contiene ninguno de los dos). Comprobado a
> mano aplicando el mutante: **muerto** (1 failed).

### 6. `services/partes-front/interface_adapters/web/app.py:1935` [booleano]

- Original: `@app.get("/api/recalculo", include_in_schema=False)`
- Mutado:   `@app.get("/api/recalculo", include_in_schema=True)`

#### Análisis (implementer, 2026-10-13)

> Por qué ningún test lo caza: **hueco real**: ningún test miraba el
> esquema OpenAPI; el endpoint responde igual con o sin `include_in_schema`.
> Design §3 lo pide fuera del esquema (interno del portal, como el resto de
> `/api/...`).
> Decisión: **test nuevo** `services/partes-front/tests/test_f043_alcance_y_seguimiento.py::test_f043_r2_r17_los_endpoints_no_salen_en_el_esquema`
> (`app.openapi()["paths"]` no contiene ninguno de los dos). Comprobado a
> mano aplicando el mutante: **muerto** (1 failed).

### 7. `services/partes-persistencia/infrastructure/database/orm_models.py:99` [entero]

- Original: `recalculo_pedido_id: Mapped[str | None] = mapped_column(String(36))        # sv4`
- Mutado:   `recalculo_pedido_id: Mapped[str | None] = mapped_column(String(37))        # sv4`

#### Análisis (implementer, 2026-10-13)

> Por qué ningún test lo caza: **hueco real de la suite de sv3**. La
> longitud la comprueban el test de la raíz `tests/test_f043_contrato_seguimiento.py`
> (R34) y el guardián byte-idéntico de F-010, pero la campaña de un fichero
> de sv3 solo corre la suite de sv3, y ningún test de esa suite miraba
> el DDL de las columnas nuevas.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f043_seguimiento_sv3.py::test_f043_r34_el_ddl_de_sv3_trae_las_cuatro_columnas`
> (parametrizado por columna: exige `VARCHAR(36|64)` en `ddl_complementario()`
> de la copia del servicio, patrón de `test_f010_r6_..._sv4`). Comprobado a
> mano aplicando el mutante: **muerto** (1 failed, 3 passed).

### 8. `services/partes-persistencia/infrastructure/database/orm_models.py:100` [entero]

- Original: `recalculo_pedido_at_utc: Mapped[str | None] = mapped_column(String(64))    # sv4`
- Mutado:   `recalculo_pedido_at_utc: Mapped[str | None] = mapped_column(String(65))    # sv4`

#### Análisis (implementer, 2026-10-13)

> Por qué ningún test lo caza: **hueco real de la suite de sv3**. La
> longitud la comprueban el test de la raíz `tests/test_f043_contrato_seguimiento.py`
> (R34) y el guardián byte-idéntico de F-010, pero la campaña de un fichero
> de sv3 solo corre la suite de sv3, y ningún test de esa suite miraba
> el DDL de las columnas nuevas.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f043_seguimiento_sv3.py::test_f043_r34_el_ddl_de_sv3_trae_las_cuatro_columnas`
> (parametrizado por columna: exige `VARCHAR(36|64)` en `ddl_complementario()`
> de la copia del servicio, patrón de `test_f010_r6_..._sv4`). Comprobado a
> mano aplicando el mutante: **muerto** (1 failed, 3 passed).

### 9. `services/partes-persistencia/infrastructure/database/orm_models.py:101` [entero]

- Original: `recalculo_terminado_id: Mapped[str | None] = mapped_column(String(36))     # sv3`
- Mutado:   `recalculo_terminado_id: Mapped[str | None] = mapped_column(String(37))     # sv3`

#### Análisis (implementer, 2026-10-13)

> Por qué ningún test lo caza: **hueco real de la suite de sv3**. La
> longitud la comprueban el test de la raíz `tests/test_f043_contrato_seguimiento.py`
> (R34) y el guardián byte-idéntico de F-010, pero la campaña de un fichero
> de sv3 solo corre la suite de sv3, y ningún test de esa suite miraba
> el DDL de las columnas nuevas.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f043_seguimiento_sv3.py::test_f043_r34_el_ddl_de_sv3_trae_las_cuatro_columnas`
> (parametrizado por columna: exige `VARCHAR(36|64)` en `ddl_complementario()`
> de la copia del servicio, patrón de `test_f010_r6_..._sv4`). Comprobado a
> mano aplicando el mutante: **muerto** (1 failed, 3 passed).

### 10. `services/partes-persistencia/infrastructure/database/orm_models.py:102` [entero]

- Original: `recalculo_terminado_at_utc: Mapped[str | None] = mapped_column(String(64)) # sv3`
- Mutado:   `recalculo_terminado_at_utc: Mapped[str | None] = mapped_column(String(65)) # sv3`

#### Análisis (implementer, 2026-10-13)

> Por qué ningún test lo caza: **hueco real de la suite de sv3**. La
> longitud la comprueban el test de la raíz `tests/test_f043_contrato_seguimiento.py`
> (R34) y el guardián byte-idéntico de F-010, pero la campaña de un fichero
> de sv3 solo corre la suite de sv3, y ningún test de esa suite miraba
> el DDL de las columnas nuevas.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f043_seguimiento_sv3.py::test_f043_r34_el_ddl_de_sv3_trae_las_cuatro_columnas`
> (parametrizado por columna: exige `VARCHAR(36|64)` en `ddl_complementario()`
> de la copia del servicio, patrón de `test_f010_r6_..._sv4`). Comprobado a
> mano aplicando el mutante: **muerto** (1 failed, 3 passed).

## Resultado efectivo (implementer, 2026-10-13)

Los 10 supervivientes eran **huecos reales**, ninguno equivalente; los cazan
5 tests nuevos (4 + 4 parametrizaciones del DDL por servicio y el del
esquema). Verificación a mano, aplicando cada mutante en el árbol, lanzando
solo el test nuevo y restaurando con `git checkout` (script en el
scratchpad del implementer):

| Mutante | Resultado |
|---|---|
| sv4 `orm_models.py:99-102` (`String(36→37)`, `String(64→65)`, ×4) | 4 × **muerto** (1 failed, 3 passed) |
| sv4 `app.py:1926` / `app.py:1935` (`include_in_schema=True`) | 2 × **muerto** (1 failed) |
| sv3 `orm_models.py:99-102` (×4) | 4 × **muerto** (1 failed, 3 passed) |

**60 mutantes, 60 muertos, 0 supervivientes sin resolver.** La campaña no se
relanza (medir-tapar-medir no tiene final). El JS (`static/app.js`) y las
plantillas quedan fuera del mutador (solo Python): los cubre
`tests/test_f043_portal_fecha.py` ejecutando `app.js` con node.
