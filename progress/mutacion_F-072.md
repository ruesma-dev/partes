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

**Cierre de T28 (2026-11-23).** De los 44, **31 muertos** con tests nuevos, cada uno verificado a mano aplicando el mutante y deshaciéndolo. Los otros **13 se proponen como equivalentes**, pendientes de que el humano los acepte: #1, 12, 13, 14, 15, 19, 20, 21, 23, 26, 34, 36 y 37. Todos cambian `is None` por la veracidad sobre un valor que nunca es falso salvo `None`; la demostración ejecutable está en `progress/equivalentes_F-072.py`. Los 16 que el encargo señalaba como sospechosos (#6, 7, 8, 9, 16, 17, 18, 23, 25, 27, 28, 32, 33, 38, 40 y 41) se han mirado uno a uno: todos menos el #23 (`entrada_agrupada.py:105`) eran huecos reales y tienen su test. Encargo del reviewer (`casar` con los `get` intercambiados en `catalogo_entradas.py:87` y `_orden` sin `h.ide` en `:92`): mueren los dos con los casos nuevos `exacta_y_con_letras` y `con_letras_mismo_normalizado`.

### 1. `services/partes-api/application/services/obra_sigrid.py:73` [veracidad]

- Original: `if self._marcas is not None and leer_forma(codigo, self._marcas):`
- Mutado:   `if self._marcas and leer_forma(codigo, self._marcas):`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `self._marcas` es `None` o un `Marcas`, dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, así que `is None`/`is not None` y la veracidad coinciden en todo el dominio. El único productor es `Settings.obras_agrupadas.marcas` (o el `None` por defecto).
> Decisión: **equivalente propuesto; aceptación del humano pendiente**. Demostración ejecutable: `progress/equivalentes_F-072.py` (#1), exit 0 en T28.

### 2. `services/partes-api/application/services/obras_agrupadas.py:152` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `frozen=False` solo cambia la inmutabilidad (y quita el `__hash__`); ningún test asignaba un campo ni usaba el valor como clave.
> Decisión: **hueco de test**. Test añadido: `test_t28_los_valores_del_gemelo_son_inmutables` (`tests/test_f072_obras_agrupadas.py` de sv3, que sv2, sv4 y sv5 ejecutan contra su copia por `test_f072_obras_agrupadas_copia.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 3. `services/partes-api/application/services/obras_agrupadas.py:199` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `frozen=False` solo cambia la inmutabilidad (y quita el `__hash__`); ningún test asignaba un campo ni usaba el valor como clave.
> Decisión: **hueco de test**. Test añadido: `test_t28_los_valores_del_gemelo_son_inmutables` (`tests/test_f072_obras_agrupadas.py` de sv3, que sv2, sv4 y sv5 ejecutan contra su copia por `test_f072_obras_agrupadas_copia.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 4. `services/partes-front/application/services/catalogo_entradas.py:41` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `frozen=False` solo cambia la inmutabilidad (y quita el `__hash__`); ningún test asignaba un campo ni usaba el valor como clave. La `Entrada` se reparte desde la caché del catálogo.
> Decisión: **hueco de test**. Test añadido: `test_t28_la_entrada_es_inmutable` (sv4 `tests/test_f072_t28_mutantes.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 5. `services/partes-front/application/services/catalogo_entradas.py:97` [entero]

- Original: `ajustes: Ajustes, ttl_seconds: int = 600) -> None:`
- Mutado:   `ajustes: Ajustes, ttl_seconds: int = 601) -> None:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: El TTL por defecto (600 s, el del catálogo de obras) no lo comprobaba nadie: los tests pasaban `ttl` explícito y `app.py` usa el defecto.
> Decisión: **hueco de test**. Test añadido: `test_t28_el_catalogo_caduca_a_los_600_s_por_defecto` (sv4 `tests/test_f072_t28_mutantes.py`; reloj parcheado: a 599 s no relee, a 600 s sí). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 6. `services/partes-front/application/services/catalogo_entradas.py:154` [logico]

- Original: `agrupadas.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):`
- Mutado:   `agrupadas.items(), key=lambda kv: (kv[0][0], kv[0][1] and 0)):`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Los tests ordenaban las entradas antes de comparar; con `and 0` todas las empresas dan la misma clave y el orden sería el de la lista de obras.
> Decisión: **hueco de test**. Test añadido: `test_t28_las_entradas_salen_por_tipo_y_empresa` (sv4 `tests/test_f072_t28_mutantes.py`; obras al revés). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 7. `services/partes-front/application/services/catalogo_entradas.py:179` [logico]

- Original: `h.res or x.nombre))`
- Mutado:   `h.res and x.nombre))`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: En los datos de prueba el rótulo de la partida coincidía con el nombre de la obra X, así que `h.res` y `x.nombre` daban lo mismo.
> Decisión: **hueco de test**. Test añadido: `test_t28_el_nombre_de_postventa_es_el_de_la_partida_o_el_de_la_obra` (sv4 `tests/test_f072_t28_mutantes.py`; rótulo distinto y partida sin rótulo). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 8. `services/partes-front/application/services/franquicia.py:246` [entero]

- Original: `clave = (int(out.get("recurso_ide") or 0), out.get("obra_ide"),`
- Mutado:   `clave = (int(out.get("recurso_ide") or 1), out.get("obra_ide"),`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Ningún test tenía una fila sin recurso: con `or 1` sería «del recurso 1» y tomaría su marca.
> Decisión: **hueco de test**. Test añadido: `test_t28_con_metodo_base_sin_recurso_no_toma_la_marca_del_recurso_1` (sv4 `tests/test_f072_t28_mutantes.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 9. `services/partes-front/application/services/franquicia.py:250` [entero]

- Original: `int(x.get("partida_ide") or 0)) == clave`
- Mutado:   `int(x.get("partida_ide") or 1)) == clave`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Ninguna línea sin partida frente a una fila de la partida 1: con `or 1` casaría.
> Decisión: **hueco de test**. Test añadido: `test_t28_con_metodo_base_una_linea_sin_partida_no_es_la_partida_1` (sv4 `tests/test_f072_t28_mutantes.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 10. `services/partes-front/application/services/obras_agrupadas.py:152` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `frozen=False` solo cambia la inmutabilidad (y quita el `__hash__`); ningún test asignaba un campo ni usaba el valor como clave.
> Decisión: **hueco de test**. Test añadido: `test_t28_los_valores_del_gemelo_son_inmutables` (`tests/test_f072_obras_agrupadas.py` de sv3, que sv2, sv4 y sv5 ejecutan contra su copia por `test_f072_obras_agrupadas_copia.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 11. `services/partes-front/application/services/obras_agrupadas.py:199` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `frozen=False` solo cambia la inmutabilidad (y quita el `__hash__`); ningún test asignaba un campo ni usaba el valor como clave.
> Decisión: **hueco de test**. Test añadido: `test_t28_los_valores_del_gemelo_son_inmutables` (`tests/test_f072_obras_agrupadas.py` de sv3, que sv2, sv4 y sv5 ejecutan contra su copia por `test_f072_obras_agrupadas_copia.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 12. `services/partes-front/infrastructure/database/parte_repository.py:4865` [veracidad]

- Original: `if r.deleted_at_utc is None}`
- Mutado:   `if not r.deleted_at_utc}`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `deleted_at_utc` solo vale `None` o un `datetime.now(timezone.utc).isoformat()` (nunca vacío): las escrituras del código de los cinco servicios son `None`, `now_iso` y `ahora` (los dos, `isoformat()`) o la copia `doc.deleted_at_utc`. La cadena vacía no se escribe nunca, así que `is None` y `not` coinciden. sv3 ya lo lee por veracidad (`if reg.get("deleted_at_utc")`).
> Decisión: **equivalente propuesto; aceptación del humano pendiente**. Demostración ejecutable: `progress/equivalentes_F-072.py` (#12), exit 0 en T28.

### 13. `services/partes-front/infrastructure/database/parte_repository.py:5088` [veracidad]

- Original: `if r.deleted_at_utc is None}:`
- Mutado:   `if not r.deleted_at_utc}:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Mismo argumento que el #12 (la misma expresión, en `borrar_obra`).
> Decisión: **equivalente propuesto; aceptación del humano pendiente**. Demostración ejecutable: `progress/equivalentes_F-072.py` (#13), exit 0 en T28.

### 14. `services/partes-front/infrastructure/database/parte_repository.py:5388` [veracidad]

- Original: `if entrada is not None:`
- Mutado:   `if entrada:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `entrada` es `None` o un `Entrada`, dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, así que `is None`/`is not None` y la veracidad coinciden en todo el dominio. Su único llamador, `/api/partes/nuevo`, pasa `entrada` solo si no es `None`, y viene de `CatalogoEntradas.entrada`.
> Decisión: **equivalente propuesto; aceptación del humano pendiente**. Demostración ejecutable: `progress/equivalentes_F-072.py` (#14), exit 0 en T28.

### 15. `services/partes-front/interface_adapters/web/app.py:2269` [veracidad]

- Original: `if entrada is None:`
- Mutado:   `if not entrada:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `entrada` es `None` o un `Entrada`, dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, así que `is None`/`is not None` y la veracidad coinciden en todo el dominio. Viene de `CatalogoEntradas.entrada`, que da un `Entrada` o `None`.
> Decisión: **equivalente propuesto; aceptación del humano pendiente**. Demostración ejecutable: `progress/equivalentes_F-072.py` (#15), exit 0 en T28.

### 16. `services/partes-front/interface_adapters/web/app.py:4234` [logico]

- Original: `obra_ide_int and obra_catalog.enabled) else None`
- Mutado:   `obra_ide_int or obra_catalog.enabled) else None`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Solo se distingue con `obra_ide` 0 y una obra de `ide` 0 en el catálogo (con el catálogo apagado `get_by_ide` da `None` igual); ningún test lo combinaba. `obra_ide` 0 es «sin obra», como en el casado de partida del mismo endpoint.
> Decisión: **hueco de test**. Test añadido: `test_t28_parte_nuevo_obra_ide_0_no_es_una_obra_del_catalogo` (sv4 `tests/test_f072_t28_mutantes.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 17. `services/partes-front/interface_adapters/web/app.py:4267` [logico]

- Original: `else (data.get("obra_codigo") or None,`
- Mutado:   `else (data.get("obra_codigo") and None,`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Ningún test miraba el código de obra guardado al crear un parte nuevo en una obra normal: con `and None` quedaría vacío.
> Decisión: **hueco de test**. Test añadido: `test_t28_parte_nuevo_en_obra_normal_guarda_su_codigo_y_nombre` (sv4 `tests/test_f072_t28_mutantes.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 18. `services/partes-front/interface_adapters/web/app.py:4268` [logico]

- Original: `data.get("obra_nombre") or None))`
- Mutado:   `data.get("obra_nombre") and None))`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Igual que el #17, con el nombre de la obra.
> Decisión: **hueco de test**. Test añadido: `test_t28_parte_nuevo_en_obra_normal_guarda_su_codigo_y_nombre` (sv4 `tests/test_f072_t28_mutantes.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 19. `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py:417` [veracidad]

- Original: `if forma is None:`
- Mutado:   `if not forma:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `forma` es `None` o un `Forma`, dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, así que `is None`/`is not None` y la veracidad coinciden en todo el dominio. `_forma` devuelve `leer_forma(...)` (un `Forma` o `None`) o `None`.
> Decisión: **equivalente propuesto; aceptación del humano pendiente**. Demostración ejecutable: `progress/equivalentes_F-072.py` (#19), exit 0 en T28.

### 20. `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py:426` [veracidad]

- Original: `if tipo is not None:`
- Mutado:   `if tipo:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `tipo` sale de `Ajustes.tipo_de` (o es `None`), que solo da `POSTVENTA` (`"postventa"`), `VAR` (`"var"`) o `None`: nunca una cadena vacía. El script lo recorre con 2.000 códigos al azar y los bordes.
> Decisión: **equivalente propuesto; aceptación del humano pendiente**. Demostración ejecutable: `progress/equivalentes_F-072.py` (#20), exit 0 en T28.

### 21. `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py:526` [veracidad]

- Original: `None if parte.entrada is None else parte.entrada.cod)`
- Mutado:   `None if not parte.entrada else parte.entrada.cod)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `parte.entrada` es `None` o un `EntradaPartida`, dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, así que `is None`/`is not None` y la veracidad coinciden en todo el dominio. Además, la línea solo forma el mensaje de un `logger.info`.
> Decisión: **equivalente propuesto; aceptación del humano pendiente**. Demostración ejecutable: `progress/equivalentes_F-072.py` (#21), exit 0 en T28.

### 22. `services/partes-persistencia/application/services/entrada_agrupada.py:58` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `frozen=False` solo cambia la inmutabilidad (y quita el `__hash__`); ningún test asignaba un campo ni usaba el valor como clave.
> Decisión: **hueco de test**. Test añadido: `test_t28_los_valores_de_la_entrada_son_inmutables` (sv3 `tests/test_f072_t28_mutantes.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 23. `services/partes-persistencia/application/services/entrada_agrupada.py:105` [veracidad]

- Original: `if len(con_entrada) == 1 and all(r.partida is not None`
- Mutado:   `if len(con_entrada) == 1 and all(r.partida`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `r.partida` es `None` o un `PartidaNodo`, dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, así que `is None`/`is not None` y la veracidad coinciden en todo el dominio. Los `ResultadoEntrada` con partida la toman de `casar_var`/`casar_postventa` sobre nodos de `build_arbol_partidas`.
> Decisión: **equivalente propuesto; aceptación del humano pendiente**. Demostración ejecutable: `progress/equivalentes_F-072.py` (#23), exit 0 en T28.

### 24. `services/partes-persistencia/application/services/entrada_agrupada.py:124` [veracidad]

- Original: `if obra.ide is None:`
- Mutado:   `if not obra.ide:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Ningún test tenía una obra VAR con `ide` 0: con `not` sería «sin obra». Solo `None` es «sin obra».
> Decisión: **hueco de test**. Test añadido: `test_t28_var_un_ide_0_es_una_obra_solo_none_es_sin_obra` (sv3 `tests/test_f072_t28_mutantes.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 25. `services/partes-persistencia/application/services/entrada_agrupada.py:126` [entero]

- Original: `desde = int(self.ajustes.var_desde or 0)`
- Mutado:   `desde = int(self.ajustes.var_desde or 1)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Con `VAR_PARTIDA_DESDE=0` (válido por R2) la partida de número 0 es del universo; con `or 1`, no. Ningún test usaba umbral 0.
> Decisión: **hueco de test**. Test añadido: `test_t28_var_desde_0_admite_la_partida_0` (sv3 `tests/test_f072_t28_mutantes.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 26. `services/partes-persistencia/application/services/entrada_agrupada.py:130` [veracidad]

- Original: `if partida is None:`
- Mutado:   `if not partida:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `partida` es `None` o un `PartidaNodo`, dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, así que `is None`/`is not None` y la veracidad coinciden en todo el dominio. `casar_var` devuelve un elemento del universo (nodos de `build_arbol_partidas`) o `None`.
> Decisión: **equivalente propuesto; aceptación del humano pendiente**. Demostración ejecutable: `progress/equivalentes_F-072.py` (#26), exit 0 en T28.

### 27. `services/partes-persistencia/application/services/entrada_agrupada.py:140` [veracidad]

- Original: `if x.ide is None or self.ajustes.tipo_de(x.codigo) is not None:`
- Mutado:   `if not x.ide or self.ajustes.tipo_de(x.codigo) is not None:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Como el #24, con la obra X de postventa de `ide` 0.
> Decisión: **hueco de test**. Test añadido: `test_t28_postventa_la_obra_x_con_ide_0_casa` (sv3 `tests/test_f072_t28_mutantes.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 28. `services/partes-persistencia/application/services/entrada_agrupada.py:160` [comparacion]

- Original: `if hit is not None and (ahora - hit[0]) < self._ttl:`
- Mutado:   `if hit is not None and (ahora - hit[0]) <= self._ttl:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: La frontera del TTL (`<` frente a `<=`) no la miraba nadie: el test de caché usa `ttl=0` y el reloj real.
> Decisión: **hueco de test**. Test añadido: `test_t28_el_presupuesto_caduca_justo_al_cumplir_el_ttl` (sv3 `tests/test_f072_t28_mutantes.py`; reloj parcheado: a 600 s justos relee). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 29. `services/partes-persistencia/application/services/obras_agrupadas.py:125` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `frozen=False` solo cambia la inmutabilidad (y quita el `__hash__`); ningún test asignaba un campo ni usaba el valor como clave.
> Decisión: **hueco de test**. Test añadido: `test_t28_los_valores_del_gemelo_son_inmutables` (`tests/test_f072_obras_agrupadas.py` de sv3, que sv2, sv4 y sv5 ejecutan contra su copia por `test_f072_obras_agrupadas_copia.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 30. `services/partes-persistencia/application/services/obras_agrupadas.py:152` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `frozen=False` solo cambia la inmutabilidad (y quita el `__hash__`); ningún test asignaba un campo ni usaba el valor como clave.
> Decisión: **hueco de test**. Test añadido: `test_t28_los_valores_del_gemelo_son_inmutables` (`tests/test_f072_obras_agrupadas.py` de sv3, que sv2, sv4 y sv5 ejecutan contra su copia por `test_f072_obras_agrupadas_copia.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 31. `services/partes-persistencia/application/services/obras_agrupadas.py:178` [veracidad]

- Original: `texto = str(desde if desde is not None else "").strip()`
- Mutado:   `texto = str(desde if desde else "").strip()`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `var_desde=0` entero (no cadena) daría `""` y `ValueError` con el mutante; los tests solo pasaban cadenas.
> Decisión: **hueco de test**. Test añadido: `test_t28_var_desde_admite_el_entero_0` (`tests/test_f072_obras_agrupadas.py` de sv3, que sv2, sv4 y sv5 ejecutan contra su copia por `test_f072_obras_agrupadas_copia.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 32. `services/partes-persistencia/application/services/obras_agrupadas.py:211` [entero]

- Original: `return sorted((p for p in pares if p[0]), key=lambda p: (-len(p[0]), p))`
- Mutado:   `return sorted((p for p in pares if p[1]), key=lambda p: (-len(p[0]), p))`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: NO es equivalente: `p[1]` es el tipo (siempre verdadero), así que el mutante deja pasar una marca cuya clave es vacía, p. ej. un alias `-`. Esa marca vacía casa cualquier código (`0578` → postventa). Ningún test configuraba un alias que fuese solo separadores.
> Decisión: **hueco de test**. Test añadido: `test_t28_una_marca_que_es_solo_separadores_no_cuenta` (`tests/test_f072_obras_agrupadas.py` de sv3, que sv2, sv4 y sv5 ejecutan contra su copia por `test_f072_obras_agrupadas_copia.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 33. `services/partes-persistencia/application/services/obras_agrupadas.py:218` [entero]

- Original: `return resto[:1].isdigit()`
- Mutado:   `return resto[:2].isdigit()`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: NO es equivalente: con `[:2]` un resto que empieza por dígito seguido de otro carácter (`2.1`, `5B`) deja de valer. Los casos de prueba tenían siempre dos dígitos delante (`29A`, `0578B`).
> Decisión: **hueco de test**. Test añadido: `test_t28_r41_basta_con_que_el_resto_empiece_por_digito` (`tests/test_f072_obras_agrupadas.py` de sv3, que sv2, sv4 y sv5 ejecutan contra su copia por `test_f072_obras_agrupadas_copia.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 34. `services/partes-persistencia/application/services/partida_conciliador.py:152` [veracidad]

- Original: `if (self._ajustes is not None`
- Mutado:   `if (self._ajustes`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `self._ajustes` es `None` o un `Ajustes`, dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, así que `is None`/`is not None` y la veracidad coinciden en todo el dominio. Lo pasa `app.py` con `settings.obras_agrupadas`, o es el `None` por defecto (como antes de F-072). `Ajustes.activo` es una propiedad, no `__bool__`.
> Decisión: **equivalente propuesto; aceptación del humano pendiente**. Demostración ejecutable: `progress/equivalentes_F-072.py` (#34), exit 0 en T28.

### 35. `services/partes-persistencia/domain/models/parte_records.py:125` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `frozen=False` solo cambia la inmutabilidad (y quita el `__hash__`); ningún test asignaba un campo ni usaba el valor como clave.
> Decisión: **hueco de test**. Test añadido: `test_t28_los_valores_de_la_entrada_son_inmutables` (sv3 `tests/test_f072_t28_mutantes.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 36. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:1373` [veracidad]

- Original: `if entrada is None:`
- Mutado:   `if not entrada:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `entrada` es `None` o un `EntradaPartida`, dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, así que `is None`/`is not None` y la veracidad coinciden en todo el dominio. `_campos_entrada` recibe `parte.entrada`, que solo escribe `_casar_entrada` con un `EntradaPartida` o `None`.
> Decisión: **equivalente propuesto; aceptación del humano pendiente**. Demostración ejecutable: `progress/equivalentes_F-072.py` (#36), exit 0 en T28.

### 37. `services/partes-transfer/application/pipelines/registro_pipeline.py:339` [veracidad]

- Original: `if agrupada is not None:`
- Mutado:   `if agrupada:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `agrupada` es `None` o la tupla `(tipo, origen)` de `_obra_agrupada` (2 elementos: siempre verdadera).
> Decisión: **equivalente propuesto; aceptación del humano pendiente**. Demostración ejecutable: `progress/equivalentes_F-072.py` (#37), exit 0 en T28.

### 38. `services/partes-transfer/application/pipelines/registro_pipeline.py:696` [booleano]

- Original: `mias: set[str], por_partida: bool = False`
- Mutado:   `mias: set[str], por_partida: bool = True`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: NO es equivalente para quien llame sin el argumento. Todos los llamadores de producción pasan `por_partida` explícito; el defecto solo lo usan los tests antiguos, con líneas sin partida (iguales con y sin el filtro). Ningún test comprobaba que el defecto sigue siendo el de antes de F-072 (no mirar la partida).
> Decisión: **hueco de test**. Test añadido: `test_t28_choques_sin_por_partida_no_mira_la_partida` (sv5 `tests/test_f072_t28_mutantes.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 39. `services/partes-transfer/application/services/obras_agrupadas.py:125` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `frozen=False` solo cambia la inmutabilidad (y quita el `__hash__`); ningún test asignaba un campo ni usaba el valor como clave.
> Decisión: **hueco de test**. Test añadido: `test_t28_los_valores_del_gemelo_son_inmutables` (`tests/test_f072_obras_agrupadas.py` de sv3, que sv2, sv4 y sv5 ejecutan contra su copia por `test_f072_obras_agrupadas_copia.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 40. `services/partes-transfer/application/services/obras_agrupadas.py:218` [entero]

- Original: `return resto[:1].isdigit()`
- Mutado:   `return resto[:2].isdigit()`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Igual que el #33 (copia de sv5).
> Decisión: **hueco de test**. Test añadido: `test_t28_r41_basta_con_que_el_resto_empiece_por_digito` (`tests/test_f072_obras_agrupadas.py` de sv3, que sv2, sv4 y sv5 ejecutan contra su copia por `test_f072_obras_agrupadas_copia.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 41. `services/partes-transfer/application/services/reglas_registro.py:134` [ternario]

- Original: `donde = f" de la obra {obra_cod}" if obra_cod else ""`
- Mutado:   `donde = f" de la obra {obra_cod}" if not obra_cod else ""`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: NO es equivalente: el mutante pone « de la obra None» sin código y lo quita con código. Ningún test miraba el texto del motivo con y sin `obra_cod`.
> Decisión: **hueco de test**. Test añadido: `test_t28_el_motivo_nombra_la_obra_solo_si_se_conoce` (sv5 `tests/test_f072_t28_mutantes.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 42. `services/partes-transfer/application/services/reglas_registro.py:148` [entero]

- Original: `elif tipo == VAR and not es_partida_var(hoja, int(desde or 0)):`
- Mutado:   `elif tipo == VAR and not es_partida_var(hoja, int(desde or 1)):`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Como el #25, en la guarda de sv5: con `desde` 0 la partida 0 es del universo VAR.
> Decisión: **hueco de test**. Test añadido: `test_t28_con_desde_0_la_partida_0_es_del_universo_var` (sv5 `tests/test_f072_t28_mutantes.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 43. `services/partes-transfer/domain/models/registro_models.py:241` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `frozen=False` solo cambia la inmutabilidad (y quita el `__hash__`); ningún test asignaba un campo ni usaba el valor como clave.
> Decisión: **hueco de test**. Test añadido: `test_t28_la_partida_hoja_es_inmutable` (sv5 `tests/test_f072_t28_mutantes.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

### 44. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:505` [entero]

- Original: `paride=(int(f.get("paride") or 0) or None) if con_partida`
- Mutado:   `paride=(int(f.get("paride") or 1) or None) if con_partida`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: Ninguna fila con `paride` NULL leída con partida: con `or 1` sería la partida 1 y chocaría con ella.
> Decisión: **hueco de test**. Test añadido: `test_t28_linea_sin_partida_en_sigrid_da_paride_none` (sv5 `tests/test_f072_t28_mutantes.py`). Verificado a mano (T28) con el mutante aplicado y deshecho: el test falla con él y pasa sin él.

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

#### Declaración

> Cinco `Field(None, alias=...)`, la propiedad `obras_agrupadas` (una llamada a `ajustes_de` con keywords) y el validador que la invoca: sin operador ni literal mutable. Lo cubre `tests/test_f072_settings.py` de sv2 (R1 y R2: lectura, apagado y `ValueError` que impide arrancar).

### `services/partes-api/interface_adapters/api/app.py` — 2 líneas en alcance, 0 mutantes

#### Declaración

> Un argumento keyword nuevo (`marcas=settings.obras_agrupadas.marcas`). Lo cubre `test_f072_r13_build_app_pasa_las_marcas_de_la_configuracion` (`tests/test_f072_marca_sv2.py`).

### `services/partes-front/config/settings.py` — 27 líneas en alcance, 0 mutantes

#### Declaración

> Los `Field(None, alias=...)` de F-072, la propiedad `obras_agrupadas` y su validador: sin operador ni literal mutable. Lo cubre `tests/test_f072_settings.py` de sv4.

### `services/partes-persistencia/config/settings.py` — 31 líneas en alcance, 0 mutantes

#### Declaración

> Igual que en sv2: campos, propiedad y validador sin nada que mutar. Lo cubre `tests/test_f072_settings.py` de sv3.

### `services/partes-transfer/application/pipelines/franquicia_pipeline.py` — 2 líneas en alcance, 0 mutantes

#### Declaración

> Un argumento keyword nuevo (`partida_metodo=getattr(p, "partida_metodo", None)`), sin nada que el generador mute. Lo cubren `test_f072_franquicia_con_la_marca_de_la_entrada_se_prepara` y `test_f072_franquicia_sin_marca_en_obra_agrupada_se_omite` (`tests/test_f072_guarda_reajuste_franquicia.py`).

### `services/partes-transfer/config/settings.py` — 27 líneas en alcance, 0 mutantes

#### Declaración

> Igual que en sv4: campos, propiedad y validador. Lo cubre `tests/test_f072_settings.py` de sv5.

### `services/partes-transfer/interface_adapters/api/app.py` — 11 líneas en alcance, 0 mutantes

#### Declaración

> Tres campos `partida_metodo: Optional[str] = None` de los modelos de entrada, el `exclude` del `model_dump` y la asignación del atributo: sin operador ni literal que el generador mute. Lo cubren `test_f072_franquicia_in_lleva_la_marca_al_dominio` y `test_f072_linea_reajuste_in_lleva_la_marca_al_dominio`.


## Aceptación del humano (2026-11-24)

Literal del humano por el chat: «acepto los 13 equivalentes de F-072». Quedan **aceptados** los
equivalentes #1, 12, 13, 14, 15, 19, 20, 21, 23, 26, 34, 36 y 37 (demostración:
`progress/equivalentes_F-072.py`). Supervivientes sin test ni aceptación: **0**.
