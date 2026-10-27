<!-- specs/F-062-ciz-el-mismo-dia-del-inicio/requirements.md -->
# F-062 · El inicio de una incidencia escribe CI* y CIZ el mismo día — Requisitos

**Servicios: sv5** (escribe el CIZ del inicio y lo encuentra para moverlo) **y sv4** (marca qué
`inicio` lleva CIZ y manda los días de la racha hacia delante). Sin esquema ni colas nuevas; el
payload gana `ciz_mismo_dia`. Rigor **crítico** (cambia lo que se escribe en Sigrid de
producción). Depende de F-060, con `MOVER_CIZ` **encendido en producción** desde el 2026-10-25
(sv5 12:08:43Z, sv4 12:09:28Z; `dev` 463869d): F-062 se activa al desplegarse (`design.md` §4).

**Aprobación del humano (2026-10-25, literal)**: «f62 ok a todo» ⇒ DA1–DA11 = A.

**Petición del humano (2026-10-25, literal)**: «da3 y da6 revisa en sigrid como esta ahaora.» y,
tras la propuesta del líder, «da de alta f62 la primera, y lanza spec». Regla de Sigrid: «no se
debe borrar en sigrid, así que solo editará líneas, por lo que si una hora extra se queda a cero
no se borrará sino se pondrá a cero.»

**Lectura del líder (2026-10-25, solo lectura, `ruesma`, líneas NO escritas por partes desde
2025-01-01)**: de los inicios CI* de Administración, **306 llevan CI* y CIZ el MISMO día** (CIV
184, CIP 99, CIF 13, CIE 7, CIA 2, CIH 1) frente a 34 sin CIZ (casi todos rachas aún abiertas):
DA6 de F-060 («un día suelto deja solo su CI*») no es su práctica. DA3 sí lo es (816 rachas con
el CIZ en el mismo parte, 224 en el del mes siguiente, 65 en el de otra obra; 12 cortes a fin de
mes). Propuesta aceptada: el `inicio` escribe su CI* y un CIZ (`can` 0) el mismo día; si la
racha sigue, ese CIZ se mueve con la mecánica de F-060 (`UPDATE`, nunca `DELETE`).

**Pares CI* + CIZ manuales del mismo recurso y día desde 2025 (líder, solo lectura)**: 315; 305
en el mismo parte; 304 con el CIZ grabado después (`ide` mayor), 213 con `ide` consecutivo; 303
con `pos` del CIZ mayor, solo 3 con `pos` + 1 (distancias más frecuentes: 64 (168), 21 (32), 32
(31), 12 (11), 16 (11)). Administración graba el CI* y enseguida su CIZ en el mismo parte; la
`pos` la pone la pantalla de Sigrid: sv5 no la imita, solo deja el CIZ detrás (R13).

## Contexto (dev f313407; detalle en `design.md` §1)

Con `MOVER_CIZ` encendido, un día suelto queda solo con su CI* y la racha queda «abierta» en
Sigrid hasta que llega su segundo día; con F-062, ninguna racha nueva queda sin CIZ.

## Glosario

- **Inicio, fin, ventana, racha, clave, persona, línea activa**: los de F-060 (`requirements.md`).
- **CIZ hermano del inicio X**: la línea CIZ que sv5 escribe el día de X con synckey
  `partes:<X>:ciz` (DA3). Al moverse pasa a la synckey del día nuevo (`partes:<D>`, F-060 R20).
- **Tramo delante de X** (día D, clave K): días desde D + 1 que son de incidencia K, hasta el
  primer día con líneas que no lo es, como mucho `hasta_delante(D)` (último del mes siguiente).
- **CIZ de la racha (ampliado)**: línea CIZ del recurso, `can` nulo o 0, cuya synckey es
  `partes:<i>` o `partes:<i>:ciz` de alguna línea i de la racha.

## Requisitos

### sv4 · qué `inicio` lleva CIZ (R1–R3: DONDE `MOVER_CIZ` de sv4 está encendido)

R1. CUANDO una incidencia que viaja queda con rol final `inicio` (tras `colapsar`), sv4 debe
enviarla con `ciz_mismo_dia` = verdadero y `racha_registro_ids` = los ids de las incidencias
activas de esa persona y clave del tramo delante de D, más las de la papelera de esa clave en
`registrado` o `encolado` con fecha en (D, último día del tramo]; ordenada y sin repetidos
(vacía si el tramo está vacío).
R2. SI en la misma aprobación viaja una incidencia con rol final `fin` de la misma persona y
clave cuya `racha_registro_ids` contiene el id del `inicio`, ENTONCES ese `inicio` debe ir con
`ciz_mismo_dia` = falso (el CIZ lo escribe ese `fin`), aunque sea de otra obra (DA5).
R3. Toda otra línea debe ir con `ciz_mismo_dia` = falso; el rol y la lista de un `fin` no
cambian (R9 de F-060).
R4. DONDE `MOVER_CIZ` de sv4 está apagado, toda línea debe ir con `ciz_mismo_dia` = falso y el
resto como R26 bis de F-060 (listas vacías, rol de dev 0926857).
R5. `decidir`, `colapsar`, `aviso_desordenada`, `_rol_incidencia_anterior` y la consulta única
por persona (R12 de F-060) no deben cambiar su resultado.

### sv5 · el inicio escribe su CI* y su CIZ hermano

R6. DONDE `MOVER_CIZ` de sv5 está encendido, CUANDO una línea `inicio` con `ciz_mismo_dia`
verdadero da acción `escribir` con su CI*, la acción debe llevar además el CIZ del recurso
(`horide` y `pre` de su `reshor`, `can` 0, `tot` 0) como hermano (DA1).
R7. SI el recurso no tiene el código CIZ, ENTONCES sv5 debe escribir solo el CI* y dejar un
WARNING `sin_ciz_mismo_dia` con el `registro_id`, sin nombres ni DNIs (DA9).
R8. DONDE `MOVER_CIZ` de sv5 está apagado, o la línea no trae `ciz_mismo_dia` verdadero, sv5
debe decidir y escribir exactamente como en dev f313407 (sin hermano).
R9. La cuenta analítica del hermano debe resolverse como la de un `fin` (F-021 y F-031 para el
código CIZ del recurso, con la partida de la línea), en la misma lectura de cuentas (DA10).
R10. SI la acción del CI* acaba en `ya_registrado`, `omitir`, `dedicacion` o en un conflicto no
confirmado, ENTONCES no debe escribirse el hermano.
R11. En el paso 6 bis (bajo el lock, tras la idempotencia), sv5 debe leer, en la MISMA lectura
de racha de F-060, las synckeys `partes:<i>` y `partes:<i>:ciz` de cada id i de la lista del
`inicio` y `partes:<D>:ciz` de la propia línea. SI alguna es un CIZ del recurso (`can` nulo o
0 y, en modo pruebas, con la marca en `tex`) con fecha posterior a D, o existe
`partes:<D>:ciz`, ENTONCES no debe escribirse el hermano (DA5).
R12. SI en algún parte del periodo de D hay ya una línea del recurso, el día D y el código CIZ
que no es de la petición, ENTONCES no debe escribirse el hermano (el CI* sigue su regla).
R13. El CI* y su hermano deben escribirse con UNA sentencia `INSERT` de dos filas (`design.md`
§5): mismas columnas y valores que `stmt_insert_linea` salvo, en el hermano, `horide` y `pre`
del CIZ, su cuenta, `pos` = la del CI* + `PASO_POS`, synckey `partes:<X>:ciz`; la guarda de
parte abierto de F-034 para las dos filas y, solo en la del hermano, que no exista ya una línea
con esa synckey (DA2).
R14. Ninguna sentencia de esta feature debe ser `DELETE`.
R15. La relectura de F-034 debe leer también `partes:<X>:ciz`: si el CI* se confirma, su
entrada de `escritas` debe llevar `ciz_hmores_ide` cuando el hermano está en el mismo parte;
SI el CI* se confirma y el hermano escrito no está, ENTONCES WARNING
`ciz_mismo_dia_no_escrito` con el `registro_id`. El estado de la línea lo decide el CI*.
R16. Por cada hermano escrito u omitido por R7, R11 o R12, sv5 debe dejar un INFO con
`registro_id`, `ide`/parte/fecha o el motivo (`posterior`, `ya_existe`, `ciz_en_sigrid`), sin
nombres ni DNIs.
R17. El hermano no es una acción propia: `n_escribir`, `omitidas`, `ya_registradas`, los
conflictos y la respuesta del preflight no deben cambiar por él.

### sv5 · el siguiente día de la racha mueve el CIZ hermano

R18. DONDE `MOVER_CIZ` de sv5 está encendido, CUANDO el paso 6 bis busca el CIZ de un `fin`
(R13 de F-060), debe leer para cada id i de su lista `partes:<i>` y `partes:<i>:ciz`, en la
misma lectura, y aplicar `decidir_fin` (R14–R19 de F-060) sin cambios a ese conjunto.
R19. CUANDO lo que se mueve es un CIZ hermano, la entrada de `escritas` NO debe llevar
`movida_de` (la línea del inicio conserva su CI* y sigue `registrado`) y sí `hmores_ide`; el
INFO de R24 de F-060 debe nombrar la synckey anterior en vez del `registro_id` anterior.
R20. `synckey_ciz_de(X)` debe dar `partes:<X>:ciz`, y `registro_de_synckey` debe dar None para
una synckey de hermano.
R21. CUANDO tras el inicio llega un día trabajado o de otra clave, el CIZ hermano no debe
tocarse (sv4 no manda `fin` de esa racha).
R22. CUANDO un `fin` llega para una racha cuyo inicio se escribió sin hermano (antes de
encender, R7 o R11), sv5 debe crear el CIZ como R16 de F-060; nada es retroactivo (DA6).
R23. SI el CIZ que habría que mover (hermano o no) está en un parte que no está En registro,
ENTONCES la acción debe pasar a `omitir` con `ciz_en_parte_cerrado` (R17 de F-060, DA7).

### sv4 · el resultado

R24. sv4 no debe cambiar `marcar_registros_sigrid`: una escrita sin `movida_de` no toca otra
línea; `sigrid_hmores_ide` del inicio sigue siendo el `ide` del CI* y `ciz_hmores_ide` no se
guarda (DA3). R28–R30 de F-060 siguen igual para los CIZ que no son hermanos.

### Interacciones (DA8, DA11)

R25. No deben cambiar: R0 de F-019 (dedicación manda: sin CI* ni hermano), la comprobación de
F-024 (solo por `partes:<id>`; el hermano no se comprueba), las guardas de F-034, el reajuste de
F-046, F-053 (pisar pone a 0; enlazada ⇒ R18 de F-060), el aviso `racha_desordenada` y el
modal de aprobación, `estado_parte.py`, `cuenta_analitica.py` y `congelacion.py`.
R26. CUANDO el día del inicio se desaprueba o va a la papelera, nada debe moverse ni ponerse a 0
en Sigrid; CUANDO un inicio `borrado_sigrid` se reaprueba, el CI* se reescribe y el hermano
solo según R10–R13.

### Documentación y verificación

R27. `docs/ARCHITECTURE.md` (semántica 4), `docs/referencia/partes-proyecto.md` (§3.5 3c, §4.4,
variables), `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (paso 3c de sv5, contrato,
«Qué se rompe», variables) y los comentarios de `config/settings.py` de sv4 y sv5 deben contar
que el inicio escribe CI* y CIZ el mismo día y que el CIZ se mueve si la racha sigue.
R28. Verificaciones M0–M6 de `design.md` §9 con comando exacto en `progress/current.md`: M0 de
solo lectura; M1–M5 en modo pruebas (obra 0404, `PRUEBA-IA`, `MOVER_CIZ=true` en sv4 y sv5),
limpiando con `prueba_escritura_sigrid.py`, ANTES de desplegar sv4; M6 de solo lectura después.

## Fuera de alcance

Rellenar el CIZ de las rachas ya abiertas al encender (DA6); mover CI* o CIZ hacia atrás por
llegadas desordenadas, desaprobaciones o papelera (DA7 de F-060); comprobar el hermano en F-024;
rotular el hermano en el modal; deshacer en Sigrid lo escrito al apagar `MOVER_CIZ`.
