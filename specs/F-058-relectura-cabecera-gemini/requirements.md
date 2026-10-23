<!-- specs/F-058-relectura-cabecera-gemini/requirements.md -->
# F-058 · Relectura de la cabecera con Gemini y prompt de cabecera (sv2) — Requisitos

**Servicio tocado: solo sv2** (`services/partes-api`; ficheros en `design.md` §3); sv1, sv3,
sv4, sv5, el ORM y la base no cambian. Rigor **estándar**: no escribe en Sigrid ni toca nada
compartido; lo nuevo es una llamada más a Gemini (al releer) y una lectura cacheada de sigrid-api.

**Peticiones del humano del 2026-10-23**, literales: «si, lanza f54 y la spec de relectura con
gemini»; «da1, vacia o no casa con ninguna obra»; y «para el tema de la cabecera podemos
mejorar el prompt diciendole que hay una cabecera y que debera obtener la obra el dia mes,
etc... añadelo a f58, lo demas ok» (aprueba DA2–DA8 con la recomendación y la comprobación de
existencia en sv2; `design.md` §11).

## Contexto (detalle en `design.md` §2)

Seis páginas de escaneos desplazados (21/10 y 23/10) se guardaron con la cabecera a `null` y
2–5 filas leídas. En la batería local, `gpt-6.1-sol` dio la cabecera vacía 12 de 12 y
`gemini-4-argon` obra y fecha bien 6 de 6 con las mismas filas. De 157 documentos con obra
leída, los 157 casaron: «obra inexistente» es preventivo. F-054 (sv3) es la red.

## Glosario

- **Lectura primaria**: la de `IA_PROVIDER` (hoy `openai`, `gpt-6.1-sol`).
- **Proveedor de relectura**: `RELECTURA_CABECERA_PROVIDER` (por defecto `gemini`), con su
  modelo ya configurado (en Azure, `GEMINI_MODEL=gemini-4-argon`).
- **Vacío**: `None` o una cadena con solo espacios.
- **Con trabajadores**: `data.empleados` es una lista con al menos un elemento.
- **Cabecera vacía**: `cabecera.obra_numero` y `cabecera.fecha` vacíos (falte o no `cabecera`).
- **Clave de obra**: el código sin acentos, en mayúsculas y sin espacios ni guiones; si queda
  solo de dígitos, además sin ceros a la izquierda (`"0672"`, `"672"` y `"00672"` dan `"672"`;
  `"000"` da `"0"`).
- **Lista de obras**: las claves de todos los `con.cod` de `obr` en Sigrid, de cualquier
  empresa y con o sin baja.
- **Obra inexistente**: `obra_numero` no vacío y su clave fuera de la lista de obras
  **cargada**. Sin lista cargada, «no se sabe», que no es inexistente.
- **Motivo** (DA1 enmendada): `cabecera_vacia` u `obra_inexistente`.
- **Relectura útil**: con `cabecera_vacia`, la cabecera releída no es vacía; con
  `obra_inexistente`, la releída trae una `obra_numero` que está en la lista de obras.
- **Relectura activa**: interruptor encendido, proveedor de relectura distinto de
  `IA_PROVIDER`, con su `ENABLE_*` a `true` y su clave presente (DA5).

## Requisitos

### Cuándo se relee

- **R1.** CUANDO la lectura primaria trae trabajadores y un motivo y la relectura está activa,
  sv2 debe releer **el mismo adjunto, una sola vez**, con el proveedor de relectura, el mismo
  `prompt_key`, el mismo esquema y el mismo contexto dinámico (catálogo auxhor) (DA2 = A).
- **R2.** El motivo se decide en este orden: `cabecera_vacia` si la cabecera es vacía (sin
  consultar Sigrid); si no, `obra_inexistente` si la obra es inexistente; si no, no hay.
- **R3.** SI la primaria trae una obra que está en la lista, o trae fecha sin obra, ENTONCES
  sv2 no debe releer: una sola llamada al modelo, como hoy.
- **R4.** SI `data.empleados` está vacío, ENTONCES sv2 no debe releer ni consultar la lista.
- **R5.** Un valor con solo espacios debe contar como vacío en la primaria y en la relectura.
- **R6.** MIENTRAS la relectura no esté activa, sv2 no debe releer ni consultar la lista.

### Lista de obras (sigrid-api)

- **R7.** sv2 debe cargar la lista con **una** consulta `sql/read` a sigrid-api (`design.md`
  §4.3) la primera vez que la necesite (R2) y cachearla en memoria `OBRAS_CACHE_TTL_S`
  segundos (600 por defecto), compartida entre páginas.
- **R8.** SI la respuesta trae `truncated: true`, ENTONCES debe tratarse como fallo: nunca una
  lista parcial.
- **R9.** SI sigrid-api no está cableado, falla, trunca o da cero códigos, ENTONCES sv2
  no debe releer por `obra_inexistente` (sí por `cabecera_vacia`), no debe propagar el error y
  la extracción sigue; usa la lista anterior si la tenía, no reintenta hasta pasado el TTL y
  deja un WARNING con el tipo de error, sin secretos ni códigos (DA10).
- **R10.** sv2 no decide la obra ni la empresa: sv3 las sigue casando como hoy y el envelope
  no lleva la lista ni nada de ella fuera de la traza de R15.

### Qué se toma

- **R11.** CUANDO la relectura es útil, `data.cabecera` debe ser la cabecera **entera** de la
  relectura (sus seis campos, también los nulos) y `data.firma` y `data.empleados` los de la
  primaria (DA3 = A; también con `obra_inexistente`, DA11 = A).
- **R12.** SI la relectura no es útil, ENTONCES `data` debe ser el de la primaria (DA4 = A).
- **R13.** SI la relectura lanza cualquier excepción (tras los reintentos del cliente),
  ENTONCES el pipeline no debe propagarla y `data` debe ser el de la primaria. Un fallo de la
  lectura primaria sigue como hoy.
- **R14.** El `data` resultante debe validar contra `ParteTrabajo`.

### Trazabilidad (envelope y log)

- **R15.** CUANDO sv2 relee, `meta.relectura_cabecera` debe ser `{"motivo", "provider",
  "model", "resultado", "error_tipo"}` con `resultado` ∈ `aplicada` | `vacia` | `no_casa` |
  `error`: `vacia` si la releída no es útil y no trae obra; `no_casa` (solo con
  `obra_inexistente`) si trae una obra que tampoco está en la lista; `error_tipo` es el nombre
  de la clase de la excepción con `error` y `null` en otro caso (DA6 = A).
- **R16.** `meta.provider` y `meta.model` deben seguir siendo los de la lectura primaria.
- **R17.** CUANDO sv2 relee, `debug.relectura_cabecera` debe guardar `cabecera_primaria` y, si
  la llamada respondió, el `debug_payload` de la relectura.
- **R18.** SI sv2 no relee, `meta` y `debug` deben tener exactamente las claves de hoy.
- **R19.** CUANDO sv2 relee, debe registrar un INFO al disparar (con el motivo) y otro con el
  resultado (WARNING si no es `aplicada`), con `source_filename`, proveedor, modelo y
  resultado, y **sin** nombres, DNIs, valores ni códigos de la cabecera ni el mensaje de la
  excepción (solo su tipo).

### Prompt de extracción (`config/prompts.yaml`, `parte_trabajo_es`; DA9)

- **R20.** El punto `1) CABECERA` de `task` debe empezar con un párrafo que diga que toda
  página tiene una cabecera encima de la tabla «PERSONAL»; que de ella salen el número de la
  obra, el día, el mes y el año de la fecha, la empresa del membrete y el resto de campos del
  punto; que se busque aunque el escaneo salga desplazado, girado o recortado; que con
  trabajadores una cabecera entera a `null` es casi siempre no haberla localizado; y que nunca
  se invente un valor (texto exacto en `design.md` §5).
- **R21.** La viñeta `cabecera.fecha` debe decir que, si el día, el mes y el año van en
  casillas separadas, se copian juntos en ese orden y sin convertir.
- **R22.** `system`, los puntos 2 a 6 de `task`, `schema_hint` y `ParteTrabajo` no deben
  cambiar; los tests de F-023 y F-051 siguen en verde sin tocarlos. El prompt nuevo vale para
  la primaria y para la relectura (ambos proveedores).

### Configuración y cableado

- **R23.** `Settings` debe leer `RELECTURA_CABECERA` (bool, `true`), `RELECTURA_CABECERA_PROVIDER`
  (`gemini` | `claude` | `openai`; `gemini`) y `OBRAS_CACHE_TTL_S` (int, 600) y exponer el
  proveedor de relectura activo (`None` si no lo hay) y, si está encendida pero inactiva, el
  motivo (`mismo_proveedor`, `no_habilitado`, `sin_clave`) (DA5 = A).
- **R24.** La relectura no debe impedir arrancar; el validador actual del primario no cambia.
- **R25.** `build_app` debe pasar al pipeline el proveedor activo y, con relectura activa y
  sigrid-api cableado, la lista de obras (mismo cliente que el catálogo auxhor), con un INFO de
  cableado (proveedor, modelo, si comprueba obra) o un WARNING con el motivo; sin secretos.
- **R26.** `GET /health` debe incluir `relectura_cabecera`: `{"provider", "model",
  "comprueba_obra"}` del proveedor activo, o `null`.

### Límite y documentación

- **R27.** sv1, sv3, sv4, sv5, `orm_models.py` y `parte_models.py` no deben cambiar, y de
  `prompts.yaml` solo el punto 1 de `task` (comprobable con `git diff dev`).
- **R28.** `docs/ARCHITECTURE.md` (punto 18, líneas de Gemini y sigrid-api), `azure-apps/partes.md`
  (sv2 consume Gemini para releer y sigrid-api para el catálogo auxhor y la lista de obras) y
  el comentario de sv2 en `infra/create_capps_partes.ps1` deben contarlo.

## Verificación manual (humano o líder; `design.md` §10)

- **M0** (solo lectura, antes de desplegar): `ca-sv2-extraccion` tiene Gemini (`ENABLE_GEMINI`,
  `GEMINI_MODEL`, clave por `secretRef`) y las tres `SIGRID_API_*`; si no, decide el humano.
- **MB** (banco del prompt, lo lanza el líder): con `gpt-6.1-sol` y solo el prompt nuevo,
  cuántas de las 12 lecturas de `paginas_sincab` traen obra y fecha (antes 0 de 12), sin
  regresión en `paginas_control` ni en la batería de F-051; resultado en `progress/`.
- **M1** (local, sin escrituras): el pipeline de la rama da obra y fecha en las 6 páginas sin
  cabecera con las mismas filas, control sin relectura y la lista de obras cargada sin truncar.
- **M2** (solo lectura, tras desplegar): recuento de `meta.relectura_cabecera` por motivo y
  resultado en las ingestas nuevas de la base `partes`.
- **M3**: los 6 documentos ya guardados se tratan según la DA8 (a mano en el portal).

## Fuera de alcance

- Cambiar el modelo primario; releer por otras causas (filas dudosas, firma, fecha sin obra);
  caer a Gemini si falla la primaria; reprocesar lo guardado (DA8); casar la obra en sv2.
