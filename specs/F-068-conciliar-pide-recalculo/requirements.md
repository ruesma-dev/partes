<!-- specs/F-068-conciliar-pide-recalculo/requirements.md -->
# F-068 · Hotfix: casar un trabajador en Conciliar pide a sv3 el recálculo de extras — requisitos

> **Solo sv4** (`services/partes-front`): es quien casa y quien ya pide recálculos (F-042,
> F-043, F-049). sv3 no cambia: el `motivo` del mensaje es solo traza y su pasada es la de
> siempre. Sin esquema, sin sv5, sin Sigrid. Rigor **crítico**. Diseño en `design.md`;
> decisiones abiertas D1–D6 en su §9, **pendientes del humano**. Requisitos marcados
> «DONDE D*n* = b» solo se implementan si el humano elige esa opción.

## El hueco (dev `7e5f600`, verificado en el código)

- `POST /api/conciliacion/confirmar` (`app.py`, `conciliacion_confirmar`) hace
  `backfill_empleado` + `upsert_empleado_alias` y responde. **No pide recálculo**, a diferencia
  de la fecha (`_pedir_recalculo_seguido`, F-042/F-043), la celda y su deshacer y «Traer de
  Sigrid» (`_pedir_recalculo_compartido`, F-049/F-052) y el reajuste (F-046).
- Una línea sin casar no tiene jornada: sv3 no la parte. Al casarla queda con todas sus horas
  como ordinarias **y aprobable** hasta la siguiente pasada completa de sv3, que llega solo con
  otro parte nuevo. Caso real: obra 0694, 04/11/2026, 8,5 h que debían ser 8 HLOF + 0,5 HEOF.
- `POST /api/empleado/reasignar` (cuatro formas: `reassign_empleado_by_*`) y deshacer una
  entrada `empleado` tienen el mismo hueco (D3, D4).

## Glosario

- **Partes del casado**: los `document_id` de las líneas que el casado **escribió** (no
  congeladas), sin repetir, en orden de `id` de línea. Las congeladas omitidas no aportan parte.
- **Pedido compartido**, **en espera**, estados `pedido` / `fallo` / `sin_cola`: los de F-042,
  F-043 y F-049 (`_pedir_recalculo_compartido`, `seguimiento_recalculo.py`).

## Conciliar (`POST /api/conciliacion/confirmar`)

- **R1.** CUANDO un casado escribe al menos una línea, sv4 debe pedir UN recálculo con pedido
  compartido sobre los partes del casado, con motivo `casado_conciliacion`, **después** del
  commit del casado y del alias, y con el `document_id` del mensaje = el primero (D1-a, D2-a).
- **R2.** CUANDO el casado no escribe ninguna línea (`updated == 0`, también si todas eran
  congeladas), sv4 no debe marcar ni publicar nada y `recalculo` debe ser `null`.
- **R3.** La respuesta 200 debe conservar sus claves (`ok`, `updated`, `alias_ok`, `congeladas`,
  `empleado`) y añadir `recalculo` (`pedido` | `fallo` | `sin_cola` | `null`) y
  `partes_recalculo` (número de partes del casado; 0 si no hubo pedido).
- **R4.** Un parte con líneas casadas y líneas congeladas omitidas debe recibir el pedido; un
  parte cuyas líneas candidatas estaban todas congeladas no debe recibirlo.
- **R5.** SI publicar falla, ENTONCES el pedido debe quitarse donde siga siendo ese (F-049 R39) y
  la respuesta debe ser 200 con `recalculo: "fallo"`, el casado y el alias guardados.
- **R6.** SI marcar o anular el pedido lanza, ENTONCES solo debe quedar un WARNING (F-043 R14) y
  la respuesta sigue siendo 200 con el casado guardado.
- **R7.** El casado nunca debe deshacerse ni responder 4xx/5xx por causa del recálculo: lo único
  que puede dar error es lo de hoy (cuerpo inválido 400, trabajador 404, `backfill` 500).
- **R8.** CUANDO se pide el recálculo, sv4 debe dejar un INFO `[conciliacion] casado` con
  `updated`, `congeladas`, los ids de los partes, el pedido y el estado; sin nombres, DNI ni
  nombre leído (F-049 R24).
- **R9.** MIENTRAS sv3 no marque terminado el pedido (o venza a los 10 min), los partes del
  casado deben estar en espera como los de una celda: ediciones con 409 de `RecalculandoError`
  y marca «recalculando» en las vistas (F-043 R38). Caracteriza lo existente.
- **R10.** CUANDO un parte del casado ya estaba en espera con otro pedido, el pedido nuevo debe
  sustituirlo (lo que hace hoy `marcar_recalculo_pedido_compartido`) y el parte sigue en espera
  hasta que sv3 termine la pasada del pedido nuevo.

## El 422 de F-069 tras un casado

- **R11.** El pedido de recálculo en sí nunca devuelve 422: es una publicación en cola sin
  respuesta de sv3. El 422 posible es el de **aprobar** con ids de una página cargada antes de
  la pasada (`_validar_ambito`, F-022 y F-069 R20: `fuera_de_ambito`, `inexistentes`).
- **R12.** SI tras un casado con recálculo pedido una aprobación responde 422 por `fuera_de_ambito`
  o `inexistentes`, ENTONCES el casado debe seguir intacto (empleado, alias y pedido) y la
  aprobación no debe escribir nada (`approved`, `sigrid_estado`, sv5). (capa: integración)
- **R13.** El texto de ese 422 no cambia (F-069 R20); el portal sigue enseñando su `error`.

## Portal (Conciliar, `static/app.js`)

- **R14.** CUANDO `recalculo` es `pedido`, la tarjeta casada debe añadir «· recalculando extras
  de N parte(s) (1–2 min)», con N = `partes_recalculo`.
- **R15.** CUANDO `recalculo` es `fallo`, la tarjeta debe decir, en estilo de error y sin
  borrarse sola: «Casado guardado, pero no se pudo pedir el recálculo de extras: se hará en la
  siguiente pasada. No apruebes esos partes hasta ver sus extras.» (D6-a).
- **R16.** CUANDO `recalculo` es `sin_cola`, debe añadir «(sin recálculo automático)»; con
  `null` o sin la clave (sv4 anterior), lo de hoy.

## Reasignar (DONDE D3 = b)

- **R17.** CUANDO una de las cuatro formas de `POST /api/empleado/reasignar` escribe al menos una
  línea, sv4 debe pedir el recálculo como en R1–R7 con motivo `reasignacion_trabajador` y añadir
  `recalculo` y `partes_recalculo` a su respuesta 200.
- **R18.** Tras reasignar el portal recarga como hoy (la recarga ya pinta el parte en espera);
  CUANDO `recalculo` es `fallo`, debe avisar antes con un `alert` con el texto de R15.

## Deshacer (DONDE D4 = b)

- **R19.** CUANDO se deshace una entrada `empleado` (casar o reasignar), `undo_last` debe devolver
  en `document_ids` los partes de las líneas restauradas (no las omitidas por congelación), y
  `/api/undo` debe pedir UN recálculo compartido con motivo `deshacer_trabajador` y poner
  `recalculo` en la respuesta. Las demás acciones no cambian. El JS de deshacer ya avisa del
  `fallo` (F-042 R11) y no cambia.

## Contrato y lo que no cambia

- **R20.** Los motivos nuevos deben ser constantes de `recalculo_publisher.py` y sv3 debe
  clasificarlos como recálculo (`tests/test_f042_contrato_recalculo.py`, parametrizado con ellos).
- **R21.** Siguen igual: sv3, sv5, `orm_models.py`, `congelacion.py`, `esta_congelado`, los
  gemelos de `CLAUDE.md`, `_pedir_recalculo_compartido`, `_pedir_recalculo_seguido`,
  `marcar_/anular_recalculo_pedido*`, `_exigir_sin_recalculo`, `approve_document`,
  `lineas_para_registro` y `_validar_ambito`. Ningún test existente cambia de expectativa,
  salvo el guardián de F-017 (`test_f017_todos_los_puntos_de_escritura_usan_el_helper`), que
  pasa de 21 a 23 llamadas a `_actor(request)`: Conciliar y reasignar firman `solicitado_por`.
  *Enmienda por decisión del humano 2026-11-13, guardián F-017 21→23.* Y el guardián de F-047
  (`test_f047_r23_ninguna_funcion_nueva_y_una_sola_variable`) descuenta la función nueva de
  F-068 en una tupla `F068_CONCILIAR` como hace con `F052_PANEL` (el resto sigue en 302).
  *Enmienda por decisión del humano 2026-11-15.*
- **R22.** Los valores de retorno de `backfill_empleado` y `reassign_empleado_by_*` no cambian
  (los afirman tests de F-004, F-023, F-030 y F-035); los partes salen por un colector opcional.

## Ejemplos (P = pedido nuevo; D1, D2 partes; «libre» = no congelada)

| Caso | Líneas con el nombre leído | Resultado |
|---|---|---|
| E1 | 1 en D1 (libre) | `updated` 1, P en D1, mensaje D1, `recalculo` `pedido`, N = 1 |
| E2 | 2 en D1, 1 en D2 (libres) | P en D1 y D2 (orden por id de línea), UN mensaje |
| E3 | 1 en D1 libre, 1 en D2 aprobada | P solo en D1, `congeladas` 1 |
| E4 | solo 1 en D2 aprobada | `updated` 0, sin pedido, `recalculo` null |
| E5 | E1 con la cola caída | P quitado de D1, 200, `recalculo` `fallo`, casado guardado |
| E6 | E1 sin cola (local) | sin marca, 200, `recalculo` `sin_cola` |
| E7 | E1 y luego aprobar con ids viejos de los que uno ya no existe | 422 `inexistentes`; casado intacto |

## Verificación manual

- **M1 (humano, tras desplegar sv4; lo pide el humano)**: en el siguiente casado real de
  Conciliar (o en la obra de pruebas 0404 con un parte de pruebas), comprobar que la tarjeta dice
  «recalculando extras», que la vista de obra pinta el parte en espera, que en ~1–2 min la línea
  queda partida en ordinaria + extra según su jornada y que el log de sv4 trae
  `[conciliacion] casado ... recalculo=pedido`. No se aprueba nada ni se toca Sigrid.
