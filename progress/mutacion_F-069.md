<!-- progress/mutacion_F-069.md -->
# F-069 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-069` el 2026-11-12 13:00.

## Alcance

Origen del diff: **rama** (`0a919416a76964c98c306df542bc6738cee2aa7f` .. `feature/F-069-extras-ids-estables`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/infrastructure/database/parte_repository.py` | 17 |
| `services/partes-front/interface_adapters/web/app.py` | 13 |
| `services/partes-persistencia/application/services/pareja_extra.py` | 101 |
| `services/partes-persistencia/application/services/recurso_conciliador.py` | 26 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 309 |
| **Total** | **466** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 72 |
| Mutantes evaluados | 72 |
| Muertos | 61 |
| Supervivientes | 11 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 3806.6 s |
| SHA de HEAD medido | `bae636389667a825aa8f7593415ec3dee01cc2f6` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_bssortu3/wk_0/services/partes-front` | 1051.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_bssortu3/wk_0/services/partes-persistencia` | 65.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_bssortu3/wk_1/services/partes-front` | 1047.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_bssortu3/wk_1/services/partes-persistencia` | 66.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_bssortu3/wk_2/services/partes-front` | 1049.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_bssortu3/wk_2/services/partes-persistencia` | 68.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_bssortu3/wk_3/services/partes-front` | 1048.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_bssortu3/wk_3/services/partes-persistencia` | 69.7 |
| Media por mutante evaluado (s) | 52.9 |
| Timeout efectivo por mutante (s) | 2103 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 600 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-persistencia/application/services/pareja_extra.py:166` [entero]

- Original: `return None if valor is None else round(float(valor), 6)`
- Mutado:   `return None if valor is None else round(float(valor), 7)`

#### Análisis (implementer)

> Por qué ningún test lo caza: La huella solo se comparaba con diferencias de 1e-9 (iguales) y 1e-5 (distintas); una de 4e-7 separa 6 de 7 decimales.
> Decisión: test nuevo: `tests/test_f069_mutacion.py`::test_f069_r13_huella_ignora_el_septimo_decimal.

### 2. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:60` [entero]

- Original: `LOTE_IN = 1000`
- Mutado:   `LOTE_IN = 1001`

#### Análisis (implementer)

> Por qué ningún test lo caza: Ningún test pasaba más de 1000 ids a `escribir_pasada`: con 1000 o 1001 por lote, todo cabía en uno.
> Decisión: test nuevo: `tests/test_f069_mutacion.py`::test_f069_r8_ids_de_los_casados_en_lotes_de_1000 (1001 casados ⇒ lotes de 1000 y 1).

### 3. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:87` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (implementer)

> Por qué ningún test lo caza: Nadie intentaba modificar un `ResumenEscritura`.
> Decisión: test nuevo: `tests/test_f069_mutacion.py`::test_f069_r6_resumen_inmutable.

### 4. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:98` [entero]

- Original: `actualizados: int = 0`
- Mutado:   `actualizados: int = 1`

#### Análisis (implementer)

> Por qué ningún test lo caza: Ningún test construía `ResumenEscritura()` sin argumentos: la escritura real rellena todos los campos. El doble `RepositorioFake.escribir_pasada` sí cuenta con los ceros (solo pasa `actualizados`, `aplicados` y `nuevas`).
> Decisión: test nuevo: `tests/test_f069_mutacion.py`::test_f069_r6_resumen_por_defecto_todo_a_cero.

### 5. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:99` [entero]

- Original: `aplicados: int = 0`
- Mutado:   `aplicados: int = 1`

#### Análisis (implementer)

> Por qué ningún test lo caza: Ningún test construía `ResumenEscritura()` sin argumentos: la escritura real rellena todos los campos. El doble `RepositorioFake.escribir_pasada` sí cuenta con los ceros (solo pasa `actualizados`, `aplicados` y `nuevas`).
> Decisión: test nuevo: `tests/test_f069_mutacion.py`::test_f069_r6_resumen_por_defecto_todo_a_cero.

### 6. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:100` [entero]

- Original: `nuevas: int = 0`
- Mutado:   `nuevas: int = 1`

#### Análisis (implementer)

> Por qué ningún test lo caza: Ningún test construía `ResumenEscritura()` sin argumentos: la escritura real rellena todos los campos. El doble `RepositorioFake.escribir_pasada` sí cuenta con los ceros (solo pasa `actualizados`, `aplicados` y `nuevas`).
> Decisión: test nuevo: `tests/test_f069_mutacion.py`::test_f069_r6_resumen_por_defecto_todo_a_cero.

### 7. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:101` [entero]

- Original: `reutilizadas: int = 0`
- Mutado:   `reutilizadas: int = 1`

#### Análisis (implementer)

> Por qué ningún test lo caza: Ningún test construía `ResumenEscritura()` sin argumentos: la escritura real rellena todos los campos. El doble `RepositorioFake.escribir_pasada` sí cuenta con los ceros (solo pasa `actualizados`, `aplicados` y `nuevas`).
> Decisión: test nuevo: `tests/test_f069_mutacion.py`::test_f069_r6_resumen_por_defecto_todo_a_cero.

### 8. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:102` [entero]

- Original: `borradas: int = 0`
- Mutado:   `borradas: int = 1`

#### Análisis (implementer)

> Por qué ningún test lo caza: Ningún test construía `ResumenEscritura()` sin argumentos: la escritura real rellena todos los campos. El doble `RepositorioFake.escribir_pasada` sí cuenta con los ceros (solo pasa `actualizados`, `aplicados` y `nuevas`).
> Decisión: test nuevo: `tests/test_f069_mutacion.py`::test_f069_r6_resumen_por_defecto_todo_a_cero.

### 9. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:103` [entero]

- Original: `parejas_cambiadas: int = 0`
- Mutado:   `parejas_cambiadas: int = 1`

#### Análisis (implementer)

> Por qué ningún test lo caza: Ningún test construía `ResumenEscritura()` sin argumentos: la escritura real rellena todos los campos. El doble `RepositorioFake.escribir_pasada` sí cuenta con los ceros (solo pasa `actualizados`, `aplicados` y `nuevas`).
> Decisión: test nuevo: `tests/test_f069_mutacion.py`::test_f069_r6_resumen_por_defecto_todo_a_cero.

### 10. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:445` [booleano]

- Original: `for fila, pareja in zip(vista, quedan, strict=True):`
- Mutado:   `for fila, pareja in zip(vista, quedan, strict=False):`

#### Análisis (implementer)

> Por qué ningún test lo caza: Mutante **equivalente**. `vista` sale de `vista_revertida(crudas, plan)`, que quita exactamente las filas de `plan.borrar` y conserva el orden; `quedan` quita de `parejas` (una por fila cruda, en el mismo orden) esas mismas ids. Las dos listas tienen siempre la misma longitud y el `strict=True` es solo defensivo: con `False` el resultado es idéntico para toda entrada que el código puede producir.
> Decisión: mutante equivalente justificado (sin test: no hay entrada alcanzable que lo distinga).

### 11. `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py:644` [comparacion]

- Original: `pg = session.get_bind().dialect.name == "postgresql"`
- Mutado:   `pg = session.get_bind().dialect.name != "postgresql"`

#### Análisis (implementer)

> Por qué ningún test lo caza: En SQLite, `with_for_update` no se compila (el dialecto lo ignora), así que mutar la condición no cambia nada en la suite. Solo lo veía el test M1 en PostgreSQL, que se salta sin `F069_PG_URL`.
> Decisión: test nuevo: `tests/test_f069_mutacion.py`::test_f069_r15_for_update_solo_en_postgresql (sesión falsa con dialecto `postgresql`/`sqlite`: la sentencia lleva `FOR UPDATE OF parte_registros` solo en el primero).


## Verificación de los tests nuevos (implementer, 2026-11-12)

La campaña no se relanza. Cada mutante cazado se aplicó a mano, uno a uno, y se ejecutó `python -m pytest tests/test_f069_mutacion.py -q` (desde `services/partes-persistencia`): los 10 dieron **MUERTO** y el fichero se restauró tras cada uno. Resultado: 72 mutantes, 71 muertos (61 en la campaña y 10 con test nuevo) y 1 equivalente justificado (n.º 10).
