<!-- progress/review_F-014.md -->
# F-014 · Revisión — «Poner candef=9 en Sigrid a los recursos que registran jornada de 9 h»

- **Veredicto:** **CHANGES_REQUESTED** (2 cambios requeridos, ambos de texto,
  sobre `progress/peticion_F-014.md`).
- **Fecha:** 2026-08-19. Rama `feature/F-014-candef-9-sigrid`.
- **Alcance revisado:** commits `e04c575`, `3446c18`, `568b5dc` y `7970933`.
  Diff contra `dev`: 3 ficheros, 658 inserciones, 1 borrado
  (`progress/peticion_F-014.md`, `progress/impl_F-014.md`,
  `harness/features.json` — solo `pending` → `in_progress`).
  **Cero ficheros de código.** Coincide con lo declarado en el informe.

> **Lectura rápida.** El núcleo de la feature está **verificado y es
> correcto**: he re-ejecutado la línea base contra Sigrid en solo lectura y
> coincide dato por dato, el hallazgo 1 (códigos duplicados) es cierto y está
> bien medido, la desviación del encargo está justificada, y no hay ni un
> dato sensible en lo versionado. El rechazo es por **dos frases del
> documento que sale por correo**: una afirmación fáctica falsa y una tabla
> de resultado esperado incompleta. Se corrigen en minutos. Rechazo ahora
> porque la ventana para corregirlas se cierra en cuanto el correo se envíe.

---

## Nivel de rigor

Declarado en `harness/features.json`: **`documental`**. `harness/rigor.json`
lo define como `fase_red: false`, `cobertura: false`, `mutacion: false`.
Según la tabla de `CHECKPOINTS.md`, exige **C1–C3, C3 bis y C5**; **no**
exige fase RED, cobertura ni campaña de mutación.

**El nivel es el adecuado y no hay abuso de la etiqueta**: he comprobado el
diff completo y no contiene ni una línea de código ni de SQL de producción.
El SQL que aparece en `peticion_F-014.md` es SQL de **verificación en solo
lectura** destinado a ejecutarse a mano, no código desplegado. La
justificación del nivel documental se sostiene.

`bash harness/init.sh` imprime la puerta de cobertura con su motivo, como
exige la regla del N/A de `CHECKPOINTS.md`:
`[OK] PUERTA COBERTURA: N/A (F-014 es de nivel documental: no exige cobertura)`.

---

## 1. Verificación independiente de la línea base (RE-EJECUTADA)

**Sí he re-ejecutado las consultas**, en **solo lectura** (`POST
/api/sql/read`, base `ruesma`, vía `sigrid-api`), el 2026-08-19, con scripts
de usar y tirar en el scratchpad de sesión (fuera del repositorio).
**Cero escrituras**: las seis consultas son `SELECT` puros; no se ejecutó
ningún `UPDATE`/`INSERT`/`DELETE`. Las credenciales se leyeron en memoria de
`services/partes-persistencia/.env` y **no se han copiado a ningún fichero,
informe ni mensaje**.

No me he fiado del informe del implementer: he recalculado cada cifra.

### 1.1 H1 · Distribución de `candef` — COINCIDE

| `candef` | F-012 (08-18) | informe impl (08-19) | **mi medición (08-19)** | |
|---|---|---|---|---|
| 1.0 | 561 | 561 | **561** | ✅ |
| 0.0 | 199 | 199 | **199** | ✅ |
| 8.0 | 106 | 106 | **106** | ✅ |
| 9.0 | 1 | 1 | **1** | ✅ |

### 1.2 H2 · Única ficha con `candef = 9` — COINCIDE

Una sola fila: `res.ide` 2798044, `con.cod` `MO/0037`, `OFIC.2ª ALBAÑIL`,
`tiene_dni = 'sin'`, `n_he = 1`. Idéntico a H2 de F-012 y al informe.

### 1.3 H5 · Las 8 fichas — COINCIDE ÍNTEGRAMENTE

Mi ejecución de V3 devuelve exactamente las 8 filas de la tabla del informe:
todas `hora_defecto = 'HLOF'`, todas `fecbaj = 0`, `candef = 8.0` en las
siete y `9.0` en `MO/0037`, `tiene_dni = 'si'` en las siete y `'sin'` en
`MO/0037`. Los siete `res.ide` son los mismos que el anexo A de F-012
publica en su cláusula `IN (1555819, 2146402, 2146404, 1392590, 1336571,
2146403, 2714845)`, más 2798044.

Últimos partes registrados, medidos por mí: 2026-08-13 / **2026-02-04** /
2026-07-16 / 2026-08-13 / 2026-07-04 / 2026-08-17 / 2026-08-13, y 2026-08-19
para `MO/0037`. **Coinciden fila a fila con el informe.**

### 1.4 Patrón de negocio 9-9-9-9-6 — CONFIRMADO

Medido por mí para la cuadrilla en may–jun 2026, por día de semana:

| día | horas ordinarias | días |
|---|---|---|
| lunes | 9 | 49 |
| martes | 9 | 48 (+1 día de 10) |
| miércoles | 9 | 44 |
| jueves | 9 | 39 |
| **viernes** | **6** | **37** |

Sin ninguna otra combinación relevante. La justificación de negocio de la
petición (9 h L–J, 6 h el viernes = 42 h) **es exactamente lo que registran
los humanos**, no una interpretación.

### 1.5 Unicidad de la línea a modificar — CONFIRMADA

Comprobación que el informe afirma y que he verificado por mi cuenta: cada
una de las 8 fichas tiene **10 líneas de horas**, de las cuales **exactamente
1** es `HLOF` y **exactamente 1** cumple `reshor.horide = res.horide`, y son
la misma. La instrucción «la línea `HLOF`, la hora por defecto del recurso»
es **unívoca**: no hay forma de que RRHH acierte de ficha y falle de línea.
Este es el punto que más podía romper la petición y está sólido.

**Conclusión del criterio 1: la fidelidad de la línea base es total.** La
afirmación «nadie ha tocado nada entre el 08-18 y el 08-19» queda confirmada
por medición independiente, no por confianza.

---

## 2. ¿Es la petición ejecutable sin ambigüedad por alguien de fuera?

Busqué activamente huecos. Lo que **funciona bien** y merece constar:

- La instrucción operativa descansa en **tres datos simultáneos** (código +
  `res.ide` + categoría) con una regla de parada explícita: «Si al abrir una
  ficha los tres datos no cuadran a la vez, no la toques y pregunta». Es el
  diseño correcto para un cambio manual en datos maestros.
- El apartado 4 («Qué NO hay que tocar») es exhaustivo y anticipa los errores
  por exceso: otras líneas de horas, la tabla `auxhor`, otros recursos, las
  fichas homónimas, categorías/fechas, partes ya registrados.
- El apartado 5 es un procedimiento numerado de 5 pasos, autosuficiente.
- El bloque de correo (§7) es copiable y conserva la advertencia de
  duplicados y el identificador de ficha.

Y los **huecos reales** que encontré, que son el motivo del rechazo:

### 🔴 D1 (REQUERIDO) · Afirmación falsa en §3.1: «la única con partes en 2026»

`peticion_F-014.md` §3.1 dice:

> «La ficha correcta es, en los cinco casos con código repetido, **la única
> que tiene partes registrados en 2026**; las demás no registran nada desde
> 2013, 2019, 2024 o mayo de 2025.»

**Las dos mitades de la frase son falsas.** Medido por mí, listando *todas*
las fichas de esos 8 códigos (21 fichas):

- **`MO/0031` tiene DOS fichas con partes en 2026**: la correcta (2714845,
  OFIC. 1ª ALBAÑIL, último parte 2026-08-13) y **537335 (ENCARGADO DE OBRA,
  hora por defecto `MENC`, `candef` 1.0, de alta, último parte
  **2026-01-30**)». El criterio «la única con partes en 2026» **no
  desambigua** en ese caso.
- La enumeración «2013, 2019, 2024 o mayo de 2025» **omite** homónimas cuyo
  último parte es de **2011** (537312), **2020** (537314), **2022**
  (1990968), **2023** (537313) y **2026-01** (537335).

**Gravedad: media.** El daño práctico está contenido —quien aplique ese
criterio en `MO/0031` encuentra dos candidatas, y la categoría de la tabla
(OFIC. 1ª ALBAÑIL vs ENCARGADO DE OBRA) desempata al instante, además de que
la regla de parada obliga a preguntar— pero es una **afirmación fáctica
falsa en un documento que va a salir por correo a un tercero** y que sirve
para justificar por qué la tabla es fiable. Un documento que pide precisión
a RRHH no puede permitirse ser impreciso él.

**Qué cambiar:** sustituir la frase por el criterio verdadero, que además es
más simple y ya está en la tabla: *«la ficha correcta es siempre la que
cumple a la vez el código, el identificador y la categoría de la tabla 3.2;
la columna “último parte registrado” está para confirmarlo. Ojo: en
`MO/0031` hay otra ficha de alta que también registra partes en 2026
(ENCARGADO DE OBRA), así que ahí la categoría es la que desempata»*.

### 🔴 D2 (REQUERIDO) · V2 no cubre el escenario alternativo de `MO/0007`

La petición abre explícitamente **dos salidas** para `MO/0007` (§3.2) y
propaga esa bifurcación a V1 (8 filas vs 7) y a V3 (mención del `fecbaj`).
**V2 no la propaga**: su tabla de resultado esperado solo declara el
escenario «se cambian los 7», y cierra con «Si aparece cualquier otro valor
de `candef` o si las filas de 1.0 y 0.0 se mueven, se ha tocado algo que no
tocaba» — lo que **no dice nada** sobre qué hacer si 8.0 sale 100 en vez
de 99.

Los tres escenarios posibles, calculados sobre la línea base que yo mismo he
medido (106 / 1):

| escenario | `8.0` esperado | `9.0` esperado | nota |
|---|---|---|---|
| A. se cambian los 7 (incluido `MO/0007`) | **99** | **8** | el único declarado hoy |
| B. `MO/0007` se queda de alta y **sin tocar** | **100** | **7** | no declarado |
| C. `MO/0007` recibe la **baja** que le falta | **99** | **7** | no declarado; además el universo baja de 867 a 866, porque `fecbaj ≠ 0` lo saca del filtro de las tres consultas |

**Gravedad: media.** Es un defecto en el criterio de `acceptance` 2 —el que
esta revisión debe juzgar como «bien especificado»—, y afecta justo a la
consulta que la petición llama **control de daños**. Tal y como está, el
escenario B produciría una falsa alarma de «se ha tocado algo que no
tocaba», y el escenario C es indistinguible del A mirando solo la fila 8.0.

**Qué cambiar:** añadir a la tabla de V2 las dos columnas de escenario (o
tres filas de escenario), y mencionar que en el caso C el total de recursos
de alta con hora por defecto baja en 1.

### 🟡 D3 (menor, cosmético) · La categoría de `MO/0037` no es literal

La petición escribe «OFIC. 2ª ALBAÑIL» (con espacio tras el punto); el
literal real en Sigrid es **`OFIC.2ª ALBAÑIL`** (sin espacio) — y sí lleva
espacio en `OFIC. 1ª ALBAÑIL`, que es una inconsistencia de los propios
datos maestros. Dado que la petición ordena «si los tres datos no cuadran a
la vez, no la toques y pregunta», una diferencia tipográfica puede generar
una consulta innecesaria. Afecta a §3.3, al anexo y al correo.

### 🟡 D4 (menor) · §4 dice «entre 2 y 10 líneas de horas»

Las ocho fichas tienen **exactamente 10** líneas de horas (medido). La
horquilla no es falsa pero es innecesariamente vaga en un documento cuyo
valor es la precisión.

### 🟡 D5 (menor) · El correo (§7) no advierte del caso `MO/0031`

El bloque copiable lleva la advertencia genérica de códigos duplicados y el
identificador de ficha —que es lo que de verdad protege—, pero no menciona
que bajo `MO/0031` hay otra ficha de alta *que también registra en 2026*.
Con D1 corregido, conviene que la advertencia del correo lo recoja.

---

## 3. La desviación declarada del encargo (hallazgo 1)

El encargo pedía citar los recursos **solo** por código `MO/NNNN`; el
implementer añadió `res.ide`. Juzgo los tres puntos por separado.

### (a) ¿El hallazgo de códigos duplicados es cierto y está bien medido? **SÍ**

Recalculado por mí, y coincide **exactamente** con la tabla del informe:

| código | fichas (informe) | **fichas (mi medición)** | de alta (informe) | **de alta (mi medición)** |
|---|---|---|---|---|
| `MO/0006` | 5 | **5** | 4 | **4** |
| `MO/0007` | 5 | **5** | 4 | **4** |
| `MO/0008` | 4 | **4** | 3 | **3** |
| `MO/0031` | 2 | **2** | 2 | **2** |
| `MO/0037` | 2 | **2** | 1 | **1** |
| `MO/0366` / `MO/0405` / `MO/0456` | 1 | **1** | 1 | **1** |

Y he confirmado que las confusiones **no son teóricas**: bajo `MO/0006`
existe la ficha 1335318, también **de alta**, también **OFIC. 1ª ALBAÑIL**,
también con hora por defecto **`HLOF`** y también con **`candef = 8`** — es
decir, indistinguible de la correcta salvo por `res.ide` y por la fecha del
último parte. Lo mismo con 1335319 y 1984734 bajo `MO/0007`, y 1335320 bajo
`MO/0008`. **Sin `res.ide`, RRHH tenía cuatro maneras de corregir la ficha
equivocada, y ninguna forma de darse cuenta.**

### (b) ¿Es `res.ide` un identificador técnico y no un dato personal? **SÍ**

Es la clave primaria de la fila de la tabla `res` (ficha de **recurso**, no
de persona). No es un DNI, no es un nombre, no es un número de afiliación, y
fuera de Sigrid no identifica a nadie. Además —y esto zanja el debate— **ya
está versionado en este repositorio desde F-012**: el anexo A de
`specs/F-012-estudio-jornada-semanal/design.md` publica literalmente
`WHERE res.ide IN (1555819, 2146402, 2146404, 1392590, 1336571, 2146403,
2714845)`. Publicarlo en F-014 no añade ninguna exposición nueva.

Conviene además notar la distinción que el propio dominio hace y que
`CHECKPOINTS.md` C3 vigila: **empleado ≠ recurso**. `res.ide` es el recurso;
el dato personal vive en `emp` (vía `res.conide`), y ni `emp.ide` ni `emp.dni`
aparecen en ningún fichero versionado por esta feature.

### (c) ¿Estaba justificada la desviación, o debió pararse y consultar? **JUSTIFICADA**

Doy por buena la desviación, por tres razones:

1. **La restricción del encargo se respeta en su intención, que era «no
   versionar DNIs ni nombres».** Eso se cumple íntegramente (ver §4). Lo que
   el implementer desvió fue la *letra* («solo por código»), no el *motivo*.
2. **Cumplir la letra habría producido una petición ejecutable de forma
   incorrecta**, que es precisamente el daño que F-014 existe para evitar.
   Una petición que manda a RRHH a tocar datos maestros con un identificador
   ambiguo no es una petición conservadora: es una petición peligrosa.
3. **La desviación está declarada, no escondida**: aparece como «Hallazgo 1
   (importante)», como «Decisión 2 · la única desviación respecto a la letra
   del encargo» y con su medición completa. Un implementer que documenta su
   desviación con los números que la justifican está haciendo exactamente lo
   que el arnés le pide.

Matiz para el líder, sin efecto sobre el veredicto: el protocolo de
`CLAUDE.md` («si el trabajo revela que la propuesta era incorrecta, para y
vuelve a proponer») habría admitido también parar y consultar. No lo exijo
aquí porque el cambio **amplía** la información sin violar ninguna regla dura
y sin coste reversible, y porque el dato añadido ya estaba versionado. Si la
desviación hubiera ido en dirección contraria —quitar información, o añadir
un dato personal— el veredicto sería otro.

---

## 4. Datos sensibles en lo versionado — LIMPIO

Barrido ejecutado **por mí** sobre `progress/peticion_F-014.md` y
`progress/impl_F-014.md` (no me fío del informe del implementer), con estos
patrones:

| patrón | resultado |
|---|---|
| DNI/NIE español `\b[0-9]{7,8}-?[A-Za-z]\b` | **0 coincidencias** |
| `https?://`, `azurewebsites`, `.net/` | **0 coincidencias** |
| `functions-key=`, `api[_-]?key=`, `Bearer `, `sk-` | **0 coincidencias** |
| `password`, `contrasen` | **0 coincidencias** |
| `tenant`, `subscription` | **0 coincidencias** |

Además, por lectura completa de ambos ficheros: **no aparece ningún nombre
de persona**. Los trabajadores se citan por código de recurso, identificador
de ficha y categoría profesional. El único dato personal mencionado es la
*existencia o ausencia* de DNI (`tiene_dni = 'si'/'sin'`), nunca su valor —
y el SQL está deliberadamente escrito para no traerlo (`CASE WHEN ... THEN
'sin' ELSE 'si' END`), igual que el anexo A de F-012.

El recorte de código Python de §6 **lee** las credenciales de `.env` pero no
las imprime ni las incrusta. Correcto.

**Regla dura de `CLAUDE.md` sobre secretos: CUMPLIDA.**

---

## 5. Hallazgo 2 (`MO/0007` sin partes desde 2026-02-04) — TRATAMIENTO CORRECTO

**Los hechos, verificados por mí**: ficha 2146403, de alta (`fecbaj = 0`),
**22 líneas** en `hmores` en 2026, primera 2026-01-07, última **2026-02-04**.
Coincide al detalle con el informe. Confirmado también que su histórico de
2026 es previo a mayo, es decir **nunca llegó a hacer el régimen de 9 h**,
que arrancó en mayo (§1.4).

**Juzgo el tratamiento correcto, y además es el punto de mejor criterio de
toda la feature.** Las alternativas eran las dos peores:

- *Incluirlo sin marcar* → se le pone `candef = 9` a alguien que quizá ya no
  está, con el efecto de que si vuelve a registrar, el portal le calcularía
  42 h semanales sin base.
- *Sacarlo por su cuenta* → el equipo de partes decidiendo sobre la plantilla
  de RRHH con datos que no le corresponden.

El implementer eligió la tercera: **incluirlo, marcarlo con ⚠, escribir las
dos salidas y devolver la decisión a quien tiene el dato** (RRHH sabe si esa
persona sigue en la cuadrilla; el equipo de partes no). Y —lo importante—
**propagó la bifurcación al resultado esperado de la verificación**: V1 con 8
filas o 7 según la decisión, y una petición explícita de que RRHH comunique
cuál eligió. Eso convierte una incógnita en una variable controlada.

La única pega es que **esa propagación no llegó a V2**, que es el defecto D2
de arriba. El tratamiento es correcto; su propagación está incompleta.

---

## 6. La verificación posterior (acceptance 2) — BIEN ESPECIFICADA, con la salvedad D2

Revisé el SQL con ojo crítico, contrastándolo contra el anexo A de F-012 y
ejecutando las tres consultas contra Sigrid para comprobar que **corren tal
cual** (lo hacen: HTTP 200, sin error de sintaxis, sin truncar).

| aspecto | juicio |
|---|---|
| **V1 reproducible** | ✅ Corre tal cual. Es la consulta H2 del anexo A, ampliada con `LTRIM(RTRIM(...)) = ''` y con `ORDER BY con.cod`. La ampliación es una **mejora**: el anexo A original solo miraba `IS NULL`, y un DNI grabado como cadena vacía habría pasado por bueno. |
| **V2 reproducible** | ✅ Corre tal cual. Es literalmente la consulta H1 del anexo A, sin modificar. |
| **V3 reproducible** | ✅ Corre tal cual. Deriva de la última consulta del anexo A (la de categoría/DNI/HE del grupo H5), con `auxhor.cod` y `fecbaj` añadidos y el `IN` ampliado con 2798044. |
| **Aritmética de V2** | ✅ **Cuadra**: 106 − 7 = **99** y 1 + 7 = **8**, sobre la línea base 106/1 que yo mismo he medido. ⚠️ Pero solo para el escenario A → **D2**. |
| **Consistencia V1 ↔ V3** | ✅ Son consistentes y **deliberadamente distintas**: V1 filtra por `fecbaj` (universo de vivos), V3 **no** filtra y devuelve `fecbaj` como columna. Eso es lo correcto: si RRHH da de baja a `MO/0007`, desaparece de V1 pero **sigue siendo auditable en V3**. Está bien pensado, no es un descuido. |
| **Consistencia V1 ↔ V3 en `candef`** | ✅ V1 filtra `reshor.candef = 9` con `reshor.horide = res.horide`; V3 usa `MAX(r3.candef)` con el mismo filtro. Son equivalentes **porque hay exactamente 1 fila** por ficha, cosa que he verificado (§1.5). |
| **`tiene_dni` cubre `res.conide = 0`** | ✅ **Sí, y lo he comprobado explícitamente.** `MO/0037` tiene `res.conide = 0`; el `LEFT JOIN emp ON emp.ide = res.conide` no encuentra pareja **porque no existe ninguna fila `emp` con `ide = 0`** (lo consulté: `COUNT(*) = 0`), luego `emp.dni` es `NULL` → `'sin'`. Era el caso borde exacto que podía dar un falso `'si'`, y no lo da. |
| **Resultado esperado sin ambigüedad** | ⚠️ **Casi**: V1 y V3 declaran su bifurcación; **V2 no** → **D2**. |
| **Método de lanzamiento** | ✅ Recorte de código incluido, `sigrid-api` como único acceso (regla dura), `max_rows` 1000 declarado, script fuera del repositorio. |

**Este criterio NO se da por ejecutado**, y así consta: depende de que RRHH
haga el cambio en Sigrid. Lo que apruebo es que la verificación esté **bien
especificada**; con D2 corregido, lo estará por completo.

---

## 7. Recorrido de `CHECKPOINTS.md`

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina en verde (`ENTORNO LISTO`), ejecutado
      por mí con el **comando limpio**, sin pipes ni decoración. Suite raíz
      `15 passed in 3.99s`; sv3, sv4 y sv5 en verde; sv1, sv2 e `infra` con
      el AVISO preexistente de «sin directorio de tests» (deuda previa, no
      introducida por F-014); `ruff` 430 avisos (deuda previa declarada).
- [x] Existen los 8 ficheros obligatorios (verificado por `init.sh`).

### C2 — El estado es coherente

- [x] Una sola feature `in_progress`: `['F-014']`.
- [x] Rama actual `feature/F-014-candef-9-sigrid`, nunca `main` ni `dev`.
- [ ] **`progress/current.md` NO describe la sesión activa**: sigue diciendo
      «Ninguna feature `in_progress`. Última sesión: 2026-08-18», mientras
      `features.json` marca F-014 `in_progress`. **No es defecto del
      implementer** —el encargo le prohibió expresamente tocarlo, y el mío
      también—: es una **acción pendiente del líder** al cerrar la sesión,
      que además debe dejar la feature `blocked`. Lo dejo sin marcar para que
      no se pierda, no como cargo contra el trabajo revisado.
- [x] Toda feature `done` tiene su resumen en `history.md` (F-014 no es
      `done`, así que no aplica en su caso).

### C3 — El código respeta arquitectura y convenciones

- **N/A justificado: la feature no contiene código.** Verificado por mí con
  `git diff --stat dev...HEAD`: los únicos ficheros del diff son dos
  Markdown en `progress/` y un cambio de una línea de estado en
  `harness/features.json`. No hay capas que violar, no hay ficheros de
  código cuya primera línea comprobar, no hay `print()` de depuración, no
  hay dependencias nuevas. Las tres trampas del monorepo (empleado ≠
  recurso, incidencias sin horas, `orm_models.py` duplicado) no se tocan.
  - Observación a favor: el documento **respeta** la distinción empleado ≠
    recurso con precisión —habla siempre de «ficha de recurso» y, para el
    DNI, de «enlazar la ficha de recurso con su ficha de empleado»—, que es
    exactamente el modelo real (`res.conide → emp`).
- [x] Sin secretos hardcodeados (barrido de §4).

### C3 bis — Documentos que entran de fuera

- **N/A justificado: F-014 no añade ni modifica ningún fichero en
  `docs/referencia/`.** Ambos entregables viven en `progress/`, y la
  decisión 1 del informe explica por qué (`docs/referencia/` es para
  documentación que **llega de fuera** convertida a Markdown; esto es un
  documento propio y efímero). Comparto el criterio. No hay PDF ni
  ofimática en el árbol ni en el historial de la rama.
- No obstante, **el barrido de datos sensibles sí lo he ejecutado igualmente**
  sobre los dos Markdown, con los patrones listados en §4, porque el
  documento está pensado para salir por correo. Resultado: limpio.

### C4 — La verificación es real

- [x] Criterio `acceptance` 1 (petición redactada): **cumplido**, con las
      salvedades D1/D2/D3/D4/D5.
- [ ] Criterio `acceptance` 2 (verificación tras el cambio): **especificado,
      NO ejecutado**, y **no puede estarlo hoy**: depende de que RRHH ejecute
      el cambio en Sigrid. **No lo apruebo como ejecutado.** Queda pendiente
      de cierre (§8).
- [x] Criterio `acceptance` 3 (`init.sh` en verde): **cumplido**, verificado
      por mí.
- **Tests trazables `test_fXXX_rN_*`: N/A justificado.** No hay código que
  testear; el «test» de esta feature es la ejecución de V1/V2/V3 contra
  Sigrid, que por naturaleza toca un sistema externo y por tanto **no puede
  ser un unit test** (los unit tests de este repositorio no tocan red ni
  BBDD, y así sigue siendo: F-014 no añade ninguno que lo haga).
- [ ] **Las verificaciones MANUAL no están listadas en
      `progress/current.md`.** Están, bien redactadas, en
      `progress/impl_F-014.md` §«Qué queda pendiente», pero `CHECKPOINTS.md`
      C4 pide que vivan en `current.md`. **Acción del líder al cerrar
      sesión**, no del implementer (que tenía prohibido tocar ese fichero).

### C4 bis — El rigor declarado se cumple

- [x] La feature declara `rigor: "documental"`, valor válido presente en
      `harness/rigor.json`. `init.sh` lo valida.
- **Fase RED: N/A justificado por el nivel.** `harness/rigor.json` fija
  `fase_red: false` para `documental`, y `CHECKPOINTS.md` lo confirma
  («Sin fase RED»). El motivo material: **no hay código de producción cuyo
  fallo previo pudiera enseñarse**, ni test que romper. No es una puerta
  omitida por comodidad; es una puerta sin objeto.
- **Cobertura: N/A justificado, con el motivo impreso por la propia
  herramienta**, como exige la regla del N/A:
  `[OK] PUERTA COBERTURA: N/A (F-014 es de nivel documental: no exige
  cobertura)`. No hay líneas cambiadas que cubrir.
- **Mutación: N/A justificado por el nivel** (`mutacion: false`). Además,
  **hice la prueba de control que exige mi protocolo** para no confundir
  «nada que mutar» con «generador roto»: el diff de la rama son tres
  ficheros, dos `.md` y un `.json`; **no contiene ni un fichero `.py`**, de
  modo que `harness.mutacion` no tendría sobre qué operar ni siquiera
  ignorando la exclusión de alcance. El cero es estructural, no sospechoso.
  No existe `progress/mutacion_F-014.md` y **no debe existir**.
- [x] Supervivientes: sin campaña, no hay supervivientes que analizar.
- [x] **La sección «Evidencias» existe y trae los cuatro números**: tests
      (15 passed, 0 failed, + sv3/sv4/sv5), cobertura (N/A con el motivo de
      la puerta), mutantes/supervivientes (N/A con motivo estructural) y
      tiempo de la suite (4.59 s). Añade además consultas a Sigrid y
      ficheros de producción tocados (0). Cumple.
- [x] Ningún punto marcado N/A sin justificación escrita: los cuatro N/A de
      arriba llevan su motivo por escrito **en este informe**, no solo en el
      del implementer.

### C4 ter — Rutas sensibles

- **N/A: `harness/rutas_sensibles.json` no existe** en este repositorio.
  Según `CHECKPOINTS.md`, «sin esa declaración este bloque es N/A y no hay
  nada que justificar».

### C5 — La sesión se cerró bien

- **`tasks.md`: N/A justificado por `sdd: false`.** La nota de cabecera de
  `CHECKPOINTS.md` lo declara N/A para estas features y sustituye el formato
  de commit por `F-XXX: <descripción>`. Los commits lo cumplen, y de hecho
  van más allá usando el formato `F-014 Tn:` de las features con spec.
- [x] Sin ficheros temporales ni artefactos sin trackear: `git status
      --porcelain` **vacío**. Los scripts de línea base viven fuera del
      repositorio (scratchpad), como declara el informe; los míos de esta
      revisión, también.
- [x] `features.json` refleja el estado real (`in_progress`). Deberá pasar a
      `blocked` al cerrar la sesión (§8).
- 🟡 **Menor:** la sección «Commits» de `impl_F-014.md` lista `e04c575` y
      `3446c18`, pero **no** `568b5dc` («fijar en el informe el hash real
      del commit T2»), que es el commit que corrigió esa misma sección. Es
      inherente al problema del pez que se muerde la cola y no engaña a
      nadie, pero conviene añadir la línea.

---

## 8. Qué falta exactamente para el cierre definitivo

F-014 **no puede cerrarse como `done` hoy**, y coincido plenamente con esa
lectura. Lo que falta, en orden:

| # | Qué | Quién | Bloquea el cierre |
|---|---|---|---|
| 0 | **Corregir D1 y D2** en `progress/peticion_F-014.md` (y, si se quiere, D3/D4/D5) | implementer | **Sí, y antes de enviar el correo** |
| 1 | Enviar la petición a RRHH/Administración (bloque §7) | humano | Sí |
| 2 | RRHH ejecuta en Sigrid: `candef` 8 → 9 en la línea `HLOF` de las 7 fichas (o 6), y el DNI de `MO/0037` | RRHH | Sí |
| 3 | RRHH comunica **qué decidió con `MO/0007`** | RRHH | Sí — sin esa respuesta el esperado de V1 y V2 es ambiguo |
| 4 | Ejecutar V1, V2 y V3 en solo lectura y anotar el **resultado real** en `progress/impl_F-014.md` | equipo de partes | Sí — es el `acceptance` 2 |
| 5 | Nueva revisión que verifique el punto 4 | reviewer | Sí |

Y dos acciones del **líder** al cerrar la sesión de hoy, ambas señaladas
arriba:

- Dejar F-014 en **`blocked`** en `harness/features.json`, con el motivo
  («a la espera de que RRHH ejecute el cambio en Sigrid»).
- Actualizar `progress/current.md`: describir la sesión activa y **añadir las
  verificaciones MANUAL de F-014** a la lista acumulada, con su comando
  exacto (C4).

**Recordatorio de orden duro, que esta feature confirma como vigente:**
**F-015 no debe mergearse hasta que el punto 4 salga en verde.** Es el riesgo
§10.6 de F-012, y mi medición de §1.4 lo respalda con datos frescos: con la
cuadrilla aún a `candef = 8`, la regla nueva marcaría sus viernes de 6 h como
jornada incompleta y generaría **+2 h/semana de extra automática falsa** por
trabajador (caso L de la tabla de escenarios de F-012).

---

## 9. Cambios requeridos (numerados y accionables)

**Bloqueantes** (los dos, sobre `progress/peticion_F-014.md`):

1. **§3.1, párrafo final** — Eliminar la afirmación «La ficha correcta es […]
   la única que tiene partes registrados en 2026; las demás no registran nada
   desde 2013, 2019, 2024 o mayo de 2025», que es **falsa en sus dos
   mitades**. Sustituirla por el criterio real (código + `res.ide` +
   categoría, los tres a la vez) y advertir del caso concreto: bajo
   `MO/0031` hay una segunda ficha **de alta y con partes en 2026**
   (`res.ide` 537335, ENCARGADO DE OBRA, hora por defecto `MENC`, último
   parte 2026-01-30); ahí desempata la **categoría**. Detalle y evidencia en
   §2/D1 de este informe.

2. **§6, tabla de resultado esperado de V2** — Completar los **tres**
   escenarios en vez de uno solo, propagando a V2 la bifurcación de
   `MO/0007` que V1 y V3 ya recogen:
   - A (se cambian los 7): `8.0` → **99**, `9.0` → **8**;
   - B (`MO/0007` de alta y sin tocar): `8.0` → **100**, `9.0` → **7**;
   - C (`MO/0007` recibe la baja): `8.0` → **99**, `9.0` → **7**, y el total
     de recursos de alta con hora por defecto baja de 867 a 866 porque
     `fecbaj ≠ 0` lo saca del filtro.
   Ajustar en consecuencia la frase «Si aparece cualquier otro valor de
   `candef` […] se ha tocado algo que no tocaba», que hoy no contempla que
   la fila 8.0 salga 100 legítimamente.

**No bloqueantes** (recomendados, se pueden hacer en la misma pasada):

3. Corregir el literal de la categoría de `MO/0037` a **`OFIC.2ª ALBAÑIL`**
   (sin espacio tras el punto) en §3.3, en el anexo y en el correo (§7), para
   que cuadre carácter a carácter con lo que RRHH verá en pantalla (D3).
4. §4: sustituir «entre 2 y 10 líneas de horas» por **«10 líneas de horas»**,
   que es el dato real medido para las ocho fichas (D4).
5. §7 (correo): recoger en la advertencia de duplicados el caso `MO/0031`,
   una vez corregido el punto 1 (D5).
6. `progress/impl_F-014.md`, sección «Commits»: añadir `568b5dc` (D6/C5).

---

## 10. Lo que esta feature hace bien (para que no se pierda al releer)

No es cortesía: son decisiones que conviene repetir en features futuras.

1. **Medir la línea base el mismo día de redactar la petición**, en vez de
   confiar en un estudio de la víspera. Convierte «suponemos que nadie ha
   tocado nada» en un hecho comprobado.
2. **Tres verificaciones en vez de una.** V2 como *control de daños* es la
   idea más valiosa del documento: un cambio manual de datos maestros falla
   por exceso tanto como por defecto, y nadie lo miraría si no estuviera
   escrito.
3. **Escribir el resultado esperado fila a fila antes de que el cambio
   ocurra.** Es lo que impide que la verificación posterior se convierta en
   «parece que está bien».
4. **Devolver a RRHH la decisión que es de RRHH** (`MO/0007`) en vez de
   suponerla, y propagar la bifurcación al resultado esperado.
5. **Declarar la desviación del encargo con los números que la justifican**,
   en vez de aplicarla en silencio o de cumplir la letra a sabiendas de que
   producía un documento peligroso.

---

## 11. Automejora propuesta (no aplicada — decide el humano)

Dos propuestas, ambas nacidas de lo que esta revisión ha tenido que
improvisar:

**A) `CHECKPOINTS.md` — un bloque para features cuyo entregable es una
petición a un tercero.** F-014 no es la última de su especie: hay cambios que
solo puede ejecutar un humano fuera del sistema (RRHH en Sigrid, un
administrador en Azure, un proveedor). El arnés no tiene hoy checkpoints para
ese formato, y he tenido que derivarlos sobre la marcha. Propongo un **C6 —
Peticiones a terceros** (o un `C3 ter`), aplicable solo si la feature entrega
un documento destinado a ejecutarse fuera:

- [ ] Cada objeto a modificar se identifica por una clave **verificada como
      unívoca**, no por un código legible que el reviewer da por bueno.
- [ ] El documento incluye un apartado explícito de **qué NO se toca**.
- [ ] La verificación posterior está escrita **antes** del cambio, con su
      resultado esperado, e incluye un **control de daños** (que no se haya
      movido nada más).
- [ ] Si el documento admite **escenarios alternativos**, TODOS los pasos de
      verificación declaran su resultado esperado en CADA escenario. *(Este
      punto es literalmente el defecto D2 de F-014.)*
- [ ] Barrido de datos sensibles ejecutado por el reviewer, porque el
      documento **sale del repositorio**.

**B) Protocolo del reviewer — verificación independiente también fuera de la
mutación.** El protocolo obliga hoy a recalcular por mi cuenta los totales de
la campaña de mutación («es la única defensa contra un informe escrito a
mano»), pero no dice nada equivalente para una feature **documental cuyo
contenido son mediciones**. El mismo riesgo existe: un informe con cifras
inventadas pasaría solo con leerlo. Propongo generalizar la regla: *«cuando
el entregable de una feature sea una medición, el reviewer la re-ejecuta —en
solo lectura— en vez de leerla»*. En esta revisión fue lo que permitió
confirmar la línea base **y** encontrar D1, que ninguna lectura del informe
habría detectado.

---

**Veredicto final: CHANGES_REQUESTED.** Dos correcciones de texto (§9.1 y
§9.2) sobre un trabajo que, en todo lo demás, está verificado punto por punto
y es de buena calidad. La línea base es fiel, el hallazgo de los códigos
duplicados es cierto y salva la feature de causar el daño que venía a evitar,
la desviación del encargo está justificada y declarada, y no hay ni un dato
sensible en lo versionado. Rechazo ahora, y no después, porque las dos
correcciones dejan de ser posibles en el momento en que el correo salga.

---
---

# Segunda pasada — 2026-08-19

- **Veredicto: APROBADO** (la parte entregada: petición + línea base +
  verificación especificada). El `acceptance` 2 **sigue sin ejecutarse** y no
  puede ejecutarse hoy: la feature **no se cierra** (§S8).
- **Alcance de esta pasada:** commit `96a9035` («F-014 T3: correcciones tras
  revisión»), diff `568b5dc..HEAD`: 3 ficheros, 215 inserciones, 33
  borrados. `harness/features.json` **no lo tocó T3** (su única línea de diff
  sigue siendo el `pending` → `in_progress` del líder en `7970933`), y
  `progress/current.md` sigue intacto. Correcto: son acciones del líder.
- **Método:** reviso **solo lo que cambia**. No repito el recorrido de lo que
  di por verificado en la primera pasada (línea base, hallazgo 1, desviación
  del encargo, C1–C5 en lo no afectado). Sí re-mido **cada afirmación fáctica
  nueva** que introdujo T3, en solo lectura, en vez de leerla.

## S1 · D1 — Corregido, y el texto nuevo es verdadero

La afirmación falsa **ha desaparecido**: `grep` de «única con partes en
2026» y de «2013, 2019, 2024» sobre `peticion_F-014.md` devuelve **0
coincidencias**. En su lugar, §3.1 dice ahora tres cosas, y he verificado las
tres contra Sigrid:

| afirmación nueva de §3.1 | mi verificación |
|---|---|
| «El criterio es que coincidan a la vez código, identificador y categoría; “último parte” está solo para confirmarlo, **no** como criterio de selección» | ✅ Correcto, y es el criterio que la primera pasada pedía. Degradar la fecha a confirmatoria es exactamente lo que había que hacer. |
| «De los tres, **el que decide siempre es el identificador**: bajo `MO/0006`, `MO/0007` y `MO/0008` hay otras fichas de alta, también OFIC. 1ª ALBAÑIL, también `HLOF`, también con cantidad por defecto 8» | ✅ **Verdadero.** Confirmado: 1335318 (`MO/0006`), 1335319 y 1984734 (`MO/0007`), 1335320 (`MO/0008`) — todas `fecbaj = 0`, `OFIC. 1ª ALBAÑIL`, `HLOF`, `candef` 8. Indistinguibles salvo por `res.ide`. |
| Recuadro ⚠️ «`MO/0031`: sus dos fichas están de alta y **las dos registran partes en 2026**; la correcta es OFIC. 1ª ALBAÑIL (2714845); la otra es ENCARGADO DE OBRA (537335, hora por defecto `MENC`, cantidad por defecto 1). **A esa segunda no se le toca nada**» | ✅ **Verdadero dato por dato.** Re-consultado hoy: 537335 = ENCARGADO DE OBRA, `MENC`, `candef` **1.0**, `fecbaj` **0**, último parte **2026-01-30**, **1 línea** en 2026; 2714845 = OFIC. 1ª ALBAÑIL, `HLOF`, `candef` 8.0, `fecbaj` 0, último parte 2026-08-13, 120 líneas en 2026. |

**El caso `MO/0031` queda advertido sin ambigüedad**, y de la forma correcta:
en un recuadro destacado, con los **dos** identificadores, diciendo cuál se
cambia y cuál no se toca. Además está replicado en el correo (§S3).

**No introduce ninguna afirmación fáctica nueva que no se sostenga.** Busqué
específicamente eso: las tres afirmaciones de arriba son las únicas nuevas
del apartado, y las tres están medidas.

Un matiz que examiné y que **no** es defecto: §3.1 dice «el que decide
siempre es el identificador» y el recuadro dice que en `MO/0031` «se
distinguen por la categoría». No es contradicción — en `MO/0031` los dos
datos apuntan a la misma ficha (2714845 **y** OFIC. 1ª ALBAÑIL), la categoría
es una pista adicional legible en pantalla, y la regla de parada de cierre
(«si los tres datos no cuadran a la vez, no la toques y pregunta») sigue
gobernando. No hay lectura doble posible.

## S2 · D2 — Corregido; los tres escenarios son correctos y B ya no da falsa alarma

La tabla de V2 pasa de una columna a tres. Contrastada contra los números que
yo mismo medí (106/1) y contra el universo, que **he recontado hoy**
(`COUNT(*) = 867`, exacto):

| `candef` | ANTES | A (los 7) | B (`MO/0007` sin tocar) | C (`MO/0007` de baja) | mi juicio |
|---|---|---|---|---|---|
| 1.0 | 561 | 561 | 561 | 561 | ✅ |
| 0.0 | 199 | 199 | 199 | 199 | ✅ |
| 8.0 | 106 | **99** (106−7) | **100** (106−6) | **99** (106−6−1) | ✅ los tres |
| 9.0 | 1 | **8** (1+7) | **7** (1+6) | **7** (1+6) | ✅ los tres |
| total | 867 | 867 | 867 | **866** | ✅ |

Coincide **exactamente** con los números que exigí en §9.2 de la primera
pasada. La aritmética de C es la que tenía trampa y está bien resuelta: 106
menos los 6 que suben a 9, menos 1 porque `fecbaj ≠ 0` saca la ficha del
filtro; y el universo baja a 866 por la misma razón.

Y añade tres cosas que yo **no** había pedido y que mejoran el resultado:

1. La nota de que **la fila «total» no la devuelve la consulta** — es la suma
   de la columna `n` y hay que calcularla a mano. Sin ese aviso, quien
   verifique buscaría una fila que no existe.
2. La explicación de **cómo se distinguen B y C**, que dan el mismo `9.0 = 7`
   y solo se separan por el total (867 vs 866) y por `8.0` (100 vs 99).
3. La aclaración de que en C la ficha «sigue siendo auditable en V3, que no
   filtra por baja» — justamente la propiedad de V3 que elogié en la primera
   pasada, ahora explícita para quien ejecute.

**La frase de cierre ya no produce falsa alarma en el escenario B.** Ahora
distingue alarma real (que se muevan 1.0 o 0.0, que aparezca otro valor de
`candef`, o que la pareja `8.0`/`9.0` no encaje en **ninguna** de las tres
columnas) de lo que no lo es: «Que `8.0` salga **100** NO es una alarma por
sí solo: es el escenario B, y hay que contrastarlo con lo que RRHH haya
respondido sobre `MO/0007`». Es exactamente la corrección pedida.

## S3 · D3, D4, D5, D6 — los cuatro aplicados

- **D3 (literal `OFIC.2ª ALBAÑIL`)** ✅ Corregidas las **3** apariciones de la
  petición (§3.3, correo §7, anexo) y las **3** del informe. `grep` de
  `OFIC. 2ª` (con espacio) sobre ambos ficheros: **0 coincidencias**. El
  literal escrito coincide ahora carácter a carácter con lo que devuelve
  Sigrid (`OFIC.2ª ALBAÑIL`) y con lo que RRHH verá en pantalla. La
  comprobación de longitudes que cita el informe (15 vs 16) es correcta.
- **D4 («10 líneas de horas»)** ✅ Corregido, y **verificado por mí**, porque
  el texto nuevo hace una afirmación **más fuerte** que la que yo pedí: no
  solo dice «10», dice que son «**las mismas diez en las ocho**:
  `CIA, CIE, CIF, CIH, CIM, CIP, CIV, CIZ, HEOF, HLOF`» y que «las otras
  nueve se quedan con la cantidad que tienen hoy, **que es 0**». Consulté las
  80 filas (8 fichas × 10 líneas): **los diez códigos son idénticos en las
  ocho fichas**, y una consulta de control sobre las líneas que no son la de
  defecto con `candef <> 0` devuelve **0 filas**. Las dos afirmaciones nuevas
  son ciertas. Buen ejemplo de por qué esta pasada re-mide en vez de leer.
- **D5 (aviso de `MO/0031` en el correo §7)** ✅ Incorporado, con los dos
  identificadores y cuál no tocar. El correo mejora además la advertencia
  general: ahora dice que algunas homónimas están «de alta, son de la misma
  categoría y tienen también 8 h por defecto: **son indistinguibles de la
  buena salvo por el identificador**», que es el hecho que de verdad protege
  a RRHH y que antes quedaba implícito.
- **D6 (listado de commits)** ✅ Resuelto. Ver §S5.

## S4 · Las correcciones no han roto nada

- **Coherencia §3.1 ↔ §3.2 ↔ §6 ↔ §7:** revisada entera. La tabla 3.2
  mantiene sus 7 filas con los mismos identificadores y categorías, que
  siguen coincidiendo con mi medición; el recuadro de `MO/0031` no la
  contradice; §6 sigue citando los mismos 8 `res.ide`; el correo §7 mantiene
  la misma tabla de 7 y ahora replica la advertencia. Sin desajustes.
- **V1, V2 y V3 siguen consistentes entre sí:** T3 **no tocó el SQL** de
  ninguna de las tres (el diff de §6 es solo la tabla de resultado esperado y
  sus notas). Todo lo que verifiqué en la primera pasada sobre las consultas
  —que corren tal cual, que V1 filtra por `fecbaj` y V3 no a propósito, que
  `MAX(candef)` de V3 equivale al filtro de V1 porque hay 1 sola fila por
  ficha, que `tiene_dni` resuelve bien el caso `res.conide = 0` porque no
  existe ninguna fila `emp` con `ide = 0`— **sigue vigente sin cambios**. La
  bifurcación de `MO/0007` está ahora declarada en las **tres**.
- **Barrido de datos sensibles, repetido sobre los dos ficheros ya
  cambiados** (mismos patrones que la primera pasada): DNI/NIE de 7-8 dígitos
  con letra, `https?://`, `azurewebsites`, `.net/`, `functions-key=`,
  `api[_-]?key=`, `Bearer `, `sk-`, `password`, `contrasen`, `tenant`,
  `subscription`, `client_secret` → **0 coincidencias en todos**. Por lectura
  del diff completo: ningún nombre de persona. Los identificadores nuevos que
  T3 introduce (537335, 1335318, 1335319, 1984734, 1335320) son `res.ide` de
  **fichas de recurso**, del mismo tipo técnico ya admitido en la primera
  pasada y ya presente en `specs/F-012`. El documento sigue siendo apto para
  salir por correo.
- **Ningún checkpoint que había aprobado se ha degradado.** El diff no toca
  código (dos Markdown de `progress/`), así que C3, C4 bis y C4 ter siguen
  N/A por los mismos motivos escritos en la primera pasada, y las Evidencias
  siguen completas —actualizadas de 4 a **6 consultas** a Sigrid, cifra que
  cuadra con las dos pasadas nuevas que declara.

## S5 · Sobre el commit: «(este)» + `--amend` — **me parece aceptable**

Lo apruebo, por tres razones:

1. **Resuelve el bucle en vez de alimentarlo.** Fijar el hash de T3 exigiría
   un commit posterior que quedaría a su vez sin listar — que es exactamente
   el problema que generó `568b5dc`. Citar el commit por **posición**
   («este») en lugar de por hash rompe la regresión infinita, y la lista
   queda cerrada: cuatro commits, tres por hash y el cuarto por posición.
2. **El `--amend` es legítimo aquí**: sobre un commit **local y no
   publicado**, no reescribe historia compartida, y evita un commit de ruido
   de un solo hash. No hay `push` ni PR (correcto: nadie los pidió).
3. **Está declarado, no disimulado**, con su porqué escrito en el informe.

Lo verifiqué: `git log dev..HEAD` muestra los cuatro commits, la lista del
informe los recoge todos y `568b5dc` aparece ya por hash. **D6 cerrado.**

## S6 · `bash harness/init.sh` — en verde

Ejecutado por mí con el **comando limpio**, sin pipes ni decoración:
`ENTORNO LISTO. Puedes trabajar.` Suite raíz **15 passed in 3.46s**; sv3, sv4
y sv5 en verde; `features.json` y `rigor.json` válidos; rama correcta
(`feature/F-014-candef-9-sigrid`); y la puerta de cobertura con su motivo
impreso: `PUERTA COBERTURA: N/A (F-014 es de nivel documental: no exige
cobertura)`. Los AVISO de sv1/sv2/`infra` sin tests y los 430 de `ruff` son
deuda previa, no introducida por esta feature.

`git status --porcelain`: solo `?? progress/review_F-014.md`, este mismo
informe, pendiente de que lo commitee el líder. Sin artefactos sospechosos.

## S7 · Consultas de esta pasada

**5 consultas, todas de solo lectura**, vía `sigrid-api` `POST /api/sql/read`
sobre la base `ruesma`: las 10 líneas de horas de las 8 fichas, el control de
`candef <> 0` fuera de la línea por defecto, el recuento del universo (867) y
el detalle de las dos fichas de `MO/0031`. **Cero escrituras** — `SELECT`
puros, ningún `UPDATE`/`INSERT`/`DELETE`, ninguna credencial de escritura.
Credenciales leídas en memoria de `services/partes-persistencia/.env` y **no
copiadas a ningún fichero, informe ni mensaje**. Scripts de usar y tirar en
el scratchpad de sesión, fuera del repositorio.

## S8 · Qué falta para el cierre (sin cambios, salvo el punto 0)

El punto 0 de la primera pasada (**corregir D1 y D2**) queda **cerrado**. Lo
demás sigue igual, y **F-014 no se cierra hoy**:

| # | Qué | Quién | Bloquea |
|---|---|---|---|
| 1 | Enviar la petición a RRHH/Administración (bloque §7 del documento) | humano | Sí |
| 2 | RRHH ejecuta en Sigrid: `candef` 8 → 9 en la línea `HLOF` de las 7 fichas (o 6), y el DNI de `MO/0037` | RRHH | Sí |
| 3 | RRHH comunica **qué decidió con `MO/0007`** | RRHH | Sí — sin eso no se sabe qué columna de V2 y qué recuento de V1 aplicar |
| 4 | Ejecutar V1, V2 y V3 en solo lectura y anotar el **resultado real** en `progress/impl_F-014.md` | equipo de partes | Sí — **es el `acceptance` 2, que NO doy por ejecutado** |
| 5 | Tercera revisión que verifique el punto 4 | reviewer | Sí |

Y las dos acciones **del líder** al cerrar la sesión, que siguen pendientes y
que el implementer hizo bien en no tocar:

- Dejar F-014 en **`blocked`** en `harness/features.json`, con el motivo («a
  la espera de que RRHH ejecute el cambio en Sigrid»).
- Actualizar `progress/current.md`: hoy sigue diciendo «Ninguna feature
  `in_progress`. Última sesión: 2026-08-18» mientras `features.json` marca
  F-014 `in_progress` (C2), y **añadir las verificaciones MANUAL de F-014** a
  la lista acumulada con su comando exacto (C4).

**Orden duro, vigente:** **F-015 no debe mergearse** hasta que el punto 4
salga en verde (riesgo §10.6 de F-012). Con la cuadrilla aún a `candef = 8`,
la regla nueva marcaría sus viernes de 6 h como incompletos y generaría
**+2 h/semana de extra automática falsa** por trabajador.

## S9 · Veredicto de la segunda pasada

**APROBADO** la parte entregada. Los seis cambios de §9 están aplicados, y
—lo que importa más— **aplicados sobre medición nueva, no sobre mi informe**:
el implementer re-consultó Sigrid antes de reescribir, y eso le llevó a
afirmar más de lo que yo pedí (los diez códigos idénticos, las nueve líneas a
0). Re-medí esas afirmaciones nuevas y **todas se sostienen**. La petición ya
no contiene ninguna afirmación falsa, el resultado esperado de la
verificación es inequívoco en los tres escenarios posibles, el documento no
lleva ni un dato sensible, y el entorno está en verde.

Queda un documento que **puede enviarse a RRHH tal cual**, que es lo que
F-014 tenía que producir.

Lo que **no** apruebo, por tercera vez y explícitamente: **el criterio
`acceptance` 2 no está ejecutado**. Está *bien especificado*, que es cosa
distinta y es todo lo que podía lograrse hoy. La feature va a `blocked`, no a
`done`.

### Automejora (sigue en pie, no aplicada — decide el humano)

Las dos propuestas de §11 de la primera pasada siguen sobre la mesa, y esta
segunda pasada refuerza la segunda de ellas. El defecto D4 lo prueba: el
texto corregido introdujo afirmaciones **nuevas** («las mismas diez líneas»,
«las otras nueve a 0») que ninguna lectura del informe habría podido validar,
y que solo se confirmaron re-consultando. **Corregir un documento de
mediciones genera mediciones nuevas, y esas también hay que medirlas.**
Propongo que la regla quede escrita así en el protocolo del reviewer: *«en
una segunda pasada, el reviewer re-mide las afirmaciones fácticas nuevas que
introduzca la corrección, no solo comprueba que el defecto señalado
desapareció»*. Por la regla de propagación de `CLAUDE.md`, iría también a
`arnes-base`.
