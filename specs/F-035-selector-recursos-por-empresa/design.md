# F-035 · Portal: elegir trabajador entre recursos activos de Sigrid, por empresa — Diseño

## 1. Encaje y límite de servicio

**Solo sv4.** Es presentación y edición del portal: qué lista ofrece cada
selector y qué escribe en la línea al elegir. Las reglas que deciden el
recurso escrito en Sigrid **no se mueven**:

- **sv3** (`recurso_conciliador`) recalcula en cada pasada el recurso de toda
  línea no congelada con `IndicePersonas.elegir_recurso(empleado_dni,
  empleado_ide, empleado_reside, empresa de la obra, fecha)`. Encuentra el
  recurso por la ficha **o por `res.cif`** (F-030), así que una línea sin
  ficha y con `empleado_dni = res.cif` se resuelve; `empleado_reside` actúa de
  preferido si la persona tiene varios.
- **sv5** verifica el `recurso_ide` (empresa de la obra, alta a la fecha, DNI)
  o, sin él, lo elige por DNI (`elegir_por_dni`).

Por eso sv4 guarda lo mismo que hoy (`empleado_*`, DNI) **más** el `reside`
elegido, y suelta el recurso como en F-023 R42. No se copia `de_alta` ni la
elección por DNI: el filtro de alta va en SQL, igual que `_SQL_EMPLEADOS`
(DA2). Ninguna responsabilidad nueva fuera de sv4.

## 2. Ficheros (bajo `services/partes-front/` salvo indicación)

| Acción | Ruta | Cambio |
|---|---|---|
| Modificar | `infrastructure/sigrid/sigrid_lookup_client.py` | `RecursoOption`, `_SQL_RECURSOS_ACTIVOS`, `fetch_recursos_activos()` (§3) |
| Crear | `application/services/recurso_catalog.py` | `RecursoCatalog`, `Asignacion`, `asignacion_de()` (§4) |
| Modificar | `infrastructure/database/parte_repository.py` | `_poner_trabajador`, `reside` en las 4 asignaciones, `METODO_RECURSO_MANUAL`, undo, `crear_parte_manual`, empresas en `list_unmatched_workers` (§4) |
| Modificar | `interface_adapters/web/app.py` | catálogo, `/api/sigrid/recursos`, Conciliar, confirmar/reasignar/buscar, detalle de obra, global `EMPRESAS` (§5) |
| Modificar | `templates/conciliacion.html`, `nuevo_parte.html`, `base.html`, `obra_detail.html` | selectores de empresa y atributos (§5) |
| Modificar | `static/app.js` | combos sobre recursos (§5) |
| Crear | `tests/test_f035_*.py` | §6 |
| Modificar | `tests/test_f023_de_alta_gemelos.py` (raíz) | + test de `_SQL_RECURSOS_ACTIVOS` (R23) |
| Modificar | `docs/ARCHITECTURE.md` (raíz), `CLAUDE.md` (raíz) | R24: una frase en semántica 12; lista cerrada (DA2) |

**No se tocan**: `_SQL_EMPLEADOS`, `fetch_empleados`, `EmpleadoCatalog`,
`/api/sigrid/empleados` (los usa la pantalla de jornadas y su aviso de DNI),
`empleado_reconciler.py`, `text_match.py`, `orm_models.py`, sv3, sv5,
`azure-apps/partes.md` (misma API consumida, `/api/sql/read`),
`trabajadores_list.html`, `parte_detail.html` (solo usa el modal de base).

## 3. SQL (sigrid-api, `/api/sql/read`, base de lectura)

```sql
-- _SQL_RECURSOS_ACTIVOS: paginado por res.ide con _leer_paginado
SELECT res.ide AS ide, rescon.cod AS codigo, rescon.res AS nombre_recurso,
       rescon.emp AS empresa, res.cif AS cif,
       emp.ide AS empleado_ide, empcon.cod AS empleado_codigo,
       emp.res AS empleado_nombre, emp.dni AS empleado_dni,
       auxrestip.res AS categoria, reshor.candef AS candef
FROM res
JOIN con rescon ON rescon.ide = res.ide
LEFT JOIN emp ON emp.ide = res.conide
LEFT JOIN con empcon ON empcon.ide = emp.ide
LEFT JOIN auxrestip ON auxrestip.ide = res.restipide
LEFT JOIN reshor ON reshor.reside = res.ide AND reshor.horide = res.horide
WHERE (rescon.fecbaj IS NULL OR rescon.fecbaj = 0 OR rescon.fecbaj > ?)
```

Parámetro: hoy `YYYYMMDD`. Orden de paginación `res.ide`. El predicado de
alta es literalmente el de `_SQL_EMPLEADOS` (`rescon.…`), que es lo que el
guardián compara. Todo lo demás se filtra en Python (testeable).

`fetch_recursos_activos() -> list[RecursoOption]`, en el mismo estilo que
`fetch_empleados`: una opción por `ide` (filas repetidas solo completan
`categoria`/`candef`), y además:

- `dni` = `empleado_dni` si no está vacío; si no, `cif` (R2).
- `nombre` = `empleado_nombre` si hay ficha; si no, `nombre_recurso`.
- Se descarta la fila sin DNI (R3) y la que no es `MO/` ni tiene ficha (R4),
  con un INFO de recuento de descartes.

```python
@dataclass(frozen=True)
class RecursoOption:
    ide: int                      # res.ide
    codigo: str | None            # código del recurso (MO/…)
    nombre: str | None
    dni: str | None
    empresa: int | None
    empleado_ide: int | None = None
    empleado_codigo: str | None = None
    categoria: str | None = None
    candef: float | None = None
```

## 4. Aplicación y repositorio

`application/services/recurso_catalog.py`:

```python
class RecursoCatalog:                       # TTL 600 s, RLock, como EmpleadoCatalog
    enabled: bool
    def list(self, empresa: int | None = None) -> list[RecursoOption]
    def get_by_ide(self, ide: int | None) -> RecursoOption | None

@dataclass(frozen=True)
class Asignacion:                           # lo que se escribe en la línea
    empleado_ide: int | None
    codigo: str | None
    nombre: str | None
    dni: str | None
    reside: int

def asignacion_de(r: RecursoOption) -> Asignacion
```

`asignacion_de`: con ficha → `(r.empleado_ide, r.empleado_codigo, r.nombre,
r.dni, r.ide)`; sin ficha → `(None, r.codigo, r.nombre, r.dni, r.ide)`.
Es el ÚNICO sitio con esta regla: el endpoint la serializa para el JS (§5).
Fallo de refresco: WARNING y se conserva la lista anterior (R6).

`parte_repository.py`:

- `METODO_RECURSO_MANUAL = "recurso_manual"` y `METODOS_RECURSO` lo incluye
  (así `esta_casado` y `_sin_casar_en_cola` lo cubren sin más cambios).
- `_poner_trabajador(r, *, ide, codigo, nombre, dni, reside)`: escribe los
  cuatro `empleado_*`, llama a `_soltar_recurso(r)` y, si `reside` no es
  None, `r.empleado_reside = reside`; si además `ide` es None,
  `r.empleado_match_method = METODO_RECURSO_MANUAL`. Sustituye los cuatro
  bloques idénticos de `backfill_empleado`, `reassign_empleado_by_leido`,
  `…_by_worker_key` y `…_by_registro_ids`, que ganan `reside: int | None =
  None` y aceptan `ide: int | None`. Sin `reside`, comportamiento idéntico
  al actual (los tests F-023 R42 siguen valiendo).
- `_REG_UNDO_FIELDS` + `"empleado_reside"`, `"empleado_match_method"`
  (R16; `_apply_reg_snapshot` ya ignora claves ausentes).
- `crear_parte_manual`: `empleado_match_method = METODO_RECURSO_MANUAL`
  cuando `empleado_ide` es None y `empleado_reside` no (R19). Lo demás igual.
- `list_unmatched_workers`: cada grupo añade `empresas` (lista ordenada de
  `doc.empresa` no nulas de sus partes).

## 5. Interfaz (app.py, plantillas, JS)

**app.py**

- `recurso_catalog = RecursoCatalog(client=sigrid_client)` junto a los
  demás; `app.state.recurso_catalog`. Global Jinja `EMPRESAS` =
  `sorted(NOMBRES_EMPRESA.items())`.
- `GET /api/sigrid/recursos?empresa=` (R5): items `{ide, codigo, nombre,
  dni, empresa, categoria, candef, jornada_sugerida, guardar}` con
  `guardar = {empleado_ide, empleado_codigo, empleado_nombre, empleado_dni,
  empleado_reside}` de `asignacion_de`. `jornada_sugerida` con la misma
  `_sugerida` (se extrae a función local compartida con `/empleados`).
- `GET /conciliacion`: por tarjeta, `empresa_defecto` = la única de
  `p["empresas"]` o None; `classify(nombre, recurso_catalog.list(empresa_defecto))`;
  cada candidato añade `empresa` (por `get_by_ide`) y `empresa_nombre`
  (`nombre_empresa`). `empleados_total` pasa a contar recursos.
- `/api/conciliacion/buscar`: `empresa: int | None` y busca sobre
  `recurso_catalog.list(empresa)`; items con `empresa`.
- `/api/conciliacion/confirmar` y `/api/empleado/reasignar`: si el body trae
  `recurso_ide` → `asignacion_de(recurso_catalog.get_by_ide(...))` (404 si no
  está) y se pasan `ide/codigo/nombre/dni/reside`; alias solo si
  `empleado_ide` no es None (R14). Sin `recurso_ide`, el camino `ide` de hoy
  intacto (R15). La respuesta mantiene `empleado: {ide, codigo, nombre}`.
- `GET /obras/{obra_key}`: contexto `empresa_obra` = empresa de
  `obra_catalog.get_by_ide(detail.obra_ide)` (None si no hay ide, catálogo
  apagado o excepción).

**Plantillas**

- `conciliacion.html`: en cada tarjeta `<select class="recon-empresa">`
  («Todas» = `""` + `EMPRESAS`) con `empresa_defecto` seleccionada; filas de
  candidato con `data-empresa`, sufijo de empresa y botón
  `data-recurso-ide`; placeholder «Buscar otro recurso…».
- `nuevo_parte.html`: campo «Empresa» `<select id="emp-empresa">` encima de
  «Trabajador»; placeholder «Código, nombre o DNI…».
- `base.html` (modal): `<select id="addline-empresa">` encima del trabajador
  y `<input type="hidden" id="addline-emp-reside">`.
- `obra_detail.html`: `.combo-emp` con `data-empresa="{{ empresa_obra }}"`
  solo si no es None.

**app.js**

- `RECURSOS_URL = "/api/sigrid/recursos"`, `fetchRecursos()` con caché única
  (todas las empresas; el filtro es en cliente). `recLabel(r)` = código ·
  nombre + `empresaSufijo`.
- `wireEmpleadoCombo`: lista `fetchRecursos()` filtrada por
  `wrap.dataset.empresa` si existe; `_empReasignar` envía `recurso_ide`.
- Conciliar: `_confirmarCasado` envía `{nombre_leido, recurso_ide}`; el
  `change` de `.recon-empresa` oculta filas con otro `data-empresa` y relanza
  la búsqueda; la búsqueda manual añade `&empresa=` si hay valor.
- Nuevo parte y modal: combo de trabajador sobre `RECURSOS_URL`, filtro =
  valor del selector de empresa (vacío = todas); al elegir obra con empresa,
  el selector toma su valor y se deshabilita (DA1), y se vacía el trabajador
  si era de otra empresa (lógica F-023 ya existente); al elegir recurso se
  copian los `guardar.*` a los hidden (`emp-reside` / `addline-emp-reside`
  incluidos) y `categoria` / `jornada_sugerida` como hoy. El payload del
  modal añade `empleado_reside`. `mismaEmpresa` se sustituye por la lectura
  del selector.

## 6. Tests (sin red ni PostgreSQL)

Cliente con `_post_sql_read` parcheado (patrón `test_f023_catalogo_empresa`);
portal con `monkeypatch` de `SigridLookupClient` por un doble que añade
`fetch_recursos_activos`, `FabricaSesionSqlite` + `ParteReviewRepository`
reales y `TestClient`. Datos sintéticos: empresa 1 y 28, un recurso `MO/`
con ficha, uno `MO/` sin ficha con `cif`, uno sin DNI, uno `MAQ/` sin ficha.

| Fichero | Tests (R) |
|---|---|
| `test_f035_recursos_cliente.py` | R1 (paginado, parámetro hoy, predicado), R2 (ficha/sin ficha, regla de DNI y nombre), R3, R4 |
| `test_f035_recurso_catalog.py` | R5 (filtro por empresa), R6, `asignacion_de` para R12/R13 |
| `test_f035_endpoints.py` | R5 endpoint, R9, R11 (404 y ok), R12, R13, R14, R15, R19, R21 |
| `test_f035_repositorio.py` | R12–R13 en las 4 asignaciones, R16, R19 (fuera de la cola) |
| `test_f035_vistas.py` (HTML) | R7, R8, R10, R17, R18 (selects y opciones), R20 |
| `tests/test_f023_de_alta_gemelos.py` | `test_f035_r23_...` |

R22: suite completa sin tocar tests ajenos. Fase RED con traza para R2–R4,
R8, R12–R16 y R19. `node --check static/app.js` y parseo Jinja2 de las cuatro
plantillas.

## 7. Riesgos y decisiones

- **Rigor estándar** (el de `features.json`): solo sv4, sin schema; lo que
  llega a Sigrid sigue pasando por la verificación de sv5 (empresa, alta,
  DNI) y por el recálculo de sv3, que no cambian. Un recurso mal elegido
  acaba igual que hoy un empleado mal elegido.
- **Se suelta el recurso al reasignar** (F-023 R42) en vez de escribir
  `recurso_ide` = el elegido: en Conciliar la tarjeta puede mezclar obras de
  dos empresas y el recurso bueno depende de la obra y la fecha de cada
  línea. El `reside` queda como preferido para sv3. En «Nuevo parte» sí se
  escribe `recurso_ide` (como hoy), porque la empresa queda fijada por la
  obra (DA1).
- **Alta a hoy**, como el catálogo de empleados: un recurso dado de baja
  después de la fecha del parte no se ofrece (caso raro; sv5 decide al
  escribir).
- **Ficha enlazada solo por `res.conide`**: un recurso con `cif` igual al DNI
  de una ficha pero sin `conide` se guarda como «sin ficha» (`empleado_ide`
  NULL, `recurso_manual`); sv3 lo resuelve igual por DNI. Solo cambia su
  agrupación en el listado de trabajadores.
- Una persona con dos recursos activos en la misma empresa sale dos veces
  (códigos distintos): es lo que hay en Sigrid y el código los distingue.
- Empresas fuera de `NOMBRES_EMPRESA` solo se ven con «Todas».

## 8. Decisiones abiertas (para el humano)

- **DA1. Empresa con obra elegida**: el selector toma la empresa de la obra y
  **queda bloqueado** (recomendado: un recurso de otra empresa sería omitido
  por sv5) vs. editable con aviso.
- **DA2. Lista cerrada de duplicación**: el nuevo `_SQL_RECURSOS_ACTIVOS`
  repite en sv4 el filtro de alta; se propone ampliar la entrada de
  `CLAUDE.md` («el filtro de alta de los SQL de empleados **y de recursos** de
  sv4») y que el guardián lo vigile (recomendado) vs. filtrar en Python con una
  tercera copia de `de_alta`.
- **DA3. Recursos sin DNI**: no se ofrecen (recomendado: sv3 y sv5 identifican
  por DNI y la línea quedaría «sin recurso» para siempre) vs. ofrecerlos y
  cambiar sv3 para casar por `reside` (otra feature, rigor crítico).
- **DA4. Qué es «recurso de una persona»**: código `MO/` o con ficha enlazada
  (recomendado; es el criterio de F-030 más los enlazados) vs. solo `MO/`.
