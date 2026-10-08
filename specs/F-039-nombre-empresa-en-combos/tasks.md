<!-- specs/F-039-nombre-empresa-en-combos/tasks.md -->
# F-039 · Portal: nombre de la empresa en combos y Conciliar — Tareas

Rama **`feature/F-039-nombre-empresa-en-combos`**. Un commit local por tarea (`F-039 Tn: …`), por rutas explícitas; sin push ni PR. Rigor **estándar**: fase RED con traza en `progress/impl_F-039.md`, cobertura y mutación muestreada. Todo en `services/partes-front/`.

- [ ] T1: Tests R1–R5, R11 y R12 (RED los que cambian, design §4); añadir `nombre_empresa_o_vacio` a `application/services/empresas.py` y `empresa_nombre` en los cuatro endpoints y en `_candidato_con_empresa` de `interface_adapters/web/app.py`  |  Verificación: `python -m pytest tests/test_f039_nombre_empresa.py -q`
- [ ] T2: Tests R6–R10 (node y texto; RED los que cambian); reescribir `empresaSufijo` en `static/app.js`  |  Verificación: `node --check static/app.js` y `python -m pytest tests -q`
- [ ] T3: Informe `progress/impl_F-039.md` (≤ 220 líneas) con fase RED, cobertura y mutación muestreada con supervivientes analizados  |  Verificación: `python -m harness.mutacion --feature F-039` y `python -m harness.tamano --feature F-039`
- [ ] T4: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
- [ ] M1: En el portal desplegado (Ctrl+F5), Conciliar → búsqueda manual muestra «· Ruesma»/«· Porsan»  |  Verificación: MANUAL (humano)
