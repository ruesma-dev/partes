<!-- specs/F-023-recurso-alta-empresa/requirements.md -->
# F-023 · Casado de trabajador y recurso: solo de alta y por la empresa correcta

Pedida por el humano el 2026-09-30. Rigor **crítico**. Datos que sostienen cada
regla: `progress/explore_F-023_sigrid.md` (§N). Decisiones DA1–DA10 y fuera de
alcance: `design.md` §7–§8, **a aprobar antes de implementar**. Servicios:
**sv3** (casado), **sv5** (escritura) y **sv4** (portal); por qué: design §1.

Glosario:
- **De alta a la fecha D**: `con.fecbaj` del concepto es NULL, 0 o `> D`
  (enteros `YYYYMMDD`).
- **Empresa** de un empleado, recurso u obra: su `con.emp`.
- **Obras gemelas**: obras de empresas distintas con el mismo código (§4).
- **Candidato de la persona P en la empresa E a la fecha D**: recurso de alta
  a D, de la empresa E, con `res.conide` = una ficha de P o `res.cif`
  normalizado = DNI de P.

## A. Regla de alta y maestros

- **R1.** El sistema debe considerar de alta a la fecha D un empleado o un
  recurso si y solo si su `con.fecbaj` es NULL, 0 o mayor que D. `emp.fecbaj`,
  `emp.fecalt` y `emphis` no intervienen (§1).
- **R2.** CUANDO sv3 carga los maestros, debe traer las fichas de empleado de
  **todas** las empresas (sin filtro `SIGRID_EMPRESA`), cada una con su
  empresa y su `con.fecbaj`; los recursos con su empresa y su `con.fecbaj`; y
  las obras con su empresa, **una entrada por `ide`** (sin deduplicar por
  código).
- **R3.** SI sigrid-api devuelve `truncated: true` en una lectura de sv3, sv4 o
  sv5, ENTONCES el cliente debe lanzar excepción en vez de devolver filas
  parciales (§7).

## B. Obra y empresa del parte (sv3, ingesta)

- **R4.** CUANDO el código leído casa con una sola obra, la empresa del parte
  es la de esa obra y el método sigue siendo `codigo` / `codigo_padded`.
- **R5.** CUANDO el código leído casa con varias obras, sv3 debe tomar como
  **discriminantes** los trabajadores del parte con DNI leído cuyos candidatos
  (a la fecha del parte) están en exactamente una de las empresas de esas
  obras; si todos los discriminantes señalan la misma empresa y en ella hay
  una sola obra con ese código, debe casar esa obra con método
  `codigo_trabajadores`.
- **R6.** SI en R5 no hay ningún discriminante, ENTONCES sv3 debe casar por
  similitud de nombre entre las obras con ese código solo si la mejor supera
  el umbral de obra y es estrictamente mayor que la de cualquier otra
  candidata; método `codigo_nombre`.
- **R7.** SI tras R5–R6 la obra sigue sin decidir, o los discriminantes
  señalan empresas distintas, ENTONCES la obra debe quedar sin casar (`ide`
  NULL), con método `codigo_ambiguo`, y el parte con `review_required`.
- **R8.** SI el casado por nombre de obra (sin código) empata en la mejor
  puntuación entre obras distintas, ENTONCES la obra debe quedar sin casar con
  método `nombre_ambiguo` y el parte con `review_required`.
- **R9.** La fecha de referencia del parte debe ser su `fecha_int`; SI el parte
  no tiene fecha válida, ENTONCES se usa la fecha de hoy.

## C. Trabajador (sv3, ingesta)

- **R10.** El casado del trabajador debe hacerse solo contra las fichas de
  alta a la fecha del parte de la empresa del parte; SI la obra quedó sin
  casar, ENTONCES contra las de todas las empresas.
- **R11.** CUANDO el DNI leído tiene exactamente una ficha candidata según
  R10, sv3 debe casar con ella (método `dni`).
- **R12.** SI el DNI leído tiene más de una ficha según R10, ENTONCES el
  trabajador debe quedar sin casar con método `dni_ambiguo`.
- **R13.** SI el DNI leído está en Sigrid pero solo en fichas de baja a la
  fecha del parte, ENTONCES debe quedar sin casar con método `dni_solo_baja`.
- **R14.** SI el DNI leído solo está de alta en fichas de otras empresas que
  la del parte, ENTONCES debe quedar sin casar con método `dni_otra_empresa`.
- **R15.** CUANDO R12, R13 o R14 se cumplen, sv3 no debe seguir al alias ni a
  la similitud de nombre para esa línea: nunca se elige una ficha al azar.
- **R16.** CUANDO un alias aprendido casa el nombre leído y su ficha no es
  candidata según R10, sv3 debe re-resolver por el DNI del alias con
  R11–R14; SI el alias no tiene DNI, ENTONCES sin casar con método
  `alias_no_valido`.
- **R17.** CUANDO se casa por similitud de nombre, solo deben competir las
  fichas de R10; SI la mejor pertenece a un DNI con más de una ficha en R10,
  o empata con la de otra persona, ENTONCES sin casar con `nombre_ambiguo`.
- **R18.** Todo trabajador sin casar por R12–R17 debe dejar el parte con
  `review_required` (regla actual de `_compute_review_required`, sin cambios).

## D. Recurso de cada línea (sv3, conciliación)

- **R19.** CUANDO sv3 resuelve el recurso de una línea, los candidatos deben
  ser los de la persona casada (fichas con su DNI, o la ficha casada si no hay
  DNI) en la empresa de la obra de la línea, de alta a la **fecha real de la
  línea**; SI la línea no tiene obra casada, ENTONCES en cualquier empresa.
- **R20.** CUANDO hay un solo candidato, sv3 debe asignarlo. CUANDO hay
  varios, debe asignar el que coincide con `empleado_reside`, o si no el único
  cuyo `conide` es la ficha casada; SI siguen quedando varios, ENTONCES la
  línea queda sin recurso.
- **R21.** `empleado_reside` no debe asignarse nunca si no está entre los
  candidatos de R19 (recurso de baja, de otra empresa o de otra persona).
- **R22.** SI una línea queda sin recurso por ambigüedad, o porque la persona
  solo tiene recursos de baja o de otra empresa, ENTONCES `parte_estado` debe
  ser `sin_recurso`, se debe loguear un WARNING con el motivo y el parte debe
  quedar con `review_required`.
- **R23.** MIENTRAS una línea está congelada (`esta_congelado`), la
  conciliación no debe cambiar su `recurso_ide`, `recurso_cif`, `hmo_ide` ni
  `parte_estado`.
- **R24.** Las líneas no congeladas de partes ya ingeridos deben re-resolverse
  con R19–R22 en la siguiente pasada; el empleado y la obra ya casados en esos
  partes **no** se re-casan.

## E. Escritura en Sigrid (sv5)

- **R25.** CUANDO sv5 crea la cabecera de un parte, `con.emp` debe ser la
  empresa de la obra destino; `SIGRID_EMPRESA` no debe intervenir.
- **R26.** CUANDO sv5 calcula el siguiente `PT<AA>/NNNNN`, el máximo debe
  tomarse solo entre los conceptos de la empresa de la obra destino (§6).
- **R27.** CUANDO sv5 inserta la extensión `hmo` de una cabecera nueva, debe
  localizarla por código, tipo **y empresa**.
- **R28.** SI la obra destino no tiene empresa (NULL o 0), o se busca por
  código y hay varias obras con ese código, ENTONCES sv5 debe fallar como con
  una obra no encontrada y no escribir nada.
- **R29.** Antes de escribir, para cada línea con `recurso_ide`, sv5 debe
  comprobar que el recurso es de la empresa de la obra destino, está de alta a
  la fecha de la línea y, si la línea trae DNI, que el DNI del recurso
  (`emp.dni` vía `conide`, o `res.cif`) coincide normalizado; SI falla algo,
  ENTONCES la línea se omite con un motivo que diga cuál de las tres falló.
- **R30.** CUANDO una línea llega sin `recurso_ide` y con DNI, sv5 debe
  resolverlo solo si hay exactamente un candidato de esa persona en la
  empresa de la obra destino a la fecha de la línea; SI hay cero o varios,
  ENTONCES la línea se omite con motivo (sin recurso / recurso ambiguo).

## F. Portal (sv4)

- **R31.** El catálogo de empleados del portal debe incluir la empresa de cada
  ficha y conservar su filtro actual de alta a hoy (R1 sobre empleado y
  recurso).
- **R32.** El catálogo de obras del portal debe listar una entrada por obra
  (`ide`) con su empresa, sin deduplicar por código.
- **R33.** `GET /api/sigrid/empleados` y `GET /api/sigrid/obras` deben añadir
  `empresa` a cada elemento sin quitar ni renombrar ningún campo.
- **R34.** Los combos de obra y de trabajador deben mostrar la empresa en la
  etiqueta; CUANDO en un alta manual hay una obra elegida, el combo de
  trabajador solo debe ofrecer fichas de su empresa.
- **R35.** CUANDO el portal casa o reasigna el empleado de unas líneas
  (conciliación, reasignar por nombre leído, por trabajador o por líneas),
  debe poner a NULL `empleado_reside`, `recurso_ide`, `recurso_cif`, `hmo_ide`
  y `parte_estado` de las líneas no congeladas que toca.

## G. Documentación

- **R36.** `docs/ARCHITECTURE.md` (semántica de dominio),
  `docs/referencia/partes-proyecto.md` (§4.6 y §6.6) y
  `azure-apps/partes.md` deben documentar la regla de alta, la empresa del
  parte, las obras gemelas y que `SIGRID_EMPRESA` deja de usarse.
