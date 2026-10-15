<!-- specs/F-050-misma-fila-para-el-mismo-trabajador/design.md -->
# F-050 · Misma fila para el mismo trabajador — Diseño

**Servicio: solo sv4** (`services/partes-front/`). La agrupación por trabajador es de
presentación y de las acciones del portal; sv3 y sv5 no tienen clave de trabajador (§7).
Sin esquema, sin SQL nuevo en la base, sin Sigrid. Rama
`feature/F-050-misma-fila-para-el-mismo-trabajador` (worktree `partes-wt-f050`).

## 1. Diagnóstico verificado (líneas de `dev` `dc03468`)

Fichero `infrastructure/database/parte_repository.py` salvo indicación:

- `worker_key_for_registro` (l.504): `emp-{empleado_ide}`, si no `nom-` + `_norm(leído)`,
  si no `sin-trabajador`. **No mira el recurso**: dos líneas casadas sin ficha del mismo
  recurso con leídos distintos dan dos claves.
- `crear_parte_manual` (l.3279; altas en l.3364 y l.3402) escribe
  `trabajador_nombre_leido = empleado_nombre` (el nombre de Sigrid, orden apellidos-nombre)
  y `empleado_line_no = 1` fijo. La línea de la IA guarda el leído del papel (orden
  nombre-apellidos). Caso real (base `partes`, 15/10, obra 0678): línea IA `recurso_dni`,
  extra 2; línea manual `recurso_manual`, normal 8; mismo recurso y DNI ⇒ dos filas.
- Usuarios de la clave (todos heredan el arreglo al cambiar la función): `list_workers`
  (l.873), `get_worker` (l.951), `list_obras` (conteo, l.1047), `get_obra` (matriz, l.1183),
  `alcance_parte` (F-043, l.1482), `registro_ids_de_trabajador` (ámbito de aprobar, l.1850
  vía `get_worker`), `reassign_empleado_by_worker_key` (l.2813), `soft_delete_worker`
  (l.3134) y `persona_de` (F-025, l.523, solo sin DNI).
- **Variantes escritas a mano** con el mismo fallo: `get_parte` (l.1449:
  `empleado_ide or leído or empleado_line_no`, sin normalizar) y `list_partes` (l.1361:
  `empleado_ide or leído`).
- **Segundo camino al mismo síntoma**: en `templates/trabajador_detail.html` (l.22–27) el
  botón «+ Añadir línea» solo pasa `data-emp-ide` (sacado de una clave `emp-`), y
  `static/app.js` `wireAddLine.setLock` (l.2065) pone `addline-emp-reside` a vacío. Para una
  persona sin ficha la línea nace **sin casar** (sin `reside` ni método) con clave
  `nom-{nombre de Sigrid}`: otra fila y además a Conciliar.
- Revisado y sin el problema: el JS de la matriz no agrupa (pinta las filas del servidor);
  `extras_por_jornada` ya agrupa por `recurso_ide`; `persona_de` con DNI; la clave de obra.
- `empleado_line_no = 1` fijo: solo afecta al **orden** del detalle del parte (se ordena por
  `(empleado_line_no, line_index)`: la persona añadida sale arriba, junto a la fila 1 del
  papel) y a la herramienta de diagnóstico `partes-persistencia/medir_casado_recursos.py`
  (`("fila", n)`). No choca con la pareja de F-037 (`document_id, line_index,
  empleado_line_no, fecha_int`): el `line_index` de la línea manual es nuevo.

## 2. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `services/partes-front/infrastructure/database/parte_repository.py` | §3: clave nueva, `get_parte`, `list_partes`, `crear_parte_manual`, método de compatibilidad |
| `services/partes-front/interface_adapters/web/app.py` | `trabajador_detail`: redirección de R12 antes del 404 |
| `services/partes-front/templates/trabajador_detail.html` | botón «+ Añadir línea»: `data-emp-reside` (R17) |
| `services/partes-front/static/app.js` | `wireAddLine`: `open` pasa `reside: d.empReside`; `setLock` lo escribe en `addline-emp-reside` |
| `docs/ARCHITECTURE.md` | semántica 14: una frase con el orden de la clave de trabajador (R1) |

**Ficheros a crear**: los cuatro tests de §5.

**Ficheros que NO se tocan**: `services/partes-persistencia/**`, `services/partes-transfer/**`,
`services/partes-api/**`, `services/partes-email/**`, ambas `orm_models.py`,
`application/services/congelacion.py`, `application/services/jornada_resolver.py`,
`infrastructure/sigrid/**`, `templates/obra_detail.html`, `templates/parte_detail.html`
(ya pintan lo que les da el repositorio), `crear_extra_desde` (ya clona leído y fila),
`list_unmatched_workers`/Conciliar, `obra_key_for_registro`, `infra/`. `azure-apps/partes.md`
no cambia: no cambia lo que sv4 expone a otros servicios (la URL es interna del portal).

## 3. Funciones (todas en `parte_repository.py`, capa infrastructure)

```python
def _clave_trabajador(*, empleado_ide: int | None, metodo: str | None,
                      reside: int | None, recurso_ide: int | None,
                      nombre_leido: str | None) -> str:
    """R1-R2: emp- > rec- (casada sin ficha con recurso) > nom- > sin-trabajador."""

def worker_key_for_registro(reg: ParteRegistroOrm) -> str:
    """Misma firma de hoy; delega en _clave_trabajador con los campos de la linea."""
```

- `rec-` solo si `empleado_ide is None and metodo in _METODOS_CASADO_SIN_FICHA` (el mismo
  criterio que `esta_casado`) y `reside` (si no, `recurso_ide`) no es None.
- La rama `nom-` y `sin-trabajador` se quedan byte a byte como hoy (R3).
- `persona_de` no cambia de código: hereda la clave nueva en su rama sin DNI (R9).

```python
def fila_para_alta_manual(regs_doc: list[ParteRegistroOrm], clave: str,
                          nombre: str | None) -> tuple[int | None, str | None]:
    """R14-R15: (empleado_line_no, trabajador_nombre_leido) de una linea nueva."""
```

- Herencia: entre `regs_doc` con `deleted_at_utc` NULL y clave = `clave`, la de menor
  `line_index` ⇒ `(su empleado_line_no, su trabajador_nombre_leido)`.
- Si no hay: `(max(empleado_line_no no nulos de regs_doc) + 1, nombre)`, o `(1, nombre)`.
- En `crear_parte_manual`, por cada día, **después** de resolver `doc` y antes de añadir:
  leer las líneas del documento (todas, papelera incluida; documento recién creado ⇒
  lista vacía), calcular la clave de la línea nueva con `_clave_trabajador(empleado_ide,
  metodo_empleado, empleado_reside, empleado_reside, empleado_nombre)` y usar el par
  devuelto en la incidencia y en cada tipo de ese día (las de un mismo día comparten fila).
- `get_parte`: `key = worker_key_for_registro(reg)`; si es `sin-trabajador`,
  `key = ("sin-trabajador", reg.empleado_line_no)` (R6). El orden de los grupos sigue siendo
  el de aparición tras ordenar por `(empleado_line_no or 0, line_index)`.
- `list_partes`: `empleados = {worker_key_for_registro(r) for r in doc.registros}` (mismo
  conjunto de líneas que hoy, papelera incluida, para no cambiar otra cosa).

```python
def clave_actual_de_clave_nombre(self, clave: str) -> str | None:
    """R12-R13: la clave de hoy de las lineas cuyo leido normalizado da `clave` (nom-)."""
```

- Lee las líneas activas (documento activo, sin papelera) como `get_worker`; filtra las que
  cumplen `"nom-" + _norm(leído).replace(" ", "_") == clave`; si sus claves actuales son
  exactamente una y distinta de `clave`, la devuelve; si no, `None`.
- `app.py` `trabajador_detail`: si `detail is None` y la clave empieza por `nom-` y el
  método devuelve destino ⇒ `RedirectResponse(f"/trabajadores/{destino}" + query, 307)`;
  si no, el 404 de hoy. Las acciones POST no tienen compatibilidad (R11).
- Plantilla: `data-emp-reside="{{ worker_key[4:] if worker_key.startswith('rec-') else '' }}"`
  junto a `data-emp-ide` (mismo patrón). JS: `setLock` escribe
  `(vals && vals.reside) || ""`; `open` añade `reside: d.empReside` a `vals`.

## 4. SQL

No hay SQL nuevo en el código ni cambios de esquema. Solo la consulta de solo lectura de
M1 (§6), que ejecuta el humano.

## 5. Tests previstos (desde `services/partes-front`, SQLite de `tests/dobles.py`)

- `tests/test_f050_clave.py`: R1 (los cuatro órdenes, `empleado_reside` antes que
  `recurso_ide`), R2 (no casada con `reside` ⇒ `nom-`; `nombre_sin_dni` sin reside), R3
  (tabla de líneas con ficha y no casadas: clave igual a la de una copia literal de la
  función de `dc03468` incluida en el test), R4 (`get_parte`/`list_partes` sin agrupación
  a mano: inspección del fuente con `inspect.getsource`), R9 (`persona_de`).
- `tests/test_f050_vistas.py`: E1 sembrado (dos líneas, leídos distintos, mismo recurso) ⇒
  `get_obra` una fila «8+2» con los dos `edit_*_id` (R5); `get_parte` un grupo, y dos
  `sin-trabajador` con filas distintas siguen separadas (R6); `list_partes` cuenta 1 (R7);
  `list_workers`, `get_worker('rec-R')`, `list_obras`, `alcance_parte` (R8); E4a da dos
  filas; reasignar, papelera y `registro_ids_de_trabajador` por `rec-R` tocan las dos
  líneas y no las de R2 (R10); una `nom-` antigua actúa sobre 0 (R11).
- `tests/test_f050_alta_manual.py`: E6 (hereda fila y leído de la de menor `line_index`,
  ignorando las de la papelera), E7 (máximo + 1, papelera incluida), documento nuevo ⇒ 1,
  incidencia + horas del mismo día comparten fila (R14–R15); el resto de campos igual que
  hoy, comparando con una llamada equivalente (R16).
- `tests/test_f050_portal.py` (TestClient como `test_f035_endpoints.py`): R12 redirección
  307 con `?modo=natural` conservado; R13 404 sin líneas y con dos claves; R17 plantilla
  con `data-emp-reside` para `rec-` y vacío para `emp-`/`nom-`, y aserciones textuales del
  JS (`reside: d.empReside`, `(vals && vals.reside)`), más `node --check static/app.js`.
- Tests existentes con claves `nom-` (`test_f004_endpoints_congelados.py`,
  `test_f035_repositorio.py`, `test_f035_endpoints.py`, `test_f040_alias.py`,
  `test_f025_*`): usan líneas **no casadas**, así que deben seguir verdes **sin tocarlos**.
  Si alguno falla, el implementer para y consulta (`blocked`), no lo reescribe.

## 6. Verificaciones manuales (humano)

**M1 · antes de desplegar** (base `partes`, solo lectura). Personas casadas sin ficha
partidas hoy en dos claves `nom-` por parte y por obra, homónimos casados fusionados hoy y
casadas sin ficha sin recurso (se espera 0; si no, ver DA1). Tildes aproximadas:

```sql
WITH l AS (
  SELECT r.document_id, r.obra_ide,
         COALESCE(r.empleado_reside, r.recurso_ide) AS recurso,
         COALESCE(regexp_replace(translate(upper(trim(r.trabajador_nombre_leido)),
           'ÁÀÉÈÍÌÓÒÚÙÜÑÇ', 'AAEEIIOOUUUNC'), '\s+', ' ', 'g'), '') AS leido
  FROM parte_registros r JOIN parte_documents d ON d.id = r.document_id
  WHERE d.is_active AND r.deleted_at_utc IS NULL AND r.empleado_ide IS NULL
    AND r.empleado_match_method IN ('recurso_dni', 'recurso_nombre', 'recurso_manual'))
SELECT
 (SELECT count(*) FROM (SELECT 1 FROM l WHERE recurso IS NOT NULL
   GROUP BY document_id, recurso HAVING count(DISTINCT leido) > 1) a) AS partidas_por_parte,
 (SELECT count(*) FROM (SELECT 1 FROM l WHERE recurso IS NOT NULL
   GROUP BY obra_ide, recurso HAVING count(DISTINCT leido) > 1) b) AS partidas_por_obra,
 (SELECT count(*) FROM (SELECT 1 FROM l WHERE recurso IS NOT NULL AND leido <> ''
   GROUP BY leido HAVING count(DISTINCT recurso) > 1) c) AS homonimos_fusionados,
 (SELECT count(*) FROM l WHERE recurso IS NULL) AS casadas_sin_recurso;
```

Tras desplegar sv4 (`.\redeploy_partes.ps1 -Solo sv4` desde `infra/`, lo pide el humano):

- **M2**: obra 0678, periodo que incluye el 15/10: el trabajador del caso sale en **una**
  fila con «8+2» el 15; su nombre enlaza a `/trabajadores/rec-…`.
- **M3**: detalle del parte del 15/10 (`/partes/d2141256…`): un solo bloque con las dos
  líneas; la cabecera «Partes» cuenta un trabajador menos que antes.
- **M4**: abrir la URL antigua `/trabajadores/nom-…` (la del nombre leído, se ve en el
  historial del navegador) ⇒ redirige a la `rec-`.
- **M5** (opcional; escribe en la base `partes`, no en Sigrid; lo decide el humano): desde
  la vista de un trabajador sin ficha, «+ Añadir línea» en un parte donde ya está ⇒ la
  línea sale en su fila, casada; SQL de solo lectura: `SELECT id, empleado_line_no,
  trabajador_nombre_leido, empleado_match_method, empleado_reside FROM parte_registros
  WHERE document_id = '<id>' ORDER BY line_index;` ⇒ fila y leído heredados. Luego se
  manda a la papelera si no era una línea real.

## 7. Límite de servicio y gemelos

sv3 no tiene clave de trabajador: agrupa por recurso y día para el reparto (F-045) y sus
únicos conjuntos por `empleado.ide or leído` son el contador del resultado de la ingesta
(`persist_parte_pipeline.py` l.197) y un log del normalizador, sobre el parte de la IA, donde
no hay líneas manuales: no se tocan. sv5 no agrupa por trabajador. **No crece la lista de
duplicación tolerada del `CLAUDE.md`.** El aviso de jornada incompleta de la vista de obra
(`app.py` l.1131–1144) va por el **nombre** de la fila; en E1 las dos líneas llevan el mismo
nombre de Sigrid, así que funciona; homónimos con distinta clave es un caso previo, fuera.

## 8. Decisiones (con recomendación) y alternativas descartadas

- **DA1 · Orden de la clave** — `emp-` > `rec-` > `nom-` > `sin-trabajador`. Recomendado:
  cambia solo la clave de las casadas sin ficha (las URL de todos los demás siguen
  valiendo) y un recurso persona (`res.cla = 1`) es una persona. Descartadas: **DNI
  primero** para todos (cambia todas las URL `emp-` y fusiona fichas de dos empresas: otra
  feature); **recurso primero** también con ficha (mismo coste); **`dni-` como tercer
  paso** (toda casada sin ficha lleva recurso: F-036 en sv3, F-035 en el portal y
  `_soltar_recurso` + `reside` al reasignar; M1 `casadas_sin_recurso` lo confirma; si no
  diera 0, se reconsidera); clave por **nombre de Sigrid** (homónimos).
- **DA2 · Una sola función** — `get_parte` y `list_partes` pasan a `worker_key_for_registro`;
  la del detalle conserva la separación por fila de las `sin-trabajador`. Ventaja añadida:
  el detalle del parte normaliza tildes y mayúsculas como el calendario.
- **DA3 · Alta manual hereda fila y leído** de la persona en ese parte (R14) y, si no está,
  va a una fila nueva al final (R15) en vez de la 1 fija. Con la clave nueva la agrupación
  ya no depende de esto, pero: el detalle del parte pone la línea junto a su fila del
  papel; reasignar por clave aprende alias de los leídos (`reassign_empleado_by_worker_key`)
  y un «leído» que es el nombre de Sigrid enseñaría un alias que nadie leyó; y es lo que ya
  hace `crear_extra_desde`. Descartado heredar `line_index` (rompería la pareja de F-037).
- **DA4 · Sin migración** — es agrupación en lectura; lo ya guardado se ve bien en cuanto se
  despliegue. Las líneas manuales antiguas conservan fila 1 y el leído de Sigrid (solo
  orden del detalle); corregirlas es fuera de alcance.
- **DA5 · Compatibilidad de enlaces** — solo en el `GET` de la vista (R12) y solo si el
  destino es único; las acciones POST fallan seguro con 0 líneas (R11), igual que una
  página desfasada hoy. Alternativa: sin redirección (404); se puede quitar si el humano
  prefiere menos código.
- **DA6 · Vista del trabajador pasa el recurso** (R17) — mismo síntoma por otro camino (§1).
  Riesgo: la persona fijada salta el filtro por empresa del selector (F-035); sv3 y sv5 ya
  verifican empresa y alta del recurso al conciliar y al registrar.
- **DA7 · E5 es un cambio visible**: una casada sin ficha y una sin casar con el mismo
  leído dejan de compartir fila (hoy coinciden por casualidad del nombre). Es lo que ya pasa
  con quien tiene ficha, y la fila sin casar es la tarea de Conciliar.
- **DA8 · Rigor estándar** — solo sv4, sin esquema, sin Sigrid, todo deshacible (reasignar
  tiene deshacer, la papelera se restaura). Lo más delicado es que la clave define el
  conjunto de las acciones masivas y el bloqueo de F-025 sin DNI; los tests de R10 y R9 lo
  cubren. Si el humano lo quiere crítico, solo cambia la campaña de mutación (completa).
- **DA9 · Orden con otras ramas** — **F-046** (reajuste) y **F-047** (parte en espera) no
  usan la clave; conflictos solo textuales (`parte_repository.py`, `app.py`,
  `trabajador_detail.html` en líneas lejanas, `features.json`, `BACKLOG.md`). **F-049**
  (editor de celda, en especificación) define la celda con `worker_key_for_registro` y
  clona `empleado_line_no` en sus líneas nuevas: con F-050 primero, la celda de E1 ya es
  una y su «Ord. (nueva)» cae en la misma fila; recomendado **F-050 antes de F-049**. Si
  F-049 entra antes, F-050 no cambia: la celda hereda la clave nueva sin tocar F-049.

## 9. Riesgos

- **R-a** Persona con recursos en dos empresas: dos `rec-` en la lista global (como hoy dos
  `emp-` con dos fichas). Fuera de alcance.
- **R-b** Un casado erróneo (dos personas en el mismo recurso) se ve en una fila: igual que
  hoy con `emp-`; se corrige reasignando.
- **R-c** Páginas abiertas antes del despliegue con una clave `nom-` vieja: la aprobación por
  ámbito se rechaza («página desfasada») y borrar o reasignar no hace nada; se recarga.
