<!-- progress/mutacion_F-063.md -->
# F-063 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-063` el 2026-10-26 08:03.

## Alcance

Origen del diff: **rama** (`bbc3172722b680f78a4cbd15a0980ef121ba1596` .. `feature/F-063-consulta-obra-rapida`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-api/application/services/obra_sigrid.py` | 1 |
| `services/partes-api/application/services/relectura_cabecera.py` | 4 |
| `services/partes-api/domain/models/clave_obra.py` | 35 |
| `services/partes-api/infrastructure/sigrid/sigrid_lookup_client.py` | 81 |
| **Total** | **121** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 23 |
| Mutantes evaluados | 20 |
| Muertos | 16 |
| Supervivientes | 4 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 191.2 s |
| SHA de HEAD medido | `a00a501ff509eee8b05894b3a8277729f2d04c2c` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-063_bx5g_vbr/wk_0/services/partes-api` | 25.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-063_bx5g_vbr/wk_1/services/partes-api` | 26.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-063_bx5g_vbr/wk_2/services/partes-api` | 25.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-063_bx5g_vbr/wk_3/services/partes-api` | 26.1 |
| Media por mutante evaluado (s) | 9.6 |
| Timeout efectivo por mutante (s) | 300 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 300 |
| Workers | 4 |
| Muestreo | sí — 20 de 23 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-api/infrastructure/sigrid/sigrid_lookup_client.py:70` [entero]

- Original: `_RANGO_VARIANTES = range(0x00A0, 0x0180)`
- Mutado:   `_RANGO_VARIANTES = range(161, 0x0180)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-api/infrastructure/sigrid/sigrid_lookup_client.py:70` [entero]

- Original: `_RANGO_VARIANTES = range(0x00A0, 0x0180)`
- Mutado:   `_RANGO_VARIANTES = range(0x00A0, 385)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/partes-api/infrastructure/sigrid/sigrid_lookup_client.py:86` [logico]

- Original: `if len(base) == 1 and base.isalnum() and caracter.isalnum():`
- Mutado:   `if len(base) == 1 or base.isalnum() and caracter.isalnum():`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/partes-api/infrastructure/sigrid/sigrid_lookup_client.py:86` [logico]

- Original: `if len(base) == 1 and base.isalnum() and caracter.isalnum():`
- Mutado:   `if len(base) == 1 and base.isalnum() or caracter.isalnum():`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

