<!-- progress/impl_F-031.md -->
# F-031 · Informe del implementer (v4 + v5)

Rama `feature/F-031-asiento-analitico` (desde `9a00ce3`), rigor **critico**.
v4 (T1-T20, spec aprobada 2026-10-06) y v5 (T21-T32, spec `9ea7c59`, alta
protegida y dependencia con `porcentajes`; DA10 y DA11 aprobadas por el
humano el 2026-10-06). Un commit por tarea. Sin push, sin despliegue, sin
escrituras en Sigrid ni en la base `partes`; `porcentajes` no se edita.

## 1. Que cambio

**sv5**
- `domain/models/registro_models.py`: `ParteSigrid`, `PartidaCuenta`
  (frozen); `ParteDestino` + `estado`, `complementario`, `cerrados`,
  `del_periodo`, `aviso`; `AccionLinea` + `caa_origen`, `caa_nota`.
- `application/services/estado_parte.py` (nuevo, puro): `elegir_parte`
  (mayor `ide` En registro; «cerrado» = `est != est_registro`),
  `nombre_estado`, `aviso_de_parte`, `motivo_choque`. v5: cabecera de
  dependencia con `porcentajes` (R48).
- `application/services/cuenta_analitica.py`: `subcuenta_de_partida`
  (`CI*`/`CD*`), `OrigenSubcuenta`, `origen_subcuenta` (recurso manda,
  partida de respaldo); R7 de F-021 matizada; v5: cabecera de dependencia.
- `infrastructure/sigrid/sigrid_write_client.py`: `partes_del_periodo`,
  `partidas_de_lineas`; v5: `stmts_crear_parte` con el **alta protegida**
  (texto y parametros identicos a `porcentajes` `40b9feb`).
- `application/pipelines/registro_pipeline.py`: paso 4b con respaldo de
  partida y log `origen cuenta`; paso 5 con todos los partes del periodo,
  `elegir_parte` y aviso; paso 7 sobre todos los partes (choque con cerrado
  ⇒ `omitir` `parte_cerrado: …`, `caa_*` a cero; con otro En registro ⇒
  conflicto con su `parte_cod`); log R19; v5: paso 8 = `_crear_parte`
  (alta, relectura con `elegir_parte`, propio u otro servicio, un
  reintento con el siguiente codigo, `RuntimeError` sin lineas; log R46).
- `config/settings.py`: `EST_PARTE_CERRADO` (3), `EST_PARTE_IMPUTADO` (10).
- `comprobar_asiento_analitico.py` (nuevo): consola de SOLO LECTURA.

**sv4**: `static/app.js` — rotulo «complementario» + aviso escapado por
parte; bloque de notas de cuenta de partida (solo si vienen los campos).

**Tests**: `dobles.py` solo crece (partidas, estados, fallos, v5
`alta_protegida`/`al_alta`/`altas`); nuevos `test_f031_*` (sv5: estado_parte,
cuenta_partida, cliente_partes, cliente_alta, pipeline_estado,
pipeline_cuenta_partida, pipeline_alta, comprobar_asiento, mutantes; sv4:
preflight_avisos). Tests ajenos tocados: D1 y DA10 (abajo).

**Docs**: `docs/ARCHITECTURE.md` (semantica 13 matizada, 16 nueva con el
alta protegida y la dependencia, herramienta), `partes-proyecto.md` §3.5,
`azure-apps/partes.md` §3.5 y «que se rompe si cambia» (commits locales
`ef43cac` y `b09865f` en ese repo).

## 2. Decisiones de diseno

1. Textos de aviso y motivo en ASCII sin tildes, como el resto de sv5.
2. Varios cerrados: el aviso los lista todos. Un conflicto por clave
   (recurso|dia|tipo); con choques en dos partes En registro, `parte_cod`
   es el del primero (mayor `ide`). R11 se evalua antes que R12.
3. v5: el INFO del alta lleva el `cod` del parte USADO (el propio o el del
   otro servicio). `INTENTOS_ALTA = 2` como constante de clase.
4. v5: el alta protegida corrige de paso un caso anterior a F-031: una
   peticion con dos meses sin parte proponia el mismo `PT..` para ambos;
   ahora el segundo choca con el codigo y reintenta con el siguiente
   (`test_f031_r44_dos_meses_nuevos_no_comparten_codigo`).
5. Corregido el docstring de `_resolver_cuentas` (O1 del reviewer de
   F-021). Quitado un `or 0` muerto sobre `COUNT(*)` en la herramienta.

## 3. Desviaciones y cambios a tests ajenos (numerados)

- **D1 (aprobada, «si», 2026-10-06)**: `test_f002_pipeline_fases.py::
  test_f002_r20_…` nombraba `partes_existentes`; ahora
  `partes_del_periodo` (un token + comentario).
- **D2**: `notasCuentaHtml` vive DENTRO de `resumenHtml`: a nivel de modulo
  rompia `test_f022_vistas_seleccion.py::test_f022_r27_…` (lista cerrada de
  funciones). Ningun test ajeno cambia por esto.
- **D3**: M1/M2 no se ejecutaron (el encargo manda no ejecutar MANUAL;
  tasks T16 lo pedia).
- **DA10 (aprobada, 2026-10-06)**: `test_f023_escritura_empresa.py`, solo
  dos aserciones: `r32` `con["parameters"] == [...]` ⇒
  `con["parameters"][:6] == [...]`; `r34` `_sql(hmo).endswith("FROM con
  WHERE cod = ? AND tip = ? AND emp = ?")` ⇒ `"… AND emp = ?" in
  _sql(hmo)`. Siguen vigilando empresa, tipo, codigo y fecha y el filtro
  por empresa del `hmo`; verdes antes y despues de T25.
- **DA11 (aprobada)**: la cabecera de dependencia cambia los bytes de los
  dos ficheros copiados: `porcentajes` `test_f037_copias_partes.py::
  test_f037_copia_igual_a_la_ref_vigilada` queda ROJO hasta que recopie.
  Aviso exacto en `progress/current.md` (recopiar de `e85ef0e`, el ultimo
  commit que toca los dos ficheros, y poner ahi su `COMMIT_COPIADO`).
- **T25 · comparacion con `porcentajes`**: por AST contra `git -C
  ../porcentajes show 40b9feb:services/dedicacion-transfer/infrastructure/
  sigrid/sigrid_write_client.py`: «sentencia 0: sql identico=True
  parametros identicos=True; sentencia 1: idem; 2 sentencias». Unica
  diferencia admitida: obra sin empresa `TypeError` aqui, `ValueError` alli.

## 4. Fase RED (traza real; completa en `progress/red_F-031.md`)

Desde `services/partes-transfer` (T13 desde `services/partes-front`):
`../../.venv/Scripts/python.exe -m pytest <fichero> -q`, contra el codigo
anterior a cada tarea de implementacion.

- T3 `test_f031_estado_parte.py`: `ModuleNotFoundError: No module named
  'application.services.estado_parte'`.
- T5 `test_f031_cuenta_partida.py`: `ImportError: cannot import name
  'SUBCUENTAS_COSTE_PARTIDA'`.
- T7 `test_f031_cliente_partes.py`: 11 failed, `AttributeError:
  'SigridWriteClient' object has no attribute 'partes_del_periodo'`.
- T9 `test_f031_pipeline_cuenta_partida.py`: 11 failed, 7 passed:
```
E         {1: (0, None, 'recurso_sin_cuenta', None, None)} != {1: (702, '0100.CIMO12', None, 'partida', 'el recurso no tiene cuenta para esa hora: se usa la de la partida 01.02 (.CIMO12)')}
E       AssertionError: assert (77, 1, ['CIMO09']) == (77, 1, ['CDQ...9', 'CIMO12'])
```
- T11 `test_f031_pipeline_estado.py`: 22 failed, 11 passed (rehecha tras
  arreglar el helper `_lin`, commit `a8c2011`):
```
E       AssertionError: assert (True, 905, '...ne, False, []) == (True, 900, '...'PT26/00009'])
E       AssertionError: assert {'insert'} == {'borrar', 'insert'}
E         {1: ('escribir', None)} != {1: ('omitir', 'parte_cerrado: ya hay horas de ese recurso, dia y tipo en el parte PT26/00004 (Cerrado); no se registran')}
```
- T13 `test_f031_preflight_avisos.py`: 7 failed, 8 passed:
  `assert 'complementario</span>' in '<li>Parte <strong>PT26/00350</strong> (05/2026): <em>se creara</em></li>'`.
- T15 `test_f031_comprobar_asiento.py`: `ModuleNotFoundError: No module
  named 'comprobar_asiento_analitico'`.
- **T23 (v5)** `test_f031_cliente_alta.py`: 5 failed, 1 passed:
```
E         + c) SELECT ISNULL(MAX(ide),0)+1, ?, ?, ?, ?, ?, ? FROM con WITH (UPDLOCK, HOLDLOCK)
E         Right contains 8 more items, first extra item: 'PT26/00122'
E       AssertionError: assert 1 == 4
```
- **T26 (v5)** `test_f031_pipeline_alta.py` + R9 reescrito: 9 failed:
```
E               RuntimeError: no se pudo crear el parte PT26/00005 en registro (la relectura no lo da): no se inserta ninguna linea
E       AssertionError: assert ('PT26/00001', True) == ('PT26/00001', False)
E         Expected regex: 'PT26/00006'
```
Verde antes de tocar nada (caracterizacion): T1 (R4, R6, R10, R20, R22,
R32, R33 y `test_f021_*` 66 passed), T21 (R40, 3 passed), T24 (DA10, 54
passed contra el codigo de hoy).

## 5. Verificacion (resultado real)

- sv5 **520 passed**; sv4 **1672 passed**; raiz **445 passed, 1 skipped**. `node --check
  services/partes-front/static/app.js` OK.
- `test_f021_*` sin cambiar ni una asercion, en verde (R27).
- Ningun test toca red, Sigrid ni PostgreSQL.
- `bash harness/init.sh`: **ENTORNO LISTO** (cobertura 99,6 %, tamano
  OK; avisos previos no bloqueantes: F-014 blocked, infra sin tests, ruff).

## 6. Pendiente MANUAL (humano; comandos en `progress/current.md`)

M1, M2 (herramienta, solo lectura), M3 (modal en produccion y Cancelar),
M4 (modo pruebas, solo con autorizacion), M5 (tras contabilizar un
complementario), **M6** (v5: un solo parte En registro con ambos servicios
desplegados). Antes de desplegar: que `porcentajes` recopie (aviso DA11).
Despliegue `-Solo sv5` y luego `-Solo sv4` (lo lanza el humano).

## 7. Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | sv5 520 passed · sv4 1672 passed · raiz 445 passed, 1 skipped (0 failed) |
| Cobertura de lineas cambiadas | **99,6 %** (239/240; umbral 80 %, nivel critico; `PUERTA COBERTURA`) |
| Mutacion, campana 3 (completa, 6 workers, `--timeout 600`, HEAD `31f13f9`) | **129 generados, 129 muertos, 0 supervivientes, 0 timeouts** (427,8 s) |
| Campanas anteriores | 2: 122/122 muertos (HEAD `bf7da1d`); 1: 126 generados, 103 muertos, 23 supervivientes, 0 timeouts, cerrados uno a uno con `test_f031_mutantes.py` (anexo de `progress/mutacion_F-031.md`) |
| Tiempo de las suites | sv5 ~8 s · sv4 504 s · raiz 114 s |
| `bash harness/init.sh` | **ENTORNO LISTO** (HEAD final de la rama) |

`app.js` no lo cubre la mutacion (solo Python): lo cubren los tests de
`node` de `test_f031_preflight_avisos.py` y M3.
