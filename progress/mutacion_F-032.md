<!-- progress/mutacion_F-032.md -->
# F-032 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-032 --workers 3` el 2026-11-17 23:09.

## Alcance

Origen del diff: **rama** (`95982acad98d9d6fa9bc93b1f0df66614e11a0d7` .. `feature/F-032-sesame-festivos-produccion`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/partes-front/application/services/calendario_provider.py` | 83 | 12 |
| `services/partes-front/application/services/festivos_guardados.py` | 126 | 31 |
| `services/partes-front/application/services/reparto_obras.py` | 3 | 0 — sin mutantes |
| `services/partes-front/config/logging_config.py` | 4 | 0 — sin mutantes |
| `services/partes-front/infrastructure/database/orm_models.py` | 42 | 10 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 48 | 2 |
| `services/partes-front/infrastructure/transfer/resultado_sigrid.py` | 3 | 0 — sin mutantes |
| `services/partes-front/interface_adapters/web/app.py` | 45 | 2 |
| `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py` | 51 | 14 |
| `services/partes-persistencia/application/services/festivos_guardados.py` | 126 | 31 |
| `services/partes-persistencia/application/services/refresco_festivos.py` | 148 | 24 |
| `services/partes-persistencia/config/logging_config.py` | 4 | 0 — sin mutantes |
| `services/partes-persistencia/config/settings.py` | 8 | 2 |
| `services/partes-persistencia/contrastar_festivos_sesame.py` | 441 | 138 |
| `services/partes-persistencia/infrastructure/calendario/tabla_calendario_laboral.py` | 119 | 18 |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | 42 | 10 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_festivos_repository.py` | 82 | 3 |
| `services/partes-persistencia/interface_adapters/api/app.py` | 63 | 6 |
| **Total** | **1438** | **303** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 303 |
| Mutantes evaluados | 111 |
| Muertos | 78 |
| Supervivientes | 32 (todos medidos: sin mapa no se poda) |
| Timeouts | 0 |
| Indeterminados | 1 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 8964.3 s |
| SHA de HEAD medido | `0e0d2f85048bcce3af0eb69c7826ac3237aa3cf4` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-032_kvrcm3j4/wk_0/services/partes-front` | 1409.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-032_kvrcm3j4/wk_0/services/partes-persistencia` | 82.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-032_kvrcm3j4/wk_1/services/partes-front` | 1404.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-032_kvrcm3j4/wk_1/services/partes-persistencia` | 75.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-032_kvrcm3j4/wk_2/services/partes-front` | 1409.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-032_kvrcm3j4/wk_2/services/partes-persistencia` | 69.6 |
| Media por mutante evaluado (s) | 80.8 |
| Timeout efectivo por mutante (s) | 2819 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 600 |
| Workers | 3 |
| Un mutante por línea | sí — 303 generados → 185 candidatos, uno por línea |
| Muestreo | sí — 111 de 185 candidatos, semilla `20261030`, nivel `critico`; tope: 60 % de 185 candidatos, acotado a [100, 300] |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 134.7 (111 mutantes) |

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/festivos_guardados.py:55` [veracidad]

- Original: `if valor is None:`
- Mutado:   `if not valor:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: ningún caso daba un nombre «falsy» distinto de `None` (p. ej. `0`): `""` sale `None` por las dos ramas.
> Decisión: **test nuevo** `services/partes-front/tests/test_f032_campana.py::test_f032_r42_un_nombre_no_textual_se_guarda_como_texto`. Verificado a mano: con el mutante aplicado, `test_f032_r42_un_nombre_no_textual_se_guarda_como_texto` cae (`mutar_a_mano.py`, sin campaña).

### 2. `services/partes-front/infrastructure/database/orm_models.py:692` [booleano]

- Original: `unique=True),`
- Mutado:   `unique=False),`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: SÍ lo caza un test, pero de la raíz: `tests/test_f032_contrato_festivos.py` comprueba que el índice `ux_festivos_trabajador_dni_ano` es UNIQUE (DDL esperado) en las DOS copias del ORM (R1). La campaña solo corre las suites de sv3 y sv4 (sus líneas base), no `tests/` de la raíz, así que no lo ve.
> Decisión: **muerto fuera de la campaña, no es hueco**. **Aceptado por el humano el 2026-11-18 («acepto»).** Verificado a mano: con el mutante aplicado en cada copia, `python -m pytest tests/test_f032_contrato_festivos.py` cae (1 failed). No se duplica el test dentro de cada servicio: el contrato de la tabla vive en la raíz porque es de las dos copias a la vez (patrón de F-010 y F-056).

### 3. `services/partes-front/infrastructure/database/orm_models.py:697` [booleano]

- Original: `String(32), nullable=False, server_default=""`
- Mutado:   `String(32), nullable=True, server_default=""`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: SÍ lo caza un test, pero de la raíz: `tests/test_f032_contrato_festivos.py` comprueba `nullable is False` en cada columna que no es la clave en las DOS copias del ORM (R1). La campaña solo corre las suites de sv3 y sv4 (sus líneas base), no `tests/` de la raíz, así que no lo ve.
> Decisión: **muerto fuera de la campaña, no es hueco**. **Aceptado por el humano el 2026-11-18 («acepto»).** Verificado a mano: con el mutante aplicado en cada copia, `python -m pytest tests/test_f032_contrato_festivos.py` cae (1 failed). No se duplica el test dentro de cada servicio: el contrato de la tabla vive en la raíz porque es de las dos copias a la vez (patrón de F-010 y F-056).

### 4. `services/partes-front/infrastructure/database/orm_models.py:700` [booleano]

- Original: `Integer, nullable=False, server_default="0"`
- Mutado:   `Integer, nullable=True, server_default="0"`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: SÍ lo caza un test, pero de la raíz: `tests/test_f032_contrato_festivos.py` comprueba `nullable is False` en cada columna que no es la clave en las DOS copias del ORM (R1). La campaña solo corre las suites de sv3 y sv4 (sus líneas base), no `tests/` de la raíz, así que no lo ve.
> Decisión: **muerto fuera de la campaña, no es hueco**. **Aceptado por el humano el 2026-11-18 («acepto»).** Verificado a mano: con el mutante aplicado en cada copia, `python -m pytest tests/test_f032_contrato_festivos.py` cae (1 failed). No se duplica el test dentro de cada servicio: el contrato de la tabla vive en la raíz porque es de las dos copias a la vez (patrón de F-010 y F-056).

### 5. `services/partes-front/infrastructure/database/orm_models.py:703` [booleano]

- Original: `Text, nullable=False, server_default="{}"`
- Mutado:   `Text, nullable=True, server_default="{}"`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: SÍ lo caza un test, pero de la raíz: `tests/test_f032_contrato_festivos.py` comprueba `nullable is False` en cada columna que no es la clave en las DOS copias del ORM (R1). La campaña solo corre las suites de sv3 y sv4 (sus líneas base), no `tests/` de la raíz, así que no lo ve.
> Decisión: **muerto fuera de la campaña, no es hueco**. **Aceptado por el humano el 2026-11-18 («acepto»).** Verificado a mano: con el mutante aplicado en cada copia, `python -m pytest tests/test_f032_contrato_festivos.py` cae (1 failed). No se duplica el test dentro de cada servicio: el contrato de la tabla vive en la raíz porque es de las dos copias a la vez (patrón de F-010 y F-056).

### 6. `services/partes-front/infrastructure/database/orm_models.py:706` [booleano]

- Original: `Integer, nullable=False, server_default="0"`
- Mutado:   `Integer, nullable=True, server_default="0"`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: SÍ lo caza un test, pero de la raíz: `tests/test_f032_contrato_festivos.py` comprueba `nullable is False` en cada columna que no es la clave en las DOS copias del ORM (R1). La campaña solo corre las suites de sv3 y sv4 (sus líneas base), no `tests/` de la raíz, así que no lo ve.
> Decisión: **muerto fuera de la campaña, no es hueco**. **Aceptado por el humano el 2026-11-18 («acepto»).** Verificado a mano: con el mutante aplicado en cada copia, `python -m pytest tests/test_f032_contrato_festivos.py` cae (1 failed). No se duplica el test dentro de cada servicio: el contrato de la tabla vive en la raíz porque es de las dos copias a la vez (patrón de F-010 y F-056).

### 7. `services/partes-front/infrastructure/database/orm_models.py:709` [entero]

- Original: `String(40), nullable=False, server_default="1970-01-01T00:00:00Z"`
- Mutado:   `String(41), nullable=False, server_default="1970-01-01T00:00:00Z"`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: SÍ lo caza un test, pero de la raíz: `tests/test_f032_contrato_festivos.py` comprueba el DDL literal `leido_en_utc VARCHAR(40)` en las DOS copias del ORM (R1). La campaña solo corre las suites de sv3 y sv4 (sus líneas base), no `tests/` de la raíz, así que no lo ve.
> Decisión: **muerto fuera de la campaña, no es hueco**. **Aceptado por el humano el 2026-11-18 («acepto»).** Verificado a mano: con el mutante aplicado en cada copia, `python -m pytest tests/test_f032_contrato_festivos.py` cae (1 failed). No se duplica el test dentro de cada servicio: el contrato de la tabla vive en la raíz porque es de las dos copias a la vez (patrón de F-010 y F-056).

### 8. `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py:297` [entero]

- Original: `if sin_dato > 0:`
- Mutado:   `if sin_dato > 1:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `test_f032_r8_sin_dato_sube_a_revision_con_warning` usa `sin_dato = 2`, que pasa `> 0` y `> 1`: no fija el borde.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f032_campana.py::test_f032_r8_una_sola_clave_sin_dato_ya_sube_a_revision`. Verificado a mano: con el mutante aplicado, `test_f032_r8_una_sola_clave_sin_dato_ya_sube_a_revision` cae (`mutar_a_mano.py`, sin campaña).

### 9. `services/partes-persistencia/application/services/festivos_guardados.py:55` [veracidad]

- Original: `if valor is None:`
- Mutado:   `if not valor:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: igual que en la copia de sv4; el guardián de gemelos compara las dos copias con los mismos casos, y ninguno tiene ese nombre.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f032_campana.py::test_f032_r42_un_nombre_no_textual_se_guarda_como_texto`. Verificado a mano: con el mutante aplicado, `test_f032_r42_un_nombre_no_textual_se_guarda_como_texto` cae (`mutar_a_mano.py`, sin campaña).

### 10. `services/partes-persistencia/application/services/refresco_festivos.py:40` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: ningún test intentaba reescribir el recuento.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f032_campana.py::test_f032_r8_el_resultado_del_refresco_es_inmutable`. Verificado a mano: con el mutante aplicado, `test_f032_r8_el_resultado_del_refresco_es_inmutable` cae (`mutar_a_mano.py`, sin campaña).

### 11. `services/partes-persistencia/application/services/refresco_festivos.py:54` [entero]

- Original: `domingo = lunes + _dt.timedelta(days=6)`
- Mutado:   `domingo = lunes + _dt.timedelta(days=7)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: los casos de año cruzado (31/12/2026) dan los mismos años con `days=6` y `days=7`; falta una semana cuyo domingo es el 31/12 (la del 27/12/2023), donde `+7` cae ya en el año siguiente.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f032_campana.py::test_f032_r4_anos_de_la_semana_iso_lunes_a_domingo`. Verificado a mano: con el mutante aplicado, `test_f032_r4_anos_de_la_semana_iso_lunes_a_domingo` cae (`mutar_a_mano.py`, sin campaña).

### 12. `services/partes-persistencia/contrastar_festivos_sesame.py:60` [entero]

- Original: `SALIDA_CONFIGURACION = 2`
- Mutado:   `SALIDA_CONFIGURACION = 3`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: los tests de R31 solo pedían `rc != 0`; el código de cada causa (2, 3, 4) no estaba fijado.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f032_campana.py::test_f032_r31_cada_fallo_sale_con_su_codigo`. Verificado a mano: con el mutante aplicado, `test_f032_r31_cada_fallo_sale_con_su_codigo` cae (`mutar_a_mano.py`, sin campaña).

### 13. `services/partes-persistencia/contrastar_festivos_sesame.py:62` [entero]

- Original: `SALIDA_IMPACTO = 4`
- Mutado:   `SALIDA_IMPACTO = 5`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: ídem: no había test de la lectura de partes fallida (`--impacto` con el repositorio caído).
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f032_campana.py::test_f032_r31_cada_fallo_sale_con_su_codigo`. Verificado a mano: con el mutante aplicado, `test_f032_r31_cada_fallo_sale_con_su_codigo` cae (`mutar_a_mano.py`, sin campaña).

### 14. `services/partes-persistencia/contrastar_festivos_sesame.py:200` [ternario]

- Original: `return ", ".join(dias) if dias else "—"`
- Mutado:   `return ", ".join(dias) if not dias else "—"`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: el test del Markdown buscaba las marcas en el texto entero, no las celdas de cada fila.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f032_campana.py::test_f032_r30_cada_fila_del_markdown_lleva_sus_marcas`. Verificado a mano: con el mutante aplicado, `test_f032_r30_cada_fila_del_markdown_lleva_sus_marcas` cae (`mutar_a_mano.py`, sin campaña).

### 15. `services/partes-persistencia/contrastar_festivos_sesame.py:215` [negacion]

- Original: `if f["faltan_del_respaldo"]:`
- Mutado:   `if not f["faltan_del_respaldo"]:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: «FALTAN DEL RESPALDO» aparecía en el Markdown por alguna fila, sin mirar cuál.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f032_campana.py::test_f032_r30_cada_fila_del_markdown_lleva_sus_marcas`. Verificado a mano: con el mutante aplicado, `test_f032_r30_cada_fila_del_markdown_lleva_sus_marcas` cae (`mutar_a_mano.py`, sin campaña).

### 16. `services/partes-persistencia/contrastar_festivos_sesame.py:220` [negacion]

- Original: `if f["por_defecto"]:`
- Mutado:   `if not f["por_defecto"]:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: «por defecto» se buscaba en el Markdown entero; con el mutante aparece en las otras filas y la búsqueda sigue acertando.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f032_campana.py::test_f032_r30_cada_fila_del_markdown_lleva_sus_marcas`. Verificado a mano: con el mutante aplicado, `test_f032_r30_cada_fila_del_markdown_lleva_sus_marcas` cae (`mutar_a_mano.py`, sin campaña).

### 17. `services/partes-persistencia/contrastar_festivos_sesame.py:225` [logico]

- Original: `f"{' '.join(marcas) or 'ok'} |")`
- Mutado:   `f"{' '.join(marcas) and 'ok'} |")`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: ningún test miraba la celda «ok» de un calendario sin marcas.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f032_campana.py::test_f032_r30_cada_fila_del_markdown_lleva_sus_marcas`. Verificado a mano: con el mutante aplicado, `test_f032_r30_cada_fila_del_markdown_lleva_sus_marcas` cae (`mutar_a_mano.py`, sin campaña).

### 18. `services/partes-persistencia/contrastar_festivos_sesame.py:259` [logico]

- Original: `vacio, tipo="calendario", calendario_id=f["id"] or "",`
- Mutado:   `vacio, tipo="calendario", calendario_id=f["id"] and "",`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: los tests del CSV miraban las filas de impacto y de error, no el id de las de calendario.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f032_campana.py::test_f032_r31_el_csv_lleva_el_id_del_calendario`. Verificado a mano: con el mutante aplicado, `test_f032_r31_el_csv_lleva_el_id_del_calendario` cae (`mutar_a_mano.py`, sin campaña).

### 19. `services/partes-persistencia/contrastar_festivos_sesame.py:299` [logico]

- Original: `return [c for c in cuerpo.get("data") or [] if isinstance(c, dict)]`
- Mutado:   `return [c for c in cuerpo.get("data") and [] if isinstance(c, dict)]`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: el test de `main` comprobaba ficheros y peticiones, no qué calendarios salían del listado.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f032_campana.py::test_f032_r29_listar_calendarios_devuelve_los_de_sesame`. Verificado a mano: con el mutante aplicado, `test_f032_r29_listar_calendarios_devuelve_los_de_sesame` cae (`mutar_a_mano.py`, sin campaña).

### 20. `services/partes-persistencia/contrastar_festivos_sesame.py:339` [booleano]

- Original: `p.add_argument("--ano", type=int, required=True)`
- Mutado:   `p.add_argument("--ano", type=int, required=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: todos los tests pasaban `--ano`.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f032_campana.py::test_f032_r31_el_ano_es_obligatorio`. Verificado a mano: con el mutante aplicado, `test_f032_r31_el_ano_es_obligatorio` cae (`mutar_a_mano.py`, sin campaña).

### 21. `services/partes-persistencia/contrastar_festivos_sesame.py:353` [veracidad]

- Original: `if settings is not None:`
- Mutado:   `if settings:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: es **equivalente**. `settings` es siempre `None` o un `Settings` de pydantic, que no define `__bool__` ni `__len__` (comprobado: `hasattr(Settings, '__len__')` y `'__bool__'` son False con pydantic 2.13.4), así que `is not None` y la veracidad dan lo mismo para todo valor posible.
> Decisión: **mutante equivalente**, sin test. **Aceptado por el humano el 2026-11-18 («acepto»).**

### 22. `services/partes-persistencia/contrastar_festivos_sesame.py:415` [booleano]

- Original: `carpeta.mkdir(parents=True, exist_ok=True)`
- Mutado:   `carpeta.mkdir(parents=False, exist_ok=True)`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `--salida` era siempre `tmp_path`, que ya existe.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f032_campana.py::test_f032_r31_la_salida_se_crea_aunque_falten_carpetas`. Verificado a mano: con el mutante aplicado, `test_f032_r31_la_salida_se_crea_aunque_falten_carpetas` cae (`mutar_a_mano.py`, sin campaña).

### 23. `services/partes-persistencia/contrastar_festivos_sesame.py:429` [logico]

- Original: `print(f"{f['nombre'] or f['id']}: {f['n_festivos']} festivos"`
- Mutado:   `print(f"{f['nombre'] and f['id']}: {f['n_festivos']} festivos"`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: la salida de consola solo se miraba para que no llevara la clave.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f032_campana.py::test_f032_r30_la_consola_resume_cada_calendario`. Verificado a mano: con el mutante aplicado, `test_f032_r30_la_consola_resume_cada_calendario` cae (`mutar_a_mano.py`, sin campaña).

### 24. `services/partes-persistencia/contrastar_festivos_sesame.py:430` [ternario]

- Original: `+ (f" · {' · '.join(marcas)}" if marcas else ""))`
- Mutado:   `+ (f" · {' · '.join(marcas)}" if not marcas else ""))`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: ídem: nadie miraba las marcas de la consola.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f032_campana.py::test_f032_r30_la_consola_resume_cada_calendario`. Verificado a mano: con el mutante aplicado, `test_f032_r30_la_consola_resume_cada_calendario` cae (`mutar_a_mano.py`, sin campaña).

### 25. `services/partes-persistencia/infrastructure/database/orm_models.py:697` [booleano]

- Original: `String(32), nullable=False, server_default=""`
- Mutado:   `String(32), nullable=True, server_default=""`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: SÍ lo caza un test, pero de la raíz: `tests/test_f032_contrato_festivos.py` comprueba `nullable is False` en cada columna que no es la clave en las DOS copias del ORM (R1). La campaña solo corre las suites de sv3 y sv4 (sus líneas base), no `tests/` de la raíz, así que no lo ve.
> Decisión: **muerto fuera de la campaña, no es hueco**. **Aceptado por el humano el 2026-11-18 («acepto»).** Verificado a mano: con el mutante aplicado en cada copia, `python -m pytest tests/test_f032_contrato_festivos.py` cae (1 failed). No se duplica el test dentro de cada servicio: el contrato de la tabla vive en la raíz porque es de las dos copias a la vez (patrón de F-010 y F-056).

### 26. `services/partes-persistencia/infrastructure/database/orm_models.py:700` [booleano]

- Original: `Integer, nullable=False, server_default="0"`
- Mutado:   `Integer, nullable=True, server_default="0"`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: SÍ lo caza un test, pero de la raíz: `tests/test_f032_contrato_festivos.py` comprueba `nullable is False` en cada columna que no es la clave en las DOS copias del ORM (R1). La campaña solo corre las suites de sv3 y sv4 (sus líneas base), no `tests/` de la raíz, así que no lo ve.
> Decisión: **muerto fuera de la campaña, no es hueco**. **Aceptado por el humano el 2026-11-18 («acepto»).** Verificado a mano: con el mutante aplicado en cada copia, `python -m pytest tests/test_f032_contrato_festivos.py` cae (1 failed). No se duplica el test dentro de cada servicio: el contrato de la tabla vive en la raíz porque es de las dos copias a la vez (patrón de F-010 y F-056).

### 27. `services/partes-persistencia/infrastructure/database/orm_models.py:703` [booleano]

- Original: `Text, nullable=False, server_default="{}"`
- Mutado:   `Text, nullable=True, server_default="{}"`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: SÍ lo caza un test, pero de la raíz: `tests/test_f032_contrato_festivos.py` comprueba `nullable is False` en cada columna que no es la clave en las DOS copias del ORM (R1). La campaña solo corre las suites de sv3 y sv4 (sus líneas base), no `tests/` de la raíz, así que no lo ve.
> Decisión: **muerto fuera de la campaña, no es hueco**. **Aceptado por el humano el 2026-11-18 («acepto»).** Verificado a mano: con el mutante aplicado en cada copia, `python -m pytest tests/test_f032_contrato_festivos.py` cae (1 failed). No se duplica el test dentro de cada servicio: el contrato de la tabla vive en la raíz porque es de las dos copias a la vez (patrón de F-010 y F-056).

### 28. `services/partes-persistencia/infrastructure/database/orm_models.py:706` [booleano]

- Original: `Integer, nullable=False, server_default="0"`
- Mutado:   `Integer, nullable=True, server_default="0"`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: SÍ lo caza un test, pero de la raíz: `tests/test_f032_contrato_festivos.py` comprueba `nullable is False` en cada columna que no es la clave en las DOS copias del ORM (R1). La campaña solo corre las suites de sv3 y sv4 (sus líneas base), no `tests/` de la raíz, así que no lo ve.
> Decisión: **muerto fuera de la campaña, no es hueco**. **Aceptado por el humano el 2026-11-18 («acepto»).** Verificado a mano: con el mutante aplicado en cada copia, `python -m pytest tests/test_f032_contrato_festivos.py` cae (1 failed). No se duplica el test dentro de cada servicio: el contrato de la tabla vive en la raíz porque es de las dos copias a la vez (patrón de F-010 y F-056).

### 29. `services/partes-persistencia/infrastructure/database/orm_models.py:709` [entero]

- Original: `String(40), nullable=False, server_default="1970-01-01T00:00:00Z"`
- Mutado:   `String(41), nullable=False, server_default="1970-01-01T00:00:00Z"`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: SÍ lo caza un test, pero de la raíz: `tests/test_f032_contrato_festivos.py` comprueba el DDL literal `leido_en_utc VARCHAR(40)` en las DOS copias del ORM (R1). La campaña solo corre las suites de sv3 y sv4 (sus líneas base), no `tests/` de la raíz, así que no lo ve.
> Decisión: **muerto fuera de la campaña, no es hueco**. **Aceptado por el humano el 2026-11-18 («acepto»).** Verificado a mano: con el mutante aplicado en cada copia, `python -m pytest tests/test_f032_contrato_festivos.py` cae (1 failed). No se duplica el test dentro de cada servicio: el contrato de la tabla vive en la raíz porque es de las dos copias a la vez (patrón de F-010 y F-056).

### 30. `services/partes-persistencia/infrastructure/database/sqlalchemy_festivos_repository.py:45` [entero]

- Original: `omitidas = 0`
- Mutado:   `omitidas = 1`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: el recuento solo va al log INFO y los tests miraban el WARNING de la fila mala, no el resumen.
> Decisión: **test nuevo** `services/partes-persistencia/tests/test_f032_campana.py::test_f032_r11_leer_todas_cuenta_las_omitidas_desde_cero`. Verificado a mano: con el mutante aplicado, `test_f032_r11_leer_todas_cuenta_las_omitidas_desde_cero` cae (`mutar_a_mano.py`, sin campaña).

### 31. `services/partes-persistencia/interface_adapters/api/app.py:87` [veracidad]

- Original: `if repositorio is None:`
- Mutado:   `if not repositorio:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: es **equivalente**. `repositorio` es siempre `None` o un `SqlAlchemyFestivosRepository`, que no define `__bool__` ni `__len__` (comprobado: ni él ni `TablaCalendarioLaboral` definen esos métodos (grep vacío)), así que `is not None` y la veracidad dan lo mismo para todo valor posible.
> Decisión: **mutante equivalente**, sin test. **Aceptado por el humano el 2026-11-18 («acepto»).**

### 32. `services/partes-persistencia/interface_adapters/api/app.py:217` [veracidad]

- Original: `calendario=(calendario if calendario is not None`
- Mutado:   `calendario=(calendario if calendario`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: es **equivalente**. `calendario` es siempre `None` o un `TablaCalendarioLaboral` o un `JsonCalendarioLaboral`, que no define `__bool__` ni `__len__` (comprobado: ninguno define esos métodos (grep vacío en `infrastructure/calendario/`)), así que `is not None` y la veracidad dan lo mismo para todo valor posible.
> Decisión: **mutante equivalente**, sin test. **Aceptado por el humano el 2026-11-18 («acepto»).**

## No muertos: código de salida

| Fichero:línea | Operador | Veredicto | Código |
|---|---|---|---|
| `services/partes-front/application/services/festivos_guardados.py:55` | veracidad | superviviente | 0 |
| `services/partes-front/infrastructure/database/orm_models.py:692` | booleano | superviviente | 0 |
| `services/partes-front/infrastructure/database/orm_models.py:697` | booleano | superviviente | 0 |
| `services/partes-front/infrastructure/database/orm_models.py:700` | booleano | superviviente | 0 |
| `services/partes-front/infrastructure/database/orm_models.py:703` | booleano | superviviente | 0 |
| `services/partes-front/infrastructure/database/orm_models.py:706` | booleano | superviviente | 0 |
| `services/partes-front/infrastructure/database/orm_models.py:709` | entero | superviviente | 0 |
| `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py:297` | entero | superviviente | 0 |
| `services/partes-persistencia/application/services/festivos_guardados.py:55` | veracidad | superviviente | 0 |
| `services/partes-persistencia/application/services/refresco_festivos.py:40` | booleano | superviviente | 0 |
| `services/partes-persistencia/application/services/refresco_festivos.py:54` | entero | superviviente | 0 |
| `services/partes-persistencia/contrastar_festivos_sesame.py:60` | entero | superviviente | 0 |
| `services/partes-persistencia/contrastar_festivos_sesame.py:62` | entero | superviviente | 0 |
| `services/partes-persistencia/contrastar_festivos_sesame.py:200` | ternario | superviviente | 0 |
| `services/partes-persistencia/contrastar_festivos_sesame.py:215` | negacion | superviviente | 0 |
| `services/partes-persistencia/contrastar_festivos_sesame.py:220` | negacion | superviviente | 0 |
| `services/partes-persistencia/contrastar_festivos_sesame.py:225` | logico | superviviente | 0 |
| `services/partes-persistencia/contrastar_festivos_sesame.py:259` | logico | superviviente | 0 |
| `services/partes-persistencia/contrastar_festivos_sesame.py:299` | logico | superviviente | 0 |
| `services/partes-persistencia/contrastar_festivos_sesame.py:339` | booleano | superviviente | 0 |
| `services/partes-persistencia/contrastar_festivos_sesame.py:353` | veracidad | superviviente | 0 |
| `services/partes-persistencia/contrastar_festivos_sesame.py:415` | booleano | superviviente | 0 |
| `services/partes-persistencia/contrastar_festivos_sesame.py:429` | logico | superviviente | 0 |
| `services/partes-persistencia/contrastar_festivos_sesame.py:430` | ternario | superviviente | 0 |
| `services/partes-persistencia/contrastar_festivos_sesame.py:440` | comparacion | indeterminado | 3 |
| `services/partes-persistencia/infrastructure/database/orm_models.py:697` | booleano | superviviente | 0 |
| `services/partes-persistencia/infrastructure/database/orm_models.py:700` | booleano | superviviente | 0 |
| `services/partes-persistencia/infrastructure/database/orm_models.py:703` | booleano | superviviente | 0 |
| `services/partes-persistencia/infrastructure/database/orm_models.py:706` | booleano | superviviente | 0 |
| `services/partes-persistencia/infrastructure/database/orm_models.py:709` | entero | superviviente | 0 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_festivos_repository.py:45` | entero | superviviente | 0 |
| `services/partes-persistencia/interface_adapters/api/app.py:87` | veracidad | superviviente | 0 |
| `services/partes-persistencia/interface_adapters/api/app.py:217` | veracidad | superviviente | 0 |

## Indeterminado: `contrastar_festivos_sesame.py:440`

- Original: `if __name__ == "__main__":` · Mutado: `if __name__ != "__main__":` · Código 3.
- Por qué es indeterminado: con el mutante, **importar** el módulo (lo hace
  `tests/test_f032_contraste.py`) ejecuta `sys.exit(main())` con el `argv` de pytest; argparse
  sale y pytest aborta la recolección («no tests ran»), con un código que no es el 1 de «tests
  fallidos». El arnés solo cuenta como muerto el código 1.
- Decisión: **detectado, no es un hueco**: la suite no llega ni a arrancar. Verificado a mano:
  `mutar_a_mano.py … 440` sobre `tests/test_f032_contraste.py` ⇒ falla, «no tests ran».

## Resultado de la pasada de campaña (implementer, 2026-11-17)

- 32 supervivientes: **18 muertos con tests nuevos** (`test_f032_campana.py` de sv3 y de sv4),
  **11 muertos por los tests de la raíz** que la campaña no corre (los ORM) y **3 equivalentes**
  (`contrastar…:353`, `api/app.py:87` y `:217`). Cada muerto se verificó a mano, mutante a
  mutante (`mutar_a_mano.py`). No se relanzó la campaña.
- El indeterminado se detecta (la recolección aborta). Cero supervivientes sin justificar.

## Ficheros sin mutantes

Cada uno tiene líneas en alcance y el generador no ha sacado de ellas ni un mutante: la campaña no las ha juzgado. Declara por qué no hay nada que mutar (solo declaraciones, cadenas, imports) o qué test de la fase RED cubre el cambio. El reviewer hace la prueba de control (`generar_mutantes` sin exclusión de alcance) y ninguna declaración puede quedarse en `PENDIENTE` al cerrar la feature.

### `services/partes-front/application/services/reparto_obras.py` — 3 líneas en alcance, 0 mutantes

#### Declaración

> Las 3 líneas son de docstring (el `aviso_sesame` no se aplana); lo retirado (`sesame_bloqueo`) son borrados, que no se mutan. El comportamiento lo cubre `test_f022_reparto_obras.py` (T16).

### `services/partes-front/config/logging_config.py` — 4 líneas en alcance, 0 mutantes

#### Declaración

> Un `import logging`, dos líneas de comentario y `logging.getLogger("httpx").setLevel(logging.WARNING)`, sin operador ni literal que el generador mute. Lo cubre la fase RED de T32: `tests/test_f032_logs_sin_dni.py` (nivel de httpx y ningún DNI en los registros); quitada la línea, cae.

### `services/partes-front/infrastructure/transfer/resultado_sigrid.py` — 3 líneas en alcance, 0 mutantes

#### Declaración

> Las 3 líneas son de docstring; lo retirado (`MOTIVO_SIN_SESAME`, `sin_sesame`) son borrados. Lo cubre `test_f032_sin_bloqueo.py` (ninguna línea nueva lleva `[SIN-SESAME]`).

### `services/partes-persistencia/config/logging_config.py` — 4 líneas en alcance, 0 mutantes

#### Declaración

> Igual que en sv4: `import`, comentario y el `setLevel` de httpx. Lo cubre `tests/test_f032_logs_sin_dni.py` de sv3 (T32, RED real).

