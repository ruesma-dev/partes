<!-- specs/F-058-relectura-cabecera-gemini/design.md -->
# F-058 · Relectura de la cabecera con Gemini y prompt de cabecera — diseño técnico

## 1. Encaje y límite de servicio

- **Solo sv2**: es el único que llama a la IA y ya lee sigrid-api (auxhor). **sv3 no cambia**:
  guarda `raw_extraction_json` entero (traza sin columna ni migración).
- **Consulta de obra (DA10 = B)**: sv2 pregunta en el momento «¿hay alguna obra en Sigrid con
  esta clave?», en cualquier empresa. **No es la conciliación de sv3** (`obra_matcher.py`,
  `seleccion_sigrid.py`): no la copia, no elige obra ni empresa y solo dispara la relectura. Su
  clave es más gruesa (cualquier número de ceros): todo código que sv3 casaría por código
  existe para ella. La lista cerrada de duplicados de `CLAUDE.md` **no crece**.

## 2. Lo que hay hoy (`dev` 38f273a)

- `ExtractPartePipeline.run` llama **una vez** a `extract(provider=IA_PROVIDER, ...)` con el
  catálogo auxhor; el servicio ya tiene los proveedores por nombre. `ExtractParteRequest` no
  lleva `document_id` (solo lo conoce `main_worker.py`).
- Azure (`infra/create_capps_partes.ps1` l. 31–53): `IA_PROVIDER=openai`, **Gemini habilitado
  con `gemini-4-argon` y clave por secretref** y las tres `SIGRID_API_*` (base `ruesma`): **sin
  cambios de entorno**. `SigridLookupClient` no mira `truncated`, usa un `timeout_s` único (30)
  y crea su `httpx.Client` en cada llamada; sigrid-api admite `?` con `parameters`
  (`azure-apps/sigrid_api.md` §5.2). `con.cod` es «Texto de 24».
- El punto 1 del prompt (UTF-8, CRLF) no avisa de la cabecera. El `.venv` no trae SDK de IA.

## 3. Ficheros (sin prefijo: `services/partes-api/`)

**A crear**: `application/services/relectura_cabecera.py` (§4.1),
`application/services/obra_sigrid.py` (§4.2), `domain/ports/existencia_obra_port.py`
(`ExistenciaObraPort(Protocol)`: `existe_obra(clave: str, *, timeout_s: float) -> bool`) y
`tests/test_f058_{relectura_cabecera,obra_sigrid,prompt,settings_wiring}.py` (§8).

**A modificar**: `infrastructure/sigrid/sigrid_lookup_client.py` (§4.3; docstring: ya no es
solo del portal), `application/pipelines/extract_parte_pipeline.py` (§4.4),
`parte_extraction_service.py` (`model_name`), `main_worker.py` (pasa `document_id`, R15),
`config/settings.py` (§6), `interface_adapters/api/app.py` (§7), `config/prompts.yaml` (solo el
punto 1 de `task`, §5) y los docstrings de «un proveedor» / «Gemini primario»; fuera de sv2,
`docs/ARCHITECTURE.md` (punto 18; en «Acceso a datos», Gemini relee y sv2 lee auxhor y consulta
obras en sigrid-api, cuyo tope es 500.000 filas), el comentario de sv2 en
`infra/create_capps_partes.ps1` (sin BOM, CRLF) y `azure-apps/partes.md` (commit local allí:
diagrama sv2 → sigrid-api, §3.2 y fila sv2 de §5.6).

**NO se tocan**: `parte_models.py`, `infrastructure/llm/*`, `auxhor_catalog_provider.py`; sv1,
sv3, sv4, sv5, los `orm_models.py`, los scripts de secretos y despliegue; ni
`azure-apps/sigrid_api.md` (es de sigrid-api; no lista a partes: se avisa al humano).

## 4. Clases y funciones

### 4.1 `application/services/relectura_cabecera.py` (application, puro)

```python
MOTIVO_CABECERA_VACIA, MOTIVO_OBRA_INEXISTENTE = "cabecera_vacia", "obra_inexistente"
RESULTADO_APLICADA, RESULTADO_VACIA, RESULTADO_NO_CASA, RESULTADO_ERROR = "aplicada", "vacia", "no_casa", "error"
ExisteObra = Callable[[str], bool | None]        # True / False / None = «no se sabe»
def es_vacio(valor: object) -> bool              # None o str con solo espacios (R5)
def clave_obra(codigo: object) -> str            # "" si vacío; NFKD sin marcas, upper, sin
    # blancos ni "-"; si isdigit(): lstrip("0") or "0"
def cabecera_vacia(data) -> bool                 # obra_numero y fecha vacíos; sin dict = vacía
def con_trabajadores(data) -> bool               # list con len >= 1
def motivo_relectura(data, existe: ExisteObra) -> str | None
    # sin trabajadores -> None y cabecera vacía -> cabecera_vacia, SIN llamar a existe;
    # obra no vacía y existe(obra) is False -> obra_inexistente; si no, None
def resultado_relectura(motivo, data_relectura, existe: ExisteObra, obra_primaria) -> str
    # cabecera_vacia: aplicada si no cabecera_vacia(rel), si no vacia (nunca llama a existe)
    # obra_inexistente: obra vacía -> vacia; misma clave que obra_primaria -> no_casa sin
    # llamar (R8); existe(obra) is True -> aplicada; False o None -> no_casa
```

### 4.2 `application/services/obra_sigrid.py` (application)

- `ConsultaObra` (dataclass congelada): `existe: bool | None` (`None` = «no se sabe», R9),
  `ms: int` (medido también si falla) y `error_tipo: str | None`.
- `ComprobadorObra(*, client: ExistenciaObraPort, timeout_s: float = 5.0, reloj=time.perf_counter)`,
  sin estado ni caché (DA10 = B); `consultar(codigo, *, document_id) -> ConsultaObra`: clave
  vacía ⇒ `ConsultaObra(None, 0, None)` sin llamar; si no, `reloj()` antes y después de
  `client.existe_obra(clave, timeout_s=...)`; cualquier excepción ⇒ `existe=None` y su
  `type(exc).__name__` (nunca lanza). Log (R10): INFO `"[obra-sigrid] document_id=%s
  resultado=%s ms=%d"` (`existe` | `no_existe`) o WARNING `"... resultado=error error=%s
  ms=%d"`; sin código ni clave; `document_id` `None` ⇒ `"-"`.

### 4.3 `SigridLookupClient` (infrastructure)

`_SQL_EXISTE_OBRA`, constante con un solo `?` (la clave de §4.1, en `parameters`), calcula la
misma clave sobre `con.cod` (mayúsculas y acentos, por la intercalación `Latin1_General_CI_AI`):

```sql
SELECT TOP 1 con.cod AS codigo
FROM obr JOIN con ON obr.ide = con.ide
CROSS APPLY (SELECT REPLACE(REPLACE(con.cod, ' ', ''), '-', '') AS n) a
CROSS APPLY (SELECT CASE WHEN a.n <> '' AND a.n NOT LIKE '%[^0-9]%'
    THEN ISNULL(NULLIF(SUBSTRING(a.n, PATINDEX('%[^0]%', a.n + 'X'), 24), ''), '0')
    ELSE a.n END AS clave) k
WHERE con.cod IS NOT NULL AND k.clave COLLATE Latin1_General_CI_AI = ?
```

- `existe_obra(self, clave, *, timeout_s) -> bool`: `_post_sql_read(parameters=[clave],
  label="existe_obra", max_rows=2, exigir_completo=True, timeout_s=timeout_s)` ⇒ `len(rows) >=
  1`. Sin filtro de empresa ni de baja (R7); misma base que el catálogo (`ruesma`).
- `_post_sql_read(..., max_rows=None, exigir_completo=False, timeout_s=None)`: con
  `exigir_completo` y `body.get("truncated") is True` ⇒ `RuntimeError("sigrid-api trunco la
  respuesta (<label>)")`; con `timeout_s`, lo usan el `httpx.Client` y `timeout_seconds =
  max(1, ceil(timeout_s))`. `fetch_tipos_hora` no cambia (los valores de hoy por defecto).
- Constructor: `transport: httpx.BaseTransport | None = None` (defecto: el de hoy) para tests.

### 4.4 `ExtractPartePipeline` (application)

- `ExtractParteRequest` gana `document_id: str | None = None` (R15); `main_worker.py` lo pasa.
- Kwargs `relectura_provider: str | None = None` y `obras: ComprobadorObra | None = None` (sin
  ellos nada cambia). En `run`, con `relectura_provider`: una lista `ms` de la página y un
  `existe(c)` local que llama a `obras.consultar(c, document_id=...)`, apunta su `ms` y devuelve
  `.existe` (sin `obras`, `None` sin log: el WARNING es el del cableado, §7).
- Si `motivo := motivo_relectura(data, existe)`, `_releer_cabecera`: `model =
  service.model_name(relectura_provider)`; INFO `"[sv2][relectura] document_id=%s motivo=%s
  filas=%d file=%s -> %s/%s"`; `debug = {"cabecera_primaria": ...}`; `service.extract(...)` con
  el proveedor de relectura y el mismo `prompt_key` y `dynamic_context` dentro de un `try` con
  `except Exception` (best-effort a propósito, R14: `resultado = "error"`, `error_tipo =
  type(exc).__name__`); si responde, `debug.update(rel.debug_payload)` y `resultado =
  resultado_relectura(motivo, rel.parsed.model_dump(), existe, obra_primaria)`; con `aplicada`,
  `data = {**data, "cabecera": <la releída>}` (R12: firma y empleados intactos). Al final INFO
  (`aplicada`) o WARNING con `document_id`, file, provider, model, motivo, resultado y
  `error_tipo` (R20), y `meta = {"motivo", "provider", "model", "resultado", "error_tipo",
  "consulta_obra_ms": list(ms)}` (R16).
- `_envelope` recibe `data: dict` y los dos bloques; solo si no son `None` añade
  `meta/debug["relectura_cabecera"]` (R19). Es la única captura amplia del pipeline.
- `ParteExtractionService.model_name(provider)` = `self._require_provider(provider).model_name`
  (mismo `KeyError`): el modelo va a la traza también cuando la llamada falla.

## 5. Prompt (`parte_trabajo_es.task`, punto 1; DA9)

Tras `1) CABECERA (datos del dia/obra):` se inserta este párrafo (sangría de 7 espacios, como
las viñetas; estilo del fichero, sin tildes salvo `Nº` y `año`) y se amplía la viñeta de fecha:

```text
       TODA pagina del parte tiene una CABECERA en su parte superior, por
       encima de la tabla "PERSONAL": el membrete o logotipo de la empresa,
       el "Nº OBRA", el "NOMBRE Y UBICACION DE OBRA", la FECHA (dia, mes y
       año), el ENCARGADO y el JEFE DE OBRA. Localizala SIEMPRE antes de
       leer la tabla y saca de ella el numero de la obra, el dia, el mes y
       el año de la fecha, la empresa del membrete y el resto de campos de
       este punto. Si el escaneo sale desplazado, girado, recortado o con
       bandas grises, la cabecera sigue en la pagina: buscala en el borde
       que corresponda segun la orientacion de la tabla. Si la tabla tiene
       trabajadores y la cabecera te sale entera a null, casi siempre es que
       no la has localizado: buscala de nuevo antes de responder. Aun asi,
       NUNCA inventes un valor: null solo en el campo que de verdad no se lea.
       - cabecera.fecha: <texto de hoy hasta ...como "6-abril-26").> Si el
         dia, el mes y el año van en casillas separadas, copialos juntos en
         ese orden (dia/mes/año) tal cual se leen. No la conviertas; si es
         ilegible, null.
```

Nada más cambia (R23): `system` («NO la conviertas ni reordenes» vale: juntar casillas en su
orden no es reordenar), puntos 2–6 y `schema_hint`. Vale para ambas lecturas: banco MB (§10).

## 6. Configuración (`config/settings.py`)

```python
relectura_cabecera_enabled: bool = Field(True, alias="RELECTURA_CABECERA")
relectura_cabecera_provider: ProviderName = Field("gemini", alias="RELECTURA_CABECERA_PROVIDER")
obra_existe_timeout_s: float = Field(5.0, gt=0, alias="OBRA_EXISTE_TIMEOUT_S")   # DA12
```

Propiedades `relectura_cabecera_motivo_inactiva -> str | None` (`None` si apagada o activa; si
no, por orden `mismo_proveedor`, `no_habilitado`, `sin_clave`) y `relectura_cabecera_activa ->
str | None` (el proveedor si está encendida y sin motivo). La clave se mira como en el
validador (`strip()` no vacío) con un helper `_clave_de(provider)` común, sin cambiar sus
mensajes (R24). Sin variable de modelo propia (DA5).

## 7. Cableado (`interface_adapters/api/app.py`)

- `obras = ComprobadorObra(client=sigrid_client, timeout_s=settings.obra_existe_timeout_s)`
  solo con `relectura_cabecera_activa` y `sigrid_client` (el de hoy), si no `None`; ambos al
  pipeline. Log `"[partes-sv2][wiring] relectura cabecera ACTIVA provider=%s model=%s
  comprueba_obra=%s timeout_obra_s=%s"` (INFO, o WARNING sin sigrid-api), `"... INACTIVA
  motivo=%s"` (WARNING) o `"... DESACTIVADA"` (INFO). `/health`: `"relectura_cabecera"` o `None`.

## 8. Tests (sin red ni BBDD; `test_f058_rN_...`; fixtures inventadas, obra `"9999"`)

- `test_f058_relectura_cabecera.py`. Puros: `es_vacio`, `cabecera_vacia`, `clave_obra`
  (`"0672"`/`"00672"` → `"672"`, `"000"` → `"0"`, `" a-12 "` → `"A12"`, acento),
  `motivo_relectura` y `resultado_relectura` (con un `existe` doble que apunta llamadas: R8).
  Pipeline con un `FakeVisionClient(LlmVisionClient)` por proveedor (devuelve o lanza; guarda
  proveedor, `instructions` y adjunto), servicio, prompts y esquemas reales y `ComprobadorObra`
  con puerto doble y reloj falso: R1–R4, R6–R9, R11–R20 (`caplog` sin nombre, DNI, obra, fecha
  ni mensaje de excepción).
- `test_f058_obra_sigrid.py`: `ComprobadorObra` (una llamada por consulta, sin caché; clave
  vacía sin llamar; excepción ⇒ `None`, tipo y WARNING; ms del reloj falso; INFO con
  `document_id` y sin código; R7, R9, R10) y `existe_obra` con `httpx.MockTransport`
  (`parameters == [clave]`, la clave fuera del texto SQL, `max_rows` 2, `timeout_seconds` del
  argumento, 0/1 filas, `truncated` o 500 ⇒ `RuntimeError`); `fetch_tipos_hora` como hoy.
- `test_f058_prompt.py` (estilo F-051): el párrafo va entre el título del punto 1 y
  `- cabecera.fecha:` y nombra `"personal"`, `nº obra`, `dia`, `mes`, `año`, `membrete`,
  `desplazado`, `null` y `nunca inventes`; la viñeta de fecha, `casillas separadas` (R21, R22).
- `test_f058_settings_wiring.py`: `Settings(_env_file=None, ...)` (R24; tope ≤ 0 rechazado);
  `build_app` con SDK falsos en `sys.modules` e import de `app.py` dentro del test: pipeline,
  `obras` con y sin `SIGRID_API_*`, logs y `/health` con `TestClient` (R25, R26); y
  `main_worker` pasa `document_id` con dobles de cola y blob (R15).

## 9. Riesgos

- **Latencia y coste**: una relectura suma ~8 s (7–11 s, una de 32 s) y ~7 k tokens (cola: ya
  pasa hoy; sv3 descarta por `source_sha256`). **Consulta por página (DA10 = B)**: casi todas
  las páginas consultan (dos como mucho), con carga sobre sigrid-api y Sigrid; la clave sobre
  `con.cod` impide usar un índice (recorre `obr ⨝ con`); no está medido: es M4.
- **Tope** (DA12, 5 s): `httpx` lo aplica por fase y `retries=1` reintenta la conexión, así
  que el peor caso ronda 2–3 veces el tope. Un arranque en frío de sigrid-api puede pasarlo:
  esa página no relee por obra (WARNING) y la red es F-054. Si sigrid-api rechazara el SQL
  (`CROSS APPLY`, `COLLATE`), M1 lo vería como `error` sin romper la extracción.
- **Fecha** con `obra_inexistente`: si la releída trae obra sin fecha, se pierde la primaria y
  F-054 manda a revisión (DA11). **Prompt**: cambia todas las extracciones; puerta MB (DA9).

## 10. Verificación manual (humano o líder)

- **M0** (solo lectura): `az containerapp show -n ca-sv2-extraccion -g rg-partes-dev --query
  "properties.template.containers[0].env[?starts_with(name,'GEMINI_') || starts_with(name,
  'ENABLE_GEMINI') || starts_with(name,'SIGRID_API_')]" -o table` ⇒ Gemini con
  `gemini-4-argon`, claves por `secretRef`, base `ruesma`. Si no, decide el humano.
- **MB** (**lo lanza el líder** tras el commit del prompt: `lanzar.ps1` del scratchpad con
  `-Repo C:\Users\pgris\PycharmProjects\partes-wt-f058`, sin relectura): (a) `-Paginas
  paginas_sincab -Runs 2 openai:gpt-6.1-sol` ⇒ cuántas de 12 traen obra y fecha (antes 0; no es
  puerta); (b) `paginas_control` con `gpt-6.1-sol` ⇒ como `control.jsonl`; (c) sincab con
  `gemini:gemini-4-argon` ⇒ 6 de 6; (d) batería de F-051 (3 pasadas, `corregir.py`) ⇒ 42 de
  42. Puerta: (b)–(d) sin regresión, o decide el humano. Va a `progress/banco_F-058.md`.
- **M1** (local, sin escrituras): script fuera del repo con `build_app(Settings())` (claves del
  KV solo en el proceso) sobre las dos carpetas, volcando por página motivo, resultado, si hay
  obra y fecha, filas y ms, sin nombres ni DNIs ⇒ obra y fecha en las 6, filas iguales, control
  sin relectura, ninguna consulta `error`; sus ms son los primeros tiempos.
- **M2** (solo lectura, tras desplegar, READ ONLY): `SELECT j->>'motivo', j->>'resultado',
  count(*) FROM (SELECT raw_extraction_json::jsonb->'meta'->'relectura_cabecera' j FROM
  parte_documents WHERE created_at_utc >= '<FECHA_DESPLIEGUE>') s GROUP BY 1, 2;`.
- **M4** (solo lectura, tras desplegar; tiempos): `<WORKSPACE_ID>` es el `customerId` de
  `appLogsConfiguration` del entorno (`az containerapp env show`); luego `az
  monitor log-analytics query -w <WORKSPACE_ID> --analytics-query "ContainerAppConsoleLogs_CL |
  where ContainerAppName_s == 'ca-sv2-extraccion' and Log_s has '[obra-sigrid]' | extend ms =
  toint(extract('ms=([0-9]+)', 1, Log_s)), res = extract('resultado=([a-z_]+)', 1, Log_s) |
  summarize n=count(), p50=percentile(ms,50), p95=percentile(ms,95), max_ms=max(ms) by
  bin(TimeGenerated, 1d), res"` ⇒ consultas, mediana, p95, máximo y `error` por día (con
  `'[sv2][relectura]'`, las relecturas). Con eso el humano cierra DA12.
- **M3** (DA8 = A): ningún agente escribe; Administración pone obra y fecha en el portal.

## 11. Decisiones

| DA | Tema | Estado y decisión |
|---|---|---|
| DA1 | Cuándo releer | **Enmendada y aprobada**: cabecera vacía (obra y fecha) **o** obra leída inexistente en Sigrid, con ≥ 1 fila; confirmada el 2026-10-23 («si la obra no existe se manda a relectura a gemini»). Fecha sin obra no relee (F-054 la manda a revisión) |
| DA2–DA8 | Relectura, toma, fallo, configuración, traza, coste, los 6 guardados | Aprobadas, todas A: página entera con el mismo prompt y esquema; cabecera entera si es útil; si falla o no es útil, la primaria con traza y WARNING; `RELECTURA_CABECERA` encendida y `RELECTURA_CABECERA_PROVIDER=gemini` sin cambios de entorno; `meta`/`debug.relectura_cabecera` solo al releer; coste aceptado; los 6, a mano en el portal |
| DA9 | Prompt de cabecera | **Pedido por el humano**; texto de §5, solo el punto 1. **Aprobada A** por el humano el 2026-10-23 («a a todo»): la puerta de MB (si (b)–(d) empeoran, se quita el párrafo y queda la relectura) |
| DA10 | Comprobación de existencia | **Decidida B** por el humano el 2026-10-23: consulta en el momento por página, sin lista cacheada; se miden los tiempos (R10, M4) |
| DA11 | Cabecera con `obra_inexistente` | **Aprobada A** por el humano el 2026-10-23 («a a todo»): la releída entera si su obra existe (como DA3). B) la releída con la fecha primaria si la releída no trae: mezcla dos lecturas de una cabecera ya dudosa |
| DA12 | Consulta de obra que falla o tarda | **Aprobada A** por el humano el 2026-10-23 («a a todo»): tope `OBRA_EXISTE_TIMEOUT_S` = 5 s (la relectura cuesta ~8 s; una consulta de una fila debería ir muy por debajo); fallo, `truncated` o tope superado = «no se sabe»: no relee por obra, WARNING y la extracción sigue. B) fallo = releer: Gemini en todas las páginas con obra mientras sigrid-api falle. Se revisa con los tiempos de M4 |
