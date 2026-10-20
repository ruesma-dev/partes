# F-049 · Editor de celda de la matriz: ordinarias y extra siempre — Diseño

## 1. Servicio y límite

**sv4**: pantalla del portal y escritura en `partes`. No reparte ni toca Sigrid: pide la
pasada de sv3 (F-042) con dos motivos nuevos que sv3 solo traza. Sin lógica gemela nueva:
reutiliza `congelacion.py`, `worker_key_for_registro` y `fila_para_alta_manual` (F-050),
`_claves_de` / `_filas_reparto` (F-046) y `_pedir_recalculo_seguido` (F-043). Escribe
`horas_orig` y `extra_auto`, hasta hoy solo de sv3, sin cambiar su significado (DA3). **sv3**
solo si el humano elige DA13-C (una condición del adaptador de seguimiento, §8 bis).

## 2. Hoy, y lo que cambia con F-050 y lo fusionado desde `dc03468`

**Hoy en dev (`ff2ed8e`)**: `get_obra` agrega por (clave de trabajador, día); cada
`ObraMatrixCell` lleva `regs` (`_reg_de_celda`: `id`, `t`, `h`, `p`, `c`) en `data-regs`. El
popup (`dblclick` en `td.mx-cell`) pinta una fila por reg, ofrece «Extra» si hay ordinaria no
congelada y guarda con `PATCH` + `/extra` en paralelo. `crear_extra_desde` clona sin partida y
no se deshace; el undo `registro_edit` no guarda `horas_orig` ni `extra_auto`.

- **F-046**: `data-reparto` en el `<td>` (`registros_con_reparto`), `_filas_reparto`,
  `_claves_de` (recurso, fecha), `ESTADOS_BLOQUEAN`. Editar líneas no tiene guarda de reparto
  (`RepartoPendienteError` solo al aprobar); «Aplicar» da 409 si el grupo cambió o si un parte
  del día está en espera (`documentos_en_espera`). ⇒ R32, R33, DA11.
- **F-048**: `horas_extra_leidas` (traza): se conserva al materializar; la nueva nace NULL.
- **F-050** (rama `feature/F-050-misma-fila-para-el-mismo-trabajador`, antes que F-049):
  `worker_key_for_registro` (`rec-` > `emp-` > `nom-` > `sin-trabajador`),
  `fila_para_alta_manual(regs_doc, clave, nombre)`; `get_obra` agrupa por la clave nueva:
  **una celda junta IA y alta manual** (E9) y puede abarcar varios partes. No toca sv3.
  Efecto: la ruta identifica la celda por (`obra_key`, `worker_key`, fecha) (DA2), la fila
  del papel de la nueva sale de `fila_para_alta_manual` (DA6), `sin-trabajador` no crea
  (DA12) y una clave anterior a F-050 reconstruye una celda vacía ⇒ 409 «recarga» (R12).

## 3. Ficheros

**Crear** (tests en `services/partes-front/tests/` salvo los dos indicados):

- `services/partes-front/application/services/edicion_celda.py` — núcleo puro (§4).
- `test_f049_plan_celda.py` (núcleo); `test_f049_guardar_celda.py` (repositorio y rutas con
  SQLite de `tests/dobles.py`: R11–R28, R33–R35, R38, R39); `test_f049_editor_js.py` (puras
  de `app.js` en node y popup con DOM falso, patrón de `test_f042_recalculo_fecha.py`: R1–R8,
  R32, R36, R37); `tests/test_f049_contrato_motivos.py` (raíz, R30, carga por ruta);
  `services/partes-persistencia/tests/test_f049_e12_otra_obra.py` (R40, solo caracteriza).

**Modificar**

- `services/partes-front/infrastructure/database/parte_repository.py` — `_reg_de_celda`
  (`a`), `_celda`, `_afectadas`, `contexto_celda`, `otras_de_celda`, `guardar_celda`,
  `_REG_UNDO_MARCAS`, `_apply_reg_snapshot`, `_record_undo` (`creadas`), `undo_last`.
- `services/partes-front/interface_adapters/web/app.py` — `CeldaPayload`,
  `POST /api/matriz/celda`, `GET /api/matriz/celda/otras` y la rama `celda_edit` de `/api/undo`.
- `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` —
  `MOTIVO_EDICION_CELDA = "edicion_celda"` y `MOTIVO_DESHACER_CELDA = "deshacer_edicion_celda"`.
- `services/partes-front/static/app.js` (IIFE «Matriz de obra», §7) y `static/styles.css`.
- `services/partes-front/templates/obra_detail.html` — leyenda (R9), `data-obra-key` en la
  tabla y `data-wk` en cada `<tr>` de la matriz (R31).
- **Lista cerrada de tests existentes** (por `undo_last(actor=…)`, DA8): el doble
  `undo_last(self)` de `test_f042_recalculo_fecha.py` (~l. 470) y el de
  `test_f043_alcance_y_seguimiento.py` (~l. 636) pasan a `undo_last(self, **_kw)`. Nada más.
- `docs/ARCHITECTURE.md` (semánticas 3 y 10) y `PycharmProjects/azure-apps/partes.md`
  (motivos, rutas nuevas; commit local en `azure-apps`).
- Solo con DA13-C: `services/partes-persistencia/infrastructure/database/recalculo_seguimiento.py`.

**No se tocan**: sv5; sv3 (salvo DA13-C); `orm_models.py`; `congelacion.py`;
`reparto_aviso.py`; `seguimiento_recalculo.py`; `jornada_resolver.py`; de F-050 todo salvo
`_reg_de_celda`; `edit_*_id`; `PATCH /api/registros/{id}`, `/extra`, `crear_extra_desde`,
`update_registro` (DA2); `trabajador_detail.html` (DA1); `crear_parte_manual`; los tests de
F-004, F-025, F-042, F-043, F-046, F-048 y F-050 (salvo los dos dobles).

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
`documentos` = los de cambios, materializadas y plantilla si se crea, sin repetir. Congelación
(R14), espera (R15) y reparto (R33) los comprueba **antes** el repositorio.

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
  `document_ids` = los de los snaps y, con DA13-B, `afectadas` = `_afectadas` de la celda.

## 6. Rutas · `app.py`

- `CeldaPayload`: `obra_key`, `worker_key`, `fecha: date`, `lineas: list[CeldaLinea]` (`id`,
  `antes`, `horas: float | None`), `nueva_ordinaria`, `nueva_extra`. Pydantic da 422.
- `POST /api/matriz/celda` (`include_in_schema=False`): `contexto_celda` (None ⇒ 409 de R12);
  códigos: ordinaria con `TipoHoraMatcher(...).match(categoria, extra=False)`, extra con
  `fetch_hora_extra_recurso(reside)` (`method="manual"`); fallo de Sigrid ⇒ WARNING y sin
  código (R21). `guardar_celda`; `CeldaInvalida` ⇒ `{ok: false, error}` con su `status`;
  `CongeladoError` ⇒ manejador global (409). Con algo escrito, `_pedir_recalculo_seguido(doc,
  MOTIVO_EDICION_CELDA, actor)` por documento tocado y, con DA13-B, por afectado (R39);
  `recalculo = peor_estado(...)` (R23). INFO `[celda]` (R24). Responde R22.
- `GET /api/matriz/celda/otras?obra_key=&worker_key=&fecha=` (`include_in_schema=False`,
  solo lectura): `{ok: true, afectadas}` (R36, R38); fecha inválida ⇒ 422.
- `/api/undo`: `undo_last(actor=_actor(request))`; en `celda_edit`, recálculo seguido de
  `document_ids` (y afectados con DA13-B) con `MOTIVO_DESHACER_CELDA` (R27).

## 7. JS · IIFE «Matriz de obra» de `static/app.js`

Funciones **puras a dos espacios de sangría** dentro de la IIFE (las extrae el test con la
regex de F-042) y el manejador `dblclick` reescrito sobre ellas:

- `camposCelda(regs, admiteNuevas)` → `[{id|null, tipo, etiqueta, valor, congelada, nueva}]`:
  una por reg (R1) y, si no todas congeladas y `admiteNuevas`, las nuevas de R2 (R3, R35).
- `cuerpoCelda(campos, valores, celda)` → `null` (R6) o el cuerpo de R7 (`celda` de
  `data-obra-key`, `data-wk`, `data-fecha`; R31).
- `textoOtras(afectadas)` (R36) y `avisoAfectadas(afectadas)` → lista de `{href, texto}` (R37).
- El popup añade la nota R5 (`.mxe-nota`), los avisos R32 y R36 (`.mxe-aviso`) y «(nueva)»
  (`.mxe-nueva`). Guardar: `fetch` → `MotivoHttp.lanzarSiFalla` → R8 o R37. Sin `Promise.all`.

## 8. Por qué materializar (DA3) y qué hace sv3 después

Lo escrito pasa a ser «lo del parte» para sv3: una base sin `horas_orig` no se restaura y una
extra explícita no se borra ni es de la pareja (`es_miembro`, F-037). sv3 sigue aplicando la
jornada en la pasada siguiente (E5, E8): R5 lo avisa y el recálculo pedido (DA4) lo enseña.

## 8 bis. Otras obras del mismo día: qué recalcula hoy el sistema (respuesta al humano)

- **La pasada es completa**: `despacho._recalcular` llama a `RecursoConciliador
  .conciliar_todos()`; el `document_id` del mensaje **no acota** nada (solo sirve al
  seguimiento). `_pasada`: `revert_extras_auto` (todas las `extra_auto` no congeladas),
  `fetch_registros_para_recurso` (todo lo activo) y `_reclasificar_extras_jornada` agrupa por
  `(recurso, fecha_int)` **entre obras y partes** y reparte con `repartir_dia` (F-045) o
  `_reajustar` (F-046). Tras guardar en la obra Y, la X del mismo día se recalcula sola.
- **Otros días no cambian**: `_detalle_jornada` → `detalle_jornada_dia(d, candef, mapa,
  es_laborable, excepcion)` no recibe horas: el resto semanal (`max(0, S − 4c)`, candef 9 ⇒ 42
  ⇒ 6 h el último laborable) sale del calendario. Cada (recurso, día) se reparte aparte.
- **La espera de F-043 cubre solo el documento pedido**: `_exigir_sin_recalculo(doc)` mira el
  `recalculo_pedido_id` / `terminado_id` de ESE documento y sv3 marca terminado solo el del
  mensaje (`marcar_terminado` con `id == document_id`). `alcance_parte` solo cuenta
  trabajadores y líneas para el diálogo de la fecha; no espera nada. Los partes de X se
  reescriben (ids nuevos de sus `extra_auto`) sin espera: riesgo R-g de F-043, anterior.
- **Líneas de X congeladas**: cuentan y no se tocan. Interruptor `REPARTO_REAJUSTE` apagado:
  Y absorbe la jornada que quede (E12b, puede salir 0 + jornada). Encendido (el líder lo anotó
  encendido en Azure el 2026-10-18; el repo lo da por pendiente): si hay alguna ordinaria
  libre, Y recibe el ideal y X queda en `reparto_pendiente` `pendiente` (E12c), visible como
  `data-reparto` en las matrices de las dos obras y decidido en el aviso al aprobar; bloquea
  aprobar el documento (R36 de F-046) y registrar las líneas del día (R32). Un `mantenido`
  previo con otra firma (`firma_grupo`) vuelve a `pendiente`: se pide decidir otra vez.
  Líneas `encolado`/`dedicacion` (duras) o sin cuadre: sin cambios y WARNING.
- **DA11 encaja**: R33 y «Aplicar» ya van por grupo (recurso, fecha), no por obra.

## 9. Tests (sin red ni BBDD real; nombres `test_f049_rN_...`)

- Núcleo: E1–E10 sobre `planificar_celda`, cada error de R11–R13 y R35 con su `status`,
  plantilla (R19) y materializar solo parejas tocadas (R18).
- Repositorio/rutas (SQLite, `sembrar_parte`, publicador falso): E2 con contexto, partida y
  código del matcher falso (R20, R21); E9/E10 con el fixture E1 de F-050 (R34); E4 (R18); 409
  congelada, en espera y `aplicando` sin escribir (R14, R15, R33); 409 de R12 (antes obsoleto,
  nueva aparecida, línea movida, clave vacía); atomicidad (R16); recálculo y null (R23); E12:
  `afectadas` = [X] con `congelada`, sin la línea de X del día siguiente ni otro recurso, y
  GET igual sin escribir (R38); con DA13-B, pedidos de Y y X y PATCH en X ⇒ 409 (R39); INFO
  (R24); deshacer (R25–R28); `regs` con `a`, leyenda y `data-*` (R9, R10, R31).
- JS en node: `camposCelda`, `cuerpoCelda`, `textoOtras`, `avisoAfectadas`; popup con DOM
  falso (una petición POST, avisos R32/R36, `fallo`, R37 sin recarga hasta «Cerrar», motivo en
  el título). `node --check`.
- sv3 (R40): E12a/b/c con `repartir_dia` y `proponer_dia` reales y `_reclasificar_extras_jornada`
  con repositorio falso: X cambia el mismo día y no otro día de la semana. Raíz: R30.

## 10. Verificaciones manuales (humano)

- **M1 · SUPERADA (2026-10-20)**: el humano confirma la pantalla (popup de doble clic de la
  matriz «Horas por día» de la vista de obra).
- **Despliegue solo de sv4** (`.\redeploy_partes.ps1 -Solo sv4` desde `infra/`, lo lanza el
  humano); con DA13-C, antes `-Solo sv3`.
- **M2**: solo extra 10 → Ord. (nueva) 8, Extra 2 → 8+2 en **una sola fila**; la nueva con
  código, partida y su fila del papel. **M3**: solo 8 → Extra (nueva) 2 → 8+2 estable.
- **M4**: pareja 8 + 2 (jornada) → Extra 3 → 8+3; solo lectura en `partes`:
  `SELECT id, tipo_hora, horas, horas_orig, extra_auto FROM parte_registros WHERE id IN (…);`
- **M5**: congelada sin «Guardar»; parte en espera ⇒ 409. **M6**: «Deshacer» tras M2.
- **M7** (DA13): trabajador con horas el mismo día en dos obras: aviso al abrir, lista con
  enlace tras guardar y, tras el recálculo, la otra obra con el reparto nuevo (o el aviso de
  reparto pendiente si estaba aprobada).

## 11. Solapes y orden

- **Orden del humano (2026-10-20)**: F-050 → **F-049** → F-014 → F-047. T1 comprueba F-050 en
  dev antes de tocar código; si no, `blocked`.
- **F-050**: §2; ficheros comunes sin solape de lógica. **F-047** (aprobada, sin implementar):
  F-049 no depende de ella; usa la guarda `_exigir_sin_recalculo` de F-043, que F-047 amplía
  sin cambiar el texto. Solape solo textual; lo resuelve quien fusione F-047.

## 12. Riesgos y alternativas descartadas

- **Espera tras guardar** (DA4-A): 22–39 s por pasada (F-047); con DA13-B, una pasada por
  documento (tocado o afectado), serializadas por el candado de F-046.
- **Aprobar X durante la pasada** no lo para la espera (F-043 DA12): riesgo anterior (R-g).
- **Celda sin `recurso_ide`**: sv3 puede resolverlo en la pasada y agruparla; `afectadas`
  sale vacía porque antes no se sabe. **Varios partes** (F-050): cada uno pide su recálculo.
- **`line_index` propio**: la nueva no hereda pareja ajena (F-037). **`/extra`** queda sin
  uso desde el editor (DA2); retirarla, otra feature.
- Descartadas: `PATCH`+`POST` (no atómico, sin CAS); celda deducida de la primera línea;
  materializar la celda entera; jornada calculada en sv4 (duplicaría sv3 fuera de la lista
  cerrada); papelera al poner 0; avisar de otros días (no cambian).

## 13. Decisiones abiertas (humano) — todas PROPUESTAS, ninguna aprobada

| DA | Decisión | Opciones | Recomendación | ¿Cambia? |
|---|---|---|---|---|
| DA1 | Alcance | A) solo el popup de la matriz de obra (M1 superada); sin editor en el calendario del trabajador ni en celda vacía o solo incidencia. B) también el calendario del trabajador | A | No |
| DA2 | Ruta y celda | A) `POST /api/matriz/celda` atómica con CAS (`antes`) y celda por (`obra_key`, `worker_key`, fecha). B) celda deducida de la primera línea. C) `PATCH` + `/extra` | A | Sí, por F-050 |
| DA3 | Lo escrito manda | A) materializar las parejas tocadas; sv3 sigue ajustando la jornada (E5). B) como hoy (se pierde) | A | Matiz F-048 |
| DA4 | Recálculo al guardar | A) seguido con espera (F-043). B) ninguno hasta la siguiente ingesta. C) sin espera | A | No |
| DA5 | Poner a 0 | A) la línea queda a 0; una nueva a 0 no crea nada. B) papelera | A | No |
| DA6 | Plantilla y destino | A) primera no congelada, su documento, `line_index` nuevo y fila de `fila_para_alta_manual`. B) fila de la plantilla | A | Sí, por F-050 |
| DA7 | Contexto de la nueva | A) clona también la partida. B) sin partida, como `/extra` | A | No |
| DA8 | Deshacer | A) restaura horas y marcas, creadas a la papelera (`undo_last(actor=…)`) y recalcula. B) no deshacer las creadas | A | No |
| DA9 | Rigor | A) crítico. B) estándar | A | No |
| DA10 | Rangos | A) ordinaria 0–24, extra −24–24, ordinaria nueva > 0. B) otros | A | No |
| DA11 | Reparto vivo (F-046) | A) aviso (R32) y 409 solo en `aplicando` (R33). B) 409 con cualquier reparto vivo. C) sin guarda | A | Nueva, F-046 |
| DA12 | Fila `sin-trabajador` | A) se editan sus líneas pero no se crean. B) como cualquier fila | A | Nueva, F-050 |
| DA13 | Otras obras del mismo día (§8 bis) | A) avisar antes (R36) y después con enlaces (R37); espera solo de los partes de la celda; solo sv4. B) A + recálculo seguido también de cada parte afectado (R39): quedan en espera; solo sv4; coste, N pasadas completas (~30 s cada una). C) A + espera de los afectados con UNA pasada: sv4 escribe el mismo `recalculo_pedido_id` en todos y sv3 `marcar_terminado` marca todo documento con ese pedido (una condición en `recalculo_seguimiento.py`, mensaje igual); toca sv3, despliegue sv3 antes que sv4 (si no, los afectados esperan 10 min). D) nada (spec anterior) | B (solo sv4); C si se acepta tocar sv3 | Nueva, pregunta del humano |
