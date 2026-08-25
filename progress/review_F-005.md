<!-- progress/review_F-005.md -->
# Review F-005 · Retirar `graphkey_nobom.json` y constancia de `GRAPH_KEY` en KV

**Pasada 2 · revisión incremental desde `a0a084b`** (delta `a0a084b..HEAD`,
HEAD `14c8aaa`). La pasada 1 fue **completa** sobre `dev...HEAD` y su resultado
queda resumido abajo; lo aprobado entonces no se relee, salvo lo que el delta
toca (`README.md`, `infra/README_partes.md`, los dos informes). `init.sh` y la
suite se ejecutan **enteros** en las dos pasadas.

## Veredicto: APPROVED

Los dos cambios que exigí están hechos y contrastados otra vez contra los
scripts, no contra el informe. El implementer además arrastró la corrección a
las tablas A2/A3 de su propio informe, donde las dos frases falsas se repetían.

## Nivel de rigor: `documental` (declarado en `harness/features.json`)

Exige C1–C3, C3 bis y C5. **Fase RED, cobertura y mutación son N/A POR NIVEL**
(`harness/rigor.json` → `niveles.documental`: los tres a `false`), no por
omisión ni por herramienta no instalada: el diff no tiene una sola línea de
código ejecutable (Markdown/JSON y un borrado de fichero no versionado), así
que no hay nada que cubrir ni que mutar. `init.sh` imprime el motivo, no un N/A
a secas: `PUERTA COBERTURA: N/A (F-005 es de nivel documental...)`. **C4** es
N/A por la misma vía: `CHECKPOINTS.md` no lo exige en `documental`.

## `bash harness/init.sh`: VERDE (pasadas 1 y 2)

`ENTORNO LISTO`, arnés v1.7.3, **402 pasados / 1 saltado**, rama correcta,
`BACKLOG.md` al día. La puerta de tamaño estuvo en KO entre medias **por este
informe** (151/140), no por el trabajo del implementer: recortado aquí. Avisos
preexistentes y ajenos: ruff 496 (mismo número antes y después), sv1/sv2/infra
sin tests, F-014 `blocked`.

## Criterios de aceptación

| # | Estado | Verificación independiente del reviewer |
|---|---|---|
| A1 | **[x]** | `infra/graphkey_nobom.json` no existe; `git log --all -- <ruta>` vacío **y** barrido de `git ls-tree -r` sobre todos los commits alcanzables: el nombre no aparece en ningún árbol de la historia. `.gitignore:15` lo cubre (`git check-ignore -v`). Sin reserva ya: tras el borrado del zip por el humano, `find . -iname 'graphkey*'` y `*.zip` no devuelven nada en el árbol. |
| A2 | **[x]** | Ninguna mención residual a `graphkey_nobom.json` como fichero del despliegue en todo el árbol (solo `.gitignore`, `BACKLOG.md`, el histórico de `infra/README_partes.md:75` y `progress/`). Exactitud corregida en `ad770be`. |
| A3 | **[x]** | Las seis afirmaciones del documento contrastadas línea a línea contra los scripts (tabla abajo). La única falsa, corregida en `861c0d1`. |
| A4 | **[x]** | `progress/current.md` §F-005 con las dos fechas (2026-08-20 los tres servicios, 2026-08-25 el secreto habilitado en KV) y la naturaleza solo-lectura. Es constancia de una comprobación del implementer contra Azure; no la repito contra Azure (sesión sin login, y la feature no lo exige). |
| A5 | **[x]** | Verde. Secretos: barrido propio sobre el diff completo y sobre el delta, cero hallazgos (abajo). |

### A3 contrastado contra los scripts

| Afirmación de `infra/README_partes.md` | Evidencia comprobada | ¿Cierta? |
|---|---|---|
| El KV es la única fuente; no hay fichero de secretos que tener al lado | ningún script de `infra/` lee `graphkey_nobom.json` ni ningún fichero de secretos | **SÍ** |
| `add_secrets_partes.ps1` los pide por consola con `Read-Host -AsSecureString` y los sube con `az keyvault secret set`, sin escribir en disco ni imprimir | `add_secrets_partes.ps1:26-32` | **SÍ** |
| el fichero versionado solo contiene los *nombres*; el valor solo existe en memoria durante la ejecución | `$secretos` es una tabla nombre→descripción; el valor vive en `$val` y no se persiste | **SÍ** (redacción de `861c0d1`; la anterior era falsa) |
| sv1, sv3 y sv4 montan `GRAPH_KEY=secretref:graph-key` | `create_sv1_poller.ps1:44,49`, `create_capps_partes.ps1:63,73`, `create_sv4_front.ps1:41,62` | **SÍ** |
| el secreto de la Container App es un `keyvaultref` resuelto con la MI `id-partes-dev` | los tres definen `KvRef` = `keyvaultref:$KV_URI/secrets/<n>,identityref:$MI_ID`; `$MI_ID` sale de `00_capps_vars_partes.ps1:14` sobre `$MI = "id-partes-dev"` | **SÍ** |
| `PG-PASSWORD` la deja `fase1` (y `README.md` lo mismo desde `ad770be`) | `fase1_infra_partes.ps1:151` la escribe en el KV; `add_secrets_partes.ps1` no la pide | **SÍ** |

### Barrido de datos sensibles (lo ejecuté yo, sobre diffs, no sobre el árbol)

Patrones aplicados a `git diff dev...HEAD` (pasada 1) y a `a0a084b..HEAD`
(pasada 2): GUID `[0-9a-f]{8}-...-[0-9a-f]{12}` (tenant/client/suscripción),
`client_secret|clientsecret|password *=|pwd=|BEGIN .*PRIVATE|api[-_]?key *[=:]|
AccountKey`, `kv-partes-[a-z0-9]+|pt7m3`, y cadenas añadidas de ≥32 caracteres.

- **Cero GUIDs, cero valores de secreto** en los ocho commits. Las únicas
  coincidencias de `client_secret` son la palabra en prosa (describir H1 y el
  formato del JSON), nunca un valor. El delta de la pasada 2 sale limpio
  también de nombre de KV. Igual en `azure-apps` (`ff22735`, `65430cd`).
- **Nombre del Key Vault**: la pasada 1 añadió `pt7m3` en un sitio
  (`progress/impl_F-005.md`, H2) y `kv-partes-<suffix>` como plantilla. **No es
  exposición nueva**: `pt7m3` ya estaba en `dev` en 12+ ficheros versionados
  —`infra/00_vars_partes.ps1:19` (necesario para desplegar),
  `docs/ARCHITECTURE.md:183`, `docs/referencia/partes-proyecto.md`, specs de
  F-003—. **Acepto A5**: el nombre de un KV no es una credencial (el acceso va
  por RBAC + identidad gestionada), A5 lo entrecomilla como caso aparte, y H2
  lo declara en vez de esconderlo. Qué hacer con `00_vars_partes.ps1:19` es
  decisión del humano y toca despliegue: fuera de F-005.

### H1 — la copia dentro del zip: verificada y RESUELTA

En la pasada 1 confirmé el hecho sin imprimir valores: `infra/partes-infra.zip`
(33.017 B, 32 entradas) contenía `graphkey_nobom.json` con `tenant_id`,
`client_id` y un `client_secret` **de 40 caracteres, no vacío**; nunca
versionado (`git log --all` vacío, `.gitignore:13 *.zip`). No lo conté contra
A1 —el alcance lo fijó el humano— y el implementer hizo lo correcto: lo
comprobó sin filtrarlo, no borró fuera de alcance y lo elevó con el comando
exacto. El humano lo borró el 2026-08-25 y lo he verificado: **ni rastro de
`graphkey*` ni de zips**.

## Checkpoints

- **C1** [x] `init.sh` exit 0; los siete ficheros obligatorios existen.
- **C2** [x] Una sola `in_progress` (F-005); rama correcta; F-015/F-016 con
  resumen en `history.md:245,307`. `current.md` arrastra sesiones anteriores
  (752 líneas): **preexistente en `dev`**, no imputable a F-005, pero conviene
  purgarlo al cerrar.
- **C3** [x] Sin código: hexagonal y «primera línea con ruta» aplican solo a
  los `.md`, que la cumplen. Sin prints, sin dependencias, **sin secretos
  hardcodeados** (barrido arriba).
- **C3 bis** **N/A justificado**: no toca `docs/referencia/`. Aun así ejecuté
  el barrido de datos sensibles que exige, con los patrones listados arriba.
- **C4** **N/A por nivel `documental`** (ver arriba). Las verificaciones MANUAL
  sí están listadas: H1 (**hecha**, zip borrado) y H2 queda en
  `impl_F-005.md` como decisión del humano.
- **C4 bis** [x] con N/A justificados: `rigor` declarado y válido; **fase RED,
  cobertura y mutación N/A POR NIVEL** (`rigor.json` los pone a `false` en
  `documental`); sin campaña, RM1–RM6 y los controles de tiempo, workers y
  «CAMPAÑA NO VÁLIDA» son N/A por ausencia legítima de campaña, no por omitir
  la herramienta. Sección **«Evidencias»** presente con los cuatro números
  (402 pasados / 1 saltado, cobertura N/A con motivo, mutación N/A, 53,27 s).
- **C4 ter** **N/A**: no existe `harness/rutas_sensibles.json` (caso
  mayoritario previsto por `CHECKPOINTS.md`; `init.sh` no señala rutas).
- **C5** [x] `tasks.md` N/A (`sdd:false`); los ocho commits cumplen el formato
  mínimo `F-005: ...` / `F-005 Tn: ...` / `F-005 rev-1: ...`; árbol limpio;
  `features.json` refleja `in_progress` (el líder lo pasa a `done`).

## Cambios de la ronda 1: los dos cerrados

| # | Frase falsa | Arreglo verificado |
|---|---|---|
| 1 | `README.md` atribuía `PG-PASSWORD` a `add_secrets_partes.ps1`, contradiciendo a `infra/README_partes.md:52` de la misma feature | `ad770be`: la lista separa los cuatro que carga `add_secrets` de la que deja `fase1_infra_partes.ps1` al provisionar. Contrastado contra `fase1_infra_partes.ps1:151` y contra la tabla `$secretos`. Propagado a `azure-apps/partes.md` en `65430cd`, como manda la regla del ecosistema |
| 2 | `infra/README_partes.md`: «el script solo conoce el *nombre* del secreto, nunca su valor» | `861c0d1`: ahora dice que el **fichero versionado** solo lleva los nombres y que el valor solo existe **en memoria** durante la ejecución. Cierto y comprobable |

## Observaciones (NO bloquean, no las arregléis en F-005)

- `az keyvault secret set --value $val` deja el secreto en la línea de comandos
  del proceso (visible en el listado de procesos de Windows). Deuda
  preexistente del script; se arreglaría con `--file` o con `Az.KeyVault`.
- `impl_F-005.md` cierra con «Portero: verde» mientras la puerta de tamaño
  estaba roja por mi informe; `current.md` documenta el KO con su causa exacta
  en la misma ronda, y con este recorte ya es verde de verdad. Sin acción.
  `azure-apps` tiene `postventa_incidencias.md` sin trackear: de otro trabajo.

## Automejora propuesta (no aplicada)

`CHECKPOINTS.md` no obliga a **contrastar contra el código las afirmaciones de
un documento**, que es justo donde se cae el nivel `documental`: aquí todo pasó
en verde y los dos defectos eran frases falsas. Propongo añadir a C3, para ese
nivel: «cada afirmación sobre cómo se ejecuta algo cita el fichero y la línea
que la respalda, y el reviewer la comprueba». Es la tabla de A3 hecha a mano;
sin checkbox depende de que se le ocurra. Aprobado por el humano, se porta a
`arnes-base` en el mismo trabajo.
