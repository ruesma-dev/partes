<!-- progress/spec_F-032.md -->
# F-032 · Spec con las decisiones finales del humano (2026-11-17)

Rama `feature/F-032-sesame-festivos-produccion`, sobre `7a289a4`. Spec en
`specs/F-032-sesame-festivos-produccion/`: requirements 150/150, design 250/250
(`python -m harness.tamano --feature F-032` en verde) y 31 tareas. **DA1–DA20 decididas**
(DA11 retirada); «Decidido» relleno en design §9. `harness/features.json` sin tocar: el rigor
nuevo y el estado los anota el líder.

## Qué cambia respecto a 7a289a4

1. **DA19 → B, sin fila ⇒ respaldo actual.** Quien no tiene fila propia en
   `festivos_trabajador` usa lo que se usa hoy: sv3 el JSON y sv4 `holidays` de Madrid más
   los extras. Con eso:
   - **La fila `*` desaparece**: no servía para nada más. El refresco ya no pide
     `calendario_por_defecto` y la columna `origen` sale de la tabla, que queda en seis columnas.
   - **Un 404 de Sesame ya no guarda el calendario por defecto bajo el DNI.** No escribe ni
     borra nada: la persona sigue con su fila si la tenía y, si no, con el respaldo actual.
     Tampoco sube el parte a revisión, porque es una respuesta de Sesame y no un fallo (R5).
     Es lo coherente con «si no tiene festivos en Sesame, que coja el estándar actual».
     DA4 no cambia: un fallo (excepción, plazo o incompleto) sin fila sigue marcando
     `review_required`.
   - En `festivos_guardados.py`, `elegir` da `sesame` o `sin_fila`. Las fuentes `default` y
     `stale` de sv4 desaparecen.
2. **DA17 → B, sin bloqueo** (design §5.10, R21–R24):
   - sv4 ya no bloquea el registro por el calendario en ningún caso. El preflight cambia
     `sesame_bloqueo` por `aviso_sesame`, que no bloquea. `ejecutar` y `encolar` dejan de
     mirarlo.
   - Se retiran el override `forzar_sin_sesame` (si llega, se ignora), la marca
     `MOTIVO_SIN_SESAME` y la casilla y el título de bloqueo de `app.js`.
   - El día de ajuste de F-056 se calcula con el calendario que haya.
   - **Las líneas que ya lleven `[SIN-SESAME]`** conservan el texto y el badge, que lee
     `sigrid_motivo`. En producción no debería haber ninguna: F-003 nunca se encendió.
   - Los tests de F-003, F-017, F-022 y F-056 que fijaban el bloqueo cambian a propósito. La
     lista, test a test, está en T16; quedan los del badge y los de R27, que es el apagado.
3. **Encendido en un solo paso.** Sin bloqueo, ya no hace falta escalonar. Cambia:
   - `add_sesame_partes.ps1` pierde `-Servicio`: configura sv3 y después sv4, y `-Quitar`
     retira las dos.
   - El antiguo M6 («sv4 días después») desaparece, y las verificaciones manuales pasan a
     **M1–M7**.
   - `--impacto` ya no cuenta los «DNIs sin fila» y el repositorio pierde `claves()`.
4. **DA18 = A y DA20 = A.** La edición de la lista cerrada de `CLAUDE.md` es la tarea T26.
5. **DA10 → crítico**, por los disparadores 1 (dinero: reparto ordinaria/extra) y 3 (datos
   personales: DNIs en la tabla). En consecuencia:
   - La cobertura sube al 90 %.
   - La mutación pasa a ser exigida con la regla del nivel (60 %, entre 100 y 300 mutantes,
     semilla 20261030), con cero supervivientes sin justificación aceptada (T27).
   - Cada M se anota con su comando y su resultado real.
6. **Numeración nueva**: R1–R42, T1–T31 y M1–M7.

## Riesgo conocido, sin decisión nueva

- **Respaldos distintos.** sv3 usa los festivos nacionales más `2026-02-28` y sv4 los de
  Madrid. Para quien no tiene fila, sv3 paga con uno y sv4 enseña el otro, bajo el aviso. Solo
  afecta a esas personas: quien tiene fila ve lo mismo en los dos servicios.
- **Sin bloqueo, una línea calculada con el respaldo puede llegar a Sigrid.** Lo cubren tres
  defensas:
  - el aviso;
  - `review_required` si falla el refresco;
  - el recálculo con el siguiente parte.
- **El día del encendido el aviso sale casi a todos**, hasta que llega el primer parte de cada
  uno.
