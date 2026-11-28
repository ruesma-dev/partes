# F-085 · Informe del implementer (`critico`)

Rama `feature/F-085-codigo-de-incidencia-convierte-la-linea` (copia `partes-wt-f085`, base
`ae0fac7`). Hechas T1–T8 y T10–T13, una por commit. T9 y T14 (mutación) quedan para la pasada de
campaña del líder. T15–T17 son MANUAL (humano). T18 es `init.sh`, abajo. `MOVER_INICIO` nace
**apagado** en sv4 y en sv5.

## Qué cambió

**Parte A (código de incidencia en el selector)**
- **sv4**: elegir un CI* con letra en `config/incidencias.yaml` convierte la línea en incidencia
  con la forma canónica: `es_incidencia`, la letra en `tipo_hora` e `incidencia_codigo`, y horas
  y `horas_orig` nulos. Otra letra cambia la letra. Un código de horas devuelve una incidencia a
  horas con las horas vacías, lo que revoca F-066 R14. CIZ y un CI* sin letra dan 400 sin tocar
  nada. Un cambio de clase:
  - deja la entrada de deshacer `registro_clase`;
  - pide UN recálculo compartido (F-049) de los partes de ese recurso y día, con motivo
    `codigo_incidencia` (`deshacer_codigo_incidencia` al deshacer);
  - añade a la respuesta `clase_cambiada`, `es_incidencia`, `incidencia_codigo` y `recalculo`;
  - hace que `app.js` recargue la página.
- **sv3**: el casado de recurso no pisa el código de una línea con `hora_match_method = "manual"`.
  Solo actualiza la categoría, `hora_candef` y el precio, y deja un INFO `hora_manual_respetada`.
  `fetch_registros_para_recurso` trae además `hora_match_method`.
- **sv5**: una línea que no es incidencia con un código CI* o CIZ (o un `hora_ide` que es un CI*
  de su recurso) se omite con `MOTIVO_CODIGO_INCIDENCIA`. La guarda va tras las omisiones previas
  y antes de mensuales y de «sin horas». `HoraRecurso.es_incidencia` usa `es_codigo_ci`.

**Parte B (el inicio se recoloca, con `MOVER_INICIO` y `MOVER_CIZ`)**
- **sv5**:
  - `racha_ciz.inicio_previo` y `decidir_inicio` (puras) y el motivo `inicio_en_parte_cerrado`.
  - En `_ciz_de_racha`, los `inicio` con CI* ≠ CIZ y tramo suman sus synckeys a la MISMA llamada
    `lineas_de_racha` (al final, sin repetir) y el parte del inicio previo a la MISMA llamada
    `estados_de_partes`.
  - Va después del hermano de F-062, sin cambios en él. Resultados: `MOVER` ⇒ `a.mover` (rama
    genérica con `stmt_mover_linea` y `movida_de`); enlazada o parte cerrado ⇒ omitir; sin
    inicio previo ⇒ `INSERT`, más el WARNING `racha_inicio_no_movido` si había una posterior
    de su código.
  - El INFO dice `inicio_movido` cuando lo movido no es un CIZ.
- **sv4**:
  - `_fin_movido` elige el motivo por `hora_codigo` de la escrita: CIZ ⇒ `fin_movido`; otro ⇒
    `inicio_movido`, con el mismo CAS.
  - `aviso_desordenada(hist, f, clave)`: con `MOVER_INICIO`, un `inicio` cuyo siguiente día que
    cuenta es de su clave no avisa.
  - `lineas_para_registro(..., mover_inicio=)` y la app pasa `settings.mover_inicio`.

## Ficheros

- sv4: `application/services/clase_hora.py`, `application/services/conversion_clase.py` (nuevo),
  `application/services/racha_incidencia.py`, `infrastructure/database/parte_repository.py`,
  `infrastructure/persistencia/recalculo_publisher.py`, `interface_adapters/web/app.py`,
  `static/app.js`, `config/settings.py`.
- sv3: `application/services/recurso_conciliador.py`,
  `infrastructure/database/sqlalchemy_parte_repository.py`.
- sv5: `domain/models/registro_models.py`, `application/services/reglas_registro.py`,
  `application/services/racha_ciz.py`, `application/pipelines/registro_pipeline.py`,
  `config/settings.py`.
- Tests nuevos:
  - sv4: `tests/test_f085_conversion.py` y `tests/test_f085_inicio_movido_sv4.py`;
  - sv3: `tests/test_f085_sv3_manual.py`;
  - sv5: `tests/test_f085_sv5_guarda.py` y `tests/test_f085_inicio_movido.py`;
  - raíz: `tests/test_f085_documentacion.py`.
- Tests ajenos enmendados, con su porqué en el propio test:
  - `test_f066_set_registro_hora` r14 y r18 (F-085 R3/R4);
  - `test_f017_punto_unico` (25 `_actor(request)`);
  - `test_f037_revert` r9 (clave `hora_match_method`);
  - `test_f043_portal_fecha` r19 (+1 `location.reload`, el de R13).
- Docs: `docs/ARCHITECTURE.md` (semánticas 3 y 4), `docs/referencia/partes-proyecto.md` (§3.5,
  §4.4 y §6.6), `progress/current.md`, `tasks.md`.
- **Ecosistema** (sí cruza la frontera: hay motivos nuevos y `MOVER_INICIO` en sv4 y sv5):
  `azure-apps/partes.md`, en dos commits aparte **sin push**: `761c28e` (parte A) y `60d7f70`
  (parte B). El `pull --rebase` no dio conflicto. Al hacer el push, el humano tiene que hacer
  antes `pull`.

## Decisiones y desviaciones (justificadas también en `progress/current.md`)

1. `set_registro_hora(..., incidencias=tabla)` en vez de `clase: ClaseNueva`. La clase se decide
   dentro de la transacción con el estado leído (sin carrera). `decidir` sigue siendo puro.
2. Devuelve `False` si la línea no existe, no `None`: el test de F-066 exige `is False`.
3. La conversión pone `extra_auto = False`. Si no, sv3 borraría la línea convertida como una
   extra automática suya. Deshacer lo restaura (`_REG_UNDO_MARCAS`).
4. Selección del MISMO parte con cola: de una en una, con aviso (D16, ciclo 1).
5. Parte B: las synckeys de los `previos` se añaden al final y sin repetir. Apagado, la llamada
   es idéntica a la de la base (R27).
6. LÍMITE DE SERVICIO: no hay duplicación nueva. `es_codigo_ci` (sv5) y `es_codigo_incidencia`
   (sv4) no son gemelas: sv5 incluye CIZ a propósito (guarda), y sv4 lo excluye (no se elige).

## Fase RED (trazas reales; comando: `<venv>\python.exe -m pytest <fichero> -q` en el servicio)

- **T1** `tests/test_f085_conversion.py`, antes de T2:
  `E   ImportError: cannot import name 'conversion_clase' from 'application.services' (unknown location)`
- **T1/T3** el mismo fichero, con T2 hecho y sin T3:
  `31 failed, 56 passed, 1 warning in 15.13s`
  (`FAILED ...::test_f085_r3_repo_cambia_de_letra - Typ...`, `...::test_f085_r11_sin_cola - KeyError: 'rec...`)
- **T6** sv3 `tests/test_f085_sv3_manual.py`: `7 failed, 16 passed in 3.98s`
  (`E  AssertionError: assert {'categoria':...de': 100, ...} == {'categoria':...o_hora': 15.0}`: la
  línea manual recibía `hora_codigo 'HLOF'`, `hora_ide 100`).
- **T7** sv5 `tests/test_f085_sv5_guarda.py`: `14 failed, 31 passed in 0.98s`
  (`E  AssertionError: assert ('escribir', None) == ('omitir', 'c...en el portal')`).
- **T10** sv5 `tests/test_f085_inicio_movido.py`, primero:
  `E   ImportError: cannot import name 'MOTIVO_INICIO_EN_PARTE_CERRADO' from 'application.services.racha_ciz'`.
  Con la regla pura hecha y el pipeline sin tocar: `11 failed, 42 passed` (`E  AssertionError:
  assert ['insert'] == ['mover']` en R30a, R31 y R21; `assert [] == [('WARNING', ...18 ide=7001')]`
  en R23; `assert 'escribir' == 'omitir'` en R26).
- **T12** sv4 `tests/test_f085_inicio_movido_sv4.py`, primero:
  `E   ImportError: cannot import name 'MOTIVO_INICIO_MOVIDO'`. Con la regla pura y sin tocar el
  repositorio: `7 failed, 11 passed` (`E  TypeError: ...lineas_para_registro() got an unexpected
  keyword argument 'mover_inicio'`; `E  AssertionError: assert ('omitido' == 'omitido'` en R28,
  por el motivo `fin_movido`; `E  KeyError: 'mover_inicio'`).
- En verde tras cada tarea (detalle en las suites de abajo).

## `init.sh` del ciclo 0 (detalle del ciclo 1 abajo)

Exit 0 en la 2.ª pasada; la 1.ª cayó solo en el flaky `test_f059_r9` (`nieto.pid`), reintentado
1 vez de 3. Raíz `2553 passed, 50 skipped`; sv1 74, sv2 579, sv3 2989, sv4 4254, sv5 1988;
`PUERTA COBERTURA` 219/219; `PUERTA CARRIL` y `CAPA E2E`, N/A. Antes, sueltas: sv4 falló solo
en el recuento de recargas de F-043 (enmendado en T12).

## Verificaciones MANUAL pendientes (humano)

En `progress/current.md`, con comando y resultado esperado: M1 (parte A, con el paso de D16), M2
y M3 (parte B, local y en modo pruebas), M5 (producción, solo lectura). M4 (D15) queda **fuera**.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | Ciclo 1: 12 442 en verde (raíz 2553 con 50 skipped, sv1 74, sv2 579, sv3 2989, sv4 4259, sv5 1988), 0 fallos. Ciclo 0: 12 437 |
| Cobertura de líneas cambiadas | 100,0 % (220/220, umbral 90 % de `critico`) en el ciclo 1, según la línea `PUERTA COBERTURA`. Ciclo 0: 219/219 |
| Mutantes generados / supervivientes | 172 generados, muestra 100: 91 muertos, 9 supervivientes, 0 timeouts (`progress/mutacion_F-085.md`). 4 los matan tests nuevos y 5 son equivalentes demostrados (`progress/equivalentes_F-085.py`); falta el repaso `--incremental` del líder |
| Tiempo de la suite | Ciclo 1: raíz 1355,60 s y sv4 1126,23 s; sv1, sv2, sv3 y sv5 en caché. Ciclo 0: sv3 65,63 s, sv2 50,22 s, sv5 36,43 s y sv1 19,76 s |
| Capa e2e | `CAPA E2E: N/A (ningún servicio declara el bloque e2e)` |

## Pendiente

- Repaso `--incremental` de la campaña y análisis en `mutacion_F-085.md` (T9, T14): líder.
- MANUAL M1, M2, M3 y M5 (T15–T17): humano.
- Push del humano: la rama y los dos commits de `azure-apps`.
- Despliegue: sv3, sv4 y sv5. `MOVER_INICIO` sigue apagado hasta después de M2.

## Ciclo 1 (CHANGES_REQUESTED en 33663c4, `progress/review_F-085.md`)

**Cambio 1 (R1), hecho.** En `parte_repository.py` (`_fin_movido`), `cod and cod != "CIZ"` pasa a ser
`cod and not es_codigo_fin(cod)`, con `es_codigo_fin` importada de `clase_hora.py`. El
comportamiento no cambia. `prohibido` de `test_f085_r1_nadie_mas_decide_es_ci` gana `'!= "CIZ"'`
y `"!= 'CIZ'"`.
- RED, con la lista ampliada y el código sin cambiar
  (`python -m pytest tests/test_f085_conversion.py -q -k nadie_mas`):
  `E  AssertionError: ('infrastructure/database/parte_repository.py', '!= "CIZ"')` /
  `E  '!= "CIZ"' is contained here: d and cod != "CIZ":` /
  `1 failed, 3 passed, 85 deselected`.
- Verde: los `test_f085_*` de sv4 dan `107 passed` (los `r28_*`, `6 passed`).
- Grep en sv4 fuera de `clase_hora.py`: no queda ninguna comparación de F-085. Hay dos anteriores
  de otras features que **no he tocado**: `sincronizacion.py:290` (F-052, incluye CIZ a propósito)
  e `incidencias_horas.py:32/77` (F-025, valida el YAML). Los `"CI"` de partidas son el capítulo de
  costes indirectos, no códigos de hora.

**Cambio 2 (R8, R13; D16 = (b), humano 2026-11-27).**
- `static/app.js`, `onChange`: cada PATCH de la selección se resuelve por separado. Con selección
  y fallo parcial, un `alert` (el mecanismo de F-004 R13 para «el sistema dice que no») dice
  «N de M línea(s) no se han guardado:», con una línea por texto de error del servidor y los ids
  de las líneas («(líneas 6, 7)»). El `alert` bloquea, así que la recarga espera a que se lea.
  Si alguna se guardó, sigue la ruta de la selección sin fallos, que recarga (decisión: la
  selección ya recargaba siempre al guardar; así también se pintan las que solo cambiaron de
  código). Si fallan todas, avisa, marca el error y no recarga. Una sola línea, como hoy. El
  ayudante `avisoNoGuardadas` es local a `onChange`, porque F-047 R23 vigila las funciones con
  nombre de `app.js`.
- Tests (`test_f085_conversion.py`): el arnés node ya admite errores (`_error`, `_status`) y `alert`.
  - `r13_d16_fallo_parcial_avisa_y_recarga`, `r13_d16_motivos_distintos_por_separado`,
    `r13_d16_todas_fallan_avisa_y_no_recarga` y `r13_d16_una_sola_que_falla_como_hoy`.
  - `r8_mismo_parte_con_cola_de_una_en_una` sustituye a la caracterización. Afirma R8 enmendado
    con pedidos secuenciales: la primera se convierte; cada una de las demás da el 409 de F-043
    con `MOTIVO_RECALCULANDO`, sin tocar ni la línea ni el deshacer, y hay un solo recálculo. No
    afirma nada de la concurrencia.
  - `r8_partes_distintos_del_mismo_dia_con_cola`: todas convertidas, dos `registro_clase` y dos
    recálculos.
- RED con `app.js` sin tocar (`python -m pytest tests/test_f085_conversion.py -q -k r13`):
  `E  ValueError: not enough values to unpack (expected 1, got 0)` ×3 (no había `alert`) /
  `3 failed, 4 passed, 86 deselected`. Los dos tests nuevos de servidor pasan contra el código
  tal cual: D16 acepta ese comportamiento, así que no hay RED de servidor que enseñar.
- Verde: los ficheros de F-085, F-043 y F-047 de sv4 dan `194 passed`. `tests/test_f085_documentacion.py`
  da `4 passed`; vigila además «D16» y `avisoNoGuardadas` en la semántica 3.
- Docs: `ARCHITECTURE.md` semántica 3 (D16) y `current.md` (D16 y el paso de M1). Los demás no
  describen la selección.
- `init.sh` del ciclo:
  - 1.ª pasada, exit 1. Falló el flaky `test_f059_r9` (`assert not True ... _vivo(50844)`).
    Falló también `test_f047_r23_ninguna_funcion_nueva_y_una_sola_variable`, por la función con
    nombre nueva: corregido haciéndola local, sin tocar F-047. Y salió la cobertura al 77,3 %,
    porque sv4 se cortó en el primer fallo.
  - 2.ª pasada, **exit 0**: raíz `2553 passed, 50 skipped`; sv4 `4259 passed, 1 skipped`; el
    resto en caché verde; `PUERTA COBERTURA` 220/220; `CAPA E2E: N/A`; ruff 1219, la deuda previa.

## Campaña de mutación (T9, T14)

Campaña del líder: 172 mutantes, muestra 100: 91 muertos, **9 supervivientes**. Sin tocar
producción (RM1). El RED de cada test es el mutante aplicado a mano en el árbol y restaurado
byte a byte.

| # | Mutante | Decisión | Test o demostración, y resultado real |
|---|---|---|---|
| 1 | `conversion_clase.py:78` `clase is not None` → `clase` | equivalente | `clase` es None o `ClaseIncidencia`, sin `__bool__`/`__len__`, de un solo `por_sigrid.get`: 84 casos iguales |
| 2 | `conversion_clase.py:89` `error is not None` → `error` | equivalente | `error_de_codigo` devuelve None, `MOTIVO_CIZ_NO_SE_ELIGE` o `motivo_sin_letra(...)`, ninguna vacía: 6048 casos iguales |
| 3 | `parte_repository.py:748` `frozen=True` → `False` | **muerto** | `test_f085_resultado_hora_inmutable` (diseño): `Failed: DID NOT RAISE FrozenInstanceError` |
| 4 | `parte_repository.py:2644` `mover_inicio = False` → `True` | **muerto** | `test_f085_r29_roles_de_racha_apagado_por_defecto`: `assert set() == {2}` |
| 5 | `parte_repository.py:3388` `clase.error is not None` → `clase.error` | equivalente | `clase` sale de `decidir_clase`; su `error` es el de #2: 252 casos en SQLite (salida, filas y deshacer) iguales |
| 6 | `parte_repository.py:3410` `elif clase.es_incidencia` → `elif not …` | **muerto** | `test_f085_deshacer_describe_la_clase_nueva`: «Cambiar a horas · …».startswith(«Cambiar a incidencia · ») False (2 failed, 1 passed) |
| 7 | `racha_ciz.py:106` `frozen=True` → `False` | **muerto** | `test_f085_decision_inicio_inmutable` (diseño): `Failed: DID NOT RAISE FrozenInstanceError` |
| 8 | `racha_ciz.py:327` `parte is not None` → `parte` | equivalente | `parte` es None o `ParteSigrid`, sin `__bool__`/`__len__`; el pipeline construye `partes` con `ParteSigrid`: 4000 casos iguales |
| 9 | `racha_ciz.py:324` `previo is None` → `not previo` | equivalente | `inicio_previo` devuelve `None` o `primera`, una `LineaSigrid` sin `__bool__`/`__len__`: 4000 casos iguales |

- Los tests de diseño (3 y 7) y el del texto del deshacer (6) no llevan `rN`, porque no afirman un
  requisito (regla del reviewer de F-084). El 4 sí lo lleva: afirma R29, el apagado por defecto.
- `python progress/equivalentes_F-085.py` (`.venv`) ⇒ «5/5 equivalentes demostrados», **exit 0**:
  localización y dominio por AST; original y mutado en memoria (sv5, en un subproceso); un control
  negativo por superviviente (`is None` invertido) que aborta con exit 1 si no distingue; el banco de
  sv5 exige ≥50 `mover` y ≥50 `parte_cerrado`. Análisis tras el `--incremental`; T9/T14 sin marcar.
- `init.sh` de este paso: PENDIENTE_INIT_MUT
