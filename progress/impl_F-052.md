# F-052 · Informe del implementer (tanda T9–T17)

Rama `feature/F-052-sincronizar-con-sigrid`, worktree `partes-wt-f052`. Rigor **crítico**.
**T1–T8** (lectura y comparación, M2) y **H-M2-1**: informe completo en
`git show 50c5d01:progress/impl_F-052.md` (RED de T2–T7, ID1–ID7, M2 superada en
`progress/m2_F-052.md`). Esta tanda (autorizada por el humano tras M2, «si, dale») hace las
**acciones**: escriben SOLO en la base `partes`, nunca en Sigrid (R26). La mutación la lanza el
líder. La feature NO se marca `done` (falta el reviewer).

## Qué cambió

| Tarea | Commit | Qué |
|---|---|---|
| T9 | 4115eec | `parte_repository.py`: `aplicar_marcar_registrada`, `aplicar_traer_de_sigrid`, `documentos_de_los_dias`, `_bloquear_para_sincronizar` (SELECT FOR UPDATE + CAS), `_motivo_sincronizar` |
| T10 | 64188c0 | `sincronizar_ambito.aplicar` (re-sync, firma, acciones), `POST /api/sincronizar/aplicar`, `SINCRONIZAR_MAX_ITEMS_ACCION` (500), `MOTIVO_SINCRONIZAR`, `CAMPOS_TRAER` (DA3) |
| T11 | 5014086 | Botón «Sincronizar con Sigrid» y contenedor del panel en `obra_detail.html` y `trabajador_detail.html` |
| T12 | a587762 | Panel en `static/app.js` (filtros, acciones, confirmación, resultado) y `styles.css` |
| T13 | c23a63c | `tests/test_f052_contrato_motivos.py` (raíz): sv3 clasifica `sincronizar` como recálculo |
| T14 | — | Suite completa de sv4 (abajo) |
| T15 | e0bc4d3 | `docs/ARCHITECTURE.md`: doble canal, semántica 10, semántica 22 nueva |
| doc | azure-apps 1289301 | `partes.md`: nota F-052, rutas de sv4 (§3.4), `SINCRONIZAR_MAX_ITEMS_ACCION`. Sin push |
| T16/T17 | (último commit) | M3/M4 en `current.md`; `bash harness/init.sh`; este informe |

Ficheros: los de la tabla, más los tests `test_f052_*` de sv4 (`vistas` y `panel_js` nuevos),
`test_f017_punto_unico.py` y `test_f047_portal_parte_nuevo.py` (ID13). **Sin tocar** (`git diff dev` vacío): `congelacion.py`, `recurso_conciliador.py`
(`esta_congelado`), `orm_models.py`, los gemelos, sv1–sv3 y sv5. H-M2-1b (selector de hora,
`option.ext`) **no se toca**.

## Cómo funciona `aplicar` (R17–R25)

`POST /api/sincronizar/aplicar` `{accion, ambito, items}`: 503 sin sv5; 422 de `validar_peticion` y de F-022
(salvo `restaurar`, ID8), sin llamar a sv5. Bajo el candado de R29 vuelve a sincronizar: id fuera del
re-sync ⇒ 422 entero; firma distinta o acción ajena a la clase ⇒ descartado. Escribe con CAS
(`marcar_registrada`, `traer_de_sigrid`) o por las rutas de siempre (`borrar_linea`, `restore_registro`);
`reaprobar` solo abre el modal de aprobar. `traer` pide un recálculo compartido (F-049, `sincronizar`).
Traza R22 en `sigrid_motivo` y log INFO `[sincronizar][aplicar]`. Detalle: design §2, §4 y §6.

## Decisiones de implementación (ID8–ID14, para el reviewer)

- **ID8 · `restaurar` sin `_validar_ambito` de F-022** e **ID10 · `aplicar` no depende de
  `SINCRONIZAR_SECO`** (el seco solo gobierna la escritura implícita de R10, también en el re-sync):
  razonamiento y tests en `design.md` §4 (ID8) y §8 (ID10), los dos **pendientes de ratificar por el
  humano** (review 1). Decisión de despliegue pendiente: `SINCRONIZAR_SECO` en Azure (M4).
- **ID11 · `_releer_portal` fuera de seco**: tras las escrituras de R10, el ítem lleva el
  estado nuevo; sin releer, la firma que veía el usuario no cuadraba con la del re-sync y toda
  acción salía «cambió desde que lo viste». Corregido y con test.
- **ID12 · DA3 = A**: `traer` solo copia `horas` (`CAMPOS_TRAER`); una `distinta` sin diferencia
  de horas ya no ofrece `traer` (`acciones_de` ⇒ `()`).
- **ID13 · guardián F-017**: `test_f017_punto_unico.py` cuenta los usos de `_actor(`; pasa de 20
  a 21 por la ruta nueva (R22 exige el actor). Justificado en el propio test. Igual con el de
  F-047 (`test_f047_portal_parte_nuevo.py`, funciones con nombre de `app.js` == 302): lo rompió
  T12 (la suite de T14 paró ahí: `1 failed, 2314 passed`); ahora lista las 17 del panel
  (`F052_PANEL`) y exige 302 fuera de ellas, así sigue cazando cualquier otra función nueva.
- **ID14 · `a_papelera`/`restaurar` sin traza en `sigrid_motivo`**: reutilizan
  `borrar_linea`/`restore_registro` tal cual (R24: sin camino nuevo). El actor queda en
  `deleted_by` y en el log. `marcar_registrada` no aplica las guardas de R21 (lo dice la spec:
  solo consolida un estado que Sigrid ya tiene).

## Fase RED (trazas reales)

Python `C:/Users/pgris/PycharmProjects/partes/.venv/Scripts/python.exe -m pytest … -q
--tb=line`, desde `services/partes-front` (T13 desde la raíz). Líneas `E` contadas con
`sort | uniq -c`; las trazas completas quedaron en el scratchpad de la sesión.

**T9 (R19–R21)** — `pytest tests/test_f052_repositorio.py`:
```
      8 E   AttributeError: 'ParteReviewRepository' object has no attribute 'aplicar_marcar_registrada'
     16 E   AttributeError: 'ParteReviewRepository' object has no attribute 'aplicar_traer_de_sigrid'
      1 E   AttributeError: 'ParteReviewRepository' object has no attribute 'documentos_de_los_dias'
25 failed, 10 passed in 4.67s
```
Verde: `35 passed`. **T10a (R17, R18, R23–R25, ID11)** — `pytest tests/test_f052_sincronizar_ambito.py`:
```
     31 E   AttributeError: 'SincronizadorAmbito' object has no attribute 'aplicar'
      1 E   assert False
      1 E   AssertionError: assert 'registrado' == 'borrado_sigrid'
33 failed, 52 passed, 1 warning in 10.78s
```
**DA3** — `pytest tests/test_f052_clasificar.py -k da3`: `NameError: CAMPOS_TRAER` (2) y
`AssertionError: assert ('traer_de_sigrid',) == ()` (3) ⇒ `5 failed`.

**T10b (ruta, R18, R30)** — `pytest tests/test_f052_endpoints.py`:
```
      5 E   assert (404 == 422)
      3 E   AssertionError: {"detail":"Not Found"}
      1 E   assert 404 == 503
      1 E   assert 404 == 422
      1 E   assert 404 == 200
      1 E   AttributeError: 'Settings' object has no attribute 'sincronizar_max_items_accion'
12 failed, 18 passed, 1 warning in 12.00s
```
**T11 (R7, R15, R30)** — `pytest tests/test_f052_vistas.py`:
```
      5 E   assert (None is not None)
5 failed, 6 passed, 1 warning in 9.99s
```
**T12 (panel)** — `pytest tests/test_f052_panel_js.py` (con el `app.js`/`styles.css` de antes:
el código se escribió primero y el RED se reprodujo restaurando la versión previa; `cmp`
confirmó después la vuelta exacta a la nueva):
```
     14 E   AssertionError: app.js no define etiquetasClaseSync
      1 E   assert 'if (clicSync(ev)) return;' in '// static/app.js — portal de partes (sv4)...'
      1 E   AssertionError: assert '.sincronizar-panel' in '/* static/styles.css — ...'
16 failed, 1 passed in 0.46s
```
**T13 (R23)** — `pytest tests/test_f052_contrato_motivos.py` (raíz, copia aislada con el
publisher de 50c5d01):
```
      3 E   AttributeError: module 'f052_contrato_sv4_recalculo_publisher' has no attribute 'MOTIVO_SINCRONIZAR'
3 failed in 0.05s
```
Verde: `test_f052_*` de sv4 215 + 115 + 11 + 17 passed; JS y vistas relacionadas 520 passed;
guardianes de raíz de T13 62 passed.

## Verificación (resultado real)

- T14, suite de sv4 (`pytest -q -p no:cacheprovider -x`): `1 failed, 2314 passed, 1 skipped`
  (462 s), el guardián de F-047 (ID13); corregido, `24 passed`, y la suite entera, en init.sh.
- T17, `bash harness/init.sh` (f402baf + informe): **ENTORNO LISTO**; sv4 3580 passed (1080 s), raíz 540.
- `git diff dev --stat` de `congelacion.py`, `orm_models.py`, `services/partes-persistencia` y
  `services/partes-transfer`: vacío.
- `git ls-files --eol` de los ficheros tocados: `i/lf` en todos.

## M3 y M4 · PENDIENTES del humano

**M3** (local, modo pruebas, obra 0404): comandos exactos en `progress/m3_F-052.md` (movido tal cual
desde este informe para respetar el tope de 220 líneas).

**M4 · PENDIENTE del humano (tras desplegar sv5 → sv4).** Decidir antes `SINCRONIZAR_SECO` en Azure (ID10). Un usuario real sincroniza y aplica una
acción; en la base `partes`, solo lectura: `SELECT id, horas, sigrid_estado, sigrid_motivo,
sigrid_registrado_by FROM parte_registros WHERE sigrid_motivo LIKE 'Sincronizado con Sigrid:%'
ORDER BY id DESC LIMIT 10;` ⇒ actor de Easy Auth (ni `local:` ni `sin-identidad`).

## Fuera de alcance y pendiente

- H-M2-1b (`option.ext` en el selector de hora): fuera; se propone como feature aparte.
- Mutación: lanzada por el líder (6b58e16); supervivientes tratados abajo, sin relanzar la
  campaña (regla del humano). Pendiente: aceptar los 4 equivalentes, M3, M4, reviewer.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests F-052 (T9–T13) | sv4 `test_f052_*` 215 + 115 + 11 + 17 passed; raíz T13 3 passed (guardianes 62) |
| Suites completas (init.sh) | sv4 3580 passed, 1 skipped; raíz 540 passed, 3 skipped; sv1, sv2, sv3, sv5 en verde (caché: sin cambios) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 99.7% de 742 líneas cambiadas cubiertas (740/742, umbral 80%, nivel critico)` |
| Mutantes | 331 generados, 289 muertos, 42 supervivientes (SHA `3424919`, **4 workers**, 31712 s); tras esta tanda: 38 matados por tests nuevos (comprobado en copia aislada) y 4 equivalentes pendientes de aceptar |
| Tiempo de la suite | sv4 942–1080 s (con cobertura); raíz 91–157 s |

## Supervivientes de la mutación

Análisis de cada uno en `progress/mutacion_F-052.md` (ninguno en `PENDIENTE`); campaña no relanzada.
Cada test nuevo se comprobó en una **copia aislada** de sv4 y sv5 (scratchpad) con el mutante en su
línea exacta, `pytest <fichero> -k <test>`: **38 de 38 fallan** (`rc=1`, «N failed»); el árbol real
no se mutó. Solo tests: `test_f052_{clasificar,sincronizar_ambito,repositorio,endpoints}.py` (sv4)
y `test_f052_api_sincronizar.py` (sv5).

Los 38 matados, mutante a mutante con su test, en `progress/mutacion_F-052.md` (secciones «Análisis (MATADO)»).

**Justificación PENDIENTE DE ACEPTAR POR EL HUMANO (4 equivalentes)**; demostración ejecutable de cada uno en `mutacion_F-052.md` (8 y 9: `DEMO_FIRMA`, bajo el 8):

| Mutante (línea) | Veredicto | Motivo |
|---|---|---|
| 5 · `sincronizacion.py:175` `split(":", 1)`→`split(":", 2)` | equivalente | `[0]` es lo anterior al primer `:` con cualquier `maxsplit >= 1` (100 000 cadenas aleatorias) |
| 8 · `sincronizacion.py:323` `sort_keys=False` | equivalente | orden de claves fijo (literal + `asdict`); firma opaca, solo se compara consigo misma |
| 9 · `sincronizacion.py:324` `ensure_ascii=True` | equivalente | el escape es inyectivo; misma relación de igualdad entre firmas |
| 14 · `sincronizar_ambito.py:294` `por_confirmar = True` | equivalente | escritura muerta: el único lector (línea 279) va antes; ni `item_a_dict`, ni `firma`, ni `aplicar` lo leen |

Ninguno se mató quitando código defensivo (RM6: N/A). `bash harness/init.sh` (7b83dc3): **ENTORNO LISTO**; sv4 3609 passed, 1 skipped (440 s); sv5 1622 passed; raíz 540 passed; `PUERTA COBERTURA: 99.9% (741/742)`.

## Review 1 (CHANGES_REQUESTED): cambios 1 a 4 aplicados

Sin código de producción, sin relanzar la mutación, sin push. Commits: 31ba861 (1), e425e2e (2),
6f138a2 (3), azure-apps d098bc6 (3, local), 3747c50 (4).
1. **Tests de R14, R26 y R28** (solo tests): sv4 `test_f052_r14_r26_solo_lectura.py` (15),
   sv5 `test_f052_r26_leer_no_escribe.py` (6), raíz `test_f052_r28_congelacion_intacta.py` (4).
   Espías que apuntan cualquier método sin reventar (un `except` no tapa la llamada) y guardias AST.
2. `tasks.md`: T8 `[x]` citando `progress/m2_F-052.md` (M2 superada, líder, 2026-11-03).
3. `design.md` §8: ID10 fuera de la celda aprobada de DA18; ID8 en §4. Los dos **pendientes de
   ratificar por el humano**. ID8 también en la fila `/api/sincronizar/aplicar` de `azure-apps/partes.md`.
4. `mutacion_F-052.md`, superviviente 9: el surrogate suelto, reproducido (original
   `UnicodeEncodeError`, mutante firma). Sigue sin observarse: el `JSONResponse` de sv4 revienta
   igual y sv5 ya da 500 antes (sv4 responde 502). Matarlo cambia producción: lo decide el humano.

**Fase RED** (copia `git archive HEAD` en el scratchpad, `red_review1/`, con lo vigilado roto a
mano; el árbol real no se tocó). Python del `.venv`, `-q -p no:cacheprovider --tb=line`, `E`
contadas con `sort | uniq -c`. La rotura se deshizo tras cada pasada y el fichero volvió a verde.
- R14, `self._repo.guardar_sincronizacion(cuerpo)` en `_sincronizar`. Con
  `pytest tests/test_f052_r14_r26_solo_lectura.py -k r14` (el `-k` casa con el nombre del módulo:
  corren los 15):
```
     13 E   AttributeError: 'RepoAcciones' object has no attribute 'guardar_sincronizacion'
13 failed, 2 passed in 0.31s
```
- R26 sv4, `self._sv5.ejecutar({"lineas": []})` en `_ejecutar` (mismo fichero, `-k r26`):
```
     10 E   AssertionError: assert ['ejecutar'] == []
      1 E   AssertionError: assert {'comprobar',...ronizar_leer'} == {'comprobar',...ronizar_leer'}
11 failed, 4 passed in 0.14s
```
- R26 sv5, `_lector().escribir([])` en la ruta (`pytest tests/test_f052_r26_leer_no_escribe.py`):
```
      1 E   AssertionError: assert 'escribir' not in ['lineas_sincronizar', 'escribir']
      1 E   AssertionError: assert 'escribir' not in ['lineas_sincronizar', 'lineas_sincronizar_por_synckey', 'escribir']
      1 E   AssertionError: assert not ({'Exception', 'JSONResponse', 'SincronizarIn', '_lector', 'ambito', 'app', ...} & {'_lock', 'escribir', 'lock', 'pipeline'})
3 failed, 3 passed, 1 warning in 1.29s
```
- R28 (raíz, `pytest tests/test_f052_r28_congelacion_intacta.py`), tres roturas:
  (a) `registrado` deja de congelar en `congelacion.py` (con un comentario «sincronizar»):
  `2 failed, 2 passed` (`assert [False, True, False, True] == [True, True, True, True]` y
  `AssertionError: congelacion.py`); (b) `aplicar_marcar_registrada` también asigna `reg.horas`:
  `1 failed, 3 passed` (`assert {'aplicar_mar...er_de_sigrid'} == {'aplicar_traer_de_sigrid'}`);
  (c) `web/app.py` nombra `aplicar_traer_de_sigrid`: `1 failed, 3 passed`.
- Verde en el árbol real: 15, 6 y 4 passed; `ruff check` limpio en los tres ficheros.

**`bash harness/init.sh`** (tras estos commits): INIT_PENDIENTE
