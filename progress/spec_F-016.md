<!-- progress/spec_F-016.md -->
# F-016 · Informe del spec-author

Fecha: 2026-08-19. Rama: `feature/F-016-admin-empleado-jornada` (worktree
aislado; el árbol principal seguía con F-015). `harness/features.json` y
`progress/current.md` **no** se han tocado: F-016 sigue `pending`.

## Qué he redactado

`specs/F-016-admin-empleado-jornada/` con los tres ficheros:

- **`requirements.md`** — 19 requisitos EARS (R1–R19) con criterios de
  aceptación y nombre de test, tabla de trazabilidad requisito → test →
  fichero, fase RED marcada en R7/R12/R14/R15 y un bloque «fuera de alcance»
  explícito.
- **`design.md`** — límite de servicio (**solo sv4**), modelo de la pantalla,
  ficheros a crear/modificar/NO tocar con ruta exacta, firmas de las
  funciones nuevas por capa, las seis rutas HTTP, el plan de pruebas (con la
  tabla de casos del solape y las 5 verificaciones MANUAL), 4 riesgos, 10
  decisiones propias (DA1–DA10) y 6 dudas para el humano.
- **`tasks.md`** — T0–T10, ordenadas por dependencia, cada una con su
  verificación; T0 es la puerta de entrada (F-015 mergeada) y T10 es
  `bash harness/init.sh` en verde.

Diseñado contra la especificación de F-015 (§6 y R16/R18/R27/R30 de su rama),
no contra el árbol actual: hoy `empleado_jornada` todavía no existe.

## Decisiones que he tomado yo

1. **El humano escribe «último día incluido», nunca `hasta`** (DA1, R7). El
   formulario y el listado hablan en inclusivo; la conversión `+1 día` vive
   solo en la capa web. «Hasta el 31/07» se guarda como `2026-08-01` sin que
   el usuario tenga que saberlo. Era la trampa que F-015 dejó señalada.
2. **Cerrar ≠ desactivar** (DA2). Cerrar pone `hasta` (historia legítima);
   desactivar es la papelera lógica `is_active` (semántica 8). No se funden.
3. **Un solape se rechaza (409), nunca se resuelve solo** (DA3, R12). La
   respuesta nombra la fila en conflicto; el sistema no recorta la vigencia
   ajena, porque reescribiría en silencio un dato con el que sv3 ya calculó
   extras. Contiguas (`hasta` = `desde`) NO solapan: es el caso normal.
4. **`sv3` no se toca**, y está justificado (DA7): que sv3 «se entere» de un
   cambio exigiría acoplamiento nuevo entre servicios. Se acepta el TTL que
   ya existe y **se avisa en pantalla**, con los minutos derivados de
   `JORNADA_CACHE_TTL_S`, no cableados (R14). sv4 sí invalida su propio
   proveedor tras cada escritura con éxito — es el único cambio de F-016
   sobre lo que deja F-015.
5. **Cero cambios de schema** (R1): F-016 vive con las 16 columnas de F-015 y
   no toca ninguna copia de `orm_models.py`. Hay un test que lo vigila.
6. **La validación en `application/services/jornada_admin.py`**, funciones
   puras, siguiendo el precedente de `congelacion.py` (F-004), y los cinco
   métodos nuevos colgando del `ParteReviewRepository` único de sv4 (DA5,
   DA6): son los patrones reales del servicio, no un patrón nuevo.
7. **Puerta de acceso en una sola función** `_exigir_admin_jornadas()`
   (DA9, R15), gobernada por `JORNADAS_ADMIN_ENABLED` (default `true`, única
   variable nueva, sin cambios en `infra/`). Cuando llegue F-008, el rol se
   enchufa ahí y en ningún otro sitio.
8. **He añadido «Reactivar»** (DA4), que no estaba en el enunciado: sin él,
   una desactivación por error solo se arregla por SQL, que es justo lo que
   la feature viene a evitar. Marcado como lo primero que se recorta si el
   humano quiere menos alcance.

## Hallazgo que corrige una premisa del encargo

**sv4 NO lee hoy la identidad de Easy Auth.** No hay ni una referencia a
`X-MS-CLIENT-PRINCIPAL-*` en todo el repositorio: `approved_by` y
`deleted_by` se rellenan con la variable `DEFAULT_REVIEWER`, igual para
todos. Así que «la identidad que sv4 ya tiene» no existe. La spec propone el
helper `_actor(request)` (cabecera de Easy Auth, con `DEFAULT_REVIEWER` de
reserva) **acotado a las columnas de F-016** — ver duda 2.

## Dudas para el humano (las 6 están en `design.md` §13)

1. **Acceso mientras no exista F-008**: propuesta = abierta a cualquier
   usuario autenticado, como el reencolado de poison (precedente del
   2026-08-13), con interruptor `JORNADAS_ADMIN_ENABLED` para apagarla desde
   Azure. Alternativas: default apagado, o dejar F-016 en `blocked` hasta
   F-008. **Es la duda que más conviene contestar antes de implementar.**
2. **¿Se introduce la lectura de Easy Auth?** Acotada a F-016, o se extiende
   a `approved_by`/`deleted_by` (eso cambiaría el significado de datos ya
   guardados: parece material de F-008).
3. **¿Selector de trabajador o DNI a mano?** La spec pide el DNI a mano y
   solo **avisa** si no consta en el catálogo de Sigrid. Un combo como el de
   «+ Nuevo» es bastante más JS; si se quiere, hay que decirlo ahora.
4. **Tres normalizadores de DNI equivalentes en sv4.** F-016 no los unifica,
   pero deja un test que salta si divergen. ¿Feature de limpieza aparte?
5. **¿Se queda «Reactivar»?** (decisión 8 de arriba).
6. **`origen`**: cuando existan filas importadas de `sigrid`/`sesame`, ¿solo
   lectura o editables desde la pantalla? No urge.

## Estado (primera pasada)

- `bash harness/init.sh`: **en verde** (exit 0) sobre la rama, con la puerta
  de cobertura en `N/A` con motivo (F-016 no cambia líneas Python: la spec es
  documentación).
- No se ha escrito ni una línea de código de producción, que es lo correcto
  para este rol.
- Siguiente paso del líder: PARADA 1 con el humano sobre las 6 dudas y, con
  su aprobación, `spec_ready`. **La implementación no puede empezar hasta que
  F-015 esté mergeada en `dev`** (T0 de `tasks.md`).

---

# Segunda pasada — decisiones del humano (2026-08-19)

El humano ha contestado cuatro de las seis dudas. La spec **no se ha
reescrito**: se ha ajustado. Sigue sin haber ni una línea de código de
producción.

## 1. Acceso (duda 1) — RESUELTA, sin cambio de diseño

Cualquier usuario autenticado, con interruptor, repitiendo el precedente del
reencolado de poison (2026-08-13). Se acepta la propuesta tal cual:
`JORNADAS_ADMIN_ENABLED` con default `true` y la puerta única
`_exigir_admin_jornadas()` para que F-008 solo tenga que enchufar el rol ahí.

**Dónde**: `design.md` §13, duda 1, marcada **RESUELTA (2026-08-19)** con las
alternativas descartadas. R15, DA9 y T3 no cambian — ya lo decían.

## 2. Identidad (duda 2) — RESUELTA, alcance ampliado y sacado a F-017

El hallazgo de la primera pasada era correcto y el líder lo ha verificado:
**cero referencias a `X-MS-CLIENT-PRINCIPAL` en el repositorio**; todo el
portal firma con `DEFAULT_REVIEWER`. El humano quiere la identidad real **en
todo el portal**, no solo en las columnas de F-016. Decisión del líder sobre
la forma: eso **no entra en F-016**, sale a **F-017 · «Identidad real de Easy
Auth en sv4»**, porque cambia el significado de datos ya guardados.

**Qué he escrito**:

- **F-017 como prerrequisito RECOMENDADO, no bloqueante** — cabecera de
  `requirements.md`. F-016 pide la identidad a **un solo helper**
  `_actor(request)` que **hoy devuelve `settings.default_reviewer`**, igual
  que el resto del portal; cuando F-017 llegue, cambia el interior del helper
  y F-016 no se toca.
- `design.md` §5.3: docstring de `_actor` reescrito — **no lee cabeceras**, y
  si F-017 ya está mergeada al implementar, se **usa su helper**, no se
  duplica.
- **R13** ahora exige que el actor se resuelva en un solo sitio y que el test
  **inyecte o parchee el helper** en vez de fabricar cabeceras: así seguirá
  en verde el día que F-017 cambie su interior.
- **`design.md` §14 (nuevo)**: qué debería cubrir F-017, enumerado como
  propuesta y **sin redactar su spec** — decodificar
  `X-MS-CLIENT-PRINCIPAL-NAME` / el token base64 y cuál manda; el fallback
  para desarrollo local; **la tabla de los once sitios exactos** que hoy
  firman con `settings.default_reviewer` (todos en
  `services/partes-front/interface_adapters/web/app.py`, líneas 1500, 1594,
  1629, 1684, 1687, 1841, 1867, 1881, 1900, 1910 y 2121, con la ruta y la
  columna de cada uno, verificadas en el árbol); qué se hace con las filas
  históricas (**no se reescriben**, se documenta el corte: inventar autores
  sería falsificar auditoría); los tests sin red; y que los **roles** siguen
  siendo F-008.
- Verificación 5 de MANUAL reescrita: mientras F-017 no esté, ver
  `DEFAULT_REVIEWER` en `created_by` es **lo correcto**, no un fallo.

Detalle útil para el líder al dar de alta F-017: son **once** puntos, no
siete; cuatro de ellos escriben en `undo_log`, así que el cambio se ve
también en el widget de deshacer.

## 3. Selector de trabajador (duda 3) — RESUELTA, y CAMBIA el diseño

He mirado primero el que ya existe, y **se reutiliza entero**:

| Pieza existente | Dónde | Veredicto |
|---|---|---|
| `GET /api/sigrid/empleados` | `app.py:1183` | **Sirve tal cual**: ya devuelve `dni` y `nombre` por trabajador. No se toca. |
| `_comboSimple(...)` | `static/app.js:1069` | **Sirve tal cual**: carga con caché, panel, y su filtro ya busca por la etiqueta, por `dni` y por `codigo`. No se toca. |
| Marcado `combo-simple` y su CSS | `nuevo_parte.html:28-36`, `styles.css` | **Sirven tal cual**. No hace falta CSS nuevo. |

**Lo mínimo que sí hay que añadir, y por qué** (`design.md` §5.6):

1. **Camino manual de excepción** — `_comboSimple` no da salida si el
   catálogo está vacío o apagado: el panel simplemente no se abre. Como R17
   exige que la pantalla funcione **sin Sigrid cableado**, hay un checkbox
   «El trabajador no está en la lista» que descubre un campo de texto, y que
   llega **ya marcado** desde el servidor cuando `sigrid_lookup_enabled` es
   falso.
2. **`sigrid_enabled` en el contexto** de `GET /admin/jornadas`, como ya
   hacen otras seis vistas del portal.
3. **Modo edición deshabilitado** (R4: cambiar de trabajador es cerrar una
   fila y crear otra).

**Un hallazgo que cambia dónde va el JS**: `_comboSimple` es **privado del
IIFE grande** de `app.js` (abre sobre la línea 40, cierra sobre la 2228). El
diseño anterior decía «un IIFE nuevo al final del fichero», y desde ahí **no
se vería**. Ahora el bloque de F-016 va **dentro de ese mismo IIFE, justo
antes de su cierre**: cuesta cero líneas ajenas modificadas. Descartado
promover `_comboSimple` a global tipo `MotivoHttp`, que tocaría código vivo
de cuatro combos de features ya cerradas para no ganar nada hoy (**DA11**).

**Qué he tocado por este cambio**:

- **R20 nuevo** en `requirements.md` (selector + alta manual + degradación),
  con su test `test_f016_r20_selector_trabajador` y su fila en la tabla de
  trazabilidad.
- **R19 ajustado**: con selector, el DNI llega del catálogo, así que el aviso
  «no consta en Sigrid» pasa a ser el **caso raro** (alta manual), no el
  normal. La regla no cambia: avisa, no bloquea.
- **R17 aclarado**: el selector no rompe el «sin red». Pintar la página no
  consulta el catálogo; el combo pide `/api/sigrid/empleados` por `fetch`
  **después** de que el humano teclee, y ese endpoint es de F-003.
- `design.md`: §1 (roce con Sigrid), §2 (el campo DNI pasa a ser el bloque
  Trabajador), §3 y §4 (plantilla y ubicación del JS), **§5.6 nueva**, §8
  (qué del selector es testeable y qué no: no hay arnés de JS en este
  repositorio), §8.2 (**verificación MANUAL 6** nueva), §9 (el endpoint, el
  catálogo y `_comboSimple` entran en la lista de «no se tocan»), **§11.4
  nueva** (riesgo: el TTL del catálogo puede tardar en mostrar un alta
  reciente de Sigrid) y **DA11/DA12**.
- `tasks.md`: **T5** (marcado del selector, ids, `sigrid_enabled`, modo
  edición) y **T7** (bloque dentro del IIFE grande, una sola llamada a
  `_comboSimple`, `_comboSimple` no se modifica), más dos verificaciones
  nuevas por `git diff`: que no se añade ninguna ruta `/api/sigrid/*` y que
  el diff de `app.js` solo añade líneas.

**No queda ni un resto del diseño anterior**: el campo «DNI (texto)» ha
desaparecido del formulario y el punto «Buscador / combo de trabajadores» ha
salido de «Fuera de alcance», sustituido por «un endpoint de catálogo propio
de F-016», que es lo que de verdad queda fuera.

## 4. «Reactivar» (duda 5) — RESUELTA: se queda

**DA4** ya no dice «lo primero que se cae si el humano quiere recortar
alcance»; dice **CONFIRMADO por el humano el 2026-08-19**. R6 se implementa
entero, con la revalidación de solape al reactivar.

## Dudas que siguen ABIERTAS (no las he cerrado yo)

- **4 · Tres normalizadores de DNI equivalentes en sv4**
  (`text_match.normalize_dni`, `calendario_provider.normalizar_dni` y el
  `_norm_dni` local de `build_app`, `app.py:363`). F-016 no los unifica y
  deja el test de R18 que salta si divergen. ¿Feature de limpieza aparte?
- **6 · `origen`**: cuando existan filas importadas de `sigrid` / `sesame`,
  ¿solo lectura o editables desde esta pantalla? No urge, pero condiciona esa
  feature futura.

Están agrupadas bajo un epígrafe **ABIERTAS** en `design.md` §13, separadas
de las cuatro **RESUELTAS**, cada una con su decisión y su fecha.

## Estado (segunda pasada)

- Ficheros tocados: los tres de `specs/F-016-admin-empleado-jornada/` y este
  informe. **Nada más**: ni `harness/features.json`, ni
  `progress/current.md`, ni un solo fichero de `services/`.
- `bash harness/init.sh`: **en verde** (exit 0) sobre
  `feature/F-016-admin-empleado-jornada`, en el worktree aislado.
- Requisitos: ahora **20** (R1–R20). Dudas: **4 resueltas, 2 abiertas**.
- **Para el líder**: dar de alta **F-017** en `harness/features.json` con el
  material de `design.md` §14, y decidir su orden respecto de F-016 (las dos
  órdenes funcionan sin retrabajo; F-017 antes solo sirve para que las filas
  de `empleado_jornada` nazcan ya firmadas con el usuario real). La puerta de
  entrada de F-016 **sigue siendo F-015 mergeada en `dev`** (T0).
