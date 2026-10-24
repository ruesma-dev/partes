<!-- progress/mutacion_F-060.md -->
# F-060 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-060` el 2026-10-24 17:12.

## Alcance

Origen del diff: **rama** (`09268570191989442d75b611357a26e028d27856` .. `feature/F-060-racha-incidencia-ciz-movil`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/racha_incidencia.py` | 250 |
| `services/partes-front/application/services/reparto_obras.py` | 4 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 169 |
| `services/partes-front/interface_adapters/web/app.py` | 2 |
| `services/partes-transfer/application/pipelines/registro_pipeline.py` | 103 |
| `services/partes-transfer/application/services/racha_ciz.py` | 139 |
| `services/partes-transfer/application/services/reglas_registro.py` | 10 |
| `services/partes-transfer/config/settings.py` | 7 |
| `services/partes-transfer/domain/models/registro_models.py` | 12 |
| `services/partes-transfer/infrastructure/sigrid/sigrid_write_client.py` | 78 |
| `services/partes-transfer/interface_adapters/api/app.py` | 2 |
| **Total** | **776** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 221 |
| Mutantes evaluados | 221 |
| Muertos | 204 |
| Supervivientes | 16 |
| Timeouts | 1 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 22626.0 s |
| SHA de HEAD medido | `1009cdb6adc6fb53343d4d0d5071745a3209a895` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-060_drtpl9cb/wk_0/services/partes-front` | 715.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-060_drtpl9cb/wk_0/services/partes-transfer` | 22.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-060_drtpl9cb/wk_1/services/partes-front` | 723.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-060_drtpl9cb/wk_1/services/partes-transfer` | 23.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-060_drtpl9cb/wk_2/services/partes-front` | 717.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-060_drtpl9cb/wk_2/services/partes-transfer` | 21.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-060_drtpl9cb/wk_3/services/partes-front` | 716.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-060_drtpl9cb/wk_3/services/partes-transfer` | 21.7 |
| Media por mutante evaluado (s) | 102.4 |
| Timeout efectivo por mutante (s) | 1448 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 300 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/racha_incidencia.py:65` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: ningún test intentaba asignar un campo de `LineaHist`; todos la construyen y la leen.
> Decisión: **hueco real, test nuevo.** `test_f060_valores_inmutables[objeto0]` (`test_f060_racha_incidencia.py`): asignar `clave` lanza `FrozenInstanceError`. Es un valor que el repositorio comparte entre las líneas de una persona.
> Con el mutante: `1 failed` (DID NOT RAISE FrozenInstanceError); sin él, en verde.
> Verificado a mano (sin relanzar la campaña): mutante aplicado al fichero, test ejecutado, fichero revertido byte a byte y árbol limpio.

### 2. `services/partes-front/application/services/racha_incidencia.py:77` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: ídem para `DecisionRacha`.
> Decisión: **hueco real, test nuevo.** `test_f060_valores_inmutables[objeto1]`: asignar `racha_registro_ids` lanza `FrozenInstanceError`.
> Con el mutante: `1 failed` (DID NOT RAISE FrozenInstanceError); sin él, en verde.
> Verificado a mano (sin relanzar la campaña): mutante aplicado al fichero, test ejecutado, fichero revertido byte a byte y árbol limpio.

### 3. `services/partes-front/application/services/racha_incidencia.py:83` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: ídem para `LineaRol`, que `colapsar` reparte entre grupos.
> Decisión: **hueco real, test nuevo.** `test_f060_valores_inmutables[objeto2]`: asignar `rol` lanza `FrozenInstanceError`.
> Con el mutante: `1 failed` (DID NOT RAISE FrozenInstanceError); sin él, en verde.
> Verificado a mano (sin relanzar la campaña): mutante aplicado al fichero, test ejecutado, fichero revertido byte a byte y árbol limpio.

### 4. `services/partes-front/application/services/racha_incidencia.py:136` [entero]

- Original: `f = int(linea.fecha_int or 0)`
- Mutado:   `f = int(linea.fecha_int or 1)`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: `int(fecha_int or 0)` frente a `or 1` solo difiere con fecha `None`/`0`.
> Decisión: **mutante equivalente — PENDIENTE DE ACEPTAR POR EL HUMANO.** `LineaHist.fecha_int` nunca es `None` ni `0`: el único productor es `ParteReviewRepository._historico` (`parte_repository.py:2366`, `fecha_int=int(reg.fecha_int)`) sobre filas filtradas por `fecha_int.between(desde, hasta)` (`:2345`), que excluye el NULL. Y aunque llegara una línea sin fecha a la regla pura, `0` y `1` caen fuera de todo rango que la regla compara: `ventana`/`hasta_delante` pasan D por `_fecha` (fecha válida, año >= 1), así que `desde >= 10101` atrás y `D + 1 >= 10102` delante. Ninguna salida de `decidir` ni de `aviso_desordenada` cambia.
> Comprobación: diferencial de 20.000 entradas al azar (fechas `None`/`0`/`1`, papelera, 1e-9 h, ids repetidos) original frente a mutante, `decidir` + `aviso_desordenada` (y `colapsar` para el 197): 80.000 comparaciones, todas iguales (script `diferencial.py` en el scratchpad de la sesión).

### 5. `services/partes-front/application/services/racha_incidencia.py:141` [comparacion]

- Original: `elif abs(float(linea.horas or 0.0)) > _EPSILON:`
- Mutado:   `elif abs(float(linea.horas or 0.0)) >= _EPSILON:`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: los tests de días a cero usaban `0.0` y `None`, no el borde `1e-9`; nadie fijaba que el épsilon es «cero» (como F-025).
> Decisión: **hueco real, test nuevo.** `test_f060_r4_horas_en_el_epsilon_no_es_trabajado`: V el 2, trabajo de 1e-9 h el 3 => el 4 es `fin`; con 2e-9 h, `inicio`.
> Con el mutante: `1 failed` (`assert 'inicio' == 'fin'`); sin él, en verde.
> Verificado a mano (sin relanzar la campaña): mutante aplicado al fichero, test ejecutado, fichero revertido byte a byte y árbol limpio.

### 6. `services/partes-front/application/services/racha_incidencia.py:172` [entero]

- Original: `if int(l.fecha_int or 0) in racha and l.es_incidencia`
- Mutado:   `if int(l.fecha_int or 1) in racha and l.es_incidencia`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: `int(l.fecha_int or 0) in racha` solo difiere con fecha `None`/`0`.
> Decisión: **mutante equivalente — PENDIENTE DE ACEPTAR POR EL HUMANO.** `LineaHist.fecha_int` nunca es `None` ni `0`: el único productor es `ParteReviewRepository._historico` (`parte_repository.py:2366`, `fecha_int=int(reg.fecha_int)`) sobre filas filtradas por `fecha_int.between(desde, hasta)` (`:2345`), que excluye el NULL. Y aunque llegara una línea sin fecha a la regla pura, `0` y `1` caen fuera de todo rango que la regla compara: `ventana`/`hasta_delante` pasan D por `_fecha` (fecha válida, año >= 1), así que `desde >= 10101` atrás y `D + 1 >= 10102` delante. `racha` solo contiene días de esos rangos, así que ni `0` ni `1` están nunca en ella.
> Comprobación: diferencial de 20.000 entradas al azar (fechas `None`/`0`/`1`, papelera, 1e-9 h, ids repetidos) original frente a mutante, `decidir` + `aviso_desordenada` (y `colapsar` para el 197): 80.000 comparaciones, todas iguales (script `diferencial.py` en el scratchpad de la sesión).

### 7. `services/partes-front/application/services/racha_incidencia.py:197` [comparacion]

- Original: `if (a.registro_id < b.registro_id and a.persona == b.persona`
- Mutado:   `if (a.registro_id <= b.registro_id and a.persona == b.persona`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: `<` frente a `<=` solo difiere cuando `a.registro_id == b.registro_id`.
> Decisión: **mutante equivalente — PENDIENTE DE ACEPTAR POR EL HUMANO.** Con ids iguales (sea la misma línea o dos con el mismo id) `raiz(b.registro_id)` y `raiz(a.registro_id)` consultan la MISMA clave de `padre`, así que la unión hace `padre[r] = r`: no cambia nada. Vale para cualquier entrada, no depende de invariantes de quien llama.
> Comprobación: diferencial de 20.000 entradas al azar (fechas `None`/`0`/`1`, papelera, 1e-9 h, ids repetidos) original frente a mutante, `decidir` + `aviso_desordenada` (y `colapsar` para el 197): 80.000 comparaciones, todas iguales (script `diferencial.py` en el scratchpad de la sesión).

### 8. `services/partes-front/application/services/racha_incidencia.py:227` [entero]

- Original: `hay = any(int(l.fecha_int or 0) == siguiente and l.activa`
- Mutado:   `hay = any(int(l.fecha_int or 1) == siguiente and l.activa`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: `int(l.fecha_int or 0) == siguiente` solo difiere con fecha `None`/`0`.
> Decisión: **mutante equivalente — PENDIENTE DE ACEPTAR POR EL HUMANO.** `LineaHist.fecha_int` nunca es `None` ni `0`: el único productor es `ParteReviewRepository._historico` (`parte_repository.py:2366`, `fecha_int=int(reg.fecha_int)`) sobre filas filtradas por `fecha_int.between(desde, hasta)` (`:2345`), que excluye el NULL. Y aunque llegara una línea sin fecha a la regla pura, `0` y `1` caen fuera de todo rango que la regla compara: `ventana`/`hasta_delante` pasan D por `_fecha` (fecha válida, año >= 1), así que `desde >= 10101` atrás y `D + 1 >= 10102` delante. `siguiente = min(delante) >= D + 1 >= 10102`, nunca `0` ni `1`.
> Comprobación: diferencial de 20.000 entradas al azar (fechas `None`/`0`/`1`, papelera, 1e-9 h, ids repetidos) original frente a mutante, `decidir` + `aviso_desordenada` (y `colapsar` para el 197): 80.000 comparaciones, todas iguales (script `diferencial.py` en el scratchpad de la sesión).

### 9. `services/partes-front/infrastructure/database/parte_repository.py:2302` [comparacion]

- Original: `and abs(float(r.horas or 0.0)) > 1e-9)`
- Mutado:   `and abs(float(r.horas or 0.0)) >= 1e-9)`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: el test de R10 con trabajo a cero usaba `0.0`; con 1e-9 h nadie miraba si la línea entraba en el histórico y llevaba aviso.
> Decisión: **hueco real, test nuevo.** `test_f060_r10_trabajo_en_el_epsilon_no_avisa` (`test_f060_aprobacion_racha.py`): V registrada el 5 y trabajo de 1e-9 h el 4 => sin aviso `racha_desordenada` y sin consulta del histórico.
> Con el mutante: `1 failed` (aparece un aviso `racha_desordenada: el 2026-10-05...` para la línea de 1e-9 h); sin él, en verde.
> Verificado a mano (sin relanzar la campaña): mutante aplicado al fichero, test ejecutado, fichero revertido byte a byte y árbol limpio.

### 10. `services/partes-front/infrastructure/database/parte_repository.py:2358` [comparacion]

- Original: `== int(persona[len("emp-"):]))`
- Mutado:   `!= int(persona[len("emp-"):]))`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: los tests de R6 cubrían DNI, `rec-` (recurso) y `nom-` (nombre leído), pero no la ficha sin DNI ni recurso (`emp-`). Hueco real, como apuntó el líder. Con `!=` la consulta trae las líneas de las DEMÁS fichas y `persona_de` las descarta todas: la persona pierde su propio histórico y todo `fin` sale `inicio` (no cruza con otro trabajador, pero rompe la racha).
> Decisión: **hueco real, test nuevo.** `test_f060_r6_sin_dni_ni_recurso_por_la_ficha`: ficha 77 sin DNI ni recurso con V el 1 y el 2, y la ficha 78 con V y trabajo el 1 => `persona_de` = `emp-77` y el 2 es `fin` con racha `[d1]` (sin las líneas de la 78).
> Con el mutante: `1 failed` (`assert ('inicio', []) == ('fin', [1])`); sin él, en verde.
> Verificado a mano (sin relanzar la campaña): mutante aplicado al fichero, test ejecutado, fichero revertido byte a byte y árbol limpio.

### 11. `services/partes-transfer/application/pipelines/registro_pipeline.py:481` [entero]

- Original: `d = decidir_fin(a.fecha_int, int(a.recurso_ide or 0), candidatas,`
- Mutado:   `d = decidir_fin(a.fecha_int, int(a.recurso_ide or 1), candidatas,`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: `int(a.recurso_ide or 0)` frente a `or 1` solo difiere con recurso nulo o 0.
> Decisión: **mutante equivalente — PENDIENTE DE ACEPTAR POR EL HUMANO.** Las acciones que mira el paso 6 bis son `escribir` (`registro_pipeline.py:465`) y toda acción `escribir` sale de `ReglasRegistro.decidir` DESPUÉS de `if not linea.recurso_ide: return omitir(...)` (`reglas_registro.py:141` para trabajo, `:217` para incidencias, incluido el `fin` con CIZ); la de `dedicacion` no es `escribir`, y nada reasigna `a.recurso_ide` después (`base` lo copia, `:122`). Así que ahí `a.recurso_ide` siempre es verdadero y `x or 0 == x or 1 == x`. No hay entrada de `ejecutar`/`preflight` que lo distinga; matarlo exigiría montar a mano una acción imposible.

### 12. `services/partes-transfer/application/pipelines/registro_pipeline.py:699` [entero]

- Original: `pos = (int(ls.pos) if int(ls.hmoide or 0) == hmoide`
- Mutado:   `pos = (int(ls.pos) if int(ls.hmoide or 1) == hmoide`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: `int(ls.hmoide or 0) == hmoide` frente a `or 1` solo difiere con `hmoide` nulo o 0 en la línea que se mueve.
> Decisión: **mutante equivalente — PENDIENTE DE ACEPTAR POR EL HUMANO.** `a.mover` solo se asigna con `decidir_fin` = `mover` (`registro_pipeline.py:486`), que exige `partes.get(int(elegida.hmoide or 0))` no nulo y En registro (`racha_ciz.py:128-133`). `partes` sale de `estados_de_partes(hmoides)` con `hmoides` solo verdaderos (`registro_pipeline.py:472`) y el cliente solo devuelve filas de `hmo.ide IN (...)` de ids verdaderos (`sigrid_write_client.py:730`): la clave 0 no existe, así que un CIZ sin parte es `parte_cerrado` (lo fija el test nuevo del superviviente 16) y nunca llega a la línea 699. Ahí `ls.hmoide` siempre es verdadero.

### 13. `services/partes-transfer/application/pipelines/registro_pipeline.py:704` [entero]

- Original: `paride=int(a.paride or 0), caaide=int(a.caa_ide),`
- Mutado:   `paride=int(a.paride or 1), caaide=int(a.caa_ide),`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: el único test del `UPDATE` con partida le ponía `partida_ide = 34`; ninguno movía un CIZ sin partida. `AccionLinea.paride` ya es `int(partida_ide or 0)` (`reglas_registro.py:123`), así que sin partida vale `0` y el mutante escribiría la partida 1 en Sigrid.
> Decisión: **hueco real, test nuevo.** `test_f060_r20_mover_sin_partida_escribe_paride_0` (`test_f060_pipeline_mover.py`): la sentencia `mover` lleva `paride = 0` y la fila movida queda con 0, como el INSERT de siempre.
> Con el mutante: `1 failed` (`assert 1 == 0`); sin él, en verde.
> Verificado a mano (sin relanzar la campaña): mutante aplicado al fichero, test ejecutado, fichero revertido byte a byte y árbol limpio.

### 14. `services/partes-transfer/application/services/racha_ciz.py:42` [entero]

- Original: `LIMITE_MOTIVO = 255`
- Mutado:   `LIMITE_MOTIVO = 256`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: el test de motivos comparaba con la constante `LIMITE_MOTIVO`, que muta a la vez; nadie fijaba el 255 de `parte_registro.sigrid_motivo` de sv4.
> Decisión: **hueco real, test nuevo.** `test_f060_motivo_recortado_a_255_exactos` (`test_f060_racha_ciz.py`): con un código de parte de 405 caracteres el motivo mide 255 literales y es el texto completo cortado en 255.
> Con el mutante: `1 failed` (`assert 256 == 255`); sin él, en verde.
> Verificado a mano (sin relanzar la campaña): mutante aplicado al fichero, test ejecutado, fichero revertido byte a byte y árbol limpio.

### 15. `services/partes-transfer/application/services/racha_ciz.py:49` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: ningún test intentaba cambiar una `DecisionFin`.
> Decisión: **hueco real, test nuevo.** `test_f060_decision_inmutable`: asignar `tipo` lanza `FrozenInstanceError`.
> Con el mutante: `1 failed` (DID NOT RAISE FrozenInstanceError); sin él, en verde.
> Verificado a mano (sin relanzar la campaña): mutante aplicado al fichero, test ejecutado, fichero revertido byte a byte y árbol limpio.

### 16. `services/partes-transfer/application/services/racha_ciz.py:128` [entero]

- Original: `parte = partes.get(int(elegida.hmoide or 0))`
- Mutado:   `parte = partes.get(int(elegida.hmoide or 1))`

#### Análisis (implementer, 2026-10-24)

> Por qué ningún test lo caza: ningún test daba a `decidir_fin` un CIZ sin `hmoide`; con `or 1` se cruzaría con el parte de ide 1 si estuviera en `partes`.
> Decisión: **hueco real, test nuevo.** `test_f060_r17_ciz_sin_parte_no_se_cruza_con_otro_parte`: CIZ anterior sin `hmoide` y `partes = {1: En registro}` => `parte_cerrado` (R17: un parte que no se leyó no se escribe a ciegas), motivo con «parte ?».
> Con el mutante: `1 failed` (`assert 'mover' == 'parte_cerrado'`); sin él, en verde.
> Verificado a mano (sin relanzar la campaña): mutante aplicado al fichero, test ejecutado, fichero revertido byte a byte y árbol limpio.

## Cierre del análisis (implementer, 2026-10-24)

**La campaña NO se ha relanzado** (ni entera ni parcial): los totales de arriba son los de
la campaña que lanzó el líder con 4 workers sobre `1009cdb`. Cada test nuevo se verificó
aplicando su mutante a mano, ejecutándolo (falla), revirtiendo y comprobando el fichero byte
a byte (script `mutar_a_mano.py` en el scratchpad de la sesión).

| Resultado | Supervivientes |
|---|---|
| Muertos con test nuevo (10) | 1, 2, 3, 5, 9, 10, 13, 14, 15, 16 |
| Equivalentes **PENDIENTES DE ACEPTAR POR EL HUMANO** (6) | 4, 6, 8 (`fecha_int or 0`, sv4), 7 (`<` / `<=`, sv4), 11 (`recurso_ide or 0`, sv5), 12 (`hmoide or 0`, sv5) |
| Timeout (1) | `racha_incidencia.py:191`: detectado (bucle infinito), ver «Timeouts» |

Sin cambios de código de producción: ningún análisis reveló un defecto.

## Timeouts

- `services/partes-front/application/services/racha_incidencia.py:191` [comparacion] while padre[i] != i: -> while padre[i] == i:

#### Análisis del timeout (implementer, 2026-10-24)

> Cuenta como **detectado**: con `==`, `raiz(i)` sobre una raíz (`padre[i] == i`, el estado
> inicial de todo `fin`) hace `i = padre[i]` = `i` para siempre. `colapsar` llama a `raiz`
> por cada `fin` (`racha_incidencia.py:205`), así que cualquier aprobación con un `fin` se
> cuelga: la suite no termina en verde, que es lo que el arnés registra como `timeout`.
> Verificado a mano: mutante aplicado y
> `test_f060_r7_varios_fin_de_una_racha_solo_el_ultimo` cortado a los 30 s sin terminar;
> revertido y árbol limpio. No se añade un test «que falle rápido»: haría falta
> `pytest-timeout` (no está en el manifiesto) o un hilo que se queda girando el resto de la
> suite; ninguno compensa para un mutante que ya no puede pasar en verde.

