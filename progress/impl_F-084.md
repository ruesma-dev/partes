# F-084 · Informe del implementer (nivel `critico`)

Rama `feature/F-084-partes-con-problemas` (copia `partes-wt-f084`). Alcance del encargo: T1–T9
y T12. **Fuera**: T10 (campaña de mutación, la lanza el líder tras el reviewer principal) y T11
(manual M1–M3, tras desplegar).

## Qué cambió

- **sv3** (`sqlalchemy_parte_repository.py`): `_deactivate_same_day_obra` gana `email_id` y, al
  desactivar, escribe `sustituido_por_id` (id del nuevo) y `sustituido_at_utc` (UTC ISO) en el
  viejo, en la misma sesión que guarda el nuevo (un solo commit), sin tocar `deleted_*`. Si los dos
  tienen el mismo `email_id` no vacío, WARNING
  `[parte-repo] reemplazo del mismo envio: <nuevo> sustituye a <viejo> (fecha_int=… obra=…)`. La
  condición del reemplazo (`_emp_signals`, `_misma_entrada`) no se toca; el INFO de siempre sigue.
- **Esquema**: las dos copias de `orm_models.py`, byte-idénticas, con el bloque de design §3.
  `ddl_complementario()` genera los dos `ADD COLUMN IF NOT EXISTS` sin tocar su código.
  Ningún test de F-010 enumera las columnas de `parte_documents`: no ha hecho falta ajustarlos (T1).
- **sv4 · módulo puro** `application/services/partes_con_problemas.py`: constantes de motivo,
  `ORDEN_MOTIVOS`, `NO_CUENTAN`, `TEXTOS`, `DocProblema`, `es_sustituido`, `motivos_activo`,
  `fecha_posterior_al_correo`, `elegir_sustituto`, `motivo_sustituido`, `mismo_envio`,
  `cuenta_para_aviso`, y además `Clasificado`, `clasificar`, `resumen`, `motivo_no_recuperable`,
  `NoRecuperableError` y `ChoqueRecuperarError`.
- **sv4 · repositorio** (`parte_repository.py`): `list_partes_con_problemas`, `resumen_problemas`
  (los dos salen de `_problemas`: una consulta y la misma clasificación), `recuperar_parte`,
  `_choques`, `_misma_obra_docs`, `_deshacer_reactivados`; `_record_undo` gana `reactivados` y
  `actor`; `undo_last` desactiva lo recuperado en `parte_recuperar`.
- **sv4 · portal** (`app.py`): `GET /problemas`, `GET /api/problemas/resumen`,
  `POST /api/partes/{id}/recuperar` (todas `include_in_schema=False`); la rama de deshacer de
  `parte_fecha` cubre también `parte_recuperar` con `MOTIVO_DESHACER_RECUPERAR`.
  `recalculo_publisher.py`: `MOTIVO_RECUPERAR_PARTE`, `MOTIVO_DESHACER_RECUPERAR`.
- **Plantillas y estáticos**: `templates/problemas.html` (nuevo), enlace «Problemas» con
  `#problemas-badge` en `base.html` entre «Conciliar» y «Partes», `wireProblemasBadge`,
  `wireRecuperar` y `parte_recuperar: "Recuperar parte"` en `app.js`, `.nav-badge` e insignias de
  motivo en `styles.css`.
- **Documentación**: `docs/ARCHITECTURE.md` (semánticas 7 y 8). `azure-apps/partes.md`, commit
  aparte **`e09fd49`** en `main` de `azure-apps` (`git pull --rebase` antes: «Already up to date»,
  sin conflicto; **sin push**): nota F-084 de cabecera, §3.3 (rastro), §3.4 (pestaña y rutas),
  §4.1 (fila nueva y nota de Papelera), §4.5 y el párrafo de `undo_log.actor`.

## Ficheros

Crear: `services/partes-front/application/services/partes_con_problemas.py`,
`services/partes-front/templates/problemas.html` y los cuatro tests
(`services/partes-persistencia/tests/test_f084_rastro_reemplazo.py`,
`services/partes-front/tests/test_f084_clasificacion.py`, `…/test_f084_recuperar.py`,
`…/test_f084_portal.py`).
Modificar: los dos `orm_models.py`, `sqlalchemy_parte_repository.py` (sv3), `parte_repository.py`,
`app.py`, `recalculo_publisher.py`, `base.html`, `app.js`, `styles.css` (sv4),
`docs/ARCHITECTURE.md`, `progress/current.md`, `specs/F-084-partes-con-problemas/tasks.md`.

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
(Los 3 en verde: descartar con `back=/problemas` y descartar un congelado, que ya funcionaban con la
ruta de siempre (R26 reutiliza `delete_document`), y «sin visor no hay Ver PDF».)

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

Segunda pasada (HEAD `1316ce4`), **EXIT 0, sin comprobaciones fallidas**:
```
[OK] pytest en verde (con medición de cobertura)      2549 passed, 50 skipped (raíz, 33 min)
[OK] servicio sv1/sv2/sv3/sv5: pytest en verde (caché del verde de la primera pasada)
[OK] servicio sv4-front: pytest en verde               4137 passed, 1 skipped (26 min)
[OK] PUERTA COBERTURA: 100.0% de 303 líneas cambiadas cubiertas (303/303, umbral 90% (del nivel critico))
[OK] PUERTA TAMAÑO: F-084 dentro de los topes (requirements 144/150, design 249/250, impl …/220)
[OK] PUERTA CARRIL: N/A (F-084 es de nivel critico: no declara límites)
[OK] CAPA E2E: N/A (ningún servicio declara el bloque e2e)
[AVISO] ruff: 1188 avisos (deuda previa, no bloquea)
```
**Primera pasada en rojo** (HEAD `3536271`), tres causas, las tres resueltas en `1316ce4`:
1. sv4 `test_f017_punto_unico.py::test_f017_todos_los_puntos_de_escritura_usan_el_helper`:
   `assert 24 == 23`. La ruta nueva de recuperar firma con `_actor(request)` (R17, R18).
2. sv4 `test_f047_portal_parte_nuevo.py::test_f047_r23_ninguna_funcion_nueva_y_una_sola_variable`:
   `assert ((322 - 17) - 1) == 301`. Las tres funciones nuevas de `app.js` (design §8).
3. raíz `test_f059_ejecucion.py::test_f059_r9_timeout_mata_el_arbol_y_no_es_rojo`
   (`FileNotFoundError ... nieto.pid`): de la familia inestable conocida de F-059 (caso r9, no el r7
   que nombraba el encargo). Coincidió con una medición de cobertura que lancé en paralelo; en la
   segunda pasada, sin carga extra, pasó. La cobertura del 35 % de esa pasada era efecto del `-x`
   de sv4: sus tests de F-084 no llegaron a correr.

**Desviación justificada (para el reviewer)**: los arreglos 1 y 2 tocan dos guardianes de otras
features. Uso el mecanismo que ya siguieron F-042, F-052, F-056 y F-068: subir la cuenta
documentando la llamada nueva (24) y descontar las funciones nuevas en una tupla propia
(`F084_PROBLEMAS`), sin tocar lo que vigilan. Las dos cosas que cuentan las pide la spec
aprobada (R17 «con actor»; design §8, `wireProblemasBadge` y el botón `data-recuperar`).

## Pendiente

- **T10** (líder): `python -m harness.mutacion --feature F-084`, tras el APPROVED del reviewer.
- **T11** (humano, tras desplegar sv3 y sv4): M1–M3 de design §12; M3 solo con OK expreso.
- **Push** (humano): rama de la feature y `azure-apps` (`e09fd49`): `git pull` y luego `git push`.
- Capa e2e: ningún requisito lleva `(capa: e2e)`; lo dice la línea `CAPA E2E` de abajo.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | raíz 2549 passed / 50 skipped; sv4 4137 passed / 1 skipped; sv3 2966 passed / 2 skipped; sv1 74; sv2 579 / 1 skipped; sv5 1890 / 1 skipped: **0 fallos** |
| Tests nuevos de F-084 | sv3 12 (`test_f084_rastro_reemplazo.py`); sv4 43 + 34 + 27 = 104 (clasificación, repositorio, portal) |
| Cobertura de las líneas cambiadas | **100,0 %** (303/303; umbral 90 % del nivel `critico`), línea `PUERTA COBERTURA` |
| Mutantes generados / supervivientes | **No lanzada** en este encargo: T10, la lanza el líder tras el APPROVED del reviewer principal (`python -m harness.mutacion --feature F-084`) |
| Tiempo de la suite | raíz 1995 s (33:15, con cobertura); sv4 1579 s (26:19); sv3 131 s (primera pasada) |
| Capa e2e | N/A: `CAPA E2E: N/A (ningún servicio declara el bloque e2e)`; ningún requisito lleva `(capa: e2e)` |
