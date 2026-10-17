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

#### Análisis

> Por qué ningún test lo caza: la reserva sin PostgreSQL (rama SQLite) solo se ejercitaba con tabla llena y se comprobaba `>` en vez del id exacto.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_reserva_sin_postgresql_es_el_siguiente_al_mayor`. Re-evaluado: **MUERTO** (1 fallos).

### 2. `services/partes-front/infrastructure/database/parte_repository.py:3169` [entero]

- Original: `return max([int(maximo), *(int(v) for v in ya.values())]) + 1`
- Mutado:   `return max([int(maximo), *(int(v) for v in ya.values())]) + 2`

#### Análisis

> Por qué ningún test lo caza: la reserva sin PostgreSQL (rama SQLite) solo se ejercitaba con tabla llena y se comprobaba `>` en vez del id exacto.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_reserva_sin_postgresql_es_el_siguiente_al_mayor`. Re-evaluado: **MUERTO** (1 fallos).

### 3. `services/partes-front/infrastructure/database/parte_repository.py:3192` [logico]

- Original: `if reg is None or reg.deleted_at_utc:`
- Mutado:   `if reg is None and reg.deleted_at_utc:`

#### Análisis

> Por qué ningún test lo caza: ningun test pedia aplicar con una linea inexistente, y el de la papelera no miraba el mensaje (con `and` salta otro 409 mas tarde).
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_iniciar_con_una_linea_que_ya_no_existe_es_409`, `test_f046_t22_iniciar_con_una_linea_en_la_papelera_dice_cual`. Re-evaluado: **MUERTO** (2 fallos).

### 4. `services/partes-front/infrastructure/database/parte_repository.py:3196` [comparacion]

- Original: `if abs(float(reg.horas or 0.0) - float(c["antes"])) > 1e-6:`
- Mutado:   `if abs(float(reg.horas or 0.0) - float(c["antes"])) >= 1e-6:`

#### Análisis

> Por qué ningún test lo caza: sin caso en el borde de la tolerancia de 1e-6 h.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_iniciar_tolera_1e_6_horas`. Re-evaluado: **MUERTO** (1 fallos).

### 5. `services/partes-front/infrastructure/database/parte_repository.py:3199` [logico]

- Original: `f"{float(reg.horas or 0.0):g} h y el aviso decia "`
- Mutado:   `f"{float(reg.horas and 0.0):g} h y el aviso decia "`

#### Análisis

> Por qué ningún test lo caza: el test de linea cambiada solo buscaba «cambi» en el mensaje.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_iniciar_con_linea_cambiada_dice_cuanto_tiene`. Re-evaluado: **MUERTO** (1 fallos).

### 6. `services/partes-front/infrastructure/database/parte_repository.py:3289` [entero]

- Original: `error=None if ok else ((error or "")[:255] or None),`
- Mutado:   `error=None if ok else ((error or "")[:256] or None),`

#### Análisis

> Por qué ningún test lo caza: ningun error largo al cerrar la aplicacion.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_cerrar_recorta_el_error_a_255`. Re-evaluado: **MUERTO** (1 fallos).

### 7. `services/partes-front/infrastructure/database/parte_repository.py:3293` [comparacion]

- Original: `if res.rowcount != 1:`
- Mutado:   `if res.rowcount == 1:`

#### Análisis

> Por qué ningún test lo caza: nadie cerraba un reparto que ya no estaba `aplicando` (CAS perdido).
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_cerrar_un_reparto_que_ya_no_esta_aplicando`. Re-evaluado: **MUERTO** (4 fallos).

### 8. `services/partes-front/infrastructure/database/parte_repository.py:3293` [entero]

- Original: `if res.rowcount != 1:`
- Mutado:   `if res.rowcount != 2:`

#### Análisis

> Por qué ningún test lo caza: con `!= 2` el exito devuelve el mismo estado leido de la BD; solo cambia que se salta el log, que nadie miraba.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_log_de_cierre_ok_sin_error`. Re-evaluado: **MUERTO** (3 fallos).

### 9. `services/partes-front/infrastructure/database/parte_repository.py:3297` [logico]

- Original: `nuevo, actor, f": {error}" if error and not ok else "")`
- Mutado:   `nuevo, actor, f": {error}" if error or not ok else "")`

#### Análisis

> Por qué ningún test lo caza: el log del cierre no se comprobaba.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_log_de_cierre_ok_sin_error`, `test_f046_t22_log_de_cierre_rechazado_con_su_error`, `test_f046_t22_log_de_cierre_rechazado_sin_error`. Re-evaluado: **MUERTO** (2 fallos).

### 10. `services/partes-front/infrastructure/database/parte_repository.py:3297` [not]

- Original: `nuevo, actor, f": {error}" if error and not ok else "")`
- Mutado:   `nuevo, actor, f": {error}" if error and ok else "")`

#### Análisis

> Por qué ningún test lo caza: el log del cierre no se comprobaba.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_log_de_cierre_ok_sin_error`, `test_f046_t22_log_de_cierre_rechazado_con_su_error`, `test_f046_t22_log_de_cierre_rechazado_sin_error`. Re-evaluado: **MUERTO** (2 fallos).

### 11. `services/partes-front/infrastructure/transfer/transfer_client.py:96` [comparacion]

- Original: `if r.status_code >= 400:`
- Mutado:   `if r.status_code > 400:`

#### Análisis

> Por qué ningún test lo caza: los tests del cliente usaban 422 y 5xx, nunca un 400 exacto, ni miraban el log.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_un_400_de_sv5_es_un_no_con_su_error`. Re-evaluado: **MUERTO** (1 fallos).

### 12. `services/partes-front/infrastructure/transfer/transfer_client.py:96` [entero]

- Original: `if r.status_code >= 400:`
- Mutado:   `if r.status_code >= 401:`

#### Análisis

> Por qué ningún test lo caza: los tests del cliente usaban 422 y 5xx, nunca un 400 exacto, ni miraban el log.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_un_400_de_sv5_es_un_no_con_su_error`. Re-evaluado: **MUERTO** (1 fallos).

### 13. `services/partes-front/infrastructure/transfer/transfer_client.py:98` [entero]

- Original: `r.text[:300])`
- Mutado:   `r.text[:301])`

#### Análisis

> Por qué ningún test lo caza: los tests del cliente usaban 422 y 5xx, nunca un 400 exacto, ni miraban el log.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_un_400_de_sv5_es_un_no_con_su_error`. Re-evaluado: **MUERTO** (1 fallos).

### 14. `services/partes-front/interface_adapters/web/app.py:2378` [booleano]

- Original: `f["id"], exc_info=True)`
- Mutado:   `f["id"], exc_info=False)`

#### Análisis

> Por qué ningún test lo caza: nadie hacia fallar `reajuste_comprobar` con una excepcion.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_comprobar_que_lanza_deja_traza_y_su_error`. Re-evaluado: **MUERTO** (1 fallos).

### 15. `services/partes-front/interface_adapters/web/app.py:2379` [booleano]

- Original: `r = {"ok": False, "error": str(exc)}`
- Mutado:   `r = {"ok": True, "error": str(exc)}`

#### Análisis

> Por qué ningún test lo caza: `_veredictos_reparto` no lee la clave `ok` del dict que fabrica al fallar.
> Decisión: **mutante equivalente E6** (ver «Equivalentes», PENDIENTE de aceptacion del humano). Re-evaluado con los tests nuevos: vivo (0 fallos).

### 16. `services/partes-front/interface_adapters/web/app.py:2382` [logico]

- Original: `out[f["id"]] = {"error": r.get("error") or "sin respuesta",`
- Mutado:   `out[f["id"]] = {"error": r.get("error") and "sin respuesta",`

#### Análisis

> Por qué ningún test lo caza: ningun `comprobar` sin `veredictos`.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_comprobar_sin_veredictos_da_su_motivo`. Re-evaluado: **MUERTO** (3 fallos).

### 17. `services/partes-front/interface_adapters/web/app.py:2392` [not]

- Original: `if not bloque:`
- Mutado:   `if bloque:`

#### Análisis

> Por qué ningún test lo caza: ningun preflight RECHAZADO con reparto en su dia.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_preflight_rechazado_lleva_el_aviso_de_repartos`, `test_f046_t22_preflight_rechazado_sin_reparto_no_lleva_aviso`. Re-evaluado: **MUERTO** (2 fallos).

### 18. `services/partes-front/interface_adapters/web/app.py:2430` [comparacion]

- Original: `if rechazo is not None:`
- Mutado:   `if rechazo is None:`

#### Análisis

> Por qué ningún test lo caza: ninguna peticion con decisiones de reparto llevaba `ambito`.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_ambito_no_valido_no_decide_ningun_reparto`. Re-evaluado: **MUERTO** (1 fallos).

### 19. `services/partes-front/interface_adapters/web/app.py:2436` [booleano]

- Original: `{"ok": False, "error": (`
- Mutado:   `{"ok": True, "error": (`

#### Análisis

> Por qué ningún test lo caza: el 409 del reparto ajeno solo comprobaba el codigo HTTP.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_reparto_ajeno_responde_ok_false`. Re-evaluado: **MUERTO** (1 fallos).

### 20. `services/partes-front/interface_adapters/web/app.py:2459` [booleano]

- Original: `ok, error = False, ("registro en Sigrid no configurado "`
- Mutado:   `ok, error = True, ("registro en Sigrid no configurado "`

#### Análisis

> Por qué ningún test lo caza: la rama sin sv5 configurado solo se alcanza por la cola (`/api/aprobar/encolar` con publicador y sin TRANSFER_BASE_URL).
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_encolar_sin_sv5_configurado_no_aplica`. Re-evaluado: **MUERTO** (1 fallos).

### 21. `services/partes-front/interface_adapters/web/app.py:2467` [booleano]

- Original: `exc_info=True)`
- Mutado:   `exc_info=False)`

#### Análisis

> Por qué ningún test lo caza: nadie hacia que `reajuste_ejecutar` lanzara; el timeout se probaba con un dict `sin_respuesta`.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_sv5_que_lanza_deja_el_reparto_aplicando`. Re-evaluado: **MUERTO** (1 fallos).

### 22. `services/partes-front/interface_adapters/web/app.py:2468` [booleano]

- Original: `r = {"ok": False, "sin_respuesta": True, "error": str(exc)}`
- Mutado:   `r = {"ok": True, "sin_respuesta": True, "error": str(exc)}`

#### Análisis

> Por qué ningún test lo caza: nadie hacia que `reajuste_ejecutar` lanzara; el timeout se probaba con un dict `sin_respuesta`.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_sv5_que_lanza_deja_el_reparto_aplicando`. Re-evaluado: **MUERTO** (1 fallos).

### 23. `services/partes-front/interface_adapters/web/app.py:2468` [booleano]

- Original: `r = {"ok": False, "sin_respuesta": True, "error": str(exc)}`
- Mutado:   `r = {"ok": False, "sin_respuesta": False, "error": str(exc)}`

#### Análisis

> Por qué ningún test lo caza: nadie hacia que `reajuste_ejecutar` lanzara; el timeout se probaba con un dict `sin_respuesta`.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_sv5_que_lanza_deja_el_reparto_aplicando`. Re-evaluado: **MUERTO** (1 fallos).

### 24. `services/partes-front/interface_adapters/web/app.py:2484` [logico]

- Original: `if not v.get("editable") and v.get("motivo"):`
- Mutado:   `if not v.get("editable") or v.get("motivo"):`

#### Análisis

> Por qué ningún test lo caza: el rechazo de sv5 se comprobaba con `in` y un unico veredicto.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_motivo_del_rechazo_es_el_primero_con_motivo`. Re-evaluado: **MUERTO** (1 fallos).

### 25. `services/partes-front/interface_adapters/web/app.py:2485` [logico]

- Original: `return f"{r.get('error') or 'sv5 rechazo el reajuste'}: " \`
- Mutado:   `return f"{r.get('error') and 'sv5 rechazo el reajuste'}: " \`

#### Análisis

> Por qué ningún test lo caza: el rechazo de sv5 se comprobaba con `in` y un unico veredicto.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_motivo_del_rechazo_es_el_primero_con_motivo`. Re-evaluado: **MUERTO** (1 fallos).

### 26. `services/partes-front/interface_adapters/web/app.py:2496` [booleano]

- Original: `"estado": fila["estado"], "ok": True, "error": None}`
- Mutado:   `"estado": fila["estado"], "ok": False, "error": None}`

#### Análisis

> Por qué ningún test lo caza: la respuesta de «Mantener» solo miraba `estado`.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_mantener_sin_nada_que_registrar_responde_ok`. Re-evaluado: **MUERTO** (1 fallos).

### 27. `services/partes-front/interface_adapters/web/app.py:2500` [comparacion]

- Original: `if r["decision"] == DECISION_APLICAR`
- Mutado:   `if r["decision"] != DECISION_APLICAR`

#### Análisis

> Por qué ningún test lo caza: `_aplicados` solo devuelve repartos `aplicado`, que no bloquean con decision ni sin ella.
> Decisión: **mutante equivalente E7** (ver «Equivalentes», PENDIENTE de aceptacion del humano). Re-evaluado con los tests nuevos: vivo (0 fallos).

### 28. `services/partes-front/interface_adapters/web/app.py:2515` [booleano]

- Original: `return JSONResponse({"ok": True, "repartos": repartos, "grupos": [],`
- Mutado:   `return JSONResponse({"ok": False, "repartos": repartos, "grupos": [],`

#### Análisis

> Por qué ningún test lo caza: la respuesta de «Mantener» solo miraba `estado`.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_mantener_sin_nada_que_registrar_responde_ok`. Re-evaluado: **MUERTO** (1 fallos).

### 29. `services/partes-front/interface_adapters/web/app.py:2516` [logico]

- Original: `"excluidas": cuerpo.get("excluidas") or {},`
- Mutado:   `"excluidas": cuerpo.get("excluidas") and {},`

#### Análisis

> Por qué ningún test lo caza: la respuesta de «Mantener» solo miraba `estado`.
> Decisión: test nuevo en `services/partes-front/tests/test_f046_t22_bordes.py`: `test_f046_t22_mantener_sin_nada_que_registrar_responde_ok`. Re-evaluado: **MUERTO** (1 fallos).

### 30. `services/partes-persistencia/application/services/reajuste_reparto.py:66` [entero]

- Original: `if _tipo(reg) in ("", "normal") and (reg.get("horas") or 0.0) <= 0:`
- Mutado:   `if _tipo(reg) in ("", "normal") and (reg.get("horas") or 0.0) <= 1:`

#### Análisis

> Por qué ningún test lo caza: las ordinarias congeladas de los tests tenian 0 o >= 4 h.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_ordinaria_registrada_con_menos_de_una_hora_es_reajustable`. Re-evaluado: **MUERTO** (2 fallos).

### 31. `services/partes-persistencia/application/services/reajuste_reparto.py:115` [booleano]

- Original: `return json.dumps(datos, sort_keys=True, ensure_ascii=False,`
- Mutado:   `return json.dumps(datos, sort_keys=False, ensure_ascii=False,`

#### Análisis

> Por qué ningún test lo caza: `cambios_a_json` siempre recibia claves ya ordenadas y texto ASCII.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_cambios_a_json_ordena_claves_y_no_escapa`. Re-evaluado: **MUERTO** (1 fallos).

### 32. `services/partes-persistencia/application/services/reajuste_reparto.py:115` [booleano]

- Original: `return json.dumps(datos, sort_keys=True, ensure_ascii=False,`
- Mutado:   `return json.dumps(datos, sort_keys=True, ensure_ascii=True,`

#### Análisis

> Por qué ningún test lo caza: `cambios_a_json` siempre recibia claves ya ordenadas y texto ASCII.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_cambios_a_json_ordena_claves_y_no_escapa`. Re-evaluado: **MUERTO** (1 fallos).

### 33. `services/partes-persistencia/application/services/recurso_conciliador.py:468` [entero]

- Original: `materializacion = {"materializados": 0, "descuadrados": 0}`
- Mutado:   `materializacion = {"materializados": 1, "descuadrados": 0}`

#### Análisis

> Por qué ningún test lo caza: valor inicial que solo se lee tras reasignarse dentro de `if self._reajuste:`.
> Decisión: **mutante equivalente E4** (ver «Equivalentes», PENDIENTE de aceptacion del humano). Re-evaluado con los tests nuevos: vivo (0 fallos).

### 34. `services/partes-persistencia/application/services/recurso_conciliador.py:468` [entero]

- Original: `materializacion = {"materializados": 0, "descuadrados": 0}`
- Mutado:   `materializacion = {"materializados": 0, "descuadrados": 1}`

#### Análisis

> Por qué ningún test lo caza: valor inicial que solo se lee tras reasignarse dentro de `if self._reajuste:`.
> Decisión: **mutante equivalente E4** (ver «Equivalentes», PENDIENTE de aceptacion del humano). Re-evaluado con los tests nuevos: vivo (0 fallos).

### 35. `services/partes-persistencia/application/services/recurso_conciliador.py:553` [entero]

- Original: `guardado = {"propuestos": 0, "mantenidos": 0}`
- Mutado:   `guardado = {"propuestos": 1, "mantenidos": 0}`

#### Análisis

> Por qué ningún test lo caza: valor inicial que solo se lee tras reasignarse dentro de `if self._reajuste:`.
> Decisión: **mutante equivalente E4** (ver «Equivalentes», PENDIENTE de aceptacion del humano). Re-evaluado con los tests nuevos: vivo (0 fallos).

### 36. `services/partes-persistencia/application/services/recurso_conciliador.py:553` [entero]

- Original: `guardado = {"propuestos": 0, "mantenidos": 0}`
- Mutado:   `guardado = {"propuestos": 0, "mantenidos": 1}`

#### Análisis

> Por qué ningún test lo caza: valor inicial que solo se lee tras reasignarse dentro de `if self._reajuste:`.
> Decisión: **mutante equivalente E4** (ver «Equivalentes», PENDIENTE de aceptacion del humano). Re-evaluado con los tests nuevos: vivo (0 fallos).

### 37. `services/partes-persistencia/application/services/recurso_conciliador.py:580` [entero]

- Original: `"repartos_propuestos": int(guardado.get("propuestos", 0)),`
- Mutado:   `"repartos_propuestos": int(guardado.get("propuestos", 1)),`

#### Análisis

> Por qué ningún test lo caza: los dobles del repositorio siempre devolvian todas las claves.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_contadores_que_el_repositorio_no_informa_son_0`. Re-evaluado: **MUERTO** (1 fallos).

### 38. `services/partes-persistencia/application/services/recurso_conciliador.py:582` [entero]

- Original: `materializacion.get("materializados", 0)),`
- Mutado:   `materializacion.get("materializados", 1)),`

#### Análisis

> Por qué ningún test lo caza: los dobles del repositorio siempre devolvian todas las claves.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_contadores_que_el_repositorio_no_informa_son_0`. Re-evaluado: **MUERTO** (1 fallos).

### 39. `services/partes-persistencia/application/services/recurso_conciliador.py:583` [entero]

- Original: `"repartos_mantenidos": int(guardado.get("mantenidos", 0)),`
- Mutado:   `"repartos_mantenidos": int(guardado.get("mantenidos", 1)),`

#### Análisis

> Por qué ningún test lo caza: los dobles del repositorio siempre devolvian todas las claves.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_contadores_que_el_repositorio_no_informa_son_0`. Re-evaluado: **MUERTO** (1 fallos).

### 40. `services/partes-persistencia/application/services/recurso_conciliador.py:585` [entero]

- Original: `materializacion.get("descuadrados", 0)),`
- Mutado:   `materializacion.get("descuadrados", 1)),`

#### Análisis

> Por qué ningún test lo caza: los dobles del repositorio siempre devolvian todas las claves.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_contadores_que_el_repositorio_no_informa_son_0`. Re-evaluado: **MUERTO** (1 fallos).

### 41. `services/partes-persistencia/application/services/recurso_conciliador.py:603` [logico]

- Original: `and clave not in self._grupos_presentes):`
- Mutado:   `or clave not in self._grupos_presentes):`

#### Análisis

> Por qué ningún test lo caza: nadie probaba un reparto vivo cuyo grupo sigue presente pero la pasada no reparte (recurso sin hora extra).
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_grupo_presente_sin_repartir_no_toca_su_reparto`. Re-evaluado: **MUERTO** (1 fallos).

### 42. `services/partes-persistencia/application/services/recurso_conciliador.py:825` [booleano]

- Original: `def _lineas_dia(regs: list[dict], reajuste: bool = False`
- Mutado:   `def _lineas_dia(regs: list[dict], reajuste: bool = True`

#### Análisis

> Por qué ningún test lo caza: `_lineas_dia` solo se llamaba desde la pasada, con el interruptor explicito; apagado, `reajustable` no lo usa F-045.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_lineas_dia_sin_interruptor_nada_es_reajustable`. Re-evaluado: **MUERTO** (1 fallos).

### 43. `services/partes-persistencia/application/services/recurso_conciliador.py:865` [logico]

- Original: `reajustable=(reajuste and clase_linea(`
- Mutado:   `reajustable=(reajuste or clase_linea(`

#### Análisis

> Por qué ningún test lo caza: `_lineas_dia` solo se llamaba desde la pasada, con el interruptor explicito; apagado, `reajustable` no lo usa F-045.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_lineas_dia_sin_interruptor_nada_es_reajustable`. Re-evaluado: **MUERTO** (1 fallos).

### 44. `services/partes-persistencia/application/services/recurso_conciliador.py:899` [comparacion]

- Original: `if fila is not None:`
- Mutado:   `if fila is None:`

#### Análisis

> Por qué ningún test lo caza: R12 solo se probaba sin reparto vivo previo.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_sin_libres_con_reparto_vivo_pasa_a_obsoleto`. Re-evaluado: **MUERTO** (1 fallos).

### 45. `services/partes-persistencia/application/services/reparto_ponderado.py:320` [logico]

- Original: `if ln.extra_auto and ln.base_id in ordinarias:`
- Mutado:   `if ln.extra_auto or ln.base_id in ordinarias:`

#### Análisis

> Por qué ningún test lo caza: ninguna extra automatica huerfana (base en la papelera).
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_extra_automatica_huerfana_pesa_en_su_obra`. Re-evaluado: **MUERTO** (1 fallos).

### 46. `services/partes-persistencia/application/services/reparto_ponderado.py:330` [comparacion]

- Original: `or (base.fija and _trabajado(base) <= 0)):`
- Mutado:   `or (base.fija and _trabajado(base) < 0)):`

#### Análisis

> Por qué ningún test lo caza: ninguna base congelada con trabajado exactamente 0.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_base_registrada_sin_trabajo_es_dura`. Re-evaluado: **MUERTO** (1 fallos).

### 47. `services/partes-persistencia/application/services/reparto_ponderado.py:354` [comparacion]

- Original: `if abs(despues - base.horas) > _EPS:`
- Mutado:   `if abs(despues - base.horas) >= _EPS:`

#### Análisis

> Por qué ningún test lo caza: sin caso en el borde de `_EPS`.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_diferencia_de_eps_en_la_ordinaria_no_es_cambio`. Re-evaluado: **MUERTO** (1 fallos).

### 48. `services/partes-persistencia/application/services/reparto_ponderado.py:357` [entero]

- Original: `extra = round(trabajado - despues, 2)`
- Mutado:   `extra = round(trabajado - despues, 3)`

#### Análisis

> Por qué ningún test lo caza: los trabajados de los tests tenian 1 o 2 decimales.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_la_extra_del_cambio_va_a_2_decimales`. Re-evaluado: **MUERTO** (1 fallos).

### 49. `services/partes-persistencia/application/services/reparto_ponderado.py:360` [comparacion]

- Original: `if abs(extra - actuales[0].horas) > _EPS:`
- Mutado:   `if abs(extra - actuales[0].horas) >= _EPS:`

#### Análisis

> Por qué ningún test lo caza: sin caso en el borde de `_EPS`.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_diferencia_de_eps_en_la_extra_no_es_cambio`. Re-evaluado: **MUERTO** (1 fallos).

### 50. `services/partes-persistencia/application/services/reparto_ponderado.py:364` [comparacion]

- Original: `elif abs(extra) > _EPS:`
- Mutado:   `elif abs(extra) >= _EPS:`

#### Análisis

> Por qué ningún test lo caza: `extra` va redondeada a centesimas: su valor absoluto nunca es exactamente 1e-9.
> Decisión: **mutante equivalente E5** (ver «Equivalentes», PENDIENTE de aceptacion del humano). Re-evaluado con los tests nuevos: vivo (0 fallos).

### 51. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:50` [entero]

- Original: `CLAVE_CANDADO_CONCILIAR = 460460001`
- Mutado:   `CLAVE_CANDADO_CONCILIAR = 460460002`

#### Análisis

> Por qué ningún test lo caza: el test de la clave solo miraba que fuera entera y positiva.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_la_clave_del_candado_no_cambia`. Re-evaluado: **MUERTO** (1 fallos).

### 52. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:446` [booleano]

- Original: `es_incidencia=False,`
- Mutado:   `es_incidencia=True,`

#### Análisis

> Por qué ningún test lo caza: nadie miraba `es_incidencia` de la extra creada.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_extra_materializada_no_es_incidencia`. Re-evaluado: **MUERTO** (1 fallos).

### 53. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:550` [booleano]

- Original: `tomado = False`
- Mutado:   `tomado = True`

#### Análisis

> Por qué ningún test lo caza: nadie hacia fallar la peticion del candado.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_si_falla_al_pedir_el_candado_no_intenta_soltarlo`. Re-evaluado: **MUERTO** (1 fallos).

### 54. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:560` [aritmetico]

- Original: `pasado = _reloj() - inicio`
- Mutado:   `pasado = _reloj() + inicio`

#### Análisis

> Por qué ningún test lo caza: el reloj doble empezaba en 0, donde `-` y `+` coinciden.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_la_espera_se_mide_desde_que_se_empieza`. Re-evaluado: **MUERTO** (1 fallos).

### 55. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:623` [logico]

- Original: `if fila is None or fila.estado != REPARTO_APLICADO:`
- Mutado:   `if fila is None and fila.estado != REPARTO_APLICADO:`

#### Análisis

> Por qué ningún test lo caza: `materializar_repartos` solo lista `aplicado`; la carrera (desaparecido o ya no aplicado al releerlo) no se probaba.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_reparto_inexistente_o_que_ya_no_es_aplicado_se_salta`. Re-evaluado: **MUERTO** (1 fallos).

### 56. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:624` [booleano]

- Original: `return True`
- Mutado:   `return False`

#### Análisis

> Por qué ningún test lo caza: `materializar_repartos` solo lista `aplicado`; la carrera (desaparecido o ya no aplicado al releerlo) no se probaba.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_reparto_inexistente_o_que_ya_no_es_aplicado_se_salta`. Re-evaluado: **MUERTO** (1 fallos).

### 57. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:637` [entero]

- Original: `fila.error = f"descuadre al materializar: {motivo}"[:255]`
- Mutado:   `fila.error = f"descuadre al materializar: {motivo}"[:256]`

#### Análisis

> Por qué ningún test lo caza: ningun motivo de descuadre de mas de 255 caracteres.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_error_de_descuadre_recortado_a_255`. Re-evaluado: **MUERTO** (1 fallos).

### 58. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:657` [booleano]

- Original: `return True`
- Mutado:   `return False`

#### Análisis

> Por qué ningún test lo caza: ninguna carrera que hiciera perder el CAS final.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_si_otro_proceso_gana_el_cas_no_se_escribe_nada`. Re-evaluado: **MUERTO** (1 fallos).

### 59. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:662` [logico]

- Original: `", ".join(f"{c.get('tipo')} {c.get('registro_id') or 'nueva'} "`
- Mutado:   `", ".join(f"{c.get('tipo')} {c.get('registro_id') and 'nueva'} "`

#### Análisis

> Por qué ningún test lo caza: el log de la materializacion no se comprobaba.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_log_de_materializacion_nombra_la_extra_nueva`. Re-evaluado: **MUERTO** (1 fallos).

### 60. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:682` [comparacion]

- Original: `if abs(horas - despues) <= tol:`
- Mutado:   `if abs(horas - despues) < tol:`

#### Análisis

> Por qué ningún test lo caza: sin caso en el borde de la tolerancia de 1e-6.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_linea_ya_en_despues_dentro_de_la_tolerancia`. Re-evaluado: **MUERTO** (1 fallos).

### 61. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:684` [comparacion]

- Original: `if abs(horas - antes) > tol:`
- Mutado:   `if abs(horas - antes) >= tol:`

#### Análisis

> Por qué ningún test lo caza: sin caso en el borde de la tolerancia de 1e-6.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_linea_en_antes_dentro_de_la_tolerancia_se_pone`. Re-evaluado: **MUERTO** (1 fallos).

### 62. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:701` [logico]

- Original: `if abs(float(hecha.horas or 0.0) - despues) > tol:`
- Mutado:   `if abs(float(hecha.horas and 0.0) - despues) > tol:`

#### Análisis

> Por qué ningún test lo caza: ningun reintento con la extra reservada ya creada.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_extra_nueva_ya_creada_con_sus_horas_no_es_descuadre`. Re-evaluado: **MUERTO** (1 fallos).

### 63. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:701` [aritmetico]

- Original: `if abs(float(hecha.horas or 0.0) - despues) > tol:`
- Mutado:   `if abs(float(hecha.horas or 0.0) + despues) > tol:`

#### Análisis

> Por qué ningún test lo caza: ningun reintento con la extra reservada ya creada.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_extra_nueva_ya_creada_con_sus_horas_no_es_descuadre`. Re-evaluado: **MUERTO** (1 fallos).

### 64. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:701` [comparacion]

- Original: `if abs(float(hecha.horas or 0.0) - despues) > tol:`
- Mutado:   `if abs(float(hecha.horas or 0.0) - despues) >= tol:`

#### Análisis

> Por qué ningún test lo caza: sin caso en el borde de la tolerancia de 1e-6.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_extra_nueva_ya_creada_dentro_de_la_tolerancia`. Re-evaluado: **MUERTO** (1 fallos).

### 65. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:771` [logico]

- Original: `and f.estado == REPARTO_PENDIENTE)`
- Mutado:   `or f.estado == REPARTO_PENDIENTE)`

#### Análisis

> Por qué ningún test lo caza: `guardar_repartos` solo se probaba con firma DISTINTA.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_sin_propuesta_misma_firma`, `test_f046_t22_con_propuesta_misma_firma_nace_otro_pendiente`. Re-evaluado: **MUERTO** (4 fallos).

### 66. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:772` [comparacion]

- Original: `or (cambios is None and f.estado in (`
- Mutado:   `or (cambios is not None and f.estado in (`

#### Análisis

> Por qué ningún test lo caza: `guardar_repartos` solo se probaba con firma DISTINTA.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_sin_propuesta_misma_firma`, `test_f046_t22_con_propuesta_misma_firma_nace_otro_pendiente`. Re-evaluado: **MUERTO** (4 fallos).

### 67. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:772` [logico]

- Original: `or (cambios is None and f.estado in (`
- Mutado:   `or (cambios is None or f.estado in (`

#### Análisis

> Por qué ningún test lo caza: `guardar_repartos` solo se probaba con firma DISTINTA.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_sin_propuesta_misma_firma`, `test_f046_t22_con_propuesta_misma_firma_nace_otro_pendiente`. Re-evaluado: **MUERTO** (4 fallos).

### 68. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:818` [logico]

- Original: `rid = c.get("registro_id") or c.get("base_registro_id")`
- Mutado:   `rid = c.get("registro_id") and c.get("base_registro_id")`

#### Análisis

> Por qué ningún test lo caza: solo se comprobaba el enriquecimiento de una linea existente.
> Decisión: test nuevo en `services/partes-persistencia/tests/test_f046_t22_bordes.py`: `test_f046_t22_la_extra_nueva_se_enriquece_desde_su_base`. Re-evaluado: **MUERTO** (1 fallos).

### 69. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:99` [entero]

- Original: `return int(getattr(self._st, "est_parte_activo", 1))`
- Mutado:   `return int(getattr(self._st, "est_parte_activo", 2))`

#### Análisis

> Por qué ningún test lo caza: `SettingsFake` siempre trae el ajuste: el defecto no se usaba.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_sin_ajustes_el_parte_en_registro_es_el_estado_1`. Re-evaluado: **MUERTO** (4 fallos).

### 70. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:102` [entero]

- Original: `return int(getattr(self._st, "sigrid_max_statements", 15))`
- Mutado:   `return int(getattr(self._st, "sigrid_max_statements", 16))`

#### Análisis

> Por qué ningún test lo caza: `SettingsFake` siempre trae el ajuste: el defecto no se usaba.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_sin_ajustes_el_tope_del_lote_es_15_sentencias`. Re-evaluado: **MUERTO** (1 fallos).

### 71. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:105` [booleano]

- Original: `return bool(getattr(self._st, "obra_pruebas_forzar", False))`
- Mutado:   `return bool(getattr(self._st, "obra_pruebas_forzar", True))`

#### Análisis

> Por qué ningún test lo caza: `SettingsFake` siempre trae el ajuste: el defecto no se usaba.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_sin_ajustes_no_es_modo_pruebas`. Re-evaluado: **MUERTO** (1 fallos).

### 72. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:118` [logico]

- Original: `if not (op.fecha_int and op.recurso_ide`
- Mutado:   `if not (op.fecha_int or op.recurso_ide`

#### Análisis

> Por qué ningún test lo caza: ninguna extra nueva incompleta.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_nueva_sin_recurso_no_se_prepara`. Re-evaluado: **MUERTO** (3 fallos).

### 73. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:119` [logico]

- Original: `and (op.obra_ide or op.obra_codigo)):`
- Mutado:   `or (op.obra_ide or op.obra_codigo)):`

#### Análisis

> Por qué ningún test lo caza: ninguna extra nueva incompleta.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_nueva_sin_fecha_no_se_prepara_y_no_es_editable`. Re-evaluado: **MUERTO** (3 fallos).

### 74. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:119` [logico]

- Original: `and (op.obra_ide or op.obra_codigo)):`
- Mutado:   `and (op.obra_ide and op.obra_codigo)):`

#### Análisis

> Por qué ningún test lo caza: las nuevas siempre traian ide Y codigo de obra.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_nueva_con_solo_el_ide_de_obra_se_prepara`, `test_f046_t22_nueva_con_solo_el_codigo_de_obra_se_prepara`. Re-evaluado: **MUERTO** (2 fallos).

### 75. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:150` [entero]

- Original: `if (int(ls.horide or 0) == int(accion.hora_ide or 0)`
- Mutado:   `if (int(ls.horide or 1) == int(accion.hora_ide or 0)`

#### Análisis

> Por qué ningún test lo caza: ninguna linea ajena sin `horide`.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_linea_ajena_sin_codigo_de_hora_no_choca_con_el_codigo_1`. Re-evaluado: **MUERTO** (1 fallos).

### 76. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:150` [entero]

- Original: `if (int(ls.horide or 0) == int(accion.hora_ide or 0)`
- Mutado:   `if (int(ls.horide or 0) == int(accion.hora_ide or 1)`

#### Análisis

> Por qué ningún test lo caza: una accion `escribir` siempre lleva `hora_ide` (el `auxhor.ide` de su `HoraRecurso`).
> Decisión: **mutante equivalente E3** (ver «Equivalentes», PENDIENTE de aceptacion del humano). Re-evaluado con los tests nuevos: vivo (0 fallos).

### 77. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:151` [logico]

- Original: `and not (ls.synckey and ls.synckey in mias)):`
- Mutado:   `or not (ls.synckey and ls.synckey in mias)):`

#### Análisis

> Por qué ningún test lo caza: ninguna linea ajena del mismo dia con OTRO codigo de hora.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_linea_ajena_de_otro_codigo_de_hora_no_choca`. Re-evaluado: **MUERTO** (2 fallos).

### 78. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:151` [logico]

- Original: `and not (ls.synckey and ls.synckey in mias)):`
- Mutado:   `and not (ls.synckey or ls.synckey in mias)):`

#### Análisis

> Por qué ningún test lo caza: ninguna linea ajena con synckey de partes fuera del reajuste.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_otra_linea_nuestra_fuera_del_reajuste_choca`. Re-evaluado: **MUERTO** (1 fallos).

### 79. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:168` [entero]

- Original: `est_parte = (partes.get(int(ls.hmoide or 0), {}).get("est")`
- Mutado:   `est_parte = (partes.get(int(ls.hmoide or 1), {}).get("est")`

#### Análisis

> Por qué ningún test lo caza: ninguna linea sin parte (`hmoide` nulo).
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_linea_sin_parte_no_es_editable`. Re-evaluado: **MUERTO** (1 fallos).

### 80. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:178` [booleano]

- Original: `base_rid, editable=False, motivo=MOTIVO_SIN_BASE)`
- Mutado:   `base_rid, editable=True, motivo=MOTIVO_SIN_BASE)`

#### Análisis

> Por qué ningún test lo caza: el test de la base ausente no miraba el motivo.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_nueva_cuya_base_no_viene_dice_por_que`. Re-evaluado: **MUERTO** (1 fallos).

### 81. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:182` [entero]

- Original: `and partes.get(int(base_ls.hmoide or 0), {}).get("obride")`
- Mutado:   `and partes.get(int(base_ls.hmoide or 1), {}).get("obride")`

#### Análisis

> Por qué ningún test lo caza: `misma_obra` solo decide con la base editable y no aplicada, que exige parte (`hmoide` no nulo).
> Decisión: **mutante equivalente E1** (ver «Equivalentes», PENDIENTE de aceptacion del humano). Re-evaluado con los tests nuevos: vivo (0 fallos).

### 82. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:184` [logico]

- Original: `escribe = (p.accion is not None and p.destino is not None`
- Mutado:   `escribe = (p.accion is not None or p.destino is not None`

#### Análisis

> Por qué ningún test lo caza: el caso no registrable no miraba si se buscaban choques.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_nueva_no_registrable_no_busca_choques`. Re-evaluado: **MUERTO** (1 fallos).

### 83. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:185` [logico]

- Original: `and p.accion.accion == "escribir")`
- Mutado:   `or p.accion.accion == "escribir")`

#### Análisis

> Por qué ningún test lo caza: ninguna nueva sin preparar (con `or` el mutante lee `None.accion`).
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_nueva_sin_fecha_no_se_prepara_y_no_es_editable`. Re-evaluado: **MUERTO** (4 fallos).

### 84. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:209` [logico]

- Original: `ok=ok, ya_aplicada=ok and all(v.ya_aplicada`
- Mutado:   `ok=ok, ya_aplicada=ok or all(v.ya_aplicada`

#### Análisis

> Por qué ningún test lo caza: `comprobar` editable sin aplicar no miraba `ya_aplicada`.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_comprobar_editable_sin_aplicar_no_es_ya_aplicada`. Re-evaluado: **MUERTO** (1 fallos).

### 85. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:227` [not]

- Original: `no = [v for v in ev.veredictos if not v.editable]`
- Mutado:   `no = [v for v in ev.veredictos if v.editable]`

#### Análisis

> Por qué ningún test lo caza: el log del rechazo no se comprobaba.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_log_de_rechazo_nombra_solo_las_no_editables`, `test_f046_t22_log_de_rechazo_nombra_como_mucho_10`. Re-evaluado: **MUERTO** (2 fallos).

### 86. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:232` [entero]

- Original: `for v in no[:10]), usuario)`
- Mutado:   `for v in no[:11]), usuario)`

#### Análisis

> Por qué ningún test lo caza: el log del rechazo no se comprobaba.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_log_de_rechazo_nombra_solo_las_no_editables`, `test_f046_t22_log_de_rechazo_nombra_como_mucho_10`. Re-evaluado: **MUERTO** (1 fallos).

### 87. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:316` [entero]

- Original: `hmoide = int(base.hmoide or 0)`
- Mutado:   `hmoide = int(base.hmoide or 1)`

#### Análisis

> Por qué ningún test lo caza: `_lote` solo ve nuevas editables, cuya base tiene parte.
> Decisión: **mutante equivalente E1** (ver «Equivalentes», PENDIENTE de aceptacion del humano). Re-evaluado con los tests nuevos: vivo (0 fallos).

### 88. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:319` [entero]

- Original: `pos[hmoide] += int(getattr(self._st, "paso_pos", 64))`
- Mutado:   `pos[hmoide] += int(getattr(self._st, "paso_pos", 65))`

#### Análisis

> Por qué ningún test lo caza: `SettingsFake` siempre trae el ajuste: el defecto no se usaba.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_sin_ajustes_la_extra_nueva_va_64_posiciones_despues`. Re-evaluado: **MUERTO** (1 fallos).

### 89. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:322` [logico]

- Original: `assert a is not None and p.destino is not None  # editable`
- Mutado:   `assert a is not None or p.destino is not None  # editable`

#### Análisis

> Por qué ningún test lo caza: el `assert` documenta un invariante que `veredicto_nueva` ya garantiza.
> Decisión: **mutante equivalente E2** (ver «Equivalentes», PENDIENTE de aceptacion del humano). Re-evaluado con los tests nuevos: vivo (0 fallos).

### 90. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:327` [entero]

- Original: `pre=float(a.pre or 0.0), paride=int(a.paride or 0),`
- Mutado:   `pre=float(a.pre or 0.0), paride=int(a.paride or 1),`

#### Análisis

> Por qué ningún test lo caza: todas las nuevas traian partida.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_nueva_sin_partida_entra_con_paride_0`. Re-evaluado: **MUERTO** (1 fallos).

### 91. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:332` [entero]

- Original: `return sentencias, [0] + [1] * (len(sentencias) - 1)`
- Mutado:   `return sentencias, [1] + [1] * (len(sentencias) - 1)`

#### Análisis

> Por qué ningún test lo caza: las filas esperadas solo se usan en el texto del descuadre (se decide releyendo), y el test buscaba «descuadre» con `in`.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_descuadre_dice_filas_y_esperadas`. Re-evaluado: **MUERTO** (2 fallos).

### 92. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:332` [entero]

- Original: `return sentencias, [0] + [1] * (len(sentencias) - 1)`
- Mutado:   `return sentencias, [0] + [2] * (len(sentencias) - 1)`

#### Análisis

> Por qué ningún test lo caza: las filas esperadas solo se usan en el texto del descuadre (se decide releyendo), y el test buscaba «descuadre» con `in`.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_descuadre_dice_filas_y_esperadas`. Re-evaluado: **MUERTO** (2 fallos).

### 93. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:332` [aritmetico]

- Original: `return sentencias, [0] + [1] * (len(sentencias) - 1)`
- Mutado:   `return sentencias, [0] + [1] * (len(sentencias) + 1)`

#### Análisis

> Por qué ningún test lo caza: las filas esperadas solo se usan en el texto del descuadre (se decide releyendo), y el test buscaba «descuadre» con `in`.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_descuadre_dice_filas_y_esperadas`. Re-evaluado: **MUERTO** (2 fallos).

### 94. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:332` [entero]

- Original: `return sentencias, [0] + [1] * (len(sentencias) - 1)`
- Mutado:   `return sentencias, [0] + [1] * (len(sentencias) - 2)`

#### Análisis

> Por qué ningún test lo caza: las filas esperadas solo se usan en el texto del descuadre (se decide releyendo), y el test buscaba «descuadre» con `in`.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_descuadre_dice_filas_y_esperadas`. Re-evaluado: **MUERTO** (2 fallos).

### 95. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:340` [entero]

- Original: `hmoide = int(ls.hmoide or 0) if ls is not None else None`
- Mutado:   `hmoide = int(ls.hmoide or 1) if ls is not None else None`

#### Análisis

> Por qué ningún test lo caza: ninguna linea sin parte ya aplicada.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_linea_sin_parte_ya_aplicada_sale_con_hmoide_0_sin_parte`. Re-evaluado: **MUERTO** (1 fallos).

### 96. `services/partes-transfer/application/pipelines/reajuste_pipeline.py:345` [entero]

- Original: `"parte_cod": ev.partes.get(hmoide or 0, {}).get("cod"),`
- Mutado:   `"parte_cod": ev.partes.get(hmoide or 1, {}).get("cod"),`

#### Análisis

> Por qué ningún test lo caza: ninguna linea sin parte ya aplicada.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_linea_sin_parte_ya_aplicada_sale_con_hmoide_0_sin_parte`. Re-evaluado: **MUERTO** (1 fallos).

### 97. `services/partes-transfer/application/services/reajuste_lineas.py:63` [comparacion]

- Original: `return abs(float(a or 0.0) - float(b or 0.0)) <= TOL + _RUIDO`
- Mutado:   `return abs(float(a or 0.0) - float(b or 0.0)) < TOL + _RUIDO`

#### Análisis

> Por qué ningún test lo caza: sin caso en el borde exacto de la tolerancia.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_la_tolerancia_incluye_el_borde`. Re-evaluado: **MUERTO** (1 fallos).

### 98. `services/partes-transfer/domain/models/registro_models.py:351` [booleano]

- Original: `ya_aplicada: bool = False`
- Mutado:   `ya_aplicada: bool = True`

#### Análisis

> Por qué ningún test lo caza: los defectos de los modelos no se comprobaban.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_defectos_del_resultado_y_del_veredicto`. Re-evaluado: **MUERTO** (1 fallos).

### 99. `services/partes-transfer/domain/models/registro_models.py:355` [booleano]

- Original: `forzada_pruebas: bool = False`
- Mutado:   `forzada_pruebas: bool = True`

#### Análisis

> Por qué ningún test lo caza: los defectos de los modelos no se comprobaban.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_pipeline_bordes.py`: `test_f046_t22_defectos_del_resultado_y_del_veredicto`. Re-evaluado: **MUERTO** (1 fallos).

### 100. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:577` [entero]

- Original: `ide=int(f["ide"]), reside=int(f["reside"] or 0),`
- Mutado:   `ide=int(f["ide"]), reside=int(f["reside"] or 1),`

#### Análisis

> Por qué ningún test lo caza: las lecturas de prueba no traian columnas NULL.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_cliente_bordes.py`: `test_f046_t22_lineas_para_reajuste_con_columnas_nulas`. Re-evaluado: **MUERTO** (1 fallos).

### 101. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:578` [entero]

- Original: `fecha_int=int(f["fec"] or 0),`
- Mutado:   `fecha_int=int(f["fec"] or 1),`

#### Análisis

> Por qué ningún test lo caza: las lecturas de prueba no traian columnas NULL.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_cliente_bordes.py`: `test_f046_t22_lineas_para_reajuste_con_columnas_nulas`. Re-evaluado: **MUERTO** (1 fallos).

### 102. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:579` [entero]

- Original: `horide=int(f["horide"] or 0) or None,`
- Mutado:   `horide=int(f["horide"] or 1) or None,`

#### Análisis

> Por qué ningún test lo caza: las lecturas de prueba no traian columnas NULL.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_cliente_bordes.py`: `test_f046_t22_lineas_para_reajuste_con_columnas_nulas`. Re-evaluado: **MUERTO** (1 fallos).

### 103. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:583` [entero]

- Original: `hmoide=int(f["hmoide"] or 0) or None,`
- Mutado:   `hmoide=int(f["hmoide"] or 1) or None,`

#### Análisis

> Por qué ningún test lo caza: las lecturas de prueba no traian columnas NULL.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_cliente_bordes.py`: `test_f046_t22_lineas_para_reajuste_con_columnas_nulas`. Re-evaluado: **MUERTO** (1 fallos).

### 104. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:605` [entero]

- Original: `"obride": int(f["obride"] or 0) or None}`
- Mutado:   `"obride": int(f["obride"] or 1) or None}`

#### Análisis

> Por qué ningún test lo caza: ningun parte sin obra.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_cliente_bordes.py`: `test_f046_t22_estados_de_partes_sin_obra`. Re-evaluado: **MUERTO** (1 fallos).

### 105. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:685` [entero]

- Original: `cenide = int(getattr(obra, "cenide", 0) or 0)`
- Mutado:   `cenide = int(getattr(obra, "cenide", 1) or 0)`

#### Análisis

> Por qué ningún test lo caza: la obra de prueba siempre tenia centro.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_cliente_bordes.py`: `test_f046_t22_insertar_extra_obra_sin_centro_va_con_cenide_0`. Re-evaluado: **MUERTO** (1 fallos).

### 106. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:685` [entero]

- Original: `cenide = int(getattr(obra, "cenide", 0) or 0)`
- Mutado:   `cenide = int(getattr(obra, "cenide", 0) or 1)`

#### Análisis

> Por qué ningún test lo caza: la obra de prueba siempre tenia centro.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_cliente_bordes.py`: `test_f046_t22_insertar_extra_obra_sin_centro_va_con_cenide_0`. Re-evaluado: **MUERTO** (1 fallos).

### 107. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:696` [entero]

- Original: `int(paride or 0), int(pos), int(fecha_int),`
- Mutado:   `int(paride or 1), int(pos), int(fecha_int),`

#### Análisis

> Por qué ningún test lo caza: el INSERT con `paride=0` solo miraba `tex`.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_cliente_bordes.py`: `test_f046_t22_insertar_extra_sin_partida_va_con_paride_0`. Re-evaluado: **MUERTO** (1 fallos).

### 108. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:698` [entero]

- Original: `round(float(can) * float(pre), 2), int(ano),`
- Mutado:   `round(float(can) * float(pre), 3), int(ano),`

#### Análisis

> Por qué ningún test lo caza: los importes de prueba tenian 2 decimales exactos.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_cliente_bordes.py`: `test_f046_t22_insertar_extra_tot_redondeado_a_2_decimales`. Re-evaluado: **MUERTO** (1 fallos).

### 109. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:715` [entero]

- Original: `" ".join(st["sql"].split())[:150], st["parameters"])`
- Mutado:   `" ".join(st["sql"].split())[:151], st["parameters"])`

#### Análisis

> Por qué ningún test lo caza: el log de `escribir_lote` no se comprobaba.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_cliente_bordes.py`: `test_f046_t22_escribir_lote_log_recorta_el_sql_a_150`. Re-evaluado: **MUERTO** (1 fallos).

### 110. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:717` [aritmetico]

- Original: `timeout=self._timeout + 60,`
- Mutado:   `timeout=self._timeout - 60,`

#### Análisis

> Por qué ningún test lo caza: el doble de la API ignoraba el `timeout`.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_cliente_bordes.py`: `test_f046_t22_escribir_lote_espera_60_s_mas_que_el_timeout`. Re-evaluado: **MUERTO** (1 fallos).

### 111. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:717` [entero]

- Original: `timeout=self._timeout + 60,`
- Mutado:   `timeout=self._timeout + 61,`

#### Análisis

> Por qué ningún test lo caza: el doble de la API ignoraba el `timeout`.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_cliente_bordes.py`: `test_f046_t22_escribir_lote_espera_60_s_mas_que_el_timeout`. Re-evaluado: **MUERTO** (1 fallos).

### 112. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:721` [entero]

- Original: `f"{r.text[:500]}")`
- Mutado:   `f"{r.text[:501]}")`

#### Análisis

> Por qué ningún test lo caza: ningun error HTTP largo.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_cliente_bordes.py`: `test_f046_t22_escribir_lote_error_http_recorta_a_500`. Re-evaluado: **MUERTO** (1 fallos).

### 113. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:723` [logico]

- Original: `if not body.get("ok") or not body.get("committed"):`
- Mutado:   `if not body.get("ok") and not body.get("committed"):`

#### Análisis

> Por qué ningún test lo caza: el caso ok-sin-committed fallaba igual por otra via (sin filas) y el test no miraba el mensaje.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_cliente_bordes.py`: `test_f046_t22_escribir_lote_ok_sin_committed_no_esta_confirmada`. Re-evaluado: **MUERTO** (1 fallos).

### 114. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:724` [entero]

- Original: `raise RuntimeError(f"escritura no confirmada: {str(body)[:400]}")`
- Mutado:   `raise RuntimeError(f"escritura no confirmada: {str(body)[:401]}")`

#### Análisis

> Por qué ningún test lo caza: ninguna respuesta larga sin confirmar.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_cliente_bordes.py`: `test_f046_t22_escribir_lote_no_confirmada_recorta_a_400`. Re-evaluado: **MUERTO** (1 fallos).

### 115. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:730` [entero]

- Original: `f"{str(body)[:400]}")`
- Mutado:   `f"{str(body)[:401]}")`

#### Análisis

> Por qué ningún test lo caza: ninguna respuesta larga sin filas.
> Decisión: test nuevo en `services/partes-transfer/tests/test_f046_t22_cliente_bordes.py`: `test_f046_t22_escribir_lote_sin_filas_recorta_a_400`. Re-evaluado: **MUERTO** (1 fallos).

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


### Re-evaluación de los timeouts (T22, 2026-10-17)

Los 14 son consecutivos (#92–#105 de la campaña) y todos de `iniciar_aplicacion`
(`parte_repository.py:3208–3257`). Re-evaluados uno a uno con
`progress/redirigir_mutantes_F-046.py` (tests `test_f046_*` de sv4, un proceso, sin `-x`):
**los 14 MUEREN** (entre 1 y varios fallos cada uno) y ninguno se cuelga; los 43 mutantes de
sv4 re-evaluados (29 supervivientes + 14 timeouts) tardaron 27 min en total, ~37 s por mutante.
No es un bucle: con 6 workers la suite completa de sv4 mide ~520 s de línea base y el timeout
efectivo era ~1040 s; un mutante que solo matan los tests de F-046 (que van casi al final de la
suite) cruza ese límite en cuanto la máquina, compartida con campañas de otros proyectos, se
carga. Se cuentan como **muertos**.

## Equivalentes (ACEPTADOS por el humano el 2026-10-18)

Once mutantes en siete grupos (RM5). Ninguno puede matarse: la línea mutada solo cambia algo en
una situación que el código no alcanza. Cada uno tiene una **demostración ejecutable** que fija
esa imposibilidad (pasa con el original y con el mutante, por construcción; si un cambio futuro la
hiciera alcanzable, fallaría). Ficheros: `services/partes-transfer/tests/test_f046_t22_equivalentes.py`,
`services/partes-persistencia/tests/test_f046_t22_equivalentes.py` y
`services/partes-front/tests/test_f046_t22_equivalentes.py`. **Aceptados por el humano el 2026-10-18** («acepto los equivalentes»).

| Id | Mutante(s) | Por qué ningún test puede distinguirlo | Demostración |
|---|---|---|---|
| E1 | #81 `reajuste_pipeline.py:182` y #87 `:316` (`hmoide or 0` → `or 1`) | `misma_obra` solo decide si la base es editable y no está ya aplicada, lo que exige su parte En registro, es decir `hmoide` no nulo; `_lote` solo recibe nuevas editables. Con la base sin parte la nueva se rechaza antes (`MOTIVO_BASE_NO_EDITABLE` o `MOTIVO_PARCIAL`) y no hay lote. | `test_f046_t22_eq_base_sin_parte_nunca_llega_a_misma_obra_ni_al_lote` (sv5) |
| E2 | #89 `reajuste_pipeline.py:322` (`assert a and destino` → `or`) | El `assert` documenta un invariante: `veredicto_nueva` solo da editable con acción `escribir` (no None) y `misma_obra`, que en `_evaluar` exige `destino` no None. En `_lote` las dos condiciones son siempre ciertas: `and` y `or` valen lo mismo. | `test_f046_t22_eq_nueva_editable_exige_accion_escribir_y_misma_obra` (sv5) |
| E3 | #76 `reajuste_pipeline.py:150` (`accion.hora_ide or 0` → `or 1`) | `_choques` solo recibe acciones `escribir`, y la de una extra lleva `hora_ide = HoraRecurso.horide` (el `auxhor.ide` de Sigrid, IDENTITY ≥ 1). Sin código de hora extra la acción no es `escribir`. **Equivalencia de dominio**: depende de que Sigrid no tenga un `auxhor.ide` 0. | `test_f046_t22_eq_toda_extra_escribible_lleva_codigo_de_hora` (sv5) |
| E4 | #33, #34 `recurso_conciliador.py:468` y #35, #36 `:553` (contadores iniciales 0 → 1) | Almacenes muertos: `materializacion` y `guardado` se reasignan dentro de `if self._reajuste:` y solo se leen dentro de otro `if self._reajuste:`; apagado no se leen. El valor inicial no llega nunca al resultado. | `test_f046_t22_eq_contadores_iniciales_son_almacenes_muertos` (AST de `_pasada`) y `test_f046_t22_eq_apagado_no_hay_contadores_del_reajuste` (sv3) |
| E5 | #50 `reparto_ponderado.py:364` (`abs(extra) > _EPS` → `>=`) | `extra = round(trabajado - despues, 2)`: su valor absoluto es 0 o ≥ 0,01, nunca exactamente `_EPS` = 1e-9. | `test_f046_t22_eq_una_extra_redondeada_a_centesimas_nunca_vale_eps` (barrido de 200 000 valores, sv3) |
| E6 | #15 `web/app.py:2379` (`{"ok": False, …}` → `True` al fallar `comprobar`) | `_veredictos_reparto` solo lee `veredictos` y `error` de la respuesta; la clave `ok` del dict que fabrica no se lee nunca. | `test_f046_t22_eq_veredictos_reparto_no_lee_ok_de_la_respuesta` (AST, sv4) |
| E7 | #27 `web/app.py:2500` (`_aplicados`: `decision == aplicar` → `!=`) | `_aplicados` solo devuelve repartos `aplicado`, que no están en `ESTADOS_BLOQUEAN`: sus líneas viajan con decisión o sin ella, y `aplicado` solo sale de «Aplicar». Original y mutante dan las mismas exclusiones. | `test_f046_t22_eq_un_reparto_aplicado_no_excluye_con_o_sin_decision` (sv4) |

## Cierre de T22 (2026-10-17)

| Métrica | Valor |
|---|---|
| Mutantes | 565 |
| Muertos en la campaña | 436 |
| Timeouts re-evaluados ⇒ muertos | 14 |
| Supervivientes matados por tests nuevos (re-evaluados uno a uno) | 104 |
| **Muertos en total** | **554 / 565 (98,1 %)** |
| Equivalentes con demostración, ACEPTADOS por el humano (2026-10-18) | 11 (E1–E7) |
| Supervivientes sin resolver | 0 |
| Bugs o desviaciones de la spec revelados | 0 |

Tests nuevos (casos de pytest; todos `test_f046_t22_*`): sv5 `tests/test_f046_t22_pipeline_bordes.py` (24),
`tests/test_f046_t22_cliente_bordes.py` (11); sv3 `tests/test_f046_t22_bordes.py` (32); sv4
`tests/test_f046_t22_bordes.py` (22); demostraciones de equivalentes en
`tests/test_f046_t22_equivalentes.py` de cada servicio (4 + 3 + 2).

Observaciones (no son bugs; no se cambia el comportamiento):

- **O1** (sv3, `_materializar_uno`): un reparto que desaparece, deja de estar `aplicado` o pierde
  el CAS final entre listarlo y materializarlo devuelve `True` y suma en `materializados`,
  aunque no se toque nada. Solo infla el contador de la pasada en una carrera.
- **O2** (sv5, `_resultado`): una línea ya aplicada cuyo `hmoide` es NULL en Sigrid sale con
  `hmoide: 0` (no `None`) y sin `parte_cod`. En Sigrid toda línea de `hmores` tiene parte, así
  que no se espera en producción.
- **O3** (sv4, `_aplicados`): pasar los repartos `aplicado` a `_preparar_registro` es redundante
  (`aplicado` no bloquea); es la razón de E7.
