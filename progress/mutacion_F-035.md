<!-- progress/mutacion_F-035.md -->
# F-035 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-035` el 2026-10-07 21:29.

## Alcance

Origen del diff: **rama** (`6e56244ac08b5565bfb18afd45e63c8d7fbb0280` .. `feature/F-035-selector-recursos-por-empresa`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/recurso_catalog.py` | 107 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 67 |
| `services/partes-front/infrastructure/sigrid/sigrid_lookup_client.py` | 109 |
| `services/partes-front/interface_adapters/web/app.py` | 171 |
| **Total** | **454** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 69 |
| Mutantes evaluados | 20 |
| Muertos | 11 |
| Supervivientes | 3 |
| Timeouts | 6 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 5973.8 s |
| SHA de HEAD medido | `35fcfe4b003e6bf1c6eba5a56cf8e943a25d86ff` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-035_mt116ekh/wk_0/services/partes-front` | 1475.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-035_mt116ekh/wk_1/services/partes-front` | 1491.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-035_mt116ekh/wk_2/services/partes-front` | 1468.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-035_mt116ekh/wk_3/services/partes-front` | 1466.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-035_mt116ekh/wk_4/services/partes-front` | 1464.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-035_mt116ekh/wk_5/services/partes-front` | 1462.1 |
| Media por mutante evaluado (s) | 298.7 |
| Timeout efectivo por mutante (s) | 1200 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 1200 |
| Workers | 6 |
| Muestreo | sí — 20 de 69 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/interface_adapters/web/app.py:1191` [booleano]

- Original: `{"ok": False, "error": "Empleado no encontrado en el maestro "`
- Mutado:   `{"ok": True, "error": "Empleado no encontrado en el maestro "`

#### Análisis (implementer)

> Por qué ningún test lo caza: es el 404 del camino `ide` (sin `recurso_ide`)
> de `_trabajador_pedido`, código que existía antes de F-035 y se movió al
> helper; ningún test miraba el `ok` de ese 404 con un `ide` desconocido.
> Decisión: **hueco real → test nuevo** `test_f035_r15_ide_desconocido_404_ok_false`
> (confirmar y reasignar). Verificado a mano: con el mutante aplicado falla
> (`assert True is False`, 2 failed); sin él, verde. Campaña NO relanzada
> (rigor estándar: supervivientes analizados).

### 2. `services/partes-front/interface_adapters/web/app.py:1216` [entero]

- Original: `p["nombre_leido"], candidatos_de, top_n=5)`
- Mutado:   `p["nombre_leido"], candidatos_de, top_n=6)`

#### Análisis (implementer)

> Por qué ningún test lo caza: `top_n=5` (tope de candidatos por tarjeta de
> Conciliar) ya existía antes de F-035 en la misma llamada; los datos de los
> tests nunca tienen más de 3 candidatos por nombre, así que 5 y 6 dan lo
> mismo.
> Decisión: **hueco real de bajo riesgo, sin test**: es un tope de
> presentación (cuántas filas se pintan), no afecta a qué se guarda ni a qué
> llega a Sigrid. Lo juzga el reviewer.

### 3. `services/partes-front/interface_adapters/web/app.py:1307` [booleano]

- Original: `alias_ok = False`
- Mutado:   `alias_ok = True`

#### Análisis (implementer)

> Por qué ningún test lo caza: es la rama `except` del alias en
> `/api/empleado/reasignar` (el alias falla al escribirse → `alias_ok =
> False`). Rama anterior a F-035, que solo se ha reindentado (F-035 la salta
> sin ficha, R14); ningún test, antes ni ahora, provoca un fallo del upsert
> del alias.
> Decisión: **hueco previo, fuera del alcance de F-035**; sin test. El efecto
> del mutante es solo el flag informativo de la respuesta.

## Timeouts

- `services/partes-front/application/services/recurso_catalog.py:73` [booleano] self._ever_loaded = False -> self._ever_loaded = True
- `services/partes-front/application/services/recurso_catalog.py:97` [comparacion] if self._ever_loaded and (now - self._loaded_at) < self._ttl: -> if self._ever_loaded and (now - self._loaded_at) <= self._ttl:
- `services/partes-front/infrastructure/database/parte_repository.py:3162` [logico] if empleado_ide is None and empleado_reside is not None -> if empleado_ide is None or empleado_reside is not None
- `services/partes-front/infrastructure/sigrid/sigrid_lookup_client.py:347` [comparacion] if ide is None or ide in sin_dni: -> if ide is not None or ide in sin_dni:
- `services/partes-front/infrastructure/sigrid/sigrid_lookup_client.py:352` [comparacion] if pos is not None: -> if pos is None:
- `services/partes-front/infrastructure/sigrid/sigrid_lookup_client.py:358` [logico] if previo.candef is None and candef is not None: -> if previo.candef is None or candef is not None:

### Re-juicio a mano de los 6 timeouts (implementer)

La línea base por worktree fue ~1470 s (máquina compartida con otros dos
implementers y otros proyectos) y el timeout se fijó a mano en 1200 s: los 6
primeros mutantes dieron timeout, que **no es una medición**. Se re-juzgaron
aplicando cada mutante en el árbol, corriendo los 6 ficheros de tests de la
feature (`test_f035_*` + `test_f023_catalogo_empresa.py`, 106 tests) y
restaurando con `git checkout` (traza en el informe de implementación):

| Mutante | Resultado | Tests que lo matan / análisis |
|---|---|---|
| `sigrid_lookup_client.py:352` `pos is not None` → `is None` | **muerto** | 6 failed (`test_f035_r1_encadena_paginas`, `test_f035_r2_…`) |
| `sigrid_lookup_client.py:347` `ide is None or …` → `is not None or …` | **muerto** | 6 failed (`test_f035_r1_…`, `test_f035_r2_…`) |
| `parte_repository.py:3162` `and` → `or` | **muerto** | 2 failed (`test_f035_r19_crear_con_ficha_o_sin_recurso_no_marca`) |
| `recurso_catalog.py:97` `<` → `<=` | **muerto** | 1 failed (`test_f035_r6_fallo_de_refresco_conserva_la_ultima_lista`, TTL 0) |
| `sigrid_lookup_client.py:358` `and` → `or` | superviviente → **hueco real, test nuevo** | Con `or`, una fila repetida pisaba un `candef` ya leído. Test nuevo `test_f035_r2_la_primera_categoria_y_candef_no_nulos_mandan`: con el mutante falla (`('Oficial', 6.0) == ('Oficial', 8.0)`). |
| `recurso_catalog.py:73` `_ever_loaded = False` → `True` | superviviente → **equivalente** | Con `_loaded_at = 0`, `now - 0` (segundos desde 1970) nunca es `< ttl` (600 s): la primera llamada carga igual. Mismo patrón que `EmpleadoCatalog`. |

**Balance tras el análisis**: de 20, 15 muertos (11 de la campaña + 4
re-juzgados), 1 equivalente, 2 huecos cerrados con test nuevo (verificados a
mano, campaña no relanzada) y 2 huecos de bajo riesgo o previos sin test.

