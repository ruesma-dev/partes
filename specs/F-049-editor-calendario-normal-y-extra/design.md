# F-049 · Editor de celda de la matriz: ordinarias y extra siempre — Diseño

## 1. Servicio y límite

**Solo sv4.** Es una pantalla del portal y su escritura en la base `partes`: encaja en sv4
(«portal de revisión»). No calcula repartos (eso es de sv3, que solo recibe el mensaje de
recálculo de F-042 de siempre, con dos motivos nuevos que solo traza) ni toca Sigrid (sv5).
No añade lógica gemela: la congelación se consulta en `congelacion.py` y el recálculo se pide
con `_pedir_recalculo_seguido` de F-043. sv4 escribe dos columnas que hasta hoy solo escribía
sv3 (`horas_orig`, `extra_auto`), sin cambiar su significado para sv3 (DA3).

## 2. Hoy (verificado el 2026-10-15)

- `ParteReviewRepository.get_obra` agrega por (trabajador, día) y da a cada `ObraMatrixCell`
  sus `regs` (`_reg_de_celda`: `id`, `t` n/e, `h`, `p`, `c` si congelada); `obra_detail.html`
  los pone en `data-regs`. El popup (IIFE «Matriz de obra», `dblclick` en `td.mx-cell`) pinta
  una fila por reg, ofrece «Extra» nueva si no hay extra y sí una ordinaria no congelada, y
  guarda con `PATCH /api/registros/{id}` + `POST /api/registros/{id}/extra` en paralelo.
- `crear_extra_desde` clona el contexto de la ordinaria (misma clave de pareja, **sin
  partida**, sin `recurso_precio_hora`) y no es deshacible; `update_registro` guarda horas con
  undo `registro_edit` (sin `horas_orig`/`extra_auto` en `_REG_UNDO_FIELDS`).
- sv3, en cada pasada (`conciliar_todos`, con cada ingesta o recálculo): borra las
  `extra_auto` no congeladas, restaura `horas = horas_orig` de las bases y vuelve a repartir
  (F-015/F-037/F-045). Por eso hoy editar un miembro de pareja se pierde.

## 3. Ficheros

**Crear**

- `services/partes-front/application/services/edicion_celda.py` — núcleo puro (§4).
- `services/partes-front/tests/test_f049_plan_celda.py` — núcleo (R11–R14, R17–R19).
- `services/partes-front/tests/test_f049_guardar_celda.py` — repositorio y ruta con SQLite
  (`tests/dobles.py`): R11–R28.
- `services/partes-front/tests/test_f049_editor_js.py` — funciones puras de `app.js` en node
  y popup con DOM falso (R1–R8), patrón de `test_f042_recalculo_fecha.py`.
- `tests/test_f049_contrato_motivos.py` (raíz) — R30, carga por ruta como el de F-042.

**Modificar**

- `services/partes-front/infrastructure/database/parte_repository.py` — `_reg_de_celda`
  (`a`), `contexto_celda`, `guardar_celda`, `_REG_UNDO_MARCAS`, `_apply_reg_snapshot`,
  `_record_undo` (clave opcional `creadas`), `undo_last` (rama `celda_edit`, `actor`).
- `services/partes-front/interface_adapters/web/app.py` — `CeldaPayload`, ruta
  `POST /api/matriz/celda`, y en `/api/undo` la rama `celda_edit`.
- `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` —
  `MOTIVO_EDICION_CELDA = "edicion_celda"`, `MOTIVO_DESHACER_CELDA =
  "deshacer_edicion_celda"` y el docstring del mensaje.
- `services/partes-front/static/app.js` — IIFE «Matriz de obra» (§7).
- `services/partes-front/static/styles.css` — filas nuevas y nota del popup.
- `services/partes-front/templates/obra_detail.html` — texto de la leyenda (R9).
- **Lista cerrada de tests existentes** (por `undo_last(actor=…)`, DA8): el doble
  `undo_last(self)` de `test_f042_recalculo_fecha.py` (~l. 470) y el de
  `test_f043_alcance_y_seguimiento.py` (~l. 636) pasan a `undo_last(self, **_kw)`. Nada más.
- `docs/ARCHITECTURE.md` — semántica 3 (edición de celda materializa) y 10 (sus guardas).
- `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` — motivos nuevos de
  `q-persistencia` y la ruta nueva (regla de mantenimiento; commit local en `azure-apps`).

**No se tocan**: todo sv3 y sv5; `orm_models.py` (gemelos); `congelacion.py`;
`seguimiento_recalculo.py`; `jornada_resolver.py`; `PATCH /api/registros/{id}`,
`POST /api/registros/{id}/extra`, `crear_extra_desde`, `update_registro` (DA2);
`trabajador_detail.html` y su calendario (DA1); `crear_parte_manual`; los tests de F-004,
F-025, F-042 y F-043 (pasan sin más cambio que los dos dobles de arriba).

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
                     nueva_ordinaria: float | None, nueva_extra: float | None) -> PlanCelda
```

`planificar_celda` (puro, en este orden): lista no vacía e ids no repetidos (R11, 422);
rangos (R13, 422); ids enviados == líneas no congeladas de `celda` y `antes` == `horas` con
tolerancia 1e-9 (R12, 409); nueva de un tipo presente en `celda` (R12, 409). `cambios` del
plan = los de valor distinto; `materializar` = líneas no congeladas de la celda cuya clave
esté en las claves de los cambios que son miembros (`extra_auto` o `con_orig`), con el valor
del popup, sin repetir las ya en `cambios` (R18); `documentos` = los de cambios,
materializadas y plantilla si se crea algo, sin repetir y en orden de aparición. La
congelación con su motivo (R14) y la espera (R15) no se deciden aquí: el repositorio las
comprueba **antes** de llamar a `planificar_celda`, sobre las líneas enviadas.

## 5. Repositorio · `parte_repository.py`

- `_reg_de_celda`: añade `fila["a"] = 1` si `reg.extra_auto` (R10).
- `contexto_celda(ids: list[int]) -> dict | None`: lee las líneas, construye la celda (todas
  las líneas de horas activas del mismo `worker_key_for_registro`, `fecha` y
  `obra_key_for_registro` que la primera) y devuelve `{plantilla_id, reside, categoria}` de
  la plantilla. Sin escribir. Lo usa la ruta para resolver códigos antes de la transacción.
- `guardar_celda(*, cambios, nueva_ordinaria, nueva_extra, hora_ordinaria, hora_extra,
  plantilla_esperada, by) -> dict`: en UNA sesión, en este orden: carga y valida la celda
  (R11, 422 si una línea no es de horas activa o son de celdas distintas);
  `_exigir_reg_editable` sobre cada línea enviada (R14) y `_exigir_sin_recalculo` sobre su
  documento (R15); `planificar_celda`; si `plan.plantilla_id != plantilla_esperada` ⇒ 409
  de R12; `_exigir_sin_recalculo` sobre el documento de la plantilla (R15); aplica `horas`;
  materializa (`horas_orig = None`, `extra_auto = False`); crea las
  nuevas (R20, R21; `line_index` = `max` del documento con papelera + 1, ordinaria antes que
  extra); `_record_undo(action="celda_edit", registros=snaps, creadas=ids)` con snaps de
  `_reg_snapshot` + `horas_orig`, `extra_auto`, `document_id` (R25); `commit`. Devuelve
  `{editadas, materializadas, creadas, documentos}`. Plan sin cambios ni nuevas: no escribe
  ni registra undo y devuelve listas vacías.
- `_REG_UNDO_MARCAS = ("horas_orig", "extra_auto")`; `_apply_reg_snapshot` aplica también
  estas solo si vienen en el snap (solo los de `celda_edit` las llevan: R28).
- `undo_last(self, *, actor: str | None = None)`: para `celda_edit`, tras aplicar snaps,
  manda a la papelera (`deleted_at_utc` ahora, `deleted_by=actor`) las `creadas` activas y
  no congeladas (las congeladas cuentan en `omitidos`) y `document_ids` = los
  `document_id` de los snaps de registros. Resto de acciones: igual que hoy (R28).

## 6. Rutas · `app.py`

- `CeldaPayload(BaseModel)`: `lineas: list[CeldaLinea]` (`id: int`, `antes: float`,
  `horas: float | None`), `nueva_ordinaria: float | None = None`, `nueva_extra: float |
  None = None`. Pydantic da 422 a lo que no sea número.
- `POST /api/matriz/celda` (`include_in_schema=False`): `contexto_celda` (None ⇒ 422 de
  R11 sin tocar nada); si hay nueva
  ordinaria, `TipoHoraMatcher(sigrid_client.fetch_tipos_hora()).match(categoria,
  extra=False)` → dict `{ide, cod, res, pre, prenom, method}`; si hay nueva extra,
  `fetch_hora_extra_recurso(reside)` → `method="manual"`; cada fallo de Sigrid, WARNING y
  sigue sin código (R21). `guardar_celda(...)`; `CeldaInvalida` ⇒ JSON `{ok: false,
  error}` con su `status`; `CongeladoError` lo sigue resolviendo el manejador global (409).
  Con algo escrito, `_pedir_recalculo_seguido(doc, MOTIVO_EDICION_CELDA, actor)` por
  documento y `recalculo = peor_estado(...)` (R23); si no, `None`. INFO `[celda]` (R24).
- `/api/undo`: `undo_last(actor=_actor(request))`; si `action == "celda_edit"`, recálculo
  seguido de cada `document_ids` con `MOTIVO_DESHACER_CELDA` (R27), como hoy con la fecha.

## 7. JS · IIFE «Matriz de obra» de `static/app.js`

Dos funciones **puras a dos espacios de sangría** dentro de la IIFE (las extrae el test con
la regex de F-042) y el manejador `dblclick` reescrito sobre ellas:

- `camposCelda(regs)` → lista de `{id|null, tipo, etiqueta, valor, congelada, nueva}`: una
  por reg (R1) y, si no hay todas congeladas, las nuevas de R2. `[]` de nuevas si todas
  congeladas (R3).
- `cuerpoCelda(campos, valores)` → `null` si no hay nada que enviar (R6) o el cuerpo de R7.
- El popup añade la nota de R5 (`.mxe-nota`) y rótulos «(nueva)» (`.mxe-nueva`). Guardar:
  `fetch` → `MotivoHttp.lanzarSiFalla` → R8. Sin `Promise.all`.

## 8. Por qué materializar (DA3) y qué hace sv3 después

Lo escrito pasa a ser «lo del parte» para sv3: una base sin `horas_orig` no se restaura y
una extra explícita no se borra ni pertenece a la pareja (`es_miembro`, F-037). sv3 sigue
aplicando su regla de jornada en la pasada siguiente (E5, E8): R5 lo avisa y el recálculo
pedido (DA4) lo enseña en segundos. En F-045 las extras explícitas cuentan en el peso de
su obra: materializar puede mover algo el reparto entre obras de ese día (riesgo §12).

## 9. Tests (sin red ni BBDD real; nombres `test_f049_rN_...`)

- Núcleo: tabla de E1–E8 sobre `planificar_celda` (plan esperado), cada rama de error de
  R11–R13 con su `status`, plantilla de R19, materializar solo parejas tocadas (R18).
- Repositorio/ruta (SQLite, `sembrar_parte`, publicador falso que anota mensajes): E2 crea
  la ordinaria con contexto, partida y código del matcher falso (R20, R21); E4 deja
  `horas_orig` NULL y `extra_auto` False (R18); 409 congelada y en espera sin escribir
  (R14, R15; contar filas antes/después); 409 por `antes` obsoleto y por línea nueva
  aparecida (R12); atomicidad forzando un fallo en la creación (R16); recálculo por
  documento con motivo y `recalculo` null sin cambios (R23); fallo de cola no deshace;
  `celda_edit` y su deshacer (R25–R27) y `registro_edit` sigue sin marcas (R28); `regs`
  con `a` (R10); leyenda (R9).
- JS en node: `camposCelda` para 1 línea, 2 (n + `extra_auto`), 3, todas congeladas, solo
  extras; `cuerpoCelda` (vacíos, 0, sin cambios); popup con DOM falso: una sola petición, el
  aviso de `fallo`, el motivo en el título (R8). `node --check static/app.js`.
- Raíz: `clasificar` de sv3 da `recalcular` con los motivos nuevos (R30).
- Suites de F-004, F-025, F-042, F-043 sin cambios (R29).

## 10. Verificaciones manuales (humano)

- **M1 · antes de implementar**: confirmar que la pantalla es la matriz de obra (doble
  clic) y si con solo ordinarias ve hoy la «Extra» a 0 (§2). Si no, se revisa R2.
- **Despliegue solo de sv4**: `.\redeploy_partes.ps1 -Solo sv4` desde `infra/` (sv3 ya
  acepta cualquier motivo). Lo lanza el humano.
- **M2**: celda con solo extra 10 (no congelada) → Ord. (nueva) 8, Extra 2 → «recalculando…»
  y, tras «Actualizar», 8+2; en Líneas, la ordinaria nueva con código y partida.
- **M3**: solo ordinarias 8 → Extra (nueva) 2 → 8+2 estable tras el recálculo.
- **M4**: pareja 8 + 2 (jornada) → Extra 3 → 8+3. Solo lectura en `partes`:
  `SELECT id, tipo_hora, horas, horas_orig, extra_auto FROM parte_registros WHERE id IN (…);`
- **M5**: celda congelada sin «Guardar»; parte en espera ⇒ mensaje de 409 en el popup.
- **M6**: «Deshacer» tras M2 → extra a 10 y la ordinaria nueva en la Papelera.

## 11. Solapes y orden

- **F-046** (rama con T22 de mutación pendiente) toca `obra_detail.html` (`data-reparto` en
  el mismo `<td>`), `recalculo_publisher.py` (`MOTIVO_REAJUSTE`), `app.py`,
  `parte_repository.py` y `app.js`. Su «Aplicar» (R33) exige que el grupo no tenga líneas
  nuevas: una línea creada aquí invalida un reparto pendiente y la pasada pedida lo rehace.
- **F-047** (spec aprobada) cambia el motivo de la espera: este diseño solo usa la guarda
  `_exigir_sin_recalculo`, así que hereda su texto.
- **F-048** (en especificación) convierte en ingesta las filas de solo extras en laborable;
  F-049 es la vía manual para el resto. Sin ficheros comunes previstos salvo
  `features.json`.
- **Orden**: F-046 → F-047 → F-049. T1 fusiona `dev` en la rama antes de tocar código; si
  lo fusionado contradice §4–§7, `blocked` y se reescribe la spec.

## 12. Riesgos y alternativas descartadas

- **Espera tras guardar** (DA4-A): otra celda del mismo parte (mismo día, otro trabajador)
  da 409 durante la pasada (22–39 s medidos en F-047). Es el precio de no dejar aprobar a
  medias.
- **Reparto entre obras**: materializar convierte `extra_auto` en explícita y su obra pesa
  más en F-045 ese día. Totales intactos.
- **Línea nueva con `line_index` propio**: no hereda una pareja ajena (F-037); queda al
  final en las listas ordenadas por `line_index`.
- **Ruta `/extra` sin uso** desde el editor (DA2): queda por sus tests; retirarla es otra
  feature.
- Descartadas: encadenar `PATCH`+`POST` como hoy (no atómico, sin CAS); materializar la celda
  entera (fija parejas que nadie tocó); calcular la jornada en sv4 para avisar con cifras
  (duplicaría sv3); borrar a la papelera al poner 0 (contra la regla «en Sigrid nunca se
  borra, se pone a 0»).

## 13. Decisiones abiertas (humano)

- **DA1 · Alcance**: solo el popup de la matriz de obra; sin editor en el calendario de
  trabajador, ni en celda vacía o con solo incidencia (para eso, «+ Nuevo»). *Recomendado.*
- **DA2 · Ruta nueva atómica** `POST /api/matriz/celda` con CAS (`antes`); `/extra` y
  `PATCH` se quedan como están. *Recomendado.*
- **DA3 · Lo escrito manda**: materializar las parejas tocadas; sv3 sigue ajustando la
  jornada (E5). Alternativa: como hoy (se pierde). *Recomendado materializar.*
- **DA4 · Recálculo al guardar**: A) seguido con espera (F-043) *recomendado*; B) ninguno,
  hasta la siguiente ingesta; C) pedido sin espera (sin 409, pero aprobable a medias).
- **DA5 · Poner a 0 deja la línea a 0** (no papelera); nueva a 0 no crea nada. *Recomendado.*
- **DA6 · Plantilla y destino**: primera no congelada (ordinaria antes), su documento y un
  `line_index` nuevo. *Recomendado.*
- **DA7 · Contexto de la nueva**: clona también la partida (hoy la extra nueva nace sin ella);
  código como hoy (extra) y como «+ Nuevo» (ordinaria). *Recomendado.*
- **DA8 · Deshacer**: restaura horas y marcas, manda las creadas a la papelera firmadas por
  quien deshace (`undo_last(actor=…)`, lo que obliga a los dos dobles de §3) y recalcula.
  *Recomendado.* Alternativa: no deshacer las creadas (E2 dejaría 8 + 10).
- **DA9 · Rigor crítico**: escribe horas que acaban en Sigrid y nómina y toca marcas que
  gobiernan el recálculo de sv3. Alternativa: estándar.
- **DA10 · Rangos**: ordinaria 0–24, extra −24–24, ordinaria nueva > 0. *Recomendado.*
