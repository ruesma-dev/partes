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
