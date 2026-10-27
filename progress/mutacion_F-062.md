<!-- progress/mutacion_F-062.md -->
# F-062 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-062` el 2026-10-26 11:47.

## Alcance

Origen del diff: **rama** (`a82f9c625ebdf01f865802b3a15ecabdf97c3c75` .. `feature/F-062-ciz-el-mismo-dia-del-inicio`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/racha_incidencia.py` | 57 |
| `services/partes-front/config/settings.py` | 5 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 26 |
| `services/partes-transfer/application/pipelines/registro_pipeline.py` | 171 |
| `services/partes-transfer/application/services/racha_ciz.py` | 45 |
| `services/partes-transfer/application/services/reglas_registro.py` | 38 |
| `services/partes-transfer/config/settings.py` | 6 |
| `services/partes-transfer/domain/models/registro_models.py` | 20 |
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | 51 |
| `services/partes-transfer/interface_adapters/api/app.py` | 6 |
| **Total** | **425** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 84 |
| Mutantes evaluados | 84 |
| Muertos | 75 |
| Supervivientes | 9 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 4185.0 s |
| SHA de HEAD medido | `37fca60b268a69eccb0d05979cce6cb138ee4eb9` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_3ranvmae/wk_0/services/partes-front` | 575.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_3ranvmae/wk_0/services/partes-transfer` | 19.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_3ranvmae/wk_1/services/partes-front` | 586.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_3ranvmae/wk_1/services/partes-transfer` | 20.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_3ranvmae/wk_2/services/partes-front` | 576.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_3ranvmae/wk_2/services/partes-transfer` | 20.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_3ranvmae/wk_3/services/partes-front` | 572.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-062_3ranvmae/wk_3/services/partes-transfer` | 20.6 |
| Media por mutante evaluado (s) | 49.8 |
| Timeout efectivo por mutante (s) | 1174 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 300 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/racha_incidencia.py:262` [entero]

- Original: `f = int(l.fecha_int or 0)`
- Mutado:   `f = int(l.fecha_int or 1)`

#### Análisis

> Por qué ningún test lo caza: `l.fecha_int` vacío da `f` = 0 o 1, y los dos dan el mismo resultado. `f in tramo` es falso para ambos, porque el tramo solo tiene fechas reales ≥ D + 1. `d < f <= ultimo` también es falso para ambos: `d` es la fecha AAAAMMDD del `inicio`, y `racha_delante` solo se llama para líneas con `LineaRol`, que exige fecha.
> Decisión: **equivalente aceptado por el humano el 2026-10-26 («acepto»)**. Ningún valor alcanzable de `d` es < 1.
> Demostración ejecutable (RM5): `progress/equivalentes_F-062.py sv4`, lanzado desde `services/partes-front`. Salida (2026-10-26): «racha_delante: 50000 llamadas, 11726 con tramo, 8279 con tramo y alguna fecha None/0/1 · EQUIVALENTE: #1 · 1 mutantes, 0 distintos». Exit 0. El control `and 0` de la misma línea sale **distinto, como debe**, así que el diferencial no es ciego.

### 2. `services/partes-transfer/application/pipelines/registro_pipeline.py:335` [logico]

- Original: `if a.paride and not subcuenta_de_linea(`
- Mutado:   `if a.paride or not subcuenta_de_linea(`

#### Análisis

> Por qué ningún test lo caza: ningún test tenía un `inicio` con partida y subcuenta propia a la vez en el CI* y en el CIZ. El mutante (`or`) pide entonces la partida, que el original no lee.
> Decisión: **hueco de test**. Test añadido: `test_f062_mut_r9_hermano_con_subcuenta_propia_no_pide_partida`. Verificado a mano con el mutante aplicado: el test falla (`partidas_leidas` = `[{parides: [33]}]` en vez de `[]`) y pasa sin él (traza en `progress/impl_F-062.md`).

### 3. `services/partes-transfer/application/pipelines/registro_pipeline.py:344` [entero]

- Original: `partidas.get(int(a.paride or 0)))`
- Mutado:   `partidas.get(int(a.paride or 1)))`

#### Análisis

> Por qué ningún test lo caza: `paride` vale 0 cuando la línea no tiene partida (las reglas lo fijan con `int(... or 0)`). Para que `get(0)` y `get(1)` den distinto hace falta que OTRA línea de la petición haya pedido la partida 1, y ningún test lo combinaba.
> Decisión: **hueco de test**. Test añadido: `test_f062_mut_r9_hermano_sin_partida_no_toma_la_de_otra_linea`. Verificado a mano con el mutante aplicado: el test falla (el hermano sin partida hereda `(704, 'C.CI55')`) y pasa sin él (traza en `progress/impl_F-062.md`).

### 4. `services/partes-transfer/application/pipelines/registro_pipeline.py:533` [entero]

- Original: `a.fecha_int, int(a.recurso_ide or 0),`
- Mutado:   `a.fecha_int, int(a.recurso_ide or 1),`

#### Análisis

> Por qué ningún test lo caza: `inicios` son acciones `escribir` con `fin_mismo_dia`, y `fin_mismo_dia` solo lo pone `ReglasRegistro._decidir_incidencia` después de omitir la línea sin recurso (`if not linea.recurso_ide: return omitir(...)`). El paso de coherencia solo reasigna `recurso_ide` a un `reside` elegido, que nunca es 0. Por tanto `a.recurso_ide` nunca es falso aquí, y el `or 0` / `or 1` no llega a evaluarse.
> Decisión: **equivalente aceptado por el humano el 2026-10-26 («acepto»)**.
> Demostración ejecutable (RM5): `progress/equivalentes_F-062.py sv5`, lanzado desde `services/partes-transfer`. Salida (2026-10-26): «pipeline: 4000 escenarios, 1390 con un CIZ hermano escrito, 2190 con alguna línea sin recurso o con recurso 0 · EQUIVALENTE: #4 · EQUIVALENTE: #5 · 2 mutantes, 0 distintos». Exit 0. El control `and 0` de la misma línea sale **distinto, como debe**, así que el diferencial no es ciego. El diferencial recorre el pipeline completo (`preflight` y `ejecutar`) con `MOVER_CIZ` encendido.

### 5. `services/partes-transfer/application/pipelines/registro_pipeline.py:547` [entero]

- Original: `d = decidir_fin(a.fecha_int, int(a.recurso_ide or 0),`
- Mutado:   `d = decidir_fin(a.fecha_int, int(a.recurso_ide or 1),`

#### Análisis

> Por qué ningún test lo caza: es la misma razón que en el 4. `fines` son acciones `escribir` con código CIZ, y toda acción `escribir` sale de una rama de `ReglasRegistro` que antes omite la línea sin recurso (incidencia, normal o extra, y mensual). El `or` nunca se evalúa. F-062 reescribió la línea en T6 (03bdafb) al reordenar el paso 6 bis; el `or 0` ya venía de F-060.
> Decisión: **equivalente aceptado por el humano el 2026-10-26 («acepto»)**. **Es el mutante #11 de F-060**: mismo texto, operador y expresión. El humano lo aceptó el 2026-10-24 («acepto»); F-062 solo partió la línea en dos.
> Demostración ejecutable (RM5): `progress/equivalentes_F-062.py sv5`, lanzado desde `services/partes-transfer`. Salida (2026-10-26): «pipeline: 4000 escenarios, 1390 con un CIZ hermano escrito, 2190 con alguna línea sin recurso o con recurso 0 · EQUIVALENTE: #4 · EQUIVALENTE: #5 · 2 mutantes, 0 distintos». Exit 0. El control `and 0` de la misma línea sale **distinto, como debe**, así que el diferencial no es ciego. `progress/equivalentes_F-060.py sv5` vuelve a dar «2 mutantes, 0 distintos».

### 6. `services/partes-transfer/application/pipelines/registro_pipeline.py:586` [entero]

- Original: `and int(ls.horide or 0) == int(fin.horide)`
- Mutado:   `and int(ls.horide or 1) == int(fin.horide)`

#### Análisis

> Por qué ningún test lo caza: para distinguirlos hace falta una línea de Sigrid sin `horide` (la columna admite nulos: el resto del cliente usa `ISNULL(horide, 0)`) cuyo CIZ tenga `horide` 1. Los tests usaban `horide` 40.
> Decisión: **hueco de test**. Test añadido: `test_f062_mut_r12_linea_sin_codigo_no_es_ciz_ajeno`. Verificado a mano con el mutante aplicado: el test falla (`_ciz_ajeno` devuelve True con una línea sin código) y pasa sin él (traza en `progress/impl_F-062.md`).

### 7. `services/partes-transfer/application/pipelines/registro_pipeline.py:817` [entero]

- Original: `fecha_int=a.fecha_int, paride=int(a.paride or 0),`
- Mutado:   `fecha_int=a.fecha_int, paride=int(a.paride or 1),`

#### Análisis

> Por qué ningún test lo caza: todos los tests de la sentencia doble comprobaban `paride` con partida 33. Un `inicio` sin partida (`paride` 0, el caso normal de una incidencia) escribiría `paride` 1, y nadie lo miraba.
> Decisión: **hueco de test**. Test añadido: `test_f062_mut_r13_inicio_sin_partida_escribe_paride_cero`. Verificado a mano con el mutante aplicado: el test falla (las dos filas con `paride` 1) y pasa sin él (traza en `progress/impl_F-062.md`).

### 8. `services/partes-transfer/application/services/racha_ciz.py:102` [logico]

- Original: `if not sk.startswith(PREFIJO_PARTES) or sk.endswith(SUFIJO_CIZ):`
- Mutado:   `if not sk.startswith(PREFIJO_PARTES) and sk.endswith(SUFIJO_CIZ):`

#### Análisis

> Por qué ningún test lo caza: los casos ajenos probados (`otro:7`, `partes:x`) acaban en `ValueError` también con el mutante. Pero una synckey ajena cuya cola, tras los 7 caracteres de `partes:`, es un entero (`ALB0000123`) se parsearía como el registro 123.
> Decisión: **hueco de test**. Test añadido: `test_f062_mut_r20_synckey_ajena_con_digitos_no_es_registro`. Verificado a mano con el mutante aplicado: el test falla (`registro_de_synckey('ALB0000123')` = 123) y pasa sin él (traza en `progress/impl_F-062.md`).

### 9. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:665` [entero]

- Original: `cenide = int(getattr(obra, "cenide", 0) or 0)`
- Mutado:   `cenide = int(getattr(obra, "cenide", 1) or 0)`

#### Análisis

> Por qué ningún test lo caza: `ObraEntrada` no declara `cenide` (se añade en ejecución), y todos los tests de la sentencia lo fijaban a 55. Con una obra sin el atributo, el mutante escribe `cenide` 1.
> Decisión: **hueco de test**. Test añadido: `test_f062_mut_r13_obra_sin_cenide_va_con_cero`. Verificado a mano con el mutante aplicado: el test falla (`cenide` = 1) y pasa sin él (traza en `progress/impl_F-062.md`).

