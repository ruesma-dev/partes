<!-- progress/mutacion_F-045.md -->
# F-045 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-045` el 2026-10-14 13:38.

## Alcance

Origen del diff: **rama** (`9d4dc26b3af9457c9b4a56214c97cf1a9edf85eb` .. `feature/F-045-reparto-ponderado-entre-obras`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-persistencia/application/services/recurso_conciliador.py` | 124 |
| `services/partes-persistencia/application/services/reparto_ponderado.py` | 258 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 17 |
| **Total** | **399** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 82 |
| Mutantes evaluados | 82 |
| Muertos | 73 |
| Supervivientes | 9 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 383.4 s |
| SHA de HEAD medido | `cc3f9108867669a5be3fa3d8e0e4246d86b8f585` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_pg03txx8/wk_0/services/partes-persistencia` | 34.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_pg03txx8/wk_1/services/partes-persistencia` | 35.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_pg03txx8/wk_2/services/partes-persistencia` | 35.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_pg03txx8/wk_3/services/partes-persistencia` | 34.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_pg03txx8/wk_4/services/partes-persistencia` | 34.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_pg03txx8/wk_5/services/partes-persistencia` | 34.1 |
| Media por mutante evaluado (s) | 4.7 |
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

### 2. `services/partes-persistencia/application/services/reparto_ponderado.py:24` [entero]

- Original: `_RESOLUCION = 10_000`
- Mutado:   `_RESOLUCION = 10001`

#### Análisis (implementer)

Es la escala entera (diezmilésimas) con la que `repartir` compara pesos.
El mayor resto solo depende de las proporciones entre pesos: escalar todos
por el mismo factor no cambia ni los suelos ni el orden de los restos. Con
10 001, el redondeo de `peso × escala` mete un ruido de menos de 1/10 001
por peso, y ese ruido lo absorbe la misma ronda de mayor resto. Los pesos
reales tienen 2 decimales y ningún test separa las dos escalas: lo comprobé
a mano con 0,25/0,75 y con un peso de 0,00001, y la campaña muestra que la
suite entera (7,75/2 y la rejilla de R4 incluidas) pasa también con 10 001. **Equivalente** a efectos de horas de parte.

### 3. `services/partes-persistencia/application/services/reparto_ponderado.py:31` [comparacion]

- Original: `return abs(valor / paso - round(valor / paso)) <= _TOLERANCIA`
- Mutado:   `return abs(valor / paso - round(valor / paso)) < _TOLERANCIA`

#### Análisis (implementer)

`<=` frente a `<` contra una tolerancia de `1e-6`: solo difieren si la
distancia al múltiplo es exactamente `1e-6`, cosa que no ocurre con horas
de 2 decimales (su distancia es 0 o ≥ 0,01/paso). **Equivalente.**

### 4. `services/partes-persistencia/application/services/reparto_ponderado.py:58` [entero]

- Original: `return round(unidades * paso, 6)`
- Mutado:   `return round(unidades * paso, 7)`

#### Análisis (implementer)

Redondear a 6 o a 7 decimales un múltiplo de 0,01 deja el mismo float: el
error de `unidades × paso` es del orden de 1e-15
(`652 × 0,01 = 6,5200000000000005`). **Equivalente.**

### 5. `services/partes-persistencia/application/services/reparto_ponderado.py:74` [comparacion]

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

### 6. `services/partes-persistencia/application/services/reparto_ponderado.py:183` [comparacion]

- Original: `if residuo < -_EPS or (abs(residuo) > _EPS and not por_obra):`
- Mutado:   `if residuo <= -_EPS or (abs(residuo) > _EPS and not por_obra):`

#### Análisis (implementer)

`residuo <= -1e-9` frente a `< -1e-9`: solo difieren si el residuo vale
exactamente `-1e-9`, imposible con jornadas y horas de 2 decimales. Los
bordes reales (residuo 0 y residuo −0,5) los fijan
`test_f045_r23_repartir_dia_residuo_cero_*` y `…_de_medio_paso_por_debajo`.
**Equivalente.**

### 7. `services/partes-persistencia/application/services/reparto_ponderado.py:183` [comparacion]

- Original: `if residuo < -_EPS or (abs(residuo) > _EPS and not por_obra):`
- Mutado:   `if residuo < -_EPS or (abs(residuo) >= _EPS and not por_obra):`

#### Análisis (implementer)

Mismo razonamiento: `abs(residuo) >= 1e-9` frente a `> 1e-9` solo
difieren en `abs(residuo) == 1e-9`. Los casos residuo 0 con y sin
ajustables los cubre `test_f045_r23_*`. **Equivalente.**

### 8. `services/partes-persistencia/application/services/reparto_ponderado.py:200` [comparacion]

- Original: `if abs(cuota - ln.horas) > _EPS:`
- Mutado:   `if abs(cuota - ln.horas) >= _EPS:`

#### Análisis (implementer)

`abs(cuota − horas) >= 1e-9` frente a `> 1e-9`. Cuando la cuota coincide
con las horas, la diferencia es 0 (los dos dicen «sin split»); cuando no,
es ≥ 0,01 (los dos dicen «split»). El caso 1e-9 exacto no existe.
**Equivalente.** No se cambia a `!=` porque las horas leídas de la base
pueden traer ruido de float (`2,3000000000000003`) y daría splits de 0,00.

### 9. `services/partes-persistencia/application/services/reparto_ponderado.py:256` [comparacion]

- Original: `if ln.fija and abs(despues_ln - ln.horas) > _EPS:`
- Mutado:   `if ln.fija and abs(despues_ln - ln.horas) >= _EPS:`

#### Análisis (implementer)

`abs(después − antes) >= 1e-9` frente a `> 1e-9` en la medición del
ideal: igual que el anterior, la diferencia es 0 o ≥ 0,01. **Equivalente.**


## Historia de la campaña

**Primera campaña** (HEAD `4960287`, T9): 88 mutantes, 64 muertos y
**24 supervivientes** en 442,9 s. De esos 24, 15 se resolvieron en el
commit `cc3f910` (T10):

- **Tests nuevos**:
  - contador de `__init__`: `test_f045_r25_el_contador_empieza_en_cero`;
  - `suma <= 0` → `<= 1` y `< 0`: `test_f045_r5_un_peso_minimo_se_lleva_todo`
    y `…_por_debajo_de_la_resolucion_no_rompe`;
  - cuatro `frozen=True`: `test_f045_r1_los_participantes_son_inmutables`
    y `test_f045_r7_repartir_dia_resultados_inmutables`;
  - `extra_auto` por defecto: `test_f045_r25_ideal_la_extra_explicita_con_base_no_es_de_la_pareja`;
  - `horas <= 0` → `< 0`: `test_f045_r22_…ordinaria_a_cero_de_la_misma_obra_no_cuenta`;
  - redondeo a 2 decimales de la extra y del ideal:
    `test_f045_r28_…la_extra_se_redondea_a_centesimas` y
    `test_f045_r25_ideal_la_extra_de_la_pareja_a_centesimas`.
- **Condiciones redundantes eliminadas**, sin cambio de comportamiento:
  - `n_obras >= 2 or` en el INFO de R30: n_lineas ≥ n_obras siempre;
    eran 2 mutantes;
  - `and tipo_linea == EXTRA` en `base_id`: una `extra_auto` siempre es
    `extra`;
  - `round(cuota, 2)` en `horas_norm`: la cuota ya es múltiplo del paso.

**Segunda campaña** (la de este informe, HEAD `cc3f910`): 82 mutantes, 73
muertos y 9 supervivientes. Los 9 son mutantes de igualdad exacta contra
una tolerancia, o de constantes de escala o de redondeo, y los 9 se
justifican arriba como equivalentes. **Pendiente: que el humano acepte esas
justificaciones** (rigor crítico).
