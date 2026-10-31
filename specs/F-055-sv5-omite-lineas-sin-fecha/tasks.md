# F-055 · sv5 omite las líneas sin fecha válida — tareas

> Refrescadas sobre `dev` 14b3cd5 (2026-10-31). Antes de T2, el humano resuelve DA1–DA11
> (`design.md` §11; DA8 superada) y el líder hace la **M1** (T1, solo lectura), que puede mover
> las constantes de DA2/DA10. Todo en `services/partes-transfer/` salvo T1 y T9. Cada tarea = un
> commit `F-055 Tn: ...`. Rigor **crítico**: fase RED con traza en `progress/impl_F-055.md`,
> cobertura y mutación completa.

- [x] T1: M1 · solo lectura en la base `partes` y en Sigrid (`design.md` §9) antes de T2  |  Verificación: MANUAL (líder o humano), resultado anotado en `design.md` §9
- [x] T2: Escribir `tests/test_f055_fecha_linea.py` (R1, R2; casos de `design.md` §8, límite hoy + 62) y verlo en ROJO (el módulo no existe)  |  Verificación: `cd services/partes-transfer && python -m pytest tests/test_f055_fecha_linea.py` falla por `ImportError` (traza RED en impl)
- [x] T3: Crear `application/services/fecha_linea.py` (`MOTIVO_FECHA_NO_VALIDA`, `FECHA_MINIMA`, `DIAS_FUTURO` = 62, `motivo_fecha_no_valida`; `design.md` §4.1)  |  Verificación: `python -m pytest tests/test_f055_fecha_linea.py` en verde
- [x] T4: Escribir `tests/test_f055_pipeline_fecha.py` (R3–R7, R10, R11, R15; incluye racha/hermano con `MOVER_CIZ` y franquicia con los helpers de `test_f056_pipeline.py`) y `tests/test_f055_canales.py` (R8, R9) y verlos en ROJO  |  Verificación: `python -m pytest tests/test_f055_pipeline_fecha.py tests/test_f055_canales.py` falla por la guarda ausente (hoy da de alta `PT0/00001`; traza RED en impl)
- [x] T5: `domain/models/registro_models.py`: `LineaEntrada.fecha_int: Optional[int] = None` y `ano`/`mes` con `or 0`; `interface_adapters/api/app.py`: `LineaIn.fecha_int: Optional[int] = None` (R9, DA4 B); `FranquiciaIn` no se toca  |  Verificación: `python -m pytest tests/test_f055_canales.py -k r9_ano_mes` en verde y la suite de sv5 sin regresiones
- [x] T6: `application/pipelines/registro_pipeline.py`: `_hoy()`, paso 2a en `preparar` (`por_fecha` antes de 2b; `con_recurso`, `sin_recurso` y `horas_de_recursos` solo con las válidas; `{**omisiones, **por_fecha}` a `ReglasRegistro`), WARNING de R11 y el paso 2a en el docstring de cabecera (`design.md` §4.2)  |  Verificación: `python -m pytest tests/test_f055_pipeline_fecha.py tests/test_f055_canales.py` en verde
- [x] T7: Suite completa de sv5 sin tocar ningún test existente (R12, también `test_f056_*`, `test_f060_*`, `test_f062_*`) y nada fuera de sv5 salvo la documentación (R13)  |  Verificación: `cd services/partes-transfer && python -m pytest` en verde; `git diff dev --stat -- services/partes-front services/partes-persistencia services/partes-email services/partes-api infra` vacío
- [x] T8: `docs/ARCHITECTURE.md` semántica 6 con el texto de `design.md` §10 (R14)  |  Verificación: revisión del reviewer; `python -m harness.tamano --feature F-055` en verde
- [x] T9: `C:\Users\pgris\PycharmProjects\azure-apps\partes.md`: punto 6 de sv5 (motivo `fecha_no_valida`, `fecha_int` admite `null`, franquicia `no_editable` por fecha) y nota informativa a `porcentajes` (DA7), commit local en ese repositorio sin push  |  Verificación: revisión del reviewer (`git -C ..\azure-apps log -1`)
- [ ] T10: Campaña de mutación completa (rigor `critico`) sobre `fecha_linea.py` y las líneas cambiadas de `registro_pipeline.py`, `registro_models.py` y `app.py`; supervivientes analizados en `progress/impl_F-055.md`  |  Verificación: `python -m harness.mutacion` con el nivel de `harness/rigor.json`, sin supervivientes sin justificar
- [ ] T11: M2 (y M2b si la franquicia está configurada) · sv5 local en modo pruebas (obra 0404), preflight y, solo si las tres salen `omitir`, ejecutar sin escritura efectiva (`design.md` §9)  |  Verificación: MANUAL (humano o líder con su autorización), resultado anotado en `progress/impl_F-055.md`
- [ ] T12: M3 · tras `redeploy_partes.ps1 -Solo sv5` (lo pide el humano) y unos días de uso, M1 otra vez  |  Verificación: MANUAL (humano o líder), `design.md` §9
- [x] T13: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida «ENTORNO LISTO»
