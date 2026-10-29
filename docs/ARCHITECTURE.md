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
at-least-once); desde **F-042**, sv4 también publica en `q-persistencia`
un mensaje `{"tipo": "recalcular", ...}` al guardar o deshacer la fecha de
un parte o (F-049) una celda de la matriz de obra (semántica 3), que sv3
distingue del de sv2 (sin `tipo`);
sv4↔sv5 por **doble canal** (ver más abajo);
sv2/sv3/sv4/sv5→Sigrid solo a través de `sigrid-api` (Function App). No hay
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
  preflight del modal, la confirmación de pisar conflictos (edita líneas
  ajenas de Sigrid: desde F-053 las pone a 0, nunca las borra; por eso
  nunca viaja por una cola con reentregas) y, desde F-024, la
  **comprobación de solo lectura** `POST /api/registro/comprobar` (¿siguen
  en Sigrid las líneas `registrado`?), que sv4 pide al abrir una obra o una
  persona y con el botón «Comprobar en Sigrid».
- **HTTP interno síncrono también para el reajuste (F-046)**:
  `POST /api/reajuste/comprobar` (solo lectura, sin lock: ¿se pueden editar
  estas líneas?) y `POST /api/reajuste/ejecutar` (escribe bajo el **mismo
  lock** que el registro). Es destructivo —edita horas ya registradas—, así
  que nunca va por cola; un rechazo es `ok: false` sin nada escrito y un
  502 o un timeout es «no se sabe» (sv4 lo deja `aplicando` y el reintento
  es seguro: lo ya aplicado vuelve como `ya_aplicada`).
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
   elige un **recurso** persona, no una ficha. F-040: el alias se aprende
   también contra el **recurso** (`empleado_alias.recurso_ide`), con o sin
   ficha y con o sin DNI; es lo único que identifica a quien no tiene DNI
   ni ficha (semántica 12).
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
   del día pero no se recalcula. **F-037**: la base y sus extras
   automáticas (mismos `document_id`, `line_index`, `empleado_line_no`,
   `fecha_int`) se congelan juntas para el recálculo de sv3: si una está
   congelada, ninguna se revierte ni se vuelve a partir, y las extras
   automáticas no congeladas de una pareja cuya extra ya está congelada son
   duplicados y se borran. La regla por línea (semántica 10) no cambia.
   **F-045 · reparto ponderado**: las ordinarias del día (recurso y fecha,
   todas las obras) suman la jornada del día, repartida entre las obras en
   proporción a sus horas (ordinarias + extras explícitas) y, dentro de cada
   obra, entre sus líneas, por mayor resto a medias horas (0,25 o 0,01 si
   las horas no lo permiten; desempate: mayor resto, mayor peso, el que llegó
   antes). Ya no hay «último parte en llegar»: 10 h + 4 h con jornada 8 dan
   5,5 + 4,5 y 2,5 + 1,5. Las extras negativas se mantienen y se reparten
   igual. Lo congelado va en **modo residual**: no cambia, cuenta, y se
   reparte lo que queda de jornada; si el reparto ideal lo cambiaría, sv3
   lo avisa (WARNING y `repartos_con_congeladas`) para el reajuste de F-046.
   Las líneas en la papelera no pesan en el día.
   **F-048 · extras leídas en la ordinaria**: la ingesta de sv3 suma las
   extras leídas > 0 de cada fila del papel a la ordinaria de esa fila (un
   registro `normal` con lo trabajado; ordinarias primero en el reparto por
   partidas) y guarda lo leído como extra en `horas_extra_leidas` (solo
   traza; sv4 la enseña como «incl. X h extra leídas» y no la edita). El
   reparto de arriba hace el resto: en laborable, jornada + exceso (solo 10
   extras ⇒ 8 + 2; 4 + 5 ⇒ 8 + 1; 4 + 2 ⇒ 8 + (−2), sin umbral), dos líneas
   por fila y nunca una `extra` explícita al lado; en no laborable, todo a
   `extra_auto` (mismos importes, una línea menos). La extra negativa leída
   sigue explícita. Solo ingestas nuevas: lo guardado antes no cambia.
   **F-046 · reajuste en Sigrid al aprobar** (interruptor `REPARTO_REAJUSTE`
   de sv3, apagado por defecto: apagado, todo es F-045). Lo congelado se
   divide en **reajustable** (`registrado`, o solo por parte aprobado) y
   **duro** (`encolado`, `dedicacion`, ordinaria sin horas, pareja con más
   de una extra automática). Si el ideal del día cambia algo reajustable y
   hay al menos una ordinaria libre, sv3 da el ideal a lo libre y deja el
   reparto `pendiente` en `reparto_pendiente` (con la firma del grupo; si
   el día cambia, `obsoleto` y otro). Al aprobar, sv4 lo avisa: «Aplicar»
   (CAS a `aplicando`, sv5 edita Sigrid, `aplicado`, y sv3 lleva los
   valores a `partes` antes de repartir: `materializado`) o «Mantener lo
   registrado» (`rechazado`; sv3 reparte en residual: `mantenido`). sv5
   solo hace `UPDATE` de `can` y `tot = can × pre` (con el `pre` de la
   línea) e `INSERT` de extras nuevas, en un lote con guardia; **nunca
   borra** (una línea a 0 queda `can = 0`). Sin decisión las líneas del día
   no viajan y no se aprueba el parte. La pasada de sv3 corre bajo un
   candado consultivo de PostgreSQL (`pg_try_advisory_lock`, sesión propia,
   ≤ `CANDADO_CONCILIAR_ESPERA_S`).
   El reparto solo lo calcula sv3 (`conciliar_todos`, que recalcula todo lo
   activo no congelado) y solo cuando le llega un mensaje por
   `q-persistencia`. **F-042**: además de cada ingesta de sv2, lo dispara
   sv4 al **guardar o deshacer la fecha** de un parte (`tipo:
   "recalcular"`, motivo `cambio_fecha` / `deshacer_cambio_fecha`); la
   fecha se guarda aunque la cola falle y el portal lo avisa
   (`recalculo`: `pedido`, `fallo`, `sin_cola`). En sv3 un recálculo
   fallido se reintenta y acaba en `q-persistencia-poison`. Editar horas,
   trabajador, obra o líneas sigue esperando a la siguiente pasada (salvo
   el editor de celda de F-049, abajo).
   **F-043**: el portal confirma el cambio de fecha con el alcance del parte
   (`GET /api/partes/{id}/alcance`: trabajadores y líneas activas) y sigue el
   recálculo: antes de publicar, sv4 escribe en el documento
   `recalculo_pedido_id` (uuid4) y su hora; sv3 lo lee **antes** de su pasada
   y, al acabar sin excepción, lo copia a `recalculo_terminado_id` solo si el
   documento sigue con ese pedido (UPDATE condicional: un pedido posterior no
   se marca). Distintos y con menos de 600 s (`ESPERA_MAX_S`) = parte **en
   espera** (semántica 10); `GET /api/recalculo?ids=…` (1–50) da el estado
   (`sin_seguimiento`, `pendiente`, `terminado`, `vencido`, `no_existe`) y el
   portal lo sondea cada 5 s sin recargar nunca solo: al terminar ofrece
   «Actualizar», que recarga conservando scroll y filtros.
   **F-049 · editor de celda de la matriz de obra**: el doble clic en la
   matriz «Horas por día» edita la celda entera (obra, clave de trabajador
   de F-050 y fecha) y ofrece la ordinaria o la extra que falte; se guarda
   en UNA transacción con comprobación de que nada cambió desde que se abrió
   (`POST /api/matriz/celda`) y se deshace como una sola acción (las líneas
   creadas van a la papelera). Lo escrito manda: las parejas automáticas
   tocadas se **materializan** (`horas_orig` NULL, `extra_auto` falso), así
   que sv3 ya no restaura esa base ni borra esa extra; la jornada la sigue
   aplicando sv3 en la pasada. La pasada es **completa** y reparte por
   (recurso, día) entre obras, así que guardar puede cambiar ese día en
   otras obras (nunca otros días, que solo dependen del calendario): sv4 lo
   avisa al abrir (`GET /api/matriz/celda/otras`) y tras guardar, y escribe
   UN **pedido compartido** (uuid4) en los partes tocados y en los de esas
   otras obras, en una sentencia, antes de publicar UN mensaje (motivos
   `edicion_celda` / `deshacer_edicion_celda`, `document_id` = el primer
   parte tocado). sv3 marca terminado **todo** documento que lleve ese
   pedido (`marcar_terminado` filtra por pedido, no por documento); un
   pedido de un solo parte (uuid4) o el de F-047 (el id del parte) nunca
   coincide con el de otro. Despliegue: **sv3 antes que sv4** (con sv4
   nuevo y sv3 viejo, las otras obras esperarían hasta vencer).
4. **Incidencias sin horas** (`can=0`) y **solo inicio/fin de racha**
   (código CI* el primer día, CIZ el último); los intermedios no se
   registran. Sigrid pinta el tramo completo a partir del par — verlo con
   solo 2 líneas físicas es correcto. La racha cruza partes y obras.
   **Desde F-060**, con el interruptor **`MOVER_CIZ`** encendido (la misma
   variable en sv4 y en sv5, apagada por defecto), el rol lo decide sv4 con
   el histórico de la persona (`persona_de`) en una **ventana** del día 1
   del mes anterior hasta el día anterior, de todas las obras, **por la
   letra** (V seguida de B abre una racha nueva) y **sin la papelera**:
   último día con líneas de la misma letra ⇒ `fin`, si no ⇒ `inicio`; con
   `fin` manda `racha_registro_ids` (las líneas de la racha y las de la
   papelera `registrado`/`encolado` del tramo, también de los días
   saltados). Varios `fin` de una racha en una aprobación: solo el último.
   Si la racha ya tiene su CIZ en Sigrid (synckey de una de esas líneas),
   sv5 lo **mueve** al día nuevo con un `UPDATE` de esa misma línea (fecha,
   synckey y, si cambia de mes u obra, parte), nunca `DELETE` ni otro CIZ;
   la línea que lo tenía queda `omitido` con motivo `fin_movido`. Un CIZ ya
   posterior ⇒ `intermedio`; en un parte cerrado ⇒ `ciz_en_parte_cerrado`;
   enlazado ⇒ `linea_enlazada`. Un trabajo o un inicio aprobado antes de
   una incidencia ya registrada solo avisa (`racha_desordenada`). Apagado
   en sv4, el rol es el de antes de F-060 (`intermedio` si el siguiente día
   ya ingerido es incidencia; sin listas ni avisos); apagado en sv5, cada
   `fin` escribe su CIZ. Se enciende sv5 y luego sv4; se apaga sv4 y luego
   sv5: **apagar los dos es la vuelta atrás completa** (lo ya movido no se
   deshace).
   **Desde F-062**, con el mismo `MOVER_CIZ`, el **`inicio` escribe su CI*
   y un CIZ el MISMO día** (como Administración: un día suelto ya no queda
   solo con su CI*): sv4 lo marca con `ciz_mismo_dia` y le manda su tramo
   delante en `racha_registro_ids`; sv5 escribe los dos con **una sola
   sentencia de dos filas** (el CIZ, «hermano», con synckey
   `partes:<id>:ciz`, `pos` detrás del CI* y la cuenta del código CIZ).
   Si la racha sigue, el siguiente `fin` encuentra ese hermano por
   `partes:<id>:ciz` y lo **mueve** como cualquier CIZ (`UPDATE`); la línea
   del inicio conserva su CI* y sigue `registrado` (sin `fin_movido`). Sin
   hermano: si su `fin` viaja en la misma aprobación (lo escribe ese
   `fin`), si la racha ya tiene un CIZ posterior, si el hermano ya existe,
   si hay un CIZ ajeno ese día o si el recurso no tiene CIZ (WARNING).
   Nada es retroactivo: una racha abierta antes de F-062 recibe su CIZ con
   su siguiente `fin`.
5. **Parte mensual por obra** (`hmo`, código `PT<AA>/NNNNN`) con el mes
   NATURAL de la fecha real de trabajo; las líneas llevan **synckey**
   (`partes:<registro_id>`, en `hmores.synckey`, no en `tex`) para
   idempotencia (reaprobar no duplica) y detección de conflictos.
   **Pisar** un conflicto confirmado **pone la línea existente a 0**
   (F-053: `can = 0`, `tot = 0`; synckey, `tex`, cuenta y lo demás
   intactos) y escribe la nueva: en Sigrid no se borra. **Una
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
   cambio de schema modifica los DOS ficheros en la misma feature. **Ocho
   tablas**: `parte_documents`, `parte_registros`, `empleado_alias`,
   `empleado_jornada` (excepciones de jornada por trabajador, F-015; nace
   vacía), `undo_log` (esta solo la usa sv4, pero la declaran las dos
   copias porque la base es una) y `dedicacion_bandeja` (F-019, la bandeja
   de salida hacia dedicación; la escribe solo sv4, semántica 15) y
   `reparto_pendiente` (F-046: la propone y materializa sv3, la decide sv4
   por CAS sobre `estado`; sin nombres ni DNIs) y `franquicia_ajuste`
   (F-056: el ajuste de franquicia de un recurso y periodo; lo decide y lo
   cierra solo sv4, por CAS sobre `estado` e índice único por recurso y
   periodo; sv3 solo la declara; semántica 21) — detalle
   en `partes-proyecto.md` §5. El DDL
   complementario de arranque (`ALTER TABLE … ADD COLUMN IF NOT EXISTS` +
   `CREATE INDEX IF NOT EXISTS`, que `create_all` no hace sobre tablas ya
   existentes) lo **genera** `ddl_complementario()` del propio ORM y lo
   aplican **sv3 y sv4** al arrancar: era la lista escrita a mano en cada
   servicio la que se quedó incompleta y distinta. Desde F-023,
   `parte_documents` lleva `empresa_membrete`, `empresa` y
   `empresa_origen` (nullables; semántica 12). Desde F-043,
   `parte_documents` lleva `recalculo_pedido_id` / `recalculo_pedido_at_utc`
   (los escribe sv4) y `recalculo_terminado_id` / `recalculo_terminado_at_utc`
   (los escribe sv3), nullables y fuera de deshacer (semántica 3). Desde F-040,
   `empleado_alias` lleva `recurso_ide` (nullable) y `empleado_ide` pasa a
   nullable: el `DROP NOT NULL` va en `DDL_EXTRA_POSTGRES`, única
   sentencia del DDL de arranque que no es «solo añadir» (idempotente y sin
   tocar filas; los tests de F-010 la nombran entera). Desde F-048,
   `parte_registros` lleva `horas_extra_leidas` (`Float`, nullable, sin
   defecto; la escribe solo la ingesta de sv3, semántica 3): 57 columnas.
8. **Papelera lógica en todo** (documentos y líneas): `is_active` +
   `deleted_*`; el único borrado físico es vaciar la papelera o «Eliminar»
   en ella. **Parte retirado (F-061, sv4)**: cuando un parte se queda sin
   ninguna línea viva (borrar la última línea, borrar una persona o
   deshacer una celda) no va a la papelera de partes: se **retira**
   (`is_active = false`, `deleted_at_utc` NULL y `deleted_by` con la marca
   `sin-lineas`), en la misma transacción y con su fila de
   `parte_documents` bloqueada (`FOR UPDATE`, por `id`). No sale en
   `/partes` ni en «Partes borrados», sus líneas siguen en «Líneas sueltas
   borradas» y su sha256 queda libre para que sv3 reingiera el PDF. La
   marca lo distingue del parte desactivado por el reemplazo de sv3
   (`deleted_by` NULL). Restaurar una de sus líneas lo devuelve; si ya hay
   otro parte activo del mismo sha256 (se reprocesó), restaurar responde
   409 sin escribir. Restaurar un parte de la papelera sin líneas vivas
   devuelve también sus líneas. Al vaciar la papelera, y al «Eliminar» su
   última fila, el parte retirado que no conserva **ninguna** fila se
   borra físicamente (decisión del humano); el que conserva filas que
   viven fuera sigue retirado. Borrar una obra y «Borrar parte» siguen
   mandando el parte a la papelera de partes. `/partes` cuenta solo las
   líneas vivas y marca con «Sin líneas» el parte activo sin ninguna.
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
    **Parte en espera (F-043)**: no es congelación (la regla de arriba no
    cambia) sino una guarda aparte, `_exigir_sin_recalculo`, detrás de cada
    guarda de congelación del repositorio: mientras sv3 recalcula un parte
    (`pendiente`, semántica 3) sus ediciones dan 409 con «El parte se está
    recalculando (extras): espera a que termine.» (`RecalculandoError`,
    subclase de `CongeladoError`), salvo cambiar la fecha y deshacer, que
    piden su propia pasada. Lo pinta el servidor (`data-recalculando`), así
    que vale en cualquier pestaña, y vence a los 10 min. Desde F-049 también
    esperan los partes de otras obras del mismo día de una celda guardada
    (pedido compartido, semántica 3).
    **Reparto pendiente (F-046)**: tampoco cambia la regla. Las líneas de un
    día con reparto `pendiente`, `aplicando` o `rechazado` no se registran
    sin decidir («Aplicar» / «Mantener lo registrado») y su parte no se
    aprueba (`RepartoPendienteError`); las vistas lo marcan
    (`data-reparto`). La única escritura de sv3 sobre líneas congeladas es
    materializar un reparto `aplicado` (los valores que sv5 ya escribió).
    Guardar una celda de la matriz (F-049) da 409 si su día tiene un reparto
    `aplicando`; con uno `pendiente` lo avisa y se vuelve a calcular.
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
    **Filtros por usuario (F-064)**: con ese mismo actor, `clave_filtros`
    (pura, en `identidad.py`) da una **clave de filtros** —16 hex del
    SHA-256, sin el UPN en claro— que `base.html` pinta en
    `<body data-filtros-usuario>`; vacía con `sin-identidad` desplegado.
    `FiltrosSesion` (`static/app.js`) guarda en `localStorage`
    (`partes.filtros.v1:<clave>`) los filtros **por usuario y pantalla**
    (filtros por columna, días con su periodo, la casilla de la matriz y la
    búsqueda de las tres listas) y los repone al volver, con el aviso
    «Quitar filtros». Caducan a las **8 h** sin cargar ninguna página (la
    cookie de Easy Auth). La **selección de líneas nunca se guarda**: con
    un filtro repuesto, aprobar sigue enviando solo lo visible (F-022).
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
    está vacío, `res.cif` (un DNI que Sigrid conoce sin ningún recurso
    persona queda sin casar, `dni_sin_recurso`, sin alias ni nombre);
    el nombre puntúa con el máximo entre `con.res`
    del recurso y el de su ficha. Se guarda `empleado_reside` = el recurso
    elegido y `empleado_dni` = su DNI; con ficha, `empleado_ide`/código/
    nombre de la ficha; sin ella, `empleado_ide` NULL, código y nombre del
    recurso y `recurso_dni`/`recurso_nombre` (sv4 lo da por casado). El
    conciliador confirma ese mismo recurso. Lo ya ingerido no se re-casa.
    F-035: los selectores de trabajador del portal (Conciliar, nuevo
    parte, modal y detalle de obra) ofrecen esos mismos **recursos
    persona** (`res.cla = 1`, alta a hoy, DNI `emp.dni` de la ficha o, si
    falta, `res.cif`; sin DNI no salen), filtrados por empresa; elegir uno
    sin ficha deja la línea en `recurso_manual` (casada) con su
    `empleado_reside`, y sv3/sv5 siguen eligiendo el recurso por DNI y
    empresa de la obra. F-040 (**recursos sin DNI**): quien no tiene DNI
    del recurso se identifica por su **clave de persona** (`emp:<conide>`
    con ficha, `res:<res.ide>` sin ella) y compite por nombre, pero si gana
    solo **se propone** (`nombre_sin_dni`: a Conciliar, sin casar). El
    portal ofrece esos recursos marcados «sin DNI»; confirmarlos o
    reasignarlos aprende el alias contra el recurso, y desde entonces esa
    variante casa sola por alias (`alias`/`recurso_nombre`). El conciliador
    conserva el recurso de una línea sin DNI ni ficha si sigue siendo
    persona, sin DNI, de alta y de la empresa (`elegir_sin_dni`; si no, sin
    recurso y a revisión). sv5 no cambia: escribe una línea sin DNI con
    recurso casado (existe, empresa de la obra, de alta). Lo ya ingerido
    no se re-casa.
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
    líneas activas de ese día, de cualquier obra y estado. La clave de
    trabajador del portal (F-050, `worker_key_for_registro`) es
    `rec-{recurso}` en toda línea casada con recurso (con o sin ficha); si
    no, `emp-{ficha}`, `nom-` + leído normalizado o `sin-trabajador`: una
    fila por obra, empresa y persona. **Bloqueo**:
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
    **Guarda de parte abierto (F-034)**: toda sentencia de sv5 que toca
    `hmores` —alta de línea, pisado y, en el reajuste F-046, la guardia,
    el `UPDATE` y la extra nueva— lleva `EXISTS (SELECT 1 FROM con c WITH
    (UPDLOCK, HOLDLOCK) WHERE c.ide = <parte> AND c.est = ?)`: si
    Administración cierra o contabiliza el parte entre la elección (dentro
    del lock) y el `commit`, la sentencia afecta 0 filas y el cierre espera
    a nuestro `commit`. El `INSERT` de una línea que pisa solo entra si
    ninguna de sus pisadas sigue con horas (no duplica si su puesta a 0
    no entró). Tras escribir, sv5 **relee por synckey**: lo que no está en el
    parte elegido sale `omitido` con `parte_no_abierto: el parte <cod> ya
    no esta En registro (<estado>)…` y se reaprueba (irá al
    complementario); `anuladas` (antes `borradas`) cuenta las pisadas
    que ya no tienen horas. El
    modal de resultado de sv4 agrupa las omitidas por motivo y el badge
    `omitido` lleva el texto entero.
    **Pisar sin borrar (F-053)**: ninguna sentencia de sv5 borra en Sigrid
    (el único `DELETE` que queda es el `limpiar` manual de
    `prueba_escritura_sigrid.py`, solo líneas `PRUEBA-IA` de la obra de
    pruebas). El pisado es `stmt_anular_linea`: `UPDATE hmores SET can = 0,
    tot = 0` con `WHERE` optimista (`ide`, recurso, día, código y `can`
    leído), sin enlaces y con la guarda de parte abierto. Solo choca una
    línea **con horas** (una a 0 no es conflicto ni `parte_cerrado`), salvo
    para incidencias; en un parte En registro, una incidencia que ya consta
    se omite (`incidencia_en_sigrid: …`) y un choque con una línea enlazada
    (albarán, factura, dedicación o nómina) también (`linea_enlazada: …`).
    Si una pisada cambió antes de ponerla a 0, la nueva sale
    `pisada_no_anulada: …` y se reaprueba. Una línea del portal pisada
    queda a 0 con su synckey: reaprobarla es `ya_registrado` y la
    comprobación de F-024 la da `presente` con «horas: portal X, Sigrid 0».
    `porcentajes` sigue borrando al pisar: aviso en `azure-apps/partes.md`.
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
17. **Lectura fila a fila y lectura dudosa (F-051, sv2 lee, sv3 juzga)**:
    el prompt `parte_trabajo_es` ordena asignar cada cifra a la fila en
    cuya franja está escrita (por su «Nº» y su DNI/nombre impresos, nunca a
    la más cercana ni a la de arriba), celda vacía = `null`, sin mover
    cifras entre filas, y avisa de los escaneos girados y de las tablas con
    pocas cifras sueltas (fin de semana), donde el modelo las desplazaba.
    Cada fila trae además la **autocomprobación** `numero_linea_horas` (el
    «Nº» leído partiendo de la cifra), declarada en el JSON Schema antes de
    las horas. sv3 marca la **lectura dudosa** (`review_required`, WARNING
    con motivo y filas, sin nombres ni DNIs) por dos motivos, puros sobre
    el payload: `autocomprobacion_fila` (fila con horas y
    `numero_linea_horas` ≠ `numero_linea`; sin el campo no salta) y
    `tabla_dispersa` (alguna fila con horas y alguna con trabajador sin
    horas ni incidencia), esta con el interruptor `REVISAR_TABLA_DISPERSA`
    (encendido por defecto; medido el 2026-10-19: habría marcado 8 de 108
    partes laborables y 9 de 17 de fin de semana). El campo viaja en
    `raw_extraction_json` (sin columna). Solo afecta a ingestas nuevas.
18. **Parte sin obra o sin fecha (F-054, sv3)**: sv3 manda a revisión
    (`review_required`) todo parte sin obra casada (`obra.ide` nulo: `none`
    y los sin casar de F-023) o sin fecha (`fecha_int` nulo o ≤ 0), con un
    WARNING `sin_obra` / `sin_fecha` sin nombres. La bandera no bloquea la
    aprobación ni la baja nadie al poner obra o fecha en el portal. Solo
    ingestas nuevas; lo guardado antes no se toca (el humano descartó la M2
    de F-054 el 2026-10-23: los partes sin obra se corrigen en el portal).
19. **Página escaneada como imagen derecha (F-059, sv2)**: OpenAI, con el
    PDF como `input_file`, no aplica el `/Rotate` de la página y lee de lado
    el JPEG que el escáner guarda girado (cabecera vacía 12/12 en el banco).
    Si el PDF es una **página escaneada** (una página cuyo contenido es solo
    `q cm Do Q` de un JPEG `DCTDecode` de 8 bits en RGB o grises, a página
    completa, sin giro en la matriz), sv2 le manda en su lugar esa imagen
    girada en sentido horario los grados del `/Rotate`, como la enseña un
    visor (JPEG RGB calidad 90, sin EXIF; `infrastructure/document/
    pagina_pdf_imagen.py`, puerto en `domain/ports/conversor_pagina.py`).
    Lo que no es página escaneada va como PDF (`no_aplica`, INFO con el
    motivo cerrado) y si la conversión lanza, también (`error`, WARNING con
    el tipo y el sha256 corto, sin nombre de fichero). Interruptor
    `PAGINA_COMO_IMAGEN` (encendido por defecto) y lista
    `PAGINA_COMO_IMAGEN_PROVEEDORES` (`openai` por defecto; un nombre
    desconocido no arranca); OpenAI manda `detail` = `OPENAI_IMAGE_DETAIL`
    (`high`) en toda `input_image`, fotos del móvil incluidas. El original
    no cambia: sv1 lo guarda tal cual, `meta.source_*` (y la deduplicación
    de sv3 por sha256) siguen siendo suyos, y `meta.adjunto_ia` (en
    `raw_extraction_json`, sin columna) dice qué se mandó: `conversion`
    (`convertida` / `no_aplica` / `error` / `apagada`), `motivo`, tipo y
    tamaño, y giro y medidas si se convirtió.
20. **Relectura de la cabecera y prompt de cabecera (F-058, sv2)**: si la
    lectura primaria (`IA_PROVIDER`, hoy OpenAI) trae trabajadores y su
    cabecera sale **vacía** (sin obra ni fecha) o su **obra no existe en
    Sigrid**, sv2 relee el mismo documento **una vez** con
    `RELECTURA_CABECERA_PROVIDER` (`gemini` por defecto, con su modelo), el
    mismo prompt, esquema y catálogo auxhor; el adjunto sigue la regla de
    F-059 con ese proveedor (hoy Gemini recibe el PDF). Si la releída es
    útil (con cabecera vacía: trae obra o fecha; con obra inexistente: trae
    una obra que existe y no es la misma clave), se toma su **cabecera
    entera** y firma y empleados siguen siendo los de la primaria; si no, o
    si la relectura falla, queda la primaria (F-054 la manda a revisión).
    La existencia de la obra se pregunta **en el momento** a sigrid-api
    (`SigridLookupClient.existe_obra`, sin caché, como mucho dos consultas
    por página: la obra leída y la releída) por la clave (sin acentos,
    mayúsculas, sin espacios ni guiones y sin ceros a la izquierda si es
    numérica), de cualquier empresa y también de baja; no casa la obra (eso
    sigue en sv3). Desde F-063 es un `SELECT DISTINCT con.cod … WHERE
    con.cod LIKE ?` parametrizado, sin funciones sobre `con.cod` (un
    recorrido sin funciones por fila, ~0,1 s; con el `%` inicial no es una
    búsqueda por índice), con el patrón `%c1%c2%…%` de la clave (cada
    carácter con sus variantes de mayúscula y acento) como único parámetro;
    trae candidatos distintos y el resultado exacto lo da sv2 con la misma
    `clave_obra` (`domain/models/clave_obra.py`) sobre cada uno. Tope
    `OBRA_EXISTE_TIMEOUT_S` (5 s); un fallo, `truncated` o el tope superado
    son «no se sabe»: no se relee por obra y la extracción sigue. Cada
    consulta deja un INFO `[obra-sigrid]` con `document_id`, resultado y ms
    (para medir los tiempos en Log Analytics), sin el código. Traza solo
    cuando se relee:
    `meta.relectura_cabecera` (`motivo` `cabecera_vacia` |
    `obra_inexistente`, `provider`, `model`, `resultado` `aplicada` |
    `vacia` | `no_casa` | `error`, `error_tipo`, `consulta_obra_ms`) y
    `debug.relectura_cabecera` (la cabecera primaria y el `debug` de la
    relectura), en `raw_extraction_json` sin columna; `meta.provider` y
    `meta.model` siguen siendo los de la primaria. Interruptor
    `RELECTURA_CABECERA` (encendido); si el proveedor de relectura es el
    primario, no está habilitado o no tiene clave, sv2 arranca igual y lo
    avisa en el log de cableado; `/health` enseña `relectura_cabecera`.
    Además, el punto 1 del prompt `parte_trabajo_es` avisa de que toda
    página tiene una cabecera encima de la tabla «PERSONAL» de la que salen
    la obra, el día, el mes y el año, el membrete y el resto, que se busque
    aunque el escaneo salga desplazado y que nunca se invente un valor.
21. **Franquicia de extras (F-056, sv5 lee y escribe, sv4 decide)**:
    algunos trabajadores solo cobran como extra lo que pasa de X horas en
    el mes de nómina (16 -> 15, etiquetado por el mes del 15). X es un
    campo de `res` en Sigrid que rellena Administración; su nombre lo da
    `FRANQUICIA_CAMPO_RES` de sv5 (vacío = `apagada`: no se lee nada) y SOLO
    sv5 lo lee, con una lectura de `INFORMATION_SCHEMA.COLUMNS` que
    comprueba que la columna existe y es numérica (si no, `no_disponible`
    con WARNING; sv5 arranca igual). NULL o 0 es `inactiva` (X = 0); de 0 a
    200 h, `activa`; lo demás, `invalida`. «No se sabe» nunca es X = 0: no
    se escribe. Con E = las horas `HE%` del recurso en el periodo (todas
    las obras y partes, sin la propia línea), el ajuste es
    `A = -min(E, X)` si E > 0 (si no, 0): una línea `hmores` de extra con
    `can = A` el **día de ajuste** (último del periodo con jornada > 0,
    F-015, con el calendario del trabajador), en la obra de más horas de
    ese día, synckey `partes:franquicia:<id>` y `tex` sin cifras.
    Recalcular es un `UPDATE` de `can`/`tot`; nunca hay `DELETE` ni se
    escribe en `res`. La línea de ajuste no choca con las demás (pisado y
    reajuste la ignoran). En sv4, el preflight de aprobar pide a sv5 la
    franquicia de la selección (`/api/franquicia/recursos`, una llamada) y
    `comprobar` por candidato, y trae un bloque `franquicias` consultivo.
    El humano decide en el modal (`ajustar`, `no_ajustar`, `recalcular`,
    `mantener`; viaja con `ejecutar`/`encolar` y se guarda ANTES que las
    líneas) o desde la vista de trabajador (`POST /api/franquicia/decidir`,
    solo `ajustar`/`recalcular`). Aplicar
    (`POST /api/franquicia/{id}/aplicar`) llama a sv5 `ejecutar` bajo el
    lock del registro, con 409 si quedan líneas del trabajador en cola. Es
    seguro de repetir (idempotente por la synckey) y la fila de
    `franquicia_ajuste` queda `aplicado` (con E, A y la X que usó sv5) o
    `error`. Quién decide y quién aplica sale de `_actor` (F-017), y queda
    fuera de `undo_log`.

## Acceso a datos y sistemas externos

- **sigrid-api** (Function App): ÚNICA vía a Sigrid; la instancia admite
  hasta **500.000 filas** por petición (`MAX_ALLOWED_ROWS`) y el balanceador
  corta a los 230 s. Lecturas contra `ruesma_rep` o `ruesma`; la ESCRITURA
  (solo sv5) siempre contra `ruesma`. sv2 lee el catálogo `auxhor` y, desde
  F-058, consulta en el momento si existe la obra leída (una `sql/read`
  parametrizada por página que la necesite, tope `OBRA_EXISTE_TIMEOUT_S`).
- **Límite de filas de las lecturas (F-038)**: sv3 y sv4 paginan los
  listados a 5.000 filas (`PAGINA_FILAS`, pedidas con `max_rows` 5.001);
  toda otra lectura de sv2, sv3, sv4 y sv5 pide `SIGRID_API_MAX_ROWS`
  (opcional, **500.000** por defecto, 1–500.000; fuera de rango el servicio
  no arranca). `truncated: true` es **siempre error**: nunca se decide con
  filas parciales (en sv2 el catálogo `auxhor` cae a la caché o vacío con
  WARNING y la extracción sigue). `SIGRID_API_TIMEOUT_S` tiene que estar en
  (0, 200] (sv5 suma 30 s al plazo HTTP: ≤ 230 s). La lista cerrada de
  lectores la vigila `tests/test_f038_lectores_sigrid.py`.
- **PostgreSQL** `psql-albaranes-rs9k2` (servidor COMPARTIDO con otros
  proyectos): solo la base `partes`; nada a nivel de servidor.
- **Microsoft Graph**: buzón (sv1) y SharePoint (sv3).
- **Google Gemini** (sv2): extracción estructurada; hoy el primario es
  OpenAI (`IA_PROVIDER=openai`) y Gemini relee la cabecera cuando sale
  vacía o su obra no existe (F-058, `RELECTURA_CABECERA_PROVIDER`).
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
  DNIs. F-040 añade la columna `sin_dni_sin_ficha` y la categoría por
  línea `propone_sin_dni` (se ejecuta desde la rama antes de desplegar).
- `services/partes-front/limpiar_partes_vacios.py` (F-061) — los partes
  ACTIVOS que ya estaban vacíos antes de F-061 reciben la misma regla. Sin
  argumentos SOLO LEE (transacción READ ONLY en `partes`) y deja un
  Markdown y un CSV en `services/partes-front/logs/`, sin nombres ni DNIs:
  por parte, categoría (`todas_en_papelera`, `sin_filas_leidos`,
  `sin_filas_nada_leido`, `sin_filas_manual`), acción prevista (`borrar`
  sin filas, `retirar` con filas) y motivo de exclusión (aprobado, línea
  que vive fuera o en vuelo, PT26/00373, 00375 y 00376). Con `--ejecutar
  --esperados N` (N = candidatos del informe; si no coincide, código 2 sin
  escribir) aplica la regla bajo bloqueo y con la marca
  `sin-lineas · F-061-limpieza`. Lo lanza el humano; sin `SessionFactory`.
- `services/partes-front/validar_datos_sesame.py` (F-013) — informe de
  solo lectura contra `sesame-api`: por cada trabajador, sus festivos del
  año, el tipo de jornada y el flag de reducida, más el calendario por
  defecto. Genera un Markdown y un CSV en `services/partes-front/logs/`
  (carpeta ignorada por git: el informe lleva DNIs) para que el humano
  valide a mano los datos que F-003 usa en el cómputo de extras y en los
  avisos de jornada. Los fallos por trabajador salen como filas del
  informe, no lo abortan. Se configura con `--base-url` / `--api-key` o
  con `SESAME_API_BASE_URL` / `SESAME_API_KEY`.
