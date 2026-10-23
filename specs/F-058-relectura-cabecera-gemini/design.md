<!-- specs/F-058-relectura-cabecera-gemini/design.md -->
# F-058 · Relectura de la cabecera vacía con Gemini — diseño técnico

## 1. Encaje y límite de servicio

- **Solo sv2 (`services/partes-api/`)**: es quien lee el papel y el único que llama a la IA.
  La relectura es una segunda lectura del mismo adjunto, dentro del mismo mensaje de
  `q-extraccion`, antes de escribir el envelope y publicar `q-persistencia`.
- **sv3 no cambia**: recibe el envelope con la misma forma (`data` conforme a `ParteTrabajo`)
  y guarda `raw_extraction_json` entero, así que la traza nueva de `meta`/`debug` queda en la
  base sin columna ni migración. `meta.provider`/`meta.model` siguen siendo los del primario
  (sv3 los copia a `provider`/`model_name`). La red cuando la relectura no basta es F-054.
- Descartado en sv3 (no llama a la IA: repartiría la lectura entre dos servicios) y en un
  servicio nuevo. Nada de la lista cerrada de duplicación de `CLAUDE.md` se toca.

## 2. Lo que hay hoy (`dev` 38f273a)

- `ExtractPartePipeline.run` (`application/pipelines/extract_parte_pipeline.py`) valida el
  adjunto, compone el catálogo auxhor (`dynamic_context`), llama **una vez** a
  `ParteExtractionService.extract(provider=IA_PROVIDER, ...)` y arma
  `{meta, data: parsed.model_dump(), debug: debug_payload}`.
- `ParteExtractionService` ya tiene un diccionario de proveedores instanciados por nombre y
  `extract(..., provider=...)` elige cualquiera: releer con otro proveedor no exige tocar
  clientes. Su `debug_payload` lleva `<provider>_request` / `<provider>_response` (hash del
  adjunto y claves parseadas; sin contenido).
- `build_app` instancia los proveedores con `ENABLE_*` a `true`. En Azure
  (`infra/create_capps_partes.ps1`, l. 31–45, y `azure-apps/partes.md`): `IA_PROVIDER=openai`,
  `OPENAI_MODEL=gpt-6.1-sol`, **`ENABLE_GEMINI=true`, `GEMINI_MODEL=gemini-4-argon` y
  `GEMINI_API_KEY=secretref:gemini-key`** (KV `GEMINI-API-KEY`). Gemini ya está instanciado y
  con clave: con los valores por defecto de §5 **no hace falta tocar el entorno** (M0 lo
  confirma en solo lectura).
- `Settings._ensure_provider_enabled_and_keyed` solo valida el primario. El cliente OpenAI usa
  `responses.parse`: la cabecera a `null` la elige el modelo, no es un fallo de parseo. Los
  clientes reintentan con `RetryPolicy` (hasta 3 intentos); el de Gemini no fija timeout.
- El intérprete del arnés (`.venv` de la raíz) **no tiene** `openai`, `anthropic` ni
  `google-genai`: los tests no pueden importar `infrastructure/llm/*` ni, por tanto,
  `interface_adapters/api/app.py` tal cual (§7).

## 3. Ficheros

### A crear

- `services/partes-api/application/services/relectura_cabecera.py` — reglas puras (§4).
- `services/partes-api/tests/test_f058_relectura_cabecera.py` — reglas puras y pipeline.
- `services/partes-api/tests/test_f058_settings_wiring.py` — `Settings`, `build_app`, `/health`.

### A modificar

- `application/pipelines/extract_parte_pipeline.py` — kwarg `relectura_provider`, paso de
  relectura, envelope desde `data` (dict) con los bloques de traza (§4.2).
- `application/services/parte_extraction_service.py` — método público `model_name(provider)`
  (el modelo del proveedor de relectura para la traza también cuando la llamada falla) y
  docstring (deja de ser «un solo proveedor»).
- `config/settings.py` — dos variables, dos propiedades y docstring (§5).
- `interface_adapters/api/app.py` — pasa el proveedor activo al pipeline, log de cableado,
  `/health` (§6).
- `main_worker.py` — solo el docstring («Gemini primario» ya no es cierto). `docs/ARCHITECTURE.md` — punto 18 en «Semántica de dominio» y la línea «Google Gemini (sv2)»
  de «Acceso a datos».
- `infra/create_capps_partes.ps1` — solo el comentario de sv2 (l. 38–39): Gemini relee la
  cabecera; no se apaga `ENABLE_GEMINI` sin apagar `RELECTURA_CABECERA`. Encoding de `infra/`:
  sin BOM y CRLF. Sin variables nuevas (el script crea, no actualiza; DA5).
- `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (otro repositorio, commit local allí)
  — fila de sv2 (l. 927) y §3.2: sv2 consume Gemini en producción para la relectura.

### NO se tocan

- `config/prompts.yaml` y `domain/models/parte_models.py` (mismo prompt y mismo esquema).
- `infrastructure/llm/*` (clientes, `retry_policy.py`): la relectura usa los que hay.
- sv1, sv3 (`persist_parte_pipeline.py`, `parte_normalizer.py`), sv4, sv5, los dos
  `orm_models.py`, `infra/add_secrets_partes.ps1` (la clave de Gemini ya está en el KV) y
  `infra/redeploy_partes.ps1`.

## 4. Clases y funciones

### 4.1 `application/services/relectura_cabecera.py` (application, puro, sin dependencias)

```python
MOTIVO_CABECERA_VACIA = "cabecera_vacia"
RESULTADO_APLICADA, RESULTADO_VACIA, RESULTADO_ERROR = "aplicada", "vacia", "error"

def es_vacio(valor: object) -> bool              # None o str con solo espacios (R4)
def cabecera_vacia(data: Mapping[str, Any]) -> bool
    # obra_numero y fecha de data["cabecera"] vacíos; cabecera ausente o no dict = vacía
def con_trabajadores(data: Mapping[str, Any]) -> bool   # list con len >= 1 (R3)
def necesita_relectura(data: Mapping[str, Any]) -> bool  # cabecera_vacia and con_trabajadores
def relectura_util(data_relectura: Mapping[str, Any]) -> bool  # not cabecera_vacia (R4, R7)
```

Trabajan sobre el `dict` de `model_dump()`, no sobre `ParteTrabajo`: el pipeline no conoce el
esquema concreto, y un esquema sin `cabecera` simplemente no dispara (`con_trabajadores` o
`cabecera_vacia` lo resuelven sin `KeyError`).

### 4.2 `ExtractPartePipeline` (application)

- Constructor: kwarg nuevo `relectura_provider: str | None = None` (sin él, nada cambia).
- `run`: tras la primaria, `data = result.parsed.model_dump()`; si `relectura_provider` y
  `necesita_relectura(data)`, llama a `self._releer_cabecera(...)`, que devuelve
  `(data, meta_relectura, debug_relectura)`; si no, los dos bloques son `None`.
- `_releer_cabecera(*, attachment, dynamic_context, data, filename)`:

```python
model = self._service.model_name(self._relectura_provider)
logger.info("[sv2][relectura] cabecera vacia con %d filas file=%s -> %s/%s", ...)
debug = {"cabecera_primaria": data.get("cabecera")}
try:
    rel = self._service.extract(attachment=attachment, provider=self._relectura_provider,
                                prompt_key=self._prompt_key, dynamic_context=dynamic_context)
except Exception as exc:          # best-effort a propósito (R8); solo el tipo (R14)
    resultado, error_tipo = RESULTADO_ERROR, type(exc).__name__
else:
    debug.update(rel.debug_payload)
    rel_data = rel.parsed.model_dump()
    if relectura_util(rel_data):
        data = {**data, "cabecera": rel_data.get("cabecera")}   # R6: firma/empleados intactos
        resultado = RESULTADO_APLICADA
    else:
        resultado = RESULTADO_VACIA
# log INFO (aplicada) o WARNING (vacia/error) con file, provider, model, resultado, error_tipo
meta = {"motivo": MOTIVO_CABECERA_VACIA, "provider": self._relectura_provider,
        "model": model, "resultado": resultado, "error_tipo": error_tipo}
```

- `_envelope` pasa a recibir `data: dict` (en vez de leer `provider_result.parsed`) y los
  dos bloques opcionales; solo si no son `None` añade `meta["relectura_cabecera"]` y
  `debug["relectura_cabecera"]` (R13). El resto de `meta` no cambia (R11).
- El `except Exception` es la única captura amplia: un fallo de la relectura nunca debe
  costar la lectura primaria (DA4). `KeyboardInterrupt`/`SystemExit` no son `Exception`.

### 4.3 `ParteExtractionService.model_name(provider: str) -> str`

Devuelve `self._require_provider(provider).model_name` (mismo `KeyError` explicativo).

## 5. Configuración (`config/settings.py`)

```python
relectura_cabecera_enabled: bool = Field(True, alias="RELECTURA_CABECERA")
relectura_cabecera_provider: ProviderName = Field("gemini", alias="RELECTURA_CABECERA_PROVIDER")

@property
def relectura_cabecera_motivo_inactiva(self) -> str | None
    # None si está apagada o activa; si encendida e inactiva, en este orden:
    # "mismo_proveedor" (== ia_provider), "no_habilitado" (ENABLE_* false), "sin_clave"
@property
def relectura_cabecera_activa(self) -> str | None
    # el proveedor si enabled y sin motivo; None en otro caso
```

- La clave de cada proveedor se mira igual que en el validador actual (`strip()` no vacío);
  se extrae a un helper privado `_clave_de(provider)` que usan los dos, sin cambiar los
  mensajes de error del validador (R16).
- Sin variable de modelo propia (DA5 = A): el modelo es el del proveedor (`GEMINI_MODEL`).
- `extra="ignore"` ya está: un `.env` local sin las variables nuevas sigue valiendo.

## 6. Cableado (`interface_adapters/api/app.py`)

- `relectura = settings.relectura_cabecera_activa` (exige `ENABLE_*`, así que el proveedor
  siempre está instanciado).
- Log: `INFO "[partes-sv2][wiring] relectura cabecera ACTIVA provider=%s model=%s"`, o
  `WARNING "... relectura cabecera INACTIVA motivo=%s"` si está encendida e inactiva, o
  `INFO "... DESACTIVADA (RELECTURA_CABECERA=false)"`.
- `ExtractPartePipeline(..., relectura_provider=relectura)`.
- `/health`: `"relectura_cabecera": {"provider": ..., "model": ...}` o `None`.

## 7. Tests (sin red ni BBDD)

`test_f058_relectura_cabecera.py` (nombres `test_f058_rN_...`):

- **Puros** (R2–R4): tabla de casos de `cabecera_vacia` (los dos nulos, solo obra, solo
  fecha, blancos `"  "`, cabecera ausente) y de `necesita_relectura` (sin empleados).
- **Pipeline** con un `FakeVisionClient(LlmVisionClient)` por proveedor que devuelve un
  `ParteTrabajo` preparado o lanza, y guarda cada llamada (proveedor, `instructions`,
  adjunto); `ParteExtractionService` real con `YamlPromptRepository(config/prompts.yaml)` y
  `SchemaRegistry` reales; catálogo con un doble de `AuxhorCatalogProvider` (`enabled`,
  `prompt_block`). Casos: R1 (segunda llamada con el mismo adjunto e `instructions` idénticas,
  una sola vez), R2/R3/R5 (una sola llamada; con `relectura_provider=None`), R6 (cabecera
  entera de la relectura, también un `encargado_nombre` nulo; firma y empleados iguales a la
  primaria), R7 (`vacia`), R8 (lanza `ValueError` y un `RuntimeError` propio: no propaga,
  `error_tipo`), R9 (`ParteTrabajo.model_validate(envelope["data"])`), R10–R13 (claves y
  valores exactos de `meta`/`debug`; sin relectura, mismo conjunto de claves que hoy), R14
  (`caplog`: hay INFO y WARNING; ningún registro contiene el nombre ni el DNI de la fixture,
  la obra o la fecha releídas ni el mensaje de la excepción).
- Fixtures con datos inventados (`"TRABAJADOR PRUEBA"`, DNI ficticio): nada real.

`test_f058_settings_wiring.py`:

- `Settings(_env_file=None, **{alias: valor})` (no lee el `.env` local): por defecto
  encendida con `gemini`; combinaciones de R15 (`mismo_proveedor`, `no_habilitado`,
  `sin_clave`, apagada) y R16 (arranca con Gemini sin clave).
- `build_app` (R17, R18): `monkeypatch.setitem(sys.modules, ...)` con módulos falsos de
  `google`, `google.genai` (`Client`, `types`), `openai` (`OpenAI` con `.responses.parse`) y
  `anthropic`, e importación de `interface_adapters.api.app` dentro del test (retirándolo de
  `sys.modules` al acabar). Se comprueba el `relectura_provider` del pipeline, el log de
  cableado con `caplog` y `/health` con `fastapi.testclient.TestClient` (fastapi y httpx están
  en el `.venv`). Ningún cliente real se construye ni llama a nadie.

Mutación muestreada (estándar) sobre el alcance de la feature; los supervivientes se analizan
en `progress/impl_F-058.md`.

## 8. Riesgos y decisiones

- **Latencia y visibilidad de la cola**: una relectura suma ~8 s (batería: 7–11 s, una de
  32 s). En el peor caso (primaria con 3 intentos a 180 s y relectura lenta) se acerca a
  `COLA_VISIBILITY_S=600` y el mensaje podría reaparecer; ya pasa hoy con la primaria sola y
  sv3 descarta el duplicado por `source_sha256`. Se acepta (DA7); no se toca el cliente.
- **Coste**: solo cuando se dispara, ~6,5 k tokens de entrada y ~0,5 k de salida (batería).
- **Membrete distinto**: la relectura trae su `empresa_membrete`; sv3 decide la empresa con
  él como siempre (F-023). Tomar la cabecera entera evita mezclar obra de un modelo y membrete
  de otro (DA3).
- **Si se apaga Gemini** (`ENABLE_GEMINI=false`), la relectura queda inactiva con WARNING en
  el arranque, sin caer (R16), y F-054 sigue mandando a revisión.
- Descartados: reforzar el prompt (sin medir; obligaría a repetir la batería de F-051) y
  cambiar el modelo primario (F-051 lo eligió por las filas).

## 9. Verificación manual (humano o líder)

- **M0** (solo lectura, antes de desplegar):
  `az containerapp show -n ca-sv2-extraccion -g rg-partes-dev --query "properties.template.containers[0].env[?starts_with(name,'ENABLE_GEMINI') || starts_with(name,'GEMINI_') || starts_with(name,'RELECTURA')]" -o table`
  ⇒ `ENABLE_GEMINI=true`, `GEMINI_MODEL=gemini-4-argon`, `GEMINI_API_KEY` con `secretRef`
  (no imprime valores) y ninguna `RELECTURA_*`. Si falta algo, se para y decide el humano.
- **M1** (local, sin escrituras; repetible con la batería del líder en el scratchpad,
  `bench/`, claves del KV solo en el proceso como `lanzar.ps1`): un script fuera del repo que
  construya el pipeline de la rama con `build_app(Settings())` y lo ejecute sobre las 6 PDF de
  `paginas_sincab/` y las 2 de `paginas_control/`, volcando por página `resultado`, si hay
  obra y fecha y las filas (nº y horas), sin nombres ni DNIs. Esperado: 6/6 `aplicada` con
  obra y fecha, filas idénticas a la primaria; control 2/2 sin `relectura_cabecera`.
- **M2** (solo lectura, tras desplegar sv2; base `partes`, transacción READ ONLY):
  `SELECT raw_extraction_json::jsonb->'meta'->'relectura_cabecera'->>'resultado' AS r, count(*) FROM parte_documents WHERE created_at_utc >= '<FECHA_DESPLIEGUE>' GROUP BY 1;`
  ⇒ la mayoría `NULL` (sin relectura); cada `vacia`/`error` debe tener `review_required`
  (con F-054 desplegada).
- **M3** (los 6 ya guardados; DA8). Por defecto (A): ningún agente escribe; con F-054 M2 ya
  marcados a revisión, Administración pone obra (`PATCH /api/partes/{id}/obra`) y fecha
  (F-043) en el portal. Alternativa B, solo con autorización expresa y tras un SELECT que
  confirme que ninguna línea está aprobada, editada ni en Sigrid: `UPDATE parte_documents
  SET is_active = false` de esos 6 `id` en una transacción y devolver los 2 correos a la
  bandeja como no leídos para que sv1 los reingiera (las páginas aún activas se omiten por
  `source_sha256`).

## 10. Decisiones abiertas (las valida el humano)

| DA | Pregunta | Alternativas | Recomendación |
|---|---|---|---|
| DA1 | ¿Qué es «cabecera vacía»? | A) los seis campos nulos; **B) `obra_numero` y `fecha` vacíos (con blancos), con ≥ 1 fila**; C) obra **o** fecha vacía | **B**: cubre los 6 casos, son los dos campos que importan (F-054) y no relee partes con solo la fecha sin escribir (C costaría llamadas y mezclaría una obra buena con otra lectura). A falla si el modelo rellena, p. ej., el encargado |
| DA2 | ¿Qué se relee? | **A) la página entera con el mismo prompt y esquema**; B) prompt y esquema solo de cabecera; C) recorte de la imagen | **A**: es lo medido (6/6) y no añade prompt que mantener; B ahorra ~0,4 k tokens de salida sin medir; C es preproceso nuevo |
| DA3 | ¿Qué se toma de la relectura? | **A) la cabecera entera si trae obra o fecha**; B) campo a campo, solo los nulos de la primaria; C) el parte entero de Gemini | **A**: una cabecera coherente de una sola lectura (obra y membrete del mismo modelo); C tira las filas, que es por lo que se usa `gpt-6.1-sol` |
| DA4 | ¿Y si la relectura falla o sale vacía? | **A) se queda la primaria, traza y WARNING; F-054 la manda a revisión**; B) propagar el error (reintento de cola y `-poison`); C) probar un tercer proveedor | **A**: B perdería una lectura de filas buena y multiplicaría coste; C no está medido |
| DA5 | Configuración | **A) `RELECTURA_CABECERA` (sí por defecto) y `RELECTURA_CABECERA_PROVIDER` (`gemini`), modelo y clave del proveedor ya desplegados, sin cambios de entorno en Azure**; B) apagada por defecto y el humano la enciende con `az containerapp update --set-env-vars RELECTURA_CABECERA=true`; C) variable de modelo propia | **A**: Gemini ya está habilitado y con clave en sv2 (M0 lo confirma); para apagarla basta `RELECTURA_CABECERA=false`. Si el humano prefiere estrenarla a mano, B (la ejecuta él) |
| DA6 | Trazabilidad | **A) `meta.relectura_cabecera` + `debug.relectura_cabecera`, solo cuando se dispara; `meta.provider/model` del primario**; B) columna en `parte_documents`; C) solo log | **A**: queda en `raw_extraction_json` sin migración; B toca el ORM duplicado de sv3 y sv4 por un dato de auditoría |
| DA7 | Coste y latencia | **A) aceptar (~7 k tokens y ~8 s solo cuando se dispara)**; B) relectura sin reintentos (`RetryPolicy` propia) | **A**: es raro y el reintento protege de un 429 puntual; B exige otro cliente Gemini en el cableado |
| DA8 | ¿Los 6 ya guardados? | **A) corrección a mano en el portal (obra y fecha), tras F-054 M2**; B) reproceso autorizado (desactivar y reingerir, §9 M3); C) nada | **A**: sin escrituras de agentes ni riesgo de pisar ediciones; B solo si el humano lo pide y el SELECT previo sale limpio |
