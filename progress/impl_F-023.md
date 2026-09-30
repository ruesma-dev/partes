<!-- progress/impl_F-023.md -->
# F-023 · Informe del implementer

Rama `feature/F-023-recurso-alta-empresa`. Rigor **crítico**. Spec aprobada
el 2026-10-01 (DA1–DA12). En curso.

## T1 · Inventario de tests afectados (sin tocar código)

| Qué cambia | Tests que lo usan | Qué se hará |
|---|---|---|
| Clientes con `empresa=` (sv3 `SigridApiClient`, sv5 `SigridWriteClient`) | Ninguno: solo el cableado de producción (sv3 `app.py`, sv5 `main.py` y `app.py`) | Se quita el parámetro en T6/T10/T12/T13 |
| `resides_por_dni` (sv5) | `tests/dobles.py::SigridFake.resides_por_dni`, usado por todos los tests del pipeline (`test_f002_pipeline_fases`, `_workers`, `_transfer_consumer`, `_mutantes`, `_credenciales_y_arranque`, `_settings_y_app`) | El doble pasa a `recursos_por_dni` + `datos_recursos` (T12–T13) |
| `siguiente_cod_pt(ano)` sin empresa (sv5) | `SigridFake.siguiente_cod_pt` | Recibe la empresa (T12–T13) |
| `ObraEntrada` sin empresa (sv5) | `OBRA` y la obra `0404` de `test_f002_pipeline_fases._sigrid` | Se les da `empresa=1`: sin ella R35 hace fallar la escritura, que es lo pedido |
| `fetch_obras` deduplicado por código | sv4 `test_f004_endpoints_congelados.py` (doble `fetch_obras -> []`); sv3 ninguno | Sin cambio: el doble devuelve lista vacía |
| `ORDER BY` de los listados | Ningún test mira el SQL | Tests nuevos en T6/T14/T18 |
| `EmpleadoMatcher.match` / `ObraMatcher.match` sin empresa | Ninguno (el pipeline `_match` no tenía tests) | Tests nuevos en T8 |
| `empleado_reside` como recurso (sv3) | `dobles.registro` (`empleado_reside=501`); con `conciliar_todos` y recursos: `test_f003_r26_review_required` (recurso 501 con `conide=1` y el mismo DNI, así que sigue siendo el único candidato). El resto llama a `_reclasificar_extras_jornada` con `ride_por_reg` ya hecho | Deben seguir en verde sin cambios (T9) |
| `EmpleadoOption` / `ObraOption` (sv4) | Dobles de `test_f004_endpoints_congelados.py` sin `empresa` | `empresa` con valor por defecto `None` |
