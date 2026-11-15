<!-- progress/mutacion_F-068.md -->
# F-068 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-068 --workers 4` el 2026-11-15 14:04.

## Alcance

Origen del diff: **rama** (`7e5f600588c2d8d441fb81640ae4c08cf0ec4f3b` .. `feature/F-068-conciliar-pide-recalculo`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/partes-front/infrastructure/database/parte_repository.py` | 43 | 9 |
| `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` | 5 | 0 — sin mutantes |
| `services/partes-front/interface_adapters/web/app.py` | 58 | 7 |
| **Total** | **106** | **16** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 16 |
| Mutantes evaluados | 10 |
| Muertos | 10 |
| Supervivientes | 0 (todos medidos: sin mapa no se poda) |
| Timeouts | 0 |
| Indeterminados | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 3071.3 s |
| SHA de HEAD medido | `5c84138c26b68a86556a28312ea74e5578393696` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-068_utnnr7c7/wk_0/services/partes-front` | 891.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-068_utnnr7c7/wk_1/services/partes-front` | 889.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-068_utnnr7c7/wk_2/services/partes-front` | 894.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-068_utnnr7c7/wk_3/services/partes-front` | 885.6 |
| Media por mutante evaluado (s) | 307.1 |
| Timeout efectivo por mutante (s) | 1789 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 600 |
| Workers | 4 |
| Un mutante por línea | sí — 16 generados → 10 candidatos, uno por línea |
| Muestreo | no: campaña completa (10 candidatos ≤ tope 100 del nivel `critico`) |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 523.7 (10 mutantes) |

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Ficheros sin mutantes

Cada uno tiene líneas en alcance y el generador no ha sacado de ellas ni un mutante: la campaña no las ha juzgado. Declara por qué no hay nada que mutar (solo declaraciones, cadenas, imports) o qué test de la fase RED cubre el cambio. El reviewer hace la prueba de control (`generar_mutantes` sin exclusión de alcance) y ninguna declaración puede quedarse en `PENDIENTE` al cerrar la feature.

### `services/partes-front/infrastructure/persistencia/recalculo_publisher.py` — 5 líneas en alcance, 0 mutantes

#### Declaración (implementer, 2026-11-15)

> Por qué no hay nada que mutar, o qué test lo cubre: las 5 líneas son dos comentarios (`#:`)
> y tres asignaciones de constantes de cadena (`MOTIVO_CASADO_CONCILIACION`,
> `MOTIVO_REASIGNACION`, `MOTIVO_DESHACER_TRABAJADOR`): el generador no muta literales de
> cadena. Su valor lo fijan `test_f068_r20_constantes_de_motivo` (sv4, RED en T1) y los 9
> casos nuevos de `tests/test_f042_contrato_recalculo.py` (raíz: sv3 los clasifica como
> recálculo), y el motivo de cada mensaje lo comprueban los tests de ruta
> (`test_f068_conciliar_e1_r1_*`, `test_f068_r17_reasignar_pide_un_recalculo`,
> `test_f068_r19_deshacer_*`).

