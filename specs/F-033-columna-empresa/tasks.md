<!-- specs/F-033-columna-empresa/tasks.md -->
# F-033 · Portal: columna Empresa en el listado de obras — Tareas

Rama **`feature/F-033-columna-empresa`**. Un commit local por tarea (`F-033 Tn: …`), por rutas explícitas; sin push ni PR. Rigor **estándar**: fase RED con traza en `progress/impl_F-033.md` para R2–R7, cobertura y mutación muestreada. Todo en `services/partes-front/`.

- [x] T1: Tests R2, R4–R7 en RED; crear `application/services/empresas.py` y el cálculo y orden en `list_obras` con los campos nuevos de `ObraRow`  |  Verificación: `python -m pytest tests/test_f033_columna_empresa.py -q`
- [x] T2: Columna, filtro y celda en `templates/obras_list.html`; tests HTML R1, R3 y R8 y parseo Jinja2  |  Verificación: `python -m pytest tests -q`
- [x] T3: Informe `progress/impl_F-033.md` (≤ 220 líneas) con fase RED, cobertura y mutación muestreada con supervivientes analizados  |  Verificación: `python -m harness.mutacion --feature F-033` y `python -m harness.tamano --feature F-033`
- [x] T4: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
