<!-- progress/impl_F-054.md -->
# F-054 · Un parte sin obra o sin fecha leídas va siempre a revisión — informe del implementer

Rama `feature/F-054-sin-obra-o-fecha-a-revision` (worktree `partes-wt-f054`), rigor
`estandar`, solo sv3. Aprobación del humano: 2026-10-21, literal «apruebo F-054 y la DA5»
(DA1–DA7 con la recomendación, DA3 = B), y 2026-10-23, literal «si, lanza f54 y la spec de
relectura con gemini». Contexto del líder del 2026-10-23: 4 páginas más del escaneo de hoy
con la cabecera a null, `obra_match_method = 'none'` y `review_required = false`; la causa
(sv2) es F-058 y el alcance de F-054 no cambia.

**Estado: T1–T5 hechas; T6 (mutación) la lanza el líder; T8 (M2) y T9 (M3) son MANUAL.**

## Rebase

La rama salía de `dev` 206354d; se rebasó sobre `dev` 38f273a. Conflictos solo en
`harness/features.json`, `BACKLOG.md` y `progress/current.md` (los dos commits de la spec).
Se quedó el lado de `dev`: su entrada de F-054 es **idéntica** a la de la rama original
(6fcfbb7), comprobado por script campo a campo (una sola entrada), y `BACKLOG.md` se
regeneró con `python harness/backlog.py`. Los ficheros de la spec entraron sin conflicto.

## Qué cambió

| Fichero | Cambio |
|---|---|
| `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py` | `MOTIVO_SIN_OBRA`, `MOTIVO_SIN_FECHA` y función pura `motivos_cabecera` (R1–R3); `_compute_review_required` usa `motivos_cabecera` en el sitio de `OBRA_A_REVISAR`, que se borra (R6); WARNING de R7 en `run` tras `save_parte`; paso 5 del docstring (R13) |
| `services/partes-persistencia/tests/test_f054_revision_cabecera.py` (nuevo) | 34 tests: R1–R7 y R9 (`design.md` §6.1) |
| `services/partes-persistencia/tests/test_f023_pipeline_match.py` | `test_f023_review_required_por_la_obra` pasa a `(metodo, con_obra, esperado)` (§6.2); `("none", sin obra)` ⇒ `True` |
| `services/partes-persistencia/tests/test_f030_casado_recurso.py` | `_parte_revisable` con `ObraMatch(ide=1, codigo="0724", method="codigo")` (neutra) |
| `services/partes-persistencia/tests/test_f051_lectura_dudosa.py` | `_parte_casado` con `fecha_int=20261017` (neutra) |
| `docs/ARCHITECTURE.md` | Semántica 18 (R13) |
| `harness/features.json`, `BACKLOG.md`, `progress/current.md`, `tasks.md` | `in_progress`, tareas marcadas, seguimiento |

Commits: `in_progress` 2142a8e, T1 4a3e754, T2 f552dd3, T3 1c17292, T4 8d63b4e, T5 c1a91cb
(la spec rebasada: c65e412 y 9e8e80d).

## Decisiones de diseño

- `motivos_cabecera` es una función de módulo (como `empresa_del_parte`), pura, y la
  condición de fecha es `fecha_int is None or fecha_int <= 0` (no `not fecha_int`), como
  pide `design.md` §3. `_compute_review_required` sigue `@staticmethod` con la misma firma.
- El WARNING se emite **después** de `save_parte` (con `document_id` ya asignado) y
  recalcula `motivos_cabecera(parte)` en vez de pasar el resultado desde
  `_compute_review_required`: así la firma de este último no cambia. Formato literal de
  `design.md` §3; `obra_leida` es `parte.obra_numero_leido` (`%r`).
- Los tests de ingesta de R7/R9 usan su propio `_Repo` en memoria y un `_match` de mentira
  que casa a los trabajadores (patrón `_ingerir` de `test_f051`); R9 de columnas reutiliza
  `_montar` y `_request` de `test_f036_pipeline` (SQLite en memoria), como dice §6.1. Los
  de casado real (R1, R2) reutilizan `_casar` y `_parte` de `test_f023_pipeline_match`.

## Desviaciones respecto a la spec (justificadas)

- **Tests añadidos que la tabla de §6.1 no lista**, para matar mutantes de frontera y del
  formato: `test_f054_r2_con_fecha_positiva_no_hay_motivo` (`fecha_int = 1` no es «sin
  fecha»: mata `<= 0` → `<= 1`), `test_f054_r3_constantes_de_los_motivos` y
  `test_f054_r7_el_warning_lleva_la_obra_leida` (solo `sin_fecha`, con obra casada:
  comprueba `obra_match_method=codigo` y `obra_leida='0100'`). R5 comprueba además que
  cada causa estropeada no cambia `motivos_cabecera` (`()`) y que el parte base no iba a
  revisión antes de estropearlo. El payload del hallazgo lleva DNIs ficticios (§6.3 no
  los pone) para que R7 compruebe también que el WARNING no los repite.
- **Texto de la semántica 18**: §7 termina «lo guardado antes se corrigió una vez a mano
  (M2)»; la M2 **aún no se ha hecho**, así que se escribe en presente: «se corrige una
  sola vez a mano (M2 de F-054: un `UPDATE` que solo sube la bandera en los activos no
  aprobados)». Si el humano descartara la M2, hay que quitar esa frase.
- `design.md` §5 y T3 hablan de 2.254 tests de sv3; en `dev` 38f273a son 2.271 (F-049 y
  otras entraron después). Con F-054: 2.305 (2.271 + 34 nuevos), sin tocar más tests que
  los de T1–T2.

## Fase RED (trazas reales)

**RED 1 · T2, antes de cualquier cambio de código** (HEAD 4a3e754), desde
`services/partes-persistencia`:

```
$ python -m pytest tests/test_f054_revision_cabecera.py tests/test_f023_pipeline_match.py
collected 47 items / 1 error
____________ ERROR collecting tests/test_f054_revision_cabecera.py ____________
tests\test_f054_revision_cabecera.py:19: in <module>
    from application.pipelines.persist_parte_pipeline import (
E   ImportError: cannot import name 'MOTIVO_SIN_FECHA' from 'application.pipelines.persist_parte_pipeline'
============================== 1 error in 0.72s ===============================

$ python -m pytest tests/test_f023_pipeline_match.py -k review_required_por_la_obra
>       assert PersistPartePipeline._compute_review_required(parte) is esperado
E       AssertionError: assert False is True
tests\test_f023_pipeline_match.py:500: AssertionError
FAILED tests/test_f023_pipeline_match.py::test_f023_review_required_por_la_obra[none-False-True]
================= 1 failed, 4 passed, 42 deselected in 0.50s ==================
```

**RED 2 · T3 a medias**: con solo las constantes y `motivos_cabecera` añadidas (sin usarla
en `_compute_review_required`, `OBRA_A_REVISAR` aún presente y sin WARNING), para ver el
fallo de comportamiento y no solo el de importación:

```
$ python -m pytest tests/test_f054_revision_cabecera.py -q -rf
FAILED tests/test_f054_revision_cabecera.py::test_f054_r1_sin_obra_va_a_revision[none]
FAILED tests/test_f054_revision_cabecera.py::test_f054_r1_sin_obra_va_a_revision[metodo_nuevo]
FAILED tests/test_f054_revision_cabecera.py::test_f054_r1_por_el_casado_real
FAILED tests/test_f054_revision_cabecera.py::test_f054_r2_sin_fecha_va_a_revision[None]
FAILED tests/test_f054_revision_cabecera.py::test_f054_r2_sin_fecha_va_a_revision[0]
FAILED tests/test_f054_revision_cabecera.py::test_f054_r2_sin_fecha_va_a_revision[-1]
FAILED tests/test_f054_revision_cabecera.py::test_f054_r2_sin_fecha_por_el_casado_real
FAILED tests/test_f054_revision_cabecera.py::test_f054_r3_motivos_cabecera[False-True-esperado1]
FAILED tests/test_f054_revision_cabecera.py::test_f054_r3_motivos_cabecera[True-False-esperado2]
FAILED tests/test_f054_revision_cabecera.py::test_f054_r3_motivos_cabecera[False-False-esperado3]
FAILED tests/test_f054_revision_cabecera.py::test_f054_r6_obra_a_revisar_desaparece
FAILED tests/test_f054_revision_cabecera.py::test_f054_r7_warning_con_motivos_sin_nombres
FAILED tests/test_f054_revision_cabecera.py::test_f054_r7_el_warning_lleva_la_obra_leida
FAILED tests/test_f054_revision_cabecera.py::test_f054_r9_ingesta_del_hallazgo
FAILED tests/test_f054_revision_cabecera.py::test_f054_r9_columnas_guardadas
15 failed, 19 passed in 1.88s
```

Detalle de dos de ellos (el hallazgo, con dobles y con SQLite):

```
    def test_f054_r9_ingesta_del_hallazgo(monkeypatch) -> None:
        ...
        assert parte.fecha_int is None
        assert parte.obra.ide is None
>       assert guardado["review_required"] is True
E       assert False is True
    def test_f054_r9_columnas_guardadas() -> None:
        ...
>           assert doc.review_required is True
E           assert False is True
E            +  where False = <infrastructure.database.orm_models.ParteDocumentOrm object at 0x000001F73D644200>.review_required
```

Los 19 que pasaban en RED 2 son los que deben pasar ya: R4 (casado completo), R5 (las demás
causas), R1 con los métodos sin casar de F-023 (ya estaban en `OBRA_A_REVISAR`), R3 del caso
completo, R7 sin motivos y las constantes.

**GREEN · T3 completa** (HEAD 1c17292):

```
$ python -m pytest -q tests/test_f054_revision_cabecera.py tests/test_f023_pipeline_match.py
81 passed in 1.63s
$ python -m pytest -q
2305 passed in 22.12s
```

## Verificaciones

- T1: `python -m pytest tests/test_f030_casado_recurso.py tests/test_f051_lectura_dudosa.py`
  ⇒ `84 passed` antes del cambio de código (neutras).
- T4: `git diff dev --stat -- services/partes-front services/partes-transfer
  services/partes-persistencia/infrastructure` ⇒ **vacío** (R8: ni sv4, ni sv5, ni esquema).
- T5: `python -m harness.tamano --feature F-054` ⇒ `PUERTA TAMAÑO: F-054 dentro de los
  topes (requirements 108/150, design 235/250)`.
- `grep OBRA_A_REVISAR` en el código: solo queda en el test de R6.
- T10: `bash harness/init.sh` (HEAD c1a91cb) ⇒ **«ENTORNO LISTO. Puedes trabajar.»**, exit 0:
  raíz 498 passed / 3 skipped; sv3 2.305 passed; sv1, sv2, sv4 y sv5 en verde (caché);
  `PUERTA COBERTURA: 100.0% de 13 líneas cambiadas cubiertas (13/13, umbral 80%)`;
  `PUERTA TAMAÑO` en verde. Avisos previos, no de F-054: F-032 `blocked`, ruff 772 avisos
  de deuda previa (desde la configuración de sv3, los ficheros tocados pasan `ruff`; el
  único aviso, UP045 en `__init__`, ya estaba), infra sin tests.

## Verificaciones MANUAL pendientes (NO ejecutadas)

- **T6 · mutación**: la lanza el líder (`python -m harness.mutacion --feature F-054`, nivel
  `estandar`: muestreada a 20 mutantes, semilla 20260820) ⇒ `progress/mutacion_F-054.md`;
  el análisis de supervivientes se añade aquí después.
- **T8 · M2** (DA3 = B): escritura en la base `partes`; **solo con autorización expresa del
  humano para esta acción y tras `redeploy_partes.ps1 -Solo sv3`** (lo pide el humano).
  Comando exacto (`design.md` §8; `<servidor>` y `<usuario>` del Key Vault):
  ```powershell
  psql -X -v ON_ERROR_STOP=1 -c "UPDATE parte_documents SET review_required = true WHERE is_active AND NOT approved AND review_required IS NOT TRUE AND (obra_ide IS NULL OR fecha_int IS NULL OR fecha_int <= 0)" "host=<servidor> dbname=partes user=<usuario> sslmode=require"
  ```
  Esperado: `UPDATE n`, con `n` = los activos no aprobados sin obra o sin fecha con
  `revisar = f`. M1 del 2026-10-21 daba **3**; con las 4 páginas del 23/10 que ha visto el
  líder, si siguen sin aprobar y sin arreglar, serían **7**: conviene repetir M1 (solo
  lectura) justo antes. Repetirlo da `UPDATE 0`. Solo sube la bandera.
- **T9 · M3**: tras unos días con sv3 desplegado, M1(a) con `AND created_at_utc >= '<hora
  UTC del despliegue>'`: ninguna fila con `revisar = f`, y un WARNING «cabecera incompleta»
  por parte en el log de sv3.

## Fuera de alcance

La guarda de sv5 contra `fecha_int = 0` (F-055), la relectura de la cabecera en sv2
(F-058), enseñar el motivo en el portal (DA4 B/C), fechas corregidas o lejanas (DA2 B/C) y
bajar la bandera al arreglar obra o fecha.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados (sv3) | **2.305 passed**, 0 fallos (2.271 de `dev` + 34 de F-054), 22,12 s |
| Tests nuevos de F-054 | 34 en `test_f054_revision_cabecera.py` (+ 1 caso cambiado en `test_f023`) |
| Cobertura de las líneas cambiadas | **100,0 %** de 13 líneas cambiadas (13/13), `PUERTA COBERTURA` de `init.sh` |
| Mutantes generados / supervivientes | **PENDIENTE: la campaña la lanza el líder** (T6) |
| Tiempo de la suite | sv3: 22,12 s; dentro de `init.sh`, sv3 39,71 s y tests de raíz 95,95 s |
