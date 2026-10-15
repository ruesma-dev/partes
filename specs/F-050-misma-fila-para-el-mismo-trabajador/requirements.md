<!-- specs/F-050-misma-fila-para-el-mismo-trabajador/requirements.md -->
# F-050 · Misma fila para el mismo trabajador — Requisitos

**Solo sv4** (`services/partes-front/`). Sin esquema, sin sv3, sin sv5, sin Sigrid. Rigor
propuesto **estándar** (design §8, DA8). Decisiones abiertas: design §8 (DA1–DA9).

Petición del humano (2026-10-15): «cuando añado la línea con "añadir línea", si el
trabajador ya tiene extras y solo extras, al añadir ordinario me duplica en el calendario
la línea del trabajador. Revisa qué ha podido ser y añade feature.»

## Causa (verificada en el código, `dev` `dc03468`; detalle en design §1)

El portal agrupa por trabajador con `worker_key_for_registro`: `emp-{empleado_ide}` y, sin
ficha, `nom-` + **nombre leído** normalizado. Un trabajador **sin ficha** casado por su
recurso tiene en la línea de la IA el nombre leído del papel (orden nombre-apellidos) y en la
línea añadida con «+ Añadir línea» el nombre de Sigrid (orden apellidos-nombre), que
`crear_parte_manual` copia en `trabajador_nombre_leido`. Mismo recurso, dos claves ⇒ dos
filas. El detalle del parte y el listado de partes agrupan con una tercera variante
(`empleado_ide or nombre leído`) con el mismo fallo.

## Glosario

- **Clave de trabajador**: la que devuelve `worker_key_for_registro`; sale en las URL
  `/trabajadores/{clave}` y en las acciones por clave (reasignar, papelera, ámbito de aprobar).
- **Casada sin ficha**: `empleado_ide` NULL y método en `recurso_dni`, `recurso_nombre` o
  `recurso_manual` (`esta_casado`, F-030/F-035).
- **Recurso de la línea**: `empleado_reside` y, si es NULL, `recurso_ide`.

## Clave de trabajador

- **R1.** El sistema debe calcular la clave en este orden: con `empleado_ide`,
  `emp-{empleado_ide}`; si no, casada sin ficha y con recurso, `rec-{recurso}`; si no, con
  nombre leído, `nom-` + nombre normalizado (como hoy); si no, `sin-trabajador`.
- **R2.** SI la línea no está casada (`esta_casado` falso), ENTONCES su clave no debe ser
  `rec-` aunque tenga `empleado_reside` o `recurso_ide`.
- **R3.** Para toda línea con ficha, o no casada, la clave debe ser idéntica a la de hoy
  (las URL `emp-` y `nom-` de esas personas no cambian).
- **R4.** Una sola función calcula la clave para todas las vistas y acciones de §Vistas y
  §Acciones; no queda ninguna agrupación por trabajador escrita a mano en el repositorio.

## Vistas

- **R5.** El calendario de la obra (`get_obra`) debe pintar una fila por clave: en el caso
  real (E1) una fila con la celda «8+2», `edit_normal_id` = la línea manual y
  `edit_extra_id` = la de la IA.
- **R6.** El detalle del parte (`get_parte`) debe agrupar por la clave de R1; las líneas
  `sin-trabajador` siguen separadas por `empleado_line_no`, como hoy.
- **R7.** El listado de partes (`list_partes`) debe contar `num_empleados` como el número de
  claves distintas del parte.
- **R8.** La lista de trabajadores, la vista `/trabajadores/{clave}`, el número de
  trabajadores por obra (`list_obras`) y `alcance_parte` (F-043) deben contar a la persona
  de E1 una sola vez.
- **R9.** `persona_de` (F-025) no cambia con DNI; sin DNI devuelve la clave de R1.

## Acciones por clave

- **R10.** `reassign_empleado_by_worker_key`, `soft_delete_worker` y
  `registro_ids_de_trabajador` con `rec-{R}` deben actuar sobre todas las líneas activas de
  ese recurso casadas sin ficha y sobre ninguna otra.
- **R11.** CUANDO una acción por clave recibe una clave que hoy no tiene líneas (p. ej.
  una `nom-` antigua), debe actuar sobre 0 líneas, como hoy con una clave desconocida
  (reasignar 0, papelera `ok: false`, aprobación rechazada por ámbito).

## Compatibilidad de enlaces

- **R12.** CUANDO `GET /trabajadores/{clave}` no encuentra líneas y la clave empieza por
  `nom-`, SI todas las líneas activas cuyo nombre leído normalizado da esa clave tienen hoy
  una misma clave distinta, ENTONCES el sistema debe redirigir a `/trabajadores/{esa clave}`
  conservando la query (`period`, `modo`).
- **R13.** SI en R12 no hay líneas o dan más de una clave, ENTONCES 404 como hoy.

## Alta manual («+ Añadir línea» y «Nuevo parte»)

- **R14.** CUANDO `crear_parte_manual` añade líneas a un documento con alguna línea activa
  de la misma clave que la nueva, las nuevas deben heredar `empleado_line_no` y
  `trabajador_nombre_leido` de la de menor `line_index`.
- **R15.** SI no la hay, ENTONCES `empleado_line_no` = máximo del documento (papelera
  incluida) + 1, o 1 sin ninguno, y `trabajador_nombre_leido` = `empleado_nombre` (hoy).
- **R16.** Lo demás que escribe `crear_parte_manual` no cambia (`line_index`, método,
  `recurso_ide`, `recurso_cif`, horas, códigos, partida).
- **R17.** CUANDO la vista de un trabajador con clave `rec-{R}` abre «+ Añadir línea», el
  modal debe enviar `empleado_reside` = R, de modo que la línea nazca `recurso_manual` y con
  la misma clave. Con `emp-` y `nom-` se envía vacío, como hoy.

## Lo que no cambia

- **R18.** No cambian sv3, sv5, `orm_models.py`, `congelacion.py`, las reglas gemelas del
  `CLAUDE.md`, la clave de obra, `crear_extra_desde`, Conciliar (`list_unmatched_workers`)
  ni los datos ya guardados (no hay migración).

## Ejemplos

| Caso | Líneas | Clave hoy | Clave F-050 | Filas |
|---|---|---|---|---|
| E1 real (0678, 15/10) | IA: sin ficha, `recurso_dni`, recurso R, leído nombre-apellidos, extra 2 · manual: `recurso_manual`, R, leído = nombre de Sigrid apellidos-nombre, normal 8 | dos `nom-` distintas | `rec-R` las dos | 2 → 1 («8+2») |
| E2 con ficha | dos líneas con `empleado_ide` E | `emp-E` | `emp-E` | 1 → 1 |
| E3 sin ficha ni recurso | sin casar, leídos «Pepe Perez» y «PEPE PÉREZ» | `nom-PEPE_PEREZ` | igual | 1 → 1 |
| E4a homónimos casados | mismo leído, sin ficha, recursos R1 ≠ R2 | una `nom-` (fusionados) | `rec-R1`, `rec-R2` | 1 → 2 |
| E4b homónimos sin casar | mismo leído, sin casar | una `nom-` | igual (Conciliar los separa) | 1 → 1 |
| E5 casada + sin casar | `rec-R` y otra sin casar con el mismo leído | una `nom-` | `rec-R` y `nom-…` | 1 → 2 (como con ficha hoy) |
| E6 alta con la persona en el parte | trabajador 4 ya en fila 3 del papel | `empleado_line_no` 1 | hereda 3 y su leído | — |
| E7 alta sin la persona | parte con filas 1–5 | 1 | 6 | — |

## Tests previstos (design §5)

`services/partes-front/tests/test_f050_clave.py` (R1–R4, R9),
`test_f050_vistas.py` (R5–R8, R10–R11), `test_f050_alta_manual.py` (R14–R16) y
`test_f050_portal.py` (R12–R13, R17). Sin red ni PostgreSQL (SQLite de `tests/dobles.py`),
datos sintéticos (ni nombres reales ni DNIs). R18: comprobación de `git diff` (T8).

## Verificaciones manuales (humano)

M1–M5 con los pasos exactos en design §6: M1 antes de desplegar (SQL de solo lectura:
cuántas personas están hoy partidas en dos claves por parte y por obra); M2–M5 tras
desplegar sv4 (calendario de la 0678 del 15/10 con UNA fila «8+2», detalle del parte,
enlace antiguo redirigido y alta desde la vista del trabajador).

## Fuera de alcance

- Unificar a una persona con fichas o recursos en dos empresas (dos `emp-` o dos `rec-`).
- Clave por DNI para todas las líneas (cambiaría las URL de todos; design DA1).
- Corregir el `empleado_line_no` y el leído de las líneas manuales ya guardadas.
- El aviso de jornada incompleta de la vista de obra, que va por nombre de fila (design §7).
