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
FAILED tests/test_f062_ciz_mismo_dia.py::test_f062_r6_reglas_el_inicio_lleva_su_ciz_hermano
11 failed, 7 passed, 29 deselected, 1 warning in 1.70s
```

**T3 (R13–R14, SQL exacto).**
`python -m pytest tests/test_f062_cliente_inicio.py -q 2>&1 | tail -9 | tee $S/red_T3.txt`
```
tests\test_f062_cliente_inicio.py:52: AttributeError
FAILED tests/test_f062_cliente_inicio.py::test_f062_r13_inicio_con_fin_texto_exacto
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
FAILED tests/test_f062_inicio_con_ciz.py::test_f062_r5_sin_consultas_nuevas
11 failed, 32 passed, 2 warnings in 3.25s
```

## Verificaciones MANUAL pendientes (comandos exactos en `progress/current.md`)

- **M0** hecha por el líder (2026-10-25): `partes:%:%` ⇒ 0 y rachas abiertas ⇒ 0.
- **M1–M5** (local, modo pruebas, obra 0404, tras el merge y ANTES de desplegar sv4: con
  `MOVER_CIZ` encendido, desplegar es activar): un día, día a día, cambio de mes, todo de una
  vez y desordenado, cada uno con su limpieza (`prueba_escritura_sigrid.py`).
- **M6** (producción, solo lectura, tras sv5 → sv4): M4 de F-060 ⇒ `grupos = 0`;
  `partes:%:ciz` ⇒ `> 0`. Quitar solo F-062 = sv4 a su revisión anterior (nunca sv5 a F-060).

## Fuera del alcance

Nada retroactivo (DA6 A); desaprobar, papelera y `borrado_sigrid` no mueven nada (DA8 A);
hermano en parte cerrado: ni se escribe ni corta la racha (DA7 A).

## Resultado de `bash harness/init.sh`

Ejecutado tal cual (2026-10-26). La primera pasada falló solo en el tope de este informe
(236 > 220); se recortó. Tras la review 1 (acf952a): **`ENTORNO LISTO`, 0 fallidas**; `PUERTA COBERTURA` 135/135 (100 %) y `PUERTA TAMAÑO` impl 217/220.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests sv5 (`partes-transfer`) | **1164 passed**, 1 warning, en 32,16 s (dentro de `init.sh`; 1158 + 6 de mutación) |
| Tests sv4 (`partes-front`) | **2791 passed, 1 skipped** en 736,86 s (dentro de `init.sh`) |
| Tests raíz del monorepo | 522 passed, 3 skipped |
| Tests nuevos de F-062 | sv5: 131 (`test_f062_ciz_mismo_dia.py`) + 7 (`test_f062_cliente_inicio.py`); sv4: 43 |
| Cobertura de líneas cambiadas | **100,0 %** (135/135; umbral 80 %, nivel crítico) |
| Mutación (campaña completa, lanzada por el líder, **4 workers**) | **84 mutantes, 75 muertos, 9 supervivientes**, 0 timeouts, 4185 s (49,8 s/mutante) ⇒ 6 huecos cerrados con test y 3 equivalentes propuestos |
| Equivalentes (RM5, review 1) | `progress/equivalentes_F-062.py`: sv4 «1 mutantes, 0 distintos», sv5 «2 mutantes, 0 distintos», exit 0, con el control `and 0` distinto. `progress/equivalentes_F-060.py` (roto por F-062, arreglado en 430412f): sv4 «4, 0 distintos», sv5 «2, 0 distintos» |

**Supervivientes** (análisis completo en `progress/mutacion_F-062.md`; la campaña NO se ha
relanzado). Cada test añadido se verificó a mano aplicando su mutante: el test falla con él y
pasa sin él (`python matar.py .` en el scratchpad ⇒ `red_mut.txt`; commit a7e22ed).

| # | Lugar | Mutación | Clasificación | Test añadido / razón |
|---|---|---|---|---|
| 1 | sv4 `racha_incidencia.py:262` | `or 0`→`or 1` | **equivalente aceptado por el humano el 2026-10-26 («acepto»)** | `d` es una fecha real: ni 0 ni 1 están en el tramo ni son > `d`; demostrado en `equivalentes_F-062.py sv4` |
| 2 | sv5 `registro_pipeline.py:335` | `and`→`or` | hueco | `test_f062_mut_r9_hermano_con_subcuenta_propia_no_pide_partida` (mutante: lee `[33]`) |
| 3 | sv5 `registro_pipeline.py:344` | `or 0`→`or 1` | hueco | `test_f062_mut_r9_hermano_sin_partida_no_toma_la_de_otra_linea` (mutante: `704`) |
| 4 | sv5 `registro_pipeline.py:533` | `or 0`→`or 1` | **equivalente aceptado por el humano el 2026-10-26 («acepto»)** | un `escribir` nunca tiene `recurso_ide` falso: las reglas omiten antes la línea sin recurso; demostrado en `equivalentes_F-062.py sv5` |
| 5 | sv5 `registro_pipeline.py:547` | `or 0`→`or 1` | **equivalente aceptado por el humano el 2026-10-26 («acepto»)** | igual que el 4, para los `fines`; es el #11 de F-060, que el humano ya aceptó; demostrado en `equivalentes_F-062.py sv5` |
| 6 | sv5 `registro_pipeline.py:586` | `or 0`→`or 1` | hueco | `test_f062_mut_r12_linea_sin_codigo_no_es_ciz_ajeno` (mutante: `True`) |
| 7 | sv5 `registro_pipeline.py:817` | `or 0`→`or 1` | hueco | `test_f062_mut_r13_inicio_sin_partida_escribe_paride_cero` (mutante: `(1, 1)`) |
| 8 | sv5 `racha_ciz.py:102` | `or`→`and` | hueco | `test_f062_mut_r20_synckey_ajena_con_digitos_no_es_registro` (mutante: `123`) |
| 9 | sv5 `sigrid_write_client.py:665` | defecto `0`→`1` | hueco | `test_f062_mut_r13_obra_sin_cenide_va_con_cero` (mutante: `1`) |
