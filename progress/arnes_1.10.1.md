<!-- progress/arnes_1.10.1.md -->
# Actualización del arnés 1.7.3 → 1.10.1 · BLOQUEADA en el paso 6

Fecha: 2026-11-13. Worktree `partes-wt-arnes`, rama `chore/arnes-1.10.1`
(sale de `dev` 680d191). Sin merge ni push.

**Estado: `init.sh` en ROJO por dos tests del payload que no son errores de
porte.** Paré según el plan: no he tocado esos tests ni los ficheros de partes
que señalan. Decisión del humano en «Abierto».

## Commits

| Commit | Qué |
|---|---|
| `cf1c645` | Informe `-SoloDiff` → `progress/arnes_1.10.1_solodiff.txt` (70 nuevos, 32 cambian, 11 iguales salvo finales de línea, 5 protegidos) |
| `18c722e` | `-Forzar`: 70 nuevos + 27 actualizados de arnés puro, `harness/VERSION` y `ARNES_VERSION.md` (backup del instalador en `%LOCALAPPDATA%\arnes-base\backups\partes-wt-arnes\20261113-140325`) |
| `a6b6995` | Cambios locales reaplicados en `reviewer.md` y `backlog.py` (+ test) |
| `f71eb7f` | `harness/rigor.local.json` con `mutacion.timeout_por_mutante_s: 600` |
| `5f644c3` | Porte a mano de los adaptados |
| `f862147` | Migración de la guía en `harness/servicios.json` |
| `eff3d1d` | `BACKLOG.md` regenerado |

## Ficheros adaptados (restaurados con `git checkout --` y portados a mano)

Fuente: `git diff a695c32..HEAD -- arnes-base/<f>`. Comparación con `diff --strip-trailing-cr`.

- **CLAUDE.md**: `qa-e2e` entre los subagentes; la primera parada pasa a ser el resumen de la spec (o la PARADA 1 si no hay spec); el resumen final dice qué queda listo para el push y termina con «Tu OK es el permiso…»; orden de prioridad de los ocho estados con «una activa»; regla «tal cual» con `ARNES_SIN_CACHE=1`; commits directos no, merges sí; regla dura del push; en el bloque de Ruesma, el protocolo de `azure-apps` (`git pull --rebase`, commit aparte, push del humano, PARAR si hay conflicto) y el párrafo de cuentas de GitHub. Se conservan sin tocar el mapa, las reglas duras de partes (Sigrid, PostgreSQL compartido, despliegue) y el LÍMITE DE SERVICIO con su lista cerrada. Fuera del título, del mapa, de las reglas duras y del límite de servicio, el resultado queda igual que la plantilla 1.10.1.
- **CHECKPOINTS.md**: se parte de la plantilla 1.10.1 y se reaplica la única adaptación de partes: las tres trampas de dominio de C3.
- **harness/init.sh**: se parte de la plantilla 1.10.1 y se reaplican `REQUIERE_ENV=0` y las dos cabeceras («adaptada al monorepo partes», «sección 9: ninguna activa»). Compruebo `RAMA_BASE=dev`: `main..dev` = 895 commits y `dev..main` = 0. Es correcto.
- **docs/CONVENTIONS.md**: sección Git (quién hace cada merge y el push).
- **.claude/settings.json**: era idéntico a la plantilla 1.7.3, así que se toma el de la 1.10.1: sin `PostToolUse`, con `model` y `effortLevel: high`, `ARNES_SIN_CACHE` y los permisos del reviewer.
- **docs/referencia/README.md**: no cambia en la plantilla.

## Cambios locales reaplicados (arnés puro)

- **reviewer.md (a)**, la suite de un servicio servida de caché (F-064): **no se reaplica**. La 1.10.1 ya la cubre y es más estricta: el paso 1 manda `ARNES_SIN_CACHE=1 bash harness/init.sh`, que ejecuta todas las suites sin caché (F-028, que cita F-064).
- **reviewer.md (b)**, lanzar pytest con el mismo intérprete (F-056): reaplicada con el texto exacto, al final de RM4. La 1.10.1 no la trae.
- **rigor.json → `harness/rigor.local.json`**: solo `{"mutacion": {"timeout_por_mutante_s": 600}}`, con `$doc` (origen dc693cc). `--validar` responde «capa local: mutacion.timeout_por_mutante_s».
- **backlog.py, adaptación propia de partes**: «Spec» (campo `spec`) en todas las columnas abiertas y en «Otros estados»; «Pendiente» (campo `pendiente`) en Done; sus dos líneas en el Detalle. En el tablero nuevo las columnas extra van tras «Feature» y las propias de cada columna, no en la posición de antes. Test propio `tests/test_backlog_columnas_partes.py` (4 tests): da 4/4 en rojo con el `backlog.py` del payload y 4/4 en verde con el adaptado. `tests/test_backlog_md.py` del payload sigue en verde.

## Migraciones de la guía (1.7.4 → 1.10.1)

- **1.7.16 §2** (en un monorepo, declarar lo que la suite usa fuera de su carpeta): `sv3-persistencia` declara `depende_de` sobre los dos ficheros de sv4 que leen sus tests de gemelos (`jornada_resolver.py` y `sesame_api_client.py`). No declaro `importa` porque no hay librería común.
- **features.json**: la guía no manda migrarlo (F-042 y F-040). No se toca y ninguna feature cambia de estado. `rules.valid_status` y `$schema_doc` se quedan viejos; la guía dice que son opcionales.
- **`no_cuentan`** (F-040): ya incluye `**/tests/**`, nada que adaptar.
- **.gitignore** (1.7.4): el bloque ya estaba.
- **Sin acción**: 1.7.5–1.7.10, 1.9.0 (no hay subclases de `EjecutorPytest` ni tests que fijen el criterio viejo; la suite raíz no muestra rojos de eso) y 1.10.0 (los adaptados ya están portados; `BACKLOG.md` regenerado).
- **No hecho**: la comprobación opcional de la 1.7.6 (suite con `PYTHONDONTWRITEBYTECODE=1`).

## Intérprete

El worktree no tiene `.venv`. La sesión trae `VIRTUAL_ENV` apuntando al `.venv` de `partes`, e `init.sh` lo respeta. `partes-wt-f069` tampoco tiene `.venv` y funcionaba igual. `servicios --shell` resuelve los cinco servicios a `partes\.venv\Scripts\python.exe`.

## Resultado real de `bash harness/init.sh`

```
[KO] pytest en rojo (¿pytest instalado en el venv?)      ← suite raíz
[OK] servicio sv1-email: 74 passed
[OK] servicio sv2-extraccion: 422 passed
[OK] servicio sv3-persistencia: 2453 passed, 2 skipped
[OK] servicio sv4-front: 3751 passed, 1 skipped (11 min)
[OK] servicio sv5-transfer: 1628 passed
1 comprobaciones fallidas. NO empieces a trabajar.
```

La suite raíz para en el primer fallo, así que la relancé entera a mano (`pytest -q -p no:cacheprovider tests/`): **2 failed, 2447 passed, 49 skipped**. El resto del portero sale OK o N/A. Avisos esperados: `BACKLOG.md` regenerado, CAPA LOCAL DE RIGOR (necesita el OK del humano, que ya consta en el plan aprobado), F-032 `blocked` y 1005 avisos de ruff (deuda previa).

### Los dos rojos

1. **`tests/test_f019_tiempos.py::test_f019_r22_ningun_test_lanza_subprocesos_con_timeout_literal`**. Es una puerta nueva de la 1.10.0/1.10.1. Señala cuatro tests propios de partes que lanzan `subprocess.run` con un timeout literal: `test_f024_borrado_no_congela_gemelos.py:54` (60), `test_f046_contrato_reajuste.py:89` (120), `test_f052_r28_congelacion_intacta.py:58` (60) y `test_f056_contrato_franquicia.py:89` (120). Según la guía, se arreglan pasando esos timeouts por `harness.tiempos.escalar_timeout`. Eso toca tests propios de partes, y uno de ellos vigila los gemelos de congelación, así que queda fuera del plan aprobado.
2. **`tests/test_f063_textos.py::test_f063_r2_el_payload_no_trae_capa_local`**. Es un defecto conocido del payload, ya recogido en `arnes-base/ENCARGO_pendiente_test_f063_r2_rojo_en_proyectos_con_capa_local.md` (de postventa, 2026-11-12) y sin arreglar en la 1.10.1. El test exige que **no** exista `harness/rigor.local.json`, y el paso 4 del plan obliga a crearlo. El encargo propone marcar el test como del taller (`skipif` si no está `politica_ficheros.json`). Postventa lo aplicó en local, pero el plan me prohíbe marcar tests como saltados.

## Abierto: decide el humano

- **Rojo 1**: (a) envolver los cuatro timeouts con `escalar_timeout` en una tarea aparte (son 4 líneas en tests, sin tocar `services/`); o (b) otra salida que decida el humano.
- **Rojo 2**: (a) aplicar en local el `skipif` del encargo, como hizo postventa; (b) no usar la capa local y devolver el 600 a `rigor.json`, que se perdería en la próxima actualización; o (c) arreglarlo antes en `arnes-base` y republicar.
- **Comportamiento nuevo sin pregunta** (llega con la 1.10.1, conviene que el humano lo sepa): el líder hace los merges a `dev` sin preguntar tras el OK final. Sigue sin hacer push y pregunta antes de mergear a `main`. El modelo y el esfuerzo quedan fijados en `settings.json` y en los agentes, y `estandar` deja de bloquear por mutación.
- La plantilla del bloque de Ruesma trae el párrafo de cuentas de GitHub con un login. `test_f070_textos` lo exige literal, así que no se puede omitir.
- Si se aprueba, falta además: relanzar `init.sh` en verde y anotar en `features.json` las fechas opcionales (`ok_humano`, `fecha_cierre`); esto último no es obligatorio.
