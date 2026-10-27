<!-- progress/impl_F-056.md -->
# F-056 · Franquicia de extras — informe del implementer (bloque sv5, T1–T7)

**Estado: CORTADO TRAS T7 A LA ESPERA DE DA1** (orden del líder del 2026-10-27). El humano valora
definir la franquicia (quién la tiene y su X) en un campo nuevo de Sigrid en vez de en la tabla
`empleado_franquicia` (DA1 = A aprobada); eso cambiaría T8, T9, T14 y parte de T10–T13. El bloque
sv5 vale tal cual porque recibe X en la petición.

Rama `feature/F-056-franquicia-de-extras` (worktree `partes-wt-f056`), desde ef46216 (dev 39aef7b).

## Encaje con lo fusionado después de la spec (comprobado antes de T1)

Comprobado contra F-058…F-064 sin encontrar nada que cambie lo aprobado:
- `RegistroPipeline._choques` (paso 7: `parte_cerrado`, `_motivo_sin_pisado`, `_conflictos`)
  delega en `pisado.choques` ⇒ R31 cubre el registro con **un** cambio en `pisado.choques`.
  `ReajustePipeline._choques` tiene su propio filtro, como decía la spec.
- F-060/F-062: `partes:<id>:ciz` y `racha_ciz.registro_de_synckey` no tocan `partes:franquicia:<id>`
  (`int("franquicia:5")` da error ⇒ None). `_ciz_ajeno` solo mira el `horide` del CIZ.
- `_crear_parte`, `stmt_insert_linea`, `stmt_actualizar_linea` y `lineas_para_reajuste` no han
  cambiado: se reutilizan como dice H3.
- sv4 (sin tocar): `/api/aprobar/preflight|ejecutar|encolar` mantienen el patrón de F-046
  (decisiones antes de los grupos); guardianes de la raíz en 7 tablas ⇒ 9 encaja.

## Commits

| Tarea | Commit | Qué |
|---|---|---|
| T1 | eec694c | `PREFIJO_FRANQUICIA`, `es_synckey_franquicia`, `PeticionFranquicia`, `VeredictoFranquicia`, `ResultadoFranquicia` |
| T2 | cfd1c61 | `application/services/franquicia.py` (puro): `ajuste_objetivo`, `veredicto`, `texto_ajuste` |
| T3 | 43c80b8 | R31 en `pisado.choques` y `ReajustePipeline._choques` + caracterización del registro |
| T4 | 1b647d7 | `synckey_franquicia`, `extras_del_periodo` (cliente) y `SigridFake` |
| T5 | 326c0eb | `FranquiciaPipeline` y `RegistroPipeline.asegurar_parte` |
| T6 | e08a259 | `FranquiciaIn`, `/api/franquicia/comprobar` y `/ejecutar`, `main.py` |
| T7 | 5f65009 | suite sv5 en verde; estado en `current.md` |
| (T8) | 95c9817 → revertido en 4e43d80 | ORM de las dos tablas + guardianes a nueve. Llegó antes del aviso del líder; se revierte con commit (sin reescribir la historia) y queda recuperable si DA1 sigue en A |

## Ficheros tocados (todo en `services/partes-transfer/`)

- `domain/models/registro_models.py`: prefijo, predicado y las tres dataclasses (+78).
- `application/services/franquicia.py` (nuevo, puro): A = `-min(E, X)` si E > 0, si no 0, a dos
  decimales y sin `-0.0`; veredicto en el orden R30 → sin línea (`sin_ajuste`/`crear`) →
  `ya_aplicado` (antes que el parte y los enlaces, como F-046 R26) → `parte_no_abierto` →
  `linea_enlazada` → `actualizar`. Los prefijos de motivo se importan de `parte_abierto` y `pisado`.
- `application/services/pisado.py` y `application/pipelines/reajuste_pipeline.py`: el filtro
  `not es_synckey_franquicia(ls.synckey)` (R31). `pisado` sigue importando solo de `domain`.
- `application/pipelines/registro_pipeline.py`: **solo** se añade `asegurar_parte(p, destino)`,
  que delega en `_crear_parte` con la descripción del paso 8 (marca en pruebas).
- `application/pipelines/franquicia_pipeline.py` (nuevo).
- `infrastructure/sigrid/sigrid_write_client.py`: `synckey_franquicia` (función de módulo y
  `staticmethod`) y `extras_del_periodo` (solo métodos nuevos).
- `interface_adapters/api/app.py` y `main.py`: rutas, `FranquiciaIn`, composición.
- `tests/dobles.py`: `extras_del_periodo`, `lineas_para_reajuste`, `stmt_actualizar_linea` y la op
  `actualizar` en `escribir` (con el `WHERE` optimista + guarda + sin enlaces). Sin op `borrar`.
- Tests nuevos: `test_f056_franquicia.py`, `test_f056_choques.py`, `test_f056_cliente.py`,
  `test_f056_pipeline.py`, `test_f056_api.py`.

## Decisiones de diseño y desviaciones (mecánicas)

1. **Fechas como `YYYYMMDD` enteras** (`inicio`, `fin`, `fecha_int`), como `hmores.fec`; el
   `BETWEEN` de §4 las usa directamente. `FranquiciaIn` valida que existan y que
   `inicio ≤ fecha_int ≤ fin`, `periodo` con `^\d{4}-(0[1-9]|1[0-2])$` y obra con `ide` o `codigo`.
2. **`preparar` recibe una extra con `horas = -1`** solo para que las reglas den código `HE*`,
   `pre` y cuenta F-021 (sin horas, `ReglasRegistro` la omite). La cantidad escrita es A,
   calculada **dentro** del lock. `registro_id` = `ajuste_id`.
3. **`veredicto` lleva `parte_cod` opcional** (no está en la firma de §4) para nombrar el parte en
   los motivos de R27.
4. **Escritura por `escribir([sentencia])`** (una sentencia; el alta del parte, si falta, antes
   vía `asegurar_parte`). Lo que decide es la **relectura** por synckey (R29): `ok` solo si la línea
   está en el parte elegido con `can` = A. Si la escritura lanza pero la línea entró ⇒ `ok` con
   WARNING; si no entró ⇒ `ok: false` con el error. Un fallo de **lectura** propaga ⇒ 502.
5. **`comprobar` con `ajuste_id` 0** no busca la línea; excluye `partes:franquicia:0` de E (no
   existe). `ejecutar` con 0 ⇒ `ValueError` en el pipeline y 422 en la API.
6. **`comprobar` devuelve `extras` = E de Sigrid** y `objetivo` = A con E + `extras_pendientes`
   (R9 pide los dos por separado). `ejecutar` ignora `extras_pendientes`.
7. **Sin franquicia inyectada en `build_app` ⇒ 503** en las dos rutas (§4). No se construye
   perezosamente, a diferencia del reajuste: escribe en Sigrid y no debe componerse a medias.
8. **`tex` al recalcular no cambia**: `stmt_actualizar_linea` (F-046) solo toca `can` y `tot`, y la
   spec manda reutilizarla tal cual. El `tex` conserva el A del alta. Si se quiere `tex` vivo,
   habría que ampliar esa sentencia (fuera de lo aprobado). **Lo señalo para el reviewer y el
   humano.**
9. `texto_ajuste` usa coma decimal y quita los ceros sobrantes: `-6`, `-7,5`, `-2,25`.

## Fase RED (trazas reales; comando ejecutado en `services/partes-transfer`)

T1 — `python -m pytest tests/test_f056_franquicia.py -k modelos -q -p no:cacheprovider`
```
E   ImportError: cannot import name 'PREFIJO_FRANQUICIA' from 'domain.models.registro_models'
ERROR tests/test_f056_franquicia.py
1 error in 1.06s
```
T2 — `python -m pytest tests/test_f056_franquicia.py -q -p no:cacheprovider`
```
E   ImportError: cannot import name 'franquicia' from 'application.services'
1 error in 1.10s
```
T3 — `python -m pytest tests/test_f056_choques.py -q -p no:cacheprovider` (7 failed, 3 passed;
los 3 que pasan son los controles: las demás synckeys siguen chocando)
```
E   AssertionError: assert [LineaSigrid(ide=7001, ..., synckey='partes:franquicia:5', ...)] == []
E   At index 1 diff: (False, 'ya hay horas de ese recurso, dia y codigo de hora en un parte En
    registro (lineas 7001)') != (True, None)
E   Left contains one more item: Conflicto(clave='501|20261015|2', ..., registros=[11])
E   At index 0 diff: ('omitir', 'parte_cerrado: ya hay horas de ese recurso, dia y tipo en el
    parte PT26/00300 (Cerrado); no se registran') != ('escribir', None)
E   assert [] == [11]
```
T4 — `python -m pytest tests/test_f056_cliente.py -q -p no:cacheprovider`
```
E   ImportError: cannot import name 'synckey_franquicia' from 'infrastructure.sigrid.sigrid_write_client'
1 error in 1.92s
```
T5 — `python -m pytest tests/test_f056_pipeline.py -q -p no:cacheprovider`
```
E   ModuleNotFoundError: No module named 'application.pipelines.franquicia_pipeline'
1 error in 0.63s
```
T6 — `python -m pytest tests/test_f056_api.py -q -p no:cacheprovider`
```
38 x  E   TypeError: build_app() got an unexpected keyword argument 'franquicia'
FAILED ...test_f056_r22_cuerpo_valido_llega_al_pipeline[/api/franquicia/comprobar]  (y 10 más)
```
Ya en verde: T1 15 passed · T2 88 · T3 10 (+123 de F-046/F-053 sin tocar) · T4 16 · T5 27 · T6 52
(con `test_f002_settings_y_app.py`).

## Qué cubren los tests (R22–R33)

- R24/R28/R25/R19 siguiendo el guion de M2 contra `SigridFake`: crear (−6, `tot` −150, `pos`,
  cuenta 702, `tex`), repetir ⇒ `ya_aplicado` sin escribir, extra de 4 h el día de ajuste
  registrada sin conflicto (R31) y recalcular ⇒ `UPDATE` a −8 (`tot` −200), X = 0 ⇒ `can = 0`,
  `tot = 0` y la fila sigue ahí; sin línea y E = 0 ⇒ `sin_ajuste`.
- Alta del parte si no hay ninguno En registro (alta protegida; `complementario`).
- R27 parte cerrado / enlazada; R30 sin `HE*` y recurso de otra empresa: nada grabado.
- R29: guarda que cierra el parte entre lectura y escritura, escritura que lanza pero entró,
  escritura que lanza sin entrar, `UPDATE` optimista que no encuentra la fila como se leyó.
- R26: un *fixture* comprueba en **cada** test del pipeline que solo se grabaron `insert`,
  `actualizar` y `crear_parte`.
- R22: lock = el del registro (un `LockEspia`: `comprobar` no lo toma, `ejecutar` una vez);
  lecturas de cuentas fuera del lock (`vigilar_lock`); composición en `main.py` con el mismo
  cliente y lock. R32: obra 0404, `tex = PRUEBA-IA`, descripción del parte con la marca.
  R33: log con `ajuste=`, `recurso=`, `objetivo=` y `usuario=`, sin nombre de obra.
- API: 13 cuerpos inválidos ⇒ 422 sin llamar; centinela (vale en comprobar, 422 en ejecutar);
  respuesta = el `ResultadoFranquicia` entero; 502 ante excepción; 503 sin pipeline.

## Fuera del alcance de este corte / pendiente

- **T8–T16 (sv4)**: a la espera de DA1. T17 (documentación, incluido `azure-apps/partes.md`), T18
  (mutación: la lanza el líder), T19 (M2–M4, humano) y T20 no se han hecho. `docs/` y `azure-apps`
  sin tocar: sv5 aún no tiene cliente que use las rutas nuevas, así que nada cambia en producción
  mientras no se despliegue sv4.
- **Verificación MANUAL pendiente**: M2 (escritura en la 0404 con `OBRA_PRUEBAS_FORZAR=true`),
  M3, M4. Ningún agente ha escrito en Sigrid ni en ninguna base real.
- `ruff`: los ficheros nuevos están limpios; `app.py` y `main.py` conservan su deuda previa.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests F-056 (sv5) | 180 passed (5 ficheros), 7,48 s |
| Suite sv5 entera | 1344 passed, 1 warning (16,6 s a mano con `-p no:cacheprovider`) |
| `bash harness/init.sh` | verde, «ENTORNO LISTO» (2026-10-27, tras el revert de T8). sv1–sv4 «de caché»: sus árboles no cambian en el estado final (el revert deja sv3/sv4 como en dev); sv5 (la tocada) corrió de verdad: 1344 passed |
| Cobertura de líneas cambiadas | PUERTA COBERTURA: 100,0 % (285/285, umbral 80 %, nivel crítico) |
| Mutación | no lanzada: la campaña la lanza el líder (T18, encargo) cuando la feature esté completa |
| Tiempo de las suites (init) | raíz 522 passed, 3 skipped en 168,5 s; sv5 1344 passed en 32,8 s |
