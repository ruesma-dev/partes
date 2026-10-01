# F-021 · Exploración de Sigrid: cuenta analítica (solo lectura, 2026-10-01)

Autor: spec-author. Datos **agregados**: sin DNIs, nombres ni identificadores
de personas. Solo `SELECT` por `POST /api/sql/read` de sigrid-api, base
`ruesma`, con el cliente de lectura de sv3 (`SigridApiClient._post_sql_read`)
y su config local, desde un script en el scratchpad (fuera del repo; el
`.env` no se abrió ni se imprimió). Ninguna escritura.

## 0. Diccionario (`azure-apps/sigrid_tablas.md`)

- `caa` «Cuentas analíticas» (propiedades de `con`, `con.tip = 19`):
  `cenide` (centro de coste), `padide` (grupo `cag`), `niv`, `prpide`…
- `caaide` («Cuenta analítica», índice a `caa`) existe en **`hmores`**
  (con índice `cencaa` = `cenide`+`caaide`), `hmo`, **`res`**, `res.caaconide`
  (contrapartida), **`reshor`** (recurso × tipo de hora), `emp`,
  `obrparpar` (partida) y muchas de compras/ventas.
- `caacod` («Código Cue analítica», texto 24) es un **código** suelto en
  tablas auxiliares, entre ellas `auxhor` (tipos de hora). `modana` («Modo
  solo analítica») es de `auxobrcin` (tipos de costes indirectos de obra):
  no aplica a las líneas de horas.
- `hmores.cuaide` (cuenta financiera) también existe.

## 1. Forma de la cuenta

184.234 cuentas `caa`, todas con código `<centro>.<subcuenta>`
(p. ej. `00000.CIMO08`): el prefijo es **siempre** el `con.cod` de su centro
(`caa.cenide`) y el par (centro, subcuenta) es **único** (0 duplicados). El
código se repite entre empresas (14.063 códigos), nunca dentro de una.
`00000` es un centro «plantilla» (existe en varias empresas). Solo 1 cuenta
tiene `con.fecbaj`. Media 231 cuentas por centro, máximo 768.

## 2. Pregunta 1 · la cuenta en la ficha del recurso

- **`res.caaide` está a 0 en TODOS** los recursos con líneas en 2026 (724
  de la empresa 1, 27 de la 28). No es la fuente.
- La cuenta «del recurso» está **por tipo de hora** en `reshor.caaide`:
  3.208 de 8.977 filas `reshor`, todas apuntando a una cuenta de **la misma
  empresa** que el recurso, casi todas del centro plantilla (`00000.*`:
  3.155; resto `0003`, `0005`, `0165`, `GG`). 27 subcuentas distintas
  (25 en la empresa 1). 2.003 de 2.009 recursos usan una sola subcuenta.
- Recursos **de alta** con líneas en 2026 que tienen alguna cuenta en
  `reshor`: **empresa 1: 711 de 713; empresa 28: 0 de 27** (ninguna fila
  `reshor` de la 28 tiene cuenta).
- Otras: `emp.caaide` 900/1.355; `obrparpar.caaide` 202.083/395.185;
  `hmo.caaide` 0/6.889; `auxhor.caacod` 44/60 tipos (códigos plantilla).

## 3. Pregunta 2 · la cuenta en la línea tecleada a mano

Campo: **`hmores.caaide`**. Líneas de 2026: 29.721 (lectura de la mañana);
24.339 con cuenta, **todas de la empresa 1**. Por mes, empresa 1: 98,6–
100 % con cuenta (septiembre 1.999/1.999); **empresa 28: 0 %** todos los
meses. `hmores.cuaide`: 0 líneas.

La cuenta de la línea es **siempre** del centro de la línea (`caa.cenide =
hmores.cenide`, 24.339/24.339) y `hmores.cenide = obr.cenide` en 29.719/
29.721. Nunca es el `ide` de la plantilla de `reshor` (0 coincidencias de
`ide`); coincide la **subcuenta**.

Regla medida (empresa 1, 24.625 líneas con recurso):

| Origen de la subcuenta | Igual | Ambas vacías | Distinta | Solo la regla | Solo el humano |
|---|---|---|---|---|---|
| `reshor` del tipo de hora de la línea | 23.123 | 279 | 3 | 0 | 0 |
| `reshor` del tipo por defecto (`res.horide`) | 1.132 | 2 | 53 | 3 | 0 |
| ninguna | — | 2 | — | — | 28 |

**Coincidencia total: 99,64 % en la empresa 1 (24.538/24.625) y 100 % en la
28 (5.093 vacías y vacías).** El respaldo por tipo por defecto explica las
incidencias `CI*` (sus filas `reshor` no tienen cuenta y la línea lleva la
de la hora por defecto del recurso: 1.132/1.213). Las 279 «ambas vacías»
con plantilla: la obra no tiene esa subcuenta (15 pares centro-subcuenta,
2 obras) y el humano deja la línea sin cuenta.

## 4. Pregunta 3 · líneas escritas por sv5

**0** líneas `hmores` y 0 cabeceras `hmo` con `synckey LIKE 'partes:%'`; 0
con `tex LIKE '%PRUEBA-IA%'`. Lo escrito en pruebas se limpió. Hoy no hay
nada que reescribir; sv5 escribe `caaide = 0` fijo (`stmt_insert_linea`).

## 5. Pregunta 4 · otras fuentes que la sobrescriban

- **Partida**: en 2.191 líneas la cuenta de la partida existe y es distinta
  de la de la línea; en 2.188 manda la del recurso. La partida no manda.
- **Obra/centro**: solo aporta el prefijo (el centro), no la subcuenta.
- **Empleado** (`emp.caaide`): 0 coincidencias de subcuenta.
- **Tipo de hora** (`auxhor.caacod`): coincide en 22.885, pero es la misma
  plantilla que `reshor` y no explica las incidencias; no aporta.
- **Empresa**: la cuenta es siempre de la empresa de la obra (24.366/24.366).

## 6. Obra de pruebas `0404` (empresa 1)

Tiene 269 cuentas y **24 de las 25 subcuentas** de la empresa 1: sirve para
verificar en modo pruebas, y la que falta sirve para provocar el aviso.

## Conclusión

Origen = `reshor.caaide` del recurso para el tipo de hora de la línea (si
no, el de su tipo por defecto `res.horide`); se toma su **subcuenta**.
Destino = `hmores.caaide` con la cuenta del **centro de la obra destino** y
esa subcuenta. Sin subcuenta o sin cuenta en la obra: 0, como hace hoy el
humano. Porsan (28) no usa cuenta analítica en horas.
