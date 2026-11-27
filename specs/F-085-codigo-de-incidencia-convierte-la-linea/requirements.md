# F-085 · Un código de incidencia convierte la línea, y el inicio de la racha se recoloca — Requisitos

**Servicios**: sv4 (conversión, deshacer, portal; parte B: estado del día movido), sv3 (no pisar
lo manual) y sv5 (guarda; parte B: mover el CI*). Sin esquema ni colas nuevas. **Rigor crítico**
(`design.md`, cabecera). Dos partes separables: **A** (R1–R20) y **B** (R21–R32); D1 decide si B
sale a otra feature. **Petición del humano (2026-11-27, literal)**: «el comportamiento esperado es
que pueda editar, cambio el codigo, pongo hora 0 (da igual para el codigo AT), eso actualiza tipo
y registra en sigrid mirando dia adelante y atras, en este caso tiene que poner inicio de
incidencia y quitar el inicio del dia 19». Caso de origen y estado medido: `features.json` (F-085)
y `design.md` §1.

**Revoca o matiza**: F-066 R14 (revocado: una incidencia sí cambia de clase), R13 y R17
(matizados: un CI* ya no da `normal`), R16 (deshacer restaura más campos); en parte F-060 DA7 y
su «Fuera de alcance» (parte B: el CI* se mueve hacia atrás). F-062 y F-083 no cambian (R24, R32).

## Definiciones

- **Código de incidencia**: código de hora que, sin espacios y en mayúsculas, empieza por `CI` y
  no es `CIZ`. **Código de fin**: `CIZ`. Su **letra** es la de `TablaIncidencias.por_sigrid`
  (`config/incidencias.yaml`: CIA → AT, CIV → V…).
- **Forma canónica de incidencia** (la de la ingesta y el alta a mano): `es_incidencia` verdadero,
  `tipo_hora` = `incidencia_codigo` = letra, `horas` y `horas_orig` nulos.
- **Cambio de clase**: una línea pasa de horas a incidencia, de incidencia a horas o de una letra
  a otra.

## A1. sv4 · el selector de código de hora (`PATCH /api/registros/{id}/hora`)

R1. `clase_hora.py` debe ofrecer `es_codigo_incidencia(codigo)` (True para `CIA`, ` cia `,
`CIV`, `CIQ`; False para `CIZ`, `HLOF`, `HEOF`, `CI`, None y vacío) y `es_codigo_fin(codigo)`
(True solo para `CIZ` normalizado). Ningún otro fichero de sv4 decide «es CI*» (test de fuente
sobre los ficheros que toca F-085). (capa: unit)
R2. CUANDO se guarda en una línea no congelada que no es incidencia un código de incidencia con
letra, el sistema debe dejarla en la forma canónica de esa letra, con los `hora_*` de la opción
y `hora_match_method = "manual"`; partida, recurso, fecha y obra no cambian. (capa: integración)
R3. CUANDO se guarda en una incidencia un código de incidencia de otra letra, el sistema debe
cambiar `tipo_hora` e `incidencia_codigo` a la letra nueva (revoca F-066 R14). (capa: integración)
R4. CUANDO se guarda en una incidencia un código con clase de F-066 (extra u ordinaria), el sistema
debe dejar `es_incidencia` falso, `tipo_hora` por la regla de F-066, `incidencia_codigo` y
`horas` nulos (D3). (capa: integración)
R5. SI el código elegido es `CIZ`, ENTONCES el sistema debe responder 400 «El fin de incidencia
(CIZ) lo pone el sistema al cerrar la racha: elige el código de la incidencia» sin tocar la línea
(D5). (capa: integración)
R6. SI el código es de incidencia y no tiene letra en la tabla, ENTONCES 400 «El código <cod> no
está en la tabla de incidencias del portal», sin tocar la línea (D5). (capa: integración)
R7. Sin código de incidencia ni de fin, el sistema debe guardar como F-066 R12, R13, R15 y R16
(caracterización: mismos valores que en la base de la rama). (capa: integración)
R8. Las guardas de F-066 R18 deben seguir (503, 404, 409 de congelada F-004, recálculo F-043);
con selección múltiple, cada línea según R2–R7. (capa: integración)
R9. La respuesta debe llevar `tipo_hora` (la letra, `normal` o `extra`), `es_incidencia`,
`incidencia_codigo` y `clase_cambiada` (booleano). (capa: integración)
R10. Cada guardado debe dejar una sola entrada de deshacer: `registro_hora` sin cambio de clase y
`registro_clase` con él; esta guarda además `incidencia_codigo`, `horas`, `horas_orig` y
`extra_auto`, y deshacerla deja la línea exactamente como estaba. `_REG_UNDO_FIELDS` gana
`incidencia_codigo`. (capa: integración)
R11. CUANDO hay cambio de clase, o se deshace un `registro_clase`, sv4 debe pedir UN recálculo
compartido (F-049) de `documentos_de_los_dias` del (recurso, fecha) de las líneas, con motivo
`codigo_incidencia` (o `deshacer_codigo_incidencia`); SI la cola falla, ENTONCES el cambio queda y
la respuesta trae `recalculo: fallo`. (capa: integración)
R12. Tras R11, la extra automática no congelada de la pareja de la línea convertida debe
desaparecer con la pasada de sv3 de siempre (F-037, F-069); una extra explícita o congelada se
queda y la marca F-025 del día la señala (D4). (capa: unit, en sv3)
R13. CUANDO `app.js` recibe `clase_cambiada` verdadero, debe recargar la página (insignia Tipo,
matriz, celda de horas); sin cambio de clase, como hoy. (capa: unit)
R14. Una línea convertida debe pintarse como incidencia en la columna Tipo (obra y trabajador) y en
la matriz (`inc` con su letra, sin horas), y viajar a sv5 con `es_incidencia` y su rol de racha
(F-060) como una incidencia de la ingesta. (capa: integración)

## A2. sv3 · el código de hora puesto a mano

R15. CUANDO el casado de recurso pasa por una línea con `hora_match_method = "manual"`, no debe
pisar `hora_ide`, `hora_codigo`, `hora_descripcion`, `hora_ext` ni `hora_match_method`; sí la
categoría, `hora_candef` y `recurso_precio_hora`. Si el código del recurso difiere, INFO
`hora_manual_respetada` con registro y códigos, sin nombres ni DNIs (D8). (capa: unit)
R16. Una incidencia convertida a mano (letra en `tipo_hora`, método `manual`) debe conservar su
código tras el recálculo; una incidencia sin `manual` toma el de `reshor` como hoy. (capa: unit)
R17. `fetch_registros_para_recurso` debe devolver `hora_match_method`. (capa: integración)
R18. Para toda línea sin `manual`, `_overwrite` debe dar lo mismo que en la base (caracterización
con los casos de los tests de hoy). (capa: unit)

## A3. sv5 · guarda contra un CI* en una línea de horas

R19. SI una línea que no es incidencia trae un `hora_codigo` de incidencia o de fin, o un
`hora_ide` que es un CI* del recurso, ENTONCES `reglas_registro.decidir` debe omitirla con
`MOTIVO_CODIGO_INCIDENCIA` («codigo de incidencia en una linea de horas: vuelve a elegir el codigo
en el portal»), después de las omisiones previas y antes de mensuales y de «sin horas»; nunca
escribe un HL* o HE* por ella (D6). (capa: unit)
R20. Las demás líneas deben decidirse exactamente como hoy (caracterización). (capa: unit)

## B. Recolocar el inicio de la racha (DONDE `MOVER_INICIO` está encendido; D12)

**Inicio previo** de un `inicio` del día D con código C: entre las candidatas que el paso 6 bis
lee por las synckeys `partes:<i>` de su `racha_registro_ids` (el tramo delante, F-062 R1), la
**línea de la racha** (F-083) posterior a D de menor (fecha, `ide`), si su código es C, su synckey
es `partes:<i>` (no `:ciz`) y hay un CIZ de la racha en su día o después (D9).

R21. CUANDO una acción `escribir` de rol `inicio` con código CI* trae `racha_registro_ids`, sv5
debe leer sus candidatas en la misma llamada a `lineas_de_racha` y, si hay inicio previo, moverlo
a D con UN `UPDATE` (`stmt_mover_linea`, F-060 R20–R21) en vez del `INSERT`. (capa: unit)
R22. SI el inicio previo está enlazado, ENTONCES omitir con `linea_enlazada` (F-053); SI su parte
no está En registro, ENTONCES omitir con `inicio_en_parte_cerrado` (línea, parte y estado); en
ninguno se escribe otro CI* (D10). (capa: unit)
R23. SI no hay inicio previo, ENTONCES el `inicio` debe escribirse como hoy; si hay una línea de la
racha posterior con código C que no cumple la definición, además WARNING
`racha_inicio_no_movido` con registro e `ide`, sin nombres ni DNIs. (capa: unit)
R24. El CIZ hermano debe decidirse con `decidir_mismo_dia` sobre las candidatas leídas antes de
mover, sin cambios (con inicio previo hay CIZ posterior: no hay hermano). (capa: unit)
R25. La escrita del `inicio` movido debe llevar `movida_de` y `hmores_ide` tras la relectura
(F-060 R23), y sv5 dejar un INFO `inicio_movido` (`ide`, fechas y partes antes y después,
`registro_id`), sin nombres ni DNIs. (capa: unit)
R26. El preflight debe aplicar R21–R23 de forma consultiva. (capa: unit)
R27. CUANDO `MOVER_INICIO` de sv5 está apagado (o el settings no lo trae), las lecturas y
sentencias deben ser idénticas a las de la base de la rama, también en los casos de F-083 R13 y
R15. Ninguna sentencia de F-085 es `DELETE`. (capa: unit)
R28. CUANDO sv4 aplica una escrita con `movida_de` = X y código distinto de `CIZ`, debe pasar X a
`omitido` con motivo `inicio_movido` («el inicio de la incidencia (<cod>, linea <ide>) paso al dia
<D>: este dia es intermedio»), con el CAS de F-060 R28; con `CIZ`, `fin_movido` como hoy;
aplicarlo dos veces da lo mismo (D11). (capa: integración)
R29. DONDE `MOVER_INICIO` de sv4 está encendido, sv4 no debe dar `racha_desordenada` a una
incidencia `inicio` cuyo siguiente día que cuenta es de su misma clave; con trabajo, otra clave o
el interruptor apagado, como hoy (F-060 R10). (capa: unit)
R30. Caso de origen con `SigridFake` (`design.md` §5.4): (a) con CIA el 19 y CIZ el 25, aprobar
el 18 mueve la CIA al 18 (un `UPDATE`, ningún `INSERT`, sin hermano) y la línea del 19 queda
`omitido · inicio_movido`; (b) sin la CIA del 19 (borrada), escribe la CIA del 18 con `INSERT` y
sin hermano. (capa: unit)
R31. Dos llegadas hacia atrás (19, luego 18, luego 17) deben dejar un solo CI*, el del 17, y el
CIZ donde estaba. (capa: unit)
R32. Los casos de F-083 R13–R17 y de F-062 deben dar lo mismo con el interruptor encendido (un CIV
sin CIZ detrás no es inicio previo). (capa: unit)

## Documentación y verificación

R33. `docs/ARCHITECTURE.md` (semánticas 3 y 4) debe nombrar `es_codigo_incidencia`, la conversión,
`MOTIVO_CODIGO_INCIDENCIA`, lo manual en sv3 y (parte B) `inicio_movido` y `MOVER_INICIO`; lo
vigila un test de fuente. `docs/referencia/partes-proyecto.md` y `azure-apps/partes.md` se
actualizan igual (`design.md` §9). (capa: unit)
R34. Las verificaciones M0–M5 de `design.md` §8 se hacen con su comando exacto y su resultado
real en `progress/`. (capa: MANUAL (humano))

## Fuera de alcance

Editar líneas registradas (F-081; aquí siguen congeladas), el guardado por cada paso del campo de
horas (D13), migrar las líneas con CI* que hoy no son incidencia (D7), mover el CI* hacia delante
al desaprobar o mandar a la papelera el día del inicio (F-062 DA8 sigue), el trabajo que llega
dentro de una racha registrada (F-060 R10 sigue), HENC en sv3 y sv5 (F-067).
