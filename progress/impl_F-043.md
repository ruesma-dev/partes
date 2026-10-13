<!-- progress/impl_F-043.md -->
# F-043 · Informe del implementer (BORRADOR: feature BLOCKED en T8)

Rama `feature/F-043-fecha-del-parte-confirmar-y-recargar`, worktree `partes-wt-f043`.
Rigor **crítico**. **T1–T7 hechas** (commits `641c8cb`..`c5ca97f`); **T8 bloqueada**:
`wireFechaInput` según R5/R18/R24 rompe el test existente
`services/partes-front/tests/test_f042_recalculo_fecha.py::test_f042_r11_tras_guardar_pinta_el_estado_del_recalculo`,
que design §7 y el `acceptance` prohíben tocar. Motivo y opciones A/B/C en
`progress/current.md`. Este borrador guarda las trazas RED reales de T1–T7 para
que no se pierdan; el informe completo (Evidencias, mutación) se escribe al cerrar.

## Hecho hasta ahora

- **T1** `orm_models.py` (sv3 y sv4, byte-idénticos): 4 columnas nullables en
  `parte_documents`. Test raíz `tests/test_f043_contrato_seguimiento.py` (R34, R35, R16).
- **T2** sv3 `infrastructure/database/recalculo_seguimiento.py`
  (`pedido_actual`, `marcar_terminado` con UPDATE condicional).
- **T3** sv3 `despacho.py` (`recalculo_seguimiento`), `api/app.py`
  (`app.state.recalculo_seguimiento`), `main_worker.py` (lo pasa con
  `getattr(..., None)`: ver «Decisión T3» en `current.md`).
- **T4** sv4 `application/services/seguimiento_recalculo.py`; repositorio:
  `_ahora_utc`, `alcance_parte`, `estados_recalculo`, `documentos_en_espera`;
  `GET /api/partes/{id}/alcance` y `GET /api/recalculo` (1–50 ids, 422).
- **T5** `marcar_recalculo_pedido`, `anular_recalculo_pedido` y la closure
  `_pedir_recalculo_seguido` en `patch_parte_fecha` y `undo_apply`
  (`_actor(request)` sigue en 17).
- **T6** `_exigir_sin_recalculo` tras las 7 guardas de F-004 (no en
  `update_parte_fecha`; deshacer libre). `delete_document` responde con la
  redirección con motivo de F-004 R7 (su `except CongeladoError` ya existente).
- **T7** rótulo «Fecha del parte» (R1) y `data-recalculando` /
  `data-parte-contenido` (R37; en `parte_detail.html`, dos contenedores:
  cabecera `.info-grid` y panel «Personal», sin el visor del PDF).

`bash harness/init.sh` (2026-10-13, tras T7 y el blocked): ENTORNO LISTO, sv4
**2013 passed, 1 skipped** (456 s), `PUERTA COBERTURA: 99.4% de 161 líneas
cambiadas`, `PUERTA TAMAÑO` dentro.

## Fase RED (trazas reales, T1–T7)

```
T1 R34 (raiz: python -m pytest -q tests/test_f043_contrato_seguimiento.py):
E           AssertionError: recalculo_pedido_id
E           assert 'ALTER TABLE parte_documents ADD COLUMN IF NOT EXISTS recalculo_pedido_id VARCHAR(36)' in ("ALTER TABLE dedicacion_bandeja ...", ...)
FAILED ...::test_f043_r34_parte_documents_tiene_la_columna[sv3-recalculo_pedido_id-36]  (x4 sv3, x4 sv4)
FAILED ...::test_f043_r34_ddl_complementario_las_anade[sv3] / [sv4]
10 failed, 2 passed in 1.75s

T2 R27/R28/R32 adaptador (cd services/partes-persistencia && python -m pytest -q tests/test_f043_seguimiento_sv3.py -k adaptador):
tests\test_f043_seguimiento_sv3.py:23: in <module>
    from infrastructure.database.recalculo_seguimiento import (
E   ModuleNotFoundError: No module named 'infrastructure.database.recalculo_seguimiento'
ERROR tests/test_f043_seguimiento_sv3.py
1 error in 2.98s

T3 R27-R33 handler (cd services/partes-persistencia && python -m pytest -q tests/test_f043_seguimiento_sv3.py), errores agrupados (grep ^E | sort | uniq -c):
     15 E       TypeError: construir_handler() got an unexpected keyword argument 'recalculo_seguimiento'
      1 E           AttributeError: 'State' object has no attribute 'recalculo_seguimiento'
      1 E       AssertionError: assert 'recalculo_seguimiento' in {'blob': 'blob', 'pipeline': 'app.state.pipeline', 'recurso_conciliador': 'app.state.recurso_conciliador', 'contenedor_input': 'CONTENEDOR_INPUT', ...}
      1 E       KeyError: 'recalculo_seguimiento'
18 failed, 11 passed in 8.03s   (pasan los 10 del adaptador y test_f043_r31_sin_seguimiento_por_defecto_es_f042, caracterizacion de F-042)

T4 (cd services/partes-front && python -m pytest -q tests/test_f043_alcance_y_seguimiento.py), 1.a pasada, sin modulo:
E   ImportError: cannot import name 'seguimiento_recalculo' from 'application.services' (unknown location)
ERROR tests/test_f043_alcance_y_seguimiento.py  (1 error during collection)
2.a pasada, con seguimiento_recalculo.py y _ahora_utc pero sin repositorio ni endpoints (grep ^E | sort | uniq -c):
     10 E        +  where 404 = <Response [404 Not Found]>.status_code
      6 E       assert 404 == 200
      5 E       AttributeError: 'ParteReviewRepository' object has no attribute 'alcance_parte'
      4 E       assert 404 == 422
      3 E       AttributeError: 'ParteReviewRepository' object has no attribute 'estados_recalculo'
      2 E       AttributeError: 'ParteReviewRepository' object has no attribute 'documentos_en_espera'
20 failed, 33 passed, 1 warning in 9.07s

T5 R12-R16 (cd services/partes-front && python -m pytest -q tests/test_f043_alcance_y_seguimiento.py), sin marca ni closure:
E       TypeError: expected string or bytes-like object, got 'NoneType'      (x3: UUID4.match(None), no hay pedido)
E       AttributeError: 'ParteReviewRepository' object has no attribute 'marcar_recalculo_pedido'   (x2)
E       AttributeError: 'ParteReviewRepository' object has no attribute 'anular_recalculo_pedido'
E       assert (1 == 1 and None is not None)          (la cola no ve marca al publicar)
E       AssertionError: assert '...00a' != '...00a'    (un pedido nuevo no sustituye al terminado)
E       assert 0 == 1  /  where 0 = len([])            (ningun WARNING [recalculo] de marcar/anular)
E       AssertionError: assert 1 == 2                 (solo el WARNING de publicar de F-042)
FAILED ...::test_f043_r12_guardar_la_fecha_marca_el_pedido
FAILED ...::test_f043_r12_la_marca_esta_confirmada_antes_de_publicar
FAILED ...::test_f043_r12_cada_peticion_es_un_pedido_nuevo
FAILED ...::test_f043_r12_un_pedido_nuevo_deja_en_espera_un_parte_terminado
FAILED ...::test_f043_r12_deshacer_la_fecha_marca_otro_pedido
FAILED ...::test_f043_r12_marcar_en_el_repositorio
FAILED ...::test_f043_r12_marcar_no_mira_la_congelacion
FAILED ...::test_f043_r13_anular_solo_si_sigue_siendo_suya
FAILED ...::test_f043_r14_si_marcar_lanza_avisa_y_sigue_como_f042
FAILED ...::test_f043_r14_si_marcar_lanza_y_publicar_falla_no_se_anula
FAILED ...::test_f043_r14_si_anular_lanza_avisa
11 failed, 60 passed, 1 warning in 15.30s
(pasan ya: R13 «si publicar falla no queda marca» y R15 «sin cola no marca» son caracterizacion: hoy no se marca nunca)

T6 R38-R39 (cd services/partes-front && python -m pytest -q tests/test_f043_guarda_espera.py), sin guarda (grep ^E | sort | uniq -c):
      7 E       assert 200 == 409
      7 E       Failed: DID NOT RAISE RecalculandoError
      1 E       AssertionError: {"ok":true,"registro_id":1,"hora_ide":2,"hora_codigo":"HE01",...,"tipo_hora":"extra"}
      1 E       AssertionError: {"ok":true,"obra_ide":null,"obra_codigo":"0999","obra_nombre":"Otra",...}
      1 E       AssertionError: assert 'El parte se está recalculando (extras): espera a que termine.' in '/partes?message=Parte movido a la papelera'
FAILED ...::test_f043_r38_en_espera_cada_edicion_da_409_y_no_escribe[...]  (x6)
FAILED ...::test_f043_r38_en_espera_mandar_el_parte_a_la_papelera_avisa
FAILED ...::test_f043_r38_otro_parte_se_edita_mientras_uno_espera
FAILED ...::test_f043_r38_el_parte_vuelve_a_editarse_al_vencer
FAILED ...::test_f043_r38_las_siete_guardas_del_repositorio[...]  (x7)
16 failed, 32 passed, 1 warning in 14.44s   (pasan las de R39 y fecha/deshacer: caracterizacion)

T7 R1/R37 (cd services/partes-front && python -m pytest -q tests/test_f043_portal_fecha.py tests/test_f043_alcance_y_seguimiento.py -k "r1 or r37"):
E       assert '<th title="Es la fecha del PARTE: cambiarla mueve todas sus líneas y trabajadores">Fecha del parte</th>' in '{% extends "base.html" %}...'   (x2)
E           assert 'title="Es la fecha del PARTE: ..."' in '<input type="date" class="fecha-edit cell-edit"\n data-document-id="{{ r.document_id }}" ...>'   (x3)
E       assert 'data-recalculando="1"' in '<tr data-registro-id="1" data-document-id="doc-f004" data-obra-ide="10" data-fecha="2026-03-02" ...'   (x2)
E       assert 0 == 2   /  where 0 = len([])     (no hay [data-parte-contenido] en el detalle)   (x2)
E       AssertionError: assert [] == [['doc-f004',... ['doc-f004']]   (ninguna vista pregunta por la espera)
10 failed, 38 passed, 38 deselected, 1 warning in 8.19s
```
