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

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: ningún test intentaba modificar la instancia; el código no la modifica nunca, así que `frozen` no se observaba.
> Decisión: **test nuevo** `test_f052_r18_lineas_y_diferencias_inmutables` (`services/partes-front/tests/test_f052_clasificar.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 2. `services/partes-front/application/services/sincronizacion.py:91` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: ningún test intentaba modificar la instancia; el código no la modifica nunca, así que `frozen` no se observaba.
> Decisión: **test nuevo** `test_f052_r18_lineas_y_diferencias_inmutables` (`services/partes-front/tests/test_f052_clasificar.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 3. `services/partes-front/application/services/sincronizacion.py:121` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: ningún test intentaba modificar la instancia; el código no la modifica nunca, así que `frozen` no se observaba.
> Decisión: **test nuevo** `test_f052_r18_lineas_y_diferencias_inmutables` (`services/partes-front/tests/test_f052_clasificar.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 4. `services/partes-front/application/services/sincronizacion.py:155` [comparacion]

- Original: `return abs(float(valor or 0.0)) <= TOLERANCIA_HORAS`
- Mutado:   `return abs(float(valor or 0.0)) < TOLERANCIA_HORAS`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: los casos de `a_cero` eran 0, 0,004 y 1; ninguno en el límite exacto 0,005.
> Decisión: **test nuevo** `test_f052_r8_a_cero_justo_en_la_tolerancia` (`services/partes-front/tests/test_f052_clasificar.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 5. `services/partes-front/application/services/sincronizacion.py:175` [entero]

- Original: `return (motivo or "").split(":", 1)[0].strip() or OMITIDO`
- Mutado:   `return (motivo or "").split(":", 2)[0].strip() or OMITIDO`

#### Análisis (EQUIVALENTE)

> Por qué ningún test lo caza: `s.split(":", n)[0]` es el texto anterior al primer `:` para cualquier `n >= 1`; el `maxsplit` solo cambia los trozos de después, que `[0]` descarta.
> Decisión: **mutante equivalente** (pendiente de aceptar por el humano). Demostración ejecutable: `python -c "import random; random.seed(52); al=['a',':','b',' ','x']; assert all(s.split(':',1)[0]==s.split(':',2)[0] for s in (''.join(random.choices(al,k=random.randint(0,12))) for _ in range(100000))); print('equivalente')"` -> `equivalente`.

### 6. `services/partes-front/application/services/sincronizacion.py:191` [comparacion]

- Original: `if abs(float(p.horas or 0.0) - float(s.can or 0.0)) > TOLERANCIA_HORAS:`
- Mutado:   `if abs(float(p.horas or 0.0) - float(s.can or 0.0)) >= TOLERANCIA_HORAS:`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: la tolerancia se probaba con 8,004/8,006, nunca con una diferencia exactamente igual a 0,005 (el test usa `comparar(P(horas=TOLERANCIA_HORAS), S(can=0.0))`, exacta en coma flotante).
> Decisión: **test nuevo** `test_f052_r9_diferencia_de_horas_justo_en_la_tolerancia` (`services/partes-front/tests/test_f052_clasificar.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 7. `services/partes-front/application/services/sincronizacion.py:270` [logico]

- Original: `if s.origen == "partes" and s.registro_id is not None:`
- Mutado:   `if s.origen == "partes" or s.registro_id is not None:`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: en el test de DA12 la línea `partes` tenía el `hmores.ide` menor y `setdefault` la guardaba primero; con la CIZ hermana leída antes, el mutante casaba la línea del portal con la CIZ.
> Decisión: **test nuevo** `test_f052_r8_ciz_hermano_con_ide_menor_no_casa_con_su_inicio` (`services/partes-front/tests/test_f052_clasificar.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 8. `services/partes-front/application/services/sincronizacion.py:323` [booleano]

- Original: `texto = json.dumps(datos, sort_keys=True, separators=(",", ":"),`
- Mutado:   `texto = json.dumps(datos, sort_keys=False, separators=(",", ":"),`

#### Análisis (EQUIVALENTE)

> Por qué ningún test lo caza: `datos` se construye siempre con el mismo orden de claves (literal `clase, portal, sigrid` y `asdict`, que sigue el orden de los campos), así que sin `sort_keys` el JSON sigue siendo función determinista e inyectiva de los valores. La firma es opaca (la spec: «huella de lo que el usuario vio») y solo se compara con otra de la misma función.
> Decisión: **mutante equivalente** (pendiente de aceptar por el humano). Único efecto: entre dos versiones desplegadas las firmas no coincidirían y la acción saldría «cambió desde que lo viste» (inocuo: se vuelve a sincronizar). Demostración ejecutable: `DEMO_FIRMA`, abajo (comprueba `f == firma` y que la igualdad de firmas entre todos los pares de ítems no cambia con `sort_keys=False`) -> `8 y 9 equivalentes: 5 items`.
>
> `DEMO_FIRMA` (8 y 9), desde `services/partes-front`, resultado real `8 y 9 equivalentes: 5 items`:
> ```
> python -B -c "
> import json,hashlib,itertools
> from dataclasses import asdict
> from application.services import sincronizacion as m
> from tests.test_f052_clasificar import P,S
> items=m.clasificar([P(1),P(2,horas=4.0),P(3,'omitido',sigrid_motivo='año: peón')],[S(9001,registro_id=1),S(9002,registro_id=2,can=3.0),S(9100,'manual',partida_cod='Ñ')])+m.clasificar([P(1,partida_cod='Ñ')],[S(9001,registro_id=1)])
> def f(it,**kw):
>     d={'clase':it.clase,'portal':asdict(it.portal) if it.portal else None,'sigrid':asdict(it.sigrid) if it.sigrid else None}
>     o=dict(sort_keys=True,ensure_ascii=False); o.update(kw)
>     return hashlib.sha256(json.dumps(d,separators=(',',':'),default=str,**o).encode()).hexdigest()[:16]
> assert all(f(it)==m.firma(it) for it in items)
> for kw in ({'sort_keys':False},{'ensure_ascii':True}):
>     assert all((f(a)==f(b))==(f(a,**kw)==f(b,**kw)) for a,b in itertools.product(items,repeat=2))
> print('8 y 9 equivalentes:', len(items), 'items')"
> ```

### 9. `services/partes-front/application/services/sincronizacion.py:324` [booleano]

- Original: `ensure_ascii=False, default=str)`
- Mutado:   `ensure_ascii=True, default=str)`

#### Análisis (EQUIVALENTE)

> Por qué ningún test lo caza: `ensure_ascii=True` cambia el texto (escapa `ñ` como `\u00f1`), pero el escape es inyectivo y la firma solo se compara consigo misma (mismo razonamiento que el 8).
> Decisión: **mutante equivalente** (pendiente de aceptar por el humano). Misma demostración que el 8 (`DEMO_FIRMA` del mutante 8, con los textos `año: peón` y `Ñ`).

### 10. `services/partes-front/application/services/sincronizar_ambito.py:81` [entero]

- Original: `if not resto.isdigit() or int(resto) <= 0:`
- Mutado:   `if not resto.isdigit() or int(resto) <= 1:`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: las claves probadas eran `obr-686`, `rec-501` y claves no válidas; ninguna con ide 1.
> Decisión: **test nuevo** `test_f052_r15_ide_1_es_sincronizable` (`services/partes-front/tests/test_f052_sincronizar_ambito.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 11. `services/partes-front/application/services/sincronizar_ambito.py:99` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: ningún test intentaba modificar la instancia; el código no la modifica nunca, así que `frozen` no se observaba.
> Decisión: **test nuevo** `test_f052_r15_ambito_inmutable` (`services/partes-front/tests/test_f052_sincronizar_ambito.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 12. `services/partes-front/application/services/sincronizar_ambito.py:152` [logico]

- Original: `if not isinstance(d, dict) or d.get("origen") not in ORIGENES:`
- Mutado:   `if not isinstance(d, dict) and d.get("origen") not in ORIGENES:`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: la única línea mal formada del test de R13 no tenía `origen` y además traía `can: "x"`, que revienta igual en `_real`; una línea completa con `origen` desconocido no se probaba.
> Decisión: **test nuevo** `test_f052_r2_linea_de_sv5_con_origen_desconocido_es_error` (`services/partes-front/tests/test_f052_sincronizar_ambito.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 13. `services/partes-front/application/services/sincronizar_ambito.py:195` [entero]

- Original: `max_items_accion: int = 500,`
- Mutado:   `max_items_accion: int = 501,`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: todos los tests pasaban `max_items_accion` explícito (el helper `_sync` y la app, desde settings); el valor por defecto no se usaba.
> Decisión: **test nuevo** `test_f052_r18_tope_por_defecto_500` (`services/partes-front/tests/test_f052_sincronizar_ambito.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 14. `services/partes-front/application/services/sincronizar_ambito.py:294` [booleano]

- Original: `it.por_confirmar = False`
- Mutado:   `it.por_confirmar = True`

#### Análisis (EQUIVALENTE)

> Por qué ningún test lo caza: escritura muerta. `por_confirmar` solo se lee en `sincronizar_ambito.py:279` (para elegir las huérfanas), ANTES de esta línea; después nadie lo lee: ni `item_a_dict`, ni `firma` (clase y los dos lados), ni `resumen`, ni `aplicar`. Matarlo exigiría un test del método privado `_leer` sobre un campo que nadie consume.
> Decisión: **mutante equivalente** (pendiente de aceptar por el humano; alternativa: borrar la línea en una feature posterior). Demostración ejecutable: `grep -rn "por_confirmar" services/partes-front --include=*.py --include=*.js --include=*.html | grep -v /tests/` -> 4 apariciones: la declaración (141), `= True` en `clasificar` (248), la lectura (279) y esta escritura (294).

### 15. `services/partes-front/application/services/sincronizar_ambito.py:335` [logico]

- Original: `and v.get("registro_id") is not None}`
- Mutado:   `or v.get("registro_id") is not None}`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: ningún doble de sv5 devolvía un veredicto con `registro_id` nulo; con el mutante, `int(None)` revienta.
> Decisión: **test nuevo** `test_f052_da18_seco_veredicto_sin_registro_id_se_ignora` (`services/partes-front/tests/test_f052_sincronizar_ambito.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 16. `services/partes-front/application/services/sincronizar_ambito.py:363` [comparacion]

- Original: `if len(items) > self._max_items:`
- Mutado:   `if len(items) >= self._max_items:`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: el tope se probaba con 3 líneas y máximo 2, no con exactamente el máximo.
> Decisión: **test nuevo** `test_f052_r18_tope_justo_es_valido` (`services/partes-front/tests/test_f052_sincronizar_ambito.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 17. `services/partes-front/config/settings.py:82` [entero]

- Original: `150.0, alias="SINCRONIZAR_TIMEOUT_S", gt=0, lt=230)`
- Mutado:   `150.0, alias="SINCRONIZAR_TIMEOUT_S", gt=1, lt=230)`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: los valores probados eran 150 (válido) y 0, -1, 230 (no válidos); ninguno entre 0 y 1.
> Decisión: **test nuevo** `test_f052_settings_limites_validos_justos` (`services/partes-front/tests/test_f052_endpoints.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 18. `services/partes-front/config/settings.py:94` [entero]

- Original: `500, alias="SINCRONIZAR_MAX_ITEMS_ACCION", ge=1, le=5000)`
- Mutado:   `500, alias="SINCRONIZAR_MAX_ITEMS_ACCION", ge=2, le=5000)`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: se probaban 500 (válido) y 0 y 5001 (no válidos); no el mínimo válido 1.
> Decisión: **test nuevo** `test_f052_settings_limites_validos_justos` (`services/partes-front/tests/test_f052_endpoints.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 19. `services/partes-front/infrastructure/database/parte_repository.py:234` [logico]

- Original: `if a is None or b is None:`
- Mutado:   `if a is None and b is None:`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: ningún test llegaba al CAS de `traer` con horas NULL en un solo lado; con el mutante revienta con `float(None)` (lo caza también `test_f052_r20_traer_horas_nulas_en_la_base_no_casan_con_lo_visto`).
> Decisión: **test nuevo** `test_f052_r20_cas_de_horas_mismas_horas` (`services/partes-front/tests/test_f052_repositorio.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 20. `services/partes-front/infrastructure/database/parte_repository.py:235` [comparacion]

- Original: `return a is None and b is None`
- Mutado:   `return a is not None and b is None`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: no se probaba NULL contra NULL.
> Decisión: **test nuevo** `test_f052_r20_cas_de_horas_mismas_horas` (`services/partes-front/tests/test_f052_repositorio.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 21. `services/partes-front/infrastructure/database/parte_repository.py:235` [logico]

- Original: `return a is None and b is None`
- Mutado:   `return a is None or b is None`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: no se probaba un solo lado NULL.
> Decisión: **test nuevo** `test_f052_r20_cas_de_horas_mismas_horas` (`services/partes-front/tests/test_f052_repositorio.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 22. `services/partes-front/infrastructure/database/parte_repository.py:235` [comparacion]

- Original: `return a is None and b is None`
- Mutado:   `return a is None and b is not None`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: no se probaba NULL en la base y horas en lo visto.
> Decisión: **test nuevo** `test_f052_r20_cas_de_horas_mismas_horas` (`services/partes-front/tests/test_f052_repositorio.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 23. `services/partes-front/infrastructure/database/parte_repository.py:236` [comparacion]

- Original: `return abs(float(a) - float(b)) < 1e-9`
- Mutado:   `return abs(float(a) - float(b)) <= 1e-9`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: no se probaba una diferencia exactamente igual a la tolerancia (1e-9 contra 0.0, exacta).
> Decisión: **test nuevo** `test_f052_r20_cas_de_horas_mismas_horas` (`services/partes-front/tests/test_f052_repositorio.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 24. `services/partes-front/infrastructure/database/parte_repository.py:2767` [logico]

- Original: `and doc.deleted_at_utc is None`
- Mutado:   `or doc.deleted_at_utc is None`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: el parte `retirado` (solo `deleted_by`) del test de R12 tenía su línea borrada, que gana en la primera rama; faltaba una línea viva en un parte con una sola marca.
> Decisión: **test nuevo** `test_f052_r12_donde_estan_parte_con_solo_una_marca_de_borrado` (`services/partes-front/tests/test_f052_repositorio.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 25. `services/partes-front/infrastructure/database/parte_repository.py:2789` [booleano]

- Original: `with_for_update=True)`
- Mutado:   `with_for_update=False)`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: SQLite ignora `FOR UPDATE`; el test mira la llamada con una sesión doble que apunta `with_for_update=True` y el orden por id.
> Decisión: **test nuevo** `test_f052_r20_bloqueo_for_update_en_orden_de_id` (`services/partes-front/tests/test_f052_repositorio.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 26. `services/partes-front/infrastructure/database/parte_repository.py:2873` [logico]

- Original: `or "sin estado")`
- Mutado:   `and "sin estado")`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: los descartes de `traer` se probaban con estado `error`; nunca con estado vacío.
> Decisión: **test nuevo** `test_f052_r20_traer_a_linea_sin_estado_lo_dice` (`services/partes-front/tests/test_f052_repositorio.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 27. `services/partes-front/infrastructure/database/parte_repository.py:2899` [logico]

- Original: `if recurso and reg.fecha_int:`
- Mutado:   `if recurso or reg.fecha_int:`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: todas las líneas traídas tenían recurso y fecha; sin recurso, el mutante revienta con `int(None)`.
> Decisión: **test nuevo** `test_f052_r23_traer_linea_sin_recurso_no_da_par_de_dia` (`services/partes-front/tests/test_f052_repositorio.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 28. `services/partes-front/interface_adapters/web/app.py:307` [entero]

- Original: `firma: str = Field(min_length=1, max_length=64)`
- Mutado:   `firma: str = Field(min_length=2, max_length=64)`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: las firmas de los tests tenían 16 caracteres; la de 1 carácter solo salía en peticiones ya inválidas por otro motivo.
> Decisión: **test nuevo** `test_f052_r18_aplicar_largo_de_la_firma` (`services/partes-front/tests/test_f052_endpoints.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 29. `services/partes-front/interface_adapters/web/app.py:307` [entero]

- Original: `firma: str = Field(min_length=1, max_length=64)`
- Mutado:   `firma: str = Field(min_length=1, max_length=65)`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: no se probaba una firma de 65 caracteres.
> Decisión: **test nuevo** `test_f052_r18_aplicar_largo_de_la_firma` (`services/partes-front/tests/test_f052_endpoints.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 30. `services/partes-front/interface_adapters/web/app.py:3464` [booleano]

- Original: `@app.post("/api/sincronizar", include_in_schema=False)`
- Mutado:   `@app.post("/api/sincronizar", include_in_schema=True)`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: no había test de `/openapi.json` para las rutas de F-052 (sí para las de F-024 y F-056).
> Decisión: **test nuevo** `test_f052_r18_rutas_fuera_del_esquema` (`services/partes-front/tests/test_f052_endpoints.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 31. `services/partes-front/interface_adapters/web/app.py:3473` [booleano]

- Original: `{"ok": False, "error": "registro en Sigrid no configurado "`
- Mutado:   `{"ok": True, "error": "registro en Sigrid no configurado "`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: el test miraba el status y el texto del error, no `ok`.
> Decisión: **test nuevo** `test_f052_r30_sin_transfer_503 (aserción añadida)` (`services/partes-front/tests/test_f052_endpoints.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 32. `services/partes-front/interface_adapters/web/app.py:3479` [booleano]

- Original: `@app.post("/api/sincronizar/aplicar", include_in_schema=False)`
- Mutado:   `@app.post("/api/sincronizar/aplicar", include_in_schema=True)`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: como el 30.
> Decisión: **test nuevo** `test_f052_r18_rutas_fuera_del_esquema` (`services/partes-front/tests/test_f052_endpoints.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 33. `services/partes-front/interface_adapters/web/app.py:3494` [booleano]

- Original: `{"ok": False, "error": "registro en Sigrid no configurado "`
- Mutado:   `{"ok": True, "error": "registro en Sigrid no configurado "`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: el test solo miraba el status.
> Decisión: **test nuevo** `test_f052_r30_aplicar_sin_transfer_503 (aserción añadida)` (`services/partes-front/tests/test_f052_endpoints.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 34. `services/partes-transfer/config/settings.py:37` [entero]

- Original: `3000, alias="SINCRONIZAR_MAX_REGISTRO_IDS", ge=1)`
- Mutado:   `3000, alias="SINCRONIZAR_MAX_REGISTRO_IDS", ge=2)`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: se probaban 3000, 10 y 0; no el mínimo válido 1.
> Decisión: **test nuevo** `test_f052_r6_settings_max_registro_ids_minimo_1` (`services/partes-transfer/tests/test_f052_api_sincronizar.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 35. `services/partes-transfer/domain/models/registro_models.py:234` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: ningún test intentaba modificar la instancia; el código no la modifica nunca, así que `frozen` no se observaba.
> Decisión: **test nuevo** `test_f052_r2_linea_sincronizar_inmutable` (`services/partes-transfer/tests/test_f052_api_sincronizar.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 36. `services/partes-transfer/interface_adapters/api/app.py:211` [entero]

- Original: `obra_ide: Optional[Annotated[int, Field(ge=1)]] = None`
- Mutado:   `obra_ide: Optional[Annotated[int, Field(ge=2)]] = None`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: se probaban `obra_ide` 686 y 0; no el ide 1.
> Decisión: **test nuevo** `test_f052_r6_ide_1_y_un_solo_dia_son_validos` (`services/partes-transfer/tests/test_f052_api_sincronizar.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 37. `services/partes-transfer/interface_adapters/api/app.py:212` [entero]

- Original: `recurso_ide: Optional[Annotated[int, Field(ge=1)]] = None`
- Mutado:   `recurso_ide: Optional[Annotated[int, Field(ge=2)]] = None`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: se probaban `recurso_ide` 501 y -1; no el ide 1.
> Decisión: **test nuevo** `test_f052_r6_ide_1_y_un_solo_dia_son_validos` (`services/partes-transfer/tests/test_f052_api_sincronizar.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 38. `services/partes-transfer/interface_adapters/api/app.py:227` [entero]

- Original: `if not 1 <= dias <= MAX_DIAS_SINCRONIZAR:`
- Mutado:   `if not 2 <= dias <= MAX_DIAS_SINCRONIZAR:`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: se probaban 31 y 62 días y rangos invertidos; nunca un solo día (`desde == hasta`).
> Decisión: **test nuevo** `test_f052_r6_ide_1_y_un_solo_dia_son_validos` (`services/partes-transfer/tests/test_f052_api_sincronizar.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 39. `services/partes-transfer/interface_adapters/api/app.py:227` [comparacion]

- Original: `if not 1 <= dias <= MAX_DIAS_SINCRONIZAR:`
- Mutado:   `if not 1 < dias <= MAX_DIAS_SINCRONIZAR:`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: como el 38.
> Decisión: **test nuevo** `test_f052_r6_ide_1_y_un_solo_dia_son_validos` (`services/partes-transfer/tests/test_f052_api_sincronizar.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 40. `services/partes-transfer/interface_adapters/api/app.py:293` [comparacion]

- Original: `if lector is None:`
- Mutado:   `if lector is not None:`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: los tests inyectaban `lector` siempre junto con `pipeline`, o ninguno; con el mutante, un `lector` inyectado sin `pipeline` se sustituía por el cliente real.
> Decisión: **test nuevo** `test_f052_r1_lector_inyectado_sin_pipeline` (`services/partes-transfer/tests/test_f052_api_sincronizar.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 41. `services/partes-transfer/interface_adapters/api/app.py:407` [booleano]

- Original: `{"ok": False, "error": f"como mucho {tope} registro_ids por "`
- Mutado:   `{"ok": True, "error": f"como mucho {tope} registro_ids por "`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: el caso de demasiados `registro_ids` estaba en el test parametrizado de 422, que solo mira el status.
> Decisión: **test nuevo** `test_f052_r6_demasiados_registro_ids_ok_false` (`services/partes-transfer/tests/test_f052_api_sincronizar.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

### 42. `services/partes-transfer/interface_adapters/api/app.py:409` [comparacion]

- Original: `ambito = "obra" if p.obra_ide is not None else "recurso"`
- Mutado:   `ambito = "obra" if p.obra_ide is None else "recurso"`

#### Análisis (MATADO)

> Por qué ningún test lo cazaba: `ambito` solo se usa en el log INFO y ningún test lo leía.
> Decisión: **test nuevo** `test_f052_r1_log_dice_el_ambito` (`services/partes-transfer/tests/test_f052_api_sincronizar.py`). Comprobado en copia aislada con el mutante aplicado: el test falla (ver `impl_F-052.md`, «Supervivientes de la mutación»).

