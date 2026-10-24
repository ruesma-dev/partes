# Informe del implementer · F-060 · Racha de incidencia con CIZ móvil

Rama `feature/F-060-racha-incidencia-ciz-movil` (worktree `partes-wt-f060`), desde a6d6d63.
Rigor **crítico**. Aprobación del humano (2026-10-23, literal): «a en todo, lanza implementer
y spec de la sigueinte feature» ⇒ DA1–DA11 = A. Regla del humano sobre Sigrid: no se borra,
solo se editan líneas ⇒ el CIZ se mueve con un `UPDATE`, nunca `DELETE`. **Enmienda tras la
review pasada 1** (humano, 2026-10-24, literal: «c y si a 2» ⇒ DA12 = C, DA13 = sí): sección
«Enmienda» abajo (T16–T22, T24; T23 la lanza el líder).

## Qué cambió (T1–T12)

**sv5** (`services/partes-transfer`): `application/services/racha_ciz.py` (nuevo, puro:
`decidir_fin` ⇒ `crear`/`mover`/`intermedio`/`parte_cerrado`/`enlazada`); modelos
(`LineaEntrada.racha_registro_ids`, `AccionLinea.mover`, `LineaSigrid.tex/pos`) y `LineaIn`
opcional; `config/settings.py` `MOVER_CIZ` (false); `sigrid_write_client.py`
`lineas_de_racha` y `stmt_mover_linea` (UN `UPDATE hmores` con WHERE optimista y guarda de
parte abierto en origen y destino; nunca `DELETE`); `registro_pipeline.py` paso 6 bis y
paso 9 (`movida_de`, `hmores_ide`, INFO `ciz movido`, WARNING `ciz_duplicados`); docstring de
R1 en `reglas_registro.py`; `tests/dobles.py` (`SigridFake`).
**sv4** (`services/partes-front`): `application/services/racha_incidencia.py` (nuevo, puro:
`ventana`, `hasta_delante`, `clave_incidencia`, `decidir`, `colapsar`, `aviso_desordenada`,
motivos); `parte_repository.py` `_roles_de_racha` + `_historico` (una consulta por
persona), `racha_registro_ids` y `avisos_racha`, `_fin_movido` con CAS en
`marcar_registros_sigrid`; `reparto_obras.py` (`GrupoObra.avisos_racha`); `app.py`
(preflight con `avisos_racha`); `static/app.js` + `styles.css` (`avisosRachaHtml`);
`tests/test_f025_aprobacion.py` (`CLAVES_LINEA`). **Docs** (T12): ARCHITECTURE,
`partes-proyecto.md` y `azure-apps/partes.md` (commit local c914caa, sin push).
Commits: f07aa3e T1, a2abad1 T2, d136b6b T3, 96203af T4, 6618fa8 T5, 80b3163 T6, 152589e T7,
d68f296 T8, 101e77f T9, c923d96 T10, 54f8701 T11, 09c4312 T12.

## Decisiones de diseño y desviaciones (T1–T12)

Justificadas en `progress/current.md` (bloque F-060, «Decisiones y desviaciones»): `decidir_fin` recibe `partes` (código y estado; un parte no leído cuenta como
cerrado); CIZ con fecha = D ⇒ `crear` (inalcanzable); `tex/pos` en T1; R23 con el origen
cerrado en carrera ⇒ `no_escrita`; `colapsar` con `LineaRol`; papelera solo de la misma clave
y `registrado`/`encolado`; `GrupoObra.avisos_racha` en T9; CAS de `fin_movido`; estilo `.ap-racha-avisos`. Además, ninguna lógica duplicada entre sv4 y
sv5 ni copia de la lista cerrada tocada.

## Fase RED (trazas reales, test escrito antes que el código)

```
T1 $ cd services/partes-transfer && python -m pytest tests/test_f060_racha_ciz.py -q
E   ImportError: cannot import name 'racha_ciz' from 'application.services' (...)
1 error in 0.58s
T2 $ python -m pytest tests/test_f060_pipeline_mover.py -k "contrato or settings" -q
E   AttributeError: 'Settings' object has no attribute 'mover_ciz'
E   AttributeError: 'LineaEntrada' object has no attribute 'racha_registro_ids'
9 failed, 1 warning in 6.61s
T3 $ python -m pytest tests/test_f060_cliente_mover.py -q
E   AttributeError: 'SigridWriteClient' object has no attribute 'lineas_de_racha'
E   AttributeError: 'SigridWriteClient' object has no attribute 'stmt_mover_linea'. Did you mean: 'stmt_insert_linea'?
15 failed in 1.61s
T4 $ python -m pytest tests/test_f060_pipeline_mover.py -k doble -q
E   AttributeError: 'SigridFake' object has no attribute 'estados_de_partes'
E   AttributeError: 'SigridFake' object has no attribute 'lineas_de_racha'
13 failed, 9 deselected, 1 warning in 3.12s
T5 $ python -m pytest tests/test_f060_pipeline_mover.py -k "r13 or r14 or r15 or r16 or r17 or r18 or r19 or r25 or r26" -q
E   Left contains one more item: {'registro_id': 4, 'hmoide': 901, 'parte_cod': 'PT26/00010', 'hora_codigo': 'CIZ', ...}
E   AttributeError: 'NoneType' object has no attribute 'ide'
E   +  where None = AccionLinea(registro_id=4, accion='escribir', ..., mover=None).mover
12 failed, 13 passed   (los 13 verdes fijan: interruptor apagado, sin ids o sin candidatas ⇒ nada cambia)
T6 $ python -m pytest tests/test_f060_pipeline_mover.py -q
E   KeyError: 'movida_de'
E   assert (5001, 901, 2...2026, 10, 704) == (7001, 901, 2...2026, 10, 704)
FAILED ...::test_f060_r20_mueve_la_misma_linea_con_un_update
FAILED ...::test_f060_r22_mover_no_inserta_ni_borra
FAILED ...::test_f060_ejemplo_del_humano_dia_a_dia      (y 6 más)
9 failed, 47 passed, 1 warning in 3.68s
T7 (R27 es caracterización: verde de entrada salvo el docstring)
E   AssertionError: assert ('MOVER_CIZ' in 'Reglas de negocio de QUE se registra en Sigrid ...')
1 failed, 12 passed
T8 $ cd services/partes-front && python -m pytest tests/test_f060_racha_incidencia.py -q
E   ImportError: cannot import name 'racha_incidencia' from 'application.services' (unknown location)
1 error in 0.58s
T9 $ python -m pytest tests/test_f060_aprobacion_racha.py -q
E   KeyError: 'racha_registro_ids'   (11)     E   KeyError: 'avisos_racha'   (8)
E   AssertionError: assert {2: 'fin'} == {2: 'inicio'}   (papelera y ventana)
26 failed, 3 passed, 1 warning in 6.81s
T10 $ python -m pytest -q -p no:cacheprovider tests/test_f060_aprobacion_racha.py -k "r28 or r29 or r30 or test_f060_r10_preflight or test_f060_r9_payload"
E   AssertionError: assert ('registrado' == 'omitido'
E   TypeError: object of type 'NoneType' has no len()
E   Right contains one more item: '[repo] fin_movido_sin_cas registro_id=2 movida_de=1 hmores_ide=9000'   (x3)
E   At index 0 diff: 'registrado' != 'omitido'      (cadena de movimientos)
E   KeyError: 'avisos_racha'                          (preflight)
7 failed, 9 passed, 29 deselected, 1 warning in 6.44s
T11 $ python -m pytest -q -p no:cacheprovider tests/test_f060_aprobacion_racha.py -k r11
E   assert 'g.avisos_racha' in '\n  function aprobar(peticion, contexto) {...'
E   AssertionError: app.js no define avisosRachaHtml   (x3)
4 failed, 45 deselected, 1 warning in 3.88s
```
Tras cada implementación, los mismos comandos en verde (T1–T7: 121 passed en los tres
ficheros de sv5; T8–T11: 109 passed en los dos de sv4). `node --check static/app.js` OK.

## Tests (resultado real, antes de la enmienda)

- sv5: 976 passed tras T7 (121 de F-060). sv4: 2671 passed, 1 skipped tras T9 (109 de F-060);
  `test_f022_*` y `test_f025_*` en verde tras T10 y T11. Los de ahora, en «Evidencias».

## Fuera del alcance

- Encender `MOVER_CIZ` en Azure y desplegar (los lanza el humano). Encenderlo espera el
  visto bueno de Administración a DA3 y DA6.
- Corregir rachas antiguas o CIZ legados (M0: 2 CIZ de partes en 2026/10, 0 enlazados, 0
  recursos-mes con más de uno). Mover hacia atrás (DA7): solo aviso `racha_desordenada`.
- Sin cambios de esquema ni de manifiestos (`MOVER_CIZ` va fuera del manifiesto, como
  `MENSUALES_A_DEDICACION`).

## Enmienda tras la review pasada 1 (implementer, 2026-10-24)

DA12 = C (`MOVER_CIZ` también gobierna sv4) y DA13 = sí (viaja la papelera de los días
saltados del tramo). Commits: 6c4220b T16, da2f7a5 T17, f01ccdd T18, 06b7b51 T19 (azure-apps
**44886eb**, local, sin push), 3f46273 T20, 03df3a7 T21, d70bb29 T22; T24 abajo.

**Qué cambió**
- **T16 · sv4**: `config/settings.py` `mover_ciz` (`MOVER_CIZ`, false) con su comentario;
  `parte_repository.py` `_rol_incidencia_anterior` (copia de `_rol_incidencia` de dev
  0926857) y `lineas_para_registro(..., mover_ciz=False)`: apagado, ese rol línea a línea, sin
  `_roles_de_racha`/`colapsar`/`aviso_desordenada`, listas y avisos vacíos; `app.py` pasa
  `settings.mover_ciz`. `marcar_registros_sigrid` sigue aplicando `movida_de` siempre (R28).
  Tests: `tests/test_f060_interruptor_sv4.py` (nuevo, 14) y los de la regla nueva piden
  `mover_ciz=True` (`_datos`) o `MOVER_CIZ=true` (fixture `portal`).
- **T17 · sv4**: `racha_incidencia.decidir`: con `fin`, la papelera `registrado`/`encolado`
  de la clave con fecha ≠ D en `[min(racha ∪ {D}), max(racha ∪ {D})]`, saltados incluidos.
  4 tests puros y 1 de repositorio (`test_f060_r9_da13_*`).
- **T18 · sv5**: `test_f060_r26_extremo_a_extremo_con_sv4_apagado[False|True]`: roles
  `intermedio`, `intermedio`, `fin` con listas vacías ⇒ UN CIZ (el del 4), también con sv5
  encendido (sin ids no se lee nada). Verde de entrada (caracteriza R26; T18 no pide RED).
- **T19 · docs**: comentario de `MOVER_CIZ` en `config/settings.py` de sv5 (y sv4 en T16),
  `docs/ARCHITECTURE.md` semántica 4, `partes-proyecto.md` §3.5, §4.4 (papelera e
  interruptor), variables (fila de sv4 y sv5) y §7; `azure-apps/partes.md` §3.5 3c, «Qué se
  rompe», §5.6 (sv4 y sv5) y §6. Orden: encender sv5→sv4, apagar sv4→sv5; apagar los dos es
  la vuelta atrás completa (lo ya movido no se deshace).
- **T20**: `progress/current.md` con M1, M2 y M3 con comando exacto (arranque local, lecturas
  L/S/V, pasos del portal, lo esperado tras cada día, limpieza) y M4 con encendido sv5→sv4 y
  vuelta atrás sv4→sv5. **T21**: «aceptados por el humano (2026-10-24, «acepto»)». **T22**:
  `progress/equivalentes_F-060.py`, citado en `progress/mutacion_F-060.md`.

**Decisiones y desviaciones**
1. T16: apagado, el rol se calcula tras el bucle de las líneas (dev 0926857 lo hacía dentro):
   mismas consultas, sin escrituras entre medias, mismo resultado.
2. T21: el grep de su verificación solo devuelve el propio texto de T21 en `tasks.md`, que
   cita la frase; no se toca el texto de la spec.
3. T22: el #6 ya no existe en la línea 172 (T17 movió la condición a `viaja`): se demuestra
   sobre `f = int(l.fecha_int or 0)` de `viaja`. La campaña de T23 regenerará los mutantes.
4. M1–M3 se hacen con el sv4 LOCAL contra el PostgreSQL local (comprobado sin imprimir
   valores: `PG_HOST` local y `TRANSFER_BASE_URL` a `127.0.0.1:8005`), así que «+ Nuevo parte»
   no toca la base de producción. `verificar` no imprime `ide` ni `synckey`: el MISMO `ide`
   se mira con la lectura S (sigrid-api, solo lectura) y en el INFO `ciz movido` de sv5.

**Comprobación de la copia (T16)**, `git show 0926857:…/parte_repository.py | sed -n 2217,2280p`
frente a las mismas 64 líneas de `_rol_incidencia_anterior`:
```
2,3c2,3
<     def _rol_incidencia(session, reg: ParteRegistroOrm) -> str:
<         """Rol de una incidencia: 'inicio', 'fin' o 'intermedio'.
---
>     def _rol_incidencia_anterior(session, reg: ParteRegistroOrm) -> str:
>         """Rol de una incidencia (dev 0926857; MOVER_CIZ apagado, DA12).
```

**Fase RED** (test antes que el código; `services/partes-front`):
```
T16 $ python -m pytest tests/test_f060_interruptor_sv4.py -q --tb=line -p no:warnings
E   AssertionError: assert [('fin', [1, ...', [1, 2, 3])] == [('intermedio..., ('fin', [])]
E   TypeError: ParteReviewRepository.lineas_para_registro() got an unexpected keyword argument 'mover_ciz'   (x2)
E   AssertionError: assert [('inicio', [...', [1, 2, 3])] == [('inicio', [..., ('fin', [])]
E   AssertionError: assert ['inicio', 'intermedio'] == ['inicio', 'inicio']
E   AssertionError: assert ('fin', [1]) == ('inicio', [])          (documento inactivo)
E   AssertionError: assert [{'registro_i...acha a mano'}] == []     (avisos_racha apagado)
E   AssertionError: regla nueva con MOVER_CIZ apagado
E   AttributeError: type object 'ParteReviewRepository' has no attribute '_rol_incidencia_anterior'
E   AttributeError: 'Settings' object has no attribute 'mover_ciz'
E   AssertionError: assert ('fin', [1, 3, 4]) == ('intermedio', [])  (app.py, x2)
E   AssertionError: assert [{'registro_i...acha a mano'}] == []     (preflight)
13 failed, 1 passed in 5.42s
T17 $ python -m pytest tests/test_f060_racha_incidencia.py tests/test_f060_aprobacion_racha.py -k r9 -q --tb=line
E   AssertionError: assert DecisionRacha..._ids=(20, 40)) == DecisionRacha...=(20, 30, 40))
E   AssertionError: assert DecisionRacha...o_ids=(1, 40)) == DecisionRacha...s=(1, 30, 40))
E   assert (1,) == (1, 2, 3)
E   assert [3, 8] == [3, 4, 7, 8]
4 failed, 21 passed, 95 deselected in 4.34s
```
En verde tras el código: T16 `tests/test_f060_interruptor_sv4.py tests/test_f060_aprobacion_racha.py
tests/test_f025_aprobacion.py` ⇒ 99 passed; vecinos (`test_f019_portal`, `test_f022_aprobar_seleccion`,
`test_f024_borrado_sigrid`, `test_f046_aplicar`, `test_f060_racha_incidencia`) ⇒ 350 passed.
T17 `-k r9` ⇒ 25 passed. T18 `-k r26` (sv5) ⇒ 10 passed.

**T22** (`progress/equivalentes_F-060.py`): `sv4` ⇒ «4 mutantes, 0 distintos», exit 0;
`sv5` ⇒ 5.000 escenarios del pipeline (142 con CIZ movido, 2.288 con un `fin` sin recurso) e
invariante de #12 (200.000 llamadas, 11.467 `mover`, todos con `hmoide`) ⇒ «2 mutantes, 0
distintos», exit 0. El diferencial sí caza mutantes no equivalentes (comprobado con 5).

## Pendiente (MANUAL y del líder)

- **T23 (líder)**: campaña de mutación de nuevo (el código de producción cambió tras T13).
- **T14 · M1–M3** (humano, local, modo pruebas) y **M4** (producción, solo lectura, tras
  encender sv5→sv4): comandos exactos en `progress/current.md` (sección F-060).
- **T13**: hecha; 6 equivalentes aceptados por el humano (2026-10-24, «acepto»).

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados (init.sh, T24) | raíz 498 passed, 3 skipped · sv4 **2717 passed**, 1 skipped · sv5 **982 passed** · sv1–sv3 en verde (caché, árbol sin cambios) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 99.7% de 339 líneas cambiadas cubiertas (338/339, umbral 80%, nivel critico)` |
| Mutantes generados / supervivientes | Campaña de T13 (sobre `1009cdb`): 221 evaluados, 204 muertos, 16 supervivientes, 1 timeout; 22.626 s, **workers 4**; tras el análisis, 10 muertos con test nuevo y 6 equivalentes aceptados por el humano (2026-10-24, «acepto»), timeout detectado (`progress/mutacion_F-060.md`). **T23 pendiente** (la lanza el líder): T16 y T17 cambian producción |
| Tiempo de la suite | raíz 89,59 s · sv4 656,39 s (10:56) · sv5 12,90 s |
| `bash harness/init.sh` (T24) | **verde**, exit 0 («ENTORNO LISTO. Puedes trabajar.»); `PUERTA TAMAÑO` OK (requirements 150/150, design 249/250, review 137/140; impl medido antes de este informe); AVISOS de siempre (F-032 `blocked`, ruff 796 de deuda, `infra` sin tests) |
| Antes de la enmienda (T15 y tras T13) | verde: raíz 498 passed, 3 skipped · sv4 2698 passed, 1 skipped (472,61 s) · sv5 980 passed (9,58 s) · cobertura 99,7 % (323/324) |
