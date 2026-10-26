Revisión completa (pasada 1) · `dev...HEAD` = `4047137..2155742`

# F-061 · Review (reviewer)

**Veredicto: APPROVED, CONDICIONADO a que el humano acepte el equivalente #1** de la
mutación (`parte_repository.py:4258`, `.limit(1)`→`.limit(2)`). Si lo rechaza, pasa a
CHANGES_REQUESTED, aunque ningún test podría matarlo porque es equivalente (§Mutación).
Las observaciones no bloquean.

**Rigor:** `estandar`, declarado en `features.json` (DA8). Exige fase RED, cobertura y
mutación con los supervivientes analizados. RM5 es N/A por nivel.

## Verificación ejecutada por el reviewer

- **`bash harness/init.sh`:** exit 0 y `ENTORNO LISTO`.
  - Raíz: `522 passed, 3 skipped`.
  - sv1–sv5 en verde, por caché.
  - `PUERTA COBERTURA: 96.9% (280/289)`.
- **sv4 sin caché:** `2884 passed, 1 skipped, 2 warnings in 588.69s`.
- **`python progress/equivalentes_F-061.py`:** `#1 equivalente en 6125 casos; el control
  .limit(0) difiere.` (salida 0).
- **`node --check static/app.js`:** OK.
- **Mutación, recálculo puro** (`parsear_diff`, `filtrar_produccion` y `generar_mutantes`
  sobre `4047137..HEAD`):
  - salen 668 líneas (131/300/20/217) y 110 mutantes, igual que el informe;
  - `random.Random(20260820).sample(·, 20)` reproduce la muestra, con los 4 supervivientes
    y el mismo texto original→mutado.
- **El script no ha corrido contra ninguna base:** no hay ningún
  `logs/limpieza_partes_vacios_*` ni en el worktree ni en `partes/`.
- **`git status`:** limpio, salvo este informe.

## Checkpoints

- **C1:** [x] exit 0 · [x] ficheros obligatorios.
- **C2:** [x] una sola feature `in_progress` · [x] rama `feature/F-061-…` · [x] `current.md`
  con F-061 arriba y al día (el historial de debajo es anterior; ver Automejora) · [x] no
  cierra ninguna feature.
- **C3:** [x] hexagonal (`parte_vacio.py` puro en application; ORM y bloqueos en
  infrastructure) · [x] ruta en la primera línea · [x] `print` solo en el script de consola
  (§4.4), sin secretos ni dependencias nuevas · [x] empleado/recurso e incidencias sin tocar,
  `orm_models.py` intacto en sv3 y sv4.
- **C3 bis:** N/A, no toca `docs/referencia/`.
- **C4**
  - [x] R1–R18 tienen tests trazables y en verde (tabla).
  - [x] R19–R20 se comprueban por revisión (design §6):
    - el diff solo toca sv4, docs, specs, progress, harness y BACKLOG;
    - en `azure-apps`, el commit 86640b4 solo cambia `partes.md`;
    - ARCHITECTURE: semántica 8 y consola.
  - [x] Tests sin red ni BBDD.
  - [x] M1 y M2 están en `current.md` con su comando exacto.
- **C4 bis**
  - [x] Rigor declarado.
  - [x] Fase RED con salida real en T1, T7 y T8.
  - [x] Cobertura `[OK]`.
  - [x] Totales de mutación verificados de forma independiente.
  - [x] **Campaña no reejecutada: 4373 s según el informe (> 60 s).** Me quedo en el
    recálculo puro más RM1–RM6.
  - [x] Coste por mutante: 4373 × 4 ÷ 20 = 875 s.
  - [x] Sin «CAMPAÑA NO VÁLIDA»; base rota = 0.
  - [x] **RM1:** medido en `b1bd419`. Desde entonces solo cambian `progress/`, `tasks.md` y
    un test, nada del alcance.
  - [x] **RM2:** media × W = 218,7 × 4 = 875 s, frente a una línea base de unos 695 s.
    Coherente.
  - [x] **RM3:** ningún muerto es equivalente (`docs[0]→[1]`, `or→and` en `vive_fuera`,
    409→410, `ok: True`…).
  - RM4: no hizo falta.
  - RM5: N/A por nivel, aunque reproduje el #1.
  - [x] **RM6:** no se quitó ninguna guarda. Los huecos #2–#4 se cerraron con tests (138bb45).
  - Campaña manual: N/A, la campaña fue automática.
  - [x] Los 4 análisis están completos. El #1 sigue pendiente del humano.
  - [x] «Evidencias» trae los 4 números y los 4 workers.
- **C4 ter:** N/A, no hay `rutas_sensibles.json`.
- **C5:** [x] T1–T13 con un commit `F-061 Tn:` cada una (T14–T15: N/A justificado, son
  MANUAL y van tras la fusión) · [x] sin temporales · [x] `in_progress` es el estado real.

## Cobertura requisito → test (`services/partes-front/tests/`)

| Req | Tests |
|---|---|
| R1 | `test_f061_borrado::test_f061_r1_*` (7: repositorio, endpoint, marca, bool) |
| R2 | `test_f061_r2_persona_*` (3), `test_f061_r2_deshacer_creadas_*` (2) |
| R3 | `test_f061_r3_sql_de_bloqueo_…`, `…_borrar_linea_bloquea_…`, `…_soft_delete_worker_bloquea_…`, `…_dos_borrados_seguidos_…` |
| R4 | `test_f061_r4_borrar_obra_…`, `test_f061_r4_borrar_parte_…` |
| R5–R8 | `test_f061_papelera::test_f061_r5_*`, `r6_*` (3), `r7_*` (5) + `test_f061_portal::test_f061_r7_restaurar_ensena_el_motivo`, `r8_*` (2) |
| R9–R11 | `test_f061_r9_*` (2), `r10_*` (3), `r11_*` (2) |
| R12–R13 | `test_f061_portal::test_f061_r12_*` (6, con `node --check`), `r13_*` (5, con Jinja2) |
| R14–R18 | `test_f061_limpieza::test_f061_r14_*`, `r14_r15_r16_informe`, `r17_*` (4), `r18_*` (2) y las funciones puras |

## Puntos con lupa (pedidos por el líder)

1. **Borrado físico.** Solo en `_borrar_retirados_sin_filas`: SQL `is_active=false AND
   deleted_at_utc IS NULL`, la marca (`es_retirado`) y ninguna fila. Con filas, nunca. Activo,
   nunca: una carrera acaba en un abrazo mortal abortado. PT26/00373, 00375 y 00376: su
   referencia vive en filas `registrado`, que no se eliminan. Aprobado: ver la observación 1.
2. **`FOR UPDATE`.** `borrar_linea` bloquea antes de las guardas y relee la línea.
   `soft_delete_worker` bloquea por `id`, relee y solo toca los partes bloqueados. El borrado
   en bloque se serializa sobre el parte, y la última petición lo retira (READ COMMITTED).
3. **409 al restaurar.** Comprueba antes de escribir y hace rollback; el test verifica que no
   cambian ni la línea ni el parte. Los dos endpoints dan `{"ok": false, "error"}` y `app.js`
   lo enseña.
4. **Script.** Informe en `READ ONLY`, sin ningún INSERT, UPDATE ni DELETE (lo comprueba un
   test). `parser.error` va antes de `Settings()`. Las tres exclusiones se recomprueban bajo
   bloqueo. Sin `SessionFactory` y sin `DELETE` de `parte_registros`.
5. **Duplicación.** No toca sv3, `congelacion.py` ni la lista cerrada; solo importa
   `vive_fuera` y `ESTADO_ENCOLADO`.

## Mutación: equivalente #1 (ACEPTADO por el humano el 2026-10-26: «acepto»)

El razonamiento es correcto. `.first()` es `None` si y solo si no hay filas, con `LIMIT 1` o
con `LIMIT 2`, así que la decisión (`fila is not None`) no cambia. La demostración muta solo
esa aparición, que comprueba única en su ámbito. Su control `.limit(0)` sí difiere, así que no
es ciega. Reproducida en verde. **Recomiendo aceptarlo.**

## Observaciones (no bloquean)

1. **Un parte aprobado puede acabar borrado físicamente**, por un camino estrecho y anterior a
   F-061:
   - `approve_document` y `_set_approval` (`parte_repository.py:3703`, `:4052`) no miran
     `is_active`, así que una pestaña abierta puede aprobar un parte ya retirado;
   - al vaciar la papelera, el barrido lo elimina.

   No viola R11, y la papelera de partes ya borra hoy un aprobado sin líneas `registrado`. Si el
   humano lo quiere, basta con `.where(ParteDocumentOrm.approved.is_(False))` en
   `_borrar_retirados_sin_filas` y un test. **El humano (2026-10-26): «si»**, aplicarlo.
2. **Carrera anterior en `vaciar_papelera`.** Si se restaura una línea durante el vaciado, se
   borra igualmente y el parte queda activo y vacío; se ve con «Sin líneas». `vaciar_papelera` y
   `hard_delete_registro` no bloquean el parte, aunque el design §7 dice «todo camino». El peor
   caso es un abrazo mortal abortado (500), sin corrupción.
3. **`undo_last`** aplica los snapshots de líneas antes de que `_deshacer_creadas` bloquee el
   parte: el orden es línea→parte, el inverso de `borrar_linea`. Lo peor es un abrazo mortal
   abortado.
4. **Dos restauraciones simultáneas** de partes retirados con el mismo sha256 pasan R7, y la
   segunda choca con el índice (500). Es teórico.

## Automejora (propuesta, no aplicada)

- **CHECKPOINTS C2** dice «`current.md` describe SOLO la sesión activa», pero aquí tiene 3.835
  líneas de historial. Propuesta: «la sección activa está arriba y al día», o mover el historial
  a `history.md`.
