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

Ficheros (sv4): `reparto_obras.py` (nuevo), `app.py`, `parte_repository.py`,
`settings.py`, las dos plantillas, `app.js`, `styles.css`, tres
`tests/test_f022_*.py`, `test_f024_borrado_sigrid.py` (1 test, T1);
`docs/ARCHITECTURE.md` (semánticas 5 y 10, +7 netas); `azure-apps/partes.md`
(commit local `fdc6e1d`, sin push). Un commit por tarea: `git log dev..HEAD`.

## 2. T1 · Inventario de tests de sv4 afectados

Contraste con dev (F-021/F-023/F-024): la spec acierta en todo salvo que no
nombra el aviso de cuenta de F-021 (`avisosCuentaHtml`, dentro de
`resumenHtml(pf)`): se pinta llamando a `resumenHtml` **por grupo**. Sin
cambios de comportamiento ni de decisiones aprobadas.

Inventario: solo **`test_f024_…::test_f024_r22_payload_repo_sin_ids`**
compara el dict ENTERO de `lineas_para_registro([])`: **adaptado** (+`grupos`,
+`excluidas_detalle`, con nota). Sin cambio, por darse con un solo grupo
(planos tal cual, R16) o por R33: `test_f021_r21`/`r19_resumen_html…`,
`test_f003_r23…se_sirve_igual`, `test_f003_r18:127`, `test_f003_r23:255`,
`test_f024:444`, las `pisar_claves` sin prefijo de `test_f002_aprobar_encolar`,
`test_f002_mutantes` y `test_f024:472`, y los `RepositorioRoto` de F-002.

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
7. **JS**: las obras bloqueadas por Sesame sin la casilla no se mandan a
   `encolar` (se listan «Sin registrar» con su motivo); si no, siendo las
   únicas de la cola, el 422 de «todas bloqueadas» taparía un resultado
   válido. R18 del servidor igual. Una sola casilla de Sesame.
8. **JS retirado**: `mostrarResultado`, `ejecutar`, `encolar`,
   `sondearEncolado`, `errorModal`, `excluidasHtml` (sustituidos por el
   resultado/sondeo por obra y «Excluidas (N)»). «Aprobar todo» de obra manda
   ids + `ambito` (el atajo `obra_key` sigue para JS en caché). La
   `.bulk-bar` gana «Aprobar seleccionadas» (DA5).
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
```
**T3** `pytest -q tests/test_f022_reparto_obras.py -k "claves or agregar"` → `19 failed in 0.34s` (esqueleto con firmas)
```
E       NotImplementedError
FAILED tests/test_f022_reparto_obras.py::test_f022_r19_claves_sin_prefijo_con_varios_grupos_es_none[grupos0]
FAILED tests/test_f022_reparto_obras.py::test_f022_r17_agregar_un_grupo_fallido_no_tumba_a_los_demas
```
**T4** `pytest -q tests/test_f022_reparto_obras.py -k "listado or totales"` → `21 failed, 1 passed, 19 deselected in 0.63s`
```
E       NotImplementedError
FAILED tests/test_f022_reparto_obras.py::test_f022_r23_listado_codigo_partida_recurso_y_horas_de_la_accion
FAILED tests/test_f022_reparto_obras.py::test_f022_r24_listado_conflicto_manda_sobre_la_accion
```
**T5** `pytest -q tests/test_f022_aprobar_seleccion.py -k ambito` → `47 failed, 5 passed, 11 deselected, 1 warning in 13.21s`
```
E       assert 200 == 422
E        +  where 200 = <Response [200 OK]>.status_code
E       AssertionError: assert 'no hay lineas seleccionadas' in 'faltan registro_ids u obra_key'
E       ValueError: invalid literal for int() with base 10: 'x'
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r10_ambito_obra_respeta_el_modo_natural
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r11_ambito_id_ajeno_es_422_sin_tocar_nada[o20_a-ambito0-/api/aprobar/encolar]
```
**T6** `pytest -q tests/test_f022_aprobar_seleccion.py -k preflight` → `19 failed, 15 passed, 48 deselected, 1 warning in 9.40s`
```
E         Right contains one more item: {'ide': 20, 'codigo': '0200', 'nombre': 'Obra Uno'}
E                   AttributeError: 'Settings' object has no attribute 'aprobacion_max_obras'
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r14_preflight_una_llamada_a_sv5_por_obra
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r15_preflight_mas_de_diez_obras_es_422_con_desglose
```
**T7** `pytest -q tests/test_f022_aprobar_seleccion.py -k ejecutar` → `8 failed, 19 passed, 68 deselected, 1 warning in 7.75s`
```
E         At index 0 diff: ('0100', ['obr-20::502|20260303|1', 'obr-10::k1', 'obr-99::kx']) != ('0100', ['k1'])
E       KeyError: 'parcial'
E           RuntimeError: se corto
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r19_ejecutar_cada_grupo_recibe_solo_sus_claves
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r22_ejecutar_un_grupo_mal_solo_deja_en_error_sus_lineas
```
**T8** `pytest -q tests/test_f022_aprobar_seleccion.py -k encolar` → `8 failed, 18 passed, 81 deselected, 1 warning in 6.48s`
```
E         At index 0 diff: ('0100', [1, 2, 5, 6], 'local:ana') != ('0100', [1, 2], 'local:ana')
E           RuntimeError: cola caida
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r20_encolar_una_publicacion_por_obra
FAILED tests/test_f022_aprobar_seleccion.py::test_f022_r21_encolar_si_falla_una_obra_las_demas_siguen
```
**T9** `pytest -q tests/test_f022_vistas_seleccion.py -k vista` → `6 failed, 4 passed, 1 warning in 5.06s`
```
E           AssertionError: la fila 1 no tiene casilla
E       AssertionError: falta la barra .sel-tools
FAILED tests/test_f022_vistas_seleccion.py::test_f022_r1_vista_casilla_en_cada_fila_tambien_congelada[/obras/obr-10?period=2026-03&modo=natural]
```
R32/R33 sin RED propia: el código previo ya los cumplía con un lote; sus
tests son guardas de regresión. Tras implementar, cada comando en verde.

## 5. Verificación (resultado real)

- `bash harness/init.sh` final (HEAD `0e7a588` + este informe): **ENTORNO
  LISTO**; raíz `419 passed, 1 skipped in 46.41s`; sv4 `1428 passed in
  192.85s`; sv1/sv2/sv3/sv5 verdes (caché); `PUERTA COBERTURA: 100.0% de 282
  líneas cambiadas cubiertas`; tamaño dentro de topes. sv5 aparte: `269
  passed in 5.76s` (sin cambios). `node --check static/app.js` OK; Jinja2 de
  las dos plantillas OK (`test_f022_r34_…`). ruff: 0 avisos en lo nuevo;
  `app.py`/`parte_repository.py` con los mismos que en dev (22 y 85).

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
| Tests ejecutados | sv4 `1428 passed`; sv5 `269 passed`; raíz `419 passed, 1 skipped`; F-022 `162 + 36` |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 282 líneas cambiadas cubiertas` |
| Mutantes generados / supervivientes | 143 / 3 → 0 tras tests nuevos |
| Tiempo de la suite | sv4 192.85 s; raíz 46.41 s; sv5 5.76 s; mutación 4506.2 s |

Después de `2524bf9` solo cambian JS (`e0951b5`), tests y docs: ninguna
línea Python de producción. Más dos pruebas de humo en `node` fuera del repo
(botón y resultado por obra con dobles de `modal`/`post`).

## 7. Pendientes MANUAL (humano)

Desplegar solo sv4 (lo pide el humano) y **Ctrl+F5**. Escrituras solo en
modo pruebas (obra 0404, `PRUEBA-IA`); limpiar con `prueba_escritura_sigrid.py`.

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
- **M3 · filtro sin selección**: casillas de la matriz → «Aprobar visibles
  (N)»; «Quitar filtro» → «Aprobar todo (M)»; una marca sobrevive al filtro.
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
