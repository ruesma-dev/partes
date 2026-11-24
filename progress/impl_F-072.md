# F-072 · Informe del implementer (`critico`)

Postventa y obras VAR como **entradas** de una obra agrupada (obra agrupada + una partida). Rama
`feature/F-072-postventa-var-como-obras`, un commit por tarea `F-072 Tn: …`. Hechas T1–T28, T32
y T33. **T29–T31 (manuales) quedan sin marcar**: son del humano.
El bloqueo de T16 se resolvió con la opción **(b)** del humano: reajuste y franquicia también
pasan la guarda y llevan la marca de la línea base (RED 6aef54d, código b66a749).

## Qué cambió

- **Gemelo** `application/services/obras_agrupadas.py`, byte-idéntico en sv2, sv3, sv4 y sv5.
  Contiene las reglas de porcentajes (postventa: código entero o seguido de letras, la más
  corta; VAR: hoja activa con número ≥ `VAR_PARTIDA_DESDE`), la lectura de la forma del papel y
  los ajustes. Los cuatro `config/settings.py` leen las variables (R1, R2; VAR sin umbral
  entero no arranca). Todo vacío = apagado.
- **sv2**: si `leer_forma` ve una marca, no consulta la obra (`obra_sigrid.py`, `app.py`); el
  prompt pide el «Nº OBRA» tal cual.
- **sv3**: `entrada_agrupada.py` (nuevo, `ResolutorEntradas`), `obra_matcher.py`,
  `parte_records.py`, `persist_parte_pipeline.py`, `sqlalchemy_parte_repository.py`,
  `partida_conciliador.py` y `app.py`. La entrada se casa solo desde `obra_numero_leido` y cada
  línea lleva la marca en `partida_match_method` (`postventa` | `var`), sin columnas nuevas.
- **sv5**:
  - `registro_models.py` gana `partida_metodo`, `PartidaHoja`, `LineaSigrid.paride` y
    `ContextoRegistro.agrupada`;
  - `sigrid_write_client.py` gana `partidas_de_obra` y `lineas_existentes(…, con_partida)`;
  - `reglas_registro.py` gana `motivo_partida_agrupada`;
  - `registro_pipeline.py`: paso 2d de la guarda (R36/R37, también en modo pruebas, por la obra
    pedida) y choques por partida (R38, `pisado.choques(…, por_partida)`);
  - `reajuste_pipeline.py`, `franquicia_pipeline.py` y `api/app.py` (`LineaIn`,
    `LineaReajusteIn`, `FranquiciaIn`) llevan `partida_metodo` (enmienda (b) y R33).
- **sv4**:
  - `catalogo_entradas.py` (nuevo, R25);
  - `parte_repository.py`: claves `agr-…` y `mixta-…`, rótulos `Postv-`/`VAR-`, partida fija
    (`PartidaFijaError`, 409), cambio de obra y alta manual con entrada, extra y celda que
    clonan la entrada, `partida_metodo` en las líneas a sv5;
  - `web/app.py`: `/api/sigrid/obras` (R26), `ObraPayload.partida_ide` y los 422 de R27/R28 en
    el cambio de obra y en `/api/partes/nuevo`;
  - `franquicia.py`, `reparto_aviso.py` y `app.py` mandan la marca de la línea base (b);
  - `sincronizar_ambito.py` (R34) y `static/app.js` (R35: los tres selectores mandan la
    `partida_ide` de la entrada).
- **Documentación** (T26): semántica 24 en `docs/ARCHITECTURE.md`, el gemelo en la lista
  cerrada de `CLAUDE.md`, las variables y el orden de encendido en `infra/README_partes.md`, y
  `depende_de` del gemelo en `harness/servicios.json`.
- **azure-apps** (T27): `partes.md` §3.3, §3.4, §3.5 (guarda, «qué se rompe» y nota a
  porcentajes), §4.5 bis y §5.6. Commit **cd58cab**, aparte; ya está en `origin/main` (lo
  subió el humano).

Tests nuevos: los `test_f072_*.py` de cada servicio y, en la raíz, `…_gemelos.py`,
`test_f072_equivalencia_porcentajes.py` y `test_f072_documentacion.py`.

## Decisiones e interpretaciones (para el reviewer)

- **(i)** Los alias solo se leen en sv2 y sv3 (design §5–§6), pese al R1 literal.
- **(ii)** El segundo paso de `casar_var` («la única con el mismo número inicial») solo se
  aplica si lo leído es solo un número: D1 (c) del humano, T33.
- **(iii)** En la forma base, un resultado mixto da `agrupada_varias_entradas`; varios fallos
  distintos, `agrupada_sin_entrada`.
- **(iv)** Desviación justificada: el reemplazo del mismo día de `save_parte` (sv3) cuenta
  también la entrada; si no, dos entradas del mismo día se pisarían.
- **(v)** `tests/test_f038_lectores_sigrid.py` lista ficheros, no métodos: `partidas_de_obra`
  vive en `sigrid_write_client.py`, ya listado. R39 se prueba en `test_f072_guarda.py`.
- **(vi)** `lineas_existentes` lee `hmores.paride` solo con `con_partida=True`. Leerlo siempre
  rompe `test_f053_cliente_anular.py::…sql_exacto`, que T25 prohíbe tocar.
- **(vii)** `partida_metodo` solo viaja cuando es una marca de entrada. Para sv5 es lo mismo y
  así los tests anteriores de payload exacto no cambian.
- **(viii)** `PeticionFranquicia` lleva la marca como atributo, no como campo: un campo nuevo
  rompe `test_f056_modelos_peticion_campos_y_defectos` (precedente: `ObraEntrada.cenide`).
- **(ix)** La fila de franquicia no guarda la marca: `fq.con_metodo_base` la recupera de una
  línea del periodo con el mismo recurso, obra y partida.
- **(x)** R31 «alta en celda» ya lo cubría `_CAMPOS_CLON_CELDA`; queda probado en
  `test_f072_repositorio.py`.
- **Observación** (reajuste sin `por_partida`): resuelta por D2 (a) en T33.

## Fase RED (trazas reales)

Cada comando es el de la columna «Verificación» de su tarea, lanzado antes del código desde la
carpeta del servicio con `python -m pytest <fichero> -q`.

- **T1** (sv3) `test_f072_obras_agrupadas.py`:
  `E   ModuleNotFoundError: No module named 'application.services.obras_agrupadas'` · `1 error in 0.37s`.
- **T2**: su traza guardada recogió un error de colección ajeno (`test_f077_cliente_hr.py`): no
  se aporta. T2 es la implementación de T1 y su RED es la de T1.
- **T4** `test_f072_settings.py`: `8 × Failed: DID NOT RAISE ValidationError`;
  `7 × AttributeError: 'Settings' object has no attribute 'obras_agrupadas'` · `15 failed in 1.63s`.
- **T6** (sv2) `test_f072_marca_sv2.py`:
  `15 × TypeError: ComprobadorObra.__init__() got an unexpected keyword argument 'marcas'`;
  `assert 'separador' in 'el "nº obra" tal cual (p.ej. "672").'` (y `posicion`, `no quites`,
  `no expandas`).
- **T8** (sv3) `test_f072_entrada_agrupada.py`:
  `E   ImportError: cannot import name 'entrada_agrupada' from 'application.services'` · `1 error in 0.37s`.
- **T10** (sv3) `test_f072_pipeline.py`: primero `E   ImportError: cannot import name
  'EntradaPartida' from 'domain.models.parte_records'`; con el dataclass,
  `29 × TypeError: PersistPartePipeline.__init__() got an unexpected keyword argument 'entradas'`
  · `29 failed, 1 passed in 2.31s`.
- **T12** (sv3) `test_f072_conciliacion.py`:
  `4 × TypeError: PartidaConciliador.__init__() got an unexpected keyword argument 'ajustes'`;
  `1 × KeyError: 'obra_codigo'` · `5 failed, 3 passed in 1.82s`.
- **T14** (sv5) `test_f072_guarda.py`: `E   ImportError: cannot import name
  'MOTIVO_PARTIDA_AGRUPADA' from 'application.services.reglas_registro'` · `1 error in 0.52s`.
- **Enmienda (b), sv5** `test_f072_guarda_reajuste_franquicia.py` · `8 failed in 1.28s`:
  `3 × TypeError: OpReajuste.__init__() got an unexpected keyword argument 'partida_metodo'`;
  `3 × TypeError: PeticionFranquicia.__init__() got an unexpected keyword argument 'partida_metodo'`;
  `AttributeError: 'OpReajuste' object has no attribute 'partida_metodo'` (y `'PeticionFranquicia'`).
- **Enmienda (b), sv4** `test_f072_marca_reajuste_franquicia.py` · `6 failed, 7 passed in 5.38s`:
  `AttributeError: module 'application.services.franquicia' has no attribute 'con_metodo_base'`;
  `3 × KeyError: 'partida_metodo'`; `AssertionError: assert None == 'var'`.
- **T16** (sv5) `test_f072_conflictos.py` · `7 failed, 5 passed in 0.88s`:
  `AssertionError: assert 'omitir' == 'escribir'`;
  `AssertionError: assert [Conflicto(cl...egistros=[1])] == []`;
  `At index 0 diff: (91013, 8.0) != (91012, 8.0)` (más los `TypeError` de `por_partida`/`con_partida`).
- **T18** (sv4) `test_f072_catalogo_entradas.py`:
  `E   ModuleNotFoundError: No module named 'application.services.catalogo_entradas'` · `1 error in 1.01s`.
- **T20** (sv4) `test_f072_repositorio.py`: `E   ImportError: cannot import name
  'PartidaFijaError' from 'infrastructure.database.parte_repository'` · `1 error in 3.40s`.
- **T22** (sv4) `test_f072_endpoints.py`: `E   ImportError: cannot import name
  'MOTIVO_ENTRADA_AGRUPADA' from 'application.services.sincronizar_ambito'` · `1 warning, 1 error in 2.04s`.
  El test de R33 en sv5 (`LineaIn` por HTTP, en `test_f072_guarda.py`), antes de añadir el campo:
  `E       AssertionError: assert None == 'var'`.
- **T26** (raíz) `test_f072_documentacion.py`:
  `E       AssertionError: falta la semántica 24 «Obras agrupadas (F-072)»`;
  `E       AssertionError: assert 'application/services/obras_agrupadas.py' in 'LÍMITE DE SERVICIO …'`;
  `E           AssertionError: sv2-extraccion`.

## Salida de los tests

Resultado real de `bash harness/init.sh` (2026-11-23, tras T28, rama de la feature): **ENTORNO
LISTO**, exit 0.

| Suite | Resultado |
|---|---|
| Raíz (`tests/`) | 2551 passed, 48 skipped in 2316.46s |
| sv1 | en verde por caché (sin cambios desde el verde del 2026-11-23 13:51) |
| sv2 | 579 passed, 1 skipped in 96.83s |
| sv3 | 2954 passed, 2 skipped in 80.44s |
| sv4 | 4018 passed in 1614.36s |
| sv5 | 1809 passed, 1 skipped in 45.56s |

Las otras líneas de `init.sh`:
- `PUERTA COBERTURA: 99.7% de 1073 líneas cambiadas cubiertas (1070/1073, umbral 90% (del nivel
  critico), nivel critico; diff desde b1fb495192, merge-base con dev)`
- `PUERTA TAMAÑO: … impl 220/220, review 140/140` · `PUERTA CARRIL: N/A (critico)` ·
  `CAPA E2E: N/A (ningún servicio declara el bloque e2e)`

Otros: T25 (`git diff dev --stat -- '*/tests/test_f0[0-6]*'`) vacío; T24 `node --check` y
`python -m harness.servicios --validar`, en verde. Las copias del gemelo se miden con
`tests/test_f072_obras_agrupadas_copia.py` (idéntico en sv2, sv4 y sv5), que ejecuta los tests del
gemelo de sv3 contra la copia del servicio; solo tests, sin lógica copiada. Pista O4 que sigue
abierta: `sqlalchemy_parte_repository.py:1196` (sv3), el `continue` del reemplazo del mismo día.

## Verificaciones MANUAL pendientes (del humano)

Los comandos completos están en `tasks.md`:
- **T29 (M0)**, antes de encender, solo lectura en la base `partes`: la consulta `SELECT
  d.obra_codigo, upper(d.obra_numero_leido) …` de T29. Cuenta cuántos partes hay ya en
  POSTV2/VAR o con marca leída.
- **T30 (M1)**, universos contra porcentajes: sv4 en local con
  `POSTVENTA_OBRA_COD=POSTV2 VAR_OBRA_COD=VAR VAR_PARTIDA_DESDE=29`, el `python -c …Counter…` de
  T30 sobre `/api/sigrid/obras`, y comparar con el preview de dedicación.
- **T31 (M2)**, portal y escritura en modo pruebas (`OBRA_PRUEBAS_FORZAR=true`, obra 0404,
  local):
  1. Pasar un parte a `VAR-<n>` y otro a `Postv-<obra>`, y aprobar.
  2. Comprobar el resultado con `python services/partes-transfer/prueba_escritura_sigrid.py verificar`.
  3. Comprobar que una línea sin marca en POSTV2 sale omitida con `partida_agrupada:`.
  4. Limpiar con `python services/partes-transfer/prueba_escritura_sigrid.py limpiar --ejecutar`.
- **Encendido**: variables en el orden sv5 → sv3 → sv2 → sv4 (`infra/README_partes.md`), y
  avisar a porcentajes. **Push** de la rama: lo hace el humano (`azure-apps` ya está subido).
- Los 13 equivalentes de T28: **aceptados** por el humano el 2026-11-24.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | 11 911 passed, 52 skipped, 0 failed (raíz y sv2 a sv5; sv1, por caché) |
| Cobertura de las líneas cambiadas | **99.7 %** (1070/1073, umbral 90 % de `critico`) |
| Mutantes generados y supervivientes | 604 generados, 222 evaluados (muestra de `critico`), 178 muertos, **44 supervivientes**: 31 muertos después con tests de T28 y **13 equivalentes aceptados** por el humano (2026-11-24). `progress/mutacion_F-072.md` |
| Tiempo de la suite | raíz 2316 s · sv2 97 s · sv3 80 s · sv4 1614 s · sv5 46 s |
| Capa e2e | N/A: `CAPA E2E: N/A (ningún servicio declara el bloque e2e)` |

## Review 1 (CHANGES_REQUESTED): cambios 1 y 2, y O3

- **Cambio 1** (013766e): `catalogo_entradas.py` guarda en `partida_capitulo` la **categoría**
  del capítulo (`h.categoria`: CD/CI/CP/OTRO, como sv3), no `h.capitulo_cod`. Sin capítulo, `OTRO`.
  - RED (20f91f6), `python -m pytest tests/test_f072_catalogo_entradas.py -q` en sv4:
    `E       AssertionError: assert ('CD.POSTVENTA', None) == ('CD', 'OTRO')` · `1 failed, 30 passed in 0.34s`.
- **Cambio 2** (20f91f6): `test_f072_r25_el_indice_desempata_como_casar_postventa`, 11 casos contra
  `casar_postventa`, verdes desde el principio (faltaba evidencia, no lógica); T28 añade 2.
- **O3**: fuera `CatalogoEntradas.ajustes`, sin uso. `init.sh` en verde, cobertura 99,7 %.

## T33: enmienda del humano del 2026-11-23 («D1 c, D2 a»)

- **D1 (c), R8**: `casar_var` solo aplica el segundo paso (la única con ese número inicial) si lo
  leído es solo un número (`_NUMERO.fullmatch`). Cambiado en las 4 copias del gemelo, md5
  `62c13db…`. R10 (equivalencia), R11 y las copias: en verde.
  - RED (99fe8d5), sv3: `assert casar_var(_hojas("29.1", "30"), "29.3") is None`, que caía con
    `E       AssertionError: assert namespace(ide=1, cod='29.1', …) is None` · `1 failed`.
- **D2 (a), R38**: el reajuste (`_Preparada.por_partida` = `ctx.agrupada`) lee `paride` y solo
  choca con la misma partida; en las obras normales, como hoy (sin `con_partida`).
  - RED (99fe8d5), sv5, `-k d2a`: `E       AssertionError: assert (False, 'ya h...lineas 7002)')
    == (True, None)` · `1 failed, 2 passed`.
- Código c3a8af8; sv3 2944/2, sv5 1800/1; `init.sh` ENTORNO LISTO, cobertura 99,7 %.

## T28: campaña de mutación (2026-11-23)

- **Campaña** (HEAD afaf5e3): 222 evaluados, 178 muertos, 44 supervivientes, 0 timeouts. Análisis
  de cada uno y las 7 declaraciones de ficheros sin mutantes en `progress/mutacion_F-072.md`.
- **31 muertos con tests nuevos** (commits 5fde8cf y 9e92935): `tests/test_f072_t28_mutantes.py` en
  sv3, sv4 y sv5, y 4 tests del gemelo en el `test_f072_obras_agrupadas.py` de sv3, que las otras
  tres copias ejecutan por `*_copia.py`. Cada mutante se aplicó a mano y se deshizo: el test cae con él
  (`EXIT 1 => MUERTO`, script del scratchpad) y pasa sin él. Ningún test cambió código.
  - No eran equivalentes: `:218` `[:2]` (`V 2.1`, `POST5B`), `:211` `p[1]` (un alias `-` casaría
    cualquier código), `:696` (defecto de `_choques`), `:134` (« de la obra»), `app.py:4234/4267/4268`,
    `franquicia.py:246/250`, `catalogo_entradas.py:154/179` y `entrada_agrupada.py:126/140/160`.
- **13 equivalentes, aceptados por el humano el 2026-11-24** («acepto los 13 equivalentes de F-072») (#1, 12–15, 19–21, 23, 26, 34, 36, 37):
  `is None` frente a la veracidad sobre valores que nunca son falsos salvo `None` (dataclasses sin
  `__bool__`/`__len__`, una tupla de 2, `tipo_de`, `deleted_at_utc` siempre `isoformat()`).
  Demostración: `progress/equivalentes_F-072.py sv2|sv3|sv4|sv5`, exit 0 en los cuatro.
- **Encargo del reviewer** (38ab77b): `[(2,"0578",0),(3,"0578B",0)]` y `[(3,"0578B",0),(2,"0578-B",0)]`.
  Matan `casar` con los `get` intercambiados (`FAILED …[exacta_y_con_letras]`) y `_orden` sin `h.ide`
  (`FAILED …[con_letras_mismo_normalizado]`). Sin mutante, los 13 casos en verde. Ningún
  superviviente revela un fallo del código ni una ambigüedad de la spec.
