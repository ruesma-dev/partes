Revisión completa (pasada 1) · `git diff e2954c7..0c251af`

# Review · integración F-035/F-036 (tercera copia de «recurso persona», sv4)

**Veredicto: APPROVED**

Rama `chore/integracion-f035-f036` en el worktree `partes-wt-f037`. Rigor: la
rama no es una feature de `features.json`; se aplica `estandar` por omisión.
Sin código de producción cambiado: cobertura N/A (impresa por init.sh, rama
`chore/`) y mutación N/A (no hay nada que mutar en `services/`; el papel lo
hacen las copias rotas del guardián, verificadas abajo).

## Qué se comprobó (con resultado real)

1. **init.sh en verde desde el worktree**: «ENTORNO LISTO», raíz `461 passed,
   3 skipped in 93.06s`, sv1–sv5 verdes, `PUERTA COBERTURA: N/A` con motivo.
   `git status` limpio después.
2. **Sin cambio de comportamiento**: `git diff e2954c7..HEAD -- services/` →
   0 líneas. Solo cambian `CLAUDE.md`, `tests/test_f036_...py`,
   `progress/current.md` y el informe.
3. **El guardián vigila la copia de sv4 de verdad**: `filtro_sv4` extrae por
   AST `_SQL_RECURSOS_ACTIVOS`, exige un único `WHERE`, una única conjunción
   de nivel superior `res.cla = N`, ningún `OR` de nivel superior, y que
   `fetch_recursos_activos` use la constante; `N` se compara con
   `CLA_PERSONA` de sv3. Suite del guardián: `17 passed`; ruff limpio.
4. **Sabe fallar (RED independiente del reviewer)**: sobre una copia del árbol
   en el scratchpad, con el SQL de sv4 cambiado a `WHERE res.cla = 2`,
   `test_f036_r19_sv4_filtra_con_el_mismo_cla_que_sv3` FALLA; con el filtro
   quitado falla con «el WHERE de _SQL_RECURSOS_ACTIVOS filtra res.cla 0
   veces». Mutaciones propias en memoria contra `filtro_sv4`, todas
   detectadas: `>= 1`, `IN (1, 2)`, `(res.cla = 1 OR 1=1)`, `NOT res.cla =
   1`, `res.cla = 1 OR res.cla = 3`, `res.cla = 3`, doble filtro `= 1 AND =
   2`. Único no detectado: añadir `AND res.cla = 1` al `ON` del `JOIN`
   interior **manteniendo** el `WHERE` — no es rotura (filtro redundante,
   mismo resultado). La traza RED del implementer (6 failed por `NameError`
   antes del comprobador) es coherente con el commit `0b3dd4e`.
5. **`_roto` falla ruidosamente** si el texto a estropear no existe (assert
   fuera del `pytest.raises`): un refactor del SQL no deja los tests de copia
   rota pasando en falso.
6. **CLAUDE.md**: diff de 4+/1−, solo dentro de la entrada «desde F-036 …
   recurso persona»: «candidatos; lo vigila» pasa a «candidatos, y sv4
   `infrastructure/sigrid/sigrid_lookup_client.py` (`WHERE res.cla = 1` en
   `_SQL_RECURSOS_ACTIVOS`, el selector de recursos de F-035) …; lo vigila».
   El resto de la lista cerrada, intacto.
7. **Convenciones**: ruta en primera línea, español, sin secretos ni prints.

## Checkpoints (aplicables a una integración sin código de producción)

- [x] C1 init.sh verde · [x] C2 tests existen y pasan · [x] C3 sin cambios
  fuera del alcance (`services/` intacto) · [x] C4 evidencia RED real
- N/A C3 bis / C4 bis (cobertura y mutación): sin código de producción; la
  puerta de cobertura lo imprime y la mutación no tiene alcance.
- N/A C5 tasks.md: integración sin spec (`sdd=false` de hecho); validada
  contra los cuatro puntos del encargo.

**Observación** (no bloquea): `filtro_sv4` es conservador; `WHERE (res.cla =
1)` o un subselect con su `WHERE` lo harían fallar sin cambiar el criterio.

**Cambios requeridos**: ninguno.
