<!-- specs/F-040-recursos-sin-dni-por-nombre/requirements.md -->
# F-040 · Recursos sin DNI: proponer por nombre, aprender alias por recurso y poder registrarlos — Requisitos

**Servicios: sv3** (casado, conciliador, alias, medición), **sv4** (catálogo,
marca «sin DNI», alias); **sv5 no cambia** (DA3, solo un test). Esquema:
`empleado_alias` gana `recurso_ide` y `empleado_ide` nullable (las dos copias
de `orm_models.py`). sv1 y sv2 no cambian. Rigor **crítico**. Petición del
humano (2026-10-08): «si no hay DNI en el parte o no hay DNI ni en recurso ni
en empleado, que proponga por nombre».

## Contexto (verificado en el código el 2026-10-08)

- sv3 `candidatos_nombre` excluye los recursos sin DNI; `match_nombre` agrupa
  por DNI; el conciliador no da recurso a una línea sin DNI ni ficha.
- sv4 `fetch_recursos_activos` descarta en Python los recursos sin DNI (F-035
  DA3); el alias de Conciliar/reasignar solo se guarda con ficha (`emp["ide"]`).
- sv5 `verificar_recurso` **ya** acepta un `recurso_ide` cuando la línea no
  trae DNI (existe, empresa de la obra, de alta): basta para registrarlos y,
  por decisión del humano (DA3), no se acota.
- Recursos persona de alta sin DNI en ningún sitio (medido 2026-10-08): Porsan
  `MO/0032` y `MO/0033` (obra 0692), empresa 12 (2), 18 (4), 25 (1).

## Glosario

- **Recurso sin DNI**: recurso persona (`res.cla = 1`) cuyo DNI del recurso
  (F-036 DA1: `emp.dni` de la ficha enlazada o, si vacío, `res.cif`) es vacío.
- **Clave de persona**: el DNI del recurso; si no hay, `emp:<conide>` con
  ficha enlazada y `res:<res.ide>` sin ella.
- **Propuesta**: casado que sv3 NO aplica; la línea queda en la cola de
  Conciliar y sv4 ofrece el candidato.

## sv3 · casado por nombre (DA1)

- **R1.** El sistema debe incluir en `candidatos_nombre` los recursos persona de
  alta a la fecha y de la empresa del parte **aunque no tengan DNI**.
- **R2.** `match_nombre` debe agrupar los candidatos por **clave de persona**,
  con el umbral y la regla de empate de hoy: otra clave con puntuación ≥ la
  mejor ⇒ `nombre_ambiguo`.
- **R3.** CUANDO gana por nombre una clave **sin DNI**, el sistema NO debe
  casar: `EmpleadoMatch(method="nombre_sin_dni")` sin `ide` ni `reside`; la
  línea sube `review_required` y queda en la cola de Conciliar.
- **R4.** CUANDO gana por nombre una clave con DNI, el sistema debe casar como
  hoy (`casar_por_dni`); un recurso sin DNI que la empata la deja en
  `nombre_ambiguo`.
- **R5.** R1–R4 deben aplicarse cuando el parte no trae DNI y cuando trae uno
  que Sigrid no conoce; un DNI con recursos persona (`dni_<motivo>`) o conocido
  sin ellos (`dni_sin_recurso`) debe seguir cerrando la línea como hoy.

## sv3 · alias aprendido

- **R6.** `find_empleado_alias` debe devolver también `recurso_ide`.
- **R7.** El DNI del alias debe ser el suyo; si vacío, el de su ficha; si vacío,
  el DNI del recurso de su `recurso_ide`. Con DNI, igual que hoy.
- **R8.** SI el alias no da DNI, ENTONCES el sistema debe resolverlo por clave:
  con `recurso_ide`, `elegir_sin_dni`; sin él y con `ide`, la clave
  `emp:<ide>`. `ok` ⇒ casado con score 1.0 y método `alias` (con ficha) o
  `recurso_nombre` (sin ella); cualquier otro motivo ⇒ `alias_no_valido`, sin
  seguir al nombre.

## sv3 · elección del recurso sin DNI

- **R9.** `IndicePersonas.elegir_sin_dni(ide, empresa, fecha)` debe dar `ok`
  solo si el recurso existe, es persona, no tiene DNI, está de alta a la fecha
  (`de_alta`) y es de la empresa (cualquiera si `None`); si no, `desconocido`
  (no está o no es persona), `con_dni`, `solo_baja` u `otra_empresa`.
- **R10.** CUANDO el conciliador pide `elegir_recurso` con DNI vacío, sin ficha
  (`empleado_ide` None) y con `preferido`, el sistema debe devolver
  `elegir_sin_dni(preferido, …)`. Con DNI, o sin DNI y con ficha (por
  `conide`), sin cambios.
- **R11.** SI `elegir_sin_dni` da `con_dni`, `solo_baja` u `otra_empresa` en el
  conciliador, ENTONCES la línea debe quedar sin recurso y su parte a revisión
  (`MOTIVOS_SIN_RECURSO_A_REVISAR` gana `con_dni`).
- **R12.** Un casado cuyo DNI del recurso es vacío debe guardar `empleado_dni`
  NULL, nunca cadena vacía.
- **R13.** Las líneas congeladas no deben cambiar (`esta_congelado` intacta).

## sv4 · catálogo y Conciliar

- **R14.** `fetch_recursos_activos` debe ofrecer también los recursos persona de
  alta sin DNI, con `dni` None, y loguear cuántos; `_SQL_RECURSOS_ACTIVOS` no
  cambia.
- **R15.** Conciliar (candidatos y buscar), nuevo parte, «+ Añadir línea» y el
  combo del detalle de obra deben marcar esos recursos «sin DNI» donde hoy
  pintan «DNI …».
- **R16.** Elegir un recurso sin DNI debe dejar la línea según `asignacion_de`:
  con ficha, su `ide` y `empleado_dni` NULL; sin ficha, `recurso_manual`,
  `empleado_dni` NULL y `empleado_reside` = el recurso.
- **R17.** CUANDO se confirma en Conciliar o se reasigna con `recurso_ide`, el
  sistema debe guardar el alias **también sin ficha**: `empleado_ide` (o NULL),
  código, nombre, `empleado_dni` (o NULL) y `recurso_ide` = `res.ide`. Por el
  camino de ficha (`ide` sin `recurso_ide`), como hoy con `recurso_ide` NULL.
- **R18.** SI un alias llega sin `empleado_ide` ni `recurso_ide`, ENTONCES
  `upsert_empleado_alias` no debe escribir nada.
- **R19.** El deshacer debe guardar y restaurar `recurso_ide` del alias; un
  snapshot anterior a F-040 (sin la clave) lo restaura a NULL.

## Esquema (`empleado_alias`, sv3 y sv4)

- **R20.** `EmpleadoAliasOrm` debe tener `empleado_ide` nullable y una columna
  nueva `recurso_ide INTEGER NULL`, byte-idéntico en sv3 y sv4.
- **R21.** `ddl_complementario()` debe incluir el `ADD COLUMN IF NOT EXISTS
  recurso_ide` y `DDL_EXTRA_POSTGRES` el `ALTER TABLE empleado_alias ALTER
  COLUMN empleado_ide DROP NOT NULL`; ningún `.sql` de migración ni `UPDATE`
  de filas existentes.

## sv5 · sin cambios (DA3, humano 2026-10-08)

«Si el recurso está casado, sv5 no deberá poner pega a que no tenga DNI.»

- **R22.** (caracterización) sv5 debe verificar una línea sin DNI con
  `recurso_ide` como hoy (existe, empresa de la obra, de alta) y escribirla,
  sin mirar DNI ni clase del recurso; sin recurso ni DNI, «sin recurso casado»
  como hoy. Un test lo fija sin cambiar código.
- **R23–R26.** Retiradas por DA3: ni motivos nuevos, ni `res.cla` en
  `datos_recursos`, ni gemela `elegir_sin_dni` ⇔ `verificar_recurso`, ni su
  guardián.

## Copias de la lista cerrada de `CLAUDE.md`

- **R27.** Los guardianes F-010 (`orm_models`), F-023 (`de_alta`), F-024
  (congelación) y F-036 (persona) deben seguir en verde sin relajarse;
  `CLAUDE.md` debe anotar que `elegir_recurso` (sv3) gana la rama sin DNI de
  R10, sin gemela en sv5 porque sv5 no elige recurso sin DNI.

## Medición de impacto (solo lectura, antes de desplegar)

- **R28.** `medir_casado_recursos.py` debe sumar: en el maestro, la columna
  `sin_dni_sin_ficha` y, por línea, `casado` = `propone_sin_dni` (R3).
- **R29.** La herramienta debe seguir de solo lectura, sin nombres ni DNIs, y
  no leer `empleado_alias.recurso_ide` (antes del despliegue no existe).

## Documentación y alcance

- **R30.** `ARCHITECTURE.md` (semánticas 2 y 12, herramientas),
  `partes-proyecto.md` (§3.3, §5.3) y `azure-apps/partes.md` (§4.3, viñeta
  Empleado) deben quedar al día.
- **R31.** Lo ya ingerido no se re-casa (DA4): las líneas en la cola ven los
  recursos sin DNI en Conciliar sin reprocesar nada.

## Fuera de alcance

- Agrupar por recurso en el portal las líneas sin DNI (`worker_key`,
  `persona_de` siguen por nombre leído); Sesame sin DNI (calendario por
  defecto, como hoy); completar DNIs en Sigrid (Administración).
