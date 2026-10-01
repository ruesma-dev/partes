<!-- specs/F-021-cuenta-analitica-sigrid/requirements.md -->
# F-021 · Cuenta analítica en las líneas que sv5 registra en Sigrid

Humano, 2026-09-30. Rigor **crítico** (cambia lo que se escribe en Sigrid en
producción). Origen: correo de Administración y Control de Costes («No
arrastra cuenta analítica del recurso»). Datos: `progress/explore_F-021_sigrid.md`
(§N). Decisiones DA1–DA12: design §8, **a aprobar antes de implementar**.
Toca **sv5** (lógica y escritura) y **sv4** (solo el aviso del preflight).

Glosario (§1–§3):
- **Cuenta** = fila de `caa` (propiedades de `con`), código `<centro>.<subcuenta>`.
- **Subcuenta** de un código = el texto tras su **primer** punto, sin espacios
  a los lados. Un código vacío, sin punto o con subcuenta vacía no tiene.
- **Plantilla del recurso** para un tipo de hora H = la cuenta de
  `reshor.caaide` del par (recurso, H), si no es 0 ni NULL.
- **Tipo por defecto** del recurso = `res.horide`.
- **Centro de la obra** = `obr.cenide` de la obra destino (el mismo que sv5 ya
  escribe en `hmores.cenide`; en modo pruebas, el de la obra de pruebas).

## A. De dónde sale la cuenta (sv5, función pura)

- **R1.** La subcuenta de una línea a escribir debe ser la de la plantilla
  del recurso para el **tipo de hora que se escribe** (`hora_ide` final de la
  acción, no el leído del papel).
- **R2.** SI esa plantilla no existe o no tiene subcuenta, ENTONCES la
  subcuenta debe ser la de la plantilla del recurso para su **tipo por
  defecto** (§3: así llevan cuenta las incidencias `CI*`).
- **R3.** SI ninguna de las dos da subcuenta, ENTONCES la línea debe quedar
  sin cuenta con motivo `recurso_sin_cuenta` y **sin aviso** (§2: todos los
  recursos de la empresa 28 están así, y el humano tampoco la pone).
- **R4.** La cuenta de la línea debe ser la única cuenta cuyo centro
  (`caa.cenide`) es el centro de la obra, cuya empresa (`con.emp`) es la de
  la obra destino y cuya subcuenta es la de R1–R2. Nunca el `ide` de la
  plantilla (§3: 0 coincidencias de `ide`).
- **R5.** SI el centro de la obra no tiene ninguna cuenta con esa subcuenta,
  o la obra destino no tiene centro, ENTONCES la línea debe quedar sin cuenta
  con motivo `obra_sin_cuenta` y un aviso que nombre la subcuenta y la obra.
- **R6.** SI hay más de una cuenta candidata para R4, ENTONCES la línea debe
  quedar sin cuenta con motivo `cuenta_ambigua` y un aviso; nunca se elige una.
- **R7.** Ni `res.caaide`, ni `emp.caaide`, ni la cuenta de la partida
  (`obrparpar.caaide`), ni `auxhor.caacod` deben intervenir (§2, §5).
- **R8.** Una línea sin cuenta (R3, R5, R6) **se escribe igual** con
  `caaide = 0`: la falta de cuenta nunca omite ni bloquea una línea.

## B. Lecturas de Sigrid (sv5)

- **R9.** `horas_de_recursos` debe devolver, en la misma consulta de hoy, el
  código de la cuenta de `reshor.caaide` de cada fila (o nada) y si esa fila
  es el tipo por defecto del recurso (`reshor.horide = res.horide`).
- **R10.** sv5 debe leer las cuentas del centro con **una** consulta por
  petición, filtrada por centro, empresa y las subcuentas pedidas, y solo si
  alguna acción a escribir tiene subcuenta.
- **R11.** SI esa lectura falla o viene `truncated`, ENTONCES `preparar` debe
  lanzar excepción y la petición no escribe nada (como hoy `datos_recursos`).

## C. Pipeline y escritura (sv5)

- **R12.** La cuenta se resuelve en `preparar`, después de las reglas y fuera
  del lock, solo para las acciones `escribir`; `preflight` y `ejecutar`
  obtienen exactamente la misma.
- **R13.** `AccionLinea` debe llevar `caa_ide` (0 si no hay), `caa_cod`,
  `caa_motivo` y `caa_aviso` (texto solo en R5 y R6), y el JSON del
  preflight (`acciones`) debe incluirlos.
- **R14.** El `INSERT INTO hmores` debe escribir en `caaide` el `caa_ide` de
  la acción como **parámetro**, en lugar del literal 0; el resto de columnas
  y valores no cambia (`cuaide` sigue sin escribirse).
- **R15.** Cada entrada de `escritas` del resultado debe incluir `caa_cod`.
- **R16.** Una acción `omitir` debe salir con `caa_ide = 0` y sin motivo de
  cuenta; una `ya_registrado` no se reescribe ni se actualiza (la synckey no
  cambia), tenga la cuenta que tenga en Sigrid.
- **R17.** CUANDO se pisa un conflicto confirmado, la línea nueva debe llevar
  la cuenta resuelta; la clave de conflicto (recurso + día + tipo de hora) no
  cambia.
- **R18.** CUANDO `preparar` resuelve cuentas, debe registrar en el log un
  INFO con la obra y el recuento por motivo (`ok`, `recurso_sin_cuenta`,
  `obra_sin_cuenta`, `cuenta_ambigua`), sin nombres ni DNIs.

## D. Portal (sv4, solo presentación)

- **R19.** CUANDO el preflight trae acciones `escribir` con `caa_aviso`, el
  modal de aprobación debe mostrar un bloque informativo con su número y una
  fila por línea (nombre · fecha · aviso); no cambia botones ni payload.
- **R20.** SI el preflight no trae `caa_aviso` (sv5 anterior a F-021) o no
  hay ninguno, ENTONCES el modal no debe pintar el bloque.
- **R21.** `POST /api/aprobar/preflight` de sv4 debe devolver los campos
  `caa_*` de cada acción tal como llegan de sv5.

## E. Lo que no cambia

- **R22.** Desaprobar un parte (F-004) no debe tocar Sigrid ni la cuenta de
  líneas ya registradas: sigue sin cambios.
- **R23.** sv3, la base `partes` y el esquema ORM no cambian.

## F. Documentación

- **R24.** `docs/ARCHITECTURE.md`, `docs/referencia/partes-proyecto.md` §3.5 y
  `azure-apps/partes.md` §3.5 deben describir la regla de la cuenta (origen,
  destino, sin cuenta) y la lectura nueva de `caa`.
