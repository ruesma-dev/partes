<!-- specs/F-052-sincronizar-con-sigrid/requirements.md -->
# F-052 · Sincronizar con Sigrid — Requisitos

Petición del humano (2026-10-20, literal): «añade una spec de sincronizar, de forma que dentro
de una obra o una persona se pueda dar a sincrnizar lea sigrid y compare contra lo que hay en
el portal, eso nos permitira conciliar linea a linea o en masa».

**Depende de F-050** (clave `rec-{recurso}` de la persona), ya en `dev`: la rama lleva `dev`
69af0f5 fusionado (0be3ef7; revalidación 2026-11-01, `tasks.md`). Toca **sv5** (una lectura nueva de solo lectura) y **sv4** (comparación, panel y
acciones hacia el portal); ni sv1, ni sv2, ni sv3, ni el esquema. Rigor **crítico**
(DA8): abre una vía controlada para escribir en líneas congeladas de producción. Alcance de
esta entrega, aprobado por el humano el 2026-11-02 (design §8): **comparar y conciliar hacia el portal**; las
escrituras en Sigrid (vía sv5) quedan para una feature posterior (DA1).

> **Regla del humano: en Sigrid no se borra.** Si algo debe desaparecer, se edita la línea a 0
> (`can = 0`), nunca `DELETE`. F-052 no escribe en Sigrid; la feature posterior lo respetará.

## Glosario

- **Ámbito**: la vista desde la que se sincroniza: obra (`obr-{ide}`) o persona (`rec-{R}`,
  F-050), con su **periodo** visible (`period` + `mode`, nómina 16→15 o natural).
- **Línea del portal**: `parte_registros` activa (fuera de la papelera, documento activo) del
  ámbito y con fecha dentro del periodo.
- **Línea de Sigrid**: fila de `hmores` con `obride` = la obra (ámbito obra) o `reside` = R
  (ámbito persona) y `fec` en el periodo, más las que lleven `partes:<id>` de una línea del
  portal del ámbito, estén donde estén. **Origen**: `partes` (`partes:<id>`), `ciz`
  (`partes:<id>:ciz`, F-062), `franquicia` (`partes:franquicia:<id>`, F-056), `ajena` (otro
  prefijo, p. ej. `porcentajes:`) o `manual` (sin synckey). Lo decide sv5, no sv4.
- **Casar**: emparejar por synckey (`partes:<registro_id>`); sin ella, el respaldo de F-024
  (`sigrid_hmores_ide` guardado, sin synckey y mismo recurso y fecha).
- **Firma**: huella de lo que el usuario vio de un ítem (clase y valores de los dos lados).

## Lectura de Sigrid (sv5, solo lectura)

- **R1.** CUANDO sv5 recibe `POST /api/sincronizar/leer` con `obra_ide` o `recurso_ide`,
  `desde`, `hasta` (YYYYMMDD, ≤ 62 días) y `registro_ids` (0–`SINCRONIZAR_MAX_REGISTRO_IDS`), debe
  devolver las líneas de Sigrid del glosario sin nombres, DNIs ni `tex`.
- **R2.** Cada línea devuelta debe llevar `hmores_ide`, `hmoide`, `parte_cod`, `parte_est`,
  `obra_ide`, `obra_cod`, `recurso_ide`, `fecha_int`, `hora_ide`, `hora_cod`, `hora_ext`,
  `partida_ide`, `partida_cod`, `can`, `tot`, `enlazada`, `origen` y, leído de su synckey,
  el `registro_id` (`partes` y `ciz`) o el `ajuste_id` (`franquicia`).
- **R3.** sv5 debe pedir cada lectura hasta el límite real de la API (`SIGRID_API_MAX_ROWS`,
  500.000 filas), ordenada por `hmores.ide`, pasar a otra página (`OFFSET/FETCH`) solo si esa
  viene llena y tratar `truncated: true` como error, sin devolver parciales. No hay tope de
  líneas: el límite es el tiempo (R4).
- **R4.** SI una lectura de sigrid-api falla o se corta por tiempo (`SIGRID_API_TIMEOUT_S`; el
  balanceador corta a los 230 s), ENTONCES sv5 debe responder 502 con `ok: false`, sin parciales.
- **R5.** El endpoint no debe tomar el lock de escritura ni llamar a `/api/sql/write`, y debe
  leer la base de escritura (`ruesma`, como F-024: la réplica puede ir con retraso).
- **R6.** SI faltan `obra_ide` y `recurso_ide`, vienen los dos, el rango es inválido o hay más
  `registro_ids` que `SINCRONIZAR_MAX_REGISTRO_IDS`, ENTONCES 422 sin leer Sigrid.

## Comparación (sv4, pura)

- **R7.** CUANDO el usuario pulsa «Sincronizar con Sigrid» en `/obras/{clave}` o
  `/trabajadores/{clave}`, sv4 debe leer las líneas del portal del ámbito y periodo, pedir a sv5
  las de Sigrid (R1, con los `registro_ids` del portal) y devolver un ítem por línea, sin
  escribir nada salvo R10.
- **R8.** Cada ítem debe tener exactamente una clase:
  `igual` · `distinta` · `anulada_en_sigrid` · `borrada_en_sigrid` · `en_sigrid_sin_registrar` ·
  `pendiente` · `no_viaja` · `en_vuelo` · `solo_sigrid_nuestra` · `solo_sigrid_ajena` ·
  `solo_sigrid_manual` · `solo_sigrid_auxiliar` (definición y ejemplo en design §3). Un ítem
  `solo_sigrid_*` con `can = 0` y código no `CI*` lleva `a_cero`; el panel los oculta por defecto
  con su recuento.
- **R9.** Para una pareja casada, sv4 debe comparar horas (tolerancia 0,005; no en
  incidencias), clase de hora (`hora_ext` contra ordinaria/extra del portal), partida, recurso,
  fecha y obra, y listar cada diferencia como `{campo, portal, sigrid}`. El código de hora con
  la misma clase es **nota**, no diferencia (las reglas de sv5 lo cambian, F-024 R6).
- **R10.** CUANDO una línea `registrado` del portal no aparece en Sigrid, sv4 debe confirmarlo
  con la comprobación existente de F-024 (`ComprobacionSigrid.comprobar_ids`, `forzar`, origen
  `sincronizar`, llamada en proceso: `ORIGENES_COMPROBACION` de `/api/sigrid/comprobar` no
  cambia), que la pasa a `borrado_sigrid` como hoy; el ítem es `borrada_en_sigrid`.
- **R11.** Una línea `encolado` debe salir `en_vuelo` sin comparar; una `dedicacion`,
  `no_viaja` (con nota si aparece en Sigrid); una `omitido` no encontrada, `pendiente` si su motivo es
  `parte_no_abierto` o `pisada_no_anulada` y, si no, `no_viaja` con el motivo como nota.
- **R12.** Un `solo_sigrid_nuestra` debe decir dónde está su línea en el portal: `papelera`,
  `otro_ambito` (otra obra, persona o periodo), `parte_reemplazado` (parte desactivado por la
  reingesta de sv3) o `no_existe`.
- **R13.** La respuesta debe traer el recuento por clase, el periodo leído, la hora de la
  lectura y la firma de cada ítem; SI sv5 falla o responde `ok: false`, ENTONCES sv4 debe
  devolver el error sin ítems (nunca una comparación parcial).
- **R14.** El resultado es **efímero** (DA5): no se guarda en la base `partes`.
- **R15.** SI la clave del ámbito no permite leer Sigrid (obra sin `obra_ide`: `cod-`, `nom-` o
  `sin-obra`; persona `emp-`, `nom-` o `sin-trabajador`), ENTONCES el botón debe salir deshabilitado con el motivo y el
  endpoint responder 422.

## Acciones hacia el portal (sv4)

- **R16.** El sistema debe ofrecer por clase solo estas acciones (tabla en design §4):
  `marcar_registrada` (`en_sigrid_sin_registrar`), `traer_de_sigrid` (`distinta` y
  `anulada_en_sigrid` de líneas `registrado`, campos de DA3), `a_papelera`
  (`borrada_en_sigrid`), `reaprobar` (`borrada_en_sigrid`, `pendiente`) y `restaurar`
  (`solo_sigrid_nuestra` en `papelera`). Las demás clases son informativas.
- **R17.** CUANDO el usuario aplica una acción a un ítem, a una selección o a «todas las de
  esta clase», el portal debe pedir confirmación con el número de líneas y el resumen de
  cambios antes de llamar al servidor.
- **R18.** CUANDO sv4 recibe `POST /api/sincronizar/aplicar` (`accion`, `ambito`, `items` con
  `registro_id` y `firma`, ≤ 500), debe validar el ámbito como F-022 (un id ajeno ⇒ 422 sin
  tocar nada), **volver a sincronizar** el ámbito y aplicar solo los ítems cuya clase y firma
  sigan iguales; los demás vuelven en `descartados` con motivo «cambió desde que lo viste».
- **R19.** `marcar_registrada` debe poner `sigrid_estado = 'registrado'`, las referencias
  `sigrid_hmores_ide`, `sigrid_hmoide`, `sigrid_parte_cod` de Sigrid, `sigrid_registrado_by` =
  actor y `sigrid_registrado_at_utc`, con CAS sobre el estado leído.
- **R20.** `traer_de_sigrid` debe copiar a la línea los valores de Sigrid de los campos de DA3
  (`anulada_en_sigrid` ⇒ horas 0), aunque esté congelada por `registrado` o por parte aprobado,
  con CAS sobre los valores del portal leídos, y dejar la traza de R22.
- **R21.** SI el parte de la línea está en espera (F-043, también el parte nuevo de F-047:
  `_exigir_sin_recalculo`) o el día tiene un reparto
  que bloquea (F-046, `ESTADOS_BLOQUEAN`), ENTONCES `traer_de_sigrid` debe descartar ese ítem con el
  motivo correspondiente, sin escribir.
- **R22.** Toda acción que escribe debe firmar con `_actor(request)` (F-017) y dejar en
  `sigrid_motivo` «Sincronizado con Sigrid: <campo antes→después> · <actor> · <fecha>» (≤ 255),
  y un log INFO con acción, ids, recuentos y actor, sin nombres ni DNIs.
- **R23.** CUANDO `traer_de_sigrid` cambia horas o clase de hora, sv4 debe pedir UN recálculo
  compartido (F-049, motivo `sincronizar`) de los documentos tocados y de los de otras obras del
  mismo recurso y día; SI la cola falla, ENTONCES el cambio queda y la respuesta lo avisa
  (`recalculo: fallo`), como F-042.
- **R24.** `a_papelera`, `reaprobar` y `restaurar` deben reutilizar las rutas y guardas que
  ya existen (papelera de línea, modal de aprobar con `ambito` e `incluir_borradas`,
  restaurar), sin camino de escritura nuevo; el 409 de `restore_registro` (F-061, parte ya
  reprocesado) vuelve como descartado con su motivo.
- **R25.** La respuesta de `aplicar` debe traer `aplicados`, `descartados` (id y motivo) y,
  al terminar, el portal debe volver a sincronizar y pintar el resultado nuevo.

## Límites y no regresión

- **R26.** Ninguna sentencia de F-052 escribe en Sigrid; sv5 no cambia el registro, el
  reajuste ni la comprobación de F-024.
- **R27.** Las vistas de obra y persona no deben llamar a sv5 al cargar por F-052 (solo el
  botón); «Comprobar en Sigrid» (F-024) sigue igual.
- **R28.** La regla de congelación (`congelacion.py`, `esta_congelado` de sv3) no cambia: la
  excepción de R20 vive solo en el método de aplicar de la sincronización.
- **R29.** Una segunda sincronización del mismo ámbito en el mismo proceso mientras corre la
  primera debe responder 409 «ya se está sincronizando».
- **R30.** SI sv4 no tiene `TRANSFER_BASE_URL`, ENTONCES el botón no se pinta y el endpoint
  responde 503, como «Comprobar en Sigrid».
