<!-- specs/F-056-franquicia-de-extras/requirements.md -->
# F-056 · Franquicia de extras: aviso y línea de ajuste el último laborable del mes de nómina — Requisitos

**Servicios tocados: sv5** (cálculo del ajuste contra Sigrid, alta y edición de la línea, choques)
**y sv4** (configuración por trabajador, aviso en el modal de aprobar, decisión, aplicación y
vista de trabajador). sv3 solo recibe la copia byte-idéntica de `orm_models.py` (dos tablas
nuevas; la base es una). Sin colas nuevas. Rigor **crítico** (escribe en Sigrid de producción y
toca nómina).

**Petición del humano (2026-10-22, literal)**: «hay trabjadores que tienen solo extras aa partir
de un numero de extras. de esta forma funciona normal pero al reistrar el mes nomina (ultimo dia
laborable), debe salir un aviso de si ajustar horas. de esta forma estos trabaajdores solo tienen
horas extras si han hecho mas de x. si tiene menos se añade el ultimo dia una linea de ajuste que
resta el numero de extras para que salga 0, y si es mas de x, esa linea resta x.»

**Regla del humano (F-053, literal)**: «no se debe borrar en sigrid, así que solo editará
líneas, por lo que si una hora extra se queda a cero no se borrará sino se pondrá a cero.»

**Aprobación del humano (2026-10-23, literal)**: «a a todo, actualzia backlog para que refleje lo que tien spec y estado real de todo» ⇒ DA1–DA20 = A. En espera de turno: detrás de F-060 y F-058 (máximo una feature en curso).

Las decisiones abiertas (DA1–DA20) y su recomendación están en `design.md` §7; estos
requisitos asumen la recomendación **A** de todas. Si el humano elige otra, se reescriben.

## Glosario

- **X** · franquicia: horas extra por periodo que el trabajador no cobra (DA1, DA2).
- **Periodo** · el mes de nómina de Ruesma: del 16 del mes anterior al 15, etiquetado por el mes
  del 15 (`calendar_builder.period_bounds(..., MODE_NOMINA)`), sea cual sea el modo de la vista.
- **Día de ajuste** · último día del periodo con jornada teórica > 0 para ese trabajador (DA6).
- **E** · extras del periodo en Sigrid: Σ `hmores.can` del recurso con código `HE%` y `fec` en el
  periodo, de todas las obras y partes (cualquier estado), sin la propia línea de ajuste (DA3).
- **A** · ajuste objetivo: `−min(E, X)` si `E > 0`; si no, `0`. Dos decimales.
- **Ajuste** · la fila de `franquicia_ajuste` (una por recurso y periodo) y su línea en Sigrid.

## Configuración (sv4)

- R1. El sistema debe guardar la franquicia en la tabla nueva `empleado_franquicia` (DNI
  normalizado, `horas` X, `desde` inclusivo, `hasta` exclusivo o nulo, nota, `is_active`,
  autoría), declarada igual en las dos copias de `orm_models.py`.
- R2. CUANDO un administrador guarda una franquicia en la sección «Franquicia de extras» de
  `/admin/jornadas`, el sistema debe validar antes de escribir: DNI no vacío, `0 < X ≤ 200`,
  vigencia válida y sin solape con otra fila activa del mismo DNI; SI algo falla, ENTONCES 422
  con motivo y campo, y la base intacta. Desactivar es papelera lógica (nunca se borra).
- R3. La franquicia de un periodo es la fila activa vigente el día de ajuste; sin fila vigente
  el trabajador no tiene franquicia en ese periodo.

## Periodo, día y obra (sv4, puro)

- R4. El sistema debe calcular el periodo de cada línea por su fecha real con el corte de
  nómina (16 → 15).
- R5. El día de ajuste debe ser el último día del periodo cuya `jornada_dia` (F-015, con el
  calendario del trabajador de F-003 y su excepción de `empleado_jornada`) sea > 0.
- R6. SI el calendario del trabajador no es fiable para algún año del periodo, ENTONCES el aviso
  sale sin propuesta, con el motivo de Sesame, y no admite «Ajustar».
- R7. La obra del ajuste debe ser la de más horas del trabajador el día de ajuste (desempate: más
  extras del periodo y después menor código de obra); si ese día no tiene líneas de trabajo, el
  último día del periodo que las tenga. La partida, la de su línea de más horas en esa obra ese
  día (desempate: menor `registro_id`).
- R8. Creado el ajuste, su día, obra y partida no cambian; recalcular solo cambia `can`.

## Aviso en el modal de aprobar (sv4)

- R9. CUANDO el preflight incluye una línea de un trabajador con franquicia fechada en el día de
  ajuste de su periodo, la respuesta debe traer un bloque `franquicias` con: recurso, periodo,
  día, obra, X, E (sv5), extras de esta aprobación que se escribirían (`extras_pendientes`, de
  las acciones `escribir` con código `HE*` del preflight), A estimado y si se puede ajustar.
- R10. CUANDO el preflight incluye cualquier línea de un trabajador y periodo con ajuste
  `aplicado`, `decidido` o `error`, el bloque debe traerlo con su `can` actual en Sigrid y el A
  recalculado, y ofrecer «Recalcular» o «Mantener».
- R11. Un ajuste `rechazado` sale en el bloque solo como información y no pide decisión.
- R12. SI el trabajador tiene extras con más de un recurso en el periodo, su recurso no tiene
  código `HE*`, la línea de ajuste está en un parte no En registro o enlazada, ENTONCES el bloque
  lo dice con su motivo y no admite «Ajustar» ni «Recalcular».
- R13. El modal debe pintar el aviso (X, E, A, obra, día, «antes → después» si existe) y no
  habilitar «Registrar» hasta que cada trabajador del bloque que pide decisión la tenga.
- R14. El bloque es consultivo: calcularlo no escribe nada en `partes` ni en Sigrid, y un fallo
  de sv5 al calcularlo deja ese trabajador sin propuesta, con motivo, sin tumbar el preflight.

## Decisión y aplicación (sv4)

- R15. CUANDO `ejecutar` o `encolar` traen `franquicias: [{recurso_ide, periodo, decision}]`
  (`ajustar`, `no_ajustar`, `recalcular`, `mantener`), el sistema debe validar el formato y que
  cada clave sea de un trabajador y periodo de la selección (422 si no) y guardar la decisión
  en `franquicia_ajuste` (alta o cambio de estado con comprobación del estado leído; 409 si
  cambió) antes de registrar las líneas, que viajan como siempre. Sin llamar a sv5.
- R16. `ajustar` y `recalcular` dejan la fila `decidido` (con día, obra, partida, X y periodo);
  `no_ajustar` la deja `rechazado`; `mantener` no la cambia. La respuesta lista las filas
  decididas (`franquicias: [{id, estado}]`).
- R17. CUANDO se pide `POST /api/franquicia/{id}/aplicar` (el modal al terminar el registro, o
  la vista de trabajador), el sistema debe llamar a sv5 `/api/franquicia/ejecutar` y dejar la
  fila `aplicado` con E, A, `hmores_ide`, `parte_cod` y la respuesta, o `error` con el motivo.
- R18. SI quedan líneas del trabajador y periodo en `sigrid_estado = 'encolado'`, ENTONCES
  aplicar responde 409 «espera a que termine el registro» sin llamar a sv5.
- R19. Aplicar es seguro de repetir (sv5 es idempotente) y, sin franquicia vigente, recalcula
  con X = 0 (la línea queda a 0, no se borra).
- R20. La vista de trabajador, en modo nómina, debe mostrar el ajuste del periodo (X, E, A, día,
  obra, parte, estado, autor) con «Aplicar» (`decidido`/`error`), «Recalcular» (`aplicado`) y
  «Ajustar» (`rechazado` o sin fila con franquicia vigente).
- R21. Quién decide y quién aplica sale solo de `_actor(request)` (F-017) y queda en la fila;
  F-056 no entra en `undo_log` (en Sigrid no hay deshacer).

## sv5

- R22. sv5 debe exponer `POST /api/franquicia/comprobar` (solo lectura, sin lock) y
  `POST /api/franquicia/ejecutar` (bajo el MISMO lock que el registro), con la entrada de
  `design.md` §6 validada (422 si no; `ajuste_id` 0 solo lo admite comprobar).
- R23. sv5 debe leer E con una consulta agregada a `sql/read` por petición; comprobar suma
  además `extras_pendientes` para el A estimado.
- R24. CUANDO ejecutar no encuentra línea con la synckey del ajuste y A ≠ 0, debe insertar UNA
  línea `hmores` en el parte En registro de la obra y mes natural del día (el de mayor `ide`,
  F-031; si no hay, alta protegida como el registro), con el código `HE*` que darían las reglas
  de registro para una extra del recurso, `pre` de `reshor`, `tot = round(can × pre, 2)`,
  cuenta analítica de F-021, la partida pedida, el `tex` de §6 y la synckey
  `partes:franquicia:<id>`.
- R25. CUANDO la línea existe y su `can` difiere de A, ejecutar debe hacer `UPDATE` de `can` y
  `tot = ROUND(can × pre, 2)` con `WHERE` optimista (`ide`, synckey, `can` leído), la guarda de
  parte abierto de F-034 y sin enlaces; A = 0 deja `can = 0` y `tot = 0`.
- R26. Ninguna sentencia de F-056 sobre Sigrid es un `DELETE`.
- R27. SI la línea existe en un parte que no está En registro o está enlazada (albarán,
  factura, dedicación, nómina), ENTONCES ejecutar no escribe y responde `ok: false` con
  `parte_no_abierto: …` o `linea_enlazada: …`.
- R28. CUANDO la línea ya vale A, la respuesta es `ya_aplicado` sin escribir; sin línea y con
  A = 0, `sin_ajuste` sin escribir.
- R29. Tras escribir, sv5 relee por synckey y responde según lo releído (`ok: true` solo si la
  línea está en el parte elegido con `can` = A); si no, `ok: false` con motivo.
- R30. SI el recurso no pasa la verificación de F-023 o las reglas no le dan código `HE*`,
  ENTONCES comprobar y ejecutar responden `no_editable` con ese motivo, sin escribir.
- R31. La línea de ajuste no es conflicto ni `parte_cerrado` para ninguna otra línea, ni se
  ofrece para pisar: `pisado.choques` y `ReajustePipeline._choques` ignoran las synckeys que
  empiezan por `partes:franquicia:`. El alta del ajuste no busca conflictos.
- R32. En modo pruebas (`OBRA_PRUEBAS_FORZAR`), la obra es la de pruebas y `tex` es la marca.
- R33. Los logs de F-056 llevan ids, horas y usuario; nunca nombres ni DNIs.

## Esquema, documentación y cierre

- R34. `franquicia_ajuste` y `empleado_franquicia` existen en las dos copias de `orm_models.py`
  (byte-idénticas) con toda `NOT NULL` con `server_default`; los guardianes de la raíz pasan a
  nueve tablas con sus columnas literales; `ddl_complementario()` las cubre.
- R35. `docs/ARCHITECTURE.md` (semántica 7 y una semántica 18 nueva), `docs/referencia/
  partes-proyecto.md` §5 y `azure-apps/partes.md` (§3.5, §4 y «qué se rompe») describen F-056.
- R36. Lo que sv4 manda a sv5 lo acepta `FranquiciaIn` (test de contrato en la raíz).
- R37. Rigor crítico: fase RED, cobertura de líneas cambiadas ≥ 80 %, mutación completa sin
  supervivientes sin justificar, y `bash harness/init.sh` en verde con APPROVED del reviewer.
