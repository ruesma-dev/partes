<!-- specs/F-039-nombre-empresa-en-combos/requirements.md -->
# F-039 · Portal: nombre de la empresa en combos y Conciliar — Requisitos

**Servicio tocado: solo sv4** (`services/partes-front/`). Sin schema, sin
SQL, sin llamadas nuevas a Sigrid. Rigor **estándar**. Alcance mínimo
(incidencia del humano, 2026-10-08).

## Contexto

En Conciliar, la búsqueda manual de recursos pinta «MO/0266 · … · empresa 1»
y «… · empresa 28». Lo hace `empresaSufijo(x)` de `static/app.js`, que usan
también los combos de obra (`obraLabel`) y de trabajador (`recLabel`) de
«+ Nuevo parte» y del modal «+ Añadir línea». El portal ya sabe los nombres
cortos (`application/services/empresas.py`, F-033), pero el JS no los recibe.

## Glosario

- **Nombre de la empresa N**: `nombre_empresa(N)` de
  `application/services/empresas.py` — `1 → «Ruesma»`, `28 → «Porsan»`, otro
  número → «Empresa N». Es la **única fuente** de nombres.
- **Item con empresa**: elemento de `items` de una respuesta JSON del portal
  que lleva el campo `empresa` (número de `con.emp`, o `null`).

## Requisitos

- **R1.** `GET /api/sigrid/obras` debe incluir en cada item
  `empresa_nombre`: el nombre de su `empresa`, o `""` si `empresa` es `null`.
- **R2.** `GET /api/sigrid/recursos` debe incluir `empresa_nombre` en cada
  item, con la regla de R1.
- **R3.** `GET /api/conciliacion/buscar` debe incluir `empresa_nombre` en
  cada item, con la regla de R1.
- **R4.** `GET /api/sigrid/empleados` debe incluir `empresa_nombre` en cada
  item, con la regla de R1 (hoy nadie pinta su empresa; se añade para que
  todo item con empresa lleve su nombre).
- **R5.** SI el número de empresa no tiene nombre en `NOMBRES_EMPRESA`,
  ENTONCES `empresa_nombre` debe ser «Empresa N».
- **R6.** CUANDO un item trae `empresa` no nula y `empresa_nombre` no vacío,
  `empresaSufijo` debe devolver « · » seguido de `empresa_nombre`
  (p. ej. « · Porsan»).
- **R7.** SI un item trae `empresa` no nula y le falta `empresa_nombre` (o
  viene vacío), ENTONCES `empresaSufijo` debe devolver « · Empresa N».
- **R8.** SI un item no trae empresa (`null` o ausente), ENTONCES
  `empresaSufijo` debe devolver `""`.
- **R9.** El combo de obra (`obraLabel`), el de trabajador (`recLabel`) y
  los resultados de la búsqueda manual de Conciliar deben componer su texto
  con `empresaSufijo`; `app.js` no debe contener el literal « · empresa ».
- **R10.** `static/app.js` no debe contener los nombres de empresa
  («Ruesma», «Porsan»): los recibe del servidor.
- **R11.** Los candidatos de Conciliar (`_candidato_con_empresa`) deben
  seguir mostrando `empresa_nombre` como hoy, calculado con la misma función
  que R1–R4.
- **R12.** El sistema no debe cambiar ningún otro campo de esas respuestas
  ni el filtrado por empresa (`deLaEmpresaDe`, `fijarEmpresa`,
  `data-empresa`); la suite de sv4 sigue en verde sin tocar tests ajenos,
  con UNA excepción (enmienda del humano, 2026-10-08, opción A): los dos
  tests que comprueban las claves EXACTAS de esas respuestas,
  `test_f015_r26_sin_fecha_las_claves_son_las_de_siempre` (empleados, R4) y
  `test_f023_r40_endpoint_obras_anade_la_empresa` (obras, R1), añaden
  `empresa_nombre` a lo que esperan, como hizo F-023 con `empresa`; nada
  más cambia en ellos. La spec original no los previó.

## Fuera de alcance

Selectores de empresa (ya usan `EMPRESAS`, F-035), columna Empresa de
`/obras` (F-033), `data-obra-label` de los detalles, `admin_jornadas`,
`docs/ARCHITECTURE.md`, sv1/sv2/sv3/sv5.

## Trazabilidad

Cada R tiene un test `test_f039_rN_...` en
`services/partes-front/tests/test_f039_nombre_empresa.py` (design §4).
