# F-069 · Diseño técnico

## 1. Límite de servicio

La raíz está en **sv3**, dueño único del cómputo de extras (`docs/ARCHITECTURE.md`, semántica
de jornada, F-037, F-045). sv4 solo lee y valida el ámbito; no hay lógica que duplicar ni
copia gemela que tocar. El mensaje de sv4 (DA1) es presentación de un 422 que ya existe.
Nada pide otro microservicio. sv5, colas, Sigrid y el esquema quedan igual.

## 2. Forma nueva de `_pasada`

Hoy (`recurso_conciliador.py:459-552`):

```
revert_extras_auto()   -> COMMIT 1 (borra extras, restaura bases)
materializar_repartos()-> commits propios (solo congeladas)
fetch_registros_para_recurso()
... Sigrid: índice, reshor, hmo, calendario ...
apply_recurso_matches(updates) -> COMMIT 2
apply_extras_splits(splits)    -> COMMIT 3 (extras con ids nuevos)
```

Con F-069:

```
materializar_repartos()        -> igual (R12)
lectura = leer_pasada()        -> solo lee; vista revertida + huellas (R7, R11)
... Sigrid y cálculo, sobre lectura.registros (sin cambios) ...
resumen = escribir_pasada(lectura, updates, splits) -> UN COMMIT (R8-R16)
```

`_guardar_repartos`, `_marcar_partes_degradados` y `_marcar_revision` siguen después, en sus
transacciones: no tocan horas ni extras. El orden «materializar antes de leer» de F-046 R15 se
mantiene; lo que desaparece es el revert previo.

## 3. Núcleo puro: `application/services/pareja_extra.py` (se amplía)

Se añaden funciones puras; `plan_revert`, `clave_pareja`, `es_miembro` y `claves_congeladas`
**no cambian** (R17).

- `vista_revertida(filas: list[dict], plan: PlanRevert) -> list[dict]`: copia de `filas` sin
  las de `plan.borrar` y con `horas = horas_orig`, `horas_orig = None` en las de
  `plan.restaurar`. No muta la entrada.
- `CAMPOS_HUELLA = ("registro_id", "horas", "horas_orig", "tipo_hora", "extra_auto",
  "sigrid_estado", "deleted_at_utc", "doc_approved", "doc_activo")`.
- `huellas_por_clave(filas: Iterable[Mapping]) -> dict[Clave, frozenset[tuple]]`: por clave,
  el conjunto de tuplas `CAMPOS_HUELLA` de sus **miembros** (`es_miembro`). Las horas se
  redondean a 6 decimales para que un float de ida y vuelta no cuente como cambio.
- `emparejar_extras(splits: list[dict], candidatas: list[int]) -> tuple[list[tuple[dict,
  int | None]], list[int]]`: R3 y R5. Splits por `normal_id`, candidatas por id; un split con
  `id` propio va con `None` (extra nueva con ese id) y no consume candidata. Devuelve los
  pares y las candidatas sobrantes (a borrar).

`LecturaPasada` (dataclass congelada, mismo módulo): `registros: list[dict]` (vista
revertida, lo que hoy devuelve `fetch_registros_para_recurso` tras el revert) y `huellas:
dict[Clave, frozenset]` (del estado **crudo** leído, antes del revert en memoria).

## 4. Repositorio: `infrastructure/database/sqlalchemy_parte_repository.py`

### 4.1 `leer_pasada() -> LecturaPasada` (nuevo)

Una sesión de solo lectura. Hace la consulta de hoy de `fetch_registros_para_recurso` (partes
activos) añadiendo `ParteDocumentOrm.is_active` como `doc_activo` (siempre `True` aquí, pero
la huella lo lleva para R13). Con esas filas:

1. `plan = plan_revert(_fila_pareja(...))` — mismo constructor que hoy.
2. `huellas = huellas_por_clave(crudas)`.
3. `registros = vista_revertida(crudas, plan)` y, sobre ellos, `congelada_por_pareja` como hoy
   (`claves_congeladas` de la vista). R11: el resultado es el mismo que hoy daban revert +
   fetch, porque `plan_revert` solo borra extras no congeladas y restaura bases no
   congeladas, que no aportan a `claves_congeladas`.

`fetch_registros_para_recurso()` pasa a ser `return self.leer_pasada().registros` (R18).

### 4.2 `escribir_pasada(lectura, updates, splits) -> ResumenEscritura` (nuevo)

`lectura` puede ser `None` (sin comprobación de huella: lo usan los envoltorios de §4.4).
Todo en UNA sesión y UN `commit` (R8); sin red (R10); si algo lanza, `rollback` y se propaga
(R16).

1. **Leer y bloquear** (R15). Documentos afectados = los de las filas candidatas al revert
   (`extra_auto` o `horas_orig` no nulo, la consulta de hoy de `revert_extras_auto`) más los
   de las bases de `splits` y de `updates`. Se leen todas las filas de esos documentos con su
   `approved` e `is_active`, con `.with_for_update(of=ParteRegistroOrm)` en PostgreSQL (en
   SQLite se omite). Orden de bloqueo: por `id`, para no cruzarse con otra transacción.
2. **Plan fresco**: `plan = plan_revert(...)` sobre esas filas (todas, también partes
   inactivos, como hoy).
3. **Parejas cambiadas** (R13, R14): con `lectura`, una clave de `lectura.huellas` cuya
   huella actual (`huellas_por_clave` de las filas bloqueadas) difiere ⇒ `cambiadas`. Una
   pareja que ahora tiene un miembro congelado también difiere (cambió `sigrid_estado` o
   `approved`). Las filas de una clave cambiada **no se tocan**: ni revert, ni casado, ni
   split. WARNING `[repo] pareja cambiada durante la pasada: documento=… linea=… fecha=…; se
   recalcula en la siguiente` (sin nombres ni DNI).
4. **Casados**: lo de `apply_recurso_matches` de hoy, saltando filas de claves cambiadas.
   Va antes de los splits para que la extra se rellene con el recurso/`hmo_ide` nuevo de su
   base, igual que hoy (`_extra_de` clonaba la base ya casada).
5. **Revert**: bases de `plan.restaurar` ⇒ `horas = horas_orig`, `horas_orig = None`.
   Extras de `plan.duplicadas` ⇒ `delete` (F-037 R6, como hoy).
6. **Splits por pareja**: candidatas de una clave = sus extras de `plan.borrar` que no son
   duplicadas. `emparejar_extras(splits_de_la_clave, candidatas)`:
   - base: `if base.horas_orig is None: base.horas_orig = s["horas_orig"]`; `base.horas =
     s["horas_norm"]` (lo de hoy);
   - par con candidata ⇒ `_rellenar_extra(extra, base, s)` (R2, mismo `id`);
   - par sin candidata ⇒ `session.add(_extra_de(base, s))` (con `s["id"]` si viene, R5);
   - candidatas sobrantes y extras de claves sin split ⇒ `delete` (R4).
   Un split cuya base no existe se salta, como hoy.
7. `commit`; `_log_plan_revert(plan)` como hoy; devuelve `ResumenEscritura(actualizados,
   aplicados, nuevas, reutilizadas, borradas, parejas_cambiadas)`.

### 4.3 `_campos_extra` / `_extra_de` / `_rellenar_extra`

`_extra_de` se parte en `_campos_extra(normal, s) -> dict` (la lista de campos que hoy clona,
literal) y el constructor. `_rellenar_extra(extra, normal, s)` deja **toda columna de
`ParteRegistroOrm` salvo `id`** con el valor con que `_extra_de` la insertaría hoy: los de
`_campos_extra`, los `sigrid_*` de `s["sigrid"]` si vienen y, el resto, su `default` del ORM
o `None` (DA2). Así una extra reutilizada es indistinguible de una recién creada salvo el
`id` (lo vigila un test columna a columna).

### 4.4 Envoltorios (R18)

- `revert_extras_auto()` ⇒ `escribir_pasada(None, [], []).borradas`. Sin splits todas las
  candidatas sobran: borra y restaura exactamente lo de hoy.
- `apply_extras_splits(splits)` ⇒ conserva su contrato de hoy (inserta sin revertir; lo usan
  los tests de F-046 R15 tras un revert explícito). Se implementa con `_extra_de` como hoy;
  no reutiliza (no hay candidatas porque no revierte).
- `apply_recurso_matches(updates)`: sin cambios (lo usan tests y no la pasada).

## 5. Conciliador: `application/services/recurso_conciliador.py`

`_pasada`: se quita la llamada a `revert_extras_auto()`; `registros = lectura.registros` con
`lectura = self._repository.leer_pasada()` tras `materializar_repartos`; al final, en vez de
`apply_recurso_matches` + `apply_extras_splits`, `resumen = escribir_pasada(lectura, updates,
splits)`. `actualizados = resumen.actualizados`, `extras_reclasificadas = resumen.aplicados`
(R6). El log `[recurso-concil] registros=…` añade `extras_nuevas`, `extras_reutilizadas`,
`extras_borradas` y `parejas_cambiadas` (solo log; el dict devuelto no cambia de claves, para
F-042, F-045 y F-046 R19). El comentario de cabecera de `_pasada` y el docstring de
`_reclasificar_extras_jornada` («la BD la toca el repositorio, que antes revierte») se
actualizan. Sin cambios en `_reclasificar_extras_jornada`, `_lineas_dia` ni el reparto.

## 6. Doble de tests: `tests/dobles.py`

`RepositorioFake` gana `leer_pasada()` (devuelve `LecturaPasada(list(self.registros), {})`,
anota `"leer"` en `orden` y suma `revertidos`) y `escribir_pasada(lectura, updates, splits)`
(acumula `matches` y `splits`, anota `"escribir"`). `fetch_registros_para_recurso`,
`apply_*` y `revert_extras_auto` se quedan para los tests que los llaman. Único test que
cambia de expectativa: `test_f046_conciliar.py:608` (`revert` < `materializar`) pasa a
`materializar` < `leer` < `escribir`, que es lo que pide F-046 R15 («antes de leer»).

## 7. sv4 (solo con DA1 aprobada)

- `services/partes-front/infrastructure/database/parte_repository.py`: nuevo
  `registro_ids_existentes(ids: list[int]) -> set[int]` (cualquier fila, papelera incluida),
  por lotes de `LOTE_IDS_CONSULTA` con `_registros_por_ids` o un `select(id)` equivalente.
- `services/partes-front/interface_adapters/web/app.py` (`_validar_ambito`, :2502-2537): si
  `fuera > 0`, `inexistentes = len(set(ids) - existentes)`; si `> 0`, el 422 añade
  `inexistentes` y el texto pasa a «{fuera} línea(s) no son de esta vista: {inexistentes} ya
  no existen porque se están recalculando las extras. Recarga en unos segundos y vuelve a
  seleccionar». Si `inexistentes == 0`, respuesta idéntica a hoy (los tests de F-019/F-022
  no cambian). JS: sin cambios (ya enseña `error`); comprobarlo con `node --check`.
- Dobles de sv4 que implementen `registro_ids_de_obra` ganan `registro_ids_existentes`.

## 8. Ficheros

**Modificar** (sv3): `application/services/pareja_extra.py` (§3),
`infrastructure/database/sqlalchemy_parte_repository.py` (§4),
`application/services/recurso_conciliador.py` (§5), `tests/dobles.py` (§6),
`tests/test_f046_conciliar.py` (solo la aserción de orden).
**Modificar** (sv4, DA1): `infrastructure/database/parte_repository.py`,
`interface_adapters/web/app.py` (§7).
**Modificar** (docs): `docs/ARCHITECTURE.md` — párrafo F-069 junto a F-037/F-045 (extras con
id estable, pasada que escribe en una transacción, `parejas_cambiadas`).
`azure-apps/partes.md`: solo si describe el revert o los ids de extras (grep); el contrato
expuesto no cambia.

**Crear** (tests, `services/partes-persistencia/tests/`):
- `test_f069_pareja_puro.py` — R3, R5, `vista_revertida`, `huellas_por_clave` (puros).
- `test_f069_ids_estables.py` — R1, R2, R4, R6, R18 (SQLite, repositorio y conciliador
  reales con los dobles de `test_f037_dos_pasadas.py`).
- `test_f069_una_transaccion.py` — R7-R11, R16: cuenta `commit`s de sesión con
  `event.listen(Session, "after_commit")` sobre `FabricaSesionSqlite` y, en cada commit de la
  pasada, un lector (otra sesión) comprueba el invariante de pareja; contra el código de hoy
  falla tras el commit del revert (traza RED). R11 compara `leer_pasada().registros` con
  `revert_extras_auto()` + lectura cruda sobre la misma siembra.
- `test_f069_concurrencia_sv4.py` — R13, R14: entre `leer_pasada` y `escribir_pasada` se
  cambia la base (horas, `sigrid_estado = encolado`, papelera, parte aprobado, fila borrada)
  y la pareja queda intacta; las demás se escriben.
- `test_f069_pg_lector_concurrente.py` — M1: se salta sin `F069_PG_URL`; con ella, PostgreSQL
  real, `FOR UPDATE` y un hilo lector en bucle durante 20 pasadas (R9, R15).
- sv4 (DA1): `services/partes-front/tests/test_f069_r20_inexistentes.py` — R20, R21.

## 9. Qué NO se toca

- `esta_congelado`, `ESTADOS_CONGELADOS`, `_congelado` (sv3) y `congelacion.py` (sv4): regla
  gemela (R17). Esta feature solo **lee** la congelación.
- `orm_models.py` (sv3 y sv4): sin columnas nuevas ni índices.
- `plan_revert`, `clave_pareja`, `es_miembro`, `claves_congeladas` (F-037).
- `reparto_ponderado.py`, `reajuste_reparto.py`, `materializar_repartos` (F-045/F-046).
- `persist_parte_pipeline.py`, `despacho.py`: el disparo de la pasada y su globalidad (fuera).
- sv5, sv1, sv2 e `infra/`.

## 10. Riesgos y alternativas

- **Bloqueo más largo**: la transacción de escritura bloquea filas de los documentos con
  parejas y ahora incluye los casados. Mitigación: entra solo con todo calculado (R10), dura lo
  que hoy duran los commits 2 y 3 juntos. sv4 espera milisegundos en sus `UPDATE`.
- **Interbloqueo con sv4**: sv4 escribe pocas filas por transacción; bloquear en orden de `id`
  lo minimiza. Si PostgreSQL aborta por interbloqueo, R16: rollback y reintento del mensaje.
- **Pareja «cambiada» que no se arregla**: queda como estaba (consistente, con su extra vieja)
  hasta la siguiente pasada. Es mejor que hoy, que la dejaba revertida.
- **Emparejamiento por orden** (R3): con varias bases en la misma clave (partidas) un cambio
  de orden podría intercambiar ids entre extras de la misma pareja. Sin una columna de enlace
  base↔extra no hay nada más preciso; añadirla es cambio de esquema (descartado, DA3).
- **Descartado**: guardar `clave → id` y reinsertar con el mismo id tras el borrado (sigue
  habiendo ventana sin fila); `SERIALIZABLE` en toda la pasada (la pasada lee Sigrid durante
  segundos: transacción larga y reintentos); bloquear la pasada contra sv4 con el candado
  consultivo (sv4 no lo toma y meterlo allí es tocar otro servicio).
- **Diferencia con hoy, a sabiendas**: una extra reutilizada conserva su `id`, así que las
  referencias de sv4 por id (`undo_log`, repartos, franquicias, selección en pantalla) siguen
  apuntando a ella. Es el objetivo.
