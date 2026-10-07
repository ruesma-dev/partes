# Integración F-035 + F-036 · tercera copia de «recurso persona» (sv4)

Rama `chore/integracion-f035-f036` (sale de dev `e2954c7`), worktree
`partes-wt-f037`. Commits locales, sin push.

## Qué cambió

- `tests/test_f036_recurso_persona_gemelos.py` (commit `0b3dd4e`): nuevo
  comprobador `filtro_sv4` + `_conjunciones`. Lee por AST
  `_SQL_RECURSOS_ACTIVOS` de sv4 y exige `res.cla = N` como conjunción de
  **nivel superior** de su único `WHERE` (sin `OR` de nivel superior), que
  `N` sea el `CLA_PERSONA` de sv3 y que `fetch_recursos_activos` use la
  constante. Docstring del módulo ampliado con la copia de sv4.
  Tests nuevos: `test_f036_r19_sv4_filtra_con_el_mismo_cla_que_sv3`,
  `test_f036_r19_falla_si_sv4_pierde_el_filtro` (4 copias rotas: filtro
  quitado, `AND` → `OR`, filtro bajado al `ON` del último `LEFT JOIN`,
  `fetch_recursos_activos` con otra SQL) y `..._falla_si_sv4_usa_otro_cla`.
  El `_roto` de los casos de sv4 va fuera del `pytest.raises`, para que un
  texto no encontrado no cuente como fallo del guardián.
- `CLAUDE.md` (commit `652371c`): la entrada «desde F-036 … recurso persona»
  de la lista cerrada nombra sv4 `infrastructure/sigrid/sigrid_lookup_client.py`
  (`WHERE res.cla = 1` en `_SQL_RECURSOS_ACTIVOS`). El resto, intacto.
- `progress/current.md`: nota de la integración.

**Sin cambios de comportamiento**: ningún fichero de `services/` tocado. El
SQL de sv4 casa con el criterio (`WHERE res.cla = 1`, mismo sentido que sv3
`es_persona` y sv5 `AND res.cla = 1`): no hubo que parar.

## Fase RED

Tests escritos antes que el comprobador:

```
python -m pytest tests/test_f036_recurso_persona_gemelos.py -q -k sv4 -p no:cacheprovider
>       assert filtro_sv4(roto) != 1
E       NameError: name 'filtro_sv4' is not defined
FAILED ...::test_f036_r19_sv4_filtra_con_el_mismo_cla_que_sv3
FAILED ...::test_f036_r19_falla_si_sv4_pierde_el_filtro[WHERE res.cla = 1\n  AND -WHERE ]
FAILED ...::test_f036_r19_falla_si_sv4_pierde_el_filtro[WHERE res.cla = 1\n  AND -WHERE res.cla = 1\n  OR ]
FAILED ...::test_f036_r19_falla_si_sv4_pierde_el_filtro[WHERE res.cla = 1\n  AND -AND res.cla = 1\nWHERE ]
FAILED ...::test_f036_r19_falla_si_sv4_pierde_el_filtro[sql=_SQL_RECURSOS_ACTIVOS,-sql=_SQL_EMPLEADOS,]
FAILED ...::test_f036_r19_falla_si_sv4_usa_otro_cla
6 failed, 11 deselected in 0.57s
```

GREEN: `python -m pytest tests/test_f036_recurso_persona_gemelos.py -v` →
`17 passed in 0.45s`. Motivo real de cada copia rota (comprobado a mano):
filtro quitado y bajado al JOIN → «filtra res.cla 0 veces»; `OR` → «OR de
nivel superior en el WHERE»; otra SQL → «fetch_recursos_activos ya no usa
_SQL_RECURSOS_ACTIVOS»; `res.cla = 2` → devuelve 2 (≠ 1). Real → 1.

## Evidencias

| Evidencia | Valor |
|---|---|
| `bash harness/init.sh` | verde: «ENTORNO LISTO», raíz `461 passed, 3 skipped in 104.53s`; sv1–sv5 verdes (caché, árbol sin cambios) |
| Guardián F-036 | 17 passed (antes 12; +5 de sv4) |
| Cobertura líneas cambiadas | N/A: la rama `chore/` no corresponde a ninguna feature declarada (PUERTA COBERTURA) |
| Mutación | no aplica (sin código de producción cambiado); las 4+1 copias rotas hacen ese papel sobre el guardián |
| ruff del fichero de test | «All checks passed!» |

## Pendiente

Revisión y merge de `chore/integracion-f035-f036` a dev (humano). Nada MANUAL.
