<!-- specs/F-039-nombre-empresa-en-combos/design.md -->
# F-039 · Portal: nombre de la empresa en combos y Conciliar — Diseño

## 1. Límite de servicio

Solo **sv4** (`services/partes-front/`): es presentación del portal. No hay
lógica nueva que pueda pertenecer a otro servicio ni duplicación de la lista
cerrada de `CLAUDE.md`. Las rutas tocadas son internas del portal
(`include_in_schema=False` o consumidas solo por `app.js`): no cambia nada de
lo que el proyecto expone a otros, así que `azure-apps/` no se actualiza.

## 2. Ficheros

### A modificar (rutas relativas a `services/partes-front/`)

- `application/services/empresas.py` — añadir
  `nombre_empresa_o_vacio(numero: int | None) -> str`: `""` si `numero` es
  `None`; si no, `nombre_empresa(numero)`. Capa **application**, función pura.
- `interface_adapters/web/app.py`:
  - importar `nombre_empresa_o_vacio` (y dejar de importar `nombre_empresa`
    si queda sin uso);
  - `sigrid_obras`: añadir `"empresa_nombre": nombre_empresa_o_vacio(o.empresa)`
    a cada item (R1);
  - `sigrid_recursos`: ídem con `r.empresa` (R2);
  - `conciliacion_buscar`: ídem con `e.empresa` (R3);
  - `sigrid_empleados`: ídem en `fila` con `e.empresa` (R4);
  - `_candidato_con_empresa`: sustituir la expresión condicional por
    `nombre_empresa_o_vacio(empresa)` (R11, mismo resultado).
- `static/app.js` — solo `empresaSufijo` (~l. 201-205):

  ```js
  // F-023 (R41) / F-039: la empresa acompaña a obras y recursos en los
  // combos; el nombre corto lo manda el servidor (`empresa_nombre`).
  function empresaSufijo(x) {
    if (!x || x.empresa == null) return "";
    return " · " + (x.empresa_nombre || ("Empresa " + x.empresa));
  }
  ```

  Sus tres usos (`obraLabel`, `recLabel`, búsqueda manual de Conciliar
  ~l. 757) ya la llaman: no cambian.

### A crear

- `tests/test_f039_nombre_empresa.py` (§4).

### Que NO se tocan

- `fijarEmpresa` (~l. 228): añade «Empresa N» solo cuando el número no está
  entre las opciones, y las opciones salen de `EMPRESAS` (= `NOMBRES_EMPRESA`):
  por construcción, solo números sin nombre. Ya cumple la regla.
- `templates/conciliacion.html` l. 65: mismo caso («Empresa N» solo para un
  `empresa_defecto` fuera de `EMPRESAS`).
- `templates/*.html` en general, `NOMBRES_EMPRESA`, global `EMPRESAS`,
  `texto_empresas`/`empresas_de_fila` (F-033), catálogos y clientes de
  `infrastructure/sigrid/`, `orm_models.py`, `docs/ARCHITECTURE.md`.

## 3. Decisiones

- **DA1 · Nombre por item en la API (elegida) frente a exponer el mapa una
  vez en la página.** Cada item con `empresa` lleva `empresa_nombre`
  calculado en el servidor con `empresas.py`.
  - A favor: sigue el precedente de F-035 (`_candidato_con_empresa`); se
    prueba en Python con `TestClient`, sin depender de que la plantilla haya
    inyectado un global JS; las cachés (`_recCache`, obras) ya llevan el
    nombre; ningún nombre en `app.js`.
  - Descartada: `<script>window.EMPRESAS = {{ EMPRESAS|tojson }}</script>`
    en `base.html` — también es fuente única, pero añade estado global y
    acopla `app.js` al orden de carga de la plantilla; los combos que viven
    fuera de `base.html` dependerían de ello sin test que lo vigile.
- **Fallback «Empresa N» en JS.** Solo defensivo (item sin `empresa_nombre`,
  p. ej. respuesta de un sv4 anterior en caché del navegador). No es un
  nombre de empresa, es el formato de «sin nombre», igual que en
  `nombre_empresa`. R10 vigila que el dict no se copie.
- **R4 (empleados).** Ningún combo pinta hoy su empresa; se añade para que
  la regla «todo item con `empresa` lleva `empresa_nombre`» sea uniforme.
  Coste: una línea. Si el humano prefiere el mínimo estricto, se quita R4 y
  su test sin afectar al resto.
- **Efecto colateral aceptado.** El combo de obra filtra por
  `_norm(obraLabel(o))`: escribir «porsan» encontrará las obras de Porsan.
  Antes «empresa 28». Se considera mejora; no requiere test propio.

## 4. Tests (`tests/test_f039_nombre_empresa.py`)

Sin red ni PostgreSQL: mismos dobles que `tests/test_f035_endpoints.py`
(catálogos simulados de obras, recursos y empleados; SQLite en memoria).
Datos sintéticos con empresas 1, 28 y una sin nombre (p. ej. 5) y una obra o
recurso con `empresa=None`.

| R | Test | Cómo |
|---|---|---|
| R1 | `test_f039_r1_obras_lleva_empresa_nombre` | `GET /api/sigrid/obras`: 1→Ruesma, 28→Porsan, None→`""` |
| R2 | `test_f039_r2_recursos_lleva_empresa_nombre` | `GET /api/sigrid/recursos` |
| R3 | `test_f039_r3_buscar_lleva_empresa_nombre` | `GET /api/conciliacion/buscar?q=…` |
| R4 | `test_f039_r4_empleados_lleva_empresa_nombre` | `GET /api/sigrid/empleados` |
| R5 | `test_f039_r5_empresa_sin_nombre_es_empresa_n` | unidad `nombre_empresa_o_vacio(5)` == «Empresa 5» y endpoint con empresa 5 |
| R6–R8 | `test_f039_r6..r8_empresa_sufijo_*` | **node**: extraer `empresaSufijo` de `app.js` (patrón `_funcion` de `test_f021_preflight_cuenta.py`) y ejecutarla; `skipif` sin node |
| R9 | `test_f039_r9_combos_usan_empresa_sufijo` | texto: `obraLabel`, `recLabel` y la búsqueda manual contienen `empresaSufijo(`; `" · empresa "` no aparece en `app.js` |
| R10 | `test_f039_r10_app_js_sin_nombres` | texto: ni «Ruesma» ni «Porsan» en `app.js` |
| R11 | `test_f039_r11_candidatos_conciliar_con_nombre` | `GET /conciliacion` con candidato de empresa 28 pinta «Porsan» |
| R12 | `test_f039_r12_resto_de_campos_intacto` | claves de cada item = las de antes + `empresa_nombre`; suite de sv4 en verde |

Fase RED (rigor estándar): R1–R7 y R9 deben fallar antes del cambio (R9 por
el literal « · empresa »); R8, R10, R11 y R12 ya pasan hoy y son guardas de
regresión (R12 compara claves, así que su versión «+ `empresa_nombre`» sí
falla en RED). Traza en `progress/impl_F-039.md`. Mutación muestreada con
`python -m harness.mutacion --feature F-039`.

Validación de estáticos (`CONVENTIONS.md`): `node --check static/app.js`.

## 5. Riesgos

- **Caché del navegador**: tras desplegar, un `app.js` viejo con la API
  nueva pinta «empresa N» como hoy (no rompe); `asset_version` ya invalida
  el estático al reiniciar. Uno nuevo con API vieja usa el fallback R7.
- **Nada contra Sigrid ni BBDD**: no hay verificación manual obligatoria;
  basta comprobar en el portal (Ctrl+F5) la búsqueda manual de Conciliar.
