# F-051 · Extracción fila a fila — tareas

> Antes de T1, el humano resuelve DA1–DA3 (`design.md` §7). Las tareas marcadas
> «(DA1 = A)» o «(DA2 ≠ A)» se saltan, anotándolo en `progress/impl_F-051.md`, si
> la decisión es otra. Cada tarea = un commit `F-051 Tn: ...`.

- [x] T1: (DA1 = A) Escribir `services/partes-api/tests/test_f051_esquema.py` (R9–R12) y verlo en ROJO  |  Verificación: `cd services/partes-api && python -m pytest tests/test_f051_esquema.py` falla por el campo ausente (traza RED en impl)
- [x] T2: (DA1 = A) Añadir `numero_linea_horas` a `EmpleadoParte` en `services/partes-api/domain/models/parte_models.py` tras `numero_linea`  |  Verificación: `python -m pytest tests/test_f051_esquema.py tests/test_f023_empresa_membrete.py` en verde
- [x] T3: Escribir `services/partes-api/tests/test_f051_prompt.py` (R1–R7, palabras clave de `design.md` §6) y verlo en ROJO  |  Verificación: `cd services/partes-api && python -m pytest tests/test_f051_prompt.py` falla (traza RED en impl)
- [x] T4: Reforzar `services/partes-api/config/prompts.yaml` según `design.md` §5 (regla en `system`, bloque «LECTURA FILA A FILA», viñeta `numero_linea_horas` si DA1 = A, `dni` y `numero_linea_horas` en `schema_hint`)  |  Verificación: `python -m pytest` de sv2 en verde y `git diff dev -- services/partes-api/config/prompts.yaml` solo toca `system`, punto 3 y `schema_hint` (R8)
- [x] T5: (DA2 ≠ A) Escribir `services/partes-persistencia/tests/test_f051_lectura_dudosa.py` (R13–R17, casos de `design.md` §6) y verlo en ROJO  |  Verificación: `cd services/partes-persistencia && python -m pytest tests/test_f051_lectura_dudosa.py` falla (traza RED en impl)
- [x] T6: (DA2 ≠ A) Crear `MotivoLectura` y `ParteDocumento.lectura_dudosa` en `domain/models/parte_records.py` y el detector `application/services/lectura_dudosa.py` de sv3  |  Verificación: tests del detector de T5 en verde
- [x] T7: (DA2 ≠ A) Cablear el detector en `ParteNormalizer` (con su WARNING) y la condición en `_compute_review_required`; con DA2 = C, además `REVISAR_TABLA_DISPERSA` en `config/settings.py` y su paso en `interface_adapters/api/app.py`  |  Verificación: `cd services/partes-persistencia && python -m pytest` en verde, `test_f003_r26_review_required.py` y `test_f048_*` sin cambios
- [ ] T8: Documentar en `docs/ARCHITECTURE.md` la lectura fila a fila de sv2 y (DA2 ≠ A) la condición nueva de `review_required` con su interruptor  |  Verificación: revisión del reviewer; `python -m harness.tamano --feature F-051` en verde
- [ ] T9: Campaña de mutación muestreada (rigor `estandar`) sobre `parte_models.py` y `lectura_dudosa.py`; analizar supervivientes en `progress/impl_F-051.md`  |  Verificación: `python -m harness.mutacion` con el nivel de `harness/rigor.json`, supervivientes documentados
- [ ] T10: M1 · PDF real de la 0686 troceado en 3 páginas contra el modelo de producción, según la DA3 (por defecto 3 de 3 por página); tabla de resultados sin nombres ni DNIs  |  Verificación: MANUAL (humano o líder), comandos de `design.md` §9; si no se alcanza, `blocked` (DA3)
- [ ] T11: M2 · ≥ 5 partes laborables bien leídos hoy, mismas horas por fila que lo aprobado en el portal  |  Verificación: MANUAL (humano o líder), `design.md` §9
- [ ] T12: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida «ENTORNO LISTO»
