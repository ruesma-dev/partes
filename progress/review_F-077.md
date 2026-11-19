Revisión completa (pasada 1, principal) · diff `dev...HEAD` (merge-base 9925fa1) sobre HEAD 9effd33b0ec35eea1e1bb303319350cf5c5eea81

# F-077 · Review del reviewer (pasada principal)

- **Veredicto:** CHANGES_REQUESTED: tres arreglos pequeños, ninguno en código de producción
  (ver «Cambios requeridos»).
- **Nivel de rigor:** `critico`, declarado (disparadores 1 y 3). Exige fase RED, cobertura
  ≥ 90 %, mutación con cero supervivientes sin justificar y M0–M6 con comando y resultado.
- **`harness/rigor.local.json`:** el diff no lo toca.

## Verificación ejecutada

- `ARNES_SIN_CACHE=1 bash harness/init.sh`: **ENTORNO LISTO**, exit 0. Raíz 2537 passed / 48
  skipped; sv1 74; sv2 422; sv3 2722 / 2 skipped; sv4 3809 (19 min); sv5 1628. COBERTURA
  99,2 % (263/265); TAMAÑO OK (design 250/250); CARRIL y CAPA E2E N/A.
- **13 mutaciones a mano (RM4/RM7)** en una copia de sv3 en mi scratchpad, con
  `sys.executable -m pytest` y la base en 0. **Mueren las 13**:
  - privacidad: `httpx` en INFO, `{exc}` en el texto de red y `respuesta.url` en el texto HTTP;
  - semántica: sin corte tras un fallo de festivos, 0 empleados aceptado, duplicado ⇒ el
    último, 404 o página vacía a mitad recortan, solo activos, 401 reintentable y 404 de
    festivos ⇒ `None`;
  - orden: el corte después del índice y el DNI vacío después del corte.
  El árbol de trabajo queda limpio.
- Leídos el código de producción de sv3, sv4 e infra, el diff de tests y `azure-apps` a568995.

## Lo que pedía el líder

- **Privacidad: OK.**
  - Los textos del cliente llevan solo el estado o el tipo y la ruta sin query, con `from None`.
  - El adaptador y `RefrescoFestivos` dan solo tipos y recuentos, y sv3 deja `httpx` en WARNING.
  - R18 se prueba con la `configure_logging` REAL sobre `MockTransport`, con un eco de DNI,
    id, email y token.
  - Herramienta: la consola lleva `{exc}`, que viene limpio; el CSV lleva DNI (R32 de F-032,
    en `logs/` ignorado) y su error es solo el tipo.
- **Solo GET: OK, salvo un transporte (cambio 1).** Hay un único `client.get`. El guardián
  AST rechaza los verbos que escriben, los literales de método y `method=`. Los falsos
  `SesameHrFalso` y `Sesame` (del contraste) afirman `GET`.
- **Semántica de F-032: OK.** Lo prueba R15 con el pipeline real:
  - sin empleado ⇒ ni fila ni revisión;
  - fallo con fila ⇒ se conserva; sin fila ⇒ `review_required`;
  - índice caído ⇒ todo el parte a revisión con 3 peticiones;
  - la pasada no llama a Sesame.
  Se cumplen DA6 (404 ⇒ fallo sin corte), DA7 (gana el activo y, a igualdad, el primero) y
  DA8 (todo o nada, más el corte de 60 s sin red).
- **sv4 sin Sesame: OK.** Fuera el cliente y `SESAME_API_*`/`SESAME_CACHE_TTL_S`.
  `sesame_enabled` es `FESTIVOS_SESAME_ENABLED` (False por defecto) y el proveedor se crea
  con `activo=`. Fuera el badge y el aviso, con los mismos KPI. `git grep` no encuentra nada
  muerto cableado. La lista cerrada de `CLAUDE.md` y `servicios.json` son coherentes.
- **Infra: OK.**
  - `sesame-token` = `keyvaultref` + `identityref:$MI_ID`, solo en sv3; sv4 lleva solo el
    interruptor.
  - R28 se valida antes del primer `containerapp`.
  - Las retiradas y `-Quitar` tocan solo lo presente. `00_vars` queda vacía.
  - Los cinco `.ps1` en CRLF y sin BOM.
- **Tests existentes cambiados: OK.** Exactamente la lista cerrada de design §4 más la
  enmienda (una línea en `test_f056_decisiones.py`).

## Checkpoints

- **C1** [x] init.sh sin caché en verde.
- **C2** [x] una sola feature activa, rama correcta y orden de prioridad.
  [ ] `progress/current.md`:
  - la línea 7 dice «Ninguna feature activa»;
  - la sección de F-032 sigue con «sesame-api P0–P4» y «M1–M7» pendientes, que ya sustituye
    F-077 ⇒ cambio 3.
- **C3** [x] Hexagonal (infrastructure → application, sin imports inversos). Primera línea
  con ruta. Sin secretos. Los `print` son de la herramienta de consola. Los ficheros de
  design §6 están intactos.
- **C3 bis / C3 ter** N/A: no entra ningún documento de fuera ni ninguna conversación.
- **C3 quater** [x] `a568995`: solo `partes.md`, en un commit aparte, con su SHA en el informe
  y conforme a design §8. Ya está en `origin/main`; ningún agente registra el push (lo
  confirma el líder).
- **C4**
  - [x] R1–R33 trazables y en verde (tabla abajo). Sin red ni BBDD real.
  - [ ] M0–M6 no están en `current.md`, ni listadas ni enlazadas ⇒ cambio 3.
  - [ ] Dobles: `_ProveedorSinJornada.jornada_contrato`
    (`services/partes-front/tests/test_f077_sin_sesame_sv4.py:165-169`) declara un método que
    `CalendarioProvider` no tiene ⇒ cambio 2. Los demás dobles (`_Repo`, `RepoFestivos` y los
    falsos del contraste) cuadran con sus originales.
- **C4 bis**
  - [x] Fase RED con salida real de los 7 commits rojos.
  - [x] Cobertura 99,2 %.
  - [x] «Evidencias» completa, con la capa e2e N/A.
  - Mutación, RM1–RM6 y supervivientes: **pendiente: pasada de evidencias** (T16).
  - RM7 a mano: los dos órdenes del adaptador mueren con tests de la propia feature. El orden
    R28 del `.ps1` lo vigila `test_f077_r28_valida_antes_del_primer_containerapp`.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T1–T15 y T19 `[x]`, con un commit `F-077 Tn:` por tarea. T16–T18 pendientes,
  como corresponde. Árbol limpio. `features.json` en `in_review`.

## Cobertura requisito → test

| Req. | Test(s) |
|---|---|
| R1–R8 | `test_f077_cliente_hr.py`: `r1_*` a `r8_*` (Bearer, https, paginado estricto, reintentos y Retry-After, 4xx, textos R5, campos de empleados, dayOff/daysOff, 404 ⇒ fallo, calendarios) |
| R9 | `r9_*` del cliente y raíz `test_f077_r9_*` (AST) |
| R10–R14, R19 | `test_f077_festivos_hr.py` `r10_*`–`r14_*`, `r19_*` |
| R15 | `test_f077_ingesta_hr.py` (6 tests, pipeline real) |
| R16–R17 | `test_f077_wiring.py`; adaptados `test_f032_wiring.py` y `test_f003_r10_wiring_sv3.py` |
| R18 | `test_f077_logs_sin_datos.py` |
| R20–R22 | `test_f077_sin_sesame_sv4.py`; raíz `test_f077_r20_*` |
| R23, R31, R33 | raíz `test_f077_sin_pasarela.py` |
| R24–R26 | `test_f077_contraste.py`; adaptados `test_f032_contraste.py` y `test_f032_campana.py` |
| R27–R30 | raíz `test_f077_infra_sesame.py` |
| R32 | por diff (solo docstrings) y `test_f032_festivos_guardados_gemelos` |

## Cambios requeridos

1. **R9.** En `services/partes-persistencia/tests/test_f077_cliente_hr.py:108-110`, el `anota`
   de `test_f077_r1_el_plazo_llega_a_httpx` contesta 200 a cualquier método. Hay que añadir
   `assert request.method == "GET"` o delegar en `SesameHrFalso`.
2. **C4, dobles.** En `services/partes-front/tests/test_f077_sin_sesame_sv4.py:165-169`, hay
   que quitar `jornada_contrato` de `_ProveedorSinJornada`. Con el proveedor real, si la vista
   lo llamara, el `AttributeError` daría 500 y el test caería igual.
3. **C2/C4, `progress/current.md`:**
   - corregir la línea 7;
   - en la sección de F-077, listar M0–M6 o enlazar «Verificaciones manuales pendientes» de
     `progress/impl_F-077.md` (como en F-032);
   - en la de F-032, marcar P0–P4 y M1–M7 como sustituidos por F-077 (sigue P5).

La pasada 2 será incremental desde 9effd33. Con esto y init.sh en verde, se aprueba.

## Observaciones (no bloquean)

- **O1 · Lo decide el humano: es una cuestión de la spec.**
  - Qué pasa: un índice con empleados pero **sin ningún DNI** se acepta vacío. Todos los DNIs
    salen «no encontrado»: ni fila ni revisión, y los partes van al respaldo en silencio.
  - Es R13 literal y lo fija `test_f077_r13_solo_filas_sin_dni_cuentan_como_empleados`.
  - Por qué importa: es el riesgo de DA8 llevado al extremo. Pasaría si el token no ve `nid`
    o si Sesame renombra el campo, y solo lo delataría `sin_dni=N` en el log.
  - Propuesta: una enmienda «0 DNIs ⇒ fallo» (una línea más un test), o dejarlo tal cual,
    cubierto por M1–M2 (`--impacto`).
- **O2.** `features.json` (F-077) nombra la URL pública de la región. No es secreto: DA13
  habla solo de los `.ps1`.
- **O3.** `SesameHrClient.ultimas_paginas` es estado compartido. Con hilos solo puede
  desviar el recuento de páginas del log.

**Automejora (propuesta):** C4 pide comprobar los dobles automáticamente, pero aquí (arnés
1.10.1) nada lo hace; en `arnes-base`, instalar esa comprobación o que C4 diga que es manual.
