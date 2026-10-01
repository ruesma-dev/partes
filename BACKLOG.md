<!-- BACKLOG.md -->
# Backlog

**Fichero generado por `harness/backlog.py` a partir de `harness/features.json`. No lo edites a mano**: edita el JSON y vuelve a generarlo (lo hace solo `bash harness/init.sh`).

Resumen: **25 features**, 11 abiertas, 14 terminadas.

En curso: **F-022**.

Bloqueadas: **F-014**.

## Trabajo abierto

| # | Feature | Prioridad | Estado | Rigor | Rama |
|---|---|---|---|---|---|
| F-021 | Escribir la cuenta analitica en las lineas que sv5 registra en Sigrid | 2 | spec lista | critico | `feature/F-021-cuenta-analitica-sigrid` |
| F-022 | Aprobar solo las lineas seleccionadas (visibles) en la vista detallada de obra o persona | 2 | en curso | critico | `feature/F-022-aprobar-seleccionadas` |
| F-025 | Incompatibilidad incidencia/horas extra el mismo dia (p.ej. baja por maternidad con hora extra) | 4 | pendiente | estandar | `feature/F-025-incidencia-vs-extra` |
| F-014 | Poner candef=9 en Sigrid a los recursos que registran jornada de 9 h | 5 | bloqueada | documental | `feature/F-014-candef-9-sigrid` |
| F-026 | Partes enviados como foto del movil se ven demasiado grandes en el portal | 6 | pendiente | estandar | `feature/F-026-visor-fotos` |
| F-018 | Log de auditoria de acciones del portal (quien hizo que y cuando) | 9 | pendiente | estandar | `feature/F-018-log-auditoria-portal` |
| F-019 | Horas aprobadas de los trabajadores con codigo de hora mes viajan a dedicacion (porcentajes) en lugar de a Sigrid | 9 | pendiente | critico | `feature/F-019-mensuales-a-dedicacion` |
| F-006 | tipo_hora_resolver con auxhor.ext para variantes HE% | 10 | pendiente | estandar | `feature/F-006-tipo-hora-ext` |
| F-007 | Revisión del prompt de extracción de sv2 (J.310 rev.1) | 11 | pendiente | critico | `feature/F-007-prompt-sv2-evals` |
| F-008 | Modelo de roles en el portal (sv4) | 12 | pendiente | estandar | `feature/F-008-roles-portal` |
| F-011 | Jornada reducida por días desde Sesame sustituye al candef | 14 | pendiente | critico | `feature/F-011-jornada-reducida-dias` |

## Terminadas

| # | Feature | Prioridad | Rigor |
|---|---|---|---|
| F-001 | Test de estructura del monorepo (calentamiento) | 1 | estandar |
| F-023 | Casado de trabajador/recurso contra Sigrid: solo los dados de alta y por la empresa correcta | 1 | critico |
| F-002 | Cola q-transfer para aprobación asíncrona | 2 | critico |
| F-013 | Informe de validación de datos Sesame por trabajador | 2 | estandar |
| F-003 | Integración sesame-api: festivos y jornada reales | 3 | critico |
| F-024 | Lineas que quedan en 'encolado' en el portal aunque el parte ya esta registrado en Sigrid | 3 | critico |
| F-012 | Estudio: candef de 9h, viernes y jornada semanal particularizable | 4 | documental |
| F-004 | Congelar registros aprobados | 5 | estandar |
| F-010 | Saneamiento: resincronizar orm_models.py entre sv3 y sv4 | 6 | estandar |
| F-015 | Jornada del día por jornada semanal derivada del candef y último laborable (extras sv3 + avisos sv4) + tabla de excepciones empleado_jornada | 7 | estandar |
| F-016 | Pantalla de administración de empleado_jornada en el portal (sv4) | 8 | estandar |
| F-017 | Identidad real de Easy Auth en el portal (sv4) | 8 | estandar |
| F-005 | Retirar graphkey_nobom.json del arbol y dejar constancia de GRAPH_KEY en Key Vault | 9 | documental |
| F-020 | Ingesta de sv1: correos adjuntos (message/rfc822) encadenados hasta encontrar el PDF | 10 | estandar |

## Detalle

### F-021 · Escribir la cuenta analitica en las lineas que sv5 registra en Sigrid

estado **spec lista** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-021-cuenta-analitica-sigrid`

Pedida por el humano el 2026-09-30, prioridad maxima. Al registrar en Sigrid (sv5: parte mensual hmo + lineas hmores), rellenar la cuenta analitica de cada linea. Hoy partes no la escribe en ningun sitio (ni rastro de 'analitic' en el codigo). En el diccionario de Sigrid (azure-apps/sigrid_tablas.md) aparece un campo caacod 'Codigo Cue analitica' (texto de 24) en varias tablas y un 'modana' (Modo solo analitica); sin identificar aun si hmores lo tiene. A DECIDIR EN LA SPEC: (a) en que tabla/campo de Sigrid va la cuenta analitica de una linea de horas y si sigrid-api permite escribirla; (b) DE DONDE SALE: de la obra, de la partida, del recurso o de otro maestro de Sigrid; su lectura via sigrid-api (nunca SQL directo); (c) que pasa si no se encuentra (linea sin cuenta, error o aviso en el portal); (d) si afecta al preflight/conflictos del portal (sv4) y a la desaprobacion (F-004). Servicios: sv5 seguro; sv3/sv4 si hay que resolverla antes o mostrarla. RIGOR critico: cambia lo que se escribe en Sigrid en produccion. ACLARADO 2026-09-30 (correo de Juan Romero, Dir. Admon y Control de Costes, 'RV: CAPTURAS'): 'No arrastra cuenta analitica del recurso' => la cuenta analitica SALE DEL RECURSO (su ficha en Sigrid) y hoy no se copia a la linea al registrar. Queda por fijar en la spec el campo exacto del recurso y el de la linea.

### F-022 · Aprobar solo las lineas seleccionadas (visibles) en la vista detallada de obra o persona

estado **en curso** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-022-aprobar-seleccionadas`

Pedida por el humano el 2026-09-30, prioridad maxima. En el portal (sv4), en la vista detallada de una obra o de una persona, si el usuario selecciona varias lineas, al pulsar 'aprobar todo' solo deben aprobarse (y registrarse en Sigrid) las lineas seleccionadas, que el humano describe como 'las visibles'. Hoy el boton aprueba el conjunto completo de la vista (preflight -> encolar/ejecutar en /api/aprobar/*). A CONFIRMAR EN LA SPEC con el humano: si 'seleccionadas' significa las que quedan visibles tras filtrar la vista, las marcadas con casilla, o ambas; que pasa con el resto (quedan pendientes, sin cambio); que el preflight, los conflictos a pisar, el bloqueo por Sesame y el resumen del modal cuenten solo esas lineas; que el servidor valide la seleccion (no fiarse solo del cliente). Servicios: sv4 (portal y API de aprobacion); sv5 no deberia cambiar si recibe ya la lista de lineas: verificarlo en la spec. RIGOR estandar. ACLARADO 2026-09-30 (correo de Juan Romero 'RV: CAPTURAS'): 'opcion de seleccionar varias lineas y aprobarlas, por si quiero dejar alguna pendiente' => seleccion explicita de lineas (casillas) en la vista detallada; el humano lo describio tambien como 'las visibles': la spec debe cubrir ambos (lo filtrado y lo marcado) y confirmarlo.

### F-025 · Incompatibilidad incidencia/horas extra el mismo dia (p.ej. baja por maternidad con hora extra)

estado **pendiente** · prioridad 4 · rigor `estandar` · SDD sí · rama `feature/F-025-incidencia-vs-extra`

Reportado el 2026-09-30 por Juan Romero ('RV: CAPTURAS'): hizo un parte con una incidencia y al lado una hora extra el mismo dia; 'si esta de baja maternidad, no puede tener horas extra'. Hay que limitarlo. A DECIDIR EN LA SPEC: que incidencias son incompatibles con horas trabajadas/extra (baja, maternidad, vacaciones...?) y de donde sale esa lista (tipos de incidencia de Sigrid o lista propia); si se bloquea la aprobacion, se marca para revision o se avisa en el preflight; en que servicio vive la regla (sv3 al conciliar y/o sv4 al aprobar). Servicios probables: sv3/sv4.

### F-014 · Poner candef=9 en Sigrid a los recursos que registran jornada de 9 h

estado **bloqueada** · prioridad 5 · rigor `documental` · SDD no · rama `feature/F-014-candef-9-sigrid`

Pedida por el humano el 2026-08-18 a raíz del estudio F-012 (design.md H5): la jornada semanal se derivará del candef (8→40 h, 9→42 h), así que todo trabajador con jornada de 9 h L–J DEBE tener candef=9 en su hora por defecto (HLOF) de Sigrid. El estudio encontró 7 recursos que registran 9-9-9-9-6 (42 h) desde 2026-05 y 10-10-10-10-8 antes, todos OFIC. 1ª ALBAÑIL con DNI en emp y código HE, y todos con candef=8 hoy: MO/0006, MO/0007, MO/0008, MO/0031, MO/0366, MO/0405, MO/0456. MO/0037 (OFIC. 2ª) ya tiene candef=9 pero NO tiene DNI en emp: corregirlo a la vez. Es un cambio de DATOS MAESTROS en Sigrid que hace RRHH/Administración a mano (los agentes NO escriben en Sigrid fuera de sv5): la feature entrega la petición redactada con la lista y la comprobación posterior por sigrid-api en solo lectura (candef del recurso), sin código nuevo. Los DNIs no se versionan: los recursos se citan por código MO/NNNN. Debe cerrarse ANTES de implementar la regla de jornada semanal que propone F-012.

### F-026 · Partes enviados como foto del movil se ven demasiado grandes en el portal

estado **pendiente** · prioridad 6 · rigor `estandar` · SDD no · rama `feature/F-026-visor-fotos`

Reportado el 2026-09-30 por Juan Romero ('RV: CAPTURAS'): un parte metido como foto tomada con el movil se dimensiona muy grande al verlo en el portal. Ajustar el visor del documento en sv4 para que las imagenes se escalen al contenedor (como los PDF). Servicio: sv4. sdd=false salvo que la investigacion muestre que hay que tocar la ingesta (sv1) o el almacenamiento de la imagen.

### F-018 · Log de auditoria de acciones del portal (quien hizo que y cuando)

estado **pendiente** · prioridad 9 · rigor `estandar` · SDD sí · rama `feature/F-018-log-auditoria-portal`

Pedida por el humano el 2026-08-20 al explicarle F-017. Hoy NO existe un registro de auditoria del portal. Lo mas parecido es la tabla undo_log, pero NO sirve como tal: su proposito es DESHACER (guarda el estado anterior en payload para restaurarlo), solo cubre las acciones reversibles -reasignar, casar, editar horas/fecha/obra-, y deja fuera las aprobaciones, los borrados, las excepciones de jornada de F-016 y cualquier accion administrativa. Ademas sus filas se marcan como undone y su vida la manda la funcion de deshacer, no la de auditar. ALCANCE A DECIDIR EN LA SPEC: que acciones se registran (como minimo las que hoy escriben approved_by/deleted_by y las cinco pantallas de administracion), que se guarda de cada una (actor, cuando, que entidad, que cambio, desde donde), donde vive (tabla propia de la base partes frente a reutilizar undo_log, que el spec-author debe valorar y descartar con argumentos), si hay pantalla de consulta o basta con SQL, y cuanto se conserva. Valorar tambien si sv3 y sv5 deben escribir en el mismo log: sv5 es el unico que escribe en Sigrid, y hoy esa escritura no deja rastro de quien la origino. DEPENDE DE F-017: sin identidad real de Easy Auth, este log registraria NULL en el campo mas importante, que es el actor. Hacerla antes seria construir un libro de firmas sin firmas. HALLAZGO del 2026-08-21, al verificar F-017 desplegada con GET /whoami: Easy Auth inyecta TRES cabeceras, y una es X-MS-CLIENT-PRINCIPAL-ID, el oid INMUTABLE del usuario, disponible sin decodificar el token. F-017 renuncio a guardar el oid por no tener columna donde ponerlo y remitio a esta feature. Si F-018 crea tabla propia, valorar dos columnas: actor (UPN legible, que puede cambiar) y actor_id (oid, que no). Es la diferencia entre una auditoria que aguanta un cambio de nombre y otra que no.

### F-019 · Horas aprobadas de los trabajadores con codigo de hora mes viajan a dedicacion (porcentajes) en lugar de a Sigrid

estado **pendiente** · prioridad 9 · rigor `critico` · SDD sí · rama `feature/F-019-mensuales-a-dedicacion`

Pedida por el humano el 2026-09-29. Los trabajadores cuyo recurso tiene un codigo de hora mes (M* en su reshor de Sigrid: encargados, jefes de obra, tecnicos...) hoy NO dejan nada de sus horas en ningun sitio: sv5 las omite (reglas_registro.py R2 si no tienen HE%, R3 si no tienen HL%). Solo sus INCIDENCIAS se escriben en Sigrid (R1). LO QUE SE PIDE: al APROBAR en el portal, las lineas de estos trabajadores viajan al sistema de dedicacion (repo porcentajes) EN LUGAR DE a Sigrid. DECISIONES DEL HUMANO (2026-09-29): (1) Criterio de 'mensual' = tener un codigo M* en reshor, el mismo que usa dedicacion (no el 'sin HE%' que usa partes hoy). (2) Se envian TODAS las horas aprobadas que haya en partes para ese trabajador. (3) El porcentaje por obra se calcula en funcion de los DIAS LABORABLES del mes; las horas indicadas en festivos se desprecian. Ese calculo es de dedicacion (porcentajes tiene o tendra la funcion): partes envia el dato del dia (trabajador, fecha, obra/partida, horas, tipo) y NO calcula porcentajes, por el limite de servicio. (4) Las VACACIONES cuentan como dias trabajados para ese calculo. (5) Las INCIDENCIAS se llevan a dedicacion COMO INCIDENCIA, con su porcentaje; dejan de escribirse en Sigrid para estos trabajadores (cambia R1). (6) Se presentan en dedicacion como PROPUESTA de reparto, que alguien revisa en el cuadrante; no lo sobrescriben solas. (7) En el portal de partes esas lineas dejan de salir como 'omitidas' y pasan a 'enviadas a dedicacion'. A DECIDIR EN LA SPEC: (a) CANAL. Recomendacion del lider: una bandeja de salida en la base partes (tabla propia escrita por sv5 al aprobar) que dedicacion-api lee con un rol de SOLO LECTURA; cada proyecto escribe solo en su base y no se abre ninguna ruta de red. Descartado HTTP hacia dedicacion-api: no tiene autenticacion propia, su ingress interno es su unico control de acceso (azure-apps/dedicacion.md 5) y vive en otro Container Apps Environment. Alternativa a valorar y descartar con argumentos: bandeja de entrada en la base dedicacion escrita por partes. Nada a nivel de servidor en psql-albaranes-rs9k2: el rol se crea dentro de la base partes. (b) Mensuales que ademas tienen HE% (capataz MCAP + HECAP): si sus extras siguen yendo a Sigrid o tambien viajan a dedicacion; hoy van a Sigrid. (c) DESAPROBAR (F-004): como se retira de dedicacion lo ya enviado, e idempotencia al reaprobar. (d) Que pasa si el periodo ya esta CERRADO en dedicacion cuando llega la aprobacion. (e) Donde vive la decision de enrutar: previsiblemente en sv5 (reglas_registro, nueva accion ademas de escribir/omitir), que ya carga los codigos del recurso. FUERA DE ESTE REPOSITORIO: la lectura y el calculo del porcentaje en dedicacion son una feature del repo porcentajes, a crear alli con decision del humano; esta feature publica el dato y actualiza azure-apps/partes.md en el mismo trabajo (pasamos a exponer algo). RIGOR critico: cambia que se escribe en Sigrid en produccion (sv5 deja de registrar las incidencias de los mensuales).

### F-006 · tipo_hora_resolver con auxhor.ext para variantes HE%

estado **pendiente** · prioridad 10 · rigor `estandar` · SDD sí · rama `feature/F-006-tipo-hora-ext`

El resolutor de tipos de hora debe usar auxhor.ext (¿computa como extra?) para reconocer todas las variantes HE% de la ficha del recurso, en lugar de depender del prefijo del código.

### F-007 · Revisión del prompt de extracción de sv2 (J.310 rev.1)

estado **pendiente** · prioridad 11 · rigor `critico` · SDD sí · rama `feature/F-007-prompt-sv2-evals`

Revisar el prompt YAML de sv2 con el caso J.310 rev.1. Antes de tocar el prompt hay que montar la verificación que lo proteja: banco de evals con ground truth (como la F-011 de albaranes) y declaración en harness/rutas_sensibles.json — un cambio de redacción de prompt no lo caza ningún test unitario.

### F-008 · Modelo de roles en el portal (sv4)

estado **pendiente** · prioridad 12 · rigor `estandar` · SDD sí · rama `feature/F-008-roles-portal`

Introducir roles en el portal (p. ej. administrador vs revisor) para restringir acciones administrativas: la primera es el reencolado de mensajes poison (F-002), que hoy queda disponible para cualquier usuario autenticado por decisión explícita del humano (2026-08-13). Base: claims de Easy Auth/Entra (grupos o app roles) leídos por sv4.

### F-011 · Jornada reducida por días desde Sesame sustituye al candef

estado **pendiente** · prioridad 14 · rigor `critico` · SDD sí · rama `feature/F-011-jornada-reducida-dias`

Corrección de alcance sobre F-003, pedida por el humano el 2026-08-16 (entonces urgente): el candef sigue siendo la jornada teórica como hasta ahora (con el fallback de 8h si falta o es bajo), PERO en los días que Sesame indique jornada reducida para un trabajador, el candef se sustituye SOLO esos días por la jornada reducida (previsiblemente 7h). Afecta al cómputo de extras (sv3) y a los avisos de jornada incompleta (sv4), vía el resolutor único jornada_efectiva que F-003 dejó preparado. OJO: la spec debe verificar qué puede exponer sesame-api sobre días/periodos de jornada reducida (hoy /jornada solo da un booleano heurístico sin fechas) — probablemente amplía la petición P1 a ese proyecto; como F-003, valorar si se implementa apagada con el enchufe listo. REPRIORIZADA A BAJA por el humano el 2026-08-18, tras el informe de F-013: Sesame HR no tiene NINGÚN contrato cargado (0 de 218 empleados; /contract/v1/.../current-contract da contract_not_found para todos), así que hoy no existe fuente de jornada ni de reducida en Sesame. La spec deberá partir de decidir la fuente (contratos en Sesame cuando RRHH los cargue, módulo de horarios de Sesame, o tabla propia). Mientras tanto el candef sigue mandando (F-003 apagada; y encendida, sin contrato Sesame devuelve None y cae al candef). NOTA F-012 (2026-08-18): su fuente candidata es la tabla empleado_jornada (patrón explícito con vigencia) + emphis.porjorlab de Sigrid (% de jornada: 87,5/75/50…, con datos reales), no los contratos de Sesame.

### F-001 · Test de estructura del monorepo (calentamiento)

estado **terminada** · prioridad 1 · rigor `estandar` · SDD no · rama `feature/F-001-test-estructura`

Feature trivial para validar el circuito completo del arnés en este repo: un test en tests/ (raíz) que valida harness/servicios.json contra el árbol real — cada ruta declarada existe y cada servicio Python tiene main.py. Igual que la F-001 de albaranes.

### F-023 · Casado de trabajador/recurso contra Sigrid: solo los dados de alta y por la empresa correcta

estado **terminada** · prioridad 1 · rigor `critico` · SDD sí · rama `feature/F-023-recurso-alta-empresa`

Pedida por el humano el 2026-09-30, prioridad maxima. Al coger el recurso del trabajador de un parte (casado contra el maestro emp/con de Sigrid por DNI -> emp.reside), (1) seleccionar SOLO los que estan dados de alta y (2) seleccionar POR EMPRESA, porque un mismo trabajador/recurso puede existir en 2 empresas. ESTADO ACTUAL: sv3 (infrastructure/sigrid/sigrid_api_client.py, _SQL_EMPLEADOS_BASE + fetch_empleados) filtra por una empresa FIJA (SIGRID_EMPRESA, con.emp = ?) y NO filtra altas/bajas; sv4 tiene su propio fetch_empleados en infrastructure/sigrid/sigrid_lookup_client.py (catalogo para corregir a mano en el portal) y sv5 usa SIGRID_EMPRESA al escribir. A DECIDIR EN LA SPEC: (a) que significa 'dado de alta' en Sigrid para un empleado/recurso (campo fecbaj u otro de emp/con/res; ver azure-apps/sigrid_tablas.md) y si se evalua a hoy o a la FECHA DEL PARTE; (b) DE DONDE SALE LA EMPRESA de cada parte: previsiblemente la empresa de la obra del parte (con.emp de la obra), en lugar del SIGRID_EMPRESA fijo; confirmar con el humano; (c) que pasa si el DNI casa en las 2 empresas y la obra no desempata, o si solo casa con un trabajador de baja (sin casar + revision, no elegir uno al azar); (d) coherencia con sv5, que escribe con SIGRID_EMPRESA fijo: si la empresa pasa a ser la de la obra, la escritura (hmo/hmores) debe usar la misma. Servicios: sv3 (casado), sv4 (catalogo del portal) y probablemente sv5. Los clientes infrastructure/sigrid/ estan en la lista cerrada de duplicacion tolerada: quien toque una copia cambia todas en la misma feature. RIGOR critico: decide a que recurso se imputan horas que se escriben en Sigrid en produccion. ACLARADO 2026-09-30: caso real de Juan Romero ('RV: CAPTURAS'): cogio el recurso MO/0239 dado de baja y no aviso de que existian dos recursos con el mismo DNI. El parte en papel TRAE LA EMPRESA EN EL MEMBRETE (p.ej. Porsan): la empresa del parte se extrae del membrete (sv2) y desempata obras gemelas y recursos. Las consultas a sigrid-api se paginan (OFFSET/FETCH); la instancia dev admite 500.000 filas por peticion.

### F-002 · Cola q-transfer para aprobación asíncrona

estado **terminada** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-002-cola-q-transfer`

sv4 publica las aprobaciones en una cola q-transfer y sv5 la consume (KEDA), en lugar del HTTP síncrono actual para lotes; el HTTP se mantiene donde haga falta respuesta inmediata (preflight y confirmación de conflictos en el modal). Tanda 5 del roadmap de infra.

### F-013 · Informe de validación de datos Sesame por trabajador

estado **terminada** · prioridad 2 · rigor `estandar` · SDD no · rama `feature/F-013-informe-validacion-sesame`

Pedida por el humano el 2026-08-16 para terminar de validar F-003: script (p. ej. services/partes-front/validar_datos_sesame.py, junto al patrón de prueba_escritura_sigrid.py de sv5) que, usando el MISMO SesameApiClient y CalendarioProvider de F-003, extrae para cada trabajador activo sus festivos del año en curso, tipo de jornada y flag de reducida, y genera un informe Markdown/CSV legible para que el humano valide los números contra la realidad. Configurable contra sesame-api local (localhost:8006) o el desplegado cuando exista. La validación de los números en sí es MANUAL del humano sobre el informe. Su salida alimenta F-011 (días de jornada reducida) y F-012 (candef 9h/viernes).

### F-003 · Integración sesame-api: festivos y jornada reales

estado **terminada** · prioridad 3 · rigor `critico` · SDD sí · rama `feature/F-003-sesame-festivos-jornada`

Sustituir la librería holidays y el candef como jornada teórica por los datos reales de Sesame HR vía el servicio general sesame-api: festivos por calendario asignado a cada trabajador y jornada del contrato. Afecta a los avisos de jornada incompleta (sv4) y al cómputo de extras (sv3). Añadir aviso al registrar horas en festivo/domingo.

### F-024 · Lineas que quedan en 'encolado' en el portal aunque el parte ya esta registrado en Sigrid

estado **terminada** · prioridad 3 · rigor `critico` · SDD sí · rama `feature/F-024-lineas-encoladas`

Reportado el 2026-09-30 por Juan Romero (correo 'RV: CAPTURAS', captura de la vista de obra). En un mismo parte y dia, la linea Extra (HEOF) muestra 'PT26/00314' en la columna Sigrid y la linea Ordinaria (HLOF) del mismo trabajador se queda en 'encolado', 'si ya lo habiamos llevado a Sigrid, igual que el de abajo'. A INVESTIGAR (explorer de solo lectura antes de la spec): si la linea se escribio en Sigrid y el portal no recibio/actualizo el resultado (q-transfer/resultado_sigrid de F-002), si el mensaje se perdio o acabo en -poison, o si sv5 la omitio sin devolver estado. Comprobar en Sigrid (solo lectura) y en la base partes. Servicios probables: sv4 (estado mostrado) y sv5 (resultado por linea). RIGOR critico si resulta que hay lineas sin registrar que el usuario cree registradas. HALLAZGO DEL LIDER 2026-10-01 (lectura por sigrid-api, base ruesma): NINGUNA linea hmores de Sigrid tiene synckey no vacio (ni 'partes:%' ni otro), aunque sv5 escribe hmores.synckey = 'partes:<id>' y el portal mostro lineas registradas en PT26/00314 (cabecera existe, empresa 1, 2026-09, 56 lineas, todas con synckey vacio). Hipotesis a verificar: Sigrid (o un proceso suyo) vacia synckey despues de escribir, o las lineas se borraron y se reteclearon. Si synckey no persiste, la idempotencia, la deteccion de conflictos y la desaprobacion (F-004) que se apoyan en el no funcionan: investigar ANTES de F-021.

### F-012 · Estudio: candef de 9h, viernes y jornada semanal particularizable

estado **terminada** · prioridad 4 · rigor `documental` · SDD sí · rama `feature/F-012-estudio-jornada-semanal`

Pedida por el humano el 2026-08-16, para después de F-011: estudiar los trabajadores con candef=9h y cómo deben comportarse sus viernes — deberían ser el resto de horas hasta la jornada SEMANAL (con 9+9+9+9 el viernes serían 4h para llegar a 40). La jornada semanal debe ser PARTICULARIZABLE por trabajador (por defecto 40h, pero hay trabajadores que hacen más de 40h semanales). Entregable: análisis con datos reales (cuántos trabajadores, qué patrones hay en reshor/Sesame) y propuesta de diseño para que el cómputo de extras y los avisos usen jornada semanal además de diaria; la implementación puede ser feature aparte si el estudio lo justifica. APROBADA por el humano el 2026-08-18 con decisiones firmes: jornada semanal DERIVADA del candef ({8:40, 9:42}, env espejo sv3+sv4), resto en el ULTIMO DIA LABORABLE de la semana (festivo cuenta como jornada), excepciones en tabla empleado_jornada (UI en F-016), candef desconocido → jornada plana 5×candef + WARNING, sin calendario → viernes. Rigor documental (estudio sin código). Sale de aquí F-014 (candef en Sigrid), F-015 (implementación) y F-016 (UI).

### F-004 · Congelar registros aprobados

estado **terminada** · prioridad 5 · rigor `estandar` · SDD sí · rama `feature/F-004-congelar-aprobados`

Un registro aprobado (y con más razón, ya registrado en Sigrid) no debe poder editarse en el portal sin desaprobarlo antes de forma explícita.

### F-010 · Saneamiento: resincronizar orm_models.py entre sv3 y sv4

estado **terminada** · prioridad 6 · rigor `estandar` · SDD sí · rama `feature/F-010-resincronizar-orm-models`

El spec-author de F-003 detectó (2026-08-15) que la duplicación tolerada de infrastructure/database/orm_models.py YA está desincronizada: sv3 tiene horas_orig/extra_auto que faltan en sv4, y sv4 tiene las columnas sigrid_* que faltan en sv3. Viola la trampa 3 de C3 (un cambio de schema modifica las DOS copias). Resincronizar ambas copias con el schema real de la BBDD partes, añadir un test que compare las dos declaraciones (como el guardián R11 de F-002), y valorar si el ALTER TABLE IF NOT EXISTS de sv4 debe cubrir también lo de sv3.

### F-015 · Jornada del día por jornada semanal derivada del candef y último laborable (extras sv3 + avisos sv4) + tabla de excepciones empleado_jornada

estado **terminada** · prioridad 7 · rigor `estandar` · SDD sí · rama `feature/F-015-jornada-semanal-candef`

Implementación de lo que propone el estudio F-012 (specs/F-012-estudio-jornada-semanal, requisitos R10–R25 del bloque B, tasks §'Propuesta de tasks para F-015'). Resolutor único gemelo sv3/sv4: L–V = candef efectivo salvo el ÚLTIMO DÍA LABORABLE de la semana del trabajador (calendario F-003; festivo cuenta como jornada), que vale jornada semanal − 4×candef (nunca negativo); jornada semanal derivada del candef por el mapa configurable JORNADA_SEMANAL_POR_CANDEF (default 8:40,9:42; env espejo en sv3 y sv4; candef válido fuera del mapa → jornada plana 5×candef + WARNING; sin calendario cableado → viernes). Excepciones por trabajador en tabla nueva empleado_jornada de la BBDD partes (DNI normalizado, jornada semanal y/o patrón 7 valores, vigencia desde/hasta, origen, auditoría), declarada en las DOS copias de orm_models.py; si falla su lectura, derivada + WARNING. sv3 usa la jornada del día en el split de extras (excluyendo del re-split lo registrado/encolado/approved, coherente con F-004); sv4 en avisos de jornada incompleta, KPI (enseña patrón y S aplicada) y +Nuevo (jornada_dia con fecha). Regresión cero con candef 8. PRERREQUISITOS: F-014 cerrada (candef 9 en Sigrid) y F-010 antes (orm_models resincronizado, decisión D6 aprobada). Servicios: sv3 y sv4 (duplicación tolerada de orm_models y resolutor gemelo, patrón F-003).

### F-016 · Pantalla de administración de empleado_jornada en el portal (sv4)

estado **terminada** · prioridad 8 · rigor `estandar` · SDD sí · rama `feature/F-016-admin-empleado-jornada`

Propuesta por el estudio F-012 (D5, R24): vista de administración en sv4 para crear/editar/cerrar filas de empleado_jornada (DNI, jornada semanal, patrón opcional L–D, desde/hasta, nota), registrando quién y cuándo, validando horas 0–24 por día, desde<hasta y sin solapes por DNI. Hasta entonces las excepciones se cargan por SQL manual del humano. Después de F-015; valorar restringirla por roles cuando exista F-008.

### F-017 · Identidad real de Easy Auth en el portal (sv4)

estado **terminada** · prioridad 8 · rigor `estandar` · SDD sí · rama `feature/F-017-identidad-easy-auth`

Detectado por el spec-author de F-016 el 2026-08-19 y verificado por el lider: sv4 NO lee hoy la identidad del usuario. No hay ni una referencia a X-MS-CLIENT-PRINCIPAL en el repositorio y las once escrituras de auditoria del portal (approved_by, deleted_by y las cuatro entradas de undo_log, todas en services/partes-front/interface_adapters/web/app.py: lineas 1500, 1594, 1629, 1684, 1687, 1841, 1867, 1881, 1900, 1910 y 2121) se firman con la variable DEFAULT_REVIEWER, igual para todos. Decision del humano del 2026-08-19: se introduce la lectura de Easy Auth y se extiende a TODO el portal, no solo a las columnas de F-016. Alcance: decodificar la cabecera de Easy Auth (X-MS-CLIENT-PRINCIPAL-NAME o el token base64, decidiendo cual manda), un unico helper de identidad que consuman los once puntos, fallback para desarrollo local, y decidir que se hace con las filas historicas ya firmadas con el valor generico (propuesta del spec-author: NO se reescriben, se documenta el corte; inventar autores seria falsificar auditoria). Los ROLES siguen siendo F-008: esta feature responde a 'quien hizo esto', no a 'quien puede hacerlo'. Material de partida en specs/F-016-admin-empleado-jornada/design.md seccion 14. AVISO del reviewer de F-016 (2026-08-19): el test test_f016_r13_auditoria (services/partes-front/tests/test_f016_endpoints_admin_jornadas.py:519) parchea DEFAULT_REVIEWER en vez del helper _actor, asi que se pondra ROJO el dia que _actor devuelva el principal real de Easy Auth. F-017 debe incluirlo en su lista de ficheros a tocar y pasarlo a inyectar o parchear el helper. Deberia ir ANTES de F-016 para que las filas de empleado_jornada nazcan firmadas con el usuario real, pero las dos ordenes funcionan sin retrabajo porque F-016 pide la identidad a un solo helper. HALLAZGO del 2026-08-20 (verificacion del despliegue): DEFAULT_REVIEWER NO esta configurada en el Container App ca-sv4-front (comprobado en Azure; .env.example la declara vacia), asi que _actor devuelve None y los once puntos de auditoria llevan sellando NULL desde el primer despliegue. El enunciado de esta feature decia que las filas van firmadas con un valor generico: NO es asi, van SIN autor. Cambia la decision sobre las filas historicas (no hay nada que reescribir, solo un corte que documentar) y sube el valor de la feature: hoy la auditoria del portal esta en blanco. DECISION del humano del 2026-08-20: no se pone un DEFAULT_REVIEWER provisional mientras tanto; la auditoria sigue con NULL hasta que esta feature lea la identidad real de Easy Auth.

### F-005 · Retirar graphkey_nobom.json del arbol y dejar constancia de GRAPH_KEY en Key Vault

estado **terminada** · prioridad 9 · rigor `documental` · SDD no · rama `feature/F-005-graphkey-keyvault`

Los dos objetivos originales estan cumplidos de hecho. Comprobado el 2026-08-20 y reconfirmado el 2026-08-25 contra Azure (solo lectura): los tres servicios que usan Graph -ca-sv1-poller, ca-sv3-persistencia y ca-sv4-front- llevan GRAPH_KEY como secretRef 'graph-key' y el secreto de la Container App es una referencia a Key Vault, no una copia; el secreto GRAPH-KEY existe y esta habilitado en el Key Vault de partes ($KV). Ningun script de infra/ lee graphkey_nobom.json: add_secrets_partes.ps1 pide el JSON por consola con Read-Host -AsSecureString y lo sube al Key Vault sin tocar disco. Lo que queda, y es esta feature: borrar la copia local de infra/graphkey_nobom.json (no versionada, nunca entro en git) y corregir las dos menciones que aun la presentan como parte del despliegue. Decision del humano del 2026-08-25: SOLO LIMPIEZA.

### F-020 · Ingesta de sv1: correos adjuntos (message/rfc822) encadenados hasta encontrar el PDF

estado **terminada** · prioridad 10 · rigor `estandar` · SDD sí · rama `feature/F-020-correo-adjunto-escaner`

Pedida por el humano el 2026-09-30. El escaner (visto desde el remitente del escaner, asunto 'Attached Image') envia los partes como un correo adjunto (message/rfc822, itemAttachment de Graph) que contiene el PDF. Hoy sv1 descarta los itemAttachment (_NON_FILE_ODATA_TYPES en polling_pipeline.py) y el correo acaba en Errores por 'sin adjuntos elegibles'. LO QUE SE PIDE: sv1 abre los correos adjuntos de CUALQUIER remitente (decision del humano: NO se filtra por remitente) y los recorre de forma recursiva, correo dentro de correo, hasta encontrar el/los PDF, que siguen el camino normal (troceo por paginas -> Blob -> q-extraccion). DECISIONES CONFIRMADAS (2026-09-30): (1) Solo se extraen PDF del interior; imagenes no. (2) Tope de seguridad de 5 niveles de anidamiento; si se excede o no aparece ningun PDF, el correo va a Errores con log explicativo. (3) Un correo con PDF directos y correos adjuntos procesa todo en la misma pasada. (4) Citas de calendario, contactos y referenceAttachment se siguen descartando. (5) El contexto del documento lleva el nombre del PDF interior y una clave nueva 'embedded_in' con la cadena de correos atravesados; verificar que sv2/sv3 no se rompen. (6) Se crean los primeros tests de sv1 (services/partes-email/tests/) con .eml sinteticos, sin red, y se registran en harness/servicios.json. PRIMER PASO OBLIGATORIO: sonda de SOLO LECTURA que confirme que GET /attachments/{id}/$value sobre un itemAttachment devuelve el MIME del correo adjunto con el PDF dentro; si no, parar y reproponer. SOLO TOCA sv1. Desplegar lo lanza el humano. Reprocesar los correos ya caidos en Errores es manual y queda fuera.
