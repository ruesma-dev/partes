Revisión de evidencias desde 11d32fc (pasada 3) · diff `11d32fc..6e2f923`

# F-077 · Review del reviewer

- **Veredicto:** APPROVED, **condicionado** a que el humano acepte por escrito los 3
  equivalentes (n.º 2, 4 y 9 de `progress/mutacion_F-077.md`). Sin esa aceptación, T16 no
  se marca y la feature no cierra (C4 bis, `supervivientes_maximos: 0`).
- **Pasada principal (resumen):** pasada 1 (9effd33) CHANGES_REQUESTED con 3 cambios fuera de
  producción; pasada 2 (31da19a, informe en 11d32fc) APPROVED: cambios resueltos, enmienda de
  R13 conforme, 6 + 13 mutaciones a mano (RM4/RM7) muertas, cobertura 99,3 %.
- **Nivel de rigor:** `critico`, declarado: fase RED, cobertura ≥ 90 %, mutación con cero
  supervivientes sin test o justificación aceptada. `rigor.local.json`: no se toca (pasadas 1–3).

## Pasada 3 · qué trae el delta

`611adac` (informe y JSON de la campaña sobre 11d32fc), `dbecb3e` (tests nuevos o reforzados en
3 ficheros de `services/partes-persistencia/tests/`; **ningún fichero de producción**) y
`6e2f923` (análisis y «Pasada de campaña (T16)»). No invalida nada de lo aprobado.

## Pasada 3 · verificación ejecutada

- `ARNES_SIN_CACHE=1 bash harness/init.sh`: **ENTORNO LISTO**, exit 0. Raíz 2537/48 skipped; sv1 74;
  sv2 422; sv3 **2732**/2 skipped; sv4 3809; sv5 1628. COBERTURA 99,6 % (267/268); TAMAÑO, CARRIL y E2E OK/N/A.
- **Recálculo puro** (`harness.alcance.alcance_de_feature` + `generar_mutantes` +
  `reducir_por_linea` con la semilla 20261030, en mi scratchpad): origen rama `9925fa1..rama`,
  **565 líneas, 141 mutantes, 85 candidatos**, tope del nivel `min(300, max(100, ⌈0,6·85⌉)) =
  100` ⇒ campaña completa sin sorteo. Los 85 candidatos que salen **coinciden uno a uno**
  (fichero, línea, operador, texto original → mutado) con los 85 `evaluados` del JSON, y el
  reparto es el del informe: 73 muertos, 12 supervivientes. Los 12 existen como mutantes reales.
- **Sin mutantes (6), control:** `generar_mutantes` sobre el fichero entero da 11–1153 en cada
  uno ⇒ el cero es por diseño; las declaraciones cuadran con el diff.
- **Campaña no reejecutada:** 7791 s según el informe (> 60 s): recálculo puro, RM1–RM7 y
  reproducción de supervivientes.
- **Reproducción en una COPIA** (`git archive HEAD` de sv3 en mi scratchpad,
  `sys.executable -m pytest`, mutante aplicado con `aplicar_mutante` y revertido):

| n.º | Mutante | Con mutante | Sin mutante |
|---|---|---|---|
| 1 | `settings.py:181` `gt=0`→`gt=1` | 1 failed | 1 passed |
| 3 | `festivos_sesame_hr.py:86` `is not None`→veracidad | 1 failed | 1 passed |
| 5 | `sesame_hr_client.py:57` `frozen=False` | 1 failed, 2 passed | 3 passed |
| 8 | `sesame_hr_client.py:90` `20_000`→`20001` | 1 failed | 1 passed |
| 10 | `sesame_hr_client.py:160` `is None`→`not dias` | 1 failed | 1 passed |
| 11 | `sesame_hr_client.py:182` `is None`→`not cuerpo` | 2 failed, 2 passed | 4 passed |
| 12 | `sesame_hr_client.py:262` `1 + intento`→`1 - intento` | 2 failed | 2 passed |
| 2 | `festivos_sesame_hr.py:75` (equivalente) | 39 passed | 39 passed |
| 4 | `festivos_sesame_hr.py:115` (equivalente) | 39 passed | 39 passed |
| 9 | `sesame_hr_client.py:107` (equivalente) | 129 passed | 129 passed |

  Siete muertes reproducidas (6 y 7 comparten test con el 5). Árbol limpio (`git status`).

## Los 9 tests nuevos fijan requisitos, no mutantes

- n.º 1: design §5.3 (`SESAME_TIMEOUT_S`, `gt=0`): un plazo de 0,5 s es válido.
- n.º 3: R14 con el reloj de design §5.2 (`time.monotonic`, origen indefinido). El caso
  (corte que acaba justo en 0.0) es raro pero posible, y el mutante saltaría el corte.
- n.º 5–7: design §5.1 declara las tres dataclasses `frozen=True` (índice de R11 compartido).
- n.º 8: design §5.1 (`tope_filas: int = 20_000`) y R2: nadie fijaba el valor por defecto.
- n.º 10: **R8 y la referencia, no una decisión nueva.** R8: «los días de `daysOff` (o
  `dayOff`)»; design §2: la spec sigue el código de `sesame-api`, y ese código
  (`sesame_http_client.py:169-171`) toma `daysOff` y `dayOff` solo `if dias is None` (el real es
  el plural). Solo el script exploratorio `explora_sesame.py:252` usa `or`. No hace falta
  decisión del humano.
- n.º 11: R5 (el texto da el estado real) y DA6: un 200 con `[]` o `""` no dice «HTTP 404».
- n.º 12: la fórmula `1 + intento` de R3. Que un `Retry-After` negativo o NaN no es espera
  válida ya estaba en el código y en un test del intento 0 aprobados en la pasada 2. El test
  nuevo solo lo extiende al segundo intento.

## Equivalentes: lo son (RM3, RM5)

- **n.º 2 y 4** (`x is None` → `not x`): `indice` solo guarda lo que devuelve
  `SesameHrClient.empleados()` (el puerto tipado de `FestivosSesameHr`), que construye siempre
  `EmpleadoSesame`. **Demostración ejecutada (RM5, muestra n.º 2):** `EmpleadoSesame` no tiene
  `__bool__` ni `__len__`, y `bool(...)` es `True` incluso con `id=''`, `dni_norm=''` y
  `activo=False`. Matarlos exigiría un doble que devuelva objetos falsos fuera del contrato:
  sería un test hecho solo para el mutante.
- **n.º 9** (`ultimas_paginas = 0` → `1`): su único lector es el log del índice
  (`festivos_sesame_hr.py:124`), tras un `empleados()` que volvió bien; `_paginado` asigna
  `pagina` (≥ 1) antes de todo `return` (`sesame_hr_client.py:203-205`), también con hilos.
  Design §5.1 no lo declara contrato: el valor inicial nunca se observa.
- **RM3:** revisé los 73 muertos del JSON uno a uno: ninguno es equivalente en su contexto.

## Checkpoints (tras la pasada 3)

- **C1** [x] init.sh sin caché en verde (pasada 3).
- **C2** [x] una feature activa, rama correcta; `current.md` al día con el estado de T16.
- **C3** [x] El delta no toca producción; los tests nuevos usan IDs y DNIs ficticios.
- **C3 bis / C3 ter** N/A: no entra ningún documento de fuera ni conversación.
- **C3 quater** [x] `a568995` en `azure-apps` (pasada 1); la campaña no cambia la frontera.
- **C4** [x] R1–R33 trazables y en verde (tabla abajo); dobles conformes (pasadas 1–2).
- **C4 bis**
  - [x] Fase RED con salida real (pasadas 1–2) y cobertura ≥ 90 % (ver init).
  - [x] Mutación: informe generado por la herramienta y fiable (`fiable: true`, línea base
    medida, 0 sin veredicto). Regla del nivel, semilla y totales verificados de forma
    independiente.
  - [x] RM1: midió `11d32fc…`. El delta posterior no toca ficheros del alcance ⇒ vale.
  - [x] RM2: base sv3 51–53 s, sv4 839–848 s; media 91,7 s; 85 × 91,7 ≈ 7791 s. Coherente.
  - [x] RM3, RM4 y RM5: ver arriba.
  - [x] RM6: N/A justificado. No se quitó código defensivo: el delta no toca producción.
  - [x] RM7: pasadas 1 (adaptador y R28) y 2 (enmienda); el delta no añade órdenes.
  - [x] Supervivientes: ninguno en `PENDIENTE`; 9 con test y 3 equivalentes justificados.
    **Falta la aceptación literal del humano** de los 3: condición del APPROVED.
  - [x] Capa e2e: N/A (`CAPA E2E: N/A`, ningún servicio declara el bloque).
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T1–T15 y T19 `[x]`. T16 queda `[ ]` hasta la aceptación, como dice el impl;
  T17–T18 son manuales del humano. Commits `F-077 T16:` en el delta.

## Cobertura requisito → test

| Req. | Test(s) |
|---|---|
| R1–R8 | `test_f077_cliente_hr.py` `r1_*`–`r8_*`; T16 añade `r2_el_tope_por_defecto_*`, `r3_retry_after_negativo_o_nan_*`, `r8_days_off_presente_manda_*` y el refuerzo de `r2_un_cuerpo_sin_forma_*` |
| R9 | `r9_*` del cliente, raíz `test_f077_r9_*` (AST), `assert GET` de R1 |
| R10–R14, R19 | `test_f077_festivos_hr.py` `r10_*`–`r14_*`, `r19_*`; T16: `r14_el_corte_no_depende_del_origen_*` |
| R15 | `test_f077_ingesta_hr.py` (pipeline real) |
| R16–R17 | `test_f077_wiring.py` (T16 refuerza `r16_timeout_*`), `test_f032_wiring.py`, `test_f003_r10_wiring_sv3.py` |
| R18; R20–R22 | `test_f077_logs_sin_datos.py`; `test_f077_sin_sesame_sv4.py`, raíz `test_f077_r20_*` |
| R23, R31, R33 | raíz `test_f077_sin_pasarela.py` |
| R24–R26; R27–R30 | `test_f077_contraste.py`, `test_f032_contraste.py`, `test_f032_campana.py`; raíz `test_f077_infra_sesame.py` |
| R32 | por diff (docstrings) y `test_f032_festivos_guardados_gemelos` |
| Design §5.1 | `test_f077_los_datos_del_cliente_son_inmutables_y_hashables` (T16) |

## Cambios requeridos

Ninguno. **Condición para cerrar:** la aceptación literal del humano de los equivalentes
n.º 2, 4 y 9. Después se marca T16 `[x]`.

## Observaciones (no bloquean)

- **O2, O3 y O4 (siguen):** URL pública en `features.json` (no es secreto); `ultimas_paginas` compartido entre hilos (solo el log); el
  `__getattr__` de `_ProveedorSinJornada` hace reventar también a `hasattr` (pasada 2).
- **O5 (nueva).** El implementer reprodujo las muertes **en el árbol** con revertido en
  `finally`. Salió bien, pero RM4 pide copia: si el proceso muere, el mutante se queda.
- **O6 (nueva).** Con el n.º 10, un `daysOff: []` junto a un `dayOff` da calendario vacío, como
  en la referencia. El contraste M1 lo destaparía.


**Automejora (propuesta, de la pasada 1):** C4 pide comprobar los dobles automáticamente, pero
en el arnés 1.10.1 nada lo hace. En `arnes-base`: instalar esa comprobación o que C4 diga que
es manual.
