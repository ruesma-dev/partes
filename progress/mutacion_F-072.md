<!-- progress/mutacion_F-072.md -->
# F-072 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-072 --workers 3` el 2026-11-23 20:22.

## Alcance

Origen del diff: **rama** (`b1fb495192c621acce268282a069e241a0d58c3f` .. `feature/F-072-postventa-var-como-obras`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/partes-api/application/services/obra_sigrid.py` | 11 | 5 |
| `services/partes-api/application/services/obras_agrupadas.py` | 265 | 68 |
| `services/partes-api/config/settings.py` | 31 | 0 — sin mutantes |
| `services/partes-api/interface_adapters/api/app.py` | 2 | 0 — sin mutantes |
| `services/partes-front/application/services/catalogo_entradas.py` | 196 | 58 |
| `services/partes-front/application/services/franquicia.py` | 36 | 11 |
| `services/partes-front/application/services/obras_agrupadas.py` | 265 | 68 |
| `services/partes-front/application/services/reparto_aviso.py` | 3 | 1 |
| `services/partes-front/application/services/sincronizar_ambito.py` | 7 | 4 |
| `services/partes-front/config/settings.py` | 27 | 0 — sin mutantes |
| `services/partes-front/infrastructure/database/parte_repository.py` | 130 | 32 |
| `services/partes-front/interface_adapters/web/app.py` | 71 | 26 |
| `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py` | 69 | 26 |
| `services/partes-persistencia/application/services/entrada_agrupada.py` | 167 | 45 |
| `services/partes-persistencia/application/services/obra_matcher.py` | 16 | 2 |
| `services/partes-persistencia/application/services/obras_agrupadas.py` | 265 | 68 |
| `services/partes-persistencia/application/services/partida_conciliador.py` | 15 | 8 |
| `services/partes-persistencia/config/settings.py` | 31 | 0 — sin mutantes |
| `services/partes-persistencia/domain/models/parte_records.py` | 19 | 1 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 44 | 11 |
| `services/partes-persistencia/interface_adapters/api/app.py` | 19 | 5 |
| `services/partes-transfer/application/pipelines/franquicia_pipeline.py` | 2 | 0 — sin mutantes |
| `services/partes-transfer/application/pipelines/reajuste_pipeline.py` | 21 | 16 |
| `services/partes-transfer/application/pipelines/registro_pipeline.py` | 83 | 28 |
| `services/partes-transfer/application/services/obras_agrupadas.py` | 265 | 68 |
| `services/partes-transfer/application/services/pisado.py` | 6 | 11 |
| `services/partes-transfer/application/services/reglas_registro.py` | 47 | 22 |
| `services/partes-transfer/config/settings.py` | 27 | 0 — sin mutantes |
| `services/partes-transfer/domain/models/registro_models.py` | 28 | 1 |
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | 30 | 19 |
| `services/partes-transfer/interface_adapters/api/app.py` | 11 | 0 — sin mutantes |
| **Total** | **2209** | **604** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 604 |
| Mutantes evaluados | 222 |
| Muertos | 178 |
| Supervivientes | 44 (todos medidos: sin mapa no se poda) |
| Timeouts | 0 |
| Indeterminados | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 22170.9 s |
| SHA de HEAD medido | `afaf5e3f89efc81980fbc4a4f908c916fbc97d39` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_3zyr2jk3/wk_0/services/partes-api` | 42.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_3zyr2jk3/wk_0/services/partes-front` | 736.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_3zyr2jk3/wk_0/services/partes-persistencia` | 47.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_3zyr2jk3/wk_0/services/partes-transfer` | 29.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_3zyr2jk3/wk_1/services/partes-api` | 42.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_3zyr2jk3/wk_1/services/partes-front` | 736.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_3zyr2jk3/wk_1/services/partes-persistencia` | 69.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_3zyr2jk3/wk_1/services/partes-transfer` | 26.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_3zyr2jk3/wk_2/services/partes-api` | 42.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_3zyr2jk3/wk_2/services/partes-front` | 743.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_3zyr2jk3/wk_2/services/partes-persistencia` | 44.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_3zyr2jk3/wk_2/services/partes-transfer` | 28.3 |
| Media por mutante evaluado (s) | 99.9 |
| Timeout efectivo por mutante (s) | 1488 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 600 |
| Workers | 3 |
| Un mutante por línea | sí — 604 generados → 370 candidatos, uno por línea |
| Muestreo | sí — 222 de 370 candidatos, semilla `20261030`, nivel `critico`; tope: 60 % de 370 candidatos, acotado a [100, 300] |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 261.3 (222 mutantes) |

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-api/application/services/obra_sigrid.py:73` [veracidad]

- Original: `if self._marcas is not None and leer_forma(codigo, self._marcas):`
- Mutado:   `if self._marcas and leer_forma(codigo, self._marcas):`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-api/application/services/obras_agrupadas.py:152` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/partes-api/application/services/obras_agrupadas.py:199` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/partes-front/application/services/catalogo_entradas.py:41` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/partes-front/application/services/catalogo_entradas.py:97` [entero]

- Original: `ajustes: Ajustes, ttl_seconds: int = 600) -> None:`
- Mutado:   `ajustes: Ajustes, ttl_seconds: int = 601) -> None:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/partes-front/application/services/catalogo_entradas.py:154` [logico]

- Original: `agrupadas.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):`
- Mutado:   `agrupadas.items(), key=lambda kv: (kv[0][0], kv[0][1] and 0)):`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/partes-front/application/services/catalogo_entradas.py:179` [logico]

- Original: `h.res or x.nombre))`
- Mutado:   `h.res and x.nombre))`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/partes-front/application/services/franquicia.py:246` [entero]

- Original: `clave = (int(out.get("recurso_ide") or 0), out.get("obra_ide"),`
- Mutado:   `clave = (int(out.get("recurso_ide") or 1), out.get("obra_ide"),`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/partes-front/application/services/franquicia.py:250` [entero]

- Original: `int(x.get("partida_ide") or 0)) == clave`
- Mutado:   `int(x.get("partida_ide") or 1)) == clave`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/partes-front/application/services/obras_agrupadas.py:152` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/partes-front/application/services/obras_agrupadas.py:199` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/partes-front/infrastructure/database/parte_repository.py:4865` [veracidad]

- Original: `if r.deleted_at_utc is None}`
- Mutado:   `if not r.deleted_at_utc}`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/partes-front/infrastructure/database/parte_repository.py:5088` [veracidad]

- Original: `if r.deleted_at_utc is None}:`
- Mutado:   `if not r.deleted_at_utc}:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/partes-front/infrastructure/database/parte_repository.py:5388` [veracidad]

- Original: `if entrada is not None:`
- Mutado:   `if entrada:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/partes-front/interface_adapters/web/app.py:2269` [veracidad]

- Original: `if entrada is None:`
- Mutado:   `if not entrada:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/partes-front/interface_adapters/web/app.py:4234` [logico]

- Original: `obra_ide_int and obra_catalog.enabled) else None`
- Mutado:   `obra_ide_int or obra_catalog.enabled) else None`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/partes-front/interface_adapters/web/app.py:4267` [logico]

- Original: `else (data.get("obra_codigo") or None,`
- Mutado:   `else (data.get("obra_codigo") and None,`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/partes-front/interface_adapters/web/app.py:4268` [logico]

- Original: `data.get("obra_nombre") or None))`
- Mutado:   `data.get("obra_nombre") and None))`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py:417` [veracidad]

- Original: `if forma is None:`
- Mutado:   `if not forma:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py:426` [veracidad]

- Original: `if tipo is not None:`
- Mutado:   `if tipo:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py:526` [veracidad]

- Original: `None if parte.entrada is None else parte.entrada.cod)`
- Mutado:   `None if not parte.entrada else parte.entrada.cod)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `services/partes-persistencia/application/services/entrada_agrupada.py:58` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `services/partes-persistencia/application/services/entrada_agrupada.py:105` [veracidad]

- Original: `if len(con_entrada) == 1 and all(r.partida is not None`
- Mutado:   `if len(con_entrada) == 1 and all(r.partida`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 24. `services/partes-persistencia/application/services/entrada_agrupada.py:124` [veracidad]

- Original: `if obra.ide is None:`
- Mutado:   `if not obra.ide:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 25. `services/partes-persistencia/application/services/entrada_agrupada.py:126` [entero]

- Original: `desde = int(self.ajustes.var_desde or 0)`
- Mutado:   `desde = int(self.ajustes.var_desde or 1)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 26. `services/partes-persistencia/application/services/entrada_agrupada.py:130` [veracidad]

- Original: `if partida is None:`
- Mutado:   `if not partida:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 27. `services/partes-persistencia/application/services/entrada_agrupada.py:140` [veracidad]

- Original: `if x.ide is None or self.ajustes.tipo_de(x.codigo) is not None:`
- Mutado:   `if not x.ide or self.ajustes.tipo_de(x.codigo) is not None:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 28. `services/partes-persistencia/application/services/entrada_agrupada.py:160` [comparacion]

- Original: `if hit is not None and (ahora - hit[0]) < self._ttl:`
- Mutado:   `if hit is not None and (ahora - hit[0]) <= self._ttl:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 29. `services/partes-persistencia/application/services/obras_agrupadas.py:125` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 30. `services/partes-persistencia/application/services/obras_agrupadas.py:152` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 31. `services/partes-persistencia/application/services/obras_agrupadas.py:178` [veracidad]

- Original: `texto = str(desde if desde is not None else "").strip()`
- Mutado:   `texto = str(desde if desde else "").strip()`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 32. `services/partes-persistencia/application/services/obras_agrupadas.py:211` [entero]

- Original: `return sorted((p for p in pares if p[0]), key=lambda p: (-len(p[0]), p))`
- Mutado:   `return sorted((p for p in pares if p[1]), key=lambda p: (-len(p[0]), p))`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 33. `services/partes-persistencia/application/services/obras_agrupadas.py:218` [entero]

- Original: `return resto[:1].isdigit()`
- Mutado:   `return resto[:2].isdigit()`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 34. `services/partes-persistencia/application/services/partida_conciliador.py:152` [veracidad]

- Original: `if (self._ajustes is not None`
- Mutado:   `if (self._ajustes`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 35. `services/partes-persistencia/domain/models/parte_records.py:125` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 36. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:1373` [veracidad]

- Original: `if entrada is None:`
- Mutado:   `if not entrada:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 37. `services/partes-transfer/application/pipelines/registro_pipeline.py:339` [veracidad]

- Original: `if agrupada is not None:`
- Mutado:   `if agrupada:`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 38. `services/partes-transfer/application/pipelines/registro_pipeline.py:696` [booleano]

- Original: `mias: set[str], por_partida: bool = False`
- Mutado:   `mias: set[str], por_partida: bool = True`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 39. `services/partes-transfer/application/services/obras_agrupadas.py:125` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 40. `services/partes-transfer/application/services/obras_agrupadas.py:218` [entero]

- Original: `return resto[:1].isdigit()`
- Mutado:   `return resto[:2].isdigit()`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 41. `services/partes-transfer/application/services/reglas_registro.py:134` [ternario]

- Original: `donde = f" de la obra {obra_cod}" if obra_cod else ""`
- Mutado:   `donde = f" de la obra {obra_cod}" if not obra_cod else ""`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 42. `services/partes-transfer/application/services/reglas_registro.py:148` [entero]

- Original: `elif tipo == VAR and not es_partida_var(hoja, int(desde or 0)):`
- Mutado:   `elif tipo == VAR and not es_partida_var(hoja, int(desde or 1)):`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 43. `services/partes-transfer/domain/models/registro_models.py:241` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 44. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:505` [entero]

- Original: `paride=(int(f.get("paride") or 0) or None) if con_partida`
- Mutado:   `paride=(int(f.get("paride") or 1) or None) if con_partida`
- Juicio: MEDIDO

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

## No muertos: código de salida

| Fichero:línea | Operador | Veredicto | Código |
|---|---|---|---|
| `services/partes-api/application/services/obra_sigrid.py:73` | veracidad | superviviente | 0 |
| `services/partes-api/application/services/obras_agrupadas.py:152` | booleano | superviviente | 0 |
| `services/partes-api/application/services/obras_agrupadas.py:199` | booleano | superviviente | 0 |
| `services/partes-front/application/services/catalogo_entradas.py:41` | booleano | superviviente | 0 |
| `services/partes-front/application/services/catalogo_entradas.py:97` | entero | superviviente | 0 |
| `services/partes-front/application/services/catalogo_entradas.py:154` | logico | superviviente | 0 |
| `services/partes-front/application/services/catalogo_entradas.py:179` | logico | superviviente | 0 |
| `services/partes-front/application/services/franquicia.py:246` | entero | superviviente | 0 |
| `services/partes-front/application/services/franquicia.py:250` | entero | superviviente | 0 |
| `services/partes-front/application/services/obras_agrupadas.py:152` | booleano | superviviente | 0 |
| `services/partes-front/application/services/obras_agrupadas.py:199` | booleano | superviviente | 0 |
| `services/partes-front/infrastructure/database/parte_repository.py:4865` | veracidad | superviviente | 0 |
| `services/partes-front/infrastructure/database/parte_repository.py:5088` | veracidad | superviviente | 0 |
| `services/partes-front/infrastructure/database/parte_repository.py:5388` | veracidad | superviviente | 0 |
| `services/partes-front/interface_adapters/web/app.py:2269` | veracidad | superviviente | 0 |
| `services/partes-front/interface_adapters/web/app.py:4234` | logico | superviviente | 0 |
| `services/partes-front/interface_adapters/web/app.py:4267` | logico | superviviente | 0 |
| `services/partes-front/interface_adapters/web/app.py:4268` | logico | superviviente | 0 |
| `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py:417` | veracidad | superviviente | 0 |
| `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py:426` | veracidad | superviviente | 0 |
| `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py:526` | veracidad | superviviente | 0 |
| `services/partes-persistencia/application/services/entrada_agrupada.py:58` | booleano | superviviente | 0 |
| `services/partes-persistencia/application/services/entrada_agrupada.py:105` | veracidad | superviviente | 0 |
| `services/partes-persistencia/application/services/entrada_agrupada.py:124` | veracidad | superviviente | 0 |
| `services/partes-persistencia/application/services/entrada_agrupada.py:126` | entero | superviviente | 0 |
| `services/partes-persistencia/application/services/entrada_agrupada.py:130` | veracidad | superviviente | 0 |
| `services/partes-persistencia/application/services/entrada_agrupada.py:140` | veracidad | superviviente | 0 |
| `services/partes-persistencia/application/services/entrada_agrupada.py:160` | comparacion | superviviente | 0 |
| `services/partes-persistencia/application/services/obras_agrupadas.py:125` | booleano | superviviente | 0 |
| `services/partes-persistencia/application/services/obras_agrupadas.py:152` | booleano | superviviente | 0 |
| `services/partes-persistencia/application/services/obras_agrupadas.py:178` | veracidad | superviviente | 0 |
| `services/partes-persistencia/application/services/obras_agrupadas.py:211` | entero | superviviente | 0 |
| `services/partes-persistencia/application/services/obras_agrupadas.py:218` | entero | superviviente | 0 |
| `services/partes-persistencia/application/services/partida_conciliador.py:152` | veracidad | superviviente | 0 |
| `services/partes-persistencia/domain/models/parte_records.py:125` | booleano | superviviente | 0 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:1373` | veracidad | superviviente | 0 |
| `services/partes-transfer/application/pipelines/registro_pipeline.py:339` | veracidad | superviviente | 0 |
| `services/partes-transfer/application/pipelines/registro_pipeline.py:696` | booleano | superviviente | 0 |
| `services/partes-transfer/application/services/obras_agrupadas.py:125` | booleano | superviviente | 0 |
| `services/partes-transfer/application/services/obras_agrupadas.py:218` | entero | superviviente | 0 |
| `services/partes-transfer/application/services/reglas_registro.py:134` | ternario | superviviente | 0 |
| `services/partes-transfer/application/services/reglas_registro.py:148` | entero | superviviente | 0 |
| `services/partes-transfer/domain/models/registro_models.py:241` | booleano | superviviente | 0 |
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:505` | entero | superviviente | 0 |

## Ficheros sin mutantes

Cada uno tiene líneas en alcance y el generador no ha sacado de ellas ni un mutante: la campaña no las ha juzgado. Declara por qué no hay nada que mutar (solo declaraciones, cadenas, imports) o qué test de la fase RED cubre el cambio. El reviewer hace la prueba de control (`generar_mutantes` sin exclusión de alcance) y ninguna declaración puede quedarse en `PENDIENTE` al cerrar la feature.

### `services/partes-api/config/settings.py` — 31 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/partes-api/interface_adapters/api/app.py` — 2 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/partes-front/config/settings.py` — 27 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/partes-persistencia/config/settings.py` — 31 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/partes-transfer/application/pipelines/franquicia_pipeline.py` — 2 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/partes-transfer/config/settings.py` — 27 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

### `services/partes-transfer/interface_adapters/api/app.py` — 11 líneas en alcance, 0 mutantes

#### Declaración (PENDIENTE del implementer)

> Por qué no hay nada que mutar, o qué test lo cubre: PENDIENTE.

