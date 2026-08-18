<!-- docs/ARCHITECTURE.md -->
# Arquitectura · partes (monorepo)

> Este documento es NORMATIVO: el spec-author diseña contra él y el
> reviewer rechaza lo que lo incumpla. Si no está aquí, no es un requisito.
> El documento maestro del dominio, con todo el detalle, es
> `docs/referencia/partes-proyecto.md`; este fichero destila lo normativo.

## Qué hace este proyecto

Los encargados de obra envían por correo (`partes@ruesma.es`) los partes
diarios de trabajo en papel escaneado (PDF). El sistema los captura (sv1),
extrae las líneas con IA (sv2), las concilia contra los maestros de Sigrid
y las persiste en PostgreSQL (sv3), ofrece un portal de revisión y
aprobación para Administración (sv4) y registra las líneas aprobadas en el
ERP Sigrid como partes mensuales de mano de obra (sv5). Desplegado como 5
Container Apps en `rg-partes-dev` (spaincentral).

## Capas y estructura

Monorepo: cada servicio en `services/<nombre>` con arquitectura hexagonal
idéntica — `domain/` (modelos y ports, sin dependencias externas),
`application/` (pipelines + steps con objeto de contexto; la composición se
hace en el punto de entrada), `infrastructure/` (adaptadores: Azure, Graph,
Gemini, PostgreSQL, sigrid-api), `interface_adapters/` (api o web),
`config/settings.py` (pydantic-settings sobre `.env`). Python 3.12,
Pydantic v2, FastAPI donde hay HTTP.

Puntos de entrada: `main.py` en todos; sv2 y sv3 tienen además
`main_worker.py` (bucle de cola, KEDA). Comunicación entre servicios:
sv1→sv2→sv3 por colas de Azure Storage (`q-extraccion`, `q-persistencia`,
at-least-once); sv4↔sv5 por **doble canal** (ver más abajo);
sv3/sv4/sv5→Sigrid solo a través de `sigrid-api` (Function App). No hay
librería compartida: los servicios se acoplan únicamente por mensajes,
HTTP y la BBDD `partes`.

### El doble canal sv4 ↔ sv5 (F-002)

Aprobar una obra × mes entera son cientos de líneas: por HTTP síncrono
bloqueaba al usuario minutos y rozaba los cortes del balanceador. Por eso
conviven dos caminos, y cuál se usa depende de lo que la acción necesita:

- **Cola `q-transfer`** para el grueso del registro. sv4 sube el payload
  al contenedor `transfer` (`peticiones/<id>.json`) y encola solo la
  referencia —un mensaje de Storage Queue no llega a 64 KB—; responde en
  cuanto está encolado y deja las líneas en `sigrid_estado='encolado'`.
- **Cola `q-transfer-result`** de vuelta: sv5 publica el veredicto por
  línea (`resultados/<id>.json`) y un hilo daemon de sv4 lo vuelca en las
  columnas `sigrid_*`. Va por cola, y no escribiendo sv5 en PostgreSQL,
  para que sv5 siga sin BBDD y la duplicación de `orm_models.py` no crezca
  a una tercera copia.
- **HTTP interno síncrono** para lo que exige respuesta inmediata: el
  preflight del modal y la confirmación de pisar conflictos (destructiva,
  y por eso nunca viaja por una cola con reentregas).
- **Sin colas configuradas, sv4 degrada al HTTP síncrono de siempre**: es
  lo que permite trabajar en local sin Azurite y desplegar el código antes
  que la infraestructura. Quitar `COLAS_ACCOUNT_URL` es también el
  rollback.

Dentro de sv5, `TRANSFER_WORKERS` hilos (por defecto 3) consumen la cola
**en el mismo proceso que la API**, no en un worker aparte con KEDA:
maxReplicas=1 es restricción dura y el lock que serializa la escritura es
de proceso. Esos hilos solapan la fase de *preparación* (datos maestros:
obra, recurso por DNI, `reshor`, reglas) y se serializan en la de
*escritura* —parte `hmo`, correlativo `PT<AA>/NNNNN`, synckeys,
conflictos e inserción—, que corre entera bajo el lock. Ganancia real
esperada: ×1,4–×2, no ×N; el lock sigue siendo el cuello.

Los mensajes que agotan sus reintentos caen en `q-transfer-poison` /
`q-transfer-result-poison`. El portal muestra el recuento en la cabecera y
permite **reencolarlos a mano** (≤32 por clic, allowlist cerrada de dos
colas); el traslado hace *send* antes que *delete*, de modo que un fallo a
mitad duplica el mensaje pero nunca lo pierde.

## Semántica de dominio imprescindible

1. **Empleado ≠ recurso.** `emp` es la persona (con DNI); `res` es el
   recurso productivo que se imputa a obras. Las líneas de Sigrid
   (`hmores.reside`) apuntan al RECURSO. El sistema arrastra ambos ides y
   tiene una red de seguridad que resuelve el recurso por DNI al registrar.
2. **Identificación por DNI normalizado** en todo el sistema; nombre solo
   como último recurso, con alias aprendidos (`empleado_alias`).
3. **Horas extra solo con código HE%** en la ficha del recurso (`reshor`).
   Los mensuales (MENC) no registran por horas: sus «extras» del papel se
   omiten con motivo. El exceso sobre la jornada (`candef`, 8 h si
   inválida) se separa como extra automática (`extra_auto`) en sv3.
4. **Incidencias sin horas** (`can=0`) y **solo inicio/fin de racha**
   (código CI* el primer día, CIZ el último); los intermedios no se
   registran. Sigrid pinta el tramo completo a partir del par — verlo con
   solo 2 líneas físicas es correcto. La racha cruza partes y obras.
5. **Parte mensual por obra** (`hmo`, código `PT<AA>/NNNNN`) con el mes
   NATURAL de la fecha real de trabajo; las líneas llevan **synckey** en
   `tex` para idempotencia (reaprobar no duplica) y detección de conflictos.
6. **Ides de Sigrid = MAX(ide)+1** bajo `UPDLOCK` (sin secuencias): por eso
   sv5 corre a UNA réplica fija. Fechas Sigrid: enteros `YYYYMMDD` (0=null).
   El nombre de un concepto está en `con.res` (¡no existe `con.nom`!).
7. **Schema PostgreSQL duplicado a propósito**: `orm_models.py` es
   **byte-idéntico** en sv3 y sv4, y desde F-010 lo comprueba el guardián
   `tests/test_f010_orm_models_gemelos.py` de la raíz en cada
   `bash harness/init.sh` (antes era una promesa, y llevaba meses rota). Un
   cambio de schema modifica los DOS ficheros en la misma feature. **Cuatro
   tablas**: `parte_documents`, `parte_registros`, `empleado_alias` y
   `undo_log` (esta solo la usa sv4, pero la declaran las dos copias porque
   la base es una) — detalle en `partes-proyecto.md` §5. El DDL
   complementario de arranque (`ALTER TABLE … ADD COLUMN IF NOT EXISTS` +
   `CREATE INDEX IF NOT EXISTS`, que `create_all` no hace sobre tablas ya
   existentes) lo **genera** `ddl_complementario()` del propio ORM y lo
   aplican **sv3 y sv4** al arrancar: era la lista escrita a mano en cada
   servicio la que se quedó incompleta y distinta.
8. **Papelera lógica en todo** (documentos y líneas): `is_active` +
   `deleted_*`; nunca borrado físico desde la aplicación.
9. **Partidas CD/CI**: el presupuesto de la obra (`obrparpar`) es un árbol
   del que solo las hojas admiten imputación; CD = costes directos
   (códigos numéricos), CI = indirectos (códigos con letras).
10. **Congelación de lo aprobado (F-004, sv4)**: una línea rechaza toda
    edición de usuario si su parte está `approved`, o si su
    `sigrid_estado` es `encolado` (petición en vuelo hacia sv5) o
    `registrado` (ya escrita en Sigrid). `omitido`/`error`/`conflicto` NO
    congelan: editarlas es el camino de arreglo. La regla se escribe UNA
    vez, en `services/partes-front/application/services/congelacion.py`, y
    la usan tanto las guardas del repositorio (`CongeladoError` → HTTP 409
    con motivo) como las vistas que pintan el candado. Desaprobar
    («Marcar pendiente») levanta la capa «aprobado», **nunca** la capa
    «vive en Sigrid»: el synckey es estable por `registro_id`, así que
    reaprobar una línea editada NO actualiza el ERP. Las acciones masivas
    (undo, reasignaciones, borrados por obra/persona, vaciar papelera)
    omiten lo congelado y devuelven el recuento en vez de abortar.

## Acceso a datos y sistemas externos

- **sigrid-api** (Function App): ÚNICA vía a Sigrid; máx. 1.000 filas por
  petición y corte del balanceador a 230 s. Lecturas contra `ruesma_rep` o
  `ruesma`; la ESCRITURA (solo sv5) siempre contra `ruesma`.
- **PostgreSQL** `psql-albaranes-rs9k2` (servidor COMPARTIDO con otros
  proyectos): solo la base `partes`; nada a nivel de servidor.
- **Microsoft Graph**: buzón (sv1) y SharePoint (sv3).
- **Google Gemini** (sv2): extracción estructurada.
- Desde local se apunta a los backends reales (ver `partes-proyecto.md`
  §9): escritura en Sigrid SOLO en modo pruebas (obra 0404, `PRUEBA-IA`).
- Los unit tests NO tocan ninguno de estos sistemas: mocks, fixtures y
  SQLite en memoria donde haga falta.

## Infra y despliegue

`infra/` (PowerShell 5.1; encoding: sin BOM, `00_vars` LF y el resto CRLF).
Recursos propios en `rg-partes-dev`; reutiliza el ACR `acralbaranesdev` y
el PostgreSQL de albaranes. El código va horneado en la imagen: cambiar
código exige `redeploy_partes.ps1 -Solo svX` (orden seguro
**sv2 → sv3 → sv5 → sv4 → sv1**); reiniciar no basta. Secretos en Key
Vault `kv-partes-pt7m3` vía managed identity (`keyvaultref`); `.env` no
viaja nunca. Los identificadores reales (suscripción, tenant) viven en
`infra/*.local.ps1`, sin versionar; los scripts versionados van redactados.

## Herramientas de consola

Scripts sueltos en la raíz de su servicio, para lanzar A MANO desde una
terminal: no forman parte de ningún pipeline ni los llama el portal. Cada
uno explica su uso en el docstring de cabecera; aquí solo consta que
existen y para qué sirven.

- `services/partes-transfer/prueba_escritura_sigrid.py` — prueba de
  ESCRITURA de partes en Sigrid por fases, siempre contra la obra de
  pruebas 0404 y con marca `PRUEBA-IA`; dry-run salvo `--ejecutar`.
- `services/partes-front/consulta_reshor_recursos.py` — diagnóstico de
  solo lectura: qué recursos y qué códigos de hora tiene un DNI en Sigrid.
- `services/partes-front/validar_datos_sesame.py` (F-013) — informe de
  solo lectura contra `sesame-api`: por cada trabajador, sus festivos del
  año, el tipo de jornada y el flag de reducida, más el calendario por
  defecto. Genera un Markdown y un CSV en `services/partes-front/logs/`
  (carpeta ignorada por git: el informe lleva DNIs) para que el humano
  valide a mano los datos que F-003 usa en el cómputo de extras y en los
  avisos de jornada. Los fallos por trabajador salen como filas del
  informe, no lo abortan. Se configura con `--base-url` / `--api-key` o
  con `SESAME_API_BASE_URL` / `SESAME_API_KEY`.
