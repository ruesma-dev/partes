<!-- progress/mutacion_F-015.md -->
# F-015 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-015` el 2026-08-19 14:16.

## Alcance

Origen del diff: **rama** (`cf77e6aaa889c5fc67e25cd6f58f334695648e4f` .. `feature/F-015-jornada-semanal-candef`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/jornada_provider.py` | 161 |
| `services/partes-front/application/services/jornada_resolver.py` | 246 |
| `services/partes-front/config/settings.py` | 15 |
| `services/partes-front/infrastructure/database/orm_models.py` | 86 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 31 |
| `services/partes-front/interface_adapters/web/app.py` | 150 |
| `services/partes-persistencia/application/services/jornada_resolver.py` | 242 |
| `services/partes-persistencia/application/services/recurso_conciliador.py` | 339 |
| `services/partes-persistencia/config/settings.py` | 18 |
| `services/partes-persistencia/domain/ports/jornada_empleado_port.py` | 42 |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | 86 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_jornada_repository.py` | 72 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 49 |
| `services/partes-persistencia/interface_adapters/api/app.py` | 33 |
| **Total** | **1570** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 259 |
| Mutantes evaluados | 259 |
| Muertos | 237 |
| Supervivientes | 22 |
| Timeouts | 0 |
| Tiempo total | 1300.2 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/jornada_provider.py:123` [comparacion]

- Original: `self._ttl > 0 and (ahora - self._cache[0]) < self._ttl`
- Mutado:   `self._ttl >= 0 and (ahora - self._cache[0]) < self._ttl`

#### Análisis

**Mutante EQUIVALENTE.** `self._ttl > 0` es redundante: con `ttl = 0` la segunda condicion (`ahora - cache < 0`) ya es falsa siempre, asi que se relee por los dos caminos. El comportamiento correcto SI esta fijado (`test_f015_r17_sv4_un_ttl_de_cero_desactiva_la_cache` y `..._un_ttl_de_uno_si_cachea`), pero esos tests no pueden distinguir las dos escrituras de una guarda que no decide nada.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 2. `services/partes-front/application/services/jornada_provider.py:123` [comparacion]

- Original: `self._ttl > 0 and (ahora - self._cache[0]) < self._ttl`
- Mutado:   `self._ttl > 0 and (ahora - self._cache[0]) <= self._ttl`

#### Análisis

**Mutante EQUIVALENTE.** `<` y `<=` solo difieren si el tiempo transcurrido es EXACTAMENTE igual al TTL, con la resolucion del reloj del sistema. No es un estado construible de forma estable, y en los dos casos la entrada esta igual de vigente o igual de caducada.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 3. `services/partes-front/application/services/jornada_resolver.py:96` [logico]

- Original: `if texto is None or not str(texto).strip():`
- Mutado:   `if texto is None and not str(texto).strip():`

#### Análisis

**Mutante EQUIVALENTE, medido.** Con `and` se deja de cortocircuitar, pero `None` y `""` acaban igualmente en `ValueError` unas lineas mas abajo (`"None"` no tiene `:`; `""` produce un par vacio). Cambia el TEXTO del mensaje, no el contrato: el arranque se cae igual. Comprobado con 19 cadenas de entrada comparando resultado y tipo de excepcion: **0 diferencias**.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 4. `services/partes-front/application/services/jornada_resolver.py:150` [comparacion]

- Original: `if abs(float(clave) - c) <= _EPS:`
- Mutado:   `if abs(float(clave) - c) < _EPS:`

#### Análisis

**Mutante EQUIVALENTE, medido.** Para que `<` y `<=` difieran haria falta una diferencia en coma flotante de EXACTAMENTE 1e-9 h (3,6 microsegundos de jornada): no es construible de forma estable ni corresponde a ningun dato que llegue de Sigrid. Comprobado sobre la misma malla, con un candef de `8.0000000001` puesto a proposito junto a la tolerancia: **105 216 + 122 752 combinaciones, 0 diferencias**.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 5. `services/partes-front/application/services/jornada_resolver.py:268` [comparacion]

- Original: `if d.weekday() >= 5:`
- Mutado:   `if d.weekday() > 5:`

#### Análisis

**Mutante EQUIVALENTE, medido.** `es_ultimo_laborable` ya descarta sabado y domingo por su propia guarda, asi que un sabado laborable acaba valiendo `c` por los dos caminos. Comprobado cargando la version integra y la mutada como modulos independientes y comparando el `DetalleJornada` completo sobre 3 anos x 5 calendarios x 8 candef x 4 excepciones, en las DOS copias: **175 360 + 122 752 combinaciones, 0 diferencias**. La rama se conserva porque R13 la enumera explicitamente (paso 2) y hace legible la regla.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 6. `services/partes-front/application/services/jornada_resolver.py:268` [entero]

- Original: `if d.weekday() >= 5:`
- Mutado:   `if d.weekday() >= 6:`

#### Análisis

**Mutante EQUIVALENTE, medido.** `es_ultimo_laborable` ya descarta sabado y domingo por su propia guarda, asi que un sabado laborable acaba valiendo `c` por los dos caminos. Comprobado cargando la version integra y la mutada como modulos independientes y comparando el `DetalleJornada` completo sobre 3 anos x 5 calendarios x 8 candef x 4 excepciones, en las DOS copias: **175 360 + 122 752 combinaciones, 0 diferencias**. La rama se conserva porque R13 la enumera explicitamente (paso 2) y hace legible la regla.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 7. `services/partes-front/application/services/jornada_resolver.py:272` [comparacion]

- Original: `if abs(resto - c) <= _EPS:`
- Mutado:   `if abs(resto - c) < _EPS:`

#### Análisis

**Mutante EQUIVALENTE, medido.** Para que `<` y `<=` difieran haria falta una diferencia en coma flotante de EXACTAMENTE 1e-9 h (3,6 microsegundos de jornada): no es construible de forma estable ni corresponde a ningun dato que llegue de Sigrid. Comprobado sobre la misma malla, con un candef de `8.0000000001` puesto a proposito junto a la tolerancia: **105 216 + 122 752 combinaciones, 0 diferencias**.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 8. `services/partes-front/interface_adapters/web/app.py:638` [logico]

- Original: `if not (_day.in_period and not _day.is_weekend`
- Mutado:   `if not (_day.in_period or not _day.is_weekend`

#### Análisis

**Mutante EQUIVALENTE, comprobado.** La primera hipotesis fue que SI era un hueco (un dia arrastrado de otro mes podria marcarse) y se escribio el test para cazarlo: **no lo mato**. La razon esta en `calendar_builder.py:199` — `agg = per_day.get(iso, {}) if in_period else {}`: las celdas fuera del periodo llevan SIEMPRE 0 h, y las de fin de semana o festivo tienen jornada 0, asi que `0.0 < horas < jornada` no se cumple nunca por ninguna de las tres vias. Las tres guardas son redundantes dado ese invariante. Los tests se conservan (`test_f015_r24_un_dia_arrastrado_de_otro_mes_no_genera_aviso` y su control en el periodo propio) porque documentan la intencion y saltarian el dia que `build_calendar` deje de anular esas celdas.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 9. `services/partes-front/interface_adapters/web/app.py:639` [logico]

- Original: `and not _day.is_holiday and _day.date_iso):`
- Mutado:   `or not _day.is_holiday and _day.date_iso):`

#### Análisis

**Mutante EQUIVALENTE, comprobado.** La primera hipotesis fue que SI era un hueco (un dia arrastrado de otro mes podria marcarse) y se escribio el test para cazarlo: **no lo mato**. La razon esta en `calendar_builder.py:199` — `agg = per_day.get(iso, {}) if in_period else {}`: las celdas fuera del periodo llevan SIEMPRE 0 h, y las de fin de semana o festivo tienen jornada 0, asi que `0.0 < horas < jornada` no se cumple nunca por ninguna de las tres vias. Las tres guardas son redundantes dado ese invariante. Los tests se conservan (`test_f015_r24_un_dia_arrastrado_de_otro_mes_no_genera_aviso` y su control en el periodo propio) porque documentan la intencion y saltarian el dia que `build_calendar` deje de anular esas celdas.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 10. `services/partes-front/interface_adapters/web/app.py:639` [logico]

- Original: `and not _day.is_holiday and _day.date_iso):`
- Mutado:   `and not _day.is_holiday or _day.date_iso):`

#### Análisis

**Mutante EQUIVALENTE, comprobado.** La primera hipotesis fue que SI era un hueco (un dia arrastrado de otro mes podria marcarse) y se escribio el test para cazarlo: **no lo mato**. La razon esta en `calendar_builder.py:199` — `agg = per_day.get(iso, {}) if in_period else {}`: las celdas fuera del periodo llevan SIEMPRE 0 h, y las de fin de semana o festivo tienen jornada 0, asi que `0.0 < horas < jornada` no se cumple nunca por ninguna de las tres vias. Las tres guardas son redundantes dado ese invariante. Los tests se conservan (`test_f015_r24_un_dia_arrastrado_de_otro_mes_no_genera_aviso` y su control en el periodo propio) porque documentan la intencion y saltarian el dia que `build_calendar` deje de anular esas celdas.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 11. `services/partes-front/interface_adapters/web/app.py:641` [comparacion]

- Original: `if 0.0 < (_day.normal_h or 0.0) < (`
- Mutado:   `if 0.0 < (_day.normal_h or 0.0) <= (`

#### Análisis

**Mutante EQUIVALENTE.** La comparacion es contra `jornada - 1e-9`, asi que el propio epsilon ya separa `<` de `<=`: para distinguirlos harian falta unas horas que valgan exactamente `jornada - 1e-9`. El borde que SI importa —horas iguales a la jornada del dia, que no debe marcarse— esta cubierto por `test_f015_r24_un_dia_con_la_jornada_justa_no_se_marca`.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 12. `services/partes-front/interface_adapters/web/app.py:661` [logico]

- Original: `_dia_kpi or date.today(), candef=_cd_real,`
- Mutado:   `_dia_kpi and date.today(), candef=_cd_real,`

#### Análisis

**Mutante EQUIVALENTE, y explica un detalle del diseno.** El KPI solo lee `semanal` y `origen`, que salen de la excepcion o del mapa y NO dependen de la fecha; la excepcion se resuelve aparte, con `_dia_kpi`, y eso si esta fijado (`test_f015_r25_el_kpi_resuelve_la_excepcion_con_el_periodo_que_se_ve`). Esa fecha es relleno para un parametro obligatorio cuyo valor no influye en lo que se ensena.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 13. `services/partes-persistencia/application/services/jornada_resolver.py:85` [logico]

- Original: `if texto is None or not str(texto).strip():`
- Mutado:   `if texto is None and not str(texto).strip():`

#### Análisis

**Mutante EQUIVALENTE, medido.** Con `and` se deja de cortocircuitar, pero `None` y `""` acaban igualmente en `ValueError` unas lineas mas abajo (`"None"` no tiene `:`; `""` produce un par vacio). Cambia el TEXTO del mensaje, no el contrato: el arranque se cae igual. Comprobado con 19 cadenas de entrada comparando resultado y tipo de excepcion: **0 diferencias**.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 14. `services/partes-persistencia/application/services/jornada_resolver.py:139` [comparacion]

- Original: `if abs(float(clave) - c) <= _EPS:`
- Mutado:   `if abs(float(clave) - c) < _EPS:`

#### Análisis

**Mutante EQUIVALENTE, medido.** Para que `<` y `<=` difieran haria falta una diferencia en coma flotante de EXACTAMENTE 1e-9 h (3,6 microsegundos de jornada): no es construible de forma estable ni corresponde a ningun dato que llegue de Sigrid. Comprobado sobre la misma malla, con un candef de `8.0000000001` puesto a proposito junto a la tolerancia: **105 216 + 122 752 combinaciones, 0 diferencias**.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 15. `services/partes-persistencia/application/services/jornada_resolver.py:257` [comparacion]

- Original: `if d.weekday() >= 5:`
- Mutado:   `if d.weekday() > 5:`

#### Análisis

**Mutante EQUIVALENTE, medido.** `es_ultimo_laborable` ya descarta sabado y domingo por su propia guarda, asi que un sabado laborable acaba valiendo `c` por los dos caminos. Comprobado cargando la version integra y la mutada como modulos independientes y comparando el `DetalleJornada` completo sobre 3 anos x 5 calendarios x 8 candef x 4 excepciones, en las DOS copias: **175 360 + 122 752 combinaciones, 0 diferencias**. La rama se conserva porque R13 la enumera explicitamente (paso 2) y hace legible la regla.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 16. `services/partes-persistencia/application/services/jornada_resolver.py:257` [entero]

- Original: `if d.weekday() >= 5:`
- Mutado:   `if d.weekday() >= 6:`

#### Análisis

**Mutante EQUIVALENTE, medido.** `es_ultimo_laborable` ya descarta sabado y domingo por su propia guarda, asi que un sabado laborable acaba valiendo `c` por los dos caminos. Comprobado cargando la version integra y la mutada como modulos independientes y comparando el `DetalleJornada` completo sobre 3 anos x 5 calendarios x 8 candef x 4 excepciones, en las DOS copias: **175 360 + 122 752 combinaciones, 0 diferencias**. La rama se conserva porque R13 la enumera explicitamente (paso 2) y hace legible la regla.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 17. `services/partes-persistencia/application/services/jornada_resolver.py:261` [comparacion]

- Original: `if abs(resto - c) <= _EPS:`
- Mutado:   `if abs(resto - c) < _EPS:`

#### Análisis

**Mutante EQUIVALENTE, medido.** Para que `<` y `<=` difieran haria falta una diferencia en coma flotante de EXACTAMENTE 1e-9 h (3,6 microsegundos de jornada): no es construible de forma estable ni corresponde a ningun dato que llegue de Sigrid. Comprobado sobre la misma malla, con un candef de `8.0000000001` puesto a proposito junto a la tolerancia: **105 216 + 122 752 combinaciones, 0 diferencias**.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 18. `services/partes-persistencia/application/services/recurso_conciliador.py:631` [comparacion]

- Original: `if (delta > 0 and disponible + 1e-9 < delta) or (`
- Mutado:   `if (delta >= 0 and disponible + 1e-9 < delta) or (`

#### Análisis

**Mutante EQUIVALENTE.** `delta == 0` no llega nunca a esta linea: el dia que cuadra sale antes por `if abs(delta) <= 1e-9: continue`. Mover el operador para incluir el cero no puede cambiar nada.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 19. `services/partes-persistencia/application/services/recurso_conciliador.py:631` [comparacion]

- Original: `if (delta > 0 and disponible + 1e-9 < delta) or (`
- Mutado:   `if (delta > 0 and disponible + 1e-9 <= delta) or (`

#### Análisis

**Mutante EQUIVALENTE.** `<` y `<=` solo difieren si `disponible + 1e-9` vale EXACTAMENTE `delta`, lo que exigiria unas horas separadas por la tolerancia justa. El borde real —sobra tanto como hay ajustable, y por tanto SI se ajusta— esta cubierto por `test_f015_r32_con_lo_justo_para_recortar_si_se_ajusta`.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 20. `services/partes-persistencia/application/services/recurso_conciliador.py:632` [comparacion]

- Original: `delta < 0 and not orden`
- Mutado:   `delta <= 0 and not orden`

#### Análisis

**Mutante EQUIVALENTE.** `delta == 0` no llega nunca a esta linea: el dia que cuadra sale antes por `if abs(delta) <= 1e-9: continue`. Mover el operador para incluir el cero no puede cambiar nada.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 21. `services/partes-persistencia/application/services/recurso_conciliador.py:632` [entero]

- Original: `delta < 0 and not orden`
- Mutado:   `delta < 1 and not orden`

#### Análisis

**Mutante EQUIVALENTE.** La segunda condicion solo se evalua si la primera no disparo; y con `not orden` (ninguna linea ajustable) y `delta > 0`, la primera ya dispara siempre porque `disponible` vale 0. El hueco de verdad de este grupo era `delta > 1` en la PRIMERA condicion, que dejaba ajustar a medias un dia descuadrado en menos de una hora: ese murio con `test_f015_r32_un_exceso_de_menos_de_una_hora_tambien_se_guarda`.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

### 22. `services/partes-persistencia/application/services/recurso_conciliador.py:727` [comparacion]

- Original: `if abs(detalle.horas - detalle.candef_efectivo) <= 1e-9:`
- Mutado:   `if abs(detalle.horas - detalle.candef_efectivo) < 1e-9:`

#### Análisis

**Mutante EQUIVALENTE.** Decide si la jornada del dia difiere del candef efectivo para anadir la marca de trazabilidad de R28. `<` y `<=` solo difieren si la diferencia vale exactamente 1e-9 h. Que la marca aparezca cuando debe y NO aparezca en el caso normal esta cubierto por `test_f015_r28_*`.

> Detalle y método de medición: `progress/impl_F-015.md`, §9.4.

