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

`POST /api/sincronizar/aplicar` `{accion, ambito, items: [{registro_id, firma}]}`:
1. 503 sin sv5; `validar_peticion` ⇒ 422 (acción desconocida, sin ítems, más de
   `SINCRONIZAR_MAX_ITEMS_ACCION`, ids repetidos); F-022 `_validar_ambito` ⇒ 422 si algún id no
   es de la vista (salvo `restaurar`, ID8). Ninguno de estos llama a sv5.
2. Bajo el MISMO candado R29 que `sincronizar`, vuelve a leer y clasificar el ámbito (re-sync).
   Un id que no sale en el re-sync ⇒ 422 de toda la petición. Firma distinta ⇒ descartado
   «cambió desde que lo viste». Acción que no está en `acciones_de` de su clase ⇒ descartado.
3. Ejecuta: `marcar_registrada` y `traer_de_sigrid` con el repositorio (CAS por lo visto:
   estado + `hmores_ide`, horas + `hmores_ide`); `a_papelera` = `borrar_linea(by=actor)`;
   `restaurar` = `restore_registro`; `reaprobar` no escribe: devuelve `abrir_aprobar` y el panel
   abre el modal de aprobar existente. Congelada (F-004) o duplicado activo (F-061) ⇒ descartado.
4. `traer`: un recálculo compartido (F-049) con motivo `sincronizar` para los documentos tocados
   y los del mismo día y persona; el actor es `_actor(request)`.
5. Log INFO `[sincronizar][aplicar] accion= actor= … recalculo=`. Respuesta `{ok, accion,
   seco, aplicados, descartados, recalculo[, abrir_aprobar, incluir_borradas]}`.

Traza (R22): `sigrid_motivo` = «Sincronizado con Sigrid: {cambio} · {actor} · {fecha}» (≤255);
en `marcar` también `sigrid_registrado_by` = actor y las referencias de Sigrid (`hmoide`,
`hmores_ide`, `parte_cod`).

## Decisiones de implementación (ID8–ID14, para el reviewer)

- **ID8 · `restaurar` no pasa por F-022**: la línea está en la papelera y la vista no la lista.
  Su pertenencia al ámbito la prueba el re-sync (sale como `solo_sigrid_nuestra` con `donde`
  papelera); un id que el re-sync no da ⇒ 422 de toda la petición.
- **ID9 · `reaprobar` solo revalida**: con firma y clase al día, abre el modal de aprobar de
  siempre (`registro_ids`, `ambito`, `incluir_borradas`). Doble confirmación: la de R17 y la del
  modal. No hay camino de escritura nuevo hacia Sigrid (R24, R26).
- **ID10 · SECO y `aplicar`**: `aplicar` NO depende de `SINCRONIZAR_SECO`. DA18 protege la
  escritura IMPLÍCITA de R10 (pasar a `borrado_sigrid` al comparar, sin que nadie lo pida); una
  acción explícita la pide un usuario, la confirma y se revalida por firma bajo candado, que es
  lo que DA18 quería garantizar. El re-sync de dentro de `aplicar` SÍ respeta seco (en seco, R10
  sigue solo informando). Consecuencia: en seco, una `borrada_en_sigrid` aún `registrado` no se
  puede llevar a la papelera (está congelada) y vuelve descartada con el motivo de F-004.
  Anotado en `design.md` (fila DA18). **Decisión de despliegue pendiente**: valor de
  `SINCRONIZAR_SECO` en Azure (M4).
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

| Mutante (línea) | Veredicto | Test / motivo |
|---|---|---|
| 1, 2, 3 · `sincronizacion.py:72, 91, 121` `frozen` | matado | `test_f052_r18_lineas_y_diferencias_inmutables` |
| 4 · `sincronizacion.py:155` `<=`→`<` | matado | `test_f052_r8_a_cero_justo_en_la_tolerancia` |
| 6 · `sincronizacion.py:191` `>`→`>=` | matado | `test_f052_r9_diferencia_de_horas_justo_en_la_tolerancia` |
| 7 · `sincronizacion.py:270` `and`→`or` | matado | `test_f052_r8_ciz_hermano_con_ide_menor_no_casa_con_su_inicio` |
| 10 · `sincronizar_ambito.py:81` `<= 0`→`<= 1` | matado | `test_f052_r15_ide_1_es_sincronizable` |
| 11 · `sincronizar_ambito.py:99` `frozen` | matado | `test_f052_r15_ambito_inmutable` |
| 12 · `sincronizar_ambito.py:152` `or`→`and` | matado | `test_f052_r2_linea_de_sv5_con_origen_desconocido_es_error` |
| 13 · `sincronizar_ambito.py:195` `500`→`501` | matado | `test_f052_r18_tope_por_defecto_500` |
| 15 · `sincronizar_ambito.py:335` `and`→`or` | matado | `test_f052_da18_seco_veredicto_sin_registro_id_se_ignora` |
| 16 · `sincronizar_ambito.py:363` `>`→`>=` | matado | `test_f052_r18_tope_justo_es_valido` |
| 17, 18 · sv4 `settings.py:82, 94` `gt/ge` | matado | `test_f052_settings_limites_validos_justos` |
| 19–23 · `parte_repository.py:234–236` (`_mismas_horas`) | matado | `test_f052_r20_cas_de_horas_mismas_horas` (y `..._horas_nulas_en_la_base_...`) |
| 24 · `parte_repository.py:2767` `and`→`or` | matado | `test_f052_r12_donde_estan_parte_con_solo_una_marca_de_borrado` |
| 25 · `parte_repository.py:2789` `with_for_update` | matado | `test_f052_r20_bloqueo_for_update_en_orden_de_id` (sesión doble: SQLite no bloquea) |
| 26 · `parte_repository.py:2873` `or`→`and` | matado | `test_f052_r20_traer_a_linea_sin_estado_lo_dice` |
| 27 · `parte_repository.py:2899` `and`→`or` | matado | `test_f052_r23_traer_linea_sin_recurso_no_da_par_de_dia` |
| 28, 29 · sv4 `app.py:307` largo de `firma` | matado | `test_f052_r18_aplicar_largo_de_la_firma` (1, 64 y 65) |
| 30, 32 · sv4 `app.py:3464, 3479` `include_in_schema` | matado | `test_f052_r18_rutas_fuera_del_esquema` |
| 31, 33 · sv4 `app.py:3473, 3494` `ok: False` | matado | aserción `ok is False` en los dos tests `..._r30_..._sin_transfer_503` |
| 34 · sv5 `settings.py:37` `ge=1` | matado | `test_f052_r6_settings_max_registro_ids_minimo_1` |
| 35 · `registro_models.py:234` `frozen` | matado | `test_f052_r2_linea_sincronizar_inmutable` |
| 36–39 · sv5 `app.py:211, 212, 227` | matado | `test_f052_r6_ide_1_y_un_solo_dia_son_validos` |
| 40 · sv5 `app.py:293` `is None` | matado | `test_f052_r1_lector_inyectado_sin_pipeline` |
| 41 · sv5 `app.py:407` `ok: False` | matado | `test_f052_r6_demasiados_registro_ids_ok_false` |
| 42 · sv5 `app.py:409` `is not None` | matado | `test_f052_r1_log_dice_el_ambito` (caplog) |

**Justificación PENDIENTE DE ACEPTAR POR EL HUMANO (4 equivalentes)**; demostración ejecutable de cada uno en `mutacion_F-052.md` (8 y 9: `DEMO_FIRMA`, bajo el 8):

| Mutante (línea) | Veredicto | Motivo |
|---|---|---|
| 5 · `sincronizacion.py:175` `split(":", 1)`→`split(":", 2)` | equivalente | `[0]` es lo anterior al primer `:` con cualquier `maxsplit >= 1` (100 000 cadenas aleatorias) |
| 8 · `sincronizacion.py:323` `sort_keys=False` | equivalente | orden de claves fijo (literal + `asdict`); firma opaca, solo se compara consigo misma |
| 9 · `sincronizacion.py:324` `ensure_ascii=True` | equivalente | el escape es inyectivo; misma relación de igualdad entre firmas |
| 14 · `sincronizar_ambito.py:294` `por_confirmar = True` | equivalente | escritura muerta: el único lector (línea 279) va antes; ni `item_a_dict`, ni `firma`, ni `aplicar` lo leen |

Ninguno se mató quitando código defensivo (RM6: N/A). `bash harness/init.sh` (7b83dc3): **ENTORNO LISTO**; sv4 3609 passed, 1 skipped (440 s); sv5 1622 passed; raíz 540 passed; `PUERTA COBERTURA: 99.9% (741/742)`.
