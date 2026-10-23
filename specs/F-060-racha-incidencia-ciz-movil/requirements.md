<!-- specs/F-060-racha-incidencia-ciz-movil/requirements.md -->
# F-060 · Racha de incidencia con CIZ móvil — Requisitos

**Servicios: sv4** (decide el rol de cada incidencia con el histórico de `partes` y aplica el
resultado) **y sv5** (localiza en Sigrid el CIZ de la racha y lo mueve editándolo). Sin
tabla ni columna nueva, sin colas nuevas. Rigor **crítico**: cambia lo que se escribe en
Sigrid de producción. Interruptor `MOVER_CIZ` en sv5, apagado por defecto (DA11).

**Petición del humano (2026-10-23, literal)**: «el primer dia de unas vacaciones siempre debe
marcarse como inicio vacaciones, si luego al dia siguiente aparece vacaciones debe guardarse
fin de vacaciones. este fin se va moviendo segun aparzcan dias de vacaciones hasta que
aparezca un dia laborable en cuyo caso ya no se mueve. [...] lo mismo para bajas.» Sobre la
tabla del líder: «la propuesta es lo correcto [...] debe buscar siempre en todos sus partes
del mes anterior». Regla de Sigrid: «no se debe borrar en sigrid, así que solo editará
líneas». Ejemplo aprobado: día 1 V ⇒ CIV; día 2 V ⇒ CIZ el día 2; días 3 y 4 V ⇒ ese CIZ
pasa al 3 y al 4; día 5 con horas ⇒ el CIZ se queda en el 4. En Sigrid, CIV y un CIZ.

**Aprobación del humano (2026-10-23, literal)**: «a en todo, lanza implementer y spec de la sigueinte feature» ⇒ DA1–DA11 = A. DA3 y DA6 siguen pendientes del visto bueno de Administración antes de encender `MOVER_CIZ` (no bloquean la implementación).

**M0 (líder, 2026-10-23, solo lectura en `ruesma`)**: CIZ con synckey `partes:%`: 2 líneas (2026/10), 2 recursos, 0 enlazadas; 0 recursos-mes con más de un CIZ. DA3 no cambia; el legado de DA8 es nulo.

## Contexto (dev 0926857; detalle en `design.md` §1)

sv4 `_rol_incidencia` (`parte_repository.py`) da `fin` a todo día de incidencia que sigue a
otro (no hay partes futuros) y sv5 (`reglas_registro.py`, R1) escribe un CIZ nuevo por cada
`fin`: hoy quedan varios CIZ por racha. Además no distingue la letra, mira 50 filas sin
límite de fechas y cuenta partes en la papelera.

## Glosario

- **Persona**: `persona_de` de F-025 (DNI normalizado; sin DNI, la clave de trabajador).
- **Línea activa**: `deleted_at_utc` nulo y documento con `is_active` verdadero (DA5).
- **Clave de incidencia**: la letra de la línea según la tabla de F-025; si no está, su
  `incidencia_codigo` y, si falta, su `hora_codigo`, normalizados (DA4).
- **Día trabajado**: con alguna línea activa que no es incidencia y con |horas| > 0.
  **Día de incidencia X**: no trabajado y con alguna línea activa de incidencia de clave X.
  Un día sin líneas activas, o solo con líneas a 0 h que no son incidencia, se salta.
- **Ventana de D**: del día 1 del mes anterior al de D hasta D − 1, ambos incluidos (DA1).
- **Racha abierta en D (clave X)**: el último día con líneas de la ventana es día de
  incidencia X. **CIZ de la racha**: línea de Sigrid con código `CIZ` y synckey
  `partes:<id>` de una línea de la racha.

## Requisitos

### sv4 · rol de cada incidencia al aprobar

R1. CUANDO sv4 prepara una aprobación (`lineas_para_registro`), el sistema debe calcular el
rol de cada línea de incidencia del día D solo con las líneas activas de su persona en la
ventana de D, de cualquier obra y estado, sin tope de filas.
R2. SI en la ventana no hay ningún día con líneas, ENTONCES el rol debe ser `inicio` (DA1).
R3. SI el último día con líneas de la ventana es día trabajado o día de incidencia con otra
clave, ENTONCES el rol debe ser `inicio` (DA4).
R4. CUANDO hay racha abierta en D con la clave de la línea, el rol debe ser `fin`, sin
mirar los días posteriores a D.
R5. Las líneas en la papelera (de línea o de documento) no deben contar para R1–R4 (DA5).
R6. CUANDO la persona no tiene DNI, el histórico debe cruzarse por la clave de trabajador
de `persona_de` (también `rec-<recurso>` de una línea sin ficha).
R7. CUANDO una aprobación lleva varias líneas de la misma persona y racha con rol `fin`
(en una o varias obras), solo debe conservarlo la de mayor fecha (empate: menor
`registro_id`); las demás deben ir `intermedio`.
R8. CUANDO una aprobación lleva varias líneas `inicio` del mismo día, persona y clave, solo
debe conservarlo la de menor `registro_id`; las demás deben ir `intermedio`.
R9. sv4 debe enviar en cada línea de incidencia con rol `fin` la lista `racha_registro_ids`:
los ids de las líneas de incidencia de esa persona y clave de la racha hacia atrás (desde
D − 1 hasta el primer día de la ventana que no es de la racha) y hacia delante (desde D + 1
hasta el primer día con líneas que no es de la racha, como mucho el último día del mes
siguiente a D), más las de la papelera de esos días que estén `registrado` o `encolado`;
ordenada y sin repetidos. En las demás líneas debe ir vacía.
R10. CUANDO se aprueba una línea del día D que es de trabajo (|horas| > 0) o de incidencia
con rol `inicio`, y el siguiente día con líneas de la persona tras D (hasta el último día
del mes siguiente) tiene alguna incidencia `registrado`, sv4 debe añadir a su grupo un
aviso en `avisos_racha` (`registro_id`, `fecha`, `nombre`, `motivo` con
`racha_desordenada`) sin bloquear la aprobación (DA7).
R11. El modal de aprobación debe listar `avisos_racha` en su propio bloque, aparte de
`avisos_incidencia`.
R12. El histórico debe leerse con una consulta por persona y aprobación, no por línea.

### sv5 · el CIZ de la racha se mueve, no se duplica

R13. DONDE `MOVER_CIZ` está encendido, CUANDO una acción `escribir` con código `CIZ` trae
`racha_registro_ids`, sv5 debe leer, dentro del lock y después de la idempotencia del paso
6, las líneas de Sigrid con synckey `partes:<id>` de esos ids (una lectura por petición) y
quedarse con las del mismo recurso, código `CIZ` y `can` nulo o 0.
R14. SI alguna de esas líneas tiene fecha posterior a D, ENTONCES la acción debe pasar a
`omitir` con el motivo de día intermedio, que debe nombrar el día del CIZ (DA7).
R15. SI ninguna es posterior y alguna es anterior a D, ENTONCES la de mayor fecha (empate:
mayor `ide`) debe ser la línea a mover; con más de una, las demás no se tocan y sv5 debe
dejar un WARNING `ciz_duplicados` con su número, sin nombres ni DNIs (DA8).
R16. SI no queda ninguna, ENTONCES sv5 debe escribir el CIZ como hoy (`INSERT`).
R17. SI la línea a mover está en un parte que no está En registro, ENTONCES la acción debe
pasar a `omitir` con motivo `ciz_en_parte_cerrado` (código y estado del parte) y no se
debe escribir otro CIZ (DA3).
R18. SI la línea a mover está enlazada (`ENLACES_HMORES`), ENTONCES la acción debe pasar a
`omitir` con el motivo `linea_enlazada` de F-053 y no se debe escribir otro CIZ.
R19. MIENTRAS el modo pruebas está activo, sv5 solo debe mover una línea cuyo `tex` lleve la
marca de pruebas; una sin ella cuenta como no encontrada (R16).
R20. Mover debe ser UN `UPDATE` de esa línea que ponga `fec` = D, `synckey` =
`partes:<registro de D>` y, del parte elegido para D (F-031), `hmoide`, `obride`,
`cenide`, `paride`, `caaide`, `ano` y `mes`, y `pos` nueva solo si cambia de parte. `can`,
`tot`, `pre`, `horide`, `reside`, `tex` y enlaces no deben cambiar (DA3).
R21. El `UPDATE` de R20 debe llevar `WHERE` optimista (`ide`, recurso, fecha, código y
synckey leídos, `ISNULL(can, 0) = 0`, sin enlaces) y la guarda de parte abierto de F-034
sobre el parte actual de la línea y sobre el parte destino.
R22. Ninguna sentencia de esta feature debe ser `DELETE`; una acción de mover no debe
generar `INSERT` de línea.
R23. CUANDO la relectura por synckey (F-034) encuentra la línea de D en el parte elegido,
su entrada de `escritas` debe llevar `movida_de` (el `registro_id` de la synckey anterior)
y `hmores_ide`; si no la encuentra, sale omitida con los motivos de F-034 y nada más cambia.
R24. CUANDO sv5 mueve un CIZ debe dejar un INFO con `ide`, parte y fecha antes y después y
los `registro_id`, sin nombres ni DNIs.
R25. El preflight (sin lock) debe aplicar R13–R19 de forma consultiva.
R26. DONDE `MOVER_CIZ` está apagado, o la línea no trae `racha_registro_ids`, sv5 debe
decidir exactamente como hoy (`fin` ⇒ CIZ nuevo). Por defecto, apagado.
R27. No deben cambiar: R0 de F-019 (dedicación manda sobre la racha), el código CI* del
`inicio`, `can = 0`, los conflictos del paso 7, F-024, F-046, `estado_parte.py` ni
`cuenta_analitica.py` (copias literales de `porcentajes`).

### sv4 · el día que tenía el CIZ

R28. CUANDO un resultado de sv5 trae en `escritas` una entrada con `movida_de` = X, sv4
debe, en la misma transacción que marca la línea de D, pasar X a `omitido` con motivo
`fin_movido` (día y línea de Sigrid nuevos), solo si X sigue `registrado` con ese
`sigrid_hmores_ide`; si no, no la toca y deja un WARNING sin nombres ni DNIs.
R29. Aplicar dos veces el mismo resultado debe dejar el mismo estado (los dos canales de
F-002 usan `aplicar_resultado`).
R30. `reparto_obras.agregar_ejecucion` debe conservar `movida_de` al juntar varias obras.

### Documentación y verificación

R31. `docs/ARCHITECTURE.md` (semántica 4), `docs/referencia/partes-proyecto.md` (§3.5 y
§4.4) y `azure-apps/partes.md` (paso 3 de sv5, `MOVER_CIZ`, «Qué se rompe») deben contar
la racha con CIZ móvil en el mismo trabajo (cambia lo que partes escribe en Sigrid).
R32. Verificaciones manuales M0–M4 de `design.md` §9: M0 de solo lectura antes de
implementar; M1–M3 en modo pruebas (obra 0404, `OBRA_PRUEBAS_FORZAR=true`, `PRUEBA-IA`),
limpiando con `prueba_escritura_sigrid.py`; M4 de solo lectura en producción.

## Fuera de alcance

Corregir las rachas ya escritas con varios CIZ (DA8: como mucho, el informe M0); mover el
CI* hacia atrás o el CIZ hacia atrás por llegadas desordenadas, desaprobaciones o papelera
(DA7: aviso y corrección manual); leer CI*/CIZ ajenos en Sigrid (DA1); un CIZ el mismo día
de un CI* suelto (DA6); rotular «mueve» en el listado del modal.
