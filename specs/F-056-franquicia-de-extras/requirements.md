<!-- specs/F-056-franquicia-de-extras/requirements.md -->
# F-056 · Franquicia de extras: aviso y línea de ajuste el último laborable del mes de nómina — Requisitos

**Servicios: sv5** (lee la franquicia en Sigrid, calcula y escribe la línea de ajuste, choques) **y sv4**
(aviso en el modal de aprobar, decisión, aplicación, vista de trabajador). sv3 solo recibe la copia
byte-idéntica de `orm_models.py` (una tabla nueva). Sin colas nuevas. Rigor **crítico**.

**Petición (2026-10-22, literal)**: «hay trabjadores que tienen solo extras aa partir de un numero de
extras. de esta forma funciona normal pero al reistrar el mes nomina (ultimo dia laborable), debe salir
un aviso de si ajustar horas. de esta forma estos trabaajdores solo tienen horas extras si han hecho mas
de x. si tiene menos se añade el ultimo dia una linea de ajuste que resta el numero de extras para que
salga 0, y si es mas de x, esa linea resta x.» Regla F-053 y aprobación del 2026-10-23: `design.md` §7.

**ENMIENDA 2026-10-27 (DA1 = C, el humano, literal en dos mensajes)**: «para saber que trabajadores son
franquiciados y cual es el valor de la franquicia habra que crear un campo en sigrid que lo defina» y
«va a ir en recursos. la fecha no hace falta, se aplica en los partes que se registren si esta activo
(valor distinto de 0 o null). el campo lo rellena adminen sigrid.» ⇒ X es un campo NUEVO de `res`; caen
`empleado_franquicia` y la pantalla de `/admin/jornadas` (DA19). DA21–DA27 van con la A (`design.md` §7).

**ENMIENDA 2026-10-27 (DA28 = A, el humano: «a»)**: la vista decide «Ajustar» y «Recalcular» por una
ruta nueva y luego aplica (R45, R46). Numeración del 2026-10-23 conservada; nuevas: R1–R3 y R38–R46.

## Glosario

- **Campo** · la columna de `res` que nombra el ajuste de sv5 `FRANQUICIA_CAMPO_RES` (aún no existe).
- **X** · franquicia del recurso: el valor del campo en el momento de leerlo (DA22, DA24).
- **Periodo** · mes de nómina (16 del mes anterior → 15), etiquetado por el mes del 15, en cualquier modo.
- **Día de ajuste** · último día del periodo con jornada teórica > 0 para ese trabajador (DA6).
- **E** · Σ `hmores.can` del recurso con código `HE%` y `fec` en el periodo, de todas las obras y partes
  (cualquier estado), sin la propia línea de ajuste (DA3).
- **A** · ajuste objetivo: `−min(E, X)` si `E > 0`; si no, `0`. Dos decimales.
- **Ajuste** · la fila de `franquicia_ajuste` (una por recurso y periodo) y su línea en Sigrid.

## Franquicia en Sigrid (sv5)

- R1. El sistema debe leer X SOLO en sv5, del campo de `res` para el `res.ide` del ajuste (el recurso de
  las extras), con el valor de ese momento: sin fecha ni vigencia (DA21, DA27).
- R2. El estado de la franquicia de un recurso debe ser: NULL o 0 ⇒ `inactiva` (X = 0); número > 0 y
  ≤ 200 ⇒ `activa` (X a dos decimales); negativo, > 200 o no convertible ⇒ `invalida` (DA24).
- R3. SI `FRANQUICIA_CAMPO_RES` está vacío, ENTONCES el estado global es `apagada` y sv5 no lee el campo.
- R38. SI el nombre no es un identificador (`^[A-Za-z_][A-Za-z0-9_]{0,127}$`), la columna no está en
  `res` o no es numérica, ENTONCES el estado global es `no_disponible` con motivo y WARNING; sv5 arranca
  igual y el registro de líneas no cambia (DA23).
- R39. sv5 debe comprobar la columna con una lectura parametrizada de `INFORMATION_SCHEMA.COLUMNS` (`dbo`,
  `res`, nombre como parámetro) antes de leer valores; recuerda el «sí» mientras vive el proceso, vuelve
  a mirar el «no» en cada petición y un fallo al leer valores olvida el «sí».
- R40. sv5 debe exponer `POST /api/franquicia/recursos` (`recurso_ides`: 1–500 enteros ≥ 1; 422 si no),
  solo lectura y sin lock, que responde `estado` (`apagada` | `no_disponible` | `ok`), `motivo` y, con
  `ok`, `{franquicia, estado}` por recurso pedido (lectura en lotes).
- R41. `comprobar` y `ejecutar` deben leer X ellos mismos (`ejecutar`, dentro del lock y junto a E); la
  petición no trae X y la respuesta trae `franquicia` (X usada o null) y `franquicia_estado`.
- R42. SI la franquicia no es `activa` ni `inactiva`, ENTONCES `comprobar` y `ejecutar` responden
  `no_editable` con motivo `franquicia_…` y nada se escribe: «no se sabe» nunca es X = 0. Con
  `inactiva`, X = 0 (la línea que exista va a 0; sin línea, `sin_ajuste`).

## Periodo, día y obra (sv4, puro)

- R4. El sistema debe calcular el periodo de cada línea por su fecha real con el corte 16 → 15.
- R5. El día de ajuste debe ser el último día del periodo cuya `jornada_dia` (F-015, calendario del
  trabajador de F-003 y excepción de `empleado_jornada`) sea > 0.
- R6. SI el calendario del trabajador no es fiable para algún año del periodo, ENTONCES el aviso sale
  sin propuesta, con el motivo de Sesame, y no admite «Ajustar».
- R7. La obra del ajuste debe ser la de más horas del trabajador el día de ajuste (desempate: más extras
  del periodo y menor código); sin líneas ese día, el último día del periodo que las tenga. La partida,
  la de su línea de más horas en esa obra ese día (desempate: menor `registro_id`).
- R8. Creado el ajuste, su día, obra y partida no cambian; recalcular solo cambia `can`.

## Aviso en el modal de aprobar (sv4)

- R43. CUANDO se calcula el preflight, sv4 debe pedir a sv5 `/api/franquicia/recursos` UNA vez (su selección).
- R9. CUANDO el preflight incluye una línea de un recurso con franquicia `activa` en el día de ajuste de
  su periodo, la respuesta debe traer un bloque `franquicias` con recurso, periodo, día, obra, X, E (sv5
  `comprobar`), `extras_pendientes` (acciones `escribir` `HE*` del preflight), A estimado y si es ajustable.
- R10. CUANDO el preflight incluye una línea de un trabajador y periodo con ajuste `aplicado`, `decidido`
  o `error`, el bloque debe traerlo con su `can` en Sigrid y el A recalculado, con «Recalcular» o
  «Mantener», aunque la franquicia ya no esté `activa`.
- R11. Un ajuste `rechazado` sale solo como información; una franquicia `invalida`, con motivo y sin «Ajustar».
- R12. SI el trabajador tiene extras con más de un recurso en el periodo, su recurso no tiene `HE*` o la
  línea de ajuste está en un parte no En registro o enlazada, ENTONCES sale con motivo, sin «Ajustar»/«Recalcular».
- R44. SI sv5 responde `no_disponible`, falla o agota el tiempo en R43, ENTONCES el preflight trae un
  aviso no bloqueante («no se ha podido comprobar la franquicia: …») y ningún candidato de R9 (los de R10
  siguen); con `apagada`, ni aviso ni candidatos.
- R13. El modal debe pintar el aviso (X, E, A, obra, día, «antes → después» si existe) y no habilitar
  «Registrar» hasta que cada trabajador del bloque que pide decisión la tenga.
- R14. El bloque es consultivo: calcularlo no escribe en `partes` ni en Sigrid, y un fallo de sv5 en
  `comprobar` deja ese trabajador sin propuesta, con motivo, sin tumbar el preflight.

## Decisión y aplicación (sv4)

- R15. CUANDO `ejecutar` o `encolar` traen `franquicias: [{recurso_ide, periodo, decision}]` (`ajustar`,
  `no_ajustar`, `recalcular`, `mantener`), el sistema debe validar el formato y que cada clave sea de la
  selección (422 si no) y guardar la decisión (CAS sobre el estado leído; 409 si cambió) antes de
  registrar las líneas, que viajan como siempre; sin llamar a sv5.
- R16. `ajustar` (sin fila o desde `rechazado`) y `recalcular` (desde `aplicado`, `decidido` o `error`)
  dejan la fila `decidido` (día, obra, partida, periodo); `no_ajustar` sin fila, `rechazado`; `mantener`
  no la cambia; otra transición, 409. La respuesta lista `franquicias: [{id, estado}]`.
- R17. CUANDO se pide `POST /api/franquicia/{id}/aplicar`, el sistema debe llamar a sv5
  `/api/franquicia/ejecutar` y dejar la fila `aplicado` con E, A, X usada, `hmores_ide`, `parte_cod` y la
  respuesta, o `error` con el motivo; si la X usada difiere de la del aviso, el modal lo enseña (DA22).
- R18. SI quedan líneas del trabajador y periodo en `sigrid_estado = 'encolado'`, ENTONCES aplicar
  responde 409 «espera a que termine el registro» sin llamar a sv5.
- R19. Aplicar es seguro de repetir (sv5 es idempotente); con franquicia `inactiva` la línea va a 0 (R42).
- R20. La vista de trabajador, en modo nómina, debe mostrar el ajuste del periodo (X usada y X actual de
  sv5, E, A, día, obra, parte, estado, autor) con «Aplicar» (`decidido`/`error`, R17), «Recalcular»
  (`aplicado`) y «Ajustar» (`rechazado`, o sin fila con franquicia `activa`); estos dos, por R45 y R46.
- R45. CUANDO se pide `POST /api/franquicia/decidir` `{recurso_ide, periodo, decision}` (DA28), sv4 debe
  validar formato y decisión (solo `ajustar` o `recalcular`) y exigir líneas activas de ese recurso en el
  periodo (422 si no), calcular la propuesta y guardar con el CAS como R15 y R16 (R6–R8, R12; 409 si no
  cabe o cambió), sin llamar a sv5, y responder `{ok, ajuste}` con su `id`.
- R46. CUANDO R45 responde `ok`, la vista debe aplicar ese `id` (R17) y enseñar el resultado, sin recargar.
- R21. Quién decide (modal o R45) y quién aplica sale solo de `_actor(request)` (F-017) y queda en la
  fila; F-056 no entra en `undo_log`.

## sv5: línea de ajuste (T1–T7 hechos; con la enmienda)

- R22. sv5 debe exponer `POST /api/franquicia/comprobar` (solo lectura, sin lock) y
  `POST /api/franquicia/ejecutar` (bajo el MISMO lock que el registro), con la entrada de `design.md` §6
  validada (422 si no; `ajuste_id` 0 solo lo admite comprobar).
- R23. sv5 debe leer E con una consulta agregada; comprobar suma además `extras_pendientes` al A estimado.
- R24. CUANDO ejecutar no encuentra línea con la synckey del ajuste y A ≠ 0, debe insertar UNA línea
  `hmores` en el parte En registro de la obra y mes natural del día (el de mayor `ide`, F-031; si no hay,
  alta protegida), con el `HE*` que darían las reglas a una extra del recurso, `pre` de `reshor`,
  `tot = round(can × pre, 2)`, cuenta F-021, la partida pedida, el `tex` sin cifras `Ajuste franquicia
  extras <periodo>` (DA26) y la synckey `partes:franquicia:<id>`.
- R25. CUANDO la línea existe y su `can` difiere de A, ejecutar debe hacer `UPDATE` de `can` y
  `tot = ROUND(can × pre, 2)` con `stmt_actualizar_linea` sin cambios (`WHERE` optimista, guarda F-034,
  sin enlaces); A = 0 deja `can = 0` y `tot = 0`; el `tex` no se toca.
- R26. Ninguna sentencia de F-056 sobre Sigrid es un `DELETE`, y F-056 no escribe en `res`.
- R27. SI la línea está en un parte no En registro o enlazada, ENTONCES ejecutar no escribe y responde
  `ok: false` con `parte_no_abierto: …` o `linea_enlazada: …`.
- R28. CUANDO la línea ya vale A, `ya_aplicado` sin escribir; sin línea y con A = 0, `sin_ajuste`.
- R29. Tras escribir, sv5 relee por synckey y responde por lo releído (`ok: true` solo si la línea está
  en el parte elegido con `can` = A); si no, `ok: false` con motivo.
- R30. SI el recurso no pasa la verificación de F-023 o las reglas no le dan `HE*`, ENTONCES comprobar y
  ejecutar responden `no_editable` con ese motivo, sin escribir.
- R31. La línea de ajuste no es conflicto ni `parte_cerrado` para otra línea ni se ofrece para pisar:
  `pisado.choques` y `ReajustePipeline._choques` ignoran `partes:franquicia:*`.
- R32. En modo pruebas (`OBRA_PRUEBAS_FORZAR`), la obra es la de pruebas y `tex` es la marca.
- R33. Los logs de F-056 llevan ids, horas, estado y usuario; nunca nombres ni DNIs.

## Esquema, documentación y cierre

- R34. `franquicia_ajuste` existe en las dos copias de `orm_models.py` (byte-idénticas), toda `NOT NULL`
  con `server_default`; los guardianes de la raíz pasan a ocho tablas con sus columnas literales;
  `ddl_complementario()` la cubre. `empleado_franquicia` no existe.
- R35. Describen F-056: `docs/ARCHITECTURE.md` (semántica 7 y una 21 nueva), `partes-proyecto.md` §5 y
  `azure-apps/partes.md` (§3.5, §4, «qué se rompe»: el campo de `res` y `FRANQUICIA_CAMPO_RES`).
- R36. Lo que sv4 manda a sv5 lo aceptan `FranquiciaIn` y `FranquiciaRecursosIn` (contrato en la raíz).
- R37. Rigor crítico: fase RED, cobertura de líneas cambiadas ≥ 80 %, mutación completa sin
  supervivientes sin justificar, y `bash harness/init.sh` en verde con APPROVED del reviewer.
