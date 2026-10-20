<!-- progress/spec_F-034.md -->
# F-034 · Informe del spec-author

## 2026-10-20 · Spec escrita (`specs/F-034-escribir-solo-en-partes-abiertos/`)

Rama `feature/F-034-escribir-solo-en-partes-abiertos` desde `dev` 4bda57e, worktree
`C:\Users\pgris\PycharmProjects\partes-wt-f034`. F-034 pasa a `spec_ready` (prioridad 1, sin
cambiar); `BACKLOG.md` regenerado. Tamaño: requirements 125/150, design 211/250, tasks con
una tarea por línea.

### Hallazgos (todos los caminos de sv5 que escriben en Sigrid)

| Camino | Sentencia | ¿Comprueba `con.est` al escribir? |
|---|---|---|
| Alta de línea (registro: HTTP y cola) | `stmt_insert_linea` | **No**. El parte se elige bien dentro del lock (F-031), pero el lock solo serializa sv5: Administración puede cerrarlo en la ventana. Y tras escribir, el pipeline da por escritas todas (una línea que no entrase saldría `registrado`). |
| Pisado de conflicto confirmado | `stmt_borrar_linea` = `DELETE FROM hmores WHERE ide = ?` (`registro_pipeline.py` l.613–620) | **No**, y además **borra**: contradice la regla del humano «no se debe borrar en sigrid… se pondrá a cero». |
| Reaprobación / synckey existente | ninguna (`ya_registrado`) | No escribe. |
| Alta de parte (F-031 v5, idéntica a porcentajes) | `stmts_crear_parte` | Crea `est = 1`; no es línea. No se toca. |
| Reajuste F-046: guardia y `UPDATE` | `stmt_guardia_reajuste`, `stmt_actualizar_linea` | Sí (`c.est = ?`), sin `UPDLOCK` sobre `con`. |
| Reajuste F-046: extra nueva | `stmt_insertar_extra` | Solo indirecto (su base se actualiza antes en la misma transacción). |
| F-024, F-019, `comprobar_asiento_analitico.py` | — | No escriben en Sigrid. |

Además, `escribir` parte en lotes de 15 que son transacciones distintas: un cierre entre
lotes deja unas líneas dentro y otras fuera. `porcentajes` (`dedicacion-transfer`) tiene
el mismo hueco en su `stmt_insert_linea`/`stmt_borrar_linea`.

### Lo que propone la spec

- **Guarda en el propio SQL** de toda sentencia que toca `hmores`: `EXISTS (SELECT 1 FROM
  con c WITH (UPDLOCK, HOLDLOCK) WHERE c.ide = <hmoide> AND c.est = ?)`; el `INSERT` del
  registro pasa al patrón de subconsulta `x` (sin la trampa del agregado con `WHERE`).
- La línea de un pisado confirmado solo entra si sus pisadas ya no tienen horas (evita
  duplicar si la guarda impidió el `DELETE`); sirve igual si el pisado pasa a «poner a 0».
- **Relectura tras escribir** por synckey: lo que no entró sale `omitido` con motivo
  `parte_no_abierto: el parte PT.. ya no esta En registro (Cerrado); …; Reaprueba…`; al
  reaprobar, F-031 lo lleva al complementario. `borradas` se cuenta por relectura.
- **sv4**: solo `resultadoHtml` agrupa las omitidas por motivo (hoy dice «(reglas)»).
- `estado_parte.py`, `cuenta_analitica.py` y `stmts_crear_parte` **no cambian** (su test de
  copias en porcentajes compara con nuestro `dev`); nota a porcentajes en `azure-apps/partes.md`.
- Lista cerrada de `CLAUDE.md`: no crece.

### Decisiones abiertas para el humano (`design.md` §11)

| DA | Pregunta | Recomendación |
|---|---|---|
| DA1 | Dónde comprobar el estado | Guarda en cada sentencia SQL (`UPDLOCK, HOLDLOCK`) |
| DA2 | Línea cuyo parte se cerró en la ventana | `omitido` con motivo, reaprobable (→ complementario) |
| DA3 | Texto del motivo | El largo de `design.md` §5 |
| DA4 | Pisado con `DELETE` | Aquí solo guarda + R4; «pisar = poner a 0» en **feature aparte** (lo que el líder ya planteó) |
| DA5 | Reajuste F-046 con parte cerrado | Se mantiene DA10 de F-046 (no editable) + `UPDLOCK` y guarda en la extra |
| DA6 | Gemelo con porcentajes | No tocar sus copias; módulo nuevo `parte_abierto.py`; nota en `azure-apps/partes.md` |
| DA7 | Qué ve el usuario | Badge `omitido` con motivo (ya existe) + modal agrupado por motivo |
| DA8 | Lista cerrada de `CLAUDE.md` | No crece |
| DA9 | Motivo F-046 «(estado 10)» | No tocar |

### Verificaciones manuales

M1 (líder, solo lectura por `sql/read` contra `ruesma`, antes de implementar): partes de
obra por estado en 09–10/2026, líneas `partes:%` por estado de su parte y periodos con más
de un parte En registro (esperado 0); SQL en `design.md` §9. M2–M4 (humano, tras desplegar
sv5 y sv4; modo pruebas obra 0404, `PRUEBA-IA`; M3 con autorización expresa).
