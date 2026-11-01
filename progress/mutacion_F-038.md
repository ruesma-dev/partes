<!-- progress/mutacion_F-038.md -->
# F-038 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-038` el 2026-10-24 13:37.

## Alcance

Origen del diff: **rama** (`09268570191989442d75b611357a26e028d27856` .. `feature/F-038-limite-filas-sigrid`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-api/config/settings.py` | 7 |
| `services/partes-api/infrastructure/sigrid/sigrid_lookup_client.py` | 13 |
| `services/partes-api/interface_adapters/api/app.py` | 1 |
| `services/partes-front/config/settings.py` | 8 |
| `services/partes-front/infrastructure/sigrid/sigrid_lookup_client.py` | 10 |
| `services/partes-front/interface_adapters/web/app.py` | 1 |
| `services/partes-persistencia/config/settings.py` | 8 |
| `services/partes-persistencia/infrastructure/sigrid/sigrid_api_client.py` | 6 |
| `services/partes-transfer/comprobar_asiento_analitico.py` | 2 |
| `services/partes-transfer/config/settings.py` | 8 |
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | 10 |
| `services/partes-transfer/interface_adapters/api/app.py` | 1 |
| `services/partes-transfer/main.py` | 1 |
| `services/partes-transfer/prueba_escritura_sigrid.py` | 6 |
| **Total** | **82** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 26 |
| Mutantes evaluados | 20 |
| Muertos | 17 |
| Supervivientes | 3 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 2820.9 s |
| SHA de HEAD medido | `45db3be90eb4267847ef880f2715f73bac6a2e1e` |
| Línea base (s) — `services/partes-api` | 12.3 |
| Línea base (s) — `services/partes-front` | 542.0 |
| Línea base (s) — `services/partes-persistencia` | 26.9 |
| Línea base (s) — `services/partes-transfer` | 19.8 |
| Media por mutante evaluado (s) | 141.0 |
| Timeout efectivo por mutante (s) | 1084 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 300 |
| Workers | 1 |
| Muestreo | sí — 20 de 26 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/config/settings.py:57` [entero]

- Original: `gt=0, le=200)`
- Mutado:   `gt=1, le=200)`

#### Análisis

> **Por qué sobrevivía:** hueco real de test, NO mutante equivalente. Los
> tests de R14 probaban valores rechazados (`0`, `-5`, `200.5`, `abc`) y el
> borde superior `200`, pero ningún valor válido en `(0, 1]`. Con `gt=1`, `0`
> y `-5` se siguen rechazando y `30`/`200` se siguen aceptando, así que la
> suite no distinguía `gt=0` de `gt=1`; en cambio `0.5` y `1` (timeouts que
> R14 admite) pasarían a tumbar el arranque.
> **Decisión:** test nuevo `test_f038_r14_timeout_por_debajo_de_1_vale`
> (parametrizado con `0.5` y `1`) en `services/partes-front/tests/test_f038_sigrid_limite.py`.
> **Verificado a mano (2026-10-24):** aplicado `gt=1` en el `settings.py`,
> `pytest tests/test_f038_sigrid_limite.py -k r14` da `2 failed, 5 passed`
> (`[0.5-0.5]` y `[1-1.0]`, `ValidationError ... greater_than`); revertido,
> `7 passed`. Árbol limpio tras revertir.

### 2. `services/partes-persistencia/config/settings.py:72` [entero]

- Original: `gt=0, le=200)`
- Mutado:   `gt=1, le=200)`

#### Análisis

> **Por qué sobrevivía:** hueco real de test, NO mutante equivalente. Los
> tests de R14 probaban valores rechazados (`0`, `-5`, `200.5`, `abc`) y el
> borde superior `200`, pero ningún valor válido en `(0, 1]`. Con `gt=1`, `0`
> y `-5` se siguen rechazando y `30`/`200` se siguen aceptando, así que la
> suite no distinguía `gt=0` de `gt=1`; en cambio `0.5` y `1` (timeouts que
> R14 admite) pasarían a tumbar el arranque.
> **Decisión:** test nuevo `test_f038_r14_timeout_por_debajo_de_1_vale`
> (parametrizado con `0.5` y `1`) en `services/partes-persistencia/tests/test_f038_sigrid_limite.py`.
> **Verificado a mano (2026-10-24):** aplicado `gt=1` en el `settings.py`,
> `pytest tests/test_f038_sigrid_limite.py -k r14` da `2 failed, 5 passed`
> (`[0.5-0.5]` y `[1-1.0]`, `ValidationError ... greater_than`); revertido,
> `7 passed`. Árbol limpio tras revertir.

### 3. `services/partes-transfer/config/settings.py:25` [entero]

- Original: `gt=0, le=200)`
- Mutado:   `gt=1, le=200)`

#### Análisis

> **Por qué sobrevivía:** hueco real de test, NO mutante equivalente. Los
> tests de R14 probaban valores rechazados (`0`, `-5`, `200.5`, `abc`) y el
> borde superior `200`, pero ningún valor válido en `(0, 1]`. Con `gt=1`, `0`
> y `-5` se siguen rechazando y `30`/`200` se siguen aceptando, así que la
> suite no distinguía `gt=0` de `gt=1`; en cambio `0.5` y `1` (timeouts que
> R14 admite) pasarían a tumbar el arranque.
> **Decisión:** test nuevo `test_f038_r14_timeout_por_debajo_de_1_vale`
> (parametrizado con `0.5` y `1`) en `services/partes-transfer/tests/test_f038_sigrid_limite.py`.
> **Verificado a mano (2026-10-24):** aplicado `gt=1` en el `settings.py`,
> `pytest tests/test_f038_sigrid_limite.py -k r14` da `2 failed, 5 passed`
> (`[0.5-0.5]` y `[1-1.0]`, `ValidationError ... greater_than`); revertido,
> `7 passed`. Árbol limpio tras revertir.

## Cierre del análisis (implementer, 2026-10-24)

- Los 3 supervivientes son el mismo hueco (límite inferior exclusivo de
  `sigrid_api_timeout_s`) repetido en sv3, sv4 y sv5. Quedan **muertos** por
  el test nuevo, verificado a mano mutante a mutante (ver cada análisis).
- El mismo test se añade en sv2 (`services/partes-api`) por coherencia: su
  mutante gemelo (`services/partes-api/config/settings.py:98`) no entró en el
  muestreo (20 de 26), pero se verificó igual a mano: `2 failed, 5 passed`
  con `gt=1`, `7 passed` sin él.
- **NO se relanza la campaña** de mutación: el cambio solo añade tests, el
  código de producción medido (HEAD `45db3be`) no cambia y la verificación
  manual cubre exactamente los mutantes supervivientes. Las cifras de los
  totales de arriba son las de la campaña original (17 muertos / 3
  supervivientes); con los tests nuevos los 3 quedan muertos (20/20).
