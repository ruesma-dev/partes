<!-- progress/mutacion_F-077.md -->
# F-077 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-077 --workers 3` el 2026-11-19 13:18.

## Alcance

Origen del diff: **rama** (`9925fa12022a54c080f0609aaf0748b3c8b44a63` .. `feature/F-077-sesame-directo-sin-pasarela`).

| Fichero | Líneas en alcance | Mutantes generados |
|---|---|---|
| `services/partes-front/application/services/calendario_provider.py` | 14 | 3 |
| `services/partes-front/config/logging_config.py` | 2 | 0 — sin mutantes |
| `services/partes-front/config/settings.py` | 15 | 1 |
| `services/partes-front/interface_adapters/web/app.py` | 13 | 0 — sin mutantes |
| `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py` | 1 | 0 — sin mutantes |
| `services/partes-persistencia/application/services/refresco_festivos.py` | 3 | 0 — sin mutantes |
| `services/partes-persistencia/config/logging_config.py` | 3 | 0 — sin mutantes |
| `services/partes-persistencia/config/settings.py` | 24 | 9 |
| `services/partes-persistencia/contrastar_festivos_sesame.py` | 51 | 11 |
| `services/partes-persistencia/infrastructure/calendario/tabla_calendario_laboral.py` | 1 | 0 — sin mutantes |
| `services/partes-persistencia/infrastructure/sesame/festivos_sesame_hr.py` | 131 | 31 |
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py` | 284 | 85 |
| `services/partes-persistencia/interface_adapters/api/app.py` | 23 | 1 |
| **Total** | **565** | **141** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 141 |
| Mutantes evaluados | 85 |
| Muertos | 73 |
| Supervivientes | 12 (todos medidos: sin mapa no se poda) |
| Timeouts | 0 |
| Indeterminados | 0 |
| Timeouts repasados en serie | 1 — 1 con veredicto tras el repaso, 0 en timeout todavía |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 7791.3 s |
| SHA de HEAD medido | `11d32fc3ce0071bbac53be70ea35cd8b924c9af7` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-077_tu009n26/wk_0/services/partes-front` | 840.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-077_tu009n26/wk_0/services/partes-persistencia` | 51.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-077_tu009n26/wk_1/services/partes-front` | 848.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-077_tu009n26/wk_1/services/partes-persistencia` | 51.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-077_tu009n26/wk_2/services/partes-front` | 839.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-077_tu009n26/wk_2/services/partes-persistencia` | 53.4 |
| Media por mutante evaluado (s) | 91.7 |
| Timeout efectivo por mutante (s) | 1697 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 600 |
| Workers | 3 |
| Un mutante por línea | sí — 141 generados → 85 candidatos, uno por línea |
| Muestreo | no: campaña completa (85 candidatos ≤ tope 100 del nivel `critico`) |
| Selección de tests | desactivada (por defecto): todo con la suite entera, como la 1.9.0 |
| SHA del mapa | n/d |
| Medición del mapa (s) | n/d |
| Tests en la suite | n/d |
| Tamaño medio del subconjunto | n/d |
| Revalidados con la suite entera | n/d |
| Subconjuntos descartados | n/d |
| Podados (sin ejecutar) | n/d |
| Tiempo ahorrado por la poda (s) — derivado: podados × línea base | n/d |
| Media por mutante juzgado con la suite entera (s) | 66.7 (86 mutantes) |

## Pasada de campaña (T16, 2026-11-19)

12 supervivientes: **9 muertos con test** (n.º 1, 3, 5–8, 10–12; commit `dbecb3e`, muerte reproducida a mano mutante por mutante) y **3 equivalentes pendientes de aceptación del humano** (n.º 2, 4 y 9). Sin código de producción tocado. Script de reproducción: `C:/Users/pgris/AppData/Local/Temp/claude/df60977b71b41004/e7e805c0-0ecb-4470-8b9f-c7a943e77b59/scratchpad/repro.py`.

## Cómo se juzgó

- Cada mutante con la **suite entera**, como en la 1.9.0: la selección de tests está apagada por defecto (en la suite del propio arnés costó más de lo que ahorró). Se enciende con `--con-seleccion` en la orden o con `mutacion.seleccion_de_tests: true` en `harness/rigor.local.json`; la orden manda sobre la clave.


## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-persistencia/config/settings.py:181` [entero]

- Original: `sesame_timeout_s: float = Field(10.0, alias="SESAME_TIMEOUT_S", gt=0)`
- Mutado:   `sesame_timeout_s: float = Field(10.0, alias="SESAME_TIMEOUT_S", gt=1)`
- Juicio: MEDIDO

#### Análisis

> Por qué no lo cazaba: `test_f077_r16_timeout_configurable_y_positivo` probaba 4.5 (válido) y 0/-1 (inválidos); ningún valor en (0, 1].
> Decisión: **test reforzado** (design 5.3, `gt=0`): `SESAME_TIMEOUT_S=0.5` arranca y vale 0.5. Reproducido a mano (`scratchpad/repro.py`: aplica el mutante, ejecuta el test, revierte): mutante `1 failed`, original `1 passed`. **MUERTO.**

### 2. `services/partes-persistencia/infrastructure/sesame/festivos_sesame_hr.py:75` [veracidad]

- Original: `if empleado is None:`
- Mutado:   `if not empleado:`
- Juicio: MEDIDO

#### Análisis

> Por qué no lo caza nadie: `indice.get(dni_norm)` da `None` o un `EmpleadoSesame`, dataclass sin `__bool__` ni `__len__`, así que siempre es verdadero: `not empleado` ⇔ `empleado is None` para todo valor posible.
> Decisión: **equivalente** (pendiente de aceptación del humano). Con el mutante, las 39 pruebas de `test_f077_festivos_hr.py` + `test_f077_ingesta_hr.py` pasan.

### 3. `services/partes-persistencia/infrastructure/sesame/festivos_sesame_hr.py:86` [veracidad]

- Original: `if (self._corte_hasta is not None`
- Mutado:   `if (self._corte_hasta`
- Juicio: MEDIDO

#### Análisis

> Por qué no lo cazaba: solo difiere si `_corte_hasta == 0.0` exacto; el `Reloj` de los tests arranca en 1000. Con `time.monotonic` (5.2), de origen indefinido según Python, un corte que acaba en 0.0 es posible: el mutante lo saltaría y llamaría a Sesame en plena ventana (R14).
> Decisión: **test nuevo** `test_f077_r14_el_corte_no_depende_del_origen_del_reloj` (reloj en -60, corte hasta 0.0, a -30 da `corte` sin red). Reproducido a mano (`scratchpad/repro.py`: aplica el mutante, ejecuta el test, revierte): mutante `1 failed`, original `1 passed`. **MUERTO.**

### 4. `services/partes-persistencia/infrastructure/sesame/festivos_sesame_hr.py:115` [veracidad]

- Original: `if previo is None:`
- Mutado:   `if not previo:`
- Juicio: MEDIDO

#### Análisis

> Por qué no lo caza nadie: `previo` es `None` o un `EmpleadoSesame` (dataclass siempre verdadero, como en el n.º 2): `not previo` ⇔ `previo is None`.
> Decisión: **equivalente** (pendiente de aceptación del humano). Con el mutante, las 39 pruebas del adaptador y la ingesta pasan.

### 5. `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:57` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué no lo cazaba: ningún test asignaba un campo ni hasheaba un `FestivoDia`.
> Decisión: **test nuevo** `test_f077_los_datos_del_cliente_son_inmutables_y_hashables` (design 5.1, `frozen=True`; el índice de R11 se comparte entre llamadas e hilos): asignar da `FrozenInstanceError` y la instancia es hasheable. Reproducido a mano (`scratchpad/repro.py`: aplica el mutante, ejecuta el test, revierte): mutante `1 failed, 2 passed` (cae el caso `FestivoDia`), original `3 passed`. **MUERTO.**

### 6. `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:64` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué no lo cazaba: como el n.º 5, para `EmpleadoSesame`.
> Decisión: **mismo test nuevo**, caso `EmpleadoSesame`. Reproducido a mano (`scratchpad/repro.py`: aplica el mutante, ejecuta el test, revierte): mutante `1 failed, 2 passed`, original `3 passed`. **MUERTO.**

### 7. `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:72` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`
- Juicio: MEDIDO

#### Análisis

> Por qué no lo cazaba: como el n.º 5, para `CalendarioSesame`.
> Decisión: **mismo test nuevo**, caso `CalendarioSesame`. Reproducido a mano (`scratchpad/repro.py`: aplica el mutante, ejecuta el test, revierte): mutante `1 failed, 2 passed`, original `3 passed`. **MUERTO.**

### 8. `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:90` [entero]

- Original: `tope_filas: int = 20_000,`
- Mutado:   `tope_filas: int = 20001,`
- Juicio: MEDIDO

#### Análisis

> Por qué no lo cazaba: los tests del tope pasaban `tope_filas=4/5` explícito; el valor por defecto no lo fijaba nadie.
> Decisión: **test nuevo** `test_f077_r2_el_tope_por_defecto_es_de_20000_filas` (design 5.1, `tope_filas: int = 20_000`; R2): 20 000 filas pasan, 20 001 son fallo. Reproducido a mano (`scratchpad/repro.py`: aplica el mutante, ejecuta el test, revierte): mutante `1 failed`, original `1 passed`. **MUERTO.**

### 9. `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:107` [entero]

- Original: `self.ultimas_paginas = 0`
- Mutado:   `self.ultimas_paginas = 1`
- Juicio: MEDIDO

#### Análisis

> Por qué no lo caza nadie: el único lector de `ultimas_paginas` es el log del índice (`festivos_sesame_hr.py:124`, R12), que solo se escribe tras un `empleados()` que ha vuelto bien; y `_paginado` asigna `ultimas_paginas = pagina` (≥ 1) justo antes de todo `return`. El valor inicial nunca llega a leerse en ningún camino observable; un test sobre él solo existiría para el mutante.
> Decisión: **equivalente en comportamiento observable** (pendiente de aceptación del humano). Con el mutante, las 129 pruebas de cliente, adaptador y contraste pasan.

### 10. `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:160` [veracidad]

- Original: `if dias is None:`
- Mutado:   `if not dias:`
- Juicio: MEDIDO

#### Análisis

> Por qué no lo cazaba: ningún calendario traía `daysOff` presente pero vacío junto a un `dayOff`; el mutante caería a `dayOff`.
> Decisión: **test nuevo** `test_f077_r8_days_off_presente_manda_aunque_venga_vacio` (R8: los días de `daysOff`, `dayOff` solo si no viene `daysOff`; lectura literal, que el humano puede revisar). Reproducido a mano (`scratchpad/repro.py`: aplica el mutante, ejecuta el test, revierte): mutante `1 failed`, original `1 passed`. **MUERTO.**

### 11. `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:182` [veracidad]

- Original: `if cuerpo is None:`
- Mutado:   `if not cuerpo:`
- Juicio: MEDIDO

#### Análisis

> Por qué no lo cazaba: los cuerpos raros del test eran verdaderos (`["no","es","objeto"]`); con un 200 de cuerpo `[]` o `""` el mutante dice «HTTP 404», un estado que no ha pasado.
> Decisión: **test reforzado** `test_f077_r2_un_cuerpo_sin_forma_de_listado_es_fallo` con `[]` y `""` y el texto exacto `sesame cuerpo sin listado en …` (R5: el texto da el estado real; DA6: el 404 tiene significado propio). Reproducido a mano (`scratchpad/repro.py`: aplica el mutante, ejecuta el test, revierte): mutante `2 failed, 2 passed`, original `4 passed`. **MUERTO.**

### 12. `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:262` [aritmetico]

- Original: `return float(1 + intento)`
- Mutado:   `return float(1 - intento)`
- Juicio: MEDIDO

#### Análisis

> Por qué no lo cazaba: el `Retry-After` negativo/NaN solo se probaba en el intento 0, donde `1 + 0 == 1 - 0`.
> Decisión: **test nuevo** `test_f077_r3_retry_after_negativo_o_nan_es_1_mas_intento` (R3: no es una espera válida ⇒ `1 + intento`), dos reintentos: esperas `[1.0, 2.0]`. Reproducido a mano (`scratchpad/repro.py`: aplica el mutante, ejecuta el test, revierte): mutante `2 failed`, original `2 passed`. **MUERTO.**

## No muertos: código de salida

| Fichero:línea | Operador | Veredicto | Código |
|---|---|---|---|
| `services/partes-persistencia/config/settings.py:181` | entero | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/festivos_sesame_hr.py:75` | veracidad | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/festivos_sesame_hr.py:86` | veracidad | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/festivos_sesame_hr.py:115` | veracidad | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:57` | booleano | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:64` | booleano | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:72` | booleano | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:90` | entero | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:107` | entero | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:160` | veracidad | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:182` | veracidad | superviviente | 0 |
| `services/partes-persistencia/infrastructure/sesame/sesame_hr_client.py:262` | aritmetico | superviviente | 0 |

## Ficheros sin mutantes

Cada uno tiene líneas en alcance y el generador no ha sacado de ellas ni un mutante: la campaña no las ha juzgado. Declara por qué no hay nada que mutar (solo declaraciones, cadenas, imports) o qué test de la fase RED cubre el cambio. El reviewer hace la prueba de control (`generar_mutantes` sin exclusión de alcance) y ninguna declaración puede quedarse en `PENDIENTE` al cerrar la feature.

### `services/partes-front/config/logging_config.py` — 2 líneas en alcance, 0 mutantes

#### Declaración

> Solo cambia un comentario (el motivo de bajar `httpx` a WARNING): nada que mutar.

### `services/partes-front/interface_adapters/web/app.py` — 13 líneas en alcance, 0 mutantes

#### Declaración

> Sin operadores mutables: se quita el import y el cableado de `SesameApiClient`, cambian dos textos de log y `cliente=`/`ttl_seconds=` pasan a `activo=settings.sesame_enabled`; fuera `jornada_contrato`. Lo cubren `services/partes-front/tests/test_f077_sin_sesame_sv4.py` y `test_f032_wiring_sv4.py` (log `CABLEADO`/`DESACTIVADO` y el proveedor sin cliente).

### `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py` — 1 líneas en alcance, 0 mutantes

#### Declaración

> Solo docstring («sesame-api» ⇒ «Sesame HR»): nada que mutar.

### `services/partes-persistencia/application/services/refresco_festivos.py` — 3 líneas en alcance, 0 mutantes

#### Declaración

> Solo docstring del contrato `None` (DNI fuera del índice): nada que mutar.

### `services/partes-persistencia/config/logging_config.py` — 3 líneas en alcance, 0 mutantes

#### Declaración

> Solo un comentario (motivo de bajar `httpx` a WARNING, R18): nada que mutar.

### `services/partes-persistencia/infrastructure/calendario/tabla_calendario_laboral.py` — 1 líneas en alcance, 0 mutantes

#### Declaración

> Solo docstring («sesame-api» ⇒ «Sesame»): nada que mutar.

