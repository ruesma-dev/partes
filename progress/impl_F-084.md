# F-084 · Informe del implementer (nivel `critico`)

Rama `feature/F-084-partes-con-problemas` (copia `partes-wt-f084`). Alcance del encargo: T1–T9
y T12. **Fuera**: T10 (campaña de mutación, la lanza el líder tras el reviewer principal) y T11
(manual M1–M3, tras desplegar).

## Qué cambió

- **sv3** (`sqlalchemy_parte_repository.py`): `_deactivate_same_day_obra` gana `email_id` y escribe
  en el viejo `sustituido_por_id` y `sustituido_at_utc` (UTC ISO) en la misma sesión del nuevo, sin
  tocar `deleted_*`; mismo `email_id` no vacío ⇒ WARNING `[parte-repo] reemplazo del mismo envio: …`.
  La condición del reemplazo no se toca.
- **Esquema**: las dos copias de `orm_models.py`, byte-idénticas (design §3); `ddl_complementario()`
  genera los dos `ADD COLUMN IF NOT EXISTS` sin tocar su código.
- **sv4**: módulo puro `application/services/partes_con_problemas.py` (motivos, `clasificar`,
  `resumen`, `elegir_sustituto`, `motivo_no_recuperable`, excepciones); repositorio
  (`list_partes_con_problemas`, `resumen_problemas`, `recuperar_parte`, `_choques`, deshacer de
  `parte_recuperar` con `reactivados` y `actor`); portal (`GET /problemas`,
  `GET /api/problemas/resumen`, `POST /api/partes/{id}/recuperar`, `include_in_schema=False`);
  `recalculo_publisher.py` (dos motivos); `problemas.html`, `base.html`, `app.js`, `styles.css`.
- **Documentación**: `docs/ARCHITECTURE.md` (semánticas 7 y 8); `azure-apps/partes.md` en commit
  aparte **`e09fd49`** (`pull --rebase` sin conflicto; **sin push**).
- Ficheros nuevos: el módulo puro, `problemas.html` y los cuatro `test_f084_*` (sv3: `…rastro_reemplazo`;
  sv4: `…clasificacion`, `…recuperar`, `…portal`).

## Decisiones de diseño (sin cambio de la spec; para el reviewer)

1. **Agrupación (R11)**: cada parte va en el grupo de su **primer** motivo (orden de
   `ORDEN_MOTIVOS`); los demás motivos salen como insignias en su fila. Dentro, fecha descendente.
2. **404 (R22)**: `recuperar_parte` devuelve `None` si el documento no existe; el resto de
   guardas lanzan, en el orden de design §6. Fecha vacía o ausente en el cuerpo = sin cambio.
3. **Fila del sustituto**: `{id, fecha, obra_codigo, obra_nombre, activo}` (design dice
   `{id, fecha, obra, activo}`): R11 pide código y nombre. El choque de R19 sí usa `{id, fecha, obra}`.
4. **Insignia `congelado`**: `"aprobado"` si el motivo de `_motivo_congelado_doc` es el de
   aprobado; `"sigrid"` (texto «en Sigrid») para encolado, registrado o dedicación.
5. **Deshacer con el parte hoy congelado**: no se desactiva y no suma otra vez en `omitidos` (ya
   suma por su snapshot de documento, que toda `parte_recuperar` lleva).
6. **Pista retroactiva (R8)**: «posterior» se compara con `created_at_utc` parseado (tolera `Z` y
   `+00:00`); un `created_at_utc` ilegible en el sustituido no da pista.
7. **«Ver PDF» (R12)**: solo con el visor activo (`preview_enabled`) y PDF archivado, como Conciliar.
8. **JS**: «Recuperar» pide la fecha con `prompt` (la actual en dd/mm/aaaa), confirma y hace el
   POST; un 409 se enseña con `alert` y los partes del choque con su ruta `/partes/{id}`; el 200
   recarga `/problemas` con mensaje y avisa si `recalculo` es `fallo`.
9. **Estilo**: ruff pide reordenar los imports de los tests nuevos (I001 con su configuración de
   raíz); se deja el estilo de los tests vecinos (`test_f061_borrado.py`, `test_f047_*`). El lint no
   bloquea (deuda previa): 1184 avisos antes, 1188 con la feature.

## Fase RED (trazas reales, comando exacto)

**T1** (commit `ed049e2`) · `python -m pytest services/partes-persistencia/tests/test_f084_rastro_reemplazo.py -q -rf --tb=line`
```
E   AttributeError: sustituido_por_id
E   assert ('ALTER TABLE parte_documents ADD COLUMN IF NOT EXISTS ' + 'sustituido_por_id VARCHAR(36)') in ("ALTER TABLE dedicacion_bandeja ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT '1' NOT NULL", ...)
FAILED ...::test_f084_r1_el_reemplazo_escribe_quien_y_cuando
FAILED ...::test_f084_r1_el_rastro_va_en_el_mismo_commit_que_el_nuevo
FAILED ...::test_f084_r1_un_parte_que_no_se_sustituye_no_lleva_rastro
FAILED ...::test_f084_r2_entre_paginas_del_mismo_envio_se_sigue_sustituyendo
FAILED ...::test_f084_r3_mismo_envio_deja_un_warning_con_los_dos_ids
FAILED ...::test_f084_r3_sin_correo_en_ninguno_no_es_mismo_envio
FAILED ...::test_f084_r4_otro_trabajador_ni_se_sustituye_ni_lleva_rastro
FAILED ...::test_f084_r4_otra_obra_u_otro_dia_no_se_sustituyen
FAILED ...::test_f084_r5_el_orm_declara_las_dos_columnas_nullables
FAILED ...::test_f084_r5_el_ddl_de_arranque_las_anade
10 failed, 2 passed in 4.07s
```
(Los 2 en verde: el INFO de otro envío y el correo vacío, que ya se cumplían antes.)

**T3** (commit `3d0e08d`) · `cd services/partes-front && python -m pytest tests/test_f084_clasificacion.py -q -p no:cacheprovider --tb=line`
```
tests\test_f084_clasificacion.py:15: in <module>
    from application.services import partes_con_problemas as pp
E   ImportError: cannot import name 'partes_con_problemas' from 'application.services' (unknown location)
ERROR tests/test_f084_clasificacion.py
1 error in 1.30s
```

**T5** (commit `f8bc8b4`) · `python -m pytest tests/test_f084_recuperar.py -q -p no:cacheprovider --tb=line` (errores agrupados)
```
     27 E   AttributeError: 'ParteReviewRepository' object has no attribute 'recuperar_parte'
      5 E   AttributeError: 'ParteReviewRepository' object has no attribute 'list_partes_con_problemas'
      1 E   AttributeError: 'ParteReviewRepository' object has no attribute 'resumen_problemas'
33 failed, 1 passed in 5.06s
```
(El verde: «las demás acciones no ganan `reactivados` ni `actor`», regresión que ya se cumplía.)

**T7** (commit `839fe43`) · `python -m pytest tests/test_f084_portal.py -q -p no:cacheprovider --tb=line` (agrupados)
```
      4 E   assert 404 == 200          2 E   assert 404 == 409
      2 E   assert (404 == 409)        2 E   assert (404 == 200)
      1 E   assert 404 == 400          1 E   AssertionError: assert 404 == 200
      2 E   AssertionError: no hay fila para viejo
      1 E   AssertionError: no hay fila para sin-obra / en-sigrid / con-pdf (uno cada uno)
      1 E   jinja2.exceptions.TemplateNotFound: 'problemas.html' not found in search path
      1 E   assert 'No hay partes con problemas' in '{"detail":"Not Found"}'
      1 E   assert 'function wireProblemasBadge' in '// static/app.js — portal de partes (sv4) ...'
      1 E   KeyError: 'total'          1 E   ValueError: substring not found
      1 E   AttributeError: module '...recalculo_publisher' has no attribute 'MOTIVO_RECUPERAR_PARTE'
      1 E   assert None
24 failed, 3 passed, 1 warning in 43.86s
```
(Los 3 en verde ya se cumplían: los dos descartes de R26, que reutiliza `delete_document`, y «sin visor no hay Ver PDF».)

## Verificación por tarea

| Tarea | Verificación | Resultado real |
|---|---|---|
| T2 | T1 + `tests/test_f010_orm_models_gemelos.py` + suite sv3 | 12/12; gemelos 35/35 (con F-043); suite sv3 desde su carpeta **2966 passed, 2 skipped** |
| T4 | T3 | 43 passed; cobertura del módulo 100 % (158/158 sentencias) |
| T6 | T5 | 34 passed |
| T8 | T7 + `node --check static/app.js` + parseo Jinja2 | 27 passed; `JS-OK`; `problemas.html` y `base.html` parsean (test `test_f084_las_plantillas_parsean`) |
| T9 | `git -C azure-apps log -1` | `e09fd49 F-084: partes, pestaña de partes con problemas…`; `git status` limpio |
| T12 | `bash harness/init.sh` | verde en la segunda pasada (ver «Salida de init.sh») |

## Requisitos → tests

R1–R5: `test_f084_rastro_reemplazo.py` (R4 además: la suite sv3 anterior intacta y en verde).
R6–R10: `test_f084_clasificacion.py`; R6–R11 en el repositorio: `test_f084_recuperar.py`
(`…_r11_lista_un_caso_de_cada_motivo`, `…_r10_resumen_es_la_misma_lista`, `…_r8_pista…`).
R17, R19–R24: `test_f084_recuperar.py`. R11–R16, R17–R22 por HTTP, R18 (y fallo de cola), R23
(rama de deshacer y etiqueta del widget), R25 (navegación, resumen, fallo del resumen, JS), R26:
`test_f084_portal.py`.

## Salida de `init.sh`

T12, segunda pasada (HEAD `1316ce4`): **EXIT 0**. Raíz 2549 passed / 50 skipped (33 min); sv4 4137
passed / 1 skipped (26 min); sv1-sv3 y sv5 en verde; `PUERTA COBERTURA` 100,0 % (303/303);
`PUERTA TAMAÑO`, `PUERTA CARRIL` y `CAPA E2E` en [OK]/N/A; ruff 1188 avisos (deuda previa).
**Primera pasada en rojo** (HEAD `3536271`), tres causas, resueltas en `1316ce4`:
1. sv4 `test_f017_punto_unico.py::test_f017_todos_los_puntos_de_escritura_usan_el_helper`:
   `assert 24 == 23` (la ruta nueva firma con `_actor(request)`, R17, R18).
2. sv4 `test_f047_portal_parte_nuevo.py::test_f047_r23_ninguna_funcion_nueva_y_una_sola_variable`:
   `assert ((322 - 17) - 1) == 301` (las tres funciones nuevas de `app.js`, design §8).
3. raíz `test_f059_ejecucion.py::test_f059_r9_…` (`nieto.pid`): inestable conocido de F-059 bajo
   carga; pasó en la segunda pasada. El 35 % de cobertura de esa pasada era el `-x` de sv4.

**Desviación justificada**: 1 y 2 tocan guardianes de otras features con el mecanismo de F-042,
F-052, F-056 y F-068 (subir la cuenta a 24; tupla propia `F084_PROBLEMAS`); lo que cuentan lo pide la spec.

## Pendiente

- **Aceptación del humano** de los 7 equivalentes (RM5 #1–#7, `progress/mutacion_F-084.md`).
- **T11** (humano, tras desplegar sv3 y sv4): M1–M3 de design §12; M3 solo con OK expreso.
- **Push** (humano): rama de la feature y `azure-apps` (`e09fd49`): `git pull` y luego `git push`.
- Capa e2e: ningún requisito lleva `(capa: e2e)`; lo dice la línea `CAPA E2E` de abajo.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | raíz 2549 passed / 50 skipped; sv4 4147 passed (tras T10) / 1 skipped; sv3 2966 passed / 2 skipped; sv1 74; sv2 579 / 1 skipped; sv5 1890 / 1 skipped: **0 fallos** |
| Tests nuevos de F-084 | sv3 12 (`test_f084_rastro_reemplazo.py`); sv4 46 + 38 + 30 = 114 (clasificación, repositorio, portal; 10 de T10) |
| Cobertura de las líneas cambiadas | **100,0 %** (303/303; umbral 90 % del nivel `critico`), línea `PUERTA COBERTURA` |
| Mutantes generados / supervivientes | 198 generados, 100 evaluados: 82 muertos, 18 supervivientes, 0 timeouts (22864.8 s, `progress/mutacion_F-084.md`); tras T10, 11 muertos por tests nuevos y 7 equivalentes justificados |
| Tiempo de la suite | raíz 1995 s (33:15, con cobertura); sv4 1579 s (26:19); sv3 131 s (primera pasada) |
| Capa e2e | N/A: `CAPA E2E: N/A (ningún servicio declara el bloque e2e)`; ningún requisito lleva `(capa: e2e)` |

## Ciclo 1 (CHANGES_REQUESTED de documentación, commit `27f6b6b`)

- `progress/current.md`: M1–M3 de design §12 con su SELECT, sus rutas y el resultado esperado. M3 lleva la marca de que solo se hace con el OK expreso del humano.
- `undo_log.actor`: ahora dicen que `parte_recuperar` (F-084) lo rellena `docs/ARCHITECTURE.md` (identidad), el docstring de `_actor` (`app.py`) y la cabecera de `identidad.py`. Coincide con `azure-apps/partes.md` §4.5. Solo cambian docstrings y comentarios; ningún guardián cuenta ese texto.
- `ARNES_SIN_CACHE=1 bash harness/init.sh` en HEAD `27f6b6b`: **EXIT 0 a la primera**, todo sin caché (raíz 2549, sv4 4137, cobertura 303/303).

## Campaña de mutación (T10)

`python -m harness.mutacion --feature F-084 --workers 3` (HEAD `8474ce9`). Cada muerte se verificó a
mano: mutante aplicado por línea, `python -m pytest <fichero>::<test> -q -p no:cacheprovider` desde
`services/partes-front` en **rojo** (1 failed) y, tras `git checkout -- <fichero>`, en **verde**
(1 passed); árbol limpio al final. Rojo real de cada uno, entre paréntesis. Tests en `c38ed73`.

| # | Mutante | Decisión | Test que lo mata o justificación |
|---|---|---|---|
| 1 | `pcp:110` `Clasificado` `frozen=False` | test de diseño | `clasificacion::test_f084_clasificado_es_inmutable`: protege el diseño (`frozen=True`), **no un requisito** (sin `rN`, ciclo 2) (`DID NOT RAISE FrozenInstanceError`) |
| 2 | `pcp:144` `is not None and` → `fecha_int and` | equivalente | `0`/`None` dan `0`/`None` en vez de `False`; los 3 llamadores usan `not`. RM5 #1 |
| 3 | `pcp:174` `is None` → `not recibido` | equivalente | `_instante` da `datetime` o None; un `datetime` siempre es verdadero. RM5 #2 |
| 4 | `pcp:231` `>` → `>=` | test | `…_r8_pista_exige_creado_estrictamente_despues` (devuelve el gemelo en vez de None) |
| 5 | `pcp:244` `is None` → `not sustituto` | equivalente | `DocProblema` es dataclass sin `__bool__` ni `__len__`: siempre verdadero. RM5 #3 |
| 6 | `pcp:275` `or 0` → `or 1` | test | `…_r11_sin_fecha_va_tras_cualquier_fecha` (`['sf','f1'] != ['f1','sf']`; solo cambia con `fecha_int` 1) |
| 7 | `orm sv4:190` `String(64)` → `65` | test | `recuperar::test_f084_r5_ddl_declara_las_columnas_del_rastro` (falta `VARCHAR(64)`; SQLite ignora longitudes) |
| 8 | `repo:4910` `is None` → `not motivo` | equivalente | `motivo_congelacion_documento` da None o una de 4 constantes no vacías. RM5 #4 |
| 9 | `repo:4942` `and` → `or` en `tiene_pdf` | test | `…_r12_tiene_pdf_exige_drive_e_item` (`assert True is False`) |
| 10 | `repo:4986` `is not None` → truthy | test | `…_r19_obra_ide_cero_es_una_obra` (`ChoqueRecuperarError` por código con `obra_ide` 0 ≠ 5) |
| 11 | `repo:5035` `is not None` → `if motivo` | equivalente | `motivo_no_recuperable` da None o una de 3 constantes no vacías. RM5 #5 |
| 12 | `repo:5059` `or` → `and` en la descripción | test | `…_r23_la_descripcion_del_deshacer_lleva_la_obra` (`'Recuperar parte 100 (…'`) |
| 13 | `app:2252` `sum(1` → `sum(2` | test | `portal::test_f084_r10_la_cabecera_cuenta_solo_los_que_cuentan` (falta `(1)</h1>`) |
| 14 | `app:2260` resumen `include_in_schema=True` | test | `…_r25_las_rutas_nuevas_no_salen_en_el_esquema` (`/api/problemas/resumen` en `paths`) |
| 15 | `app:2273` recuperar `include_in_schema=True` | test | el mismo (`/api/partes/{document_id}/recuperar` en `paths`) |
| 16 | `app:2284` `is None` → `not parsed` | equivalente | `_parse_fecha_to_iso_int` da None o una tupla de 2: nunca vacía. RM5 #6 |
| 17 | `app:2300` `is None` → `not res` | equivalente | `recuperar_parte` da None o `{"document_id", "fecha"}`: nunca vacío. RM5 #7 |
| 18 | `app:2301` `"ok": True` en el 404 | test | `…_r22_el_404_lleva_ok_false` (`{'ok': True, …} == {'ok': False, …}`) |

Ningún mutante destapó un defecto: sin cambios de producción. Los 7 equivalentes, a la aceptación del humano.
El 7 también lo caza `tests/test_f010_orm_models_gemelos.py` (raíz), que la campaña no ejecuta.

**`init.sh` tras T10** (HEAD `c38ed73` + este informe): **EXIT 0 a la primera**. Raíz 2549 passed / 50 skipped (995 s); sv4 **4147 passed** / 1 skipped (896 s); sv1-sv3, sv5 en verde por caché;
`PUERTA COBERTURA` 100,0 % (303/303); `PUERTA TAMAÑO` impl 214/220; `PUERTA CARRIL` y `CAPA E2E` N/A; ruff 1188 (deuda).

## Ciclo 2 (CHANGES_REQUESTED del reviewer de evidencias)

- `progress/mutacion_F-084.md`: los 7 análisis y las 2 declaraciones escritos (patrón de F-083), con
  enlace a RM5; `grep -c PENDIENTE` ⇒ **0** (la frase fija del generador sobre `PENDIENTE` se reescribió
  sin la palabra). El `.json` no se toca; la campaña no se relanza.
- Test 1 renombrado a `test_f084_clasificado_es_inmutable` (docstring: protege el diseño, no R7). No
  hay guardián que exija `rN` en todos los nombres (C4 pide ≥ 1 por requisito; R7 conserva los suyos).
- **RM5** `progress/equivalentes_F-084.py`: por cada equivalente, localización en su función (AST),
  dominio leído del código (AST de los `return`, tipo sin `__bool__`/`__len__` o constantes no vacías),
  mutante en memoria contra el original en N casos con bordes y un control negativo que sí distingue.
  `cd services/partes-front && python ../../progress/equivalentes_F-084.py` (47 s), **exit 0**:
```
#1 application/services/partes_con_problemas.py:144: equivalente (3 llamadores, todos bajo `not`); 5000 casos iguales; control negativo distinguido
#2 application/services/partes_con_problemas.py:174: equivalente (None o datetime, siempre verdadero); 5000 casos iguales; control negativo distinguido
#3 application/services/partes_con_problemas.py:244: equivalente (None o DocProblema, siempre verdadero); 5000 casos iguales; control negativo distinguido
#4 infrastructure/database/parte_repository.py:4910: equivalente (None o 4 constantes no vacias); 960 casos iguales; control negativo distinguido
#5 infrastructure/database/parte_repository.py:5035: equivalente (None o 3 constantes no vacias); 30 casos iguales; control negativo distinguido
#6 interface_adapters/web/app.py:2284: equivalente (None o tupla de 2, siempre verdadera); 128 casos iguales; control negativo distinguido
#7 interface_adapters/web/app.py:2300: equivalente (None o dict de 2 claves, siempre verdadero); 128 casos iguales; control negativo distinguido
7/7 equivalentes demostrados
```
- `bash harness/init.sh` (HEAD `7384a14`): **EXIT 0 a la primera** (equipo cargado). Raíz 2549 passed (3042 s); sv4 4147
  passed (3393 s); resto por caché; cobertura 303/303; impl 218/220; ruff 1206 (+18 del `.py` de RM5, no bloquea).
