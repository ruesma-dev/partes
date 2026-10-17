Revisión incremental desde 242dea6 (pasada 2) · delta `242dea6..20f495b` (base de la pasada 1: `c01788a`)
# F-046 · Review: reajuste en Sigrid al aprobar

**Veredicto: APPROVED** (pasada 2). El único punto de la pasada 1 (T24 sin marcar y sin
commit) está resuelto. **Antes de `done` hacen falta dos cosas**: que el humano acepte los
equivalentes E1–E7 (11 mutantes, hoy PENDIENTES) y M2–M6 MANUAL (están en `current.md`).

**Nivel de rigor: `critico`** (declarado en `features.json`). Exige fase RED, cobertura
≥ 80 %, mutación completa con cero supervivientes salvo los que acepte el humano, RM5 con
muestra, y MANUAL con su comando exacto.

## Pasada 2 · delta revisado (2026-10-17)

- **Ficheros del delta**: 4 tests de T22, `progress/impl_F-046.md` (una celda de
  «Evidencias») y `tasks.md:31` (T24 `[x]`). **No toca producción**, así que la campaña sigue
  midiendo el código revisado (RM1 se mantiene) y lo aprobado en la pasada 1 sigue valiendo.
- **No cambia lo que comprueban los tests**: el `dict(...)` de `_insertar`
  (`partes-transfer/tests/test_f046_t22_cliente_bordes.py:25`) pasa a literal con las mismas
  17 claves y valores. El resto es orden de imports y líneas en blanco. No se añade, quita ni
  modifica ningún `def test_*` ni ningún `assert`.
- **T24** [x] con su commit `20f495b F-046 T24: bash harness/init.sh en verde (ENTORNO LISTO)`.
- **`bash harness/init.sh`** (lo ejecuté tal cual): **exit 0, «ENTORNO LISTO»**. Raíz 493
  passed y 3 skipped. sv1–sv5 en verde (caché del árbol actual). PUERTA COBERTURA **98,0 %**
  (1176/1200, nivel crítico). PUERTA TAMAÑO dentro de los topes. ruff da 730 avisos: es deuda,
  no bloquea.
- **Los tests del delta, sin caché**: sv4 `test_f046_t22_bordes.py` **22 passed** · sv3
  `test_f046_t22_equivalentes.py` **3 passed** · sv5 `test_f046_t22_cliente_bordes.py` +
  `test_f046_t22_equivalentes.py` **15 passed**. El `git status` queda limpio.
- **Observación, no bloquea (el lint es informativo y el punto era opcional)**: `a0c3d26`
  arregla 2 de los 4 avisos (C408 y el I001 de sv3), pero introduce uno nuevo. Con el
  `python -m ruff check .` de `init.sh` quedan 3 I001 en ficheros de T22:
  `partes-front/tests/test_f046_t22_bordes.py:17`,
  `partes-transfer/tests/test_f046_t22_cliente_bordes.py:14` (este es nuevo) y
  `partes-transfer/tests/test_f046_t22_equivalentes.py:12`. Con la configuración raíz,
  `application`/`domain` van en el mismo bloque que `pytest`, sin línea en blanco, y `fastapi`
  se ordena alfabéticamente entre ellos. Se arregla con `python -m ruff check --select I001
  --fix` sobre esos 3 ficheros, ejecutado **desde la raíz**.

## Pasada 1 (completa, `dc03468..0158410`): resumen

- **Ejecutado**: `init.sh` exit 0. Sin caché: sv5 656 passed, sv3 2150 passed, sv4
  `test_f046_*` + `test_f017_punto_unico` 142 passed y 1 skipped.
- **R40/R41**: diff vacío en `estado_parte.py`, `cuenta_analitica.py`, la cola, `registro_pipeline.py`,
  `congelacion.py`, `jornada_resolver.py` (sv3 y sv4), `pareja_extra.py`, `despacho.py` y
  `CLAUDE.md`. En `sigrid_write_client.py` y `registro_models.py` el diff solo añade. Las dos
  copias de `orm_models.py` son idénticas. **R42**: `ARCHITECTURE.md`, `partes-proyecto.md` y
  `azure-apps/partes.md` (commit `dc25286`) describen el reajuste.
- **Mutación**: recálculo puro con 19 ficheros, 2671 líneas y **565 mutantes**, igual que el
  informe. **Campaña no reejecutada: el informe declara 25 666 s.**
- **RM1** [x]: el SHA medido es `6b9ceed`; después solo cambian tests y `progress/`. **RM2** [x]: el total cuadra con
  565 × 45,4 s; las líneas base son 520 s (sv4), 34 s (sv3) y 18–31 s (sv5); no hay saltos de
  orden de magnitud, ni «CAMPAÑA NO VÁLIDA», y la línea base está corrida.
- **RM4** [x]: re-evalué 9 mutantes, cada uno identificado por operador y texto, sobre una copia
  `git archive` y con la base verificada. Mueren los 9, incluido el timeout de sv4 `:3217` (21
  fallos). **RM3** [x]: ningún equivalente sale muerto. **RM5** [x]: reproduje E1 y E3, y los
  dos sobreviven a la suite completa de sv5. **RM6** [x]: T22 no tocó producción.
- **Análisis**: 115 secciones completas, ninguna en `PENDIENTE`.

## Equivalentes E1–E7: opinión para el humano (NO están aceptados)

Los 11 son equivalentes de verdad. **Recomiendo aceptarlos.**
- **E1**: con `hmoide` nulo, `partes.get(hmoide or 0)` da `{}` y la base no es editable.
  **E2**: `misma_obra` exige `destino`.
- **E3** (de dominio): toda acción `escribir` lleva `hora.horide`. Solo cambiaría si existiera
  un `auxhor.ide` igual a 0.
- **E4**: son almacenes muertos (lo fija la demo AST). **E5**: `round(x, 2)` da 0 o un valor
  ≥ 0,01.
- **E6**: solo se leen `veredictos` y `error`. **E7**: `aplicado` no está en `ESTADOS_BLOQUEAN`,
  y «Mantener» solo hace CAS desde `pendiente`.
- **Alternativa**: E1–E4 y E7 desaparecerían simplificando el código, pero habría que repetir
  la campaña en esas líneas. No la recomiendo ahora.
- **O1–O3** no son bugs: O1 es una carrera inalcanzable, O2 una rareza fijada por un test y
  O3 código redundante, que es la causa de E7.

## Checkpoints

- **C1** [x] init.sh exit 0 (pasada 2) · [x] existen los ficheros del arnés.
- **C2** [x] solo F-046 está `in_progress` · [x] rama `feature/F-046-…` · [x] `current.md`
  al día · [x] historia de las `done`, sin cambios.
- **C3** [x] Hexagonal. Nota no bloqueante: `reajuste_reparto.py` importa constantes de
  `orm_models.py` por DA14 · [x] primera línea con la ruta en todos los `.py` · [x] sin
  `print` de depuración, sin secretos y sin dependencias nuevas · [x] trampas del dominio.
- **C3 bis** [x] cabecera de origen y fecha · [x] sin originales PDF ni ofimáticos · [x]
  barrido de secretos y datos personales en `docs/`: 0 coincidencias (solo aparece el DNI
  sintético `12345678Z`).
- **C4** [x] cada requisito tiene su test (R40–R42, por diff y lectura) · [x] sin red ni BBDD ·
  [x] M2–M6 en `current.md` con su comando.
- **C4 bis** [x] rigor declarado · [x] fase RED con trazas reales (T2–T18) · [x] cobertura
  98 % · [x] mutación verificada (recálculo, RM1–RM6 y muestra) · [x] coste por mutante ≫ 1 s
  · [x] campaña manual: N/A, porque la automática dio 565 · [x] análisis completos; **los 11
  equivalentes necesitan la aceptación del humano antes de `done`** · [x] «Evidencias» con
  los cuatro números.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json` en este repositorio.
- **C5** [x] T1–T24 en `[x]` con commits `F-046 Tn: …` (T24 = `20f495b`) · [x] `git status`
  limpio · [x] `features.json` dice `in_progress`, que es el estado real hasta que el humano
  acepte los equivalentes.

## Cobertura: requisito → tests

| Req. | Tests (servicio, fichero) |
|---|---|
| R1–R9c | sv3 `test_f046_proponer_dia.py` |
| R10–R19, R46 | sv3 `test_f046_conciliar.py`, `…reajuste_reparto.py`, `…candado.py`, `…wiring.py` |
| R20–R29, R47 | sv5 `test_f046_reajuste_lineas.py`, `…cliente_reajuste.py`, `…reajuste_pipeline.py`, `…api_reajuste.py`; raíz `test_f046_contrato_reajuste.py` |
| R30–R38 | sv4 `test_f046_reparto_aviso.py`, `…aplicar.py`, `…aprobar_documento.py`, `…marcas.py`, `…cliente_transfer.py` |
| R39 | raíz `test_f010_orm_models_gemelos.py`, `test_f015_r29_…`; sv3/sv4 `test_f046_orm_reparto.py` |
| R40–R42 | diff vacío, `test_f024_borrado_no_congela_gemelos.py` y lectura de documentación |

## Notas de riesgo para el humano (no bloquean)

- **Guardia (DA6)**: si SQL Server evaluara el `CONVERT` fuera del `WHERE`, falla hacia el
  lado seguro (rechaza un lote válido, nunca escribe uno inválido). Hay que hacer M3 (c) y
  (e bis) antes de encender. El candado (R18) actúa también con el interruptor apagado.
- Dos «Aplicar» simultáneos pasan ambos el CAS; es seguro por el lock de sv5 y R26.

## Cambios requeridos

Ninguno. **Condiciones previas a `done`, no de código**: (1) aceptación de E1–E7 por el
humano; (2) M2–M6 MANUAL. Opcional: los 3 I001 de la observación de la pasada 2.

**Automejora (propuesta, no aplicada)**: que `init.sh` avise si la feature `in_progress`
tiene `[ ]` la tarea «Ejecutar `bash harness/init.sh`», y que el implementer compruebe un
arreglo de lint con el mismo `ruff check .` desde la raíz que usa `init.sh` (en `a0c3d26`,
con otra configuración, deshizo uno y metió otro).
