# F-024 · Exploración (solo lectura, 2026-10-01)

Autor: explorer. Fuentes: código de sv4/sv5 en la rama
`feature/F-024-lineas-encoladas`; Sigrid por `POST /api/sql/read` de
sigrid-api (base `ruesma`, cliente de sv3 `SigridApiClient._post_sql_read`,
sin abrir ni imprimir el `.env`); Log Analytics (`ContainerAppConsoleLogs_CL`,
retención visible desde el 2026-09-01); blobs `transfer/peticiones/*.json` y
`transfer/resultados/*.json` del storage de partes (lectura con
`--auth-mode login`). Ninguna escritura. Sin nombres, DNIs ni UPNs: los
recursos van con alias (R-A, R-B, R-C); el mapa alias→`res.ide` está en el
scratchpad de la sesión (`f024/mapa_recursos.txt`), fuera del repo.

Leyenda: **[HECHO]** comprobado con datos; **[HIPÓTESIS]** inferencia sin
prueba directa.

## 0. Resumen en cinco líneas

1. **Sigrid NO vacía `synckey`.** sv5 escribió 35 líneas con
   `synckey='partes:<id>'` el 30/09 y las volvió a encontrar por `synckey`
   ese mismo día (lectura posterior a la escritura y `ya_registradas` a los
   4 y 9 minutos). **Después alguien BORRÓ esas 35 líneas**: hoy no existe
   ninguno de sus `ide` en `hmores`. [HECHO]
2. Por eso hay 0 líneas con `synckey` en Sigrid: eran las únicas de sv5 en
   obras reales, y ya no están. [HECHO]
3. **El portal dice «registrado en PT26/00314» de 35 líneas que NO están en
   Sigrid** (horas del 16 al 28/09 de tres recursos de la obra 0719).
   Ese es el problema de rigor crítico, no el «encolado». [HECHO en Sigrid
   y logs; el estado en PG está por confirmar, §5]
4. El «encolado» de la captura casa con una **vista vieja**: la línea HLOF se
   reaprobó sola a las 10:46:03 UTC, el modal recarga la página al cerrar
   (antes de que vuelva el resultado) y el resultado llegó a las 10:46:12.
   Todos los resultados del 30/09 volvieron y se aplicaron. [HECHO los
   tiempos; HIPÓTESIS que la captura sea de esa ventana]
5. Quién borró y cómo: **no determinable** con lo accesible (Sigrid no
   tiene auditoría de líneas; sigrid-api no tiene Application Insights
   visible). [HECHO que no hay rastro]

## 1. Pregunta 1 · `synckey` en Sigrid

### 1.1 Recuentos y esquema [HECHO]

| Medida | Valor |
|---|---|
| `hmores` total | 331.709 filas (`MAX(ide)` 408.207) |
| `hmores.synckey` NULL / no vacío / `LIKE 'partes:%'` | 0 / 0 / 0 → **todas `''`** |
| `hmo` total; `synckey` no vacío | 6.889; 0 |
| `dca` con `synckey` no vacío | 0 |
| Tipo de columna (`INFORMATION_SCHEMA`) | `hmores.synckey`, `hmo.synckey`, `dca.synckey`: `varchar(128)`, NULL permitido, sin default. `con` no tiene `synckey` |
| Triggers (`sys.triggers`) | 0 filas (puede ser falta de permiso de metadatos del usuario de lectura; `sigrid_api.md` afirma «Sigrid no tiene triggers») |
| `hmores` con `tex` que contenga `PRUEBA-IA` | 0. La obra 0404 no tiene líneas en 2026 |

Diccionario (`azure-apps/sigrid_tablas.md`): `synckey` = «Clave externa de
sincronización», texto de 128, en `hmo`, `hmores` y varias tablas de
documentos. No dice que la aplicación lo vacíe. Única pista de uso propio:
sigrid-api, al **copiar** cabeceras de albarán, resetea `dca.synckey = ''`
(`create_purchase_albaran_use_case.py`, `create_direct_albaran_use_case.py`);
es decir, la aplicación lo trata como clave que no debe heredarse, no como
algo que borre después.

`hmores` **no tiene campos de auditoría** (ni fecha/usuario de alta o
modificación). `con` tiene `tiemod` (fecha OLE).

### 1.2 Lo que sv5 escribió y lo que hay ahora [HECHO]

Logs de `ca-sv5-transfer` (todo septiembre) + blobs de resultado: sv5 solo
escribió el **30/09**, en 7 peticiones de cola de un único aprobador, todas
contra la obra **0719** y el parte existente **PT26/00314** (`hmo.ide`
2.832.224; sv5 no lo creó: `creado=false`):

| Petición (UTC) | Líneas | Escritas | Ya | Omitidas | `hmores.ide` devueltos |
|---|---|---|---|---|---|
| 78595a3b 10:41:57→10:42:08 | 1 (reg. 2354, R-A, 16/09, HLOF 8 h) | 1 | 0 | 0 | 408.069 |
| 6797a04e 10:42:08→10:42:09 | 1 (reg. 2355, R-A, 16/09, HEOF 1 h) | 1 | 0 | 0 | 408.070 |
| d7b7e172 10:46:04→10:46:08 | 1 (reg. **2354** otra vez) | 0 | **1** | 0 | — |
| 235f8c25 10:51:30→10:51:37 | 44 | 30 | **2** (2354, 2355) | 12 | 408.071–408.100 |
| 554e237a 11:09:50→11:09:58 | 1 (CIE, R-C, 28/09) | 1 | 0 | 0 | 408.103 |
| 6e47cf92 11:24:28→11:24:37 | 1 (HEOF, R-A, 28/09) | 1 | 0 | 0 | 408.126 |
| 5c7c9d61 11:24:42→11:24:43 | 1 (CIM, R-A, 28/09) | 1 | 0 | 0 | 408.127 |

- Cada `INSERT` se registró con sus parámetros (`[sigrid-write]`), incluida
  la `synckey` `partes:<registro_id>`; `filas` afectadas = escritas en las
  cinco escrituras.
- Los `hmores_ide` del resultado salen de `lineas_por_synckey` **después**
  de escribir (`registro_pipeline.py:394-399`): si la `synckey` no se
  hubiera guardado, vendrían vacíos. Vienen rellenos en las 35.
- `ya=1` (10:46) y `ya=2` (10:51) solo son posibles si `lineas_por_synckey`
  encontró `partes:2354` y `partes:2355` en Sigrid.
- 12 omitidas: todas de R-C, «el recurso no tiene código de hora extra».
- **Hoy**: `SELECT COUNT(*) FROM hmores WHERE ide BETWEEN 408069 AND 408100
  OR ide IN (408103,408126,408127)` → **0**. Los huecos de `ide` actuales
  son exactamente `[408069-408100]`, `[408103]`, `[408126-408127]`; los
  vecinos (408.067-068, 408.101-102, 408.104, 408.125, 408.128) existen y
  son de otros partes. Ninguna línea de PT26/00314 tiene `pos ≥ 19200`
  (sv5 escribió con `pos` 19.200–21.376).

Conclusión: **las 35 líneas se borraron enteras** entre el 30/09 11:24 UTC y
la lectura del 01/10 por la mañana (la exploración de F-021 ya vio «0 líneas
de sv5»). La hipótesis «Sigrid vacía `synckey`» queda **descartada**; la de
«se borraron» queda **probada**. Ninguna reapareció tecleada a mano (§1.4).

### 1.3 PT26/00314 hoy [HECHO]

- Cabecera: `con.emp` 1, `tip` 35, `est` 1, `fec` 20260930,
  `con.tiemod` = 2026-09-08 16:19 (no cambió al borrar las líneas: o el
  borrado no toca `tiemod`, o no se hizo desde la ficha del parte), obra
  0719, `hmo.reside` 0.
- 56 líneas, `ide` 405.150–407.279, `pos` 12.480–19.136, fechas 01/09–30/09,
  20 recursos. **Todas con `caaide` ≠ 0** (sv5 escribe `caaide=0`: ninguna es
  de sv5), `synckey` vacía, 1 con `tex` («AGOSTO»), `verifec1`/`fecext` a 0.
  El `max_pos` que leyó sv5 a las 10:42 (19.136) es el máximo de hoy: las 56
  ya estaban antes de las escrituras de sv5.
- Líneas HLOF/HEOF de PT26/00314: solo del 01/09 al 15/09. **Ninguna del
  16/09 en adelante.** Ningún duplicado (mismo recurso/día/código).

### 1.4 El trabajador y el día de la captura [HECHO]

- Registro 2354 (HLOF 8 h) y 2355 (HEOF 1 h), recurso R-A, 16/09/2026.
- En Sigrid hoy: **0 líneas** de R-A el 16/09 (en ningún parte). R-A tiene 15
  líneas en PT26/00314 (06/09–15/09) y 1 HEOF el 26/09 en otro parte (obra
  0676-B), que no es ninguna de las escritas por sv5.
- R-B (recurso **de baja desde 2021-01-26**, misma persona que R-B', de alta)
  recibió de sv5 HLOF/HEOF del 16 al 25/09; hoy R-B no tiene ninguna línea
  en septiembre y R-B' solo tiene HLOF/HEOF del 01/09 al 15/09. Es el caso
  que motivó F-023 (recurso de baja); sv5 aún no tenía F-023 el 30/09.
- R-C: sus CIE/CIM del 28/09 tampoco están.

## 2. Pregunta 2 · Qué dijo sv5 [HECHO]

- Septiembre, `ca-sv5-transfer` (revisión `--0000002` hasta el 01/10 06:30
  UTC, luego `--r20261001083016`): 87 líneas relevantes de log. Antes del
  30/09 solo hay dos `preflight` del 17/09 (obra 0713, `omitir=1`, sin
  escritura). Ninguna `Traceback`, `FALLO` ni `ok=false`.
- Escrituras: las de la tabla §1.2, todas `committed` (si no, `escribir`
  lanza). Resultado devuelto por `q-transfer-result` para las 7 peticiones
  (blob `resultados/<id>.json` presente para las 7, `ok: true`).
- sv4 (`ca-sv4-front`): para cada petición, `[transfer-cola] encolada` →
  `[repo] N linea(s) marcadas como encoladas` → `[transfer-result]
  peticion_id=… ok=True lineas_marcadas=N` con **N igual al número de
  líneas de la petición** (1, 1, 1, 44, 1, 1, 1). Fuera del 30/09 no hay
  ninguna aprobación en septiembre ni el 01/10, ni avisos `[poison]`.

## 3. Pregunta 3 · Por qué una línea en «encolado» y la otra con PT26/00314

### 3.1 Lo que NO es [HECHO]

- No es un resultado perdido ni en `-poison`: los 7 resultados se aplicaron
  (§2). Ojo: la **lectura de colas da 403** al usuario (`az storage message
  peek`, falta rol de datos de cola); no me he dado permisos. Los logs bastan
  para descartar poison en estas 7 peticiones.
- No es que sv5 omita una línea sin estado: `ReglasRegistro.decidir` da una
  acción a **todas** (`escribir`/`omitir`/`ya_registrado`) y el resultado las
  devuelve todas (escritas, omitidas, ya, pendientes). Coincide con los
  recuentos.
- No hay otro camino que ponga `encolado`: solo `marcar_registros_encolado`
  (`parte_repository.py:1356`), llamado solo desde `aprobar_encolar`.

### 3.2 Lo que encaja [tiempos HECHO; que sea la captura, HIPÓTESIS]

La captura (HEOF «PT26/00314», HLOF «encolado», mismo trabajador y día) es
exactamente el estado de los registros 2354/2355 entre **10:46:03 y
10:46:12 UTC** del 30/09:

1. 10:41:56 se aprueba solo el HLOF (2354) → encolado; resultado 10:42:12.
2. 10:42:09 se aprueba solo el HEOF (2355) → encolado; resultado 10:42:12.
3. 10:45:19 preflight de 2354 (dice «ya registrada»); 10:46:03 se **reaprueba
   2354** → `marcar_registros_encolado` lo pasa de `registrado` a
   `encolado` (y borra su motivo y sobreescribe fecha/autor de registro).
4. Al cerrar el modal «Registro encolado», `app.js:2936-2941` hace
   `window.location.reload()` **al instante**, sin esperar el resultado
   (~9 s): la página recargada pinta 2354 «encolado» y 2355 «PT26/00314».
   No hay refresco automático: la vista queda así hasta que el usuario
   recarga.
5. 10:46:12 llega el resultado (`ya=[2354]`) y sv4 vuelve a poner
   `registrado` (rama `ya_registradas`, que acepta estados en vuelo).

El texto del correo («si ya lo habíamos llevado a Sigrid, igual que el de
abajo») encaja con alguien que reaprueba una línea porque la vio «encolada»
tras la primera aprobación (paso 1: la recarga es inmediata). Ninguna otra
ventana del 30/09 deja HLOF encolado y HEOF con código a la vez (en la
petición de 44 iban las dos).

### 3.3 Defectos de diseño que salen de aquí (para la spec)

- **D1** El portal permite reaprobar líneas `registrado` (congeladas) y las
  pasa a `encolado`. Inocuo si el resultado vuelve, pero si ese resultado
  acabara en `-poison`, una línea que SÍ está en Sigrid quedaría
  «encolada» indefinidamente y congelada.
- **D2** El modal de cola recarga antes de que haya resultado y no hay
  sondeo: el usuario ve «encolado» y no sabe si recargar (el texto lo dice,
  pero la recarga automática lo contradice).
- **D3** El preflight dice «ya registrada» pero el botón deja encolar igual.

## 4. Pregunta 4 · Consecuencias si la línea de Sigrid desaparece o pierde `synckey`

### 4.1 Lo que pasa hoy con el borrado [HECHO en código; estado PG por confirmar]

- **El portal miente**: 35 registros (`parte_registros.id` 2352-2353,
  2354-2355, 2358-2361, 2413-2415, 2468-2471, 2526-2529, 2584-2587,
  2641-2643, 2696-2697, 2784-2785, 2804-2806, 2919-2920) figuran
  `registrado` con `sigrid_parte_cod='PT26/00314'` y un
  `sigrid_hmores_ide` que ya no existe. Nadie lo detecta: no hay
  conciliación portal↔Sigrid.
- **F-004 los congela**: `registrado` congela siempre, también tras
  desaprobar; el portal no deja editarlos («para corregirla hay que eliminar
  la línea en Sigrid y volver a aprobarla»: justo lo que ya pasó, salvo el
  «volver a aprobarla»).
- **Reaprobar sí los recupera**: sin `synckey` en Sigrid no hay
  `ya_registrado`; sin líneas del mismo recurso/día/código no hay conflicto
  → se escriben de nuevo. Con F-023 ya desplegada, las de R-B saldrían
  `omitido` («recurso de baja») y sv4 las marcaría `omitido` (la rama de
  omitidas no respeta veredictos finales), lo que permite corregir el
  recurso tras desaprobar.

### 4.2 Si la línea siguiera ahí pero sin `synckey` (escenario original de la hipótesis)

- Idempotencia (paso 6): falla; la línea no es «ya registrada».
- Conflictos (paso 7): la protegen, porque `lineas_existentes` busca por
  parte+recurso+día y el filtro `not (ls.synckey and ls.synckey in mias)`
  la cuenta como ajena → `pendientes_confirmacion` → la línea queda
  `conflicto` (por cola) en vez de duplicarse. Pisar la borraría y
  reescribiría: sin duplicado, pero con un borrado que sobra.
- Duplica si además cambió el recurso, el día o el código de hora en Sigrid,
  o si la línea se movió a otro parte del mes (solo se mira el `hmo` de la
  obra+mes).
- `hmores_ide` post-escritura vacío; reentregas de `q-transfer`
  (reintentos/poison reencolado) ya no serían «inocuas por synckey»
  (`cola_cliente.py:107,144`), aunque el paso 7 las frenaría como conflicto.

### 4.3 Duplicados hoy [HECHO]

- Partes por los que pasó sv5 en septiembre: solo PT26/00314 → **0**
  duplicados (mismo recurso/día/código).
- Global septiembre 2026 (orientativo, todo manual): 4 grupos mismo
  hmo/recurso/día/código/cantidad (4 sobrantes); 19 grupos mismo
  hmo/recurso/día/código HL%/HE% sin mirar cantidad. Ninguno en un parte
  tocado por sv5. No hay líneas de sv5 en Sigrid, así que **hoy sv5 no ha
  generado ningún duplicado**.

## 5. Pregunta 5 · Consultas pendientes en PostgreSQL `partes`

No hay regla de firewall para el puesto (los agentes no la crean). Cuando el
humano la abra, solo lecturas:

```sql
-- a) Estado actual de los 47 registros distintos aprobados el 30/09
--    (35 escritos, de ellos 2354/2355 reaprobados como «ya», y 12 omitidos).
SELECT r.id, r.fecha_int, r.tipo_hora, r.hora_codigo, r.sigrid_estado,
       r.sigrid_parte_cod, r.sigrid_hmores_ide, r.sigrid_registrado_at_utc,
       left(r.sigrid_motivo, 60) AS motivo, d.approved
FROM parte_registros r JOIN parte_documents d ON d.id = r.document_id
WHERE r.id BETWEEN 2350 AND 2920 AND r.sigrid_registrado_at_utc >= '2026-09-30'
ORDER BY r.id;

-- b) ¿Queda algo en vuelo en todo el portal? (esperado: 0)
SELECT sigrid_estado, count(*), min(sigrid_registrado_at_utc)
FROM parte_registros WHERE deleted_at_utc IS NULL
GROUP BY 1 ORDER BY 1;

-- c) Todos los `registrado` con su referencia en Sigrid, para cruzarla
--    después con `SELECT ide FROM hmores WHERE ide IN (...)` por sigrid-api.
SELECT r.id, r.sigrid_parte_cod, r.sigrid_hmores_ide
FROM parte_registros r
WHERE r.deleted_at_utc IS NULL AND r.sigrid_estado = 'registrado'
ORDER BY r.sigrid_hmores_ide NULLS FIRST;
```

Esperado: a) 2354 y 2355 en `registrado` (no `encolado`), las 35 con
`hmores_ide` 408.069–408.127; c) ningún `hmores_ide` de c) existe hoy en
Sigrid (salvo registros anteriores a septiembre, si los hubo).

## 6. Lo que no se pudo saber

- **Quién y cómo borró las 35 líneas.** Sin auditoría en `hmores`;
  `con.tiemod` del parte no cambió; sigrid-api (`func-sigridapi-dev-huyke`)
  no tiene Application Insights en la suscripción visible y su workspace no
  está en el de partes; `prueba_escritura_sigrid.py limpiar` solo borra en
  la 0404 por `tex='PRUEBA-IA'` y `porcentajes-transfer` solo borra por
  `ide` de conflictos confirmados. **[HIPÓTESIS]** borrado manual en Sigrid
  (seleccionar las líneas del final del parte, todas de sv5 y con `pos`
  contiguos) por Administración, quizá al ver horas en un recurso de baja.
  Hay que **preguntarlo a Administración** antes de diseñar: si borrar lo
  que escribe el portal es un uso legítimo, F-024 necesita conciliar.
- Si la captura es de las 10:46:03–10:46:12: lo dirá la hora del correo
  original o la consulta a) (si 2354 está `registrado`, era vista vieja).
- Colas: lectura denegada (403); no comprobado el contenido actual de
  `q-transfer-poison`/`q-transfer-result-poison` (los logs no muestran
  ningún mensaje que llegara a poison en septiembre).

## 7. Implicaciones para la spec (orientativo, no decidido)

1. Antes de F-021 no hace falta tocar la escritura: la `synckey` funciona.
2. El hueco real es **conciliación**: detectar `registrado` cuyo
   `sigrid_hmores_ide` (o `synckey`) ya no existe en Sigrid y avisar /
   desmarcar para poder reaprobar. Servicios: sv5 (lectura por lote de
   `ide`/`synckey`) y sv4 (estado y vista); sin escrituras nuevas en Sigrid.
3. UX de cola (D1-D3): no reaprobar `registrado`, no recargar antes de
   tiempo o sondear el resultado, y respetar el «ya registrada» del
   preflight.
4. Decidir con el humano qué hacer con las 35 de la 0719 (reaprobar tras
   F-023, o dejarlas fuera si Administración las borró a propósito).
