<!-- specs/F-022-aprobar-seleccionadas/design.md -->
# F-022 · Diseño técnico

## 0. Resumen para el humano (detalle en §8)

- **Aprobado el 2026-10-01** (DA1–DA18 según recomendación): con algo
  marcado se aprueba **solo lo marcado y visible**; sin marcar, **lo
  visible** (sin filtros, todo). Casillas sobre la selección Ctrl/Shift+clic
  existente. Ids que no son de la vista ⇒ **422 entero** (DA7).
- **DA8** Varias obras no se rechazan: **sv4 parte la aprobación en una
  petición por obra**; sv5 no cambia. Hoy un lote de varias obras va entero
  a la obra de la primera línea: **aviso inmediato**, en persona filtrar la
  columna Obra antes de «Aprobar visibles». M1: ¿ya pasó?
- **DA14** rigor `critico`; **DA15** tope 10 obras; **DA16** resultado por
  obra, sin «todo o nada».
- **DA19 (nueva, a validar)**: el modal lista **lo que se va a aprobar**,
  por obra, con totales, estado de cada línea y las excluidas con su motivo.
  Lo construye **el servidor** con la respuesta de sv5. Con más de 40 filas,
  secciones plegadas y scroll interno; **sin paginar**.

## 1. Servicios que toca y por qué

| Servicio | Por qué | Qué no hace |
|---|---|---|
| sv4 | Dueño de vistas, selección y payload de registro: elige la obra de cada petición y arma el listado | Ni esquema, ni cola, ni formato del mensaje |

**sv5 no cambia** (verificado): `PeticionIn` = `{obra, lineas, pisar_claves,
usuario}`, **una obra por petición**; su paso 2 ya agrupa por mes natural, así
que sv4 **no agrupa por mes**. Su preflight ya devuelve lo que pide el
listado: `acciones` por línea (`accion`, `motivo`, `hora_codigo`, `can`,
`partida_cod`, `recurso_ide`) y `conflictos[].registros`. **Descartado que
agrupe sv5**: cambia el contrato del único que escribe (HTTP, cola,
resultado), su fallo es «petición entera» y obliga a desplegarlo antes.

## 2. Qué hace hoy y qué se toma de dedicación

- **Obra**: «Aprobar todo» aprueba el periodo entero e **ignora** filtros.
  **Persona**: «Aprobar visibles» envía ids visibles de una tabla con
  **todos** los meses y obras, sin validar. **Obra del payload**: la de la
  primera línea. `PartidaSel` (Ctrl/Shift+clic) sin casillas; Shift+clic
  incluye ocultas. La clave de conflicto de sv5 (`recurso|fecha|hora_ide`)
  **no lleva obra** (motiva R19).
- **Dedicación** (repo `porcentajes`, `dedicacion-api` y `dedicacion-front`,
  leído): su API ya **agrupa por obra** con preflight/ejecutar en serie
  (como DA8). Modal: por obra un título, partes «existe / se creará», **una
  tabla** (Trabajador, Destino, Acción, %, Cód. hora, Partida editable) y
  los conflictos con casilla debajo; ≤ 1060 px y 86 vh con scroll del modal
  entero; **sin totales, plegado ni paginado**, y manda todas las claves de
  pisar a todas las obras (R19 lo evita). Se adopta el patrón y se añaden
  totales, estado, excluidas y plegado; la partida no se edita en el modal.

## 3. Flujo

Conjunto (DA1/DA2) → `preflight {registro_ids, ambito}` → ámbito (R10–R12)
→ `lineas_para_registro` → `grupos` (R14, R15) → preflight a sv5, Sesame,
avisos y **listado** por grupo (R23–R25) → modal (R27, R28) → `ejecutar` con
los grupos síncronos y `encolar` con el resto (R29), reagrupando igual →
resultado y sondeo por grupo (R30). Cada llamada es subconjunto de la vista.

## 4. Ficheros

| Ruta | Crear / qué cambia |
|---|---|
| `services/partes-front/application/services/reparto_obras.py` | **Crear** (puro, §5.2) |
| `services/partes-front/tests/test_f022_reparto_obras.py` | **Crear**: R14–R25 en lo puro (tablas de casos) |
| `services/partes-front/tests/test_f022_aprobar_seleccion.py` | **Crear**: R10–R26, R31–R33 por endpoint (`TestClient`, SQLite, dobles de sv5, publisher y calendario de F-003/F-024) |
| `services/partes-front/tests/test_f022_vistas_seleccion.py` | **Crear**: R1, R8, R9 y estáticos de R4 y del listado (HTML y `app.js`, patrón `test_f004_r16`) |
| `services/partes-front/infrastructure/database/parte_repository.py` | `registro_ids_de_trabajador`; `lineas_para_registro` + `grupos` y `excluidas_detalle` (§5.1) |
| `services/partes-front/interface_adapters/web/app.py` | `_payload_registro` → `_preparar_registro`; los tres endpoints iteran por grupo (§5.3). Sin endpoints nuevos |
| `services/partes-front/config/settings.py` | `APROBACION_MAX_OBRAS=10` (1–50) |
| `services/partes-front/templates/obra_detail.html`, `trabajador_detail.html` | casilla `sel-linea` en `cell-fecha`; barra `.sel-tools`; `#aprobar-todo` con `data-vista` y `data-obra-key/period/mode` o `data-worker-key` |
| `services/partes-front/static/app.js`, `styles.css` | §5.4; casilla, barra, secciones plegables, tabla del listado con cabecera fija, modal más ancho |
| `services/partes-front/tests/test_f024_borrado_sigrid.py` | `test_f024_r22_payload_repo_sin_ids` (dict entero): + claves nuevas con nota |
| `docs/ARCHITECTURE.md` | Semántica 5: una petición a sv5 = una obra; sv4 reparte. Semántica 10: masivas por selección (≤ 8 líneas) |
| `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` | Selección explícita y una petición `q-transfer` por obra (contrato con sv5 igual) |

**No se tocan**: sv5, sv3, `orm_models.py`, `congelacion.py`,
`resultado_sigrid.py`, `resultado_consumer.py`, `transfer_queue_publisher.py`,
`transfer_client.py`, `comprobacion_sigrid.py`, `registro_ids_de_obra`,
`/api/sigrid/comprobar`, `/api/aprobar/estado`, `parte_detail.html`, `infra/`.

## 5. Clases y funciones

### 5.1 Repositorio (infrastructure)

- `registro_ids_de_trabajador(worker_key) -> list[int]`: ids de
  `get_worker(key).registros` (`[]` si no existe).
- `lineas_para_registro(...)` añade `grupos: [{clave, obra: {ide, codigo,
  nombre}, lineas, estado_previo: {registro_id: estado normalizado}}]` de
  las líneas que viajan, por `obra_key_for_registro(r)` y en orden de
  clave, y `excluidas_detalle: [{registro_id, fecha_int, nombre, obra_codigo,
  horas, hora_codigo, estado, parte_cod}]`. `obra`, `lineas` y `excluidas`
  no cambian; `estado_previo` no entra en las líneas del payload (R33).

### 5.2 `reparto_obras.py` (application, puro)

```python
@dataclass
class GrupoObra: clave: str; obra: dict; lineas: list[dict]; estado_previo: dict[int, str]
SEPARADOR_CLAVE = "::"
UMBRAL_PLEGADO = 40  # filas; el navegador lo recibe en la respuesta
def repartir_claves(pisar: list[str], claves_grupo: list[str]) -> dict[str, list[str]] | None
def listado_grupo(g: GrupoObra, pf: dict) -> list[dict]
def totales(listado: list[dict]) -> dict
def agregar_preflight(evaluados: list[dict]) -> dict
def agregar_ejecucion(ejecutados: list[dict]) -> dict
```

- `repartir_claves` (R19): `"g::k"` → `k` al grupo `g` (desconocido se
  ignora); sin `::` → al único grupo, o `None` con varios (⇒ 422).
- `listado_grupo` (R23, R24): una fila por línea del grupo, cruzando por
  `registro_id` con `pf["acciones"]` y `pf["conflictos"][*]["registros"]`;
  código de hora, partida y recurso de la acción si vienen (las reglas de
  sv5 pueden cambiarlos), si no de la línea; horas = `can` de la acción si
  se escribe, si no `horas` de la línea; tipo por `es_incidencia` y
  `tipo_hora`; `estado`/`motivo` según R24 (con `pf.ok` falso, todas
  `no_se_registra` con `pf.error`). Orden: fecha, trabajador, tipo.
- `totales` (R25): `{lineas, por_estado, horas_ordinarias, horas_extra,
  incidencias}`; las horas solo de `nuevo`, `reaprobacion` y `conflicto`.
- `agregar_preflight` (R16, R17): planos concatenados (`partes`,
  `acciones`, `conflictos`, `avisos_calendario`), `resumen` sumado,
  `obra_destino`/`forzada_pruebas` del primer grupo `ok`, `sesame_bloqueo`
  si algún grupo lo tiene, `ok` = alguno `ok`, `totales` = suma de grupos.
  Con un grupo, el plano es su respuesta tal cual (+ claves nuevas).
- `agregar_ejecucion` (R22): `escritas`, `omitidas`, `ya_registradas`,
  `pendientes_confirmacion`, `partes` concatenados, `borradas` sumado,
  `ok` = todos, `parcial`; `bloqueado_sesame` cuenta como no `ok`.

### 5.3 Portal (`interface_adapters/web/app.py`)

`_preparar_registro(body, *, actor)` → `(grupos, excluidas,
excluidas_detalle) | JSONResponse`: ids deduplicados → `_validar_ambito`
(R10–R12) → sin `ambito` ni ids, `obra_key` heredado → `lineas_para_registro`
→ vacío: 422 de F-024 R23 → más de `aprobacion_max_obras` grupos: 422 (R15).
`_payload_grupo(g, claves, actor)` arma el payload de siempre (R33).

- **preflight**: por grupo, `transfer_client.preflight`, avisos y
  `_calendario_fiable` de sus líneas (R18, R31), `listado_grupo` y
  `totales`; responde `agregar_preflight` + `grupos` (cada uno con
  `listado`, `totales`, `sesame_bloqueo`, `avisos_calendario`) +
  `excluidas` + `excluidas_detalle` + `umbral_plegado`.
- **ejecutar**: `repartir_claves` (None ⇒ 422); por grupo y en orden:
  bloqueado sin override ⇒ `bloqueado_sesame`; si no, `ejecutar` +
  `_trazar(sus ids, sin_sesame=bloqueado y forzado)`; todos bloqueados ⇒
  422 de hoy; respuesta `agregar_ejecucion` + `grupos` + `excluidas`.
- **encolar**: `pisar_claves` ⇒ 422 (F-002 R5); por grupo: bloqueado ⇒
  `bloqueado_sesame`; sin publisher ⇒ `ejecutar` (F-002 R3); con publisher
  ⇒ `publicar` y luego `marcar_registros_encolado(sus ids)`; excepción ⇒
  `error_cola` y sigue (R21). Todos bloqueados ⇒ 422 de hoy; todos
  `error_cola` ⇒ 502. Respuesta: `ok`, `modo`, `peticion_id` (el primero),
  `peticiones`, `encoladas`, `registro_ids`, `excluidas`, `grupos`.

### 5.4 Navegador (`static/app.js`)

- **Selección**: `PartidaSel` pasa a global junto a `MotivoHttp` con
  `visible(tr)`; casillas ↔ selección, rango solo visibles, botones y
  contador (R1–R5); `_filterCellText` ignora `.sel-linea`; filtros y
  selección emiten `lineas:cambio`. **Botón**: `conjuntoAprobacion()` →
  `{modo, ids, total, ocultas}`; texto, `disabled` y `title` (R6, R7);
  `{registro_ids, ambito}` (R8); alcance y `ocultas` solo en el modal.
- **Modal** (R26–R28), sin calcular estados: cabecera con alcance y total
  general (`pf.totales`); por `pf.grupos` un `<details>` cuyo `<summary>`
  lleva obra y sus `totales`, abierto si el listado total ≤
  `umbral_plegado`; dentro, partes, tabla (Fecha, Trabajador, Tipo, Cód.
  hora, Horas, Partida, Recurso, Estado con `motivo` en `title`) en un área
  de ≤ 45 vh con `thead` fijo. Conflictos (casilla `value="<grupo>::<clave>"`),
  errores y bloqueos **fuera** del `<details>`. Al final, `<details>`
  plegado «Excluidas (N)» con `excluidas_detalle` y la línea de ocultas.
  Modal ≤ 1100 px de ancho y 86 vh de alto, como dedicación.
- **Confirmar y resultado** (R29, R30): síncronos → `ejecutar`, resto →
  `encolar`; resultado por grupo y sondeo de F-024 por grupo; obras sin
  registrar con motivo; pisar tras `ejecutar` solo con sus grupos.
  `.aprobar-linea` no cambia (R9).

## 6. SQL

Ninguno: ni esquema nuevo ni consultas nuevas a Sigrid.

## 7. Fuera de alcance

Acotar la tabla de persona al mes (DA12); casillas en `parte_detail.html` o
la matriz; editar la partida en el modal; arnés JS; corregir lo que halle M1.

## 8. Decisiones (DA1–DA18 aprobadas el 2026-10-01; DA19 a validar)

1. **DA1** Sin nada marcado, aprueba lo visible. **DA2** Marcada y oculta no
   se aprueba. **DA3** Una sola selección (editar hora, partida o
   trabajador de una marcada sigue aplicando a toda la selección).
2. **DA4** Casilla en la celda Fecha, sin columna nueva (no rompe orden ni
   anchos guardados ni filtros por `cellIndex`). **DA5** «Seleccionar
   visibles»/«Quitar selección»; la `.bulk-bar` gana «Aprobar
   seleccionadas». **DA6** Casilla en todas las filas.
3. **DA7** Ids fuera de la vista ⇒ 422 entero.
4. **DA8** Reparto por obra en sv4, sv5 sin cambios (§1); no por mes.
5. **DA9–DA13** Botón por línea ajeno a la selección; Shift+clic solo en
   visibles; tope de 5000 ids; ámbito de persona = toda su tabla; JS sin
   arnés (`node --check`, estáticos, M2–M8).
6. **DA14** Rigor **`critico`**: el reparto decide qué obra, empresa y parte
   reciben las horas en Sigrid de producción (mismo nivel que F-024):
   mutación completa sobre `reparto_obras.py` y los hunks de `app.py` y
   `parte_repository.py`, 0 supervivientes sin test o justificación.
7. **DA15** Grupos uno a uno, tope 10 obras (`APROBACION_MAX_OBRAS`).
8. **DA16** Resultado por grupo, sin «todo o nada»: no hay transacción entre
   partes de obras distintas y cada línea es idempotente por `synckey`.
9. **DA17** Claves de pisar con prefijo de grupo. **DA18** Modo pruebas:
   todos los grupos a la 0404 en peticiones separadas; el modal puede
   anunciar dos veces «se creará PT…», pero bajo el lock se crea uno.
10. **DA19 · Listado en el modal** — **recomendación**: lo arma el servidor
    (R23) con lo que sv5 hará de verdad (acción, código y horas tras las
    reglas, conflicto), no con lo que el navegador cree; tabla por obra
    como dedicación más totales, estado y excluidas; **plegado por obra
    por encima de 40 filas** (umbral en `reparto_obras.py`) con scroll
    interno y cabecera fija; conflictos y errores siempre visibles.
    Descartado **paginar**: impide repasar el mes de un vistazo y buscar
    con Ctrl+F. Alternativa: todo desplegado con el scroll del modal
    entero (como dedicación), cómodo hasta unas decenas de filas.

## 9. Verificaciones manuales (humano)

- **M1 · ¿ya pasó? (PG `partes`, lectura)**: `SELECT sigrid_parte_cod,
  count(DISTINCT coalesce(obra_ide::text, obra_codigo, obra_nombre)),
  count(*) FROM parte_registros WHERE sigrid_hmoide IS NOT NULL GROUP BY 1
  HAVING count(DISTINCT coalesce(obra_ide::text, obra_codigo,
  obra_nombre)) > 1;` (las de modo pruebas en la 0404 también salen).
- **M2 · obra** (modo pruebas, Ctrl+F5): marcar 2 → «Aprobar seleccionadas
  (2)»; el modal lista esas 2 de M y solo cambian esas. **M3** · filtro de
  matriz sin selección: «Aprobar visibles (N)»; «Quitar filtro» no borra.
- **M4 · ocultas**: marcar 3 y ocultar 1 → «(1 oculta…)», «(2)» y la línea
  de ocultas en el modal; ocultar las 3 → botón deshabilitado.
- **M5 · persona con dos obras** (modo pruebas): sin filtrar → dos
  secciones con su listado y total; tras confirmar, en `ca-sv5-transfer`
  dos `[registro] MODO PRUEBAS: la obra <X> se ignora` (una por obra) y en
  `ca-sv4-front` dos `[transfer-cola] encolada`; resultado por obra.
- **M6 · listado**: una `registrado` y una `borrado_sigrid` en la selección
  salen en «Excluidas» con su motivo; una `error` previa sale
  `reaprobacion`; una incidencia sale con su código y 0 h; los totales
  cuadran con la tabla.
- **M7 · muchas filas**: «Aprobar todo» en una obra × mes completa →
  secciones plegadas, resumen visible, scroll con cabecera fija;
  regresión: «Reaprobar» de una marcada aprueba solo esa; «Editar partida»
  en bloque igual.
- **M8 · primera aprobación real de varias obras** (producción): repetir M1.

## 10. Riesgos

- **JS en caché**: el viejo envía `obra_key` o ids sin `ambito`; se reparte
  igual; claves sin prefijo con varias obras ⇒ 422 (seguro).
- **Duración y tamaño**: N preflights en serie (tope 10); listado de una obra
  × mes (≈ 1.000 filas) ≈ 200 KB. **JS sin tests**: M2–M8. **Tests
  heredados** de la forma de las respuestas: T1; se adaptan con nota.
