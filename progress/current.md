<!-- progress/current.md -->
# Trabajo en curso

## F-003 · Integración sesame-api: festivos y jornada reales

- Estado: **IMPLEMENTADA**, pendiente de reviewer (2026-08-15) en la rama
  `feature/F-003-sesame-festivos-jornada`. Rigor critico · sdd=true.
  Las 18 tareas de `tasks.md` están marcadas y commiteadas (un commit por
  tarea, más tres de refuerzo de tests guiado por mutación).
- Informe completo: **`progress/impl_F-003.md`**.
  Campaña de mutación y análisis de supervivientes:
  **`progress/mutacion_F-003.md`**.
- `bash harness/init.sh` en verde, con `PUERTA COBERTURA` al 93,4 % de las
  líneas cambiadas (umbral 80 %).

### Lo que hay que saber para revisar

- **La feature va APAGADA**: sin `SESAME_API_BASE_URL` + `SESAME_API_KEY`
  no hay ni una llamada de red, los festivos salen del respaldo de
  siempre (`holidays` en sv4, JSON en sv3) y no existe ningún bloqueo ni
  marca. Hay tests de regresión que lo fijan (R7, R10, R27).
- **Cero cambios de schema**: ninguna copia de `orm_models.py` se ha
  tocado. La marca `[SIN-SESAME]` va en `sigrid_motivo`, que ya existía.
- **Desviación consciente del design**: `marcar_registros_sigrid` recibe
  un `motivo_ok` opcional (el design decía «nada más» de
  `parte_repository.py` aparte del `dni` de `ObraMatrixRow`). Sin ese
  parámetro no había forma de escribir la marca de R25, porque la traza
  se escribe dentro del repositorio. Por defecto no cambia nada.
- **Un bug real encontrado y arreglado** por la campaña de mutación:
  `SesameCalendarioLaboral.es_no_laborable` normalizaba la fecha para el
  fin de semana pero buscaba el festivo con la cadena cruda; un ISO con
  hora daba «laborable» en pleno festivo. Detalle en el informe.

### Pendiente del humano

1. Verificaciones MANUALES listadas en `progress/impl_F-003.md`
   («+ Nuevo» en el navegador, modal de override, diff de `infra/`, diff
   de `CLAUDE.md`, documento de `azure-apps`).
2. `azure-apps/partes.md` actualizado con el consumo de sesame-api:
   commit local `5a95c03` en ESE repositorio, **sin push**.
3. **Peticiones al proyecto sesame-api** (no se implementan aquí):
   - **P1**: exponer la jornada del contrato en horas; hasta entonces la
     jornada teórica sigue saliendo del `candef` de Sigrid.
   - **P2**: commitear y desplegar sesame-api, con la clave de partes en
     `kv-partes-pt7m3` (`sesame-api-key`). Hasta P2 la feature no se
     puede encender.
   - **P3**: escribir `azure-apps/sesame-api.md` (dueño: ese proyecto).
4. **Aviso operativo**: encender `SESAME_*` contra una URL que no
   responda BLOQUEA las aprobaciones (R23). Es deliberado —calcular mal
   en silencio es peor— pero conviene saberlo antes de tocar Azure.

### Contexto operativo heredado

- F-002 desplegada en Azure; sv5 en MODO PRUEBAS (obra 0404) hasta que el
  humano valide en navegador y pase a modo normal.
- F-010 (resincronizar `orm_models.py` entre sv3 y sv4) sigue en el
  backlog: F-003 no lo ha tocado, a propósito.
