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

PEGAR_VERIF

## M2 · PUNTO DE CONTROL (T8) — lista para ejecutar

**Ninguna escritura en Sigrid** (sv5 solo usa `/api/sql/read` en esta ruta) **ni en `partes`**
(sv4 en seco). Lo ejecuta el humano; los agentes no lanzan servicios contra producción.

**Candidatas** (implementer, 2026-11-03, solo lectura: agregados `GROUP BY` sobre `hmores` de
`ruesma` vía sigrid-api con el cliente de sv5, sin nombres; script en el scratchpad de la sesión).
Octubre de 2026, natural:

| Ámbito | Clave | Líneas Sigrid | `partes:` | manuales | a 0 |
|---|---|---|---|---|---|
| Obra 0686 | `obr-2313811` | 168 | 111 | 57 | 18 |
| Obra 0711 | `obr-2607369` | 107 | 93 | 14 | 4 |
| Persona (3 obras) | `rec-2778601` | 44 | 16 | — | — |
| Persona (2 obras) | `rec-2138746` | 15 | 13 | — | — |

Opcional (nómina 10/2026, 16/09–15/10): obra 0678 `obr-2348888` (175 líneas, 83 `partes:`, 92
manuales); el código 0678 existe en dos empresas (también `obr-2245328`): sirve para ver que la
clave va por `obra_ide`. Lecturas de 4–11 s por agregado.

**Requisito previo — la base `partes` de sv4.** Las synckeys `partes:<id>` son ids de la base de
**producción**; el `.env` local apunta a `localhost/partes`: si no es copia reciente, no casarán.
Recomendado: sv4 local contra la base `partes` de Azure en **sesión de solo lectura** de PostgreSQL
(`PGOPTIONS`) además del seco. Así el DDL de `initialize()` falla, se registra y el portal arranca
igual (lo captura `initialize`); sincronizar solo lee.

1. **`.env` de la rama** (no versionados; copia de los del repo principal, PowerShell):
   ```powershell
   Copy-Item C:\Users\pgris\PycharmProjects\partes\services\partes-transfer\.env C:\Users\pgris\PycharmProjects\partes-wt-f052\services\partes-transfer\.env
   Copy-Item C:\Users\pgris\PycharmProjects\partes\services\partes-front\.env C:\Users\pgris\PycharmProjects\partes-wt-f052\services\partes-front\.env
   ```
2. **sv5** (consola 1; sin `COLAS_*` en su `.env` solo arranca la API, puerto 8005):
   ```powershell
   cd C:\Users\pgris\PycharmProjects\partes-wt-f052\services\partes-transfer
   C:\Users\pgris\PycharmProjects\partes\.venv\Scripts\python.exe main.py
   ```
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
5. **Qué mirar** (M2 de design §9): `seco = True` en las cuatro; elegir 10 ítems de clases
   distintas en los JSON (`$env:TEMP\m2_*.json`: `clase`, `registro_id`, `hmores_ide`,
   `diferencias`, `notas`, `donde`) y contrastarlos a mano con Sigrid y con el portal (horas,
   clase de hora, partida, obra y fecha; `solo_sigrid_manual` = línea sin synckey;
   `borrada_en_sigrid` = está en `marcaria_borrado_sigrid` y no aparece en Sigrid). Si alguna
   clase no cuadra: **se para y se vuelve a proponer** (T8).
6. **Resultado**: anotarlo aquí (fecha, recuentos por ámbito, los 10 ítems y su veredicto) y en
   `progress/current.md`; sin eso no se empieza T9.

## Fuera de alcance y pendiente

- T9–T17 (acciones, `/api/sincronizar/aplicar`, botón y panel, motivos, `ARCHITECTURE.md`): **no
  se empiezan sin M2 anotada y la autorización del humano**. Mutación: la lanza el líder.

## Evidencias

PEGAR_EVID
