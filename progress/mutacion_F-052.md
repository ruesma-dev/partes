<!-- progress/mutacion_F-052.md -->
# F-052 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-052` el 2026-11-04 04:58.

## Alcance

Origen del diff: **rama** (`69af0f58b23c464be1b7fde3d48110517e21590f` .. `feature/F-052-sincronizar-con-sigrid`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/sincronizacion.py` | 349 |
| `services/partes-front/application/services/sincronizar_ambito.py` | 510 |
| `services/partes-front/config/settings.py` | 16 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 261 |
| `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` | 2 |
| `services/partes-front/infrastructure/transfer/transfer_client.py` | 7 |
| `services/partes-front/interface_adapters/web/app.py` | 98 |
| `services/partes-transfer/config/settings.py` | 6 |
| `services/partes-transfer/domain/models/registro_models.py` | 29 |
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | 128 |
| `services/partes-transfer/interface_adapters/api/app.py` | 82 |
| **Total** | **1488** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 331 |
| Mutantes evaluados | 331 |
| Muertos | 289 |
| Supervivientes | 42 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 31711.7 s |
| SHA de HEAD medido | `34249197b3494588921eef676bfb479b2800221d` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-052_rxs2zdl7/wk_0/services/partes-front` | 692.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-052_rxs2zdl7/wk_0/services/partes-transfer` | 29.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-052_rxs2zdl7/wk_1/services/partes-front` | 693.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-052_rxs2zdl7/wk_1/services/partes-transfer` | 29.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-052_rxs2zdl7/wk_2/services/partes-front` | 691.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-052_rxs2zdl7/wk_2/services/partes-transfer` | 30.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-052_rxs2zdl7/wk_3/services/partes-front` | 693.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-052_rxs2zdl7/wk_3/services/partes-transfer` | 29.5 |
| Media por mutante evaluado (s) | 95.8 |
| Timeout efectivo por mutante (s) | 1388 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 600 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/sincronizacion.py:72` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-front/application/services/sincronizacion.py:91` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/partes-front/application/services/sincronizacion.py:121` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/partes-front/application/services/sincronizacion.py:155` [comparacion]

- Original: `return abs(float(valor or 0.0)) <= TOLERANCIA_HORAS`
- Mutado:   `return abs(float(valor or 0.0)) < TOLERANCIA_HORAS`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/partes-front/application/services/sincronizacion.py:175` [entero]

- Original: `return (motivo or "").split(":", 1)[0].strip() or OMITIDO`
- Mutado:   `return (motivo or "").split(":", 2)[0].strip() or OMITIDO`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/partes-front/application/services/sincronizacion.py:191` [comparacion]

- Original: `if abs(float(p.horas or 0.0) - float(s.can or 0.0)) > TOLERANCIA_HORAS:`
- Mutado:   `if abs(float(p.horas or 0.0) - float(s.can or 0.0)) >= TOLERANCIA_HORAS:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/partes-front/application/services/sincronizacion.py:270` [logico]

- Original: `if s.origen == "partes" and s.registro_id is not None:`
- Mutado:   `if s.origen == "partes" or s.registro_id is not None:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/partes-front/application/services/sincronizacion.py:323` [booleano]

- Original: `texto = json.dumps(datos, sort_keys=True, separators=(",", ":"),`
- Mutado:   `texto = json.dumps(datos, sort_keys=False, separators=(",", ":"),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/partes-front/application/services/sincronizacion.py:324` [booleano]

- Original: `ensure_ascii=False, default=str)`
- Mutado:   `ensure_ascii=True, default=str)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/partes-front/application/services/sincronizar_ambito.py:81` [entero]

- Original: `if not resto.isdigit() or int(resto) <= 0:`
- Mutado:   `if not resto.isdigit() or int(resto) <= 1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/partes-front/application/services/sincronizar_ambito.py:99` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/partes-front/application/services/sincronizar_ambito.py:152` [logico]

- Original: `if not isinstance(d, dict) or d.get("origen") not in ORIGENES:`
- Mutado:   `if not isinstance(d, dict) and d.get("origen") not in ORIGENES:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/partes-front/application/services/sincronizar_ambito.py:195` [entero]

- Original: `max_items_accion: int = 500,`
- Mutado:   `max_items_accion: int = 501,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/partes-front/application/services/sincronizar_ambito.py:294` [booleano]

- Original: `it.por_confirmar = False`
- Mutado:   `it.por_confirmar = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/partes-front/application/services/sincronizar_ambito.py:335` [logico]

- Original: `and v.get("registro_id") is not None}`
- Mutado:   `or v.get("registro_id") is not None}`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/partes-front/application/services/sincronizar_ambito.py:363` [comparacion]

- Original: `if len(items) > self._max_items:`
- Mutado:   `if len(items) >= self._max_items:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/partes-front/config/settings.py:82` [entero]

- Original: `150.0, alias="SINCRONIZAR_TIMEOUT_S", gt=0, lt=230)`
- Mutado:   `150.0, alias="SINCRONIZAR_TIMEOUT_S", gt=1, lt=230)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/partes-front/config/settings.py:94` [entero]

- Original: `500, alias="SINCRONIZAR_MAX_ITEMS_ACCION", ge=1, le=5000)`
- Mutado:   `500, alias="SINCRONIZAR_MAX_ITEMS_ACCION", ge=2, le=5000)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `services/partes-front/infrastructure/database/parte_repository.py:234` [logico]

- Original: `if a is None or b is None:`
- Mutado:   `if a is None and b is None:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `services/partes-front/infrastructure/database/parte_repository.py:235` [comparacion]

- Original: `return a is None and b is None`
- Mutado:   `return a is not None and b is None`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `services/partes-front/infrastructure/database/parte_repository.py:235` [logico]

- Original: `return a is None and b is None`
- Mutado:   `return a is None or b is None`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `services/partes-front/infrastructure/database/parte_repository.py:235` [comparacion]

- Original: `return a is None and b is None`
- Mutado:   `return a is None and b is not None`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `services/partes-front/infrastructure/database/parte_repository.py:236` [comparacion]

- Original: `return abs(float(a) - float(b)) < 1e-9`
- Mutado:   `return abs(float(a) - float(b)) <= 1e-9`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 24. `services/partes-front/infrastructure/database/parte_repository.py:2767` [logico]

- Original: `and doc.deleted_at_utc is None`
- Mutado:   `or doc.deleted_at_utc is None`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 25. `services/partes-front/infrastructure/database/parte_repository.py:2789` [booleano]

- Original: `with_for_update=True)`
- Mutado:   `with_for_update=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 26. `services/partes-front/infrastructure/database/parte_repository.py:2873` [logico]

- Original: `or "sin estado")`
- Mutado:   `and "sin estado")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 27. `services/partes-front/infrastructure/database/parte_repository.py:2899` [logico]

- Original: `if recurso and reg.fecha_int:`
- Mutado:   `if recurso or reg.fecha_int:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 28. `services/partes-front/interface_adapters/web/app.py:307` [entero]

- Original: `firma: str = Field(min_length=1, max_length=64)`
- Mutado:   `firma: str = Field(min_length=2, max_length=64)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 29. `services/partes-front/interface_adapters/web/app.py:307` [entero]

- Original: `firma: str = Field(min_length=1, max_length=64)`
- Mutado:   `firma: str = Field(min_length=1, max_length=65)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 30. `services/partes-front/interface_adapters/web/app.py:3464` [booleano]

- Original: `@app.post("/api/sincronizar", include_in_schema=False)`
- Mutado:   `@app.post("/api/sincronizar", include_in_schema=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 31. `services/partes-front/interface_adapters/web/app.py:3473` [booleano]

- Original: `{"ok": False, "error": "registro en Sigrid no configurado "`
- Mutado:   `{"ok": True, "error": "registro en Sigrid no configurado "`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 32. `services/partes-front/interface_adapters/web/app.py:3479` [booleano]

- Original: `@app.post("/api/sincronizar/aplicar", include_in_schema=False)`
- Mutado:   `@app.post("/api/sincronizar/aplicar", include_in_schema=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 33. `services/partes-front/interface_adapters/web/app.py:3494` [booleano]

- Original: `{"ok": False, "error": "registro en Sigrid no configurado "`
- Mutado:   `{"ok": True, "error": "registro en Sigrid no configurado "`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 34. `services/partes-transfer/config/settings.py:37` [entero]

- Original: `3000, alias="SINCRONIZAR_MAX_REGISTRO_IDS", ge=1)`
- Mutado:   `3000, alias="SINCRONIZAR_MAX_REGISTRO_IDS", ge=2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 35. `services/partes-transfer/domain/models/registro_models.py:234` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 36. `services/partes-transfer/interface_adapters/api/app.py:211` [entero]

- Original: `obra_ide: Optional[Annotated[int, Field(ge=1)]] = None`
- Mutado:   `obra_ide: Optional[Annotated[int, Field(ge=2)]] = None`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 37. `services/partes-transfer/interface_adapters/api/app.py:212` [entero]

- Original: `recurso_ide: Optional[Annotated[int, Field(ge=1)]] = None`
- Mutado:   `recurso_ide: Optional[Annotated[int, Field(ge=2)]] = None`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 38. `services/partes-transfer/interface_adapters/api/app.py:227` [entero]

- Original: `if not 1 <= dias <= MAX_DIAS_SINCRONIZAR:`
- Mutado:   `if not 2 <= dias <= MAX_DIAS_SINCRONIZAR:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 39. `services/partes-transfer/interface_adapters/api/app.py:227` [comparacion]

- Original: `if not 1 <= dias <= MAX_DIAS_SINCRONIZAR:`
- Mutado:   `if not 1 < dias <= MAX_DIAS_SINCRONIZAR:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 40. `services/partes-transfer/interface_adapters/api/app.py:293` [comparacion]

- Original: `if lector is None:`
- Mutado:   `if lector is not None:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 41. `services/partes-transfer/interface_adapters/api/app.py:407` [booleano]

- Original: `{"ok": False, "error": f"como mucho {tope} registro_ids por "`
- Mutado:   `{"ok": True, "error": f"como mucho {tope} registro_ids por "`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 42. `services/partes-transfer/interface_adapters/api/app.py:409` [comparacion]

- Original: `ambito = "obra" if p.obra_ide is not None else "recurso"`
- Mutado:   `ambito = "obra" if p.obra_ide is None else "recurso"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

