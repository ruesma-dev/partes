<!-- progress/mutacion_F-085.md -->
# F-085 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-085 --workers 3` el 2026-11-28 07:50.

## Alcance

Origen del diff: **rama** (`b5e935b52a5a679612c5b210093127daeb8e0946` .. `feature/F-085-codigo-de-incidencia-convierte-la-linea`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/partes-front/application/services/clase_hora.py` | 26 | 5 |
| `services/partes-front/application/services/conversion_clase.py` | 110 | 28 |
| `services/partes-front/application/services/racha_incidencia.py` | 26 | 11 |
| `services/partes-front/config/settings.py` | 7 | 1 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 119 | 24 |
| `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` | 4 | 0 — sin mutantes |
| `services/partes-front/interface_adapters/web/app.py` | 43 | 13 |
| `services/partes-persistencia/application/services/recurso_conciliador.py` | 35 | 11 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 8 | 0 — sin mutantes |
| `services/partes-transfer/application/pipelines/registro_pipeline.py` | 79 | 37 |
| `services/partes-transfer/application/services/racha_ciz.py` | 95 | 28 |
| `services/partes-transfer/application/services/reglas_registro.py` | 24 | 12 |
| `services/partes-transfer/config/settings.py` | 6 | 1 |
| `services/partes-transfer/domain/models/registro_models.py` | 13 | 1 |
| **Total** | **595** | **172** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 172 |
| Mutantes evaluados | 19 (+ 81 veredictos reutilizados) |
| Muertos | 95 |
| Supervivientes | 5 (todos medidos: sin mapa no se poda) |
| Timeouts | 0 |
| Indeterminados | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 4613.2 s |
| SHA de HEAD medido | `17dee7e3cea3cae3743787ba604a16baddf72bf9` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-085_guh4p7nm/wk_0/services/partes-front` | 835.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-085_guh4p7nm/wk_0/services/partes-transfer` | 43.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-085_guh4p7nm/wk_1/services/partes-front` | 836.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-085_guh4p7nm/wk_1/services/partes-persistencia` | 49.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-085_guh4p7nm/wk_1/services/partes-transfer` | 35.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-085_guh4p7nm/wk_2/services/partes-front` | 835.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-085_guh4p7nm/wk_2/services/partes-transfer` | 36.4 |
| Media por mutante evaluado (s) | 242.8 |
| Timeout efectivo por mutante (s) | 1674 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 600 |
| Workers | 3 |
| Un mutante por línea | sí — 172 generados → 110 candidatos, uno por línea |
| Muestreo | sí — 100 de 110 candidatos, semilla `20261030`, nivel `critico`; tope: 60 % de 110 candidatos, acotado a [100, 300] |
| Modo | incremental desde `7bf0a638c5b40c82460d6309855aab8bee69e4bf` — 81 reutilizados, 9 reevaluados, 10 de control |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 394.6 (19 mutantes) |

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/conversion_clase.py:78` [veracidad]

- Original: `return clase.letra if clase is not None else None`
- Mutado:   `return clase.letra if clase else None`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `_letra` es privada. `clase` sale de una sola llamada `tabla.por_sigrid.get(normalizar_codigo(codigo))`, sin valor por defecto: es `None` o una `ClaseIncidencia`, la única clase que guarda `por_sigrid` (la construye `parsear_tabla`). `ClaseIncidencia` es una dataclass sin `__bool__` ni `__len__`, así que toda instancia es verdadera. `is not None` y la veracidad coinciden en todo el dominio, y ningún test puede ver la diferencia.
> Decisión: **mutante equivalente, pendiente de aceptación del humano**. Demostración ejecutable: `progress/equivalentes_F-085.py` (#1), exit 0 (salida en `progress/impl_F-085.md`, «Campaña de mutación (T9, T14)»). Comprueba por el AST la única llamada `get` sin defecto, que el tipo guardado es `ClaseIncidencia` y que no tiene `__bool__`/`__len__`. Con el mutante en memoria, `_letra` da lo mismo en 84 casos (los 42 códigos, con bordes `None`, «», « », «CI», minúsculas, espacios, CIZ, CI* sin letra y códigos de horas, × la tabla real y `None`). Control negativo (`clase is None`): sí se distingue.

### 2. `services/partes-front/application/services/conversion_clase.py:89` [veracidad]

- Original: `if error is not None:`
- Mutado:   `if error:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `error` sale de `error_de_codigo`, cuyos tres `return` son `None`, `MOTIVO_CIZ_NO_SE_ELIGE` (constante no vacía) o `motivo_sin_letra(codigo)`, que empieza siempre por «El código …» y nunca está vacía. Ninguna salida es falsa sin ser `None`, así que `is not None` y la veracidad deciden lo mismo.
> Decisión: **mutante equivalente, pendiente de aceptación del humano**. Demostración ejecutable: `progress/equivalentes_F-085.py` (#2), exit 0 (salida en `progress/impl_F-085.md`, «Campaña de mutación (T9, T14)»). Comprueba los `return` por el AST, que la constante no está vacía y que `motivo_sin_letra` no da «» en ningún código. `decidir` da lo mismo, original y mutado, en 6048 casos (42 códigos × 72 estados de la línea, con `es_incidencia`, la letra y `tipo_hora` vacíos, en minúsculas y de otra letra, × la tabla real y `None`). Control negativo (`error is None`): sí se distingue.

### 3. `services/partes-front/infrastructure/database/parte_repository.py:3388` [veracidad]

- Original: `if clase.error is not None:`
- Mutado:   `if clase.error:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `clase` sale de una sola llamada a `decidir_clase`, que es `conversion_clase.decidir`. El campo `error` de la `ClaseNueva` solo se rellena con el `error` de `error_de_codigo`: `None` o un motivo no vacío, el dominio del superviviente 2. `clase.error` nunca es «».
> Decisión: **mutante equivalente, pendiente de aceptación del humano**. Demostración ejecutable: `progress/equivalentes_F-085.py` (#5), exit 0 (salida en `progress/impl_F-085.md`, «Campaña de mutación (T9, T14)»). Comprueba por el AST la única asignación de `clase` y que `error=` solo recibe `error`. `set_registro_hora`, original y mutado, en SQLite en memoria da lo mismo en 252 casos (42 códigos × 3 líneas, de horas con `horas_orig`, extra automática e incidencia AT, × la tabla real y `None`): resultado o excepción, las 9 columnas de las tres líneas y el deshacer. Control negativo (`clase.error is None`): sí se distingue.

### 4. `services/partes-transfer/application/services/racha_ciz.py:324` [veracidad]

- Original: `if previo is None:`
- Mutado:   `if not previo:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `previo` es el primer valor de `inicio_previo`, cuyos `return` dan `None` o `primera`, una de las `candidatas`: una `LineaSigrid`. `LineaSigrid` es una dataclass sin `__bool__` ni `__len__`, así que toda instancia es verdadera, también con todos los campos a 0 o vacíos. `is None` y `not` coinciden en todo el dominio.
> Decisión: **mutante equivalente, pendiente de aceptación del humano**. Demostración ejecutable: `progress/equivalentes_F-085.py` (#9), exit 0 (salida en `progress/impl_F-085.md`, «Campaña de mutación (T9, T14)»). Comprueba por el AST los `return` de `inicio_previo` y que el tipo no tiene `__bool__`/`__len__`. `decidir_inicio`, original y mutado, da lo mismo en 4000 casos al azar con semilla fija: candidatas de 0 a 6 con recurso, fecha, código, synckey (`partes:<i>`, `:ciz`, manual, `None`), `can`, parte, enlace y marca al azar, y la mitad con una racha con inicio previo. El banco exige al menos 50 `mover` y 50 `parte_cerrado`. Control negativo (`previo is not None`): sí se distingue.

### 5. `services/partes-transfer/application/services/racha_ciz.py:327` [veracidad]

- Original: `cod = parte.cod if parte is not None else None`
- Mutado:   `cod = parte.cod if parte else None`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `parte` sale de `partes.get(int(previo.hmoide or 0))`, sin valor por defecto. En el único llamador, el paso 6 bis de `registro_pipeline.py`, `partes` es `{h: ParteSigrid(...)}`. `ParteSigrid` es una dataclass sin `__bool__` ni `__len__`, así que `parte` es `None` o siempre verdadera, también con `cod` «» o `est` `None`.
> Decisión: **mutante equivalente, pendiente de aceptación del humano**. Demostración ejecutable: `progress/equivalentes_F-085.py` (#8), exit 0 (salida en `progress/impl_F-085.md`, «Campaña de mutación (T9, T14)»). Comprueba en el fuente el `partes.get` y la construcción de `partes` con `ParteSigrid` en el pipeline, y que el tipo no tiene `__bool__`/`__len__`. Usa el mismo banco de 4000 casos que #9, con partes En registro, Cerrado, con `cod`/`est` `None` y con `cod` «»: misma decisión y mismo motivo. Control negativo (`parte is None`): sí se distingue.

## No muertos: código de salida

| Fichero:línea | Operador | Veredicto | Código |
|---|---|---|---|
| `services/partes-front/application/services/conversion_clase.py:78` | veracidad | superviviente | 0 |
| `services/partes-front/application/services/conversion_clase.py:89` | veracidad | superviviente | 0 |
| `services/partes-front/infrastructure/database/parte_repository.py:3388` | veracidad | superviviente | 0 |
| `services/partes-transfer/application/services/racha_ciz.py:324` | veracidad | superviviente | 0 |
| `services/partes-transfer/application/services/racha_ciz.py:327` | veracidad | superviviente | 0 |

## Ficheros sin mutantes

Cada uno tiene líneas en alcance y el generador no ha sacado de ellas ni un mutante: la campaña no las ha juzgado. Declara por qué no hay nada que mutar (solo declaraciones, cadenas, imports) o qué test de la fase RED cubre el cambio. El reviewer hace la prueba de control (`generar_mutantes` sin exclusión de alcance) y ninguna declaración puede quedarse sin escribir al cerrar la feature.

### `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` — 4 líneas en alcance, 0 mutantes

#### Declaración

> Por qué no hay nada que mutar, o qué test lo cubre: Las 4 líneas en alcance son un comentario y dos constantes de cadena (`MOTIVO_CODIGO_INCIDENCIA = "codigo_incidencia"` y `MOTIVO_DESHACER_CODIGO_INCIDENCIA = "deshacer_codigo_incidencia"`): no hay operador, comparación ni rama que mutar. Su valor lo afirman `test_f085_r9_r11_convertir_responde_y_pide_recalculo` (el mensaje de la cola lleva `motivo == MOTIVO_CODIGO_INCIDENCIA`) y `test_f085_r10_r11_deshacer_por_el_endpoint` (`MOTIVO_DESHACER_CODIGO_INCIDENCIA`), en `services/partes-front/tests/test_f085_conversion.py`.

### `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` — 8 líneas en alcance, 0 mutantes

#### Declaración

> Por qué no hay nada que mutar, o qué test lo cubre: Las 8 líneas en alcance (`fetch_registros_para_recurso`) son el docstring, un comentario, una columna más en el `select` (`ParteRegistroOrm.hora_match_method`), un nombre más en el desempaquetado de la fila (`hora_metodo`) y una clave más en el dict (`"hora_match_method": hora_metodo`). No hay operador, comparación ni rama que mutar. Las cubre `services/partes-persistencia/tests/test_f085_sv3_manual.py::test_f085_r17_fetch_trae_hora_match_method` (fase RED de T6: falló antes de añadir la columna), además de `test_f037_revert.py::test_f037_r9_la_unica_clave_nueva_es_la_marca`, que fija el conjunto de claves.

