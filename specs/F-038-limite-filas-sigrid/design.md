<!-- specs/F-038-limite-filas-sigrid/design.md -->
# F-038 · Límite de filas de las lecturas de Sigrid — diseño

> Requisitos en `requirements.md`. Rama `feature/F-038-limite-filas-sigrid` desde
> `dev` 0926857. Rigor `estandar`. DA1–DA7 en §7, **pendientes del humano**.

## 1. Inventario de lecturas de Sigrid (dev 0926857)

Todas pasan por `POST /api/sql/read`. «Silencio» = puede devolver filas parciales
sin avisar. Las paginadas piden 5.000 por página con `max_rows` 5.001.

| Serv. | Lectura (método) | `max_rows` hoy | `truncated` | Pagina | Silencio | Tamaño real |
|---|---|---|---|---|---|---|
| sv2 | `SigridLookupClient.fetch_tipos_hora` (`auxhor` activos) | 10.000 fijo (sin variable) | **no** | no | **sí** | decenas |
| sv3 | `fetch_empleados`, `fetch_obras`, `fetch_tipos_hora`, `fetch_empresas`, `fetch_recursos`, `fetch_reshor` | 5.001 | error | sí | no | maestros completos |
| sv3 | `fetch_partidas_obra(obra)`, `fetch_hmo_obra(obra)` | 5.001 | error | sí | no | partidas / partes de una obra |
| sv3 | `_post_sql_read` sin `max_rows` (usa `SIGRID_API_MAX_ROWS` 10.000) | — | — | — | — | **ningún llamador** |
| sv4 | `fetch_tipos_hora`, `fetch_obras`, `fetch_empleados`, `fetch_recursos_activos`, `fetch_partidas_obra` | 5.001 | error | sí | no | catálogos / partidas de la obra |
| sv4 | `fetch_dnis_sin_extra(dnis)` | 10.000 fijo | error | no | no | ≤ nº de DNI (agregado) |
| sv4 | `fetch_hora_extra_recurso(reside)` | 10.000 fijo | error | no | no | `TOP 1` |
| sv4 | `consulta_reshor_recursos.py` (script manual) | 10.000 literal | **no** | no | **sí** | por DNI |
| sv5 | `_read` → `obra_por_codigo`, `obra_por_ide`, `siguiente_cod_pt`, `max_pos` | 1.000 fijo | error | no | no | 1 fila / agregado |
| sv5 | `_read` → `datos_recursos` (lotes 500), `lineas_por_synckey`, `lineas_por_ide`, `partes_por_ide`, `lineas_para_reajuste`, `estados_de_partes` (lotes 200) | 1.000 fijo | error | lotes | no | ≤ 1 fila por id |
| sv5 | `_read` → `partes_existentes`, `partes_del_periodo`, `cuentas_de_centro`, `partidas_de_lineas` | 1.000 fijo | error | no | no | pocas filas |
| sv5 | `_read` → `recursos_por_dni`, `horas_de_recursos`, **`lineas_existentes`** | 1.000 fijo | error | **no, ni lotes** | no | **puede pasar de 1.000** (líneas de un parte mensual; horas × recursos) ⇒ hoy el registro falla |
| sv5 | `comprobar_asiento_analitico.py` (usa `_read`) | 1.000 | error | no | no | agregados |
| sv5 | `prueba_escritura_sigrid.py` (script de pruebas en la 0404) | 1.000 literal | **no** | no | **sí** | pequeñas |

Conclusiones: (1) la queja de `porcentajes` (partidas de obras grandes) **no se
reproduce en partes**: sv3 y sv4 paginan las partidas y sv5 las lee por `ide`;
(2) en el pipeline nada trunca en silencio salvo sv2; (3) el riesgo real es de
**fallo ruidoso** en sv5 (tope 1.000 en lecturas sin lote); (4) las demás «subidas»
son de coherencia (10.000 → 200.000) y no cambian el comportamiento observable.
M1 (§9) mide cuánto margen había.

## 2. Encaje y límite de servicio

Cada servicio cambia **solo su propio cliente y su settings**; no se comparte
código (el cliente de sv3/sv4 ya está en la lista cerrada de duplicación tolerada
de `CLAUDE.md`; sv2 y sv5 tienen el suyo). La constante 200.000 se repite por
servicio a propósito: es configuración, no lógica. La regla «`truncated` = error»
y el inventario los vigila un guardián de raíz (§6), no una copia de código.
Ninguna responsabilidad nueva: no hay nada que extraer a otro microservicio.

## 3. Ficheros a modificar

- **sv2** `services/partes-api/`:
  - `config/settings.py`: `sigrid_api_max_rows: int = Field(200_000,
    alias="SIGRID_API_MAX_ROWS", ge=1, le=500_000)`; `sigrid_api_timeout_s` gana
    `gt=0, le=200`.
  - `infrastructure/sigrid/sigrid_lookup_client.py`: `MAX_ROWS_DEFECTO = 200_000`;
    constructor `max_rows: int = MAX_ROWS_DEFECTO`; log de instanciación con
    `max_rows` y `timeout_s` (R6); en `_post_sql_read`, tras `ok`, `if
    body.get("truncated"): raise RuntimeError(f"sigrid-api devolvio una respuesta
    truncada [{label}]")` (mismo texto que sv3/sv4).
  - `interface_adapters/api/app.py`: `max_rows=settings.sigrid_api_max_rows`.
  - `application/services/auxhor_catalog_provider.py`: **no cambia**; su `except`
    ya degrada a caché/vacío con WARNING (R8 solo se fija con test).
- **sv3** `services/partes-persistencia/`:
  - `config/settings.py`: `sigrid_api_max_rows` 10.000 → 200.000 con `ge=1,
    le=500_000`; `sigrid_api_timeout_s` con `gt=0, le=200`.
  - `infrastructure/sigrid/sigrid_api_client.py`: `MAX_ROWS_DEFECTO = 200_000` y
    constructor con ese defecto. `PAGINA_FILAS` y `_leer_paginado` no cambian.
- **sv4** `services/partes-front/`:
  - `config/settings.py`: `sigrid_api_max_rows` nuevo (como sv2) y
    `sigrid_api_timeout_s` con `gt=0, le=200`.
  - `infrastructure/sigrid/sigrid_lookup_client.py`: `MAX_ROWS_DEFECTO`, defecto
    del constructor, log con `max_rows` y `timeout_s`.
  - `interface_adapters/web/app.py` (construcción de `SigridLookupClient`, ~l.482):
    `max_rows=settings.sigrid_api_max_rows`.
  - `tests/test_f023_catalogo_empresa.py` l.169: `== 10000` → `== 200000`
    (**enmienda** de un test antiguo, citarla en el informe).
- **sv5** `services/partes-transfer/`:
  - `config/settings.py`: `sigrid_api_max_rows` nuevo y `sigrid_api_timeout_s`
    con `gt=0, le=200`.
  - `infrastructure/sigrid/sigrid_write_client.py`: `MAX_ROWS_DEFECTO = 200_000`;
    constructor gana `max_rows: int = MAX_ROWS_DEFECTO` (último parámetro con
    nombre) y `logger.info` de instanciación; `_read` manda `"max_rows":
    self._max_rows`. **Nada más del fichero** (lecturas, sentencias, docstring de
    cabecera solo en la frase «Todas las lecturas...» si se quiere citar F-038).
  - `interface_adapters/api/app.py` (`_cliente_sigrid`), `main.py` y
    `comprobar_asiento_analitico.py`: pasan `max_rows=settings.sigrid_api_max_rows`.
  - `prueba_escritura_sigrid.py`: `"max_rows": MAX_ROWS` con `MAX_ROWS = 200_000`
    y, tras `ok`, `if body.get("truncated"): raise SystemExit("sql/read: respuesta
    truncada ...")` (R10). Nada más.
  - `tests/test_f024_comprobacion.py` l.274 y l.304: `== 1000` → `== 200000`
    (**enmienda**).
- **Docs**: `docs/ARCHITECTURE.md` «Acceso a datos y sistemas externos» (hoy dice
  «máx. 1.000 filas por petición», desfasado): tope 500.000 de la instancia;
  partes pagina los listados a 5.000 y el resto pide `SIGRID_API_MAX_ROWS`
  (200.000); `truncated` = error; timeout ≤ 200 s. Con DA6 = A, quitar la entrada
  de `consulta_reshor_recursos.py` (l.589).
  `C:\Users\pgris\PycharmProjects\azure-apps\partes.md`: §3.3 (frase de
  paginación: añadir el límite de las no paginadas) y §5.6, filas sv2–sv5:
  `SIGRID_API_MAX_ROWS` opcional (200.000, 1–500.000) y rango de
  `SIGRID_API_TIMEOUT_S`. Commit local en ese repositorio, sin push.

## 4. Ficheros a crear / borrar

- Crear `tests/test_f038_lectores_sigrid.py` (raíz, guardián, §6).
- Crear `services/partes-api/tests/test_f038_sigrid_limite.py`,
  `services/partes-persistencia/tests/test_f038_sigrid_limite.py`,
  `services/partes-front/tests/test_f038_sigrid_limite.py`,
  `services/partes-transfer/tests/test_f038_sigrid_limite.py` (§10).
- Borrar `services/partes-front/consulta_reshor_recursos.py` (solo con DA6 = A).

## 5. Ficheros que NO se tocan

- `_leer_paginado` y `PAGINA_FILAS` de sv3 y sv4 (DA5), ni sus SQL.
- Todas las lecturas y sentencias de `sigrid_write_client.py` salvo `__init__` y
  `_read`; `escribir`/`escribir_lote` (escritura, otro tope: `MAX_AFFECTED_ROWS`).
- sv4 `infrastructure/database/parte_repository.py` (no lee Sigrid), `tests/dobles.py`
  de sv5, `infra/` (la variable es opcional, no va a manifiestos: DA2),
  `orm_models.py`, sv1.
- `services/partes-persistencia/medir_casado_recursos.py`: ya pasa
  `settings.sigrid_api_max_rows` (R5 se comprueba, no se cambia).

## 6. Guardián de lectores (`tests/test_f038_lectores_sigrid.py`)

Recorre `services/*/**/*.py` excluyendo carpetas `tests/` y `.venv`; parsea con
`ast`. Un **lector** es un fichero con una constante de cadena (incluidas las
partes de un f-string) que contiene `/api/sql/read` y **no** es docstring de
módulo, clase o función. Lista cerrada esperada (DA6 = A):

```
services/partes-api/infrastructure/sigrid/sigrid_lookup_client.py
services/partes-persistencia/infrastructure/sigrid/sigrid_api_client.py
services/partes-front/infrastructure/sigrid/sigrid_lookup_client.py
services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py
services/partes-transfer/prueba_escritura_sigrid.py
```

(con DA6 = B, más `services/partes-front/consulta_reshor_recursos.py`).
Comprobaciones: R11 conjunto igual (mensaje con los sobrantes y los que faltan);
R12 hay una `ast.Call` a atributo `get` con primer argumento la constante
`"truncated"`; R13 ningún `ast.Constant` entero < 200.000 como valor de la clave
`"max_rows"` en un `ast.Dict`, de un `keyword` `max_rows` ni como defecto de un
argumento `max_rows`. `PAGINA_FILAS + 1` es un `BinOp` y no cuenta. Prueba de
verdad del guardián: un test con código sintético (cadena) que viola R12 y otro
que viola R13 y hacen fallar las funciones de comprobación.

## 7. Decisiones abiertas (pendientes del humano; recomendación: A en todas)

- **DA1 · Valor por defecto.** A: 200.000 (lo pedido; 40 % del tope de la
  instancia). B: 500.000 (el tope). C: un valor por lectura. Recomendada A: el
  tope de filas no es el que manda (manda el corte de 230 s) y ninguna lectura no
  paginada se acerca.
- **DA2 · Variable.** A: `SIGRID_API_MAX_ROWS` **opcional** en sv2–sv5 (mismo
  nombre que ya tiene sv3), defecto en código, fuera de manifiestos y de `infra/`;
  rango 1–500.000 con arranque fallido fuera de él. B: obligatoria y fijada en los
  manifiestos. Recomendada A: cero cambios en Azure para desplegar.
- **DA3 · `truncated`.** A: error siempre, también en los scripts; en sv2 el error
  lo absorbe el proveedor del catálogo como cualquier fallo de Sigrid (caché o
  vacío + WARNING) y la extracción sigue sin catálogo. B: en sv2, que el fallo
  tumbe la extracción del parte. Recomendada A: el catálogo es una ayuda a la IA,
  no un dato que se persista.
- **DA4 · Timeouts frente a 230 s.** A: validar `0 < SIGRID_API_TIMEOUT_S ≤ 200`
  en los cuatro (sv5 suma 30 s al plazo HTTP ⇒ ≤ 230); defectos sin cambio (30,
  30, 30, 60). B: solo documentarlo. Recomendada A. Riesgo: si en Azure hubiera
  un valor > 200, el servicio no arrancaría; M0 (§9) lo comprueba antes.
- **DA5 · Tamaño de página.** A: `PAGINA_FILAS` sigue en 5.000. B: subirlo
  (p. ej. 50.000) para hacer menos peticiones. Recomendada A: cada página tarda
  poco y una página grande se acerca a los 230 s sin ganar nada.
- **DA6 · `consulta_reshor_recursos.py` (sv4).** Diagnóstico manual obsoleto: lee
  el `.env` del repositorio archivado `partes-front`, replica la consulta de
  `fetch_dnis_sin_extra` y **lleva DNIs y nombres reales en claro** en el código.
  A: borrarlo (y su línea de `ARCHITECTURE.md`). B: arreglarlo (`truncated` +
  `max_rows`) y sustituir los datos por un argumento. Recomendada A. Borrarlo **no**
  limpia el historial de git: si se quiere purgar, es decisión aparte del humano.
- **DA7 · Lecturas de sv5 con `IN` sin lote** (`recursos_por_dni`,
  `horas_de_recursos`, `lineas_existentes`, `partidas_de_lineas`,
  `cuentas_de_centro`). Con 200.000 dejan de fallar por filas; el límite de ~2.100
  parámetros de SQL Server sigue ahí. A: fuera de alcance; si M1 lo justifica, se
  propone una feature. B: trocearlas aquí. Recomendada A.

## 8. Choque con F-060 (en curso en `partes-wt-f060`)

F-060 toca en sv5 `sigrid_write_client.py` (añade `lineas_de_racha`, que lee por
`_read`, y `stmt_mover_linea`), `config/settings.py` (`MOVER_CIZ`),
`interface_adapters/api/app.py` (`LineaIn`) y la fila sv5 de
`azure-apps/partes.md` §5.6; en sv4 `parte_repository.py` (F-038 no lo toca).
F-038 cambia en esos ficheros solo `__init__`/`_read`, dos campos de settings,
`_cliente_sigrid` y la fila sv5: trozos distintos, conflicto textual probable
solo en `partes.md` §5.6. La lectura nueva de F-060 hereda el límite y el
guardián sin cambios (mismo fichero lector). **Recomendación**: implementar F-038
después de mezclar F-060 en `dev` (rebase de esta rama); si no, quien mezcle
segundo resuelve la fila sv5 de `partes.md` uniendo las dos frases.

## 9. Verificación manual (solo lectura)

- **M0 (humano, antes de desplegar)**: que ningún servicio tenga en Azure un
  `SIGRID_API_TIMEOUT_S` > 200 ni un `SIGRID_API_MAX_ROWS` fuera de rango. Para
  cada app (`ca-sv2-extraccion`, `ca-sv3-persistencia`, `ca-sv4-front`,
  `ca-sv5-transfer`):
  `az containerapp show -n <app> -g rg-partes-dev --query "properties.template.containers[0].env[?name=='SIGRID_API_TIMEOUT_S' || name=='SIGRID_API_MAX_ROWS'].{n:name,v:value}" -o table`
  Esperado (por `infra/`): sv4 30, sv5 60, el resto sin definir.
- **M1 (humano o líder, cuando se quiera; no bloquea)**: tamaños reales, sin
  nombres. Desde `services/partes-persistencia` (con su `.env`):
  `../../.venv/Scripts/python.exe -c "from config.settings import Settings as S; from infrastructure.sigrid.sigrid_api_client import SigridApiClient as C; s=S(); c=C(base_url=s.sigrid_api_base_url, function_key=s.sigrid_api_function_key, database=s.sigrid_api_database, timeout_s=120); print(c._post_sql_read(sql='<SQL>', parameters=[], label='m1', max_rows=10))"`
  con cada `<SQL>`:
  (a) `SELECT TOP 5 obride, COUNT(*) AS n FROM obrparpar GROUP BY obride ORDER BY COUNT(*) DESC`
  (partidas de las obras más grandes: páginas de sv3/sv4);
  (b) `SELECT TOP 5 hmoide, COUNT(*) AS n FROM hmores GROUP BY hmoide ORDER BY COUNT(*) DESC`
  (líneas del parte más grande: cota de `lineas_existentes`);
  (c) `SELECT MAX(n) AS m FROM (SELECT reside, COUNT(*) AS n FROM reshor GROUP BY reside) q`
  (horas por recurso: cota de `horas_de_recursos`).
  Salen `ide` y cuentas, nunca nombres. Anotar en `progress/impl_F-038.md`.
- **M2 (humano, tras desplegar)**: el log de arranque de sv4 y sv5 (`az
  containerapp logs show -n ca-sv5-transfer -g rg-partes-dev --tail 80`) muestra
  `max_rows=500000` (DA1 = B).

## 10. Tests (sin red ni BBDD; `httpx` sustituido como en los tests F-023/F-024)

Por servicio, `test_f038_sigrid_limite.py`: R1 (payload con el `max_rows` del
constructor en cada lectura no paginada: sv2 `fetch_tipos_hora`; sv4
`fetch_dnis_sin_extra`, `fetch_hora_extra_recurso`; sv5 una lectura de cada fila
de §1), R2 (settings sin variable = 200.000 = `MAX_ROWS_DEFECTO`), R3
(parametrizado: 0, 500.001, «abc» ⇒ `ValidationError`; 1 y 500.000 valen), R4
(sv3/sv4 con `max_rows=7` siguen pidiendo 5.001), R5 (cableado con
`SIGRID_API_MAX_ROWS=12345` ⇒ cliente con 12345; sustituir la clase del cliente
para capturar los kwargs), R6 (`caplog`), R7–R9, R14 (0, 200,5 ⇒ error; 200
vale), R15 (plazo `httpx.post` 230). R10 por guardián (texto) más un test que
importe `sql_read` con `ENV_PATH` sustituido si es viable; si no, solo guardián
(anotarlo). R11–R13 en el guardián de raíz.

## 11. Riesgos y alternativas descartadas

- Respuestas enormes en memoria: no aplica; las lecturas no paginadas están
  acotadas por su SQL y las grandes ya paginan. Subir `max_rows` solo quita un
  tope artificial.
- Descartado paginar las lecturas de sv5: son lotes por `id` o agregados
  (`sigrid_api.md` §6.7: no necesitan paginar).
- Descartado fijar la variable en manifiestos (DA2 B): cambio de Azure sin
  necesidad.
- Despliegue: sv2, sv3, sv4 y sv5 (`.\infra\redeploy_partes.ps1`), lo lanza el
  humano tras M0. Sin cambio de esquema ni de colas: orden indiferente.
