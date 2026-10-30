<!-- progress/impl_F-047.md -->
# F-047 · Informe del implementer — PARCIAL (bloqueada en T6, 2026-10-30)

Rama `feature/F-047-parte-nuevo-en-espera`, worktree `partes-wt-f047`. Rigor **crítico**.
Estado y opciones del bloqueo: `progress/current.md` (bloque «F-047 · BLOQUEADA en T6»).
Este informe se completará al cerrar (Evidencias, cobertura, mutación).

## Hecho

- Paso previo: DA11–DA13 = A en `design.md` §11 (literal «ok», 2026-10-30), DA13 aplicada a R19,
  F-047 `in_progress` (commit 37b96d6). Tamaños: requirements 150/150, design 250/250.
- **T1** (657dab3): comentario del bloque «Seguimiento del recalculo» en las dos copias de
  `orm_models.py` (byte-idénticas; `# sv4 / sv3 (F-047)` en las columnas del pedido) y
  `tests/test_f047_contrato_parte_nuevo.py` (R24).
- **T2** (521d93d): `save_parte(..., recalculo_pedido_id=None)` en el puerto y en el repositorio de
  sv3; con pedido, `recalculo_pedido_at_utc` = `now_iso` (= `created_at_utc`), mismo commit.
- **T3** (bd2ee7a): `PersistPartePipeline(recalculo_seguimiento=…)`; `seguido` = conciliador de
  recurso y seguimiento cableados; `_conciliar_*_safely` devuelven `bool`; `_marcar_parte_nuevo`
  con el INFO/WARNING de R6. Docstring del módulo (paso 7).
- **T4** (f98ddc8): `build_app` crea UN `SqlAlchemyRecalculoSeguimiento` y lo pasa al pipeline y a
  `app.state`; docstring del módulo del adaptador. Suite sv3 completa: **2371 passed in 12.29s**.
- **T5** (86f7f5d): sv4 `MOTIVO_NUEVO`, `MOTIVO_RECALCULO`, `motivo_espera`; repositorio
  `motivos_espera(ids | None)` (una consulta; con None, filtrada en la base); contrato R25 por AST.
- **T6 (sin commitear, bloqueada)**: ver `progress/current.md`.

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
