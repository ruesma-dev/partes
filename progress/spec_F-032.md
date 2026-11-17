<!-- progress/spec_F-032.md -->
# F-032 · Resumen de la spec rehecha (2026-11-17)

Rama `feature/F-032-sesame-festivos-produccion`, sobre `f2de8dd`. Spec en
`specs/F-032-sesame-festivos-produccion/`: requirements 150/150, design 249/250
(`python -m harness.tamano --feature F-032` en verde) y 29 tareas. Rigor **estándar** (DA10, que se
mantiene). `harness/features.json` no se ha tocado: el estado lo marca el líder.

## Qué cambia respecto a f2de8dd (diseño del humano, 2026-11-17)

1. **Los festivos se guardan (DA14).** Hay una tabla nueva, `festivos_trabajador`, en la base
   `partes`:
   - Columnas: `dni_norm`, `ano`, `festivos_json` (fecha → nombre), `n_festivos`, `origen`
     (`sesame` o `por_defecto`) y `leido_en_utc`. Índice único (DNI, año).
   - La fila `*` guarda el calendario por defecto de Sesame de cada año.
   - Va en los dos `orm_models.py` gemelos, en el mismo commit, y el guardián de F-010 pasa a
     nueve tablas.
   - **Migración**: no hace falta script. La crea `create_all` al arrancar sv3 o sv4, igual que
     se creó `franquicia_ajuste` (F-056). `ddl_complementario()` añade su índice.
2. **Sesame solo se lee al ingerir (DA15).** sv3 tiene un `RefrescoFestivos` nuevo en el
   pipeline, que corre antes de `save_parte`:
   - Pide los festivos de cada DNI del parte para los años de la semana ISO de su fecha, más
     el calendario por defecto, y hace upsert (`ON CONFLICT`, aguanta dos réplicas).
   - Si Sesame responde 404, guarda el calendario por defecto bajo ese DNI.
   - Una respuesta incompleta (por debajo del mínimo, DA5 = 1) no se guarda.
   - **Si falla, se queda lo último guardado**, sin marcar el parte. Sin nada guardado, el
     parte se guarda con `review_required` (DA4 ajustada: la degradación pasa a la ingesta).
   - Las pasadas `conciliar_todos` y los `recalcular` de sv4 **no llaman a Sesame**: leen la
     tabla, con caché de 60 s que el refresco invalida.
3. **sv4 solo lee la tabla (DA16).** `CalendarioProvider` deja de pedir festivos a Sesame.
   - Aparece la fuente nueva `sin_fila`, que no es fiable.
   - Los avisos dicen «Sin calendario de Sesame» en vez de «Sesame no disponible».
   - La jornada (`/jornada`, DA8) no cambia.
4. **Lo que se retira.**
   - DA11, `pedir_recalculo_partes.py` y la lectura de claves de storage.
   - `SesameCalendarioLaboral` y su test de F-003: el código muerto que vuelve a llamar a
     Sesame es peligroso.
   - En sv3, `SESAME_CACHE_TTL_S`.
   - Del cliente gemelo, el mínimo de festivos: ahora solo lo usa sv3, en el refresco, y los
     dos `sesame_api_client.py` no cambian.
5. **Encendido.** `add_sesame_partes.ps1` sigue haciendo falta, porque crea el secreto
   `keyvaultref`, fija las variables y valida, pero se simplifica:
   - Gana `-Servicio sv3|sv4` y no encola nada.
   - sv3 lleva `SESAME_FESTIVOS_MINIMOS`. sv4 sigue necesitando `SESAME_API_*` para la jornada
     y como interruptor (DA18).
   - Se enciende **primero sv3 y, días después, sv4** (DA17, M6).
   - La herramienta de contraste (DA6) sigue llamando a sesame-api directamente. Con
     `--impacto` cuenta además los DNIs activos sin fila: es el dato para encender sv4.
6. **Recálculo.** Cada trabajador pasa a usar Sesame cuando llega un parte suyo: la pasada de
   esa ingesta recalcula también sus líneas libres anteriores. Lo congelado sigue intacto
   salvo las propuestas de F-046.
7. **Se mantienen** DA1–DA3 y DA6–DA10 (DA3 con `-Servicio`), DA12 (puerta) y DA13 (rejilla
   por persona, ahora leída de la tabla). En design §9 queda «Decidido» relleno para DA1–DA16.
8. **Numeración nueva**: R1–R39, T1–T29 y M1–M8.

## Límite de servicio

- **Repositorios.** sv3 escribe y lee; sv4 solo hace un `SELECT`. **No es lógica duplicada**:
  son responsabilidades distintas sobre una tabla común, como `empleado_jornada`.
- **Lo que sí se duplicaría.** La regla de qué fila manda y el formato de `festivos_json`. Va
  a un módulo puro gemelo, `application/services/festivos_guardados.py`, con un guardián de la
  raíz. Para entrar en la lista cerrada necesita tu sí (DA20).
- **DNI.** Es un dato personal: ningún log nuevo lo lleva (R3).

## Decisiones abiertas (recomendación en negrita)

- **DA17: el bloqueo `[SIN-SESAME]` cuando una persona no tiene fila.**
  - **(A) Se mantiene**: sin fila no es fiable, así que bloquea salvo override. Para que el día
    del encendido no quede todo bloqueado con la tabla vacía, se enciende sv4 después que sv3,
    tras al menos dos días laborables y cuando `--impacto` dé pocos DNIs sin fila.
  - (B) Solo aviso.
  - (C) Bloqueo con los dos encendidos a la vez.
- **DA18: el interruptor de sv4.**
  - **(A) sv4 conserva `SESAME_API_*`**: encienden la lectura de la tabla y la jornada, como
    decía DA8, sin variable nueva.
  - (B) Una variable nueva y la jornada apagada.
- **DA19: los respaldos cuando no hay fila** (el riesgo que pediste tratar).
  - **(A) Los dos servicios usan la fila `*`** (calendario por defecto, Madrid para 196 de 218
    personas) y, sin ella, su respaldo local. Así sv3 paga y sv4 enseña lo mismo en cuanto
    existe la fila `*`, que se crea con el primer parte tras encender. **Ojo: cambia tu «sin
    fila ⇒ JSON» de DA15** por «sin fila ⇒ fila `*`; sin ella ⇒ JSON».
  - (B) Dejar sv3 con el JSON y sv4 con la fila `*`: difieren bajo el aviso.
  - (C) Alinear sv4 con el JSON por configuración: cambiaría hoy el portal con Sesame apagado.
- **DA20: la cascada gemela.** **(A) `festivos_guardados.py` entra en la lista cerrada de
  `CLAUDE.md`** con su guardián. (B) Cada servicio la suya, sin guardián.

## Avisos para el humano

- **Rigor.** Se queda en estándar, como decidiste, pero ahora es código nuevo el que decide con
  qué festivos se paga (disparador 1 de `critico`). Si lo quieres crítico, es el momento.
- **Partes activos de 2025.** Si los hay, M2 y M3 se pasan también con `--ano 2025`.
- **La pregunta de f2de8dd sobre las claves de la storage desaparece.**
