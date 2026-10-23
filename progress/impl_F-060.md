# Informe del implementer · F-060 · Racha de incidencia con CIZ móvil

Rama `feature/F-060-racha-incidencia-ciz-movil` (worktree `partes-wt-f060`), desde a6d6d63.
Rigor **crítico**. Aprobación del humano (2026-10-23, literal): «a en todo, lanza implementer
y spec de la sigueinte feature» ⇒ DA1–DA11 = A. Regla del humano sobre Sigrid: no se borra,
solo se editan líneas ⇒ el CIZ se mueve con un `UPDATE`, nunca `DELETE`.

## Qué cambió

**sv5 (`services/partes-transfer`)**: el CIZ de una racha ya escrito se **mueve**, no se duplica.
- `application/services/racha_ciz.py` (nuevo): `decidir_fin` (pura) decide para una acción
  `escribir` con `CIZ`: `crear`, `mover`, `intermedio` (ya hay un CIZ posterior),
  `parte_cerrado` (`ciz_en_parte_cerrado`) o `enlazada` (motivo de F-053). Si hay varios CIZ
  candidatos anteriores mueve el más reciente y cuenta los duplicados.
- `domain/models/registro_models.py`: `LineaEntrada.racha_registro_ids`, `AccionLinea.mover`,
  `LineaSigrid.tex/pos`. `interface_adapters/api/app.py`: `LineaIn.racha_registro_ids`
  (opcional, por defecto `[]`: el contrato viejo sigue valiendo).
- `config/settings.py`: `MOVER_CIZ` (`mover_ciz`, **false por defecto**).
- `infrastructure/sigrid/sigrid_write_client.py`: `lineas_de_racha` (lectura por synckey en
  lotes) y `stmt_mover_linea`: UN `UPDATE hmores` de fecha, synckey y parte (`hmoide`,
  `obride`, `cenide`, `paride`, `caaide`, `ano`, `mes`, `pos`) con WHERE optimista (ide,
  recurso, fecha, tipo, synckey, `can = 0`, no enlazada) y guarda de parte abierto de F-034
  en el parte de origen y en el de destino.
- `application/pipelines/registro_pipeline.py`: paso 6 bis (`_ciz_de_racha`: una lectura de
  la racha y una de partes por petición; solo con `MOVER_CIZ`) y paso 9 (`stmt_mover_linea`;
  pos nueva solo si cambia de parte; la escrita lleva `movida_de` y `hmores_ide`; INFO
  `ciz movido` sin nombres; WARNING `ciz_duplicados`).
- `application/services/reglas_registro.py`: solo el docstring de R1.
- `tests/dobles.py`: `SigridFake` con `lineas_de_racha`, `estados_de_partes` y la op `mover`
  con la misma semántica que el SQL.

**sv4 (`services/partes-front`)**: decide el rol con el histórico y aplica el movimiento.
- `application/services/racha_incidencia.py` (nuevo, puro): `ventana` (día 1 del mes
  anterior a D − 1), `hasta_delante`, `clave_incidencia` (letra de F-025 o código
  normalizado), `decidir` (`inicio`/`fin` + `racha_registro_ids`), `colapsar` (un `fin` por
  racha y un `inicio` por día, persona y clave), `aviso_desordenada`, `motivo_desordenada`,
  `motivo_fin_movido`.
- `infrastructure/database/parte_repository.py`: `_roles_de_racha` + `_historico` sustituyen
  a `_rol_incidencia` (UNA consulta por persona, papelera marcada, `persona_de`); cada línea
  lleva `racha_registro_ids` y cada grupo `avisos_racha`; `marcar_registros_sigrid` aplica
  `movida_de` con CAS (`_fin_movido`) en la misma transacción.
- `application/services/reparto_obras.py`: `GrupoObra.avisos_racha`.
- `interface_adapters/web/app.py`: el preflight de cada obra lleva `avisos_racha`.
- `static/app.js` + `static/styles.css`: `avisosRachaHtml`, bloque propio en el modal.
- `tests/test_f025_aprobacion.py`: `CLAVES_LINEA` gana `racha_registro_ids` (enmienda prevista).

**Docs**: `docs/ARCHITECTURE.md` (semántica 4), `docs/referencia/partes-proyecto.md` (§3.5,
§4.4, §6 y la fila de sv5 de variables) y `azure-apps/partes.md` (§3.5 3c, «Qué se rompe»,
§5.6 `MOVER_CIZ`, §6): commit local **c914caa** en `azure-apps`, sin push.

Commits (uno por tarea): f07aa3e T1, a2abad1 T2, d136b6b T3, 96203af T4, 6618fa8 T5,
80b3163 T6, 152589e T7, d68f296 T8, 101e77f T9, c923d96 T10, 54f8701 T11, 09c4312 T12.

## Decisiones de diseño y desviaciones (justificadas también en `progress/current.md`)

1. `decidir_fin` recibe `partes: Mapping[int, ParteSigrid]` (código y estado) en vez de
   `estados`: los motivos de R17 y R18 nombran el código del parte. Un parte que no se pudo
   leer cuenta como cerrado (no se escribe a ciegas).
2. Un CIZ de la racha con fecha = D ⇒ `crear` (el paso 7 lo deja `incidencia_en_sigrid`);
   no puede llegar porque R9 excluye el día D.
3. `LineaSigrid.tex/pos` entraron en T1 (los usa la regla pura de R19).
4. R23 con el parte de ORIGEN cerrado en carrera: la relectura de F-034 solo mira los partes
   del periodo de D ⇒ sale `no_escrita` (con su ERROR), no `parte_no_abierto`. Nada más cambia.
5. `colapsar` recibe `LineaRol` con `racha_registro_ids`: dos `fin` son de la misma racha si
   son del mismo día o uno está en la racha del otro; con solo persona y letra, dos rachas
   distintas de la misma letra en una aprobación se fundirían.
6. La papelera entra en `racha_registro_ids` solo si es incidencia de la MISMA clave y está
   `registrado` o `encolado` (su synckey puede seguir en Sigrid).
7. `GrupoObra.avisos_racha` se añadió en T9 (sin él, `GrupoObra(**g)` falla).
8. CAS de `fin_movido`: exige `registrado` y el mismo `sigrid_hmores_ide`. Sin CAS: silencio
   si X ya está `omitido` con ese motivo (reentrega por la cola o por HTTP) y WARNING
   `fin_movido_sin_cas registro_id=… movida_de=… hmores_ide=…` en otro caso (sin nombres).
9. Duplicaciones: ninguna lógica nueva duplicada entre sv4 y sv5. sv4 decide el rol y sv5
   decide sobre lo que hay en Sigrid; no se tocó ninguna copia de la lista cerrada.

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

## Tests (resultado real)

- sv5 completo: **976 passed** (tras T7). F-060: 121 tests en `test_f060_racha_ciz.py`,
  `test_f060_cliente_mover.py` y `test_f060_pipeline_mover.py`.
- sv4 completo (tras T9, `python -m pytest -q -p no:cacheprovider -x`): **2671 passed,
  1 skipped en 547,95 s**. F-060: 109 tests en `test_f060_racha_incidencia.py` y
  `test_f060_aprobacion_racha.py`; más `test_f022_reparto_obras`, `test_f025_aprobacion`,
  `test_f022_aprobar_seleccion`, `test_f025_vistas` y `test_f022_vistas_seleccion` en verde
  tras T10 y T11.
- `bash harness/init.sh`: ver «Evidencias».

## Fuera del alcance

- Encender `MOVER_CIZ` en Azure y desplegar (los lanza el humano). Encenderlo espera el
  visto bueno de Administración a DA3 y DA6.
- Corregir rachas antiguas o CIZ legados (M0: 2 CIZ de partes en 2026/10, 0 enlazados, 0
  recursos-mes con más de uno). Mover hacia atrás (DA7): solo aviso `racha_desordenada`.
- Sin cambios de esquema ni de manifiestos (`MOVER_CIZ` va fuera del manifiesto, como
  `MENSUALES_A_DEDICACION`).

## Pendiente (MANUAL y del líder)

- **T13**: campaña de mutación (la lanza el líder): `python -m harness.mutacion --feature F-060`.
- **T14 · M1–M3** (humano, local, `OBRA_PRUEBAS_FORZAR=true`, `MOVER_CIZ=true`, obra 0404,
  `PRUEBA-IA`, limpiar con `prueba_escritura_sigrid.py limpiar --ejecutar`): día a día,
  cambio de mes y todo de una vez (`design.md` §9).
- **T14 · M4** (humano, producción, solo lectura tras encender): comando exacto en
  `progress/current.md` (sección F-060). Orden de despliegue: sv5 → sv4.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados (init.sh) | raíz 498 passed, 3 skipped · sv4 2692 passed, 1 skipped · sv5 976 passed · sv1–sv3 en verde (caché, árbol sin cambios) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 99.4% de 324 líneas cambiadas cubiertas (322/324, umbral 80%, nivel critico)` |
| Mutantes generados / supervivientes | No lanzada por el implementer: la campaña es del líder (T13), por instrucción expresa |
| Tiempo de la suite | raíz 113,94 s · sv4 784,03 s (13:04) · sv5 25,47 s |
| `bash harness/init.sh` | **verde** («ENTORNO LISTO. Puedes trabajar.»); `PUERTA TAMAÑO` OK (requirements 142/150, design 248/250, impl 168/220); único AVISO, el de siempre de `infra` sin tests |
