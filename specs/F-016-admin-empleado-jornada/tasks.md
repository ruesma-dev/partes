<!-- specs/F-016-admin-empleado-jornada/tasks.md -->
# F-016 · Pantalla de administración de `empleado_jornada` (sv4) — Tareas

Rama: **`feature/F-016-admin-empleado-jornada`** (ya creada desde `dev`; no se
crea otra). Un commit **local** por tarea, mensaje `F-016 Tn: …`, por rutas
explícitas (nunca `git add -A`). Sin `git push` y sin PR: eso lo hace el
humano.

> **Actualizado el 2026-08-19** con las decisiones del humano: acceso abierto
> a cualquier autenticado con interruptor (duda 1), identidad por helper con
> F-017 aparte (duda 2), **selector de trabajador** en vez de teclear el DNI
> (duda 3, afecta a T5 y T7) y «Reactivar» confirmado (duda 5). Ver
> `design.md` §13 y §14.

Rigor **`estandar`** ⇒ fase **RED** con traza real en `progress/impl_F-016.md`
para **R7, R12, R14 y R15**; **cobertura** de las líneas cambiadas ≥ umbral;
**campaña de mutación** con los supervivientes analizados.

Reglas que no se negocian durante la ejecución:

- **Ningún test toca red ni BBDD**: `FabricaSesionSqlite` (SQLite en memoria
  con el ORM real), dobles y `Settings(_env_file=None)`.
- **Ningún cambio de schema.** Si en algún momento parece que hace falta una
  columna nueva en `empleado_jornada`, es que el diseño se torció: **parar y
  consultar** (R1).
- **Ningún fichero de sv3 (ni de sv1, sv2, sv5, `infra/`).** Si parece
  necesario, `blocked` y se consulta (`design.md` §1 y DA7).
- **Ningún test existente se modifica.** Si uno se pone rojo, se rompió algo
  que ya funcionaba: parar y avisar, no adaptar el test.
- **Ni un DNI ni un nombre de persona real** en el código, los tests, la spec
  o los informes.
- **Ninguna ruta `/api/sigrid/*` nueva ni modificada**, y **`_comboSimple` no
  se toca**: el selector de R20 los reutiliza tal cual (`design.md` §5.6). Si
  parece que hay que cambiarlos, parar y consultar.
- **La identidad no se implementa aquí.** `_actor(request)` devuelve
  `settings.default_reviewer` y punto; leer Easy Auth es **F-017**
  (`design.md` §14). Si F-017 ya está mergeada al empezar, se **usa** su
  helper en vez de escribir otro.
- Si la spec resulta ambigua o una herramienta falla de forma inesperada:
  `blocked`, motivo en `progress/current.md`, parar. Nada de workarounds.

> **PUERTA DE ENTRADA (T0).** Ninguna tarea de código empieza antes de que
> **F-015 esté mergeada en `dev`**: la tabla, `EmpleadoJornadaOrm`,
> `list_jornadas_empleado()` y `JornadaEmpleadoProvider` los crea ella. Ver
> `design.md` §11.1.

---

- [x] **T0**: Comprobar la puerta de entrada. `git log --oneline dev | head`
      muestra el merge de F-015; existen `EmpleadoJornadaOrm` en
      `services/partes-front/infrastructure/database/orm_models.py`,
      `list_jornadas_empleado` en
      `services/partes-front/infrastructure/database/parte_repository.py` y
      `JornadaEmpleadoProvider` en
      `services/partes-front/application/services/jornada_provider.py`.
      Anotar en `progress/impl_F-016.md` las **firmas reales** encontradas y
      cualquier diferencia con lo que supone `design.md` §4 y §5.
      | Verificación: `bash harness/init.sh` en verde sobre la rama, con la
      rama al día respecto de `dev`; sección «Puerta de entrada» del informe
      con las firmas pegadas. **Si falta cualquiera de las tres, PARAR**
      (`blocked`); si difiere la semántica (`hasta` exclusivo, `is_active`,
      `origen`), PARAR también.

- [x] **T1**: Validación pura —
      `services/partes-front/application/services/jornada_admin.py`
      (`design.md` §5.1): `JornadaInvalida`, `EntradaJornada`,
      `a_hasta_exclusivo`, `a_ultimo_dia_incluido`, `normalizar_entrada`,
      `validar_entrada`, `buscar_solape`. Sin BBDD, sin FastAPI, sin logging.
      Tests **primero** (fase RED por `ImportError`) en
      `services/partes-front/tests/test_f016_validacion_jornada_admin.py`:
      `test_f016_r7_hasta_exclusivo`, `test_f016_r8_semanal_o_patron`,
      `test_f016_r9_horas_patron`, `test_f016_r10_semanal_rango`,
      `test_f016_r11_fechas`, `test_f016_r12_solape` (la tabla entera de
      `design.md` §8.1), `test_f016_r18_dni_normalizado`.
      | Verificación:
      `python -m pytest services/partes-front/tests/test_f016_validacion_jornada_admin.py -q`
      en verde; trazas de la fase RED de **R7 y R12** pegadas en
      `progress/impl_F-016.md`.

- [x] **T2**: Repositorio — cinco métodos nuevos en `ParteReviewRepository`
      (`services/partes-front/infrastructure/database/parte_repository.py`,
      `design.md` §5.2): `list_jornadas_admin`, `crear_jornada`,
      `actualizar_jornada`, `cerrar_jornada`, `set_jornada_activa`.
      **`list_jornadas_empleado()` de F-015 no se toca.** Ningún `DELETE`.
      Añadir `sembrar_jornadas(fabrica, filas)` a
      `services/partes-front/tests/dobles.py` y los tests de repositorio
      dentro de `test_f016_endpoints_admin_jornadas.py` (o un módulo propio
      si crece): orden del listado, sellado de auditoría, `origen` forzado a
      `manual`, `False` cuando el id no existe.
      | Verificación: `python -m pytest services/partes-front/tests -q -k f016`
      en verde; `grep -n "DELETE\|session.delete" ` sobre los métodos nuevos
      sin resultados.

- [x] **T3**: Configuración y puerta de acceso —
      `jornadas_admin_enabled: bool = Field(True, alias="JORNADAS_ADMIN_ENABLED")`
      en `services/partes-front/config/settings.py`; `_exigir_admin_jornadas()`
      y `_actor(request)` en
      `services/partes-front/interface_adapters/web/app.py` (`design.md`
      §5.3); `JORNADAS_ADMIN_ENABLED=true` con su comentario en
      `services/partes-front/.env.example`. `_actor` devuelve
      `settings.default_reviewer` **sin leer cabeceras** (eso es F-017,
      `design.md` §14): un solo punto, con el docstring que dice quién lo
      relevará. Tests **primero** (fase RED) en
      `services/partes-front/tests/test_f016_vista_admin_jornadas.py`:
      `test_f016_r15_puerta_de_acceso` (404 en las seis rutas con la variable
      a falso; 200 con ella a verdadero) y la parte de `_actor` de
      `test_f016_r13_auditoria`, que **inyecta o parchea el helper** en vez
      de fabricar cabeceras, para que siga en verde cuando llegue F-017.
      | Verificación: `python -m pytest services/partes-front/tests -q -k f016`
      en verde; traza de la fase RED de **R15** en el informe; el `.env` real
      **no** se toca (`git status` limpio para `services/partes-front/.env`).

- [x] **T4**: Endpoints JSON —
      `POST /api/admin/jornadas`, `PATCH /api/admin/jornadas/{jornada_id}`,
      `POST /api/admin/jornadas/{jornada_id}/cerrar`, `…/desactivar` y
      `…/reactivar` en `interface_adapters/web/app.py` (`design.md` §5.3),
      con la traducción `JornadaInvalida` → 422 y solape → 409, y el aviso de
      DNI desconocido (R19). Tests en
      `services/partes-front/tests/test_f016_endpoints_admin_jornadas.py`:
      `test_f016_r3_crear`, `test_f016_r4_editar`, `test_f016_r5_cerrar`,
      `test_f016_r6_papelera_logica`, `test_f016_r12_solape` (409 por HTTP,
      con `conflicto` en el cuerpo y **la BBDD intacta**),
      `test_f016_r13_auditoria`, `test_f016_r16_no_encontrada`,
      `test_f016_r19_dni_desconocido_avisa`.
      | Verificación: `python -m pytest services/partes-front/tests -q -k f016`
      en verde; en cada caso de rechazo, el test comprueba el `count(*)` de
      la tabla antes y después.

- [x] **T5**: Página y plantilla — `GET /admin/jornadas` (con `?editar=<id>`)
      en `app.py` y `services/partes-front/templates/admin_jornadas.html`
      (`design.md` §2), extendiendo `base.html` y reutilizando las clases CSS
      existentes; enlace `Jornadas` en `<nav class="topnav">` de
      `services/partes-front/templates/base.html` bajo
      `{% if jornadas_admin_enabled %}`, con el global registrado junto a
      `asset_version`. **Incluye el bloque de trabajador de `design.md`
      §5.6**: marcado `combo-simple` / `combo-panel` copiado de
      `nuevo_parte.html` (ids `jor-emp-combo` / `jor-emp-input` /
      `jor-emp-panel` y el oculto `jor-dni`), checkbox «El trabajador no está
      en la lista» con su campo de texto, y `"sigrid_enabled":
      settings.sigrid_lookup_enabled` en el contexto de la vista. En modo
      edición, bloque **deshabilitado** con el DNI de la fila (R4).
      Tests: `test_f016_r1_schema_intacto`, `test_f016_r2_listado`,
      `test_f016_r17_sin_red`, `test_f016_r20_selector_trabajador`.
      | Verificación: `python -m pytest services/partes-front/tests -q -k f016`
      en verde; el test de listado comprueba el orden, el estado vacío, el
      «sin fin» y el último día incluido pintado (no el valor exclusivo); el
      de R20 comprueba el marcado, que apunta a `/api/sigrid/empleados`, la
      degradación con `sigrid_lookup_enabled` falso y el bloque deshabilitado
      en `?editar=<id>`; además,
      `git diff dev -- services/partes-front/interface_adapters/web/app.py`
      **no** muestra ninguna ruta `/api/sigrid/*` añadida ni cambiada.

- [x] **T6**: Aviso de caché e invalidación — `invalidar()` en
      `services/partes-front/application/services/jornada_provider.py`;
      llamada tras cada escritura con éxito (y **solo** con éxito); aviso
      permanente en `admin_jornadas.html` con los minutos derivados de
      `settings.jornada_cache_ttl_s`. Test **primero** (fase RED):
      `test_f016_r14_cache_y_aviso` con un doble de proveedor que cuenta las
      llamadas.
      | Verificación: `python -m pytest services/partes-front/tests -q -k f016`
      en verde; traza de la fase RED de **R14** en el informe; con TTL 900 en
      settings el HTML dice «15 minutos» (número derivado, no cableado).

- [x] **T7**: JS de la pantalla — bloque nuevo **dentro del IIFE grande** de
      `services/partes-front/static/app.js` (el que define `_comboSimple`;
      hoy abre sobre la línea 40 y cierra sobre la 2228), **justo antes de su
      cierre** (`design.md` §5.4 y DA11), con `MotivoHttp.lanzarSiFalla`,
      delegación por `data-*` y `confirm()` en desactivar/reactivar. Incluye
      **una** llamada a `_comboSimple` para el selector (`design.md` §5.6,
      con el `render` que pone el **DNI delante** del nombre) y el
      mostrar/ocultar del DNI manual. **`_comboSimple` no se modifica** y no
      se duplica. Sin frameworks, sin build. Tocar `static/styles.css`
      **solo** si alguna clase falta de verdad — el combo ya tiene la suya.
      | Verificación: `node --check services/partes-front/static/app.js` sin
      salida; `python -m pytest services/partes-front/tests -q` en verde;
      `git diff dev -- services/partes-front/static/app.js` muestra **solo
      líneas añadidas** en el tramo del bloque nuevo (ninguna modificada
      dentro de `_comboSimple` ni de los combos existentes).

- [x] **T8**: Documentación — la pantalla y el criterio «último día incluido»
      en `docs/referencia/partes-proyecto.md` (sección de `empleado_jornada`
      que abrió F-015); rutas nuevas de sv4 y la variable
      `JORNADAS_ADMIN_ENABLED` en
      `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (**commit local
      en ese repositorio, sin push**: no tiene remoto). Sin secretos, sin
      DNIs, sin nombres de persona.
      | Verificación: `git diff --stat` de los dos repositorios; barrido de
      sensibles sobre lo añadido (`grep -niE "dni|[0-9]{8}[A-Za-z]|password|
      key|token"`), con el resultado pegado en el informe.

- [ ] **T9**: Campaña de mutación y evidencias —
      `python -m harness.mutacion --feature F-016`; analizar **cada**
      superviviente en `progress/mutacion_F-016.md` (ninguno en `PENDIENTE`)
      y completar la sección «Evidencias» de `progress/impl_F-016.md` con los
      cuatro números: tests ejecutados y resultado, cobertura de las líneas
      cambiadas, mutantes generados y supervivientes, y tiempo de la suite.
      Listar en `progress/current.md` las verificaciones **MANUAL (humano)**
      de `design.md` §8.2 con su comando exacto.
      | Verificación: existe `progress/mutacion_F-016.md` con totales reales
      y sin secciones pendientes.

- [ ] **T10**: Ejecutar `bash harness/init.sh` en verde (comando limpio, sin
      pipes ni decoración) y dejar `tasks.md` con todas las tareas marcadas.
      | Verificación: `bash harness/init.sh` termina con exit code 0,
      incluida la puerta de cobertura de las líneas cambiadas.

---

## Verificaciones MANUAL (humano) — no se pueden hacer sin BBDD ni navegador

Detalle y comandos en `design.md` §8.2. Resumen:

1. `/admin/jornadas` en local: crear una excepción y comprobar en la base
   `origen='manual'`, `is_active=true`, `created_by` y `hasta` **un día
   después** del último día incluido que se escribió.
2. Intentar una vigencia que solape: aviso en pantalla nombrando la fila en
   conflicto y `count(*)` idéntico antes y después.
3. Efecto en caliente: el portal refleja el cambio enseguida; sv3 tarda hasta
   `JORNADA_CACHE_TTL_S`.
4. `Ctrl+F5` tras desplegar estáticos.
5. Identidad: **mientras F-017 no esté**, lo esperado en `created_by` es
   `DEFAULT_REVIEWER` (correcto, no un fallo). Con F-017 desplegada, en Azure
   debe verse el principal real de Easy Auth; en local esa cabecera no
   existe.
6. **Selector de trabajador (R20)**, lo único que ningún test cubre: buscar
   por nombre y por DNI, elegir y comprobar el DNI guardado; marcar «no está
   en la lista», dar de alta un DNI desconocido y ver el aviso de R19 sin que
   se bloquee; repetirlo con Sigrid apagado (combo deshabilitado, camino
   manual entero).
