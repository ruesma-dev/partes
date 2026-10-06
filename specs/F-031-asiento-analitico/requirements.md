<!-- specs/F-031-asiento-analitico/requirements.md -->
# F-031 · El parte registrado en Sigrid acaba en el asiento analítico de la obra

Humano, 2026-10-05, URGENTE. Rigor **crítico**. Fuente: correo de Juan Romero
(2026-09-29); datos en `progress/spec_F-031.md` (§D1–§D11). **Versión 5**
(2026-10-06): la v4 (design §8) más el **alta protegida** frente a
`porcentajes` y su dependencia (§I, §J; design §13). Toca **sv5** (lógica) y
**sv4** (solo pintar). Amplía F-021. Sigrid **ya genera** el asiento al
«Contabilizar» (design §1): sv5 no lo escribe; elige parte y cuenta.

Glosario:
- **Partes del periodo**: los `hmo` de la obra destino, año y mes, con
  `reside = 0` y `con.tip` de parte (35), cada uno con su `con.est`.
- **En registro** = `EST_PARTE_ACTIVO` (1). **Cerrado** = cualquier otro
  estado (3 Cerrado, 10 Imputado…). **Complementario**: el parte elegido
  cuando el periodo tiene algún cerrado. **Alta**: crear `con` + `hmo`.

## A. Parte destino (sv5; DA1/DA2)

- **R1.** Para cada periodo con acciones `escribir`, sv5 debe leer **todos**
  los partes del periodo con su estado, en **una** consulta por periodo.
- **R2.** El parte elegido debe ser el de mayor `ide` En registro del periodo.
- **R3.** SI el periodo tiene partes y ninguno está En registro, ENTONCES sv5
  debe proponer (preflight) y crear (escritura) un complementario nuevo:
  código `PT<AA>/NNNNN` por empresa (F-023), En registro, `Parte <obra>`.
- **R4.** SI el periodo no tiene partes, ENTONCES el parte nuevo se crea como
  hoy, con `complementario = False` y sin aviso.
- **R5.** Ninguna sentencia de sv5 (`INSERT`/`DELETE` de `hmores`, alta) debe
  referirse a un parte cerrado ni modificar `con` o `hmo` de uno existente.
- **R6.** MIENTRAS el periodo no tiene partes cerrados, elección y escritura
  deben ser las de hoy, sin aviso (salvo R12 con varios En registro).
- **R7.** En registro sale de `EST_PARTE_ACTIVO`; los nombres, de
  `EST_PARTE_CERRADO` (3, «Cerrado») y `EST_PARTE_IMPUTADO` (10,
  «Imputado»); otro estado se nombra «estado N» (DA7).
- **R8.** CUANDO se aprueban más líneas de un periodo cuyo complementario ya
  existe En registro, ENTONCES deben ir a él sin crear otro.
- **R9.** (v5) Sustituido por R43–R45.

## B. Duplicados y conflictos en TODOS los partes del periodo (sv5)

- **R10.** Una línea nuestra (synckey) que ya vive en cualquier parte, también
  cerrado, sigue siendo `ya_registrado`, sin escribir ni borrar nada.
- **R11.** CUANDO una acción `escribir` coincide en recurso, día y tipo de
  hora con una línea **ajena** de un parte **cerrado** del periodo, ENTONCES
  pasa a `omitir` con motivo `parte_cerrado: …` (parte y estado; DA5).
- **R12.** CUANDO coincide con una línea ajena de un parte **En registro** (el
  elegido u otro), ENTONCES sale como conflicto confirmable como hoy, con el
  `parte_cod` donde vive; R11 prevalece sobre R12.
- **R13.** `pisar_claves` solo debe borrar líneas de partes En registro.
- **R14.** Toda acción omitida por R11 sale con `caa_ide = 0` y sin
  `caa_motivo`, `caa_aviso`, `caa_origen` ni `caa_nota`.

## C. Lecturas, lock y contrato del parte (sv5)

- **R15.** SI la lectura de partes del periodo o de líneas existentes falla o
  viene `truncated`, ENTONCES la petición falla entera sin escribir.
- **R16.** La elección, R3 y R11–R12 se evalúan en el mismo paso que hoy
  (dentro del lock al escribir): `preflight` y `ejecutar` coinciden.
- **R17.** Cada elemento de `partes` (preflight y resultado) debe llevar
  `estado` (`None` si es nuevo), `complementario`, `cerrados` (códigos),
  `del_periodo` (ide, cod, est) y `aviso`; los campos existentes no cambian.
- **R18.** CUANDO el parte es complementario, `aviso` nombra los cerrados y
  el parte al que van las líneas (nuevo o existente); si no, `None`.
- **R19.** Por periodo, un INFO (obra, año/mes, código y estado del elegido,
  complementario, nº de cerrados y de omitidas por R11), sin nombres.

## D. Cuenta analítica: manda el recurso, la partida es respaldo (DA6)

- **R20.** La cuenta de una acción `escribir` sigue saliendo de la ficha de
  horas del recurso en el centro de la obra destino, como F-021 R1–R6
  (`caa_origen = "recurso"`), aunque la partida tenga otra.
- **R21.** SI el recurso no da subcuenta Y la de la partida es de coste
  (`obrparpar.caaide` que empieza por `CI` o `CD`), ENTONCES la línea lleva
  esa subcuenta en el centro de la obra con F-021 R4–R6, `caa_origen =
  "partida"` y una `caa_nota` con partida y subcuenta, sin nombres.
- **R22.** SI tampoco (sin partida, no encontrada, sin cuenta, `INGR`, `CP`…),
  ENTONCES va sin cuenta como F-021 R3, `caa_origen = None`, sin nota.
- **R23.** `AccionLinea` lleva `caa_origen` y `caa_nota`, también en el JSON
  del preflight; `caa_motivo` y `caa_aviso` conservan su significado.
- **R24.** Las partidas se leen con **una** consulta por petición, solo si
  alguna acción sin subcuenta del recurso tiene partida, en `preparar`
  (fuera del lock); fallo o `truncated` tumba la petición sin escribir.
- **R25.** La lectura de cuentas del centro sigue siendo **una** por petición
  (F-021 R10), con las subcuentas de ambos orígenes.
- **R26.** Un INFO `origen cuenta` con la obra y el recuento
  recurso/partida/ninguna, sin nombres; el INFO de F-021 R18 no cambia.
- **R27.** F-021 R7 queda matizado por R21; el resto y sus tests, igual.

## E. Portal (sv4, solo presentación)

- **R28.** CUANDO un parte del preflight trae `complementario`, el modal lo
  rotula «complementario» y muestra su `aviso` (escapado).
- **R29.** CUANDO hay `escribir` con `caa_nota`, el modal pinta un bloque
  aparte del de F-021 (nombre · fecha · nota); botones y payload, igual.
- **R30.** SI el preflight no trae esos campos o vienen vacíos, ENTONCES el
  modal se pinta exactamente como hoy.

## F. Lo que no cambia

- **R31.** sv5 no escribe en `asa`, `apa`, `apu`, `asi` ni cambia ningún `con.est` (DA4).
- **R32.** `dedicacion`, `omitir` y `ya_registrado` no dependen del parte ni la partida.
- **R33.** Un periodo de la empresa 28 sin cerrados ni cuentas, como hoy.
- **R34.** Desaprobar (F-004) y la comprobación de F-024 no cambian.

## G. Herramienta de comprobación (consola, solo lectura; DA8)

- **R35.** `services/partes-transfer/comprobar_asiento_analitico.py --empresa
  E --obra COD --ano A --mes M` lista cada parte del periodo con código,
  estado, nº de líneas, nº de líneas nuestras e importe con cuenta.
- **R36.** Para cada parte Imputado localiza su asiento (empresa + resumen +
  fecha, tipo 32), compara el Debe por cuenta con las líneas por cuenta
  (0,01 €) y da `cuadra`, `descuadre`, `sin_asiento` o `varios_asientos`.
- **R37.** La salida no contiene nombres, DNIs ni contrapartidas por persona.
- **R38.** La comparación es pura y con tests; solo `POST /api/sql/read`.

## H. Alta protegida frente a `porcentajes` (sv5; humano, 2026-10-06)

- **R40.** Toda alta (R3 y R4) pasa por una única función del pipeline, con
  `con` y `hmo` en **una** llamada a `escribir` (una transacción).
- **R41.** La cabecera `con` solo se inserta SI su código está libre en la
  empresa (`cod`, `emp`, `tip`) Y no hay ya un parte En registro de la obra y
  periodo, ambas con `WITH (UPDLOCK, HOLDLOCK)` fuera del agregado
  `MAX(ide)`; SQL y parámetros idénticos a `porcentajes` (design §13).
- **R42.** El `hmo` se cuelga del `con` (código, tipo, empresa) solo si aún no lo tiene.
- **R43.** CUANDO termina el alta, sv5 relee el periodo y usa el parte En
  registro que dé `elegir_parte`, sea suyo o del otro servicio (su `ide`,
  `cod`, `estado`); `creado` solo si el alta insertó filas con ese código.
- **R44.** SI tras el alta no hay parte En registro (código cogido), ENTONCES
  sv5 pide el siguiente código y repite el alta **una** sola vez.
- **R45.** SI tras el reintento sigue sin haberlo, ENTONCES falla con un error
  que nombra obra, periodo y último código, sin insertar líneas.
- **R46.** Por alta, un INFO con obra, periodo, código, intento y si el parte
  usado es propio o de otro servicio, sin nombres ni DNIs.
- **R47.** CUANDO el otro servicio crea un parte entre la lectura y el alta
  (En registro del periodo, o el mismo código en otra obra), ENTONCES las
  líneas van a un único parte y no quedan dos En registro del periodo.

## I. Documentación y dependencia con `porcentajes`

- **R39.** `docs/ARCHITECTURE.md`, `partes-proyecto.md` §3.5 y
  `azure-apps/partes.md` §3.5 describen el asiento, el complementario, la
  cuenta (recurso, respaldo de partida), la herramienta y el alta (§H).
- **R48.** Las cabeceras de `estado_parte.py` y `cuenta_analitica.py` dicen
  que son copia literal en `porcentajes` (F-037) y que cambiarlos obliga a
  avisarle en el mismo trabajo; `stmts_crear_parte`, que el alta es común.
- **R49.** `ARCHITECTURE.md` y `azure-apps/partes.md` («qué se rompe si
  cambia») documentan parte compartido, copias, alta y aviso obligatorio, y
  que no entra en la lista cerrada de `CLAUDE.md` (es entre repositorios).
