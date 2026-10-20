<!-- specs/F-050-misma-fila-para-el-mismo-trabajador/design.md -->
# F-050 · Misma fila para el mismo trabajador — Diseño

**Solo sv4** (`services/partes-front/`): la agrupación por trabajador es del portal (§7).
Sin esquema, SQL nuevo ni Sigrid. Revisada el 2026-10-20 con las dos reglas del humano.

## 1. Diagnóstico (`infrastructure/database/parte_repository.py` salvo indicación; líneas de `dc03468`, §10)

- `worker_key_for_registro` (l.504): `emp-{empleado_ide}`, si no `nom-` + `_norm(leído)`,
  si no `sin-trabajador`. **No mira el recurso.**
- `crear_parte_manual` (l.3279) escribe `trabajador_nombre_leido = empleado_nombre` (nombre
  de Sigrid) y `empleado_line_no = 1` fijo; la IA guarda el leído del papel. Caso real
  (base `partes`, 15/10, obra 0678): IA `recurso_dni` extra 2, manual `recurso_manual`
  normal 8, mismo recurso y DNI ⇒ dos filas.
- **El recurso es lo común a toda línea casada; la ficha no.** sv3 casa contra recursos
  persona con `reside` = recurso y la ficha enlazada (`res.conide`) si la hay
  (`casado_recurso._a_match`); el portal igual (`recurso_catalog.asignacion_de`); el
  conciliador de sv3 (`recurso_conciliador._resuelve_recurso` → `elegir_recurso`) escribe
  `recurso_ide` en toda línea no congelada. Con y sin ficha del mismo recurso en una obra:
  **C1** el enlace ficha↔recurso cambia en Sigrid; **C2** líneas anteriores a F-035/F-036
  (casado por ficha; `_soltar_recurso` al reasignar por empleado); **C3** la vista del
  trabajador da de alta sin recurso (`templates/trabajador_detail.html` l.22–27 solo pasa
  `data-emp-ide` de una clave `emp-`; `static/app.js` `wireAddLine.setLock` l.2065 vacía
  `addline-emp-reside`), y sin ficha la línea nace sin casar.
- **E11**: un DNI con dos recursos persona en la misma empresa. sv3 desempata con el
  `reside` de la ficha (gemela F-023), pero el selector del portal ofrece los dos (F-035).
- **Empresa.** La línea no la guarda; el parte sí (`parte_documents.empresa`, F-023), NULL
  en los anteriores a F-023 y en los manuales (`crear_parte_manual` no la pone). «Por obra»
  ya la pinta (F-033: `list_obras` deduce `empresa_por_recurso` y decide con
  `application/services/empresas.py`); «Por persona» y la cabecera del trabajador, no.
- Heredan el arreglo: `list_workers`, `get_worker`, `list_obras`, `get_obra`, `alcance_parte`,
  `registro_ids_de_trabajador`, `reassign_empleado_by_worker_key`, `soft_delete_worker` y
  `persona_de` (sin DNI). A mano con el mismo fallo: `get_parte` (l.1449), `list_partes`
  (l.1361) y el «Ver» de «Nuevo parte» (`app.js` l.2017). Sin el problema: la matriz JS,
  `extras_por_jornada`, el reparto de F-045/F-046 (por `recurso_ide`) y la clave de obra.

## 2. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `services/partes-front/infrastructure/database/parte_repository.py` | §3: clave nueva, `get_parte`, `list_partes`, `get_worker` (ficha y empresa), `list_workers` (empresa y orden), `crear_parte_manual`, compatibilidad |
| `services/partes-front/interface_adapters/web/app.py` | `trabajador_detail`: redirección de R14 antes del 404 |
| `services/partes-front/templates/trabajador_detail.html` | «+ Añadir línea» con `data-emp-ide` de `detail.empleado_ide` y `data-emp-reside` (R19); empresa en la cabecera (R24) |
| `services/partes-front/templates/trabajadores_list.html` | columna «Empresa» con su filtro tras «Trabajador» (R23), como `obras_list.html` |
| `services/partes-front/static/app.js` | `wireAddLine` (`open` y `setLock` con `reside`); enlace «Ver» de «Nuevo parte» (R20) |
| `docs/ARCHITECTURE.md` | semántica 14: una frase con el orden de la clave de trabajador (R1) |
| Tests existentes de sv4 (R22) | solo el literal de la clave esperada; lista en §5 |
| **A crear**: los cinco `tests/test_f050_*.py` de §5 | nuevos |

**NO se tocan**: sv1, sv2, sv3, sv5, `infra/`, ambas `orm_models.py`, `application/**` de
sv4 (`empresas.py` se reutiliza tal cual), `infrastructure/sigrid/**`,
`templates/obra_detail.html` y `parte_detail.html`, `crear_extra_desde`,
`list_unmatched_workers`, `obra_key_for_registro`. `azure-apps/partes.md` no cambia.

## 3. Funciones (todas en `parte_repository.py`, capa infrastructure)

```python
def _clave_trabajador(*, casada: bool, empleado_ide: int | None,
                      recurso: int | None, nombre_leido: str | None) -> str:
    """R1-R2: rec- (casada con recurso) > emp- > nom- > sin-trabajador."""
def worker_key_for_registro(reg: ParteRegistroOrm) -> str:
    """Delega: casada=esta_casado(reg), recurso=recurso_ide o empleado_reside."""
def _empresa_por_recurso(regs: list[ParteRegistroOrm]) -> dict[int, set[int]]:
    """F-033 R4: el bucle de hoy de list_obras, extraido sin cambios."""
def fila_para_alta_manual(regs_doc: list[ParteRegistroOrm], clave: str,
                          nombre: str | None) -> tuple[int | None, str | None]:
    """R16-R17: (empleado_line_no, trabajador_nombre_leido) de una linea nueva."""
def clave_actual_de_clave_antigua(self, clave: str) -> str | None:  # metodo
    """R14-R15: la clave de hoy de las lineas que con la regla anterior daban `clave`."""
```

- **Clave.** `rec-` exige `casada`; con ficha y sin recurso ⇒ `emp-` (E12); `nom-` y
  `sin-trabajador` byte a byte como hoy (R3). `persona_de` no cambia de código (R11).
  `get_worker`: `empleado_ide` del detalle = el de la línea más reciente (`fecha_int`,
  `line_index`) que lo tenga, o None (R19). `get_parte`: `key = worker_key_for_registro(
  reg)`, o `("sin-trabajador", empleado_line_no)` (R6); `list_partes`:
  `{worker_key_for_registro(r) for r in doc.registros}` (mismas líneas, papelera incluida).
- **Empresa (R23–R26, DA11).** `list_obras` llama a `_empresa_por_recurso` (mismo
  resultado; lo vigila `tests/test_f033_columna_empresa.py`). `WorkerRow` y `WorkerDetail`
  ganan al final `empresas: list[int] = field(default_factory=list)` y `empresa_texto: str
  = "—"`, como `ObraRow`. `list_workers` hace el mapa con sus `regs` y, por grupo, junta
  `reg.document.empresa` y el recurso de cada línea (`recurso_ide`, si no
  `empleado_reside`) ⇒ `empresas_de_fila` y `texto_empresas`; orden `(0 si casada,
  _norm(nombre), empresas[0] o 10**9)`. `get_worker`, igual con el mapa de `todas` (ya
  cargadas para `_incompatibilidades`). Sin consultas nuevas ni Sigrid.
- **Plantillas.** `trabajadores_list.html`: `<th>Empresa</th>`, su `col-filter` («Filtrar
  empresa…») y `<td>{{ w.empresa_texto }}</td>`. Cabecera de `trabajador_detail.html`:
  `{% if detail.empresas %} · {{ detail.empresa_texto }}{% endif %}` tras la insignia.
- **Alta manual.** Herencia: entre `regs_doc` con `deleted_at_utc` NULL y clave = `clave`,
  la de menor `line_index` ⇒ `(su empleado_line_no, su trabajador_nombre_leido)`; si no
  hay, `(max(empleado_line_no no nulos de regs_doc) + 1, nombre)`, o `(1, nombre)`. En
  `crear_parte_manual`, por cada día, tras resolver `doc`: leer sus líneas (papelera
  incluida; documento nuevo ⇒ vacía), clave de la nueva con `_clave_trabajador(casada=
  empleado_ide is not None or metodo_empleado is not None, empleado_ide, recurso=
  empleado_reside, nombre_leido=empleado_nombre)` y el par para la incidencia y cada tipo
  de ese día (comparten fila).
- **Compatibilidad.** `clave_actual_de_clave_antigua` lee las líneas activas como
  `get_worker`; con `nom-X` filtra `"nom-" + _norm(leído).replace(" ", "_") == clave`; con
  `emp-E`, `empleado_ide == E` (E no entero ⇒ None). Si sus claves actuales son una sola y
  distinta de `clave`, la devuelve; si no, None. `app.py` `trabajador_detail`: si `detail
  is None`, clave `nom-`/`emp-` y destino ⇒ `RedirectResponse(f"/trabajadores/{destino}"
  + query, 307)`; si no, 404. Las acciones POST no tienen compatibilidad (R13).
- **Botón y JS.** `data-emp-ide="{{ detail.empleado_ide or '' }}"` y `data-emp-reside="{{
  worker_key[4:] if worker_key.startswith('rec-') else '' }}"`. `open` añade `reside:
  d.empReside` a `vals`; `setLock` escribe `(vals && vals.reside) || ""`. «Nuevo parte»:
  `verHref` = `rec-` + `emp-reside` si tiene valor; si no, `emp-` + `emp-ide`; si no,
  `/partes` (R20).

## 4. SQL

No hay SQL nuevo en el código ni cambios de esquema. Solo la consulta de M1 (§6).

## 5. Tests (desde `services/partes-front`, SQLite de `tests/dobles.py`)

- `tests/test_f050_clave.py`: R1 (cada rama; `recurso_ide` antes que `empleado_reside`;
  con y sin ficha da `rec-`), R2 (no casada con `reside` ⇒ `nom-`; `nombre_sin_dni`), R3
  (tabla de líneas no casadas: igual que una copia literal de la función de `dc03468` en el
  test), R4 (`inspect.getsource` de `get_parte`/`list_partes` sin agrupación a mano), R11.
- `tests/test_f050_vistas.py`: E1 y E8 ⇒ `get_obra` una fila con los dos `edit_*_id` (R5);
  `get_parte` un bloque y dos `sin-trabajador` de filas distintas separadas (R6);
  `list_partes` cuenta 1 (R7); `list_obras` y `alcance_parte` (R8); `list_workers`: E9 una
  fila, E10 dos (R9); `get_worker('rec-R')` con las dos obras de E9 y `rec-R1` sin líneas
  de R2 en E10 (R10); E4a y E11 dos filas; reasignar, papelera y `registro_ids_de_
  trabajador` por `rec-R` tocan las de R con y sin ficha y ninguna de R2 (R12); `nom-` y
  `emp-` antiguas actúan sobre 0 (R13).
- `tests/test_f050_empresa.py`: E10 con partes de las empresas 1 y 28 ⇒ «Ruesma» y
  «Porsan» en `list_workers`, en el HTML de `/trabajadores` (R23) y en la cabecera de cada
  `/trabajadores/rec-R` (R24); recurso en un parte manual y en otro con empresa ⇒ la
  deducida; sin nada ⇒ «—» en la lista y nada en la cabecera; `nom-` con partes de dos
  empresas ⇒ «Ruesma / Porsan» (R25); homónimos por empresa (R26); doble de Sigrid que
  falla si se le llama.
- `tests/test_f050_alta_manual.py`: E6 (hereda de la de menor `line_index`, ignora la
  papelera), E7 (máximo + 1, papelera incluida), documento nuevo ⇒ 1, incidencia y horas
  del mismo día comparten fila (R16–R17); resto de campos como hoy (R18).
- `tests/test_f050_portal.py` (TestClient como `test_f035_endpoints.py`): R14 307 desde
  `nom-` y desde `emp-` con `?modo=natural` conservado; R15 404 sin líneas y con dos claves;
  R19 plantilla (`data-emp-ide` de la ficha más reciente, `data-emp-reside` con `rec-`,
  vacío con `emp-`/`nom-`) y aserciones textuales del JS; R20 `verHref`; `node --check`.
- **Tests existentes (R22).** Experimento (2026-10-20, `dc03468`, función parcheada en
  memoria): **119 tests de 21 ficheros** esperan `emp-77` con recurso 501 (f003 ×5, f004 ×2,
  f015 ×3, f019, f022 ×2, f023, f024 ×2, f025 ×2, f028, f035_repositorio, f043; en `dev`,
  f046_marcas y f048_traza_portal). Solo cambian el literal (`emp-N` → `rec-R`) y
  `persona_de` sin DNI; otro cambio ⇒ `blocked`. `test_f033_columna_empresa.py`, intacto.

## 6. Verificaciones manuales (humano)

**M1 · antes de implementar** (base `partes`, solo lectura). Decide DA1 y DA1b: filas que
se unen por obra, fichas sin recurso (E12), casadas sin ficha ni recurso (se espera 0) y
DNIs con más de un recurso en una obra (E11):

```sql
WITH l AS (
  SELECT r.obra_ide, r.empleado_ide AS ficha,
         COALESCE(r.recurso_ide, r.empleado_reside) AS recurso,
         upper(replace(replace(COALESCE(r.empleado_dni, ''), '-', ''), ' ', '')) AS dni,
         COALESCE(upper(trim(r.trabajador_nombre_leido)), '') AS leido
  FROM parte_registros r JOIN parte_documents d ON d.id = r.document_id
  WHERE d.is_active AND r.deleted_at_utc IS NULL
    AND (r.empleado_ide IS NOT NULL OR r.empleado_match_method IN
         ('recurso_dni', 'recurso_nombre', 'recurso_manual')))
SELECT
 (SELECT count(*) FROM (SELECT 1 FROM l WHERE recurso IS NOT NULL GROUP BY obra_ide, recurso
   HAVING count(DISTINCT COALESCE('emp-' || ficha::text, 'nom-' || leido)) > 1) a)
   AS filas_que_se_unen,
 (SELECT count(*) FROM l WHERE ficha IS NOT NULL AND recurso IS NULL) AS ficha_sin_recurso,
 (SELECT count(*) FROM l WHERE ficha IS NULL AND recurso IS NULL) AS sin_ficha_sin_recurso,
 (SELECT count(*) FROM (SELECT 1 FROM l WHERE recurso IS NOT NULL AND dni <> ''
   GROUP BY obra_ide, dni HAVING count(DISTINCT recurso) > 1) b) AS dni_con_varios_recursos;
```

**Resultado de M1 (líder, 2026-10-20, solo lectura sobre la base `partes`)**: 560 líneas
casadas activas en 38 filas (obra, recurso); **1 fila que se une**; 0 fichas sin recurso
(E12); 0 casadas sin ficha ni recurso; 0 DNIs con varios recursos en una obra (E11); 36
recursos; 0 recursos sin empresa en sus partes (hoy no saldría ninguna «—», R25); 0 DNIs
en dos empresas.

Tras desplegar sv4 (`.\redeploy_partes.ps1 -Solo sv4` desde `infra/`, lo pide el humano):
**M2** obra 0678, periodo con el 15/10: el trabajador del caso en **una** fila «8+2»,
enlazada a `/trabajadores/rec-…`. **M3** detalle de ese parte: un bloque con las dos
líneas; el listado de partes cuenta un trabajador menos. **M4** una URL antigua `emp-…` y
una `nom-…` redirigen a la `rec-`. **M5** (opcional; escribe en la base `partes`, no en
Sigrid) «+ Añadir línea» desde la vista de un trabajador en un parte donde ya está ⇒ su
fila, casada y con su ficha (`empleado_line_no`, leído, `empleado_ide`, `empleado_reside`).
**M6** «Por persona» con la columna «Empresa»: una persona de Ruesma y de Porsan en dos
filas con su empresa, y cada vista con la suya en la cabecera; anotar cuántas «—».

## 7. Límite de servicio y gemelos

sv3 no tiene clave de trabajador: agrupa por recurso y día (F-045/F-046); sus conjuntos por
`empleado.ide or leído` (ingesta, normalizador) son del parte de la IA y no se tocan. sv5 no
agrupa por trabajador. La empresa sale de la base `partes` con la regla de F-033, solo de
sv4: **ni sv3 ni Sigrid, y no crece la lista de duplicación tolerada del `CLAUDE.md`.** El
aviso de jornada incompleta de la obra (`app.py` l.1131–1144) va por el nombre de la fila:
sigue valiendo (homónimos con distinta clave, caso previo, fuera).

## 8. Decisiones

- **DA1 · Clave — APROBADA por el humano el 2026-10-20 («ok»), opción A.** Recomendada **A**: `rec-{recurso}`
  para **toda** línea casada con recurso (con o sin ficha) > `emp-` (ficha sin recurso) >
  `nom-` > `sin-trabajador`. El recurso persona es de una sola empresa y común a toda línea
  casada (§1): una fila por (obra, empresa, persona) en E1, E8, E9 y E10, el grupo de sv3 y
  del reparto de F-046. La decisión del humano de hoy («en 2 empresas son 2 personas») es
  justo lo que A garantiza: dos recursos, dos claves. Coste: cambian las URL `emp-` (R14) y
  21 ficheros de tests (literales, R22). Descartadas: **la del 15/10** (`emp-` primero: C1–C3
  en dos filas); **empresa + DNI** (la línea no guarda la empresa y el documento manual
  nace sin ella; DNI en la URL y los logs; sin DNI hace falta el recurso); **ficha antes
  con un mapa ficha↔recurso** (la clave dependería de otras líneas o de Sigrid); nombre de
  Sigrid (homónimos).
- **DA1b · Dos recursos del mismo DNI en una empresa (E11) — APROBADA por el humano el
  2026-10-20 («ok»): dos filas, anomalía que se reasigna.** Con A, dos filas,
  como en Sigrid (cada recurso, su parte y su reparto). Recomendado: anomalía visible que se
  reasigna; si M1 da casos y el humano quiere una fila, otra feature (unir por DNI).
- **DA10 · Lista «Por persona» — APROBADA el 2026-10-20, opción (a)** («en la vista por
  persona, se juntan las obras»): una fila por clave = (empresa, persona) con todas sus
  obras (R9); `/trabajadores/{clave}` las separa por día y obra y «Por obra» da la fila por
  (obra, persona). Descartada (b): una fila por (obra, clave) también aquí.
- **DA11 · Empresa de la persona — APROBADA por el humano el 2026-10-20 («ok»): regla de
  F-033 sobre la base `partes`.** Recomendada **la
  regla de F-033 sobre la base `partes`** (§3): empresas no nulas de los partes de las
  líneas de la clave o, si ninguno la tiene, la de su recurso deducida de otros partes
  (un recurso persona es de una sola empresa). Fiable (sv3 fija `parte_documents.empresa`
  por membrete, obra o trabajadores, F-023, y sv3 y el selector eligen el recurso en la
  empresa de la obra), barata (datos ya cargados), sin Sigrid y probada en «Por obra». Sin
  empresa ⇒ «—» (R25): persona solo en partes manuales o anteriores a F-023 cuyo recurso no
  sale en partes con empresa, o `emp-` sin recurso en esos partes. En `nom-`/
  `sin-trabajador` es la de sus partes: dos («Ruesma / Porsan») avisan de homónimos o de
  líneas por casar. Descartadas: **catálogo de Sigrid** (`RecursoCatalog`,
  `_SQL_RECURSOS_ACTIVOS` trae `rescon.emp`): solo recursos de alta hoy, carga de toda la
  tabla con TTL y vacía si sigrid-api falla; **Sigrid por fila** (N llamadas); **empresa
  en la línea** (esquema, migración y sv3: fuera del límite); **`recurso_cif`** (es el
  DNI); **respaldo por obra** (cambia `empresas_de_fila` de F-033; R-d); **«—» siempre en
  `nom-`/`sin-trabajador`** (oculta un dato cierto y rompe la regla única con «Por obra»).
- **Aprobadas por el humano el 2026-10-20 («ok a lo demás»)**: **DA2** una sola función
  (`get_parte` y `list_partes` incluidas; las `sin-trabajador` del detalle, por fila); **DA3**
  el alta manual hereda fila y leído (R16) o va al final (R17), sin heredar `line_index`
  (F-037); **DA4** sin migración; **DA7** E5 visible; **DA8** estándar; **DA9** antes de F-049.
- **DA5 · Enlaces** — aprobada para `nom-`; con A **se amplía a `emp-`** (R14), **confirmada
  con DA1 el 2026-10-20**. Solo el `GET` y con destino único; las POST fallan seguras con 0 líneas (R13).
- **DA6 · La vista del trabajador pasa el recurso** (R19) — aprobada; con A **se amplía** (confirmada con DA1 el 2026-10-20) a
  la ficha y al «Ver» de «Nuevo parte» (R20). La persona fijada salta el filtro por empresa
  del selector (F-035); sv3 y sv5 verifican empresa y alta.

## 9. Riesgos

- **Dos empresas (E10)**: dos filas, distinguibles por la columna «Empresa» (R23–R24).
- **R-b** Un casado erróneo (dos personas en un recurso) sale en una fila; se reasigna.
- **R-c** Página con clave vieja: aprobar por ámbito se rechaza, borrar o reasignar no hace nada.
- **R-d** Persona sin empresa deducible ⇒ «—» (M6 las cuenta; el respaldo por obra, otra
  feature). Una `rec-` con dos empresas (su recurso en un parte de otra empresa, p. ej. vía
  DA6) es una anomalía visible que sv5 rechaza al aprobar.
- **R-e** E12 (ficha sin recurso) queda en `emp-` y separada de sus `rec-` hasta que el
  conciliador de sv3 le pone `recurso_ide`; M1 mide cuántas hay.

## 10. Lo fusionado en `dev` después de `dc03468` (hasta `ff2ed8e`)

**F-046** (marcas de fila en `trabajador_detail.html`, no en el botón ni la cabecera),
**F-048** y **F-051** no tocan la clave, el alta manual, `empresas.py` ni
`trabajadores_list.html`. Tras el rebase, repetir el recuento de R22.
