<!-- progress/impl_F-051.md -->
# F-051 · Extracción fila a fila — informe del implementer

Rama `feature/F-051-extraccion-fila-a-fila` (worktree `partes-wt-f051`), rigor
`estandar`. Aprobación del humano 2026-10-19 («ok apruebo»): **DA1 = A**, **DA2 = C**
(interruptor `REVISAR_TABLA_DISPERSA`, defecto `true`), **DA3 = 3 de 3**. Dato de la
DA2 (líder, solo lectura, partes activos desde 2026-06-01): `tabla_dispersa` habría
marcado **8 de 108** laborables y **9 de 17** de fin de semana (anotado en
`requirements.md`, `docs/ARCHITECTURE.md` semántica 17 y `progress/current.md`).

## Qué cambió

| Servicio | Fichero | Cambio |
|---|---|---|
| sv2 | `domain/models/parte_models.py` | `EmpleadoParte.numero_linea_horas: Optional[int] = None` entre `numero_linea` y `categoria`, sin cotas (R9–R12) |
| sv2 | `config/prompts.yaml` | `system`: una viñeta (fila por «Nº» y DNI, nunca la más cercana ni la de arriba). Punto 3: bloque «LECTURA FILA A FILA» y viñeta `numero_linea_horas`. `schema_hint`: `numero_linea_horas` y `dni` en empleados + regla de tipo (R1–R8) |
| sv3 | `domain/models/parte_records.py` | `MotivoLectura(motivo, filas)` (frozen) y `ParteDocumento.lectura_dudosa` |
| sv3 | `application/services/lectura_dudosa.py` (nuevo) | Detector puro `detectar_lectura_dudosa(empleados_raw, *, tabla_dispersa)` (R13, R14, R16, R17) |
| sv3 | `application/services/parte_normalizer.py` | Parámetro `revisar_tabla_dispersa=True`; asigna `parte.lectura_dudosa` y WARNING con motivo y filas (R15) |
| sv3 | `application/pipelines/persist_parte_pipeline.py` | `_compute_review_required`: `True` si `parte.lectura_dudosa` (R15) |
| sv3 | `config/settings.py`, `interface_adapters/api/app.py` | `REVISAR_TABLA_DISPERSA` (bool, `True`) y su paso al normalizer |
| docs | `docs/ARCHITECTURE.md` | Semántica 17 (lectura fila a fila + lectura dudosa + interruptor + dato DA2) |
| tests | `services/partes-api/tests/test_f051_esquema.py`, `test_f051_prompt.py`, `services/partes-persistencia/tests/test_f051_lectura_dudosa.py` | 12 + 12 + 44 tests nuevos |

Commits: `e2375d9` (in_progress + DA), T1 `ccfcd64`, T2 `bd9c4db`, T3 `5d0910e`,
T4 `c5c9cf8`, T5 `e1f2ca3`, T6 `caf6052`, T7 `388561e`, T8 `6e0bfc2` + `b06420b`
(el primero solo marcó la tarea: la edición de ARCHITECTURE falló y se commiteó en
el segundo), T9 `ddf26b1`, orden de imports `dea6ede`.

## Decisiones de diseño

- **Detector (sv3)**: «tiene horas» = ordinaria o extra convertible a número y ≠ 0
  (la extra negativa cuenta); «trabajador» = `nombre` o `dni` con texto; «incidencia»
  = dict con `codigo` o `texto_leido` con texto (misma regla que el normalizer, que
  descarta una incidencia que no es dict). Los no-dict se ignoran. Valores como texto
  («12,5», «2») se interpretan con la misma tolerancia que `_opt_float`/`_opt_int`
  del normalizer; un ilegible no dispara nada.
- **Filas implicadas**: en `autocomprobacion_fila`, el `numero_linea` de las filas
  incoherentes; en `tabla_dispersa`, el de las filas **con trabajador y sin horas**
  (las sospechosas de haber perdido su cifra). Ordenadas, `None` al final. Orden
  de motivos fijo: autocomprobación, tabla dispersa; cada uno como mucho una vez.
- **Conversiones locales en el detector** (`_a_float`, `_a_int`) en vez de importar
  las del normalizer: el normalizer importa el detector y el import inverso sería
  circular; el diseño prohíbe tocar el normalizer fuera de la llamada.
- **WARNING**: `[parte-normalizer] lectura dudosa, el parte va a revision:
  fecha=… obra=… tabla_dispersa filas=3, 4, 5`. Lleva fecha y nº de obra (no son
  datos personales) para poder localizar el parte; nunca nombres ni DNIs (test).
- **Prompt**: el texto de `design.md` §5 tal cual, más una línea «Para cada fila,
  rellena:» entre el bloque y las viñetas de campos, para que la viñeta
  `numero_linea` no parezca parte de las reglas de lectura. Se conserva el `Nº` con
  `º` que ya usaba el fichero.

## Desviaciones y pendientes fuera del worktree

- **`azure-apps/partes.md` (pendiente del líder)**: `design.md` §1 dice que no se
  actualiza, pero F-051 añade una variable de entorno **consumida por sv3**
  (`REVISAR_TABLA_DISPERSA`, opcional, defecto `true`), y la regla de `CLAUDE.md`
  manda documentarla; la fila de sv3 de la tabla de variables (línea ~849) ya lista
  las de F-046. Propuesta de texto, a añadir tras la de F-046: «F-051:
  `REVISAR_TABLA_DISPERSA` (default `true`; a `false` deja de mandar a revisión los
  partes con filas de trabajador sin horas ni incidencia; la autocomprobación de
  fila sigue activa), opcional». No lo toco: el encargo me limita al worktree.
- **Mutación**: T9 cita `parte_models.py` y `lectura_dudosa.py`; la campaña usa el
  alcance por defecto del arnés (líneas cambiadas de la feature frente a `dev`), que
  incluye esos dos y además el cableado de sv3.

## Mutación (T9, rigor `estandar`, muestreada)

`python -m harness.mutacion --feature F-051 --workers 3` (log fuera del worktree, sin
`--timeout`), HEAD `b06420b`. Alcance por defecto: 162 líneas en 7 ficheros. **31
generados, 20 evaluados (semilla 20260820), 17 muertos, 3 supervivientes, 0
timeouts**, 207 s. Detalle en `progress/mutacion_F-051.md`:

| # | Mutante | Veredicto |
|---|---|---|
| 1 | `lectura_dudosa.py:32` `or` → `and` en `_a_float` | **Equivalente**: `None` y `""` acaban en `None` por la excepción de `float()` |
| 2 | `lectura_dudosa.py:73` clave `n or 0` → `n or 1` | Hueco real (fila 0 empata con la 1): test nuevo `..._una_fila_cero_se_ordena_antes_que_la_uno`, comprobado con el mutante aplicado (`1 failed`) |
| 3 | `parte_records.py:113` `frozen=True` → `False` | Sin uso hoy, pero es diseño (§4 bis): test nuevo `..._el_motivo_es_inmutable_y_hashable`, comprobado (`DID NOT RAISE` → `1 failed`) |

La campaña no se relanza tras los tests nuevos (criterio del líder: supervivientes
analizados, no medir-tapar-medir).

## Verificaciones MANUAL pendientes (líder o humano)

- **M1 (R18, R20, T10)** · PDF real de la 0686 troceado en 3 páginas fuera del
  repo, sv2 local con `IA_PROVIDER=gemini` y el `GEMINI_MODEL` de producción,
  `curl` por página, **3 de 3 ejecuciones correctas por página** (DA3). Esperado:
  16/10 igual que hoy; 17/10 fila 2 = 12 extra, fila 3 = 10 extra, filas 1, 4, 5
  sin horas; 18/10 fila 2 = 14 extra y el resto sin horas. Anotar tabla
  proveedor · modelo · página · ejecución · horas por fila · `numero_linea_horas`
  · correcto (sin nombres ni DNIs). Si no se alcanza: `blocked` sin iterar el
  prompt. Comandos en `design.md` §9.
- **M2 (R19, T11)** · ≥ 5 partes laborables bien leídos hoy (los elige el humano),
  mismas horas por fila que lo aprobado en el portal.
- **Tras desplegar**: comprobar en los logs de sv3 el WARNING de lectura dudosa en
  el primer parte de fin de semana y que el portal lo enseña como pendiente de
  revisar. El orden de despliegue no importa (sv3 tolera la ausencia del campo).

## Fase RED (trazas reales)

**T1** · `cd services/partes-api && python -m pytest tests/test_f051_esquema.py -q`
(antes de T2):

```
E       pydantic_core._pydantic_core.ValidationError: 1 validation error for EmpleadoParte
E       numero_linea_horas
E         Extra inputs are not permitted [type=extra_forbidden, input_value=2, input_type=int]
E       KeyError: 'numero_linea_horas'
E       AssertionError: assert 'numero_linea_horas' in ['numero_linea', 'categoria', 'nombre', 'dni', 'horas_ordinarias', 'horas_extraordinarias', ...]
E                   AttributeError: 'EmpleadoParte' object has no attribute 'numero_linea_horas'
FAILED tests/test_f051_esquema.py::test_f051_r9_el_empleado_admite_numero_linea_horas_entero
FAILED tests/test_f051_esquema.py::test_f051_r10_el_json_schema_lo_pone_tras_numero_linea_y_antes_de_las_horas
FAILED tests/test_f051_esquema.py::test_f051_r11_una_respuesta_sin_el_campo_sigue_validando
... (11 FAILED en total)
11 failed, 1 passed in 0.70s
```

(El que pasa es R12, «sigue rechazando campos no declarados»: ya era cierto.)

**T3** · `cd services/partes-api && python -m pytest tests/test_f051_prompt.py -q`
(antes de T4; el test R1 «por_numero_y_dni» se llamaba entonces `..._por_nº_y_dni`):

```
E       AssertionError: falta el bloque LECTURA FILA A FILA
E       AssertionError: assert 'fila mas cercana' in 'eres un extractor de datos estructurados de partes de trabajo ...'
E       AssertionError: falta la vineta numero_linea_horas
E       assert '"dni"' in ': [\n      { "numero_linea", "categoria", "nombre",\n        "horas_ordinarias", ...'
E       AssertionError: assert 'numero_linea_horas es entero o null' in ': - ningun numero ni booleano puede ir como string. ...'
FAILED tests/test_f051_prompt.py::test_f051_r1_el_system_prohibe_la_fila_mas_cercana_y_la_de_arriba
FAILED tests/test_f051_prompt.py::test_f051_r6_vineta_numero_linea_horas_en_el_punto_3
FAILED tests/test_f051_prompt.py::test_f051_r7_el_schema_hint_lista_dni_y_numero_linea_horas
6 failed, 6 errors in 0.25s
```

(Los 6 errores son los tests del bloque: falla su fixture con «falta el bloque».)

**T5** · `cd services/partes-persistencia && python -m pytest tests/test_f051_lectura_dudosa.py -q`
(antes de T6):

```
tests\test_f051_lectura_dudosa.py:31: in <module>
    from application.services.lectura_dudosa import (
E   ModuleNotFoundError: No module named 'application.services.lectura_dudosa'
ERROR tests/test_f051_lectura_dudosa.py
1 error in 0.39s
```

**T6 → T7** · mismo comando con el detector ya escrito y sin cablear (el detector
pasa; normalizer, pipeline e interruptor siguen en rojo):

```
E       AssertionError: assert [] == [MotivoLectur...as=(3, 4, 5))]
E       TypeError: ParteNormalizer.__init__() got an unexpected keyword argument 'revisar_tabla_dispersa'
E           AssertionError: assert False is True
E            +  where False = <function PersistPartePipeline._compute_review_required at 0x...>(ParteDocumento(...
E                   AttributeError: 'Settings' object has no attribute 'revisar_tabla_dispersa'
FAILED tests/test_f051_lectura_dudosa.py::test_f051_r15_el_normalizer_anota_la_lectura_dudosa_y_avisa
FAILED tests/test_f051_lectura_dudosa.py::test_f051_r15_lectura_dudosa_sube_review_required
FAILED tests/test_f051_lectura_dudosa.py::test_f051_r15_la_ingesta_guarda_el_parte_disperso_para_revisar
FAILED tests/test_f051_lectura_dudosa.py::test_f051_r14_interruptor_encendido_por_defecto
FAILED tests/test_f051_lectura_dudosa.py::test_f051_r14_build_app_pasa_el_interruptor_al_normalizer
... (10 FAILED en total)
10 failed, 32 passed in 2.17s
```

Verde tras cada tarea: T2 `20 passed` (esquema + F-023); T4 sv2 `32 passed`;
T7 sv3 `2252 passed in 11.50s` (los de F-003 R26 y F-048 sin tocar: `git diff dev
--stat -- services/partes-persistencia/tests` solo lista el fichero nuevo).

## Evidencias

| Evidencia | Valor real |
|---|---|
| `bash harness/init.sh` (HEAD `dea6ede`) | **ENTORNO LISTO**; raíz `493 passed, 3 skipped in 116.44s` |
| Suite sv2 (`services/partes-api`) | `32 passed in 1.47s` (24 nuevos de F-051 + 8 de F-023 sin tocar) |
| Suite sv3 (`services/partes-persistencia`) | `2254 passed in 52.77s` (44 nuevos de F-051) |
| Suites sv1, sv4, sv5 | en verde (caché: árbol sin cambios) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 66 líneas cambiadas cubiertas (66/66, umbral 80%)` |
| Mutación | 20 evaluados de 31, 17 muertos, 3 supervivientes (1 equivalente, 2 cazados con tests nuevos), 0 timeouts, 207.0 s |
| Tamaño | `PUERTA TAMAÑO: requirements 148/150, design 249/250` |
| ruff | 734 avisos frente a 732 en `dev`: los 2 de más son `UP045` (`Optional[int]`) en `parte_models.py` y `parte_records.py`, el mismo estilo que el resto de esos ficheros; los `I001` de los tests nuevos, corregidos |

## Qué falta para cerrar

M1 y M2 (arriba, del líder), la línea de `azure-apps/partes.md` y el reviewer.
El despliegue (sv2 y sv3, sin orden obligado) lo pide el humano.
