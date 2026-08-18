<!-- progress/impl_F-010.md -->
# F-010 · Saneamiento: resincronizar `orm_models.py` entre sv3 y sv4 — informe del implementer

Rama `feature/F-010-resincronizar-orm-models` (desde `dev` 716a4f7) · rigor
**estandar** · spec aprobada por el humano (D1–D5) · 7 commits, uno por
tarea, más un commit local en `azure-apps`.

## 1. Qué cambió, en una frase

Las dos copias de `orm_models.py` vuelven a ser **el mismo fichero** (y hay
un guardián que lo comprueba en cada `init.sh`), el DDL de arranque ya **no
se escribe a mano** sino que se genera del propio ORM, y el borrado de la
papelera de sv4 deja de emitir los `SAWarning` que arrastraba desde F-004.

## 2. Ficheros tocados

| Fichero | Qué |
|---|---|
| `tests/test_f010_orm_models_gemelos.py` | **nuevo** · guardián R1–R4 (raíz del monorepo) |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | contenido canónico (unión) + `DDL_EXTRA_POSTGRES` + `ddl_complementario()` |
| `services/partes-front/infrastructure/database/orm_models.py` | **byte-idéntico** al anterior |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | `initialize()` usa el generador; fuera `_DDL_ALTERS` y `_DDL_PARTIAL_UNIQUE` (−46 líneas) |
| `services/partes-front/infrastructure/database/parte_repository.py` | `initialize()` idem (−80 líneas de DDL); R11 en `hard_delete_document` y `vaciar_papelera`; import `delete` retirado (ya no se usa) |
| `services/partes-persistencia/tests/test_f010_r6_ddl_complementario.py` | **nuevo** · R6, R9, R10 (+ ampliado en T8) |
| `services/partes-persistencia/tests/test_f010_r7_initialize_sv3.py` | **nuevo** · R7 |
| `services/partes-front/tests/test_f010_r6_ddl_complementario_sv4.py` | **nuevo** (T8) · el generador probado sobre LA COPIA DE sv4 |
| `services/partes-front/tests/test_f010_r8_initialize_sv4.py` | **nuevo** · R8 |
| `services/partes-front/tests/test_f010_r11_borrado_sin_sawarning.py` | **nuevo** · R11 |
| `docs/ARCHITECTURE.md` | punto 7 reescrito (R12) |
| `docs/referencia/partes-proyecto.md` | §5 corregida en el sitio + nota fechada en cabecera (D5) |
| `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` | §4, misma corrección · commit local `8f55505`, **sin push** (ese repo no tiene remoto) |

Sin cambios en sv1, sv2, sv5, `infra/`, manifiestos, `.env` ni `CLAUDE.md`.

## 3. Tarea por tarea, con la verificación real

### T1 · Guardián de las copias gemelas (commit `80a9cb3`)

`tests/test_f010_orm_models_gemelos.py`: R1 (bytes iguales, con `unified
diff` en el fallo), R2 (huella semántica: tabla → columna → tipo compilado a
PostgreSQL, `nullable`, PK, `server_default`, `index`, `unique`, FKs, más
los índices), R3 (4 alteraciones en `tmp_path` + control de que el árbol
real no se toca) y R4 (4 tablas, las 56 columnas literales de
`parte_registros`, atributos de las columnas que aportaba cada copia).

**Fase RED (traza real).** `python -m pytest tests -q -k f010`:

```
FF.....FF                                                                [100%]
E           Failed: las dos copias de orm_models.py han divergido: quien toca una tiene que tocar la otra en la misma feature (CLAUDE.md, LIMITE DE SERVICIO). Diferencias:
E           --- services\partes-persistencia\infrastructure\database\orm_models.py
E           +++ services\partes-front\infrastructure\database\orm_models.py
E           @@ -159,12 +159,9 @@
E                # --- Tipo de registro --- #
E                tipo_hora: Mapped[str | None] = mapped_column(String(16))  # normal|extra|V|B|...
E
E           -    # --- Borrado a nivel LINEA (soft delete -> papelera de sv4). --- #
E           -    # NULL = activo. Lo escribe sv4; sv3 SOLO LO LEE para EXCLUIR estas
E           -    # lineas de las conciliaciones (partida, recurso y reparto de jornada).
E           +    # --- Borrado (soft delete -> papelera). NULL = activo. --- #
...
E           - parte_registros.sigrid_estado: columna solo en sv4
E           - parte_registros.sigrid_hmoide: columna solo en sv4
E           - parte_registros.sigrid_hmores_ide: columna solo en sv4
E           - parte_registros.sigrid_motivo: columna solo en sv4
E           - parte_registros.sigrid_parte_cod: columna solo en sv4
E           - parte_registros.sigrid_registrado_at_utc: columna solo en sv4
E           - parte_registros.sigrid_registrado_by: columna solo en sv4
E       assert not ["tabla 'undo_log': solo en sv4", 'parte_registros.extra_auto: columna solo en sv3', 'parte_registros.horas_orig: colu...']

E       AssertionError: la base 'partes' tiene CUATRO tablas (undo_log solo la escribe sv4)
E         Right contains one more item: 'undo_log'

E       KeyError: 'sigrid_estado'

FAILED tests/test_f010_orm_models_gemelos.py::test_f010_r1_las_dos_copias_son_byte_identicas
FAILED tests/test_f010_orm_models_gemelos.py::test_f010_r2_las_dos_copias_declaran_el_mismo_schema
FAILED tests/test_f010_orm_models_gemelos.py::test_f010_r4_el_orm_canonico_tiene_las_cuatro_tablas_y_56_columnas
FAILED tests/test_f010_orm_models_gemelos.py::test_f010_r4_los_atributos_de_las_columnas_reunidas
4 failed, 5 passed, 6 deselected in 2.46s
```

Es la RED natural que pedía la spec: el guardián nace en rojo contra el árbol
real y nombra exactamente la divergencia que motivó la feature. Los 5 casos
de R3 pasan desde el principio (demuestran que el guardián muerde).

### T2 · Tests del generador de DDL (commit `efc8452`)

**Fase RED (traza real).** `python -m pytest tests -q -k f010` en sv3:

```
ImportError while importing test module '...\tests\test_f010_r6_ddl_complementario.py'.
tests\test_f010_r6_ddl_complementario.py:30: in <module>
    from infrastructure.database.orm_models import (
E   ImportError: cannot import name 'DDL_EXTRA_POSTGRES' from 'infrastructure.database.orm_models'
95 deselected, 1 error in 2.25s
```

### T3 · `orm_models.py` canónico (commit `6719590`)

Base textual de sv3 (comentarios de conciliación más ricos) + el bloque
`sigrid_*` de sv4 en su sitio (tras `parte_estado`) + `UndoLogOrm` +
docstring de «cuatro tablas» + el generador. Copiado byte a byte a las dos
rutas.

```
$ cmp services/partes-persistencia/.../orm_models.py services/partes-front/.../orm_models.py
CMP: identicos
$ python -m pytest tests -q -k f010                  (raíz)      9 passed
$ python -m pytest tests -q -k f010                  (sv3)       9 passed
$ python -m pytest tests -q                          (sv3)     104 passed
$ python -m pytest tests -q                          (sv4)     448 passed
```

Ningún tipo, `nullable`, default ni `__tablename__` cambia respecto a lo que
declaraba la copia que ya tenía cada columna: la BBDD real ya está creada
así (R4).

### T4 · `initialize()` de sv3 (commit `3a15064`)

**Fase RED (traza real).**

```
E           AssertionError: '_DDL_ALTERS' sigue en sqlalchemy_parte_repository.py: el DDL debe salir de ddl_complementario() (orm_models.py), que es la unica declaracion del esquema
FAILED tests/test_f010_r7_initialize_sv3.py::test_f010_r7_initialize_crea_las_tablas_y_luego_completa_el_esquema
FAILED tests/test_f010_r7_initialize_sv3.py::test_f010_r7_no_queda_ddl_escrito_a_mano_en_el_repositorio
2 failed, 1 passed in 0.91s
```

**GREEN**: `python -m pytest tests -q` (sv3) → `107 passed in 2.15s`;
`grep -rn "_DDL_ALTERS\|_DDL_PARTIAL_UNIQUE" services/partes-persistencia`
sin resultados fuera del propio test que lo vigila.

### T5 · `initialize()` de sv4 (commit `f2ce6d1`)

**Fase RED (traza real).**

```
E           AssertionError: 'ADD COLUMN IF NOT EXISTS' sigue en parte_repository.py: el DDL de arranque debe salir de ddl_complementario() (orm_models.py), igual que en sv3
FAILED tests/test_f010_r8_initialize_sv4.py::test_f010_r8_initialize_ejecuta_el_mismo_generador_que_sv3
FAILED tests/test_f010_r8_initialize_sv4.py::test_f010_r8_no_queda_ddl_escrito_a_mano_en_el_portal
2 failed, 2 passed in 1.06s
```

**GREEN**: `4 passed`; `grep -rn "ADD COLUMN IF NOT EXISTS\|CREATE TABLE IF
NOT EXISTS" services/partes-front/infrastructure` → solo `orm_models.py`.
Se conserva el contrato de arranque de sv4 (D6): `True`/`False` con
`logger.exception`, sin propagar; hay test del caso de fallo.

### T6 · R11, los `SAWarning` (commit `6ede86c`)

**Fase RED (traza real).**

```
E           sqlalchemy.exc.SAWarning: DELETE statement on table 'parte_registros' expected to delete 1 row(s); 0 were matched.  Please set confirm_deleted_rows=False within the mapper configuration to prevent this warning. (This warning originated from the Session 'autoflush' process...)
FAILED tests/test_f010_r11_borrado_sin_sawarning.py::test_f010_r11_hard_delete_no_emite_sawarning
FAILED tests/test_f010_r11_borrado_sin_sawarning.py::test_f010_r11_vaciar_papelera_no_emite_sawarning
FAILED tests/test_f010_r11_borrado_sin_sawarning.py::test_f010_r11_lo_congelado_se_sigue_omitiendo_sin_avisos
3 failed, 1 passed in 2.43s
```

**GREEN**: `4 passed`, y la comprobación cruzada que pedía `tasks.md`:

```
$ python -m pytest tests -q -W error::sqlalchemy.exc.SAWarning -k "f004 or f010"
142 passed, 314 deselected, 1 warning in 20.31s
```

(el único warning que queda es el `StarletteDeprecationWarning` de
`fastapi.testclient`, ajeno a F-010). La suite de sv4 pasa de **5 avisos a
0**.

### T7 · Documentación (commit `4404348` + `8f55505` en `azure-apps`)

`docs/ARCHITECTURE.md` punto 7 reescrito; `docs/referencia/partes-proyecto.md`
§5 corregida en el sitio con la línea «Corregido el 2026-08-18 por F-010» en
la cabecera (D5), nueva §5.4 de `undo_log` y renumerado de «Datos que NO
están» a §5.5; misma corrección en `azure-apps/partes.md` §4.

Barrido C3 bis sobre lo añadido (correos, IPs, GUID, tokens, claves) en los
dos repositorios: **sin coincidencias**.

### T8 · Mutación y refuerzo de los tests (commits de T8)

La **primera** campaña dio 23 mutantes, 5 muertos y **18 supervivientes**.
No se justificaron como equivalentes: casi todos señalaban un hueco real
(análisis completo en `progress/mutacion_F-010.md`, sección «Nota del
implementer»). Se añadieron 11 tests —DDL literal de `undo_log` y de las
siete `sigrid_*`, autoincremento de las PK, defaults de Python, orden
alfabético de los índices, y un fichero propio en sv4 que prueba SU copia
del generador— y la segunda campaña quedó en **23/23 muertos, 0
supervivientes**.

### T9 · Cierre (`bash harness/init.sh`)

`exit 0` · `ENTORNO LISTO`. De regalo, la deuda de ruff del repositorio baja
de **450 a 430** avisos al desaparecer el DDL escrito a mano.

## 4. Decisiones de diseño y desviaciones

- **D1–D7 de la spec: aplicadas tal cual.** Ninguna decisión nueva.
- **Desviación menor (1).** El diseño escribía
  `sorted(tabla.indexes, key=lambda i: i.name)`; el código usa
  `key=lambda i: i.name or ""`. Motivo: un índice sin nombre haría reventar
  el `sorted` comparando `str` con `None`. Mismo orden para todos los
  índices reales (todos tienen nombre).
- **Desviación menor (2).** Se retira `from sqlalchemy import delete` de
  `parte_repository.py`: R11 eliminó sus dos únicos usos y `ruff` lo marcaba
  como `F401`. El diseño ya lo anticipaba («se conserva si lo usan otros
  métodos: comprobar»).
- **`ISC004`** (nuevo aviso de ruff que introducía `DDL_EXTRA_POSTGRES`)
  corregido envolviendo la cadena en paréntesis. Lo nuevo queda limpio.
- **Deuda previa NO tocada** (fuera de alcance, declarada como aviso por
  `init.sh`): `UP037` en `orm_models.py` (2), `I001` en
  `sqlalchemy_parte_repository.py` (1) y los 84 avisos de
  `parte_repository.py`, que son **exactamente los mismos que en `dev`**
  (comprobado pasando ruff sobre la versión de `dev` por stdin). El
  repositorio de sv3 baja de 21 avisos a 1.

## 5. Riesgo operativo (lo que cambia en la BBDD real al desplegar)

Todo el DDL que emite F-010 es `IF NOT EXISTS` y aditivo; sobre una base que
ya tiene las 56 columnas es un **no-op**. El **único cambio físico
esperado** es el índice `ix_parte_registros_deleted_at_utc`, que ambas
copias del ORM ya declaraban y la BBDD no tenía (D3, autorizado por el
humano): tabla de 104 filas, creación instantánea, solo en la base `partes`.
Nada a nivel de servidor del PostgreSQL compartido.

Ningún agente ha ejecutado DDL contra el PostgreSQL real: los tests de
`initialize()` usan un `engine` doble (D7).

## 6. Verificaciones MANUAL pendientes (humano, requieren BBDD real)

- **M1 · el único cambio físico es el índice.** Tras arrancar sv3 o sv4 en
  local con el `.env` de desarrollo:
  ```sql
  SELECT indexname FROM pg_indexes
   WHERE schemaname='public' AND tablename='parte_registros' ORDER BY 1;
  ```
  Debe listar `ix_parte_registros_deleted_at_utc` (nuevo),
  `ix_parte_registros_document_id`, `ix_parte_registros_empleado_ide` y
  `parte_registros_pkey`. Y que el número de columnas NO cambió:
  ```sql
  SELECT table_name, count(*) FROM information_schema.columns
   WHERE table_schema='public' GROUP BY 1 ORDER BY 1;
  ```
  → `empleado_alias 7`, `parte_documents 47`, `parte_registros 56`,
  `undo_log 7`.
- **M2 · el arranque no revienta.** `python main.py` (o `main_worker.py`) en
  sv3 y `python main.py` en sv4 terminan sin excepción en `initialize()`.
  En el log debe aparecer `[parte-repo] esquema inicializado (N sentencias
  complementarias).` en sv3 y `[parte-repo-sv4] esquema inicializado (N
  sentencias complementarias).` en sv4, con el mismo N en los dos.
- **M3 · despliegue** (cuando el humano lo decida, `redeploy_partes.ps1`):
  orden habitual sv3 antes que sv4; como el DDL es el mismo e idempotente,
  el orden no es crítico para F-010.

## 7. Fuera de alcance (no se hizo, a propósito)

Cambiar tipos/nombres/nullabilidad de columnas existentes; añadir columnas
nuevas (`EmpleadoJornadaOrm` es F-015); Alembic; tocar la FK
`parte_registros.document_id`; unificar el comportamiento de `initialize()`
ante fallo entre sv3 y sv4 (D6); cualquier cosa de sv1, sv2, sv5 o `infra/`.
La deuda de ruff previa tampoco se toca.

## 8. Evidencias

| Evidencia | Valor medido |
|---|---|
| **Tests ejecutados** | **676 en verde, 0 fallos**: raíz 15 (6 → 15), sv3 112 (95 → 112), sv4 462 (448 → 462), sv5 87 (sin cambios). **+40 tests nuevos de F-010** |
| **Cobertura de las líneas cambiadas** | **100,0 % (60/60 líneas)**, umbral 80 % (línea `PUERTA COBERTURA` de `bash harness/init.sh`, nivel `estandar`) |
| **Mutantes generados / supervivientes** | **23 generados, 23 muertos, 0 supervivientes, 0 timeouts** en 61,0 s (segunda campaña; la primera dio 18 supervivientes y se taparon los huecos — sección 9) |
| **Tiempo de ejecución de la suite** | raíz 3,64 s · sv3 3,58 s · sv4 64,66 s · sv5 4,05 s (**≈ 76 s** el conjunto que ejecuta `init.sh`) |
| **`bash harness/init.sh`** | **exit 0** — `ENTORNO LISTO` |
| **Avisos `SAWarning` en la suite de sv4** | 5 → **0** |
| **Deuda de ruff del repositorio** | 450 → **430** avisos (al desaparecer el DDL a mano) |

## 9. Campaña de mutación

`python -m harness.mutacion --feature F-010` · alcance: 257 líneas de
producción en 4 ficheros · informe completo en
**`progress/mutacion_F-010.md`**.

| Campaña | Mutantes | Muertos | Supervivientes | Tiempo |
|---|---|---|---|---|
| 1.ª (antes de reforzar) | 23 | 5 | **18** | 67,1 s |
| 2.ª (final) | 23 | **23** | **0** | 61,0 s |

**Qué enseñaron los 18 supervivientes** (análisis completo en el informe de
mutación; ninguno se cerró como «equivalente» sin más):

1. El guardián de las copias gemelas vive en la suite de la **raíz**, y la
   herramienta solo ejecuta la suite del **servicio** cuyo fichero muta. Por
   eso sobrevivían mutaciones que `init.sh` sí caza (cambiar `String(255)`
   por `String(256)` en una sola copia rompe R1/R2/R4). Es una limitación de
   la herramienta, no un hueco de los tests —pero servía de tapadera para
   los otros dos puntos, así que igualmente se tapó.
2. **13 de los 18** eran mutaciones sobre `undo_log` y las siete `sigrid_*`
   dentro de la copia de **sv3**: columnas que sv3 declara (la base es una
   sola) y no lee nadie allí, así que su suite no las miraba.
3. En **sv4** nadie probaba su copia del generador: R8 compara lo ejecutado
   contra `ddl_complementario()` del mismo módulo —si el generador se
   estropea, los dos lados cambian a la vez y el test sigue verde—.

Se añadieron 11 tests que fijan el DDL literal de `undo_log` y de las
`sigrid_*`, el autoincremento de las PK, los defaults de Python
(`extra_auto`, `es_incidencia`, `undone`) y el orden alfabético de los
índices, más el fichero
`services/partes-front/tests/test_f010_r6_ddl_complementario_sv4.py`, que
ejercita **la copia de sv4**. Ninguna sección del informe de mutación queda
en `PENDIENTE`.
