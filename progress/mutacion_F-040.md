<!-- progress/mutacion_F-040.md -->
# F-040 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-040` el 2026-10-08 16:39.

## Alcance

Origen del diff: **rama** (`1a5b795bccfacf5cbe924585d5d30e6948635edf` .. `feature/F-040-recursos-sin-dni-por-nombre`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/recurso_catalog.py` | 4 |
| `services/partes-front/infrastructure/database/orm_models.py` | 17 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 12 |
| `services/partes-front/infrastructure/sigrid/sigrid_lookup_client.py` | 6 |
| `services/partes-front/interface_adapters/web/app.py` | 8 |
| `services/partes-persistencia/application/services/casado_recurso.py` | 50 |
| `services/partes-persistencia/application/services/empleado_matcher.py` | 6 |
| `services/partes-persistencia/application/services/medicion_casado.py` | 16 |
| `services/partes-persistencia/application/services/recurso_conciliador.py` | 3 |
| `services/partes-persistencia/application/services/seleccion_sigrid.py` | 67 |
| `services/partes-persistencia/application/services/sigrid_matcher_provider.py` | 6 |
| `services/partes-persistencia/domain/models/parte_records.py` | 3 |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | 17 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 4 |
| `services/partes-persistencia/medir_casado_recursos.py` | 6 |
| **Total** | **225** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 40 |
| Mutantes evaluados | 40 |
| Muertos | 38 |
| Supervivientes | 0 |
| Timeouts | 2 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 3244.4 s |
| SHA de HEAD medido | `0c851f467724bea9c353815e71f791b90be5229c` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_lowjdul1/wk_0/services/partes-front` | 539.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_lowjdul1/wk_0/services/partes-persistencia` | 22.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_lowjdul1/wk_1/services/partes-front` | 546.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_lowjdul1/wk_1/services/partes-persistencia` | 24.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_lowjdul1/wk_2/services/partes-front` | 548.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_lowjdul1/wk_2/services/partes-persistencia` | 23.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_lowjdul1/wk_3/services/partes-front` | 548.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_lowjdul1/wk_3/services/partes-persistencia` | 22.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_lowjdul1/wk_4/services/partes-front` | 547.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_lowjdul1/wk_4/services/partes-persistencia` | 22.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_lowjdul1/wk_5/services/partes-front` | 543.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_lowjdul1/wk_5/services/partes-persistencia` | 21.0 |
| Media por mutante evaluado (s) | 81.1 |
| Timeout efectivo por mutante (s) | 600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 600 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Timeouts

- `services/partes-front/interface_adapters/web/app.py:1431` [logico] con_alias = emp["ide"] is not None or emp["reside"] is not None -> con_alias = emp["ide"] is not None and emp["reside"] is not None
- `services/partes-front/interface_adapters/web/app.py:1431` [comparacion] con_alias = emp["ide"] is not None or emp["reside"] is not None -> con_alias = emp["ide"] is not None or emp["reside"] is None


## Análisis de los timeouts (implementer, 2026-10-08)

Los dos timeouts son de sv4, cuya suite completa tarda **540–549 s** en la
línea base con 6 workers en paralelo: con 600 s de tope, cualquier mutante de
sv4 roza el límite. No son bucles: comprobados a mano aplicando cada mutante
en el worktree y lanzando solo `tests/test_f040_alias.py` (luego
`git checkout` del fichero):

| Mutante (`app.py:1431`) | Resultado | Tests que lo cazan |
|---|---|---|
| `... is not None and emp["reside"] is not None` | **muerto** (3 failed, 14 passed, 7.5 s) | `test_f040_r17_reasignar_a_recurso_sin_dni_guarda_alias[cuerpo0/1]`, `test_f040_r17_reasignar_por_ficha_recurso_ide_null` |
| `... or emp["reside"] is None` | **muerto** (2 failed, 15 passed, 8.2 s) | `test_f040_r17_reasignar_a_recurso_sin_dni_guarda_alias[cuerpo0/1]` |

Resultado efectivo: **40 mutantes, 40 muertos, 0 supervivientes.** El JS
(`static/app.js`) y la plantilla quedan fuera del mutador (solo Python): los
cubre `tests/test_f040_vistas.py` ejecutándolos con node.
