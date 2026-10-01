<!-- progress/mutacion_F-022.md -->
# F-022 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-022` el 2026-10-01 20:42.

## Alcance

Origen del diff: **rama** (`a6c342741a5d14fd694f2c15119f69e100e65162` .. `feature/F-022-aprobar-seleccionadas`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/reparto_obras.py` | 255 |
| `services/partes-front/config/settings.py` | 4 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 57 |
| `services/partes-front/interface_adapters/web/app.py` | 278 |
| **Total** | **594** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 143 |
| Mutantes evaluados | 143 |
| Muertos | 140 |
| Supervivientes | 3 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 4506.2 s |
| SHA de HEAD medido | `2524bf9bcd540bcf607f6ee71bed0a233009a80b` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-022_hlhpdm9c/wk_0/services/partes-front` | 301.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-022_hlhpdm9c/wk_1/services/partes-front` | 305.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-022_hlhpdm9c/wk_2/services/partes-front` | 304.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-022_hlhpdm9c/wk_3/services/partes-front` | 303.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-022_hlhpdm9c/wk_4/services/partes-front` | 301.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-022_hlhpdm9c/wk_5/services/partes-front` | 303.8 |
| Media por mutante evaluado (s) | 31.5 |
| Timeout efectivo por mutante (s) | 600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 600 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/reparto_obras.py:84` [entero]

- Original: `lineas += t.get("lineas") or 0`
- Mutado:   `lineas += t.get("lineas") or 1`

#### Análisis

> Por qué ningún test lo caza: todos los `totales` de los tests traían
> `lineas`; nadie sumaba uno sin esa clave.
> Decisión: **test nuevo**. `test_f022_r25_totales_sumados_redondean_a_dos_decimales`
> ahora exige `lineas == 0`, `incidencias == 0` y `por_estado == {}` al sumar
> totales sin esas claves. Aplicado el mutante a mano: `1 failed`.

### 2. `services/partes-front/infrastructure/database/parte_repository.py:509` [entero]

- Original: `"fecha_int": int(reg.fecha_int or 0),`
- Mutado:   `"fecha_int": int(reg.fecha_int or 1),`

#### Análisis

> Por qué ningún test lo caza: todas las líneas excluidas de los tests tenían
> fecha; el `or 0` (línea sin `fecha_int`) no se ejercitaba.
> Decisión: **test nuevo** `test_f022_r26_repo_excluida_sin_fecha_va_con_cero`
> (excluida sin fecha ⇒ `fecha_int == 0`, igual que las que viajan). Aplicado
> el mutante a mano: `1 failed`.

### 3. `services/partes-front/interface_adapters/web/app.py:1844` [booleano]

- Original: `{"ok": False, "error": "registro_ids no validos"},`
- Mutado:   `{"ok": True, "error": "registro_ids no validos"},`

#### Análisis

> Por qué ningún test lo caza: el test de ids no numéricos miraba el código
> 422 y el texto del error, no el campo `ok` del cuerpo.
> Decisión: **test nuevo**: `test_f022_r12_ambito_ids_no_numericos_son_422`
> exige además `ok is False` (9 parametrizaciones). Aplicado el mutante a
> mano: `9 failed`.


## Cierre del implementer

Campaña completa (`--workers 6 --timeout 600`) sobre HEAD `2524bf9`: 143
mutantes, 140 muertos, 3 supervivientes, 0 timeouts. Los 3 supervivientes
tienen test nuevo (comprobado aplicando cada mutante a mano: su test FALLA);
**0 supervivientes sin resolver**. Los commits posteriores a `2524bf9` solo
tocan JS (`e0951b5`), tests y documentación: ninguna línea Python de
producción cambia después de la campaña.
