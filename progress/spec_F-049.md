<!-- progress/spec_F-049.md -->
# F-049 · Informe del spec-author

## Revisión del 2026-10-20: rebase sobre dev `ff2ed8e` y diseño sobre dev + F-050

Encargo del líder (2026-10-20): poner al día la spec escrita el 2026-10-15 sobre `dc03468`,
con el orden de cola decidido por el humano (F-050 → **F-049** → F-014 → F-047) y el código
de dev más el de F-050 (rama `feature/F-050-misma-fila-para-el-mismo-trabajador`, leída solo
con `git show` / `git diff`; su worktree no se ha tocado).

### Rebase

`git rebase dev` de la rama `feature/F-049-editor-calendario-normal-y-extra`: conflictos solo
en `harness/features.json` (resuelto: el de dev más la entrada F-049 tras F-048),
`progress/current.md` (las dos partes; la sección de F-049 reescrita abajo) y `BACKLOG.md`
(regenerado con `harness/backlog.py`). El commit original queda reescrito sobre `ff2ed8e`.

### Qué cambió en la spec (`specs/F-049-editor-calendario-normal-y-extra/`)

- **Orden y dependencias**: fuera «después de F-046 y F-047». Va después de F-050 y antes de
  F-047. **No depende de F-047**: solo usa la guarda `_exigir_sin_recalculo` de F-043, que
  F-047 amplía al parte nuevo sin cambiar el texto (su R15); la celda hereda ese 409 cuando
  F-047 se fusione. Solape solo textual (`parte_repository.py`, `obra_detail.html`,
  `app.js`). Design §11; T1 ahora exige F-050 en dev.
- **Sección nueva «lo que cambia con F-050 y lo fusionado desde `dc03468`»** (design §2):
  F-046 (`data-reparto`, `_filas_reparto`, `_claves_de`, `ESTADOS_BLOQUEAN`, editar sin
  guarda de reparto), F-048 (`horas_extra_leidas`, solo traza), F-051 (nada de sv4) y F-050
  (`worker_key_for_registro` con `rec-`, `fila_para_alta_manual`, celda que junta IA y alta
  manual de filas del papel distintas y posiblemente de varios partes; `edit_*_id` no los usa
  ni plantilla ni JS).
- **Identificación de la celda (DA2, cambia por F-050)**: `POST /api/matriz/celda` recibe
  `obra_key`, `worker_key` (clave de F-050) y `fecha`; el servidor reconstruye la celda con
  `obra_key_for_registro` + `worker_key_for_registro` + `fecha_int` (`_celda`) y exige que los
  ids enviados sean exactamente sus líneas no congeladas (con `antes` = hora actual). Una
  línea movida, una clave antigua o una celda vacía dan el 409 «recarga» (R7, R11, R12, R31;
  plantilla con `data-obra-key` en la tabla y `data-wk` en cada fila).
- **Fila del papel de la línea nueva (DA6, cambia por F-050)**: `empleado_line_no` y leído
  de `fila_para_alta_manual` sobre el documento de la plantilla, y la nueva con la misma
  clave que la celda (R34; E9/E10 con el fixture E1 de F-050).
- **Fila `sin-trabajador` (DA12, nueva)**: se editan sus líneas pero no se le crean (R35).
- **Reparto de F-046 (DA11, nueva)**: aviso en el popup si la celda lleva `data-reparto`
  (R32) y 409 si el grupo (recurso, fecha) tiene un reparto `aplicando` (R33). Congelación
  sin cambios (`congelacion.py`, `_exigir_reg_editable`).
- **F-048**: materializar no toca `horas_extra_leidas` y la nueva nace con NULL (R18, R20).
- Ejemplos E9–E11 nuevos; tests y tareas al día (T1, T6, T7, T10–T12). Topes: requirements
  150/150, design ≤ 250 (`python -m harness.tamano --feature F-049` en verde).

### Decisiones abiertas que necesita validar el humano (design §13)

Todas son **propuestas** (las del commit original nunca se aprobaron). Recomendación: A en
todas.

| DA | Tema | Recomendación | ¿Cambia? |
|---|---|---|---|
| DA1 | Alcance: solo el popup de la matriz de obra | A | No |
| DA2 | Ruta atómica con CAS y celda por (obra, clave de trabajador, fecha) | A | **Sí, por F-050** |
| DA3 | Lo escrito manda: materializar las parejas tocadas | A | Matiz F-048 |
| DA4 | Recálculo seguido con espera al guardar | A | No |
| DA5 | A 0 no va a la papelera | A | No |
| DA6 | Plantilla, su documento, `line_index` nuevo y fila de `fila_para_alta_manual` | A | **Sí, por F-050** |
| DA7 | La nueva clona también la partida | A | No |
| DA8 | Deshacer manda las creadas a la papelera (`undo_last(actor=…)`, dos dobles) | A | No |
| DA9 | Rigor crítico | A | No |
| DA10 | Rangos 0–24 / −24–24 / nueva > 0 | A | No |
| DA11 | Reparto vivo: aviso y 409 solo en `aplicando` | A | **Nueva, por F-046** |
| DA12 | `sin-trabajador`: editar sí, crear no | A | **Nueva, por F-050** |

### Pendiente

- PARADA 1: aprobación del humano de DA1–DA12 y de la spec.
- M1 (humano, antes de implementar): confirmar la pantalla y el caso «solo ordinarias».
- Implementación solo cuando F-050 esté fusionada en dev (T1).
