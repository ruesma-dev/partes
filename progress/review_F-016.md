<!-- progress/review_F-016.md -->
# F-016 · Pantalla de administración de `empleado_jornada` (sv4) — review

**Veredicto: APROBADO**

Rama `feature/F-016-admin-empleado-jornada`, 11 commits propios sobre el merge
de `dev`. Rigor declarado en `harness/features.json`: **`estandar`** (no por
omisión). Puertas que exige ese nivel (`CHECKPOINTS.md` §Niveles): C1–C3, C3
bis, C4, **fase RED** en los requisitos centrales, **cobertura** de lo cambiado
≥ 80 % y **campaña de mutación** con todos los supervivientes analizados.

Todo lo que sigue está **verificado ejecutando**, no leyendo el informe. Los
dos huecos que quedan sin verificar están declarados como tales en §6.

---

## 1. Números: verificados de forma independiente

| Lo que declara el implementer | Lo que he medido yo | ¿Coincide? |
|---|---|---|
| 799 tests en sv4, 0 fallos | `python -m pytest -q` en `services/partes-front` → **799 passed en 73,84 s** | Sí |
| 134 tests nuevos de F-016 | `-k f016` → **134 passed**, 665 deselected | Sí |
| 92 tests en la raíz | `bash harness/init.sh` → **92 passed** | Sí |
| sv3 y sv5 en verde | `init.sh` → verde (caché del arnés, árbol sin cambios) | Sí |
| Cobertura 98,5 % (326/331) | línea `PUERTA COBERTURA` de `init.sh` → **[OK] 98.5 % de 331 líneas (326/331, umbral 80 %, nivel estandar)** | Sí |
| Alcance: 5 ficheros, 827 líneas | `harness.alcance.alcance_de_feature('F-016')` → 368 + 11 + 6 + 131 + 311 = **827** | Sí |
| 93 mutantes generados | `harness.mutacion.generar_mutantes` fichero a fichero (cálculo puro) → 51 + 0 + 1 + 7 + 34 = **93** | Sí |
| 79 muertos / 14 supervivientes / 0 timeouts | 14 secciones `###` en `progress/mutacion_F-016.md`, **ninguna en `PENDIENTE`** | Sí |

`bash harness/init.sh` (comando limpio) termina en **ENTORNO LISTO**, exit 0.

### 1.1 Muestreo de supervivientes (defensa contra un informe escrito a mano)

Tres supervivientes declarados, contrastados contra los mutantes que el
generador produce de verdad — mismo fichero, misma línea, mismo operador,
mismo texto original→mutado:

| Informe | Recalculado | ¿Existe? |
|---|---|---|
| `jornada_admin.py:69` [booleano] `frozen=True`→`frozen=False` | idéntico | Sí |
| `jornada_admin.py:127` [entero] `[None] * 7`→`[None] * 8` | idéntico | Sí |
| `app.py:1991` [entero] `// 60`→`// 61` | idéntico | Sí |

La campaña **no declara cero mutantes**, así que no procede la prueba de
control por exclusión de alcance. El hueco conocido del arnés (la campaña solo
ejecuta la suite del servicio dueño del fichero mutado) **no aplica aquí**: los
cinco ficheros del alcance son de sv4 y la suite ejecutada es la de sv4.

Análisis de los 14: 4 equivalentes reales, 5 fuera del contrato observable
(`include_in_schema`), 5 huecos acotados. El único con consecuencia visible es
el texto «sin fin» del 409 (`app.py:2019`) — **cosmético, sin riesgo de dato**:
el código es correcto (`fin = detalle["hasta_inclusivo"] or "sin fin"`), lo que
falta es un test que pase por esa rama. El nivel `estandar` exige
supervivientes **analizados**, no cero; y la decisión de no tapar huecos
*después* de medir, para que los números correspondan al árbol que reviso, es
la correcta.

---

## 2. Los puntos de riesgo, comprobados ejecutando

Escribí una batería propia (9 tests, fuera de la del implementer), la ejecuté
—**9 passed a la primera**— y la borré: el árbol queda limpio
(`git status --porcelain` vacío).

### R1 · cero cambios de schema — **verificado**
- `EmpleadoJornadaOrm.__table__.columns` → **19 columnas**, exactamente las que
  R1 enumera.
- `git diff --name-only dev...HEAD | grep orm_models` → **vacío**. Ninguna de
  las dos copias tocada.
- `tests/test_f010_orm_models_gemelos.py` → **no aparece en el diff** y pasa
  dentro de los 92 de la raíz. Guardián en verde **sin haberse modificado**.
- Ficheros del diff fuera de `services/partes-front/`: solo
  `docs/referencia/partes-proyecto.md`, `specs/F-016-*` (3), `progress/` (3) y
  `harness/features.json` (el cambio de estado del líder, no del implementer).
  **sv3, sv1, sv2, sv5 e `infra/`: ni un fichero.**

### R7 · el humano nunca ve `hasta` — **verificado**
- Alta con último día `2026-07-31` ⇒ en BBDD `hasta = '2026-08-01'`; la página
  pinta `2026-07-31` y **`2026-08-01` no aparece en el HTML**.
- `grep -i "exclusiv" templates/admin_jornadas.html` → **vacío**.
- La conversión vive solo en `application/services/jornada_admin.py`
  (`a_hasta_exclusivo` / `a_ultimo_dia_incluido`), con aritmética de `date`.
- El ida y vuelta sobre **366 fechas consecutivas** existe
  (`test_f016_r7_el_ida_y_vuelta_es_estable_en_366_fechas_seguidas`) y pasa.

### R12 · solape — **verificado contra la tabla de `design.md` §8.1**
Los nueve casos, por HTTP contra el endpoint real:

| Caso (A = `[2026-07-01, 2026-08-01)` activa) | Esperado | Obtenido |
|---|---|---|
| `[2026-08-01, ∞)` contigua por la derecha | No solapa | 200 |
| `[2026-07-31, ∞)` | Solapa | 409 |
| `[2026-06-01, 2026-07-01)` contigua por la izquierda | No solapa | 200 |
| `[2026-06-01, 2026-07-02)` | Solapa | 409 |
| Contenida en A | Solapa | 409 |
| Contiene a A | Solapa | 409 |
| Otro DNI | No solapa | 200 |
| A inactiva | No solapa | 200 |
| Editar A sin cambios | No solapa (`excluir_id`) | 200 |

Además: el 409 **nombra la fila en conflicto** (`conflicto.id` correcto) y **no
ajusta la fila ajena** (volcado idéntico). Reactivar una fila cuyo hueco se
ocupó ⇒ 409 y **la fila se queda inactiva** (comprobado leyendo `is_active`
directamente de la BBDD).

La regla `_solapan` está escrita como `da < hb and db < ha` sobre `date`, así
que «contiguas no solapan» **sale de la propia regla**, no de un caso especial
borrable. Bien.

### R8–R11 · las validaciones corren ANTES de escribir — **verificado de verdad**
No por lectura: comparé el **volcado completo de la tabla** (id, dni, S, desde,
hasta, origen, is_active, created_by, updated_by) antes y después de **nueve
cuerpos distintos rechazados con 422** (R8 sin S ni patrón; R9 patrón a medias
y hora 25; R10 S=169 y S=0; R11 `2026-02-30`, `31/07/2026` y último día
anterior a `desde`; R18 DNI vacío), del **409 de solape** y de un **cuerpo
no-JSON**. En los once casos el volcado es **byte a byte el mismo**. Y el
cuerpo ilegible sale 422, no 500.

### R6 · papelera lógica — **verificado**
`git diff dev...HEAD -- parte_repository.py | grep -iE "^\+.*(delete|drop )"`
devuelve **una sola línea, y es el comentario** que explica por qué no hay
`DELETE`. Encadenando desactivar/reactivar ×2 + cerrar sobre la misma fila,
`count(*)` sigue siendo 1.

### R18 · normalización de DNI — **verificado**
`jornada_admin.normalize_dni is jornada_provider.normalize_dni` → **True**: es
literalmente el mismo objeto (`application.services.text_match.normalize_dni`),
el que usa la lectura de F-015. No pueden divergir. `« 1234-abcd »` se guarda
como `1234ABCD`.

### R20 · selector — **verificado**
- `git diff dev...HEAD -- app.py | grep "api/sigrid"` → **ni una línea**. No se
  añade ni se modifica ninguna ruta `/api/sigrid/*`.
- El bloque JS de F-016 arranca en `static/app.js:2230`. El IIFE que define
  `_comboSimple` (línea 1069) abre en la **40** y cierra en la **2452**: el
  bloque está **dentro**. Verificado localizando los cinco IIFE del fichero, no
  de oídas — desde uno nuevo al final `_comboSimple` no se vería.
- Con Sigrid apagado (como corre la suite) `GET /admin/jornadas` responde
  **200**, el marcado `combo-simple` / `combo-panel` /
  `data-empleados-url="/api/sigrid/empleados"` está, el combo llega
  `disabled` y el **camino manual está visible**.

### R14 · caché — **verificado**
- TTL 600 s ⇒ el HTML dice «10 minutos»; TTL 900 s ⇒ «15 minutos». Derivado de
  `settings.jornada_cache_ttl_s`, **no un literal** (redondeo hacia arriba, que
  es lo prudente: no promete menos espera de la real).
- Contador propio sobre el proveedor: alta, edición, cierre, desactivar y
  reactivar ⇒ `invalidar()` **exactamente una vez cada una** (1→5). Un rechazo
  posterior **no suma**. Sin proveedor inyectado, las escrituras no fallan
  (`_invalidar_jornadas` va por `getattr` + `callable`).

### R15 · puerta de acceso — **verificado**
- `settings.jornadas_admin_enabled` aparece **2 veces** en `app.py`: el global
  de la plantilla (465) y la puerta (502). Una sola función
  `_exigir_admin_jornadas`, llamada como **primera línea** de las **6** rutas.
- Con la variable a falso: la página y **los cinco endpoints** devuelven 404, y
  `GET /health` sigue en 200 (ninguna otra ruta cambia).

### R13 · auditoría — **verificado, con una observación**
`_actor(request)` se declara **una vez** y se usa en las **cinco** escrituras;
el bloque de F-016 **no contiene** `settings.default_reviewer` ni una vez (hay
un test que lo fija leyendo el propio fichero). Sin `DEFAULT_REVIEWER` se sella
`NULL` y la operación no falla. Ver observación 1 de §5.

### Secretos y datos personales — **verificado**
Barrido sobre lo añadido: sin secretos, sin cadenas de conexión, sin claves.
Los DNIs son sintéticos (`AAA1`, `BBB2`, `1234ABCD`, `00000000T`); ningún
nombre de persona. Sin `print()` de debug, sin `console.log`, sin `debugger`,
sin TODO/FIXME nuevos. Primera línea con la ruta en todos los ficheros nuevos
(incluida la plantilla, con la sintaxis `{# … #}` de Jinja).

---

## 3. Recorrido de `CHECKPOINTS.md`

### C1 — El arnés está completo y en verde
- [x] `bash harness/init.sh` exit 0, «ENTORNO LISTO».
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`, etc.

### C2 — El estado es coherente
- [x] Una sola feature `in_progress` (`F-016`); `init.sh` lo valida.
- [x] Rama actual `feature/F-016-admin-empleado-jornada`, la declarada en
      `branch`.
- [x] `progress/current.md` describe la sesión activa. *(No lo he tocado: no me
      corresponde.)*
- [x] Las features `done` tienen resumen en `progress/history.md`.

### C3 — El código respeta arquitectura y convenciones
- [x] Hexagonal respetada. `jornada_admin.py` vive en `application/services/`
      y es **puro**: sus únicos imports son `dataclasses`, `datetime`,
      `collections.abc`, `typing` y `text_match`. Ni BBDD, ni FastAPI, ni
      logging. La capa web solo traduce HTTP ⇄ esas firmas.
- [x] El repositorio importa `columnas_patron` de `application`: **no es una
      inversión de capas nueva**, `parte_repository.py` ya importaba
      `text_match`, `congelacion` y `calendar_builder` de ahí (líneas 42, 44,
      55). Precedente comprobado, no aceptado de palabra.
- [x] Primera línea con la ruta en todos los ficheros nuevos.
- [x] Sin prints de debug, sin TODOs sin contexto, sin secretos.
- [x] Semántica 8 de `docs/ARCHITECTURE.md` (papelera lógica) respetada.
- [x] LÍMITE DE SERVICIO: la spec declara sv4 y **solo** sv4, y el diff lo
      cumple. **No se añade nada a la lista cerrada de duplicación tolerada.**

### C3 bis — Documentos de fuera
**N/A justificado**: F-016 no incorpora ningún documento externo. El único
cambio en `docs/` es `docs/referencia/partes-proyecto.md`, documento **propio**
del repositorio, editado (§5.4 y §5.4.1 nueva), no convertido de un PDF.

### C4 — La verificación es real
- [x] **Los 20 requisitos EARS tienen test**, y los tests existen con el nombre
      declarado. Recuento por requisito sobre los tres ficheros: R1×2, R2×7,
      R3×3, R4×2, R5×4, R6×3, R7×4, R8×3, R9×5, R10×4, R11×2, R12×16, R13×3,
      R14×6, R15×6, R16×2, R17×2, R18×5, R19×4, R20×5 = **134**. Ninguno a cero.
- [x] Los unit tests no tocan red ni BBDD real: SQLite en memoria +
      `Settings(_env_file=None)`, app construida sin Sigrid, sin Sesame, sin
      colas y sin sv5 (R17).
- [x] Las **6 verificaciones MANUAL (humano)** están listadas en
      `progress/impl_F-016.md` §8, con el SQL y los pasos concretos.

### C4 bis — El rigor declarado se cumple
- [x] `rigor: "estandar"` declarado explícitamente en `harness/features.json`.
- [x] **Fase RED con traza real** para los cuatro requisitos que la spec exige:
      **R7 y R12** (T1, `ModuleNotFoundError` del módulo inexistente), **R15**
      (T3, `assert 0 == 2` sobre la puerta única, con 9 fallos) y **R14** (T6,
      `AttributeError: … has no attribute 'invalidar'`). Son salidas reales de
      pytest, no frases del tipo «se siguió TDD».
      La RED de R15 está además **argumentada**: el caso «apagada ⇒ 404» pasa
      con la feature sin escribir (una ruta inexistente también da 404), y lo
      que falla es la otra mitad. Eso es exactamente el razonamiento que la
      fase RED persigue.
- [x] **Cobertura**: `PUERTA COBERTURA` en `[OK]`, 98,5 % ≥ 80 %.
- [x] **Mutación**: `progress/mutacion_F-016.md` generado por
      `python -m harness.mutacion --feature F-016`, con totales reales
      **recalculados por mí** (§1) y **0 timeouts**.
- [x] Los **14 supervivientes** tienen sección de análisis; **ninguno en
      `PENDIENTE`**.
- [x] El informe trae la sección **«Evidencias»** (§9) con los cuatro números:
      tests, cobertura, mutantes/supervivientes y tiempo de suite.
- [x] Ningún punto de este bloque en N/A.

**Mención aparte, porque es lo que da valor a la campaña**: los mutantes sobre
la lógica de riesgo murieron todos —los cuatro extremos del solape, el
`days=1`→`days=2` de la conversión de fechas, los límites de R9 y R10, la
exclusión de la propia fila al editar, el filtro por `is_active`, el
`origen='manual'` forzado y el 404 de la puerta—. En una pantalla que edita el
cómputo de nóminas, eso es lo que había que comprobar.

### C4 ter — Rutas sensibles
**N/A por configuración**: no existe `harness/rutas_sensibles.json` (solo el
`.ejemplo.json`). Sin declaración, `CHECKPOINTS.md` dice literalmente que este
bloque es N/A y no hay nada que justificar.

### C5 — La sesión se cerró bien
- [x] `tasks.md` con **T0–T10 todas `[x]`** y ningún `[ ]` suelto.
- [x] Commits por tarea con el formato `F-016 Tn: …` (T1–T9/T10). Los dos
      commits sin `Tn` son la spec y el informe, que no son tareas.
- [x] Árbol limpio, sin temporales ni artefactos sin trackear.
- [x] `features.json` refleja `in_progress`; moverlo a `done` es del líder.

---

## 4. Cobertura requisito → test

| Req | Test | Fichero | Verificado por mí |
|---|---|---|---|
| R1 | `test_f016_r1_schema_intacto` (+1) | vista | Sí: 19 columnas, ORM y guardián intactos, diff acotado |
| R2 | `test_f016_r2_listado` (+6) | vista | Parcial: la página responde 200 y pinta el día inclusivo; el orden lo cubre su test |
| R3 | `test_f016_r3_crear` (+2) | endpoints | Sí: alta 200, `origen='manual'`, `updated_*` nulos |
| R4 | `test_f016_r4_editar` (+1) | endpoints | Sí: PATCH sin cambios no choca consigo mismo |
| R5 | `test_f016_r5_cerrar` (+3) | endpoints | Sí: cierre 200 e invalidación |
| R6 | `test_f016_r6_papelera_logica` (+2) | endpoints | Sí: sin `DELETE`, `count(*)` estable |
| R7 | `test_f016_r7_hasta_exclusivo` (+3, incl. 366 fechas) | validación | Sí: BBDD `+1 día`, HTML inclusivo, sin «exclusiv» |
| R8 | `test_f016_r8_semanal_o_patron` (+2) | validación | Sí: 422 y BBDD intacta |
| R9 | `test_f016_r9_horas_patron` (+4) | validación | Sí: patrón a medias y hora 25 ⇒ 422 sin escribir |
| R10 | `test_f016_r10_semanal_rango` (+3) | validación | Sí: 0 y 169 ⇒ 422 sin escribir |
| R11 | `test_f016_r11_fechas` (+1) | validación | Sí: fecha imposible, formato ES y `hasta ≤ desde` ⇒ 422 |
| R12 | `test_f016_r12_solape` (+15) | validación + endpoints | Sí: los 9 casos de `design.md` §8.1 por HTTP |
| R13 | `test_f016_r13_auditoria` (+2) | endpoints | Sí: `_actor` único, 5 usos, sin `default_reviewer` en el bloque |
| R14 | `test_f016_r14_cache_y_aviso` (+5) | vista | Sí: minutos derivados (600/900) e invalidación 1:1 |
| R15 | `test_f016_r15_puerta_de_acceso` (+5) | vista | Sí: 404 en página y los 5, `/health` intacto |
| R16 | `test_f016_r16_no_encontrada` (+1) | endpoints | Parcial: cubierto por su test |
| R17 | `test_f016_r17_sin_red` (+1) | vista | Sí: mi montaje no inyecta Sigrid/Sesame/colas/sv5 y todo funciona |
| R18 | `test_f016_r18_dni_normalizado` (+4) | validación | Sí: identidad de función y `« 1234-abcd »` ⇒ `1234ABCD` |
| R19 | `test_f016_r19_dni_desconocido_avisa` (+3) | endpoints | Parcial: cubierto por su test; catálogo apagado ⇒ cero llamadas |
| R20 | `test_f016_r20_selector_trabajador` (+4) | vista | Sí: sin rutas nuevas, JS dentro del IIFE, 200 con Sigrid apagado |

---

## 5. Observaciones (ninguna bloquea)

1. **`test_f016_r13_auditoria` parchea `DEFAULT_REVIEWER`, no el helper**
   (`tests/test_f016_endpoints_admin_jornadas.py:519`). R13 pide inyectar o
   parchear `_actor` «así este test sigue en verde el día que F-017 cambie su
   interior». Parchear la variable de entorno es «parchear su resultado»
   *hoy*, pero el día que `_actor` devuelva el principal real de Easy Auth
   este test se pondrá **rojo**. Lo aviso aquí para que **F-017 lo tenga en su
   lista de tocar**, no como defecto de F-016: el objetivo de fondo —no
   fabricar cabeceras— sí se cumple, y el resto de R13 (punto único, ausencia
   de `settings.default_reviewer` en el bloque) está fijado por test.
   *Gravedad: baja. Acción: anotarlo en la spec de F-017.*

2. **`JORNADAS_ADMIN_ENABLED` no queda en ningún fichero versionado del
   repositorio.** `design.md` §4 pedía añadirla a `.env.example`, que
   `services/partes-front/.gitignore:189` ignora por la regla `*.example`. El
   implementer no forzó el `git add -f`, y hace bien: revertir una decisión del
   repositorio por la puerta de atrás es peor. La variable queda documentada en
   `azure-apps/partes.md` (commit local) y con default `True` en el código.
   *Gravedad: informativa. Acción: ninguna en F-016; si molesta, es una
   decisión sobre el `.gitignore`, no sobre esta feature.*

3. **El superviviente del texto «sin fin» del 409** (`app.py:2019`) es el único
   de los 14 con consecuencia visible para el humano, y es **de mensaje**: el
   código es correcto, falta un test que pase por la rama de vigencia abierta.
   Está analizado y anotado como primera mejora. *Gravedad: baja.*

4. **La suite de sv4 ha pasado de ~52 s a ~74–114 s.** Lo mide y lo explica el
   propio informe: 134 tests que levantan `build_app` entera, el patrón que ya
   usan F-002/F-003/F-004. No es deuda de F-016 sino del montaje del servicio.
   La propuesta del implementer (una fixture de app compartida, como mejora
   transversal de sv4) me parece correcta y **fuera de esta feature**.

---

## 6. Lo que NO he verificado (declarado, no escondido)

1. **Las 5 líneas cambiadas sin cubrir no están enumeradas.** El implementer no
   las listó para no lanzar una segunda medición de cobertura, y yo tampoco lo
   he hecho: exigiría otra pasada completa de `coverage` sobre sv4 (~2 min) y
   **la puerta está en `[OK]` con 98,5 % sobre un umbral del 80 %**. La campaña
   de mutación, superviviente por superviviente, confirma que el hueco no está
   en la lógica de riesgo. *Motivo: coste desproporcionado frente a una puerta
   ya verde.*
2. **Las 6 verificaciones MANUAL de `design.md` §8.2** (portal levantado,
   PostgreSQL y navegador). Son **del humano**, están listadas con sus pasos y
   su SQL, y ninguna es automatizable en este repositorio. La 6 —comportamiento
   del combo en el navegador— es la única funcionalidad que ningún test cubre.
   *Motivo: no hay arnés de JS ni BBDD real aquí.*

---

## 7. Automejora del protocolo (propuesta, no aplicada)

1. **`progress/mutacion_*.md` debería registrar qué suite se ejecutó.** El
   arnés solo corre la del servicio dueño del fichero mutado. Aquí es inocuo
   —los cinco ficheros son de sv4—, pero en una feature que toque dos servicios
   el informe no permite detectarlo sin recalcular. *Propuesta: que
   `harness/mutacion.py` escriba una línea «Suite ejecutada: …» por fichero, y
   que `CHECKPOINTS.md` C4 bis pida al reviewer comprobarla.*
2. **`CHECKPOINTS.md` C4 podría pedir el recuento test-por-requisito.** Que
   cada requisito «tenga al menos un test» se comprueba hoy leyendo la tabla de
   trazabilidad de la spec; un recuento mecánico sobre los nombres
   `test_fXXX_rN_*` lo hace verificable en un comando y detecta un requisito
   con cero tests aunque la tabla diga otra cosa. Es lo que he hecho en §3/C4.

Las dos valen para cualquier proyecto ⇒ si el humano las aprueba, van a
`arnes-base` en el mismo trabajo.

---

## 8. Conclusión

F-016 hace lo que su spec dice, donde dice y sin salirse: **cero cambios de
schema, cero ficheros fuera de sv4, cero rutas nuevas de catálogo, cero
`DELETE`**. Lo que de verdad importa en una pantalla que edita el cómputo de
nóminas —que se valide antes de escribir, que un rechazo deje la tabla intacta,
que el solape no ajuste la fila ajena y que el humano nunca vea un `hasta`
exclusivo— está comprobado ejecutando, no leyendo. El rigor `estandar` se
cumple entero: fase RED con traza real en los cuatro requisitos exigidos,
cobertura 98,5 % y campaña de mutación completa con los 14 supervivientes
analizados y sus totales recalculados de forma independiente.

**APROBADO.** Queda pendiente del humano el bloque MANUAL de `design.md` §8.2
antes de dar la pantalla por buena en producción.
