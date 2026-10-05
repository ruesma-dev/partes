<!-- specs/F-030-recurso-sin-ficha/design.md -->
# F-030 · Diseño técnico

Requisitos en `requirements.md`. Nada se implementa sin DA1–DA9 (§8) aprobadas.

## 1. Datos medidos en Sigrid (2026-10-05, solo lectura, agregados)

Por sigrid-api con el cliente de lectura de sv3, script en el scratchpad (fuera
del repo); ninguna respuesta `truncated`; sin DNIs ni nombres. «Alta» = a hoy.

| Medida | Emp. 1 | Emp. 28 |
|---|---|---|
| Recursos `MO/` de alta | 229 | 39 |
| …sin ficha por DNI (`res.cif` ≠ todo `emp.dni`) | 19 | 18 |
| …de ellos con `res.cif` vacío | 0 | 12 |
| …con `res.cif` y `conide` 0 (sin ficha alguna) | 12 | 6 |
| …con `res.cif` y `conide` → ficha de alta con DNI vacío u otro | 7 (4 vacío) | 0 |
| …con `res.cif` vacío y `conide` → ficha de alta (ya casan por la ficha) | 0 | 10 |
| …sin `cif` ni `conide` (no identificables por DNI) | 0 | 2 |
| Líneas `hmores` 2026 tecleadas a mano con esos recursos sin ficha | 707 (18 rec.) | 582 (6 rec.) |
| Recursos `MO/` de alta con alguna cuenta en `reshor` | 229 | **0** |
| Líneas `hmores` 2026 de obras de la 28 con `caaide` ≠ 0 | — | **0 de 5.123** |
| Obras con centro y cuentas `caa` en él | — | 103 de 103 |

- **Forma del DNI en Sigrid**: 0 fichas de alta (1.095) y 0 `res.cif` `MO/` con
  7 dígitos + letra; 215 + 43 fichas empiezan por `0`. Sigrid guarda siempre 8
  dígitos: el cero que falta es del **papel leído**, no de Sigrid (R1).
- Solo recursos `MO/` tienen `res.cif` con forma de DNI o NIE (255 de alta):
  casar por `cif` no puede caer en maquinaria ni subcontratas.
- Ningún recurso sin ficha comparte `cif` con otro recurso de alta de su
  empresa: `elegir_recurso` no dará `ambiguo` en la población de hoy.
- La obra 0724 existe en las empresas 1 y 28 (gemelas, F-023); la de la 28 tiene
  centro con 270 cuentas. Un solo recurso de toda la base tiene `emp.dni` y
  `res.cif` distintos solo en el cero (dato de Sigrid, no de F-030).

## 2. Servicios que toca y por qué (límite de servicio)

- **sv3** (casado de la ingesta): DNI canónico, paso nuevo «recurso por DNI»,
  nombre del recurso en la lectura de maestros y `review_required`. El
  conciliador **no** cambia: ya resuelve el recurso por `res.cif` cuando la
  línea trae `empleado_dni` (`_recursos_de` une `conide` y `cif`).
- **sv4** (portal): que un `recurso_dni` no se pinte «Sin casar» ni entre en la
  cola de conciliación, donde casarlo por nombre soltaría su recurso.
- **sv5**: **sin código**. Verifica igual que hoy (R14–R15) y ya escribe
  `caaide = 0` en la 28 (R20). Solo gana tests de caracterización.
- Ninguna responsabilidad nueva fuera de su servicio; sin schema nuevo (los
  campos `empleado_*` existen). Nada se duplica fuera de la lista cerrada.

## 3. Encaje en la arquitectura

Semántica 1, 2 y 12: sin ficha, la persona se identifica por el DNI de su
recurso, con los mismos candidatos (empresa y alta) en sv3 y sv5. El paso nuevo
vive en `application/` sobre funciones puras existentes.

## 4. Ficheros a crear (tests)

| Ruta | Requisitos |
|---|---|
| `services/partes-persistencia/tests/test_f030_dni_canonico.py` | R1, R2, R3 |
| `services/partes-persistencia/tests/test_f030_casado_recurso.py` | R4–R10 |
| `services/partes-persistencia/tests/test_f030_conciliador_sin_ficha.py` | R11, R12 |
| `services/partes-transfer/tests/test_f030_coherencia_sin_ficha.py` | R14, R15, R20 |
| `services/partes-front/tests/test_f030_portal_recurso_dni.py` | R16–R19 |

Patrón de `test_f023_pipeline_match.py` y `test_f023_recurso_conciliador.py`:
`SigridMatcherProvider` real sobre un lookup en memoria, repositorio falso,
datos **sintéticos**. R9 va en `test_f030_casado_recurso.py` con el
`SigridFalso` de `test_f023_cliente_sigrid.py` (columnas del `SELECT`).

## 5. Ficheros a modificar

**sv3** (`services/partes-persistencia/`):
- `application/services/text_match.py`: `dni_canonico()` (R1). `normalize_dni`
  **no** cambia (la usan índices, calendario y alias).
- `application/services/parte_normalizer.py`: `trabajador_dni_leido` =
  `dni_canonico(...) or None` (R2). Un único punto de entrada: obra (R11 de
  F-023), ficha y recurso ven el mismo DNI.
- `domain/models/sigrid_models.py`: `RecursoRow.nombre: str | None = None` (R9).
- `infrastructure/sigrid/sigrid_api_client.py`: `rc.res AS nombre` en
  `_SQL_RECURSOS` y su mapeo en `fetch_recursos` (misma lectura paginada, R9).
- `application/pipelines/persist_parte_pipeline.py`: constante
  `METODO_RECURSO_DNI = "recurso_dni"`; paso nuevo en `_casar_trabajador`;
  `_compute_review_required` (R10). Docstring de cabecera al día.
- `domain/models/parte_records.py`: solo el comentario de `EmpleadoMatch.method`.

**sv4** (`services/partes-front/`):
- `infrastructure/database/parte_repository.py`: `METODO_RECURSO_DNI`, helpers
  `esta_casado(reg)` y `casado_por_recurso(reg)`; campo `sin_ficha: bool =
  False` en las cuatro vistas con `matched` y sus cuatro cálculos (hoy
  `empleado_ide is not None`); filtro en `list_unmatched_workers` y en la
  confirmación por nombre leído (R16–R18).
- `templates/parte_detail.html`, `obra_detail.html`, `trabajadores_list.html`,
  `trabajador_detail.html`: badge «Casado por recurso (sin ficha)» (R17).

**Documentación** (R21): `docs/ARCHITECTURE.md` (semántica 2 y 12, ≤ 6
líneas), `docs/referencia/partes-proyecto.md` §4.6 y §7, y
`C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (viñetas Empleado y
Recurso; commit local en ese repositorio).

## 6. Clases y funciones

### 6.1 sv3 · `text_match.dni_canonico(dni: str | None) -> str` (pura)

`n = normalize_dni(dni)`; si `re.fullmatch(r"[0-9]{1,7}[A-Z]", n)`, devuelve
`n[:-1].zfill(8) + n[-1]`; si no, `n`. Ejemplos de test: con y sin cero dan lo
mismo; `X1234567L`, `B12345678`, `123456789Z` y `""` quedan igual.

### 6.2 sv3 · pipeline `_casar_trabajador` (application)

Orden nuevo (lo que no se nombra queda igual que hoy):

1. `elegir_ficha(dni, empresa, fecha)`: `ok` ⇒ `dni`; `ambiguo`/`solo_baja`/
   `otra_empresa` ⇒ `dni_<motivo>` y fin (R7).
2. **Nuevo**, solo si fue `desconocido` y hay DNI: `_casar_por_recurso(reg,
   indice, empresa, fecha) -> EmpleadoMatch | None`, que llama
   `indice.elegir_recurso(dni, None, None, empresa, fecha)`. Con `ok` devuelve
   `EmpleadoMatch(ide=None, codigo=None, nombre=r.nombre, dni=r.cif,
   reside=None, score=1.0, method=METODO_RECURSO_DNI)` y loguea INFO (registro
   y recurso, sin DNI ni nombre). Con otro motivo devuelve None (log INFO salvo
   `desconocido`) y sigue el paso 3 (R6).
3. Alias aprendido y nombre por similitud, como hoy.

`empleado_reside` queda NULL a propósito: la ficha no existe y el conciliador
re-elige por línea (fecha y empresa de la obra) con el mismo `elegir_recurso`.
`_compute_review_required`: «trabajador sin casar» pasa a ser `empleado.ide is
None and empleado.method != METODO_RECURSO_DNI`.

### 6.3 sv3 · sin cambios que conviene conocer

`IndicePersonas` (índices y `elegir_recurso`), `RecursoConciliador`,
`fetch_registros_para_recurso` y `SqlAlchemyParteRepository.save_parte`: una
línea `recurso_dni` ya llega al conciliador con `empleado_dni` = `res.cif` y
`empleado_ide` NULL, y `_fichas_de` + `_recursos_de` la resuelven por `cif`
(R11). El calendario (`_dni_grupo`) y `empleado_jornada` se buscan por ese DNI
(R12); si Sesame no conoce el DNI, calendario por defecto **no degradado**.
`_deactivate_same_day_obra` ya usa `empleado_dni` y el nombre como señales.

### 6.4 sv4 · `parte_repository.py`

`METODO_RECURSO_DNI = "recurso_dni"` (contrato con sv3 por la columna);
`casado_por_recurso(reg) -> bool` (`empleado_ide` NULL y ese método) y
`esta_casado(reg) -> bool` (`empleado_ide` o lo anterior). Las cuatro vistas
rellenan `matched=esta_casado(r)` y `sin_ficha=casado_por_recurso(r)`. Filtro SQL de la cola: `empleado_ide IS NULL AND
(empleado_match_method IS NULL OR empleado_match_method <> 'recurso_dni')`.
`worker_key_for_registro` y `persona_de` **no** cambian: un `recurso_dni` se
agrupa por su nombre leído (`nom-…`) y cruza días por DNI (F-025).

## 7. Ficheros que NO se tocan y fuera de alcance

- **Lista cerrada** (DA6): `seleccion_sigrid.py` (`de_alta`, `IndicePersonas`,
  `_desempatar`), `coherencia_recurso.py`, el SQL de empleados de sv4,
  `jornada_resolver.py` de sv3 y sv4, `orm_models.py` de sv3 y sv4. Ni sv5
  `registro_pipeline.py`, `reglas_registro.py`, `cuenta_analitica.py` ni
  `sigrid_write_client.py`.
- `recurso_conciliador.py`, `empleado_matcher.py`, `obra_matcher.py`, ni de
  sv4 `static/app.js`, el catálogo ni los modales de alta; ni sv1 ni sv2.
- Fuera: casar por nombre contra recursos (DA1); tomar la ficha de
  `res.conide` (DA2); columna nueva para el DNI leído y re-casado automático
  de lo ya ingerido (DA8); excepciones de jornada o alta manual de personas sin
  ficha en sv4; regla «empresa sin analítica» en sv5 (DA9); los 2 recursos de
  la 28 sin `cif` ni `conide` (solo los casaría el nombre).

## 8. Decisiones abiertas (el humano aprueba o rebate)

- **DA1 · (a) ¿también por nombre contra el recurso?** Alternativas: (i) solo
  DNI; (ii) sin DNI leído, nombre (`con.res`, «APELLIDOS, NOMBRE») contra los
  recursos `MO/` sin ficha de la empresa del parte. **Recomiendo (i)**: los
  partes J.310 rev. 1+ traen DNI y el caso real lo traía; un nombre mal casado
  escribe horas a otra persona en Sigrid. (ii) puede ser feature aparte.
- **DA2 · (b) qué se guarda.** `empleado_ide` NULL, `empleado_dni` = `res.cif`,
  `empleado_nombre` = `con.res` del recurso, método `recurso_dni` (R5).
  Descartadas: rellenar `empleado_ide` con `res.conide` (en 3 de los 7 de la
  empresa 1 la ficha tiene otro DNI) y una columna nueva (schema en sv3 y sv4
  para nada que no quepa en las de hoy). Riesgo: `empleado_*` pasa a significar
  «la persona identificada», con o sin ficha.
- **DA3 · `review_required`.** **Recomiendo no subirlo** por `recurso_dni`
  (R10): el DNI casa exacto con el recurso y, si luego el recurso no vale a la
  fecha, el conciliador ya sube la revisión (F-023 R29). Subirlo mandaría a
  revisión todo parte de Porsan con estas personas (6 de 39 en la 28).
- **DA4 · (b) portal.** **Recomiendo** R16–R18. Sin tocar sv4, la línea seguiría
  «Sin casar» y en `/conciliacion`, donde casarla por nombre a una ficha
  equivocada soltaría el recurso bueno (F-023 R42).
- **DA5 · DNI con recurso de baja, de otra empresa o ambiguo.** (i) seguir como
  hoy a alias y nombre (R6); (ii) cerrar sin casar como F-023 R22.
  **Recomiendo (i)**: no cambia nada de lo que hoy casa; (ii) puede perder
  casados por nombre de personas con ficha y DNI distinto.
- **DA6 · (c) lista cerrada.** **Recomiendo no tocar ninguna copia**: el paso
  nuevo **usa** `elegir_recurso` tal cual y el cero se arregla en la entrada
  (normalizador), no en los índices. Así sv3 y sv5 siguen con los mismos
  candidatos y el guardián no cambia. Descartado: clave sin ceros dentro de
  `IndicePersonas`, que obligaría a cambiar `_dni` y el SQL de sv5.
- **DA7 · DNI canónico.** Completar a 8 dígitos solo `^[0-9]{1,7}[A-Z]$`
  (R1). También arregla el casado **con ficha** de un DNI leído sin cero
  (R3), que hoy cae al nombre. Riesgo: ninguno medido (Sigrid no tiene DNIs
  de 7 dígitos).
- **DA8 · (d) partes ya ingeridos.** El DNI leído **no se guarda** en
  `parte_registros` y F-023 R31 no re-casa empleados: lo ingerido con `none`
  no se arregla solo. **Recomiendo** reprocesar a mano los 2 partes de Porsan
  (M3). Descartado aquí: endpoint de re-casado desde `raw_extraction_json`
  (casar líneas por `line_index` con un normalizador que cambia) o columna
  nueva del DNI leído: feature aparte si hay volumen.
- **DA9 · (e) cuenta analítica en Porsan.** Hoy sv5 ya escribe `caaide = 0`
  en la 28: ningún recurso de la 28 tiene cuenta en `reshor` y Administración
  no pone cuenta en ninguna de las 5.123 líneas de 2026, aunque las 103 obras
  sí tienen cuentas. **Recomiendo no cambiar código** y fijarlo con un test
  (R20). Riesgo: si alguien rellena `reshor.caaide` en la 28, sv5 empezará a
  poner cuenta; si se quiere garantizar el 0, una lista `EMPRESAS_SIN_ANALITICA`
  en sv5 es feature aparte.

## 9. Despliegue y verificaciones manuales (humano)

**Orden**: sv3 y después sv4, en la misma sesión (`redeploy_partes.ps1 -Solo
sv3`, luego `-Solo sv4`); sv5 no se despliega. Sin schema nuevo. Hasta
desplegar sv4, un `recurso_dni` se ve «Sin casar»: no tocarlo en
`/conciliacion`. Rollback: volver a la imagen anterior de sv3 (las líneas ya
casadas por recurso conservan su recurso y sv5 las verifica igual).

- **M1 · tras sv3.** Logs de arranque: `maestros cargados … recursos=` sin error.
- **M2 · lectura en Sigrid antes de aprobar.** Desde
  `services/partes-persistencia` (`PYTHONPATH=. ../../.venv/Scripts/python.exe
  <script>` con `SigridApiClient(...)._post_sql_read(sql=..., parameters=[...],
  label=...)`, comprobando `truncated`): `SELECT COUNT(*) FROM reshor rh JOIN
  con rc ON rc.ide = rh.reside WHERE rc.emp = 28 AND ISNULL(rh.caaide, 0) <> 0`
  ⇒ `0`.
- **M3 · reprocesar los 2 partes de Porsan (obra 0724, 25 y 28/09).** (1) En el
  portal, si están aprobados, «Marcar pendiente»; (2) «Mover a la papelera»
  cada parte (si no, la deduplicación por sha256 lo ignora); (3) en el buzón
  `partes@ruesma.es`, mover sus dos correos de `Procesados` a la bandeja de
  entrada y marcarlos no leídos; (4) esperar a sv1 → sv2 → sv3. Comprobar en el
  portal: el trabajador sin ficha sale «Casado por recurso (sin ficha)» con el
  nombre del recurso, sus líneas con recurso y estado `ok`/`sin_parte` (no «Sin
  recurso»), y el trabajador con ficha igual que antes.
- **M4 · cuenta analítica, sin escribir.** Abrir el modal de aprobación de
  esas líneas (preflight, solo lectura) y buscar en los logs de
  `ca-sv5-transfer` `[registro] cuentas obra=0724 ok=0 recurso_sin_cuenta=N`
  con N = líneas a escribir, y ninguna omitida por recurso. Aprobar de verdad
  es decisión de Administración; si se aprueba, comprobar por lectura que esas
  líneas `hmores` (synckey `partes:<registro_id>`) tienen `caaide = 0`.

## 10. Riesgos

- **DNI mal leído que coincide con el `cif` de otra persona sin ficha**: se
  imputaría a otra persona; mismo riesgo que con fichas desde F-023, mitigado
  porque el portal enseña el nombre del recurso junto al leído («Leído: …»).
- Los 3 recursos de la empresa 1 con `conide` a una ficha de otro DNI se
  casarán en sv3 pero sv5 los **omitirá** con motivo (R15): falla seguro;
  se arregla en Sigrid.
- Más líneas con recurso ⇒ más extras por jornada (sin recurso no entraban).
- La matriz agrupa a la persona por nombre leído: dos lecturas distintas del
  mismo nombre salen como dos filas (igual que hoy sin casar).
