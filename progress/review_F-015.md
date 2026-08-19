<!-- progress/review_F-015.md -->
# F-015 · Revisión — jornada del día por jornada semanal derivada del candef

Rama `feature/F-015-jornada-semanal-candef` (22 commits en `dev...HEAD`, todos
con prefijo `F-015`) · spec `specs/F-015-jornada-semanal-candef/` (R10–R35,
con §13 bis y §13 ter del `design.md`) · informes `progress/impl_F-015.md` y
`progress/mutacion_F-015.md`.

> Revisión hecha de cero. Un reviewer anterior se colgó sin escribir nada; no
> se ha reutilizado ningún juicio suyo.

## Veredicto

**APROBADO.**

Nada bloqueante. Quedan **cuatro observaciones menores** (sección 7), ninguna
de las cuales cambia comportamiento, y **una condición de cierre que no es del
implementer**: T12 es MANUAL del humano y sigue pendiente (sección 6).

## Nivel de rigor y puertas que exige

`harness/features.json` declara `"rigor": "estandar"` para F-015. Ese nivel, en
`harness/rigor.json`, exige **fase RED**, **cobertura** (umbral 80 % de las
líneas cambiadas) y **campaña de mutación** con `supervivientes_maximos: null`
—es decir, supervivientes **analizados**, no cero supervivientes—.

| Puerta | Exigida | Resultado |
|---|---|---|
| Fase RED | Sí | **[x]** trazas reales en el informe para T1, T4, T5, T6 y T9 |
| Cobertura | Sí | **[x]** `PUERTA COBERTURA: 99.4% de 523 líneas cambiadas (520/523, umbral 80%)` |
| Mutación | Sí | **[x]** 259 / 237 / 22 / 0 timeouts, **recalculada por el reviewer** |

## 1. Entorno (ejecutado por el reviewer)

`bash harness/init.sh` → **exit 0**, `ENTORNO LISTO. Puedes trabajar.`

- raíz `92 passed`; sv3 `438 passed`; sv4 `665 passed` → **1 195 tests**,
  exactamente lo declarado en «Evidencias».
- `PUERTA COBERTURA: 99.4% de 523 líneas cambiadas cubiertas (520/523,
  umbral 80%, nivel estandar)` — **[OK]**, coincide con lo declarado.
- Avisos no bloqueantes preexistentes: `ruff` (deuda previa), sv1/sv2 sin
  directorio de tests, `infra` sin comando de tests.
- Árbol limpio (`git status --short` sin salida).

## 2. Verificación independiente de la mutación (C4 bis)

No me he fiado del informe: he **recalculado** el alcance y los mutantes con
`harness.alcance` + `harness.mutacion.generar_mutantes` (cálculo puro, sin
ejecutar la suite ni escribir en disco).

| Magnitud | Informe | Recálculo del reviewer |
|---|---|---|
| Ficheros en alcance | 14 | **14** |
| Líneas de producción | 1 570 | **1 570** |
| Mutantes generados | 259 | **259** |

Coincidencia **fichero a fichero** además del total (p. ej. `jornada_resolver.py`
55 mutantes en cada copia, `recurso_conciliador.py` 53, `web/app.py` 19,
`interface_adapters/api/app.py` 0). La campaña **no** declara cero mutantes, así
que la prueba de control de exclusión no aplica.

**Muestreo de supervivientes** (9 de los 22, más de lo mínimo exigido): los
números 1, 2, 5, 6, 12, 18, 19, 20 y 21 existen como **mutantes reales**, con el
mismo operador y el mismo texto original→mutado que declara
`progress/mutacion_F-015.md`. El informe de mutación no está escrito a mano.

**Equivalencias comprobadas leyendo el código** (tres grupos):

1. **#5/#6/#15/#16 — `d.weekday() >= 5` → `> 5` / `>= 6`** en
   `detalle_jornada_dia` (sv3 línea 257, sv4 268). Equivalencia **confirmada**:
   con la mutación un sábado laborable cae al bloque siguiente, y allí o bien
   sale por el atajo `|resto − c| ≤ ε` devolviendo `c`, o bien llega a
   `es_ultimo_laborable`, que descarta sábado y domingo por su propia guarda
   (línea 153) y devuelve `_detalle(c, False)`. Mismo `DetalleJornada` completo,
   incluido `ultimo_laborable=False`, por los dos caminos.
2. **#18/#20 — `delta > 0` → `>= 0` y `delta < 0` → `<= 0`** en
   `recurso_conciliador.py:631-632`. Equivalencia **confirmada**: `delta == 0` no
   alcanza esa línea por ninguna de las dos ramas — la laborable sale antes en
   `if abs(delta) <= 1e-9: continue` (línea 621) y la no laborable en
   `if delta <= 1e-9: continue` (delta = `total_ord`).
3. **#3/#13 — `texto is None or …` → `and`** en `parsear_mapa_semanal`.
   Equivalencia de contrato **confirmada**: con `and`, `None` recorre
   `str(None).split(",")` → `["None"]` → `ValueError` («par mal formado») y `""`
   → `[""]` → `ValueError` («par vacío»). El fail-fast del arranque se mantiene;
   cambia el texto, no el comportamiento.

Ningún análisis de superviviente queda en `PENDIENTE`. Las **tres campañas**
están documentadas con su porqué (informe §9.1): la 1.ª (260/116/44 con **100
timeouts**) se descarta correctamente por no ser una medición —los timeouts son
«sin resultado», no «mutante resistente»—; la 2.ª (259/211/48/0) motiva los
tests que faltaban; la 3.ª y final (259/237/22/0, **91,5 %**) es la válida y es
la que está en `progress/mutacion_F-015.md`.

**El fallo de diseño que destapó la mutación está bien corregido.** La rama «sin
fecha utilizable» de `_detalle_jornada`
(`recurso_conciliador.py:882-896`) ya no inventa `5 × c` con
`origen="plana"`: llama a `jornada_semanal_de(...)` como todas las demás. Tiene
test (`services/partes-persistencia/tests/test_f015_r22_sin_dni.py:91-120`, cinco
casos), y el assert fija candef 9 → `(9.0, 9.0, 42.0, "mapa", False)` y
candef 10 → `(10.0, 50.0, "plana")`, que es exactamente la corrección.

## 3. Regresión cero (R11) — la propiedad que lo sostiene todo

- `git diff --stat dev...HEAD -- "*test_f003*" "*test_f010*"` devuelve **una sola
  línea**: `tests/test_f010_orm_models_gemelos.py`. **Ningún test dorado de
  F-003 ha sido tocado.**
- Suites `-k f003` verdes por su cuenta: sv3 `95 passed`, sv4 `160 passed`.
- El guardián de F-010 crece **sin relajar nada**: las 5 líneas eliminadas son
  docstring, comentario, el nombre de un test y el texto de un mensaje de
  assert. `COLUMNAS_PARTE_REGISTROS` (56 columnas literales) intacta, `TABLAS`
  sigue comparándose por igualdad estricta y gana `empleado_jornada`, y se añade
  `test_f010_r29_parte_registros_no_gana_ni_pierde_columnas`.
- El diff de `orm_models.py` **no toca `ParteRegistroOrm`**: solo docstring
  («CUATRO»→«CINCO tablas») y la clase nueva. R21 cumplido; `hora_candef` sigue
  guardando el candef crudo (`test_f015_r21_el_split_guarda_el_candef_crudo`).
- La **rama de día no laborable** de `_reclasificar_extras_jornada` no se ha
  modificado (revisado el diff de líneas eliminadas: solo comentarios, el
  cálculo de `ordinarios`/`total_ord` por congelados y la sustitución de
  `candef_efectivo` por `detalle_jornada_dia` en la rama laborable). El recorte
  por `registro_id` descendente y la extra negativa única sobre el pivote se
  conservan.
- **DI1 (atajo `S = 5c`)** es una decisión acertada y bien argumentada: es lo que
  permite que el dorado
  `test_f003_r8_el_dni_del_grupo_llega_al_puerto` —que exige exactamente una
  consulta al calendario— siga verde sin tocarlo. Está fijada por test propio.

## 4. Copias gemelas y guardianes

- Los dos `infrastructure/database/orm_models.py`: **byte-idénticos** (mismo
  MD5, `cmp` sin diferencias).
- Los dos `application/services/jornada_resolver.py`: **ni una línea de código
  ejecutable difiere**; los tres hunks del diff son docstrings. El guardián
  `tests/test_f015_r19_jornada_resolver_gemelo.py` compara firmas, campos de las
  dataclases, superficie pública, 27 casos, un barrido de 3 semanas, el parseo
  del mapa y sus errores — y **muerde** (`test_f015_r19_el_guardian_detecta_una_copia_alterada`).
- Guardianes de la raíz verdes por su cuenta: `pytest tests -q -k "f015 or f010"`
  → `86 passed`.
- **R33 (variable espejo)**: mismo nombre de campo, mismo alias de entorno
  (`JORNADA_SEMANAL_POR_CANDEF`, `JORNADA_CACHE_TTL_S`), mismo tipo y mismo
  default (`"8:40,9:42"` / `600`) en los dos `config/settings.py`. Fail-fast al
  arrancar probado en **los dos** servicios
  (`test_f015_r10_fail_fast_wiring.py` en sv3 y
  `test_f015_r10_sv4_un_mapa_mal_formado_no_levanta_la_app` en sv4).

## 5. Cobertura requisito → test

| Req. | Test que lo cubre | ✓ |
|---|---|---|
| R10 mapa candef→semanal + aviso | `sv3/test_f015_r10_mapa_candef.py`, `sv3/test_f015_r10_fail_fast_wiring.py`, `sv4/test_f015_r10_mapa_candef_sv4.py` | [x] |
| R11 regresión cero candef 8 | `sv3/test_f015_r11_regresion_candef8.py` + dorados de F-003 intactos | [x] |
| R12 candef inválido | `sv3/…r12_candef_invalido.py`, `sv4/…r12_candef_invalido_sv4.py` | [x] |
| R13 último laborable | `sv3/…r13_ultimo_laborable.py`, `sv4/…r13_ultimo_laborable_sv4.py` | [x] |
| R14 finde y semana festiva | `sv3/…r14_finde_y_semana_festiva.py` | [x] |
| R15 sin calendario → viernes | `sv3/…r15_calendario_no_registros.py` | [x] |
| R16 excepciones vigentes | `sv3/…r16_excepciones.py`, `sv4/…r16_excepciones_sv4.py` | [x] |
| R17 tabla caída o vacía | `sv3/…r17_tabla_caida_o_vacia.py`, `sv4/…r17_…_sv4.py` | [x] |
| R18 ORM en las dos copias | `sv3/…r18_orm_empleado_jornada.py`, `sv4/…r18_…_sv4.py` | [x] |
| R19 resolutor gemelo | `tests/test_f015_r19_jornada_resolver_gemelo.py` (raíz) | [x] |
| R20 cómputo último laborable | `sv3/…r20_computo_ultimo_laborable.py` | [x] |
| R21 `hora_candef` crudo / 56 columnas | `sv3/…r21_hora_candef_intacto.py` | [x] |
| R22 sin DNI / sin fecha | `sv3/…r22_sin_dni.py` | [x] |
| R23 degradado a review | `sv3/…r23_degradado_review.py` | [x] |
| R24 avisos de jornada incompleta | `sv4/…r24_avisos.py` | [x] |
| R25 KPI de jornada | `sv4/…r25_kpi.py` + `templates/trabajador_detail.html` | [x] |
| R26 «+ Nuevo» con `fecha` | `sv4/…r26_sugerida_fecha.py` | [x] |
| R27 | **N/A — reservado a F-016** por la propia spec | N/A |
| R28 traza en el log (sin DNI) | `sv3/…r28_log_trazable.py` (8 casos, incluido «el log no lleva el DNI de nadie») | [x] |
| R29 guardián de cinco tablas | `tests/test_f015_r29_guardian_cinco_tablas.py` + `test_f010_orm_models_gemelos.py` | [x] |
| R30 DDL de arranque | `sv3/…r30_ddl_empleado_jornada.py`, `sv4/…r30_…_sv4.py` | [x] |
| R31 revert respeta congelados | `sv3/…r31_revert_respeta_congelados.py` | [x] |
| R32 congelados cuentan, no se tocan | `sv3/…r32_congelados_cuentan_no_se_tocan.py` | [x] |
| R33 variable espejo | `tests/test_f015_r33_variable_espejo.py` (raíz) | [x] |
| R34 documentación | Verificado por lectura (sección 5.1) | [x] |
| R35 | **N/A justificado**: invertido por decisión del humano (`design.md` §13 ter). F-015 se mergea y despliega sin F-014; la puerta pasa a gobernar el **envío** de la petición de F-014 | N/A |

**D7 / DA3 (R31, R32)** implementados según la lectura NO literal aprobada por
el humano: las congeladas suman en `total_ord` (`todas_ordinarias`) pero se
excluyen de `ordinarios` —candidatos y pivote—, y si el día no cuadra sin
tocarlas no se genera **ningún** split y se emite WARNING
(`recurso_conciliador.py:627-642`). La regla vive escrita **una vez**
(`esta_congelado`, línea 82) y la importa el repositorio: correcto, es
justamente lo que evita que reversión y cálculo discrepen.

### 5.1 Documentación (R34)

- `docs/ARCHITECTURE.md`: semántica 3 reescrita (jornada **del día**, mapa,
  último laborable, `max(0, S − 4×candef)`, regresión con candef 8, congelados)
  y semántica 7 con **cinco tablas**. `grep "uatro tabla"` → **sin resultados**.
- `docs/referencia/partes-proyecto.md`: §4.3 reescrita y §5.4 nueva con la tabla
  `empleado_jornada`; cabecera de §5 con «Cinco tablas».
- `infra/create_capps_partes.ps1:81` e `infra/create_sv4_front.ps1:67`:
  `JORNADA_SEMANAL_POR_CANDEF=8:40,9:42` y `JORNADA_CACHE_TTL_S=600` en sv3 **y**
  en sv4, con el comentario de «espejo» y «no es secreto». Sin BOM y en CRLF.
- `CLAUDE.md:158-162`: `application/services/jornada_resolver.py` añadido a la
  lista cerrada de duplicación tolerada, con fecha y motivo.
- `azure-apps/partes.md`: **sí tocaba y sí se hizo**. Commit local `a05e1f1`
  («partes: F-015 anade la tabla empleado_jornada y las variables…»), árbol
  limpio, **sin push** — coherente con que ese repo no tiene remoto.

### 5.2 Convenciones, secretos y capas (C3)

- Arquitectura hexagonal respetada: el puerto vive en
  `domain/ports/jornada_empleado_port.py` sin un solo import de infraestructura;
  el adaptador en `infrastructure/`; el resolutor y el proveedor en
  `application/`. La única dirección `infrastructure → application`
  (`esta_congelado`) tiene precedente en el mismo servicio (`text_match`) y está
  justificada por escrito (DI9).
- Primera línea con la ruta en **todos** los `.py` nuevos y modificados. Las dos
  desviaciones formales (plantilla Jinja2 y los `.ps1` de `infra/`) son la línea
  base preexistente del repositorio, no algo que introduzca F-015.
- **Cero `print()` de depuración**, cero `TODO`/`FIXME` nuevos.
- **Cero secretos y cero datos personales.** Los únicos DNIs del diff son de
  prueba (`12345678Z`, `00000000T`, `11111111H`), los únicos nombres son
  ficticios, y las únicas contraseñas son
  `"PG_PASSWORD": "irrelevante-en-tests"` en fixtures. Ni GUIDs de
  suscripción/tenant, ni IPs internas, ni cadenas de conexión. Hay incluso un
  test que exige que ninguna variable nueva case con
  `PASSWORD|KEY|SECRET|TOKEN|CONNECTION_STRING`.
- Los unit tests **no tocan red ni BBDD**: SQLite en memoria y dobles; búsqueda
  de `psycopg|requests\.|httpx\.|socket\.` en los ficheros `test_f015_*` sin
  resultados.

## 6. Recorrido de `CHECKPOINTS.md`

| Checkpoint | Estado | Nota |
|---|---|---|
| **C1** arnés completo y en verde | **[x]** | `init.sh` exit 0; todos los ficheros del arnés presentes |
| **C2** estado coherente | **[x]** | una sola feature `in_progress`; rama correcta; `current.md` describe la sesión activa; F-015 aún no es `done`, así que nada que llevar a `history.md` |
| **C3** arquitectura y convenciones | **[x]** | sección 5.2 |
| **C3 bis** documentos de fuera | **N/A justificado** | esta feature **no incorpora ningún documento externo** (PDF/ofimática): no hay nada que convertir, redactar ni verificar |
| **C4** verificación real | **[x]** | cada requisito con su test (sección 5); tests sin red ni BBDD; las verificaciones `MANUAL (humano)` listadas en `progress/impl_F-015.md` §7, con sus cuatro puntos y su acuse pendiente |
| **C4 bis** rigor declarado | **[x]** | `rigor: estandar` declarado; fase RED con traza real; cobertura 99,4 % `[OK]`; mutación existente, **verificada de forma independiente**, sin ningún análisis en `PENDIENTE`; sección «Evidencias» con los cuatro números (tests, cobertura, mutantes/supervivientes, tiempo de suite) |
| **C4 ter** rutas sensibles | **N/A justificado** | no existe `harness/rutas_sensibles.json` en este repositorio; `init.sh` no señala ninguna ruta sensible. Es el caso mayoritario que el propio checkpoint declara N/A sin nada que justificar |
| **C5** cierre de sesión | **[x] con una salvedad** | `tasks.md` con T1–T11 y T13 en `[x]` y un commit `F-015 Tn: …` por tarea; árbol limpio, sin artefactos sospechosos; `features.json` refleja `in_progress`, que es el estado real hasta que el líder cierre. **Salvedad**: T12 sigue en `[ ]` |

**Sobre T12 (la salvedad de C5).** T12 es **MANUAL del humano** por definición de
la propia spec: exige arranque real de sv3/sv4 contra la base `partes` y una
mirada al portal. No es trabajo que el implementer pudiera hacer ni que se le
pueda exigir, y está correctamente declarado como pendiente y sin ejecutar en
`progress/impl_F-015.md` §7 (no se ha fingido ninguna verificación). **No
bloquea la aprobación del trabajo, pero sí es condición de cierre de la
feature**: F-015 no debería pasar a `done` sin el acuse del humano sobre esos
cuatro puntos, y el líder debe conservarlos como deuda visible tras el merge y
el despliegue.

**R35 no se aplica como puerta de merge**, conforme a `design.md` §13 ter: con
candef 8 la regresión es cero y F-015 puede mergearse y desplegarse sin F-014.
Lo verificado en esta revisión es consistente con esa decisión.

## 7. Observaciones menores (no bloqueantes, no exigen otra pasada)

1. **`docs/referencia/partes-proyecto.md:289`** — la referencia cruzada dice
   `(§5.5)` cuando la tabla `empleado_jornada` está en **§5.4**; §5.5 es
   `undo_log`. Errata de una palabra. Se puede corregir en el mismo commit del
   merge o dejarla para la siguiente feature que toque el documento.
2. **`specs/F-015-jornada-semanal-candef/tasks.md`, T12** — sigue diciendo «las
   16 columnas» cuando la tabla implementada tiene **19** (DI2 explica que el
   «16» era una cuenta incompleta del propio `tasks.md`/§8 y que la normativa es
   el §6 del `design.md`, con 19). El informe lo corrige en su §7, pero **el
   humano leerá `tasks.md`**: conviene alinear el texto de T12 a 19 antes de dar
   la verificación manual por buena, o al menos avisarle al pasarle el acuse.
3. **`services/partes-persistencia/tests/test_f015_r22_sin_dni.py:91`** — el test
   se llama `…_sin_fecha_utilizable_la_jornada_es_plana`, pero lo que fija es
   justo lo contrario (origen `"mapa"`, que es la corrección del fallo de
   diseño). El assert es correcto; el **nombre** engaña a quien lo lea de
   pasada. Renombrarlo a algo como `…_la_semanal_sale_del_mapa` haría el test
   honesto con lo que prueba.
4. **`.env.example` (DI7)** — el criterio de R33 «ambos `.env.example` contienen
   la variable» **no es verificable en un clon limpio**: `*.example` está
   ignorado en el `.gitignore` de cada servicio, y el test hace `skip` si el
   fichero no existe. Está declarado y justificado, y el vehículo real de la
   variable (`infra/*.ps1`) sí está versionado y verificado, así que no bloquea;
   queda anotado porque es una parte de un requisito que ningún test protege en
   CI.

Detalles cosméticos que ni siquiera son observaciones: `CLAUDE.md:162` quedó con
una línea de ~100 columnas tras el reflow, y los ficheros nuevos suman 3 avisos
`ruff UP035` (`typing.Callable`), que es el estilo del resto del repositorio y
deuda previa declarada.

## 8. Lo que este reviewer NO verificó (declarado)

- **Las cuatro verificaciones de T12**: exigen BBDD real y despliegue. Sin
  ejecutar, por diseño.
- **Las equivalencias de los 13 supervivientes restantes** (los de tolerancia en
  coma flotante, TTL, KPI y filtro de la vista): se comprobaron **tres grupos
  leyendo el código** y se muestrearon 9 de 22 contra el generador. Los demás se
  aceptan sobre el análisis escrito del implementer, que es coherente,
  reproducible y en dos casos (los filtros de `in_period`/`is_weekend`/
  `is_holiday`) llega a la conclusión contraria a su hipótesis inicial y
  conserva igualmente los tests. No agotar esta verificación es una decisión
  consciente de alcance de la revisión.
- **El render visual del KPI** (T12.4): la plantilla se leyó y es correcta en
  Jinja2 y en contenido (S aplicada con su origen, patrón, último laborable),
  pero nadie ha mirado cómo queda en pantalla.

## 9. Automejora del protocolo (propuesta, NO aplicada)

El implementer deja en su §9.5 un hallazgo **genérico y real** del arnés, que
este reviewer confirma leyendo `harness/mutacion.py::ejecutor_para`: **la
campaña de mutación no ejecuta la suite de la raíz al mutar un fichero de un
servicio**, así que el guardián de una copia gemela —que por construcción vive
en `tests/` de la raíz— nunca entra. En F-015 eso produjo **27 de los 48
supervivientes** de la segunda campaña, todos falsos «equivalentes».

Propuesta para `arnes-base` (no aplicada aquí, decide el humano): la opción 2 del
implementer —**ejecutar siempre la suite de la raíz junto a la del servicio**— es
la más simple y en este repositorio cuesta ~4 s. Como mínimo, la opción 3:
**avisar en el informe de mutación** cuando el fichero mutado tenga una copia
gemela declarada en la lista cerrada de `CLAUDE.md`.

Añadiría una línea al protocolo del reviewer (`.claude/agents/reviewer.md`),
sección «Validación contra el nivel de rigor»: **cuando la feature toque un
fichero de la lista cerrada de duplicación, tratar con especial desconfianza los
supervivientes de esa copia** —la herramienta no puede matarlos aunque la
regresión sí se detecte en `init.sh`— y exigir que cada copia tenga sus propios
tests en la suite de su servicio, que es exactamente la contramedida que F-015
aplicó por su cuenta.
