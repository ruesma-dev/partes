<!-- specs/F-017-identidad-easy-auth/requirements.md -->
# F-017 · Identidad real de Easy Auth en el portal (sv4) — Requisitos

> **De dónde viene**: hallazgo del spec-author de F-016 (2026-08-19),
> verificado por el líder y ampliado por el material de
> `specs/F-016-admin-empleado-jornada/design.md` **§14**. sv4 está detrás de
> Easy Auth (Entra), pero **no hay ni una referencia a `X-MS-CLIENT-PRINCIPAL`
> en todo el repositorio**: las once escrituras de auditoría del portal se
> firman con la variable `DEFAULT_REVIEWER`, igual para todos.
>
> **Hallazgo del 2026-08-20 (verificación del despliegue, `progress/current.md`
> H1)**: `DEFAULT_REVIEWER` **no está configurada** en el Container App
> `ca-sv4-front`, y `.env.example` la declara vacía. Es decir: `_actor`
> devuelve `None` y **la auditoría del portal lleva `NULL` desde el primer
> despliegue**. Confirmado contra la base real (`progress/
> verif_esquema_partes_20260820.md`): las filas de `empleado_jornada` creadas
> desde el portal el 2026-08-20 tienen `created_by` y `updated_by` a `NULL`.
>
> El enunciado original de la feature («pasar del valor genérico al usuario
> real») **es incorrecto**: hoy no hay ni genérico. Eso cambia dos cosas —
> el problema de las filas históricas es más simple (no hay autores que
> convivan, hay ausencia) y el valor de la feature es mayor (hoy la auditoría
> del portal está en blanco).
>
> **Decisión del humano del 2026-08-20**: NO se pone un `DEFAULT_REVIEWER`
> provisional mientras tanto. Por tanto **el fallback que diseñe esta feature
> es el único que va a existir**.
>
> **Punto de apoyo ya construido**: `_actor(request)` en
> `services/partes-front/interface_adapters/web/app.py:477`, que F-016 dejó
> escrito con este docstring literal: *«cuando F-017 llegue solo cambia el
> INTERIOR de esta función»*. Comprobado en el árbol el 2026-08-20: es cierto,
> pero **solo cubre las 5 escrituras de F-016**; las otras 11 leen
> `settings.default_reviewer` a pelo. Esta feature las hace pasar todas por
> ese mismo helper.

---

## 0. La frontera de esta feature (léase antes que nada)

Tres features distintas que es fácil confundir:

| Feature | La pregunta que responde | Estado |
|---|---|---|
| **F-017 (esta)** | **«¿QUIÉN hizo esto?»** — poner un nombre real en las columnas de autor que ya existen | esta spec |
| **F-008** | «¿QUIÉN PUEDE hacerlo?» — roles y permisos leídos de los claims de Entra | `pending`, prioridad 12 |
| **F-018** | «¿QUÉ pasó en la aplicación?» — log de auditoría de acciones, tabla propia, con pantalla o sin ella | `pending`, prioridad 9, **depende de esta** |

**F-017 no restringe nada a nadie.** Después de esta feature, exactamente los
mismos usuarios pueden hacer exactamente las mismas cosas que antes; lo único
que cambia es que la fila queda firmada. Cualquier requisito que empiece por
«solo el usuario X puede…» **no es de esta feature**: es F-008.

**F-017 no crea ninguna tabla ni ninguna columna.** Rellena columnas que ya
existen. Si durante la implementación parece que hace falta una tabla de
auditoría, un histórico o una columna nueva, eso **es F-018**: parar y
consultar (ver `design.md` §11, DA6).

---

## 1. Requisitos EARS

### 1.1 Resolución de la identidad

**R1.** CUANDO llega una petición HTTP al portal con la cabecera
`X-MS-CLIENT-PRINCIPAL-NAME` con contenido no vacío, el sistema debe usar su
valor —normalizado según R4— como actor de todas las escrituras de auditoría
que produzca esa petición.

**R2.** CUANDO llega una petición sin `X-MS-CLIENT-PRINCIPAL-NAME` (ausente o
en blanco) pero **con** `X-MS-CLIENT-PRINCIPAL`, el sistema debe decodificar
ese token (base64 de un JSON de claims) y tomar como actor el primer claim no
vacío de esta lista de preferencia, en este orden: `preferred_username`,
`upn`, `email`, `emails`, `name`.

**R3.** SI `X-MS-CLIENT-PRINCIPAL` no es base64 válido, no decodifica a JSON,
no tiene la estructura esperada o no trae ninguno de los claims de R2,
ENTONCES el sistema debe tratar la cabecera como ausente, continuar con el
fallback de R5 y **no elevar ninguna excepción**.

**R4.** El sistema debe normalizar todo actor antes de guardarlo: recortar
espacios de los extremos, eliminar los caracteres de control (incluidos `\r`
y `\n`), pasar a minúsculas y truncar a **120 caracteres**.

**R5.** MIENTRAS el proceso **no** esté desplegado (desarrollo local) y no
llegue ninguna de las dos cabeceras de Easy Auth, el sistema debe resolver un
actor de desarrollo local con el prefijo reservado `local:`: `local:` +
`DEFAULT_REVIEWER` si esa variable está configurada, o `local:sin-identidad`
si no lo está.

**R5b.** MIENTRAS el proceso **sí** esté desplegado y no llegue ninguna de las
dos cabeceras de Easy Auth, el sistema debe sellar el actor
**`sin-identidad`** —sin el prefijo `local:`— y registrar un **WARNING** en el
log por cada petición afectada. La operación solicitada debe completarse
igualmente.

> **Por qué son dos casos y no uno** (enmienda del humano, 2026-08-20). Un
> portal desplegado sin cabecera de Easy Auth no es «una sesión sin
> identificar»: es **la autenticación caída**. Escribir ahí `local:…` no sería
> honesto, sería **afirmar algo falso** —que la fila vino de un puesto de
> desarrollo— y un dato de auditoría que miente sobre su origen es peor que
> uno vacío. Además, un incidente de autenticación tiene que **verse en los
> logs**, no colarse en una columna en silencio. Lo que NO cambia es el
> principio heredado de F-016: no saber quién fue **no** es motivo para perder
> el cambio.

**R5c.** El sistema debe decidir si está desplegado **sin ninguna variable de
configuración nueva y sin tocar Azure**, mirando el entorno del proceso: se
considera desplegado si está presente cualquiera de las variables que Azure
Container Apps inyecta en todos sus contenedores (`CONTAINER_APP_NAME`,
`CONTAINER_APP_REVISION`, `CONTAINER_APP_REPLICA_NAME`,
`CONTAINER_APP_HOSTNAME`) **o** si el proceso ya ha atendido alguna petición
con cabecera de Easy Auth desde su arranque.

> **La segunda señal es la red de seguridad de la primera.** Ver
> `design.md` §4.1: el fallo de detección solo es peligroso en un sentido
> (creerse local estando desplegado), y esa disyunción lo corrige en cuanto
> entra el primer usuario autenticado.

**R6.** SI el valor recibido por cualquiera de las dos cabeceras invade el
**espacio de nombres reservado** —empieza por `local:` o es exactamente
`sin-identidad`, comparado ya normalizado (R4)—, ENTONCES el sistema debe
descartarlo, registrar un WARNING y resolver como si la cabecera no existiera
(R5 o R5b según el entorno). Ningún valor de origen externo puede fabricar un
actor reservado.

> R6 es lo que hace la garantía **estructural**, no una apuesta sobre la forma
> del texto: los valores reservados solo puede producirlos el propio
> resolutor. Por eso no hace falta razonar si `sin-identidad` «parece» un UPN
> (no lo es: no lleva `@`) ni confiar en que un display name nunca coincida
> con esa cadena.

**R7.** El sistema debe resolver **siempre** un actor no vacío para toda
petición HTTP del portal. A partir de esta feature, un `NULL` en una columna
de autor significa **exclusivamente** «fila anterior al corte de F-017».

**R8.** SI el valor recibido por cabecera supera los 120 caracteres, ENTONCES
el sistema debe truncarlo (R4) y completar la operación con normalidad: una
identidad larga no puede hacer fallar una escritura.

**R9.** El sistema debe registrar en el log, **una sola vez por arranque**, si
se considera desplegado (y por qué señal) y si la primera petición atendida
trajo o no cabecera de Easy Auth, sin volcar el token ni los claims. El
WARNING de R5b es aparte y **no** está sujeto a esa limitación: se emite en
cada petición sin identidad estando desplegado, porque cada una es un
incidente.

### 1.2 Un único punto de identidad

**R10.** El sistema debe resolver la identidad en **una única función**
(`_actor(request)`); ninguna ruta, plantilla ni repositorio del portal debe
leer `settings.default_reviewer` ni cabecera alguna de Easy Auth por su
cuenta.

**R11.** MIENTRAS exista `services/partes-front/interface_adapters/web/
app.py`, el número de lecturas de `settings.default_reviewer` en ese fichero
debe ser exactamente **una**, y estar dentro del resolutor de identidad
(`_actor` o la función a la que delega, que vive pegada a él). Ninguna ruta
puede leerla.

### 1.3 Los once puntos que hoy firman sin autor

**R12.** CUANDO el usuario aprueba un parte (`POST /documents/{id}/approve`),
el sistema debe sellar `parte_documents.approved_by` con el actor de esa
petición.

**R13.** CUANDO el usuario borra un parte (`POST /documents/{id}/delete`), el
sistema debe sellar `parte_documents.deleted_by` con el actor de esa petición.

**R14.** CUANDO el usuario borra una línea, una obra o un trabajador
(`POST /api/registro/{id}/delete`, `POST /api/obra/{key}/delete`,
`POST /api/trabajador/{key}/delete`), el sistema debe sellar el actor de esa
petición en la columna de autor que esas operaciones escriben:
`parte_registros.deleted_by` y `parte_documents.deleted_by`.

> **ENMENDADO el 2026-08-20, decisión del humano.** La redacción original decía
> «en `undo_log.actor`», y eso **no describía el código**: esas tres
> operaciones NO generan filas de `undo_log`, y esa columna no la escribe
> nadie. Lo verificamos en el árbol antes de enmendar. El requisito de fondo
> —que un borrado quede firmado— se cumple igual, y mejor, en la columna que
> esas operaciones ya usan.

**R15.** CUANDO el usuario da de alta un parte manual
(`POST /api/partes/nuevo`), el sistema debe hacer llegar el actor de esa
petición a la capa de aplicación por el parámetro `by` de
`crear_parte_manual`, que hasta ahora se recibía y se descartaba.

> **ENMENDADO el 2026-08-20, decisión del humano.** La redacción original decía
> «en `undo_log.actor`». Verificado en el árbol: el alta manual **no** genera
> fila de `undo_log`, y `crear_parte_manual` declara `by` **sin usarlo**
> (`services/partes-front/infrastructure/database/parte_repository.py:2562`).
> Persistir quién dio de alta un parte manual exigiría una **columna nueva**:
> ni `parte_documents` ni `parte_registros` tienen `created_by`. Esta feature
> prometió **cero cambios de schema**, así que no se añade aquí.
>
> **Lo que queda cubierto**: el cableado, hasta la frontera de la persistencia.
> **Lo que NO**: el dato guardado. Eso lo aporta **F-018**, cuyo diseño existe
> justamente para registrar la *decisión* de acciones que hoy no tienen
> columna. Añadir la columna en F-017 habría tocado las **dos copias** del ORM
> por un caso que otra feature resuelve mejor.
>
> **Consecuencia asumida y documentada**: el criterio del corte
> (`autor IS NULL` ⇔ anterior a F-017) vale para las columnas que sí se
> escriben; `undo_log.actor` sigue vacío y no significa nada nuevo.

**R16.** CUANDO el usuario aprueba de forma síncrona
(`POST /api/aprobar/ejecutar`) o encolada (`POST /api/aprobar/encolar`), el
sistema debe llevar el actor de esa petición al campo `usuario` del payload
que viaja a sv5 y a las marcas de estado de las líneas
(`parte_registros.sigrid_registrado_by`, tanto en la traza del resultado como
en el marcado a `encolado`).

**R17.** CUANDO el usuario fuerza un registro con el calendario de Sesame no
disponible, el aviso `[sesame] registro FORZADO por …` del log debe nombrar
al actor de esa petición.

**R18.** MIENTRAS el resultado de una aprobación encolada llegue por
`q-transfer-result` —fuera de toda petición HTTP—, el sistema debe seguir
tomando el `usuario` del sobre del mensaje, que ya viaja firmado con el actor
real gracias a R16.

**R19.** CUANDO el usuario crea, edita, cierra, desactiva o reactiva una
excepción de jornada (las cinco escrituras de F-016), el sistema debe sellar
`empleado_jornada.created_by` / `updated_by` con el actor real de Easy Auth,
sin cambiar ni una línea del bloque de endpoints de F-016.

### 1.4 Robustez y diagnóstico

**R20.** SI las cabeceras de Easy Auth llegan vacías, repetidas o mal
formadas, ENTONCES ninguna ruta del portal debe cambiar su código de estado
respecto al comportamiento anterior a esta feature.

**R21.** CUANDO se consulta `GET /whoami`, el sistema debe responder con el
actor resuelto, **por qué rama salió** (`cabecera-name`, `cabecera-token`,
`local` o `sin-identidad-desplegado`), si el proceso se considera desplegado y
**por qué señal**, y la lista de **nombres** de las cabeceras de Easy Auth
presentes en la petición — nunca sus valores, nunca el token, nunca los
claims.

### 1.5 El corte

**R22.** El sistema debe dejar **intactas** las filas de auditoría anteriores
al despliegue de esta feature: ninguna migración, ningún `UPDATE`, ningún
valor inventado.

**R23.** El corte debe quedar documentado en
`docs/referencia/partes-proyecto.md` con la fecha de despliegue, indicando que
`NULL` en una columna de autor significa «anterior a F-017» y que a partir de
ahí el valor es el principal de Easy Auth o el marcador `local:…`.

---

## 2. Lo que esta feature NO hace (fuera de alcance, explícito)

1. **Roles, permisos y restricciones de acceso** ⇒ **F-008**. Ni un `403`
   nuevo, ni una comprobación de grupo, ni un claim de rol.
2. **Tabla o pantalla de log de auditoría de acciones** ⇒ **F-018**. Esta
   feature no crea tablas ni columnas.
3. **Guardar el `oid` inmutable del usuario.** Hoy no existe columna para él
   y no se va a inventar una (ver punto 2). Consecuencia asumida y
   documentada: si una persona cambia de UPN, las filas antiguas conservan el
   UPN que tenía en ese momento — que es lo que una auditoría debe decir.
   Si el humano quiere identidad inmutable, es una columna de F-018.
4. **Reescribir filas históricas** (R22).
5. **Cambiar el aspecto de ninguna pantalla.** `parte_detail.html` ya pinta
   «Aprobado por {{ parte.approved_by }}» y `admin_jornadas.html` ya pinta
   `created_by`/`updated_by`: empezarán a mostrar un nombre real sin tocar ni
   una plantilla. Esa es la prueba de que el diseño anterior era correcto.
6. **Tocar sv1, sv2, sv3 o sv5.** Ver `design.md` §1.
7. **Configurar nada en Azure.** Easy Auth ya está en pie en `ca-sv4-front`
   (verificado el 2026-08-20: `HTTP 401` sin cookie). Esta feature no cambia
   la configuración de autenticación.

---

## 3. Trazabilidad requisito → test

Todos los tests son de sv4 salvo el de R23. Ninguno toca red ni BBDD: SQLite
en memoria con el ORM real, `Settings(_env_file=None)` y dobles, igual que la
suite de F-016.

| R | Test (`services/partes-front/tests/…` salvo indicación) |
|---|---|
| R1 | `test_f017_identidad.py::test_f017_r1_manda_la_cabecera_name` |
| R2 | `test_f017_identidad.py::test_f017_r2_sin_name_se_lee_el_token` (parametrizado por los cinco claims) |
| R3 | `test_f017_identidad.py::test_f017_r3_token_corrupto_no_rompe` (parametrizado: no-base64, no-JSON, JSON sin `claims`, claims vacíos) |
| R4 | `test_f017_identidad.py::test_f017_r4_normalizacion` (espacios, mayúsculas, `\r\n`, 120) |
| R5 | `test_f017_identidad.py::test_f017_r5_fallback_local_sin_desplegar` (con y sin `DEFAULT_REVIEWER`) |
| R5b | `test_f017_identidad.py::test_f017_r5b_desplegado_sin_cabecera_es_sin_identidad_con_warning` (valor exacto, ausencia del prefijo `local:`, WARNING en `caplog` y **la escritura se completa**) |
| R5c | `test_f017_entorno.py::test_f017_r5c_deteccion_de_despliegue` (parametrizado por las cuatro variables `CONTAINER_APP_*`, entorno vacío, y la segunda señal: tras una petición con cabecera, una posterior sin ella ya no cae en `local:`) |
| R6 | `test_f017_identidad.py::test_f017_r6_espacio_reservado_por_cabecera_se_descarta` (parametrizado: `local:x`, `LOCAL:X`, `sin-identidad`, ` Sin-Identidad `; y en los dos entornos) |
| R7 | `test_f017_identidad.py::test_f017_r7_siempre_hay_actor` (barrido de las 4 combinaciones de cabeceras × los 2 entornos) |
| R8 | `test_f017_identidad.py::test_f017_r8_upn_larguisimo_se_trunca_y_no_falla` |
| R9 | `test_f017_identidad.py::test_f017_r9_aviso_una_sola_vez` (`caplog`: la nota de arranque una vez; el WARNING de R5b, en cada petición) |
| R10 | `test_f017_punto_unico.py::test_f017_r10_ninguna_ruta_lee_la_identidad_por_su_cuenta` (grep sobre `app.py`) |
| R11 | `test_f017_punto_unico.py::test_f017_r11_una_sola_lectura_de_default_reviewer` |
| R12 | `test_f017_endpoints_firmados.py::test_f017_r12_approved_by` |
| R13 | `test_f017_endpoints_firmados.py::test_f017_r13_deleted_by` |
| R14 | `test_f017_endpoints_firmados.py::test_f017_r14_borrar_linea_sella_deleted_by`, `::test_f017_r14_undo_log_actor_borrados` (parametrizado: registro / obra / trabajador), `::test_f017_r14_sin_cabecera_tambien_se_firma`, `::test_f017_r14_cada_peticion_lleva_su_actor` |
| R15 | `test_f017_endpoints_firmados.py::test_f017_r15_undo_log_actor_parte_manual` (el nombre conserva el literal histórico; comprueba el paso del actor por `by=`), `::test_f017_r15_sin_cabecera_el_alta_manual_tambien_se_firma`, `::test_f017_r15_desplegado_sin_cabecera_el_alta_lleva_sin_identidad` |
| R16 | `test_f017_aprobacion_firmada.py::test_f017_r16_payload_y_marcas` (síncrono y encolado) |
| R17 | `test_f017_aprobacion_firmada.py::test_f017_r17_log_forzado_nombra_al_actor` |
| R18 | `test_f017_aprobacion_firmada.py::test_f017_r18_el_sobre_manda_en_el_consumidor` |
| R19 | `test_f016_endpoints_admin_jornadas.py::test_f016_r13_auditoria` **reescrito** (ver `design.md` §6) |
| R20 | `test_f017_identidad.py::test_f017_r20_cabeceras_basura_no_cambian_el_estado` (parametrizado sobre varias rutas) |
| R21 | `test_f017_identidad.py::test_f017_r21_whoami` (las cuatro ramas de `origen`, el `entorno` y que **no** aparece ningún valor de cabecera ni claim en la respuesta) |
| R22 | `tests/test_f017_r22_sin_reescritura_historica.py` (raíz): (a) el ORM sigue declarando exactamente las mismas columnas de autor, con los mismos anchos, en las **dos** copias; (b) barrido del árbol: no existe ningún `UPDATE` sobre `approved_by`/`deleted_by`/`created_by`/`updated_by`/`actor` ni ningún fichero `.sql` de migración nuevo |
| R23 | `tests/test_f017_r23_corte_documentado.py` (raíz del monorepo) |

**Fase RED obligatoria** (rigor `estandar`) con traza real pegada en
`progress/impl_F-017.md` para los requisitos centrales: **R1, R5, R5b, R10,
R12 y R16**. R5b entra en la lista por la enmienda del humano: es el requisito
que impide que un fallo de autenticación en producción se disfrace de sesión
local, y esa clase de defecto no se detecta leyendo el código.

---

## 4. Verificaciones MANUAL (humano)

En local **no existe** ninguna cabecera de Easy Auth: que las cabeceras
lleguen de verdad en Azure no lo puede demostrar ningún test.

- **M1.** Con sv4 desplegado, abrir en el navegador
  `https://<fqdn de ca-sv4-front>/whoami` con la sesión de Entra iniciada, y
  comprobar **tres cosas**: `actor` es el correo/UPN de quien mira, `origen`
  es `cabecera-name` y `entorno` es `desplegado`. Lecturas posibles:
  - `origen = cabecera-token`: la cabecera `-NAME` no llega y el suplente de
    R2 está haciendo su trabajo. Correcto, pero **anótalo**.
  - `origen = sin-identidad-desplegado`: Easy Auth no está inyectando nada.
    **Incidente**: la feature funciona (no miente), pero la autenticación del
    portal está rota. Parar y avisar.
  - `origen = local` o `entorno = local`: **la detección de R5c ha fallado en
    Azure** y el portal está firmando filas de producción como si fueran
    locales. **Parar y avisar de inmediato**: es el único fallo de esta
    feature que ensucia datos. El campo `senal_despliegue` de la respuesta
    dice qué se buscó y qué se encontró.
- **M1 bis (se puede hacer ANTES de implementar, y conviene).** Comprobar que
  Azure Container Apps inyecta de verdad las variables de R5c en este
  entorno — hoy **ningún servicio del monorepo las lee**, así que es un
  supuesto de plataforma sin verificar aquí:
  `az containerapp exec -n ca-sv4-front -g rg-partes-dev --command "printenv" | Select-String CONTAINER_APP`
  Si no aparece ninguna, R5c se queda **solo** con la segunda señal y hay que
  decidir otra (ver `design.md` §4.1).
- **M2.** Aprobar un parte de prueba desde el portal desplegado y comprobar
  en la base `partes` que `parte_documents.approved_by` lleva ese mismo valor
  y no `NULL`:
  `SELECT id, approved_by, approved_at_utc FROM parte_documents WHERE approved_at_utc IS NOT NULL ORDER BY approved_at_utc DESC LIMIT 5;`
- **M3.** Borrar una línea de prueba y comprobar
  `SELECT created_at_utc, action, actor FROM undo_log ORDER BY id DESC LIMIT 5;`
- **M4.** Comprobar que las filas anteriores al despliegue **siguen** con
  `NULL` (R22):
  `SELECT count(*) FROM parte_documents WHERE approved_at_utc IS NOT NULL AND approved_by IS NULL;`
  El número debe ser el mismo antes y después del despliegue.

M2, M3 y M4 necesitan la regla de firewall de `psql-albaranes-rs9k2` que ya
está pendiente en `progress/current.md`.
