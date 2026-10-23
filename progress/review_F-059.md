<!-- progress/review_F-059.md -->
Revisión completa (pasada 1) · `dev...HEAD` = `d50207f`

# F-059 · Review — página escaneada a la IA como imagen derecha (sv2)

**Veredicto: CHANGES_REQUESTED** — por un solo punto documental (C4: el comando exacto de la
M4 no está escrito en ningún sitio). Código, tests, mutación y banco, bien.

**Nivel de rigor: `estandar`** (declarado en `harness/features.json`). Exige C1–C5, C3 bis,
C4 bis con fase RED, cobertura ≥ 80 % de las líneas cambiadas y mutación muestreada con los
supervivientes analizados. Sin exigencia de cero supervivientes; RM5 N/A por nivel.

## Lo verificado por el reviewer (resultado real)

- `bash harness/init.sh` ⇒ **ENTORNO LISTO**, exit 0; raíz 498 passed / 3 skipped; COBERTURA
  `[OK]` 99,4 % (164/165). Suite de sv2 en el `.venv` de la raíz: **148 passed**.
- **Dobles de SDK (desviación 2)**: venv nuevo en el scratchpad instalado SOLO desde
  `infra/manifests/sv2/requirements.txt` (+ pytest) ⇒ resuelve limpio en Python 3.12
  (openai 3.37.0, anthropic 2.2.0, google-genai 2.33.0, pypdf 6.21.2, Pillow 13.0.0). Con los
  SDK reales la suite da **148 passed** y `instalar_si_faltan()` deja `openai.OpenAI`,
  `anthropic.Anthropic` y `genai.Client` reales: los dobles no se activan ni enmascaran nada
  (y el banco M1–M3 usó el SDK real con `image_detail="high"`).
- **Imagen Docker**: `build_images_partes.ps1:59–61` copia el `requirements.txt` del manifiesto
  al contexto y el `Dockerfile` lo instala: pypdf y Pillow entran sin tocar el `Dockerfile`. El
  worker (`main_worker.py:62`) usa el pipeline de `build_app`, donde se cablea el conversor.
- **Límite de servicio**: el diff solo toca `services/partes-api/`, `infra/manifests/sv2/`,
  `docs/`, `progress/`, `specs/` y el arnés. Nada en sv1, sv3–sv5 ni ORM; ninguna lógica
  copiada (sv1 usa pypdf para trocear, sv2 para leer la estructura: fuera de la lista cerrada).
- **Logs sin datos**: WARNING de R13 solo con `type(exc).__name__` y `sha256[:12]`, sin
  `exc_info` ni mensaje; INFO de no-aplica y de convertida, sin nombre de fichero; el test lo
  comprueba con un nombre y un DNI ficticios. `meta.adjunto_ia` sin `filename`.
- **Un fallo de conversión nunca tumba la extracción**: `convertir` va dentro de un
  `except Exception` (con `noqa` justificado); el resto de `_preparar_para_ia` no puede lanzar.
  Tests con `ValueError`, `OSError`, `DecompressionBombError` y `KeyError`; el conversor real
  lanza ante no-PDF, JPEG truncado e imagen no JPEG (R13 del conversor).
- **`meta.source_*` y sha256 del original**: el sha se calcula sobre `request.file_bytes` y
  `_envelope` recibe `attachment=original` (R16, test explícito y de extremo a extremo con
  el conversor real). sv3 lee `envelope.get("meta")` (`persist_parte_pipeline.py:138`) y
  guarda el envelope entero: la clave nueva no le afecta y la dedup no cambia.
- **azure-apps** `7cc2e66` (master, sin push): §3.2 y fila sv2 de §5.6 con las variables,
  defectos, vuelta atrás y dependencias; sin secretos. Trailer correcto.

## Mutación (C4 bis)

- Recálculo puro con `harness.alcance` + `harness.mutacion.generar_mutantes`: **366 líneas,
  49 mutantes** (pipeline 4, settings 3, modelo 1, conversor 39, app 2) = el informe.
- «Tiempo total» 42,2 s **< 60 s ⇒ campaña reejecutada entera** con `--salida` en el
  scratchpad (`mutacion_F-059_reviewer.md`, fuera de `progress/`; `git status` limpio después).
  Misma muestra (20 de 49, semilla 20260820): **19 muertos, 1 superviviente, 0 timeouts,
  0 sin veredicto, 38,8 s**, líneas base 5,2–5,3 s, 4 workers. Cuadra con el informe: sus
  17 muertos + [16] y [20], que mueren ahora con los 4 tests de 198fe85; el superviviente es
  el [19], el declarado equivalente.
- **RM1**: el informe midió `319d951`; `319d951..HEAD` solo toca `progress/`, `tasks.md` y
  tests (nada del alcance); la mía mide `d50207f`. **RM2**: 2,1 s × 4 workers = 8,4 s por
  mutante frente a base 6,5 s (la mía: 7,8 frente a 5,2). Coherente; muy por encima de 1 s.
- **RM3 / equivalente [19]** (`<=` → `<` en la proporción): comprobado. `0.02` es
  `5764607523034235 / 2**58` (numerador impar) y `abs(q−1)` con `q` en [0,5, 2] es exacto
  (Sterbenz) y múltiplo de 2^-53: la igualdad es inalcanzable. Equivalente de verdad, y sale
  superviviente, no muerto. RM5 N/A (nivel `estandar`: basta la justificación escrita).
- **RM4** (copia en el scratchpad) sobre los 4 mutantes del pipeline, que la muestra no
  tocó: `if resultado.adjunto is None` → `is not None` ⇒ 7 fallos (muerto);
  `sha256[:12]` → `[:13]` ⇒ **sobrevive a toda la suite de sv2** (ver observación 1).
- **RM6**: no se quitó ninguna guarda (T8 solo añadió tests). Sin «⚠ CAMPAÑA NO VÁLIDA»;
  «Sin veredicto (base rota)» = 0; ningún análisis en `PENDIENTE`.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros del arnés presentes.
- **C2** [x] solo F-059 `in_progress` · [x] rama `feature/F-059-pagina-como-imagen-derecha`
  · [x] `current.md`: F-059 es la activa; las otras secciones siguen por sus MANUAL pendientes
  (criterio de F-053/F-054) · [x] `history.md`: F-059 no está `done`.
- **C3** [x] hexagonal: el modelo y el puerto solo importan `dataclasses`/`abc` y dominio;
  pypdf y Pillow solo en `infrastructure/document/`; la decisión, en `application/` · [x]
  primera línea con la ruta en los 12 `.py` del diff · [x] sin `print`, TODO ni secretos
  (la clave de los tests es `clave-falsa-de-test`); dependencias nuevas = las de la spec ·
  [x] trampas del dominio no aplican (sv2 no toca recurso, incidencias ni ORM).
- **C3 bis** N/A: la feature no añade ni toca nada en `docs/referencia/`.
- **C4** [x] cada requisito con test trazable (tabla abajo), todo en verde · [x] sin red ni
  BBDD (cliente LLM y conversor falsos, PDF sintéticos en memoria) · **[ ] MANUAL con
  comando exacto: la M4 (T10, humano) no lo tiene.** `current.md` solo dice «T10 (M4 tras
  desplegar sv2, humano)»; `impl_F-059.md:167`, `design.md:224` y `tasks.md:17` dicen «un
  SELECT de solo lectura» sin escribirlo. Toda M de este repositorio lleva su SQL literal en
  `current.md`, y F-034 pasada 1 se rechazó exactamente por esto. → cambio 1.
- **C4 bis** [x] `rigor` declarado (`estandar`) · [x] fase RED con trazas reales de T2,
  T3 (esqueleto con `NotImplementedError`: 67 failed), T4 (22 failed) y T6 (18 failed) ·
  [x] cobertura `[OK]` 99,4 % · [x] informe de mutación de la herramienta, totales
  recalculados · [x] muertos comprobados reejecutando (< 60 s) · [x] coste por mutante ≈ 8 s
  · [x] sin cabecera de campaña no válida · [x] RM1 · [x] RM2 · N/A RM5 (nivel `estandar`,
  justificado arriba) · [x] RM6 · N/A campaña manual (la automática generó 49) · [x]
  supervivientes analizados · [x] «Evidencias» con tests, cobertura, mutantes y tiempo; los
  4 workers constan en la fila «Workers» del informe de mutación (no en «Evidencias»; se
  pide añadirlo en el cambio 1) · [x] ningún N/A sin justificar.
- **C4 ter** N/A: el repositorio no declara `harness/rutas_sensibles.json`.
- **C5** [x] T1–T9 y T11 `[x]` con su commit `F-059 Tn:`; T10 en `[ ]` por ser MANUAL del
  humano tras desplegar (mismo criterio que F-054) · [x] árbol limpio, sin temporales
  (`coverage.json` de sv2 está ignorado) · [x] `features.json` en `in_progress`, coherente.

## Cobertura requisito → test (`services/partes-api/tests/`)

| Req | Test(s) |
|---|---|
| R1–R4 | `test_f059_conversor.py::test_f059_r1_…`, `…_r2_el_giro_se_normaliza_modulo_360` (−90, −270, 450, 360, −180), `…_r3_la_marca_queda_arriba_a_la_izquierda`, `…_r4_ancho_y_alto_se_intercambian_…` (0/90/180/270) |
| R5 | `…::test_f059_r5_jpeg_rgb_calidad_90_y_sin_exif`, `…_r5_la_calidad_se_puede_configurar`, `…_r5_la_escala_de_grises_sale_en_rgb` |
| R6–R8 | `…_r6_varias_paginas_no_aplica`; `…_r7_contenido_que_no_es_una_imagen`, `…_r7_el_orden_q_cm_do_q_es_obligatorio`; `…_r8_imagen_no_soportada_no_aplica`, `…_r8_filtro_como_lista_de_uno_si_aplica`, `…_r8_escala_de_grises_si_aplica` |
| R9–R10 | `…_r9_imagen_que_no_cubre_la_pagina`, `…_r9_dentro_de_las_tolerancias_si_aplica` (borde exacto de 1 pt); `…_r10_giro_que_no_es_multiplo_de_90` |
| R11 | `test_f059_pipeline.py::test_f059_r11_activa_el_cliente_recibe_la_imagen`, `…_r11_extremo_a_extremo_rotate_270` |
| R12 | `…::test_f059_r12_no_aplica_manda_el_pdf_byte_a_byte_e_info` |
| R13 | `…::test_f059_r13_fallo_manda_el_pdf_con_warning_sin_datos` (4 excepciones); conversor: `test_f059_r13_*` (3) |
| R14–R15 | `…_r14_sin_conversor_es_el_interruptor_apagado`, `…_r14_los_constructores_de_antes_siguen_valiendo`, `…_r14_proveedor_fuera_de_la_lista_no_llama_al_conversor`, `…_r14_la_lista_es_por_proveedor_activo`; `…_r15_una_foto_no_pasa_por_el_conversor` (jpg, png, webp) |
| R16–R17 | `…_r16_meta_source_es_del_documento_recibido` (+ extremo a extremo); `…_r17_traza_de_la_convertida`, `…_r17_sin_nombre_de_fichero_en_la_traza` (+ R12–R15) |
| R18–R19 | `…_r18_debug_lleva_el_sha256_de_la_imagen`, `…_r18_debug_sin_convertir_es_el_pdf`; `…_r19_info_con_giro_medidas_y_bytes` |
| R20–R21 | `test_f059_config.py::test_f059_r20_*` (defectos, entorno, CSV, cableado ×3, log de wiring ×2); `…_r21_un_nombre_desconocido_tumba_el_arranque`, `…_r21_vacio_es_ningun_proveedor` |
| R22 | `…::test_f059_r22_*` (detail high/low/auto, vacío/None, defecto del cliente, PDF sin detail) |
| R23 | `test_f023_empresa_membrete.py`, `test_f051_esquema.py`, `test_f051_prompt.py` sin tocar, en verde; clientes de Gemini y Claude fuera del diff |
| R24 | `…::test_f059_r24_requirements_de_sv2_declara_pypdf_y_pillow` (+ venv del reviewer desde el manifiesto) |
| R25–R29 | MANUAL del líder, `progress/banco_F-059.md` (M0 22/22, M1 12/12, M2 4/4, M3 sin regresión); R29 = M4 del humano, pendiente (cambio 1) |

## Cambios requeridos

1. **`progress/current.md`, sección de F-059** (y la misma línea en `progress/impl_F-059.md:167`):
   escribir la M4 con su **comando exacto**: el despliegue (`.\infra\redeploy_partes.ps1
   -Solo sv2`, lo lanza el humano), el SELECT literal de solo lectura en la base `partes`
   —p. ej. `SELECT id, created_at_utc, raw_extraction_json::jsonb #>> '{meta,adjunto_ia,conversion}'
   AS conversion, raw_extraction_json::jsonb #>> '{meta,adjunto_ia,motivo}' AS motivo FROM
   parte_documents WHERE created_at_utc >= '<instante del despliegue>' ORDER BY
   created_at_utc DESC LIMIT 20;` (`raw_extraction_json` es `Text`, de ahí el `::jsonb`)—, el
   resultado esperado (las páginas escaneadas, `convertida`; ningún `error`) y la vuelta atrás
   ya escrita (`az containerapp update … PAGINA_COMO_IMAGEN=false`). De paso, añadir a
   «Evidencias» de `impl_F-059.md` que la campaña se lanzó con **4 workers**.

## Observaciones (no bloquean)

1. `sha256[:12]` → `[:13]` (pipeline:116, fuera de la muestra) sobrevive: R12/R13 buscan
   `sha256=<12>` como **subcadena**. Fijar el final (`f"sha256={SHA_PDF[:12]}:"`) lo mataría.
   R13 se cumple igual: el código corta en 12.
2. `azure-apps/partes.md` dice «sin desplegar»: actualizarlo tras la M4, en ese trabajo.
3. Instalar los SDK de IA en el `.venv` de la raíz dejaría de sobra los dobles (que hoy cumplen).

**Automejora (propuesta, no aplicada)**: `CHECKPOINTS.md` C4, añadir «un SELECT sin escribir
no es un comando exacto» (segunda vez que se cae aquí: F-034, F-059).
