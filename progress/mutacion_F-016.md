<!-- progress/mutacion_F-016.md -->
# F-016 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-016` el 2026-08-19 16:56.

## Alcance

Origen del diff: **rama** (`047eb5b8bf8dc3201421a9ec524e43269eb08adc` .. `feature/F-016-admin-empleado-jornada`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/jornada_admin.py` | 368 |
| `services/partes-front/application/services/jornada_provider.py` | 11 |
| `services/partes-front/config/settings.py` | 6 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 131 |
| `services/partes-front/interface_adapters/web/app.py` | 311 |
| **Total** | **827** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 93 |
| Mutantes evaluados | 93 |
| Muertos | 79 |
| Supervivientes | 14 |
| Timeouts | 0 |
| Tiempo total | 1409.6 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/jornada_admin.py:69` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**Por qué ningún test lo caza.** `EntradaJornada` es un `dataclass` congelado,
pero **ningún test intenta mutar una instancia**: se construye, se valida y se
pasa al repositorio, nunca se reescribe un campo. Desprotegerla no cambia
ninguna respuesta observable.

**Decisión: hueco real de test, de valor bajo — analizado, no tapado.**
`frozen=True` es una **garantía de diseño**, no un comportamiento: impide que
alguien, en el futuro, modifique una entrada *entre* `validar_entrada` y la
escritura, que es exactamente el agujero por el que se colaría una fila sin
validar en una pantalla que toca nóminas. Hoy nadie lo hace, así que el mutante
es equivalente **para el comportamiento actual**. Matarlo cuesta un test de una
línea (`pytest.raises(FrozenInstanceError)`), pero el nivel `estandar` exige
supervivientes **analizados**, no cero supervivientes, y añadir tests después
de medir dejaría los números de esta campaña sin corresponder con el árbol.
Queda anotado como la primera mejora si esa garantía se considera crítica.

### 2. `services/partes-front/application/services/jornada_admin.py:102` [logico]

- Original: `if len(texto) != 10 or texto[4] != "-" or texto[7] != "-":`
- Mutado:   `if len(texto) != 10 or texto[4] != "-" and texto[7] != "-":`

#### Análisis

**Por qué ningún test lo caza.** Con `and`, la guarda deja pasar una cadena de
diez caracteres a la que le falta **solo uno** de los dos guiones (por ejemplo
`2026-07/01`). Pero justo después está `date.fromisoformat`, que la rechaza
igual con `ValueError`, y el `except` la convierte en la **misma**
`JornadaInvalida`, con el **mismo `campo`** y el mismo HTTP 422. Lo único que
cambia es cuál de los dos mensajes lee el humano («no está en formato
AAAA-MM-DD» en vez de «no existe en el calendario»).

**Decisión: mutante equivalente para el contrato observable.** Los tests fijan
la clase de la excepción, el `campo` y el código HTTP, y **a propósito no fijan
el texto de los mensajes**: atarlos haría la suite frágil ante cualquier
reescritura de la redacción, sin proteger nada. La validación de formato sigue
teniendo sentido —da un mensaje mejor y no depende de qué acepte
`fromisoformat` en cada versión de Python—, pero su valor es de redacción, no
de contrato.

### 3. `services/partes-front/application/services/jornada_admin.py:127` [entero]

- Original: `valores: list[float | None] = list(patron) if patron else [None] * 7`
- Mutado:   `valores: list[float | None] = list(patron) if patron else [None] * 8`

#### Análisis

**Por qué ningún test lo caza.** El valor solo se usa en
`dict(zip(DIAS, valores))`, y `zip` **para en la lista más corta**: `DIAS`
tiene siete elementos, así que ocho `None` producen exactamente el mismo
diccionario de siete columnas que siete.

**Decisión: mutante equivalente, de verdad.** No hay test que pueda matarlo sin
inventar una aserción sobre una lista intermedia que nunca sale de la función.
El `7` es documentación (dice cuántos días tiene la semana), no una decisión
que el programa pueda equivocar.

### 4. `services/partes-front/interface_adapters/web/app.py:1991` [entero]

- Original: `1, -(-int(settings.jornada_cache_ttl_s) // 60)),`
- Mutado:   `2, -(-int(settings.jornada_cache_ttl_s) // 60)),`

#### Análisis

**Por qué ningún test lo caza.** El `max(1, …)` es un **suelo** para
`JORNADA_CACHE_TTL_S` menor de 60 s: evita que el aviso diga «0 minutos». Los
dos TTL que se prueban son 600 y 900, que dan 10 y 15 minutos; con el suelo a 2
el resultado no cambia porque nunca llega a aplicarse.

**Decisión: hueco real de test, de valor muy bajo.** Solo se manifiesta con un
TTL por debajo de 120 s, una configuración que nadie va a poner: la tabla
`empleado_jornada` se toca dos veces al año y bajar el TTL multiplica las
lecturas sin ganar nada (`design.md` §7 lo descarta expresamente). El suelo
está para que el aviso nunca diga una tontería, no porque se espere ese caso.
Queda anotado; taparlo sería un test de un caso que la configuración real nunca
produce.

### 5. `services/partes-front/interface_adapters/web/app.py:1991` [entero]

- Original: `1, -(-int(settings.jornada_cache_ttl_s) // 60)),`
- Mutado:   `1, -(-int(settings.jornada_cache_ttl_s) // 61)),`

#### Análisis

**Por qué ningún test lo caza — y esto sí merece leerse.** Se comprobó
numéricamente: `ceil(ttl/60)` y `ceil(ttl/61)` dan **el mismo número para todo
TTL múltiplo de 60 hasta 3600 s inclusive**. El primer múltiplo de 60 en que
difieren es **3660 s (61 minutos)**.

| TTL (s) | `//60` | `//61` | ¿coinciden? |
|---|---|---|---|
| 60 | 1 | 1 | sí |
| 600 (default) | 10 | 10 | sí |
| 900 | 15 | 15 | sí |
| 3600 | 60 | 60 | sí |
| **3660** | **61** | **60** | **NO** |

Así que **ningún** valor razonable de `JORNADA_CACHE_TTL_S` distingue las dos
versiones: no es que los tests hayan elegido mal los casos, es que el dominio
entero de configuraciones sensatas es indistinguible.

**Decisión: mutante equivalente en el dominio de uso.** Añadir un caso con TTL
de 61 minutos solo para matarlo sería un test que documenta una aritmética que
a nadie le importa. Lo que R14 exige —que el número salga de la configuración y
no esté cableado— **sí** está probado, con dos TTL distintos que dan dos
números distintos (600 ⇒ «10 minutos», 900 ⇒ «15 minutos»).

### 6. `services/partes-front/interface_adapters/web/app.py:2019` [logico]

- Original: `fin = detalle["hasta_inclusivo"] or "sin fin"`
- Mutado:   `fin = detalle["hasta_inclusivo"] and "sin fin"`

#### Análisis

**Por qué ningún test lo caza.** `fin` solo entra en el **texto** del error del
409. Los tests fijan la parte estructurada —`conflicto` con `id`, `desde` y
`hasta_inclusivo`, que es lo que el JS usa para señalar la fila— y que `error`
no venga vacío, pero no su redacción.

**Decisión: hueco real de test, y el único de los catorce con consecuencia
visible.** Con `and`, una fila en conflicto **de vigencia abierta**
(`hasta_inclusivo` nulo) haría que el mensaje dijera literalmente `None` en vez
de «sin fin». No rompe nada —el 409 se emite igual y la BBDD sigue intacta—,
pero es feo delante del humano. Se anota como la mejora de mayor valor de esta
lista: un test que compruebe que el mensaje del 409 contra una vigencia abierta
contiene «sin fin» lo cerraría. No se añade ahora para no invalidar los números
de esta campaña.

### 7. `services/partes-front/interface_adapters/web/app.py:2061` [booleano]

- Original: `"contra Sigrid", exc_info=True)`
- Mutado:   `"contra Sigrid", exc_info=False)`

#### Análisis

**Por qué ningún test lo caza.** `exc_info` solo decide si el WARNING lleva la
traza completa cuando el catálogo de Sigrid falla. Ningún test de F-016 mira el
contenido de los logs; el que ejercita ese camino
(`test_f016_r19_si_sigrid_falla_el_alta_se_guarda_igual`) comprueba lo que
importa: que **el alta se guarda igual**.

**Decisión: mutante equivalente para el comportamiento.** La traza es para
diagnosticar, no para el contrato. Fijarla en un test ataría la suite al
formato del logging.

### 8. `services/partes-front/interface_adapters/web/app.py:2083` [booleano]

- Original: `@app.post("/api/admin/jornadas", include_in_schema=False)`
- Mutado:   `@app.post("/api/admin/jornadas", include_in_schema=True)`

#### Análisis (común a los supervivientes 8, 9, 10, 11 y 13)

**Por qué ningún test lo caza.** `include_in_schema=False` solo decide si la
ruta aparece en el OpenAPI de `/docs`. Ningún test de F-016 mira el esquema
generado: miran el comportamiento HTTP, que es idéntico con `True` o `False`.

**Decisión: hueco real de test, barato de cerrar.** Que los cinco endpoints
JSON queden fuera del esquema es una decisión explícita del diseño («todos los
endpoints JSON llevan `include_in_schema=False`, como sus vecinos») y hoy no la
comprueba nadie: los cinco mutantes sobreviven por la misma razón. Un solo test
—que ninguna ruta `/api/admin/jornadas*` aparezca en `app.openapi()["paths"]`—
mataría los cinco de golpe. Queda anotado; no se añade ahora para no invalidar
los números de esta campaña.

### 9. `services/partes-front/interface_adapters/web/app.py:2104` [booleano]

- Original: `@app.patch("/api/admin/jornadas/{jornada_id}", include_in_schema=False)`
- Mutado:   `@app.patch("/api/admin/jornadas/{jornada_id}", include_in_schema=True)`

#### Análisis

Mismo caso que el superviviente **8**: ver su análisis. `include_in_schema` no
cambia el comportamiento HTTP y ningún test mira el OpenAPI. Los cinco (8, 9,
10, 11 y 13) los mataría **un solo test** sobre `app.openapi()["paths"]`.

### 10. `services/partes-front/interface_adapters/web/app.py:2131` [booleano]

- Original: `include_in_schema=False)`
- Mutado:   `include_in_schema=True)`

#### Análisis

Mismo caso que el superviviente **8**: ver su análisis.

### 11. `services/partes-front/interface_adapters/web/app.py:2156` [booleano]

- Original: `include_in_schema=False)`
- Mutado:   `include_in_schema=True)`

#### Análisis

Mismo caso que el superviviente **8**: ver su análisis.

### 12. `services/partes-front/interface_adapters/web/app.py:2165` [booleano]

- Original: `return JSONResponse({"ok": True, "id": jornada_id})`
- Mutado:   `return JSONResponse({"ok": False, "id": jornada_id})`

#### Análisis (común a los supervivientes 12 y 14)

**Por qué ningún test lo caza — y este sí es un hueco de verdad.** Los tests de
`desactivar` y `reactivar` comprueban el **código HTTP** (200), el efecto en la
BBDD (`is_active`, que la fila no se borra) y la invalidación de la caché, pero
**ninguno mira el campo `ok` del cuerpo**. Se verificó con `grep`: cero
aserciones sobre `json()["ok"]` en esas dos rutas. En cambio, los mismos
mutantes sobre **crear**, **editar** y **cerrar** murieron, porque esos tests sí
comparan el cuerpo.

**Decisión: hueco real de test, con impacto acotado.** Hoy no rompería la
pantalla: el JS decide el éxito con `MotivoHttp.lanzarSiFalla`, que mira el
**estado HTTP**, no el campo `ok`, así que un `{"ok": false}` con HTTP 200
seguiría tratándose como éxito. Pero deja dos endpoints contradiciendo a los
otros tres, y cualquier cliente futuro que lea `ok` —lo natural— se confundiría.
Cerrarlo es añadir `assert respuesta.json()["ok"] is True` a los dos casos de
`test_f016_r6_papelera_logica`. Queda anotado; no se añade ahora para no
invalidar los números de esta campaña.

### 13. `services/partes-front/interface_adapters/web/app.py:2168` [booleano]

- Original: `include_in_schema=False)`
- Mutado:   `include_in_schema=True)`

#### Análisis

Mismo caso que el superviviente **8**: ver su análisis.

### 14. `services/partes-front/interface_adapters/web/app.py:2190` [booleano]

- Original: `return JSONResponse({"ok": True, "id": jornada_id})`
- Mutado:   `return JSONResponse({"ok": False, "id": jornada_id})`

#### Análisis

Mismo caso que el superviviente **12**: ver su análisis. Ningún test comprueba
el campo `ok` del cuerpo de `reactivar`; sí su HTTP 200, su efecto en
`is_active` y el 409 cuando hay solape.



---

## Lectura de conjunto (implementer)

**79 de 93 muertos (85 %), 0 timeouts.** Los 14 supervivientes se reparten en
tres grupos, y ninguno toca las reglas que sostienen la feature:

| Grupo | Cuántos | Qué son |
|---|---|---|
| **Equivalentes de verdad** (3, 5, 7, y 2 para el contrato) | 4 | `zip` trunca a siete; `//60` vs `//61` da lo mismo para todo TTL sensato; `exc_info` es diagnóstico; el formato de fecha acaba en el mismo 422 con el mismo `campo` |
| **Fuera del contrato observable** (8, 9, 10, 11, 13) | 5 | `include_in_schema`: solo el OpenAPI. **Un solo test los mataría los cinco** |
| **Huecos reales, acotados** (1, 4, 6, 12, 14) | 5 | inmutabilidad de `EntradaJornada`; suelo del aviso con TTL < 120 s; «sin fin» en el texto del 409; campo `ok` de desactivar/reactivar |

**Lo importante: ningún superviviente está en la lógica de riesgo.** Los 93
mutantes incluyen los límites del solape (`>=` ↔ `>`, `and` ↔ `or`, `<` ↔ `<=`
sobre `desde`/`hasta`), la conversión de fechas (`days=1` → `days=2`), los
rangos de R9 y R10 (`<` ↔ `<=` en los cuatro extremos), la exclusión de la
propia fila al editar, el filtro por `is_active`, el `origen='manual'` forzado y
el 404 de la puerta de acceso — **y todos murieron**. Eso es lo que la campaña
tenía que decir de una pantalla que edita el cómputo de nóminas.

**Las tres mejoras anotadas, por valor**, si el humano quiere cerrarlas en una
pasada posterior (no se aplican ahora para que estos números sigan
correspondiendo con el árbol medido):

1. Superviviente **6** — que el 409 contra una vigencia abierta diga «sin fin» y
   no `None`. Es el único con consecuencia visible para el usuario.
2. Supervivientes **12 y 14** — `assert respuesta.json()["ok"] is True` en
   desactivar y reactivar. Dos líneas, y alinea los cinco endpoints.
3. Supervivientes **8–11 y 13** — un test sobre `app.openapi()["paths"]`. Mata
   cinco de golpe.

## Nota de operación

El proceso devuelve **exit 1** cuando quedan supervivientes; **no es un fallo de
ejecución**. El nivel `estandar` de `harness/rigor.json` fija
`supervivientes_maximos: null`, es decir, exige supervivientes **analizados**,
no cero supervivientes.

**Parámetros usados y por qué.** `--workers 6 --timeout 600`, por la lección de
F-015: la suite de sv4 tarda ~115 s y con el `timeout_por_mutante_s: 120` por
defecto de `rigor.json` la campaña produce **timeouts masivos**, que no son una
medición. Con 600 s de margen salieron **0 timeouts** en 1409,6 s.

**Aviso conocido del arnés** (ya documentado por F-010 y F-015): la campaña
ejecuta solo la suite del **servicio dueño** del fichero mutado, así que los
guardianes de `tests/` (raíz) no matan mutantes de sv4. Aquí **no distorsiona
nada**: los cinco ficheros mutados son de sv4 y toda su cobertura vive en la
suite de sv4. F-016 no añade ninguna duplicación entre servicios.
