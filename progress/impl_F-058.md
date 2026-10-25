<!-- progress/impl_F-058.md -->
# F-058 · Informe del implementer — relectura de la cabecera con Gemini y prompt de cabecera (sv2)

Rama `feature/F-058-relectura-cabecera-gemini` (worktree `partes-wt-f058`), rigor `estandar`,
spec aprobada entera (DA1 enmendada, DA2–DA8 = A, DA9 = A, DA10 = B, DA11 = A, DA12 = A).
Solo sv2 (`services/partes-api`). Antes de T1 se hizo `git merge dev` (9b1a7e3, commit b9de23c;
conflictos solo en `BACKLOG.md` y `progress/current.md`, resueltos con lo de `dev`).

## Qué cambió

- **Prompt** (`config/prompts.yaml`, solo el punto 1 de `task`): párrafo de cabecera de
  `design.md` §5 (toda página tiene cabecera sobre «PERSONAL»; obra, día, mes, año, membrete;
  buscarla aunque el escaneo salga desplazado; cabecera entera a null con trabajadores = no
  localizada; nunca inventar) y la frase de fecha en casillas separadas (`dia/mes/año`).
- **Reglas puras** `application/services/relectura_cabecera.py`: `es_vacio`, `clave_obra`,
  `cabecera_vacia`, `con_trabajadores`, `obra_de`, `motivo_relectura`, `resultado_relectura`.
- **Consulta de obra en el momento** (DA10 = B): puerto `domain/ports/existencia_obra_port.py`;
  `application/services/obra_sigrid.py` (`ComprobadorObra`, `ConsultaObra`: sin caché, reloj
  monotónico, nunca lanza, INFO/WARNING `[obra-sigrid] document_id=… resultado=… ms=…` sin
  código); `SigridLookupClient.existe_obra` con `_SQL_EXISTE_OBRA` (`SELECT TOP 1`, un solo
  `?`), `timeout_s` por llamada en `_post_sql_read` y `transport` inyectable para tests.
- **Pipeline** (`extract_parte_pipeline.py`): `ExtractParteRequest.document_id` (R15),
  kwargs `relectura_provider` y `obras`, `existe` por página, `_releer_cabecera` (única captura
  amplia, R14), `_envelope` desde `data` con `meta/debug.relectura_cabecera` solo al releer.
  `ParteExtractionService.model_name`. `main_worker.py` pasa el `document_id` del mensaje.
- **Configuración y cableado**: `RELECTURA_CABECERA` (true), `RELECTURA_CABECERA_PROVIDER`
  (gemini), `OBRA_EXISTE_TIMEOUT_S` (5, > 0); propiedades `relectura_cabecera_activa` y
  `relectura_cabecera_motivo_inactiva`; helpers `_habilitado`/`_clave_de` reutilizados por el
  validador del primario con los mismos mensajes. `app.py`: `ComprobadorObra` con el mismo
  `SigridLookupClient` del catálogo, log de cableado ACTIVA/INACTIVA/DESACTIVADA y
  `/health.relectura_cabecera`.
- **Docs**: docstrings de sv2 (T12); `docs/ARCHITECTURE.md` punto **20** y «Acceso a datos»;
  comentario de sv2 en `infra/create_capps_partes.ps1` (ASCII, CRLF, sin BOM, solo comentarios);
  `azure-apps/partes.md` (diagrama, §3.2, §5.2 y fila sv2 de §5.6), commit local **7470cf2** en
  ese repositorio, sin push.

Ficheros de sv2 tocados: `config/prompts.yaml`, `config/settings.py`,
`application/pipelines/extract_parte_pipeline.py`, `application/services/{relectura_cabecera,
obra_sigrid,parte_extraction_service}.py`, `domain/ports/existencia_obra_port.py`,
`infrastructure/sigrid/sigrid_lookup_client.py`, `interface_adapters/api/app.py`,
`main_worker.py` y `tests/test_f058_{prompt,relectura_cabecera,obra_sigrid,settings_wiring}.py`.
R27: `git diff 9b1a7e3 -- services/` solo toca `services/partes-api`; `parte_models.py`,
`orm_models.py`, `infrastructure/llm/*` y `auxhor_catalog_provider.py` sin cambios.

## Decisiones de diseño y desviaciones (justificadas también en `progress/current.md`)

1. **`existe_obra` pide el `max_rows` del cliente, no 2** (`design.md` §4.3 decía `max_rows=2`):
   F-038 (llegó a `dev` después de la spec) prohíbe en todo lector un `max_rows` literal por
   debajo del tope (R13, guardián `tests/test_f038_lectores_sigrid.py`) y `ARCHITECTURE.md` fija
   que toda lectura pide `SIGRID_API_MAX_ROWS`. Con `SELECT TOP 1` el resultado es el mismo.
   El test de §8 «`max_rows` 2» pasa a «`max_rows` = el del cliente» + `TOP 1` en el SQL.
2. **Sin `exigir_completo`**: desde F-038 `_post_sql_read` trata `truncated: true` como error en
   toda lectura; es lo que R9 pide para la de obra (test `truncated` ⇒ `RuntimeError`).
3. **F-059 (página como imagen)**: la relectura pasa por `_preparar_para_ia` con SU proveedor
   (el método recibe ahora `provider`). Con `PAGINA_COMO_IMAGEN_PROVEEDORES=openai` (hoy) Gemini
   recibe el PDF original, como en la medición 6/6 de la spec; si Gemini estuviera en la lista,
   recibiría la imagen. `meta.adjunto_ia` sigue siendo de la primaria (R16 fija las claves);
   lo enviado en la relectura queda en `debug.relectura_cabecera.<proveedor>_request`.
4. `model_name` del proveedor de relectura no instanciado (`KeyError`) = fallo de la relectura
   (`resultado=error`, `model` null), no tumba la extracción (R14). En producción no ocurre: el
   cableado solo activa un proveedor habilitado.
5. `consulta_obra_ms` apunta solo consultas hechas: con clave vacía (p. ej. `" - "`) no se llama
   a sigrid-api ni se apunta nada (`ComprobadorObra` devuelve «no se sabe» sin log).
6. `ARCHITECTURE.md`: el punto es el **20** (el 18 es F-054 y el 19, F-059; la spec decía 18).
7. R15 (worker) quedó implementado en T9 como dice `tasks.md`; su test (T10) ya pasaba en RED.

## Fase RED (trazas reales, `cd services/partes-api && python -m pytest <fichero> -q`)

**T1** `python -m pytest tests/test_f058_prompt.py -q` (antes del cambio del prompt):
```
>       assert "casillas separadas" in vineta_fecha
E       assert 'casillas separadas' in 'la fecha manuscrita del parte, copiada tal cual como aparece (dd/mm/aaaa, dd/mm/aa, o con el mes en letra como "6-abril-26"). no la conviertas; si es ilegible, null.'
FAILED tests/test_f058_prompt.py::test_f058_r21_el_parrafo_va_antes_de_la_vineta_de_fecha
FAILED tests/test_f058_prompt.py::test_f058_r21_toda_pagina_tiene_cabecera_sobre_la_tabla_personal
FAILED tests/test_f058_prompt.py::test_f058_r21_buscarla_aunque_el_escaneo_salga_desplazado
FAILED tests/test_f058_prompt.py::test_f058_r21_cabecera_entera_a_null_con_trabajadores
FAILED tests/test_f058_prompt.py::test_f058_r21_nunca_inventes_un_valor - Ass...
FAILED tests/test_f058_prompt.py::test_f058_r22_la_fecha_en_casillas_separadas_se_copia_junta
11 failed, 1 passed in 0.65s
```
Tras T2: `python -m pytest tests/test_f058_prompt.py tests/test_f023_empresa_membrete.py
tests/test_f051_prompt.py -q` ⇒ `32 passed in 1.88s`.

**T4** `python -m pytest tests/test_f058_relectura_cabecera.py -q`:
```
E   ModuleNotFoundError: No module named 'application.services.relectura_cabecera'
ERROR tests/test_f058_relectura_cabecera.py
1 error in 0.53s
```
Tras T5: `53 passed in 0.28s`.

**T6** `python -m pytest tests/test_f058_obra_sigrid.py -q` (sin módulo; y con `ComprobadorObra`
ya escrito y el cliente sin tocar):
```
E   ModuleNotFoundError: No module named 'application.services.obra_sigrid'
1 error in 1.23s
---
E       TypeError: SigridLookupClient.__init__() got an unexpected keyword argument 'transport'
FAILED tests/test_f058_obra_sigrid.py::test_f058_r7_existe_obra_parametrizada
FAILED tests/test_f058_obra_sigrid.py::test_f058_r9_existe_obra_truncada_es_error
FAILED tests/test_f058_obra_sigrid.py::test_f058_r9_existe_obra_usa_el_tope_del_argumento[0.3-1]
14 failed, 15 passed in 0.77s
```
Tras T7: `29 passed in 0.43s`; guardián F-038 `python -m pytest tests/test_f038_lectores_sigrid.py`
(raíz) ⇒ `24 passed`.

**T8** `python -m pytest tests/test_f058_relectura_cabecera.py -q` (pipeline sin relectura):
```
E       TypeError: ExtractPartePipeline.__init__() got an unexpected keyword argument 'relectura_provider'
tests\test_f058_relectura_cabecera.py:370: TypeError
FAILED tests/test_f058_relectura_cabecera.py::test_f058_r1_cabecera_vacia_relee_una_vez_con_el_mismo_prompt
FAILED tests/test_f058_relectura_cabecera.py::test_f058_r12_toma_la_cabecera_entera_y_firma_y_empleados_primarios
FAILED tests/test_f058_relectura_cabecera.py::test_f058_r14_el_data_resultante_valida_contra_el_esquema
36 failed, 53 passed in 4.33s
```
Tras T9: `89 passed in 2.10s`.

**T10** `python -m pytest tests/test_f058_settings_wiring.py -q`:
```
E                   AttributeError: 'Settings' object has no attribute 'relectura_cabecera_enabled'
E       Failed: DID NOT RAISE ValidationError
23 failed, 6 passed, 1 warning in 7.50s
```
(Los 6 en verde: los 4 del validador del primario sin cambios, el de secretos en el log y R15
del worker, ya implementado en T9.) Tras T11: `29 passed, 1 warning in 5.62s`.

## Resultado de los tests y del portero

- Suite de sv2: `cd services/partes-api && python -m pytest -q` ⇒ **329 passed, 1 warning
  in 13.45s** (170 antes de F-058; 159 tests nuevos de F-058).
- `bash harness/init.sh` (final, sin pipes): **ENTORNO LISTO** (exit 0). Raíz: `522 passed, 3 skipped in 127.18s`; sv2: `329 passed, 1 warning in 48.09s`; sv1, sv3, sv4 y sv5 en verde (caché de árbol sin cambios); `PUERTA COBERTURA: 100.0% de 214 líneas cambiadas cubiertas (214/214, umbral 80%, nivel estandar)`; `PUERTA TAMAÑO: F-058 dentro de los topes (requirements 150/150, design 250/250)`. Avisos previos: ruff 798 (deuda, no bloquea), F-032 `blocked`, infra sin tests, `BACKLOG.md` regenerado (incluido en el commit).

## Verificaciones MANUAL pendientes (comandos exactos en `progress/current.md`, F-058)

- **T3 · MB** (líder): banco del prompt sobre c67c253; puerta DA9 en (b)–(d).
- **T16 · mutación** (líder): `python -m harness.mutacion --feature F-058`; NO lanzada.
- **T17 · M0**, **T18 · M1** (script incluido, entorno con los SDK de IA), **T19 · M2** (SQL en
  transacción READ ONLY), **T20 · M4** (KQL de tiempos y relecturas) y **T21 · M3** (portal).

## Fuera del alcance y avisos

- No se cambió el modelo primario, no se relee por otras causas, no se cae a Gemini si falla la
  primaria, no se reprocesa nada (DA8), sv2 no casa obra ni empresa (R11).
- `dev` avanzó a **776f923** después del merge (solo `progress/`, `BACKLOG.md`,
  `features.json`): entre ello **«F-059: M4 OK (6 partes reprocesados, convertida, obra y fecha
  leídas)»**. Con F-059 desplegada, la primaria ya lee esas 6 páginas: la relectura queda como
  red. El líder decide si vuelve a mezclar `dev` antes del review (no hay código nuevo).
- `azure-apps/sigrid_api.md` no se tocó (es de sigrid-api): conviene avisar a su dueño de que
  partes/sv2 hace una lectura más por página (`obr ⨝ con`, sin índice usable por la clave).
- Riesgo medido solo en M4: carga de la consulta por página sobre sigrid-api y Sigrid, y que
  sigrid-api acepte `CROSS APPLY` y `COLLATE` (si no, `[obra-sigrid] resultado=error` y la
  extracción sigue).

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (sv2) | 329 passed, 0 failed (159 de F-058) |
| Tiempo de la suite de sv2 | 13.45 s (pytest); en `init.sh`: 48.09 s |
| Cobertura de líneas cambiadas | **100.0 %** (214/214 líneas cambiadas, umbral 80 %; `PUERTA COBERTURA` de `init.sh`) |
| Cobertura de los ficheros tocados (coverage local de sv2) | `relectura_cabecera.py` 100 %, `obra_sigrid.py` 100 %, `settings.py` 100 %, `extract_parte_pipeline.py` 99 %, `sigrid_lookup_client.py` 89 %, `app.py` 80 % (lo no cubierto es previo: endpoint `/v1/partes/extract` y CORS) |
| Mutantes generados / supervivientes | No lanzada por el implementer (T16, la lanza el líder): pendiente de `progress/mutacion_F-058.md` |
