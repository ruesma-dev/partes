Revisión incremental desde 2155742 (pasada 2) · delta `2155742..a3dba3c` (pasada 1: completa, `4047137..2155742`)

# F-061 · Review (reviewer)

**Veredicto final: APPROVED.** La condición de la pasada 1 está cumplida: el humano aceptó el
equivalente #1 (2026-10-26: «acepto»). El arreglo de la observación 1, que pidió con «si», está
hecho, probado con su RED y no toca nada más. Las observaciones 2–4 quedan fuera por decisión
del humano.

**Rigor:** `estandar`, declarado en `features.json` (DA8). Exige fase RED, cobertura y mutación
con los supervivientes analizados. RM5 es N/A por nivel.

## Pasada 2 · delta `2155742..a3dba3c`

**Qué entra.** `229c30c` añade el filtro y dos tests; `ad2ef34` el informe; `a3dba3c` el
recorte de este fichero por la PUERTA TAMAÑO. Fuera de `progress/` el delta toca solo dos ficheros:
- `parte_repository.py`: una línea de código en `_borrar_retirados_sin_filas`,
  `.where(ParteDocumentOrm.approved.is_(False))`, más tres de docstring;
- `test_f061_papelera.py`: `_retirado_aprobado` y los dos `test_f061_obs1_*`.

`approve_document`, `_set_approval` y las observaciones 2–4 no se tocan.

**Cubre los dos caminos.** El filtro está en el único sitio de borrado físico, así que alcanza a
sus tres llamadores: `vaciar_papelera`, `hard_delete_registro` (eliminar la última fila) y
`limpiar_vacios`, que ya excluía los aprobados. Cada test cubre un camino:
- `test_f061_obs1_vaciar_*`: dos retirados aprobados, con fila en papelera y sin filas;
- `test_f061_obs1_eliminar_su_ultima_fila_*`: la fila se borra y el parte se queda.

`approved` es `NOT NULL DEFAULT false` (`orm_models.py:161`), así que `is_(False)` no deja
fuera ningún NULL.

**Verificación ejecutada por el reviewer:**
- **RED reproducido.** En una copia de `a3dba3c` en mi scratchpad, sin la línea del filtro:
  `-k obs1` ⇒ `2 failed`, los dos `obs1`. Con el filtro, `test_f061_papelera.py` da `20 passed`.
- **Mutante de la línea nueva.** Recalculado con `generar_mutantes` sobre el delta, sale uno
  solo: `[booleano] approved.is_(False) -> is_(True)`. Lo evalué por RM4, en una copia:
  **muerto, 5 fallos** (r9, r10, r10_r11 y los dos obs1). La rama completa pasa de 668 líneas y
  110 mutantes a 671 y 111. La campaña muestreada de `b1bd419` no se repite: el único mutante
  nuevo está muerto y verificado, y nada del alcance cambia salvo esa línea (RM1).
- **`python progress/equivalentes_F-061.py`:** `#1 equivalente en 6125 casos; el control
  .limit(0) difiere.` (salida 0). El `.limit(1)` sigue siendo único en su ámbito.
- **`bash harness/init.sh`:** exit 0, `ENTORNO LISTO`.
  - Raíz: `522 passed, 3 skipped`.
  - `PUERTA COBERTURA: 96.9% (280/289)`.
  - `PUERTA TAMAÑO` en verde (review 139/140).
  - sv4 salió en verde por caché. Por eso lo corrí entero sin caché en la copia de `a3dba3c`:
    `2886 passed, 1 skipped in 666.95s`. Es la cifra del informe; en la pasada 1 eran 2884
    más estos 2 tests.
- **`git status`:** limpio antes de este informe; las copias viven fuera del árbol.

**Checkpoints del delta:**
- [x] C1, init en verde.
- [x] C3: sin infraestructura en dominio; sin prints ni secretos.
- [x] C4: los tests nuevos no tocan red ni BBDD.
- [x] C4 bis: RED con la salida real en `impl_F-061.md`, reproducida por mí; cobertura `[OK]`;
  mutante nuevo verificado.
- [x] C5: commits con prefijo `F-061`, sin temporales.

El resto se da por aprobado en la pasada 1.

## Pasada 1 (resumen; detalle en el historial de git, `2a3cf8c`)

**Veredicto:** APPROVED, condicionado al equivalente #1, `parte_repository.py`
`.limit(1)`→`.limit(2)` en `_borrar_retirados_sin_filas`. **El humano lo aceptó el 2026-10-26:
«acepto».** `.first()` es `None` si y solo si no hay filas, con LIMIT 1 o con LIMIT 2. La
demostración tiene un control `.limit(0)` que sí difiere, así que no es ciega.

**Verificado:**
- init en verde, y sv4 sin caché `2884 passed`;
- recálculo puro de la mutación: 668 líneas y 110 mutantes, igual que el informe, con la
  muestra reproducida con la semilla `20260820`;
- **campaña no reejecutada: 4373 s según el informe (> 60 s)**;
- el script no ha corrido contra ninguna base;
- `node --check` OK.

**Checkpoints:**
- [x] **C1–C2.**
- [x] **C3:** hexagonal; `orm_models.py` intacto en sv3 y sv4.
- **C3 bis:** N/A, no toca `docs/referencia/`.
- [x] **C4:** R1–R18 con tests; R19–R20 por revisión; en `azure-apps`, `86640b4` solo cambia
  `partes.md`; M1 y M2 están en `current.md`.
- [x] **C4 bis:**
  - RED en T1, T7 y T8;
  - cobertura `[OK]`;
  - totales verificados;
  - RM1: medido en `b1bd419`;
  - RM2: 218,7 × 4 = 875 s frente a una línea base de unos 695 s;
  - RM3: ningún muerto es equivalente;
  - RM6: no se quitó ninguna guarda.
- **C4 ter:** N/A, no hay `rutas_sensibles.json`.
- [x] **C5:** T1–T13 con un commit cada una. T14–T15 son N/A justificado: son MANUAL y van tras
  la fusión.

| Req | Tests (`services/partes-front/tests/`) |
|---|---|
| R1 | `test_f061_borrado::test_f061_r1_*` (7) |
| R2 | `test_f061_r2_persona_*` (3), `test_f061_r2_deshacer_creadas_*` (2) |
| R3 | `test_f061_r3_sql_de_bloqueo_…`, `…_borrar_linea_bloquea_…`, `…_soft_delete_worker_bloquea_…`, `…_dos_borrados_seguidos_…` |
| R4 | `test_f061_r4_borrar_obra_…`, `test_f061_r4_borrar_parte_…` |
| R5–R8 | `test_f061_papelera::test_f061_r5_*`, `r6_*` (3), `r7_*` (5), `test_f061_portal::test_f061_r7_restaurar_ensena_el_motivo`, `r8_*` (2) |
| R9–R11 | `test_f061_r9_*` (2), `r10_*` (3), `r11_*` (2), y desde la pasada 2 `test_f061_obs1_*` (2) |
| R12–R13 | `test_f061_portal::test_f061_r12_*` (6), `r13_*` (5) |
| R14–R18 | `test_f061_limpieza::test_f061_r14_*`, `r14_r15_r16_informe`, `r17_*` (4), `r18_*` (2) |

**Observaciones de la pasada 1:**
1. **Un parte retirado podía aprobarse desde una pestaña abierta, y luego se borraba
   físicamente.** El humano (2026-10-26) dijo **«si»** a arreglarlo. **Hecho en la pasada 2.**
2. **Carrera en `vaciar_papelera`.** Ni él ni `hard_delete_registro` bloquean el parte. Lo peor
   es un abrazo mortal abortado. Fuera, por decisión del humano.
3. **`undo_last`** bloquea en orden línea→parte, el inverso de `borrar_linea`. Lo peor es un
   abrazo mortal abortado. Fuera, por decisión del humano.
4. **Dos restauraciones simultáneas** con el mismo sha256 acaban en un 500. Es teórico. Fuera,
   por decisión del humano.

## Automejora (propuesta, no aplicada)

- **CHECKPOINTS C2** dice «`current.md` describe SOLO la sesión activa», pero aquí lleva miles
  de líneas de historial. Propuesta: exigir que «la sección activa está arriba y al día», o
  mover el historial a `history.md`.
- **Revisión incremental:** el protocolo del reviewer debería decir qué hacer con una campaña MUESTREADA
  cuando el delta añade una línea al alcance. Aquí apliqué RM4 al mutante nuevo, pero RM1, al
  pie de la letra, pediría repetir 73 minutos de campaña por una sola línea. Propuesta: si el
  delta añade ≤ N mutantes, basta con evaluarlos por RM4 y dejarlo escrito.
