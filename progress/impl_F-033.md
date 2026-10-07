<!-- progress/impl_F-033.md -->
# F-033 · Portal: columna Empresa en el listado de obras — Informe del implementer

Rama `feature/F-033-columna-empresa`, rigor `estandar`, spec mínima
aprobada por el humano el 2026-10-07. **Solo sv4** (`services/partes-front/`).
Sin schema, sin Sigrid, sin JS, sin despliegue, sin push. Datos de los
tests sintéticos (obra «0678 · Obra Gemela Sintetica», recursos 9xx).

## 1. Qué cambió (commits locales)

| Commit | Tarea | Qué |
|---|---|---|
| `381c872` | — | F-033 `in_progress` en `features.json` (+ `BACKLOG.md`, `current.md`) |
| `825a163` | T1 | `application/services/empresas.py` (nuevo, puro); `ObraRow.empresas` / `ObraRow.empresa_texto`; cálculo y orden en `list_obras`; tests R2, R4–R7 |
| `ea0ba9e` | T2 | `templates/obras_list.html`: `<th>Empresa</th>`, filtro «Filtrar empresa…» y celda `{{ o.empresa_texto }}`; tests R1, R3, R8 y parseo Jinja2 |
| `e9f2f58` | — | Cero avisos de ruff en el test nuevo (`Optional[X]` → `X \| None`) |
| (T3) | T3 | Este informe y `progress/mutacion_F-033.md` |

Ficheros tocados (todos bajo `services/partes-front/`):

- `application/services/empresas.py` (nuevo, 52 líneas):
  `NOMBRES_EMPRESA = {1: "Ruesma", 28: "Porsan"}`, `nombre_empresa`
  (o «Empresa N»), `texto_empresas` (`[]` → «—»; si no, « / ».join),
  `empresas_de_fila` (empresas no nulas de los partes; si no hay, unión de
  las empresas de sus recursos no nulos; siempre ordenada).
- `infrastructure/database/parte_repository.py` (+31/−6, solo
  `ObraRow` y `list_obras`): mapa `empresa_por_recurso` sobre las mismas
  líneas ya cargadas (sin consulta nueva); por grupo, `empresas_doc` y
  `recursos`; `ObraRow(..., empresas=, empresa_texto=)`; tercera clave de
  orden `r.empresas[0] if r.empresas else 10**9`.
- `templates/obras_list.html` (+3): columna, filtro y celda tras «Obra».
- `tests/test_f033_columna_empresa.py` (nuevo, 11 tests).

**No se ha tocado**: `app.py`, `settings.py`, `orm_models.py`, `get_obra`,
`list_partes`, `get_parte`, otras plantillas, `static/` (el filtro genérico
`wireColumnFilters` trabaja por `cellIndex`, así que la columna nueva queda
filtrable sin JS), sv3, sv5, `obra_catalog.py`, `azure-apps/`. Ningún test
existente modificado. La lista cerrada de duplicación no crece.

## 2. Decisiones y desviaciones

**Ninguna desviación de la spec.** Detalles dentro de ella:

1. Los dos campos nuevos de `ObraRow` van al final con defecto
   (`field(default_factory=list)` y `"—"`), como dice el design §3: ningún
   constructor existente de `ObraRow` se rompe.
2. El texto «—» vive en una constante `SIN_EMPRESA` del módulo puro (mismo
   carácter que el defecto del dataclass).
3. R2 con mezcla: si una fila tiene partes con empresa y otros NULL, valen
   solo los no nulos y **no** se activa el respaldo por recurso (glosario:
   «los valores no nulos»; design §3 «si `empresas_partes` sin `None` no
   está vacío»). Lo fija `test_f033_r2_varias_empresas_unidas`.
4. El respaldo de R4 se calcula con todas las líneas activas que ya carga
   `list_obras`, también de otras obras; es la definición del glosario
   («cualquier obra»).
5. R8 «búsqueda intacta»: `search="Porsan"` sigue sin devolver nada (busca
   por código o nombre, no por empresa); está fijado en el test. El filtro
   de columna del navegador sí filtra por empresa.

## 3. Tests (R → test)

| R | Test | Nivel |
|---|---|---|
| R1 | `test_f033_r1_columna_y_filtro_alineados` | HTML (TestClient) |
| R2 | `test_f033_r2_varias_empresas_unidas`, `test_f033_r2_texto_empresas_puro` | repo + puro |
| R3 | `test_f033_r3_gemelas_dos_filas_ruesma_porsan` | HTML |
| R4 | `test_f033_r4_partes_null_usa_empresa_del_recurso`, `test_f033_r4_empresas_de_fila_puro` | repo + puro |
| R5 | `test_f033_r5_sin_empresa_guion` | repo + puro |
| R6 | `test_f033_r6_numero_desconocido_empresa_n` | repo + puro |
| R7 | `test_f033_r7_orden_gemelas` | repo |
| R8 | `test_f033_r8_obra_key_y_totales_intactos` (+ suite sv4 entera en verde) | repo + HTML |
| — | `test_f033_plantilla_obras_list_parsea` (parseo Jinja2) | plantilla |

Patrón: `FabricaSesionSqlite` + `ParteReviewRepository` real; HTML con
`build_app(Settings(_env_file=None), repository=...)` y `TestClient`
(fixture `entorno_portal` con `PG_PASSWORD`/`PG_ADMIN_PASSWORD` de relleno,
como `test_f025_vistas.py`). Sin red ni PostgreSQL.

## 4. Fase RED (trazas reales)

### T1 (R2, R4, R5, R6, R7) — antes de crear `empresas.py` y tocar `list_obras`

Comando: `cd services/partes-front && python -m pytest tests/test_f033_columna_empresa.py -q -rf --tb=line`

```
tests\test_f033_columna_empresa.py:89: AttributeError: 'ObraRow' object has no attribute 'empresas'
tests\test_f033_columna_empresa.py:94: ModuleNotFoundError: No module named 'application.services.empresas'
tests\test_f033_columna_empresa.py:116: AttributeError: 'ObraRow' object has no attribute 'empresas'
tests\test_f033_columna_empresa.py:121: ModuleNotFoundError: No module named 'application.services.empresas'
tests\test_f033_columna_empresa.py:133: ModuleNotFoundError: No module named 'application.services.empresas'
tests\test_f033_columna_empresa.py:148: ModuleNotFoundError: No module named 'application.services.empresas'
E   AssertionError: assert ['obr-600', '...1', 'obr-502'] == ['obr-600', '...1', 'obr-503']
      At index 1 diff: 'obr-503' != 'obr-502'
tests\test_f033_columna_empresa.py:176: AssertionError: assert ['obr-600', '...1', 'obr-502'] == ['obr-600', '...1', 'obr-503']
=========================== short test summary info ===========================
FAILED tests/test_f033_columna_empresa.py::test_f033_r2_varias_empresas_unidas
FAILED tests/test_f033_columna_empresa.py::test_f033_r2_texto_empresas_puro
FAILED tests/test_f033_columna_empresa.py::test_f033_r4_partes_null_usa_empresa_del_recurso
FAILED tests/test_f033_columna_empresa.py::test_f033_r4_empresas_de_fila_puro
FAILED tests/test_f033_columna_empresa.py::test_f033_r5_sin_empresa_guion - M...
FAILED tests/test_f033_columna_empresa.py::test_f033_r6_numero_desconocido_empresa_n
FAILED tests/test_f033_columna_empresa.py::test_f033_r7_orden_gemelas - Asser...
7 failed in 0.97s
```

R7 falla por su aserción de orden (no por import): sin la tercera clave,
las gemelas salían en orden de inserción (503 sin empresa delante de 502).
Tras el código: `7 passed in 0.99s`.

### T2 (R1, R3) — con T1 hecho, antes de tocar la plantilla

Comando: `cd services/partes-front && python -m pytest tests/test_f033_columna_empresa.py -q -rf --tb=line -p no:warnings`

```
E   AssertionError: assert ['Obra', 'Trabajadores'] == ['Obra', 'Empresa']
      At index 1 diff: 'Trabajadores' != 'Empresa'
tests\test_f033_columna_empresa.py:262: AssertionError: assert ['Obra', 'Trabajadores'] == ['Obra', 'Empresa']
E   AssertionError: assert ['1', '2'] == ['Ruesma', 'Porsan']
      At index 0 diff: '1' != 'Ruesma'
tests\test_f033_columna_empresa.py:279: AssertionError: assert ['1', '2'] == ['Ruesma', 'Porsan']
=========================== short test summary info ===========================
FAILED tests/test_f033_columna_empresa.py::test_f033_r1_columna_y_filtro_alineados
FAILED tests/test_f033_columna_empresa.py::test_f033_r3_gemelas_dos_filas_ruesma_porsan
2 failed, 9 passed in 2.96s
```

(R8 y el parseo Jinja2 pasan ya en RED a propósito: R8 es «no cambiar» y
fija el comportamiento previo.) Tras la plantilla: `11 passed in 2.49s`.

## 5. Verificación

- `python -m pytest tests/test_f033_columna_empresa.py -q` (sv4):
  **11 passed**.
- Suite sv4 completa (`python -m pytest tests -q`): **1683 passed** en
  131 s (antes de F-033 eran 1672 + 11 nuevos; ningún test ajeno tocado ni
  rojo).
- `bash harness/init.sh` (resultado real, 2026-10-07, tras el commit
  `ea0ba9e`): raíz `445 passed, 1 skipped in 46.90s`; sv4 `1683 passed`
  en 200 s; sv1/sv2/sv3/sv5 en verde (caché); **PUERTA COBERTURA 100.0 %
  de 32 líneas cambiadas (32/32, umbral 80 %)**; PUERTA TAMAÑO dentro de
  topes; **ENTORNO LISTO**. Ruff marcó 5 avisos nuevos (`UP045` en el test),
  corregidos en `e9f2f58`; la pasada final de T4 está en §7.
- `python -m harness.tamano --feature F-033`: dentro de los topes.
- JS: sin cambios en `static/app.js` (no aplica `node --check`).

## 6. Mutación (muestreada, nivel estandar)

`python -m harness.mutacion --feature F-033 --workers 6 --timeout 600`
(detalle en `progress/mutacion_F-033.md`): 83 líneas en alcance (2
ficheros), **12 mutantes, 10 muertos, 2 supervivientes**, 0 timeouts,
0 sin veredicto, 1295.7 s.

Supervivientes, ambos en `parte_repository.py:1028`
(`r.empresas[0] if r.empresas else 10**9`): `10**9 → 11**9` y
`10**9 → 10**10`. **Equivalentes**: el centinela solo tiene que ser mayor
que cualquier número de empresa (hoy 1 y 28) para mandar detrás las
gemelas sin empresa; cualquier valor mayor da el mismo orden. Las
mutaciones con efecto real de esa línea (`[0]→[1]`, `or "~"→and "~"`) y
las de la regla (`is not None`, `if not numeros`, el dict de nombres, el
`and` del mapa por recurso) están **muertas**. Sin test nuevo (no se
relanza la campaña).

## 7. Cierre y pendientes

- T4: `bash harness/init.sh` final tras el commit de este informe: ver la
  última línea de §8 (Evidencias).
- **Verificación MANUAL pendiente (humano, tras desplegar sv4)**: abrir
  `/obras` en el portal, comprobar que la 0678 sale en dos filas con
  «Ruesma» y «Porsan», que el filtro «Filtrar empresa…» filtra y que las
  filas de partes antiguos sin empresa muestran la empresa del recurso o
  «—». No se ha probado contra la BBDD `partes` real (solo SQLite).
- Fuera de alcance (por decisión del humano): detalle de obra, listado y
  detalle de parte, `data-label` del borrado, catálogo de obras de Sigrid,
  `docs/ARCHITECTURE.md`, `azure-apps/` (no cambia lo que sv4 expone ni
  consume).
- Una empresa nueva sale «Empresa N» hasta añadirla a `NOMBRES_EMPRESA`.

## 8. Evidencias

| Evidencia | Valor real |
|---|---|
| Tests F-033 | 11 ejecutados, 11 passed (2.4 s) |
| Suite sv4 | 1683 passed, 0 failed (131 s en suelto; 200 s dentro de `init.sh`) |
| Suite raíz | 445 passed, 1 skipped (46.9 s) |
| Cobertura de líneas cambiadas | **100.0 %** (32/32), `PUERTA COBERTURA` de `init.sh` |
| Mutantes | 12 generados/evaluados, 10 muertos, **2 supervivientes (equivalentes, analizados)** |
| Tiempo de la campaña | 1295.7 s (6 workers, línea base ~303 s por worktree) |
| `bash harness/init.sh` final (T4) | ENTORNO LISTO (ver commit `F-033 T4`) |
