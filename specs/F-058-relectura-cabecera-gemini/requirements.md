<!-- specs/F-058-relectura-cabecera-gemini/requirements.md -->
# F-058 · Relectura de la cabecera vacía con Gemini (sv2) — Requisitos

**Servicio tocado: solo sv2** (`services/partes-api`: un módulo puro nuevo, el pipeline, el
servicio de extracción, `Settings` y el cableado de `app.py`). sv1, sv3, sv4, sv5, el ORM y
el esquema de la base no cambian (`design.md` §1). Rigor **estándar**: no escribe en Sigrid
ni toca nada compartido; el único efecto externo nuevo es una llamada más a Gemini.

**Petición del humano del 2026-10-23**, literal: «si, lanza f54 y la spec de relectura con
gemini». La propuesta que aprobó: si la IA devuelve la cabecera vacía pero con trabajadores,
sv2 relee esa página con el segundo modelo (`gemini-4-argon`) y se queda con esa cabecera;
`gpt-6.1-sol` (`IA_PROVIDER=openai`) sigue leyendo las filas.

## Contexto (hallazgo del líder del 2026-10-23; detalle en `design.md` §2)

Seis páginas de dos escaneos (21/10 y 23/10) se guardaron con la cabecera entera a `null`
(fecha, obra, nombre de obra, membrete, encargado, jefe de obra), con 2 a 5 filas de
trabajadores y la firma leídas, `obra_match_method = 'none'` y `review_required = false`.
El papel es legible; el escaneo sale desplazado. En la batería local, `gpt-6.1-sol` dio la
cabecera vacía 12 de 12 veces; `gemini-4-argon`, obra y fecha correctas 6 de 6 y las mismas
filas que `gpt-6.1-sol` en las 6; las páginas de control de esas obras salen bien con
`gpt-6.1-sol`. F-054 (sv3, `spec_ready`) manda a revisión el parte sin obra o sin fecha:
F-058 intenta que no llegue así; F-054 es la red cuando la relectura no basta.

## Glosario

- **Lectura primaria**: la del proveedor `IA_PROVIDER` (hoy `openai`, `gpt-6.1-sol`).
- **Proveedor de relectura**: `RELECTURA_CABECERA_PROVIDER` (por defecto `gemini`), con el
  modelo ya configurado para ese proveedor (en Azure, `GEMINI_MODEL=gemini-4-argon`).
- **Vacío**: `None` o una cadena que solo tiene espacios.
- **Cabecera vacía** (DA1 = B): `data.cabecera.obra_numero` y `data.cabecera.fecha` vacíos
  los dos (falte o no la propia clave `cabecera`).
- **Con trabajadores**: `data.empleados` es una lista con al menos un elemento.
- **Relectura útil**: la cabecera de la relectura NO es vacía (trae obra o fecha).
- **Relectura activa**: interruptor encendido, proveedor de relectura distinto de
  `IA_PROVIDER`, con su `ENABLE_*` a `true` y su clave presente (DA5).

## Requisitos

### Cuándo se relee (sv2)

- **R1.** CUANDO la lectura primaria devuelve una cabecera vacía con trabajadores y la
  relectura está activa, sv2 debe releer **el mismo adjunto, una sola vez**, con el proveedor
  de relectura y con el mismo `prompt_key`, el mismo esquema y el mismo contexto dinámico
  (catálogo auxhor) que la primaria (DA2 = A).
- **R2.** SI la cabecera primaria trae obra o fecha (cualquiera de las dos no vacía),
  ENTONCES sv2 no debe releer: una sola llamada al modelo, como hoy.
- **R3.** SI `data.empleados` está vacío, ENTONCES sv2 no debe releer aunque la cabecera
  esté vacía (página en blanco o sin tabla).
- **R4.** Un valor con solo espacios (`"  "`) debe contar como vacío, tanto en la cabecera
  primaria (dispara) como en la de la relectura (no es útil).
- **R5.** MIENTRAS `RELECTURA_CABECERA=false`, o el proveedor de relectura sea el mismo que
  `IA_PROVIDER`, o no esté habilitado o sin clave, sv2 no debe releer nunca.

### Qué se toma (sv2)

- **R6.** CUANDO la relectura es útil, `data.cabecera` del envelope debe ser la cabecera
  **entera** de la relectura (sus seis campos, también los nulos) y `data.firma` y
  `data.empleados` deben ser exactamente los de la lectura primaria (DA3 = A).
- **R7.** SI la relectura no es útil (también sale vacía), ENTONCES `data` debe ser
  exactamente el de la lectura primaria (DA4 = A).
- **R8.** SI la relectura lanza cualquier excepción (tras los reintentos del cliente),
  ENTONCES el pipeline no debe propagarla: `data` debe ser el de la primaria y el envelope
  debe salir igual hacia sv3 (DA4 = A). Un fallo de la lectura primaria sigue como hoy.
- **R9.** El `data` resultante debe validar contra `ParteTrabajo` (sv3 lo recibe con la
  misma forma de siempre).

### Trazabilidad (sv2, envelope y log)

- **R10.** CUANDO sv2 relee, `meta.relectura_cabecera` debe ser
  `{"motivo": "cabecera_vacia", "provider", "model", "resultado", "error_tipo"}`, con
  `resultado` ∈ `aplicada` | `vacia` | `error` y `error_tipo` el nombre de la clase de la
  excepción (solo con `error`; si no, `null`) (DA6 = A).
- **R11.** `meta.provider` y `meta.model` deben seguir siendo los de la lectura primaria
  también cuando se aplica la relectura (sv3 los guarda en `provider` y `model_name`).
- **R12.** CUANDO sv2 relee, `debug.relectura_cabecera` debe guardar `cabecera_primaria`
  (la cabecera que devolvió la primaria) y, si la llamada respondió, el `debug_payload` de
  la relectura (petición y respuesta).
- **R13.** SI sv2 no relee, `meta` y `debug` deben tener exactamente las mismas claves que
  hoy (no aparece `relectura_cabecera`).
- **R14.** CUANDO sv2 relee, debe registrar un INFO al disparar y otro con el resultado
  (WARNING si `vacia` o `error`), con `source_filename`, proveedor, modelo y resultado, y
  **sin** nombres, DNIs, valores de la cabecera ni el mensaje de la excepción (solo su tipo:
  un error de validación de Pydantic copia en su mensaje lo que leyó el modelo).

### Configuración y cableado (sv2)

- **R15.** `Settings` debe leer `RELECTURA_CABECERA` (bool, por defecto `true`) y
  `RELECTURA_CABECERA_PROVIDER` (`gemini` | `claude` | `openai`, por defecto `gemini`) y
  exponer el proveedor de relectura activo (`None` si no lo hay) y, si está encendida pero no
  activa, el motivo (`mismo_proveedor`, `no_habilitado`, `sin_clave`) (DA5 = A).
- **R16.** La relectura no debe impedir arrancar: un proveedor de relectura no habilitado o
  sin clave deja la relectura inactiva; el validador actual del primario no cambia.
- **R17.** `build_app` debe pasar al pipeline el proveedor de relectura activo y dejar un
  INFO de cableado con proveedor y modelo de relectura, o un WARNING con el motivo si está
  encendida pero inactiva; sin secretos.
- **R18.** `GET /health` debe incluir `relectura_cabecera`: `{"provider", "model"}` del
  proveedor activo, o `null`.

### Límite y documentación

- **R19.** sv1, sv3, sv4, sv5, `orm_models.py` y `prompts.yaml` no deben cambiar
  (comprobable con `git diff dev --stat`).
- **R20.** `docs/ARCHITECTURE.md` (punto 18 de la semántica y la línea de Gemini),
  `azure-apps/partes.md` (lo que consume sv2) y el comentario de sv2 en
  `infra/create_capps_partes.ps1` deben contar la relectura.

## Verificación manual (humano o líder; `design.md` §9)

- **M0** (solo lectura, antes de desplegar): la revisión de `ca-sv2-extraccion` en Azure
  tiene `ENABLE_GEMINI=true`, `GEMINI_MODEL=gemini-4-argon` y `GEMINI_API_KEY` por
  `secretRef`; si no, se para y el humano decide (DA5).
- **M1** (local, sin escrituras): el pipeline de la rama sobre las 6 páginas sin cabecera da
  6/6 `aplicada` con obra y fecha y las mismas filas; las 2 de control, sin relectura.
- **M2** (solo lectura, tras desplegar): recuento de `meta.relectura_cabecera.resultado` en
  las ingestas nuevas de la base `partes`.
- **M3**: los 6 documentos ya guardados se tratan según la DA8 (por defecto, a mano en el
  portal; sin escrituras de los agentes).

## Fuera de alcance

- Cambiar el prompt `parte_trabajo_es` o el modelo primario; releer por otras causas (filas
  dudosas, firma); caer a Gemini cuando falla la llamada primaria.
- La revisión del parte sin obra o sin fecha: es F-054 (sv3).
- Reprocesar automáticamente lo ya guardado (DA8).
