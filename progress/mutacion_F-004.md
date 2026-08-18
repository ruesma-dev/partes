<!-- progress/mutacion_F-004.md -->
# F-004 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-004` el 2026-08-18 15:39.

## Alcance

Origen del diff: **rama** (`9772ba49bbb820698f7b0a79b9a7eb60ee148097` .. `feature/F-004-congelar-aprobados`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/congelacion.py` | 170 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 255 |
| `services/partes-front/interface_adapters/web/app.py` | 56 |
| **Total** | **481** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 54 |
| Mutantes evaluados | 54 |
| Muertos | 49 |
| Supervivientes | 5 |
| Timeouts | 0 |
| Tiempo total | 642.2 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/infrastructure/database/parte_repository.py:173` [booleano]

- Original: `congelado: bool = False`
- Mutado:   `congelado: bool = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-front/infrastructure/database/parte_repository.py:517` [logico]

- Original: `"id": reg.id, "t": tipo, "h": reg.horas or 0.0,`
- Mutado:   `"id": reg.id, "t": tipo, "h": reg.horas and 0.0,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/partes-front/infrastructure/database/parte_repository.py:518` [logico]

- Original: `"p": reg.partida_cod or reg.partida or None,`
- Mutado:   `"p": reg.partida_cod and reg.partida or None,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/partes-front/infrastructure/database/parte_repository.py:518` [logico]

- Original: `"p": reg.partida_cod or reg.partida or None,`
- Mutado:   `"p": reg.partida_cod or reg.partida and None,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/partes-front/interface_adapters/web/app.py:929` [entero]

- Original: `congeladas = 0`
- Mutado:   `congeladas = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

