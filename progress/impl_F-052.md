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

## M3 · PENDIENTE del humano (local, modo pruebas, obra 0404)

Solo escribe en Sigrid la aprobación del portal (sv5 en pruebas, obra 0404, `PRUEBA-IA`);
sincronizar y aplicar solo leen Sigrid. Mes `<M3>` (`<AAAA>`, `<MM>`): nunca 2026/06–2026/11
(PT26/00373, 00375 y 00376 se conservan) y con `estado` ⇒ `NO existe parte <AAAA>/<MM> de obra
0404`. Consolas nuevas (sin el `PGOPTIONS` de M2).

1. **V** (`services\partes-transfer\prueba_escritura_sigrid.py`, cambio local sin commit):
   `ANO, MES = <AAAA>, <MM>`; `python .\prueba_escritura_sigrid.py estado` ⇒ `NO existe`.
2. Consola 1, sv5:
   ```powershell
   cd C:\Users\pgris\PycharmProjects\partes-wt-f052\services\partes-transfer
   ..\..\..\partes\.venv\Scripts\Activate.ps1
   $env:OBRA_PRUEBAS_FORZAR = 'true'; python main.py
   ```
   `Invoke-RestMethod http://localhost:8005/health` ⇒ `modo_pruebas: True`, `obra_pruebas:
   0404`. **Si no, PARA.**
3. Consola 2, sv4 contra la base `partes` LOCAL:
   ```powershell
   cd C:\Users\pgris\PycharmProjects\partes-wt-f052\services\partes-front
   ..\..\..\partes\.venv\Scripts\Activate.ps1
   python -c "from config.settings import Settings as S; s=S(); print(s.pg_host, s.sincronizar_seco)"
   $env:TRANSFER_BASE_URL = 'http://127.0.0.1:8005'; python main.py
   ```
   Si `pg_host` no es local, **PARA** (no edites el `.env`: avisa al líder). Portal en
   `http://127.0.0.1:8014`; el actor será `local:<DEFAULT_REVIEWER>`.
4. «+ Nuevo parte» en la **obra 0404**, trabajador 2717792, 4 líneas ordinarias de 8 h (días
   L1–L4 de `<M3>`) ⇒ crear ⇒ aprobar las 4 ⇒ «Registrar». V `verificar` ⇒ 4 líneas.
5. En Sigrid, a mano, en el parte de la 0404 de `<M3>`: L1 `can` 8 → 6; L3 `can` → 0.
   En la base local: `UPDATE parte_registros SET sigrid_estado = 'error' WHERE id = <L4>;`
6. Vista de la obra 0404, periodo `<AAAA>-<MM>`, natural ⇒ «Sincronizar con Sigrid». Esperado:
   L1 `distinta` (horas 8/6, «Traer de Sigrid»), L2 `igual`, L3 `anulada_en_sigrid`, L4
   `en_sigrid_sin_registrar` («Marcar registrada»). Si la 0404 no se ofrece en «+ Nuevo parte»,
   usar otra obra y la vista de la persona (`rec-2717792`): las 4 llevarán además la diferencia
   `obra` y L2 saldrá `distinta` sin acción.
7. Aplicar «Traer de Sigrid» a L1 y L3 y «Marcar registrada» a L4 (confirmar). Opcional, firma
   vieja: cambiar otra vez L1 en Sigrid sin re-sincronizar y aplicar ⇒ «cambió desde que lo
   viste». Comprobar en local:
   ```sql
   SELECT id, horas, sigrid_estado, sigrid_hmores_ide, sigrid_motivo, sigrid_registrado_by
   FROM parte_registros WHERE id IN (<L1>, <L2>, <L3>, <L4>) ORDER BY id;
   ```
   ⇒ L1 6 y L3 0, con «Sincronizado con Sigrid: horas 8→6 · local:… · …»; L4 `registrado` con
   su `hmores_ide` y «estado error→registrado · local:…». Consola 2:
   `[sincronizar][aplicar] … recalculo=…`; consola 1: `[sincronizar] ambito=…` y **ninguna
   escritura `[sigrid-write]`** durante sincronizar y aplicar.
8. Limpieza (V con `<M3>`; si el DRY-RUN muestra otro ide de parte, **PARA**):
   ```powershell
   python .\prueba_escritura_sigrid.py limpiar
   python .\prueba_escritura_sigrid.py limpiar --ejecutar
   python .\prueba_escritura_sigrid.py estado
   git checkout -- prueba_escritura_sigrid.py
   ```
   `estado` ⇒ `NO existe`. Ctrl+C en las consolas 1 y 2 y cerrarlas.

**M4 · PENDIENTE del humano (tras desplegar sv5 → sv4).** Decidir antes `SINCRONIZAR_SECO` en Azure (ID10). Un usuario real sincroniza y aplica una
acción; en la base `partes`, solo lectura: `SELECT id, horas, sigrid_estado, sigrid_motivo,
sigrid_registrado_by FROM parte_registros WHERE sigrid_motivo LIKE 'Sincronizado con Sigrid:%'
ORDER BY id DESC LIMIT 10;` ⇒ actor de Easy Auth (ni `local:` ni `sin-identidad`).

## Fuera de alcance y pendiente

- H-M2-1b (`option.ext` en el selector de hora): fuera; se propone como feature aparte.
- Mutación: la lanza el líder (`python -m harness.mutacion --feature F-052`). M3, M4, reviewer.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests F-052 (T9–T13) | sv4 `test_f052_*` 215 + 115 + 11 + 17 passed; raíz T13 3 passed (guardianes 62) |
| Suites completas (init.sh) | sv4 3580 passed, 1 skipped; raíz 540 passed, 3 skipped; sv1, sv2, sv3, sv5 en verde (caché: sin cambios) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 99.7% de 742 líneas cambiadas cubiertas (740/742, umbral 80%, nivel critico)` |
| Mutantes | no lanzada en esta tanda: la lanza el líder |
| Tiempo de la suite | sv4 942–1080 s (con cobertura); raíz 91–157 s |
