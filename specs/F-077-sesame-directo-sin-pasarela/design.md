<!-- specs/F-077-sesame-directo-sin-pasarela/design.md -->
# F-077 · Sesame HR directo, sin la pasarela — Diseño

**Rigor: `critico`** (DA4). Disparadores de `CHECKPOINTS.md`: **1** (dinero: los festivos que
guarda sv3 deciden en `RecursoConciliador` qué horas son ordinarias o extra) y **3** (seguridad:
un token de Sesame HR que probablemente permite escribir y un listado de empleados con DNI,
nombre y email). Encendido manual tras M0–M2 (§7).

## 1. Estado de partida (leído el 2026-11-18 en `2921cae`, solo lectura)

- **F-032 (done, sin desplegar).** `RefrescoFestivos` (sv3) pide por duck-typing
  `cliente.festivos(dni_norm, ano) -> list[FestivoDia] | None` (lista ⇒ upsert; `None` ⇒ sin
  fila; excepción o incompleto ⇒ conservar o revisión). El contrato **no cambia**; hoy lo da
  `SesameApiClient` (`x-api-key`, `/api/v1/festivos`), cableado en `api/app.py`.
- **sv4.** `CalendarioProvider` usa `cliente is None` como interruptor de la tabla y el cliente
  solo para `jornada_contrato` (badge «contrato:» y `jornada_divergente` de `trabajador_detail`,
  `web/app.py` ~:1215, plantilla :65–70), que nunca sale: Sesame HR no tiene contratos (0/218).
  Otro usuario: `validar_datos_sesame.py` (F-013). Es gemelo del de sv3 y `servicios.json` hace
  depender a sv3 de él (lo compara `test_f032_cliente_sesame`).
- **Referencia** (repo `sesame-api`, sin commitear, leído sin `.env`): `SesameHttpClient`
  (Bearer, `limit/page` + `meta.lastPage`, reintentos 429/5xx con `Retry-After` ≤ 30 s, 2
  reintentos) y `EmpleadoIndex` (`/core/v3/employees`, `status[in]=active,inactive`, duplicado ⇒
  el activo, TTL); `/api/v1/festivos` da **404 si el DNI no está**. **Formato**: cada fila de
  `/schedule/v1/holidays` trae `dayOff` (`date`, `name`); `daysOff` es de `/holiday-calendar`
  (la descripción de F-077 los mezcla; la spec sigue el código, R7–R8).
- **No se copia de la referencia**: el 404 o la página vacía a mitad que corta el listado **en
  silencio** (índice parcial ⇒ DNIs «no encontrados» sin revisión), `float(Retry-After)` que
  revienta con una fecha HTTP y los `RuntimeError` con `r.text` o la URL. Su
  `test_start_time_entry.py` indica que el token escribe.

## 2. Límite de servicio y trabajo fuera del repositorio

**sv3** es el único que llama a Sesame HR: cliente, índice y herramienta (DA1). **sv4** deja
de llamar a Sesame y solo lee `festivos_trabajador` con su interruptor (DA10). Sin lógica nueva
duplicada: los clientes `infrastructure/sesame/` **dejan de ser gemelos** (sv4 pierde el suyo)
y salen de la lista cerrada; `festivos_guardados.py` sigue gemelo. **sesame-api** no se toca y
partes deja de depender de él (DA2). Humano: token, Key Vault y Azure (§7).

## 3. Ficheros a crear

| Ruta | Contenido |
|---|---|
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py` | §5.1 |
| `services/partes-persistencia/infrastructure/sesame/festivos_sesame_hr.py` | §5.2 |
| `services/partes-persistencia/tests/test_f077_{cliente_hr,festivos_hr,wiring,ingesta_hr,logs_sin_datos,contraste}.py` | R1–R19, R24–R26 |
| `services/partes-front/tests/test_f077_sin_sesame_sv4.py` | R20–R22 |
| `tests/test_f077_{sin_pasarela,infra_sesame}.py` | R9 (estático), R20, R23, R31, R33 (lista y `servicios.json`); R27–R30 |

## 4. Ficheros a modificar y a retirar

- **sv3**: `config/settings.py`, `interface_adapters/api/app.py` (§5.3), `contrastar_festivos_
  sesame.py` (§5.5); solo docstrings en `refresco_festivos.py`, `persist_parte_pipeline.py`,
  `tabla_calendario_laboral.py`, `logging_config.py`. **Se retira** `sesame_api_client.py`.
- **sv4**: `config/settings.py`, `application/services/calendario_provider.py`,
  `interface_adapters/web/app.py`, `templates/trabajador_detail.html` y, si quedan muertas, las
  reglas `.jornada-contrato`/divergencia de `static/styles.css` (§5.4). **Se retiran**
  `infrastructure/sesame/` entero y `validar_datos_sesame.py` (DA9).
- **infra**: `add_sesame_partes.ps1`, `create_capps_partes.ps1`, `create_sv4_front.ps1`,
  `add_secrets_partes.ps1`, `00_vars_partes.ps1` (§5.6), `README_partes.md`.
- **Raíz y docs**: `CLAUDE.md` (fuera de la lista cerrada los clientes `infrastructure/sesame/`),
  `harness/servicios.json` (sv3 sin `depende_de` del cliente de sv4), `docs/ARCHITECTURE.md`,
  `README.md` (`SESAME-TOKEN`) y `azure-apps/partes.md` (§8). `features.json`: el líder.
- **Tests existentes que cambian (lista CERRADA; si cae otro, PARAR y volver a la spec):**
  - sv3, se retiran: `test_f032_cliente_sesame.py` (cliente viejo y su comparación con sv4) y
    `test_f032_logs_sin_dni.py` (lo sustituye `test_f077_logs_sin_datos.py`). Se reescribe
    `fixtures_sesame.py` con respuestas de Sesame HR **ficticias** (forma de §1).
  - sv3, se adaptan: `test_f032_wiring.py` y `test_f003_r10_wiring_sv3.py` (nombres de
    variables y `SesameHrClient`), `test_f032_refresco.py` (import de `FestivoDia`),
    `test_f032_contraste.py` y `test_f032_campana.py` (sin `--api-key`, token por entorno,
    `https://`, calendarios en formato Sesame HR).
  - sv4, se retiran: `test_f003_r1_sesame_client.py`, `test_f003_r13_jornada_contrato.py`,
    `test_f013_informe_sesame.py` y `fixtures_sesame.py`.
  - sv4, se adaptan: `test_f003_r4_calendario_provider.py`, `test_f003_r16_api_calendario.py`,
    `test_f003_r23_bloqueo_registro.py`, `test_f032_avisos.py`, `test_f032_provider_tabla.py`
    (`cliente=` ⇒ `activo=`; fuera `ClienteSoloJornada` y los casos de jornada),
    `test_f003_r7_wiring.py` y `test_f032_wiring_sv4.py` (`FESTIVOS_SESAME_ENABLED`) y
    `test_f032_logs_sin_dni.py` (quedan solo los de `httpx` en WARNING).
  - Raíz, se retira `tests/test_f032_infra_sesame.py` (lo sustituye `test_f077_infra_sesame.py`).
  - No cambian `test_f016_vista_admin_jornadas.py` (sv4 conserva `sesame_enabled`), ni
    `test_f003_r2_vistas_festivos.py` y `test_f015_r24_avisos.py` (su `jornada_contrato` sobra).

## 5. Clases y funciones

### 5.1 `SesameHrClient` (sv3, infrastructure, `sesame_hr_client.py`)

```python
RUTA_EMPLEADOS = "/core/v3/employees"; RUTA_FESTIVOS = "/schedule/v1/holidays"
RUTA_CALENDARIOS = "/schedule/v1/holiday-calendar"
class SesameNoDisponible(RuntimeError): ...       # red, 429/5xx agotados, 401/403/4xx
@dataclass(frozen=True) class FestivoDia: fecha: str; nombre: str | None   # mismo de F-032
@dataclass(frozen=True) class EmpleadoSesame: id: str; dni_norm: str; activo: bool
@dataclass(frozen=True) class CalendarioSesame: id: str; nombre: str | None; por_defecto: bool;
                                                festivos: tuple[FestivoDia, ...]
class SesameHrClient:
    def __init__(self, *, base_url: str, token: str, timeout_s: float = 10.0,
                 page_size: int = 100, max_reintentos: int = 2, tope_filas: int = 20_000,
                 transport: httpx.BaseTransport | None = None,
                 dormir: Callable[[float], None] = time.sleep) -> None
    def empleados(self) -> list[EmpleadoSesame]                        # R6
    def festivos_de_empleado(self, employee_id: str, ano: int) -> list[FestivoDia]   # R7
    def calendarios_festivos(self) -> list[CalendarioSesame]           # R8
```
- Constructor: `ValueError` si `base_url` no empieza por `https://` o el token está en blanco.
  Log INFO `[sesame-hr] Instanciado base_url=… token_len=… timeout_s=…`.
- `_get(ruta, params) -> dict | None` (privado): un `client.get` por intento sobre
  `httpx.Client(timeout, transport, headers)`; 404 ⇒ `None`; 429/5xx y red ⇒ reintento (R3,
  `float(Retry-After)` en `try`); 401/403/otro 4xx ⇒ `SesameNoDisponible`; JSON inválido ⇒
  `RuntimeError`. Mensajes (R5) `sesame HTTP {status} en {ruta}` / `sesame red en {ruta}:
  {tipo}`, con `from None`. El WARNING de reintento: ruta, estado y espera.
- `_paginado(ruta, params) -> list[dict]` (R2): `None` en cualquier página o página vacía con
  `page < lastPage` ⇒ `RuntimeError`; tope ⇒ `RuntimeError`.
- `empleados()`: `normalize_dni` de `application.services.text_match` sobre `nid` (DA5);
  `activo = status == "active"`; el resto de campos de la fila no sale de la función.
- Ningún otro método público. Sin `post`, `put`, `patch`, `delete`, `request`, `send` ni
  `stream` en el módulo (R9; lo mira el guardián por AST).

### 5.2 `FestivosSesameHr` (sv3, infrastructure, `festivos_sesame_hr.py`)

```python
class FestivosSesameHr:
    def __init__(self, *, cliente: SesameHrClient, ttl_indice_s: float = 600,
                 corte_s: float = 60, reloj: Callable[[], float] = time.monotonic) -> None
    def festivos(self, dni: str | None, ano: int) -> list[FestivoDia] | None   # R10
```
Orden de `festivos`: `normalize_dni`; vacío ⇒ `None` (sin red). En corte ⇒ `SesameNoDisponible
("corte")`. Índice vigente o reconstruido (R11): `dict[dni_norm, EmpleadoSesame]` con la regla
de R12 y log `[sesame-hr] indice empleados=… duplicados=… sin_dni=…`; 0 empleados o cualquier
excepción del listado ⇒ no se guarda, se abre el corte y sube `SesameNoDisponible` (R13–R14).
DNI ausente ⇒ `None` (DA6). Presente ⇒ `cliente.festivos_de_empleado(id, ano)`; si lanza
`SesameNoDisponible`, abre el corte y relanza; otro `RuntimeError` (404, cuerpo) se relanza sin
corte. `threading.Lock` alrededor del índice y del corte. Nada a disco (R19).

### 5.3 sv3: configuración y cableado

- `config/settings.py`: `sesame_api_*` ⇒ `sesame_base_url` (`SESAME_BASE_URL`), `sesame_token`
  (`SESAME_TOKEN`), `sesame_timeout_s` (`SESAME_TIMEOUT_S`, 10, `gt=0`), con `field_validator`
  que rechaza una URL sin `https://` (R16). `sesame_festivos_minimos` y `sesame_enabled` (URL +
  token) conservan su nombre.
- `api/app.py`: `construir_refresco_festivos` da a `RefrescoFestivos` como `cliente` un
  `FestivosSesameHr(cliente=SesameHrClient(...))`; los logs pasan a R17. `build_app`, igual.

### 5.4 sv4: sin Sesame (DA9, DA10)

- `config/settings.py`: fuera el bloque `SESAME_API_*` y `SESAME_CACHE_TTL_S`; entra
  `festivos_sesame_enabled: bool = Field(False, alias="FESTIVOS_SESAME_ENABLED")`; la propiedad
  `sesame_enabled` devuelve ese valor (mismo nombre: `test_f016` no cambia).
- `CalendarioProvider(*, activo: bool = False, respaldo_holiday_name, reloj=time.time,
  leer_festivos=None, ttl_tabla_s=60)`: `activo` sustituye a `cliente is None` en `_resolver`,
  `fiable_para` y la propiedad `activo`. Fuera `cliente`, `ttl_seconds`, `jornada_contrato`,
  `_cache`, `_de_cache`, `_a_cache` y el import del cliente. La cascada de la tabla, intacta.
- `web/app.py::build_app`: `CalendarioProvider(activo=settings.sesame_enabled, ...)`, log
  `[sesame][wiring] CABLEADO festivos=tabla (sv4 no llama a Sesame)` o `DESACTIVADO
  (FESTIVOS_SESAME_ENABLED=false)`. `trabajador_detail`: fuera `jornada_contrato` y
  `jornada_divergente` del contexto; la plantilla pierde el badge y el aviso (R22).

### 5.5 `contrastar_festivos_sesame.py` (consola, sv3)

`listar_calendarios(cliente: SesameHrClient) -> list[dict]` convierte cada `CalendarioSesame` a
la forma que ya consume `contrastar_calendario` (`id`, `nombre`, `por_defecto`, `festivos:
[{fecha, nombre}]`): las puras de F-032 no cambian. `_festivos_por_dni` recibe un
`FestivosSesameHr`. `main(argv, *, ahora, transport, repositorio, pedir_token=getpass.getpass)`:
URL de `--base-url` > settings > `SESAME_BASE_URL`; token de settings > `SESAME_TOKEN` >
`pedir_token("Token de Sesame HR: ")`; fuera `--api-key`; `https://` obligatorio (R25). La
salida de listado fallido captura `RuntimeError` (incluye `SesameNoDisponible`).

### 5.6 `infra/` (PowerShell 5.1, CRLF, sin BOM)

- `add_sesame_partes.ps1` (mismo esqueleto y `[-Quitar]`): valida R28 antes del primer
  `containerapp`. Por app, `Get-EnvNames` (`az containerapp show --query "properties.template.
  containers[0].env[].name" -o tsv`); las retiradas presentes salen en un `update
  --remove-env-vars` **previo** y, si existe, `secret remove --secret-names sesame-key`. Luego
  sv3: `secret set sesame-token=keyvaultref:$KV_URI/secrets/SESAME-TOKEN,identityref:$MI_ID` y
  `update --set-env-vars` de R27; sv4, solo `FESTIVOS_SESAME_ENABLED=true`. `-Quitar`: las
  presentes de R29 (`sesame-token` queda inerte).
- `create_capps_partes.ps1` (sv3) y `create_sv4_front.ps1` (sv4): sus bloques `if
  ($SESAME_BASE_URL)` pasan a lo de R27. `add_secrets_partes.ps1`: `SESAME-TOKEN` («token de la
  API de Sesame HR, Bearer, solo sv3; rotado y, si Sesame lo permite, de solo lectura») en vez
  de `SESAME-API-KEY`. `00_vars_partes.ps1`: comentarios nuevos, `$SESAME_BASE_URL = ""` (DA13).
  La URL pública de la región va en `00_vars_partes.local.ps1` y la nombra `README_partes.md`.

## 6. Ficheros que NO se tocan

`congelacion.py`, `recurso_conciliador.py` (`esta_congelado`), `festivos_guardados.py` (sv3 y
sv4), los dos `orm_models.py`, `sqlalchemy_festivos_repository.py`, `json_calendario_laboral.py`,
`calendario_laboral.json`, `holiday_provider.py`, `jornada_resolver.py` (sv3 y sv4, aunque su
docstring nombre la pasarela), `parte_repository.py`, `redeploy_*.ps1`, sv1, sv2, sv5, el repo
`sesame-api` y cualquier `.env`.

## 7. Guía de despliegue y verificación manual (humano)

Sustituye a M1–M7 y P0–P4 de F-032 (T28–T30 de F-032 quedan sin objeto; P5, RRHH, sigue). Cada
M va a `progress/impl_F-077.md` con su comando y su resultado real.
- **M0**: **rotar el token** de Sesame HR (el `.env` de sesame-api estuvo en git) y, si Sesame
  lo permite, **de solo lectura**; `.\infra\add_secrets_partes.ps1` (`SESAME-TOKEN`); en local,
  `SESAME_BASE_URL`/`SESAME_TOKEN` en el `.env` de sv3 y fuera `SESAME_API_*` de sv3 y sv4.
- **M1 (puerta DA12 de F-032)**: en `services/partes-persistencia`, `python
  contrastar_festivos_sesame.py --ano 2026` (y 2025 si hay partes activos). `FALTAN DEL
  RESPALDO` ⇒ no se enciende; `INCOMPLETO` ⇒ RRHH (P5).
- **M2**: lo mismo con `--impacto`; revisar `dura` y días mixtos.
- **M3**: `.\infra\redeploy_partes.ps1 -Solo sv3,sv4`; los dos logs dicen `DESACTIVADO`.
- **M4**, fuera del horario de aprobación: `$SESAME_BASE_URL` en el `.local` y
  `.\infra\add_sesame_partes.ps1`; `CABLEADO` en los dos; con el siguiente parte, `[sesame-hr]
  indice …` y `[festivos] refresco …` en sv3 y ningún DNI en `az containerapp logs show -n
  ca-sv3-persistencia -g $RG --tail 300 | Select-String -Pattern '\b[0-9XYZ][0-9]{7}[A-Z]\b'`.
- **M5**: portal: un trabajador con fila sin aviso; uno sin fila, aviso y registro que pasa;
  la vista de trabajador, sin badge «contrato:».
- **M6**: `.\infra\add_sesame_partes.ps1 -Quitar` ⇒ `DESACTIVADO`; volver a encender.

## 8. Frontera

¿Cruza la frontera del proyecto? **Sí.** sv3 consume la **API pública de Sesame HR** (SaaS,
HTTPS de salida desde `cae-partes-dev`: `/core/v3/employees`, `/schedule/v1/holidays`; la
herramienta, `/schedule/v1/holiday-calendar`) y partes **deja de consumir `sesame-api`** (nunca
desplegada). Variables: sv3 `SESAME_BASE_URL`, `SESAME_TOKEN` (secretref `sesame-token`) y
`SESAME_TIMEOUT_S`; sv4 `FESTIVOS_SESAME_ENABLED`; secreto `SESAME-TOKEN` por `SESAME-API-KEY`.
La tabla no cambia. Se actualiza `azure-apps/partes.md` (§3.4, §4.6, §4.7, §5.3, §5.3 bis como
«Consumo de Sesame HR», filas de variables de sv3 y sv4, §8), con `pull --rebase` y commit aparte.

## 9. Decisiones

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| DA1 Quién llama a Sesame | (A) solo sv3; sv4 lee la tabla y no llama | (A) | (A) 2026-11-18 |
| DA2 sesame-api | (A) no se toca; partes deja de depender | (A) | (A) 2026-11-18 |
| DA3 Índice DNI → empleado | (A) en memoria de sv3, TTL ~10 min, sin tabla | (A) | (A) 2026-11-18 |
| DA4 Rigor | (A) crítico | (A) | (A) 2026-11-18 |
| DA5 Normalización del DNI del índice | (A) `normalize_dni` de sv3, la de `dni_norm` y del pipeline; (B) `norm_dni` de sesame-api (igual para DNI/NIE salvo tildes) | (A) | |
| DA6 «No encontrado» | (A) DNI ausente de un índice bien cargado ⇒ `None` (sin fila, sin revisión); 404 de festivos de un empleado conocido ⇒ fallo; (B) los dos ⇒ `None` | (A) | |
| DA7 Inactivos en el índice | (A) activos e inactivos, duplicado ⇒ el activo (como sesame-api); (B) solo activos | (A) | |
| DA8 Índice fallido a mitad | (A) todo o nada: no se guarda, fallo para el (DNI, año) y corte de 60 s sin red; (B) índice parcial, como sesame-api | (A) | |
| DA9 Cliente de sv4 y su configuración | (A) quitar: `infrastructure/sesame/`, `SESAME_API_*`, `SESAME_CACHE_TTL_S`, `jornada_contrato` con su badge y `validar_datos_sesame.py`; (B) dejarlo muerto | (A) | |
| DA10 Interruptor de la tabla en sv4 | (A) `FESTIVOS_SESAME_ENABLED` (defecto `false`), lo fija el script; (B) leer siempre la tabla; (C) conservar `SESAME_API_*` solo como interruptor | (A) | |
| DA11 Nombres | (A) `SESAME_BASE_URL`, `SESAME_TOKEN`, `SESAME_TIMEOUT_S`, `SESAME_FESTIVOS_MINIMOS`; secreto `SESAME-TOKEN` (KV) / `sesame-token` (app); (B) conservar `SESAME_API_TIMEOUT_S` | (A) | |
| DA12 Token en la herramienta | (A) solo entorno/`.env` o consola sin eco; sin `--token`; (B) `--token` como F-032 | (A) | |
| DA13 URL en la infra versionada | (A) `$SESAME_BASE_URL` vacía en `00_vars`, valor en el `.local`; (B) versionar la URL pública | (A) | |
| DA14 Solo HTTPS | (A) sv3 y la herramienta rechazan una URL sin `https://`; (B) aceptar http | (A) | |

## 10. Riesgos y alternativas descartadas

- **Token con escritura**: un solo `get` en el módulo (guardián AST) y `MockTransport` que
  rechaza otros métodos; rotación y solo lectura, M0.
- **Índice desfasado**: un alta tarda ≤ 10 min en verse; su parte va al respaldo sin revisión
  y el siguiente lo corrige (R38 de F-032). Un inactivo cuya consulta falle y sin fila manda
  su parte a revisión, como con la pasarela.
- **Caída de Sesame**: la primera llamada tarda hasta ~1,5 min (plazo × 3 + esperas); el corte
  hace fallar al instante el resto del parte (R8 de F-032). **Sin caché de festivos** (la
  pasarela la tenía): ~20 llamadas por parte, y cada ingesta lee lo último de RRHH.
- **Descartados**: portar la pasarela (DA2), índice persistido (DA3) y los defectos de §1.
