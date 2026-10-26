<!-- specs/F-063-consulta-obra-rapida/tasks.md -->
# F-063 · Consulta de existencia de obra que use el índice — tareas

> Antes de T1 el humano confirma DA1–DA5 (`design.md` §10; las tareas suponen la
> recomendación A en todas). Cada tarea = un commit `F-063 Tn: ...` con rutas explícitas. Rutas
> sin prefijo: `services/partes-api/`. Los tests se lanzan desde `services/partes-api` con
> `python -m pytest`.

- [x] T1: Escribir `tests/test_f063_consulta_obra.py` (emulador `_like` y sus tests; R4–R10 y R12 de `design.md` §7) y verlo en ROJO  |  Verificación: `python -m pytest tests/test_f063_consulta_obra.py` falla por `domain.models.clave_obra` y `patron_like` ausentes (traza RED en `progress/impl_F-063.md`)
- [x] T2: Crear `domain/models/clave_obra.py` con `es_vacio` y `clave_obra` movidas tal cual; `application/services/relectura_cabecera.py` y `application/services/obra_sigrid.py` las importan de ahí (§4, §5.1)  |  Verificación: tests de R9 y R12 en verde y `python -m pytest tests/test_f058_relectura_cabecera.py tests/test_f058_obra_sigrid.py` en verde sin tocarlos
- [x] T3: Añadir `_tabla_variantes`, `_clase` y `patron_like` a `infrastructure/sigrid/sigrid_lookup_client.py` (§5.2)  |  Verificación: tests de R4–R7 en verde
- [ ] T4: Sustituir `_SQL_EXISTE_OBRA` (§6) y el cuerpo de `existe_obra` (§5.3), con docstrings del módulo y de la constante al día; ajustar en `tests/test_f058_obra_sigrid.py` solo las aserciones de `test_f058_r7_existe_obra_parametrizada` (§7)  |  Verificación: `python -m pytest` de sv2 en verde (R1–R3, R8, R10, R11) y `python -m pytest tests/test_f038_lectores_sigrid.py` desde la raíz en verde
- [ ] T5: Actualizar `docs/ARCHITECTURE.md` (punto 18: consulta `LIKE` parametrizada sin funciones sobre `con.cod`, candidatos distintos y filtro exacto con la misma clave, F-063)  |  Verificación: revisión del reviewer; `git diff dev -- docs/ARCHITECTURE.md` solo toca esa frase
- [ ] T6: Actualizar `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` §3.2 (`SELECT TOP 1` ⇒ `LIKE` parametrizado + filtro en sv2) y commit local allí con ruta explícita  |  Verificación: `git -C C:\Users\pgris\PycharmProjects\azure-apps log -1 --stat` muestra solo `partes.md`
- [ ] T7: Comprobar el límite (R12): sin cambios fuera de los ficheros de §4  |  Verificación: `git diff --stat dev` lista solo `services/partes-api/{domain/models/clave_obra.py,application/services/relectura_cabecera.py,application/services/obra_sigrid.py,infrastructure/sigrid/sigrid_lookup_client.py,tests/test_f063_consulta_obra.py,tests/test_f058_obra_sigrid.py}`, `docs/ARCHITECTURE.md`, `specs/`, `progress/`, `harness/features.json` y `BACKLOG.md`
- [ ] T8: Campaña de mutación muestreada (rigor `estandar`) y análisis de supervivientes en `progress/impl_F-063.md`  |  Verificación: `python -m harness.mutacion --feature F-063` con el nivel de `harness/rigor.json`, supervivientes documentados
- [ ] T9: M-EQ · equivalencia exhaustiva contra `ruesma` en solo lectura (§9)  |  Verificación: MANUAL (líder); cero filas en todos los lotes, el par trampa vuelve, vieja = nueva en las claves elegidas; agregados en `progress/impl_F-063.md`; si falla, `blocked`
- [ ] T10: M-T · 60 consultas reales con el cliente de la rama (§9)  |  Verificación: MANUAL (líder); 60/60 con la verdad, 0 errores, mediana y máximo dentro de la puerta de DA3; mediana, p95, máximo y candidatos máximos en `progress/impl_F-063.md`; si no pasa, `blocked` y decide el humano
- [ ] T11: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida «ENTORNO LISTO»
- [ ] T12: Tras el APPROVED y la fusión, despliegue de sv2 y M2/M4 de F-058  |  Verificación: MANUAL (humano: pide el despliegue; ningún agente lanza `redeploy_partes.ps1`); M4 con la KQL de F-058 `design.md` §10
