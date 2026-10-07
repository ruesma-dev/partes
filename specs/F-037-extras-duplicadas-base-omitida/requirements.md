<!-- specs/F-037-extras-duplicadas-base-omitida/requirements.md -->
# F-037 · sv3: no duplicar la extra automática de una base omitida — Requisitos

**Servicio tocado: solo sv3** (`services/partes-persistencia/`). Sin schema,
sin Sigrid, sin sv4 ni sv5. Rigor **crítico** (datos que viajan al ERP).
URGENTE: incidencia en producción.

## Contexto

Leído en producción (solo lectura, 2026-10-07): 7 `extra_auto` duplicadas
en la base `partes`, obra 0678, 01–03/10/2026 (Ruesma 4, Porsan 3). En
todas: base normal `sigrid_estado='omitido'` (mensual sin hora laborable,
10 → 8 h; o base de 0 h «sin horas») + su `extra_auto` ya `registrado` +
una `extra_auto` nueva idéntica sin estado. Con la base `registrado` no hay
duplicado.

Mecanismo (código de hoy): `revert_extras_auto()` respeta la extra
congelada pero restaura la base no congelada (`horas = horas_orig`);
`RecursoConciliador._reclasificar_extras_jornada` la vuelve a partir
(cuenta la extra congelada **y** las horas restauradas: el día suma de más)
y `apply_extras_splits()` inserta otra extra. Cada mensaje de sv3 recalcula
todos los partes activos: un duplicado nuevo por pasada (el anterior, no
congelado, se borra). Aprobarlo lo escribiría en Sigrid con otro synckey.

Caso inverso (mismo defecto): base `registrado` recortada + su extra no
congelada (`error`, pendiente…): la pasada borra la extra y no la recrea
(la base congelada ya no deja hueco): horas perdidas.

## Glosario

- **Clave de pareja**: `(document_id, line_index, empleado_line_no,
  fecha_int)`. `apply_extras_splits` clona esos cuatro campos de la base en
  su extra; `line_index` es único por línea original del documento.
- **Miembro de la pareja**: fila con esa clave que sea `extra_auto = true`
  (sus extras) o `extra_auto = false` con `tipo_hora` ordinario (`""` o
  `normal`; la base). Una extra explícita (`extra_auto = false`, `tipo_hora
  = extra`, p. ej. la de `crear_extra_desde` de sv4) NO es miembro.
- **Congelada** (por sí misma): `esta_congelado(sigrid_estado, approved)`,
  la regla compartida de F-004/F-019/F-024. **No cambia** en esta feature.
- **Pareja congelada**: alguno de sus miembros está congelado.
- **Congelada por pareja**: miembro no congelado de una pareja congelada.

## Requisitos

### Pareja (núcleo puro)

- **R1.** El sistema debe calcular la clave de pareja de una fila con los
  cuatro campos del glosario, tratando `None` como un valor más (dos `None`
  son iguales).
- **R2.** El sistema debe considerar miembro de la pareja solo a las filas
  descritas en el glosario: una extra explícita con la misma clave ni la
  congela ni se ve afectada.
- **R3.** El sistema debe considerar congelada una pareja si y solo si
  alguno de sus miembros está congelado; parejas de otra clave (otra línea
  del mismo parte, otro día) no se influyen.

### Reversión (`revert_extras_auto`)

- **R4.** MIENTRAS una pareja esté congelada, la reversión no debe
  restaurar su base (conserva `horas` y `horas_orig`) ni borrar sus extras
  congeladas.
- **R5.** CUANDO una pareja congelada no tenga ninguna extra congelada
  (caso inverso: solo la base lo está), la reversión debe conservar sus
  extras no congeladas.
- **R6.** CUANDO una pareja tenga alguna extra congelada, la reversión debe
  borrar sus extras NO congeladas (son duplicados) y emitir un WARNING con
  el número y hasta 10 `id` de las borradas (sin nombres ni DNIs).
- **R7.** SI una pareja tiene más de una extra congelada, ENTONCES la
  reversión no debe borrar ninguna de ellas y debe emitir un WARNING con su
  clave (`document_id`, `line_index`) para revisión manual.
- **R8.** Las parejas no congeladas deben revertirse como hoy (borrar
  extras, restaurar la base). El valor devuelto sigue siendo el número de
  `extra_auto` borradas (incluidos los duplicados de R6) y el INFO de
  «CONGELADAS respetadas» sigue contando solo las congeladas por sí mismas;
  las protegidas por pareja se cuentan en un INFO aparte.

### Lectura y cálculo de splits

- **R9.** `fetch_registros_para_recurso` debe devolver en cada fila la
  marca `congelada_por_pareja` (bool), calculada sobre todas las filas
  leídas con la regla de R1–R3.
- **R10.** El conciliador debe tratar como congelada, a todos los efectos
  de sv3, una fila congelada por sí misma O por pareja: no re-resuelve su
  recurso (F-023 R30), suma en el total del día y nunca es candidata a
  recorte ni pivote (F-015 R32).

### Comportamiento extremo a extremo (dos pasadas)

- **R11.** CUANDO se concilie dos veces seguidas un día laborable con base
  `omitido` (10 h originales, 8 tras el split) y su extra de 2 h
  `registrado`, el sistema no debe crear ninguna `extra_auto`; base y extra
  quedan como estaban.
- **R12.** CUANDO se concilie dos veces seguidas un día no laborable con
  base de 0 h `omitido` (4 h originales) y su extra de 4 h `registrado`, el
  sistema no debe crear ninguna `extra_auto`.
- **R13.** CUANDO se concilie el estado de la incidencia (R11 o R12 más un
  duplicado sin estado), la primera pasada debe borrar el duplicado y no
  recrearlo, y la segunda no debe cambiar nada.
- **R14.** CUANDO se concilie dos veces una base `registrado` recortada con
  su extra no congelada (sin estado o `error`), la extra debe sobrevivir con
  sus horas, la base no cambia y no se crea ninguna extra nueva.
- **R15.** En un día mixto (pareja congelada + otra línea ordinaria libre
  del mismo recurso y día), el ajuste debe caer solo sobre la línea libre y
  contar la base y la extra de la pareja una sola vez.

### No regresión y límites

- **R16.** Una pareja sin nada congelado debe re-partirse en cada pasada
  como hoy: tras dos pasadas hay exactamente una `extra_auto` por base
  partida, con las mismas horas.
- **R17.** Los tests existentes de F-015 (R31, R32), F-023 (R30) y F-024
  deben seguir en verde sin modificarlos.
- **R18.** `esta_congelado`, `ESTADOS_CONGELADOS`
  (`recurso_conciliador.py`) y sv4 `application/services/congelacion.py` no
  deben cambiar (diff vacío); el guardián
  `tests/test_f024_borrado_no_congela_gemelos.py` sigue en verde.
- **R19.** Los tests no tocan red ni PostgreSQL (SQLite en memoria con el
  ORM real y dobles) y usan datos sintéticos.

### Documentación y verificación

- **R20.** `docs/ARCHITECTURE.md` (semántica 3) y
  `docs/referencia/partes-proyecto.md` (cómputo de extras, §3.3 y su
  repetición) deben decir que base y extra automática se congelan juntas
  para el recálculo de sv3. `azure-apps/partes.md` no cambia (no varía lo
  que el proyecto expone ni consume).
- **R21.** Tras desplegar sv3, la consulta de solo lectura M2 del diseño
  (§8) debe dar 0 parejas con más de una `extra_auto` — verificación
  MANUAL del humano.
