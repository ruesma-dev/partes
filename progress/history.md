<!-- progress/history.md -->
# Histórico del arnés

Registro append-only. El líder mueve aquí el resumen de cada feature terminada.

---

## F-001 · Test de estructura del monorepo (calentamiento) — done 2026-08-13

- Rama `feature/F-001-test-estructura` · rigor estandar · sdd=false ·
  APPROVED del reviewer (`progress/review_F-001.md`).
- Entregado: `tests/conftest.py` y `tests/test_estructura_monorepo.py`
  (6 tests `test_f001_r*` que validan `harness/servicios.json` contra el
  árbol real reutilizando `harness/servicios.py`; R2 con declaración falsa
  en `tmp_path` + 2 tests de control).
- Verificado: init.sh en verde (exit 0, reproducido por el reviewer),
  6/6 tests, ruff limpio en lo nuevo, fase RED con 3 roturas en copia
  aislada (reproducidas de forma independiente por el reviewer), cobertura
  N/A con motivo impreso, mutación 0/0 con prueba de control (9 mutantes al
  ignorar la exclusión ⇒ generador vivo, cero legítimo).
- Observaciones no bloqueantes del reviewer: (1) el test admite
  `pyproject.toml` como punto de entrada alternativo, algo más laxo que
  ARCHITECTURE.md — si un servicio se empaqueta, actualizar doc y test a la
  vez; (2) los 6 AVISOS de servicios sin tests siguen ahí y merecen feature
  propia; (3) propuesta de automejora: añadir a C4 bis de CHECKPOINTS.md la
  prueba de control del cero de mutación (si se acepta, portar a arnes-base
  en el mismo trabajo). Pendiente de decisión del humano.
- Circuito completo del arnés (líder → implementer → reviewer → cierre)
  validado por primera vez en este repositorio.

## F-002 · Cola q-transfer para aprobación asíncrona — done 2026-08-13

- Rama `feature/F-002-cola-q-transfer` (HEAD APPROVED `63b1afe`) · rigor
  critico · sdd=true · spec R1–R26 / T1–T15 aprobada por el humano con dos
  ampliaciones suyas (preparación en paralelo con escritura serializada;
  gestión de poison desde el portal) · 1 ciclo de review.
- Entregado: doble canal sv4↔sv5 (colas `q-transfer`/`q-transfer-result`
  con hand-off por blob en el contenedor `transfer`; HTTP síncrono solo
  para preflight y pisado), split preparar/registrar del pipeline de sv5
  con `TRANSFER_WORKERS=3` y lock inyectado (escritura 1 a 1), endpoint
  `POST /api/aprobar/encolar` con fallback síncrono, consumidor de
  resultados en sv4, estados `encolado`/`conflicto`/`error` sin cambio de
  schema, aviso + reencolado manual de poison en el portal
  (send-antes-de-delete, allowlist), `infra/add_qtransfer_partes.ps1`
  (auth-mode login, sin clave), suite nueva de sv4 (112 tests) y ampliada
  de sv5 (84 + guardián R11), docs y `azure-apps/partes.md` (commit local
  `1440598` + fix posterior en azure-apps).
- Verificado (reviewer, de forma independiente): init.sh verde ×2,
  202 tests, cobertura líneas cambiadas 97,4 % (umbral 80), mutación
  132/0 con muestreo de 19 mutantes, fase RED reproducida (lock
  decorativo ⇒ 3 cabeceras duplicadas PT26/00001 — el daño que la feature
  evita), arranque simulado de la imagen sin `.venv` (el bloqueante de la
  1.ª pasada, corregido declarando azure-* en los manifiestos de sv4/sv5).
- CHANGES_REQUESTED de la 1.ª pasada: paquetes azure-* ausentes de los
  manifiestos (crash-loop en el próximo deploy). Corregido + 2 mejoras del
  reviewer aplicadas. Lección: la suite corre contra el .venv de la raíz,
  el contenedor instala manifests/svN/requirements.txt.
- MANUAL pendiente del humano (comandos exactos en el resumen de cierre y
  en `progress/impl_F-002.md`): ejecutar `add_qtransfer_partes.ps1`,
  verificar colas y escala 1/1 de sv5, badges y poison en navegador,
  redeploy (orden sv5 antes que sv4), merge a dev y push (rama y commits
  de azure-apps).
- Automejoras del arnés propuestas por el reviewer, PENDIENTES de decisión
  del humano: (1) C4 bis — exigir evidencia alternativa cuando un fichero
  del alcance con >N líneas genere 0 mutantes; (2) C3/C4 o init.sh —
  cruzar imports nuevos de terceros contra el requirements del manifiesto
  del servicio. Ambas portables a arnes-base si se aprueban.

## F-003 · Integración sesame-api: festivos y jornada reales — done 2026-08-16

- Rama `feature/F-003-sesame-festivos-jornada` · rigor critico · sdd=true ·
  spec aprobada por el humano con enmienda suya (resiliencia en DOS
  niveles) · 1 ciclo de review · APPROVED en segunda pasada.
- Entregado (APAGADO por defecto, `sesame_enabled=false` = comportamiento
  actual): clientes Sesame gemelos en sv3/sv4 (duplicación tolerada
  AMPLIADA en CLAUDE.md, redacción firmada por el humano el 2026-08-16),
  proveedor con caché DNI×año y stale-while-error, resolutor único de
  jornada (regla candef desduplicada de 4 sitios), festivos por calendario
  del trabajador en avisos/matriz/+Nuevo, aviso festivo/domingo en
  preflight, endpoint GET /api/calendario, y el régimen de resiliencia:
  vistas degradadas con aviso visible; registro BLOQUEADO con Sesame
  activado-pero-caído, override forzar_sin_sesame solo por /ejecutar con
  marca [SIN-SESAME] en sigrid_motivo, y review_required en sv3. CERO
  cambios de schema. Se inaugura la suite de sv3.
- Verificado (reviewer, independiente): init.sh verde, **373 tests**
  (6 raíz + 95 sv3 NUEVOS + 272 sv4, +144), cobertura líneas cambiadas
  **94,5 %** (umbral 80), mutación **211 mutantes / 25 supervivientes,
  todos analizados como equivalentes** (de 57 iniciales: la campaña forzó
  refuerzo real de la suite), fase RED de la enmienda reproducida.
- Hallazgos externos de la feature: sesame-api NO desplegado y sin
  commitear (P2), su /jornada sin horas (P1), sin doc en azure-apps (P3) —
  peticiones al proyecto sesame-api, del humano. F-010 (orm_models
  desincronizado) al backlog. IP de Sigrid redactada en azure-apps
  (deuda previa, commit fe4e977 de ese repo).
- ENCENDIDO futuro (tras P2): variables SESAME_* en sv3 y sv4 A LA VEZ +
  secreto sesame-api-key en kv-partes. OJO: encender contra URL muerta
  bloquea las aprobaciones (por diseño, decisión del humano).
- MANUAL pendiente del humano: merge a dev y push; verificación visual de
  los avisos (R17) cuando se encienda.

## F-013 · Informe de validación de datos Sesame por trabajador — done 2026-08-18

- Rama `feature/F-013-informe-validacion-sesame` (HEAD APPROVED `c2e1c5e`) ·
  rigor estandar · sdd=false (acceptance como mini-spec, propuesta
  confirmada por el humano) · 1 ciclo de review (CHANGES_REQUESTED formal:
  análisis del superviviente en `mutacion_F-013.md`; resuelto + NB-1).
- Entregado: `services/partes-front/validar_datos_sesame.py`, herramienta de
  consola de SOLO LECTURA que lista los empleados que conoce sesame-api
  (`GET /api/v1/empleados`, hecho en el propio script para no tocar los
  clientes gemelos sv3/sv4) y por cada uno saca con el `SesameApiClient`
  de F-003 EN CRUDO (sin `CalendarioProvider`, para que los 404 se vean)
  festivos del año, tipo de jornada, reducida y tipo de contrato; informe
  Markdown + CSV (`;`, BOM) en `services/partes-front/logs/` (ignorado por
  git: lleva DNIs), con calendario por defecto, resumen (distribuciones,
  «(no se pudo leer)», DNIs con error) y tabla por trabajador. Errores por
  trabajador = filas; solo abortan listado (exit 1) y configuración
  (exit 2). Configuración `--base-url/--api-key` > `--env` >
  `SESAME_API_BASE_URL/SESAME_API_KEY` > localhost:8006. Sección
  «Herramientas de consola» en ARCHITECTURE.md.
- Verificado (reviewer, independiente): init.sh verde, 314 tests sv4 (42
  nuevos, sin red), cobertura del diff 99,6 %, mutación 77/76 con 1
  superviviente equivalente analizado (retries del transporte real), fase
  RED en el historial (0e6a47f), clave nunca en informe/log, contrato de
  sesame-api contrastado con su código, ruff limpio, camino de aborto
  probado.
- MANUAL pendiente del humano: ejecutar el script contra sesame-api local
  y validar los números (alimenta F-011/F-012). Comando en
  `progress/impl_F-013.md`.
- Automejoras del arnés propuestas por el reviewer (pendientes de decisión
  del humano; genéricas ⇒ arnes-base): AM-1 oficializar `test_fXXX_aN_*`
  para features sdd=false; AM-2 campo `base` opcional en features.json que
  lea `harness.alcance` (evita alcances inflados al ramificar desde una
  feature no mergeada); AM-3 el reviewer recalcula con la MISMA base que
  declara el informe de mutación.

## F-004 · Congelar registros aprobados — done 2026-08-18

- Rama `feature/F-004-congelar-aprobados` (HEAD APPROVED `c27dc04`) · rigor
  estandar · sdd=true · spec aprobada por el humano (3 decisiones tal cual)
  · APPROVED a la primera (`progress/review_F-004.md`).
- Entregado (solo sv4, sin cambio de schema ni orm_models): módulo
  `application/services/congelacion.py` (matriz R1: `approved` del
  documento + `sigrid_estado` ∈ {encolado, registrado} congela;
  omitido/error/conflicto editables; `CongeladoError`), guardas en el
  repositorio para línea y documento con handler → 409 `congelado: true`
  y motivo; `unapprove` bloqueado con líneas `encolado` y las `registrado`
  siguen congeladas; reasignación/conciliación/undo y borrados masivos
  omiten congeladas y reportan recuento; papelera y hard-delete bloqueados
  con `registrado`; flags a vistas y matriz (candado, disabled, banner
  🔒), `static/app.js` sin editores en filas congeladas y mostrando el
  motivo del 409; regla documentada en ARCHITECTURE.md.
- Verificado (reviewer, independiente): init.sh verde, **448 tests sv4**
  (134 nuevos; 314 previos intactos, comprobado en worktree de la base),
  cobertura del diff **100 % (183/183)**, mutación **54/53 con 1
  superviviente equivalente** analizado, fase RED por tarea en el
  historial, `node --check` OK, ruff limpio en lo nuevo, camino
  aprobar→editar 409→desaprobar→editar OK reproducido con TestClient.
- No bloqueantes: `crear_extra_desde` más estricto que la letra de R5
  (superconjunto coherente); `#fechaEdit` disabled sin data-congelado
  (cosmético); ventana teórica en `unapprove` entre sesiones (sin riesgo);
  3 SAWarning de DELETE previos a F-004 (→ F-010).
- MANUAL pendiente del humano (pasos en `progress/impl_F-004.md` /
  review): 7 comprobaciones en navegador con Ctrl+F5 (banner y candados en
  parte aprobado, 409 sobre línea registrada, encolado bloquea «Marcar
  pendiente», matriz solo lectura, masivas y papelera avisan y omiten, no
  regresión de ↻/Revisar/Aprobar).
- Automejoras del arnés propuestas (pendientes de decisión; genéricas ⇒
  arnes-base): puerta de cobertura contra la base real de la rama (campo
  `base` o merge-base) — coincide con AM-2 de F-013; el reviewer debe
  REPRODUCIR una fase RED en un worktree del commit RED; `harness.mutacion`
  debe `git worktree prune`/limpiar en `finally`.

## F-012 · Estudio: candef 9 h, viernes y jornada semanal particularizable — done 2026-08-18

- Estudio sin código (rigor documental): el entregable es la propia spec
  `specs/F-012-estudio-jornada-semanal/` (requirements bloque A = el
  estudio, bloque B = requisitos EARS que hereda F-015; design H1–H8 con
  datos reales de Sigrid vía sigrid-api solo lectura y anexo SQL
  reproducible; tasks). Rama de cierre
  `feature/F-012-estudio-jornada-semanal` (HEAD 0333c69). Spec aprobada
  por el humano el 2026-08-18; 1 ciclo de review (bloque B contradecía
  una decisión, decisiones cerradas en «abiertas», tasks sin marcar) y
  APPROVED en segunda pasada con errata E1 corregida por el líder.
- Hallazgos clave: candef 9 = 1 recurso (MO/0037, sin DNI en emp); en
  3.498 viernes no hay ninguno de 4 h (la práctica es 8 − 2 / 8 − 3);
  los >40 h son una cuadrilla de 7 oficiales de 1.ª con candef 8 que
  registran 9-9-9-9-6 = 42 (48 antes de 2026-05); intensiva de verano
  7×5 masiva (F-011); Sigrid tiene auxtur/emphis.turide vacíos pero
  emphis.porjorlab (% jornada) con datos reales; contratos Sesame vacíos.
- Decisiones del humano (firmes): jornada semanal DERIVADA del candef por
  mapa configurable {8:40, 9:42} en env espejo sv3+sv4; «resto» en el
  ÚLTIMO DÍA LABORABLE de la semana del trabajador (calendario F-003), el
  festivo cuenta como jornada; candef válido fuera del mapa → jornada
  plana 5×candef + WARNING; sin calendario → viernes; excepciones en tabla
  `empleado_jornada` (UI en F-016, SQL manual mientras); F-010 antes de
  F-015; excluir del re-split lo registrado/encolado/approved.
- Reviewer (independiente): 18/18 sentencias del anexo ejecutan tal cual
  y las cifras cuadran exactas; sin DNIs/claves en la spec; init.sh verde.
- Salen de aquí: F-014 (candef 9 en Sigrid a MO/0006, 0007, 0008, 0031,
  0366, 0405, 0456 y DNI de MO/0037 — MANUAL RRHH/Administración),
  F-015 (implementación) y F-016 (UI). F-011 replanteada sobre
  `empleado_jornada` + `emphis.porjorlab`.

## F-010 · Saneamiento: resincronizar orm_models.py entre sv3 y sv4 — done 2026-08-18

- Rama `feature/F-010-resincronizar-orm-models` (HEAD APPROVED `cd62e5b`,
  base dev 716a4f7) · rigor estandar · sdd=true · spec aprobada por el
  humano (D2 DDL generado, D3 índice, D4 SAWarning, D5 docs en el sitio) ·
  APPROVED a la primera (`progress/review_F-010.md`). Arranque accidentado
  por saturación de la API (3×529 + 1 stall), sin pérdida de trabajo.
- Entregado: `orm_models.py` canónico (unión: base sv3 + `sigrid_*` y
  `UndoLogOrm` de sv4) BYTE-IDÉNTICO en sv3 y sv4; `ddl_complementario()`
  generado desde el ORM (`ADD COLUMN IF NOT EXISTS` de la unión + índices;
  118 sentencias, idempotente) usado por `initialize()` de sv3 y sv4 (las
  listas a mano desaparecen); guardián en `tests/` de la raíz que exige las
  dos copias byte-idénticas; borrado de papelera/hard-delete en sv4 sin
  los 3 SAWarning (se quita el DELETE masivo, la cascada borra); esquema
  real documentado y corregido en el sitio en `docs/referencia/
  partes-proyecto.md` §5 (línea de corrección en cabecera; `approved*` en
  parte_registros no existía) y `azure-apps/partes.md` §4 (commit local
  8f55505). Único cambio físico previsto en la BBDD `partes`: el índice
  `ix_parte_registros_deleted_at_utc` (autorizado; tabla de 104 filas).
- Verificado (reviewer, independiente): init.sh verde, 676 tests (raíz +
  sv3 + sv4 + sv5) sin regresión, guardián roto a propósito en worktree,
  DDL recalculado, cobertura 100 % (60/60), mutación 23/23 (3 candidatos a
  superviviente comprobados uno a uno), C3 bis limpio, ruff limpio, ningún
  test toca PostgreSQL real.
- MANUAL pendiente del humano (pasos exactos en `progress/impl_F-010.md`
  §6): M1 arrancar sv3 o sv4 en local y comprobar en `pg_indexes` el
  índice nuevo (recomendación: mirar también `parte_documents`) y que las
  columnas siguen siendo empleado_alias 7 / parte_documents 47 /
  parte_registros 56 / undo_log 7; M2 arranque de sv3 y sv4 con «esquema
  inicializado (118 sentencias complementarias)» en ambos; M3 redeploy
  cuando decida (sv3 antes que sv4, no crítico).
- Observación para F-015: `undo_log.undone` se genera `NOT NULL` sin
  DEFAULT porque la BBDD real es así; una columna nueva NOT NULL sin
  default sobre tabla con filas hará fallar el arranque «en voz alta»
  (deliberado, documentado en el docstring del generador).
- Automejora del arnés (pendiente, genérica ⇒ arnes-base, para F-009):
  `harness/mutacion.py` solo ejecuta la suite del servicio dueño del
  fichero mutado, así que los guardianes de la raíz nunca matan mutantes
  ⇒ supervivientes falsos; debería ejecutar también la suite de la raíz (o
  todas las que importan el fichero).

## F-015 · Jornada del día por jornada semanal derivada del candef y último laborable (2026-08-19)

- Rama `feature/F-015-jornada-semanal-candef`, 19 commits + cierre del líder.
  Rigor `estandar`, `sdd: true`. Spec: `specs/F-015-jornada-semanal-candef/`
  (R10–R35, 13 tareas), nacida del estudio F-012 y de sus decisiones firmes.
- Qué hace: la jornada deja de ser el candef plano y pasa a ser **jornada del
  día**. L–V vale el candef efectivo salvo el **último día laborable** de la
  semana del trabajador (calendario de F-003; un festivo cuenta como jornada),
  que recibe `max(0, S − 4c)`. La jornada semanal `S` se **deriva del candef**
  por el mapa configurable `JORNADA_SEMANAL_POR_CANDEF` (`8:40,9:42`, variable
  espejo en sv3 y sv4, fail-fast al arrancar); candef válido fuera del mapa ⇒
  `5×c` + WARNING. Excepciones por trabajador en la tabla nueva
  `empleado_jornada` (19 columnas, declarada en las DOS copias del ORM, nace
  vacía); si su lectura falla ⇒ derivada + WARNING.
- Regresión cero: con `c = 8` y `S = 40` el último laborable recibe
  `40 − 32 = 8`, idéntico a hoy con festivos o sin ellos. Los tests dorados de
  F-003 quedaron **intactos** y verdes.
- Congelados (D7, lectura NO literal aprobada por el humano): las líneas
  `encolado`/`registrado`/`approved` **cuentan en el total del día pero no se
  modifican nunca**; si el día no cuadra sin tocarlas, no hay split y se avisa.
  La lectura literal habría dado una segunda jornada completa en días mixtos.
- Verificado (reviewer, independiente): `init.sh` verde, **1.195 tests**
  (raíz 92, sv3 438, sv4 665), cobertura de líneas cambiadas **99,4 %**
  (520/523), mutación **259/237/22/0 → 91,5 %**. El reviewer **recalculó** el
  alcance y los mutantes con las herramientas del arnés (coincidencia fichero a
  fichero), muestreó 9 de los 22 supervivientes contra el generador y
  **confirmó leyendo el código tres grupos de equivalencias**.
- Tres campañas de mutación, documentadas las tres: la 1.ª dio **100 timeouts**
  (16 evaluadores × suite de sv4 de ~80 s contra el presupuesto de 120 s de
  `rigor.json`) y NO es una medición; la 2.ª (211/48) motivó **+70 tests**; la
  3.ª es la válida. El salto 211 → 237 muertos es el valor de esos tests.
- La mutación destapó **un fallo real de diseño**: la rama «sin fecha
  utilizable» inventaba `5×c` con `origen="plana"` aunque el candef estuviera
  en el mapa — mentía en el KPI y disparaba un WARNING falso. Corregido y con
  test.
- Huecos de test que destapó y se taparon: el adaptador
  `SqlAlchemyJornadaRepository` de sv3 **no tenía ningún test** (sobrevivía
  invertir `is_active`, es decir leer justo las filas retiradas); bordes de
  `Excepcion.valida()` y `parsear_mapa_semanal`; tres de las cuatro ramas de
  `ultimo_laborable`; asserts que colaban un signo cambiado por usar `in` en
  vez del prefijo exacto.
- **CONFIRMA con datos la automejora del arnés ya anotada en F-010**:
  `harness/mutacion.py` solo ejecuta la suite del servicio dueño del fichero
  mutado, así que el guardián de una copia gemela —que vive en `tests/` de la
  raíz— nunca entra. Fueron **27 de los 48 supervivientes** de la 2.ª campaña,
  todos falsos «equivalentes». Contramedida aplicada aquí: cada copia tiene ya
  sus propios tests de la regla en la suite de su servicio. Arreglo genérico
  propuesto (F-009 ⇒ `arnes-base`): ejecutar también la suite de la raíz
  (~4 s en este repo) o, como mínimo, avisar en el informe cuando el fichero
  mutado tenga copia gemela declarada en `CLAUDE.md`.
- `CLAUDE.md`: `application/services/jornada_resolver.py` entra en la lista
  cerrada de duplicación tolerada (decisión del humano del 2026-08-19).
- Puerta R35 **invertida** por decisión del humano: F-015 se mergea y despliega
  **sin** F-014 (regresión cero). Lo que no se puede es aplicar el `candef = 9`
  en Sigrid antes de desplegar F-015 (daría −3 h/semana a esos 7 recursos).
- MANUAL pendiente del humano: **T12** (`specs/F-015-.../tasks.md`), tras
  desplegar sv3 y sv4 — «esquema inicializado (N sentencias)» en ambos y las
  19 columnas de `empleado_jornada` con su índice; un viernes de 6 h de la
  cuadrilla sin aviso de incompleta y el KPI «9 h · 42 h/sem · último laborable
  6 h»; y que un parte ya aprobado no cambie su desglose tras la primera pasada
  de sv3.

## F-016 · Pantalla de administración de `empleado_jornada` en el portal (2026-08-19)

- Rama `feature/F-016-admin-empleado-jornada`, 11 commits sobre el merge de
  `dev` + cierre del líder. Rigor `estandar`, `sdd: true`. Spec:
  `specs/F-016-admin-empleado-jornada/` (R1–R20, T0–T10), aprobada por el
  humano tras dos pasadas del spec-author.
- Qué hace: `/admin/jornadas` en sv4 permite crear, editar, cerrar, desactivar
  y reactivar las excepciones de jornada que F-015 dejó sin UI. Cinco endpoints
  JSON bajo `/api/admin/`, validación pura en
  `application/services/jornada_admin.py` (vecino de `congelacion.py` de
  F-004), cinco métodos nuevos en el repositorio de sv4 y una sola variable
  nueva, `JORNADAS_ADMIN_ENABLED`.
- Las tres decisiones que definen la pantalla: **el humano nunca ve ni escribe
  `hasta`** (habla de «último día incluido» y el `+1 día` vive solo en la capa
  web, R7); **cerrar ≠ desactivar** (fin de vigencia vs papelera lógica, sin
  un solo `DELETE`); y **un solape se rechaza con 409 nombrando la fila en
  conflicto y nunca se ajusta la fila ajena** (R12), porque recortar la
  vigencia de otro reescribiría en silencio un dato con el que sv3 ya calculó
  extras.
- Se reutiliza lo existente en vez de reinventarlo: el selector de trabajador
  consume `GET /api/sigrid/empleados` (F-003) y el componente `_comboSimple`
  **sin tocarlos**, y el bloque JS va DENTRO del IIFE que define esa función
  —desde un IIFE nuevo al final del fichero no se vería—. Con Sigrid apagado la
  página sigue entera por el camino de alta manual.
- Verificado (reviewer, ejecutando y recalculando): `init.sh` verde, **799
  tests en sv4** (134 nuevos) + 92 en la raíz, cobertura de líneas cambiadas
  **98,5 %** (326/331), mutación **93/79/14/0** (85 %) con los 14 supervivientes
  analizados. El reviewer recalculó el alcance (827 líneas) y los 93 mutantes
  fichero a fichero, y muestreó tres supervivientes contra el generador.
- Cero cambios de schema (R1): la tabla sigue con sus 19 columnas, ninguna
  copia de `orm_models.py` tocada, el guardián de F-010 en verde sin
  modificarse y **sv3 sin un solo fichero cambiado**.
- Observación heredada por **F-017** (anotada en su descripción): el test
  `test_f016_r13_auditoria` parchea `DEFAULT_REVIEWER` en vez del helper
  `_actor`, así que se pondrá rojo cuando `_actor` devuelva el principal real.
- Observación informativa: `JORNADAS_ADMIN_ENABLED` no queda en ningún fichero
  versionado porque `services/partes-front/.gitignore` ignora `*.example`. El
  implementer NO forzó un `git add -f` y el reviewer le da la razón: revertir
  una decisión del repositorio por la puerta de atrás es peor. Queda con
  default `True` en el código y documentada en `azure-apps/partes.md`.
- Deuda transversal detectada, NO de esta feature: la suite de sv4 pasa de
  ~52 s a ~114 s porque cada test de endpoint levanta `build_app` entera
  (patrón de F-002/F-003/F-004). Candidata a fixture de app compartida ⇒ F-009.
- Automejoras del arnés propuestas por el reviewer (⇒ F-009 y `arnes-base`):
  que `progress/mutacion_*.md` registre **qué suite se ejecutó** por fichero
  (hoy no se puede detectar el hueco de las copias gemelas sin recalcular), y
  que C4 de `CHECKPOINTS.md` pida un **recuento mecánico test-por-requisito**
  sobre los nombres `test_fXXX_rN_*` en vez de fiarse de la tabla de
  trazabilidad de la spec.
- MANUAL pendiente del humano: las 6 verificaciones de `design.md` §8.2
  (portal levantado, PostgreSQL y navegador). La 6 —comportamiento del combo en
  el navegador— es la única funcionalidad que ningún test cubre.

---

## F-017 · Identidad real de Easy Auth en el portal (sv4) — done 2026-08-21

- Rama `feature/F-017-identidad-easy-auth` · rigor estandar · sdd=true ·
  **APROBADO** del reviewer en segunda vuelta (`progress/review_F-017.md`).
  Detalle en `progress/impl_F-017.md` y `progress/mutacion_F-017.md`.
- Entregado: `interface_adapters/web/identidad.py` (cinco funciones puras que
  traducen cabeceras a `(actor, origen)`, sin FastAPI ni I/O), `_actor` pasa a
  leer Easy Auth, los once puntos de auditoría firman con la identidad real,
  `GET /whoami` para diagnóstico, y el consumidor de resultados deja de leer
  `DEFAULT_REVIEWER` (R24). Un solo servicio: **sv4**. **Cero cambios de
  schema.**
- Verificado: init.sh en verde, **1.057 tests en sv4** + 138 en la raíz,
  cobertura **99,3 %** (141/142 líneas cambiadas), mutación **32/32 muertos,
  0 supervivientes, 0 timeouts** (re-ejecutada por el reviewer, que recalculó
  el alcance: 3 ficheros / 462 líneas / 32 mutantes, coincidencia exacta).
- **T0 fue una puerta bloqueante y pasó**: las cuatro `CONTAINER_APP_*`
  existen en `ca-sv4-front`, comprobadas variable a variable. El implementer
  detectó que el comando `printenv` que proponía la spec **habría volcado los
  secretos de Key Vault**, y lo corrigió en la spec.
- **Enmienda de R14/R15 durante la implementación**: la spec decía que los
  borrados y el alta manual escribirían en `undo_log.actor`; se verificó en el
  árbol que **eso no describía el código** (esas operaciones no generan filas
  de `undo_log`, y `crear_parte_manual` declaraba `by` sin usarlo). Decisión
  del humano: enmendar los requisitos, no ampliar el alcance. El reviewer
  validó por su cuenta que la enmienda era honesta y no una tapadera.
  Consecuencia documentada: `undo_log.actor` NO participa del criterio del
  corte y sigue siempre a `NULL`.
- **Primera vuelta RECHAZADA**, con tres defectos que merece la pena recordar:
  (1) una tercera lectura de identidad en `resultado_consumer.py`, invisible
  para el guardián porque solo miraba `app.py` — se corrigió Y se amplió el
  guardián a todo sv4 con `rglob`, y el reviewer lo verificó **rompiéndolo**
  (sembró la lectura en un fichero desechable y el guardián se puso rojo);
  (2) la enmienda de R14/R15 no se había propagado a los otros cuatro sitios
  que enunciaban el corte, y **F-018 lo habría heredado**; (3) la spec seguía
  proponiendo el `printenv` peligroso, porque el `Select-String` filtra la
  vista, no el volcado.
- **Hallazgo que originó la feature** (verificación del despliegue del
  2026-08-20): `DEFAULT_REVIEWER` nunca estuvo configurada en Azure, así que
  la auditoría del portal no llevaba «un genérico», llevaba **NULL desde el
  primer despliegue**. Decisión del humano: no poner un genérico provisional.
- **Evidencia para el arnés**: la campaña con el presupuesto por defecto de
  `rigor.json` (120 s, concurrencia alta) dio **8 timeouts de 32** con la
  suite de sv4 ya en 1.057 tests; con `--timeout 420 --workers 4` los 8
  resultaron ser mutantes muertos. **Un timeout no es una medición.** Refuerza
  la automejora ya anotada. Además: la campaña paralela **exige árbol limpio**
  (aborta con exit 2 explicándolo, porque crea los worktrees desde `HEAD`), y
  **canalizar su salida por `tail` se traga el código de salida** — el mismo
  motivo por el que `init.sh` se lanza sin pipes.
- **Verificado DESPLEGADO el 2026-08-21** con `GET /whoami`: Azure inyecta el
  **UPN** en `X-MS-CLIENT-PRINCIPAL-NAME` (no el display name), el origen es
  `cabecera-name` y el entorno se detecta por `CONTAINER_APP_NAME`. La única
  ambigüedad que la spec no podía cerrar se cerró a favor de lo diseñado.
  De propina: Easy Auth inyecta también **`X-MS-CLIENT-PRINCIPAL-ID`**, el
  `oid` inmutable, dato que F-017 daba por no disponible sin decodificar el
  token y que se anota como material de F-018.

---

## F-005 · Retirar `graphkey_nobom.json` y constancia de `GRAPH_KEY` en Key Vault — done 2026-08-25

- Rama `feature/F-005-graphkey-keyvault` · rigor documental · sdd=false ·
  APROBADO del reviewer (`progress/review_F-005.md`), tras una ronda de
  `CHANGES_REQUESTED`.
- Contexto: la feature nació como «mover GRAPH_KEY a Key Vault + retirar el
  fichero del despliegue». Al estudiarla, **los dos objetivos estaban
  cumplidos de hecho**: los tres servicios que usan Graph (sv1, sv3, sv4)
  llevan `GRAPH_KEY=secretref:graph-key` contra una referencia a Key Vault, y
  ningún script de `infra/` lee `graphkey_nobom.json` —`add_secrets_partes.ps1`
  pide el JSON por consola con `Read-Host -AsSecureString`—. Se reabrió como
  limpieza por decisión del humano: `sdd=false` y cinco criterios `acceptance`.
- Entregado: borrado de `infra/graphkey_nobom.json` (no versionado, **nunca
  entró en git**, comprobado con un barrido de `git ls-tree` sobre toda la
  historia); `CLAUDE.md`, `README.md` e `infra/README_partes.md` dejan de
  presentarlo como fichero del despliegue y explican dónde viven de verdad los
  secretos; constancia fechada de la comprobación contra Azure en
  `progress/current.md`; `azure-apps/partes.md` §5.5 actualizado en el mismo
  trabajo (`ff22735` y `65430cd`).
- Hallazgo H1 del implementer, resuelto: `infra/partes-infra.zip` guardaba una
  **segunda copia del `client_secret`** en claro. Borrado por decisión del
  humano el 2026-08-25; en el árbol no queda rastro de `graphkey*`.
- La ronda de rechazo fue por dos afirmaciones falsas en documentación, el
  mismo defecto que la feature venía a eliminar. Y **la puerta de tamaño del
  arnés 1.7.3 mordió por primera vez**: el informe del reviewer salió a
  151/140 y lo recortó él, no el implementer.
- Verificado: init.sh en verde (402 pasados, 1 saltado), cobertura y mutación
  N/A por nivel `documental` con el motivo impreso, cero secretos en el diff
  `dev...HEAD`.

## F-020 · Ingesta de sv1: correos adjuntos encadenados hasta el PDF — done 2026-09-30

- Rama `feature/F-020-correo-adjunto-escaner` · rigor estandar · sdd=true ·
  APPROVED del reviewer (`progress/review_F-020.md`).
- Motivo: el escáner envía el parte como correo adjunto (`message/rfc822`)
  con el PDF dentro; sv1 descartaba los `itemAttachment` y el correo caía en
  `Errores`. Sonda de solo lectura previa (`progress/explore_F-020_sonda.md`):
  `$value` devuelve el MIME RFC 822 con el PDF.
- Entregado (solo sv1): `MimePdfExtractor` (stdlib `email`, recursivo, tope 5
  niveles) tras el puerto `ExtractorCorreoAdjunto`; el pipeline abre correos
  adjuntos de cualquier remitente (item o fileAttachment), ingiere cada PDF
  interior por el camino de siempre y añade `embedded_in` al contexto.
  Decisiones del humano: D2 correo adjunto sin PDF junto a otros ingeridos ⇒
  Procesados con WARNING; D3 tope excedido ⇒ nada de ese correo adjunto;
  D4 `.eml` como fichero también se abre. sv2/sv3 sin cambios (verificado).
- Verificado: primera suite de sv1 (74 tests, sin red), init.sh en verde,
  cobertura 99.0 %, mutación 20 muestreados con 1 superviviente equivalente.
- Observaciones no bloqueantes: `azure-apps/partes.md` §3.1 no menciona los
  correos adjuntos (decisión del humano); log de R23 algo impreciso cuando el
  único adjunto es un correo adjunto descartado por tamaño.
- Pendiente del humano: desplegar sv1 y verificación manual (ver
  `current.md`).

## F-023 · Casado de trabajador/recurso: solo de alta y por empresa — done 2026-10-01

- Rama `feature/F-023-recurso-alta-empresa` · rigor critico · sdd=true ·
  APPROVED del reviewer en la pasada 2 (`progress/review_F-023.md`; la 1
  pidió tres cambios documentales y de formato).
- Pedida por el humano y por el correo de Juan Romero «RV: CAPTURAS» (el
  portal cogió MO/0239, de baja desde 2021, porque la ficha del empleado
  apuntaba a él con `emp.reside`). Exploración de Sigrid en
  `progress/explore_F-023_sigrid.md`: 22 códigos de obra con gemela activa en
  las empresas 1 y 28; sv5 numeraba `PT` mezclando empresas.
- Entregado (sv2, sv3, sv4, sv5): sv2 lee `empresa_membrete`; sv3 la traduce
  con alias versionados y casa obra, empleado y recurso por empresa y por
  alta (`con.fecbaj`) a la fecha de la línea, con revisión cuando no puede
  decidir; sv5 numera y localiza `hmo` por la empresa de la obra y verifica
  empresa/alta/DNI antes de escribir; portal con empresa en los combos y alta
  manual filtrada; listados de Sigrid paginados y `truncated` como error;
  tres columnas nuevas en `parte_documents`; `SIGRID_EMPRESA` inerte. Lista
  cerrada de duplicación de `CLAUDE.md` ampliada (DA6) con guardián.
  `azure-apps/partes.md` actualizado (commit local `8c7df86`).
- Verificado: init.sh en verde (raíz 416, sv3 640, sv4 1.093, sv5 141, sv2
  8), cobertura 99,8 % de 597 líneas, mutación completa 214/214 muertos.
- Observaciones no bloqueantes: con Sigrid caído en arranque en frío, las
  líneas no congeladas sin obra pasan a `sin_recurso`; en «Añadir línea»,
  elegir la obra después del trabajador no limpia una ficha de otra empresa
  (sv5 la omitiría); `partes_existentes` localiza `hmo` por `obride`.
- Pendiente del humano: M1, M5, despliegue sv5 → sv2 → sv3 → sv4, M2, M3, M4
  y T17 (ver `current.md`).

## F-024 · Líneas borradas en Sigrid y estado «encolado» en el portal — done 2026-10-01

- Rama `feature/F-024-lineas-encoladas` · rigor critico · sdd=true · APPROVED
  del reviewer (`progress/review_F-024.md`).
- Origen: correo de Juan Romero «RV: CAPTURAS» (línea en «encolado» aunque el
  parte estaba en Sigrid). Investigación (`progress/explore_F-024.md`): sv5
  escribió 35 líneas el 30/09 en PT26/00314 y Administración las borró a
  propósito en Sigrid; el portal las seguía dando por registradas y
  congeladas. El «encolado» era una vista recargada antes del resultado.
- Entregado: sv5 expone `POST /api/registro/comprobar` (solo lectura, por
  synckey con respaldo por `hmores.ide`); sv4 añade el estado
  `borrado_sigrid` (no congela), lo comprueba en segundo plano al entrar en
  la vista de obra y de persona (antimartilleo 120 s) y con el botón
  «Comprobar en Sigrid», «Reaprobar» por línea; las aprobaciones masivas
  excluyen `registrado` y `borrado_sigrid` salvo casilla; el modal sondea el
  resultado en vez de recargar. Decisiones del humano: comprobación al entrar
  en la obra (no barrido horario) y también en la vista de persona.
- Verificado: init.sh en verde (sv4 1.219, sv5 203, sv3 640, raíz 419),
  cobertura 99,7 % de 347 líneas, mutación completa 175 mutantes (22
  supervivientes matados con tests nuevos, 1 equivalente justificado).
- Observaciones no bloqueantes: avisos de ruff autocorregibles en ficheros
  nuevos de sv5; un fallo a mitad de varios lotes deja aplicados los
  anteriores (lo pide R14); en la vista de persona con muchos lotes el
  navegador puede cortar a los 90 s y decir «no se pudo» aunque sv4 termine.
- Pendiente del humano: despliegue sv5 → sv4 y M1–M5 (ver `current.md`).

## F-021 · Cuenta analítica en las líneas que sv5 registra en Sigrid — done 2026-10-01

- Rama `feature/F-021-cuenta-analitica-sigrid` · rigor critico · sdd=true ·
  APPROVED del reviewer (`progress/review_F-021.md`).
- Origen: correo de Juan Romero «RV: CAPTURAS» («no arrastra cuenta
  analítica del recurso»). Exploración (`progress/explore_F-021_sigrid.md`):
  la cuenta del recurso es `reshor.caaide` (plantilla del centro `00000`);
  la línea manual lleva la cuenta del centro de su obra con esa subcuenta
  (99,64 % en la empresa 1); Porsan no usa cuenta en horas.
- Entregado: sv5 resuelve la subcuenta del tipo escrito (o del tipo por
  defecto) y escribe en `hmores.caaide` la cuenta del centro de la obra;
  sin cuenta ⇒ 0 y aviso, sin bloquear; fallo al leer cuentas ⇒ la petición
  falla sin escribir nada; sv4 avisa en el modal del preflight de las líneas
  sin cuenta. Sin reescritura de lo ya registrado.
- Verificado: init.sh en verde (sv5 269, sv4 1.230, raíz 419), cobertura
  100 % de 75 líneas, mutación completa 33/33 muertos.
- Observación O1: el docstring de `_resolver_cuentas` afirma un reintento de
  cola que no existe.
- Pendiente del humano: despliegue sv5 → sv4 y M1–M4 (ver `current.md`).

## F-022 · Aprobar solo lo seleccionado, una petición por obra y listado en el modal — done 2026-10-01

- Rama `feature/F-022-aprobar-seleccionadas` · rigor critico · sdd=true ·
  APPROVED del reviewer (`progress/review_F-022.md`).
- Origen: humano y correo de Juan Romero («seleccionar varias líneas y
  aprobarlas, por si quiero dejar alguna pendiente»). Hallazgo de la spec:
  sv5 escribía toda una petición en el parte de UNA obra (la de la primera
  línea); en la ficha de persona «Aprobar visibles» podía llevar horas a la
  obra equivocada (no llegó a ocurrir: sv5 solo escribió el 30/09).
- Entregado (solo sv4; sv5 sin cambios): casillas sobre la selección
  existente, «Seleccionar visibles»/«Quitar selección»; sin marcar aprueba lo
  visible, con marcadas solo esas; validación de ámbito en servidor; reparto
  en una petición por obra con resultado por obra (sin «todo o nada»),
  claves de conflicto con grupo, tope de 10 obras; modal con el listado de
  lo que se va a aprobar construido por el servidor (por obra, totales,
  estado y excluidas, plegado con más de 40 filas). Decisiones del humano:
  repartir por obra en vez de rechazar, y el listado «como porcentajes».
- Verificado: init.sh en verde (sv4 1.428, raíz 419), cobertura 100 % de 282
  líneas, mutación completa sin supervivientes sin resolver.
- Observaciones: O4 escape heredado en modales anteriores y O5 selector sin
  escapar ⇒ F-027; O2 `parcial:false` cuando fallan todas (R22 decía true).
- Pendiente del humano: despliegue de sv4 y M1–M8 (ver `current.md`).

## F-025 · Incompatibilidad incidencia/horas el mismo día — done 2026-10-02

- Rama `feature/F-025-incidencia-vs-extra` · rigor estandar · sdd=true ·
  APPROVED del reviewer (`progress/review_F-025.md`).
- Origen: correo de Juan Romero «RV: CAPTURAS» (incidencia de baja por
  maternidad con una hora extra el mismo día). Exploración
  (`progress/explore_F-025_sigrid.md`): Sigrid no clasifica las incidencias;
  Administración casi nunca junta incidencia y horas (5 de 1.191 días en
  2026); la H es Huelga (corregido en `partes-proyecto.md`).
- Entregado (solo sv4): tabla versionada `config/incidencias.yaml` (día
  completo V, B, M, F, H —huelga cambiada a día completo por el humano—; parcial AT, FJ; si está mal, sv4 no arranca);
  detección por día-trabajador cruzando obras; día completo + horas ⇒ líneas
  excluidas de la aprobación con motivo propio en el modal de F-022, sin
  forzar; parcial + extra ⇒ aviso; marcado en matriz, calendario y líneas de
  las vistas de obra y persona; nada se bloquea al crear o editar.
- Verificado: init.sh en verde (sv4 1.535), cobertura 100 % de 204 líneas,
  mutación muestreada con 6 supervivientes (5 con test nuevo, 1 equivalente).
- Observaciones: los avisos agregados del modal no nombran la obra;
  `/api/admin/poison/reencolar` reenvía sin pasar por la exclusión.

## F-028 · Detalle de obra y de trabajador a todo el ancho — done 2026-10-02

- Rama `feature/F-028-ancho-detalle` · rigor estandar · sdd=false · APPROVED
  del reviewer en la primera pasada (`progress/review_F-028.md`). Petición del
  humano con captura: scroll horizontal en el detalle de obra con sitio de
  sobra en un monitor de 3440 px.
- Causa: `.container` topaba todo el portal a 1500 px. Entregado (solo sv4):
  bloque Jinja `container_class` en el contenedor del `<main>` de `base.html`
  (vacío por defecto), `container--ancho` en `obra_detail.html` y
  `trabajador_detail.html`, regla `width: calc(100% - 32px)` en
  `styles.css`. Listados y topbar sin cambios (decisión del humano).
- Verificado: 13 tests `test_f028_*` (RED 4 failed antes del cambio), sv4
  1548 passed, init.sh en verde. Mutación N/A por lenguaje (sin Python de
  producción); el reviewer hizo una campaña manual de 9 mutantes sobre
  plantillas y CSS, 9 muertos.
- Observaciones: O2, anchos de columna guardados en localStorage pueden
  estirar la tabla o mantener el scroll (doble clic en la manija los
  reajusta); propuesta de automejora de C4 bis para «proyecto Python sin
  líneas Python de producción» (sin aplicar).

## F-019 · Horas de los mensuales a dedicación — done 2026-10-03

- Rama `feature/F-019-mensuales-a-dedicacion` · rigor crítico · sdd=true ·
  spec con DA1–DA8 aprobadas por el humano el 2026-10-02 (DA4 opción 2:
  hora mes a dedicación y `HE*` a Sigrid como siempre, blindado en R3 bis) ·
  APPROVED del reviewer en la primera pasada (`progress/review_F-019.md`).
- Entregado: sv5 decide tras el interruptor `MENSUALES_A_DEDICACION`
  (apagado por defecto) la acción `dedicacion` para recursos con `M*`
  (ordinarias, extras sin `HE*`, incidencias); sv4 la marca y escribe
  `dedicacion_bandeja` en la misma transacción (versión por línea, retirada
  con autor, `POST /api/dedicacion/retirar`, «→ dedicación» en las vistas);
  sv3 con el ORM gemelo a seis tablas y la congelación; script
  `infra/sql/01_dedicacion_lectura.sql` (GRANT de lectura dentro de la base
  `partes`, lo ejecuta el humano); docs y `azure-apps/partes.md`
  (`c7ad8e9`, local).
- Verificado: apagado, 0 diferencias frente a `dev` en 730 líneas
  (comparación del reviewer); 11 roturas deliberadas de la regla, 11
  detectadas; cobertura 100 % (201/201); mutación 126 generados, 125
  muertos, 1 superviviente cerrado con test, 0 timeouts (6794 s, 6
  workers); suites sv5 357, sv3 654, sv4 1636, raíz 445.
- Desviaciones aceptadas por el humano el 2026-10-03: D3 (`dedicacion`
  fuera de `ESTADOS_CONGELANTES`, tupla sin uso en producción), D4
  (guardián de `_actor` a 15) y D5 (lista blanca de un `.sql` en F-017).
- Pendiente: M0 antes de desplegar, despliegue sv3 → sv4 → M1/M2 → sv5
  apagado, y M3 al encender cuando `porcentajes` lea la bandeja.
  Automejora propuesta: en rigor crítico, relanzar sin caché las suites de
  servicio en la review.

## F-029 · Alias del logotipo de Ruesma en el membrete — done 2026-10-05

- Rama `feature/F-029-alias-logo-ruesma` · rigor estandar · sdd=false ·
  APPROVED del reviewer en la primera pasada (`progress/review_F-029.md`).
  Origen: revisión por el líder de las plantillas J.310 rev. 1 de Ruesma y
  Porsan (petición del humano tras el ejemplo de Porsan de Administración).
- Hallazgo: `text_match.normalize` convierte la Ξ/≡ del logotipo «ruΞsma»
  en espacio («ru sma») y no casaba con el alias RUESMA. Entregado: alias
  `RUΞSMA` para la empresa 1 en `services/partes-persistencia/config/
  empresas_membrete.yaml`, con comentario; sin código ni cambio de prompt.
- Verificado: 12 tests `test_f029_*` (RED 4 failed), sv3 666 passed,
  init.sh en verde; mutación con alcance vacío (sin Python de producción) y
  campaña manual del YAML (implementer y reviewer). D1: tres asserts de
  F-023 que fijaban la tabla literal, actualizados sin relajar la vigilancia.
- Exploración con Gemini real sobre 4 PDFs (0678 y 0694, Ruesma y Porsan,
  plantilla rev. 0): el logotipo se transcribe `ruesma` (empresa 1) y Porsan
  como su razón social (empresa 28). El alias es red de seguridad. La
  plantilla rev. 1 con DNI queda sin probar con un escaneo real.

## F-030 · Ficha de recurso cuando no hay ficha de empleado — done 2026-10-05

- Rama `feature/F-030-recurso-sin-ficha` · rigor crítico · sdd=true · spec v2
  con DA1–DA9 aprobadas por el humano el 2026-10-05 («el proceso es el mismo
  que con empleado pero contra la ficha de recurso cuando no está la de
  empleado»; «los partes se guardan siempre en el recurso») · APPROVED del
  reviewer en la pasada 2 (`progress/review_F-030.md`).
- Origen: prueba real de Administración con partes de Porsan (obra 0724): un
  trabajador con recurso `MO/` de alta (`res.cif` = su DNI) y sin ficha en
  `emp` salía «Sin recurso».
- Entregado: sv3 completa el DNI leído a 8 dígitos y casa contra «fichas de
  recurso» (MO/ con `res.cif`, sin ficha por DNI ni `conide`) con el MISMO
  proceso que las fichas de empleado (DNI y, si no, nombre con las dos
  juntas; empates a revisión); métodos `recurso_dni`/`recurso_nombre` en el
  campo existente, sin columnas; sv4 al mínimo (casado y fuera de la cola de
  conciliación); sv5 sin código (tests: verificación y cuenta 0 en la 28).
  Lista cerrada y `text_match.py` intactos. `azure-apps/partes.md` `1c7238c`.
- Verificado: cobertura 100 % (59/59), mutación 18/18, suites sin caché sv3
  754, sv4 1657, sv5 362; diferencial del reviewer dev vs HEAD en 20.000
  partes sintéticos: 0 diferencias en lo que ya casaba; oráculo
  independiente sin discrepancias; 17 roturas deliberadas, la única
  superviviente (cableado de `Matchers.recursos`) cerrada con T16.
- Lección: un worktree de agente DENTRO del repo rompe el guardián de `.sql`
  de F-017 (bloqueó F-030 un rato); los worktrees, fuera del repo.
- Pendiente: desplegar sv3 → sv4, reprocesar los 2 partes de prueba de
  Porsan (M3) y M4; Administración puede poner DNI a 2 recursos de la 28 sin
  `cif`.

## F-031 · El parte registrado acaba en el asiento analítico — done 2026-10-06

- Rama `feature/F-031-asiento-analitico` · rigor crítico · sdd=true · spec v5
  aprobada por el humano el 2026-10-05/06 · APPROVED del reviewer en la pasada
  2 (`progress/review_F-031.md`).
- Hallazgo (solo lectura en Sigrid): Sigrid genera un asiento analítico por
  parte al «Contabilizar parte» (estado Imputado), con Debe = Σ `hmores.tot`
  por `hmores.caaide` y Haber por `res.caaconide`. sv5 no escribe asientos.
  La cuenta de la línea sale de la ficha de horas del recurso, nunca de la
  partida cuando difieren (1.013 casos, 0 a favor de la partida).
- Entregado (sv5 y modal de sv4): sv5 nunca escribe en un parte que no esté
  En registro (Cerrado o Imputado, decisión del humano): usa o crea un
  complementario de la obra y mes; duplicados y pisado contra todos los
  partes del periodo; choque con un parte cerrado ⇒ omitir con motivo.
  Cuenta del recurso (F-021) con respaldo de la partida de coste si el
  recurso no tiene. **Alta protegida** del parte (normal y complementario),
  idéntica a la de `porcentajes` F-037, con relectura y un reintento.
  Herramienta de solo lectura `comprobar_asiento_analitico.py`. Cabecera de
  dependencia en `estado_parte.py` y `cuenta_analitica.py` (copiados por
  `porcentajes`). Docs y `azure-apps/partes.md`.
- Desviaciones aprobadas: D1 (test F-002 `partes_existentes` →
  `partes_del_periodo`), DA10 (tests F-023 r32/r34) y DA11 (cabecera; el test
  de copias de porcentajes queda rojo hasta que recopien).
- Verificado: sv5 520+ passed, sv4 1672, raíz 445; cobertura 99,6 %;
  mutación campaña 3 129/129; pasada 2 añade el test de «una sola escritura»
  del alta (cabecera + `hmo`).
- Pendiente: aviso a porcentajes; prueba de escritura en 0404 y despliegue
  sv5 → sv4 (los decide el humano); DA3 con Juan (2 recursos sin
  contrapartida).

## F-033 · Portal: columna Empresa en el listado de obras — done 2026-10-07

- Rama `feature/F-033-columna-empresa` · rigor estandar · sdd=true ·
  APPROVED del reviewer (`progress/review_F-033.md`).
- Origen: la 0678 salía «duplicada» en `/obras`; en Sigrid son dos fichas
  (Ruesma y Porsan) y la fila no decía de qué empresa era.
- Entregado (solo sv4): columna «Empresa» con filtro en `obras_list.html`;
  el valor sale de `parte_documents.empresa` de los partes de la fila, con
  respaldo por la empresa de los recursos de sus líneas dentro de la BBDD
  `partes`; nombres 1 Ruesma, 28 Porsan, si no «Empresa N»; «—» sin dato.
- Primer alcance (detalle, vistas de parte, YAML de nombres) rechazado por el
  humano y reescrito en mínimo.
- Verificado: init.sh en verde, cobertura 100 % (32 líneas), mutación
  12/10/2 (2 equivalentes analizados).
- Pendiente del humano: desplegar sv4 y comprobar `/obras` (0678 en dos filas
  Ruesma/Porsan, filtro de empresa).

## F-037 · sv3 no duplica la extra automática de una base omitida — done 2026-10-07

- Rama `feature/F-037-extras-duplicadas-base-omitida` · rigor critico · sdd=true ·
  APPROVED del reviewer en la pasada 2 (`progress/review_F-037.md`; la 1 pidió
  solo los comandos exactos de M1–M4).
- Origen: 7 extra_auto duplicadas en la 0678 (01–03/10): base `omitido`
  (mensual o 0 h) + extra ya registrada; el revert restauraba la base y el
  recálculo creaba otra extra.
- Entregado (solo sv3): base y extra automática se tratan como pareja; si la
  extra está congelada, la base no se revierte ni se re-parte (no se genera
  ninguna extra nueva); la primera pasada borra las extra_auto no congeladas
  duplicadas con WARNING de ids; dobles congeladas solo avisan. Regla de
  congelación compartida sin cambios.
- Verificado: init.sh en verde, cobertura 100 % (83/83), mutación completa
  21/21 muertos, 0 supervivientes. M1 en producción antes de desplegar: 0.
- Pendiente: desplegar sv3 (lo pide el humano) y M2–M4 (comandos en
  `current.md`).

## F-036 · sv3: casar el trabajador leído contra los recursos persona de la empresa — done 2026-10-07

- Rama `feature/F-036-casado-contra-recursos` · rigor critico · sdd=true ·
  APPROVED del reviewer en la pasada 2 (`progress/review_F-036.md`; la 1 pidió
  los comandos exactos de M2/M3 y despliegue).
- Petición: el casado de sv3 debe ir contra la lista de recursos de la empresa
  del parte, no contra empleados; DNI del recurso y, si falta, el de su ficha.
- Entregado (sv3 + una condición en sv5): casado DNI → alias → nombre contra
  recursos persona (`res.cla = 1`) de alta en la empresa del parte; DNI guardado
  `emp.dni` y si falta `res.cif` (se busca por ambos); respaldo F-030 retirado;
  R6 (decisión A del humano): DNI conocido sin recurso persona ⇒ sin casar
  (`dni_sin_recurso`) y a Conciliar; sv5 `recursos_por_dni` exige `cla = 1`; nueva
  entrada en la lista cerrada de CLAUDE.md con guardián; herramienta de impacto
  de solo lectura (no ejecutada contra producción). No se re-casa lo ingerido.
- Verificado: init.sh en verde, cobertura 99,7 % (314/315), mutación completa
  0 supervivientes (110 mutantes), sv3 928 passed.
- Pendiente: M1 (impacto, solo lectura, la autoriza el humano), desplegar sv3 y
  sv5 (junto con sv4 de F-035) y M2/M3.

## F-035 · Portal: elegir trabajador entre recursos persona por empresa — done 2026-10-07

- Rama `feature/F-035-selector-recursos-por-empresa` · rigor estandar · sdd=true ·
  APPROVED del reviewer en la pasada 2 (`progress/review_F-035.md`; la 1 cazó un
  ReferenceError en el combo de «Nuevo parte»).
- Origen: los selectores tiraban de empleados y no ofrecían a quien solo tiene
  recurso (caso F-030, Porsan).
- Entregado (solo sv4 + CLAUDE.md, ARCHITECTURE.md y guardián raíz): Conciliar,
  parte nuevo, añadir línea y cambio de trabajador en detalle de obra ofrecen
  recursos persona (`res.cla = 1`) de alta, con selector de empresa (bloqueado a
  la de la obra cuando hay obra) y, en detalle de obra, solo los de su empresa;
  DNI guardado `emp.dni` y, si falta, `res.cif`; sin DNI no se ofrecen. Ruta nueva
  `/api/sigrid/recursos` (añadida a la lista del guardián F-016). Método
  `recurso_manual` vía `_METODOS_CASADO_SIN_FICHA` (desviación aceptada).
- Verificado: init.sh en verde, sv4 1774 passed, cobertura 97,0 % (194/200),
  mutación muestreada con supervivientes analizados y los 5 nuevos muertos.
- Pendiente: T9 manual (solo lectura) y desplegar sv4 junto con F-036.

## F-039 · Portal: nombre de empresa en vez de «empresa N» en combos y Conciliar — done 2026-10-08

- Rama `feature/F-039-nombre-empresa-en-combos` · rigor estandar · sdd=true ·
  APPROVED del reviewer en la pasada 2 (`progress/review_F-039.md`; la 1 pidió
  solo el procedimiento exacto de M1 en `current.md`).
- Entregado (solo sv4): cada item con `empresa` de las APIs de obras, empleados,
  recursos y búsqueda de Conciliar lleva `empresa_nombre` calculado con
  `empresas.py`; `app.js` pinta « · Ruesma»/« · Porsan» y «Empresa N» solo si no
  hay nombre; el dict no se copia a JS. R12 enmendada (opción A del humano):
  dos tests ajenos (F-015 r26, F-023 r40) esperan además `empresa_nombre`.
- Verificado: init.sh en verde; tests de F-039 ejecutan el JS con node.
- Pendiente: desplegar sv4 y M1 manual (humano).

## F-040 · Recursos sin DNI: proponer por nombre y aprender el alias por recurso — done 2026-10-08

- Rama `feature/F-040-recursos-sin-dni-por-nombre` · rigor critico · sdd=true ·
  APPROVED del reviewer en la pasada 2 (`progress/review_F-040.md`; la 1 pidió
  los comandos exactos de T15/M2/M3 e integrar dev). Bloqueada una vez en T4 y
  desbloqueada con la opción A (tres tests de F-023 adaptados).
- Petición: si no hay DNI en el parte ni en el recurso ni en su ficha, proponer
  por nombre (Iván y Juan Gaviño, Porsan MO/0032 y MO/0033, no salían).
- Entregado: sv3 da identidad de persona a quien no tiene DNI (ficha o recurso),
  compite por nombre y, si gana un recurso sin DNI, PROPONE (`nombre_sin_dni`,
  a Conciliar; nunca casa solo); alias con `recurso_ide` (empleado_ide nullable,
  DDL al arrancar en las dos copias de orm_models.py); sv4 ofrece recursos sin
  DNI marcados «sin DNI» y aprende el alias contra el recurso. sv5 sin cambios
  (DA3 del humano). Lo ingerido no se re-casa.
- Verificado: init.sh en verde, mutación completa 40/40, 0 supervivientes.
- Pendiente: medición M1 (solo lectura, la autoriza el humano), desplegar sv3 y
  sv4 (con F-039) y M2/M3.
