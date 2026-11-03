# F-052 · Informe del implementer (tanda T1–T8)

Rama `feature/F-052-sincronizar-con-sigrid`, worktree `partes-wt-f052`, desde 846f6aa.
Rigor **crítico**. Alcance de esta tanda: T1–T8; **T8 es el punto de control** (M2 del humano).
La campaña de mutación la lanza el líder después.

## T1 · Base y datos de partida

- `git merge-base --is-ancestor dev HEAD` ⇒ verdadero: `dev` sigue en 69af0f5 y ya está
  fusionado (0be3ef7). No hay nada que fusionar.
- **Clave real de persona** (F-050, `parte_repository._clave_trabajador`): `rec-{recurso}` si la
  línea está casada y tiene recurso (`recurso_ide` o, si es NULL, `empleado_reside`); si no,
  `emp-{ficha}`, `nom-<leído>` o `sin-trabajador`. Solo `rec-` permite leer Sigrid (R15).
- **Clave de obra**: `obr-{obra_ide}`; sin `obra_ide`, `cod-`, `nom-` o `sin-obra` (R15).
- **M1** (líder, 2026-11-02, solo lectura; `design.md` §9): obra mayor 244 líneas en 5,4 s
  (natural) y 371 en 4,8 s (nómina), recurso con 11 obras 23 líneas en 0,8 s, lote de 200
  synckeys 7,9 s, `truncated` nunca. Se queda `WHERE hmores.obride = ?`. Salvedad: sin líneas
  `partes:`; M2 debe elegir obras y personas con líneas del portal.
