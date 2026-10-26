# F-061 · Informe del implementer

Rama `feature/F-061-parte-vacio-tras-borrar-lineas`, worktree `partes-wt-f061`. Solo sv4
(`services/partes-front`). Rigor `estandar`. Spec: `specs/F-061-parte-vacio-tras-borrar-lineas/`.
T1–T13 hechas, un commit por tarea (`git log --oneline dev..`). La mutación (T12) la lanzó
el líder y el implementer analizó sus supervivientes; T14 y T15 son MANUAL (M1 y M2, comandos en `progress/current.md`).

## Qué cambió

| Fichero (`services/partes-front/`) | Cambio |
|---|---|
| `application/services/parte_vacio.py` (nuevo) | Marca `sin-lineas`, `marca_retirado`, `es_retirado`, `DuplicadoActivoError` y su motivo, `PARTES_SIGRID_PROTEGIDOS`, `motivo_exclusion_limpieza`, `categoria_vacio` y `empleados_leidos`. Todo puro |
| `infrastructure/database/parte_repository.py` | `_sql_bloqueo_documentos` (`FOR UPDATE … ORDER BY id`, `populate_existing`), `_bloquear_documentos`, `_retirar_si_vacios` (el único que escribe la regla), `borrar_linea` (con `soft_delete_registro` delegando), `soft_delete_worker` (bloquea, relee, retira), `_deshacer_creadas` (bloquea y retira), `restore_registro` (R6/R7), `restore_document` (R7/R8), `_borrar_retirados_sin_filas` (el único borrado físico nuevo) en `vaciar_papelera` y `hard_delete_registro`, `list_partes` con solo las vivas y `ParteRow.sin_lineas`, `partes_vacios_activos` y `limpiar_vacios` |
| `interface_adapters/web/app.py` | `api_registro_delete` devuelve el dict de `borrar_linea`; los dos restaurar dan 409 `{"ok": false, "error"}` con `DuplicadoActivoError` |
| `static/app.js` | `destinoTrasBorrar` (pura) y `_irTrasBorrar`: aviso de R12 y `/partes` si se está en el detalle del parte retirado, en `.line-del` y en `doBorrar` (que pasa a `_postJSON` para leer cada JSON); los dos restaurar enseñan `d.error` |
| `templates/partes_list.html` | Insignia `badge warn` «Sin líneas» |
| `limpiar_partes_vacios.py` (nuevo) | Informe READ ONLY (MD + CSV en `logs/`) y `--ejecutar --esperados N` |
| `tests/test_f061_{borrado,papelera,portal,limpieza}.py` (nuevos) | 91 tests |
| `tests/test_f017_endpoints_firmados.py` | Espía `borrar_linea` y compara `["ok"]` (desviación justificada en `progress/current.md`) |

Fuera de sv4: `docs/ARCHITECTURE.md` (semántica 8 y «Herramientas de consola») y
`azure-apps/partes.md` (filas `source_sha256` y papelera, commit local `86640b4` en
`azure-apps`, solo `partes.md`). No cambian sv1, sv2, sv3, sv5, `orm_models.py` ni
`congelacion.py` (`git diff --stat dev`).

## Decisiones de diseño y desviaciones

- **`partes_borrados` solo si es > 0**, como `EXCLUIDA_REPARTO`: el dict de `vaciar_papelera`
  no cambia sin retirados que borrar, y los tests de F-010 R11 y F-019 R16 que lo comparan
  exacto siguen verdes sin tocarlos.
- **F-017**: su test comparaba `{"ok": True}` exacto y espiaba `soft_delete_registro`, que la
  ruta ya no llama. Se adapta (3 líneas); lo que vigila (el actor en `deleted_by`) no cambia.
- **Bloqueos añadidos a los de la spec**: los dos restaurar y `_deshacer_creadas` también
  bloquean el parte antes de tocar líneas (R3: ningún camino cambia líneas sin él).
- `borrar_linea` relee la línea tras el bloqueo (`session.refresh`): si otro la borró mientras
  esperaba, devuelve `{"ok": False}`. `soft_delete_worker` relee las candidatas y solo toca las
  de partes que bloqueó.
- `categoria_vacio`: con filas manda `todas_en_papelera`; sin filas, `manual` va antes que
  `leídos` (igual que la consulta M0 de `design.md` §9 del commit `02da480`).
- `limpiar_vacios` devuelve listas de ids (no nombres) para que el script imprima los saltados.
- El script no se ha ejecutado contra ninguna base: solo en tests (SQLite) y `--help` /
  `--ejecutar` sin `--esperados` (error de uso antes de conectar).

## Fuera de alcance y pendiente

- Lo de `requirements.md` «Fuera de alcance» (reprocesar, F-042, el parte que nace vacío).
- **T12**: el humano tiene que aceptar el equivalente #1 de la mutación (ver «Evidencias»).
- **T14 (M1)** tras desplegar sv4 y **T15 (M2)** con autorización literal del humano.

## Fase RED

### T1 · `tests/test_f061_borrado.py` y `tests/test_f061_papelera.py` (R1–R11)

Comando (desde `services/partes-front`):
`python -m pytest tests/test_f061_borrado.py tests/test_f061_papelera.py -q`

```
=================================== ERRORS ====================================
_________________ ERROR collecting tests/test_f061_borrado.py _________________
E   ModuleNotFoundError: No module named 'application.services.parte_vacio'
________________ ERROR collecting tests/test_f061_papelera.py _________________
E   ModuleNotFoundError: No module named 'application.services.parte_vacio'
ERROR tests/test_f061_borrado.py
ERROR tests/test_f061_papelera.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!
1 warning, 2 errors in 2.87s
```

Con `parte_vacio.py` ya creado (T2), el mismo comando sigue en ROJO por lo que falta en el
repositorio y el portal (`--tb=line`, causas; 26 failed, 10 passed):

```
tests\test_f061_borrado.py:72: AttributeError: 'ParteReviewRepository' object has no attribute 'borrar_linea'
tests\test_f061_borrado.py:113: assert False            (soft_delete_registro no retira el parte)
tests\test_f061_borrado.py:124: AssertionError: assert {'ok': True} == {'ok': True, ...': 'doc-f004'}
tests\test_f061_borrado.py:150: assert False            (soft_delete_worker lo manda a la papelera de partes)
tests\test_f061_borrado.py:173: AssertionError: assert False   (_deshacer_creadas no retira)
tests\test_f061_borrado.py:201: AttributeError: type object 'ParteReviewRepository' has no attribute '_sql_bloqueo_documentos'
tests\test_f061_borrado.py:212: AttributeError: type object 'ParteReviewRepository' has no attribute '_bloquear_documentos'
tests\test_f061_papelera.py:76: AttributeError: 'ParteReviewRepository' object has no attribute 'borrar_linea'
tests\test_f061_papelera.py:157: Failed: DID NOT RAISE DuplicadoActivoError
tests\test_f061_papelera.py:167: Failed: DID NOT RAISE DuplicadoActivoError
tests\test_f061_papelera.py:204: assert False            (restore_document no devuelve las líneas)
```

### T2 · funciones puras (`tests/test_f061_limpieza.py`, parte pura)

Su ROJO es el de T1 (`ModuleNotFoundError: No module named 'application.services.parte_vacio'`).
Tras crear el módulo: `python -m pytest tests/test_f061_limpieza.py -q` ⇒ `35 passed in 0.27s`.

### T7 · `tests/test_f061_portal.py` (R12, R13 y el aviso de R7)

Comando: `python -m pytest tests/test_f061_portal.py -q --tb=line` (10 failed, 2 passed):

```
tests\test_f061_portal.py:48: AssertionError: app.js no define destinoTrasBorrar   (x4)
tests\test_f061_portal.py:102: assert (<re.Match ...'_bindClick(".line-del", ...> and '_irTrasBorrar([d])' in ...
tests\test_f061_portal.py:116: AssertionError: [data-restore-doc]
tests\test_f061_portal.py:148: assert (2, 3) == (1, 2)      (list_partes contaba las de la papelera)
tests\test_f061_portal.py:160: AttributeError: 'ParteRow' object has no attribute 'sin_lineas'
tests\test_f061_portal.py:171: AttributeError: 'ParteRow' object has no attribute 'sin_lineas'
tests\test_f061_portal.py:184: assert 0 == 1                (la plantilla no pinta «Sin líneas»)
```

Tras el cambio: `12 passed`; `node --check static/app.js` sin errores; `partes_list.html` parsea
en Jinja2 (test `test_f061_r13_partes_list_parsea_en_jinja2`).

### T8 · R14–R18 (`tests/test_f061_limpieza.py`, script y repositorio)

Comando: `python -m pytest tests/test_f061_limpieza.py -q --tb=line`. Primero, sin el script:

```
E   ModuleNotFoundError: No module named 'limpiar_partes_vacios'
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.96s
```

Con el script y sin los métodos del repositorio (5 failed, 38 passed):

```
limpiar_partes_vacios.py:92: AttributeError: 'ParteReviewRepository' object has no attribute 'partes_vacios_activos'   (x4)
tests	est_f061_limpieza.py:286: AttributeError: 'ParteReviewRepository' object has no attribute 'limpiar_vacios'
```

Tras `partes_vacios_activos` y `limpiar_vacios`: `43 passed`. `python limpiar_partes_vacios.py
--ejecutar` (sin `--esperados`) ⇒ `error: --ejecutar exige --esperados N`, código 2, sin tocar la base.

## Resultado de `bash harness/init.sh` (T13)

Primera pasada en ROJO: `test_f043_r19_r40_ninguna_recarga_nueva_salvo_actualizar` cuenta las
`location.reload` de `app.js` (esperaba 23 y había 22, porque T7 juntaba las dos recargas de
los borrados en `_irTrasBorrar`). Por la parada en el primer fallo, la cobertura salió en 46,7 %.
Arreglo en `057afc3`: la recarga vuelve a cada llamada y `_irTrasBorrar` solo avisa y navega.
No se tocó el test de F-043. La segunda pasada termina en `ENTORNO LISTO. Puedes trabajar.`

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de F-061 | 93 (`test_f061_borrado` 18, `_papelera` 18, `_portal` 12, `_limpieza` 45), todos en verde |
| Suite sv4 (`init.sh`, tras el análisis de la mutación) | `2884 passed, 1 skipped, 2 warnings in 1058.21s (0:17:38)` |
| Suite raíz (`init.sh`) | `522 passed, 3 skipped in 110.45s (0:01:50)` |
| sv1, sv2, sv3 y sv5 | en verde (caché de `init.sh`: árbol sin cambios) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 96.9% de 289 líneas cambiadas cubiertas (280/289, umbral 80%, nivel estandar)` |
| Mutación (lanzada por el líder, sin relanzar) | 110 generados y 20 evaluados (muestreo `estandar`, semilla `20260820`): 16 muertos, 4 supervivientes y 0 timeouts, en 4373 s con **4 workers**. Detalle en `progress/mutacion_F-061.md` |
| Tiempo de la suite | sv4 1058,21 s; raíz 110,45 s |
| Verificaciones MANUAL | M1 (T14) y M2 (T15), con sus comandos exactos en `progress/current.md` |

### Supervivientes de la mutación

| # | Línea | Mutante | Clasificación | Cómo se cierra |
|---|---|---|---|---|
| 1 | `parte_repository.py:4258` (`_borrar_retirados_sin_filas`) | `.limit(1)` → `.limit(2)` | **Equivalente propuesto, pendiente de aceptación del humano** | `.first()` es None si y solo si no hay filas, con LIMIT 1 o 2. `python progress/equivalentes_F-061.py` ⇒ `#1 equivalente en 6125 casos; el control .limit(0) difiere.` (salida 0) |
| 2 | `limpiar_partes_vacios.py:78` | `create_engine(future=False)` | **Hueco** | `test_f061_r18_fabrica_de_sesiones_del_script_funciona`; a mano: `1 failed, 44 passed` (`ArgumentError` de SQLAlchemy 2) |
| 3 | `limpiar_partes_vacios.py:83` | `sessionmaker(future=False)` | **Hueco** | El mismo test; a mano: `1 failed, 44 passed` (`ArgumentError` en `Session()`) |
| 4 | `limpiar_partes_vacios.py:127` | `if not f["motivo_exclusion"]` → `if f[...]` | **Hueco**: la tabla de categorías del informe contaría los excluidos | `test_f061_r14_markdown_cuenta_categorias_y_acciones_de_candidatos` (las tres tablas); a mano: `1 failed, 44 passed` |

El #4 no cambia qué cuenta ni qué borra el script: el nº de candidatos, el `--esperados` y
`limpiar_vacios` salen de `candidatos()`, que ya estaba cubierta. Lo que cambiaba es la tabla
del informe que el humano lee antes de autorizar la M2. Ahora la tabla queda vigilada.

## Arreglo de la observación 1 de la review (el humano dijo «si» el 2026-10-26)

El problema: un parte retirado que alguien aprueba después (una pestaña abierta) se borraba
físicamente al vaciar la papelera o al eliminar su última fila.

**RED.** Comando: `python -m pytest tests/test_f061_papelera.py -q --tb=line -k obs1` ⇒
`2 failed`:
```
tests	est_f061_papelera.py:310: AssertionError: assert 2 == 0      (vaciar borraba los 2 retirados aprobados)
tests	est_f061_papelera.py:322: assert None is not None           (eliminar su última fila borraba el parte)
```

**Cambio** (commit `229c30c`): `_borrar_retirados_sin_filas` filtra además
`ParteDocumentOrm.approved.is_(False)`. No se tocan `approve_document` ni `_set_approval`, ni las
observaciones 2–4. **Verde:** los dos `test_f061_obs1_*` pasan, junto a F-061, F-004, F-010 y
F-019 (`222 passed`). La demostración del equivalente #1 (aceptado por el humano) sigue igual:
`python progress/equivalentes_F-061.py` ⇒ `#1 equivalente en 6125 casos; el control .limit(0)
difiere.` (salida 0; su `.limit(1)` sigue siendo único en el ámbito).

**`bash harness/init.sh`:**
- Suites: raíz `522 passed, 3 skipped in 225.97s`; sv4 `2886 passed, 1 skipped in 1166.32s`.
- `PUERTA COBERTURA: 96.9% de 289 líneas cambiadas cubiertas (280/289)`.
- **KO** en `PUERTA TAMAÑO`: `progress/review_F-061.md: 141 líneas > tope 140`. Ese fichero es
  del reviewer y del líder; ya tenía 141 líneas en `2a3cf8c`, antes de este arreglo, y el
  implementer no lo toca.
