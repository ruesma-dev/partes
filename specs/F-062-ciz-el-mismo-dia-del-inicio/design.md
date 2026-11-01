<!-- specs/F-062-ciz-el-mismo-dia-del-inicio/design.md -->
# F-062 · El inicio de una incidencia escribe CI* y CIZ el mismo día — Diseño

## 1. Contexto y límite de servicio

Hoy (F-060, `MOVER_CIZ` encendido en producción): el `inicio` escribe su CI*; el `fin` busca
el CIZ por `partes:<id>` de `racha_registro_ids` y lo mueve o lo crea; un día suelto queda solo
con su CI*. Con F-062 el `inicio` escribe además un **CIZ hermano** (`partes:<X>:ciz`) y el
siguiente `fin` lo mueve: día 1 V ⇒ CIV + CIZ el 1; días 2, 3 y 4 ⇒ el CIZ al 2, 3 y 4; día 5.

**Límite de servicio** (sin duplicar lógica, nada entra en la lista cerrada): **sv4** sabe qué
días hay en `partes` y qué viaja en la aprobación: decide qué `inicio` lleva CIZ (R1–R3) y
manda su tramo delante; no lee Sigrid. **sv5** sabe qué hay en Sigrid: escribe el hermano o no
(R6–R17) y lo mueve (R18–R23); no lee `partes`. sv1, sv2 y sv3 no se tocan.

## 2. Ficheros

**Crear** (tests): `services/partes-transfer/tests/test_f062_ciz_mismo_dia.py` (puro y
pipeline con `SigridFake`), `test_f062_cliente_inicio.py` (texto y parámetros SQL),
`services/partes-front/tests/test_f062_inicio_con_ciz.py` (puro y repositorio).

**Modificar — sv5** (`services/partes-transfer/`):
- `domain/models/registro_models.py`: `LineaEntrada.ciz_mismo_dia: bool = False`; `FinMismoDia`
  (`horide`, `hora_codigo`, `pre`, `caa_ide = 0`, `caa_cod`); `AccionLinea.fin_mismo_dia = None`.
- `interface_adapters/api/app.py`: `LineaIn.ciz_mismo_dia: bool = False`. La cola construye
  `LineaEntrada` filtrando por `fields`: el campo nuevo entra solo.
- `application/services/reglas_registro.py`: `ReglasRegistro(..., mover_ciz=False)`; en
  `_decidir_incidencia`, rol `inicio` con `mover_ciz` y `linea.ciz_mismo_dia` ⇒ `fin_mismo_dia`
  con el CIZ de `cis` (R6) o WARNING `sin_ciz_mismo_dia` (R7). Docstring de R1.
- `application/services/racha_ciz.py`: `decidir_mismo_dia` (§5.2), `es_ciz_del_recurso` (hoy
  privada), `registro_de_synckey` da None con sufijo de forma explícita (R20); docstring.
- `infrastructure/sigrid/sigrid_write_client.py`: `SUFIJO_CIZ = ":ciz"`, `synckey_ciz_de`,
  `stmt_insert_inicio_con_fin` (§5.4). `config/settings.py`: comentario de `MOVER_CIZ`.
- `application/pipelines/registro_pipeline.py`: `preparar` pasa `mover_ciz` a las reglas; pasos
  4b, 6, 6 bis, 7, 9 y relectura (§5); docstring. `tests/dobles.py`: §5.4 en `SigridFake`.

**Modificar — sv4** (`services/partes-front/`):
- `application/services/racha_incidencia.py`: `racha_delante(hist, D, clave)` e
  `inicios_con_ciz(lineas, roles)` (§3).
- `infrastructure/database/parte_repository.py`: `lineas_para_registro` añade
  `"ciz_mismo_dia": False` a cada línea; `_roles_de_racha` devuelve también el tramo delante y
  los `inicio` con CIZ (§3). `config/settings.py`: comentario de `MOVER_CIZ`.
- `tests/test_f025_aprobacion.py`: `CLAVES_LINEA` gana `ciz_mismo_dia`; las aserciones de F-060
  con lista vacía en un `inicio` encendido se enmiendan (R1 enmienda R9 de F-060), citadas.

**Docs**: §10. **No se tocan**: `orm_models.py`, sv1–sv3, `decidir`, `colapsar`,
`aviso_desordenada`, `_rol_incidencia_anterior`, `_fin_movido`, `marcar_registros_sigrid`,
`reparto_obras.py`, `static/app.js`, plantillas, `decidir_fin`, `stmt_mover_linea`,
`stmt_insert_linea`, `comprobacion_lineas.py`, `pisado.py`, `parte_abierto.py`, `estado_parte.py`,
`cuenta_analitica.py`, `congelacion.py`, `reajuste_pipeline.py`, `resultado_json.py`,
`prueba_escritura_sigrid.py` e `incidencias.yaml`.

## 3. sv4 · qué `inicio` lleva CIZ

Puro, en `racha_incidencia.py`:
- `racha_delante(hist, D, clave) -> tuple[int, ...]` (R1): días que cuentan (`_dias`) desde
  D + 1 hasta `hasta_delante(D)`, en orden, mientras sean de la clave; ids de las incidencias
  activas de esa clave de esos días, más las de la papelera de esa clave en `registrado`/
  `encolado` con fecha en (D, último día del tramo] (sin tramo, solo nada). Ordenada.
- `inicios_con_ciz(lineas: Sequence[LineaRol], roles: Mapping[int, str]) -> set[int]` (R2): los
  `registro_id` con rol final `inicio` para los que ningún `fin` final de la misma persona y
  clave tiene ese id en su `racha_registro_ids`.

En `_roles_de_racha` (solo con `mover_ciz`), tras `colapsar`: por cada `inicio` final, su lista
es `racha_delante(historicos[persona], D, clave)`; `ciz` = `inicios_con_ciz(...)`. Devuelve
`(roles, rachas, avisos, ciz)` y `lineas_para_registro` pone `ciz_mismo_dia = r.id in ciz` y la
lista de `rachas` (también del `inicio`). Apagado (R4): `False` y listas vacías. Antes del
reparto por obra (F-022): cuenta un `fin` de otra obra (R2). Ninguna consulta nueva.

## 4. Contrato sv4 ↔ sv5

- Línea del payload (HTTP y cola): `ciz_mismo_dia: bool` nuevo; `racha_registro_ids` viaja
  también en el `inicio` (su tramo delante). Un sv5 anterior lo ignora (extras ignorados).
- `escritas[i]` del inicio gana `ciz_hmores_ide` (informativa, sv4 no la guarda, DA3); una
  escrita de un hermano movido lleva `hmores_ide` y no `movida_de` (R19).
- **Despliegue con `MOVER_CIZ` YA encendido** (producción, 2026-10-25: sv5 `ca-sv5-transfer--
  0000003` 12:08:43Z, sv4 `ca-sv4-front--0000002` 12:09:28Z; `dev` 463869d). Con DA1 = A,
  F-062 se activa al desplegar, sin tocar variables: **sv5 y luego sv4**, con M0 y M1–M5 hechas
  ANTES de desplegar sv4. sv5 nuevo con sv4 viejo es F-060 por R8 (sv4 viejo no manda
  `ciz_mismo_dia`; `partes:<i>:ciz` no existe aún); el orden inverso también (sv5 viejo ignora
  el campo). **Quitar solo F-062**: volver sv4 a su revisión anterior y dejar sv5 nuevo (R8),
  que sigue moviendo los hermanos ya escritos; NO volver sv5 a la imagen de F-060 con hermanos
  vivos (no lee `:ciz`: el siguiente `fin` escribiría otro CIZ). **Vuelta atrás completa**:
  `MOVER_CIZ=false` en sv4 y luego en sv5 (R4, R8); lo escrito no se deshace.

## 5. sv5

### 5.1 Reglas y cuenta (pasos 3–4b)
`reglas.decidir` con `mover_ciz = settings.mover_ciz`: `inicio` + `ciz_mismo_dia` ⇒ acción CI*
de siempre con `fin_mismo_dia = FinMismoDia(ciz.horide, ciz.cod, ciz.pre)` (R6); sin CIZ ⇒
WARNING (R7). En `_resolver_cuentas`, el hermano se resuelve con
`origen_subcuenta(horas_de(a), fin.horide, partida)` y `resolver_cuenta`, en las MISMAS lecturas
(sus `sub` entran en `pedidas`); los recuentos del log no lo cuentan (R9).

### 5.2 Pasos 6 y 6 bis (bajo el lock; consultivo en `preflight`)
Paso 6: si la acción del CI* pasa a `ya_registrado`, `fin_mismo_dia = None` (R10). Paso 6 bis
(`_ciz_de_racha`, solo con `mover_ciz`): `fines` como hoy; `inicios` = acciones `escribir` con
`fin_mismo_dia`. UNA llamada a `lineas_de_racha` con, por cada id i de las listas de `fines` e
`inicios`, `synckey_de(i)` y `synckey_ciz_de(i)`, más `synckey_ciz_de(a.registro_id)` de cada
inicio (R11, R18). Los `fines`, `decidir_fin` sin cambios sobre sus candidatas ampliadas. Por
cada inicio, puro en `racha_ciz.py`,
`decidir_mismo_dia(fecha_int, recurso_ide, candidatas, propia, *, marca_pruebas) -> str | None`:
`"ya_existe"` si `propia` (la de `partes:<D>:ciz`) no es None; `"posterior"` si alguna candidata
cumple `es_ciz_del_recurso` con fecha > D; si no, None (se escribe). Con motivo ⇒
`fin_mismo_dia = None` e INFO `ciz_mismo_dia_omitido registro_id=… motivo=…` (R16).

### 5.3 Paso 7
Acción con `fin_mismo_dia` que sigue `escribir` tras las omisiones del CI*: si en `existentes`
de algún parte del periodo hay una línea con su `reside`, `fecha_int` y `horide == fin.horide`
y synckey fuera de `mias` ⇒ `fin_mismo_dia = None`, INFO `ciz_en_sigrid` (R12). Bloqueada por
un conflicto, no se escribe (R10): no hay hermano sin CI*.

### 5.4 Paso 9: una sentencia, dos filas (DA2)
Acción con `fin_mismo_dia` ⇒ `stmt_insert_inicio_con_fin` en lugar de `stmt_insert_linea`;
`pos_ci = pos_nueva(hmoide)` y `pos_ciz = pos_nueva(hmoide)`:
```sql
INSERT INTO hmores (ide, hmoide, reside, cenide, obride, paride, pos, fec, horide, can, pre,
  tot, ano, mes, fac, ortide, caaide, tex, synckey)
SELECT x.n + v.k, ?, ?, ?, ?, ?, v.pos, ?, v.horide, 0, v.pre, 0, ?, ?, 0, 0, v.caaide, ?,
  v.synckey
FROM (SELECT ISNULL(MAX(ide),0)+1 AS n FROM hmores WITH (UPDLOCK, HOLDLOCK)) x
CROSS JOIN (VALUES (0, ?, ?, ?, ?, ?), (1, ?, ?, ?, ?, ?)) v(k, pos, horide, pre, caaide, synckey)
WHERE <_guarda_parte_abierto('?')>
  AND (v.k = 0 OR NOT EXISTS (SELECT 1 FROM hmores s WHERE s.synckey = ?))
```
Parámetros, en orden: `hmoide, reside, cenide, obride, paride, fecha_int, ano, mes, tex`;
`pos_ci, horide_ci, pre_ci, caaide_ci, partes:<X>`; `pos_ciz, horide_ciz, pre_ciz, caaide_ciz,
partes:<X>:ciz`; `hmoide, est` (guarda); `partes:<X>:ciz`. `can` y `tot` literales 0 (las
incidencias van sin horas). Una sentencia es atómica en SQL Server: las dos filas o ninguna
(salvo el hermano por su `NOT EXISTS`), sin depender del corte en lotes de 15. `SigridFake` la
reproduce (guarda, `NOT EXISTS`, `ide` n y n + 1: el del hermano, consecutivo).
**`pos`**: dos `pos_nueva` seguidas del parte (`max_pos` + `PASO_POS` y + 2 × `PASO_POS`; 64
por defecto), como dos líneas cualesquiera de sv5: el CIZ queda detrás de su CI*, que es lo que
hace Administración (`requirements.md`, 303 de 315 pares). Su distancia la pone la pantalla de
Sigrid y no hay que imitarla: que la de sv5 sea también 64 es casualidad de `PASO_POS`.

### 5.5 Relectura y escritas
La relectura de F-034 pide también `synckey_ciz_de(X)`; `confirmar_escritas` no cambia (decide
el CI*). Confirmado el CI*: con el hermano, `ciz_hmores_ide` en la escrita e INFO `ciz mismo dia
ide=… hmoide=… fecha=… registro_id=…`; sin él, WARNING `ciz_mismo_dia_no_escrito registro_id=…` (R15, R16). Mover (R19): en el paso 9,
si `registro_de_synckey(ls.synckey)` es None no se pone `movida_de`; el INFO «ciz movido»
imprime `synckey=<anterior>-><nueva>` en lugar de `registro_id=…->…`.

## 6. sv4 · aplicar el resultado

Sin cambios (R24): `_fin_movido` ignora una escrita sin `movida_de`; X sigue `registrado` con
el `ide` de su CI* y D queda `registrado` con el del CIZ. Un test de repositorio lo fija.

## 7. Interacciones (DA11)

- **F-019 R0**: dedicación manda antes que R1: sin CI* no hay hermano.
- **F-024**: comprueba `partes:<id>`: X ⇒ su CI*. Si Administración borra el hermano, nadie lo
  ve; el siguiente `fin` crea su CIZ (R22). Si borra el CI*, X sale `borrado_sigrid` y al
  reaprobar el hermano no se duplica (R11 `ya_existe` y el `NOT EXISTS`).
- **F-034**: guarda en las dos filas; carrera ⇒ 0 filas ⇒ omitido por la relectura.
  **F-046/F-053**: sin horas, ni reajuste ni pisado lo tocan; enlazado ⇒ R18 de F-060.
  **F-031**: va al parte elegido de su CI*. **Avisos y modal**: no cambian (R17).
  **Desaprobar/papelera** (DA8): lo `registrado` está congelado (F-004).
- **F-060 DA6** («un día suelto deja solo su CI*») queda sustituida por esta feature.

## 8. Tests (sin red ni BBDD; fase RED con traza en R1–R26 salvo R5 y R25, caracterización)

sv4 puros: `racha_delante` (tramo, corte por trabajo y por otra letra, papelera, fin de mes,
diciembre ⇒ enero), `inicios_con_ciz` (fin de la misma racha en la aprobación, de otra racha,
otra persona, otra clave). Repositorio con `FabricaSesionSqlite`: payload con `ciz_mismo_dia` y
lista delante; días 1–4 de una vez ⇒ el 1 falso; aprobar el 1 con 2–4 ingeridos ⇒ verdadero y
[2, 3, 4]; apagado ⇒ falso y listas vacías; contador de `execute` igual que en F-060.
sv5 puros: `decidir_mismo_dia`, `synckey_ciz_de`, `registro_de_synckey`. Cliente: texto y
parámetros de §5.4, fuente sin `DELETE`. Pipeline con `SigridFake`: los casos M1–M5 de §9 (1
sigue `registrado`), `borrado_sigrid` reaprobado, CIZ ajeno el día D, recurso sin CIZ, parte
cerrado (R23), carrera, reentrega, modo pruebas sin marca, y apagado o sin `ciz_mismo_dia` ⇒
sentencias idénticas a dev f313407 (R8).

## 9. Verificaciones manuales

`$KEY` = function key de sigrid-api que el humano saca del Key Vault (nunca en un fichero). S =
`Invoke-RestMethod -Method Post -Uri "$env:SIGRID_API_BASE_URL/api/sql/read" -Headers
@{ 'x-functions-key' = $KEY } -ContentType 'application/json' -Body $q`.

- **M0 (líder, antes de T1, producción, solo lectura)**: (a) formato libre:
  `$q = @{ database='ruesma'; max_rows=10; parameters=@('partes:%:%'); sql='SELECT COUNT(*) AS n
  FROM hmores WHERE synckey LIKE ?' } | ConvertTo-Json` ⇒ `n = 0` (si no, **PARA**, `blocked`).
  (b) rachas abiertas heredadas (DA6): `sql='SELECT COUNT(*) AS abiertas FROM hmores h JOIN
  auxhor a ON a.ide = h.horide WHERE a.cod LIKE ''CI%'' AND a.cod <> ''CIZ'' AND h.synckey LIKE
  ''partes:%'' AND NOT EXISTS (SELECT 1 FROM hmores z JOIN auxhor b ON b.ide = z.horide WHERE
  b.cod = ''CIZ'' AND z.reside = h.reside AND z.fec >= h.fec)'` (sin parámetros): se anota.
- **Preparación M1–M5 (humano, local)**: la de F-060 en `progress/current.md` («M1–M3 ·
  preparación»: sv5 con `$env:OBRA_PRUEBAS_FORZAR = 'true'; $env:MOVER_CIZ = 'true'; python
  main.py`, `/health` ⇒ `modo_pruebas: True` o **PARA**; sv4 con `$env:MOVER_CIZ = 'true';
  python main.py`; lecturas L, S y V), con F-062 en `dev`, ANTES de desplegar sv4, recurso
  2717792. Meses que
  elige el humano, con `estado` ⇒ `NO existe parte` de la 0404 y **nunca 2026/06–2026/11**
  (PT26/00373, 00375 y 00376 se conservan). Antes, con S: `synckey LIKE 'partes:%:ciz'` ⇒ 0 y
  ninguna `partes:<id>` de los ids locales siguientes (colisión con producción, como en F-060).
- **M1 · un día (`<M1>`)**: V el día 1 y 8 h el 2; aprobar el 1 ⇒ V: CIV y CIZ el 01; S: synckeys
  `partes:<id1>` y `partes:<id1>:ciz`, `pos` seguidas; consola 1: `ciz mismo dia`; L: el 1
  `registrado` con `sigrid_hmores_ide` = `ide` del CIV. Aprobar el 2 ⇒ HL de 8 h; el CIZ sigue el 01.
- **M2 · día a día (`<M2>`)**: V 1–4 y 8 h el 5, aprobando de uno en uno: 1 ⇒ CIV + CIZ el 01
  (anotar su `ide` IZ); 2 ⇒ IZ con `fec` 02 y synckey `partes:<id2>` (consola: `ciz movido
  ide=<IZ> … synckey=partes:<id1>:ciz->partes:<id2>`); 3 y 4 ⇒ IZ al 03 y al 04; 5 ⇒ nada. L: 1
  y 4 `registrado`, 2 y 3 `omitido` `fin_movido`. Administración mira la «Vista calendario».
- **M3 · cambio de mes (`<M3a>` 31, `<M3b>` 1)**: aprobar el 31 ⇒ CIV + CIZ el 31 (IZ, `hmoide`
  Pa); aprobar el 1 ⇒ IZ con `fec` `<M3b>01` y otro `hmoide` (Pb); el 31 sigue `registrado`.
- **M4 · todo de una vez (`<M4>`)**: V 1–4 en una aprobación ⇒ exactamente CIV el 01 y CIZ el 04
  (synckey `partes:<id4>`, ninguna `:ciz`); 2 y 3 `intermedio`.
- **M5 · desordenado (`<M5>`)**: V 1–3; aprobar el 2 ⇒ CIZ el 02; el 1 ⇒ solo CIV el 01 (consola:
  `ciz_mismo_dia_omitido … motivo=posterior`); el 3 ⇒ el CIZ pasa al 03.
- **Limpieza** (cada mes, con `ANO, MES` del mes en `prueba_escritura_sigrid.py`, sin commit):
  `python .\prueba_escritura_sigrid.py limpiar`, revisar que el DRY-RUN va sobre el ide de su
  parte (si no, **PARA**), `limpiar --ejecutar` y `estado` ⇒ `NO existe parte`; al final
  `git checkout -- prueba_escritura_sigrid.py` y cerrar las consolas.
- **M6 (humano, producción, solo lectura, tras desplegar sv5 → sv4)**: la M4 de F-060 (`grupos
  = 0`) y `$q = @{ database='ruesma'; max_rows=10; parameters=@('partes:%:ciz', <AAAAMMDD>);
  sql='SELECT COUNT(*) AS n FROM hmores WHERE synckey LIKE ? AND fec >= ?' } | ConvertTo-Json`
  ⇒ `n > 0` cuando se aprueben incidencias. Vuelta atrás: §4.

## 10. Documentación

ARCHITECTURE semántica 4 (l.213–237) y `partes-proyecto.md` §3.5 3c (l.216–227), §4.4
(l.516–559: el CIZ del inicio, «un día suelto» deja de ser solo CI*) y variables (l.1007–1008);
`azure-apps/partes.md` paso 3c (l.504–535), contrato (`ciz_mismo_dia`, `partes:<id>:ciz`), «Qué
se rompe» (l.623–635: quien lea `hmores` verá synckeys `partes:<id>:ciz`) y variables
(l.1007–1008, 1020); comentarios de `MOVER_CIZ` en `config/settings.py` de sv4 y sv5. Commit
local en `azure-apps`, sin push.

## 11. Riesgos y alternativas descartadas

- Aprobación desordenada entre peticiones: R11 (`posterior`) la cubre en los dos órdenes; lo
  demás, el aviso `racha_desordenada` de F-060. Un `fin` de otra obra que falla deja el
  `inicio` sin hermano (R2): racha abierta hasta reaprobar, como hoy.
- Hermano en un parte cerrado al llegar el mes siguiente (DA7): más frecuente que en F-060.
- Descartados: dos sentencias en un lote (el corte de 15 puede separarlas); la synckey
  `partes:<X>` en el hermano (rompe idempotencia y F-024); un campo nuevo en vez de
  `racha_registro_ids` en el `inicio` (sv5 solo trata como `fin` lo que es CIZ).

## 12. Decisiones (humano, 2026-10-25, literal: «f62 ok a todo» ⇒ DA1–DA11 = A)

| DA | Pregunta | Alternativas | Recomendación |
|---|---|---|---|
| DA1 | Interruptor y orden | A: el mismo `MOVER_CIZ` (sv4 y sv5): encendido = F-060 + F-062. B: `CIZ_MISMO_DIA` propio en sv4 y sv5 (exige `MOVER_CIZ`; 4 combinaciones más por servicio). C: propio solo en sv4 | **A**; encender sv5→sv4, apagar sv4→sv5 (F-060 sin F-062 no es lo que hace Administración) |
| DA2 | Cómo se escriben CI* y CIZ | A: UNA sentencia de dos filas (§5.4). B: dos sentencias, la del CIZ condicionada a que exista el CI*. C: dos independientes | **A** (B y C pueden partirse entre lotes y dejar el CI* sin CIZ) |
| DA3 | Synckey del hermano y qué guarda sv4 | A: `partes:<X>:ciz`; sv4 guarda el `ide` del CI* (como hoy) y el del CIZ solo viaja en el resultado y el log. B: A + columna `sigrid_ciz_hmores_ide` (esquema en los dos `orm_models.py`) | **A** (sin esquema; se encuentra por synckey) |
| DA4 | Cómo lo encuentra el día siguiente | A: sv5 deriva `partes:<i>:ciz` de cada id de la lista; `decidir_fin` igual; sin `movida_de` (X conserva su CI*). B: sv4 manda las synckeys | **A** |
| DA5 | Inicio con la racha ya escrita delante o con su `fin` en la misma aprobación | A: sv4 manda el tramo delante y `ciz_mismo_dia` falso si el `fin` viaja con él; sv5 no escribe el hermano si hay un CIZ posterior, si ya existe o si hay un CIZ ajeno ese día. B: siempre hermano | **A** (B deja dos CIZ en la racha) |
| DA6 | Rachas abiertas al encender (solo CI*) | A: su siguiente `fin` crea el CIZ (R16 de F-060), nada retroactivo. B: script de relleno de hermanos (otra feature) | **A**; M0 (b) da su número |
| DA7 | CIZ a mover en un parte cerrado | A: `ciz_en_parte_cerrado` (R17 de F-060) y Administración corrige. B: cortar: D abre racha nueva con CI* + CIZ (como los 12 cortes). C: CIZ nuevo en D | **A** (coherente con DA3 de F-060; B cambia R17 y pide decidir el CI* en sv5) |
| DA8 | Desaprobar, papelera o `borrado_sigrid` del día del inicio | A: nada se mueve ni se pone a 0; reaprobar reescribe el CI* y el hermano solo según R10–R13. B: mover el CIZ hacia atrás (DA7 B de F-060) | **A** |
| DA9 | Recurso sin código CIZ | A: solo el CI* y WARNING. B: no escribir la incidencia | **A** (como hoy) |
| DA10 | Cuenta analítica del hermano | A: la del código CIZ, como un `fin`. B: la del CI* | **A** (al moverse ya toma la del CIZ) |
| DA11 | F-019, F-024, F-034, F-046, F-053, avisos y modal | Impacto de §7, sin cambios en esas reglas | **Aceptar §7** |
