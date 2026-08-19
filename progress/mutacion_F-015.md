<!-- progress/mutacion_F-015.md -->
# F-015 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-015` el 2026-08-19 12:05.

## Alcance

Origen del diff: **rama** (`cf77e6aaa889c5fc67e25cd6f58f334695648e4f` .. `feature/F-015-jornada-semanal-candef`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/jornada_provider.py` | 161 |
| `services/partes-front/application/services/jornada_resolver.py` | 246 |
| `services/partes-front/config/settings.py` | 15 |
| `services/partes-front/infrastructure/database/orm_models.py` | 86 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 31 |
| `services/partes-front/interface_adapters/web/app.py` | 150 |
| `services/partes-persistencia/application/services/jornada_resolver.py` | 242 |
| `services/partes-persistencia/application/services/recurso_conciliador.py` | 320 |
| `services/partes-persistencia/config/settings.py` | 18 |
| `services/partes-persistencia/domain/ports/jornada_empleado_port.py` | 42 |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | 86 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_jornada_repository.py` | 73 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 49 |
| `services/partes-persistencia/interface_adapters/api/app.py` | 33 |
| **Total** | **1552** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 260 |
| Mutantes evaluados | 260 |
| Muertos | 116 |
| Supervivientes | 44 |
| Timeouts | 100 |
| Tiempo total | 1013.0 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-persistencia/application/services/jornada_resolver.py:47` [entero]

- Original: `_MAX_HORAS = 24.0 * 7`
- Mutado:   `_MAX_HORAS = 24.0 * 8`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-persistencia/application/services/jornada_resolver.py:85` [logico]

- Original: `if texto is None or not str(texto).strip():`
- Mutado:   `if texto is None and not str(texto).strip():`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/partes-persistencia/application/services/jornada_resolver.py:112` [entero]

- Original: `if not (0 < valor <= _MAX_HORAS):`
- Mutado:   `if not (1 < valor <= _MAX_HORAS):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/partes-persistencia/application/services/jornada_resolver.py:112` [comparacion]

- Original: `if not (0 < valor <= _MAX_HORAS):`
- Mutado:   `if not (0 < valor < _MAX_HORAS):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/partes-persistencia/application/services/jornada_resolver.py:139` [comparacion]

- Original: `if abs(float(clave) - c) <= _EPS:`
- Mutado:   `if abs(float(clave) - c) < _EPS:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/partes-persistencia/application/services/jornada_resolver.py:163` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/partes-persistencia/application/services/jornada_resolver.py:187` [logico]

- Original: `v is not None and 0.0 <= float(v) <= 24.0`
- Mutado:   `v is not None or 0.0 <= float(v) <= 24.0`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/partes-persistencia/application/services/jornada_resolver.py:187` [comparacion]

- Original: `v is not None and 0.0 <= float(v) <= 24.0`
- Mutado:   `v is not None and 0.0 <= float(v) < 24.0`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/partes-persistencia/application/services/jornada_resolver.py:191` [booleano]

- Original: `return False`
- Mutado:   `return True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/partes-persistencia/application/services/jornada_resolver.py:192` [comparacion]

- Original: `return 0.0 < float(self.semanal) <= _MAX_HORAS`
- Mutado:   `return 0.0 < float(self.semanal) < _MAX_HORAS`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/partes-persistencia/application/services/jornada_resolver.py:195` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/partes-persistencia/application/services/jornada_resolver.py:256` [booleano]

- Original: `return _detalle(0.0, False)`
- Mutado:   `return _detalle(0.0, True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/partes-persistencia/application/services/jornada_resolver.py:257` [comparacion]

- Original: `if d.weekday() >= 5:`
- Mutado:   `if d.weekday() > 5:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/partes-persistencia/application/services/jornada_resolver.py:257` [entero]

- Original: `if d.weekday() >= 5:`
- Mutado:   `if d.weekday() >= 6:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/partes-persistencia/application/services/jornada_resolver.py:258` [booleano]

- Original: `return _detalle(c, False)`
- Mutado:   `return _detalle(c, True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/partes-persistencia/application/services/jornada_resolver.py:261` [comparacion]

- Original: `if abs(resto - c) <= _EPS:`
- Mutado:   `if abs(resto - c) < _EPS:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/partes-persistencia/application/services/jornada_resolver.py:265` [booleano]

- Original: `return _detalle(c, False)`
- Mutado:   `return _detalle(c, True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/partes-persistencia/application/services/recurso_conciliador.py:119` [entero]

- Original: `jornada_cache_ttl_s: int = 600,`
- Mutado:   `jornada_cache_ttl_s: int = 601,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `services/partes-persistencia/application/services/recurso_conciliador.py:625` [comparacion]

- Original: `if (delta > 0 and disponible + 1e-9 < delta) or (`
- Mutado:   `if (delta >= 0 and disponible + 1e-9 < delta) or (`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `services/partes-persistencia/application/services/recurso_conciliador.py:625` [entero]

- Original: `if (delta > 0 and disponible + 1e-9 < delta) or (`
- Mutado:   `if (delta > 1 and disponible + 1e-9 < delta) or (`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `services/partes-persistencia/application/services/recurso_conciliador.py:625` [comparacion]

- Original: `if (delta > 0 and disponible + 1e-9 < delta) or (`
- Mutado:   `if (delta > 0 and disponible + 1e-9 <= delta) or (`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `services/partes-persistencia/application/services/recurso_conciliador.py:626` [comparacion]

- Original: `delta < 0 and not orden`
- Mutado:   `delta <= 0 and not orden`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `services/partes-persistencia/application/services/recurso_conciliador.py:626` [entero]

- Original: `delta < 0 and not orden`
- Mutado:   `delta < 1 and not orden`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 24. `services/partes-persistencia/application/services/recurso_conciliador.py:721` [comparacion]

- Original: `if abs(detalle.horas - detalle.candef_efectivo) <= 1e-9:`
- Mutado:   `if abs(detalle.horas - detalle.candef_efectivo) < 1e-9:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 25. `services/partes-persistencia/application/services/recurso_conciliador.py:764` [booleano]

- Original: `memo[iso] = True`
- Mutado:   `memo[iso] = False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 26. `services/partes-persistencia/application/services/recurso_conciliador.py:765` [booleano]

- Original: `return True`
- Mutado:   `return False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 27. `services/partes-persistencia/application/services/recurso_conciliador.py:773` [booleano]

- Original: `valor = True`
- Mutado:   `valor = False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 28. `services/partes-persistencia/application/services/recurso_conciliador.py:793` [comparacion]

- Original: `and (now - self._jornadas_cache[0]) < self._jornada_ttl):`
- Mutado:   `and (now - self._jornadas_cache[0]) <= self._jornada_ttl):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 29. `services/partes-persistencia/application/services/recurso_conciliador.py:799` [booleano]

- Original: `self._aviso_jornadas_fallo = True`
- Mutado:   `self._aviso_jornadas_fallo = False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 30. `services/partes-persistencia/application/services/recurso_conciliador.py:810` [aritmetico]

- Original: `ignoradas += 1`
- Mutado:   `ignoradas -= 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 31. `services/partes-persistencia/application/services/recurso_conciliador.py:810` [entero]

- Original: `ignoradas += 1`
- Mutado:   `ignoradas += 2`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 32. `services/partes-persistencia/application/services/recurso_conciliador.py:818` [aritmetico]

- Original: `ignoradas += 1`
- Mutado:   `ignoradas -= 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 33. `services/partes-persistencia/application/services/recurso_conciliador.py:818` [entero]

- Original: `ignoradas += 1`
- Mutado:   `ignoradas += 2`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 34. `services/partes-persistencia/application/services/recurso_conciliador.py:831` [logico]

- Original: `lista.sort(key=lambda f: (f.desde or ""), reverse=True)`
- Mutado:   `lista.sort(key=lambda f: (f.desde and ""), reverse=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 35. `services/partes-persistencia/application/services/recurso_conciliador.py:831` [booleano]

- Original: `lista.sort(key=lambda f: (f.desde or ""), reverse=True)`
- Mutado:   `lista.sort(key=lambda f: (f.desde or ""), reverse=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 36. `services/partes-persistencia/application/services/recurso_conciliador.py:845` [logico]

- Original: `if self._jornadas is None or not fecha_iso:`
- Mutado:   `if self._jornadas is None and not fecha_iso:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 37. `services/partes-persistencia/application/services/recurso_conciliador.py:884` [aritmetico]

- Original: `semanal=5.0 * candef_efectivo, origen="plana",`
- Mutado:   `semanal=5.0 // candef_efectivo, origen="plana",`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 38. `services/partes-persistencia/application/services/recurso_conciliador.py:885` [booleano]

- Original: `ultimo_laborable=False,`
- Mutado:   `ultimo_laborable=True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 39. `services/partes-persistencia/domain/ports/jornada_empleado_port.py:22` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 40. `services/partes-persistencia/infrastructure/database/sqlalchemy_jornada_repository.py:48` [booleano]

- Original: `EmpleadoJornadaOrm.is_active.is_(True)`
- Mutado:   `EmpleadoJornadaOrm.is_active.is_(False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 41. `services/partes-persistencia/infrastructure/database/sqlalchemy_jornada_repository.py:67` [logico]

- Original: `origen=f.origen or "manual",`
- Mutado:   `origen=f.origen and "manual",`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 42. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:251` [entero]

- Original: `congeladas = 0`
- Mutado:   `congeladas = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 43. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:254` [aritmetico]

- Original: `congeladas += 1`
- Mutado:   `congeladas -= 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 44. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:254` [entero]

- Original: `congeladas += 1`
- Mutado:   `congeladas += 2`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

## Timeouts

- `services/partes-front/application/services/jornada_provider.py:38` services/partes-front/application/services/jornada_provider.py:38 [booleano] @dataclass(frozen=True) -> @dataclass(frozen=False)
- `services/partes-front/application/services/jornada_provider.py:75` services/partes-front/application/services/jornada_provider.py:75 [logico] origen=fila.get("origen") or "manual", -> origen=fila.get("origen") and "manual",
- `services/partes-front/application/services/jornada_provider.py:90` services/partes-front/application/services/jornada_provider.py:90 [entero] ttl_seconds: int = 600, -> ttl_seconds: int = 601,
- `services/partes-front/application/services/jornada_provider.py:100` services/partes-front/application/services/jornada_provider.py:100 [booleano] self._avisado = False -> self._avisado = True
- `services/partes-front/application/services/jornada_provider.py:108` services/partes-front/application/services/jornada_provider.py:108 [not] if not clave: -> if clave:
- `services/partes-front/application/services/jornada_provider.py:112` services/partes-front/application/services/jornada_provider.py:112 [logico] if fila.desde and iso < fila.desde: -> if fila.desde or iso < fila.desde:
- `services/partes-front/application/services/jornada_provider.py:112` services/partes-front/application/services/jornada_provider.py:112 [comparacion] if fila.desde and iso < fila.desde: -> if fila.desde and iso <= fila.desde:
- `services/partes-front/application/services/jornada_provider.py:114` services/partes-front/application/services/jornada_provider.py:114 [logico] if fila.hasta and iso >= fila.hasta: -> if fila.hasta or iso >= fila.hasta:
- `services/partes-front/application/services/jornada_provider.py:114` services/partes-front/application/services/jornada_provider.py:114 [comparacion] if fila.hasta and iso >= fila.hasta: -> if fila.hasta and iso > fila.hasta:
- `services/partes-front/application/services/jornada_provider.py:123` services/partes-front/application/services/jornada_provider.py:123 [comparacion] self._ttl > 0 and (ahora - self._cache[0]) < self._ttl -> self._ttl >= 0 and (ahora - self._cache[0]) < self._ttl
- `services/partes-front/application/services/jornada_provider.py:123` services/partes-front/application/services/jornada_provider.py:123 [entero] self._ttl > 0 and (ahora - self._cache[0]) < self._ttl -> self._ttl > 1 and (ahora - self._cache[0]) < self._ttl
- `services/partes-front/application/services/jornada_provider.py:123` services/partes-front/application/services/jornada_provider.py:123 [logico] self._ttl > 0 and (ahora - self._cache[0]) < self._ttl -> self._ttl > 0 or (ahora - self._cache[0]) < self._ttl
- `services/partes-front/application/services/jornada_provider.py:123` services/partes-front/application/services/jornada_provider.py:123 [aritmetico] self._ttl > 0 and (ahora - self._cache[0]) < self._ttl -> self._ttl > 0 and (ahora + self._cache[0]) < self._ttl
- `services/partes-front/application/services/jornada_provider.py:123` services/partes-front/application/services/jornada_provider.py:123 [comparacion] self._ttl > 0 and (ahora - self._cache[0]) < self._ttl -> self._ttl > 0 and (ahora - self._cache[0]) <= self._ttl
- `services/partes-front/application/services/jornada_provider.py:129` services/partes-front/application/services/jornada_provider.py:129 [not] if not self._avisado: -> if self._avisado:
- `services/partes-front/application/services/jornada_provider.py:130` services/partes-front/application/services/jornada_provider.py:130 [booleano] self._avisado = True -> self._avisado = False
- `services/partes-front/application/services/jornada_provider.py:138` services/partes-front/application/services/jornada_provider.py:138 [booleano] self._avisado = False -> self._avisado = True
- `services/partes-front/application/services/jornada_provider.py:140` services/partes-front/application/services/jornada_provider.py:140 [entero] ignoradas = 0 -> ignoradas = 1
- `services/partes-front/application/services/jornada_provider.py:142` services/partes-front/application/services/jornada_provider.py:142 [not] if not fila.dni_norm or not _excepcion_de(fila).valida(): -> if fila.dni_norm or not _excepcion_de(fila).valida():
- `services/partes-front/application/services/jornada_provider.py:142` services/partes-front/application/services/jornada_provider.py:142 [logico] if not fila.dni_norm or not _excepcion_de(fila).valida(): -> if not fila.dni_norm and not _excepcion_de(fila).valida():
- `services/partes-front/application/services/jornada_provider.py:142` services/partes-front/application/services/jornada_provider.py:142 [not] if not fila.dni_norm or not _excepcion_de(fila).valida(): -> if not fila.dni_norm or _excepcion_de(fila).valida():
- `services/partes-front/application/services/jornada_provider.py:145` services/partes-front/application/services/jornada_provider.py:145 [aritmetico] ignoradas += 1 -> ignoradas -= 1
- `services/partes-front/application/services/jornada_provider.py:145` services/partes-front/application/services/jornada_provider.py:145 [entero] ignoradas += 1 -> ignoradas += 2
- `services/partes-front/application/services/jornada_provider.py:158` services/partes-front/application/services/jornada_provider.py:158 [logico] lista.sort(key=lambda f: (f.desde or ""), reverse=True) -> lista.sort(key=lambda f: (f.desde and ""), reverse=True)
- `services/partes-front/application/services/jornada_provider.py:158` services/partes-front/application/services/jornada_provider.py:158 [booleano] lista.sort(key=lambda f: (f.desde or ""), reverse=True) -> lista.sort(key=lambda f: (f.desde or ""), reverse=False)
- `services/partes-front/application/services/jornada_resolver.py:53` services/partes-front/application/services/jornada_resolver.py:53 [entero] _MAX_HORAS = 24.0 * 7 -> _MAX_HORAS = 24.0 * 8
- `services/partes-front/application/services/jornada_resolver.py:96` services/partes-front/application/services/jornada_resolver.py:96 [logico] if texto is None or not str(texto).strip(): -> if texto is None and not str(texto).strip():
- `services/partes-front/application/services/jornada_resolver.py:115` services/partes-front/application/services/jornada_resolver.py:115 [entero] candef = float(trozos[0].strip()) -> candef = float(trozos[1].strip())
- `services/partes-front/application/services/jornada_resolver.py:123` services/partes-front/application/services/jornada_resolver.py:123 [entero] if not (0 < valor <= _MAX_HORAS): -> if not (1 < valor <= _MAX_HORAS):
- `services/partes-front/application/services/jornada_resolver.py:123` services/partes-front/application/services/jornada_resolver.py:123 [comparacion] if not (0 < valor <= _MAX_HORAS): -> if not (0 <= valor <= _MAX_HORAS):
- `services/partes-front/application/services/jornada_resolver.py:123` services/partes-front/application/services/jornada_resolver.py:123 [comparacion] if not (0 < valor <= _MAX_HORAS): -> if not (0 < valor < _MAX_HORAS):
- `services/partes-front/application/services/jornada_resolver.py:150` services/partes-front/application/services/jornada_resolver.py:150 [aritmetico] if abs(float(clave) - c) <= _EPS: -> if abs(float(clave) + c) <= _EPS:
- `services/partes-front/application/services/jornada_resolver.py:150` services/partes-front/application/services/jornada_resolver.py:150 [comparacion] if abs(float(clave) - c) <= _EPS: -> if abs(float(clave) - c) < _EPS:
- `services/partes-front/application/services/jornada_resolver.py:152` services/partes-front/application/services/jornada_resolver.py:152 [aritmetico] return 5.0 * c, "plana" -> return 5.0 // c, "plana"
- `services/partes-front/application/services/jornada_resolver.py:164` services/partes-front/application/services/jornada_resolver.py:164 [comparacion] if dia_semana >= 5: -> if dia_semana > 5:
- `services/partes-front/application/services/jornada_resolver.py:164` services/partes-front/application/services/jornada_resolver.py:164 [entero] if dia_semana >= 5: -> if dia_semana >= 6:
- `services/partes-front/application/services/jornada_resolver.py:165` services/partes-front/application/services/jornada_resolver.py:165 [booleano] return False -> return True
- `services/partes-front/application/services/jornada_resolver.py:166` services/partes-front/application/services/jornada_resolver.py:166 [not] if not es_laborable(d): -> if es_laborable(d):
- `services/partes-front/application/services/jornada_resolver.py:167` services/partes-front/application/services/jornada_resolver.py:167 [booleano] return False -> return True
- `services/partes-front/application/services/jornada_resolver.py:168` services/partes-front/application/services/jornada_resolver.py:168 [aritmetico] for siguiente in range(dia_semana + 1, 5): -> for siguiente in range(dia_semana - 1, 5):
- `services/partes-front/application/services/jornada_resolver.py:168` services/partes-front/application/services/jornada_resolver.py:168 [entero] for siguiente in range(dia_semana + 1, 5): -> for siguiente in range(dia_semana + 2, 5):
- `services/partes-front/application/services/jornada_resolver.py:168` services/partes-front/application/services/jornada_resolver.py:168 [entero] for siguiente in range(dia_semana + 1, 5): -> for siguiente in range(dia_semana + 1, 6):
- `services/partes-front/application/services/jornada_resolver.py:169` services/partes-front/application/services/jornada_resolver.py:169 [aritmetico] if es_laborable(d + timedelta(days=siguiente - dia_semana)): -> if es_laborable(d - timedelta(days=siguiente - dia_semana)):
- `services/partes-front/application/services/jornada_resolver.py:169` services/partes-front/application/services/jornada_resolver.py:169 [aritmetico] if es_laborable(d + timedelta(days=siguiente - dia_semana)): -> if es_laborable(d + timedelta(days=siguiente + dia_semana)):
- `services/partes-front/application/services/jornada_resolver.py:170` services/partes-front/application/services/jornada_resolver.py:170 [booleano] return False -> return True
- `services/partes-front/application/services/jornada_resolver.py:171` services/partes-front/application/services/jornada_resolver.py:171 [booleano] return True -> return False
- `services/partes-front/application/services/jornada_resolver.py:174` services/partes-front/application/services/jornada_resolver.py:174 [booleano] @dataclass(frozen=True) -> @dataclass(frozen=False)
- `services/partes-front/application/services/jornada_resolver.py:195` services/partes-front/application/services/jornada_resolver.py:195 [comparacion] if len(self.patron) != 7: -> if len(self.patron) == 7:
- `services/partes-front/application/services/jornada_resolver.py:195` services/partes-front/application/services/jornada_resolver.py:195 [entero] if len(self.patron) != 7: -> if len(self.patron) != 8:
- `services/partes-front/application/services/jornada_resolver.py:196` services/partes-front/application/services/jornada_resolver.py:196 [booleano] return False -> return True
- `services/partes-front/application/services/jornada_resolver.py:198` services/partes-front/application/services/jornada_resolver.py:198 [logico] v is not None and 0.0 <= float(v) <= 24.0 -> v is not None or 0.0 <= float(v) <= 24.0
- `services/partes-front/application/services/jornada_resolver.py:198` services/partes-front/application/services/jornada_resolver.py:198 [comparacion] v is not None and 0.0 <= float(v) <= 24.0 -> v is not None and 0.0 < float(v) <= 24.0
- `services/partes-front/application/services/jornada_resolver.py:198` services/partes-front/application/services/jornada_resolver.py:198 [comparacion] v is not None and 0.0 <= float(v) <= 24.0 -> v is not None and 0.0 <= float(v) < 24.0
- `services/partes-front/application/services/jornada_resolver.py:202` services/partes-front/application/services/jornada_resolver.py:202 [booleano] return False -> return True
- `services/partes-front/application/services/jornada_resolver.py:203` services/partes-front/application/services/jornada_resolver.py:203 [comparacion] return 0.0 < float(self.semanal) <= _MAX_HORAS -> return 0.0 <= float(self.semanal) <= _MAX_HORAS
- `services/partes-front/application/services/jornada_resolver.py:203` services/partes-front/application/services/jornada_resolver.py:203 [comparacion] return 0.0 < float(self.semanal) <= _MAX_HORAS -> return 0.0 < float(self.semanal) < _MAX_HORAS
- `services/partes-front/application/services/jornada_resolver.py:206` services/partes-front/application/services/jornada_resolver.py:206 [booleano] @dataclass(frozen=True) -> @dataclass(frozen=False)
- `services/partes-front/application/services/jornada_resolver.py:252` services/partes-front/application/services/jornada_resolver.py:252 [booleano] origen="excepcion", ultimo_laborable=False, -> origen="excepcion", ultimo_laborable=True,
- `services/partes-front/application/services/jornada_resolver.py:267` services/partes-front/application/services/jornada_resolver.py:267 [booleano] return _detalle(0.0, False) -> return _detalle(0.0, True)
- `services/partes-front/application/services/jornada_resolver.py:268` services/partes-front/application/services/jornada_resolver.py:268 [comparacion] if d.weekday() >= 5: -> if d.weekday() > 5:
- `services/partes-front/application/services/jornada_resolver.py:268` services/partes-front/application/services/jornada_resolver.py:268 [entero] if d.weekday() >= 5: -> if d.weekday() >= 6:
- `services/partes-front/application/services/jornada_resolver.py:269` services/partes-front/application/services/jornada_resolver.py:269 [booleano] return _detalle(c, False) -> return _detalle(c, True)
- `services/partes-front/application/services/jornada_resolver.py:271` services/partes-front/application/services/jornada_resolver.py:271 [aritmetico] resto = max(0.0, semanal - 4.0 * c) -> resto = max(0.0, semanal + 4.0 * c)
- `services/partes-front/application/services/jornada_resolver.py:271` services/partes-front/application/services/jornada_resolver.py:271 [aritmetico] resto = max(0.0, semanal - 4.0 * c) -> resto = max(0.0, semanal - 4.0 // c)
- `services/partes-front/application/services/jornada_resolver.py:272` services/partes-front/application/services/jornada_resolver.py:272 [aritmetico] if abs(resto - c) <= _EPS: -> if abs(resto + c) <= _EPS:
- `services/partes-front/application/services/jornada_resolver.py:272` services/partes-front/application/services/jornada_resolver.py:272 [comparacion] if abs(resto - c) <= _EPS: -> if abs(resto - c) < _EPS:
- `services/partes-front/application/services/jornada_resolver.py:276` services/partes-front/application/services/jornada_resolver.py:276 [booleano] return _detalle(c, False) -> return _detalle(c, True)
- `services/partes-front/application/services/jornada_resolver.py:278` services/partes-front/application/services/jornada_resolver.py:278 [booleano] return _detalle(resto, True) -> return _detalle(resto, False)
- `services/partes-front/application/services/jornada_resolver.py:279` services/partes-front/application/services/jornada_resolver.py:279 [booleano] return _detalle(c, False) -> return _detalle(c, True)
- `services/partes-front/config/settings.py:123` services/partes-front/config/settings.py:123 [entero] jornada_cache_ttl_s: int = Field(600, alias="JORNADA_CACHE_TTL_S") -> jornada_cache_ttl_s: int = Field(601, alias="JORNADA_CACHE_TTL_S")
- `services/partes-front/infrastructure/database/orm_models.py:316` services/partes-front/infrastructure/database/orm_models.py:316 [booleano] id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) -> id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
- `services/partes-front/infrastructure/database/orm_models.py:323` services/partes-front/infrastructure/database/orm_models.py:323 [entero] String(32), nullable=False, server_default="", index=True -> String(33), nullable=False, server_default="", index=True
- `services/partes-front/infrastructure/database/orm_models.py:323` services/partes-front/infrastructure/database/orm_models.py:323 [booleano] String(32), nullable=False, server_default="", index=True -> String(32), nullable=True, server_default="", index=True
- `services/partes-front/infrastructure/database/orm_models.py:323` services/partes-front/infrastructure/database/orm_models.py:323 [booleano] String(32), nullable=False, server_default="", index=True -> String(32), nullable=False, server_default="", index=False
- `services/partes-front/infrastructure/database/orm_models.py:340` services/partes-front/infrastructure/database/orm_models.py:340 [entero] String(16), nullable=False, server_default="1900-01-01" -> String(17), nullable=False, server_default="1900-01-01"
- `services/partes-front/infrastructure/database/orm_models.py:340` services/partes-front/infrastructure/database/orm_models.py:340 [booleano] String(16), nullable=False, server_default="1900-01-01" -> String(16), nullable=True, server_default="1900-01-01"
- `services/partes-front/infrastructure/database/orm_models.py:342` services/partes-front/infrastructure/database/orm_models.py:342 [entero] hasta: Mapped[str | None] = mapped_column(String(16)) -> hasta: Mapped[str | None] = mapped_column(String(17))
- `services/partes-front/infrastructure/database/orm_models.py:346` services/partes-front/infrastructure/database/orm_models.py:346 [entero] String(16), nullable=False, default="manual", server_default="manual" -> String(17), nullable=False, default="manual", server_default="manual"
- `services/partes-front/infrastructure/database/orm_models.py:346` services/partes-front/infrastructure/database/orm_models.py:346 [booleano] String(16), nullable=False, default="manual", server_default="manual" -> String(16), nullable=True, default="manual", server_default="manual"
- `services/partes-front/infrastructure/database/orm_models.py:348` services/partes-front/infrastructure/database/orm_models.py:348 [entero] nota: Mapped[str | None] = mapped_column(String(255)) -> nota: Mapped[str | None] = mapped_column(String(256))
- `services/partes-front/infrastructure/database/orm_models.py:352` services/partes-front/infrastructure/database/orm_models.py:352 [booleano] Boolean, nullable=False, default=True, server_default="true" -> Boolean, nullable=True, default=True, server_default="true"
- `services/partes-front/infrastructure/database/orm_models.py:352` services/partes-front/infrastructure/database/orm_models.py:352 [booleano] Boolean, nullable=False, default=True, server_default="true" -> Boolean, nullable=False, default=False, server_default="true"
- `services/partes-front/infrastructure/database/orm_models.py:357` services/partes-front/infrastructure/database/orm_models.py:357 [entero] String(40), nullable=False, server_default="1970-01-01T00:00:00Z" -> String(41), nullable=False, server_default="1970-01-01T00:00:00Z"
- `services/partes-front/infrastructure/database/orm_models.py:357` services/partes-front/infrastructure/database/orm_models.py:357 [booleano] String(40), nullable=False, server_default="1970-01-01T00:00:00Z" -> String(40), nullable=True, server_default="1970-01-01T00:00:00Z"
- `services/partes-front/infrastructure/database/orm_models.py:359` services/partes-front/infrastructure/database/orm_models.py:359 [entero] created_by: Mapped[str | None] = mapped_column(String(120)) -> created_by: Mapped[str | None] = mapped_column(String(121))
- `services/partes-front/infrastructure/database/orm_models.py:360` services/partes-front/infrastructure/database/orm_models.py:360 [entero] updated_at_utc: Mapped[str | None] = mapped_column(String(40)) -> updated_at_utc: Mapped[str | None] = mapped_column(String(41))
- `services/partes-front/infrastructure/database/orm_models.py:361` services/partes-front/infrastructure/database/orm_models.py:361 [entero] updated_by: Mapped[str | None] = mapped_column(String(120)) -> updated_by: Mapped[str | None] = mapped_column(String(121))
- `services/partes-front/infrastructure/database/parte_repository.py:1805` services/partes-front/infrastructure/database/parte_repository.py:1805 [booleano] EmpleadoJornadaOrm.is_active.is_(True) -> EmpleadoJornadaOrm.is_active.is_(False)
- `services/partes-front/interface_adapters/web/app.py:638` services/partes-front/interface_adapters/web/app.py:638 [logico] if not (_day.in_period and not _day.is_weekend -> if not (_day.in_period or not _day.is_weekend
- `services/partes-front/interface_adapters/web/app.py:639` services/partes-front/interface_adapters/web/app.py:639 [logico] and not _day.is_holiday and _day.date_iso): -> or not _day.is_holiday and _day.date_iso):
- `services/partes-front/interface_adapters/web/app.py:639` services/partes-front/interface_adapters/web/app.py:639 [logico] and not _day.is_holiday and _day.date_iso): -> and not _day.is_holiday or _day.date_iso):
- `services/partes-front/interface_adapters/web/app.py:641` services/partes-front/interface_adapters/web/app.py:641 [comparacion] if 0.0 < (_day.normal_h or 0.0) < ( -> if 0.0 < (_day.normal_h or 0.0) <= (
- `services/partes-front/interface_adapters/web/app.py:642` services/partes-front/interface_adapters/web/app.py:642 [aritmetico] _jornada_de(date.fromisoformat(_day.date_iso)) - 1e-9 -> _jornada_de(date.fromisoformat(_day.date_iso)) + 1e-9
- `services/partes-front/interface_adapters/web/app.py:653` services/partes-front/interface_adapters/web/app.py:653 [logico] for _d in _w if _d.in_period and _d.date_iso), -> for _d in _w if _d.in_period or _d.date_iso),
- `services/partes-front/interface_adapters/web/app.py:661` services/partes-front/interface_adapters/web/app.py:661 [logico] _dia_kpi or date.today(), candef=_cd_real, -> _dia_kpi and date.today(), candef=_cd_real,
- `services/partes-front/interface_adapters/web/app.py:680` services/partes-front/interface_adapters/web/app.py:680 [aritmetico] else max(0.0, _detalle_kpi.semanal - 4.0 * _cd_efectivo) -> else max(0.0, _detalle_kpi.semanal + 4.0 * _cd_efectivo)
- `services/partes-front/interface_adapters/web/app.py:680` services/partes-front/interface_adapters/web/app.py:680 [aritmetico] else max(0.0, _detalle_kpi.semanal - 4.0 * _cd_efectivo) -> else max(0.0, _detalle_kpi.semanal - 4.0 // _cd_efectivo)
- `services/partes-front/interface_adapters/web/app.py:1292` services/partes-front/interface_adapters/web/app.py:1292 [entero] dia = date.fromisoformat(str(fecha)[:10]) -> dia = date.fromisoformat(str(fecha)[:11])
- `services/partes-front/interface_adapters/web/app.py:1295` services/partes-front/interface_adapters/web/app.py:1295 [booleano] {"ok": False, "error": "fecha debe ser YYYY-MM-DD", -> {"ok": True, "error": "fecha debe ser YYYY-MM-DD",
- `services/partes-front/interface_adapters/web/app.py:1343` services/partes-front/interface_adapters/web/app.py:1343 [booleano] return JSONResponse({"ok": True, "items": salida}) -> return JSONResponse({"ok": False, "items": salida})

