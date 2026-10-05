<!-- specs/F-031-asiento-analitico/requirements.md -->
# F-031 · El parte registrado en Sigrid acaba en el asiento analítico de la obra

Humano, 2026-10-05, URGENTE. Rigor **crítico** (sv5 escribe en Sigrid de
producción). Fuente: correo de Juan Romero (Admon. y Control de Costes,
2026-09-29). Datos: `progress/spec_F-031.md` (anexo §D1–§D10). Decisiones
**aprobadas por el humano el 2026-10-05** (design §8; DA6 en su versión 3).
Abiertas: DA3 (Juan Romero) y **DA6-e** (humano, R18). Toca **sv5** (lógica)
y **sv4** (solo pintar avisos). **Modifica F-021** (origen de la cuenta, §D).

Sigrid **ya genera** el asiento analítico de cada parte al «Contabilizar»
(parte **Imputado**; design §1). sv5 no escribe asientos: no debe escribir
en un parte Imputado y debe poner en `hmores.caaide` la cuenta de la
**partida que la línea tiene en el portal**, sea CI o CD (DA6).

Glosario:
- **Partes del periodo**: los `hmo` de la obra destino, año y mes, con
  `reside = 0` y `con.tip` de parte (35), cada uno con su estado `con.est`.
- **Imputado** = `EST_PARTE_IMPUTADO` (10); **Cerrado** = `EST_PARTE_CERRADO`
  (3); En registro = 1. **Contabilizados**: los Imputados del periodo.
- **Parte elegido**: el que recibe las líneas del periodo.
- **Partida de la línea**: `paride` de la acción, la del portal (automática
  de sv3 o corregida por el administrativo); su cuenta, `obrparpar.caaide`.
- **Rama** de una cuenta: el grupo de nivel 2 del árbol analítico de su
  centro del que cuelga (`caa.padide` → `cag` → `cag.padide`), p. ej. `CI`.
  **Cuenta de coste**: la de rama `CD`, `CI` o `CP` (no `IN`, ingresos).

## A. Estado del parte destino (sv5)

- **R1.** Para cada periodo con acciones `escribir`, sv5 debe leer **todos**
  los partes del periodo con su estado, en **una** consulta por periodo.
- **R2.** El parte elegido debe ser el de mayor `ide` cuyo estado **no** es
  Imputado; los Imputados del periodo quedan como contabilizados.
- **R3.** SI todos los partes del periodo están Imputados, ENTONCES sv5 **no**
  debe crear parte: cada acción `escribir` del periodo pasa a `omitir` con
  motivo `parte_contabilizado` y un texto que nombra el parte y pide a
  Administración **reabrirlo en Sigrid** y volver a aprobar (DA1); el parte
  sale en `partes` con su estado y un aviso con el nº de líneas retenidas.
- **R4.** Ninguna sentencia de escritura de sv5 (`INSERT INTO hmores`,
  `DELETE FROM hmores`, cabecera de parte) debe referirse a un parte Imputado.
- **R5.** MIENTRAS el parte elegido está Cerrado, sv5 debe escribir en él
  como hoy y el periodo debe llevar el aviso «cerrado por Administración: las
  líneas entrarán en su asiento analítico cuando lo contabilice» (DA2).
- **R6.** MIENTRAS el parte elegido está en otro estado, o el periodo no tiene
  partes, el comportamiento debe ser idéntico al de hoy y sin aviso.
- **R7.** Los estados Imputado y Cerrado deben salir de los ajustes
  `EST_PARTE_IMPUTADO` (10) y `EST_PARTE_CERRADO` (3) de sv5 (DA7).
- **R8.** CUANDO se vuelven a aprobar líneas de un periodo cuyo parte ya no
  está Imputado (Administración lo reabrió), ENTONCES deben escribirse en él
  como en R5/R6, sin nada especial.

## B. Conflictos con lo ya contabilizado (sv5)

- **R9.** CUANDO una acción `escribir` coincide en recurso, día y tipo de
  hora con una línea **ajena** (sin su synckey) de un parte contabilizado del
  periodo, ENTONCES debe pasar a `omitir` con motivo `parte_contabilizado`
  (texto que nombra el parte) y no escribirse (DA5).
- **R10.** Los conflictos confirmables solo se calculan contra el parte
  elegido no Imputado: una clave de `pisar_claves` nunca borra en un Imputado.
- **R11.** Una línea nuestra (synckey) que vive en un parte Imputado debe
  seguir siendo `ya_registrado`, sin escribir ni borrar nada.
- **R12.** Toda acción que pasa a `omitir` por R3 o R9 debe salir con
  `caa_ide = 0` y sin `caa_motivo`, `caa_aviso`, `caa_origen` ni `caa_nota`.

## C. Lecturas, lock y contrato del parte (sv5)

- **R13.** SI la lectura de partes del periodo falla o viene `truncated`,
  ENTONCES la petición falla entera sin escribir.
- **R14.** La elección de parte, R3 y R9 deben evaluarse en el mismo paso que
  hoy (dentro del lock al escribir): `preflight` y `ejecutar` obtienen lo
  mismo para el mismo estado de Sigrid.
- **R15.** Cada elemento de `partes` del preflight y del resultado debe llevar
  `estado`, `contabilizados` (códigos) y `aviso`; los campos existentes no
  cambian de nombre ni de valor.
- **R16.** Por periodo, sv5 debe registrar un INFO con obra, año/mes, estado
  del parte elegido, nº de contabilizados y nº de líneas retenidas por R3,
  sin nombres ni DNIs.

## D. Cuenta analítica según la partida (sv5; modifica F-021, DA6)

- **R17.** SI la partida de una acción `escribir` tiene cuenta de coste,
  ENTONCES la subcuenta de la línea debe ser la de la cuenta de la partida
  (`caa_origen = "partida"`), y la cuenta, la del centro de la obra destino
  con esa subcuenta (F-021 R4–R6, incluido modo pruebas).
- **R18.** SI la acción no tiene partida, la partida no está en Sigrid o no
  tiene cuenta de coste (ninguna, o solo de ingresos `INGR`), ENTONCES,
  provisional hasta DA6-e, la subcuenta debe salir de la ficha del recurso
  como en F-021 R1–R2 (`caa_origen = "recurso"`) con una `caa_nota` que dice
  por qué y nombra la partida.
- **R19.** La regla no mira el tipo de coste (`tipcos`) ni el oficio del
  recurso: una partida CD, CI o CP con cuenta de coste se trata igual (R17),
  aunque su cuenta difiera de la del recurso, y no hay nota «pendiente».
- **R20.** SI tampoco el recurso da subcuenta (F-021 R3), ENTONCES la línea va
  sin cuenta con `recurso_sin_cuenta`, `caa_origen = None` y **sin** nota
  (Porsan, empresa 28, sigue igual).
- **R21.** `AccionLinea` debe llevar `caa_origen` y `caa_nota`, y el JSON del
  preflight (`acciones`) debe incluirlos; `caa_motivo` y `caa_aviso`
  conservan su significado de F-021 (solo línea sin cuenta).
- **R22.** sv5 debe leer las partidas con **una** consulta por petición
  (código de su cuenta y rama), solo si alguna acción `escribir`
  tiene partida, en `preparar`, fuera del lock; un fallo o `truncated` tumba
  la petición sin escribir (como F-021 R11).
- **R23.** La lectura de cuentas del centro sigue siendo **una** por petición
  (F-021 R10), con las subcuentas de ambos orígenes.
- **R24.** sv5 debe registrar un INFO `origen cuenta` con la obra y el
  recuento por origen y por nota, sin nombres ni DNIs; el INFO de F-021 R18
  no cambia.
- **R25.** F-021 R7 («la partida no interviene») queda sustituido por R17–
  R19; el resto de F-021 sigue vigente y sus tests no cambian.

## E. Portal (sv4, solo presentación)

- **R26.** CUANDO un parte del preflight trae `aviso`, el resumen del modal
  debe mostrarlo (escapado) junto a ese parte.
- **R27.** CUANDO hay acciones `escribir` con `caa_nota`, el modal debe pintar
  un bloque informativo aparte del de F-021 con su número y una fila por
  línea (nombre · fecha · nota); no cambia botones ni payload.
- **R28.** SI el preflight no trae esos campos (sv5 anterior a F-031) o vienen
  vacíos, ENTONCES el modal debe pintarse exactamente como hoy.

## F. Lo que no cambia

- **R29.** sv5 no debe generar sentencias sobre `asa`, `apa`, `apu`, `asi` ni
  cambiar el `con.est` de ningún parte (DA4): reabrir y contabilizar es de
  Administración en Sigrid.
- **R30.** Las acciones `dedicacion` (F-019), `omitir` y `ya_registrado` no
  dependen del estado del parte ni de la partida.
- **R31.** La regla no distingue empresa: un parte de la empresa 28 en
  registro y sin cuentas se comporta exactamente como hoy.
- **R32.** Desaprobar (F-004) y la comprobación de F-024 no cambian.

## G. Herramienta de comprobación (consola, solo lectura; DA8)

- **R33.** `services/partes-transfer/comprobar_asiento_analitico.py --empresa
  E --obra COD --ano A --mes M` debe listar cada parte del periodo con código,
  estado, nº de líneas, nº de líneas nuestras (synckey) e importe con cuenta.
- **R34.** Para cada parte Imputado debe localizar su asiento (empresa +
  resumen + fecha, tipo 32), comparar el Debe por cuenta con las líneas por
  cuenta (tolerancia 0,01 €) y dar `cuadra`, `descuadre`, `sin_asiento` o
  `varios_asientos`.
- **R35.** La salida no debe contener nombres, DNIs ni contrapartidas por
  persona: solo cuentas del centro de la obra y el total del Haber.
- **R36.** La comparación debe ser una función pura con tests; el script solo
  usa `POST /api/sql/read`.

## H. Documentación

- **R37.** `docs/ARCHITECTURE.md`, `partes-proyecto.md` §3.5 y
  `azure-apps/partes.md` §3.5 deben describir el asiento de Sigrid, el parte
  Imputado (reabrir), la cuenta por partida y la herramienta.
