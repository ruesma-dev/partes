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
