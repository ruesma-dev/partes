<!-- progress/impl_F-005.md -->
# F-005 · Retirar `graphkey_nobom.json` y dejar constancia de `GRAPH_KEY` en Key Vault

Rama `feature/F-005-graphkey-keyvault`. Feature **sin spec** (`sdd: false`),
rigor **`documental`**: se trabaja contra los cinco criterios `acceptance` de
la ficha. **No se ha tocado ni una línea de código de producción.**

Detalle largo de la comprobación contra Azure: `progress/current.md`, sección
«F-005 · GRAPH_KEY en Key Vault: constancia de la comprobación (2026-08-25)».

## Qué cambió

| Fichero | Qué se hizo |
|---|---|
| `infra/graphkey_nobom.json` | **borrado del disco**. No versionado, nunca en git. |
| `CLAUDE.md:95` | ya no lo presenta como el fichero con los valores reales |
| `README.md:17` | ídem, y enumera qué secretos viven en el Key Vault |
| `infra/README_partes.md` | sección nueva «Ningún script lee secretos de ficheros en disco» |
| `progress/current.md` | constancia de la verificación en Azure + hallazgo del zip |
| `harness/features.json` | la ficha nombraba el Key Vault en claro; ahora usa `$KV` |
| `BACKLOG.md` | regenerado con `harness/backlog.py` (init.sh lo valida) |
| `azure-apps/partes.md` §5.5 | misma corrección, commit `ff22735` en ese repo |

Commits: `dfac173` (T2), `2b7cbfa` (T3), `c7831d4` (T4+T5), `a0a084b` (este
informe) y los dos de la ronda 1 —`ad770be`, `861c0d1`—; en `azure-apps`,
`ff22735` y `65430cd`. Ningún `push`, ningún PR.

## Criterios de aceptación, uno a uno

### A1 — el fichero fuera del árbol, `.gitignore` intacto — CUMPLIDO

```
$ rm -f infra/graphkey_nobom.json
$ ls infra/graphkey_nobom.json
ls: cannot access 'infra/graphkey_nobom.json': No such file or directory
$ grep -n graphkey_nobom .gitignore
15:infra/graphkey_nobom.json
$ git status --porcelain          # no aparece: nunca estuvo trazado
 M BACKLOG.md
$ git log --all --oneline -- infra/graphkey_nobom.json
                                  # (vacío: jamás entró en git)
$ find . -name "graphkey*" -not -path "./.git/*"
                                  # (vacío)
```

Había una segunda copia dentro de un zip (H1), ya resuelta: el árbol no
contiene hoy **ningún** rastro de `graphkey*` ni el zip.

### A2 — `CLAUDE.md` y `README.md` — CUMPLIDO

Las dos menciones decían, en esencia, «los valores reales van en
`infra/*.local.ps1` y `graphkey_nobom.json`». Ahora separan las dos cosas:

- **Identificadores de suscripción y tenant** → `infra/*.local.ps1`, que sigue
  sin versionarse. Eso no cambia.
- **Secretos de la app** → **no viven en ningún fichero**: Key Vault (`$KV`),
  consumidos por `secretref` + identidad gestionada. `GRAPH-KEY`,
  `SIGRID-API-FUNCTION-KEY`, `GEMINI-API-KEY` y `SESAME-API-KEY` los carga
  `infra/add_secrets_partes.ps1`; `PG-PASSWORD` la deja
  `infra/fase1_infra_partes.ps1` (corregido en la ronda 1: ver abajo).

### A3 — `infra/README_partes.md` — CUMPLIDO

Sección nueva bajo «Secretos», con cuatro afirmaciones **verificadas contra
los scripts antes de escribirlas**, no asumidas:

| Afirmación | Evidencia |
|---|---|
| `add_secrets_partes.ps1` pide por consola y no escribe el valor en disco | `Read-Host -AsSecureString` + `az keyvault secret set`; el fichero versionado solo lleva los *nombres* (corregido en la ronda 1: ver abajo) |
| sv1 monta `GRAPH_KEY=secretref:graph-key` | `create_sv1_poller.ps1:44,49` |
| sv3 (vía el creador común) ídem | `create_capps_partes.ps1:63,73` |
| sv4 ídem | `create_sv4_front.ps1:41,62` |
| el secreto de la Container App es una referencia, no una copia | los tres definen `KvRef` = `keyvaultref:$KV_URI/secrets/<n>,identityref:$MI_ID` |

Y deja el histórico: el fichero existió, se usó para la carga manual inicial,
ningún script lo leía, ya está borrado, sigue en `.gitignore` por si alguien lo
regenera.

### A4 — constancia en `progress/` con su fecha — CUMPLIDO

En `progress/current.md`, con las dos fechas separadas:

| Fecha | Comprobado (solo lectura, sesión de `pgris@ruesma.es`) | Resultado |
|---|---|---|
| 2026-08-20 | `ca-sv1-poller`, `ca-sv3-persistencia`, `ca-sv4-front` | `GRAPH_KEY` como `secretref:graph-key`; el secreto de la Container App es un `keyvaultref` (`keyVaultUrl` informado), **no una copia** |
| 2026-08-25 | secreto `GRAPH-KEY` en el Key Vault de `rg-partes-dev` | existe, **habilitado**; creado y actualizado `2026-06-22T13:59:10+00:00` |

sv5 no usa Graph. El objetivo original de la feature —sacar la credencial de
las variables de entorno en claro— **ya estaba cumplido de hecho** antes de
abrirla.

### A5 — portero en verde y ningún secreto en el repo — CUMPLIDO EN PARTE

Verde, sí (ver «Evidencias»). Sobre los secretos, con precisión:

- **Ningún valor secreto** (`client_secret`, claves, contraseñas) entra en el
  repositorio con este trabajo. El contenido de `graphkey_nobom.json` no se ha
  impreso en ningún fichero, commit ni mensaje.
- **`tenant_id` y `client_id`**: no aparecen en nada de lo escrito.
- **Nombre del Key Vault**: lo he sacado de la ficha (`features.json` →
  `$KV`), pero **no puedo declarar el repositorio libre de él**, y conviene no
  fingir lo contrario. Ver H2.

## Hallazgos para el humano

### H1 — segunda copia del secreto en disco — **RESUELTO el 2026-08-25**

`infra/partes-infra.zip` (33 KB, 2026-07-26, **no versionado**, cubierto por la
regla `*.zip`) **contenía dentro `graphkey_nobom.json`**, con `tenant_id`,
`client_id` y un `client_secret` no vacío. Comprobado en su día **sin imprimir
los valores**:

```
$ python -c "import zipfile,json; z=zipfile.ZipFile('infra/partes-infra.zip'); \
    d=json.loads(z.read('graphkey_nobom.json').decode('utf-8-sig')); \
    print('claves:',sorted(d.keys())); print('secret no vacio:',bool(d.get('client_secret')))"
claves: ['client_id', 'client_secret', 'tenant_id']
secret no vacio: True
```

No lo borré yo: A1 nombraba solo `infra/graphkey_nobom.json` y borrar fuera
del alcance declarado no me tocaba. **El humano decidió borrar el zip entero
el 2026-08-25 y ya está hecho**, así que el objetivo real de A1 —que la
credencial de Graph no esté en claro en el disco— sí está conseguido:

```
$ find . -name "graphkey*" -o -name "partes-infra.zip"
                                  # (vacío)
```

Tampoco llegó nunca a git (`git log --all -- infra/partes-infra.zip`, vacío).

### H2 — el nombre del Key Vault ya es vocabulario del repo

`infra/00_vars_partes.ps1:19` declara `$Global:SUFFIX = "pt7m3"` en un fichero
**versionado y necesario para desplegar**, del que `$KV = "kv-partes-$SUFFIX"`
sale por construcción. Además el nombre completo aparece en
`docs/ARCHITECTURE.md:183`, `docs/referencia/partes-proyecto.md` (3 sitios),
specs de F-002/F-003 e informes de progreso cerrados.

O sea: mi redacción de la ficha es **coherencia con la instrucción recibida,
no protección real**. Reescribir specs cerradas e informes históricos queda
fuera de alcance y además falsearía el registro. Si el humano considera que el
nombre no debe estar en el repo, la decisión de fondo es qué hacer con
`00_vars_partes.ps1`, y eso sí toca despliegue.

### H3 — rotación de la credencial de Graph (fuera de alcance, apuntado)

Excluida por decisión del humano del 2026-08-25 y **no implementada ni
propuesta como tarea del arnés** en ningún documento. Solo queda dicho que es
pendiente suyo. H1 refuerza el argumento: ese `client_secret` estuvo en claro
en disco desde el `2026-06-22` hasta el `2026-08-25`.

## Fase RED

**No aplica.** Nivel `documental` (`harness/rigor.json`) y, sobre todo, esta
feature **no escribe código**: no hay requisito que un test pueda hacer
fallar. Los 402 tests que pasan son los preexistentes del monorepo, aquí solo
como red de seguridad de no-regresión.

## Verificaciones MANUAL pendientes

1. ~~Decidir sobre H1~~ — **hecho**: zip borrado por el humano el 2026-08-25.
2. **Decidir sobre H2** (el sufijo en `00_vars_partes.ps1`).
3. Rotación de `GRAPH-KEY` (H3), cuando el humano quiera.

Nada de esto requiere redespliegue: no ha cambiado ningún manifiesto ni
ninguna variable de entorno de ningún servicio.

## Evidencias

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** | **402 pasados, 1 saltado**, 0 fallos (suite del monorepo). sv3, sv4 y sv5 en verde por caché de árbol sin cambios. |
| **Tiempo de la suite** | **53,27 s** (`402 passed, 1 skipped in 53.27s`) |
| **Cobertura de líneas cambiadas** | **N/A por diseño**: `PUERTA COBERTURA: N/A (F-005 es de nivel documental: no exige cobertura)`. Además el diff no contiene líneas de código: son 6 ficheros Markdown/JSON y un borrado. |
| **Mutantes generados / supervivientes** | **N/A**: el nivel `documental` no exige campaña, y no habría nada que mutar (cero código tocado). No se ha lanzado. |
| **Puerta de tamaño** | `PUERTA TAMAÑO: F-005 dentro de los topes` |
| **`bash harness/init.sh`** | **VERDE** — `ENTORNO LISTO. Puedes trabajar.`, arnés v1.7.3, rama `feature/F-005-graphkey-keyvault` |

Avisos del portero, todos **preexistentes y ajenos a F-005**: `ruff` 496
(mismo número antes y después), sv1/sv2/infra sin directorio de tests, y
F-014 en `blocked`.

## Ronda de revisión 1 (CHANGES_REQUESTED → corregido)

El reviewer (`progress/review_F-005.md`) dio por buena toda la parte de
seguridad y señaló **dos frases falsas**, las dos del tipo que esta feature
existía para eliminar: documentación que describe un flujo que no existe.
Corregidas y **verificadas contra los scripts**, no contra mi memoria:

| # | Frase falsa | Qué es cierto | Arreglo |
|---|---|---|---|
| 1 | `README.md` metía `PG-PASSWORD` entre los secretos que carga `add_secrets_partes.ps1` | su tabla `$secretos` no la incluye, y su cabecera dice «PG-PASSWORD ya la dejo ese script»; la deja `fase1_infra_partes.ps1:151` | la lista separa ahora los cuatro de `add_secrets` de la que deja `fase1`. Commit `ad770be` |
| 2 | `infra/README_partes.md`: «el script solo conoce el *nombre* del secreto, nunca su valor» | el valor pasa por `$val` y viaja como argumento de `az keyvault secret set --value` | redactado como lo que sí es cierto: el **fichero versionado** solo lleva los nombres, y el valor solo existe **en memoria** durante la ejecución, sin tocar disco. Commit `861c0d1` |

El punto 1 contradecía además a `infra/README_partes.md:52`, editado en esta
misma feature: dos documentos míos decían cosas distintas. El mismo matiz, más
leve, estaba en `azure-apps/partes.md:494`; corregido en su repositorio, commit
`65430cd`.

**No se ha tocado nada más.** Las dos observaciones que el reviewer marcó como
«no bloquean» se dejan como están: el `--value` en la línea de comandos de
`az` es deuda preexistente del script, ajena a esta feature de documentación.

Portero tras las correcciones: **verde**, `402 passed, 1 skipped`.
