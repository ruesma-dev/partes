<!-- specs/F-058-relectura-cabecera-gemini/design.md -->
# F-058 · Relectura de la cabecera con Gemini y prompt de cabecera — diseño técnico

## 1. Encaje y límite de servicio

- **Solo sv2**: lee el papel, es el único que llama a la IA y ya lee sigrid-api (auxhor).
  **sv3 no cambia**: recibe `data` conforme a `ParteTrabajo` y guarda `raw_extraction_json`
  entero (traza sin columna ni migración); `meta.provider/model` siguen siendo del primario.
- **Comprobación de existencia (opción A, aprobada)**: sv2 solo pregunta «¿hay alguna obra en
  Sigrid con esta clave?», en cualquier empresa. **No es la conciliación de sv3**
  (`obra_matcher.py`, `seleccion_sigrid.py`): no la importa ni la copia, no elige obra ni
  empresa y solo dispara la relectura. Su clave es más gruesa (cualquier número de ceros), así
  que todo código que sv3 casaría por código está en la lista: nunca relee un parte que sv3
  casaría por código. La lista cerrada de duplicados de `CLAUDE.md` **no crece**. Descartado
  releer en sv3 (no llama a la IA) o en un servicio nuevo.

## 2. Lo que hay hoy (`dev` 38f273a)

- `ExtractPartePipeline.run` llama **una vez** a `extract(provider=IA_PROVIDER, ...)` con el
  catálogo auxhor; el servicio ya tiene los proveedores por nombre (releer no toca clientes).
- Azure (`infra/create_capps_partes.ps1` l. 31–53): `IA_PROVIDER=openai`, **Gemini habilitado
  con `gemini-4-argon` y clave por secretref** y las tres `SIGRID_API_*` (base `ruesma`): **sin
  cambios de entorno**. `SigridLookupClient` pide `max_rows` 10.000, **no mira `truncated`** y
  crea su `httpx.Client` dentro. `con.cod` es «Texto de 24» (`DISTINCT` vale).
- El punto 1 del prompt (UTF-8, CRLF) lista los seis campos, pero no dice que la cabecera
  existe ni qué hacer con un escaneo desplazado. El `.venv` del arnés no tiene los SDK de IA.

## 3. Ficheros (sin prefijo: `services/partes-api/`)

**A crear**: `application/services/relectura_cabecera.py` (§4.1),
`application/services/obras_sigrid.py` (§4.2), `domain/ports/codigos_obra_port.py`
(`CodigosObraPort(Protocol)` con `fetch_codigos_obra() -> list[str]`: application no importa
infraestructura) y los tests `tests/test_f058_relectura_cabecera.py`,
`tests/test_f058_obras_sigrid.py`, `tests/test_f058_prompt.py` y
`tests/test_f058_settings_wiring.py` (§8).

**A modificar**:

- `infrastructure/sigrid/sigrid_lookup_client.py` (§4.3, docstring: ya no es solo del portal),
  `application/pipelines/extract_parte_pipeline.py` (§4.4), `parte_extraction_service.py`
  (`model_name`), `config/settings.py` (§6), `interface_adapters/api/app.py` (§7),
  `config/prompts.yaml` (solo el punto 1 de `task`, §5) y los docstrings de «un proveedor» /
  «Gemini primario» (`settings.py`, servicio, pipeline, `main_worker.py`).
- `docs/ARCHITECTURE.md`: punto 18 de «Semántica de dominio»; en «Acceso a datos», Gemini (sv2
  relee) y sigrid-api (sv2 lee auxhor y obras; el tope de la instancia es 500.000, no 1.000).
- `infra/create_capps_partes.ps1`: solo el comentario de sv2 (sin BOM, CRLF, sin variables).
- `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (commit local allí): diagrama (sv2 →
  sigrid-api), §3.2 (relectura y comprobación de obra) y la fila sv2 de §5.6.

**NO se tocan**: `domain/models/parte_models.py`, `infrastructure/llm/*`,
`auxhor_catalog_provider.py`; sv1, sv3 (`obra_matcher.py`, `seleccion_sigrid.py`), sv4, sv5,
los dos `orm_models.py`, `infra/add_secrets_partes.ps1`, `infra/redeploy_partes.ps1`; y
`azure-apps/sigrid_api.md`, que es de sigrid-api (su tabla de consumidores no lista partes:
se avisa al humano).

## 4. Clases y funciones

### 4.1 `application/services/relectura_cabecera.py` (application, puro)

```python
MOTIVO_CABECERA_VACIA, MOTIVO_OBRA_INEXISTENTE = "cabecera_vacia", "obra_inexistente"
RESULTADO_APLICADA, RESULTADO_VACIA, RESULTADO_NO_CASA, RESULTADO_ERROR = (
    "aplicada", "vacia", "no_casa", "error")
ExisteObra = Callable[[str], bool | None]        # True / False / None = «no se sabe»

def es_vacio(valor: object) -> bool              # None o str con solo espacios (R5)
def clave_obra(codigo: object) -> str            # "" si vacío; NFKD sin marcas, upper, sin
    # blancos ni "-"; si isdigit(): lstrip("0") or "0"
def cabecera_vacia(data) -> bool                 # obra_numero y fecha vacíos; sin dict = vacía
def con_trabajadores(data) -> bool               # list con len >= 1
def motivo_relectura(data, existe: ExisteObra) -> str | None
    # sin trabajadores -> None y cabecera vacía -> cabecera_vacia, los dos SIN llamar a existe;
    # obra no vacía y existe(obra) is False -> obra_inexistente; si no, None
def resultado_relectura(motivo: str, data_relectura, existe: ExisteObra) -> str
    # cabecera_vacia: aplicada si no cabecera_vacia(rel), si no vacia
    # obra_inexistente: obra vacía -> vacia; existe(obra) is True -> aplicada; si no, no_casa
```

### 4.2 `application/services/obras_sigrid.py` (application)

```python
class ObrasSigrid:
    def __init__(self, *, client: CodigosObraPort, ttl_seconds: int = 600,
                 reloj: Callable[[], float] = time.monotonic) -> None
        # no carga nada; dos hilos de la API podrían cargar a la vez (solo dos consultas)
    def existe(self, codigo: str) -> bool | None
        # clave vacía -> None; caducada o sin cargar -> _cargar(); sin claves -> None;
        # si no, clave_obra(codigo) in claves. Nunca lanza.
    def _cargar(self) -> None   # éxito con >= 1 clave: claves = {clave_obra(c)} - {""} e INFO
        # "[obras-sigrid] %d claves"; excepción (también truncated) o 0 claves: WARNING con
        # type(exc).__name__ o "lista_vacia" y se conservan las anteriores (o None).
        # Siempre ts = reloj(): no reintenta hasta pasado el TTL (R9, DA10).
```

### 4.3 `SigridLookupClient` (infrastructure)

- `_SQL_CODIGOS_OBRA` = `SELECT DISTINCT con.cod AS codigo FROM obr JOIN con ON obr.ide =
  con.ide WHERE con.cod IS NOT NULL`; `_MAX_CODIGOS_OBRA = 50_000`; `fetch_codigos_obra(self)
  -> list[str]` (`_opt_str` de cada fila, sin `None`; INFO con el número).
- `_post_sql_read(..., max_rows: int | None = None, exigir_completo: bool = False)`: con
  `exigir_completo` y `body.get("truncated") is True` ⇒ `RuntimeError("sigrid-api trunco la
  respuesta (<label>)")`. `fetch_tipos_hora` no cambia (por defecto `False`).
- Constructor: `transport: httpx.BaseTransport | None = None` (por defecto el
  `HTTPTransport(retries=1)` de hoy), para probar con `httpx.MockTransport`.
- Misma base que el catálogo (`SIGRID_API_DATABASE`, `ruesma`); sentencia constante, sin `?`.

### 4.4 `ExtractPartePipeline` (application)

- Kwargs `relectura_provider: str | None = None` y `obras: ObrasSigrid | None = None` (sin ellos
  nada cambia); `self._existe = obras.existe if obras else (lambda _c: None)`. En `run`, si hay
  `relectura_provider` y `motivo := motivo_relectura(data, self._existe)`, `_releer_cabecera`
  devuelve `(data, meta_relectura, debug_relectura)`:

```python
model = self._service.model_name(self._relectura_provider)
logger.info("[sv2][relectura] motivo=%s filas=%d file=%s -> %s/%s", ...)  # sin valores (R19)
debug, error_tipo = {"cabecera_primaria": data.get("cabecera")}, None
try:
    rel = self._service.extract(attachment=attachment, provider=self._relectura_provider,
                                prompt_key=self._prompt_key, dynamic_context=dynamic_context)
except Exception as exc:          # best-effort a propósito (R13); solo el tipo (R19)
    resultado, error_tipo = RESULTADO_ERROR, type(exc).__name__
else:
    debug.update(rel.debug_payload)
    rel_data = rel.parsed.model_dump()
    resultado = resultado_relectura(motivo, rel_data, self._existe)
    if resultado == RESULTADO_APLICADA:
        data = {**data, "cabecera": rel_data.get("cabecera")}   # R11: firma/empleados intactos
# INFO si aplicada, WARNING si no: file, provider, model, motivo, resultado, error_tipo
meta = {"motivo": motivo, "provider": self._relectura_provider, "model": model,
        "resultado": resultado, "error_tipo": error_tipo}
```

- `_envelope` recibe `data: dict` y los dos bloques; solo si no son `None` añade
  `meta/debug["relectura_cabecera"]` (R18). Es la única captura amplia.
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

Nada más cambia (R22): `system` («Fechas: ... NO la conviertas ni reordenes» sigue valiendo:
juntar casillas en su orden no es reordenar), puntos 2–6 y `schema_hint`. Vale para la primaria
y la relectura: de ahí el banco MB (§10).

## 6. Configuración (`config/settings.py`)

```python
relectura_cabecera_enabled: bool = Field(True, alias="RELECTURA_CABECERA")
relectura_cabecera_provider: ProviderName = Field("gemini", alias="RELECTURA_CABECERA_PROVIDER")
obras_cache_ttl_s: int = Field(600, alias="OBRAS_CACHE_TTL_S")
# @property relectura_cabecera_motivo_inactiva -> str | None: None si apagada o activa; si
#   encendida e inactiva, por orden "mismo_proveedor", "no_habilitado", "sin_clave"
# @property relectura_cabecera_activa -> str | None: el proveedor si enabled y sin motivo
```

La clave se mira como en el validador (`strip()` no vacío), con un helper `_clave_de(provider)`
que usan los dos sin cambiar sus mensajes (R24). Sin variable de modelo propia (DA5).

## 7. Cableado (`interface_adapters/api/app.py`)

- `relectura = settings.relectura_cabecera_activa`; `sigrid_client` como hoy; `obras =
  ObrasSigrid(client=sigrid_client, ttl_seconds=settings.obras_cache_ttl_s)` solo con los dos,
  si no `None`; ambos al `ExtractPartePipeline`. `/health`: `"relectura_cabecera"` o `None`.
- Log `INFO "[partes-sv2][wiring] relectura cabecera ACTIVA provider=%s model=%s
  comprueba_obra=%s"`, `WARNING "... INACTIVA motivo=%s"` o `INFO "... DESACTIVADA"`.

## 8. Tests (sin red ni BBDD; `test_f058_rN_...`; fixtures inventadas, obra `"9999"`)

- `test_f058_relectura_cabecera.py`. Puros: `es_vacio`, `cabecera_vacia`, `clave_obra`
  (`"0672"`/`"00672"` → `"672"`, `"000"` → `"0"`, `" a-12 "` → `"A12"`, acento),
  `motivo_relectura` (con un `existe` doble que apunta llamadas) y `resultado_relectura`.
  Pipeline con un `FakeVisionClient(LlmVisionClient)` por proveedor (devuelve o lanza; guarda
  proveedor, `instructions` y adjunto), servicio, prompts y esquemas reales y dobles del
  catálogo y del puerto: R1, R3, R4, R6, R11–R18 y R19 (`caplog` sin nombre, DNI, obra, fecha
  ni mensaje de excepción).
- `test_f058_obras_sigrid.py`: carga perezosa, una por TTL (reloj falso), fallo o lista vacía
  sin reintentar (R7, R9); `fetch_codigos_obra` con `httpx.MockTransport` (`max_rows` 50.000,
  filas sin `None`, `truncated` ⇒ `RuntimeError`, R8); `fetch_tipos_hora` igual que hoy.
- `test_f058_prompt.py` (estilo F-051): el párrafo va entre el título del punto 1 y
  `- cabecera.fecha:` y nombra `"personal"`, `nº obra`, `dia`, `mes`, `año`, `membrete`,
  `desplazado`, `null` y `nunca inventes`; la viñeta de fecha, `casillas separadas` (R20, R21).
- `test_f058_settings_wiring.py`: `Settings(_env_file=None, ...)` (R23, R24); `build_app` con
  SDK falsos en `sys.modules` e import de `app.py` dentro del test: pipeline, `obras` con y sin
  `SIGRID_API_*`, logs y `/health` con `TestClient` (R25, R26).

## 9. Riesgos

- **Latencia, cola y coste**: una relectura suma ~8 s (7–11 s, una de 32 s) y ~7 k tokens;
  en el peor caso roza `COLA_VISIBILITY_S=600` (ya pasa hoy; sv3 descarta por `source_sha256`).
  La lista de obras: ~1–3 s en la primera página tras arrancar y una consulta por TTL.
- **Obra nueva dentro del TTL**: relee sin necesidad; si Gemini lee la misma, `no_casa` y se
  queda la primaria; solo si leyera otro código existente se tomaría su cabecera (sv3 sigue
  validando con membrete y trabajadores). Se acepta: TTL corto y caso preventivo.
- **Fecha** con `obra_inexistente`: si la releída trae obra sin fecha, se pierde la primaria y
  F-054 manda a revisión (DA11). **Prompt**: cambia todas las extracciones; puerta MB (DA9).

## 10. Verificación manual (humano o líder)

- **M0** (solo lectura): `az containerapp show -n ca-sv2-extraccion -g rg-partes-dev --query
  "properties.template.containers[0].env[?starts_with(name,'GEMINI_') || starts_with(name,
  'ENABLE_GEMINI') || starts_with(name,'SIGRID_API_')]" -o table` ⇒ Gemini con
  `gemini-4-argon`, claves por `secretRef`, base `ruesma`. Si no, decide el humano.
- **MB** (banco del prompt; **lo lanza el líder** tras el commit del prompt, con `lanzar.ps1` del
  scratchpad y `-Repo C:\Users\pgris\PycharmProjects\partes-wt-f058`, que lee el prompt de la
  rama, sin relectura): (a) `-Paginas paginas_sincab -Runs 2 openai:gpt-6.1-sol` ⇒ cuántas de
  12 traen obra y fecha, y si son las de Gemini (antes 0; se mide, no es puerta); (b)
  `paginas_control` con `gpt-6.1-sol` ⇒ como `control.jsonl`; (c) `paginas_sincab` con
  `gemini:gemini-4-argon` ⇒ 6 de 6; (d) batería de F-051 (`paginas`, 3 pasadas, `corregir.py`)
  ⇒ 42 de 42. Puerta: (b)–(d) sin regresión, o para y decide el humano. Va a `progress/banco_F-058.md`.
- **M1** (local, sin escrituras): script fuera del repo con `build_app(Settings())` (claves del
  KV solo en el proceso) sobre las dos carpetas, volcando por página motivo, resultado, si hay
  obra y fecha y filas, sin nombres ni DNIs ⇒ obra y fecha en las 6 (primaria o `aplicada`),
  filas iguales, control sin relectura e INFO `[obras-sigrid]`.
- **M2** (solo lectura, tras desplegar, READ ONLY): `SELECT j->>'motivo', j->>'resultado',
  count(*) FROM (SELECT raw_extraction_json::jsonb->'meta'->'relectura_cabecera' j FROM
  parte_documents WHERE created_at_utc >= '<FECHA_DESPLIEGUE>') s GROUP BY 1, 2;`.
- **M3** (DA8 = A): ningún agente escribe; Administración pone obra y fecha en el portal.

## 11. Decisiones

| DA | Tema | Estado y decisión |
|---|---|---|
| DA1 | Cuándo releer | **Enmendada y aprobada**: cabecera vacía (obra y fecha) **o** obra leída fuera de la lista de Sigrid, con ≥ 1 fila. Fecha sin obra no relee (F-054 la manda a revisión) |
| DA2–DA8 | Relectura, toma, fallo, configuración, traza, coste, los 6 guardados | Aprobadas, todas A: página entera con el mismo prompt y esquema; cabecera entera si es útil; si falla o no es útil, la primaria con traza y WARNING; `RELECTURA_CABECERA` encendida y `RELECTURA_CABECERA_PROVIDER=gemini` sin cambios de entorno; `meta`/`debug.relectura_cabecera` solo al releer; coste aceptado; los 6, a mano en el portal |
| DA9 | Prompt de cabecera | **Pedido por el humano**; texto de §5, solo el punto 1. Abierto: la puerta de MB (si (b)–(d) empeoran, se quita el párrafo y queda la relectura) |
| DA10 | Comprobación de existencia | **Abierta. Recomendada A**: lista de códigos cacheada (una consulta por TTL; `truncated` o 0 códigos = fallo; fallo = no releer por obra, sin bloquear). B) consulta por página: una llamada y un punto de fallo más en cada página. C) fallo = releer: Gemini en todas las páginas con Sigrid caído |
| DA11 | Cabecera con `obra_inexistente` | **Abierta. Recomendada A**: la releída entera si su obra está en la lista (como DA3). B) la releída con la fecha primaria si la releída no trae: mezcla dos lecturas de una cabecera ya dudosa |
