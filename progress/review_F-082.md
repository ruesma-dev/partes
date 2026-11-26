<!-- progress/review_F-082.md -->
Revisión incremental desde 3e76c87 (pasada 2) · `git diff 3e76c87..5a897d3` (HEAD 5a897d3)

# Review F-082 · El portal siempre ofrece «Sin partida» al editar la partida

**Veredicto: APPROVED** (pasada 2, carril `estandar`). **SHA aprobado: 5a897d3.**
Pasada 1: CHANGES_REQUESTED sobre 78957b7 (ciclo 1 de 2), con dos cambios: el test del
eslabón servidor de A2 y las MANUAL en `current.md`. Los dos están resueltos.

**Nivel de rigor: `estandar`** (declarado; D1 de la PARADA 1). Exige fase RED y cobertura;
mutación y capa e2e son informativas. El delta no toca `harness/rigor.local.json`. No hay
pasada de evidencias: la capa e2e es N/A y no hay Python de producción.

## Pasada 2 · delta revisado

- **Producción: 0 líneas.** El delta (commit 5a897d3) toca `test_f082_sin_partida.py` (+58),
  `progress/current.md` (+10) y `progress/impl_F-082.md` (+35, «Ciclo 2»). No invalida nada
  de lo aprobado en la pasada 1: ni firmas, ni ficheros movidos, ni alcance medido.
- **Cambio 1, resuelto.** Hay tres tests nuevos sobre el repositorio real (SQLite de
  `tests/dobles.py`):
  - `test_f082_a2_servidor_partida_vacia_queda_manual`: con leída `0716` y método `sin`, los
    cuatro null ⇒ campos None y método `manual`, la leída se conserva, y `undo_last` devuelve
    `(None, "sin")`.
  - `test_f082_a2_servidor_d3_ya_sin_partida_se_guarda_igual`: D3, dos veces seguidas ⇒
    `manual`.
  - `test_f082_a2_servidor_entrada_f072_sigue_fija`: R32 ⇒ `PartidaFijaError` y la partida
    fija intacta.

  Las aserciones son concretas (la tupla entera). El `check=False` añadido a `subprocess.run`
  no cambia nada: el `returncode` se comprueba justo después.
- **Los tests nuevos cazan la regresión: mutación a mano.** En una copia de HEAD en el
  scratchpad cambié `set_registro_partida` a `reg.partida_match_method = "manual" if
  partida_ide is not None else None` ⇒ `2 failed, 14 passed`: caen los dos tests de partida
  vacía, que es justo el hueco del cambio 1. El árbol de trabajo no se tocó.
- **Cambio 2, resuelto.** `progress/current.md`, sección F-082, lista las 4 verificaciones
  MANUAL (humano): Ctrl+F5, página, acción y resultado esperado. Cubren el ✎ en obra, parte y
  trabajador, «Editar partida» en bloque, la obra sin presupuesto y Deshacer.

## Lo que ejecuté yo (pasada 2)

- `python -m pytest tests/test_f082_sin_partida.py tests/test_f072_repositorio.py` (sv4)
  ⇒ `29 passed` (16 de F-082).
- `bash harness/init.sh` tal cual (encargo del líder) sobre 5a897d3: **exit 0, `ENTORNO
  LISTO`**.
  - Raíz ejecutada: `2549 passed, 50 skipped in 1418.24s`.
  - **sv4 ejecutada entera** (su caché se invalidó con el test nuevo): `4033 passed, 1
    skipped in 1249.78s`.
  - sv1, sv2, sv3 y sv5 por caché: no cambian.
  - `COBERTURA` N/A con motivo, `TAMAÑO` OK (impl 159/220), `CARRIL` N/A y `CAPA E2E` N/A.
- **Test ajeno e inestable, según el líder**: una ejecución de init.sh del implementer cayó en
  `tests/test_f059_ejecucion.py::test_f059_r7_el_arranque_va_antes_y_se_para_al_terminar`
  (caso TIMEOUT), que pasó 3 de 3 suelto y en verde al repetir. En mi ejecución pasó: la raíz
  sale entera en verde. F-082 no toca nada de F-059 (harness/e2e). Queda anotado como
  observación O4.

## Pasada 1 · resumen de lo ya aprobado (78957b7)

- **Fase RED reproducida.** Con `git archive 2f033d9` en el scratchpad ⇒ `8 failed, 5
  passed`, los mismos 8 del informe.
- **El selector.** La fila «— Sin partida —» de `buildPartidaPicker` se pinta fuera de
  `filtrados()`, así que sale siempre: con texto que no casa, con chip y en obra sin
  presupuesto. Va en los dos usos (✎ de celda y «Editar partida» en bloque) y manda los
  cuatro campos a null.
- **Las plantillas.** Solo añaden la rama `manual` dentro del `else`. No cambian los otros
  métodos, ni la leída no encontrada, ni las entradas F-072 (primera rama), ni las congeladas
  (sin ✎ y con 409).
- **Fuera del diff.** Sin backend ni sv3. sv3 no re-casa las líneas `manual`
  (`partida_conciliador.py:149-151`).
- **Mutación (informativa).** `alcance_de_feature('F-082')` ⇒ 0 líneas y 0 mutantes; el cero
  es legítimo, porque el diff de producción es solo JS y Jinja2.

## Checkpoints

- **C1** [x] init.sh en verde (tal cual por encargo; esta vez sv4 y la raíz se ejecutaron sin
  caché efectiva). [x] Ficheros base presentes.
- **C2** [x] Una sola activa (F-082). [x] Orden: la cola del 2026-11-23. [x] Rama
  `feature/F-082-opcion-sin-partida`. [x] `current.md` solo con la sesión activa.
  [x] Historia de lo `done`.
- **C3** [x] Hexagonal: static, templates y tests. [x] Cabecera de ruta en `app.js` y en el
  test; las plantillas no la llevaban ya antes (`{% extends %}`), no es regresión. [x] Sin
  prints, TODOs, secretos ni dependencias nuevas. [x] Trampas de dominio: no aplican.
- **C3 bis / C3 ter** N/A: no entra documento externo ni acta de conversación.
- **C3 quater** N/A: no cambia lo que sv4 expone ni consume.
- **C4** [x] Cada `acceptance` tiene tests y pasan (tabla). [x] Sin red ni BBDD (node,
  Jinja2 y SQLite en memoria). [x] MANUAL en `progress/current.md`. [x] Dobles: los tests
  usan los del árbol (`FabricaSesionSqlite`, `_repo`), y la barrida de init.sh pasa.
- **C4 bis** [x] `rigor` declarado. [x] RED real y reproducida. [x] Cobertura N/A con motivo
  impreso. Mutación: N/A por nivel (informativa) y 0 mutantes recalculados. RM1–RM7 y
  supervivientes: N/A por carril `estandar`. [x] «Evidencias» completas. Capa e2e: N/A,
  ningún servicio la declara.
- **C4 ter** N/A: init.sh no señala rutas sensibles.
- **C5** `tasks.md` N/A (sdd=false); commits `F-082 T1/T2` y ciclo 2 con prefijo.
  [x] Árbol limpio. [x] `features.json` en `in_review`.

## Cobertura (acceptance → test)

| Criterio | Tests | Estado |
|---|---|---|
| A1 Los dos selectores ofrecen «Sin partida», también sin presupuesto | `test_f082_a1_*` (5): picker ejecutado en node (con partidas, filtro, chip CI y obra vacía) y cableado de los dos usos | cubierto |
| A2 Elegirla deja la línea sin partida y sin aviso | JS ⇒ PATCH con los cuatro null; `test_f082_a2_servidor_*` (3): `manual`, D3, undo y R32; celda `manual` sin ⚠ ×3 plantillas; regresión del resto ×3 | cubierto |
| A3 init.sh verde + APPROVED | init.sh de la pasada 2 y este veredicto | cubierto |

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean)

- O1. Cambiar luego la obra del parte re-casa la línea por su leída y pierde el «sin partida»
  manual (`parte_repository.py:4190-4208`); también se pierde con un reproceso que cree un
  documento nuevo. Ya pasaba antes con cualquier partida manual.
- O2. `test_f082_a1_los_dos_selectores_usan_el_picker` es una búsqueda de texto. Es aceptable
  porque el picker se ejecuta de verdad en los otros cuatro tests.
- O3. En bloque, una selección que incluya una entrada F-072 aplica las demás líneas y saca
  un mensaje genérico. Ya pasaba antes con cualquier partida.
- O4. `test_f059_r7_el_arranque_va_antes_y_se_para_al_terminar` es intermitente por TIMEOUT
  bajo carga (lo cuenta el líder; en mi ejecución pasó). Es ajeno a F-082. Conviene abrir una
  feature o una nota en el backlog para estabilizarlo.

## Automejora (propuesta, no aplicada)

- `leader.md` debería decir explícitamente qué manda cuando el encargo pide `init.sh` tal cual
  y `reviewer.md` pide `ARNES_SIN_CACHE=1` (con suites de más de 10 min).
