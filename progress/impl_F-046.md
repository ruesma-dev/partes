# F-046 · Informe del implementer: reajuste en Sigrid al aprobar

Rama `feature/F-046-reajuste-en-sigrid-al-aprobar` (worktree `partes-wt-f046`), rigor
**crítico**. Toca sv5, sv3, sv4, las dos copias del ORM, docs y `azure-apps/partes.md`.
Interruptor `REPARTO_REAJUSTE` (sv3) **apagado por defecto**: apagado, sv3 es F-045 (R10).

## T1 · API real de F-045

`9c5b7a1` es ancestro de HEAD; `test_f045_*` (sv3): 211 passed. **H9**: `LineaDia` ya trae
`extra_auto` y `base_id` (enmienda A de F-045): se usan tal cual y solo se añade
`reajustable: bool = False`.

## Qué cambió (un commit por tarea, `git log dev..HEAD`)

| Bloque | Ficheros |
|---|---|
| sv5 T2–T5 | `application/services/reajuste_lineas.py` (nuevo, veredictos R21/R22/R26), `application/pipelines/reajuste_pipeline.py` (nuevo), `infrastructure/sigrid/sigrid_write_client.py` (solo métodos nuevos), `domain/models/registro_models.py` (`OpReajuste`, `VeredictoReajuste`, `ResultadoReajuste`; `LineaSigrid.pre/hmoide/enlazada` con defecto), `interface_adapters/api/app.py` (rutas), `main.py` (composición) |
| ORM T8 | `RepartoPendienteOrm` + `ESTADOS_REPARTO` en las DOS copias (byte-idénticas); guardianes a siete tablas con `COLUMNAS_REPARTO_PENDIENTE` |
| sv3 T9–T12 | `reparto_ponderado.py` (`proponer_dia`, `CambioCongelada`, `PropuestaDia`), `reajuste_reparto.py` (nuevo), `recurso_conciliador.py`, `sqlalchemy_parte_repository.py`, `config/settings.py`, `interface_adapters/api/app.py`, `tests/dobles.py` (`RepositorioFake` al día) |
| sv4 T14–T18 | `application/services/reparto_aviso.py` (nuevo), `parte_repository.py`, `transfer_client.py`, `recalculo_publisher.py` (`MOTIVO_REAJUSTE`), `interface_adapters/web/app.py`, `static/app.js`, `static/styles.css`, plantillas de obra y trabajador |
| Raíz/docs T16, T20, T21 | `tests/test_f046_contrato_reajuste.py`; `docs/ARCHITECTURE.md`; `docs/referencia/partes-proyecto.md`; `azure-apps/partes.md` (commit local `azure-apps`, solo ese fichero) |

**No tocados** (comprobado con `git diff dev --stat`): `estado_parte.py`, `cuenta_analitica.py`,
`interface_adapters/queue`, `registro_pipeline.py` (sv5); `congelacion.py`, `jornada_resolver.py`
(sv3 y sv4), `pareja_extra.py`; `esta_congelado`/`ESTADOS_CONGELADOS`/`_congelado`;
`test_f045_*`; `CLAUDE.md`. En `sigrid_write_client.py` y `registro_models.py` el diff solo añade.

## Decisiones y desviaciones (justificadas)

1. **Guardia (DA6)**: `can = CONVERT(INT, 'reajuste-descuadrado-' + CAST(ide…))` en vez de `can / 0`
   (con `ANSI_WARNINGS` apagado dividir por 0 da NULL y confirmaría). **Cuenta** las líneas en su
   estado esperado (synckey, `can` = «antes», sin enlaces, parte En registro) y falla si no son
   todas o si alguna extra nueva ya existe. M3 (e bis) lo comprueba contra la API real.
2. **INSERT de la extra condicionado** (`stmt_insertar_extra`, nuevo; `stmt_insert_linea` no se
   toca): solo entra si la base ya tiene «después» y su synckey no existe; `MAX(ide)+1` en
   subconsulta. Una base borrada a mano entre leer y escribir no deja extra huérfana.
3. **sv5 decide releyendo**: todo con «después» = hecho; nada = rechazo `ok:false`; a medias =
   excepción → 502 → sv4 lo deja `aplicando` con ERROR (DA6). Un 5xx/timeout no es rechazo.
4. **R26 antes que el estado del parte**: con «después» es `ya_aplicada` aunque cerraran el parte.
5. **R22 · otra obra**: la extra nueva exige que el parte de su base sea de la obra destino.
6. **`fetch_registros_para_recurso` sin claves nuevas** (design §4): `test_f037_r9` fija el
   conjunto exacto; `sigrid_hmores_ide` y `obra_codigo` los rellena `guardar_repartos`.
7. **`clase_linea(reg, *, congelada)`** recibe la congelación hecha (evita un import circular).
8. **Wiring de sv3 en `interface_adapters/api/app.py`** (`main_worker.py` reutiliza `build_app`);
   `candado_espera_s` se asigna tras construir el repositorio (no rompe los dobles de F-042/F-043).
9. **Candado (R18)** siempre que el repositorio lo tenga, también apagado; conexión propia en
   `AUTOCOMMIT`; si no puede soltarlo, invalida la conexión. `TimeoutError`: la cola reintenta; la
   ingesta lo deja en WARNING (`persist_parte_pipeline`, fuera de alcance) y recalcula después.
10. **Máquina de estados**: `decidir_grupo` añade `residual` (R12). `aplicando`/`aplicado`: fila y
    congelado intactos, lo libre al ideal. Grupo desaparecido ⇒ `obsoleto`; grupo presente que la
    pasada no reparte ⇒ no se toca. Encendido, sin el WARNING de medición de F-045.
11. **sv4**: `RepartoCambiadoError`/`RepartoPendienteError` ⊂ `CongeladoError` (409).
    `iniciar_aplicacion` admite `aplicando` (R34) y conserva las reservas; las extras automáticas
    de lo libre no son «líneas nuevas». Reserva por `nextval(pg_get_serial_sequence(...))`.
12. **Preflight** consultivo «como si se aplicara», con `repartos`; la extra sin reserva va a sv5
    con id provisional `-base`. **Cliente sv4**: rechazo (`ok:false`, también sin conexión) frente
    a `sin_respuesta` (timeout, error a mitad, 5xx).
13. **Modal**: cada decisión viaja una vez, en la llamada (síncrona o cola) que lleva líneas de su
    día (`decisionesPara`); el servidor rechaza (409) un reparto ajeno. Sin decisión → alerta.

## Fase RED (trazas reales; comando `python -m pytest -q <fichero>` desde cada servicio)

Sin «ModuleNotFound» como RED: antes del código se dejó un stub o solo las constantes, para que
fallaran las aserciones. T16 y T18 se escribieron antes que su test: su RED es una copia aislada
(scratchpad) con lo de `dev`. T6, T13, T19 son suites; T7, T20, T21, T23 no tienen código.

**T2 (sv5) R21 R22 R26 — `-m pytest -q tests/test_f046_reajuste_lineas.py` con stub que devuelve siempre editable**
```
E       assert (True, False, None) == (True, True, None)          # r26 ya_aplicada
E       assert (not True)  where True = VeredictoReajuste(registro_id=11, editable=True, ...).editable   # r21 parte cerrado / enlazada / can distinta
20 failed, 4 passed in 0.55s   (los 4 que pasan: los casos «editable»)
Verde: 24 passed in 0.39s
```
**T3 (sv5) R21 R24 R25 R27 R47 — `tests/test_f046_cliente_reajuste.py`, solo con ENLACES_HMORES añadido**
```
E       AttributeError: 'SigridWriteClient' object has no attribute 'escribir_lote'          (x7)
E       AttributeError: 'SigridWriteClient' object has no attribute 'stmt_guardia_reajuste'  (x4)
E       AttributeError: 'SigridWriteClient' object has no attribute 'lineas_para_reajuste'   (x4)
E       AttributeError: 'SigridWriteClient' object has no attribute 'stmt_insertar_extra'. Did you mean: 'stmt_insert_linea'?
E       AttributeError: 'SigridWriteClient' object has no attribute 'stmt_actualizar_linea'
21 failed, 2 passed in 0.78s
Verde: 23 passed in 0.31s
```
**T4 (sv5) R20 R22-R29 R47 — `tests/test_f046_reajuste_pipeline.py` con un ReajustePipeline vacío (ok=True siempre, sin escribir)**
```
E       assert (8.0, 160.0) == (2.5, 50.0)                 # r24 caso real: nada escrito
E       assert (not True) where True = ResultadoReajuste(ok=True, ...).ok   # r23 / r27 / r22: no rechaza
E       Failed: DID NOT RAISE RuntimeError                   # r23 fallo de lectura
E       assert (True and False) ... .ya_aplicada             # r26
E       assert False where False = ResultadoReajuste(...).forzada_pruebas   # r28
Verde: 23 passed in 0.28s
```
**T5 (sv5) R20 R23 — `tests/test_f046_api_reajuste.py` con solo MAX_LINEAS_REAJUSTE y el parámetro `reajuste`**
```
E       AssertionError: assert 404 == 422          (rutas inexistentes)
E       assert 404 == 502
E       KeyError: 'reajuste'                         (main no compone el reajuste)
```
**T8 (raíz) R39 — guardianes con TABLAS a siete y COLUMNAS_REPARTO_PENDIENTE, ORM sin la tabla**
```
E       AssertionError: la base 'partes' tiene SIETE tablas (...)
E         At index 5 diff: 'undo_log' != 'reparto_pendiente'
E       KeyError: 'reparto_pendiente'
FAILED test_f010_orm_models_gemelos.py::test_f010_r4_el_orm_canonico_tiene_las_tablas_y_56_columnas
FAILED test_f010_orm_models_gemelos.py::test_f046_r39_reparto_pendiente_declara_sus_columnas_literales (+ atributos, + f015_r29 lista)
Verde: 28 passed in 11.18s; sv3 test_f046_orm_reparto.py 3 passed
```
**T9 (sv3) R1-R9c — `tests/test_f046_proponer_dia.py` con un proponer_dia que hace lo de F-045 (repartir_dia, sin cambios)**
```
FAILED test_f046_r6_caso_real_0678_registrada_y_0704_nueva
E       assert {3: (0.0, 8.0)} == {3: (5.5, 2.5)}
FAILED test_f046_r7_extra_nueva_de_una_base_registrada_sin_extra
E       assert {3: (0.0, 4.0)} == {3: (2.5, 1.5)}
FAILED r8, r9c_e, r1 orden, r3 dura, r4 no laborable + 264 casos de las propiedades R2/R1
271 failed, 353 passed in 7.09s  (pasan R9 —0678 encolada = F-045—, R9a/R9b sin congeladas, R5)
```
**T10 (sv3) R11-R15 — `tests/test_f046_reajuste_reparto.py` con un stub (todo libre, firma vacía, siempre proponer)**
```
E       AssertionError: assert 'libre' == 'reajustable'      (x8)
E       AssertionError: assert '' != ''                      (firma, x8)
E       AssertionError: assert 'proponer' == 'residual'      (x6)
```
**T11 (sv3) R15-R18 — `tests/test_f046_candado.py tests/test_f046_conciliar.py`, solo con CLAVE_CANDADO_CONCILIAR y `candado_espera_s`**
```
E       AttributeError: 'SqlAlchemyParteRepository' object has no attribute 'materializar_repartos'  (x8)
E       AttributeError: 'SqlAlchemyParteRepository' object has no attribute 'guardar_repartos'       (x8)
E       AttributeError: 'SqlAlchemyParteRepository' object has no attribute 'candado_pasada'          (x6)
E       AttributeError: 'SqlAlchemyParteRepository' object has no attribute 'repartos_vigentes'
E       AttributeError: 'NoneType' object has no attribute 'horas'     (apply_extras_splits sin `id`)
```
**T12 (sv3) R10-R14 R18 R19 R46 — `tests/test_f046_conciliar.py` con solo el parámetro `reajuste` (sin comportamiento)**
```
E       assert (0.0, 8.0) == (5.5, 8.0)                     # r11: lo libre sigue en 0 + 8 (F-045)
E       ValueError: not enough values to unpack (expected 1, got 0)   # r11/r46: no nace el reparto
E       sqlalchemy.exc.NoResultFound: No row was found when one was required   (r13/r14/r15)
E       KeyError: 'repartos_propuestos'                     # r19
E       AssertionError: assert ('revert' == 'candado'       # r18: sin candado
E       Failed: DID NOT RAISE TimeoutError                   # r18
E       assert 0.0 == 2.5                                    # r46
```
**T14 (sv4) R30-R33 — `tests/test_f046_reparto_aviso.py` con un reparto_aviso vacío**
```
E       KeyError: 'opciones'  (x4) · KeyError: 'editable' (x3) · KeyError: 'fecha'
E       assert 0 == -11                                      # id provisional
E       AssertionError: assert {} == {20: 'p'}               # r32 exclusiones
E       IndexError: list index out of range                  # r33 payload vacío
```
**T15 (sv4) R32-R36 R38 — `tests/test_f046_aplicar.py tests/test_f046_aprobar_documento.py` sin los métodos del repositorio**
```
E       AttributeError: 'ParteReviewRepository' object has no attribute 'iniciar_aplicacion'   (x16)
E       AttributeError: ... 'repartos_de_registros' (x3) · 'rechazar_reparto' (x3) · 'registros_con_reparto'
E       Failed: DID NOT RAISE RepartoPendienteError          (x3, r36)
E       assert [3, 4, 5] == [5]                              # r32: las del reparto viajan
E       TypeError: ... lineas_para_registro() got an unexpected keyword argument 'repartos_decididos'
```
**T16 (sv4) R34 — código escrito antes que el test: RED sobre una copia aislada de `dev` (git archive en el scratchpad) con solo MOTIVO_REAJUSTE añadido**
```
E       AttributeError: 'TransferClient' object has no attribute 'reajuste_ejecutar'   (x8)
E       AttributeError: 'TransferClient' object has no attribute 'reajuste_comprobar'
```
**T17 (sv4) rutas R30-R35 R38 — `tests/test_f046_aplicar.py` (sección rutas) con el repositorio ya hecho y las rutas de `dev`**
```
E       KeyError: 'repartos'                                 # r30: el preflight no trae el bloque
E       AssertionError: {"ok":false,"error":"no hay lineas activas que registrar","excluidas":{...,"reparto_pendiente":2}}   # r33/r35: la decisión no se procesa
E       assert 422 == 409                                    # r33: reparto ajeno
E       AssertionError: assert ('pendiente', None) == ('aplicando', 'timeout')   # r34
```
**T18 (sv4) R31 R37 — código antes que el test: RED en una copia aislada del sv4 actual con plantillas, app.js y styles.css de `dev`**
```
E       AssertionError: app.js no define TEXTO_DECISION_REPARTO          (x5, R31)
E       assert 'data-reparto="pendiente"' in 'data-registro-id="1" ...'  (x3, R37 líneas)
E       assert 0 == 1  where 0 = len([])                                  (x2, matriz y calendario)
E       assert None                                                       (x5, estilos y cableado del modal)
```

## MANUAL pendiente (humano) — también en `progress/current.md`

- **M2** (lectura): la SELECT de enlaces de design §9 por `/api/sql/read` ⇒ todo 0/NULL.
- **M3** (escritura en la 0404, sv5 local con `OBRA_PRUEBAS_FORZAR=true`): (a)–(h) de design §9
  más **(e bis)**: tocar a mano `can` entre `comprobar` y `ejecutar` ⇒ error de conversión
  `reajuste-descuadrado-<ide>` y nada escrito (confirma que sigrid-api revierte el lote).
- **Despliegue sv5 → sv4 → sv3** (interruptor apagado), **M4**, encender `REPARTO_REAJUSTE`,
  **M5** y **M6** (caso real del 14/10 con «Aplicar»): comandos en `progress/current.md`.
- **Aceptar o rechazar los 11 mutantes equivalentes E1–E7** (sección «Equivalentes» de
  `progress/mutacion_F-046.md`, cada uno con su demostración ejecutable). Siguen PENDIENTES.

## Fuera de alcance

- No se borra nada en Sigrid (R47); `persist_parte_pipeline` no cambia (nota 9).
- Repartos de recursos sin código de hora extra o en grupos que la pasada no reparte: no se
  proponen (como F-045).

## T22 · cierre de la campaña de mutación (2026-10-17)

Campaña completa (la lanzó el humano; HEAD `6b9ceed`): 565 mutantes, 436 muertos, 115
supervivientes, 14 timeouts, 25 666 s con 6 workers. Re-evaluación DIRIGIDA, mutante a mutante,
con `progress/redirigir_mutantes_F-046.py` (tests `test_f046_*` del servicio, árbol con los
tests nuevos): **104 supervivientes mueren** con 89 tests nuevos `test_f046_t22_*` (sv5 35,
sv3 32, sv4 22) y **los 14 timeouts mueren** (~37 s por mutante, ninguno colgado: contención de
la máquina, no un bucle). Quedan **11 equivalentes (E1–E7) PENDIENTES del humano**, con
demostración en `tests/test_f046_t22_equivalentes.py` de cada servicio. **0 sin resolver, 0
bugs.** Por qué sobrevivía cada uno, qué test lo mata y su re-evaluación: `progress/mutacion_F-046.md`
(análisis por superviviente, «Equivalentes», «Cierre de T22» y observaciones O1–O3, ninguna
es un bug ni cambia el comportamiento).

## Evidencias

Medido con `bash harness/init.sh` el 2026-10-17 tras T22 (HEAD con los tests `test_f046_t22_*`).

| Evidencia | Valor real |
|---|---|
| Tests (raíz / sv3 / sv4 / sv5) | 493 + 3 skipped / 2150 / 2196 + 1 skipped / 656, todo en verde |
| Tiempo de la suite (raíz / sv3 / sv4 / sv5) | 132,6 s / 56,5 s / 826,0 s / 19,1 s |
| Cobertura de líneas cambiadas | 98,0 % (1176/1200; umbral 80 %, nivel crítico) |
| Mutación (completa, 565) | 554 muertos (436 + 14 timeouts + 104 con tests nuevos), 0 sin resolver, 11 equivalentes PENDIENTES del humano |
| `bash harness/init.sh` | exit 0, «ENTORNO LISTO»; PUERTA TAMAÑO impl 216/220 |
