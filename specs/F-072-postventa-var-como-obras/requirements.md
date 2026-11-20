# F-072 · Postventa y obras varias (VAR) como obras, con los criterios de porcentajes — Requisitos

**Servicios**: sv2 (marca en la lectura), sv3 (casado de la entrada), sv4 (catálogo, portal y
claves), sv5 (guarda y conflictos). sv1 no cambia. **Sin cambio de esquema** (DA5). **Rigor
crítico** (design, cabecera). **Origen**: petición del humano del 2026-11-13 (F-072 en
`harness/features.json`) y enmienda del 2026-11-20 («V y número, POST y número, y variantes»,
§H). Referencia: `porcentajes/docs/ARCHITECTURE.md#regla-p5` y `#regla-var` (F-002, F-025,
F-039), leídos en `5381243`.

**Vocabulario.** **Obra agrupada**: de código normalizado `POSTVENTA_OBRA_COD` o `VAR_OBRA_COD`,
en cualquier empresa. **Entrada**: obra agrupada + una partida (`Postv-<p>`, `VAR-<p>`). **Marca
de entrada**: `partida_match_method` `postventa`/`var`. **Marca del papel**: código o alias (§H).
**Normalizar**: mayúsculas, sin acentos, espacios ni guiones.

## A. Configuración

R1. sv2, sv3, sv4 y sv5 deben leer del entorno `POSTVENTA_OBRA_COD`, `POSTVENTA_ALIAS`,
`VAR_OBRA_COD`, `VAR_ALIAS` (los alias, listas separadas por comas) y `VAR_PARTIDA_DESDE`, sin
valores en el código. Vacío = postventa o VAR desactivados (DA11). (capa: unit)
R2. SI VAR está activo y `VAR_PARTIDA_DESDE` falta o no es un entero ≥ 0, ENTONCES el servicio no
debe arrancar y el error debe nombrar la variable. (capa: unit)
R3. MIENTRAS postventa y VAR estén desactivados, los cuatro servicios deben comportarse como antes
de F-072: la suite actual en verde sin tocar sus tests. (capa: unit)

## B. Reglas puras (`obras_agrupadas.py`, gemelo en sv2, sv3, sv4 y sv5)

R4. `casar_postventa(hojas, codigo_obra)` debe devolver la hoja activa cuyo código normalizado es
**igual entero** al de la obra (`0656` y `656` no casan). (capa: unit)
R5. Sin exacta, debe devolver la hoja cuyo código es el de la obra seguido **solo de letras**
(`0578` → `0578B`, `0654` → `0654-B`), la más corta y, a igualdad, la menor. Nada más: ni prefijo
seguido de otra cosa (`CP` → `CP.1`), ni descripción, ni nombre. (capa: unit)
R6. Solo deben contar las hojas activas, nunca un capítulo ni una de baja. El resultado no debe
depender del orden de las filas, y con varias exactas gana la de menor `ide`. (capa: unit)
R7. `es_partida_var(hoja, desde)` debe aceptar una hoja activa con número inicial ≥ `desde`. Con
29: entran `29`, `30`, `100`, `029`, `29.1` y `29A`; no entran `28`, `05`, `CI.1.1`, un
capítulo ni una de baja. (capa: unit)
R8. `casar_var(partidas_var, leido)` debe devolver la de código normalizado igual al leído. Si no
la hay, la única con el mismo número inicial sin contar los ceros a la izquierda (`29` →
`029`). Con varias o ninguna, `None`. (capa: unit)
R9. `leer_forma(leido, marcas)` debe aplicar las variantes de R41. Devuelve el tipo y el resto
(vacío si solo está la marca, la forma base) o `None` si no hay marca. (capa: unit)
R10. La tabla de casos de los tests de F-025 y F-039 de porcentajes debe dar lo mismo en partes.
Con el repo `porcentajes` al lado, la misma tabla pasada por su `resolver_postventa` y su
`es_partida_var` (en un subproceso) también. Sin el repo, el test se salta; con él, un fallo de
importación es rojo. (capa: integración)
R11. El módulo debe ser byte-idéntico en sv2, sv3, sv4 y sv5, y un test de la raíz debe
vigilarlo (DA4). (capa: unit)

## C. sv2 · lectura

R12. El prompt `parte_trabajo_es` debe pedir que `obra_numero` copie el «Nº OBRA» **tal cual**,
con la marca, su posición y su separador (`V-29`, `post 578`). La IA no debe normalizar: ni
expandir `V` a `VAR` o `POST` a `POSTVENTA`, ni quitar separadores, ni añadir ceros. (capa: unit)
R13. CUANDO `leer_forma` reconoce una marca en la obra leída, sv2 no debe consultar su
existencia («no se sabe») ni releer por `obra_inexistente` (DA3). (capa: unit)

## D. sv3 · ingesta

R14. CUANDO la forma es VAR con resto, sv3 debe elegir la obra VAR entre las de código
`VAR_OBRA_COD` con las reglas de F-023 (membrete y trabajadores) y casar el resto con R7 y R8.
Si casa: la obra del parte es la VAR, `obra_match_method='var'`, y cada línea lleva esa partida
con `partida_match_method='var'` y puntuación 1.0. (capa: unit)
R15. CUANDO la forma es postventa con resto, sv3 debe casar el resto como obra X con el casado de
siempre (ceros a la izquierda, F-023), tomar la obra `POSTVENTA_OBRA_COD` de la empresa de X y
casar el código de Sigrid de X con R4-R6. Si casa: la obra es la de postventa, con método
`postventa` en la obra y en cada línea. (capa: unit)
R16. CUANDO la forma es base, sv3 debe tratar como resto cada partida leída distinta y no vacía
de las líneas (R14, R15). Si todas dan la misma entrada, se queda esa; si no, R17. (capa: unit)
R17. SI no hay entrada, ENTONCES el parte debe quedar sin obra (`obra_ide` nulo) y a revisión
(F-054), con `obra_match_method` igual a uno de estos motivos (≤ 24 caracteres):
`postventa_obra_no_casa` (X no casa o es agrupada), `agrupada_sin_obra` (en la empresa no hay
obra agrupada, o hay varias), `postventa_sin_partida`, `var_fuera_universo`,
`agrupada_sin_entrada` o `agrupada_varias_entradas`. Nunca se elige al azar ni se cae al casado
normal. (capa: unit)
R18. SI el casado normal diera una obra agrupada, ENTONCES sv3 debe tratarla como forma base:
una obra agrupada solo llega a un parte con su entrada. (capa: unit)
R19. SI falla, o viene `truncated`, la lectura del presupuesto de una obra agrupada, ENTONCES sv3
no debe persistir el parte, y el mensaje debe seguir en la cola para reintentarse. (capa: unit)
R20. La conciliación de partidas no debe tocar las líneas con marca de entrada (como las
`manual`). Las líneas sin marca de una obra agrupada deben quedar en `sin`, sin casado por
categoría ni por partida leída. (capa: unit)
R21. Las líneas que sv3 crea (`extra_auto`, reparto) deben clonar partida y marca de su base. (capa: unit)
R22. Las líneas de una entrada deben contar en la jornada del día, las extras y la franquicia
como las de cualquier obra; la unidad del reparto F-045 es la obra de Sigrid. (capa: unit)

## E. sv4 · portal

R23. La clave de una línea con marca de entrada debe ser `agr-<obra_ide>-<partida_ide>`, y las
demás no cambian. La de un documento es la clave común de sus líneas activas; si tiene varias,
«borrar obra» no lo mueve y deja un WARNING. (capa: unit)
R24. La lista y el detalle deben rotular cada entrada `Postv-<partida_cod>` o
`<VAR_OBRA_COD>-<partida_cod>`, con la descripción de la partida. (capa: integración)
R25. El catálogo de entradas, por empresa: con una sola obra VAR, sus partidas VAR; con una sola
de postventa, cada obra no agrupada de la empresa que case (R4-R6); con varias o ninguna, nada.
TTL del catálogo de obras; un fallo de lectura lo deja vacío con WARNING. (capa: unit)
R26. `/api/sigrid/obras` debe devolver las obras normales, sin las agrupadas (DA7), y las
entradas con `codigo`, `nombre`, `empresa`, `agrupada` y `partida_ide`. (capa: integración)
R27. CUANDO se cambia la obra a una entrada (`PATCH /api/partes/{id}/obra` con `partida_ide`),
sv4 debe comprobar que la entrada está en el catálogo y poner la obra agrupada al parte y a sus
líneas, y la partida con su marca a las no congeladas. Si la entrada no está, 422 sin cambios.
(capa: integración)
R28. SI se pide una obra agrupada sin entrada (cambio de obra o `/api/partes/nuevo`), ENTONCES
sv4 debe responder 422 sin cambios. (capa: integración)
R29. CUANDO un parte pasa de una entrada a una obra normal, sus partidas quedan en `sin`. (capa: integración)
R30. Un alta manual con entrada debe reutilizar o crear el documento activo del mismo día, la
misma obra y la misma entrada, con la partida y la marca en las líneas. (capa: integración)
R31. Toda línea que sv4 crea en una entrada (la extra del popup, el alta en celda) debe copiar
la partida y la marca de su base. (capa: integración)
R32. SI se cambia la partida de una línea con marca de entrada, ENTONCES 409 «partida fija: cambia la entrada del parte». (capa: integración)
R33. Aprobar una entrada debe mandar a sv5 una petición con la obra agrupada, y en cada línea
`partida_ide` y `partida_metodo`. (capa: integración)
R34. Sincronizar (F-052) una vista `agr-` debe dar «no sincronizable» con motivo, sin llamar a
sv5 (DA12). (capa: unit)
R35. El selector de obra (cambio de obra y parte nuevo) debe ofrecer las entradas y mandar
`partida_ide`; se comprueba con `node --check` y M2. (capa: unit)

## F. sv5 · registro

R36. CUANDO la obra pedida es agrupada, sv5 debe leer su presupuesto una vez por petición y omitir,
antes de escribir, la línea sin `partida_metodo` de entrada, sin partida, con partida que no es
hoja activa de esa obra o, en VAR, fuera del universo VAR: motivo `partida_agrupada: …` con la
partida por su código, sin tildes, ≤ 255. En modo pruebas igual, por la obra pedida. (capa: unit)
R37. SI esa lectura falla o viene `truncated`, ENTONCES la petición falla entera sin escribir. (capa: unit)
R38. En una obra agrupada, una línea de Sigrid solo debe chocar (conflicto, `parte_cerrado`, R11
de F-031) si además tiene la misma partida (DA8); en las demás obras, como hoy. (capa: unit)
R39. La lectura nueva de sv5 debe estar en la lista de F-038 y pedir `SIGRID_API_MAX_ROWS`. (capa: unit)

## G. Documentación

R40. Un test debe comprobar dos cosas: `docs/ARCHITECTURE.md` gana la semántica 24 «Obras
agrupadas (F-072)», y la lista cerrada de `CLAUDE.md`, el gemelo (DA4). `azure-apps/partes.md`
va en un commit aparte. (capa: unit)

## H. Variantes de la marca del papel (enmienda del humano, 2026-11-20)

R41. `leer_forma` debe reconocer como marca el código o un alias configurado (propuesta DA2:
`POSTVENTA,POSTV,POST` y `V`), de forma cerrada y determinista: sin distinguir mayúsculas ni
tildes; delante o detrás del resto; separador ninguno, espacios, guion, punto o barra; gana la
marca más larga; sin separador, el resto empieza por dígito; un alias de una letra solo vale con
resto que empiece por dígito, nunca solo. Valen `V29`, `v-29`, `V.29`, `V/29`, `29 V`, `VAR 29`,
`POST578`, `post-578`, `578/POST`, `Postventá 578`, `POSTV2` (base); no `V`, `VALENCIA 3`,
`POSTE`. (capa: unit)
R42. SI la clave de lo leído (sin tildes ni separadores) es la de un código de obra real que no
es marca, ENTONCES debe ganar esa obra por el casado normal, con un WARNING `marca_colisiona`
(caso real: `150702-V`). SI es exactamente una marca, ENTONCES es forma base aunque exista una
obra con ese código: la antigua `POSTV` (DA13). (capa: unit)
R43. La marca solo debe buscarse en `cabecera.obra_numero`. La incidencia `V` (vacaciones), o
cualquier otra letra de las filas de personal, nunca debe intervenir en el casado de la obra.
(capa: unit)
