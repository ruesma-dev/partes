<!-- progress/impl_F-004.md -->
# F-004 · Congelar registros aprobados — implementación

- Rama: `feature/F-004-congelar-aprobados`. **Base del diff de la feature:
  `9772ba4`** (la rama arranca de la punta de F-013, `191b6ed`, que aún no
  está en `dev`; medir contra `dev` arrastraría F-003 y F-013 y no sería
  representativo). Rigor **estandar**. sdd=true: spec aprobada por el humano
  en `specs/F-004-congelar-aprobados/`.
- Fecha: 2026-08-18. Sin `git push`, sin PR, sin tocar `dev` ni `main`.
- Servicio afectado: **solo sv4** (`services/partes-front`), como fija el
  diseño. Ni sv3, ni sv5, ni `infra/`, ni `orm_models.py` (F-010), ni
  `azure-apps/partes.md` (no cambia nada de lo que el proyecto expone o
  consume: los endpoints tocados son APIs internas del portal).
- En esta misma rama trabajó en paralelo el spec-author de F-012
  (`specs/F-012-*`, `harness/features.json`): sus commits (`f83cde8`,
  `093ee41`, `c13b524`) están intercalados con los míos y **no** son de
  F-004.

## Qué se ha hecho

Una línea del portal queda **congelada** —rechaza toda mutación de usuario—
cuando editarla dejaría la BBDD `partes` diciendo una cosa y Sigrid otra:
parte **aprobado**, `sigrid_estado='encolado'` (petición en vuelo) o
`sigrid_estado='registrado'` (ya escrita en el ERP). `omitido`, `error`,
`conflicto` y el estado vacío **siguen editables**: editarlas es justamente
el camino de arreglo.

La decisión vive en UNA función pura; la guarda se aplica en el repositorio
(dentro de la misma sesión que la mutación, sin ventana entre comprobar y
escribir) y responde **409 con motivo**; la UI refleja con candado, inputs
`disabled` y banner. La UI es cosmética: `curl` se para igual.

### Ficheros tocados

| Fichero | Qué |
|---|---|
| `services/partes-front/application/services/congelacion.py` | **NUEVO** (170 líneas). La regla: `motivo_congelacion_linea` (R1), `motivo_congelacion_documento` (R2), `exigir_*_editable`, `es_registrado`, `hay_linea_encolada`, `CongeladoError` y los textos de los motivos. Pura: ni BBDD, ni ORM, ni FastAPI. |
| `services/partes-front/infrastructure/database/parte_repository.py` | Guardas en las 9 mutaciones de usuario, filtrado+recuento en las 6 masivas, `RegistroView.congelado/congelado_motivo`, `ParteDetail.congelado_doc` y flag `"c"` en los `regs` de la matriz. |
| `services/partes-front/interface_adapters/web/app.py` | `@app.exception_handler(CongeladoError)` → 409 `{ok:false, congelado:true, error:<motivo>}`; los dos flujos de formulario redirigen con el motivo; `congeladas`/`congelados`/`omitidos` en las respuestas de las acciones masivas. |
| `services/partes-front/templates/obra_detail.html`, `trabajador_detail.html`, `parte_detail.html` | Candado 🔒 con tooltip, `disabled` en fecha/horas/trabajador/obra/código de hora, aspa de borrado oculta, banner del parte congelado y «+ Añadir línea» deshabilitado. |
| `services/partes-front/static/app.js` | No cablea editores en filas congeladas; popup de la matriz en solo-lectura para las líneas con `c` (sin Guardar ni crear extra si todas lo están); TODOS los manejadores de error muestran el motivo del 409; avisos de los recuentos de las masivas. |
| `services/partes-front/static/styles.css` | 25 líneas: fila congelada, candado, campo congelado del popup. |
| `services/partes-front/tests/test_f004_congelacion_reglas.py` | **NUEVO**. 26 tests de la matriz R1/R2 (funciones puras). |
| `services/partes-front/tests/test_f004_endpoints_congelados.py` | **NUEVO**. 79 tests de R3–R13 + R18 vía `TestClient` sobre SQLite en memoria. |
| `services/partes-front/tests/test_f004_vistas_candado.py` | **NUEVO**. 29 tests de R14/R15/R16/R17 sobre el HTML renderizado. |
| `services/partes-front/tests/dobles.py` | `sembrar_parte(...)` (documento con `approved` y `sigrid_estado` por línea, incluidas líneas en papelera) y `datos_registros(...)` (foto de lo que una edición tocaría, para probar que NO se tocó). |
| `docs/ARCHITECTURE.md` | Punto 10 de «Semántica de dominio imprescindible»: qué congela, dónde vive la regla y qué NO levanta la desaprobación. |
| `specs/F-004-congelar-aprobados/tasks.md` | T1–T8 marcadas `[x]`. |
| `progress/current.md`, `progress/impl_F-004.md`, `progress/mutacion_F-004.md` | Estado, este informe y la campaña de mutación. |

### Commits (uno por tarea, más su fase RED)

```
2c13b44  F-004 T1 (RED): tests de la matriz de congelacion — fallan por falta del modulo
c2ace84  F-004 T1: application/services/congelacion.py (regla pura R1/R2) y su matriz en verde
1cbc557  F-004 T2 (RED): tests R3/R4/R5 — hoy el portal ACEPTA editar una linea registrada
eab21bd  F-004 T2: guardas de LINEA en el repositorio y 409 con motivo en la capa web
8592041  F-004 T3 (RED): tests R6/R7/R10/R11 — hoy un parte con lineas en Sigrid se edita y se borra
a23ac1e  F-004 T3: guardas de DOCUMENTO y desaprobacion con lineas en vuelo
d059662  F-004 T4 (RED): tests R8/R9 — hoy la reasignacion pisa las congeladas y el undo las revive
50cf865  F-004 T4: reasignacion/conciliacion y undo omiten lo congelado y reportan el recuento
8f122fd  F-004 T5 (RED): tests R12/R13 — hoy el hard-delete borra la referencia a Sigrid
dc80029  F-004 T5: hard-delete bloqueado y masivos que omiten y cuentan lo registrado
e9c6226  F-004 T6 (RED): tests R14/R15/R17 — hoy la vista deja escribir lo que el servidor rechaza
0311667  F-004 T6: candado, inputs deshabilitados y banner del parte aprobado en las tres vistas
fd00e6c  F-004 T7: app.js no cablea filas congeladas, popup solo-lectura y errores con motivo
26db275  F-004 T8: tests de los caminos vacios y de las filas desaparecidas
647c532  F-004 T8: ARCHITECTURE.md, informe de implementacion y 1a campana
9157ff4  F-004 T8: tests que cazan los mutantes de 'ok' en los borrados masivos
e5950af  F-004 T8: el aviso solo para congelaciones, y tests del payload de la celda
(+ el commit de cierre con la campaña definitiva y este informe)
```

## Decisiones de diseño (y por qué)

1. **La regla, escrita UNA vez.** `application/services/congelacion.py` la
   usan las guardas del repositorio Y las vistas que pintan el candado. Si
   se escribiera dos veces, un día el portal enseñaría como editable algo
   que el servidor rechaza con un 409 —el peor de los dos mundos—. Los
   tests de R14 comprueban que el flag lo calcula el repositorio, no el JS.
2. **La guarda vive en el repositorio, no en un middleware.** La decisión
   depende de DATOS (el estado de la fila), no de la URL, y dentro del
   repositorio la comprobación va en la misma sesión que la mutación: no
   hay TOCTOU y cualquier llamador futuro la hereda sin acordarse.
3. **Prioridad de motivos: encolado > registrado > aprobado.** El texto no
   es decoración: el de una línea registrada tiene que decir que
   desaprobar el parte NO la libera (R11), y el de una encolada, que hay
   que esperar al resultado. Un test exige que los tres sean distintos.
4. **`crear_extra_desde` se guarda con la matriz COMPLETA (R1), no solo con
   `approved`.** R5 habla de documentos aprobados, pero R15 exige que el
   popup de una celda con todas sus líneas congeladas —lo que incluye una
   línea `registrado` de un parte nunca aprobado— no ofrezca crear la
   extra. Si el servidor fuera más permisivo que la UI, la única forma de
   descubrirlo sería una petición a pelo que sí colaría. Se eligió que
   servidor y UI digan lo mismo, y lo más restrictivo.
5. **El hard-delete se bloquea SOLO por `registrado`** (R12), no por toda la
   matriz: un parte aprobado sin registrar, o una línea `omitido`, no dejan
   rastro en el ERP y vaciar la papelera con ellas dentro no rompe nada. Lo
   irreparable es perder `sigrid_hmores_ide`/`sigrid_parte_cod`, la única
   referencia local a lo escrito en Sigrid. Está en su propia función
   (`es_registrado`) con el motivo escrito al lado.
6. **Las masivas omiten y CUENTAN, nunca abortan (D5).** `undo_last`, las
   cuatro reasignaciones, `vaciar_papelera`, `soft_delete_obra` y
   `soft_delete_worker` tocan N filas: abortar entero por UNA congelada las
   volvería inservibles en cuanto hubiera un mes registrado; omitir en
   silencio ocultaría que la acción fue parcial. Las firmas cambiaron a
   tuplas `(tocadas, congeladas)` y la respuesta lleva el número, que el JS
   muestra en un aviso.
7. **`doc.registros` incluye las líneas en PAPELERA** al decidir si el
   DOCUMENTO está congelado. Una línea borrada del portal puede seguir viva
   en Sigrid, y cambiar la fecha o la obra del parte propaga a todas. Hay un
   caso de test dedicado (`registrada-en-papelera`).
8. **R10 mira solo las líneas ACTIVAS.** Una `encolado` en la papelera no
   tiene petición en vuelo que esperar; bloquear la desaprobación por ella
   dejaría el parte atrapado para siempre.
9. **Las escrituras del SISTEMA no se congelan jamás.**
   `marcar_registros_encolado` y `marcar_registros_sigrid` son la traza del
   registro, no ediciones de usuario: si la guarda las alcanzara, ninguna
   línea podría pasar de `encolado` a `registrado` y el pipeline entero se
   rompería. Hay un test explícito (R18) que lo fija.
10. **El JS deja de tragarse los errores.** `applyPartidaToIds` ni siquiera
    miraba el estado de la respuesta: un rechazo del servidor acababa en un
    `reload()` que fingía éxito. Ahora todos los caminos pasan por
    `MotivoHttp.lanzarSiFalla` y enseñan el motivo real (R16). El error que
    lanza ese helper trae `congelado`, para distinguir «el sistema dice que
    NO» —que se enseña con un aviso, porque el usuario no lo espera y tiene
    que saber qué hacer— de un fallo de red, que se queda en el aviso
    discreto de siempre (borde rojo + tooltip) para no volverse molesto.
11. **Coste de las guardas: valorado y aceptado.** Decidir si una línea está
    congelada exige mirar `reg.document.approved`, y en las masivas eso es
    una carga perezosa por fila (N+1) cuando el `selectinload` no está
    puesto. Se dejó así a propósito: las listas que llegan a
    `_separar_congeladas` ya vienen filtradas (las líneas de UN trabajador o
    de UN nombre leído) y **todas esas filas se van a escribir a
    continuación**, así que el viaje extra es marginal frente al UPDATE.
    Meter `selectinload` en las cinco consultas sería una micro-optimización
    con riesgo cero de comportamiento; queda anotada por si alguna vez se
    ven listas grandes, no se hizo aquí para no mezclarla con la feature.
12. **Sin cambios de schema** (D4): `parte_documents.approved*` +
    `parte_registros.sigrid_estado` bastan. No se tocó `orm_models.py` en
    NINGUNA de sus dos copias, así que el duplicado sv3/sv4 sigue idéntico.

## Fase RED (obligatoria en rigor estandar)

Los tests de los requisitos centrales se escribieron **antes** que el
código y se ejecutaron en rojo; cada rojo tiene su commit propio para que
se pueda comprobar en el historial.

### T1 · la regla (R1/R2) — commit `2c13b44`

```
$ cd services/partes-front && python -m pytest tests/test_f004_congelacion_reglas.py -q --tb=short
=================================== ERRORS ====================================
___________ ERROR collecting tests/test_f004_congelacion_reglas.py ____________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\partes\services\partes-front\tests\test_f004_congelacion_reglas.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f004_congelacion_reglas.py:15: in <module>
    from application.services.congelacion import (
E   ModuleNotFoundError: No module named 'application.services.congelacion'
=========================== short test summary info ===========================
ERROR tests/test_f004_congelacion_reglas.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.20s
```

### T2 · el rechazo en el servidor (R3) — commit `1cbc557`

Este es **el rojo que enseña el bug**: hoy el portal acepta con un `200 OK`
la edición de una línea ya registrada en Sigrid.

```
$ cd services/partes-front && python -m pytest "tests/test_f004_endpoints_congelados.py::test_f004_r3_patch_horas_de_linea_congelada_responde_409" -q --tb=short
FFF                                                                      [100%]
================================== FAILURES ===================================
___ test_f004_r3_patch_horas_de_linea_congelada_responde_409[doc-aprobado] ____
tests\test_f004_endpoints_congelados.py:150: in test_f004_r3_patch_horas_de_linea_congelada_responde_409
    _congelado(cliente.patch(f"/api/registros/{ids[0]}", json={"horas": 3.0}))
tests\test_f004_endpoints_congelados.py:109: in _congelado
    assert respuesta.status_code == 409, respuesta.text
E   AssertionError: {"ok":true,"registro_id":1}
E   assert 200 == 409
E    +  where 200 = <Response [200 OK]>.status_code
__ test_f004_r3_patch_horas_de_linea_congelada_responde_409[linea-encolada] ___
    ... (idéntico)
_ test_f004_r3_patch_horas_de_linea_congelada_responde_409[linea-registrada] __
    ... (idéntico)
3 failed in 1.61s
```

Ese mismo rojo cubrió R4 y R5: 18 fallos en la primera ejecución del fichero
(`18 failed, 9 passed`), incluidos `DID NOT RAISE CongeladoError` en la
prueba que llama al repositorio directamente.

### T3 · documentos y desaprobación (R7/R10) — commit `8592041`

```
$ cd services/partes-front && python -m pytest "tests/test_f004_endpoints_congelados.py::test_f004_r7_papelera_de_documento_congelado_no_borra_y_avisa" -q --tb=short
_ test_f004_r7_papelera_de_documento_congelado_no_borra_y_avisa[doc-aprobado] _
tests\test_f004_endpoints_congelados.py:352: in test_f004_r7_papelera_de_documento_congelado_no_borra_y_avisa
    assert _doc(fabrica).is_active is True
E   assert False is True
E    +  where False = <infrastructure.database.orm_models.ParteDocumentOrm object at 0x...>.is_active
```

(14 fallos en total: R6 fecha/obra en 409, R7 en las cuatro variantes de
documento congelado, R10 y R11.)

### T4 · masivas y undo (R8/R9) — commit `d059662`

```
$ cd services/partes-front && python -m pytest tests/test_f004_endpoints_congelados.py -q --tb=short -k "r8_la_conciliacion or r9_el_undo_no_revive"
_______ test_f004_r8_la_conciliacion_omite_las_congeladas_y_lo_reporta ________
tests\test_f004_endpoints_congelados.py:482: in test_f004_r8_la_conciliacion_omite_las_congeladas_y_lo_reporta
    assert cuerpo["updated"] == 1
E   assert 2 == 1
___________ test_f004_r9_el_undo_no_revive_una_linea_hoy_registrada ___________
tests\test_f004_endpoints_congelados.py:554: in test_f004_r9_el_undo_no_revive_una_linea_hoy_registrada
    assert cuerpo["omitidos"] == 1
           ^^^^^^^^^^^^^^^^^^
E   KeyError: 'omitidos'
2 failed, 56 deselected in 2.44s
```

El `2 == 1` es el bug: la conciliación reasignaba también la línea ya
registrada en Sigrid.

### T5 · hard-delete y masivos (R12/R13) — commit `8f122fd`

```
$ cd services/partes-front && python -m pytest tests/test_f004_endpoints_congelados.py -q --tb=short -k "r12_hard_delete_de_linea_registrada or r13_borrar_al_trabajador"
_________ test_f004_r12_hard_delete_de_linea_registrada_responde_409 __________
    _congelado(cliente.post(f"/api/registro/{ids[0]}/hard-delete"))
E   AssertionError: {"ok":true}
E   assert 200 == 409
_______ test_f004_r13_borrar_al_trabajador_omite_las_lineas_congeladas ________
    assert cuerpo["lineas"] == 1
E   assert 2 == 1
2 failed, 67 deselected in 3.03s
```

### T6 · las vistas (R14/R15/R17) — commit `e9c6226`

```
$ cd services/partes-front && python -m pytest tests/test_f004_vistas_candado.py -q --tb=short -k "r14_el_flag or (r14_la_linea_congelada and registrada and obra)"
___ test_f004_r14_la_linea_congelada_sale_bloqueada[linea-registrada-obra] ____
tests\test_f004_vistas_candado.py:88: in test_f004_r14_la_linea_congelada_sale_bloqueada
    assert 'data-congelado="1"' in fila
E   assert 'data-congelado="1"' in 'data-registro-id="1" data-document-id="doc-f004" ... '
_______________ test_f004_r14_el_flag_lo_calcula_el_repositorio _______________
tests\test_f004_vistas_candado.py:129: in test_f004_r14_el_flag_lo_calcula_el_repositorio
    congelados = {v.id: (v.congelado, v.congelado_motivo)
                         ^^^^^^^^^^^
E   AttributeError: 'RegistroView' object has no attribute 'congelado'
2 failed, 23 deselected in 3.16s
```

(20 fallos en total sobre las tres vistas.)

## Cobertura de los requisitos (R1–R18)

| R | Test(s) |
|---|---|
| R1 | `test_f004_r1_*` (11) en `test_f004_congelacion_reglas.py`: matriz completa, prioridad de motivos, normalización del estado. |
| R2 | `test_f004_r2_*` (7): documento aprobado, una sola línea en Sigrid, prioridad, normalización, guarda. |
| R3 | `test_f004_r3_*` (12): los tres endpoints × las tres condiciones de congelación, motivo distinto por caso, línea libre intacta, 404 sigue siendo 404. |
| R4 | `test_f004_r4_*` (4): papelera de línea congelada → 409 y sigue activa; línea libre se borra. |
| R5 | `test_f004_r5_*` (5): crear extra → 409 y no se crea la línea; el repositorio también se niega. |
| R6 | `test_f004_r6_*` (9): fecha y obra × las 4 formas de documento congelado, sin re-casar partidas; documento libre editable. |
| R7 | `test_f004_r7_*` (5): redirección con mensaje, documento no borrado; documento libre sí. |
| R8 | `test_f004_r8_*` (9): conciliación y las cuatro variantes de reasignación, recuento, caso «todas congeladas», caminos vacíos. |
| R9 | `test_f004_r9_*` (5): undo de línea hoy registrada, mezcla, documento congelado, filas desaparecidas, undo normal. |
| R10 | `test_f004_r10_*` (3): línea en vuelo rechaza; en papelera no bloquea; parte inexistente. |
| R11 | `test_f004_r11_*` (3): libera lo no registrado, mantiene lo registrado, el documento sigue congelado. |
| R12 | `test_f004_r12_*` (7): hard-delete de línea y de documento, vaciar papelera (documento y línea suelta), casos libres, ids inexistentes. |
| R13 | `test_f004_r13_*` (4): obra y trabajador con congelados, otra obra intacta, sin congelados. |
| R14 | `test_f004_r14_*` (13): las tres vistas × las tres condiciones, línea libre sin candado, motivo en el tooltip, convivencia, flag calculado en el repositorio. |
| R15 | `test_f004_r15_*` (2): flag `c` en los `regs` de la celda, y ausencia cuando no hay congeladas. |
| R15 (bis) | `test_f004_r15_la_celda_sigue_llevando_horas_tipo_y_partida` y `..._no_inventa_valores`: el flag `c` se añadió a un payload que ya existía y ahora está fijado entero (`id`, `t`, `h`, `p`). |
| R16 | `test_f004_r16_el_front_lee_el_motivo_del_409` (estático sobre `app.js`) + `test_f004_r3_el_motivo_del_409_distingue_el_caso` (el contrato que el front consume). El comportamiento en el navegador es verificación MANUAL: el proyecto no tiene arnés de tests JS. |
| R17 | `test_f004_r17_*` (3): banner + fecha/obra/«+ Añadir línea» bloqueados; parte pendiente sin bloqueos; parte sin aprobar con línea en Sigrid también avisa. |
| R18 | `test_f004_r18_*` (7): aprobar/desaprobar/reaprobar siguen funcionando, la traza del sistema no se congela, restaurar de papelera permitido, undo y masivas sin congelados idénticos a antes, botones Aprobar/↻/Revisar presentes. Y las suites de F-002/F-003/F-013, intactas. |

## Verificación

### `bash harness/init.sh` (entero, en verde)

Última ejecución (2026-08-18, tras cerrar T8):

```
[OK] Arnés v1.4.0 (2026-08-13)
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 450 avisos (deuda previa, no bloquea)
[OK] pytest en verde (con medición de cobertura)        # 6 tests de la raíz
[OK] servicio sv3-persistencia: pytest en verde (caché)
448 passed, 5 warnings in 65.47s (0:01:05)
[OK] servicio sv4-front (services/partes-front): pytest en verde
[OK] servicio sv5-transfer: pytest en verde (caché)
[OK] PUERTA COBERTURA: 96.7% de 1067 líneas cambiadas cubiertas (1032/1067, umbral 80%, nivel estandar)
[OK] Rama actual: feature/F-004-congelar-aprobados
ENTORNO LISTO. Puedes trabajar.
```

Los cinco `warnings` son el `StarletteDeprecationWarning` de `TestClient`
(previo) y los tres `SAWarning` que se explican al final de este informe.

**ruff sigue en 450 avisos, los mismos que antes de F-004** (medido contra
`9772ba4`): la feature no añade ni uno. Sobre los ficheros nuevos, ruff sale
limpio:

```
$ python -m ruff check services/partes-front/application/services/congelacion.py services/partes-front/tests/test_f004_*.py services/partes-front/tests/dobles.py --output-format=concise
All checks passed!
```

Nota de estilo: los tres ficheros de test siguen el bloque de imports único
de las suites F-002/F-003/F-013 (limpio ejecutando ruff **desde la raíz**,
que es como lo mide `init.sh`). Ejecutado desde `services/partes-front/`, la
detección de first-party cambia y ruff pide otro agrupado —le pasa igual a
`test_f003_r2_vistas_festivos.py` y a `test_f013_informe_sesame.py`—; se
eligió la forma que deja el contador del arnés donde estaba.

### JavaScript y plantillas

```
$ node --check services/partes-front/static/app.js
(sin salida: OK)
```

Las tres plantillas las parsea Jinja2 en cada test de vistas (26 tests que
renderizan `obra_detail`, `trabajador_detail` y `parte_detail` con
`TestClient`): un error de sintaxis Jinja las tumbaría todas.

## Evidencias

| Evidencia | Valor real |
|---|---|
| **Tests ejecutados** | **448 passed, 0 failed** en la suite de sv4 (**134 nuevos** de F-004: 26 de la regla + 79 de los endpoints + 29 de las vistas). Más 6 en la suite de la raíz y sv3/sv5 en verde. |
| **Cobertura de las líneas cambiadas** | **100,0 % (183/183)** midiendo solo el diff de F-004 (`python -m harness.cobertura --base 9772ba4`). Umbral 80 %. La puerta de `init.sh` contra `dev` da **96,7 % (1032/1067)** porque arrastra F-003 y F-013, que aún no están en `dev`. |
| **Mutantes generados y supervivientes** | **54 generados, 54 evaluados, 53 muertos, 1 superviviente, 0 timeouts** (678,9 s). Informe: `progress/mutacion_F-004.md`. |
| **Tiempo de ejecución de la suite** | sv4 completa: **46,08 s** (448 tests); dentro de `init.sh`, con medición de cobertura, **65,47 s**. Solo los tests de F-004: **20,84 s** (134 tests). |

### Análisis del superviviente

El único que queda es **equivalente y está justificado por escrito** en
`progress/mutacion_F-004.md` (ninguna sección en `PENDIENTE`):
`app.py:929`, `congeladas = 0` → `congeladas = 1`. Es la inicialización de
una variable que los cuatro caminos que llegan a la respuesta reasignan
siempre; los otros dos caminos salen por un 400 o un 500 que no llevan ese
campo. No hay ejecución que distinga 0 de 1. Se mantiene la inicialización
a propósito: sin ella, un quinto selector futuro que olvidara asignarla
produciría un `NameError` en producción en vez de un dato malo visible.

**Las tres campañas y qué destaparon** (los números de arriba son los de la
tercera y definitiva):

| Campaña | Ajustes | Resultado |
|---|---|---|
| 1ª | por defecto (16 workers, 120 s) | 36 muertos, 5 supervivientes, **13 timeouts** |
| 2ª | `--workers 4 --timeout 400` | 49 muertos, 5 supervivientes, 0 timeouts |
| 3ª (definitiva) | `--workers 4 --timeout 400`, con los tests nuevos | **53 muertos, 1 superviviente, 0 timeouts** |

Los 13 timeouts de la primera **no eran mutantes indestructibles**: con 16
evaluadores compitiendo por la misma máquina, la suite (≈46 s en solitario)
no cabía en los 120 s por mutante y el veredicto se quedaba sin emitir. Con
4 evaluadores y 400 s los 54 mutantes tienen veredicto real. Queda dicho
porque un timeout NO es un mutante muerto: es una casilla vacía.

Los **cuatro supervivientes que sí eran huecos reales** se taparon con
tests, y esos huecos merecían serlo:

1. **`{"ok": n > 0}` en `/api/obra/{key}/delete`** (mutado a `n >= 0` y a
   `n > 1`). Ningún test miraba `ok`, y ese campo es el que decide si el
   front navega a `/obras` dando el borrado por hecho. Con todos los partes
   congelados, un `ok` erróneo dejaría al usuario mirando una lista donde la
   obra sigue viva. Test:
   `test_f004_r13_si_toda_la_obra_esta_congelada_la_respuesta_no_dice_ok`.
2. **Lo mismo en `/api/trabajador/{key}/delete`**. Test:
   `test_f004_r13_si_todas_las_lineas_estan_congeladas_no_dice_ok`.
3. **El payload de la celda de la matriz** (`"h": reg.horas or 0.0` mutado a
   `and`, y las dos variantes de `"p"`). Al mover ese diccionario a
   `_reg_de_celda` para colgarle el flag `c`, nada comprobaba que `h`, `t` y
   `p` siguieran llegando bien: el popup habría abierto con las horas a cero
   —y el usuario habría guardado ese cero encima de lo bueno—. Tests:
   `test_f004_r15_la_celda_sigue_llevando_horas_tipo_y_partida` y
   `test_f004_r15_una_linea_sin_partida_ni_horas_no_inventa_valores`.
4. **El valor por defecto de `RegistroView.congelado`** (mutado a `True`).
   Los tests de F-003 construyen `RegistroView` a mano para
   `extras_por_jornada`: con el defecto invertido, cualquier vista
   construida fuera de `_registro_view` saldría bloqueada sin haberlo
   pedido. Test:
   `test_f004_r14_un_dto_construido_a_mano_no_sale_congelado`.

## Verificaciones MANUAL pendientes (del humano)

Todas necesitan el portal levantado en local contra la BBDD real y, para lo
de Sigrid, sv5 en **modo pruebas** (`OBRA_PRUEBAS_FORZAR=true`, obra 0404,
marca `PRUEBA-IA`). **Ctrl+F5** en cada pantalla: `app.js` y `styles.css`
han cambiado y el navegador cachea.

1. **Parte aprobado (R17).** Abrir `/partes/<id>` de un parte aprobado.
   Esperado: banner 🔒 arriba con «Parte aprobado: márcalo pendiente…»,
   fecha y obra deshabilitadas, «+ Añadir línea» gris, y en cada línea el
   candado en vez del aspa, con horas y código de hora bloqueados. Pulsar
   «Marcar pendiente» debe devolver todo a editable.
2. **Línea registrada (R3, R11, R16).** En `/obras/<obra>` con un mes ya
   registrado: la fila `✓ PT…` sale con candado; pasar el ratón por él debe
   explicar que corregirla exige actuar en Sigrid. Comprobar además que el
   servidor manda, con el portal abierto:
   ```
   curl -i -X PATCH http://localhost:8000/api/registros/<id> \
        -H "Content-Type: application/json" -d "{\"horas\": 1}"
   ```
   Esperado: `HTTP/1.1 409` y `{"ok":false,"congelado":true,"error":"Linea ya registrada en Sigrid…"}`.
3. **Línea encolada (R10).** Encolar una obra×mes («Aprobar todo») y, antes
   de que llegue el resultado, intentar «Marcar pendiente» en uno de sus
   partes. Esperado: NO se desaprueba y el mensaje explica que la petición
   está en vuelo. Al llegar el resultado, las líneas pasan a `registrado` y
   el parte ya se puede marcar pendiente (sus líneas registradas siguen con
   candado).
4. **Matriz (R15).** Doble clic en una celda de un día ya registrado:
   las filas salen en gris con 🔒, no hay botón «Guardar» y no se ofrece
   crear la línea extra. En una celda libre, el popup funciona como
   siempre.
5. **Masivas (R8, R13).** Con un mes registrado, «Borrar persona» o
   «Borrar obra» y una reasignación de trabajador: deben avisar de cuántas
   líneas/partes se han omitido, y esos elementos deben seguir ahí.
6. **Papelera (R12).** Con una línea registrada en la papelera, «Vaciar
   papelera» debe avisar de cuántos elementos se quedan y no borrarlos.
7. **No regresión (R18).** Sobre líneas `omitido`/`error`/`conflicto`, los
   botones ↻ / Revisar / Aprobar siguen ahí y siguen funcionando; una línea
   sin registrar se sigue editando con normalidad.

## Qué queda fuera (no es de esta feature)

- Propagar ediciones a Sigrid (update/delete de `hmores` desde el portal).
  Si algún día se quiere «anular en Sigrid desde el portal», es una feature
  nueva con su spec: aquí se descartó expresamente (D3).
- Aprobación POR LÍNEA y roles/permisos (F-008).
- Resincronizar `orm_models.py` (F-010) y corregir el §5.2 del documento
  maestro `docs/referencia/partes-proyecto.md`, que lista `approved*` en
  `parte_registros` cuando ninguna de las dos copias del ORM la tiene. La
  granularidad por línea la da `sigrid_estado`; queda anotado para F-010.
- Reparar el pasado: la feature congela desde su despliegue; una línea
  registrada y editada ANTES de F-004 puede estar ya desincronizada y esto
  no lo detecta ni lo arregla.
- Desplegar (`redeploy_partes.ps1`): lo pide el humano.

## Avisos observados (no son regresiones)

Tres `SAWarning: DELETE statement on table 'parte_registros' expected to
delete 1 row(s); 0 were matched` en los tests de hard-delete de documento y
de vaciar papelera. Vienen de código **anterior** a F-004
(`hard_delete_document`/`vaciar_papelera` hacen un `DELETE` masivo de las
líneas y después `session.delete(doc)`, con lo que la cascada del ORM
intenta borrar filas que ya no están). No los provoca la feature: los saca
a la luz porque hasta ahora ningún test recorría esos caminos. Limpiarlo
—`passive_deletes` o borrar solo por la relación— toca `orm_models.py`, que
esta feature no puede modificar (F-010). Anotado ahí.
