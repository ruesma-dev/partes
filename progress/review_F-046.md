Revisión completa (pasada 1) · `dev` (dc03468)..`0158410`, worktree `partes-wt-f046`
# F-046 · Review: reajuste en Sigrid al aprobar

**Veredicto: CHANGES_REQUESTED (1 punto, de forma)**. El fondo está bien: código, tests,
mutación y equivalentes. Lo que falla es solo C5: T24 sin marcar y sin su commit.

**Nivel de rigor: `critico`** (declarado en `features.json`). Exige fase RED, cobertura
≥ 80 %, mutación completa con cero supervivientes salvo los que acepte el humano, y MANUAL
con su comando exacto.

## Lo ejecutado (resultados reales, 2026-10-17)

- `bash harness/init.sh`: **exit 0**, «ENTORNO LISTO». Raíz 493 passed, 3 skipped.
  Servicios en verde (caché del mismo árbol). Cobertura **98,0 %** (1176/1200). Tamaño
  dentro de los topes.
- Reejecutado por mí sin caché: sv5 **656 passed**, sv3 **2150 passed**, sv4
  `test_f046_*` + `test_f017_punto_unico` **142 passed, 1 skipped**.
- R40 y R41: `git diff dc03468..HEAD` vacío en `estado_parte.py`, `cuenta_analitica.py`,
  `interface_adapters/queue`, `registro_pipeline.py`, `congelacion.py`,
  `jornada_resolver.py` (sv3 y sv4), `pareja_extra.py`, `test_f045_*`, `test_f024_*`,
  `test_f042_*`, `CLAUDE.md` y `despacho.py`. En `sigrid_write_client.py` y
  `registro_models.py` el diff solo añade. Las dos copias de `orm_models.py` son idénticas
  (`cmp`).
- R42: `ARCHITECTURE.md`, `partes-proyecto.md` (§3.3–3.5, §5.5 ter) y
  `azure-apps/partes.md` (commit `dc25286`, solo ese fichero) describen el reajuste.

## Mutación: verificación independiente

- **Recálculo puro** (`harness.alcance` + `generar_mutantes`): 19 ficheros, **2671 líneas,
  565 mutantes**. Coincide con el informe. **Campaña no reejecutada**: el informe declara
  25 666 s, muy por encima de 60 s; me quedo en el recálculo, RM1–RM6 y la muestra.
- **RM1** [x]: SHA medido `6b9ceed`. Desde entonces solo cambian tests y `progress/`, ninguna
  línea de producción del alcance.
- **RM2** [x]: 565 × 45,4 s cuadra con el total. Coste real por mutante: 45,4 × 6 ≈ 272 s,
  con líneas base de 520 s (sv4), 34 s (sv3) y 18–31 s (sv5). No hay ningún salto de orden
  de magnitud. Sin «CAMPAÑA NO VÁLIDA», 0 sin veredicto y línea base corrida.
- **RM4 · muestra re-evaluada** sobre una copia `git archive HEAD` en mi scratchpad. Antes
  de cada mutante pasé la base con el original, y cada mutante se localiza por operador y
  texto exacto. Mueren los 9: `reajuste_pipeline.py:332` `[0]`→`[1]` (2 fallos) · `:151`
  and→or (2) · `sigrid_write_client.py:723` or→and (1) · repo sv3 `:771` (4) · `:623` (1) ·
  `recurso_conciliador.py:603` (1) · repo sv4 `:3192` (2) · `:3217` `not` (era timeout: 21
  fallos) · `web/app.py:2484` (1).
- **RM3** [x]: ningún equivalente sale muerto. **RM6** [x]: en T22 no se tocó producción.
- **RM5** [x]: reproduje E1 (`reajuste_pipeline.py:182`) y, además, E3 (`:150`). Los dos
  sobreviven a la suite COMPLETA de sv5. Su único fallo es `test_f002_r11`, que en la copia
  falla también con el original (no está `infra/`).
- Las 115 secciones de análisis están completas; ninguna queda en `PENDIENTE`.

## Equivalentes E1–E7: opinión para el humano (NO están aceptados)

Los 11 son equivalentes de verdad. **Recomiendo aceptarlos.**
- **E1**: `misma_obra` y `_lote` solo actúan con la base editable y no aplicada. Eso exige su
  parte En registro, leído con `partes.get(hmoide or 0)`: con `hmoide` nulo da `{}` y la
  línea no es editable.
- **E2**: `veredicto_nueva` solo deja editable con acción `escribir` y `misma_obra`, y esta
  última exige `destino`.
- **E3** (de dominio): toda acción `escribir` lleva `hora.horide`
  (`reglas_registro.py:157/223/241`) y `_lote` ya hace `int(a.hora_ide)` sin `or`. Solo
  cambiaría si existiera un `auxhor.ide` igual a 0.
- **E4**: son almacenes muertos; la demo AST lo fija. **E5**: `round(x, 2)` da 0 o un valor
  ≥ 0,01. La demo prueba `round`, pero el `round(…, 2)` ya lo fija el test del #48.
- **E6**: `_veredictos_reparto` solo lee `veredictos` y `error`. **E7**: `aplicado` no está
  en `ESTADOS_BLOQUEAN`, y «Mantener» nunca devuelve `aplicado` (`rechazar_reparto` solo
  hace CAS desde `pendiente`).
- Alternativa, que no recomiendo ahora: E1–E4 y E7 desaparecerían simplificando el código
  (quitar `or 0`/`or 1`, quitar `_aplicados` o reestructurar los contadores). Pero tocar
  producción obligaría a repetir la campaña en esas líneas.

## O1–O3: ninguna es un bug que haya que arreglar antes de cerrar

- **O1**: carrera inalcanzable (candado; sv4 nunca cambia un `aplicado`); solo un contador.
- **O2**: la extra nueva toma el `hmoide` de una base editable, nunca nulo; el test
  `…hmoide_0_sin_parte` fija la rareza. **O3**: código redundante, causa de E7.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] existen los ficheros del arnés.
- **C2** [x] solo F-046 está `in_progress` · [x] rama `feature/F-046-…` · [x]
  `current.md`: la sección de F-046 está al día; el resto son pendientes MANUAL vivos
  heredados de `dev` · [x] historia de las `done`, sin cambios.
- **C3** [x] Hexagonal. Una nota, no bloqueante: `reajuste_reparto.py` («puro» según el
  diseño) importa las constantes de estado de `infrastructure/database/orm_models.py`. Es
  consecuencia de DA14. En sv5, importar `synckey_de` sigue el precedente de
  `registro_pipeline.py` · [x] primera línea con la ruta en todos los `.py` del diff ·
  [x] sin `print` de depuración (los que hay van en scripts de subproceso del test de
  contrato), sin secretos y sin dependencias nuevas · [x] trampas: recurso ≠ empleado,
  incidencias intactas y ORM gemelo con sus lectores en §5.5 ter.
- **C3 bis** [x] `partes-proyecto.md` conserva su cabecera de origen y fecha.
  `git log --diff-filter=A` no muestra originales PDF ni ofimáticos. Barrido del diff de
  `docs/` (correos, IPv4, GUID, `password|secret|token|api_key|AccountKey|
  SharedAccessKey|Bearer`, base64 ≥ 40, DNI `\d{8}[A-Z]`): **0 coincidencias**. En el
  código solo aparece el DNI sintético `12345678Z`. No se redactó nada.
- **C4** [x] Todos los requisitos tienen test `test_f046_rN_*`. Las excepciones son R40 y
  R41, que verifiqué con el diff vacío y con `test_f024_*` en verde, y R42, que verifiqué
  leyendo · [x] sin red ni BBDD · [x] M2–M6 están en `current.md` con su comando.
- **C4 bis** [x] rigor declarado · [x] fase RED con trazas reales de T2–T18 (T16 y T18 en
  copia aislada) · [x] cobertura 98 % · [x] mutación verificada · [x] coste por mutante ≫
  1 s · [x] RM1, RM2, RM5, RM6 · [x] campaña manual: N/A, porque la automática dio 565 ·
  [x] análisis completos; los 11 equivalentes **necesitan la aceptación del humano** antes
  de pasar a `done` (como en F-045) · [x] «Evidencias» con los cuatro números y 6 workers.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** **[ ] T24** («Ejecutar `bash harness/init.sh` en verde») sigue `[ ]` en `tasks.md`
  y no tiene commit `F-046 T24: …` (`git log` llega hasta T23) · [x] `git status` limpio;
  el script de re-evaluación y el log parcial son evidencia citada · [x] `features.json`
  dice `in_progress`, que es el estado real.

## Cobertura: requisito → tests

| Req. | Tests (servicio, fichero) |
|---|---|
| R1–R9c | sv3 `test_f046_proponer_dia.py` (R6, R7, R8, R9 dura, R9a/b/c candef 9, propiedad de R2) |
| R10–R19, R46 | sv3 `test_f046_conciliar.py`, `…reajuste_reparto.py`, `…candado.py`, `…wiring.py` |
| R20–R29, R47 | sv5 `test_f046_reajuste_lineas.py`, `…cliente_reajuste.py`, `…reajuste_pipeline.py`, `…api_reajuste.py`; raíz `test_f046_contrato_reajuste.py` |
| R30–R38 | sv4 `test_f046_reparto_aviso.py`, `…aplicar.py`, `…aprobar_documento.py`, `…marcas.py`, `…cliente_transfer.py` |
| R39 | raíz `test_f010_orm_models_gemelos.py`, `test_f015_r29_…`; sv3/sv4 `test_f046_orm_reparto.py` |
| R40–R42 | diff vacío, `test_f024_borrado_no_congela_gemelos.py` y lectura de documentación |

## Notas de riesgo para el humano (no bloquean)

- **Guardia (DA6)**: si SQL Server evaluara el `CONVERT` fuera del `WHERE`, falla hacia el
  lado seguro (rechaza un lote válido, nunca escribe uno inválido); M3 (c) y (e bis) antes
  de encender. El candado (R18) actúa también apagado (`TimeoutError` → reintento).
- Dos «Aplicar» simultáneos pasan ambos el CAS; es seguro por el lock de sv5 y R26.

## Cambios requeridos

1. `specs/F-046-reajuste-en-sigrid-al-aprobar/tasks.md:31`: ejecutar `bash harness/init.sh`,
   marcar T24 `[x]` y commitearlo como `F-046 T24: …` por ruta explícita (C5).

Opcional, en el mismo commit: los 4 avisos de ruff de T22 (I001 en
`partes-front/tests/test_f046_t22_bordes.py:17`,
`partes-persistencia/tests/test_f046_t22_equivalentes.py:10` y
`partes-transfer/tests/test_f046_t22_equivalentes.py:12`; C408 en
`partes-transfer/tests/test_f046_t22_cliente_bordes.py:25`).

**Pasada 2 (incremental desde `c01788a`)**: bastará con el delta y `init.sh`. Antes de
`done`: aceptación de E1–E7 por el humano y M2–M6.

**Automejora (propuesta, no aplicada)**: que `init.sh` avise si la feature `in_progress`
tiene `[ ]` la tarea «Ejecutar `bash harness/init.sh`», que es el olvido típico del cierre.
