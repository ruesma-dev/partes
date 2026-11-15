<!-- progress/impl_F-068.md -->
# F-068 · Informe del implementer (rigor `critico`)

Rama `feature/F-068-conciliar-pide-recalculo` (worktree `partes-wt-f068`, base 04afcfa).
Decisiones aplicadas: D1-a, D2-a, D3-b (T10 entra), D4-b (T11 entra), D5-b (F-073 ya dada de
alta, sin tocar), D6-a. Solo sv4, más `tests/test_f042_contrato_recalculo.py`,
`docs/ARCHITECTURE.md` y `azure-apps/partes.md`. F-057 no está en `dev` (solo su alta en el
backlog, ab48b48): no hay conflicto de fusión que anotar todavía.

## Commits (uno por tarea; RED y verde separados en T10 y T11)

T1 9ee6e3d · T2 27c7b41 · T3 1262357 · T4 487469f · T5 362de68 · T6 432f360 · T7 6b78b72 ·
T8 525274a · T9 a75eba5 · T10 2c80903 (RED) + b67f82c · T11 20003bd (RED) + 67e91d6 ·
T12 sin commit (verificación) · T13 f2e58d0 + `azure-apps` ef721cd. Enmiendas del humano:
6b1b3e8 (F-017) y 5eeeb33 (F-047). Review ciclo 1: 827e111, 3676be9, d83f12f.

## Qué cambió (producción)

- `infrastructure/persistencia/recalculo_publisher.py`: `MOTIVO_CASADO_CONCILIACION`,
  `MOTIVO_REASIGNACION`, `MOTIVO_DESHACER_TRABAJADOR` (solo stdlib, como exige el test raíz).
- `infrastructure/database/parte_repository.py`:
  - `_documentos_de(regs)`: `document_id` ordenados por `id` de línea, sin repetir ni vacíos.
  - `backfill_empleado` y las tres `reassign_empleado_by_*`: parámetro opcional
    `documentos: list[str] | None = None`; los partes se calculan antes del commit y se
    añaden (`extend`) al colector **después** del commit. El retorno no cambia (R22).
  - `undo_last`: guarda las líneas cuyo snapshot se **aplicó**; si `action == "empleado"`,
    `document_ids = _documentos_de(restauradas)` (las omitidas por congelación no cuentan).
    Las demás acciones, igual.
- `interface_adapters/web/app.py`:
  - `_recalculo_de_trabajador(documentos, motivo, actor, *, etiqueta, updated, congeladas)`:
    sin partes ⇒ `{recalculo: None, partes_recalculo: 0}` sin marcar ni publicar; con partes ⇒
    `_pedir_recalculo_compartido` (sin tocarla) + INFO
    `[<etiqueta>] casado updated=… congeladas=… documentos=[…] pedido=… recalculo=…`.
  - `conciliacion_confirmar`: colector en `backfill_empleado`; el pedido va **después** del
    alias; respuesta + `recalculo` y `partes_recalculo`.
  - `empleado_reasignar`: colector en las cuatro formas, motivo `reasignacion_trabajador`,
    etiqueta `reasignar`.
  - `undo_apply`: rama `empleado` con `document_ids` ⇒ recálculo compartido
    `deshacer_trabajador`; pone `recalculo` en la respuesta.
- `static/app.js`: `textoRecalculoCasado(recalculo, partes) -> [texto, clase] | null`;
  `_confirmarCasado` añade «· recalculando extras de N parte(s) (1–2 min)» o «(sin recálculo
  automático)» tras el recuento, y con `fallo` un `<div class="recon-status error">` fijo con el
  texto de R15; `_empReasignar` hace `alert` con ese texto antes del `reload` si `fallo`.

No se tocan: sv1, sv2, sv3, sv5, `infra/`, `orm_models.py`, `congelacion.py`,
`esta_congelado`, gemelos, `_pedir_recalculo_compartido`, `_pedir_recalculo_seguido`,
`marcar_/anular_recalculo_pedido*`, `_exigir_sin_recalculo`, `approve_document`,
`lineas_para_registro`, `_validar_ambito`. `git diff dev --stat` lo confirma (solo los
ficheros de arriba, specs, progress, BACKLOG y features.json).

## Decisiones de diseño (dentro de la spec)

1. **Los partes se calculan antes del commit y se añaden al colector después.** El design dice
   «tras el commit se le añaden»: se respeta lo observable (el colector solo crece si el commit
   tuvo éxito), pero leer `id`/`document_id` de ORM antes del commit evita depender de
   `expire_on_commit=False`.
2. **La clase de `pedido`/`sin_cola` es `recon-recalculo`** (sin CSS nuevo: hereda el estilo
   de `recon-meta`). El design no la fijaba.
3. **Dobles de sv4** (design §10): ningún doble existente implementa `backfill_empleado` ni
   `reassign_empleado_by_*`; los dos que sustituyen `undo_last` (F-042, F-043) devuelven
   dicts sin `action == "empleado"`, así que no hubo que tocarlos.
4. **Tests de reasignar (R18) en `test_f068_conciliar_js.py`** junto a R14-R16: ejecutan
   `_empReasignar` real en node con `fetch`, `alert` y `location.reload` falsos y comprueban el
   orden `alert` → `reload`.

Desviaciones respecto a la spec: ninguna desde el ciclo 1 de review. Hasta entonces
`partes_recalculo` contaba los partes también con `fallo`/`sin_cola`, contra R3 («0 si no hubo
pedido»); el humano eligió alinear el código (opción a, 2026-11-15) y R3 no se enmienda.

## Review ciclo 1 (CHANGES_REQUESTED, `progress/review_F-068.md`)

- **RM7 · R17** (827e111): `test_f068_r17_el_mensaje_sale_tras_la_reasignacion_y_los_alias`
  (formas `nombre_leido` y `worker_key`, `cola.al_enviar`). Mutación a mano en `app.py`
  (calcular `_recalculo_de_trabajador` antes del bucle de alias de `empleado_reasignar`),
  `python -m pytest tests/test_f068_conciliar_recalculo.py -k tras_la_reasignacion -q`:
  ```
  E       assert (4242 == 4242 and None == 4242)
  FAILED ...::test_f068_r17_el_mensaje_sale_tras_la_reasignacion_y_los_alias[nombre_leido]
  FAILED ...::test_f068_r17_el_mensaje_sale_tras_la_reasignacion_y_los_alias[worker_key]
  2 failed, 41 deselected, 1 warning in 3.97s
  ```
  Revertido con `git checkout --` (diff vacío) ⇒ `2 passed`.
- **Cambio 2 · R3, opción (a)** (3676be9 RED, d83f12f verde): `partes_recalculo` = 0 si
  `recalculo` ≠ `pedido`. RED, `-k "e5 or e6 or cola_caida or sin_cola_partes"`:
  ```
  E       AssertionError: assert ('fallo', 1) == ('fallo', 0)
  E       AssertionError: assert ('sin_cola', 1) == ('sin_cola', 0)
  4 failed, 1 passed, 39 deselected, 1 warning in 4.37s
  ```
  `app.js` solo usa N con `pedido` (`textoRecalculoCasado`); los dobles de los tests de JS con
  `fallo`/`sin_cola` pasan a N = 0. Deshacer no devuelve `partes_recalculo` (R19): sin cambio.
- **T16** marcada tras `init.sh` en verde (abajo).

## Fase RED (salida real; recortada a las líneas `E`/`FAILED`/resumen)

**T1** `python -m pytest tests/test_f042_contrato_recalculo.py -q` (raíz) y
`python -m pytest tests/test_f068_conciliar_recalculo.py -q` (sv4):
```
FAILED tests/test_f042_contrato_recalculo.py::test_f042_r22_sv3_clasifica_como_recalculo_lo_de_sv4[revisora@ejemplo.es-MOTIVO_CASADO_CONCILIACION]
... (6 de clasifica + 3 de lo_que_publica)
9 failed, 11 passed in 0.69s
E       AttributeError: module 'f042_contrato_sv4_recalculo_publisher' has no attribute 'MOTIVO_CASADO_CONCILIACION'
E   ImportError: cannot import name 'MOTIVO_CASADO_CONCILIACION' from 'infrastructure.persistencia.recalculo_publisher'
```
**T3** `python -m pytest tests/test_f068_repositorio.py -q`:
```
9 failed, 1 passed in 3.52s
E       AttributeError: module 'infrastructure.database.parte_repository' has no attribute '_documentos_de'
E       TypeError: ParteReviewRepository.backfill_empleado() got an unexpected keyword argument 'documentos'
FAILED tests/test_f068_repositorio.py::test_f068_e3_r4_parte_con_libres_y_congeladas_recibe_el_pedido
```
(el que pasa es `test_f068_r22_backfill_sin_colector_igual_que_hoy`: caracteriza R22).

**T5** `python -m pytest tests/test_f068_conciliar_recalculo.py -k conciliar -q`:
```
14 failed, 5 passed, 1 warning in 17.70s
E       AssertionError: assert {'alias_ok', ...k', 'updated'} == {'alias_ok', ...calculo', ...}
E       KeyError: 'recalculo'
E       ValueError: not enough values to unpack (expected 1, got 0)
FAILED ...::test_f068_conciliar_e1_r1_un_parte_un_recalculo
FAILED ...::test_f068_conciliar_r8_info_sin_nombres
```
(pasan los de R7 ×3, `r8_sin_pedido_no_hay_info` y la constante, que ya existía por T2).

**T7**: caracterización. `-k "r9 or r12 or r13"` ⇒ `6 passed` a la primera **sin código nuevo**
después de T6: la espera y el 409 son de F-043, el 422 es el de F-069.

**T8** `python -m pytest tests/test_f068_conciliar_js.py -q`:
```
10 failed in 0.73s
E       AssertionError: app.js no define textoRecalculoCasado
```
**T10** `python -m pytest tests/test_f068_repositorio.py tests/test_f068_conciliar_recalculo.py tests/test_f068_conciliar_js.py -k "r17 or r18 or r22" -q`:
```
16 failed, 7 passed, 44 deselected, 1 warning in 15.39s
E       TypeError: ParteReviewRepository.reassign_empleado_by_leido() got an unexpected keyword argument 'documentos'
E       KeyError: 'recalculo'
E       AssertionError: assert [['reload']] == [['alert', 'C...], ['reload']]
FAILED ...::test_f068_r18_reasignar_con_fallo_avisa_antes_de_recargar
```
**T11** `python -m pytest tests/test_f068_repositorio.py tests/test_f068_conciliar_recalculo.py -k r19 -q`:
```
6 failed, 3 passed, 52 deselected, 1 warning in 12.18s
E       AssertionError: assert [] == ['d-2', 'd-1']
E       KeyError: 'recalculo'
FAILED ...::test_f068_r19_deshacer_casado_pide_un_recalculo
```
(pasan los que caracterizan lo de hoy: otras acciones, todo congelado ⇒ nada).

## Verificación (resultados reales)

- T4: `test_f068_repositorio.py` + `test_f004_endpoints_congelados.py`,
  `test_f023_catalogo_empresa.py`, `test_f030_portal_recurso.py`, `test_f035_repositorio.py`
  ⇒ **170 passed**.
- T6: `test_f068_conciliar_recalculo.py`, `test_f035_endpoints.py`, `test_f040_alias.py`,
  `test_f004_endpoints_congelados.py` ⇒ **134 passed**.
- T9/T10: `node --check services/partes-front/static/app.js` OK; los tres `test_f068_*` ⇒
  **67 passed**; `test_f035_*.py` + `test_f004_endpoints_congelados.py` ⇒ **169 passed**.
- T11: `test_f068_*` (repo y ruta), `test_f042_recalculo_fecha.py`,
  `test_f043_alcance_y_seguimiento.py`, `test_f049_guardar_celda.py` ⇒ **287 passed**.
- T12: gemelos (`test_f010_orm_models_gemelos`, `test_f024_borrado_no_congela_gemelos`,
  `test_f023_de_alta_gemelos`, `test_f036_recurso_persona_gemelos`,
  `test_f015_r19_jornada_resolver_gemelo`) + contrato raíz ⇒ **134 passed**; suite completa de
  sv4 dentro de `init.sh` (abajo).
- T13: `grep -n "F-068" docs/ARCHITECTURE.md` ⇒ l. 34, 212, 255. `azure-apps`: `git pull`
  antes de editar; commit **ef721cd** en `main` (`partes.md`, 13+/1−). Sin push desde aquí.

### `bash harness/init.sh`
**VERDE** (2026-11-15, HEAD ba9a123: enmiendas F-017 6b1b3e8 y F-047 5eeeb33 y review
ciclo 1), salida real:
```
2457 passed, 50 skipped in 938.48s (0:15:38)          [OK] pytest en verde (con medición de cobertura)
[OK] sv1-email, sv2-extraccion, sv3-persistencia, sv5-transfer: pytest en verde (caché)
3830 passed, 1 skipped, 2 warnings in 733.66s (0:12:13)   [OK] servicio sv4-front: pytest en verde
[OK] PUERTA COBERTURA: 100.0% de 38 líneas cambiadas cubiertas (38/38, umbral 90% (del nivel critico)
[OK] PUERTA TAMAÑO: requirements 128/150, design 190/250, impl 220/220, review 140/140
[OK] PUERTA CARRIL: N/A (nivel critico)      [OK] CAPA E2E: N/A (ningún servicio declara el bloque e2e)
```
Los dos únicos tests existentes que cambian de expectativa son esos guardianes, cada uno con su
enmienda expresa del humano (R21 y design §5 y §7 lo dicen).

## Trazabilidad requisito → test (sv4 salvo indicación)

| R | Tests |
|---|---|
| R1, E1, E2 | `test_f068_conciliar_e1_*`, `_e2_*`, `_r1_el_mensaje_sale_tras_el_casado_y_el_alias` |
| R2, E4 | `test_f068_conciliar_e4_r2_*` (×2) |
| R3 | `test_f068_conciliar_r3_*` |
| R4, E3 | `test_f068_e3_r4_*`, `test_f068_e4_r4_*` (repo), `test_f068_conciliar_e3_r4_*` |
| R3, R5, E5 / E6 | `test_f068_conciliar_e5_r5_cola_caida`, `_e6_sin_cola` (N = 0) |
| R6 | `test_f068_conciliar_r6_marcar_lanza`, `_r6_anular_lanza` |
| R7 | `test_f068_conciliar_r7_*` (×4) |
| R8 | `test_f068_conciliar_r8_*` (×2), `test_f068_r17_reasignar_info_sin_nombres` |
| R9 | `test_f068_r9_*` (×3, caracterización) |
| R10 | `test_f068_conciliar_r10_*` |
| R11-R13, E7 | `test_f068_e7_r12_r13_*` (×3 endpoints de aprobar) |
| R14-R16 | `test_f068_conciliar_js.py` (`r14`, `r15`, `r16`) |
| R17 | `test_f068_r17_*` (repo ×4, ruta ×15, con el orden tras los alias) |
| R18 | `test_f068_r18_*` (JS ×5) |
| R19 | `test_f068_r19_*` (repo ×5, ruta ×4) |
| R20 | `test_f068_r20_constantes_de_motivo`; raíz `test_f042_contrato_recalculo.py` (+9 casos) |
| R21 | gemelos (T12) y `git diff dev --stat` |
| R22 | `test_f068_r22_*` (×2) + suites de F-004, F-023, F-030, F-035 sin cambios |

## Pendiente

- **T14 (mutación)**: en la pasada de campaña, tras el APPROVED (sobre el HEAD con los cambios
  del ciclo 1) ⇒ `progress/mutacion_F-068.md`.
- **T15 · M1 (MANUAL, humano, tras desplegar sv4)**: pasos de M1 en `requirements.md`.
- Fuera de alcance (D5-b): bloquear aprobar durante la pasada ⇒ F-073.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests nuevos | 79 en sv4 (`test_f068_repositorio.py` 20, `test_f068_conciliar_recalculo.py` 44, `test_f068_conciliar_js.py` 15) + 9 casos en el contrato raíz |
| Suite (init.sh) | raíz 2457 passed / 50 skipped en 938,48 s; sv4 3830 passed / 1 skipped en 733,66 s |
| Cobertura de líneas cambiadas | 100 % (38/38), re-medida tras el review ciclo 1 (umbral 90 %) |
| Mutantes generados / supervivientes | pendiente de la pasada de campaña (T14), como manda el protocolo |
| Capa e2e | `CAPA E2E: N/A (ningún servicio declara el bloque e2e)` |
