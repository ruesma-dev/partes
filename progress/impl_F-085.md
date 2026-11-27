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
4. **Riesgo**: con la cola configurada, cambiar varias líneas del MISMO parte da 409 en las
   siguientes, porque la primera deja el parte en espera (F-043). Un test lo caracteriza.
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

## Suites por servicio (antes de `init.sh`)

- sv4: `1 failed, 4253 passed, 1 skipped in 1003.55s`. El fallo era el recuento de recargas de
  F-043, enmendado en T12. Después: `165 passed` en `test_f043_portal_fecha`, `test_f085_conversion`
  y `test_f085_inicio_movido_sv4`.
- sv3: `2988 passed` más los 23 de F-085 (tras enmendar f037 r9).
- sv5: `1988 passed, 1 skipped in 26.40s`.
- raíz: `tests/test_f085_documentacion.py` `4 passed`.

## Salida de `init.sh`

`bash harness/init.sh` ⇒ **exit 0** (segunda pasada). La primera dio exit 1 solo por el flaky
conocido `tests/test_f059_ejecucion.py::test_f059_r9_timeout_mata_el_arbol_y_no_es_rojo`
(`FileNotFoundError ... nieto.pid`, con la máquina cargada: `1 failed, 1571 passed`). Lo
reintenté 1 vez de las 3 permitidas y pasó, sin cambiar nada.
- Raíz: `2553 passed, 50 skipped in 1979.86s`, con medición de cobertura.
- Servicios (verde de la pasada 1, en caché en la 2): sv1 `74 passed`, sv2 `579 passed`,
  sv3 `2989 passed`, sv4 `4254 passed`, sv5 `1988 passed`.
- `PUERTA COBERTURA: 100.0% de 219 líneas cambiadas cubiertas (219/219, umbral 90% (del nivel
  critico) ...; diff desde b5e935b52a, merge-base con dev)`.
- `PUERTA TAMAÑO: F-085 dentro de los topes (requirements 144/150, design 248/250, impl 150/220)`.
- `PUERTA CARRIL: N/A (F-085 es de nivel critico: no declara límites)`.
- `CAPA E2E: N/A (ningún servicio declara el bloque e2e)`.

## Verificaciones MANUAL pendientes (humano)

En `progress/current.md`, con el comando y el resultado esperado de cada una:
- M1 (parte A, local, modo pruebas);
- M2 y M3 (parte B, local, modo pruebas, M3 opcional);
- M5 (producción, solo lectura, tras encender B).

M4 (la reparación del 0678, D15) queda **fuera**: ningún agente escribe en producción ni en
Sigrid. Encendido de B: sv5 y luego sv4, con `MOVER_CIZ` encendido.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | 12 437 en verde: raíz 2553 (50 skipped), sv1 74, sv2 579, sv3 2989, sv4 4254, sv5 1988; 0 fallos en la pasada final |
| Cobertura de líneas cambiadas | 100,0 % (219/219, umbral 90 % de `critico`), según la línea `PUERTA COBERTURA` |
| Mutantes generados / supervivientes | Sin medir: la campaña (T9, T14) la lanza el líder en la pasada de campaña, tras el APPROVED |
| Tiempo de la suite | raíz 1979,86 s; sv4 1290,18 s; sv3 65,63 s; sv2 50,22 s; sv5 36,43 s; sv1 19,76 s (las suites de los servicios, de la pasada 1) |
| Capa e2e | `CAPA E2E: N/A (ningún servicio declara el bloque e2e)` |

## Pendiente

- Pasada de campaña de mutación (T9, T14): líder.
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
- Verde: `test_f085_conversion.py` y `test_f085_inicio_movido_sv4.py` dan `107 passed`, y los
  `r28_*` dan `6 passed`. Según lo pedido, `init.sh` no se ha ejecutado: va al terminar el Cambio 2.
- Repaso con grep en sv4 (`"CIZ"`, `'CI'`, `startswith("CI`, `LIKE 'CI`) fuera de `clase_hora.py`.
  No queda ninguna comparación de F-085. Hay dos anteriores a F-085 que **no he tocado**, porque son
  de otras features y cambiarlas sería tocar otra feature sin spec:
  - `application/services/sincronizacion.py:290`, `.startswith("CI")` (F-052 `a5bcef1`): el
    `a_cero` de una línea solo de Sigrid. Incluye CIZ a propósito.
  - `application/services/incidencias_horas.py:32/77`, `PREFIJO_SIGRID = "CI"` (F-025 `d4cda31`):
    valida `config/incidencias.yaml` al cargarlo.
  
  Los usos de `"CI"` de `partida_catalog.py`, `partida_matcher.py`, `app.py:4389` y `app.js`
  son el capítulo de costes indirectos de las partidas, no códigos de hora.

**Cambio 2 (R8, desviación 4)**: pendiente de la decisión del humano. No lo he tocado.
