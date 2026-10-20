# F-049 · Editor de celda de la matriz: ordinarias y extra siempre — Diseño

## 1. Servicio y límite

**Solo sv4**: pantalla del portal y escritura en `partes`. No reparte (sv3 recibe el mensaje
de F-042 con dos motivos nuevos que solo traza) ni toca Sigrid. Sin lógica gemela nueva:
`congelacion.py`, `worker_key_for_registro` y `fila_para_alta_manual` (F-050) y
`_pedir_recalculo_seguido` (F-043). Escribe `horas_orig` y `extra_auto`, hasta hoy solo de
sv3, sin cambiar su significado para sv3 (DA3).

## 2. Hoy, y lo que cambia con F-050 y lo fusionado desde `dc03468`

**Hoy en dev (`ff2ed8e`)**: `get_obra` agrega por (clave de trabajador, día); cada
`ObraMatrixCell` lleva `regs` (`_reg_de_celda`: `id`, `t`, `h`, `p`, `c`) en `data-regs`. El
popup (`dblclick` en `td.mx-cell`) pinta una fila por reg, ofrece «Extra» si hay ordinaria no
congelada y guarda con `PATCH` + `/extra` en paralelo. `crear_extra_desde` clona sin partida y
no se deshace; el undo `registro_edit` no guarda `horas_orig` ni `extra_auto`. sv3, en cada
pasada, borra las `extra_auto` no congeladas y restaura `horas = horas_orig`: editar la pareja se pierde.

**Fusionado en dev desde `dc03468`** (lo que la spec original no veía):

- **F-046**: la matriz marca `data-reparto` en el `<td>` (`registros_con_reparto`);
  `_filas_reparto`, `_claves_de` (recurso, fecha), `ESTADOS_BLOQUEAN`, `MOTIVO_REAJUSTE`.
  Editar líneas no tiene guarda de reparto (`RepartoPendienteError` solo al aprobar) y
  «Aplicar» da 409 si el grupo cambió (su R33). `congelacion.py` igual. ⇒ R32, R33, DA11.
- **F-048**: `horas_extra_leidas` (solo traza): se conserva al materializar y la nueva nace
  con NULL (R18, R20). **F-051**: solo sv2/sv3, nada de este diseño.

**F-050** (rama `feature/F-050-misma-fila-para-el-mismo-trabajador`, se fusiona antes):

- `parte_repository.py`: `_clave_trabajador`, `_recurso_de`, `worker_key_for_registro`
  (`rec-` > `emp-` > `nom-` > `sin-trabajador`), `fila_para_alta_manual(regs_doc, clave,
  nombre)` (la usa `crear_parte_manual`), `clave_actual_de_clave_antigua` (307 en `GET
  /trabajadores/{clave}`) y empresa en «Por persona» (no en la matriz). `get_obra` no cambia
  de código pero agrupa por la clave nueva: **una celda junta IA y alta manual** (E9: mismo
  parte, filas 1 y 3, parejas distintas) y puede abarcar varios partes. `edit_*_id` no los
  usan plantilla ni JS (sí los tests de F-050). Su `app.js` toca otras IIFE, no esta.
- **Efecto en F-049**: (a) la ruta identifica la celda por (`obra_key`, `worker_key`, fecha)
  y no por la primera línea (R7, R11, R12, R31; DA2); (b) la fila del papel de la nueva sale
  de `fila_para_alta_manual` (R34; DA6); (c) la celda `sin-trabajador` junta a personas sin
  identificar: no se le crean líneas (R35; DA12); (d) un POST con una clave anterior a F-050
  reconstruye una celda vacía ⇒ 409 «recarga» (R12).

## 3. Ficheros

**Crear** (tests en `services/partes-front/tests/` salvo el de la raíz):

- `services/partes-front/application/services/edicion_celda.py` — núcleo puro (§4).
- `test_f049_plan_celda.py` (núcleo: R11–R14, R17–R19, R35); `test_f049_guardar_celda.py`
  (repositorio y ruta con SQLite de `tests/dobles.py`: R11–R28, R33–R35);
  `test_f049_editor_js.py` (funciones puras de `app.js` en node y popup con DOM falso: R1–R8,
  R32; patrón de `test_f042_recalculo_fecha.py`); `tests/test_f049_contrato_motivos.py`
  (raíz, R30, carga por ruta como el de F-042).

**Modificar**

- `services/partes-front/infrastructure/database/parte_repository.py` — `_reg_de_celda`
  (`a`), `_celda`, `contexto_celda`, `guardar_celda`, `_REG_UNDO_MARCAS`,
  `_apply_reg_snapshot`, `_record_undo` (clave opcional `creadas`), `undo_last` (rama
  `celda_edit`, `actor`).
- `services/partes-front/interface_adapters/web/app.py` — `CeldaPayload`,
  `POST /api/matriz/celda` y la rama `celda_edit` de `/api/undo`.
- `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` —
  `MOTIVO_EDICION_CELDA = "edicion_celda"` y `MOTIVO_DESHACER_CELDA = "deshacer_edicion_celda"`.
- `services/partes-front/static/app.js` (IIFE «Matriz de obra», §7) y `static/styles.css`.
- `services/partes-front/templates/obra_detail.html` — leyenda (R9), `data-obra-key` en la
  tabla y `data-wk` en cada `<tr>` de la matriz (R31).
- **Lista cerrada de tests existentes** (por `undo_last(actor=…)`, DA8): el doble
  `undo_last(self)` de `test_f042_recalculo_fecha.py` (~l. 470) y el de
  `test_f043_alcance_y_seguimiento.py` (~l. 636) pasan a `undo_last(self, **_kw)`. Nada más.
- `docs/ARCHITECTURE.md` (semánticas 3 y 10) y `PycharmProjects/azure-apps/partes.md`
  (motivos de `q-persistencia` y la ruta nueva; commit local en `azure-apps`).

**No se tocan**: sv3 y sv5; `orm_models.py`; `congelacion.py`; `reparto_aviso.py`;
`seguimiento_recalculo.py`; `jornada_resolver.py`; de F-050, `worker_key_for_registro`,
`_clave_trabajador`, `fila_para_alta_manual` y `get_obra` (salvo `_reg_de_celda`);
`edit_normal_id` / `edit_extra_id`; `PATCH /api/registros/{id}`, `/extra`,
`crear_extra_desde`, `update_registro` (DA2); `trabajador_detail.html` (DA1);
`crear_parte_manual`; los tests de F-004, F-025, F-042, F-043, F-046, F-048 y F-050 (salvo
los dos dobles de arriba).

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
def planificar_celda(celda: Sequence[LineaCelda], cambios: Sequence[Cambio],
                     nueva_ordinaria: float | None, nueva_extra: float | None,
                     *, admite_nuevas: bool) -> PlanCelda
```

`planificar_celda` (puro, en este orden): lista no vacía e ids no repetidos (R11, 422);
rangos (R13, 422); nueva con `admite_nuevas` False (R35, 422); ids enviados == líneas no
congeladas de `celda` (vacía incluida) y `antes` == `horas` con tolerancia 1e-9 (R12, 409);
nueva de un tipo presente en `celda` (R12, 409). `cambios` del plan = los de valor distinto;
`materializar` = líneas no congeladas cuya clave de pareja esté en las de los cambios que son
miembros (`extra_auto` o `con_orig`), con el valor del popup, sin repetir las de `cambios`
(R18); `documentos` = los de cambios, materializadas y plantilla si se crea algo, sin repetir
y en orden de aparición. Congelación (R14), espera (R15) y reparto (R33) no se deciden aquí:
el repositorio las comprueba **antes**, sobre las líneas enviadas que estén en la celda.

## 5. Repositorio · `parte_repository.py`

- `_reg_de_celda`: añade `fila["a"] = 1` si `reg.extra_auto` (R10).
- `_celda(session, obra_key, worker_key, fecha_int) -> list[ParteRegistroOrm]`: líneas no
  incidencia, fuera de la papelera, de documento activo y con ese `fecha_int` (filtro SQL),
  y en Python `obra_key_for_registro` y `worker_key_for_registro` iguales (las de F-050).
- `contexto_celda(obra_key, worker_key, fecha_iso) -> dict | None`: `{plantilla_id, reside,
  categoria}` de la plantilla (None si la celda no tiene líneas), sin escribir.
- `guardar_celda(*, obra_key, worker_key, fecha_iso, cambios, nueva_ordinaria, nueva_extra,
  hora_ordinaria, hora_extra, plantilla_esperada, by) -> dict`: en UNA sesión, en orden:
  `_celda`; `_exigir_reg_editable` (R14) y `_exigir_sin_recalculo` (R15) sobre cada línea
  enviada que esté en la celda; reparto en `aplicando` del grupo (`_filas_reparto(session,
  _claves_de(celda), (ESTADO_APLICANDO,))`) ⇒ `CeldaInvalida` 409 (R33); `planificar_celda`
  (`admite_nuevas = worker_key != "sin-trabajador"`); si `plan.plantilla_id !=
  plantilla_esperada` ⇒ 409 de R12; guardas R14/R15 sobre la plantilla; aplica `horas`;
  materializa (`horas_orig = None`, `extra_auto = False`); crea las nuevas (R20, R21, R34:
  `line_index` = `max` del documento con papelera + 1, ordinaria antes que extra;
  `empleado_line_no` y leído de `fila_para_alta_manual(regs_doc, worker_key, nombre)`);
  `_record_undo(action="celda_edit", registros=snaps, creadas=ids)` con snaps de
  `_reg_snapshot` + `horas_orig`, `extra_auto`, `document_id` (R25); `commit`. Devuelve
  `{editadas, materializadas, creadas, documentos}`. Sin cambios ni nuevas: no escribe ni
  registra undo y devuelve listas vacías.
- `_REG_UNDO_MARCAS = ("horas_orig", "extra_auto")`, aplicadas solo si vienen en el snap (R28).
- `undo_last(self, *, actor: str | None = None)`: para `celda_edit`, tras aplicar snaps,
  manda a la papelera (`deleted_at_utc` ahora, `deleted_by=actor`) las `creadas` activas y
  no congeladas (las congeladas cuentan en `omitidos`) y `document_ids` = los
  `document_id` de los snaps. Resto de acciones: igual que hoy (R28).

## 6. Rutas · `app.py`

- `CeldaPayload(BaseModel)`: `obra_key: str`, `worker_key: str`, `fecha: date`, `lineas:
  list[CeldaLinea]` (`id: int`, `antes: float`, `horas: float | None`), `nueva_ordinaria:
  float | None = None`, `nueva_extra: float | None = None`. Pydantic da 422 a lo mal formado.
- `POST /api/matriz/celda` (`include_in_schema=False`): `contexto_celda` (None ⇒ 409 de R12);
  si hay nueva ordinaria, `TipoHoraMatcher(sigrid_client.fetch_tipos_hora()).match(categoria,
  extra=False)` pasado al dict `{ide, cod, res, pre, prenom, method}`; si hay nueva extra,
  `fetch_hora_extra_recurso(reside)` → `method="manual"`; cada fallo de Sigrid, WARNING y
  sigue sin código (R21). `guardar_celda(...)`; `CeldaInvalida` ⇒ `{ok: false, error}` con su
  `status`; `CongeladoError` lo sigue resolviendo el manejador global (409). Con algo
  escrito, `_pedir_recalculo_seguido(doc, MOTIVO_EDICION_CELDA, actor)` por documento y
  `recalculo = peor_estado(...)` (R23); si no, `None`. INFO `[celda]` (R24).
- `/api/undo`: `undo_last(actor=_actor(request))`; si `action == "celda_edit"`, recálculo
  seguido de cada `document_ids` con `MOTIVO_DESHACER_CELDA` (R27), como hoy con la fecha.

## 7. JS · IIFE «Matriz de obra» de `static/app.js`

Dos funciones **puras a dos espacios de sangría** dentro de la IIFE (las extrae el test con
la regex de F-042) y el manejador `dblclick` reescrito sobre ellas:

- `camposCelda(regs, admiteNuevas)` → lista de `{id|null, tipo, etiqueta, valor, congelada,
  nueva}`: una por reg (R1) y, si no están todas congeladas y `admiteNuevas`, las nuevas de
  R2 (R3, R35). `admiteNuevas = wk !== "sin-trabajador"`.
- `cuerpoCelda(campos, valores, celda)` → `null` si no hay nada que enviar (R6) o el cuerpo
  de R7 (`celda` = `{obra_key, worker_key, fecha}` de `data-obra-key`, `data-wk` y
  `data-fecha`, R31).
- El popup añade la nota de R5 (`.mxe-nota`), el aviso de R32 si `td.dataset.reparto`
  (`.mxe-aviso`) y rótulos «(nueva)» (`.mxe-nueva`). Guardar: `fetch` →
  `MotivoHttp.lanzarSiFalla` → R8. Sin `Promise.all`.

## 8. Por qué materializar (DA3) y qué hace sv3 después

Lo escrito pasa a ser «lo del parte» para sv3: una base sin `horas_orig` no se restaura y una
extra explícita no se borra ni es de la pareja (`es_miembro`, F-037). sv3 sigue aplicando la
jornada en la pasada siguiente (E5, E8): R5 lo avisa y el recálculo pedido (DA4) lo enseña en
segundos. Efectos en F-045 y F-046: riesgo §12.

## 9. Tests (sin red ni BBDD real; nombres `test_f049_rN_...`)

- Núcleo: E1–E10 sobre `planificar_celda`, cada error de R11–R13 y R35 con su `status`,
  plantilla (R19) y materializar solo parejas tocadas (R18).
- Repositorio/ruta (SQLite, `sembrar_parte`, publicador falso): E2 crea la ordinaria con
  contexto, partida y código del matcher falso (R20, R21); E9/E10 con el fixture de F-050 E1:
  la nueva hereda la fila de menor `line_index` y su clave es la de la celda (R34); E4 deja
  `horas_orig` NULL y `extra_auto` False sin tocar `horas_extra_leidas` (R18); 409 congelada,
  en espera y `aplicando` sin escribir (R14, R15, R33); 409 por `antes` obsoleto, nueva
  aparecida, línea movida y clave sin líneas (R12); atomicidad forzando un fallo (R16);
  recálculo por documento y null sin cambios, fallo de cola no deshace (R23); INFO sin clave
  (R24); deshacer (R25–R28); `regs` con `a`, leyenda y `data-*` (R9, R10, R31).
- JS en node: `camposCelda` (1, 2 con `extra_auto`, 3, congeladas, solo extras,
  `sin-trabajador`), `cuerpoCelda` (vacíos, 0, sin cambios, claves) y popup con DOM falso
  (una petición, avisos de R32 y `fallo`, motivo en el título). `node --check`.
- Raíz: `clasificar` de sv3 da `recalcular` con los motivos nuevos (R30). Suites existentes
  sin cambios (R29).

## 10. Verificaciones manuales (humano)

- **M1 · antes de implementar**: confirmar que la pantalla es la matriz de obra (doble clic)
  y si con solo ordinarias ve hoy la «Extra» a 0. Si no, se revisa R2.
- **Despliegue solo de sv4**: `.\redeploy_partes.ps1 -Solo sv4` desde `infra/`, lo lanza el
  humano (sv3 ya acepta cualquier motivo).
- **M2**: solo extra 10 → Ord. (nueva) 8, Extra 2 → tras «Actualizar», 8+2 en **una sola
  fila**; en Líneas, la nueva con código, partida y la fila del papel de la persona.
- **M3**: solo ordinarias 8 → Extra (nueva) 2 → 8+2 estable. **M4**: pareja 8 + 2 (jornada)
  → Extra 3 → 8+3; solo lectura en `partes`: `SELECT id, tipo_hora, horas, horas_orig,
  extra_auto FROM parte_registros WHERE id IN (…);`
- **M5**: congelada sin «Guardar»; parte en espera ⇒ 409 en el popup. **M6**: «Deshacer» tras
  M2 → extra a 10 y la ordinaria nueva en la Papelera.

## 11. Solapes y orden

- **Orden del humano (2026-10-20)**: F-050 → **F-049** → F-014 → F-047. T1 comprueba que
  F-050 está en dev antes de tocar código; si no, `blocked`.
- **F-050**: §2. Ficheros comunes (`parte_repository.py`, `obra_detail.html`, `app.js`) sin
  solape de lógica: F-049 consume su clave y su `fila_para_alta_manual`.
- **F-047** (aprobada, sin implementar): **F-049 no depende de ella**. Usa solo la guarda
  `_exigir_sin_recalculo` de F-043, que F-047 amplía al parte nuevo sin cambiar el texto (su
  R15): la celda hereda ese 409 sin tocar nada. Solape solo textual en `parte_repository.py`,
  `obra_detail.html` y `app.js`; lo resuelve quien fusione F-047.

## 12. Riesgos y alternativas descartadas

- **Espera tras guardar** (DA4-A): otra celda del mismo parte da 409 durante la pasada
  (22–39 s medidos en F-047). Es el precio de no dejar aprobar a medias.
- **Reparto entre obras y F-046**: la `extra_auto` materializada pesa más en F-045 ese día
  (totales intactos); con F-046 encendido el reparto del día se rehace y «Aplicar» sobre el
  viejo da 409 (su R33).
- **`line_index` propio**: la nueva no hereda una pareja ajena (F-037). **Varios partes**
  (F-050): cada documento tocado pide su recálculo; la nueva va al de la plantilla.
- **`/extra` sin uso** desde el editor (DA2): queda por sus tests; retirarla, otra feature.
- Descartadas: `PATCH`+`POST` como hoy (no atómico, sin CAS); deducir la celda de la primera
  línea (con F-050 una línea movida daría 422 en vez del 409 «recarga»); materializar la
  celda entera (fija parejas que nadie tocó); calcular la jornada en sv4 (duplicaría sv3);
  papelera al poner 0 (contra «en Sigrid nunca se borra, se pone a 0»).

## 13. Decisiones abiertas (humano) — todas PROPUESTAS, ninguna aprobada

| DA | Decisión | Opciones | Recomendación | ¿Cambia? |
|---|---|---|---|---|
| DA1 | Alcance | A) solo el popup de la matriz de obra; sin editor en el calendario del trabajador ni en celda vacía o solo incidencia (para eso, «+ Nuevo»). B) también el calendario del trabajador | A | No |
| DA2 | Ruta y forma de identificar la celda | A) ruta atómica nueva `POST /api/matriz/celda` con CAS (`antes`) y la celda por (`obra_key`, `worker_key`, fecha). B) igual, pero celda deducida de la primera línea (spec original). C) seguir con `PATCH` + `/extra` | A | **Sí, por F-050** (antes B) |
| DA3 | Lo escrito manda | A) materializar las parejas tocadas; sv3 sigue ajustando la jornada (E5); `horas_extra_leidas` se queda como traza. B) como hoy (se pierde) | A | Matiz F-048 |
| DA4 | Recálculo al guardar | A) seguido con espera (F-043). B) ninguno, hasta la siguiente ingesta. C) pedido sin espera (sin 409, aprobable a medias) | A | No |
| DA5 | Poner a 0 | A) la línea queda a 0 (no papelera) y una nueva a 0 no crea nada. B) a la papelera | A | No |
| DA6 | Plantilla y destino de la nueva | A) primera no congelada (ordinaria antes), su documento, `line_index` nuevo y fila y leído de `fila_para_alta_manual` (F-050). B) fila y leído de la propia plantilla (spec original) | A | **Sí, por F-050** (antes B) |
| DA7 | Contexto de la nueva | A) clona también la partida (hoy la extra nueva nace sin ella); código como hoy (extra) y como «+ Nuevo» (ordinaria). B) sin partida, como `/extra` | A | No |
| DA8 | Deshacer | A) restaura horas y marcas, manda las creadas a la papelera firmadas por quien deshace (`undo_last(actor=…)`, toca los dos dobles de §3) y recalcula. B) no deshacer las creadas (E2 dejaría 8 + 10) | A | No |
| DA9 | Rigor | A) crítico: escribe horas que acaban en Sigrid y nómina y marcas que gobiernan sv3. B) estándar | A | No |
| DA10 | Rangos | A) ordinaria 0–24, extra −24–24, ordinaria nueva > 0. B) otros | A | No |
| DA11 | Celda con reparto vivo (F-046) | A) se edita con aviso (R32) y 409 solo en `aplicando` (R33). B) 409 con cualquier reparto vivo (decidir antes). C) sin guarda, como `PATCH` hoy | A | **Nueva, por F-046** |
| DA12 | Fila `sin-trabajador` | A) se editan sus líneas pero no se crean (junta a personas sin identificar). B) como cualquier fila | A | **Nueva, por F-050** |
