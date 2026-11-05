# F-066 · Selector de código de hora por prefijo `HE` — Diseño

Base: rama `feature/F-066-selector-hora-por-prefijo-he` desde la punta de F-052 (0d8fc14).
Servicio: **solo sv4**. Requisitos en `requirements.md` (R1–R19); decisiones en §8.

## 1. Inventario: dónde decide sv4 extra/ordinaria (barrido de Python, JS y plantillas)

| # | Sitio (sv4) | Qué hace hoy | F-066 |
|---|---|---|---|
| 1 | `infrastructure/database/parte_repository.py::set_registro_hora` (~3186–3220) | `tipo_hora = "extra" if hora_ext == 1 else "normal"` | **Cambia** (R4–R9): por `es_hora_extra(hora_codigo)`. Es el defecto. |
| 2 | `interface_adapters/web/app.py::set_registro_hora` (`PATCH /api/registros/{id}/hora`, ~3842–3877) | responde `tipo_hora` con `option.ext == 1` | **Cambia** (R10): por la regla. Sigue pasando `hora_ext=option.ext`. |
| 3 | `app.py` `GET /api/sigrid/tipos-hora` (~1795–1808) | expone `ext` | **Cambia** (R13): añade `extra`. |
| 4 | `static/app.js::buildOptions` (~466–469) | agrupa por `t.ext === 1` (las `HE*` salen en «ordinarias») | **Cambia** (R14–R15): agrupa por `t.extra`. |
| 5 | `application/services/sincronizacion.py::es_hora_extra` (~158) | la regla (F-052) | **Se mueve** a `clase_hora.py` y se reimporta (R1–R2, DA1). |
| 6 | `parte_repository.py::_is_extra` (~879), `extras_por_jornada` (~5353), `app.py` (~1019), plantillas `obra_detail.html:241`, `parte_detail.html:159`, `trabajador_detail.html:292` | `tipo_hora == "extra" or hora_ext == 1` (badges, totales, extras por jornada, reparto) | **No se toca** salvo DA5 (R18). Con `tipo_hora` bien puesto el disyuntivo `hora_ext == 1` solo importa si algún código **no** `HE` tiene `ext = 1` (M1). |
| 7 | `infrastructure/sigrid/sigrid_lookup_client.py::fetch_tipos_hora` (~252) | ordena por `(ext, codigo)` | **No se toca**: solo orden; con todo `ext = 0` queda por código, y el JS agrupa por `extra` conservando el orden relativo. |
| 8 | `application/services/tipo_hora_matcher.py` (alta manual «+ Nuevo», celda F-049) | clasifica por la palabra `EXTRA` de la descripción (espejo de sv3) | **No se toca**: ahí `tipo_hora` lo fija el campo que rellena el usuario (ordinarias/extra), no `ext`; `hora_ext=hm.ext` es informativo. |
| 9 | `parte_repository.py::crear_extra_desde` (~1952–1958), `app.py::_hora_extra_celda` (~2332) | `tipo_hora="extra"` y `hora_ext=1` fijo con la hora `HE%` del recurso | **No se toca**: el tipo sale del contexto y el código ya es `HE%`. |
| 10 | `sigrid_lookup_client.py::fetch_dnis_sin_extra` (~437), `fetch_hora_extra_recurso` | SQL `auxhor.cod LIKE 'HE%'` | **No se toca**; lo vigila el guardián si DA8 = B. |
| 11 | `application/services/franquicia.py::extras_pendientes` (~244, F-056) | copia de la regla: `.upper().startswith("HE")` sobre el `hora_codigo` de las acciones de sv5 | **Cambia** (R3): `es_hora_extra(...) is True`. Mismo resultado salvo espacios a la izquierda, que los códigos de Sigrid no traen. |

Fuera de sv4 (no se tocan, LÍMITE DE SERVICIO): sv5 ya usa prefijo (`registro_models.py`
`HoraRecurso.es_extra`, `franquicia.py::_es_extra`); sv3 `recurso_conciliador.py` (~300–315)
elige la extra del recurso por `ext == 1` con respaldo por descripción (DA7); F-006 (pending)
propone justo lo contrario de H-M2-1 (DA7).

## 2. Ficheros a crear

- `services/partes-front/application/services/clase_hora.py` (application, puro, sin E/S):
  `es_hora_extra(codigo: str | None) -> bool | None` (cuerpo actual de F-052, sin cambios) y
  `tipo_hora_de_codigo(codigo: str | None) -> str | None` (`"extra"`/`"normal"`/`None`).
- `services/partes-front/tests/test_f066_clase_hora.py` — R1–R3 (tabla de casos y test de
  fuente: ninguna otra `startswith("HE")` en el Python de sv4 fuera de `clase_hora.py`; las
  cadenas SQL `LIKE 'HE%'` no cuentan).
- `services/partes-front/tests/test_f066_set_registro_hora.py` — R4–R12 (repositorio sobre
  `FabricaSesionSqlite` como `test_f048_traza_portal.py`; endpoint con `TestClient`, catálogo y
  repositorio falsos como `test_f004_endpoints_congelados.py`).
- `services/partes-front/tests/test_f066_selector_js.py` — R13 (endpoint) y R14–R15: se extrae
  `buildOptions` de `app.js` y se ejecuta en node sobre un DOM mínimo (patrón
  `test_f064_filtros_js.py` / `test_f049_editor_js.py`); sin node, `skip` como allí.
- `tests/test_f066_prefijo_he_gemelos.py` (raíz) — R16, solo si DA8 = B (patrón
  `tests/test_f023_de_alta_gemelos.py`: extracción por AST, sin importar).

## 3. Ficheros a modificar

- `application/services/sincronizacion.py`: borra el cuerpo de `es_hora_extra` y lo importa de
  `clase_hora` (`from application.services.clase_hora import es_hora_extra`, re-export
  explícito en `__all__` o comentario `# noqa: F401`). Nada más cambia.
- `infrastructure/database/parte_repository.py::set_registro_hora`: sustituye

  ```python
  if hora_ext is not None and not reg.es_incidencia:
      reg.tipo_hora = "extra" if hora_ext == 1 else "normal"
  ```
  por `tipo = tipo_hora_de_codigo(hora_codigo)`; `if tipo is not None and not
  reg.es_incidencia: reg.tipo_hora = tipo`. Firma, guardas (F-004, F-043), snapshot, deshacer y
  el resto de asignaciones no cambian (R8, R11). Docstring: una línea con la regla y H-M2-1b.
- `interface_adapters/web/app.py`:
  - `set_registro_hora`: `"tipo_hora": tipo_hora_de_codigo(option.codigo) or "normal"` (R10).
  - `GET /api/sigrid/tipos-hora`: cada item gana `"extra": es_hora_extra(t.codigo) is True`.
- `static/app.js::buildOptions`: `t.extra === true` / `t.extra !== true` en vez de `t.ext`;
  comentario de una línea (clase por prefijo, la decide el servidor). Nada más del IIFE cambia.
- `application/services/franquicia.py::extras_pendientes`: la condición del prefijo pasa a
  `es_hora_extra(a.get("hora_codigo")) is True` (R3); nada más de F-056 cambia.
- `application/services/tipo_hora_catalog.py`: docstring (`ext` es informativo). Sin código.
- `docs/ARCHITECTURE.md` semántica 3: una frase (R17). `CLAUDE.md` y `tests/` raíz: solo si
  DA8 = B. `progress/` según protocolo.

## 4. Ficheros que NO se tocan

`application/services/congelacion.py`, `esta_congelado` y `recurso_conciliador.py` (sv3),
`infrastructure/database/orm_models.py` (sv3 y sv4: sin esquema nuevo), los demás gemelos de
`CLAUDE.md`, `tipo_hora_matcher.py`, `sigrid_lookup_client.py`, las plantillas (salvo DA5),
sv1, sv2, sv3, sv5, colas, `infra/`. `azure-apps/partes.md` no cambia: `/api/sigrid/tipos-hora`
es interno del portal (un campo más, compatible) y no cambia lo que el proyecto expone ni consume.

## 5. Encaje en la arquitectura

`clase_hora.py` vive en `application/services` (regla de dominio Sigrid sin E/S, como
`congelacion.py`); el repositorio (infrastructure) ya importa de `application.services`
(congelación, sincronización, franquicia), así que no hay dependencia nueva de capa. El endpoint
y el repositorio usan la misma función: un solo punto de verdad dentro de sv4. No se crea
librería compartida entre servicios (ARCHITECTURE «Capas»): la regla sigue existiendo en sv4 y
sv5 por separado, y DA8 decide si pasa a la lista cerrada con guardián.

Diferencias conocidas entre copias (el guardián las fija, no las arregla): sv4 quita espacios
y devuelve `None` sin código; `HoraRecurso.es_extra` de sv5 no quita espacios y da `False`
sin código. Los códigos de `auxhor` llegan sin espacios a la izquierda, así que la tabla común
usa códigos reales (`HE01`, `HL01`, `CI01`, minúsculas) y trata `None` de sv4 como «no extra».

## 6. Tests (sin red ni BBDD)

| R | Test | Cómo |
|---|---|---|
| R1 | `test_f066_r1_regla_del_prefijo` | tabla parametrizada |
| R2 | `test_f066_r2_sincronizacion_reexporta` | `sincronizacion.es_hora_extra is clase_hora.es_hora_extra` |
| R3 | `test_f066_r3_sin_otra_regla_en_python` | fuente: `startswith("HE"` solo en `clase_hora.py` |
| R4/R5 | `test_f066_r4_he_con_ext_0_es_extra`, `test_f066_r5_hl_con_ext_1_es_normal` | repo SQLite; también `HE` sobre línea `extra` y `HL` sobre `extra` |
| R6 | `test_f066_r6_incidencia_no_cambia_tipo` | línea `es_incidencia=True`, código `HE01` |
| R7 | `test_f066_r7_sin_codigo_no_cambia_tipo` | `hora_codigo=None`, `hora_ext=1` ⇒ tipo intacto |
| R8 | `test_f066_r8_campos_y_undo_registrados` | todos los campos y una fila `registro_hora` en `undo_log` |
| R9 | `test_f066_r9_deshacer_restaura_tipo` | `HE`/`ext=0` ⇒ extra; deshacer ⇒ `normal` |
| R10 | `test_f066_r10_respuesta_por_prefijo` | `TestClient`, opción `HE01` `ext=0` ⇒ `tipo_hora="extra"`, `hora_ext=0` |
| R11 | tests existentes F-004/F-043/F-048 en verde | sin cambios |
| R12 | `test_f066_r12_varias_lineas` | dos PATCH, dos líneas, ambas `extra` |
| R13 | `test_f066_r13_tipos_hora_lleva_extra` | `HE01`/`ext=0` ⇒ `extra=True`; `HL01`/`ext=1` ⇒ `False`; sin código ⇒ `False`; `ext` intacto |
| R14 | `test_f066_r14_grupos_por_extra` | node: grupos y orden, `selected` de la actual |
| R15 | `test_f066_r15_js_sin_regla` | fuente de `buildOptions`: sin `.ext` ni `startsWith` |
| R16 | `test_f066_r16_gemelos_prefijo_he` | raíz, AST/texto (si DA8 = B) |
| R17 | revisión del reviewer | docs |
| R18 | `test_f066_r18_badges_intactos` | fuente: los 6 disyuntivos siguen (si DA5 = A) |

El test existente `test_f048_r23_cambiar_codigo_de_hora_no_la_toca` (`HE01`, `ext=1` ⇒ extra)
sigue valiendo sin cambios.

## 7. Verificaciones manuales (comandos exactos)

**M1** (líder, solo lectura, antes de T2):

- Sigrid vía sigrid-api (`POST` de lectura, base `ruesma_rep`):
  `SELECT cod, ext, COUNT(*) AS n FROM auxhor WHERE ext = 1 GROUP BY cod, ext` — si sale algún
  código no `HE`, DA5 se replantea.
- Base `partes`, sesión con `SET default_transaction_read_only = on`:
  `SELECT id, tipo_hora, sigrid_estado FROM parte_registros WHERE deleted_at_utc IS NULL AND
  es_incidencia = false AND upper(trim(hora_codigo)) LIKE 'HE%' AND tipo_hora = 'normal';`
  Esperado: 16417, 16422, 16640, `omitido` (o lo que haya cambiado desde el 2026-11-03).
  Y el inverso (`NOT LIKE 'HE%'` y `tipo_hora = 'extra'` con `hora_match_method = 'manual'`)
  para saber si el defecto tuvo la otra cara.

**M2** (humano, tras desplegar sv4): obra 0404 (`OBRA_PRUEBAS_FORZAR`), línea ordinaria sin
registrar: elegir una `HE*` en el desplegable (debe estar en «Horas extra») ⇒ Ctrl+F5 ⇒ badge
extra; deshacer ⇒ normal. No se aprueba ni se envía a Sigrid.

**M3** (humano): lo que decida DA6 sobre las 3 líneas.

## 8. Decisiones abiertas (PARADA 1)

| DA | Pregunta | Opciones | Recomendada |
|---|---|---|---|
| DA1 | ¿Dónde vive `es_hora_extra` dentro de sv4? | **A** módulo nuevo `application/services/clase_hora.py`, `sincronizacion.py` la reimporta. **B** importarla de `sincronizacion.py` tal cual. **C** `domain/`. | **A**: la regla no es de la sincronización; B ata el selector a F-052; sv4 no tiene `domain/` de reglas Sigrid (todas en `application/services`). |
| DA2 | ¿Quién fija `tipo_hora`? | **A** el repositorio `set_registro_hora` por `hora_codigo` (como hoy con `hora_ext`). **B** el endpoint calcula y pasa un parámetro `tipo_hora` nuevo. | **A**: un solo punto, cualquier llamador futuro hereda la regla, firma intacta (los tests de F-043/F-048 la usan). |
| DA3 | Opción sin código | **A** no tocar `tipo_hora`. **B** `normal`. | **A**: «no se sabe» no debe pasar una extra a normal (hoy daría `normal` por `ext = 0`). |
| DA4 | Desplegable | **A** el servidor manda `extra` y el JS agrupa por él. **B** el JS aplica el prefijo. | **A**: sin regla en JS (R15); `ext` se conserva por compatibilidad. |
| DA5 | Disyuntivos `hora_ext == 1` de badges y totales (§1 fila 6) | **A** no tocarlos; si M1 encuentra códigos no `HE` con `ext = 1`, feature aparte. **B** cambiarlos por `es_hora_extra(hora_codigo)`. **C** quitar el disyuntivo (solo `tipo_hora`). | **A**: con `tipo_hora` bien puesto son redundantes; B ocultaría las 3 líneas mal clasificadas (badge extra, sv5 escribiría `HL`); C cambia vistas que no son el defecto. |
| DA6 | Las 3 líneas afectadas (16417, 16422, 16640, `omitido`, obra 0678) | **A** no migrar: tras desplegar, el humano re-elige el código en cada una (queda `extra` por R4) o decide que era ordinaria, y reaprueba. **B** script puntual `UPDATE … SET tipo_hora = 'extra' WHERE id IN (…) AND tipo_hora = 'normal' AND upper(hora_codigo) LIKE 'HE%'`, lanzado por el humano. **C** reparación general de toda línea con `HE%` y `normal`. | **A**: son 3, ninguna registrada y con `omitido` no viajan solas; re-elegir deja deshacer y traza, y confirma la intención (la `HE` pudo ser un error). **Riesgo de A**: reaprobarlas **sin** re-elegir escribiría `HL`; el líder lo avisa al cerrar. |
| DA7 | sv3 (`recurso_conciliador.py`, `ext == 1` con respaldos) y F-006 (pide usar `auxhor.ext` «en lugar del prefijo») | **A** F-066 no toca sv3; proponer reescribir F-006 como «sv3 elige la extra del recurso por prefijo `HE`» (su premisa la refuta M2 de F-052). **B** cancelar F-006. **C** incluir sv3 aquí. | **A**: LÍMITE DE SERVICIO y `recurso_conciliador.py` es fichero de gemelos (congelación); F-006 con su texto actual reintroduciría el defecto. El líder cambia F-006 solo con el «sí» del humano. |
| DA8 | ¿La regla del prefijo entra en la lista cerrada de gemelos? Hoy está de hecho en sv4 (Python y SQL) y sv5 (dos copias) sin guardián. | **A** no; F-066 solo amplía su uso dentro de sv4. **B** sí, con guardián raíz `tests/test_f066_prefijo_he_gemelos.py` y entrada en `CLAUDE.md`. | **B**: decide qué hora se escribe en Sigrid; una divergencia sv4/sv5 sería silenciosa. Requiere decisión expresa del humano (la lista no crece sin ella). |
| DA9 | Rigor | **crítico** / estándar | **crítico**: `tipo_hora` llega a Sigrid como `HL`/`HE` (dinero); mutación completa de las líneas cambiadas (pocas). |

## 9. Riesgos

- **Cambio de comportamiento deliberado**: un código no `HE` con `ext = 1` dejará la línea
  `normal` (antes `extra`). Es lo que hace sv5; M1 dice si existe alguno.
- **JS cacheado**: hasta Ctrl+F5 el desplegable viejo agrupa por `ext`; el guardado ya es
  correcto en el servidor (la clase no la manda el cliente).
- **Sin badge en vivo**: tras guardar una sola línea el JS actualiza solo el texto del código,
  no el badge (como hoy); se ve al recargar. Fuera de alcance.
