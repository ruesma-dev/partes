<!-- docs/referencia/partes-proyecto.md -->
# PARTES DE TRABAJO — Documento maestro del proyecto

> Origen: redactado por el humano (pgris) en la raíz del monorepo · Fecha
> del documento: 2026-08-13.
> Incorporado a `docs/referencia/` el 2026-08-13.
> Llegó ya en Markdown: no requirió conversión con `markitdown`.

> **Redactado.** Se ha sustituido por un marcador la IP del SQL Server de
> Sigrid (`<ip-vpn-sigrid>`). El detalle está fuera del repositorio
> (infra local).

> **Corregido el 2026-08-18 por F-010**: §5 (esquema real de la base
> `partes`). La versión anterior describía tres tablas y listaba en
> `parte_registros` columnas que nunca existieron (`approved*`,
> `is_active`, `page_number`, `created_at_utc`, `created_by`,
> `nombre_norm`), un índice en `fecha_int` que no existe y `confianza_pct`
> en `parte_documents` (la que hay es `firma_confianza_pct`). Se corrige
> en el sitio, contra `information_schema` de la base real.

> Sistema completo de captura, revisión y registro en Sigrid de los partes
> diarios de trabajo de Construcciones Ruesma. Julio 2026.
> Estado: **desplegado en Azure y operativo** (sv1–sv4 en producción de
> pruebas; sv5 recién dado de alta, escribiendo en modo normal).

---

## 1. Qué hace el sistema

Los encargados de obra envían por **correo** (a `partes@ruesma.es`) los
partes diarios en papel escaneado/foto (PDF). El sistema:

1. **Captura** el correo y su adjunto (sv1).
2. **Extrae con IA** las líneas del parte: trabajador, día, horas
   ordinarias/extra, incidencias, partida de imputación, firmas (sv2).
3. **Concilia contra Sigrid** (el ERP): casa obra, trabajador (por DNI),
   partida y tipo de hora; calcula las horas extra por exceso de jornada;
   guarda todo en PostgreSQL y archiva el PDF en SharePoint (sv3).
4. **Portal de revisión** para Administración: ver, corregir, completar,
   crear partes manualmente y aprobar (sv4).
5. **Registra en Sigrid** las líneas aprobadas, creando/actualizando los
   partes mensuales de mano de obra del ERP (sv5).

Además del flujo por correo, el portal permite **crear partes a mano**
(trabajador + obra + días + horas/incidencia) con el mismo destino final.

---

## 2. Arquitectura de microservicios

Cinco microservicios (cada uno = un proyecto PyCharm = un Container App),
arquitectura hexagonal (Ports & Adapters), pipeline + steps con objeto de
contexto, Pydantic v2, Python 3.12.

```
correo partes@ruesma.es
      │ (Microsoft Graph)
      ▼
┌───────────────┐   q-extraccion    ┌────────────────┐
│ sv1 · email   │ ────────────────▶ │ sv2 · extracción│  (IA: Gemini)
│ ca-sv1-poller │   (Azure Queue)   │ ca-sv2-extraccion│
└───────────────┘                   └────────┬───────┘
                                             │ q-persistencia
                                             ▼
                                    ┌────────────────────┐
                                    │ sv3 · persistencia │──▶ PostgreSQL `partes`
                                    │ ca-sv3-persistencia│──▶ SharePoint (PDF)
                                    └────────┬───────────┘──▶ sigrid-api (lecturas)
                                             │
                                             ▼
┌─────────────────────────┐  HTTP   ┌────────────────────┐
│ sv4 · portal revisión   │ ──────▶ │ sv5 · transfer     │──▶ sigrid-api (ESCRITURA)
│ ca-sv4-front (Easy Auth)│ interno │ ca-sv5-transfer    │      └▶ Sigrid (SQL Server)
└─────────────────────────┘         └────────────────────┘
```

| Servicio | Proyecto PyCharm | Rol | Réplicas |
|---|---|---|---|
| sv1 | `partes-email` | Poller/webhook del buzón; encola PDFs | 1/1 (productor) |
| sv2 | `partes-api` | Worker de extracción con IA (Gemini) | KEDA 0–N (cola) |
| sv3 | `partes-persistencia` | Worker de conciliación y persistencia | KEDA 0–N (cola) |
| sv4 | `partes-front` | Portal FastAPI + Jinja2 (Easy Auth Entra) | 1 |
| sv5 | `partes-transfer` | Registro en Sigrid (escritura) | **1/1 fijo** |

Comunicación: sv1→sv2→sv3 por **colas de Azure Storage** (patrón
at-least-once, KEDA despierta a los workers); sv4→sv5 por **HTTP síncrono
interno** (necesario para confirmar conflictos en el mismo modal);
sv3/sv5→Sigrid a través de **sigrid-api** (Function App pasarela al SQL
Server on-premises por VPN). sv5 es el ÚNICO con credencial de escritura.

---

## 3. Flujo funcional detallado

### 3.1 Captura (sv1)
Vigila el buzón `partes@ruesma.es` vía Microsoft Graph. Por cada correo
con PDF: guarda el adjunto, registra metadatos (remitente, asunto, fecha)
y encola un mensaje en `q-extraccion`.

### 3.2 Extracción IA (sv2)
Worker KEDA. Lee el PDF y llama a **Gemini** con prompt YAML + esquema
estructurado. Extrae: obra (número y nombre leídos), encargado y jefe de
obra, firmas (encargado / jefe de obra / administración), y por línea:
trabajador (nombre y **DNI** si figura), categoría, día, horas ordinarias
y extra, incidencias (V/B/AT/FJ/F/H/M), partida de imputación y texto.
Publica el sobre en `q-persistencia` con confianza por campo.

### 3.3 Conciliación y persistencia (sv3)
Worker KEDA con los **matchers** contra los maestros de Sigrid (leídos
por sigrid-api, cacheados en el wiring):

- **Obra**: código exacto > nombre por similitud.
- **Empleado**: DNI exacto > código exacto > nombre por similitud
  (umbral 0.55), con **alias aprendidos** (tabla `empleado_alias`) que
  Administración confirma desde el portal (vista Conciliar).
- **Recurso**: `res` de Sigrid por CIF/DNI (`recurso_ide`), que es lo que
  luego necesita la escritura.
- **Partida**: contra el presupuesto de la obra (`obrparpar`), guardando
  capítulo (CD/CI/…), método y score.
- **Tipo de hora**: contra `auxhor` (HLOF ordinaria, HEOF extra, CI*
  incidencias…), con precios coste/nómina y `candef` (jornada por defecto
  del recurso, `reshor`).
- **Cómputo de extras**: si un día trae más horas ordinarias que la
  jornada (`candef`, u 8 h si no es válida), divide la línea: jornada
  como ordinarias + exceso como **extra automática** (`extra_auto`,
  conservando `horas_orig`); admite ajustes negativos.

Persiste documento + registros en PostgreSQL y sube el PDF a
**SharePoint** (Graph), guardando drive/item/URL.

### 3.4 Portal (sv4)
FastAPI + Jinja2 + vanilla JS, protegido con **Easy Auth** (Entra ID).
Vistas: **Partes** (documentos con estado y PDF), **Obras** y
**Trabajadores** (matriz horas×día del mes, con modo *mes natural* o
*mes nómina*), **Conciliar** (alias de trabajadores), **Papelera**
(borrado lógico recuperable) y **+ Nuevo** (partes manuales).

Funcionalidad clave: edición inline de líneas (día, obra, categoría,
tipo, horas, código de hora, partida con chips de filtro **CD/CI**,
recurso); KPIs (ordinarias, extra, incidencias, registros); avisos de
jornada incompleta (ordinarias < candef en día laborable); festivos
(librería `holidays`, pendiente de migrar a sesame-api); creación manual
con calendario multi-día, incidencias exclusivas con horas, y flujo
encadenado (tras crear se queda en la página con los días vacíos);
aprobación con **preflight** (modal con qué se registrará y qué no, y
por qué) → registro vía sv5 → estado por línea.

### 3.5 Registro en Sigrid (sv5)
Recibe de sv4 la obra y las líneas aprobadas y aplica el **pipeline de
registro**:

1. Resuelve la **obra destino** (o la obra de pruebas si
   `OBRA_PRUEBAS_FORZAR=true`).
2. Agrupa por **periodo** (año/mes de la fecha real de trabajo): el parte
   de Sigrid es por obra y mes natural.
   - 2b. Red de seguridad: líneas sin `recurso_ide` pero con DNI se
     resuelven contra Sigrid (emp.dni vía res.conide ∪ res.cif).
3. Carga los **tipos de hora de cada recurso** (`reshor`) y aplica las
   reglas:
   - Ordinarias → código laborable del recurso (HLOF…).
   - Extra → SOLO si el recurso tiene código HE% en su ficha; si no, se
     omite con motivo (los mensuales con MENC no registran por horas).
   - **Incidencias**: van SIN horas (can=0). Solo se registran el
     **inicio** de la racha (con su código CI*) y el **fin** (código
     CIZ); los días intermedios se omiten. El rol lo calcula sv4 mirando
     el histórico del trabajador hacia atrás Y hacia delante, saltando
     días vacíos y cruzando partes/obras. Sigrid pinta el tramo completo
     en su vista calendario a partir del par inicio/fin.
4. **Parte mensual**: busca el `hmo` de la obra+mes; si no existe crea
   cabecera `con`+`hmo` con código `PT<AA>/NNNNN` correlativo.
5. **Líneas** `hmores` con `ide = MAX(ide)+1` bajo `UPDLOCK` (por eso
   sv5 va a 1 réplica), importes can×pre, y **synckey** en `tex` para
   idempotencia: reaprobar no duplica; detecta conflictos si alguien
   modificó la línea en Sigrid y pide confirmación para pisar.
6. Devuelve por línea: escrita (con ide de Sigrid) / ya registrada /
   omitida (motivo) / conflicto.

Modo pruebas (apagado por defecto): desvía todo a la obra 0404 y marca
`PRUEBA-IA` en `tex`; el script `prueba_escritura_sigrid.py` permite
verificar/limpiar por mes.

---

## 4. El dominio de conocimiento, en detalle

Esta sección explica el **negocio** que modela la aplicación: qué es un
parte de trabajo en una constructora, cómo lo representa Sigrid, y por qué
las reglas del sistema son las que son. Es la sección que hay que leer
para entender cualquier decisión del código.

### 4.1 El parte de trabajo en papel (el origen de todo)

Cada obra tiene un **encargado** que apunta a diario, en una hoja por
semana o por mes, qué ha hecho su cuadrilla: para cada **trabajador** y
**día**, las horas ordinarias trabajadas, las horas extra si las hubo, o
una **letra de incidencia** si ese día no trabajó (vacaciones, baja…).
Opcionalmente anota a qué **partida** del presupuesto se imputa el
trabajo («alquiler plataforma elevadora», «cimentación»…). La hoja lleva
las firmas del encargado, del jefe de obra y, al validarla, de
Administración. Ese papel, fotografiado o escaneado y enviado por correo,
es la entrada del sistema.

Convenciones del papel que el sistema respeta:

- Las **incidencias se marcan solo el primer y el último día** del
  periodo; los intermedios se dejan en blanco («V……V» = vacaciones toda
  la quincena). Un día suelto lleva su letra sola.
- Las letras usadas y su significado (mapa a códigos Sigrid entre
  paréntesis): **V** vacaciones (CIV) · **B** baja por enfermedad (CIE)
  · **AT** accidente de trabajo (CIA) · **FJ** falta justificada (CIP)
  · **F** falta (CIF) · **H** horas sindicales/permiso horario (CIH) ·
  **M** maternidad/paternidad (CIM).
- Las horas extra se apuntan aparte de las ordinarias, pero muchos
  encargados escriben el total del día (p. ej. «13») y toca separar.

### 4.2 El modelo de Sigrid que toca esta aplicación

Sigrid (el ERP, SQL Server on-premises) modela TODO como **Conceptos**:
la tabla `con` es el padre genérico (con `ide` numérico global, `cod`,
`res` descripción, `fec` fecha) y cada tipo de entidad la extiende 1:1
por `ide`. Los que usa partes:

| Entidad | Tablas | Claves de lectura |
|---|---|---|
| **Obra** | `obr` ⋈ `con` (`obr.ide = con.ide`) | código (`con.cod`, ej. `0404`), nombre (`con.res` — ¡no existe `con.nom`!), centro de coste (`cenide`) |
| **Empleado** (persona) | `emp` ⋈ `con` | `emp.res` nombre completo, **`emp.dni`**, `con.cod` código |
| **Recurso** (productivo) | `res` | `res.conide` → `emp.ide` (a qué persona corresponde), `res.cif` (DNI de nuevo), `res.restipide` → categoría (`auxrestip.res`: «OFIC. 1ª ALBAÑIL») |
| **Tipos de hora** | `auxhor` | catálogo: código, descripción, `ext` (¿computa como extra?) |
| **Horas del recurso** | `reshor` (`reside`,`horide`) | qué tipos de hora tiene CADA recurso en su ficha, con **precio** (`pre`) y **`candef`** (cantidad por defecto = su jornada diaria) |
| **Parte de mano de obra** | `hmo` ⋈ `con` (cabecera) + `hmores` (líneas) | ver 4.4 |
| **Presupuesto** | `obrparpar` (partidas por obra) | ver 4.5 |

**La distinción crítica: empleado ≠ recurso.** El `emp` es la persona a
efectos administrativos (con su DNI); el `res` es el «recurso productivo»
que se imputa a las obras, con sus precios y tipos de hora. Un trabajador
puede estar «casado» como empleado (badge del portal) y aun así no tener
resuelto el recurso — y **las líneas del parte de Sigrid apuntan al
recurso** (`hmores.reside`), no al empleado. Por eso el sistema arrastra
ambos (`empleado_ide` y `recurso_ide`) y tiene una red de seguridad que
resuelve el recurso por DNI en el momento de registrar (doble camino:
`emp.dni` vía `res.conide`, y `res.cif`).

**Identificadores**: Sigrid no usa secuencias; los `ide` se asignan como
`MAX(ide)+1` (por eso la escritura serializa con `UPDLOCK HOLDLOCK` y
sv5 corre a UNA réplica). Las fechas son enteros `YYYYMMDD` (0 = null).

### 4.3 Tipos de hora y jornada: las reglas económicas

Cada recurso tiene en su ficha (`reshor`) los tipos de hora que puede
imputar, con su precio. Los relevantes:

- **HLOF** — Hora Laborable Oficial (ordinaria). Su `candef` es la
  **jornada diaria** del recurso (normalmente 8; si viene vacía o
  inválida, el sistema asume 8).
- **HEOF / HE%** — Horas Extra. **Regla clave: solo se registran extras
  a quien tiene un código HE en su ficha.** Los encargados y otros
  **mensuales** tienen en cambio el código **MENC** (mensualidad, precio
  mensual, p. ej. 6.500 €): cobran por mes, no por horas, así que sus
  «extras» del papel NO se registran (y el portal los excluye de los
  totales de extra).
- **CI\*** — Códigos de Incidencia (CIV, CIE, CIA, CIP, CIF, CIH, CIM)
  y **CIZ** («Fin de Incidencia»). Van **sin cantidad** (`can=0`): la
  línea marca el hecho, no una duración.

**Cómputo de extras por exceso** (en la conciliación, sv3): si un día
trae más ordinarias que la **jornada de ese día**, se divide la línea:
jornada como HLOF + exceso como extra automática (`extra_auto=true`,
conservando `horas_orig`). Admite ajustes negativos (un «8-1» = 8
ordinarias y −1 de regularización de extra).

**La jornada del día no es plana** (F-015). El `candef` de Sigrid son las
horas de lunes a jueves; el **último día laborable de la semana** —el
mayor L–V que sea laborable en el calendario de ESE trabajador— recibe el
resto de la jornada semanal: `max(0, S − 4 × candef)`. Es como trabaja la
cuadrilla de régimen 42 h: 9-9-9-9-6, y hasta F-015 el viernes de 6 h
generaba una extra negativa de −3 h todas las semanas.

- `S` (jornada semanal) sale del mapa configurable
  `JORNADA_SEMANAL_POR_CANDEF` — el mismo valor en sv3 y en sv4, por
  defecto `8:40,9:42`. Un `candef` que no esté en el mapa se queda con la
  **jornada plana** `5 × candef`, que es el comportamiento anterior, y se
  avisa en el log.
- Los **festivos entre semana cuentan como jornada**: el último laborable
  recibe siempre `S − 4 × candef`, haya festivos o no. Si el viernes es
  fiesta, el resto se queda en el jueves; el sábado nunca es candidato.
- Con `candef = 8` y `S = 40` el resto vale `40 − 32 = 8`: **exactamente lo
  de antes de F-015** para todo el mundo que tenga jornada normal.
- Las **excepciones por trabajador** (otra jornada semanal, o un patrón
  explícito de horas por día) viven en `empleado_jornada` (§5.5). La tabla
  nace vacía.
- Lo que ya viajó a Sigrid (línea `encolado`/`registrado` o parte
  aprobado) **cuenta en el total del día pero no se recalcula**: si el día
  no se puede cuadrar sin tocarlo, no se genera ningún ajuste y se avisa.

El portal (sv4) usa la misma jornada del día para los avisos de «jornada
incompleta», para el KPI de jornada de la vista trabajador y —cuando se le
pasa una fecha— para la jornada sugerida de «+ Nuevo».

### 4.4 El parte mensual de Sigrid (el destino)

En Sigrid los partes de mano de obra son **mensuales por obra**: una
cabecera `hmo` (extendiendo `con`, con código correlativo `PT<AA>/NNNNN`,
año y mes, obra y centro de coste) y una línea `hmores` por
(recurso, fecha, tipo de hora) con `can` (horas), `pre` (precio de la
ficha), `tot = can × pre` y `tex` (texto libre).

El sistema usa `tex` para su **synckey** (idempotencia): reaprobar una
línea ya registrada no la duplica; y si alguien la modificó en Sigrid a
mano, se detecta el **conflicto** y el portal pide confirmación antes de
pisar. En modo pruebas se añade la marca `PRUEBA-IA`, que permite
limpiar todo lo escrito de golpe.

**Incidencias en el destino**: replicando la convención del papel, solo
se registran **el primer día de la racha** (con su código CI\*) y **el
último** (con CIZ); los intermedios ni se escriben. La racha se calcula
mirando el histórico del trabajador hacia atrás Y hacia delante,
saltando días sin líneas y cruzando partes/obras (una racha puede
empezar en una obra y seguir tras un traslado). La **Vista calendario**
de Sigrid pinta el tramo completo entre el par inicio/fin — ver 12 M
seguidas en pantalla con solo 2 líneas físicas es el comportamiento
correcto. Un día suelto (trabajo antes y después) lleva su código, como
la «A» de un accidente puntual.

### 4.5 Partidas de imputación (a qué se atribuye el coste)

El presupuesto de cada obra vive en `obrparpar`: un árbol de capítulos y
partidas del que solo las **hojas** admiten imputación. Dos familias:

- **CD — Costes Directos**: las partidas del presupuesto de ejecución,
  con códigos numéricos jerárquicos (`01.03.02.01 · ALQUILER PLATAFORMA
  ELEVADORA`).
- **CI — Costes Indirectos**: gastos generales de obra (`CI.1.10 ·
  GRUISTA`…), con códigos que empiezan por letras.

El parte imputa cada línea de mano de obra a una partida. La
conciliación casa el texto leído contra el presupuesto de ESA obra
(matching bidireccional con prefijos ≥4 caracteres); en el portal los
buscadores filtran por capítulo con chips **Todas / CD / CI** (2.211
partidas en una obra real: los códigos numéricos ordenan primero, por
eso el filtro).

### 4.6 Personas: identificación y aprendizaje

La clave de identidad en toda la casa es el **DNI normalizado** (sin
guiones/espacios, mayúsculas; vale NIE). Cadena de casado del
trabajador: DNI exacto → código exacto → nombre por similitud (umbral
0,55). Como los encargados escriben los nombres «a su manera» («Fco.
Javier Roldán»), la primera vez Administración concilia a mano en el
portal y el sistema **aprende el alias** (`empleado_alias`): la
siguiente vez casa solo. Los trabajadores dados de baja en Sigrid se
excluyen de las búsquedas.

### 4.7 Mes natural vs mes nómina

Las vistas de matriz permiten dos cortes: **mes natural** (1 → último
día) y **mes nómina** (el corte con el que Administración prepara la
nómina, que agrupa el final de un mes con el principio del siguiente).
El registro en Sigrid usa SIEMPRE el mes natural de la fecha real de
trabajo — el parte `PT26/00252` de agosto contiene los días de agosto,
se aprueben cuando se aprueben.

### 4.8 Festivos y jornada (hoy, y hacia dónde va)

Hoy los festivos salen de la librería `holidays` (subdivisión Madrid) y
la jornada teórica del `candef` de Sigrid. La evolución acordada es
tomarlos de **Sesame HR** (control horario) vía el servicio general
`sesame-api`: festivos reales por calendario asignado a cada trabajador,
y jornada (completa/reducida) del contrato — con lo que los avisos de
«jornada incompleta» y el cómputo de extras usarán la verdad de RRHH.

---

## 5. Esquema de la base de datos

**Servidor**: PostgreSQL Flexible Server `psql-albaranes-rs9k2`
(compartido con albaranes) · **Base de datos**: `partes` · ORM:
SQLAlchemy 2 (fichero `infrastructure/database/orm_models.py`,
**byte-idéntico** en sv3 y sv4, con guardián automático desde F-010).
**Cinco tablas**: `parte_documents`, `parte_registros`, `empleado_alias`,
`empleado_jornada` y `undo_log`.

Al arrancar, sv3 y sv4 ejecutan el mismo DDL complementario —`ALTER TABLE
… ADD COLUMN IF NOT EXISTS` por columna y `CREATE INDEX IF NOT EXISTS`—
porque `create_all()` no añade columnas ni índices a una tabla que ya
existe. Ese DDL se **genera del propio ORM** (`ddl_complementario()`), no
se escribe a mano: las dos listas manuales anteriores acabaron incompletas
y distintas entre servicios.

### 5.1 `parte_documents` — un PDF de parte recibido/creado

| Grupo | Columnas | Notas |
|---|---|---|
| Identidad | `id` (PK, uuid), `created_at_utc` | |
| Origen | `source_filename`, `source_attachment_filename`, `source_attachment_sha256`, `source_mime_type`, `source_sha256`, `page_number`, `page_count` | índice único PARCIAL por `source_sha256` `WHERE is_active`: deduplica reenvíos, pero un parte borrado no bloquea reingerir el mismo PDF |
| Correo | `email_id`, `email_subject`, `email_sender`, `email_received_datetime` | vacíos en creación manual |
| Obra leída/casada | `obra_numero_leido`, `obra_nombre_leido`, `obra_codigo`, `obra_ide`, `obra_nombre`, `obra_match_method`, `obra_match_score` | ide = `con.ide`/`obr` en Sigrid |
| Día del parte | `fecha` (ISO), `fecha_int` (YYYYMMDD) | |
| Personas del parte | `encargado_nombre`, `jefe_obra_nombre` | |
| Firmas | `firma_encargado`, `firma_jefe_obra`, `firma_administracion`, `firmado`, `firmante_nombre`, `firmante_rol`, `firma_confianza_pct` | |
| Extracción IA | `provider`, `model_name`, `prompt_key`, `schema_name`, `review_required`, `raw_extraction_json`, `raw_context_json` | trazabilidad completa. La confianza por línea vive en `parte_registros.confianza_pct`; aquí solo hay `firma_confianza_pct` (fila «Firmas») |
| SharePoint | `sharepoint_drive_id`, `sharepoint_item_id`, `sharepoint_url` | PDF archivado |
| Aprobación | `approved`, `approved_at_utc`, `approved_by` | |
| Papelera | `is_active`, `deleted_at_utc`, `deleted_by` | borrado lógico |

### 5.2 `parte_registros` — una línea (trabajador × día × tipo)

**56 columnas** (contadas contra la base real); FK `document_id` →
`parte_documents.id`, `document` relación ORM con `cascade="all,
delete-orphan"` (borrar el parte se lleva sus líneas). Índices:
`document_id`, `empleado_ide` y `deleted_at_utc`.

| Grupo | Columnas | Notas |
|---|---|---|
| Identidad | `id` (PK autoinc), `document_id` (FK), `line_index`, `empleado_line_no` | la línea NO guarda fecha de creación ni autor: eso vive en el documento |
| Trabajador leído | `trabajador_nombre_leido` | el nombre normalizado solo se guarda en `empleado_alias.nombre_norm` |
| Trabajador casado | `empleado_ide`, `empleado_codigo`, `empleado_nombre`, `empleado_dni`, `empleado_reside`, `empleado_match_method`, `empleado_match_score`, `categoria` | ide = `emp.ide`; reside = `res.ide` |
| Fecha | `fecha` (ISO), `fecha_int` (YYYYMMDD) | desnormalizadas del documento; `fecha_int` es el formato de Sigrid (NO está indexada) |
| Obra (por línea) | `obra_codigo`, `obra_ide`, `obra_nombre` | editable; manual la fija aquí |
| Horas | `tipo_hora` (normal/extra/V/B/AT/FJ/F/H/M), `horas`, `horas_orig`, `extra_auto` | extra_auto = generada por cómputo |
| Incidencias | `es_incidencia`, `incidencia_codigo`, `incidencia_texto`, `incidencia_dias` | sin horas |
| Partida | `partida` (texto leído), `partida_ide`, `partida_cod`, `partida_res`, `partida_capitulo` (CD/CI/…), `partida_match_method`, `partida_match_score` | contra `obrparpar` |
| Recurso Sigrid | `recurso_ide` (`res.ide`), `recurso_cif`, `recurso_precio_hora`, `hmo_ide`, `parte_estado` (ok/sin_recurso/sin_parte) | conciliación de sv3 |
| Tipo de hora Sigrid | `hora_ide`, `hora_codigo` (HLOF/HEOF/CI*…), `hora_descripcion`, `hora_ext` (¿es extra?), `hora_candef` (jornada), `hora_precio_coste`, `hora_precio_nomina`, `hora_match_method` | contra `auxhor`/`reshor` |
| Calidad | `confianza_pct` | de la extracción |
| **Registro en Sigrid** | `sigrid_estado` (registrado/omitido/error), `sigrid_parte_cod` (PT26/00251…), `sigrid_hmoide` (cabecera), `sigrid_hmores_ide` (línea), `sigrid_motivo`, `sigrid_registrado_at_utc`, `sigrid_registrado_by` | escrito por sv4 tras sv5 |
| Papelera (de la línea) | `deleted_at_utc`, `deleted_by` | soft-delete recuperable; NULL = activa. La APROBACIÓN es del documento (`parte_documents.approved*`): la línea no tiene `approved*` ni `is_active` |

### 5.3 `empleado_alias` — aprendizaje de la conciliación

| Columna | Notas |
|---|---|
| `nombre_norm` (clave) | nombre leído, normalizado |
| `empleado_ide`, `empleado_codigo`, `empleado_nombre`, `empleado_dni` | ficha de Sigrid a la que corresponde |
| `created_at_utc`, `created_by` | quién lo confirmó en Conciliar |

Cuando Administración concilia un nombre una vez, los siguientes partes
con ese nombre casan solos.

### 5.4 `empleado_jornada` — excepciones de jornada (F-015)

**Nace vacía y se espera que siga así**: es para los trabajadores cuyo
régimen no cabe en el `candef` de Sigrid. Mientras no tenga filas, la
jornada de cada día se deriva del mapa `JORNADA_SEMANAL_POR_CANDEF`
(§4.3). Hasta F-016 (pantalla de administración) las filas se cargan por
SQL a mano; una fila mal formada se ignora, no cambia el reparto.

| Columna | Notas |
|---|---|
| `id` (PK autoinc) | |
| `dni_norm` (indexado) | DNI normalizado, la clave de identidad de la casa |
| `jornada_semanal` | `S` de la excepción; NULL si solo hay patrón |
| `h_lun`…`h_dom` (7) | patrón explícito de horas por día; manda entero y no se aplica la regla del resto |
| `desde`, `hasta` | vigencia ISO. `desde` **inclusivo**, `hasta` **exclusivo** (una vigencia «hasta el 31/07» se carga como `hasta = 2026-08-01`); `hasta` NULL = abierta |
| `origen` | `manual` (hoy) / `sigrid` / `sesame`: deja sitio a importarlas sin migrar el modelo |
| `nota` | |
| `is_active` | papelera lógica |
| `created_at_utc`, `created_by`, `updated_at_utc`, `updated_by` | auditoría |

La leen sv3 (cómputo de extras) y sv4 (avisos y KPI), cada uno con su
propio adaptador y su caché con TTL (`JORNADA_CACHE_TTL_S`). Si la lectura
falla, los dos siguen con la jornada derivada y dejan un WARNING: la tabla
es un accesorio, no puede tumbar ni la conciliación ni el portal.

### 5.5 `undo_log` — historial para DESHACER del portal

Solo la escribe y la lee **sv4**; sv3 la declara igualmente porque las dos
copias del ORM son gemelas y la base es una.

| Columna | Notas |
|---|---|
| `id` (PK autoinc), `created_at_utc` | |
| `action`, `description` | qué se hizo (reasignar, casar, editar horas/fecha/obra…) y cómo se le enseña al usuario |
| `payload` | estado ANTERIOR de las filas afectadas (registros/documento/alias) en JSON: es lo que permite restaurarlas |
| `undone` | si ya se deshizo |
| `actor` | quién lo hizo |

### 5.6 Datos que NO están en esta BBDD

- Los **partes de Sigrid** (`con`+`hmo` cabecera, `hmores` líneas) viven
  en el SQL Server de Sigrid (base `ruesma`); esta BBDD solo guarda la
  referencia (`sigrid_*`).
- Los **PDF** viven en SharePoint (aquí solo drive/item/URL).
- `sesame-api` (festivos/jornada, futuro) no persiste nada.

---

## 6. Recursos de Azure

### 6.1 Resource group propio: `rg-partes-dev` (spaincentral)

| Recurso | Nombre | Función |
|---|---|---|
| Container Apps Environment | `cae-partes-dev` | aloja los 5 servicios |
| Container App | `ca-sv1-poller` | sv1, min/max 1 |
| Container App | `ca-sv2-extraccion` | sv2, KEDA sobre `q-extraccion`, min 0 |
| Container App | `ca-sv3-persistencia` | sv3, KEDA sobre `q-persistencia`, min 0 |
| Container App | `ca-sv4-front` | sv4, **ingress externo** + Easy Auth (Entra) |
| Container App | `ca-sv5-transfer` | sv5, **ingress interno** (solo CAE), allow-insecure para HTTP, min/max 1 |
| Storage Account | `stpartespt7m3` | colas `q-extraccion`, `q-persistencia` (+ blobs de tránsito) |
| Key Vault | `kv-partes-pt7m3` | secretos (ver 6.4) |
| Managed Identity | `id-partes-dev` | pull del ACR (`--registry-identity`) + `keyvaultref` de secretos |
| Log Analytics | `log-partes-dev` | logs de los Container Apps |

Portal: `https://ca-sv4-front.yellowplant-2add9c3e.spaincentral.azurecontainerapps.io`

Tags obligatorios (Azure Policy acens): `acens-customer=Construcciones-Ruesma`,
`acens-environment=dev`, `acens-project=partes`, `acens-responsable-so-app=pgris`.

### 6.2 Recursos REUTILIZADOS de otros RG

| Recurso | Nombre | RG | Uso desde partes |
|---|---|---|---|
| Container Registry | `acralbaranesdev` | `rg-albaranes-dev` | imágenes `sv1-partes:latest` … `sv5-partes:latest` (build con `az acr build`) |
| PostgreSQL Flexible | `psql-albaranes-rs9k2` | `rg-albaranes-dev` | BBDD **`partes`** (esquema §5) |
| Function App | `func-sigridapi-dev-huyke` | `rg-sigrid-dev-data-api` | **sigrid-api**: pasarela SQL al Sigrid on-premises (VPN). sv3 lee (`ruesma_rep`/`ruesma`); sv5 escribe (SOLO base `ruesma`) |

### 6.3 Servicios externos

| Servicio | Uso |
|---|---|
| Microsoft Graph | sv1: buzón `partes@ruesma.es` · sv3: subida de PDF a SharePoint |
| Google Gemini | sv2: extracción estructurada de los partes |
| Entra ID | Easy Auth del portal sv4 (app registration propia) |
| Sigrid (SQL Server on-prem, `<ip-vpn-sigrid>` vía VPN) | destino final, a través de sigrid-api |

### 6.4 Secretos (Key Vault `kv-partes-pt7m3`, vía `keyvaultref` + MI)

Claves de Graph (client/secret del app registration), clave de Gemini,
contraseña de PostgreSQL, `SIGRID-API-FUNCTION-KEY` (function key de
sigrid-api; sv5 la referencia como secreto `sigrid-key`).

### 6.5 Infraestructura como scripts (`partes-infra`)

PowerShell 5.1 (encoding cuidado: sin BOM; `00_vars` LF, resto CRLF):

- `00_vars_partes.ps1` · variables + mapa `$IMG` (fuente única de tags).
- `00_capps_vars_partes.ps1` · MI, KV_URI, URLs de queue/blob, SIGRID_*.
- `fase1_infra_partes.ps1`, `create_capps_partes.ps1`,
  `create_sv1_poller.ps1`, `create_sv4_front.ps1`,
  `create_sv5_transfer.ps1`, `setup_sv4_easyauth.ps1`,
  `add_secrets_partes.ps1`.
- `build_images_partes.ps1` · robocopy a contexto temporal + `az acr build`
  con `manifests/svN/{Dockerfile,requirements.txt,.dockerignore}`.
- `redeploy_partes.ps1` · rebuild + revisión nueva (`--revision-suffix`)
  en orden seguro **sv2 → sv3 → sv5 → sv4 → sv1** (productor el último,
  sv5 antes que su consumidor sv4).

### 6.6 Variables de entorno relevantes por servicio (Container App)

| Servicio | Claves principales |
|---|---|
| sv1 | Graph (tenant/client/secret ref), buzón, QUEUE_URL |
| sv2 | GEMINI (secreto), colas, prompts/schema |
| sv3 | PG (host/db/user/secret), Graph SharePoint, SIGRID_API_BASE_URL + function key (lectura), colas |
| sv4 | PG, SIGRID_API_*, `TRANSFER_BASE_URL` (=fqdn interno de sv5) + `TRANSFER_TIMEOUT_S=120`, Easy Auth |
| sv5 | SIGRID_API_BASE_URL, `SIGRID_API_FUNCTION_KEY` (secretref), **`SIGRID_API_DATABASE=ruesma`** (nunca la réplica), `SIGRID_EMPRESA=1`, `OBRA_PRUEBAS_FORZAR=false` (·true = pruebas·), `OBRA_PRUEBAS_COD=0404`, `MARCA_PRUEBAS=PRUEBA-IA`, API_PORT=8005 |

---

## 7. Reglas de negocio importantes (resumen)

- **Identificación de trabajadores por DNI** en todo el sistema; nombre
  solo como último recurso (con alias aprendidos).
- **Horas extra**: solo se registran en Sigrid si el recurso tiene código
  HE en su ficha (`reshor`); el exceso sobre la jornada (`candef`) se
  separa automáticamente como extra en la conciliación.
- **Incidencias sin horas** (can=0) y **solo inicio/fin de racha** (CI* /
  CIZ); intermedios ni se registran — Sigrid pinta el tramo.
- **Parte mensual por obra**: código `PT<AA>/NNNNN`; las líneas llevan
  synckey para idempotencia y detección de pisados.
- **Papelera** en todo (documentos y líneas): borrado lógico recuperable.
- **Mes natural vs mes nómina** en las vistas de matriz.
- sv5 **una réplica** (MAX(ide)+1 con UPDLOCK) y **base `ruesma`** (la
  réplica `ruesma_rep` no admite escritura).

## 8. Operativa

- **Despliegue**: cambiar código → `.\redeploy_partes.ps1 -Solo svX`
  (el código va horneado en la imagen; reiniciar no basta).
- **Logs**: `az containerapp logs show -n <app> -g rg-partes-dev --tail 60`.
- **Pruebas de escritura**: `prueba_escritura_sigrid.py` (fases
  `verificar` / `limpiar [--ejecutar]`, mes en CONFIG) contra la obra
  0404 con marca `PRUEBA-IA`.
- **Colas atascadas**: los workers a min 0 despiertan con mensajes; para
  depurar, subir temporalmente `--min-replicas 1`.

## 9. Pruebas en local

Todo el sistema puede ejecutarse en el PC de desarrollo (Windows +
PyCharm, Python 3.12, un venv por proyecto). Cada servicio arranca con
`python main.py` y lee su `.env` (nunca versionado; hay `.env.example`).

### 9.1 Qué apunta a dónde en local

En local NO se levanta ni Sigrid ni una nube paralela: los servicios
apuntan a los MISMOS backends que en Azure, con dos salvedades de
seguridad (BBDD y modo pruebas):

| Dependencia | En local |
|---|---|
| PostgreSQL | La BBDD `partes` del servidor de Azure (regla de firewall con tu IP, `MY_IP` en la infra) — o un PG local si se prefiere aislar |
| sigrid-api | La Function App real por Internet (function key en `.env`); las LECTURAS pueden ir a la réplica; la ESCRITURA de sv5 siempre a `ruesma` |
| Graph / Gemini | Las credenciales reales de desarrollo |
| sv4 → sv5 | `TRANSFER_BASE_URL=http://127.0.0.1:8005` en el `.env` de sv4 |

### 9.2 Arranque típico de una sesión de trabajo (portal + registro)

```powershell
# consola 1 — sv5 (registro en Sigrid), puerto 8005
cd C:\Users\pgris\PycharmProjects\partes-transfer
# .env: SIGRID_API_*, y OBRA_PRUEBAS_FORZAR=true mientras se prueba
python .\main.py

# consola 2 — sv4 (portal)
cd C:\Users\pgris\PycharmProjects\partes-front
python .\main.py
# navegador → http://127.0.0.1:<puerto sv4> · Ctrl+F5 tras cambiar JS/CSS
```

En el arranque de sv4 debe verse `[transfer][wiring] CABLEADO
base_url=http://127.0.0.1:8005`; si sale `DESHABILITADO`, falta la
variable y los botones de aprobar no aparecen.

Los workers (sv2/sv3) se arrancan igual (`python .\main_worker.py`) solo
cuando toca probar extracción/conciliación; consumen las colas de Azure,
así que un correo reenviado a `partes@ruesma.es` (o un mensaje inyectado
con `enqueue_test.py` desde la infra) los alimenta también en local.

### 9.3 El modo pruebas y el ciclo con Sigrid

Para probar el registro SIN tocar obras reales, sv5 tiene el **modo
pruebas** (`OBRA_PRUEBAS_FORZAR=true` en su `.env`): toda escritura se
desvía a la obra **0404** y las líneas llevan la marca `PRUEBA-IA` en
`hmores.tex`. El ciclo completo:

```powershell
cd C:\Users\pgris\PycharmProjects\partes-transfer
# ANO, MES en el bloque CONFIG del script (un mes por pasada)
python .\prueba_escritura_sigrid.py verificar          # ¿qué hay escrito?
python .\prueba_escritura_sigrid.py limpiar            # dry-run de los DELETE
python .\prueba_escritura_sigrid.py limpiar --ejecutar # borra lo PRUEBA-IA
```

`limpiar` borra las líneas con la marca y la cabecera del parte si la
descripción la lleva y queda vacía. La validación visual se hace en la
ficha del parte en Sigrid (pestañas «Líneas de detalle» — las líneas
físicas — y «Vista calendario» — que PINTA los tramos de incidencia
entre inicio y fin, no una línea por día).

Para pasar a comportamiento real en local: `OBRA_PRUEBAS_FORZAR=false`
en el `.env` (o borrar la línea: el defecto ya es false) y reiniciar sv5
— limpiando antes la 0404.

### 9.4 Validaciones antes de desplegar (convención del proyecto)

Todo cambio entregado pasa, como mínimo:

- `python -m py_compile <archivos.py>` (sintaxis Python),
- `node --check static/app.js` (sintaxis JS del portal),
- parseo Jinja2 de las plantillas tocadas,
- prueba funcional del caso concreto (a menudo con SQLite en memoria
  para el repositorio, o un upstream simulado para clientes HTTP),
- y en PowerShell, revisión de los pitfalls conocidos (`${var}:` en
  cadenas, backticks con espacios, encoding BOM/CRLF correcto).

El código va horneado en la imagen: en Azure un cambio exige
`redeploy_partes.ps1 -Solo svX` (build + revisión nueva); en local basta
reiniciar el `python main.py` (y Ctrl+F5 si hubo estáticos).

## 10. Hoja de ruta

- Cola `q-transfer` para aprobación asíncrona (Tanda 5).
- Integración **sesame-api**: festivos reales por trabajador y jornada
  (sustituye a la librería `holidays` y al candef como jornada teórica);
  aviso al registrar horas en festivo/domingo.
- Congelar registros aprobados (F3) y endurecer requisitos faltantes (F4).
- `GRAPH_KEY` a Key Vault donde falte (F5); revisión del prompt sv2
  (J.310 rev.1); `tipo_hora_resolver` con `auxhor.ext` para variantes HE%.
