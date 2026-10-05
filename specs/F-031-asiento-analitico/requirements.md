<!-- specs/F-031-asiento-analitico/requirements.md -->
# F-031 · El parte registrado en Sigrid acaba en el asiento analítico de la obra

Humano, 2026-10-05, URGENTE. Rigor **crítico** (sv5 escribe en Sigrid de
producción). Fuente: correo de Juan Romero (Admon. y Control de Costes,
2026-09-29, «ARBOL ANALITICO OBRAS»). Datos: `progress/spec_F-031.md`
(anexo, §D1–§D8). Decisiones DA1–DA8: design §8, **a validar con Juan Romero
y aprobar por el humano antes de implementar**. Toca **sv5** (lógica) y
**sv4** (solo pintar un aviso).

## Lo que se ha descubierto (y por qué la feature es pequeña)

Sigrid **ya genera** el asiento analítico de cada parte: el proceso de
Administración «Contabilizar parte» (cambio de estado del `hmo` a
**Imputado**, `con.est = 10`) crea un asiento analítico (`asa`, `con.tip =
32`, serie `ANA<AA>/NNNNN`, mismo resumen y fecha que el parte) con el
**Debe** de cada `hmores.caaide` por su `tot` y el **Haber** en la cuenta de
contrapartida del recurso (`res.caaconide`, centro `CP`). 441/441 partes
imputados de 2025 y 58/58 de 2026 lo tienen; ninguno de los demás (§D2–§D4).
sv5 **no tiene que escribir asientos**: F-021 ya escribe `caaide`. El hueco
real es otro: sv5 escribe hoy en el parte del mes **sin mirar su estado**, y
una línea que entra en un parte ya **Imputado** nunca llega a la analítica
(su asiento ya está hecho), y pisar un conflicto ahí borra una línea que el
asiento sí cuenta (§D5).

Glosario:
- **Partes del periodo**: los `hmo` de la obra destino, año y mes, con
  `reside = 0` y `con.tip` de parte (35), cada uno con su estado `con.est`.
- **Imputado** = `EST_PARTE_IMPUTADO` (10, `conest` «IMP»); **Cerrado** =
  `EST_PARTE_CERRADO` (3, «CER»); En registro = 1.
- **Parte elegido**: el que recibe las líneas del periodo.
- **Contabilizados**: los partes del periodo en estado Imputado.

## A. Estado del parte destino (sv5)

- **R1.** Para cada periodo con acciones `escribir`, sv5 debe leer **todos**
  los partes del periodo con su estado, en **una** consulta por periodo.
- **R2.** El parte elegido debe ser el de mayor `ide` cuyo estado **no** es
  Imputado; los Imputados del periodo deben quedar como contabilizados
  (`ide` y código).
- **R3.** SI todos los partes del periodo están Imputados, ENTONCES el periodo
  debe tratarse como parte **nuevo** (`existe = false`, `complementario =
  true`, código del correlativo de siempre) y llevar un aviso que nombre los
  contabilizados y el nuevo (DA1).
- **R4.** Ninguna sentencia de escritura de sv5 (`INSERT INTO hmores`,
  `DELETE FROM hmores`) debe referirse a un parte Imputado.
- **R5.** MIENTRAS el parte elegido está Cerrado, sv5 debe escribir en él como
  hoy y el periodo debe llevar el aviso «cerrado por Administración: las
  líneas entrarán en su asiento analítico cuando lo contabilice» (DA2).
- **R6.** MIENTRAS el parte elegido está en otro estado, o el periodo no tiene
  partes, el comportamiento debe ser idéntico al de hoy y sin aviso.
- **R7.** Los estados Imputado y Cerrado deben salir de los ajustes
  `EST_PARTE_IMPUTADO` (10) y `EST_PARTE_CERRADO` (3) de sv5 (DA7).

## B. Conflictos con lo ya contabilizado (sv5)

- **R8.** CUANDO una acción `escribir` coincide en recurso, día y tipo de
  hora con una línea **ajena** (sin su synckey) de un parte contabilizado del
  periodo, ENTONCES debe pasar a `omitir` con motivo `parte_contabilizado`
  (texto que nombra el parte), con `caa_ide = 0` y sin campos `caa_*` (F-021
  R16), y no escribirse (DA5).
- **R9.** Los conflictos confirmables solo deben calcularse contra el parte
  elegido: una clave en `pisar_claves` nunca borra una línea de un parte
  Imputado.
- **R10.** Una línea nuestra (synckey) que vive en un parte Imputado debe
  seguir siendo `ya_registrado`, sin escribir ni borrar nada.

## C. Lecturas, lock y contrato (sv5)

- **R11.** SI la lectura de partes del periodo falla o viene `truncated`,
  ENTONCES la petición debe fallar entera sin escribir (como hoy).
- **R12.** La elección de parte y los avisos deben evaluarse en el mismo paso
  que hoy (dentro del lock al escribir), de modo que `preflight` y `ejecutar`
  obtengan lo mismo para el mismo estado de Sigrid.
- **R13.** Cada elemento de `partes` del preflight y del resultado debe llevar
  `estado`, `complementario`, `contabilizados` (códigos) y `aviso`; los campos
  que ya existen no cambian de nombre ni de valor.
- **R14.** Por periodo, sv5 debe registrar un INFO con obra, año/mes, estado
  del parte elegido, número de contabilizados y si es complementario, sin
  nombres ni DNIs.

## D. Portal (sv4, solo presentación)

- **R15.** CUANDO un parte del preflight trae `aviso`, el resumen del modal de
  aprobación debe mostrarlo (escapado) junto a ese parte; no cambia botones ni
  payload.
- **R16.** SI el parte no trae `aviso` (o sv5 es anterior a F-031), ENTONCES el
  resumen debe pintarse exactamente como hoy.

## E. Lo que no cambia

- **R17.** sv5 no debe generar sentencias sobre `asa`, `apa`, `apu`, `asi` ni
  cambiar el `con.est` de ningún parte: contabilizar es de Administración
  (DA4).
- **R18.** Las acciones `dedicacion` (F-019), `omitir` y `ya_registrado` no
  deben depender del estado del parte ni abrir parte.
- **R19.** La regla no distingue empresa: un parte de la empresa 28 en
  registro se comporta exactamente como hoy.
- **R20.** Desaprobar (F-004), la comprobación de F-024 y la cuenta de F-021
  no cambian; sus tests siguen en verde sin tocarlos.

## F. Herramienta de comprobación (consola, solo lectura)

- **R21.** `services/partes-transfer/comprobar_asiento_analitico.py --empresa
  E --obra COD --ano A --mes M` debe listar cada parte del periodo con código,
  estado, nº de líneas, nº de líneas nuestras (synckey) e importe con cuenta.
- **R22.** Para cada parte Imputado debe localizar su asiento analítico
  (empresa + resumen + fecha del parte, tipo 32), comparar el Debe por cuenta
  con el importe de las líneas por cuenta (tolerancia 0,01 €) y dar el
  veredicto `cuadra`, `descuadre`, `sin_asiento` o `varios_asientos`.
- **R23.** La salida no debe contener nombres, DNIs ni cuentas de contrapartida
  por persona: solo cuentas del centro de la obra y el total del Haber.
- **R24.** La comparación debe ser una función pura con tests; el script no
  escribe (solo `POST /api/sql/read`).

## G. Documentación

- **R25.** `docs/ARCHITECTURE.md` (semántica nueva 16),
  `docs/referencia/partes-proyecto.md` y `azure-apps/partes.md` deben
  describir: el asiento lo genera Sigrid al contabilizar, sv5 lee `con.est`
  de los partes y no escribe en uno Imputado, el parte complementario y la
  herramienta de comprobación.
