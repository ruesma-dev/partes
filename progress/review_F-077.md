Revisión completa (pasada 1, principal) · diff `dev...HEAD` (merge-base 9925fa1) sobre HEAD 9effd33b0ec35eea1e1bb303319350cf5c5eea81

# F-077 · Review del reviewer (pasada principal)

- **Veredicto:** CHANGES_REQUESTED (tres arreglos pequeños, sin cambio de código de producción; ver al final).
- **Nivel de rigor:** `critico`, declarado en `features.json` (disparadores 1 y 3 citados en
  design). Exige fase RED, cobertura ≥ 90 % de lo cambiado, campaña de mutación exigida con
  cero supervivientes sin justificar, y M0–M6 manuales con comando y resultado real.
- **`harness/rigor.local.json`:** no lo toca el diff (sin aviso `CAPA LOCAL DE RIGOR`).

## Verificación ejecutada

- `ARNES_SIN_CACHE=1 bash harness/init.sh`: **ENTORNO LISTO**, exit 0. Raíz 2537 passed / 48
  skipped; sv1 74; sv2 422; sv3 2722 passed / 2 skipped; sv4 3809 passed (19 min); sv5 1628.
  PUERTA COBERTURA 99,2 % (263/265); PUERTA TAMAÑO OK (design 250/250); CARRIL y CAPA E2E N/A.
- **Mutaciones a mano (RM4/RM7), en una copia de sv3 en mi scratchpad**, no en el árbol de
  trabajo, con el mismo intérprete (`sys.executable -m pytest`). La base sin mutar sale con 0.
  Las **13 mueren**:
  - privacidad: `httpx` en INFO, el mensaje de red con `{exc}` y el mensaje HTTP con
    `respuesta.url` los caza `test_f077_logs_sin_datos`;
  - semántica: sin corte tras `SesameNoDisponible` de festivos, 0 empleados aceptado,
    el duplicado se queda con el último, 404 a mitad recorta, página vacía antes de la última
    aceptada, solo activos, 401 reintentable y 404 de festivos ⇒ `None`;
  - orden: el corte comprobado después del índice, y el DNI vacío comprobado después del corte.
  `git status` queda limpio.
- Lectura del código de producción de sv3, sv4 e infra, del diff entero de tests y del
  commit `a568995` de `azure-apps`.

## Lo que pedía el líder

- **Privacidad.** El cliente solo usa en sus textos el estado o el tipo del error y la ruta
  sin query, siempre con `from None`. El adaptador da en sus textos el tipo y registra solo
  recuentos. `RefrescoFestivos` registra `type(exc).__name__`. sv3 deja `httpx` en WARNING.
  R18 se prueba con la `configure_logging` REAL, el cliente y el adaptador reales sobre
  `MockTransport` y un cuerpo de error que repite DNI, id, email y token. La herramienta de
  contraste saca por consola `{exc}`, que es un texto de cliente limpio; el CSV lleva DNI (R32
  de F-032, en `logs/`, ignorado por git) y su columna de error lleva solo el tipo. **OK.**
- **Solo GET.** Hay un único `client.get` por `httpx.Client` y ningún otro verbo. El guardián
  AST (`test_f077_r9_*`) rechaza `post/put/patch/delete/request/send/stream`, los literales de
  método y `method=`. Los dos falsos (`SesameHrFalso` y el `Sesame` de `test_f032_contraste`)
  hacen `assert request.method == "GET"`. **Salvo un transporte: cambio 1.**
- **Semántica de F-032 (R15, integración con el pipeline real).** Sin empleado ⇒ ni fila ni
  revisión. Fallo con fila ⇒ se conserva. Fallo sin fila ⇒ `review_required`. El índice
  caído manda el parte entero a revisión con 3 peticiones. La pasada no llama a Sesame. Se
  cumplen DA6 (404 de festivos ⇒ `RuntimeError` sin corte), DA7 (activos e inactivos, gana
  el activo y, a igualdad, el primero) y DA8 (todo o nada, `_indice = None` y corte de 60 s
  sin red). **OK.**
- **sv4 sin Sesame.** No queda `infrastructure/sesame/` ni `SESAME_API_*`/`SESAME_CACHE_TTL_S`.
  `sesame_enabled` es `festivos_sesame_enabled` (False por defecto) y
  `CalendarioProvider(activo=…)` va sin caché de jornada. Fuera el badge y el aviso, con los
  KPI fotografiados iguales. `git grep` no encuentra nada muerto cableado. La lista cerrada de
  `CLAUDE.md` es coherente: el cliente de Sesame deja de ser gemelo y sigue
  `festivos_guardados.py`. `servicios.json` sin la dependencia. **OK.**
- **Infra.** `sesame-token` es `keyvaultref` + `identityref:$MI_ID`, solo en sv3; sv4 lleva
  solo `FESTIVOS_SESAME_ENABLED=true`. La validación R28 (`^https://` y `secret show --query
  id`) va antes del primer `containerapp`. Las retiradas solo salen si están, y lo mismo
  `-Quitar`. `00_vars` vacía (DA13). Los cinco `.ps1` en CRLF y sin BOM. **OK.**
- **Tests existentes cambiados.** Coinciden exactamente con la lista cerrada de design §4
  más la enmienda: en `test_f056_decisiones.py`, solo la línea del doble. **OK.**

## Checkpoints

- **C1** [x] init.sh sin caché en verde; ficheros base presentes.
- **C2** [x] una sola feature activa (F-077 `in_review`); rama correcta; orden de prioridad.
  [ ] `progress/current.md`: la línea 7 dice «Ninguna feature activa» y F-077 está en
  `in_review`; además, su sección de F-032 sigue listando como pendientes «sesame-api P0–P4»
  y «M1–M7», que F-077 sustituye (ya lo dice `features.json`) ⇒ cambio 3.
- **C3** [x] Hexagonal: infrastructure → application (`normalize_dni`), sin imports
  inversos. Primera línea con ruta en los ficheros nuevos. Sin secretos. Los `print` son de
  la herramienta de consola. Ficheros de design §6 intactos.
- **C3 bis / C3 ter** N/A: no entra ningún documento de fuera ni se registra ninguna
  conversación.
- **C3 quater** [x] `a568995` toca solo `partes.md`, va aparte y su SHA consta en
  `impl_F-077.md`; el contenido coincide con design §8. Ese commit ya está en `origin/main`
  de `azure-apps`: el push no lo registra ningún agente, así que se entiende hecho por el
  humano (el líder lo confirmará).
- **C4** [x] Cada R1–R33 tiene su test `test_f077_rN_*` y todos pasan (tabla abajo).
  [x] Sin red ni BBDD real (`MockTransport` y SQLite de `tests/dobles`).
  [ ] Las verificaciones MANUAL M0–M6 no están en `progress/current.md`, ni listadas ni
  enlazadas; solo viven en `impl_F-077.md` ⇒ cambio 3.
  [ ] Dobles contra el original: `_ProveedorSinJornada.jornada_contrato`
  (`services/partes-front/tests/test_f077_sin_sesame_sv4.py:165-169`) declara un método que
  `CalendarioProvider` ya no tiene ⇒ cambio 2. Los demás cuadran: `_Repo` y `RepoFestivos`
  frente a `SqlAlchemyFestivosRepository`, y los falsos del contraste frente a
  `SesameHrClient.calendarios_festivos` y `FestivosSesameHr.festivos`.
- **C4 bis**
  - [x] `rigor` declarado.
  - [x] Fase RED con salida real de los siete commits rojos (T1, T2, T4, T6, T8, T10, T12).
  - [x] Cobertura 99,2 % ≥ 90 %.
  - [x] Sección «Evidencias» completa, con la fila «Capa e2e» N/A (ningún servicio la declara).
  - Mutación, RM1–RM7 aplicados a la campaña, supervivientes y muertos comprobados:
    **pendiente: pasada de evidencias** (T16 la lanza el líder tras este veredicto).
  - RM7 a mano ya hecho sobre los órdenes del adaptador: los dos mueren con tests de la
    propia feature. El orden de R28 del `.ps1` lo vigila
    `test_f077_r28_valida_antes_del_primer_containerapp`.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T1–T15 y T19 `[x]`, con commit `F-077 Tn:` por tarea. T16–T18 sin marcar, como
  corresponde (mutación del líder y manuales del humano). Árbol limpio. `features.json`
  dice `in_review`.

## Cobertura requisito → test

| Req. | Test(s) |
|---|---|
| R1–R4 | `test_f077_cliente_hr.py`: `r1_*` (Bearer, https, token, plazo), `r2_*` (paginado, 404 o vacía a mitad, tope), `r3_*` (429/5xx, Retry-After numérico, fecha, tope 30 s, red), `r4_*` |
| R5 | `test_f077_r5_los_mensajes_no_llevan_cuerpo_query_url_ni_token` |
| R6–R8 | `r6_*` (estados, campos descartados, `normalize_dni`), `r7_*` (dayOff/daysOff, 404 ⇒ fallo), `r8_*` |
| R9 | `r9_solo_tres_metodos_publicos`, `r9_el_falso_rechaza_otros_metodos`; raíz `test_f077_r9_*` (AST) |
| R10–R14, R19 | `test_f077_festivos_hr.py`: `r10_*`, `r11_*` (TTL), `r12_*`, `r13_*`, `r14_*` (corte), `r19_*` |
| R15 | `test_f077_ingesta_hr.py` (6, pipeline real) |
| R16–R17 | `test_f077_wiring.py`; adaptados `test_f032_wiring.py` y `test_f003_r10_wiring_sv3.py` |
| R18 | `test_f077_logs_sin_datos.py` (7 escenarios, excepciones, índice caído, httpx) |
| R20–R22 | `test_f077_sin_sesame_sv4.py`; raíz `test_f077_r20_*` |
| R23, R31, R33 | raíz `test_f077_sin_pasarela.py` |
| R24–R26 | `test_f077_contraste.py`; adaptados `test_f032_contraste.py` y `test_f032_campana.py` |
| R27–R30 | raíz `test_f077_infra_sesame.py` |
| R32 | por diff: `festivos_guardados`, `recurso_conciliador`, `jornada_resolver` y la tabla no cambian; `RefrescoFestivos` y `TablaCalendarioLaboral`, solo docstring; `test_f032_festivos_guardados_gemelos` en verde |

## Cambios requeridos

1. **R9 (todos los `MockTransport` rechazan otro método).**
   `services/partes-persistencia/tests/test_f077_cliente_hr.py:108-110`: el `anota` de
   `test_f077_r1_el_plazo_llega_a_httpx` contesta 200 a cualquier método. Añadir
   `assert request.method == "GET"`, o delegar en `SesameHrFalso`, como hacen los
   demás.
2. **C4, dobles contra el original.**
   `services/partes-front/tests/test_f077_sin_sesame_sv4.py:165-169`: quitar el método
   `jornada_contrato` de `_ProveedorSinJornada`, porque el `CalendarioProvider` real ya no lo
   tiene. Usar el proveedor real: si la vista lo llamara, el `AttributeError` daría 500 y el
   test caería igual.
3. **C2/C4, `progress/current.md`.**
   - Corregir la línea 7: F-077 está en `in_review`.
   - En la sección de F-077, listar M0–M6 con su comando o, como se aceptó en F-032, enlazar
     `progress/impl_F-077.md` («Verificaciones manuales pendientes»).
   - En la sección de F-032, marcar como sustituidos por F-077 los P0–P4 de sesame-api y los
     M1–M7. Sigue pendiente P5.

La pasada 2 será incremental desde 9effd33. Con estos tres cambios y init.sh en verde,
aprobaría sin más.

## Observaciones (no bloquean)

- **O1 · Para el humano, decisión de spec.** Un índice con empleados pero **sin ningún DNI**
  se acepta, aunque quede vacío, y todos los DNIs salen «no encontrado»: ni fila ni revisión,
  y los partes se calculan con el respaldo. Lo dice R13 al pie de la letra («0 empleados»)
  y lo fija `test_f077_r13_solo_filas_sin_dni_cuentan_como_empleados`. Pero es el mismo
  riesgo que DA8 quería evitar, llevado al extremo: si el token no ve `nid` o Sesame renombra
  el campo, el respaldo entra en silencio; solo lo delataría `sin_dni=N` en el log. Propongo
  que el humano decida si «índice con 0 DNIs ⇒ fallo» entra como enmienda (una línea en el
  adaptador más el test) o si se queda tal cual, cubierto por M1–M2 (`--impacto`).
- **O2.** El texto de `features.json` (F-077) nombra la URL pública de la región. No es
  secreto y DA13 se refiere solo a los `.ps1`; lo anoto porque `README_partes.md` la deja en
  plantilla a propósito.
- **O3.** `SesameHrClient.ultimas_paginas` es estado compartido y solo alimenta el recuento
  del log del índice. Con hilos en paralelo puede dar un número de páginas inexacto, sin más
  efecto.

## Automejora (propuesta, no aplicada)

C4 pide comprobar los dobles de forma automática, pero en este repositorio (arnés 1.10.1) no
hay ninguna comprobación así en `init.sh` ni en `tests/`. El doble del cambio 2 solo se ha
visto a mano. Propuesta para `arnes-base`: o se instala esa comprobación, o el texto de C4
declara que hoy es manual.
