<!-- progress/impl_F-023.md -->
# F-023 · Informe del implementer

Rama `feature/F-023-recurso-alta-empresa`. Rigor **crítico**. Spec aprobada
el 2026-10-01 (DA1–DA12, con DA6, DA11 y DA12). T1–T24 hechas, un commit
por tarea (`git log --oneline dev..HEAD`: T1…T23 más un commit de ajuste de
T15, ver D6). Sin push, sin despliegue, ni una escritura en Sigrid.

## Qué cambió, por servicio

| Servicio | Cambio | Ficheros |
|---|---|---|
| sv2 | `cabecera.empresa_membrete` (R5): campo del modelo + viñeta y clave del prompt (DA12, nada más). Primera suite de sv2 | `domain/models/parte_models.py`, `config/prompts.yaml`, `tests/conftest.py`, `tests/test_f023_empresa_membrete.py` |
| sv3 | Reglas puras (`seleccion_sigrid.py`: `de_alta`, `IndicePersonas`, `elegir_obra`, `elegir_por_nombre`); membrete→empresa (`empresa_membrete.py` + `config/empresas_membrete.yaml`); cliente paginado, todas las empresas, `fetch_empresas`, `truncated` ⇒ error; casado de ingesta R6–R24 (`persist_parte_pipeline`, `obra_matcher`, `empleado_matcher`, `sigrid_matcher_provider`); recurso R25–R31 (`recurso_conciliador`); 3 columnas (DA11); cableado sin `SIGRID_EMPRESA` | `application/…`, `domain/…`, `infrastructure/sigrid/sigrid_api_client.py`, `infrastructure/database/{orm_models,sqlalchemy_parte_repository}.py`, `interface_adapters/api/app.py`, `config/settings.py` |
| sv5 | `coherencia_recurso.py` (R36–R37); cliente con `con.emp` de la obra, `PT` por empresa, `INSERT INTO hmo … AND emp = ?`, `obra_por_codigo` falla con varias empresas, `recursos_por_dni` y `datos_recursos`, `truncated` ⇒ error; `preparar` verifica/resuelve; motivos concretos; sin `SIGRID_EMPRESA` | `application/{services/coherencia_recurso,services/reglas_registro,pipelines/registro_pipeline}.py`, `domain/models/registro_models.py`, `infrastructure/sigrid/sigrid_write_client.py`, `config/settings.py`, `main.py`, `interface_adapters/api/app.py` |
| sv4 | Cliente paginado + `truncated`; `empresa` en `EmpleadoOption`/`ObraOption`, obras por `ide` (R38–R39); endpoints con `empresa` (R40); combos y filtro por empresa (R41, `static/app.js`); `_soltar_recurso` (R42); copia de `orm_models.py` | `infrastructure/sigrid/sigrid_lookup_client.py`, `interface_adapters/web/app.py`, `application/services/obra_catalog.py`, `infrastructure/database/{orm_models,parte_repository}.py`, `static/app.js` |
| Raíz / docs | Guardián `tests/test_f023_de_alta_gemelos.py`; lista cerrada de `CLAUDE.md` (DA6); `docs/ARCHITECTURE.md` (punto 12 y 7); `partes-proyecto.md` §4.6, §5.1, §6.6; `azure-apps/partes.md` (commit local `8c7df86`, sin push) | |

## Decisiones de diseño (dentro de la spec)

- **Motivos de casado**: trabajador sin casar por `dni_ambiguo`,
  `dni_solo_baja`, `dni_otra_empresa`, `alias_no_valido`, `nombre_ambiguo`
  en `empleado_match_method`; obra por `codigo_otra_empresa`,
  `codigo_ambiguo`, `nombre_ambiguo` en `obra_match_method`.
- **`empresa_origen` (R15)**: obra casada con membrete conocido ⇒
  `membrete`; sin membrete, por método: `codigo_trabajadores` ⇒
  `trabajadores`, `codigo_nombre`/`nombre` ⇒ `nombre`, resto ⇒ `obra`. Sin
  obra: `membrete` o NULL. Obra sin `con.emp` ⇒ NULL/NULL.
- **Umbral de nombre** `>=` (como el matcher de siempre); «supera
  estrictamente a las demás» es `>` (un empate es ambiguo).
- **R23**: alias fuera de R17 con DNI que el maestro no conoce ⇒
  `alias_no_valido` (R18–R21 no cubren «desconocido»).
- **R25** sin DNI: la ficha casada; con DNI y sin fichas cargadas (conciliador
  sin proveedor): también la ficha casada, más `res.cif`. Obra fuera del
  maestro ⇒ empresa del parte. Línea sin fecha ⇒ hoy (como R16).
- **R29**: `desconocido` (la persona no tiene ningún recurso) sigue siendo
  el `sin_recurso` de siempre, sin subir revisión; solo ambigüedad, solo
  baja u otra empresa marcan el parte.
- **R30**: una congelada no se actualiza y cuenta en el día con su
  `recurso_ide` actual (por eso `fetch_registros_para_recurso` lo trae).
- **R37**: si falla la lectura por DNI, la línea queda sin recurso (motivo
  de siempre). **R36**: si falla `datos_recursos`, la petición falla entera:
  nada se escribe sin verificar.
- **R36, recurso sin DNI y línea con DNI** ⇒ «no es de este trabajador» (no
  se puede comprobar). El DNI del recurso es `emp.dni` o, vacío, `res.cif`
  (design §6); un recurso con `cif` ≠ `emp.dni` (10 en Sigrid) solo pasa por
  `emp.dni`.
- `SIGRID_API_MAX_ROWS` de sv3 queda solo como valor por defecto de
  `_post_sql_read`: hoy todas las lecturas de sv3 paginan (5.001).

## Desviaciones respecto a la spec (para el reviewer y el humano)

- **D1 · PATCH de obra por `ide` (sv4).** Con las gemelas en el combo (R39),
  `patch_parte_obra` resolvía la obra por código en el catálogo y
  **cambiaba la elegida por su gemela** (RED en T15: se eligió 100 y quedó
  200). Ahora resuelve por `ide` (`ObraCatalog.get_by_ide`) y por código
  solo si es único. Toca `obra_catalog.py`, fuera de la lista de design §4.
  Sin esto R39/R41 dejaban un camino roto. **A validar por el humano.**
- **D2 · PyYAML** no está en `requirements.txt` de sv3: llega con
  `uvicorn[standard]`. No se añade (regla del implementer); recomendable
  declararlo si se quiere depender de él explícitamente.
- **D3 · `construir_casado_sigrid`** sale de `build_app` (sv3) para probar el
  cableado sin PostgreSQL; `test_f015_r10_fail_fast_wiring` se adapta (mira
  `jornada_cache_ttl_s` en la función nueva).
- **D4 · `RecursoSigrid`** vive en `domain/models/registro_models.py` (sv5) y
  `coherencia_recurso` lo reexporta: la infraestructura no importa de
  `application`.
- **D5 · Modo pruebas de sv5**: la obra 0404 tiene empresa; los recursos de
  otra empresa ahora se omiten también en pruebas (M4).
- **D6 · Commit de ajuste de T15** (`31a411d`): dos dobles de sv4
  (`test_f015_r26_sugerida_fecha`, `test_f003_r12_jornada_resolver`) no
  tenían `empresa`; el commit de T16 se hizo sin ver la suite de sv4 en
  verde (un `| tail` tapó el código de salida). Arreglado en commit aparte.

## Tests existentes adaptados (nunca borrados)

`partes-transfer/tests/dobles.py` (`SigridFake`: `recursos_por_dni`,
`datos_recursos`, `siguiente_cod_pt(ano, empresa)`, `emp` en la cabecera),
`test_f002_pipeline_fases.py` (obras con `empresa=1`),
`partes-persistencia/tests/test_f015_r10_fail_fast_wiring.py` (D3),
`partes-front/tests/test_f015_r26_sugerida_fecha.py` (clave `empresa`),
`partes-front/tests/test_f003_r12_jornada_resolver.py` (doble con `empresa`).

## Fase RED (traza real pegada; el esqueleto previo solo tenía firmas)

Comando por servicio: `cd services/<svc> && ../../.venv/Scripts/python.exe
-m pytest -q -p no:cacheprovider <fichero> -k <tests>`. Extracto de líneas
`>`/`E`/`FAILED`; sin editar el texto.

**R1, R9, R10, R11, R13, R19, R25, R27** — `test_f023_seleccion_sigrid.py`
contra el esqueleto (`raise NotImplementedError`):
```
E       NotImplementedError
E       NotImplementedError: elegir_ficha
E       NotImplementedError: elegir_recurso
FAILED ...::test_f023_r1_de_alta_segun_con_fecbaj[20260915-False]
FAILED ...::test_f023_r9_con_membrete_gana_la_obra_de_esa_empresa
FAILED ...::test_f023_r10_membrete_de_otra_empresa_no_casa
FAILED ...::test_f023_r11_los_trabajadores_eligen_la_gemela
FAILED ...::test_f023_r13_discriminantes_que_discrepan_es_ambiguo
FAILED ...::test_f023_r19_dos_fichas_de_alta_en_la_empresa_es_ambiguo
FAILED ...::test_f023_r25_r27_caso_guia_queda_el_recurso_de_alta
13 failed, 37 deselected in 0.47s
```
**R3 y R4** (`test_f023_cliente_sigrid.py`, cliente de sv3 anterior):
```
>       assert [p["parameters"] for p in falso.peticiones] == \
E       assert [[1]] == [[0, 5000], [5000, 5000]]
>       assert [p["max_rows"] for p in falso.peticiones] == [PAGINA + 1]
E       assert [10000] == [5001]
>       with pytest.raises(RuntimeError, match="truncad"):
E       Failed: DID NOT RAISE RuntimeError
```
**R7** (`test_f023_empresa_membrete.py` de sv3): 26 fallos contra el
esqueleto (`NotImplementedError`) y `FileNotFoundError: …config\empresas_membrete.yaml`.

**R9, R10, R11, R13, R19, R22** (`test_f023_pipeline_match.py`, pipeline
anterior, con el constructor ya aceptando `hoy` y `alias_empresas`):
```
E       AssertionError: assert (100, 'codigo_padded', None) == (200, 'codigo_membrete', 28)
E       AssertionError: assert 300 is None            # R10: casaba la obra de otra empresa
E       AssertionError: assert (100, 'codigo_padded') == (200, 'codigo_trabajadores')
E       AssertionError: assert (100, 'codigo_padded') == (None, 'codigo_ambiguo')
E       AssertionError: assert 30 is None             # R19/R22: casaba la primera ficha
E       AssertionError: assert 'dni' == 'dni_otra_empresa'
6 failed, 37 deselected in 0.90s
```
**R25, R27, R30** (`test_f023_recurso_conciliador.py`, conciliador anterior):
```
E       AssertionError: assert (900, 4000, 'ok') == (901, 5000, 'ok')   # caso guía: el de baja
E       AssertionError: assert (900, 'sin_parte') == (None, 'sin_recurso')
E       assert 900 == 902                                               # empresa de la obra
E       assert [1, 2, 3, 4] == [4]                                      # congeladas re-resueltas
4 failed, 19 deselected in 3.83s
```
**R32, R33, R34** (`test_f023_escritura_empresa.py -k cliente`, cliente de sv5 anterior):
```
E       AssertionError: assert [1, 35, 1, 'P...ve', 20260930] == [28, 35, 1, '...ve', 20260930]
E        +    where '...' = _sql('INSERT INTO hmo (ide, cenide, obride, ano, mes, reside, cenmul) SELECT ide, ?, ?, ?, ?, 0, 0 FROM con WHERE cod = ? AND tip = ?')
E       TypeError: SigridWriteClient.siguiente_cod_pt() takes 2 positional arguments but 3 were given
```
**R36** (`-k coherencia` contra el esqueleto: `NotImplementedError` en
`verificar_recurso` y `elegir_por_dni`, 22 failed) y en el pipeline:
```
E               TypeError: SigridFake.siguiente_cod_pt() missing 1 required positional argument: 'empresa'
E       assert [] == [1]                   # R37: la línea sin recurso no se resolvía por DNI
4 failed, 48 deselected in 0.49s
```
**R42** (`test_f023_catalogo_empresa.py -k soltar`, repositorio anterior):
```
E       AssertionError: assert (900, 501, '1...78Z', 7, 'ok') == (None, None, None, None, None)
5 failed, 23 deselected, 1 warning in 3.35s
```
**D1** (`-k endpoint`): `E  AssertionError: assert (200, 'Sur') == (100, 'Norte')`.

**Guardianes (entregable = test)**, roto a propósito en copias aisladas del
scratchpad, nunca en el árbol real:
- T18 (sv3, `fetch_reshor` sin paginar / sv4, `fetch_tipos_hora`):
  `E AssertionError: fetch_reshor` · `1 failed, 8 passed`; `E AssertionError: fetch_tipos_hora` · `1 failed, 6 passed`.
- T19 (`>=` en `de_alta` de sv5 y en el SQL de sv4): `FAILED …tabla_comun[20260915-20260915-False-sv5]`,
  `…misma_firma_y_codigo` (`ops=[GtE()]` vs `ops=[Gt()]`), `…sql_de_sv4_conserva_la_misma_regla` · `3 failed, 11 passed`.

## T1 · Inventario (resumen)

Ningún test construía los clientes con `empresa=` ni miraba `ORDER BY` o el
`_match` de sv3. Sí dependían de lo que cambia: el doble `SigridFake` de sv5
(`resides_por_dni`, `siguiente_cod_pt(ano)`), las obras sin empresa de
`test_f002_pipeline_fases`, el `fetch_obras` del doble de
`test_f004_endpoints_congelados` (lista vacía: sin cambio) y
`dobles.registro` de sv3 (`empleado_reside=501`; `test_f003_r26` sigue
verde porque el recurso 501 es el único candidato). Adaptados: ver arriba.

## Resultados reales

- `bash harness/init.sh` tras el commit `92d88c2`: **exit 0**, «ENTORNO
  LISTO»; raíz `416 passed, 1 skipped in 71.31s`; sv3 `640 passed in
  20.18s`; sv4 `1093 passed, 1 warning in 323.03s`; sv5 `141 passed, 1
  warning in 9.61s`; sv1 y sv2 en verde (caché; sv2 `8 passed` a mano).
- `node --check services/partes-front/static/app.js`: OK.
- Mutación (T23): primera campaña sobre `200a98c`, 214 mutantes, **3
  supervivientes** (`@dataclass(frozen=True)` de `RecursoSigrid` y de
  `EmpresaRow`, y `cod = p.cod or …siguiente_cod_pt` → `and` en sv5).
  Ninguno era equivalente: se mataron con tests (inmutabilidad de los DTO y
  «el correlativo se pide una vez por parte nuevo», `16dc86a`). Campaña
  final sobre `ad48d2d`: **214/214 muertos, 0 supervivientes, 0 timeouts,
  0 sin veredicto**. Informe: `progress/mutacion_F-023.md`.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | sv2 8 · sv3 640 · sv4 1.093 · sv5 141 · raíz 416 (+1 skipped): todo en verde |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 99.8% de 597 líneas cambiadas cubiertas (596/597, umbral 80%, nivel critico)` |
| Mutantes / supervivientes | 214 generados y evaluados (sv3 155, sv4 22, sv5 37; sv2 sin mutantes: solo un campo `Optional`), **0 supervivientes** |
| Workers / timeout | `--workers 6 --timeout 600` · tiempo total 2.076,5 s · media 9,7 s (≈ 58 s reales por mutante con 6 workers; líneas base sv4 ≈ 291 s, sv3 ≈ 16 s, sv5 ≈ 12 s) |
| Tiempo de las suites | dentro de `init.sh` (con cobertura): sv4 323 s, raíz 71 s, sv3 20 s, sv5 9,6 s; sv2 0,4 s suelta |
| SHA medido | `ad48d2dd39b92197f09e5d11b6250a71ca8f2823` (después solo cambian `progress/` y `tasks.md`) |

## Pendientes MANUAL (humano) — detalle y comandos en `progress/current.md`

M1 (gemelas con líneas pendientes, antes de desplegar), M5 (≥ 10 partes
reales con sv2 en local, antes de desplegar sv2), despliegue
**sv5 → sv2 → sv3 → sv4** (lo pide el humano; el DDL de arranque pasa de 137
a 140 sentencias), M2 (cabecera `con.emp = 28` y `PT` de la 28), M3
(`POST /admin/reconciliar-recursos` y caso guía), M4 (`0404` en una sola
empresa) y T17 en navegador (empresa en los combos y filtro del alta
manual). Además, validar **D1** y, si se quiere, declarar PyYAML (D2).

## Fuera de alcance (sin tocar)

Banco de evals y `rutas_sensibles.json` del prompt (F-007); re-casar
empleado, obra o empresa de partes ya ingeridos (DA7); mostrar la empresa
del parte en las pantallas de sv4; `prueba_escritura_sigrid.py`; infra.
