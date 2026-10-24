<!-- progress/review_F-060.md -->
Revisión incremental desde d5d7431 (pasada 2) · `git diff d5d7431..3cdc017` (pasada 1: `0926857...4f102aa`)

# Review F-060 · Racha de incidencia con CIZ móvil

**Veredicto: APPROVED** (pasada 2 de 2)

**Nivel de rigor: `critico`** (declarado en `features.json`): C1–C5, C3 bis, C4 bis con fase RED,
cobertura ≥ 80 %, mutación con 0 supervivientes salvo los que acepte el humano, RM1–RM6 (RM5 de
`critico`) y MANUAL en `current.md` con comando exacto.

## Pasada 1 (resumen; texto íntegro en `git show d5d7431:progress/review_F-060.md`)

CHANGES_REQUESTED sobre 4f102aa. El código cumplía la spec (sin `DELETE`, `UPDATE` con WHERE
optimista y doble guarda, CAS idempotente), pero: (1) M1–M3 sin comando exacto en `current.md`;
(2) **divergencia de R26**: con `MOVER_CIZ` apagado, sv4 ya usaba la regla nueva (V 1–4 y trabajo
el 5 ingeridos, aprobando 2, 3 y 4 de uno en uno: dev 0926857 daba 1 CIZ y F-060 apagado, 3), y la
documentación vendía el apagado como vuelta atrás; (3) «PENDIENTES DE ACEPTAR» desfasado; (4) RM5
sin demostraciones versionadas. Observación: la papelera de los días saltados no viajaba.
Humano (2026-10-24, literal): «c y si a 2» ⇒ DA12 = C y DA13 = sí.

## Pasada 2 · los cuatro cambios

1. **[x] M1–M3 con comando exacto** (`current.md`): arranque de sv5 (`OBRA_PRUEBAS_FORZAR` y
   `MOVER_CIZ`) y sv4 en local, con `/health` y PARA si no está en pruebas; lecturas L (`partes`
   local), S (`/api/sql/read`, solo lectura) y V (`verificar`/`estado` con `ANO, MES`); pasos del
   portal; lo esperado tras cada día; `limpiar`, `limpiar --ejecutar`, `estado` y `git checkout`.
   Comprobado contra el código: puertos 8005/8014, `ca-sv4-front`/`ca-sv5-transfer`, fases de
   `prueba_escritura_sigrid.py`, texto del INFO `ciz movido`, motivos `fin_movido` e intermedio.
2. **[x] R26 resuelta con DA12 = C y verificada por mí** (sin fiarme del test del implementer):
   - `_rol_incidencia_anterior` frente a `git show 0926857` (l.2217–2280): `diff` = solo el nombre
     y una línea del docstring.
   - **Diferencial base frente a HEAD apagado**: `git archive` de sv4 en 0926857 y en 3cdc017 al
     scratchpad, 600 escenarios al azar con semilla (1–3 personas con y sin DNI, V/B/trabajo/
     mixtos, papelera, documentos inactivos, estados, mes anterior, dos obras, aprobación de un
     subconjunto) ⇒ `lineas_para_registro` da un payload **byte a byte igual** (2.660 líneas: 995
     `inicio`, 643 `intermedio`, 546 `fin`) quitando solo las dos claves nuevas, que van vacías.
   - El único llamante (`app.py:2369`, preflight y ejecutar) pasa `settings.mover_ciz`; sv5 con la
     lista vacía no lee nada aunque esté encendido (`registro_pipeline.py:460-469`). Con el orden de
     encendido sv5→sv4 y de apagado sv4→sv5, el estado intermedio es siempre el de dev 0926857.
   - Frases corregidas: `settings.py` de sv4 y sv5, ARCHITECTURE semántica 4, `partes-proyecto.md`
     l.225, l.551-556 y variables, `azure-apps/partes.md` (commit local 44886eb, sin push) y la
     vuelta atrás de la M4 (sv4 y luego sv5). «Como antes de F-060» solo queda donde es verdad.
3. **[x] Papeleo**: «aceptados por el humano (2026-10-24, «acepto»)» en `tasks.md`, `current.md` e
   `impl_F-060.md`; `grep "PENDIENTES DE ACEPTAR"` sin resultados fuera de la cita de T21.
4. **[x] RM5**: `progress/equivalentes_F-060.py` ejecutado por mí: sv4 «4 mutantes, 0 distintos»
   y sv5 «2 mutantes, 0 distintos» (5.000 escenarios del pipeline, invariante #12 en 200.000
   llamadas, 11.467 `mover`, todas con `hmoide`), exit 0. Citado en `mutacion_F-060.md`.

## Checkpoints (pasada 2)

- **C1** [x] `bash harness/init.sh` exit 0 (abajo) · [x] ficheros del arnés.
- **C2** [x] solo F-060 `in_progress` · [x] rama de la feature · [x] `current.md` con la sesión y la
  decisión literal del humano · [x] `history.md` sin cambios (no está `done`).
- **C3** [x] hexagonal: `racha_incidencia.decidir` (DA13) puro en `application/`; interruptor en
  `config/` e `interface_adapters/`; SQL solo en `infrastructure/` · [x] primera línea con ruta en
  los ficheros nuevos (`test_f060_interruptor_sv4.py`, `equivalentes_F-060.py`,
  `mutacion_F-060_enmienda.md`) · [x] sin `print`, TODOs, secretos ni dependencias.
  **LÍMITE DE SERVICIO** [x]: la copia de `_rol_incidencia` es del propio sv4 (su código de dev),
  no cruza servicios; ninguna copia de la lista cerrada tocada.
- **C3 bis** [x] sin documento nuevo en `docs/referencia/` · [x] sin PDF ni ofimática · [x] barrido
  de las líneas añadidas (correos, IPv4, GUID, DNI, `password|secret|token|AccountKey|sig=`), aquí
  y en 44886eb: solo `127.0.0.1`, `$KEY` y valores de test · [x] nada que redactar.
- **C4** [x] R1–R32 con tests (tabla abajo); R26 bis con 16 tests (18 casos) en
  `test_f060_interruptor_sv4.py` y los dos casos de T18; R9/DA13 con 5 nuevos · [x] sin red ni
  BBDD (SQLite en memoria) · **[x] MANUAL con comando exacto** (cambio 1).
- **C4 bis**
  - [x] `rigor: critico` · [x] fase RED con traza real de T16 (13 failed) y T17 (4 failed); T18
    caracteriza R26 (verde de entrada, declarado).
  - [x] `PUERTA COBERTURA` [OK] 99,7 % (338/339).
  - [x] Recálculo puro de la campaña de la enmienda: `alcance_de_feature(base="4f102aa")` = **5
    ficheros, 120 líneas, 30 mutantes**, igual que el informe; los 6 supervivientes existen con el
    mismo operador y texto (`:179`, `:184`, `:2320`, `:2331`, `:2346`, `:2353`).
  - [x] «Tiempo total» 5.517 s > 60 s: **campaña no reejecutada (92 min según el informe)**; me
    quedo en el recálculo, RM1–RM6 y la RM4 de abajo.
  - [x] Sin «NO VÁLIDA», base rota 0, 4 líneas base. **RM1** [x]: mide `ef2b5c5`;
    `ef2b5c5..3cdc017` solo toca tests, `progress/` y `tasks.md`. **RM2** [x]: 5.517 × 4 ÷ 30 =
    736 s/mutante frente a ~520 s de base: más caro que la base, nunca un salto a la baja (máquina
    cargada; la de T13 dio 409,6 frente a ~461). **RM3** [x]: ningún equivalente sale muerto.
    **RM5** [x] (cambio 4). **RM6** [x]: ninguna guarda quitada; T23 no toca producción.
  - [x] Los 5 tests nuevos de T23 caen con su mutante según el informe, y su razonamiento cuadra
    (la copia de dev 0926857 no se toca: caracterizan su tope de 50 filas y la rama sin DNI).
  - [x] «Evidencias» con los cuatro números y **workers 4** en las dos campañas.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T1–T13 y T15–T24 `[x]` con commit `F-060 Tn:` (T16 6c4220b … T23 3cdc017); T14 `[ ]`
  legítimo (MANUAL del humano) · [x] árbol limpio · [x] `features.json` coherente (`in_progress`).

## Las dos preguntas del líder sobre T23

**¿Basta una campaña limitada al delta de la enmienda?** Sí, y no lo doy por supuesto. El riesgo
real no es el que cubre la nota de alcance: con DA12, los tests de F-022, F-025, F-046… que llaman
a `lineas_para_registro` sin `mover_ciz` pasan a ejercitar la regla vieja, así que un mutante de
`_roles_de_racha`/`_historico`/`racha_incidencia.py` que en T13 solo mataran ellos sobreviviría
hoy. **RM4** sobre una copia en el scratchpad: los **132 mutantes de sv4 en líneas de T13 que la
enmienda no tocó** (100 de `racha_incidencia.py`, 32 de `parte_repository.py`), contra los tres
ficheros de tests de F-060 de sv4 (piden `MOVER_CIZ` encendido): **128 muertos, 1 timeout**
(`:204 while padre[i] == i`, el mismo de T13, detectado) **y 3 vivos = #4, #7 y #8**, los
equivalentes ya aceptados. Los tests de F-060 encendidos matan por sí solos todo lo que mató T13.
sv5 no cambió producción en la enmienda (solo un comentario). Worktree limpio tras la prueba.

**¿Cabe el superviviente [1] (`:179 f = int(l.fecha_int or 0) → or 1`) en la aceptación del #6?**
Sí. Mismo texto y operador, y lo que el humano aceptó es que **el operando nunca se evalúa**:
`LineaHist` tiene un solo productor (`_historico`, l.2440, tras `fecha_int.between(desde, hasta)`,
que excluye NULL y 0) y `decidir` un solo llamante (l.2392, con `int(r.fecha_int)` de una fecha
verdadera). Eso no depende de que `f` vaya luego a `in racha` o al rango de DA13, y aun así `0` y
`1` quedan fuera de `primero >= 10101`. El diferencial versionado lo aplica sobre la línea nueva
(20.000 entradas con fechas `None`/`0`/`1`, 0 distintos). No es un equivalente nuevo; conviene que
el líder se lo cuente al humano al cerrar (informativo, no bloquea).

## Puntos críticos (sobre el delta)

- **R22** [x]: el delta no añade `DELETE` ni `INSERT`; de sv5 solo cambia un comentario de `settings`.
- **R21** [x]: `stmt_mover_linea` y sus guardas no cambian desde la pasada 1.
- **R26 / R26 bis** [x]: apagado = dev 0926857 en sv4 (diferencial) y en sv5 (R26 de la pasada 1 y
  `test_f060_r26_extremo_a_extremo_con_sv4_apagado[False|True]`: un solo CIZ, el del 4).
- **R28/R29** [x]: `_fin_movido` se aplica siempre (un resultado en vuelo con sv4 ya apagado).
- **Logs** [x]: el delta no añade logs; el INFO de roles que ya existía solo lleva ids.

**Requisito → nº de tests `test_f060_rN_*`**: R1 4 · R2 5 · R3 8 · R4 4 · R5 2 · R6 6 · R7 8 · R8 2 ·
R9 20 · R10 12 · R11 3 · R12 2 · R13 12 · R14 6 · R15 7 · R16 3 · R17 5 · R18 4 · R19 7 · R20 11 ·
R21 2 · R22 3 · R23 6 · R24 2 · R25 1 · R26 5 · R26 bis 16 · R27 7 · R28 9 · R29 3 · R30 1 ·
R31 revisión (cambio 2) · R32 MANUAL (T14).

**Ejecución** (pasada 2, sobre 3cdc017): `bash harness/init.sh` exit 0 · raíz 498 passed, 3 skipped
(116,7 s) · sv4 **2722 passed**, 1 skipped (962,1 s) · sv5 en verde (caché) · sv1–sv3 en verde
(caché) · `PUERTA COBERTURA` 99,7 % · `PUERTA TAMAÑO` OK · «ENTORNO LISTO».

## Observaciones (no bloquean)

- `tasks.md` T23 conserva como verificación `python -m harness.mutacion --feature F-060` (campaña
  completa) y se hizo con `--base 4f102aa`: está justificado en `mutacion_F-060_enmienda.md` y lo
  cubre la RM4 de arriba. Sigue en pie la de `persona_de` y el DNI con tabulador (pasada 1).

## Automejora (propuesta al humano, no aplicada)

`CHECKPOINTS.md` C4 bis / RM1: cuando una campaña se limita al delta (`--base`) porque cambió
producción tras la completa, exigir que se compruebe que **los tests que mataban los mutantes de
fuera del delta siguen ejercitando ese código** (un interruptor como DA12 manda los tests de otras
features por otra rama). Una RM4 como la de arriba (132 mutantes contra los tests de la feature,
unos 40 min) es la forma barata de hacerlo.
