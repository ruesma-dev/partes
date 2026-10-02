<!-- progress/current.md -->
# Trabajo en curso

## F-019 · in_progress (2026-10-02), implementer

Rama `feature/F-019-mensuales-a-dedicacion`. Tarea en curso: ver
`specs/F-019-mensuales-a-dedicacion/tasks.md` (las marcadas `[x]` estan
hechas, un commit por tarea). Decisiones y desviaciones: se anotan aqui y
en `progress/impl_F-019.md`.

- T1 hecha: 26 tests de caracterizacion de `ReglasRegistro` en verde
  contra el codigo de hoy, ANTES de tocar `reglas_registro.py`.
- T2 hecha. **Desviacion D1 (interpretacion, no improvisacion)**: R2 y
  R3 bis chocan en una ficha M*+HL*+HE* (hoy inexistente en Sigrid: 0
  recursos M* con HL*). R2 mandaria su ordinaria a dedicacion; R3 bis
  prohibe que algo que hoy se escribe y no es incidencia cambie. Manda
  R3 bis (innegociable del humano transmitido por el lider: «encendido,
  solo cambia omitir->dedicacion e incidencia M* escribir->dedicacion»).
  Test: `test_f019_r3bis_mensual_con_hl_y_he_sigue_escribiendo_ordinarias`.
- T3 hecha. **Desviacion D2**: `resumen.dedicacion` del preflight (R7)
  solo aparece si hay alguna linea a dedicacion. Con la clave siempre
  presente fallaba `test_f002_r4_preflight_del_endpoint_no_escribe`, que
  compara el resumen clave a clave y T12 prohibe tocar tests ajenos; asi,
  con el interruptor apagado el contrato de F-002 queda identico.
- T4 hecha: `DedicacionBandejaOrm` (23 columnas, sin FK, indice
  `(anio, mes)`, server_default en toda NOT NULL) en las dos copias byte a
  byte; guardianes de raiz a seis tablas. Test extra en sv3
  (`test_f019_orm_bandeja.py`) para que la copia de sv3 tenga sus tests.
- T5 hecha. **Desviacion D3**: `dedicacion` NO entra en la tupla
  `ESTADOS_CONGELANTES` (design §4 lo pedia): dos tests ajenos (F-004 y
  F-024) fijan esa tupla literal y T12 prohibe tocarlos. La tupla no la
  usa ningun codigo de produccion; la congelacion de `dedicacion` va en
  `motivo_congelacion_linea/documento` y el guardian F-024 lo compara con
  sv3. Para el bloqueo de borrado definitivo: `vive_fuera` y
  `motivo_borrado_definitivo` (motivo propio para dedicacion).
- T6 hecha: `_upsert_bandeja` + `marcar_registros_sigrid(dedicacion=,
  prueba=, incidencias=)` en la misma transaccion. Decision: el
  `recurso_ide` de la fila es el del resultado de sv5 (pudo resolverlo por
  DNI) y, si no viene, el de la linea; el motivo de la linea no se trunca
  (el codigo `M*` es corto y la columna `codigo_mes` es String(16)).
- T7 hecha: `aplicar_resultado(..., incidencias=)`; el consumidor recibe la
  tabla de clases desde `main.py` (la construye `main()` con
  `construir_tabla_incidencias`, parametro opcional de
  `_componentes_de_cola` para no romper sus tests de F-002); `_trazar` usa
  la tabla del portal. Test de los dos canales marcando igual.

## F-019 · spec_ready (2026-10-02), DA1–DA8 APROBADAS por el humano

spec-author: `specs/F-019-mensuales-a-dedicacion/` en la rama
`feature/F-019-mensuales-a-dedicacion`; resumen en llano en
`progress/spec_F-019.md`. Rigor crítico; servicios sv5 (decide), sv4
(publica en `dedicacion_bandeja`, estado, retirada) y sv3 (ORM gemelo y
congelación). Decisiones abiertas que valida el humano (design §8): DA1
canal (bandeja en base `partes`), DA2 la escribe **sv4, no sv5** (difiere de
la propuesta del líder: sv5 va sin BBDD), DA3 `GRANT SELECT` al rol de
dedicación existente (un rol nuevo sería objeto de servidor), DA4 extras de
`MCAP`+`HECAP` siguen a Sigrid (**excepción a la decisión 2**), DA5 congelar
+ «Retirar de dedicación», DA6 periodo cerrado lo decide dedicación, DA7
sv5, DA8 interruptor `MENSUALES_A_DEDICACION` apagado y sin migración del
histórico. Verificaciones MANUAL M0–M3 en design §10. Aprobadas tal cual el
2026-10-02; el matiz de DA4 (hora mes a porcentajes y HE a Sigrid con
normalidad) queda blindado en R3 bis (no regresión, con RED).

## F-028 · done y DESPLEGADA (2026-10-02), pendiente de M1

APPROVED del reviewer (`progress/review_F-028.md`); resumen en
`progress/history.md`. Mergeada a `dev` (`62c544b`) y desplegada a petición
del humano: sv4 `ca-sv4-front--r20261002122235` (Healthy, 100 % del tráfico,
arranque limpio en Log Analytics).

Rama `feature/F-028-ancho-detalle`, solo sv4. `base.html` admite una clase
extra en el contenedor del `<main>` (bloque `container_class`, vacío por
defecto); `obra_detail.html` y `trabajador_detail.html` usan
`container--ancho` (`styles.css`: `width: calc(100% - 32px)`, sin tope).
Listados y topbar sin cambios. Informe: `progress/impl_F-028.md`. Sin
desviaciones. Sin despliegue.

Pendiente MANUAL (humano, tras desplegar sv4 y Ctrl+F5): **M1** abrir el
detalle de una obra (y el de un trabajador) en la ventana ancha (3440 px) y
comprobar que el contenido ocupa todo el ancho menos 16 px por lado y que no
hay scroll horizontal en la matriz de días ni en la tabla de líneas cuando
caben; un listado (Obras) sigue centrado a 1500 px. Si la tabla de líneas
sale estirada o con scroll por anchos de columna guardados de antes, doble
clic en la manija de la columna los reajusta (O2 del reviewer).

## F-025 · done y DESPLEGADA (2026-10-02), pendiente de verificaciones manuales

APPROVED del reviewer (`progress/review_F-025.md`); resumen en
`progress/history.md`. Mergeada a `dev` (`04ac4fb`) y desplegada a petición del humano: sv4
`ca-sv4-front--r20261002110836`; el log de arranque lista las clases
(H=CIH:dia_completo). azure-apps actualizado por el líder (commit local `6347c60`:
`INCIDENCIAS_PATH` y la regla). Pendientes MANUAL (humano): M1 (lectura en
PG antes de desplegar, requiere firewall) y M2–M5 tras desplegar sv4, con
los pasos de `impl_F-025.md` §6. Clasificación confirmada por el humano
con Administración el 2026-10-02: F día completo y **H (huelga) día
completo** (cambiado respecto a la spec, que la proponía parcial).

## F-022 · done y DESPLEGADA (2026-10-01), pendiente de verificaciones manuales

APPROVED del reviewer (`progress/review_F-022.md`, seis observaciones no
bloqueantes; O4 y O5 dan lugar a F-027); resumen en `progress/history.md`.
Mergeada a `dev` (`5dea576`) y desplegada a petición del humano: sv4
`ca-sv4-front--r20261001210234` (140 sentencias, Uvicorn 8014, revisión
anterior retirada). El aviso de filtrar por obra en la ficha de persona ya
no aplica.
azure-apps: commit local `fdc6e1d` (sin push).

Pendientes MANUAL (humano, design §9; pasos exactos en `impl_F-022.md` §7):
M1 consulta de lectura en PG (¿ya pasó un lote de varias obras?); desplegar
sv4 (solo sv4) y Ctrl+F5; M2–M7 en navegador en modo pruebas (selección,
filtros, ocultas, persona con dos obras, listado y excluidas, muchas filas y
regresión del botón por línea); M8 tras la primera aprobación real de varias
obras. El JS no tiene arnés: lo de navegador solo lo verifica M2–M7.

## F-024 · done y DESPLEGADA (2026-10-01), pendiente de verificaciones manuales

APPROVED del reviewer (`progress/review_F-024.md`); resumen en
`progress/history.md`. Mergeada a `dev` (`93a3eff`) y desplegada a petición
del humano: sv5 `ca-sv5-transfer--r20261001170655` (Uvicorn 8005) y luego sv4
`ca-sv4-front--r20261001170858` (140 sentencias, transfer y sigrid-lookup
CABLEADOS, Uvicorn 8014, revisión anterior retirada). azure-apps: commit local `03f994c` (sin push).

**AVISO OPERATIVO (DA13): ya NO aplica tras el despliegue del 2026-10-01**; era: no usar «Aprobar todo» en
la obra 0719 · 09/2026 ni «Aprobar visibles» en la ficha de sus trabajadores
(reescribiría las 35 líneas que Administración borró a propósito).

Pendientes MANUAL (comandos exactos en `progress/impl_F-024.md`, design §9):
M1 consulta de `registrado` en PG antes de desplegar (requiere firewall);
M2 desplegar sv5 y luego sv4; M3 abrir la obra 0719 en el periodo del
16–28/09 y ver en el log `[comprobacion-sigrid] … borradas=35` sin
`[sigrid-write]`; M4 PG: PT26/00314 con 35 `borrado_sigrid`; M5 navegador
(Reaprobar, botón, sondeo del modal, casilla de borradas: el JS no tiene
tests). Después: M3 de F-023 (reconciliar recursos) y reaprobación por
Administración.

## F-021 · done y DESPLEGADA (2026-10-01), pendiente de verificaciones manuales

APPROVED del reviewer (`progress/review_F-021.md`); resumen en
`progress/history.md`. Mergeada a `dev` (`3e5d85f`) y desplegada a petición
del humano: sv5 `ca-sv5-transfer--r20261001183051` y luego sv4
`ca-sv4-front--r20261001183229` (arranques limpios en Log Analytics).
**M1 hecha por el líder**: 0 líneas `partes:%` en `hmores` (nada que
rellenar). M2 requiere escritura en modo pruebas desde local: solo con
autorización expresa del humano. Observación O1 del reviewer: el docstring de `_resolver_cuentas`
(`registro_pipeline.py:210`) dice que la cola reintenta; no reintenta (sv4
marca las líneas en error hasta que se reaprueban). Corregir en la próxima
feature de sv5.

MANUAL (humano), design §9 — solo lecturas salvo M2 (modo pruebas):

- **M1 · antes de desplegar sv5** (sigrid-api, base `ruesma`, lectura):
  `SELECT h.ano, h.mes, COUNT(*) AS n, SUM(CASE WHEN ISNULL(h.caaide,0)=0
  THEN 1 ELSE 0 END) AS sin_cuenta FROM hmores h WHERE h.synckey LIKE
  'partes:%' GROUP BY h.ano, h.mes`. Esperado: lo que haya escrito sv5
  desde la exploración (0 filas el 2026-10-01); si hay, decidir según DA6.
- **M2 · tras desplegar sv5** (modo pruebas, obra `0404`): aprobar un
  parte con ordinarias, extras y una incidencia de un recurso de la
  empresa 1 y leer `SELECT h.synckey, ah.cod AS hora, c.cod AS cuenta,
  ca.cenide, o.cenide AS cen_obra FROM hmores h JOIN obr o ON o.ide =
  h.obride LEFT JOIN auxhor ah ON ah.ide = h.horide LEFT JOIN con c ON
  c.ide = h.caaide LEFT JOIN caa ca ON ca.ide = h.caaide WHERE h.synckey
  IN (…)`. Esperado: `cuenta` = `<código del centro de 0404>.<subcuenta>`,
  `ca.cenide = cen_obra`; `CI*`/`CIZ` con la subcuenta del tipo por
  defecto. En el log de sv5: `[registro] cuentas obra=0404 ok=…`. Limpiar
  con `prueba_escritura_sigrid.py`.
- **M3 · tras desplegar sv4** (navegador, Ctrl+F5): preflight de un
  recurso cuya subcuenta no tiene la `0404` (consulta en design §9 M3).
  Esperado: bloque «N linea(s) se registraran sin cuenta analitica» en el
  modal y la línea escrita con `caaide = 0`.
- **M4 · Administración**: la línea de M2 se ve en Sigrid con la cuenta
  igual que una tecleada; confirmar DA3 y DA13 (Porsan sin cuenta).

### (histórico) spec escrita, pendiente de aprobación

Spec en `specs/F-021-cuenta-analitica-sigrid/` (rama
`feature/F-021-cuenta-analitica-sigrid`, sin commits). Exploración de solo
lectura en `progress/explore_F-021_sigrid.md`. Toca **sv5** (regla y
escritura) y **sv4** (solo un aviso en el modal del preflight); sv3 no.

Hallazgo: la «cuenta analítica del recurso» **no** es `res.caaide` (0 en
todos); es `reshor.caaide` (recurso × tipo de hora), una plantilla del centro
`00000`. La línea manual lleva en `hmores.caaide` la cuenta **del centro de
su obra** con la misma subcuenta: 99,64 % de coincidencia en la empresa 1 con
respaldo por el tipo de hora por defecto. Porsan (28) no usa cuenta en horas
(0 %). Hoy hay 0 líneas de sv5 en Sigrid: nada que reescribir.

Decisiones a validar (design §8, con recomendación):

1. DA1 · origen `reshor.caaide` del tipo escrito; si no, del tipo por defecto.
2. DA2 · destino: la cuenta del centro de la obra con esa subcuenta.
3. DA3 · sin cuenta ⇒ escribir 0 y avisar solo si la obra no la tiene; no bloquear.
4. DA4 · aviso en el modal del preflight (JS de sv4); alternativa: solo log.
5. DA5 · la partida no interviene.
6. DA6 · sin reescritura de lo ya registrado (M1 lo comprueba antes).
7. DA7 · fallo al leer cuentas ⇒ la petición falla entera.
8. DA8 · sin variable de activación (marcha atrás = revisión anterior).
9. DA9 · `caaide` obligatorio en `stmt_insert_linea`.
10. DA10 · `cuaide` sin escribir; cuentas de baja sin filtrar.
11. DA11 · corregir solo comentarios de `prueba_escritura_sigrid.py`.
12. DA12 · despliegue sv5 → sv4 (cualquier orden es seguro).
13. DA13 · Porsan: nada en código; si la quieren, se rellena `reshor` en Sigrid.

## F-023 · done y DESPLEGADA (2026-10-01), pendiente de verificaciones manuales

Mergeada a `dev` (`27fc03c`) y desplegada a petición del humano, que decidió
desplegar sin esperar a M1 ni M5. Orden de la spec: sv5 primero
(`ca-sv5-transfer--r20261001083016`) y luego sv2 → sv3 → sv4
(`…--r20261001083313`). Arranques comprobados en Log Analytics: sv5 Uvicorn
8005; sv2 catálogo auxhor CABLEADO; sv3 «140 sentencias complementarias»,
Sigrid «todas las empresas», alias del membrete 1 y 28; sv4 «140 sentencias»,
transfer y sigrid-lookup CABLEADOS, Uvicorn 8014; portal responde 302 (Easy
Auth). Hechas por el líder (solo lectura, sigrid-api, base `ruesma`):
**M4 OK** (`0404` solo en la empresa 1) y **línea base de M2**: `PT26` máximo
`00338` en la empresa 1 y `00121` en la 28 antes de cualquier aprobación con
el código nuevo. T17 no se pudo hacer: extensión de Chrome sin conectar.


APPROVED del reviewer en la pasada 2 (`progress/review_F-023.md`); resumen en
`progress/history.md`. Rama `feature/F-023-recurso-alta-empresa`, sin mergear
ni desplegar. Desviación D1 del implementer (el PATCH de obra del portal
resuelve por `ide`) aceptada por el reviewer.

### MANUAL (humano) pendientes de F-023 (design §9 y T17)

1. **M1 · antes de desplegar (lectura, SQL Server vía sigrid-api y PG
   `partes`)**: `ide` de obras gemelas en Sigrid
   (`SELECT con.ide, con.cod, con.emp FROM obr JOIN con ON con.ide = obr.ide
   WHERE con.cod IN (SELECT c.cod FROM obr o JOIN con c ON c.ide = o.ide
   GROUP BY c.cod HAVING COUNT(DISTINCT c.emp) > 1)`) y, con esos ides, en
   `partes`: `SELECT r.obra_ide, d.approved, count(*) FROM parte_registros r
   JOIN parte_documents d ON d.id = r.document_id WHERE d.is_active AND
   r.deleted_at_utc IS NULL AND r.obra_ide IN (…) GROUP BY 1, 2;`
2. **M5 · antes de desplegar sv2**: con sv2 en local, ≥ 10 partes reales
   (≥ 5 de cada empresa): `empresa_membrete` correcto y el resto de la
   cabecera y los empleados igual que su extracción guardada. Anotar en
   `progress/evals_F-023.md` sin nombres ni DNIs.
3. **Despliegue** (lo pide el humano): orden **sv5 → sv2 → sv3 → sv4**
   (`redeploy_partes.ps1 -Solo svN`). Al arrancar sv3/sv4 el DDL
   complementario pasa de 137 a 140 sentencias (log de arranque).
4. **M2 · tras sv5** (lecturas por `POST /api/sql/read` de sigrid-api,
   base `ruesma`; `<OBRA_IDE>`, `<AAAA>`, `<MM>` = obra de la empresa 28 y
   mes del parte aprobado; `$KEY` = function key que el humano saca del Key
   Vault, nunca escrita en ningún fichero). Antes de aprobar, apuntar el
   `PT` máximo de cada empresa con la 2.ª consulta (con `28` y con `1`):
   ```powershell
   $q = @{ database = 'ruesma'; max_rows = 10; parameters = @(<OBRA_IDE>, <AAAA>, <MM>);
     sql = 'SELECT con.ide, con.cod, con.emp, con.tip FROM hmo JOIN con ON con.ide = hmo.ide WHERE hmo.obride = ? AND hmo.ano = ? AND hmo.mes = ? AND ISNULL(hmo.reside, 0) = 0 AND con.tip = 35' } | ConvertTo-Json
   Invoke-RestMethod -Method Post -Uri "$env:SIGRID_API_BASE_URL/api/sql/read" -Headers @{ 'x-functions-key' = $KEY } -ContentType 'application/json' -Body $q
   $pt = @{ database = 'ruesma'; max_rows = 1; parameters = @('PT26/%', 28);
     sql = 'SELECT MAX(cod) AS maxcod FROM con WHERE cod LIKE ? AND emp = ?' } | ConvertTo-Json
   Invoke-RestMethod -Method Post -Uri "$env:SIGRID_API_BASE_URL/api/sql/read" -Headers @{ 'x-functions-key' = $KEY } -ContentType 'application/json' -Body $pt
   ```
   **Esperado**: la 1.ª devuelve UNA fila con `emp = 28` y `tip = 35`; si
   la cabecera la creó sv5, su `cod` es el máximo de la 28 anterior + 1 (la
   2.ª consulta con `28` lo devuelve) y el máximo de la empresa `1` no ha
   cambiado. `truncated` = false.
5. **M3 · tras sv3** (lo lanza el humano): `POST
   <url-de-sv3>/admin/reconciliar-recursos` → `{"ok": true, …,
   "partes_sin_recurso": N}`. Después, en la base `partes` (solo lectura;
   `:dni` = DNI del caso guía, que el humano escribe en la consola y no se
   apunta en ningún fichero):
   ```sql
   SELECT r.recurso_ide, r.parte_estado, (d.approved OR r.sigrid_estado IN ('encolado','registrado')) AS congelada, count(*)
   FROM parte_registros r JOIN parte_documents d ON d.id = r.document_id
   WHERE d.is_active AND r.deleted_at_utc IS NULL
     AND upper(replace(replace(r.empleado_dni,'-',''),' ','')) = upper(:dni)
   GROUP BY 1, 2, 3 ORDER BY 3, 1;
   ```
   y, con los `recurso_ide` que salgan, en Sigrid: `SELECT res.ide, rc.emp,
   rc.fecbaj FROM res JOIN con rc ON rc.ide = res.ide WHERE res.ide IN
   (<ides>)`. **Esperado**: las filas NO congeladas tienen un único
   `recurso_ide`, de `emp = 1` con `fecbaj` 0 (no el dado de baja en 2021),
   y `parte_estado` `ok` o `sin_parte`; las congeladas conservan el que
   tenían.
6. **M4**: el código `0404` (modo pruebas) existe en una sola empresa
   (`SELECT con.emp FROM obr JOIN con ON con.ide = obr.ide WHERE con.cod = '0404'`).
7. **T17 · navegador (sv4, Ctrl+F5)**: los combos de obra y trabajador
   muestran «· empresa N»; en «+ Nuevo» y en «Añadir línea», con obra
   elegida (o fijada por el parte), el combo de trabajador solo ofrece
   fichas de su empresa; elegir la gemela de la 28 en el combo de obra del
   detalle deja esa obra (no la de la 1).

## F-020 · done y DESPLEGADA (2026-09-30), pendiente de verificación manual

Cerrada con APPROVED del reviewer; resumen en `progress/history.md`.
Mergeada a `dev` y desplegada a petición del humano:
`redeploy_partes.ps1 -Solo sv1` → imagen `sv1-partes:latest`
(digest `sha256:06fa219d…`), revisión **`ca-sv1-poller--r20260930150607`**,
`Healthy` y `RunningAtMaxScale`. Arranque limpio en el log: carpetas origen,
Procesados y Errores resueltas, «Pre-checks OK» y primer sondeo del inbox
con `200 OK`. Pendiente del humano (design §10):

1. ~~Merge a `dev` y despliegue de sv1~~ (hecho).
2. Mover **uno** de los cuatro correos del escáner («Attached Image», 17/09 y
   tres del 30/09) de `Errores` a la carpeta origen y marcarlo **no leído**.
3. Logs de `ca-sv1-poller`: `correo adjunto con 1 PDF interior(es)`,
   `Documento logico INGERIDO` (una por página) y `movido a Procesados`; el
   parte (o sus páginas) en el portal.
4. Reprocesar los otros tres igual (la dedup de sv3 por `document.sha256`
   hace inocuo repetir uno ya ingerido).

## Sesión 2026-09-02 · sv5 pasa a MODO NORMAL de escritura en Sigrid

Cambio operativo en Azure, pedido por el humano. No toca código ni features.

```powershell
az containerapp update -n ca-sv5-transfer -g rg-partes-dev `
    --set-env-vars OBRA_PRUEBAS_FORZAR=false
```

Verificado tras el cambio (lecturas reales, no supuestos):

| Comprobación | Resultado |
|---|---|
| `OBRA_PRUEBAS_FORZAR` | `false` |
| `SIGRID_API_DATABASE` | `ruesma` (la base de escritura, no la réplica) |
| Revisión activa | `ca-sv5-transfer--0000002`, 100 % tráfico, 1 réplica, `RunningAtMaxScale` |
| Otras revisiones | ninguna activa |

`OBRA_PRUEBAS_COD=0404` y `MARCA_PRUEBAS=PRUEBA-IA` siguen definidas pero son
inertes con el flag en `false`. **Desde ahora cada parte aprobado en el portal
se registra en SU obra real de Sigrid.**

Del arranque no se pudo leer la línea de Uvicorn: el buffer de
`az containerapp logs show` venía lleno de trazas del SDK de colas y el
arranque ya había pasado. La evidencia válida es la revisión corriendo con su
réplica.

Documentación actualizada en el mismo trabajo: `azure-apps/partes.md`
(commit local `66682f8`, **sin push**).

### Lo que queda pendiente de esto

1. **Limpiar las líneas `PRUEBA-IA` de la obra 0404** que dejó la etapa de
   pruebas. El flag ya no afecta a lo escrito, así que el orden da igual, pero
   la basura sigue en Sigrid:
   `cd services\partes-transfer && python .\prueba_escritura_sigrid.py limpiar --ejecutar`
2. **Revisar si algún parte de la BD `partes` figura como registrado en Sigrid
   cuando en realidad fue a la 0404** (aprobado mientras el modo pruebas estaba
   activo). Ofrecido al humano, aún sin hacer.
3. **Aviso: el `.env` local de sv5 también tiene `OBRA_PRUEBAS_FORZAR=false`.**
   Cualquier prueba lanzada desde local escribe en la obra REAL, al contrario
   de lo que manda `CLAUDE.md` para pruebas locales.

## Sesión 2026-08-25 y anteriores

Sesión 2026-08-25: **F-005 `in_progress`** en `feature/F-005-graphkey-keyvault`
(limpieza documental, ver la sección final). De la sesión anterior
(2026-08-19/20): **F-015 y F-016 `done`**, las dos APROBADAS por el reviewer,
mergeadas, publicadas y **DESPLEGADAS**. **F-014 `blocked`** como deuda
aparcada, pero su puerta ya está abierta (ver abajo).

| Rama | Estado |
|---|---|
| `feature/F-016-admin-empleado-jornada` | mergeada a `dev` y borrada |
| `feature/F-014-candef-9-sigrid` | petición lista, aparcada a la espera de RRHH |

`dev` = merge de F-016 (`5606954`), publicado, con F-015 dentro.

## Despliegue del 2026-08-20 (00:10)

`redeploy_partes.ps1 -Solo sv3,sv4` desde el árbol en `dev`. Ambos servicios en
la revisión **`r20260820000737`**:

| Servicio | Estado comprobado |
|---|---|
| `ca-sv4-front` | `Running`, 1 réplica. Arranque limpio: «esquema inicializado (137 sentencias complementarias)» → `Application startup complete` → Uvicorn en 8014. `HTTP 401` sin cookie ⇒ Easy Auth en pie. |
| `ca-sv3-persistencia` | `ScaledToZero` (KEDA min 0, normal). Su log de arranque **ya está verificado** (2026-08-20 por la mañana): ver la sección siguiente. |

Con esto queda aplicado también el DDL pendiente de **F-010** (M1/M2).

Dos tropiezos, ninguno de código y los dos ya conocidos:

1. `RequestDisallowedByAzure` (MFA) en el primer intento: el `az login` normal
   vale para el build en el ACR pero no para `containerapp update`. Se resuelve
   con el `--claims-challenge` de `infra/README_partes.md:28`.
2. `getaddrinfo failed` de DNS en el **paso final informativo**, ya creadas las
   dos revisiones: solo dejó vacío el «Portal sv4: https://». FQDN real:
   `ca-sv4-front.yellowplant-2add9c3e.spaincentral.azurecontainerapps.io`.

Aprendizaje operativo: `az containerapp logs show --tail` ya no alcanza el
arranque —el polling de colas llena el buffer en minutos—. Los logs de arranque
salen con `az monitor log-analytics query -w <workspace de log-partes-dev>`
filtrando por `RevisionName_s`.

## Verificación del despliegue (2026-08-20, mañana)

Dos verificaciones lanzadas a subagentes. Informes:
`progress/verif_sv3_arranque_20260820.md` y
`progress/verif_esquema_partes_20260820.md`.

### 1. Arranque de sv3 — VERDE

Sin `Traceback`, sin `ERROR` y **sin ningún WARNING de jornada** (ni candef
fuera del mapa, ni fallo leyendo `empleado_jornada`). Esquema inicializado con
**137 sentencias complementarias**, las mismas que reportó sv4. Wiring
correcto: `[jornada][wiring] mapa candef -> jornada semanal: 8:40, 9:42`, más
calendario, Sigrid, SharePoint y consumo de `q-persistencia`. Misma imagen del
despliegue (`sv3-partes:latest`, digest `sha256:b3b533c5…`). Devuelto a **0
réplicas**, confirmado `ScaledToZero`.

Dos aprendizajes operativos:

- **La revisión `r20260820000737` YA había arrancado** entre 22:09 y 22:14 UTC
  de anoche y su log estaba en Log Analytics desde entonces. Forzar réplicas no
  era necesario: antes de hacerlo, mirar si la revisión ya tiene filas en
  `ContainerAppConsoleLogs_CL`.
- **Cada cambio de `--min-replicas` crea una revisión nueva.** La activa ya no
  se llama `r2026…` sino `ca-sv3-persistencia--0000010`. El código se rastrea
  por **digest del ACR**, no por el nombre de la revisión.
- El `az containerapp update` pasó a la primera: el `--claims-challenge` no
  llegó a hacer falta (el humano había reautenticado con MFA en su consola).

### 2. Esquema en PostgreSQL — CONFORME (verificado contra la base real)

Al primer intento el subagente reportó `connection timeout expired` y **acusó
al firewall**. Era un diagnóstico sin evidencia: la IP pública del puesto
(`nslookup myip.opendns.com`) YA tenía regla en `psql-albaranes-rs9k2`, y
`Test-NetConnection ... -Port 5432` responde `TcpTestSucceeded: True` en 0,01 s.
Al reintentar, `psycopg` conectó en 0,1 s con el mismo host, puerto y usuario.
**Lección** (candidata a automejora del arnés): un timeout no basta para
acusar al firewall sin probar antes el TCP crudo.

Verificado contra PostgreSQL 16.14, base `partes`:

- **19/19 columnas** en `empleado_jornada`: nombre, orden ordinal, tipo,
  nulabilidad y `DEFAULT` coinciden con el ORM y con la spec.
- **`ix_empleado_jornada_dni_norm`** presente sobre `(dni_norm)`, no único, más
  la PK con secuencia. **Cero CHECKs**, que es lo correcto: F-015 §6 delega esas
  validaciones a la aplicación (F-016/R27).
- **M1 de F-010 ✅**: `ix_parte_registros_deleted_at_utc` presente, recuentos
  exactos **7/47/56/7**, `ux_parte_documents_sha256_active` intacto. Ninguna
  tabla ganó ni perdió columnas.
- **Base ↔ sv3 ↔ sv4 coinciden**: las dos copias del ORM siguen byte-idénticas
  y cuadran con la base. Control cruzado: 118 + 19 = **137 sentencias**, justo
  lo que loguearon los dos servicios.
- **4 filas de prueba** de las pruebas en navegador, **ya desactivadas** por el
  humano: `origen='manual'` ✅ y `created_by`/`updated_by` **NULL** ✅, que es
  lo esperado sin `DEFAULT_REVIEWER` (H1) y confirma ese hallazgo desde la base.

**R7 VERIFICADO** (2026-08-20, segunda vuelta). Alta en pantalla con último
día incluido `2026-07-31`: la base guarda **`hasta = 2026-08-01`** y el listado
repinta `2026-07-31`. La conversión «+1 día» funciona. Confirmado por partida
doble con una fila de control (último día `2026-08-20` → `hasta = 2026-08-21`),
y una tercera fila «sin fin» cubre la mitad NULL del requisito.

`desde` sin desplazamiento de huso en las tres. Se sostiene porque `desde` y
`hasta` son **`varchar(16)`** con la fecha ISO, no `date`/`timestamp`: no hay
capa que pueda reinterpretar la zona horaria.

**R12 (solapes) sin violación**: las tres filas se solapan en julio pero solo
una está activa; la auditoría muestra que el humano desactivó cada una antes de
crear la siguiente (baja 11:31:16 → alta 11:31:42), así que el alta **no debía**
rechazarse. La rama de rechazo sí se ejercitó, pero en la prueba anterior de
navegador (el aviso rojo nombrando la fila en conflicto), no en estas filas —
lógicamente no deja rastro en la base, porque no llega a crear nada.

### 2-bis. (histórico) el falso bloqueo por firewall

No se pudo consultar la base real: la IP pública del puesto no figura en
ninguna regla de `psql-albaranes-rs9k2` (`connection timeout expired`). **No se
tocó nada del servidor**, que es compartido. Queda pendiente de que el humano
añada la regla (`datamart-puesto-pgris-<fecha>`) y se relance; el SQL exacto
está listo en el informe, incluida la **M1 de F-010**.

Lo verificable sin base salió **CONFORME**: 19 columnas declaradas, índice
`ix_empleado_jornada_dni_norm` sobre `(dni_norm)` declarado, y las **dos copias
de `orm_models.py` (sv3 y sv4) byte-idénticas** — el defecto que F-010 vino a
arreglar sigue sano. `ddl_complementario()` genera 137 sentencias, 19 de ellas
de `empleado_jornada`: **cuadra con el log de arranque de los dos servicios**.

Sin CHECKs de horas 0–24 ni de vigencias en la base, y eso es **correcto**: la
spec los pone en la aplicación (F-016/R27), no en el schema.

Dos correcciones que salieron de aquí:

- **Errata en `specs/F-015-jornada-semanal-candef/design.md` §8**: dice «las 16
  columnas». La tabla normativa §6, el ORM y el guardián dicen **19**. El texto
  está mal, no el código. Pendiente de corregir.
- **F-010 no tiene «migraciones M1/M2»**: M1/M2/M3 son sus *verificaciones
  manuales*. M2/M3 se dan por cumplidas con las 137 sentencias; **M1 sigue
  pendiente** (índice `ix_parte_registros_deleted_at_utc` y los recuentos
  7/47/56/7) y necesita acceso a la base.

### 3. Pruebas en navegador (2026-08-20, humano) — SUPERADAS

Las 6 verificaciones de `specs/F-016-admin-empleado-jornada/design.md` §8.2 y
el punto de KPI de **F-015 T12**, hechas por el humano contra el portal
desplegado. **Todo funciona.** Combo de trabajador (la 6, que ningún test
cubre): busca por nombre y por DNI, y el alta guarda el DNI elegido. Alta con
DNI ficticio: sale el aviso de R19 y la fila se crea igual. Solape: rechazado
nombrando la fila en conflicto, sin crear nada. Contigua: aceptada. El
listado enseña el `hasta` **inclusivo**, no el interno.

Tres hallazgos, ninguno de ellos un fallo del código desplegado:

**H1 · `DEFAULT_REVIEWER` NO está configurada en el Container App de sv4.**
Comprobado en Azure: la variable no existe en la plantilla del contenedor, y
`.env.example` la declara vacía. El helper `_actor`
(`services/partes-front/interface_adapters/web/app.py:477`) lo contempla —
«sin `DEFAULT_REVIEWER` configurado se sella `NULL` y la operación NO falla»—
y la plantilla pinta `—`. Consecuencia que va más allá de F-016: **los once
puntos de auditoría del portal (`approved_by`, `deleted_by` y las cuatro
entradas de `undo_log`) llevan sellando NULL desde el primer despliegue**. La
auditoría del portal está en blanco, no «firmada con un genérico».
Reordena el enunciado de **F-017**: no es «pasar del valor genérico al usuario
real», es que hoy no hay ni genérico. **DECIDIDO por el humano el 2026-08-20**:
NO se configura un `DEFAULT_REVIEWER` provisional; se espera a **F-017**. El
NULL dice «no se sabe», que es la verdad, y un genérico crearía un tramo de
filas que luego habría que explicar.

**H2 · El KPI de jornada se resuelve con el PRIMER DÍA DEL PERIODO MOSTRADO,
no con hoy** (`app.py:698`, decisión consciente de R25). El periodo que sale
por defecto es el más reciente **con registros de ese trabajador**. Efecto
práctico: se creó una excepción con `desde` = hoy y **el KPI no la reflejaba**;
tampoco con `desde` = 1 del mes en curso. Con `desde` = 2026-01-01 apareció al
instante. Le pasó al humano, que conoce el sistema: **a un administrador le
parecerá que la pantalla no funciona**. No es un bug —la caché se invalida
bien y sv4 tiene una réplica— pero es deuda de usabilidad real. Candidatas:
avisar en la pantalla, o resolver el KPI con `hoy` cuando la excepción esté
vigente hoy.

**H3 · Hueco de borde**: si el trabajador **no tiene ningún registro**, la
ficha no construye calendario, y entonces el KPI se calcula con `date.today()`
pero pasando `excepcion=None` — ignoraría una excepción vigente hoy. En esa
rama la fecha y la excepción dejan de ir juntas. Menor, pero es una
incoherencia real.

**LIMPIEZA**: las pruebas dejaron filas en `empleado_jornada` de la BASE REAL,
incluida una de **un trabajador real** con vigencia desde 2026-01-01 y 42
h/sem. Hay que dejarlas todas `inactiva` (esta pantalla no borra, por diseño).

## F-017 · done, APROBADA y lista para mergear (2026-08-21)

Identidad real de Easy Auth en sv4. Resumen en `progress/history.md`; detalle
en `progress/impl_F-017.md`, `progress/mutacion_F-017.md` y
`progress/review_F-017.md`.

Verificado por el reviewer re-ejecutando: **1.057 tests** en sv4 + 138 en la
raíz, cobertura **99,3 %**, mutación **32/32 muertos, 0 supervivientes, 0
timeouts**. Solo sv4, cero cambios de schema. Primera vuelta RECHAZADA con
tres defectos, los tres corregidos y verificados —el guardián ampliado lo
comprobó **rompiéndolo**—.

**MERGEADA Y DESPLEGADA el 2026-08-21.** La ambigüedad que la spec no podía
cerrar **queda cerrada a favor de lo diseñado**. `GET /whoami` en el portal
desplegado devuelve:

```json
{"actor":"<upn del usuario>","origen":"cabecera-name",
 "entorno":"desplegado","senal_despliegue":"CONTAINER_APP_NAME",
 "cabeceras_easy_auth":["X-MS-CLIENT-PRINCIPAL-NAME",
                        "X-MS-CLIENT-PRINCIPAL",
                        "X-MS-CLIENT-PRINCIPAL-ID"]}
```

- Azure inyecta el **UPN**, no el display name: la apuesta de DA3 era correcta.
- Manda `cabecera-name`; el suplente base64 no hace falta.
- R5c detecta el entorno por la **señal A** (`CONTAINER_APP_NAME`), como
  confirmó T0. La señal B (haber visto una cabecera) no llegó a necesitarse.

**HALLAZGO PARA F-018**: Easy Auth inyecta también
**`X-MS-CLIENT-PRINCIPAL-ID`**, que es el **`oid` inmutable** del usuario.
F-017 dejó por escrito que no guardaba el `oid` «porque no hay columna y no se
va a inventar una», remitiendo a F-018 — y ahora sabemos que **el dato está
disponible en una cabecera dedicada**, sin decodificar el token. Si F-018 crea
la tabla de auditoría, puede llevar `actor` (legible) y `actor_id`
(inmutable) sin coste extra: es la diferencia entre una auditoría que aguanta
un cambio de nombre y otra que no.

**Verificación que queda**: aprobar algo en el portal y comprobar que
«Aprobado por» ya sale con el usuario real.

**Aviso para F-018**: su borrador vive en el worktree
`worktree-agent-ad862e62640d64553` y **heredó el criterio del corte SIN la
excepción de `undo_log.actor`**. Hay que refrescarlo contra `dev` después de
mergear, antes de darlo por bueno.

## Cierre de sesión · 2026-08-21

Trabajo hecho hoy, todo commiteado en `dev` (**`git push origin dev` PENDIENTE**):

1. **Verificación completa del despliegue del 2026-08-20** (sv3 y sv4, esquema
   con las 19 columnas, M1 de F-010, las 6 de F-016 §8.2, KPI de F-015, R7 y
   R12). Sin nada abierto.
2. **F-017 done, mergeada, desplegada y verificada en producción.**
3. **F-005 revisada** contra Azure: su primer objetivo ya estaba cumplido.
   **Pendiente de decisión del humano**: cerrarla o reescribirla como retirada
   de `graphkey_nobom.json`.
4. **F-009 eliminada** por decisión del humano; su lista de automejoras sigue
   viva en este fichero, sin feature propia.
5. **F-018 dada de alta**, con spec redactada **en un worktree sin integrar**.

### Por dónde seguir, en orden

1. `git push origin dev`.
2. Comprobar en el portal que **«Aprobado por» ya sale con el usuario real**
   (única verificación que queda de F-017).
3. **Integrar la spec de F-018** desde `worktree-agent-ad862e62640d64553`
   (commit `eee9d53`), refrescándola antes contra `dev`: heredó el criterio del
   corte SIN la excepción de `undo_log.actor`, y tiene material nuevo (el `oid`
   de `X-MS-CLIENT-PRINCIPAL-ID`). Luego `git worktree remove`.
4. ~~Decidir sobre **F-005**~~ — hecha y cerrada el 2026-08-25.
5. Cuando toque: el **correo de F-014 a RRHH**. La actualización del arnés ya
   no está pendiente: va por la 1.7.3.

## Lo que el humano tiene que decidir o hacer

1. **Verificaciones del despliegue**: las 6 de F-016 §8.2 y el KPI de F-015
   **SUPERADAS** en navegador el 2026-08-20 (sección anterior). Quedan: el
   contraste contra la BASE (`origen`, `is_active`, `created_by` y que el
   `hasta` sea un día después del escrito) y la **M1 de F-010**, los dos a la
   espera de la **regla de firewall** de `psql-albaranes-rs9k2`; el «último
   laborable 6 h» con `candef = 9` de verdad, que no llega hasta F-014; y la
   **limpieza** de las filas de prueba.
   Decisión pendiente: qué hacer con `DEFAULT_REVIEWER` (H1).
2. **Enviar la petición de F-014 a RRHH**: la condición ya se cumple (F-015
   desplegada). Texto aprobado en `progress/peticion_F-014.md`.
3. **F-017** (identidad real de Easy Auth): **spec escrita el 2026-08-20**, a
   la espera de aprobación del humano. Ver la sección «F-017 · spec escrita»
   más abajo. Mientras no exista, todas las filas de auditoría del portal
   siguen sellando `NULL` (H1).
4. **Dos dudas abiertas de F-016** (`design.md` §13): los tres normalizadores
   de DNI equivalentes de sv4 (¿feature de limpieza aparte?) y si las filas con
   `origen` `sigrid`/`sesame` serán editables cuando existan.
5. **Automejoras del arnés** acumuladas (lista abajo), ya sin feature propia:
   F-009 se eliminó el 2026-08-20 por decisión del humano. Varias con evidencia
   medida. Destino previsto: portarlas a `arnes-base` al actualizar el arnés.

## F-015 · done, en `dev` (2026-08-19)

Jornada del día por jornada semanal derivada del candef y último día laborable.
Resumen en `progress/history.md`; detalle en `progress/impl_F-015.md`,
`progress/mutacion_F-015.md` y `progress/review_F-015.md`.

Verificado por el reviewer: 1.195 tests, cobertura **99,4 %** (520/523),
mutación **259/237/22/0** (91,5 %). Regresión cero: con `candef = 8` —que hoy
son todos— no cambia el comportamiento de nadie. Por eso se puede desplegar
sin F-014.

## F-016 · done, en `dev` y desplegada (2026-08-19/20)

Pantalla `/admin/jornadas` en sv4: crear, editar, cerrar, desactivar y
reactivar las excepciones de jornada. Resumen en `progress/history.md`; detalle
en `progress/impl_F-016.md`, `progress/mutacion_F-016.md` y
`progress/review_F-016.md`.

Verificado por el reviewer ejecutando y recalculando: 799 tests en sv4 (134
nuevos) + 92 en la raíz, cobertura **98,5 %** (326/331), mutación **93/79/14/0**
(85 %). Cero cambios de schema, cero ficheros fuera de sv4, cero rutas nuevas
de catálogo, cero `DELETE`.

## F-014 · DEUDA IMPORTANTE, aparcada (2026-08-19)

Decisión del humano: no es crítico, lo ejecuta RRHH en Sigrid y lleva tiempo;
él avisará. La petición está redactada y **APROBADA** en
`progress/peticion_F-014.md` (rama `feature/F-014-candef-9-sigrid`), con un ⛔
en la cabecera.

**El orden importa**: primero F-015 desplegada, después el correo. Aplicar el
`candef = 9` en Sigrid con sv3/sv4 sin F-015 daría **−3 h/semana** de extra
negativa a esos 7 recursos; al revés no pasa nada. **Desde el despliegue del
2026-08-20 esa condición se cumple**: el correo ya se puede enviar en cuanto el
humano quiera.

Cuando se retome: enviar el correo (§7) → RRHH cambia el `candef` de 7 fichas y
el DNI de `MO/0037` → responde qué decide con `MO/0007` (de alta pero sin
partes desde 2026-02-04) → ejecutar V1/V2/V3 en solo lectura → segunda revisión
→ `done` → merge.

Hallazgos que no conviene perder: los códigos `MO/NNNN` **no identifican una
sola ficha** (bajo MO/0006, MO/0007 y MO/0008 hay homónimas de alta, misma
categoría, misma hora por defecto y también con `candef = 8`: solo las separa
`res.ide`); `MO/0031` tiene dos fichas de alta que registran en 2026 y ahí
desempata la categoría; y `MO/0037` sigue sin DNI (`res.conide = 0`).

## F-017 · spec escrita (2026-08-20), pendiente de aprobación

`specs/F-017-identidad-easy-auth/` con los tres ficheros. **Solo sv4**: se
comprobó que sv5 ya acepta el campo `usuario` (`Optional[str]`) y **solo lo
loguea** — no llega a ninguna columna de Sigrid, así que empezará a registrar
un nombre real sin un cambio de código. Cero cambios de schema: las siete
columnas de autor ya existen y la más estrecha es `String(120)`
(`undo_log.actor`, `empleado_jornada.created_by`/`updated_by`,
`empleado_alias.created_by`); un UPN cabe de sobra y el helper trunca a 120 de
una vez para todos.

**Ocho decisiones que el humano tiene que aprobar o rebatir** (detalle y
argumentos en `design.md` §11):

| # | Decisión propuesta |
|---|---|
| DA1 | Manda `X-MS-CLIENT-PRINCIPAL-NAME`; el token base64 es el suplente y **nunca** puede lanzar |
| DA2 | Se guarda el **UPN**, no el `oid`: la columna la leen personas (`parte_detail.html`, `admin_jornadas.html`) y no hay dónde meter el `oid`. Identidad inmutable ⇒ F-018 |
| DA3 | El actor se normaliza a **minúsculas** (los UPN son insensibles a mayúsculas; si no, un `GROUP BY` cuenta dos personas donde hay una) |
| DA4 | **ENMENDADA por el humano el 2026-08-20 y ya incorporada.** El fallback tiene **dos ramas**: sin desplegar ⇒ `local:<DEFAULT_REVIEWER>` / `local:sin-identidad`; **desplegado y sin cabecera ⇒ `sin-identidad`, sin prefijo, con WARNING por petición**. Motivo: escribir `local:` en producción no sería «honesto», sería **afirmar un origen falso** y taparía una caída de la autenticación en una columna. La operación se completa igual en las dos ramas |
| DA4 bis | Se distingue el entorno **sin variable nueva ni tocar Azure**: `CONTAINER_APP_*` presente **o** haber visto ya una cabecera de Easy Auth desde el arranque (segunda señal, red de seguridad de la primera). ⚠ **Supuesto de plataforma NO verificado en este repo**: nadie lee esas variables hoy ⇒ **T0 es una puerta** que lo comprueba con `az containerapp exec … printenv` **antes** de implementar, y si no aparecen, `blocked` y se consulta |
| DA5 | `DEFAULT_REVIEWER` se queda con el nombre, cambia el significado: pasa a ser la etiqueta de la sesión local. Renombrarla obligaría a tocar Azure para nada |
| DA6 | El test `test_f016_r13_auditoria` **se pone rojo a propósito** (T4, es la evidencia de que `_actor` manda) y se repara **fabricando la cabecera**, no parcheando el helper: `_actor` es una clausura dentro de `build_app` y no hay nada que `monkeypatch` alcance |
| DA7 | Las filas que escribe **sv3** (ingesta automática) NO se tocan: ahí el autor es el pipeline, no una persona |
| DA8 | **Aprobado por el humano.** `GET /whoami` devuelve actor, **por qué rama salió** (`cabecera-name` / `cabecera-token` / `local` / `sin-identidad-desplegado`), `entorno`, la señal que lo prueba y los **nombres** de las cabeceras presentes (nunca valores). Con la enmienda gana papel: es el único sitio donde se comprueba la detección de entorno **sin escribir una fila** |

**Filas históricas**: no se reescribe ni una (R22). Con H1 la decisión sale
más barata de lo previsto — no hay genéricos que traducir, hay `NULL`, que ya
dice la verdad. Y como a partir de la feature **siempre** hay actor (R7), el
corte queda exacto y gratis: `autor IS NULL` ⇔ «anterior a F-017». Se
documenta en `docs/referencia/partes-proyecto.md` (T10) con un hueco
`⛔ PENDIENTE: fecha de despliegue` que **rellena el humano al desplegar**.

**Ambigüedades encontradas que conviene que el humano sepa:**

0. **La enmienda mete un riesgo nuevo, y es el único de la feature que
   ensucia datos**: si en Azure no existieran las `CONTAINER_APP_*`, el
   portal se creería local y firmaría filas de producción como `local:…` —
   justo la mentira que la enmienda quiere evitar. El fallo es asimétrico
   (creerse desplegado en local es inocuo: `sin-identidad` + WARNINGs en un
   puesto de trabajo). Mitigado por tres vías: **T0** lo comprueba antes de
   implementar (y si falla, `blocked`), el arranque lo loguea, y la segunda
   señal lo corrige en cuanto entra el primer usuario autenticado. Aun así,
   el humano debe saber que la detección de entorno pasa a ser **una pieza
   con peso en la auditoría** que antes no existía.
1. **No está verificado que Azure inyecte `-NAME`** con el UPN: en local no
   existe la cabecera y en el repositorio no hay ni una referencia a
   `X-MS-CLIENT-PRINCIPAL`. Puede llegar el *display name*. No es un fallo
   (identifica igual) y `/whoami` lo resuelve en un minuto (M1), pero el
   humano debe saber que el valor exacto que acabará en la columna **no se
   puede confirmar hasta desplegar**.
2. **Alcance colateral no acotado del todo**: siete ficheros de tests de
   F-002/F-003/F-004 configuran `DEFAULT_REVIEWER="ana"` y alguno comprueba
   ese valor. **T1 los inventaría antes de tocar nada** en vez de descubrirlos
   a mitad, pero el número final de tests a ajustar no se sabrá hasta ese
   inventario.
3. **`docs/referencia/partes-proyecto.md` §5.4 está desactualizado**: dice que
   `created_by`/`updated_by` llevan `DEFAULT_REVIEWER`. Con H1 sabemos que
   llevan `NULL`. Se corrige en T10.
4. **`.env.example` de sv4 no está versionado** (el `.gitignore` ignora
   `*.example`), igual que pasó con `JORNADAS_ADMIN_ENABLED` en F-016: la
   documentación efectiva de `DEFAULT_REVIEWER` va al docstring y a
   `azure-apps/partes.md` (T11).
5. **Aviso para F-008**: esta feature confía en el texto en claro de la
   cabecera porque lo que decide es una *anotación*, no un permiso. Un **rol**
   leído igual sí sería una decisión de permiso y ahí esa confianza deja de
   ser gratis (`design.md` §8).

## Orden del backlog

1. **F-017** — identidad real de Easy Auth en sv4 (`pending`, prioridad 8).
   **Spec escrita** en `specs/F-017-identidad-easy-auth/` (2026-08-20), a la
   espera de que el humano apruebe las ocho decisiones DA1–DA8. Los once
   puntos exactos, verificados de nuevo contra el árbol: `app.py` líneas
   1675, 1769, 1804, 1859, 1862, 2279, 2305, 2319, 2338, 2348 y 2559.
2. **F-014** — `blocked`, solo la desbloquea RRHH.
3. F-005 GRAPH_KEY→KV · F-006 tipo_hora ext · F-007 prompt sv2 + evals ·
   F-008 roles · F-011 jornada reducida
   (última; fuente candidata `empleado_jornada` + `emphis.porjorlab`).

## MANUAL pendiente del humano (acumulado)

- **F-016 (NUEVO)**: las 6 verificaciones de
  `specs/F-016-admin-empleado-jornada/design.md` §8.2, con el portal levantado
  y PostgreSQL. La 6 (comportamiento del combo de trabajador en el navegador)
  no la cubre ningún test.
- **F-015 · T12** (desplegado el 2026-08-20; los logs de esquema de sv4 **y de
  sv3** ya están comprobados, los dos con 137 sentencias y sin errores): la tabla
  `empleado_jornada` con sus **19** columnas y el índice
  `ix_empleado_jornada_dni_norm`; un trabajador de la cuadrilla con viernes de
  6 h **sin** aviso de jornada incompleta y el KPI «9 h · 42 h/sem · último
  laborable 6 h»; y que un parte ya aprobado **no**
  cambie su desglose tras la primera pasada de sv3. Ojo: la cuadrilla sigue con
  `candef = 8` hasta F-014, así que ese punto solo se ve del todo después.
- **F-010:** M2/M3 cumplidas (137 sentencias en sv3 y sv4). **M1 pendiente**:
  índice `ix_parte_registros_deleted_at_utc` y recuentos 7/47/56/7, a la espera
  de la regla de firewall de PostgreSQL.
- **F-014**: la puerta ya está abierta (F-015 desplegada el 2026-08-20); queda
  enviar la petición cuando el humano decida.
- **F-002 (Azure):** validar en navegador la aprobación asíncrona (⏳ encolado →
  ✓ PT26/…, obra 0404 en modo pruebas), limpiar 0404 (`python
  prueba_escritura_sigrid.py limpiar --ejecutar` en sv5) y pasar sv5 a modo
  normal (`az containerapp update -n ca-sv5-transfer -g $RG --set-env-vars
  OBRA_PRUEBAS_FORZAR=false`).
- **F-003:** encendido cuando sesame-api esté desplegado (P2) — variables
  SESAME_* en sv3 y sv4 a la vez + secreto `sesame-api-key` en kv-partes. Ojo:
  encender contra URL muerta bloquea aprobaciones por diseño.
- **F-004:** 7 comprobaciones en navegador con Ctrl+F5 (pasos al final de
  `progress/impl_F-004.md`).
- **F-013:** validar el Excel `services/partes-front/logs/
  festivos_por_trabajador_2026.xlsx` (no versionado): Alicante 8/21 y
  asignaciones por centro.
- **sesame-api (otro repo, del humano):** commitear el árbol P2 (incluye el fix
  `daysOff` del 2026-08-18), desplegar, doc en azure-apps (P3);
  `contract_not_found` → 404 en vez de 502.
- **Sesame HR (RRHH):** completar el calendario Alicante; contratos vacíos
  (0/218) — decidir si se cargan.
- **Cambio de modelo Gemini** en sv2 (comando dado; actualizar
  `infra/create_capps_partes.ps1:38`).

## Automejoras del arnés pendientes (⇒ genéricas a `arnes-base`)

> **F-009 se eliminó de `harness/features.json` el 2026-08-20** por decisión
> del humano. Esta lista NO desaparece con ella: sigue siendo el registro de lo
> que hay que portar a `arnes-base`. Varios puntos (1, 2, 3 y 7) son de la
> campaña de mutación y **probablemente ya vengan resueltos en el arnés
> 1.6.0**, que la rehace entera; confirmarlo con
> `progress/analisis_arnes_1.6.2.md` antes de implementar ninguno.
>
> Los **dos puntos originales de F-009**, que NO son de mutación y se habrían
> perdido al borrar la ficha, se conservan aquí:
>
> - **C4 bis**: cuando un fichero del alcance con muchas líneas cambiadas
>   genera **0 mutantes**, exigir evidencia alternativa (fase RED específica
>   sobre ese fichero).
> - **C3/C4 + `init.sh`**: cruzar los imports nuevos de terceros del diff
>   contra el `requirements.txt` del manifiesto de despliegue del servicio que
>   los importa. Habría cazado en automático el crash-loop de `azure-*` de
>   F-002.

1. **La más rentable, confirmada con datos por F-015 y anotada desde F-010**:
   `harness/mutacion.py` ejecuta solo la suite del servicio dueño del fichero
   mutado, así que **el guardián de una copia gemela nunca mata mutantes**
   (vive en `tests/` de la raíz). Fueron **27 de los 48 supervivientes** de la
   2.ª campaña de F-015, todos falsos «equivalentes». Arreglo: ejecutar también
   la suite de la raíz (~4 s aquí) o, mínimo, avisar cuando el fichero mutado
   tenga copia gemela declarada en `CLAUDE.md`.
2. **El presupuesto de mutación por mutante es engañoso** (F-015): con 16
   evaluadores y una suite de ~80 s, el timeout de 120 s de `rigor.json`
   convirtió 100 mutantes en «timeout», que **no es una medición**. Debería
   escalar con la concurrencia o avisar cuando los timeouts pasen de un umbral.
3. **`progress/mutacion_*.md` debería registrar qué suite se ejecutó** por
   fichero (reviewer de F-016): sin eso, en una feature que toque dos servicios
   el hueco de (1) no se detecta sin recalcular.
4. **C4 de `CHECKPOINTS.md` podría pedir un recuento mecánico
   test-por-requisito** sobre los nombres `test_fXXX_rN_*`, en vez de fiarse de
   la tabla de trazabilidad de la spec (reviewer de F-016).
5. **Checkpoint para features cuyo entregable es una petición a un tercero**
   (reviewer de F-014): clave unívoca verificada, apartado «qué NO se toca»,
   verificación escrita ANTES con control de daños, resultado esperado en TODOS
   los escenarios, barrido de datos sensibles porque el documento sale del
   repositorio.
6. **Generalizar «si el entregable es una medición, el reviewer la re-ejecuta
   en vez de leerla»** (reviewer de F-014): es lo que destapó su defecto D1.
7. **Desconfiar por defecto de los supervivientes de una copia duplicada**, en
   `.claude/agents/reviewer.md` (reviewer de F-015).
8. **Fixture de app compartida en sv4** (deuda transversal, no del arnés): la
   suite pasó de ~52 s a ~114 s porque cada test de endpoint levanta `build_app`
   entera. Patrón heredado de F-002/F-003/F-004.

Las anteriores de F-013 (AM-1..3), F-004 y F-010 siguen en `history.md`.

## Notas de contexto

- **Deuda detectada el 2026-08-19**: `services/partes-front/
  consulta_reshor_recursos.py` tiene 4 DNIs y nombres de personas reales
  **hardcodeados y versionados** (líneas 27-31) y apunta a una ruta `.env` de
  otro repositorio. Pendiente de decisión del humano.
- **`JORNADAS_ADMIN_ENABLED` no está en ningún fichero versionado**: el
  `.gitignore` de sv4 ignora `*.example`. Default `True` en el código y
  documentada en `azure-apps/partes.md`. No es un olvido: el implementer evitó
  un `git add -f` y el reviewer le dio la razón.
- F-013 (2026-08-18): 218 empleados; festivos OK (Madrid 196, Tomares 15,
  Sevilla 4, Málaga 2, Alicante 1 parcial); contratos en Sesame: NINGUNO ⇒
  jornada/reducida sin fuente en Sesame; F-011 repriorizada a baja por eso.
- F-012 (2026-08-18): decisiones firmes del humano sobre la jornada semanal, ya
  implementadas por F-015.
- azure-apps es un repo git LOCAL sin remoto (decisión del humano); no proponer
  push.

---

## F-017 · Identidad real de Easy Auth (sv4) — pendientes del humano

Rama `feature/F-017-identidad-easy-auth`. Implementación terminada (T0–T14),
suite en verde, **pendiente de review**. Informe: `progress/impl_F-017.md`.

### ⚠ DECISIÓN PENDIENTE — R14/R15 nombran una columna que nadie escribe

Verificado contra el árbol al implementar T6 (y coincide con lo que encontró
el agente de F-018 por su cuenta):

- `undo_log.actor` **existe pero no la escribe nadie**: `_record_undo` ni
  siquiera acepta un actor.
- Las cuatro operaciones de R14/R15 —los tres borrados y el alta manual—
  **no generan ninguna fila de `undo_log`**. Solo la generan las ediciones.
- `crear_parte_manual` **acepta `by=` y lo ignora**: el parámetro no aparece
  en su cuerpo.

Lo implementado es lo que manda `design.md` §5.2: entregar `_actor(request)`
por el parámetro `by=`. Para los tres borrados eso llega de verdad a
`deleted_by`; para el alta manual se queda en la puerta del repositorio.

**No se resolvió por cuenta propia**, y el motivo es que las dos salidas
posibles se salen del alcance aprobado:

| Salida | Por qué se paró |
|---|---|
| Que los borrados escriban en `undo_log` | Hay que **crear** filas de historial que hoy no existen: payload de restauración, `undo_last` sabiendo deshacerlas y entradas nuevas en el widget de deshacer. Es funcionalidad nueva, y un log de acciones es **F-018** |
| Que `crear_parte_manual` use su `by=` | **No hay dónde escribirlo**: ni `parte_documents` ni `parte_registros` tienen columna `created_by` (solo la tienen `empleado_alias` y `empleado_jornada`). Exigiría **columna nueva** ⇒ cambio de schema en las dos copias gemelas del ORM ⇒ prohibido por la spec y por `CLAUDE.md` |

**Consecuencia que hay que conocer**: el criterio del corte (`autor IS NULL`
⇔ «anterior a F-017») vale para las columnas de autor que sí se escriben,
**no para `undo_log.actor`**, que seguirá siempre a `NULL`. Queda dicho así,
sin redondear, en `docs/referencia/partes-proyecto.md` §5.7 punto 3.

### Verificaciones MANUAL pendientes

- **M1 bis — YA EJECUTADA en T0 (2026-08-20), resultado POSITIVO.** Las cuatro
  variables `CONTAINER_APP_NAME` / `_REVISION` / `_REPLICA_NAME` / `_HOSTNAME`
  **existen** en `ca-sv4-front`. La señal A de R5c es un hecho verificado, no
  un supuesto; no hace falta la alternativa `ENTORNO=produccion`.
  Comprobado **sin volcar el entorno**, una variable por invocación:
  `az containerapp exec -n ca-sv4-front -g rg-partes-dev --command "printenv CONTAINER_APP_NAME"`
  (ídem con las otras tres). **No usar `printenv` a secas**: vuelca los
  secretos resueltos desde Key Vault.
- **M1 — tras desplegar.** Abrir `https://<fqdn de ca-sv4-front>/whoami` con
  la sesión de Entra iniciada y comprobar tres cosas: `actor` es el correo/UPN
  de quien mira, `origen` es `cabecera-name` y `entorno` es `desplegado`.
  Lecturas posibles:
  - `origen = cabecera-token`: la cabecera `-NAME` no llega y el suplente hace
    su trabajo. Correcto, pero **anótalo**.
  - `origen = sin-identidad-desplegado`: Easy Auth no inyecta nada.
    **Incidente**: la feature funciona (no miente), pero la autenticación del
    portal está rota. Parar y avisar.
  - `origen = local` o `entorno = local`: la detección de R5c ha fallado en
    Azure y el portal estaría firmando filas de producción como locales.
    **Parar y avisar de inmediato**: es el único fallo de esta feature que
    ensucia datos. El campo `senal_despliegue` dice qué se buscó.
- **M2 — tras desplegar.** Aprobar un parte de prueba desde el portal y
  comprobar en la base `partes`:
  `SELECT id, approved_by, approved_at_utc FROM parte_documents WHERE approved_at_utc IS NOT NULL ORDER BY approved_at_utc DESC LIMIT 5;`
- **M3 — tras desplegar.** Borrar una línea de prueba y comprobar:
  `SELECT created_at_utc, action, actor FROM undo_log ORDER BY id DESC LIMIT 5;`
  **Ojo**: por lo dicho arriba, `actor` saldrá `NULL` y el borrado **no**
  generará fila de `undo_log`. La comprobación útil hoy es sobre
  `parte_registros.deleted_by`.
- **M4 — antes y después de desplegar.** Que las filas anteriores sigan
  intactas (R22): el número debe ser **el mismo** las dos veces:
  `SELECT count(*) FROM parte_documents WHERE approved_at_utc IS NOT NULL AND approved_by IS NULL;`

M2, M3 y M4 necesitan la regla de firewall de `psql-albaranes-rs9k2` que ya
está pendiente más arriba en este mismo documento.

### Otros pendientes de F-017

- **La fecha del corte la rellena quien despliegue.**
  `docs/referencia/partes-proyecto.md` §5.7 tiene el hueco marcado como
  `⛔ PENDIENTE: fecha de despliegue`, y
  `tests/test_f017_r23_corte_documentado.py` se pondrá **rojo** cuando se
  cambie, a propósito: obliga a actualizar el test en el mismo trabajo.
- **`DEFAULT_REVIEWER` cambia de significado, no de nombre**: ya no es «quién
  firma el portal» sino la etiqueta de la sesión local (`local:<valor>`).
  Sigue sin estar configurada en Azure y **no hace falta configurarla**.
- **Nota para F-018** (aviso recibido del coordinador, no aplicado aquí a
  propósito): si F-018 llama a `_resolver_identidad` más de una vez por
  petición, saldrán varios WARNING de R5b. Hoy no ocurre —cada endpoint pide
  el actor una sola vez—, así que memoizar sería resolver un problema que aún
  no existe. Cuando F-018 lo necesite, son tres líneas en
  `_resolver_identidad` y no cambia ninguna firma.

---

## Actualización del arnés: 1.4.0 → 1.7.2 (2026-08-21)

Rama `chore/arnes-1.7.2`, sin push. Origen: `arnes-base` (payload 1.7.2 del
2026-08-21). Ejecutado `instalar_arnes.ps1 -Modo actualizar`; los seis ficheros
«adaptados» se restauraron a la versión de `partes` y las novedades genéricas
se portaron a mano, bloque a bloque. Backup del instalador en
`%LOCALAPPDATA%\arnes-base\backups\partes\20260821-232232` (16 ficheros).

**Qué entra**: puerta de tamaño del papeleo (`harness/tamano.py`, sección
7 quater de `init.sh`), `BACKLOG.md` generado desde `features.json`
(`harness/backlog.py`, sección 3 bis), centinela de campaña de mutación en
curso (sección 1 bis), motor de mutación de la 1.6.0–1.7.2 (línea base que no
puede mentir, mutación de `is`, sin envenenar el árbol con bytecode,
`--ficheros`, dimensionado automático de timeout y workers), reglas RM1–RM6 del
reviewer en `CHECKPOINTS.md` y 16 tests nuevos del arnés en `tests/`.

**Qué se conservó de `partes`**: las tres adaptaciones de `init.sh`
(`REQUIERE_ENV=0`, cabeceras de las secciones de configuración y 9), el punto
C4 de dominio de `CHECKPOINTS.md` (empleado ≠ recurso, incidencias, schema
duplicado), `docs/CONVENTIONS.md` entero (la plantilla no cambió desde 1.4.0) y
todo el contenido propio de `CLAUDE.md`. Los cuatro agentes de `.claude/agents/`
no tenían adaptación local: se comprobó antes de dejar que el instalador los
pisara.

**Rigor**: `nivel_por_defecto` pasa de `critico` a `estandar`, pero **las 17
features declaran su nivel explícitamente**, así que ninguna cambia de
exigencia. Lo que sí cambia de aquí en adelante: las campañas de nivel
`estandar` van **muestreadas a 20 mutantes con semilla fija** (`--max-mutantes 0`
para la campaña entera) y sus números **no son comparables** con los de
campañas anteriores. Tampoco lo son los tiempos: desde la 1.7.2 el timeout por
mutante se deriva de la línea base medida.

**Verificado**: `bash harness/init.sh` en verde con el arnés v1.7.2 — 401 tests
pasados (138 antes de la actualización) y 1 saltado, servicios sv3/sv4/sv5 en
verde por caché, `BACKLOG.md` generado. `python -m harness.mutacion --estado` y
`python -m harness.tamano --feature F-018` responden bien.

**Pendiente / sabido**: `ruff` sube de 468 a 496 avisos, los 28 nuevos en el
código del arnés recién entrado (deuda del genérico, no bloquea). Nada que
propagar de vuelta a `arnes-base`: esta actualización solo consume.

## Actualización del arnés: 1.7.2 → 1.7.3 (2026-08-25)

Rama `chore/arnes-1.7.3`. Correctivo de la puerta de tamaño que estrenó la
1.7.0: la sección 7 quater medía también el papeleo de features **`done`**, y
una feature cerrada que declara la rama base como suya dejaba el portero en
rojo permanente en `dev`. El snippet descarta ahora la ficha si su `status` es
`done` y el N/A lo dice con sus palabras. Encontrado en `porcentajes`, no aquí:
en `partes` ninguna feature declara `dev` o `main` como rama, así que el
portero nunca llegó a ponerse rojo por esto.

Toca `harness/init.sh` (portado a mano, conservando las tres adaptaciones de
`partes`), `tests/test_tamano.py` y `harness/VERSION`. Verificado:
`bash harness/init.sh` en verde con v1.7.3, 402 tests pasados y 1 saltado.

## F-005 · GRAPH_KEY en Key Vault: constancia de la comprobación (2026-08-25)

Rama `feature/F-005-graphkey-keyvault`. Feature de **limpieza documental**
(`sdd: false`, rigor `documental`): **no se toca código de producción**. Queda
aquí la constancia que pide su criterio A4.

### Lo comprobado contra Azure (solo lectura, sesión de `pgris@ruesma.es`)

| Fecha | Qué se comprobó | Resultado |
|---|---|---|
| 2026-08-20 | Los **tres** servicios que usan Graph (`ca-sv1-poller`, `ca-sv3-persistencia`, `ca-sv4-front`) | `GRAPH_KEY` llega como `secretref:graph-key`, y el secreto de la Container App es una **referencia** a Key Vault (`keyVaultUrl` informado), **no una copia**. Ningún valor en claro. |
| 2026-08-25 | El secreto `GRAPH-KEY` en el Key Vault de `rg-partes-dev` (`$KV`) | **Existe y está habilitado**. Creación y última actualización: `2026-06-22T13:59:10+00:00`. |

sv5 no usa Graph. Es decir: el objetivo original de la feature —sacar la
credencial de las variables de entorno en claro— **ya estaba cumplido de
hecho** antes de abrirla; lo que quedaba era la limpieza.

### Lo comprobado en el árbol

- **Ningún script de `infra/` lee `graphkey_nobom.json`.**
  `add_secrets_partes.ps1` pide el JSON por consola con
  `Read-Host -AsSecureString` y lo sube con `az keyvault secret set`, sin
  tocar disco. `create_capps_partes.ps1:63,73`, `create_sv1_poller.ps1:44,49`
  y `create_sv4_front.ps1:41,62` montan `GRAPH_KEY=secretref:graph-key` sobre
  un `keyvaultref` resuelto con la identidad gestionada `id-partes-dev`.
- **Nunca entró en git**: `git log --all -- infra/graphkey_nobom.json` no
  devuelve nada, y sigue cubierto por `.gitignore:15`.
- **Borrado del disco** el 2026-08-25 (criterio A1). El valor vive en el Key
  Vault, ya verificado arriba.

### HALLAZGO H1, RESUELTO: la segunda copia del secreto en disco

`infra/partes-infra.zip` (33 KB, del 2026-07-26, **no versionado**, cubierto
por la regla `*.zip` del `.gitignore`) contenía dentro `graphkey_nobom.json`
con `tenant_id`, `client_id` y un `client_secret` no vacío. Comprobado sin
imprimir los valores: 32 entradas, una foto de `infra/` del 2026-06-22, y todo
lo demás que llevaba está en git en versiones más nuevas.

**Borrado el 2026-08-25 por decisión del humano**, entero. En el árbol no
queda ningún rastro de `graphkey*` (`find . -name "graphkey*"`, vacío), así
que el objetivo real de A1 —que la credencial de Graph no esté en claro en el
disco— sí está conseguido.

### F-005 · CERRADA, APROBADA por el reviewer (2026-08-25)

Ronda 1: `CHANGES_REQUESTED` por **dos frases falsas** en documentación —el
defecto que esta feature existía para eliminar—. `README.md` atribuía
`PG-PASSWORD` a `add_secrets_partes.ps1` (la carga `fase1_infra_partes.ps1:151`)
e `infra/README_partes.md` decía que el script «solo conoce el nombre del
secreto, nunca su valor» (el valor viaja en `az keyvault secret set --value`).
Corregidas en `ad770be` y `861c0d1`, más `65430cd` en `azure-apps`. El
implementer encontró además que **su propio informe repetía las dos frases** en
las tablas de A2 y A3, y las arregló ahí también.

**La puerta de tamaño del arnés 1.7.3 mordió por primera vez** en este
repositorio: `progress/review_F-005.md` salió a 151 líneas contra un tope de
140 y dejó el portero en KO. El implementer NO lo recortó —recortar el informe
de quien te revisa para que tu entrega salga verde es justo lo que la puerta
impide—; lo recortó el reviewer a 140/140 y lo commiteó (`0d7fd31`).

Veredicto final **APROBADO** (`progress/review_F-005.md`). Verificaciones
independientes del reviewer que conviene no perder: barrido de `git ls-tree`
sobre **todos** los commits alcanzables (el nombre `graphkey_nobom.json` no
aparece en ningún árbol de la historia), barrido de secretos sobre el diff
completo `dev...HEAD` (cero hallazgos) y contraste línea a línea de cada
afirmación de los documentos contra los scripts de `infra/`.

`bash harness/init.sh` en verde: 402 pasados / 1 saltado, cobertura N/A por
nivel `documental` con su motivo impreso, puerta de tamaño 206/220 y 140/140.

Dos cosas que el reviewer deja apuntadas y **no** entran aquí:

- **Deuda preexistente**: `add_secrets_partes.ps1` pasa el secreto por
  `--value`, que lo deja visible en la línea de comandos del proceso. Se
  arreglaría con `--file` o con `Az.KeyVault`.
- **Automejora del arnés (genérica ⇒ `arnes-base`)**: que `CHECKPOINTS.md`
  obligue, en nivel `documental`, a que cada afirmación de un documento sobre
  cómo se ejecuta algo cite el fichero y la línea que la respalda. Aquí todo
  pasó en verde y el defecto era una frase falsa.
