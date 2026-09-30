<!-- specs/F-023-recurso-alta-empresa/design.md -->
# F-023 · Diseño técnico

Datos: `progress/explore_F-023_sigrid.md` (§N). Requisitos: `requirements.md`.
Revisado el 2026-09-30 con tres respuestas del humano: la empresa viene en el
**membrete** del parte, las lecturas de sigrid-api se **paginan**, y el caso
guía es **MO/0239** (§8.2).

## 1. Servicios que toca y por qué (límite de servicio)

| Servicio | Por qué | Qué no hace |
|---|---|---|
| sv2 | Solo él lee el papel: la empresa del membrete no existe en ningún otro sitio. Un campo más en la cabecera (R5) | No traduce a empresa de Sigrid ni decide nada |
| sv3 | Dueño del casado de obra, trabajador y recurso (R2–R31) y de la base `partes` en la ingesta | No escribe en Sigrid |
| sv5 | Único que escribe: hoy firma con `SIGRID_EMPRESA=1` y numera `PT` mezclando empresas (§6) (R32–R37) | No casa; solo **verifica** |
| sv4 | Sus clientes `infrastructure/sigrid/` y su `orm_models.py` son copias de la lista cerrada: se cambian con las de sv3. Su combo de obras **oculta** la gemela de la 28 (R38–R42) | No re-casa |

La traducción texto → empresa vive en sv3 y no en sv2: sv2 no tiene maestros
de Sigrid (solo el catálogo `auxhor` para el prompt) y el casado es de sv3.

## 2. Encaje en la arquitectura

Reglas como **funciones puras** en `application/services/` (tests por tablas
de casos, mutación barata); los adaptadores solo aportan campos. Flujo sv3:
maestros paginados → `IndicePersonas` → empresa del membrete (R7) → obra
(R9–R14) → empresa del parte (R15) → trabajador (R17–R24). Conciliación:
recurso por persona, empresa y fecha de la línea (R25–R31).

## 3. Ficheros a crear

| Ruta | Contenido |
|---|---|
| `services/partes-persistencia/application/services/seleccion_sigrid.py` | `de_alta`, `IndicePersonas`, `Resolucion`, `elegir_obra` (§5.1) |
| `services/partes-persistencia/application/services/empresa_membrete.py` | `ResolutorEmpresa` (§5.2) |
| `services/partes-persistencia/config/empresas_membrete.yaml` | alias por `numemp`: `1: [RUESMA]`, `28: [PORSAN]` (DA3) |
| `services/partes-transfer/application/services/coherencia_recurso.py` | `de_alta`, `verificar_recurso`, `elegir_por_dni` (§5.4) |
| `services/partes-api/tests/conftest.py` + `test_f023_empresa_membrete.py` | primera suite de sv2: schema (R5) y prompt (§4) |
| `services/partes-persistencia/tests/test_f023_*.py` | `seleccion_sigrid`, `empresa_membrete`, `pipeline_match`, `recurso_conciliador`, `cliente_sigrid` (paginación) |
| `services/partes-transfer/tests/test_f023_escritura_empresa.py` | R32–R37 y R4 |
| `services/partes-front/tests/test_f023_catalogo_empresa.py` | R3–R4, R38–R42 |
| `tests/test_f023_de_alta_gemelos.py` | guardián de `de_alta` sv3/sv5 y del SQL de sv4 (solo si DA6) |

## 4. Ficheros a modificar

**sv2** (`services/partes-api/`)
- `domain/models/parte_models.py`: `CabeceraParte.empresa_membrete: Optional[str] = None`
  (el modelo es `extra="forbid"`: sin el campo, la respuesta nueva fallaría).
- `config/prompts.yaml`: en `task` §1 CABECERA, una viñeta nueva para
  `cabecera.empresa_membrete` (nombre de empresa del membrete o logotipo, tal
  cual; null si no hay; no deducirlo) y la clave en `schema_hint`. Nada más del
  prompt cambia (DA12). El prompt solo se versiona por git (`prompt_key` en la
  base no lleva versión).

**sv3** (`services/partes-persistencia/`)
- `domain/models/sigrid_models.py`: `empresa`/`fecbaj` en `EmpleadoRow` y
  `RecursoRow`, `empresa` en `ObraRow`, `EmpresaRow(numemp, nombre, fecbaj,
  desact)` nueva. `parte_records.py`: `ObraMatch.empresa`;
  `ParteDocumento.empresa_membrete`, `.empresa`, `.empresa_origen`.
- `domain/ports/sigrid_lookup_port.py`: `fetch_empresas()`.
- `infrastructure/sigrid/sigrid_api_client.py`: `_leer_paginado` (§6),
  `truncated` ⇒ excepción, SQL de §6, `fetch_empresas`, sin `empresa` en el
  constructor.
- `application/services/parte_normalizer.py`: lee `cabecera.empresa_membrete`.
- `obra_matcher.py`, `empleado_matcher.py`, `sigrid_matcher_provider.py`
  (carga recursos y empresas; `Matchers.indice`, `Matchers.empresas`),
  `persist_parte_pipeline.py` (`_match` §5.3, `_compute_review_required`).
- `recurso_conciliador.py`: `_resuelve_recurso` vía `IndicePersonas` con
  `indice_provider` inyectado (mismo caché del provider); empresa de la línea
  = obra → `parte_documents.empresa` → ninguna (R25); congeladas sin update
  (R30); marca de revisión como `_docs_degradados` (R29).
- `infrastructure/database/orm_models.py` (**y la copia de sv4, byte-idéntica**):
  `ParteDocumentOrm` + `empresa_membrete String(255)`, `empresa Integer`,
  `empresa_origen String(24)`, nullables (DA11). `ddl_complementario()` las
  añade solo al arrancar (`ADD COLUMN IF NOT EXISTS`).
- `sqlalchemy_parte_repository.py`: persiste las tres columnas;
  `fetch_registros_para_recurso` devuelve `recurso_ide` y `parte_empresa`.
- `interface_adapters/api/app.py` y `config/settings.py`: sin `sigrid_empresa`
  (DA5); ruta del YAML de alias en settings con valor por defecto.

**sv5** (`services/partes-transfer/`)
- `sigrid_write_client.py`: `obra_por_*` con `con.emp` y fallo si hay varias
  filas (R35); `siguiente_cod_pt(ano, empresa)` (R33); `stmts_crear_parte`
  con `con.emp` de la obra y `INSERT INTO hmo … WHERE cod=? AND tip=? AND
  emp=?` (R32, R34); `recursos_por_dni` sustituye a `resides_por_dni`;
  `datos_recursos` nueva; `_read` con `truncated` ⇒ excepción (sin paginar:
  todas sus lecturas van por lotes acotados, §6.7 de `sigrid_api.md`).
- `registro_pipeline.py` (`preparar`): `elegir_por_dni` (R37) y
  `verificar_recurso` (R36) antes de reglas y escritura. `reglas_registro.py`:
  motivos concretos. `main.py`, `app.py`, `settings.py`: sin `empresa`.

**sv4** (`services/partes-front/`)
- `sigrid_lookup_client.py`: `EmpleadoOption.empresa`, `ObraOption.empresa`,
  obras por `ide`, `_leer_paginado` y `truncated` como sv3; el filtro de alta
  a hoy no cambia. `orm_models.py`: la copia de sv3.
- `interface_adapters/web/app.py`: `empresa` en los dos endpoints (R40).
- `static/app.js`: empresa en las etiquetas; filtro por la empresa de la obra
  en los dos modales de alta manual (R41).
- `parte_repository.py`: `_soltar_recurso(reg)` en `backfill_empleado` y los
  tres `reassign_empleado_*`, solo líneas no congeladas (R42).

**Docs y arnés**: `docs/ARCHITECTURE.md` (punto 12 de semántica de dominio y
las tres columnas en el punto 7), `docs/referencia/partes-proyecto.md` §4.6,
§5.1, §6.6; `azure-apps/partes.md` (commit allí, sin push); `CLAUDE.md` solo
si DA6.

## 5. Clases y funciones

### 5.1 sv3 · `seleccion_sigrid.py` (pura)

```python
def de_alta(fecbaj: int | None, fecha: int) -> bool                       # R1
@dataclass(frozen=True)
class Resolucion: ide: int | None; motivo: str  # ok|ambiguo|solo_baja|otra_empresa|desconocido
class IndicePersonas:
    def __init__(self, empleados: list[EmpleadoRow], recursos: list[RecursoRow]) -> None
    def empresas_con_recurso(self, dni: str | None, fecha: int) -> frozenset[int]
    def elegir_ficha(self, dni: str | None, empresa: int | None, fecha: int) -> Resolucion
    def fichas_candidatas(self, empresa: int | None, fecha: int) -> list[EmpleadoRow]
    def elegir_recurso(self, dni, empleado_ide, preferido, empresa, fecha) -> ResolucionRecurso
def elegir_obra(candidatas: list[ObraRow], empresa_membrete: int | None,
                discriminantes: list[frozenset[int]], nombre: str | None,
                min_score: float) -> tuple[ObraRow | None, str]
```

`ResolucionRecurso` añade a `Resolucion` los descartados por baja y por otra
empresa (R28). `elegir_obra` implementa R9–R13 sobre las candidatas que
`ObraMatcher` ya encontró por código (con el padding de siempre).

### 5.2 sv3 · `empresa_membrete.py` (pura)

`ResolutorEmpresa(alias: dict[int, list[str]], empresas: list[EmpresaRow])`
con `resolver(texto: str | None) -> tuple[int | None, str]` (`membrete`,
`sin_texto`, `sin_alias`, `varias`, `empresa_no_valida`). Normaliza con
`text_match.normalize` y casa por palabras completas (R7). Un alias cuyo
`numemp` no esté en `auxemp` o esté de baja se ignora con WARNING al construir.

### 5.3 sv3 · pipeline `_match`

1. Fecha de referencia (R16). 2. `empresa_m = resolutor.resolver(texto)`.
3. Discriminantes: `indice.empresas_con_recurso(dni, fecha)` por registro con
DNI. 4. Obra: `ObraMatcher.match(codigo, nombre, empresa_m, discriminantes)`.
5. Empresa del parte y origen (R15). 6. Trabajador: `elegir_ficha`; `ok` casa;
`ambiguo`/`solo_baja`/`otra_empresa` cierran la línea (R22); `desconocido`
sigue a alias (R23) y nombre (R24, sobre `fichas_candidatas`). 7.
`review_required` también con obra `codigo_otra_empresa`, `codigo_ambiguo` o
`nombre_ambiguo`.

### 5.4 sv5 · `coherencia_recurso.py` (pura)

```python
def de_alta(fecbaj: int | None, fecha: int) -> bool
@dataclass(frozen=True)
class RecursoSigrid: reside: int; empresa: int | None; fecbaj: int | None; dni: str | None
def verificar_recurso(r: RecursoSigrid | None, empresa: int, fecha: int, dni: str | None) -> str | None
def elegir_por_dni(cands: list[RecursoSigrid], empresa: int, fecha: int) -> tuple[int | None, str | None]
```

## 6. SQL y paginación (lecturas de Sigrid; ningún SQL manual de PostgreSQL)

**Paginación (R3)** en sv3 y sv4, mismo diseño en las dos copias:
`_leer_paginado(sql, params, orden, label)` añade `ORDER BY <orden> OFFSET ?
ROWS FETCH NEXT ? ROWS ONLY`, pide `max_rows = PAGINA_FILAS + 1`
(`PAGINA_FILAS = 5000`, constante del cliente: sin variable nueva en Azure) y
encadena hasta una página con menos de `PAGINA_FILAS`. Con `max_rows` una fila
por encima de la página, `truncated: true` nunca es legítimo ⇒ excepción (R4).
Clave de orden (única y estable; nunca un campo `text`):

| Lectura | `ORDER BY` | Cambio de SQL |
|---|---|---|
| empleados sv3 | `con.ide` | + `con.emp AS empresa, con.fecbaj AS fecbaj`; sin `WHERE con.emp` |
| recursos sv3 | `res.ide` | + `JOIN con rc ON rc.ide=res.ide`, `rc.emp`, `rc.fecbaj` |
| obras sv3/sv4 | `con.ide` | + `con.emp AS empresa`; dedup por `ide` |
| empresas sv3 | `auxemp.ide` | nueva: `numemp, res, fecbaj, desact` |
| reshor sv3 | `reshor.ide` | — |
| tipos de hora sv3/sv4 | `auxhor.ide` | orden `(ext, cod)` se rehace en Python |
| partidas sv3/sv4 | `obrparpar.ide` | — |
| hmo de obra sv3 | `hmo.ide` | — |
| empleados sv4 | `con.ide, res.ide` | + `con.emp AS empresa`; `WHERE` de alta igual |

Sin paginar (agregados o lotes acotados, §6.7 de `sigrid_api.md`), solo con
`truncated` ⇒ excepción: `fetch_dnis_sin_extra`, `fetch_hora_extra_recurso`
(sv4) y todas las de sv5. sv5 nuevo: `obra_por_*` + `con.emp`;
`siguiente_cod_pt`: `… WHERE cod LIKE ? AND emp = ?`; `recursos_por_dni`: el
`UNION ALL` actual sin `MAX/GROUP BY`, con `reside, rc.emp, rc.fecbaj` y DNI;
`datos_recursos(resides)` en lotes de ≤ 500: `reside, rc.emp, rc.fecbaj` y DNI
(`emp.dni` si no vacío, si no `res.cif`).

## 7. Ficheros que NO se tocan y fuera de alcance

`jornada_resolver.py`, clientes `infrastructure/sesame/`, `partida_*`,
`tipo_hora_resolver.py`, `congelacion.py`, sv1, `infra/`,
`prueba_escritura_sigrid.py` (M4). **Fuera de alcance**: el banco de evals y
`harness/rutas_sensibles.json` del prompt (son **F-007**, que sigue
pendiente); re-casar empleado, obra o empresa de partes ya ingeridos (DA7);
mostrar la empresa del parte en las pantallas de sv4 (candidata a feature
pequeña); cualquier escritura en Sigrid fuera de sv5.

## 8. Decisiones abiertas (el humano aprueba o rebate)

| # | Propuesta | Por qué / alternativa |
|---|---|---|
| DA1 | «De alta» = `con.fecbaj` del recurso y de la ficha; `emp.fecbaj` no | 22 empleados con líneas posteriores a su `emp.fecbaj`; la baja del recurso es la mantenida (804 en agosto). Es la regla de sv4 (§1) |
| DA2 | A la fecha de la línea (recurso, sv3 y sv5) o del parte (ficha); `fecbaj > fecha`; el portal sigue con «hoy» | sv3 re-concilia lo pendiente en cada pasada: con «hoy», una línea de julio cambiaría de recurso por una baja de agosto. 0 líneas caen el día de la baja |
| DA3 | **Empresa del parte = membrete** (sv2 lo lee, sv3 lo traduce con alias versionados). Sin membrete útil: obra única → su empresa; gemelas → trabajadores → nombre → revisión | `auxemp` no trae CIF y el nombre oficial («PORSAN E HIJOS CONSTRUCCIONES SL») no es lo que pone el logotipo: una tabla de alias es determinista y la mantiene el humano. Alternativa: similitud contra `auxemp.res` (descartada: no determinista) |
| DA4 | Sin empresa del parte, el trabajador se casa solo con una única ficha de alta en todas las empresas | Alternativa: no casar nunca sin empresa |
| DA5 | `SIGRID_EMPRESA` sale del código de sv3 y sv5; la variable de Azure queda inerte (`extra="ignore"`) | Alternativa: «empresas permitidas». Nadie lo ha pedido |
| DA6 | sv5 verifica empresa, alta y persona de cada recurso y resuelve por DNI con la misma regla ⇒ **ampliar la lista cerrada de `CLAUDE.md`** con `de_alta` y la elección por DNI (sv3/sv5, guardián en la raíz). **Pendiente del humano** | Último punto antes de producción; caza recursos rancios tras reasignar y bajas posteriores. Alternativa: confiar en sv3 (sin duplicación, sin red) |
| DA7 | Sin reescritura histórica: empleado, obra y empresa ya casados no se re-casan; congeladas no cambian de recurso; lo pendiente sí se re-resuelve (R31) | Lo pendiente aún no está en Sigrid. Re-casar pendientes, en otra feature tras M1 |
| DA8 | Portal: empleados «de alta a hoy» con empresa; al reasignar se suelta el recurso y lo resuelven sv5 y sv3 | Alternativa: que sv4 resuelva ⇒ copiaría la lógica de sv3 |
| DA9 | Una sola feature; **despliegue sv5 → sv2 → sv3 → sv4** | sv5 primero es seguro (su verificación omite recursos de otra empresa). sv2 antes que sv3: sv3 tolera la clave ausente y sv2 nuevo contra sv3 viejo solo añade una clave que se ignora |
| DA10 | **Paginación** `OFFSET/FETCH` de 5.000 en todos los listados de sv3 y sv4 y `truncated` ⇒ excepción en los tres | Pedido por el humano; `sigrid_api.md` §6.4. Un maestro parcial puede hacer única a una persona con dos fichas |
| DA11 | Tres columnas nullables en `parte_documents` (`empresa_membrete`, `empresa`, `empresa_origen`), en las dos copias de `orm_models.py` | Sin ellas, la conciliación no sabe la empresa de un parte sin obra casada y nadie puede auditar por qué se eligió una gemela. Alternativa: no persistir (solo se usa en la ingesta) |
| DA12 | Cambio **mínimo y aditivo** del prompt (un campo) **antes de F-007**, protegido por M5 y por el diseño: un membrete mal leído nunca escribe en otra empresa (R9 exige obra de esa empresa; sv5 verifica) | F-007 pide banco de evals antes de tocar el prompt. Alternativa: hacer antes F-007 o su banco mínimo; retrasa F-023 |

## 9. Verificaciones manuales (humano)

- **M1 · antes de desplegar (lectura).** Impacto en `partes`: `ide` de obras
  gemelas en Sigrid (`… WHERE con.cod IN (SELECT c.cod … GROUP BY c.cod HAVING
  COUNT(DISTINCT c.emp)>1)`) y en PostgreSQL `SELECT r.obra_ide, d.approved,
  count(*) FROM parte_registros r JOIN parte_documents d ON d.id=r.document_id
  WHERE d.is_active AND r.deleted_at_utc IS NULL AND r.obra_ide IN (…) GROUP BY 1,2;`
- **M2 · tras sv5.** Aprobar un parte de una obra de la 28 y comprobar en
  Sigrid que su cabecera tiene `con.emp = 28` y el siguiente `PT` de la 28.
- **M3 · tras sv3.** `POST /admin/reconciliar-recursos` (lo decide el humano);
  el caso guía (MO/0239) queda con el recurso de alta de su empresa.
- **M4.** El código `0404` (modo pruebas) existe en una sola empresa.
- **M5 · evaluación del membrete (antes de desplegar sv2).** Con sv2 en local,
  ≥ 10 partes reales (≥ 5 de cada empresa): `empresa_membrete` correcto y el
  resto de la cabecera y los empleados igual que su extracción guardada. Se
  anota en `progress/evals_F-023.md` sin nombres ni DNIs.

## 10. Riesgos

- Más partes en revisión (gemelas sin membrete ni DNI legibles; personas en dos
  empresas). Es lo pedido: no elegir al azar.
- Un membrete leído mal no escribe mal: si no hay obra con ese código en esa
  empresa, la obra queda sin casar (R9–R10).
- Tras soltar el recurso (R42) la matriz agrupa esas líneas por su clave
  alternativa hasta la siguiente pasada de sv3.
- Añadir columnas cambia el recuento de `ddl_complementario()` (137 ⇒ 140) que
  sale en los logs de arranque.
- Tests que construyen los clientes con `empresa=` o usan `resides_por_dni`: se
  inventarían en T1 y se adaptan, nunca se borran.
