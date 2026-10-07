<!-- specs/F-033-columna-empresa/tasks.md -->
# F-033 · Portal: columna Empresa en las vistas de obra — Tareas

Rama: **`feature/F-033-columna-empresa`** (ya creada). Un commit **local** por tarea, `F-033 Tn: …`, por rutas explícitas (nunca `git add -A`). Sin push ni PR.
Rigor **`estandar`**: fase RED con traza en `progress/impl_F-033.md` para **R2, R4, R5, R7, R8, R9, R12, R13, R15, R17 y R18**; cobertura de líneas cambiadas ≥ umbral; mutación muestreada con los supervivientes analizados.
No empezar sin **DA1–DA7 aprobadas** (`design.md` §10). Si cambia DA2, reescribir R8–R9 antes; si cambia DA3, R17–R18. Ningún test toca red, Sigrid ni PostgreSQL. Todo en `services/partes-front/` salvo el doc.

- [ ] T1: Tests R1–R5 en RED; crear `config/empresas.yaml` y `application/services/empresas.py` (`NombresEmpresa`, `parsear_nombres_empresa`, `empresas_de_grupo`)  |  Verificación: `python -m pytest tests/test_f033_nombres_empresa.py -q`
- [ ] T2: `settings.empresas_path` y `construir_nombres_empresa` en `app.py`, cargada en `build_app` tras la tabla de incidencias, en `app.state` y como filtro Jinja `empresa`; tests de arranque R2 (ruta inexistente, YAML roto, mapa vacío, clave no numérica, nombre vacío)  |  Verificación: `python -m pytest tests/test_f033_nombres_empresa.py -q`
- [ ] T3: Tests de repositorio R7–R12 y R20 en RED; campos `ObraRow.empresas`, `ObraDetail.empresas` (en los dos `return`), `ParteRow.empresa`, `ParteDetail.empresa` y parámetro `empresa_de_ficha` en `list_obras`, `get_obra`, `list_partes`, `get_parte`, con el orden de R12  |  Verificación: `python -m pytest tests/test_f033_vistas_empresa.py -q`
- [ ] T4: `_empresa_de_ficha` en `build_app` sobre `obra_catalog` y pasado a las cuatro rutas; tests con `SigridLookupClient` falso (gemelas 501/502) y con `fetch_obras` que lanza (R19)  |  Verificación: `python -m pytest tests/test_f033_vistas_empresa.py -q`
- [ ] T5: Plantillas `obras_list.html` y `obra_detail.html` (columna, filtro, cabecera, `data-label`); tests HTML R6, R7, R10, R13–R16 y parseo Jinja2  |  Verificación: `python -m pytest tests/test_f033_vistas_empresa.py -q`
- [ ] T6: Plantillas `partes_list.html` y `parte_detail.html`; tests HTML R17–R18 y parseo Jinja2  |  Verificación: `python -m pytest tests/test_f033_vistas_empresa.py -q`
- [ ] T7: No regresión R20: suite completa de sv4 sin tocar tests ajenos y `git diff --stat` sin `app.js`, `styles.css`, `orm_models.py` ni ficheros de otros servicios  |  Verificación: `python -m pytest tests -q` y `git diff --stat dev...HEAD`
- [ ] T8: Doc: una frase al final de la semántica 12 de `docs/ARCHITECTURE.md` (R21)  |  Verificación: lectura del reviewer
- [ ] T9: Informe `progress/impl_F-033.md` (≤ 220 líneas) con fase RED, cobertura y mutación muestreada con los supervivientes analizados  |  Verificación: `python -m harness.mutacion --feature F-033` y `python -m harness.tamano --feature F-033`
- [ ] T10: MANUAL (humano) M1 de `design.md` §8 tras el despliegue de sv4 (lo pide el humano) y Ctrl+F5; solo lectura  |  Verificación: MANUAL (humano)
- [ ] T11: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
