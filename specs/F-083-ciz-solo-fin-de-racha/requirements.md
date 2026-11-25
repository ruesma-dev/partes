<!-- specs/F-083-ciz-solo-fin-de-racha/requirements.md -->
# F-083 · Una racha de incidencia solo lleva CIZ en su último día — Requisitos

**Servicio: sv5** (`services/partes-transfer/`), si el humano acepta D1 (a). sv4 no cambia.
Sin esquema, cola, variable ni campo de contrato nuevos. Rigor **crítico**: cambia cuándo sv5
escribe en `hmores` de Sigrid de producción. Va tras `MOVER_CIZ`, que está **encendido en
producción** desde el 2026-10-25: desplegar sv5 activa F-083 (D7).

**Petición del humano (2026-11-23, literal)**: «da igual en el orden en el que vengan, si al
final hacen una racha solo debería tener fin de incidencia el de fin de racha».

**Caso real (líder, logs de sv4/sv5 y lectura de `hmores`)**: obra 0730, recurso 1811653,
vacaciones V del 18 al 20/11/2026, parte PT26/00415. A las 11:48 UTC se aprueban juntos 18, 19
y 20: 18 `inicio` (CIV, 416318), 19 `intermedio` (omitido), 20 `fin` (CIZ, 416319, synckey
`partes:25092`). Antes de las 14:38 alguien cambia a mano la 416319 de CIZ a CIV. A las 14:38 se
reaprueba el 19 (registro 25091) con el ↻ del portal. sv4 lo manda como `fin` con la racha
`[25090, 25092]`. `decidir_fin` no ve ningún CIZ posterior y devuelve `crear`, así que se
escribe un CIZ el 19 (416356, `partes:25091`), en medio de la racha. Después también se pasó a
CIV a mano.

**El hueco**: `decidir_fin` y `decidir_mismo_dia` (`racha_ciz.py`, F-060 R14 y F-062 R11) dan
el fin por posterior solo si ven un **CIZ** después de D. Una línea de la racha escrita en un
día posterior con otro código no cuenta.

## Definiciones

- **Candidatas**: las líneas que `lineas_de_racha` lee por las synckeys `partes:<i>` y
  `partes:<i>:ciz` de `racha_registro_ids` (del `fin`, o del tramo delante del `inicio`).
  Es la lectura que ya se hace hoy, sin cambios.
- **Línea de la racha**: una candidata del mismo recurso (`reside`), con `can` nulo o 0 y, en
  modo pruebas, con la marca en `tex`. Cuenta **cualquier código de hora** (D5).
- **CIZ de la racha**: una línea de la racha con código `CIZ` (`es_ciz_del_recurso`, sin cambios).
- **Posterior**: con `fecha_int` mayor que la del día D de la acción.

## sv5 · el `fin` (`decidir_fin`)

R1. DONDE `MOVER_CIZ` está encendido y el `fin` del día D trae `racha_registro_ids`, SI hay un
CIZ de la racha posterior a D, ENTONCES el sistema debe omitir la acción como `intermedio`
con el motivo de hoy (`motivo_intermedio_ciz` del CIZ de mayor (fecha, `ide`)), como F-060 R14.
(capa: unit)

R2. DONDE `MOVER_CIZ` está encendido, SI no hay ningún CIZ de la racha posterior a D pero sí
alguna línea de la racha posterior a D, ENTONCES el sistema debe omitir la acción como
`intermedio`, sin `INSERT` ni `UPDATE`, con el motivo `motivo_intermedio_racha`. El motivo
nombra la línea posterior de mayor (fecha, `ide`): su `ide`, su día y su código. (capa: unit)

R3. R2 debe decidir antes que mover, `enlazada` y `parte_cerrado`. Con una línea de la racha
posterior, el CIZ anterior no se mueve ni se mira su parte, igual que con un CIZ posterior
(F-060 R14). (capa: unit)

R4. Una línea de la racha posterior debe contar aunque esté enlazada o en un parte que no está
En registro. (capa: unit)

R5. No deben contar como posteriores para R2: una candidata de otro recurso, una con `can`
distinto de 0 (positivo o negativo), en modo pruebas una sin la marca en `tex`, y una del mismo
día D o anterior. Con solo esas candidatas, la decisión es la de hoy. (capa: unit)

R6. SI no hay ninguna línea de la racha posterior a D, ENTONCES `decidir_fin` debe dar
exactamente lo de hoy: `mover` con sus `duplicados`, `crear`, `enlazada` o `parte_cerrado`.
Es la caracterización de F-060 R15–R19. (capa: unit)

R7. La decisión de R2 debe marcarse como «fin sin CIZ posterior» (`DecisionFin.sin_ciz`
verdadero). En R1 y en toda otra decisión, falso. (capa: unit)

## sv5 · el `inicio` con `ciz_mismo_dia` (`decidir_mismo_dia`)

R8. DONDE `MOVER_CIZ` está encendido y el `inicio` del día D lleva `ciz_mismo_dia`, SI no hay
CIZ de la racha posterior a D en su tramo delante pero sí alguna línea de la racha posterior a
D, ENTONCES el sistema no debe escribir el CIZ hermano. Devuelve el motivo `posterior_sin_ciz`
(`MOTIVO_POSTERIOR_SIN_CIZ`) y el CI* se escribe igual. (capa: unit)

R9. `decidir_mismo_dia` debe seguir este orden: `ya_existe` (el hermano ya está escrito),
`posterior` (CIZ de la racha posterior), `posterior_sin_ciz` (R8) y, si no, `None` (se escribe
el hermano); con R5 aplicado a sus candidatas. (capa: unit)

## sv5 · el pipeline (`RegistroPipeline._ciz_de_racha`, paso 6 bis)

R10. CUANDO `decidir_fin` devuelve una decisión con `sin_ciz`, el sistema debe omitir la
acción con su motivo y registrar un WARNING `racha_fin_no_ciz` con el `registro_id` y el
motivo, sin nombres ni DNIs. (capa: unit)

R11. CUANDO `decidir_mismo_dia` devuelve `posterior_sin_ciz`, el sistema debe quitar el hermano
como hoy (`_sin_hermano`, INFO `ciz_mismo_dia_omitido`) y registrar además el WARNING
`racha_fin_no_ciz` con el `registro_id`, sin nombres ni DNIs. (capa: unit)

R12. F-083 no debe añadir lecturas a Sigrid: el paso 6 bis hace las mismas llamadas a
`lineas_de_racha` y a `estados_de_partes`, con los mismos argumentos que hoy. (capa: unit)

R13. Caso 0730, con `SigridFake`:
1. Se aprueban juntos d1 (`inicio`), d2 (`intermedio`) y d3 (`fin`): queda CIV en d1 y CIZ
   en d3.
2. El doble cambia el código de la línea de d3 a CIV.
3. Se reaprueba d2 como `fin`, con la racha `[id1, id3]`.

Resultado esperado:
- d2 sale `omitida` con el motivo de R2, que nombra la línea de d3 y `CIV`;
- ninguna sentencia de escritura;
- ni `partes:<id2>` ni `partes:<id2>:ciz` en el doble;
- las líneas de d1 y d3, intactas.

(capa: unit)

R14. El mismo caso sin el cambio manual (la línea de d3 sigue CIZ) debe dar el motivo de R1 y
ninguna escritura: es la regresión. (capa: unit)

R15. Caso desordenado del `inicio`, con `SigridFake`: d3 ya tiene una línea de la racha con
código CIV y no hay CIZ; se aprueba d1 como `inicio` con `ciz_mismo_dia` y tramo `[id2, id3]`.
Se escribe solo su CI*, sin `partes:<id1>:ciz` en el doble. (capa: unit)

R16. Reaprobar la misma acción de R13 dos o más veces debe dar siempre el mismo resultado,
sin escrituras. (capa: unit)

R17. En `preflight` (consultivo, F-060 R25), la acción de R13 debe salir con `accion`
`omitir` y el motivo de R2, sin escribir nada. (capa: unit)

R18. CUANDO `MOVER_CIZ` está apagado (o el settings no trae el ajuste), el sistema no debe
leer ni decidir nada nuevo: las sentencias deben ser idénticas a las de la base de la rama
(011bc2a) para los mismos casos de R13 y R15. Es la caracterización de F-060 R26. (capa: unit)

## Motivos y regla pura

R19. `motivo_intermedio_racha` debe empezar por `MOTIVO_INTERMEDIO` (el portal lo agrupa con
los demás intermedios por el texto anterior a «:»), ir sin tildes, caber en `LIMITE_MOTIVO`
(255) y no contener nombres ni DNIs. Su detalle dice que la racha sigue en Sigrid después de D
sin CIZ y que no se escribe un fin en medio. (capa: unit)

R20. `racha_ciz.py` debe seguir siendo una regla pura: sin lecturas ni escrituras. Ninguna
sentencia nueva ni modificada de `sigrid_write_client.py` contiene `DELETE`; F-083 no añade
sentencias. (capa: unit)

## Lo que no cambia (caracterización)

R21. sv4 no debe cambiar en nada: rol, `colapsar`, `racha_registro_ids`, `ciz_mismo_dia`,
`aviso_desordenada`, el ↻ de una línea `omitido` y cómo guarda la `omitida` de sv5. Su suite
debe pasar sin tocar ningún test. (capa: unit)

R22. Las dos aserciones que codificaban lo contrario se enmiendan citando «F-083 R2/R8», y
solo en el subcaso de la línea posterior de otro código (CIV o sin código):
- en `test_f060_racha_ciz.py`, `test_f060_r16_las_que_no_son_ciz_del_recurso_no_cuentan`, la
  línea posterior de otro código daba `crear`;
- en `test_f062_ciz_mismo_dia.py`, `test_f062_r11_puro_lo_que_no_es_ciz_posterior_no_cuenta`,
  daba `None`.

Los subcasos de otro recurso y de `can` ≠ 0 se conservan. (capa: unit)
