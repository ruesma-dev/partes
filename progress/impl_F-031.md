<!-- progress/impl_F-031.md -->
# F-031 · Informe del implementer

Rama `feature/F-031-asiento-analitico` (desde `9a00ce3`), rigor **critico**,
spec v4 aprobada (2026-10-06). T1-T20 hechas, un commit por tarea (mas los
de bloqueo/desbloqueo y el arreglo de un helper de test). Sin push, sin
despliegue, sin escrituras en Sigrid ni en la base `partes`.

## 1. Que cambio

**sv5 (logica)**
- `domain/models/registro_models.py`: `ParteSigrid` y `PartidaCuenta`
  (frozen); `ParteDestino` + `estado`, `complementario`, `cerrados`,
  `del_periodo`, `aviso`; `AccionLinea` + `caa_origen`, `caa_nota`.
- `application/services/estado_parte.py` (nuevo, puro): `elegir_parte`
  (mayor `ide` En registro; «cerrado» = `est != est_registro`, unico
  predicado), `nombre_estado`, `aviso_de_parte`, `motivo_choque`.
- `application/services/cuenta_analitica.py`: `subcuenta_de_partida`
  (`CI*`/`CD*`), `OrigenSubcuenta`, `origen_subcuenta` (recurso manda,
  partida de respaldo); docstring con R7 de F-021 matizada. `resolver_cuenta`
  y lo demas, intactos.
- `infrastructure/sigrid/sigrid_write_client.py`: `partes_del_periodo` y
  `partidas_de_lineas` (SQL de design §9). `partes_existentes`,
  `stmts_crear_parte`, `lineas_existentes` sin tocar.
- `application/pipelines/registro_pipeline.py`: paso 4b con respaldo de
  partida (una lectura solo si hace falta, fuera del lock) y log `origen
  cuenta`; paso 5 con `partes_del_periodo` + `elegir_parte` + aviso; paso 7
  sobre TODOS los partes del periodo (choque con cerrado ⇒ `omitir` con
  `parte_cerrado: …` y `caa_*` a cero; con otro En registro ⇒ conflicto con
  su `parte_cod`); log R19 por periodo; paso 8 relee por codigo + En
  registro y si no, `RuntimeError` sin insertar. Docstring de pasos.
- `config/settings.py`: `EST_PARTE_CERRADO` (3), `EST_PARTE_IMPUTADO` (10).
- `comprobar_asiento_analitico.py` (nuevo): consola de SOLO LECTURA
  (`SigridWriteClient._read`), `comparar` pura (tolerancia 0,01).

**sv4 (solo pintar)**: `static/app.js` — `resumenHtml` rotula
«complementario» y pinta `esc(p.aviso)` por parte solo si vienen; bloque
de notas de cuenta de partida aparte del de F-021. Python de sv4 sin tocar
(el preflight ya reenviaba `partes`/`acciones` tal cual).

**Tests**: `dobles.py` solo crece; nuevos `test_f031_{estado_parte,
cuenta_partida,cliente_partes,pipeline_estado,pipeline_cuenta_partida,
comprobar_asiento,mutantes}.py` (sv5) y `test_f031_preflight_avisos.py`
(sv4). Un token de `test_f002_pipeline_fases.py` (D1).

**Docs**: `docs/ARCHITECTURE.md` (semantica 13 matizada, 16 nueva,
herramienta), `docs/referencia/partes-proyecto.md` §3.5,
`azure-apps/partes.md` §3.5 (commit local `ef43cac` en ese repo).

## 2. Decisiones de diseno

1. Textos de aviso y motivo en ASCII sin tildes (como el resto de mensajes
   de sv5); el contenido es el de design §7.1/§7.2.
2. Varios partes cerrados: el aviso los lista todos («los partes X
   (Cerrado), Y (Imputado) de MM/AAAA estan cerrados: …»).
3. Un conflicto por clave (recurso|dia|tipo) como hoy; si hubiera choques
   en dos partes En registro, `lineas` lleva todas y `parte_cod` es el del
   primero (el de mayor `ide`). El contexto sale de los partes En registro.
4. R11 se evalua antes que R12 (prevalece). R13 sale solo: los conflictos
   solo contienen lineas de partes En registro.
5. Tras crear el parte, `ParteDestino.estado` toma el estado releido.
6. Corregido de paso el docstring de `_resolver_cuentas` que decia que la
   cola reintenta (observacion O1 del reviewer de F-021).
7. En `comprobar_asiento_analitico.py` se quito un `or 0` sobre `COUNT(*)` y
   `SUM(CASE…)` (nunca NULL): era codigo muerto (mutante 97).

## 3. Desviaciones (numeradas)

- **D1 (aprobada por el humano el 2026-10-06, «si»)**: el test AJENO
  `test_f002_pipeline_fases.py::test_f002_r20_el_estado_escrito_se_lee_dentro_del_lock`
  exigia por nombre `partes_existentes`; ahora `partes_del_periodo` (un
  token + comentario). La intencion (estado leido DENTRO del lock) sigue
  comprobada por `vigilar_lock`. Bloqueo y propuesta en `progress/current.md`.
- **D2 (sin tocar tests ajenos)**: con `notasCuentaHtml` a nivel de modulo
  se ponia rojo `test_f022_vistas_seleccion.py::test_f022_r27_js_seccion_por_obra_con_resumen_y_listado`
  (ejecuta `resumenHtml` con una lista cerrada de funciones). Se define
  DENTRO de `resumenHtml` (solo ella la usa); design §6 pedia «añade
  `notasCuentaHtml(pf.acciones)`» sin fijar el ambito. T13 se ajusto y su
  RED se volvio a sacar contra el `app.js` anterior.
- **D3**: tasks.md T16 pedia al implementer ejecutar M1 y M2 (solo
  lectura); el encargo del lider manda NO ejecutar las MANUAL. No se
  ejecutaron: comandos exactos en `progress/current.md`.

Fuera de alcance (observado, no tocado): si una peticion abarca DOS meses
sin parte, el paso 5 propone el mismo `PT..` para ambos (comportamiento
anterior a F-031, `siguiente_cod_pt` por periodo sin escribir entre medias).

## 4. Fase RED (traza real; completa en `progress/red_F-031.md`)

Comando, desde `services/partes-transfer`:
`../../.venv/Scripts/python.exe -m pytest <fichero> -q`, contra el codigo
anterior a cada tarea de implementacion.

T3 · `tests/test_f031_estado_parte.py` (R2, R3, R4, R7, R18, R11 texto):
```
E   ModuleNotFoundError: No module named 'application.services.estado_parte'
1 error in 0.38s
```
T5 · `tests/test_f031_cuenta_partida.py` (R21 puro):
```
E   ImportError: cannot import name 'SUBCUENTAS_COSTE_PARTIDA' from 'application.services.cuenta_analitica'
```
T7 · `tests/test_f031_cliente_partes.py` (R1, R15, R24): `11 failed`
```
E       AttributeError: 'SigridWriteClient' object has no attribute 'partes_del_periodo'
E       AttributeError: 'SigridWriteClient' object has no attribute 'partidas_de_lineas'
```
T9 · `tests/test_f031_pipeline_cuenta_partida.py` (R21, R23-R26): `11 failed, 7 passed`
```
E         {1: (0, None, 'recurso_sin_cuenta', None, None)} != {1: (702, '0100.CIMO12', None, 'partida', 'el recurso no tiene cuenta para esa hora: se usa la de la partida 01.02 (.CIMO12)')}
E       AssertionError: assert [] == [{'parides': ...lock': False}]
E       Failed: DID NOT RAISE RuntimeError
E       AssertionError: assert (77, 1, ['CIMO09']) == (77, 1, ['CDQ...9', 'CIMO12'])
```
T11 · `tests/test_f031_pipeline_estado.py` (R1-R3, R5, R7-R9, R11-R13,
R15-R17, R19, R31): `22 failed, 11 passed` (los 11: caracterizacion de T1 y
guardas que el codigo de hoy ya cumplia). Rehecha tras arreglar el helper
`_lin` (los tests de varios dias fallaban por `TypeError`, no por la razon
buena; commit `a8c2011`), con `git stash` de T12:
```
E       assert [] == [(10, 2026, 3), (10, 2026, 4)]
E       AssertionError: assert (True, 905, '...ne, False, []) == (True, 900, '...'PT26/00009'])
E       AssertionError: assert (True, 800, '...ne, False, []) == (False, None,...'PT26/00004'])
E       AssertionError: assert {'insert'} == {'borrar', 'insert'}
E       Failed: DID NOT RAISE RuntimeError
E         {1: ('escribir', None)} != {1: ('omitir', 'parte_cerrado: ya hay horas de ese recurso, dia y tipo en el parte PT26/00004 (Cerrado); no se registran')}
E         At index 0 diff: ['501|20260302|1'] != []
```
T13 · `services/partes-front/tests/test_f031_preflight_avisos.py` (R28,
R29; R30 ya verde): `7 failed, 8 passed`
```
E       AssertionError: assert 'complementario</span>' in '<li>Parte <strong>PT26/00350</strong> (05/2026): <em>se creara</em></li>'
```
T15 · `tests/test_f031_comprobar_asiento.py` (R35-R38):
```
E   ModuleNotFoundError: No module named 'comprobar_asiento_analitico'
```
En verde antes de tocar nada (T1, caracterizacion): R4, R6, R10, R20, R22,
R32, R33 y la suite `test_f021_*` (66 passed, R27).

## 5. Verificacion (resultado real)

- sv5: **503 passed** (8,9 s). sv4: **1672 passed** (504 s). Raiz:
  **445 passed, 1 skipped**. `node --check services/partes-front/static/app.js` OK.
- `test_f021_*` (sv5 y sv4) sin cambiar ni una asercion, en verde (R27).
- Ningun test toca red, Sigrid ni PostgreSQL (dobles y `httpx` simulado).
- `bash harness/init.sh`: **ENTORNO LISTO**, cobertura 99,6 %, tamano
  OK. Ruff (no bloqueante) quedan avisos de estilo en tests nuevos
  (`ISC004`/`C408`) y `UP045` de los modelos, como la deuda previa.

## 6. Pendiente MANUAL (humano; detalle y comandos en `progress/current.md`)

M1 y M2 (herramienta, solo lectura, obras 0696 y 0404), M3 (modal en
produccion y Cancelar), M4 (modo pruebas, solo con autorizacion), M5 (tras
el primer complementario contabilizado). Despliegue `-Solo sv5` y luego
`-Solo sv4` (lo lanza el humano). M0 hecho por el humano.

## 7. Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | sv5 503 passed · sv4 1672 passed · raiz 445 passed, 1 skipped (0 failed) |
| Cobertura de lineas cambiadas | **99,6 %** (227/228 lineas cambiadas; umbral 80 %, nivel critico; `PUERTA COBERTURA` de init.sh) |
| Mutantes (campana completa, 6 workers, timeout 600 s) | **122 generados, 122 muertos, 0 supervivientes, 0 timeouts** (304,9 s; HEAD `bf7da1d`) |
| Primera campana (antes de los tests de `test_f031_mutantes.py`) | 126 generados, 103 muertos, 23 supervivientes, 0 timeouts (317 s); analisis uno a uno en el anexo de `progress/mutacion_F-031.md` |
| Tiempo de las suites | sv5 8,9 s (16,9 s dentro de init) · sv4 504 s · raiz 86,9 s |
| `bash harness/init.sh` | **ENTORNO LISTO** (todo OK; avisos previos: F-014 blocked, infra sin tests, ruff no bloqueante) |

`app.js` no lo cubre la mutacion (solo Python): lo cubren los tests de
`node` de `test_f031_preflight_avisos.py` y M3.
