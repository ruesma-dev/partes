<!-- progress/spec_F-055.md -->
# spec-author · F-055 · sv5 omite las líneas sin fecha válida (2026-10-22)

Spec en `specs/F-055-sv5-omite-lineas-sin-fecha/` (rama `feature/F-055-sv5-omite-lineas-sin-fecha`
desde `dev` 2bfeab7, worktree `C:\Users\pgris\PycharmProjects\partes-wt-f055`). `F-055` estaba
libre: el último id de `dev` es F-053, F-054 vive en su rama y ninguna rama `feature/*` declara
F-055 en su `features.json`. Origen: DA5 de F-054, aprobada el 2026-10-21 («apruebo F-054 y la
DA5»). `features.json`: F-055 `spec_ready`, prioridad **4** (DA8 A), rigor `critico` (DA9 A).

## Qué hace

- **Solo sv5**. Función pura `motivo_fecha_no_valida(fecha_int, *, hoy)` en
  `application/services/fecha_linea.py`: válida = entero, fecha del calendario, entre
  01/01/2026 y hoy + 31 días. Paso **2a** de `RegistroPipeline.preparar`: la línea va a
  `omisiones` con `fecha_no_valida: <detalle>; corrige la fecha en el portal y reaprueba`
  antes de 2b/2c/3, de modo que no se lee nada de Sigrid por ella y su omisión manda sobre la
  del recurso y sobre `dedicacion`. Un único punto para preflight, ejecutar, cola y extras
  nuevas del reajuste.
- `fecha_int` opcional en `LineaIn` y `LineaEntrada` (`ano`/`mes` con `or 0`): `null` o sin
  la clave no da 422 ni tumba la petición de cola.
- sv4, sv3, esquema, colas y contrato de respuesta sin cambios. Doc: ARCHITECTURE semántica 6
  y `azure-apps/partes.md` (motivo nuevo y nota informativa a `porcentajes`).

## Hallazgos

1. **El daño es real** (sonda con `SigridFake` en el scratchpad, sin commit): con
   `fecha_int = 0`, `ejecutar` da de alta `PT0/00001` con `ano = 0`, `mes = 0` y escribe la
   línea con `fec = 0`; con `20261340`, un parte de **2026/13**. El cliente real hace lo mismo
   (`siguiente_cod_pt(0, …)` da `PT0/…`; `stmts_crear_parte` no valida el periodo). Con un año
   mal tecleado (2016) y los partes cerrados, F-031 crearía un complementario en ese año. Y el
   paso 7 buscaría choques en el día 0 (líneas ajenas con fecha NULL, que podría pisar a 0).
2. sv4 no filtra por fecha al aprobar: las 15 líneas con obra y sin fecha de M1 de F-054 (3
   documentos) viajarían con 0. Las 10 sin obra fallan antes (obra no encontrada).
3. `null` hoy: HTTP 422 a la petición entera; cola, `TypeError` en `LineaEntrada.ano` y
   `ok: false` para todas las líneas.
4. Todas las fechas de los tests de sv5 son de 2026 y ya pasadas (máx. 20261016;
   `20260300 + dia` siempre con día ≥ 1): la guarda no rompe la suite existente.
5. F-046: con `fecha_int` nulo o 0, la extra nueva ya no se prepara; con otro valor no válido,
   la cubre el paso 2a sin tocar `reajuste_pipeline.py`. F-034 y F-053 no ven las omitidas.
6. Sin gemelos ni copias de `porcentajes` afectadas; la lista cerrada no crece.

## Decisiones abiertas para el humano (`design.md` §11)

| DA | Recomendación |
|---|---|
| DA1 dónde | A: paso 2a de `preparar` (un punto para los cuatro caminos) |
| DA2 fecha válida | B: del calendario y entre 01/01/2026 y hoy + 31 días |
| DA3 sv4 | A: sin cambios (el que escribe se protege; F-054 da la señal) |
| DA4 `null` | B: opcional en dominio y en HTTP |
| DA5 sin obra | A: fuera (ya falla cerrado) |
| DA6 límites | A: constantes en código |
| DA7 `azure-apps` | A: motivo en `partes.md` + nota informativa a `porcentajes` |
| DA8 cola | A: prioridad 4, detrás de F-054 |
| DA9 rigor | A: crítico |

## Verificaciones manuales (`design.md` §9)

- **M1** (solo lectura, antes de implementar): líneas activas sin fecha, anteriores a 2026 o a
  más de 31 días, por `sigrid_estado`; y en Sigrid, líneas `partes:` con fecha imposible y
  partes `PT0/…` (esperado 0). Puede mover los límites de DA2.
- **M2** (sv5 local, modo pruebas, 0404): preflight con tres líneas inválidas ⇒ tres `omitir`;
  solo entonces ejecutar ⇒ `ok`, nada escrito, ningún `[sigrid-write]`. Sin `limpiar` ni los
  meses 06, 08 y 10/2026 (partes de pruebas que el humano conserva).
- **M3** tras desplegar sv5: M1 otra vez.

## Estado

Topes: requirements 98/150, design 241/250. `bash harness/init.sh` en verde. Un commit local
en la rama; sin push.
