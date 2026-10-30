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

## Resumen del análisis (implementer, 2026-10-29)

| Fichero | Supervivientes | Mata un test nuevo | Candidato a equivalente |
|---|---|---|---|
| sv4 `interface_adapters/web/app.py` | 31 | 30 | 1 (#31) |
| sv3 `infrastructure/database/orm_models.py` | 22 | 22 | 0 |
| sv4 `application/services/franquicia.py` | 16 | 14 | 2 (#3, #10) |
| sv5 `application/pipelines/franquicia_pipeline.py` | 13 | 6 | 7 (#79, #80, #84, #86, #87, #89, #90) |
| sv4 `infrastructure/database/parte_repository.py` | 9 | 7 | 2 (#17, #19) |
| sv5 `application/services/franquicia.py` | 7 | 6 | 1 (#95) |
| sv5 `interface_adapters/api/app.py` | 3 | 3 | 0 |
| sv5 `application/pipelines/registro_pipeline.py` | 1 | 0 | 1 (#92) |
| **Total** | **102** | **88** | **14** |

Los 14 equivalentes son **propuestas**: solo los acepta el humano. De los
8 timeouts, ninguno cuelga; dos (t1, t3) no los cazaba la suite de F-056 y
tienen test nuevo (§ Timeouts). Sin cambios en el código de producción: todo
son tests. La campaña no se ha relanzado (los números de arriba son los de
3ba3403).

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/franquicia.py:97` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ningún test intentaba cambiar un `Periodo`/`DiaAjuste` ni los usaba como clave.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_franquicia.py::test_f056_periodo_y_dia_de_ajuste_son_valores_inmutables`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 2. `services/partes-front/application/services/franquicia.py:113` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ningún test intentaba cambiar un `Periodo`/`DiaAjuste` ni los usaba como clave.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_franquicia.py::test_f056_periodo_y_dia_de_ajuste_son_valores_inmutables`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 3. `services/partes-front/application/services/franquicia.py:128` [entero]

- Original: `fi = int(valor or 0)`
- Mutado:   `fi = int(valor or 1)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: con `valor` vacío, `fi` vale 0 o 1.
> Decisión: CANDIDATO A EQUIVALENTE (lo acepta o no el humano): `fecha_de_int` devuelve None en los dos casos: `date(0, 0, 0)` y `date(0, 0, 1)` lanzan `ValueError` por el año 0, que se captura.

### 4. `services/partes-front/application/services/franquicia.py:174` [logico]

- Original: `and bool(linea.get("obra_ide") or linea.get("obra_codigo")))`
- Mutado:   `and bool(linea.get("obra_ide") and linea.get("obra_codigo")))`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: todas las líneas de los tests traían obra por ide Y por código.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_franquicia.py::test_f056_r7_obra_solo_por_ide_o_solo_por_codigo_es_trabajo`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 5. `services/partes-front/application/services/franquicia.py:196` [entero]

- Original: `ultimo = max(int(x.get("fecha_int") or 0) for x in periodo)`
- Mutado:   `ultimo = max(int(x.get("fecha_int") or 1) for x in periodo)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ninguna línea del periodo llegaba sin `fecha_int`.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_franquicia.py::test_f056_r7_lineas_del_periodo_sin_fecha_siguen_eligiendo_obra`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 6. `services/partes-front/application/services/franquicia.py:197` [entero]

- Original: `base = [x for x in periodo if int(x.get("fecha_int") or 0) == ultimo]`
- Mutado:   `base = [x for x in periodo if int(x.get("fecha_int") or 1) == ultimo]`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ninguna línea del periodo llegaba sin `fecha_int`.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_franquicia.py::test_f056_r7_lineas_del_periodo_sin_fecha_siguen_eligiendo_obra`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 7. `services/partes-front/application/services/franquicia.py:208` [entero]

- Original: `int(x.get("registro_id") or 0)))`
- Mutado:   `int(x.get("registro_id") or 1)))`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ningún empate de partida tenía una línea sin `registro_id`.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_franquicia.py::test_f056_r7_partida_empate_sin_registro_id_va_primero`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 8. `services/partes-front/application/services/franquicia.py:217` [entero]

- Original: `recursos = {int(x.get("recurso_ide") or 0) for x in lineas_periodo`
- Mutado:   `recursos = {int(x.get("recurso_ide") or 1) for x in lineas_periodo`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ninguna extra llegaba sin recurso junto a la del recurso 1.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_franquicia.py::test_f056_r12_extra_sin_recurso_cuenta_como_otro_recurso`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 9. `services/partes-front/application/services/franquicia.py:233` [entero]

- Original: `and int(a.get("recurso_ide") or 0) == int(recurso_ide)`
- Mutado:   `and int(a.get("recurso_ide") or 1) == int(recurso_ide)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ninguna acción llegaba sin `recurso_ide` con el recurso 1.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_franquicia.py::test_f056_r9_accion_sin_recurso_no_es_del_recurso_1`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 10. `services/partes-front/application/services/franquicia.py:235` [entero]

- Original: `and periodo.inicio_int <= int(a.get("fecha_int") or 0)`
- Mutado:   `and periodo.inicio_int <= int(a.get("fecha_int") or 1)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: con `fecha_int` vacío la acción compara 0 o 1 contra `periodo.inicio_int`.
> Decisión: CANDIDATO A EQUIVALENTE (lo acepta o no el humano): `inicio_int` es `fecha_a_int` de una fecha real (>= 10101), así que 0 y 1 quedan fuera del periodo igual y la acción no suma en ningún caso.

### 11. `services/partes-front/application/services/franquicia.py:263` [entero]

- Original: `rec = int(x.get("recurso_ide") or 0)`
- Mutado:   `rec = int(x.get("recurso_ide") or 1)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ninguna línea sin recurso llegaba a `candidatos` con el recurso 1 activo.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_franquicia.py::test_f056_r9_linea_sin_recurso_no_es_candidata_del_recurso_1`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 12. `services/partes-front/application/services/franquicia.py:336` [logico]

- Original: `dia = c.get("dia") or fecha_de_int(prop.get("fecha_int"))`
- Mutado:   `dia = c.get("dia") and fecha_de_int(prop.get("fecha_int"))`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: en los tests el día del candidato y el de la propuesta eran el mismo.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_franquicia.py::test_f056_r9_bloque_dia_del_candidato_y_si_no_el_de_la_propuesta`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 13. `services/partes-front/application/services/franquicia.py:338` [logico]

- Original: `if (prop.get("obra_ide") or prop.get("obra_codigo")) else None)`
- Mutado:   `if (prop.get("obra_ide") and prop.get("obra_codigo")) else None)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: la propuesta de los tests traía siempre ide y código de obra.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_franquicia.py::test_f056_r9_bloque_obra_solo_por_ide_o_por_codigo`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 14. `services/partes-front/application/services/franquicia.py:355` [logico]

- Original: `"parte_cod": sv5.get("parte_cod") or fila.get("parte_cod"),`
- Mutado:   `"parte_cod": sv5.get("parte_cod") and fila.get("parte_cod"),`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ningún test miraba `parte_cod` de un item sin fila.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_franquicia.py::test_f056_r9_bloque_parte_de_sv5_sin_fila`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 15. `services/partes-front/application/services/franquicia.py:401` [entero]

- Original: `if rec <= 0 or periodo is None:`
- Mutado:   `if rec <= 1 or periodo is None:`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: los recursos de los tests eran 501/502; nadie probaba el 1.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_franquicia.py::test_f056_r15_el_recurso_1_es_valido`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 16. `services/partes-front/application/services/franquicia.py:459` [entero]

- Original: `"fin": periodo.fin_int, "fecha_int": int(datos.get("fecha_int") or 0),`
- Mutado:   `"fin": periodo.fin_int, "fecha_int": int(datos.get("fecha_int") or 1),`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: el payload siempre llevaba `fecha_int`.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_franquicia.py::test_f056_r9_payload_sin_dia_va_con_fecha_0`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 17. `services/partes-front/infrastructure/database/parte_repository.py:4071` [entero]

- Original: `"registro_id": x.id, "fecha_int": int(x.fecha_int or 0),`
- Mutado:   `"registro_id": x.id, "fecha_int": int(x.fecha_int or 1),`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: `fecha_int` de las líneas devueltas nunca es vacío.
> Decisión: CANDIDATO A EQUIVALENTE (lo acepta o no el humano): la consulta filtra `fecha_int >= inicio AND <= fin` (un NULL no cumple ninguna comparación) y todos los llamantes pasan `periodo.inicio_int` (>= 10101), así que `x.fecha_int or ...` nunca llega a la rama del defecto.

### 18. `services/partes-front/infrastructure/database/parte_repository.py:4091` [entero]

- Original: `for i in range(0, len(ids), 500):`
- Mutado:   `for i in range(0, len(ids), 501):`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ningún test pasaba más de 500 líneas.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r15_repositorio_recurso_fechas_en_lotes_sin_perder_ninguna`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 19. `services/partes-front/infrastructure/database/parte_repository.py:4096` [entero]

- Original: `.where(ParteRegistroOrm.id.in_(ids[i:i + 500]))`
- Mutado:   `.where(ParteRegistroOrm.id.in_(ids[i:i + 501]))`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: con el paso de 500 y el trozo de 501, los lotes se solapan en un id.
> Decisión: CANDIDATO A EQUIVALENTE (lo acepta o no el humano): el resultado se acumula en un `set`, así que el id repetido no cambia nada; la única diferencia es un `IN` de 501 parámetros en vez de 500, lejos de cualquier límite.

### 20. `services/partes-front/infrastructure/database/parte_repository.py:4101` [entero]

- Original: `return sorted((int(r), int(f or 0)) for r, f in out)`
- Mutado:   `return sorted((int(r), int(f or 1)) for r, f in out)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ninguna línea de los tests llegaba sin `fecha_int`.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r15_repositorio_linea_sin_fecha_sale_con_fecha_0`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 21. `services/partes-front/infrastructure/database/parte_repository.py:4156` [entero]

- Original: `"obra_ide": int(datos.get("obra_ide") or 0),`
- Mutado:   `"obra_ide": int(datos.get("obra_ide") or 1),`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: la propuesta de los tests traía siempre `obra_ide`.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r8_repositorio_ajustar_con_obra_solo_por_codigo`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 22. `services/partes-front/infrastructure/database/parte_repository.py:4164` [logico]

- Original: `and (datos.get("obra_ide") or datos.get("obra_codigo")))`
- Mutado:   `and (datos.get("obra_ide") and datos.get("obra_codigo")))`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: la propuesta de los tests traía siempre `obra_ide`.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r8_repositorio_ajustar_con_obra_solo_por_codigo`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 23. `services/partes-front/infrastructure/database/parte_repository.py:4282` [comparacion]

- Original: `if res.rowcount == 1:`
- Mutado:   `if res.rowcount != 1:`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: la condición y el sufijo solo afectan a la línea de log, y ningún test la miraba.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r17_repositorio_cerrar_deja_su_log_solo_si_cambia`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 24. `services/partes-front/infrastructure/database/parte_repository.py:4282` [entero]

- Original: `if res.rowcount == 1:`
- Mutado:   `if res.rowcount == 2:`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: la condición y el sufijo solo afectan a la línea de log, y ningún test la miraba.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r17_repositorio_cerrar_deja_su_log_solo_si_cambia`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 25. `services/partes-front/infrastructure/database/parte_repository.py:4285` [not]

- Original: `f": {valores['error']}" if not ok else "")`
- Mutado:   `f": {valores['error']}" if ok else "")`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: la condición y el sufijo solo afectan a la línea de log, y ningún test la miraba.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r17_repositorio_cerrar_deja_su_log_solo_si_cambia`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 26. `services/partes-front/interface_adapters/web/app.py:2740` [entero]

- Original: `for i in range(0, len(recursos), 500):`
- Mutado:   `for i in range(0, len(recursos), 501):`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ningún preflight tenía más de 500 recursos.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r43_preflight_pide_la_franquicia_en_lotes_de_500`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 27. `services/partes-front/interface_adapters/web/app.py:2743` [entero]

- Original: `recursos[i:i + 500],`
- Mutado:   `recursos[i:i + 501],`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ningún preflight tenía más de 500 recursos.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r43_preflight_pide_la_franquicia_en_lotes_de_500`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 28. `services/partes-front/interface_adapters/web/app.py:2746` [booleano]

- Original: `logger.warning("[franquicia] /recursos fallo", exc_info=True)`
- Mutado:   `logger.warning("[franquicia] /recursos fallo", exc_info=False)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: los tests miraban el aviso, no la traza del log.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r44_preflight_fallo_de_recursos_con_traza`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 29. `services/partes-front/interface_adapters/web/app.py:2764` [comparacion]

- Original: `if x.get("candef") is not None), None)`
- Mutado:   `if x.get("candef") is None), None)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sin candef en las líneas, el mutante (candef siempre None) daba el mismo día; hace falta un candef que deje el viernes a 0 h.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r5_preflight_dia_de_ajuste_con_el_candef_del_trabajador`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 30. `services/partes-front/interface_adapters/web/app.py:2786` [comparacion]

- Original: `[x for x in lineas_p if x["fecha_int"] == dia_int], lineas_p)`
- Mutado:   `[x for x in lineas_p if x["fecha_int"] != dia_int], lineas_p)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: en los tests solo había líneas el día de ajuste, y la reserva «último día con trabajo» elegía ese mismo día.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r7_preflight_obra_de_las_lineas_del_dia_de_ajuste`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 31. `services/partes-front/interface_adapters/web/app.py:2815` [logico]

- Original: `if c["tipo"] in (fq.TIPO_RECHAZADO, fq.INVALIDA) or c.get("motivo"):`
- Mutado:   `if c["tipo"] in (fq.TIPO_RECHAZADO, fq.INVALIDA) and c.get("motivo"):`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: `A or B` y `A and B` solo difieren con un candidato NO informativo que trae motivo.
> Decisión: CANDIDATO A EQUIVALENTE (lo acepta o no el humano): un informativo siempre trae motivo (TIPO_RECHAZADO lleva MOTIVO_RECHAZADO; INVALIDA, el del día o MOTIVO_INVALIDA). El único caso es NUEVO con el calendario no fiable (R6). Ahí el mutante sigue adelante, pero sin día `_propuesta` da None: no llama a sv5, no guarda propuesta y deja un motivo propio. `_item` usa primero el del candidato, así que la salida es idéntica. Las líneas del periodo ya las había leído `dia_de` (caché por petición), así que tampoco hay una lectura de más.

### 32. `services/partes-front/interface_adapters/web/app.py:2835` [booleano]

- Original: `exc_info=True)`
- Mutado:   `exc_info=False)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: los tests miraban el motivo, no la traza del log.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r14_preflight_fallo_de_comprobar_con_traza`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 33. `services/partes-front/interface_adapters/web/app.py:2846` [entero]

- Original: `recursos = sorted({int(x.get("recurso_ide") or 0)`
- Mutado:   `recursos = sorted({int(x.get("recurso_ide") or 1)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ninguna línea de la selección llegaba sin recurso.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r9_preflight_linea_sin_recurso_no_estorba`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 34. `services/partes-front/interface_adapters/web/app.py:2847` [entero]

- Original: `for x in lineas} - {0})`
- Mutado:   `for x in lineas} - {1})`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: nadie probaba el recurso 1 en el preflight.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r10_preflight_el_recurso_1_tiene_su_ajuste`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 35. `services/partes-front/interface_adapters/web/app.py:2854` [logico]

- Original: `if d is not None and int(x.get("recurso_ide") or 0) > 0:`
- Mutado:   `if d is not None or int(x.get("recurso_ide") or 0) > 0:`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ninguna línea de la selección llegaba sin recurso.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r9_preflight_linea_sin_recurso_no_estorba`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 36. `services/partes-front/interface_adapters/web/app.py:2854` [entero]

- Original: `if d is not None and int(x.get("recurso_ide") or 0) > 0:`
- Mutado:   `if d is not None and int(x.get("recurso_ide") or 1) > 0:`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ninguna línea de la selección llegaba sin recurso.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r9_preflight_linea_sin_recurso_no_estorba`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 37. `services/partes-front/interface_adapters/web/app.py:2854` [comparacion]

- Original: `if d is not None and int(x.get("recurso_ide") or 0) > 0:`
- Mutado:   `if d is not None and int(x.get("recurso_ide") or 0) >= 0:`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ninguna línea de la selección llegaba sin recurso.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r9_preflight_linea_sin_recurso_no_estorba`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 38. `services/partes-front/interface_adapters/web/app.py:2854` [entero]

- Original: `if d is not None and int(x.get("recurso_ide") or 0) > 0:`
- Mutado:   `if d is not None and int(x.get("recurso_ide") or 0) > 1:`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: nadie probaba el recurso 1 en el preflight.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r10_preflight_el_recurso_1_tiene_su_ajuste`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 39. `services/partes-front/interface_adapters/web/app.py:2868` [booleano]

- Original: `exc_info=True)`
- Mutado:   `exc_info=False)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: el test del fallo interno miraba el aviso, no la traza.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r14_preflight_fallo_interno_con_traza`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 40. `services/partes-front/interface_adapters/web/app.py:2888` [logico]

- Original: `if d is not None and rec:`
- Mutado:   `if d is not None or rec:`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ninguna selección con decisiones traía una línea sin fecha.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r15_ejecutar_con_una_linea_sin_fecha_en_la_seleccion`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 41. `services/partes-front/interface_adapters/web/app.py:2916` [comparacion]

- Original: `if (decision == fq.AJUSTAR and datos is None`
- Mutado:   `if (decision != fq.AJUSTAR and datos is None`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: «No ajustar» solo se probaba con propuesta calculable; el 409 del mutante sale cuando no la hay.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r16_ejecutar_no_ajustar_sin_propuesta_si_se_guarda`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 42. `services/partes-front/interface_adapters/web/app.py:2917` [not]

- Original: `and not fila.get("fecha_int")):`
- Mutado:   `and fila.get("fecha_int")):`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: «Ajustar» tras un rechazo con día solo se probaba con propuesta calculable.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r8_ejecutar_ajustar_tras_rechazo_con_dia_sin_calendario`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 43. `services/partes-front/interface_adapters/web/app.py:2954` [booleano]

- Original: `respuesta = {"ok": True, "grupos": [], "franquicias": franquicias,`
- Mutado:   `respuesta = {"ok": False, "grupos": [], "franquicias": franquicias,`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: el test de «sin líneas que registrar» no miraba `ok` ni `excluidas`.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r15_sin_lineas_que_registrar_ok_y_las_excluidas`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 44. `services/partes-front/interface_adapters/web/app.py:2955` [logico]

- Original: `"excluidas": cuerpo.get("excluidas") or {},`
- Mutado:   `"excluidas": cuerpo.get("excluidas") and {},`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: el test de «sin líneas que registrar» no miraba `ok` ni `excluidas`.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r15_sin_lineas_que_registrar_ok_y_las_excluidas`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 45. `services/partes-front/interface_adapters/web/app.py:2969` [logico]

- Original: `if mode != MODE_NOMINA or periodo is None or not recursos:`
- Mutado:   `if mode != MODE_NOMINA or periodo is None and not recursos:`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: siempre había periodo; nadie abría la vista con líneas sin fecha.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_vista.py::test_f056_r20_vista_sin_periodo_no_pregunta_a_sv5`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 46. `services/partes-front/interface_adapters/web/app.py:2980` [booleano]

- Original: `exc_info=True)`
- Mutado:   `exc_info=False)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: el test del fallo de la vista miraba el aviso, no la traza.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_vista.py::test_f056_r20_vista_fallo_propio_con_traza`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 47. `services/partes-front/interface_adapters/web/app.py:2983` [booleano]

- Original: `@app.post("/api/franquicia/decidir", include_in_schema=False)`
- Mutado:   `@app.post("/api/franquicia/decidir", include_in_schema=True)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ningún test miraba el esquema OpenAPI de estas rutas.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_vista.py::test_f056_r21_rutas_de_franquicia_fuera_del_esquema`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 48. `services/partes-front/interface_adapters/web/app.py:2993` [booleano]

- Original: `{"ok": False, "error": "registro en Sigrid no configurado "`
- Mutado:   `{"ok": True, "error": "registro en Sigrid no configurado "`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: el 503 de `decidir` solo comprobaba el código, y el de `aplicar` no tenía test.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_vista.py::test_f056_r21_sin_sv5_configurado_es_503_ok_false`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 49. `services/partes-front/interface_adapters/web/app.py:3006` [entero]

- Original: `if not any(int(x.get("recurso_ide") or 0) == rec`
- Mutado:   `if not any(int(x.get("recurso_ide") or 1) == rec`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: nadie probaba el recurso 1 con líneas sin recurso de su misma persona (por DNI) en el periodo.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_vista.py::test_f056_r45_decidir_linea_sin_recurso_no_es_del_recurso_1`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 50. `services/partes-front/interface_adapters/web/app.py:3017` [booleano]

- Original: `@app.post("/api/franquicia/{ajuste_id}/aplicar", include_in_schema=False)`
- Mutado:   `@app.post("/api/franquicia/{ajuste_id}/aplicar", include_in_schema=True)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ningún test miraba el esquema OpenAPI de estas rutas.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_vista.py::test_f056_r21_rutas_de_franquicia_fuera_del_esquema`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 51. `services/partes-front/interface_adapters/web/app.py:3026` [booleano]

- Original: `{"ok": False, "error": "registro en Sigrid no configurado "`
- Mutado:   `{"ok": True, "error": "registro en Sigrid no configurado "`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: el 503 de `decidir` solo comprobaba el código, y el de `aplicar` no tenía test.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_vista.py::test_f056_r21_sin_sv5_configurado_es_503_ok_false`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 52. `services/partes-front/interface_adapters/web/app.py:3028` [entero]

- Original: `status_code=503)`
- Mutado:   `status_code=504)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: el 503 de `decidir` solo comprobaba el código, y el de `aplicar` no tenía test.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_vista.py::test_f056_r21_sin_sv5_configurado_es_503_ok_false`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 53. `services/partes-front/interface_adapters/web/app.py:3033` [booleano]

- Original: `{"ok": False, "error": "ajuste de franquicia no encontrado"},`
- Mutado:   `{"ok": True, "error": "ajuste de franquicia no encontrado"},`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: el test del 404 solo miraba el código.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r17_aplicar_inexistente_dice_ok_false`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 54. `services/partes-front/interface_adapters/web/app.py:3050` [booleano]

- Original: `exc_info=True)`
- Mutado:   `exc_info=False)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: el test sin respuesta miraba el error, no la traza.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r19_aplicar_sin_respuesta_con_traza`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 55. `services/partes-front/interface_adapters/web/app.py:3051` [booleano]

- Original: `r = {"ok": False, "sin_respuesta": True, "error": str(exc)}`
- Mutado:   `r = {"ok": False, "sin_respuesta": False, "error": str(exc)}`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: el test sin respuesta partía de una fila sin datos previos de sv5, y pisarlos con None no se notaba.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r19_aplicar_sin_respuesta_conserva_lo_que_dijo_sv5`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 56. `services/partes-front/interface_adapters/web/app.py:3059` [logico]

- Original: `"ok": ok and ajuste["estado"] == fq.APLICADO, "error": error,`
- Mutado:   `"ok": ok or ajuste["estado"] == fq.APLICADO, "error": error,`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: nadie probaba que sv5 dijera que no mientras otro usuario dejaba la fila `aplicado`.
> Decisión: TEST NUEVO `services/partes-front/tests/test_f056_decisiones.py::test_f056_r17_aplicar_que_falla_no_es_ok_aunque_otro_lo_aplicara`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 57. `services/partes-persistencia/infrastructure/database/orm_models.py:620` [booleano]

- Original: `unique=True),`
- Mutado:   `unique=False),`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 58. `services/partes-persistencia/infrastructure/database/orm_models.py:624` [booleano]

- Original: `id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)`
- Mutado:   `id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 59. `services/partes-persistencia/infrastructure/database/orm_models.py:626` [booleano]

- Original: `Integer, nullable=False, server_default="0"`
- Mutado:   `Integer, nullable=True, server_default="0"`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 60. `services/partes-persistencia/infrastructure/database/orm_models.py:630` [entero]

- Original: `String(7), nullable=False, server_default=""`
- Mutado:   `String(8), nullable=False, server_default=""`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 61. `services/partes-persistencia/infrastructure/database/orm_models.py:630` [booleano]

- Original: `String(7), nullable=False, server_default=""`
- Mutado:   `String(7), nullable=True, server_default=""`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 62. `services/partes-persistencia/infrastructure/database/orm_models.py:633` [booleano]

- Original: `Integer, nullable=False, server_default="0"`
- Mutado:   `Integer, nullable=True, server_default="0"`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 63. `services/partes-persistencia/infrastructure/database/orm_models.py:636` [booleano]

- Original: `Integer, nullable=False, server_default="0"`
- Mutado:   `Integer, nullable=True, server_default="0"`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 64. `services/partes-persistencia/infrastructure/database/orm_models.py:638` [entero]

- Original: `obra_codigo: Mapped[str | None] = mapped_column(String(32))`
- Mutado:   `obra_codigo: Mapped[str | None] = mapped_column(String(33))`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 65. `services/partes-persistencia/infrastructure/database/orm_models.py:640` [entero]

- Original: `partida_cod: Mapped[str | None] = mapped_column(String(32))`
- Mutado:   `partida_cod: Mapped[str | None] = mapped_column(String(33))`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 66. `services/partes-persistencia/infrastructure/database/orm_models.py:647` [entero]

- Original: `String(16), nullable=False, server_default="decidido"`
- Mutado:   `String(17), nullable=False, server_default="decidido"`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 67. `services/partes-persistencia/infrastructure/database/orm_models.py:647` [booleano]

- Original: `String(16), nullable=False, server_default="decidido"`
- Mutado:   `String(16), nullable=True, server_default="decidido"`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 68. `services/partes-persistencia/infrastructure/database/orm_models.py:650` [entero]

- Original: `decision: Mapped[str | None] = mapped_column(String(16))`
- Mutado:   `decision: Mapped[str | None] = mapped_column(String(17))`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 69. `services/partes-persistencia/infrastructure/database/orm_models.py:653` [entero]

- Original: `parte_cod: Mapped[str | None] = mapped_column(String(32))`
- Mutado:   `parte_cod: Mapped[str | None] = mapped_column(String(33))`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 70. `services/partes-persistencia/infrastructure/database/orm_models.py:655` [entero]

- Original: `error: Mapped[str | None] = mapped_column(String(255))`
- Mutado:   `error: Mapped[str | None] = mapped_column(String(256))`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 71. `services/partes-persistencia/infrastructure/database/orm_models.py:656` [entero]

- Original: `decidido_por: Mapped[str | None] = mapped_column(String(120))`
- Mutado:   `decidido_por: Mapped[str | None] = mapped_column(String(121))`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 72. `services/partes-persistencia/infrastructure/database/orm_models.py:657` [entero]

- Original: `aplicado_por: Mapped[str | None] = mapped_column(String(120))`
- Mutado:   `aplicado_por: Mapped[str | None] = mapped_column(String(121))`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 73. `services/partes-persistencia/infrastructure/database/orm_models.py:658` [entero]

- Original: `decidido_at_utc: Mapped[str | None] = mapped_column(String(64))`
- Mutado:   `decidido_at_utc: Mapped[str | None] = mapped_column(String(65))`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 74. `services/partes-persistencia/infrastructure/database/orm_models.py:659` [entero]

- Original: `aplicado_at_utc: Mapped[str | None] = mapped_column(String(64))`
- Mutado:   `aplicado_at_utc: Mapped[str | None] = mapped_column(String(65))`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 75. `services/partes-persistencia/infrastructure/database/orm_models.py:661` [entero]

- Original: `String(64), nullable=False, server_default=""`
- Mutado:   `String(65), nullable=False, server_default=""`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 76. `services/partes-persistencia/infrastructure/database/orm_models.py:661` [booleano]

- Original: `String(64), nullable=False, server_default=""`
- Mutado:   `String(64), nullable=True, server_default=""`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 77. `services/partes-persistencia/infrastructure/database/orm_models.py:664` [entero]

- Original: `String(64), nullable=False, server_default=""`
- Mutado:   `String(65), nullable=False, server_default=""`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 78. `services/partes-persistencia/infrastructure/database/orm_models.py:664` [booleano]

- Original: `String(64), nullable=False, server_default=""`
- Mutado:   `String(64), nullable=True, server_default=""`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: sv3 no lee ni escribe `franquicia_ajuste`: solo la declara, porque la base es una y `create_all` la crea si sv3 arranca antes que sv4. La campaña juzga cada copia SOLO con la suite de su servicio, y sv3 no tenía ningún test de la tabla. El guardián de gemelos de la raíz (`tests/test_f010_orm_models_gemelos.py`, R1 byte a byte) caza cualquier cambio de esta copia, pero no corre en la campaña.
> Decisión: TEST NUEVO `services/partes-persistencia/tests/test_f056_orm_franquicia.py` (DDL literal de `create_all` y de arranque, los dos índices, la clave con serie): falla con el mutante y pasa sin él (§ Verificación a mano).

### 79. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:182` [entero]

- Original: `return int(getattr(self._st, "est_parte_activo", 1))`
- Mutado:   `return int(getattr(self._st, "est_parte_activo", 2))`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: el defecto de `getattr` (1 -> 2) nunca se lee.
> Decisión: CANDIDATO A EQUIVALENTE (lo acepta o no el humano): el defecto de `getattr` no se usa nunca: `Settings` declara el campo con ese mismo valor (pydantic, siempre presente) y `SettingsFake` también, así que el segundo argumento es código muerto en producción y en los tests.

### 80. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:215` [entero]

- Original: `[linea.hmoide]).get(int(linea.hmoide or 0), {})`
- Mutado:   `[linea.hmoide]).get(int(linea.hmoide or 1), {})`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: con `hmoide` vacío se busca la clave 0 o 1.
> Decisión: CANDIDATO A EQUIVALENTE (lo acepta o no el humano): `estados_de_partes` devuelve solo las claves de los partes pedidos y descarta los ids vacíos (real y doble: `if i`). Con `hmoide` vacío el diccionario está vacío y `.get(0)` y `.get(1)` dan `{}`.

### 81. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:235` [entero]

- Original: `hmoide = int(linea.hmoide or 0) or None`
- Mutado:   `hmoide = int(linea.hmoide or 1) or None`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: las líneas de ajuste de los tests traían siempre `hmoide`.
> Decisión: TEST NUEVO `services/partes-transfer/tests/test_f056_pipeline.py::test_f056_r22_comprobar_linea_sin_parte_no_inventa_el_parte`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 82. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:266` [logico]

- Original: `float(p.extras_pendientes or 0.0), ev.objetivo,`
- Mutado:   `float(p.extras_pendientes and 0.0), ev.objetivo,`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ningún test miraba el log de `comprobar`.
> Decisión: TEST NUEVO `services/partes-transfer/tests/test_f056_pipeline.py::test_f056_r33_comprobar_registra_los_pendientes`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 83. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:276` [logico]

- Original: `if not p.ajuste_id or int(p.ajuste_id) <= 0:`
- Mutado:   `if not p.ajuste_id and int(p.ajuste_id) <= 0:`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: solo se probaba el centinela 0, no un `ajuste_id` negativo.
> Decisión: TEST NUEVO `services/partes-transfer/tests/test_f056_pipeline.py::test_f056_r22_ejecutar_con_ajuste_negativo_es_error`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 84. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:276` [comparacion]

- Original: `if not p.ajuste_id or int(p.ajuste_id) <= 0:`
- Mutado:   `if not p.ajuste_id or int(p.ajuste_id) < 0:`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: `<= 0` frente a `< 0` solo difiere en 0.
> Decisión: CANDIDATO A EQUIVALENTE (lo acepta o no el humano): con `ajuste_id == 0`, `not p.ajuste_id` ya es True y el `or` no evalúa la comparación. Con un valor verdadero no es 0.

### 85. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:276` [entero]

- Original: `if not p.ajuste_id or int(p.ajuste_id) <= 0:`
- Mutado:   `if not p.ajuste_id or int(p.ajuste_id) <= 1:`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: los tests usaban el ajuste 5; nadie probaba el 1.
> Decisión: TEST NUEVO `services/partes-transfer/tests/test_f056_pipeline.py::test_f056_r22_ejecutar_con_el_ajuste_1`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 86. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:311` [entero]

- Original: `hmoide = int(ev.linea.hmoide or 0)`
- Mutado:   `hmoide = int(ev.linea.hmoide or 1)`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: en la rama ACTUALIZAR, `ev.linea.hmoide` vacío daría 0 o 1.
> Decisión: CANDIDATO A EQUIVALENTE (lo acepta o no el humano): a ACTUALIZAR solo se llega con `est_parte == est_registro`, y `est_parte` sale de `estados_de_partes` por ese `hmoide`. Vacío da `{}`, `est` None y el veredicto es NO_EDITABLE antes. En esta rama `hmoide` es siempre verdadero y el `or` nunca usa su defecto.

### 87. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:327` [entero]

- Original: `[tras.hmoide]).get(int(tras.hmoide or 0), {})`
- Mutado:   `[tras.hmoide]).get(int(tras.hmoide or 1), {})`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: igual que el 80, con la línea releída.
> Decisión: CANDIDATO A EQUIVALENTE (lo acepta o no el humano): `estados_de_partes([tras.hmoide])` con `hmoide` vacío es `{}`, y `.get(0)` y `.get(1)` dan `{}`.

### 88. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:328` [entero]

- Original: `escrita = (tras is not None and int(tras.hmoide or 0) == hmoide`
- Mutado:   `escrita = (tras is not None and int(tras.hmoide or 1) == hmoide`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ninguna relectura llegaba sin `hmoide` con el parte 1 como destino.
> Decisión: TEST NUEVO `services/partes-transfer/tests/test_f056_pipeline.py::test_f056_r29_relectura_sin_parte_no_es_escrita_ni_en_el_parte_1`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 89. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:355` [logico]

- Original: `if not (p.existe and p.ide):`
- Mutado:   `if not (p.existe or p.ide):`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: `existe and ide` frente a `existe or ide`.
> Decisión: CANDIDATO A EQUIVALENTE (lo acepta o no el humano): `ev.elegido` sale solo de `elegir_parte`, que pone `existe = True` y `ide` (el de un parte de Sigrid, > 0) a la vez, o deja `False` y `None`. Nunca hay un parte con solo uno de los dos.

### 90. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:369` [entero]

- Original: `64))`
- Mutado:   `65))`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: el defecto de `getattr` (64 -> 65) nunca se lee.
> Decisión: CANDIDATO A EQUIVALENTE (lo acepta o no el humano): el defecto de `getattr` no se usa nunca: `Settings` declara el campo con ese mismo valor (pydantic, siempre presente) y `SettingsFake` también, así que el segundo argumento es código muerto en producción y en los tests.

### 91. `services/partes-transfer/application/pipelines/franquicia_pipeline.py:374` [entero]

- Original: `paride=int(a.paride or 0), ano=p.ano, mes=p.mes, synckey=sk,`
- Mutado:   `paride=int(a.paride or 1), ano=p.ano, mes=p.mes, synckey=sk,`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: las peticiones de los tests traían siempre partida.
> Decisión: TEST NUEVO `services/partes-transfer/tests/test_f056_pipeline.py::test_f056_r24_ajuste_sin_partida_va_con_partida_0`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 92. `services/partes-transfer/application/pipelines/registro_pipeline.py:991` [booleano]

- Original: `if bool(getattr(self._st, "obra_pruebas_forzar", False))`
- Mutado:   `if bool(getattr(self._st, "obra_pruebas_forzar", True))`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: el defecto de `getattr` (False -> True) nunca se lee.
> Decisión: CANDIDATO A EQUIVALENTE (lo acepta o no el humano): el defecto de `getattr` no se usa nunca: `Settings` declara el campo con ese mismo valor (pydantic, siempre presente) y `SettingsFake` también, así que el segundo argumento es código muerto en producción y en los tests.

### 93. `services/partes-transfer/application/services/franquicia.py:109` [comparacion]

- Original: `if e <= 0:`
- Mutado:   `if e < 0:`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ningún test pedía A con E = 0 y X negativa.
> Decisión: TEST NUEVO `services/partes-transfer/tests/test_f056_franquicia.py::test_f056_r24_sin_extras_el_ajuste_es_0_sea_cual_sea_x`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 94. `services/partes-transfer/application/services/franquicia.py:125` [logico]

- Original: `if isinstance(valor, bool) or not isinstance(`
- Mutado:   `if isinstance(valor, bool) and not isinstance(`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: los tests de valores no numéricos miraban el estado, no el motivo.
> Decisión: TEST NUEVO `services/partes-transfer/tests/test_f056_franquicia.py::test_f056_r2_leer_valor_no_numerico_dice_el_tipo`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 95. `services/partes-transfer/application/services/franquicia.py:137` [comparacion]

- Original: `if x < 0 or x > MAX_FRANQUICIA_H:`
- Mutado:   `if x <= 0 or x > MAX_FRANQUICIA_H:`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: `x < 0` frente a `x <= 0` solo difiere en 0.
> Decisión: CANDIDATO A EQUIVALENTE (lo acepta o no el humano): el `if x == 0` anterior ya devolvió INACTIVA, así que aquí x nunca es 0.

### 96. `services/partes-transfer/application/services/franquicia.py:146` [comparacion]

- Original: `return abs(float(a or 0.0) - float(b or 0.0)) <= TOL + _RUIDO`
- Mutado:   `return abs(float(a or 0.0) - float(b or 0.0)) < TOL + _RUIDO`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: nadie probaba el borde exacto de la tolerancia.
> Decisión: TEST NUEVO `services/partes-transfer/tests/test_f056_franquicia.py::test_f056_r28_igual_con_la_tolerancia_justa`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 97. `services/partes-transfer/application/services/franquicia.py:146` [aritmetico]

- Original: `return abs(float(a or 0.0) - float(b or 0.0)) <= TOL + _RUIDO`
- Mutado:   `return abs(float(a or 0.0) - float(b or 0.0)) <= TOL - _RUIDO`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: nadie probaba el borde exacto de la tolerancia.
> Decisión: TEST NUEVO `services/partes-transfer/tests/test_f056_franquicia.py::test_f056_r28_igual_con_la_tolerancia_justa`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 98. `services/partes-transfer/application/services/franquicia.py:179` [logico]

- Original: `f"{MOTIVO_SIN_HE} (codigo {accion.hora_codigo or '-'})")`
- Mutado:   `f"{MOTIVO_SIN_HE} (codigo {accion.hora_codigo and '-'})")`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: el test del código que no es HE* miraba el prefijo del motivo, no el código.
> Decisión: TEST NUEVO `services/partes-transfer/tests/test_f056_franquicia.py::test_f056_r30_el_motivo_sin_he_dice_el_codigo`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 99. `services/partes-transfer/application/services/franquicia.py:193` [logico]

- Original: `f"parte {parte_cod or '?'} esta enlazada (albaran, factura, "`
- Mutado:   `f"parte {parte_cod and '?'} esta enlazada (albaran, factura, "`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: el test de la línea enlazada miraba el prefijo y el ide, no el parte.
> Decisión: TEST NUEVO `services/partes-transfer/tests/test_f056_franquicia.py::test_f056_r27_el_motivo_de_enlazada_dice_el_parte`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 100. `services/partes-transfer/interface_adapters/api/app.py:140` [booleano]

- Original: `return False`
- Mutado:   `return True`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: la fecha imposible de los tests (20261099) caía fuera del periodo, y la comparación ya la rechazaba.
> Decisión: TEST NUEVO `services/partes-transfer/tests/test_f056_api.py::test_f056_r22_fecha_imposible_dentro_del_periodo_es_422`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 101. `services/partes-transfer/interface_adapters/api/app.py:152` [entero]

- Original: `recurso_ide: Annotated[int, Field(ge=1)]`
- Mutado:   `recurso_ide: Annotated[int, Field(ge=2)]`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ningún test probaba el recurso 1 ni `fecha_int == inicio`.
> Decisión: TEST NUEVO `services/partes-transfer/tests/test_f056_api.py::test_f056_r22_limites_validos_llegan_al_pipeline`, que falla con el mutante y pasa sin él (§ Verificación a mano).

### 102. `services/partes-transfer/interface_adapters/api/app.py:168` [comparacion]

- Original: `if not self.inicio <= self.fecha_int <= self.fin:`
- Mutado:   `if not self.inicio < self.fecha_int <= self.fin:`

#### Análisis (implementer, 2026-10-29)

> Por qué ningún test lo caza: ningún test probaba el recurso 1 ni `fecha_int == inicio`.
> Decisión: TEST NUEVO `services/partes-transfer/tests/test_f056_api.py::test_f056_r22_limites_validos_llegan_al_pipeline`, que falla con el mutante y pasa sin él (§ Verificación a mano).

## Timeouts

Ninguno cuelga de verdad: los ocho mutan una expresión sin bucle ni espera. El timeout efectivo era 1650 s, y la suite de sv4 sola tarda ~820 s con 4 workers en paralelo; un mutante que hace caer muchos tests (trazas largas) la pasa del tope. Se comprobó cada uno a mano (§ Verificación a mano):

- `services/partes-front/application/services/franquicia.py:238` [entero] return round(total, 2) -> return round(total, 3)
  - **t1**: no cuelga (expresión pura): lentitud. La suite de F-056 no lo cazaba; TEST NUEVO `test_f056_r9_extras_pendientes_a_dos_decimales`, que lo mata en 1,2 s.
- `services/partes-front/application/services/franquicia.py:264` [comparacion] if d is None or rec <= 0: -> if d is not None or rec <= 0:
  - **t2**: no cuelga: lentitud. `test_f056_franquicia.py` lo mata en 3,8 s.
- `services/partes-front/application/services/franquicia.py:264` [comparacion] if d is None or rec <= 0: -> if d is None or rec < 0:
  - **t3**: no cuelga (expresión pura): lentitud. La suite de F-056 no lo cazaba; TEST NUEVO `test_f056_r9_el_recurso_0_es_sin_recurso`, que lo mata en 1,2 s.
- `services/partes-front/application/services/franquicia.py:264` [entero] if d is None or rec <= 0: -> if d is None or rec <= 1:
  - **t4**: no cuelga: lentitud. Los tests de F-056 lo matan en 13,3 s.
- `services/partes-front/application/services/franquicia.py:276` [entero] "dni": grupo[0].get("dni"), "nombre": grupo[0].get("nombre"), -> "dni": grupo[0].get("dni"), "nombre": grupo[1].get("nombre"),
  - **t5**: no cuelga (`IndexError` inmediato): lentitud. Lo mata en 3,3 s.
- `services/partes-front/application/services/franquicia.py:503` [comparacion] "dia": None if dia is None else dia.isoformat(), -> "dia": None if dia is not None else dia.isoformat(),
  - **t6**: no cuelga (`AttributeError` inmediato): lentitud. Lo mata en 22,7 s.
- `services/partes-front/infrastructure/database/orm_models.py:620` [booleano] unique=True), -> unique=False),
  - **t7**: no cuelga: lentitud. `test_f056_orm.py` lo mata en 1,4 s.
- `services/partes-front/infrastructure/database/orm_models.py:640` [entero] partida_cod: Mapped[str | None] = mapped_column(String(32)) -> partida_cod: Mapped[str | None] = mapped_column(String(33))
  - **t8**: no cuelga: lentitud. `test_f056_orm.py` lo mata en 1,0 s.

## Verificación a mano (implementer, 2026-10-29)

Cada mutante se aplicó a mano sobre su línea (el texto «Mutado» de arriba),
se corrió el fichero de tests que lo cubre con
`python -m pytest -q -p no:cacheprovider -x <fichero>` desde su servicio y
se revirtió siempre (`try/finally`). Después se corrió el mismo fichero sin
el mutante. **MATA** = exit 1 con el mutante y exit 0 sin él. **NO MATA**
en un candidato a equivalente confirma que ningún test lo distingue. Ficheros
usados: sv3 `tests/test_f056_orm_franquicia.py`; sv4
`tests/test_f056_franquicia.py`, `test_f056_decisiones.py`,
`test_f056_vista.py` y `test_f056_orm.py`; sv5 `tests/test_f056_api.py`,
`test_f056_franquicia.py` y `test_f056_pipeline.py`. Los timeouts t1 y t3
se repitieron tras sus tests nuevos: la fila es la última corrida.

| # | Sitio | Veredicto | Con el mutante | Sin él |
|---|---|---|---|---|
| 1 | `partes-front/application/franquicia.py:97` | MATA | exit 1: 1 failed, 63 passed in 0.61s | exit 0 |
| 2 | `partes-front/application/franquicia.py:113` | MATA | exit 1: 1 failed, 63 passed in 0.55s | exit 0 |
| 3 | `partes-front/application/franquicia.py:128` | NO MATA | exit 0: 77 passed in 0.40s | exit 0 |
| 4 | `partes-front/application/franquicia.py:174` | MATA | exit 1: 1 failed, 64 passed in 0.66s | exit 0 |
| 5 | `partes-front/application/franquicia.py:196` | MATA | exit 1: 1 failed, 66 passed in 0.63s | exit 0 |
| 6 | `partes-front/application/franquicia.py:197` | MATA | exit 1: 1 failed, 66 passed in 0.63s | exit 0 |
| 7 | `partes-front/application/franquicia.py:208` | MATA | exit 1: 1 failed, 67 passed in 0.55s | exit 0 |
| 8 | `partes-front/application/franquicia.py:217` | MATA | exit 1: 1 failed, 68 passed in 0.74s | exit 0 |
| 9 | `partes-front/application/franquicia.py:233` | MATA | exit 1: 1 failed, 69 passed in 0.59s | exit 0 |
| 10 | `partes-front/application/franquicia.py:235` | NO MATA | exit 0: 77 passed in 0.47s | exit 0 |
| 11 | `partes-front/application/franquicia.py:263` | MATA | exit 1: 1 failed, 70 passed in 0.53s | exit 0 |
| 12 | `partes-front/application/franquicia.py:336` | MATA | exit 1: 1 failed, 71 passed in 0.71s | exit 0 |
| 13 | `partes-front/application/franquicia.py:338` | MATA | exit 1: 1 failed, 72 passed in 0.58s | exit 0 |
| 14 | `partes-front/application/franquicia.py:355` | MATA | exit 1: 1 failed, 74 passed in 0.54s | exit 0 |
| 15 | `partes-front/application/franquicia.py:401` | MATA | exit 1: 1 failed, 75 passed in 0.53s | exit 0 |
| 16 | `partes-front/application/franquicia.py:459` | MATA | exit 1: 1 failed, 76 passed in 0.44s | exit 0 |
| 17 | `partes-front/infrastructure/database/parte_repository.py:4071` | NO MATA | exit 0: 85 passed, 1 warning in 22.36s | exit 0 |
| 18 | `partes-front/infrastructure/database/parte_repository.py:4091` | MATA | exit 1: 1 failed, 65 passed, 1 warning in 15.17s | exit 0 |
| 19 | `partes-front/infrastructure/database/parte_repository.py:4096` | NO MATA | exit 0: 85 passed, 1 warning in 43.09s | exit 0 |
| 20 | `partes-front/infrastructure/database/parte_repository.py:4101` | MATA | exit 1: 1 failed, 66 passed, 1 warning in 13.51s | exit 0 |
| 21 | `partes-front/infrastructure/database/parte_repository.py:4156` | MATA | exit 1: 1 failed, 67 passed, 1 warning in 12.17s | exit 0 |
| 22 | `partes-front/infrastructure/database/parte_repository.py:4164` | MATA | exit 1: 1 failed, 67 passed, 1 warning in 15.29s | exit 0 |
| 23 | `partes-front/infrastructure/database/parte_repository.py:4282` | MATA | exit 1: 1 failed, 68 passed, 1 warning in 21.42s | exit 0 |
| 24 | `partes-front/infrastructure/database/parte_repository.py:4282` | MATA | exit 1: 1 failed, 68 passed, 1 warning in 18.58s | exit 0 |
| 25 | `partes-front/infrastructure/database/parte_repository.py:4285` | MATA | exit 1: 1 failed, 68 passed, 1 warning in 19.22s | exit 0 |
| 26 | `partes-front/interface_adapters/web/app.py:2740` | MATA | exit 1: 1 failed, 73 passed, 1 warning in 21.32s | exit 0 |
| 27 | `partes-front/interface_adapters/web/app.py:2743` | MATA | exit 1: 1 failed, 73 passed, 1 warning in 18.41s | exit 0 |
| 28 | `partes-front/interface_adapters/web/app.py:2746` | MATA | exit 1: 1 failed, 69 passed, 1 warning in 18.28s | exit 0 |
| 29 | `partes-front/interface_adapters/web/app.py:2764` | MATA | exit 1: 1 failed, 76 passed, 1 warning in 20.65s | exit 0 |
| 30 | `partes-front/interface_adapters/web/app.py:2786` | MATA | exit 1: 1 failed, 77 passed, 1 warning in 20.18s | exit 0 |
| 31 | `partes-front/interface_adapters/web/app.py:2815` | NO MATA | exit 0: 147 passed, 1 warning in 27.46s | exit 0 |
| 32 | `partes-front/interface_adapters/web/app.py:2835` | MATA | exit 1: 1 failed, 70 passed, 1 warning in 14.40s | exit 0 |
| 33 | `partes-front/interface_adapters/web/app.py:2846` | MATA | exit 1: 1 failed, 74 passed, 1 warning in 22.57s | exit 0 |
| 34 | `partes-front/interface_adapters/web/app.py:2847` | MATA | exit 1: 1 failed, 74 passed, 1 warning in 14.39s | exit 0 |
| 35 | `partes-front/interface_adapters/web/app.py:2854` | MATA | exit 1: 1 failed, 74 passed, 1 warning in 17.65s | exit 0 |
| 36 | `partes-front/interface_adapters/web/app.py:2854` | MATA | exit 1: 1 failed, 74 passed, 1 warning in 20.30s | exit 0 |
| 37 | `partes-front/interface_adapters/web/app.py:2854` | MATA | exit 1: 1 failed, 74 passed, 1 warning in 18.26s | exit 0 |
| 38 | `partes-front/interface_adapters/web/app.py:2854` | MATA | exit 1: 1 failed, 75 passed, 1 warning in 17.88s | exit 0 |
| 39 | `partes-front/interface_adapters/web/app.py:2868` | MATA | exit 1: 1 failed, 71 passed, 1 warning in 16.47s | exit 0 |
| 40 | `partes-front/interface_adapters/web/app.py:2888` | MATA | exit 1: 1 failed, 78 passed, 1 warning in 20.35s | exit 0 |
| 41 | `partes-front/interface_adapters/web/app.py:2916` | MATA | exit 1: 1 failed, 79 passed, 1 warning in 19.43s | exit 0 |
| 42 | `partes-front/interface_adapters/web/app.py:2917` | MATA | exit 1: 1 failed, 80 passed, 1 warning in 15.41s | exit 0 |
| 43 | `partes-front/interface_adapters/web/app.py:2954` | MATA | exit 1: 1 failed, 81 passed, 1 warning in 14.44s | exit 0 |
| 44 | `partes-front/interface_adapters/web/app.py:2955` | MATA | exit 1: 1 failed, 81 passed, 1 warning in 18.07s | exit 0 |
| 45 | `partes-front/interface_adapters/web/app.py:2969` | MATA | exit 1: 1 failed, 56 passed, 1 warning in 19.09s | exit 0 |
| 46 | `partes-front/interface_adapters/web/app.py:2980` | MATA | exit 1: 1 failed, 55 passed, 1 warning in 24.05s | exit 0 |
| 47 | `partes-front/interface_adapters/web/app.py:2983` | MATA | exit 1: 1 failed, 57 passed, 1 warning in 17.80s | exit 0 |
| 48 | `partes-front/interface_adapters/web/app.py:2993` | MATA | exit 1: 1 failed, 59 passed, 1 warning in 15.00s | exit 0 |
| 49 | `partes-front/interface_adapters/web/app.py:3006` | MATA | exit 1: 1 failed, 61 passed, 1 warning in 17.45s | exit 0 |
| 50 | `partes-front/interface_adapters/web/app.py:3017` | MATA | exit 1: 1 failed, 58 passed, 1 warning in 15.20s | exit 0 |
| 51 | `partes-front/interface_adapters/web/app.py:3026` | MATA | exit 1: 1 failed, 60 passed, 1 warning in 16.79s | exit 0 |
| 52 | `partes-front/interface_adapters/web/app.py:3028` | MATA | exit 1: 1 failed, 60 passed, 1 warning in 16.69s | exit 0 |
| 53 | `partes-front/interface_adapters/web/app.py:3033` | MATA | exit 1: 1 failed, 82 passed, 1 warning in 15.80s | exit 0 |
| 54 | `partes-front/interface_adapters/web/app.py:3050` | MATA | exit 1: 1 failed, 72 passed, 1 warning in 12.52s | exit 0 |
| 55 | `partes-front/interface_adapters/web/app.py:3051` | MATA | exit 1: 1 failed, 83 passed, 1 warning in 19.31s | exit 0 |
| 56 | `partes-front/interface_adapters/web/app.py:3059` | MATA | exit 1: 1 failed, 84 passed, 1 warning in 22.18s | exit 0 |
| 57 | `partes-persistencia/infrastructure/database/orm_models.py:620` | MATA | exit 1: 1 failed, 1 passed in 2.84s | exit 0 |
| 58 | `partes-persistencia/infrastructure/database/orm_models.py:624` | MATA | exit 1: 1 failed in 4.91s | exit 0 |
| 59 | `partes-persistencia/infrastructure/database/orm_models.py:626` | MATA | exit 1: 1 failed in 7.44s | exit 0 |
| 60 | `partes-persistencia/infrastructure/database/orm_models.py:630` | MATA | exit 1: 1 failed in 4.96s | exit 0 |
| 61 | `partes-persistencia/infrastructure/database/orm_models.py:630` | MATA | exit 1: 1 failed in 4.87s | exit 0 |
| 62 | `partes-persistencia/infrastructure/database/orm_models.py:633` | MATA | exit 1: 1 failed in 1.57s | exit 0 |
| 63 | `partes-persistencia/infrastructure/database/orm_models.py:636` | MATA | exit 1: 1 failed in 3.20s | exit 0 |
| 64 | `partes-persistencia/infrastructure/database/orm_models.py:638` | MATA | exit 1: 1 failed in 2.92s | exit 0 |
| 65 | `partes-persistencia/infrastructure/database/orm_models.py:640` | MATA | exit 1: 1 failed in 3.87s | exit 0 |
| 66 | `partes-persistencia/infrastructure/database/orm_models.py:647` | MATA | exit 1: 1 failed in 2.06s | exit 0 |
| 67 | `partes-persistencia/infrastructure/database/orm_models.py:647` | MATA | exit 1: 1 failed in 2.62s | exit 0 |
| 68 | `partes-persistencia/infrastructure/database/orm_models.py:650` | MATA | exit 1: 1 failed in 1.67s | exit 0 |
| 69 | `partes-persistencia/infrastructure/database/orm_models.py:653` | MATA | exit 1: 1 failed in 1.67s | exit 0 |
| 70 | `partes-persistencia/infrastructure/database/orm_models.py:655` | MATA | exit 1: 1 failed in 5.27s | exit 0 |
| 71 | `partes-persistencia/infrastructure/database/orm_models.py:656` | MATA | exit 1: 1 failed in 4.57s | exit 0 |
| 72 | `partes-persistencia/infrastructure/database/orm_models.py:657` | MATA | exit 1: 1 failed in 3.38s | exit 0 |
| 73 | `partes-persistencia/infrastructure/database/orm_models.py:658` | MATA | exit 1: 1 failed in 2.67s | exit 0 |
| 74 | `partes-persistencia/infrastructure/database/orm_models.py:659` | MATA | exit 1: 1 failed in 2.86s | exit 0 |
| 75 | `partes-persistencia/infrastructure/database/orm_models.py:661` | MATA | exit 1: 1 failed in 2.51s | exit 0 |
| 76 | `partes-persistencia/infrastructure/database/orm_models.py:661` | MATA | exit 1: 1 failed in 1.94s | exit 0 |
| 77 | `partes-persistencia/infrastructure/database/orm_models.py:664` | MATA | exit 1: 1 failed in 2.71s | exit 0 |
| 78 | `partes-persistencia/infrastructure/database/orm_models.py:664` | MATA | exit 1: 1 failed in 2.07s | exit 0 |
| 79 | `partes-transfer/application/pipelines/franquicia_pipeline.py:182` | NO MATA | exit 0: 58 passed in 0.53s | exit 0 |
| 80 | `partes-transfer/application/pipelines/franquicia_pipeline.py:215` | NO MATA | exit 0: 58 passed in 0.49s | exit 0 |
| 81 | `partes-transfer/application/pipelines/franquicia_pipeline.py:235` | MATA | exit 1: 1 failed, 52 passed in 1.19s | exit 0 |
| 82 | `partes-transfer/application/pipelines/franquicia_pipeline.py:266` | MATA | exit 1: 1 failed, 53 passed in 0.72s | exit 0 |
| 83 | `partes-transfer/application/pipelines/franquicia_pipeline.py:276` | MATA | exit 1: 1 failed, 54 passed in 0.67s | exit 0 |
| 84 | `partes-transfer/application/pipelines/franquicia_pipeline.py:276` | NO MATA | exit 0: 58 passed in 0.48s | exit 0 |
| 85 | `partes-transfer/application/pipelines/franquicia_pipeline.py:276` | MATA | exit 1: 1 failed, 55 passed in 1.06s | exit 0 |
| 86 | `partes-transfer/application/pipelines/franquicia_pipeline.py:311` | NO MATA | exit 0: 58 passed in 0.64s | exit 0 |
| 87 | `partes-transfer/application/pipelines/franquicia_pipeline.py:327` | NO MATA | exit 0: 58 passed in 0.50s | exit 0 |
| 88 | `partes-transfer/application/pipelines/franquicia_pipeline.py:328` | MATA | exit 1: 1 failed, 56 passed in 0.71s | exit 0 |
| 89 | `partes-transfer/application/pipelines/franquicia_pipeline.py:355` | NO MATA | exit 0: 58 passed in 0.71s | exit 0 |
| 90 | `partes-transfer/application/pipelines/franquicia_pipeline.py:369` | NO MATA | exit 0: 58 passed in 0.80s | exit 0 |
| 91 | `partes-transfer/application/pipelines/franquicia_pipeline.py:374` | MATA | exit 1: 1 failed, 57 passed in 1.24s | exit 0 |
| 92 | `partes-transfer/application/pipelines/registro_pipeline.py:991` | NO MATA | exit 0: 124 passed, 1 warning in 9.08s | exit 0 |
| 93 | `partes-transfer/application/franquicia.py:109` | MATA | exit 1: 1 failed, 133 passed in 0.94s | exit 0 |
| 94 | `partes-transfer/application/franquicia.py:125` | MATA | exit 1: 1 failed, 135 passed in 0.91s | exit 0 |
| 95 | `partes-transfer/application/franquicia.py:137` | NO MATA | exit 0: 143 passed in 0.60s | exit 0 |
| 96 | `partes-transfer/application/franquicia.py:146` | MATA | exit 1: 1 failed, 138 passed in 1.32s | exit 0 |
| 97 | `partes-transfer/application/franquicia.py:146` | MATA | exit 1: 1 failed, 138 passed in 0.72s | exit 0 |
| 98 | `partes-transfer/application/franquicia.py:179` | MATA | exit 1: 1 failed, 139 passed in 0.74s | exit 0 |
| 99 | `partes-transfer/application/franquicia.py:193` | MATA | exit 1: 1 failed, 141 passed in 0.75s | exit 0 |
| 100 | `partes-transfer/interface_adapters/api/app.py:140` | MATA | exit 1: 1 failed, 60 passed, 1 warning in 7.25s | exit 0 |
| 101 | `partes-transfer/interface_adapters/api/app.py:152` | MATA | exit 1: 1 failed, 62 passed, 1 warning in 8.81s | exit 0 |
| 102 | `partes-transfer/interface_adapters/api/app.py:168` | MATA | exit 1: 1 failed, 64 passed, 1 warning in 7.95s | exit 0 |
| t1 | `partes-front/application/franquicia.py:238` | MATA | exit 1: 1 failed, 77 passed in 1.18s | exit 0 |
| t2 | `partes-front/application/franquicia.py:264` | MATA | exit 1: 1 failed, 23 passed, 1 warning in 3.80s | exit 0 |
| t3 | `partes-front/application/franquicia.py:264` | MATA | exit 1: 1 failed, 78 passed in 1.18s | exit 0 |
| t4 | `partes-front/application/franquicia.py:264` | MATA | exit 1: 1 failed, 152 passed, 1 warning in 13.31s | exit 0 |
| t5 | `partes-front/application/franquicia.py:276` | MATA | exit 1: 1 failed, 23 passed, 1 warning in 3.27s | exit 0 |
| t6 | `partes-front/application/franquicia.py:503` | MATA | exit 1: 1 failed, 162 passed, 1 warning in 22.70s | exit 0 |
| t7 | `partes-front/infrastructure/database/orm_models.py:620` | MATA | exit 1: 1 failed in 1.35s | exit 0 |
| t8 | `partes-front/infrastructure/database/orm_models.py:640` | MATA | exit 1: 1 failed in 1.02s | exit 0 |
