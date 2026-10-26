<!-- progress/mutacion_F-058.md -->
# F-058 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-058` el 2026-10-25 13:14.

## Alcance

Origen del diff: **rama** (`9b1a7e312985feb547b8abf4cab5595a1944e79b` .. `feature/F-058-relectura-cabecera-gemini`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-api/application/pipelines/extract_parte_pipeline.py` | 149 |
| `services/partes-api/application/services/obra_sigrid.py` | 84 |
| `services/partes-api/application/services/parte_extraction_service.py` | 9 |
| `services/partes-api/application/services/relectura_cabecera.py` | 126 |
| `services/partes-api/config/settings.py` | 75 |
| `services/partes-api/domain/ports/existencia_obra_port.py` | 13 |
| `services/partes-api/infrastructure/sigrid/sigrid_lookup_client.py` | 56 |
| `services/partes-api/interface_adapters/api/app.py` | 40 |
| `services/partes-api/main_worker.py` | 8 |
| **Total** | **560** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 63 |
| Mutantes evaluados | 20 |
| Muertos | 19 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 242.9 s |
| SHA de HEAD medido | `da0317c149bcdc4333c665bb8a212e318c7f1548` |
| Línea base (s) — `services/partes-api` | 18.8 |
| Media por mutante evaluado (s) | 12.1 |
| Timeout efectivo por mutante (s) | 300 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 300 |
| Workers | 1 |
| Muestreo | sí — 20 de 63 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-api/config/settings.py:100` [entero]

- Original: `5.0, gt=0, alias="OBRA_EXISTE_TIMEOUT_S"`
- Mutado:   `5.0, gt=1, alias="OBRA_EXISTE_TIMEOUT_S"`

#### Análisis (implementer, 2026-10-25)

> Por qué ningún test lo caza: los tests de R24 solo probaban el valor por
> defecto (5.0), uno leído del entorno (2.5) y valores no positivos (0, -1,
> -0.5) que deben fallar. Con `gt=1` todos dan lo mismo: ninguno cae en el
> intervalo (0, 1], que es justo donde `gt=0` y `gt=1` difieren. Es el mismo
> hueco que tuvo F-038. **Hueco real, no equivalente**: con `gt=1` un
> `OBRA_EXISTE_TIMEOUT_S=0.5` —válido según la spec («> 0»)— impediría
> arrancar sv2.
>
> Decisión: **test nuevo**,
> `test_f058_r24_tope_de_la_consulta_positivo_menor_o_igual_a_1_se_acepta`
> en `services/partes-api/tests/test_f058_settings_wiring.py`,
> parametrizado con `0.5` y `1`: ambos deben aceptarse y leerse tal cual.
>
> Verificación a mano: mutante aplicado con `sed` en la línea 100, suite
> ejecutada y revertido con `git checkout -- config/settings.py` (árbol
> limpio después, solo queda el test nuevo):
>
> ```
> $ cd services/partes-api && python -m pytest tests/test_f058_settings_wiring.py -q -k "tope"
> FAILED tests/test_f058_settings_wiring.py::test_f058_r24_tope_de_la_consulta_positivo_menor_o_igual_a_1_se_acepta[0.5]
> FAILED tests/test_f058_settings_wiring.py::test_f058_r24_tope_de_la_consulta_positivo_menor_o_igual_a_1_se_acepta[1]
> 2 failed, 3 passed, 26 deselected, 1 warning in 3.41s
> ```
>
> Con el original (`gt=0`): `5 passed, 26 deselected, 1 warning in 3.43s`.
> Mutante **muerto**.
>
> **No se relanza la campaña**: la muestra (20 de 63, semilla `20260820`,
> workers: 1) ya se evaluó entera y el único superviviente queda muerto con
> la verificación manual de arriba; relanzarla costaría ~4 min sin aportar
> nada sobre este mutante. Resultado efectivo: 20 evaluados, 20 muertos,
> 0 supervivientes.

