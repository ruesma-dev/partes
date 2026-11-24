<!-- progress/mutacion_F-083.md -->
# F-083 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-083 --workers 4` el 2026-11-24 14:09.

## Alcance

Origen del diff: **rama** (`5b7ddce4a716caf988c019a29fd84fa41b585f15` .. `feature/F-083-ciz-solo-fin-de-racha`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/partes-transfer/application/pipelines/registro_pipeline.py` | 20 | 2 |
| `services/partes-transfer/application/services/racha_ciz.py` | 80 | 23 |
| **Total** | **100** | **25** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 25 |
| Mutantes evaluados | 19 |
| Muertos | 17 |
| Supervivientes | 2 (todos medidos: sin mapa no se poda) |
| Timeouts | 0 |
| Indeterminados | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 176.4 s |
| SHA de HEAD medido | `9784e0e7ae001ede2ed98c773eea6065ea6bc4bf` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_t1bx_ug0/wk_0/services/partes-transfer` | 24.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_t1bx_ug0/wk_1/services/partes-transfer` | 24.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_t1bx_ug0/wk_2/services/partes-transfer` | 24.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_t1bx_ug0/wk_3/services/partes-transfer` | 24.3 |
| Media por mutante evaluado (s) | 9.3 |
| Timeout efectivo por mutante (s) | 600 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 600 |
| Workers | 4 |
| Un mutante por línea | sí — 25 generados → 19 candidatos, uno por línea |
| Muestreo | no: campaña completa (19 candidatos ≤ tope 100 del nivel `critico`) |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 24.7 (19 mutantes) |

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

**Cierre de T6 (2026-11-24).** Los **2 supervivientes son equivalentes**, pendientes de aceptación del humano: los dos cambian `is not None` por la veracidad sobre el resultado de `ultima_posterior`, que es `None` o una `LineaSigrid` (siempre verdadera). Demostración ejecutable en `progress/equivalentes_F-083.py` (exit 0). **Encargo del reviewer** (quitar `candidatas = list(candidatas)` de `decidir_fin`, que la campaña no genera como mutante): NO es equivalente y muere con el test nuevo `test_f083_puro_r2_con_un_iterador` (`services/partes-transfer/tests/test_f083_ciz_solo_fin_de_racha.py`). Verificado a mano: sin la línea da `crear` en vez de `intermedio` y el test cae; con ella pasa. El mutante se deshizo. Ningún cambio de código de producción.

### 1. `services/partes-transfer/application/services/racha_ciz.py:189` [veracidad]

- Original: `if ultima is not None:`
- Mutado:   `if ultima:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `ultima` es el resultado de `ultima_posterior(..., solo_ciz=True)`, que solo tiene dos `return`: `None` o `max(posteriores, ...)` con `posteriores = [ls for ls in candidatas ...]`, es decir, una `LineaSigrid`. `LineaSigrid` es una dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, aunque traiga `ide` 0 o todos sus campos vacíos. `is not None` y la veracidad coinciden en todo el dominio.
> Decisión: **mutante equivalente, pendiente de aceptación del humano**. Demostración ejecutable: `progress/equivalentes_F-083.py` (#1), exit 0 en T6: comprueba el dominio por el AST, el tipo y, aplicando el mutante en memoria, que `decidir_fin` original y mutado deciden igual en 5.000 casos al azar con bordes (listas e iteradores). Control negativo: con un mutante no equivalente (`if False:`) el script cae en el caso 5.

### 2. `services/partes-transfer/application/services/racha_ciz.py:196` [veracidad]

- Original: `if sigue is not None:`
- Mutado:   `if sigue:`
- Juicio: MEDIDO

#### Análisis

> Por qué ningún test lo caza: `sigue` es el resultado de `ultima_posterior(..., solo_ciz=False)`, que solo tiene dos `return`: `None` o `max(posteriores, ...)` con `posteriores = [ls for ls in candidatas ...]`, es decir, una `LineaSigrid`. `LineaSigrid` es una dataclass sin `__bool__` ni `__len__`: toda instancia es verdadera, aunque traiga `ide` 0 o todos sus campos vacíos. `is not None` y la veracidad coinciden en todo el dominio.
> Decisión: **mutante equivalente, pendiente de aceptación del humano**. Demostración ejecutable: `progress/equivalentes_F-083.py` (#2), exit 0 en T6: comprueba el dominio por el AST, el tipo y, aplicando el mutante en memoria, que `decidir_fin` original y mutado deciden igual en 5.000 casos al azar con bordes (listas e iteradores). Control negativo: con un mutante no equivalente (`if False:`) el script cae en el caso 5.

## No muertos: código de salida

| Fichero:línea | Operador | Veredicto | Código |
|---|---|---|---|
| `services/partes-transfer/application/services/racha_ciz.py:189` | veracidad | superviviente | 0 |
| `services/partes-transfer/application/services/racha_ciz.py:196` | veracidad | superviviente | 0 |

