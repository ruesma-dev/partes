<!-- progress/spec_F-056.md -->
# spec-author · F-056 · Franquicia de extras — ENMIENDA DA1 = C (2026-10-27)

Spec enmendada en `specs/F-056-franquicia-de-extras/` (rama `feature/F-056-franquicia-de-extras`,
worktree `partes-wt-f056`, sobre 6d777c4). Topes: requirements 150/150, design 233/250, tasks 22
(una por línea). La versión aprobada el 2026-10-23 sigue en `git show 6d777c4:specs/...`.
Resumen del 2026-10-23 (DA1–DA20, M1): mismo fichero en 6d777c4.

## Enmienda DA28 (2026-10-27): decidir desde la vista

Hueco que halló el implementer en R20: la vista pedía «Ajustar»/«Recalcular» pero solo existía
`POST /api/franquicia/{id}/aplicar` (y sin fila no hay `id`). **Decisión del humano, literal «a»**,
a la opción A tal como se le presentó: «Una llamada nueva, "decidir", con trabajador, periodo y
decisión. Tiene las mismas comprobaciones que la decisión del modal (que ese trabajador tenga líneas
en el periodo y que nadie lo haya cambiado entretanto) y después aplica.» B (`aplicar` con `decision`
opcional) y C (solo en el modal) descartadas. Tamaños: requirements 150/150, design 248/250.

- **R45** `POST /api/franquicia/decidir {recurso_ide, periodo, decision}`: 422 por formato, por
  decisión distinta de `ajustar`/`recalcular` (la vista no ofrece «No ajustar» ni «Mantener») o sin
  líneas activas de ese recurso en el periodo; propuesta y CAS como el modal (409); sin sv5;
  `{ok, ajuste}`. **R46** con `ok`, la vista llama a `/aplicar` de ese `id` y pinta el resultado, sin
  recarga nueva (F-043). **R16** ahora lista las transiciones ya implementadas en T14. **R21** cubre R45.
- Diseño (§4): `fq.decision_vista` + `_decision` compartida con `validar_decisiones`; `_plan_franquicia`
  extraído de `_planes_franquicia` (sin duplicar R6–R8, R12); `decidir_ajuste` sin cambios; guardián
  F-017 a 20 `_actor(request)`; botones `data-franquicia-decidir` y `decidirDesdeVista` en `app.js`.
- **T17b** nueva (sin renumerar). Para compactar: se resumieron la cabecera, el glosario (Periodo),
  R12, R15 y R23 sin perder contenido.
- Abierto para el humano: nada nuevo (DA28 decidida). Sigue abierto lo de antes (M1b–M4).

## Qué cambia

- **X sale de Sigrid**: campo NUEVO de `res`, nombre en el ajuste de sv5 `FRANQUICIA_CAMPO_RES`
  (vacío = apagado). Activa si ≠ NULL y ≠ 0; sin fecha ni vigencia. Caen `empleado_franquicia`,
  `franquicia_admin.py`, las rutas y la sección de `/admin/jornadas` y `franquicia_vigente` (DA19).
- **Solo sv5 lee el campo** (DA21): `POST /api/franquicia/recursos` nuevo (una llamada por preflight
  o vista; estado global `apagada`/`no_disponible`/`ok` y `{franquicia, estado}` por recurso), y
  `comprobar`/`ejecutar` releen X ellos mismos (`ejecutar`, bajo el lock). La petición pierde
  `franquicia`; la respuesta gana `franquicia` y `franquicia_estado`. sv4 no lee `res` ⇒ ningún
  gemelo de F-023/F-036 cambia y la lista cerrada no crece.
- **Comprobación de la columna**: `INFORMATION_SCHEMA.COLUMNS` parametrizado (`dbo`/`res`/nombre)
  y tipo numérico; el nombre se valida con `^[A-Za-z_][A-Za-z0-9_]{0,127}$` antes de interpolarlo
  entre corchetes. Lectura de valores en consulta aparte (no en `datos_recursos`: una columna
  inexistente tumbaría el registro).
- **Fallos**: apagada = silencio; nombre malo, columna ausente, tipo no numérico o lectura fallida =
  `no_disponible`, aviso no bloqueante en el modal, WARNING; `ejecutar` NO escribe («no se sabe» no
  es X = 0). sv5 arranca y registra igual.
- **sv5 hecho (T1–T7)**: cambia poco y se hace en T8–T11 (dataclasses, `leer_valor`, `veredicto`
  con la lectura, `texto_ajuste` sin cifras, settings, dos lecturas del cliente, `franquicias()` en
  el pipeline, endpoint y `/health`). Lo demás (E, A, alta, `UPDATE`, choques, relectura) intacto.
- **`franquicia_ajuste` se queda** (DA25): guarda la decisión (rechazo, pendiente en asíncrono),
  autoría, X usada, y su `id` es la synckey ya implementada. Guardianes a OCHO tablas, no nueve.
- **`tex`** (punto abierto del implementer, DA26): sin cifras, `Ajuste franquicia extras <periodo>`;
  nunca queda desfasado y `stmt_actualizar_linea` (compartida con F-046/F-053) no cambia.
- Numeración de requisitos conservada (los tests de T1–T7 llevan R19, R22–R33): nuevas R1–R3 y
  R38–R44. Semántica nueva de `ARCHITECTURE.md` = la 21 (la 18 ya es F-054).

## DA nuevas o enmendadas (recomendación A en todas)

DA1 = **C (el humano)** · DA2 enmendada (X = valor del campo al leerlo) · DA17 enmendada (ajuste
vacío = apagado) · DA19 **cae** · DA20 enmendada (sv5 T1–T11, sv4 T12–T18) · **DA21** solo sv5 lee
el campo · **DA22** vale la X de Sigrid al aplicar/recalcular (también al recalcular un periodo
anterior); se guarda y se enseña si difiere del aviso · **DA23** fallo de configuración = no se
aplica, aviso, sin romper nada · **DA24** negativo, > 200 h o no numérico = `invalida` · **DA25**
`franquicia_ajuste` se mantiene · **DA26** `tex` sin cifras · **DA27** franquicia del recurso que
lleva las extras (el elegido por DNI de F-023/F-036), no de la persona.

## Riesgos

- **R-e**: si el compañero crea el campo fuera de `res` o no numérico, el diseño no basta ⇒ M1b
  (solo lectura, `design.md` §10) antes de activar; si falla, `blocked` y enmienda.
- **R-f**: retroactividad de DA22 (un cambio de X afecta a periodos que se recalculen antes de la
  nómina).
- **M2** necesita que Administración ponga X en el recurso de pruebas de F-034 en Sigrid (F-056 no
  escribe `res`); M2 no se puede hacer hasta que exista el campo.
- Sigue siendo grande; corte natural tras T11 (sv5 entero, desplegable con el campo vacío).
