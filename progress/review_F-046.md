Revisión completa (pasada 1) · `dev` (dc03468)..`0158410`, worktree `partes-wt-f046`
# F-046 · Review: reajuste en Sigrid al aprobar

**Veredicto: CHANGES_REQUESTED (1 punto, de forma)**. El fondo está bien: código, tests,
mutación y equivalentes. Lo que falla es solo C5: T24 sin marcar y sin su commit.

**Nivel de rigor: `critico`** (declarado en `harness/features.json`). Exige fase RED,
cobertura ≥ 80 %, mutación completa con cero supervivientes salvo los que acepte el humano,
y MANUAL con su comando exacto.

## Lo ejecutado (resultados reales, 2026-10-17)

- `bash harness/init.sh`: **exit 0**, «ENTORNO LISTO». Raíz 493 passed, 3 skipped.
  Servicios en verde (caché del mismo árbol). Cobertura **98,0 %** (1176/1200, nivel
  crítico). Tamaño dentro de los topes.
- Reejecutado por mí sin caché: sv5 **656 passed**, sv3 **2150 passed**, sv4
  `test_f046_*.py` + `test_f017_punto_unico.py` **142 passed, 1 skipped**.
- R40 y R41: `git diff dc03468..HEAD` vacío en `estado_parte.py`, `cuenta_analitica.py`,
  `interface_adapters/queue`, `registro_pipeline.py`, `congelacion.py`,
  `jornada_resolver.py` (sv3 y sv4), `pareja_extra.py`, `test_f045_*`, `test_f024_*`,
  `test_f042_*`, `CLAUDE.md` y `despacho.py`. En `sigrid_write_client.py` y
  `registro_models.py` el diff solo añade (0 líneas quitadas). Las dos copias de
  `orm_models.py` son idénticas (`cmp`).
- R42: `ARCHITECTURE.md`, `partes-proyecto.md` (§3.3–3.5, §5.5 ter) y
  `azure-apps/partes.md` (commit `dc25286`, solo ese fichero) describen el reajuste.

## Mutación: verificación independiente

- **Recálculo puro** (`harness.alcance` + `generar_mutantes`): 19 ficheros, **2671 líneas,
  565 mutantes**. Coincide con el informe.
- **Campaña no reejecutada**: el informe declara 25 666 s, muy por encima de 60 s. Me quedo
  en el recálculo puro, RM1–RM6 y la muestra de abajo.
- **RM1** [x]: SHA medido `6b9ceed`. Desde entonces solo cambian tests y `progress/`
  (`git diff --stat 6b9ceed..HEAD`), ninguna línea de producción del alcance.
- **RM2** [x]: 565 × 45,4 s cuadra con el total. Coste real por mutante: 45,4 × 6 workers
  ≈ 272 s. Las líneas base son 520 s (sv4), 34 s (sv3) y 18–31 s (sv5), con 191/190/184
  mutantes por servicio. No hay ningún salto de orden de magnitud. Sin «CAMPAÑA NO
  VÁLIDA», 0 sin veredicto y línea base corrida.
- **RM4 · muestra re-evaluada**: lo hice sobre una copia `git archive HEAD` en mi
  scratchpad. Antes de cada mutante pasé la base con el original, y cada mutante se
  localiza por operador y texto exacto. Mueren los 9 de la muestra:
  `reajuste_pipeline.py:332` `[0]`→`[1]` (2 fallos) · `:151` and→or (2) ·
  `sigrid_write_client.py:723` or→and (1) · sv3 repo `:771` and→or (4) · `:623` or→and
  (1) · `recurso_conciliador.py:603` and→or (1) · sv4 repo `:3192` or→and (2) · `:3217`
  `not` (timeout de la campaña: 21 fallos) · `web/app.py:2484` and→or (1).
- **RM3** [x]: ningún equivalente sale muerto en la campaña.
- **RM5** [x] (crítico): reproduje E1 (`reajuste_pipeline.py:182`, `or 0`→`or 1`) y,
  además, E3 (`:150`). Los dos sobreviven a la suite COMPLETA de sv5. Su único fallo es
  `test_f002_r11`, que en la copia aislada falla también con el original (no está `infra/`).
- **RM6** [x]: en T22 no se tocó código de producción, así que no se quitó ninguna guarda.
- Las 115 secciones de análisis están completas; ninguna queda en `PENDIENTE`.

## Equivalentes E1–E7: opinión para el humano (NO están aceptados)

Los 11 son equivalentes de verdad. **Recomiendo aceptarlos.**
- **E1** (`:182`, `:316`): `misma_obra` y `_lote` solo actúan si la base es editable y no
  está aplicada. Eso exige `est_parte` = En registro, leído con `partes.get(hmoide or 0)`:
  con `hmoide` nulo da `{}` y la línea no es editable. `estados_de_partes` nunca tiene la
  clave 0. Confirmado en ejecución.
- **E2** (`assert` and→or): `veredicto_nueva` solo deja editable con acción `escribir` y
  `misma_obra`, y esta última exige `destino`. Correcto.
- **E3** (`accion.hora_ide or 1`): es **de dominio**. Toda acción `escribir` lleva
  `hora.horide` (`reglas_registro.py:157/223/241`) y `_lote` ya hace `int(a.hora_ide)` sin
  `or`. Solo cambiaría si existiera un `auxhor.ide` igual a 0. Confirmado en ejecución.
- **E4** (contadores iniciales): son almacenes muertos. La demo AST lo fija.
- **E5** (`abs(extra) >= _EPS`): `round(x, 2)` da 0 o un valor ≥ 0,01. La demo prueba
  `round`, no el código, pero el `round(…, 2)` ya lo fija el test del #48.
- **E6** (`ok` del dict de fallo): `_veredictos_reparto` solo lee `veredictos` y `error`.
- **E7** (`_aplicados` ==→!=): `aplicado` no está en `ESTADOS_BLOQUEAN`, y «Mantener» nunca
  devuelve `aplicado` (`rechazar_reparto` solo hace CAS desde `pendiente`).
- Alternativa, a decidir por el humano y sin recomendarla ahora: E1–E4 y E7 desaparecerían
  simplificando el código (quitar `or 0`/`or 1` donde el invariante ya lo garantiza, quitar
  `_aplicados` (O3) o reestructurar los contadores). Pero tocar producción obligaría a
  repetir la campaña en esas líneas.

## O1–O3: ninguna es un bug que haya que arreglar antes de cerrar

- **O1**: `_materializar_uno` devuelve True si el reparto desapareció o perdió el CAS. La
  carrera es inalcanzable: la pasada corre bajo el candado y sv4 nunca cambia un
  `aplicado`, porque `cerrar_aplicacion` solo parte de `aplicando`. Como mucho infla un
  contador.
- **O2**: `hmoide: 0` cuando la línea no tiene parte. La extra nueva toma el `hmoide` de una
  base editable, que nunca es nulo. El test
  `…sale_con_hmoide_0_sin_parte` fija esa rareza: si algún día pasa a `None`, se
  actualiza el test.
- **O3**: código redundante. Es la causa de E7.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] existen los ficheros del arnés.
- **C2** [x] solo F-046 está `in_progress` · [x] rama `feature/F-046-…` · [x]
  `current.md`: la sección de F-046 está al día; el resto son pendientes MANUAL vivos
  heredados de `dev`, que F-046 no toca · [x] las `done` tienen su historia (sin cambios).
- **C3** [x] Hexagonal. Dominio sin infraestructura. Una nota, no bloqueante:
  `reajuste_reparto.py`, que el diseño llama «puro», importa las constantes de estado de
  `infrastructure/database/orm_models.py`. Es consecuencia de DA14 (los estados viven en el
  ORM para no crear un gemelo). En sv5, importar `synckey_de` sigue el precedente de
  `registro_pipeline.py` y `comprobacion_lineas.py`.
- **C3** [x] Primera línea con la ruta en todos los `.py` del diff · [x] sin `print` de
  depuración (los que hay van dentro de scripts de subproceso del test de contrato), sin
  secretos y sin dependencias nuevas · [x] trampas: recurso ≠ empleado (el `reside` de la
  extra sale de `preparar`), incidencias intactas, ORM gemelo idéntico y lectores en
  `partes-proyecto.md` §5.5 ter.
- **C3 bis** [x] Se toca `docs/referencia/partes-proyecto.md`, que conserva su cabecera de
  origen y fecha. `git log --diff-filter=A` no muestra originales PDF ni ofimáticos.
  Barrido sobre el diff de `docs/` (correos, IPv4, GUID, `password|secret|token|api_key|
  AccountKey|SharedAccessKey|Bearer`, base64 ≥ 40, DNI `\d{8}[A-Z]`): **0 coincidencias**.
  En el código solo aparece el DNI sintético `12345678Z`. No se redactó nada.
- **C4** [x] Todos los requisitos tienen test (`test_f046_rN_*`; R39 en los guardianes de
  raíz). Las excepciones son R40 y R41, que verifiqué con el diff vacío y con
  `test_f024_*` en verde, y R42, que verifiqué leyendo · [x] sin red ni BBDD (SQLite y
  dobles) · [x] M2–M6 están en `current.md` con su comando exacto.
- **C4 bis** [x] rigor declarado · [x] fase RED con trazas reales de T2–T18 (T16 y T18 en
  copia aislada, como manda la regla) · [x] cobertura [OK] 98 % · [x] mutación verificada
  (arriba) · [x] coste por mutante muy por encima de 1 s · [x] RM1, RM2, RM5, RM6 · [x]
  campaña manual: N/A, porque la automática dio 565 mutantes · [x] análisis completos; los
  11 equivalentes **necesitan la aceptación del humano** antes de pasar a `done` (como en
  F-045) · [x] «Evidencias» con los cuatro números y los workers (6).
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** **[ ] T24** («Ejecutar `bash harness/init.sh` en verde») sigue `[ ]` en `tasks.md`
  y no tiene commit `F-046 T24: …` (`git log dev..HEAD` llega hasta T23) · [x] sin
  artefactos sueltos (`git status` limpio; `redirigir_mutantes_F-046.py` y el log parcial
  son evidencia citada) · [x] `features.json` dice `in_progress`, que es el estado real.

## Cobertura: requisito → tests (fichero principal)

| Req. | Tests |
|---|---|
| R1–R5, R9–R9c | sv3 `test_f046_proponer_dia.py` (R6 `…r6_caso_real…`, R7, R8, R9 dura, R9a/b/c candef 9, R2 propiedad) |
| R10–R19, R46 | sv3 `test_f046_conciliar.py`, `test_f046_reajuste_reparto.py`, `test_f046_candado.py`, `test_f046_wiring.py` |
| R20–R29, R47 | sv5 `test_f046_reajuste_lineas.py`, `…cliente_reajuste.py`, `…reajuste_pipeline.py`, `…api_reajuste.py`; raíz `test_f046_contrato_reajuste.py` |
| R30–R38 | sv4 `test_f046_reparto_aviso.py`, `…aplicar.py`, `…aprobar_documento.py`, `…marcas.py`, `…cliente_transfer.py` |
| R39 | raíz `test_f010_orm_models_gemelos.py`, `test_f015_r29_guardian_cinco_tablas.py`; sv3/sv4 `test_f046_orm_reparto.py` |
| R40, R41, R42 | diff vacío y `test_f024_borrado_no_congela_gemelos.py`; lectura de documentación (arriba) |

## Notas de riesgo para el humano (no bloquean)

- **La guardia (DA6)** cuenta con que SQL Server solo evalúe el `CONVERT` en las filas que
  cumplen el `WHERE`. Si fallara, se iría al lado seguro: rechazaría un lote válido, nunca
  escribiría uno inválido. M3 (c) y (e bis) lo comprueban contra la API real **antes de
  encender**.
- El candado (R18) actúa también con el interruptor apagado (nota 9 del implementer). Es un
  modo de fallo nuevo, `TimeoutError` → reintento de la cola, que antes no existía.
- Dos «Aplicar» simultáneos sobre el mismo reparto pasan ambos el CAS (`aplicando` admite
  reintento). Es seguro porque sv5 serializa con el lock y el segundo ve `ya_aplicada`
  (R26).

## Cambios requeridos

1. `specs/F-046-reajuste-en-sigrid-al-aprobar/tasks.md:31`: ejecutar `bash harness/init.sh`,
   marcar T24 `[x]` y commitearlo como `F-046 T24: …` por ruta explícita (C5).

Opcional, en el mismo commit: los 4 avisos de ruff que añadió T22 (I001 en
`services/partes-front/tests/test_f046_t22_bordes.py:17`,
`services/partes-persistencia/tests/test_f046_t22_equivalentes.py:10` y
`services/partes-transfer/tests/test_f046_t22_equivalentes.py:12`; C408 en
`services/partes-transfer/tests/test_f046_t22_cliente_bordes.py:25`). El commit `dd7cfa6` ya
había dejado limpios los ficheros nuevos.

**Pasada 2 (incremental desde `0158410`)**: bastará con mirar el delta y `init.sh`. Antes de
`done` siguen pendientes la aceptación de E1–E7 por el humano y M2–M6.

## Automejora (propuesta, no aplicada)

Que `init.sh` avise cuando la feature `in_progress` tenga en `tasks.md` alguna tarea `[ ]`
cuyo enunciado sea «Ejecutar `bash harness/init.sh`». Es el olvido típico del cierre, y hoy
solo lo caza el reviewer.
