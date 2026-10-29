<!-- progress/mutacion_F-056.md -->
# F-056 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-056` el 2026-10-29 07:12.

## Alcance

Origen del diff: **rama** (`39aef7b2870532035a8fecf72b360b010bfff0c0` .. `feature/F-056-franquicia-de-extras`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/franquicia.py` | 517 |
| `services/partes-front/infrastructure/database/orm_models.py` | 84 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 258 |
| `services/partes-front/infrastructure/transfer/transfer_client.py` | 24 |
| `services/partes-front/interface_adapters/web/app.py` | 373 |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | 84 |
| `services/partes-transfer/application/pipelines/franquicia_pipeline.py` | 375 |
| `services/partes-transfer/application/pipelines/reajuste_pipeline.py` | 5 |
| `services/partes-transfer/application/pipelines/registro_pipeline.py` | 12 |
| `services/partes-transfer/application/services/franquicia.py` | 201 |
| `services/partes-transfer/application/services/pisado.py` | 11 |
| `services/partes-transfer/config/settings.py` | 9 |
| `services/partes-transfer/domain/models/registro_models.py` | 103 |
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | 68 |
| `services/partes-transfer/interface_adapters/api/app.py` | 145 |
| `services/partes-transfer/main.py` | 25 |
| **Total** | **2294** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 513 |
| Mutantes evaluados | 513 |
| Muertos | 403 |
| Supervivientes | 102 |
| Timeouts | 8 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 57637.1 s |
| SHA de HEAD medido | `06065ea584296634daf7de5f7e442dc84b5d0946` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-056_pxbk51e_/wk_0/services/partes-front` | 824.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-056_pxbk51e_/wk_0/services/partes-persistencia` | 32.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-056_pxbk51e_/wk_0/services/partes-transfer` | 44.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-056_pxbk51e_/wk_1/services/partes-front` | 822.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-056_pxbk51e_/wk_1/services/partes-persistencia` | 33.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-056_pxbk51e_/wk_1/services/partes-transfer` | 41.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-056_pxbk51e_/wk_2/services/partes-front` | 820.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-056_pxbk51e_/wk_2/services/partes-persistencia` | 34.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-056_pxbk51e_/wk_2/services/partes-transfer` | 51.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-056_pxbk51e_/wk_3/services/partes-front` | 821.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-056_pxbk51e_/wk_3/services/partes-persistencia` | 34.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-056_pxbk51e_/wk_3/services/partes-transfer` | 45.0 |
| Media por mutante evaluado (s) | 112.4 |
| Timeout efectivo por mutante (s) | 1650 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 300 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/franquicia.py:97` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-front/application/services/franquicia.py:113` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/partes-front/application/services/franquicia.py:128` [entero]

- Original: `fi = int(valor or 0)`
- Mutado:   `fi = int(valor or 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/partes-front/application/services/franquicia.py:174` [logico]

- Original: `and bool(linea.get("obra_ide") or linea.get("obra_codigo")))`
- Mutado:   `and bool(linea.get("obra_ide") and linea.get("obra_codigo")))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/partes-front/application/services/franquicia.py:196` [entero]

- Original: `ultimo = max(int(x.get("fecha_int") or 0) for x in periodo)`
- Mutado:   `ultimo = max(int(x.get("fecha_int") or 1) for x in periodo)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/partes-front/application/services/franquicia.py:197` [entero]

- Original: `base = [x for x in periodo if int(x.get("fecha_int") or 0) == ultimo]`
- Mutado:   `base = [x for x in periodo if int(x.get("fecha_int") or 1) == ultimo]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/partes-front/application/services/franquicia.py:208` [entero]

- Original: `int(x.get("registro_id") or 0)))`
- Mutado:   `int(x.get("registro_id") or 1)))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/partes-front/application/services/franquicia.py:217` [entero]

- Original: `recursos = {int(x.get("recurso_ide") or 0) for x in lineas_periodo`
- Mutado:   `recursos = {int(x.get("recurso_ide") or 1) for x in lineas_periodo`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/partes-front/application/services/franquicia.py:233` [entero]

- Original: `and int(a.get("recurso_ide") or 0) == int(recurso_ide)`
- Mutado:   `and int(a.get("recurso_ide") or 1) == int(recurso_ide)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/partes-front/application/services/franquicia.py:235` [entero]

- Original: `and periodo.inicio_int <= int(a.get("fecha_int") or 0)`
- Mutado:   `and periodo.inicio_int <= int(a.get("fecha_int") or 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/partes-front/application/services/franquicia.py:263` [entero]

- Original: `rec = int(x.get("recurso_ide") or 0)`
- Mutado:   `rec = int(x.get("recurso_ide") or 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/partes-front/application/services/franquicia.py:336` [logico]

- Original: `dia = c.get("dia") or fecha_de_int(prop.get("fecha_int"))`
- Mutado:   `dia = c.get("dia") and fecha_de_int(prop.get("fecha_int"))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/partes-front/application/services/franquicia.py:338` [logico]

- Original: `if (prop.get("obra_ide") or prop.get("obra_codigo")) else None)`
- Mutado:   `if (prop.get("obra_ide") and prop.get("obra_codigo")) else None)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/partes-front/application/services/franquicia.py:355` [logico]

- Original: `"parte_cod": sv5.get("parte_cod") or fila.get("parte_cod"),`
- Mutado:   `"parte_cod": sv5.get("parte_cod") and fila.get("parte_cod"),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/partes-front/application/services/franquicia.py:401` [entero]

- Original: `if rec <= 0 or periodo is None:`
- Mutado:   `if rec <= 1 or periodo is None:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/partes-front/application/services/franquicia.py:459` [entero]

- Original: `"fin": periodo.fin_int, "fecha_int": int(datos.get("fecha_int") or 0),`
- Mutado:   `"fin": periodo.fin_int, "fecha_int": int(datos.get("fecha_int") or 1),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/partes-front/infrastructure/database/parte_repository.py:4071` [entero]

- Original: `"registro_id": x.id, "fecha_int": int(x.fecha_int or 0),`
- Mutado:   `"registro_id": x.id, "fecha_int": int(x.fecha_int or 1),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/partes-front/infrastructure/database/parte_repository.py:4091` [entero]

- Original: `for i in range(0, len(ids), 500):`
- Mutado:   `for i in range(0, len(ids), 501):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `services/partes-front/infrastructure/database/parte_repository.py:4096` [entero]

- Original: `.where(ParteRegistroOrm.id.in_(ids[i:i + 500]))`
- Mutado:   `.where(ParteRegistroOrm.id.in_(ids[i:i + 501]))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `services/partes-front/infrastructure/database/parte_repository.py:4101` [entero]

- Original: `return sorted((int(r), int(f or 0)) for r, f in out)`
- Mutado:   `return sorted((int(r), int(f or 1)) for r, f in out)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `services/partes-front/infrastructure/database/parte_repository.py:4156` [entero]

- Original: `"obra_ide": int(datos.get("obra_ide") or 0),`
- Mutado:   `"obra_ide": int(datos.get("obra_ide") or 1),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `services/partes-front/infrastructure/database/parte_repository.py:4164` [logico]

- Original: `and (datos.get("obra_ide") or datos.get("obra_codigo")))`
- Mutado:   `and (datos.get("obra_ide") and datos.get("obra_codigo")))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `services/partes-front/infrastructure/database/parte_repository.py:4282` [comparacion]

- Original: `if res.rowcount == 1:`
- Mutado:   `if res.rowcount != 1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 24. `services/partes-front/infrastructure/database/parte_repository.py:4282` [entero]

- Original: `if res.rowcount == 1:`
- Mutado:   `if res.rowcount == 2:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 25. `services/partes-front/infrastructure/database/parte_repository.py:4285` [not]

- Original: `f": {valores['error']}" if not ok else "")`
- Mutado:   `f": {valores['error']}" if ok else "")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 26. `services/partes-front/interface_adapters/web/app.py:2740` [entero]

- Original: `for i in range(0, len(recursos), 500):`
- Mutado:   `for i in range(0, len(recursos), 501):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 27. `services/partes-front/interface_adapters/web/app.py:2743` [entero]

- Original: `recursos[i:i + 500],`
- Mutado:   `recursos[i:i + 501],`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 28. `services/partes-front/interface_adapters/web/app.py:2746` [booleano]

- Original: `logger.warning("[franquicia] /recursos fallo", exc_info=True)`
- Mutado:   `logger.warning("[franquicia] /recursos fallo", exc_info=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 29. `services/partes-front/interface_adapters/web/app.py:2764` [comparacion]

- Original: `if x.get("candef") is not None), None)`
- Mutado:   `if x.get("candef") is None), None)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 30. `services/partes-front/interface_adapters/web/app.py:2786` [comparacion]

- Original: `[x for x in lineas_p if x["fecha_int"] == dia_int], lineas_p)`
- Mutado:   `[x for x in lineas_p if x["fecha_int"] != dia_int], lineas_p)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 31. `services/partes-front/interface_adapters/web/app.py:2815` [logico]

- Original: `if c["tipo"] in (fq.TIPO_RECHAZADO, fq.INVALIDA) or c.get("motivo"):`
- Mutado:   `if c["tipo"] in (fq.TIPO_RECHAZADO, fq.INVALIDA) and c.get("motivo"):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 32. `services/partes-front/interface_adapters/web/app.py:2835` [booleano]

- Original: `exc_info=True)`
- Mutado:   `exc_info=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 33. `services/partes-front/interface_adapters/web/app.py:2846` [entero]

- Original: `recursos = sorted({int(x.get("recurso_ide") or 0)`
- Mutado:   `recursos = sorted({int(x.get("recurso_ide") or 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 34. `services/partes-front/interface_adapters/web/app.py:2847` [entero]

- Original: `for x in lineas} - {0})`
- Mutado:   `for x in lineas} - {1})`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 35. `services/partes-front/interface_adapters/web/app.py:2854` [logico]

- Original: `if d is not None and int(x.get("recurso_ide") or 0) > 0:`
- Mutado:   `if d is not None or int(x.get("recurso_ide") or 0) > 0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 36. `services/partes-front/interface_adapters/web/app.py:2854` [entero]

- Original: `if d is not None and int(x.get("recurso_ide") or 0) > 0:`
- Mutado:   `if d is not None and int(x.get("recurso_ide") or 1) > 0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 37. `services/partes-front/interface_adapters/web/app.py:2854` [comparacion]

- Original: `if d is not None and int(x.get("recurso_ide") or 0) > 0:`
- Mutado:   `if d is not None and int(x.get("recurso_ide") or 0) >= 0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 38. `services/partes-front/interface_adapters/web/app.py:2854` [entero]

- Original: `if d is not None and int(x.get("recurso_ide") or 0) > 0:`
- Mutado:   `if d is not None and int(x.get("recurso_ide") or 0) > 1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 39. `services/partes-front/interface_adapters/web/app.py:2868` [booleano]

- Original: `exc_info=True)`
- Mutado:   `exc_info=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 40. `services/partes-front/interface_adapters/web/app.py:2888` [logico]

- Original: `if d is not None and rec:`
- Mutado:   `if d is not None or rec:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 41. `services/partes-front/interface_adapters/web/app.py:2916` [comparacion]

- Original: `if (decision == fq.AJUSTAR and datos is None`
- Mutado:   `if (decision != fq.AJUSTAR and datos is None`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 42. `services/partes-front/interface_adapters/web/app.py:2917` [not]

- Original: `and not fila.get("fecha_int")):`
- Mutado:   `and fila.get("fecha_int")):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 43. `services/partes-front/interface_adapters/web/app.py:2954` [booleano]

- Original: `respuesta = {"ok": True, "grupos": [], "franquicias": franquicias,`
- Mutado:   `respuesta = {"ok": False, "grupos": [], "franquicias": franquicias,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 44. `services/partes-front/interface_adapters/web/app.py:2955` [logico]

- Original: `"excluidas": cuerpo.get("excluidas") or {},`
- Mutado:   `"excluidas": cuerpo.get("excluidas") and {},`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 45. `services/partes-front/interface_adapters/web/app.py:2969` [logico]

- Original: `if mode != MODE_NOMINA or periodo is None or not recursos:`
- Mutado:   `if mode != MODE_NOMINA or periodo is None and not recursos:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 46. `services/partes-front/interface_adapters/web/app.py:2980` [booleano]

- Original: `exc_info=True)`
- Mutado:   `exc_info=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 47. `services/partes-front/interface_adapters/web/app.py:2983` [booleano]

- Original: `@app.post("/api/franquicia/decidir", include_in_schema=False)`
- Mutado:   `@app.post("/api/franquicia/decidir", include_in_schema=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 48. `services/partes-front/interface_adapters/web/app.py:2993` [booleano]

- Original: `{"ok": False, "error": "registro en Sigrid no configurado "`
- Mutado:   `{"ok": True, "error": "registro en Sigrid no configurado "`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 49. `services/partes-front/interface_adapters/web/app.py:3006` [entero]

- Original: `if not any(int(x.get("recurso_ide") or 0) == rec`
- Mutado:   `if not any(int(x.get("recurso_ide") or 1) == rec`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 50. `services/partes-front/interface_adapters/web/app.py:3017` [booleano]

- Original: `@app.post("/api/franquicia/{ajuste_id}/aplicar", include_in_schema=False)`
- Mutado:   `@app.post("/api/franquicia/{ajuste_id}/aplicar", include_in_schema=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 51. `services/partes-front/interface_adapters/web/app.py:3026` [booleano]

- Original: `{"ok": False, "error": "registro en Sigrid no configurado "`
- Mutado:   `{"ok": True, "error": "registro en Sigrid no configurado "`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 52. `services/partes-front/interface_adapters/web/app.py:3028` [entero]

- Original: `status_code=503)`
- Mutado:   `status_code=504)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 53. `services/partes-front/interface_adapters/web/app.py:3033` [booleano]

- Original: `{"ok": False, "error": "ajuste de franquicia no encontrado"},`
- Mutado:   `{"ok": True, "error": "ajuste de franquicia no encontrado"},`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 54. `services/partes-front/interface_adapters/web/app.py:3050` [booleano]

- Original: `exc_info=True)`
- Mutado:   `exc_info=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 55. `services/partes-front/interface_adapters/web/app.py:3051` [booleano]

- Original: `r = {"ok": False, "sin_respuesta": True, "error": str(exc)}`
- Mutado:   `r = {"ok": False, "sin_respuesta": False, "error": str(exc)}`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 56. `services/partes-front/interface_adapters/web/app.py:3059` [logico]

- Original: `"ok": ok and ajuste["estado"] == fq.APLICADO, "error": error,`
- Mutado:   `"ok": ok or ajuste["estado"] == fq.APLICADO, "error": error,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 57. `services/partes-persistencia/infrastructure/database/orm_models.py:620` [booleano]

- Original: `unique=True),`
- Mutado:   `unique=False),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 58. `services/partes-persistencia/infrastructure/database/orm_models.py:624` [booleano]

- Original: `id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)`
- Mutado:   `id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 59. `services/partes-persistencia/infrastructure/database/orm_models.py:626` [booleano]

- Original: `Integer, nullable=False, server_default="0"`
- Mutado:   `Integer, nullable=True, server_default="0"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 60. `services/partes-persistencia/infrastructure/database/orm_models.py:630` [entero]

- Original: `String(7), nullable=False, server_default=""`
- Mutado:   `String(8), nullable=False, server_default=""`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 61. `services/partes-persistencia/infrastructure/database/orm_models.py:630` [booleano]

- Original: `String(7), nullable=False, server_default=""`
- Mutado:   `String(7), nullable=True, server_default=""`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 62. `services/partes-persistencia/infrastructure/database/orm_models.py:633` [booleano]

- Original: `Integer, nullable=False, server_default="0"`
- Mutado:   `Integer, nullable=True, server_default="0"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 63. `services/partes-persistencia/infrastructure/database/orm_models.py:636` [booleano]

- Original: `Integer, nullable=False, server_default="0"`
- Mutado:   `Integer, nullable=True, server_default="0"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 64. `services/partes-persistencia/infrastructure/database/orm_models.py:638` [entero]

- Original: `obra_codigo: Mapped[str | None] = mapped_column(String(32))`
- Mutado:   `obra_codigo: Mapped[str | None] = mapped_column(String(33))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 65. `services/partes-persistencia/infrastructure/database/orm_models.py:640` [entero]

- Original: `partida_cod: Mapped[str | None] = mapped_column(String(32))`
- Mutado:   `partida_cod: Mapped[str | None] = mapped_column(String(33))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 66. `services/partes-persistencia/infrastructure/database/orm_models.py:647` [entero]

- Original: `String(16), nullable=False, server_default="decidido"`
- Mutado:   `String(17), nullable=False, server_default="decidido"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 67. `services/partes-persistencia/infrastructure/database/orm_models.py:647` [booleano]

- Original: `String(16), nullable=False, server_default="decidido"`
- Mutado:   `String(16), nullable=True, server_default="decidido"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 68. `services/partes-persistencia/infrastructure/database/orm_models.py:650` [entero]

- Original: `decision: Mapped[str | None] = mapped_column(String(16))`
- Mutado:   `decision: Mapped[str | None] = mapped_column(String(17))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 69. `services/partes-persistencia/infrastructure/database/orm_models.py:653` [entero]

- Original: `parte_cod: Mapped[str | None] = mapped_column(String(32))`
- Mutado:   `parte_cod: Mapped[str | None] = mapped_column(String(33))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 70. `services/partes-persistencia/infrastructure/database/orm_models.py:655` [entero]

- Original: `error: Mapped[str | None] = mapped_column(String(255))`
- Mutado:   `error: Mapped[str | None] = mapped_column(String(256))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 71. `services/partes-persistencia/infrastructure/database/orm_models.py:656` [entero]

- Original: `decidido_por: Mapped[str | None] = mapped_column(String(120))`
- Mutado:   `decidido_por: Mapped[str | None] = mapped_column(String(121))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 72. `services/partes-persistencia/infrastructure/database/orm_models.py:657` [entero]

- Original: `aplicado_por: Mapped[str | None] = mapped_column(String(120))`
- Mutado:   `aplicado_por: Mapped[str | None] = mapped_column(String(121))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 73. `services/partes-persistencia/infrastructure/database/orm_models.py:658` [entero]

- Original: `decidido_at_utc: Mapped[str | None] = mapped_column(String(64))`
- Mutado:   `decidido_at_utc: Mapped[str | None] = mapped_column(String(65))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 74. `services/partes-persistencia/infrastructure/database/orm_models.py:659` [entero]

- Original: `aplicado_at_utc: Mapped[str | None] = mapped_column(String(64))`
- Mutado:   `aplicado_at_utc: Mapped[str | None] = mapped_column(String(65))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 75. `services/partes-persistencia/infrastructure/database/orm_models.py:661` [entero]

- Original: `String(64), nullable=False, server_default=""`
- Mutado:   `String(65), nullable=False, server_default=""`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 76. `services/partes-persistencia/infrastructure/database/orm_models.py:661` [booleano]

- Original: `String(64), nullable=False, server_default=""`
- Mutado:   `String(64), nullable=True, server_default=""`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 77. `services/partes-persistencia/infrastructure/database/orm_models.py:664` [entero]

- Original: `String(64), nullable=False, server_default=""`
- Mutado:   `String(65), nullable=False, server_default=""`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 78. `services/partes-persistencia/infrastructure/database/orm_models.py:664` [booleano]

- Original: `String(64), nullable=False, server_default=""`
- Mutado:   `String(64), nullable=True, server_default=""`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 79. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:182` [entero]

- Original: `return int(getattr(self._st, "est_parte_activo", 1))`
- Mutado:   `return int(getattr(self._st, "est_parte_activo", 2))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 80. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:215` [entero]

- Original: `[linea.hmoide]).get(int(linea.hmoide or 0), {})`
- Mutado:   `[linea.hmoide]).get(int(linea.hmoide or 1), {})`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 81. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:235` [entero]

- Original: `hmoide = int(linea.hmoide or 0) or None`
- Mutado:   `hmoide = int(linea.hmoide or 1) or None`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 82. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:266` [logico]

- Original: `float(p.extras_pendientes or 0.0), ev.objetivo,`
- Mutado:   `float(p.extras_pendientes and 0.0), ev.objetivo,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 83. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:276` [logico]

- Original: `if not p.ajuste_id or int(p.ajuste_id) <= 0:`
- Mutado:   `if not p.ajuste_id and int(p.ajuste_id) <= 0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 84. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:276` [comparacion]

- Original: `if not p.ajuste_id or int(p.ajuste_id) <= 0:`
- Mutado:   `if not p.ajuste_id or int(p.ajuste_id) < 0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 85. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:276` [entero]

- Original: `if not p.ajuste_id or int(p.ajuste_id) <= 0:`
- Mutado:   `if not p.ajuste_id or int(p.ajuste_id) <= 1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 86. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:311` [entero]

- Original: `hmoide = int(ev.linea.hmoide or 0)`
- Mutado:   `hmoide = int(ev.linea.hmoide or 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 87. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:327` [entero]

- Original: `[tras.hmoide]).get(int(tras.hmoide or 0), {})`
- Mutado:   `[tras.hmoide]).get(int(tras.hmoide or 1), {})`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 88. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:328` [entero]

- Original: `escrita = (tras is not None and int(tras.hmoide or 0) == hmoide`
- Mutado:   `escrita = (tras is not None and int(tras.hmoide or 1) == hmoide`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 89. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:355` [logico]

- Original: `if not (p.existe and p.ide):`
- Mutado:   `if not (p.existe or p.ide):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 90. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:369` [entero]

- Original: `64))`
- Mutado:   `65))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 91. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:374` [entero]

- Original: `paride=int(a.paride or 0), ano=p.ano, mes=p.mes, synckey=sk,`
- Mutado:   `paride=int(a.paride or 1), ano=p.ano, mes=p.mes, synckey=sk,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 92. `services/partes-transfer/application/pipelines/registro_pipeline.py:991` [booleano]

- Original: `if bool(getattr(self._st, "obra_pruebas_forzar", False))`
- Mutado:   `if bool(getattr(self._st, "obra_pruebas_forzar", True))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 93. `services/partes-transfer/application/services/franquicia.py:109` [comparacion]

- Original: `if e <= 0:`
- Mutado:   `if e < 0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 94. `services/partes-transfer/application/services/franquicia.py:125` [logico]

- Original: `if isinstance(valor, bool) or not isinstance(`
- Mutado:   `if isinstance(valor, bool) and not isinstance(`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 95. `services/partes-transfer/application/services/franquicia.py:137` [comparacion]

- Original: `if x < 0 or x > MAX_FRANQUICIA_H:`
- Mutado:   `if x <= 0 or x > MAX_FRANQUICIA_H:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 96. `services/partes-transfer/application/services/franquicia.py:146` [comparacion]

- Original: `return abs(float(a or 0.0) - float(b or 0.0)) <= TOL + _RUIDO`
- Mutado:   `return abs(float(a or 0.0) - float(b or 0.0)) < TOL + _RUIDO`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 97. `services/partes-transfer/application/services/franquicia.py:146` [aritmetico]

- Original: `return abs(float(a or 0.0) - float(b or 0.0)) <= TOL + _RUIDO`
- Mutado:   `return abs(float(a or 0.0) - float(b or 0.0)) <= TOL - _RUIDO`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 98. `services/partes-transfer/application/services/franquicia.py:179` [logico]

- Original: `f"{MOTIVO_SIN_HE} (codigo {accion.hora_codigo or '-'})")`
- Mutado:   `f"{MOTIVO_SIN_HE} (codigo {accion.hora_codigo and '-'})")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 99. `services/partes-transfer/application/services/franquicia.py:193` [logico]

- Original: `f"parte {parte_cod or '?'} esta enlazada (albaran, factura, "`
- Mutado:   `f"parte {parte_cod and '?'} esta enlazada (albaran, factura, "`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 100. `services/partes-transfer/interface_adapters/api/app.py:140` [booleano]

- Original: `return False`
- Mutado:   `return True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 101. `services/partes-transfer/interface_adapters/api/app.py:152` [entero]

- Original: `recurso_ide: Annotated[int, Field(ge=1)]`
- Mutado:   `recurso_ide: Annotated[int, Field(ge=2)]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 102. `services/partes-transfer/interface_adapters/api/app.py:168` [comparacion]

- Original: `if not self.inicio <= self.fecha_int <= self.fin:`
- Mutado:   `if not self.inicio < self.fecha_int <= self.fin:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

## Timeouts

- `services/partes-front/application/services/franquicia.py:238` [entero] return round(total, 2) -> return round(total, 3)
- `services/partes-front/application/services/franquicia.py:264` [comparacion] if d is None or rec <= 0: -> if d is not None or rec <= 0:
- `services/partes-front/application/services/franquicia.py:264` [comparacion] if d is None or rec <= 0: -> if d is None or rec < 0:
- `services/partes-front/application/services/franquicia.py:264` [entero] if d is None or rec <= 0: -> if d is None or rec <= 1:
- `services/partes-front/application/services/franquicia.py:276` [entero] "dni": grupo[0].get("dni"), "nombre": grupo[0].get("nombre"), -> "dni": grupo[0].get("dni"), "nombre": grupo[1].get("nombre"),
- `services/partes-front/application/services/franquicia.py:503` [comparacion] "dia": None if dia is None else dia.isoformat(), -> "dia": None if dia is not None else dia.isoformat(),
- `services/partes-front/infrastructure/database/orm_models.py:620` [booleano] unique=True), -> unique=False),
- `services/partes-front/infrastructure/database/orm_models.py:640` [entero] partida_cod: Mapped[str | None] = mapped_column(String(32)) -> partida_cod: Mapped[str | None] = mapped_column(String(33))

