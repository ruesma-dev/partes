<!-- progress/mutacion_F-060_enmienda.md -->
# F-060 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-060` el 2026-10-24 22:42.

## Alcance

Origen del diff: **rama** (`4f102aa583779a70e17bdf59c5c8de78e669fc58` .. `feature/F-060-racha-incidencia-ciz-movil`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/racha_incidencia.py` | 19 |
| `services/partes-front/config/settings.py` | 10 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 82 |
| `services/partes-front/interface_adapters/web/app.py` | 2 |
| `services/partes-transfer/config/settings.py` | 7 |
| **Total** | **120** |

### Nota de alcance (implementer, T23)

Es la campaña de T23 que lanzó el líder **solo sobre lo que cambió la enmienda** (DA12, DA13):
`--base 4f102aa`, 5 ficheros, 120 líneas, **4 workers**. Por qué basta:

- La campaña completa de T13 (`progress/mutacion_F-060.md`) se midió sobre `1009cdb`, y entre
  `1009cdb` y `4f102aa` **no cambia ningún fichero de producción** (`git diff --name-only
  1009cdb 4f102aa`: solo tests de F-060, `progress/` y `tasks.md`). Todo el código de
  producción fuera de este diff ya pasó por la campaña de T13 con su análisis cerrado.
- Desde entonces los tests solo han crecido; los de la regla nueva que T16 tocó siguen
  ejercitando las mismas rutas (piden `mover_ciz=True` o el portal con `MOVER_CIZ=true`), así
  que lo que mataban lo siguen pudiendo matar. Las 4 equivalencias de sv4 aceptadas se
  re-ejecutaron sobre el fuente actual: `progress/equivalentes_F-060.py sv4` ⇒ «4 mutantes,
  0 distintos», exit 0 (2026-10-24, T23).
- **La campaña no se relanza** (por instrucción del líder): cada test nuevo se verificó
  aplicando su mutante a mano (ver abajo).

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 30 |
| Mutantes evaluados | 30 |
| Muertos | 24 |
| Supervivientes | 6 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 5517.4 s |
| SHA de HEAD medido | `ef2b5c597290b91813d4aa620dd52ee1e944b3e7` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-060_5zpfrt0u/wk_0/services/partes-front` | 518.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-060_5zpfrt0u/wk_1/services/partes-front` | 519.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-060_5zpfrt0u/wk_2/services/partes-front` | 517.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-060_5zpfrt0u/wk_3/services/partes-front` | 530.8 |
| Media por mutante evaluado (s) | 183.9 |
| Timeout efectivo por mutante (s) | 1062 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 300 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

Verificación a mano de cada test nuevo (todos en `services/partes-front`): script del
scratchpad que sustituye la línea exacta por la mutada, ejecuta los ficheros de test,
restaura el fichero y comprueba su sha256 byte a byte; al final `git status` sin cambios en
producción.

### 1. `services/partes-front/application/services/racha_incidencia.py:179` [entero]

- Original: `f = int(l.fecha_int or 0)`
- Mutado:   `f = int(l.fecha_int or 1)`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: es **el mismo mutante que el #6 de la campaña de T13** (misma
> línea de `viaja` dentro de `decidir`, desplazada de 172 a 179 por la enmienda), que el
> humano ya aceptó como equivalente (2026-10-24, «acepto»), y cuyo análisis ya se escribió
> sobre `viaja` con DA13 (T17 es anterior a T21/T22). `LineaHist.fecha_int` nunca es `None`
> ni `0` (su único productor, `_historico`, filtra `fecha_int.between(desde, hasta)`); y aunque
> llegara, `0` y `1` no cambian `viaja`: con `l.activa`, `racha` solo tiene días de
> `[desde, hasta_delante]` (>= 10101); sin ella, `primero = min(racha ∪ {D}) >= 10101`, así
> que `primero <= f` es falso para `0` y para `1`.
> Decisión: **mutante equivalente — ya ACEPTADO POR EL HUMANO como #6** (`progress/mutacion_F-060.md`).
> Comprobación: `progress/equivalentes_F-060.py sv4` (entrada #6, que se aplica sobre esta
> misma línea del fuente actual) re-ejecutado en T23: «4 mutantes, 0 distintos», exit 0. A
> mano: mutante aplicado ⇒ `87 passed` (sobrevive, como se espera); revertido, árbol limpio.

### 2. `services/partes-front/application/services/racha_incidencia.py:184` [comparacion]

- Original: `return (primero <= f <= ultimo and f != d`
- Mutado:   `return (primero <= f < ultimo and f != d`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: los tests de DA13 ponían la papelera en un día saltado
> intermedio o con el tramo acabando en D (donde `f == ultimo` implica `f == d`, ya excluido
> por `f != d`). Ninguno ponía una línea de la papelera **en el último día del tramo cuando ese
> día es posterior a D** (racha hacia delante).
> Decisión: **hueco real de test, test nuevo** (el código es correcto: DA13 dice «entre el
> primero y el último del tramo», ambos incluidos). `test_f060_r9_da13_papelera_del_ultimo_dia_del_tramo_viaja`
> (`tests/test_f060_racha_incidencia.py`): V el 1 y el 3, D = 2, en la papelera una V del 3
> `registrado` ⇒ viaja (`(1, 30, 31)`); la del 4 (tras el tramo, día trabajado) no.
> Con el mutante: `1 failed, 68 passed` (`DecisionRacha(..., (1, 30)) == DecisionRacha(..., (1, 30, 31))`);
> sin él, en verde. Revertido byte a byte, árbol limpio.

### 3. `services/partes-front/infrastructure/database/parte_repository.py:2320` [comparacion]

- Original: `ParteRegistroOrm.empleado_ide == reg.empleado_ide)`
- Mutado:   `ParteRegistroOrm.empleado_ide != reg.empleado_ide)`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: es `_rol_incidencia_anterior`, la copia literal de dev 0926857
> (DA12); sus tests solo usaban personas con DNI, así que la rama de identidad por
> `empleado_ide` (sin DNI) no se ejercitaba.
> Decisión: **test de caracterización nuevo, sin tocar la copia.**
> `test_f060_r26bis_rol_anterior_sin_dni_solo_cuenta_su_empleado`
> (`tests/test_f060_interruptor_sv4.py`): sin DNI, empleado 77 con V el 1 y el 2; empleado 88
> (sin DNI) trabaja el 1 y el 3 en la misma obra ⇒ el 2 del 77 es `fin` (las líneas del 88 no
> cuentan). Con el mutante la consulta mira al 88 ⇒ `inicio`: `1 failed, 17 passed`
> (`assert 'inicio' == 'fin'`). Revertido byte a byte, árbol limpio.

### 4. `services/partes-front/infrastructure/database/parte_repository.py:2331` [entero]

- Original: `.order_by(ParteRegistroOrm.fecha_int.desc()).limit(50)`
- Mutado:   `.order_by(ParteRegistroOrm.fecha_int.desc()).limit(51)`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: ningún test tenía más de 50 líneas de la persona en el día
> anterior. Solo se distingue con 51 o más líneas **del mismo día** (las 50 primeras filas de
> la consulta son siempre de la fecha más alta), y entonces depende de qué fila empatada en
> fecha queda fuera.
> Decisión: **test de caracterización nuevo, sin tocar la copia**, robusto al orden de los
> empates: `test_f060_r26bis_rol_anterior_tope_de_50_filas_hacia_atras` prueba las dos
> colocaciones de la única línea de trabajo (primera o última insertada). Con 50 líneas el día
> anterior, las dos dan `inicio` (se ven todas); con 51, al menos una da `fin` (la de trabajo
> se queda fuera del tope). En SQLite los empates salen en orden de inserción: queda fuera la
> última. Con el mutante las dos colocaciones dan `inicio`: `1 failed, 17 passed`
> (`assert 'fin' in {'inicio'}`). Revertido byte a byte, árbol limpio.

### 5. `services/partes-front/infrastructure/database/parte_repository.py:2346` [entero]

- Original: `.order_by(ParteRegistroOrm.fecha_int.asc()).limit(50)`
- Mutado:   `.order_by(ParteRegistroOrm.fecha_int.asc()).limit(51)`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: el mismo hueco que el 4, hacia delante.
> Decisión: **test de caracterización nuevo, sin tocar la copia.**
> `test_f060_r26bis_rol_anterior_tope_de_50_filas_hacia_delante`: V el 1 y el 2, y el 3 con
> 50 líneas (49 V + 1 de trabajo) ⇒ `fin` en las dos colocaciones; con 51 líneas, al menos una
> colocación da `intermedio`. Con el mutante: `1 failed, 17 passed`
> (`assert 'intermedio' in {'fin'}`). Revertido byte a byte, árbol limpio.

### 6. `services/partes-front/infrastructure/database/parte_repository.py:2353` [booleano]

- Original: `delante_incidencia = False`
- Mutado:   `delante_incidencia = True`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: todos los escenarios del rol anterior tenían algún día
> posterior a D (el 5 trabajado), así que nunca se llegaba a la rama «sin siguientes».
> Decisión: **test de caracterización nuevo, sin tocar la copia.**
> `test_f060_r26bis_rol_anterior_sin_dia_posterior_es_fin`: V el 1 y el 2 y nada después ⇒
> el 2 es `fin`. Con el mutante: `3 failed, 15 passed` (este y los de los supervivientes 3 y
> 4, que también acaban sin días posteriores; `assert 'intermedio' == 'fin'`). Revertido byte a byte, árbol limpio.

## Cierre del análisis (implementer, 2026-10-24)

| Resultado | Supervivientes |
|---|---|
| Muertos con test nuevo (5) | 2 (`viaja`, borde superior de DA13), 3, 4, 5, 6 (copia de dev 0926857) |
| Equivalente ya ACEPTADO POR EL HUMANO (1) | 1 = el #6 de la campaña de T13 (2026-10-24, «acepto») |
| Equivalentes nuevos | ninguno |

`_rol_incidencia_anterior` no se ha tocado: sigue siendo la copia literal de dev 0926857
salvo nombre y docstring (los 4 supervivientes de esa copia se matan con tests de
caracterización del comportamiento antiguo, incluido su tope de 50 filas). Ningún análisis
reveló un defecto de producción; no hay cambios de código de producción en T23.

## Timeouts

Ninguno.
