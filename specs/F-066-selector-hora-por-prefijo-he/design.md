# F-066 · sv4 clasifica la hora extra por «`HE` salvo `HENC`» — Diseño

Base: rama `feature/F-066-selector-hora-por-prefijo-he` desde la punta de F-052 (0d8fc14).
Servicio: **solo sv4**. Requisitos en `requirements.md` (R1–R23); decisiones en §8. Revisada el
2026-11-06 con la M1 del líder (§7) y la decisión A del humano (regla con excepción `HENC`).

## 1. Inventario: dónde decide sv4 extra/ordinaria (barrido de Python, SQL, JS y plantillas)

| # | Sitio (sv4) | Qué hace hoy | F-066 |
|---|---|---|---|
| 1 | `infrastructure/database/parte_repository.py::set_registro_hora` (~3186–3220) | `tipo_hora = "extra" if hora_ext == 1 else "normal"` | **Cambia** (R6–R11): por `tipo_hora_de_codigo(hora_codigo)`. Es el defecto H-M2-1b. |
| 2 | `interface_adapters/web/app.py::set_registro_hora` (`PATCH /api/registros/{id}/hora`, ~3842–3877) | responde `tipo_hora` con `option.ext == 1` | **Cambia** (R12). Sigue pasando `hora_ext=option.ext`. |
| 3 | `app.py` `GET /api/sigrid/tipos-hora` (~1795–1808) | expone `ext` | **Cambia** (R15): añade `extra`. |
| 4 | `static/app.js::buildOptions` (~466–469) | agrupa por `t.ext === 1` (todas las `HE*` en «ordinarias») | **Cambia** (R16–R17): agrupa por `t.extra`. |
| 5 | `application/services/sincronizacion.py::es_hora_extra` (~158, F-052) | `startswith("HE")`: `HENC` cuenta como extra | **Se mueve** a `clase_hora.py` con la excepción y se reimporta (R1–R4). |
| 6 | `infrastructure/sigrid/sigrid_lookup_client.py::fetch_hora_extra_recurso` (~497–502) | `WHERE auxhor.cod LIKE 'HE%' ORDER BY auxhor.cod`, `TOP 1`: con `HENC` y `HEOF` elige **`HENC`** | **Cambia** (R18): `condicion_sql_extra("auxhor.cod")`. Lo usan `crear_extra_desde` (`/extra`) y `_hora_extra_celda` (F-049). |
| 7 | `sigrid_lookup_client.py::fetch_dnis_sin_extra` (~437–460) | `CASE WHEN auxhor.cod LIKE 'HE%'` en las dos ramas | **Cambia** (R19): mismo fragmento en las dos ramas. |
| 8 | `application/services/franquicia.py::extras_pendientes` (~244, F-056) | `.upper().startswith("HE")` | **Cambia** (R20): `es_hora_extra(...) is True`. |
| 9 | `parte_repository.py::_is_extra` (~879), `extras_por_jornada` (~5353), `app.py` (~1019), plantillas `obra_detail.html:241`, `parte_detail.html:159`, `trabajador_detail.html:292` | `tipo_hora == "extra" or hora_ext == 1` | **No se toca** (DA5, R22). |
| 10 | `sigrid_lookup_client.py::fetch_tipos_hora` (~252) | ordena por `(ext, codigo)` | **No se toca**: con `ext = 0` en todos (M1) es orden por código; el JS agrupa sin reordenar. |
| 11 | `application/services/tipo_hora_matcher.py` («+ Nuevo», celda F-049) | clasifica por la palabra `EXTRA` de la descripción (espejo de sv3) | **No se toca**: el tipo lo fija el campo que rellena el usuario; `HENC` («HORA ENCARGADO») no lleva `EXTRA`, así que ya no lo elige como extra. |
| 12 | `parte_repository.py::crear_extra_desde` (~1952–1958), `app.py::_hora_extra_celda` (~2332) | `tipo_hora="extra"`, `hora_ext=1` fijo con la hora de la fila 6 | **No se toca**: queda bien al arreglar la fila 6. |

Plantillas y el resto de `app.js`: sin otros usos (grep de `HE`, `.ext`, `hora_ext`). Fuera de
sv4 (no se tocan): sv5 `registro_models.py::HoraRecurso.es_extra`, `franquicia.py::_es_extra` y
el resto de usos del prefijo → **F-067**; sv3 `recurso_conciliador.py` (~300–315) → DA7.

## 2. Ficheros a crear

- `services/partes-front/application/services/clase_hora.py` (application, puro, sin E/S):
  - `PREFIJO_EXTRA = "HE"`, `CODIGOS_NO_EXTRA: tuple[str, ...] = ("HENC",)` con el porqué
    (M1 2026-11-06, decisión A del humano) en el comentario.
  - `es_hora_extra(codigo: str | None) -> bool | None` (R1).
  - `tipo_hora_de_codigo(codigo: str | None) -> str | None`: `"extra"`/`"normal"`/`None`.
  - `condicion_sql_extra(columna: str) -> str` (R3): `(UPPER(LTRIM(RTRIM(col))) LIKE 'HE%' AND
    UPPER(LTRIM(RTRIM(col))) NOT IN ('HENC'))`, generado de las constantes; `columna` la pone el
    código (nunca el usuario) y se valida con una regex de identificador (`ValueError` si no).
- `services/partes-front/tests/test_f066_clase_hora.py` — R1–R5 (tablas, derivación de las
  constantes con `monkeypatch`, fuente: ni `startswith("HE"` ni `LIKE 'HE%'` fuera de
  `clase_hora.py`).
- `services/partes-front/tests/test_f066_set_registro_hora.py` — R6–R14 (repositorio sobre
  `FabricaSesionSqlite` como `test_f048_traza_portal.py`; endpoint con `TestClient`, catálogo y
  repositorio falsos como `test_f004_endpoints_congelados.py`).
- `services/partes-front/tests/test_f066_selector_js.py` — R15 (endpoint) y R16–R17: se extrae
  `buildOptions` de `app.js` y se ejecuta en node sobre un DOM mínimo (patrón
  `test_f064_filtros_js.py`); sin node, `skip` como allí.
- `services/partes-front/tests/test_f066_usos_sv4.py` — R18–R20: cliente con `_post_sql_read`
  falso que captura el SQL y devuelve filas sintéticas (patrón `test_f023_catalogo_empresa.py`);
  `extras_pendientes` con acciones `HENC` y `HEOF`.

## 3. Ficheros a modificar

- `application/services/sincronizacion.py`: borra el cuerpo de `es_hora_extra` y la importa
  de `clase_hora` (re-export con `# noqa: F401`); docstrings que dicen «prefijo `HE`» pasan a
  citar la regla. Tests de F-052 que fijen `HENC` como extra, si los hay, se ajustan (R4).
- `infrastructure/database/parte_repository.py::set_registro_hora`: sustituye

  ```python
  if hora_ext is not None and not reg.es_incidencia:
      reg.tipo_hora = "extra" if hora_ext == 1 else "normal"
  ```
  por `tipo = tipo_hora_de_codigo(hora_codigo)`; `if tipo is not None and not
  reg.es_incidencia: reg.tipo_hora = tipo`. Firma, guardas (F-004, F-043), snapshot y deshacer
  no cambian (`tipo_hora` ya está en `_REG_UNDO_FIELDS`).
- `interface_adapters/web/app.py`: `set_registro_hora` responde
  `tipo_hora_de_codigo(option.codigo) or "normal"`; `tipos-hora` añade
  `"extra": es_hora_extra(t.codigo) is True`.
- `infrastructure/sigrid/sigrid_lookup_client.py`: `fetch_hora_extra_recurso` y las dos ramas de
  `fetch_dnis_sin_extra` usan `condicion_sql_extra("auxhor.cod")`; el comentario de ~437 cita la
  regla. `_SQL_EMPLEADOS` y `_SQL_RECURSOS_ACTIVOS` (gemelos F-023/F-036) **no** se tocan.
- `application/services/franquicia.py::extras_pendientes`: `es_hora_extra(a.get("hora_codigo"))
  is True`; docstrings `HE*` → «horas extra (regla de `clase_hora`)».
- `static/app.js::buildOptions`: `t.extra === true` / `t.extra !== true`; nada más del IIFE.
- `application/services/tipo_hora_catalog.py`: docstring (`ext` informativo).
- `docs/ARCHITECTURE.md` semántica 3 (R21). `progress/` según protocolo. `CLAUDE.md` **no**.

## 4. Ficheros que NO se tocan

`application/services/congelacion.py`, `esta_congelado` y `recurso_conciliador.py` (sv3),
`infrastructure/database/orm_models.py` (sv3 y sv4: sin esquema), los gemelos de `CLAUDE.md`
(incluidos `_SQL_EMPLEADOS` y `_SQL_RECURSOS_ACTIVOS` del mismo cliente), `tipo_hora_matcher.py`,
las plantillas, sv1, sv2, sv3, **sv5** (F-067), colas, `infra/`, `CLAUDE.md`.
`azure-apps/partes.md` no cambia: `/api/sigrid/tipos-hora` es interno del portal (un campo más,
compatible) y no cambia lo que el proyecto expone ni consume.

## 5. Encaje en la arquitectura

`clase_hora.py` es una regla de dominio Sigrid sin E/S en `application/services` (como
`congelacion.py`). El repositorio ya importa de `application.services`; el cliente
`sigrid_lookup_client.py` gana esa importación por primera vez (DA1): es la forma de que el
SQL y el Python de sv4 no tengan dos copias de la excepción. No hay librería compartida entre
servicios: sv5 tendrá su propio sitio único en F-067 y el guardián de gemelos vigilará las dos.

## 6. Tests (sin red ni BBDD)

| R | Test | Cómo |
|---|---|---|
| R1 | `test_f066_r1_regla` | tabla parametrizada (incluye `HENC`, `MENC`, espacios) |
| R2 | `test_f066_r2_derivada_de_constantes` | `monkeypatch` de `CODIGOS_NO_EXTRA` cambia las tres funciones |
| R3 | `test_f066_r3_condicion_sql` | texto exacto; `ValueError` con columna no identificador |
| R4 | `test_f066_r4_sincronizacion_reexporta` | `is` misma función; `comparar` con `HENC` en Sigrid y portal `normal` ⇒ sin diferencia de clase |
| R5 | `test_f066_r5_sin_otra_regla` | fuente de sv4 |
| R6/R7 | `test_f066_r6_he_ext_0_extra`, `test_f066_r7_henc_y_hl_normal` | repo SQLite, desde líneas `normal` y `extra` |
| R8/R9 | `test_f066_r8_incidencia_intacta`, `test_f066_r9_sin_codigo_intacto` | |
| R10/R11 | `test_f066_r10_campos_y_undo`, `test_f066_r11_deshacer_restaura_tipo` | `undo_log` |
| R12/R13/R14 | `test_f066_r12_respuesta`, tests F-004/F-043/F-048 existentes, `test_f066_r14_varias_lineas` | `TestClient` |
| R15 | `test_f066_r15_tipos_hora_lleva_extra` | `HEOF`⇒`True`, `HENC`⇒`False`, sin código ⇒ `False`, `ext` intacto |
| R16/R17 | `test_f066_r16_grupos_por_extra`, `test_f066_r17_js_sin_regla` | node; fuente |
| R18/R19 | `test_f066_r18_hora_extra_recurso`, `test_f066_r19_dnis_sin_extra` | SQL capturado contiene `condicion_sql_extra`; filas falsas |
| R20 | `test_f066_r20_extras_pendientes_sin_henc` | acciones `HENC` 2 h + `HEOF` 3 h ⇒ 3 |
| R21 | revisión del reviewer | |
| R22 | `test_f066_r22_disyuntivos_intactos` | fuente: los 6 siguen |

`test_f048_r23_cambiar_codigo_de_hora_no_la_toca` (`HE01` ⇒ extra) sigue valiendo.

## 7. M1 — HECHA (líder, 2026-11-06, solo lectura)

Comando corregido: `auxhor` está en la base **`ruesma`** (la réplica `ruesma_rep` no la tiene),
lectura vía sigrid-api. Resultados:

- **`ext = 1`: ninguna fila** en `auxhor`. Los 7 `HE*` tienen `ext = 0`: `HEAA` HORA EXTRA
  AYUDANTE (0 usos en `hmores`), `HECAP` HORA EXTRA CAPATAZ (23695), `HEGR` HORA EXTRA GRUISTA
  (33995), **`HENC` HORA ENCARGADO (1 uso; no es extra)**, `HEOF` HORA EXTRA OFICIAL (59976),
  `HEOM` HORA EXTRA OFICIAL DE MIRAS (0), `HEPE` HORA EXTRA PEON (5759).
- Base `partes` (`default_transaction_read_only = on`): líneas `HE*` con `tipo_hora = 'normal'`:
  solo 7 `HENC` (registros 44, 46, 53, 55, 67, 69, 142), sin estado, de documentos inactivos
  (obras 0678 y 0713): `normal` es **correcto** con la regla A. Por código: `HECAP` extra 205,
  `HEGR` extra 136, `HENC` normal 7, `HEOF` extra 199, `HEPE` extra 27. Los registros 16417,
  16422 y 16640 del 2026-11-03 ya tienen `hora_codigo = 'MENC'`.
- Inverso (código no `HE` con `tipo_hora = 'extra'` y `hora_match_method = 'manual'`): ninguna.

**M2** (humano, tras desplegar sv4): ver `requirements.md`.

## 8. Decisiones abiertas (PARADA 1)

| DA | Pregunta | Opciones | Recomendada |
|---|---|---|---|
| DA1 | ¿Dónde vive la regla en sv4? | **A** `application/services/clase_hora.py` (Python + fragmento SQL), importado por sincronización, repositorio, endpoint, franquicia y cliente Sigrid. **B** constantes en `clase_hora` y el SQL escrito en el cliente. | **A**: la excepción `HENC` en un solo sitio (decisión A del humano); B deja dos textos que divergen. |
| DA2 | ¿Quién fija `tipo_hora`? | **A** el repositorio por `hora_codigo`. **B** el endpoint pasa un `tipo_hora` nuevo. | **A**: un punto, firma intacta. |
| DA3 | Opción sin código | **A** no tocar `tipo_hora`. **B** `normal`. | **A**: «no se sabe» no pasa una extra a normal. |
| DA4 | Desplegable | **A** el servidor manda `extra`. **B** el JS aplica la regla. | **A**: sin tercera copia (R17). |
| DA5 | Disyuntivos `hora_ext == 1` (§1 fila 9) | **A** no tocarlos. **B** cambiarlos por la regla. **C** quitarlos. | **A**, **confirmada por M1**: ningún `auxhor` tiene `ext = 1`, así que `hora_ext == 1` solo existe en las líneas de la fila 12, que nacen `extra`. Única divergencia posible: una de ellas pasada a `normal` a mano con `update_registro` (badge extra, sv5 escribiría `HL`). Caso de borde fuera de alcance; C es la limpieza natural en otra feature. |
| DA6 | ~~Las 3 líneas 16417, 16422, 16640~~ | — | **Retirada** (2026-11-06): M1 muestra que ya tienen `MENC` y que las únicas `HE*` con `normal` son 7 `HENC`, correctas con la regla A. No hay nada que migrar. |
| DA7 | sv3 (`recurso_conciliador.py`) y F-006 | **A** F-066 no toca sv3; proponer reescribir F-006 como «sv3 elige la hora extra del recurso con la regla `HE` salvo `HENC`». **B** cancelar F-006. **C** incluir sv3 aquí. | **A**, y la excepción lo **refuerza**: la rama `ext == 1` de sv3 está muerta (M1); la de la descripción («extra») ya excluye `HENC`; pero la de último recurso («primera hora de trabajo distinta de la ordinaria») puede elegir `HENC` o una `HL`. F-006 tal como está (usar `ext`) no serviría. Sería la tercera copia de la regla: entra en el guardián de F-067 o en F-006. LÍMITE DE SERVICIO y fichero de gemelos (congelación). |
| DA8 | Gemelos de la regla | **A** el guardián raíz y la propuesta de entrada en la lista cerrada de `CLAUDE.md` van en **F-067**, cuando sv4 y sv5 coincidan. **B** en F-066. | **A** (instrucción del líder): en F-066 sv4 y sv5 difieren a propósito en `HENC`; un guardián hoy fallaría. La entrada en `CLAUDE.md` es una DA de F-067 y requiere el «sí» del humano. |
| DA9 | Rigor | crítico / estándar | **crítico**: la clase llega a Sigrid. Mutación completa de las líneas cambiadas. |
| DA10 | Desfase sv4/sv5 entre F-066 y F-067 | **A** desplegar F-066 sin esperar a F-067. **B** desplegarlas juntas (sv5 primero). | **A**: la exposición medida es mínima (`HENC` tiene 1 uso en `hmores` y 7 líneas inactivas en `partes`). Mientras dure, sv5 aún trata `HENC` como extra en `franquicia` (E, X) y en «sin ningún `HE%` ⇒ fuera», y sv4 no (R19–R20): un encargado con solo `HENC` saldría distinto en el aviso de franquicia y en los totales. B si el humano prefiere cero desfase. |

## 9. Riesgos

- **Cambio de comportamiento deliberado**: `HENC` deja de ser extra en todo sv4 (sincronizar,
  franquicia, `/extra`, celda, totales por DNI). Lo pide la decisión A; M1 da la exposición.
- **Desfase con sv5** hasta F-067 (DA10).
- **JS cacheado**: hasta Ctrl+F5 el desplegable viejo agrupa por `ext`; el guardado ya es
  correcto (la clase no la manda el cliente).
- **Sin badge en vivo**: tras guardar una línea el JS actualiza solo el texto del código, no el
  badge (como hoy). Fuera de alcance.
