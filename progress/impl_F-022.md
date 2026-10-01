<!-- progress/impl_F-022.md -->
# F-022 · Aprobar solo las líneas seleccionadas — Informe del implementer

Rama `feature/F-022-aprobar-seleccionadas`. Rigor **critico**. Solo **sv4**
(sv5 sin cambios, R21). Ni una escritura en Sigrid ni en producción.

## 1. Qué cambió

- **Reparto por obra (sv4)**: `lineas_para_registro` devuelve `grupos` (una
  obra por `obra_key_for_registro`, en orden de clave, con `estado_previo`) y
  `excluidas_detalle`; `registro_ids_de_trabajador` nuevo. Los tres
  `/api/aprobar/*` mandan **una petición a sv5 (o a la cola) por obra**, una
  tras otra, sin «todo o nada»; tope `APROBACION_MAX_OBRAS=10` (1–50).
- **Ámbito**: con `ambito` (`obra`+periodo+modo o `trabajador`), un id ajeno
  a la vista (otra obra, periodo, persona, papelera o inexistente) es 422
  `fuera_de_ambito` sin llamar a sv5 ni marcar; tope de 5000 ids.
- **Listado del modal (DA19)**: lo arma el servidor (`reparto_obras.py`) con
  la respuesta de sv5: fila por línea, estado (`nuevo`, `reaprobacion`,
  `conflicto`, `omitida`, `ya_registrada`, `no_se_registra`) y `totales`.
- **Navegador**: casilla `sel-linea` en la celda Fecha de cada fila (también
  congelada), «Seleccionar visibles»/«Quitar selección» y contador; el botón
  de cabecera pasa a «Aprobar seleccionadas/visibles/todo (N)» con `ambito`;
  modal por obra (resumen siempre visible, listado plegado con > 40 filas,
  tabla con cabecera fija, conflictos/errores/bloqueo fuera del pliegue,
  «Excluidas (N)» con las ocultas); confirmar y sondeo por obra.

Ficheros: `application/services/reparto_obras.py` (nuevo),
`interface_adapters/web/app.py`, `infrastructure/database/parte_repository.py`,
`config/settings.py`, `templates/obra_detail.html`,
`templates/trabajador_detail.html`, `static/app.js`, `static/styles.css`,
`tests/test_f022_{aprobar_seleccion,reparto_obras,vistas_seleccion}.py`,
`tests/test_f024_borrado_sigrid.py` (1 test adaptado, T1), `docs/ARCHITECTURE.md`
(semánticas 5 y 10, +7 líneas netas) y, en `azure-apps`, `partes.md`
(commit local `fdc6e1d`, sin push).

Commits (uno por tarea): `b5b28dc` T1 · `8730a51` T2 · `e70692f` T3 ·
`223eeee` T4 · `678d5ad` T5 · `6a43fe6` T6 · `e79460a` T7 · `3ecd9e6` T8 ·
`b7f95d1` T9 · `f4aed49` T10 · `1fe276b` T11 · `2524bf9` (tests de
endurecimiento previos a la mutación) · T13–T15 en el commit de cierre.

## 2. T1 · Inventario de tests de sv4 afectados

Contraste de la spec con dev (F-021, F-023, F-024 ya mergeadas): describe bien
`_payload_registro`, los tres `/api/aprobar/*`, el modal y `PartidaSel`. Solo
no nombra el aviso de cuenta de F-021 (`avisosCuentaHtml`, dentro de
`resumenHtml(pf)`): se integra llamando a `resumenHtml` **por grupo**. Ningún
cambio de comportamiento ni de decisiones aprobadas.

| Test | Qué mira | Efecto |
|---|---|---|
| `test_f024_…::test_f024_r22_payload_repo_sin_ids` | dict ENTERO de `lineas_para_registro([])` | **adaptado** (+`grupos`, +`excluidas_detalle`, con nota) |
| `test_f021_…::test_f021_r21_…` / `…_r19_resumen_html_llama_a_avisos_cuenta` | `acciones` plano; `resumenHtml` llama a `avisosCuentaHtml(pf.acciones)` | sin cambio (un grupo ⇒ plano tal cual; `resumenHtml(g)` por obra) |
| `test_f003_r23_…::…se_sirve_igual` | campo plano `escribir` del doble | sin cambio |
| `test_f003_r18:127`, `test_f003_r23:255`, `test_f024:444` | claves del payload | sin cambio (R33) |
| `test_f002_aprobar_encolar:133,154`, `test_f002_mutantes:245`, `test_f024:472` | `pisar_claves` sin prefijo | sin cambio (un grupo ⇒ a ese grupo) |
| `test_f002_degradacion`, `test_f002_mutantes` (`RepositorioRoto`) | traza/marcado que fallan | sin cambio |

## 3. Decisiones y desviaciones (justificadas)

1. **R19 también en el preflight**: claves sin prefijo con varias obras ⇒ 422
   en los tres endpoints (el preflight manda a sv5 las claves repartidas).
2. **Línea sin acción de sv5** en el preflight: el listado la trata como
   escritura (`nuevo`/`reaprobacion`, horas de la línea); sv5 siempre manda
   una acción por línea, así que solo afecta a dobles o a un sv5 viejo.
3. **`parcial`** = no todo fue bien **y** algo sí; si todas fallan,
   `parcial: false` y `ok: false`. `agregar_ejecucion` concatena también
   `pisadas` (además de lo que lista el design).
4. **Obra sin identificar** (`nom-…`): viaja con `obra: {}`, la misma regla
   que ya tenía el plano de F-024 (sv5 decide; en pruebas va a la 0404).
5. **`excluidas_detalle` lleva `motivo`** (R26 lo pide; el design §5.1 no lo
   listaba), construido en el repositorio.
6. **Ids no numéricos ⇒ 422** también sin `ambito` (antes era un 500).
   `MAX_IDS_APROBACION=5000` es constante de `app.py`, no variable (DA11).
7. **JS**: las obras bloqueadas por Sesame sin la casilla **no se mandan** a
   `encolar` desde el navegador (se listan como «Sin registrar» con su
   motivo): mandarlas haría que, si eran las únicas de la cola, el servidor
   devolviera el 422 de «todas bloqueadas» encima de un resultado válido. La
   guarda del servidor (R18) sigue igual. Una sola casilla de Sesame para
   todas las obras bloqueadas.
8. **JS retirado**: `mostrarResultado`, `ejecutar`, `encolar`,
   `sondearEncolado`, `errorModal` y `excluidasHtml` (F-024) los sustituyen
   el resultado y el sondeo **por obra** y «Excluidas (N)». «Aprobar todo» de
   obra manda ahora ids + `ambito` (el atajo `obra_key` del servidor sigue
   para JS en caché). La `.bulk-bar` gana «Aprobar seleccionadas» (DA5), que
   pulsa el botón de cabecera.
9. **Orden del listado**: `ORDEN_TIPOS` es una tupla (`.index`) y `fecha_int`
   va sin `or 0` (el repositorio ya pone 0): evita mutantes equivalentes.
10. Los docstrings de `test_f017_aprobacion_firmada.py:160` y
    `test_f017_punto_unico.py:274` citan `_payload_registro`, que ya no
    existe (ahora `_preparar_registro` + `_payload_grupo`). No se tocan
    (R34: solo se adapta lo inventariado); `_actor(request)` sigue en 14.
11. El test `test_f022_r13_ambito_ausente_sigue_como_hoy` de la traza RED de
    T5 se renombró a `test_f022_r13_preflight_sin_vista_reparte_por_obra`
    (es de §D, se verifica en T6).

## 4. Fase RED (requisitos centrales: R10–R12, R14, R15, R17–R19, R21–R24, R31, R32)

Salida real completa (líneas `E`/`FAILED` y resumen de pytest) en
**`progress/red_F-022.log`** (379 líneas). Extracto por tarea, desde
`services/partes-front`:

**T2** `pytest -q tests/test_f022_aprobar_seleccion.py -k repo` → `11 failed in 1.74s`
```
E       AttributeError: 'ParteReviewRepository' object has no attribute 'registro_ids_de_trabajador'. Did you mean: 'registro_ids_de_obra'?
E       KeyError: 'grupos'
E       KeyError: 'excluidas_detalle'
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r10_repo_ids_de_trabajador_son_los_de_su_tabla
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r14_repo_grupos_uno_por_obra_en_orden_de_clave
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r26_repo_excluidas_detalle
```
**T3** `pytest -q tests/test_f022_reparto_obras.py -k "claves or agregar"` → `19 failed in 0.34s` (esqueleto con firmas)
```
E       NotImplementedError
FAILED tests/test_f022_reparto_obras.py::test_f022_r19_claves_sin_prefijo_con_varios_grupos_es_none[grupos0]
FAILED tests/test_f022_reparto_obras.py::test_f022_r17_agregar_un_grupo_fallido_no_tumba_a_los_demas
FAILED tests/test_f022_reparto_obras.py::test_f022_r22_agregar_ejecucion_parcial_sin_todo_o_nada
```
**T4** `pytest -q tests/test_f022_reparto_obras.py -k "listado or totales"` → `21 failed, 1 passed, 19 deselected in 0.63s`
```
E       NotImplementedError
FAILED tests/test_f022_reparto_obras.py::test_f022_r23_listado_codigo_partida_recurso_y_horas_de_la_accion
FAILED tests/test_f022_reparto_obras.py::test_f022_r24_listado_conflicto_manda_sobre_la_accion
FAILED tests/test_f022_reparto_obras.py::test_f022_r24_listado_grupo_fallido_no_se_registra
```
**T5** `pytest -q tests/test_f022_aprobar_seleccion.py -k ambito` → `47 failed, 5 passed, 11 deselected, 1 warning in 13.21s`
```
E       assert 200 == 422
E        +  where 200 = <Response [200 OK]>.status_code
E       AssertionError: assert 'no hay lineas seleccionadas' in 'faltan registro_ids u obra_key'
E       ValueError: invalid literal for int() with base 10: 'x'
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r10_ambito_obra_respeta_el_modo_natural
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r11_ambito_id_ajeno_es_422_sin_tocar_nada[o20_a-ambito0-/api/aprobar/encolar]
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r12_ambito_mal_formado_es_422_sin_sv5[ambito7-<lambda>-el maximo es 5000-/api/aprobar/ejecutar]
```
**T6** `pytest -q tests/test_f022_aprobar_seleccion.py -k preflight` → `19 failed, 15 passed, 48 deselected, 1 warning in 9.40s`
```
E         Right contains one more item: {'ide': 20, 'codigo': '0200', 'nombre': 'Obra Uno'}
E                   AttributeError: 'Settings' object has no attribute 'aprobacion_max_obras'
E       KeyError: 'grupos'
E       AssertionError: assert 'caido' == 'ninguna obra...; 0200: caido'
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r14_preflight_una_llamada_a_sv5_por_obra
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r15_preflight_mas_de_diez_obras_es_422_con_desglose
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r18_preflight_sesame_no_fiable_solo_en_un_grupo
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r31_preflight_avisos_y_bloqueo_solo_de_lo_pedido
```
**T7** `pytest -q tests/test_f022_aprobar_seleccion.py -k ejecutar` → `8 failed, 19 passed, 68 deselected, 1 warning in 7.75s`
```
E         At index 0 diff: ('0100', ['obr-20::502|20260303|1', 'obr-10::k1', 'obr-99::kx']) != ('0100', ['k1'])
E       KeyError: 'parcial'
E           RuntimeError: se corto
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r19_ejecutar_cada_grupo_recibe_solo_sus_claves
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r22_ejecutar_un_grupo_mal_solo_deja_en_error_sus_lineas
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r18_ejecutar_grupo_bloqueado_sin_override_no_se_envia
```
**T8** `pytest -q tests/test_f022_aprobar_seleccion.py -k encolar` → `8 failed, 18 passed, 81 deselected, 1 warning in 6.48s`
```
E         At index 0 diff: ('0100', [1, 2, 5, 6], 'local:ana') != ('0100', [1, 2], 'local:ana')
E           RuntimeError: cola caida
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r20_encolar_una_publicacion_por_obra
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r21_encolar_si_falla_una_obra_las_demas_siguen
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r21_encolar_si_fallan_todas_es_502_sin_marcas
```
**T9** `pytest -q tests/test_f022_vistas_seleccion.py -k vista` → `6 failed, 4 passed, 1 warning in 5.06s`
```
E           AssertionError: la fila 1 no tiene casilla
E       AssertionError: falta la barra .sel-tools
FAILED tests/test_f022_vistas_seleccion.py::test_f022_r1_vista_casilla_en_cada_fila_tambien_congelada[/obras/obr-10?period=2026-03&modo=natural]
```
R32 (lo no pedido no cambia) y R33 no tienen traza RED propia: el código previo
ya los cumplía con un solo lote; sus tests (`…r32_ejecutar…`, `…r32_encolar…`,
`…r33_…`) son guardas de regresión y pasaron desde el primer día. Tras cada
implementación, el mismo comando en verde (p. ej. T7: `27 passed`).

## 5. Verificación (resultado real)

- `bash harness/init.sh` (HEAD `2524bf9`): **ENTORNO LISTO**; raíz `419
  passed, 1 skipped`; sv4 `1427 passed in 266.95s`; resto por caché verde;
  `PUERTA COBERTURA: 100.0% de 282 líneas cambiadas cubiertas`; tamaño OK.
- Suites (T13): sv4 `1414 passed in 187.42s` (antes de los tests de
  endurecimiento), sv5 `269 passed in 5.76s` (sin cambios), raíz `419 passed,
  1 skipped in 58.93s`. F-022: `197 passed` en sus tres ficheros.
- `node --check services/partes-front/static/app.js`: OK. Jinja2: las dos
  plantillas parsean (`test_f022_r34_vista_las_plantillas_parsean`).
- ruff: sin avisos en los ficheros nuevos; `app.py` y `parte_repository.py`
  con los mismos avisos que en dev (22 y 85, deuda previa).

## 6. Mutación (T14) y evidencias

`python -m harness.mutacion --feature F-022 --workers 6 --timeout 600`
(campaña completa, HEAD `2524bf9`, 4 ficheros, 594 líneas en alcance):
**143 generados, 140 muertos, 3 supervivientes, 0 timeouts, 4506.2 s**. Los
3 tienen **test nuevo**, comprobado aplicando cada mutante a mano (su test
falla: `1 failed`, `1 failed`, `9 failed`): `sumar_totales` sin `lineas`
(`or 0→1`), excluida sin fecha en el repositorio (`or 0→1`) y `ok` del 422 de
ids no numéricos (`False→True`). **0 sin resolver**. Detalle en
`progress/mutacion_F-022.md`. Antes de la campaña se endurecieron tests y se
quitaron constantes que darían mutantes equivalentes (§3.9).

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | sv4 `1427 passed` (init.sh); sv5 `269 passed`; raíz `419 passed, 1 skipped`; F-022 `162 + 36` |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 282 líneas cambiadas cubiertas` |
| Mutantes generados / supervivientes | 143 / 3 → 0 tras tests nuevos |
| Tiempo de la suite | sv4 266.95 s (init.sh); raíz 62.37 s; mutación 4506.2 s |

Tras la campaña: commit `e0951b5` (solo JS: nombre de obra sin separador
colgante) y los tests de los supervivientes; ninguna línea Python de
producción cambia después de `2524bf9`. Verificado además con dos pruebas
de humo en `node` (lógica del botón y del resultado por obra con dobles de
`modal`/`post`), fuera del repositorio.

## 7. Pendientes MANUAL (humano)

Desplegar solo sv4 (`redeploy_partes.ps1`, lo pide el humano) y **Ctrl+F5**.
Escrituras solo en **modo pruebas** (`OBRA_PRUEBAS_FORZAR=true`, obra 0404,
`PRUEBA-IA`) y limpiar con `prueba_escritura_sigrid.py`.

- **M1 · ¿ya pasó? (PG `partes`, solo lectura)**:
  `SELECT sigrid_parte_cod, count(DISTINCT coalesce(obra_ide::text,
  obra_codigo, obra_nombre)) AS obras, count(*) FROM parte_registros WHERE
  sigrid_hmoide IS NOT NULL GROUP BY 1 HAVING count(DISTINCT
  coalesce(obra_ide::text, obra_codigo, obra_nombre)) > 1;`
  Esperado: 0 filas fuera de los partes de la 0404 (modo pruebas). Una fila
  con un parte real = un lote de varias obras que fue entero a una: revisarlo.
- **M2 · obra**: abrir una obra × periodo; marcar 2 casillas → el botón dice
  «✓ Aprobar seleccionadas (2)» y el contador «2 seleccionadas». Pulsarlo:
  el modal dice «Alcance: 2 seleccionadas de M», una sección de la obra con
  una tabla de 2 filas y estado. Registrar → solo esas 2 cambian de estado.
- **M3 · filtro sin selección**: pinchar casillas de la matriz → «Aprobar
  visibles (N)» con N = filas visibles; «Quitar filtro» → «Aprobar todo (M)».
  Marcar 1 y quitar el filtro: la marca sigue.
- **M4 · ocultas**: marcar 3, filtrar una columna para ocultar 1 → contador
  «3 seleccionadas (1 oculta: no se aprueban)», botón «(2)»; en el modal,
  «Excluidas (1)» con «1 linea(s) marcadas estan ocultas…». Ocultar las 3 →
  botón deshabilitado con el `title` «Las 3 lineas seleccionadas…».
- **M5 · persona con dos obras** (modo pruebas): sin filtrar, «Aprobar todo»
  → dos secciones con su listado y total y el total general «(2 obras)».
  Registrar → en `ca-sv5-transfer` dos `[registro] MODO PRUEBAS: la obra <X>
  se ignora` y en `ca-sv4-front` dos `[transfer-cola] encolada`; el modal
  sondea cada obra y da su resultado.
- **M6 · listado**: con una `registrado` y una `borrado_sigrid` en la
  selección → «Excluidas (2)» con su motivo; una `error` previa → estado
  «reaprobación» (title «antes: error»); una incidencia → su código CI* y
  0 h; los totales del `<summary>` cuadran con la tabla.
- **M7 · muchas filas**: «Aprobar todo» en una obra × mes completa (> 40
  filas) → secciones plegadas con el resumen visible, tabla con scroll y
  cabecera fija; conflictos fuera del pliegue con casilla `obr-…::…`.
  Regresión: «Reaprobar»/«Aprobar» de una línea marcada aprueba solo esa;
  «Editar partida» en bloque sigue igual; Shift+clic tras ordenar marca el
  rango visible en el orden de pantalla.
- **M8 · primera aprobación real de varias obras** (producción): repetir M1.
