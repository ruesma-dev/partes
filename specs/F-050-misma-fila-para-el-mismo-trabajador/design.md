<!-- specs/F-050-misma-fila-para-el-mismo-trabajador/design.md -->
# F-050 · Misma fila para el mismo trabajador — Diseño

**Solo sv4** (`services/partes-front/`): la agrupación por trabajador es del portal (§7).
Sin esquema, SQL nuevo ni Sigrid. Revisada el 2026-10-20 con la regla del humano «una línea
por obra, empresa y persona» (requirements).

## 1. Diagnóstico (`infrastructure/database/parte_repository.py` salvo indicación; líneas de `dc03468`, §10)

- `worker_key_for_registro` (l.504): `emp-{empleado_ide}`, si no `nom-` + `_norm(leído)`,
  si no `sin-trabajador`. **No mira el recurso.**
- `crear_parte_manual` (l.3279) escribe `trabajador_nombre_leido = empleado_nombre` (nombre
  de Sigrid) y `empleado_line_no = 1` fijo; la IA guarda el leído del papel. Caso real
  (base `partes`, 15/10, obra 0678): IA `recurso_dni` extra 2, manual `recurso_manual`
  normal 8, mismo recurso y DNI ⇒ dos filas.
- **Quién pone ficha y recurso en una línea casada.** sv3 casa contra recursos persona y
  guarda la ficha enlazada (`res.conide`) si la hay, siempre con `reside` = recurso
  (`casado_recurso._a_match`); el portal hace lo mismo al elegir recurso
  (`recurso_catalog.asignacion_de`); el conciliador de sv3 (`recurso_conciliador.
  _resuelve_recurso` → `elegir_recurso` con DNI, ficha y `reside`) escribe `recurso_ide` en
  toda línea no congelada. Por eso **el recurso es lo común a toda línea casada**, y la
  ficha no: una persona puede tener en la misma obra líneas con y sin ficha del mismo
  recurso:
  - **C1** — el enlace ficha↔recurso cambia en Sigrid (un recurso sin ficha al que luego se
    le crea): las líneas viejas quedan `recurso_*` sin ficha y las nuevas con ficha.
  - **C2** — líneas anteriores a F-035/F-036 (sv3 casaba por ficha; reasignar por empleado
    soltaba el recurso, `_soltar_recurso`) junto a líneas casadas por recurso.
  - **C3** — la vista del trabajador da de alta sin recurso: `templates/trabajador_detail.
    html` (l.22–27) solo pasa `data-emp-ide` sacado de una clave `emp-`, y `static/app.js`
    `wireAddLine.setLock` (l.2065) vacía `addline-emp-reside`; sin ficha la línea nace sin
    casar (`nom-{nombre de Sigrid}`, otra fila y a Conciliar).
- **E11**: un DNI con dos recursos persona en la misma empresa. sv3 desempata con el
  `reside` de la ficha (gemela F-023), pero el selector del portal ofrece los dos (F-035).
- Heredan el arreglo: `list_workers`, `get_worker`, `list_obras`, `get_obra`,
  `alcance_parte`, `registro_ids_de_trabajador`, `reassign_empleado_by_worker_key`,
  `soft_delete_worker` y `persona_de` (sin DNI). A mano con el mismo fallo: `get_parte`
  (l.1449), `list_partes` (l.1361) y el enlace «Ver» de «Nuevo parte» (`app.js` l.2017).
- Sin el problema: el JS de la matriz, `extras_por_jornada` y el reparto de F-045/F-046
  (agrupan por `recurso_ide`), la clave de obra.

## 2. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `services/partes-front/infrastructure/database/parte_repository.py` | §3: clave nueva, `get_parte`, `list_partes`, `get_worker` (ficha del grupo), `crear_parte_manual`, compatibilidad |
| `services/partes-front/interface_adapters/web/app.py` | `trabajador_detail`: redirección de R14 antes del 404 |
| `services/partes-front/templates/trabajador_detail.html` | botón «+ Añadir línea»: `data-emp-ide` de `detail.empleado_ide` y `data-emp-reside` (R19) |
| `services/partes-front/static/app.js` | `wireAddLine` (`open` y `setLock` con `reside`); enlace «Ver» de «Nuevo parte» (R20) |
| `docs/ARCHITECTURE.md` | semántica 14: una frase con el orden de la clave de trabajador (R1) |
| Tests existentes de sv4 (R22) | solo el literal de la clave esperada; lista en §5 |

**Ficheros a crear**: los cuatro tests de §5.

**NO se tocan**: sv1, sv2, sv3, sv5, `infra/`, ambas `orm_models.py`, `application/**` de
sv4, `infrastructure/sigrid/**`, `templates/obra_detail.html`, `parte_detail.html` y
`trabajadores_list.html` (pintan lo del repositorio), `crear_extra_desde`,
`list_unmatched_workers`, `obra_key_for_registro`. `azure-apps/partes.md` no cambia.

## 3. Funciones (todas en `parte_repository.py`, capa infrastructure)

```python
def _clave_trabajador(*, casada: bool, empleado_ide: int | None,
                      recurso: int | None, nombre_leido: str | None) -> str:
    """R1-R2: rec- (casada con recurso) > emp- > nom- > sin-trabajador."""

def worker_key_for_registro(reg: ParteRegistroOrm) -> str:
    """Misma firma de hoy; delega con casada=esta_casado(reg) y
    recurso = reg.recurso_ide si no es None, si no reg.empleado_reside."""
```

- `rec-` exige `casada`; con ficha y sin recurso ⇒ `emp-` (E12); la rama `nom-` y
  `sin-trabajador` byte a byte como hoy (R3). `persona_de` no cambia de código (R11).
- `get_worker`: `empleado_ide` del detalle = el de la línea más reciente
  (`fecha_int`, `line_index`) que lo tenga, o None (R19); el resto, como hoy.

```python
def fila_para_alta_manual(regs_doc: list[ParteRegistroOrm], clave: str,
                          nombre: str | None) -> tuple[int | None, str | None]:
    """R16-R17: (empleado_line_no, trabajador_nombre_leido) de una linea nueva."""
```

- Herencia: entre `regs_doc` con `deleted_at_utc` NULL y clave = `clave`, la de menor
  `line_index` ⇒ `(su empleado_line_no, su trabajador_nombre_leido)`. Si no hay:
  `(max(empleado_line_no no nulos de regs_doc) + 1, nombre)`, o `(1, nombre)`.
- En `crear_parte_manual`, por cada día, tras resolver `doc`: leer sus líneas (todas,
  papelera incluida; documento nuevo ⇒ vacía), clave de la línea nueva con
  `_clave_trabajador(casada=empleado_ide is not None or metodo_empleado is not None,
  empleado_ide, recurso=empleado_reside, nombre_leido=empleado_nombre)` y usar el par en la
  incidencia y en cada tipo de ese día (comparten fila).
- `get_parte`: `key = worker_key_for_registro(reg)`, o `("sin-trabajador",
  empleado_line_no)` (R6). `list_partes`: `{worker_key_for_registro(r) for r in
  doc.registros}` (mismas líneas que hoy, papelera incluida).

```python
def clave_actual_de_clave_antigua(self, clave: str) -> str | None:
    """R14-R15: la clave de hoy de las lineas que con la regla anterior daban `clave`."""
```

- Lee las líneas activas como `get_worker`; con `nom-X` filtra
  `"nom-" + _norm(leído).replace(" ", "_") == clave`; con `emp-E`, `empleado_ide == E`
  (E entero; si no lo es, None). Si sus claves actuales son exactamente una y distinta de
  `clave`, la devuelve; si no, None.
- `app.py` `trabajador_detail`: si `detail is None`, la clave empieza por `nom-` o `emp-` y
  hay destino ⇒ `RedirectResponse(f"/trabajadores/{destino}" + query, 307)`; si no, 404.
  Las acciones POST no tienen compatibilidad (R13).
- Plantilla: `data-emp-ide="{{ detail.empleado_ide or '' }}"` y `data-emp-reside="{{
  worker_key[4:] if worker_key.startswith('rec-') else '' }}"`. JS: `open` añade
  `reside: d.empReside` a `vals`; `setLock` escribe `(vals && vals.reside) || ""`. «Nuevo
  parte»: `verHref` = `rec-` + `emp-reside` si tiene valor; si no, `emp-` + `emp-ide`; si
  no, `/partes` (R20).

## 4. SQL

No hay SQL nuevo en el código ni cambios de esquema. Solo la consulta de M1 (§6).

## 5. Tests (desde `services/partes-front`, SQLite de `tests/dobles.py`)

- `tests/test_f050_clave.py`: R1 (cada rama; `recurso_ide` antes que `empleado_reside`;
  con y sin ficha da `rec-`), R2 (no casada con `reside` ⇒ `nom-`; `nombre_sin_dni`), R3
  (tabla de líneas no casadas: igual que una copia literal de la función de `dc03468` en el
  test), R4 (`inspect.getsource` de `get_parte`/`list_partes` sin agrupación a mano), R11.
- `tests/test_f050_vistas.py`: E1 y E8 sembrados ⇒ `get_obra` una fila con los dos
  `edit_*_id` (R5); `get_parte` un bloque y dos `sin-trabajador` de filas distintas
  separadas (R6); `list_partes` cuenta 1 (R7); `list_obras` y `alcance_parte` (R8);
  `list_workers`: E9 una fila, E10 dos (R9); `get_worker('rec-R')` con las dos obras de E9
  (R10); E4a y E11 dos filas; reasignar, papelera y `registro_ids_de_trabajador` por
  `rec-R` tocan las líneas de R con y sin ficha y ninguna de R2 (R12); `nom-` y `emp-`
  antiguas actúan sobre 0 (R13).
- `tests/test_f050_alta_manual.py`: E6 (hereda de la de menor `line_index`, ignora la
  papelera), E7 (máximo + 1, papelera incluida), documento nuevo ⇒ 1, incidencia y horas
  del mismo día comparten fila (R16–R17); resto de campos como hoy (R18).
- `tests/test_f050_portal.py` (TestClient como `test_f035_endpoints.py`): R14 307 desde
  `nom-` y desde `emp-` con `?modo=natural` conservado; R15 404 sin líneas y con dos claves;
  R19 plantilla (`data-emp-ide` de la ficha más reciente, `data-emp-reside` con `rec-`,
  vacío con `emp-`/`nom-`) y aserciones textuales del JS; R20 `verHref`; `node --check`.
- **Tests existentes (R22).** Experimento del spec-author (2026-10-20, `dc03468`, función
  parcheada en memoria, árbol intacto): **119 tests de 21 ficheros** fallan, porque sus
  fixtures casan con ficha y recurso (ficha 77, recurso 501) y esperan `emp-77` (f003 ×5,
  f004 ×2, f015 ×3, f019, f022 ×2, f023, f024 ×2, f025 ×2, f028, `test_f035_repositorio`,
  f043; en `dev`, también `test_f046_marcas` y `test_f048_traza_portal`). Se cambia
  **solo** el literal de la clave (`emp-N` → `rec-R` de su fixture) y la esperanza de
  `persona_de` sin DNI; otro cambio ⇒ `blocked`. El reviewer lo mira con `git diff -U0`.

## 6. Verificaciones manuales (humano)

**M1 · antes de implementar** (base `partes`, solo lectura, cifras aproximadas). Decide DA1
y DA1b: filas que F-050 une por obra, fichas sin recurso (E12), casadas sin ficha ni recurso
(se espera 0) y DNIs con más de un recurso en una obra (E11):

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

Tras desplegar sv4 (`.\redeploy_partes.ps1 -Solo sv4` desde `infra/`, lo pide el humano):

- **M2**: obra 0678, periodo con el 15/10: el trabajador del caso en **una** fila «8+2»; su
  nombre enlaza a `/trabajadores/rec-…`.
- **M3**: detalle del parte del 15/10 de la 0678: un solo bloque con las dos líneas; el
  listado de partes cuenta un trabajador menos que antes.
- **M4**: una URL antigua `/trabajadores/emp-…` y una `/trabajadores/nom-…` (historial del
  navegador) redirigen a la `rec-`.
- **M5** (opcional; escribe en la base `partes`, no en Sigrid): desde la vista de un
  trabajador, «+ Añadir línea» en un parte donde ya está ⇒ sale en su fila, casada y con su
  ficha si la tiene (`SELECT id, empleado_line_no, trabajador_nombre_leido, empleado_ide,
  empleado_reside FROM parte_registros WHERE document_id = '<id>' ORDER BY line_index;`).

## 7. Límite de servicio y gemelos

sv3 no tiene clave de trabajador: agrupa por recurso y día (F-045/F-046), y sus conjuntos por
`empleado.ide or leído` (contador de la ingesta, log del normalizador) son del parte de la
IA: no se tocan. sv5 no agrupa por trabajador. **No crece la lista de duplicación tolerada
del `CLAUDE.md`.** El aviso de jornada incompleta de la vista de obra (`app.py`
l.1131–1144) va por el **nombre** de la fila: con una fila por clave sigue valiendo;
homónimos con distinta clave es un caso previo, fuera.

## 8. Decisiones

- **DA1 · Clave — ABIERTA (revisada el 2026-10-20).** Recomendada **A**: `rec-{recurso}`
  para **toda** línea casada con recurso (con o sin ficha) > `emp-` (ficha sin recurso) >
  `nom-` > `sin-trabajador`. El recurso persona es de una sola empresa y es lo común a toda
  línea casada (§1): da una fila por (obra, empresa, persona) en E1, E8, E9 y E10, y es el
  mismo grupo que ya usan sv3 y el reparto de F-046 (`recurso_ide`, día). Coste: cambian
  las URL `emp-` de casi todos (R14 las redirige) y 21 ficheros de tests (solo literales,
  R22). Descartadas: **la de la spec del 15/10** (`emp-` antes que `rec-`: deja en dos
  filas C1–C3, contra la regla); **empresa + DNI** (la línea no guarda la empresa del
  recurso y el documento manual nace sin `empresa`; pondría el DNI en la URL y en los logs;
  sin DNI hace falta igualmente el recurso); **ficha antes, con un mapa ficha↔recurso
  sacado de las demás líneas o del catálogo de Sigrid** (la clave de una línea dependería
  de otras o de que Sigrid responda); nombre de Sigrid (homónimos).
- **DA1b · Dos recursos persona del mismo DNI en una empresa (E11) — ABIERTA.** Con A
  salen dos filas, una por recurso, como en Sigrid (cada recurso lleva su parte y su
  reparto). Recomendado: anomalía visible que se arregla reasignando; si M1 da casos y el
  humano quiere una fila, otra feature (unir por DNI dentro de la obra).
- **DA10 · Lista «Por persona» — ABIERTA.** La regla literal («una línea por obra») choca
  con esta lista, que hoy agrega todas las obras de una persona. Recomendado **(a)**: una
  fila por (empresa, persona) = clave, con sus obras dentro (`/trabajadores/{clave}` las
  separa por día y obra); la vista «Por obra» ya da una fila por (obra, persona).
  Alternativa (b): una fila por (obra, clave) también aquí; duplica «Por obra» y pierde el
  total por persona.
- **Aprobadas por el humano el 2026-10-20 («ok a lo demás»)**, sin cambio con la revisión:
  **DA2** una sola función (`get_parte` y `list_partes` incluidas; las `sin-trabajador` del
  detalle siguen por fila); **DA3** el alta manual hereda fila y leído (R16) o va al final
  (R17), como `crear_extra_desde`, sin heredar `line_index` (pareja de F-037); **DA4** sin
  migración; **DA7** E5 es un cambio visible; **DA8** rigor estándar (lo delicado, las
  acciones masivas y F-025 sin DNI, lo cubren R12 y R11); **DA9** F-050 antes de F-049.
- **DA5 · Compatibilidad de enlaces** — aprobada para `nom-`; con A **se amplía a `emp-`**
  (R14), lo que el humano confirma junto con DA1. Solo el `GET` y solo con destino único;
  las acciones POST fallan seguras con 0 líneas (R13).
- **DA6 · La vista del trabajador pasa el recurso** (R19) — aprobada; con A **se amplía** a
  pasar también la ficha del grupo (antes salía de la clave `emp-`) y al enlace de «Nuevo
  parte» (R20). Riesgo: la persona fijada salta el filtro por empresa del selector (F-035);
  sv3 y sv5 verifican empresa y alta.

## 9. Riesgos

- **Dos empresas (E10) ya no es un riesgo**: dos filas es lo correcto por la regla.
- **R-b** Un casado erróneo (dos personas en un recurso) sale en una fila; se reasigna.
- **R-c** Páginas abiertas con una clave vieja: aprobar por ámbito se rechaza («página
  desfasada»), borrar o reasignar no hace nada; se recarga.
- **R-d** En «Por persona», E10 da dos filas con el mismo nombre (se distinguen por código,
  no por empresa, que la línea no guarda). Fuera de alcance.
- **R-e** E12 (ficha sin recurso) queda en `emp-` y separada de sus `rec-` hasta que el
  conciliador de sv3 le pone `recurso_ide`; M1 mide cuántas hay.

## 10. Lo fusionado en `dev` después de `dc03468` (hasta `ff2ed8e`)

- **F-046** (reajuste al aprobar): `RepartoPendienteOrm` por (`recurso_ide`, `fecha_int`),
  `registros_con_reparto` y `con_reparto`/`dias_reparto` en el contexto de
  `trabajador_detail`; toca filas de `trabajador_detail.html`, no el botón «+ Añadir
  línea». No usa la clave de trabajador y agrupa por recurso, igual que la clave A.
- **F-048** (`horas_extra_leidas` y su etiqueta) y **F-051** (solo sv2/sv3) no tocan la
  clave ni `empleado_line_no` de sv4. `worker_key_for_registro`, `persona_de` y
  `crear_parte_manual` son idénticas en `dev` (l.524, l.534, l.3641). Tras el rebase
  (implementer), repetir el recuento de R22 sobre `dev`.
