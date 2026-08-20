<!-- progress/impl_F-017.md -->
# F-017 · Identidad real de Easy Auth en el portal (sv4) — Informe de implementación

Rama: `feature/F-017-identidad-easy-auth` (desde `dev`, `3d6fd7e`).
Rigor: **`estandar`** ⇒ fase RED obligatoria para R1, R5, R5b, R10, R12 y R16;
cobertura de líneas cambiadas ≥ 80 %; campaña de mutación con supervivientes
analizados uno a uno.

---

## T0 (PUERTA) · Confirmación de la señal de despliegue (R5c) — **PASA**

La verificación **M1 bis** de `requirements.md` §4 era la puerta bloqueante de
esta feature: `design.md` §4.1 marcaba la señal A como **supuesto de
plataforma no verificado en este repositorio** (ningún servicio del monorepo
lee esas variables y ningún script de `infra/` las declara).

**Resultado: las cuatro variables existen en el contenedor desplegado.**

| Variable de `VARIABLES_DESPLIEGUE` | ¿Presente en `ca-sv4-front`? |
|---|---|
| `CONTAINER_APP_NAME` | **Sí** |
| `CONTAINER_APP_REVISION` | **Sí** |
| `CONTAINER_APP_REPLICA_NAME` | **Sí** |
| `CONTAINER_APP_HOSTNAME` | **Sí** |

Contenedor: `ca-sv4-front` en `rg-partes-dev`, revisión activa a 2026-08-20.
**Los valores no se transcriben aquí** (T0 pide nombres sin valores).

### Cómo se comprobó, y por qué no con el comando de la spec

El comando literal de `tasks.md` T0 vuelca **todo** el entorno del contenedor
y filtra *en el cliente*. Eso expondría los secretos resueltos desde Key Vault
(`GRAPH_KEY`, `PG-PASSWORD`, la credencial de Sigrid). **No se ejecutó así.**

Primer intento, con el filtro **dentro** del contenedor:

```
az containerapp exec -n ca-sv4-front -g rg-partes-dev \
  --command "sh -c 'printenv | grep CONTAINER_APP'"
```

Conecta a la réplica y falla al ejecutar:

```
INFO: Successfully connected to container: 'ca-sv4-front'. [ Revision: ... ].
WARNING: Disconnecting...
ERROR: {"Error":{"Code":"ClusterExecFailure","Message":"Cluster exec API
returns error: Internal error occurred: error executing command in container:
websocket: close 1011 (internal server error): ... Cannot attach to a
container that is not running. ..., code: 500.", ...}}
```

Causa: el comando compuesto con comillas anidadas no sobrevive al transporte
del `exec`. Se descartó reintentar variantes de *quoting* del pipe: si el
entrecomillado se rompe, el comando degenera en `printenv` a secas y vuelca los
secretos. **Riesgo asimétrico, no se corre.**

Vía usada, una variable por invocación — no puede volcar nada más que la
variable nombrada:

```
az containerapp exec -n ca-sv4-front -g rg-partes-dev --command "printenv CONTAINER_APP_NAME"
az containerapp exec -n ca-sv4-front -g rg-partes-dev --command "printenv CONTAINER_APP_REVISION"
az containerapp exec -n ca-sv4-front -g rg-partes-dev --command "printenv CONTAINER_APP_REPLICA_NAME"
az containerapp exec -n ca-sv4-front -g rg-partes-dev --command "printenv CONTAINER_APP_HOSTNAME"
```

Las cuatro devuelven valor no vacío y `INFO: received success status from
cluster`. Ningún secreto ha pasado por el chat, por el informe ni por un commit.

**Consecuencia para el diseño**: la señal A de R5c es un **hecho verificado en
este despliegue**, no un supuesto. No hace falta la alternativa
`ENTORNO=produccion` de `design.md` §4.1 (que habría obligado a tocar Azure y
a consultar al humano). La señal B se implementa igualmente como red de
seguridad, tal y como manda §4.1: cubre el caso de que la plataforma deje de
inyectarlas en el futuro.

Interacción con Azure en toda la feature: **solo estas cuatro lecturas**.

---

## T1 · Punto de partida e inventario de rojos

Suite de sv4 sobre la rama recién creada, sin tocar nada:

```
$ python -m pytest services/partes-front/tests -q
799 passed, 1 warning in 54.37s
```

`bash harness/init.sh` de arranque: en verde (92 tests en la raíz, 4.07 s;
puerta de cobertura `N/A` porque la rama aún no cambia líneas Python).

### Las doce lecturas de `settings.default_reviewer` en `app.py`

Confirmada la tabla de `design.md` §5.2 contra el árbol (líneas del 2026-08-20):

| Punto | Línea | Contexto |
|---|---|---|
| dentro de `_actor` | 490 | la única que debe sobrevivir (R11) |
| 1 | 1675 | `_payload_registro` → campo `usuario` |
| 2 | 1769 | `_trazar` → `usuario=` |
| 3 | 1804 | `aprobar_ejecutar`, log de forzado (R17) |
| 4 | 1859 | `aprobar_encolar` → `publisher.publicar(usuario=)` |
| 5 | 1862 | `aprobar_encolar` → `marcar_registros_encolado(usuario=)` |
| 6 | 2279 | `approve_document` → `approved_by=` |
| 7 | 2305 | `delete_document` → `deleted_by=` |
| 8 | 2319 | `api_registro_delete` → `by=` |
| 9 | 2338 | `api_obra_delete` → `by=` |
| 10 | 2348 | `api_trabajador_delete` → `by=` |
| 11 | 2559 | `api_partes_nuevo` → `by=` |

Once fuera del helper, exactamente lo que anunciaba la spec.

### Tests candidatos a ponerse rojos

Revisados por lectura los siete ficheros que `design.md` §6 señalaba como
«rondan la zona». **La distinción que decide** es si el test llega al valor
*a través de una petición HTTP* (el TestClient no manda cabeceras de Easy
Auth ⇒ caerá al fallback) o si llama al repositorio / al consumidor
directamente (no pasa por `_actor` ⇒ intacto).

| Test | Predicción | Motivo |
|---|---|---|
| `test_f002_aprobar_encolar.py:101` (`assert usuario == "ana"`) | **ROJO** | El valor llega por `POST /api/aprobar/encolar` ⇒ pasará a `local:ana` |
| `test_f016_r13_auditoria` | **ROJO** | La trampa anunciada en `design.md` §6: espera `quien-firma`, obtendrá `local:quien-firma` |
| `test_f016_r13_sin_default_reviewer_se_sella_nulo_y_no_falla` | **ROJO** | Espera `NULL`; con R7 ya nunca hay `NULL` ⇒ `local:sin-identidad` |
| `test_f016_r13_la_identidad_se_resuelve_en_un_solo_sitio` | **VERDE** (y es el guardián) | Compara textos que el diseño respeta; si se pone rojo, se rompió el punto único |
| `test_f002_mutantes.py:429` (`sigrid_registrado_by == "revisor-por-defecto"`) | VERDE | Es el **consumidor de resultados** (R18), sin petición HTTP: toma el usuario del sobre y su `Settings` es un doble |
| `test_f002_degradacion.py`, `test_f002_credenciales_y_arranque.py`, `test_f002_resultado_consumer.py`, `test_f002_publisher.py` | VERDE | `Settings` dobles y llamadas directas al repositorio/publisher |
| `test_f003_r23_bloqueo_registro.py`, `test_f004_endpoints_congelados.py` | VERDE | Ponen `DEFAULT_REVIEWER=ana` en el entorno pero **no asertan sobre quién firma** |

Comprobado además que **ningún test comprueba el texto del log de forzado**
(R17) ni **las firmas de las cinco rutas** que ganan `request: Request`: no hay
ni una referencia a `FORZADO`, `approve_document`, `delete_document`,
`api_registro_delete`, `api_obra_delete` ni `api_trabajador_delete` en la
suite. Añadir el parámetro no puede romper una aserción de firma porque no
existe.

**Regla de reparación** (de `design.md` §6, aplicada en T5 y T7): si el test
comprueba *quién firma*, se le pone cabecera; si solo necesita *que haya algún
valor*, basta con actualizar el literal esperado a `local:…`.

---

## T2 · Fase RED de la resolución de identidad (R1–R9, R20, R21)

Los dos ficheros de test escritos **antes** de que exista `identidad.py`.
Traza real, no un resumen:

```
$ python -m pytest services/partes-front/tests/test_f017_identidad.py \
                   services/partes-front/tests/test_f017_entorno.py -q

ERROR collecting services/partes-front/tests/test_f017_identidad.py
services\partes-front\tests\test_f017_identidad.py:27: in <module>
    from interface_adapters.web.identidad import (
E   ModuleNotFoundError: No module named 'interface_adapters.web.identidad'

ERROR collecting services/partes-front/tests/test_f017_entorno.py
services\partes-front\tests\test_f017_entorno.py:28: in <module>
    from interface_adapters.web.identidad import (
E   ModuleNotFoundError: No module named 'interface_adapters.web.identidad'

!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!
1 warning, 2 errors in 1.44s
```

**R5b y R5c no son una formalidad en esta fase**, como avisaba T2. Los tests
que las cubren están escritos de forma que un `local:` en el sitio equivocado
los pone rojos aunque el valor «parezca» correcto:

- `test_f017_r5b_desplegado_sin_cabecera_es_sin_identidad` no se conforma con
  `actor == "sin-identidad"`: afirma **además** `not actor.startswith("local:")`.
  Comprobar sólo la igualdad dejaría pasar justo la confusión que la enmienda
  del humano viene a evitar.
- `test_f017_r5c_la_senal_b_se_aprende_y_corrige_a` reproduce el escenario del
  agujero de la señal A (la plataforma deja de inyectar `CONTAINER_APP_*`) y
  comprueba que, tras el primer usuario autenticado, una petición sin cabecera
  ya **no** se firma como sesión local.
- `test_f017_r5c_la_senal_b_tambien_llega_a_la_columna` impide que la señal B
  se quede en cosmética de `/whoami`: comprueba el valor **sellado en la fila**.
- `test_f017_r5c_creerse_desplegado_en_local_es_inocuo` documenta la otra
  dirección del fallo asimétrico y fija por qué es tolerable.

---

## T3 · `identidad.py` · T3 bis · las dos ramas del fallback

Creado `services/partes-front/interface_adapters/web/identidad.py` con las
cinco funciones puras de `design.md` §7. Resultado sobre los tests de T2:

```
$ python -m pytest services/partes-front/tests/test_f017_identidad.py \
                   services/partes-front/tests/test_f017_entorno.py -q
14 failed, 179 passed, 1 warning in 13.59s
```

**Los 14 rojos son exactamente los que T3 anunciaba**: los que necesitan la
app entera (`_actor` y `/whoami`), no las funciones puras. Se cierran en T4 y
T7. Verificación literal de T3 bis:

```
$ python -m pytest services/partes-front/tests/test_f017_identidad.py -q -k "r5 or r5b or r6"
2 failed, 48 passed, 124 deselected      # los 2 son el WARNING de R5b, que vive en app.py (T4)
```

Dos decisiones tomadas al implementar, ninguna de ellas contradice la spec:

1. **`es_actor_reservado` normaliza por su cuenta** en vez de confiar en que
   el llamante le pase el valor ya normalizado. R6 es una garantía de
   seguridad: hacerla depender de que quien llama se acuerde de un paso previo
   es exactamente como se pierden las garantías de seguridad.
2. **Un `-NAME` reservado no impide que el token identifique.** R6 dice
   descartar el valor y seguir «como si la cabecera no existiera»; el
   paréntesis de la spec cita R5/R5b porque es el caso normal (no hay token).
   Se ha implementado la lectura literal —seguir el flujo— que además es la
   útil: si el `-NAME` viniera envenenado, el token real sigue sirviendo. En
   el caso sin token el resultado es idéntico al que pide el paréntesis, y
   `test_f017_r6_espacio_reservado_por_cabecera_se_descarta` lo comprueba en
   las dos cabeceras y en los dos entornos.

`python -m ruff check` sobre los tres ficheros nuevos: `All checks passed!`.

---

## T4 · `_actor` pasa a leer la cabecera

Tres cambios en `app.py`, ninguno fuera de lo previsto: el `import` de
`identidad`, `app.state.easy_auth_visto = False` (+ `identidad_anunciada`,
para la nota única de R9) en `build_app`, y `_resolver_identidad` junto a
`_actor`. **La firma de `_actor` no se ha tocado.**

### La trampa de F-016, tal y como estaba anunciada

```
$ python -m pytest services/partes-front/tests/test_f016_endpoints_admin_jornadas.py -q
FAILED ...::test_f016_r13_auditoria
FAILED ...::test_f016_r13_sin_default_reviewer_se_sella_nulo_y_no_falla
2 failed, 50 passed, 1 warning in 6.10s
```

Traza real del primero — **es la evidencia de que `_actor` manda de verdad**,
no una molestia:

```
        monkeypatch.setenv("DEFAULT_REVIEWER", "quien-firma")
        cliente, _, fabrica, _ = _montaje()
        jid = cliente.post("/api/admin/jornadas", json=_alta()).json()["id"]
        fila = _fila_cruda(fabrica, jid)
>       assert fila.created_by == "quien-firma"
E       AssertionError: assert 'local:quien-firma' == 'quien-firma'
E         - quien-firma
E         + local:quien-firma
E         ? ++++++
```

Y el segundo, que confirma R7 (ya no hay `NULL` posible):

```
>       assert _fila_cruda(fabrica, jid).created_by is None
E       AssertionError: assert 'local:sin-identidad' is None
```

### El guardián del punto único, VERDE sin tocarlo

```
$ python -m pytest services/partes-front/tests/test_f016_endpoints_admin_jornadas.py -q -k "identidad_se_resuelve"
1 passed, 51 deselected, 1 warning in 1.28s
```

`test_f016_r13_la_identidad_se_resuelve_en_un_solo_sitio` sigue afirmando las
tres cosas que hacían intangible la firma: `def _actor(request: Request)`
aparece **una** vez, el bloque de F-016 llama `_actor(request)` **cinco**
veces y no contiene `settings.default_reviewer`. Las cinco escrituras de F-016
pasaron a firmar con la identidad real **sin tocar una sola línea de sus
endpoints** (R19), que era la promesa que F-016 dejó escrita.

---

## T6 · Fase RED de los once puntos (R12–R18)

Escritos `test_f017_endpoints_firmados.py` (R12–R15) y
`test_f017_aprobacion_firmada.py` (R16–R18) **antes** de tocar las rutas.
Traza real de los dos requisitos que el rigor exige en RED:

```
$ python -m pytest .../test_f017_endpoints_firmados.py::test_f017_r12_approved_by \
                   .../test_f017_aprobacion_firmada.py::test_f017_r16_payload_y_marcas_encolado -q

>       assert documento.approved_by == USUARIO
E       AssertionError: assert None == 'ana.ejemplo@ejemplo.invalid'
E        +  where None = <...ParteDocumentOrm object...>.approved_by

>       assert usuario == USUARIO                    # el sobre de q-transfer
E       AssertionError: assert None == 'ana.ejemplo@ejemplo.invalid'

2 failed, 1 warning in 1.80s
```

Merece la pena pararse en el valor que devuelve el fallo: **`None`**, no un
genérico. La fase RED no está reproduciendo un caso de laboratorio — está
reproduciendo **el estado real del despliegue**, donde `DEFAULT_REVIEWER` no
está configurada y la auditoría del portal lleva en blanco desde el primer día
(hallazgo H1). El rojo de estos dos tests es la feature entera en una línea.

### ⚠ HALLAZGO QUE EL HUMANO DEBE DECIDIR — R14 y R15 nombran una columna que nadie escribe

Al implementar T6 se comprobó contra el árbol que **la premisa de R14 y R15 es
incorrecta**. Los dos dicen que el actor debe escribirse en `undo_log.actor`.
Los hechos, verificados uno a uno:

1. **`undo_log.actor` existe** (la añadió F-010 por DDL complementario) **pero
   no la escribe nadie**: `_record_undo` ni siquiera acepta un actor, y no hay
   una sola asignación a esa columna en todo sv4.
2. **Las cuatro operaciones de R14/R15 no generan ninguna fila de `undo_log`.**
   Los tres borrados (`soft_delete_registro`, `soft_delete_obra`,
   `soft_delete_worker`) y el alta manual no llaman a `_record_undo`. Quienes
   sí lo llaman son las **ediciones**: `update_registro`, `set_registro_hora`,
   `set_registro_partida`, `backfill_empleado`, `reassign_empleado_*`,
   `update_parte_fecha`, `update_parte_obra`.
3. **`crear_parte_manual` acepta `by=` y lo ignora**: el parámetro se declara
   en la firma y no aparece ni una vez en el cuerpo del método.

`design.md` §5.2 (puntos 8–11) sí es correcto y es lo que se ha implementado:
entregar `_actor(request)` por el parámetro `by=` que esas rutas ya usaban.
Para los tres borrados eso llega de verdad a `deleted_by`. Para el alta manual
**se queda en la puerta del repositorio**.

**Lo que NO se ha hecho por cuenta propia**, y por qué:

| Opción | Por qué se descartó sin consultar |
|---|---|
| Que los borrados escriban en `undo_log` | Es **funcionalidad nueva**: pasarían a ser deshacibles. Y un «log de auditoría de acciones» es literalmente **F-018** (`requirements.md` §0 y §2.2) |
| Que `crear_parte_manual` use su `by=` | Toca `parte_repository.py`, que `design.md` §5.3 marca explícitamente como fichero que **NO se toca** |

**Por qué esto importa y no es un detalle**: R7 declara que, tras esta feature,
`autor IS NULL` significa **exclusivamente** «fila anterior al corte». Ese
criterio es la base de R22 y el apoyo que §12 promete a F-018. Con
`undo_log.actor` condenada a seguir siempre a `NULL`, el criterio **no es
universal**: vale para las seis columnas que sí se escriben, no para la
séptima. La documentación de T10 lo dice así, sin redondear.

Los tests dejan el hecho a la vista en vez de taparlo: `test_f017_r14_*` y
`test_f017_r15_*` comprueban el actor **en el punto que la ruta controla** (el
argumento con el que llama al repositorio), y el fichero termina con un bloque
de comentario que explica los tres hechos anteriores.

---

## T7 · Los once puntos + `/whoami`

Los doce cambios de `design.md` §5.2, aplicados tal cual. Las cinco firmas que
no tenían `request` lo reciben **el primero**, con los `Form(default=…)`
intactos; `_payload_registro` y `_trazar` reciben el actor **por parámetro**
(no lo resuelven: R10); y `/whoami` devuelve sus cinco campos.

Un punto **añadido** a la tabla de §5.2, y conviene justificarlo: el
**preflight** (`POST /api/aprobar/preflight`) también llama a
`_payload_registro`. La spec no lo listaba porque no escribe en ninguna
columna, pero comparte el constructor del payload: al añadir el parámetro
`actor` había que dárselo igualmente, y así el `usuario` que ve sv5 es el
mismo en las tres rutas. Lo cubre
`test_f017_r16_el_preflight_tambien_va_firmado`.

```
$ python -m pytest services/partes-front/tests -q
1021 passed, 1 warning in 74.58s
```

**Un único rojo colateral en toda la suite**, el que T1 predijo:
`test_f002_aprobar_encolar.py` esperaba `usuario == "ana"` y pasa a
`"local:ana"`. Se aplicó la regla de `design.md` §6: el test sólo necesitaba
*que hubiera un valor y cuál*, así que se actualizó el literal y se explicó
por qué en un comentario. Los otros seis ficheros que «rondaban la zona»
siguieron verdes sin tocarlos, exactamente como se predijo en T1.

También se retiró el `or "(sin usuario)"` del aviso de forzado (R17): con R7
el actor nunca es vacío, así que ese relleno ya no puede ocurrir — y hay un
test que comprueba que ese texto no vuelve a aparecer en la fuente.

---

## T8 · El punto único, con guardián (R10, R11)

`test_f017_punto_unico.py`, 12 tests, en verde:

```
$ python -m pytest services/partes-front/tests/test_f017_punto_unico.py -q
12 passed in 0.14s
```

Comprueba que `app.py` tiene **exactamente una** lectura de
`settings.default_reviewer` (antes había doce) y que está dentro de
`_resolver_identidad`; que ninguna ruta la lee en su cuerpo; que ningún
fichero de producción de sv4 usa el literal de una cabecera de Easy Auth
fuera de `identidad.py`; y que `infrastructure/`, `application/`, `domain/` y
`config/` ni saben que Easy Auth existe.

### El guardián detecta el defecto (verificación pedida por T8)

Se introdujo a propósito una segunda lectura en `api_registro_delete`
(`by=settings.default_reviewer`) y se ejecutó el guardián. Lo caza **por tres
vías independientes**:

```
FAILED ...::test_f017_r11_una_sola_lectura_de_default_reviewer
FAILED ...::test_f017_r11_ninguna_ruta_lee_default_reviewer
FAILED ...::test_f017_todos_los_puntos_de_escritura_usan_el_helper
3 failed, 9 passed
```

Traza del segundo, que además **señala la ruta culpable**:

```
>           assert "settings.default_reviewer" not in cuerpo
E           assert 'settings.default_reviewer' not in '@app.post("..."ok": ok})\n'
E             'settings.default_reviewer' is contained here:
E               ro_id, by=settings.default_reviewer
E                       )
E                       return JSONResponse({"ok": ok})
```

El defecto se deshizo con `git checkout` sobre el fichero (el commit de T7 ya
estaba hecho) y los 12 vuelven a verde.

**Un ajuste durante T8, por precisión del guardián.** La primera versión
prohibía el texto `X-MS-CLIENT-PRINCIPAL` en `app.py` a secas, y eso ponía
rojo el **docstring** de `_actor`, que menciona la cabecera para explicar de
dónde sale el actor. Perseguir la documentación habría sido un guardián
contraproducente: empuja a escribir docstrings peores. Ahora busca el literal
**entrecomillado**, que es lo que delata una lectura de verdad.

---

## T9 · Guardián del corte histórico (R22)

`tests/test_f017_r22_sin_reescritura_historica.py`, en la raíz del monorepo:
**27 tests**, en verde. Vigila las dos cosas de las que depende el criterio
del corte:

- **(a)** Las ocho columnas de autor conservan nombre y ancho en las **dos**
  copias del ORM (sv3 y sv4), el mínimo sigue siendo 120 —el que
  `identidad.py` usa para truncar— y no ha aparecido ninguna columna de autor
  sin declarar.
- **(b)** No hay ningún `UPDATE` sobre esas columnas en el árbol, ningún
  fichero `.sql`, y el DDL complementario de F-010 no las estrecha ni las
  reescribe.

Incluye `test_f017_r22_el_guardian_muerde`, que comprueba sobre texto
fabricado —nunca sobre el árbol— que el patrón de `UPDATE` masivo se detecta
de verdad y que **no** salta con una escritura legítima por ORM.

## T10 · El corte, documentado (R23)

`docs/referencia/partes-proyecto.md`:

- **§5.4 corregido.** Decía literalmente que `created_by`/`updated_by`
  «llevan hoy `DEFAULT_REVIEWER`». Era **falso**, y de una forma que
  importaba: llevaban `NULL`, porque esa variable nunca se configuró.
- **§5.7 nuevo, «Corte de auditoría (F-017)»**, con el criterio
  (`autor IS NULL` ⇔ anterior a F-017), la explicación de los dos marcadores
  reservados, las consultas SQL para comprobarlo, la mención a `/whoami` y el
  hueco `⛔ PENDIENTE: fecha de despliegue`.
- **§5.5**: `undo_log.actor` marcada como «hoy no la escribe nadie».

`docs/ARCHITECTURE.md`: regla de dominio 11, la identidad se resuelve en un
único punto y `NULL` significa «anterior a F-017».

`tests/test_f017_r23_corte_documentado.py` (10 tests) no se conforma con que
el apartado exista: comprueba que contiene el criterio, que distingue
`local:…` de `sin-identidad`, que dice que no se reescribió nada, que advierte
de `undo_log.actor` y que el hueco de la fecha sigue puesto. **Ese último test
se pondrá rojo el día del despliegue, y es deliberado**: un recordatorio que
no molesta no recuerda nada.

## T11 · `azure-apps/partes.md`

Commit **local y sin push** en su propio repositorio (`47cb860`), como manda
la regla de mantenimiento de `CLAUDE.md`. Documenta qué se guarda y dónde, la
ruta nueva `GET /whoami`, el cambio de significado de `DEFAULT_REVIEWER` (y
que **no** hace falta configurarla), los dos marcadores que no son personas,
cómo se distingue «desplegado» de «local» sin variable nueva, y el criterio
del corte con su excepción declarada.

---

## Ficheros tocados

| Fichero | Qué |
|---|---|
| `services/partes-front/interface_adapters/web/identidad.py` | **Nuevo.** Las cinco funciones puras del resolutor (257 líneas) |
| `services/partes-front/interface_adapters/web/app.py` | **El único fichero de producción modificado.** `_resolver_identidad` + interior de `_actor`, `app.state.easy_auth_visto`/`identidad_anunciada`, `actor` por parámetro en `_payload_registro` y `_trazar`, `request: Request` en cinco firmas, las once lecturas sustituidas, `GET /whoami` |
| `services/partes-front/tests/test_f017_identidad.py` | **Nuevo.** R1–R9 (menos R5c), R20, R21 |
| `services/partes-front/tests/test_f017_entorno.py` | **Nuevo.** R5c y la asimetría del fallo |
| `services/partes-front/tests/test_f017_punto_unico.py` | **Nuevo.** R10, R11 |
| `services/partes-front/tests/test_f017_endpoints_firmados.py` | **Nuevo.** R12–R15 |
| `services/partes-front/tests/test_f017_aprobacion_firmada.py` | **Nuevo.** R16–R18 |
| `tests/test_f017_r22_sin_reescritura_historica.py` | **Nuevo** (raíz). R22 |
| `tests/test_f017_r23_corte_documentado.py` | **Nuevo** (raíz). R23 |
| `services/partes-front/tests/test_f016_endpoints_admin_jornadas.py` | Helper `_como`, `test_f016_r13_auditoria` reescrito, el de `NULL` convertido y uno nuevo (R19) |
| `services/partes-front/tests/test_f002_aprobar_encolar.py` | Un literal: `"ana"` → `"local:ana"` |
| `docs/referencia/partes-proyecto.md` | §5.4 corregido, §5.5 matizada, §5.7 nueva (R23) |
| `docs/ARCHITECTURE.md` | Regla de dominio 11 |
| `progress/current.md` | Verificaciones MANUAL y la decisión pendiente |
| `azure-apps/partes.md` | **Repo distinto**, commit `47cb860`, local y sin push |

**Cero cambios** en `orm_models.py` (ninguna de las dos copias), en
`parte_repository.py`, en `resultado_consumer.py`, en las plantillas, en el JS,
en `config/settings.py`, en `infra/` y en sv1, sv2, sv3 y sv5. **Cero cambios
de schema, cero columnas, cero tablas, cero rutas de catálogo nuevas** (aparte
de `/whoami`, que la spec aprueba explícitamente). Ningún `403`, ningún rol,
ninguna restricción de acceso nueva.

## Decisiones de diseño tomadas al implementar

Las de la spec (DA1–DA8) se respetaron sin cambios. Estas son las que hubo que
tomar sobre la marcha, todas menores salvo la primera:

1. **R14/R15 no se resolvieron por cuenta propia** — el hallazgo del bloque de
   T6. Las dos salidas posibles (crear filas de `undo_log`, o dar destino al
   `by` de `crear_parte_manual`) se salen del alcance aprobado: la primera es
   funcionalidad nueva y territorio de F-018; la segunda exige **una columna
   nueva**, porque ni `parte_documents` ni `parte_registros` tienen
   `created_by` (solo la tienen `empleado_alias` y `empleado_jornada`).
   Elevado al humano; detalle en `progress/current.md`.
2. **El preflight también va firmado.** No estaba en la tabla de §5.2 porque
   no escribe en ninguna columna, pero comparte `_payload_registro`: al añadir
   el parámetro había que dárselo, y así el `usuario` que ve sv5 es el mismo
   en las tres rutas.
3. **`es_actor_reservado` normaliza por su cuenta.** R6 es una garantía de
   seguridad; hacerla depender de que el llamante recuerde un paso previo es
   como se pierden las garantías de seguridad.
4. **Un `-NAME` reservado no impide que el token identifique.** Lectura
   literal de R6 («como si la cabecera no existiera») y la más útil.
5. **El guardián de R10 persigue el literal entrecomillado, no el nombre.**
   La primera versión ponía rojo el docstring de `_actor`; un guardián que
   castiga la documentación produce documentación peor.
6. **No se memoizó `_resolver_identidad`** (aviso recibido del coordinador
   pensando en F-018). Hoy cada endpoint pide el actor una sola vez, así que
   no hay WARNING duplicados y memoizar sería resolver un problema que aún no
   existe. Anotado en `progress/current.md` para F-018: tres líneas, sin
   cambiar ninguna firma.

---

## Verificaciones MANUAL pendientes (humano)

Copiadas con su comando exacto a `progress/current.md` (T13). En local **no
existe** ninguna cabecera de Easy Auth: que lleguen de verdad en Azure no lo
puede demostrar ningún test.

| | Qué | Estado |
|---|---|---|
| **M1 bis** | ¿Inyecta Container Apps las `CONTAINER_APP_*`? | ✅ **EJECUTADA en T0, positiva.** Las cuatro presentes en `ca-sv4-front` |
| **M1** | `GET /whoami` en el portal desplegado con sesión de Entra: `actor` = tu UPN, `origen` = `cabecera-name`, `entorno` = `desplegado` | Pendiente del despliegue |
| **M2** | Aprobar un parte y ver `parte_documents.approved_by` | Pendiente (necesita firewall) |
| **M3** | Borrar una línea y mirar el autor | Pendiente (necesita firewall). **Ojo**: por el hallazgo de R14, `undo_log` no recibirá fila; lo que hay que mirar es `parte_registros.deleted_by` |
| **M4** | Que el recuento de filas históricas con autor `NULL` sea **el mismo** antes y después del despliegue (R22) | Pendiente (necesita firewall) |

M2, M3 y M4 necesitan la regla de firewall de `psql-albaranes-rs9k2` que ya
estaba pendiente en `progress/current.md`.

**Lo que M1 debe delatar si sale mal**, por orden de gravedad: `entorno = local`
en el portal desplegado sería el **único fallo de esta feature que ensucia
datos** (filas de producción firmadas `local:…`), y el campo
`senal_despliegue` dice exactamente qué se buscó y qué se encontró. T0 hace
ese escenario muy improbable —la señal A está verificada en el contenedor—,
pero la comprobación sigue costando abrir una URL.

---

## Trazabilidad requisito → test (recuento real)

Los 23 requisitos, con el test que los cubre. Ninguno se quedó sin cubrir.

| R | Dónde | Estado |
|---|---|---|
| R1 | `test_f017_identidad.py` (4 tests: la cabecera manda, gana al token, insensible a mayúsculas, vacía = ausente) | ✅ **fase RED** |
| R2 | `test_f017_identidad.py` (5 claims parametrizados + orden de preferencia + claim vacío + normalización) | ✅ |
| R3 | `test_f017_identidad.py` (7 formas de token roto + claim desconocido + entrada mal formada) | ✅ |
| R4 | `test_f017_identidad.py` (10 casos + truncado + inyección de log) | ✅ |
| R5 | `test_f017_identidad.py` (con y sin `DEFAULT_REVIEWER`, con espacios, en blanco) | ✅ **fase RED** |
| R5b | `test_f017_identidad.py` (valor exacto, **no** empieza por `local:`, WARNING, escritura completada, aviso por petición) | ✅ **fase RED** |
| R5c | `test_f017_entorno.py` (4 variables + entorno normal + vacías + señal B + asimetría + llega a la columna) | ✅ |
| R6 | `test_f017_identidad.py` (8 valores × 2 cabeceras × 2 entornos = 32, + WARNING + qué cuenta como reservado) | ✅ |
| R7 | `test_f017_identidad.py` (4 cabeceras × 2 entornos × 4 fallbacks = 32) + `test_f017_endpoints_firmados.py` (los 6 puntos) | ✅ |
| R8 | `test_f017_identidad.py` (trunca + cabe en la columna más estrecha) | ✅ |
| R9 | `test_f017_identidad.py` (una sola nota; no vuelca token ni claims) | ✅ |
| R10 | `test_f017_punto_unico.py` (app, `identidad.py`, 4 capas internas, repositorio) | ✅ **fase RED** (T8: defecto inyectado) |
| R11 | `test_f017_punto_unico.py` (una lectura, dentro del resolutor, ninguna ruta) | ✅ |
| R12 | `test_f017_endpoints_firmados.py` (cabecera, token, `back` intacto) | ✅ **fase RED** |
| R13 | `test_f017_endpoints_firmados.py` | ✅ |
| R14 | `test_f017_endpoints_firmados.py` (3 borrados parametrizados + `deleted_by` real + dos personas) | ⚠ **ver hallazgo de T6**: se cumple vía `deleted_by`, no vía `undo_log.actor` |
| R15 | `test_f017_endpoints_firmados.py` (3 tests) | ⚠ **ver hallazgo de T6**: el actor llega al repositorio, que lo descarta |
| R16 | `test_f017_aprobacion_firmada.py` (encolado, síncrono, traza, preflight, dos personas, sin cabecera, desplegado) | ✅ **fase RED** |
| R17 | `test_f017_aprobacion_firmada.py` (2 tests, uno sobre la fuente) | ✅ |
| R18 | `test_f017_aprobacion_firmada.py` (2 tests) | ✅ |
| R19 | `test_f016_endpoints_admin_jornadas.py` reescrito + uno nuevo (dos personas, dos firmas) | ✅ |
| R20 | `test_f017_identidad.py` (8 cabeceras basura × 6 rutas = 48) | ✅ |
| R21 | `test_f017_identidad.py` (5 tests: 4 ramas de `origen`, no revela nada, no escribe) | ✅ |
| R22 | `tests/test_f017_r22_sin_reescritura_historica.py` (27) | ✅ |
| R23 | `tests/test_f017_r23_corte_documentado.py` (10) | ✅ |

**Fase RED con traza pegada** para los seis que exigía el rigor `estandar`:
R1, R5, R5b (T2), R10 (T8, con el defecto inyectado), R12 y R16 (T6).
