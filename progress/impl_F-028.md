<!-- progress/impl_F-028.md -->
# F-028 · Detalle de obra y de trabajador a todo el ancho — Informe del implementer

Rama `feature/F-028-ancho-detalle`, **solo sv4**, `sdd: false`, rigor
`estandar`. Contrato: la entrada de F-028 en `harness/features.json`
(descripción + 4 `acceptance`). Sin despliegue, sin push, sin secretos, sin
tocar Sigrid ni PostgreSQL.

## 1. Qué cambió

| Commit | Tarea | Qué |
|---|---|---|
| `a1a7731` | T1 | Plantillas, CSS y tests (abajo) |
| (siguiente) | T2 | `progress/current.md` (F-028 en curso, M1) y este informe |

Ficheros tocados (`services/partes-front/`):

- `templates/base.html`: el div del `<main class="page-shell">` pasa a
  `<div class="container{% block container_class %}{% endblock %}">`.
  Bloque vacío por defecto ⇒ el resto de páginas renderiza `class="container"`
  exactamente igual que antes. La topbar (`container topbar-inner`) no se toca.
- `templates/obra_detail.html` y `templates/trabajador_detail.html`:
  `{% block container_class %} container--ancho{% endblock %}`.
- `static/styles.css` (justo detrás de `.container`, línea 76–77):
  `.container--ancho { width: calc(100% - 32px); }`. Misma especificidad que
  `.container` y declarada después ⇒ pisa su `width: min(1500px, …)`; el
  `margin: 0 auto` se hereda de `.container`.
- `tests/test_f028_ancho_detalle.py` (nuevo, 13 tests).

Caché del navegador: `asset_version` es `int(time.time())` al arrancar la app
(`app.py:595`), así que tras un despliegue el CSS nuevo se sirve con otra
`?v=`; en local basta Ctrl+F5.

## 2. Otros topes de ancho revisados (punto 3 del encargo)

Revisado `styles.css` y las clases que usan las dos plantillas de detalle:
**no hay otro tope que limite el detalle**. `.panel` (sin ancho, `overflow:
hidden`), `.matrix-scroll` y `.table-scroll` (solo `overflow-x: auto`),
`.table` (`width: 100%`), `.page-header`, `.stat-grid`, `.cal-grid` y
`.sel-tools` no fijan máximo. Los `max-width` que existen son de elementos
internos (`.mx-name` 260 px, `.mx-cat` 110 px, combos 460–520 px, modales,
`.manual-q`), que no limitan el ancho del contenedor. No se amplía alcance.

## 3. Decisiones y desviaciones

- Nombre de bloque `container_class` y clase `container--ancho`, los
  sugeridos en el encargo. El bloque incluye el espacio inicial en la
  plantilla hija (` container--ancho`) para que el valor por defecto sea
  literalmente `class="container"` (verificado por test en los listados).
- Sin desviaciones respecto al contrato.
- Documentación: ni `docs/ARCHITECTURE.md` ni `azure-apps/` describen el
  ancho del portal (búsqueda de `1500px` / `.container`: sin resultados
  relevantes). No cambia nada expuesto ni consumido: no se tocan.

## 4. Fase RED

Tests escritos antes del cambio. Comando y salida real (resumida a las líneas
de resultado; el resto es el traceback estándar de pytest):

```
$ cd services/partes-front && python -m pytest tests/test_f028_ancho_detalle.py -q -p no:cacheprovider
FFFF.........                                                            [100%]
...
>       assert CLASE_ANCHA in clases
E       AssertionError: assert 'container--ancho' in ['container']
...
>       assert m, f"no hay regla para {selector}"
E       AssertionError: no hay regla para .container--ancho
...
>       pos_ancha = re.search(re.escape("." + CLASE_ANCHA) + r"\s*\{", css).start()
E       AttributeError: 'NoneType' object has no attribute 'start'
=========================== short test summary info ===========================
FAILED tests/test_f028_ancho_detalle.py::test_f028_r1_detalle_contenedor_main_con_clase_ancha[/obras/obr-10?period=2026-03&modo=natural]
FAILED tests/test_f028_ancho_detalle.py::test_f028_r1_detalle_contenedor_main_con_clase_ancha[/trabajadores/emp-77?period=2026-03&modo=natural]
FAILED tests/test_f028_ancho_detalle.py::test_f028_r1_css_clase_ancha_sin_tope
FAILED tests/test_f028_ancho_detalle.py::test_f028_r1_css_clase_ancha_despues_de_container
4 failed, 9 passed, 1 warning in 9.16s
```

Los 9 que ya pasaban en RED son los de **no regresión** (acceptance 2 y 3:
listados sin clase ancha, `.container` con su tope de 1500 px, topbar igual):
pasar antes y después es exactamente lo que deben hacer.

GREEN tras el cambio, mismo comando:

```
13 passed, 1 warning in 6.98s
```

## 5. Trazabilidad acceptance → tests (`tests/test_f028_ancho_detalle.py`)

| Acceptance | Tests |
|---|---|
| 1 · detalles con clase ancha y sin tope | `test_f028_r1_detalle_contenedor_main_con_clase_ancha` (obra y trabajador, HTML real vía `TestClient` + SQLite en memoria), `test_f028_r1_css_clase_ancha_sin_tope` (`width: calc(100% - 32px)`, sin `1500px`, `min(` ni `max-width`), `test_f028_r1_css_clase_ancha_despues_de_container` (orden de cascada) |
| 2 · listados con tope de 1500 px | `test_f028_r2_listado_contenedor_main_sin_clase_ancha` (`/obras`, `/trabajadores`, `/partes`: clase exactamente `["container"]`), `test_f028_r2_css_container_conserva_tope_1500` |
| 3 · topbar sin cambios | `test_f028_r3_topbar_sin_cambios` (las 5 URLs: `["container", "topbar-inner"]`) |
| 4 · suite de sv4 en verde | §6 |

El render de las dos plantillas por `TestClient` cubre también el parseo
Jinja2 que pide `docs/CONVENTIONS.md`. `app.js` no se toca (no aplica
`node --check`).

## 6. Verificación real

- Suite de sv4 directa (`python -m pytest -q` en `services/partes-front`):
  `1548 passed, 1 warning in 204.09s (0:03:24)`.
- `bash harness/init.sh` (tras T1): **ENTORNO LISTO**. Raíz `419 passed,
  1 skipped in 66.47s`; sv4 re-ejecutada (no caché) `1548 passed, 1 warning
  in 367.31s (0:06:07)`; sv1, sv2, sv3, sv5 en verde (caché, árbol sin
  cambios); `PUERTA COBERTURA: N/A (F-028 no cambia líneas Python de
  producción frente a dev)`; `PUERTA TAMAÑO` dentro de topes; ruff 557 avisos
  de deuda previa (no bloquea). El `init.sh` final, tras el commit de T2, se
  vuelve a lanzar antes de responder al líder.

## 7. Fuera de alcance

- Rehacer las columnas de la tabla de líneas (fuera por contrato).
- El resto de páginas (conciliación, papelera, nuevo, admin de jornadas,
  detalle de parte) conserva el tope de 1500 px; si alguna lo necesita, basta
  rellenar el mismo bloque en su plantilla (feature aparte).

## 8. Pendiente MANUAL (humano)

**M1** — tras desplegar sv4 (lo decide el humano) y Ctrl+F5: abrir el detalle
de una obra y el de un trabajador en la ventana ancha (monitor de 3440 px) y
comprobar que el contenido ocupa todo el ancho menos 16 px por lado y que la
matriz de días y la tabla de líneas no sacan scroll horizontal cuando caben;
abrir Obras (listado) y comprobar que sigue centrado a 1500 px. El CSS real
del navegador no tiene arnés: los tests solo garantizan clase y regla.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | sv4: 1548 passed (13 nuevos de F-028); raíz: 419 passed, 1 skipped |
| Cobertura de líneas cambiadas | N/A: `PUERTA COBERTURA: N/A (F-028 no cambia líneas Python de producción frente a dev)`. El cambio es Jinja2 + CSS, cubierto por los tests de render y de lectura del CSS |
| Mutantes generados / supervivientes | 0 / 0, sin informe: `python -m harness.mutacion --feature F-028` termina con `ALCANCE VACÍO en F-028: ni una línea de producción que mutar` (exit 2, 0 ficheros, 0 líneas Python de producción). La herramienta solo muta Python; las plantillas y el CSS no son mutables con ella. Sustituto: los 4 tests RED de §4 hacen de mutación manual (quitar la clase o la regla los pone en rojo) |
| Tiempo de la suite | sv4 204,09 s (directa) / 367,31 s (dentro de `init.sh`); raíz 66,47 s; tests de F-028 6,98 s |
