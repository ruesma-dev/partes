<!-- specs/F-053-pisar-sin-borrar/design.md -->
# F-053 · Pisar sin borrar — Diseño

## 1. Encaje, límite de servicio, dependencia y hallazgos

- **sv5** es el único que escribe en Sigrid: la regla vive allí (sentencia, choques, motivos,
  resultado). **sv4** solo cambia textos y el nombre de un recuento. sv1–sv3, ORM, colas y
  esquema: sin cambios. Ninguna responsabilidad fuera de partes; no se propone servicio nuevo.
- **Lista cerrada de `CLAUDE.md`: no crece** (nada se duplica). `congelacion.py` es gemelo
  (F-024) por su **regla**; aquí solo cambia el texto de `MOTIVO_LINEA_REGISTRADA`, que sv3 no
  tiene, así que `recurso_conciliador.py` no se toca.
- **Sobre `dev` + F-034.** F-034 añade la guarda `EXISTS (SELECT 1 FROM con c WITH (UPDLOCK,
  HOLDLOCK) WHERE c.ide = … AND c.est = ?)` a toda sentencia sobre `hmores`, su R4 (`INSERT`
  de la línea de un pisado con `NOT EXISTS (… p.ide IN (<pisadas>) AND ISNULL(p.can, 0) <>
  0)`), la relectura tras escribir (R9–R12) y `application/services/parte_abierto.py`. F-053
  **sustituye** su `stmt_borrar_linea` con guarda por `stmt_anular_linea` y amplía su
  clasificación de no escritas. Sin F-034 en `dev`, F-053 no empieza.

Hallazgos en `dev` 4bda57e (`services/partes-transfer/` salvo indicación):

1. **Único `DELETE` de sv5 en ejecución**: `stmt_borrar_linea` (`sigrid_write_client.py`
   l.544–547), usado en el paso 9 (`registro_pipeline.py` l.531–538). El otro `DELETE` del
   servicio es la fase `limpiar` de `prueba_escritura_sigrid.py` (l.459–484): herramienta
   manual sancionada por `CLAUDE.md`, solo líneas `PRUEBA-IA` de la obra de pruebas (DA9).
2. **Qué se puede pisar hoy**: `_choques` (l.401–410) toma toda línea del mismo recurso, día
   y `horide` cuya synckey no sea de la petición: **manuales** (sin synckey), **ajenas**
   (`porcentajes:` u otras) y **otras líneas del portal** (`partes:<otro id>`). No mira `can`
   ni enlaces: hoy se borran líneas enlazadas a albarán, factura, dedicación o nómina.
3. **Una línea a 0 seguiría chocando**: con «poner a 0» y el `_choques` de hoy, cada pisada
   quedaría como conflicto eterno («0 h → 8 h») y, en un parte cerrado, provocaría
   `parte_cerrado` sin horas que proteger (F-031 R11). De ahí R5.
4. **Incidencias** (semántica 4, `can = 0`): pisar una incidencia hoy la borra y escribe la
   nueva; ponerla a 0 no hace nada y F-034 R4 dejaría entrar la nueva ⇒ dos `CIV` el mismo día.
   De ahí R6.
5. **F-024** (`comprobacion_lineas.py`): una `partes:<id>` a 0 sigue `presente` (su synckey
   existe) con la diferencia de horas; ya no pasaría a `borrado_sigrid`. Es correcto: la línea
   está, con 0 h. F-052 la clasifica `anulada_en_sigrid` (portal con horas, Sigrid 0) y ofrece
   `traer_de_sigrid`. sv3 y sv4 no leen `hmores`: nada más cambia en sus vistas.
6. **Asiento analítico** (F-021/F-031): Σ `tot` por `caaide`; una pisada a 0 aporta 0, como
   borrada. En un parte cerrado no se pisa (F-031 R11 + guarda de F-034).
7. **`porcentajes`**: `dedicacion-transfer` tiene el mismo `stmt_borrar_linea`
   (`sigrid_write_client.py` l.743–744, usado en `registro_pipeline.py` l.852 y en su
   `prueba_escritura_porcentajes.py` l.223). No se toca su repositorio: aviso en §10.

## 2. Ficheros

**Crear (sv5)**
- `application/services/pisado.py` (application, puro; §5).
- `tests/test_f053_cliente_anular.py`, `tests/test_f053_pisado.py`,
  `tests/test_f053_pipeline_pisado.py`.

**Crear (sv4)**: `tests/test_f053_textos_pisado.py`.

**Modificar (sv5)**
- `infrastructure/sigrid/sigrid_write_client.py`: `stmt_anular_linea` (§4); se **elimina**
  `stmt_borrar_linea`; `lineas_existentes` lee `enlazada` (R9); docstring del módulo.
- `application/pipelines/registro_pipeline.py`: `_choques` delega en `pisado.choques`;
  paso 7 con las omisiones de R6–R8; paso 9 con `stmt_anular_linea`; relectura de F-034 con
  `anuladas` y `pisada_no_anulada`; docstring (pasos 7 y 9).
- `domain/models/registro_models.py`: `ResultadoRegistro.borradas` → `anuladas`; docstring de
  `Conflicto` («se pondrían a 0»).
- `interface_adapters/resultado_json.py`: clave `anuladas` (DA7).
- `application/services/parte_abierto.py` (de F-034): `MOTIVO_PISADA_NO_ANULADA` y la
  elección de motivo de §5.3, sin tocar sus motivos de F-034.
- `tests/dobles.py` (`SigridFake`): §7. Tests que fijan lo que cambia (§8): se amplían a lo
  nuevo, nunca se relajan; cada enmienda, citada en el informe.

**Modificar (sv4)**
- `static/app.js`: `conflictosHtml` y `resultadoHtml` (§6).
- `application/services/reparto_obras.py`: `plano["anuladas"]` (l.142–145).
- `application/services/congelacion.py`: solo el texto `MOTIVO_LINEA_REGISTRADA` (DA8).
- `infrastructure/transfer/transfer_queue_publisher.py` (docstring l.14) e
  `interface_adapters/web/app.py` (comentario l.2691): «pisar pone a 0 líneas de Sigrid».

**Documentación**: `docs/ARCHITECTURE.md` y `azure-apps/partes.md` (§10; commit local allí).

**NO se tocan**: `comprobacion_lineas.py` (R16), `estado_parte.py`, `cuenta_analitica.py` y
`stmts_crear_parte` (copias de `porcentajes`), `reajuste_pipeline.py`, `reajuste_lineas.py`,
`reglas_registro.py`, `prueba_escritura_sigrid.py` (DA9), `transfer_consumer.py`, la regla de
`congelacion.py` y `recurso_conciliador.py` (sv3), plantillas (el aviso «se borraron allí»
describe lo que hizo Administración y sigue siendo cierto), ORM, sv1–sv3, repo `porcentajes`.

## 3. Flujo (paso 7 y paso 9, bajo el lock de siempre)

```
paso 7, por línea a escribir del grupo (orden R8):
  choques en parte cerrado            -> omitir parte_cerrado         (F-031 R11, ahora con R5)
  es incidencia y choques abiertos    -> omitir incidencia_en_sigrid  (R6)
  algún choque abierto enlazado       -> omitir linea_enlazada        (R7)
  choques abiertos                    -> Conflicto (confirmable, como hoy)
paso 9: por conflicto confirmado y pisada -> stmt_anular_linea(pisada)  (R1, R2)
        insert de la nueva con pisadas=…  (F-034 R4, sin cambios)
relectura (F-034): anuladas = pisadas sin horas; no escritas con pisada viva -> pisada_no_anulada
```

## 4. SQL (sv5, infraestructura: `SigridWriteClient`)

```python
def stmt_anular_linea(self, *, ide: int, reside: int, fecha_int: int,
                      horide: int | None, antes: float | None) -> dict:
    return {"sql": (
        "UPDATE hmores SET can = 0, tot = 0 WHERE ide = ? AND reside = ? "
        "AND fec = ? AND ISNULL(horide, 0) = ? AND ABS(ISNULL(can, 0) - ?) <= 0.001 "
        + self._sin_enlaces() + " AND "
        + self._guarda_parte_abierto("hmores.hmoide")),        # F-034
        "parameters": [int(ide), int(reside), int(fecha_int), int(horide or 0),
                       float(antes or 0), self._est]}
```

- Patrón de `stmt_actualizar_linea` (F-046): `WHERE` optimista (DA12) con lo que hizo
  chocar a la línea, sin enlaces (`_sin_enlaces()` ya existe) y parte abierto.
- `tot = 0` literal (no `ROUND(0 × pre)`): mismo resultado, sin depender de `pre` nulo.
- Solo `can` y `tot` (DA1): ni `synckey`, ni `tex`, ni nada más (R3).
- `lineas_existentes`: añade `CASE WHEN <enlaces> THEN 1 ELSE 0 END AS enlazada` (la misma
  expresión que `lineas_para_reajuste`, extraída a un helper `_expr_enlazada()` que usan las
  dos) y rellena `LineaSigrid.enlazada` (campo de F-046, ya existe).
- Se elimina `stmt_borrar_linea`: el cliente queda sin `DELETE` (R4); el test de F-034 «un
  solo `DELETE` en el cliente» se endurece a «ninguno».

## 5. Módulo puro `application/services/pisado.py` (imports solo de `domain`)

```python
MOTIVO_INCIDENCIA_EN_SIGRID = "incidencia_en_sigrid"
MOTIVO_LINEA_ENLAZADA = "linea_enlazada"
def tiene_horas(ls: LineaSigrid) -> bool: ...            # can no nulo y != 0
def es_incidencia(hora_codigo: str | None) -> bool: ...  # empieza por "CI"
def choques(lineas, accion: AccionLinea, mias: set[str]) -> list[LineaSigrid]: ...
def origen_linea(synckey: str | None) -> str: ...        # "partes" | "ajena" | "manual"
def motivo_incidencia_en_sigrid(ides: Sequence[int], parte_cod: str | None) -> str: ...
def motivo_linea_enlazada(ides: Sequence[int], parte_cod: str | None) -> str: ...
```

1. `choques`: mismo recurso, día y `horide`, synckey fuera de `mias` (como hoy) **y**
   (`es_incidencia(accion.hora_codigo)` **o** `tiene_horas(ls)`) (R5).
2. `_evaluar`, paso 7: la omisión por parte cerrado no cambia salvo que usa `choques`; tras
   ella, para cada línea con choques en partes abiertos, R6 y R7 por ese orden (helper
   `_omitir(a, motivo)`, que generaliza `_omitir_por_cerrado`: acción `omitir` y sin cuenta);
   el resto, `_conflictos` como hoy.
3. Relectura (F-034 §4.5): para una no escrita, si el parte que lo impidió está cerrado, F-034
   (`parte_no_abierto`); si no y tiene pisadas vivas (con horas) en partes abiertos,
   `motivo_pisada_no_anulada(ides, cod)` (en `parte_abierto.py`) + WARNING `[registro] pisada
   no anulada` (obra, periodo, `ide`, `registro_id`); si no, `no_escrita` de F-034.
4. `anuladas` = pisadas releídas por `ide` (`lineas_por_ide`, ya en la relectura de F-034)
   sin horas o ausentes. INFO de R13 por cada una, con `origen_linea`.

## 6. Textos (DA3 de F-034: sin tildes como el resto de motivos de sv5; ≤ 255)

- `incidencia_en_sigrid: la incidencia ya consta en Sigrid ese dia (linea 9001 del parte
  PT26/00314); no se duplica`.
- `linea_enlazada: la linea 9001 del parte PT26/00314 tiene ese dia las mismas horas y esta
  enlazada (albaran, factura, dedicacion o nomina); no se pone a 0. Corrigela en Sigrid`.
- `pisada_no_anulada: la linea 9001 del parte PT26/00314 cambio antes de ponerla a 0; no se
  registra. Vuelve a aprobar para revisar el conflicto`.
- **sv4, modal** (`conflictosHtml`): «Marca las que quieras **pisar**: la linea actual **se
  pone a 0 en Sigrid** (no se borra) y se escribe la nueva. Las lineas con OTRO codigo de ese
  dia no se tocan.»; cada pisada «linea N · HN · 8 h · 120 € → 0 h» y, al lado, «nueva: X h ·
  Y €» (hoy «actualizacion a …»).
- **sv4, resultado**: `if (r.anuladas)` «N linea(s) anteriores puestas a 0 en Sigrid
  (pisadas).», escapado con `esc`.
- **`MOTIVO_LINEA_REGISTRADA`** (DA8 A): «Linea ya registrada en Sigrid: editarla aqui no la
  cambiaria alli (el synckey evita que se reescriba). En Sigrid no se borran lineas: para
  corregirla, que Administracion la edite alli (si sobra, a 0 horas); «Comprobar en Sigrid»
  enseña la diferencia.» Hasta F-052 el portal no tiene vía para traer ese cambio.

## 7. Doble `SigridFake` (tests/dobles.py)

- `stmt_anular_linea(...)` → `{"op": "anular", ide, reside, fec, horide, antes}`; en
  `escribir`, pone `can = 0` y `tot = 0` solo si la fila existe con esos valores, sin
  `enlazada` y con su parte En registro (la semántica del SQL, que fija
  `test_f053_cliente_anular.py`); si no, 0 filas. Desaparece `op == "borrar"`.
- Las filas del doble admiten `enlazada` y `tex`, y `_a_linea_sigrid` los traslada.

## 8. Tests (sin red ni BBDD; datos sintéticos)

| Fichero | Cubre |
|---|---|
| `test_f053_cliente_anular.py` | R2–R4, R9: texto y parámetros exactos de `stmt_anular_linea` (horide nulo → 0, `antes` nulo → 0); sin `DELETE` ni `stmt_borrar_linea` en las dos fuentes; `lineas_existentes` con `enlazada` y la misma expresión que `lineas_para_reajuste` (`httpx` simulado) |
| `test_f053_pisado.py` | R5–R8, R11, R13: `tiene_horas` (None, 0, 0.0, −2, 8), `es_incidencia`, `choques` (a 0, incidencia a 0, mías, otro código), `origen_linea`, motivos (prefijo, `ide`, código, ≤ 255, sin nombres) |
| `test_f053_pipeline_pisado.py` | R1, R5–R8, R10, R12–R17: ejemplos 1–6; parte cerrado con línea a 0 ⇒ se escribe; precedencia; `anuladas`; `caplog` sin nombres; relectura que falla; `vigilar_lock`; ninguna op `borrar` |
| `test_f053_textos_pisado.py` (sv4) | R19–R21: `conflictosHtml` y `resultadoHtml` ejecutados con `node` (patrón de `test_f031_preflight_avisos.py`), sin «se borra» y con escape; `reparto_obras` suma `anuladas`; `MOTIVO_LINEA_REGISTRADA` sin «borra la linea en Sigrid» |

**Enmiendas**: `test_f002_pipeline_fases.py` l.308 y `test_f002_mutantes.py` l.157
(`borradas` → `anuladas`); `test_f031_pipeline_estado.py` l.215–217, 346–349, 456, 477
(espía y op `anular`); `test_f022_reparto_obras.py` l.203–233; `test_f024_borrado_sigrid.py`
l.110–115 (R16 de F-024: la vía sigue existiendo pero el texto ya no la aconseja); los de
F-034 que fijan `stmt_borrar_linea`, su `DELETE` o `borradas`. R4 y R19 también con un test
de fuente («ningún `DELETE FROM` en el cliente», «ningún "se borra" en `conflictosHtml`»).
Fase RED con traza para R1, R2, R4–R12, R19–R21; R15–R18 son de caracterización.

## 9. Verificaciones manuales

- **M1 (líder, solo lectura, antes de implementar; sigrid-api `sql/read`, base `ruesma`,
  agregados)**, sobre partes de obra (`con.tip = 35`, `ISNULL(hmo.reside, 0) = 0`) de 2026:
  (a) líneas por origen (`partes:%`, otra synckey, sin synckey), cuántas sin horas que no
  son `CI%` y cuántas enlazadas (`ENLACES_HMORES`) o con `ISNULL(canven, 0) <> 0` (DA1, DA4);
  (b) grupos `(hmoide, reside, fec, horide)` con más de una línea con horas, y los de `CI%`
  con más de una (DA6); (c) prefijos de synckey ajenos (`LEFT(synckey, CHARINDEX(':',
  synckey))`). **No es medible en Sigrid** cuántas se borraron al pisar (un `DELETE` no deja
  fila); sí en los logs de sv5, opcional: `ContainerAppConsoleLogs` de `partes-transfer` con
  `[sigrid-write] DELETE FROM hmores` y `[registro] escritas=… borradas=`, y en la base
  `partes` `COUNT(*)` de `sigrid_estado = 'borrado_sigrid'` (sin saber quién borró).
- **M2 (humano, tras `redeploy_partes.ps1 -Solo sv5` y `-Solo sv4`)**: desde local, modo
  pruebas (`OBRA_PRUEBAS_FORZAR=true`, obra 0404, `PRUEBA-IA`): con una línea manual de
  pruebas en 0404 (mismo recurso, día y código), aprobar la del portal ⇒ conflicto ⇒ pisar ⇒
  la manual queda en Sigrid con `can = 0`, `tot = 0` y su `tex`, la nueva `registrado`, el
  modal dice «puestas a 0». Limpiar con `prueba_escritura_sigrid.py limpiar`.
- **M3 (humano)**: volver a aprobar otra línea del mismo recurso, día y código en 0404 ⇒ la
  línea a 0 ya no sale como conflicto.
- **M4 (humano)**: el candado de una línea `registrado` muestra el texto de DA8.

## 10. Documentación y aviso a `porcentajes`

- `docs/ARCHITECTURE.md`: doble canal («la confirmación de pisar conflictos (destructiva…)»
  → «edita líneas ajenas: las pone a 0»); semántica 5 (pisado = `can = 0`, `tot = 0`) y 16
  (ninguna sentencia de sv5 borra en Sigrid; choques solo con horas; `incidencia_en_sigrid`
  y `linea_enlazada`).
- `azure-apps/partes.md`, paso 5 de sv5 y «Qué se rompe»: lo mismo y la **nota a
  `porcentajes`**: (1) su `dedicacion-transfer` sigue borrando al pisar (mismo
  `stmt_borrar_linea`): recomendación de la misma regla; (2) desde F-053 partes puede dejar a
  0 líneas suyas (synckey intacta: su idempotencia las dará por escritas y no las
  reinsertará); (3) `estado_parte.py`, `cuenta_analitica.py` y el alta no cambian.
  `dedicacion.md` es de `porcentajes`: no se toca.

## 11. Riesgos y alternativas descartadas

- **Líneas a 0 en Sigrid**: más filas a 0 h para Administración; es la regla (F-046 igual).
- **Pisada en otro lote** (lotes de 15): la anulación y su `INSERT` pueden ir en
  transacciones distintas; F-034 R4 impide la duplicación y R10 lo explica.
- **Descartado**: limpiar la synckey de una pisada `partes:<id>` para poder reaprobarla
  (DA2 B): rompe la idempotencia y F-024; el arreglo de esas líneas es F-052.

## 12. Decisiones abiertas (para el humano)

| DA | Pregunta | Alternativas | Recomendación |
|---|---|---|---|
| DA1 | Qué se pone a 0 | A: `can` y `tot` (patrón F-046). B: además `canven` (venta). C: A + marca en `tex` | **A** (B si M1(a) da líneas con venta) |
| DA2 | Synckey de la pisada | A: no se toca. B: se vacía. C: se reescribe a `pisada:<ide>` | **A** (idempotencia, F-024 y `porcentajes` siguen viendo su línea) |
| DA3 | Cómo se reconoce una pisada | A: por los datos (0 h junto a la línea nueva del mismo recurso, día y código) + INFO de R13. B: marca en `tex`. C: A + B | **A** (`tex` de una ajena no es nuestro) |
| DA4 | Qué se puede pisar | A: cualquier origen salvo enlazadas (R7). B: solo `partes:`. C: todo, como hoy | **A** |
| DA5 | Líneas a 0 al detectar choques | A: no chocan, salvo para incidencias (R5). B: siguen chocando | **A** (B deja conflictos eternos y omisiones `parte_cerrado` sin horas) |
| DA6 | Incidencia contra la misma incidencia | A: `omitido` `incidencia_en_sigrid`. B: pisar inserta igualmente (duplica). C: conflicto no pisable | **A** |
| DA7 | Clave del resultado | A: `anuladas` en lugar de `borradas`, sv4 y sv5 a la vez. B: `borradas` con el significado nuevo. C: las dos una versión | **A** (el desfase de despliegue solo oculta un recuento del modal) |
| DA8 | `MOTIVO_LINEA_REGISTRADA` | A: texto de §6 ya. B: dejarlo a F-052, que traerá la vía «corrige en Sigrid y sincroniza». C: no tocarlo | **A** (B si se prefiere un solo cambio de texto) |
| DA9 | `DELETE` de `prueba_escritura_sigrid.py limpiar` | A: se mantiene (solo `PRUEBA-IA` de la obra de pruebas, herramienta manual). B: pasarlo a 0 | **A** |
| DA10 | Línea del portal pisada (`partes:<id>`) | A: el portal no cambia; F-024 enseña la diferencia y F-052 la concilia. B: sv5 devuelve sus `registro_id` y sv4 anota `sigrid_motivo` | **A** |
| DA11 | Rigor | crítico / estándar | **crítico** (escribe en Sigrid) |
| DA12 | `WHERE` optimista del `UPDATE` | A: `ide` + recurso + fecha + código + `can` leído. B: solo `ide`. C: A + synckey | **A** |
