# F-052 · Informe del implementer (tanda T1–T8)

Rama `feature/F-052-sincronizar-con-sigrid`, worktree `partes-wt-f052`, desde 846f6aa.
Rigor **crítico**. Alcance de esta tanda: T1–T8; **T8 es el punto de control** (M2 del humano):
lo posterior (acciones que escriben en líneas congeladas, T9–T17) NO está hecho.
La campaña de mutación la lanza el líder después.

## Qué cambió

| Tarea | Commit | Qué |
|---|---|---|
| T1 | bb9f5c7 | F-052 `in_progress`, BACKLOG, `current.md`; datos de partida (abajo) |
| DA18 | bc1de1c | Spec: DA18 = A (modo seco) en `design.md` §5/§8/§9, R10 y T7/T8 |
| T2 | 7996ed3 | sv5 `origen_de`, `lineas_sincronizar`, `lineas_sincronizar_por_synckey`, `LineaSincronizar` |
| T3 | 7b21c40 | sv5 `POST /api/sincronizar/leer` y `SINCRONIZAR_MAX_REGISTRO_IDS` (3000) |
| T4 | 668d88a | Suite sv5 completa; `application/` de sv5 sin cambios (R26) |
| T5 | a5bcef1 | sv4 `application/services/sincronizacion.py` (puro: 12 clases, firma, acciones) |
| T6 | 9c3757e | sv4 `lineas_para_sincronizar`, `donde_estan` en `parte_repository.py` |
| T7 | 7fed7fb | sv4 `sincronizar_ambito.py`, `transfer_client.sincronizar_leer`, `POST /api/sincronizar`, `SINCRONIZAR_TIMEOUT_S`, `SINCRONIZAR_SECO` |
| doc | azure-apps dddde8a | `partes.md`: nota F-052, endpoint de sv5 (§3.5) y variables (§5.6). Sin push |

Producción: sv5 `sigrid_write_client.py`, `registro_models.py`, `api/app.py`, `settings.py`; sv4
`sincronizacion.py` y `sincronizar_ambito.py` (nuevos), `parte_repository.py`, `transfer_client.py`,
`web/app.py`, `settings.py`. **Sin tocar**: `congelacion.py`, `recurso_conciliador.py`,
`comprobacion_sigrid.py`, `comprobacion_lineas.py`, ORM, gemelos, sv1–sv3, `application/` de sv5.

## T1 · Base y datos de partida

- `git merge-base --is-ancestor dev HEAD` ⇒ verdadero: `dev` sigue en 69af0f5, ya fusionado.
- **Persona** (F-050, `_clave_trabajador`): `rec-{recurso}` si está casada con recurso
  (`recurso_ide` o `empleado_reside`); si no, `emp-`/`nom-`/`sin-trabajador`, que no leen Sigrid.
  **Obra**: `obr-{ide}`; `cod-`, `nom-`, `sin-obra` no (R15).
- **M1** (líder, 2026-11-02, design §9): 371 líneas en 4,8 s, lote de 200 synckeys 7,9 s, sin
  `truncated`; sin líneas `partes:`, por eso M2 va a ámbitos con líneas del portal.

## DA18 · modo seco (humano, 2026-11-03)

**Variable de entorno de sv4 `SINCRONIZAR_SECO`, `true` por defecto**, sin campo en la petición.
En seco, `POST /api/sincronizar` NO llama a `comprobar_ids` (la única escritura de R10): lee
`registrados_para_comprobar`, pide a sv5 el mismo veredicto (`/api/registro/comprobar`, lectura,
lotes de `COMPROBACION_SIGRID_LOTE`), clasifica igual y devuelve `seco: true` y
`marcaria_borrado_sigrid`. Fuera de seco: `marcadas_borrado_sigrid` (escribe como F-024).
**Por qué el defecto impide una escritura accidental en M2**: un sv4 local sin la variable arranca
en seco y ninguna petición (curl o navegador) puede pedir otra cosa; salir de seco exige poner
`SINCRONIZAR_SECO=false` en el entorno a propósito, tras T8.

## Decisiones de implementación (para revisar en M2)

- **ID1**: un `registrado` sin pareja que F-024 NO da por borrado (o que dejó de estar
  `registrado` entre lecturas) ⇒ 409 «vuelve a sincronizar», sin ítems (R13). El respaldo de
  `clasificar` usa los criterios de F-024 (sin synckey, recurso, fecha y parte): solo en carreras.
- **ID2**: `partes:` sin id (`partes:abc`) ⇒ `origen = ajena`, como `registro_de_synckey` (None).
- **ID3**: en incidencias no se comparan horas (R9) ni clase de hora; el código es nota.
- **ID4**: candado R29 por (vista, clave), sin periodo: dos periodos de la misma obra a la vez, 409.
- **ID5**: synckey repetida en Sigrid: casa la de menor `hmores.ide`; la otra es
  `solo_sigrid_nuestra` con nota, sin `donde` ni `restaurar`.
- **ID6**: por `registro_ids` sv5 busca solo `partes:<id>`; el CIZ hermano sale si está en el ámbito.
- **ID7**: el periodo es obligatorio (sin `period` ⇒ 422); `mode` por defecto nómina.

## Fase RED (trazas reales)

Python: `C:/Users/pgris/PycharmProjects/partes/.venv/Scripts/python.exe -m pytest …`, desde la
carpeta de cada servicio. Cada test se escribió y se ejecutó ANTES que su código.

**T2 (sv5, R1–R3, R5, DA11, DA12)** — `pytest tests/test_f052_leer_sincronizar.py -q`:
```
tests\test_f052_leer_sincronizar.py:23: in <module>
    from domain.models.registro_models import LineaSincronizar
E   ImportError: cannot import name 'LineaSincronizar' from 'domain.models.registro_models'
ERROR tests/test_f052_leer_sincronizar.py
1 error in 0.68s
```
Verde: `37 passed in 0.59s`.

**T3 (sv5, R1, R4–R6)** — `pytest tests/test_f052_api_sincronizar.py -q`:
```
E       TypeError: build_app() got an unexpected keyword argument 'lector'      (16)
E       assert 404 == 502                                                       (4)
E       assert (404 == 200)                                                     (2)
E                   AttributeError: 'Settings' object has no attribute 'sincronizar_max_registro_ids'
23 failed, 1 warning in 2.20s
```
Verde: `60 passed` (T2 + T3).

**T5 (sv4, R8, R9, R11, R16, R18)** — `pytest tests/test_f052_clasificar.py -q`:
```
    from application.services.sincronizacion import (
E   ModuleNotFoundError: No module named 'application.services.sincronizacion'
ERROR tests/test_f052_clasificar.py
1 error in 0.48s
```
Verde: `83 passed` (el borde 8,005 se cambió a 8,004/7,996: 8,005 − 8 en coma flotante es
0,0050000000000008 > 0,005; la regla `> TOLERANCIA_HORAS` es la de F-024 y no cambia).

**T6 (sv4, R7, R12)** — `pytest tests/test_f052_repositorio.py -q`:
```
E       AttributeError: 'ParteReviewRepository' object has no attribute 'lineas_para_sincronizar'   (7)
E       AttributeError: 'ParteReviewRepository' object has no attribute 'donde_estan'               (2)
9 failed in 4.22s
```
Verde: `9 passed in 1.92s`.

**T7 (sv4, R7, R10, R12, R13, R15, R29, R30, DA18)** — `pytest tests/test_f052_sincronizar_ambito.py -q`
(con el módulo apartado) y `pytest tests/test_f052_endpoints.py -q`:
```
E   ModuleNotFoundError: No module named 'application.services.sincronizar_ambito'
ERROR tests/test_f052_sincronizar_ambito.py
1 error in 1.15s
---
E       assert 404 == 200 / assert 404 == 422                                     (11)
E                   AttributeError: 'Settings' object has no attribute 'sincronizar_seco'   (4)
E       Failed: DID NOT RAISE ValidationError                                        (4)
E       AttributeError: 'TransferClient' object has no attribute 'sincronizar_leer'    (2)
18 failed, 1 warning in 9.80s
```
Verde: `52 passed` y `18 passed` (`70 passed` juntos).

## Verificación (resultado real)

`bash harness/init.sh` (árbol final, aab3c59): **ENTORNO LISTO**; raíz 537 passed, 3 skipped; sv4
3469 passed, 1 skipped (1450 s); sv5 1614 passed (31 s, T4; la caché del portero lo da en verde);
`git diff dev --stat -- services/partes-transfer/application` vacío (R26); guardián F-038 (raíz)
24 passed. Lo MANUAL pendiente: M2 (abajo).

## M2 · PUNTO DE CONTROL (T8)

**Hecha por el líder el 2026-11-03, NO superada** solo por H-M2-1 (abajo): recuentos y los 11
ítems contrastados en `progress/m2_F-052.md`. Procedimiento completo (candidatas, base `partes` en
solo lectura con `PGOPTIONS`, `.env` de la rama, sv5 en 8005, qué mirar): `git show
f232303:progress/impl_F-052.md`. Para repetirla, sv4 y las llamadas:

3. **sv4** (consola 2, puerto 8014; las variables de la consola mandan sobre el `.env`):
   ```powershell
   cd C:\Users\pgris\PycharmProjects\partes-wt-f052\services\partes-front
   $env:SINCRONIZAR_SECO = "true"                              # DA18 (es el defecto; explícito)
   $env:PGOPTIONS = "-c default_transaction_read_only=on"      # PostgreSQL: sesión de solo lectura
   $env:AUTO_CREATE_DATABASE = "false"
   $env:TRANSFER_BASE_URL = "http://127.0.0.1:8005"
   # Solo si se usa la base de Azure: PG_HOST, PG_USER y PG_PASSWORD de la base `partes` de
   # producción, con el mismo método de siempre (no van en ningún fichero del repo).
   C:\Users\pgris\PycharmProjects\partes\.venv\Scripts\python.exe main.py
   ```
   En el log de arranque debe salir `[sincronizar][wiring] CABLEADO seco=True timeout_s=150.0`.
   **No abrir el portal en el navegador** durante M2: la vista de obra/persona dispara la
   comprobación de F-024 (que sí escribe; con `PGOPTIONS` fallaría sin efecto).
4. **Llamadas** (consola 3; una por ámbito; tardan unos segundos):
   ```powershell
   function Sync($ambito, $nombre) {
     $b = @{ ambito = $ambito } | ConvertTo-Json -Depth 5
     $r = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8014/api/sincronizar `
          -ContentType "application/json; charset=utf-8" -Body $b -TimeoutSec 200
     $r | ConvertTo-Json -Depth 8 | Out-File -Encoding utf8 "$env:TEMP\m2_$nombre.json"
     "{0}: seco={1} total={2} a_cero={3} marcaria_borrado_sigrid={4}" -f $nombre, $r.seco, `
       $r.recuento.total, $r.recuento.a_cero, ($r.marcaria_borrado_sigrid -join ",")
     $r.recuento.por_clase
   }
   Sync @{ vista = "obra"; obra_key = "obr-2313811"; period = "2026-10"; mode = "natural" } "obra_0686"
   Sync @{ vista = "obra"; obra_key = "obr-2607369"; period = "2026-10"; mode = "natural" } "obra_0711"
   Sync @{ vista = "trabajador"; worker_key = "rec-2778601"; period = "2026-10"; mode = "natural" } "rec_2778601"
   Sync @{ vista = "trabajador"; worker_key = "rec-2138746"; period = "2026-10"; mode = "natural" } "rec_2138746"
   ```
   Un error sale como excepción de `Invoke-RestMethod` con el JSON `{ok:false, error}`: 422 (clave
   que no lee Sigrid), 409 (ya en curso, o «Sigrid o el portal cambiaron mientras se leía»: repetir),
   502 (sv5/sigrid-api).

## H-M2-1 · clase de hora por el prefijo `HE` (corrección tras M2)

Autorizado por el humano el 2026-11-03 («si, dale»). **Causa**: `comparar` decidía «extra» en
Sigrid con `hora_ext` (`auxhor.ext`), que vale 0 en las 7 `HE*`: 152 de 166 `distinta` falsas.
**Cambio** (`services/partes-front/application/services/sincronizacion.py`): `es_hora_extra(codigo)`
⇒ `True` si el código (sin espacios, en mayúsculas) empieza por `HE`, `None` sin código (no se
compara la clase, como antes con `hora_ext` nulo). Misma regla que sv5 (`HoraRecurso.es_extra`,
`franquicia._es_extra`) y sv4 (`fetch_dnis_sin_extra`, `franquicia.extras_pendientes`); ninguno es
un helper importable de sv4 para este módulo puro (los de sv4 van en SQL o inline), así que va en
`sincronizacion.py`, sin importar nada de sv5 (límite de servicio).
- **Contrato**: `hora_ext` se queda en la respuesta de sv5 y en `LineaSigridSync` (R2; anotado
  como informativo): quitarlo tocaría sv5, sus tests y R2 sin necesidad.
- **Lado del portal**: sin cambio. `LineaPortal.extra = _is_extra(r)` (`tipo_hora == "extra"` o
  `hora_ext == 1`): `tipo_hora` es lo que sv5 usa para elegir `HE`/`HL` (`reglas_registro`), y la
  rama `hora_ext == 1` no la activa ninguna `HE*`.
- **Otros usos en la diff de F-052**: sv5 solo lee y pasa `auxhor.ext AS hora_ext`
  (`sigrid_write_client.py`), sin decidir nada; sv4 `sincronizar_ambito.lineas_de_sv5` solo lo
  convierte. No hay más criterios con `ext`.
- **Hallazgo fuera de alcance (H-M2-1b, previo a F-052)**: al elegir hora en el selector del
  portal, `set_registro_hora` (`parte_repository.py:3021`) y la respuesta de
  `PATCH /api/registros/{id}/hora` (`web/app.py:3815`) ponen `tipo_hora` con `option.ext == 1`:
  elegir una `HE*` deja la línea `normal` y sv5 escribiría una `HL`. No se toca aquí (no es de
  F-052); se propone al líder como feature aparte.
- Tests: 6 nuevos y 2 ajustados en `tests/test_f052_clasificar.py` (el 503 lleva `HE01`; «sin
  clase» pasa a `hora_cod` nulo/vacío). Spec: R9, design §10 (H-M2-1) y T8 bis en `tasks.md`.

**RED** — `pytest tests/test_f052_clasificar.py -q -k "h_m2_1" --tb=line` (sv4, código sin tocar):
```
tests	est_f052_clasificar.py:249: AssertionError: assert [Diferencia(c...='ordinaria')] == []
E   AssertionError: assert 'igual' == 'distinta'
tests	est_f052_clasificar.py:255: AssertionError: assert 'igual' == 'distinta'
FAILED tests/test_f052_clasificar.py::test_f052_h_m2_1_hecap_con_ext_cero_es_extra
FAILED tests/test_f052_clasificar.py::test_f052_h_m2_1_ext_uno_en_una_hl_no_la_hace_extra
FAILED tests/test_f052_clasificar.py::test_f052_h_m2_1_prefijo_sin_mayusculas_ni_espacios[HECAP]
FAILED tests/test_f052_clasificar.py::test_f052_h_m2_1_prefijo_sin_mayusculas_ni_espacios[ hecap]
FAILED tests/test_f052_clasificar.py::test_f052_h_m2_1_prefijo_sin_mayusculas_ni_espacios[he01]
FAILED tests/test_f052_clasificar.py::test_f052_h_m2_1_cambio_real_de_clase_sigue_saliendo
6 failed, 1 passed, 83 deselected in 0.14s
```
El que pasa (`hlof_con_ext_cero_es_ordinaria`) es guarda. Verde: `test_f052_*` de sv4 `169 passed
in 7.14s`; ruff sin avisos nuevos. `bash harness/init.sh` (árbol con H-M2-1): **ENTORNO LISTO**.

## Fuera de alcance y pendiente

- T9–T17 (acciones, `/api/sincronizar/aplicar`, botón y panel, motivos, `ARCHITECTURE.md`): **no
  se empiezan sin M2 anotada y la autorización del humano**. Mutación: la lanza el líder.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests F-052 | sv5 60 passed (6,3 s); sv4 169 passed (7,1 s; 162 antes de H-M2-1) |
| Suites completas (init.sh, H-M2-1) | sv4 3476 passed, 1 skipped (974 s con cobertura); raíz 537 passed, 3 skipped (116 s); sv5 1614 (caché: sin cambios) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 99.8% de 509 líneas cambiadas cubiertas (508/509, umbral 80%, nivel critico)` |
| Mutantes | no lanzada: la campaña la lanza el líder (`python -m harness.mutacion --feature F-052`) |
