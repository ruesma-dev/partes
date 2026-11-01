<!-- progress/mutacion_F-061.md -->
# F-061 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-061` el 2026-10-26 17:29.

## Alcance

Origen del diff: **rama** (`4047137585df160bc1a7c68404abc2d5097aeed9` .. `feature/F-061-parte-vacio-tras-borrar-lineas`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/parte_vacio.py` | 131 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 300 |
| `services/partes-front/interface_adapters/web/app.py` | 20 |
| `services/partes-front/limpiar_partes_vacios.py` | 217 |
| **Total** | **668** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 110 |
| Mutantes evaluados | 20 |
| Muertos | 16 |
| Supervivientes | 4 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 4373.0 s |
| SHA de HEAD medido | `b1bd41961d067c41de6c48d0b9e76caf59b478a7` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-061_uwgwjqdb/wk_0/services/partes-front` | 693.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-061_uwgwjqdb/wk_1/services/partes-front` | 696.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-061_uwgwjqdb/wk_2/services/partes-front` | 694.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-061_uwgwjqdb/wk_3/services/partes-front` | 695.7 |
| Media por mutante evaluado (s) | 218.7 |
| Timeout efectivo por mutante (s) | 1394 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 300 |
| Workers | 4 |
| Muestreo | sí — 20 de 110 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/infrastructure/database/parte_repository.py:4258` [entero]

- Original: `.limit(1)`
- Mutado:   `.limit(2)`

#### Análisis (implementer, 2026-10-26)

> Por qué ningún test lo caza: la consulta «¿le queda alguna fila?» de
> `_borrar_retirados_sin_filas` se lee con `.first()`, que es None si y solo
> si el parte no tiene ninguna fila, con `LIMIT 1` o con `LIMIT 2`. Solo
> cambia una fila leída de más, nunca la decisión.
> Decisión: **equivalente propuesto, pendiente de aceptación del humano**.
> Demostración ejecutable: `python progress/equivalentes_F-061.py` ⇒
> `#1 equivalente en 6125 casos; el control .limit(0) difiere.` (salida 0,
> 6 min): original y mutado sobre SQLite con partes retirados, con otra
> marca, activos, de sv3 y de la papelera, de 0 a 3 filas, por `ids=None`
> y por ids; el control `.limit(0)` sí difiere.

### 2. `services/partes-front/limpiar_partes_vacios.py:78` [booleano]

- Original: `self.engine = create_engine(database_url, future=True,`
- Mutado:   `self.engine = create_engine(database_url, future=False,`

#### Análisis (implementer, 2026-10-26)

> Por qué ningún test lo caza: ningún test construía `FabricaSesiones`
> (los tests pasan su propia fábrica a `main`). En SQLAlchemy 2.0.52,
> `create_engine(..., future=False)` lanza `ArgumentError`.
> Decisión: **hueco**. Lo mata
> `test_f061_r18_fabrica_de_sesiones_del_script_funciona`. Comprobado
> aplicando el mutante a mano: `1 failed, 44 passed`
> (`ArgumentError: The 'future' parameter passed to create_engine() may
> only be set to True.`).

### 3. `services/partes-front/limpiar_partes_vacios.py:83` [booleano]

- Original: `expire_on_commit=False, future=True)`
- Mutado:   `expire_on_commit=False, future=False)`

#### Análisis (implementer, 2026-10-26)

> Por qué ningún test lo caza: el mismo hueco que el #2. `Session(future=False)`
> lanza `ArgumentError` en SQLAlchemy 2, al abrir la primera sesión.
> Decisión: **hueco**. Lo mata
> `test_f061_r18_fabrica_de_sesiones_del_script_funciona`, que abre una
> sesión con cada fábrica. Comprobado a mano: `1 failed, 44 passed`
> (`ArgumentError: The 'future' parameter passed to Session() may only be
> set to True.`).

### 4. `services/partes-front/limpiar_partes_vacios.py:127` [not]

- Original: `if not f["motivo_exclusion"])`
- Mutado:   `if f["motivo_exclusion"])`

#### Análisis (implementer, 2026-10-26)

> Por qué ningún test lo caza: la línea es la tabla «Categoría
> (candidatos)» del Markdown. El nº de candidatos y lo que `--ejecutar`
> borra o retira salen de `candidatos()`, que sí está cubierta, pero
> ningún test leía las tablas del informe. Con el mutante, el informe que
> lee el humano antes de autorizar la M2 contaría las categorías de los
> EXCLUIDOS.
> Decisión: **hueco**. Lo mata
> `test_f061_r14_markdown_cuenta_categorias_y_acciones_de_candidatos`, que
> comprueba las tres tablas (categoría y acción de los candidatos y motivo
> de los excluidos). Comprobado a mano: `1 failed, 44 passed`
> (`assert [... 'todas_en_papelera' | 2 |] == [... | 1 |]`).

