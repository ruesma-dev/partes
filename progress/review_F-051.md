<!-- progress/review_F-051.md -->
Revisión completa (pasada 1), `git diff dev...HEAD` con HEAD `8818271`.

# F-051 · Extracción fila a fila — review

- **Veredicto: APPROVED**
- **Nivel de rigor:** `estandar` (declarado en `harness/features.json`). Exige fase RED,
  cobertura de lo cambiado ≥ 80 % y campaña de mutación muestreada (20, semilla
  `20260820`) con los supervivientes analizados. RM5 no aplica (solo `critico`).
- **Fuera del veredicto, por encargo del líder:** M1 (T10) y M2 (T11), la verificación
  con el PDF real contra el modelo, y la línea de `azure-apps/partes.md` para
  `REVISAR_TABLA_DISPERSA`. Las tres constan como pendientes en `progress/impl_F-051.md`
  y en `progress/current.md`; el texto que se propone para azure-apps está en el informe.

## Verificación ejecutada (resultados reales)

| Qué | Resultado |
|---|---|
| `bash harness/init.sh` | exit 0, **ENTORNO LISTO**; raíz `493 passed, 3 skipped` |
| Suite sv2 (sin caché, la lancé yo) | `32 passed in 1.22s` (24 de F-051 + 8 de F-023) |
| Suite sv3 (sin caché, la lancé yo) | `2254 passed in 29.09s` |
| Suites sv1, sv4 y sv5 | verdes (caché de init.sh: no hay diff fuera de sv2 ni sv3) |
| PUERTA COBERTURA | `[OK] 100.0% de 66 líneas cambiadas (66/66, umbral 80%)` |
| PUERTA TAMAÑO | `[OK]` requirements 148/150, design 249/250, impl 186/220 |
| Tests existentes tocados | ninguno: `git diff dev...HEAD --stat` en `tests/` solo lista los 3 `test_f051_*` nuevos |
| `git status` al terminar | limpio |

## Lo que pedía comprobar el líder

- **Prompt R1–R8.** El diff de `prompts.yaml` tiene exactamente tres hunks: una viñeta
  al final de las «Reglas absolutas» de `system`, el bloque «LECTURA FILA A FILA» y la
  viñeta `numero_linea_horas` dentro del punto 3, y `schema_hint` (`numero_linea_horas`
  y `dni` en empleados, más una línea en «Reglas de tipo», que va dentro de
  `schema_hint`). Cabecera, firma, puntos 4–6 y el catálogo de horas no cambian, y los
  8 tests de F-023 pasan sin haberlos tocado (R8). La línea «Para cada fila, rellena:»
  es un añadido de redacción permitido por el §5 del diseño; el implementer la anota.
- **JSON Schema real.** Gemini recibe `response_model.model_json_schema()` como
  `response_json_schema` (`gemini_genai_client.py:104,128`), y `schema_registry` mapea
  `parte_trabajo` → `ParteTrabajo`. El test R10 comprueba ese mismo esquema:
  `numero_linea_horas` va justo después de `numero_linea` y antes de las dos horas,
  de tipo `integer|null` y sin cotas. R11: si el campo falta, el parseo da `None`.
  R12: `extra="forbid"` sigue activo. sv4 y sv5 no parsean `raw_extraction_json` con
  un modelo estricto, así que la clave nueva no rompe a nadie.
- **Red de sv3 pura (R17).** `lectura_dudosa.py` solo importa `domain.models.parte_records`:
  ni Sigrid, ni BBDD, ni calendario. El normalizer solo asigna `parte.lectura_dudosa`
  antes del bucle de filas; `test_f051_r17_los_registros_no_cambian` demuestra que los
  registros salen iguales. En `_compute_review_required` hay un único `return True`
  nuevo, colocado después de las condiciones existentes y antes del bucle; no hay
  ninguna rama `return False` antes, así que solo puede subir el flag. Ningún otro
  camino de sv3 recalcula o baja `review_required` (`marcar_review_required` nunca lo
  baja).
- **El interruptor apaga solo `tabla_dispersa`.** El flag solo entra en
  `if tabla_dispersa and alguna_con_horas and vacias`; la autocomprobación no lo
  consulta. Lo demuestran `test_f051_r14_con_el_interruptor_apagado_no_hay_tabla_dispersa`
  y `..._el_normalizer_respeta_el_interruptor`, y la R13 se prueba con `tabla_dispersa=False`.
  `Settings` lo tiene a `True` por defecto, se apaga por entorno y `build_app` lo pasa
  al normalizer (es el único sitio de producción que construye uno;
  `medir_casado_recursos.py` es un script de medición y usa el defecto).
- **LÍMITE DE SERVICIO.** sv2 pide el dato y sv3 lo juzga, sin lógica copiada entre
  servicios. No se toca ninguna gemela de la lista cerrada de `CLAUDE.md` ni las dos
  `orm_models.py`. `_a_float` y `_a_int` repiten dentro de sv3 la tolerancia de tipos
  del normalizer para evitar un import circular. Está justificado en el informe y no
  cruza servicios.
- **Datos personales.** Los tests usan nombres sintéticos («TRABAJADOR UNO»…,
  «Trabajador A») y DNIs de relleno que ya existían en el repo (`11111111H` está en
  `test_f013_informe_sesame.py` de sv4). Un barrido de `\d{8}[A-Z]` y `[XYZ]\d{7}[A-Z]`
  sobre las líneas añadidas solo da esa lista. Spec, ARCHITECTURE e informes solo
  citan la obra 0686 y las fechas. El WARNING lleva fecha, nº de obra, motivo y filas,
  y hay un test que comprueba que no aparecen ni nombres ni DNIs.

## Mutación (C4 bis, RM1–RM6)

- **Tiempo total 207 s, por encima de 60 s: no reejecuté la campaña.** Apliqué el
  recálculo puro, RM1–RM6 y RM4 sobre una copia.
- **Recálculo independiente** (`harness.alcance` + `generar_mutantes`, script en el
  scratchpad): da 162 líneas en 7 ficheros y **31 mutantes**, lo mismo que el informe.
  Repetí el sorteo con `random.Random(20260820).sample(…, 20)`: salen los mismos 20, y
  entre ellos los 3 supervivientes, con el mismo operador y el mismo texto
  original → mutado (`:32` logico, `:73` entero, `parte_records.py:113` booleano).
- **RM1.** La campaña se midió en `b06420b…`. De ahí a HEAD solo cambian tests,
  `progress/` y `tasks.md`; ningún fichero del alcance, así que el alcance medido es
  el que reviso.
- **RM2.** Línea base 26–27 s; media 10,4 s × 3 workers = 31 s por mutante, coherente
  con la base y con 17 de 20 muertos con `-x`. `20 × 10,4 ≈ 207 s`. El coste por
  mutante (207 × 3 / 20 ≈ 31 s) está muy por encima de 1 s. Ni «CAMPAÑA NO VÁLIDA» ni
  filas sin veredicto.
- **RM3.** Repasé los 17 muertos: todos cambian el comportamiento (el `or`↔`and` de las
  condiciones, `is None`↔`is not None`, `==`, el flag a `False`, la clave de orden).
  Ninguno es equivalente.
- **RM4.** Sobre una copia de sv3 en el scratchpad apliqué los dos supervivientes
  «cazados». `n or 1` hace fallar `..._una_fila_cero_se_ordena_antes_que_la_uno`
  (`1 failed, 43 passed`) y `frozen=False` hace fallar `..._el_motivo_es_inmutable_y_hashable`
  (`1 failed, 43 passed`). Lo que declara el informe se confirma.
- **Equivalente `:32`** (`or` → `and` en `_a_float`): la justificación escrita es
  correcta, porque `None` y `""` acaban en `None` por la excepción de `float()`. Por
  ser rigor `estandar`, RM5 es N/A.
- **RM6.** No se quitó ninguna guarda para matar mutantes: los dos huecos se cerraron
  añadiendo tests.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] existen los ficheros base.
- **C2** [x] solo F-051 en `in_progress` · [x] rama `feature/F-051-extraccion-fila-a-fila`
  · [x] `current.md`: la sección de F-051 está arriba y lo demás es el registro
  acumulado de pendientes que ya había en `dev` (mismo criterio que en las reviews de
  F-046 y F-048) · [x] las `done` tienen resumen en `history.md`.
- **C3** [x] hexagonal: `MotivoLectura` vive en domain para que `ParteDocumento` no
  importe de application · [x] primera línea con la ruta en los ficheros nuevos ·
  [x] sin prints, secretos ni dependencias nuevas; ruff pasa de 732 a 734 avisos por
  dos `UP045` (`Optional[int]`), el mismo estilo que el resto de esos ficheros · [x]
  trampas: empleado ≠ recurso, incidencias y schema duplicado no se tocan (ni casado,
  ni registro, ni ORM).
- **C3 bis** N/A: la feature no toca `docs/referencia/`.
- **C4** [x] R1–R17 con tests verdes (tabla abajo) · [x] sin red ni BBDD: el YAML real,
  Pydantic y dobles del repositorio · [x] M1 y M2 listadas como pendientes en
  `current.md` e `impl_F-051.md`; el comando exacto (`curl … /v1/partes/extract`) está
  en `design.md` §9, enlazado desde el informe.
- **C4 bis** [x] `rigor: estandar` declarado · [x] fase RED con trazas reales de T1, T3,
  T5 y T6→T7 · [x] cobertura `[OK]` 100 % · [x] `mutacion_F-051.md` generado y
  verificado (arriba) · [x] muertos: campaña de más de 60 s, recálculo puro más RM4,
  dicho aquí · [x] coste por mutante coherente · [x] sin cabecera de campaña no válida
  · [x] RM1 · [x] RM2 · N/A RM5, por nivel `estandar` · [x] RM6 · N/A campaña manual,
  porque la automática generó 31 · [x] los 3 supervivientes analizados, ninguno en
  PENDIENTE · [x] «Evidencias» con tests, cobertura, mutantes y tiempo de suite, y los
  workers (`--workers 3`) en T9 y en el informe de mutación.
- **C4 ter** N/A: el repo no declara `harness/rutas_sensibles.json`, solo el ejemplo.
  Ver la automejora 1.
- **C5** [x] T1–T9 y T12 en `[x]`, con un commit `F-051 Tn:` cada una (T8 en dos
  commits, explicado). T10 y T11 están en `[ ]`: son las verificaciones MANUAL
  M1 y M2, que el líder hace aparte; están documentadas como pendientes · [x] árbol
  limpio · [x] `features.json` en `in_progress`, a la espera de esta review y de M1 y M2.

## Cobertura requisito → test

| Req | Test(s) |
|---|---|
| R1 | `test_f051_r1_el_system_prohibe_…`, `…_identifica_la_fila_por_numero_y_dni`, `…_el_bloque_cubre_todas_las_cifras_de_la_fila` |
| R2 | `test_f051_r2_recorrido_fila_a_fila_hasta_ord_y_extraord` |
| R3 | `test_f051_r3_celda_vacia_es_null_…`, `…_advierte_de_las_pocas_cifras_sueltas` |
| R4 | `test_f051_r4_escaneos_girados_y_cifras_que_invaden_la_vecina` |
| R5 | `test_f051_r5_todas_las_filas_con_trabajador_…` |
| R6 | `test_f051_r6_vineta_numero_linea_horas_en_el_punto_3`, `…_la_vineta_va_tras_numero_linea_…` |
| R7 | `test_f051_r7_el_schema_hint_lista_dni_y_numero_linea_horas`, `…_las_reglas_de_tipo_dicen_entero_o_null` |
| R8 | 8 tests de F-023 sin tocar y en verde, más el diff de `prompts.yaml` revisado arriba |
| R9 | `test_f051_r9_*` (entero, null, fuera de rango y sin cotas en el esquema) |
| R10 | `test_f051_r10_el_json_schema_lo_pone_tras_numero_linea_…`, `…_lo_declara_entero_o_null` |
| R11 | `test_f051_r11_una_respuesta_sin_el_campo_sigue_validando` |
| R12 | `test_f051_r12_el_empleado_sigue_rechazando_campos_no_declarados` |
| R13 | `test_f051_r13_*` (9 tests: ordinaria, extra negativa, varias filas, coherente, sin horas, sin `numero_linea`, texto, ilegibles) |
| R14 | `test_f051_r14_*` (caso 17/10 leído y en papel, incidencia, trabajador, interruptor en detector, normalizer, Settings y build_app) |
| R15 | `test_f051_r15_*` (normalizer + WARNING sin datos personales, dos motivos, `_compute_review_required`, ingesta completa) |
| R16 | `test_f051_r16_sin_numero_linea_horas_no_salta` (ausente, null, ""), `…_parte_anterior_sin_la_clave_…` |
| R17 | `test_f051_r17_*` (registros iguales, `review_required` como hoy, parte lleno y coherente sin revisión, entradas no-dict) |
| R18–R20 | MANUAL M1 y M2 (T10, T11), pendientes del líder y fuera de este veredicto |

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean)

1. `docs/referencia/partes-proyecto.md` (el documento maestro) no menciona la lectura
   dudosa ni `REVISAR_TABLA_DISPERSA`. F-046 sí anotó ahí su interruptor. El diseño no
   lo pedía; queda a criterio del líder.
2. `_a_int` acepta `True` y trunca los float (`int(2.7)` da 2). Hoy no tiene efecto,
   porque sv2 valida `Optional[int]` antes de mandar el dato.

## Automejora propuesta (no aplicada)

1. **Declarar `harness/rutas_sensibles.json` en este repo**, con
   `services/partes-api/config/prompts.yaml` y `domain/models/parte_models.py` →
   informe de verificación con el PDF o el modelo (por ejemplo
   `progress/m_F-XXX.md`), exigencia `aviso`. Un cambio de prompt no se puede
   verificar con tests unitarios, y hoy C4 ter queda N/A justo en el caso para el que
   se diseñó.
2. **En `CHECKPOINTS.md` C5**, aclarar que una tarea `MANUAL (humano o líder)` de
   `tasks.md` puede seguir en `[ ]` al pasar la review si consta como pendiente en
   `current.md`. Hoy cada reviewer lo justifica por su cuenta.
