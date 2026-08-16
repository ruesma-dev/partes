<!-- progress/review_F-003.md -->
# F-003 · Integración sesame-api: festivos y jornada reales — Review

**VEREDICTO FINAL: APPROVED** (2026-08-16, segunda pasada). El detalle está
en la sección **«Segunda pasada»** al final de este fichero; lo que sigue
inmediatamente es la primera pasada, que se conserva íntegra como registro.

---

## Primera pasada (2026-08-15)

**Veredicto: CHANGES_REQUESTED** (2026-08-15, rama
`feature/F-003-sesame-festivos-jornada`, 24 commits sobre `dev`).

> Aviso de calibración, para que el veredicto no se lea mal: la ingeniería
> de esta feature es **muy buena** y ha resistido toda la verificación
> independiente, incluida la parte que más se falsea (mutación y fase RED).
> Los cuatro puntos que la paran son pequeños y de arreglo corto — un
> import, dos números desactualizados y unos finales de línea — más una
> edición del `CLAUDE.md` que necesita el visto bueno explícito del humano.
> Ninguno es un fallo de corrección ni de seguridad.

## Nivel de rigor

`harness/features.json` declara **`rigor: "critico"`** para F-003. Puertas
exigidas: C1–C5 completos + tests trazables + **fase RED** + **cobertura**
de las líneas cambiadas ≥ 80 % + **campaña de mutación** con supervivientes
analizados + **cero supervivientes** salvo justificación escrita + las
verificaciones `MANUAL (humano)` listadas con su comando y su resultado.

## Verificación independiente (lo que he ejecutado yo, no lo que dice el informe)

### Portero y suites

`bash harness/init.sh` completo, sin `ARNES_SALTAR_SUITES`: **exit 0,
ENTORNO LISTO**. Como el portero trae caché de suites, he lanzado las tres
a mano:

| Suite | Resultado |
|---|---|
| `tests/` (raíz) | **6 passed** en 0,08 s |
| `services/partes-persistencia` (sv3) | **95 passed** en 1,22 s |
| `services/partes-front` (sv4) | **272 passed** en 14,63 s |

Total **373**, coincide con el informe. `PUERTA COBERTURA` en `[OK]`:
**94,5 % de 621 líneas cambiadas** (587/621, umbral 80 %).

### Mutación — recalculada de cero

No me he creído ningún número del informe. `harness.alcance` +
`harness.mutacion.generar_mutantes` (cálculo puro):

- **Alcance: 17 ficheros, 1537 líneas** — coincide **fichero a fichero**
  con la tabla de `progress/mutacion_F-003.md`.
- **Mutantes: 211** — coincide con el total declarado.
- **Muestreo de supervivientes** (5 de los 26): todos existen como mutantes
  reales, con el **mismo operador y el mismo texto original→mutado** que el
  informe. Verificados `calendario_provider.py:263` [comparacion],
  `parte_repository.py:1388` [entero], `app.py:1501` [comparacion],
  `app.py:1603` [logico] y `sesame_api_client.py:60` [booleano]. El informe
  no está escrito a mano.
- **El superviviente nº 26 muere de verdad.** El informe afirma que se cazó
  después de la pasada con un test nuevo. Lo he comprobado aplicando la
  mutación (`@dataclass(frozen=True)` → `frozen=False` en el cliente de
  sv3) y lanzando la suite: `1 failed` —
  `test_f003_r8_los_datos_del_cliente_son_inmutables[JornadaContrato-valores1-reducida]`.
  Quedan por tanto **25 supervivientes**, todos con análisis COMPLETADO y
  ninguno en `PENDIENTE`.
- **Prueba de control de la lección de F-002** (fichero del alcance con
  líneas pero 0 mutantes): los tres casos son
  `infrastructure/sesame/__init__.py` (sv3 y sv4, 1 línea de comentario) y
  `domain/ports/parte_repository.py` (5 líneas: un `import`, una firma de
  `Protocol`, un docstring y `...`). Mutados **ignorando el filtro de
  alcance, el fichero entero**, siguen dando **0 mutantes**: el cero es
  legítimo (no hay nada mutable), no un generador roto.

Los 25 supervivientes que quedan son aceptables como equivalentes: 10
dentro de argumentos de `logger.*`, 6 constantes de ajuste, 2 truncados a
255 sobre un motivo de 74 caracteres, 2 cortocircuitos que llegan al mismo
resultado, 2 guardas redundantes de TTL, 1 epsilon de coma flotante, 1
`include_in_schema` y 1 guarda de un WARNING. He revisado los análisis uno
a uno y ninguno cambia comportamiento observable.

### Fase RED — reproducida por mí, no leída

El informe trae trazas reales de T1–T16. Además he roto a propósito el
código de producción (con restauración posterior; **árbol limpio**,
`git status --porcelain` vacío) para comprobar que los tests de los
requisitos centrales de la ENMIENDA muerden de verdad:

| Sabotaje | Resultado |
|---|---|
| `app.py`: anular la guarda `if degradado and not forzar:` (R23/R24) | **2 failed**: `test_f003_r24_ejecutar_sin_override_da_422`, `test_f003_r24_el_bloqueo_no_depende_del_modal` |
| `resultado_sigrid.py`: `motivo_ok=MOTIVO_SIN_SESAME if sin_sesame else None` → `motivo_ok=None` (R25) | **3 failed**: `..._el_override_marca_las_lineas`, `..._una_linea_ya_registrada_tambien_se_marca`, `..._la_marca_se_ve_en_las_vistas` |
| `sqlalchemy_parte_repository.py`: que `marcar_review_required` pueda BAJAR el flag (R26) | **1 failed**: `test_f003_r26_marcar_review_required_solo_sube_el_flag`, que afirma tanto el contador como el estado final `{doc-A: True, doc-B: True, doc-C: False}` |

Los tres bloqueos de la enmienda están sujetos por tests que fallan cuando
el comportamiento desaparece. No son tests decorativos.

### Regresión de apagado (lo crítico) — leída, no solo ejecutada

Con `sesame_enabled=false` el comportamiento debe ser **idéntico**. He
mirado qué afirman los tests, no solo que pasen:

- `test_f003_r7_sin_configurar_ni_toca_la_red`: corta
  `httpx.HTTPTransport.handle_request` con un `AssertionError` y renderiza
  la vista trabajador. Cualquier llamada de red real haría fallar el test.
  Además exige `[sesame][wiring] DESACTIVADO` en el log.
- `test_f003_r7_sin_configurar_usa_el_respaldo_holidays`: sobre el
  proveedor **REAL** que ha cableado `build_app` (no un doble), afirma
  `proveedor.activo is False`, que el 2026-01-01 sale `festivo=True` y
  `fiable=True`, y que el 2026-01-02 no es festivo. Es la prueba de que el
  respaldo `holidays` sigue enchufado.
- Los tres `test_f003_r27_*` de sv4 construyen un `CalendarioProvider`
  **real con `cliente=None`** y afirman: preflight sin `sesame_bloqueo`,
  `/ejecutar` 200 con la llamada a sv5 hecha, `/encolar` 200 con la
  publicación hecha, y `sigrid_motivo is None` en todas las líneas.
- sv3: `test_f003_r10_sin_configurar_se_cablea_el_json_de_siempre` y
  `test_f003_r10_el_json_no_ofrece_senal_de_degradacion`;
  `test_f003_r27_sin_calendario_cableado_no_marca_nada`.

**Sin latencia ni llamadas nuevas en caliente con la feature apagada**:
lo he verificado leyendo el camino, no solo confiando en los tests. Con
`cliente is None`, `CalendarioProvider._resolver` devuelve
`(None, "sin_sesame")` en la primera línea — sin caché, sin lock, sin red —
y `_nombre_festivo` cae directo en `self._respaldo(d)`, que es el mismo
`holiday_provider.name` de antes. `fiable_para` devuelve `True` en la
primera línea y `jornada_contrato` devuelve `None` sin tocar nada. En
`obra_detail`, `_es_festivo(_fecha)` con Sesame apagado resuelve al mismo
respaldo que alimentaba `_c.is_holiday`: mismo veredicto.

### Otros puntos vigilados

| Punto | Resultado |
|---|---|
| **Cero cambios de schema** | ✔ Ninguna copia de `orm_models.py` aparece en `git diff dev...HEAD --stat`. La marca va en `sigrid_motivo` (`String(255)`), que ya existía |
| **Clientes gemelos sv3/sv4** | ✔ Comparados línea a línea tras el docstring de cabecera: **cuerpo idéntico**. Los docstrings difieren a propósito (cada uno apunta a su gemelo). Pero ver defecto 4: finales de línea distintos |
| **Tests sin red/BBDD/Sesame real** | ✔ Fixture `sin_red` + `httpx.MockTransport` + SQLite en memoria. **Todas** las construcciones de `Settings(...)` de la suite llevan `_env_file=None` (único hit sin él es un comentario) |
| **Sin secretos en el diff** | ✔ Barrido sobre el diff completo con `(api[_-]?key\|password\|secret\|token)\s*=\s*["'][^"']{8,}`: cero hallazgos reales. `SESAME_BASE_URL=""` vacía a propósito, la clave solo como `keyvaultref`/`secretref`, `.env.example` con placeholders vacíos |
| **Sin prints de debug** | ✔ Cero `print(` añadidos en el diff `.py` |
| **Cabecera de ruta** | ✔ Los 26 ficheros `.py` nuevos llevan su ruta relativa en la primera línea |
| **`azure-apps/partes.md`** | ✔ Commit local `5a95c03` (sin push). Declara el consumo **sin inventar despliegue**: «Consumo declarado, todavía APAGADO», «A 2026-08-15 **no está desplegado**», «El secreto de Sesame **aún no está cargado**». P1/P2/P3 anotadas, y no escribe `sesame-api.md` porque el dueño es ese proyecto |
| **Sintaxis JS** | ✔ `node --check services/partes-front/static/app.js` → JS OK |
| **Arbol limpio** | ✔ `git status --porcelain` vacío tras mis sabotajes |

## Checkpoints

| Checkpoint | Estado | Nota |
|---|---|---|
| **C1** arnés completo y en verde | **[x]** | `init.sh` exit 0; los 7 ficheros obligatorios existen |
| **C2** estado coherente | **[x]** | Una sola feature `in_progress`; rama correcta; `current.md` solo la sesión activa; F-001 y F-002 con su resumen en `history.md` |
| **C3** arquitectura y convenciones | **[x]** | Dominio limpio (`domain/ports/parte_repository.py` solo importa `typing` y modelos de dominio). `calendario_provider.py` (application) importa del cliente en infrastructure, igual que los cuatro `*_catalog.py`/`empleado_reconciler.py` ya existentes de sv4: es el estilo de la casa, no una desviación. Trampas de dominio: empleado≠recurso intacta (el DNI se usa para *consultar* el calendario, los ides de registro no se tocan); incidencias sin tocar; schema duplicado **sin tocar** |
| **C3 bis** documentos de fuera | **N/A** | **Justificación**: el diff no añade ni modifica nada en `docs/referencia/` (comprobado en `--stat`). No hay barrido que hacer |
| **C4** verificación real | **[ ]** | Trazabilidad y aislamiento, perfectos (ver defecto 3 sobre el listado de las MANUALES) |
| **C4 bis** rigor cumplido | **[x]** | `rigor: critico` declarado; fase RED con trazas reales **y reproducida por mí**; cobertura `[OK]` 94,5 %; mutación recalculada y coincidente; 25 supervivientes, cero `PENDIENTE`; sección «Evidencias» con los cuatro números |
| **C4 ter** rutas sensibles | **N/A** | **Justificación**: `harness/rutas_sensibles.json` no existe en este repositorio. Sin declaración, el bloque es N/A por configuración y no hay nada que justificar más allá de esto |
| **C5** sesión cerrada | **[ ]** | T1–T18 todas `[x]` con su commit `F-003 Tn:` (T14 vive en `azure-apps`, commit `5a95c03`: correcto, es otro repositorio). Árbol limpio. `features.json` coherente. Falla por el número desactualizado de `current.md` (defecto 3) |

## Cobertura requisito → test

| Req | Tests | Req | Tests |
|---|---|---|---|
| R1 | 22 `test_f003_r1_*` | R15 | 18 `test_f003_r15_*` (splits dorados) |
| R2 | 6 | R16 | 16 |
| R3 | 3 | R17 | **MANUAL** (declarado en la spec) |
| R4 | 16 | R18 | 9 |
| R5 | 4 | R19 | propiedad de la suite: fixture `sin_red` + `MockTransport` |
| R6 | 6 | R20 | 3 |
| R7 | 9 | R21 | **documental**: `azure-apps/partes.md`, commit `5a95c03` |
| R8 | 20 | R22 | 6 |
| R9 | 10 | R23 | 4 |
| R10 | 5 | R24 | 4 |
| R11 | 6 | R25 | 11 (+ modal MANUAL) |
| R12 | 9 | R26 | 19 |
| R13 | 3 | R27 | 6 |
| R14 | 5 | | |

Las tres ausencias (R17, R19, R21) están declaradas por escrito en la spec
y en el informe del implementer, con motivo. Las acepto.

## Cambios requeridos

1. **`services/partes-front/interface_adapters/web/app.py:61` — import sin
   usar que además acopla la suite.** `MOTIVO_SIN_SESAME` se importa pero
   no se usa en `app.py`; `python -m ruff check --select F401` lo señala
   (`F401 ... imported but unused`, 1 error, marcado como *fixable*). No es
   inocuo: `services/partes-front/tests/test_f003_r23_bloqueo_registro.py:279`
   hace `from interface_adapters.web.app import MOTIVO_SIN_SESAME`, así que
   depende de esa reexportación implícita. Un `ruff --fix` de rutina
   borraría el import y **rompería la suite**.
   *Arreglo*: quitar `MOTIVO_SIN_SESAME` del import de `app.py` y que el
   test lo importe de su origen,
   `infrastructure.transfer.resultado_sigrid`.

2. **`progress/impl_F-003.md:268-273` — la afirmación sobre `ruff` es
   falsa.** Dice: «ninguno de los 9 nuevos [avisos] está en los ficheros de
   la feature». El F401 del punto 1 está en `app.py`, que es un fichero de
   la feature, y la constante no existía antes de F-003, luego el aviso es
   nuevo. A rigor `critico` la sección de evidencias tiene que ser exacta:
   corregir la frase (o el import, que la vuelve cierta).

3. **`progress/current.md:13-14` — cobertura desactualizada.** Dice
   «`PUERTA COBERTURA` al 93,4 %»; el valor real que imprime `init.sh` es
   **94,5 %** (587/621), que es además el que trae bien el informe del
   implementer. `current.md` es el fichero que lee la siguiente sesión:
   corregir el número. Aprovecha para listar ahí las verificaciones
   MANUALES **con su comando exacto** (hoy delega en el informe: C4 pide
   que estén en `current.md`); para las tres de revisión de diff basta con
   `git diff dev...HEAD -- infra/`, `git diff dev...HEAD -- CLAUDE.md` y
   `git -C ../azure-apps show 5a95c03`.

4. **Finales de línea del cliente gemelo de sv3.**
   `services/partes-persistencia/infrastructure/sesame/sesame_api_client.py`
   está en **CRLF**; su gemelo de sv4 y el resto de ficheros nuevos, en
   **LF**. El cuerpo del código es idéntico byte a byte (verificado
   normalizando), pero un `diff` entre las dos copias reporta **el fichero
   entero como distinto**, que es justo la herramienta con la que se
   comprueba la regla que esta misma feature acaba de escribir en el
   `CLAUDE.md` («quien toque una copia cambia TODAS»). Pasar el fichero a
   LF.

## Punto que necesita decisión del humano (no lo arregla el implementer)

**La edición del `CLAUDE.md` (T17) va más allá de la lista ampliada.** La
decisión D1, tal y como quedó escrita en `design.md:108-115`, era añadir
«los clientes `infrastructure/sesame/` (sv3 y sv4)» **«con redacción mínima
coherente con la existente»**. El commit `a4a9a61` hace eso, pero además
reescribe el cierre de la regla:

- antes: «La única duplicación tolerada es **la ya existente** (…): **no
  crece**, y quien la toque cambia TODAS las copias en la misma feature.»
- ahora: «La única duplicación tolerada es **esta lista cerrada**: (…).
  **Solo crece con una decisión así**; quien toque una copia cambia TODAS
  en la misma feature.»

En descargo del implementer: algo había que reescribir, porque mantener
«no crece» justo después de hacerla crecer sería contradictorio, y el
sustituto sigue exigiendo decisión expresa del humano. Pero es un cambio en
el significado de una **regla dura del fichero que gobierna todas las
sesiones**, no venía declarado entre las desviaciones conscientes del
informe (que sí declara las otras dos, `festivos()→None` y `motivo_ok`), y
el propio implementer lo dejó como verificación MANUAL nº 5. **No lo puede
aprobar un reviewer**: o el humano firma la nueva redacción, o se vuelve al
absoluto y se limita a añadir el ítem a la lista.

## Observaciones (no bloquean)

- `azure-apps/partes.md` sigue conteniendo la IP interna de Sigrid
  (`80.28.223.30`) en una **línea de contexto no tocada** por el commit de
  F-003. Es deuda previa de ese repositorio, ajena a esta feature, pero
  conviene que el humano lo sepa: la regla transversal de no versionar IPs
  internas aplica también allí.
- El aviso de `ruff` del portero (451, deuda previa) sigue siendo un
  `[AVISO]` que no bloquea. Salvo el F401 del punto 1, no he encontrado
  avisos nuevos atribuibles a la feature.
- Riesgo operativo bien documentado y que suscribo: encender `SESAME_*`
  contra una URL muerta **bloquea las aprobaciones** (R23). Está avisado en
  `infra/00_vars_partes.ps1`, en `current.md` y en `azure-apps/partes.md`.
  Es la decisión correcta (calcular mal en silencio es peor), pero el
  humano tiene que verlo antes de tocar Azure.

## Automejora del protocolo (propuesta, no aplicada)

1. **`CHECKPOINTS.md` · C3.** Añadir un checkbox explícito para las
   ediciones de ficheros de gobierno: «Si el diff toca `CLAUDE.md`,
   `.claude/agents/*` o `CHECKPOINTS.md`, el cambio **no excede** lo que la
   spec aprobada autorizaba, y toda reescritura de una regla existente
   consta como desviación declarada». Esta review lo ha tenido que razonar
   a mano porque ningún checkpoint lo cubre, y es la clase de cambio con
   más alcance de todo el repositorio.
2. **`harness/init.sh` · puerta de lint diferencial.** El aviso agregado
   («451 avisos, deuda previa») es hoy inútil para detectar un aviso
   **nuevo** en un fichero de la feature: he tenido que correr `ruff` sobre
   el alcance a mano para encontrar el F401. Propongo que la puerta corra
   `ruff` solo sobre los ficheros del alcance del diff y avise si aparece
   algo nuevo ahí.
3. **`.claude/agents/reviewer.md`.** Añadir al protocolo, como paso fijo,
   el sabotaje-y-restauración de los requisitos centrales que ya he hecho
   aquí: es lo que distingue «los tests pasan» de «los tests muerden», y
   hoy solo lo pide la fase RED del *informe del implementer*, que es
   precisamente la parte que se puede escribir sin ejecutar nada.

Los tres valen para cualquier proyecto: si el humano los acepta, van a
`arnes-base` en el mismo trabajo (regla de propagación del `CLAUDE.md`).

---

# Segunda pasada (2026-08-16)

**Veredicto: APPROVED.** Rama `feature/F-003-sesame-festivos-jornada`, 29
commits sobre `dev` (los 24 de la primera pasada + 5 nuevos).

Los cuatro cambios requeridos están aplicados y **verificados uno a uno de
forma independiente**; el punto que necesitaba decisión del humano está
firmado y consta por escrito. No he encontrado ningún defecto nuevo
introducido por las correcciones.

## Alcance del delta (solo lo pedido)

`git diff f4dea7a..HEAD --name-only` devuelve **exactamente cuatro
ficheros**:

| Fichero | Motivo |
|---|---|
| `services/partes-front/interface_adapters/web/app.py` | punto 1 |
| `services/partes-front/tests/test_f003_r23_bloqueo_registro.py` | punto 1 |
| `progress/impl_F-003.md` | puntos 2 y 4 (documentación) |
| `progress/current.md` | punto 3 + firma del humano |

**Cero código de producción tocado salvo un import**, y **`CLAUDE.md` no
aparece en el delta**: el implementer respetó la orden de no tocarlo
mientras el humano decidía. Los cuatro commits del implementer llevan
prefijo `F-003 fix-review:`; el quinto, `a2bb905`, es del líder recogiendo
la firma.

## Los cuatro puntos, verificados

### Punto 1 · import `MOTIVO_SIN_SESAME` — RESUELTO

- `app.py` colapsa el import de cuatro líneas a
  `from infrastructure.transfer.resultado_sigrid import aplicar_resultado`.
  Búsqueda de `MOTIVO_SIN_SESAME` en `app.py` → **cero ocurrencias**: ya no
  hay reexportación implícita que un `ruff --fix` pueda romper.
- `test_f003_r23_bloqueo_registro.py:279` importa la constante **de su
  origen**, `infrastructure.transfer.resultado_sigrid`.
- `python -m ruff check --select F401 <los 36 ficheros .py del diff>` →
  **All checks passed!** (ejecutado por mí, no leído del informe).

### Punto 2 · la frase sobre `ruff` — RESUELTO

El informe ya no afirma lo falso: reconoce que el F401 **sí** estaba en un
fichero de la feature, dice qué se hizo y da el recuento nuevo. Comprobado
contra la realidad: el portero imprime hoy `[AVISO] ruff: 450 avisos`
— **451 → 450**, exactamente el aviso retirado.

### Punto 3 · `current.md` — RESUELTO, y mejor de lo pedido

- La cobertura ya no dice 93,4 %: dice **94,5 % (586/620)**, que es
  literalmente lo que imprime `init.sh` en mi ejecución. El implementer
  además **explica el 587/621 de mi primera medición** (el arreglo del
  punto 1 elimina una línea cambiada), en vez de sobrescribir el número sin
  más. Eso es exactitud, no maquillaje.
- Las **cinco verificaciones MANUALES** están en `current.md` en tabla, con
  su comando exacto (`git diff dev...HEAD -- infra/`,
  `git diff dev...HEAD -- CLAUDE.md`, `git -C ../azure-apps show 5a95c03`)
  y las dos de navegador marcadas como tales, con la nota de que la del
  modal no se puede probar de verdad hasta P2.

### Punto 4 · finales de línea del gemelo de sv3 — RESUELTO

Este punto merece explicación porque **no tiene commit propio, y es
correcto que no lo tenga**. Lo he verificado yo, no aceptado:

- `git cat-file blob HEAD:…sv3…/sesame_api_client.py` → **0 CRLF, 210 LF**.
  Y en `664d233` (el commit que lo creó) → **idéntico, 0 CRLF**. El blob
  **siempre estuvo en LF**: `core.autocrlf=true` normaliza al indexar, así
  que la divergencia era **exclusivamente del árbol de trabajo** y
  arreglarla no puede producir diff. Mi punto 4 era real como problema del
  árbol, pero no había nada que commitear.
- `git ls-files --eol` sobre los dos gemelos → `i/lf w/lf` en ambos.
- Y lo que de verdad pedía el punto: `diff` entre los dos gemelos ahora
  enseña **tres hunks, todos dentro del docstring de cabecera** (el puntero
  cruzado al gemelo, el módulo donde vive la cascada en cada servicio, y un
  párrafo de sv3 sobre por qué allí los festivos son críticos). **El cuerpo
  del código es idéntico**, que es la comprobación que la regla del
  `CLAUDE.md` exige poder hacer con un `diff` a secas.
- **Causa raíz confirmada en carne propia**: durante esta review hice
  `git checkout --` de `resultado_sigrid.py` para restaurar un sabotaje, y
  git me lo devolvió en **CRLF** (`w/crlf`) sin que yo tocara nada. El
  diagnóstico del implementer —`core.autocrlf=true` + repositorio sin
  `.gitattributes` ⇒ el arreglo no es permanente— es exacto. Más aún:
  cuando lo devolví a LF a mano, `git status` lo marcó como modificado
  aunque `git diff --quiet` salía en 0 (contenido idéntico al blob), y
  git avisaba «LF will be replaced by CRLF the next time Git touches it».
  Lo dejé como git lo materializa (`w/crlf`, blob `i/lf`, árbol limpio),
  que es el estado en el que estaba antes de mi sabotaje. Suscribo su
  decisión de **no** añadir
  `.gitattributes` por su cuenta: es un cambio de alcance de repositorio
  completo, afecta a los seis servicios y no estaba ni en la spec ni en la
  review. Queda propuesto al humano y lo respaldo (ver observaciones).

### Punto del humano · RESUELTO

`progress/current.md`, sección **«Decisión del humano (2026-08-16, tras la
review)»** (commit `a2bb905`): el humano **firma** la nueva redacción de la
regla de duplicación tolerada («lista cerrada… solo crece con una decisión
así»). El `CLAUDE.md` queda como lo dejó T17 y **no hay nada que revertir**.
Verificado que el fichero no se ha tocado desde `a4a9a61`.

### Observación de la primera pasada · RESUELTA por el líder

`git -C ../azure-apps show fe4e977` redacta la IP del SQL de Sigrid del
§5.3 (→ `<ip-vpn-sigrid>`). Barrido posterior sobre `azure-apps/partes.md`
buscando IPs: **cero hallazgos**.

## Portero y suites (ejecutados de nuevo)

`bash harness/init.sh` completo → **ENTORNO LISTO, exit 0**.
`PUERTA COBERTURA: 94.5% de 620 líneas cambiadas cubiertas (586/620,
umbral 80%, nivel critico)`.

Como el portero cachea las suites de servicio, las lancé las tres directas:

| Suite | Resultado |
|---|---|
| `tests/` (raíz) | **6 passed** en 0,15 s |
| `services/partes-persistencia` (sv3) | **95 passed** en 5,06 s |
| `services/partes-front` (sv4) | **272 passed** en 38,69 s |

**373 tests, el mismo total que antes**: ninguna corrección quitó ni añadió
tests.

## Cobertura y mutación siguen válidas para el diff ampliado

El alcance **sí cambió** (el arreglo del punto 1 lo encoge), así que no me
he fiado de la campaña anterior. Recalculado de cero:

- **Alcance: 17 ficheros, 1533 líneas** (antes 1537). El delta son
  **4 líneas y todas en `app.py`** (288 → 284): en `dev` ya existía
  `from infrastructure.transfer.resultado_sigrid import aplicar_resultado`
  en una sola línea, F-003 la había convertido en un bloque de cuatro para
  meter `MOTIVO_SIN_SESAME`, y al revertirlo esa línea **deja de ser una
  línea cambiada**. Cuadra exactamente con el −1 de la puerta de cobertura
  (621 → 620) y con el −4 de líneas añadidas de `app.py` (276 → 272).
- **Mutantes: 211** — recalculados fichero a fichero con
  `harness.mutacion.generar_mutantes` sobre el alcance nuevo: **el mismo
  total que declara `progress/mutacion_F-003.md`**. Era previsible (las
  cuatro líneas perdidas son un `import`, que no genera mutantes) pero está
  comprobado, no supuesto.
- **Supervivientes remuestreados**: los de `app.py` siguen existiendo con
  **el mismo operador y el mismo texto original→mutado** que el informe
  (`if degradado and forzar:` → `or` [logico]; `abs(...) <= 1e-9` → `<`
  [comparacion]; `settings.default_reviewer or "(sin usuario)"` → `and`
  [logico]). La campaña sigue siendo válida: **25 supervivientes, cero
  `PENDIENTE`**.

## Los tests siguen mordiendo (sabotaje, no solo ejecución)

El punto 1 cambió por dónde se exporta `MOTIVO_SIN_SESAME`, así que repetí
el sabotaje del requisito que depende de esa constante:
`resultado_sigrid.py`, `motivo_ok=MOTIVO_SIN_SESAME if sin_sesame else None`
→ `motivo_ok=None`. Resultado: **3 failed**
(`test_f003_r25_el_override_marca_las_lineas`,
`..._una_linea_ya_registrada_tambien_se_marca`,
`..._la_marca_se_ve_en_las_vistas`). Fichero restaurado; **árbol limpio**
salvo este propio informe, que aún no está versionado.

## Checkpoints (los dos que faltaban)

| Checkpoint | Estado | Nota |
|---|---|---|
| **C4** verificación real | **[x]** | Era lo único que fallaba: las MANUALES ya están en `current.md` con su comando exacto. Trazabilidad y aislamiento seguían perfectos |
| **C5** sesión cerrada | **[x]** | `tasks.md`: **18 `[x]`, 0 pendientes**. `current.md` con la cobertura real. Árbol limpio. `features.json` coherente (F-003 sigue `in_progress`: lo pasa a `done` el líder tras esta aprobación) |

C1, C2, C3 y C4 bis siguen `[x]`; **C3 bis** y **C4 ter** siguen `N/A` con
la justificación escrita en la primera pasada (el diff no toca
`docs/referencia/`; `harness/rutas_sensibles.json` no existe en este
repositorio). El resto de la primera pasada —trazabilidad requisito→test,
regresión de apagado, ausencia de secretos, cero cambios de schema— sigue
vigente y no lo repito.

## Observaciones (no bloquean la aprobación)

1. **`.gitattributes` con `* text=auto eol=lf`**: lo propone el implementer
   y lo respaldo con la evidencia de arriba (un `git checkout` me devolvió
   un fichero en CRLF durante esta misma review). Hay ya seis ficheros del
   alcance en `w/crlf` en el árbol. Ninguno es un gemelo, así que hoy no
   estropea ninguna comparación, pero es una trampa que se disparará sola el
   día que alguien duplique otro fichero. **Decisión del humano**, no de un
   agente: afecta a los seis servicios.
2. **Números de línea de `progress/mutacion_F-003.md` desfasados en 3** para
   los cuatro supervivientes de `app.py` (1085→1082, 1501→1498, 1603→1600,
   1607→1604), porque el arreglo del punto 1 quitó tres líneas por encima.
   **No bloquea y no exijo re-lanzar la campaña**: el informe identifica
   cada mutante por su texto `Original:`/`Mutado:`, que es lo que he usado
   para verificarlos y lo que hace el informe auditable. Queda anotado aquí
   para que quien lo audite en el futuro no lea el desfase como señal de
   informe fabricado, que es justo lo contrario de lo que he encontrado.
3. **`progress/review_F-003.md` no está versionado.** `review_F-001.md` y
   `review_F-002.md` sí lo están. Es tarea del líder, no del implementer:
   conviene commitearlo al cerrar la feature para que el historial de
   revisiones quede completo.
4. Siguen vigentes los avisos de la primera pasada: el **riesgo operativo**
   de encender `SESAME_*` contra una URL muerta (bloquea aprobaciones, es
   deliberado, está documentado en tres sitios) y las **cinco verificaciones
   MANUALES** que solo puede cerrar el humano.

## Automejora del protocolo (propuestas, ninguna aplicada)

Las tres de la primera pasada siguen en pie (checkbox de C3 para ficheros de
gobierno, puerta de lint diferencial sobre el alcance, y el sabotaje como
paso fijo del reviewer). La segunda pasada añade una cuarta:

4. **`.claude/agents/reviewer.md` · re-review con alcance cambiado.** Cuando
   una corrección modifica ficheros del alcance, el reviewer debe
   **recalcular alcance y mutantes** y comprobar que la campaña anterior
   sigue valiendo, en vez de darla por buena porque «solo fue un import».
   Aquí ha salido bien (211 = 211), pero el mismo arreglo podría haber
   borrado mutantes cubiertos sin que nadie lo notara. Y como corolario:
   **un desfase de números de línea en el informe de mutación no es motivo
   de rechazo si el texto original→mutado sigue casando** — conviene decirlo
   por escrito para que una futura re-review no bloquee por algo cosmético.

Las cuatro valen para cualquier proyecto: si el humano las acepta, van a
`arnes-base` en el mismo trabajo (regla de propagación del `CLAUDE.md`).
