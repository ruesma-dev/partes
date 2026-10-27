<!-- progress/review_F-059.md -->
Revisión incremental desde d50207f (pasada 2) · HEAD `800a681`

# F-059 · Review — página escaneada a la IA como imagen derecha (sv2)

**Veredicto (pasada 2): APPROVED.** El único cambio requerido de la pasada 1 (C4, comando
exacto de la M4) está hecho y la observación 1 cerrada con un mutante que ahora muere.

**Nivel de rigor: `estandar`** (declarado en `harness/features.json`): C1–C5, C3 bis, C4 bis
con fase RED, cobertura ≥ 80 % de las líneas cambiadas y mutación muestreada con los
supervivientes analizados. Sin exigencia de cero supervivientes; RM5 N/A por nivel.

## Pasada 2 · lo verificado (delta `d50207f..800a681`, resultado real)

- **Delta**: un solo commit del implementer (`800a681`, más mi `b06bd37`): `progress/current.md`,
  `progress/impl_F-059.md`, `design.md` §9, `tasks.md` T10 y
  `services/partes-api/tests/test_f059_pipeline.py`. **Ningún fichero de producción**
  (`git diff --name-only d50207f..HEAD -- services infra docs harness` ⇒ solo ese test): nada
  invalida lo aprobado en la pasada 1, el alcance de la campaña no cambia.
- **Cambio 1 (C4) [x]**: `current.md` lleva la M4 como `[ ]` con el despliegue
  (`.\infra\redeploy_partes.ps1 -Solo sv2`, lo lanza el humano), el SELECT literal de solo
  lectura, el resultado esperado (`convertida`, ningún `error`) y la vuelta atrás; el mismo
  SELECT en `impl_F-059.md`, `design.md` §9 y `tasks.md` T10. Contrastado con el código:
  tabla `parte_documents`, `raw_extraction_json` `Text` (de ahí el `::jsonb`) y
  `created_at_utc` `String(64)` (`orm_models.py:74,175,177`); `-Solo` existe en
  `redeploy_partes.ps1:35`; `ca-sv2-extraccion` y `rg-partes-dev` son los de `infra/`.
  «Evidencias» trae los **4 workers**.
- **Observación 1 [x]**: R12 y R13 fijan el final (`f"sha256={SHA_PDF[:12]}:"`). Mutante
  `sha256[:12]` → `[:13]` (`extract_parte_pipeline.py:116`) aplicado por mí en una **copia de
  `services/partes-api` en el scratchpad**: `test_f059_pipeline.py` ⇒ **5 failed, 17 passed**
  (R12 y las 4 de R13, como dice el informe); suite de sv2 entera ⇒ 6 failed, 142 passed.
  Sin mutar, sv2 en el worktree ⇒ **148 passed**. Copia borrada; `git status` limpio.
- **`bash harness/init.sh`** ⇒ **ENTORNO LISTO**: raíz 498 passed / 3 skipped; sv1–sv5 en
  verde; COBERTURA `[OK]` 99,4 % (164/165); TAMAÑO en verde (design 250/250, impl 220/220).
- **Campaña no reejecutada** en la pasada 2: el delta no toca el alcance (RM1: los ficheros
  mutados no cambian) y la pasada 1 ya la reejecutó entera (42,2 s < 60 s).

## Pasada 1 · lo verificado (`dev...d50207f`, resumen)

- init.sh verde; sv2 148 passed; con un venv solo desde `infra/manifests/sv2/requirements.txt`
  los SDK reales resuelven y los dobles no se activan. `build_images_partes.ps1:59–61` mete
  pypdf y Pillow en la imagen sin tocar el `Dockerfile`; el worker usa el pipeline de `build_app`.
- **Límite de servicio**: solo `services/partes-api/`, `infra/manifests/sv2/`, `docs/`,
  `progress/`, `specs/`. Nada en sv1, sv3–sv5 ni ORM; ninguna lógica copiada.
- **Logs sin datos**: WARNING de R13 solo con `type(exc).__name__` y `sha256[:12]`, sin
  `exc_info`; INFO sin nombre de fichero; `meta.adjunto_ia` sin `filename`.
- **Un fallo de conversión nunca tumba la extracción** (`except Exception` con `noqa`
  justificado; 4 excepciones probadas). `meta.source_*` y sha256 son del original (R16); sv3
  guarda el envelope entero y la dedup no cambia.
- **azure-apps** `7cc2e66` (sin push): §3.2 y fila sv2 de §5.6, sin secretos.

## Mutación (C4 bis)

- Recálculo puro (`harness.alcance` + `generar_mutantes`): **366 líneas, 49 mutantes** = el
  informe. «Tiempo total» 42,2 s < 60 s ⇒ **campaña reejecutada entera** en la pasada 1 con
  `--salida` en el scratchpad: misma muestra (20 de 49, semilla 20260820), **19 muertos,
  1 superviviente, 0 timeouts, 0 sin veredicto**, 4 workers. Cuadra: los 17 muertos del
  informe + [16] y [20] cerrados por los 4 tests de 198fe85; el superviviente es el [19].
- **RM1**: midió `319d951`; lo posterior no toca el alcance. **RM2**: 2,1 s × 4 workers ≈ 8,4 s
  por mutante frente a base 6,5 s: coherente.
- **RM3 / [19]** (`<=` → `<` en la proporción): equivalente comprobado (`0.02` tiene numerador
  impar sobre 2^58 y `abs(q−1)` es exacto y múltiplo de 2^-53: la igualdad es inalcanzable);
  sale superviviente, no muerto. RM5 N/A (nivel `estandar`).
- **RM4** sobre los mutantes del pipeline fuera de la muestra: `is None` → `is not None` muere
  (7 fallos); `sha256[:13]` sobrevivía en la pasada 1 y **muere desde la pasada 2** (arriba).
- **RM6**: no se quitó ninguna guarda. Sin «⚠ CAMPAÑA NO VÁLIDA»; ningún `PENDIENTE`.

## Checkpoints (estado en `800a681`)

- **C1** [x] init.sh exit 0 · [x] ficheros del arnés presentes.
- **C2** [x] solo F-059 `in_progress` · [x] rama `feature/F-059-pagina-como-imagen-derecha`
  · [x] `current.md`: F-059 es la activa, con su pendiente T10 · [x] `history.md`: F-059 no
  está `done`.
- **C3** [x] hexagonal: modelo y puerto sin infraestructura; pypdf y Pillow solo en
  `infrastructure/document/`; la decisión en `application/` · [x] primera línea con la ruta
  en los `.py` del diff (también el test tocado en la pasada 2) · [x] sin `print`, TODO ni
  secretos · [x] dependencias = las de la spec · [x] trampas del dominio no aplican.
- **C3 bis** N/A: la feature no añade ni toca nada en `docs/referencia/`.
- **C4** [x] cada requisito con test trazable, todo en verde · [x] sin red ni BBDD · [x] MANUAL
  con comando exacto: M0–M3 en `progress/banco_F-059.md` y **M4 con su SELECT literal**
  en `current.md` (pasada 2).
- **C4 bis** [x] `rigor` declarado · [x] fase RED con trazas reales (T2, T3: 67 failed, T4: 22,
  T6: 18) · [x] cobertura `[OK]` 99,4 % · [x] informe de la herramienta, totales recalculados
  · [x] muertos comprobados reejecutando · [x] RM1 · [x] RM2 · N/A RM5 (nivel `estandar`)
  · [x] RM6 · N/A campaña manual (la automática generó 49) · [x] supervivientes analizados
  · [x] «Evidencias» con los cuatro números y los workers · [x] ningún N/A sin justificar.
- **C4 ter** N/A: el repositorio no declara `harness/rutas_sensibles.json`.
- **C5** [x] T1–T9 y T11 `[x]` con commit `F-059 Tn:`; T10 en `[ ]` por ser MANUAL del humano
  tras desplegar (criterio de F-054) · [x] árbol limpio · [x] `features.json` coherente.

## Cobertura requisito → test (`services/partes-api/tests/`)

| Req | Test(s) |
|---|---|
| R1–R4 | `test_f059_conversor.py::test_f059_r1_…`, `…_r2_el_giro_se_normaliza_modulo_360`, `…_r3_la_marca_queda_arriba_a_la_izquierda`, `…_r4_ancho_y_alto_se_intercambian_…` |
| R5 | `…::test_f059_r5_jpeg_rgb_calidad_90_y_sin_exif`, `…_r5_la_calidad_se_puede_configurar`, `…_r5_la_escala_de_grises_sale_en_rgb` |
| R6–R8 | `…_r6_varias_paginas_no_aplica`; `…_r7_*` (2); `…_r8_*` (3) |
| R9–R10 | `…_r9_imagen_que_no_cubre_la_pagina`, `…_r9_dentro_de_las_tolerancias_si_aplica`; `…_r10_giro_que_no_es_multiplo_de_90` |
| R11 | `test_f059_pipeline.py::test_f059_r11_activa_el_cliente_recibe_la_imagen`, `…_r11_extremo_a_extremo_rotate_270` |
| R12 | `…::test_f059_r12_no_aplica_manda_el_pdf_byte_a_byte_e_info` (sha12 con final fijo) |
| R13 | `…::test_f059_r13_fallo_manda_el_pdf_con_warning_sin_datos` (4 excepciones, corte exacto a 12); conversor: `test_f059_r13_*` (3) |
| R14–R15 | `…_r14_*` (4: interruptor, constructores, proveedor fuera de lista, lista por proveedor); `…_r15_una_foto_no_pasa_por_el_conversor` |
| R16–R17 | `…_r16_meta_source_es_del_documento_recibido` (+ extremo a extremo); `…_r17_traza_de_la_convertida`, `…_r17_sin_nombre_de_fichero_en_la_traza` |
| R18–R19 | `…_r18_debug_lleva_el_sha256_de_la_imagen`, `…_r18_debug_sin_convertir_es_el_pdf`; `…_r19_info_con_giro_medidas_y_bytes` |
| R20–R21 | `test_f059_config.py::test_f059_r20_*`; `…_r21_un_nombre_desconocido_tumba_el_arranque`, `…_r21_vacio_es_ningun_proveedor` |
| R22 | `…::test_f059_r22_*` (detail high/low/auto, vacío/None, defecto, PDF sin detail) |
| R23 | `test_f023_empresa_membrete.py`, `test_f051_esquema.py`, `test_f051_prompt.py` sin tocar, en verde |
| R24 | `…::test_f059_r24_requirements_de_sv2_declara_pypdf_y_pillow` (+ venv del reviewer) |
| R25–R29 | MANUAL del líder en `progress/banco_F-059.md` (M0 22/22, M1 12/12, M2 4/4, M3 sin regresión); R29 = M4 del humano tras desplegar, con comando exacto en `current.md` |

## Cambios requeridos

Ninguno. (Pasada 1: cambio 1, la M4 sin comando exacto ⇒ hecho en `800a681`.)

## Observaciones (no bloquean)

1. ~~`sha256[:13]` sobrevive~~ ⇒ cerrada en la pasada 2.
2. `azure-apps/partes.md` dice «sin desplegar»: actualizarlo tras la M4, en ese trabajo.
3. Instalar los SDK de IA en el `.venv` de la raíz dejaría de sobra los dobles (que hoy cumplen).
4. Antes de pasar a `done` queda la M4 (T10) del humano: desplegar sv2 y correr el SELECT.

**Automejora (propuesta, no aplicada)**:
- `CHECKPOINTS.md` C4: añadir «un SELECT sin escribir no es un comando exacto» (segunda vez
  que se cae aquí: F-034, F-059).
- `rigor.json` / `tamano`: el tope de 140 líneas del review se alcanza ya en la pasada 1 de una
  feature mediana; o se sube para las pasadas 2+ o se acepta que la pasada 2 resuma la 1
  (lo hecho aquí).
