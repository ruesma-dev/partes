<!-- specs/F-060-racha-incidencia-ciz-movil/design.md -->
# F-060 · Racha de incidencia con CIZ móvil — Diseño

## 1. Contexto y límite de servicio

Hoy (dev 0926857): sv4 `_rol_incidencia` (`parte_repository.py` l.2218) busca por
`empleado_dni` o `empleado_ide`, 50 filas atrás y delante, sin `is_active` del documento ni
letra; sv5 `_decidir_incidencia` (R1): `intermedio` ⇒ omitir, `fin` ⇒ CIZ nuevo, resto ⇒ CI*.

Límite de servicio (sin duplicar lógica): **sv4** sabe qué días trabajó o faltó la persona
(base `partes`, todas las obras, también mensuales cuyas horas no llegan a Sigrid) y decide
el rol y qué líneas forman la racha; no lee Sigrid. **sv5** sabe qué hay en Sigrid: busca el
CIZ de esas líneas por synckey y lo mueve; no lee `partes`. Cada lado tiene su mitad: nada
entra en la lista cerrada de duplicaciones. sv1, sv2 y sv3 no se tocan.

## 2. Ficheros

**Crear**
- `services/partes-front/application/services/racha_incidencia.py` (application, puro).
- `services/partes-transfer/application/services/racha_ciz.py` (application, puro).
- Tests: `services/partes-front/tests/test_f060_racha_incidencia.py` (puro),
  `test_f060_aprobacion_racha.py` (repositorio con `FabricaSesionSqlite`, modal con node),
  `services/partes-transfer/tests/test_f060_racha_ciz.py` (puro),
  `test_f060_cliente_mover.py` (texto y parámetros SQL), `test_f060_pipeline_mover.py`.

**Modificar**
- sv4 `infrastructure/database/parte_repository.py`: `_rol_incidencia` sustituido por
  `_roles_de_racha(session, regs, incidencias)` (una consulta por persona, §3);
  `lineas_para_registro` añade `racha_registro_ids` a cada línea y `avisos_racha` a cada
  grupo; `marcar_registros_sigrid` aplica `movida_de` (§6).
- sv4 `application/services/reparto_obras.py`: `escritas` ya se concatena tal cual (test,
  R30); `avisos_racha` por grupo como `avisos_incidencia`. `static/app.js`:
  `avisosRachaHtml` junto a `avisosIncidenciaHtml` (R11).
- sv4 `tests/test_f025_aprobacion.py`: `CLAVES_LINEA` gana `racha_registro_ids` (enmienda
  citada en el informe).
- sv5 `domain/models/registro_models.py`: `LineaEntrada.racha_registro_ids: list[int]`;
  `AccionLinea.mover: LineaSigrid | None`; `LineaSigrid` gana `tex` y `pos` opcionales.
- sv5 `interface_adapters/api/app.py`: `LineaIn.racha_registro_ids: list[int] = []`;
  `config/settings.py`: `mover_ciz: bool = Field(False, alias="MOVER_CIZ")`.
- sv5 `infrastructure/sigrid/sigrid_write_client.py`: `lineas_de_racha` y
  `stmt_mover_linea` (§5).
- sv5 `application/pipelines/registro_pipeline.py`: paso 6 bis en `_evaluar`; paso 9 usa
  `stmt_mover_linea` para las acciones con `mover`; `escritas` con `movida_de` (§5).
- sv5 `reglas_registro.py`: solo el docstring de R1. `tests/dobles.py` (`SigridFake`):
  `lineas_de_racha` y op `mover` con la semántica del SQL (WHERE optimista y guardas).
- Docs: `docs/ARCHITECTURE.md` semántica 4, `docs/referencia/partes-proyecto.md` §3.5 y
  §4.4, `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (commit local, sin push).

**No se tocan**: `orm_models.py` (sin esquema), sv3, `incidencias_horas.py` (se reutilizan
`normalizar_codigo` y `TablaIncidencias`), `congelacion.py`, `pisado.py`, `parte_abierto.py`,
`estado_parte.py` y `cuenta_analitica.py` (copias de `porcentajes`), `comprobacion_lineas.py`,
el reajuste de F-046, `resultado_json.py`, `prueba_escritura_sigrid.py`, `incidencias.yaml`.

## 3. sv4 · `racha_incidencia.py` y su uso

```python
@dataclass(frozen=True)
class LineaHist:            # lo que la regla necesita de una línea del portal
    registro_id: int; fecha_int: int; es_incidencia: bool; clave: str
    horas: float | None; sigrid_estado: str | None; activa: bool

@dataclass(frozen=True)
class DecisionRacha:
    rol: str                         # inicio | fin
    racha_registro_ids: tuple[int, ...]

def ventana(fecha_int: int) -> tuple[int, int]          # (día 1 del mes anterior, D − 1)
def hasta_delante(fecha_int: int) -> int                 # último día del mes siguiente
def decidir(hist: Sequence[LineaHist], fecha_int: int, clave: str) -> DecisionRacha
def colapsar(lineas: Sequence[tuple[int, str, int, str, str]]) -> dict[int, str]
    # (registro_id, persona, fecha, clave, rol) -> rol final (R7, R8)
def aviso_desordenada(hist, fecha_int: int) -> bool       # R10
```

`decidir`: agrupa `hist` (solo `activa`) por día; recorre hacia atrás desde D − 1 dentro de
la ventana saltando días sin líneas que cuenten; el primero que cuenta decide (R2–R4). Con
`fin`, sigue hacia atrás mientras los días sean de incidencia de la misma clave y hacia
delante (D + 1 … `hasta_delante`) igual; `racha_registro_ids` = las incidencias de esa clave
de esos días, más las inactivas `registrado`/`encolado` de esos días (R9). Clave de una
línea: `tabla.clase_de(incidencia_codigo, hora_codigo).letra` si hay tabla y la reconoce;
si no, `normalizar_codigo(incidencia_codigo) or normalizar_codigo(hora_codigo)`.

En el repositorio, `_roles_de_racha` agrupa las líneas de incidencia de la aprobación por
`persona_de`; por persona, UNA consulta de `ParteRegistroOrm` join `ParteDocumentOrm` en
`[min(ventana), max(hasta_delante)]`, prefiltrada en SQL por `empleado_dni` (o
`recurso_ide` / `empleado_ide` según la clave de `persona_de`) y confirmada en Python con
`persona_de` (R6, R12); trae activas e inactivas con su marca `activa`. Después `colapsar`
sobre todas las líneas de la aprobación (antes del reparto por obra de F-022). El log INFO de
roles no cambia (solo ids). El aviso de R10 usa la misma consulta por persona, que se hace
para toda persona de la aprobación con alguna línea de trabajo o de incidencia.

## 4. Contrato sv4 ↔ sv5

- Línea del payload (los dos canales de F-002): `racha_registro_ids: list[int]` nuevo.
  sv5 viejo lo ignora (pydantic ignora extras; el consumidor filtra por `fields`).
- `escritas[i]` gana `movida_de: int` y `hmores_ide: int` cuando se movió. Sin la clave,
  sv4 se comporta como hoy. `resultado_json.py` no cambia (pasa `escritas` tal cual).
- Despliegue: **sv5 y luego sv4**, `MOVER_CIZ` apagado; se enciende tras M1–M3 (§9).

## 5. sv5 · decidir y mover

`racha_ciz.py` (puro):
```python
@dataclass(frozen=True)
class DecisionFin:
    tipo: str             # crear | mover | intermedio | parte_cerrado | enlazada
    linea: LineaSigrid | None = None
    motivo: str | None = None
    duplicados: int = 0

def decidir_fin(fecha_int: int, recurso_ide: int, candidatas: Iterable[LineaSigrid], *,
                estados: Mapping[int, int | None], est_registro: int,
                marca_pruebas: str | None) -> DecisionFin
```
Filtra recurso, código `CIZ`, `can` nulo o 0 y, con `marca_pruebas`, `tex` que la contenga
(R19). Posterior a D ⇒ `intermedio` (R14); anterior ⇒ la de mayor (fecha, ide): enlazada ⇒
`enlazada` (R18), su parte no En registro ⇒ `parte_cerrado` (R17), si no ⇒ `mover` con
`duplicados` = resto (R15); nada ⇒ `crear` (R16). Motivos sin tildes, sin nombres, ≤ 255.

Pipeline, `_evaluar`, **paso 6 bis** (tras la idempotencia, antes de conflictos; bajo el
lock en `registrar`, consultivo en `preflight`, R25): si `settings.mover_ciz` y hay acciones
`escribir` con `hora_codigo == "CIZ"` y `racha_registro_ids`, una llamada a
`lineas_de_racha(synckeys)` para todas, una a `estados_de_partes(hmoides)` de las
candidatas, y `decidir_fin` por acción: `intermedio` / `parte_cerrado` / `enlazada` ⇒
`_omitir`; `mover` ⇒ `a.mover = linea` + WARNING si `duplicados`. El paso 7 corre igual
para la acción (un CIZ ajeno el día D sigue siendo `incidencia_en_sigrid`).

Cliente:
```sql
-- lineas_de_racha(claves): por lotes como lineas_por_synckey
SELECT hmores.ide, hmores.hmoide, hmores.reside, hmores.fec, hmores.horide,
       auxhor.cod AS hora, hmores.can, hmores.tot, hmores.synckey, hmores.tex, hmores.pos,
       CASE WHEN <_expr_enlazada()> THEN 1 ELSE 0 END AS enlazada
FROM hmores LEFT JOIN auxhor ON auxhor.ide = hmores.horide
WHERE hmores.synckey IN (?, …)
-- stmt_mover_linea(linea, destino, hmoide, pos, fecha_int, synckey, paride, caaide, ano, mes)
UPDATE hmores SET fec = ?, synckey = ?, hmoide = ?, obride = ?, cenide = ?, paride = ?,
       caaide = ?, ano = ?, mes = ?, pos = ?
WHERE ide = ? AND reside = ? AND fec = ? AND ISNULL(horide, 0) = ? AND synckey = ?
  AND ISNULL(can, 0) = 0 AND NOT (<_expr_enlazada()>)
  AND <_guarda_parte_abierto('hmores.hmoide')> AND <_guarda_parte_abierto('?')>
```
`pos`: la leída si `hmoide` no cambia; si cambia, la del contador `pos_por_parte` del paso 9.
`cenide` y `obride` del destino como en `stmt_insert_linea`; `paride`, `caaide`, `ano`, `mes`
los de la acción de D. En SQL Server el `WHERE` ve la fila antes del `UPDATE`: la primera
guarda mira el parte de origen. Paso 9: con `a.mover` va `stmt_mover_linea` en lugar de
`stmt_insert_linea`; `escritas` añade `movida_de` (id de `linea.synckey`) y `hmores_ide`.
La relectura por synckey de F-034 confirma o deja `omitido` (R23). INFO de R24.

## 6. sv4 · aplicar `movida_de`

En `marcar_registros_sigrid`, tras marcar cada escrita: si trae `movida_de` = X y X ≠ D,
`UPDATE parte_registros SET sigrid_estado='omitido', sigrid_motivo=:m … WHERE id = X AND
sigrid_estado='registrado' AND sigrid_hmores_ide = :ide` (CAS, misma sesión y commit). 0
filas ⇒ WARNING `fin_movido_sin_cas` con ids. Motivo (≤ 255): `fin_movido: el fin de la
incidencia (CIZ, linea <ide>) paso al dia <AAAA-MM-DD>`. Reaplicar: la segunda vez X ya está
`omitido` ⇒ 0 filas, sin WARNING si su motivo ya es ese (R29). X queda editable como hoy un
`intermedio`; reaprobarla da `intermedio` (R14).

## 7. Interacciones

- **F-019 (R0)**: dedicación manda antes que R1; con el interruptor de mensuales encendido
  sus incidencias no llegan a Sigrid y no hay nada que mover. Sus días trabajados sí están
  en `partes` y cierran la racha.
- **F-024**: X deja de ser `registrado` ⇒ no se comprueba; D se comprueba por su synckey y
  da `presente` sin diferencia de fecha. Si el resultado no llega, X saldría `borrado_sigrid`
  en la comprobación (editable y reaprobable: da `intermedio`). Riesgo aceptado.
- **F-025**: sin cambios; un día con V y horas cuenta como trabajado (cierra) y no viaja.
- **F-031 / F-034**: destino = parte elegido (complementario si hace falta); origen cerrado
  ⇒ R17; cierre en carrera ⇒ 0 filas y relectura (R23). **F-046 / F-053**: sin cambios,
  ningún `DELETE`. **`porcentajes`**: no se tocan sus copias.

## 8. Tests (sin red ni BBDD)

sv4: puros de `decidir`/`colapsar`/`ventana` (bordes: 1 de enero ⇒ diciembre del año
anterior; fin de semana sin líneas; letra distinta; papelera; sin DNI); repositorio con
`FabricaSesionSqlite` (payload, avisos, CAS de §6, una consulta por persona con contador de
`execute`); `node --check static/app.js` y texto de `avisosRachaHtml`. sv5: `decidir_fin`
por tipo; texto y parámetros exactos de las dos sentencias y test de fuente sin `DELETE`;
pipeline con `SigridFake`: el ejemplo del humano día a día (CIV; CIZ día 2; movido a 3 y 4;
día 5 nada), cambio de mes (mueve de parte), interruptor apagado y sin ids ⇒ como hoy,
modo pruebas sin marca ⇒ crea, carrera (WHERE falla ⇒ omitido), reentrega ⇒
`ya_registrado`. Fase RED con traza para R1–R30 salvo R27 (caracterización).

## 9. Verificaciones manuales

`$KEY` = function key de sigrid-api que el humano saca del Key Vault (nunca en un fichero).
Lectura: `Invoke-RestMethod -Method Post -Uri "$env:SIGRID_API_BASE_URL/api/sql/read"
-Headers @{ 'x-functions-key' = $KEY } -ContentType 'application/json' -Body $q`.

- **M0 (líder, antes de implementar, solo lectura)**: legado y enlaces de los CIZ de partes.
  ```powershell
  $q = @{ database = 'ruesma'; max_rows = 200; parameters = @('CIZ', 'partes:%');
    sql = 'SELECT h.ano, h.mes, COUNT(*) AS lineas, COUNT(DISTINCT h.reside) AS recursos, SUM(CASE WHEN ISNULL(h.dvaproide,0)<>0 OR ISNULL(h.dvfproide,0)<>0 OR ISNULL(h.hdereside,0)<>0 OR ISNULL(h.emprccide,0)<>0 OR ISNULL(h.empdpreide,0)<>0 OR ISNULL(h.empabside,0)<>0 THEN 1 ELSE 0 END) AS enlazadas FROM hmores h JOIN auxhor a ON a.ide = h.horide WHERE a.cod = ? AND h.synckey LIKE ? GROUP BY h.ano, h.mes ORDER BY h.ano, h.mes' } | ConvertTo-Json
  ```
  Y los recursos-mes con más de un CIZ: el mismo `$q` con `sql = 'SELECT COUNT(*) AS grupos
  FROM (SELECT h.reside, h.ano, h.mes FROM hmores h JOIN auxhor a ON a.ide = h.horide WHERE
  a.cod = ? AND h.synckey LIKE ? GROUP BY h.reside, h.ano, h.mes HAVING COUNT(*) > 1) x'`.
  Anotar cifras sin nombres. `enlazadas` > 0 cambia DA3 (R18 deja esos CIZ sin mover).
- **M1 (humano, local, sv5 con `OBRA_PRUEBAS_FORZAR=true` y `MOVER_CIZ=true`)**: en el
  portal local, partes de prueba de un recurso de `prueba_escritura_sigrid.py`: V los días
  1–4 y 8 h el 5 de un mes; aprobar día a día. Tras cada uno, `python
  .\prueba_escritura_sigrid.py verificar` (ANO/MES del bloque CONFIG): día 1 un CIV; día 2
  CIV + CIZ el 2; días 3 y 4 el MISMO `ide` de CIZ con fecha 3 y 4; día 5 sin cambio en la
  incidencia. En el portal, los días 2 y 3 `omitido` con `fin_movido`. Administración mira
  la «Vista calendario» de la 0404: tramo 1–4. Partes de prueba a la papelera y
  `limpiar --ejecutar`.
- **M2 (humano, igual que M1)**: V el 30 y 31 de un mes y el 1 del siguiente: el CIZ pasa del
  parte de un mes al del otro (mismo `ide`, `verificar` con los dos meses); limpiar ambos.
- **M3 (humano)**: aprobar los días 1–4 de una vez ⇒ CIV el 1, CIZ el 4, 2 y 3 `intermedio`.
- **M4 (humano, producción, tras `az containerapp update -n ca-sv5-transfer -g
  rg-partes-dev --set-env-vars MOVER_CIZ=true`, solo lectura)**: con `<AAAAMMDD>` = día del
  encendido, el segundo `$q` de M0 añadiendo `AND h.fec >= ?` (parámetro `<AAAAMMDD>`)
  debe dar 0 grupos nuevos; en la base `partes`: `SELECT COUNT(*) FROM parte_registros
  WHERE sigrid_motivo LIKE 'fin_movido:%' AND sigrid_registrado_at_utc >= '<ISO UTC>';`.
  Vuelta atrás: `--set-env-vars MOVER_CIZ=false`.

## 10. Documentación

ARCHITECTURE semántica 4 y `partes-proyecto.md` §3.5 y §4.4 (el papel, §4.1, no cambia):
ventana, letra, papelera, CIZ móvil por `UPDATE`, `MOVER_CIZ`, `fin_movido`.
`azure-apps/partes.md` (paso 3 de sv5, `MOVER_CIZ`, «Qué se rompe»): **sí cambia lo que el
proyecto escribe en Sigrid** (edita fecha y parte de sus CIZ), por eso se actualiza.

## 11. Riesgos y alternativas descartadas

- Ventana corta: una baja con el papel marcando solo el primer y el último día a más de un
  mes, o una racha anterior al sistema o puesta a mano en Sigrid, abre un CI* nuevo a mitad
  de racha (DA1). Mover entre partes es nuevo en Sigrid: M2 y Administración (DA3).
- Descartado: tabla `incidencia_racha` (DA2 B); conservar la synckey de X (F-024 vería otra
  fecha y D no sería idempotente); mover solo `fec` entre meses (línea de agosto en un parte
  de julio); buscar el CIZ por recurso y código (editaría líneas ajenas o manuales).

## 12. Decisiones abiertas (las valida el humano)

| DA | Pregunta | Alternativas | Recomendación |
|---|---|---|---|
| DA1 | Ventana «del mes anterior» y qué pasa si no hay nada en ella | A: del día 1 del mes anterior al de D hasta D − 1, todas las obras; sin líneas ⇒ abre con CI* (como hoy). B: A + sv5 lee los CI*/CIZ del recurso en Sigrid en esa ventana para decidir. C: A + esa lectura solo como aviso | **A**. B descartada: Sigrid no tiene los días trabajados de mensuales ni de recursos sin `HL*` (no sabe si la racha se cerró), lo manual no lleva synckey y editarlo es tocar lo ajeno, y añade una lectura por incidencia. C posible en otra feature |
| DA2 | Dónde vive el estado de la racha y la synckey | A: se deduce (sv4 del histórico de `partes`, sv5 busca el CIZ por synckey); la synckey pasa a D y X queda `omitido`. B: tabla `incidencia_racha` en `partes` (sv4 la escribe; 8.ª tabla en los dos `orm_models.py`). C: columna con el código escrito | **A** (sin esquema; B es una segunda verdad que hay que mantener con papelera, desaprobar y ediciones) |
| DA3 | CIZ en otro parte (otra obra u otro mes) o en parte cerrado | A: `UPDATE` también de parte, obra, centro, partida, cuenta, año, mes y posición, con guarda en los dos partes; origen cerrado ⇒ `omitido` `ciz_en_parte_cerrado`. B: igual, pero origen cerrado ⇒ CIZ nuevo (dos CIZ). C: solo mover dentro del mismo parte; si no, CIZ nuevo | **A**, condicionada a M2 y al visto bueno de Administración (mover una línea de parte es nuevo) |
| DA4 | V seguida de B | A: cierra la V y abre la B con su CI*. B: misma racha | **A** |
| DA5 | Papelera | A: no cuenta para decidir (línea y documento). B: cuenta | **A** (sí se buscan por synckey sus CIZ registrados) |
| DA6 | Incidencia de un día y luego trabajo | A: solo CI*, como hoy. B: CI* y CIZ el mismo día | **A**, **pendiente de Administración** |
| DA7 | Desorden: trabajo o incidencia que llega dentro de una racha ya escrita; desaprobar o papelera del día del CIZ | A: incidencia anterior al CIZ ⇒ `intermedio` (R14); trabajo o inicio antes de una incidencia registrada ⇒ aviso `racha_desordenada` y corrección manual; desaprobar y papelera no mueven nada (lo registrado está congelado, F-004). B: mover el CIZ o el CI* hacia atrás | **A** |
| DA8 | Rachas ya escritas con varios CIZ | A: fuera; informe M0 y R15 mueve solo el último. B: corregirlas en esta feature | **A** |
| DA9 | Mensuales (F-019) y F-024 | Impacto en §7, sin cambios en esas reglas | **Aceptar §7** |
| DA10 | Identidad | A: `persona_de` (DNI; sin DNI, clave de trabajador) para decidir; sv5 solo mueve un CIZ del mismo recurso. B: por recurso | **A** (un cambio de empresa con otro recurso abre CIZ nuevo) |
| DA11 | Encendido | A: `MOVER_CIZ` en sv5, apagado, se enciende tras M1–M3. B: sin interruptor | **A** (rigor crítico; rollback sin redesplegar) |
