Revisión completa (pasada 1) · rama `feature/F-049-editor-calendario-normal-y-extra`, `git diff dev...HEAD` (merge-base `2bfeab7`), HEAD `f731012`
<!-- progress/review_F-049.md -->
# F-049 · Review (reviewer, 2026-10-23)

**Veredicto: APPROVED**

**Nivel de rigor: `critico`** (declarado en `harness/features.json`). Exige C1–C5, C3 bis,
fase RED, cobertura de lo cambiado ≥ umbral, campaña de mutación con **cero supervivientes**
sin justificación aceptada, RM1–RM6 (RM5 en su forma de `critico`) y MANUAL listadas con su
comando exacto.

## Verificación ejecutada por el reviewer (resultado real)

- `bash harness/init.sh` (worktree, HEAD `f731012`): exit 0, «ENTORNO LISTO». Raíz `498 passed,
  3 skipped`; `PUERTA COBERTURA [OK] 100.0% de 362 líneas cambiadas (umbral 80%, critico)`;
  `PUERTA TAMAÑO [OK]` (requirements 149/150, design 250/250, impl 123/220). sv1–sv5 salieron
  por caché, así que las dos suites tocadas se reejecutaron enteras sin caché
  (`-p no:cacheprovider`): **sv4 `2583 passed, 1 skipped` (134,6 s)**, **sv3 `2271 passed`**.
- `node --check services/partes-front/static/app.js`: OK.
- `git status` limpio antes y después (la reproducción de mutantes se hizo en una copia en el
  scratchpad, `git archive HEAD services/partes-front`).

## Checkpoints

**C1** — [x] init.sh exit 0 · [x] ficheros del arnés presentes.
**C2** — [x] una sola `in_progress` (F-049) · [x] rama `feature/F-049-…` · [x] `current.md`:
la sección F-049 es la sesión activa (el resto son secciones de otras features que el repo
conserva por costumbre, no restos de esta) · [x] las `done` siguen con su resumen en `history.md`
(esta feature no toca `history.md`).
**C3** — [x] hexagonal: `edicion_celda.py` es núcleo puro en `application/services` (solo
`math`, `dataclasses`, `collections.abc`); SQL en el repositorio; rutas en `app.py` ·
[x] primera línea con ruta en los ficheros nuevos (código y tests) · [x] sin `print`, sin
TODO, sin secretos (los DNI de los tests son sintéticos `000000NNA`; `PG_PASSWORD` de un test es
`"irrelevante-en-tests"`), sin dependencias nuevas · [x] reglas de dominio: empleado ≠ recurso
respetado (la extra nueva usa `_recurso_de` de la plantilla, `recurso_ide` y `empleado_reside`
de respaldo, sin consultar Sigrid si no hay recurso); incidencias fuera de la celda; esquema
sin tocar (`orm_models.py` intacto en sv3 y sv4).
**C3 bis** — N/A: la feature no añade ni modifica nada en `docs/referencia/` (comprobado en el
`--stat` del diff).
**C4** — [x] trazabilidad completa (tabla abajo), todo en verde · [x] sin red ni BBDD real
(SQLite de `tests/dobles.py`, cola y Sigrid falsos) · [x] M2–M8 en `progress/current.md`
(«F-049 · verificaciones MANUAL») con el orden de despliegue sv3 → sv4, el comando
`az containerapp revision list …` y las dos consultas SQL de solo lectura; M1 superada.
**C4 bis** —
- [x] `rigor` declarado (`critico`).
- [x] Fase RED con salida real en `impl_F-049.md` para T2, T4, T5, T6, T9, T10, T12 y T14
  (comando y línea `E …`); T13 justificada (solo caracteriza sv3).
- [x] Cobertura `[OK]` 100 % (362/362).
- [x] Mutación: `progress/mutacion_F-049.md` generado por la herramienta. **Recalculado por el
  reviewer** con `harness.alcance.alcance_de_feature("F-049")` + `generar_mutantes`: origen
  `rama` `2bfeab7..feature/…`, **775 líneas en 5 ficheros, 164 mutantes** (66 + 60 + 0 + 35 +
  3): coincide fichero a fichero.
- [x] Muertos: «Tiempo total» 44.292,9 s > 60 s ⇒ **campaña no reejecutada (≈ 12,3 h según el
  informe)**; vale el recálculo puro + RM1–RM6. Log completo leído (164 líneas de veredicto).
- [x] Coste por mutante = 44.292,9 × 1 ÷ 164 = 270,1 s (≫ 1 s).
- [x] Sin cabecera «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0; línea base en verde
  en los dos servicios (log: `[base] … en verde`).
- [x] RM1: medido sobre `4f73add`. Entre `4f73add` y HEAD solo cambian
  `test_f049_guardar_celda.py` (+36, los dos tests nuevos), `progress/*` y `tasks.md`: ningún
  fichero del alcance; el recálculo sobre HEAD da el mismo alcance.
- [x] RM2: W = 1; media 270,1 s × 1 frente a base sv4 413,9 s (mismo orden; más baja por `-x`
  con 162/164 muertos); 164 × 270,1 = 44.296 ≈ total. Timeout efectivo 828 s.
- [x] RM5: no hay ningún superviviente declarado equivalente: nada que reproducir.
- [x] RM6: no se quitó código defensivo; el superviviente 1 (`if reg is not None`) se mató con un
  test, la guarda sigue.
- N/A justificado · campaña manual: la automática dio 164 mutantes, no 0.
- [x] Supervivientes con análisis completado (ninguno `PENDIENTE`) y **cero sin resolver**: los
  dos eran huecos reales y los mata un test nuevo. **Reproducidos por el reviewer** (RM4, copia
  en scratchpad, `aplicar_mutante` de la herramienta con el mismo operador y texto):
  `parte_repository.py:3229` `if reg is not None:` → `if reg is None:` ⇒
  `test_f049_r26_r38_deshacer_sin_creadas_da_las_afectadas` falla (`assert [] == [{'obra_key':
  'obr-686', …}]`); `app.py:2245` `… or not reside:` → `… and not reside:` ⇒
  `test_f049_r21_extra_nueva_sin_recurso_no_pregunta_a_sigrid` falla (`('extra', 1.5, 31,
  'HE01') == ('extra', 1.5, None, None)`). Sin mutar, los dos pasan.
- [x] «Evidencias» con los cuatro números; los workers (`--workers 1`) constan en la sección T17
  del mismo informe y en la fila «Workers» del de mutación (ver Automejora 2).
- [x] Ningún N/A sin motivo.
- RM3 (criterio): recorridos los 162 muertos del log; ninguno es equivalente. Los dudosos se
  descartan: `synchronize_session=True` (valor inválido, lanza), `nueva: bool = False → True`
  (lo caza `…_validar_horas_por_defecto_no_es_nueva`), `> EPSILON → >= EPSILON` (distinguible con
  horas 0, lo caza `…_borde_exacto`), `frozen=True → False` (lo caza `…_son_inmutables`).
**C4 ter** — N/A: el repo no declara `harness/rutas_sensibles.json`.
**C5** — [x] `tasks.md` T1–T19 `[x]`; commits `F-049 Tn:` de T2 a T19 (T1 es el rebase sin código
propio, commit `fa47d4c` «F-049: estado in_progress…», aceptado) · [x] sin temporales ni
artefactos sin trackear · [x] `features.json` en `in_progress` y con el `acceptance` enmendado
(F-017 a 18, decisión del humano del 2026-10-22).

## Límite de servicio y lista cerrada (CLAUDE.md)

- sv5 intacto; de sv3 solo `recalculo_seguimiento.py::marcar_terminado` (+ tests F-049 y la
  inversión de F-043 R28). `congelacion.py`, `orm_models.py`, `jornada_resolver.py`,
  `seleccion_sigrid.py`, `coherencia_recurso.py` y los SQL gemelos, sin tocar: ninguna copia de
  la lista cerrada de duplicaciones cambia y no se crea lógica gemela nueva (sv4 pide, sv3 marca).
- Tests existentes tocados = exactamente la lista cerrada de design §3: (a) los dos dobles
  `undo_last(self, **_kw)`, (b) `test_f043_r28_…_marca_todo_documento_con_su_pedido` invertido,
  (c) `test_f017_…usan_el_helper` 17 → 18 (opción A, literal «a», enmendado en design §3 y en
  el `acceptance`). Nada más.
- `azure-apps`: commit local `08b5755` en `partes.md` (rutas, motivos, pedido compartido, orden
  sv3 → sv4); sin push, según la memoria del proyecto.

## Cobertura · requisito → test (todos `test_f049_…`, en verde)

| Req. | Test(s) |
|---|---|
| R1–R3, R10 | `r1_r10_una_fila_por_linea_y_extra_de_jornada`, `r1_r2_…`, `r2_…`, `r3_todas_congeladas_*`, `r10_regs_marcan_solo_las_extra_auto` |
| R4–R9 | `r4_sin_lineas_no_hay_popup`, `r1_r2_r5_popup_solo_extra`, `r6_*`, `r7_*`, `r7_r8_guardar_una_post_y_recarga`, `r8_*`, `r9_leyenda_de_la_matriz` |
| R11–R13 | `r11_*` (núcleo y ruta), `r12_*` (antes obsoleto, línea movida, nueva aparecida, plantilla distinta, papelera, celda vacía), `r13_*` |
| R14, R15, R33 | `r14_linea_congelada_es_409_con_su_motivo`, `r15_parte_en_espera_es_409`, `r15_espera_de_la_plantilla_tambien_con_nueva`, `e11_r33_…`, `r33_*` |
| R16–R20, R34 | `r16_todo_o_nada*`, `r16_una_entrada_…`, `e6_r17_…`, `e4_r18_…`, `e5_r18_…`, `r18_*`, `r19_*`, `e2_r20_r21_…`, `e10_r34_…`, `e9_*` |
| R21–R24 | `r21_*` (incl. el nuevo sin recurso), `r22_respuesta_ok`, `r23_*`, `r24_info_celda_sin_datos_personales` |
| R25–R28 | `r25_*`, `r26_*` (incl. el nuevo sin creadas), `r26_r27_deshacer_e12_…`, `r27_*`, `r28_*` |
| R29, R40 | `git diff --stat` revisado (arriba); `r40_e12a/b/c_*`, `r40_el_martes_…` (sv3) |
| R30 | `r30_*` (raíz, `tests/test_f049_contrato_motivos.py`) |
| R31, R32, R35–R39 | `r31_*`, `r32_aviso_de_reparto_pendiente`, `r35_*`, `r36_*`, `r37_*`, `r38_*`, `e12a_r38_…`, `e12b_r38_…`, `e12a_r39_…`, `r39_*` |
| R41, R42 | `r41_*` (incl. `e12d`), `r42_*` (sv3, adaptador real con SQLite) |

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean)

1. **Conflicto previsto al fusionar** en `BACKLOG.md` (`git merge-tree dev HEAD`: conflicto
   solo ahí; `features.json` se auto-fusiona). Es generado: tras el merge, regenerarlo con
   `bash harness/init.sh` (o `harness/backlog.py`) en vez de resolverlo a mano.
2. **Hueco de la spec, no del código**: si una celda junta líneas de dos partes de la MISMA obra
   (F-050, «varios partes») y solo cambia una, el otro parte no recibe el pedido compartido: no es
   «tocado» (R23) ni «afectado» (R38 excluye las líneas de la celda), pero la pasada completa sí
   puede reescribir sus `extra_auto`. Queda el residual R-g de F-043 en ese parte durante la
   pasada (~30 s). Candidato a feature pequeña: incluir en el pedido todo documento con líneas
   en la celda.

## Automejora (propuestas, no aplicadas)

1. `reviewer.md`, paso 1: cuando `init.sh` da los servicios por caché, decir explícitamente que
   el reviewer reejecuta sin caché la suite de los servicios que toca el diff (hoy se deduce de
   «la suite se ejecuta entera», pero la caché lo oculta).
2. `CHECKPOINTS.md` C4 bis: pedir que la fila de workers vaya **dentro** de la tabla «Evidencias»
   del implementer (aquí estaba en la sección T17, al lado).
