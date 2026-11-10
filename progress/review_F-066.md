<!-- progress/review_F-066.md -->
Revisión incremental desde 2bc9649 (pasada 2)

# F-066 · Review

**Veredicto: APPROVED**

**Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura,
mutación completa con cero supervivientes sin justificar y las MANUAL listadas.

La pasada 1 (`git show 2bc9649:progress/review_F-066.md`) revisó la feature entera contra `0d8fc14`
y la dio por buena en código, tests y mutación:

- Alcance recalculado: 7 ficheros, 138 líneas, 21 mutantes, igual que el informe.
- RM1–RM6 cumplidas; dos de los supervivientes matados, reproducidos en una copia.
- Solo sv4: sv3, sv5, `congelacion.py`, `orm_models.py` y los gemelos quedan sin cambios.
- La regla vive solo en `clase_hora.py`, y R6 y R11 vigilan que no se copie.
- La tabla requisito → test de la pasada 1 sigue valiendo: el delta no toca tests.

Lo ya aprobado allí no se vuelve a leer.

## Delta revisado (`2bc9649..be9baf7`)

- `6b6adf9` y `be9baf7`. Solo cambian `progress/current.md` y
  `specs/F-066-selector-hora-por-prefijo-he/tasks.md`.
- No tocan producción, tests, firmas ni el alcance de la mutación, así que no invalidan nada de
  lo aprobado.

## Ejecución (entera, como exige el protocolo)

- `bash harness/init.sh` sobre `be9baf7`: **ENTORNO LISTO**, exit 0.
  - `PUERTA COBERTURA` 99.9% (783/784) [OK].
  - `PUERTA TAMAÑO` [OK]: impl 219/220 y review 139/140.
- sv4 salió **de caché** en `init.sh`. Lo ejecuté además **a mano y sin caché** desde
  `services/partes-front` (`python -m pytest -q -p no:cacheprovider`):
  **3740 passed, 1 skipped in 623.28s**.
- El resto de servicios también salió de caché, pero la feature no toca sus árboles.

## Cambios requeridos de la pasada 1: cómo quedan

1. **[x]** `tasks.md`: T9 `[x]`.
2. **[x]** `current.md`, sección F-066:
   - el estado está al día: T1–T9 hechas, con la T9 explicada (21/18/3 y los supervivientes
     matados con `test_f066_r7_log_cuenta_excluidas`);
   - ya no aparecen ni «Decisiones que debe validar el humano» ni «`features.json` en `pending`»;
   - la aprobación consta con sus DA;
   - **M2 listada en 6 pasos** (obra 0404, sin `HENC`, `HEOF` en «Horas extra», badge al
     recargar, deshacer, sin aprobar ni enviar). Coinciden con `requirements.md`.
3. **[x]** `tasks.md`: T11 `[x]`, en su propio commit (`be9baf7`), y he comprobado yo que `init.sh`
   está en verde sobre ese HEAD.
4. **[x]** `impl_F-066.md` no se tocó y sigue en 219/220.

## Checkpoints (afectados por el delta; el resto, como en la pasada 1)

- C1: [x] `init.sh` exit 0 · [x] están los ficheros del arnés.
- C2: [x] una sola `in_progress` · [x] rama de la feature · [x] la sección de F-066 describe la
  sesión activa. Lo que se acumula de features anteriores ya venía de antes y no es de F-066 ·
  [x] no hay `done` nuevo.
- C3: [x] sin cambios en el delta (aprobado en la pasada 1).
- C3 bis: N/A, no toca `docs/referencia/`. C4 ter: N/A, no existe `harness/rutas_sensibles.json`.
- C4: [x] trazabilidad (tabla de la pasada 1, sin cambios) · [x] sin red ni BBDD ·
  [x] la MANUAL M2 aparece en `progress/current.md` con sus pasos exactos.
- C4 bis: [x] todo como en la pasada 1:
  - fase RED con trazas reales;
  - cobertura [OK];
  - mutación recalculada (21 mutantes y alcance de 138 líneas);
  - campaña no reejecutada: 10220,6 s según el informe;
  - RM1–RM6 [x];
  - 0 supervivientes vivos;
  - «Evidencias» completas (workers en la fila del informe de mutación).
- C5: [x] `tasks.md`: T1–T9 y T11 `[x]`, con un commit `F-066 Tn:` por tarea. T10 sigue `[ ]` con
  motivo: es la M2 del humano tras desplegar sv4, el despliegue lo pide el humano y es el mismo
  criterio que la T12 de F-055 · [x] `git status` limpio · [x] `features.json` en `in_progress`.
  Pasarla a `done` es cosa del líder después de este veredicto.

## Pendiente fuera de este veredicto (no bloquea)

- **T10 · M2**, del humano, después de desplegar sv4.
- `azure-apps/partes.md`: la l.933 llama a `hora_ext` «(¿es extra?)» y la l.1233 sigue
  mencionando F-006, que está retirada. Recomiendo corregirlas aquí o en F-067; el contrato no
  cambia.
- F-067: sv3 y sv5, más el guardián de gemelos.

## Automejora (propuesta, no aplicada)

Se mantiene la propuesta de la pasada 1 sobre los workers. Además, en una pasada cuyo delta no
toca el árbol de ningún servicio, reejecutar la suite sin caché no aporta nada (aquí costó 10 min).
Propongo eximir de ese paso a un delta que solo toque `progress/` o `specs/`, siempre que `init.sh`
diga que sirvió de caché por «árbol sin cambios desde el último verde».
