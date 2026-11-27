<!-- progress/mutacion_F-084.md -->
# F-084 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-084 --workers 3` el 2026-11-27 09:00.

## Alcance

Origen del diff: **rama** (`d11d228b2194b520e5249a55c6b3b91b555e3190` .. `feature/F-084-partes-con-problemas`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/partes-front/application/services/partes_con_problemas.py` | 289 | 75 |
| `services/partes-front/infrastructure/database/orm_models.py` | 6 | 2 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 217 | 83 |
| `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` | 3 | 0 — sin mutantes |
| `services/partes-front/interface_adapters/web/app.py` | 101 | 32 |
| `services/partes-front/interface_adapters/web/identidad.py` | 7 | 0 — sin mutantes |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | 6 | 2 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 17 | 4 |
| **Total** | **646** | **198** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 198 |
| Mutantes evaluados | 27 (+ 73 veredictos reutilizados) |
| Muertos | 93 |
| Supervivientes | 7 (todos medidos: sin mapa no se poda) |
| Timeouts | 0 |
| Indeterminados | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 7109.1 s |
| SHA de HEAD medido | `6ef7b5e4cd4c70359134a8cbc9a80e2d36d748aa` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-084_ntx2erad/wk_0/services/partes-front` | 624.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-084_ntx2erad/wk_1/services/partes-front` | 623.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-084_ntx2erad/wk_2/services/partes-front` | 643.8 |
| Media por mutante evaluado (s) | 263.3 |
| Timeout efectivo por mutante (s) | 1288 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 600 |
| Workers | 3 |
| Un mutante por línea | sí — 198 generados → 131 candidatos, uno por línea |
| Muestreo | sí — 100 de 131 candidatos, semilla `20261030`, nivel `critico`; tope: 60 % de 131 candidatos, acotado a [100, 300] |
| Modo | incremental desde `8474ce964ec3f257d5e304c9a617e1942f1675c4` — 73 reutilizados, 18 reevaluados, 9 de control |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 627.8 (27 mutantes) |

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/partes_con_problemas.py:144` [veracidad]

- Original: `return fecha_int is not None and fecha_int > 0`
- Mutado:   `return fecha_int and fecha_int > 0`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `_fecha_valida` es privada y sus 3 llamadores (`fecha_posterior_al_correo`, `motivos_activo`, `elegir_sustituto`) la usan siempre bajo `not`; nadie fuera del módulo la importa. Con `None` o `0` el mutado devuelve `None`/`0` en vez de `False`, la misma decisión bajo `not`; con negativos y positivos devuelve lo mismo. Ningún test puede ver la diferencia por la API pública.
> Decisión: **mutante equivalente, aceptado por el humano el 2026-11-27 («ok» a la PARADA 2)**. Demostración ejecutable: `progress/equivalentes_F-084.py` (#1), exit 0 (salida en `progress/impl_F-084.md`, «Campaña de mutación»): comprueba por el AST que todo `_fecha_valida(...)` está dentro de un `not` y, con el mutante en memoria, que `motivos_activo`, `fecha_posterior_al_correo`, `elegir_sustituto`, `clasificar` y `resumen` dan lo mismo en 5.000 casos con `fecha_int` None, 0, −5, 1 y fechas reales. Control negativo (`>= 0`): sí se distingue.

### 2. `services/partes-front/application/services/partes_con_problemas.py:174` [veracidad]

- Original: `if recibido is None:`
- Mutado:   `if not recibido:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `recibido` sale de `_instante`, que solo tiene tres `return`: `None` (except) y `momento.replace(...)` / `momento.astimezone(...)` sobre `momento = datetime.fromisoformat(...)`. Un `datetime` no define `__bool__` ni `__len__`: siempre es verdadero, también `datetime.min`.
> Decisión: **mutante equivalente, aceptado por el humano el 2026-11-27 («ok» a la PARADA 2)**. Demostración ejecutable: `progress/equivalentes_F-084.py` (#2), exit 0 (salida en `progress/impl_F-084.md`, «Campaña de mutación»): dominio por el AST de `_instante`, tipo de `datetime` y 5.000 casos con instantes None, «», « », ilegibles, `0001-01-01T00:00:00`, medianoche y con zona. Control negativo (`is not None`): sí se distingue.

### 3. `services/partes-front/application/services/partes_con_problemas.py:244` [veracidad]

- Original: `if sustituto is None:`
- Mutado:   `if not sustituto:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: El único llamador de `motivo_sustituido` es `clasificar`, que le pasa `elegir_sustituto(...)`: `None`, `por_id.get(...)` (un `DocProblema` o `None`) o un candidato `DocProblema`. `DocProblema` es una dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, aunque traiga todos los campos vacíos. Es equivalencia de dominio, no de firma (la función es pública).
> Decisión: **mutante equivalente, aceptado por el humano el 2026-11-27 («ok» a la PARADA 2)**. Demostración ejecutable: `progress/equivalentes_F-084.py` (#3), exit 0 (salida en `progress/impl_F-084.md`, «Campaña de mutación»): comprueba el llamador y los cinco `return` de `elegir_sustituto` por el AST, el tipo y 5.000 casos de `clasificar`. Control negativo (`if True:`): sí se distingue.

### 4. `services/partes-front/infrastructure/database/parte_repository.py:4910` [veracidad]

- Original: `if motivo is None:`
- Mutado:   `if not motivo:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `motivo` sale de `motivo_congelacion_documento`, cuyos cinco `return` son `None` o una de `MOTIVO_DOC_ENCOLADO`, `MOTIVO_DOC_REGISTRADO`, `MOTIVO_DOC_DEDICACION`, `MOTIVO_DOC_APROBADO`: cuatro cadenas no vacías. `is None` y `not` coinciden en todo el dominio.
> Decisión: **mutante equivalente, aceptado por el humano el 2026-11-27 («ok» a la PARADA 2)**. Demostración ejecutable: `progress/equivalentes_F-084.py` (#4), exit 0 (salida en `progress/impl_F-084.md`, «Campaña de mutación»): dominio por el AST, constantes no vacías y `_insignia_congelado` original y mutado iguales en 960 combinaciones de `approved` y estados de línea (vacíos, mayúsculas, espacios). Control negativo (`is not None`): sí se distingue.

### 5. `services/partes-front/infrastructure/database/parte_repository.py:5035` [veracidad]

- Original: `if motivo is not None:`
- Mutado:   `if motivo:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `motivo` sale de `motivo_no_recuperable`, cuyos cuatro `return` son `None` o una de `MOTIVO_NO_REC_ACTIVO`, `MOTIVO_NO_REC_PAPELERA`, `MOTIVO_NO_REC_RETIRADO`: tres cadenas no vacías.
> Decisión: **mutante equivalente, aceptado por el humano el 2026-11-27 («ok» a la PARADA 2)**. Demostración ejecutable: `progress/equivalentes_F-084.py` (#5), exit 0 (salida en `progress/impl_F-084.md`, «Campaña de mutación»): dominio por el AST, constantes no vacías y `recuperar_parte` sobre SQLite en memoria en 30 casos (activo, sustituido, papelera, retirado, aprobado, sin fecha, sin líneas, en Sigrid × sin fecha y dos fechas), comparando resultado o excepción y estado final. Control negativo (`is None`): sí se distingue.

### 6. `services/partes-front/interface_adapters/web/app.py:2284` [veracidad]

- Original: `if parsed is None:`
- Mutado:   `if not parsed:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `parsed` sale de `_parse_fecha_to_iso_int`, que solo devuelve `None` o una tupla de 2 (`(iso, YYYYMMDD)`): una tupla no vacía siempre es verdadera.
> Decisión: **mutante equivalente, aceptado por el humano el 2026-11-27 («ok» a la PARADA 2)**. Demostración ejecutable: `progress/equivalentes_F-084.py` (#6), exit 0 (salida en `progress/impl_F-084.md`, «Campaña de mutación»): dominio por el AST (todo `return` es `None` o una tupla de 2) y `POST /api/partes/{id}/recuperar` original y mutado con el mismo estado y JSON en 128 peticiones (16 fechas, vacías e inválidas incluidas, × 4 estados × existe/no existe). Control negativo (`if parsed:`): sí se distingue.

### 7. `services/partes-front/interface_adapters/web/app.py:2300` [veracidad]

- Original: `if res is None:`
- Mutado:   `if not res:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `res` sale de `ParteReviewRepository.recuperar_parte` (la única implementación; `_RepoRoto` de los tests hereda de ella), que solo devuelve `None` o `{"document_id", "fecha"}`: un dict de 2 claves siempre es verdadero.
> Decisión: **mutante equivalente, aceptado por el humano el 2026-11-27 («ok» a la PARADA 2)**. Demostración ejecutable: `progress/equivalentes_F-084.py` (#7), exit 0 (salida en `progress/impl_F-084.md`, «Campaña de mutación»): dominio por el AST (dos `return`: `None` y el dict de esas 2 claves; ninguna otra `def recuperar_parte` fuera de los tests) y las mismas 128 peticiones HTTP. Control negativo (`is not None`): sí se distingue.

## No muertos: código de salida

| Fichero:línea | Operador | Veredicto | Código |
|---|---|---|---|
| `services/partes-front/application/services/partes_con_problemas.py:144` | veracidad | superviviente | 0 |
| `services/partes-front/application/services/partes_con_problemas.py:174` | veracidad | superviviente | 0 |
| `services/partes-front/application/services/partes_con_problemas.py:244` | veracidad | superviviente | 0 |
| `services/partes-front/infrastructure/database/parte_repository.py:4910` | veracidad | superviviente | 0 |
| `services/partes-front/infrastructure/database/parte_repository.py:5035` | veracidad | superviviente | 0 |
| `services/partes-front/interface_adapters/web/app.py:2284` | veracidad | superviviente | 0 |
| `services/partes-front/interface_adapters/web/app.py:2300` | veracidad | superviviente | 0 |

## Ficheros sin mutantes

Cada uno tiene líneas en alcance y el generador no ha sacado de ellas ni un mutante: la campaña no las ha juzgado. Declara por qué no hay nada que mutar (solo declaraciones, cadenas, imports) o qué test de la fase RED cubre el cambio. El reviewer hace la prueba de control (`generar_mutantes` sin exclusión de alcance) y ninguna declaración puede quedarse sin escribir al cerrar la feature.

### `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` — 3 líneas en alcance, 0 mutantes

#### Declaración

> Por qué no hay nada que mutar, o qué test lo cubre: las 3 líneas (52–54) son un comentario `#:` y dos constantes de cadena (`MOTIVO_RECUPERAR_PARTE`, `MOTIVO_DESHACER_RECUPERAR`), sin operador ni literal que el generador mute (prueba de control del reviewer: 0 mutantes en esas líneas). Lo cubre la fase RED de T7: `tests/test_f084_portal.py::test_f084_motivos_del_recalculo` (valor exacto de las dos) y `…::test_f084_r23_deshacer_recuperar_pide_su_recalculo` (los dos motivos llegan a la cola).

### `services/partes-front/interface_adapters/web/identidad.py` — 7 líneas en alcance, 0 mutantes

#### Declaración

> Por qué no hay nada que mutar, o qué test lo cubre: las 7 líneas (10–16) son texto del docstring del módulo (qué escribe `undo_log.actor`: solo `parte_recuperar`, F-084); no hay código. El comportamiento que describe lo cubren `tests/test_f084_recuperar.py::test_f084_r23_las_demas_acciones_no_ganan_reactivados_ni_actor` y los tests de recuperar con actor de T5.

