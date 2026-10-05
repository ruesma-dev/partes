<!-- specs/F-031-asiento-analitico/requirements.md -->
# F-031 · El parte registrado en Sigrid acaba en el asiento analítico de la obra

Humano, 2026-10-05, URGENTE. Rigor **crítico** (sv5 escribe en Sigrid de
producción). Fuente: correo de Juan Romero (Admon. y Control de Costes,
2026-09-29). Datos: `progress/spec_F-031.md` (anexo §D1–§D11). **Versión 4**:
decisiones del humano del 2026-10-05 (design §8): DA1/DA2 → **parte
complementario**; DA6 → **la cuenta sale del recurso**. La lectura de
«cerrado» es del líder y está **pendiente de confirmar** (design §8). Toca
**sv5** (lógica) y **sv4** (solo pintar). **Amplía F-021** (respaldo, §D).

Sigrid **ya genera** el asiento al «Contabilizar» (design §1): sv5 no lo
escribe; no escribe en partes cerrados y pone la cuenta correcta.

Glosario:
- **Partes del periodo**: los `hmo` de la obra destino, año y mes, con
  `reside = 0` y `con.tip` de parte (35), cada uno con su `con.est`.
- **En registro** = `EST_PARTE_ACTIVO` (1, el ajuste con el que sv5 ya crea
  partes). **Cerrado** = cualquier otro estado (3 Cerrado, 10 Imputado…).
- **Complementario**: el parte elegido (el que recibe las líneas) cuando el
  periodo tiene algún parte cerrado (En registro reutilizado o nuevo).
- **Subcuenta de coste de la partida**: la subcuenta de `obrparpar.caaide`
  si empieza por `CI` o `CD` (`C[ID]`; no `CP`, no `INGR`).

## A. Parte destino (sv5; DA1/DA2)

- **R1.** Para cada periodo con acciones `escribir`, sv5 debe leer **todos**
  los partes del periodo con su estado, en **una** consulta por periodo.
- **R2.** El parte elegido debe ser el de mayor `ide` En registro del periodo.
- **R3.** SI el periodo tiene partes y ninguno está En registro, ENTONCES sv5
  debe proponer (preflight) y crear (escritura) un complementario nuevo con
  el esquema de hoy: cabecera `con` + `hmo`, código `PT<AA>/NNNNN` por
  empresa (F-023), estado En registro y descripción `Parte <obra>`.
- **R4.** SI el periodo no tiene partes, ENTONCES el parte nuevo debe crearse
  como hoy, con `complementario = False` y sin aviso.
- **R5.** Ninguna sentencia de sv5 (`INSERT`/`DELETE` de `hmores`, alta de
  parte) debe referirse a un parte cerrado, ni modificar `con` o `hmo` de un
  parte existente: el estado del original no cambia.
- **R6.** MIENTRAS el periodo no tiene partes cerrados, la elección del parte
  y la escritura deben ser las de hoy, sin aviso (salvo R12 con varios
  partes En registro).
- **R7.** En registro debe salir de `EST_PARTE_ACTIVO`; los nombres de los
  textos, de `EST_PARTE_CERRADO` (3, «Cerrado») y `EST_PARTE_IMPUTADO` (10,
  «Imputado»); otro estado se nombra «estado N» (DA7).
- **R8.** CUANDO se aprueban más líneas de un periodo cuyo complementario ya
  existe En registro, ENTONCES deben ir a él sin crear otro.
- **R9.** SI tras crear el parte la relectura no lo da (código, En registro),
  ENTONCES sv5 debe fallar sin insertar líneas.

## B. Duplicados y conflictos en TODOS los partes del periodo (sv5)

- **R10.** Una línea nuestra (synckey) que ya vive en cualquier parte, también
  cerrado, debe seguir siendo `ya_registrado`, sin escribir ni borrar nada.
- **R11.** CUANDO una acción `escribir` coincide en recurso, día y tipo de
  hora con una línea **ajena** (sin su synckey) de un parte **cerrado** del
  periodo, ENTONCES debe pasar a `omitir` con motivo `parte_cerrado: …` que
  nombra el parte y su estado y dice que esas horas ya constan en él (DA5).
- **R12.** CUANDO coincide con una línea ajena de un parte **En registro** del
  periodo (el elegido u otro), ENTONCES debe salir como conflicto confirmable
  como hoy, con el `parte_cod` del parte donde vive; R11 prevalece sobre R12.
- **R13.** Una clave de `pisar_claves` solo debe borrar líneas de partes En
  registro.
- **R14.** Toda acción que pasa a `omitir` por R11 debe salir con
  `caa_ide = 0` y sin `caa_motivo`, `caa_aviso`, `caa_origen` ni `caa_nota`.

## C. Lecturas, lock y contrato del parte (sv5)

- **R15.** SI la lectura de partes del periodo o de líneas existentes falla o
  viene `truncated`, ENTONCES la petición falla entera sin escribir.
- **R16.** La elección, R3 y R11–R12 deben evaluarse en el mismo paso que hoy
  (dentro del lock al escribir): `preflight` y `ejecutar` coinciden.
- **R17.** Cada elemento de `partes` del preflight y del resultado debe llevar
  `estado` (del elegido; `None` si es nuevo), `complementario`, `cerrados`
  (códigos), `del_periodo` (ide, cod, est) y `aviso`; los campos existentes
  no cambian de nombre ni de valor.
- **R18.** CUANDO el parte es complementario, ENTONCES `aviso` debe nombrar los
  partes cerrados con su estado y decir que las líneas van al complementario
  (nuevo o existente, con su código); si no lo es, `aviso` es `None`.
- **R19.** Por periodo, sv5 debe registrar un INFO con obra, año/mes, código y
  estado del elegido, complementario sí/no, nº de cerrados y nº de omitidas
  por R11, sin nombres ni DNIs.

## D. Cuenta analítica: manda el recurso, la partida es respaldo (DA6)

- **R20.** La cuenta de una acción `escribir` debe seguir saliendo de la ficha
  de horas del recurso llevada al centro de la obra destino, exactamente
  como F-021 R1–R6 (`caa_origen = "recurso"`), aunque la partida tenga otra.
- **R21.** SI el recurso no da subcuenta (F-021 R3) Y la partida de la acción
  tiene subcuenta de coste, ENTONCES la línea debe llevar esa subcuenta en
  el centro de la obra destino con F-021 R4–R6 (modo pruebas, obra sin
  cuenta, ambigua), `caa_origen = "partida"` y una `caa_nota` que nombra la
  partida y la subcuenta, sin nombres de personas.
- **R22.** SI tampoco hay subcuenta de coste de la partida (sin partida, no
  encontrada, sin cuenta, `INGR`, `CP`…), ENTONCES la línea va sin cuenta
  como F-021 R3 (`recurso_sin_cuenta`, sin aviso), `caa_origen = None` y sin
  nota (Porsan, empresa 28, sigue igual).
- **R23.** `AccionLinea` debe llevar `caa_origen` y `caa_nota`, y el JSON del
  preflight (`acciones`) debe incluirlos; `caa_motivo` y `caa_aviso`
  conservan su significado de F-021.
- **R24.** sv5 debe leer las partidas con **una** consulta por petición, solo
  si alguna acción `escribir` sin subcuenta del recurso tiene partida, en
  `preparar`, fuera del lock; un fallo o `truncated` tumba la petición sin
  escribir (como F-021 R11).
- **R25.** La lectura de cuentas del centro sigue siendo **una** por petición
  (F-021 R10), con las subcuentas de ambos orígenes.
- **R26.** sv5 debe registrar un INFO `origen cuenta` con la obra y el
  recuento recurso/partida/ninguna, sin nombres ni DNIs; el INFO de F-021
  R18 no cambia.
- **R27.** F-021 R7 («la partida no interviene») queda matizado por R21; el
  resto de F-021 sigue vigente y sus tests no cambian.

## E. Portal (sv4, solo presentación)

- **R28.** CUANDO un parte del preflight trae `complementario`, el resumen del
  modal debe rotularlo «complementario» y mostrar su `aviso` (escapado).
- **R29.** CUANDO hay acciones `escribir` con `caa_nota`, el modal debe pintar
  un bloque informativo aparte del de F-021 con su número y una fila por
  línea (nombre · fecha · nota); no cambia botones ni payload.
- **R30.** SI el preflight no trae esos campos (sv5 anterior a F-031) o vienen
  vacíos, ENTONCES el modal debe pintarse exactamente como hoy.

## F. Lo que no cambia

- **R31.** sv5 no debe generar sentencias sobre `asa`, `apa`, `apu`, `asi` ni
  cambiar el `con.est` de ningún parte (DA4).
- **R32.** Las acciones `dedicacion` (F-019), `omitir` y `ya_registrado` no
  dependen del estado del parte ni de la partida.
- **R33.** La regla no distingue empresa: un periodo de la empresa 28 sin
  partes cerrados y sin cuentas se comporta exactamente como hoy.
- **R34.** Desaprobar (F-004) y la comprobación de F-024 no cambian.

## G. Herramienta de comprobación (consola, solo lectura; DA8)

- **R35.** `services/partes-transfer/comprobar_asiento_analitico.py --empresa
  E --obra COD --ano A --mes M` debe listar cada parte del periodo con código,
  estado, nº de líneas, nº de líneas nuestras (synckey) e importe con cuenta.
- **R36.** Para cada parte Imputado debe localizar su asiento (empresa +
  resumen + fecha, tipo 32), comparar el Debe por cuenta con las líneas por
  cuenta (tolerancia 0,01 €) y dar `cuadra`, `descuadre`, `sin_asiento` o
  `varios_asientos`.
- **R37.** La salida no debe contener nombres, DNIs ni contrapartidas por
  persona: solo cuentas del centro de la obra y el total del Haber.
- **R38.** La comparación debe ser una función pura con tests; el script solo
  usa `POST /api/sql/read`.

## H. Documentación

- **R39.** `docs/ARCHITECTURE.md`, `partes-proyecto.md` §3.5 y
  `azure-apps/partes.md` §3.5 deben describir el asiento, el complementario,
  la cuenta (recurso, respaldo de partida) y la herramienta.
