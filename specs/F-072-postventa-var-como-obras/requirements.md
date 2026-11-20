# F-072 · Postventa y obras varias (VAR) como obras, con los criterios de porcentajes — Requisitos

**Servicios**: sv2 (marca en la lectura), sv3 (casado de la entrada), sv4 (catálogo, portal y
claves), sv5 (guarda y conflictos). sv1 no cambia. **Sin cambio de esquema** (DA5).
**Rigor crítico**: decide en qué obra y partida de Sigrid escribe sv5 (design §0).
**Origen**: petición del humano del 2026-11-13 (`harness/features.json`, F-072). Reglas de
referencia: repo `porcentajes`, `docs/ARCHITECTURE.md#regla-p5` y `#regla-var` (F-002, F-025,
F-039), leídas en `5381243`.

**Vocabulario.** **Obra agrupada**: obra de Sigrid de código normalizado `POSTVENTA_OBRA_COD` o
`VAR_OBRA_COD`, en cualquier empresa. **Entrada**: obra agrupada + una de sus partidas, la «obra»
que se trata como tal (`Postv-<partida>`, `VAR-<partida>`). **Marca de entrada**:
`partida_match_method` `postventa` o `var`. **Normalizar**: mayúsculas, sin acentos, espacios
ni guiones (`normalize_code` de porcentajes).

## A. Configuración

R1. sv2, sv3, sv4 y sv5 deben leer del entorno `POSTVENTA_OBRA_COD`, `POSTVENTA_ALIAS` (lista
separada por comas), `VAR_OBRA_COD` y `VAR_PARTIDA_DESDE`. Los tres primeros no tienen valor en el
código: vacío significa postventa o VAR desactivados (DA11). (capa: unit)
R2. SI VAR está activo y `VAR_PARTIDA_DESDE` falta o no es un entero ≥ 0, ENTONCES el servicio
debe negarse a arrancar con un error que nombre la variable. (capa: unit)
R3. MIENTRAS postventa y VAR estén desactivados, los cuatro servicios deben comportarse
exactamente como antes de F-072: la suite actual en verde sin tocar sus tests. (capa: unit)

## B. Reglas puras (`obras_agrupadas.py`, gemelo en sv3, sv4 y sv5)

R4. `casar_postventa(hojas, codigo_obra)` debe devolver la hoja activa cuyo código normalizado es
**igual entero** al de la obra (`0656` y `656` no casan). (capa: unit)
R5. Sin coincidencia exacta, debe devolver la hoja cuyo código normalizado es el de la obra
seguido **solo de letras** (`0578` → `0578B`, `0654` → `0654-B`), la más corta y, a igualdad,
la menor. Nada más: ni prefijo seguido de otra cosa (`CP` → `CP.1`), ni descripción, ni nombre.
(capa: unit)
R6. Solo cuentan las hojas activas (nunca un capítulo ni una partida de baja), y el resultado no
depende del orden de las filas. Con varias exactas gana la de menor `ide`. (capa: unit)
R7. `es_partida_var(hoja, desde)` debe aceptar una hoja activa si su número inicial (los dígitos
con que empieza el código, sin espacios) es ≥ `desde`. Con 29: `29`, `30`, `100`, `029`, `29.1`
y `29A` entran; `28`, `05`, `CI.1.1`, un capítulo y una partida de baja, no. (capa: unit)
R8. `casar_var(partidas_var, leido)` debe devolver la partida de código normalizado igual al
leído. Si no hay, la única con el mismo número inicial salvo los ceros a la izquierda (`29` →
`029`). Con varias o ninguna, `None`. (capa: unit)
R9. `leer_forma(leido, postventa, var)` debe reconocer al principio un código o alias (gana el
más largo), separado del resto por espacio, guion, barra o dos puntos (sin separador solo si el
resto empieza por dígito), y también al final con separador. Devuelve el tipo y el resto, el
resto vacío si solo está la marca, o `None` si no hay marca. Ejemplos: `VAR-29`, `var 29`,
`VAR29`, `POSTVENTA 578`, `578 POSTVENTA`, `POSTV2` (base), `VARIOS 3` (`None`). (capa: unit)
R10. Una tabla de casos copiada de los tests de F-025 y F-039 de porcentajes debe dar en partes
el mismo resultado. Con el repo `porcentajes` al lado, esa misma tabla, pasada por sus funciones
`resolver_postventa` y `es_partida_var` en un subproceso, debe dar lo mismo. Sin el repo, el test
se salta con motivo; con el repo, un fallo de importación es rojo. (capa: integración)
R11. El módulo debe ser byte-idéntico en sv3, sv4 y sv5, y un test de la raíz lo vigila (DA4).
(capa: unit)

## C. sv2 · lectura

R12. El prompt `parte_trabajo_es` debe pedir que, si junto al «Nº OBRA» hay una marca de
postventa o VAR, `obra_numero` la copie entera con su separador (`VAR-29`, `POSTVENTA 578`).
(capa: unit)
R13. CUANDO la obra leída lleva una marca (R9 aplicado a la clave: empieza o acaba por un código
o alias configurado y tiene algo más), sv2 no debe consultar su existencia (resultado «no se
sabe») y no debe releer por `obra_inexistente` (DA3). (capa: unit)

## D. sv3 · ingesta

R14. CUANDO la obra leída tiene forma VAR con resto, sv3 debe elegir la obra VAR entre las de
código `VAR_OBRA_COD` con las reglas de obra de F-023 (membrete y trabajadores) y casar el resto
contra sus partidas VAR (R7, R8). Si casa: obra del parte = la VAR, `obra_match_method='var'`, y
todas sus líneas llevan esa partida con `partida_match_method='var'` y puntuación 1.0. (capa: unit)
R15. CUANDO la forma es postventa con resto, sv3 debe casar el resto como obra X con el casado de
obra de siempre (ceros a la izquierda, F-023), buscar la obra `POSTVENTA_OBRA_COD` de la empresa
de X y casar el código de Sigrid de X con R4-R6. Si casa: obra = la de postventa,
`obra_match_method='postventa'`, y todas las líneas llevan esa partida con
`partida_match_method='postventa'`. (capa: unit)
R16. CUANDO la forma es base (solo la marca), sv3 debe tratar cada partida leída distinta y no
vacía de las líneas como resto (R14, R15). Si todas dan la misma entrada, se queda esa; si no,
se aplica R17. (capa: unit)
R17. SI no hay entrada, ENTONCES el parte debe quedar sin obra (`obra_ide` nulo), con
`obra_match_method` igual a uno de estos motivos (≤ 24 caracteres): `postventa_obra_no_casa`,
`postventa_sin_partida`, `agrupada_sin_obra`, `var_fuera_universo`, `agrupada_sin_entrada`,
`agrupada_varias_entradas`. Va a revisión como F-054. Nunca se elige al azar ni se cae al casado
normal. Los casos: X no casa o es agrupada; no hay obra agrupada en la empresa o hay varias; el
resto no casa; ninguna entrada; varias entradas. (capa: unit)
R18. SI el casado normal de la obra leída diera una obra agrupada, ENTONCES sv3 debe tratarla como
forma base (R16): una obra agrupada solo llega a un parte con su entrada. (capa: unit)
R19. SI la lectura del presupuesto de una obra agrupada falla o viene `truncated`, ENTONCES sv3
no debe persistir el parte y el mensaje debe seguir en la cola para reintentarse. (capa: unit)
R20. La conciliación de partidas no debe tocar las líneas con marca de entrada, igual que con las
`manual`. A las líneas sin marca de una obra agrupada debe dejarlas en blanco (`sin`), sin casado
por categoría ni por partida leída. (capa: unit)
R21. Las líneas que crea sv3 (`extra_auto` y reparto) deben clonar la partida y la marca de su
línea base. (capa: unit)
R22. Las líneas de una entrada deben contar en la jornada del día, las extras y la franquicia
como las de cualquier obra. La unidad del reparto F-045 es la obra de Sigrid. (capa: unit)

## E. sv4 · portal

R23. La clave de obra de una línea con marca de entrada debe ser `agr-<obra_ide>-<partida_ide>`;
las demás no cambian. La de un documento es la clave común de sus líneas activas; si tiene
varias, «borrar obra» no lo mueve y deja un WARNING. (capa: unit)
R24. La lista y el detalle de obras deben rotular cada entrada como `Postv-<partida_cod>` o
`<VAR_OBRA_COD>-<partida_cod>`, seguido de la descripción de la partida. (capa: integración)
R25. El catálogo de entradas debe construirse por empresa. Si la empresa tiene una sola obra VAR,
entran sus partidas VAR. Si tiene una sola obra de postventa, entra cada obra no agrupada de esa
empresa que case (R4-R6), con su partida. Si hay varias o ninguna, esa empresa no aporta
entradas. Caché con el TTL del catálogo de obras; un fallo de lectura deja el catálogo vacío con
WARNING. (capa: unit)
R26. `/api/sigrid/obras` debe devolver las obras normales, sin las agrupadas (DA7), y las
entradas con `codigo` de entrada, `nombre`, `empresa`, `agrupada` y `partida_ide`.
(capa: integración)
R27. CUANDO se cambia la obra de un parte a una entrada (`PATCH /api/partes/{id}/obra` con
`partida_ide`), sv4 debe comprobar que la entrada está en el catálogo. Pone la obra agrupada al
parte y a sus líneas, y a las líneas no congeladas la partida con su marca. Si la entrada no está
en el catálogo, 422 sin cambios. (capa: integración)
R28. SI se pide una obra agrupada sin entrada, en el cambio de obra o en `/api/partes/nuevo`,
ENTONCES sv4 debe responder 422 sin cambios. (capa: integración)
R29. CUANDO un parte pasa de una entrada a una obra normal, sus partidas deben quedar en blanco
(`sin`), sin recasado por código. (capa: integración)
R30. Un alta manual con entrada debe reutilizar o crear el documento activo del mismo día, la
misma obra y la misma entrada, con la partida y la marca en sus líneas. (capa: integración)
R31. Toda línea que sv4 crea en una entrada (extra del popup, alta en celda) debe copiar la
partida y la marca de su base. (capa: integración)
R32. SI se pide cambiar la partida de una línea con marca de entrada, ENTONCES sv4 debe responder
409 con «partida fija: cambia la entrada del parte». (capa: integración)
R33. Aprobar una entrada debe mandar a sv5 una petición con la obra agrupada y sus líneas, cada
una con `partida_ide` y `partida_metodo`. (capa: integración)
R34. Sincronizar (F-052) una vista `agr-` debe responder «no sincronizable» con su motivo, sin
llamar a sv5 (DA12). (capa: unit)
R35. El selector de obra (cambio de obra y parte nuevo) debe ofrecer las entradas y mandar su
`partida_ide`: `node --check` en verde y manual M2. (capa: unit)

## F. sv5 · registro

R36. CUANDO la obra pedida es una obra agrupada, sv5 debe leer su presupuesto una sola vez por
petición y omitir, antes de escribir, toda línea sin `partida_metodo` de entrada, sin partida,
con una partida que no es hoja activa de esa obra o, en VAR, fuera del universo VAR. El motivo
empieza por `partida_agrupada:`, nombra la partida por su código, va sin tildes y tiene
≤ 255 caracteres. En modo pruebas se aplica igual, por la obra pedida. (capa: unit)
R37. SI esa lectura falla o viene `truncated`, ENTONCES la petición debe fallar entera sin
escribir nada. (capa: unit)
R38. En una obra agrupada, una línea de Sigrid solo debe chocar (conflicto, `parte_cerrado` y
R11 de F-031) si además tiene la misma partida (DA8). En las demás obras, como hoy.
(capa: unit)
R39. La lectura nueva de sv5 debe estar en la lista de lectores de F-038 y pedir `SIGRID_API_MAX_ROWS`. (capa: unit)

## G. Documentación

R40. `docs/ARCHITECTURE.md` debe ganar la semántica 24 «Obras agrupadas (F-072)», y la lista
cerrada de `CLAUDE.md` el gemelo `obras_agrupadas.py` (DA4). Un test comprueba las dos.
`azure-apps/partes.md` (variables, bandeja y aviso a `porcentajes`) va en un commit aparte.
(capa: unit)
