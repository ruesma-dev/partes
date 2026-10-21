<!-- specs/F-054-sin-obra-o-fecha-a-revision/design.md -->
# F-054 · Un parte sin obra o sin fecha leídas va siempre a revisión — Diseño

## 1. Estado actual (`dev` 206354d, leído para esta spec)

### 1.1 Métodos de casado de obra (`obra_match_method`)

`ObraMatcher.match` (`services/partes-persistencia/application/services/obra_matcher.py`) y
`elegir_obra` / `elegir_por_nombre` (`application/services/seleccion_sigrid.py`) dan:

| Con obra (`ide` relleno) | Sin obra (`ide` `None`) |
|---|---|
| `codigo`, `codigo_padded`, `codigo_membrete`, `codigo_trabajadores`, `codigo_nombre`, `nombre` | `none` (ni código ni nombre que casen; también el defecto de `ObraMatch()` si Sigrid no está cableado), `codigo_otra_empresa`, `codigo_ambiguo`, `nombre_ambiguo` (F-023) |

Fuera de sv3, el portal escribe `manual` al cambiar la obra (`update_parte_obra` de sv4,
normalmente con `ide`). Ningún método «sin obra» devuelve `ide`, así que `obra.ide is None`
es exactamente «sin obra» y cubre los métodos que vengan (DA1).

### 1.2 Fecha

`FechaParteResolver.resolve` (`application/services/fecha_resolver.py`) devuelve
`fecha_int = None` (método `none`) si no lee día y mes (`null`, `15/10` sin año, texto) o si
la fecha no existe (`32/13/2026`). Con fecha, el método (`leido`, `leido_pasado`,
`futuro_corregido`, `inferido`, `+email_mes`) no llega a `ParteDocumento`: solo se loguea.
`futuro_corregido` ya sale como ERROR «REVISAR» en el log (DA2 B).

### 1.3 Qué hace hoy el portal (sv4) con un parte sin obra o sin fecha

- `review_required` solo pinta: «Revisar» en la columna Estado de `/partes`
  (`templates/partes_list.html` l. 88, filtrable con el filtro de columna) y «Requiere
  revision» en el detalle (`parte_detail.html` l. 82). **No bloquea** aprobar
  (`approve_document` no lo mira) ni registra motivo alguno.
- **Sin obra**: el listado enseña el número leído o «—»; las líneas se agrupan en
  `/obras` con la clave `sin-obra` (`obra_key_for_registro`, sin `obra_ide`, `obra_codigo`
  ni nombre). El detalle permite ponerla (combo de obra → `PATCH /api/partes/{id}/obra`,
  `obra_match_method = 'manual'`) y enseña «Leido: X (sin casar)».
- **Sin fecha**: el listado enseña la fecha vacía; en `/obras/{clave}` las líneas sin fecha
  no entran en ninguna columna de la matriz (si ninguna línea tiene fecha, la vista son
  «registros sueltos»). El detalle permite ponerla (`PATCH /api/partes/{id}/fecha`, F-043,
  con recálculo de F-042).
- Cambiar obra o fecha **no** toca `review_required` (ni sube ni baja).

### 1.4 Qué haría sv5 si se aprobara

- **Sin obra**: `RegistroPipeline._obra_destino` lanza `RuntimeError("obra no encontrada en
  Sigrid…")` y la petición de esa obra acaba en `error` sin escribir. En modo pruebas
  (`OBRA_PRUEBAS_FORZAR`) todo va a la 0404, como siempre.
- **Sin fecha**: sv4 manda `fecha_int = int(r.fecha_int or 0)` (`parte_repository.py`
  l. 1873) y sv5 lo acepta (`LineaIn.fecha_int: int`); no se ha encontrado ninguna guarda
  contra `fecha_int = 0` en sv4 ni en sv5 (periodo 0/00). Es un hueco aparte: DA5.

### 1.5 Lo que ya no se pisa y lo que no cambia

`_deactivate_same_day_obra` no desactiva nada sin fecha o sin obra (l. 879–885). El casado
usa «hoy» como fecha de referencia sin fecha (F-023 R16). `marcar_review_required` (F-003,
F-023) solo sube la bandera. Nada de esto cambia.

## 2. Ficheros

### A crear

- `services/partes-persistencia/tests/test_f054_revision_cabecera.py` — R1–R7 y R9 (§6).

### A modificar

- `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py`:
  - constantes `MOTIVO_SIN_OBRA = "sin_obra"` y `MOTIVO_SIN_FECHA = "sin_fecha"` y función
    pura `motivos_cabecera` (§3), a nivel de módulo como `empresa_del_parte`;
  - `_compute_review_required`: la condición de `OBRA_A_REVISAR` se sustituye por
    `if motivos_cabecera(parte): return True` (R1–R3, R6), en el mismo sitio;
  - se borra `OBRA_A_REVISAR` (R6; solo lo usa esa línea, comprobado con `grep`);
  - `run`: tras `save_parte`, el WARNING de R7 si `motivos_cabecera(parte)` no está vacía;
  - docstring de cabecera, paso 5: «sin obra casada o sin fecha ⇒ revisión (F-054)» (R13).
- `services/partes-persistencia/tests/test_f023_pipeline_match.py` — enmienda de
  `test_f023_review_required_por_la_obra` (§6.2).
- `services/partes-persistencia/tests/test_f030_casado_recurso.py` — `_parte_revisable` gana
  obra casada (neutral, §6.2).
- `services/partes-persistencia/tests/test_f051_lectura_dudosa.py` — `_parte_casado` gana
  fecha (neutral, §6.2).
- `docs/ARCHITECTURE.md` — semántica 18 (R13, texto en §7).

### Que NO se tocan

- `domain/models/parte_records.py` (ni `fecha_metodo`: DA2 A), `fecha_resolver.py`,
  `obra_matcher.py`, `seleccion_sigrid.py`, `parte_normalizer.py`, `lectura_dudosa.py`.
- `infrastructure/database/orm_models.py` de sv3 y sv4 (sin esquema; el guardián de F-010 no
  se entera) ni `sqlalchemy_parte_repository.py` (`save_parte` ya guarda lo que le llega).
- `recurso_conciliador.py` y `partida_conciliador.py`: no recalculan `review_required`.
- Todo sv4 (`parte_repository.py`, plantillas, `app.js`) y todo sv5 (DA4, DA5).
- `azure-apps/partes.md`: no cambia nada de lo que el proyecto expone o consume.

## 3. Funciones (capa application de sv3)

```python
#: F-054 (R3): motivos de cabecera que mandan el parte a revision.
MOTIVO_SIN_OBRA = "sin_obra"
MOTIVO_SIN_FECHA = "sin_fecha"

def motivos_cabecera(parte: ParteDocumento) -> tuple[str, ...]:
    """R1-R3: `sin_obra` si no hay obra casada (`obra.ide` None, sea cual sea el
    metodo) y `sin_fecha` si `fecha_int` es None o <= 0, en ese orden."""
```

- La condición de fecha se escribe `parte.fecha_int is None or parte.fecha_int <= 0` (no
  `not parte.fecha_int`): así `0` y `-1` matan los mutantes de la comparación (§6).
- `_compute_review_required` sigue siendo `@staticmethod` con la misma firma (la llaman
  `test_f023`, `test_f030` y `test_f051`). Orden: sin registros, sin firma, **cabecera**,
  lectura dudosa, registros. El orden no cambia el booleano.
- WARNING de R7 (en `run`, tras `save_parte`, con el `document_id` ya asignado):
  `"[persist-parte] cabecera incompleta, el parte va a revision: document_id=%s motivos=%s
  obra_match_method=%s obra_leida=%r"`, con los motivos unidos por coma. Ni
  `trabajador_nombre_leido`, ni DNI, ni nombre de obra.

## 4. Límite de servicio y gemelos

- **sv3** es quien calcula `review_required` al ingerir: el cambio vive donde ya vive la
  regla. sv4 solo lo lee y sv5 no lo conoce. No hace falta otro servicio.
- `_compute_review_required` no tiene gemelo en la lista cerrada de `CLAUDE.md` ni copia en
  sv4. No se toca ningún gemelo (`orm_models.py`, `de_alta`, congelación, `res.cla = 1`).

## 5. Riesgos y decisiones

- **Más partes en «Revisar»**: los que hoy entran sin obra o sin fecha. M1 los cuenta.
  Sin Sigrid cableado (local) ya iban todos a revisión por los trabajadores sin casar.
- **La bandera no bloquea** (§1.3): F-054 da la señal, no la guarda. La guarda real contra
  `fecha_int = 0` es DA5.
- **Tests existentes**: con la regla aplicada a modo de sonda (y revertida) sobre `dev`,
  fallan exactamente 4 de 2.254 tests de sv3 (3 casos de `test_f030_r13_…_por_el_trabajador`
  y `test_f051_r17_…_como_hoy`), todos por partes de prueba sin obra o sin fecha. Quitar
  `OBRA_A_REVISAR` (R6) hace fallar además los 3 casos «sin casar» de `test_f023`, que
  ponen el método con la obra casada. Las enmiendas de §6.2 los dejan con partes realistas.
- **Solo ingestas nuevas** (R11), como F-051: lo guardado se arregla con M2 (DA3).
- Descartado guardar motivos en columna (DA4 C): esquema gemelo, migración y portal para
  algo que hoy se ve en la propia cabecera.

## 6. Tests (sin red ni BBDD; SQLite en memoria donde ya se usa)

### 6.1 `tests/test_f054_revision_cabecera.py`

Parte base «casado»: firmado, `fecha_int = 20261020`, `ObraMatch(ide=1, codigo="0100",
method="codigo")`, un registro normal de 8 h con `EmpleadoMatch(ide=1, method="dni")` y
`TipoHoraMatch(ide=1)`. Nombres y DNIs ficticios.

| Test | Caso | Esperado |
|---|---|---|
| `test_f054_r1_sin_obra_va_a_revision[…]` | `ObraMatch(method=m)` para `none`, `codigo_otra_empresa`, `codigo_ambiguo`, `nombre_ambiguo`, `metodo_nuevo` | `True` |
| `test_f054_r1_por_el_casado_real` | `_casar(_parte(("ANA UNO", DNI_A), obra=None))` de `test_f023` | `method == "none"`, `True` |
| `test_f054_r2_sin_fecha_va_a_revision[…]` | `fecha_int` `None`, `0`, `-1` | `True` |
| `test_f054_r2_sin_fecha_por_el_casado_real` | `_casar(_parte(("ANA UNO", DNI_A), obra="300", fecha=None))` | obra casada, `True` |
| `test_f054_r3_motivos_cabecera` | los 4 cruces obra/fecha | `()`, `("sin_obra",)`, `("sin_fecha",)`, `("sin_obra", "sin_fecha")` |
| `test_f054_r4_casado_completo_no_va_a_revision[…]` | los 6 métodos con obra | `False` |
| `test_f054_r4_casado_por_recurso_no_cambia` | `EmpleadoMatch(ide=None, reside=950, method="recurso_dni")` | `False` |
| `test_f054_r5_las_demas_causas_no_cambian` | sin firma, sin registros, lectura dudosa, trabajador `none`, hora sin `ide` | `True` cada una |
| `test_f054_r6_obra_a_revisar_desaparece` | `hasattr(modulo, "OBRA_A_REVISAR")` | `False` |
| `test_f054_r7_warning_con_motivos_sin_nombres` | `run` del hallazgo (§6.3), `caplog` | un WARNING con `document_id`, `sin_obra,sin_fecha`, `obra_match_method=none`; sin nombres ni DNIs del payload |
| `test_f054_r7_sin_motivos_no_hay_warning` | `run` con cabecera completa | ningún registro con «cabecera incompleta» |
| `test_f054_r9_ingesta_del_hallazgo` | `run` del hallazgo con `_match` que casa todos los trabajadores (patrón `_ingerir` de `test_f051`) | `review_required is True`, `parte.fecha_int is None`, `parte.obra.ide is None` |
| `test_f054_r9_columnas_guardadas` | `_montar()` y `_request(None, (…), fecha=None)` de `test_f036_pipeline` (SQLite) | `doc.review_required`, `obra_ide`/`fecha_int` NULL, `obra_match_method == "none"` |

R8 se comprueba con `git diff dev --stat -- services/partes-front services/partes-transfer`
vacío. R10 lo siguen cubriendo, sin cambios, los tests de F-023 R16 y del reemplazo.

### 6.2 Enmiendas de tests existentes

- `test_f023_review_required_por_la_obra` (fase RED de F-054): pasa a `(metodo, con_obra,
  esperado)`; los «sin casar» ponen `parte.obra = ObraMatch(method=metodo)` (sin `ide`, como
  lo deja `ObraMatcher`) ⇒ `True`; `codigo` deja la obra casada ⇒ `False`; y `("none",
  False)` pasa a `("none", sin obra, True)`: es el cambio de comportamiento de la feature.
- `_parte_revisable` (`test_f030`): `parte.obra = ObraMatch(ide=1, codigo="0724",
  method="codigo")`. `_parte_casado` (`test_f051`): `fecha_int=20261017`. Neutras: verdes
  antes y después; ningún `assert` cambia y su docstring ya dice «obra y trabajador casados».

### 6.3 Payload del hallazgo (ficticio)

`{"cabecera": {"fecha": null, "obra_numero": null, "obra_nombre": null,
"empresa_membrete": null}, "firma": {"firmado": true}, "empleados": [4 filas con
"numero_linea" 1–4, "horas_ordinarias": 8 y nombres ficticios]}`.

## 7. `docs/ARCHITECTURE.md` · semántica 18 (texto propuesto)

> 18. **Parte sin obra o sin fecha (F-054, sv3)**: sv3 manda a revisión
> (`review_required`) todo parte sin obra casada (`obra.ide` nulo: `none` y los sin casar
> de F-023) o sin fecha (`fecha_int` nulo), con un WARNING `sin_obra` / `sin_fecha` sin
> nombres. La bandera no bloquea la aprobación ni la baja nadie al poner obra o fecha en el
> portal. Solo ingestas nuevas; lo guardado antes se corrigió una vez a mano (M2).

## 8. Verificaciones manuales (humano o líder)

Desde una consola con la regla de firewall de `psql-albaranes-rs9k2`; `<servidor>` y
`<usuario>` son los del Key Vault (nunca en el repositorio). Solo la base `partes`.

- **M1 · solo lectura (antes de aprobar DA3)**:
  ```powershell
  $env:PGOPTIONS = '-c default_transaction_read_only=on'
  psql -X -v ON_ERROR_STOP=1 -c "SELECT (obra_ide IS NULL) AS sin_obra, (fecha_int IS NULL OR fecha_int <= 0) AS sin_fecha, approved, COALESCE(review_required, false) AS revisar, obra_match_method, COUNT(*) AS partes, MIN(created_at_utc) AS desde, MAX(created_at_utc) AS hasta FROM parte_documents WHERE is_active AND (obra_ide IS NULL OR fecha_int IS NULL OR fecha_int <= 0) GROUP BY 1,2,3,4,5 ORDER BY 1,2,3,4,5" -c "SELECT (r.obra_ide IS NULL) AS sin_obra, (r.fecha_int IS NULL OR r.fecha_int <= 0) AS sin_fecha, COALESCE(r.sigrid_estado, '') AS sigrid_estado, COUNT(*) AS lineas FROM parte_registros r JOIN parte_documents d ON d.id = r.document_id WHERE d.is_active AND r.deleted_at_utc IS NULL AND (r.obra_ide IS NULL OR r.fecha_int IS NULL OR r.fecha_int <= 0) GROUP BY 1,2,3 ORDER BY 1,2,3" "host=<servidor> dbname=partes user=<usuario> sslmode=require"
  Remove-Item Env:PGOPTIONS
  ```
  Esperado: (a) al menos una fila `t | t | f | f | none` con los 2 documentos del
  2026-10-21 (si no se han arreglado ya); el total de filas `approved = f` y `revisar = f`
  es lo que corregiría M2. (b) Ninguna línea sin fecha en `registrado`, `encolado`,
  `dedicacion` o `conflicto`; si aparece alguna, DA5 pasa a urgente y se avisa al humano.
- **M2 · escritura en la base `partes` (solo si DA3 = B y con autorización expresa del
  humano para esta acción; tras desplegar sv3)**:
  ```powershell
  psql -X -v ON_ERROR_STOP=1 -c "UPDATE parte_documents SET review_required = true WHERE is_active AND NOT approved AND review_required IS NOT TRUE AND (obra_ide IS NULL OR fecha_int IS NULL OR fecha_int <= 0)" "host=<servidor> dbname=partes user=<usuario> sslmode=require"
  ```
  Esperado: `UPDATE n`, con `n` = la suma de M1(a) con `approved = f` y `revisar = f` (si
  entre medias llegó otro, ya lo marcó sv3). Repetirlo da `UPDATE 0`. Solo sube.
- **M3 · tras `redeploy_partes.ps1 -Solo sv3` y unos días de ingesta**: M1(a) añadiendo
  `AND created_at_utc >= '<AAAA-MM-DDTHH:MM>'` (hora UTC del despliegue) antes del
  `GROUP BY`. Esperado: ninguna fila con `revisar = f`; y en el log de sv3, un WARNING
  «cabecera incompleta» por cada parte que salga.

## 9. Decisiones abiertas (las aprueba el humano)

| DA | Pregunta | Alternativas | Recomendación |
|---|---|---|---|
| DA1 | Qué es «sin obra» | **A**: `obra.ide is None`, y `OBRA_A_REVISAR` desaparece. B: añadir `none` a `OBRA_A_REVISAR`. C: A sin quitar la lista (dos controles, uno ya no decide) | **A**: cubre métodos futuros y `manual` sin ide; B olvida el siguiente; C deja un mutante superviviente |
| DA2 | Qué es «sin fecha» | **A**: `fecha_int` nulo o ≤ 0. B: A + año futuro corregido (`futuro_corregido`; campo nuevo `fecha_metodo` en `ParteDocumento`). C: A + fecha lejana (más de N días antes de la recepción) | **A**: es el hueco medido; B y C son criterios nuevos sin datos (el año futuro ya sale como ERROR en el log), feature aparte si M1 lo pide |
| DA3 | Lo ya guardado | A: no tocarlo (como F-051), M1 informativa. **B**: M2, un `UPDATE` único manual que solo sube la bandera en activos no aprobados. C: recálculo en código (`conciliar_todos` o arranque) | **B**: barato, idempotente y acotado a la base `partes`; C mete lógica permanente para una corrección de una vez |
| DA4 | Motivo visible | **A**: WARNING en sv3 con `sin_obra`/`sin_fecha`; portal igual (la cabecera ya lo enseña). B: sv4 rotula el motivo deducido de las columnas. C: columna `review_motivos` con todas las causas | **A**: sin esquema ni sv4; B solo explicaría 2 de 7 causas; C es otra feature |
| DA5 | Guarda aguas abajo (§1.4) | **A**: fuera de F-054; abrir feature «sv5 omite las líneas sin fecha válida» (y sin obra). B: sv4 no envía líneas sin obra o sin fecha (`excluidas`). C: sv5 las omite con motivo | **A** aquí, y la feature nueva con **C** (el que escribe se protege; rigor crítico y despliegue de sv5); urgente si M1(b) da líneas sin fecha enviadas |
| DA6 | Sitio en la cola | **A**: prioridad **2**, delante de F-014 (3, bloqueada) y F-049 (4), sin renumerar. B: 3 y desplazar las demás. C: detrás de F-052 | **A**: pequeña (solo sv3, ~15 líneas) y hueco de seguridad; 2 ya la usan solo features `done` |
| DA7 | Rigor | **A**: `estandar`. B: `critico` | **A**: no escribe en Sigrid ni toca nada compartido; solo sube una bandera |
