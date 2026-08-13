<!-- progress/impl_F-002.md -->
# F-002 · Cola q-transfer para aprobación asíncrona — informe de implementación

Rama `feature/F-002-cola-q-transfer`. Spec R1–R26 / T1–T15, rigor
**crítico**. Las 15 tareas de `tasks.md` quedan marcadas `[x]`, una por
commit, más tres commits de cierre del rigor.

El resumen en una línea: la aprobación de partes deja de ser una llamada
HTTP que bloquea al usuario minutos y pasa a viajar por `q-transfer`, con
el veredicto de vuelta por `q-transfer-result`; el HTTP se queda para lo
que exige respuesta inmediata (preflight y pisado de conflictos), y sin
colas configuradas todo sigue funcionando como antes.

## Qué cambió, por tarea

Además de las 15 tareas, tres commits de cierre del rigor: `aebad0d`
(cerrar los 46 supervivientes de la primera campaña de mutación),
`5c6c632` (los 6 que quedaban eran dos tests míos mal escritos) y
`e438942` (orden de imports).

| Tarea | Commit | Qué entrega |
|---|---|---|
| T1 | `7540c29` | sv5: adaptadores `infrastructure/azure/` (cola, blob, credenciales) + creación de `services/partes-transfer/tests/` |
| T2 | `ed0555a` | sv5: split del pipeline en `preparar` / `_evaluar` / `registrar`, lock en el constructor, `ContextoRegistro` |
| T3 | `086dc26` | sv5: claves de storage en `settings` (+`transfer_workers`), `build_app(settings, pipeline=None)` |
| T4 | `a40c03c` | sv5: `transfer_consumer` (handler de `q-transfer`) + `resultado_json` como fuente única del contrato |
| T5 | `2abf1f1` | sv5: `arrancar_workers_transfer` (pool de N hilos) + composición en `main.py` |
| T6 | `53b0ef8` | sv4: adaptadores `infrastructure/azure/`, claves de storage, creación de `services/partes-front/tests/` |
| T7 | `007c261` | sv4: `TransferQueuePublisher`, `marcar_registros_encolado`, `marcar_registros_sigrid` extendido |
| T8 | `47f27c6` | sv4: `POST /api/aprobar/encolar` con fallback síncrono; `build_app` inyectable; `resultado_sigrid` |
| T9 | `9c2f9be` (+`e438942`) | sv4: `resultado_consumer` + arranque del hilo daemon en `main.py` |
| T10 | `5013fdd` | sv4: modal que encola sin conflictos + badges `encolado`/`conflicto`/`error` |
| T11 | `75e42ea` | sv4: `contar_aproximado`/`mover` + endpoints `GET/POST /api/admin/poison` |
| T12 | `c7cbf2e` | sv4: aviso de poison en la cabecera (`base.html`, `app.js`, `styles.css`) |
| T13 | `2d595c7` | infra: `add_qtransfer_partes.ps1` (MANUAL, no ejecutado) |
| T14 | `884ccc4` | docs: `ARCHITECTURE.md` + `azure-apps/partes.md` (commit local `1440598` en ese repo, **sin push**) |
| T15 | `bc44ed9` | cobertura de credenciales, bucle de cola y composición: 74,8 % → 97,4 % |

## Decisiones de diseño (y por qué)

1. **El corte del pipeline es donde manda el estado, no donde apetecía.**
   `preparar` (pasos 1–4) solo lee datos maestros que sv5 nunca escribe
   —obra, DNI→recurso, `reshor`, reglas—, así que solaparlo es seguro.
   `registrar` mete DENTRO del lock la evaluación (pasos 5–7) además de
   la escritura (8–9), porque el parte `hmo`, el correlativo
   `PT<AA>/NNNNN`, las synckeys y los conflictos son estado que la propia
   escritura modifica. Evaluar eso fuera del lock es exactamente el fallo
   que la feature debía evitar (evidencia medida más abajo).
2. **El lock viaja en el constructor del pipeline**, no en los llamantes.
   Así lo adquiere `registrar` y ningún camino —HTTP de pisado o worker
   de cola— puede olvidarlo. `main.py` crea UNO y lo comparte.
3. **Fuente única del contrato en los dos sentidos.** `resultado_json.py`
   (sv5) lo usan el endpoint HTTP y la cola; `resultado_sigrid.py` (sv4)
   lo usan el endpoint síncrono y el consumidor. Dos copias del mapeo
   habrían divergido a la primera corrección.
4. **Publicar antes de marcar** (sv4) y **send antes de delete** (poison):
   en ambos casos el orden elegido convierte un fallo intermedio en algo
   recuperable (blob huérfano, mensaje duplicado) en vez de en pérdida.
5. **Fallo de negocio ≠ fallo de infraestructura** en el consumidor de
   sv5. El de negocio se publica como `ok=false` y consume el mensaje
   (reintentarlo daría el mismo error cinco veces y acabaría en poison sin
   que nadie se entere); el de infraestructura relanza para que el mensaje
   reaparezca.
6. **`ya_registradas` distingue veredicto final de estado en vuelo.** El
   código anterior solo marcaba si la línea no tenía estado; con la cola,
   las líneas llegan en `'encolado'` (que es un valor verdadero) y se
   habrían quedado ahí para siempre pese a estar ya en Sigrid.

## Desviaciones respecto a la spec (justificadas)

1. **sv4 no tenía suite de tests.** El design daba por hecho que «la suite
   del servicio ya existe» y que el patrón de SQLite en memoria «ya se usa
   en ella». No era cierto: `init.sh` venía avisando de que nadie
   comprobaba sv4. Se ha creado `services/partes-front/tests/` con su
   `conftest.py` y sus dobles, incluida la fábrica de sesión SQLite.
2. **`build_app` de sv4 acepta sus colaboradores por parámetro**
   (`repository`, `transfer_client`, `publisher`, `cola_cliente`). El
   design solo preveía esto para sv5 (`pipeline=None`). Sin ello, levantar
   la app en un test exige PostgreSQL, y la regla dura dice que los unit
   tests no tocan BBDD. Es retrocompatible: sin inyección se comporta como
   antes.
3. **Dependencias nuevas en sv4 y sv5**: `azure-identity`,
   `azure-storage-queue`, `azure-storage-blob`. No están escritas en la
   spec, pero son la consecuencia directa de los adaptadores que el design
   manda crear (`from azure.storage.queue import ...`). Son las mismas
   librerías que ya usan sv1, sv2 y sv3.

   > **Corregido tras la review.** La redacción original de este punto
   > —«Dependencias nuevas **en los manifiestos** de sv4 y sv5»— era
   > **falsa**: los paquetes se instalaron en el `.venv` de la raíz (ver
   > desviación 6) pero **no se declararon** en
   > `infra/manifests/sv4/requirements.txt` ni en `sv5/requirements.txt`,
   > que es lo que `build_images_partes.ps1` copia al contexto de build. La
   > imagen no los habría instalado y ambos contenedores habrían muerto en
   > el import de `main.py`. Lo declaré por hecho sin comprobarlo. Los tres
   > paquetes están ya en ambos manifiestos, con los mismos pines que sv3;
   > la evidencia está en «Correcciones tras review».
4. **El sobre de resultado lleva `registro_ids`** además del `resultado`.
   El design no lo contemplaba y R14 lo necesita: sin la lista de líneas
   de la petición, un `ok=false` no se puede trazar en ninguna parte.
5. **`resultado_json.py` (sv5) y `resultado_sigrid.py` (sv4)** son ficheros
   nuevos que el design no listaba (ver decisión 3).
6. **El `.venv` de la raíz no tenía las dependencias de sv4 ni sv5.** Se
   instalaron; sin ellas `init.sh` no podía ejecutar las suites nuevas.
   Es cambio de entorno, no del repositorio.

## Fase RED (rigor crítico)

Cada tarea con código nuevo se escribió con el test primero. Trazas reales
del fallo previo, con el comando exacto.

### T1 — adaptadores de Storage de sv5

```
$ cd services/partes-transfer && python -m pytest tests/test_f002_cola_cliente.py -q --tb=short
tests\test_f002_cola_cliente.py:9: in <module>
    from infrastructure.azure import blob_cliente as mod_blob
E   ModuleNotFoundError: No module named 'infrastructure.azure'
=========================== short test summary info ===========================
ERROR tests/test_f002_cola_cliente.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.27s
```

### T2 — split del pipeline (R7, R19, R20): el requisito central

```
$ cd services/partes-transfer && python -m pytest tests/test_f002_pipeline_fases.py -q --tb=line
C:\...\tests\test_f002_pipeline_fases.py:58: TypeError: RegistroPipeline.__init__() got an unexpected keyword argument 'lock'
=========================== short test summary info ===========================
FAILED tests/test_f002_pipeline_fases.py::test_f002_regresion_preflight_equivalente
FAILED tests/test_f002_pipeline_fases.py::test_f002_regresion_ejecutar_equivalente
FAILED tests/test_f002_pipeline_fases.py::test_f002_r8_ejecutar_dos_veces_no_duplica
FAILED tests/test_f002_pipeline_fases.py::test_f002_regresion_modo_pruebas_desvia_la_obra
FAILED tests/test_f002_pipeline_fases.py::test_f002_preparar_devuelve_contexto_sin_tocar_estado_escrito
FAILED tests/test_f002_pipeline_fases.py::test_f002_r20_el_estado_escrito_se_lee_dentro_del_lock
FAILED tests/test_f002_pipeline_fases.py::test_f002_r7_el_lock_lo_adquiere_registrar_no_el_llamante
FAILED tests/test_f002_pipeline_fases.py::test_f002_r19_preparar_no_espera_al_lock
FAILED tests/test_f002_pipeline_fases.py::test_f002_r19_registrar_serializa_entre_peticiones
FAILED tests/test_f002_pipeline_fases.py::test_f002_r20_dos_peticiones_misma_obra_y_mes_crean_un_solo_parte
FAILED tests/test_f002_pipeline_fases.py::test_f002_r19_el_lock_se_comparte_con_quien_lo_inyecta
FAILED tests/test_f002_pipeline_fases.py::test_f002_r10_conflictos_no_confirmados_no_se_escriben
FAILED tests/test_f002_pipeline_fases.py::test_f002_r10_pisar_confirmado_borra_e_inserta
13 failed, 1 passed in 0.17s
```

### T3 — `build_app` con pipeline inyectado

```
$ cd services/partes-transfer && python -m pytest tests/test_f002_settings_y_app.py -q --tb=line
C:\...\tests\test_f002_settings_y_app.py:78: TypeError: build_app() got an unexpected keyword argument 'pipeline'
12 failed, 1 passed, 1 warning in 1.31s
```

### T4 — handler de `q-transfer`

```
$ cd services/partes-transfer && python -m pytest tests/test_f002_transfer_consumer.py -q --tb=short
tests\test_f002_transfer_consumer.py:18: in <module>
    from interface_adapters.queue.transfer_consumer import (
E   ModuleNotFoundError: No module named 'interface_adapters.queue'
1 error in 1.38s
```

### T5 — pool de workers

```
$ cd services/partes-transfer && python -m pytest tests/test_f002_workers.py -q --tb=line
tests\test_f002_workers.py:20: in <module>
    from interface_adapters.queue.transfer_consumer import (
E   ImportError: cannot import name 'arrancar_workers_transfer' from 'interface_adapters.queue.transfer_consumer'
1 error in 0.56s
```

### T7 — publisher y traza `sigrid_*`

```
$ cd services/partes-front && python -m pytest tests/test_f002_publisher.py -q --tb=line
tests\test_f002_publisher.py:21: in <module>
    from infrastructure.transfer.transfer_queue_publisher import (
E   ModuleNotFoundError: No module named 'infrastructure.transfer.transfer_queue_publisher'
1 error in 1.07s
```

### T8 — endpoint `POST /api/aprobar/encolar`

```
$ cd services/partes-front && python -m pytest tests/test_f002_aprobar_encolar.py -q --tb=line
FAILED tests/test_f002_aprobar_encolar.py::test_f002_r1_encolar_responde_asincrono_sin_esperar_a_sigrid
FAILED tests/test_f002_aprobar_encolar.py::test_f002_r2_encolar_deja_las_lineas_en_encolado
FAILED tests/test_f002_aprobar_encolar.py::test_f002_encolar_sin_lineas_activas_responde_422
FAILED tests/test_f002_aprobar_encolar.py::test_f002_r5_pisar_claves_no_entra_por_la_cola
FAILED tests/test_f002_aprobar_encolar.py::test_f002_r5_ejecutar_sigue_registrando_de_forma_sincrona
FAILED tests/test_f002_aprobar_encolar.py::test_f002_r4_preflight_sigue_siendo_http_sincrono
FAILED tests/test_f002_aprobar_encolar.py::test_f002_r3_sin_colas_configuradas_registra_en_sincrono
FAILED tests/test_f002_aprobar_encolar.py::test_f002_r3_el_fallback_nunca_pisa_conflictos
FAILED tests/test_f002_aprobar_encolar.py::test_f002_r14_el_fallback_marca_error_si_sv5_falla
FAILED tests/test_f002_aprobar_encolar.py::test_f002_r12_el_camino_sincrono_marca_los_conflictos
FAILED tests/test_f002_aprobar_encolar.py::test_f002_r3_sin_sv5_ni_colas_el_endpoint_avisa
11 failed, 1 warning in 1.38s
```

### T9 — consumidor de `q-transfer-result`

```
$ cd services/partes-front && python -m pytest tests/test_f002_resultado_consumer.py -q --tb=line
tests\test_f002_resultado_consumer.py:21: in <module>
    from interface_adapters.workers.resultado_consumer import (
E   ModuleNotFoundError: No module named 'interface_adapters.workers.resultado_consumer'
1 error in 0.94s
```

### T11 — gestión de poison

```
$ cd services/partes-front && python -m pytest tests/test_f002_poison.py -q --tb=line
FAILED tests/test_f002_poison.py::test_f002_r23_cuenta_los_mensajes_aproximados
FAILED tests/test_f002_poison.py::test_f002_r24_mueve_los_mensajes_a_la_cola_principal
FAILED tests/test_f002_poison.py::test_f002_r24_no_mueve_mas_del_tope - Attri...
FAILED tests/test_f002_poison.py::test_f002_r25_el_mensaje_se_borra_SOLO_tras_encolarlo
FAILED tests/test_f002_poison.py::test_f002_r26_sin_colas_configuradas_el_endpoint_lo_dice
...
17 failed, 1 warning in 2.29s
```

## Dos evidencias extra sobre el requisito central (R19/R20)

El split del pipeline es refactor de código que ya existía, así que un test
en verde no prueba gran cosa por sí solo. Se comprobaron las dos mitades.

**(a) Las aserciones de regresión se anclaron contra el pipeline ANTERIOR**
al refactor, ejecutándolas con la firma vieja del constructor
(`scratchpad/pin_pre_refactor.py`, fuera del repositorio):

```
$ cd services/partes-transfer && python .../pin_pre_refactor.py
PIN OK (pipeline PRE-refactor): preflight_equivalente
PIN OK (pipeline PRE-refactor): ejecutar_equivalente
PIN OK (pipeline PRE-refactor): reentrega_no_duplica
PIN OK (pipeline PRE-refactor): modo_pruebas
PIN OK (pipeline PRE-refactor): conflictos_no_confirmados
PIN OK (pipeline PRE-refactor): pisar_confirmado
```

Las mismas aserciones pasan después del split ⇒ se movió código, no se
cambiaron decisiones. `reglas_registro.py` no se ha tocado.

**(b) Con un lock decorativo, los tests de R19/R20 fallan como fallaría
producción** (`scratchpad/sin_lock.py`: mismo pipeline con un objeto que
finge ser lock pero no serializa):

```
SIN LOCK REAL (lock decorativo):
  R19 max_concurrencia['escribir'] = 3  (el test exige 1)
  R20 partes creados = 3 cods = ['PT26/00001', 'PT26/00001', 'PT26/00001']  (el test exige 1 y ['PT26/00001'])
  R20 posiciones = [64, 64, 64]  (el test exige 3 distintas)
```

Tres cabeceras para la misma obra y mes con el MISMO correlativo, y tres
líneas en la misma posición: exactamente el daño que el design anticipaba.

## Campaña de mutación

Primera pasada: **132 mutantes, 82 muertos, 46 supervivientes, 4 timeouts**
(1005 s). Los 46 se revisaron uno a uno y **ninguno resultó ser
equivalente**: todos tenían consecuencia real y todos se han cerrado con
test (commit `aebad0d`). Los de más enjundia:

- **`max_dequeue` corrido en uno** (`>` → `>=`, en sv4 y sv5): mandaba a
  la DLQ una petición que aún tenía un reintento. Ahora se comprueba el
  límite por los dos lados (intento 5 se procesa, intento 6 va a poison).
- **`overwrite=True` → `False`** al subir un blob: rompía el reproceso de
  un mensaje reentregado. Sobrevivía porque el doble ignoraba el flag; se
  ha endurecido para comportarse como el SDK real.
- **`{"ok": False}` → `{"ok": True}`** en dos respuestas de rechazo (pisar
  conflictos y cola no admitida). El portal decide por ese campo: habría
  celebrado un error. Los tests miraban el código HTTP y no el cuerpo.
- **`[:255]` → `[:256]`** en `sigrid_motivo`, que es `VARCHAR(255)`:
  SQLite lo traga y PostgreSQL no. Un error largo de sigrid-api habría
  reventado el marcado en producción y no en la suite.
- **`got = True` → `False`**: el worker dormía teniendo trabajo. Y
  **`not got and not self._stop` → `not got and self._stop`**: sondeo
  invertido. Se distingue asertando que la espera ocurre con la cola
  vacía y **sin** haber pedido parar.
- **`exc_info=True` → `False`** en los cuatro avisos que se tragan una
  excepción a propósito. Son justo los que hay que investigar; sin el
  traceback el fallo desaparece. Cerrados con `caplog`.
- **`approximate_message_count` por defecto 1** en vez de 0: encendía el
  aviso de poison del portal sin nada parado.

Segunda pasada: **120 muertos, 6 supervivientes, 6 timeouts**. Los 6
supervivientes que quedaban **no eran código sin comprobar: eran dos
tests mal escritos míos**, y merece la pena dejarlo por escrito porque es
justo lo que la mutación sirve para encontrar:

1. **`exc_info`**. Con `exc_info=False`, `logging` deja
   `record.exc_info` valiendo `False`, que **no es `None`**. Mi
   aserción `is not None` pasaba igual con la traza suprimida: comprobaba
   nada. Ahora se exige la tupla de la excepción.
2. **`got = True`**. Mi test paraba el bucle DENTRO del handler, así que
   con `got = False` la condición del sondeo salía falsa igualmente por
   el flag de parada, y los dos comportamientos eran indistinguibles. La
   parada tiene que llegar por la ronda vacía.

Corregidos (commit `5c6c632`) y verificados aplicando los seis mutantes
uno a uno: los seis mueren.

**Sobre los timeouts**: son mutaciones que anulan la parada del bucle
(`self._stop = True` → `False`, y el sondeo invertido). No son
supervivientes silenciosos: dejan la suite colgada, o sea que la cazan
igualmente —una suite que no termina no está en verde—, solo que
tardando. Se cuentan aparte porque el veredicto no llega por aserción.

Tercera pasada (definitiva, `progress/mutacion_F-002.md` del 17:46):
**132 mutantes, 126 muertos, 0 supervivientes, 6 timeouts**, 1139,5 s,
campaña completa (sin muestreo). La sección «Supervivientes» del informe
dice literalmente «Ninguno: cada mutación aplicada la cazó al menos un
test», así que no queda ningún análisis en `PENDIENTE`.

## Trazabilidad de requisitos

23 de los 26 requisitos tienen al menos un test `test_f002_rN_*`. R15
(badges) y R16/R17 (infra) son los tres únicos sin test, y la propia spec
los declara de verificación MANUAL; ver más abajo.

R11 **sí tiene test desde la review**: era el único requisito que se
sostenía solo por inspección, y ahora lo cubre
`services/partes-transfer/tests/test_f002_r11_sin_postgresql.py` (ver
«Correcciones tras review»).

## Verificaciones MANUAL pendientes (del humano)

1. **Ejecutar el script de infra** (R17), tras `. .\00_vars_partes.ps1`:
   ```
   cd infra
   .\add_qtransfer_partes.ps1
   az storage queue list --account-name stpartespt7m3 --auth-mode login -o table
   ```
   Debe listar `q-transfer`, `q-transfer-result` y sus `-poison`.

   **Cambio tras la review**: el script ya no lee la clave de la cuenta;
   todo va con `--auth-mode login`. Eso significa que **quien lo ejecute
   necesita los roles de DATOS** sobre `stpartespt7m3` (Storage Queue Data
   Contributor y Storage Blob Data Contributor): «Contributor» del plano de
   control **no basta**. Si `az` responde `AuthorizationPermissionMismatch`,
   es eso y no otra cosa. La cabecera del script lo deja escrito.
2. **Comprobar que la escala de sv5 sigue intacta** (R16) — el propio
   script lo imprime al final; debe salir `Min 1 / Max 1`.
3. **Badges en el navegador** (R15): con Azurite, aprobar un parte y, tras
   recargar, ver el badge `⏳ encolado` y luego `✓ PT26/...`. Ctrl+F5 para
   los estáticos.
4. **Aviso de poison en el portal** (R23/R24): con un mensaje en
   `q-transfer-poison`, ver el badge en la cabecera y reencolarlo.
5. **Despliegue** (`redeploy_partes.ps1`), que los agentes no lanzan: el
   orden seguro ya existente (sv5 antes que sv4) es el correcto aquí.
6. **Push y PR** de esta rama y del commit `1440598` en `azure-apps`.

## Correcciones tras review

Veredicto **CHANGES_REQUESTED** de `progress/review_F-002.md`: un cambio
bloqueante, uno menor y dos mejoras sugeridas. Aplicados los cuatro, un
commit por cambio.

| # | Commit | Qué corrige |
|---|---|---|
| 1 | `5f51a82` | BLOQUEANTE: los tres paquetes `azure-*` en los manifiestos de sv4 y sv5 |
| 2 | `36c1c68` | MENOR: `_settings()` en `test_f002_degradacion.py:44,48` |
| 3 | `19f3347` | Mejora: `add_qtransfer_partes.ps1` sin clave de cuenta |
| 4 | `c18173d` | Mejora: test guardián de R11 |

Antes de empezar, el árbol traía dos ficheros marcados como modificados
(`services/partes-front/infrastructure/azure/credenciales.py` y
`services/partes-transfer/config/settings.py`). **No eran cambios**:
`git diff --numstat` salía vacío y `git ls-files --eol` daba `i/lf w/crlf`
en ambos. Era el rastro de los `git checkout` con los que el reviewer
restauró sus roturas de RED, que reescribieron los ficheros con CRLF.
Restaurados; el contenido nunca llegó a cambiar.

### 1. BLOQUEANTE — los paquetes `azure-*` en los manifiestos

El diagnóstico del reviewer era correcto y mi desviación 3 era **falsa**:
los tres paquetes se instalaron en el `.venv` de la raíz, que es lo que
ejecuta la suite, pero **no se declararon** en los `requirements.txt` que
`build_images_partes.ps1` copia al contexto de build. La imagen no los
habría instalado y sv4 y sv5 habrían muerto en el import de `main.py`. La
desviación 3 del informe queda corregida arriba, diciendo lo que pasó.

Añadidos a ambos manifiestos con los **mismos pines que sv3**:

```
$ grep -n "azure-" infra/manifests/sv4/requirements.txt infra/manifests/sv5/requirements.txt
infra/manifests/sv4/requirements.txt:12:azure-identity>=1.17
infra/manifests/sv4/requirements.txt:13:azure-storage-queue>=12.10
infra/manifests/sv4/requirements.txt:14:azure-storage-blob>=12.20
infra/manifests/sv5/requirements.txt:8:azure-identity>=1.17
infra/manifests/sv5/requirements.txt:9:azure-storage-queue>=12.10
infra/manifests/sv5/requirements.txt:10:azure-storage-blob>=12.20

$ diff <(grep '^azure-' infra/manifests/sv3/requirements.txt) <(grep '^azure-' infra/manifests/sv4/requirements.txt) \
  && diff <(grep '^azure-' infra/manifests/sv3/requirements.txt) <(grep '^azure-' infra/manifests/sv5/requirements.txt) \
  && echo "PINES IDENTICOS A sv3"
PINES IDENTICOS A sv3
```

Que las tres distribuciones declaradas son **exactamente** las que proveen
los tres paquetes importados, comprobado contra los metadatos instalados y
no de memoria:

```
$ python -c "from importlib.metadata import version; ..."
azure.identity           <- azure-identity           instalado 1.25.3
azure.storage.queue      <- azure-storage-queue      instalado 12.17.0
azure.storage.blob       <- azure-storage-blob       instalado 12.30.0
```

El arranque simulado sin las librerías —la reproducción del reviewer— ya no
es reproducible aquí, porque el fallo no estaba en el código sino en un
fichero que la suite local no consume: la prueba de que está cerrado es que
los manifiestos las declaran. Lo que **sí** queda comprobado de forma
ejecutable es el caso de sv5, por el guardián nº 4: su test de manifiesto
lee `infra/manifests/sv5/requirements.txt` de verdad y falla si su
contenido no es el esperado.

**Lo que este arreglo NO cubre, y conviene decirlo**: sigue sin haber nada
que impida repetir el fallo en sv4 o en cualquier otro servicio. La causa
raíz es la que el reviewer describe en su automejora nº 2 (la suite corre
contra un `.venv`, el contenedor instala otro fichero, y ningún checkpoint
cruza ambos). El arreglo correcto es esa comprobación en `init.sh`, que es
decisión del humano y del arnés genérico; no la he improvisado aquí.

### 2. MENOR — `_settings()` en el test de degradación

Aplicado en las dos líneas. Antes de tocarlas comprobé que el problema era
real y no teórico, **sin volcar ni modificar el `.env` del desarrollador**:

```
$ cd services/partes-front && python -c "..."
sv4 resuelve el .env por ruta ABSOLUTA: C:\...\services\partes-front\.env
  ese fichero existe en esta maquina: True

El fichero .env es una FUENTE REAL de esta asercion:
  Settings(_env_file=<fichero con COLAS_ACCOUNT_URL>).transfer_queue_enabled = True
  Settings(_env_file=None).transfer_queue_enabled                            = False
```

Y la RED, simulando el `.env` de quien haya seguido la guía de trabajo
local de esta misma feature (Azurite), que es la trampa concreta
(`scratchpad/red_env_dependiente.py`, fuera del repositorio):

```
Simulando .env del desarrollador: .env con COLAS_CONNECTION_STRING=UseDevelopmentStorage=true

--- Asercion ANTIGUA (linea 42, `Settings()` a pelo) ---
  FALLA: AssertionError -> transfer_queue_enabled es True porque lo enciende
  el .env del desarrollador, no el test

--- Asercion NUEVA (`_settings()`, con _env_file=None) ---
  PASA: el .env de la maquina es irrelevante
```

Se añade al test un docstring con el porqué, para que no vuelva a colarse.

### 3. Mejora — `add_qtransfer_partes.ps1` sin clave de cuenta

Las tres operaciones de datos (crear las cuatro colas, crear el contenedor
y listar las colas) pasan a `--auth-mode login`, y desaparece todo el
manejo de `$STKEY`. Rastro que queda de la clave, **cero**:

```
$ grep -n "account-key\|STKEY\|keys list" infra/add_qtransfer_partes.ps1
(sin coincidencias)

$ grep -n "auth-mode" infra/add_qtransfer_partes.ps1
26:# Todo el acceso de datos va con --auth-mode login (el token de 'az login'),
36:#     az storage queue list --account-name stpartespt7m3 --auth-mode login -o table
78:                 "--account-name",$STORAGE,"--auth-mode","login",
86:         "--account-name",$STORAGE,"--auth-mode","login",
91:az storage queue list --account-name $STORAGE --auth-mode login `
```

Encoding respetado (el fichero es ASCII, CRLF, sin BOM; el repositorio lo
guarda en LF vía `core.autocrlf`) y sintaxis validada con el parser real de
PowerShell 5.1, porque el script **no lo ejecuta ningún test**:

```
$ file infra/add_qtransfer_partes.ps1
infra/add_qtransfer_partes.ps1: ASCII text, with CRLF line terminators

PS> [System.Management.Automation.Language.Parser]::ParseFile(...)
PARSER OK: 0 errores de sintaxis (544 tokens) en PowerShell 5.1.26100.9168
```

**Contrapartida real, no gratuita**: `--auth-mode login` exige que **el
humano que ejecute el script** tenga los roles de datos sobre el storage
(Storage Queue/Blob Data Contributor). La Fase 1 se los concedió a la
managed identity `id-partes-dev`, no necesariamente a la persona. Con
`--account-key` bastaba «Contributor». Queda escrito en la cabecera del
script y en la verificación MANUAL nº 1 de este informe, con el error
concreto (`AuthorizationPermissionMismatch`) que se vería si falta.

### 4. Mejora — test guardián de R11

`services/partes-transfer/tests/test_f002_r11_sin_postgresql.py`, tres
tests. Vigila las tres puertas por las que entraría una BBDD en sv5: los
**imports** (con `ast`, no con `grep`, para que la mención en un comentario
—o la propia lista de prohibidos de ese fichero— no cuente), el
**manifiesto de despliegue** y los **campos de `Settings`** (R11 dice «ni
conexión ni CREDENCIAL»).

Un guardián que pasa el día que se escribe no demuestra nada, así que la
RED se hizo inyectando las tres violaciones a la vez —un módulo con `from
sqlalchemy.orm import Session`, `psycopg[binary]>=3.1` en el manifiesto y
un campo `pg_password` en `Settings`— y revirtiéndolas después
(`scratchpad/red_r11.py`, fuera del repositorio):

```
FFF                                                                      [100%]
E   AssertionError: sv5 no debe tener BBDD (R11), pero estos modulos importan un
    driver relacional: {'infrastructure/database/parte_repository.py': ['sqlalchemy']}...
E   AssertionError: requirements.txt de sv5 declara paquetes de BBDD: ['psycopg']...
E   AssertionError: Settings de sv5 expone campos de BBDD: ['pg_password']...
=========================== short test summary info ===========================
FAILED tests/test_f002_r11_sin_postgresql.py::test_f002_r11_ningun_modulo_de_sv5_importa_una_bbdd_relacional
FAILED tests/test_f002_r11_sin_postgresql.py::test_f002_r11_el_manifiesto_de_sv5_no_declara_ninguna_bbdd
FAILED tests/test_f002_r11_sin_postgresql.py::test_f002_r11_la_configuracion_de_sv5_no_expone_credenciales_de_bbdd
3 failed in 0.44s

--- revertido; git status del repo ---
?? progress/review_F-002.md
?? services/partes-transfer/tests/test_f002_r11_sin_postgresql.py
```

Cada uno falla por su motivo: ninguno pasa por casualidad ni tapa a otro.

### Verificación final de las correcciones

```
$ bash harness/init.sh
[OK] PUERTA COBERTURA: 97.4% de 648 líneas cambiadas cubiertas (631/648, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-002-cola-q-transfer
ENTORNO LISTO. Puedes trabajar.
    6 passed (raíz) · 112 passed (sv4) · 87 passed (sv5)

$ cd services/partes-front  && python -m pytest tests -q   ->  112 passed in 4.64s
$ cd services/partes-transfer && python -m pytest tests -q ->   87 passed in 2.77s
```

**La campaña de mutación NO se ha vuelto a lanzar, y con motivo medido**:
ninguna corrección toca código de producción Python (son dos `.txt`, un
`.ps1` y dos ficheros de test), así que el alcance y los mutantes son los
mismos. Comprobado, no supuesto:

```
$ python -c "from harness.alcance import alcance_de_feature; ..."
alcance: F-002: 24 fichero(s), 1630 línea(s) de producción
mutantes generables sobre el alcance actual: 132
```

24 ficheros / 1630 líneas / 132 mutantes: **los mismos tres números** de la
campaña del 17:46 y del recálculo independiente del reviewer. La campaña
sigue siendo válida.

Ruff sigue en **442 avisos**, los mismos de antes de las correcciones: los
dos ficheros nuevos o tocados pasan `ruff check` limpios.

## Evidencias

Medidos en la última pasada de `bash harness/init.sh` (en verde) y en
`progress/mutacion_F-002.md` (campaña del 17:46).

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** | **205**, todos en verde: 6 raíz + 112 sv4 + 87 sv5 (eran 202 antes de la review; +3 del guardián de R11) |
| **Cobertura de las líneas cambiadas** | **97,4 %** (631 de 648), umbral 80 %, nivel crítico (sin cambio: las correcciones no tocan producción) |
| **Mutantes generados / supervivientes** | **132 generados, 132 evaluados, 126 muertos, 0 supervivientes**, 6 timeouts (campaña completa, sin muestreo; alcance y recuento reconfirmados tras las correcciones) |
| **Tiempo de ejecución de la suite** | raíz 0,05 s · sv4 9,35 s · sv5 3,97 s vía init.sh (directas: sv4 4,64 s · sv5 2,77 s; campaña de mutación: 1139,5 s) |

Los 17 huecos de cobertura que quedan son, en su mayoría, la rama de
`build_app` que construye `SessionFactory` contra PostgreSQL: no se puede
cubrir sin base de datos, y la regla dura prohíbe que los unit tests la
toquen.

## Estado del entorno al terminar

`bash harness/init.sh` en **verde** (reejecutado tras aplicar las cuatro
correcciones de la review). Avisos que quedan y NO son de esta
feature: ruff con 442 avisos de deuda previa (F-002 no añade ninguno:
eran 444 antes de empezar), y sv1, sv2, sv3 sin directorio de tests —sv4
y sv5 ya no aparecen en esa lista, porque esta feature les ha creado la
suya—. `infra` sigue sin `comando_tests` (es PowerShell).
