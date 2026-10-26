<!-- specs/F-064-filtro-en-sesion/tasks.md -->
# F-064 · El filtro del portal se mantiene durante la sesión de cada usuario — tareas

> Antes de T1, el humano confirma DA1–DA7 (`design.md` §9; las tareas suponen la A en todas) y
> el líder hace M0. Cada tarea es un commit `F-064 Tn: ...` con rutas explícitas. Las rutas sin
> prefijo son de `services/partes-front/`. Los tests se lanzan desde `services/partes-front` con
> `python -m pytest`.

- [x] T0: M0 · caducidad de la cookie de Easy Auth de `ca-sv4-front` (design.md §8)  |  Verificación: MANUAL (líder, solo lectura); valor anotado en `progress/current.md`; si no es 8 h, `SESION_MS` toma ese valor
- [x] T1: Escribir `tests/test_f064_clave_usuario.py` y `tests/test_f064_filtros_js.py` (design.md §6) y verlos en ROJO  |  Verificación: `python -m pytest tests/test_f064_clave_usuario.py tests/test_f064_filtros_js.py` falla por `clave_filtros` y `FiltrosSesion` ausentes (traza RED en `progress/impl_F-064.md`)
- [x] T2: `clave_filtros` en `interface_adapters/web/identidad.py`, el global `clave_filtros_de` en `interface_adapters/web/app.py` y `data-filtros-usuario` en `templates/base.html` (§4.1, §4.2)  |  Verificación: tests de R1–R3 en verde; `python -m pytest tests/test_f017_punto_unico.py tests/test_f017_identidad.py` en verde sin tocarlos
- [x] T3: El IIFE `FiltrosSesion` en `static/app.js` tras `avisarCambioLineas`, con constantes y puras (§4.3)  |  Verificación: tests de node de R5–R10, R12, R14, R16, R17 y R19 en verde; `node --check static/app.js`
- [x] T4: `_setupDaySelection` y `wireDayFilters` devuelven el manejador de días (§4.4)  |  Verificación: tests de R12 y R16 del DOM falso en verde; el clic y «Quitar filtro» siguen cubiertos por los tests existentes de sv4 en verde
- [x] T5: El cableado de `FiltrosSesion` (DOM: foto, guardar, restaurar, aviso, quitarTodo, redirigir y barrido) y sus dos líneas en el `DOMContentLoaded` principal (§4.3, §4.5)  |  Verificación: tests de R11, R15, R18, R19, R21–R23 en verde; `node --check static/app.js`
- [x] T6: «Limpiar» con `?search=` en `templates/partes_list.html`, `obras_list.html` y `trabajadores_list.html` (R20)  |  Verificación: test de R20 en verde; parseo Jinja2 de las tres plantillas y de `base.html`
- [x] T7: `docs/ARCHITECTURE.md`, punto 11: clave de filtros, guardado por usuario y pantalla, caducidad de 8 h y selección nunca guardada (R25)  |  Verificación: revisión del reviewer; `git diff dev -- docs/ARCHITECTURE.md` solo toca ese punto
- [x] T8: Comprobar el límite (R24)  |  Verificación: `git diff --stat dev` lista solo `services/partes-front/{interface_adapters/web/identidad.py,interface_adapters/web/app.py,static/app.js,templates/base.html,templates/partes_list.html,templates/obras_list.html,templates/trabajadores_list.html,tests/test_f064_clave_usuario.py,tests/test_f064_filtros_js.py}`, `docs/ARCHITECTURE.md`, `specs/`, `progress/`, `harness/features.json` y `BACKLOG.md`
- [x] T9: Campaña de mutación muestreada (rigor `estandar`) y análisis de supervivientes en `progress/impl_F-064.md`  |  Verificación: `python -m harness.mutacion --feature F-064` con el nivel de `harness/rigor.json`, supervivientes documentados
- [x] T10: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida «ENTORNO LISTO»
- [ ] T11: M1 · recorrido del portal en local (design.md §8)  |  Verificación: MANUAL (humano o líder); los seis puntos anotados en `progress/impl_F-064.md`; no se aprueba nada fuera de la obra 0404
- [ ] T12: Tras el APPROVED y la fusión, despliegue de sv4 y M2 con dos usuarios de Entra  |  Verificación: MANUAL (humano: pide el despliegue; ningún agente lanza `redeploy_partes.ps1`); resultado en `progress/current.md`
