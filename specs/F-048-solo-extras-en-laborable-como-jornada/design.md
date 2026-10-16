<!-- specs/F-048-solo-extras-en-laborable-como-jornada/design.md -->
# F-048 · Ordinarias + extras leídas en laborable siguen la regla de jornada — Diseño

## 1. Límite de servicio

- **sv3** (ingesta): el normalizador es el único sitio que ve la fila completa del papel
  (ordinarias y extras juntas). Sumarlas allí hace que todo lo de después —jornada del
  día (F-015), calendario, reparto ponderado (F-045), congelación (F-004/F-037) y
  reajuste (F-046)— las trate como lo que son: horas trabajadas de ese día.
- **sv4** solo: copia gemela del ORM (lista tolerada) y la etiqueta de traza (R22).
- **sv2 no** (DA1), **sv5 no**: un registro sumado es una `normal` con el código
  ordinario del recurso; sv5 la registra como cualquier otra. Nada fuera de la base `partes`.

## 2. Ficheros a crear

- `services/partes-persistencia/tests/test_f048_normalizer.py` — R1-R7 (normalizador puro).
- `services/partes-persistencia/tests/test_f048_conciliar.py` — R8-R18: JSON de sv2 ⇒
  `ParteNormalizer` ⇒ `save_parte` ⇒ `conciliar_todos` con el repositorio real sobre
  SQLite y los dobles de `tests/dobles.py` (calendario, lookup, `reshor`), como
  `test_f045_conciliar.py`. Datos sintéticos.
- `services/partes-persistencia/tests/test_f048_esquema.py` — R6, R24 (`ddl_complementario`
  y lectura/escritura de la columna).
- `services/partes-front/tests/test_f048_traza_portal.py` — R22-R23.

## 3. Ficheros a modificar

**sv3** (`services/partes-persistencia/`):
- `domain/models/parte_records.py`: `RegistroNormalizado.horas_extra_leidas:
  Optional[float] = None`.
- `application/services/parte_normalizer.py` (`normalize`, bloque de reparto por fila):
  - `suma = extra_pos > 0` (extras leídas > 0). Si `suma`: `ord_total = ord_pos +
    extra_pos`, y el reparto entre partidas de hoy se hace con `rem_ord = ord_total` y
    `rem_extra = 0` (sin `extra_parts`). La rama sin partidas emite un único `normal` de
    `ord_total`. Si no `suma`: el código de hoy, intacto (R3).
  - `horas_extra_leidas` de cada `normal` de la fila sumable: la parte del registro que
    cae más allá de las primeras `ord_pos` horas en el orden de emisión, es decir
    `max(0, min(h, acumulado_tras − ord_pos))`; `None` si sale 0 (R2).
  - `codigo_hora_propuesto = cod_ord` en todos los `normal` (R4; ya era así).
  - Contadores para el INFO final (R7). El comentario «Aquí se respetan las horas tal
    cual…» se reescribe: las extras leídas > 0 se suman a la ordinaria (F-048).
- `infrastructure/database/orm_models.py`: `horas_extra_leidas: Mapped[float | None] =
  mapped_column(Float)` tras `horas_orig`, con comentario «F-048: horas de esta línea que
  la IA leyó como extra y la ingesta sumó a la ordinaria; solo traza».
- `infrastructure/database/sqlalchemy_parte_repository.py` (`save_parte`):
  `horas_extra_leidas=reg.horas_extra_leidas`. `apply_extras_splits` no la copia al
  clon (la `extra_auto` nace con nula) y no cambia.

**sv4** (`services/partes-front/`):
- `infrastructure/database/orm_models.py`: el mismo cambio, byte a byte (gemelo F-010).
- `infrastructure/database/parte_repository.py`: `RegistroView.horas_extra_leidas:
  Optional[float] = None` y rellenarlo donde se construye (las vistas de obra y
  trabajador); el detalle de parte lee el ORM directamente.
- `templates/parte_detail.html`, `obra_detail.html`, `trabajador_detail.html`: junto a
  las etiquetas de método, `{% if r.horas_extra_leidas %}<span class="tag-auto"
  title="La IA leyó estas horas como extra; en la ingesta se suman a la jornada y el
  exceso sobre la jornada del día sale como extra (F-048)">incl. {{ … }} h extra
  leídas</span>{% endif %}` (formato de horas el de cada plantilla).

**Documentación**: `docs/ARCHITECTURE.md` (semántica 3, tras F-045: «F-048: la ingesta
suma las extras leídas a la ordinaria de su fila»), `docs/referencia/partes-proyecto.md`
(las dos menciones de «Cómputo de extras»), `azure-apps/partes.md` §3.3 (commit local).

## 4. Ficheros que NO se tocan

`recurso_conciliador.py`, `reparto_ponderado.py`, `pareja_extra.py`, `jornada_resolver.py`
(sv3 y sv4), `congelacion.py` (sv4), `tipo_hora_resolver.py`, `persist_parte_pipeline.py`,
`revert_extras_auto`, `apply_extras_splits`, sv2 (prompt y esquema), sv5, `static/`,
`infra/`.

## 5. Tests existentes que cambian

**Ninguno** (ningún test actual pasa extras > 0 por el normalizador; comprobado con
`grep extraordinarias` el 2026-10-15). Si alguno falla ⇒ parar y anotarlo.

**Enmienda (2026-10-15, decisión del humano «en f48 opcion A», tras el bloqueo de T1).**
La columna nueva obliga a tocar los guardianes que fijan las columnas de
`parte_registros` en 56 (están hechos para que quien añada una columna la declare):
`"horas_extra_leidas"` tras `"horas_orig"` en `COLUMNAS_PARTE_REGISTROS` y las cuentas
de 56 a 57, con mensajes y docstrings, en `tests/test_f010_orm_models_gemelos.py`
(`test_f010_r4_…_56_columnas`, `test_f010_r29_…` y `test_f019_r29_…`),
`tests/test_f015_r29_guardian_cinco_tablas.py` (`…_sigue_siendo_de_56`, que solo falla
al crecer la lista), `services/partes-persistencia/tests/test_f015_r18_orm_empleado_jornada.py`,
`…/test_f015_r21_hora_candef_intacto.py`,
`services/partes-front/tests/test_f015_r18_orm_empleado_jornada_sv4.py` y los dos de F-019
`services/partes-persistencia/tests/test_f019_orm_bandeja.py::test_f019_r29_sv3_…_56_columnas`
y `services/partes-front/tests/test_f019_bandeja.py::test_f019_r29_sv4_…_56_columnas`
(estos tres últimos no salieron en el bloqueo: aparecieron al aplicar A; mismo cambio). Los nombres de
las funciones no cambian (conservan la cuenta de su feature; el docstring lo dice).
Solo cambian cuentas y la lista: ninguna aserción de comportamiento.

## 6. Decisiones (con recomendación; las valida el humano en la PARADA 1)

- **DA1 · Dónde.** En la ingesta de sv3. No en el prompt de sv2: la IA leyó bien el
  papel (el encargado escribió en la columna de extras) y sv2 no conoce recurso, jornada
  ni calendario; cambiar el prompt perdería lo leído y dependería del modelo. No en el
  conciliador (ver DA2).
- **DA2 · Mecanismo: sumar en la ingesta (A, recomendado) o decidir en cada pasada (B).**
  - A: la fila sumable entra como una ordinaria con su trabajado, y `horas_extra_leidas`
    guarda lo leído. Todo lo existente funciona sin tocarlo: el reparto da J + exceso
    (caso 1 y 2 en dos líneas), F-037 congela base y `extra_auto` juntas y F-046 usa
    `horas_orig` = lo trabajado. La edición humana no necesita reglas nuevas (DA7).
  - B (la primera versión de esta spec): marcar las extras leídas y convertirlas en cada
    pasada según el día. Permite R14 literal y un umbral (DA4), pero el caso 2 exige que
    una extra explícita absorba el exceso de otra línea: un vínculo nuevo entre dos
    líneas que F-037 (pareja) y F-046 (ideal) no conocen, más columna de marca, reversión
    y reglas de edición en sv4. Mucho más riesgo para el mismo resultado en laborable.
- **DA3 · No laborable.** Con A, mismos importes que hoy pero una línea menos: 4 + 5 en
  sábado da `normal` 0 + `extra_auto` 9 (hoy `normal` 0 + `extra_auto` 4 + `extra` 5).
  Solo 10 extras da 0 + 10 (hoy una `extra` 10). Lo que viaja a Sigrid (sv5 omite las
  líneas sin horas) son las mismas horas extra con el mismo código del recurso.
- **DA4 · Sin umbral.** Toda fila sigue la regla de 8+x, también si no llega a J
  (4 + 2 ⇒ 8 + (−2), como decidió el humano; solo 6 extras ⇒ 8 + (−2), igual que 6
  ordinarias hoy). Riesgo: 2 extras sueltas tras una jornada que no viene en ningún parte
  saldrían 8 + (−6). Si el humano quiere el umbral para las filas solo extra, hace falta
  B para esas filas (no se puede decidir en la ingesta: allí no se conoce J).
- **DA5 · Por fila.** Inherente a A: una fila solo extra pesa y recibe jornada aunque el
  trabajador tenga ordinarias en otra obra (R17: mismos totales, coste repartido como pide
  F-045). Hoy esa obra no recibía jornada (F-045 R8).
- **DA6 · Sin retroactivo.** Solo ingestas nuevas. M1 cuenta lo que queda como hoy sin
  congelar; si son pocas, a mano en el portal; si son muchas, M5 (reingesta) con
  autorización. Lo **congelado** (caso 2, ya en Sigrid) se propone como feature aparte
  sobre la maquinaria de F-046: en Sigrid solo `UPDATE` (p. ej. `extra_auto` −4 ⇒ 0 y
  `extra` 5 ⇒ 1, o al revés), nunca borrar; una extra que queda a 0 se pone a 0.
- **DA7 · Edición humana.** Respetada como hoy: sv3 nunca cambia el tipo; si el humano
  quiere otra cosa, edita horas o tipo de la línea o crea una extra (`/extra`) y, como
  con cualquier ordinaria, el siguiente recálculo reparte lo que haya.
- **DA8 · Extras negativas leídas y ordinarias negativas.** Como hoy: la extra negativa
  no se suma (sigue explícita); ordinarias ≤ 0 cuentan 0 (ya se descartaban).
- **DA9 · Mensuales (MENC, sin código extra).** La ingesta no conoce el recurso: sus filas
  también se suman y, como el conciliador no reparte ese grupo, la `normal` queda con el
  trabajado. Sus horas no se registran por horas (se omiten, o van a dedicación con
  F-019), así que no cambia lo escrito en Sigrid; `horas_extra_leidas` guarda lo leído.
- **DA10 · Traza.** Columna `horas_extra_leidas` (no `hora_match_method`, que `_overwrite`
  pisa en cada pasada). Rigor **crítico** (nómina, coste, Sigrid, esquema compartido).

## 7. Ejemplos de la ingesta (R1-R2)

| Fila leída (ord / extra / partidas)   | Registros emitidos (`horas`, `horas_extra_leidas`) |
|---------------------------------------|----------------------------------------------------|
| null / 10 / —                         | `normal` (10, 10)                                  |
| 4 / 5 / —                             | `normal` (9, 5)                                    |
| 8 / 0 / —                             | `normal` (8, null) — como hoy                      |
| 8 / −2 / —                            | `normal` (8, null) + `extra` (−2, null) — como hoy |
| 4 / 5 / P1 con 6 h, P2 abierta        | `normal` P1 (6, 2) + `normal` P2 (3, 3)            |
| null / 6 / P1 con 2 h, P2 con 4 h     | `normal` P1 (2, 2) + `normal` P2 (4, 4)            |

## 8. Solapes y orden con F-046 y F-047

- **Orden recomendado: F-046 y F-047 primero** (T0 fusiona `dev`). Con A los conflictos
  son pequeños: F-046 añade una tabla a las dos copias de `orm_models.py` (F-048 una
  columna) y F-047 cambia la firma de `save_parte` (F-048 una línea en el constructor de
  `ParteRegistroOrm`). Ni el conciliador ni `reparto_ponderado.py` se tocan aquí.
- **F-046**: un registro sumado es una base normal; su `horas_orig` es lo trabajado y su
  extra, una `extra_auto`: el ideal y el reajuste de F-046 lo tratan sin cambios. Con B
  habría que enseñar a F-046 la «extra absorbente» (DA2).
- **F-047**: la ingesta sigue guardando y luego conciliando; el «procesando…» cubre el
  reparto del registro sumado como el de cualquier ordinaria.

## 9. Verificación manual (humano)

- **M1 · antes de desplegar (solo lectura, base `partes`)**: filas que se quedan como
  hoy sin congelar (extras explícitas > 0 de la IA en partes activos no aprobados):
  ```sql
  SELECT (EXISTS (SELECT 1 FROM parte_registros n
            WHERE n.document_id = r.document_id AND NOT n.extra_auto
              AND n.empleado_line_no IS NOT DISTINCT FROM r.empleado_line_no
              AND coalesce(n.tipo_hora, '') IN ('', 'normal'))) AS con_ordinaria,
         count(*) AS lineas, count(DISTINCT r.document_id) AS partes,
         round(sum(r.horas)::numeric, 2) AS horas
  FROM parte_registros r JOIN parte_documents d ON d.id = r.document_id
  WHERE d.is_active AND NOT coalesce(d.approved, false)
    AND r.deleted_at_utc IS NULL AND r.tipo_hora = 'extra'
    AND NOT r.extra_auto AND NOT coalesce(r.es_incidencia, false) AND r.horas > 0
    AND coalesce(r.sigrid_estado, '') NOT IN ('encolado', 'registrado', 'dedicacion')
  GROUP BY 1;
  ```
  Aproximada: incluye extras creadas a mano en sv4 y no distingue festivos.
- **Despliegue**: sv3 y sv4 (los dos aplican `ddl_complementario`; cualquier orden vale).
- **M2 · columna**: `SELECT data_type, is_nullable FROM information_schema.columns WHERE
  table_name = 'parte_registros' AND column_name = 'horas_extra_leidas';` ⇒ `double
  precision`, `YES`.
- **M3 · Log Analytics** (`ca-sv3-persistencia`): `Log_s has 'filas_extra_sumadas'`
  (ingesta) y `Log_s has 'reparto'` (F-045) en el mismo documento.
- **M4 · Primer caso real**: el siguiente parte con extras leídas en laborable ⇒ en el
  portal, `normal` J con la etiqueta «incl. X h extra leídas» y su `extra_auto`:
  `SELECT tipo_hora, horas, horas_orig, horas_extra_leidas, extra_auto FROM
  parte_registros WHERE document_id = '<id>' ORDER BY line_index, extra_auto;`
- **M5 · Opcional, solo con autorización expresa**: reingestar partes sin congelar de M1
  (borrar el parte en el portal y volver a enviar el PDF), uno a uno.

## 10. Riesgos

- **DA4**: sin umbral, extras sueltas de quien no trae su jornada en ningún parte salen
  con extra negativa grande. Se ve en el portal (etiqueta) y en el aviso de jornada.
- **DA3**: en no laborable cambia la forma (una línea menos), no los importes.
- **DA5**: días mixtos ya «bien» hoy cambian de reparto entre obras, no de totales.
- **F-025**: con incidencia parcial el aviso «incidencia + extra > 0» depende ahora del
  exceso sobre J y no de la columna leída.
- **Partidas**: el reparto de una fila entre partidas no cambia de orden; solo deja de
  separar ordinaria y extra dentro de cada partida (§7).
