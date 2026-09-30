<!-- specs/F-023-recurso-alta-empresa/requirements.md -->
# F-023 · Casado de trabajador y recurso: solo de alta y por la empresa correcta

Humano, 2026-09-30 (revisada con sus respuestas). Rigor **crítico**. Datos:
`progress/explore_F-023_sigrid.md` (§N). DA1–DA12 y fuera de alcance: design
§7–§8, **a aprobar antes de implementar**. Toca sv2, sv3, sv5 y sv4 (design §1).

Glosario: **de alta a la fecha D** = `con.fecbaj` NULL, 0 o `> D` (`YYYYMMDD`).
**Empresa** de un empleado, recurso u obra = su `con.emp` (= `auxemp.numemp`).
**Obras gemelas** = mismo código en empresas distintas (§4). **Candidato** de
una persona en E a la fecha D = recurso de alta a D, de la empresa E, con
`res.conide` = una de sus fichas o `res.cif` = su DNI.
**Caso guía** (§8.2): la ficha de alta apunta (`emp.reside`) a un recurso de
baja desde 2021 y la persona tiene otro recurso de alta en la misma empresa.

## A. Alta y lectura de Sigrid

- **R1.** Un empleado o recurso está de alta a la fecha D si y solo si su
  `con.fecbaj` es NULL, 0 o mayor que D; `emp.fecbaj`, `emp.fecalt` y
  `emphis` no intervienen (§1).
- **R2.** sv3 debe cargar las fichas de empleado de **todas** las empresas (sin
  `SIGRID_EMPRESA`) con empresa y `con.fecbaj`; los recursos con empresa y
  `con.fecbaj`; las obras con empresa, una entrada por `ide`; y las empresas
  de `auxemp` (`numemp`, `res`, `fecbaj`, `desact`).
- **R3.** CUANDO sv3 o sv4 leen un listado de Sigrid (maestros, partidas,
  `reshor`, `hmo` de una obra), deben paginar con `ORDER BY` por clave única y
  estable y `OFFSET ? ROWS FETCH NEXT ? ROWS ONLY`, en páginas de 5.000 filas
  pedidas con `max_rows` = página + 1, hasta recibir una página incompleta.
- **R4.** SI una respuesta de sigrid-api trae `truncated: true` en sv3, sv4 o
  sv5, ENTONCES el cliente debe lanzar excepción y no devolver filas parciales.

## B. Empresa del membrete (sv2 → sv3)

- **R5.** sv2 debe extraer `cabecera.empresa_membrete`: el nombre de empresa
  impreso en el membrete o logotipo, tal cual; null si no aparece o no se lee.
  Nunca se deduce de la obra, del encargado ni de los trabajadores.
- **R6.** sv3 debe guardar ese texto en `parte_documents.empresa_membrete`.
- **R7.** sv3 debe traducir el texto a empresa con la tabla versionada de alias
  (`config/empresas_membrete.yaml`): casa si el texto normalizado contiene,
  como palabras completas, un alias de **exactamente una** empresa que exista
  en `auxemp` sin baja ni `desact`.
- **R8.** SI el texto es null, no contiene ningún alias o contiene alias de
  varias empresas, ENTONCES la empresa del membrete queda desconocida y se
  aplica C sin ella; el caso se loguea con el texto leído.

## C. Obra y empresa del parte (sv3, ingesta)

- **R9.** CUANDO hay empresa del membrete, solo compiten las obras de esa
  empresa con el código leído; si hay exactamente una, se casa (`codigo`, o
  `codigo_membrete` si el código tenía gemelas).
- **R10.** SI hay empresa del membrete y el código solo existe en obras de otras
  empresas, ENTONCES la obra queda sin casar con `codigo_otra_empresa` y el
  parte con `review_required`.
- **R11.** CUANDO no hay empresa del membrete y el código casa con varias obras,
  los **discriminantes** son los trabajadores con DNI leído cuyos candidatos a
  la fecha del parte están en exactamente una de sus empresas; si todos
  señalan la misma y en ella hay una sola obra, se casa (`codigo_trabajadores`).
- **R12.** SI en R11 no hay discriminantes, ENTONCES se casa por nombre entre
  esas obras solo si la mejor supera el umbral y supera estrictamente a las
  demás (`codigo_nombre`).
- **R13.** SI tras R11–R12 no hay una única obra, o los discriminantes discrepan,
  ENTONCES obra sin casar con `codigo_ambiguo` y `review_required`.
- **R14.** El casado por nombre sin código debe limitarse a la empresa del
  membrete si se conoce; SI empata la mejor puntuación entre obras distintas,
  ENTONCES sin casar con `nombre_ambiguo` y `review_required`.
- **R15.** La empresa del parte es la de la obra casada; sin obra, la del
  membrete; si no, ninguna. sv3 debe guardarla en `parte_documents.empresa`
  con su origen en `empresa_origen` (`membrete`, `obra`, `trabajadores`,
  `nombre` o NULL).
- **R16.** La fecha de referencia del parte es su `fecha_int`; sin fecha válida,
  la de hoy.

## D. Trabajador (sv3, ingesta)

- **R17.** El trabajador se casa solo contra las fichas de alta a la fecha del
  parte de la empresa del parte; sin empresa del parte, contra todas.
- **R18.** Con exactamente una ficha para el DNI leído, se casa (`dni`).
- **R19.** SI el DNI tiene varias fichas en R17, ENTONCES sin casar con
  `dni_ambiguo`.
- **R20.** SI el DNI solo tiene fichas de baja a la fecha, ENTONCES sin casar
  con `dni_solo_baja`.
- **R21.** SI el DNI solo está de alta en otras empresas, ENTONCES sin casar con
  `dni_otra_empresa`.
- **R22.** Tras R19–R21 no se sigue al alias ni al nombre (nunca se elige al
  azar); todo trabajador sin casar deja `review_required` (regla actual).
- **R23.** CUANDO un alias casa el nombre y su ficha no está en R17, se
  re-resuelve por el DNI del alias con R18–R21; SI el alias no tiene DNI,
  ENTONCES sin casar con `alias_no_valido`.
- **R24.** Por similitud de nombre solo compiten las fichas de R17; SI la mejor
  es de un DNI con varias fichas en R17 o empata con otra persona, ENTONCES sin
  casar con `nombre_ambiguo`.

## E. Recurso de cada línea (sv3, conciliación)

- **R25.** Los candidatos del recurso de una línea son los de la persona casada
  (fichas con su DNI, o la ficha casada si no hay DNI), de alta a la **fecha de
  la línea**, en la empresa de su obra; sin obra, en `parte_documents.empresa`;
  sin ninguna, en cualquier empresa.
- **R26.** Con un candidato, se asigna; con varios, el que coincide con
  `empleado_reside` o, si no, el único cuyo `conide` es la ficha casada; SI
  quedan varios, ENTONCES sin recurso.
- **R27.** `empleado_reside` nunca se asigna fuera de los candidatos de R25
  (caso guía: recurso de baja, de otra empresa o de otra persona).
- **R28.** CUANDO la persona tenía más recursos que candidatos, se loguea INFO
  con cuántos se descartaron y por qué (baja / otra empresa).
- **R29.** SI la línea queda sin recurso por ambigüedad, o la persona solo tiene
  recursos de baja o de otra empresa, ENTONCES `parte_estado = 'sin_recurso'`,
  WARNING con el motivo y el parte con `review_required`.
- **R30.** MIENTRAS una línea está congelada (`esta_congelado`), no cambian su
  `recurso_ide`, `recurso_cif`, `hmo_ide` ni `parte_estado`.
- **R31.** Las líneas no congeladas de partes ya ingeridos se re-resuelven con
  R25–R29 en la siguiente pasada; su empleado, obra y empresa no se re-casan.

## F. Escritura en Sigrid (sv5)

- **R32.** La cabecera de un parte nuevo lleva `con.emp` = empresa de la obra
  destino; `SIGRID_EMPRESA` no interviene.
- **R33.** El siguiente `PT<AA>/NNNNN` se calcula solo entre los conceptos de la
  empresa de la obra destino (§6).
- **R34.** El `INSERT INTO hmo` localiza la cabecera por código, tipo y empresa.
- **R35.** SI la obra destino no tiene empresa, o se busca por código y hay
  varias, ENTONCES sv5 falla como con obra no encontrada y no escribe nada.
- **R36.** Para cada línea con `recurso_ide`, sv5 comprueba antes de escribir
  que el recurso es de la empresa de la obra destino, está de alta a la fecha
  de la línea y, si la línea trae DNI, que es de esa persona (`emp.dni` vía
  `conide`, o `res.cif`); SI falla, ENTONCES la línea se omite con un motivo
  que dice cuál de las tres comprobaciones falló.
- **R37.** Una línea sin `recurso_ide` y con DNI se resuelve solo con un único
  candidato en la empresa de la obra destino a la fecha de la línea; SI hay
  cero o varios, ENTONCES se omite con motivo (sin recurso / ambiguo).

## G. Portal (sv4)

- **R38.** El catálogo de empleados incluye la empresa de cada ficha y conserva
  su filtro actual de alta a hoy (R1 sobre empleado y recurso).
- **R39.** El catálogo de obras lista una entrada por obra (`ide`) con su
  empresa, sin deduplicar por código.
- **R40.** `GET /api/sigrid/empleados` y `/api/sigrid/obras` añaden `empresa` a
  cada elemento sin quitar ni renombrar campos.
- **R41.** Los combos de obra y trabajador muestran la empresa; en un alta
  manual con obra elegida, el de trabajador solo ofrece fichas de su empresa.
- **R42.** CUANDO el portal casa o reasigna el empleado de unas líneas, pone a
  NULL `empleado_reside`, `recurso_ide`, `recurso_cif`, `hmo_ide` y
  `parte_estado` de las no congeladas que toca.

## H. Documentación

- **R43.** `docs/ARCHITECTURE.md`, `partes-proyecto.md` (§4.6, §5.1, §6.6) y
  `azure-apps/partes.md` documentan alta, empresa del membrete, obras gemelas,
  columnas nuevas y que `SIGRID_EMPRESA` deja de usarse.
