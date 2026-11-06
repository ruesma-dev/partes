# F-066 · sv4 clasifica la hora extra por la regla «`HE` salvo `HENC`» — Requisitos

**Servicio**: solo **sv4** (`services/partes-front`). sv5 sigue con «prefijo `HE`» hasta
**F-067** («sv5: HENC no es hora extra»), que trae el guardián de gemelos (DA8). sv3 queda
fuera (LÍMITE DE SERVICIO, DA7). Esquema, colas y contratos sv4↔sv5 no cambian. Rigor
**crítico** (DA9): `tipo_hora` decide qué hora escribe sv5 en Sigrid y en Sigrid no se borra.

**Origen**: hallazgo **H-M2-1b** de F-052 (M2, 2026-11-03), acordado con el humano el
2026-11-03 («me parece bien»): `auxhor.ext` no es fiable y el selector de código de hora
(`PATCH /api/registros/{id}/hora`) fija `tipo_hora` con él; elegir una `HE*` deja la línea
`normal` y sv5 (`reglas_registro.py`) escribiría una `HL`.
**Revisión 2026-11-06**: la M1 del líder (solo lectura, `design.md` §7) refuta «prefijo `HE` =
extra»: ningún código de `auxhor` tiene `ext = 1` y uno de los 7 `HE*`, **`HENC` «HORA
ENCARGADO», no es extra**. El humano decidió la opción **A** («a», 2026-11-06): extra = código
que empieza por `HE` **excepto `HENC`**, con la excepción en un solo sitio por servicio, y
F-066 la aplica en **todo sv4**, incluido el `es_hora_extra` de F-052. La M1 también mostró
que no hay líneas mal clasificadas que reparar (la DA6 original se retira, `design.md` §8).

## Glosario

- **Regla de la hora extra**: con el código sin espacios a los lados y en mayúsculas, es extra
  si empieza por `HE` y no es exactamente `HENC`. Sin código (None, vacío o espacios) la clase
  **no se sabe**.
- **`clase_hora.py`**: el único sitio de sv4 donde vive la regla
  (`application/services/clase_hora.py`): prefijo, lista de excepciones y fragmento SQL.
- **`auxhor.ext`**: flag de Sigrid, a 0 en todos los códigos (M1). Se sigue guardando en
  `parte_registros.hora_ext` como dato **informativo**; no decide nada nuevo.

## Requisitos

### La regla, en un único sitio de sv4

- **R1.** `es_hora_extra(codigo)` de `clase_hora.py` debe devolver `True` para `"HECAP"`,
  `"HEGR"`, `" heof "`, `"HEPE"`, `"HEAA"`, `"HEOM"`; `False` para `"HENC"`, `" henc "`,
  `"HL01"`, `"MENC"`, `"CI01"`, `"H"`, `"XHE"`; `None` para `None`, `""`, `"   "`.
- **R2.** `clase_hora.py` debe declarar el prefijo (`HE`) y las excepciones (`("HENC",)`) como
  constantes una sola vez; `es_hora_extra`, `tipo_hora_de_codigo` y `condicion_sql_extra` deben
  derivarse de ellas (cambiar la lista cambia las tres; test).
- **R3.** `condicion_sql_extra(columna)` debe devolver un predicado T-SQL equivalente a R1 sobre
  la columna dada (`UPPER(LTRIM(RTRIM(col))) LIKE 'HE%' AND ... NOT IN ('HENC')`), sin
  parámetros del usuario (solo constantes del módulo).
- **R4.** `application/services/sincronizacion.py` debe seguir ofreciendo `es_hora_extra` con el
  mismo nombre, importado de `clase_hora` sin copia: una línea `HENC` de Sigrid cuenta como
  `ordinaria` al comparar (F-052 R9), y los tests de F-052 se ajustan solo donde usen `HENC`.
- **R5.** Ningún fichero Python de sv4 fuera de `clase_hora.py` debe implementar la regla
  (`startswith("HE")` ni `LIKE 'HE%'` literal) (test de fuente).

### Guardar el código de hora (`PATCH /api/registros/{id}/hora`)

- **R6.** CUANDO se guarda en una línea que no es incidencia un código extra según R1, el
  sistema debe dejar `tipo_hora = "extra"`, aunque su `auxhor.ext` sea 0.
- **R7.** CUANDO se guarda en una línea que no es incidencia un código no extra según R1
  (`HENC`, `HL*`…), el sistema debe dejar `tipo_hora = "normal"`, aunque su `auxhor.ext` sea 1.
- **R8.** MIENTRAS la línea sea incidencia, el sistema no debe cambiar su `tipo_hora`.
- **R9.** SI la opción elegida no tiene código, ENTONCES el sistema debe guardar el resto de
  campos y no cambiar `tipo_hora` (DA3).
- **R10.** El sistema debe seguir guardando `hora_ide`, `hora_codigo`, `hora_descripcion`,
  `hora_ext` (= `auxhor.ext`), los dos precios y `hora_match_method = "manual"` como hoy, y
  registrar el deshacer `registro_hora` con el estado anterior.
- **R11.** CUANDO se deshace un cambio de código que movió `tipo_hora`, el sistema debe
  restaurar el `tipo_hora` anterior.
- **R12.** La respuesta del endpoint debe devolver `tipo_hora` por la regla (`"extra"` si
  `True`, `"normal"` en otro caso) y `hora_ext` con el valor de `auxhor.ext`.
- **R13.** El sistema debe mantener las guardas del endpoint: 503 sin Sigrid, 400 si el
  `hora_ide` no está en el catálogo, 404 sin registro, línea congelada (F-004) y recálculo en
  curso (F-043); los tests existentes siguen en verde.
- **R14.** CUANDO el usuario guarda el código en varias líneas a la vez (selección múltiple),
  cada una debe quedar con el `tipo_hora` de R6–R9.

### El desplegable (`GET /api/sigrid/tipos-hora` y `static/app.js`)

- **R15.** Cada elemento de `GET /api/sigrid/tipos-hora` debe ganar `extra` (booleano,
  `es_hora_extra(codigo) is True`) y conservar `ext` sin cambios (DA4).
- **R16.** `buildOptions` de `app.js` debe agrupar en «Horas extra» las opciones con
  `extra === true` y en «Horas ordinarias» el resto, sin leer `ext`: `HEOF` va a «extra» y
  `HENC` a «ordinarias». Conserva el orden relativo y la marca de la opción actual.
- **R17.** `app.js` no debe implementar la regla (ni `startsWith("HE")` ni `.ext`) en el
  desplegable: la clase llega del servidor (test de fuente).

### Los demás usos de la regla en sv4

- **R18.** `fetch_hora_extra_recurso` (la hora extra que usan «+ extra» y la celda de F-049)
  debe filtrar con `condicion_sql_extra`: un recurso con `HENC` y `HEOF` debe devolver `HEOF`
  (hoy, `ORDER BY auxhor.cod`, devuelve `HENC`).
- **R19.** `fetch_dnis_sin_extra` debe calcular `es_he` con `condicion_sql_extra`: un DNI cuyo
  único código `HE*` es `HENC` cuenta como **sin extra**.
- **R20.** `franquicia.extras_pendientes` (F-056) debe sumar solo las acciones cuyo
  `hora_codigo` es extra según R1 (`HENC` no suma); el resto de F-056 no cambia.

### Documentación y no regresión

- **R21.** `docs/ARCHITECTURE.md` semántica 3 debe recoger la regla («`HE` salvo `HENC`», en
  sv4 desde F-066 y en sv5 cuando se cierre F-067) y la M1 que la motiva.
- **R22.** El sistema no debe cambiar los disyuntivos `tipo_hora == "extra" or hora_ext == 1`
  de badges y totales (DA5).
- **R23.** Todos los tests de F-066 deben correr sin red ni BBDD (SQLite en memoria, clientes
  falsos que capturan el SQL, node para el JS).

## Verificaciones manuales

- **M1** — HECHA por el líder el 2026-11-06 (solo lectura), resultados en `design.md` §7.
- **M2** (humano, tras desplegar sv4): obra de pruebas 0404, línea ordinaria sin registrar:
  elegir `HEOF` (en «Horas extra») ⇒ badge extra al recargar; elegir `HENC` (en «Horas
  ordinarias») ⇒ normal; deshacer ⇒ vuelve. No se aprueba ni se envía a Sigrid.

## Decisiones abiertas

Tabla en `design.md` §8 (DA1–DA5, DA7–DA10; DA6 retirada). El humano las aprueba (PARADA 1).
