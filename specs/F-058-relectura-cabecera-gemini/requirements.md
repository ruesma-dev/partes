<!-- specs/F-058-relectura-cabecera-gemini/requirements.md -->
# F-058 · Relectura de la cabecera con Gemini y prompt de cabecera (sv2) — Requisitos

**Servicio tocado: solo sv2** (`services/partes-api`; ficheros en `design.md` §3). Rigor
**estándar**: no escribe en Sigrid ni toca nada compartido; lo nuevo es una llamada más a
Gemini (al releer) y una consulta de lectura a sigrid-api por página que la necesite.

**Peticiones del humano del 2026-10-23**, literales: «si, lanza f54 y la spec de relectura con
gemini»; «da1, vacia o no casa con ninguna obra»; «para el tema de la cabecera podemos
mejorar el prompt diciendole que hay una cabecera y que debera obtener la obra el dia mes,
etc... añadelo a f58, lo demas ok» (DA2–DA8 con la recomendación); y «da10, vamos a poner una
consulta en el momento al vuelo, y vemos tiempos. si la obra no existe se manda a relectura a
gemini» (DA10 = B; `design.md` §11).

**Contexto** (`design.md` §2): seis páginas de escaneos desplazados se guardaron con la
cabecera a `null`; `gpt-6.1-sol` la dio vacía 12 de 12 y `gemini-4-argon` bien 6 de 6. De 157
documentos con obra leída, los 157 casaron: «obra inexistente» es preventivo. F-054 es la red.

## Glosario

- **Lectura primaria**: la de `IA_PROVIDER` (hoy `openai`, `gpt-6.1-sol`).
- **Proveedor de relectura**: `RELECTURA_CABECERA_PROVIDER` (por defecto `gemini`), con su
  modelo ya configurado (en Azure, `GEMINI_MODEL=gemini-4-argon`).
- **Vacío**: `None` o una cadena con solo espacios. **Con trabajadores**: `data.empleados` es
  una lista con al menos un elemento.
- **Cabecera vacía**: `cabecera.obra_numero` y `cabecera.fecha` vacíos (falte o no `cabecera`).
- **Clave de obra**: el código sin acentos, en mayúsculas y sin espacios ni guiones; si queda
  solo de dígitos, además sin ceros a la izquierda (`"0672"`, `"672"` y `"00672"` dan `"672"`;
  `"000"` da `"0"`).
- **Consulta de obra**: una `sql/read` a sigrid-api, hecha en el momento, que dice si hay en
  `obr` alguna obra cuyo `con.cod` tenga esa clave, de cualquier empresa y también de baja.
- **Obra inexistente**: `obra_numero` no vacío y la consulta de obra responde que no hay
  ninguna. Si la consulta no responde (R9), «no se sabe», que no es inexistente.
- **Motivo** (DA1 enmendada): `cabecera_vacia` u `obra_inexistente`.
- **Relectura útil**: con `cabecera_vacia`, la cabecera releída no es vacía; con
  `obra_inexistente`, la releída trae una `obra_numero` que la consulta de obra da por existente.
- **Relectura activa**: interruptor encendido, proveedor de relectura distinto de
  `IA_PROVIDER`, con su `ENABLE_*` a `true` y su clave presente (DA5).

## Requisitos

### Cuándo se relee

- **R1.** CUANDO la lectura primaria trae trabajadores y un motivo y la relectura está activa,
  sv2 debe releer **el mismo adjunto, una sola vez**, con el proveedor de relectura, el mismo
  `prompt_key`, el mismo esquema y el mismo contexto dinámico (catálogo auxhor) (DA2 = A).
- **R2.** El motivo se decide en este orden: `cabecera_vacia` si la cabecera es vacía (sin
  consultar Sigrid); si no, `obra_inexistente` si la obra es inexistente; si no, no hay.
- **R3.** SI la primaria trae una obra que existe, o trae fecha sin obra, ENTONCES sv2 no debe
  releer: una sola llamada al modelo, como hoy.
- **R4.** SI `data.empleados` está vacío, ENTONCES sv2 no debe releer ni consultar Sigrid.
- **R5.** Un valor con solo espacios debe contar como vacío en la primaria y en la relectura.
- **R6.** MIENTRAS la relectura no esté activa, sv2 no debe releer ni consultar Sigrid.

### Consulta de obra (sigrid-api, DA10 = B)

- **R7.** CUANDO la primaria trae trabajadores y una obra no vacía y la relectura está activa,
  sv2 debe hacer **en ese momento** una consulta de obra (`design.md` §4.3) con la clave como
  parámetro `?`, nunca concatenada en el SQL, y sin caché entre páginas.
- **R8.** CUANDO la releída por `obra_inexistente` trae obra, sv2 debe hacer una segunda consulta
  de obra, salvo que su clave sea la de la primaria (entonces `no_casa` sin consultar): como
  mucho dos consultas por página, y ninguna con `cabecera_vacia`.
- **R9.** SI sigrid-api no está cableado, falla, responde con `truncated: true` o tarda más de
  `OBRA_EXISTE_TIMEOUT_S` (5 s; propuesta pendiente, DA12), ENTONCES la consulta da «no se
  sabe»: sv2 no debe releer por `obra_inexistente` (sí por `cabecera_vacia`) ni propagar el
  error, la extracción sigue, no reintenta en esa página y deja un WARNING con el tipo de error,
  sin secretos ni códigos. Con la segunda consulta, «no se sabe» da `no_casa`.
- **R10.** Cada consulta de obra debe medir su duración (reloj monotónico) y dejar un INFO
  `[obra-sigrid]` con `document_id`, milisegundos y resultado (`existe`, `no_existe` o `error`
  con su tipo), sin el código de obra, nombres ni DNIs (para ver los tiempos, M4).
- **R11.** sv2 no decide la obra ni la empresa (las sigue casando sv3) ni lleva al envelope
  nada de Sigrid fuera de la traza de R16.

### Qué se toma

- **R12.** CUANDO la relectura es útil, `data.cabecera` debe ser la cabecera **entera** de la
  relectura (sus seis campos, también los nulos) y `data.firma` y `data.empleados` los de la
  primaria (DA3 = A; también con `obra_inexistente`, DA11 = A).
- **R13.** SI la relectura no es útil, ENTONCES `data` debe ser el de la primaria (DA4 = A).
- **R14.** SI la relectura lanza cualquier excepción (tras los reintentos del cliente),
  ENTONCES el pipeline no debe propagarla y `data` debe ser el de la primaria. Un fallo de la
  lectura primaria sigue como hoy. El `data` resultante debe validar contra `ParteTrabajo`.

### Trazabilidad (envelope y log)

- **R15.** `ExtractParteRequest` debe aceptar `document_id` opcional (`None` por defecto, el
  endpoint HTTP no cambia) y el worker debe pasarle el del mensaje de `q-extraccion`.
- **R16.** CUANDO sv2 relee, `meta.relectura_cabecera` debe ser `{"motivo", "provider",
  "model", "resultado", "error_tipo", "consulta_obra_ms"}` con `resultado` ∈ `aplicada` |
  `vacia` | `no_casa` | `error` (`vacia`: no útil y sin obra; `no_casa`, solo con
  `obra_inexistente`: trae una obra que no existe o no se sabe), `error_tipo` el tipo de la
  excepción o `null` y `consulta_obra_ms` la lista de ms de las consultas de la página (DA6 = A).
- **R17.** `meta.provider` y `meta.model` deben seguir siendo los de la lectura primaria.
- **R18.** CUANDO sv2 relee, `debug.relectura_cabecera` debe guardar `cabecera_primaria` y, si
  la llamada respondió, el `debug_payload` de la relectura.
- **R19.** SI sv2 no relee, `meta` y `debug` deben tener exactamente las claves de hoy.
- **R20.** CUANDO sv2 relee, debe registrar un INFO al disparar (con el motivo) y otro con el
  resultado (WARNING si no es `aplicada`), con `document_id`, `source_filename`, proveedor,
  modelo y resultado, y **sin** nombres, DNIs, valores ni códigos de la cabecera ni el mensaje
  de la excepción (solo su tipo).

### Prompt de extracción (`config/prompts.yaml`, `parte_trabajo_es`; DA9)

- **R21.** El punto `1) CABECERA` de `task` debe empezar con un párrafo que diga que toda
  página tiene una cabecera encima de la tabla «PERSONAL»; que de ella salen el número de la
  obra, el día, el mes y el año de la fecha, la empresa del membrete y el resto de campos del
  punto; que se busque aunque el escaneo salga desplazado, girado o recortado; que con
  trabajadores una cabecera entera a `null` es casi siempre no haberla localizado; y que nunca
  se invente un valor (texto exacto en `design.md` §5).
- **R22.** La viñeta `cabecera.fecha` debe decir que, si el día, el mes y el año van en
  casillas separadas, se copian juntos en ese orden y sin convertir.
- **R23.** `system`, los puntos 2 a 6 de `task`, `schema_hint` y `ParteTrabajo` no deben
  cambiar; los tests de F-023 y F-051 siguen en verde sin tocarlos. El prompt nuevo vale para
  la primaria y para la relectura (ambos proveedores).

### Configuración y cableado

- **R24.** `Settings` debe leer `RELECTURA_CABECERA` (bool, `true`), `RELECTURA_CABECERA_PROVIDER`
  (`gemini` | `claude` | `openai`; `gemini`) y `OBRA_EXISTE_TIMEOUT_S` (float > 0, 5) y exponer
  el proveedor de relectura activo (`None` si no lo hay) y, si está encendida pero inactiva, el
  motivo (`mismo_proveedor`, `no_habilitado`, `sin_clave`) (DA5 = A). La relectura no debe
  impedir arrancar; el validador actual del primario no cambia.
- **R25.** `build_app` debe pasar al pipeline el proveedor activo y, con relectura activa y
  sigrid-api cableado, la consulta de obra (mismo cliente que el catálogo auxhor), con un INFO
  de cableado (proveedor, modelo, si comprueba obra y el tiempo máximo) o un WARNING con el
  motivo; sin secretos.
- **R26.** `GET /health` debe incluir `relectura_cabecera`: `{"provider", "model",
  "comprueba_obra"}` del proveedor activo, o `null`.

### Límite y documentación

- **R27.** sv1, sv3, sv4, sv5, `orm_models.py` y `parte_models.py` no deben cambiar, y de
  `prompts.yaml` solo el punto 1 de `task` (comprobable con `git diff dev`).
- **R28.** `docs/ARCHITECTURE.md` (punto 18, líneas de Gemini y sigrid-api), `azure-apps/partes.md`
  (sv2 consume Gemini para releer y sigrid-api para el catálogo auxhor y la consulta de obra) y
  el comentario de sv2 en `infra/create_capps_partes.ps1` deben contarlo.

## Verificación manual (humano o líder; comandos en `design.md` §10)

- **M0** (solo lectura, antes de desplegar): `ca-sv2-extraccion` tiene Gemini y `SIGRID_API_*`.
- **MB** (banco del prompt, lo lanza el líder): `paginas_sincab` con `gpt-6.1-sol` y el prompt
  nuevo (antes 0 de 12 con obra y fecha), sin regresión en control ni en la batería de F-051.
- **M1** (local, sin escrituras): obra y fecha en las 6 páginas sin cabecera con las mismas
  filas, control sin relectura y los milisegundos de cada consulta de obra en el log.
- **M2** y **M4** (solo lectura, tras desplegar): recuento de `meta.relectura_cabecera` por
  motivo y resultado en la base `partes`; tiempos de la consulta de obra en Log Analytics.
- **M3**: los 6 documentos ya guardados se tratan según la DA8 (a mano en el portal).

**Fuera de alcance**: cambiar el modelo primario; releer por otras causas (filas dudosas,
firma, fecha sin obra); caer a Gemini si falla la primaria; reprocesar (DA8); casar en sv2.
