<!-- progress/mutacion_F-050.md -->
# F-050 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-050` el 2026-10-20 16:47.

## Alcance

Origen del diff: **rama** (`ff2ed8e5fa9e34384b290e37dbd0ae2b3f894e1c` .. `feature/F-050-misma-fila-para-el-mismo-trabajador`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/infrastructure/database/parte_repository.py` | 153 |
| `services/partes-front/interface_adapters/web/app.py` | 10 |
| **Total** | **163** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 35 |
| Mutantes evaluados | 20 |
| Muertos | 13 |
| Supervivientes | 4 |
| Timeouts | 3 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 14175.8 s |
| SHA de HEAD medido | `04613e647b6613548e3429ec0ba9c9ef826d03d6` |
| Línea base (s) — `services/partes-front` | 519.6 |
| Media por mutante evaluado (s) | 708.8 |
| Timeout efectivo por mutante (s) | 1040 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 300 |
| Workers | 1 |
| Muestreo | sí — 20 de 35 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/infrastructure/database/parte_repository.py:1036` [entero]

- Original: `0 if r.matched else 1, _norm(r.nombre),`
- Mutado:   `0 if r.matched else 2, _norm(r.nombre),`

#### Análisis (implementer, 2026-10-20) · EQUIVALENTE

> Por qué ningún test lo caza: el primer elemento de la clave de orden solo toma dos
> valores (casada / sin casar) y `sort` solo los compara entre sí. `{0, 1}` y `{0, 2}`
> ordenan igual (0 < 1 y 0 < 2): casadas primero en los dos casos. No hay entrada que dé
> otro orden. El orden «casadas primero» sí está cubierto (lo caza el mutante #6, `1 if
> r.matched else 1`, muerto).
> Decisión: **mutante equivalente**; sin test.

### 2. `services/partes-front/infrastructure/database/parte_repository.py:1037` [entero]

- Original: `r.empresas[0] if r.empresas else 10**9,`
- Mutado:   `r.empresas[0] if r.empresas else 10**10,`

#### Análisis (implementer, 2026-10-20) · EQUIVALENTE en el dominio

> Por qué ningún test lo caza: `10**9` es el centinela «sin empresa ⇒ detrás» de R26; los
> dos valores son mayores que cualquier código de empresa con el que se compara, así que
> ordenan igual. Solo darían órdenes distintos para una empresa con código entre 10^9 y
> 10^10; la columna `parte_documents.empresa` es `Integer` y los códigos de empresa de
> Sigrid (`emp`, entero) son números de empresa del grupo, de muy pocas cifras, así que
> ese intervalo no se da. «Sin empresa, detrás» sí está cubierto: lo caza el mutante #8
> (`r.empresas[1]`, muerto) y lo fijan los tests de R26 de `test_f050_empresa.py`.
> Decisión: **mutante equivalente** para los datos reales; sin test (un test con una
> empresa 5·10^9 fijaría un valor que no existe). Observación para el reviewer: si se
> quisiera robustez formal, el centinela podría ser `float("inf")`; no se cambia porque
> no altera ningún comportamiento observable.

### 3. `services/partes-front/infrastructure/database/parte_repository.py:1120` [booleano]

- Original: `casada=False, empleado_ide=r.empleado_ide, recurso=None,`
- Mutado:   `casada=True, empleado_ide=r.empleado_ide, recurso=None,`

#### Análisis (implementer, 2026-10-20) · EQUIVALENTE

> Por qué ningún test lo caza: en `clave_actual_de_clave_antigua` la llamada pasa siempre
> `recurso=None` para reproducir la regla anterior a F-050 (ficha ⇒ `emp-`; si no, leído
> ⇒ `nom-`). En `_clave_trabajador` el único uso de `casada` es la primera rama, `if casada
> and recurso is not None`, que con `recurso=None` es falsa valga lo que valga `casada`;
> el resto de ramas no lo miran. La función es pura, así que el resultado es idéntico para
> toda línea. El `casada=False` es documentación de la intención («la regla anterior»).
> Decisión: **mutante equivalente**; sin test. El filtro sí está cubierto: el mutante #10
> (`not` invertido) murió y `test_f050_r14_repo_nom_solo_de_lineas_sin_ficha` fija qué
> líneas cuentan.

### 4. `services/partes-front/infrastructure/database/parte_repository.py:3804` [comparacion]

- Original: `casada=empleado_ide is not None or metodo_empleado is not None,`
- Mutado:   `casada=empleado_ide is None or metodo_empleado is not None,`

#### Análisis (implementer, 2026-10-20) · HUECO REAL ⇒ test nuevo

> Por qué ningún test lo caza: `metodo_empleado` solo es `recurso_manual` sin ficha y con
> recurso. Por casos de (ficha, recurso) del alta: sin ficha y con recurso, los dos dan
> `casada=True`; sin ficha ni recurso, el mutante da `True` pero con `recurso=None` no
> importa (ver #3); **con ficha y con recurso**, el original da `casada=True` ⇒
> `rec-{recurso}` y el mutante `False` ⇒ `emp-{ficha}`. Ese es justo el caso de R19 (la
> vista del trabajador manda ficha y recurso al modal, M5), y ningún test de R16 lo
> cubría: `test_f050_r16_con_ficha_hereda_de_su_clave` usa ficha **sin** recurso (`emp-`) y
> los de E6 son sin ficha. Con el mutante, el alta de una persona con ficha y recurso no
> encuentra a su `rec-` en el parte y abre fila nueva: el defecto que F-050 viene a quitar.
> Decisión: **test nuevo**
> `test_f050_r16_con_ficha_y_recurso_hereda_de_su_rec` (`tests/test_f050_alta_manual.py`):
> en el parte, la persona con ficha 56 y recurso 5601 en la fila 4; el alta con
> `ide=56, reside=5601` debe caer en la fila 4 con su leído. Contra el mutante falla (traza
> en `progress/impl_F-050.md`, T11); contra el código, verde. No se relanza la campaña.

## Timeouts

- `services/partes-front/infrastructure/database/parte_repository.py:1123` [comparacion] if len(actuales) == 1 and clave not in actuales: -> if len(actuales) != 1 and clave not in actuales:
- `services/partes-front/infrastructure/database/parte_repository.py:1123` [entero] if len(actuales) == 1 and clave not in actuales: -> if len(actuales) == 2 and clave not in actuales:
- `services/partes-front/interface_adapters/web/app.py:873` [aritmetico] + (f"?{query}" if query else ""), -> - (f"?{query}" if query else ""),

### Análisis de los timeouts (implementer, 2026-10-20) · DETECTADOS, sin bucle

Reproducidos uno a uno (sin relanzar la campaña) con
`PYTHONDONTWRITEBYTECODE=1 python -m pytest -q --tb=line -p no:cacheprovider <23 ficheros>`
desde `services/partes-front`: los 18 ficheros de sv4 que piden `/trabajadores/…` más los 5
de F-050, sobre el fichero mutado y restaurado después (`git status` limpio de producción).
Script y log en el scratchpad de la sesión, fuera del worktree.

| Mutante | Qué hace | Resultado | Tiempo del subconjunto |
|---|---|---|---|
| (sin mutar) | — | `664 passed` | 527,3 s |
| #12 `!= 1` | destino único ⇒ `None` (404); varios ⇒ uno al azar (307); ninguno ⇒ `set.pop()` vacío ⇒ `KeyError` | **13 failed**, todos en `test_f050_portal.py` (R14 ×7, R15 ×6) | 598,5 s |
| #13 `== 2` | destino único ⇒ 404; dos ⇒ 307 a uno de ellos | **9 failed** en `test_f050_portal.py` (R14 ×7, R15 ×2) | 433,1 s |
| #20 `-` | `str - str` ⇒ `TypeError` al construir la redirección | **4 failed** en `test_f050_portal.py` (R14) | 337,1 s |

**Ninguno es un bucle ni un cuelgue.** Ninguno redirige a una clave sin líneas: el 307 solo
apunta a claves que `get_worker` sirve (mismos filtros de activa y no borrada), y el único
mutante de la muestra que sí redirige en bucle (#19, `if destino is None` ⇒
`/trabajadores/None`, que vuelve a no tener líneas) salió **muerto** en la campaña, sin
timeout (el cliente de pruebas sigue un número acotado de redirecciones). Los tres fallan en segundos dentro de `test_f050_portal.py` (aislado, #20 cae en
21 s con `-x`).

Por qué la campaña los dio por timeout: con `-x` un mutante que solo matan los tests de F-050
corre casi toda la suite antes de llegar a `test_f050_portal.py` (alfabéticamente al final),
así que tarda lo mismo que la línea base (519,6 s) y queda a merced de la carga de la
máquina frente al tope de 1040 s. La variación medida aquí lo confirma: el **mismo**
subconjunto tardó entre 337 y 598 s según el momento (factor 1,8), sin cambiar nada más que
el mutante. Es el mismo diagnóstico que los 14 timeouts de F-046 (contención, no bucle).

Decisión: **los tres cuentan como detectados** (muertos por tests existentes de R14/R15, con
la traza de arriba); sin test nuevo.

## Balance tras el análisis

20 evaluados: **13 muertos + 3 timeouts detectados + 1 superviviente matado con test nuevo
(#16) = 17 detectados; 3 equivalentes justificados (#7, #9, #11)**. 0 bugs de producción.

