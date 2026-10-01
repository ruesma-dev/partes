<!-- progress/impl_F-022.md -->
# F-022 · Aprobar solo las líneas seleccionadas — Informe del implementer

(En curso.)

## T1 · Inventario de tests de sv4 afectados

Contraste de la spec con el código de dev (F-021, F-023 y F-024 incluidas):
la spec describe bien `_payload_registro`, los tres `/api/aprobar/*`, el
modal (`resumenHtml`, sondeo de F-024 R29) y `PartidaSel`. Lo único que no
nombra es el aviso de cuenta de F-021 (`avisosCuentaHtml`), que vive dentro
de `resumenHtml(pf)`: se integra llamando a `resumenHtml` por grupo.

| Test | Qué mira | Efecto de F-022 |
|---|---|---|
| `test_f024_borrado_sigrid.py::test_f024_r22_payload_repo_sin_ids` | dict ENTERO de `lineas_para_registro([])` | **Se adapta**: + `grupos: []` y `excluidas_detalle: []` (nota en el test) |
| `test_f021_preflight_cuenta.py::test_f021_r21_…` | `acciones` plano == sv5 | un grupo ⇒ plano idéntico (R16): sin cambio |
| `test_f021_preflight_cuenta.py::test_f021_r19_resumen_html_llama_a_avisos_cuenta` | `resumenHtml` contiene `avisosCuentaHtml(pf.acciones)` | se conserva `resumenHtml(pf)` y se llama por grupo |
| `test_f003_r23_bloqueo_registro.py::…se_sirve_igual` | campo plano `escribir` que inventa el doble de sv5 | un grupo ⇒ plano = respuesta tal cual: sin cambio |
| `test_f003_r18_…:127`, `test_f003_r23_…:255`, `test_f024_…:444` | claves del payload a sv5 = `obra, lineas, pisar_claves, usuario` | R33 lo conserva |
| `test_f002_aprobar_encolar.py:133,154`, `test_f002_mutantes.py:245`, `test_f024_…:472` | `pisar_claves` SIN prefijo | un solo grupo ⇒ van a ese grupo (R19): sin cambio |
| `test_f002_degradacion.py`, `test_f002_mutantes.py` (`RepositorioRoto`) | traza o marcado que fallan | el doble delega por `__getattr__`: sin cambio |

Ningún test de sv4 posta lotes de varias obras.
