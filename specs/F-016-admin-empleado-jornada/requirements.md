<!-- specs/F-016-admin-empleado-jornada/requirements.md -->
# F-016 · Pantalla de administración de `empleado_jornada` (sv4) — Requisitos

> **De dónde viene**: estudio **F-012** (decisión **D5**: las excepciones de
> jornada se mantienen desde una pantalla del portal) y **F-015 R27**, que
> reservó explícitamente para esta feature *las validaciones de negocio y la
> UI*. F-015 crea la tabla `empleado_jornada` vacía y solo se defiende
> ignorando con WARNING una fila mal cargada; hasta esta feature, las filas
> se cargan por SQL manual del humano.
>
> **Prerrequisito duro**: `feature/F-015-jornada-semanal-candef` mergeada en
> `dev`. Sin ella no existen ni la tabla, ni `EmpleadoJornadaOrm`, ni el
> proveedor con TTL de sv4. Ver `design.md` §11 (riesgo D1).
>
> **Semántica heredada que NO se reabre** (F-015 §6 y su duda 4, aceptada por
> el humano el 2026-08-19): la vigencia es el intervalo semiabierto
> `desde ≤ d < hasta`; `desde` es **inclusivo** y `hasta` es **EXCLUSIVO**;
> `hasta` nulo es vigencia abierta. Una vigencia «hasta el 31/07» se almacena
> como `hasta = 2026-08-01`. R7 existe para que el humano no tenga que saber
> esto.

## Glosario de esta spec

- **Fila** — un registro de `empleado_jornada`.
- **Patrón** — los siete valores `h_lun … h_dom`. O están los **siete**, o no
  hay patrón (los siete a `NULL`).
- **`S`** — `jornada_semanal` de la fila.
- **Último día incluido** — la fecha que ve y escribe el humano en el
  formulario. Se traduce a `hasta = último día incluido + 1 día`.
- **Actor** — la identidad que se sella en `created_by` / `updated_by`
  (ver R13; hoy sv4 no lee Easy Auth, ver `design.md` §5.4).
- **Fila vigente en `d`** — `is_active` verdadero y `desde ≤ d` y
  (`hasta` nulo o `d < hasta`).

---

## Alcance y límite de servicio

- **R1** (ubicuo). F-016 debe operar **exclusivamente sobre sv4**
  (`services/partes-front/`) y **sobre el schema tal como lo dejó F-015**: no
  añade, quita ni cambia ninguna columna de `empleado_jornada`, no toca
  ninguna de las dos copias de `infrastructure/database/orm_models.py` y no
  modifica ningún fichero de sv3, sv1, sv2, sv5 ni de `infra/`.
  - *Criterios de aceptación*: `EmpleadoJornadaOrm.__table__.columns` expone
    exactamente las **16** columnas declaradas por F-015 (`id`, `dni_norm`,
    `jornada_semanal`, `h_lun`…`h_dom`, `desde`, `hasta`, `origen`, `nota`,
    `is_active`, `created_at_utc`, `created_by`, `updated_at_utc`,
    `updated_by`), con los mismos tipos y `nullable`; el guardián de F-010
    (`tests/test_f010_orm_models_gemelos.py`) sigue en verde **sin haberse
    modificado**; el diff de la rama no toca ningún fichero fuera de
    `services/partes-front/`, `specs/F-016-*`, `progress/` y `docs/`.
  - *Test*: `test_f016_r1_schema_intacto`.

## Listado

- **R2** (dirigido por evento). CUANDO el usuario pide
  `GET /admin/jornadas`, el sistema debe devolver HTML 200 con **todas** las
  filas de `empleado_jornada` —activas e inactivas— ordenadas por `dni_norm`
  ascendente y, dentro de cada DNI, por `desde` **descendente**, mostrando
  por fila: DNI normalizado, `S` (o «—»), el patrón como siete valores (o
  «—»), la vigencia **en formato inclusivo** (`desde` … último día incluido,
  o «sin fin»), `origen`, `nota`, el estado (`activa` / `inactiva`) y la
  auditoría (`created_by` + `created_at_utc`, y `updated_by` +
  `updated_at_utc` si los hay).
  - *Criterios*: con la tabla vacía, la página responde 200 y muestra el
    estado vacío, sin traza ni error; con tres filas de dos DNIs distintos,
    el orden del HTML es el declarado; una fila con `hasta = 2026-08-01` se
    pinta como último día incluido `2026-07-31`; una fila con `hasta` nulo se
    pinta «sin fin»; una fila con `is_active` falso aparece marcada como
    inactiva y **no** desaparece del listado.
  - *Test*: `test_f016_r2_listado`.

## Alta, edición, cierre y papelera lógica

- **R3** (dirigido por evento). CUANDO el usuario envía un alta válida a
  `POST /api/admin/jornadas`, el sistema debe insertar una fila con los
  valores enviados, `origen = 'manual'`, `is_active` verdadero,
  `created_at_utc` = instante UTC en ISO-8601 y `created_by` = actor; y
  responder HTTP 200 con `{"ok": true, "id": <id nuevo>}`.
  - *Criterios*: la fila existe en BBDD con esos valores; `updated_at_utc` y
    `updated_by` quedan a `NULL` en el alta; `origen` es `manual` **aunque el
    cliente mande otra cosa en el cuerpo** (el campo no es del cliente).
  - *Test*: `test_f016_r3_crear`.

- **R4** (dirigido por evento). CUANDO el usuario envía una edición válida a
  `PATCH /api/admin/jornadas/{id}`, el sistema debe sobrescribir `S`, el
  patrón, `desde`, `hasta` y `nota` con lo enviado, sellar `updated_at_utc` y
  `updated_by` = actor, y **no** modificar `id`, `dni_norm`, `origen`,
  `created_at_utc` ni `created_by`; y responder `{"ok": true, "id": <id>}`.
  - *Criterios*: editar una fila con patrón y mandar el patrón vacío deja los
    siete a `NULL` (se puede quitar el patrón); `created_by` conserva su
    valor original después de una edición hecha por otro actor; `dni_norm`
    enviado en el cuerpo de un PATCH se **ignora** (cambiar de trabajador es
    cerrar una fila y crear otra, no editar).
  - *Test*: `test_f016_r4_editar`.

- **R5** (dirigido por evento). CUANDO el usuario cierra una vigencia con
  `POST /api/admin/jornadas/{id}/cerrar` indicando el **último día incluido**
  `u`, el sistema debe guardar `hasta = u + 1 día`, dejar `is_active`
  verdadero, sellar `updated_at_utc` / `updated_by` y responder
  `{"ok": true, ...}`.
  - *Criterios*: cerrar con `u = 2026-07-31` guarda `hasta = 2026-08-01`;
    cerrar una fila ya cerrada la re-cierra con la fecha nueva; cerrar con
    `u` anterior a `desde` se rechaza por R11 y no escribe nada.
  - *Test*: `test_f016_r5_cerrar`.

- **R6** (dirigido por evento). CUANDO el usuario desactiva una fila
  (`POST /api/admin/jornadas/{id}/desactivar`), el sistema debe poner
  `is_active` a falso **sin borrado físico** (semántica 8 de
  `docs/ARCHITECTURE.md`) y sellar la auditoría; y CUANDO la reactiva
  (`POST /api/admin/jornadas/{id}/reactivar`), debe volver a ponerla activa
  **solo si no solapa** con otra fila activa del mismo DNI (R12).
  - *Criterios*: tras desactivar, la fila sigue en la tabla y desaparece de
    lo que lee el resolutor de F-015; reactivar una fila cuya vigencia se
    solapa con otra activa devuelve 409 y **la deja inactiva**; reactivar sin
    solape la deja activa; ningún endpoint de esta pantalla ejecuta `DELETE`.
  - *Test*: `test_f016_r6_papelera_logica`.

- **R7** (ubicuo). El sistema debe hablar con el humano en **último día
  incluido** y almacenar en **exclusivo**: el formulario y el listado
  muestran y aceptan el último día incluido, y la conversión
  (`hasta = último día incluido + 1 día`, y a la inversa al pintar) ocurre
  **solo** en la capa web. «Sin fecha de fin» equivale a `hasta = NULL` en
  los dos sentidos.
  - *Criterios*: alta con último día incluido `2026-07-31` ⇒ BBDD
    `hasta = '2026-08-01'`; esa misma fila releída por el listado se pinta
    `2026-07-31`; alta marcando «sin fin» ⇒ `hasta` es `NULL` y se pinta «sin
    fin»; el par ida-y-vuelta es estable para 366 fechas consecutivas
    (incluye cambio de mes, de año y 29 de febrero).
  - *Test*: `test_f016_r7_hasta_exclusivo`.

## Validaciones de negocio (lo que F-015 dejó a F-016, su R27)

Todas las validaciones ocurren **antes** de escribir. En todos los casos de
R8–R12 la respuesta lleva `{"ok": false, "error": "<motivo en español>"}` y
**la BBDD queda intacta** (un 4xx que ya haya escrito no sirve de nada, misma
regla que F-004).

- **R8** (comportamiento no deseado). SI una fila no trae **ni** `S` **ni**
  patrón completo, ENTONCES el sistema debe rechazarla con HTTP **422** y no
  escribir nada.
  - *Criterios*: cuerpo sin `S` y con los siete días vacíos ⇒ 422; solo `S`
    ⇒ se acepta; solo patrón completo ⇒ se acepta; `S` **y** patrón ⇒ se
    acepta (F-015 R16 da prioridad al patrón, y esta pantalla no la cambia:
    solo lo advierte en el aviso de la respuesta).
  - *Test*: `test_f016_r8_semanal_o_patron`.

- **R9** (comportamiento no deseado). SI el patrón viene **incompleto**
  (entre uno y seis valores) o alguna de sus horas está fuera del rango
  `[0, 24]` o no es numérica, ENTONCES el sistema debe rechazar con HTTP
  **422**, nombrando el día ofensor, y no escribir nada.
  - *Criterios*: seis días con valor y uno vacío ⇒ 422 con el día vacío en el
    mensaje; `h_mie = 25` ⇒ 422; `h_sab = -1` ⇒ 422; `h_dom = 0` ⇒ válido
    (domingo sin jornada es el caso normal); `h_vie = "6,5"` ⇒ válido (coma
    decimal, criterio ES) y se guarda `6.5`.
  - *Test*: `test_f016_r9_horas_patron`.

- **R10** (comportamiento no deseado). SI `S` no es numérica o está fuera de
  `(0, 168]`, ENTONCES el sistema debe rechazar con HTTP **422** y no
  escribir nada.
  - *Criterios*: `S = 0` ⇒ 422; `S = -5` ⇒ 422; `S = 169` ⇒ 422; `S = 42`
    ⇒ válido; `S = "42,5"` ⇒ válido y se guarda `42.5`.
  - *Test*: `test_f016_r10_semanal_rango`.

- **R11** (comportamiento no deseado). SI `desde` falta o no es una fecha ISO
  `YYYY-MM-DD` válida, o el último día incluido es **anterior** a `desde`
  (es decir, `hasta ≤ desde`), ENTONCES el sistema debe rechazar con HTTP
  **422** y no escribir nada.
  - *Criterios*: `desde` vacío ⇒ 422; `desde = '2026-02-30'` ⇒ 422;
    `desde = '31/07/2026'` ⇒ 422 (el formulario usa `<input type="date">`,
    que envía ISO); último día incluido `2026-06-30` con `desde =
    2026-07-01` ⇒ 422; último día incluido **igual** a `desde` ⇒ **válido**
    (vigencia de un solo día, `hasta = desde + 1`).
  - *Test*: `test_f016_r11_fechas`.

- **R12** (comportamiento no deseado). SI la fila resultante de un alta, una
  edición o una reactivación **solapa** la vigencia de otra fila **activa**
  del mismo `dni_norm`, ENTONCES el sistema debe rechazar con HTTP **409**,
  identificar en la respuesta la fila en conflicto
  (`{"conflicto": {"id": N, "desde": "...", "hasta_inclusivo": "..."}}`) y no
  escribir nada. El sistema **nunca** ajusta automáticamente la otra fila.
  - *Criterios*: intervalos semiabiertos `[desde, hasta)` con `hasta` nulo =
    infinito; **contiguas no solapan** (`hasta` de una igual a `desde` de la
    otra ⇒ se acepta: es el caso normal de encadenar vigencias); dos abiertas
    del mismo DNI ⇒ 409; la existente abierta y la nueva anterior y cerrada
    justo antes ⇒ se acepta; al **editar**, la propia fila se excluye de la
    comparación (guardar una fila sin cambios nunca choca consigo misma); las
    filas **inactivas** no cuentan; otro `dni_norm` no cuenta.
  - *Test*: `test_f016_r12_solape`.

- **R18** (ubicuo). El sistema debe normalizar el DNI **con la misma función
  que usa la lectura de F-015** antes de guardarlo en `dni_norm`, de modo que
  una excepción dada de alta desde la pantalla case siempre con el trabajador
  al que se le aplica.
  - *Criterios*: la entrada `« 1234-abcd »` se guarda como `1234ABCD`;
    guardar dos veces el mismo DNI escrito distinto (con y sin guiones,
    minúsculas y mayúsculas, con espacios) produce el **mismo** `dni_norm` y
    por tanto dispara el control de solape de R12; una batería de entradas
    normalizada por la función que usa la pantalla da **carácter a carácter**
    el mismo resultado que la que usa el proveedor de jornadas de sv4 (si
    algún día divergen, este test se pone rojo antes de que nadie lo note en
    producción); un DNI vacío ⇒ 422.
  - *Test*: `test_f016_r18_dni_normalizado`.

- **R19** (opcional / DONDE). DONDE el catálogo de empleados de Sigrid esté
  activo en sv4, SI el DNI del alta no consta en él, el sistema debe
  **guardar igualmente** y devolver en la respuesta un campo `aviso` con el
  texto de que ese DNI no consta en Sigrid.
  - *Criterios*: catálogo activo y DNI desconocido ⇒ 200, fila creada y
    `aviso` presente; catálogo activo y DNI conocido ⇒ 200 sin `aviso`;
    catálogo **apagado** ⇒ 200 sin `aviso` y sin ninguna llamada al cliente
    de Sigrid (la pantalla no depende de que Sigrid esté cableado).
  - *Test*: `test_f016_r19_dni_desconocido_avisa`.

## Auditoría, caché y acceso

- **R13** (ubicuo). Toda escritura de esta pantalla debe dejar **quién y
  cuándo**: `created_at_utc` / `created_by` en el alta y `updated_at_utc` /
  `updated_by` en toda modificación posterior (edición, cierre, desactivar,
  reactivar), con instantes UTC en ISO-8601 y el actor resuelto por un único
  punto del código.
  - *Criterios*: las cuatro operaciones de modificación sellan
    `updated_by`; con la cabecera de Easy Auth presente en la petición se
    sella ese principal; sin ella, se sella `DEFAULT_REVIEWER`; sin ninguno
    de los dos, se sella `NULL` y la operación **no** falla.
  - *Test*: `test_f016_r13_auditoria`.

- **R14** (ubicuo). MIENTRAS los servicios cacheen `empleado_jornada` con
  TTL, la pantalla debe advertirlo de forma **permanente y visible**,
  indicando los minutos reales derivados de `JORNADA_CACHE_TTL_S`, y debe
  invalidar el proveedor de jornadas **de su propio proceso** tras cada
  escritura con éxito.
  - *Criterios*: el HTML de la página contiene el aviso con el número de
    minutos calculado desde `settings.jornada_cache_ttl_s` (600 s ⇒ «10
    minutos»), no un literal cableado; tras un alta, una edición, un cierre,
    una desactivación y una reactivación con éxito se ha llamado **una vez**
    a `invalidar()` del proveedor; tras un rechazo (422 / 409) **no** se
    llama; sin proveedor inyectado (`None`), las escrituras siguen
    funcionando sin error.
  - *Test*: `test_f016_r14_cache_y_aviso`.

- **R15** (opcional / DONDE). DONDE `JORNADAS_ADMIN_ENABLED` sea falso, el
  sistema debe responder **404** en la página y en **todos** los endpoints de
  la pantalla, y no debe pintar su enlace en la barra de navegación. La
  comprobación debe estar escrita **una sola vez**, para que F-008 la
  sustituya por la comprobación de rol tocando un solo punto.
  - *Criterios*: con la variable a falso, `GET /admin/jornadas` y los cinco
    endpoints devuelven 404 y ninguna otra ruta del portal cambia de
    comportamiento; con la variable a verdadero (**default**), todo responde;
    el enlace «Jornadas» aparece en la barra solo en el segundo caso; hay
    exactamente **una** función que decide el acceso.
  - *Test*: `test_f016_r15_puerta_de_acceso`.

- **R16** (comportamiento no deseado). SI el `{id}` de un endpoint de
  modificación no existe en `empleado_jornada`, ENTONCES el sistema debe
  responder **404** con `{"ok": false, "error": ...}`, nunca 500 ni una traza.
  - *Criterios*: `PATCH`, `cerrar`, `desactivar` y `reactivar` sobre un id
    inexistente ⇒ 404 con cuerpo JSON; un id no numérico ⇒ 422 de FastAPI
    (validación de ruta), nunca 500.
  - *Test*: `test_f016_r16_no_encontrada`.

- **R17** (ubicuo). Ni la página ni sus endpoints deben tocar la red: toda la
  validación es local y la única dependencia externa es la BBDD `partes`.
  - *Criterios*: la app construida **sin** cliente de Sigrid, **sin** cliente
    de Sesame, **sin** colas y **sin** cliente de sv5 sirve la página y las
    cinco operaciones enteras; ningún endpoint de esta pantalla llama a
    `sigrid-api`, a Graph, a Sesame ni a sv5; toda la suite de F-016 corre
    sobre SQLite en memoria y `Settings(_env_file=None)`.
  - *Test*: `test_f016_r17_sin_red`.

---

## Trazabilidad requisito → test

| Requisito | Test (nombre de función) | Fichero |
|---|---|---|
| R1 | `test_f016_r1_schema_intacto` | `tests/test_f016_vista_admin_jornadas.py` |
| R2 | `test_f016_r2_listado` | `tests/test_f016_vista_admin_jornadas.py` |
| R3 | `test_f016_r3_crear` | `tests/test_f016_endpoints_admin_jornadas.py` |
| R4 | `test_f016_r4_editar` | `tests/test_f016_endpoints_admin_jornadas.py` |
| R5 | `test_f016_r5_cerrar` | `tests/test_f016_endpoints_admin_jornadas.py` |
| R6 | `test_f016_r6_papelera_logica` | `tests/test_f016_endpoints_admin_jornadas.py` |
| R7 | `test_f016_r7_hasta_exclusivo` | `tests/test_f016_validacion_jornada_admin.py` |
| R8 | `test_f016_r8_semanal_o_patron` | `tests/test_f016_validacion_jornada_admin.py` |
| R9 | `test_f016_r9_horas_patron` | `tests/test_f016_validacion_jornada_admin.py` |
| R10 | `test_f016_r10_semanal_rango` | `tests/test_f016_validacion_jornada_admin.py` |
| R11 | `test_f016_r11_fechas` | `tests/test_f016_validacion_jornada_admin.py` |
| R12 | `test_f016_r12_solape` | `tests/test_f016_validacion_jornada_admin.py` (unidad) + `tests/test_f016_endpoints_admin_jornadas.py` (409 por HTTP) |
| R13 | `test_f016_r13_auditoria` | `tests/test_f016_endpoints_admin_jornadas.py` |
| R14 | `test_f016_r14_cache_y_aviso` | `tests/test_f016_vista_admin_jornadas.py` |
| R15 | `test_f016_r15_puerta_de_acceso` | `tests/test_f016_vista_admin_jornadas.py` |
| R16 | `test_f016_r16_no_encontrada` | `tests/test_f016_endpoints_admin_jornadas.py` |
| R17 | `test_f016_r17_sin_red` | `tests/test_f016_vista_admin_jornadas.py` |
| R18 | `test_f016_r18_dni_normalizado` | `tests/test_f016_validacion_jornada_admin.py` |
| R19 | `test_f016_r19_dni_desconocido_avisa` | `tests/test_f016_endpoints_admin_jornadas.py` |

**Fase RED obligatoria** (rigor `estandar`) con la traza real pegada en
`progress/impl_F-016.md` para **R7, R12, R14 y R15**: son los cuatro donde un
test que pasa por casualidad no probaría nada (la conversión de fechas, el
solape, la invalidación de caché y la puerta de acceso).

## Fuera de alcance (explícito)

- **Cambiar la regla de jornada**: `jornada_resolver.py` (ninguna de las dos
  copias) ni cómo F-015 aplica las excepciones. Esta pantalla **solo edita
  filas**.
- **sv3**: no se toca ni un fichero. La conciliación sigue leyendo la tabla
  con su propio TTL (ver R14 y `design.md` §7).
- **Roles** (F-008): esta feature deja el punto único donde engancharlos
  (R15), no los implementa. Ver `design.md` §13, duda 1.
- **Leer la identidad real de Easy Auth en el resto del portal**
  (`approved_by`, `deleted_by`, …): F-016 introduce el helper solo para sus
  columnas. Ver `design.md` §13, duda 2.
- **Origen `sigrid` / `sesame`**: la columna existe desde F-015 y esta
  pantalla escribe siempre `manual`. Importar excepciones de esas fuentes es
  otra feature.
- **Buscador / combo de trabajadores contra Sigrid** para elegir el DNI: se
  queda en el aviso de R19. Ver `design.md` §13, duda 3.
- **Invalidar la caché de sv3 (o la de otras réplicas de sv4) desde la
  pantalla**: exigiría una llamada entre servicios que `docs/ARCHITECTURE.md`
  no contempla. Ver `design.md` §7.
- **Borrado físico de filas**: prohibido por la semántica 8 de
  `docs/ARCHITECTURE.md`. La papelera es lógica (R6).
