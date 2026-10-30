<!-- progress/mutacion_F-045.md -->
# F-045 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-045` el 2026-10-14 14:10.

## Alcance

Origen del diff: **rama** (`9d4dc26b3af9457c9b4a56214c97cf1a9edf85eb` .. `feature/F-045-reparto-ponderado-entre-obras`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-persistencia/application/services/recurso_conciliador.py` | 128 |
| `services/partes-persistencia/application/services/reparto_ponderado.py` | 263 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 17 |
| **Total** | **408** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 84 |
| Mutantes evaluados | 84 |
| Muertos | 76 |
| Supervivientes | 8 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 387.1 s |
| SHA de HEAD medido | `259e60958bdd583cf735ad99a3a15dfe2a27eeb7` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_hs43mhn4/wk_0/services/partes-persistencia` | 28.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_hs43mhn4/wk_1/services/partes-persistencia` | 28.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_hs43mhn4/wk_2/services/partes-persistencia` | 28.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_hs43mhn4/wk_3/services/partes-persistencia` | 29.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_hs43mhn4/wk_4/services/partes-persistencia` | 28.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_hs43mhn4/wk_5/services/partes-persistencia` | 28.8 |
| Media por mutante evaluado (s) | 4.6 |
| Timeout efectivo por mutante (s) | 600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 600 |
| Workers | 6 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-persistencia/application/services/recurso_conciliador.py:663` [comparacion]

- Original: `if total_ord <= 1e-9:`
- Mutado:   `if total_ord < 1e-9:`

#### Análisis (implementer)

Solo difiere si `total_ord` vale EXACTAMENTE `1e-9`, y las horas de un
parte nunca valen eso: son números del parte, de 2 decimales como mucho. Con
0 h, `0 < 1e-9` sigue siendo cierto, así que el
mutante también sale (`test_f045_r20_sabado_sin_horas_ordinarias_no_se_toca`
pasa con los dos). La guarda es la de siempre, solo se ha movido de sitio.
**Equivalente.**

**Demostración ejecutable (RM5)**: `progress/equivalentes_F-045.py` compara los splits y el log de `_reclasificar_extras_jornada` en 3.000 grupos (candef 8 y 9; sábado no laborable, viernes festivo a veces; horas de 0 incluidas) y da **EQUIVALENTE**.

### 2. `services/partes-persistencia/application/services/reparto_ponderado.py:36` [comparacion]

- Original: `return abs(valor / paso - round(valor / paso)) <= _TOLERANCIA`
- Mutado:   `return abs(valor / paso - round(valor / paso)) < _TOLERANCIA`

#### Análisis (implementer)

`<=` frente a `<` contra una tolerancia de `1e-6`: solo difieren si la
distancia al múltiplo es exactamente `1e-6`, cosa que no ocurre con horas
de 2 decimales (su distancia es 0 o ≥ 0,01/paso). **Equivalente.**

**Demostración ejecutable (RM5)**: `progress/equivalentes_F-045.py` compara original y mutante en 20.000 días sintéticos con horas de parte (`repartir_dia`, `diferencias_ideal`, `elegir_paso`) y da **EQUIVALENTE**. Releído tras la pasada 2: el código de alrededor no cambió.

### 3. `services/partes-persistencia/application/services/reparto_ponderado.py:63` [entero]

- Original: `return round(unidades * paso, 6)`
- Mutado:   `return round(unidades * paso, 7)`

#### Análisis (implementer)

Redondear a 6 o a 7 decimales un múltiplo de 0,01 deja el mismo float: el
error de `unidades × paso` es del orden de 1e-15
(`652 × 0,01 = 6,5200000000000005`). **Equivalente.**

**Demostración ejecutable (RM5)**: `progress/equivalentes_F-045.py` compara original y mutante en 20.000 días sintéticos con horas de parte (`repartir_dia`, `diferencias_ideal`, `elegir_paso`) y da **EQUIVALENTE**. Releído tras la pasada 2: el código de alrededor no cambió.

### 4. `services/partes-persistencia/application/services/reparto_ponderado.py:79` [comparacion]

- Original: `positivos = [p for p in participantes if p.peso > 0]`
- Mutado:   `positivos = [p for p in participantes if p.peso >= 0]`

#### Análisis (implementer)

Con `>= 0` entran participantes de peso 0: su suelo es 0 y su resto 0, y
nunca reciben un paso. Eso se debe a que hay al menos `faltan`
participantes con resto > 0 (Σrestos/Σpesos = faltan, y cada cociente es
< 1), y los de resto 0 van al final del orden. Si todos pesan 0, `suma = 0`
y salen ceros igual. `test_f045_r1_peso_cero_recibe_cero` y
`test_f045_r5_*` pasan con los dos. Los pesos negativos siguen fuera.
**Equivalente.**

**Demostración ejecutable (RM5)**: `progress/equivalentes_F-045.py` compara original y mutante en 20.000 días sintéticos con horas de parte (`repartir_dia`, `diferencias_ideal`, `elegir_paso`) y da **EQUIVALENTE**. Releído tras la pasada 2: el código de alrededor no cambió.

### 5. `services/partes-persistencia/application/services/reparto_ponderado.py:188` [comparacion]

- Original: `if residuo < -_EPS or (abs(residuo) > _EPS and not por_obra):`
- Mutado:   `if residuo <= -_EPS or (abs(residuo) > _EPS and not por_obra):`

#### Análisis (implementer)

`residuo <= -1e-9` frente a `< -1e-9`: solo difieren si el residuo vale
exactamente `-1e-9`, imposible con jornadas y horas de 2 decimales. Los
bordes reales (residuo 0 y residuo −0,5) los fijan
`test_f045_r23_repartir_dia_residuo_cero_*` y `…_de_medio_paso_por_debajo`.
**Equivalente.**

**Demostración ejecutable (RM5)**: `progress/equivalentes_F-045.py` compara original y mutante en 20.000 días sintéticos con horas de parte (`repartir_dia`, `diferencias_ideal`, `elegir_paso`) y da **EQUIVALENTE**. Releído tras la pasada 2: el código de alrededor no cambió.

### 6. `services/partes-persistencia/application/services/reparto_ponderado.py:188` [comparacion]

- Original: `if residuo < -_EPS or (abs(residuo) > _EPS and not por_obra):`
- Mutado:   `if residuo < -_EPS or (abs(residuo) >= _EPS and not por_obra):`

#### Análisis (implementer)

Mismo razonamiento: `abs(residuo) >= 1e-9` frente a `> 1e-9` solo
difieren en `abs(residuo) == 1e-9`. Los casos residuo 0 con y sin
ajustables los cubre `test_f045_r23_*`. **Equivalente.**

**Demostración ejecutable (RM5)**: `progress/equivalentes_F-045.py` compara original y mutante en 20.000 días sintéticos con horas de parte (`repartir_dia`, `diferencias_ideal`, `elegir_paso`) y da **EQUIVALENTE**. Releído tras la pasada 2: el código de alrededor no cambió.

### 7. `services/partes-persistencia/application/services/reparto_ponderado.py:205` [comparacion]

- Original: `if abs(cuota - ln.horas) > _EPS:`
- Mutado:   `if abs(cuota - ln.horas) >= _EPS:`

#### Análisis (implementer)

`abs(cuota − horas) >= 1e-9` frente a `> 1e-9`. Cuando la cuota coincide
con las horas, la diferencia es 0 (los dos dicen «sin split»); cuando no,
es ≥ 0,01 (los dos dicen «split»). El caso 1e-9 exacto no existe.
**Equivalente.** No se cambia a `!=` porque las horas leídas de la base
pueden traer ruido de float (`2,3000000000000003`) y daría splits de 0,00.

**Demostración ejecutable (RM5)**: `progress/equivalentes_F-045.py` compara original y mutante en 20.000 días sintéticos con horas de parte (`repartir_dia`, `diferencias_ideal`, `elegir_paso`) y da **EQUIVALENTE**. Releído tras la pasada 2: el código de alrededor no cambió.

### 8. `services/partes-persistencia/application/services/reparto_ponderado.py:261` [comparacion]

- Original: `if ln.fija and abs(despues_ln - ln.horas) > _EPS:`
- Mutado:   `if ln.fija and abs(despues_ln - ln.horas) >= _EPS:`

#### Análisis (implementer)

`abs(después − antes) >= 1e-9` frente a `> 1e-9` en la medición del
ideal: igual que el anterior, la diferencia es 0 o ≥ 0,01. **Equivalente.**

**Demostración ejecutable (RM5)**: `progress/equivalentes_F-045.py` compara original y mutante en 20.000 días sintéticos con horas de parte (`repartir_dia`, `diferencias_ideal`, `elegir_paso`) y da **EQUIVALENTE**. Releído tras la pasada 2: el código de alrededor no cambió.


## Demostración de los equivalentes (RM5)

Comando, lanzado desde `services/partes-persistencia` con el Python del `.venv` del repositorio:
`python ../../progress/equivalentes_F-045.py`. Salida real en HEAD `259e609`:

```
EQUIVALENTE: application/services/recurso_conciliador.py: if total_ord <= 1e-9: (no laborable) -> if total_ord < 1e-9:
EQUIVALENTE: application/services/reparto_ponderado.py: round(valor / paso)) <= _TOLERANCIA -> round(valor / paso)) < _TOLERANCIA
EQUIVALENTE: application/services/reparto_ponderado.py: return round(unidades * paso, 6) -> return round(unidades * paso, 7)
EQUIVALENTE: application/services/reparto_ponderado.py: if p.peso > 0] -> if p.peso >= 0]
EQUIVALENTE: application/services/reparto_ponderado.py: if abs(cuota - ln.horas) > _EPS: -> if abs(cuota - ln.horas) >= _EPS:
EQUIVALENTE: application/services/reparto_ponderado.py: (abs(residuo) > _EPS and not por_obra) -> (abs(residuo) >= _EPS and not por_obra)
EQUIVALENTE: application/services/reparto_ponderado.py: if residuo < -_EPS or -> if residuo <= -_EPS or
EQUIVALENTE: application/services/reparto_ponderado.py: if ln.fija and abs(despues_ln - ln.horas) > _EPS: -> if ln.fija and abs(despues_ln - ln.horas) >= _EPS:
8 mutantes, 0 distintos            (exit 0, ~70 s)
```

**Control de que el script discrimina**: con el mutante de la pasada 1
(`_RESOLUCION = 10_000 → 10001`) el mismo comparador sale **DISTINTO** y
enseña un contraejemplo de `repartir_dia` (obra 30 con 10,5 h y 3,5 h).

## Historia de la campaña

| Campaña | HEAD | Mutantes | Muertos | Supervivientes | Tiempo |
|---|---|---|---|---|---|
| 1 | `4960287` (T9) | 88 | 64 | 24 | 442,9 s |
| 2 | `cc3f910` (refuerzo T10) | 82 | 73 | 9 | 383,4 s |
| 3 | `259e609` (review pasada 1) | 84 | 76 | **8** | 387,1 s |

- **De la 1 a la 2**: 11 mutantes muertos con tests nuevos y 4 que
  desaparecen al quitar condiciones redundantes (`n_obras >= 2 or`,
  `round(cuota, 2)` y la guarda de `base_id`).
- **Review, pasada 1 (dos errores corregidos en la 3)**:
  - **Análisis #2 erróneo.** `_RESOLUCION = 10_000 → 10001` **no era
    equivalente**: con 10 001, `round(1,5 × 10 001)` y `round(2,5 × 10 001)`
    redondean hacia lados distintos y deshacen el empate de restos de R2.
    Lo matan ahora `test_f045_r2_empate_de_restos_con_pesos_de_media_hora`,
    `…_coincide_con_el_modelo_exacto_en_horas_de_parte` (3.000 repartos
    contra un modelo con fracciones) y
    `test_f045_r2_repartir_dia_empate_de_restos_con_congelada`.
  - **Código revisado.** Con escala potencia de 10 y horas de ≤ 4 decimales,
    `peso × escala` es entero salvo ruido de coma flotante, así que `round`
    nunca cae en un .5. Se documenta en `_RESOLUCION` y lo vigila el test
    del modelo exacto.
  - **Guarda de `base_id` repuesta** (`if extra_auto and tipo_linea ==
    EXTRA`). No era redundante: sv4 puede reclasificar una `extra_auto` a
    normal y, congelada, sin la guarda se tomaba por extra de su propia
    pareja (`(1, 8→5,5), (2, 2→0)` en vez de `(1, 8→5,0), (2, 2→1,0)`). Lo
    fija `test_f045_r25_extra_auto_reclasificada_a_normal_pesa_por_si_misma`
    (RED contra la versión sin guarda).
- **Tests de R33** (candef 9): se añadieron entre la campaña 2 y la 3. La 3
  ya los incluye.

Los 8 supervivientes de la campaña 3 son equivalentes, y cada uno lleva su
demostración ejecutable. **Pendiente: que el humano acepte estas
justificaciones** (rigor crítico).
