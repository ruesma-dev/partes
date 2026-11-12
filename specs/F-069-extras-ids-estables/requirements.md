# F-069 · sv3: extras automáticas con ids estables y recálculo en una sola transacción — Requisitos

**Servicio**: **sv3** (`services/partes-persistencia`) y, si el humano aprueba DA1, un mensaje
de **sv4** (`services/partes-front`). Sin cambios de esquema, colas ni contratos sv3↔sv4↔sv5.
Rigor **crítico**: lo que sv3 deja en `parte_registros` es lo que sv5 escribe en Sigrid.

**Origen**: pedida por el humano el 2026-11-12 como **urgente**. Obra 0697, 12/11 09:20-09:24:
el portal rechazaba aprobar con «4 línea(s) no son de esta vista». Diagnóstico con
fichero:línea, cronología y las 4 líneas en `progress/explore_aprobar_fuera_ambito_0697.md`.
Cada pasada de conciliación (`RecursoConciliador._pasada`) hace `revert_extras_auto` (BORRA las
`extra_auto` no congeladas y hace commit) y luego `apply_extras_splits` las crea con ids
nuevos en otra transacción. Dos efectos: (a) los ids de la página dejan de existir y sv4
rechaza el ámbito; (b) entre los dos commits la ordinaria se ve entera y sin su extra, y una
aprobación de una sola línea en ese momento mandaría a Sigrid todo como ordinario.

## Glosario

- **Pareja** (F-037): la base ordinaria y sus `extra_auto` con la misma `clave_pareja`
  `(document_id, line_index, empleado_line_no, fecha_int)`.
- **Vista revertida**: las filas leídas tal como quedarían tras `plan_revert`, calculada en
  memoria: sin las extras de `plan.borrar` y con `horas = horas_orig`, `horas_orig = None` en
  las de `plan.restaurar`. Nada se escribe al calcularla.
- **Escritura de la pasada**: la única transacción en la que la pasada escribe revert,
  casados de recurso y splits (`escribir_pasada`, `design.md` §2).
- **Huella** de una fila: los campos leídos que deciden su revert y su split (§3 del design).
- **Extra reutilizada**: una `extra_auto` que el plan iba a borrar y que, por volver a hacer
  falta en su pareja, se actualiza en el sitio y conserva su `id`.

## Requisitos

### Ids estables (pieza 1)

R1. CUANDO dos pasadas seguidas corren sin ningún cambio entre ellas, el sistema debe dejar
exactamente las mismas `extra_auto` con los mismos `id`, `horas` y `hora_*`, y no consumir
ningún valor de la secuencia de `parte_registros`.

R2. CUANDO un split cae en una pareja que ya tenía `extra_auto` no congelada, el sistema debe
actualizar esa fila en el sitio (mismo `id`) con los campos que hoy clona `_extra_de`, en vez
de borrarla y crear otra.

R3. CUANDO una pareja tiene varios splits o varias extras reutilizables, el sistema debe
emparejarlos por orden (splits por `normal_id` ascendente, extras por `id` ascendente): el
k-ésimo split reutiliza la k-ésima extra; los splits sobrantes crean extra nueva y las extras
sobrantes se borran.

R4. CUANDO una pareja que tenía `extra_auto` ya no necesita extra en esta pasada (cambió la
jornada, las horas o el día pasó a laborable), el sistema debe borrar esa extra y dejar la base
con `horas = horas_orig` y `horas_orig = None`, igual que hoy.

R5. CUANDO un split trae `id` (camino de F-046), el sistema debe usar ese `id` para la extra
nueva y no reutilizar otra de la pareja para ese split.

R6. El número `extras_reclasificadas` del resumen debe seguir contando los splits aplicados
(extras nuevas + reutilizadas), para que F-037 R10-R16 y F-003 R26 no cambien. El log de la
pasada debe dar además `extras_nuevas`, `extras_reutilizadas` y `extras_borradas`.

### Una sola transacción (pieza 2)

R7. La pasada no debe hacer commit de ningún revert antes de la escritura de la pasada: el
cálculo de splits se hace sobre la vista revertida en memoria.

R8. El sistema debe escribir en UNA transacción el revert de todas las parejas (también las de
partes inactivos, como hoy), los casados de recurso (`apply_recurso_matches`) y los splits.

R9. MIENTRAS corre una pasada, un lector concurrente en READ COMMITTED debe ver cada pareja
o en su estado anterior completo o en el nuevo completo: nunca una base revertida sin su
extra, ni una extra sin la base recortada, ni un id de extra que exista solo a medias.

R10. Dentro de la transacción de escritura el sistema no debe hacer ninguna llamada de red
(Sigrid, Sesame, colas): todo lo de fuera se lee antes.

R11. La vista revertida debe dar al cálculo exactamente las mismas filas que hoy dan
`revert_extras_auto` + `fetch_registros_para_recurso` sobre el mismo estado, incluido
`congelada_por_pareja`, de modo que los splits sean idénticos (los dorados de F-003 R15 y los
de F-045 siguen verdes sin tocar sus valores esperados).

R12. F-046 (R15): `materializar_repartos` debe seguir corriendo antes de leer, en sus propias
transacciones y sin cambios; solo toca líneas congeladas, que el revert no toca.

### Concurrencia con sv4 entre la lectura y la escritura

R13. CUANDO en la escritura una fila de una pareja ya no tiene la huella leída (cambió horas,
`horas_orig`, `tipo_hora`, `extra_auto`, `sigrid_estado`, `deleted_at_utc`, la aprobación del
parte, o la fila desapareció o apareció una nueva en la pareja), el sistema NO debe tocar
ninguna fila de esa pareja en esta pasada (ni revert ni split) y debe emitir un WARNING con
la clave sin nombres ni DNI y contar `parejas_cambiadas` en el log.

R14. SI una fila de la pareja está congelada al escribir (por `esta_congelado`, la regla
gemela que no cambia), ENTONCES el sistema debe aplicar R13 aunque al leer no lo estuviera.

R15. La escritura debe bloquear las filas de las parejas que toca (`SELECT … FOR UPDATE` en
PostgreSQL) antes de comprobar huellas, para que nadie las cambie entre la comprobación y el
commit. En SQLite (tests) no hay bloqueo y el resto se comporta igual.

R16. SI la escritura de la pasada lanza, ENTONCES el sistema debe hacer rollback completo
(ninguna pareja a medias) y propagar la excepción como hoy (reintento del mensaje; F-047 no
marca el parte nuevo como repartido).

### Lo que se conserva

R17. La regla de congelación por línea (`esta_congelado`, `ESTADOS_CONGELADOS` en sv3,
`congelacion.py` en sv4) y F-037 (`plan_revert`, `clave_pareja`, duplicados R6) no cambian;
`tests/test_f024_borrado_no_congela_gemelos.py` y los tests de F-037 siguen verdes.

R18. `revert_extras_auto` y `apply_extras_splits` siguen existiendo con el mismo contrato
observable para sus tests (F-015 R31, F-037, F-046 R15), implementados sobre las mismas piezas
que `escribir_pasada`.

R19. La pasada sigue bajo el candado consultivo de F-046 (`candado_pasada`) y se dispara
igual que hoy (parte nuevo y recálculo). Que la pasada sea global queda FUERA.

### Mensaje opcional de sv4 (solo si el humano aprueba DA1)

R20. DONDE DA1 esté aprobada, CUANDO `_validar_ambito` encuentra ids fuera del ámbito y alguno
no existe en `parte_registros` (ni en la papelera), el sistema debe responder 422 con
`fuera_de_ambito` como hoy, un campo nuevo `inexistentes` (cuántos) y un texto que diga que
esas líneas ya no existen porque se están recalculando las extras y que recargue en unos
segundos. Si todos los ids fuera existen, la respuesta es la de hoy, sin cambiar el texto.

R21. DONDE DA1 esté aprobada, comprobar la existencia debe costar como mucho una consulta por
lote de `LOTE_IDS_CONSULTA` y solo cuando ya hay ids fuera del ámbito.

## Verificaciones manuales (humano)

**M1 · local, PostgreSQL desechable** (antes de desplegar). Con Docker:
1. `docker run --rm -d --name pg-f069 -e POSTGRES_PASSWORD=<local> -p 55432:5432 postgres:16`.
2. En `services/partes-persistencia`, con `F069_PG_URL` apuntando a ese contenedor:
   `python -m pytest tests/test_f069_pg_lector_concurrente.py -v` (sin la variable se salta).
   Debe pasar: 20 pasadas con un lector que consulta en bucle y nunca ve una base sin su
   extra, ni ids distintos tras la primera pasada.
3. `docker stop pg-f069`. Sin Docker: DA4.

**M2 · Azure, solo lectura, tras desplegar sv3** (lo pide el humano). En una tanda de partes:
1. Antes y después de la tanda, en `partes` con `default_transaction_read_only=on`:
   `SELECT last_value FROM parte_registros_id_seq;` y los `id` de las `extra_auto` no
   congeladas. Debe crecer solo por las líneas nuevas, no ~50 por pasada.
2. En Log Analytics de sv3: `extras_reutilizadas` ≈ `extras_reclasificadas` y
   `parejas_cambiadas` = 0 casi siempre.
3. Durante la tanda, abrir una obra con extras automáticas pendientes y anotar los
   `data-registro-id` de sus extras (herramientas del navegador); recargar tras otra pasada:
   son los mismos. **No** se aprueba nada ni se escribe en Sigrid.
