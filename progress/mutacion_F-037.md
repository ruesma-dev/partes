<!-- progress/mutacion_F-037.md -->
# F-037 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-037` el 2026-10-07 19:35.

## Alcance

Origen del diff: **rama** (`6e56244ac08b5565bfb18afd45e63c8d7fbb0280` .. `feature/F-037-extras-duplicadas-base-omitida`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-persistencia/application/services/pareja_extra.py` | 122 |
| `services/partes-persistencia/application/services/recurso_conciliador.py` | 14 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 121 |
| **Total** | **257** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 21 |
| Mutantes evaluados | 21 |
| Muertos | 21 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 262.7 s |
| SHA de HEAD medido | `a86fdaf9f2220c41eaf3c19b415bb77b22c5584d` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-037_8jjyr0mv/wk_0/services/partes-persistencia` | 47.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-037_8jjyr0mv/wk_1/services/partes-persistencia` | 46.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-037_8jjyr0mv/wk_2/services/partes-persistencia` | 46.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-037_8jjyr0mv/wk_3/services/partes-persistencia` | 46.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-037_8jjyr0mv/wk_4/services/partes-persistencia` | 50.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-037_8jjyr0mv/wk_5/services/partes-persistencia` | 46.5 |
| Media por mutante evaluado (s) | 12.5 |
| Timeout efectivo por mutante (s) | 600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 600 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Historia de la campaña (anotado por el implementer)

Primera campaña (HEAD `d53ae98`, 2026-10-07 19:25): 21 mutantes, 19 muertos,
**2 supervivientes**, ambos `@dataclass(frozen=True) -> frozen=False` en
`pareja_extra.py` (`FilaPareja`, línea 51, y `PlanRevert`, línea 67). Hueco
real, no equivalente: ningún test exigía que el plan fuese un valor inmutable
(se calcula y luego se aplica; nada en medio debe poder cambiarlo) ni
hashable. Matados con
`test_f037_fila_pareja_es_inmutable_y_hashable` y
`test_f037_plan_revert_es_inmutable_y_hashable` (commit `a86fdaf`). Esta
segunda campaña, completa y sin muestreo, da 0 supervivientes.
