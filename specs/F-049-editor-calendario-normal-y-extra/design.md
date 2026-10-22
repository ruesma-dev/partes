# F-049 · Editor de celda de la matriz: ordinarias y extra siempre — Diseño

## 1. Servicio y límite

**sv4**: pantalla y escritura en `partes`; no reparte ni toca Sigrid: pide la pasada de sv3
(F-042) con dos motivos nuevos que sv3 solo traza. Sin lógica gemela nueva: reutiliza
`congelacion.py`, F-050 (`worker_key_for_registro`, `fila_para_alta_manual`), F-046
(`_claves_de`, `_filas_reparto`) y el patrón de F-043. Escribe `horas_orig` y `extra_auto`
(hasta hoy solo de sv3) sin cambiar su significado (DA3). **sv3** (DA13-C): solo
`SqlAlchemyRecalculoSeguimiento.marcar_terminado`, porque marcar «terminado» es de sv3 desde
F-043 (solo sv3 sabe cuándo acaba la pasada) y la pasada ya es completa (§8): basta con que la
marca llegue a todo documento con el pedido. Sin lógica duplicada: sv4 pide, sv3 marca.

## 2. Hoy, lo fusionado (dev `ff2ed8e` + F-050) y orden

**Hoy**: cada `ObraMatrixCell` de `get_obra` (por clave de trabajador y día) lleva `regs`
(`_reg_de_celda`: `id`, `t`, `h`, `p`, `c`) en `data-regs`; el popup pinta una fila por reg,
ofrece «Extra» si hay ordinaria no congelada y guarda con `PATCH` + `/extra` en paralelo;
`crear_extra_desde` clona sin partida y no se deshace; el undo no guarda `horas_orig` ni `extra_auto`.

- **F-046**: `data-reparto` (`registros_con_reparto`), `_filas_reparto`, `_claves_de`,
  `ESTADOS_BLOQUEAN`; editar no tiene guarda de reparto y «Aplicar» da 409 si el grupo cambió
  o un parte del día está en espera (`documentos_en_espera`) ⇒ R32, R33, DA11.
- **F-048**: `horas_extra_leidas` (traza): se conserva al materializar; la nueva nace NULL.
- **F-050** (antes que F-049): `worker_key_for_registro` (`rec-` > `emp-` > `nom-` >
  `sin-trabajador`) y `fila_para_alta_manual`; una celda junta IA y alta manual (E9) y varios
  partes ⇒ celda por claves (DA2), fila de la nueva por `fila_para_alta_manual` (DA6),
  `sin-trabajador` no crea (DA12) y una clave anterior a F-050 da celda vacía ⇒ 409 (R12).
- **Orden del humano (2026-10-20)**: F-050 → **F-049** → F-014 → F-047; T1 exige F-050 en dev
  (si no, `blocked`). **F-047** (aprobada, sin implementar): F-049 no depende de ella; su pedido
  (= id del parte) y su `marcar_terminado(id, id)` siguen valiendo con R41 (R42) y amplía
  `_exigir_sin_recalculo` sin cambiar el texto. Solape con F-050 y F-047 solo textual.

## 3. Ficheros

**Crear** (tests en `services/partes-front/tests/` salvo los indicados):
- `services/partes-front/application/services/edicion_celda.py` — núcleo puro (§4).
- `test_f049_plan_celda.py` (núcleo); `test_f049_guardar_celda.py` (repositorio y rutas con
  SQLite de `tests/dobles.py`: R11–R28, R33–R35, R38, R39); `test_f049_editor_js.py` (puras
  de `app.js` en node y popup con DOM falso, patrón de `test_f042_recalculo_fecha.py`: R1–R8,
  R32, R36, R37); `tests/test_f049_contrato_motivos.py` (raíz, R30, carga por ruta).
- sv3 (`services/partes-persistencia/tests/`): `test_f049_e12_otra_obra.py` (R40, solo
  caracteriza) y `test_f049_pedido_compartido.py` (R41–R42, SQLite de `tests/dobles.py`).

**Modificar**:
- `services/partes-front/infrastructure/database/parte_repository.py` — `_reg_de_celda`
  (`a`), `_celda`, `_afectadas`, `contexto_celda`, `otras_de_celda`, `guardar_celda`,
  `_REG_UNDO_MARCAS`, `_apply_reg_snapshot`, `_record_undo` (`creadas`), `undo_last`,
  `marcar_recalculo_pedido_compartido` y `anular_recalculo_pedido_compartido` (§5).
- `services/partes-front/interface_adapters/web/app.py` — `CeldaPayload`,
  `_pedir_recalculo_compartido`, `POST /api/matriz/celda`, `GET …/otras` y undo `celda_edit`.
- `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` —
  `MOTIVO_EDICION_CELDA = "edicion_celda"` y `MOTIVO_DESHACER_CELDA = "deshacer_edicion_celda"`.
- `services/partes-front/static/app.js` (IIFE «Matriz de obra», §7) y `static/styles.css`.
- `services/partes-front/templates/obra_detail.html` — leyenda (R9), `data-obra-key` en la
  tabla y `data-wk` en cada `<tr>` de la matriz (R31).
- `services/partes-persistencia/infrastructure/database/recalculo_seguimiento.py` —
  `marcar_terminado`: el UPDATE filtra solo `recalculo_pedido_id == peticion_id` (sin
  `id == document_id`) y devuelve `rowcount >= 1`; misma firma; docstring con F-049 R41.
- **Lista cerrada de tests existentes**: (a) por `undo_last(actor=…)` (DA8), los dobles `undo_last(self)` de
  `test_f042_recalculo_fecha.py` (~l. 470) y `test_f043_alcance_y_seguimiento.py` (~l. 636) pasan a
  `undo_last(self, **_kw)`; (b) por DA13-C, `test_f043_r28_adaptador_solo_toca_su_documento` (sv3, ~l. 122
  de `test_f043_seguimiento_sv3.py`) contradice R41: se invierte y se renombra `…_marca_todo_documento_con_su_pedido`;
  (c) `test_f017_punto_unico.py`: `_actor(request)` de 17 a 18 por `POST /api/matriz/celda`, que firma
  `solicitado_por` (decisión del humano 2026-10-22, opción A, literal «a»). Nada más.
- `docs/ARCHITECTURE.md` (semánticas 3 y 10, pedido compartido) y
  `PycharmProjects/azure-apps/partes.md` (motivos, rutas; commit local en `azure-apps`).

**No se tocan**: sv5; de sv3 todo salvo `marcar_terminado` (`despacho.py`, `mensajes.py`, la
pasada, `pedido_actual`); `orm_models.py`; `congelacion.py`; `reparto_aviso.py`;
`seguimiento_recalculo.py`; `jornada_resolver.py`; de F-050 todo salvo `_reg_de_celda`;
`edit_*_id`; `PATCH /api/registros/{id}`, `/extra`, `crear_extra_desde`, `update_registro`
(DA2); `_pedir_recalculo_seguido`, `marcar_recalculo_pedido`, `anular_recalculo_pedido`;
`trabajador_detail.html` (DA1); `crear_parte_manual`; los demás tests (salvo la lista cerrada).

## 4. Núcleo puro · `application/services/edicion_celda.py`

```python
ORDINARIA, EXTRA = "n", "e"
class CeldaInvalida(ValueError):          # .status: 409 | 422, str(e) = motivo para el usuario
@dataclass(frozen=True) class LineaCelda: id: int; tipo: str; horas: float; congelada: bool;
    extra_auto: bool; con_orig: bool; clave: tuple; document_id: str
@dataclass(frozen=True) class Cambio: id: int; antes: float; horas: float
@dataclass(frozen=True) class PlanCelda: cambios: tuple[tuple[int, float], ...];
    materializar: tuple[tuple[int, float], ...]; plantilla_id: int | None;
    crear_ordinaria: float | None; crear_extra: float | None; documentos: tuple[str, ...]
def validar_horas(tipo: str, horas: object, *, nueva: bool) -> float     # R13
def plantilla(celda: Sequence[LineaCelda]) -> LineaCelda | None          # R19
def planificar_celda(celda, cambios, nueva_ordinaria, nueva_extra, *, admite_nuevas) -> PlanCelda
```

`planificar_celda` (puro, en este orden): lista no vacía e ids no repetidos (R11, 422);
rangos (R13, 422); nueva con `admite_nuevas` False (R35, 422); ids == no congeladas de `celda`
y `antes` == `horas` ± 1e-9 (R12, 409); nueva de un tipo presente (R12, 409). `cambios` = los
de valor distinto; `materializar` = no congeladas cuya clave de pareja esté en la de algún
cambio miembro (`extra_auto` o `con_orig`), con el valor del popup, sin repetir (R18);
`documentos` = los de cambios, materializadas y plantilla si se crea, sin repetir, en ese
orden. Congelación (R14), espera (R15) y reparto (R33) los comprueba **antes** el repositorio.

**Por qué materializar (DA3)**: lo escrito pasa a ser «lo del parte» para sv3: una base sin
`horas_orig` no se restaura y una extra explícita no es de la pareja (`es_miembro`, F-037).
sv3 sigue aplicando la jornada en la pasada (E5, E8): R5 lo avisa y el recálculo lo enseña.

## 5. Repositorio · `parte_repository.py`

- `_reg_de_celda`: añade `fila["a"] = 1` si `reg.extra_auto` (R10).
- `_celda(session, obra_key, worker_key, fecha_int)`: líneas no incidencia, fuera de la
  papelera, de documento activo y con ese `fecha_int` (SQL), y en Python las dos claves.
- `_afectadas(session, celda) -> list[dict]` (R38): líneas activas no incidencia de
  `_claves_de(celda)` (mismo filtro que `registros_con_reparto`) que no están en la celda,
  agrupadas por documento: `{obra_key, obra_codigo, document_id, congelada}` (`congelada` si
  alguna tiene `_motivo_congelado_reg`). Sin `recurso_ide` en la celda, `[]`.
- `contexto_celda(...)` → `{plantilla_id, reside, categoria}` o None; `otras_de_celda(...)`
  → `_afectadas` sin escribir (R36, R38).
- `guardar_celda(*, obra_key, worker_key, fecha_iso, cambios, nueva_ordinaria, nueva_extra,
  hora_ordinaria, hora_extra, plantilla_esperada, by) -> dict`, en UNA sesión: `_celda`;
  `_exigir_reg_editable` (R14) y `_exigir_sin_recalculo` (R15) sobre cada línea enviada que
  esté en la celda; reparto `aplicando` del grupo (`_filas_reparto(session, _claves_de(celda),
  (ESTADO_APLICANDO,))`) ⇒ `CeldaInvalida` 409 (R33); `planificar_celda` (`admite_nuevas =
  worker_key != "sin-trabajador"`); `plan.plantilla_id != plantilla_esperada` ⇒ 409 de R12;
  R14/R15 sobre la plantilla; aplica `horas`; materializa; crea las nuevas (R20, R21, R34;
  ordinaria antes que extra); `_record_undo(action="celda_edit", registros=snaps,
  creadas=ids)` con `_reg_snapshot` + `horas_orig`, `extra_auto`, `document_id` (R25);
  `_afectadas` tras escribir; `commit`. Devuelve `{editadas, materializadas, creadas,
  documentos, afectadas}`. Sin cambios ni nuevas: no escribe ni registra undo.
- `_REG_UNDO_MARCAS = ("horas_orig", "extra_auto")`, aplicadas solo si vienen (R28).
- `undo_last(self, *, actor=None)`: en `celda_edit`, tras los snaps, papelera
  (`deleted_by=actor`) para las `creadas` activas no congeladas (las congeladas, `omitidos`);
  `document_ids` = los de los snaps; `afectadas` = `_afectadas` de las líneas de la entrada.
- `marcar_recalculo_pedido_compartido(ids, *, peticion_id, ahora_utc=None) -> int` (R39):
  `UPDATE parte_documents SET recalculo_pedido_id, recalculo_pedido_at_utc WHERE id IN (ids)`,
  un `commit`, devuelve `rowcount`; sin guarda de congelación ni undo (seguimiento, F-043).
- `anular_recalculo_pedido_compartido(ids, *, peticion_id)`: lo mismo a NULL, solo donde
  `recalculo_pedido_id == peticion_id` (un pedido posterior se respeta).

## 6. Rutas · `app.py`

- `CeldaPayload`: `obra_key`, `worker_key`, `fecha: date`, `lineas: list[CeldaLinea]` (`id`,
  `antes`, `horas: float | None`), `nueva_ordinaria`, `nueva_extra`. Pydantic da 422.
- `POST /api/matriz/celda` (`include_in_schema=False`): `contexto_celda` (None ⇒ 409 de R12);
  códigos: ordinaria con `TipoHoraMatcher(...).match(categoria, extra=False)`, extra con
  `fetch_hora_extra_recurso(reside)` (`method="manual"`); fallo de Sigrid ⇒ WARNING y sin
  código (R21). `guardar_celda`; `CeldaInvalida` ⇒ `{ok: false, error}` con su `status`;
  `CongeladoError` ⇒ manejador global (409). Con algo escrito, `recalculo =
  _pedir_recalculo_compartido(documentos + afectados, MOTIVO_EDICION_CELDA, actor)` (R23).
  INFO `[celda]` (R24, con el pedido). Responde R22.
- `_pedir_recalculo_compartido(ids, motivo, actor) -> str` (R39), con la forma de
  `_pedir_recalculo_seguido`: ids sin repetir (tocados primero); con publicador, uuid4 y
  `marcar_recalculo_pedido_compartido` (fallo ⇒ WARNING, sin espera); UN `pedir_recalculo` con
  `document_id = ids[0]`; si `fallo`, `anular_recalculo_pedido_compartido` (fallo ⇒ WARNING).
- `GET /api/matriz/celda/otras?obra_key=&worker_key=&fecha=` (`include_in_schema=False`,
  solo lectura): `{ok: true, afectadas}` (R36, R38); fecha inválida ⇒ 422.
- `/api/undo`: `undo_last(actor=_actor(request))`; en `celda_edit`,
  `_pedir_recalculo_compartido(document_ids + afectados, MOTIVO_DESHACER_CELDA, actor)` (R27).

## 7. JS · IIFE «Matriz de obra» de `static/app.js`

Funciones **puras a dos espacios de sangría** (las extrae la regex de F-042); `dblclick` sobre ellas:
- `camposCelda(regs, admiteNuevas)` → `[{id|null, tipo, etiqueta, valor, congelada, nueva}]`:
  una por reg (R1) y, si no todas congeladas y `admiteNuevas`, las nuevas de R2 (R3, R35).
- `cuerpoCelda(campos, valores, celda)` → `null` (R6) o el cuerpo de R7 (`celda` de
  `data-obra-key`, `data-wk`, `data-fecha`; R31).
- `textoOtras(afectadas)` (R36) y `avisoAfectadas(afectadas)` → lista de `{href, texto}` (R37).
- El popup añade la nota R5 (`.mxe-nota`), los avisos R32 y R36 (`.mxe-aviso`) y «(nueva)»
  (`.mxe-nueva`). Guardar: `fetch` → `MotivoHttp.lanzarSiFalla` → R8 o R37. Sin `Promise.all`.

## 8. Otras obras del mismo día (respuesta al humano)

- **La pasada es completa**: `despacho._recalcular` → `RecursoConciliador.conciliar_todos()`;
  el `document_id` del mensaje no acota nada (solo el seguimiento). `_pasada` revierte las
  `extra_auto` no congeladas, lee todo lo activo y `_reclasificar_extras_jornada` agrupa por
  `(recurso, fecha_int)` entre obras y partes (`repartir_dia`, F-045, o `_reajustar`, F-046).
- **Otros días no cambian**: `detalle_jornada_dia(d, candef, mapa, es_laborable, excepcion)`
  no recibe horas; el resto semanal (candef 9 ⇒ 42 ⇒ 6 h el último laborable) es de calendario.
- **Espera (DA13-C)**: hoy `_exigir_sin_recalculo(doc)` mira el pedido de ESE documento y sv3
  marca solo el del mensaje: X se reescribiría sin espera (R-g de F-043). Con F-049 sv4 escribe
  el mismo P en Y y X (R39) y sv3 marca todo documento con P (R41): una pasada; X en espera
  entretanto (editar y «Aplicar» de F-046 dan 409) y libre a la vez que Y. P es uuid4 (sv4) o
  el id del parte (F-047): nunca coincide con el pedido de otro documento.
- **Líneas de X congeladas**: cuentan y no se tocan; su documento recibe P (seguimiento sin
  guarda, F-043). `REPARTO_REAJUSTE` apagado: Y absorbe la jornada que quede (E12b). Encendido
  (anotado así en Azure el 2026-10-18): Y recibe el ideal y X queda en `reparto_pendiente`
  `pendiente` (E12c), visible en las dos matrices, decidido al aprobar y que bloquea aprobar
  (F-046 R36) y registrar el día (R32); `mantenido` con otra `firma_grupo` ⇒ `pendiente`.
- **DA11 encaja**: R33 y «Aplicar» ya van por grupo (recurso, fecha), no por obra.

## 9. Tests (sin red ni BBDD real; nombres `test_f049_rN_...`)

- Núcleo: E1–E10 sobre `planificar_celda`, errores R11–R13 y R35 con su `status`, R18 y R19.
- sv4 repositorio/rutas (SQLite, `sembrar_parte`, publicador falso): E2 con contexto, partida
  y código del matcher falso (R20, R21); E9/E10 con el fixture E1 de F-050 (R34); E4 (R18);
  409 congelada, en espera y `aplicando` sin escribir (R14, R15, R33); 409 de R12 (antes
  obsoleto, nueva aparecida, línea movida, clave vacía); atomicidad (R16); E12: `afectadas` =
  [X] con `congelada`, sin X del día siguiente ni otro recurso, y GET igual sin escribir (R38);
  pedido compartido (R23, R39): el mismo P en Y y X, UN mensaje con `document_id` de Y, PATCH
  en X ⇒ 409, cola caída ⇒ P quitado solo donde siga y un Q posterior intacto; sin cambios,
  null; INFO (R24); deshacer (R25–R28); `regs` con `a`, leyenda y `data-*` (R9, R10, R31).
- JS en node: `camposCelda`, `cuerpoCelda`, `textoOtras`, `avisoAfectadas`; popup con DOM falso
  (una POST, avisos R32/R36, `fallo`, R37 sin recarga hasta «Cerrar», motivo). `node --check`.
- sv3: R40 (E12a/b/c con `repartir_dia` y `proponer_dia` reales y `_reclasificar_extras_jornada`
  con repositorio falso; otro día de la semana intacto). R41–R42 sobre el adaptador real con
  SQLite: P en Y y X ⇒ los dos marcados y True; Q en X ⇒ solo Y (E12d); sin pedido u otro,
  nada; pedido F-047 (= id) solo ese; repetir idempotente. Raíz: R30.

## 10. Verificaciones manuales (humano)

- **M1 · SUPERADA (2026-10-20)**: popup de doble clic de la matriz «Horas por día» de la obra.
- **Despliegue (lo lanza el humano, desde `infra/`), sv3 antes que sv4**: `.\redeploy_partes.ps1
  -Solo sv3`, comprobar en su resumen que la revisión activa es la nueva (KEDA, mínimo 0
  réplicas: activa aunque no corra) y luego `-Solo sv4`. Sin variable de entorno nueva.
- **M2**: solo extra 10 → Ord. (nueva) 8, Extra 2 → 8+2 en **una sola fila**; la nueva con
  código, partida y su fila del papel. **M3**: solo 8 → Extra (nueva) 2 → 8+2 estable.
- **M4**: pareja 8 + 2 (jornada) → Extra 3 → 8+3; solo lectura en `partes`:
  `SELECT id, tipo_hora, horas, horas_orig, extra_auto FROM parte_registros WHERE id IN (…);`
- **M5**: congelada sin «Guardar»; parte en espera ⇒ 409. **M6**: «Deshacer» tras M2.
- **M7**: mismo trabajador y día en dos obras: aviso al abrir, lista con enlace tras guardar y,
  tras el recálculo, la otra obra con su reparto nuevo (o reparto pendiente si estaba aprobada).
- **M8**: en M7 la otra obra espera y se libera con la de la celda (una sola pasada en el log
  de sv3); solo lectura: `SELECT id, recalculo_pedido_id, recalculo_terminado_id FROM
  parte_documents WHERE id IN (…);` da el mismo pedido y terminado en los dos.

## 11. Riesgos y alternativas descartadas

- **Espera tras guardar** (DA4-A): 22–39 s por pasada (F-047); con DA13-C, una sola pasada.
- **Despliegue mixto** (sv4 nuevo, sv3 viejo): afectados en espera 10 min (sin editar ni
  «Aplicar»); lo evita el orden de §10. sv3 nuevo con sv4 viejo: se marca como hoy (R42).
- **Residual (E12d)**: si X recibe otro pedido Q antes de que sv3 lea P, X espera a la pasada
  de Q (o a vencer); los datos quedan bien porque cada pasada es completa.
- **Aprobar X durante la pasada** no lo para la espera (F-043 DA12): riesgo anterior (R-g).
- **Celda sin `recurso_ide`**: `afectadas` vacía (sv3 puede agruparla en la pasada). **Varios
  partes** (F-050): un solo pedido compartido. **`line_index` propio**: sin pareja ajena.
- Descartadas: `PATCH`+`POST` (no atómico, sin CAS); celda deducida de la primera línea;
  materializar la celda entera; jornada en sv4 (duplicaría sv3); papelera al poner 0; avisar
  de otros días (no cambian); DA13-B (N pasadas completas serializadas por el candado).

## 12. Decisiones del humano — APROBADAS el 2026-10-20

Citas literales (chat con el líder): a la DA13, «c»; a las demás, «apruebo las DA con los
comentarios que te he hecho anteriormente» (la confirmación de M1 y el caso de DA13).

- **DA1–DA12 = A**: DA1 solo el popup de la matriz de obra (ni calendario del trabajador ni
  celda vacía); DA2 `POST /api/matriz/celda` atómica con CAS, celda por (`obra_key`,
  `worker_key`, fecha); DA3 materializar las parejas tocadas; DA4 recálculo seguido con
  espera; DA5 a 0 sin papelera (una nueva a 0 no crea); DA6 plantilla = primera no congelada,
  su documento, `line_index` nuevo y fila de `fila_para_alta_manual`; DA7 clona la partida;
  DA8 deshacer con creadas a la papelera y recálculo; DA9 rigor crítico; DA10 ordinaria 0–24,
  extra −24–24, nueva > 0; DA11 aviso (R32) y 409 solo en `aplicando` (R33); DA12 `sin-trabajador` sin nuevas.
- **DA13 = C**: aviso al abrir (R36), lista con enlaces tras guardar (R37) y UN pedido
  compartido que sv3 da por terminado en todos los documentos que lo llevan (R39, R41).
  Descartadas: A (sin espera de los afectados), B (N pasadas serializadas) y D (nada).
