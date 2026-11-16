# Exploración · bug «deshacer un cambio de fecha deja líneas con `fecha_int` NULL»

- **Fecha**: 2026-11-16. **Rama**: `dev` (3aa1346). **Alcance**: SOLO LECTURA (código + `SELECT`
  sobre la base `partes` de producción en `psql-albaranes-rs9k2`, sesión con
  `default_transaction_read_only=on`; credencial leída del Key Vault de partes, sin escribirla en
  ningún sitio). Nada escrito en la base, en Sigrid ni en el repo salvo este fichero.
- **Documento**: `5ea328f7-dbf3-4f12-b6b8-dee1cca7d093` (obra 0692).

## 1. Causa (código)

**El deshacer de una acción de cabecera (`parte_fecha`) se aplica a medias cuando el documento
está congelado pero algunas de sus líneas no.** La entrada de deshacer guarda a la vez el snapshot
del documento y los de sus líneas, pero `undo_last` decide la congelación de cada snapshot por
separado y con criterios distintos:

- `services/partes-front/infrastructure/database/parte_repository.py:3755-3762` — snapshot de
  documento: se omite si `_motivo_congelado_doc(doc)` no es None. Ese motivo
  (`application/services/congelacion.py:148-167`, `motivo_congelacion_documento`) congela el
  documento entero en cuanto **una** línea (incluso en papelera) está `registrado` / `encolado` /
  `dedicacion`.
- `parte_repository.py:3763-3771` — snapshots de línea: se omiten solo si **esa** línea está
  congelada (`_motivo_congelado_reg` → `congelacion.py:126-145`: `encolado`, `registrado`,
  `dedicacion` o documento aprobado). Una línea `omitido` (o sin estado) de un parte desaprobado
  **no** está congelada y se restaura.
- `parte_repository.py:764-768` (`_apply_reg_snapshot`) restaura `fecha` y `fecha_int` del snapshot
  (`_REG_UNDO_FIELDS`, `parte_repository.py:740-750`). Si el parte nació sin fecha (`? → fecha`),
  el valor anterior es NULL/NULL.

Resultado: el documento conserva la fecha nueva y las líneas libres vuelven a `fecha`/`fecha_int`
NULL. Es la aplicación literal de F-004 R9 («omitir esos snapshots, aplicar el resto»), que vale
para acciones por línea pero rompe la atomicidad de una acción de cabecera: la acción directa
`update_parte_fecha` (`parte_repository.py:4022`, `_exigir_doc_editable`) rechazaría entero ese
mismo cambio, pero su inversa lo aplica parcialmente.

Agravante en la ruta: `undo_last` devuelve en `document_ids` los ids de **todos** los snapshots de
documento, también los omitidos (`parte_repository.py:3793-3794`), y `undo_apply`
(`interface_adapters/web/app.py:1749-1758`, F-042 R7) pide el recálculo de sv3 sobre ese estado
incoherente. sv3 agrupa por `(recurso, fecha_int)`
(`services/partes-persistencia/application/services/recurso_conciliador.py:704-712`), así que las
líneas a NULL forman su propio «día» `None`, separado de la extra ya registrada del día real, y
genera una extra automática nueva sin fecha.

Nota sobre el síntoma anotado: en este caso las líneas tienen **`fecha` y `fecha_int` NULL las dos**
(no «fecha no nula»); lo que sí tiene fecha es el **documento**. El desajuste es documento ↔ líneas.

`parte_obra` (`update_parte_obra`, `parte_repository.py:4040-4094`) tiene la misma forma
(snapshot de documento + líneas) y por tanto el mismo defecto latente: deshacer un cambio de obra
en un parte con una línea registrada dejaría líneas libres con la obra vieja y el documento con la
nueva.

## 2. Confirmación en producción (solo `SELECT`)

Documento: `fecha = 2026-11-05`, `fecha_int = 20261105`, `approved = false`
(`approved_at_utc` NULL: se aprobó y luego se desaprobó), `is_active = true`, creado
2026-11-11 14:11 UTC; último recálculo pedido 2026-11-12 08:16:26 y terminado 08:17:33.

Líneas:

| id | line_index | fecha | fecha_int | tipo | horas (orig) | extra_auto | sigrid_estado |
|---|---|---|---|---|---|---|---|
| 21344 | 0 | NULL | NULL | normal | 9 | no | omitido (recurso sin código de hora extra) |
| 21345 | 1 | NULL | NULL | normal | 8 (10) | no | omitido (recurso mensual: solo extras) |
| 22597 | 1 | 2026-11-05 | 20261105 | extra | 2 | sí | **registrado** (con parte y `hmores`) |
| 24433 | 1 | NULL | NULL | extra | 2 | sí | — (pendiente) |

`undo_log` 216 (`parte_fecha`, 2026-11-11 16:27:52, «? → 2026-11-05», `undone = true`). Su payload:
documento con `fecha`/`fecha_int` NULL y líneas 22554, 21344, 21345 con `fecha`/`fecha_int` NULL.

Cronología reconstruida:

1. 14:11 sv3 guarda el parte sin fecha leída (doc y líneas NULL).
2. 16:27 el usuario fija la fecha 2026-11-05 (entrada 216). Recálculo F-042: la extra automática
   22554 se sustituye por la 22597 (ya con fecha).
3. 16:30 se aprueba y sv5 registra la 22597; 21344 y 21345 quedan `omitido`. Después se desaprueba.
4. 2026-11-12 ~08:16 se deshace la 216: el documento se **omite** (congelado por la 22597
   registrada), la 22554 ya no existe, la 21344 y la 21345 (no congeladas) vuelven a NULL. Se pide
   el recálculo igualmente (pedido 08:16:26).
5. 08:17 sv3 recalcula el grupo `(recurso, None)` y crea la extra automática 24433 (2 h, sin fecha),
   **además** de la 22597 registrada (2 h, 2026-11-05) del mismo trabajador y misma línea.

Recuento en toda la base:

- Líneas con `fecha` no nula y `fecha_int` NULL: **0**.
- Líneas con `fecha_int` NULL: **22**, todas también con `fecha` NULL, todas en documentos activos,
  ninguna en papelera, **ninguna `registrado`/`encolado`** y ningún documento aprobado
  (20 sin estado, 2 `omitido`). Repartidas en 4 documentos: 3 que nacieron sin fecha (documento
  también NULL, caso legítimo: 9 + 6 + 4 líneas) y el `5ea328f7` (3 líneas).
- Líneas cuya `fecha`/`fecha_int` difiere de la de su documento: **3**, todas del `5ea328f7`
  (21344, 21345, 24433). Es el único caso del bug hoy.

## 3. Impacto de una línea con `fecha_int` NULL

- **Sigrid (sv5)**: no se escribe nada. F-055 omite la línea con `fecha_no_valida`
  (`services/partes-transfer/application/pipelines/registro_pipeline.py:252`,
  `application/services/fecha_linea.py:36`). Riesgo de escritura errónea: nulo, pero el parte
  queda «aprobado» con líneas que nunca viajan.
- **Recálculo de sv3**: las líneas sin fecha forman un día aparte `(recurso, None)`
  (`recurso_conciliador.py:712`); la jornada se calcula sin fecha real y no cuenta lo ya
  registrado del día verdadero. En el `5ea328f7` eso ha generado la extra duplicada 24433 junto a
  la 22597 registrada. La conciliación de recurso usa «hoy» en vez de la fecha
  (`recurso_conciliador.py:413`, también `medicion_casado.py:152,176`) para alta/empresa.
- **Portal (sv4)**: la cabecera enseña 2026-11-05 y las líneas no tienen día: no salen en el día
  correcto de las vistas por fecha (matriz/calendario por `fecha_int`), los avisos de calendario
  las ignoran (`app.py:2636-2644`) y la pareja base/extra se clave por `fecha_int`
  (`pareja_extra.py:31`).
- **No se puede arreglar desde el portal**: volver a guardar la fecha llama a `update_parte_fecha`,
  que exige el documento editable (`parte_repository.py:4022`) y lo rechaza (409) por la línea
  22597 registrada. El parte se queda atascado.

## 4. Propuesta de arreglo (solo propuesta)

**Servicio: sv4.** Fichero: `services/partes-front/infrastructure/database/parte_repository.py`
(`undo_last`), más tests en `services/partes-front/tests/`.

- Opción A (recomendada): en las entradas de cabecera (`parte_fecha`, `parte_obra`) el deshacer es
  **todo o nada**. Si algún snapshot de documento está hoy congelado, no se aplica ningún snapshot
  de esa entrada (ni documento ni líneas), la entrada no se marca `undone` (o se marca con aviso) y
  se responde con el motivo de congelación, igual que haría la acción directa. Simétrico con
  `_exigir_doc_editable` de `update_parte_fecha`/`update_parte_obra`.
- Opción B (alternativa): restaurar las líneas libres **siempre desde el documento** final (si el
  documento se omite, las líneas toman su `fecha`/`fecha_int`), es decir, no dejar nunca líneas
  distintas de su cabecera. Más compleja y con semántica menos clara; no la recomiendo.
- En ambos casos: `document_ids` de la respuesta solo con los documentos realmente restaurados, para
  no pedir recálculos sobre un deshacer omitido (`parte_repository.py:3793-3794`).
- Requiere spec (enmienda acotada de F-004 R9 para acciones de cabecera) y test que reproduzca:
  parte sin fecha → fijar fecha → registrar una línea → desaprobar → deshacer ⇒ ni documento ni
  líneas cambian.

**Reparar datos existentes** (proponer al humano; no ejecutado). Solo afecta al `5ea328f7`:

1. Poner `fecha = '2026-11-05'`, `fecha_int = 20261105` en las líneas 21344, 21345 (y 24433, o
   dejar que el recálculo la quite) para que coincidan con su documento.
2. Pedir un recálculo de sv3 de ese parte (con `fecha_int` correcta, la 24433 deberá desaparecer o
   absorberse porque la 22597 registrada ya cubre las 2 h extra; comprobar después que no queda una
   extra pendiente duplicada).

Como el portal no lo permite (409), la vía sería un `UPDATE` puntual en la base `partes`
autorizado expresamente por el humano, o un pequeño script de reparación; los otros 3 documentos
con `fecha_int` NULL son partes sin fecha leída (doc y líneas NULL) y no necesitan reparación por
este bug, solo que alguien les fije la fecha.
