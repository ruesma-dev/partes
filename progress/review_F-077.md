Revisión incremental desde 9effd33 (pasada 2, principal) · diff `9effd33..HEAD` sobre HEAD 31da19a

# F-077 · Review del reviewer (pasada principal)

- **Veredicto:** APPROVED (pasada principal). No da por hecha la mutación: T16 y la pasada de
  evidencias siguen pendientes.
- **Pasada 1 (9effd33):** CHANGES_REQUESTED con tres cambios pequeños fuera de producción (R9
  en un `MockTransport`, un doble con un método inexistente y `current.md`) y O1–O3. Resumen
  abajo.
- **Nivel de rigor:** `critico`, declarado (disparadores 1 y 3). Exige fase RED, cobertura
  ≥ 90 %, mutación con cero supervivientes sin justificar y M0–M6 con comando y resultado.
- **`harness/rigor.local.json`:** el diff no lo toca (ni en la pasada 1 ni en la 2).

## Pasada 2 · verificación ejecutada

- `ARNES_SIN_CACHE=1 bash harness/init.sh` (sin pipes; salida a un log de mi scratchpad):
  **ENTORNO LISTO**, exit 0. Raíz 2537 passed / 48 skipped (80 min); sv1 74; sv2 422; sv3 2722
  / 2 skipped; sv4 3809 (22 min); sv5 1628. COBERTURA 99,3 % (266/268); TAMAÑO OK (design
  250/250, impl 220/220); CARRIL y CAPA E2E N/A. No repetí la variante con caché: esta la
  incluye y tarda más de hora y media. Este informe tiene 131/140 líneas.
- **6 mutaciones a mano (RM4)** en una copia de sv3 y sv4 en mi scratchpad, con
  `sys.executable -m pytest -x` y la base en 0 (sv3 32 passed, sv4 13 passed). **Mueren las 6**:
  - enmienda de R13: quitarla; no abrir el corte con 0 DNIs; guardar el índice antes de fallar;
    fallar antes del log de recuentos;
  - R22 (sv4): la vista de trabajador vuelve a llamar a `jornada_contrato(detail.dni)`, o lo
    sondea con `getattr(..., None)`.
  El árbol de trabajo queda limpio (`git status` vacío).

## Pasada 2 · lo que pedía el líder

- **Cambio 1 (a370158): resuelto.** `anota` hace `assert request.method == "GET"` antes de
  contestar 200 (`test_f077_cliente_hr.py:109`).
- **Cambio 2 (ce697ec): resuelto.** `_ProveedorSinJornada` ya no declara nada que
  `CalendarioProvider` no tenga. El `__getattr__` es **aceptable**:
  - solo salta cuando falla la búsqueda normal, así que los métodos reales no cambian;
  - no es más débil: con `jornada_contrato` da lo mismo que el doble anterior (la mutación
    muere) y además caza cualquier otro atributo retirado;
  - no es más frágil hoy: producción no hace `hasattr`/`getattr` sobre el proveedor (`git grep`
    en sv4) y los 13 tests pasan con él. Ver O4.
- **Cambio 3 (5e6ffb1): resuelto.** La línea 7 de `current.md` nombra F-077 activa, M0–M6
  quedan enlazadas a «Verificaciones manuales pendientes» de `progress/impl_F-077.md` y P0–P4 y
  M1–M7 de F-032 constan como sustituidos (sigue P5).
- **Enmienda de R13 (41bdaed spec, 2e33a1f código): conforme.**
  - Spec: R13, design §5.2 y T5 dicen lo mismo, con fecha y origen (O1, opción «a» del humano).
  - Código: `_indice_vigente` de `festivos_sesame_hr.py:126-129`, tras el log de recuentos y
    antes de guardar. Índice vacío ⇒ corte y `SesameNoDisponible("sesame indice sin DNIs")`. El
    texto no lleva datos (R18). Va dentro del `threading.Lock`, como el resto del índice.
  - Test: `test_f077_r13_solo_filas_sin_dni_cuentan_como_empleados`, reescrito. Cubre las filas
    con `None` y con `""`, el error distinto de «corte», el índice sin guardar, el log de
    recuentos exacto, el corte a los 59,9 s sin red y que no se piden festivos.
  - RED real en el informe (`DID NOT RAISE SesameNoDisponible`, 1 failed) con el test reescrito
    y el código sin tocar.
  - Alcance: solo el adaptador y su test, sin ficheros fuera de la lista cerrada de design §4 ni
    gemelos. `contrastar_festivos_sesame.py --impacto` recoge el fallo por DNI (fila de error,
    R32) y ya no lo confunde con «no encontrado», que es lo que buscaba O1.
- **Regresiones:** ninguna. Lo confirman las suites enteras de init.sh y que ningún otro test
  fijaba el índice vacío.

## Checkpoints (estado tras la pasada 2)

- **C1** [x] init.sh sin caché en verde (pasada 2).
- **C2** [x] una sola feature activa, rama correcta y `current.md` al día (cambio 3).
- **C3** [x] Hexagonal, primera línea con ruta, sin secretos ni `print` de debug. El delta
  toca un fichero de producción y lo deja en su capa.
- **C3 bis / C3 ter** N/A: no entra ningún documento de fuera ni ninguna conversación.
- **C3 quater** [x] `a568995` en `azure-apps` (pasada 1). La enmienda no cambia lo que se
  expone ni lo que se consume: `partes.md` no necesita tocarse.
- **C4**
  - [x] R1–R33 trazables y en verde (tabla abajo). Sin red ni BBDD real.
  - [x] M0–M6 enlazadas desde `current.md`.
  - [x] Dobles: `_ProveedorSinJornada` hereda del real y no añade métodos. `SesameHrFalso`,
    `_Repo`, `RepoFestivos` y los falsos del contraste cuadran con sus originales (pasada 1).
- **C4 bis**
  - [x] Fase RED con salida real: los 7 commits rojos (pasada 1) y la enmienda (ciclo 1).
  - [x] Cobertura 99,3 % (266/268), umbral 90 %.
  - [x] «Evidencias» completa, con la capa e2e N/A.
  - Mutación, RM1–RM6 y supervivientes: **pendiente: pasada de evidencias** (T16). El informe
    tiene que medir HEAD 31da19a o posterior (RM1): la enmienda añade un `if` al alcance.
  - RM7 a mano (pasada 1): los dos órdenes del adaptador mueren con tests de la propia feature.
    El orden R28 del `.ps1` lo vigila `test_f077_r28_valida_antes_del_primer_containerapp`. La
    enmienda añade un orden (log, después corte) y también muere.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T1–T15 y T19 `[x]`, con un commit `F-077 Tn:` por tarea, y la enmienda de T5
  anotada. T16–T18 pendientes, como corresponde. Árbol limpio. `features.json` en `in_review`.

## Cobertura requisito → test

| Req. | Test(s) |
|---|---|
| R1–R8 | `test_f077_cliente_hr.py`: `r1_*` a `r8_*` (Bearer, https, paginado estricto, reintentos y Retry-After, 4xx, textos R5, campos de empleados, dayOff/daysOff, 404 ⇒ fallo, calendarios) |
| R9 | `r9_*` del cliente, raíz `test_f077_r9_*` (AST) y el `assert GET` de `r1_el_plazo_llega_a_httpx` |
| R10–R14, R19 | `test_f077_festivos_hr.py` `r10_*`–`r14_*` y `r19_*`; la enmienda, en `r13_solo_filas_sin_dni_*` |
| R15 | `test_f077_ingesta_hr.py` (6 tests, pipeline real) |
| R16–R17 | `test_f077_wiring.py`; adaptados `test_f032_wiring.py` y `test_f003_r10_wiring_sv3.py` |
| R18 | `test_f077_logs_sin_datos.py` |
| R20–R22 | `test_f077_sin_sesame_sv4.py`; raíz `test_f077_r20_*` |
| R23, R31, R33 | raíz `test_f077_sin_pasarela.py` |
| R24–R26 | `test_f077_contraste.py`; adaptados `test_f032_contraste.py` y `test_f032_campana.py` |
| R27–R30 | raíz `test_f077_infra_sesame.py` |
| R32 | por diff (solo docstrings) y `test_f032_festivos_guardados_gemelos` |

## Pasada 1 (9effd33) · resumen

- init.sh sin caché en verde: raíz 2537 / 48 skipped, sv3 2722, sv4 3809, sv5 1628, cobertura
  99,2 %. 13 mutaciones a mano (privacidad, semántica y orden): mueren las 13.
- Lo que pedía el líder: privacidad, solo GET (salvo un transporte), semántica de F-032
  (R15, DA6–DA8), sv4 sin Sesame, infra (`keyvaultref`, R28 antes del primer `containerapp`,
  CRLF sin BOM) y tests existentes cambiados. Todo OK.
- Cambios requeridos, ya resueltos: (1) el `assert GET` en el `MockTransport` de R1; (2) quitar
  `jornada_contrato` del doble de R22; (3) `current.md`: línea 7, M0–M6 y P0–P4/M1–M7 de F-032.

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean)

- **O1 · cerrada.** La resolvió la enmienda de R13 (decisión del humano «a», 2026-11-19).
- **O2.** `features.json` (F-077) nombra la URL pública de la región. No es secreto: DA13
  habla solo de los `.ps1`.
- **O3.** `SesameHrClient.ultimas_paginas` es estado compartido. Con hilos solo puede
  desviar el recuento de páginas del log.
- **O4 (nueva).** El `__getattr__` de `_ProveedorSinJornada` lanza `AssertionError`, no
  `AttributeError`, así que `hasattr` y `getattr(..., default)` sobre el proveedor también
  revientan (lo comprobé con una mutación). Hoy es lo que se quiere: sondear la jornada
  retirada también es pedirla. Si mañana el portal sondea el proveedor por otro motivo
  legítimo, este test caerá con «la vista pide 'x' al proveedor» y habrá que decidir.

**Automejora (propuesta, de la pasada 1):** C4 pide comprobar los dobles automáticamente, pero
aquí (arnés 1.10.1) nada lo hace; en `arnes-base`, instalar esa comprobación o que C4 diga que
es manual.
