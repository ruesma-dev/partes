<!-- progress/mutacion_F-034.md -->
# F-034 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-034` el 2026-10-21 00:10.

## Alcance

Origen del diff: **rama** (`4bda57e3fc5cd20ca521c75243e7a536bf40a911` .. `feature/F-034-escribir-solo-en-partes-abiertos`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-transfer/application/pipelines/registro_pipeline.py` | 99 |
| `services/partes-transfer/application/services/parte_abierto.py` | 87 |
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | 66 |
| **Total** | **252** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 22 |
| Mutantes evaluados | 22 |
| Muertos | 18 |
| Supervivientes | 4 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 227.0 s |
| SHA de HEAD medido | `2afb1aec5894cb0f4f9955f01041f3b9dbd8539f` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-034_fivxyu04/wk_0/services/partes-transfer` | 29.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-034_fivxyu04/wk_1/services/partes-transfer` | 31.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-034_fivxyu04/wk_2/services/partes-transfer` | 31.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-034_fivxyu04/wk_3/services/partes-transfer` | 30.0 |
| Media por mutante evaluado (s) | 10.3 |
| Timeout efectivo por mutante (s) | 300 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 300 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-transfer/application/pipelines/registro_pipeline.py:599` [entero]

- Original: `if float(ls.can or 0) != 0}`
- Mutado:   `if float(ls.can or 1) != 0}`

#### Análisis (implementer, 2026-10-21)

> Por qué ningún test lo caza: ninguna pisada de los tests tenía `can` NULL; con `or 1` una
> pisada con `can` NULL contaría como «viva» (el SQL la trata como 0: `ISNULL(p.can, 0)`) y el
> motivo nombraría su parte en vez del elegido. **Hueco real.**
> Decisión: test nuevo `test_f034_t12_pisada_con_can_nulo_no_esta_viva`
> (`test_f034_pipeline_cierre.py`): falla contra el mutante aplicado a mano («PT26/00314
> (Cerrado)» en vez de «PT26/00400 (Imputado)») y pasa contra el código.

### 2. `services/partes-transfer/application/pipelines/registro_pipeline.py:599` [entero]

- Original: `if float(ls.can or 0) != 0}`
- Mutado:   `if float(ls.can or 0) != 1}`

#### Análisis (implementer, 2026-10-21)

> Por qué ningún test lo caza: las pisadas vivas de los tests tenían `can = 8`, y `8 != 1`
> igual que `8 != 0`; una pisada con exactamente una hora no estaba probada. **Hueco real.**
> Decisión: test nuevo `test_f034_t12_pisada_con_una_hora_si_esta_viva`; contra el mutante
> sale `no_escrita` en vez de `parte_no_abierto: el parte PT26/00314`, y lo caza también el de
> `can` NULL. Pasa contra el código.

### 3. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:569` [entero]

- Original: `int(paride or 0), int(pos), int(fecha_int),`
- Mutado:   `int(paride or 1), int(pos), int(fecha_int),`

#### Análisis (implementer, 2026-10-21)

> Por qué ningún test lo caza: comportamiento anterior a F-034 (la línea se reformateó al
> añadir la guarda) que ningún test de `stmt_insert_linea` fijaba con `paride` None (sí lo
> hacía `test_f046_t22` para la extra). **Hueco real.**
> Decisión: test nuevo `test_f034_t12_insert_linea_sin_partida_va_con_paride_0`
> (`test_f034_cliente_guarda.py`): `assert 1 == 0` contra el mutante; verde contra el código.

### 4. `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py:571` [entero]

- Original: `round(float(can) * float(pre), 2), int(ano),`
- Mutado:   `round(float(can) * float(pre), 3), int(ano),`

#### Análisis (implementer, 2026-10-21)

> Por qué ningún test lo caza: igual que el 3, redondeo de `tot` anterior a F-034 sin test en
> `stmt_insert_linea` (`8 × 10,5 = 84,0` es igual con 2 y con 3 decimales). **Hueco real.**
> Decisión: test nuevo `test_f034_t12_insert_linea_tot_redondeado_a_2_decimales`
> (`can = 0,5`, `pre = 0,123`): `0.061 == 0.06` falla contra el mutante; verde contra el
> código.


## Cierre (implementer)

Los 4 supervivientes eran huecos reales y tienen test nuevo; cada test se comprobó **aplicando
el mutante a mano** y ejecutando `pytest tests -k t12` en `services/partes-transfer` (falla con
el mutante, verde sin él; trazas en `progress/impl_F-034.md`). Balance: 22 de 22 detectados,
0 equivalentes. La campaña no se relanzó: cada mutante se verificó uno a uno.

Nota sobre el alcance: la herramienta muta operadores, enteros y comparaciones, **no el texto
de las cadenas SQL**. El texto exacto de las 5 sentencias y sus parámetros lo fijan
`test_f034_cliente_guarda.py` y los tests de F-021/F-046 ampliados (rigor crítico, design §3).
