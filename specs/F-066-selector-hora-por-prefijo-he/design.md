# F-066 · sv4: hora extra por el prefijo `HE` y `HENC` excluido — Diseño

Base: rama `feature/F-066-selector-hora-por-prefijo-he` desde la punta de F-052 (0d8fc14).
Servicio: **solo sv4**. Requisitos en `requirements.md` (R1–R24); decisiones en §8. Revisada el
2026-11-06 con la M1 del líder (§7) y la decisión del humano «HENC no debe ser tenido en cuenta
por la app» (alcance aprobado con «ok»), que sustituye a la regla «`HE` salvo `HENC`».

## 1. Inventario: dónde decide sv4 extra/ordinaria (barrido de Python, SQL, JS y plantillas)

| # | Sitio (sv4) | Qué hace hoy | F-066 |
|---|---|---|---|
| 1 | `infrastructure/database/parte_repository.py::set_registro_hora` (~3186–3220) | `tipo_hora = "extra" if hora_ext == 1 else "normal"` | **Cambia** (R12–R16): `tipo_hora_de_codigo(hora_codigo)`. Es el defecto H-M2-1b. |
| 2 | `interface_adapters/web/app.py::set_registro_hora` (`PATCH …/hora`, ~3842–3877) | responde `tipo_hora` con `option.ext == 1` | **Cambia** (R17). Sigue pasando `hora_ext=option.ext`. |
| 3 | `infrastructure/sigrid/sigrid_lookup_client.py::fetch_tipos_hora` (~230–254) | devuelve todo `auxhor` (con `HENC`), ordenado por `(ext, codigo)` | **Cambia** (R7): omite los excluidos. El orden no cambia (con `ext = 0` en todos es por código). |
| 4 | `app.py` `GET /api/sigrid/tipos-hora` (~1795–1808) | expone `ext` | **Cambia** (R9): añade `extra`. |
| 5 | `static/app.js::buildOptions` (~466–469) | agrupa por `t.ext === 1` (todas las `HE*` en «ordinarias») | **Cambia** (R10–R11): agrupa por `t.extra`. |
| 6 | `application/services/sincronizacion.py::es_hora_extra` (~158, F-052) | `startswith("HE")` | **Se mueve** a `clase_hora.py` y se reimporta (R2, R5). |
| 7 | `sigrid_lookup_client.py::fetch_hora_extra_recurso` (~497–502) | `WHERE auxhor.cod LIKE 'HE%' ORDER BY auxhor.cod`, `TOP 1` | **Cambia** (R19): `condicion_sql_extra("auxhor.cod")`. Defensivo: `HENC` no está en `reshor`. |
| 8 | `sigrid_lookup_client.py::fetch_dnis_sin_extra` (~437–460) | `CASE WHEN auxhor.cod LIKE 'HE%'` en dos ramas | **Cambia** (R20), mismo fragmento. |
| 9 | `application/services/franquicia.py::extras_pendientes` (~244, F-056) | `.upper().startswith("HE")` | **Cambia** (R21): `es_hora_extra(...) is True`. |
| 10 | `application/services/tipo_hora_matcher.py` («+ Nuevo», celda F-049) | casa por categoría sobre lo que da `fetch_tipos_hora`; para «ENCARGADO» normal podía elegir `HENC` (así lo hizo sv3 con las 7 líneas, `categoria_normal`) | **No se toca**: deja de ver `HENC` por la fila 3. |
| 11 | `parte_repository.py::_is_extra` (~879), `extras_por_jornada` (~5353), `app.py` (~1019), plantillas `obra_detail.html:241`, `parte_detail.html:159`, `trabajador_detail.html:292` | `tipo_hora == "extra" or hora_ext == 1` | **No se toca** (DA5, R23). |
| 12 | `parte_repository.py::crear_extra_desde` (~1952–1958), `app.py::_hora_extra_celda` (~2332) | `tipo_hora="extra"`, `hora_ext=1` fijo con la hora de la fila 7 | **No se toca**: hereda la fila 7. |

Plantillas y resto de `app.js`: sin otros usos (grep de `HE`, `HENC`, `.ext`, `hora_ext`). Fuera
de sv4: sv3 (`recurso_conciliador.py` ~300–315, último recurso) y sv5 (`HoraRecurso.es_extra`,
`franquicia._es_extra`, `reglas_registro`) → **F-067**.

## 2. Ficheros a crear

- `services/partes-front/application/services/clase_hora.py` (application, puro, sin E/S):
  - `PREFIJO_EXTRA = "HE"` y `CODIGOS_EXCLUIDOS: tuple[str, ...] = ("HENC",)`, con el porqué en
    el comentario (decisión del humano 2026-11-06, M1: `auxhor` ide 63, 0 filas en `reshor`).
  - `es_excluido(codigo: str | None) -> bool` (R1).
  - `es_hora_extra(codigo: str | None) -> bool | None` (R2): `None` sin código, `False` si
    excluido, si no el prefijo.
  - `tipo_hora_de_codigo(codigo: str | None) -> str | None`: `"extra"`/`"normal"`/`None`.
  - `condicion_sql_extra(columna: str) -> str` (R4), generado de las constantes; `columna`
    pasa por una regex de identificador (`ValueError` si no).
- `services/partes-front/tests/test_f066_clase_hora.py` — R1–R6 (tablas, `monkeypatch` de las
  constantes, fuente).
- `services/partes-front/tests/test_f066_set_registro_hora.py` — R8, R12–R18 (repositorio sobre
  `FabricaSesionSqlite` como `test_f048_traza_portal.py`; endpoint con `TestClient`, catálogo y
  repositorio falsos como `test_f004_endpoints_congelados.py`).
- `services/partes-front/tests/test_f066_selector_js.py` — R7 (cliente con lectura falsa que
  devuelve `HENC`), R9 y R10–R11 (se extrae `buildOptions` de `app.js` y se ejecuta en node
  sobre un DOM mínimo, patrón `test_f064_filtros_js.py`; sin node, `skip`).
- `services/partes-front/tests/test_f066_usos_sv4.py` — R19–R21 (cliente con `_post_sql_read`
  falso que captura el SQL, patrón `test_f023_catalogo_empresa.py`; `extras_pendientes` con
  acciones `HENC` y `HEOF`).

## 3. Ficheros a modificar

- `application/services/sincronizacion.py`: borra el cuerpo de `es_hora_extra` y la importa
  de `clase_hora` (re-export con `# noqa: F401`); docstrings citan la regla.
- `infrastructure/database/parte_repository.py::set_registro_hora`: sustituye

  ```python
  if hora_ext is not None and not reg.es_incidencia:
      reg.tipo_hora = "extra" if hora_ext == 1 else "normal"
  ```
  por `tipo = tipo_hora_de_codigo(hora_codigo)`; `if tipo is not None and not
  reg.es_incidencia: reg.tipo_hora = tipo`. Firma, guardas, snapshot y deshacer no cambian
  (`tipo_hora` ya está en `_REG_UNDO_FIELDS`).
- `interface_adapters/web/app.py`: `set_registro_hora` responde
  `tipo_hora_de_codigo(option.codigo) or "normal"`; `tipos-hora` añade
  `"extra": es_hora_extra(t.codigo) is True`.
- `infrastructure/sigrid/sigrid_lookup_client.py`: `fetch_tipos_hora` descarta las filas con
  `es_excluido(codigo)` antes de construir la lista (log INFO con el número omitido);
  `fetch_hora_extra_recurso` y las dos ramas de `fetch_dnis_sin_extra` usan
  `condicion_sql_extra("auxhor.cod")`. `_SQL_EMPLEADOS` y `_SQL_RECURSOS_ACTIVOS` (gemelos
  F-023/F-036) **no** se tocan.
- `application/services/franquicia.py::extras_pendientes`: `es_hora_extra(a.get("hora_codigo"))
  is True`; docstrings `HE*` → «horas extra (`clase_hora`)».
- `static/app.js::buildOptions`: `t.extra === true` / `t.extra !== true`; nada más del IIFE.
- `application/services/tipo_hora_catalog.py`: docstring (`ext` informativo, sin excluidos).
- `docs/ARCHITECTURE.md` semántica 3 (R22). `progress/` según protocolo. `CLAUDE.md` **no**.

## 4. Ficheros que NO se tocan

`application/services/congelacion.py`, `esta_congelado`, `ESTADOS_CONGELADOS` y
`recurso_conciliador.py` (sv3), `infrastructure/database/orm_models.py` (sin esquema), los
gemelos de `CLAUDE.md`, `tipo_hora_matcher.py`, `tipo_hora_catalog.py` (salvo docstring), las
plantillas, sv1, sv2, sv3 y sv5 (F-067), colas, `infra/`, `CLAUDE.md`. `azure-apps/partes.md` no
cambia: `/api/sigrid/tipos-hora` es interno del portal y no cambia lo que se expone ni consume.

## 5. Encaje en la arquitectura

`clase_hora.py` es una regla de dominio Sigrid sin E/S en `application/services` (como
`congelacion.py`). El repositorio ya importa de `application.services`; `sigrid_lookup_client.py`
gana esa importación por primera vez (DA1): así el SQL y el Python de sv4 comparten la lista. No
hay librería compartida entre servicios: sv3 y sv5 tendrán su sitio único en F-067 y el guardián
de gemelos vigilará los tres.

## 6. Tests (sin red ni BBDD)

| R | Test | Cómo |
|---|---|---|
| R1/R2 | `test_f066_r1_excluidos`, `test_f066_r2_regla_extra` | tablas parametrizadas |
| R3/R4 | `test_f066_r3_derivadas`, `test_f066_r4_condicion_sql` | `monkeypatch`; texto exacto y `ValueError` |
| R5 | `test_f066_r5_sincronizacion_excluido_no_es_extra` | `is` misma función; `comparar` con `HENC` en Sigrid y portal `normal` ⇒ sin diferencia de clase |
| R6/R11 | `test_f066_r6_sin_otra_regla`, `test_f066_r11_js_sin_regla` | fuente de sv4 y de `buildOptions` |
| R7 | `test_f066_r7_catalogo_sin_excluidos` | `fetch_tipos_hora` con `HENC` en las filas falsas ⇒ no sale; `TipoHoraMatcher` para «Encargado» no la elige |
| R8 | `test_f066_r8_patch_excluido_400` | catálogo real sobre cliente falso; línea intacta |
| R9/R10 | `test_f066_r9_tipos_hora_lleva_extra`, `test_f066_r10_grupos_por_extra` | `TestClient`; node |
| R12–R16 | `test_f066_r12_he_ext_0_extra`, `…_r13_hl_ext_1_normal`, `…_r14_incidencia`, `…_r15_sin_codigo`, `…_r16_campos_y_deshacer` | repo SQLite, `undo_log` |
| R17/R18 | `test_f066_r17_respuesta`, `test_f066_r18_varias_lineas` + tests F-004/F-043/F-048 | `TestClient` |
| R19–R21 | `test_f066_r19_hora_extra_recurso`, `…_r20_dnis_sin_extra`, `…_r21_extras_pendientes` | SQL capturado; `HENC` 2 h + `HEOF` 3 h ⇒ 3 |
| R22 | revisión del reviewer | |
| R23 | `test_f066_r23_disyuntivos_intactos` | fuente: los 6 siguen |

## 7. M1 — HECHA (líder, 2026-11-06, solo lectura)

`auxhor` vive en la base **`ruesma`** (la réplica `ruesma_rep` no la tiene), lectura vía
sigrid-api.

- **`ext = 1`: ninguna fila**. Los 7 `HE*` tienen `ext = 0`: `HEAA` (0 usos en `hmores`),
  `HECAP` (23695), `HEGR` (33995), **`HENC` «HORA ENCARGADO»** (1), `HEOF` (59976), `HEOM` (0),
  `HEPE` (5759).
- **`HENC`**: `auxhor` ide 63, unidad horas (`medide` 1), sin cuenta analítica (`caacod`) ni
  concepto de nómina (`connom`), modificado por última vez en 2022. **1 uso** en `hmores`: obra
  0640, 21/04/2022, 4 h a 1 €, sin synckey (manual). **0 filas en `reshor`**.
- Base `partes` (`default_transaction_read_only = on`): las únicas `HE*` con `normal` son 7
  `HENC` (registros 44, 46, 53, 55, 67, 69, 142), sin estado, de documentos inactivos (obras 0678
  y 0713), asignadas por sv3 (`hora_match_method = categoria_normal`). Por código: `HECAP` extra
  205, `HEGR` extra 136, `HEOF` extra 199, `HEPE` extra 27. Los registros 16417, 16422 y 16640
  ya tienen `MENC`. Inverso (no `HE`, `extra`, `manual`): ninguna.

## 8. Decisiones

| DA | Pregunta | Opciones | Recomendada / estado |
|---|---|---|---|
| DA1 | ¿Dónde viven la lista y la regla en sv4? | `clase_hora.py` (Python y fragmento SQL) | **Decidida** por el humano (2026-11-06, «ok»). |
| DA2 | ¿Quién fija `tipo_hora`? | **A** el repositorio por `hora_codigo`. **B** el endpoint pasa un `tipo_hora` nuevo. | **A**: un punto, firma intacta. |
| DA3 | Opción sin código | **A** no tocar `tipo_hora`. **B** `normal`. | **A**: «no se sabe» no pasa una extra a normal. |
| DA4 | Desplegable | **A** el servidor manda `extra`. **B** el JS aplica la regla. | **A**: sin tercera copia (R11). |
| DA5 | Disyuntivos `hora_ext == 1` (§1 fila 11) | **A** no tocarlos. **B** por la regla. **C** quitarlos. | **A**, confirmada por M1: sin `ext = 1` en `auxhor`, `hora_ext == 1` solo existe en las líneas de la fila 12, que nacen `extra`. Borde: una de ellas pasada a `normal` a mano (`update_registro`) se vería extra; fuera de alcance, C sería la limpieza en otra feature. |
| DA6 | ~~Las 3 líneas 16417, 16422, 16640~~ | — | **Retirada**: ya tienen `MENC`; las 7 `HENC` del portal quedan fuera de alcance por decisión del humano. |
| DA7 | sv3 (`recurso_conciliador.py`) | — | **A F-067** (decisión del humano). **Propuesta sobre F-006** (sin cambiarla): pide usar `auxhor.ext` para reconocer las `HE%`; con `ext = 1` en ningún código (M1) no tiene sentido, y lo que sí hace falta en sv3 (no asignar `HENC`, regla de extra por prefijo) lo cubre F-067. Propuesta: cerrarla como superada por F-066/F-067 si el humano lo confirma. |
| DA8 | Gemelos | guardián raíz de lista y regla (sv3, sv4, sv5) y entrada en `CLAUDE.md` | **En F-067** (la entrada es DA de F-067, pendiente del «sí» del humano). Hasta entonces sv4 excluye `HENC` y sv3/sv5 no: un guardián hoy fallaría. |
| DA9 | Rigor | crítico / estándar | **crítico**: mutación completa de las líneas cambiadas. |
| DA10 | Desfase sv4 frente a sv3/sv5 hasta F-067 | **A** desplegar F-066 sin esperar. **B** juntas. | **A**, mantenida por el humano: `HENC` no está en `reshor`, así que sv5 no la elige; solo sv3 podría asignarla por categoría a una línea nueva (como las 7 antiguas), y el portal la mostraría sin ofrecerla. |
| DA11 | ¿Dónde se quitan los excluidos del catálogo? | **A** en `fetch_tipos_hora` (cubre desplegable, `get_by_ide`, matcher de «+ Nuevo» y celda, incidencias). **B** solo en `TipoHoraCatalog`. | **A**: B dejaría que «+ Nuevo» asignase `HENC` a un encargado por categoría. |
| DA12 | `PATCH` con el `hora_ide` de un excluido | **A** 400 «no existe» (sale solo de DA11). **B** 422 con motivo propio. | **A**: el desplegable no lo ofrece; solo llega a mano. |

## 9. Riesgos

- **Líneas con `HENC` ya guardadas** (7, inactivas): se ven con su código; al abrir el
  desplegable no aparece como actual (no está en la lista). Fuera de alcance; sv5 las omitirá con
  F-067.
- **JS cacheado**: hasta Ctrl+F5 el desplegable viejo agrupa por `ext`; el guardado ya es
  correcto en el servidor.
- **Sin badge en vivo**: tras guardar una línea el JS actualiza solo el texto del código (como
  hoy). Fuera de alcance.
