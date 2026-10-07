<!-- specs/F-033-columna-empresa/requirements.md -->
# F-033 · Portal: columna Empresa en el listado de obras — Requisitos

**Servicio tocado: solo sv4** (`services/partes-front/`). Sin schema, sin
llamadas a Sigrid, sin `app.js`. Rigor **estándar**. Versión mínima
(2026-10-07): el humano rechazó el alcance anterior.

## Contexto

En `/obras` la 0678 sale en dos filas idénticas: son dos fichas de Sigrid
(Ruesma, empresa 1; Porsan, empresa 28) con mismo código y nombre. El
listado ya las separa (una fila por `obra_key`); falta ver de qué empresa
es cada una.

## Glosario

- **Empresa de los partes de la fila**: los valores no nulos y distintos de
  `parte_documents.empresa` de los documentos activos de las líneas de la
  fila (F-023).
- **Empresa de un recurso**: los valores no nulos de
  `parte_documents.empresa` de los partes activos donde aparece una línea
  con ese `recurso_ide` (cualquier obra). Un recurso de Sigrid es de una
  sola empresa, así que es dato ya guardado en la BBDD `partes`.
- **Nombre**: `{1: "Ruesma", 28: "Porsan"}`; otro número N → «Empresa N».

## Requisitos

- **R1.** El listado de obras debe tener una columna «Empresa» justo
  después de «Obra», con su `<input class="col-filter">` en la fila de
  filtros (mismo número de celdas en las dos filas de cabecera).
- **R2.** La celda debe mostrar el nombre de la empresa de los partes de la
  fila; con varias, los nombres unidos por « / » en orden numérico.
- **R3.** CUANDO dos filas tienen el mismo código y nombre de obra y sus
  partes son de empresas distintas, el listado debe pintar dos filas, una
  con «Ruesma» y otra con «Porsan».
- **R4.** SI todos los partes de la fila tienen `empresa` NULL (anteriores a
  F-023), ENTONCES la celda debe mostrar la empresa de los recursos
  (`recurso_ide` no nulo) de sus líneas, con la misma regla de R2.
- **R5.** SI tampoco así hay empresa, ENTONCES la celda debe mostrar «—».
- **R6.** SI el número no es 1 ni 28, ENTONCES el nombre debe ser
  «Empresa N».
- **R7.** Las filas con mismo código y nombre deben salir ordenadas por el
  menor número de empresa (las de sin empresa detrás).
- **R8.** El sistema no debe cambiar `obra_key`, la agrupación, los
  totales, la búsqueda `search` ni ninguna otra vista; la suite de sv4
  sigue en verde sin tocar tests ajenos.

## Fuera de alcance

Detalle de obra, listado y detalle de parte, `data-label` del borrado,
catálogo de obras de Sigrid, `docs/ARCHITECTURE.md`.

## Trazabilidad

Cada R tiene un test `test_f033_rN_...` (design §4).
