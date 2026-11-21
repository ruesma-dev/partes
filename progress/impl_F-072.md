# F-072 · Informe del implementer (`critico`)

Postventa y obras VAR como **entradas** de una obra agrupada (obra agrupada + una partida). Rama
`feature/F-072-postventa-var-como-obras`, un commit por tarea `F-072 Tn: …`. Hechas T1–T27 y
T32. **T28 (mutación) y T29–T31 (manuales) quedan sin marcar**: son del líder y del humano.
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
  porcentajes), §4.5 bis y §5.6. Commit **cd58cab**, aparte y **sin push**; el `pull --rebase`
  previo estaba al día.

Tests nuevos: los `test_f072_*.py` de cada servicio y, en la raíz,
`test_f072_obras_agrupadas_gemelos.py`, `test_f072_equivalencia_porcentajes.py` y
`test_f072_documentacion.py`.

## Decisiones e interpretaciones (para el reviewer)

- **(i)** Los alias solo se leen en sv2 y sv3 (design §5–§6), pese al R1 literal.
- **(ii)** El segundo paso de `casar_var` es «la única con el mismo número inicial», al pie de
  la letra.
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
- **Observación**: `ReajustePipeline._choques` (F-046 R22) no aplica `por_partida`, porque R38
  solo nombra el pipeline de registro. Si se quiere igual en reajuste, es otra feature.

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

Resultado real de `bash harness/init.sh` (2026-11-21, rama de la feature): **ENTORNO LISTO**,
exit 0.

| Suite | Resultado |
|---|---|
| Raíz (`tests/`) | 2551 passed, 48 skipped in 1550.33s |
| sv1 | en verde por caché (sin cambios desde el verde del 2026-11-20) |
| sv2 | 574 passed, 1 skipped in 70.15s |
| sv3 | 2943 passed, 2 skipped in 64.83s |
| sv4 | 3991 passed in 1116.40s |
| sv5 | 1796 passed, 1 skipped in 27.60s |

Las otras líneas de `init.sh`:
- `PUERTA COBERTURA: 99.3% de 1072 líneas cambiadas cubiertas (1065/1072, umbral 90% (del nivel
  critico), nivel critico; diff desde b1fb495192, merge-base con dev)`
- `PUERTA TAMAÑO: F-072 dentro de los topes (requirements 149/150, design 250/250, impl 150/220)`
- `PUERTA CARRIL: N/A (F-072 es de nivel critico: no declara límites)`
- `CAPA E2E: N/A (ningún servicio declara el bloque e2e)`

Otros resultados:
- **T25**: `git diff dev --stat -- '*/tests/test_f0[0-6]*'` sale vacío. Ningún test anterior se
  ha tocado.
- **T24**: `node --check services/partes-front/static/app.js` en verde.
- `python -m harness.servicios --validar` en verde.

**Las 7 líneas sin cubrir** (pistas para la campaña):
- `obras_agrupadas.py:62` en sv2 y sv5: la rama del árbol `dict`. Su único test usa
  `partida_catalog`, que esos dos servicios no tienen. Se salta allí y se cubre en sv3 y sv4.
- `catalogo_entradas.py:71`: una hoja de postventa sin código.
- `catalogo_entradas.py:91-92`: `_orden`, el desempate de varias candidatas con el mismo código.
- `catalogo_entradas.py:109`: la propiedad `ajustes`.
- `sqlalchemy_parte_repository.py:1196` (sv3): el `continue` del reemplazo del mismo día cuando
  los trabajadores no coinciden.

**Para medir las copias del gemelo**:
- `tests/test_f072_obras_agrupadas_copia.py`, idéntico en sv2, sv4 y sv5, carga por ruta los
  tests del gemelo escritos en sv3 y los ejecuta contra la copia del servicio.
- Uno de ellos comprueba que el módulo usado es el del servicio.
- `harness/servicios.json` declara esa dependencia, así la caché no salta la suite.
- Es solo de tests, sin lógica copiada.

**Incidencia del entorno, no del código.** En una pasada suelta de sv4, con otras suites de otros
proyectos corriendo a la vez, `test_f021_r19_pinta_una_fila_por_linea_escribir_con_aviso` cayó
con `CalledProcessError … returned non-zero exit status 3221225794`. Es `0xC0000142`: node no
llegó a arrancar. Suelto da 11/11, y en `init.sh` está en verde.

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
  avisar a porcentajes. **Push** de la rama y de `azure-apps` (cd58cab): lo hace el humano.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | 11 855 passed, 52 skipped, 0 failed (raíz y sv2 a sv5; sv1, por caché) |
| Cobertura de las líneas cambiadas | **99.3 %** (1065/1072, umbral 90 % de `critico`) |
| Mutantes generados y supervivientes | **pendiente de la pasada de campaña** (T28): la lanza el líder tras el APPROVED, con `python -m harness.mutacion --feature F-072` ⇒ `progress/mutacion_F-072.md` |
| Tiempo de la suite | raíz 1550 s · sv2 70 s · sv3 65 s · sv4 1116 s · sv5 28 s |
| Capa e2e | N/A: `CAPA E2E: N/A (ningún servicio declara el bloque e2e)` |

## Review 1 (CHANGES_REQUESTED): cambios 1 y 2, y O3

- **Cambio 1** (013766e): `catalogo_entradas.py` guarda en `partida_capitulo` la **categoría**
  del capítulo (`h.categoria`: CD/CI/CP/OTRO, como sv3), no `h.capitulo_cod`. Sin capítulo, `OTRO`.
  - RED (20f91f6), `python -m pytest tests/test_f072_catalogo_entradas.py -q` en sv4:
    `E       AssertionError: assert ('CD.POSTVENTA', None) == ('CD', 'OTRO')` · `1 failed, 30 passed in 0.34s`.
  - El test pone una hoja bajo `CD.POSTVENTA`, otra sin padre, y comprueba la longitud ≤ 8.
- **Cambio 2** (20f91f6): `test_f072_r25_el_indice_desempata_como_casar_postventa` contrasta el
  índice con `casar_postventa`, con 11 casos y en verde desde el principio. Eran falta de
  evidencia, no de lógica. Los casos:
  - `mas_corto`, `menor_normalizado`, `orden_inverso` (y con las filas al revés);
  - `letra_digito`, `letra_punto`, `de_baja`;
  - dos exactas con el `ide` invertido;
  - hoja sin código y hoja con código vacío.
- **O3**: fuera `CatalogoEntradas.ajustes`, que nadie usaba. D1 y D2 no se tocan.
- `bash harness/init.sh`: **ENTORNO LISTO**, exit 0. Raíz 2551/48; sv4 4003 passed; sv1–sv3 y
  sv5 por caché. `PUERTA COBERTURA` 99,7 % (1066/1069); impl 217/220.
