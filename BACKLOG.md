<!-- BACKLOG.md -->
# Backlog

**Fichero generado por `harness/backlog.py` a partir de `harness/features.json`. No lo edites a mano**: edita el JSON y vuelve a generarlo (lo hace solo `bash harness/init.sh`).

Resumen: **59 features**, 13 abiertas, 46 terminadas.

Bloqueadas: **F-032**.

## Trabajo abierto

| # | Feature | Prioridad | Estado | Spec | Rigor | Rama |
|---|---|---|---|---|---|---|
| F-056 | Trabajadores con franquicia de extras: al cerrar el mes, aviso y línea de ajuste el último laborable | 3 | spec lista | aprobada (DA1–DA20 = A) · `partes-wt-f056` | critico | `feature/F-056-franquicia-de-extras` |
| F-055 | sv5 omite las líneas sin fecha válida (no abre partes del periodo 0/00 ni de años mal tecleados) | 4 | spec lista | escrita, pendiente de aprobación · `partes-wt-f055` | critico | `feature/F-055-sv5-omite-lineas-sin-fecha` |
| F-047 | Parte nuevo en espera hasta que sv3 reparta sus horas (ordinaria y extra) | 5 | spec lista | aprobada (DA1–DA10) · `partes-wt-f047` | critico | `feature/F-047-parte-nuevo-en-espera` |
| F-052 | Sincronizar con Sigrid: desde una obra o una persona, leer Sigrid, comparar línea a línea con el portal y conciliar una a una o en masa | 6 | spec lista | escrita, pendiente de aprobación · `partes-wt-f052` | critico | `feature/F-052-sincronizar-con-sigrid` |
| F-057 | Editor de celda: el pedido de recálculo incluye todos los partes con líneas en la celda | 7 | spec lista | aprobada 2026-10-24 (DA1–DA5 = A) · `partes-wt-f057` | estandar | `feature/F-057-pedido-celda-todos-los-partes` |
| F-032 | Activar Sesame en produccion: festivos de cada trabajador leidos de Sesame HR | 8 | bloqueada | en `dev`; feature bloqueada por decisión del humano (2026-10-07) | estandar | `feature/F-032-sesame-festivos-produccion` |
| F-027 | Escapar HTML en los modales heredados del portal (nombres que vienen del OCR) | 9 | pendiente | no lleva (sdd: false) | estandar | `feature/F-027-escape-modales` |
| F-026 | Partes enviados como foto del movil se ven demasiado grandes en el portal | 10 | pendiente | no lleva (sdd: false) | estandar | `feature/F-026-visor-fotos` |
| F-018 | Log de auditoria de acciones del portal (quien hizo que y cuando) | 11 | pendiente | borrador en la rama `worktree-agent-ad862e62640d64553`, sin presentar | estandar | `feature/F-018-log-auditoria-portal` |
| F-006 | tipo_hora_resolver con auxhor.ext para variantes HE% | 12 | pendiente | sin spec | estandar | `feature/F-006-tipo-hora-ext` |
| F-007 | Revisión del prompt de extracción de sv2 (J.310 rev.1) | 13 | pendiente | sin spec | critico | `feature/F-007-prompt-sv2-evals` |
| F-008 | Modelo de roles en el portal (sv4) | 14 | pendiente | sin spec | estandar | `feature/F-008-roles-portal` |
| F-011 | Jornada reducida por días desde Sesame sustituye al candef | 15 | pendiente | sin spec | critico | `feature/F-011-jornada-reducida-dias` |

## Terminadas

| # | Feature | Prioridad | Rigor | Pendiente |
|---|---|---|---|---|
| F-001 | Test de estructura del monorepo (calentamiento) | 1 | estandar |  |
| F-023 | Casado de trabajador/recurso contra Sigrid: solo los dados de alta y por la empresa correcta | 1 | critico |  |
| F-028 | Detalle de obra y de trabajador a todo el ancho de la ventana | 1 | estandar |  |
| F-029 | El logotipo de Ruesma (ruΞsma) se reconoce como empresa 1 en el membrete | 1 | estandar |  |
| F-030 | Trabajadores con recurso en Sigrid pero sin ficha de empleado: casar el recurso por DNI | 1 | critico |  |
| F-031 | El parte registrado en Sigrid genera su asiento en la cuenta analitica de la obra | 1 | critico |  |
| F-033 | Portal: columna Empresa en el listado de obras | 1 | estandar |  |
| F-034 | sv5 solo escribe en partes de Sigrid abiertos (estado 1, En registro) | 1 | critico | M3 (Administración cierra PT26/00375) y M4 |
| F-035 | Portal: elegir trabajador entre recursos activos de Sigrid, filtrados por empresa | 1 | estandar |  |
| F-036 | sv3: casar el trabajador leido contra los recursos persona de la empresa del parte | 1 | critico |  |
| F-037 | sv3: no duplicar la extra automatica cuando su linea base esta omitida y la extra ya esta registrada | 1 | critico |  |
| F-039 | Portal: mostrar el nombre de la empresa (Ruesma, Porsan) en vez de «empresa N» en combos y Conciliar | 1 | estandar |  |
| F-040 | Recursos sin DNI: proponer por nombre, aprender alias por recurso y poder registrarlos | 1 | critico |  |
| F-042 | Recalcular el reparto normal/extra al cambiar la fecha de un parte | 1 | critico |  |
| F-043 | Fecha del parte: rotulo claro, confirmacion antes de moverlo y parte en espera mientras sv3 recalcula las extras | 1 | critico |  |
| F-045 | Reparto ponderado de la jornada entre obras: ordinarias y extras del dia repartidas en proporcion a las horas de cada parte, a medias horas | 1 | critico |  |
| F-048 | Ordinarias + extras leidas en laborable siguen la regla de jornada: la ingesta suma las extras leidas de cada fila a su ordinaria y el reparto da J + exceso | 1 | critico | M4 |
| F-050 | Misma fila para el mismo trabajador: una fila por obra, empresa y persona (clave por recurso persona de toda linea casada) y el alta manual hereda la fila del papel | 1 | estandar | M2–M6 en el portal |
| F-051 | Extraccion fila a fila: cada numero manuscrito a la fila en la que esta escrito, no a la mas cercana | 1 | estandar |  |
| F-059 | La IA no lee bien el PDF con /Rotate: sv2 le manda la página escaneada ya derecha, como la ve un visor | 1 | estandar | nada: M4 OK el 2026-10-25 (los 6 partes sin obra reprocesados: 6 convertida, 0 error, obra y fecha leídas en los 6; partes nuevos 0ef28361, b7599bcb, f1e8900d, e8ff17d2, fc892aaf, 7b26d9df) |
| F-060 | Racha de incidencia con CIZ móvil: el primer día abre con su CI* y el fin (CIZ) se mueve editando la línea de Sigrid hasta que llega un día con horas | 1 | critico | MOVER_CIZ ENCENDIDO por el humano el 2026-10-25 (sv5 ca-sv5-transfer--0000003 12:08:43Z, luego sv4 ca-sv4-front--0000002 12:09:28Z; sanos, sin Traceback). M4: línea base 0 recursos-mes con más de un CIZ de partes desde 20261025; repetirla cuando se hayan aprobado incidencias. DA3 confirmada en Sigrid; DA6 la sustituye F-062 |
| F-062 | Incidencia: el primer día escribe el CI* y también el CIZ ese mismo día; si la racha sigue, el CIZ se mueve (como hace Administración) | 1 | critico | Desplegada 2026-10-26 (sv5 r20261026140625, sv4 r20261026140755); M6: repetir la lectura cuando se aprueben incidencias (n > 0, grupos = 0); vista calendario de Administración |
| F-063 | sv2: la consulta de existencia de obra de F-058 tiene que usar el índice (hoy 12–16 s frente al tope de 5 s) | 1 | estandar | Desplegada en sv2 r20261026094916 (2026-10-26 08:51:31Z). Pendiente: M2 (motivo/resultado de relectura en partes) y M4 (tiempos de [obra-sigrid] en Log Analytics) cuando haya partes |
| F-002 | Cola q-transfer para aprobación asíncrona | 2 | critico |  |
| F-013 | Informe de validación de datos Sesame por trabajador | 2 | estandar |  |
| F-021 | Escribir la cuenta analitica en las lineas que sv5 registra en Sigrid | 2 | critico |  |
| F-022 | Aprobar solo las lineas seleccionadas (visibles) en la vista detallada de obra o persona | 2 | critico |  |
| F-046 | Reajuste en Sigrid al aprobar: al aprobar el segundo parte del dia, editar con aviso previo el primero ya aprobado o registrado para llevarlo al reparto ponderado de F-045 | 2 | critico | M6 |
| F-053 | Pisar sin borrar: el pisado de conflictos de sv5 pone a 0 en Sigrid en vez de hacer DELETE | 2 | critico | M4 |
| F-058 | sv2: si la cabecera sale vacía o su obra no existe en Sigrid, relee la página con Gemini y se queda con su cabecera; el prompt avisa de la cabecera | 2 | estandar | Desplegada en sv2 r20261026094916 (2026-10-26 08:51:31Z). Pendiente: M2 (motivo/resultado de relectura en partes) y M4 (tiempos de [obra-sigrid] en Log Analytics) cuando haya partes |
| F-061 | Borrar todas las líneas de un parte (y vaciar la papelera) deja el parte activo y vacío, que bloquea su reproceso | 2 | estandar | desplegar sv4 (humano), M1 en el portal y M2: el humano lee el informe de limpiar_partes_vacios.py y lo ejecuta con --ejecutar --esperados N |
| F-003 | Integración sesame-api: festivos y jornada reales | 3 | critico |  |
| F-024 | Lineas que quedan en 'encolado' en el portal aunque el parte ya esta registrado en Sigrid | 3 | critico |  |
| F-012 | Estudio: candef de 9h, viernes y jornada semanal particularizable | 4 | documental |  |
| F-025 | Incompatibilidad incidencia/horas extra el mismo dia (p.ej. baja por maternidad con hora extra) | 4 | estandar |  |
| F-049 | Portal: el editor de celda de la matriz de obra muestra siempre ordinarias y extra y permite añadir la línea que falta | 4 | critico | M2–M8 en el portal |
| F-054 | Un parte sin obra o sin fecha leídas va siempre a revisión | 4 | estandar | releer los 6 partes sin obra cuando F-059 esté desplegada |
| F-004 | Congelar registros aprobados | 5 | estandar |  |
| F-010 | Saneamiento: resincronizar orm_models.py entre sv3 y sv4 | 6 | estandar |  |
| F-015 | Jornada del día por jornada semanal derivada del candef y último laborable (extras sv3 + avisos sv4) + tabla de excepciones empleado_jornada | 7 | estandar |  |
| F-038 | Subir a 500.000 el límite de filas de las lecturas de Sigrid en sv2–sv5 (antes 1.000 en sv5 y 10.000 en el resto) | 7 | estandar | M1 (lecturas reales de obras grandes; no bloquea). Desplegada sv2–sv5 el 2026-10-24 (r20261024215445); M2 OK |
| F-016 | Pantalla de administración de empleado_jornada en el portal (sv4) | 8 | estandar |  |
| F-017 | Identidad real de Easy Auth en el portal (sv4) | 8 | estandar |  |
| F-005 | Retirar graphkey_nobom.json del arbol y dejar constancia de GRAPH_KEY en Key Vault | 9 | documental |  |
| F-019 | Horas aprobadas de los trabajadores con codigo de hora mes viajan a dedicacion (porcentajes) en lugar de a Sigrid | 9 | critico | interruptor MENSUALES_A_DEDICACION apagado: falta la feature espejo en porcentajes y la M3 |
| F-020 | Ingesta de sv1: correos adjuntos (message/rfc822) encadenados hasta encontrar el PDF | 10 | estandar |  |

## Detalle

### F-056 · Trabajadores con franquicia de extras: al cerrar el mes, aviso y línea de ajuste el último laborable

estado **spec lista** · prioridad 3 · rigor `critico` · SDD sí · rama `feature/F-056-franquicia-de-extras`

**Spec**: aprobada (DA1–DA20 = A) · `partes-wt-f056`

Petición del humano del 2026-10-22, literal: «hay trabjadores que tienen solo extras aa partir de un numero de extras. de esta forma funciona normal pero al reistrar el mes nomina (ultimo dia laborable), debe salir un aviso de si ajustar horas. de esta forma estos trabaajdores solo tienen horas extras si han hecho mas de x. si tiene menos se añade el ultimo dia una linea de ajuste que resta el numero de extras para que salga 0, y si es mas de x, esa linea resta x.» Regla: algunos trabajadores tienen una franquicia mensual de X horas extra que no cobran. Durante el mes las extras se registran como siempre; al registrar el último día laborable del mes (el que cierra la nómina) el portal avisa y ofrece ajustar: si las extras del mes son menos de X, se añade ese día una línea de ajuste que resta todas (el mes queda en 0 extras); si son X o más, la línea resta X. Pendiente de spec; preguntas para el spec-author: dónde se guarda X por trabajador (¿empleado_jornada de F-015/F-016, una columna nueva, Sigrid?) y si es mensual; qué cuenta como extras del mes (todas las obras y tipos de hora extra, también las de reajuste F-046); en qué obra y con qué tipo de hora y precio va la línea negativa si el trabajador tiene varias obras ese día; qué pasa si el último laborable se registra antes que otros días del mes o se reabre (F-034 parte abierto) y cómo se recalcula sin borrar en Sigrid (F-053: se edita la línea, no se borra); en qué pantalla sale el aviso (aprobación de sv4) y si se puede rechazar; y que sv5 siga siendo el único que escribe. Decisión del humano del 2026-10-22/23 («si a todo, pon la nueva feature como primera y lanza spec»): primera de la cola, spec en marcha.

### F-055 · sv5 omite las líneas sin fecha válida (no abre partes del periodo 0/00 ni de años mal tecleados)

estado **spec lista** · prioridad 4 · rigor `critico` · SDD sí · rama `feature/F-055-sv5-omite-lineas-sin-fecha`

**Spec**: escrita, pendiente de aprobación · `partes-wt-f055`

Origen: DA5 de F-054, aprobada por el humano el 2026-10-21 («apruebo F-054 y la DA5»). Una línea de un parte sin fecha viaja de sv4 a sv5 con fecha_int = 0 (int(r.fecha_int or 0) en lineas_para_registro) y sv5 la acepta: con SigridFake, ejecutar da de alta PT0/00001 del periodo 0/00 y escribe la línea con fec = 0; con 20261340 abre un parte de 2026/13. No ha pasado (M1 de F-054: 25 líneas sin fecha, ninguna enviada), pero 15 con obra son aprobables hoy y en Sigrid no se borra. sv5: función pura motivo_fecha_no_valida (application/services/fecha_linea.py; válida = entero, del calendario, entre 01/01/2026 y hoy + 31 días) y paso 2a de RegistroPipeline.preparar: la línea se omite con «fecha_no_valida: …» antes de leer nada de Sigrid (recursos, reshor, partes), manda sobre las demás omisiones y sobre dedicacion, y vale para preflight, ejecutar, la cola q-transfer y las extras nuevas del reajuste F-046. fecha_int pasa a opcional en LineaIn y LineaEntrada (null u omitido = sin fecha, sin 422). sv4, sv3, esquema y colas no cambian; F-034, F-053 y F-031 tampoco. Doc: ARCHITECTURE semántica 6 y azure-apps/partes.md con nota informativa a porcentajes. Decisiones DA1-DA9 y M1-M3 en specs/F-055-sv5-omite-lineas-sin-fecha/design.md §9 y §11.

### F-047 · Parte nuevo en espera hasta que sv3 reparta sus horas (ordinaria y extra)

estado **spec lista** · prioridad 5 · rigor `critico` · SDD sí · rama `feature/F-047-parte-nuevo-en-espera`

**Spec**: aprobada (DA1–DA10) · `partes-wt-f047`

Pedida por el humano el 2026-10-14 (idea aprobada) tras dos quejas de Administracion el mismo dia: un parte recien entrado «no resta las horas» y «si sales y vuelves a entrar, sale bien». Causa: sv3 guarda el parte con las horas leidas (commit) y despues ejecuta las conciliaciones, cuyo conciliar_todos reparte ordinaria y extra; entre una cosa y otra pasan 20-40 s (medido el 2026-10-14) y el portal ensena las horas sin repartir y no se refresca solo. LO QUE SE PIDE: reutilizar el seguimiento de F-043 sin columnas nuevas. sv3 escribe recalculo_pedido_id = id del documento en el mismo commit en que guarda un parte nuevo y, tras conciliar sin excepcion, lo marca terminado con el UPDATE condicional de F-043. sv4 deduce el motivo (pedido = id => parte nuevo), lo pinta en obra, trabajador, detalle y listado de partes con textos propios («procesando…»), mantiene el 409 de F-043, excluye de la aprobacion los partes en espera y ofrece Actualizar al terminar. Nada recarga solo. El algoritmo de reparto es F-045.

### F-052 · Sincronizar con Sigrid: desde una obra o una persona, leer Sigrid, comparar línea a línea con el portal y conciliar una a una o en masa

estado **spec lista** · prioridad 6 · rigor `critico` · SDD sí · rama `feature/F-052-sincronizar-con-sigrid`

**Spec**: escrita, pendiente de aprobación · `partes-wt-f052`

Pedida por el humano el 2026-10-20 («añade una spec de sincronizar, de forma que dentro de una obra o una persona se pueda dar a sincronizar lea sigrid y compare contra lo que hay en el portal, eso nos permitira conciliar linea a linea o en masa»). Botón «Sincronizar con Sigrid» en /obras/{clave} y /trabajadores/{clave} (clave rec- de F-050) para el periodo visible: sv5 (dueño del synckey) lee hmores del ámbito y por synckey en solo lectura (POST /api/sincronizar/leer, paginado, truncated = error, sin lock) y sv4 clasifica cada línea en 11 clases (igual, distinta, anulada_en_sigrid, borrada_en_sigrid, en_sigrid_sin_registrar, pendiente, no_viaja, en_vuelo, solo_sigrid_nuestra/ajena/manual). Primera entrega (DA1 = A recomendada): acciones hacia el portal con confirmación y actor (marcar_registrada, traer_de_sigrid de horas sobre líneas registrado, y reutilizando lo existente a_papelera, reaprobar y restaurar); la escritura en Sigrid vía sv5 (llevar_a_sigrid con el reajuste de F-046, poner a 0 en Sigrid, importar al portal) va en otra feature. En Sigrid no se borra: F-052 no escribe en Sigrid. Reutiliza F-024 (comprobación y borrado_sigrid), F-022 (ámbito), F-017 (actor), F-042 (recálculo), F-043 y F-046 (guardas). Resultado efímero, sin esquema nuevo. Depende de F-050. Decisiones DA1-DA10 y M1 de dimensionado (solo lectura) en specs/F-052-sincronizar-con-sigrid/design.md §8-§9. Hallazgo H1 (fuera de alcance): el pisado de conflictos de sv5 hace DELETE y el candado de línea registrada dice «borra la línea en Sigrid».

### F-057 · Editor de celda: el pedido de recálculo incluye todos los partes con líneas en la celda

estado **spec lista** · prioridad 7 · rigor `estandar` · SDD sí · rama `feature/F-057-pedido-celda-todos-los-partes`

**Spec**: aprobada 2026-10-24 (DA1–DA5 = A) · `partes-wt-f057`

Observación 2 del reviewer de F-049 (progress/review_F-049.md), apuntada como feature por decisión del humano del 2026-10-23 («si a todo»). Si una celda de la matriz junta líneas de dos partes de la MISMA obra (F-050, varios partes) y solo cambia una, el otro parte no recibe el pedido compartido de recálculo: no es «tocado» (R23 de F-049) ni «afectado» (R38 excluye las líneas de la celda), pero la pasada completa de sv3 sí puede reescribir sus extra_auto; queda el residual R-g de F-043 en ese parte durante la pasada (~30 s). Propuesta: incluir en el pedido todo documento con líneas en la celda. Pendiente de spec.

### F-032 · Activar Sesame en produccion: festivos de cada trabajador leidos de Sesame HR

estado **bloqueada** · prioridad 8 · rigor `estandar` · SDD sí · rama `feature/F-032-sesame-festivos-produccion`

**Spec**: en `dev`; feature bloqueada por decisión del humano (2026-10-07)

Pedida por el humano el 2026-10-06. La integracion ya existe en el codigo (F-003 done, F-013 done: clientes `infrastructure/sesame/` de sv3 y sv4, CalendarioProvider, festivos por calendario asignado a cada trabajador), pero en Azure esta APAGADA: el arranque de sv3 dice «[sesame][wiring] DESACTIVADO (faltan SESAME_API_*); los festivos salen del JSON local config/calendario_laboral.json». Motivo: el servicio pasarela `sesame-api` (repo C:/Users/pgris/PycharmProjects/sesame-api, uvicorn local en 8006) NO esta desplegado en Azure y su rediseño estaba sin commitear a 2026-08-18. LO QUE SE PIDE: vincular partes con Sesame y leer de ahi los festivos. A DECIDIR EN LA SPEC: (a) desplegar sesame-api en Azure (repo propio, su documento en azure-apps; red: ingress interno en el mismo Container Apps Environment que partes o el que corresponda; secretos SESAME_TOKEN y API_KEYS en Key Vault), trabajo fuera de este repo que el humano debe autorizar; (b) configurar SESAME_API_BASE_URL y SESAME_API_KEY (secretref) en sv3 y sv4 y verificar el cableado; (c) comportamiento si Sesame no responde (hoy: fallback al JSON local; mantenerlo y avisar); (d) contraste de los festivos de Sesame con el JSON actual y por calendario (Madrid por defecto, Alicante, Malaga, Tomares, Sevilla) antes de encender; (e) que pasa con los partes ya conciliados (recalculo de extras en festivo); (f) jornada y contratos: Sesame HR tenia 0/218 contratos a 2026-08-18 y por eso F-011 sigue aparcada; esta feature es SOLO festivos. Servicios: sv3 y sv4 (configuracion), mas sesame-api (otro repo). Actualizar azure-apps/partes.md (pasamos a consumir sesame-api).

### F-027 · Escapar HTML en los modales heredados del portal (nombres que vienen del OCR)

estado **pendiente** · prioridad 9 · rigor `estandar` · SDD no · rama `feature/F-027-escape-modales`

**Spec**: no lleva (sdd: false)

Observacion O4 del reviewer de F-022 (2026-10-01): resumenHtml, conflictosHtml, avisosCalendarioHtml y resultadoHtml de static/app.js (sv4, anteriores a F-022) pintan sin esc() nombre, motivo y cod, y esos nombres pueden venir del OCR de un PDF recibido por correo (inyeccion de HTML en el portal). Ademas (O5) sondearGrupos mete g.clave sin escapar en un querySelector. Aplicar el esc() existente de F-024 y CSS.escape en el selector, con tests que ejecuten el JS con node como en F-021/F-022. Solo sv4.

### F-026 · Partes enviados como foto del movil se ven demasiado grandes en el portal

estado **pendiente** · prioridad 10 · rigor `estandar` · SDD no · rama `feature/F-026-visor-fotos`

**Spec**: no lleva (sdd: false)

Reportado el 2026-09-30 por Juan Romero ('RV: CAPTURAS'): un parte metido como foto tomada con el movil se dimensiona muy grande al verlo en el portal. Ajustar el visor del documento en sv4 para que las imagenes se escalen al contenedor (como los PDF). Servicio: sv4. sdd=false salvo que la investigacion muestre que hay que tocar la ingesta (sv1) o el almacenamiento de la imagen.

### F-018 · Log de auditoria de acciones del portal (quien hizo que y cuando)

estado **pendiente** · prioridad 11 · rigor `estandar` · SDD sí · rama `feature/F-018-log-auditoria-portal`

**Spec**: borrador en la rama `worktree-agent-ad862e62640d64553`, sin presentar

Pedida por el humano el 2026-08-20 al explicarle F-017. Hoy NO existe un registro de auditoria del portal. Lo mas parecido es la tabla undo_log, pero NO sirve como tal: su proposito es DESHACER (guarda el estado anterior en payload para restaurarlo), solo cubre las acciones reversibles -reasignar, casar, editar horas/fecha/obra-, y deja fuera las aprobaciones, los borrados, las excepciones de jornada de F-016 y cualquier accion administrativa. Ademas sus filas se marcan como undone y su vida la manda la funcion de deshacer, no la de auditar. ALCANCE A DECIDIR EN LA SPEC: que acciones se registran (como minimo las que hoy escriben approved_by/deleted_by y las cinco pantallas de administracion), que se guarda de cada una (actor, cuando, que entidad, que cambio, desde donde), donde vive (tabla propia de la base partes frente a reutilizar undo_log, que el spec-author debe valorar y descartar con argumentos), si hay pantalla de consulta o basta con SQL, y cuanto se conserva. Valorar tambien si sv3 y sv5 deben escribir en el mismo log: sv5 es el unico que escribe en Sigrid, y hoy esa escritura no deja rastro de quien la origino. DEPENDE DE F-017: sin identidad real de Easy Auth, este log registraria NULL en el campo mas importante, que es el actor. Hacerla antes seria construir un libro de firmas sin firmas. HALLAZGO del 2026-08-21, al verificar F-017 desplegada con GET /whoami: Easy Auth inyecta TRES cabeceras, y una es X-MS-CLIENT-PRINCIPAL-ID, el oid INMUTABLE del usuario, disponible sin decodificar el token. F-017 renuncio a guardar el oid por no tener columna donde ponerlo y remitio a esta feature. Si F-018 crea tabla propia, valorar dos columnas: actor (UPN legible, que puede cambiar) y actor_id (oid, que no). Es la diferencia entre una auditoria que aguanta un cambio de nombre y otra que no.

### F-006 · tipo_hora_resolver con auxhor.ext para variantes HE%

estado **pendiente** · prioridad 12 · rigor `estandar` · SDD sí · rama `feature/F-006-tipo-hora-ext`

**Spec**: sin spec

El resolutor de tipos de hora debe usar auxhor.ext (¿computa como extra?) para reconocer todas las variantes HE% de la ficha del recurso, en lugar de depender del prefijo del código.

### F-007 · Revisión del prompt de extracción de sv2 (J.310 rev.1)

estado **pendiente** · prioridad 13 · rigor `critico` · SDD sí · rama `feature/F-007-prompt-sv2-evals`

**Spec**: sin spec

Revisar el prompt YAML de sv2 con el caso J.310 rev.1. Antes de tocar el prompt hay que montar la verificación que lo proteja: banco de evals con ground truth (como la F-011 de albaranes) y declaración en harness/rutas_sensibles.json — un cambio de redacción de prompt no lo caza ningún test unitario.

### F-008 · Modelo de roles en el portal (sv4)

estado **pendiente** · prioridad 14 · rigor `estandar` · SDD sí · rama `feature/F-008-roles-portal`

**Spec**: sin spec

Introducir roles en el portal (p. ej. administrador vs revisor) para restringir acciones administrativas: la primera es el reencolado de mensajes poison (F-002), que hoy queda disponible para cualquier usuario autenticado por decisión explícita del humano (2026-08-13). Base: claims de Easy Auth/Entra (grupos o app roles) leídos por sv4.

### F-011 · Jornada reducida por días desde Sesame sustituye al candef

estado **pendiente** · prioridad 15 · rigor `critico` · SDD sí · rama `feature/F-011-jornada-reducida-dias`

**Spec**: sin spec

Corrección de alcance sobre F-003, pedida por el humano el 2026-08-16 (entonces urgente): el candef sigue siendo la jornada teórica como hasta ahora (con el fallback de 8h si falta o es bajo), PERO en los días que Sesame indique jornada reducida para un trabajador, el candef se sustituye SOLO esos días por la jornada reducida (previsiblemente 7h). Afecta al cómputo de extras (sv3) y a los avisos de jornada incompleta (sv4), vía el resolutor único jornada_efectiva que F-003 dejó preparado. OJO: la spec debe verificar qué puede exponer sesame-api sobre días/periodos de jornada reducida (hoy /jornada solo da un booleano heurístico sin fechas) — probablemente amplía la petición P1 a ese proyecto; como F-003, valorar si se implementa apagada con el enchufe listo. REPRIORIZADA A BAJA por el humano el 2026-08-18, tras el informe de F-013: Sesame HR no tiene NINGÚN contrato cargado (0 de 218 empleados; /contract/v1/.../current-contract da contract_not_found para todos), así que hoy no existe fuente de jornada ni de reducida en Sesame. La spec deberá partir de decidir la fuente (contratos en Sesame cuando RRHH los cargue, módulo de horarios de Sesame, o tabla propia). Mientras tanto el candef sigue mandando (F-003 apagada; y encendida, sin contrato Sesame devuelve None y cae al candef). NOTA F-012 (2026-08-18): su fuente candidata es la tabla empleado_jornada (patrón explícito con vigencia) + emphis.porjorlab de Sigrid (% de jornada: 87,5/75/50…, con datos reales), no los contratos de Sesame.

### F-001 · Test de estructura del monorepo (calentamiento)

estado **terminada** · prioridad 1 · rigor `estandar` · SDD no · rama `feature/F-001-test-estructura`

Feature trivial para validar el circuito completo del arnés en este repo: un test en tests/ (raíz) que valida harness/servicios.json contra el árbol real — cada ruta declarada existe y cada servicio Python tiene main.py. Igual que la F-001 de albaranes.

### F-023 · Casado de trabajador/recurso contra Sigrid: solo los dados de alta y por la empresa correcta

estado **terminada** · prioridad 1 · rigor `critico` · SDD sí · rama `feature/F-023-recurso-alta-empresa`

Pedida por el humano el 2026-09-30, prioridad maxima. Al coger el recurso del trabajador de un parte (casado contra el maestro emp/con de Sigrid por DNI -> emp.reside), (1) seleccionar SOLO los que estan dados de alta y (2) seleccionar POR EMPRESA, porque un mismo trabajador/recurso puede existir en 2 empresas. ESTADO ACTUAL: sv3 (infrastructure/sigrid/sigrid_api_client.py, _SQL_EMPLEADOS_BASE + fetch_empleados) filtra por una empresa FIJA (SIGRID_EMPRESA, con.emp = ?) y NO filtra altas/bajas; sv4 tiene su propio fetch_empleados en infrastructure/sigrid/sigrid_lookup_client.py (catalogo para corregir a mano en el portal) y sv5 usa SIGRID_EMPRESA al escribir. A DECIDIR EN LA SPEC: (a) que significa 'dado de alta' en Sigrid para un empleado/recurso (campo fecbaj u otro de emp/con/res; ver azure-apps/sigrid_tablas.md) y si se evalua a hoy o a la FECHA DEL PARTE; (b) DE DONDE SALE LA EMPRESA de cada parte: previsiblemente la empresa de la obra del parte (con.emp de la obra), en lugar del SIGRID_EMPRESA fijo; confirmar con el humano; (c) que pasa si el DNI casa en las 2 empresas y la obra no desempata, o si solo casa con un trabajador de baja (sin casar + revision, no elegir uno al azar); (d) coherencia con sv5, que escribe con SIGRID_EMPRESA fijo: si la empresa pasa a ser la de la obra, la escritura (hmo/hmores) debe usar la misma. Servicios: sv3 (casado), sv4 (catalogo del portal) y probablemente sv5. Los clientes infrastructure/sigrid/ estan en la lista cerrada de duplicacion tolerada: quien toque una copia cambia todas en la misma feature. RIGOR critico: decide a que recurso se imputan horas que se escriben en Sigrid en produccion. ACLARADO 2026-09-30: caso real de Juan Romero ('RV: CAPTURAS'): cogio el recurso MO/0239 dado de baja y no aviso de que existian dos recursos con el mismo DNI. El parte en papel TRAE LA EMPRESA EN EL MEMBRETE (p.ej. Porsan): la empresa del parte se extrae del membrete (sv2) y desempata obras gemelas y recursos. Las consultas a sigrid-api se paginan (OFFSET/FETCH); la instancia dev admite 500.000 filas por peticion.

### F-028 · Detalle de obra y de trabajador a todo el ancho de la ventana

estado **terminada** · prioridad 1 · rigor `estandar` · SDD no · rama `feature/F-028-ancho-detalle`

Peticion del humano (2026-10-02, captura del detalle de obra): el contenido de todas las paginas de sv4 esta topado a 1500 px por .container (static/styles.css), y en ventanas mas anchas la matriz de dias y la tabla de lineas del detalle de obra y de trabajador sacan scroll horizontal aunque sobre espacio. Solucion aprobada: base.html admite una clase extra para el contenedor principal (bloque Jinja), obra_detail.html y trabajador_detail.html la usan, y styles.css la define a todo el ancho menos 16 px por lado. Los listados conservan el tope de 1500 px. Fuera: rehacer columnas de la tabla de lineas. Solo sv4.

### F-029 · El logotipo de Ruesma (ruΞsma) se reconoce como empresa 1 en el membrete

estado **terminada** · prioridad 1 · rigor `estandar` · SDD no · rama `feature/F-029-alias-logo-ruesma`

Hallazgo del lider revisando las plantillas J.310 rev. 1 (2026-10-05): el membrete de la plantilla de Ruesma es el texto 'ruΞsma' (Xi griega, como el logotipo real). text_match.normalize convierte toda letra no latina en espacio, asi que 'ruΞsma', 'RUΞSMA' y 'ru≡sma' quedan 'ru sma' y no casan con el alias RUESMA de services/partes-persistencia/config/empresas_membrete.yaml: la empresa del membrete de los partes de Ruesma queda desconocida (sin_alias) y en las obras gemelas (codigo en empresas 1 y 28) el desempate depende solo de los trabajadores. Solucion aprobada por el humano: anadir a la empresa 1 el alias del logotipo (RUΞSMA, normalizado 'ru sma') con comentario, sin tocar codigo ni el prompt de sv2. Solo sv3 (config versionada). La plantilla de Porsan ('PORSAN E HIJOS CONSTRUCCIONES, S.L.') ya casa con 28.

### F-030 · Trabajadores con recurso en Sigrid pero sin ficha de empleado: casar el recurso por DNI

estado **terminada** · prioridad 1 · rigor `critico` · SDD sí · rama `feature/F-030-recurso-sin-ficha`

Prueba real de Administracion (2026-10-05, partes de Porsan obra 0724 del 25 y 28/09): un trabajador con recurso de mano de obra de alta en la empresa 28 (res.cif = su DNI) pero SIN ficha en `emp` sale 'Sin recurso' en el portal, porque sv3 casa primero contra la ficha de empleado (emp, por DNI o nombre) y llega al recurso por emp.reside. Alcance medido en Sigrid el 2026-10-05: recursos MO/ de alta sin ficha de empleado por DNI: 19 de 229 en la empresa 1 y 18 de 39 en la 28. LO QUE SE PIDE (humano, 2026-10-05): cuando no haya ficha de empleado, sv3 casa el RECURSO directamente por DNI (res.cif) entre los recursos de la empresa de la obra y de alta (los mismos candidatos que ya exige sv5 al escribir), normalizando el DNI con o sin ceros a la izquierda (el parte de prueba lo traia con y sin el 0). A DECIDIR EN LA SPEC: (a) si ademas se casa por nombre contra el recurso (formato 'APELLIDOS, NOMBRE') o solo por DNI; (b) que se guarda como empleado en la linea cuando no hay ficha (empleado_ide nulo, metodo nuevo) y como lo ve el portal (sv4) y el resto del pipeline (jornada, extras, calendario, Sesame, que hoy cuelgan del empleado); (c) la lista cerrada de duplicacion de CLAUDE.md: IndicePersonas.elegir_recurso (sv3) y elegir_por_dni (sv5) son copias vigiladas, quien toque una cambia todas; (d) reprocesar los partes ya entrados sin recurso; (e) CUENTA ANALITICA EN PORSAN: Administracion dice que en Porsan no se pone cuenta analitica; desde F-021 sv5 escribe hmores.caaide con la cuenta del centro de la obra: comprobar si las obras de la empresa 28 la tienen y proponer si para la empresa 28 debe ir 0 (puede ser una DA separada o feature aparte). Servicios previstos: sv3 (casado), quiza sv4 (vista) y sv5 (cuenta analitica). RIGOR critico: cambia que recurso se escribe en Sigrid.

### F-031 · El parte registrado en Sigrid genera su asiento en la cuenta analitica de la obra

estado **terminada** · prioridad 1 · rigor `critico` · SDD sí · rama `feature/F-031-asiento-analitico`

Peticion del humano (2026-10-05), URGENTE, inmediatamente despues de F-030. Fuente: correo de Juan Romero (Dir. Admon y Control de Costes) del 2026-09-29 «ARBOL ANALITICO OBRAS»: las cuentas analiticas de una obra cuelgan de su CENTRO DE COSTE (p. ej. obra 0702 -> centro 0702, ficha Obra > Contabilidad > «Cuentas analiticas»: 0702 centro de coste asociado, 0702.INGR02 certificacion, 0702.INGR01 produccion). El arbol del centro tiene C·COSTES (CD costes directos, CI costes indirectos, CP costes proporcionales CP0001..CP0010) e I·INGRESOS (INGR01..03). «Dentro del asiento se define el financiero, y la cuenta analitica del gasto (6XX)»: ejemplo de asiento con apunte 6260000000 y Desglose Analitico al centro 0702, cuenta 0702.CP0004 AVALES, 100 %. LO QUE SE PIDE: que el coste de mano de obra de los partes que sv5 registra en Sigrid quede imputado en la analitica de la obra (asiento/desglose analitico al centro de coste de la obra con la cuenta de coste que corresponda). RELACION CON F-021 (done): hoy sv5 escribe hmores.caaide = cuenta del centro de la obra con la subcuenta de la ficha de horas del recurso (reshor.caaide); en Porsan sale 0 (ningun recurso tiene cuenta). A INVESTIGAR EN LA SPEC (solo lectura en Sigrid y en azure-apps/sigrid_tablas.md): si Sigrid genera el asiento analitico a partir de hmores.caaide por algun proceso propio (y por que no aparece), o si hay que escribir el apunte/desglose analitico en otras tablas; que cuenta de coste corresponde a la mano de obra (CD..., por categoria o tipo de hora), importe (horas x precio de reshor), fecha y diario; como lo hace hoy Administracion a mano con partes tecleados (comparar con lineas reales de 2026); idempotencia con synckey y que pasa al borrar o reaprobar (F-024); empresas 1 y 28. Solo sv5 escribe en Sigrid. RIGOR critico: escribe contabilidad en Sigrid. Validar con Juan Romero antes de implementar.

### F-033 · Portal: columna Empresa en el listado de obras

estado **terminada** · prioridad 1 · rigor `estandar` · SDD sí · rama `feature/F-033-columna-empresa`

Incidencia del humano (2026-10-07), URGENTE. En el listado de obras del portal (sv4) la obra 0678 salia «duplicada»: en Sigrid hay dos fichas de obra 0678, una de Ruesma (empresa 1) y otra de Porsan (empresa 28), y la fila solo pintaba «codigo · nombre». Alcance final decidido por el humano («lo unico que hay que hacer es que busque la empresa a la que esta vinculada cada linea»): columna «Empresa» con su filtro SOLO en el listado de obras; el dato sale de parte_documents.empresa de los partes de la fila, con respaldo por la empresa de los recursos de sus lineas dentro de la BBDD partes; nombres 1 Ruesma, 28 Porsan; sin Sigrid ni configuracion nueva. El alcance inicial (detalle de obra, vistas de parte, YAML de nombres) se descarto.

### F-034 · sv5 solo escribe en partes de Sigrid abiertos (estado 1, En registro)

estado **terminada** · prioridad 1 · rigor `critico` · SDD sí · rama `feature/F-034-escribir-solo-en-partes-abiertos`

**Pendiente**: M3 (Administración cierra PT26/00375) y M4

Pedida por el humano el 2026-10-07: «solo se puede escribir en partes abiertos (1 REG)». sv5 solo puede añadir o modificar lineas (hmores) en un parte (hmo/con) cuyo con.est sea 1 (En registro); nunca en Cerrado (3), Imputado (10) ni cualquier otro estado. A REVISAR EN LA SPEC: que hace hoy sv5 tras F-031 (partes_del_periodo, complementario cuando el parte del periodo no esta En registro, alta protegida compartida con porcentajes F-037) y si queda algun camino que escriba o actualice/borre lineas (synckey ya existente, reaprobacion, borrado) en un parte que no este en estado 1; comprobacion del estado DENTRO del lock y justo antes de escribir; que se le dice al usuario en el portal; reglas gemelas con porcentajes (estado_parte.py es copia en porcentajes: si cambia, aviso a porcentajes).

### F-035 · Portal: elegir trabajador entre recursos activos de Sigrid, filtrados por empresa

estado **terminada** · prioridad 1 · rigor `estandar` · SDD sí · rama `feature/F-035-selector-recursos-por-empresa`

Pedida por el humano el 2026-10-07. Hoy los selectores de trabajador del portal (sv4) tiran de EMPLEADOS (emp) y no encuentran a quien solo tiene ficha de recurso (ejemplo real: en Conciliar no aparece un trabajador de Porsan que solo tiene recurso, el caso de F-030). LO QUE SE PIDE: (1) en Conciliar y al crear un parte nuevo, el selector de trabajador lista RECURSOS ACTIVOS de Sigrid (de alta a la fecha), no empleados; (2) en Conciliar y en partes se puede ELEGIR LA EMPRESA y el selector solo ofrece recursos de esa empresa; (3) en el detalle de obra, al cambiar el trabajador de una linea, tambien recursos activos y SOLO los de la empresa de esa obra (cada fila de obras es obra+empresa: la 0678 Carmona existe en Ruesma y en Porsan). A REVISAR EN LA SPEC: endpoints /api/sigrid/... de sv4 que alimentan los combos, regla de alta compartida (de_alta, lista cerrada de CLAUDE.md, F-023), que se guarda en la linea al elegir recurso (recurso_ide, empleado_*, DNI) y su efecto en conciliacion y registro (sv3/sv5 eligen recurso por DNI y empresa de la obra).

### F-036 · sv3: casar el trabajador leido contra los recursos persona de la empresa del parte

estado **terminada** · prioridad 1 · rigor `critico` · SDD sí · rama `feature/F-036-casado-contra-recursos`

Pedida por el humano el 2026-10-07: «el macheo de la IA tambien debe hacerlo contra recursos, no empleados»; «en el punto donde sv3 casa, que case contra la lista de recursos de la empresa, que viene de pasos anteriores»; «si no hay dni en el recurso que lo traiga de empleado». sv2 no recibe lista de personas: el casado lo hace sv3 (DNI, alias, nombre) y hoy es contra fichas de empleado (emp) con el respaldo F-030 de fichas de recurso. LO QUE SE PIDE: el casado de sv3 pasa a ser contra los RECURSOS persona (res.cla = 1, criterio de porcentajes) de la empresa del parte y de alta a la fecha; DNI del recurso = res.cif o, si vacio, el de su ficha de empleado (res.conide). A REVISAR EN LA SPEC: que se guarda en empleado_* y recurso_*, alias, respaldo F-030, conciliador de recursos y lista cerrada de CLAUDE.md (elegir_recurso sv3 / elegir_por_dni sv5), efecto en sv5, recalculo de partes activos al desplegar y como medir el impacto antes.

### F-037 · sv3: no duplicar la extra automatica cuando su linea base esta omitida y la extra ya esta registrada

estado **terminada** · prioridad 1 · rigor `critico` · SDD sí · rama `feature/F-037-extras-duplicadas-base-omitida`

URGENTE. Incidencia verificada en produccion (solo lectura, 2026-10-07): 7 lineas extra_auto DUPLICADAS en la base partes, todas de la obra 0678 del 01 al 03/10/2026 (Ruesma 4, Porsan 3). Patron: linea base normal con sigrid_estado='omitido' (mensual MCAP sin codigo de hora laborable, o base con 0 horas 'sin horas') + su extra_auto ya 'registrado' en Sigrid + una extra_auto NUEVA identica sin sigrid_estado, mismo document_id/line_index/empleado_line_no/fecha. Mecanismo: revert_extras_auto() de sv3 respeta la extra congelada pero restaura la base no congelada (horas = horas_orig); el calculo de splits del RecursoConciliador la vuelve a partir y apply_extras_splits() inserta otra extra_auto en cada pasada. Riesgo: aprobar la nueva la escribe en Sigrid con otro synckey (extra doble en el ERP). Caso inverso: base registrada y extra no congelada -> la pasada borra la extra y deja la base recortada sin ella. Arreglo: base y extra_auto de la misma pareja se congelan juntas para el recalculo de sv3; la siguiente pasada borra sola los duplicados no congelados.

### F-039 · Portal: mostrar el nombre de la empresa (Ruesma, Porsan) en vez de «empresa N» en combos y Conciliar

estado **terminada** · prioridad 1 · rigor `estandar` · SDD sí · rama `feature/F-039-nombre-empresa-en-combos`

Incidencia del humano el 2026-10-08 (captura): en Conciliar los resultados de la busqueda manual de recursos salen «MO/0266 · ... · empresa 1», «... · empresa 28». Causa: static/app.js empresaSufijo(x) devuelve « · empresa N» y la usan los combos de obra (obraLabel), de trabajador (recLabel) y la busqueda manual de Conciliar. El portal ya tiene los nombres cortos en application/services/empresas.py (NOMBRES_EMPRESA / nombre_empresa, F-033), global Jinja EMPRESAS (F-035) y empresa_nombre en los candidatos de Conciliar. LO QUE SE PIDE: que todo sitio que hoy pinta «empresa N» pinte el nombre corto y «Empresa N» solo si no hay nombre, con una sola fuente de nombres (sin copiar el dict a JS a mano) y tests. Solo sv4.

### F-040 · Recursos sin DNI: proponer por nombre, aprender alias por recurso y poder registrarlos

estado **terminada** · prioridad 1 · rigor `critico` · SDD sí · rama `feature/F-040-recursos-sin-dni-por-nombre`

Pedida por el humano el 2026-10-08: «si no hay DNI en el parte o no hay DNI ni en recurso ni en empleado, que proponga por nombre». Tras F-035/F-036 el trabajador es un RECURSO persona (res.cla = 1) de alta en la empresa del parte; su DNI es emp.dni de la ficha (res.conide) o, si falta, res.cif. Recursos persona de alta SIN DNI en ningun sitio (medido 2026-10-08): Porsan MO/0032 y MO/0033 (obra 0692, el portal no los encuentra), empresa 12 (2), 18 (4), 25 (1). Hoy: (a) sv3 IndicePersonas.candidatos_nombre excluye recursos sin DNI y casar_trabajador agrupa por persona = DNI; (b) sv4 _SQL_RECURSOS_ACTIVOS/RecursoCatalog (F-035, DA3) no los ofrece; (c) el alias aprendido en Conciliar (empleado_alias, empleado_ide NOT NULL) no se guarda para recursos sin ficha de empleado; (d) sv5 verifica recurso_ide por empresa, alta y DNI: un recurso sin DNI no pasa. LO QUE SE PIDE: sv3 propone por nombre entre recursos sin DNI; sv4 los ofrece marcados 'sin DNI' y aprende el alias contra el recurso; sv5 puede registrar una linea con recurso_ide de un recurso sin DNI sin abrir la puerta al recurso equivocado; lista cerrada de CLAUDE.md al dia; medicion de impacto de solo lectura antes de desplegar.

### F-042 · Recalcular el reparto normal/extra al cambiar la fecha de un parte

estado **terminada** · prioridad 1 · rigor `critico` · SDD sí · rama `feature/F-042-recalcular-extras-al-cambiar-fecha`

Pedida por el humano el 2026-10-09: «en este caso el dia 11 al ser domingo lo puso como extras, al cambiar el dia, no ha recalculado, sino que ha puesto eso mismo como extra pero en el dia 1». Parte de la obra 0694: la IA leyo 1/10/26 como 2026-10-11 (domingo) y sv3 lo repartio como no laborable (bases a 0 con horas_orig y sus extra_auto). Al cambiar la fecha a 2026-10-01 en el portal, sv4 update_parte_fecha cambia la fecha del documento y de sus lineas pero no avisa a nadie: el reparto lo calcula solo sv3 (RecursoConciliador.conciliar_todos, que revierte las extra_auto y recalcula todo lo no congelado) y solo cuando llega un mensaje a q-persistencia, asi que queda mal hasta la siguiente ingesta y alguien puede aprobarlo entretanto. LO QUE SE PIDE (alcance cerrado): sv4, al guardar la fecha de un parte (y al deshacer ese cambio, DA1), publica en q-persistencia un mensaje 'recalcular' tras guardar; la fecha se guarda aunque la cola falle y la pantalla avisa. sv3 distingue ese mensaje del de sv2 por el campo 'tipo' y ejecuta su pasada normal (conciliar_todos), sin logica nueva de extras; las congeladas no se tocan. Editar horas, cambiar trabajador u obra y borrar lineas quedan fuera. Permiso: la identidad de sv4 (id-partes-dev) ya tiene Storage Queue Data Contributor sobre la cuenta de colas.

### F-043 · Fecha del parte: rotulo claro, confirmacion antes de moverlo y parte en espera mientras sv3 recalcula las extras

estado **terminada** · prioridad 1 · rigor `critico` · SDD sí · rama `feature/F-043-fecha-del-parte-confirmar-y-recargar`

Pedida por el humano el 2026-10-12 (opcion A) y enmendada el 2026-10-13: «tengo que seguir usando la plataforma para el resto de partes, solo queda en espera el que esta recalculando». En el detalle de obra y de trabajador cada fila lleva un input de fecha (.fecha-edit) que hace PATCH /api/partes/{id}/fecha, y update_parte_fecha mueve el PARTE ENTERO: el humano lo cambio en la fila de un trabajador y movio a los cuatro del parte. Tras el cambio sv3 recalcula el reparto (F-042) en ~1-2 min y el portal no lo refleja. LO QUE SE PIDE: (1) rotular el campo como fecha del parte; (2) antes de guardar, window.confirm con cuantos trabajadores y lineas se mueven y a que dia; cancelar deja la fecha anterior; (3) mientras sv3 recalcula, SOLO ese parte queda en espera (filas marcadas y deshabilitadas, y el servidor rechaza sus ediciones salvo fecha y deshacer, porque una edicion a mitad de pasada se pisa) y el resto del portal sigue usable; al terminar, una tarjeta ofrece Actualizar (recarga conservando scroll y filtros): nada recarga solo. Seguimiento: sv4 marca recalculo_pedido_id antes de publicar, sv3 copia a recalculo_terminado_id el pedido que leyo antes de su pasada (UPDATE condicional), el estado lo pinta el servidor y vence a los 10 min. Cuatro columnas nullables en parte_documents (las dos copias de orm_models.py). Mover una sola linea es F-044. La logica de recalculo de sv3 no cambia.

### F-045 · Reparto ponderado de la jornada entre obras: ordinarias y extras del dia repartidas en proporcion a las horas de cada parte, a medias horas

estado **terminada** · prioridad 1 · rigor `critico` · SDD sí · rama `feature/F-045-reparto-ponderado-entre-obras`

Pedida por el humano el 2026-10-14. Hoy sv3 (_reclasificar_extras_jornada) agrupa por recurso y dia cruzando obras pero recorta las extras desde el registro_id mayor y, si falta jornada, sube solo la ultima ordinaria con una extra negativa: el ultimo parte en llegar se queda todas las extras (10 h + 4 h con jornada 8 = 8+2 y 0+4). F-045 (fase 1, solo sv3, sin esquema ni Sigrid) reparte la jornada del dia entre las obras en proporcion a sus horas (ordinarias + extras explicitas) y dentro de cada obra entre sus lineas, por mayor resto a pasos de 0,5 h (0,25 o 0,01 si las horas no lo permiten) conservando los totales exactos; las extras negativas se mantienen y se reparten igual. Lo congelado sigue fijo (modo residual) y se mide con un WARNING cuando el reparto ideal lo cambiaria. Las lineas en la papelera dejan de pesar. El reajuste en Sigrid de lo ya registrado, con aviso previo al aprobar el segundo parte, se propone como F-046 (design.md §8). Spec: specs/F-045-reparto-ponderado-entre-obras/.

### F-048 · Ordinarias + extras leidas en laborable siguen la regla de jornada: la ingesta suma las extras leidas de cada fila a su ordinaria y el reparto da J + exceso

estado **terminada** · prioridad 1 · rigor `critico` · SDD sí · rama `feature/F-048-solo-extras-en-laborable-como-jornada`

**Pendiente**: M4

Pedida por el humano el 2026-10-15 (literal: «cuando sea laborable, aunque las horas sean extras se usa la regla de 8+x») y ampliada el mismo dia a las filas con ordinarias Y extras: se suman y el total sigue la regla de jornada (J normales + exceso extra, o extra negativa si no llega). Caso 1: 15/10/2026, obra 0678, fila con ordinarias nulas y 10 extras quedo como una extra de 10 h (esperado 8 + 2). Caso 2: 02/10/2026, obra 0686, fila 4 + 5 extras quedo en tres lineas (normal 8, extra_auto -4, extra 5; esperado 8 + 1, dos lineas). Diseno recomendado (DA2, opcion A): el normalizador de sv3 suma las extras leidas > 0 de cada fila a su ordinaria (por partida, ordinarias primero) y guarda lo leido como extra en la columna nueva parte_registros.horas_extra_leidas (dos copias del ORM); el conciliador, F-045, F-037 y F-046 no cambian. En no laborable salen los mismos importes con una linea menos (DA3); sin umbral (DA4). Solo ingestas nuevas; lo congelado (caso 2, ya en Sigrid) seria feature aparte sobre F-046 (solo UPDATE). Toca sv3 y sv4 (ORM gemelo y etiqueta en el portal); sv2 y sv5 no. Se implementa despues de F-046 y F-047. Spec: specs/F-048-solo-extras-en-laborable-como-jornada/.

### F-050 · Misma fila para el mismo trabajador: una fila por obra, empresa y persona (clave por recurso persona de toda linea casada) y el alta manual hereda la fila del papel

estado **terminada** · prioridad 1 · rigor `estandar` · SDD sí · rama `feature/F-050-misma-fila-para-el-mismo-trabajador`

**Pendiente**: M2–M6 en el portal

Pedida por el humano el 2026-10-15: al añadir con «+ Añadir línea» una ordinaria a un trabajador que solo tenía extras, el calendario de la obra lo pinta en dos filas. Causa (verificada en sv4): worker_key_for_registro agrupa por emp-{empleado_ide} y, sin ficha, por el nombre leído; la línea de la IA guarda el leído del papel y crear_parte_manual escribe como leído el nombre de Sigrid; además una persona puede tener en una obra líneas con y sin ficha del mismo recurso; el detalle y el listado de partes agrupan con otra variante, y la vista del trabajador da de alta sin el recurso. Reglas del humano (2026-10-20): «es una linea por obra empresa y persona. puede estar en varias obras, o en 2 empresas» y «en la vista por persona, se juntan las obras. lo que es importante es que en 2 empresas son 2 personas con vistas diferenciadas». F-050 (solo sv4, sin esquema ni Sigrid ni migración): clave rec-{recurso} para toda línea casada con recurso (con o sin ficha) > emp- (ficha sin recurso) > nom- > sin-trabajador, en una sola función para todas las vistas y acciones; «Por persona» una fila por (empresa, persona) con todas sus obras y la empresa a la vista (columna «Empresa» y cabecera del trabajador, con la regla de F-033 sobre la base partes); el alta manual hereda empleado_line_no y leído de la persona en ese parte (si no está, fila nueva al final); la vista del trabajador pasa ficha y recurso al modal; las URL emp- y nom- antiguas redirigen si el destino es único; en los tests existentes solo cambia el literal de la clave. DA1 (opción A), DA1b y DA11 aprobadas por el humano el 2026-10-20, junto con DA2-DA10. M1 (líder, 2026-10-20): 1 fila que se une, 0 fichas sin recurso, 0 DNIs con varios recursos en una obra. Spec: specs/F-050-misma-fila-para-el-mismo-trabajador/.

### F-051 · Extraccion fila a fila: cada numero manuscrito a la fila en la que esta escrito, no a la mas cercana

estado **terminada** · prioridad 1 · rigor `estandar` · SDD sí · rama `feature/F-051-extraccion-fila-a-fila`

Pedida por el humano el 2026-10-19 («reforzar el prompt»). Caso real: obra 0686, partes del 17 y 18/10/2026 (fin de semana, escaneo girado, tabla de 5 filas casi vacia): en el papel fila 2 = 12 y fila 3 = 10 extra (17/10) y fila 2 = 14 extra (18/10); Gemini subio cada cifra una fila (fila 1 = 12, fila 2 = 10; fila 1 = 14) con confianza 95. sv3 caso bien por DNI: el error nace en la lectura. Diseno: sv2 refuerza el prompt parte_trabajo_es (lectura fila a fila por el Nº y el DNI impresos, celda vacia = null, sin mover cifras entre filas, escaneos girados, cifras que invaden la fila vecina) y anade dni al schema_hint; DA1 (recomendada A): campo de autocomprobacion numero_linea_horas por fila en EmpleadoParte, antes de las horas. DA2 (recomendada C): red de seguridad en sv3 (dueno de review_required): lectura dudosa por autocomprobacion incoherente y por tabla dispersa, con interruptor REVISAR_TABLA_DISPERSA. DA3: M1 aceptada con 3 de 3 ejecuciones por pagina. Verificacion manual con el PDF real (no versionado) repetible con otro proveedor/modelo via el .env de sv2; la comparativa de modelos va aparte. Toca sv2 y, con DA2 distinta de A, sv3; sv1, sv4, sv5 y el ORM no. Spec: specs/F-051-extraccion-fila-a-fila/.

### F-059 · La IA no lee bien el PDF con /Rotate: sv2 le manda la página escaneada ya derecha, como la ve un visor

estado **terminada** · prioridad 1 · rigor `estandar` · SDD sí · rama `feature/F-059-pagina-como-imagen-derecha`

**Pendiente**: nada: M4 OK el 2026-10-25 (los 6 partes sin obra reprocesados: 6 convertida, 0 error, obra y fecha leídas en los 6; partes nuevos 0ef28361, b7599bcb, f1e8900d, e8ff17d2, fc892aaf, 7b26d9df)

Petición del humano del 2026-10-23: «es que el giro lo hace fatal. mantiene el formato vertical pero la imagen es ahora horizontal con lo que lo corta., pon la primera arreglar esto», precisada el mismo día: «el parte viene cortado del escaner pero viene bien orientado y la obra se lee perfectamente. el problema no es del giro, es de lectura. de hecho imagen girada esta bien orientado y tal cual esta mal orientado». El fallo es de lectura de la IA, no del escáner ni de sv1: las 6 páginas con la cabecera vacía de los escaneos del 21/10 y del 23/10 son PDF de una página (sv1 las copia tal cual con pypdf) con un JPEG 3507×2480 guardado de lado y /Rotate 270, que las deja derechas en cualquier visor; la obra y la fecha se leen bien. Todo apunta a que OpenAI, con el PDF como input_file, no aplica el /Rotate y lee la imagen cruda de lado. Banco del líder (2026-10-23, fuera del repo, gpt-6.1-sol, 2 pasadas): PDF tal cual, cabecera vacía 12 de 12, también con reasoning.effort = high; JPEG incrustado girado según /Rotate con detail high, obra y fecha bien 12 de 12 (las mismas que gemini-4-argon) y control 4 de 4. Diseño: solo sv2; el pipeline pide a un conversor (puerto en domain, adaptador pypdf + Pillow en infrastructure/document) la página derecha cuando el PDF es una sola imagen JPEG a página completa y la manda como imagen; si no aplica o falla, PDF como hoy (WARNING sin nombres ni DNIs en el fallo). meta.adjunto_ia deja la traza; meta.source_* siguen siendo del original. DA1 (recomendada A): solo OpenAI por defecto, lista PAGINA_COMO_IMAGEN_PROVEEDORES. DA2 (A): imagen incrustada, sin render. DA3 (A): PAGINA_COMO_IMAGEN encendido por defecto, sin cambio de entorno en Azure. DA4 (A): OPENAI_IMAGE_DETAIL=high para toda imagen. Va antes que F-056 y F-058 (la relectura con Gemini sigue como red de seguridad). Spec: specs/F-059-pagina-como-imagen-derecha/.

### F-060 · Racha de incidencia con CIZ móvil: el primer día abre con su CI* y el fin (CIZ) se mueve editando la línea de Sigrid hasta que llega un día con horas

estado **terminada** · prioridad 1 · rigor `critico` · SDD sí · rama `feature/F-060-racha-incidencia-ciz-movil`

**Pendiente**: MOVER_CIZ ENCENDIDO por el humano el 2026-10-25 (sv5 ca-sv5-transfer--0000003 12:08:43Z, luego sv4 ca-sv4-front--0000002 12:09:28Z; sanos, sin Traceback). M4: línea base 0 recursos-mes con más de un CIZ de partes desde 20261025; repetirla cuando se hayan aprobado incidencias. DA3 confirmada en Sigrid; DA6 la sustituye F-062

Petición del humano del 2026-10-23: «el primer dia de unas vacaciones siempre debe marcarse como inicio vacaciones, si luego al dia siguiente aparece vacaciones debe guardarse fin de vacaciones. este fin se va moviendo segun aparzcan dias de vacaciones hasta que aparezca un dia laborable en cuyo caso ya no se mueve. [...] hay que ver si ese recurso tiene vacaciones en algun parte de alguna obra (no solo la suya) y si lo tiene cerrar. si no hay se abre. lo mismo para bajas.» Aprobó la tabla del líder («la propuesta es lo correcto [...] debe buscar siempre en todos sus partes del mes anterior»): incidencia sin racha abierta ⇒ abre con su CI*; con racha abierta ⇒ mueve el CIZ a ese día editando la línea existente (si no hay CIZ, lo crea); horas ⇒ la racha queda cerrada. Regla de Sigrid: «no se debe borrar en sigrid, así que solo editará líneas». Hoy (sv4 `_rol_incidencia`, sv5 R1) cada día de incidencia que sigue a otro sale «fin» y escribe un CIZ nuevo; además no distingue la letra, no tiene ventana y no excluye la papelera. Diseño: sv4 decide el rol con la ventana (día 1 del mes anterior a D−1, todas las obras) y manda los ids de la racha; sv5 localiza el CIZ por synckey y lo mueve con un UPDATE (fecha, synckey y, si cambia de parte, parte, obra, centro, cuenta, año y mes), con guarda de parte abierto, sin DELETE ni INSERT. Interruptor MOVER_CIZ en sv5, apagado por defecto. Sin tabla ni columna nueva. Spec: specs/F-060-racha-incidencia-ciz-movil/.

### F-062 · Incidencia: el primer día escribe el CI* y también el CIZ ese mismo día; si la racha sigue, el CIZ se mueve (como hace Administración)

estado **terminada** · prioridad 1 · rigor `critico` · SDD sí · rama `feature/F-062-ciz-el-mismo-dia-del-inicio`

**Pendiente**: Desplegada 2026-10-26 (sv5 r20261026140625, sv4 r20261026140755); M6: repetir la lectura cuando se aprueben incidencias (n > 0, grupos = 0); vista calendario de Administración

Petición del humano del 2026-10-25: «da de alta f62 la primera, y lanza spec», tras la lectura del líder en Sigrid (solo lectura, ruesma, líneas NO escritas por partes desde 2025-01-01) sobre DA3 y DA6 de F-060. DA6 (F-060, DA6 = A: una incidencia de un solo día deja solo su CI*) NO coincide con la práctica de Administración: de los inicios CI* manuales, 306 llevan CI* y CIZ el MISMO día (CIV 184, CIP 99, CIF 13, CIE 7, CIA 2, CIH 1) frente a 34 sin CIZ (casi todos rachas aún abiertas, sobre todo CIE). DA3 sí coincide (816 rachas con el CIZ en el mismo parte, 224 en el parte del mes siguiente de la misma obra, 65 en el parte de otra obra; solo 12 cortes a fin de mes). Propuesta del líder, aceptada por el humano como feature: al registrar el `inicio` de una racha, sv5 escribe el CI* y además un CIZ (can 0) el mismo día; si llega otro día de la misma racha, ese CIZ se mueve con la mecánica de F-060 (UPDATE optimista, sin DELETE). Así un día suelto queda CI*+CIZ y ninguna racha queda abierta sin CIZ. Depende de F-060 (desplegada, MOVER_CIZ apagado); a decidir en la spec: si va bajo el mismo interruptor MOVER_CIZ, qué pasa con las rachas ya abiertas (solo CI*), el `fin` que hoy escribe un CIZ nuevo cuando no encuentra el de la racha, y el impacto en sv4 (roles, racha_registro_ids, aviso de racha desordenada).

### F-063 · sv2: la consulta de existencia de obra de F-058 tiene que usar el índice (hoy 12–16 s frente al tope de 5 s)

estado **terminada** · prioridad 1 · rigor `estandar` · SDD sí · rama `feature/F-063-consulta-obra-rapida`

**Pendiente**: Desplegada en sv2 r20261026094916 (2026-10-26 08:51:31Z). Pendiente: M2 (motivo/resultado de relectura en partes) y M4 (tiempos de [obra-sigrid] en Log Analytics) cuando haya partes

Petición del humano del 2026-10-25 («1a») tras la M1 de F-058 (líder, local, solo lectura): las 8 consultas `[obra-sigrid]` salieron `resultado=error error=ReadTimeout` (5,6–6,2 s, tope `OBRA_EXISTE_TIMEOUT_S` = 5 s). Medido aparte en sigrid-api: `_SQL_EXISTE_OBRA` (sv2 `infrastructure/sigrid/sigrid_lookup_client.py`, normaliza `con.cod` fila a fila con `CROSS APPLY` + `COLLATE`) tarda 12–16 s; `SELECT 1` 79 ms; `con.cod IN (variantes con ceros)` 110–124 ms; `con.cod LIKE '%692'` 101 ms; `OPTION (FORCE ORDER)` no lo arregla (13 s). Desplegada así, toda consulta de obra sería «no se sabe» (la relectura por obra inexistente nunca saltaría), +~6 s por parte y ~13 s de consulta en el SQL de producción de Sigrid por parte. Objetivo: misma semántica de F-058 (clave normalizada: sin espacios ni guiones, sin ceros a la izquierda si es numérica, sin distinguir mayúsculas ni acentos) con una consulta que use el índice de `con.cod` y quepa holgada en el tope. sv2 NO se despliega hasta cerrar esta feature (F-058 está en dev sin desplegar).

### F-002 · Cola q-transfer para aprobación asíncrona

estado **terminada** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-002-cola-q-transfer`

sv4 publica las aprobaciones en una cola q-transfer y sv5 la consume (KEDA), en lugar del HTTP síncrono actual para lotes; el HTTP se mantiene donde haga falta respuesta inmediata (preflight y confirmación de conflictos en el modal). Tanda 5 del roadmap de infra.

### F-013 · Informe de validación de datos Sesame por trabajador

estado **terminada** · prioridad 2 · rigor `estandar` · SDD no · rama `feature/F-013-informe-validacion-sesame`

Pedida por el humano el 2026-08-16 para terminar de validar F-003: script (p. ej. services/partes-front/validar_datos_sesame.py, junto al patrón de prueba_escritura_sigrid.py de sv5) que, usando el MISMO SesameApiClient y CalendarioProvider de F-003, extrae para cada trabajador activo sus festivos del año en curso, tipo de jornada y flag de reducida, y genera un informe Markdown/CSV legible para que el humano valide los números contra la realidad. Configurable contra sesame-api local (localhost:8006) o el desplegado cuando exista. La validación de los números en sí es MANUAL del humano sobre el informe. Su salida alimenta F-011 (días de jornada reducida) y F-012 (candef 9h/viernes).

### F-021 · Escribir la cuenta analitica en las lineas que sv5 registra en Sigrid

estado **terminada** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-021-cuenta-analitica-sigrid`

Pedida por el humano el 2026-09-30, prioridad maxima. Al registrar en Sigrid (sv5: parte mensual hmo + lineas hmores), rellenar la cuenta analitica de cada linea. Hoy partes no la escribe en ningun sitio (ni rastro de 'analitic' en el codigo). En el diccionario de Sigrid (azure-apps/sigrid_tablas.md) aparece un campo caacod 'Codigo Cue analitica' (texto de 24) en varias tablas y un 'modana' (Modo solo analitica); sin identificar aun si hmores lo tiene. A DECIDIR EN LA SPEC: (a) en que tabla/campo de Sigrid va la cuenta analitica de una linea de horas y si sigrid-api permite escribirla; (b) DE DONDE SALE: de la obra, de la partida, del recurso o de otro maestro de Sigrid; su lectura via sigrid-api (nunca SQL directo); (c) que pasa si no se encuentra (linea sin cuenta, error o aviso en el portal); (d) si afecta al preflight/conflictos del portal (sv4) y a la desaprobacion (F-004). Servicios: sv5 seguro; sv3/sv4 si hay que resolverla antes o mostrarla. RIGOR critico: cambia lo que se escribe en Sigrid en produccion. ACLARADO 2026-09-30 (correo de Juan Romero, Dir. Admon y Control de Costes, 'RV: CAPTURAS'): 'No arrastra cuenta analitica del recurso' => la cuenta analitica SALE DEL RECURSO (su ficha en Sigrid) y hoy no se copia a la linea al registrar. Queda por fijar en la spec el campo exacto del recurso y el de la linea.

### F-022 · Aprobar solo las lineas seleccionadas (visibles) en la vista detallada de obra o persona

estado **terminada** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-022-aprobar-seleccionadas`

Pedida por el humano el 2026-09-30, prioridad maxima. En el portal (sv4), en la vista detallada de una obra o de una persona, si el usuario selecciona varias lineas, al pulsar 'aprobar todo' solo deben aprobarse (y registrarse en Sigrid) las lineas seleccionadas, que el humano describe como 'las visibles'. Hoy el boton aprueba el conjunto completo de la vista (preflight -> encolar/ejecutar en /api/aprobar/*). A CONFIRMAR EN LA SPEC con el humano: si 'seleccionadas' significa las que quedan visibles tras filtrar la vista, las marcadas con casilla, o ambas; que pasa con el resto (quedan pendientes, sin cambio); que el preflight, los conflictos a pisar, el bloqueo por Sesame y el resumen del modal cuenten solo esas lineas; que el servidor valide la seleccion (no fiarse solo del cliente). Servicios: sv4 (portal y API de aprobacion); sv5 no deberia cambiar si recibe ya la lista de lineas: verificarlo en la spec. RIGOR estandar. ACLARADO 2026-09-30 (correo de Juan Romero 'RV: CAPTURAS'): 'opcion de seleccionar varias lineas y aprobarlas, por si quiero dejar alguna pendiente' => seleccion explicita de lineas (casillas) en la vista detallada; el humano lo describio tambien como 'las visibles': la spec debe cubrir ambos (lo filtrado y lo marcado) y confirmarlo.

### F-046 · Reajuste en Sigrid al aprobar: al aprobar el segundo parte del dia, editar con aviso previo el primero ya aprobado o registrado para llevarlo al reparto ponderado de F-045

estado **terminada** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-046-reajuste-en-sigrid-al-aprobar`

**Pendiente**: M6

Pedida por el humano el 2026-10-14 junto con F-045, de la que DEPENDE (se implementa sobre dev con F-045 fusionada y usa su API pura reparto_ponderado.py). Caso real: el 14/10 un recurso tenia la 0678 registrada como 8 normales y -4 extra (4 h trabajadas); llega la 0704 con 8 h y el reparto ideal es 0678 2,5+1,5 y 0704 5,5+2,5, pero F-045 deja la 0678 congelada (0704 0+8). F-046: sv3 (con el interruptor REPARTO_REAJUSTE) aplica el ideal a lo no congelado y guarda la propuesta de lo congelado en la tabla nueva reparto_pendiente (las dos copias del ORM); sv4, al aprobar, avisa con obra, dia, linea y horas antes -> despues y ofrece Aplicar o Mantener lo registrado; sv5 reajusta en Sigrid las lineas hmores ya escritas (UPDATE can/tot con el pre de la linea, INSERT de la extra nueva; por regla del humano nunca DELETE: a 0 se pone can=0, tot=0) bajo el lock, en un lote atomico con concurrencia optimista y solo en partes En registro y lineas sin enlaces; sv3 materializa lo aplicado en partes (excepcion acotada a la congelacion) bajo un candado consultivo de la base partes. Toca sv3, sv4 y sv5. Spec: specs/F-046-reajuste-en-sigrid-al-aprobar/.

### F-053 · Pisar sin borrar: el pisado de conflictos de sv5 pone a 0 en Sigrid en vez de hacer DELETE

estado **terminada** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-053-pisar-sin-borrar`

**Pendiente**: M4

Regla del humano: «no se debe borrar en sigrid, así que solo editará líneas, por lo que si una hora extra se queda a cero no se borrará sino se pondrá a cero.» Hallazgo del 2026-10-20 (specs de F-052 y F-034): al registrar con un conflicto confirmado sv5 hace DELETE FROM hmores WHERE ide = ? (stmt_borrar_linea) y el portal dice que borra. Aprobado abrirla aparte el 2026-10-20 («Ok a las 2»), justo detrás de F-034, que toca la misma sentencia: se implementa sobre dev con F-034 fusionada (su guarda de parte abierto, su R4 y su relectura). sv5: el pisado pasa a stmt_anular_linea (UPDATE can = 0, tot = 0 con WHERE optimista, sin enlaces y con la guarda de F-034; synckey, tex y demás intactos), sin ningún DELETE en el cliente ni en el pipeline; una línea a 0 ya no choca (salvo incidencias); incidencia contra la misma incidencia ⇒ omitido incidencia_en_sigrid; choque con línea enlazada (albarán, factura, dedicación, nómina) ⇒ omitido linea_enlazada; pisada que cambió ⇒ pisada_no_anulada; el resultado cuenta anuladas en vez de borradas. sv4: textos del modal de conflictos y del resultado («se pone a 0, no se borra») y MOTIVO_LINEA_REGISTRADA sin aconsejar borrar. Sin esquema ni colas. Aviso a porcentajes (su dedicacion-transfer tiene el mismo DELETE) en azure-apps/partes.md, sin tocar su repositorio. Decisiones DA1-DA12 y M1 de solo lectura en specs/F-053-pisar-sin-borrar/design.md §9 y §12.

### F-058 · sv2: si la cabecera sale vacía o su obra no existe en Sigrid, relee la página con Gemini y se queda con su cabecera; el prompt avisa de la cabecera

estado **terminada** · prioridad 2 · rigor `estandar` · SDD sí · rama `feature/F-058-relectura-cabecera-gemini`

**Pendiente**: Desplegada en sv2 r20261026094916 (2026-10-26 08:51:31Z). Pendiente: M2 (motivo/resultado de relectura en partes) y M4 (tiempos de [obra-sigrid] en Log Analytics) cuando haya partes

Hallazgo del líder del 2026-10-23 (solo lectura en producción y batería local sin escrituras): 6 páginas de dos escaneos (21/10 y 23/10) se guardaron sin obra ni fecha porque gpt-6.1-sol (IA_PROVIDER=openai en sv2) devolvió la cabecera entera a null aunque leyó las filas. El escaneo sale desplazado. Reproducido: 12 de 12 lecturas con gpt-6.1-sol dan cabecera vacía; gemini-4-argon da obra y fecha correctas 6 de 6 con las mismas filas. Decisiones del humano del 2026-10-23: «si, lanza f54 y la spec de relectura con gemini»; DA1 enmendada, «da1, vacia o no casa con ninguna obra»; y «para el tema de la cabecera podemos mejorar el prompt diciendole que hay una cabecera y que debera obtener la obra el dia mes, etc... añadelo a f58, lo demas ok» (DA2–DA8 aprobadas con la recomendación; comprobación de existencia en sv2). Spec enmendada (specs/F-058-relectura-cabecera-gemini/): solo sv2. Con al menos una fila de empleados, relee el mismo adjunto una vez con RELECTURA_CABECERA_PROVIDER (gemini, modelo GEMINI_MODEL) y el mismo prompt, esquema y catálogo si (a) obra_numero y fecha vienen vacíos o (b) la obra leída no existe en Sigrid (DA10 = B, «da10, vamos a poner una consulta en el momento al vuelo, y vemos tiempos. si la obra no existe se manda a relectura a gemini»: una consulta sql/read parametrizada a sigrid-api por página, sin caché, clave sin ceros a la izquierda, cualquier empresa y también de baja; truncated = fallo; cada consulta deja en el log INFO [obra-sigrid] con document_id y milisegundos, y en meta.relectura_cabecera.consulta_obra_ms al releer; si sigrid-api falla o pasa de OBRA_EXISTE_TIMEOUT_S = 5 s, no se relee por obra y la extracción sigue, propuesta pendiente DA12). No es la conciliación de sv3 ni amplía la lista de duplicados. Toma la cabecera entera de la relectura si es útil (con obra o fecha; con obra inexistente, si su obra existe); firma y empleados de la primaria; si falla o no es útil, la primaria (F-054 la manda a revisión). Traza en meta/debug.relectura_cabecera (motivo cabecera_vacia|obra_inexistente, resultado aplicada|vacia|no_casa|error). Interruptor RELECTURA_CABECERA encendido; sin cambios de entorno en Azure (Gemini y SIGRID_API_* ya están en ca-sv2-extraccion; M0 en solo lectura). Además, el punto 1 del prompt parte_trabajo_es dice que toda página tiene una cabecera y que de ella salen la obra, el día, el mes y el año, el membrete y el resto; vale para ambos proveedores y se mide con el banco del líder (MB: sincab con gpt-6.1-sol antes 0 de 12; sin regresión en control, Gemini ni batería de F-051). De 157 documentos con obra leída, los 157 casaron: el motivo obra inexistente es preventivo. Pendientes de confirmar DA9 (puerta del banco), DA11 (cabecera entera también con obra inexistente) y DA12 (fallo o lentitud de la consulta: no releer por obra, tope 5 s), recomendadas A. Tiempos de la consulta en Log Analytics tras desplegar (M4). Se actualizan ARCHITECTURE.md, azure-apps/partes.md (sv2 consume Gemini y sigrid-api) y el comentario de create_capps_partes.ps1.

### F-061 · Borrar todas las líneas de un parte (y vaciar la papelera) deja el parte activo y vacío, que bloquea su reproceso

estado **terminada** · prioridad 2 · rigor `estandar` · SDD sí · rama `feature/F-061-parte-vacio-tras-borrar-lineas`

**Pendiente**: desplegar sv4 (humano), M1 en el portal y M2: el humano lee el informe de limpiar_partes_vacios.py y lo ejecuta con --ejecutar --esperados N

Petición del humano del 2026-10-25: «añade una feature para ver por que no los borro bien». Observado por el líder ese día al reprocesar los 6 partes sin obra de F-059 (doc002836 y doc021390): el humano borró en el portal sus 40 líneas una a una (POST /api/registro/{id}/delete) y vació la papelera (POST /api/papelera/vaciar); las líneas desaparecieron, pero los 6 parte_documents siguieron is_active = true, sin deleted_at_utc y con 0 líneas. Al reingerir los correos, sv3 los descartó por sha256 («ya existe … Se omite reinserción», get_by_sha256 filtra is_active) y la relectura (ya con obra y fecha gracias a F-059) se perdió. El líder los pasó a la papelera a nivel de documento por SQL (deleted_by «lider-claude …») para poder reprocesarlos. En producción había ese día 36 parte_documents activos sin ninguna línea. A decidir en la spec: si al quedarse un documento sin líneas vivas (borrado de líneas, de trabajador o de obra, y vaciado de papelera) debe ir solo a la papelera o desactivarse; qué hacer con los 36 existentes (informe y limpieza autorizada); si el portal debe enseñar o avisar de los partes vacíos; y que la deduplicación de sv3 no quede bloqueada por un documento vacío. Pendiente de spec.

### F-003 · Integración sesame-api: festivos y jornada reales

estado **terminada** · prioridad 3 · rigor `critico` · SDD sí · rama `feature/F-003-sesame-festivos-jornada`

Sustituir la librería holidays y el candef como jornada teórica por los datos reales de Sesame HR vía el servicio general sesame-api: festivos por calendario asignado a cada trabajador y jornada del contrato. Afecta a los avisos de jornada incompleta (sv4) y al cómputo de extras (sv3). Añadir aviso al registrar horas en festivo/domingo.

### F-024 · Lineas que quedan en 'encolado' en el portal aunque el parte ya esta registrado en Sigrid

estado **terminada** · prioridad 3 · rigor `critico` · SDD sí · rama `feature/F-024-lineas-encoladas`

Reportado el 2026-09-30 por Juan Romero (correo 'RV: CAPTURAS', captura de la vista de obra). En un mismo parte y dia, la linea Extra (HEOF) muestra 'PT26/00314' en la columna Sigrid y la linea Ordinaria (HLOF) del mismo trabajador se queda en 'encolado', 'si ya lo habiamos llevado a Sigrid, igual que el de abajo'. A INVESTIGAR (explorer de solo lectura antes de la spec): si la linea se escribio en Sigrid y el portal no recibio/actualizo el resultado (q-transfer/resultado_sigrid de F-002), si el mensaje se perdio o acabo en -poison, o si sv5 la omitio sin devolver estado. Comprobar en Sigrid (solo lectura) y en la base partes. Servicios probables: sv4 (estado mostrado) y sv5 (resultado por linea). RIGOR critico si resulta que hay lineas sin registrar que el usuario cree registradas. HALLAZGO DEL LIDER 2026-10-01 (lectura por sigrid-api, base ruesma): NINGUNA linea hmores de Sigrid tiene synckey no vacio (ni 'partes:%' ni otro), aunque sv5 escribe hmores.synckey = 'partes:<id>' y el portal mostro lineas registradas en PT26/00314 (cabecera existe, empresa 1, 2026-09, 56 lineas, todas con synckey vacio). Hipotesis a verificar: Sigrid (o un proceso suyo) vacia synckey despues de escribir, o las lineas se borraron y se reteclearon. Si synckey no persiste, la idempotencia, la deteccion de conflictos y la desaprobacion (F-004) que se apoyan en el no funcionan: investigar ANTES de F-021.

### F-012 · Estudio: candef de 9h, viernes y jornada semanal particularizable

estado **terminada** · prioridad 4 · rigor `documental` · SDD sí · rama `feature/F-012-estudio-jornada-semanal`

Pedida por el humano el 2026-08-16, para después de F-011: estudiar los trabajadores con candef=9h y cómo deben comportarse sus viernes — deberían ser el resto de horas hasta la jornada SEMANAL (con 9+9+9+9 el viernes serían 4h para llegar a 40). La jornada semanal debe ser PARTICULARIZABLE por trabajador (por defecto 40h, pero hay trabajadores que hacen más de 40h semanales). Entregable: análisis con datos reales (cuántos trabajadores, qué patrones hay en reshor/Sesame) y propuesta de diseño para que el cómputo de extras y los avisos usen jornada semanal además de diaria; la implementación puede ser feature aparte si el estudio lo justifica. APROBADA por el humano el 2026-08-18 con decisiones firmes: jornada semanal DERIVADA del candef ({8:40, 9:42}, env espejo sv3+sv4), resto en el ULTIMO DIA LABORABLE de la semana (festivo cuenta como jornada), excepciones en tabla empleado_jornada (UI en F-016), candef desconocido → jornada plana 5×candef + WARNING, sin calendario → viernes. Rigor documental (estudio sin código). Sale de aquí F-014 (candef en Sigrid), F-015 (implementación) y F-016 (UI).

### F-025 · Incompatibilidad incidencia/horas extra el mismo dia (p.ej. baja por maternidad con hora extra)

estado **terminada** · prioridad 4 · rigor `estandar` · SDD sí · rama `feature/F-025-incidencia-vs-extra`

Reportado el 2026-09-30 por Juan Romero ('RV: CAPTURAS'): hizo un parte con una incidencia y al lado una hora extra el mismo dia; 'si esta de baja maternidad, no puede tener horas extra'. Hay que limitarlo. A DECIDIR EN LA SPEC: que incidencias son incompatibles con horas trabajadas/extra (baja, maternidad, vacaciones...?) y de donde sale esa lista (tipos de incidencia de Sigrid o lista propia); si se bloquea la aprobacion, se marca para revision o se avisa en el preflight; en que servicio vive la regla (sv3 al conciliar y/o sv4 al aprobar). Servicios probables: sv3/sv4.

### F-049 · Portal: el editor de celda de la matriz de obra muestra siempre ordinarias y extra y permite añadir la línea que falta

estado **terminada** · prioridad 4 · rigor `critico` · SDD sí · rama `feature/F-049-editor-calendario-normal-y-extra`

**Pendiente**: M2–M8 en el portal

Pedida por el humano el 2026-10-15 («si solo hay extras u ordinarias edita pero no me sale 0+2 para poder añadir línea»). Hoy el popup de doble clic de la matriz Horas por día (vista de obra) solo ofrece crear la extra si hay una ordinaria; con solo extras no deja añadir la ordinaria, y editar un miembro de la pareja base + extra_auto se pierde en la siguiente pasada de sv3. F-049 (sv4 partes-front y, por la DA13-C, sv3 solo en marcar_terminado; sin esquema, sv5 ni Sigrid): el popup ofrece siempre la ordinaria y la extra que falten («(nueva)»), guarda la celda entera en una ruta atómica nueva (POST /api/matriz/celda) que identifica la celda por (obra_key, clave de trabajador de F-050, fecha) y comprueba que nada cambió desde que se abrió, clona el contexto de la plantilla (incluida la partida; fila del papel y leído con fila_para_alta_manual de F-050), materializa las parejas tocadas (horas_orig NULL, extra_auto False), avisa de las otras obras del mismo día (al abrir y, tras guardar, con enlaces) y pide UN recálculo seguido (F-043) con un pedido compartido escrito en los partes tocados y en los de otras obras de ese día, que sv3 da por terminado en todos (marcar_terminado por pedido, no por documento), respeta la congelación y el reparto de F-046 (aviso si pendiente, 409 si aplicando) y se puede deshacer. Revisada el 2026-10-20 sobre dev ff2ed8e + F-050: va DESPUÉS de F-050 y ANTES de F-047 (de la que no depende). Aprobada por el humano el 2026-10-20: DA1–DA12 opción A y DA13 opción C. Despliegue sv3 antes que sv4. Spec: specs/F-049-editor-calendario-normal-y-extra/.

### F-054 · Un parte sin obra o sin fecha leídas va siempre a revisión

estado **terminada** · prioridad 4 · rigor `estandar` · SDD sí · rama `feature/F-054-sin-obra-o-fecha-a-revision`

**Pendiente**: releer los 6 partes sin obra cuando F-059 esté desplegada

Petición del humano del 2026-10-21 («2 si»): «abro una feature pequeña para que un parte sin obra o sin fecha vaya siempre a revisión». Hallazgo del líder el 2026-10-21 (solo lectura en producción): las dos páginas de un escaneo de ese día llegaron con la cabecera vacía (fecha, obra_numero y empresa_membrete null), firmadas y con 4 y 6 trabajadores casados, y se guardaron con review_required = false, obra_match_method = 'none' y obra_ide, obra_codigo y fecha_int NULL: _compute_review_required de sv3 no miraba la obra sin casar por 'none' ni la fecha. sv3: motivos_cabecera (sin_obra si obra.ide es None, sea cual sea el método; sin_fecha si fecha_int es None o <= 0) sube review_required, sustituye a OBRA_A_REVISAR (que desaparece) y deja un WARNING con document_id y motivos, sin nombres ni DNIs. Solo ingestas nuevas; sin esquema, sin colas, sin cambios en sv4 ni sv5. Lo ya guardado: M1 de solo lectura en la base partes y, si se aprueba DA3 = B, un UPDATE único manual que solo sube la bandera en los activos no aprobados. Hallazgo aparte (DA5, feature propuesta): una línea sin fecha viaja a sv5 con fecha_int = 0 y sv5 no la rechaza. Decisiones DA1-DA7 APROBADAS el 2026-10-21 con la recomendación (A salvo DA3 = B; «apruebo F-054 y la DA5»); la guarda de DA5 es F-055. M1 hecha el 2026-10-21 (M2 afectará a 3 documentos; ninguna línea sin fecha llegó a Sigrid). Va justo detrás de F-049 (en curso): prioridad 4, desempata el id. Detalle en specs/F-054-sin-obra-o-fecha-a-revision/design.md §8 y §9.

### F-004 · Congelar registros aprobados

estado **terminada** · prioridad 5 · rigor `estandar` · SDD sí · rama `feature/F-004-congelar-aprobados`

Un registro aprobado (y con más razón, ya registrado en Sigrid) no debe poder editarse en el portal sin desaprobarlo antes de forma explícita.

### F-010 · Saneamiento: resincronizar orm_models.py entre sv3 y sv4

estado **terminada** · prioridad 6 · rigor `estandar` · SDD sí · rama `feature/F-010-resincronizar-orm-models`

El spec-author de F-003 detectó (2026-08-15) que la duplicación tolerada de infrastructure/database/orm_models.py YA está desincronizada: sv3 tiene horas_orig/extra_auto que faltan en sv4, y sv4 tiene las columnas sigrid_* que faltan en sv3. Viola la trampa 3 de C3 (un cambio de schema modifica las DOS copias). Resincronizar ambas copias con el schema real de la BBDD partes, añadir un test que compare las dos declaraciones (como el guardián R11 de F-002), y valorar si el ALTER TABLE IF NOT EXISTS de sv4 debe cubrir también lo de sv3.

### F-015 · Jornada del día por jornada semanal derivada del candef y último laborable (extras sv3 + avisos sv4) + tabla de excepciones empleado_jornada

estado **terminada** · prioridad 7 · rigor `estandar` · SDD sí · rama `feature/F-015-jornada-semanal-candef`

Implementación de lo que propone el estudio F-012 (specs/F-012-estudio-jornada-semanal, requisitos R10–R25 del bloque B, tasks §'Propuesta de tasks para F-015'). Resolutor único gemelo sv3/sv4: L–V = candef efectivo salvo el ÚLTIMO DÍA LABORABLE de la semana del trabajador (calendario F-003; festivo cuenta como jornada), que vale jornada semanal − 4×candef (nunca negativo); jornada semanal derivada del candef por el mapa configurable JORNADA_SEMANAL_POR_CANDEF (default 8:40,9:42; env espejo en sv3 y sv4; candef válido fuera del mapa → jornada plana 5×candef + WARNING; sin calendario cableado → viernes). Excepciones por trabajador en tabla nueva empleado_jornada de la BBDD partes (DNI normalizado, jornada semanal y/o patrón 7 valores, vigencia desde/hasta, origen, auditoría), declarada en las DOS copias de orm_models.py; si falla su lectura, derivada + WARNING. sv3 usa la jornada del día en el split de extras (excluyendo del re-split lo registrado/encolado/approved, coherente con F-004); sv4 en avisos de jornada incompleta, KPI (enseña patrón y S aplicada) y +Nuevo (jornada_dia con fecha). Regresión cero con candef 8. PRERREQUISITOS: F-014 cerrada (candef 9 en Sigrid) y F-010 antes (orm_models resincronizado, decisión D6 aprobada). Servicios: sv3 y sv4 (duplicación tolerada de orm_models y resolutor gemelo, patrón F-003).

### F-038 · Subir a 500.000 el límite de filas de las lecturas de Sigrid en sv2–sv5 (antes 1.000 en sv5 y 10.000 en el resto)

estado **terminada** · prioridad 7 · rigor `estandar` · SDD sí · rama `feature/F-038-limite-filas-sigrid`

**Pendiente**: M1 (lecturas reales de obras grandes; no bloquea). Desplegada sv2–sv5 el 2026-10-24 (r20261024215445); M2 OK

Pedida por el humano el 2026-10-07, viene de porcentajes: al leer obras con muchas partidas la lectura se trunca por el limite de filas de sigrid-api. Se pide subir el limite a 200.000. La instancia desplegada de sigrid-api admite hasta 500.000 por peticion (MAX_ALLOWED_ROWS, azure-apps); el corte real es el balanceador a 230 s. Limites actuales en partes (2026-10-07): sv2 sigrid_lookup_client max_rows 10000; sv3 SIGRID_API_MAX_ROWS 10000 (settings) en sigrid_api_client; sv4 sigrid_lookup_client 10000 (y consulta_reshor_recursos.py 10000); sv5 sigrid_write_client _read con max_rows 1000 fijo (partidas_de_lineas, cuentas_de_centro, etc.); las lecturas paginadas usan PAGINA_FILAS + 1 y tratan truncated como error. A REVISAR EN LA SPEC: que lecturas pueden truncarse hoy (partidas por obra en sv4 y sv5, catalogos de sv3) y si alguna trunca EN SILENCIO (sin comprobar truncated); subir a 200000 donde no haya paginacion, configurable por variable de entorno, y comprobar truncated siempre como error; timeouts frente al limite de 230 s; tests.

### F-016 · Pantalla de administración de empleado_jornada en el portal (sv4)

estado **terminada** · prioridad 8 · rigor `estandar` · SDD sí · rama `feature/F-016-admin-empleado-jornada`

Propuesta por el estudio F-012 (D5, R24): vista de administración en sv4 para crear/editar/cerrar filas de empleado_jornada (DNI, jornada semanal, patrón opcional L–D, desde/hasta, nota), registrando quién y cuándo, validando horas 0–24 por día, desde<hasta y sin solapes por DNI. Hasta entonces las excepciones se cargan por SQL manual del humano. Después de F-015; valorar restringirla por roles cuando exista F-008.

### F-017 · Identidad real de Easy Auth en el portal (sv4)

estado **terminada** · prioridad 8 · rigor `estandar` · SDD sí · rama `feature/F-017-identidad-easy-auth`

Detectado por el spec-author de F-016 el 2026-08-19 y verificado por el lider: sv4 NO lee hoy la identidad del usuario. No hay ni una referencia a X-MS-CLIENT-PRINCIPAL en el repositorio y las once escrituras de auditoria del portal (approved_by, deleted_by y las cuatro entradas de undo_log, todas en services/partes-front/interface_adapters/web/app.py: lineas 1500, 1594, 1629, 1684, 1687, 1841, 1867, 1881, 1900, 1910 y 2121) se firman con la variable DEFAULT_REVIEWER, igual para todos. Decision del humano del 2026-08-19: se introduce la lectura de Easy Auth y se extiende a TODO el portal, no solo a las columnas de F-016. Alcance: decodificar la cabecera de Easy Auth (X-MS-CLIENT-PRINCIPAL-NAME o el token base64, decidiendo cual manda), un unico helper de identidad que consuman los once puntos, fallback para desarrollo local, y decidir que se hace con las filas historicas ya firmadas con el valor generico (propuesta del spec-author: NO se reescriben, se documenta el corte; inventar autores seria falsificar auditoria). Los ROLES siguen siendo F-008: esta feature responde a 'quien hizo esto', no a 'quien puede hacerlo'. Material de partida en specs/F-016-admin-empleado-jornada/design.md seccion 14. AVISO del reviewer de F-016 (2026-08-19): el test test_f016_r13_auditoria (services/partes-front/tests/test_f016_endpoints_admin_jornadas.py:519) parchea DEFAULT_REVIEWER en vez del helper _actor, asi que se pondra ROJO el dia que _actor devuelva el principal real de Easy Auth. F-017 debe incluirlo en su lista de ficheros a tocar y pasarlo a inyectar o parchear el helper. Deberia ir ANTES de F-016 para que las filas de empleado_jornada nazcan firmadas con el usuario real, pero las dos ordenes funcionan sin retrabajo porque F-016 pide la identidad a un solo helper. HALLAZGO del 2026-08-20 (verificacion del despliegue): DEFAULT_REVIEWER NO esta configurada en el Container App ca-sv4-front (comprobado en Azure; .env.example la declara vacia), asi que _actor devuelve None y los once puntos de auditoria llevan sellando NULL desde el primer despliegue. El enunciado de esta feature decia que las filas van firmadas con un valor generico: NO es asi, van SIN autor. Cambia la decision sobre las filas historicas (no hay nada que reescribir, solo un corte que documentar) y sube el valor de la feature: hoy la auditoria del portal esta en blanco. DECISION del humano del 2026-08-20: no se pone un DEFAULT_REVIEWER provisional mientras tanto; la auditoria sigue con NULL hasta que esta feature lea la identidad real de Easy Auth.

### F-005 · Retirar graphkey_nobom.json del arbol y dejar constancia de GRAPH_KEY en Key Vault

estado **terminada** · prioridad 9 · rigor `documental` · SDD no · rama `feature/F-005-graphkey-keyvault`

Los dos objetivos originales estan cumplidos de hecho. Comprobado el 2026-08-20 y reconfirmado el 2026-08-25 contra Azure (solo lectura): los tres servicios que usan Graph -ca-sv1-poller, ca-sv3-persistencia y ca-sv4-front- llevan GRAPH_KEY como secretRef 'graph-key' y el secreto de la Container App es una referencia a Key Vault, no una copia; el secreto GRAPH-KEY existe y esta habilitado en el Key Vault de partes ($KV). Ningun script de infra/ lee graphkey_nobom.json: add_secrets_partes.ps1 pide el JSON por consola con Read-Host -AsSecureString y lo sube al Key Vault sin tocar disco. Lo que queda, y es esta feature: borrar la copia local de infra/graphkey_nobom.json (no versionada, nunca entro en git) y corregir las dos menciones que aun la presentan como parte del despliegue. Decision del humano del 2026-08-25: SOLO LIMPIEZA.

### F-019 · Horas aprobadas de los trabajadores con codigo de hora mes viajan a dedicacion (porcentajes) en lugar de a Sigrid

estado **terminada** · prioridad 9 · rigor `critico` · SDD sí · rama `feature/F-019-mensuales-a-dedicacion`

**Pendiente**: interruptor MENSUALES_A_DEDICACION apagado: falta la feature espejo en porcentajes y la M3

Pedida por el humano el 2026-09-29. Los trabajadores cuyo recurso tiene un codigo de hora mes (M* en su reshor de Sigrid: encargados, jefes de obra, tecnicos...) hoy NO dejan nada de sus horas en ningun sitio: sv5 las omite (reglas_registro.py R2 si no tienen HE%, R3 si no tienen HL%). Solo sus INCIDENCIAS se escriben en Sigrid (R1). LO QUE SE PIDE: al APROBAR en el portal, las lineas de estos trabajadores viajan al sistema de dedicacion (repo porcentajes) EN LUGAR DE a Sigrid. DECISIONES DEL HUMANO (2026-09-29): (1) Criterio de 'mensual' = tener un codigo M* en reshor, el mismo que usa dedicacion (no el 'sin HE%' que usa partes hoy). (2) Se envian TODAS las horas aprobadas que haya en partes para ese trabajador. (3) El porcentaje por obra se calcula en funcion de los DIAS LABORABLES del mes; las horas indicadas en festivos se desprecian. Ese calculo es de dedicacion (porcentajes tiene o tendra la funcion): partes envia el dato del dia (trabajador, fecha, obra/partida, horas, tipo) y NO calcula porcentajes, por el limite de servicio. (4) Las VACACIONES cuentan como dias trabajados para ese calculo. (5) Las INCIDENCIAS se llevan a dedicacion COMO INCIDENCIA, con su porcentaje; dejan de escribirse en Sigrid para estos trabajadores (cambia R1). (6) Se presentan en dedicacion como PROPUESTA de reparto, que alguien revisa en el cuadrante; no lo sobrescriben solas. (7) En el portal de partes esas lineas dejan de salir como 'omitidas' y pasan a 'enviadas a dedicacion'. A DECIDIR EN LA SPEC: (a) CANAL. Recomendacion del lider: una bandeja de salida en la base partes (tabla propia escrita por sv5 al aprobar) que dedicacion-api lee con un rol de SOLO LECTURA; cada proyecto escribe solo en su base y no se abre ninguna ruta de red. Descartado HTTP hacia dedicacion-api: no tiene autenticacion propia, su ingress interno es su unico control de acceso (azure-apps/dedicacion.md 5) y vive en otro Container Apps Environment. Alternativa a valorar y descartar con argumentos: bandeja de entrada en la base dedicacion escrita por partes. Nada a nivel de servidor en psql-albaranes-rs9k2: el rol se crea dentro de la base partes. (b) Mensuales que ademas tienen HE% (capataz MCAP + HECAP): si sus extras siguen yendo a Sigrid o tambien viajan a dedicacion; hoy van a Sigrid. (c) DESAPROBAR (F-004): como se retira de dedicacion lo ya enviado, e idempotencia al reaprobar. (d) Que pasa si el periodo ya esta CERRADO en dedicacion cuando llega la aprobacion. (e) Donde vive la decision de enrutar: previsiblemente en sv5 (reglas_registro, nueva accion ademas de escribir/omitir), que ya carga los codigos del recurso. FUERA DE ESTE REPOSITORIO: la lectura y el calculo del porcentaje en dedicacion son una feature del repo porcentajes, a crear alli con decision del humano; esta feature publica el dato y actualiza azure-apps/partes.md en el mismo trabajo (pasamos a exponer algo). RIGOR critico: cambia que se escribe en Sigrid en produccion (sv5 deja de registrar las incidencias de los mensuales).

### F-020 · Ingesta de sv1: correos adjuntos (message/rfc822) encadenados hasta encontrar el PDF

estado **terminada** · prioridad 10 · rigor `estandar` · SDD sí · rama `feature/F-020-correo-adjunto-escaner`

Pedida por el humano el 2026-09-30. El escaner (visto desde el remitente del escaner, asunto 'Attached Image') envia los partes como un correo adjunto (message/rfc822, itemAttachment de Graph) que contiene el PDF. Hoy sv1 descarta los itemAttachment (_NON_FILE_ODATA_TYPES en polling_pipeline.py) y el correo acaba en Errores por 'sin adjuntos elegibles'. LO QUE SE PIDE: sv1 abre los correos adjuntos de CUALQUIER remitente (decision del humano: NO se filtra por remitente) y los recorre de forma recursiva, correo dentro de correo, hasta encontrar el/los PDF, que siguen el camino normal (troceo por paginas -> Blob -> q-extraccion). DECISIONES CONFIRMADAS (2026-09-30): (1) Solo se extraen PDF del interior; imagenes no. (2) Tope de seguridad de 5 niveles de anidamiento; si se excede o no aparece ningun PDF, el correo va a Errores con log explicativo. (3) Un correo con PDF directos y correos adjuntos procesa todo en la misma pasada. (4) Citas de calendario, contactos y referenceAttachment se siguen descartando. (5) El contexto del documento lleva el nombre del PDF interior y una clave nueva 'embedded_in' con la cadena de correos atravesados; verificar que sv2/sv3 no se rompen. (6) Se crean los primeros tests de sv1 (services/partes-email/tests/) con .eml sinteticos, sin red, y se registran en harness/servicios.json. PRIMER PASO OBLIGATORIO: sonda de SOLO LECTURA que confirme que GET /attachments/{id}/$value sobre un itemAttachment devuelve el MIME del correo adjunto con el PDF dentro; si no, parar y reproponer. SOLO TOCA sv1. Desplegar lo lanza el humano. Reprocesar los correos ya caidos en Errores es manual y queda fuera.
