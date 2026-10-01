<!-- specs/F-021-cuenta-analitica-sigrid/tasks.md -->
# F-021 · Cuenta analítica en las líneas de sv5 — Tareas

Rama: **`feature/F-021-cuenta-analitica-sigrid`** (ya creada). Un commit
**local** por tarea, `F-021 Tn: …`, por rutas explícitas (nunca `git add -A`).
Sin push ni PR. Rigor **`critico`**: fase RED con traza en
`progress/impl_F-021.md` para **R1, R2, R4, R5, R6, R8, R11, R12, R14 y R16**;
cobertura de líneas cambiadas ≥ umbral; campaña de mutación **completa** con
**0 supervivientes** sin test o justificación aceptada.

Reglas que no se negocian:

- **No empezar sin DA1–DA13 aprobadas** (`design.md` §8). Si DA3 o DA4
  cambian, se reescriben R3/R5/R8 o R19–R21 antes de seguir.
- **Ningún test toca red ni Sigrid**: dobles de `tests/dobles.py` y
  `httpx.post` sustituido por `monkeypatch`, como en F-023.
- **Ninguna escritura real en Sigrid** durante la implementación; M2–M3 las
  hace el humano tras desplegar, en modo pruebas.

- [ ] T1: Inventario de tests de sv5 que llaman a `stmt_insert_linea`, comparan el SQL de `horas_de_recursos` o construyen `HoraRecurso`/`AccionLinea`, anotado en `progress/impl_F-021.md`  |  Verificación: lista en el informe; sin cambios de código
- [ ] T2: Tests RED de `cuenta_analitica.py` por tablas: `subcuenta` (punto, sin punto, vacío, espacios, varios puntos), R1, R2, R3, R4, R5 (sin subcuenta en el centro y sin centro), R6, R7 (una `HoraRecurso` con otra cuenta no interviene)  |  Verificación: `pytest -q services/partes-transfer/tests/test_f021_cuenta_analitica.py` en rojo por import (traza en el informe)
- [ ] T3: Crear `application/services/cuenta_analitica.py` (design §6.1)  |  Verificación: los tests de T2 en verde
- [ ] T4: `registro_models.py`: `HoraRecurso.caa_cod`/`defecto` y `AccionLinea.caa_ide`/`caa_cod`/`caa_motivo`/`caa_aviso` con sus valores por defecto  |  Verificación: suite de sv5 en verde sin tocar otros tests
- [ ] T5: Tests RED del cliente: SQL y parámetros de `horas_de_recursos` con `caacod`/`defecto` (R9), `cuentas_de_centro` (centro, empresa, subcuentas; `truncated` ⇒ excepción; R10–R11) y `stmt_insert_linea` con `caaide` como parámetro y sin literal 0 (R14)  |  Verificación: `pytest -q services/partes-transfer/tests/test_f021_cliente_cuenta.py` en rojo (traza)
- [ ] T6: `sigrid_write_client.py`: SQL de `horas_de_recursos`, `cuentas_de_centro`, `stmt_insert_linea(caaide=…)` obligatorio y docstring de cabecera (design §5, §7); adaptar los tests de T1  |  Verificación: tests de T5 y suite de sv5 en verde
- [ ] T7: `tests/dobles.py`: `cuentas_de_centro` falso (registro de llamadas, fallo inyectable) y `stmt_insert_linea` que guarda `caaide`  |  Verificación: suite de sv5 en verde
- [ ] T8: Tests RED del pipeline: cuenta en `preparar` solo para `escribir` (R12, R16), una sola lectura por petición y ninguna sin subcuentas (R10), fallo de lectura ⇒ excepción y nada escrito (R11), `caa_*` en `acciones` del preflight (R13), `caaide` en el `INSERT` y `caa_cod` en `escritas` (R14–R15), pisado con cuenta (R17), `ya_registrado` sin reescritura (R16), modo pruebas con el centro de la obra de pruebas, log por motivo sin datos personales (R18), línea sin cuenta escrita con 0 (R8)  |  Verificación: `pytest -q services/partes-transfer/tests/test_f021_pipeline_cuenta.py` en rojo (traza)
- [ ] T9: `registro_pipeline.py`: `_resolver_cuentas` al final de `preparar`, `caaide` y `caa_cod` en `_registrar_bajo_lock`, docstring de pasos (design §6.2)  |  Verificación: tests de T8 y suite de sv5 en verde
- [ ] T10: Test de sv4 `test_f021_preflight_cuenta.py`: `/api/aprobar/preflight` reenvía los `caa_*` de sv5 sin tocarlos (R21) y `static/app.js` define `avisosCuentaHtml`, filtra `accion === "escribir"` con `caa_aviso` y la llama desde `resumenHtml` (R19–R20)  |  Verificación: en rojo antes de T11 (traza)
- [ ] T11: `services/partes-front/static/app.js`: `avisosCuentaHtml(acciones)` y su llamada en `resumenHtml` (design §5)  |  Verificación: `node --check services/partes-front/static/app.js`; tests de T10 en verde; navegador como MANUAL (M3)
- [ ] T12: Comentarios de `services/partes-transfer/prueba_escritura_sigrid.py` (líneas de `caaide`), sin cambio de comportamiento (DA11)  |  Verificación: `git diff` solo en comentarios/docstring; lectura del reviewer
- [ ] T13: `docs/ARCHITECTURE.md` (punto 13, ≤ 8 líneas) y `docs/referencia/partes-proyecto.md` §3.5 (R24)  |  Verificación: lectura del reviewer contra design §1
- [ ] T14: `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` §3.5: cuenta analítica y lectura nueva de `caa` (R24); commit local en ese repositorio, sin push  |  Verificación: `git -C ../azure-apps log -1` muestra el commit
- [ ] T15: Cobertura de líneas cambiadas y campaña de mutación completa sobre `cuenta_analitica.py`, `registro_models.py`, `sigrid_write_client.py`, `registro_pipeline.py` y `app.js` (si la herramienta lo cubre), en `progress/mutacion_F-021.md`  |  Verificación: informe con 0 supervivientes sin test o justificación
- [ ] T16: Ejecutar `bash harness/init.sh` en verde  |  Verificación: salida en verde; M1–M4 (design §9) anotados en `progress/current.md` como MANUAL (humano)
