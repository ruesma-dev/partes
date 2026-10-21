<!-- specs/F-054-sin-obra-o-fecha-a-revision/requirements.md -->
# F-054 · Un parte sin obra o sin fecha leídas va siempre a revisión — Requisitos

**Servicio tocado: solo sv3** (`persist_parte_pipeline.py`: el cálculo de `review_required`
y un WARNING). Sin esquema, sin colas, sin cambios en sv4 ni en sv5 (DA4, DA5). Rigor
**estándar** (DA7): no escribe en Sigrid ni toca nada compartido.

**Petición del humano del 2026-10-21** («2 si») a la propuesta del líder: «abro una feature
pequeña para que un parte sin obra o sin fecha vaya siempre a revisión».

## Contexto (lo que hay en `dev` 206354d; detalle en `design.md` §1)

Hallazgo del líder el 2026-10-21 (solo lectura en producción): las dos páginas de un escaneo
de hoy llegaron con la **cabecera vacía** (`fecha`, `obra_numero` y `empresa_membrete` a
`null`) pero con 4 y 6 trabajadores casados y la firma marcada, y se guardaron con
`review_required = false`, `obra_match_method = 'none'` y `obra_ide`, `obra_codigo` y
`fecha_int` a NULL. `_compute_review_required` (sv3, l. 376) manda a revisión sin registros,
sin firma, con la obra en `OBRA_A_REVISAR` (F-023), con lectura dudosa (F-051) o con algún
trabajador u hora sin casar, pero **no** con la obra sin casar por `none` ni sin fecha.

En el portal, `review_required` es la etiqueta «Revisar» del listado `/partes` y «Requiere
revision» del detalle; no bloquea aprobar ni dice el motivo. El detalle ya permite poner la
fecha (F-043) y la obra (`PATCH /api/partes/{id}/obra`).

## Glosario

- **Sin obra**: el parte no tiene obra casada, `parte.obra.ide` es `None`. Hoy son los
  métodos `none`, `codigo_otra_empresa`, `codigo_ambiguo` y `nombre_ambiguo` (y cualquiera
  futuro que no case); con obra, `codigo`, `codigo_padded`, `codigo_membrete`,
  `codigo_trabajadores`, `codigo_nombre` y `nombre` (`design.md` §1.1).
- **Sin fecha**: `parte.fecha_int` es `None` o ≤ 0. Es lo que da `FechaParteResolver` si
  no lee día y mes o si la fecha no existe (`32/13/2026`, `15/10` sin año, `null`).
- **Motivo de cabecera**: `sin_obra` o `sin_fecha` (constantes `MOTIVO_SIN_OBRA` y
  `MOTIVO_SIN_FECHA` de sv3).

## Requisitos

### Revisión por la cabecera (sv3)

- **R1.** SI el parte no tiene obra casada (`obra.ide is None`), ENTONCES sv3 debe calcular
  `review_required = True`, sea cual sea `obra.method` (DA1).
- **R2.** SI el parte no tiene fecha (`fecha_int` `None` o ≤ 0), ENTONCES sv3 debe calcular
  `review_required = True` (DA2).
- **R3.** La función pura `motivos_cabecera(parte)` debe devolver, en este orden y sin
  repetir, `("sin_obra",)`, `("sin_fecha",)`, `("sin_obra", "sin_fecha")` o `()`, y
  `_compute_review_required` debe dar `True` siempre que no esté vacía.
- **R4.** Un parte con obra casada por cualquiera de los seis métodos con obra, con fecha,
  firmado, con registros, sin lectura dudosa y con trabajadores y horas casados (el casado
  por recurso de F-030 cuenta como casado) debe seguir con `review_required = False`.
- **R5.** Las demás causas de revisión no deben cambiar: sin registros, sin firma, lectura
  dudosa (F-051), trabajador sin casar, hora de un registro de horas sin resolver.
- **R6.** La constante `OBRA_A_REVISAR` debe desaparecer: R1 la contiene (DA1) y un control
  que ya no decide nada sería un mutante superviviente.

### Lo que se ve (sv3, log)

- **R7.** CUANDO sv3 guarda un parte con algún motivo de cabecera, debe registrar un
  WARNING con `document_id`, los motivos, `obra_match_method` y el número de obra leído, y
  sin nombres ni DNIs (DA4). Sin motivos de cabecera, ese WARNING no sale.
- **R8.** El portal no cambia (DA4): el motivo se ve porque la fecha sale vacía y la obra
  «—» o «Leido: X (sin casar)», como hoy.

### Ingesta completa (sv3)

- **R9.** CUANDO llega el payload del hallazgo (cabecera con `fecha`, `obra_numero` y
  `empresa_membrete` a `null`, firma marcada y trabajadores con horas), sv3 debe guardar el
  documento con `review_required = True`, `fecha_int` NULL y `obra_ide` NULL, aunque todos
  los trabajadores casen.
- **R10.** El resto de la ingesta no cambia: el casado sigue usando «hoy» como fecha de
  referencia sin fecha (F-023 R16), el dedup por `sha256` y el reemplazo del mismo día y
  obra (que sin fecha u obra no desactiva nada) siguen igual, y los conciliadores no tocan
  `review_required` salvo con `marcar_review_required` (F-003, F-023), que solo sube.

### Alcance en el tiempo y datos ya guardados

- **R11.** F-054 solo cambia las ingestas nuevas: ni sv3 ni sv4 recalculan
  `review_required` de lo ya guardado, y poner obra o fecha en el portal no baja la
  bandera (como hoy).
- **R12.** Los documentos ya guardados se miden con **M1** (solo lectura en la base `partes`)
  y, si el humano aprueba DA3 = B, se corrigen con **M2**: un `UPDATE` único que solo **sube**
  `review_required` en los activos, no aprobados, sin obra o sin fecha (`design.md` §8). Nada
  a nivel de servidor del PostgreSQL compartido.

### Documentación

- **R13.** `docs/ARCHITECTURE.md` debe ganar la semántica 18 (parte sin obra o sin fecha a
  revisión, solo ingestas nuevas, sin cambios en el portal) y el docstring de cabecera de
  `persist_parte_pipeline.py` (paso 5) debe nombrar las causas nuevas.

## Ejemplos (detalle y origen en `design.md` §6)

| Caso | Obra | Fecha | Hoy | F-054 |
|---|---|---|---|---|
| Hallazgo: cabecera vacía, 4 trabajadores casados, firmado | `none`, sin ide | `None` | `False` | `True` (`sin_obra`, `sin_fecha`) |
| Obra leída «672» que no existe en Sigrid | `none`, sin ide | 20261020 | `False` | `True` (`sin_obra`) |
| Código de dos empresas sin membrete ni discriminante | `codigo_ambiguo` | 20261020 | `True` | `True` (`sin_obra`) |
| Fecha «32/13/2026» o «15/10» (sin año) | `codigo` | `None` | `False` | `True` (`sin_fecha`) |
| Año futuro «15/10/2027», corregido a 2026 | `codigo` | 20261015 | `False` | `False` (DA2) |
| Todo casado y firmado | `codigo_padded` | 20261020 | `False` | `False` |
| Sigrid sin cablear (local) | `none`, sin ide | 20261020 | `True` (trabajadores) | `True` |

## Fuera de alcance

- Bloquear la aprobación o el envío a sv5 de las líneas sin obra o sin fecha (DA5: hoy una
  línea sin fecha viaja con `fecha_int = 0` y sv5 no la rechaza; se propone feature aparte).
- Guardar o enseñar en el portal los motivos de revisión (DA4 B/C).
- Revisar fechas corregidas o lejanas (`futuro_corregido`, `leido_pasado`: DA2 B/C).
- Bajar `review_required` cuando el usuario arregla la obra o la fecha.
