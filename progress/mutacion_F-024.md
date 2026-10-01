<!-- progress/mutacion_F-024.md -->
# F-024 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-024` el 2026-10-01 16:42.

## Alcance

Origen del diff: **rama** (`557fb4519639f1cf5d2af7fc78a9250d38748342` .. `feature/F-024-lineas-encoladas`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/comprobacion_sigrid.py` | 140 |
| `services/partes-front/application/services/congelacion.py` | 8 |
| `services/partes-front/config/settings.py` | 9 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 149 |
| `services/partes-front/infrastructure/transfer/transfer_client.py` | 13 |
| `services/partes-front/interface_adapters/web/app.py` | 123 |
| `services/partes-transfer/application/services/comprobacion_lineas.py` | 182 |
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | 46 |
| `services/partes-transfer/interface_adapters/api/app.py` | 72 |
| `services/partes-transfer/main.py` | 4 |
| **Total** | **746** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 175 |
| Mutantes evaluados | 175 |
| Muertos | 152 |
| Supervivientes | 23 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 4130.5 s |
| SHA de HEAD medido | `156d6e3b7998ccf31a80a01fb10cebe3e707b890` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-024_ntn2sj41/wk_0/services/partes-front` | 277.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-024_ntn2sj41/wk_0/services/partes-transfer` | 12.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-024_ntn2sj41/wk_1/services/partes-front` | 279.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-024_ntn2sj41/wk_1/services/partes-transfer` | 11.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-024_ntn2sj41/wk_2/services/partes-front` | 279.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-024_ntn2sj41/wk_2/services/partes-transfer` | 11.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-024_ntn2sj41/wk_3/services/partes-front` | 278.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-024_ntn2sj41/wk_3/services/partes-transfer` | 11.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-024_ntn2sj41/wk_4/services/partes-front` | 280.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-024_ntn2sj41/wk_4/services/partes-transfer` | 11.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-024_ntn2sj41/wk_5/services/partes-front` | 278.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-024_ntn2sj41/wk_5/services/partes-transfer` | 11.7 |
| Media por mutante evaluado (s) | 23.6 |
| Timeout efectivo por mutante (s) | 600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 600 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/comprobacion_sigrid.py:104` [booleano]

- Original: `resp = {"ok": False, "error": f"error llamando a sv5: {exc}"}`
- Mutado:   `resp = {"ok": True, "error": f"error llamando a sv5: {exc}"}`

#### Análisis

> Por qué ningún test lo caza: el lote fallaba igual (sin veredictos ⇒ `faltan`), pero nadie comprobaba que el error devuelto fuese el de la excepción.
> Decisión: **test nuevo** `test_f024_r14_servicio_la_excepcion_de_sv5_llega_al_error` (`services/partes-front/tests/test_f024_comprobar_y_estado.py`). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 2. `services/partes-front/config/settings.py:69` [entero]

- Original: `30.0, alias="COMPROBACION_SIGRID_TIMEOUT_S", gt=0)`
- Mutado:   `30.0, alias="COMPROBACION_SIGRID_TIMEOUT_S", gt=1)`

#### Análisis

> Por qué ningún test lo caza: ningún test usaba un plazo positivo menor que 1 s.
> Decisión: **test nuevo** `test_f024_r17_servicio_settings_timeout_fraccionario` (`services/partes-front/tests/test_f024_comprobar_y_estado.py`). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 3. `services/partes-front/infrastructure/database/parte_repository.py:87` [entero]

- Original: `LOTE_IDS_CONSULTA = 1000`
- Mutado:   `LOTE_IDS_CONSULTA = 1001`

#### Análisis

> Por qué ningún test lo caza: ningún test pasaba más de 1000 ids ni contaba consultas.
> Decisión: **test nuevo** `test_f024_r17_repo_consulta_por_lotes_de_mil_ids` (`services/partes-front/tests/test_f024_borrado_sigrid.py`): 1001 ids ⇒ 2 consultas. Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 4. `services/partes-front/infrastructure/database/parte_repository.py:99` [logico]

- Original: `or reg.sigrid_hmoide or "?")`
- Mutado:   `and reg.sigrid_hmoide or "?")`

#### Análisis

> Por qué ningún test lo caza: ningún test borraba sin `sigrid_parte_cod` guardado; el respaldo por el código del veredicto no se ejercía.
> Decisión: **test nuevo** `test_f024_r10_repo_motivo_parte_de_respaldo[del-veredicto]` (`services/partes-front/tests/test_f024_borrado_sigrid.py`). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 5. `services/partes-front/infrastructure/database/parte_repository.py:99` [logico]

- Original: `or reg.sigrid_hmoide or "?")`
- Mutado:   `or reg.sigrid_hmoide and "?")`

#### Análisis

> Por qué ningún test lo caza: ningún test llegaba al último respaldo (`?`) del motivo.
> Decisión: **test nuevo** `test_f024_r10_repo_motivo_parte_de_respaldo[sin-nada]` (`services/partes-front/tests/test_f024_borrado_sigrid.py`). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 6. `services/partes-front/infrastructure/database/parte_repository.py:1456` [entero]

- Original: `rid = int(v.get("registro_id") or 0)`
- Mutado:   `rid = int(v.get("registro_id") or 1)`

#### Análisis

> Por qué ningún test lo caza: ningún veredicto llegaba sin `registro_id` con el id 1 enviado.
> Decisión: **test nuevo** `test_f024_r11_repo_veredicto_sin_registro_id_no_se_aplica` (`services/partes-front/tests/test_f024_borrado_sigrid.py`). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 7. `services/partes-front/infrastructure/database/parte_repository.py:1459` [booleano]

- Original: `reg = session.get(ParteRegistroOrm, rid, with_for_update=True)`
- Mutado:   `reg = session.get(ParteRegistroOrm, rid, with_for_update=False)`

#### Análisis

> Por qué ningún test lo caza: SQLite ignora `FOR UPDATE`: el bloqueo de fila del CAS (R11) no se observaba.
> Decisión: **test nuevo** `test_f024_r11_repo_lee_cada_linea_con_bloqueo_de_fila` (`services/partes-front/tests/test_f024_borrado_sigrid.py`), que espía `session.get`. Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 8. `services/partes-front/interface_adapters/web/app.py:2057` [booleano]

- Original: `@app.post("/api/sigrid/comprobar", include_in_schema=False)`
- Mutado:   `@app.post("/api/sigrid/comprobar", include_in_schema=True)`

#### Análisis

> Por qué ningún test lo caza: nadie miraba el esquema OpenAPI.
> Decisión: **test nuevo** `test_f024_r17_endpoint_fuera_del_esquema_publico[/api/sigrid/comprobar]` (`services/partes-front/tests/test_f024_comprobar_y_estado.py`). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 9. `services/partes-front/interface_adapters/web/app.py:2076` [booleano]

- Original: `@app.post("/api/aprobar/estado", include_in_schema=False)`
- Mutado:   `@app.post("/api/aprobar/estado", include_in_schema=True)`

#### Análisis

> Por qué ningún test lo caza: nadie miraba el esquema OpenAPI.
> Decisión: **test nuevo** `test_f024_r17_endpoint_fuera_del_esquema_publico[/api/aprobar/estado]` (`services/partes-front/tests/test_f024_comprobar_y_estado.py`). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 10. `services/partes-transfer/application/services/comprobacion_lineas.py:47` [booleano]

- Original: `es_incidencia: bool = False`
- Mutado:   `es_incidencia: bool = True`

#### Análisis

> Por qué ningún test lo caza: los tests siempre pasaban `es_incidencia` explícito.
> Decisión: **test nuevo** `test_f024_r6_clasificar_por_defecto_no_es_incidencia` (`services/partes-transfer/tests/test_f024_comprobacion.py`). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 11. `services/partes-transfer/application/services/comprobacion_lineas.py:84` [comparacion]

- Original: `float(fila.can) - float(linea.horas)) > TOLERANCIA_HORAS):`
- Mutado:   `float(fila.can) - float(linea.horas)) >= TOLERANCIA_HORAS):`

#### Análisis

> Por qué ningún test lo caza: ningún caso caía justo en 0,005 (las tablas usaban 0,004/0,006).
> Decisión: **test nuevo** `test_f024_r6_clasificar_tolerancia_justo_en_el_limite` (`services/partes-transfer/tests/test_f024_comprobacion.py`): horas 0 frente a can 0,005. Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 12. `services/partes-transfer/application/services/comprobacion_lineas.py:98` [booleano]

- Original: `return False`
- Mutado:   `return True`

#### Análisis

> Por qué ningún test lo caza: es **equivalente**. Es el `return False` de `_respaldo_valido` cuando no hay fila en `por_ide`. Con `True`, `clasificar` asigna `fila = candidata`, que es `None`, y el `if fila is not None` siguiente lleva igualmente a `borrada` con los mismos campos: no hay entrada que distinga los dos programas.
> Decisión: **mutante equivalente**, justificado para el humano. La guarda se mantiene porque sin ella la línea siguiente (`fila.synckey`) fallaría con `None`.

### 13. `services/partes-transfer/application/services/comprobacion_lineas.py:178` [entero]

- Original: `sum(1 for v in veredictos if v.estado == PRESENTE),`
- Mutado:   `sum(2 for v in veredictos if v.estado == PRESENTE),`

#### Análisis

> Por qué ningún test lo caza: el log `[comprobar]` no tenía test.
> Decisión: **test nuevo** `test_f024_r21_comprobador_log_con_los_recuentos` (`services/partes-transfer/tests/test_f024_comprobacion.py`). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 14. `services/partes-transfer/application/services/comprobacion_lineas.py:178` [comparacion]

- Original: `sum(1 for v in veredictos if v.estado == PRESENTE),`
- Mutado:   `sum(1 for v in veredictos if v.estado != PRESENTE),`

#### Análisis

> Por qué ningún test lo caza: el log `[comprobar]` no tenía test.
> Decisión: **test nuevo** `test_f024_r21_comprobador_log_con_los_recuentos` (`services/partes-transfer/tests/test_f024_comprobacion.py`), con 2 presentes y 3 borradas (asimétrico). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 15. `services/partes-transfer/application/services/comprobacion_lineas.py:179` [entero]

- Original: `sum(1 for v in veredictos if v.estado == BORRADA),`
- Mutado:   `sum(2 for v in veredictos if v.estado == BORRADA),`

#### Análisis

> Por qué ningún test lo caza: el log `[comprobar]` no tenía test.
> Decisión: **test nuevo** `test_f024_r21_comprobador_log_con_los_recuentos` (`services/partes-transfer/tests/test_f024_comprobacion.py`). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 16. `services/partes-transfer/application/services/comprobacion_lineas.py:179` [comparacion]

- Original: `sum(1 for v in veredictos if v.estado == BORRADA),`
- Mutado:   `sum(1 for v in veredictos if v.estado != BORRADA),`

#### Análisis

> Por qué ningún test lo caza: el log `[comprobar]` no tenía test.
> Decisión: **test nuevo** `test_f024_r21_comprobador_log_con_los_recuentos` (`services/partes-transfer/tests/test_f024_comprobacion.py`), con 2 presentes y 3 borradas (asimétrico). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 17. `services/partes-transfer/application/services/comprobacion_lineas.py:180` [entero]

- Original: `sum(1 for v in veredictos if v.sin_synckey),`
- Mutado:   `sum(2 for v in veredictos if v.sin_synckey),`

#### Análisis

> Por qué ningún test lo caza: el log `[comprobar]` no tenía test.
> Decisión: **test nuevo** `test_f024_r21_comprobador_log_con_los_recuentos` (`services/partes-transfer/tests/test_f024_comprobacion.py`). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 18. `services/partes-transfer/application/services/comprobacion_lineas.py:181` [entero]

- Original: `sum(1 for v in veredictos if v.diferencias))`
- Mutado:   `sum(2 for v in veredictos if v.diferencias))`

#### Análisis

> Por qué ningún test lo caza: el log `[comprobar]` no tenía test.
> Decisión: **test nuevo** `test_f024_r21_comprobador_log_con_los_recuentos` (`services/partes-transfer/tests/test_f024_comprobacion.py`). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 19. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:352` [entero]

- Original: `ide=int(f["ide"]), reside=int(f["reside"] or 0),`
- Mutado:   `ide=int(f["ide"]), reside=int(f["reside"] or 1),`

#### Análisis

> Por qué ningún test lo caza: ninguna fila simulada traía `reside` NULL.
> Decisión: **test nuevo** `test_f024_r7_cliente_lineas_por_ide_nulos_a_cero` (`services/partes-transfer/tests/test_f024_comprobacion.py`). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 20. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:353` [entero]

- Original: `fecha_int=int(f["fec"] or 0),`
- Mutado:   `fecha_int=int(f["fec"] or 1),`

#### Análisis

> Por qué ningún test lo caza: ninguna fila simulada traía `fec` NULL.
> Decisión: **test nuevo** `test_f024_r7_cliente_lineas_por_ide_nulos_a_cero` (`services/partes-transfer/tests/test_f024_comprobacion.py`). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 21. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:357` [entero]

- Original: `setattr(ls, "hmoide", int(f["hmoide"] or 0))`
- Mutado:   `setattr(ls, "hmoide", int(f["hmoide"] or 1))`

#### Análisis

> Por qué ningún test lo caza: ninguna fila simulada traía `hmoide` NULL.
> Decisión: **test nuevo** `test_f024_r7_cliente_lineas_por_ide_nulos_a_cero` (`services/partes-transfer/tests/test_f024_comprobacion.py`). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 22. `services/partes-transfer/interface_adapters/api/app.py:75` [booleano]

- Original: `es_incidencia: bool = False`
- Mutado:   `es_incidencia: bool = True`

#### Análisis

> Por qué ningún test lo caza: los tests del endpoint siempre enviaban `es_incidencia`.
> Decisión: **test nuevo** `test_f024_r6_endpoint_por_defecto_no_es_incidencia` (`services/partes-transfer/tests/test_f024_comprobacion.py`). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

### 23. `services/partes-transfer/interface_adapters/api/app.py:117` [comparacion]

- Original: `if comprobador is None:`
- Mutado:   `if comprobador is not None:`

#### Análisis

> Por qué ningún test lo caza: con `pipeline=None` y comprobador inyectado a la vez no había test; el mutante sustituía el inyectado por uno propio.
> Decisión: **test nuevo** `test_f024_r1_endpoint_respeta_el_comprobador_inyectado_sin_pipeline` (`services/partes-transfer/tests/test_f024_comprobacion.py`). Verificado aplicando el mutante a mano y corriendo el test: FALLA (muerto); árbol restaurado después.

## Cierre del análisis

22 de 23 supervivientes muertos con tests nuevos (cada uno verificado
aplicando el mutante a mano y corriendo su test: falla), 1 equivalente
justificado (n.º 12). **0 supervivientes sin resolver**; el n.º 12 queda
pendiente de aceptación del humano (nivel critico). La campaña no se
relanzó tras los tests (regla del flujo: medir-tapar-medir no termina);
la verificación de cada mutante está en el informe del implementer.
