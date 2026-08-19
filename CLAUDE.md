<!-- CLAUDE.md -->
# Arnés · partes (monorepo del pipeline de partes de trabajo)

Eres parte de un sistema de agentes (arnés) de este repositorio. Tu punto de
entrada es el rol **líder**: lee `.claude/agents/leader.md` y actúa según su
protocolo. Todo en español.

## Autorización permanente de subagentes

El humano **autoriza y espera** que lances los subagentes de
`.claude/agents/` (`spec-author`, `implementer`, `reviewer`) mediante la
herramienta Agent. No hace falta pedir permiso feature a feature: esta línea
es esa petición explícita, dada de antemano y para todas las sesiones.

Si el entorno te impide lanzarlos (por ejemplo, una sesión hija de Claude
Code, detectable con `CLAUDE_CODE_CHILD_SESSION=1`, arranca restringida),
**dilo en el primer mensaje** en vez de asumir el trabajo en silencio: el
humano decidirá si relanza la sesión desde una terminal limpia o si acepta
que trabajes sin delegar. Si trabajas sin delegar, mantén igualmente el
rastro documental en `progress/`.

Esta autorización cubre **usar la herramienta Agent**, no la aprobación del
plan: la PARADA 1 de la sección siguiente sigue siendo obligatoria. Lanzar un
subagente sin permiso, sí; implementar sin haber enseñado la propuesta, no.

## Ritmo de trabajo con el humano (obligatorio)

Dos paradas fijas en todo trabajo, por pequeño que sea:

1. **Antes de implementar.** Cuando estudiemos una feature o un cambio,
   primero piensa cómo hacerlo y **explica la propuesta**: qué ficheros se
   tocan, en qué orden, qué decisiones se toman, qué riesgos hay y qué queda
   fuera. Luego **espera confirmación del humano antes de escribir nada**.
   Aplica también a los cambios pequeños y a los que el propio humano haya
   pedido: pedir confirmación no es dudar de la petición, es enseñar el plan
   antes de gastar trabajo en la dirección equivocada.
2. **Después de implementar.** Entrega un **resumen de lo hecho**: qué
   cambió, qué se verificó (con el resultado real, no «debería funcionar»),
   qué quedó fuera y qué falta para cerrar. El detalle largo vive en
   `progress/`; por el chat va solo el resumen.

No requieren confirmación previa las acciones de **solo lectura** (ejecutar
`bash harness/init.sh`, leer ficheros, buscar en el árbol) ni aquello que el
humano haya pedido explícitamente «sin preguntar» en esa misma petición.

Si el humano confirma una propuesta y luego el trabajo revela que la
propuesta era incorrecta o incompleta, **para y vuelve a proponer**: la
confirmación cubre el plan que se enseñó, no lo que apareció después.

## Protocolo obligatorio (antes de cualquier trabajo)

1. Ejecuta `bash harness/init.sh`. Si falla, **PARA** y reporta el motivo.
   No trabajes nunca sobre un entorno en rojo.
2. Lee `progress/current.md`. Si hay trabajo a medias o una feature
   `blocked` de una sesión anterior, retómala antes de empezar nada nuevo.
3. Lee `harness/features.json` y localiza la primera tarea no terminada
   (por orden de prioridad: `blocked` > `in_progress` > `spec_ready` >
   `pending`). Máximo UNA feature `in_progress` a la vez (init.sh lo valida).
4. Sigue el flujo SDD descrito en `.claude/agents/leader.md`.

## Mapa del repositorio (no leas todo el proyecto, ve a lo que necesites)

Monorepo de 5 servicios + infra. El flujo del pipeline es:
**sv1 → `q-extraccion` → sv2 → `q-persistencia` → sv3**; sv4 es el portal
humano y llama a **sv5 por HTTP interno** para registrar en Sigrid. Detalle
completo en `docs/ARCHITECTURE.md`; el documento maestro del dominio es
`docs/referencia/partes-proyecto.md`.

- `services/partes-email/` (**sv1**) — poller del buzón `partes@ruesma.es`
  vía Graph; guarda el PDF y publica `q-extraccion`. Python puro (sin API).
- `services/partes-api/` (**sv2**) — worker KEDA de extracción IA (Gemini,
  prompt YAML + esquema). Pese al nombre, NO es «la API del sistema».
  Publica `q-persistencia`.
- `services/partes-persistencia/` (**sv3**) — worker KEDA de conciliación
  contra los maestros de Sigrid (obra, empleado por DNI, recurso, partida,
  tipo de hora), cómputo de extras por exceso de jornada, PostgreSQL
  `partes` y archivo del PDF en SharePoint.
- `services/partes-front/` (**sv4**) — portal de revisión/aprobación
  (FastAPI + Jinja2 + JS vanilla, Easy Auth Entra). Aprueba → llama a sv5.
- `services/partes-transfer/` (**sv5**) — escritura en Sigrid vía
  sigrid-api: parte mensual `hmo` + líneas `hmores` con synckey. ÚNICO
  servicio con credencial de escritura; 1 réplica fija.
- `infra/` — scripts PowerShell de provisión/despliegue y
  `manifests/svN/`. Los `infra/*.local.ps1` y `graphkey_nobom.json` (no
  versionados) llevan los valores reales; los versionados van redactados.
- Estructura interna de cada servicio: hexagonal (`domain/`,
  `application/`, `infrastructure/`, `interface_adapters/`, `config/`).
- `tests/` (raíz) — tests del monorepo como conjunto; los de cada servicio
  viven en su carpeta. Los unit tests NO tocan red ni BBDD.
- `specs/` — especificaciones SDD (una carpeta por feature).
- `progress/` — memoria externa del arnés (`current.md`, `history.md`,
  informes `impl_*.md` / `review_*.md` / `explore_*.md` por subagente).
- `docs/` — `ARCHITECTURE.md`, `CONVENTIONS.md`.
- `docs/referencia/` — documentación de negocio y de sistemas origen que
  llega de fuera, siempre en Markdown. Consúltala cuando la pregunta sea
  «por qué el código hace esto» y la respuesta no esté en el código. Ver su
  `README.md`.
- `CHECKPOINTS.md` — criterios objetivos de estado final; el reviewer los
  recorre antes de cerrar cualquier feature.
- `harness/ARNES_VERSION.md` — qué versión del arnés genérico lleva este
  repositorio. Lo escribe el instalador; no lo edites a mano.
- `infra/` — scripts de despliegue (si aplica).

## Documentos que llegan de fuera (PDF y ofimática)

Cuando el humano pase un PDF —o un `.docx`, `.xlsx`, `.pptx`— conviértelo a
Markdown y guárdalo en `docs/referencia/` antes de trabajar con él. El
original NO se versiona: al repositorio entra solo el Markdown.

- La conversión se hace **siempre con la herramienta MCP `markitdown`**, no
  leyendo el documento por tu cuenta. Única excepción: que el humano lo
  indique explícitamente en esa petición.
- Si `markitdown` no está conectada, **PARA y dilo**. No improvises otra vía
  de conversión: el resultado saldría distinto según quién lo convierta y el
  Markdown va a quedar versionado en git.
- Nombra el fichero según la convención de `docs/referencia/README.md` y
  ponle la cabecera con origen y fecha del documento.
- Si el documento trae datos sensibles (precios de proveedor, datos
  personales, credenciales), **no lo conviertas sin preguntar**: acabaría
  versionado en git.

## Reglas duras (no negociables)

- PROHIBIDO marcar una feature como `done` sin que `bash harness/init.sh`
  termine en verde (incluye tests) y sin veredicto APROBADO del reviewer
  contra `CHECKPOINTS.md`.
- PROHIBIDO tocar `.env` o subirlo a git. Los secretos no se escriben en
  ningún fichero del repo ni en specs ni en progress.
- Sigrid (el ERP) SOLO se toca a través de `sigrid-api`, nunca por SQL
  directo. Escribir en Sigrid es exclusivo de sv5, contra la base `ruesma`
  (la réplica `ruesma_rep` no admite escritura). Desde local, toda prueba
  de escritura va en modo pruebas (`OBRA_PRUEBAS_FORZAR=true`, obra 0404,
  marca `PRUEBA-IA`) y se limpia con `prueba_escritura_sigrid.py`.
- El PostgreSQL `psql-albaranes-rs9k2` es COMPARTIDO con otros proyectos:
  prohibido tocar nada a nivel de servidor; solo la base `partes`.
- Desplegar en Azure (`redeploy_partes.ps1`) lo pide el humano; los agentes
  no lo lanzan por iniciativa propia.
- Cada feature se desarrolla en su rama `feature/F-XXX-slug`. Nunca commits
  directos a `dev` ni a `main`.
- ANTI TELÉFONO-DESCOMPUESTO: por el chat no circula código ni informes
  largos. Cada subagente escribe su resultado en `progress/` y responde con
  UNA línea de referencia (`done -> progress/impl_F-XXX.md`). Si un
  subagente devuelve contenido largo por chat sin fichero, se rechaza.
- Si una herramienta falla de forma inesperada o la spec resulta ambigua:
  NO improvisar workarounds. Marcar la feature `blocked`, anotar el motivo
  en `progress/current.md` y parar.
- Los agentes ejecutan `bash harness/init.sh` tal cual, sin pipes, tail,
  variables ni decoración (la allowlist de permisos cubre el comando limpio).
- Convenciones de código: `docs/CONVENTIONS.md`. Arquitectura:
  `docs/ARCHITECTURE.md`. Léelos antes de diseñar o implementar.
- LÍMITE DE SERVICIO (adaptación monorepo): cada feature declara en su spec
  qué servicio(s) toca y por qué. La lógica NO se copia entre servicios; si
  dos la necesitan, se propone al humano dónde debe vivir. La única
  duplicación tolerada es esta lista cerrada:
  `infrastructure/database/orm_models.py` (sv3 y sv4), los clientes
  `infrastructure/sigrid/` y los clientes `infrastructure/sesame/`
  (sv3 y sv4, añadidos por F-003 con decisión expresa del humano el
  2026-08-15) y `application/services/jornada_resolver.py` (sv3 y sv4,
  duplicado de hecho desde F-003 y añadido a esta lista con decisión
  expresa del humano el 2026-08-19, al ampliarlo F-015 con la jornada
  del día; equivalencia comprobada por
  `tests/test_f015_r19_jornada_resolver_gemelo.py`). Solo crece con una
  decisión así; quien toque una copia cambia TODAS en la misma feature. Una responsabilidad nueva que no
  encaje en ningún servicio ⇒ `blocked` y se consulta.
- Los agentes NO hacen `git push` ni crean PRs salvo petición explícita del
  humano. Commits locales sí, según protocolo del implementer.

<!-- ==================== INICIO · ENTORNO DE RUESMA ==================== -->
<!-- Esta sección NO es del arnés: describe convenios de la organización    -->
<!-- Construcciones Ruesma. Si instalas el arnés fuera de ese entorno,      -->
<!-- BORRA el bloque entero, desde este comentario hasta el de cierre.      -->

## Convenios del entorno de Ruesma

### El ecosistema: `azure-apps/`

`C:\Users\pgris\PycharmProjects\azure-apps` es un repositorio git con un
documento por proyecto del ecosistema, explicando qué expone cada uno, qué
consume y qué se rompe si cambia.

**Consúltalo antes de diseñar nada que cruce la frontera del proyecto**: una
llamada a otro servicio, una base de datos compartida, un registro de
contenedores común.

Dos reglas: el documento de este proyecto **se actualiza cuando cambie lo que
exponemos o consumimos**, en el mismo trabajo y no después; y **no se
duplican aquí** los documentos de otros proyectos, se enlazan.

### El arnés genérico: `arnes-base`

Este arnés no nació aquí. Su versión genérica y reutilizable vive en
`C:\Users\pgris\PycharmProjects\arnes-base` (repositorio git versionado), y
desde ahí se instala y se actualiza en los demás repositorios. La versión
instalada consta en `harness/ARNES_VERSION.md`.

**Regla de propagación (obligatoria).** Si mejoras algo del arnés
—`CLAUDE.md`, `.claude/agents/`, `CHECKPOINTS.md`, `harness/init.sh`,
`specs/SPECS.md`, las convenciones— y esa mejora **vale para cualquier
proyecto**, la portas a `arnes-base` **en el mismo trabajo**, no después. Si
es específica de este proyecto, se queda aquí.

No es una recomendación: el 2026-08-08 se perdieron **cinco mejoras del arnés
en una sola tarde** porque `arnes-base` era una copia suelta sin versionar y
nadie la refrescó. Es la misma regla de propiedad que rige `azure-apps`.

<!-- ===================== FIN · ENTORNO DE RUESMA ====================== -->
