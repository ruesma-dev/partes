# F-066 · sv4: hora extra por el prefijo `HE` y `HENC` excluido — Requisitos

**Servicio**: solo **sv4** (`services/partes-front`). sv3 y sv5 van en **F-067** («sv3 y sv5:
HENC excluido»), que trae el guardián de gemelos (DA8). Esquema, colas y contratos sv4↔sv5 no
cambian. Rigor **crítico** (DA9): `tipo_hora` decide qué hora escribe sv5 en Sigrid y en
Sigrid no se borra.

**Origen**: hallazgo **H-M2-1b** de F-052 (M2, 2026-11-03), acordado con el humano el
2026-11-03 («me parece bien»): `auxhor.ext` no es fiable y el selector de código de hora
(`PATCH /api/registros/{id}/hora`) fija `tipo_hora` con él; elegir una `HE*` deja la línea
`normal` y sv5 (`reglas_registro.py`) escribiría una `HL`.
**Revisión 2026-11-06** (`design.md` §7): la M1 del líder muestra que ningún `auxhor` tiene
`ext = 1` y que `HENC` («HORA ENCARGADO») empieza por `HE` sin ser extra. **Decisión del
humano** del 2026-11-06, que sustituye a la anterior («a»): «**HENC no debe ser tenido en
cuenta por la app**»; alcance aprobado con «ok». `HENC` pasa a ser un **código excluido** y la
regla de extra vuelve a ser «prefijo `HE`». No hay líneas que reparar (DA6 retirada).

## Glosario

- **Código excluido**: código de `auxhor` que la app no usa: no se ofrece, no se asigna, no se
  elige ni cuenta como extra. Lista de un elemento, `CODIGOS_EXCLUIDOS = ("HENC",)`, en un solo
  sitio de sv4 (`application/services/clase_hora.py`). Se compara con el código sin espacios a
  los lados y en mayúsculas.
- **Regla de extra**: un código no excluido es extra si (normalizado igual) empieza por `HE`.
  Sin código (None, vacío o espacios) la clase **no se sabe**.
- **`auxhor.ext`**: a 0 en todos los códigos (M1). Se sigue guardando en
  `parte_registros.hora_ext` como dato **informativo**; no decide nada nuevo.

## Requisitos

### La lista y la regla, en un único sitio de sv4 (DA1, decidida)

- **R1.** `es_excluido(codigo)` de `clase_hora.py` debe dar `True` para `"HENC"` y `" henc "`
  y `False` para `"HEOF"`, `"MENC"`, `"HENCX"`, `None` y `""`.
- **R2.** `es_hora_extra(codigo)` debe dar `True` para `"HECAP"`, `"HEGR"`, `" heof "`,
  `"HEPE"`, `"HEAA"`, `"HEOM"`; `False` para los excluidos (`"HENC"`) y para `"HL01"`,
  `"MENC"`, `"CI01"`, `"H"`, `"XHE"`; `None` para `None`, `""`, `"   "`.
- **R3.** El prefijo y la lista deben declararse una sola vez; `es_excluido`, `es_hora_extra`,
  `tipo_hora_de_codigo` y `condicion_sql_extra` se derivan de ellos (test con `monkeypatch`).
- **R4.** `condicion_sql_extra(columna)` debe devolver el predicado T-SQL de R2 sobre la columna
  (`UPPER(LTRIM(RTRIM(col))) LIKE 'HE%' AND … NOT IN ('HENC')`), solo con constantes del módulo
  y una columna que valida como identificador (`ValueError` si no).
- **R5.** `application/services/sincronizacion.py` debe seguir ofreciendo `es_hora_extra` con el
  mismo nombre, importado de `clase_hora` sin copia; una línea de Sigrid con un código excluido
  no cuenta como extra al comparar (F-052 R9; basta un test: la única de Sigrid es de 2022).
- **R6.** Ningún fichero Python de sv4 fuera de `clase_hora.py` debe implementar la regla ni la
  lista (`startswith("HE")`, `LIKE 'HE%'` ni `"HENC"` literales) (test de fuente).

### El catálogo y el desplegable

- **R7.** `fetch_tipos_hora` debe omitir los códigos excluidos (DA11): ni el desplegable
  (`GET /api/sigrid/tipos-hora`), ni `TipoHoraCatalog.get_by_ide`, ni el `TipoHoraMatcher` de
  «+ Nuevo» y de la celda de F-049, ni la búsqueda de incidencias los ven.
- **R8.** SI llega un `PATCH /api/registros/{id}/hora` con el `hora_ide` de un código excluido,
  ENTONCES el sistema debe responder 400 «El tipo de hora seleccionado no existe en Sigrid» sin
  tocar la línea (consecuencia de R7, DA12).
- **R9.** Cada elemento de `GET /api/sigrid/tipos-hora` debe ganar `extra` (booleano,
  `es_hora_extra(codigo) is True`) y conservar `ext` sin cambios (DA4).
- **R10.** `buildOptions` de `app.js` debe agrupar en «Horas extra» las opciones con
  `extra === true` y en «Horas ordinarias» el resto, sin leer `ext`; conserva el orden relativo
  y la marca de la opción actual.
- **R11.** `app.js` no debe implementar la regla ni la lista (ni `startsWith("HE")`, ni `.ext`,
  ni `HENC`) en el desplegable: todo llega del servidor (test de fuente).

### Guardar el código de hora (`PATCH /api/registros/{id}/hora`)

- **R12.** CUANDO se guarda en una línea que no es incidencia un código con prefijo `HE`, el
  sistema debe dejar `tipo_hora = "extra"`, aunque su `auxhor.ext` sea 0.
- **R13.** CUANDO se guarda en una línea que no es incidencia un código sin prefijo `HE`, el
  sistema debe dejar `tipo_hora = "normal"`, aunque su `auxhor.ext` sea 1.
- **R14.** MIENTRAS la línea sea incidencia, el sistema no debe cambiar su `tipo_hora`.
- **R15.** SI la opción elegida no tiene código, ENTONCES el sistema debe guardar el resto de
  campos y no cambiar `tipo_hora` (DA3).
- **R16.** El sistema debe seguir guardando `hora_ide`, `hora_codigo`, `hora_descripcion`,
  `hora_ext` (= `auxhor.ext`), los dos precios y `hora_match_method = "manual"` como hoy, y
  registrar el deshacer `registro_hora`; deshacer restaura el `tipo_hora` anterior.
- **R17.** La respuesta debe devolver `tipo_hora` por la regla (`"extra"` si `True`, `"normal"`
  en otro caso) y `hora_ext` con el valor de `auxhor.ext`.
- **R18.** El sistema debe mantener las guardas del endpoint (503 sin Sigrid, 404 sin registro,
  congelada F-004, recálculo F-043); los tests existentes siguen en verde. Con selección
  múltiple, cada línea queda con el `tipo_hora` de R12–R15.

### Los demás usos de la regla en sv4

- **R19.** `fetch_hora_extra_recurso` («+ extra», celda de F-049) debe filtrar con
  `condicion_sql_extra`: nunca devuelve un código excluido (hoy `HENC` no está en `reshor`; test
  con filas falsas `HENC` y `HEOF` ⇒ `HEOF`).
- **R20.** `fetch_dnis_sin_extra` debe calcular `es_he` con `condicion_sql_extra` en sus dos
  ramas: un DNI cuyo único `HE*` es excluido cuenta como **sin extra**.
- **R21.** `franquicia.extras_pendientes` (F-056) debe sumar solo acciones con `hora_codigo`
  extra según R2 (un excluido no suma); el resto de F-056 no cambia.

### Documentación y no regresión

- **R22.** `docs/ARCHITECTURE.md` semántica 3 debe recoger la lista de excluidos, la regla de
  extra y la M1 (en sv4 desde F-066; sv3 y sv5 cuando se cierre F-067).
- **R23.** El sistema no debe cambiar los disyuntivos `tipo_hora == "extra" or hora_ext == 1`
  de badges y totales (DA5).
- **R24.** Todos los tests de F-066 deben correr sin red ni BBDD (SQLite en memoria, clientes
  falsos que capturan el SQL, node para el JS).

## Verificaciones manuales

- **M1** — HECHA por el líder el 2026-11-06 (solo lectura), resultados en `design.md` §7.
- **M2** (humano, tras desplegar sv4): obra de pruebas 0404, línea ordinaria sin registrar: el
  desplegable no ofrece `HENC`; elegir `HEOF` (en «Horas extra») ⇒ badge extra al recargar;
  deshacer ⇒ vuelve. No se aprueba ni se envía a Sigrid.

## Fuera de alcance

Las 7 líneas `HENC` del portal (documentos inactivos), la línea de 2022 en Sigrid, la baja de
`HENC` en Sigrid (la decide Administración), sv3 y sv5 (F-067).

## Decisiones abiertas

Tabla en `design.md` §8 (DA1 decidida; DA6 retirada; DA7 a F-067). PARADA 1.
