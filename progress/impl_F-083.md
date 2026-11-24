<!-- progress/impl_F-083.md -->
# F-083 · Informe del implementer (rigor `critico`)

Rama `feature/F-083-ciz-solo-fin-de-racha`, copia `partes-wt-f083`, base 4a614d3 (sobre `dev`
5b7ddce). Spec aprobada el 2026-11-23, D1–D8 en (a).

## Qué cambió

**Solo sv5.** Desde F-083, cualquier línea de la racha que esté en Sigrid en un día posterior
deja el día como intermedio, sea cual sea su código. Una línea de la racha es del mismo
recurso, con `can` nulo o 0 y, en pruebas, con la marca. El efecto:
- un `fin` ya no escribe un CIZ en medio de la racha (caso 0730);
- un `inicio` ya no escribe su CIZ hermano;
- si el CIZ se cambió a mano, la racha queda sin fin (D6).

Con un CIZ posterior, todo sigue como hoy. No hay lecturas, sentencias ni variables nuevas: F-083
solo convierte `crear`/`mover`/hermano en omisiones.

## Ficheros

- `services/partes-transfer/application/services/racha_ciz.py`:
  - nuevos `es_linea_de_la_racha`, `ultima_posterior`, `motivo_intermedio_racha`,
    `MOTIVO_POSTERIOR_SIN_CIZ` y `DecisionFin.sin_ciz`;
  - `es_ciz_del_recurso` se reescribe sobre `es_linea_de_la_racha`, con la misma semántica;
  - nuevo orden en `decidir_fin` (CIZ posterior → otra posterior con `sin_ciz` → lo de hoy) y en
    `decidir_mismo_dia` (`ya_existe` → `posterior` → `posterior_sin_ciz` → None);
  - docstrings.
- `services/partes-transfer/application/pipelines/registro_pipeline.py`: WARNING
  `racha_fin_no_ciz` (`_racha_fin_no_ciz`) en los bucles de `fines` y de `inicios` de
  `_ciz_de_racha`, y docstrings del paso 6 bis.
- `services/partes-transfer/tests/test_f083_ciz_solo_fin_de_racha.py` (nuevo, 78 tests): puro
  (R1–R9, R19, R20) y pipeline con `SigridFake` (R10–R18).
- `services/partes-transfer/tests/test_f060_racha_ciz.py` y `tests/test_f062_ciz_mismo_dia.py`:
  enmiendas de R22 (ver «Decisiones»).
- `docs/ARCHITECTURE.md` (semántica 4) y `docs/referencia/partes-proyecto.md` (§3.5 3c): una
  frase F-083 en cada uno.
- `azure-apps/partes.md`, §3.5 3c y 3d: **commit aparte 5078dc0** en `main` de `azure-apps`.
  Antes, `git pull --rebase` («Already up to date»). **Sin push.**
- `harness/features.json` y `BACKLOG.md` (`in_progress`), `specs/.../tasks.md` (T1–T5 y T8
  marcadas), `progress/current.md`.

Commits: dbbde6a (estado), 9a73523 (T1), c43d3be (T2), 6fc7ccc (T3), f170bc2 (T4), 10681ce (T5)
y el cierre con este informe.

## Decisiones e interpretaciones (para el reviewer)

1. **Desviación en R22, justificada en `progress/current.md`.** R22 nombra dos tests. La suite
   completa de sv5 tumbó además un tercero, el gemelo de pipeline del mismo subcaso:
   `test_f062_r11_lo_que_no_es_ciz_posterior_no_lo_impide[fila1]`, un CIV posterior del tramo
   en `test_f062_ciz_mismo_dia.py`.
   - Su aserción (que se escribe el hermano) es lo contrario de R8 y R15: cumplir la spec y
     conservarla es imposible.
   - Se enmendó igual, con `# F-083 R8`, y solo ese subcaso: los de otro recurso, `can` ≠ 0 y
     día anterior siguen esperando el hermano.
   - Ningún otro test de sv5 ni de sv4 cambió.
2. **R18 contra 011bc2a.** El código de sv5 de 011bc2a y de 4a614d3 es idéntico: `git diff
   --stat 011bc2a 4a614d3 -- services/partes-transfer/` solo da `test_f072_t28_mutantes.py`.
   - Las sentencias esperadas se capturaron con el doble sobre el código de 4a614d3, antes de
     tocar nada.
   - Los 4 tests de R18 pasan **también con el código base restaurado**: es una caracterización
     de verdad, no un test escrito a posteriori.
3. **`candidatas` se materializa con `list()`** en `decidir_fin` y `decidir_mismo_dia`, porque se
   recorre dos veces. Hay un test con un iterador de una sola pasada (`iter(...)`).
4. **`motivo_intermedio_racha` con `cod` vacío o None** escribe «sin codigo» (design §3).
5. **R12.** Las listas exactas que pide el doble (`racha_leidas` y `estados_leidos`) se comparan
   con las de hoy, en el `fin` y en el `inicio`.
6. **R20.** `racha_ciz.py` no contiene `lineas_de_racha`, `estados_de_partes`, `httpx`, `_read(`,
   `escribir(` ni `DELETE`, y `sigrid_write_client.py` no contiene `DELETE`: no se tocó.

## Fase RED (trazas reales)

Todo se lanzó en `services/partes-transfer`. Las trazas completas están en el scratchpad de la
sesión; aquí van los extractos literales.

**T1 (a)**: `python -m pytest tests/test_f083_ciz_solo_fin_de_racha.py -k puro -q -p no:cacheprovider`,
con el test escrito y sin código:
```
E   ImportError: cannot import name 'MOTIVO_POSTERIOR_SIN_CIZ' from 'application.services.racha_ciz'
1 error in 1.24s
```
**T1 (b)**: la misma orden, con los símbolos nuevos y **sin** el orden nuevo de las decisiones,
para tener un RED de comportamiento:
```
E       AssertionError: assert ('crear' == 'intermedio'
E       AssertionError: assert None == 'dia intermedio de la incidencia: solo se registran el inicio y el fin (la racha sigue en Sigrid el dia 2026-10-08, linea 5 con CIV, sin CIZ despues; no se escribe un fin en medio)'
E       AssertionError: assert ('mover' == 'intermedio'
E       AssertionError: assert ('parte_cerrado' == 'intermedio'
E       AssertionError: assert ('enlazada' == 'intermedio'
E       AssertionError: assert None == 'posterior_sin_ciz'
FAILED ...::test_f083_puro_r2_otra_linea_posterior_hace_intermedio[CIV]   (y [None], [HL01])
FAILED ...::test_f083_puro_r3_posterior_antes_que_mover_enlazada_y_cerrado[anterior0..3]
FAILED ...::test_f083_puro_r4_cuenta_enlazada_o_en_parte_cerrado[posterior0..2]
FAILED ...::test_f083_puro_r8_inicio_sin_hermano_si_la_racha_sigue[CIV]   (y [None])
FAILED ...::test_f083_puro_r9_orden[candidatas6-None-posterior_sin_ciz]
19 failed, 43 passed in 3.12s
```
Con el orden nuevo: `62 passed in 0.95s`.

**T2**: tras T1, `python -m pytest -q -p no:cacheprovider` (suite de sv5):
```
FAILED tests/test_f060_racha_ciz.py::test_f060_r16_las_que_no_son_ciz_del_recurso_no_cuentan[ajena1]
FAILED tests/test_f060_racha_ciz.py::test_f060_r16_las_que_no_son_ciz_del_recurso_no_cuentan[ajena2]
FAILED tests/test_f062_ciz_mismo_dia.py::test_f062_r11_puro_lo_que_no_es_ciz_posterior_no_cuenta[linea3]
FAILED tests/test_f062_ciz_mismo_dia.py::test_f062_r11_lo_que_no_es_ciz_posterior_no_lo_impide[fila1]
4 failed, 1867 passed, 1 skipped
```
Tras las enmiendas: `171 passed` en los dos ficheros.

**T3**: R13–R17 contra el **código base**. Se restauraron temporalmente `racha_ciz.py` y
`registro_pipeline.py` de 4a614d3 y se lanzó la sección de pipeline del test, copiada a un
fichero temporal ya borrado:
```
E       AssertionError: assert ([{'registro_i...: 'CIZ', ...}] == []
E         Left contains one more item: {'registro_id': 2, 'hmoide': 901, 'parte_cod': 'PT26/00010', 'hora_codigo': 'CIZ', ...}
E       AssertionError: assert 'ciz_hmores_ide' not in {'registro_id': 1, ... 'hora_codigo': 'CIV', ...}
E       AssertionError: assert ('escribir' == 'omitir'
FAILED tests/test_zz_red_f083_base.py::test_f083_pipeline_r13_caso_0730
FAILED tests/test_zz_red_f083_base.py::test_f083_pipeline_r15_inicio_desordenado_sin_hermano
FAILED tests/test_zz_red_f083_base.py::test_f083_pipeline_r16_reaprobar_es_idempotente
FAILED tests/test_zz_red_f083_base.py::test_f083_pipeline_r17_preflight_omite_sin_escribir
FAILED tests/test_zz_red_f083_base.py::test_f083_pipeline_r10_warning_del_fin
FAILED tests/test_zz_red_f083_base.py::test_f083_pipeline_r11_warning_del_inicio
6 failed, 6 passed
```
Es el bug 0730 reproducido: d2 escribe un CIZ en medio. La orden fue
`python -m pytest tests/test_zz_red_f083_base.py -q -p no:cacheprovider`.

Con T1 ya hecho y sin el WARNING, `-k pipeline` daba:
```
E       AssertionError: assert [] == [('WARNING', ...n en medio)')]
E         Right contains one more item: ('WARNING', '[registro] racha_fin_no_ciz registro_id=2 motivo=dia intermedio ... linea 5002 con CIV, sin CIZ despues; no se escribe un fin en medio)')
FAILED ...::test_f083_pipeline_r10_warning_del_fin
FAILED ...::test_f083_pipeline_r11_warning_del_inicio
2 failed, 10 passed, 62 deselected
```
Después: `146 passed` con `test_f060_pipeline_mover.py`.

**T4 (R18, caracterización, sin RED a propósito)**: con el código base restaurado, `-k apagado -v`
da `4 passed` (los dos casos, con `mover_ciz=False` y con un settings sin el ajuste).

## Salida de los tests

- sv5: `python -m pytest -q` → `1887 passed, 1 skipped in 16.35s`.
- sv4: `python -m pytest -q` → `4017 passed, 1 skipped in 526.72s`. Sin tocar ningún fichero de
  sv4 (`git diff 5b7ddce -- services/partes-front` vacío): R21.
- `test_f083_ciz_solo_fin_de_racha.py` → `78 passed in 1.68s`.
- `bash harness/init.sh`: en verde, ver «Evidencias».

## T6 · pasada de campaña (2026-11-24)

Campaña lanzada por el líder sobre 9784e0e (`progress/mutacion_F-083.md`): 25 generados, 19
evaluados, **17 muertos, 2 supervivientes**, 0 timeouts, 176,4 s.
- **#1 `racha_ciz.py:189`** (`if ultima is not None:` → `if ultima:`) y **#2 `:196`** (`sigue`):
  **equivalentes, aceptados por el humano el 2026-11-24** («acepto ñas 2 equivalentes»). Los dos valen lo que devuelve
  `ultima_posterior`: `None` o una `LineaSigrid`, dataclass sin `__bool__` ni `__len__`, siempre
  verdadera. Demostración: `progress/equivalentes_F-083.py` (desde `services/partes-transfer`,
  exit 0): dominio por el AST, tipo, y mutante aplicado en memoria contra 5.000 casos al azar
  con bordes, con listas e iteradores. Control negativo (`if False:`) → el script cae, exit 1.
- **Encargo del reviewer** (quitar `candidatas = list(candidatas)` de `decidir_fin`): no es
  equivalente. Muere con `test_f083_puro_r2_con_un_iterador` (CIZ anterior + CIV posterior en un
  `iter`, espera `intermedio` + `sin_ciz`). A mano: sin la línea, `assert ('crear' ==
  'intermedio')`, `1 failed`; con ella, `1 passed`. Línea restaurada (`git status` sin cambios en
  `application/`).
- **RM7**: coincido con el reviewer, N/A justificable: el orden lectura → decisión → escritura es
  de F-060 y no cambia; el orden interno de `decidir_fin` (R3) lo cazan los mutantes muertos. Lo
  decide el reviewer de evidencias.
- Ningún cambio de código de producción en T6.

## Fuera de alcance y pendiente

- **Fuera (design §10)**: un CI* escrito en medio de una racha, nada retroactivo (D8) y sv4 sin
  cambios.
- **M0**: hecha por el líder el 2026-11-24 (solo lectura), anotada en `progress/current.md`.
- **Equivalentes de T6**: aceptados por el humano el 2026-11-24.
- **T7, MANUAL (humano)**: M1–M3 en local en modo pruebas tras el merge en `dev`. M1 y M3 piden
  editar a mano una línea PRUEBA-IA en Sigrid, y eso lo hace el humano (autorizadas el 2026-11-24). M4 es de solo lectura,
  tras desplegar sv5.
- **Push**: `azure-apps` 5078dc0 y la rama de la feature quedan sin push (lo hace el humano).
- Desplegar sv5 activa F-083, porque `MOVER_CIZ` está encendido en producción (D7).

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | sv5 1888 passed, 1 skipped (T6: +1 test); sv4 4017 passed, 1 skipped; F-083 79 |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 31 líneas cambiadas cubiertas (31/31, umbral 90%, nivel critico)` |
| Mutantes | 25 generados, 19 evaluados, 17 muertos, 2 supervivientes equivalentes (aceptados por el humano el 2026-11-24), 0 timeouts, 176,4 s; encargo del reviewer muerto con test nuevo |
| Tiempo de la suite | sv5 27,60 s (init.sh de T6); sv4 526,72 s |
| Capa e2e | `CAPA E2E: N/A (ningún servicio declara el bloque e2e)`; sv4 intacto |
| `init.sh` | T6: `ENTORNO LISTO`, exit 0; raíz 2549 passed, 50 skipped (570 s); sv5 1888 passed; impl 191/220. Antes: raíz 2549 passed, 50 skipped (769 s). sv4: 4017 passed. sv5: verde por la caché del servicio (y 1887 passed lanzada a mano tras el último cambio). `PUERTA TAMAÑO` OK (requirements 144/150, design 249/250, impl 173/220). `PUERTA CARRIL` N/A (nivel crítico). `CAPA E2E` N/A |
