<!-- progress/red_F-031.md -->
# F-031 · Trazas de la fase RED (salida real, filtrada a las lineas E/FAILED/resumen)

Comando, desde `services/partes-transfer`: `../../.venv/Scripts/python.exe -m pytest <fichero> -q`,
contra el codigo ANTERIOR a la tarea que implementa (T4, T6, T8, T10, T12).
La de T11 se volvio a sacar tras arreglar el helper `_lin` (commit a8c2011),
con `git stash` de los ficheros de T12, para que cada fallo sea por la razon buena.

## T3 · tests/test_f031_estado_parte.py

```
E   ModuleNotFoundError: No module named 'application.services.estado_parte'
ERROR tests/test_f031_estado_parte.py
1 error in 0.38s
```

## T5 · tests/test_f031_cuenta_partida.py

```
E   ImportError: cannot import name 'SUBCUENTAS_COSTE_PARTIDA' from 'application.services.cuenta_analitica' (C:\Users\pgris\PycharmProjects\partes\services\partes-transfer\application\services\cuenta_analitica.py)
ERROR tests/test_f031_cuenta_partida.py
1 error in 0.59s
```

## T7 · tests/test_f031_cliente_partes.py

```
E       AttributeError: 'SigridWriteClient' object has no attribute 'partes_del_periodo'
E       AttributeError: 'SigridWriteClient' object has no attribute 'partes_del_periodo'
E       AttributeError: 'SigridWriteClient' object has no attribute 'partes_del_periodo'
E           AttributeError: 'SigridWriteClient' object has no attribute 'partes_del_periodo'
E           AttributeError: 'SigridWriteClient' object has no attribute 'partes_del_periodo'
E       AttributeError: 'SigridWriteClient' object has no attribute 'partidas_de_lineas'
E       AttributeError: 'SigridWriteClient' object has no attribute 'partidas_de_lineas'
E       AttributeError: 'SigridWriteClient' object has no attribute 'partidas_de_lineas'
E       AttributeError: 'SigridWriteClient' object has no attribute 'partidas_de_lineas'
E           AttributeError: 'SigridWriteClient' object has no attribute 'partidas_de_lineas'
E           AttributeError: 'SigridWriteClient' object has no attribute 'partidas_de_lineas'
FAILED tests/test_f031_cliente_partes.py::test_f031_r1_partes_del_periodo_una_consulta_con_estado
FAILED tests/test_f031_cliente_partes.py::test_f031_r1_partes_del_periodo_convierte_tipos
FAILED tests/test_f031_cliente_partes.py::test_f031_r1_periodo_sin_partes_lista_vacia
FAILED tests/test_f031_cliente_partes.py::test_f031_r15_partes_truncado_es_excepcion
FAILED tests/test_f031_cliente_partes.py::test_f031_r15_partes_error_http_es_excepcion
FAILED tests/test_f031_cliente_partes.py::test_f031_r24_partidas_una_consulta_un_marcador_por_partida
FAILED tests/test_f031_cliente_partes.py::test_f031_r24_partida_sin_codigo - ...
FAILED tests/test_f031_cliente_partes.py::test_f031_r24_sin_partidas_no_lee[parides0]
FAILED tests/test_f031_cliente_partes.py::test_f031_r24_sin_partidas_no_lee[parides1]
FAILED tests/test_f031_cliente_partes.py::test_f031_r24_partidas_truncado_es_excepcion
FAILED tests/test_f031_cliente_partes.py::test_f031_r24_partidas_error_http_es_excepcion
11 failed in 0.59s
```

## T9 · tests/test_f031_pipeline_cuenta_partida.py

```
E       AssertionError: assert {1: (0, None,..., None, None)} == {1: (702, '01...1 (.CDQA01)')}
E         Differing items:
E         {1: (0, None, 'recurso_sin_cuenta', None, None)} != {1: (702, '0100.CIMO12', None, 'partida', 'el recurso no tiene cuenta para esa hora: se usa la de la partida 01.02 (.CIMO12)')}
E         {2: (0, None, 'recurso_sin_cuenta', None, None)} != {2: (703, '0100.CDQA01', None, 'partida', 'el recurso no tiene cuenta para esa hora: se usa la de la partida 02.01 (.CDQA01)')}
E       IndexError: list index out of range
E       AssertionError: assert (0, None, 're...cuenta', None) == (0, None, 'ob...a', 'partida')
E         At index 2 diff: 'recurso_sin_cuenta' != 'obra_sin_cuenta'
E       TypeError: argument of type 'NoneType' is not iterable
E       AssertionError: assert {1: (701, '01..., None, None)} == {1: (701, '01..., None, None)}
E         Omitting 2 identical items, use -vv to show
E         Differing items:
E         {1: (701, '0100.CIMO09', None, None, None)} != {1: (701, '0100.CIMO09', None, 'recurso', None)}
E       AssertionError: assert (None, None) == ('partida', '...02 (.CIMO12)')
E         At index 0 diff: None != 'partida'
E       AssertionError: assert (None, None) == ('partida', '...02 (.CIMO12)')
E         At index 0 diff: None != 'partida'
E       AssertionError: assert [] == [{'parides': ...lock': False}]
E         Right contains one more item: {'parides': [300, 301], 'bajo_lock': False}
E       Failed: DID NOT RAISE RuntimeError
E       AssertionError: assert (77, 1, ['CIMO09']) == (77, 1, ['CDQ...9', 'CIMO12'])
E         At index 2 diff: ['CIMO09'] != ['CDQA01', 'CIMO09', 'CIMO12']
E       ValueError: not enough values to unpack (expected 1, got 0)
FAILED tests/test_f031_pipeline_cuenta_partida.py::test_f031_r21_preflight_e_insert_con_la_cuenta_de_la_partida
FAILED tests/test_f031_pipeline_cuenta_partida.py::test_f031_r21_modo_pruebas_al_centro_de_pruebas
FAILED tests/test_f031_pipeline_cuenta_partida.py::test_f031_r21_obra_sin_esa_cuenta_o_ambigua_como_f021
FAILED tests/test_f031_pipeline_cuenta_partida.py::test_f031_r21_la_nota_no_lleva_nombres
FAILED tests/test_f031_pipeline_cuenta_partida.py::test_f031_r20_r22_origen_recurso_y_ninguno
FAILED tests/test_f031_pipeline_cuenta_partida.py::test_f031_r23_accion_lleva_origen_y_nota
FAILED tests/test_f031_pipeline_cuenta_partida.py::test_f031_r23_el_json_del_preflight_incluye_origen_y_nota
FAILED tests/test_f031_pipeline_cuenta_partida.py::test_f031_r24_una_lectura_solo_con_las_que_hacen_falta
FAILED tests/test_f031_pipeline_cuenta_partida.py::test_f031_r24_fallo_al_leer_partidas_tumba_la_peticion
FAILED tests/test_f031_pipeline_cuenta_partida.py::test_f031_r25_una_lectura_de_cuentas_con_ambos_origenes
FAILED tests/test_f031_pipeline_cuenta_partida.py::test_f031_r26_info_origen_cuenta_sin_nombres
11 failed, 7 passed, 1 warning in 1.95s
```

## T11 · tests/test_f031_pipeline_estado.py

```
E       assert [] == [(10, 2026, 3), (10, 2026, 4)]
E         Right contains 2 more items, first extra item: (10, 2026, 3)
E       AssertionError: assert (True, 905, '...ne, False, []) == (True, 900, '...'PT26/00009'])
E         At index 1 diff: 905 != 900
E       AssertionError: assert (901, []) == (901, ['PT26/00005'])
E         At index 1 diff: [] != ['PT26/00005']
E       TypeError: argument of type 'NoneType' is not iterable
E       AssertionError: assert (True, 800, '...ne, False, []) == (False, None,...'PT26/00004'])
E         At index 0 diff: True != False
E       AssertionError: assert (True, 800, '...ne, False, []) == (False, None,...'PT26/00004'])
E         At index 0 diff: True != False
E       assert (False, None, None) == (False, None, 1)
E         At index 2 diff: None != 1
E       AssertionError: assert {'insert'} == {'borrar', 'insert'}
E         Extra items in the right set:
E         'borrar'
E       ValueError: not enough values to unpack (expected 1, got 0)
E       AssertionError: assert 1 == 2
E        +  where 1 = len([{'ide': 800, 'obride': 10, 'ano': 2026, 'mes': 3, ...}])
E        +    where [{'ide': 800, 'obride': 10, 'ano': 2026, 'mes': 3, ...}] = <tests.dobles.SigridFake object at 0x000001B6CC446F90>.partes
E       Failed: DID NOT RAISE RuntimeError
E       Failed: DID NOT RAISE RuntimeError
E       AssertionError: assert ('escribir', None) == ('omitir', 'p...se registran')
E         At index 0 diff: 'escribir' != 'omitir'
E       AssertionError: assert {1: ('escribir', None)} == {1: ('omitir'...e registran')}
E         Differing items:
E         {1: ('escribir', None)} != {1: ('omitir', 'parte_cerrado: ya hay horas de ese recurso, dia y tipo en el parte PT26/00004 (Cerrado); no se registran')}
E       ValueError: not enough values to unpack (expected 1, got 0)
E       AssertionError: assert (['501|202603...'HL01', ...}]) == ([], 0, [])
E         At index 0 diff: ['501|20260302|1'] != []
E       Failed: DID NOT RAISE RuntimeError
E       AssertionError: assert [] == [{'registro_i...e registran'}]
E         Right contains one more item: {'registro_id': 1, 'motivo': 'parte_cerrado: ya hay horas de ese recurso, dia y tipo en el parte PT26/00004 (Cerrado); no se registran'}
E       AssertionError: assert (2026, 3, Tru...00004', False) == (2026, 3, Fal...00005', False)
E         At index 2 diff: True != False
E       AssertionError: assert (True, False,..., None, False) == (True, True, ...005', 1, True)
E         At index 1 diff: False != True
E       AssertionError: assert [] == ['[registro] ...as_cerrado=0']
E         Right contains 2 more items, first extra item: '[registro] parte obra=0100 periodo=2026/03 elegido=PT26/00005 estado=None complementario=si cerrados=2 omitidas_cerrado=1'
E       AssertionError: assert '[registro] parte obra=0100 periodo=2026/03 elegido=PT26/00005 estado=1 complementario=no cerrados=0 omitidas_cerrado=0' in 'INFO     application.pipelines.registro_pipeline:registro_pipeline.py:262 [registro] cuentas obra=0100 ok=1 recurso_s...stro_pipeline:registro_pipeline.py:364 [registro] preflight obra=0100 partes=1 escribir=1 omitir=0 ya=0 conflictos=0\n'
E        +  where 'INFO     application.pipelines.registro_pipeline:registro_pipeline.py:262 [registro] cuentas obra=0100 ok=1 recurso_s...stro_pipeline:registro_pipeline.py:364 [registro] preflight obra=0100 partes=1 escribir=1 omitir=0 ya=0 conflictos=0\n' = <_pytest.logging.LogCaptureFixture object at 0x000001B6CC42B5F0>.text
FAILED tests/test_f031_pipeline_estado.py::test_f031_r1_una_lectura_de_partes_por_periodo_con_escribir
FAILED tests/test_f031_pipeline_estado.py::test_f031_r2_cerrado_de_mayor_ide_y_uno_en_registro
FAILED tests/test_f031_pipeline_estado.py::test_f031_r7_en_registro_sale_del_ajuste
FAILED tests/test_f031_pipeline_estado.py::test_f031_r7_nombres_de_estado_desde_el_ajuste
FAILED tests/test_f031_pipeline_estado.py::test_f031_r3_todos_cerrados_crea_complementario[3-Cerrado]
FAILED tests/test_f031_pipeline_estado.py::test_f031_r3_todos_cerrados_crea_complementario[10-Imputado]
FAILED tests/test_f031_pipeline_estado.py::test_f031_r6_un_parte_en_registro_sin_aviso
FAILED tests/test_f031_pipeline_estado.py::test_f031_r5_r31_ni_partes_cerrados_ni_asientos_ni_estados
FAILED tests/test_f031_pipeline_estado.py::test_f031_r31_crear_parte_solo_inserta_cabecera_en_registro
FAILED tests/test_f031_pipeline_estado.py::test_f031_r8_la_segunda_aprobacion_reutiliza_el_complementario
FAILED tests/test_f031_pipeline_estado.py::test_f031_r9_relectura_que_no_cuadra_no_inserta[est_al_crear-3]
FAILED tests/test_f031_pipeline_estado.py::test_f031_r9_relectura_que_no_cuadra_no_inserta[cod_al_crear-PT26/09999]
FAILED tests/test_f031_pipeline_estado.py::test_f031_r11_r14_choque_con_parte_cerrado_se_omite
FAILED tests/test_f031_pipeline_estado.py::test_f031_r11_prevalece_sobre_r12
FAILED tests/test_f031_pipeline_estado.py::test_f031_r12_choque_en_otro_parte_en_registro_es_conflicto
FAILED tests/test_f031_pipeline_estado.py::test_f031_r13_pisar_no_borra_lineas_de_un_parte_cerrado
FAILED tests/test_f031_pipeline_estado.py::test_f031_r15_fallo_de_lectura_tumba_la_peticion[fallo_partes]
FAILED tests/test_f031_pipeline_estado.py::test_f031_r16_preflight_y_ejecutar_coinciden_y_bajo_lock
FAILED tests/test_f031_pipeline_estado.py::test_f031_r17_partes_del_preflight_http
FAILED tests/test_f031_pipeline_estado.py::test_f031_r17_partes_del_resultado
FAILED tests/test_f031_pipeline_estado.py::test_f031_r19_info_por_periodo_sin_nombres
FAILED tests/test_f031_pipeline_estado.py::test_f031_r19_estado_del_elegido_existente
22 failed, 11 passed, 1 warning in 2.29s
```

## T13 · services/partes-front/tests/test_f031_preflight_avisos.py (desde services/partes-front)

```
E       assert 'notasCuentaHtml(pf.acciones)' in '\n  function resumenHtml(pf) {\n    var r = pf.resumen || {};\n    var partes = (pf.partes || []).map(function (p) {\...o ? " Ya registradas: " + r.ya_registrado + "." : "")\n      + "</p>" 
E       AssertionError: assert 'complementario</span>' in '<li>Parte <strong>PT26/00350</strong> (05/2026): <em>se creara</em></li>'
E       assert ('complementario</span>' in "<ul class='ap-list'><li>Parte <strong>PT26/00350</strong> (05/2026): ya existe</li></ul><p>Se registraran <strong>2</...tran 1 linea(s):</strong></p><ul class='ap-list'><li>Persona Tres · 20/05/2
E       assert 'a &amp; &lt;i&gt;b&lt;/i&gt;' in "<ul class='ap-list'><li>Parte <strong>PT26/00350</strong> (05/2026): <em>se creara</em></li></ul><p>Se registraran <s...tran 1 linea(s):</strong></p><ul class='ap-list'><li>Persona Tres · 2
E               subprocess.CalledProcessError: Command '['C:\\Program Files\\nodejs\\node.EXE', '-e', '\n  function esc(v) {\n    return String(v === null || v === undefined ? "" : v)\n      .replace(/&/g, "&amp;").replace(/</g, "&lt;")\n  
E               subprocess.CalledProcessError: Command '['C:\\Program Files\\nodejs\\node.EXE', '-e', '\n  function esc(v) {\n    return String(v === null || v === undefined ? "" : v)\n      .replace(/&/g, "&amp;").replace(/</g, "&lt;")\n  
E               subprocess.CalledProcessError: Command '['C:\\Program Files\\nodejs\\node.EXE', '-e', '\n  function esc(v) {\n    return String(v === null || v === undefined ? "" : v)\n      .replace(/&/g, "&amp;").replace(/</g, "&lt;")\n  
E               subprocess.CalledProcessError: Command '['C:\\Program Files\\nodejs\\node.EXE', '-e', '\n  function esc(v) {\n    return String(v === null || v === undefined ? "" : v)\n      .replace(/&/g, "&amp;").replace(/</g, "&lt;")\n  
E               subprocess.CalledProcessError: Command '['C:\\Program Files\\nodejs\\node.EXE', '-e', '\n  function esc(v) {\n    return String(v === null || v === undefined ? "" : v)\n      .replace(/&/g, "&amp;").replace(/</g, "&lt;")\n  
E               subprocess.CalledProcessError: Command '['C:\\Program Files\\nodejs\\node.EXE', '-e', '\n  function esc(v) {\n    return String(v === null || v === undefined ? "" : v)\n      .replace(/&/g, "&amp;").replace(/</g, "&lt;")\n  
E               subprocess.CalledProcessError: Command '['C:\\Program Files\\nodejs\\node.EXE', '-e', '\n  function esc(v) {\n    return String(v === null || v === undefined ? "" : v)\n      .replace(/&/g, "&amp;").replace(/</g, "&lt;")\n  
FAILED tests/test_f031_preflight_avisos.py::test_f031_r29_resumen_html_llama_a_notas_cuenta
FAILED tests/test_f031_preflight_avisos.py::test_f031_r28_rotula_complementario_y_pinta_el_aviso
FAILED tests/test_f031_preflight_avisos.py::test_f031_r28_complementario_existente
FAILED tests/test_f031_preflight_avisos.py::test_f031_r28_escapa_el_aviso - a...
FAILED tests/test_f031_preflight_avisos.py::test_f031_r29_notas_una_fila_por_linea_escribir_con_nota
FAILED tests/test_f031_preflight_avisos.py::test_f031_r29_notas_escapa_y_cuenta_todas
FAILED tests/test_f031_preflight_avisos.py::test_f031_r30_sin_notas_no_pinta_el_bloque[acciones0]
FAILED tests/test_f031_preflight_avisos.py::test_f031_r30_sin_notas_no_pinta_el_bloque[None]
FAILED tests/test_f031_preflight_avisos.py::test_f031_r30_sin_notas_no_pinta_el_bloque[acciones2]
FAILED tests/test_f031_preflight_avisos.py::test_f031_r30_sin_notas_no_pinta_el_bloque[acciones3]
FAILED tests/test_f031_preflight_avisos.py::test_f031_r30_sin_notas_no_pinta_el_bloque[acciones4]
11 failed, 3 passed, 1 warning in 5.97s
```

## T13 (rehecho tras D2: notasCuentaHtml anidada en resumenHtml) · contra el app.js anterior (git stash)

```
E       assert '\n    function notasCuentaHtml(acciones) {' in '\n  function resumenHtml(pf) {\n    var r = pf.resumen || {};\n    var partes = (pf.partes || []).map(function (p) {\...o ? " Ya registradas: " + r.ya_registrado + "." : "")\n 
E       AssertionError: assert 'complementario</span>' in '<li>Parte <strong>PT26/00350</strong> (05/2026): <em>se creara</em></li>'
E       assert ('complementario</span>' in "<ul class='ap-list'><li>Parte <strong>PT26/00350</strong> (05/2026): ya existe</li></ul><p>Se registraran <strong>2</...tran 1 linea(s):</strong></p><ul class='ap-list'><li>Persona Tres · 20/05/2
E       assert 'a &amp; &lt;i&gt;b&lt;/i&gt;' in "<ul class='ap-list'><li>Parte <strong>PT26/00350</strong> (05/2026): <em>se creara</em></li></ul><p>Se registraran <s...tran 1 linea(s):</strong></p><ul class='ap-list'><li>Persona Tres · 2
E       assert False
E        +  where False = <built-in method startswith of str object at 0x00007FFBBC9F3CA0>("<div class='ap-ctx ap-cuenta-notas'><p><strong>1</strong> linea(s) llevaran la <strong>cuenta analitica de su partida</strong>:</p>")
E        +    where <built-in method startswith of str object at 0x00007FFBBC9F3CA0> = ''.startswith
E       ValueError: substring not found
E       AssertionError: assert ('<strong>2</strong>' in '')
FAILED tests/test_f031_preflight_avisos.py::test_f031_r29_resumen_html_llama_a_notas_cuenta
FAILED tests/test_f031_preflight_avisos.py::test_f031_r28_rotula_complementario_y_pinta_el_aviso
FAILED tests/test_f031_preflight_avisos.py::test_f031_r28_complementario_existente
FAILED tests/test_f031_preflight_avisos.py::test_f031_r28_escapa_el_aviso - a...
FAILED tests/test_f031_preflight_avisos.py::test_f031_r29_notas_una_fila_por_linea_escribir_con_nota
FAILED tests/test_f031_preflight_avisos.py::test_f031_r29_notas_aparte_del_bloque_de_f021
FAILED tests/test_f031_preflight_avisos.py::test_f031_r29_notas_escapa_y_cuenta_todas
7 failed, 8 passed, 1 warning in 10.84s
```

## T15 · tests/test_f031_comprobar_asiento.py

```
E   ModuleNotFoundError: No module named 'comprobar_asiento_analitico'
ERROR tests/test_f031_comprobar_asiento.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.92s
```

## T23 (v5) · tests/test_f031_cliente_alta.py

```
E       AssertionError: assert 'INSERT INTO ...CK, HOLDLOCK)' == 'INSERT INTO ...ND r.est = ?)'
E         Skipping 49 identical leading characters in diff, use -v to show
E         - c) SELECT x.n, ?, ?, ?, ?, ?, ? FROM (SELECT ISNULL(MAX(ide),0)+1 AS n FROM con WITH (UPDLOCK, HOLDLOCK)) x WHERE NOT EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK) WHERE c.cod = ? AND c.emp = ? AND c.tip = ?) AND NOT EXIS
E         + c) SELECT ISNULL(MAX(ide),0)+1, ?, ?, ?, ?, ?, ? FROM con WITH (UPDLOCK, HOLDLOCK)
E       AssertionError: assert [28, 35, 1, '...DD', 20260228] == [28, 35, 1, '...20260228, ...]
E         Right contains 8 more items, first extra item: 'PT26/00122'
E       IndexError: list index out of range
E       AssertionError: assert 1 == 4
E        +  where 1 = <built-in method count of str object at 0x0000029A91819370>('WITH (UPDLOCK, HOLDLOCK)')
E        +    where <built-in method count of str object at 0x0000029A91819370> = 'INSERT INTO con (ide, emp, tip, est, cod, res, fec) SELECT ISNULL(MAX(ide),0)+1, ?, ?, ?, ?, ?, ? FROM con WITH (UPDLOCK, HOLDLOCK)'.count
E       AssertionError: assert False
E        +  where False = <built-in method endswith of str object at 0x0000029A918EC030>('AND NOT EXISTS (SELECT 1 FROM hmo h WHERE h.ide = con.ide)')
E        +    where <built-in method endswith of str object at 0x0000029A918EC030> = 'INSERT INTO hmo (ide, cenide, obride, ano, mes, reside, cenmul) SELECT ide, ?, ?, ?, ?, 0, 0 FROM con WHERE cod = ? AND tip = ? AND emp = ?'.endswith
E        +      where 'INSERT INTO hmo (ide, cenide, obride, ano, mes, reside, cenmul) SELECT ide, ?, ?, ?, ?, 0, 0 FROM con WHERE cod = ? AND tip = ? AND emp = ?' = _sql('INSERT INTO hmo (ide, cenide, obride, ano, mes, reside, cenmul) SELE
FAILED tests/test_f031_cliente_alta.py::test_f031_r41_r42_una_lista_con_cabecera_y_hmo
FAILED tests/test_f031_cliente_alta.py::test_f031_r41_parametros_de_la_cabecera_en_orden
FAILED tests/test_f031_cliente_alta.py::test_f031_r41_tipo_y_estado_salen_del_cliente
FAILED tests/test_f031_cliente_alta.py::test_f031_r41_las_condiciones_van_fuera_del_agregado
FAILED tests/test_f031_cliente_alta.py::test_f031_r42_hmo_solo_si_el_con_no_lo_tiene
5 failed, 1 passed in 0.32s
```

## T26 (v5) · tests/test_f031_pipeline_alta.py + R9 reescrito en tests/test_f031_pipeline_estado.py

```
E               RuntimeError: no se pudo crear el parte PT26/00001 en registro (la relectura no lo da): no se inserta ninguna linea
E               RuntimeError: no se pudo crear el parte PT26/00005 en registro (la relectura no lo da): no se inserta ninguna linea
E       AssertionError: assert ('PT26/00001', True) == ('PT26/00001', False)
E         At index 1 diff: True != False
E               RuntimeError: no se pudo crear el parte PT26/00005 en registro (la relectura no lo da): no se inserta ninguna linea
E               RuntimeError: no se pudo crear el parte PT26/00001 en registro (la relectura no lo da): no se inserta ninguna linea
E       AssertionError: assert ('obra 0100' in 'no se pudo crear el parte PT26/00005 en registro (la relectura no lo da): no se inserta ninguna linea')
E               RuntimeError: no se pudo crear el parte PT26/00005 en registro (la relectura no lo da): no se inserta ninguna linea
E       AssertionError: Regex pattern did not match.
E         Expected regex: 'PT26/00006'
E         Actual message: 'no se pudo crear el parte PT26/00005 en registro (la relectura no lo da): no se inserta ninguna linea'
E               RuntimeError: no se pudo crear el parte PT26/00005 en registro (la relectura no lo da): no se inserta ninguna linea
FAILED tests/test_f031_pipeline_alta.py::test_f031_r43_r47_otro_servicio_crea_un_parte_en_registro[cerrados0]
FAILED tests/test_f031_pipeline_alta.py::test_f031_r43_r47_otro_servicio_crea_un_parte_en_registro[cerrados1]
FAILED tests/test_f031_pipeline_alta.py::test_f031_r43_otro_servicio_con_el_mismo_codigo_y_periodo
FAILED tests/test_f031_pipeline_alta.py::test_f031_r44_codigo_cogido_en_otra_obra_reintenta_con_el_siguiente
FAILED tests/test_f031_pipeline_alta.py::test_f031_r44_dos_meses_nuevos_no_comparten_codigo
FAILED tests/test_f031_pipeline_alta.py::test_f031_r45_dos_altas_bloqueadas_fallan_sin_lineas
FAILED tests/test_f031_pipeline_alta.py::test_f031_r46_info_del_alta_sin_nombres
FAILED tests/test_f031_pipeline_estado.py::test_f031_r45_relectura_sin_parte_en_registro_no_inserta
FAILED tests/test_f031_pipeline_estado.py::test_f031_r43_relectura_con_otro_codigo_usa_ese_parte
9 failed, 35 passed, 1 warning in 1.86s
```
