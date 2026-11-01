<!-- progress/impl_F-038.md -->
# F-038 · Informe del implementer

> Rama `feature/F-038-limite-filas-sigrid` (worktree `partes-wt-f038`), desde 825a441.
> Rigor `estandar`. Aprobación del humano (2026-10-24): DA1 = B (**500.000**), DA2–DA7 = A.
> Commits: 258bd8e (T1), fd95dba (T6), 7963211 (T2), f458e32 (T3), dc62da7 (T4),
> 5810d8b (T5), fe93a33 (T7), db01cc6 (T8). azure-apps: c581115 (local, sin push).

## Qué cambió

| Servicio | Antes | Ahora |
|---|---|---|
| sv5 | `_read` con `max_rows` **1.000 fijo** (un parte grande hacía fallar el registro) | `max_rows` del cliente = `SIGRID_API_MAX_ROWS` (500.000 por defecto) en toda lectura |
| sv2 | 10.000 fijo y **sin mirar `truncated`** (catálogo `auxhor` truncable en silencio) | `SIGRID_API_MAX_ROWS` nuevo; `truncated` ⇒ `RuntimeError` «truncada [tipos_hora]», que el proveedor del catálogo absorbe (caché o vacío + WARNING) |
| sv3 | `SIGRID_API_MAX_ROWS` 10.000 (sin uso: todo pagina) | 500.000; las paginadas siguen pidiendo 5.001 |
| sv4 | 10.000 fijo en `fetch_dnis_sin_extra` y `fetch_hora_extra_recurso` | `SIGRID_API_MAX_ROWS` nuevo (500.000), cableado en `build_app` |
| Scripts | `prueba_escritura_sigrid.py` 1.000 y sin `truncated`; `consulta_reshor_recursos.py` 10.000, sin `truncated` y con DNIs y nombres reales | el primero pide `MAX_ROWS = 500_000` y sale con `SystemExit` «truncada»; el segundo, **borrado** (DA6; el historial no se purga) |

Además, en los cuatro: `SIGRID_API_MAX_ROWS` opcional con rango 1–500.000 y
`SIGRID_API_TIMEOUT_S` en (0, 200] (fuera de rango el servicio no arranca;
defectos sin cambio: 30, 30, 30 y 60); `MAX_ROWS_DEFECTO = 500_000` en cada
cliente, igual que el defecto de settings; log INFO de instanciación con
`timeout_s` y `max_rows`, sin la clave (sv3 ya lo tenía).

## Ficheros tocados

- **sv5** `services/partes-transfer/`: `config/settings.py`,
  `infrastructure/sigrid/sigrid_write_client.py`, `interface_adapters/api/app.py`,
  `main.py`, `comprobar_asiento_analitico.py`, `prueba_escritura_sigrid.py`;
  tests: `test_f038_sigrid_limite.py` (nuevo), enmiendas en `test_f024_comprobacion.py`,
  `test_f031_comprobar_asiento.py`, `test_f046_api_reajuste.py`.
- **sv2** `services/partes-api/`: `config/settings.py`,
  `infrastructure/sigrid/sigrid_lookup_client.py`, `interface_adapters/api/app.py`;
  `tests/test_f038_sigrid_limite.py` (nuevo).
- **sv3** `services/partes-persistencia/`: `config/settings.py`,
  `infrastructure/sigrid/sigrid_api_client.py`; `tests/test_f038_sigrid_limite.py` (nuevo).
- **sv4** `services/partes-front/`: `config/settings.py`,
  `infrastructure/sigrid/sigrid_lookup_client.py`, `interface_adapters/web/app.py`;
  `tests/test_f038_sigrid_limite.py` (nuevo), enmienda en `test_f023_catalogo_empresa.py`;
  **borrado** `consulta_reshor_recursos.py`.
- **Raíz**: `tests/test_f038_lectores_sigrid.py` (guardián), `docs/ARCHITECTURE.md`,
  `BACKLOG.md` (regenerado por `init.sh`), `progress/current.md`, `tasks.md`.
- **azure-apps** `partes.md`: §3.3 (lecturas no paginadas) y §5.6 (filas sv2–sv5).

## Choque con F-060 (líneas de los ficheros compartidos, diff contra 825a441)

- sv5 `config/settings.py`: solo la l.22 (`sigrid_api_timeout_s`) pasa a ser
  l.22–29 (comentario, rango y el campo nuevo `sigrid_api_max_rows`), en el
  bloque «sigrid-api». F-060 añade `MOVER_CIZ` hacia la l.42: trozos distintos.
- sv5 `sigrid_write_client.py`: +l.69–72 (`MAX_ROWS_DEFECTO`, tras
  `LOTE_COMPROBACION`), +l.98 (parámetro `max_rows` de `__init__`), +l.108–111
  (`self._max_rows` y el `logger.info`), l.121 (`"max_rows": self._max_rows` en
  `_read`). **No** se toca el docstring de cabecera (F-060 lo amplía hacia la
  l.37) ni ninguna lectura o sentencia (F-060 añade en l.441+ y l.602+).
- sv5 `interface_adapters/api/app.py`: +l.132 (`max_rows=` en `_cliente_sigrid`);
  F-060 toca `LineaIn`, en otro sitio.
- azure-apps `partes.md` §5.6 fila sv5: F-060 ya estaba commiteado allí
  (c914caa); F-038 añade su frase **al final** de la fila, tras la de
  `MOVER_CIZ`, sin conflicto (mismo repositorio, una sola rama).
- `lineas_de_racha` de F-060 lee por `_read`: hereda el límite y el guardián.

## Decisiones de diseño y desviaciones (justificadas)

1. **Umbral del guardián R13 = 500.000**, no el 200.000 que escribe la spec: la
   aprobación dice «donde la spec dice 200.000 como valor por defecto, léase
   500.000» y el umbral de R13 es ese defecto («ningún límite por debajo del
   acordado»). Con 200.000 un literal de 300.000 pasaría sin ser el acordado.
2. **Orden de tareas**: T1 → **T6** → T2 → T3 → T4 → T5 → T7 → T8, por la
   prioridad expresa del líder (sv5 primero). Cada commit lleva su `Tn`.
3. **Enmiendas de dobles de settings** en tres tests de sv5 (f024, f031, f046):
   simulan `Settings` campo a campo y el cableado ahora lee
   `sigrid_api_max_rows`. Se añade el campo en cada test; `tests/dobles.py` NO
   se toca (design §5). Alternativa descartada: `getattr(settings, ..., defecto)`
   en producción para complacer a los dobles.
4. **R10 con test real** (no solo guardián): `prueba_escritura_sigrid.py` se
   importa con su `.env` sustituido en memoria (`mock.patch.object` de
   `Path.exists`/`read_text` solo para esa ruta) y `httpx.post` falso.
5. **R6 en sv5**: el log va con prefijo `[sigrid-write] Instanciado.` y sin
   `base_url` (sv5 no lo registraba); en sv2/sv4 se amplía el log que ya había.
6. Los textos de `tasks.md` T11 (`max_rows=200000`) y de la spec no se editan
   (son del spec-author); con DA1 = B el valor esperado en M2 es **500000**.

## Fase RED (trazas reales, salida de pytest resumida por tipo de error)

**T1** · `python -m pytest tests/test_f038_lectores_sigrid.py -q` (desde la raíz):
```
E       AssertionError: Lectores de Sigrid fuera de la lista cerrada: ['services/partes-front/consulta_reshor_recursos.py']; de la lista que ya no leen: []. ...
E       AssertionError: services/partes-api/infrastructure/sigrid/sigrid_lookup_client.py no comprueba `truncated` (falta `.get("truncated")`)
E       AssertionError: services/partes-transfer/prueba_escritura_sigrid.py no comprueba `truncated` (falta `.get("truncated")`)
E       AssertionError: services/partes-api/infrastructure/sigrid/sigrid_lookup_client.py: `max_rows` literal por debajo de 500000 en las líneas [55]
E       AssertionError: services/partes-front/infrastructure/sigrid/sigrid_lookup_client.py: `max_rows` literal por debajo de 500000 en las líneas [205]
E       AssertionError: services/partes-persistencia/infrastructure/sigrid/sigrid_api_client.py: `max_rows` literal por debajo de 500000 en las líneas [188]
E       AssertionError: services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py: `max_rows` literal por debajo de 500000 en las líneas [112]
E       AssertionError: services/partes-transfer/prueba_escritura_sigrid.py: `max_rows` literal por debajo de 500000 en las líneas [102]
8 failed, 16 passed in 2.97s
```
(la l.112 de sv5 es el `"max_rows": 1000` fijo de `_read`). Tras T7: `24 passed`.

**T6 (sv5)** · `cd services/partes-transfer && python -m pytest tests/test_f038_sigrid_limite.py -q`:
```
     17 E       TypeError: SigridWriteClient.__init__() got an unexpected keyword argument 'max_rows'
      8 E       Failed: DID NOT RAISE ValidationError
      3 E       KeyError: 'max_rows'
      2 E                   AttributeError: 'Settings' object has no attribute 'sigrid_api_max_rows'
      1 E       AttributeError: module 'infrastructure.sigrid.sigrid_write_client' has no attribute 'MAX_ROWS_DEFECTO'
32 failed, 8 passed in 7.54s
```
Tras el código: `40 passed`; la suite de sv5 entera, `895 passed`.

**T2 (sv2)** · `cd services/partes-api && python -m pytest tests/test_f038_sigrid_limite.py -q`:
```
      8 E       Failed: DID NOT RAISE ValidationError
      2 E                   AttributeError: 'Settings' object has no attribute 'sigrid_api_max_rows'
      1 E       KeyError: 'max_rows'
      1 E       Failed: DID NOT RAISE RuntimeError          <- R7: truncated devolvía filas
      1 E       AttributeError: module 'infrastructure.sigrid.sigrid_lookup_client' has no attribute 'MAX_ROWS_DEFECTO'
      1 E       AssertionError: ['[sigrid-lookup] Instanciado. base_url=http://sigrid.invalid database=bd']
      1 E       AssertionError: assert 'CATALOGO DE ...- Hora normal' == ''   <- R8: el catálogo truncado se usaba
15 failed, 5 passed in 8.74s
```
Tras T3: suite de sv2 `168 passed`.

**T4 (sv3)** · `cd services/partes-persistencia && python -m pytest tests/test_f038_sigrid_limite.py -q`:
```
      6 E       Failed: DID NOT RAISE ValidationError
      1 E       AttributeError: module 'infrastructure.sigrid.sigrid_api_client' has no attribute 'MAX_ROWS_DEFECTO'
7 failed, 26 passed in 5.91s
```
(R4, R5, R6 y R9 ya se cumplían en sv3: pasan en rojo y quedan fijados). Tras el código: suite `2338 passed`.

**T5 (sv4)** · `cd services/partes-front && python -m pytest tests/test_f038_sigrid_limite.py -q`:
```
      8 E       Failed: DID NOT RAISE ValidationError
      2 E                   AttributeError: 'Settings' object has no attribute 'sigrid_api_max_rows'
      1 E       KeyError: 'max_rows'
      1 E       AttributeError: module 'infrastructure.sigrid.sigrid_lookup_client' has no attribute 'MAX_ROWS_DEFECTO'
      1 E       AssertionError: ['[sigrid-lookup] Instanciado. base_url=http://sigrid.invalid database=bd']
13 failed, 11 passed in 4.98s
```
Tras el código: suite de sv4 `2607 passed, 1 skipped` (612 s).

**T7 (R10)** · `cd services/partes-transfer && python -m pytest tests/test_f038_sigrid_limite.py -q -k r10`:
```
E       Failed: DID NOT RAISE SystemExit
1 failed, 1 passed, 40 deselected in 5.13s
```
Tras el código: `42 passed`.

## Verificaciones MANUAL pendientes (solo lectura; ninguna lanzada por el implementer)

- **M0** (antes de desplegar): comando exacto por app en `progress/current.md`.
  Riesgo que cubre: un `SIGRID_API_TIMEOUT_S` > 200 o un `SIGRID_API_MAX_ROWS`
  fuera de rango en Azure haría que ese servicio NO arrancara tras desplegar.
- **M1** (no bloquea) y **M2** (tras desplegar sv2–sv5; esperado
  `max_rows=500000` en el log de arranque de sv4 y sv5): `design.md` §9.
- **T9 · mutación**: hecha (ver Evidencias y `progress/mutacion_F-038.md`).

## Fuera de alcance (sin cambios)

- Trocear las lecturas `IN (...)` sin lote de sv5 (límite de ~2.100 parámetros de SQL Server, DA7).
- `PAGINA_FILAS` y `_leer_paginado` de sv3/sv4 (DA5); `infra/` y manifiestos (DA2).
- Purgar del historial de git los datos personales del script borrado.

## Evidencias

Números medidos con `bash harness/init.sh` (ejecución completa sobre db01cc6, «ENTORNO LISTO»):

| Evidencia | Valor real |
|---|---|
| Tests nuevos de F-038 | **143**: raíz 24, sv2 20, sv3 33, sv4 24, sv5 42 (todos verdes) |
| Suite raíz | 522 passed, 3 skipped · 139,15 s |
| sv2 | 168 passed · 47,44 s |
| sv3 | 2338 passed · 47,63 s |
| sv4 | 2607 passed, 1 skipped · 1051,88 s (máquina cargada; suelta, 612 s) |
| sv5 | 897 passed · 30,93 s |
| sv1 | sin cambios (caché de verde del arnés) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 19 líneas cambiadas cubiertas (19/19, umbral 80%, nivel estandar)` |
| Tamaño | `PUERTA TAMAÑO: ... impl 166/220` |
| Mutantes | campaña del líder (estándar, 20 de 26, semilla 20260820, workers: 1): **26 generados, 20 evaluados, 17 muertos, 3 supervivientes** (`gt=0`→`gt=1` del timeout en sv3/sv4/sv5); los 3 mueren con el test añadido, verificado a mano (`progress/mutacion_F-038.md`) |

Tras ese `init.sh`, `ruff` contaba 9 avisos nuevos en los tests de F-038 (orden de imports,
`noqa` sobrantes y un `ClassVar`); corregidos en el commit de cierre (solo tests, sin
cambio de producción), las cinco baterías de F-038 vuelven a dar 24/20/33/24/42 passed y
se relanzó `bash harness/init.sh` completo: resultado en la línea siguiente.

**`bash harness/init.sh` final (sobre 29f71d8): «ENTORNO LISTO. Puedes trabajar.»** — raíz 522
passed, 3 skipped (197,98 s); sv2 168 (54,31 s); sv3 2338 (71,01 s); sv4 2607 passed, 1 skipped
(1021,49 s); sv5 897 (25,18 s); cobertura 100,0 % (19/19); tamaño impl 186/220; ruff 772 avisos
(los mismos de antes de F-038: cero nuevos).

**Añadido tras la mutación (2026-10-24):** test `test_f038_r14_timeout_por_debajo_de_1_vale` (0.5 y 1) en sv2–sv5, que mata los 3 supervivientes `gt=0`→`gt=1` (verificado a mano). `bash harness/init.sh`: «ENTORNO LISTO» — raíz 522 passed, 3 skipped; sv2 170; sv3 2340; sv4 2609 passed, 1 skipped (1367 s); sv5 899; cobertura 100,0 % (19/19); ruff 772 (sin nuevos).
