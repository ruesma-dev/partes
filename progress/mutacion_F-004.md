<!-- progress/mutacion_F-004.md -->
# F-004 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-004` el 2026-08-18 15:25.

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
| Muertos | 36 |
| Supervivientes | 5 |
| Timeouts | 13 |
| Tiempo total | 358.2 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/interface_adapters/web/app.py:929` [entero]

- Original: `congeladas = 0`
- Mutado:   `congeladas = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-front/interface_adapters/web/app.py:1905` [comparacion]

- Original: `{"ok": n > 0, "partes": n, "congelados": congelados})`
- Mutado:   `{"ok": n >= 0, "partes": n, "congelados": congelados})`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/partes-front/interface_adapters/web/app.py:1905` [entero]

- Original: `{"ok": n > 0, "partes": n, "congelados": congelados})`
- Mutado:   `{"ok": n > 1, "partes": n, "congelados": congelados})`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/partes-front/interface_adapters/web/app.py:1913` [comparacion]

- Original: `{"ok": n > 0, "lineas": n, "congelados": congelados})`
- Mutado:   `{"ok": n >= 0, "lineas": n, "congelados": congelados})`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/partes-front/interface_adapters/web/app.py:1913` [entero]

- Original: `{"ok": n > 0, "lineas": n, "congelados": congelados})`
- Mutado:   `{"ok": n > 1, "lineas": n, "congelados": congelados})`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

## Timeouts

- `services/partes-front/infrastructure/database/parte_repository.py:173` services/partes-front/infrastructure/database/parte_repository.py:173 [booleano] congelado: bool = False -> congelado: bool = True
- `services/partes-front/infrastructure/database/parte_repository.py:517` services/partes-front/infrastructure/database/parte_repository.py:517 [logico] "id": reg.id, "t": tipo, "h": reg.horas or 0.0, -> "id": reg.id, "t": tipo, "h": reg.horas and 0.0,
- `services/partes-front/infrastructure/database/parte_repository.py:518` services/partes-front/infrastructure/database/parte_repository.py:518 [logico] "p": reg.partida_cod or reg.partida or None, -> "p": reg.partida_cod and reg.partida or None,
- `services/partes-front/infrastructure/database/parte_repository.py:518` services/partes-front/infrastructure/database/parte_repository.py:518 [logico] "p": reg.partida_cod or reg.partida or None, -> "p": reg.partida_cod or reg.partida and None,
- `services/partes-front/infrastructure/database/parte_repository.py:1893` services/partes-front/infrastructure/database/parte_repository.py:1893 [aritmetico] omitidos += 1 -> omitidos -= 1
- `services/partes-front/infrastructure/database/parte_repository.py:1893` services/partes-front/infrastructure/database/parte_repository.py:1893 [entero] omitidos += 1 -> omitidos += 2
- `services/partes-front/infrastructure/database/parte_repository.py:1901` services/partes-front/infrastructure/database/parte_repository.py:1901 [aritmetico] omitidos += 1 -> omitidos -= 1
- `services/partes-front/infrastructure/database/parte_repository.py:1901` services/partes-front/infrastructure/database/parte_repository.py:1901 [entero] omitidos += 1 -> omitidos += 2
- `services/partes-front/infrastructure/database/parte_repository.py:1941` services/partes-front/infrastructure/database/parte_repository.py:1941 [entero] return 0, 0 -> return 1, 0
- `services/partes-front/infrastructure/database/parte_repository.py:1941` services/partes-front/infrastructure/database/parte_repository.py:1941 [entero] return 0, 0 -> return 0, 1
- `services/partes-front/infrastructure/database/parte_repository.py:2040` services/partes-front/infrastructure/database/parte_repository.py:2040 [entero] return 0, congeladas -> return 1, congeladas
- `services/partes-front/infrastructure/database/parte_repository.py:2171` services/partes-front/infrastructure/database/parte_repository.py:2171 [booleano] return False -> return True
- `services/partes-front/infrastructure/database/parte_repository.py:2271` services/partes-front/infrastructure/database/parte_repository.py:2271 [entero] congelados = 0 -> congelados = 1

