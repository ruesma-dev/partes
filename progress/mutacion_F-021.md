<!-- progress/mutacion_F-021.md -->
# F-021 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-021` el 2026-10-01 18:02.

## Alcance

Origen del diff: **rama** (`c115f73339fb23b05feddddc71522711b908e6f2` .. `feature/F-021-cuenta-analitica-sigrid`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-transfer/application/pipelines/registro_pipeline.py` | 54 |
| `services/partes-transfer/application/services/cuenta_analitica.py` | 96 |
| `services/partes-transfer/domain/models/registro_models.py` | 13 |
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | 46 |
| `services/partes-transfer/prueba_escritura_sigrid.py` | 6 |
| **Total** | **215** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 33 |
| Mutantes evaluados | 33 |
| Muertos | 33 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 82.4 s |
| SHA de HEAD medido | `fe3af6615c35547b2ed1a6d585c785c1446b3d59` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-021_8lvr1g35/wk_0/services/partes-transfer` | 10.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-021_8lvr1g35/wk_1/services/partes-transfer` | 10.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-021_8lvr1g35/wk_2/services/partes-transfer` | 10.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-021_8lvr1g35/wk_3/services/partes-transfer` | 10.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-021_8lvr1g35/wk_4/services/partes-transfer` | 10.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-021_8lvr1g35/wk_5/services/partes-transfer` | 10.8 |
| Media por mutante evaluado (s) | 2.5 |
| Timeout efectivo por mutante (s) | 600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 600 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Historial (añadido por el implementer)

Primera pasada (commit `b038943`, informe en el commit `fe3af66`): 35
mutantes, 33 muertos, **2 supervivientes**, ambos cerrados en `37fdcbd`:

1. `registro_pipeline.py:216` `int(a.recurso_ide or 0)` → `or 1`: el
   `or 0` era código muerto (una acción `escribir` siempre trae recurso;
   las reglas omiten las que no). **Hueco real de diseño, no de test**: se
   quitó el `or 0` y el mutante deja de existir.
2. `registro_models.py:76` `defecto: bool = False` → `True`: ningún test
   fijaba el valor por defecto. **Hueco real**: si fuera `True`, cualquier
   `HoraRecurso` construida sin el campo actuaría de respaldo (R2) y
   colaría su cuenta en otro tipo de hora. Test nuevo
   `test_f021_r2_una_fila_sin_marcar_no_es_el_tipo_por_defecto`.

Esta segunda pasada (la de arriba) es la que vale: 0 supervivientes.
