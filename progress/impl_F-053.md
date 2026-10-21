<!-- progress/impl_F-053.md -->
# implementer · F-053 · Pisar sin borrar (2026-10-21)

Rama `feature/F-053-pisar-sin-borrar` (worktree `partes-wt-f053`), **rebasada sobre `dev`
12e1f23** (F-034 fusionada). F-034 llegó con la forma que la spec supone
(`_guarda_parte_abierto`, R4 en `stmt_insert_linea`, relectura, `parte_abierto.py`): no hubo
choque. Rigor **crítico**. DA1–DA12 aprobadas con la opción A (humano, 2026-10-21, «Lanza la
siguiente luego despliego»; `design.md` §12); M1 del líder anotada en §9.
Ninguna escritura real en Sigrid; tests sin red ni BBDD.

## Qué cambió

**sv5 (`services/partes-transfer/`)**
- `application/services/pisado.py` (nuevo, puro, solo importa `domain`): `tiene_horas`,
  `es_incidencia`, `choques` (R5: solo choca una línea con horas, salvo incidencias),
  `origen_linea` (R13), `nombrar_lineas`, `motivo_incidencia_en_sigrid` (R6) y
  `motivo_linea_enlazada` (R7).
- `infrastructure/sigrid/sigrid_write_client.py`: `stmt_anular_linea` (R2/R3: `UPDATE hmores
  SET can = 0, tot = 0` con `WHERE` optimista —`ide`, recurso, fecha, código, `can` ±0,001—,
  `_sin_enlaces()` y guarda de parte abierto); **se elimina `stmt_borrar_linea`** (el cliente
  no tiene ningún `DELETE`, R4); `_expr_enlazada()` compartido por `lineas_para_reajuste` y
  `lineas_existentes`, que ahora trae `enlazada` y `hmoide` (R9).
- `application/pipelines/registro_pipeline.py`: paso 7 con `pisado.choques` y las omisiones
  `incidencia_en_sigrid` > `linea_enlazada` tras `parte_cerrado` (R8, helper `_omitir`); paso
  9 con una `stmt_anular_linea` por pisada (R1); `anuladas` = pisadas releídas sin horas o
  ausentes (R12); INFO `[registro] pisada a 0 ide= hmoide= can_antes= origen= registro_id=`
  (R13); `pisada_no_anulada` + WARNING en la relectura (R10); docstring pasos 7 y 9 (R22).
- `application/services/parte_abierto.py`: `MOTIVO_PISADA_NO_ANULADA`,
  `motivo_pisada_no_anulada`, `pisadas_no_anuladas` (motivos de F-034 intactos).
- `domain/models/registro_models.py`: `ResultadoRegistro.anuladas` (sustituye a `borradas`);
  docstring de `Conflicto` («se pondrían a 0»).
- `interface_adapters/resultado_json.py` y `queue/transfer_consumer.py`: clave `anuladas` en
  el JSON de los dos canales (DA7), también en el resultado fallido de la cola.
- `tests/dobles.py`: op `anular` con la semántica del SQL, filas con `enlazada`/`tex`, sin op
  `borrar` (op desconocida = `AssertionError`).

**sv4 (`services/partes-front/`)**
- `static/app.js`: `conflictosHtml` («la linea actual se pone a 0 en Sigrid (no se borra)»;
  cada pisada «linea N · código · X h · Y € → 0 h» + «nueva: …», escapada) y `resultadoHtml`
  («N linea(s) anteriores puestas a 0 en Sigrid (pisadas).» con `esc(r.anuladas)`) (R19, R20).
- `application/services/reparto_obras.py`: `plano["anuladas"]` (R20).
- `application/services/congelacion.py`: solo el texto `MOTIVO_LINEA_REGISTRADA` (DA8, R21).
- Comentarios «pisar pone a 0» en `transfer_queue_publisher.py` y `web/app.py` (R22).

**Documentación**: `docs/ARCHITECTURE.md` (doble canal, semánticas 5 y 16; R23).
`C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (paso 5 de sv5, «Qué se rompe» y nota a
`porcentajes`), commit local `7b057b8` en `azure-apps`, sin push.

**Lista cerrada de `CLAUDE.md`: no crece.** `recurso_conciliador.py` (sv3) no se toca; de
`congelacion.py` solo cambia un texto que sv3 no tiene.

## Decisiones y desviaciones (detalle en `progress/current.md`)

1. `transfer_consumer.py` estaba en «NO se tocan», pero R12/DA7 y la enmienda que la spec
   lista de `test_f002_mutantes.py` l.157 obligan a cambiar `borradas` → `anuladas` en su
   `_resultado_fallido`; la lógica no cambia.
2. `lineas_existentes` rellena `hmoide` (su parámetro) para el INFO de R13.
3. `pisado.py` repite `PREFIJO_PARTES` y `LIMITE_MOTIVO` (imports solo de `domain`); dos tests
   los atan a `PREFIJO_SYNCKEY` y a `parte_abierto.LIMITE_MOTIVO`.
4. Plural en los motivos (`nombrar_lineas`); con una línea, el texto es el de §6 literal.
   `incidencia_en_sigrid` nombra todos los choques En registro; `linea_enlazada`, las enlazadas.
5. `tex` se queda en la fila del doble (R3 se comprueba sobre ella), no en `LineaSigrid`.
6. sv4: los campos de la pisada se escapan con `esc` (no lo pedía la spec).
7. Códigos de hora de los tests `HL01`/`HE01`/`CIV` (las reglas exigen `HL*`/`HE*`; el
   «HN» de la spec era ilustrativo).
8. Entre T2 y T8 los tests de pisado de F-002/F-021/F-031/F-034 estuvieron rojos (el orden de
   `tasks.md` cambia código y dobles antes que sus enmiendas); T10 se verificó con
   `-k "r19 or r20"` (R21/R22, del mismo fichero, son de T11).
9. La primera campaña de mutación abortó en la línea base de sv4:
   `test_f034_resultado_omitidas.py::test_f034_r19_sin_omitidas_el_modal_no_cambia` fijaba el
   texto «anteriores borradas». Enmendado (commit `dcf427a`) y la campaña repetida entera.

## Enmiendas de tests existentes (ampliadas, ninguna relajada)

| Test | Enmienda |
|---|---|
| sv5 `test_f034_cliente_guarda.py` | R3 sobre `stmt_anular_linea` (guarda al final, sobre `hmores.hmoide`); R7 «un solo `DELETE`» → ninguno y sin `stmt_borrar_linea`; R1 incluye la puesta a 0 |
| sv5 `test_f002_pipeline_fases.py` | `..._borra_e_inserta` → `..._anula_e_inserta`: la anterior sigue a 0 h/0 €, `anuladas == 1` |
| sv5 `test_f002_mutantes.py` | `_resultado_fallido`: `anuladas == 0` y sin `borradas` |
| sv5 `test_f002_transfer_consumer.py` | la cola no pone a 0 (`can` sigue 5.0); esquema con `anuladas`, sin `borradas` |
| sv5 `test_f021_pipeline_cuenta.py` | la ajena sigue a 0 con SU cuenta; la nueva lleva 701 |
| sv5 `test_f031_pipeline_estado.py` | espía de `stmt_anular_linea`; el único `UPDATE` es la puesta a 0, ningún `DELETE`; la pisada sigue en su parte; en parte cerrado ni borrada ni a 0 |
| sv5 `test_f034_pipeline_cierre.py` | op `anular`; `borradas` → `anuladas` por relectura; la pisada queda a 0 (antes desaparecía); `can` NULL ya ni choca (R5) |
| sv4 `test_f022_reparto_obras.py` | `agregar_ejecucion` suma `anuladas` |
| sv4 `test_f024_borrado_sigrid.py` R16 | exige «En Sigrid no se borran lineas» y que no diga «borra la linea en Sigrid» |
| sv4 `test_f034_resultado_omitidas.py` R19 | `anuladas` y «puestas a 0 en Sigrid (pisadas)» |
| sv4 `test_f019_bandeja.py`, `test_f022_aprobar_seleccion.py` | respuestas simuladas de sv5 con `anuladas` |

## Tests nuevos

- sv5 `tests/test_f053_pisado.py` (43): R5–R8, R11, R13 puros.
- sv5 `tests/test_f053_cliente_anular.py` (19): R2–R4, R9, R22 (texto y parámetros exactos,
  fuente sin `DELETE` en cliente y pipeline, docstrings).
- sv5 `tests/test_f053_pipeline_pisado.py` (57): doble (§7), ejemplos 1–6, R1, R5–R8, R10,
  R12–R18, `caplog` sin nombres ni `tex`, relectura que falla, `vigilar_lock`.
- sv4 `tests/test_f053_textos_pisado.py` (13): R19–R22 con `node` (v24.14.1).

## Fase RED (salida real, comando exacto; antes de escribir el código)

```
### T1: python -m pytest tests/test_f053_pisado.py -q      (services/partes-transfer)
E   ModuleNotFoundError: No module named 'application.services.pisado'
ERROR tests/test_f053_pisado.py
1 error in 0.53s

### T2: python -m pytest tests/test_f053_cliente_anular.py -q
FAILED ...::test_f053_r2_anular_texto_exacto        (y 13 más: r2, r3, r4 fuente, r9)
14 failed, 1 passed in 0.67s
E   AttributeError: 'SigridWriteClient' object has no attribute 'stmt_anular_linea'. Did you mean: 'stmt_borrar_linea'?
E   'DELETE' is contained here:  ... PIDIO SU `DELETE`, LA NUEVA NO DUPLICA HORAS."""
E   - AS synckey, CASE WHEN ISNULL(hmores.dvaproide, 0) <> 0 OR ... END AS enlazada FROM hmores ...
E   + AS synckey FROM hmores LEFT JOIN auxhor ON auxhor.ide = hmores.horide WHERE hmores.hmoid...

### T3: python -m pytest tests/test_f053_pipeline_pisado.py -k doble -q
14 failed in 0.46s
E   +  where True = hasattr(SigridFake, 'stmt_borrar_linea')
E   AttributeError: 'SigridFake' object has no attribute 'stmt_anular_linea'. Did you mean: 'stmt_borrar_linea'?
E   assert (False, False) == (True, False)

### T4: python -m pytest tests/test_f053_pipeline_pisado.py -k "r5 or r6 or r7 or r8" -q
FAILED ...::test_f053_r5_linea_a_cero_no_es_conflicto_y_se_escribe
FAILED ...::test_f053_r6_ejemplo_3_incidencia_que_ya_consta
FAILED ...::test_f053_r7_ejemplo_4_choque_con_linea_enlazada      (y 9 más)
12 failed, 5 passed, 14 deselected in 0.86s   (los 5 verdes son caracterización)
E   AssertionError: assert ([Conflicto(cl...egistros=[1])] == []
E   AssertionError: assert ('escribir', None) == ('omitir', 'i...o se duplica')
E   AssertionError: assert ('escribir', None) == ('omitir', 'l...la en Sigrid')

### T5: python -m pytest tests/test_f053_pipeline_pisado.py -k "r1 or r12 or r13 or r14" -q
11 failed, 31 deselected in 1.51s
E   AttributeError: 'SigridFake' object has no attribute 'stmt_borrar_linea'. Did you mean: 'stmt_anular_linea'?
E   AttributeError: 'ResultadoRegistro' object has no attribute 'anuladas'

### T6: python -m pytest tests/test_f053_pipeline_pisado.py -k r10 -q
7 failed, 2 passed, 42 deselected in 0.62s
E   + no_escrita: Sigrid no confirmo la linea en el parte PT26/00314; reaprueba
E   - pisada_no_anulada: la linea 9001 del parte PT26/00314 cambio antes de ponerla a 0; no se registra. Vuelve a aprobar para revisar el conflicto

### T9: python -m pytest tests/test_f053_cliente_anular.py -k fuente -q
2 failed, 3 passed, 14 deselected in 0.42s
E   AssertionError: assert 'se PONDRIAN A 0 al pisar' in '... ``lineas`` son las que se BORRARIAN al pisar ...'
E   AssertionError: assert '9. Poner a 0 las lineas pisadas confirmadas' in '... `borradas` cuenta las pisadas que ya no estan ...'

### T10/T11: python -m pytest tests/test_f053_textos_pisado.py -q      (services/partes-front)
13 failed in 1.60s
E     html += "<p>" + r.borradas + " linea(s) anteriores borradas (pisadas).</p>";
E     'borradas' is contained here: ...nteriores borradas (pisadas).</p>
E     siempre: pisar borra lineas de Sigrid, es una
```

Después de cada código, el mismo comando en verde (y la suite del servicio, desde T8).
R15–R18 son de caracterización (verdes al escribirlas, como dice la spec).

## Verificaciones MANUAL pendientes (humano)

M2–M4 en `progress/current.md` (§ «F-053 · verificaciones MANUAL») con comando exacto y
resultado esperado: M2 escribe A y B en 0404 en modo pruebas y pisa A (queda a 0 con su
synckey y `tex`); M3 (solo lectura) comprueba que A a 0 ya no choca y que reaprobarla es
`ya_registrado`, y limpia con `prueba_escritura_sigrid.py limpiar`; M4 textos del portal tras
desplegar. **No usar 10/2026** (4 líneas `PRUEBA-IA` de F-046 que se conservan). Despliegue
(lo pide el humano): sv5 y sv4 a la vez (DA7: con desfase, solo se oculta el recuento).

## Fuera de alcance

`prueba_escritura_sigrid.py limpiar` mantiene su `DELETE` (DA9). El repositorio
`porcentajes` no se toca (aviso en `azure-apps/partes.md`). La conciliación de líneas del
portal pisadas es F-052. Plantillas, ORM, sv1–sv3 sin cambios.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests sv5 (`services/partes-transfer`) | **855 passed**, 1 warning, 10,26 s |
| Tests sv4 (`services/partes-front`) | **2372 passed**, 1 skipped, 1 warning, 342,15 s |
| Tests raíz (`tests/`) | **493 passed**, 3 skipped, 59,50 s |
| sv1–sv3 | en verde (caché de `init.sh`: árbol sin cambios) |
| Cobertura de líneas cambiadas | **100,0 % de 86** (86/86, umbral 80 %, nivel crítico) — `PUERTA COBERTURA` |
| Mutación | `python -m harness.mutacion --feature F-053` (sin `--timeout`, 4 workers): 11 ficheros, 314 líneas; **57 mutantes, 57 muertos, 0 supervivientes, 0 timeouts**, 1017,8 s; líneas base sv5 ~24 s y sv4 ~437 s, timeout por mutante 300/875 s. Informe `progress/mutacion_F-053.md` |
| Supervivientes | ninguno: no hay análisis pendiente |
| `node --check static/app.js` | sin errores |
| `bash harness/init.sh` | **ENTORNO LISTO**: todas las secciones `[OK]`; único `[AVISO]` el de siempre (infra sin tests); `PUERTA TAMAÑO` dentro de los topes |
