<!-- specs/F-050-misma-fila-para-el-mismo-trabajador/requirements.md -->
# F-050 · Misma fila para el mismo trabajador — Requisitos

**Solo sv4** (`services/partes-front/`). Sin esquema, sin sv3, sin sv5, sin Sigrid. Rigor
**estándar**. Decisiones: design §8 (todas aprobadas por el humano; DA1 opción A, DA1b y DA11 el
2026-10-20).

Petición del humano (2026-10-15): «cuando añado la línea con "añadir línea", si el
trabajador ya tiene extras y solo extras, al añadir ordinario me duplica en el calendario
la línea del trabajador. Revisa qué ha podido ser y añade feature.»

**Regla del humano (2026-10-20, literal)**: «es una linea por obra empresa y persona. puede
estar en varias obras, o en 2 empresas». Fila = **(obra, empresa, persona)**: una por obra,
dos en dos empresas y **una** dentro de una obra y una empresa (IA o alta manual, con ficha o
sin ella).

**Segunda regla (2026-10-20, literal)**: «en la vista por persona, se juntan las obras. lo
que es importante es que en 2 empresas son 2 personas con vistas diferenciadas». En «Por
persona» una fila por (empresa, persona) con todas sus obras, y la empresa **a la vista**.

## Causa (verificada en el código; detalle en design §1)

`worker_key_for_registro` agrupa por `emp-{empleado_ide}` y, sin ficha, por el **nombre
leído**; la IA guarda el leído del papel y `crear_parte_manual` el nombre de Sigrid: dos
filas (caso real E1). Una persona puede tener además líneas con y sin ficha del mismo
recurso (C1–C3). El detalle y el listado de partes agrupan con otra variante.

## Glosario

- **Clave de trabajador**: la de `worker_key_for_registro` (URL `/trabajadores/{clave}`,
  reasignar, papelera, ámbito de aprobar). **Casada**: `esta_casado` (F-030/F-035).
- **Recurso de la línea**: `recurso_ide` y, si es NULL, `empleado_reside`: un recurso
  persona (`res.cla = 1`) de **una** empresa; identifica a la persona dentro de ella.

## Clave de trabajador

- **R1.** El sistema debe calcular la clave en este orden: casada y con recurso,
  `rec-{recurso}` (con o sin ficha); si no, con `empleado_ide`, `emp-{empleado_ide}`; si no,
  con nombre leído, `nom-` + nombre normalizado (como hoy); si no, `sin-trabajador`.
- **R2.** SI la línea no está casada, ENTONCES su clave no debe ser `rec-` aunque tenga
  `empleado_reside` o `recurso_ide`.
- **R3.** Para toda línea no casada la clave debe ser idéntica a la de hoy (`nom-` y
  `sin-trabajador` no cambian).
- **R4.** Una sola función calcula la clave para todas las vistas y acciones de §Vistas y
  §Acciones; no queda ninguna agrupación por trabajador escrita a mano en el repositorio.

## Vistas (cómo aplica la regla en cada una)

- **R5.** Calendario de obra (`get_obra`): una fila por clave. En E1 una fila «8+2» con
  `edit_normal_id` = la línea manual y `edit_extra_id` = la de la IA; en E8 una fila.
- **R6.** Detalle del parte (`get_parte`): un bloque por clave; las `sin-trabajador` siguen
  separadas por `empleado_line_no`, como hoy.
- **R7.** Listado de partes (`list_partes`): `num_empleados` = claves distintas del parte.
- **R8.** Recuento de trabajadores por obra (`list_obras`) y `alcance_parte` (F-043): claves
  distintas; la persona de E1 y la de E8 cuentan una vez.
- **R9.** Lista «Por persona» (`list_workers`): una fila por clave, es decir, por
  (empresa, persona), con todas sus obras dentro (DA10): E9, una fila; E10, dos filas.
- **R10.** `/trabajadores/{clave}` (`get_worker`): las líneas de esa clave en todas sus
  obras (columna por obra de cada día, como hoy) y ninguna otra (E10: `rec-R1` sin las de R2).
- **R11.** `persona_de` (F-025) no cambia con DNI; sin DNI devuelve la clave de R1.

## Empresa de la persona (DA11)

- **R23.** La lista «Por persona» debe mostrar en cada fila una columna «Empresa», con su
  filtro, con la regla de «Por obra» (F-033): las empresas no nulas de los partes de sus
  líneas o, si ninguno la tiene, las de su recurso deducidas de otros partes con empresa.
- **R24.** La cabecera de `/trabajadores/{clave}` debe mostrar la empresa de R23 sobre las
  líneas activas de la clave (E10: empresa A en una vista y B en la otra).
- **R25.** SI no se puede saber (ni partes con empresa ni recurso deducible), ENTONCES la
  lista pinta «—» y la cabecera no la pinta. En `nom-`/`sin-trabajador` es la de sus partes.
- **R26.** CUANDO dos filas tienen el mismo nombre, va primero la de menor empresa y las
  sin empresa detrás (F-033 R7). R23–R25 no llaman a Sigrid ni añaden consultas a la BBDD.

## Acciones por clave

- **R12.** Reasignar, papelera y `registro_ids_de_trabajador` con `rec-{R}` deben actuar
  sobre las líneas activas de esa clave (con y sin ficha) y ninguna otra.
- **R13.** CUANDO una acción por clave recibe una clave que hoy no tiene líneas (una `nom-`
  o una `emp-` antiguas), debe actuar sobre 0 líneas, como hoy con una clave desconocida.

## Compatibilidad de enlaces

- **R14.** CUANDO `GET /trabajadores/{clave}` no encuentra líneas y la clave es `nom-…` o
  `emp-{E}`, SI todas las líneas activas que darían esa clave con la regla anterior (leído
  normalizado igual, o `empleado_ide` = E) tienen hoy una misma clave distinta, ENTONCES
  debe redirigir (307) a `/trabajadores/{esa clave}` conservando la query.
- **R15.** SI en R14 no hay líneas o dan más de una clave, ENTONCES 404 como hoy.

## Alta manual («+ Añadir línea» y «Nuevo parte»)

- **R16.** CUANDO `crear_parte_manual` añade líneas a un documento con alguna línea activa
  de la misma clave que la nueva, las nuevas deben heredar `empleado_line_no` y
  `trabajador_nombre_leido` de la de menor `line_index`.
- **R17.** SI no la hay, ENTONCES `empleado_line_no` = máximo del documento (papelera
  incluida) + 1, o 1 sin ninguno, y `trabajador_nombre_leido` = `empleado_nombre` (hoy).
- **R18.** Lo demás que escribe `crear_parte_manual` no cambia (`line_index`, método,
  `recurso_ide`, `recurso_cif`, horas, códigos, partida).
- **R19.** CUANDO la vista de un trabajador abre «+ Añadir línea», el modal debe enviar
  `empleado_ide` = la ficha del trabajador (la de su línea más reciente con ficha, o vacío)
  y `empleado_reside` = R si la clave es `rec-{R}` (vacío con `emp-` y `nom-`).
- **R20.** CUANDO «Nuevo parte» termina bien, el enlace «Ver» debe llevar a
  `/trabajadores/rec-{reside}` si se eligió recurso, a `emp-{ide}` si solo hay ficha, y a
  `/partes` si no hay ninguno.

## Lo que no cambia

- **R21.** No cambian sv3, sv5, `orm_models.py`, `congelacion.py`, las reglas gemelas del
  `CLAUDE.md`, la clave de obra, `crear_extra_desde`, Conciliar (`list_unmatched_workers`)
  ni los datos guardados (no hay migración).
- **R22.** En los tests existentes solo cambia el literal de la clave esperada de las líneas
  casadas con recurso (`emp-N` → `rec-R` de su fixture) y nada más (design §5).

## Ejemplos

| Caso | Líneas (misma obra salvo E9) | Clave hoy | Clave F-050 | Filas |
|---|---|---|---|---|
| E1 real (0678, 15/10) | IA sin ficha `recurso_dni`, recurso R, extra 2 · manual `recurso_manual`, R, leído = nombre de Sigrid, normal 8 | dos `nom-` | `rec-R` | 2 → 1 («8+2») |
| E2 con ficha | dos líneas con ficha E y recurso R | `emp-E` | `rec-R` | 1 → 1 (URL cambia, R14) |
| E3 sin casar | leídos «Pepe Perez» y «PEPE PÉREZ» | `nom-PEPE_PEREZ` | igual | 1 → 1 |
| E4a homónimos casados | mismo leído, sin ficha, recursos R1 ≠ R2 | una `nom-` | `rec-R1`, `rec-R2` | 1 → 2 |
| E4b homónimos sin casar | mismo leído, sin casar | una `nom-` | igual (Conciliar) | 1 → 1 |
| E5 casada + sin casar | `rec-R` y otra sin casar con el mismo leído | una `nom-` | `rec-R` y `nom-…` | 1 → 2 |
| E6 alta con la persona en el parte | trabajador ya en la fila 3 del papel | `empleado_line_no` 1 | hereda 3 y su leído | — |
| E7 alta sin la persona | parte con filas 1–5 | 1 | 6 | — |
| E8 ficha + sin ficha | IA con ficha E y recurso R · otra línea sin ficha del mismo R (C1–C3) | `emp-E` y `nom-…` | `rec-R` | 2 → 1 |
| E9 dos obras | recurso R en las obras X e Y | `emp-E` o `nom-…` | `rec-R` | una fila en X y otra en Y; una en «Por persona» (R9) |
| E10 dos empresas | ficha E1 y recurso R1 en la empresa A; ficha E2 y recurso R2 en B | `emp-E1`, `emp-E2` | `rec-R1`, `rec-R2` | 2 → 2, cada una con su empresa (R23–R24) |
| E11 dos recursos, una empresa | mismo DNI, recursos R1 y R2 de la empresa A, misma obra | `emp-E` y `nom-…` | `rec-R1`, `rec-R2` | 2 → 2 (DA1b) |
| E12 ficha sin recurso | ficha E, `recurso_ide` y `reside` NULL (transitorio hasta sv3) | `emp-E` | `emp-E` | 1 → 1 |

## Tests previstos (design §5)

`services/partes-front/tests/test_f050_clave.py` (R1–R4, R11), `test_f050_vistas.py`
(R5–R10, R12–R13), `test_f050_alta_manual.py` (R16–R18), `test_f050_portal.py` (R14–R15,
R19–R20) y `test_f050_empresa.py` (R23–R26). Sin red ni PostgreSQL (SQLite de
`tests/dobles.py`), datos sintéticos. R21–R22: `git diff` (T10).

## Verificaciones manuales (humano)

M1–M6 en design §6. M1 (SQL de solo lectura) **antes de implementar**: filas que se unen,
fichas sin recurso y DNIs con dos recursos en una obra; sus cifras deciden DA1 y DA1b.
M2–M6 tras desplegar sv4 (M6: la columna «Empresa» de «Por persona»).

## Fuera de alcance

- Unir en una fila los dos recursos persona de un mismo DNI en una misma empresa (E11): si
  M1 da casos y el humano lo quiere, otra feature (DA1b).
- Deducir la empresa por la obra cuando ni los partes ni el recurso la dan (design §9 R-d).
- Corregir el `empleado_line_no` y el leído de las líneas manuales ya guardadas.
- El aviso de jornada incompleta de la vista de obra, que va por nombre de fila (design §7).
