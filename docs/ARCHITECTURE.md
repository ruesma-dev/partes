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
  preflight del modal, la confirmación de pisar conflictos (destructiva,
  y por eso nunca viaja por una cola con reentregas) y, desde F-024, la
  **comprobación de solo lectura** `POST /api/registro/comprobar` (¿siguen
  en Sigrid las líneas `registrado`?), que sv4 pide al abrir una obra o una
  persona y con el botón «Comprobar en Sigrid».
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

### Ingesta de sv1: correos adjuntos (F-020)

El escáner envía cada parte como **correo adjunto** (`message/rfc822`) con
el PDF dentro. sv1 descarga su `$value` (MIME RFC 822, sin llamadas Graph
nuevas) y `MimePdfExtractor` (tras el puerto `ExtractorCorreoAdjunto`) lo
recorre hasta **5 niveles** de correos anidados; más ⇒ no se ingiere nada
de ese adjunto. Cada PDF interior sigue el camino de un PDF directo y su
contexto añade `embedded_in` (la cadena de correos). El correo va a
`Procesados` si no falló nada y entró ≥ 1 documento; si no, a `Errores`.

## Semántica de dominio imprescindible

1. **Empleado ≠ recurso.** `emp` es la persona (con DNI); `res` es el
   recurso productivo que se imputa a obras. Las líneas de Sigrid
   (`hmores.reside`) apuntan al RECURSO. El sistema arrastra ambos ides y
   tiene una red de seguridad que resuelve el recurso por DNI al registrar.
2. **Identificación por DNI normalizado** en todo el sistema; nombre solo
   como último recurso, con alias aprendidos (`empleado_alias`). F-030: el
   DNI leído es **canónico** (de 1 a 7 dígitos y letra, ceros a la
   izquierda hasta 8, como en Sigrid). F-036: solo es **recurso persona**
   el de `res.cla = 1` (0 consumo, 2 medio), y el casado del trabajador
   elige un **recurso** persona, no una ficha.
3. **Horas extra solo con código HE%** en la ficha del recurso (`reshor`).
   Los mensuales (MENC) no registran por horas: sus «extras» del papel se
   omiten con motivo. El exceso se mide contra la **jornada DEL DÍA** y se
   separa como extra automática (`extra_auto`) en sv3. Desde **F-015** esa
   jornada no es plana: es el `candef` (8 h si inválida) de lunes a jueves,
   y el **último día laborable de la semana** —según el calendario del
   trabajador, festivos incluidos— recibe el resto de la jornada semanal,
   `max(0, S − 4 × candef)`. `S` sale del mapa configurable
   `JORNADA_SEMANAL_POR_CANDEF` (espejo en sv3 y sv4, por defecto
   `8:40,9:42`); un `candef` que no esté en el mapa se queda con la jornada
   plana `5 × candef`. Las excepciones por trabajador viven en
   `empleado_jornada`. Con `candef = 8` y `S = 40` el resto vale 8: idéntico
   a antes de F-015. Lo ya **congelado** (semántica 10) cuenta en el total
   del día pero no se recalcula.
4. **Incidencias sin horas** (`can=0`) y **solo inicio/fin de racha**
   (código CI* el primer día, CIZ el último); los intermedios no se
   registran. Sigrid pinta el tramo completo a partir del par — verlo con
   solo 2 líneas físicas es correcto. La racha cruza partes y obras.
5. **Parte mensual por obra** (`hmo`, código `PT<AA>/NNNNN`) con el mes
   NATURAL de la fecha real de trabajo; las líneas llevan **synckey**
   (`partes:<registro_id>`, en `hmores.synckey`, no en `tex`) para
   idempotencia (reaprobar no duplica) y detección de conflictos. **Una
   petición a sv5 = una obra** (F-022): sv4 reparte cada aprobación por
   `obra_key_for_registro` y manda una petición por obra (tope
   `APROBACION_MAX_OBRAS`, 10), sin «todo o nada»; sv5 no agrupa obras.
6. **Ides de Sigrid = MAX(ide)+1** bajo `UPDLOCK` (sin secuencias): por eso
   sv5 corre a UNA réplica fija. Fechas Sigrid: enteros `YYYYMMDD` (0=null).
   El nombre de un concepto está en `con.res` (¡no existe `con.nom`!).
7. **Schema PostgreSQL duplicado a propósito**: `orm_models.py` es
   **byte-idéntico** en sv3 y sv4, y desde F-010 lo comprueba el guardián
   `tests/test_f010_orm_models_gemelos.py` de la raíz en cada
   `bash harness/init.sh` (antes era una promesa, y llevaba meses rota). Un
   cambio de schema modifica los DOS ficheros en la misma feature. **Seis
   tablas**: `parte_documents`, `parte_registros`, `empleado_alias`,
   `empleado_jornada` (excepciones de jornada por trabajador, F-015; nace
   vacía), `undo_log` (esta solo la usa sv4, pero la declaran las dos
   copias porque la base es una) y `dedicacion_bandeja` (F-019, la bandeja
   de salida hacia dedicación; la escribe solo sv4, semántica 15) — detalle
   en `partes-proyecto.md` §5. El DDL
   complementario de arranque (`ALTER TABLE … ADD COLUMN IF NOT EXISTS` +
   `CREATE INDEX IF NOT EXISTS`, que `create_all` no hace sobre tablas ya
   existentes) lo **genera** `ddl_complementario()` del propio ORM y lo
   aplican **sv3 y sv4** al arrancar: era la lista escrita a mano en cada
   servicio la que se quedó incompleta y distinta. Desde F-023,
   `parte_documents` lleva `empresa_membrete`, `empresa` y
   `empresa_origen` (nullables; semántica 12).
8. **Papelera lógica en todo** (documentos y líneas): `is_active` +
   `deleted_*`; nunca borrado físico desde la aplicación.
9. **Partidas CD/CI**: el presupuesto de la obra (`obrparpar`) es un árbol
   del que solo las hojas admiten imputación; CD = costes directos
   (códigos numéricos), CI = indirectos (códigos con letras).
10. **Congelación de lo aprobado (F-004, sv4)**: una línea rechaza toda
    edición de usuario si su parte está `approved`, o si su
    `sigrid_estado` es `encolado` (petición en vuelo hacia sv5) o
    `registrado` (ya escrita en Sigrid). `omitido`/`error`/`conflicto` NO
    congelan: editarlas es el camino de arreglo. Tampoco `borrado_sigrid`
    (F-024): estaba registrada y una comprobación vio que Administración la
    borró en Sigrid; se edita y se reaprueba («Reaprobar»), y sv3
    (`esta_congelado`) dice lo mismo. Las aprobaciones masivas excluyen
    siempre `registrado` y `borrado_sigrid` salvo casilla explícita, y
    (F-022) aprueban solo lo seleccionado y visible, o lo visible, con el
    `ambito` de la vista: un id ajeno a ella es 422 sin tocar nada. La regla se escribe UNA
    vez, en `services/partes-front/application/services/congelacion.py`, y
    la usan tanto las guardas del repositorio (`CongeladoError` → HTTP 409
    con motivo) como las vistas que pintan el candado. Desaprobar
    («Marcar pendiente») levanta la capa «aprobado», **nunca** la capa
    «vive en Sigrid»: el synckey es estable por `registro_id`, así que
    reaprobar una línea editada NO actualiza el ERP. Las acciones masivas
    (undo, reasignaciones, borrados por obra/persona, vaciar papelera)
    omiten lo congelado y devuelven el recuento en vez de abortar.
11. **Identidad del portal (F-017, sv4)**: quién firma una escritura se
    resuelve en **un único punto**, `_actor(request)` en
    `interface_adapters/web/app.py`, que delega en las funciones puras de
    `interface_adapters/web/identidad.py`. Ninguna ruta, plantilla ni
    repositorio lee `settings.default_reviewer` ni una cabecera de Easy
    Auth por su cuenta: el autor **se recibe por parámetro** (`by=`,
    `usuario=`, `approved_by=`, `actor=`), no se averigua — leer una
    cabecera HTTP es transporte, no dominio. El valor es el principal de
    Entra normalizado (minúsculas, sin caracteres de control, 120), o un
    marcador reservado que ningún valor externo puede fabricar: `local:…`
    en un puesto de desarrollo y `sin-identidad` —con WARNING por
    petición— si el proceso está desplegado y la cabecera no llega. El
    consumidor de `q-transfer-result` es el único punto de escritura sin
    petición HTTP: toma el actor **del sobre**, y si el sobre no lo trae
    sella `sin-identidad` con WARNING (nunca `NULL`, nunca
    `DEFAULT_REVIEWER`). A partir de F-017, **`NULL` en una columna de
    autor significa «fila anterior a F-017»** — con **una excepción que
    hay que conocer: `undo_log.actor`**, que no la escribe nadie y sigue
    naciendo `NULL` después del corte (escribirla es trabajo de F-018).
    `GET /whoami` permite comprobar la identidad resuelta sin escribir
    ninguna fila. `DEFAULT_REVIEWER` sobrevive con otro significado: ya no
    es «quién firma el portal» sino la etiqueta de la sesión local.
12. **Empresa y alta (F-023)**: maestros de TODAS las empresas (`con.emp`;
    `SIGRID_EMPRESA` ya no se usa). «De alta a D» = `con.fecbaj` NULL, 0 o
    `> D` (nunca `emp.fecbaj`). Hay códigos de obra en dos empresas: la
    **empresa del parte** sale del **membrete** (sv2 lo copia; sv3 lo
    traduce con `config/empresas_membrete.yaml`), si no de la obra única,
    los trabajadores o el nombre; si no, revisión. El trabajador se casa
    entre las fichas de alta de esa empresa y el **recurso**, entre los de
    la persona de alta a la fecha de la línea en la empresa de su obra
    (`emp.reside` solo desempata). Nada se elige al azar. sv5 firma la
    cabecera con la empresa de la obra y verifica cada recurso. Los
    listados de Sigrid se paginan y `truncated: true` es error. F-036
    (sustituye al respaldo F-030 de «ficha de recurso»): sv3 casa el
    trabajador (DNI → alias → nombre) contra los **recursos persona**
    (`res.cla = 1`) de alta a la fecha y de la empresa del parte, con
    **DNI del recurso** = el `emp.dni` de su ficha (`res.conide`) y, si
    está vacío, `res.cif`; el nombre puntúa con el máximo entre `con.res`
    del recurso y el de su ficha. Se guarda `empleado_reside` = el recurso
    elegido y `empleado_dni` = su DNI; con ficha, `empleado_ide`/código/
    nombre de la ficha; sin ella, `empleado_ide` NULL, código y nombre del
    recurso y `recurso_dni`/`recurso_nombre` (sv4 lo da por casado). El
    conciliador confirma ese mismo recurso. Lo ya ingerido no se re-casa.
13. **Cuenta analítica de la línea (F-021, sv5)**: `hmores.caaide` = la
    cuenta `caa` del **centro de la obra destino** (`obr.cenide`, su
    empresa) cuya subcuenta (texto tras el primer punto de `con.cod`) es
    la de la ficha del recurso: `reshor.caaide` del tipo de hora escrito o,
    si no tiene, del tipo por defecto (`res.horide`). Nunca `res.caaide`
    ni `auxhor.caacod`. **F-031 (respaldo de partida)**: solo si el recurso
    no da subcuenta, la de la cuenta de la **partida** de la línea
    (`obrparpar.caaide`) si es de coste (`CI*`/`CD*`; nunca `CP` ni
    `INGR`), llevada igual al centro de la obra; la acción lleva
    `caa_origen` (`recurso`/`partida`/None) y, si es de la partida, una
    `caa_nota` que el modal lista aparte. Sin subcuenta, sin esa cuenta en
    la obra o con varias: `caaide = 0` y la línea se escribe igual (aviso
    en el preflight solo en los dos últimos). Una lectura de `caa` por
    petición y, solo si hace falta, una de partidas.
14. **Incidencia y horas el mismo día (F-025, solo sv4)**: Sigrid no
    clasifica sus incidencias; la clase de cada letra vive en la tabla
    versionada `services/partes-front/config/incidencias.yaml`
    (`INCIDENCIAS_PATH`), que sv4 lee al arrancar y sin la que no levanta
    (falta una letra, clase desconocida, código que no empieza por `CI`).
    Día completo: V, B, M, F, H; parcial: AT, FJ. La persona es el DNI
    normalizado (si no hay, la clave de trabajador) y se miran todas sus
    líneas activas de ese día, de cualquier obra y estado. **Bloqueo**:
    incidencia de día completo + horas (|h| > 0) ⇒ las líneas de ese
    día-trabajador no viajan a sv5 (`excluidas.incompatible`, con motivo en
    `excluidas_detalle`; ni `incluir_borradas`, ni `pisar_claves`, ni
    `forzar_sin_sesame` lo levantan; las `registrado`/`borrado_sigrid` se
    cuentan solo en su estado). **Aviso**: incidencia parcial + extra > 0
    ⇒ viaja y el grupo del preflight lo lista en `avisos_incidencia`. Se
    marca en la matriz y las líneas de la vista de obra, y en el
    calendario y las líneas de la de trabajador; crear y editar no se
    bloquea. El rol de racha (`_rol_incidencia`) y las extras por jornada
    no cambian.
15. **Horas de los mensuales a dedicación (F-019, sv5 decide, sv4
    publica)**: «mensual» es el recurso con algún código `M*` en `reshor`
    (el criterio P1 de dedicación, compartido: si allí cambia, aquí se
    sigue). Con el interruptor de sv5 `MENSUALES_A_DEDICACION` **apagado**
    (por defecto) todo es como antes. **Encendido**, `ReglasRegistro`
    manda a la acción `dedicacion` (con `codigo_mes`) las ordinarias, las
    extra sin `HE*` y las incidencias de cualquier rol de un mensual; solo
    cambia `omitir` → `dedicacion` e incidencia `escribir` → `dedicacion`
    (R3 bis): las extra de un mensual con `HE*` (capataz `MCAP`+`HECAP`)
    siguen a Sigrid con su `HE*`, y nada de un recurso sin `M*` cambia.
    Antes mandan las omisiones de siempre (recurso no verificado, tipo
    raro, sin recurso, sin horas); si la synckey ya está en Sigrid, es
    `ya_registrado` (Sigrid manda). `dedicacion` no escribe, no abre parte,
    no pide cuenta ni entra en conflictos; viaja en `resultado.dedicacion`
    (`{registro_id, recurso_ide, codigo_mes}`) por los dos canales. sv4,
    en la MISMA transacción que pone la línea en `sigrid_estado =
    'dedicacion'`, hace upsert de su fila en `dedicacion_bandeja` (una por
    línea, `version` + `vigente`, sin nombres ni DNIs; reaplicar el mismo
    resultado no la toca). `dedicacion` **congela** como `registrado` (sv4
    y sv3), no se borra definitivamente y no viaja al aprobar
    (`excluidas.dedicacion`). **«Retirar de dedicación»**
    (`POST /api/dedicacion/retirar`, con `ambito`) deja la fila
    `vigente = false` con `version + 1` y libera la línea, que se corrige y
    se reaprueba. La lee dedicación con `GRANT SELECT` solo sobre esa tabla
    (`infra/sql/01_dedicacion_lectura.sql`, lo ejecuta el humano); partes
    no calcula porcentajes ni lee la base de dedicación.
16. **Parte destino y asiento analítico (F-031, sv5 decide, sv4 pinta)**:
    Sigrid genera el asiento analítico de un parte al «Contabilizar parte»
    (Administración, por lotes): lo pasa a **Imputado** (`con.est` 10) y
    crea un asiento tipo 32 con Debe = Σ `hmores.tot` por `hmores.caaide`.
    sv5 no escribe asientos ni cambia estados. Estados del parte (`conest`
    tipo 35): 1 En registro (`EST_PARTE_ACTIVO`), 3 Cerrado, 10 Imputado.
    **«Cerrado» = cualquier parte que no esté En registro** (humano,
    2026-10-06): sv5 nunca escribe en él. Lee TODOS los partes de la obra y
    mes (`partes_del_periodo`) y escribe en el de mayor `ide` En registro;
    si el periodo tiene partes cerrados, ese es el **complementario**
    (reutilizado o, si no hay ninguno En registro, creado como siempre:
    `PT<AA>/NNNNN` de la empresa, `Parte <obra>`), sin tocar el original.
    Duplicados (synckey) y pisado miran todos los partes del periodo: una
    línea con horas ajenas del mismo recurso, día y tipo en un parte
    cerrado se omite (`parte_cerrado: …`); en otro En registro, conflicto
    confirmable con su `parte_cod`. Tras el alta se relee el periodo y se
    usa el parte En registro que haya, propio o de `porcentajes`; si no
    hay ninguno, un reintento con el siguiente código y, si tampoco, error
    sin insertar líneas. El preflight lleva por
    parte `estado`, `complementario`, `cerrados`, `del_periodo` y `aviso`,
    y el modal rotula «complementario». Comprobación:
    `comprobar_asiento_analitico.py` (Herramientas de consola).
    **Parte compartido con `porcentajes` (v5)**: su `dedicacion-transfer`
    (F-037) también da de alta y escribe en los partes de obra de Sigrid.
    Toda alta de sv5 pasa por `_crear_parte` con el **alta protegida**,
    texto y parámetros idénticos a los suyos (`stmts_crear_parte`): `con`
    + `hmo` en una transacción; la cabecera solo entra si el código está
    libre en la empresa y el periodo no tiene ya un parte En registro
    (`NOT EXISTS` con `UPDLOCK, HOLDLOCK` fuera de `MAX(ide)`), y el `hmo`
    solo si ese `con` no lo tiene. Después sv5 relee el periodo y usa el
    parte En registro que haya, suyo o del otro servicio (`creado` solo si
    es suyo); si no hay, un reintento con el siguiente código y, si
    tampoco, error sin insertar líneas. `porcentajes` tiene **copia
    literal** de `estado_parte.py` y `cuenta_analitica.py` (su test de
    copias los compara byte a byte): cambiarlos, o cambiar el alta, obliga
    a **avisar a `porcentajes` en el mismo trabajo**. No entra en la lista
    cerrada de duplicación de `CLAUDE.md`: es una dependencia entre
    repositorios, documentada aquí y en `azure-apps/partes.md`.

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
- `services/partes-transfer/comprobar_asiento_analitico.py` (F-031) —
  SOLO LECTURA (`/api/sql/read`): lista los partes de una obra y mes con
  su estado, líneas y líneas nuestras, y para cada Imputado compara el
  Debe de su asiento por cuenta con sus líneas (`cuadra`, `descuadre`,
  `sin_asiento`, `varios_asientos`). Sin nombres ni contrapartidas.
- `services/partes-persistencia/medir_casado_recursos.py` (F-036) — SOLO
  LECTURA (`/api/sql/read` y SELECT en `partes` en transacción READ ONLY):
  antes de desplegar F-036, recursos persona de alta por empresa (sin DNI,
  DNI solo por ficha, `res.cif` distinto de la ficha, `MO/` que no son
  persona) y, por línea activa, qué hará el conciliador con su recurso y
  qué daría el casado nuevo. Markdown y CSV en
  `services/partes-persistencia/logs/` (ignorada por git), sin nombres ni
  DNIs.
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
