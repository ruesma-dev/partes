<!-- specs/F-030-recurso-sin-ficha/design.md -->
# F-030 · Diseño técnico

Requisitos en `requirements.md`. DA1–DA9 **aprobadas** por el humano el
2026-10-05 (§8); esta versión las incorpora sin reabrirlas.

## 1. Datos medidos en Sigrid (2026-10-05, solo lectura, agregados)

Por sigrid-api con el cliente de lectura de sv3, script en el scratchpad (fuera
del repo); ninguna respuesta `truncated`; sin DNIs ni nombres. «Alta» = a hoy.

| Medida | Emp. 1 | Emp. 28 |
|---|---|---|
| Recursos `MO/` de alta | 229 | 39 |
| …sin ficha por DNI (`res.cif` ≠ todo `emp.dni`) | 19 | 18 |
| …con `res.cif` y `conide` 0: **fichas de recurso** de F-030 | 12 | 6 |
| …con `res.cif` y `conide` → ficha de alta con DNI vacío u otro | 7 (4 vacío) | 0 |
| …con `res.cif` vacío y `conide` → ficha de alta (ya casan por la ficha) | 0 | 10 |
| …sin `cif` ni `conide` (fuera de F-030) | 0 | 2 |
| Líneas `hmores` 2026 tecleadas a mano con recursos sin ficha por DNI | 707 (18 rec.) | 582 (6 rec.) |
| Recursos `MO/` de alta con alguna cuenta en `reshor` | 229 | **0** |
| Líneas `hmores` 2026 de obras de la 28 con `caaide` ≠ 0 | — | **0 de 5.123** |
| Obras con centro y cuentas `caa` en él | — | 103 de 103 |

- **DNI**: 0 fichas de alta (1.095) y 0 `res.cif` `MO/` con 7 dígitos + letra;
  215 + 43 fichas empiezan por `0`. Sigrid guarda siempre 8 dígitos: el cero
  que falta es del **papel leído** (R1).
- **Nombre**: 0 de 1.095 fichas de alta llevan coma; los recursos `MO/` de alta
  sí («APELLIDOS, NOMBRE»): 229 de 229 en la 1 y 32 de 39 en la 28 (2 de las 6
  fichas de recurso de la 28). `name_similarity` compara tokens sin orden y
  `normalize` quita la coma: «Pedro Gomez Ruiz» contra «GOMEZ RUIZ, PEDRO» da
  1,0 (sintético). Ninguno de los 246 recursos con ficha tiene el mismo texto
  de nombre que su ficha: por eso solo compiten recursos **sin** ficha (R9).
- Solo recursos `MO/` tienen `res.cif` con forma de DNI o NIE (255 de alta).
  Ningún recurso sin ficha comparte `cif` con otro de alta de su empresa.
- La obra 0724 existe en las empresas 1 y 28 (gemelas, F-023); la de la 28 tiene
  centro con 270 cuentas.

## 2. Servicios que toca y por qué (límite de servicio)

- **sv3** (casado de la ingesta): DNI canónico, fichas de recurso, el mismo
  proceso de casado de empleados sobre ellas y `review_required`. El
  conciliador **no** cambia: ya resuelve el recurso por `res.cif` cuando la
  línea trae `empleado_dni` (`_recursos_de` une `conide` y `cif`).
- **sv4** (portal), al mínimo: que un casado por recurso cuente como casado y
  no entre en la cola de conciliación, cuya confirmación por nombre le
  pondría una ficha ajena y soltaría su recurso (F-023 R42).
- **sv5**: **sin código**. Verifica igual que hoy (R17) y ya escribe
  `caaide = 0` en la 28 (R21). Solo gana tests de caracterización.
- Sin schema nuevo ni columnas nuevas (DA2). Nada se duplica: el casado
  **reutiliza** `IndicePersonas.elegir_ficha`, `fichas_candidatas` y
  `EmpleadoMatcher.match_nombre`/`to_match` sobre las fichas de recurso.

## 3. Encaje en la arquitectura

Semántica 1, 2 y 12: el empleado es la persona; si no tiene ficha, su «ficha»
es su recurso, y los candidatos (empresa y alta) son los mismos en sv3 y sv5.
La construcción de fichas de recurso es una función pura de `application/`.

## 4. Ficheros a crear

| Ruta | Contenido |
|---|---|
| `services/partes-persistencia/application/services/fichas_de_recurso.py` | §6.2 |
| `services/partes-persistencia/tests/test_f030_dni_canonico.py` | R1–R3 |
| `services/partes-persistencia/tests/test_f030_casado_recurso.py` | R4–R13 |
| `services/partes-persistencia/tests/test_f030_conciliador_sin_ficha.py` | R14, R15 |
| `services/partes-transfer/tests/test_f030_coherencia_sin_ficha.py` | R17, R21 |
| `services/partes-front/tests/test_f030_portal_recurso.py` | R18–R20 |

Patrón de `test_f023_pipeline_match.py` y `test_f023_recurso_conciliador.py`:
`SigridMatcherProvider` real sobre un lookup en memoria, repositorio falso,
datos **sintéticos**. Casos obligatorios: DNI sin cero; ficha de recurso por
DNI y por nombre en formato invertido; empate de nombre entre dos fichas de
recurso y entre una de recurso y una de empleado (R10); recurso con `conide` a
ficha o sin `cif` (no es ficha de recurso); recurso de baja u otra empresa.

## 5. Ficheros a modificar

**sv3** (`services/partes-persistencia/`):
- `application/services/parte_normalizer.py`: función pura `dni_canonico()`
  (R1) y `trabajador_dni_leido = dni_canonico(...) or None` (R2): un único
  punto para obra, ficha y recurso. Va aquí y **no** en `text_match.py`, cuya
  cabecera lo declara idéntico al de sv4 (hoy solo difieren en fin de línea).
- `domain/models/sigrid_models.py`: `RecursoRow.codigo` y `RecursoRow.nombre`
  (`str | None = None`) (R4).
- `infrastructure/sigrid/sigrid_api_client.py`: `rc.cod AS codigo` y
  `rc.res AS nombre` en `_SQL_RECURSOS` y su mapeo en `fetch_recursos`.
- `application/services/sigrid_matcher_provider.py`: `Matchers.recursos:
  IndicePersonas` = `IndicePersonas(fichas_de_recurso(empleados, recursos), [])`
  construido en `_montar` (vacío en `_empty`).
- `application/pipelines/persist_parte_pipeline.py`: `_casar_trabajador` (§6.3),
  `_compute_review_required` (R13) y docstring de cabecera.
- `domain/models/parte_records.py`: solo el comentario de `EmpleadoMatch.method`.

**sv4** (`services/partes-front/`): solo
`infrastructure/database/parte_repository.py` (§6.4). Sin plantillas, sin
`app.js`, sin campos nuevos en las vistas.

**Documentación** (R22): `docs/ARCHITECTURE.md` (semántica 2 y 12, ≤ 6
líneas), `docs/referencia/partes-proyecto.md` §4.6 y §7, y
`C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (viñetas Empleado y
Recurso; commit local en ese repositorio).

## 6. Clases y funciones

### 6.1 sv3 · `parte_normalizer.dni_canonico(dni: str | None) -> str` (pura)

`n = text_match.normalize_dni(dni)`; si `re.fullmatch(r"[0-9]{1,7}[A-Z]",
n)`, devuelve `n[:-1].zfill(8) + n[-1]`; si no, `n`. Con y sin cero dan lo mismo;
`X1234567L`, `B12345678`, `123456789Z` y `""` quedan igual.

### 6.2 sv3 · `fichas_de_recurso.py` (application, pura)

`PREFIJO_MANO_DE_OBRA = "MO/"`.
`fichas_de_recurso(empleados: Iterable[EmpleadoRow], recursos:
Iterable[RecursoRow]) -> list[EmpleadoRow]`: por cada recurso con `codigo` que
empieza por `MO/`, `normalize_dni(cif)` no vacío, sin ficha con ese DNI
normalizado y con `conide` None o que no es `ide` de ninguna ficha, devuelve
`EmpleadoRow(ide=r.ide, codigo=r.codigo, nombre=r.nombre, dni=r.cif,
reside=r.ide, empresa=r.empresa, fecbaj=r.fecbaj)`. De todas las empresas y
estados: `elegir_ficha` filtra alta y empresa y da los mismos motivos que con
fichas de empleado. `emp.ide` y `res.ide` son `con.ide`, únicos en Sigrid: una
ficha de recurso nunca choca con una de empleado.

### 6.3 sv3 · pipeline `_casar_trabajador` (application)

1. `indice.elegir_ficha(dni, empresa, fecha)`: `ok` ⇒ `dni`; `ambiguo`/
   `solo_baja`/`otra_empresa` ⇒ `dni_<motivo>` y fin (R7). Igual que hoy.
2. **Nuevo**, si fue `desconocido` y hay DNI: `matchers.recursos.elegir_ficha(
   dni, empresa, fecha)`; `ok` ⇒ `_de_recurso(ficha, 1.0, "recurso_dni")`; otro
   motivo ⇒ INFO (salvo `desconocido`) y sigue (R6).
3. Alias: igual que hoy, solo con fichas de empleado (R8).
4. Nombre: `match_nombre(nombre, candidatas=indice.fichas_candidatas(empresa,
   fecha) + matchers.recursos.fichas_candidatas(empresa, fecha))`. Si el `ide`
   elegido es de `matchers.recursos.ficha(...)`, se convierte con
   `_de_recurso(..., "recurso_nombre")`; `nombre_ambiguo` y `none` como hoy.

`_de_recurso(ficha, score, metodo)` = `dataclasses.replace(
EmpleadoMatcher.to_match(ficha, score, metodo), ide=None, codigo=None)` (R12).
`_compute_review_required`: «sin casar» pasa a ser `empleado.ide is None and
empleado.method not in METODOS_RECURSO` (`{"recurso_dni", "recurso_nombre"}`).

### 6.4 sv4 · `parte_repository.py` (DA4 al mínimo)

`METODOS_RECURSO = frozenset({"recurso_dni", "recurso_nombre"})` y
`esta_casado(reg) -> bool` (`empleado_ide` o método en `METODOS_RECURSO`); los
cuatro `matched=` de hoy (`empleado_ide is not None`) pasan a
`esta_casado(r)`. Filtro de la cola y de su confirmación: `empleado_ide IS NULL
AND (empleado_match_method IS NULL OR empleado_match_method NOT IN (...))`.
`worker_key_for_registro` y `persona_de` no cambian.

**Qué se deja y por qué (una línea):** el filtro de la cola, porque su
«confirmar» pisa la persona y suelta el recurso aunque el casado sea por
nombre, y `esta_casado`, porque sin él la persona saldría «Sin casar».

## 7. Ficheros que NO se tocan y fuera de alcance

- **Lista cerrada**: `seleccion_sigrid.py` entero, `coherencia_recurso.py`, el
  SQL de empleados de sv4, `jornada_resolver.py` y `orm_models.py` de sv3 y sv4.
  Tampoco `text_match.py` (idéntico en sv3 y sv4), `recurso_conciliador.py`,
  `empleado_matcher.py`, `obra_matcher.py`, ni de sv5 `registro_pipeline.py`, `reglas_registro.py`, `cuenta_analitica.py`
  y `sigrid_write_client.py`; ni sv1, sv2, plantillas ni `app.js` de sv4.
- Fuera: recursos sin `res.cif` (el conciliador elige por `cif`; los 2 de la
  28 necesitarían cambiarlo) o con `conide` a una ficha (casan por su ficha);
  alias de recurso (`empleado_alias` guarda fichas: sería schema); guardar el
  DNI leído y re-casado automático de lo ingerido (DA8); alta manual o
  jornada de personas sin ficha en sv4; «empresa sin analítica» en sv5 (DA9).

## 8. Decisiones del humano (APROBADAS el 2026-10-05)

- **DA1 · APROBADA, cambiada.** Humano: «da1, si no tiene dni, por nombre igual
  que hacemos con la ficha de empleados. ese dato está. el proceso es el mismo
  que con empleado pero contra la ficha de recurso cuando no está la de
  empleado». Queda: DNI (R5) y nombre (R9–R11) con el mismo código, umbral y
  ambigüedad; en el nombre compiten juntas las fichas de empleado y de recurso
  (una persona, una ficha), para que el mejor gane y un empate vaya a revisión.
- **DA2 · APROBADA.** Humano: «los partes se guardan siempre en el recurso, no
  debería cambiar nada». Sin columnas ni cambios de registro. Se mantienen los
  valores `recurso_dni`/`recurso_nombre` en `empleado_match_method` porque son
  imprescindibles: con `empleado_ide` NULL, sin ellos la línea no se distingue
  de una sin casar (revisión, portal y cola).
- **DA3 · APROBADA:** `review_required` no sube por un casado por recurso.
- **DA4 · APROBADA, reducida.** Humano: «todo lo demás debe ser como ahora»;
  líder: se ven como cualquier trabajador casado. Queda solo §6.4.
- **DA5 · APROBADA:** DNI con ficha de recurso de baja, de otra empresa o
  ambigua ⇒ sigue a alias y nombre.
- **DA6 · APROBADA:** ninguna copia de la lista cerrada se toca.
- **DA7 · APROBADA:** DNI canónico de 8 dígitos (R1), también para fichas.
- **DA8 · APROBADA:** los 2 partes de Porsan se reprocesan a mano (M3).
- **DA9 · APROBADA:** sin código en sv5; el 0 de la 28 se fija con test (R21).

## 9. Despliegue y verificaciones manuales (humano)

**Orden**: sv3 y después sv4, en la misma sesión (`redeploy_partes.ps1 -Solo
sv3`, luego `-Solo sv4`); sv5 no se despliega. Sin schema nuevo. Hasta
desplegar sv4, un casado por recurso se ve «Sin casar»: no tocarlo en
`/conciliacion`. Rollback: imagen anterior de sv3 (lo ya casado conserva su
recurso y sv5 lo verifica igual).

- **M1 · tras sv3.** Logs de arranque: `maestros cargados … recursos=` sin error.
- **M2 · lectura en Sigrid antes de aprobar.** Desde
  `services/partes-persistencia` (`PYTHONPATH=. ../../.venv/Scripts/python.exe
  <script>` con `SigridApiClient(...)._post_sql_read(sql=..., parameters=[],
  label=...)`, comprobando `truncated`): `SELECT COUNT(*) FROM reshor rh JOIN
  con rc ON rc.ide = rh.reside WHERE rc.emp = 28 AND ISNULL(rh.caaide, 0) <> 0`
  ⇒ `0`.
- **M3 · reprocesar los 2 partes de Porsan (obra 0724, 25 y 28/09).** (1) En el
  portal, si están aprobados, «Marcar pendiente»; (2) «Mover a la papelera»
  cada parte (si no, la deduplicación por sha256 lo ignora); (3) en el buzón
  `partes@ruesma.es`, mover sus correos de `Procesados` a la bandeja de entrada
  y marcarlos no leídos; (4) esperar a sv1 → sv2 → sv3. Comprobar: el
  trabajador sin ficha sale casado con el nombre de su recurso y sus líneas con
  recurso y estado `ok`/`sin_parte` (no «Sin recurso»); el de ficha, igual.
- **M4 · cuenta analítica, sin escribir.** Abrir el modal de aprobación de
  esas líneas (preflight, solo lectura) y buscar en los logs de
  `ca-sv5-transfer` `[registro] cuentas obra=0724 ok=0 recurso_sin_cuenta=N`
  con N = líneas a escribir, y ninguna omitida por recurso. Aprobar de verdad
  es decisión de Administración; si se aprueba, comprobar por lectura que esas
  líneas `hmores` (synckey `partes:<registro_id>`) tienen `caaide = 0`.

## 10. Riesgos

- **Nombre mal casado** contra una ficha de recurso: horas a otra persona en
  Sigrid. Mismo riesgo y umbral que con fichas (con 0,60, dos personas que
  comparten apellidos pueden dar justo el umbral); se mitiga con el empate a
  revisión (R10), el umbral estricto y el «Leído: …» del portal.
- Que una ficha de recurso compita en el nombre puede cambiar un casado por
  nombre de hoy: si el recurso puntúa más gana él, y si empata va a revisión.
- **DNI mal leído** que coincide con el `cif` de otra persona sin ficha: mismo
  riesgo que con fichas desde F-023.
- Más líneas con recurso ⇒ más extras por jornada (sin recurso no entraban).
