<!-- progress/spec_F-019.md -->
# F-019 · Spec lista para revisar (resumen para el humano)

Spec: `specs/F-019-mensuales-a-dedicacion/` (requirements 149 líneas, design
~235, tasks 19 tareas). Rigor crítico. Estado `spec_ready`. **No se
implementa nada hasta que apruebes DA1–DA8** (`design.md` §8).

## Qué propone, en llano

1. **sv5 decide.** Al aprobar, si el recurso de la línea tiene un código
   `M*` en Sigrid, la línea no se escribe en Sigrid: sv5 la marca «a
   dedicación» y lo devuelve en su resultado. sv5 sigue sin base de datos.
2. **sv4 la publica.** Al recibir ese resultado, sv4 deja la línea en estado
   `dedicacion` y escribe una fila en una tabla nueva de la base `partes`,
   `dedicacion_bandeja`: una fila por línea, con trabajador (`res.ide`),
   fecha, obra, partida, tipo, horas, incidencia y su clase. Sin nombres
   ni DNIs.
3. **dedicación la lee.** Con permiso de solo lectura sobre esa tabla y
   nada más. El permiso lo das tú, con un script versionado (`psql -f`).
4. **En el portal**: «→ dedicación» en lugar de «omitido», la línea queda
   congelada como si estuviera registrada, y un botón «Retirar» la saca de
   la bandeja (queda como retirada, con versión) y la deja editable para
   reaprobar.
5. **Un interruptor en sv5** (`MENSUALES_A_DEDICACION`, apagado por
   defecto). Con él apagado todo funciona como hoy. Lo enciendes tú cuando
   dedicación ya lea la bandeja; apagarlo es el rollback.

## Decisiones que te tocan (mi recomendación)

| DA | Pregunta | Recomiendo |
|---|---|---|
| DA1 | Canal | Bandeja en la base `partes` que dedicación lee. Descarto escribir en la base de dedicación, HTTP (su API no tiene autenticación) y colas |
| DA2 | Quién escribe la bandeja | **sv4**, no sv5: la arquitectura fija que sv5 va sin BBDD. Cambia lo que proponía el líder |
| DA3 | Con qué rol lee dedicación | Su rol de aplicación de siempre, con `GRANT SELECT` solo sobre esa tabla. Aviso: en PostgreSQL un rol es del **servidor**, no de una base; «crear el rol dentro de la base partes» no se puede hacer. Así no se crea nada a nivel de servidor |
| DA4 | Capataces `MCAP`+`HECAP` (32) | Sus extras siguen a Sigrid con `HECAP` como hoy; lo demás, a dedicación. **Es una excepción a tu decisión 2** («todas las horas»): necesito tu sí |
| DA5 | Desaprobar y reaprobar | Congelar como `registrado` y botón «Retirar de dedicación»; reaprobar no duplica (una fila por línea, con versión) |
| DA6 | Periodo cerrado en dedicación | partes publica igual; decide dedicación al leer. El portal dice «enviada», no «aplicada» |
| DA7 | Dónde se decide | sv5, que ya lee los códigos del recurso al aprobar |
| DA8 | Despliegue y lo ya aprobado | Interruptor apagado; nada automático con el histórico: lo `omitido` de los meses que elijas se reaprueba desde el portal; lo `registrado` se queda en Sigrid |

## Riesgos

- **El cambio de producción** (las incidencias de los mensuales dejan de ir
  a Sigrid) solo ocurre al encender el interruptor. Si se enciende antes de
  que dedicación lea, esas incidencias no las ve nadie: por eso el orden.
- Orden de despliegue: **sv3 → sv4 → script de permiso → sv5** (apagado) →
  feature de porcentajes leyendo → encender.
- Una reentrega tardía de la cola tras una retirada vuelve a publicar la
  línea: ventana de minutos, se arregla retirando otra vez.
- El criterio `M*` es el mismo que el de dedicación: si allí cambia, aquí
  hay que cambiarlo (queda en `azure-apps/partes.md`).

## Datos reales (lectura de Sigrid, 2026-10-02, solo recuentos)

195 recursos persona de alta con `M*`; 32 son `MCAP`+`HECAP`; ninguno con
`HL*` ni con dos `M*`; los 163 sin `HE*` tienen todos `M*` (el cambio de
criterio solo afecta de verdad a los capataces). Ninguna línea de `hmores`
lleva synckey `partes:`: hoy no vive en Sigrid ninguna incidencia de
mensual escrita por partes (lo confirmas con M0 en la base `partes`).

## Lo que queda fuera

La feature espejo en `porcentajes` (la creas tú allí): leer la bandeja,
convertirla en propuesta del cuadrante, el cálculo por días laborables
(vacaciones como trabajadas, festivos fuera), el calendario, el periodo
cerrado, las obras de otra empresa y su `azure-apps/dedicacion.md`.
Ejecutar el `GRANT` y desplegar también son tuyos.
