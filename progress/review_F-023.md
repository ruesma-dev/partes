<!-- progress/review_F-023.md -->
Revisión incremental desde df72dcc (pasada 2) · HEAD `5d9a3ce`; la pasada 1 fue completa (`dev...df72dcc`)

# F-023 · Review

**Veredicto (pasada 2): APPROVED.** Están corregidos los tres cambios de la pasada 1
(ver «Pasada 2»). Pasada 1: CHANGES_REQUESTED, sin defectos de lógica.

**Nivel de rigor:** `critico` (declarado en `harness/features.json`): fase RED
de los requisitos centrales, cobertura ≥ 80 %, mutación completa con 0
supervivientes y MANUAL con comando exacto.

## Verificación ejecutada por el reviewer

- `bash harness/init.sh` tal cual: **exit 0**; raíz 416 passed/1 skipped,
  sv1–sv5 en verde, `PUERTA COBERTURA` [OK] 99,8 % (596/597), tamaño [OK].
- Recálculo puro (`harness.alcance` + `generar_mutantes`): **28 ficheros,
  1.503 líneas, 214 mutantes** (sv3 155, sv4 22, sv5 37): coincide.
- **Campaña no reejecutada: 2.076,5 s (≈ 35 min) según el informe** (> 60 s):
  recálculo + RM1–RM6 + RM4.
- RM4 en copia de sv5 en el scratchpad (árbol real intacto): `r.empresa !=
  empresa`→`==` muere en `test_f002_regresion_preflight_equivalente`;
  `len(filas) > 1`→`>= 1` en `…r35_cliente_obra_por_codigo_con_su_empresa`; a
  mano, quitar `AND emp = ?` del `INSERT INTO hmo` muere en `…r34…` y del
  correlativo en `…r33_cliente_el_correlativo_es_de_la_empresa`. Base: 140
  passed (deseleccionado el test del manifiesto, que lee `../../infra`).
- Tests sin red ni BBDD; DNIs sintéticos; ni `MO/0239` ni nombres reales.

## Lo que se pidió comprobar especialmente

- **sv5**: correlativo con `AND emp = ?`; `INSERT INTO hmo … AND emp = ?`;
  cabecera con `obra.empresa` leída de Sigrid (nunca del portal); obra sin
  empresa o código en varias ⇒ excepción antes de escribir (también en modo
  pruebas). `verificar_recurso` (empresa → alta a la fecha → DNI) y
  `elegir_por_dni` (único candidato) corren en `preparar` (preflight y
  escritura); si `datos_recursos` falla, no se escribe nada. Sin
  `SIGRID_EMPRESA` en código de producción (`prueba_escritura_sigrid.py` queda
  fuera por design §7).
- **sv3**: `elegir_recurso` nunca devuelve `empleado_reside` fuera de
  candidatos (caso guía en `seleccion_sigrid` y conciliador); gemelas por
  membrete → trabajadores → nombre estricto → revisión (DA3); congeladas
  intactas (R30, DA7); nada se re-casa (R31).
- **Paginación/`truncated`**: `_leer_paginado` en todos los listados de sv3 y
  sv4 (`max_rows` 5.001) con guardianes `test_f023_r3_todo_paginado.py`;
  `truncated` ⇒ excepción en sv3, sv4 y sv5. Claves de orden = índice primario
  según `azure-apps/sigrid_tablas.md`; ningún SQL base traía `ORDER BY`.
- **Duplicados**: `orm_models.py` byte-idénticos (`cmp`) + guardián F-010;
  `de_alta` sv3/sv5 y SQL de sv4 vigilados por `tests/test_f023_de_alta_gemelos.py`;
  `CLAUDE.md` amplía solo lo de DA6 más el filtro SQL de sv4 previsto en T19.
- **sv2**: solo viñeta + clave `empresa_membrete` y el campo del modelo (DA12).
- **azure-apps `8c7df86`**: membrete, columnas, `SIGRID_EMPRESA` inerte,
  paginación y orden de despliegue (R43).

## Desviaciones

D1 (PATCH de obra por `ide`): necesaria para R39; aceptable, la valida el
humano (se guarda `payload.codigo` aunque la obra salga por `ide`). D2
(PyYAML): llega por `uvicorn[standard]` en `requirements.txt` y en el manifiesto
de sv3; si faltara, sv3 no arranca (fallo visible); declararlo, al humano.
D3–D5 correctas (D4 respeta capas). D6 bien declarado y arreglado.

## Checkpoints

- C1 [x] init.sh exit 0 · [x] ficheros del arnés.
- C2 [x] una `in_progress` · [x] rama de la feature · [x] `current.md`: F-023
  arriba como sesión activa (el resto es histórico previo del líder, como en
  reviews anteriores) · [x] history.
- C3 [x] hexagonal (los dos imports application→infrastructure ya estaban en
  `dev`) · [x] ruta en primera línea · [x] sin prints/TODO/secretos (PyYAML,
  D2) · [x] empleado≠recurso, incidencias sin cambio, ORM en las dos copias ·
  [x] estilo (pasada 2; en la 1, cambio 2).
- C3 bis [x] cabecera de origen ya presente + nota de actualización · [x] sin
  PDF/ofimática (`git log --diff-filter=A`) · [x] barrido del reviewer sobre
  las líneas añadidas (correos, IPv4, GUID, `password|secret|token|api_key|
  AccountKey=|sig=|Bearer`): solo `irrelevante-en-tests` de fixtures · [x] nada
  redactado.
- C4 [x] R1–R40 y R42 con ≥ 1 `test_f023_rN_*` (244 tests; p. ej.
  `…r25_r27_caso_guia_*`, `…r30_una_linea_congelada…`, `…r33/r34_cliente_*`,
  `…r36_pipeline_verifica_cada_recurso…`); R41 es JS: `node --check` OK +
  MANUAL T17 (sin banco de tests JS, justificado por T17); R43 leído ·
  [x] sin red/BBDD · [x] MANUAL (pasada 2; en la 1, cambio 1).
- C4 bis [x] rigor declarado · [x] fase RED (pasada 2; en la 1, cambio 3) · [x] cobertura 99,8 % ·
  [x] mutación recalculada · [x] > 60 s, no reejecutada (dicho) + RM4 ·
  [x] coste 2.076,5 × 6 ÷ 214 = 58,2 s ≫ 1 s · [x] sin «⚠ CAMPAÑA NO VÁLIDA»,
  0 sin veredicto · [x] RM1: SHA `ad48d2d`, después solo `progress/` y
  `tasks.md` · [x] RM2: 9,7 × 6 = 58 s/mutante, coherente con bases 16,7 /
  12,5 / 292 s y `-x` · [x] RM3: repasados los 214; los de solo-log los matan
  tests de caplog que exigen R28/R29, los `frozen` tests de inmutabilidad o la
  herencia frozen; ningún equivalente muerto · [x] RM5 N/A: no hay
  equivalentes declarados (los 3 supervivientes iniciales se mataron con
  tests, `16dc86a`) · [x] RM6: `200a98c` solo refactoriza `obra_matcher` (la
  guarda `if cod_n` sigue) · [x] campaña automática · [x] 0 supervivientes ·
  [x] «Evidencias» completas con 6 workers · [x] ningún N/A sin motivo.
- C4 ter N/A: no existe `harness/rutas_sensibles.json`.
- C5 [x] T1–T24 `[x]`, commit `F-023 Tn:` por tarea · [x] árbol limpio ·
  [x] `features.json` en `in_progress`.

## Cambios de la pasada 1 (resumen) y pasada 2

Pedidos: (1) comando exacto de M2/M3 en `current.md`; (2) partir la línea de
`app.py:1653` (salto perdido, 125 columnas); (3) traza RED real de R7 y R36.
Delta `df72dcc..5d9a3ce`: `a2ef047`, `976f67a` y `5d9a3ce` (más el commit de
la review 1). Solo cambian `app.py`, `current.md` e `impl_F-023.md`.

- (2) [x] `git diff -w` sobre `services/` **no** sale vacío: `-w` no ignora
  saltos de línea. Por eso lo comparé por AST: el `app.py` de `df72dcc` y el de
  HEAD tienen **AST idéntico**. Recálculo en HEAD: 28 ficheros, 1.505 líneas
  (+2 por el salto), **214 mutantes**, el mismo único mutante en `app.py`.
  Código idéntico ⇒ la campaña sobre `ad48d2d` **sigue valiendo** (RM1). No
  se repite. Los 29 tests de `test_f023_catalogo_empresa.py` pasan en HEAD.
- (1) [x] M2: dos `SELECT` de solo lectura por `/api/sql/read` (cabecera del
  `hmo` de obra/año/mes con `emp`/`tip`, y `MAX(cod)` por empresa) con el
  resultado esperado. La function key se pide por consola y no queda en ningún
  fichero. M3: el POST, un `SELECT` sobre `partes` con el DNI escrito en
  consola, la consulta de `res`/`con` en Sigrid y el resultado esperado. C4 [x].
- (3) [x] R7: 12 FAILED con `NotImplementedError` en copia aislada. R36:
  12 FAILED de coherencia, y con `verificar_recurso = return None` fallan los
  dos tests de pipeline por la razón correcta (`[1..6] == [1, 6]` y el motivo
  «otra empresa»). Es la verificación ausente. C4 bis RED [x].
- `bash harness/init.sh` tal cual: **exit 0**. Raíz 416 passed / 1 skipped,
  sv1–sv5 en verde, cobertura [OK] 99,8 %, tamaño [OK] (impl 220/220).
  Árbol limpio. Con esto, C3 estilo [x] y todos los checkpoints en [x] o en
  N/A justificado.

## Observaciones (no bloquean)

- Arranque en frío con Sigrid caído: índice vacío ⇒ las líneas no congeladas
  **sin obra** pasan a `sin_recurso` (antes conservaban `emp.reside`). No llega
  a Sigrid y se corrige en la pasada siguiente.
- «Añadir línea»: elegir la obra después del trabajador no limpia una ficha de
  otra empresa (en «+ Nuevo» sí). sv5 la omitiría (R36).
- `partes_existentes` localiza el `hmo` por `obride`: un parte antiguo mal
  firmado se reutilizaría; la exploración §2 dice que no hay ninguno (M1).

## Automejora propuesta (no aplicada)

`reviewer.md`, RM4: copiar un solo servicio rompe los tests que leen
`../../infra`; copiar el repo o deseleccionarlos, y correr la base antes que el
mutante (aquí casi da un falso «muerto»). Genérico: portar a `arnes-base`.
