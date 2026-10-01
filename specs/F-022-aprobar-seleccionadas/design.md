<!-- specs/F-022-aprobar-seleccionadas/design.md -->
# F-022 · Diseño técnico

## 0. Resumen para el humano (decisiones a validar, detalle en §8)

- **DA1/DA2** Con algo marcado, aprueba **solo lo marcado y visible**; sin
  nada marcado, **lo visible** (sin filtros, todo). **DA3–DA5** Casillas
  sobre la selección Ctrl/Shift+clic que ya existe. **DA7** Ids que no son
  de la vista ⇒ **422 de toda la petición**.
- **DA8 (revisada por el humano, 2026-10-01)**: varias obras **no** se
  rechazan: **sv4 parte la aprobación en una petición por obra** y cada
  línea va al parte de su obra; sv5 no cambia. Hoy un lote de varias obras
  va entero a la obra de la primera línea: **aviso inmediato**, en persona
  filtrar la columna Obra antes de «Aprobar visibles». M1: ¿ya pasó?
- **DA16** Resultado **por obra**, sin «todo o nada». **DA14** Rigor
  **`critico`** (decide a qué obra van las horas en Sigrid). Solo **sv4**.

## 1. Servicios que toca y por qué

| Servicio | Por qué | Qué no hace |
|---|---|---|
| sv4 | Dueño de las vistas, de la selección y de construir el payload (`lineas_para_registro`, `_payload_registro`): es quien elige la obra de cada petición | No toca esquema, cola ni el formato del mensaje |

**sv5 no cambia** (verificado): `PeticionIn` = `{obra, lineas, pisar_claves,
usuario}`, **una obra por petición**; su paso 2 ya agrupa por mes natural (un
parte por obra y mes), así que sv4 **no agrupa por mes**. Empresa,
verificación de recurso (F-023) y conflictos dependen de esa obra.
**Alternativa descartada: que agrupe sv5** (obra por línea): cambia el
contrato del único servicio que escribe (HTTP, mensaje de `q-transfer`,
resultado y su consumidor), su fallo es «petición entera» y habría que
rehacerlo por obra dentro del lock, y obliga a desplegar sv5 antes. En sv4,
cada grupo pasa por el pipeline ya probado; coste: N viajes y N mensajes.

## 2. Qué hace hoy (diagnóstico)

- **Obra**: «✓ Aprobar todo» envía `{obra_key, period, mode}`; el servidor
  aprueba **todo** el periodo e **ignora** filtros de columna y de matriz.
- **Persona**: «✓ Aprobar visibles» envía los ids visibles, pero la tabla
  pinta **todas** sus líneas (todos los meses y obras) y nadie las valida.
- **Obra del payload**: la de la primera línea leída, sin mirar el resto.
  **Selección**: `PartidaSel` (Ctrl/Shift+clic), sin casillas, local a un
  IIFE; Shift+clic incluye ocultas.
- **Clave de conflicto** de sv5 = `recurso|fecha|hora_ide`, **sin obra**:
  dos obras pueden producir la misma clave (motiva R22).

## 3. Encaje y flujo

Conjunto (DA1/DA2) → `preflight {registro_ids, ambito}` → ámbito (R13–R15)
→ `lineas_para_registro` → `grupos` (R17, R18) → preflight, Sesame y avisos
por grupo → modal por obra (R26) → `ejecutar` con los ids de los grupos
síncronos y `encolar` con el resto (R27), reagrupando igual (determinista) →
resultado y sondeo por grupo (R28). Cada llamada es subconjunto de la vista.

## 4. Ficheros

### Crear

| Ruta | Contenido |
|---|---|
| `services/partes-front/application/services/reparto_obras.py` | `GrupoObra`, `repartir_claves`, `agregar_preflight`, `agregar_ejecucion` (§5.2), puro |
| `services/partes-front/tests/test_f022_reparto_obras.py` | R17–R22, R25 en lo puro (tablas de casos) |
| `services/partes-front/tests/test_f022_aprobar_seleccion.py` | R13–R16, R18–R25, R29–R31 por endpoint (`TestClient`, SQLite, dobles de sv5, publisher y calendario de F-003/F-024) |
| `services/partes-front/tests/test_f022_vistas_seleccion.py` | R1, R10, R12 y lo estático de R5 (HTML de las dos vistas y comprobaciones mínimas de `app.js`, patrón `test_f004_r16`) |

### Modificar

| Ruta | Qué cambia |
|---|---|
| `services/partes-front/infrastructure/database/parte_repository.py` | `registro_ids_de_trabajador(worker_key)`; `lineas_para_registro` añade `grupos` (§5.1); `obra`, `lineas` y exclusiones no cambian |
| `services/partes-front/interface_adapters/web/app.py` | `_payload_registro` → `_preparar_registro` (ámbito, grupos, tope); los tres endpoints iteran por grupo (§5.3). Sin endpoints nuevos |
| `services/partes-front/config/settings.py` | `APROBACION_MAX_OBRAS=10` (1–50) |
| `services/partes-front/templates/obra_detail.html`, `trabajador_detail.html` | casilla `sel-linea` en `cell-fecha`; barra `.sel-tools`; `#aprobar-todo` con `data-vista` y `data-obra-key/period/mode` o `data-worker-key` |
| `services/partes-front/static/app.js`, `static/styles.css` | §5.4; estilo de casilla, barra, secciones por obra y botón deshabilitado |
| `services/partes-front/tests/test_f024_borrado_sigrid.py` | `test_f024_r22_payload_repo_sin_ids` compara el dict entero: + `"grupos": []` con nota (R32) |
| `docs/ARCHITECTURE.md` | Semántica 5: una petición a sv5 es de una obra; sv4 parte las aprobaciones por obra. Semántica 10: masivas por selección/visibles (≤ 8 líneas netas) |
| `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` | «Aprobar todo/visibles» → selección explícita y una petición `q-transfer` por obra (el contrato con sv5 no cambia) |

### No se tocan

`services/partes-transfer/**` (sv5), `services/partes-persistencia/**`,
`orm_models.py`, `congelacion.py`, `resultado_sigrid.py`,
`resultado_consumer.py`, `transfer_queue_publisher.py`, `transfer_client.py`,
`comprobacion_sigrid.py`, `registro_ids_de_obra`, `/api/sigrid/comprobar`,
`/api/aprobar/estado`, `parte_detail.html`, `infra/`.

## 5. Clases y funciones

### 5.1 Repositorio (infrastructure)

- `registro_ids_de_trabajador(worker_key) -> list[int]`: ids de
  `get_worker(key).registros` (`[]` si no existe): las filas de la tabla.
- `lineas_para_registro(...)["grupos"]`: `[{clave, obra: {ide, codigo,
  nombre}, lineas: [...]}]` de **las líneas que viajan**, por
  `obra_key_for_registro(r)`, en orden de `clave`; `obra` del grupo = la de
  sus líneas. `[]` sin líneas.

### 5.2 `reparto_obras.py` (application, puro)

```python
@dataclass
class GrupoObra: clave: str; obra: dict; lineas: list[dict]  # + registro_ids
SEPARADOR_CLAVE = "::"
def repartir_claves(pisar: list[str], claves_grupo: list[str]) -> dict[str, list[str]] | None
def agregar_preflight(evaluados: list[dict]) -> dict
def agregar_ejecucion(ejecutados: list[dict]) -> dict
```

- `repartir_claves`: `"g::k"` → grupo `g` recibe `k` (grupo desconocido se
  ignora); claves sin `::` → al único grupo, o `None` si hay más de uno
  (R22 → 422).
- `agregar_preflight` (R19, R20): cada evaluado es `{clave, obra,
  registro_ids, ok, error, …respuesta de sv5, avisos_calendario,
  sesame_bloqueo}`. Plano: `partes`, `acciones`, `conflictos`,
  `avisos_calendario` concatenados; `resumen` sumado por clave numérica;
  `obra_destino`/`forzada_pruebas` del primer grupo `ok`; `sesame_bloqueo`
  si algún grupo lo tiene; `ok` = algún grupo `ok`; `error` = los de los
  grupos si ninguno. Con un grupo, el plano es su respuesta tal cual.
- `agregar_ejecucion` (R25): `escritas`, `omitidas`, `ya_registradas`,
  `pendientes_confirmacion`, `partes` concatenados; `borradas` sumado;
  `ok` = todos `ok`; `parcial` = unos sí y otros no. Un grupo
  `bloqueado_sesame` cuenta como no `ok`.

### 5.3 Portal (`interface_adapters/web/app.py`)

`_preparar_registro(body, *, actor) -> tuple[list[GrupoObra], dict] |
JSONResponse`: ids deduplicados → con `ambito`, `_validar_ambito` (R13–R15,
422 `fuera_de_ambito`) → sin `ambito` ni ids, `obra_key` heredado →
`lineas_para_registro` → vacío: 422 de F-024 R23 → más de
`aprobacion_max_obras` grupos: 422 con desglose (R18). `_payload_grupo(g,
claves, actor)` construye el payload de siempre (R31).

- **preflight**: por grupo, `transfer_client.preflight`, avisos y
  `_calendario_fiable` sobre sus líneas (R21, R29); `agregar_preflight` +
  `grupos` + `excluidas`.
- **ejecutar**: `repartir_claves` (None ⇒ 422); por grupo y en orden:
  bloqueado sin override ⇒ `bloqueado_sesame`; si no, `ejecutar` +
  `_trazar(sus ids, sin_sesame=bloqueado y forzado)`. Todos bloqueados ⇒
  422 de hoy. Respuesta `agregar_ejecucion` + `grupos` + `excluidas`.
- **encolar**: `pisar_claves` ⇒ 422 (F-002 R5); por grupo: bloqueado ⇒
  `bloqueado_sesame`; sin publisher ⇒ `ejecutar` síncrono (F-002 R3);
  con publisher ⇒ `publicar` y después `marcar_registros_encolado(sus ids)`;
  excepción al publicar ⇒ `error_cola` y sigue (R24). Todos bloqueados ⇒
  422 de hoy; todos `error_cola` ⇒ 502. Respuesta: `ok` (todos
  encolados), `modo`, `peticion_id` (el primero, compatibilidad),
  `peticiones`, `encoladas`, `registro_ids`, `excluidas`, `grupos`.

### 5.4 Navegador (`static/app.js`)

- `PartidaSel` pasa a global junto a `MotivoHttp` (mismo nombre) con
  `visible(tr)`; casillas ↔ selección, rango solo visibles, «Seleccionar
  visibles»/«Quitar selección», contador con ocultas; `_filterCellText`
  ignora `.sel-linea`; filtros y selección emiten `lineas:cambio`.
- Botón: `conjuntoAprobacion()` → `{modo, ids, total, ocultas}`; texto,
  `disabled` y `title` en `ready` y en `lineas:cambio` (R7, R8); la
  petición lleva `{registro_ids, ambito}` (R10) y el `alcance` (R11) se
  pinta en el modal sin viajar.
- Modal (R26): una sección por `pf.grupos` (obra, «se registrarán N»,
  partes, conflictos con `value="<clave grupo>::<clave>"`, avisos, error o
  bloqueo) y total. Confirmar (R27): grupos síncronos → `ejecutar`,
  evaluados restantes → `encolar`, en ese orden si hay ambos.
- Resultado (R28): síncrono por grupo (`r.grupos`); encolado: sondeo de
  F-024 por grupo con sus `registro_ids`; obras sin registrar con motivo
  (`error` de preflight, `bloqueado_sesame`, `error_cola`, `ok:false`).
  Repetir para pisar conflictos de la respuesta de `ejecutar` usa solo los
  grupos con claves marcadas. `.aprobar-linea` no cambia (R12).

## 6. SQL

Ninguno: ni esquema nuevo ni consultas nuevas a Sigrid.

## 7. Fuera de alcance

- Acotar la tabla de persona al mes del calendario (DA12).
- Casillas en `parte_detail.html` o en la matriz (sigue siendo filtro).
- Arnés de tests JS (DA13). Cambiar las exclusiones de F-024.
- Corregir en Sigrid lo que M1 encuentre (feature aparte si aparece).

## 8. Decisiones abiertas (recomendación en negrita)

1. **DA1 · Sin nada marcado aprueba lo visible**. Alternativas:
   deshabilitado hasta marcar; «todo» ignorando filtros (el fallo de hoy).
2. **DA2 · Marcada y oculta no se aprueba**; contador y modal lo dicen.
3. **DA3 · Una sola selección**: con filas marcadas, editar hora, partida
   o trabajador de una sigue aplicando a toda la selección (ya es así).
4. **DA4 · Casilla en la celda Fecha**, sin columna nueva: no rompe orden ni
   anchos guardados (`wireColumnTools`), filtros por `cellIndex` ni tests.
5. **DA5 · «Seleccionar visibles»/«Quitar selección» como botones**; la
   `.bulk-bar` gana «Aprobar seleccionadas» si existe `#aprobar-todo`.
6. **DA6 · Casilla en todas las filas**; el servidor excluye (F-024).
7. **DA7 · Ids fuera de la vista ⇒ 422 entero**, no aprobar «lo que se
   pueda» en silencio.
8. **DA8 · Reparto por obra en sv4, sv5 sin cambios** (§1); por obra y no
   por (obra, mes): sv5 ya parte por mes natural.
9. **DA9–DA13**: el botón por línea no mira la selección; Shift+clic solo
   en visibles; tope de 5000 ids con `ambito` (como F-024); ámbito de
   persona = toda su tabla; JS sin arnés (`node --check`, estáticos, M2–M7).
10. **DA14 · Rigor `critico`** (hoy `estandar`): el reparto decide qué obra,
    qué empresa y qué parte reciben las horas en Sigrid de producción; un
    fallo imputa coste a la obra equivocada, mismo nivel que F-024. Exige
    campaña de mutación completa sobre `reparto_obras.py` y los hunks de
    `app.py` y `parte_repository.py`, con 0 supervivientes sin test o
    justificación aceptada. Si el humano lo aprueba, el líder actualiza
    `features.json`.
11. **DA15 · Grupos uno a uno, tope 10 obras** (`APROBACION_MAX_OBRAS`):
    preflights en serie (sv5 una réplica; el lock serializa la escritura de
    todos modos). Alternativa: preflights en paralelo con hilos.
12. **DA16 · Resultado por grupo, sin «todo o nada»**: Sigrid no tiene
    transacción entre partes de obras distintas y cada línea es idempotente
    por `synckey`; lo fallido queda en `error`/sin cambios, visible, y se
    reaprueba. Alternativa: abortar todo si un preflight falla (bloquea a
    todas las obras por una).
13. **DA17 · Claves de pisar con prefijo de grupo** (`<grupo>::<clave>`):
    la de sv5 no lleva obra y dos obras pueden coincidir el mismo día.
14. **DA18 · Modo pruebas**: todos los grupos van a la 0404 en peticiones
    separadas; el modal puede anunciar el mismo «se creará PT…» en dos
    grupos, pero la escritura bajo lock crea uno y el segundo lo reutiliza.

## 9. Verificaciones manuales (humano)

- **M1 · ¿ya pasó? (PG `partes`, lectura)**: `SELECT sigrid_parte_cod,
  count(DISTINCT coalesce(obra_ide::text, obra_codigo, obra_nombre)),
  count(*) FROM parte_registros WHERE sigrid_hmoide IS NOT NULL GROUP BY 1
  HAVING count(DISTINCT coalesce(obra_ide::text, obra_codigo,
  obra_nombre)) > 1;` (las de modo pruebas en la 0404 también salen).
- **M2 · obra** (modo pruebas, Ctrl+F5): marcar 2 → «Aprobar seleccionadas
  (2)»; el modal dice «2 seleccionadas de M»; solo esas cambian de estado.
- **M3 · filtro de matriz sin selección**: «Aprobar visibles (N)» con N =
  filas visibles; «Quitar filtro» no borra la selección.
- **M4 · ocultas**: marcar 3 y ocultar 1 → «(1 oculta…)» y «(2)»; ocultar
  las 3 → botón deshabilitado con su `title`.
- **M5 · persona con dos obras** (modo pruebas): sin filtrar → modal con
  dos secciones y total; tras confirmar, en `ca-sv5-transfer` dos líneas
  `[registro] MODO PRUEBAS: la obra <X> se ignora` (una por obra, prueba
  que cada petición llevó la suya) y en `ca-sv4-front` dos `[transfer-cola]
  encolada`; el resultado se ve por obra.
- **M6 · regresión**: «Reaprobar» de una marcada aprueba solo esa;
  «Editar partida» en bloque igual; Shift+clic con filtro no marca ocultas.
- **M7 · primera aprobación real de varias obras** (producción, tras
  desplegar y salir de modo pruebas): repetir M1 y que no aparezcan partes
  nuevos con más de una obra.

## 10. Riesgos

- **JS en caché**: el viejo envía `obra_key` o ids sin `ambito`; el
  servidor reparte igual y pinta planos agregados; claves sin prefijo con
  varias obras ⇒ 422 (seguro).
- **Duración**: N preflights en serie (endpoint `async` que llama síncrono
  a sv5, como hoy con uno); tope 10 (DA15). **Modo pruebas**: DA18.
- **`app.js` sin tests de comportamiento**: M2–M7. **Tests heredados** de
  la forma de las respuestas: T1 los inventaría; se adaptan con nota.
