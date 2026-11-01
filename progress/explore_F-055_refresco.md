<!-- progress/explore_F-055_refresco.md -->
# F-055 · refresco de la spec sobre `dev` 14b3cd5 (spec-author, 2026-10-31)

## Rama

`feature/F-055-sv5-omite-lineas-sin-fecha` rebasada de `dev` 2bfeab7 a 14b3cd5 (worktree
`partes-wt-f055`). Conflictos en `harness/features.json`, `progress/current.md` y `BACKLOG.md`:
se tomó la versión de `dev` (ya traía la entrada de F-055, idéntica salvo `spec`) y
`BACKLOG.md` se regeneró con `harness/backlog.py`. Commits: ba3cb52 (spec original rebasada),
a148e38 (refresco). Sin push; `dev` y las demás ramas, sin tocar.

## Qué se comprobó en sv5 (solo lectura)

- **Sonda repetida** con `SigridFake` sobre 14b3cd5 (scratchpad, sin commit): `0` ⇒ alta
  `PT0/00001` (0/00); `20261340` ⇒ `PT26/00001` del 2026/13; `20160315` ⇒ `PT16/00001`. El
  defecto sigue igual.
- **Paso 2a sigue siendo el punto único.** Los caminos que deciden una línea pasan todos por
  `RegistroPipeline.preparar`: preflight, ejecutar, cola, extras nuevas del reajuste (F-046)
  y, **nuevo**, la línea de ajuste de la franquicia (`FranquiciaPipeline._preparar`, F-056).
- **F-060 / F-062**: `_ciz_de_racha` (6 bis), `_ciz_ajeno` y el hermano `fin_mismo_dia` solo
  miran acciones `escribir`; el CIZ se busca por synckey, no por fecha. La omisión previa de
  `decidir` sigue antes que `_fin_mismo_dia`. Ningún camino nuevo lee Sigrid con la fecha
  antes de `preparar`.
- **F-056**: `_evaluar` de la franquicia lee E y los partes del mes del día de ajuste antes del
  veredicto, pero con la acción `omitir` el veredicto es `no_editable` y no se escribe ni se da
  de alta nada. `FranquiciaIn` ya valida el calendario (`_fecha_valida`): 0/`null`/imposibles
  son 422 ahí; F-055 solo añade el rango.
- **F-038**: solo el cliente (`truncated`); sin efecto.
- sv4 sigue mandando `int(r.fecha_int or 0)` (ahora `parte_repository.py` l. 2284).

## Qué cambió en la spec

| Dónde | Cambio | Por qué |
|---|---|---|
| design §1 | Hash 14b3cd5, líneas nuevas, sonda repetida (+ caso 2016), tabla de caminos | Estado actual |
| design §1.3 / §5 | Franquicia como quinto camino; F-060/F-062 explicados; F-038 | Features nuevas en sv5 |
| `DIAS_FUTURO` | 31 → **62** (DA10) | El día de ajuste de la franquicia va hasta ~30 días por delante de la línea; con 31, una línea anotada por adelantado dejaría su ajuste `no_editable` |
| design §4.2 | `por_fecha` aparte y `{**omisiones, **por_fecha}` a las reglas | Más simple que separar después para el WARNING de 2c |
| requirements | R5 amplía a racha/hermano; **R15** franquicia; R1 y ejemplos con 62 y hoy = 31/10 | Cobertura de F-056/F-060/F-062 |
| design §8 / tasks | Tests nuevos (`r3_racha_y_hermano`, `r15_franquicia[…]`); helpers de F-056/F-062 | Nombres actuales; T4/T7 los citan |
| design §9 | M1 con hoy + 62 y cifra «≈ 25» (M2 de F-054 descartada); M2 aclara 2717792; **M2b** opcional | El recurso de pruebas es también el gruista de F-056 (campo 0): M2 no lee ni escribe nada por él, no le afecta |
| design §11 | DA8 superada; DA10 y DA11 nuevas | — |
| `features.json` | Descripción y aceptación de F-055 (62 días, franquicia, DA1–DA11) | Coherencia; `BACKLOG.md` regenerado |

Tamaños: requirements 106/150, design 249/250 (`python -m harness.tamano --feature F-055` en
verde).

## Decisiones abiertas finales (las aprueba el humano)

| DA | Pregunta | Recomendación |
|---|---|---|
| DA1 | Dónde va la guarda | **A**: paso 2a de `preparar` (sigue siendo el punto único, ahora de cinco caminos) |
| DA2 | Qué es «fecha válida» | **B**: del calendario y entre 01/01/2026 y hoy + N días (N en DA10) |
| DA3 | ¿Cambia sv4? | **A**: no |
| DA4 | `fecha_int` nulo | **B**: opcional en el dominio y en `LineaIn` (sin 422) |
| DA5 | Líneas sin obra | **A**: fuera (ya fallan cerradas) |
| DA6 | Límites | **A**: constantes en `fecha_linea.py` |
| DA7 | `azure-apps` y `porcentajes` | **A**: motivo en `partes.md` + nota a `porcentajes` |
| DA8 | Sitio en la cola | **Superada**: F-055 ya es prioridad 4 y la siguiente de la cola |
| DA9 | Rigor | **A**: crítico |
| **DA10** (nueva) | Margen futuro con la franquicia | **A**: `DIAS_FUTURO` = 62 (B: 31 y ajustes futuros `no_editable`; C: 31 con excepción para la franquicia) |
| **DA11** (nueva) | Franquicia con fecha no válida | **A**: le basta `preparar` (`no_editable`, nada escrito; sus lecturas siguen), sin tocar F-056 (B: validar en `FranquiciaPipeline` antes de leer) |
