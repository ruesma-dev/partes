# F-066 · El selector de código de hora clasifica extra por el prefijo `HE` — Requisitos

**Servicio**: solo **sv4** (`services/partes-front`). sv5 ya decide por prefijo y no cambia;
sv3 usa `auxhor.ext` con respaldos y queda fuera (LÍMITE DE SERVICIO, DA7). Esquema, colas y
contratos sv4↔sv5 no cambian. Rigor **crítico** (DA9): `tipo_hora` decide qué hora escribe sv5
en Sigrid (`HL` o `HE`), y en Sigrid no se borra.

**Origen**: hallazgo **H-M2-1b** de F-052 (M2, 2026-11-03), acordado con el humano el
2026-11-03 («me parece bien»). En Sigrid el flag `auxhor.ext` no es fiable: las 7 horas `HE*`
lo tienen a 0 (`progress/m2_F-052.md`, `progress/impl_F-052.md` §H-M2-1). El portal ya lo sabía
(`fetch_dnis_sin_extra`, `fetch_hora_extra_recurso`) y F-052 añadió `es_hora_extra` por prefijo,
pero el selector de código de hora (`PATCH /api/registros/{id}/hora`) sigue fijando `tipo_hora`
con `auxhor.ext`: si se elige una `HE*`, la línea queda `normal` y sv5
(`reglas_registro.py`, rama `tipo == "normal"`) escribiría una `HL`. Impacto medido por el líder
el 2026-11-03 (base `partes`, solo lectura): 3 líneas (registros 16417, 16422, 16640, obra
0678), las tres `omitido`, ninguna registrada; nada mal escrito en Sigrid (DA6).

## Glosario

- **Regla del prefijo**: una hora de Sigrid es extra si su código, sin espacios a los lados y
  en mayúsculas, empieza por `HE`. Sin código (None, vacío o solo espacios) la clase **no se
  sabe**. Es la regla de sv5 (`HoraRecurso.es_extra`, `franquicia._es_extra`).
- **`es_hora_extra(codigo)`**: la función pura de sv4 que la implementa (F-052); devuelve
  `True`, `False` o `None` (no se sabe).
- **`auxhor.ext`**: flag de Sigrid «computa como extra». Se sigue guardando en
  `parte_registros.hora_ext` como dato **informativo**; no decide nada nuevo.

## Requisitos

### La regla, en un único sitio de sv4

- **R1.** El sistema debe exponer `es_hora_extra` en `application/services/clase_hora.py`
  (DA1) con el comportamiento actual: `"HE01"`, `" he02 "`, `"HEX"` ⇒ `True`; `"HL01"`,
  `"CI01"`, `"H"`, `"XHE"` ⇒ `False`; `None`, `""`, `"   "` ⇒ `None`.
- **R2.** `application/services/sincronizacion.py` debe seguir ofreciendo `es_hora_extra` con
  el mismo nombre (importado de `clase_hora`, sin copia del cuerpo), de modo que F-052 y sus
  tests no cambian.
- **R3.** Ningún fichero de sv4 debe contener otra implementación de la regla en Python: los
  usos nuevos de R4–R10 y R13 importan de `clase_hora`, y la copia de
  `franquicia.py::extras_pendientes` (F-056, `.upper().startswith("HE")`) pasa a
  `es_hora_extra(...) is True` con el mismo resultado para códigos de Sigrid (test de fuente y
  los tests de F-056 en verde). Las cadenas SQL `LIKE 'HE%'` no cuentan (R16).

### Guardar el código de hora (`PATCH /api/registros/{id}/hora`)

- **R4.** CUANDO se guarda en una línea que no es incidencia un código con prefijo `HE`, el
  sistema debe dejar `tipo_hora = "extra"`, **aunque** su `auxhor.ext` sea 0.
- **R5.** CUANDO se guarda en una línea que no es incidencia un código sin prefijo `HE`, el
  sistema debe dejar `tipo_hora = "normal"`, **aunque** su `auxhor.ext` sea 1.
- **R6.** MIENTRAS la línea sea incidencia (`es_incidencia`), el sistema no debe cambiar su
  `tipo_hora` al guardar un código (como hoy).
- **R7.** SI la opción elegida no tiene código (`es_hora_extra` ⇒ `None`), ENTONCES el sistema
  debe guardar el resto de campos y no cambiar `tipo_hora` (DA3).
- **R8.** El sistema debe seguir guardando `hora_ide`, `hora_codigo`, `hora_descripcion`,
  `hora_ext` (= `auxhor.ext`, informativo), los dos precios y `hora_match_method = "manual"`
  exactamente como hoy, y registrar el deshacer `registro_hora` con el estado anterior.
- **R9.** CUANDO se deshace un cambio de código que movió `tipo_hora`, el sistema debe
  restaurar el `tipo_hora` anterior (ya está en `_REG_UNDO_FIELDS`; test nuevo con `HE` y
  `ext = 0`).
- **R10.** La respuesta del endpoint debe devolver `tipo_hora` calculado con la regla del
  prefijo (`"extra"` si `True`, `"normal"` en otro caso) y `hora_ext` con el valor de
  `auxhor.ext`, como hoy.
- **R11.** El sistema debe mantener intactas las guardas del endpoint: 503 sin Sigrid, 400 si
  el `hora_ide` no está en el catálogo, 404 sin registro, línea congelada (F-004) y recálculo
  en curso (F-043). Lo cubren los tests existentes, que deben seguir en verde.
- **R12.** CUANDO el usuario guarda el código en varias líneas a la vez (selección múltiple de
  `app.js`), cada una debe quedar con el `tipo_hora` de R4–R7 (el JS llama al mismo endpoint
  por línea; test del endpoint con dos líneas).

### El desplegable (`GET /api/sigrid/tipos-hora` y `static/app.js`)

- **R13.** El sistema debe añadir a cada elemento de `GET /api/sigrid/tipos-hora` el campo
  `extra` (booleano: `es_hora_extra(codigo) is True`) y conservar `ext` sin cambios (DA4).
- **R14.** El desplegable del código de hora (`buildOptions` de `app.js`) debe agrupar en
  «Horas extra» las opciones con `extra === true` y en «Horas ordinarias» el resto, sin leer
  `ext`: una `HE*` con `ext = 0` sale en «Horas extra» y una `HL*` con `ext = 1` en
  «Horas ordinarias». Se mantiene el orden relativo de las opciones y la marca de la actual.
- **R15.** `app.js` no debe implementar la regla del prefijo (ni `startsWith("HE")` ni
  comparaciones con `.ext`) en el desplegable: la clase llega del servidor (test de fuente).

### Gemelos y documentación

- **R16.** DONDE el humano apruebe DA8 = B, el sistema debe tener un guardián
  `tests/test_f066_prefijo_he_gemelos.py` que compruebe, con una tabla común de casos, que
  `es_hora_extra` de sv4, `HoraRecurso.es_extra` y `franquicia._es_extra` de sv5 dan la misma
  clase, y que las consultas `HE%` de sv4 (`fetch_dnis_sin_extra`, `fetch_hora_extra_recurso`)
  siguen usando `LIKE 'HE%'`. Extraído por AST o texto, sin importar los módulos.
- **R17.** El sistema debe documentar el cambio en `docs/ARCHITECTURE.md` (semántica 3: la
  clase de una hora elegida en el portal sale del prefijo `HE`) y, si DA8 = B, añadir la regla a
  la lista cerrada de gemelos de `CLAUDE.md`.

### No regresión y fuera de alcance

- **R18.** El sistema no debe cambiar los criterios de badges y totales que ya combinan
  `tipo_hora == "extra" or hora_ext == 1` (`_is_extra`, `extras_por_jornada`, `app.py` ~1019,
  plantillas `obra_detail`, `parte_detail`, `trabajador_detail`) salvo que DA5 lo decida.
- **R19.** Todos los tests de F-066 deben correr sin red ni BBDD (SQLite en memoria, clientes
  falsos, node para el JS); los de BBDD real son verificaciones manuales (M1, M2).

## Verificaciones manuales (humano o líder, solo lectura salvo M3)

- **M1** (líder, antes de implementar, solo lectura): en Sigrid vía sigrid-api, qué códigos
  tienen `ext = 1` y no empiezan por `HE` (decide DA5); en la base `partes`
  (`default_transaction_read_only=on`), recontar líneas vivas con código `HE%` y
  `tipo_hora = 'normal'` (esperado: las 3 de DA6). Comandos en `design.md` §7.
- **M2** (humano, tras desplegar sv4): elegir una `HE*` en una línea de la obra de pruebas
  0404 ⇒ queda «extra» al recargar y sale en el grupo «Horas extra»; deshacer ⇒ vuelve.
- **M3** (humano, según DA6): tratamiento de los registros 16417, 16422 y 16640.

## Decisiones abiertas

Tabla DA1–DA9 con la opción recomendada en `design.md` §8. El humano las aprueba (PARADA 1).
