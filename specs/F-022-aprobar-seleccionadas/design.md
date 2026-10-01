<!-- specs/F-022-aprobar-seleccionadas/design.md -->
# F-022 · Diseño técnico

## 0. Resumen para el humano (decisiones a validar, detalle en §8)

- **DA1** Sin nada marcado, el botón aprueba **lo visible** («Aprobar visibles
  (N)»; sin filtros, «Aprobar todo (N)»). Con algo marcado, **solo lo
  marcado** («Aprobar seleccionadas (N)»).
- **DA2** Marcado + oculto por un filtro **no** se aprueba; se avisa.
- **DA3** Una sola selección: las casillas son la cara visible de la
  selección Ctrl/Shift+clic que ya existe (la de editar partida en bloque).
- **DA4/DA5** Casilla dentro de la celda Fecha (sin columna nueva) y botones
  «Seleccionar visibles» / «Quitar selección» sobre la tabla.
- **DA7** El servidor exige que los ids pertenezcan a la vista y, si no,
  **rechaza toda la petición** (422), no aprueba «lo que pueda».
- **DA8 · Hallazgo**: sv5 escribe todas las líneas de una petición en el
  parte de **una** obra, la de la primera línea. Hoy «Aprobar visibles» en
  la ficha de una persona con líneas de varias obras **las escribiría en la
  obra equivocada**. F-022 lo rechaza (422 con desglose por obra) en toda
  petición. **Aviso inmediato**: hasta desplegar, en la ficha de persona
  filtrar la columna Obra antes de «Aprobar visibles». M1 (§9) mira si ya
  ocurrió.
- **DA14** Solo **sv4**; sv5 sin cambios. Rigor `estandar`.

## 1. Servicios que toca y por qué

| Servicio | Por qué | Qué no hace |
|---|---|---|
| sv4 | Dueño de las vistas, de la selección en el navegador y de construir el payload de registro (`_payload_registro`, `lineas_para_registro`) | No toca el esquema ni la cola |

**sv5 no cambia** (verificado): `PeticionIn` es `{obra, lineas, pisar_claves,
usuario}`; preflight, conflictos y escritura operan solo sobre las `lineas`
recibidas; el mensaje de `q-transfer` y el resultado por línea no cambian.
Basta con que sv4 envíe menos líneas. El guardia de una obra (R17) va en sv4
porque es quien elige la obra del payload. sv3 no se toca.

## 2. Qué hace hoy (diagnóstico)

- **Obra** (`obra_detail.html`): «✓ Aprobar todo» envía `{obra_key, period,
  mode}`; el servidor resuelve **todas** las líneas del periodo
  (`registro_ids_de_obra`). **Ignora** filtros de columna y el filtro por
  casillas de la matriz: es el caso que reporta el humano.
- **Persona** (`trabajador_detail.html`): «✓ Aprobar visibles» ya envía los
  `registro_ids` de las filas sin `filtered-day` ni `display:none`. Pero la
  tabla de persona pinta **todas** sus líneas (todos los meses y obras; el
  selector de mes solo mueve el calendario) y el servidor no comprueba nada
  de esos ids salvo papelera y exclusiones de F-024.
- **Selección**: existe `PartidaSel` (Ctrl/Shift+clic, barra `.bulk-bar` con
  «Editar partida», «Borrar», «Quitar selección»), sin casillas, local al
  segundo IIFE de `app.js`; el IIFE de aprobar no la ve. El rango de
  Shift+clic incluye filas ocultas.
- **Obra del payload**: `lineas_para_registro` toma la obra de la primera
  línea leída (orden de la BBDD) y no comprueba que el resto sea de la misma.

## 3. Encaje y flujo

Navegador: conjunto = `seleccionadas ∩ visibles` si hay selección; si no,
`visibles` → `aprobar({registro_ids, ambito}, alcanceTexto)` → preflight →
(encolar | ejecutar) con la misma petición. Servidor: `_payload_registro` →
si hay `ambito`, `_validar_ambito` (R13–R15) → `lineas_para_registro`
(exclusiones F-024, R16) → guardia de una obra (R17) → payload de siempre a
sv5 (R21). Sin `ambito`, como hoy + R17 (R18).

## 4. Ficheros

### Crear

| Ruta | Contenido |
|---|---|
| `services/partes-front/tests/test_f022_aprobar_seleccion.py` | R13–R21 (endpoints con `TestClient`, repositorio SQLite, dobles de sv5, publisher y calendario de F-003/F-024) |
| `services/partes-front/tests/test_f022_vistas_seleccion.py` | R1, R10, R12 y R5 en lo estático: HTML de las dos vistas (casilla por fila, botones de selección, `data-*` del ámbito) y comprobaciones mínimas de `app.js` (patrón `test_f004_r16`) |

### Modificar

| Ruta | Qué cambia |
|---|---|
| `services/partes-front/infrastructure/database/parte_repository.py` | `registro_ids_de_trabajador(worker_key)`; `lineas_para_registro` añade la clave `obras` (§5.1). `registro_ids_de_obra` no cambia |
| `services/partes-front/interface_adapters/web/app.py` | `_payload_registro`: rama `ambito` (R13–R15) y guardia de una obra (R17); constantes `MAX_IDS_APROBACION = 5000` y `VISTAS_AMBITO`. Sin endpoints nuevos |
| `services/partes-front/templates/obra_detail.html` | `#aprobar-todo` conserva `id` y `data-obra-key/period/mode`, añade `data-vista="obra"`; casilla `sel-linea` en `cell-fecha`; barra de selección en la cabecera del panel |
| `services/partes-front/templates/trabajador_detail.html` | Igual, con `data-vista="trabajador"` y `data-worker-key` |
| `services/partes-front/static/app.js` | §5.2 |
| `services/partes-front/static/styles.css` | Estilo mínimo de `.sel-linea`, `.sel-tools` y botón deshabilitado |
| `services/partes-front/tests/test_f024_borrado_sigrid.py` | `test_f024_r22_payload_repo_sin_ids` compara el dict entero: se añade `"obras": []` con comentario (R22). Nada más |
| `docs/ARCHITECTURE.md` | Semántica 5: una petición de registro es de **una** obra; sv4 rechaza lotes de varias. Semántica 10: masivas por selección/visibles (≤ 6 líneas netas) |
| `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` | Líneas que citan «Aprobar todo»/«Aprobar visibles»: selección explícita y regla de una obra (no cambia lo expuesto entre servicios) |

### No se tocan

`services/partes-transfer/**` (sv5), `services/partes-persistencia/**`,
`orm_models.py` (las dos copias), `congelacion.py`, `resultado_sigrid.py`,
`resultado_consumer.py`, `comprobacion_sigrid.py`, `registro_ids_de_obra`,
las exclusiones de `lineas_para_registro` (F-024 R22), los endpoints
`/api/sigrid/comprobar` y `/api/aprobar/estado`, `parte_detail.html`, `infra/`.

## 5. Clases y funciones

### 5.1 Repositorio (infrastructure)

```python
def registro_ids_de_trabajador(self, worker_key: str) -> list[int]
def lineas_para_registro(self, registro_ids, *, incluir_borradas=False) -> dict
    # + "obras": list[{"clave", "codigo", "nombre", "lineas": int}]
```

- `registro_ids_de_trabajador`: `[v.id for v in get_worker(key).registros]`
  (`[]` si no existe). Son las filas de la tabla de persona (DA12).
- `obras`: agrupa **las líneas que viajan** (no las excluidas) por
  `obra_key_for_registro(r)`, en orden de clave; `[]` sin líneas. `obra`
  sigue saliendo de la primera línea que viaja (con una obra, da igual).

### 5.2 Portal (`interface_adapters/web/app.py`)

`_payload_registro(body, *, actor)` mantiene su firma y su retorno
`(payload, excluidas) | JSONResponse`:

1. `ids` = `registro_ids` deduplicados. Si `body.ambito` existe →
   `_validar_ambito(ambito, ids)`; si devuelve respuesta, se devuelve.
2. Sin `ambito` y sin ids → `obra_key` heredado como hoy (R18).
3. `lineas_para_registro` → si `lineas` vacío, 422 de F-024 R23 sin cambios.
4. Si `len(datos["obras"]) > 1` → 422 `{ok:false, error, obras}`; el `error`
   lista «0719 · Nombre: 20 líneas; 0404 · …: 3» y dice «Sigrid registra por
   obra: filtra la columna Obra o selecciona líneas de una sola» (R17).

`_validar_ambito(ambito: dict, ids: list[int]) -> JSONResponse | None`:
422 si `vista` ∉ `VISTAS_AMBITO = ("obra", "trabajador")`, falta `obra_key` /
`worker_key`, `ids` vacío o `len(ids) > MAX_IDS_APROBACION` (R15); resuelve
los ids de la vista (R13) y, si `set(ids) - vista` no es vacío, 422 con
`fuera_de_ambito` y «N línea(s) ya no pertenecen a esta vista; recarga la
página» (R14). La validación ocurre **antes** de cualquier llamada a sv5, al
publisher o a `marcar_registros_encolado`, y en los tres endpoints por
pasar todos por `_payload_registro`. `ambito` no entra en el payload (R21).

### 5.3 Navegador (`static/app.js`)

- **Global compartido**: `PartidaSel` sale del segundo IIFE a nivel de
  fichero, junto a `MotivoHttp` (mismo nombre: sus usos no cambian), y gana
  `visible(tr)` (sin `filtered-day`, `style.display !== "none"`, sin
  `hidden`). El IIFE de aprobar la usa.
- **`wireBulkSelect`**: cablea `change` de `.sel-linea` ↔ `toggle(tr)`;
  `paint` marca también la casilla (R2); `selectRange` salta filas no
  visibles (R4); «Seleccionar visibles» y «Quitar selección» (`[data-sel-
  visibles]`, `[data-sel-ninguna]`) y contador `[data-sel-cuenta]` con
  ocultas (R3, R6). `isInteractive` ya excluye `input`.
- **`_filterCellText`**: ignora `.sel-linea` (R5).
- **Aviso de cambios**: filtros por columna, filtro por días/casillas y
  selección disparan `document.dispatchEvent(new CustomEvent("lineas:cambio"))`.
- **IIFE de aprobar**: `conjuntoAprobacion()` → `{modo: "seleccion" |
  "visibles" | "todo", ids, total, ocultas}`; `pintarBotonAprobar()` en
  `ready` y en `lineas:cambio` pone texto, `disabled` y `title` (R7, R8).
  El clic en `#aprobar-todo` construye `{registro_ids, ambito}` desde los
  `data-*` del botón (R10) y llama `aprobar(peticion, alcance)`; `alcance`
  (texto de R11) se pinta al principio de `resumenHtml` y **no** viaja al
  servidor; `conBorradas` y `ejecutar` reutilizan la misma `peticion`. La
  rama `.aprobar-linea` no cambia (R12).

## 6. SQL

Ninguno. Sin cambios de esquema ni consultas nuevas a Sigrid.

## 7. Fuera de alcance

- Partir automáticamente un lote de varias obras en varias peticiones
  (alternativa de DA8): feature aparte si el humano la quiere.
- Acotar la tabla de persona al mes del calendario (DA12).
- Casillas en `parte_detail.html` y en la matriz (la matriz sigue siendo
  filtro, no selección).
- Arnés de tests JS (DA13). Cambiar las reglas de exclusión de F-024.

## 8. Decisiones abiertas (recomendación en negrita)

1. **DA1 · Botón sin nada marcado**: **aprueba lo visible**, con el texto
   diciendo qué («Aprobar visibles (N)» / «Aprobar todo (N)»). Alternativas:
   (b) deshabilitado hasta marcar algo (pierde «aprobar el mes» de un clic);
   (c) «todo» ignorando filtros (es lo que falla hoy en obra).
2. **DA2 · Marcadas ocultas**: **no se aprueban** («apruebo lo que veo
   marcado»); contador y modal lo dicen. Alternativas: que manden aunque
   estén ocultas; o que filtrar desmarque (cambiaría la edición en bloque).
3. **DA3 · Una sola selección** (casillas = Ctrl/Shift+clic). Consecuencia
   conocida: con filas marcadas, cambiar hora, partida o trabajador de una
   de ellas sigue aplicándose a toda la selección (hoy ya es así).
   Alternativa: selección aparte para aprobar (dos selecciones confunden).
4. **DA4 · Casilla en la celda Fecha**, no columna nueva: no rompe el orden
   y los anchos guardados en `localStorage` (`wireColumnTools`), los filtros
   por `cellIndex` ni los tests de vistas. Alternativa: columna propia con
   casilla «todas» en la cabecera, fijada fuera del reordenado.
5. **DA5 · «Seleccionar visibles» / «Quitar selección» como botones** sobre
   la tabla, con contador; la barra flotante `.bulk-bar` gana «Aprobar
   seleccionadas» solo si existe `#aprobar-todo`.
6. **DA6 · Casilla en todas las filas** (también `registrado`/`encolado`):
   el servidor excluye y el modal cuenta (F-024 R22, R25); no se copia la
   regla en JS. Alternativa: sin casilla en `registrado`.
7. **DA7 · Ids fuera de la vista ⇒ 422 de toda la petición**. Alternativa:
   descartarlos en silencio (aprobaría menos de lo marcado sin decirlo).
8. **DA8 · Una obra por petición, en toda petición** (también la heredada
   y la de persona): 422 con desglose. Alternativa: el navegador parte el
   lote por obra (varios preflights/modales): §7.
9. **DA9 · El botón por línea no mira la selección** (a diferencia de las
   ediciones): aprobar es una escritura en Sigrid y se quiere exacta.
10. **DA10 · Shift+clic solo en visibles** (hoy marca también ocultas).
11. **DA11 · Tope de 5000 ids con `ambito`**, como F-024 R17/R28.
12. **DA12 · Ámbito de persona = toda su tabla** (todos los meses), porque
    es lo que pinta hoy; con DA8, sin filtrar por obra la mayoría de
    personas con varias obras recibirá el 422 explicativo.
13. **DA13 · JS sin arnés**: `node --check`, comprobaciones estáticas en
    pytest y M2–M6 (como F-004 y F-024).
14. **DA14 · Servicios y rigor**: solo sv4; **`estandar`**. DA8 reduce un
    riesgo de escritura en Sigrid sin escribir nada nuevo; si el humano
    prefiere `critico` por ello, cambia solo la campaña de mutación.

## 9. Verificaciones manuales (humano)

- **M1 · ¿ya pasó lo de DA8? (PG `partes`, lectura)**: partes de Sigrid con
  líneas de más de una obra:
  `SELECT sigrid_parte_cod, count(DISTINCT coalesce(obra_ide::text,
  obra_codigo, obra_nombre)) AS obras, count(*) FROM parte_registros WHERE
  sigrid_hmoide IS NOT NULL GROUP BY 1 HAVING count(DISTINCT
  coalesce(obra_ide::text, obra_codigo, obra_nombre)) > 1;` (las de modo
  pruebas, todas a la 0404, también saldrán). Si hay filas reales: feature
  de limpieza aparte.
- **M2 · obra** (modo pruebas, obra 0404, tras Ctrl+F5): marcar 2 líneas →
  «Aprobar seleccionadas (2)» → el modal dice «2 seleccionadas de M» y solo
  esas pasan a `encolado`/`registrado`; el resto sigue igual.
- **M3 · obra, filtro de matriz sin selección**: marcar 2 casillas de la
  matriz → «Aprobar visibles (N)» con N = filas visibles; con un filtro de
  columna además, N baja; «Quitar filtro» no borra la selección.
- **M4 · marcadas ocultas**: marcar 3, filtrar para ocultar 1 → contador
  «(1 oculta: no se aprueba)» y «Aprobar seleccionadas (2)»; ocultar las 3
  → botón deshabilitado con su `title`.
- **M5 · persona con dos obras**: «Aprobar visibles» sin filtrar → 422 con
  el desglose por obra; filtrar Obra = 0404 → se aprueba solo esa.
- **M6 · regresión**: «Reaprobar» de una `borrado_sigrid` marcada aprueba
  solo esa; «Seleccionar visibles» + «Editar partida» en bloque sigue igual;
  Shift+clic con filtro activo no marca ocultas.

## 10. Riesgos

- **JS en caché tras desplegar**: el JS viejo envía `obra_key` (obra) o ids
  sin `ambito` (persona): sigue funcionando (R18) y ya le aplica R17.
- **Selección compartida** (DA3): aprobar no cambia, pero un usuario puede
  editar en bloque sin querer; el contador visible lo mitiga.
- **`app.js` sin tests de comportamiento**: M2–M6. **Mutación** (estándar,
  20 mutantes) sobre los hunks de `app.py` y `parte_repository.py`.
- **Tests heredados** que posten lotes de varias obras: T1 los inventaría;
  se adaptan con nota, no se borran.
