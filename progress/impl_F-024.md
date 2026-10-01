# F-024 · Informe del implementer

Rama `feature/F-024-lineas-encoladas`. Rigor **critico**. Spec aprobada por
el humano el 2026-10-01 (DA1–DA15 según recomendación, DA15 incluida).
Servicios tocados: **sv5** (lectura) y **sv4**. sv3 no se toca (solo lo lee
el guardián de raíz). Sin cambio de schema. Ni una escritura en Sigrid.

## T1 · Inventario de tests afectados

- **Payload con líneas `registrado`**: ninguno. Los tests de aprobación de
  F-002/F-003/F-017 siembran líneas sin estado; los que siembran
  `registrado` (F-004, F-023) no aprueban.
- **`MOTIVO_LINEA_REGISTRADA`**: ningún test compara su texto.
- **Respuesta de `/api/aprobar/encolar`**: `test_f002_aprobar_encolar`,
  `test_f002_degradacion`; R27 solo añade claves. No se rompen.
- **Omitido en el inventario y visto en T16**: `test_f016_vista_admin_jornadas
  ::test_f016_r20_f016_no_anade_ni_cambia_ninguna_ruta_de_sigrid` cierra la
  lista de rutas `/api/sigrid/*`. Se adaptó **añadiendo** la ruta nueva de
  R17 a la lista (no se afloja el guardián), con la decisión en el docstring.

## Qué cambió

**sv5** (`services/partes-transfer`)
- `application/services/comprobacion_lineas.py` (nuevo): `LineaComprobar`,
  `Veredicto`, `clasificar` (pura, R2–R6) y `ComprobadorLineas` (dedupe,
  `lineas_por_synckey` → `lineas_por_ide` solo de los fallos →
  `partes_por_ide`; log `[comprobar]`).
- `infrastructure/sigrid/sigrid_write_client.py`: `lineas_por_ide` y
  `partes_por_ide` por `_read` (base de escritura, `max_rows` 1000,
  `truncated` ⇒ excepción), lotes `LOTE_COMPROBACION=200`. Nada de escritura.
- `interface_adapters/api/app.py`: `POST /api/registro/comprobar` (`def`,
  1–500 líneas por pydantic ⇒ 422, fallo ⇒ 502 sin veredictos);
  `build_app(settings, pipeline=None, comprobador=None)`.
- `main.py`: `ComprobadorLineas(cliente=cliente)` con el MISMO cliente.

**sv4** (`services/partes-front`)
- `congelacion.py`: `ESTADO_BORRADO_SIGRID`; motivo nuevo del candado (R16).
- `parte_repository.py`: `ESTADOS_EN_VUELO` + `borrado_sigrid` (R15);
  `lineas_para_registro(ids, *, incluir_borradas=False)` con `excluidas`
  (R22); `registrados_para_comprobar`, `aplicar_comprobacion_sigrid` (CAS por
  estado y `hmores_ide`, `with_for_update`) y `recuento_estados`.
- `application/services/comprobacion_sigrid.py` (nuevo):
  `RegistroComprobaciones` (TTL por id, sellado al reservar, lock, purga) y
  `ComprobacionSigrid` (lotes, para al primer lote fallido, log
  `[comprobacion-sigrid]`).
- `transfer_client.py`: `comprobar(payload, *, timeout_s)`.
- `config/settings.py`: `COMPROBACION_SIGRID_TTL_S=120` (≥0),
  `_TIMEOUT_S=30` (>0), `_LOTE=500` (1–500).
- `web/app.py`: `_payload_registro` devuelve `(payload, excluidas)` y 422
  con motivo (R23); `excluidas` en preflight/ejecutar/encolar y
  `registro_ids` al encolar (R27); `POST /api/sigrid/comprobar` y
  `POST /api/aprobar/estado` (`def`); `borradas_sigrid` en las dos vistas.
- Plantillas `obra_detail.html` / `trabajador_detail.html`:
  `data-sigrid-estado` normalizado en cada fila, rama «✗ borrada en Sigrid»
  + «Reaprobar» (`data-incluir-borradas="1"`), aviso de cabecera, botón
  «Comprobar en Sigrid» (`data-origen`), contenedor `#sigrid-aviso`, tooltip
  de `encolado` sin «recarga». Las ramas comparan el estado normalizado.
- `static/app.js` (+ 3 reglas en `styles.css`): `comprobarVista()` al cargar
  (AbortController 90 s), botón con modal de resultado, sondeo del modal
  tras encolar (3 s / 120 s) sin `reload()` prematuro, aviso de encoladas
  (15 s / 30 min) con «Actualizar», casilla «Incluirlas» en el preflight y
  botón «Incluir las borradas en Sigrid» si el 422 solo traía borradas.

**Raíz**: `tests/test_f024_borrado_no_congela_gemelos.py` (R13, sv3 y sv4
en subprocesos). **Docs**: `docs/ARCHITECTURE.md` (+8 netas) y
`azure-apps/partes.md` (commit local `03f994c` en ese repo, sin push).

## Commits (rama de la feature)

`16da3a2` T1 · `4e2363b` T2 · `5381260` T3 · `0b3826c` T4 · `0c92944` T5 ·
`0beaf74` T6 · `8a64ee8` T7 · `c0d0620` T8 · `fced683` T9 · `331c3ce` T10 ·
`78ee961` T11 · `77c4d36` T12 · `216be6a` T13 · `3983533` T14 · `ec2ff3c`
T15 · `7afeb8b` T16 · `156d6e3` estilo (ruff) · `46c650b` T17 ·
T18 (este informe y `current.md`).

## Fase RED (trazas reales, comando y líneas E/FAILED)

Comando en cada servicio: `../../.venv/Scripts/python.exe -m pytest -q
tests/<fichero> -k <filtro>`. Para R2–R4, R19 y R14/R17 se creó antes un
esqueleto con las firmas que lanza `NotImplementedError`, para que la traza
sea de aserción y no de importación. Trazas completas en el scratchpad de la
sesión (`red/t2..t12.txt`).

- **R2, R3, R4** (sv5, `-k clasificar`, 27 failed):
  `E       NotImplementedError` ·
  `FAILED ...::test_f024_r2_clasificar_acierto_por_synckey_es_presente` ·
  `FAILED ...::test_f024_r3_clasificar_respaldo_por_ide_sin_synckey` ·
  `FAILED ...::test_f024_r3_clasificar_ide_reutilizado_es_borrada[otra-synckey]` ·
  `FAILED ...::test_f024_r4_clasificar_cabecera_borrada`.
- **R8 (cliente)** (`-k cliente`, 8 failed):
  `E       AttributeError: 'SigridWriteClient' object has no attribute 'lineas_por_ide'` ·
  `FAILED ...::test_f024_r8_cliente_truncated_es_una_excepcion[lineas_por_ide]`.
- **R1, R8, R9 (endpoint)** (fichero entero, 11 failed / 43 passed):
  `E       TypeError: build_app() got an unexpected keyword argument 'comprobador'` ·
  `FAILED ...::test_f024_r1_endpoint_un_veredicto_por_registro_id` ·
  `FAILED ...::test_f024_r1_endpoint_no_toma_el_lock_de_escritura` ·
  `FAILED ...::test_f024_r8_endpoint_truncated_es_502` ·
  `FAILED ...::test_f024_r9_endpoint_cuerpo_invalido_es_422_sin_leer[501-lineas]`.
  Los 43 verdes eran `clasificar`/cliente ya hechos y los de
  `ComprobadorLineas`, escrito en T2 junto al clasificador (design §5.1):
  sus tests llegaron después del código.
- **R13** (sv4): primero `E   ImportError: cannot import name
  'ESTADO_BORRADO_SIGRID'`. Con la constante, los tests de R13 de sv4 pasan
  porque la regla ya dejaba libre cualquier estado no congelante: R13 era
  cierto por construcción. La evidencia de que el guardián muerde es T6: en
  una copia aislada con `"borrado_sigrid"` añadido a `ESTADOS_CONGELADOS` de
  sv3, `E   AssertionError: sv3` · `{"'borrado_sigrid'": True} !=
  {"'borrado_sigrid'": False}` · `FAILED ...::test_f024_r13_borrado_sigrid_no_congela_en_sv3_ni_en_sv4`
  · `FAILED ...::test_f024_r13_sv3_y_sv4_coinciden_en_todos_los_estados`
  (2 failed, 1 passed).
- **R15, R16** (`-k "congel or vuelo or motivo"`, 3 failed / 7 passed):
  `E       AssertionError: assert 'borrado_sigrid' in (None, '', 'encolado', 'conflicto', 'error')` ·
  `E       AssertionError: assert 'borrado_sigrid' == 'registrado'` ·
  `FAILED ...::test_f024_r15_vuelo_ya_registrada_devuelve_la_linea_a_registrado` ·
  `FAILED ...::test_f024_r16_motivo_explica_la_via_nueva`.
- **R10, R11, R28 (repo)** (`-k repo`, 20 failed):
  `E       AttributeError: 'ParteReviewRepository' object has no attribute 'aplicar_comprobacion_sigrid'` ·
  `FAILED ...::test_f024_r10_repo_borrada_pasa_a_borrado_sigrid_y_conserva_rastro` ·
  `FAILED ...::test_f024_r11_repo_si_cambio_su_hmores_ide_no_se_toca` ·
  `FAILED ...::test_f024_r28_repo_recuento_estados`.
- **R19** (`-k recientes`, 8 failed / 1 passed): `E       NotImplementedError` ·
  `FAILED ...::test_f024_r19_recientes_dentro_del_ttl_no_repite` ·
  `FAILED ...::test_f024_r19_recientes_sella_al_reservar_aunque_el_lote_falle`.
- **R14, R17 (servicio)** (`-k servicio`, 22 failed):
  `E       NotImplementedError` ·
  `E       AttributeError: 'TransferClient' object has no attribute 'comprobar'` ·
  `FAILED ...::test_f024_r14_servicio_lote_fallido_no_aplica_y_para[ok-false]` ·
  `FAILED ...::test_f024_r14_servicio_veredicto_ausente_no_aplica_el_lote`.
- **R22** (`-k payload`, 15 failed / 1 passed):
  `E       TypeError: ParteReviewRepository.lineas_para_registro() got an unexpected keyword argument 'incluir_borradas'` ·
  `E       assert [1, 2, 3, 4, 5, 6, ...] == [3, 5, 6, 7, 8]` ·
  `E       KeyError: 'excluidas'` ·
  `FAILED ...::test_f024_r22_payload_repo_excluye_registrado_y_borrado_sigrid` ·
  `FAILED ...::test_f024_r22_payload_preflight_devuelve_excluidas`.
- **R17, R28 (endpoints)** (`-k endpoint`, 22 failed / 1 passed):
  `E       assert 404 == 503` · `E       assert 404 == 422` ·
  `FAILED ...::test_f024_r17_endpoint_comprobar_aplica_y_responde` ·
  `FAILED ...::test_f024_r28_endpoint_estado_cuenta_sin_escribir`.
- **R18**: `test_f024_r18_endpoint_servir_las_vistas_no_llama_a_sv5` fue el
  único verde en RED de `-k endpoint`, y es correcto: es un requisito
  negativo (el `GET` no llama a sv5) que el código previo ya cumplía. La
  parte activa de R18 es JS (`comprobarVista`): verificación MANUAL (M3).

## Resultado real de las suites (T16)

| Suite | Resultado |
|---|---|
| sv3 `services/partes-persistencia` | 640 passed in 3.51s |
| sv4 `services/partes-front` | 1209 passed, 1 warning in 130.09s |
| sv5 `services/partes-transfer` | 197 passed, 1 warning in 4.63s |
| raíz `tests/` | 419 passed, 1 skipped in 44.94s |

`node --check services/partes-front/static/app.js` → sin errores. Plantillas
parseadas por Jinja2 al servir las vistas en los tests de T12.

## Desviaciones e interpretaciones (justificadas)

1. **R6 · recurso**: se compara solo si el portal envía `recurso_ide`; sin
   él, sv5 resolvió el recurso por DNI (F-023 R37) y no es un cambio manual.
2. **R12**: un `presente` con referencia `None` no borra la guardada (solo
   se actualiza con valores no nulos).
3. **R21 · origen**: valores fuera de `vista-obra`/`vista-trabajador`/`boton`
   se registran como `boton` (el log no repite texto libre del navegador).
4. **R17 · estado HTTP**: `ok: false` responde 502 (con los recuentos de lo
   ya aplicado); el navegador lee el cuerpo igual.
5. **R4 · `parte_existe`** sin `hmoide` enviado: `true` (no se afirma que
   falte una cabecera que no se preguntó).
6. **Vista de persona**: pinta todas las líneas del trabajador, no un
   periodo; `comprobarVista` envía todas sus `registrado` (tope 5000 en JS).
7. Las ramas de la celda Sigrid comparan el estado **normalizado**
   (`trim|lower`), como la congelación.
8. Guardián de F-016 adaptado (ver T1).

## Fuera de alcance (spec §7)

Borrar en Sigrid desde el portal; traer valores cambiados a mano (R6 solo
informa); auditar quién borra; F-021; las 35 de septiembre (R31) se marcan
al abrir la obra tras desplegar (MANUAL).

## Pendientes MANUAL (humano; design §9)

- **M1** (antes de desplegar, PG `partes`, lectura): `SELECT
  sigrid_parte_cod, min(fecha_int), max(fecha_int), count(*) FROM
  parte_registros WHERE sigrid_estado = 'registrado' GROUP BY 1 ORDER BY 1;`
  → esperado: PT26/00314 con 35 (16–28/09) y, si quedan, las de pruebas.
- **M2** (lo pide el humano): `redeploy_partes.ps1 -Solo sv5` y después
  `-Solo sv4`.
- **M3**: abrir la obra 0719 (Ctrl+F5) en el periodo del 16–28/09 → aviso
  «35 línea(s) … ya no están en Sigrid». Log Analytics:
  `ContainerAppConsoleLogs_CL | where ContainerAppName_s == 'ca-sv4-front'
  and Log_s has '[comprobacion-sigrid]'` → `origen=vista-obra …
  borradas=35`; en `ca-sv5-transfer`, `[comprobar]` y ningún
  `[sigrid-write]` en ese intervalo. Recargar antes de 120 s: ninguna línea
  nueva de `[comprobacion-sigrid]` con `comprobadas` > 0.
- **M4** (R31, PG, lectura): `SELECT sigrid_estado, count(*) FROM
  parte_registros WHERE sigrid_parte_cod = 'PT26/00314' GROUP BY 1;` →
  35 `borrado_sigrid`, ninguna `registrado`.
- **M5** (navegador, T13): tras «Actualizar», «Reaprobar» por línea;
  «Comprobar en Sigrid» → modal con 0 borradas nuevas; ficha de un
  trabajador afectado sin consulta nueva (TTL); aprobar una línea de prueba
  (modo pruebas, obra 0404) y ver el sondeo del modal sin recarga
  prematura; «Aprobar todo» con borradas → casilla «Incluirlas».

## Evidencias (medidas, `bash harness/init.sh` final en verde)

| Evidencia | Valor real |
|---|---|
| Tests | sv4 1219 passed (132.8 s) · sv5 203 passed (5.5 s) · raíz 419 passed, 1 skipped (44.3 s) · sv3 640 passed (3.5 s, T16) |
| Tests nuevos F-024 | sv5 62 · sv4 126 (`test_f024_borrado_sigrid` + `test_f024_comprobar_y_estado`) · raíz 3 |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 99.7% de 347 líneas cambiadas cubiertas (346/347, umbral 80%, nivel critico)` |
| Mutación (completa, `--workers 6 --timeout 600`) | 175 generados, 152 muertos, **23 supervivientes**, 0 timeouts, 4130.5 s |
| Supervivientes resueltos | 22 con test nuevo (cada uno comprobado aplicando el mutante a mano: su test FALLA) + 1 **equivalente justificado** (n.º 12, `_respaldo_valido` `return False`→`True`: lleva a `borrada` igual). Detalle en `progress/mutacion_F-024.md` |
| init.sh | `ENTORNO LISTO`; ruff 553 avisos (antes de F-024 eran 542; los ficheros nuevos pasan ruff limpio, el resto es deuda de ficheros existentes tocados) |

**Para el humano (nivel critico)**: aceptar o rebatir la justificación del
mutante equivalente n.º 12. La campaña no se relanzó tras los tests nuevos.
