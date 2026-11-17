Revisión completa (pasada 1, principal) desde el merge-base `95982ac` con `dev` hasta HEAD `85b4c02`

# F-032 · Review del reviewer: activar Sesame en producción (festivos por trabajador)

- **Veredicto: CHANGES_REQUESTED.** Hay un solo motivo bloqueante: R3 no se cumple en producción
  (cambio 1). El resto del trabajo está bien y no hay que rehacerlo.
- **Rigor:** `critico`, declarado en `features.json` (DA10 = B). Exige fase RED, cobertura ≥ 90 %
  de las líneas cambiadas, mutación exigida (uno por línea, 60 % en [100, 300], semilla
  20261030) con cero supervivientes sin aceptar, y RM1–RM7.
- **T27 (campaña):** no se ha lanzado, a propósito: va después del APPROVED. Sus puntos quedan
  como «pendiente: pasada de evidencias».

## Ejecución

`ARNES_SIN_CACHE=1 bash harness/init.sh` ⇒ `ENTORNO LISTO`, exit 0.
- Suites: raíz 2517 passed / 48 skipped; sv1 74; sv2 422; sv3 2568 / 2 skipped; sv4 3885; sv5 1628.
- Puertas: `COBERTURA` 95.4 % (585/613, umbral 90 %); `TAMAÑO` OK; `CAPA E2E` N/A (ningún
  servicio declara el bloque e2e).
- Avisos: F-032 sin `spec_aprobada` (cambio 3) y la deuda previa de ruff.
- El diff no toca `harness/rigor.local.json`.

## Cambios requeridos

1. **R3 (bloqueante): DNIs en claro en los logs de sv3, en cada ingesta.**
   - **Qué pasa.** `RefrescoFestivos` llama a `SesameApiClient.festivos`, que hace
     `GET /api/v1/festivos?dni=…&ano=…`. La raíz de sv3 queda en INFO (`config/logging_config.py`;
     `LOG_LEVEL` por defecto `INFO`), y httpx 0.28.1 escribe la URL completa en INFO.
   - **Reproducido** con la propia `configure_logging(…, "INFO")` de sv3, el cliente real sobre
     `MockTransport` y `RefrescoFestivos.refrescar(['12345678Z'], {2026})`:
     ```
     INFO | httpx | _client.py:1025 | HTTP Request: GET http://sesame.local/api/v1/festivos?dni=12345678Z&ano=2026 "HTTP/1.1 200 OK"
     ```
   - **Por qué no lo caza la suite.** `test_f032_refresco.py::test_f032_r3_logs_sin_dnis_y_con_el_recuento`
     usa un cliente falso, así que no lo ve. Es justo el disparador 3 (datos personales) que
     hace `critico` a la feature. sv5 ya silencia httpx (`partes-transfer/config/logging_config.py:28`),
     igual que `validar_datos_sesame.py:529`.
   - **Qué hacer.** Fijar `logging.getLogger("httpx").setLevel(logging.WARNING)` en
     `services/partes-persistencia/config/logging_config.py`, y añadir un test: el refresco con el
     cliente REAL (`MockTransport`) y el logging de sv3 en INFO, sin el DNI en ningún registro.
   - **Alcance.** `logging_config.py` no está en design §4: el líder lo lleva al humano como
     enmienda de alcance. `sesame_api_client.py` está en §6 y no se toca.
2. **R3 en sv4: el mismo defecto, que F-032 enciende por primera vez.** Con DA18 = A,
   `add_sesame_partes.ps1` da `SESAME_API_*` a sv4, que empieza a llamar a `/api/v1/jornada?dni=…`.
   Se filtra por dos sitios:
   - la línea de httpx en INFO, porque el logging de sv4 no la silencia;
   - el WARNING de `CalendarioProvider.jornada_contrato` (`application/services/calendario_provider.py`,
     `"%s jornada de %s no disponible (%r)…"`), que lleva `dni_norm` y el `exc!r` con la URL.

   El código es de F-003, pero F-032 modifica este fichero y lo activa en producción. Hay que
   quitar el DNI y el `exc!r` del WARNING (dejar solo `type(exc).__name__`, como el refresco) y
   silenciar httpx en `services/partes-front/config/logging_config.py`, con su test. Va en la
   misma enmienda de alcance.
3. **Papeleo** (no bloquea por sí solo):
   - `progress/current.md` dice «T28–T30 son manuales del humano», pero no da los comandos que pide
     C4. Basta con enlazar a design §7 y a la sección «Verificaciones manuales pendientes» de
     `progress/impl_F-032.md`.
   - Falta `spec_aprobada: "2026-11-17"` en la entrada de F-032 de `features.json`. Lo anota el líder.

## Checkpoints

- **C1** [x] `init.sh` sin caché, en verde; [x] ficheros base. **C2** [x] una sola feature activa; [x] rama correcta; [x] orden de prioridad;
  [x] `current.md`; [x] N/A `history.md`, porque F-032 no está `done`.
- **C3**
  - [x] Arquitectura hexagonal: `festivos_guardados.py` puro; repositorio y calendario en
    `infrastructure/`; el refresco en `application/`, por duck-typing.
  - [x] Primera línea con la ruta en los 25 ficheros nuevos.
  - [x] Sin prints de debug: los `print` de `contrastar_festivos_sesame.py` son salida de
    consola, prevista en §5.8.
  - [x] Sin secretos ni hosts: `SESAME_BASE_URL` vacía, la clave por `keyvaultref`, DNIs de los
    tests sintéticos. Sin dependencias nuevas.
  - [x] Trampa (3): los dos `orm_models.py` son byte-idénticos (`cmp`), van en el mismo commit
    (a50a4ea) y `TABLAS` sube a 9 en los dos guardianes.
  - [ ] **Reglas de dominio: R3, ver los cambios 1 y 2.**
- **C3 bis / ter / C4 ter:** N/A (sin documentos de fuera, sin conversación, sin rutas sensibles).
- **C3 quater** (`azure-apps` `af27d0c`): [x] solo `partes.md`; [x] commit aparte, con el SHA en
  el informe; [x] sin URLs, claves ni IDs; [x] coincide con §8.
  - [x] Ningún agente hizo push. Hoy `main` ya no va por delante de `origin/main`: lo subió el
    humano.
  - `sesame-api.md` no existe, y por eso se nombra como P4 pendiente. Es aceptable por DA9.
- **C4** [x] trazabilidad (ver la tabla); [x] tests sin red ni BBDD real; [ ] M1–M7 sin comando
  en `current.md` (cambio 3).
  - [x] Dobles: `RepoFestivos` y `_Refresco` exponen `leer_todas`, `guardar`, `festivos` y
    `refrescar`, igual que los reales. Comprobado a mano: `init.sh` no tiene puerta de dobles.
- **C4 bis** [x] rigor declarado; [x] RED real de T1, T3, T5, T7, T9, T11, T14, T16, T18, T20,
  T22 y T24; [x] cobertura 95,4 %; [x] «Evidencias» con tests, cobertura, tiempos y e2e;
  [x] capa e2e N/A, con el motivo impreso.
  - Pendiente (pasada de evidencias): mutación, supervivientes, muertos comprobados, tiempo,
    CAMPAÑA NO VÁLIDA, RM1, RM2, RM5, RM6 y la fila de mutantes de «Evidencias».
- **C5** [x] T1–T26 y T31 `[x]`, con un commit `F-032 Tn:` por tarea (T27 pendiente a propósito;
  T28–T30 son del humano); [x] árbol limpio; [ ] `spec_aprobada` (cambio 3).

## RM7: orden protegido (hecho ya, en copias del scratchpad)

R4 pide refrescar ANTES de `save_parte` y, por R15, antes de la pasada de esa ingesta. Probé dos
mutaciones de `persist_parte_pipeline.py`:
- (a) el refresco DESPUÉS de `save_parte`;
- (b) el refresco DESPUÉS de `_conciliar_recursos_safely`.

En las dos caen tres tests de la feature:
- `test_f032_ingesta.py::test_f032_r4_refresca_antes_de_guardar_con_dnis_y_anos`;
- `test_f032_ingesta.py::test_f032_r8_sin_dato_sube_a_revision_con_warning`;
- `test_f032_ingesta.py::test_f032_r9_un_error_inesperado_sube_a_revision_y_guarda`.

Un cuarto fallo, `test_f003_r8_…_gemelo_…`, es un artefacto de la copia (le falta sv4 al lado).
La suite ve el orden. El árbol de trabajo no se tocó.

## Puntos que pidió el líder

| Punto | Resultado |
|---|---|
| Recálculos sin llamar a Sesame | OK: la tabla no tiene cliente; `test_f032_r14_la_pasada_no_llama_a_sesame` |
| Upsert y caché | OK: `on_conflict_do_update` por el índice único; `al_guardar = olvidar`; el mismo `calendario` en `build_app` y el conciliador |
| 404 | OK: `sin_calendario`, ni escribe ni borra, sin revisión |
| Fallo o incompleto | OK: con fila ⇒ `conservadas`; sin fila ⇒ `sin_dato` ⇒ `review_required` y un WARNING con el recuento |
| Respaldos sin fila | OK: sv3, el JSON (también con la lectura fallida); sv4, `holidays`, no fiable |
| Retirada de `[SIN-SESAME]` | OK: sin bloqueo, override, 422 ni marca nueva; el badge, por `sigrid_motivo` |
| Rejilla de obra | OK: `holiday_name_de` por fila, cabecera sin `mx-hol`, sin `(None, año)` |
| Gemelos y `CLAUDE.md` | OK: `festivos_guardados.py` idénticos (`diff`), guardián y lista cerrada (DA20) |
| DNIs en logs | **NO** (cambios 1 y 2) |
| Secretos o hosts en `infra/` y `azure-apps` | OK. Los ficheros de §6 están intactos |

## Cobertura: requisito → test

R1–R2 `contrato_festivos` y guardianes F-010/F-015 · R3 `refresco`/`wiring`, con cliente falso:
**insuficiente** (cambio 1) · R4–R10 `refresco`/`ingesta` · R11 `repositorio` · R12–R17 `wiring`,
`tabla_calendario`, `test_f003_r10` · R18–R20 `provider_tabla` · R21–R24 `sin_bloqueo` y los
adaptados · R25 `avisos` · R26–R28 `rejilla_obra` · R29–R33 `contraste` · R34–R37 `infra_sesame` ·
R38–R39 `recalculo` · R40 por el diff · R41 por lectura (OK) · R42 `festivos_guardados_gemelos`.

## Observaciones (no bloquean)

- Con Sesame colgado, 10 s por DNI: con `COLA_VISIBILITY_S = 300`, unas 25–30 claves (vigilar en M5).
- Comentario desfasado en `web/app.py` (aviso de `obra_detail`): «la columna pinta el calendario por
  defecto» (ya no, R27). El contraste usa `SesameApiClient._get`: desviación declarada, aceptable.

## Automejora (propuesta, no aplicada)

Añadir a `CHECKPOINTS.md` C3 una trampa (4): toda llamada HTTP nueva con un dato personal en la
query exige comprobar el log de httpx en INFO con la configuración de logging REAL del servicio,
no con un cliente falso.
