<!-- progress/review_F-031.md -->
Revisión completa (pasada 1) · `dev...HEAD` (HEAD `20420a0`; alcance propio desde `9a00ce3` + commits de spec)

# F-031 · Review

**Veredicto: CHANGES_REQUESTED** (dos cambios pequeños; lo demás, verificado, se da por bueno en la pasada 2).
**Rigor:** `critico` (declarado): RED, cobertura ≥ 80 %, mutación completa con 0 supervivientes y MANUAL con comando.
Ninguna escritura en Sigrid ni en `partes`; ni worktrees ni copias dentro del árbol.

## Qué se ejecutó (resultado real)

- `bash harness/init.sh` tal cual: **ENTORNO LISTO**, exit 0. PUERTA COBERTURA 99,6 % (239/240), PUERTA TAMAÑO OK,
  raíz 445 passed y 1 skipped. Avisos previos: F-014 blocked, ruff, infra sin tests.
- **Sin caché**, sobre una copia `git archive 20420a0` en el scratchpad (`-p no:cacheprovider`): sv5 **520 passed**;
  sv4 **1671 passed, 1 skipped** (el skip es `test_f017_punto_unico` «sv4 no tiene capa …»: `git archive` no copia
  directorios vacíos; el implementer informa 1672 passed en el árbol real).
- M1 y M2 (solo lectura, `/api/sql/read`), ejecutadas por mí: 0696 01/2026 ⇒ `PT26/00004 · Imputado · 308 linea(s)
  (0 nuestras)`, `asiento ANA26/00017: cuadra`; 0404 07/2026 ⇒ `PT26/00296 · En registro · 0 linea(s)`. Coinciden
  con design §11. Cubre la D3 del informe (el implementer no las ejecutó). `git status` limpio después.

## Roturas deliberadas (copia fuera del repo; `romper.py` en el scratchpad): 32, la suite caza 31
- **Parte destino (9/9 cazadas):** coger el En registro de menor `ide`; Imputado no contado como cerrado; elegir el
  último parte sin mirar el estado; no marcar nunca complementario; R11 invertido; pisar también en cerrados; omitida
  que conserva la cuenta; leer líneas solo del elegido; `parte_cod` del elegido en vez del del choque.
- **Alta protegida (11/12 cazadas):** quitar el `NOT EXISTS` de En registro; año y mes cambiados de sitio en sus
  parámetros; quitar el reintento; exigir el código propio al releer; `creado` sin mirar las filas; no fallar tras
  dos intentos; reintentar con el mismo código; `hmo` sin `NOT EXISTS`; releer aceptando un Cerrado; quitar el
  `UPDLOCK` del código libre; releer al estilo `partes_existentes`, sin estado. **SOBREVIVE: mandar el alta en dos `escribir`** (`for s in stmts: escribir([s])`, dos transacciones). Ver el cambio 1.
- **Respaldo de cuenta (8/8 cazadas):** que la partida mande sobre el recurso; admitir `CP`; admitir `IN…`; quitar
  `upper()`; leer partidas siempre; desactivar el respaldo; respaldo sin nota; envolver en `try` la lectura de
  partidas.
- **Herramienta (2/2) y `app.js` (4/4):** tolerancia `>=`; asiento de no-Imputados; sin `esc()` (×2); sin rótulo; notas
  de no-`escribir`.

## Decisiones del humano verificadas

1. **Parte destino:** `elegir_parte` toma el mayor `ide` En registro, y «cerrado» es `est != est_registro` (vive solo
   ahí). El complementario se crea si no hay ninguno En registro y nada toca `con`/`hmo` del original
   (`test_f031_r5_*`, `r31`). El paso 7 lee las líneas de todos los partes del periodo. Choque con un cerrado ⇒
   `omitir` `parte_cerrado: …` con `caa_*` vacíos; `pisar_claves` solo ve partes En registro. El modal rotula el
   complementario y pinta el aviso escapado. OK.
2. **Cuenta:** `origen_subcuenta` prueba primero el recurso (F-021) y luego la partida `CI*`/`CD*`; si no hay ninguna,
   `(None, None, None)`. Los `test_f021_*` no aparecen en el diff y están en verde. OK.
3. **sv5 no contabiliza:** nada sobre `asa`/`apa`/`apu`/`asi` ni `UPDATE con`. OK.
4. **Alta protegida:** comparé por AST el `return` de `stmts_crear_parte` con `porcentajes` en `40b9feb` y en su `dev`
   actual: **idéntico en los dos** (SQL, 14+7 parámetros, mismo orden). `_tip`/`_est` se inicializan igual.
   Relectura con `elegir_parte`, un reintento con `siguiente_cod_pt` y `RuntimeError` antes del paso 9: mismo esquema
   que `porcentajes` `_crear_parte`. Única diferencia: aquí `creado` exige además `filas > 0` (lo pide R43, más
   estricto). Los tests de carrera con `alta_protegida`/`al_alta` cubren R43–R47. Hueco en R40: cambio 1.
5. **Herramienta de solo lectura:** solo llama a `cliente._read` (`POST /api/sql/read`) y sus 5 sentencias son
   `SELECT`. `test_f031_r38_*` comprueba la URL y que no hay `.escribir(` ni `/api/sql/write`. La ejecuté sin
   escribir nada.
6. **D1:** un token en `test_f002_r20` y sigue vigilando la lectura bajo lock. **DA10:** `r32` sigue fijando empresa
   28, tipo, estado, código, descripción y fecha de la fila (`[:6]`); `r34` sigue exigiendo el filtro
   `cod/tip/emp` y `params[-3:] == [cod, 35, 28]`. La lista completa de parámetros la fija `test_f031_cliente_alta`.
   No se pierde nada. **DA11:** entre `9b202e9` (el `COMMIT_COPIADO` de `porcentajes`) y HEAD, los dos ficheros
   cambian solo en el docstring (+18, 0 borrados). El aviso de `progress/current.md` es exacto. **D2** (función
   anidada para no romper `test_f022_r27`): aceptable. **D3:** cubierta (ver arriba).
   **Dec. 4** (dos meses nuevos con el mismo `PT` en el preflight se arreglan con el reintento): aceptable. Queda la
   observación O1.
7. La lista cerrada de `CLAUDE.md` está intacta (`CLAUDE.md` fuera del diff). No se tocan sv1–sv3, `infra/`,
   `interface_adapters`, `reglas_registro`, `coherencia_recurso` ni `prueba_escritura_sigrid`. Barrido del diff sin
   DNIs reales, GUID, claves ni cadenas de conexión: solo el sintético `12345678Z`. El único `print(` es la salida de
   la herramienta de consola. `azure-apps`: commits locales `ef43cac` y `b09865f` (§3.5 y «qué se rompe si cambia»),
   sin push y al día con v5.

## Mutación (C4 bis, RM1–RM6)

- Recálculo puro con `harness.alcance` + `generar_mutantes`: **7 ficheros, 654 líneas, 129 mutantes**; coincide con el
  informe. Por fichero: pipeline 67, herramienta 38, estado_parte 10, write_client 7, cuenta 2, settings 2, models 3.
- Campaña **no reejecutada**: 427,8 s según el informe (> 60 s). En su lugar, RM4 sobre la copia: reproduje 3 mutantes
  del generador (`registro_pipeline.py:320` `!=`→`==` y `:410` `and`→`or` en dos sitios) más la tolerancia
  `>`→`>=`. **Los 4 mueren.**
- **RM1:** SHA medido `31f13f9`. Después solo cambian `progress/` y `tasks.md`; ningún fichero del alcance. OK.
- **RM2:** línea base 14,2 s; media 3,3 s × 6 workers = 19,8 s por mutante, del orden de la base. Total ≈ 129 × 3,3.
  Coherente.
- **RM3/RM5:** N/A justificado: ningún equivalente declarado y 0 supervivientes. Sin «⚠ CAMPAÑA NO VÁLIDA»; base
  rota = 0. **RM6:** el `or 0` quitado iba sobre `COUNT(*)` y `SUM(CASE … ELSE 0)` de un `GROUP BY`: nunca son NULL,
  y la SQL que construye el dato está en la misma función. OK.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros del arnés. **C2** [x] una `in_progress` · [x] rama de F-031 · [x]
  `current.md` de la sesión · [x] `done` en `history.md`.
- **C3** [x] hexagonal: `estado_parte` y `cuenta_analitica` solo importan dominio; la herramienta es un punto de
  entrada como `main.py` · [x] primera línea con la ruta · [x] sin prints de debug, secretos ni dependencias nuevas
  · [x] trampas: el recurso sigue en `reside`; incidencias y ORM no se tocan.
- **C3 bis** [x] solo `partes-proyecto.md` (no es externo nuevo); barrido DNI/GUID/claves del diff: limpio.
- **C4** [ ] **cada requisito con un test que lo cubra: R40 no** (cambio 1). El resto está trazado (tabla) ·
  [x] sin red ni BBDD · [x] M1–M6 en `current.md` con su comando.
- **C4 bis** [x] rigor declarado · [x] RED con trazas reales (`impl` §4, `red_F-031.md`), incluida la v5 contra
  `7276ff3` · [x] cobertura 99,6 % · [x] mutación 129/129 recalculada · [x] muertos: recálculo + RM4 (dicho arriba)
  · [x] coste por mutante 19,8 s > 1 s · [x] sin cabecera de campaña no válida · [x] RM1 · [x] RM2 · [x] RM5 N/A
  (sin equivalentes) · [x] RM6 · [x] campaña automática, no manual · [x] 0 supervivientes · [x] «Evidencias» con
  los cuatro números y 6 workers · [x] ningún N/A sin motivo.
- **tasks.md:** T1–T32 `[x]`, con commits `F-031 Tn:`. T16 pedía M1/M2 al implementer: hechas ahora por el reviewer.

## Cobertura requisito → test (`services/partes-transfer/tests/`, salvo sv4)

| R | Test |
|---|---|
| R1, R2, R3, R4, R7, R18 | `test_f031_estado_parte.py`; `test_f031_pipeline_estado.py::r1_*`, `r2_*`, `r3_*` |
| R5, R6, R8, R10–R17, R19, R31–R33 | `test_f031_pipeline_estado.py::r5_*` … `r33_*`; `test_f031_mutantes.py` |
| R20–R27 | `test_f031_cuenta_partida.py`, `test_f031_pipeline_cuenta_partida.py`; `test_f021_*` (R27) |
| R28–R30 | `services/partes-front/tests/test_f031_preflight_avisos.py` (node) |
| R34 | suites de F-004 y F-024 sin cambios, en verde |
| R35–R38 | `test_f031_comprobar_asiento.py` |
| R40 | `test_f031_pipeline_alta.py::r40_*`. **Parcial: no ve el corte en dos `escribir`** |
| R41, R42 | `test_f031_cliente_alta.py` |
| R43–R47 | `test_f031_pipeline_alta.py::r43_*` … `r46_*`, `r43_r47_*` |
| R39, R48, R49 | lectura del reviewer: docs y cabeceras. Frase obsoleta: cambio 2 |

## Cambios requeridos

1. **R40 sin test real de «una llamada a `escribir`».** `SigridConSql.stmts_crear_parte`
   (`tests/test_f031_pipeline_estado.py:205-208`) y `SigridFake.stmts_crear_parte` (`tests/dobles.py:461`) meten
   cabecera y `hmo` en **un único** elemento. Por eso `test_f031_pipeline_alta.py:58-76` no distingue un pipeline que
   parta la lista en varias `escribir` ni uno que cambie su orden. Si alguien lo hace, en Sigrid queda un `con` sin
   `hmo` (un huérfano por intento) y el alta acaba en `RuntimeError`. Añadir un test con un doble cuyo
   `stmts_crear_parte` devuelva **dos** elementos, como el cliente real (vale apuntar los SQL reales de
   `SigridWriteClient`). Debe exigir que `_crear_parte` los mande en **una sola** llamada a `escribir`, en orden
   `[con, hmo]` y sin otras sentencias en ese lote. Comprobar que se pone en rojo con la rotura «`for s in sts:
   escribir([s])`» y anotar la traza en `progress/red_F-031.md`. Solo crecen los tests; `dobles.py` solo crece.
2. **Frase de la v4 que contradice la v5 (R39).** Hay que reescribirlas con la semántica de R43–R45: se relee el
   periodo, se usa el parte En registro que haya (propio o de `porcentajes`), un reintento con el siguiente código y,
   si tampoco, error sin líneas.
   - `docs/ARCHITECTURE.md:278-279`: «El parte creado se relee por código y En registro; si no sale, no se inserta
     nada».
   - `docs/referencia/partes-proyecto.md:224-225`: «y la relee (si no sale En registro con su código, no inserta
     nada)».

   (`azure-apps/partes.md` ya la quitó en `b09865f`.)

**Observaciones (no bloquean).** O1: dos meses sin parte en una petición reciben el mismo `PT` en el preflight; la
escritura lo arregla gastando el único reintento del segundo mes (futuro: reservar códigos consecutivos). O2: en M1,
ANA26/00017 tiene Debe 111.637,21 y Haber 111.577,21 (60 €): contrapartida, fuera de alcance (DA3).

**Automejora (propuesta para `reviewer.md`, no aplicada):** si un requisito fija un límite de transacción (una
llamada, un lote, un orden), comprobar que el doble no junta en un elemento lo que el cliente real da en varios.
