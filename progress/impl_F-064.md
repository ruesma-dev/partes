<!-- progress/impl_F-064.md -->
# F-064 · Informe del implementer — el filtro del portal se mantiene durante la sesión

Rama `feature/F-064-filtro-en-sesion` (worktree `partes-wt-f064`), desde 2b2c735. Rigor
**estándar**. Solo sv4 (+ `docs/ARCHITECTURE.md`). DA1–DA7 = A; M0 del líder: 8 h.

## Qué cambió (un commit por tarea)

| Tarea | Commit | Qué |
|---|---|---|
| T1 | b85b574 | `tests/test_f064_clave_usuario.py` (9) y `tests/test_f064_filtros_js.py` (89) en ROJO |
| T2 | 5d08d0b | `clave_filtros(actor, origen)` en `identidad.py`; global Jinja `clave_filtros_de` en `app.py` (tras `_actor`, delega en `_resolver_identidad`); `<body data-filtros-usuario>` en `base.html` |
| T3 | 900ae84 | IIFE global `FiltrosSesion` en `static/app.js` tras `avisarCambioLineas`: constantes y puras |
| T4 | 98a751a | `_setupDaySelection` devuelve `{claves, disponibles, seleccionar, limpiar}`; `wireDayFilters` el de la página o uno nulo |
| T5 | 29e1f43 | DOM de `FiltrosSesion` (leer/escribir/barrer, foto, guardar, redirigir, restaurar, aviso, quitarTodo) + 2 líneas del `DOMContentLoaded` principal |
| T6 | a0b2156 | «Limpiar» de `partes_list`, `obras_list`, `trabajadores_list` ⇒ `?search=` |
| T7 | 2a4ebf0 | `docs/ARCHITECTURE.md` punto 11: párrafo «Filtros por usuario (F-064)» |
| T8 | 8699741 | Límite comprobado con `git diff --stat dev` |

Ficheros tocados (`services/partes-front/` salvo el doc): `interface_adapters/web/identidad.py`,
`interface_adapters/web/app.py`, `templates/base.html`, `templates/{partes,obras,trabajadores}_list.html`,
`static/app.js`, `tests/test_f064_clave_usuario.py`, `tests/test_f064_filtros_js.py`,
`tests/test_f043_portal_fecha.py` (desviación 1), `docs/ARCHITECTURE.md`, más `specs/` y `progress/`.

## Decisiones de diseño

- **API de `FiltrosSesion`**: `{redirigir, restaurar, puras: {...}}`. Las puras (`claveAlmacen`,
  `rutaNormal`, `estadoVigente`, `fotoVacia`, `filtrosRepuestos`, `conPantalla`, `consultaDeLista`,
  `destinoRestaurar`, `diasRestaurables`) se ejecutan en node extrayendo el IIFE entero.
- **Forma guardada**: la de `design.md` §5. Solo se guardan valores no vacíos; la búsqueda solo
  si no es vacía; `sinExtra` solo si es `false` (R13). Sin pantallas, la clave se **borra** en vez
  de escribir un estado vacío.
- **Columna** = `data-col-key` de la cabecera de la 1.ª fila de `thead` en la misma posición
  (`cellIndex` vivo) o su texto. `wireColumnTools` ya ha puesto `data-col-key` antes de restaurar,
  así que las flechas de ordenación no ensucian la clave.
- **Una sola escritura al restaurar**: bandera `restaurando` (también en `quitarTodo`); el
  `lineas:cambio` y el `change` de `#hide-sin-extra` se enganchan a `guardar` **después**.
- **Hueco de la spec cubierto (decisión)**: la foto **conserva** los días guardados de OTRO periodo
  si ahora no hay ninguno marcado (si no, visitar otro mes los borraría y M1.2 «de vuelta ⇒ días»
  fallaría), y conserva la búsqueda guardada cuando la consulta trae otro parámetro (R19 «ni
  guarda»: p. ej. `?message=` tras borrar no pisa la búsqueda).
- **Barrido (R8)** al principio de `restaurar`, haya o no clave de usuario.
- **Aviso (R17)**: `div.alert.info#filtros-sesion-aviso` como primer hijo de
  `main.page-shell .container`, con «Quitar filtros» (`btn secondary small`). Sin CSS nuevo.
- `quitarTodo`: pulsa el `.filter-clear` de cada tabla o, si no tiene (la matriz), vacía y
  dispara `input`; `dias.limpiar()`; vuelve a marcar la casilla con `change`; borra la entrada.

## Desviaciones (justificadas)

1. **`tests/test_f043_portal_fecha.py::_manejador_principal`** (fuera de la lista de T8). Localizaba
   el `DOMContentLoaded` principal por el texto `{\n    // Toggle del visor de PDF.` pegado; con
   `if (FiltrosSesion.redirigir()) return;` como 1.ª línea (R19, design §4.5) dejaba de
   encontrarlo y `test_f043_r18_r21_r26_al_cargar_restaura_y_pone_en_espera` fallaba. Solo cambia
   el ancla (`rindex` del `addEventListener` que precede al comentario); sus aserciones, intactas.
2. `_node` de `test_f064_filtros_js.py` ejecuta el programa desde un fichero temporal: con
   `node -e`, el programa de DOM (DOM falso + funciones reales) pasa del límite de la línea de
   órdenes de Windows (`WinError 206`).

## Fase RED (trazas reales)

**T1** — `python -m pytest tests/test_f064_clave_usuario.py tests/test_f064_filtros_js.py -q -p no:cacheprovider`
(desde `services/partes-front`, con T1 recién escrita):

```
>       from interface_adapters.web.identidad import clave_filtros
E       ImportError: cannot import name 'clave_filtros' from 'interface_adapters.web.identidad' (C:\Users\pgris\PycharmProjects\partes-wt-f064\services\partes-front\interface_adapters\web\identidad.py)
tests\test_f064_clave_usuario.py:36: ImportError
...
E       AssertionError: el <body> no lleva data-filtros-usuario
E       assert None
...
>       assert m, "app.js no define FiltrosSesion"
E       AssertionError: app.js no define FiltrosSesion
...
E       assert 'href="/partes?search=">Limpiar</a>' in '{% extends "base.html" %}\n{% block content %}\n<div class="page-header">...
E       assert '    var dias = wireDayFilters();\n' in '  document.addEventListener("DOMContentLoaded", function () {\n    // Toggle del visor de PDF.\n ...
FAILED tests/test_f064_clave_usuario.py::test_f064_r1_clave_16_hexadecimales_del_sha256
...
92 failed, 6 passed, 1 warning in 13.23s
```

Los 6 que pasan son a propósito los guardianes de R22/R23 (huellas de `conjuntoAprobacion`,
`restaurarVista`, `vistaRestaurable`, `actualizarVista`, `_ctKey` y la línea de `VISTA_CLAVE`
tomadas de `dev`): deben pasar antes y después.

**T4** — `python -m pytest tests/test_f064_filtros_js.py -q -p no:cacheprovider -k "manejador"`
con el `app.js` de T3 (900ae84) repuesto temporalmente:

```
E         TypeError: Cannot read properties of undefined (reading 'disponibles')
E         TypeError: Cannot read properties of undefined (reading 'seleccionar')
2 failed, 87 deselected in 0.91s
```

**T5** — `python -m pytest tests -q -p no:cacheprovider -k "f022 or day or dias or f043_portal or f049_editor"`
tras T4, antes del DOM (fallaba `test_f064_r12_otro_periodo_no_repone_ni_pierde_los_dias`):

```
E         FiltrosSesion.restaurar(wireDayFilters());
E                       ^
E         TypeError: FiltrosSesion.restaurar is not a function
```

Ya en verde: `python -m pytest tests/test_f064_filtros_js.py tests/test_f064_clave_usuario.py -q`
⇒ `98 passed, 1 warning in 29.08s`.

## Qué se verificó (resultado real)

- `node --check static/app.js`: OK tras T3, T4 y T5.
- Parseo Jinja2 (`Environment().parse`) de `partes_list.html`, `obras_list.html`,
  `trabajadores_list.html` y `base.html`: OK.
- Guardianes de F-017 sin tocarlos: `python -m pytest tests/test_f064_clave_usuario.py
  tests/test_f017_punto_unico.py tests/test_f017_identidad.py -q` ⇒ `204 passed, 1 skipped`
  (`_actor(request)` sigue en 18; la global no lee cabeceras).
- Todos los tests de sv4 que leen `app.js` (19 ficheros) en verde tras la desviación 1.
- `git diff --stat dev`: solo sv4 (`identidad.py`, `app.py`, `app.js`, `base.html`, las tres
  listas, los dos tests nuevos y el ancla de F-043), `docs/ARCHITECTURE.md`, `specs/`,
  `progress/`, `harness/features.json` y `BACKLOG.md`. Ni sv1/sv2/sv3/sv5, ni `infra/`, ni
  `orm_models.py`, ni `azure-apps/`.

Cobertura de requisitos por los tests: R1–R3 (`test_f064_clave_usuario.py`); R5–R19 y R21 en
`test_f064_filtros_js.py` (puras, DOM falso con `wireColumnFilters`/`_setupDaySelection`/
`wireDayFilters` reales y fuente); R20 (plantillas); R22/R23 (huellas). R24 por `git diff`.
R25 la revisa el reviewer.

## `bash harness/init.sh` (final, tras T8)

```
522 passed, 3 skipped in 124.63s (0:02:04)
[OK] pytest en verde (con medición de cobertura)
[OK] servicio sv1-email / sv2-extraccion / sv3-persistencia: pytest en verde (caché)
2984 passed, 1 skipped, 2 warnings in 862.99s (0:14:22)
[OK] servicio sv4-front (services/partes-front): pytest en verde
[OK] servicio sv5-transfer (services/partes-transfer): pytest en verde (caché)
[OK] PUERTA COBERTURA: 100.0% de 7 líneas cambiadas cubiertas (7/7, umbral 80%, nivel estandar)
[OK] PUERTA TAMAÑO: F-064 dentro de los topes (requirements 149/150, design 250/250)
[OK] Rama actual: feature/F-064-filtro-en-sesion
ENTORNO LISTO. Puedes trabajar.
```

Nota: un `init.sh` lanzado como precondición antes de T1 dio un rojo **transitorio** en sv4
(`UndefinedError: 'clave_filtros_de' is undefined`) porque `base.html` se editó en T2 mientras
la suite corría con el `app.py` ya importado. No es un fallo del código: el final está en verde.

## Fuera de alcance / pendiente

- **T9 mutación**: la lanza el líder (`python -m harness.mutacion --feature F-064`); el análisis
  de supervivientes irá en `progress/mutacion_F-064.md`. La mutación solo alcanza Python
  (`clave_filtros` y la global): el JS no es mutable con la herramienta del arnés.
- **T11 / M1** (humano o líder, portal local, `design.md` §8, los seis puntos): lista → detalle →
  volver; Ctrl+F5; otro mes ⇒ sin días y de vuelta ⇒ días; «Quitar filtros»; «Limpiar»;
  pestaña nueva; «Aprobar visibles (n)» sin filas seleccionadas; bajar `t` 8 h ⇒ limpio.
  Mirar también `_irTrasBorrar` (F-061) ⇒ `/partes` vuelve a la búsqueda guardada.
- **T12 / M2** (humano, tras desplegar sv4): dos usuarios de Entra en el mismo navegador.
- Fuera de alcance por spec: servidor/entre ordenadores, mes y modo de los detalles, ordenación,
  selección de líneas, sincronizar pestañas, anchos por usuario, «olvidar mis filtros».
- Efecto aceptado (design §4.2): con la autenticación caída, cada página renderizada deja el
  WARNING de F-017 R5b también desde la global de la plantilla.
- Al redirigir (R19), los demás `DOMContentLoaded` (matriz, poison, jornadas) llegan a correr
  antes de que el navegador cambie de página; no escriben nada.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | sv4: **2984 passed, 1 skipped**; raíz: 522 passed, 3 skipped; F-064: **98** (9 + 89), todos en verde |
| Cobertura de líneas cambiadas | **100.0 %** (7/7 líneas Python; umbral 80 %, estándar) |
| Mutantes generados / supervivientes | **PENDIENTE del líder** por encargo (T9): no la lanza el implementer |
| Tiempo de la suite | sv4 862.99 s; raíz 124.63 s; los 98 de F-064, 29.08 s |

La cobertura de líneas cambiadas solo mide Python: las ≈ 400 líneas de `static/app.js` no entran
en la puerta. Su cobertura es la de los 89 tests de node (puras + DOM falso + fuente).
