<!-- progress/spec_F-054.md -->
# spec-author · F-054 · Un parte sin obra o sin fecha va siempre a revisión (2026-10-21)

Spec en `specs/F-054-sin-obra-o-fecha-a-revision/` (rama
`feature/F-054-sin-obra-o-fecha-a-revision` desde `dev` 206354d, worktree
`C:\Users\pgris\PycharmProjects\partes-wt-f054`). `F-054` estaba libre: el último id de
`harness/features.json` en `dev` es F-053 y no hay rama `feature/F-054*`. Topes: requirements
108/150, design 224/250. `features.json`: F-054 `spec_ready`, prioridad **2** (DA6 A), rigor
`estandar` (DA7 A), sin renumerar ninguna otra.

## Qué hace

- **Solo sv3** (`persist_parte_pipeline.py`): función pura `motivos_cabecera(parte)` →
  `sin_obra` si `obra.ide is None` (sea cual sea el método) y `sin_fecha` si `fecha_int` es
  `None` o ≤ 0. `_compute_review_required` la usa en lugar de `OBRA_A_REVISAR`, que se borra
  (ya queda contenida). WARNING en `run` con `document_id`, motivos, método y obra leída, sin
  nombres ni DNIs. Sin esquema, sin colas, sin sv4 ni sv5. Solo ingestas nuevas.

## Hallazgos

1. **Métodos de obra**: con obra, `codigo`, `codigo_padded`, `codigo_membrete`,
   `codigo_trabajadores`, `codigo_nombre`, `nombre`; sin obra, `none` (también el defecto si
   Sigrid no está cableado), `codigo_otra_empresa`, `codigo_ambiguo`, `nombre_ambiguo`. sv4
   escribe `manual` al cambiar la obra. Ningún «sin obra» lleva `ide` ⇒ DA1 A.
2. **Fecha**: el resolver da `fecha_int = None` sin día y mes o con fecha imposible. Su método
   (`futuro_corregido`, `leido_pasado`…) no llega a `ParteDocumento`.
3. **Portal**: `review_required` solo pinta «Revisar» (listado) y «Requiere revision»
   (detalle); no bloquea aprobar y no hay motivos. Sin obra ⇒ grupo `sin-obra` en `/obras`;
   sin fecha ⇒ fuera de la matriz. El detalle permite poner fecha (F-043) y obra
   (`PATCH …/obra`), y ninguno toca la bandera.
4. **sv5**: sin obra ⇒ `RuntimeError` «obra no encontrada» (error, no escribe; en modo
   pruebas va a la 0404). **Sin fecha ⇒ viaja con `fecha_int = 0`** (`int(r.fecha_int or 0)`
   en sv4) y sv5 lo acepta: no hay guarda en ningún lado. Fuera de F-054 (DA5): se propone
   feature aparte en la que sv5 omita la línea; urgente si M1(b) da líneas sin fecha enviadas.
5. **Sonda** (aplicada y revertida, árbol limpio): con la regla, fallan 4 de 2.254 tests de
   sv3 (3 casos de `test_f030_r13_…` y `test_f051_r17_…`) por partes de prueba sin obra o sin
   fecha; quitar `OBRA_A_REVISAR` rompe además 3 casos de `test_f023`. Las enmiendas son de
   fixtures (neutras) salvo la de `test_f023` (`("none", False)` → `True`), que es la fase RED.
6. Reproducido hoy en SQLite con el doble de `test_f036`: cabecera vacía + trabajador casado
   ⇒ `review_required False`, `obra_ide`/`fecha_int` NULL, método `none` (lo que vio el líder).
7. Gemelos: `_compute_review_required` no tiene copia en sv4 ni está en la lista cerrada.

## Decisiones abiertas para el humano (`design.md` §9)

| DA | Recomendación |
|---|---|
| DA1 «sin obra» | A: `obra.ide is None`; `OBRA_A_REVISAR` desaparece |
| DA2 «sin fecha» | A: `fecha_int` nulo o ≤ 0 (año futuro corregido y fechas lejanas, fuera) |
| DA3 lo ya guardado | B: M2, `UPDATE` único manual que solo sube la bandera (activos no aprobados), tras M1 |
| DA4 motivo visible | A: WARNING en sv3; portal sin cambios |
| DA5 guarda aguas abajo | A: fuera; feature nueva «sv5 omite líneas sin fecha válida» (rigor crítico) |
| DA6 cola | A: prioridad 2, delante de F-014 (3, bloqueada) y F-049 (4) |
| DA7 rigor | A: `estandar` |

## Verificaciones manuales (`design.md` §8)

- **M1** (solo lectura, `PGOPTIONS` read-only): documentos activos sin obra o sin fecha por
  aprobado/revisión/método, y líneas sin obra o sin fecha por `sigrid_estado`. Puede hacerse
  antes de aprobar la spec: decide DA3 y la urgencia de DA5.
- **M2** (DA3 = B; escritura en la base `partes`, autorización expresa; tras desplegar sv3).
- **M3** tras unos días: ningún documento nuevo sin obra o sin fecha sin revisar.

## Estado

`bash harness/init.sh` en verde. Un commit local en la rama; sin push.

## Aprobación (2026-10-21)

Humano, 2026-10-21, literal: «apruebo F-054 y la DA5» ⇒ **DA1–DA7 APROBADAS con la
recomendación** (A en todas salvo DA3 = B), anotado en `design.md` §9. DA5 = A: la guarda aguas
abajo se especifica en **F-055** («sv5 omite las líneas sin fecha válida», rama propia).

- **M1 hecha por el líder el 2026-10-21** (solo lectura; resultado en `design.md` §8): 3
  documentos activos no aprobados y sin revisar sin obra o sin fecha (los 2 del 2026-10-21 y
  uno del 2026-10-14 con obra y sin fecha) ⇒ M2 afectará a 3. Las 25 líneas sin obra o sin
  fecha tienen `sigrid_estado` vacío: ninguna llegó a Sigrid, F-055 no es urgente. T7 marcada.
- **Cola**: DA6 se aprobó con prioridad 2, pero F-049 está `in_progress` desde hoy («lanza
  f49») y solo cabe una. F-054 pasa a **prioridad 4**, la misma que F-049: el backlog desempata
  por id, así que sale F-049 → F-054 → F-047 (5) sin renumerar ninguna otra.
- Estado `spec_ready`. Topes: design 235/250, requirements 108/150.

