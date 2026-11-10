<!-- progress/impl_F-066.md -->
# F-066 · Informe del implementer

sv4 decide la hora extra por el prefijo `HE` y excluye `HENC`. Rama
`feature/F-066-selector-hora-por-prefijo-he`, worktree `partes-wt-f066`. Rigor **crítico**.
Solo sv4: no se tocaron sv3, sv5, `congelacion.py`, `orm_models.py`, los gemelos de
`CLAUDE.md`, `tipo_hora_matcher.py`, las plantillas ni `infra/`.

## Commits (uno por tarea)

| Tarea | Commit | Qué |
|---|---|---|
| T1 | 76ac588 | `clase_hora.py` (RED+GREEN) y reimport en `sincronizacion.py`; F-066 a `in_progress` |
| T2 | ec49161 | tests RED de R8 y R12–R18 |
| T3 | 4d3df09 | `set_registro_hora` (repositorio) y `PATCH …/hora` por `tipo_hora_de_codigo` |
| T4 | 6e0dfc5 | tests RED de R7, R9–R11 y R23 |
| T5 | 3aa5c8f | `fetch_tipos_hora` sin excluidos, `extra` en `tipos-hora`, `buildOptions` por `t.extra` |
| T6 | 5e9d01e | tests RED de R6 y R19–R21 |
| T7 | 4922706 | `fetch_hora_extra_recurso`, `fetch_dnis_sin_extra`, `extras_pendientes` |
| T8 | 00bf0d9 | `docs/ARCHITECTURE.md` semántica 3 (y la referencia de F-052) y docstrings |

Todos los ficheros normalizados a LF antes de `git add`, rutas explícitas, sin push.

## Qué cambió (ficheros y líneas de producción, para la mutación de T9)

Base de comparación: `b1a468b` (spec aprobada). `git diff b1a468b -- services/partes-front`
excluyendo `tests/`:

- `application/services/clase_hora.py` — **nuevo**, 78 líneas: `PREFIJO_EXTRA`,
  `CODIGOS_EXCLUIDOS`, `_COLUMNA`, `_normaliza`, `es_excluido`, `es_hora_extra`,
  `tipo_hora_de_codigo`, `condicion_sql_extra`.
- `application/services/sincronizacion.py` — import de `es_hora_extra` (+27–30), comentario
  de `hora_ext` (~108), borrado del cuerpo antiguo (antes 158–167), docstring de `comparar`.
- `application/services/franquicia.py` — import (+37), docstring (16–18, 238–239) y la
  condición de `extras_pendientes` (~247): `es_hora_extra(a.get("hora_codigo")) is True`.
- `application/services/tipo_hora_catalog.py` — solo docstring (+7–11).
- `infrastructure/database/parte_repository.py` — import (+51) y `set_registro_hora`
  (~3213–3219): `tipo = tipo_hora_de_codigo(hora_codigo)`; `if tipo is not None and not
  reg.es_incidencia: reg.tipo_hora = tipo`.
- `infrastructure/sigrid/sigrid_lookup_client.py` — import (+28–29); `fetch_tipos_hora`
  (~238, 244–248, 261–262: omite `es_excluido`, cuenta y registra los omitidos);
  `fetch_dnis_sin_extra` (~437–466: `es_he` con `condicion_sql_extra` en las dos ramas);
  `fetch_hora_extra_recurso` (~506–513: `WHERE {condicion_sql_extra('auxhor.cod')}`).
- `interface_adapters/web/app.py` — import (+77–80); `tipos-hora` añade `"extra":
  es_hora_extra(t.codigo) is True` (~1809–1811); `PATCH …/hora` responde
  `tipo_hora_de_codigo(option.codigo) or "normal"` (~3883–3884).
- `static/app.js` — `buildOptions` (467–471): agrupa por `t.extra === true` (JS, fuera del
  alcance de la mutación Python).

Docs: `docs/ARCHITECTURE.md` (semántica 3 y la frase de F-052). Progreso:
`progress/current.md`, `specs/…/tasks.md` (T1–T8 `[x]`), `harness/features.json`
(`in_progress`), `BACKLOG.md` (regenerado por `init.sh`).

## Decisiones de diseño (las de `design.md` §8, sin cambios)

- **DA1**: la lista y la regla solo en `clase_hora.py`; el SQL se genera de las constantes
  (`condicion_sql_extra` valida la columna con `fullmatch` de una regex de identificador
  `a` o `a.b`; `ValueError` si no). `sigrid_lookup_client.py` importa por primera vez de
  `application.services` (previsto en design §5).
- **DA2 A**: el repositorio fija `tipo_hora` por `hora_codigo`; firma intacta.
- **DA3 A**: sin código (None, vacío, espacios) no se toca `tipo_hora`; el resto sí se guarda.
- **DA4 A**: el servidor manda `extra`; el JS no tiene regla.
- **DA5 A**: los seis disyuntivos `tipo_hora == "extra" or hora_ext == 1` intactos (R23 lo vigila).
- **DA11 A / DA12 A**: los excluidos se quitan en `fetch_tipos_hora`, así que el
  `PATCH` con `hora_ide` 63 da 400 «no existe» sin código nuevo.
- Detalle de normalización: `extras_pendientes` antes comparaba `upper()` sin `strip()`;
  ahora usa `es_hora_extra`, que también recorta espacios (R2). Un `" HE01"` ahora suma.

## Desviaciones respecto a `tasks.md` (justificadas)

1. **R6 se prueba en `test_f066_usos_sv4.py`, no en `test_f066_clase_hora.py`.** El test
   de fuente no puede estar verde en T1: `franquicia.py` y `sigrid_lookup_client.py` todavía
   llevaban `startswith("HE")` / `LIKE 'HE%'` hasta T7. Lo moví a T6 (RED) y cierra en T7,
   para que cada commit deje su verificación en verde.
2. **R8 pasa a verde en T5, no en T3.** El 400 por `HENC` sale de R7/DA11 (catálogo sin
   excluidos), que es T5. En T3, `test_f066_set_registro_hora.py` dio 1 fallo (R8) y 171
   en verde; tras T5, el fichero entero en verde.
3. **Dos defectos de mis tests de T4, corregidos en el commit de T5**: (a) el código vacío
   `""` lo convierte `_opt_str` en `None`, así que la clave esperada en R9 es `None`; (b) el
   test de R11 buscaba `".ext"`, que casa con `.extra`; ahora es `\.ext\b`. Comprobé que
   con el `app.js` antiguo (`t.ext !== 1`) el regex nuevo sí falla.

Ninguna ambigüedad ni error de la spec que bloquee: no hizo falta parar.

## Fase RED (trazas reales)

**T1** — `cd services/partes-front && python -m pytest tests/test_f066_clase_hora.py -q`:

```
tests\test_f066_clase_hora.py:21: in <module>
    from application.services import clase_hora
E   ImportError: cannot import name 'clase_hora' from 'application.services' (unknown location)
=========================== short test summary info ===========================
ERROR tests/test_f066_clase_hora.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 1.10s
```

**T2** — `python -m pytest tests/test_f066_set_registro_hora.py -q -rf` (antes de T3):

```
E       AssertionError: assert 'normal' == 'extra'        (r12, HEOF con ext 0)
E       AssertionError: assert 'extra' == 'normal'        (r13, HL09 con ext 1)
E       AssertionError: assert ('normal', 'normal') == ('normal', 'extra')   (r15)
E       AssertionError: assert ('HEOF', 0, 'normal') == ('HEOF', 0, 'extra') (r17)
E       AssertionError: assert ['normal', 'normal', 'normal'] == ['extra', 'extra', 'normal'] (r18)
FAILED …::test_f066_r12_he_ext_0_extra[HEOF] / [ hecap ] / [HEGR]
FAILED …::test_f066_r13_sin_prefijo_ext_1_normal[HL01] / [HL09] / [HENC] / [MENC]
FAILED …::test_f066_r15_sin_codigo_no_toca_tipo[0-None] … [1-   ]   (6 casos)
FAILED …::test_f066_r16_campos_y_deshacer
FAILED …::test_f066_r17_respuesta[7-HEOF-0-extra] / [8-HECAP-0-extra] / [9-HL09-1-normal]
FAILED …::test_f066_r17_respuesta_sin_codigo_es_normal
FAILED …::test_f066_r8_patch_excluido_400
FAILED …::test_f066_r18_varias_lineas
20 failed, 13 passed, 1 warning in 31.77s
```

**T4** — `python -m pytest tests/test_f066_selector_js.py -q -rf` (antes de T5):

```
E       AssertionError: assert ['CI01', 'HEN...HL01', 'henc'] == ['CI01', 'HEOF', 'HL01']
E       AssertionError: assert TipoHoraOption(ide=63, codigo='HENC', ...) is None
E           AssertionError: assert (HoraMatch(ide=63, codigo='HENC', descripcion='HORA ENCARGADO', ext=0, ..., method='categoria_normal') is None or 'HENC' != 'HENC')
E       KeyError: 'extra'
E         At index 0 diff: {... 'Horas ordinarias', 'opciones': [['option', '1', 'HL01 · Ordinaria', False], ['option', '7', 'HEOF · Extra oficial', False], ['option', '8', 'HECAP · Extra capataz', True]]} != {...}
E       AssertionError: assert '.ext' not in '\n  functio...tra);\n  }\n'
FAILED …::test_f066_r7_catalogo_sin_excluidos
FAILED …::test_f066_r7_catalogo_por_ide_no_ve_excluidos
FAILED …::test_f066_r7_matcher_encargado_no_elige_henc
FAILED …::test_f066_r9_tipos_hora_lleva_extra
FAILED …::test_f066_r10_grupos_por_extra / r10_solo_true_es_extra / r10_grupo_vacio_no_sale
FAILED …::test_f066_r11_js_sin_regla
8 failed, 7 passed, 1 warning in 19.26s
```

(El matcher de «+ Nuevo» elegía de verdad `HENC` para un «Encargado»: el defecto de DA11.)

**T6** — `python -m pytest tests/test_f066_usos_sv4.py -q -rf` (antes de T7):

```
E         {'cod': 'HENC'} != {'cod': 'HEOF'}            (r19: TOP 1 por código elegía HENC)
E       assert "WHERE UPPER(LTRIM(RTRIM(auxhor.cod))) LIKE 'HE%' AND ... NOT IN ('HENC') AND reshor.reside = ?" in "SELECT TOP 1 ... WHERE auxhor.cod LIKE 'HE%' AND reshor.reside = ? ORDER BY auxhor.cod"
E         Extra items in the right set: '44444444D' '11111111A'   (r20: solo HENC contaba como extra)
E       assert 0 == 2                                    (r20: fragmento en las dos ramas)
E       AssertionError: assert 5.0 == 3.0                (r21: HENC 2 h + HEOF 3 h)
E       AssertionError: assert 1.0 == 0.0 / assert 0.5 == 2.0
E         Left contains 2 more items, first extra item: ('application\\services\\franquicia.py', 'startswith...')   (r6)
8 failed, 2 passed in 2.31s
```

R19/R20 ejecutan el SQL capturado sobre un SQLite en memoria (`TOP 1` → `LIMIT 1`,
`ISNULL` → `IFNULL`), así que prueban el resultado y no solo el texto.

## Verificación por tarea (GREEN, resultado real)

- T1: `pytest tests/test_f066_clase_hora.py tests/test_f052_clasificar.py -q` → 156 passed.
- T3: `pytest test_f066_set_registro_hora test_f048_traza_portal test_f043_guarda_espera
  test_f004_endpoints_congelados -q` → 171 passed, 1 failed (R8, cierra en T5; desviación 2).
- T5: `pytest test_f066_selector_js test_f023_catalogo_empresa test_f066_set_registro_hora -q`
  → 77 passed (tras corregir los dos tests); `node --check static/app.js` → OK.
- T7: `pytest test_f066_usos_sv4 test_f056_franquicia test_f066_clase_hora -q` → 147 passed;
  `pytest test_f049_guardar_celda test_f023_catalogo_empresa -q` → 126 passed.
- Grep final de sv4 (Python, sin tests): `LIKE 'HE`, `startswith("HE` y `HENC` solo en
  `clase_hora.py` (y una mención en un docstring de `franquicia.py`, que no es literal entre
  comillas).

## Fuera de alcance / pendiente

- **T9** mutación completa: la lanza el líder (`python -m harness.mutacion --feature F-066`);
  líneas en «Qué cambió». No la he lanzado.
- **T10 / M2** (humano, tras desplegar sv4): obra 0404, sin `HENC` en el desplegable, `HEOF` en
  «Horas extra» ⇒ badge extra al recargar; deshacer ⇒ vuelve.
- sv3 y sv5 (`HENC` y regla), guardián de gemelos y entrada en `CLAUDE.md`: **F-067**.
- Las 7 líneas `HENC` del portal, la línea de 2022 en Sigrid y la baja de `HENC`: fuera.
- `azure-apps/partes.md`: **sin cambios**. `/api/sigrid/tipos-hora` es interno del portal
  (el campo `extra` es aditivo) y sv4 sigue consumiendo lo mismo de sigrid-api (solo cambia
  el texto del `WHERE` de dos lecturas).

## Evidencias

`bash harness/init.sh` final (2026-11-06, sobre 00bf0d9): **ENTORNO LISTO**, en verde.

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | raíz 544 passed, 3 skipped (338 s); **sv4 3737 passed, 1 skipped** (3264 s); sv1, sv2, sv3 y sv5 en verde por caché (árbol sin cambios) |
| Tests nuevos de F-066 | 4 ficheros: `test_f066_clase_hora`, `test_f066_set_registro_hora` (33), `test_f066_selector_js` (15, 3 en node), `test_f066_usos_sv4` (10) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 99.9% de 784 líneas cambiadas cubiertas (783/784, umbral 80%, nivel critico)`. `init.sh` no dice cuál es la línea sin cubrir; no la he buscado |
| Mutantes | Campaña del líder (T9): **21 generados, 18 muertos, 3 supervivientes, 0 timeouts** (10220,6 s), `progress/mutacion_F-066.md`. Los 3 supervivientes, matados a mano por un test nuevo (sección siguiente); campaña no relanzada |
| Tiempo de la suite | sv4: 54 min 24 s; raíz: 5 min 38 s |
| Tamaño | `PUERTA TAMAÑO`: requirements 116/150, design 154/250, impl 181/220 (antes de esta sección) |
| JS | `node --check static/app.js` OK; `buildOptions` ejecutado en node (R10) |

Avisos de `init.sh` que no vienen de F-066: ruff 981 (deuda previa), F-032 `blocked`, infra
sin tests y BACKLOG.md regenerado (incluido en el commit del informe).

## Supervivientes de la mutación

Los 3 están en `fetch_tipos_hora` (`sigrid_lookup_client.py`) y tocan solo `omitidos`, que
alimenta el log `tipos_hora -> N filas (M excluidas)`. **Hueco real, no equivalentes**: el log es
la traza operativa de cuántos códigos quita el catálogo y ningún test lo leía. Test nuevo
`test_f066_r7_log_cuenta_excluidas` (`test_f066_selector_js.py`, `caplog`, con 0, 1 y 2
excluidas). Cada mutante, aplicado a mano sobre el fichero y restaurado después (`git status`
limpio; con el original, `3 passed`), con `python -m pytest tests/test_f066_selector_js.py -q -k log_cuenta -rf`:

```
=== l.238 'omitidos = 0' -> 'omitidos = 1' ===
E  assert ['[sigrid-loo...1 excluidas)'] == ['[sigrid-loo...0 excluidas)']
E  assert ['[sigrid-loo...2 excluidas)'] == ['[sigrid-loo...1 excluidas)']
E  assert ['[sigrid-loo...3 excluidas)'] == ['[sigrid-loo...2 excluidas)']
3 failed, 15 deselected
=== l.247 'omitidos += 1' -> 'omitidos -= 1' ===   (sale "-1" y "-2 excluidas")
FAILED …::test_f066_r7_log_cuenta_excluidas[ides1-4-1]
FAILED …::test_f066_r7_log_cuenta_excluidas[ides2-3-2]
2 failed, 1 passed, 15 deselected
=== l.247 'omitidos += 1' -> 'omitidos += 2' ===
E  assert ['[sigrid-loo...2 excluidas)'] == ['[sigrid-loo...1 excluidas)']
E  assert ['[sigrid-loo...4 excluidas)'] == ['[sigrid-loo...2 excluidas)']
2 failed, 1 passed, 15 deselected
```
