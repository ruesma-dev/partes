# Informe del implementer · F-062 · CIZ el mismo día del inicio

- Rama: `feature/F-062-ciz-el-mismo-dia-del-inicio` (worktree `partes-wt-f062`), con `dev`
  fusionado en f490f6c (conflictos solo en `BACKLOG.md`, `features.json` y `current.md`).
- Rigor: **crítico**. Aprobación del humano (2026-10-25): «f62 ok a todo», así que DA1–DA11
  quedan en A.
- Servicios: **sv5** (`partes-transfer`: escribe el CI\* y su CIZ hermano y lo mueve) y
  **sv4** (`partes-front`: marca el `inicio` y envía el tramo de delante). No hay variable
  nueva: va detrás de `MOVER_CIZ`.

## Commits (uno por tarea; detalle con `git log f490f6c..HEAD`)

T1 7cc5081 · T2 447401a · T3 1ff7791 · T4 b6463a4 · T5 4981927 · T6 03bdafb · T7 01a5a98 ·
T8 dd7f48a · T9 bb7924a · T10 9c7e6a5 · T11 96fdb27 (+ `azure-apps` a9d3b5b, local) · T13 ef79b8f.

## Ficheros tocados

- **sv5**
  - `infrastructure/sigrid/sigrid_write_client.py`: añade `SUFIJO_CIZ`, `synckey_ciz_de` y
    `stmt_insert_inicio_con_fin`, con el SQL exacto de design §5.4. La guarda de parte
    abierto (F-034) se aplica a las dos filas, y el hermano lleva además un `NOT EXISTS` sobre
    su synckey.
  - `application/services/racha_ciz.py`: añade `decidir_mismo_dia` y los motivos
    `posterior`, `ya_existe` y `ciz_en_sigrid`.
  - `domain/models/registro_models.py`: añade `LineaEntrada.ciz_mismo_dia`, `FinMismoDia` y
    `AccionLinea.fin_mismo_dia`.
  - `interface_adapters/api/app.py`: añade `LineaIn.ciz_mismo_dia`. El preflight no
    serializa `fin_mismo_dia` (R17).
  - `application/services/reglas_registro.py`: añade `mover_ciz` y `_fin_mismo_dia`; sin CIZ
    en el recurso escribe el WARNING `sin_ciz_mismo_dia`.
  - `application/pipelines/registro_pipeline.py`: paso 4b (mismas lecturas de cuentas),
    6 bis (una sola `lineas_de_racha` para fines e inicios con `:ciz`), 7 (CIZ ajeno ⇒
    `ciz_en_sigrid`) y 9 (`INSERT` doble, `movida_de` solo para registros reales, relectura con `ciz_hmores_ide`).
  - `config/settings.py`: comentario.
- **sv5, tests**: `tests/dobles.py` (op `insert_inicio_con_fin`); nuevos `test_f062_ciz_mismo_dia.py`
  (126) y `test_f062_cliente_inicio.py`; `test_f060_pipeline_mover.py`: tres asertos de `racha_leidas`
  enmendados con «F-062 (R18) enmienda R13» (la lectura incluye las claves `:ciz`).
- **sv4**
  - `application/services/racha_incidencia.py`: añade `racha_delante` e `inicios_con_ciz`.
  - `infrastructure/database/parte_repository.py`: `_roles_de_racha` devuelve también
    `ciz`; cada línea lleva `ciz_mismo_dia`. Con `MOVER_CIZ` apagado, `ciz = set()`.
  - `config/settings.py`: comentario.
  - `tests/test_f025_aprobacion.py`: `CLAVES_LINEA` gana `ciz_mismo_dia`.
  - Nuevo: `tests/test_f062_inicio_con_ciz.py`.
- **Docs**
  - `docs/ARCHITECTURE.md`: semántica 4.
  - `docs/referencia/partes-proyecto.md`: §3.5 3c, §4.4 «El CIZ del mismo día (F-062)» y las
    variables.
  - `azure-apps/partes.md`: 3c pasa a encendido; añade 3d y «Qué se rompe (F-062)».
- **Arnés**: `features.json` (F-062 `in_progress`), `progress/current.md` y `tasks.md`.

**Gemelos.** No hay lógica duplicada nueva. `racha_delante` e `inicios_con_ciz` viven solo
en sv4, y `decidir_mismo_dia` solo en sv5. `jornada_resolver`, la congelación, `de_alta` y
`res.cla` no se han tocado.

## Decisiones y desviaciones (justificadas)

1. **R7, recurso sin CIZ.** Solo se escribe el CI\* más el WARNING
   `[registro] sin_ciz_mismo_dia registro_id=…`, sin un INFO adicional (DA9 A).
2. **R17.** El preflight excluye `fin_mismo_dia` de las acciones, para que su respuesta no
   cambie respecto a F-060. Es el único cambio en `app.py` aparte del campo de entrada.
3. **`_omitir` limpia `fin_mismo_dia`.** Así, una línea omitida en cualquier paso (6, 6 bis
   o 7) nunca escribe hermano, aunque se omita por un motivo ajeno a F-062.
4. **Incidencia sin fecha.** Nunca recibe `ciz_mismo_dia`, porque sin `LineaRol` sv4 no le
   calcula rol.
5. **«Conflicto no confirmado» de R10.** No puede ocurrir con incidencias: se omiten antes
   como `incidencia_en_sigrid`. Queda documentado en el test de R10 y no tiene rama propia.
6. **`estados_de_partes`.** Los `hmoide` que se leen salen solo de los candidatos de los
   fines. El hermano del inicio va en el parte del propio CI\*, que ya protege la guarda del
   `INSERT`.
7. **Movimiento del hermano.** Al mover el hermano (`partes:<i>:ciz`), la escrita del `fin`
   no lleva `movida_de`, porque `registro_de_synckey` devuelve `None` para `:ciz` (DA8 A: la
   línea del inicio sigue `registrado`). El log usa la variante `synckey=<antigua>-><nueva>`.
8. **Asertos de F-060 en sv4.** No hubo que enmendar ninguno. En sv5 hubo que enmendar tres,
   por R18 (la lectura incluye las claves `:ciz`), cada uno con su comentario de cita.

## Fase RED (trazas reales; scratchpad `…/scratchpad/f062/red_T*.txt`)

Comandos desde `services/partes-transfer` (T1–T8) o `services/partes-front` (T9–T10); `S` = scratchpad.

**T1 (R5, puro).**
`python -m pytest tests/test_f062_ciz_mismo_dia.py -k "puro" -q 2>&1 | tail -6 > $S/red_T1.txt`
```
E   ImportError: cannot import name 'MOTIVO_POSTERIOR' from 'application.services.racha_ciz'
ERROR tests/test_f062_ciz_mismo_dia.py
1 error in 0.30s
```

**T2 (R6–R8, reglas).** La primera traza (`red_T2a`) es la ImportError de `FinMismoDia`.
Después se añadió el modelo vacío y se relanzó:
`python -m pytest tests/test_f062_ciz_mismo_dia.py -k "r6 or r7 or r8" -q 2>&1 | tail -22 | tee $S/red_T2b.txt`
```
E        +  where None = AccionLinea(registro_id=4, accion='escribir', ... mover=None, fin_mismo_dia=None).fin_mismo_dia
tests\test_f062_ciz_mismo_dia.py:302: AssertionError
FAILED tests/test_f062_ciz_mismo_dia.py::test_f062_r6_reglas_el_inicio_lleva_su_ciz_hermano
FAILED tests/test_f062_ciz_mismo_dia.py::test_f062_r6_preparar_pasa_mover_ciz_a_las_reglas[True]
11 failed, 7 passed, 29 deselected, 1 warning in 1.70s
```

**T3 (R13–R14, SQL exacto).**
`python -m pytest tests/test_f062_cliente_inicio.py -q 2>&1 | tail -9 | tee $S/red_T3.txt`
```
tests\test_f062_cliente_inicio.py:52: AttributeError
FAILED tests/test_f062_cliente_inicio.py::test_f062_r13_inicio_con_fin_texto_exacto
FAILED tests/test_f062_cliente_inicio.py::test_f062_r13_una_sola_sentencia - ...
6 failed in 0.41s
```

**T4 (doble).**
`python -m pytest tests/test_f062_ciz_mismo_dia.py -k doble -q 2>&1 | tail -8 | tee $S/red_T4.txt`
```
FAILED tests/test_f062_ciz_mismo_dia.py::test_f062_doble_inserta_dos_filas_con_ide_consecutivo
FAILED tests/test_f062_ciz_mismo_dia.py::test_f062_doble_hermano_ya_existe_solo_el_ci
5 failed, 47 deselected, 1 warning in 1.44s
```

**T5 (R9).**
`python -m pytest tests/test_f062_ciz_mismo_dia.py -k r9 -q 2>&1 | tail -8 | tee $S/red_T5.txt`
```
FAILED tests/test_f062_ciz_mismo_dia.py::test_f062_r9_cuenta_del_hermano_la_del_codigo_ciz
FAILED tests/test_f062_ciz_mismo_dia.py::test_f062_r9_respaldo_de_la_partida_en_la_misma_lectura
2 failed, 3 passed, 52 deselected, 1 warning in 1.39s
```

**T6 (R10–R12, R17, R18).**
`python -m pytest tests/test_f062_ciz_mismo_dia.py -k "r10 or r11 or r12 or r17 or r18" -q 2>&1 | grep -E "FAILED|passed|failed" | tee $S/red_T6.txt`
```
FAILED tests/test_f062_ciz_mismo_dia.py::test_f062_r10_ci_ya_registrado_sin_hermano_ni_lectura
FAILED tests/test_f062_ciz_mismo_dia.py::test_f062_r11_una_lectura_con_el_tramo_y_la_propia
FAILED tests/test_f062_ciz_mismo_dia.py::test_f062_r18_hermano_posterior_es_intermedio
15 failed, 29 passed, 38 deselected, 1 warning in 2.01s
```

**T6, R17 (preflight).** La traza se capturó revirtiendo temporalmente el cambio de `app.py`:
`python -m pytest tests/test_f062_ciz_mismo_dia.py -k r17_preflight -q 2>&1 | grep -E "^E |passed|failed" | head -8 | tee $S/red_T6_r17.txt`
```
E       AssertionError: assert {'ok': True, ...1, ...}], ...} == {'ok': True, ...1, ...}], ...}
E         {'acciones': [{'registro_id': 4, 'accion': 'escribir', ...}, ...]} != {'acciones': [...]}
1 failed, 81 deselected, 1 warning in 1.55s
```

**T7 (R13, R15, R16, R19, paso 9).**
`python -m pytest tests/test_f062_ciz_mismo_dia.py -q 2>&1 | grep -E "FAILED|passed|failed" | tee $S/red_T7.txt`
```
FAILED tests/test_f062_ciz_mismo_dia.py::test_f062_r13_una_sentencia_con_las_dos_filas
FAILED tests/test_f062_ciz_mismo_dia.py::test_f062_r15_escrita_con_ciz_hmores_ide
FAILED tests/test_f062_ciz_mismo_dia.py::test_f062_r19_en_pruebas_mueve_el_hermano_con_marca
14 failed, 94 passed, 1 warning in 2.01s
```

**T8 (docstrings; R8, R14 y R25 son caracterización y pasan desde el principio).**
`python -m pytest tests/test_f062_ciz_mismo_dia.py -q ... | tee $S/red_T8.txt`
```
FAILED tests/test_f062_ciz_mismo_dia.py::test_f062_docstrings_cuentan_el_ciz_del_inicio
1 failed, 125 passed, 1 warning in 1.78s
```

**T9 (sv4 puro).** La primera traza es la ImportError de `inicios_con_ciz`. Después se
añadieron stubs vacíos y se relanzó:
`python -m pytest tests/test_f062_inicio_con_ciz.py -k puro -q 2>&1 | grep -E "^FAILED|passed|failed" | tee -a $S/red_T9.txt`
```
E   ImportError: cannot import name 'inicios_con_ciz' from 'application.services.racha_incidencia'
FAILED tests/test_f062_inicio_con_ciz.py::test_f062_r1_puro_tramo_hasta_el_primer_dia_que_no_es_de_la_racha
FAILED tests/test_f062_inicio_con_ciz.py::test_f062_r2_puro_varios_inicios - ...
25 failed, 5 passed in 0.49s
```

**T10 (sv4 repositorio, R1–R5; los 32 que pasan son puros o de caracterización R24).**
`python -m pytest tests/test_f062_inicio_con_ciz.py -q 2>&1 | grep -E "^FAILED|^ERROR|passed|failed|error" | tee $S/red_T10.txt`
```
FAILED tests/test_f062_inicio_con_ciz.py::test_f062_r1_un_dia_suelto_lleva_ciz_y_lista_vacia
FAILED tests/test_f062_inicio_con_ciz.py::test_f062_r2_todo_de_una_vez_el_inicio_sin_ciz
FAILED tests/test_f062_inicio_con_ciz.py::test_f062_r4_apagado_sin_ciz_y_listas_vacias
FAILED tests/test_f062_inicio_con_ciz.py::test_f062_r5_sin_consultas_nuevas
11 failed, 32 passed, 2 warnings in 3.25s
```

Después de cada tarea, el mismo comando quedó en verde antes del commit.

## Verificaciones MANUAL pendientes (comandos exactos en `progress/current.md`)

- **M0**: hecha por el líder el 2026-10-25. `partes:%:%` dio 0 y las rachas abiertas, 0.
- **M1–M5**: local, en modo pruebas sobre la obra 0404. Hay que hacerlas tras el merge en
  `dev` y ANTES de desplegar sv4, porque con `MOVER_CIZ` encendido desplegar es activar.
  Escenarios: un día, día a día, cambio de mes, todo de una vez y desordenado. Cada uno lleva
  su limpieza con `prueba_escritura_sigrid.py`.
- **M6**: producción, solo lectura, después de desplegar sv5 y luego sv4. La M4 de F-060
  debe dar `grupos = 0` y la cuenta de `partes:%:ciz` debe ser `> 0`.
- **Despliegue / vuelta atrás**: sv5 → sv4; quitar solo F-062 = sv4 a su revisión anterior
  (nunca sv5 a la imagen de F-060 con hermanos escritos).

## Fuera del alcance

Nada retroactivo (DA6 A: las rachas abiertas las cierra el siguiente `fin`); desaprobar,
papelera y `borrado_sigrid` no mueven nada (DA8 A); hermano en parte cerrado: no se escribe
ni se corta la racha (DA7 A).

## Resultado de `bash harness/init.sh`

Ejecutado tal cual (2026-10-26). Única comprobación fallida en la primera pasada: este
informe en borrador (236 líneas > 220); recortado y relanzado. Resto en `[OK]`, entre ellas:
`pytest en verde (con medición de cobertura)` (raíz: 522 passed, 3 skipped, 91 s), sv4 y sv5
en verde, sv1–sv3 en verde por caché (árbol sin cambios), `PUERTA COBERTURA: 100.0% de 135
líneas cambiadas cubiertas (135/135, umbral 80%, nivel critico)` y rama
`feature/F-062-ciz-el-mismo-dia-del-inicio`. Resultado final de la segunda pasada: **verde, 0 comprobaciones fallidas** (commit del informe).

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests sv5 (`partes-transfer`) | **1158 passed**, 1 warning, en 19,75 s (dentro de `init.sh`) |
| Tests sv4 (`partes-front`) | **2791 passed, 1 skipped**, 2 warnings, en 736,86 s dentro de `init.sh` (370,40 s en la corrida suelta) |
| Tests raíz del monorepo | 522 passed, 3 skipped, en 91,31 s |
| Tests nuevos de F-062 | sv5: 126 (`test_f062_ciz_mismo_dia.py`) + los de `test_f062_cliente_inicio.py`; sv4: 43 (`test_f062_inicio_con_ciz.py`) |
| Cobertura de líneas cambiadas | **100,0 %** (135/135; umbral 80 %, nivel crítico) |
| Mutación | **PENDIENTE DEL LÍDER** por instrucción expresa: `python -m harness.mutacion --feature F-062` ⇒ `progress/mutacion_F-062.md`. El análisis de supervivientes lo completa el implementer cuando exista ese informe |

La campaña de mutación es la única evidencia sin número, y está así por indicación del
líder, no por omisión.
