# F-023 · Exploración de Sigrid (solo lectura, 2026-09-30)

Autor: spec-author. Datos **agregados**: sin DNIs, nombres ni identificadores
de personas. Todas las consultas son `SELECT` por `POST /api/sql/read` de
sigrid-api, usando el cliente de lectura de sv3 con su config local.

## Cómo se consultó

- Cliente: `SigridApiClient._post_sql_read` de sv3 (`services/partes-persistencia`),
  con un script de sondeo fuera del repo (scratchpad).
- **Base**: `ruesma`. Se intentó primero `ruesma_rep` como pedía el encargo y
  **no sirve**: responde `42S02 El nombre de objeto 'emp' no es válido` (lo mismo
  con `res` y `obr`). `ruesma_rep` es la base documental y no tiene estas
  tablas. sv3 en producción ya lee de `ruesma` por esta misma ruta de solo
  lectura, así que no se abrió ningún acceso nuevo.
- Fecha de referencia «hoy» = 20260930.

## 1. Qué marca la baja y cómo se codifica

| Campo | Qué es | Uso real |
|---|---|---|
| `con.fecbaj` del **recurso** | «Dar de baja concepto» (entero `YYYYMMDD`, `0` = sin baja; NULL no aparece) | 1.723 de 2.622 recursos con fecha, 899 a `0`. **Limpieza masiva**: 804 recursos dados de baja entre el 06-08 y el 10-08-2026 (552 nunca tuvieron líneas y solo 3 tenían líneas en 2026) |
| `con.fecbaj` del **empleado** | el mismo campo en la ficha `emp` | Solo 52 de 1.355 fichas. Siempre que el empleado está de baja, su recurso también (34/34) |
| `emp.fecbaj` / `emp.fecalt` | datos laborales de la ficha | 781 fichas con `emp.fecbaj`, 778 de ellas con `con.fecbaj = 0`. **No es fiable como baja**: 22 empleados tienen líneas en 2026 **posteriores** a su `emp.fecbaj` |
| `emphis` | histórico laboral (1.633 filas, 1.017 empleados, última `20260601`) | no se usa en el casado |

Líneas de 2026 (`hmores`, 29.701): solo **20** caen después de la `con.fecbaj`
de su recurso y **0** el mismo día de la baja. Con `emp.fecbaj` serían 38.
Tampoco hay ninguna `con.fecbaj` futura hoy.

`emp.reside` apunta a un recurso **de baja** en 507 fichas de empleado de alta:
el camino actual de sv3 (`empleado_reside` primero) puede devolver un recurso
de baja.

**Conclusión**: «de alta a la fecha D» = `con.fecbaj` NULL, 0 o `> D`, sobre el
recurso (y sobre la ficha de empleado). Es la regla que ya aplica sv4 (`> hoy`).

## 2. Empresas

- `con.emp` es la empresa (numeración de `auxemp.numemp`, 39 empresas, todas
  sin baja). Las fichas se reparten en 19 empresas (1: 859, 28: 288…).
- **Solo dos empresas con actividad en 2026**: la **1** (50 obras, 24.608
  líneas) y la **28** (23 obras, 5.093 líneas). Desde julio: 43 y 14 obras.
- **Recurso y obra comparten siempre empresa**: en las 29.701 líneas de 2026,
  `con.emp` del recurso = `con.emp` de la obra en el 100 %.
- **Cabecera del parte = empresa de la obra**: 323 partes `hmo` de 2026 con
  (1,1) y 118 con (28,28); ninguno cruzado. El único parte escrito por sv5
  (synckey `partes:`) es de la empresa 1.
- `res.conide` → `emp`: misma empresa en 825/825.
- Obras: ninguna de las 922 tiene `con.fecbaj`; la baja no sirve para
  descartar obras.

## 3. DNIs en varias empresas

- 83 DNIs tienen ficha `emp` en más de una empresa (32 en 2, 50 en 3, 1 en 4).
  11 están en la 1 y en la 28 a la vez.
- Con `con.fecbaj` del empleado siguen siendo 83 «de alta» en varias: **el
  filtro de alta del empleado no desempata**.
- Contando **recursos de alta**: 57 no tienen ninguno, 19 tienen en una sola
  empresa y **7 en dos**.
- Hay 2 DNIs con dos fichas de alta en la **misma** empresa, y 1 DNI con dos
  recursos de alta en la misma empresa.
- Recursos con líneas en 2026 cuyo DNI tiene **otro recurso de alta en otra
  empresa**: 9 (en obras de la 1) + 1 (en obras de la 28). En la misma
  empresa: 3.

## 4. Hallazgo que cambia el alcance: códigos de obra repetidos

- **58 códigos de obra existen en más de una empresa** (134 obras). Todos los
  repetidos son entre empresas distintas; 42 de ellos entre la 1 y la 28.
- **22 códigos tienen las dos obras activas en 2026** (una en la 1 y otra en
  la 28); 13 de esos pares se llaman igual. En ninguno de los 22 pares
  trabaja la misma persona en las dos.
- En 41 de 42 pares (1, 28) la obra de la 28 es la más nueva (`ide` mayor).
- `fetch_obras` (sv3 y sv4) **deduplica por código y se queda con la primera
  fila**: hoy un parte de una obra de la 28 puede casarse con su gemela de la
  1, y en el portal la gemela de la 28 **ni siquiera aparece** en el combo.

**Consecuencia**: el código leído del papel **no determina** la empresa en esos
22 códigos. La empresa hay que deducirla también de los trabajadores del parte.

## 5. Recursos sin empleado enlazado

- 609 recursos de alta sin `conide`; 401 de ellos con líneas desde agosto de
  2026. De esos 401: 383 sin `cif`, 16 con `cif` que no está en `emp` y 2 con
  `cif` presente en `emp`. Son recursos genéricos o externos que el casado por
  DNI no puede alcanzar de todas formas.
- Recursos con empleado enlazado: `cif` = `emp.dni` en 597, vacío en 218,
  distinto en 10.

## 6. sv5: el correlativo del parte es por empresa

- `PT26/…` de la empresa 1: 00001–00338 (324 conceptos). Empresa 28:
  00001–00121 (120). **115 códigos se repiten entre las dos**.
- `siguiente_cod_pt` toma hoy `MAX(cod)` de **todas** las empresas, y el
  `INSERT INTO hmo … FROM con WHERE cod = ? AND tip = ?` no filtra por
  empresa: con un correlativo por empresa ese `SELECT` devolvería **dos**
  cabeceras.

## 7. Límite de filas

Sin filtro de empresa, `emp` son 1.355 filas y `res` 2.622. La instancia `dev`
de sigrid-api admite hasta 500.000 y los clientes piden 10.000, así que no se
recorta. Pero ningún cliente mira `truncated`: si algún día se recorta, el
maestro llega incompleto **sin error**.

## Qué no se pudo medir aquí

El impacto en la base `partes` (cuántas líneas pendientes hay hoy en obras de
la 28 o casadas con la gemela equivocada) exige PostgreSQL, que no entraba en
este encargo: queda como verificación manual M1 en
`specs/F-023-recurso-alta-empresa/design.md` §9.
