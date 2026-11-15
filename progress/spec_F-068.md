# Spec F-068 · Hotfix: casar un trabajador en Conciliar pide a sv3 el recálculo de extras

Fecha: 2026-11-13. Autor: spec-author. Rama `feature/F-068-conciliar-pide-recalculo` (desde `dev`
7e5f600), worktree `C:\Users\pgris\PycharmProjects\partes-wt-f068`. Prioridad 2, rigor crítico.
Estado en `harness/features.json`: `spec_ready` (BACKLOG.md regenerado).

## Ficheros

- `specs/F-068-conciliar-pide-recalculo/requirements.md` (122/150): R1-R22, E1-E7 y M1.
- `specs/F-068-conciliar-pide-recalculo/design.md` (185/250).
- `specs/F-068-conciliar-pide-recalculo/tasks.md`: T1-T16 (T10 solo con D3-b, T11 solo con D4-b).
- `python -m harness.tamano --feature F-068`: dentro de los topes.

## Qué propone, en corto

- **Servicio**: solo sv4. sv3 no cambia (no valida `motivo`; lo fija el test raíz de contrato
  ampliado). Sin esquema, sin sv5, sin gemelos; no toca `congelacion.py`, `esta_congelado` ni
  `orm_models.py`.
- `conciliacion_confirmar`, tras el commit del casado y del alias, pide **UN recálculo con pedido
  compartido** reutilizando `_pedir_recalculo_compartido` (el de la celda y de «Traer de
  Sigrid»), sobre los partes de las líneas casadas no congeladas, motivo `casado_conciliacion`.
- Los partes salen de `backfill_empleado` por un **colector opcional** (`documentos=`), sin
  cambiar su retorno `(updated, congeladas)` que afirman ~26 llamadas en tests anteriores.
- Respuesta: añade `recalculo` y `partes_recalculo`. El portal dice «recalculando extras de N
  parte(s)» o el aviso de `fallo`.
- **422 de F-069**: el recálculo no responde (es una cola), así que nunca da 422. El 422 posible
  es el de aprobar con ids viejos tras la pasada (`inexistentes`); no escribe nada y el casado ya
  está confirmado en otra transacción: no se pierde. Texto el de F-069, sin cambios; un test de
  integración lo fija (R12).
- **Solape con F-057**: ninguno funcional (F-057 es solo la celda y su deshacer); los dos dejan
  intacto `_pedir_recalculo_compartido`. Conflicto textual previsible en `undo_apply` /
  `undo_last` si D4-b: se conservan las dos ramas.
- `azure-apps/partes.md` lista los motivos del mensaje: se actualiza en T13 (regla de
  mantenimiento).

## Decisiones abiertas para el humano (tabla completa en design.md §9)

| Decisión | Recomendado |
|---|---|
| D1 · Qué partes reciben el pedido | (a) solo los de las líneas casadas (no las otras obras del día: la pasada es global) |
| D2 · Un pedido o uno por parte | (a) UN pedido compartido y UN mensaje |
| D3 · Reasignar trabajador también | (b) sí: mismo hueco y mismo riesgo |
| D4 · Deshacer casar/reasignar también | (b) sí, como deshacer fecha o celda |
| D5 · Aprobar durante la pasada | (b) como fecha y celda hoy (en espera pero aprobable) y alta de una feature aparte para estudiar bloquearlo; bloquearlo aquí exige esquema |
| D6 · Texto con `fallo` | (a) aviso fijo «se hará en la siguiente pasada; no apruebes esos partes hasta ver sus extras» |

## Notas para el líder

- El riesgo del hotfix (aprobar con 8,5 h ordinarias) baja de «hasta el siguiente parte nuevo»
  a la duración de la pasada, con el parte marcado en espera; no se cierra del todo sin D5-c.
- `backfill_empleado` no aplica `_exigir_sin_recalculo` y la spec no lo añade (R10, design §11).
- M1 es del humano tras desplegar sv4; el despliegue no necesita orden con sv3.
