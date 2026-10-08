<!-- specs/F-040-recursos-sin-dni-por-nombre/design.md -->
# F-040 · Recursos sin DNI: proponer por nombre, aprender alias por recurso y poder registrarlos — Diseño

## 1. Encaje y límite de servicio

- **sv3** casa (ingesta) y elige el recurso de cada línea (conciliador): es
  donde vive «quién es la persona». Gana una identidad para quien no tiene DNI
  (la **clave de persona**: `emp:<conide>` o `res:<ide>`), la usa para competir
  por nombre (R1–R5) y para resolver el alias (R6–R8), y el conciliador
  conserva el recurso de una línea sin DNI casada a mano (R9–R11).
- **sv4** es quien ofrece candidatos y aprende alias. Deja de esconder los
  recursos sin DNI (los marca) y aprende el alias contra el recurso (R14–R19).
- **sv5** es el último punto antes del ERP. Hoy ya deja pasar una línea sin DNI
  con `recurso_ide` (solo mira empresa y alta): F-040 no le abre nada, le
  **acota** esa rama a recursos persona sin DNI (R22–R25, DA3), la gemela de
  `elegir_sin_dni` de sv3.
- **Esquema**: `empleado_alias` (base `partes`) lo completan sv3 y sv4 al
  arrancar (`ddl_complementario`). sv1 y sv2 no cambian; nada se copia salvo
  lo de la lista cerrada (§6).

## 2. Ficheros

`sv3` = `services/partes-persistencia/`, `sv4` = `services/partes-front/`,
`sv5` = `services/partes-transfer/`.

| Acción | Ruta | Cambio |
|---|---|---|
| Modificar | sv3 `application/services/seleccion_sigrid.py` | `clave_persona`, `casar_por_clave`, `elegir_sin_dni`; `candidatos_nombre` sin exigir DNI; rama R10 en `elegir_recurso` (§3) |
| Modificar | sv3 `application/services/casado_recurso.py` | `_casar_nombre` por clave y `nombre_sin_dni`; `_casar_alias` R7–R8; `_a_match` DNI vacío → None (§4) |
| Modificar | sv3 `application/services/recurso_conciliador.py` | `MOTIVOS_SIN_RECURSO_A_REVISAR` + `"con_dni"` (R11). Nada de congelación |
| Modificar | sv3 `empleado_matcher.py`, `sigrid_matcher_provider.py`, `domain/models/parte_records.py` | solo textos: persona = clave; INFO de F-036 R3 «se proponen por nombre»; método `nombre_sin_dni` |
| Modificar | sv3 `infrastructure/database/sqlalchemy_parte_repository.py` | `find_empleado_alias` devuelve `recurso_ide` (R6) |
| Modificar | sv3 y sv4 `infrastructure/database/orm_models.py` | `EmpleadoAliasOrm` + `DDL_EXTRA_POSTGRES` (§5), byte-idénticos |
| Modificar | sv3 `application/services/medicion_casado.py` | R28 (§7); `medir_casado_recursos.py` solo docstring |
| Modificar | sv4 `infrastructure/sigrid/sigrid_lookup_client.py` | `fetch_recursos_activos` ya no descarta sin DNI (R14); el SQL no cambia |
| Modificar | sv4 `application/services/recurso_catalog.py` | docstrings («con o sin DNI»); `asignacion_de` ya da `dni` None |
| Modificar | sv4 `infrastructure/database/parte_repository.py` | `upsert_empleado_alias(…, ide: int \| None, recurso_ide: int \| None)` con guarda R18; snapshots de alias con `recurso_ide` (R19) |
| Modificar | sv4 `interface_adapters/web/app.py` | `conciliacion_confirmar` y `empleado_reasignar`: alias con `ide` o `reside` (R17) |
| Modificar | sv4 `static/app.js`, `templates/conciliacion.html` | marca «sin DNI» en los 4 puntos de JS que pintan `DNI …`/`· dni` y en la plantilla (R15) |
| Modificar | sv5 `domain/models/registro_models.py` | `RecursoSigrid.cla: Optional[int] = None` |
| Modificar | sv5 `infrastructure/sigrid/sigrid_write_client.py` | `datos_recursos`: `res.cla AS cla` y mapeo (R22) |
| Modificar | sv5 `application/services/coherencia_recurso.py` | `CLA_PERSONA = 1`; rama sin DNI de `verificar_recurso` (R23–R25) |
| Modificar | sv5 `application/services/reglas_registro.py` | `MOTIVO_RECURSO_NO_PERSONA`, `MOTIVO_RECURSO_CON_DNI` |
| Crear | `tests/test_f040_recurso_sin_dni_gemelos.py` (raíz) | guardián R26 |
| Modificar | `tests/test_f036_recurso_persona_gemelos.py` (raíz) | también `res.cla` en `datos_recursos` (R27) |
| Crear/adaptar | tests por servicio (§8) | — |
| Modificar | `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/referencia/partes-proyecto.md`, `azure-apps/partes.md` | R27, R30 (§9) |

**No se tocan**: `de_alta` (sv3 y sv5), `esta_congelado`/`ESTADOS_CONGELADOS`
y `congelacion.py`, `elegir_por_dni` y `recursos_por_dni` de sv5, los SQL de
sv4 (`_SQL_EMPLEADOS`, `_SQL_RECURSOS_ACTIVOS`), `jornada_resolver.py`,
`text_match.py`, `persist_parte_pipeline.py` (R3 ya sube `review_required`
porque `ide` es None y el método no está en `METODOS_RECURSO`), los
`METODOS_RECURSO` de sv3/sv4, `worker_key_for_registro`/`persona_de`, sv1, sv2.

## 3. `IndicePersonas` (sv3, application)

```python
PREFIJO_FICHA, PREFIJO_RECURSO = "emp:", "res:"

def clave_persona(self, r: RecursoRow) -> str
    # dni_de_recurso(r) or f"emp:{r.conide}" (ficha enlazada) or f"res:{r.ide}"
def elegir_sin_dni(self, ide: int | None, empresa: int | None, fecha: int) -> ResolucionRecurso
def casar_por_clave(self, clave: str, empresa: int | None, fecha: int) -> ResolucionRecurso
```

- `elegir_sin_dni` (R9), en este orden: `r = recurso(ide)`; `None` o no
  `es_persona(r)` ⇒ `desconocido`; `dni_de_recurso(r)` ⇒ `con_dni`; no
  `de_alta(r.fecbaj, fecha)` ⇒ `solo_baja`; `empresa` no None y distinta ⇒
  `otra_empresa`; si no, `ResolucionRecurso(r.ide, "ok")`.
- `casar_por_clave`: `res:N` ⇒ `elegir_sin_dni(N, …)`; `emp:N` ⇒
  `elegir_recurso(None, N, ficha(N).reside, empresa, fecha)` (el camino por
  `conide` que ya existe; ficha ausente del maestro ⇒ `desconocido`); otro ⇒
  `casar_por_dni(clave, …)`.
- `candidatos_nombre` (R1): persona, de alta y de la empresa; se quita
  `and self.dni_de_recurso(r)`.
- `elegir_recurso` (R10): al principio, `if not dni_n and empleado_ide is None
  and preferido is not None: return self.elegir_sin_dni(preferido, empresa,
  fecha)`. El resto, intacto.

## 4. Casado (sv3, `casado_recurso.py`)

- `_casar_nombre` (R2–R4): `candidatos.append((indice.clave_persona(r),
  nombres))`. Si la ganadora empieza por `emp:` o `res:` ⇒
  `EmpleadoMatch(method="nombre_sin_dni")` (DA1); si no, como hoy.
- `_casar_alias` (R7–R8): `dni` = alias → ficha → `dni_de_recurso(
  recurso(alias["recurso_ide"]))`. Con DNI, como hoy. Sin él: `clave =
  f"res:{recurso_ide}"` si lo hay, si no `f"emp:{ide}"` si hay `ide`, si no
  `alias_no_valido`; `casar_por_clave(clave)` `ok` ⇒ `_a_match(…, 1.0,
  "alias")`; otro ⇒ `alias_no_valido`.
- `_a_match` (R12): `dni=indice.dni_de_recurso(r) or None`.
- No cambian el orden DNI → alias → nombre ni el cierre por DNI (R5).

## 5. Esquema y DDL (las dos copias de `orm_models.py`)

```python
empleado_ide: Mapped[int | None] = mapped_column(Integer, nullable=True)
...
#: F-040: recurso elegido en el portal (con o sin ficha). Sin ficha y sin
#: DNI es lo unico que identifica a la persona.
recurso_ide: Mapped[int | None] = mapped_column(Integer, nullable=True)
```

`recurso_ide` va al final de la clase. `ddl_complementario()` ya genera `ALTER TABLE empleado_alias ADD COLUMN IF NOT
EXISTS recurso_ide INTEGER`. `create_all` no relaja un `NOT NULL` existente, así
que `DDL_EXTRA_POSTGRES` gana `"ALTER TABLE empleado_alias ALTER COLUMN
empleado_ide DROP NOT NULL"`: idempotente en PostgreSQL (sobre una columna ya
nullable no hace nada) y sobre una tabla de decenas de filas. Es la vía del
repositorio (F-010/F-017: nada de `.sql` de migración); no se reescribe ninguna
fila. No se añade `CHECK` (no hay forma idempotente sin bloque `DO`): la regla
«`empleado_ide` o `recurso_ide`» la impone `upsert_empleado_alias` (R18).

## 6. sv5 y la lista cerrada

`verificar_recurso(r, empresa, fecha, dni)` (orden): no existe ⇒
`NO_EXISTE`; otra empresa; de baja; **con DNI de línea**: el de hoy
(`OTRA_PERSONA` si difiere); **sin DNI de línea** (nuevo): `r.cla !=
CLA_PERSONA` ⇒ `MOTIVO_RECURSO_NO_PERSONA`; `_dni(r.dni)` ⇒
`MOTIVO_RECURSO_CON_DNI`. Textos para el preflight:

- `MOTIVO_RECURSO_NO_PERSONA = "la linea no trae DNI y el recurso no es de persona"`
- `MOTIVO_RECURSO_CON_DNI = "la linea no trae DNI y el recurso si: reasignar el trabajador"`

Gemelos (entrada nueva en la lista cerrada de `CLAUDE.md`): sv3
`IndicePersonas.elegir_sin_dni` ⇔ sv5 `verificar_recurso` rama sin DNI. Mismo
criterio (persona, sin DNI, alta, empresa); sv3 elige y sv5 verifica. El
guardián R26 (AST/texto, sin importar, como F-036):

1. `CASOS_SIN_DNI` (lista literal de tuplas `(cla, tiene_dni, fecbaj,
   empresa_recurso, empresa, fecha, vale)`) existe **idéntica** en
   `sv3 tests/test_f040_elegir_sin_dni.py` y `sv5 tests/test_f040_verificar_sin_dni.py`
   (`ast.literal_eval`), y cada uno la recorre contra su función.
2. `elegir_sin_dni` llama a `de_alta` y `es_persona`; `verificar_recurso`
   usa `de_alta` y `CLA_PERSONA`.
3. Cada comprobación se prueba contra una copia estropeada en memoria.

`datos_recursos` lee `res.cla`: tercera aparición del criterio persona en sv5;
el guardián F-036 lo comprueba también ahí.

## 7. Medición (R28–R29, `medicion_casado.py`)

- `COLUMNAS_MAESTRO` + `sin_dni_sin_ficha` (persona, sin DNI, sin ficha
  enlazada; sale de las filas de `sin_dni`).
- `_casado`: si el nuevo casado es `nombre_sin_dni` ⇒ `propone_sin_dni` (antes
  de las demás ramas).
- `_recurso` pasa a devolver `(categoria, ide_nuevo)`; nueva `_sv5(linea,
  ide_nuevo, indice)`: `omite_sin_dni` si la línea no está congelada, su
  `empleado_dni` es vacío, `ide_nuevo` no es None y el recurso no es persona o
  tiene DNI; si no, `igual`. Columna `sv5` en la fila y en el CSV; `resumir`
  cuenta `sv5_omite_sin_dni`.
- `leer_aliases` **no cambia**: columnas explícitas; antes del despliegue
  `recurso_ide` no existe.

Se ejecuta desde la rama de F-040 **antes de desplegar** (M1 en §10).

## 8. Tests (sin red ni PostgreSQL; datos sintéticos)

| Fichero | Cubre |
|---|---|
| sv3 `tests/test_f040_seleccion.py` | `clave_persona`, `casar_por_clave`, `candidatos_nombre` (R1), `elegir_recurso` R10, R11 (conciliador con dobles) |
| sv3 `tests/test_f040_elegir_sin_dni.py` | R9 por `CASOS_SIN_DNI` |
| sv3 `tests/test_f040_casado.py` | R2–R5, R7, R8, R12 por tabla de casos |
| sv3 `tests/test_f040_alias_repo.py` | R6 (SQLite en memoria), R20 en sv3 |
| sv3 `tests/test_f040_medicion.py` | R28, R29 (sin columna `recurso_ide` leída) |
| sv3 `tests/test_f040_caracterizacion.py` | R13 (en verde antes de tocar nada) |
| sv3/sv4 tests de DDL F-010 | R21: la sentencia nueva en `DDL_EXTRA_POSTGRES` y el `ADD COLUMN` |
| sv4 `tests/test_f040_catalogo.py` | R14, R16 |
| sv4 `tests/test_f040_alias.py` | R17–R19 (SQLite en memoria + endpoints con dobles) |
| sv4 `tests/test_f040_vistas.py` | R15: `node --check`, parseo Jinja2 y la cadena «sin DNI» en los puntos de pintado |
| sv5 `tests/test_f040_verificar_sin_dni.py` | R23–R25 por `CASOS_SIN_DNI`; R22 con el SQL capturado |
| raíz `tests/test_f040_recurso_sin_dni_gemelos.py` | R26 |

Adaptaciones declaradas (se listan en `impl_F-040.md`): sv3
`test_f036_r3_nombre_de_un_recurso_sin_dni_no_casa` (ahora `nombre_sin_dni`),
`test_f036_r8_alias_sin_dni_y_ficha_sin_dni_no_valido` (ahora resuelve por
`emp:`), los de `candidatos_nombre` con DNI obligatorio, el INFO de R3; sv4
`test_f035_r3_sin_dni_ni_en_la_ficha_no_se_ofrece` (ahora se ofrece con `dni`
None) y los que esperan que no haya alias sin ficha; sv5 los dobles de
`RecursoSigrid` de líneas sin DNI (ganan `cla=1`); los recuentos de
`test_f010_r6_ddl_complementario*` si cuentan sentencias.

## 9. Documentación (R27, R30)

- `CLAUDE.md`, lista cerrada: entrada F-040 (`elegir_sin_dni` sv3 ⇔ rama sin
  DNI de `verificar_recurso` sv5, guardián `test_f040_…`; `datos_recursos` en
  el criterio persona de sv5).
- `ARCHITECTURE.md`: semántica 2 (alias también por recurso), 12 (recursos sin
  DNI: se proponen, no casan solos; alias por recurso; sv5 exige persona y sin
  DNI a una línea sin DNI; F-035 ya los ofrece marcados), 7 (`empleado_alias`
  con `recurso_ide`), Herramientas (la medición amplía columnas).
- `partes-proyecto.md` §3.3, §4.6 y §5.3; `azure-apps/partes.md` §4.3 y la
  viñeta Empleado (commit local en `azure-apps`).

## 10. Despliegue y verificación manual (humano)

Orden: **sv3 → sv5 → sv4**. sv3 primero porque añade la columna (DDL) y
conserva el recurso de una línea sin DNI (R10): con sv4 nuevo y sv3 viejo, un
casado manual sin DNI perdería su recurso en la siguiente pasada. sv5 antes de
sv4 para que ninguna línea sin DNI viaje sin la verificación acotada. Un sv4
viejo con la columna ya creada sigue funcionando (no la lee).

- **M1 · antes de desplegar** (solo lectura): `python medir_casado_recursos.py`
  desde la rama, en `services/partes-persistencia`. Se miran
  `sin_dni`/`sin_dni_sin_ficha` por empresa, `casado_pierde_casado`,
  `casado_propone_sin_dni` y `sv5_omite_sin_dni`. Si `sv5_omite_sin_dni > 0`,
  se decide antes (DA3).
- **M2 · tras sv3** (base `partes`, solo lectura): `SELECT column_name,
  is_nullable FROM information_schema.columns WHERE table_name =
  'empleado_alias' AND column_name IN ('empleado_ide','recurso_ide');` ⇒ dos
  filas, las dos `YES`.
- **M3 · tras sv4**: en Conciliar, empresa Porsan, `MO/0032` y `MO/0033`
  salen con «sin DNI»; confirmar uno deja su alias con `recurso_ide` y la línea
  `recurso_manual`; el preflight de su obra la da por verificada.

## 11. Riesgos y decisiones

- **Cambio colateral buscado**: un recurso sin DNI compite por nombre; quien
  hoy casa por nombre con una persona con DNI puede pasar a `nombre_ambiguo` o
  `nombre_sin_dni` si el sin DNI puntúa igual o más. Va a Conciliar, nada se
  elige al azar; M1 lo cuenta (`pierde_casado`).
- **sv5 más estricto** con líneas sin DNI (DA3): una línea antigua sin DNI con
  recurso con DNI (ficha sin DNI y `res.cif` lleno) pasa a omitirse con motivo.
  M1 lo cuenta (`sv5_omite_sin_dni`); se arregla reasignando.
- **Alias sin ficha ⇒ `recurso_nombre`**, como decidió F-036: sin método nuevo
  en `METODOS_RECURSO` (sv3 y sv4 no se tocan ahí).
- **Descartado**: tabla nueva `recurso_alias` (séptima tabla, guardianes
  F-010/F-015 y doble lectura del alias); `CHECK` en la tabla (§5); casar solo
  por nombre sin DNI (DA1).
- **Conflicto de merge** con F-039 (sv4 JS, etiquetas de empresa) en
  `static/app.js` junto a `recLabel`: trivial, lo integra el humano.

## 12. Decisiones abiertas (para el humano)

- **DA1. ¿Casa solo o solo propone?** Recomendado: **propone** (R3). Sin DNI
  nada confirma la identidad salvo el nombre leído (OCR o letra a mano): la
  línea va a Conciliar con el candidato ofrecido y marcado «sin DNI»;
  confirmarlo aprende el alias contra el recurso (R17) y desde entonces esa
  variante casa sola por alias (R8). Alternativa: casar por nombre como si
  tuviera DNI (`recurso_nombre`), más automático y con el riesgo de imputar
  horas a otra persona sin ninguna comprobación.
- **DA2. Alias contra el recurso.** Recomendado: **columna `recurso_ide` en
  `empleado_alias` y `empleado_ide` nullable** (§5), y alias para todo recurso
  elegido en Conciliar o al reasignar, con o sin ficha y con o sin DNI (los 8
  de 39 de Porsan sin ficha también aprenden). Alternativa: tabla nueva (§11).
- **DA3. Acotar sv5 para líneas sin DNI.** Recomendado: **recurso persona y sin
  DNI** (R23–R24), gemelo de `elegir_sin_dni`. Alternativas: solo persona
  (R23), o no tocar sv5 (hoy acepta cualquier recurso de la empresa y de alta).
- **DA4. Lo ya ingerido.** Recomendado: **no se re-casa** (R31); la cola de
  Conciliar ya ofrece los recursos sin DNI tras desplegar sv4.
