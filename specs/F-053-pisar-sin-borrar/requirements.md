<!-- specs/F-053-pisar-sin-borrar/requirements.md -->
# F-053 · Pisar sin borrar: el pisado de conflictos de sv5 pone a 0 en Sigrid — Requisitos

**Servicios tocados: sv5** (sentencia del pisado, detección de choques, motivos, resultado)
**y sv4** (textos del modal y del candado, recuento del resultado). Sin esquema, sin colas
nuevas; el JSON del resultado cambia una clave (`borradas` → `anuladas`, DA7). Rigor
**crítico** (escribe en Sigrid de producción).

**Regla del humano (literal)**: «no se debe borrar en sigrid, así que solo editará líneas,
por lo que si una hora extra se queda a cero no se borrará sino se pondrá a cero.»
Aprobado abrir esta feature el 2026-10-20 («Ok a las 2»), **justo detrás de F-034**.

**Depende de F-034** (`feature/F-034-escribir-solo-en-partes-abiertos`, en implementación):
se implementa sobre `dev` con F-034 fusionada. Reutiliza su guarda de parte abierto, su R4
(la línea de un pisado solo entra si sus pisadas ya no tienen horas), su relectura tras
escribir y su módulo `parte_abierto.py`. Si F-034 se fusiona con otra forma, el implementer
para y se revisa esta spec (`blocked`).

## Contexto (lo que hay en `dev` 4bda57e; detalle en `design.md` §1)

Al registrar con un conflicto confirmado («pisar»), sv5 manda `stmt_borrar_linea` =
`DELETE FROM hmores WHERE ide = ?` por cada línea pisada (`registro_pipeline.py` l.531–538,
`sigrid_write_client.py` l.544–547) y cuenta `borradas`. El portal dice «se borra la linea
actual» (modal), «anteriores borradas (pisadas)» (resultado) y el candado de línea registrada
aconseja «borra la linea en Sigrid». El reajuste de F-046 ya cumple la regla («R47: el
reajuste NUNCA borra en Sigrid»: `UPDATE` a `can = 0`, `tot = 0`).

## Glosario

- **Pisada**: línea de Sigrid de un conflicto confirmado (mismo recurso, día y código de hora
  que la nueva, en un parte En registro, sin la synckey de la petición).
- **Anular (poner a 0)**: `UPDATE` de la pisada a `can = 0` y `tot = 0`; nada más cambia.
- **Tener horas**: `can` no nulo y distinto de 0 (el criterio de F-034 R4).
- **Enlazada**: alguno de los `ENLACES_HMORES` de F-046 (albarán, factura, dedicación,
  nómina) distinto de 0.
- **Incidencia**: línea cuyo código de hora empieza por `CI` (semántica 4: siempre sin horas).

## Requisitos

### El pisado anula, no borra (sv5)

- **R1.** CUANDO se registra con un conflicto confirmado, sv5 debe poner a 0 cada pisada con
  `stmt_anular_linea` y no enviar ninguna sentencia `DELETE`.
- **R2.** `stmt_anular_linea` debe ser exactamente el `UPDATE` de `design.md` §4: `SET can = 0,
  tot = 0`; `WHERE` con el `ide`, el recurso, la fecha, el código de hora y el `can` leídos
  (tolerancia 0,001), sin enlaces y con la guarda de parte abierto de F-034 sobre
  `hmores.hmoide`. SI algo de eso cambió, ENTONCES afecta 0 filas.
- **R3.** El pisado no debe cambiar ninguna otra columna de la pisada: ni `synckey` (DA2), ni
  `tex` (DA3), ni partida, cuenta, código, precio, posición o enlaces.
- **R4.** Ni `sigrid_write_client.py` ni `registro_pipeline.py` deben contener `DELETE` ni
  `stmt_borrar_linea` (test sobre la fuente). `prueba_escritura_sigrid.py` queda fuera (DA9).

### Qué es un choque (sv5)

- **R5.** Para una línea a escribir que **no** es incidencia, una línea de Sigrid solo choca
  si tiene horas: una a 0 (pisada antes o anulada a mano) no genera conflicto ni la omisión
  `parte_cerrado` de F-031 R11 (DA5).
- **R6.** CUANDO la línea a escribir es una incidencia y hay en un parte En registro una
  línea ajena del mismo recurso, día y código, sv5 debe omitirla con el motivo
  `incidencia_en_sigrid` en vez de ofrecer un conflicto (DA6): anular una incidencia no
  cambia nada y pisarla la duplicaría.
- **R7.** SI alguna línea que choca en un parte En registro está enlazada, ENTONCES sv5 debe
  omitir la línea nueva con el motivo `linea_enlazada` en vez de ofrecer un conflicto (DA4).
- **R8.** El orden de las omisiones de una línea debe ser: `parte_cerrado` (F-031 R11) >
  `incidencia_en_sigrid` > `linea_enlazada` > conflicto confirmable.
- **R9.** `lineas_existentes` debe leer si cada línea está enlazada con la misma expresión de
  `ENLACES_HMORES` que `lineas_para_reajuste` (F-046).

### Lo que no entra y lo que se cuenta (sv5)

- **R10.** CUANDO una línea con pisadas no se confirma escrita (F-034 R9) y alguna de sus
  pisadas sigue con horas en un parte En registro, su motivo debe empezar por
  `pisada_no_anulada` (en vez del `no_escrita` de F-034 R11) y sv5 debe registrar un WARNING;
  si el parte está cerrado manda `parte_no_abierto` (F-034 R11).
- **R11.** Los motivos nuevos (R6, R7, R10) deben nombrar el `ide` de la línea de Sigrid y el
  código del parte, decir qué hacer, no llevar nombres ni DNIs y medir ≤ 255 caracteres
  (textos en `design.md` §6).
- **R12.** `ResultadoRegistro.anuladas` debe contar las pisadas que, releídas por `ide` tras
  escribir (F-034 R12), ya no tienen horas, y sustituir a `borradas` en el JSON de los dos
  canales (`resultado_a_dict`, DA7).
- **R13.** Por cada pisada anulada, sv5 debe registrar un INFO `[registro] pisada a 0` con
  `ide`, `hmoide`, `can` anterior, origen (`partes`, `ajena`, `manual`) y `registro_id` de la
  nueva, sin nombres, DNIs ni `tex`.
- **R14.** SI la relectura falla, ENTONCES la petición falla entera, como F-034 R14.

### Comportamiento que se conserva (caracterización)

- **R15.** CUANDO se reaprueba una línea del portal cuya synckey `partes:<id>` está en Sigrid
  a 0 por un pisado, sv5 debe devolverla `ya_registrado` sin enviar sentencias.
- **R16.** La comprobación de F-024 sobre esa línea debe dar `presente` con la diferencia
  `horas: portal X, Sigrid 0`, nunca `borrada` (`comprobacion_lineas.py` no cambia).
- **R17.** Las líneas con OTRO código del mismo día siguen siendo contexto informativo y no
  se tocan; pisar sigue viajando solo por HTTP síncrono, nunca por la cola.
- **R18.** El alta de partes, el reajuste de F-046 y la cuenta analítica no cambian; una
  pisada a 0 aporta 0 al asiento analítico (Σ `tot` por `caaide`).

### Portal (sv4)

- **R19.** El modal de conflictos debe decir que la línea actual **se pone a 0 en Sigrid (no
  se borra)** y se escribe la nueva, y pintar cada pisada como «linea N · código · X h · Y €
  → 0 h» con la nueva al lado; ningún texto del modal debe decir que se borra.
- **R20.** El resultado debe decir «N linea(s) anteriores puestas a 0 en Sigrid (pisadas)»
  con `anuladas`, y `reparto_obras` debe sumar `anuladas` en vez de `borradas`.
- **R21.** `MOTIVO_LINEA_REGISTRADA` no debe aconsejar borrar en Sigrid: texto de DA8.
- **R22.** Los comentarios y docstrings que dicen «pisar borra» (sv4 `app.py`,
  `transfer_queue_publisher.py`; sv5 `Conflicto`, docstring del pipeline) deben decir «pisar
  pone a 0».

### Documentación

- **R23.** `docs/ARCHITECTURE.md` (doble canal y semánticas 5 y 16) y
  `azure-apps/partes.md` (paso 5 de sv5 y «Qué se rompe») deben decir que pisar pone a 0, que
  ninguna sentencia de sv5 borra en Sigrid y la nota a `porcentajes` (`design.md` §10).

## Ejemplos (datos sintéticos)

1. Línea manual 9001 (8 h, `HN`, sin synckey) en `PT26/00314` En registro; el portal aprueba
   8 h `HN` del mismo recurso y día y el usuario pisa: `UPDATE` de 9001 a 0 h / 0 €, `INSERT`
   de `partes:501`; `anuladas = 1`; 9001 sigue en Sigrid con su `tex` y su cuenta.
2. Días después se aprueba `partes:502` (mismo recurso, día y `HN`): 9001 está a 0 ⇒ no hay
   conflicto con ella; solo choca `partes:501`, que tiene horas.
3. Incidencia `CIV` del portal y ya hay una `CIV` manual ese día: `omitido`
   «incidencia_en_sigrid: …», sin conflicto ni sentencias.
4. La línea que choca tiene `hdereside ≠ 0`: `omitido` «linea_enlazada: …»; nada se anula.
5. Entre la lectura y la escritura Administración cambia 9001 a 6 h: el `UPDATE` afecta 0
   filas, la nueva no entra (F-034 R4) y sale `omitido` «pisada_no_anulada: …»; reaprobar
   vuelve a enseñar el conflicto con los 6 h.
6. La pisada era `partes:480` (otra línea del portal, `registrado`): queda a 0 con su
   synckey; «Comprobar en Sigrid» la da `presente` con «horas: portal 8, Sigrid 0» y
   reaprobarla es `ya_registrado`; F-052 la clasificará `anulada_en_sigrid`.
