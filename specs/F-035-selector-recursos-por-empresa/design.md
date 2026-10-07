# F-035 · Portal: elegir trabajador entre recursos activos de Sigrid, por empresa — Diseño

## 1. Encaje y límite de servicio

**Solo sv4.** Es presentación y edición del portal: qué lista ofrece cada
selector y qué escribe en la línea al elegir. Las reglas que deciden el
recurso escrito en Sigrid **no se mueven**:

- **sv3** (`recurso_conciliador`) recalcula en cada pasada el recurso de toda
  línea no congelada con `elegir_recurso(empleado_dni, empleado_ide,
  empleado_reside, empresa de la obra, fecha)`: lo encuentra por la ficha **o
  por `res.cif`** (F-030); `empleado_reside` es el preferido si hay varios.
- **sv5** verifica el `recurso_ide` (empresa de la obra, alta a la fecha, DNI)
  o, sin él, lo elige por DNI (`elegir_por_dni`).

Por eso sv4 guarda lo mismo que hoy (`empleado_*`, DNI) **más** el `reside`
elegido, y suelta el recurso como en F-023 R42. No se copia `de_alta` ni la
elección por DNI: el filtro de alta va en SQL, igual que `_SQL_EMPLEADOS`
(DA2). Ninguna responsabilidad nueva fuera de sv4.

**Criterio de persona** (humano, 2026-10-07): el de `porcentajes`
(`dedicacion-api/config/config.yaml`, `sync.empleados.sql`): recurso de
clase persona (`res.cla = 1`), uno por recurso, empresa `rcon.emp`, de alta;
DNI = `res.cif` o, vacío, el de la ficha (`res.conide > 0`). Sin el filtro de
hora mensual. **F-036** (otra spec) llevará el mismo criterio al casado de
sv3; F-035 no copia nada a sv3.

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
SELECT res.ide AS ide, rescon.cod AS codigo, rescon.res AS nombre,
       rescon.emp AS empresa, res.cif AS cif,
       emp.ide AS empleado_ide, empcon.cod AS empleado_codigo,
       emp.res AS empleado_nombre, emp.dni AS empleado_dni,
       auxrestip.res AS categoria, reshor.candef AS candef
FROM res
JOIN con rescon ON rescon.ide = res.ide
LEFT JOIN emp ON emp.ide = res.conide AND res.conide > 0
LEFT JOIN con empcon ON empcon.ide = emp.ide
LEFT JOIN auxrestip ON auxrestip.ide = res.restipide
LEFT JOIN reshor ON reshor.reside = res.ide AND reshor.horide = res.horide
WHERE res.cla = 1
  AND (rescon.fecbaj IS NULL OR rescon.fecbaj = 0 OR rescon.fecbaj > ?)
```

Parámetro: hoy `YYYYMMDD`. Orden de paginación `res.ide`. El predicado de
alta es literalmente el de `_SQL_EMPLEADOS` (`rescon.…`), que es lo que el
guardián compara. La clase (R4) va en SQL, como en porcentajes; el DNI se
decide en Python (testeable).

`fetch_recursos_activos() -> list[RecursoOption]`, en el mismo estilo que
`fetch_empleados`: una opción por `ide` (filas repetidas solo completan
`categoria`/`candef`), y además:

- `dni` = `cif` si no está vacío; si no, `empleado_dni` (R2).
- Se descarta la fila que sigue sin DNI (R3), con un INFO de recuento.

```python
@dataclass(frozen=True)
class RecursoOption:
    ide: int                      # res.ide
    codigo: str | None            # con.cod del recurso
    nombre: str | None            # con.res del recurso
    dni: str | None               # cif o, vacío, el de la ficha
    empresa: int | None
    empleado_ide: int | None = None      # ficha enlazada (o None)
    empleado_codigo: str | None = None
    empleado_nombre: str | None = None
    empleado_dni: str | None = None
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

`asignacion_de`: con ficha → `(r.empleado_ide, r.empleado_codigo,
r.empleado_nombre, r.empleado_dni or r.dni, r.ide)`; sin ficha → `(None, r.codigo, r.nombre, r.dni, r.ide)`.
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
- `GET /obras/{obra_key}`: `empresa_obra` = empresa de
  `obra_catalog.get_by_ide(detail.obra_ide)`, o None (sin ide, error).

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

- `fetchRecursos()` sobre `/api/sigrid/recursos`, caché única (filtro en
  cliente); `recLabel(r)` = código · nombre + `empresaSufijo`.
- `wireEmpleadoCombo`: lista `fetchRecursos()` filtrada por
  `wrap.dataset.empresa` si existe; `_empReasignar` envía `recurso_ide`.
- Conciliar: `_confirmarCasado` envía `{nombre_leido, recurso_ide}`; el
  `change` de `.recon-empresa` oculta filas con otro `data-empresa` y relanza
  la búsqueda; la búsqueda manual añade `&empresa=` si hay valor.
- Nuevo parte y modal: combo de trabajador sobre `fetchRecursos()`, filtro =
  valor del selector de empresa (vacío = todas); al elegir obra con empresa,
  el selector toma su valor y se deshabilita (DA1), y se vacía el trabajador
  si era de otra empresa (lógica F-023); al elegir recurso se copian los
  `guardar.*` a los hidden (con `…-emp-reside`) y `categoria` /
  `jornada_sugerida` como hoy; el payload del modal añade `empleado_reside`.

## 6. Tests (sin red ni PostgreSQL)

Cliente con `_post_sql_read` parcheado (patrón `test_f023_catalogo_empresa`);
portal con `monkeypatch` de `SigridLookupClient` por un doble que añade
`fetch_recursos_activos`, `FabricaSesionSqlite` + `ParteReviewRepository`
reales y `TestClient`. Datos sintéticos (empresas 1 y 28, todos `cla = 1`
salvo uno): con `cif` y ficha, sin `cif` con ficha con DNI, con `cif` sin
ficha, sin `cif` ni ficha, y uno `cla = 2` (comprobado en el texto del SQL).

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

- **Rigor estándar** (`features.json`): solo sv4, sin schema; lo que llega a
  Sigrid sigue pasando por sv3 (recálculo) y sv5 (verificación), sin cambios.
- **Se suelta el recurso al reasignar** (F-023 R42) en vez de escribir
  `recurso_ide`: en Conciliar una tarjeta puede mezclar obras de dos empresas
  y el recurso depende de obra y fecha; el `reside` queda de preferido. En
  «Nuevo parte» sí se escribe (como hoy): la obra fija la empresa (DA1).
- **Alta a hoy**, como el catálogo de empleados (sv5 decide a la fecha).
- **DNI guardado con ficha** (R12): `emp.dni` primero, porque sv5 verifica
  contra `emp.dni` o `res.cif` en ese orden; guardar `cif` con una ficha de
  DNI escrito distinto (p. ej. cero inicial) haría omitir la línea por «otra
  persona». El DNI ofrecido y el filtro R3 siguen el criterio del humano.
- **Ficha enlazada solo por `res.conide`**: un recurso con `cif` igual al DNI
  de una ficha pero sin `conide` se guarda «sin ficha» (`recurso_manual`);
  sv3 lo resuelve igual por DNI; solo cambia su agrupación en el listado.
- Dos recursos activos de una persona salen dos veces (códigos distintos).
- Empresas fuera de `NOMBRES_EMPRESA` solo se ven con «Todas».

## 8. Decisiones (todas resueltas por el humano el 2026-10-07)

- **DA1. Empresa con obra elegida — APROBADA la recomendada (2026-10-07)**:
  el selector toma la empresa de la obra y **queda bloqueado** (un recurso de
  otra empresa sería omitido por sv5); descartado «editable con aviso».
- **DA2. Lista cerrada de duplicación — APROBADA la recomendada
  (2026-10-07)**: el nuevo `_SQL_RECURSOS_ACTIVOS` repite en sv4 el filtro de
  alta; se amplía la entrada de `CLAUDE.md` («el filtro de alta de los SQL de
  empleados **y de recursos** de sv4») y el guardián lo vigila; descartado
  filtrar en Python con una tercera copia de `de_alta`.
- **DA3 y DA4: resueltas por el humano (2026-10-07)**: criterio de persona de
  porcentajes (`res.cla = 1`) y DNI `res.cif` con respaldo en la ficha; el
  recurso que siga sin DNI no se ofrece (§1, R3, R4).
