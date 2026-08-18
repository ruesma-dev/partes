<!-- specs/F-004-congelar-aprobados/requirements.md -->
# F-004 · Congelar registros aprobados — Requisitos (EARS)

Alcance: un registro aprobado —y con más razón, ya registrado en Sigrid— no
debe poder editarse en el portal (sv4) sin desaprobarlo antes de forma
explícita. Servicio afectado: **solo sv4** (`services/partes-front`).

Vocabulario: «línea» = fila de `parte_registros`; «documento» = fila de
`parte_documents`; «congelado» = rechaza toda mutación de usuario.

## La regla central

- **R1** (ubicuo). El sistema debe decidir si una línea está congelada con
  UNA única función de decisión (pura, sin BBDD), según esta matriz:

  | Condición de la línea                                      | ¿Congelada? |
  |------------------------------------------------------------|-------------|
  | Documento `approved=true` (cualquier `sigrid_estado`)      | SÍ |
  | `sigrid_estado='encolado'` (petición en vuelo hacia sv5)   | SÍ |
  | `sigrid_estado='registrado'` (ya escrita en Sigrid)        | SÍ |
  | Resto (`NULL`/vacío, `omitido`, `error`, `conflicto`) con documento sin aprobar | NO |

  El motivo devuelto prioriza: encolado > registrado > aprobado (el más
  restrictivo/informativo primero).

- **R2** (ubicuo). El sistema debe considerar congelado un documento cuando
  `approved=true` O cuando alguna de sus líneas —activa o en papelera—
  tiene `sigrid_estado` en {`encolado`, `registrado`} (las ediciones de
  cabecera propagan fecha/obra a TODAS las líneas del documento).

## Rechazo en el servidor (la UI sola es papel mojado)

- **R3**. SI llega `PATCH /api/registros/{id}` (horas/tipo),
  `PATCH /api/registros/{id}/hora` o `PATCH /api/registros/{id}/partida`
  sobre una línea congelada, ENTONCES el sistema debe responder **409**
  con `{ok: false, congelado: true, error: <motivo>}` y no persistir
  ningún cambio.
- **R4**. SI llega `POST /api/registro/{id}/delete` (mover a papelera)
  sobre una línea congelada, ENTONCES el sistema debe responder 409 y la
  línea debe seguir activa (una línea registrada que desaparece del portal
  pero sigue en Sigrid es una desincronización silenciosa).
- **R5**. SI llega `POST /api/registros/{id}/extra` (crear línea extra)
  clonando una línea de un documento aprobado, ENTONCES el sistema debe
  responder 409 y no crear la línea (un parte aprobado no cambia de
  contenido, tampoco por adición).
- **R6**. SI llega `PATCH /api/partes/{id}/fecha` o
  `PATCH /api/partes/{id}/obra` sobre un documento congelado (R2),
  ENTONCES el sistema debe responder 409 sin tocar ni el documento ni
  ninguna de sus líneas (ni re-casar partidas).
- **R7**. SI llega `POST /documents/{id}/delete` (papelera) sobre un
  documento congelado, ENTONCES el sistema debe NO borrarlo y redirigir
  con un mensaje que incluya el motivo (es un flujo de formulario, no
  JSON).
- **R8**. CUANDO una conciliación o reasignación de empleado
  (`/api/conciliacion/confirmar`, `/api/empleado/reasignar` en sus cuatro
  variantes) alcanza líneas congeladas, el sistema debe excluirlas de la
  actualización, actualizar solo las libres y devolver en la respuesta el
  número de excluidas (`congeladas`).
- **R9**. CUANDO `POST /api/undo` deshace una acción cuyo snapshot toca
  líneas o documentos HOY congelados, el sistema debe omitir esos
  snapshots (no mutarlos), aplicar el resto y devolver cuántos omitió.
- **R10**. SI llega `POST /documents/{id}/unapprove` con alguna línea
  activa en `sigrid_estado='encolado'`, ENTONCES el sistema debe rechazar
  la desaprobación (el documento sigue aprobado) e informar del motivo:
  la petición está en vuelo y editar mientras sv5 procesa produce carrera.
- **R11**. CUANDO se desaprueba un documento sin líneas en vuelo, el
  sistema debe dejar editables sus líneas NO registradas Y mantener
  congeladas las líneas con `sigrid_estado='registrado'`: la desaprobación
  quita la capa «aprobado», nunca la capa «vive en Sigrid» (el registro en
  Sigrid NO se borra desde el portal; el parte `PT<AA>/NNNNN` sigue
  existiendo).
- **R12**. SI un hard-delete (`POST /api/registro/{id}/hard-delete`,
  `POST /api/documento/{id}/hard-delete`) alcanza una línea con
  `sigrid_estado='registrado'`, ENTONCES el sistema debe responder 409 sin
  borrar nada; y CUANDO `POST /api/papelera/vaciar` alcanza esas líneas
  (o documentos que las contienen), debe omitirlas y devolver el recuento
  de omitidas. Motivo: `sigrid_hmores_ide`/`sigrid_parte_cod` son la única
  referencia local a la línea escrita en Sigrid.
- **R13**. CUANDO un borrado masivo (`POST /api/obra/{key}/delete`,
  `POST /api/trabajador/{key}/delete`) alcanza documentos o líneas
  congelados, el sistema debe omitirlos, borrar el resto y devolver el
  recuento de omitidos (`congelados`) para que la UI lo muestre.

## Reflejo en la interfaz

- **R14**. El sistema debe marcar en las vistas de líneas (obra_detail,
  trabajador_detail, parte_detail) cada línea congelada: inputs de horas,
  fecha, trabajador, código de hora y partida deshabilitados, aspa de
  borrado oculta, y un candado (🔒) con tooltip que explique el motivo. El
  flag y el motivo viajan del servidor (calculados con la MISMA función de
  R1), no se recalculan en JS.
- **R15**. El sistema debe marcar como solo-lectura, en el popup de
  edición de celda de la matriz (dblclick), las líneas congeladas (flag
  `c` en el JSON `regs` de la celda); si todas lo están, el popup no
  ofrece guardado ni creación de extra.
- **R16**. CUANDO el servidor responde 409 de congelación a una edición,
  el front debe mostrar el motivo recibido (no un «✗ Error» genérico).
- **R17**. MIENTRAS un documento está aprobado, la vista `parte_detail`
  debe deshabilitar los editores de fecha y obra, las horas y códigos de
  sus líneas y el botón «+ Añadir línea», y mostrar un aviso con la vía de
  desaprobación («Marcar pendiente»).

## No regresión

- **R18**. El sistema debe mantener intacto el flujo de aprobación y
  registro (preflight, `/api/aprobar/ejecutar`, `/api/aprobar/encolar`,
  botones Aprobar/↻/Revisar por línea y «Aprobar todo»): la congelación
  bloquea EDICIONES, nunca el camino por el que las líneas llegan a
  Sigrid ni los reintentos de `omitido`/`error`/`conflicto`. Las suites
  existentes de F-002 y F-003 siguen en verde.

Regla de oro: cada R tiene al menos un test `test_f004_rN_*` en
`services/partes-front/tests/`, sin red ni BBDD (SQLite en memoria,
`Settings(_env_file=None)`, patrón de las suites F-002/F-003). R14/R15/R17
se verifican sobre el HTML renderizado por `TestClient`; el comportamiento
JS de R15/R16 se valida con `node --check` + verificación manual del humano
(no hay arnés de tests JS en el proyecto).
