<!-- progress/impl_F-069.md -->
# F-069 · Informe del implementer

sv3: extras automáticas con ids estables y recálculo en una sola transacción; sv4: el 422 de
ámbito dice cuántas líneas ya no existen (DA1). Rama `feature/F-069-extras-ids-estables`,
worktree `partes-wt-f069`, base `0a91941`. Rigor **crítico**. No se tocaron `esta_congelado`,
`ESTADOS_CONGELADOS`, `_congelado` (sv3), `congelacion.py` (sv4), `orm_models.py` (ninguno),
`plan_revert`/`clave_pareja`/`es_miembro`/`claves_congeladas`, F-045/F-046, sv1, sv2, sv5 ni
`infra/`. Sin push. Commits en LF (comprobado: ningún blob de la rama lleva `\r`).

## Commits (uno por tarea)

| Tarea | Commit | Qué |
|---|---|---|
| T1 | 6c0a364 | tests puros RED (`test_f069_pareja_puro.py`) |
| T2 | 9c55e53 | `vista_revertida`, `CAMPOS_HUELLA`, `huellas_por_clave`, `emparejar_extras`, `LecturaPasada` |
| T3 | 0f0a72c | tests RED de `leer_pasada` + `tests/f069_comun.py` (siembra común) |
| T4 | 88ed120, 129ceec | `leer_pasada`; el 2.º commit rehace el 1.º (ver D1) |
| — | 9b4519d | `current.md` con D1-D3 y tareas T1-T4 marcadas |
| T5 | 5512d38 | tests RED de `escribir_pasada` |
| T6 | 1cd5e7d | `escribir_pasada`, `_bloquear_documentos`, `_campos_extra`, `_rellenar_extra`, envoltorio `revert_extras_auto` |
| T7 | bdd370c | tests RED de concurrencia con sv4 |
| T8 | e17841e | `_parejas_cambiadas` (huella, WARNING, `parejas_cambiadas`) |
| T9 | 6d48eb0 | tests RED de la pasada completa (R1, R6, R9, R10) |
| T10 | 64435f5 | `_pasada` recableada, `RepositorioFake`, aserción de orden de F-046 R18 |
| T11 | 1b82778 | `test_f069_pg_lector_concurrente.py` (M1) |
| T12 | 5cfb9f6 | tests RED de sv4 (R20, R21) |
| T13 | 89640bf | sv4: `registro_ids_existentes` y `_validar_ambito` |
| T14 | 8ebf782 | `docs/ARCHITECTURE.md` |
| T16 | bae6363 | guardianes de gemelos (56 passed) y tareas marcadas |
| T15/T19 | (commit de este informe) | mutación, `init.sh` |

## Qué cambió (producción)

- `services/partes-persistencia/application/services/pareja_extra.py` (+101): núcleo puro nuevo
  (design §3). Lo de F-037 sin tocar.
- `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py`:
  - `leer_pasada()` (nuevo): llama a `fetch_registros_para_recurso` (intacto), calcula
    `plan_revert` sobre las filas que consulta el revert, devuelve la vista revertida con
    `congelada_por_pareja` recalculada y las huellas del estado crudo. No escribe.
  - `escribir_pasada(lectura, updates, splits) -> ResumenEscritura` (nuevo): una sesión, un
    `commit`, rollback y reenvío de la excepción si algo lanza. Pasos: bloquear (todas las filas
    de los partes afectados, por `id`, `FOR UPDATE OF parte_registros` solo en PostgreSQL;
    `IN` en lotes de `LOTE_IN = 1000`), plan nuevo, parejas cambiadas, casados, revert, splits
    por pareja con `emparejar_extras` (la extra se rellena en el sitio o se crea; lo que sobra se
    borra).
  - `_parejas_cambiadas`: compara las huellas de la lectura con las de las filas bloqueadas,
    solo en partes que estén en las dos; WARNING `[repo] pareja cambiada durante la pasada:
    documento=… linea=… fecha=…` (sin nombres ni DNI).
  - `_extra_de` = `ParteRegistroOrm(**_campos_extra(...))` + `id`/`sigrid` como antes;
    `_rellenar_extra` recorre todas las columnas del ORM salvo `id` (DA2).
  - `revert_extras_auto()` = `escribir_pasada(None, [], []).borradas`. `apply_extras_splits` y
    `apply_recurso_matches` sin cambios.
- `services/partes-persistencia/application/services/recurso_conciliador.py` (`_pasada`): sin el
  revert previo; `lectura = leer_pasada()` tras `materializar_repartos`; al final, una
  `escribir_pasada`. `actualizados`/`extras_reclasificadas` salen del resumen; el log añade
  `extras_nuevas`, `extras_reutilizadas`, `extras_borradas`, `parejas_cambiadas`. El dict
  devuelto no cambia (DA8). Comentario de `_pasada` y docstring de `_reclasificar_extras_jornada`
  actualizados.
- `services/partes-front/infrastructure/database/parte_repository.py`:
  `registro_ids_existentes(ids) -> set[int]` (cualquier fila, por lotes de `LOTE_IDS_CONSULTA`).
- `services/partes-front/interface_adapters/web/app.py` (`_validar_ambito`): con ids fuera,
  una llamada a `registro_ids_existentes(ajenos)`; si hay inexistentes, el 422 lleva
  `inexistentes` y el texto de design §7. Sin inexistentes, respuesta idéntica a la de hoy
  (lo comprueba un test con igualdad exacta del JSON). JS sin cambios (`node --check` OK).
- `docs/ARCHITECTURE.md`: párrafo F-069 junto a F-037. `azure-apps/partes.md`: **sin cambios**;
  `grep -i "revert|fuera_de_ambito|no son de esta vista|ids de extra"` no da ninguna línea (el
  documento no describe el revert, los ids de las extras ni el 422 de ámbito).

## Desviaciones y decisiones (justificadas también en `progress/current.md`)

- **D1 · `fetch_registros_para_recurso` no pasa a ser `leer_pasada().registros`** (design
  §4.1). Conserva su cuerpo y su contrato crudo, y `leer_pasada` se construye encima. Motivo:
  R18 y la verificación de T4 exigen `test_f037_*` en verde, y
  `test_f037_revert.py::test_f037_r9_*` llama a `fetch` sin revert previo y espera ver la extra.
  Además, `test_f003_r26_fetch_registros_trae_el_document_id` inspecciona el código fuente de
  `fetch`; el primer intento (88ed120) lo rompía y 129ceec lo rehízo. Así R11 se prueba sin
  circularidad: `leer_pasada` contra `revert_extras_auto` + `fetch` sobre la misma siembra.
- **D2 · el plan de `leer_pasada` y el de `escribir_pasada` se calculan sobre las filas que
  consulta el revert** (`extra_auto` o `horas_orig` no nulo), igual que `revert_extras_auto`. Si
  se calculasen sobre todas, una base congelada sin `horas_orig` protegería a su extra, y el
  revert de hoy la borra (variante p4 del escenario de `f069_comun.py`, cubierta por R11).
- **D3**: siembra y dobles comunes en `tests/f069_comun.py`, que no es un módulo de tests.
- **Comparación de huellas** (detalle no escrito en el design): solo se comparan claves de
  partes que estén a la vez en la lectura y entre las filas bloqueadas. Así, una pareja sin
  extras, splits ni casados no se marca «cambiada» solo porque no se bloqueó.
- **R14**: sale de la huella, porque `sigrid_estado` y `doc_approved` están en ella. Una pareja
  que ya estaba congelada al leer y lo sigue al escribir no cuenta como cambiada (hay test).
- **Hallazgo fuera de alcance, para el líder**: en laborable, una ordinaria por debajo de la
  jornada genera una `extra_auto` **negativa** (7 h ⇒ 8 + (−1)). Es el diseño de F-045 (DA6,
  `reparto_ponderado.py:164`) y no lo cambia esta feature. Lo anoto porque al escribir el test
  de R4 lo esperaba de otra forma: el test usa 8 h justas.
- `_PISA` existe ahora como atributo de clase (para `escribir_pasada`) y como local en
  `apply_recurso_matches` (intacto, R18). Es la misma tupla en el mismo fichero: el reviewer
  puede pedir que la segunda use la primera.

## Fase RED (trazas reales, comando exacto; recortadas solo en anchura)

Todas desde `services/partes-persistencia` (T12, desde `services/partes-front`).

```
## T1  python -m pytest tests/test_f069_pareja_puro.py -q
E   ImportError: cannot import name 'CAMPOS_HUELLA' from 'application.services.pareja_extra'
1 error in 0.26s
## T3  python -m pytest tests/test_f069_una_transaccion.py -k leer -q
E       AttributeError: 'SqlAlchemyParteRepository' object has no attribute 'leer_pasada'  (x5)
5 failed in 2.48s
## T5  python -m pytest tests/test_f069_ids_estables.py tests/test_f069_una_transaccion.py -k escribir -q
E       AttributeError: 'SqlAlchemyParteRepository' object has no attribute 'escribir_pasada'  (x14)
14 failed, 6 deselected in 1.53s
## T7  python -m pytest tests/test_f069_concurrencia_sv4.py -q   (escribir_pasada aún sin huella)
E       AssertionError: assert [(1, 'doc-1', ... 7.5 ...)] == [(1, 'doc-1', ... 8.0 ...)]
FAILED ...test_f069_r13_pareja_cambiada_no_se_toca[base_nueva|encolado|error|extra_auto|
  fila_borrada|horas|horas_orig|miembro_nuevo|papelera|parte_aprobado|parte_inactivo|
  registrado_base|tipo_hora]
13 failed, 5 passed in 1.55s
## T9  python -m pytest tests/test_f069_ids_estables.py tests/test_f069_una_transaccion.py -q  (_pasada de hoy)
E       AssertionError: assert ['INSERT INTO... ?, ?, ?, ?)'] == []
E         Left contains 6 more items, first extra item: 'INSERT INTO parte_registros (document_id, ...
E       AssertionError: assert ['INSERT INTO... ?, ?, ?, ?)'] == []
E       AssertionError: assert 'extras_nuevas=2 extras_reutilizadas=0 extras_borradas=0 parejas_cambiadas=0' in ...
E           AssertionError: commit 0: pareja a medias
E             {('doc-1', 0, 1, 20261001): ((10.0,), (None,), ())} != {('doc-1', 0, 1, 20261001): ((4.0,), (10.0,), ((3, 6.0),))}
E             {('doc-1', 1, 1, 20261001): ((11.0,), (None,), ())} != {('doc-1', 1, 1, 20261001): ((4.0,), (11.0,), ((4, 7.0),))}
E       assert ([(False, 0, 0)] == [(True, 1, 1)]
5 failed, 21 passed in 2.61s
## T11/M1  PostgreSQL 16 desechable; el test de M1 contra el código de 0a91941 (worktree temporal)
F069_PG_URL=postgresql+psycopg://postgres:<local>@localhost:55432/postgres python -m pytest tests/test_f069_pg_lector_concurrente.py -q -k lector
E       AssertionError: assert Counter({'id ...edias': 5170}) == Counter()
E         {'id de extra distinto': 6182, 'pareja a medias': 5170}
## T12 (sv4)  python -m pytest tests/test_f069_r20_inexistentes.py -q
E       AttributeError: 'ParteReviewRepository' object has no attribute 'registro_ids_existentes'  (x4)
E       KeyError: 'inexistentes'  (x4)
8 failed, 3 passed in 4.07s
```

El «commit 0» de T9 es el bug de la 0697 reproducido: tras el commit del revert, la base se ve
entera (10 h, sin `horas_orig`) y sin su extra. En PostgreSQL real, el código de antes dejó ver
**5170 lecturas** con una pareja a medias y **6182** con ids de extra distintos en 20 pasadas.
Con F-069 fueron **0 y 0** (3 ejecuciones seguidas). Los 3 tests de T12 que ya pasaban son de
caracterización: los ids ajenos que existen siguen dando la respuesta de hoy.

## Verificación

- `python -m pytest` en sv3: **2447 passed, 2 skipped** antes de T15 (2453 con `test_f069_mutacion.py`) (los 2 de M1 sin `F069_PG_URL`).
  Dorados de F-003 R15 y F-045 sin tocar sus valores. Único test existente cambiado:
  `test_f046_conciliar.py::test_f046_r18_la_pasada_entera_va_bajo_el_candado` (orden
  `materializar` < `leer` < `escribir` < `guardar`, design §6).
- sv4: **3751 passed, 1 skipped**; `test_f019_portal.py` + `test_f022_aprobar_seleccion.py` +
  T12: 186 passed. `node --check static/app.js` OK.
- T16, guardianes (`tests/test_f010_orm_models_gemelos.py`, `test_f024_borrado_no_congela_gemelos.py`,
  `test_f023_de_alta_gemelos.py`, `test_f036_recurso_persona_gemelos.py`): **56 passed**.
- **M1 (T17) hecha** contra `postgres:16` en Docker local (`pg-f069`, puerto 55432, contraseña
  desechable que no está en ningún fichero; contenedor parado al terminar):
  `F069_PG_URL=… python -m pytest tests/test_f069_pg_lector_concurrente.py -v` → **2 passed**
  (lector concurrente en 20 pasadas sin violaciones, secuencia sin avanzar; `UPDATE` de una
  fila bloqueada durante `escribir_pasada` corta por `lock_timeout`, es decir, R15). Repetido
  3 veces, siempre verde. Nada contra Azure.

## Pendiente

- **T18 · M2** (líder/humano, tras desplegar sv3, solo lectura en Azure): secuencia
  `parte_registros_id_seq` y ids de `extra_auto` antes y después de una tanda; en Log
  Analytics, `extras_reutilizadas` ≈ `extras_reclasificadas` y `parejas_cambiadas` = 0 casi
  siempre; `data-registro-id` iguales tras otra pasada. Pasos completos en
  `requirements.md` §M2. Desplegar lo pide el humano.
- Reviewer contra `CHECKPOINTS.md`.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | sv3 **2453 passed, 2 skipped** (los 2 de M1 sin `F069_PG_URL`; 2447 antes de T15 + 6 de `test_f069_mutacion.py`); sv4 **3751 passed, 1 skipped**; raíz 544 passed, 3 skipped; M1 en PostgreSQL 16: 2 passed (×3) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 100.0% de 211 líneas cambiadas cubiertas (211/211, umbral 80%, nivel critico)` (init.sh final; antes de T15 daba 99,5 %, 210/211) |
| Mutantes | `python -m harness.mutacion --feature F-069 --base 0a91941`: **72 generados, 61 muertos, 11 supervivientes, 0 timeouts** en 3806,6 s (4 workers). 10 supervivientes cazados con tests nuevos en `services/partes-persistencia/tests/test_f069_mutacion.py`, comprobados uno a uno a mano (los 10 MUERTO). 1 **equivalente** justificado (n.º 10, `zip(..., strict=True)` en `leer_pasada`): el rigor crítico pide que **el humano acepte** esa justificación. Detalle en `progress/mutacion_F-069.md` (sin `PENDIENTE`) |
| Tiempo de la suite | sv3 36,9 s; sv4 660 s (dentro de init.sh, con la máquina cargada; 411 s sola); raíz 80,7 s |
| `bash harness/init.sh` | **verde**: `ENTORNO LISTO`; sv3 2453 passed, 2 skipped; sv4 en caché del verde de 3751; `PUERTA TAMAÑO` impl 177/220. Un intento anterior salió en rojo (3 tests de `test_f069_mutacion.py`) por bytecode viejo: al restaurar a mano el último mutante de cada fichero, `.pyc` y fuente coincidían en segundo y tamaño. Se borró `__pycache__` de sv3 y quedó en verde. Los veredictos MUERTO no se ven afectados: cada mutante cambiaba el mtime y se recompilaba |
