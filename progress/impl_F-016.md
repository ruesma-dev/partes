<!-- progress/impl_F-016.md -->
# F-016 · Pantalla de administración de `empleado_jornada` (sv4) — informe del implementer

Rama `feature/F-016-admin-empleado-jornada` (desde `dev` `047eb5b`, con
F-015 ya mergeada) · rigor **estandar** · spec aprobada por el humano ·
**9 commits** de tarea más uno local en `azure-apps`. Las **seis
verificaciones MANUAL** de `design.md` §8.2 son del humano y quedan
pendientes (sección 8).

## 1. Qué cambió, en una frase

El portal gana la pantalla **`/admin/jornadas`**, que da de alta, edita,
cierra, desactiva y reactiva las excepciones de jornada de
`empleado_jornada` **sin salir a SQL**, hablando siempre en «último día
incluido» (nunca en `hasta` exclusivo), rechazando **antes de escribir** todo
lo que el resolutor de F-015 ignoraría en silencio, y rechazando con 409 —sin
tocar la fila ajena— cualquier vigencia que pise a otra activa del mismo DNI.
**Cero cambios de schema y cero ficheros fuera de sv4.**

## 2. Puerta de entrada (T0) — firmas reales encontradas

F-015 está mergeada en `dev` (`047eb5b Merge F-015: jornada del dia por
jornada semanal derivada del candef`) y las tres piezas existen. Las firmas
reales **coinciden** con lo que suponía `design.md` §4 y §5, y la semántica
heredada (`hasta` exclusivo, `is_active` como papelera, `origen` con tres
valores) **no ha cambiado**: no hubo que adaptar ningún nombre.

| Pieza | Dónde | Firma real |
|---|---|---|
| `EmpleadoJornadaOrm` | `services/partes-front/infrastructure/database/orm_models.py:283` | **19 columnas**: `id`, `dni_norm`, `jornada_semanal`, `h_lun`…`h_dom`, `desde`, `hasta`, `origen`, `nota`, `is_active`, `created_at_utc`, `created_by`, `updated_at_utc`, `updated_by` |
| `list_jornadas_empleado` | `…/database/parte_repository.py:1793` | `def list_jornadas_empleado(self) -> list[dict]` — solo filas **activas**, 14 claves (sin auditoría) |
| `JornadaEmpleadoProvider` | `…/application/services/jornada_provider.py` | `__init__(cargar, *, ttl_seconds=600, reloj=time.time)`, `excepcion_para(dni, fecha)`, `_indice()`; caché `(timestamp, índice)` bajo `RLock` |

Dos hallazgos menores, ninguno bloqueante:

1. **`sembrar_jornadas` ya existía**: lo dejó F-015 en
   `services/partes-front/tests/dobles.py`. T2 pedía crearlo. En vez de
   duplicarlo se le han añadido las **cuatro columnas de auditoría**
   (`created_at_utc`, `created_by`, `updated_at_utc`, `updated_by`), que el
   listado de R2 pinta y F-015 no necesitaba.
2. **`list_jornadas_empleado()` devuelve 14 claves, no las 19**: no incluye
   `is_active` (filtra por ella) ni la auditoría. Por eso F-016 **no la
   reutiliza** —tampoco la toca— y añade `list_jornadas_admin()`, que
   devuelve las 19 y también las inactivas.

## 3. Ficheros tocados

### Producción (todos en `services/partes-front/`, ninguno fuera)

| Fichero | Qué |
|---|---|
| `application/services/jornada_admin.py` | **nuevo** (368 líneas) · reglas **puras**: `JornadaInvalida`, `EntradaJornada`, `a_hasta_exclusivo`, `a_ultimo_dia_incluido`, `ultimo_dia_incluido_de_fila`, `normalizar_entrada`, `entrada_desde_fila`, `validar_vigencia`, `validar_entrada`, `buscar_solape`, `describir_conflicto`, `columnas_patron`, `DIAS`, `NOMBRE_DIA`, `ABREVIATURA_DIA` |
| `infrastructure/database/parte_repository.py` | **+5 métodos**: `list_jornadas_admin`, `crear_jornada`, `actualizar_jornada`, `cerrar_jornada`, `set_jornada_activa` (+ el helper `_jornada_admin_dict`). `list_jornadas_empleado()` de F-015 **intacta** |
| `interface_adapters/web/app.py` | `_actor`, `_exigir_admin_jornadas`, la página `GET /admin/jornadas` y los cinco endpoints JSON, más los helpers `_cuerpo`, `_rechazo`, `_conflicto`, `_no_encontrada`, `_invalidar_jornadas`, `_aviso_dni_desconocido`, `_fila_para_pantalla`; global `jornadas_admin_enabled` junto a `asset_version` |
| `application/services/jornada_provider.py` | **`invalidar()`** · lo ÚNICO que F-016 cambia de lo que dejó F-015 (R14) |
| `config/settings.py` | `jornadas_admin_enabled: bool = Field(True, alias="JORNADAS_ADMIN_ENABLED")` · **única variable nueva** |
| `templates/admin_jornadas.html` | **nueva** · formulario (con el selector de trabajador) + listado + aviso de caché |
| `templates/base.html` | enlace `Jornadas` en `<nav class="topnav">`, bajo `{% if jornadas_admin_enabled %}` |
| `static/app.js` | **+224 líneas, 0 modificadas**, dentro del IIFE que define `_comboSimple` |
| `static/styles.css` | **+2 reglas**: `.input-error` y `tr.is-conflicto` |

### Tests (los tres ficheros son nuevos)

| Fichero | Requisitos |
|---|---|
| `tests/test_f016_validacion_jornada_admin.py` | R7, R8, R9, R10, R11, R12 (unidad), R18 — **40 tests**, sin app y sin BBDD |
| `tests/test_f016_endpoints_admin_jornadas.py` | repositorio (T2) + R3, R4, R5, R6, R12 (409 por HTTP), R13, R16, R19 — **52 tests** |
| `tests/test_f016_vista_admin_jornadas.py` | R1, R2, R14, R15, R17, R20 — **42 tests** |
| `tests/dobles.py` | `sembrar_jornadas` acepta las cuatro columnas de auditoría |

### Documentación

`docs/referencia/partes-proyecto.md` (§5.4 actualizada y **§5.4.1 nueva**) y
`C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (commit local `767392d`,
**sin push**: ese repositorio no tiene remoto).

### Lo que NO se ha tocado (comprobado sobre el diff)

- **Ni un fichero de sv3, sv1, sv2, sv5 ni `infra/`.** El diff de la rama solo
  contiene `services/partes-front/`, `specs/F-016-*`, `progress/`, `docs/` y
  el `harness/features.json` que movió el líder.
- **Las dos copias de `orm_models.py`** y `tests/test_f010_orm_models_gemelos.py`:
  cero cambios. El guardián de F-010 sigue en verde **sin haberse modificado**.
- **`_comboSimple`, `MotivoHttp`, `EmpleadoCatalog`, `nuevo_parte.html`** y
  **ninguna ruta `/api/sigrid/*`**:
  `git diff dev -- …/app.py | grep -E "^[+-].*api/sigrid"` no devuelve **ni una
  línea**, y un test lo fija comparando el conjunto de rutas `/api/sigrid/*`
  de la app con las cuatro que ya existían.
- **Ningún test existente se modificó.** Los 717 tests de sv4 anteriores
  siguen pasando tal cual.

## 4. Qué se hizo en cada tarea

### T0 · Puerta de entrada
Verificada (sección 2). `bash harness/init.sh` en verde sobre la rama antes de
escribir nada.

### T1 · Validación pura (commit `292f400`)

`jornada_admin.py`, módulo **puro** (ni BBDD, ni FastAPI, ni logging), vecino
de `congelacion.py`. Lo que hay que saber de él:

- La conversión **«último día incluido» ⇄ `hasta` exclusivo** vive aquí y solo
  aquí, con `date + timedelta(days=1)`, **nunca** aritmética de cadenas.
- `_fecha()` no acepta `date.fromisoformat` a secas: exige el formato
  `AAAA-MM-DD` de diez caracteres, porque en 3.12 `fromisoformat` traga
  `20260701`, que el `<input type="date">` no manda nunca.
- `buscar_solape` compara sobre `date` y con la regla `d1 < h2 and d2 < h1`
  (`None` = infinito). De esa forma **las contiguas no solapan sale gratis**,
  no como un caso especial que alguien pueda borrar por descuido.
- Una fila **ya guardada** con basura en `desde` o `hasta` (las cargó el humano
  por SQL hasta F-016) **no bloquea** un alta correcta ni rompe el listado:
  se salta en la comparación y se pinta tal cual. Los dos casos tienen test.

**Fase RED (traza real).**
`cd services/partes-front && python -m pytest tests/test_f016_validacion_jornada_admin.py -q`

```
=================================== ERRORS ====================================
________ ERROR collecting tests/test_f016_validacion_jornada_admin.py _________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\partes\services\partes-front\tests\test_f016_validacion_jornada_admin.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f016_validacion_jornada_admin.py:21: in <module>
    from application.services.jornada_admin import (
E   ModuleNotFoundError: No module named 'application.services.jornada_admin'
=========================== short test summary error ==========================
ERROR tests/test_f016_validacion_jornada_admin.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.20s
```

Esa traza cubre la RED de **R7 y R12**: los dos tests exigidos
(`test_f016_r7_hasta_exclusivo`, `test_f016_r12_solape`) estaban escritos y no
podían pasar porque el módulo no existía.

**Verde.** `40 passed in 0.09s`.

### T2 · Repositorio (commit `281f531`)

Los cinco métodos, con el idioma del repositorio único de sv4
(`with self._session_factory.create_session() as session: … session.commit()`)
e instantes `datetime.now(timezone.utc).isoformat()`, igual que
`upsert_empleado_alias`. `origen='manual'` lo pone el servidor **aunque el
cliente mande otra cosa** (hay test). Los cuatro métodos de modificación
devuelven `False` si el id no existe, sin lanzar.

**Ningún `DELETE`.** `grep -niE "delete|session.delete"` sobre el bloque nuevo
devuelve **una sola línea, y es el comentario** que explica por qué no lo hay:

```
3:    # AQUI NO HAY NINGUN `DELETE`, y no es un descuido: la papelera de
```

**Verde.** `12 passed` (repositorio) · suite de sv4 entera `717 passed`.

### T3 · Configuración, puerta y actor (commit `f10d976`)

- `JORNADAS_ADMIN_ENABLED`, default **`true`**.
- **`_exigir_admin_jornadas()`**: la puerta, escrita **una sola vez**. Un test
  lo fija leyendo el propio `app.py`: `settings.jornadas_admin_enabled`
  aparece **exactamente 2 veces** (la puerta y el global de la plantilla), la
  función se declara **1 vez** y las **6 rutas** la llaman como primera línea.
  Cuando llegue F-008, el rol se escribe ahí y en ningún otro sitio.
- **`_actor(request)`**: punto único de identidad. Devuelve
  `settings.default_reviewer` y **no lee ninguna cabecera** (eso es F-017).
  Un test comprueba que el bloque de F-016 **no contiene**
  `settings.default_reviewer` ni una vez y que las **cinco escrituras** piden
  el actor al mismo helper.

**Fase RED (traza real).** `python -m pytest tests/test_f016_vista_admin_jornadas.py -q`
antes de escribir la puerta:

```
FAILED tests/test_f016_vista_admin_jornadas.py::test_f016_r15_con_la_variable_a_verdadero_las_seis_responden[get-/admin/jornadas-None]
FAILED tests/test_f016_vista_admin_jornadas.py::test_f016_r15_con_la_variable_a_verdadero_las_seis_responden[post-/api/admin/jornadas-cuerpo1]
FAILED tests/test_f016_vista_admin_jornadas.py::test_f016_r15_con_la_variable_a_verdadero_las_seis_responden[patch-/api/admin/jornadas/1-cuerpo2]
FAILED tests/test_f016_vista_admin_jornadas.py::test_f016_r15_con_la_variable_a_verdadero_las_seis_responden[post-/api/admin/jornadas/1/cerrar-cuerpo3]
FAILED tests/test_f016_vista_admin_jornadas.py::test_f016_r15_con_la_variable_a_verdadero_las_seis_responden[post-/api/admin/jornadas/1/desactivar-cuerpo4]
FAILED tests/test_f016_vista_admin_jornadas.py::test_f016_r15_con_la_variable_a_verdadero_las_seis_responden[post-/api/admin/jornadas/1/reactivar-cuerpo5]
FAILED tests/test_f016_vista_admin_jornadas.py::test_f016_r15_el_interruptor_llega_encendido_de_fabrica
FAILED tests/test_f016_vista_admin_jornadas.py::test_f016_r15_el_enlace_de_la_barra_sigue_al_interruptor
FAILED tests/test_f016_vista_admin_jornadas.py::test_f016_r15_hay_exactamente_una_funcion_que_decide_el_acceso
9 failed, 7 passed, 1 warning in 4.08s
```

con este detalle, que es el que importa:

```
        fuente = (Path(__file__).resolve().parents[1]
                  / "interface_adapters" / "web" / "app.py").read_text(
                      encoding="utf-8")
>       assert fuente.count("settings.jornadas_admin_enabled") == 2, (
            "solo la puerta unica y el global de la plantilla pueden leer el "
            "interruptor")
E       AssertionError: solo la puerta unica y el global de la plantilla pueden leer el interruptor
E       assert 0 == 2
```

**Por qué esa RED prueba algo.** El caso «apagada ⇒ 404» pasa en verde con la
feature **entera sin escribir**, porque una ruta que no existe también da 404.
Los nueve que fallan son la otra mitad —«encendida ⇒ no es 404», el default,
el enlace de la barra y el punto único—, que es lo que no se puede fingir.

**Nota de honestidad sobre el orden de los commits.** El commit de T3 lleva
**solo el código de producción**; el fichero de tests de la vista entró en el
commit de T5, cuando ya podían pasar todas sus aserciones (las de R15 hablan
de rutas que crean T4 y T5). Por la misma razón, los commits de **T6 y T7 van
antes que el de T5**: así **cada commit de la rama queda en verde** y un
`git bisect` no encuentra ninguno roto a mitad.

**Sobre `.env.example`.** El diseño (§4) pedía añadir ahí la variable. Se ha
añadido **en local**, pero **no se versiona**: este repositorio lo ignora por
la regla `*.example` de `services/partes-front/.gitignore:189`, y forzarlo con
`git add -f` sería revertir una decisión del repositorio por la puerta de
atrás. El `.env` real **no se ha tocado**.

### T4 · Los cinco endpoints (commit `2e7485e`)

Las tres reglas que se repiten en los cinco, y que son la feature:

1. **Se valida antes de escribir.** `normalizar_entrada` → `validar_entrada`
   → `buscar_solape` → y solo entonces el repositorio.
2. **Un rechazo deja la BBDD intacta.** Cada test de rechazo cuenta la tabla
   **antes y después** (`_cuantas`), incluidos los ocho casos parametrizados
   de 422 y el 409 de solape, que además comprueba que **la fila ajena sigue
   igual** (`hasta` sin tocar).
3. **No hay `DELETE`.** Un test encadena desactivar/reactivar/desactivar +
   editar + cerrar sobre la misma fila y exige `count(*) == 1`.

Decisiones de la capa web:

- `JornadaInvalida` → 422 con un `try/except` **local** en cada endpoint, no
  con un `exception_handler` global: un handler global la metería en el
  contrato de todo el portal, y esta excepción es de esta pantalla.
- **Cerrar no revalida el solape** a propósito: cerrar solo *acorta* la
  vigencia, así que no puede crear un solape nuevo. Sí valida R11
  (`hasta > desde`) reusando `validar_vigencia`.
- **Reactivar sí revalida**: mientras estuvo inactiva, su hueco pudo ocuparse.
  Si choca, 409 y **la fila se queda inactiva**; ni ella ni la otra se tocan.
- `_aviso_dni_desconocido` y `_invalidar_jornadas` leen su colaborador de
  `app.state`, no del cierre de `build_app`. Es lo que permite probar
  «catálogo apagado ⇒ **cero** llamadas a Sigrid» y «sin proveedor ⇒ la
  escritura sigue funcionando» sin inventar parámetros que solo usan los tests.
- Un cuerpo ilegible (no-JSON) sale como **422 con motivo**, no como 500.

**Verde.** `52 passed`.

### T5 · Página, plantilla y selector (commit `818c742`)

- `GET /admin/jornadas` y `?editar=<id>` **relleno desde el servidor** (PRG,
  cero JS de precarga). Un id que no existe **cae al modo alta** en vez de dar
  404: la página sigue siendo útil.
- **`hasta` no viaja a la plantilla.** La vista traduce cada fila con
  `ultimo_dia_incluido_de_fila` antes de pasarla. El test de R2 comprueba que
  el HTML trae `2026-07-31` (para `hasta = 2026-08-01`) y que **la palabra
  «exclusiv» no aparece en ningún sitio de la página**.
- **Selector (R20)**: marcado `combo-simple` / `combo-panel` copiado de
  `nuevo_parte.html`, con el campo oculto `jor-dni` y
  `data-empleados-url="/api/sigrid/empleados"`. Con
  `sigrid_lookup_enabled` falso —que es como corre la suite— el combo llega
  **deshabilitado** con el placeholder «Sigrid no configurado» y el checkbox
  «El trabajador no está en la lista» llega **marcado** con su campo de texto
  **descubierto**. En modo edición no se pinta ni combo ni alta manual: solo
  el DNI en un campo `readonly`.
- **Cero CSS nuevo aquí**: el panel del formulario reutiliza `nuevo-form`, que
  es lo que da estilo a `.field` y a los `label`.

**Verde.** `42 passed`.

### T6 · Aviso de caché e invalidación (commit `0fd0a79`)

`JornadaEmpleadoProvider.invalidar()` vacía la caché bajo el mismo `RLock` que
la escribe. Se llama tras **cada escritura con éxito** y **solo** con éxito.

El aviso de la página lleva los minutos **derivados** de
`settings.jornada_cache_ttl_s`, redondeando **hacia arriba** (para no prometer
menos espera de la real): 600 s ⇒ «10 minutos», 900 s ⇒ «15 minutos». Los dos
casos son test.

**Fase RED (traza real).**
`python -m pytest tests/test_f016_vista_admin_jornadas.py -q -k "proveedor_de_verdad"`

```
____________ test_f016_r14_el_proveedor_de_verdad_sabe_invalidarse ____________

    def test_f016_r14_el_proveedor_de_verdad_sabe_invalidarse() -> None:
        """El doble no vale como unica prueba: `invalidar()` existe y funciona."""
        from application.services.jornada_provider import JornadaEmpleadoProvider

        lecturas = []

        def cargar():
            lecturas.append(1)
            return []

        proveedor = JornadaEmpleadoProvider(cargar, ttl_seconds=600)
        proveedor.excepcion_para(DNI, __import__("datetime").date(2026, 7, 1))
        proveedor.excepcion_para(DNI, __import__("datetime").date(2026, 7, 1))
        assert len(lecturas) == 1               # la segunda salio de la cache
>       proveedor.invalidar()
        ^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'JornadaEmpleadoProvider' object has no attribute 'invalidar'

tests\test_f016_vista_admin_jornadas.py:346: AttributeError
```

Ese test existe porque **el doble no vale como única prueba**: un
`ProveedorFake` que cuenta llamadas seguiría en verde aunque el proveedor real
no supiera invalidarse. Aquí se comprueba sobre el objeto de verdad que la
segunda consulta sale de la caché y que, **tras invalidar, relee**.

**Aviso honesto sobre esta RED.** La mitad de R14 que vive en los endpoints
(«cada escritura con éxito invalida una vez, un rechazo no invalida») se
escribió *después* de que `_invalidar_jornadas` ya existiera en T4, así que
**de esa mitad no hay traza roja**. La traza de arriba es la de la pieza que
T6 entrega, que es a la que `tasks.md` ata la fase RED de R14.

### T7 · El JS (commit `c6d6d64`)

**224 líneas añadidas, 0 modificadas** (`git diff --numstat dev` ⇒ `224 0`).
El bloque va **dentro del IIFE grande**, justo antes de su `})();` (que estaba
en la línea 2228), porque `_comboSimple` es privado de ese IIFE y desde uno
nuevo al final del fichero **no se vería**.

- El selector se cabla con **una sola llamada** a `_comboSimple`, con el
  `render` que pone el **DNI delante** del nombre. El filtro del componente ya
  mira `it.dni` aparte de la etiqueta, así que **la búsqueda incremental por
  DNI funciona sin añadir nada**.
- El DNI viaja **siempre por el mismo campo oculto**, venga del combo o del
  alta manual (DA12).
- **Un ajuste que conviene que el reviewer mire.** `MotivoHttp.lanzarSiFalla`
  lanza un `Error` con `message`, `congelado` y `status`, pero **no** con el
  cuerpo del rechazo; sin él no se puede ni marcar el campo culpable (`campo`
  del 422) ni señalar la fila del 409. Como `MotivoHttp` es compartido y no se
  toca, F-016 **clona la respuesta antes** de dársela al componente y adjunta
  el cuerpo en `err.data`. Cero líneas ajenas modificadas.
- Dos reglas CSS nuevas, las únicas que faltaban de verdad: `.input-error`
  (campo señalado por un 422) y `tr.is-conflicto` (fila nombrada por un 409),
  ambas con las variables de color que ya existen.

`node --check services/partes-front/static/app.js` **sin salida**.

### T8 · Documentación (commits `efa2d03` y, en `azure-apps`, `767392d`)

`docs/referencia/partes-proyecto.md`: §5.4 dice ahora que las filas se
mantienen desde el portal, y la **§5.4.1 nueva** explica el criterio «último
día incluido», que cerrar ≠ desactivar, que el solape se rechaza sin ajustar
la fila ajena, el retardo de sv3 y el interruptor.

`azure-apps/partes.md`: la vista **Jornadas**, la tabla de las **seis rutas**
que expone sv4 y `JORNADAS_ADMIN_ENABLED` en la fila de variables de sv4, con
la nota de que **no va al manifiesto**. Commit **local, sin push** (ese
repositorio no tiene remoto).

**Barrido de sensibles sobre lo añadido en la rama**
(`git diff dev | grep "^+" | grep -niE "password|secret|token|api.?key|connection.?string|[0-9]{8}[A-Za-z]|@ruesma|subscription|tenant"`):
12 coincidencias, **todas benignas y revisadas una a una** — nombres de
variables de entorno (`SESAME_API_KEY`, `PG_PASSWORD` como *clave*, no como
valor), las contraseñas de prueba `"irrelevante-en-tests"` de los fixtures,
texto de la propia spec sobre la cabecera de Easy Auth y el comando de barrido
copiado de `tasks.md`. **Ni un secreto, ni un DNI real, ni un nombre de
persona.** Los DNIs de los tests son sintéticos (`AAA1`, `BBB2`, `1234ABCD`,
`00000000T`).

## 5. Decisiones tomadas durante la implementación

1. **`ultimo_dia_incluido_de_fila` aparte de `a_ultimo_dia_incluido`.** La
   segunda **lanza** si la fecha es ilegible, que es lo correcto para lo que
   escribe el humano. Pero *pintar* una fila ya guardada con basura en `hasta`
   no puede tumbar la página entera: para eso está la primera, que devuelve el
   valor tal cual para que se vea y se corrija desde la propia pantalla.
2. **El repositorio importa `columnas_patron` de `application`.** No es una
   inversión de capas nueva: `parte_repository.py` ya importa `text_match` y
   `congelacion` de ahí (F-004). La alternativa —repetir la lista de las siete
   columnas en el repositorio— es exactamente la duplicación que se quiere
   evitar.
3. **`_aviso_dni_desconocido` y `_invalidar_jornadas` leen `app.state`.** Ver
   T4. Es lo que hace testeable «con el catálogo apagado no se llama a Sigrid»
   sin meter parámetros de test en el código de producción.
4. **`_fecha()` valida el formato a mano antes de `fromisoformat`.** Explicado
   en T1: `fromisoformat` de 3.12 acepta formas que el formulario nunca manda,
   y colarlas por la API dejaría fechas que el resto del sistema lee como
   texto ISO de diez caracteres.
5. **El listado ordena también por `id` descendente** como tercer criterio,
   detrás de `dni_norm ASC, desde DESC`: sin él, dos filas del mismo DNI y el
   mismo `desde` (que R12 impide crear, pero que pueden existir de la carga
   manual) saldrían en orden indefinido y el test sería intermitente.
6. **Orden de los commits T5/T6/T7.** Explicado en T3: T6 y T7 se commitean
   antes que T5 para que ningún commit de la rama quede en rojo.

## 6. Resultado de los tests

| Suite | Resultado |
|---|---|
| `services/partes-front` (sv4) entera | **799 passed** en 114,06 s |
| solo F-016 (`-k f016`) | **134 passed**, 665 deselected, en 40,04 s |
| `tests/` (raíz del monorepo) | **92 passed** en 6,27 s — incluye el guardián de F-010 **sin modificar** |
| `services/partes-persistencia` (sv3) | en verde (caché del arnés: árbol sin cambios) |
| `services/partes-transfer` (sv5) | en verde (caché del arnés: árbol sin cambios) |

`bash harness/init.sh` termina con **ENTORNO LISTO**.

## 7. Informe de mutación (T9)

`python -m harness.mutacion --feature F-016 --workers 6 --timeout 600`, lanzada
**una sola vez y al final**. Detalle completo, superviviente por superviviente,
en **`progress/mutacion_F-016.md`**; aquí, el resumen.

| Métrica | Valor |
|---|---|
| Ficheros en alcance | 5 (827 líneas de producción) |
| Mutantes generados y evaluados | **93** (campaña completa, sin muestreo) |
| Muertos | **79** (85 %) |
| Supervivientes | **14**, los 14 analizados |
| **Timeouts** | **0** |
| Tiempo total | 1409,6 s |

**Los parámetros no son decorativos.** Con el `timeout_por_mutante_s: 120` por
defecto de `rigor.json` y la suite de sv4 en ~115 s, la campaña habría dado
timeouts masivos —que no son una medición— en vez de veredictos; es la lección
que dejó F-015. Con 600 s de margen y 6 workers salieron **0 timeouts**.

**Los 14 supervivientes, en tres grupos:**

| Grupo | Cuántos | Qué son |
|---|---|---|
| Equivalentes de verdad | 4 | `zip` trunca a siete (`[None]*7` vs `*8`); `//60` vs `//61` **da el mismo número para todo TTL múltiplo de 60 hasta 3600 s** (comprobado numéricamente, el primero que difiere es 3660); `exc_info` es diagnóstico; el `or`→`and` de la guarda de formato acaba en el **mismo** 422 con el **mismo `campo`** |
| Fuera del contrato observable | 5 | `include_in_schema=False` → `True`: solo afecta al OpenAPI. **Un solo test los mataría los cinco** |
| Huecos reales, acotados | 5 | inmutabilidad de `EntradaJornada`; el suelo del aviso con TTL < 120 s; «sin fin» en el **texto** del 409; el campo `ok` del cuerpo de desactivar y reactivar |

**Lo que de verdad dice la campaña.** Los mutantes sobre la lógica de riesgo
**murieron todos**: los cuatro extremos del solape (`>=`↔`>`, `and`↔`or`,
`<`↔`<=`), la conversión de fechas (`days=1`→`days=2`), los rangos de R9 y R10
en sus cuatro límites, la exclusión de la propia fila al editar, el filtro por
`is_active`, el `origen='manual'` forzado y el 404 de la puerta de acceso. Eso
es lo que había que comprobar en una pantalla que edita el cómputo de nóminas.

**Tres mejoras anotadas y no aplicadas**, por orden de valor: (1) que el 409
contra una vigencia abierta diga «sin fin» y no `None` —el único superviviente
con consecuencia visible—; (2) `assert respuesta.json()["ok"] is True` en
desactivar y reactivar; (3) un test sobre `app.openapi()["paths"]`. **No se
aplican en esta feature a propósito**: el nivel `estandar` exige supervivientes
**analizados**, no cero supervivientes, y añadir tests después de medir dejaría
estos números sin corresponder con el árbol que el reviewer va a leer.

**Exit code 1 es lo esperado** cuando quedan supervivientes; no es un fallo de
ejecución (`supervivientes_maximos: null` en el nivel `estandar`).

**Sobre cómo se ejecutó.** La campaña tarda ~23 minutos y el `timeout` máximo de
una llamada en primer plano es de 10, así que se lanzó **en segundo plano** y se
esperó su notificación de salida —una sola ejecución, sin relanzarla—. Es el
mecanismo que la propia herramienta recomienda para «una notificación cuando
termine», y no es un monitor de los que se quedaron colgados en F-015.

## 8. Verificaciones MANUAL (humano) — pendientes

Son las seis de `design.md` §8.2. Ninguna se puede hacer aquí: exigen
PostgreSQL, el portal levantado y un navegador.

1. **Alta en local.** Portal en `/admin/jornadas`, crear una excepción con
   `S = 48` para un trabajador de pruebas y comprobar en la base:
   ```sql
   SELECT id, dni_norm, jornada_semanal, desde, hasta, origen, is_active, created_by
   FROM empleado_jornada ORDER BY id DESC LIMIT 5;
   ```
   Lo que debe verse: `origen='manual'`, `is_active=true`, `created_by` con
   `DEFAULT_REVIEWER` y **`hasta` un día después** del que se escribió.
2. **Solape en pantalla.** Intentar una segunda vigencia que pise la primera:
   debe salir el aviso rojo nombrando la fila en conflicto, resaltarse esa fila
   de la tabla, y `SELECT count(*) FROM empleado_jornada;` debe dar **lo mismo
   antes y después**.
3. **Efecto en caliente.** Tras crear la excepción, el KPI de jornada de la
   vista del trabajador (F-015 R25) debe reflejarla enseguida en el portal;
   sv3 tarda hasta `JORNADA_CACHE_TTL_S`.
4. **Estáticos.** `Ctrl+F5` tras desplegar (convención de sv4).
   `node --check services/partes-front/static/app.js` ya se ha ejecutado aquí:
   **sin salida**.
5. **Identidad.** Con F-017 aún sin hacer, lo esperado en `created_by` es
   `DEFAULT_REVIEWER`, y **eso es correcto, no un fallo**.
6. **Selector de trabajador (R20)** en el navegador — lo único que ningún test
   cubre: teclear tres letras del nombre y ver la lista; teclear tres cifras
   del DNI y ver la misma lista filtrada; elegir uno y comprobar que el alta
   guarda **ese** DNI normalizado; marcar «no está en la lista», dar de alta un
   DNI que no exista en Sigrid y ver que **la fila se crea igual** con el aviso
   de R19. Repetirlo con Sigrid apagado (sin `SIGRID_API_BASE_URL`): el combo
   debe salir deshabilitado y el camino manual funcionar entero.

## 9. Evidencias

Números **medidos**, no estimados, y comparables con los de features anteriores.

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests ejecutados y resultado** | **799 passed, 0 failed** (suite de sv4); de ellos **134 nuevos de F-016**. Raíz del monorepo: **92 passed**. sv3 y sv5: en verde | `python -m pytest` de cada suite y `bash harness/init.sh` |
| **Cobertura de las líneas cambiadas** | **98,5 % — 326 de 331 líneas** (umbral del nivel `estandar`: 80 %) | línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Mutantes generados / supervivientes** | **93 generados, 79 muertos, 14 supervivientes, 0 timeouts** (85 % de mortalidad); los 14 **analizados uno a uno** | `python -m harness.mutacion --feature F-016 --workers 6 --timeout 600` → `progress/mutacion_F-016.md` |
| **Tiempo de ejecución de la suite** | sv4 **114,06 s** (799 tests) · solo F-016 **40,04 s** (134 tests) · raíz **6,27 s** (92 tests) · campaña de mutación **1409,6 s** | salida de las propias suites |

Notas de honestidad sobre estos números:

- **La suite de sv4 ha pasado de ~52 s a ~114 s** con F-016. La causa es que
  cada test de endpoint o de vista levanta la app entera con `build_app`, que es
  el montaje que usan F-002, F-003 y F-004: no se ha inventado nada, pero 134
  tests nuevos con ese patrón cuestan unos 60 s. Es lo que hace que la campaña
  de mutación necesite `--timeout 600`. Queda dicho por si en el futuro alguien
  quiere una fixture de app compartida — sería una mejora transversal del
  servicio, no de esta feature.
- **Las 5 líneas cambiadas sin cubrir**: el arnés da el porcentaje agregado y no
  las enumera, y no se han listado a mano para no lanzar una segunda medición de
  cobertura mientras corría la campaña de mutación. Con 98,5 % sobre 331 líneas
  y 79 de 93 mutantes muertos, el hueco no está en la lógica de riesgo: la
  campaña lo confirma superviviente por superviviente.
- **Rigor `estandar` cumplido**: fase RED con traza real en **R7, R12** (T1),
  **R15** (T3) y **R14** (T6); cobertura por encima del umbral; campaña de
  mutación con **cero** secciones en `PENDIENTE`.
