<!-- specs/F-038-limite-filas-sigrid/tasks.md -->
# F-038 · Límite de filas de las lecturas de Sigrid — tareas

> Antes de T1, el humano resuelve DA1–DA7 (`design.md` §7). Con otra respuesta que
> la recomendada (A), se ajustan las tareas afectadas y se anota en
> `progress/impl_F-038.md`. Recomendado empezar tras mezclar F-060 en `dev` y
> rebasar esta rama (`design.md` §8). Cada tarea = un commit `F-038 Tn: ...`.

- [x] T1: Escribir `tests/test_f038_lectores_sigrid.py` (R11–R13 y su prueba de verdad, `design.md` §6) y verlo en ROJO  |  Verificación: `python -m pytest tests/test_f038_lectores_sigrid.py` falla por sv2 sin `truncated`, `prueba_escritura_sigrid.py` y los literales 1.000/10.000 (traza RED en impl)
- [ ] T2: Escribir `services/partes-api/tests/test_f038_sigrid_limite.py` (R1–R3, R5–R8, R14) y verlo en ROJO  |  Verificación: `cd services/partes-api && python -m pytest tests/test_f038_sigrid_limite.py` falla (traza RED)
- [ ] T3: sv2: `SIGRID_API_MAX_ROWS` y rango de `SIGRID_API_TIMEOUT_S` en `config/settings.py`, `MAX_ROWS_DEFECTO`, log y `truncated` en `sigrid_lookup_client.py`, `max_rows` en `app.py` (`design.md` §3)  |  Verificación: `cd services/partes-api && python -m pytest` en verde
- [ ] T4: Escribir `services/partes-persistencia/tests/test_f038_sigrid_limite.py` (R2–R6, R9, R14) en ROJO y cambiar settings (200.000, rangos) y el defecto del cliente de sv3  |  Verificación: `cd services/partes-persistencia && python -m pytest` en verde (traza RED en impl)
- [ ] T5: Escribir `services/partes-front/tests/test_f038_sigrid_limite.py` (R1–R6, R9, R14) en ROJO; cambiar settings, cliente y cableado de sv4 y enmendar `tests/test_f023_catalogo_empresa.py` l.169 (10000 → 200000)  |  Verificación: `cd services/partes-front && python -m pytest` en verde (traza RED en impl)
- [ ] T6: Escribir `services/partes-transfer/tests/test_f038_sigrid_limite.py` (R1–R6, R9, R14, R15) en ROJO; cambiar settings, `__init__`/`_read` de `sigrid_write_client.py`, `app.py`, `main.py`, `comprobar_asiento_analitico.py`; enmendar `tests/test_f024_comprobacion.py` l.274 y l.304 (1000 → 200000)  |  Verificación: `cd services/partes-transfer && python -m pytest` en verde (traza RED en impl)
- [ ] T7: `prueba_escritura_sigrid.py`: `MAX_ROWS = 200_000` y `SystemExit` ante `truncated` (R10); con DA6 = A, borrar `services/partes-front/consulta_reshor_recursos.py` (R16)  |  Verificación: `python -m pytest tests/test_f038_lectores_sigrid.py` en verde
- [ ] T8: Documentar en `docs/ARCHITECTURE.md` («Acceso a datos»; quitar la línea del script con DA6 = A) y en `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` §3.3 y §5.6 (R17), con commit local en ese repositorio  |  Verificación: revisión del reviewer; `python -m harness.tamano --feature F-038` en verde
- [ ] T9: Campaña de mutación muestreada (rigor `estandar`) sobre los cuatro clientes de Sigrid y los cuatro `config/settings.py`; supervivientes analizados en `progress/impl_F-038.md`  |  Verificación: `python -m harness.mutacion` con el nivel de `harness/rigor.json`
- [ ] T10: M0 antes de desplegar y M1 cuando se quiera (`design.md` §9), solo lectura; resultados sin nombres en `progress/impl_F-038.md`  |  Verificación: MANUAL (humano): M0, por app, `az containerapp show -n <app> -g rg-partes-dev --query "properties.template.containers[0].env[?name=='SIGRID_API_TIMEOUT_S' || name=='SIGRID_API_MAX_ROWS'].{n:name,v:value}" -o table` ⇒ ningún timeout > 200; M1 con el comando exacto de `design.md` §9 (a), (b) y (c)
- [ ] T11: M2 tras desplegar sv2–sv5 (`.\infra\redeploy_partes.ps1`, lo lanza el humano)  |  Verificación: MANUAL (humano): `az containerapp logs show -n ca-sv5-transfer -g rg-partes-dev --tail 80` (y `ca-sv4-front`) muestra `max_rows=200000`
- [ ] T12: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida «ENTORNO LISTO»
