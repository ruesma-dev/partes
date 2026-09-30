<!-- specs/F-023-recurso-alta-empresa/design.md -->
# F-023 · Diseño técnico

Datos de Sigrid: `progress/explore_F-023_sigrid.md` (§N). Requisitos:
`requirements.md` (RN). **Cero cambios de esquema en PostgreSQL**: los métodos
nuevos caben en las columnas `*_match_method` (`String(24)`) y `parte_estado`
no gana valores.

## 1. Servicios que toca y por qué (límite de servicio)

| Servicio | Por qué | Qué no hace |
|---|---|---|
| sv3 | Dueño del casado de obra, trabajador y recurso (R2–R24) | No escribe en Sigrid |
| sv5 | Único que escribe: hoy firma todo con `SIGRID_EMPRESA=1` y numera `PT` mezclando empresas (§6). Sin él, un parte bien casado de la empresa 28 se escribiría con la cabecera de la 1 (R25–R30) | No decide el casado; solo lo **verifica** |
| sv4 | Sus clientes `infrastructure/sigrid/` están en la lista cerrada de duplicación: al tocar el de sv3 se cambia el suyo en la misma feature. Además su combo de obras **oculta** la gemela de la 28 (§4) (R31–R35) | No re-casa nada por su cuenta |

Nada exige otro microservicio: la regla vive donde ya vive el casado (sv3) y
sv5 solo añade una comprobación de seguridad antes de escribir.

## 2. Encaje en la arquitectura

La regla se escribe como **funciones puras** en `application/services/` (sin
red ni BBDD), y los adaptadores solo aportan campos nuevos a los DTOs. Así el
grueso de los tests son tablas de casos sobre funciones puras y la mutación
crítica sale barata.

Flujo en sv3 (ingesta): maestros (empleados + recursos + obras) → **índice de
personas** → obra candidata(s) por código → empresa del parte (R4–R8) →
trabajador dentro de esa empresa (R10–R17). Conciliación: recurso por persona,
empresa de la obra y fecha de la línea (R19–R24).

## 3. Ficheros a crear

| Ruta | Contenido |
|---|---|
| `services/partes-persistencia/application/services/seleccion_sigrid.py` | `de_alta`, `IndicePersonas`, `Resolucion`, `elegir_obra` (§5.1) |
| `services/partes-transfer/application/services/coherencia_recurso.py` | `de_alta`, `verificar_recurso`, `elegir_por_dni` (§5.3) |
| `services/partes-persistencia/tests/test_f023_seleccion_sigrid.py` | tablas de casos R1, R5–R8, R10–R17, R19–R21 |
| `services/partes-persistencia/tests/test_f023_pipeline_match.py` | `_match` y `review_required` con dobles (R4–R18) |
| `services/partes-persistencia/tests/test_f023_recurso_conciliador.py` | R19–R24 |
| `services/partes-persistencia/tests/test_f023_cliente_sigrid.py` | R2–R3 con `httpx` simulado |
| `services/partes-transfer/tests/test_f023_escritura_empresa.py` | R25–R30 |
| `services/partes-front/tests/test_f023_catalogo_empresa.py` | R3, R31–R35 |
| `tests/test_f023_de_alta_gemelos.py` | guardián: `de_alta` de sv3 y sv5 dan lo mismo en la misma tabla, y el SQL de sv4 conserva el predicado (DA6) |

## 4. Ficheros a modificar

**sv3** (`services/partes-persistencia/`)
- `domain/models/sigrid_models.py`: `EmpleadoRow`, `RecursoRow` y `ObraRow`
  ganan `empresa: int | None = None`; los dos primeros, además,
  `fecbaj: int | None = None`. Con valores por defecto, los tests existentes
  no cambian.
- `domain/models/parte_records.py`: `ObraMatch.empresa: Optional[int] = None`.
- `infrastructure/sigrid/sigrid_api_client.py`: SQL de §6; `fetch_empleados`
  sin `WHERE con.emp`; `fetch_obras` deduplica por `ide`; `_post_sql_read`
  lanza si `truncated` (R3); el constructor pierde `empresa`.
- `application/services/empleado_matcher.py`: `match(..., empresa, fecha_int)`
  delega en `IndicePersonas` (R10–R17).
- `application/services/obra_matcher.py`: índice `código → list[ObraRow]`;
  `match(codigo, nombre, discriminantes)` con R4–R8; `empresa_de(obra_ide)`.
- `application/services/sigrid_matcher_provider.py`: carga también
  `fetch_recursos`; `Matchers.indice: IndicePersonas`.
- `application/pipelines/persist_parte_pipeline.py` (`_match`,
  `_compute_review_required`): fecha de referencia (R9), discriminantes antes
  de la obra, parada de la cadena (R15), alias por DNI (R16), revisión por
  `codigo_ambiguo` / `nombre_ambiguo` de obra (R7, R8).
- `application/services/recurso_conciliador.py`: `_resuelve_recurso` usa
  `IndicePersonas.elegir_recurso` (R19–R22) a través de un `indice_provider`
  inyectado (el mismo caché del provider, sin segunda carga de empleados);
  congeladas sin update (R23); marca de revisión como `_docs_degradados`.
- `infrastructure/database/sqlalchemy_parte_repository.py`:
  `fetch_registros_para_recurso` devuelve además `recurso_ide` (para agrupar
  las congeladas por su recurso guardado, R23).
- `interface_adapters/api/app.py`: cableado (sin `empresa`, con
  `indice_provider`). `config/settings.py`: `sigrid_empresa` se retira (DA5).

**sv5** (`services/partes-transfer/`)
- `infrastructure/sigrid/sigrid_write_client.py`: `obra_por_ide` /
  `obra_por_codigo` leen `con.emp` y fallan con varias filas (R28);
  `siguiente_cod_pt(ano, empresa)` (R26); `stmts_crear_parte` con `con.emp` de
  la obra y `INSERT INTO hmo … WHERE cod = ? AND tip = ? AND emp = ?` (R25,
  R27); `recursos_por_dni` sustituye a `resides_por_dni` y `datos_recursos`
  es nueva (§6); `_read` lanza si `truncated` (R3); el constructor pierde
  `empresa`.
- `application/pipelines/registro_pipeline.py` (`preparar`): resolución por
  DNI con `elegir_por_dni` (R30) y verificación de todas las líneas con
  `verificar_recurso` (R29) **antes** de reglas y escritura.
- `application/services/reglas_registro.py`: el motivo de omisión de una línea
  sin recurso usa el motivo concreto que dejó `preparar` (constantes nuevas
  `MOTIVO_RECURSO_OTRA_EMPRESA`, `…_DE_BAJA`, `…_OTRA_PERSONA`, `…_AMBIGUO`).
- `main.py`, `interface_adapters/api/app.py`, `config/settings.py`: sin
  `empresa` (DA5).

**sv4** (`services/partes-front/`)
- `infrastructure/sigrid/sigrid_lookup_client.py`: `EmpleadoOption.empresa`
  y `ObraOption.empresa`; SQL de §6; obras deduplicadas por `ide`;
  `_post_sql_read` lanza si `truncated`. Se conserva el filtro de alta a hoy.
- `interface_adapters/web/app.py`: `empresa` en `/api/sigrid/empleados` y
  `/api/sigrid/obras` (R33).
- `static/app.js`: etiqueta con empresa en los combos de obra y trabajador;
  en los dos modales de alta manual, el combo de trabajador filtra por la
  empresa de la obra elegida (R34). `node --check`.
- `infrastructure/database/parte_repository.py`: helper
  `_soltar_recurso(reg)` llamado en `backfill_empleado` y en los tres
  `reassign_empleado_*` sobre las líneas no congeladas (R35).

**Documentación y arnés**: `docs/ARCHITECTURE.md` (punto 12 de la semántica
de dominio, ≤ 12 líneas), `docs/referencia/partes-proyecto.md` §4.6 y §6.6,
`azure-apps/partes.md` (commit en ese repositorio, sin push) y, **solo si DA6
se aprueba**, la lista cerrada de duplicación de `CLAUDE.md`.

## 5. Clases y funciones

### 5.1 sv3 · `seleccion_sigrid.py` (application, pura)

```python
def de_alta(fecbaj: int | None, fecha: int) -> bool          # R1
@dataclass(frozen=True)
class Resolucion:                                             # ide o None + por qué
    ide: int | None
    motivo: str   # ok | ambiguo | solo_baja | otra_empresa | desconocido
class IndicePersonas:
    def __init__(self, empleados: list[EmpleadoRow], recursos: list[RecursoRow]) -> None
    def empresas_con_recurso(self, dni: str | None, fecha: int) -> frozenset[int]
    def elegir_ficha(self, dni: str | None, empresa: int | None, fecha: int) -> Resolucion
    def ficha_es_candidata(self, ide: int, empresa: int | None, fecha: int) -> bool
    def fichas_candidatas(self, empresa: int | None, fecha: int) -> list[EmpleadoRow]
    def elegir_recurso(self, dni: str | None, empleado_ide: int | None,
                       preferido: int | None, empresa: int | None,
                       fecha: int) -> Resolucion                    # R19–R21
def elegir_obra(candidatas: list[ObraRow], discriminantes: list[frozenset[int]],
                nombre: str | None, min_score: float) -> tuple[ObraRow | None, str]
```

- `IndicePersonas` indexa por DNI normalizado (`text_match.normalize_dni`) las
  fichas y los recursos (por `cif` y por `conide` → ficha → DNI).
- `motivo` de `elegir_ficha`: `ambiguo` (R12), `solo_baja` (R13),
  `otra_empresa` (R14), `desconocido` (DNI inexistente: la cadena sigue a
  alias y nombre como hoy). El pipeline traduce a los métodos `dni_*`.
- Desempate de `elegir_recurso` (R20): preferido ∈ candidatos → ese; si no,
  el único con `conide` = `empleado_ide`; si no, `ambiguo`.
- `elegir_obra` devuelve `(obra, metodo)` con `metodo` ∈ {`codigo`,
  `codigo_trabajadores`, `codigo_nombre`, `codigo_ambiguo`}; recibe solo las
  candidatas ya encontradas por código (el padding sigue en `ObraMatcher`).

### 5.2 sv3 · pipeline `_match` (orden nuevo)

1. `fecha = parte.fecha_int` válida o hoy (R9).
2. Por cada registro con DNI leído: `indice.empresas_con_recurso(dni, fecha)`
   → lista de conjuntos (discriminantes).
3. `parte.obra = matchers.obra.match(codigo, nombre, discriminantes)`;
   `empresa = parte.obra.empresa` (None si sin casar).
4. Trabajador: DNI → `elegir_ficha(dni, empresa, fecha)`; `ok` casa;
   `ambiguo`/`solo_baja`/`otra_empresa` cierran la línea sin casar (R15);
   `desconocido` sigue a alias (R16, por DNI del alias) y a nombre (R17, sobre
   `fichas_candidatas`). La caché por clave de trabajador se mantiene.

### 5.3 sv5 · `coherencia_recurso.py` (application, pura)

```python
def de_alta(fecbaj: int | None, fecha: int) -> bool
@dataclass(frozen=True)
class RecursoSigrid:
    reside: int; empresa: int | None; fecbaj: int | None; dni: str | None
def verificar_recurso(r: RecursoSigrid | None, empresa: int, fecha: int,
                      dni: str | None) -> str | None          # None = coherente
def elegir_por_dni(cands: list[RecursoSigrid], empresa: int,
                   fecha: int) -> tuple[int | None, str | None]
```

## 6. SQL (lecturas de Sigrid vía sigrid-api; ningún SQL de PostgreSQL)

- sv3 `_SQL_EMPLEADOS_BASE`: añade `con.emp AS empresa, con.fecbaj AS fecbaj`;
  `fetch_empleados` termina en `ORDER BY con.cod` sin `WHERE`.
- sv3 `_SQL_RECURSOS`: añade `JOIN con rc ON rc.ide = res.ide` y
  `rc.emp AS empresa, rc.fecbaj AS fecbaj`.
- sv3 y sv4 `_SQL_OBRAS`: añaden `con.emp AS empresa`.
- sv4 `_SQL_EMPLEADOS`: añade `con.emp AS empresa`; el `WHERE` de alta no
  cambia.
- sv5 `obra_por_*`: añaden `con.emp AS emp`. `siguiente_cod_pt`:
  `SELECT MAX(cod) … WHERE cod LIKE ? AND emp = ?`.
- sv5 `recursos_por_dni(dnis)`: el `UNION ALL` actual (por `emp.dni` vía
  `conide` y por `res.cif`) sin `MAX/GROUP BY`, devolviendo `reside`,
  `rc.emp`, `rc.fecbaj` y el DNI normalizado.
- sv5 `datos_recursos(resides)`: `res ⋈ con rc` ⋈ `emp` (LEFT, por `conide`),
  en lotes de ≤ 500 ides: `reside`, `rc.emp`, `rc.fecbaj`, DNI
  (`emp.dni` si no vacío, si no `res.cif`).

## 7. Ficheros que NO se tocan

`orm_models.py` (sv3 y sv4, byte-idénticos), `jornada_resolver.py`, los
clientes `infrastructure/sesame/`, `fetch_dnis_sin_extra` y
`fetch_hora_extra_recurso` de sv4, `partida_*`, `tipo_hora_resolver.py`,
`congelacion.py`, sv1, sv2, `infra/` y `prueba_escritura_sigrid.py` (escribe
solo en la 0404 con su propia config; ver M4). **Fuera de alcance**: re-casar
empleado u obra de partes ya ingeridos (DA7) y cualquier escritura en Sigrid
fuera de sv5.

## 8. Decisiones abiertas (el humano aprueba o rebate)

| # | Propuesta | Por qué / alternativa |
|---|---|---|
| DA1 | «De alta» = `con.fecbaj` del **recurso** y de la ficha de empleado; `emp.fecbaj` no | `emp.fecbaj` tiene 22 empleados con líneas posteriores; la baja del recurso es la que se mantiene (limpieza de 804 en agosto). Es la regla que ya usa sv4 (§1) |
| DA2 | Se evalúa a la **fecha real de la línea** (recurso, sv3 y sv5) y a la **fecha del parte** (ficha); `fecbaj > fecha` | sv3 re-concilia todas las líneas pendientes en cada pasada: con «hoy», una línea de julio cambiaría de recurso al dar a alguien de baja en agosto. El portal sigue con «hoy» (DA8). 0 líneas caen el mismo día de la baja: `>` o `>=` no cambia nada medido |
| DA3 | Empresa del parte = empresa de la obra; las **obras gemelas** (22 códigos activos en la 1 y la 28) se deciden por los trabajadores del parte, luego por nombre, y si no, obra sin casar y revisión | El papel no trae la empresa (el esquema de sv2 no tiene ese campo). Alternativa: que sv2 extraiga la empresa del membrete, si el J.310 la trae: el humano lo sabe, nosotros no. Otra: añadir un campo al parte de papel |
| DA4 | Sin obra casada, el trabajador se casa si su DNI tiene una sola ficha de alta en todas las empresas; si no, sin casar | Alternativa: no casar nunca sin obra. Se descarta: hoy casa, y con ficha única no hay riesgo de empresa |
| DA5 | `SIGRID_EMPRESA` se retira del código de sv3 y sv5; la variable en Azure queda inerte (`extra="ignore"`) y se documenta; se borra de Azure a mano cuando se quiera | Alternativa: conservarla como filtro de «empresas permitidas». Nadie lo ha pedido |
| DA6 | sv5 **verifica** cada recurso (empresa, alta, DNI) y resuelve por DNI con la misma regla. El predicado `de_alta` y la elección por DNI quedan en sv3 y sv5, con guardián en la raíz ⇒ **ampliar la lista cerrada de `CLAUDE.md`** | Es el último punto antes de escribir en producción y recoge lo que sv3 no ve (recurso rancio tras una reasignación, bajas posteriores). Alternativa: sv5 confía en sv3 y no verifica nada ⇒ sin duplicación, pero sin red |
| DA7 | **Sin reescritura histórica**: empleado y obra casados no se re-casan; el recurso de líneas congeladas no se toca nunca (R23). Las líneas **pendientes** sí se re-resuelven en la siguiente pasada (R24) | Pendiente no es histórico: aún no está en Sigrid, y re-resolverlo es justo lo que corrige. Si el humano quiere re-casar también empleado y obra de los pendientes, va en otra feature tras ver M1 |
| DA8 | Portal: catálogo de empleados «de alta a hoy» (como ya hace), con empresa; al reasignar se suelta el recurso (R35) y lo resuelven sv5 (al aprobar) y sv3 (siguiente pasada) | Alternativa: que sv4 resuelva el recurso al reasignar ⇒ copiaría la lógica de sv3 en sv4 |
| DA9 | Una sola feature y **despliegue sv5 → sv3 → sv4** | sv3 sin sv5 escribiría partes de la 28 con cabecera de la 1. sv5 primero es seguro: pone la cabecera con la empresa de la obra y su verificación (R29) omite cualquier recurso de otra empresa que le mande el sv3 antiguo. Partirla en dos exigiría desplegar las dos juntas igualmente |
| DA10 | `truncated: true` ⇒ excepción en los tres clientes | Un maestro parcial puede hacer **única** a una persona que tiene dos fichas: peor que no casar. El provider ya conserva el caché anterior si la carga falla |

## 9. Verificaciones manuales (humano)

- **M1 · antes de desplegar (solo lectura).** Impacto en la base `partes`. En
  Sigrid: `SELECT con.ide FROM obr JOIN con ON con.ide=obr.ide WHERE con.cod IN
  (SELECT c.cod FROM obr o JOIN con c ON c.ide=o.ide GROUP BY c.cod HAVING
  COUNT(DISTINCT c.emp)>1)`; en PostgreSQL, con esos `ide`:
  `SELECT r.obra_ide, d.approved, count(*) FROM parte_registros r JOIN
  parte_documents d ON d.id=r.document_id WHERE d.is_active AND
  r.deleted_at_utc IS NULL AND r.obra_ide IN (…) GROUP BY 1,2;`
  Dice cuántas líneas pueden estar en la gemela equivocada (DA7).
- **M2 · tras desplegar sv5.** Aprobar un parte de una obra de la empresa 28 y
  comprobar en Sigrid (lectura) que su cabecera tiene `con.emp = 28` y el
  siguiente `PT` **de la 28**.
- **M3 · tras desplegar sv3.** `POST /admin/reconciliar-recursos` (lo decide
  el humano) y contar en el log los WARNING de recurso y los métodos
  `codigo_trabajadores` / `codigo_ambiguo` de los partes nuevos.
- **M4.** Que el código `0404` (modo pruebas) exista en **una sola** empresa;
  si no, R28 hace fallar el modo pruebas y hay que decidir.

## 10. Riesgos

- Más partes en revisión: los de obras gemelas sin DNI legible (J.310 rev. 0)
  y los de personas en dos empresas. Es el comportamiento pedido: no elegir
  al azar.
- Al soltar el recurso en sv4 (R35), la matriz del trabajador agrupa esas
  líneas por su clave alternativa hasta que sv3 vuelva a pasar.
- `IndicePersonas` se construye por TTL con ~1.400 fichas y ~2.600 recursos:
  O(n), despreciable frente a la llamada HTTP.
- Tests existentes que construyen los clientes con `empresa=` o esperan
  `resides_por_dni`: se inventarían en T1 y se adaptan, nunca se borran.
