<!-- progress/review_F-002.md -->
# F-002 · Cola q-transfer para aprobación asíncrona — review

Rama `feature/F-002-cola-q-transfer`, contra `dev`. Spec R1–R26 / T1–T15.

- **Primera pasada** — HEAD `4f72189` — **CHANGES_REQUESTED**.
- **Segunda pasada** — HEAD `63b1afe` — **APPROVED**. Ver la sección
  «Segunda pasada» al final, que es la que manda. Lo que sigue hasta ahí se
  conserva **tal como se escribió** para que quede el rastro de qué se
  pidió y por qué; el único checkbox vacío queda cerrado allí.

## Veredicto de la primera pasada (histórico)

**CHANGES_REQUESTED**

Un solo motivo bloqueante, y no está en la lógica: **sv4 y sv5 importan tres
paquetes `azure-*` que sus manifiestos de despliegue no declaran**. La
imagen que construye `build_images_partes.ps1` no los instalará y ambos
contenedores morirán en el import de `main.py` en el próximo despliegue.
Lo demuestro reproducido más abajo (cambio requerido nº 1).

Quiero dejar claro lo que NO es este veredicto. El trabajo es de calidad
alta y su evidencia de rigor es **real**: he recalculado el alcance y los
mutantes de forma independiente y **coinciden exactamente** con el informe,
he matado 19 mutantes de muestra sin un solo superviviente, y he
**reproducido por mi cuenta** las tres roturas centrales (lock, synckey,
marcado). Nada de esto está inflado. El fallo es un hueco de despliegue que
ni la spec ni el informe cerraron, y que la suite —por construcción— no
podía ver.

## Nivel de rigor

Declarado **`critico`** en `harness/features.json` (`"rigor": "critico"`,
prioridad 2). Exige: C1–C5 + tests trazables + **fase RED** + **cobertura**
de líneas cambiadas ≥ 80 % + **campaña de mutación** con **cero
supervivientes** salvo justificación escrita + verificaciones `MANUAL
(humano)` listadas con comando exacto.

Las tres puertas están **satisfechas y verificadas de forma independiente**
(detalle en C4 bis). Ninguna se declara N/A.

## Verificación independiente ejecutada por el reviewer

No he dado por bueno ningún número del informe. Lo que he ejecutado:

| Comprobación | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual, dos veces) | **ENTORNO LISTO**, exit 0 |
| Suites vía init.sh | 6 raíz + 112 sv4 + 84 sv5 = **202**, verde |
| `pytest` directo en `services/partes-transfer/tests` | **84 passed** |
| `pytest` directo en `services/partes-front/tests` | **112 passed** |
| Puerta de cobertura (la imprime init.sh) | **97,4 %** de 648 líneas (631/648, umbral 80) |
| `harness.alcance` recalculado | **24 ficheros, 1630 líneas** — coincide exactamente con el informe |
| `harness.mutacion.generar_mutantes` recalculado | **132 mutantes** — coincide exactamente |
| Los 6 TIMEOUT declarados, contrastados con el generador | Los 6 existen, mismo operador y mismo texto original→mutado |
| Muestreo de mutantes (19: dirigido + aleatorio con semilla) | **19 muertos, 0 supervivientes** |
| RED R7/R19/R20 reproducida (lock decorativo) | Rompe como se anuncia |
| RED R8 reproducida (synckey anulada) | 2 tests caen |
| RED R12/R13 reproducida (condición anterior) | 2 tests caen |
| Árbol tras mis pruebas | `git status` **limpio**, init.sh verde de nuevo |

### Fase RED reproducida (lo importante, porque aquí la mutación no llega)

`registro_pipeline.py` aporta **90 líneas al alcance y 0 mutantes**: el
split en fases es movimiento de código y `with self._lock:` no ofrece
ningún operador mutable. Es decir, **la campaña de mutación no da ninguna
evidencia sobre el requisito central de la feature**. Por eso he
reproducido la rotura yo mismo, inyectando un lock decorativo por el
constructor (sin tocar el árbol, porque el lock es inyectable):

```
--- LOCK REAL (arbol tal cual) ---
  R19 max_concurrencia['escribir'] = 1   (el test exige 1)
  R20 partes creados = 1  cods = ['PT26/00001']
  R20 posiciones = [64, 128, 192]   (3 distintas)
--- LOCK DECORATIVO (rotura deliberada) ---
  R19 max_concurrencia['escribir'] = 3   (el test exige 1)
  R20 partes creados = 3  cods = ['PT26/00001', 'PT26/00001', 'PT26/00001']
  R20 posiciones = [64, 64, 64]   (el test exige 3 distintas)
```

Tres cabeceras para la misma obra y mes con el MISMO correlativo y tres
líneas en la misma posición: el daño exacto que la feature debía evitar.
Coincide con lo que el implementer reportó. **R7/R19/R20 sostenidos.**

R8: anulando el paso 6 (detección por synckey) caen
`test_f002_r8_ejecutar_dos_veces_no_duplica` y
`test_f002_r8_reentrega_no_duplica_lineas`. R12/R13: devolviendo la
condición de `ya_registradas` a la anterior (`not reg.sigrid_estado`),
caen dos tests de R12 con `AssertionError: assert 'encolado' ==
'registrado'` — la línea se quedaría en `encolado` para siempre estando ya
en Sigrid. Ambas roturas restauradas con `git checkout`.

## Checkpoints

### C1 — El arnés está completo y en verde
- [x] `bash harness/init.sh` termina con exit 0 (ENTORNO LISTO, verificado dos veces).
- [x] Existen CLAUDE.md, features.json, SPECS.md, current.md, history.md, ARCHITECTURE.md, CONVENTIONS.md.

### C2 — El estado es coherente
- [x] Una sola feature `in_progress` (F-002); init.sh lo valida.
- [x] Rama `feature/F-002-cola-q-transfer`, nunca `main`.
- [x] `current.md` describe solo la sesión activa de F-002.
- [x] F-001 (`done`) tiene su resumen en `history.md:8`.

### C3 — El código respeta arquitectura y convenciones
- [x] Hexagonal respetada. `domain/models/registro_models.py` importa solo `__future__`, `dataclasses` y `typing`. Los imports de `azure.*` y `sqlalchemy` viven solo en `infrastructure/`. Los consumidores de `interface_adapters/` reciben cola y blob por parámetro y no importan Azure.
- [x] Primera línea con la ruta relativa en los 30 ficheros `.py` del diff, más `static/app.js` y `static/styles.css`.
- [x] Sin `print()` de debug, sin `console.log`, sin TODO/FIXME, sin secretos hardcodeados. Barrido hecho (`AccountKey=`, `password`, `token`, `Bearer`, `-----BEGIN`, `subscription`, `tenant`, IPs, `.internal.`, `*.core.windows.net`, correos): **cero valores reales**. Lo que hay son alias de variables de entorno sin default, `DefaultAzureCredential` con managed identity, y una CS de Azurite en tests con la clave sustituida por `xxx`. Las únicas IPs son `127.0.0.1:10000/10001` (Azurite) y los binds por defecto.
- [ ] → **[x] en la segunda pasada** (commit `5f51a82`). **Sin dependencias nuevas no previstas en la spec.** ← **ÚNICO CHECKBOX VACÍO en la primera pasada.** `azure-storage-queue`, `azure-storage-blob` y `azure-identity` son dependencias nuevas y necesarias, pero **no están declaradas en `infra/manifests/sv4/requirements.txt` ni en `sv5/requirements.txt`**. Ver cambio requerido nº 1.
- [x] Reglas de dominio y las tres trampas del monorepo:
  - **empleado ≠ recurso**: intacta. El pipeline mueve código sin cambiar decisiones; los tests de regresión se anclaron contra el pipeline previo y yo he confirmado por RED que la semántica se sostiene.
  - **incidencias**: no se tocan.
  - **schema duplicado**: **CERO cambios** en `orm_models.py` (ninguna de las dos copias) y **cero** en `reglas_registro.py`, confirmado sobre `git diff dev...HEAD --name-only`. Los estados nuevos (`encolado`/`conflicto`/`error`) son valores de una `String(16)` existente: no hay cambio de schema. Tampoco se toca `sigrid_write_client.py` ni ninguna copia de los clientes Sigrid, ni sv1/sv2/sv3.

### C3 bis — Documentos de fuera
**N/A justificado**: el diff no añade ni modifica ningún fichero en
`docs/referencia/` (verificado sobre `git diff dev...HEAD --name-only`). Sin
documentos nuevos no hay cabecera, original ofimático ni barrido que exigir.

### C4 — La verificación es real
- [x] Trazabilidad requisito → test: **22 de 26** requisitos tienen ≥1 test `test_f002_rN_*` (tabla abajo). Los 4 restantes, justificados:
  - **R15** (badges), **R16** (escala sv5), **R17** (colas en Storage): la propia spec los declara de verificación **MANUAL** (`requirements.md:102-114`, `tasks.md:96-127`). No son N/A a secas: tienen su comando exacto en `current.md`.
  - **R11** (sv5 sin PostgreSQL): requisito negativo/estructural, sin test propio. **Lo he verificado por inspección**: cero imports de `sqlalchemy`/`psycopg` en todo sv5, y su `requirements.txt` no trae PG. Se sostiene, pero ver mejora sugerida nº 2.
- [x] Los unit tests no tocan red, BBDD ni Azure real. `QueueServiceClient`/`BlobServiceClient` se sustituyen por dobles con `monkeypatch.setattr` **antes** de construir nada; `DefaultAzureCredential` nunca se ejecuta; PostgreSQL es **SQLite en memoria** (`sqlite://` con `StaticPool`); `TestClient` usa transporte ASGI en proceso. Importar `main.py` no tiene efectos: todo el cableado vive en `main()` tras `if __name__ == "__main__":` (línea 103 en ambos servicios), y lo he comprobado importándolo. *(Un matiz de higiene en el cambio requerido nº 2.)*
- [x] Verificaciones `MANUAL (humano)` listadas en `current.md:90-107` con comando exacto y pendientes del humano.

### C4 bis — El rigor declarado se cumple
- [x] `rigor: "critico"` declarado con valor válido.
- [x] **Fase RED**: el informe trae trazas reales por tarea (T1–T11), no «se hizo TDD». Además reproduje por mi cuenta las tres roturas centrales.
- [x] **Cobertura**: puerta en `[OK]`, **97,4 %** de 648 líneas cambiadas (umbral 80, nivel critico). Los 17 huecos son la rama de `build_app` que construye `SessionFactory` contra PostgreSQL, incubrible sin BBDD.
- [x] **Mutación**: existe `progress/mutacion_F-002.md` generado por la herramienta. **Totales verificados de forma independiente**: alcance 24 ficheros / 1630 líneas y **132 mutantes**, ambos coincidentes al dígito con mi recálculo. La campaña declara 132 evaluados, así que no aplica la prueba de control de «cero mutantes».
- [x] **Cero supervivientes**, ninguno en `PENDIENTE`. Muestreé 19 mutantes (dirigidos a los ficheros críticos + aleatorios con semilla fija) y **murieron los 19**. Los 6 TIMEOUT existen como mutantes reales y su tratamiento —anulan la parada del bucle, así que cuelgan la suite en vez de pasar desapercibidos— está argumentado y lo comparto.
- [x] Sección **«Evidencias»** con los cuatro números (tests, cobertura, mutantes/supervivientes, tiempo de suite).
- [x] Ningún punto N/A sin justificación escrita.

### C4 ter — Rutas sensibles
**N/A justificado**: este repositorio **no declara** `harness/rutas_sensibles.json`
(solo existe el `.ejemplo.json`). Sin declaración el bloque es N/A por
configuración, según la propia cabecera del checkpoint.

### C5 — La sesión se cerró bien
- [x] `tasks.md` con las **15 tareas `[x]`** y un commit `F-002 Tn: ...` por tarea (T1→`7540c29` … T15→`bc44ed9`), más 3 commits de cierre de rigor y 4 de spec.
- [x] Sin ficheros temporales ni artefactos sin trackear (`git status --porcelain -uall` vacío). Los scripts auxiliares del implementer vivieron fuera del repositorio.
- [x] `features.json` refleja el estado real: F-002 sigue `in_progress` a la espera de este veredicto, y F-008 queda anotada como backlog de la decisión de roles.

## Cobertura requisito → test

| Req | Tests trazables | Nº |
|---|---|---|
| R1 | `test_f002_r1_publica_blob_y_mensaje`, `test_f002_r1_encolar_responde_asincrono_sin_esperar_a_sigrid` | 8 |
| R2 | `test_f002_r2_marca_encolado`, `test_f002_r2_encolar_deja_las_lineas_en_encolado` | 6 |
| R3 | `test_f002_r3_fallback_sincrono`, `test_f002_r3_transfer_queue_enabled_reconoce_las_dos_formas` | 4 |
| R4 | `test_f002_r4_preflight_sigue_siendo_http_sincrono` | 2 |
| R5 | `test_f002_r5_pisar_claves_no_entra_por_la_cola` | 4 |
| R6 | `test_f002_r6_*` (handler de q-transfer) | 6 |
| R7 | `test_f002_r7_el_lock_lo_adquiere_registrar_no_el_llamante` | 4 |
| R8 | `test_f002_r8_ejecutar_dos_veces_no_duplica`, `test_f002_r8_reentrega_no_duplica_lineas` | 3 |
| R9 | `test_f002_r9_fallo_infra_relanza`, poison tras `max_dequeue` | 12 |
| R10 | `test_f002_r10_conflictos_no_confirmados_no_se_escriben` | 4 |
| **R11** | **sin test** — verificado por inspección (sv5 sin imports de BBDD ni PG en su manifiesto) | 0 |
| R12 | `test_f002_r12_marca_el_resultado_por_linea`, `test_f002_r12_consumer_actualiza_sigrid` | 16 |
| R13 | `test_f002_r13_aplicar_el_mismo_resultado_dos_veces_no_cambia_nada` | 3 |
| R14 | `test_f002_r14_error_global_marca_todas_las_lineas_de_la_peticion` | 10 |
| **R15** | **MANUAL por spec** (`node --check` + navegador) | 0 |
| **R16** | **MANUAL por spec** (escala sv5; el script la imprime) | 0 |
| **R17** | **MANUAL por spec** (colas en `stpartespt7m3`) | 0 |
| R18 | `test_f002_r18_preparacion_solapa` | 5 |
| R19 | `test_f002_r19_registrar_serializa_entre_peticiones` | 4 |
| R20 | `test_f002_r20_dos_peticiones_misma_obra_y_mes_crean_un_solo_parte` | 2 |
| R21 | `test_f002_r21_orden_no_garantizado` | 1 |
| R22 | `test_f002_r22_fallo_no_afecta_al_resto` | 2 |
| R23 | `test_f002_r23_cuenta_los_mensajes_aproximados` | 6 |
| R24 | `test_f002_r24_reencola_max_32`, `test_f002_r24_no_mueve_mas_del_tope` | 12 |
| R25 | `test_f002_r25_el_mensaje_se_borra_SOLO_tras_encolarlo` | 3 |
| R26 | `test_f002_r26_sin_colas_configuradas_el_endpoint_lo_dice` | 2 |

## Las dos desviaciones declaradas: juicio explícito

**1. La suite de sv4 no existía y el implementer la ha creado.**
**ACEPTADA, no requiere decisión humana.** El design afirmaba que «la suite
del servicio ya existe» (`design.md:265`) y era falso: `init.sh` venía
avisando de que nadie comprobaba sv4. La spec ya mandaba crear cuatro
ficheros de test para sv4; lo único que ha cambiado es que además hubo que
poner el `conftest.py` y los dobles. Va en la dirección de la spec, no en
contra, y cierra un agujero de verificación preexistente: sv4 y sv5 ya no
aparecen en la lista de servicios sin tests de `init.sh`. Es una mejora.

**2. `build_app` de sv4 acepta colaboradores por parámetro.**
**ACEPTADA, no requiere decisión humana.** El design ya bendecía
exactamente este patrón para sv5 (`build_app(settings, pipeline=None)`,
`design.md:296-299`); extenderlo a sv4 es aplicar la misma decisión ya
aprobada al otro servicio. Es **inyección de dependencias en la frontera de
composición**, que es justo lo que pide la arquitectura hexagonal de
`docs/ARCHITECTURE.md`, y es **estrictamente retrocompatible**: los cuatro
parámetros (`repository`, `transfer_client`, `publisher`, `cola_cliente`)
son keyword-only con default `None`, y la rama `None` construye igual que
antes (`app.py:249-257`). Sin ella no hay forma de levantar la app en un
test sin PostgreSQL, y la regla dura del CLAUDE.md prohíbe que los unit
tests toquen BBDD: la alternativa era no testear sv4.

Ninguna de las dos exige decisión humana. La que **sí** la exigía —el
reencolado de poison disponible para cualquier usuario autenticado— ya se
tomó y consta cerrada en `current.md:65-71`, con F-008 creada en el backlog
para restringirlo por roles.

## Los puntos que se me pidió vigilar

| Punto | Veredicto |
|---|---|
| Escritura en Sigrid estrictamente serializada | **OK.** El lock viaja en el constructor y lo adquiere `registrar`, así que ningún llamante puede olvidarlo; `_evaluar` (pasos 5–7: parte `hmo`, correlativo, synckeys, conflictos) corre **dentro** del lock, que es lo que exige R20. HTTP de pisado y workers comparten un único lock creado en `main.py`. Reproducido por RED. |
| Sin cambios en `orm_models.py` (ninguna copia) | **OK.** Cero. |
| Sin cambios en `reglas_registro.py` | **OK.** Cero. |
| Poison: send-antes-de-delete con allowlist | **OK.** `cola_cliente.mover` envía a la principal y **solo borra de la poison tras el send con éxito**; si el send falla, retorna sin borrar; si falla el delete, avisa y acepta el duplicado (benigno por R8/R13). El bucle está acotado por `maximo` también en número de vueltas, así que un delete que falla no lo vuelve infinito. La allowlist es **cerrada** (`COLAS_REENCOLABLES`, las dos colas de settings) y el sufijo `-poison` lo pone el servidor: el cliente nunca aporta un nombre de cola libre; fuera de la lista, 422. |
| Sin secretos ni URLs internas nuevas | **OK.** Barrido hecho, cero hallazgos. Ver C3. |
| `azure-apps/partes.md` refleja colas y contenedor | **OK.** Commit local `1440598`, sin push. Añade las dos colas y sus `-poison`, el contenedor `transfer`, las variables de entorno de sv4 y sv5, el script nuevo, el diagrama de doble canal, la resolución de «líneas atascadas en encolado», y **retira la línea de la hoja de ruta** ya cumplida. Deja escrito lo fácil de olvidar: sv5 no lleva KEDA y quitar `COLAS_ACCOUNT_URL` es el rollback. Sin secretos. |
| Nada del diff ataca Azure/Sigrid/PostgreSQL reales | **OK.** Ni en tests ni en imports. Ver C4. |

## Cambios requeridos

### 1. BLOQUEANTE — Declarar los paquetes `azure-*` en los manifiestos de sv4 y sv5

**Ficheros**: `infra/manifests/sv4/requirements.txt` e
`infra/manifests/sv5/requirements.txt`.

El código nuevo importa Azure **a nivel de módulo, sin guarda**:

- `services/partes-front/infrastructure/azure/credenciales.py:12` y
  `services/partes-transfer/infrastructure/azure/credenciales.py:12` →
  `from azure.identity import DefaultAzureCredential`
- `.../infrastructure/azure/cola_cliente.py:29` (sv4) y `:26` (sv5) →
  `from azure.storage.queue import QueueClient, QueueServiceClient`
- `.../infrastructure/azure/blob_cliente.py:16` (ambos) →
  `from azure.storage.blob import BlobServiceClient`

Y ambos `main.py` importan esa cadena **incondicionalmente**:
`services/partes-front/main.py:10` y `services/partes-transfer/main.py:27`
hacen `from infrastructure.azure.credenciales import (...)`.

Ninguno de los dos manifiestos declara un solo paquete `azure-*`, mientras
que **sv3, que ya usa colas, sí los declara** (`azure-identity>=1.17`,
`azure-storage-queue>=12.10`, `azure-storage-blob>=12.20`). El
`Dockerfile` de ambos servicios hace `RUN pip install -r requirements.txt`
y luego `CMD ["python", "main.py"]`, y `build_images_partes.ps1:59` copia
`manifests/svN/requirements.txt` al contexto de build **sobrescribiendo**
cualquier otro. La imagen, por tanto, no tendrá las librerías.

Reproducido bloqueando los paquetes `azure-*` en el import, que es
exactamente la imagen que se construiría:

```
########## partes-transfer (imagen sin azure-*) ##########
FALLO DE ARRANQUE -> No module named 'azure'
    File "...\services\partes-transfer\main.py", line 27, in <module>
    from infrastructure.azure.credenciales import (
    File "...\infrastructure\azure\credenciales.py", line 12, in <module>

########## partes-front (imagen sin azure-*) ##########
FALLO DE ARRANQUE -> No module named 'azure'
    File "...\services\partes-front\main.py", line 10, in <module>
    from infrastructure.azure.credenciales import (
```

**Consecuencia**: el próximo `redeploy_partes.ps1` deja a **sv5 y a sv4 —el
portal, que da la cara al usuario— en crash-loop**. Y el fallback R3 **no
protege**: es una comprobación de *runtime* sobre settings, mientras que el
import es de *carga*; sin `COLAS_ACCOUNT_URL` el contenedor muere igual.
La suite local no lo detecta porque el implementer instaló las librerías en
el `.venv` de la raíz (desviación 6 de su informe), que no es lo que se
despliega.

Esto vuelve inexacta la desviación 3 del informe
(`progress/impl_F-002.md:82-86`), que dice «**Dependencias nuevas en los
manifiestos** de sv4 y sv5» dándolo por hecho. No están.

**Arreglo**: añadir a **ambos** manifiestos, con los mismos pines que sv3
para no divergir:

```
azure-identity>=1.17
azure-storage-queue>=12.10
azure-storage-blob>=12.20
```

Y corregir la desviación 3 del informe para que diga lo que se hizo.

### 2. MENOR — `Settings()` sin `_env_file=None` lee el `.env` real del desarrollador

**Fichero**: `services/partes-front/tests/test_f002_degradacion.py:44` y `:48`.

El propio fichero define el helper correcto en `:28-29`
(`Settings(_env_file=None)`) y lo usa en `:43`, pero las dos líneas
siguientes llaman a `Settings()` a pelo. Como sv4 resuelve el `.env` por
**ruta absoluta** (`config/settings.py:10`), esas dos aserciones leen
`services/partes-front/.env`, que existe en la máquina y está gitignored.

Hoy pasa (ese `.env` no tiene claves `COLAS_*`/`BLOBS_*`, lo he
comprobado sin volcar su contenido), y además el `delenv` de `:46` no
anula lo que venga del fichero. Pero el test queda **dependiente de la
máquina**, y la trampa es concreta: la guía de trabajo local de esta misma
feature invita a poner Azurite en el `.env`. El resto de la suite sí se
protege —`test_f002_aprobar_encolar.py:47-54` lleva incluso un docstring
explicando este problema, y sv5 usa `monkeypatch.chdir(tmp_path)`—, así
que es una inconsistencia, no un criterio nuevo.

**Arreglo**: usar `_settings()` en `:44` y `:48`.

## Mejoras sugeridas (no bloquean)

1. **`add_qtransfer_partes.ps1:64` maneja la clave del storage.** Hace
   `az storage account keys list ... -o tsv` a `$STKEY` y la pasa como
   `--account-key` (`:71-72`, `:79-80`, `:84`). No se persiste ni se
   imprime, pero viaja en la línea de comandos del proceso. El propio
   script ya usa `--auth-mode login` en la comprobación documentada de
   `:31`: usarlo también aquí evita la clave por completo.
2. **R11 merece un test guardián.** «sv5 no debe tener conexión ni
   credencial de PostgreSQL» es el requisito que sostiene la decisión
   central del design (no crear una tercera copia de `orm_models.py`), y
   hoy solo se sostiene por inspección. Un test barato —que ningún módulo
   de sv5 importe `sqlalchemy`/`psycopg` y que su `requirements.txt` no
   los traiga— lo convertiría en regresión detectable.

## Automejora del arnés (propuesta, no aplicada)

Esta feature destapó **dos huecos del protocolo**, y los dos son
generalizables a cualquier proyecto, así que —si el humano los aprueba—
tocaría portarlos a `arnes-base` en el mismo trabajo.

1. **La mutación puede dar cero mutantes sobre el requisito central sin que
   nadie se entere.** `registro_pipeline.py` aportó 90 líneas al alcance y
   **0 mutantes**: un refactor de movimiento con `with lock:` no tiene
   operadores mutables. La campaña sale en verde perfecto y no dice
   absolutamente nada del invariante que la feature existía para proteger.
   El `CHECKPOINTS.md` ya obliga a la prueba de control cuando la campaña
   **entera** declara cero mutantes, pero no cuando el cero es **por
   fichero**. Propongo extender C4 bis: *si un fichero del alcance con más
   de N líneas cambiadas genera 0 mutantes, el reviewer debe exigir
   evidencia alternativa* (fase RED específica sobre ese fichero, como el
   lock decorativo de aquí). Que la evidencia existiera en esta feature fue
   mérito del implementer, no del protocolo.

2. **Ningún checkpoint mira si lo que se despliega puede arrancar.** C1–C5
   cubren tests, cobertura, mutación, convenciones y arquitectura, y las
   cinco puertas salieron verdes con un fallo que tumba dos servicios en
   producción. La suite corre contra el `.venv` de desarrollo; el
   contenedor instala otro fichero. Propongo un punto en C3 (o C4):
   *si el diff añade un `import` de tercero en código de producción,
   verificar que el paquete está declarado en el manifiesto de despliegue
   del servicio que lo importa*. Es automatizable en `init.sh` para
   proyectos Python (cruzar los imports de nivel superior del diff contra
   el `requirements.txt` del servicio) y habría cazado esto solo.

---

# Segunda pasada — HEAD `63b1afe`

## Veredicto

**APPROVED**

Los dos cambios requeridos están aplicados y **verificados por mi cuenta**,
no por lo que dice el informe; las dos mejoras sugeridas también. El delta
desde `4f72189` toca **exactamente** lo pedido y **ni una línea de código de
producción**, así que todo lo que aprobé en la primera pasada sigue en pie
sin necesidad de rehacerlo: mismo alcance, misma cobertura, misma campaña de
mutación (las tres cifras recalculadas más abajo).

## Qué he ejecutado en esta pasada

| Comprobación | Resultado |
|---|---|
| `bash harness/init.sh` (tal cual) | **ENTORNO LISTO**, `exit=0` |
| Suites vía init.sh | 6 raíz + 112 sv4 + **87** sv5 = **205**, verde (eran 202; +3 del guardián de R11) |
| Puerta de cobertura | **[OK] 97,4 %** de 648 líneas (631/648, umbral 80, nivel critico) |
| `alcance_de_feature('F-002')` recalculado | **24 ficheros, 1630 líneas** — idéntico al de la campaña |
| `generar_mutantes` recalculado sobre ese alcance | **132 mutantes** — idéntico |
| Delta `4f72189..HEAD`: ficheros `.py` de producción | **ninguno** (solo 2 `.txt`, 1 `.ps1`, 2 tests y `progress/`) |
| Arranque simulado sv4 y sv5 con el manifiesto de hoy | **ARRANQUE OK**, `exit=0` en ambos |
| Control del arranque simulado (manifiesto sin `azure-*`) | **FALLO reproducido**, `exit=1` en ambos |
| Guardián R11: las 3 puertas, con violación inyectada | **las 3 en rojo**, cada una por su motivo |
| `add_qtransfer_partes.ps1`: bytes y parser | sin BOM, **166/166 CRLF**, ASCII puro, **0 errores** de parser PS 5.1 |
| `ruff check` sobre los dos ficheros de test tocados | **All checks passed** (total del repo sigue en 442, deuda previa) |
| Barrido de secretos/debug sobre el delta | **cero hallazgos** (los 3 positivos son la palabra «Todo» en comentarios y un `password` dentro de un regex) |
| `git status --porcelain -uall` tras mis pruebas | **vacío** |

## 1. BLOQUEANTE — paquetes `azure-*` en los manifiestos · **CERRADO**

Ambos manifiestos declaran los tres paquetes con **los pines exactos** que
pedí, los mismos de sv3 (commit `5f51a82`):

```
infra/manifests/sv4/requirements.txt:12-14   infra/manifests/sv5/requirements.txt:8-10
azure-identity>=1.17                         azure-identity>=1.17
azure-storage-queue>=12.10                   azure-storage-queue>=12.10
azure-storage-blob>=12.20                    azure-storage-blob>=12.20
```

El implementer escribe que «el arranque simulado ya no es reproducible
aquí». **Sí lo es, y lo he reproducido**, porque la pregunta correcta no es
si falla sin las librerías sino si **arranca con lo que el manifiesto
instala**. Monté la imagen simulada: un `meta_path` finder que niega todo
módulo que no provenga de una distribución declarada en
`infra/manifests/svN/requirements.txt`, **más su cierre transitivo
respetando los marcadores de extra** (pip instala `uvicorn[standard]`, no
todos los extras de todo), y ejecuté `main.py` entero:

```
########## partes-transfer — manifiesto tal cual esta hoy ##########
  ARRANQUE OK: main.py importado entero          exit=0
########## partes-front — manifiesto tal cual esta hoy ##########
  ARRANQUE OK: main.py importado entero          exit=0
```

Y —esto es lo que hace que la prueba valga algo— **el control con las tres
líneas quitadas vuelve a romper por el mismo sitio exacto que en la primera
pasada**:

```
########## partes-transfer — manifiesto SIN los azure-* (control) ##########
  File "...\services\partes-transfer\main.py", line 27, in <module>
  FALLO DE ARRANQUE -> ModuleNotFoundError: No module named 'azure'   exit=1
########## partes-front — manifiesto SIN los azure-* (control) ##########
  File "...\services\partes-front\main.py", line 10, in <module>
  FALLO DE ARRANQUE -> ModuleNotFoundError: No module named 'azure'   exit=1
```

Aviso metodológico, por si alguien repite esto: mi **primer** intento de
control dio verde en falso. Al calcular el cierre transitivo sin mirar los
marcadores, `pydantic-settings` arrastraba su extra `azure-key-vault` y
colaba `azure-identity` por la puerta de atrás. Un control que no falla
cuando debe no prueba nada; hubo que arreglar el instrumento antes de
creerse el resultado.

Cerrado además el caso general: he cruzado **todos** los imports de tercero
del código de producción de sv4 y sv5 contra sus manifiestos y no queda
**ninguno sin cubrir**.

La desviación 3 del informe está corregida (`impl_F-002.md:88-97`) y no
maquilla nada: dice literalmente «Lo declaré por hecho sin comprobarlo».

## 2. MENOR — `Settings()` a pelo en el test de degradación · **CERRADO**

`test_f002_degradacion.py` ya no construye `Settings()` sin `_env_file`. La
única coincidencia de la cadena en el fichero está **dentro del docstring**
que explica por qué no se debe hacer (`:43`). El test ya no depende del
`.env` de la máquina.

## Mejora 1 — `add_qtransfer_partes.ps1` sin clave de cuenta · **APLICADA**

`grep -i "account-key|keys list|STKEY|account_key|sas"` → **sin
coincidencias**. Las tres operaciones de datos (crear las 4 colas, crear el
contenedor, listar) van con `--auth-mode login` (`:78`, `:86`, `:91`).
Fichero sin BOM, 166 líneas CRLF sin un solo LF suelto, ASCII puro, y el
parser real de PowerShell 5.1 lo acepta con **0 errores** — importante
porque este script **no lo ejecuta ningún test**.

La contrapartida operativa (hacen falta los roles de **datos** sobre el
storage; «Contributor» no basta, y el síntoma sería
`AuthorizationPermissionMismatch`) está escrita **en los tres sitios donde
hace falta**: cabecera del script `:26-30`, verificación MANUAL nº 1 del
informe, y `current.md:95` ya usaba `--auth-mode login`. No queda ninguna
instrucción que contradiga al script.

## Mejora 2 — guardián de R11 · **APLICADA, y de las buenas**

`services/partes-transfer/tests/test_f002_r11_sin_postgresql.py`, 3 tests,
verde. Cubre las tres puertas por las que entraría una BBDD en sv5:
imports (con `ast`, no `grep` —así la propia lista `PROHIBIDOS` del fichero
no se autoacusa), manifiesto de despliegue, y campos de `Settings`.

Un guardián solo vale si **falla cuando debe**, así que lo he roto yo, por
separado y sin dejar rastro (`git status` vacío después):

```
# puerta 1 — modulo temporal con "from sqlalchemy import create_engine"
E   AssertionError: sv5 no debe tener BBDD (R11), pero estos modulos importan
    un driver relacional: {'infrastructure/_regresion_temporal.py': ['sqlalchemy']}
    1 failed in 0.48s
# puerta 2 — MANIFIESTO redirigido a uno con psycopg[binary]
PUERTA MANIFIESTO: RED -> requirements.txt de sv5 declara paquetes de BBDD: ['psycopg']
# puerta 3 — Settings falso con un campo pg_dsn
PUERTA SETTINGS: RED -> Settings de sv5 expone campos de BBDD: ['pg_dsn']
```

Las tres son sensibles y cada una falla por su motivo. R11 pasa de
«verificado por inspección del reviewer» a **regresión detectable**: en la
tabla de trazabilidad, R11 deja de estar en 0 tests. Quedan 3 requisitos sin
test automático (R15, R16, R17), los tres **MANUAL por spec**.

Detalle que agradezco y que no me esperaba: el test importa `Settings` pero
**no lo instancia** (lee `Settings.model_fields`), así que no toca el `.env`
de nadie. No introduce la misma trampa que acabábamos de quitar en sv4.

## Cobertura y mutación tras el delta · siguen válidas

El alcance **no ha crecido**: `harness.alcance` da los mismos **24 ficheros
/ 1630 líneas** y `generar_mutantes` los mismos **132 mutantes** que la
campaña del 17:46 y que mi recálculo de la primera pasada. Es coherente con
el delta, que no toca ni un `.py` de producción (los ficheros nuevos son
tests, y los tests no entran en el alcance). **No hacía falta relanzar la
campaña**, y el informe lo justifica con ese mismo recálculo en vez de
darlo por supuesto (`impl_F-002.md:552-565`). No aplica la prueba de control
de «cero mutantes»: la campaña declara 132 evaluados.

La puerta de cobertura sigue en `[OK] 97,4 %`, mismo numerador y
denominador.

## Checkpoints tras la segunda pasada

- **C1** [x] · **C2** [x] · **C3** [x] · **C3 bis** N/A justificado (el diff
  no toca `docs/referencia/`) · **C4** [x] · **C4 bis** [x] · **C4 ter** N/A
  justificado (el repo no declara `harness/rutas_sensibles.json`) ·
  **C5** [x].
- El **único checkbox vacío** de la primera pasada —dependencias nuevas no
  declaradas, en C3— queda **marcado**: los tres paquetes están en ambos
  manifiestos y el arranque simulado lo demuestra.
- C4: la trazabilidad mejora (R11 con test propio). C5: `tasks.md` con
  **15 [x] y 0 [ ]**, árbol limpio, `features.json` con F-002 aún
  `in_progress` a la espera de este veredicto y `rigor: critico`.
- **Ningún N/A sin justificación escrita.**
- La sección **«Evidencias»** del informe trae los cuatro números
  actualizados (205 tests, 97,4 %, 132/0 supervivientes, tiempos).

## Higiene del delta

Los 6 commits desde `4f72189` son uno por arreglo, con mensaje que explica
**por qué** y no solo qué, más los dos de documentación:

| Commit | Qué |
|---|---|
| `5f51a82` | manifiestos sv4/sv5 + corrección de la desviación 3 |
| `36c1c68` | `_settings()` en el test de degradación |
| `19f3347` | script de infra con `--auth-mode login` |
| `c18173d` | guardián de R11 |
| `1aa4313` | sección «Correcciones tras review» |
| `63b1afe` | versiona `progress/review_F-002.md` (mi entregable, sin tocarlo) |

Nada fuera de lo pedido. Ningún `push`, ningún PR (siguen en la lista de
pendientes del humano, junto con el commit `1440598` de `azure-apps`).

## Lo que este APPROVED no cubre (para el humano, no bloquea)

1. **Las verificaciones MANUAL siguen pendientes**, y una cambió de
   requisitos: `add_qtransfer_partes.ps1` ahora exige que **la persona** que
   lo ejecute tenga Storage Queue/Blob **Data** Contributor sobre
   `stpartespt7m3`. La Fase 1 concedió esos roles a la managed identity
   `id-partes-dev`, no necesariamente al humano. Es un cambio a mejor —la
   clave de cuenta abre el storage entero— pero puede sorprender al
   ejecutarlo.
2. **La causa raíz del bloqueante sigue viva.** El arreglo pone los
   paquetes; nada impide que el próximo import de tercero se olvide otra
   vez en cualquier servicio. El propio implementer lo dice y hace bien en
   **no** improvisar la solución (`impl_F-002.md:428-433`): es mi automejora
   nº 2, y es decisión del humano y del arnés genérico. **Mantengo las dos
   propuestas de automejora de la primera pasada**; esta pasada refuerza la
   nº 2, porque el fallo se cerró a mano y a mano se puede repetir.
