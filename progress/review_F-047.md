Revisión completa (pasada 1) — `git diff dev...HEAD`, merge-base 75816f2, HEAD 966c999

# F-047 · Review (reviewer, 2026-10-31)

**Veredicto: CHANGES_REQUESTED**. El código, los tests y la mutación están bien. Lo que falla es el
papeleo de cierre: un comando MANUAL estropeado en `current.md`, T12 sin marcar y la tabla
«Evidencias» desactualizada. Son tres arreglos de texto que no tocan código (lista al final).

**Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura
≥ 80 % de las líneas cambiadas, mutación completa con 0 supervivientes sin justificar, RM1–RM6 y
verificaciones MANUAL con su comando exacto.

## Lo ejecutado por el reviewer

- `bash harness/init.sh` tal cual, en el worktree: `ENTORNO LISTO`, exit 0. `PUERTA COBERTURA:
  100.0% de 68 líneas cambiadas (68/68)`. `PUERTA TAMAÑO` OK. Avisos previos: ruff 904, F-032
  blocked, infra sin tests.
- init.sh sirvió sv3 y sv4 **de caché**, así que lancé a mano las dos suites enteras, sin caché
  (`python -m pytest -q -p no:cacheprovider`): sv3 **2371 passed (33,1 s)**; sv4 **3307 passed, 1 skipped (593,0 s)**.
- Raíz: `test_f047_contrato_parte_nuevo.py` + `test_f010_orm_models_gemelos.py` → 28 passed.
- Gemelos: `cmp` de las dos `orm_models.py` → **byte-idénticas**. Sin columnas nuevas (R24).
- R27 / DA8: `git diff dev...HEAD --name-status` sobre los tests da solo 4 líneas `A`
  (los cuatro ficheros `test_f047_*`). **Ningún test existente modificado.**
- Ficheros de design §7 sin tocar (diff vacío: despacho, main_worker, conciliadores,
  congelacion, styles.css, sv1/sv2/sv5, infra, CLAUDE.md).

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros base presentes.
**C2** [x] una sola feature `in_progress` (lo valida init.sh) · [x] rama
`feature/F-047-parte-nuevo-en-espera` · [x] `current.md` lleva la sesión activa en primer lugar; los
cierres anteriores son el formato vigente en `dev`, no los introduce F-047 · [x] history al día
(F-047 no está `done`).
**C3** [x] hexagonal: el puerto de sv3 solo gana un parámetro; `motivo_espera` es puro y vive en
`application/`; las consultas están en `infrastructure/` · [x] primera línea con la ruta (los 4
tests nuevos y los ficheros tocados) · [x] sin `print`/`console.log`/TODO ni dependencias nuevas
(grep sobre las líneas `+`) · [x] trampas: (1) y (2) no se tocan; (3) se cambian las dos copias
del ORM en la misma feature (solo comentarios).
**C3 bis** [x] `docs/referencia/partes-proyecto.md` se modifica: es documentación propia, no un
original externo, así que no lleva cabecera nueva. Barrido mío sobre las líneas `+` de
`docs/referencia` con los patrones correo, IPv4, GUID, `password|secret|token|apikey|api_key|AccountKey`:
**0 coincidencias**. `git log --diff-filter=A` dev..HEAD sin pdf/docx/xlsx/pptx: **0**. Nada que
redactar.
**C4** [x] trazabilidad R1–R27 (tabla abajo), todos en verde · [x] sin red: SQLite con
`FabricaSesionSqlite`/`fabrica`, dobles y node local · **[ ] MANUAL con su comando exacto**:
`progress/current.md` línea 16 tiene un **CR literal (0x0D)** donde va `\r`. Se lee
`` `.<CR>edeploy_partes.ps1 -Solo sv4` `` (lo comprobé con `od -c`; es el único CR del fichero y
entró en 04a8adc). El comando de despliegue que tiene que copiar el humano está roto. En
`tasks.md` T13 está bien.
**C4 bis**
- [x] `rigor: critico` declarado.
- [x] Fase RED: trazas reales de T1–T8 en `impl_F-047.md`, incluida la re-RED de T6 tras DA3-B.
  R15, R22 y R23 son no regresión (la guarda va por estado) y lo dice por escrito. Las 3
  comprobaciones AST de sv3 en R25 se apoyan en la RED de T2/T3. Lo acepto.
- [x] Cobertura: `[OK]` 100 % (68/68).
- [x] Mutación, recálculo independiente con `harness.alcance.alcance_de_feature` +
  `generar_mutantes`: **205 líneas, 32 mutantes**. Coincide fichero a fichero (2/2/13/3/10/0/2/0/0/0).
- [x] Campaña no reejecutada: **4543 s (76 min) según el informe**, por encima de 60 s. Me quedo en
  el recálculo puro + RM1–RM6 + RM4 (abajo).
- [x] Coste por mutante = 4543,2 × 3 ÷ 32 = **426 s**: muy por encima de 1 s.
- [x] Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0; la línea base se corrió en los
  3 workers.
- [x] **RM1**: se midió en a7b3f4d. `git diff --stat a7b3f4d..HEAD` = solo
  `progress/mutacion_F-047.md`, fuera del alcance. Vale.
- [x] **RM2**: media 142,0 s × 3 workers = 426 s por mutante, frente a una base de 657 s (sv4) y
  30 s (sv3). Es el mismo orden de magnitud, y que quede por debajo encaja con `-x` y 32/32 muertos.
  32 × 142,0 = 4544 ≈ total.
- [x] **RM3**: ningún equivalente sale muerto. Los mutantes de `return` en
  `_conciliar_partidas_safely` (L261, 270, 271) cambian un valor que `run()` descarta, pero el
  design §3 lo fija como contrato y `test_f047_…` lo comprueba directamente (L411 del test de sv3).
  No son equivalentes respecto a ese contrato. El valor está muerto en producción: lo anoto como
  observación, no como defecto.
- [x] RM5: N/A, porque no hay supervivientes ni equivalentes declarados.
- [x] RM6: no se quitó ninguna guarda; el diff solo añade código defensivo.
- [x] Sin campaña manual sustitutiva: N/A, porque la automática generó 32.
- [x] Cero supervivientes: no hay análisis `PENDIENTE`.
- **[ ] «Evidencias»**: la fila de mutación sigue diciendo «PENDIENTE: la campaña completa la lanza
  el líder» y falta el **nº de workers**. T12 pedía `--workers 6`, pero la campaña corrió con 3.
**C4 ter** N/A: no hay `harness/rutas_sensibles.json`, e init.sh no señala rutas sensibles.
**C5** **[ ] `tasks.md`**: T12 sigue en `[ ]`, aunque 966c999 «F-047 T12: mutación completa» la
cierra · [x] árbol limpio (`git status` vacío) · [x] `features.json` en `in_progress`, que es lo
correcto hasta el cierre.

## ¿Bastan 32 mutantes para 205 líneas? (RM4)

De las 205 líneas, la mayoría son comentarios, docstrings, firmas, logging y kwargs. El generador
no muta `IfExp`, `in`/`not in` ni llamadas, y no ve plantillas ni JS (estos los cubren los tests de
node). Por eso hice 10 mutantes a mano sobre las líneas críticas sin mutar, en una **copia** en el
scratchpad, con `sys.executable -m pytest -q -x -p no:cacheprovider`. Sin mutante, la base sale
**0**: sv3 26 passed y sv4 102 passed (`test_f047_parte_nuevo_sv4.py` + `test_f062_inicio_con_ciz.py`).

| # | Fichero | Original → mutado | Resultado |
|---|---|---|---|
| A | sv3 sqlalchemy_parte_repository.py:1023 | `now_iso if recalculo_pedido_id else None),` → `None),` | MATA (1 failed) |
| B | sv3 persist_parte_pipeline.py:216 | `recalculo_pedido_id=document_id if seguido else None,` → `recalculo_pedido_id=document_id,` | MATA (1 failed) |
| C | sv3 persist_parte_pipeline.py:301 | `document_id, document_id)` → `document_id, "otro")` | MATA (1 failed) |
| D | sv3 api/app.py:281 | `recalculo_seguimiento=recalculo_seguimiento,` → `recalculo_seguimiento=None,` | MATA (1 failed) |
| E | sv4 parte_repository.py:3792 | `if _parte_nuevo_en_espera(doc):` → `if False:` | MATA (1 failed) |
| F | sv4 parte_repository.py:2259 | `if r.document_id in en_espera:` → `if r.document_id not in en_espera:` | MATA (1 failed) |
| G | sv4 parte_repository.py:2226 | `if _parte_nuevo_en_espera(r.document)}` → `if False}` | MATA (1 failed) |
| H | sv4 parte_repository.py:2219 | `.options(joinedload(ParteRegistroOrm.document))` → `` (borrado) | MATA (1 failed: sentencias de F-062/R17) |
| I | sv4 web/app.py:2510 | `if excluidas.get("recalculando"):` → `if False:` | MATA (1 failed) |
| J | sv4 web/app.py:3838 | `except CongeladoError as exc:   # F-046 (R36) y F-047 (R16)` → `except KeyError as exc:` | MATA (1 failed) |

**Conclusión RM4: 10/10 muertos.** Las líneas críticas que el generador no muta también están
vigiladas. Los 32 automáticos más estos 10 bastan para este alcance.

Script: `rm4_f047.py` en el scratchpad del reviewer. El árbol de trabajo no se tocó.

## Cobertura requisito → test

| Req | Test(s) |
|---|---|
| R1 | `test_f047_r1_save_parte_escribe_el_pedido_en_el_mismo_commit`, `…r1_el_pipeline_pasa_el_id_del_documento_como_pedido` |
| R2 | `…r2_save_parte_con_pedido_none_igual_que_sin_el`, `…r2_sin_conciliador_o_sin_seguimiento_no_hay_pedido[×3]` |
| R3 | `…r3_sha256_repetido_ni_guarda_ni_concilia_ni_marca` |
| R4 | `…r4_orden_guardar_partidas_recurso_marcar` (+3) |
| R5 | `…r5_si_la_conciliacion_de_recurso_lanza_no_se_marca[runtime|timeout_candado]` |
| R6 | `…r6_info_al_marcar[True|False]`, `…r6_si_marcar_lanza_warning_sin_propagar` |
| R7 | `…r7_un_pedido_de_sv4_durante_la_pasada_no_se_toca` (adaptador real) |
| R8 / R9 / R10 | `…r8_save_parte_reemplazo_solo_marca_el_nuevo` / `…r9_…parametro_opcional_en_el_puerto` / `…r10_…` |
| R11–R12 | sv4 `test_f047_r11_*` (2), `test_f047_r12_*` (5, borde 600 s) |
| R13–R14 | sv4 `test_f047_r13_*` (4), `…r13_r18_*` (2), `test_f047_r14_*` (2) |
| R15 / R16 / R17 | sv4 `test_f047_r15_*` (3) / `…r16_*` (6) / `…r17_*` (8) |
| R18 | sv4 `…r13_r18_el_detalle_*` (2); node `test_f047_r18_*` |
| R19–R23 | node `test_f047_r19_*` (3), `r20` (1), `r21` (1), `r22` (3), `r23` (2) |
| R24–R25 | raíz `test_f047_r24_*` (3), `test_f047_r25_*` (4) |
| R26 | revisado a mano: ARCHITECTURE (semánticas 3 y 10), partes-proyecto (§5 y «El parte nuevo también espera»), azure-apps e4804d8 (solo `partes.md`) |
| R27 | `git diff --name-status`: solo `A` |

## Observaciones (no bloquean)

1. La barra del detalle también se deshabilita en la espera de un recálculo uuid4, que el servidor
   sí aprobaría (DA3-B). R18 dice «mientras dure la espera» sin distinguir motivo: es coherente con
   la spec. El implementer lo anota.
2. `_conciliar_partidas_safely` devuelve un `bool` que nadie consume (design §3 lo pide).
3. `/partes` llama a `motivos_espera(None)` en cada carga, con una consulta filtrada a los pedidos
   sin terminar. El coste es bajo, pero conviene vigilarlo si crece la base.

## Cambios requeridos

1. `progress/current.md:16`: sustituir el byte CR (0x0D) de `` `.<CR>edeploy_partes.ps1 `` por
   `` `.\redeploy_partes.ps1 `` (C4, comando MANUAL exacto). Comprobar con `grep -c $'\r'` = 0.
2. `specs/F-047-parte-nuevo-en-espera/tasks.md`: marcar T12 `[x]` (C5).
3. `progress/impl_F-047.md`, «Evidencias»: sustituir la fila «PENDIENTE» por los datos reales
   (32 generados, 32 muertos, 0 supervivientes, **3 workers**, 4543 s, medida en a7b3f4d) y
   actualizar la cabecera «a falta de la campaña de mutación» (C4 bis).

Con eso, la pasada 2 (incremental desde 966c999) solo tiene que comprobar esos tres ficheros e
init.sh.

## Automejora (propuesta, no aplicada)

- Que `harness/init.sh` avise de bytes de control (CR suelto, `\t` o `\b` literales) en
  `progress/current.md`. Es justo el texto que el humano copia a la terminal, y aquí un `\r` dentro
  de `` `.\redeploy` `` se convirtió en un retorno de carro al escribirlo. Vale para cualquier
  proyecto (portar a `arnes-base`).
