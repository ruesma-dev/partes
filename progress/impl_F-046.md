# F-046 · Informe del implementer: reajuste en Sigrid al aprobar

Rama `feature/F-046-reajuste-en-sigrid-al-aprobar` (worktree `partes-wt-f046`),
rigor **crítico**. Toca sv5, sv3, sv4 y las dos copias del ORM.

## T1 · API real de F-045 (`reparto_ponderado.py`, en `dev` desde `9c5b7a1`)

- `git merge-base --is-ancestor 9c5b7a1 HEAD` → OK; `test_f045_*` (sv3) → `211 passed`.
- Públicas: `PASOS`, `elegir_paso(total, pesos)`, `Participante(clave, peso, llegada)`,
  `repartir(total, participantes, paso)`, `ORDINARIA`/`EXTRA`, `LineaDia`, `Ajuste(registro_id,
  horas_norm, extra_horas, horas_orig)`, `ResultadoDia(cuadra, paso, ajustes, n_obras,
  n_lineas)`, `repartir_dia(lineas, jornada)`, `diferencias_ideal(lineas, jornada)`.
- **H9**: `LineaDia` ya trae el equivalente de la pareja: `extra_auto: bool = False` y
  `base_id: int | None = None` (enmienda A de F-045), además de `horas_orig` y `fija`. F-046 los
  usa tal cual en vez de `pareja`/`extra_auto` nuevos y solo añade `reajustable: bool = False`.
