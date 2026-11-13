<!-- specs/F-068-conciliar-pide-recalculo/design.md -->
# F-068 · Diseño técnico

## 1. Servicio y límite (LÍMITE DE SERVICIO)

- **Toca solo sv4** (`services/partes-front`). Motivo: el casado y la reasignación los escribe
  sv4, y sv4 ya es quien pide recálculos a sv3 por `q-persistencia` (F-042). Pedir uno más es
  reutilizar `_pedir_recalculo_compartido`, no lógica nueva.
- **sv3 no cambia**: `mensajes.py` clasifica por `tipo: "recalcular"` y no valida `motivo` (solo
  traza); `marcar_terminado` ya filtra por pedido (F-049 R41). Lo fija el test de contrato raíz.
- **No se copia lógica entre servicios** ni crece la lista cerrada de duplicaciones. No se tocan
  `congelacion.py`, `esta_congelado`, `orm_models.py` ni ningún gemelo.
- **¿Cruza la frontera del proyecto?** No: ni endpoint externo, ni tabla, ni variable, ni base
  compartida. Sí cambia lo que documenta el propio proyecto en el ecosistema: los motivos del
  mensaje «recalcular» viven listados en `azure-apps/partes.md` (§ F-042 y F-049), así que se
  añaden allí en el mismo trabajo (T13, con `git -C … pull` antes).

## 2. Lo que ya existe y se reutiliza (dev `7e5f600`)

- `app.py` `_pedir_recalculo_compartido(ids, motivo, solicitado_por) -> (estado, pedido)`
  (:680): marca UN uuid4 en todos los documentos en una sentencia, publica UN mensaje con
  `document_id = ids[0]`, anula si publicar falla y nunca lanza. Es exactamente lo que piden
  R1, R5 y R6. Lo usan la celda (:2388), deshacer celda (:1723) y sincronizar (:3527).
- `_pedir_recalculo_seguido` (un documento) no sirve aquí: un casado toca N partes y N
  mensajes son N pasadas globales de sv3 (lo que F-069 midió como problema). D2.
- `recalculo_publisher.py`: constantes de motivo y estados; `peor_estado`.
- `ParteRepository.backfill_empleado` (:3377) y `reassign_empleado_by_leido` (:3837),
  `_by_worker_key` (:3877), `_by_registro_ids` (:3920): calculan `affected` (líneas libres
  tras `_separar_congeladas`) y hacen commit. Son el único sitio donde se conocen los partes.
- `undo_last` (:3699) devuelve `action` y `document_ids` (snapshots de documento; vacío para
  `empleado`). `undo_apply` (:1696) ya ramifica por `action` (`parte_fecha`, `celda_edit`).
- JS: `_confirmarCasado` (`app.js` :1478) pinta la tarjeta; el reasignar (:1620) recarga; el
  deshacer (:1858) ya avisa de `recalculo === "fallo"`.

## 3. Solape con F-057 (spec aprobada, rama `feature/F-057-…`, sin implementar)

- **Qué cubre F-057**: solo el editor de celda y deshacer una `celda_edit`: mete en el pedido
  compartido el «resto de la celda». No toca Conciliar, reasignar ni deshacer `empleado`.
- **Qué no cubre y cubre F-068**: todo lo del casado y la reasignación. No hay solape funcional.
- **Comparten**: los dos usan `_pedir_recalculo_compartido` y los dos declaran que **no** lo
  cambian (F-057 R16, F-068 R21): el que entre segundo no tiene que adaptar nada de la función.
- **Conflicto de fusión previsible**: los dos editan `undo_apply` (`app.py` :1716–1727) y la cola
  de `undo_last` (`parte_repository.py` :3765–3775). F-068 añade una rama `empleado` aparte de
  la de `celda_edit`, sin tocar esta; el conflicto es textual y se resuelve conservando ambas.
  El implementer lo anota en su informe si F-057 ya está en `dev` al empezar.

## 4. Repositorio (`infrastructure/database/parte_repository.py`)

Colector opcional, **sin cambiar el valor de retorno** (R22):

```python
def backfill_empleado(self, *, nombre_leido, ide, codigo, nombre, dni,
                      reside=None, documentos: list[str] | None = None) -> tuple[int, int]
```

- Si `documentos` no es None, tras el commit se le añaden (`extend`) los `document_id` de
  `affected` ordenados por `id` de línea, sin repetir (`_documentos_de(affected)`).
- Igual en `reassign_empleado_by_leido`, `_by_worker_key` y `_by_registro_ids` (solo con D3-b).
- Función de módulo nueva, pura sobre ORM ya cargado:
  `_documentos_de(regs) -> list[str]`: `dict.fromkeys(r.document_id for r in sorted(regs,
  key=id))`, sin None. Un solo sitio para las cuatro (y para deshacer).
- `undo_last` (solo D4-b): si `action == "empleado"`, `document_ids` = `_documentos_de` de las
  líneas cuyos snapshots se **aplicaron** (las omitidas por congelación no cuentan). Para el
  resto de acciones el cálculo de hoy no cambia.

Descartado: devolver una tripleta o un NamedTuple (rompe las ~26 llamadas que lo desempaquetan o comparan en tests de F-004,
F-023, F-030 y F-035); consultar los partes después del commit (las líneas ya no están «sin
casar» y no se distinguen las recién casadas; además hay carrera con otra pestaña).

## 5. Rutas (`interface_adapters/web/app.py`)

Ayudante local nuevo, junto a `_pedir_recalculo_compartido`:

```python
def _recalculo_de_trabajador(documentos: list[str], motivo: str,
                             actor: str | None, *, etiqueta: str,
                             updated: int, congeladas: int) -> dict:
    """{recalculo, partes_recalculo}: pide UN recálculo compartido si hay partes."""
```

- Sin partes ⇒ `{"recalculo": None, "partes_recalculo": 0}` y no marca ni publica (R2).
- Con partes ⇒ `_pedir_recalculo_compartido(documentos, motivo, actor)` y el INFO
  `[<etiqueta>] casado updated=… congeladas=… documentos=[…] pedido=… recalculo=…` (R8), sin
  nombres, DNI ni nombre leído.
- No lanza: `_pedir_recalculo_compartido` ya no lanza (R5–R7).
- `conciliacion_confirmar` (:1499): `docs: list[str] = []`, `backfill_empleado(...,
  documentos=docs)`, alias como hoy, y **después** `res.update(_recalculo_de_trabajador(docs,
  MOTIVO_CASADO_CONCILIACION, _actor(request), etiqueta="conciliacion", ...))`. El orden
  importa: el mensaje sale tras los dos commits, así sv3 lee el casado y el alias.
- `empleado_reasignar` (:1590, D3-b): igual con `MOTIVO_REASIGNACION` y etiqueta `reasignar`;
  en la rama `worker_key` el colector va también.
- `undo_apply` (:1696, D4-b): rama nueva `if res.get("ok") and res.get("action") == "empleado"
  and res.get("document_ids")` ⇒ `res["recalculo"], _ = _pedir_recalculo_compartido(ids,
  MOTIVO_DESHACER_TRABAJADOR, actor)`.
- `_actor(request)` ya existe: hoy `conciliacion_confirmar` no lo lee; se lee para
  `solicitado_por`.

## 6. Contrato (`infrastructure/persistencia/recalculo_publisher.py`)

```python
#: F-068: tras casar en Conciliar, reasignar o deshacer cualquiera de los dos.
MOTIVO_CASADO_CONCILIACION = "casado_conciliacion"
MOTIVO_REASIGNACION = "reasignacion_trabajador"
MOTIVO_DESHACER_TRABAJADOR = "deshacer_trabajador"
```

Solo biblioteca estándar (lo exige el test raíz que carga el módulo por ruta). El test raíz
`tests/test_f042_contrato_recalculo.py` amplía sus dos `parametrize` con los tres nombres (R20):
es ampliar casos, no cambiar expectativas.

## 7. Portal (`static/app.js`)

- `_confirmarCasado`: tras el texto «✓ Casado con … · N registro(s) actualizados», función pura
  nueva `textoRecalculoCasado(recalculo, partes) -> [texto, clase] | null` (R14–R16):
  `pedido` ⇒ «· recalculando extras de N parte(s) (1–2 min)»; `sin_cola` ⇒ «(sin recálculo
  automático)»; `fallo` ⇒ texto de R15 en un `recon-status error` que se queda; `null` ⇒ nada.
- Reasignar (D3-b): antes del `window.location.reload()`, si `recalculo === "fallo"`, `alert`
  con el texto de R15 (R18).
- Validación: `node --check services/partes-front/static/app.js`. Los tests de JS del repo (p. ej.
  `test_f049_editor_js.py`) muestran cómo probar la función pura con `node`.

## 8. Comportamiento ante el 422 de F-069 (R11–R13)

- El recálculo pedido **no responde**: sv4 publica y sv3 consume; no hay camino por el que el
  recálculo devuelva 422 a sv4 ni al navegador. Estados posibles: `pedido`, `fallo`, `sin_cola`.
- El 422 que introdujo F-069 es el de **aprobar** (`_validar_ambito`): con ids estables
  (F-069) la base casada conserva su `id`; la extra que crea la pasada es nueva y no estaba en
  la página, así que no da 422 (simplemente no se aprueba). Puede darlo una extra que la pasada
  **borra** (p. ej. reasignar a alguien con otra jornada): ese id viejo ya no existe ⇒ 422 con
  `inexistentes` y «recarga en unos segundos».
- Comportamiento definido: ese 422 no escribe nada (F-022) y el casado ya estaba confirmado en
  otra transacción, así que **no se pierde**; el usuario recarga y aprueba lo que vea. Mensaje:
  el de F-069 R20, sin cambios. El test R12 lo fija de punta a punta en sv4 con SQLite.

## 9. Decisiones

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| D1 · Qué partes reciben el pedido | (a) solo los partes de las líneas casadas no congeladas; (b) además los de otras obras del mismo trabajador y día, como las «afectadas» de F-049 (tras el casado el `recurso_ide` está soltado, F-023 R42: habría que buscarlos por DNI o `empleado_reside`, más código y consultas) | (a): la pasada de sv3 es global y los recalcula igual; solo no salen «en espera» (residual R-g de F-043, como F-057) |  **(a)** (humano, 2026-11-13) |
| D2 · Un pedido o uno por parte | (a) UN pedido compartido y UN mensaje (`_pedir_recalculo_compartido`); (b) `_pedir_recalculo_seguido` por parte (N mensajes, N pasadas globales) | (a) |  **(a)** (humano, 2026-11-13) |
| D3 · Reasignar trabajador | (a) fuera: solo Conciliar y alta de feature aparte; (b) dentro: las cuatro formas de `/api/empleado/reasignar` piden el recálculo (R17, R18) | (b): mismo hueco y mismo riesgo (cambia la jornada ⇒ cambian las extras, y la línea es aprobable al momento); coste: el colector en 3 métodos y 6 líneas de ruta |  **(b)** (humano, 2026-11-13) |
| D4 · Deshacer un casado o una reasignación | (a) fuera; (b) pide recálculo como deshacer fecha o celda (R19) | (b): mismo criterio que F-042 DA1 («la misma acción en sentido contrario») |  **(b)** (humano, 2026-11-13) |
| D5 · Aprobar durante la pasada (~30 s–2 min) | (a) como fecha y celda hoy: el parte está en espera (se pinta y sus ediciones dan 409) pero se puede aprobar (F-047 DA3-B); (b) como (a) y alta de una feature para estudiar bloquear la aprobación de un parte en espera por recálculo de sv4 salvo F-046 «Aplicar»; (c) bloquearlo aquí: no se distingue el pedido de un casado del de F-046 sin columna nueva (`recalculo_pedido_id` es `String(36)`, justo un uuid) ⇒ cambio de esquema, fuera de un hotfix | (b): F-068 baja la ventana de «hasta el siguiente parte nuevo» (horas o días) a la pasada, con el parte marcado; cerrarla del todo es otra feature |  **(b): alta de F-073** (humano, 2026-11-13) |
| D6 · Texto con `fallo` (no hay reintento: las líneas ya no están sin casar) | (a) aviso fijo: «… se hará en la siguiente pasada. No apruebes esos partes hasta ver sus extras.»; (b) botón «Reintentar recálculo» (endpoint nuevo) | (a) |  **(a)** (humano, 2026-11-13) |

## 10. Ficheros

**Modificar** (sv4):
- `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` (§6).
- `services/partes-front/infrastructure/database/parte_repository.py` (§4).
- `services/partes-front/interface_adapters/web/app.py` (§5; import de los motivos nuevos).
- `services/partes-front/static/app.js` (§7).
- Dobles de sv4 que implementen `backfill_empleado` / `reassign_empleado_by_*` / `undo_last` y
  se usen con las rutas tocadas: aceptan `documentos=None` (sin cambiar sus expectativas).

**Modificar** (raíz y documentación): `tests/test_f042_contrato_recalculo.py` (ampliar
parametrize); `docs/ARCHITECTURE.md` (semántica 3: Conciliar, reasignar y deshacer `empleado`
piden recálculo compartido; motivos); `azure-apps/partes.md` (motivos nuevos), en su repo.

**Crear** (tests sv4):
- `services/partes-front/tests/test_f068_repositorio.py` — R4, R22, colector, `_documentos_de`,
  `undo_last` de `empleado` (R19 parte repo).
- `services/partes-front/tests/test_f068_conciliar_recalculo.py` — R1–R10, R11–R13 (integración
  con SQLite y `ColaFake` como en `test_f042_recalculo_fecha.py`), R17, R19 ruta.
- `services/partes-front/tests/test_f068_conciliar_js.py` — R14–R16, R18 con `node`.

**No se tocan**: sv1, sv2, sv3, sv5, `infra/`; `orm_models.py` (sv3 y sv4), `congelacion.py`,
`esta_congelado`/`ESTADOS_CONGELADOS`, `jornada_resolver.py`, `seleccion_sigrid.py`,
`coherencia_recurso.py`, `sigrid_*_client.py`; `_pedir_recalculo_compartido`,
`_pedir_recalculo_seguido`, `marcar_/anular_recalculo_pedido*`, `_exigir_sin_recalculo`,
`seguimiento_recalculo.py`, `approve_document`, `lineas_para_registro`, `_validar_ambito`,
`guardar_celda`, `_afectadas`; `conciliacion.html` (el texto lo pinta `app.js`).

## 11. Riesgos

- **Casado durante una pasada en curso**: sv3 leyó el pedido viejo; al terminar no marca el
  nuevo (UPDATE condicional), así que el parte sigue en espera hasta la pasada del mensaje nuevo,
  que sí ve el casado. Correcto por construcción (F-043); sin cambios.
- **Casado sobre un parte ya en espera**: hoy `backfill_empleado` no aplica `_exigir_sin_recalculo`
  y F-068 no lo añade (cambiaría el comportamiento de Conciliar con un 409 parcial). R10 deja el
  pedido nuevo encima.
- **Muchos partes en un casado** (un nombre leído en todo el mes): una sentencia `UPDATE … IN`
  y un mensaje; la página de Conciliar no sondea `GET /api/recalculo` (tope 1–50), así que no
  hay límite que respetar.
- **Despliegue**: solo sv4; sv3 viejo ya acepta cualquier motivo. Sin orden especial.
