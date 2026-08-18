<!-- progress/mutacion_F-003.md -->
# F-003 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-003` el 2026-08-15 22:56.

## Alcance

Origen del diff: **rama** (`43a35fe95a28cd250f0cc24950a878a61bc6b49d` .. `feature/F-003-sesame-festivos-jornada`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/calendario_provider.py` | 275 |
| `services/partes-front/application/services/jornada_resolver.py` | 51 |
| `services/partes-front/config/settings.py` | 30 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 13 |
| `services/partes-front/infrastructure/sesame/__init__.py` | 1 |
| `services/partes-front/infrastructure/sesame/sesame_api_client.py` | 206 |
| `services/partes-front/infrastructure/transfer/resultado_sigrid.py` | 16 |
| `services/partes-front/interface_adapters/web/app.py` | 288 |
| `services/partes-persistencia/application/services/jornada_resolver.py` | 44 |
| `services/partes-persistencia/application/services/recurso_conciliador.py` | 80 |
| `services/partes-persistencia/config/settings.py` | 26 |
| `services/partes-persistencia/domain/ports/parte_repository.py` | 5 |
| `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py` | 215 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 33 |
| `services/partes-persistencia/infrastructure/sesame/__init__.py` | 1 |
| `services/partes-persistencia/infrastructure/sesame/sesame_api_client.py` | 210 |
| `services/partes-persistencia/interface_adapters/api/app.py` | 43 |
| **Total** | **1537** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 211 |
| Mutantes evaluados | 211 |
| Muertos | 185 |
| Supervivientes | 26 |
| Timeouts | 0 |
| Tiempo total | 401.9 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/application/services/calendario_provider.py:84` [entero]

- Original: `ttl_seconds: int = 21600,`
- Mutado:   `ttl_seconds: int = 21601,`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (constante de ajuste).** El valor exacto es un parámetro de tuning, no una regla: 6 h de caché, 300 caracteres de cuerpo de error o 1 reintento de red. Un segundo o un carácter más no cambian ningún comportamiento observable, y fijarlo en un test convertiría un ajuste operativo en una rotura de la suite. Lo que SÍ está cubierto es el comportamiento que sostienen: que la caché caduca (`test_f003_r6_al_expirar_el_ttl_vuelve_a_preguntar`, `..._justo_en_el_ttl_la_entrada_ya_ha_caducado`), que el cuerpo del error se recorta (`test_f003_r1_el_cuerpo_del_error_se_recorta`) y que el transporte inyectado manda sobre el de red.

### 2. `services/partes-front/application/services/calendario_provider.py:222` [logico]

- Original: `_LOG_PREFIX, dni_norm or "(sin dni)", ano,`
- Mutado:   `_LOG_PREFIX, dni_norm and "(sin dni)", ano,`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (texto de log).** La mutación cae dentro de los argumentos de un `logger.*`: cambia lo que se lee en el log («(sin dni)» en vez del DNI, o cuántos identificadores se listan), no lo que el sistema hace. Ningún test lo caza porque ninguno afirma el texto literal de estas líneas, y no debe hacerlo: atarlas volvería la suite frágil sin proteger nada.
>
> Sí se afirma el contenido de UN log, el de wiring, porque ahí el log es la única evidencia de que la clave no se filtra (R20).

### 3. `services/partes-front/application/services/calendario_provider.py:230` [logico]

- Original: `_LOG_PREFIX, dni_norm or "(sin dni)", ano, len(mapa), fuente,`
- Mutado:   `_LOG_PREFIX, dni_norm and "(sin dni)", ano, len(mapa), fuente,`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (texto de log).** La mutación cae dentro de los argumentos de un `logger.*`: cambia lo que se lee en el log («(sin dni)» en vez del DNI, o cuántos identificadores se listan), no lo que el sistema hace. Ningún test lo caza porque ninguno afirma el texto literal de estas líneas, y no debe hacerlo: atarlas volvería la suite frágil sin proteger nada.
>
> Sí se afirma el contenido de UN log, el de wiring, porque ahí el log es la única evidencia de que la clave no se filtra (R20).

### 4. `services/partes-front/application/services/calendario_provider.py:249` [logico]

- Original: `_LOG_PREFIX, exc, dni_norm or "(sin dni)", ano,`
- Mutado:   `_LOG_PREFIX, exc, dni_norm and "(sin dni)", ano,`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (texto de log).** La mutación cae dentro de los argumentos de un `logger.*`: cambia lo que se lee en el log («(sin dni)» en vez del DNI, o cuántos identificadores se listan), no lo que el sistema hace. Ningún test lo caza porque ninguno afirma el texto literal de estas líneas, y no debe hacerlo: atarlas volvería la suite frágil sin proteger nada.
>
> Sí se afirma el contenido de UN log, el de wiring, porque ahí el log es la única evidencia de que la clave no se filtra (R20).

### 5. `services/partes-front/application/services/calendario_provider.py:255` [logico]

- Original: `_LOG_PREFIX, exc, dni_norm or "(sin dni)", ano,`
- Mutado:   `_LOG_PREFIX, exc, dni_norm and "(sin dni)", ano,`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (texto de log).** La mutación cae dentro de los argumentos de un `logger.*`: cambia lo que se lee en el log («(sin dni)» en vez del DNI, o cuántos identificadores se listan), no lo que el sistema hace. Ningún test lo caza porque ninguno afirma el texto literal de estas líneas, y no debe hacerlo: atarlas volvería la suite frágil sin proteger nada.
>
> Sí se afirma el contenido de UN log, el de wiring, porque ahí el log es la única evidencia de que la clave no se filtra (R20).

### 6. `services/partes-front/application/services/calendario_provider.py:263` [comparacion]

- Original: `if self._ttl <= 0:`
- Mutado:   `if self._ttl < 0:`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (guarda redundante).** Con `ttl = 0` el atajo deja de dispararse, pero la comprobación de abajo calcula `(ahora - ts) >= 0`, que es cierta siempre: la entrada se da por caducada igual y no hay caché. El comportamiento coincide, y está cubierto por `test_f003_r6_ttl_no_positivo_no_cachea` (que pasa con las dos versiones, precisamente porque son equivalentes). El otro extremo, que un TTL positivo sí cachee, lo fija `test_f003_r6_un_ttl_de_un_segundo_si_cachea`.

### 7. `services/partes-front/application/services/jornada_resolver.py:32` [logico]

- Original: `if candef is None or candef == "":`
- Mutado:   `if candef is None and candef == "":`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (otro camino, mismo resultado).** Con `and` la condición nunca se cumple (`None == ""` es falso), así que la ejecución sigue hasta `float(candef)`, que levanta `TypeError` con `None` y `ValueError` con `""`; ambas las captura el `except` de debajo y devuelve exactamente lo mismo. Los casos están cubiertos (`test_f003_r1{1,2}_regla_candef` con `None` y `..._no_numericos_son_no_informados` con `""`): pasan con el mutante porque el resultado ES el mismo.

### 8. `services/partes-front/infrastructure/database/parte_repository.py:1388` [entero]

- Original: `reg.sigrid_motivo = (motivo_ok or None) and motivo_ok[:255]`
- Mutado:   `reg.sigrid_motivo = (motivo_ok or None) and motivo_ok[:256]`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (truncado defensivo).** El recorte protege la columna `sigrid_motivo`, que es `String(255)`. El único motivo que se escribe por esta vía es `MOTIVO_SIN_SESAME`, de 74 caracteres, así que 255 o 256 dan el mismo resultado; hay un test que fija que la marca cabe en el campo (`test_f003_r25_la_marca_cabe_en_el_campo`). Cubrir la diferencia exigiría escribir un motivo de 256 caracteres que hoy nadie genera.

### 9. `services/partes-front/infrastructure/database/parte_repository.py:1407` [entero]

- Original: `reg.sigrid_motivo = (motivo_ok or None) and motivo_ok[:255]`
- Mutado:   `reg.sigrid_motivo = (motivo_ok or None) and motivo_ok[:256]`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (truncado defensivo).** El recorte protege la columna `sigrid_motivo`, que es `String(255)`. El único motivo que se escribe por esta vía es `MOTIVO_SIN_SESAME`, de 74 caracteres, así que 255 o 256 dan el mismo resultado; hay un test que fija que la marca cabe en el campo (`test_f003_r25_la_marca_cabe_en_el_campo`). Cubrir la diferencia exigiría escribir un motivo de 256 caracteres que hoy nadie genera.

### 10. `services/partes-front/infrastructure/sesame/sesame_api_client.py:46` [entero]

- Original: `_MAX_CUERPO = 300`
- Mutado:   `_MAX_CUERPO = 301`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (constante de ajuste).** El valor exacto es un parámetro de tuning, no una regla: 6 h de caché, 300 caracteres de cuerpo de error o 1 reintento de red. Un segundo o un carácter más no cambian ningún comportamiento observable, y fijarlo en un test convertiría un ajuste operativo en una rotura de la suite. Lo que SÍ está cubierto es el comportamiento que sostienen: que la caché caduca (`test_f003_r6_al_expirar_el_ttl_vuelve_a_preguntar`, `..._justo_en_el_ttl_la_entrada_ya_ha_caducado`), que el cuerpo del error se recorta (`test_f003_r1_el_cuerpo_del_error_se_recorta`) y que el transporte inyectado manda sobre el de red.

### 11. `services/partes-front/infrastructure/sesame/sesame_api_client.py:153` [entero]

- Original: `transport = self._transport or httpx.HTTPTransport(retries=1)`
- Mutado:   `transport = self._transport or httpx.HTTPTransport(retries=2)`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (constante de ajuste).** El valor exacto es un parámetro de tuning, no una regla: 6 h de caché, 300 caracteres de cuerpo de error o 1 reintento de red. Un segundo o un carácter más no cambian ningún comportamiento observable, y fijarlo en un test convertiría un ajuste operativo en una rotura de la suite. Lo que SÍ está cubierto es el comportamiento que sostienen: que la caché caduca (`test_f003_r6_al_expirar_el_ttl_vuelve_a_preguntar`, `..._justo_en_el_ttl_la_entrada_ya_ha_caducado`), que el cuerpo del error se recorta (`test_f003_r1_el_cuerpo_del_error_se_recorta`) y que el transporte inyectado manda sobre el de red.

### 12. `services/partes-front/interface_adapters/web/app.py:1085` [booleano]

- Original: `@app.get("/api/calendario", include_in_schema=False)`
- Mutado:   `@app.get("/api/calendario", include_in_schema=True)`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (documentación).** `include_in_schema` solo decide si el endpoint aparece en el OpenAPI que publica FastAPI. No cambia ni la ruta, ni la respuesta, ni el acceso. Se mantiene en `False` por coherencia con el resto de endpoints internos del portal (`/api/aprobar/*`, `/api/sigrid/*`), no por una regla.

### 13. `services/partes-front/interface_adapters/web/app.py:1501` [comparacion]

- Original: `if abs(float(linea.get("horas") or 0.0)) <= 1e-9:`
- Mutado:   `if abs(float(linea.get("horas") or 0.0)) < 1e-9:`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (epsilon de coma flotante).** La diferencia solo se notaría con unas horas que valieran EXACTAMENTE 1e-9. Las horas del parte llegan en pasos de 0,5 desde el formulario y desde la extracción, así que ese valor no es producible; el epsilon está ahí para no comparar flotantes con `== 0`. Lo cubierto es lo que importa: una línea a 0 h no genera aviso y una con horas sí (`test_f003_r18_solo_las_lineas_con_horas`).

### 14. `services/partes-front/interface_adapters/web/app.py:1603` [logico]

- Original: `if degradado and forzar:`
- Mutado:   `if degradado or forzar:`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (guarda de un log).** Ese `if` solo decide si se escribe el WARNING de «registro forzado»; lo que marca las líneas es el `sin_sesame=degradado and forzar` de la llamada a `_trazar`, que sí está cubierto (`test_f003_r25_el_override_marca_las_lineas` y `..._sin_degradacion_no_marca_nada`). Con el mutante se registraría un WARNING de más cuando se manda el flag sin hacer falta; el efecto en la BBDD no cambia.

### 15. `services/partes-front/interface_adapters/web/app.py:1607` [logico]

- Original: `settings.default_reviewer or "(sin usuario)",`
- Mutado:   `settings.default_reviewer and "(sin usuario)",`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (texto de log).** La mutación cae dentro de los argumentos de un `logger.*`: cambia lo que se lee en el log («(sin dni)» en vez del DNI, o cuántos identificadores se listan), no lo que el sistema hace. Ningún test lo caza porque ninguno afirma el texto literal de estas líneas, y no debe hacerlo: atarlas volvería la suite frágil sin proteger nada.
>
> Sí se afirma el contenido de UN log, el de wiring, porque ahí el log es la única evidencia de que la clave no se filtra (R20).

### 16. `services/partes-persistencia/application/services/jornada_resolver.py:25` [logico]

- Original: `if candef is None or candef == "":`
- Mutado:   `if candef is None and candef == "":`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (otro camino, mismo resultado).** Con `and` la condición nunca se cumple (`None == ""` es falso), así que la ejecución sigue hasta `float(candef)`, que levanta `TypeError` con `None` y `ValueError` con `""`; ambas las captura el `except` de debajo y devuelve exactamente lo mismo. Los casos están cubiertos (`test_f003_r1{1,2}_regla_candef` con `None` y `..._no_numericos_son_no_informados` con `""`): pasan con el mutante porque el resultado ES el mismo.

### 17. `services/partes-persistencia/application/services/recurso_conciliador.py:419` [entero]

- Original: `"para revision (%s).", len(docs), ", ".join(docs[:10]),`
- Mutado:   `"para revision (%s).", len(docs), ", ".join(docs[:11]),`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (texto de log).** La mutación cae dentro de los argumentos de un `logger.*`: cambia lo que se lee en el log («(sin dni)» en vez del DNI, o cuántos identificadores se listan), no lo que el sistema hace. Ningún test lo caza porque ninguno afirma el texto literal de estas líneas, y no debe hacerlo: atarlas volvería la suite frágil sin proteger nada.
>
> Sí se afirma el contenido de UN log, el de wiring, porque ahí el log es la única evidencia de que la clave no se filtra (R20).

### 18. `services/partes-persistencia/config/settings.py:125` [entero]

- Original: `sesame_cache_ttl_s: int = Field(21600, alias="SESAME_CACHE_TTL_S")`
- Mutado:   `sesame_cache_ttl_s: int = Field(21601, alias="SESAME_CACHE_TTL_S")`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (constante de ajuste).** El valor exacto es un parámetro de tuning, no una regla: 6 h de caché, 300 caracteres de cuerpo de error o 1 reintento de red. Un segundo o un carácter más no cambian ningún comportamiento observable, y fijarlo en un test convertiría un ajuste operativo en una rotura de la suite. Lo que SÍ está cubierto es el comportamiento que sostienen: que la caché caduca (`test_f003_r6_al_expirar_el_ttl_vuelve_a_preguntar`, `..._justo_en_el_ttl_la_entrada_ya_ha_caducado`), que el cuerpo del error se recorta (`test_f003_r1_el_cuerpo_del_error_se_recorta`) y que el transporte inyectado manda sobre el de red.

### 19. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:60` [entero]

- Original: `ttl_seconds: int = 21600,`
- Mutado:   `ttl_seconds: int = 21601,`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (constante de ajuste).** El valor exacto es un parámetro de tuning, no una regla: 6 h de caché, 300 caracteres de cuerpo de error o 1 reintento de red. Un segundo o un carácter más no cambian ningún comportamiento observable, y fijarlo en un test convertiría un ajuste operativo en una rotura de la suite. Lo que SÍ está cubierto es el comportamiento que sostienen: que la caché caduca (`test_f003_r6_al_expirar_el_ttl_vuelve_a_preguntar`, `..._justo_en_el_ttl_la_entrada_ya_ha_caducado`), que el cuerpo del error se recorta (`test_f003_r1_el_cuerpo_del_error_se_recorta`) y que el transporte inyectado manda sobre el de red.

### 20. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:167` [logico]

- Original: `_LOG_PREFIX, dni_norm or "(sin dni)", ano,`
- Mutado:   `_LOG_PREFIX, dni_norm and "(sin dni)", ano,`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (texto de log).** La mutación cae dentro de los argumentos de un `logger.*`: cambia lo que se lee en el log («(sin dni)» en vez del DNI, o cuántos identificadores se listan), no lo que el sistema hace. Ningún test lo caza porque ninguno afirma el texto literal de estas líneas, y no debe hacerlo: atarlas volvería la suite frágil sin proteger nada.
>
> Sí se afirma el contenido de UN log, el de wiring, porque ahí el log es la única evidencia de que la clave no se filtra (R20).

### 21. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:175` [logico]

- Original: `_LOG_PREFIX, dni_norm or "(sin dni)", ano, len(mapa),`
- Mutado:   `_LOG_PREFIX, dni_norm and "(sin dni)", ano, len(mapa),`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (texto de log).** La mutación cae dentro de los argumentos de un `logger.*`: cambia lo que se lee en el log («(sin dni)» en vez del DNI, o cuántos identificadores se listan), no lo que el sistema hace. Ningún test lo caza porque ninguno afirma el texto literal de estas líneas, y no debe hacerlo: atarlas volvería la suite frágil sin proteger nada.
>
> Sí se afirma el contenido de UN log, el de wiring, porque ahí el log es la única evidencia de que la clave no se filtra (R20).

### 22. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:194` [logico]

- Original: `"revision.", _LOG_PREFIX, exc, dni_norm or "(sin dni)", ano,`
- Mutado:   `"revision.", _LOG_PREFIX, exc, dni_norm and "(sin dni)", ano,`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (texto de log).** La mutación cae dentro de los argumentos de un `logger.*`: cambia lo que se lee en el log («(sin dni)» en vez del DNI, o cuántos identificadores se listan), no lo que el sistema hace. Ningún test lo caza porque ninguno afirma el texto literal de estas líneas, y no debe hacerlo: atarlas volvería la suite frágil sin proteger nada.
>
> Sí se afirma el contenido de UN log, el de wiring, porque ahí el log es la única evidencia de que la clave no se filtra (R20).

### 23. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:200` [logico]

- Original: `"revision.", _LOG_PREFIX, exc, dni_norm or "(sin dni)", ano,`
- Mutado:   `"revision.", _LOG_PREFIX, exc, dni_norm and "(sin dni)", ano,`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (texto de log).** La mutación cae dentro de los argumentos de un `logger.*`: cambia lo que se lee en el log («(sin dni)» en vez del DNI, o cuántos identificadores se listan), no lo que el sistema hace. Ningún test lo caza porque ninguno afirma el texto literal de estas líneas, y no debe hacerlo: atarlas volvería la suite frágil sin proteger nada.
>
> Sí se afirma el contenido de UN log, el de wiring, porque ahí el log es la única evidencia de que la clave no se filtra (R20).

### 24. `services/partes-persistencia/infrastructure/calendario/sesame_calendario_laboral.py:205` [comparacion]

- Original: `if self._ttl <= 0:`
- Mutado:   `if self._ttl < 0:`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (guarda redundante).** Con `ttl = 0` el atajo deja de dispararse, pero la comprobación de abajo calcula `(ahora - ts) >= 0`, que es cierta siempre: la entrada se da por caducada igual y no hay caché. El comportamiento coincide, y está cubierto por `test_f003_r6_ttl_no_positivo_no_cachea` (que pasa con las dos versiones, precisamente porque son equivalentes). El otro extremo, que un TTL positivo sí cachee, lo fija `test_f003_r6_un_ttl_de_un_segundo_si_cachea`.

### 25. `services/partes-persistencia/infrastructure/sesame/sesame_api_client.py:50` [entero]

- Original: `_MAX_CUERPO = 300`
- Mutado:   `_MAX_CUERPO = 301`

#### Análisis (COMPLETADO por el implementer)

> **Mutante equivalente (constante de ajuste).** El valor exacto es un parámetro de tuning, no una regla: 6 h de caché, 300 caracteres de cuerpo de error o 1 reintento de red. Un segundo o un carácter más no cambian ningún comportamiento observable, y fijarlo en un test convertiría un ajuste operativo en una rotura de la suite. Lo que SÍ está cubierto es el comportamiento que sostienen: que la caché caduca (`test_f003_r6_al_expirar_el_ttl_vuelve_a_preguntar`, `..._justo_en_el_ttl_la_entrada_ya_ha_caducado`), que el cuerpo del error se recorta (`test_f003_r1_el_cuerpo_del_error_se_recorta`) y que el transporte inyectado manda sobre el de red.

### 26. `services/partes-persistencia/infrastructure/sesame/sesame_api_client.py:60` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (COMPLETADO por el implementer)

> > **Cazado DESPUÉS de esta pasada.** `frozen=True` es una barandilla de diseño: estos objetos viven en la caché del adaptador, compartida entre persistencias. Sobrevivía porque sv3 no usa hoy `JornadaContrato` (solo el portal consulta la jornada), así que ninguna ruta ejercitaba su inmutabilidad. Se añadió el caso correspondiente a `test_f003_r8_los_datos_del_cliente_son_inmutables`: el cliente de sv3 es GEMELO del de sv4 y tiene que seguir siéndolo también en esto. Verificado a mano aplicando la mutación: con el test nuevo, falla.

