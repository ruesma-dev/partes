<!-- progress/review_F-017.md -->
# F-017 · Identidad real de Easy Auth en el portal (sv4) — Review

**Segunda vuelta · 2026-08-21** · Rama `feature/F-017-identidad-easy-auth`
**Diff:** `dev` (`4ca131c`) … `HEAD` (`a62c9f7`)
**Primera vuelta:** 2026-08-20, CHANGES_REQUESTED (resumen conservado al final)

## Veredicto

> ## APPROVED (APROBADO)

Los **tres defectos** del rechazo están corregidos, y las tres correcciones
las he verificado yo, no leído del informe:

- **Defecto 1** (la lectura suelta de identidad en el consumidor): corregido
  **y convertido en requisito** (R24). El guardián ampliado **caza ahora la
  forma exacta que se coló**, comprobado sembrando el defecto en un fichero
  desechable.
- **Defecto 2** (la enmienda sin propagar): corregido en los **cinco** sitios
  y, mejor que eso, **convertido en test**: `test_f017_r23_*` obliga a que
  todos los sitios que enuncian el criterio nombren la excepción de
  `undo_log.actor`. La corrección ya no depende de que alguien se acuerde.
- **Defecto 3** (el `printenv` que volcaba Key Vault, y M3 obsoleta):
  corregido con la explicación de por qué el `Select-String` no protegía.

**Campaña de mutación reejecutada entera por mí: 32/32 muertos, 0
supervivientes, 0 timeouts.** Alcance y número de mutantes recalculados: 3
ficheros, 462 líneas, 32 mutantes — coincidencia exacta con el informe.

Quedan tres observaciones **no bloqueantes** (§«Residuales») y dos avisos
operativos que el humano debe conocer antes de mergear. Ninguno afecta al
comportamiento de la feature.

---

## Nivel de rigor

`rigor: "estandar"` en `harness/features.json`. Exige fase RED, cobertura
≥ 80 % de las líneas cambiadas y campaña de mutación con supervivientes
documentados (`supervivientes_maximos: null`, los juzga el reviewer). Las tres
puertas se cumplen. La corrección tocó **código de producción nuevo**, así que
las tres se han vuelto a comprobar desde cero, no heredado de la primera
vuelta.

---

## C1–C5 recorridos (segunda vuelta completa)

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` tal cual → `ENTORNO LISTO`, exit 0.
- [x] Los nueve ficheros obligatorios, presentes.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress`: `['F-017']`.
- [x] Rama `feature/F-017-identidad-easy-auth`; ni `main` ni `dev`.
- [x] `progress/current.md` describe la sesión activa (con la sección
      «MANUAL pendiente (acumulado)» heredada, deliberada).
- [x] `progress/history.md` al día.

### C3 — El código respeta arquitectura y convenciones

- [x] **Hexagonal respetada.** La única dependencia nueva es
      `interface_adapters/workers/resultado_consumer.py` →
      `interface_adapters/web/identidad.py`, para importar
      `ACTOR_SIN_IDENTIDAD`. Es **lateral dentro de la misma capa**, no una
      inversión: un worker de adaptadores usa una constante de adaptadores.
      Y es la alternativa correcta a la otra opción, que era duplicar el
      literal `"sin-identidad"` en dos sitios — exactamente lo que R6
      prohíbe conceptualmente. El barrido de capas internas
      (`infrastructure/`, `application/`, `domain/`, `config/`) sigue limpio.
- [x] Primera línea con ruta relativa en los dos ficheros nuevos o tocados
      (`# interface_adapters/workers/resultado_consumer.py`,
      `# tests/test_f017_r24_consumer_firmado.py`).
- [x] `python -m ruff check` sobre los cinco ficheros de la corrección:
      **All checks passed**. Sin `print()`, sin TODO/FIXME, sin dependencias
      nuevas.
- [x] **Cero cambios de schema**, cero ficheros de sv1/sv2/sv3/sv5. El diff de
      la segunda vuelta toca 3 ficheros de producción de sv4, 4 de test, 2 de
      documentación, 1 de spec y 3 de `progress/`.

### C3 bis — Documentos que entran de fuera

Aplica (la primera vuelta modificó `docs/referencia/partes-proyecto.md`; la
segunda ya no lo toca).

- [x] Ningún documento nuevo en `docs/referencia/`; ningún original PDF ni
      ofimático en el árbol ni en el historial de la rama.
- [x] **Barrido de datos sensibles reejecutado** sobre las 1 393 líneas
      añadidas en la segunda vuelta, con los mismos patrones de la primera
      (correos, `[0-9]{8}[A-Za-z]`, IPs, GUID, `password|secret|api_key`,
      `subscription|tenant_id`). **Dos coincidencias, las dos inocuas y
      comprobadas una a una:**

      | Coincidencia | Veredicto |
      |---|---|
      | `aaaa1111-bbbb-2222-cccc-333344445555` | Constante `PETICION_ID` sintética, **reutilizada** del test existente `test_f002_resultado_consumer.py:35`. No es un GUID real |
      | `00000000T` | Aparece **solo en mi propio informe de la primera vuelta** (`progress/review_F-017.md`, versionado en `5763e9f`), donde se cita como el DNI ficticio conocido de las filas de prueba. No hay ni un DNI en código, tests ni spec |

      Cero correos reales (todos `.invalid`, RFC 2606), cero IPs, cero
      secretos, cero identificadores de suscripción o tenant.
- [x] Nada que redactar.

### C4 — La verificación es real

- [x] **25 requisitos** (R1–R24 + R5b/R5c) con test trazable, todos pasando.
      R24 es nuevo de esta vuelta y trae su fila en la tabla de trazabilidad
      de la spec (línea 350).
- [x] Los tests no tocan red ni BBDD: el nuevo `test_f017_r24_consumer_
      firmado.py` monta blob y cola falsos y SQLite en memoria, igual que el
      resto.
- [x] Verificaciones MANUAL listadas en `progress/current.md` con comando
      exacto. **M3 ya no es la obsoleta** (ver defecto 3).
- [x] **Suites relanzadas por mí, no leídas del informe**: sv4
      **1057 passed** (exit 0, 63,7 s; eran 1040 en la primera vuelta, +17) y
      raíz **138 passed** (eran 129, +9 por el guardián de R23 ampliado).

### C4 bis — El rigor declarado se cumple

- [x] `rigor: "estandar"` declarado y válido.
- [x] **Fase RED**: la de los seis requisitos centrales sigue en el informe
      (T2, T6, T8) con traza real. Para el requisito nuevo, **R24**, el
      informe trae la traza del rojo previo y —lo que importa más— el
      guardián se demostró rojo sembrando el defecto (ver defecto 1).
- [x] **Cobertura**: `PUERTA COBERTURA: 99.3 % de 142 líneas cambiadas
      (141/142, umbral 80 %, nivel estandar)`, en `[OK]`, de mi propia
      ejecución.
- [x] **Mutación verificada de forma independiente**: recalculada y
      **reejecutada entera**. Ver la sección siguiente.
- [x] Cero supervivientes, ninguna sección en `PENDIENTE`.
- [x] Sección **«Evidencias»** con los cuatro números, y los dos grandes
      (1057 y 32/32) comprobados a mano.
- [x] Ningún punto N/A.

### C4 ter — Rutas sensibles

**N/A justificado**: no existe `harness/rutas_sensibles.json`.
`CHECKPOINTS.md` dice que sin esa declaración el bloque es N/A y no hay nada
que justificar. `init.sh` no señaló ninguna ruta.

### C5 — La sesión se cerró bien

- [x] `tasks.md`: 16 tareas, **todas `[x]`, cero `[ ]`**, con su commit
      `F-017 Tn:`. Los cuatro commits de esta vuelta van etiquetados
      `F-017 review: …` / `F-017: campana …` en vez de `Tn`, lo cual es
      correcto: **no son tareas del plan, son correcciones de review**, y
      `tasks.md` no debe inventarse tareas a posteriori para justificarlas.
- [x] `git status` limpio, tanto al empezar como después de mis experimentos
      (los verifiqué explícitamente: escribí y borré ficheros de prueba, y
      mutá y restauré los tres ficheros de producción 32 veces).
- [x] `features.json` refleja el estado real (`in_progress`; el paso a `done`
      lo hace el líder).

---

## Verificación de la campaña de mutación (independiente)

Igual que en la primera vuelta, no me creí el número. Tres comprobaciones:

**1. La campaña juzga el código final.** Verifiqué qué tocó cada commit
nuevo: **todo el código está en `c9d136b`**; `5763e9f`, `f7231a9` y `a62c9f7`
solo tocan `progress/`. La campaña corrió sobre `5763e9f`, así que cubre
exactamente el código que se va a mergear.

**2. Recálculo puro del alcance y del número de mutantes**
(`harness.alcance` + `harness.mutacion.generar_mutantes`, sin ejecutar nada):

| | Informe | Mi recálculo |
|---|---|---|
| `app.py` | 146 | 146 ✔ |
| `identidad.py` | 272 | 272 ✔ |
| `workers/resultado_consumer.py` | 44 | 44 ✔ |
| Total líneas | 462 | **462** ✔ |
| Mutantes | 32 | **32** ✔ |

El fichero nuevo entró en el alcance, como debía, y aporta **1** mutante
(`logico`, línea 64). Reparto: 11 lógico, 8 not, 7 booleano, 4 comparación,
1 entero, 1 aritmético.

**3. La reejecuté entera**, los 32 mutantes uno a uno sobre el árbol real,
con el ejecutor del propio arnés y restaurando en un `finally`:

```
TOTAL 32 {'muerto': 32} 91s
mutante del consumidor: muerto | resultado_consumer.py:64 [logico]
    if isinstance(usuario, str) and usuario.strip():
 -> if isinstance(usuario, str) or usuario.strip():
--- arbol --- (git status vacío)
```

**32/32 muertos, 0 supervivientes. El informe del líder es exacto**, y el
mutante nuevo —el que convierte el `and` del consumidor en `or`, que dejaría
pasar un `usuario` vacío como firma— **muere**.

**Sobre los 8 timeouts de la pasada anterior.** El diagnóstico del líder se
sostiene: en serie, los 32 se evalúan en **91 s** (≈ 2,8 s por mutante, porque
`-x` corta en el primer fallo). Un presupuesto de 120 s por mutante solo se
agota si la concurrencia deja a cada worker sin CPU. **Un timeout no es una
medición**: contarlo como «muerto» habría sido inventar cobertura, y
recontarlo como «superviviente» habría sido inventar un defecto. Rehacer la
campaña con `--timeout 420 --workers 4` fue lo correcto.

**La limitación conocida del arnés, revisada otra vez.** `harness/mutacion.py`
juzga cada mutante con la suite **del servicio dueño del fichero**. Los tres
ficheros mutados son de sv4, cuya suite contiene todos los tests de F-017,
así que la limitación **sigue sin morder**. Los guardianes de la raíz
—R22 y ahora también los de R23 ampliados— no generan ni un mutante (vigilan
ficheros que no están en el diff, y un `.md` no se muta). Sigue siendo un
riesgo real para features futuras que toquen código de la raíz.

---

## Defecto 1 — La lectura suelta de identidad · **CORREGIDO**

### Lo que se pedía y lo que hay

| Se pedía | Estado |
|---|---|
| Que no lea `settings.default_reviewer` | ✔ La línea es ahora `usuario = _quien_firma(sobre)`; el `getattr` desapareció |
| Que reutilice la constante, no un literal duplicado | ✔ `from interface_adapters.web.identidad import ACTOR_SIN_IDENTIDAD`. **No hay ni un `"sin-identidad"` suelto** en el fichero |
| Que emita el WARNING de R5b | ✔ Un WARNING por mensaje, con `peticion_id` y el valor sellado |
| Test de la rama «sobre firmado» (R18) | ✔ `test_f017_r18_el_sobre_manda_y_su_usuario_llega_intacto`, `::_el_sobre_gana_a_default_reviewer`, `::_los_marcadores_reservados_del_sobre_se_respetan` |
| Test de la rama «sobre sin firma» | ✔ `test_f017_r24_sobre_sin_usuario_se_sella_sin_identidad`, parametrizado por **5 formas** de sobre sin firma, + 5 tests más |
| Que el guardián lo cubra de verdad | ✔ **Comprobado rompiéndolo**, ver abajo |

**El valor del sobre se respeta intacto** —no se re-normaliza— y la razón que
da el docstring es correcta: ya viene normalizado del punto único, y volver a
tocarlo solo podría estropearlo. Comprobé que eso no abre un agujero de R6:
el sobre lo escribe el propio publicador de sv4 desde `_actor(request)`, que
ya descarta los valores reservados que lleguen por cabecera; no hay camino
por el que un valor externo entre en el sobre.

**Se especificó, no solo se parcheó.** La corrección trae **R24** en
`requirements.md:240`, en forma EARS, con la decisión del humano fechada, el
razonamiento de por qué el fallback es `sin-identidad` (el consumidor corre
siempre desplegado ⇒ es el caso de R5b) y su fila en la tabla de
trazabilidad. Eso es lo que convierte un arreglo en un requisito.

**El test de F-002 se actualizó con honestidad.**
`test_f002_r12_sin_usuario_en_el_sobre_se_usa_el_revisor_por_defecto` pasa a
llamarse `…_se_sella_sin_identidad`, y **no se debilitó**: conserva lo que
F-002 protegía (la traza no se queda sin firmar) y **añade** dos aserciones
(`firma is not None`, `firma != "revisor-por-defecto"`). El cambio de
comportamiento se explica en el docstring y consta como decisión del humano.

### El guardián ampliado: intenté romperlo

Pasó de mirar `app.py` a barrer **todo el código de producción de sv4 por
AST** (`rglob`), detectando la forma directa (`<algo>.default_reviewer`) y la
indirecta (`getattr(settings, "default_reviewer", …)`) sin castigar los
docstrings que explican por qué no hay que leerla — que era el dilema real y
está bien resuelto. Además se autocomprueba sobre ficheros fabricados en
`tmp_path`, nunca sobre el árbol.

No me bastó con leerlo. **Sembré cuatro evasiones** en ficheros desechables
dentro de `services/partes-front/interface_adapters/web/`, ejecuté el
guardián con cada una y las borré (árbol limpio verificado después):

| Evasión sembrada | Guardián |
|---|---|
| `getattr(settings, "default_reviewer", None)` — **la que se coló** | **ROJO** ✔ |
| `os.getenv("DEFAULT_REVIEWER")` | verde — no la ve |
| `request.headers.get(CABECERA_NOMBRE)` importando la constante | verde — no la ve |
| `settings.model_dump()["default_reviewer"]` | verde — no la ve |

**El agujero por el que se coló el defecto está cerrado**, que es lo que se
pedía. Las otras tres son **puntos ciegos residuales**, no regresiones:
ninguna existe en el árbol, las tres son formas que nadie ha escrito nunca
aquí, y ningún guardián razonable cubre todas las maneras concebibles de leer
una variable. Las dejo anotadas abajo como mejora barata, **no como defecto**:
la segunda es la que más me haría vigilar, porque importar constantes de
`identidad.py` acaba de convertirse en patrón establecido con esta misma
corrección.

---

## Defecto 2 — La enmienda propagada · **CORREGIDO Y BLINDADO**

Los cinco sitios, verificados uno a uno en el árbol:

| Sitio | Estado |
|---|---|
| `specs/…/requirements.md` **R7** (línea 136) | ✔ Acota el criterio a las columnas que el portal escribe, **las enumera**, y añade un bloque explicando la excepción y por qué importa («F-018 hereda este criterio») |
| `docs/ARCHITECTURE.md` (línea 155) | ✔ «con **una excepción que hay que conocer: `undo_log.actor`**». Y además documenta el consumidor: toma el actor del sobre, y sin sobre sella `sin-identidad`, «nunca `NULL`, nunca `DEFAULT_REVIEWER`» |
| `identidad.py` (cabecera del módulo y `ACTOR_MAX_LEN`) | ✔ La lista de columnas ya no incluye `undo_log.actor`, y se dice en negrita por qué. El comentario de `ACTOR_MAX_LEN` deja de justificar el 120 con una columna que nadie escribe y lo justifica con las tres `String(120)` reales |
| `azure-apps/partes.md` (línea 224) | ✔ Corregido **en su propio repositorio y con su propio commit** (`c0d1e6e`), como manda la regla de propiedad |
| `docs/referencia/partes-proyecto.md` §5.7 | ✔ Ya estaba bien; sigue siéndolo |

**Barrido independiente**: busqué en todo el repositorio los enunciados del
criterio (`anterior a F-017` / `anterior al corte`) y revisé los 20 sitios
vivos. Los cinco de arriba dicen lo mismo. `app.py:545` y
`resultado_consumer.py:60` también lo enuncian y **también traen la
salvedad**.

**Lo mejor de esta corrección no es el texto, es el test.** El guardián de
R23 se amplió con un bloque parametrizado sobre los cuatro sitios versionados
en este repositorio, que exige (a) que quien hable del corte nombre
`undo_log.actor`, y (b) que **ningún párrafo diga «exclusivamente» sobre un
`NULL` de autor sin la excepción en el mismo párrafo**. Es exactamente la
automejora que propuse en la primera vuelta, implementada como código en vez
de como norma que hay que recordar. Y excluye `azure-apps/partes.md` con el
motivo correcto: vive en otro repositorio y esta suite no puede depender de
él.

---

## Defecto 3 — El `printenv` y la M3 obsoleta · **CORREGIDO**

**M1 bis** ya no propone el comando peligroso. En su lugar hay un aviso
`⚠ Nunca con printenv a secas` que explica **por qué el `Select-String` no
protegía** —filtra lo que se muestra, no lo que el contenedor imprime— y
nombra los secretos que se habrían volcado (`PG_PASSWORD`, `GRAPH_KEY`,
`SESAME_API_KEY`, la credencial de Sigrid). Debajo, la forma segura: cuatro
invocaciones, una por variable, que no pueden imprimir nada más.

Un detalle que me convence de que no es cosmética: documentan también el
intento **fallido** de filtrar dentro del contenedor
(`sh -c 'printenv | grep CONTAINER_APP'` rompe el entrecomillado del `exec`) y
advierten de no insistir por ahí «si el entrecomillado se rompe, el comando
degenera en `printenv` a secas». Eso es lo que impide que alguien reinvente el
riesgo dentro de seis meses.

**M3 ya no está obsoleta**: consulta
`parte_registros.deleted_by` en vez de `undo_log.actor`, con una nota fechada
que explica que el camino antiguo no existe y que la consulta vieja «no habría
devuelto nada nuevo y se habría leído como un fallo de la feature».

---

## Residuales (no bloqueantes)

1. **`specs/F-017-identidad-easy-auth/design.md` conserva el criterio sin
   acotar** en tres puntos: línea 288 («vale para las **siete** columnas de
   autor a la vez» — son seis), línea 292 y línea 558
   («`autor IS NULL` ⇔ anterior a F-017. Es un criterio exacto»); y su boceto
   de código de la línea 384 mantiene el comentario viejo de `ACTOR_MAX_LEN`.
   **No bloquea** y no lo pedí en la primera vuelta: `design.md` es el plan
   tal como se aprobó, la norma vive en `requirements.md` —que ya está
   corregido y guardado por test—, y su tabla de anchos (línea 106) **sí dice
   la verdad**: «`undo_log.actor`: columna que hoy no escribe nadie». Aun así,
   es el único sitio del repositorio donde queda la redacción vieja; si se
   toca, con una nota fechada basta (no reescribir un plan en silencio).
2. **Tres formas de leer la identidad que el guardián no ve**
   (`os.getenv("DEFAULT_REVIEWER")`, `settings.model_dump()[…]`, y sobre todo
   `request.headers.get(CABECERA_NOMBRE)` importando la constante). Mejora
   barata para cuando toque: añadir al guardián que **solo `app.py` puede
   importar `CABECERA_*` de `identidad.py`**, y que `DEFAULT_REVIEWER` no se
   lee del entorno fuera de `config/settings.py`. Dos aserciones.
3. **`/whoami`** sigue calculando `senal` antes de `_resolver_identidad`
   (el campo `entorno` puede ir una petición por detrás en el instante en que
   se aprende la señal B, irrelevante estando desplegado) y es la única ruta
   sin `include_in_schema=False`. Cosmético, ya anotado en la primera vuelta.

## Avisos operativos para el humano

1. **Quedan cuatro `git worktree` registrados de la campaña de mutación**,
   apuntando a `5763e9f` (detached), con sus directorios todavía en disco:
   `…/Temp/mutacion_F-017_qgbzfpqf/wk_0..wk_3`. La campaña paralela **exige
   árbol limpio y crea sus worktrees desde `HEAD`**, así que conviene limpiar
   antes de la próxima: `git worktree prune` y borrar el directorio temporal.
   No afecta a este merge (`git status` está limpio), pero es basura que
   crece.
2. **La spec de F-018 que se está redactando en paralelo ya heredó el
   criterio sin acotar.** En el worktree de otro agente
   (`.claude/worktrees/agent-ad862e62640d64553/`, ignorado por git) hay un
   borrador de `specs/F-018-log-auditoria-portal/design.md` cuya línea 788
   dice «Que `NULL` en una columna de autor signifique “anterior a F-017”»,
   sin la excepción — porque se escribió contra la foto **anterior** a esta
   corrección (su copia de `requirements.md` todavía dice «exclusivamente»).
   Cuando esa spec aterrice hay que refrescarla contra el `dev` de después de
   F-017. Es justo el daño que el defecto 2 podía causar, pillado a tiempo.

---

## Cobertura requisito → test (25 requisitos)

Sin cambios respecto a la primera vuelta salvo lo que sigue; los 24 anteriores
siguen trazados y en verde.

| R | Test | Estado |
|---|---|---|
| R7 | `test_f017_identidad.py::test_f017_r7_siempre_hay_actor` + `test_f017_r24_consumer_firmado.py::test_f017_r24_ninguna_fila_nace_con_autor_nulo_tras_el_corte` | ✔ **ahora también fuera de la petición HTTP** |
| R10/R11 | `test_f017_punto_unico.py` (15 tests): recuento en `app.py`, ubicación en el resolutor, barrido por ruta, **barrido por AST de todo sv4**, el consumidor nombrado, y el autotest del guardián | ✔ **el hueco cerrado** |
| R18 | `test_f017_aprobacion_firmada.py::test_f017_r18_el_sobre_manda_en_el_consumidor` + los tres `::test_f017_r18_*` de `test_f017_r24_consumer_firmado.py` | ✔ |
| **R24** | `test_f017_r24_consumer_firmado.py`: `::_sobre_sin_usuario_se_sella_sin_identidad` (5 formas), `::_el_aviso_nombra_la_peticion`, `::_el_aviso_se_repite_por_mensaje`, `::_un_sobre_firmado_no_genera_aviso`, `::_el_marcado_se_completa_aunque_no_haya_firma`, `::_ninguna_fila_nace_con_autor_nulo_tras_el_corte` | ✔ nuevo |
| R23 | `tests/test_f017_r23_corte_documentado.py` + el bloque nuevo de propagación (4 sitios × 2 comprobaciones + el de `identidad.py`) | ✔ **ampliado** |

---

## Resumen de la primera vuelta (2026-08-20, CHANGES_REQUESTED)

Se conserva porque explica por qué la feature está donde está.

**Lo que ya estaba bien entonces y sigue estándolo**, verificado en su momento
contra el árbol y no leído del informe:

- **La enmienda de R14/R15 dice la verdad.** `undo_log.actor` no la escribe
  nadie (`_record_undo` ni siquiera acepta un actor); los nueve llamantes de
  `_record_undo` son todos ediciones, ninguno de los tres borrados ni el alta
  manual; `crear_parte_manual` declara `by` y lo usa **cero** veces (aparece
  solo en la firma, línea 2562); y no existe `created_by` en
  `parte_documents` ni en `parte_registros` donde persistir el alta. No era
  una excusa para tapar trabajo no hecho: era trabajo imposible dentro del
  alcance declarado, y se dijo en voz alta en vez de esconderlo.
- **R6, el espacio reservado, aguanta.** Intenté romperlo con mayúsculas,
  espacios de control, caracteres invisibles (`​`, `\xa0`), truncado y
  envenenamiento de una de las dos cabeceras. No cede: la comprobación se hace
  sobre el valor ya normalizado y ya truncado, que es el que se devuelve.
- **R5c y la asimetría del fallo**, cubiertas por tests que reproducen el
  escenario (creerse local estando desplegado) y comprueban **el valor sellado
  en la fila**, no solo `/whoami`.
- **`/whoami` no filtra nada**: ni token, ni claims, ni `oid`, ni valores de
  cabecera; el test lo comprueba sobre el texto crudo de la respuesta y
  congela el conjunto de claves.
- **R19**: el test de F-016 se reparó **fabricando la cabecera**, como
  prometía la spec, y se reforzó con dos tests nuevos en vez de debilitarse.
- **Mutación**: 31/31 reejecutados por mí; alcance y mutantes recalculados.

**Los tres defectos** por los que se rechazó son los tres que esta segunda
vuelta corrige. El defecto 1 —la tercera lectura de identidad en
`resultado_consumer.py`— no constaba en ningún informe: apareció barriendo a
mano las 22 asignaciones a columnas de autor de sv4.

---

## Automejora del arnés (propuesta, no aplicada)

Las tres de la primera vuelta siguen en pie; la primera y la tercera ya se han
demostrado útiles en esta misma feature.

1. **`CHECKPOINTS.md` / `.claude/agents/reviewer.md` — «la enmienda de un
   requisito se propaga».** Confirmado por los hechos: la enmienda de R14/R15
   se escribió bien en un documento y se quedó sin propagar a otros cuatro, y
   un borrador de F-018 en otro worktree ya la había heredado mal. Redacción
   propuesta para C3: *«Si algún requisito se enmendó durante la
   implementación, el informe de review lista los sitios donde la premisa
   antigua seguía enunciada y confirma que se corrigieron todos»*.
   **La feature ya trae la versión ejecutable de esto** (el bloque nuevo de
   `test_f017_r23_corte_documentado.py`): merece la pena señalarlo en
   `specs/SPECS.md` como patrón — cuando un hecho se enuncia en más de un
   documento, un test barato comprueba que todos dicen lo mismo.
2. **`harness/mutacion.py` — que el informe declare qué suite juzgó cada
   mutante.** Sigue haciendo falta razonarlo a mano en cada review.
3. **`.claude/agents/reviewer.md` — con 0 supervivientes, muestrear
   MUERTOS.** Reafirmada: un informe de mutación falso es más fácil de
   escribir sin supervivientes, porque no hay nada que muestrear y los totales
   cuadran solos. Reejecutar los 32 costó **91 s**.
4. **Nueva: `harness/mutacion.py` debe limpiar sus worktrees al terminar**
   (o `init.sh` avisar si quedan registrados). Han sobrevivido cuatro a la
   campaña, y la propia herramienta exige árbol limpio para la siguiente.
5. **Nueva: los timeouts de una campaña no deben poder confundirse con
   supervivientes ni con muertos.** Aquí se resolvió bien —se rehízo la
   campaña con más presupuesto—, pero conviene dejarlo escrito en
   `CHECKPOINTS.md`: *«una campaña con timeouts > 0 no es una medición
   válida; se repite con más presupuesto o menos concurrencia antes de
   juzgar»*.
