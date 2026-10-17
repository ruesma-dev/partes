<!-- progress/mutacion_F-046.md -->
# F-046 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-046` el 2026-10-17 04:23.

## Alcance

Origen del diff: **rama** (`dc034684d39b64ddfb505ec2afedcfd0506d171e` .. `feature/F-046-reajuste-en-sigrid-al-aprobar`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/reparto_aviso.py` | 205 |
| `services/partes-front/infrastructure/database/orm_models.py` | 78 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 358 |
| `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` | 2 |
| `services/partes-front/infrastructure/transfer/transfer_client.py` | 50 |
| `services/partes-front/interface_adapters/web/app.py` | 242 |
| `services/partes-persistencia/application/services/reajuste_reparto.py` | 129 |
| `services/partes-persistencia/application/services/recurso_conciliador.py` | 187 |
| `services/partes-persistencia/application/services/reparto_ponderado.py` | 103 |
| `services/partes-persistencia/config/settings.py` | 10 |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | 78 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 389 |
| `services/partes-persistencia/interface_adapters/api/app.py` | 4 |
| `services/partes-transfer/application/pipelines/reajuste_pipeline.py` | 352 |
| `services/partes-transfer/application/services/reajuste_lineas.py` | 132 |
| `services/partes-transfer/domain/models/registro_models.py` | 67 |
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | 190 |
| `services/partes-transfer/interface_adapters/api/app.py` | 87 |
| `services/partes-transfer/main.py` | 8 |
| **Total** | **2671** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 565 |
| Mutantes evaluados | 565 |
| Muertos | 436 |
| Supervivientes | 115 |
| Timeouts | 14 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 25666.3 s |
| SHA de HEAD medido | `6b9ceed72b31fa0d6dc81c645603bcab389368cf` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-046_6bfxsr7u/wk_0/services/partes-front` | 516.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-046_6bfxsr7u/wk_0/services/partes-persistencia` | 35.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-046_6bfxsr7u/wk_0/services/partes-transfer` | 30.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-046_6bfxsr7u/wk_1/services/partes-front` | 518.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-046_6bfxsr7u/wk_1/services/partes-persistencia` | 33.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-046_6bfxsr7u/wk_1/services/partes-transfer` | 18.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-046_6bfxsr7u/wk_2/services/partes-front` | 525.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-046_6bfxsr7u/wk_2/services/partes-persistencia` | 34.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-046_6bfxsr7u/wk_2/services/partes-transfer` | 17.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-046_6bfxsr7u/wk_3/services/partes-front` | 520.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-046_6bfxsr7u/wk_3/services/partes-persistencia` | 33.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-046_6bfxsr7u/wk_3/services/partes-transfer` | 17.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-046_6bfxsr7u/wk_4/services/partes-front` | 516.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-046_6bfxsr7u/wk_4/services/partes-persistencia` | 34.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-046_6bfxsr7u/wk_4/services/partes-transfer` | 19.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-046_6bfxsr7u/wk_5/services/partes-front` | 522.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-046_6bfxsr7u/wk_5/services/partes-persistencia` | 34.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-046_6bfxsr7u/wk_5/services/partes-transfer` | 18.4 |
| Media por mutante evaluado (s) | 45.4 |
| Timeout efectivo por mutante (s) | 1052 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/infrastructure/database/parte_repository.py:3168` [entero]

- Original: `select(func.max(ParteRegistroOrm.id))).scalar() or 0`
- Mutado:   `select(func.max(ParteRegistroOrm.id))).scalar() or 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-front/infrastructure/database/parte_repository.py:3169` [entero]

- Original: `return max([int(maximo), *(int(v) for v in ya.values())]) + 1`
- Mutado:   `return max([int(maximo), *(int(v) for v in ya.values())]) + 2`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/partes-front/infrastructure/database/parte_repository.py:3192` [logico]

- Original: `if reg is None or reg.deleted_at_utc:`
- Mutado:   `if reg is None and reg.deleted_at_utc:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/partes-front/infrastructure/database/parte_repository.py:3196` [comparacion]

- Original: `if abs(float(reg.horas or 0.0) - float(c["antes"])) > 1e-6:`
- Mutado:   `if abs(float(reg.horas or 0.0) - float(c["antes"])) >= 1e-6:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/partes-front/infrastructure/database/parte_repository.py:3199` [logico]

- Original: `f"{float(reg.horas or 0.0):g} h y el aviso decia "`
- Mutado:   `f"{float(reg.horas and 0.0):g} h y el aviso decia "`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/partes-front/infrastructure/database/parte_repository.py:3289` [entero]

- Original: `error=None if ok else ((error or "")[:255] or None),`
- Mutado:   `error=None if ok else ((error or "")[:256] or None),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/partes-front/infrastructure/database/parte_repository.py:3293` [comparacion]

- Original: `if res.rowcount != 1:`
- Mutado:   `if res.rowcount == 1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/partes-front/infrastructure/database/parte_repository.py:3293` [entero]

- Original: `if res.rowcount != 1:`
- Mutado:   `if res.rowcount != 2:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/partes-front/infrastructure/database/parte_repository.py:3297` [logico]

- Original: `nuevo, actor, f": {error}" if error and not ok else "")`
- Mutado:   `nuevo, actor, f": {error}" if error or not ok else "")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/partes-front/infrastructure/database/parte_repository.py:3297` [not]

- Original: `nuevo, actor, f": {error}" if error and not ok else "")`
- Mutado:   `nuevo, actor, f": {error}" if error and ok else "")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/partes-front/infrastructure/transfer/transfer_client.py:96` [comparacion]

- Original: `if r.status_code >= 400:`
- Mutado:   `if r.status_code > 400:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/partes-front/infrastructure/transfer/transfer_client.py:96` [entero]

- Original: `if r.status_code >= 400:`
- Mutado:   `if r.status_code >= 401:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/partes-front/infrastructure/transfer/transfer_client.py:98` [entero]

- Original: `r.text[:300])`
- Mutado:   `r.text[:301])`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/partes-front/interface_adapters/web/app.py:2378` [booleano]

- Original: `f["id"], exc_info=True)`
- Mutado:   `f["id"], exc_info=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/partes-front/interface_adapters/web/app.py:2379` [booleano]

- Original: `r = {"ok": False, "error": str(exc)}`
- Mutado:   `r = {"ok": True, "error": str(exc)}`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/partes-front/interface_adapters/web/app.py:2382` [logico]

- Original: `out[f["id"]] = {"error": r.get("error") or "sin respuesta",`
- Mutado:   `out[f["id"]] = {"error": r.get("error") and "sin respuesta",`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/partes-front/interface_adapters/web/app.py:2392` [not]

- Original: `if not bloque:`
- Mutado:   `if bloque:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/partes-front/interface_adapters/web/app.py:2430` [comparacion]

- Original: `if rechazo is not None:`
- Mutado:   `if rechazo is None:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `services/partes-front/interface_adapters/web/app.py:2436` [booleano]

- Original: `{"ok": False, "error": (`
- Mutado:   `{"ok": True, "error": (`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `services/partes-front/interface_adapters/web/app.py:2459` [booleano]

- Original: `ok, error = False, ("registro en Sigrid no configurado "`
- Mutado:   `ok, error = True, ("registro en Sigrid no configurado "`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `services/partes-front/interface_adapters/web/app.py:2467` [booleano]

- Original: `exc_info=True)`
- Mutado:   `exc_info=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `services/partes-front/interface_adapters/web/app.py:2468` [booleano]

- Original: `r = {"ok": False, "sin_respuesta": True, "error": str(exc)}`
- Mutado:   `r = {"ok": True, "sin_respuesta": True, "error": str(exc)}`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `services/partes-front/interface_adapters/web/app.py:2468` [booleano]

- Original: `r = {"ok": False, "sin_respuesta": True, "error": str(exc)}`
- Mutado:   `r = {"ok": False, "sin_respuesta": False, "error": str(exc)}`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 24. `services/partes-front/interface_adapters/web/app.py:2484` [logico]

- Original: `if not v.get("editable") and v.get("motivo"):`
- Mutado:   `if not v.get("editable") or v.get("motivo"):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 25. `services/partes-front/interface_adapters/web/app.py:2485` [logico]

- Original: `return f"{r.get('error') or 'sv5 rechazo el reajuste'}: " \`
- Mutado:   `return f"{r.get('error') and 'sv5 rechazo el reajuste'}: " \`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 26. `services/partes-front/interface_adapters/web/app.py:2496` [booleano]

- Original: `"estado": fila["estado"], "ok": True, "error": None}`
- Mutado:   `"estado": fila["estado"], "ok": False, "error": None}`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 27. `services/partes-front/interface_adapters/web/app.py:2500` [comparacion]

- Original: `if r["decision"] == DECISION_APLICAR`
- Mutado:   `if r["decision"] != DECISION_APLICAR`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 28. `services/partes-front/interface_adapters/web/app.py:2515` [booleano]

- Original: `return JSONResponse({"ok": True, "repartos": repartos, "grupos": [],`
- Mutado:   `return JSONResponse({"ok": False, "repartos": repartos, "grupos": [],`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 29. `services/partes-front/interface_adapters/web/app.py:2516` [logico]

- Original: `"excluidas": cuerpo.get("excluidas") or {},`
- Mutado:   `"excluidas": cuerpo.get("excluidas") and {},`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 30. `services/partes-persistencia/application/services/reajuste_reparto.py:66` [entero]

- Original: `if _tipo(reg) in ("", "normal") and (reg.get("horas") or 0.0) <= 0:`
- Mutado:   `if _tipo(reg) in ("", "normal") and (reg.get("horas") or 0.0) <= 1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 31. `services/partes-persistencia/application/services/reajuste_reparto.py:115` [booleano]

- Original: `return json.dumps(datos, sort_keys=True, ensure_ascii=False,`
- Mutado:   `return json.dumps(datos, sort_keys=False, ensure_ascii=False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 32. `services/partes-persistencia/application/services/reajuste_reparto.py:115` [booleano]

- Original: `return json.dumps(datos, sort_keys=True, ensure_ascii=False,`
- Mutado:   `return json.dumps(datos, sort_keys=True, ensure_ascii=True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 33. `services/partes-persistencia/application/services/recurso_conciliador.py:468` [entero]

- Original: `materializacion = {"materializados": 0, "descuadrados": 0}`
- Mutado:   `materializacion = {"materializados": 1, "descuadrados": 0}`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 34. `services/partes-persistencia/application/services/recurso_conciliador.py:468` [entero]

- Original: `materializacion = {"materializados": 0, "descuadrados": 0}`
- Mutado:   `materializacion = {"materializados": 0, "descuadrados": 1}`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 35. `services/partes-persistencia/application/services/recurso_conciliador.py:553` [entero]

- Original: `guardado = {"propuestos": 0, "mantenidos": 0}`
- Mutado:   `guardado = {"propuestos": 1, "mantenidos": 0}`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 36. `services/partes-persistencia/application/services/recurso_conciliador.py:553` [entero]

- Original: `guardado = {"propuestos": 0, "mantenidos": 0}`
- Mutado:   `guardado = {"propuestos": 0, "mantenidos": 1}`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 37. `services/partes-persistencia/application/services/recurso_conciliador.py:580` [entero]

- Original: `"repartos_propuestos": int(guardado.get("propuestos", 0)),`
- Mutado:   `"repartos_propuestos": int(guardado.get("propuestos", 1)),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 38. `services/partes-persistencia/application/services/recurso_conciliador.py:582` [entero]

- Original: `materializacion.get("materializados", 0)),`
- Mutado:   `materializacion.get("materializados", 1)),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 39. `services/partes-persistencia/application/services/recurso_conciliador.py:583` [entero]

- Original: `"repartos_mantenidos": int(guardado.get("mantenidos", 0)),`
- Mutado:   `"repartos_mantenidos": int(guardado.get("mantenidos", 1)),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 40. `services/partes-persistencia/application/services/recurso_conciliador.py:585` [entero]

- Original: `materializacion.get("descuadrados", 0)),`
- Mutado:   `materializacion.get("descuadrados", 1)),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 41. `services/partes-persistencia/application/services/recurso_conciliador.py:603` [logico]

- Original: `and clave not in self._grupos_presentes):`
- Mutado:   `or clave not in self._grupos_presentes):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 42. `services/partes-persistencia/application/services/recurso_conciliador.py:825` [booleano]

- Original: `def _lineas_dia(regs: list[dict], reajuste: bool = False`
- Mutado:   `def _lineas_dia(regs: list[dict], reajuste: bool = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 43. `services/partes-persistencia/application/services/recurso_conciliador.py:865` [logico]

- Original: `reajustable=(reajuste and clase_linea(`
- Mutado:   `reajustable=(reajuste or clase_linea(`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 44. `services/partes-persistencia/application/services/recurso_conciliador.py:899` [comparacion]

- Original: `if fila is not None:`
- Mutado:   `if fila is None:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 45. `services/partes-persistencia/application/services/reparto_ponderado.py:320` [logico]

- Original: `if ln.extra_auto and ln.base_id in ordinarias:`
- Mutado:   `if ln.extra_auto or ln.base_id in ordinarias:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 46. `services/partes-persistencia/application/services/reparto_ponderado.py:330` [comparacion]

- Original: `or (base.fija and _trabajado(base) <= 0)):`
- Mutado:   `or (base.fija and _trabajado(base) < 0)):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 47. `services/partes-persistencia/application/services/reparto_ponderado.py:354` [comparacion]

- Original: `if abs(despues - base.horas) > _EPS:`
- Mutado:   `if abs(despues - base.horas) >= _EPS:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 48. `services/partes-persistencia/application/services/reparto_ponderado.py:357` [entero]

- Original: `extra = round(trabajado - despues, 2)`
- Mutado:   `extra = round(trabajado - despues, 3)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 49. `services/partes-persistencia/application/services/reparto_ponderado.py:360` [comparacion]

- Original: `if abs(extra - actuales[0].horas) > _EPS:`
- Mutado:   `if abs(extra - actuales[0].horas) >= _EPS:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 50. `services/partes-persistencia/application/services/reparto_ponderado.py:364` [comparacion]

- Original: `elif abs(extra) > _EPS:`
- Mutado:   `elif abs(extra) >= _EPS:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 51. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:50` [entero]

- Original: `CLAVE_CANDADO_CONCILIAR = 460460001`
- Mutado:   `CLAVE_CANDADO_CONCILIAR = 460460002`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 52. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:446` [booleano]

- Original: `es_incidencia=False,`
- Mutado:   `es_incidencia=True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 53. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:550` [booleano]

- Original: `tomado = False`
- Mutado:   `tomado = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 54. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:560` [aritmetico]

- Original: `pasado = _reloj() - inicio`
- Mutado:   `pasado = _reloj() + inicio`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 55. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:623` [logico]

- Original: `if fila is None or fila.estado != REPARTO_APLICADO:`
- Mutado:   `if fila is None and fila.estado != REPARTO_APLICADO:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 56. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:624` [booleano]

- Original: `return True`
- Mutado:   `return False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 57. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:637` [entero]

- Original: `fila.error = f"descuadre al materializar: {motivo}"[:255]`
- Mutado:   `fila.error = f"descuadre al materializar: {motivo}"[:256]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 58. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:657` [booleano]

- Original: `return True`
- Mutado:   `return False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 59. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:662` [logico]

- Original: `", ".join(f"{c.get('tipo')} {c.get('registro_id') or 'nueva'} "`
- Mutado:   `", ".join(f"{c.get('tipo')} {c.get('registro_id') and 'nueva'} "`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 60. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:682` [comparacion]

- Original: `if abs(horas - despues) <= tol:`
- Mutado:   `if abs(horas - despues) < tol:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 61. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:684` [comparacion]

- Original: `if abs(horas - antes) > tol:`
- Mutado:   `if abs(horas - antes) >= tol:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 62. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:701` [logico]

- Original: `if abs(float(hecha.horas or 0.0) - despues) > tol:`
- Mutado:   `if abs(float(hecha.horas and 0.0) - despues) > tol:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 63. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:701` [aritmetico]

- Original: `if abs(float(hecha.horas or 0.0) - despues) > tol:`
- Mutado:   `if abs(float(hecha.horas or 0.0) + despues) > tol:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 64. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:701` [comparacion]

- Original: `if abs(float(hecha.horas or 0.0) - despues) > tol:`
- Mutado:   `if abs(float(hecha.horas or 0.0) - despues) >= tol:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 65. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:771` [logico]

- Original: `and f.estado == REPARTO_PENDIENTE)`
- Mutado:   `or f.estado == REPARTO_PENDIENTE)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 66. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:772` [comparacion]

- Original: `or (cambios is None and f.estado in (`
- Mutado:   `or (cambios is not None and f.estado in (`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 67. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:772` [logico]

- Original: `or (cambios is None and f.estado in (`
- Mutado:   `or (cambios is None or f.estado in (`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 68. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:818` [logico]

- Original: `rid = c.get("registro_id") or c.get("base_registro_id")`
- Mutado:   `rid = c.get("registro_id") and c.get("base_registro_id")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 69. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:99` [entero]

- Original: `return int(getattr(self._st, "est_parte_activo", 1))`
- Mutado:   `return int(getattr(self._st, "est_parte_activo", 2))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 70. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:102` [entero]

- Original: `return int(getattr(self._st, "sigrid_max_statements", 15))`
- Mutado:   `return int(getattr(self._st, "sigrid_max_statements", 16))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 71. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:105` [booleano]

- Original: `return bool(getattr(self._st, "obra_pruebas_forzar", False))`
- Mutado:   `return bool(getattr(self._st, "obra_pruebas_forzar", True))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 72. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:118` [logico]

- Original: `if not (op.fecha_int and op.recurso_ide`
- Mutado:   `if not (op.fecha_int or op.recurso_ide`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 73. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:119` [logico]

- Original: `and (op.obra_ide or op.obra_codigo)):`
- Mutado:   `or (op.obra_ide or op.obra_codigo)):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 74. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:119` [logico]

- Original: `and (op.obra_ide or op.obra_codigo)):`
- Mutado:   `and (op.obra_ide and op.obra_codigo)):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 75. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:150` [entero]

- Original: `if (int(ls.horide or 0) == int(accion.hora_ide or 0)`
- Mutado:   `if (int(ls.horide or 1) == int(accion.hora_ide or 0)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 76. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:150` [entero]

- Original: `if (int(ls.horide or 0) == int(accion.hora_ide or 0)`
- Mutado:   `if (int(ls.horide or 0) == int(accion.hora_ide or 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 77. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:151` [logico]

- Original: `and not (ls.synckey and ls.synckey in mias)):`
- Mutado:   `or not (ls.synckey and ls.synckey in mias)):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 78. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:151` [logico]

- Original: `and not (ls.synckey and ls.synckey in mias)):`
- Mutado:   `and not (ls.synckey or ls.synckey in mias)):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 79. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:168` [entero]

- Original: `est_parte = (partes.get(int(ls.hmoide or 0), {}).get("est")`
- Mutado:   `est_parte = (partes.get(int(ls.hmoide or 1), {}).get("est")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 80. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:178` [booleano]

- Original: `base_rid, editable=False, motivo=MOTIVO_SIN_BASE)`
- Mutado:   `base_rid, editable=True, motivo=MOTIVO_SIN_BASE)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 81. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:182` [entero]

- Original: `and partes.get(int(base_ls.hmoide or 0), {}).get("obride")`
- Mutado:   `and partes.get(int(base_ls.hmoide or 1), {}).get("obride")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 82. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:184` [logico]

- Original: `escribe = (p.accion is not None and p.destino is not None`
- Mutado:   `escribe = (p.accion is not None or p.destino is not None`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 83. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:185` [logico]

- Original: `and p.accion.accion == "escribir")`
- Mutado:   `or p.accion.accion == "escribir")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 84. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:209` [logico]

- Original: `ok=ok, ya_aplicada=ok and all(v.ya_aplicada`
- Mutado:   `ok=ok, ya_aplicada=ok or all(v.ya_aplicada`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 85. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:227` [not]

- Original: `no = [v for v in ev.veredictos if not v.editable]`
- Mutado:   `no = [v for v in ev.veredictos if v.editable]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 86. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:232` [entero]

- Original: `for v in no[:10]), usuario)`
- Mutado:   `for v in no[:11]), usuario)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 87. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:316` [entero]

- Original: `hmoide = int(base.hmoide or 0)`
- Mutado:   `hmoide = int(base.hmoide or 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 88. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:319` [entero]

- Original: `pos[hmoide] += int(getattr(self._st, "paso_pos", 64))`
- Mutado:   `pos[hmoide] += int(getattr(self._st, "paso_pos", 65))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 89. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:322` [logico]

- Original: `assert a is not None and p.destino is not None  # editable`
- Mutado:   `assert a is not None or p.destino is not None  # editable`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 90. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:327` [entero]

- Original: `pre=float(a.pre or 0.0), paride=int(a.paride or 0),`
- Mutado:   `pre=float(a.pre or 0.0), paride=int(a.paride or 1),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 91. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:332` [entero]

- Original: `return sentencias, [0] + [1] * (len(sentencias) - 1)`
- Mutado:   `return sentencias, [1] + [1] * (len(sentencias) - 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 92. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:332` [entero]

- Original: `return sentencias, [0] + [1] * (len(sentencias) - 1)`
- Mutado:   `return sentencias, [0] + [2] * (len(sentencias) - 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 93. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:332` [aritmetico]

- Original: `return sentencias, [0] + [1] * (len(sentencias) - 1)`
- Mutado:   `return sentencias, [0] + [1] * (len(sentencias) + 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 94. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:332` [entero]

- Original: `return sentencias, [0] + [1] * (len(sentencias) - 1)`
- Mutado:   `return sentencias, [0] + [1] * (len(sentencias) - 2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 95. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:340` [entero]

- Original: `hmoide = int(ls.hmoide or 0) if ls is not None else None`
- Mutado:   `hmoide = int(ls.hmoide or 1) if ls is not None else None`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 96. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:345` [entero]

- Original: `"parte_cod": ev.partes.get(hmoide or 0, {}).get("cod"),`
- Mutado:   `"parte_cod": ev.partes.get(hmoide or 1, {}).get("cod"),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 97. `services/partes-transfer/application/services/reajuste_lineas.py:63` [comparacion]

- Original: `return abs(float(a or 0.0) - float(b or 0.0)) <= TOL + _RUIDO`
- Mutado:   `return abs(float(a or 0.0) - float(b or 0.0)) < TOL + _RUIDO`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 98. `services/partes-transfer/domain/models/registro_models.py:351` [booleano]

- Original: `ya_aplicada: bool = False`
- Mutado:   `ya_aplicada: bool = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 99. `services/partes-transfer/domain/models/registro_models.py:355` [booleano]

- Original: `forzada_pruebas: bool = False`
- Mutado:   `forzada_pruebas: bool = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 100. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:577` [entero]

- Original: `ide=int(f["ide"]), reside=int(f["reside"] or 0),`
- Mutado:   `ide=int(f["ide"]), reside=int(f["reside"] or 1),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 101. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:578` [entero]

- Original: `fecha_int=int(f["fec"] or 0),`
- Mutado:   `fecha_int=int(f["fec"] or 1),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 102. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:579` [entero]

- Original: `horide=int(f["horide"] or 0) or None,`
- Mutado:   `horide=int(f["horide"] or 1) or None,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 103. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:583` [entero]

- Original: `hmoide=int(f["hmoide"] or 0) or None,`
- Mutado:   `hmoide=int(f["hmoide"] or 1) or None,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 104. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:605` [entero]

- Original: `"obride": int(f["obride"] or 0) or None}`
- Mutado:   `"obride": int(f["obride"] or 1) or None}`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 105. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:685` [entero]

- Original: `cenide = int(getattr(obra, "cenide", 0) or 0)`
- Mutado:   `cenide = int(getattr(obra, "cenide", 1) or 0)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 106. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:685` [entero]

- Original: `cenide = int(getattr(obra, "cenide", 0) or 0)`
- Mutado:   `cenide = int(getattr(obra, "cenide", 0) or 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 107. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:696` [entero]

- Original: `int(paride or 0), int(pos), int(fecha_int),`
- Mutado:   `int(paride or 1), int(pos), int(fecha_int),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 108. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:698` [entero]

- Original: `round(float(can) * float(pre), 2), int(ano),`
- Mutado:   `round(float(can) * float(pre), 3), int(ano),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 109. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:715` [entero]

- Original: `" ".join(st["sql"].split())[:150], st["parameters"])`
- Mutado:   `" ".join(st["sql"].split())[:151], st["parameters"])`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 110. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:717` [aritmetico]

- Original: `timeout=self._timeout + 60,`
- Mutado:   `timeout=self._timeout - 60,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 111. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:717` [entero]

- Original: `timeout=self._timeout + 60,`
- Mutado:   `timeout=self._timeout + 61,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 112. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:721` [entero]

- Original: `f"{r.text[:500]}")`
- Mutado:   `f"{r.text[:501]}")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 113. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:723` [logico]

- Original: `if not body.get("ok") or not body.get("committed"):`
- Mutado:   `if not body.get("ok") and not body.get("committed"):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 114. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:724` [entero]

- Original: `raise RuntimeError(f"escritura no confirmada: {str(body)[:400]}")`
- Mutado:   `raise RuntimeError(f"escritura no confirmada: {str(body)[:401]}")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 115. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:730` [entero]

- Original: `f"{str(body)[:400]}")`
- Mutado:   `f"{str(body)[:401]}")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

## Timeouts

- `services/partes-front/infrastructure/database/parte_repository.py:3208` [booleano] .where(ParteDocumentOrm.is_active.is_(True)) -> .where(ParteDocumentOrm.is_active.is_(False))
- `services/partes-front/infrastructure/database/parte_repository.py:3211` [comparacion] .where(ParteRegistroOrm.fecha_int == fila.fecha_int) -> .where(ParteRegistroOrm.fecha_int != fila.fecha_int)
- `services/partes-front/infrastructure/database/parte_repository.py:3213` [logico] grupo = {int(i) for i in datos.get("ids_grupo") or []} -> grupo = {int(i) for i in datos.get("ids_grupo") and []}
- `services/partes-front/infrastructure/database/parte_repository.py:3217` [logico] if r.id not in grupo and not r.extra_auto) -> if r.id not in grupo or not r.extra_auto)
- `services/partes-front/infrastructure/database/parte_repository.py:3217` [not] if r.id not in grupo and not r.extra_auto) -> if r.id not in grupo and r.extra_auto)
- `services/partes-front/infrastructure/database/parte_repository.py:3222` [aritmetico] faltan = sorted(grupo - {r.id for r in actuales}) -> faltan = sorted(grupo + {r.id for r in actuales})
- `services/partes-front/infrastructure/database/parte_repository.py:3236` [comparacion] .where(RepartoPendienteOrm.id == reparto_id, -> .where(RepartoPendienteOrm.id != reparto_id,
- `services/partes-front/infrastructure/database/parte_repository.py:3242` [booleano] .execution_options(synchronize_session=False)) -> .execution_options(synchronize_session=True))
- `services/partes-front/infrastructure/database/parte_repository.py:3243` [comparacion] if res.rowcount != 1: -> if res.rowcount == 1:
- `services/partes-front/infrastructure/database/parte_repository.py:3243` [entero] if res.rowcount != 1: -> if res.rowcount != 2:
- `services/partes-front/infrastructure/database/parte_repository.py:3249` [logico] reservas = dict(resultado.get("reservas") or {}) -> reservas = dict(resultado.get("reservas") and {})
- `services/partes-front/infrastructure/database/parte_repository.py:3250` [logico] for c in self._json(fila.cambios).get("cambios") or []: -> for c in self._json(fila.cambios).get("cambios") and []:
- `services/partes-front/infrastructure/database/parte_repository.py:3252` [comparacion] if c.get("registro_id") is None and clave not in reservas: -> if c.get("registro_id") is not None and clave not in reservas:
- `services/partes-front/infrastructure/database/parte_repository.py:3257` [comparacion] .where(RepartoPendienteOrm.id == reparto_id) -> .where(RepartoPendienteOrm.id != reparto_id)

