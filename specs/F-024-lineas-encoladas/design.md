<!-- specs/F-024-lineas-encoladas/design.md -->
# F-024 · Diseño técnico

Datos: `progress/explore_F-024.md` (§N) y lecturas del spec-author (2026-10-01,
sigrid-api, `ruesma`, solo lectura): **0** `hmores` huérfanas de `hmo`, **0**
`synckey` `partes:%`, los 35 `ide` de sv5 siguen sin existir, ≤ 1.337 líneas por `hmo`.

## 1. Servicios que toca y por qué (límite de servicio)

| Servicio | Por qué | Qué no hace |
|---|---|---|
| sv5 | Dueño del `synckey` (`synckey_de`, `PREFIJO_SYNCKEY`) y de su lectura (`lineas_por_synckey`): saber si una línea suya sigue en Sigrid es su conocimiento. Endpoint HTTP **de solo lectura** (R1–R9) | No escribe, no toma el lock, sigue sin BBDD |
| sv4 | Dueño de `parte_registros.sigrid_*`, de la congelación (F-004) y de las vistas: estado nuevo, comprobación al abrir la vista, botón, sondeo (R10–R30) | No lee `hmores` ni conoce el formato del `synckey` |

Descartado que sv4 lea `hmores`: copiaría el criterio de idempotencia de sv5
fuera de la lista cerrada. **HTTP interno síncrono** sv4→sv5 (como el
preflight), no cola: es lectura y quien pregunta espera. sv3 no se toca: su
`esta_congelado` ya deja editable `borrado_sigrid` (guardián de raíz, R13).

## 2. Encaje y flujo

Vista de obra/persona cargada (JS, 2.º plano) o botón (`forzar`) →
`POST /api/sigrid/comprobar` → `ComprobacionSigrid` (TTL por id) → HTTP →
sv5 `/api/registro/comprobar` (`lineas_por_synckey`, `lineas_por_ide`,
`partes_por_ide`) → `repo.aplicar_comprobacion_sigrid` (CAS por línea).

El `GET` de la vista no llama a sv5: se pinta con lo guardado y el navegador
pide la comprobación al cargar (R18). Ámbito: las filas `registrado` que
pinta la vista, que **siempre acota periodo** (`get_obra` toma el más
reciente si no se pide; sin fechas válidas, solo las sueltas): no hace falta
ventana configurable. Ids del navegador: inocuo, sv4 refiltra a `registrado`
y solo cambia lo que diga sv5 (tope 5000 y TTL).

Máquina de estados (solo lo nuevo): `registrado` → `borrado_sigrid`
(veredicto `borrada`, R10); `borrado_sigrid` → `encolado` (Reaprobar) →
`registrado`/`omitido`/`conflicto`/`error` como siempre; `borrado_sigrid` →
`registrado` si sv5 la da por `ya_registrada` (R15). Sin cambio de schema:
`borrado_sigrid` son 14 caracteres en `String(16)`.

## 3. Ficheros a crear

| Ruta | Contenido |
|---|---|
| `services/partes-transfer/application/services/comprobacion_lineas.py` | `LineaComprobar`, `Veredicto`, `clasificar` (pura) y `ComprobadorLineas` (§5.1) |
| `services/partes-transfer/tests/test_f024_comprobacion.py` | R1–R9 (clasificador, cliente con `httpx` simulado, endpoint con `TestClient`) |
| `services/partes-front/application/services/comprobacion_sigrid.py` | `ComprobacionSigrid` y `RegistroComprobaciones` (§5.2) |
| `services/partes-front/tests/test_f024_borrado_sigrid.py` | R10–R16, R22–R24 (repositorio SQLite, congelación, HTML) |
| `services/partes-front/tests/test_f024_comprobar_y_estado.py` | R17–R21, R26–R28, R30 (endpoints; TTL con reloj inyectado; el `GET` de las vistas no llama a sv5) |
| `tests/test_f024_borrado_no_congela_gemelos.py` | R13: `esta_congelado('borrado_sigrid', False)` de sv3 y `motivo_congelacion_linea` de sv4, cada uno en un **subproceso** con `cwd` en su servicio (los dos paquetes se llaman `application`) |

## 4. Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | `lineas_por_ide(ides)` y `partes_por_ide(hmoides)` (§6). `lineas_por_synckey` **no cambia** |
| `services/partes-transfer/interface_adapters/api/app.py` | `POST /api/registro/comprobar` como `def` (hilo del pool, no bloquea el bucle), esquema con tope 500; `build_app(settings, pipeline=None, comprobador=None)` |
| `services/partes-transfer/main.py` | crea `ComprobadorLineas(cliente=cliente)` con el MISMO cliente y lo inyecta |
| `services/partes-front/application/services/congelacion.py` | `ESTADO_BORRADO_SIGRID`; texto de `MOTIVO_LINEA_REGISTRADA` (R16); fuera de `ESTADOS_CONGELANTES` |
| `services/partes-front/infrastructure/database/parte_repository.py` | `ESTADOS_EN_VUELO` + `borrado_sigrid` (R15); `lineas_para_registro(ids, *, incluir_borradas=False)` con `excluidas` (R22); `registrados_para_comprobar(...)`, `aplicar_comprobacion_sigrid(...)`, `recuento_estados(ids)` (§5.2); `RegistroView` sin cambios de campos |
| `services/partes-front/infrastructure/transfer/transfer_client.py` | `comprobar(payload, *, timeout_s)` → `_post` con ese timeout (R17) |
| `services/partes-front/interface_adapters/web/app.py` | `_payload_registro` pasa `incluir_borradas` y devuelve `excluidas` (R22, R23); `encolar` añade `registro_ids` (R27); `POST /api/sigrid/comprobar` (R17, un `RegistroComprobaciones` por proceso) y `POST /api/aprobar/estado` (R28) como `def`; `borradas_sigrid` en el contexto de las dos vistas (R24) |
| `services/partes-front/config/settings.py` | `COMPROBACION_SIGRID_TTL_S=120` (≥0), `COMPROBACION_SIGRID_TIMEOUT_S=30`, `COMPROBACION_SIGRID_LOTE=500` (1–500) |
| `services/partes-front/templates/obra_detail.html`, `trabajador_detail.html` | `data-sigrid-estado` en cada `<tr>`; rama `borrado_sigrid` con «Reaprobar» (`data-incluir-borradas="1"`); aviso de cabecera; botón «Comprobar en Sigrid»; tooltip de `encolado` (R24, R26, R30) |
| `services/partes-front/static/app.js` | comprobación al cargar la vista y su aviso (R18, R20, §5.3); `encolar` sin `reload()`: sondeo de R29; aviso de R30; casilla de R25; botón de R26 (`forzar`); `incluir_borradas` en la aprobación por línea |
| `services/partes-front/static/styles.css` | estilo mínimo del aviso y de la insignia (si `badge danger` no basta) |
| `docs/ARCHITECTURE.md` | semántica 10 (`borrado_sigrid` no congela), semántica 5 (`synckey` va en `hmores.synckey`, no en `tex`), tercer uso del HTTP sv4↔sv5 (comprobar) |
| `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` | endpoint nuevo de sv5, estado `borrado_sigrid` (§4.2), comprobación al abrir obra/persona y variables `COMPROBACION_SIGRID_*` de sv4 |

## 5. Clases y funciones

### 5.1 sv5 · `comprobacion_lineas.py` (application)

```python
@dataclass  # todo opcional salvo registro_id
class LineaComprobar: registro_id; hmores_ide; hmoide; recurso_ide; fecha_int; horas; es_incidencia=False
@dataclass  # estado: "presente" | "borrada"
class Veredicto: registro_id; estado; hmores_ide; hmoide; parte_cod; parte_existe=True; sin_synckey=False; diferencias=[]; motivo
def clasificar(lineas, por_synckey: dict[str, LineaSigrid], por_ide: dict[int, LineaSigrid], partes: dict[int, str]) -> list[Veredicto]
class ComprobadorLineas: __init__(self, *, cliente); comprobar(self, lineas) -> list[Veredicto]
```

`clasificar` es pura: (1) acierto por `synckey_de(registro_id)` → `presente`
(R2, R5); (2) si no, fila de `por_ide[hmores_ide]` con `synckey` vacía y
mismo `reside`, `fecha_int` y `hmoide` (si vino) → `presente` +
`sin_synckey` (R3); (3) si no → `borrada`, `parte_existe = hmoide in partes`
y motivo «la línea N del parte X ya no existe en Sigrid» o «el parte X ya no
existe en Sigrid» (R4). Diferencias (R6): recurso y fecha siempre; horas solo
si `not es_incidencia` y `horas is not None` (las reglas ponen `can=0` a las
incidencias y pueden cambiar el código: el código de hora **no** se compara).
`comprobar` deduplica por `registro_id`, hace las tres lecturas (las de `ide`
solo para los fallos; `partes_por_ide` sobre los `hmoide` de aciertos y
fallos) y llama a `clasificar`; cualquier excepción sube (el endpoint → 502).

### 5.2 sv4 · `comprobacion_sigrid.py` (application) y repositorio

```python
class ComprobacionSigrid:  # __init__(*, repository, transfer_client, lote, timeout_s, recientes)
    def comprobar_ids(self, registro_ids: list[int], *, origen: str, forzar: bool = False) -> dict
class RegistroComprobaciones:  # antimartilleo (R19); __init__(*, ttl_s, reloj=time.monotonic); lock interno
    def reservar(self, ids: list[int], *, forzar: bool) -> list[int]
```

`reservar` devuelve los ids no vistos en los últimos `ttl_s` (todos con
`forzar`), los sella con la hora **al reservar** —un id en curso no se
reenvía y un lote fallido no se reintenta en cada recarga contra un sv5
caído— y purga las entradas caducadas. Por proceso: con dos réplicas de sv4
una obra se comprueba como mucho dos veces por TTL; inocuo por el CAS.

`comprobar_ids`: `registrados_para_comprobar(ids)` → `reservar` → lotes →
`transfer_client.comprobar({"lineas": [...]})` → si `ok` y hay un veredicto
por línea, `aplicar_comprobacion_sigrid(veredictos, enviados, ahora_iso)`; si
no, el lote no se aplica, se anota `fallidos` y **se para** (R14). Devuelve
`{ok, comprobadas, recientes, borradas, borradas_ids, actualizadas,
sin_synckey, con_diferencias, fallidos}` y deja el log de R21.

Repositorio (`parte_repository.py`):
- `registrados_para_comprobar(registro_ids) -> list[dict]`: de esos ids,
  solo `sigrid_estado='registrado'` (normalizado); campos de `LineaComprobar`
  (`hmoide` = `sigrid_hmoide`).
- `aplicar_comprobacion_sigrid(veredictos, enviados: dict[int, int | None],
  ahora_iso) -> dict`: una sesión; por línea, `session.get` y CAS (R11):
  estado `registrado` y `sigrid_hmores_ide == enviados[id]`; `borrada` →
  R10; `presente` con referencias distintas → R12; nada más se toca.
- `recuento_estados(registro_ids) -> dict`: R28.
- `lineas_para_registro(..., incluir_borradas)`: excluye por estado
  normalizado y cuenta (R22); `registro_ids_de_obra` no cambia.

### 5.3 sv4 · navegador (`app.js`)

Al cargar obra o persona (si existe el botón), `comprobarVista()` reúne los
ids de `tr[data-sigrid-estado="registrado"]` y hace el `POST` sin `forzar`,
con `AbortController` a 90 s. Con `borradas_ids`, cambia el texto de su
celda Sigrid a «✗ borrada en Sigrid» y muestra el aviso con «Actualizar»
(los controles de edición llegan con la recarga, que decide el usuario,
DA9). Con error, 4xx/5xx o plazo vencido: nota discreta junto al botón y
nada más. Sin borradas: «Comprobado en Sigrid hh:mm» atenuado.

## 6. SQL (solo lecturas de Sigrid; sin PostgreSQL nuevo ni schema)

Las dos consultas nuevas van por `_read` (base `ruesma`, `max_rows` 1000,
`truncated` ⇒ excepción) en lotes de 200 (R7). La base es la de escritura, no
`ruesma_rep`: una réplica con retraso daría por borradas líneas recién
escritas.

- `lineas_por_ide` (R3, solo fallos): `SELECT ide, hmoide, reside, fec,
  horide, can, tot, synckey FROM hmores WHERE ide IN (?, …)`.
- `partes_por_ide` (R4, R5): `SELECT hmo.ide, con.cod FROM hmo JOIN con ON
  con.ide = hmo.ide WHERE hmo.ide IN (?, …)`.

Volumen: 500 líneas = ≤ 8 lecturas (segundos), lejos de 1.000 filas, 2.100
parámetros y 230 s. Una vista: 1–3 peticiones a sv5, como mucho una por TTL.

## 7. Ficheros que NO se tocan y fuera de alcance

- `registro_pipeline.py`, `reglas_registro.py`, `coherencia_recurso.py`,
  `lineas_por_synckey` y las sentencias de escritura de sv5.
- `orm_models.py` (las dos copias), `resultado_sigrid.py`,
  `resultado_consumer.py`, `services/partes-persistencia/**`, `infra/`.
- **Fuera**: borrar en Sigrid desde el portal; traer al portal los valores
  que Administración cambie a mano (R6 solo informa); auditar quién borra
  (Sigrid no lo guarda, explore §6); F-021 (cuenta analítica).

## 8. Decisiones abiertas (el humano aprueba o rebate; recomendación en negrita)

1. **DA1 · Cuándo (revisada por el humano el 2026-10-01)**: **al entrar en
   la vista de obra, en segundo plano, acotada a sus líneas `registrado` del
   periodo mostrado**, más el botón «Comprobar en Sigrid» para forzarla. Sin
   barrido horario. Descartado comprobar dentro del `GET` (la vista tardaría
   o caería con Sigrid lento) y una ventana configurable (la vista ya acota).
2. **DA2 · Quién consulta**: **sv5**, endpoint HTTP interno de solo lectura
   (§1). La lista cerrada de duplicación no crece.
3. **DA3 · Criterio**: **el de la idempotencia** (`synckey`), más el respaldo
   estricto por `ide` (R3). Así `borrada` ⇔ «reaprobar la escribiría»; un
   falso `borrada` no duplica (sv5 la vería por `synckey` o como conflicto).
4. **DA4 · Estado y referencias**: **`borrado_sigrid`**, no congela,
   **conserva** `sigrid_parte_cod`/`sigrid_hmores_ide`/`sigrid_hmoide` como
   rastro y no toca `sigrid_registrado_at/by` (la fecha va en el motivo):
   lo marca una comprobación, no un registro. Al reaprobar, `escritas`
   pisa las referencias.
5. **DA5 · Modificadas a mano**: **no cambian de estado**; Sigrid manda y la
   línea sigue congelada. Las diferencias se ven en el resultado del botón y
   en el log. Alternativa: persistirlas (columna o prefijo en el
   motivo, que ya usa `[SIN-SESAME]`).
6. **DA6 · Cabecera borrada**: **misma transición**, motivo propio; al
   reaprobar sv5 crea un parte nuevo con otro `PT<AA>/NNNNN`.
7. **DA7 · Aprobaciones masivas**: **excluyen siempre `registrado`** (hoy
   «Aprobar todo» las reencola y, si Administración las borró, **las
   reescribe**) **y `borrado_sigrid` salvo casilla explícita**; por línea,
   «Reaprobar». Arregla también D1 y D3 de explore §3.3.
8. **DA8 · `encolado` sigue entrando** en las masivas (salida de un atasco).
9. **DA9 · Vista con resultado pendiente**: **aviso con «Actualizar»**, sin
   recarga automática (recargar sola perdería lo que se esté tecleando). El
   modal sí recarga al cerrarlo, con el resultado ya llegado.
10. **DA10 · Las 35 de septiembre**: **al entrar en la obra 0719** en el
    periodo que contiene el 16–28/09, tras desplegar (sin script: otro camino
    de escritura en `partes` sin tests). Las `registrado` de otras obras (p.
    ej. las de modo pruebas ya limpiadas) se marcarán cuando alguien abra su
    obra o persona; las de la papelera no se comprueban. Después, el
    humano lanza la reconciliación de recursos de F-023 (M3), que ya puede
    corregir el recurso de baja porque `borrado_sigrid` no congela, y
    reaprueba.
11. **DA11 · Despliegue sv5 → sv4**. sv4 nuevo contra sv5 viejo recibe 404:
    `ok: false`, nada cambia (R14).
12. **DA12 · Desaprobar**: **sin cambios** (F-004 nunca borra en Sigrid).
13. **DA13 · Aviso inmediato (antes de desplegar)**: **no usar «Aprobar
    todo»** en la obra 0719 · 09/2026 ni «Aprobar visibles» en la ficha de
    sus trabajadores: reescribiría las líneas borradas a propósito.
14. **DA14 · Antimartilleo**: **TTL de 120 s por línea y proceso**, sellado
    al reservar (recargas, varios usuarios en la misma obra y obra↔persona
    no repiten; un sv5 caído no recibe una petición por recarga); el botón lo
    salta. Lote 500, timeout 30 s; todo configurable (§4).
15. **DA15 · Vista de persona**: **también comprueba al entrar** (mismo
    endpoint y JS, otro `origen`): ahí también se aprueba y se ve el estado
    Sigrid, y el TTL evita repetir lo ya visto en la obra. Alternativa: en
    persona, solo el botón.

## 9. Verificaciones manuales (humano)

- **M1 · antes de desplegar (PG `partes`, lectura)**: cuántas `registrado`
  hay y de qué partes —las de modo pruebas de la 0404 ya limpiadas también
  saldrán `borrado_sigrid`, y es correcto—:
  `SELECT sigrid_parte_cod, min(fecha_int), max(fecha_int), count(*) FROM
  parte_registros WHERE sigrid_estado = 'registrado' GROUP BY 1 ORDER BY 1;`
- **M2 · despliegue** (lo pide el humano): `redeploy_partes.ps1 -Solo sv5` y
  después `-Solo sv4`.
- **M3 · abrir la obra 0719** (Ctrl+F5) en el periodo que contiene el
  16–28/09 y esperar unos segundos: aviso «35 líneas ya no están en Sigrid».
  Log Analytics: `ContainerAppConsoleLogs_CL | where ContainerAppName_s ==
  'ca-sv4-front' and Log_s has '[comprobacion-sigrid]'` → `origen=vista-obra
  … borradas=35`, y en `ca-sv5-transfer` `[comprobar]` sin `[sigrid-write]`
  en ese intervalo. Recargar antes de 120 s: ninguna línea nueva en el log.
- **M4 · R31 (PG, lectura)**: `SELECT sigrid_estado, count(*) FROM
  parte_registros WHERE sigrid_parte_cod = 'PT26/00314' GROUP BY 1;` →
  **35 `borrado_sigrid`** y ninguna `registrado`.
- **M5 · navegador**, obra 0719 tras «Actualizar»: aviso de borradas,
  «Reaprobar» por línea, «Comprobar en Sigrid» → modal con 0 borradas
  nuevas; ficha de un trabajador afectado sin consulta nueva (TTL); aprobar una línea de prueba (modo pruebas, obra 0404) y ver el
  sondeo del modal sin recarga prematura (R25, R29, R30).

## 10. Riesgos

- **Falso `borrada`** (Sigrid devolviendo menos filas sin error): `truncated`
  ⇒ error y CAS; reaprobar no duplica (DA3). **`app.js`** sin tests: M5.
- **Tests de F-002/F-003 que esperan `registrado` en el payload** (DA7): se
  adaptan en T1 con la decisión escrita, no se borran.
- **Mutación** sobre `app.py` y `parte_repository.py`: solo hunks cambiados.
