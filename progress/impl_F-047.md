<!-- progress/impl_F-047.md -->
# F-047 · Informe del implementer (2026-10-31) — a falta de la campaña de mutación

Rama `feature/F-047-parte-nuevo-en-espera`, worktree `partes-wt-f047`. Rigor **crítico**.
T1–T11, T13 y T14 hechas; T12: cobertura hecha, **mutación completa pendiente (la lanza el líder)**.

## Decisiones del humano aplicadas

- DA11–DA13 = A (2026-10-30, «ok»): matriz fuera; la misma regla con o sin obra/fecha; R19 con
  «suele tardar menos de 1 min; con más partes en cola, unos minutos».
- **Bloqueo en T6 y desbloqueo (2026-10-31, «a»)**: DA3 → **B** (solo el parte **nuevo** en espera
  no se aprueba; el de un recálculo uuid4 sí, porque F-046 «Aplicar» pide un recálculo y registra
  en la misma petición: 3 tests de `test_f046_aplicar.py` caían con DA3-A). Desviación de design §4:
  el estado se lee con `joinedload(ParteRegistroOrm.document)` en el SELECT de líneas que ya existía
  (0 sentencias nuevas; `test_f062_r5_sin_consultas_nuevas` fija 5). Registradas en `design.md`
  §4 y §11, R16–R17 y T6. **Ningún test existente modificado** (`git diff dev --name-status` de
  tests: solo `A`).

## Qué cambió

**sv3** (`services/partes-persistencia/`)
- `domain/ports/parte_repository.py`, `infrastructure/database/sqlalchemy_parte_repository.py`:
  `save_parte(..., recalculo_pedido_id=None)`; con él, pedido = id y su hora = `created_at_utc`,
  en el mismo `session.add` + `commit` (R1, R2, R8, R9).
- `application/pipelines/persist_parte_pipeline.py`: `recalculo_seguimiento`; `seguido` =
  conciliador de recurso + seguimiento; `_conciliar_*_safely` → `bool`; `_marcar_parte_nuevo`
  (INFO `parte nuevo repartido … marcado=`; WARNING con el tipo de error, sin propagar) (R3–R7).
- `interface_adapters/api/app.py`: UN adaptador para el pipeline y `app.state` (R10);
  docstring de `recalculo_seguimiento.py`.

**sv4** (`services/partes-front/`)
- `application/services/seguimiento_recalculo.py`: `MOTIVO_NUEVO`, `MOTIVO_RECALCULO`,
  `motivo_espera` (R11).
- `infrastructure/database/parte_repository.py`: `motivos_espera(ids | None)` (R12);
  `_parte_nuevo_en_espera(doc)` (activo + motivo `nuevo` + `pendiente`), usada en
  `approve_document` (R16, detrás de la guarda de F-046) y en `lineas_para_registro` (R17:
  `excluidas["recalculando"]`, detrás de `reparto_pendiente`, con `joinedload`).
- `interface_adapters/web/app.py`: ruta de aprobar con `except CongeladoError` (y fuera el import
  ya sin uso de `RepartoPendienteError`); `_partes_nuevos` (sin espera, ni una consulta); `nuevos`
  en obra, trabajador y detalle; `/partes` con `motivos_espera(None)`; `_motivo_sin_lineas` (R13,
  R14, R17).
- Plantillas: `data-recalculo-motivo="nuevo"` y «procesando…» en obra, trabajador y detalle;
  `data-parte-acciones data-document-id` en la barra del detalle (R18); filas de `partes_list.html`
  con `data-document-id`, `data-fecha` y la marca en la celda de estado (R14).
- `static/app.js`: `var recalculoMotivos = {};` (una línea) y cambios dentro de
  `textoAvisoRecalculo`, `contenedoresEspera`, `ponerEnEspera`, `avisoRecalculo`,
  `aplicarEstadoRecalculo` y `esperasDeLaPagina`; ninguna función nueva (302 con nombre, como en
  dev); huella sha256 de las 11 que no cambian fijada en el test (R19–R23).

**Ambos**: comentario del bloque de seguimiento en las dos copias de `orm_models.py`
(byte-idénticas, sin columnas) (R24). **Raíz**: `tests/test_f047_contrato_parte_nuevo.py` (R24, R25).
**Docs**: `docs/ARCHITECTURE.md` (semánticas 3, 7 y 10), `docs/referencia/partes-proyecto.md`
(fila del §5 y «El parte nuevo también espera»), `azure-apps/partes.md` (commit local en ese
repositorio: nota de F-047 y fila de columnas; orden sv4 → sv3).

## Tests nuevos (todos `test_f047_rN_…`)

- sv3 `tests/test_f047_parte_nuevo_sv3.py`: 26 (R1–R10; `save_parte` real sobre SQLite con contador
  de commits; pipeline con dobles; de punta a punta con el adaptador real para R4 y R7).
- sv4 `tests/test_f047_parte_nuevo_sv4.py`: 59 (R11–R18) y `tests/test_f047_portal_parte_nuevo.py`:
  24 (R18–R23 con node). Raíz: 8 (R24–R25).
- R15 y las huellas/textos de F-043 de R22–R23 pasan sin cambio de código: son no regresión (la
  guarda 409 de F-043 va por estado). Las tres comprobaciones AST de sv3 en R25 se escribieron
  con T2/T3 ya hechas: su fase RED es la de T2/T3.

## Fuera de alcance / pendiente

- Matriz «Horas por día» (DA11), `/obras`, `/trabajadores`, `/conciliacion` (DA7), partes manuales
  de sv4, reentrega tras caída (DA9).
- La barra del detalle se deshabilita también en la espera de un recálculo de F-043 (R18 dice «la
  espera», sin motivo): el servidor sí aprobaría ese parte (DA3-B). Inocuo; lo anoto para el reviewer.
- **Mutación completa**: la lanza el líder (`python -m harness.mutacion --feature F-047 --workers 6
  --timeout 600`); el análisis de supervivientes queda por hacer.
- **MANUAL** (humano, `progress/current.md`): despliegue sv4 → sv3 en dos llamadas; M1 portal, M2 SQL
  de solo lectura, M3 Log Analytics (mide la espera real).

## Fase RED (trazas reales)

### T1 (R24) — `python -m pytest -q tests/test_f047_contrato_parte_nuevo.py` (raíz)
```
>       assert "F-047" in bloque
E       AssertionError: assert 'F-047' in '    # --- Seguimiento del recalculo (F-043) --- #\n    # sv4 escribe el «pedido» (uuid4 y hora UTC) antes de publicar...d_column(String(36))     # sv3\n ...'
FAILED tests/test_f047_contrato_parte_nuevo.py::test_f047_r24_el_comentario_cuenta_el_pedido_de_sv3
1 failed, 3 passed in 2.74s
```

### T2 (R1, R2, R8, R9) — `python -m pytest -q tests/test_f047_parte_nuevo_sv3.py -k "save_parte"` (sv3)
```
E       TypeError: SqlAlchemyParteRepository.save_parte() got an unexpected keyword argument 'recalculo_pedido_id'   (x3)
E           KeyError: 'recalculo_pedido_id'
FAILED ...::test_f047_r1_save_parte_escribe_el_pedido_en_el_mismo_commit
FAILED ...::test_f047_r2_save_parte_con_pedido_none_igual_que_sin_el
FAILED ...::test_f047_r8_save_parte_reemplazo_solo_marca_el_nuevo
FAILED ...::test_f047_r9_save_parte_parametro_opcional_en_el_puerto
4 failed, 1 passed in 2.32s
```

### T3 (R1-R7, pipeline) — `python -m pytest -q tests/test_f047_parte_nuevo_sv3.py` (sv3)
```
E       TypeError: PersistPartePipeline.__init__() got an unexpected keyword argument 'recalculo_seguimiento'   (x17)
FAILED ...::test_f047_r1_el_pipeline_pasa_el_id_del_documento_como_pedido
FAILED ...::test_f047_r2_sin_conciliador_o_sin_seguimiento_no_hay_pedido[recurso|seguimiento|los_dos]
FAILED ...::test_f047_r3_sha256_repetido_ni_guarda_ni_concilia_ni_marca
FAILED ...::test_f047_r4_orden_guardar_partidas_recurso_marcar
FAILED ...::test_f047_r5_si_la_conciliacion_de_recurso_lanza_no_se_marca[runtime|timeout_candado]
FAILED ...::test_f047_r6_info_al_marcar[True|False]
FAILED ...::test_f047_r6_si_marcar_lanza_warning_sin_propagar
FAILED ...::test_f047_r7_un_pedido_de_sv4_durante_la_pasada_no_se_toca
17 failed, 5 passed in 3.27s
```

### T4 (R10) — `python -m pytest -q tests/test_f047_parte_nuevo_sv3.py -k r10` (sv3)
```
E       assert None is <infrastructure.database.recalculo_seguimiento.SqlAlchemyRecalculoSeguimiento object at 0x00000153282E1640>
E        +  where None = <application.pipelines.persist_parte_pipeline.PersistPartePipeline object at 0x000001532800EBD0>._recalculo_seguimiento
1 failed, 25 deselected in 2.43s
```

### T5 (R11, R12, R25) — raíz `python -m pytest -q tests/test_f047_contrato_parte_nuevo.py` y sv4 `python -m pytest -q tests/test_f047_parte_nuevo_sv4.py -k "r11 or r12"`
```
E       AssertionError: no se define motivo_espera
FAILED tests/test_f047_contrato_parte_nuevo.py::test_f047_r25_motivo_espera_de_sv4_compara_con_el_id
1 failed, 7 passed in 2.60s
---
E   ImportError: cannot import name 'MOTIVO_NUEVO' from 'application.services.seguimiento_recalculo'
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 1.32s
```
(Las tres comprobaciones R25 de sv3 se escribieron en T5, con T2/T3 ya hechas: pasan desde el
primer momento; su fase RED es la de T2/T3, que prueban el mismo comportamiento.)

### T6 (R15-R17) — sv4 `python -m pytest -q tests/test_f047_parte_nuevo_sv4.py`
Primero `ImportError: cannot import name 'EXCLUIDA_RECALCULANDO'`; con solo las dos constantes:
```
E       Failed: DID NOT RAISE RecalculandoError                                   (R16 repositorio x2)
E       AssertionError: assert 'El parte se está recalculando (extras): espera a que termine.' in '/partes/doc-f004?message=Parte aprobado'   (R16 ruta x2)
E       AssertionError: assert {'registrado'...do_sigrid': 0} == {'registrado'...alculando': 2}   (R17 x2)
E       AssertionError: assert [] == [['doc-f004', 'doc-otro']]                    (R17 una consulta)
E       assert 200 == 422                                                          (R17 preflight/ejecutar/encolar)
E       KeyError: 'error'                                                          (R17 motivo combinado)
11 failed, 39 passed, 1 warning in 21.33s
```
R15 (409 en las ediciones, fecha y deshacer permitidos) pasa sin tocar código: la guarda de F-043
va por estado (design §4, «no cambian»). Su fase RED no aplica; queda como test de no regresión.

### T6 tras el desbloqueo (DA3-B: solo el motivo `nuevo`) — sv4 `python -m pytest -q -p no:cacheprovider tests/test_f047_parte_nuevo_sv4.py`
```
E           application.services.seguimiento_recalculo.RecalculandoError: El parte se está recalculando (extras): espera a que termine.
E       AssertionError: assert 'Parte aprobado' in '/partes?message=El parte se está recalculando (extras): espera a que termine.'
E       AssertionError: assert {'registrado'...alculando': 1} == {'registrado'...do_sigrid': 0}
FAILED ...::test_f047_r16_fuera_de_espera_se_aprueba_como_siempre[recalculo_en_espera]
FAILED ...::test_f047_r16_la_ruta_aprueba_fuera_de_espera[recalculo_en_espera]
FAILED ...::test_f047_r17_sin_espera_las_claves_no_cambian[recalculo_en_espera]
3 failed, 48 passed, 1 warning in 8.92s
```

### T7 (R13, R14, R18) — sv4 `python -m pytest -q -p no:cacheprovider tests/test_f047_parte_nuevo_sv4.py -k "r13 or r14 or r18"`
```
E       assert 'data-recalculo-motivo="nuevo"' in '<tr data-registro-id="1" data-document-id="doc-f004" ... data-recalculando="1"'   (obra y trabajador)
E           assert 'data-recalculo-motivo="nuevo"' in '<div class="info-grid" data-parte-contenido data-document-id="doc-f004" data-recalculando="1">'
E       assert 'data-parte-acciones' in '<div class="action-bar">'           (x2)
E       ValueError: substring not found                                        (listado sin data-document-id, x2)
E       AssertionError: assert [] == [['doc-f004',...-f004'], None]
8 failed, 51 deselected, 1 warning in 5.69s
```

### T8 (R18-R23, node) — sv4 `python -m pytest -q -p no:cacheprovider tests/test_f047_portal_parte_nuevo.py`
```
E       AssertionError: assert ['recalculando…'] == ['procesando…']                       (R19)
E       assert [False, True] == [True, True]                                            (R18 barra)
E       AssertionError: assert ['recalculado...a Actualizar'] == ['procesado ·...a Actualizar']   (R20)
E       ... 'No se ha podido confirmar el recálculo de extras del parte del 01/10/2026. ...' != '... el reparto de horas del parte nuevo del 01/10/2026. ...'   (R21)
E       ... 'Recalculando extras del parte del 01/10/2026 (suele tardar 1–2 min). ...' != 'Procesando el parte nuevo del 01/10/2026: ...'   (R19 textos)
E       Right contains one more item: '  var recalculoMotivos = {};          // document_id -> motivo (F-047)'
E         ReferenceError: recalculoMotivos is not defined
7 failed, 17 passed in 13.71s
```
(R22 y las huellas de R23 pasan antes y después: fijan que lo de F-043 no cambia.)

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests F-047 | sv3 26 passed (3.90 s); sv4 83 passed (22.79 s); raíz 8 passed (1.80 s) |
| Suites en `bash harness/init.sh` | raíz 537 passed, 3 skipped (73.92 s); sv3 2371 passed (31.48 s); sv4 3307 passed, 1 skipped (699.15 s); sv1, sv2, sv5 en verde (caché) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 68 líneas cambiadas cubiertas (68/68, umbral 80%, nivel critico)` |
| Mutantes generados / supervivientes | PENDIENTE: la campaña completa la lanza el líder (`progress/mutacion_F-047.md`) |
| `bash harness/init.sh` | `ENTORNO LISTO. Puedes trabajar.` (2026-10-31). Avisos previos: ruff 904 (deuda), F-032 `blocked`, infra sin tests |

Nota: la primera ejecución de `init.sh` (2026-10-30, al arrancar) corrió mientras ya editaba T1–T5 y
dio `PUERTA COBERTURA 77.2 %` sobre el código a medias; la de cierre, arriba, es la válida. Por error
la de cierre se lanzó con la salida redirigida a un fichero (no tal cual, como pide `CLAUDE.md`).
