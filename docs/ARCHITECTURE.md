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
at-least-once); sv4→sv5 por HTTP síncrono interno; sv3/sv4/sv5→Sigrid solo
a través de `sigrid-api` (Function App). No hay librería compartida: los
servicios se acoplan únicamente por mensajes, HTTP y la BBDD `partes`.

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
7. **Schema PostgreSQL duplicado a propósito**: `orm_models.py` es idéntico
   en sv3 y sv4 (sv4 hace `ALTER TABLE … ADD COLUMN IF NOT EXISTS` al
   arrancar). Un cambio de schema modifica los DOS ficheros en la misma
   feature. Tres tablas: `parte_documents`, `parte_registros`,
   `empleado_alias` — detalle en `partes-proyecto.md` §5.
8. **Papelera lógica en todo** (documentos y líneas): `is_active` +
   `deleted_*`; nunca borrado físico desde la aplicación.
9. **Partidas CD/CI**: el presupuesto de la obra (`obrparpar`) es un árbol
   del que solo las hojas admiten imputación; CD = costes directos
   (códigos numéricos), CI = indirectos (códigos con letras).

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
