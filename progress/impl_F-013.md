<!-- progress/impl_F-013.md -->
# F-013 · Informe de validación de datos Sesame por trabajador — implementación

- Rama: `feature/F-013-informe-validacion-sesame` (base de la feature:
  `da7293d`, la punta de F-004). Rigor **estandar**. sdd=false: la mini-spec
  son los `acceptance` de F-013 en `harness/features.json` más el plan
  confirmado por el humano en `progress/current.md`.
- Fecha: 2026-08-17. Sin `git push`, sin PR, sin tocar `dev` ni `main`.

## Qué se ha hecho

Una herramienta de consola de SOLO LECTURA que barre los empleados que
conoce `sesame-api` y saca, por cada uno, sus festivos del año, el tipo de
jornada y el flag de reducida, en un Markdown legible y un CSV para Excel.
No toca la BBDD `partes`, ni Sigrid, ni ningún endpoint del portal.

### Ficheros tocados

| Fichero | Qué |
|---|---|
| `services/partes-front/validar_datos_sesame.py` | **NUEVO**. 573 líneas. El script. |
| `services/partes-front/tests/test_f013_informe_sesame.py` | **NUEVO**. 40 tests, sin red (`httpx.MockTransport`). |
| `docs/ARCHITECTURE.md` | Sección nueva «Herramientas de consola»: los tres scripts sueltos del monorepo y para qué sirve cada uno. |
| `progress/current.md` | Entrada de estado de F-013. |
| `progress/mutacion_F-013.md` | Informe de la campaña de mutación (lo genera `harness.mutacion`). |

NO se tocó `services/partes-front/infrastructure/sesame/sesame_api_client.py`
ni nada de `application/`, `interface_adapters/` o `config/`. El alcance de
mutación lo confirma: **1 fichero de producción** en el diff de la feature.

### Commits (uno por tarea)

```
0e6a47f  F-013 T1: fase RED — tests del informe (fallan: falta el script)
2b2d3f2  F-013 T2: script validar_datos_sesame.py (solo lectura) y tests en verde
1612b99  F-013 T3: tests de las ramas de error y de la configuracion por --env
144d0f2  F-013 T4: tests que matan 21 de los 22 supervivientes; ARCHITECTURE.md
cdbdc00  F-013 T5: el test del 400 usa cuerpo valido para exigir que se mire el HTTP
d25c198 / 6a497cf / 00b3d19  informes de las tres campañas de mutación
```

## Decisiones de diseño

1. **El listado de empleados se hace en el propio script, no en el cliente.**
   `GET /api/v1/empleados?solo_activos=` se implementa en
   `listar_empleados()` dentro de `validar_datos_sesame.py`, con `httpx` y
   `transport` inyectable. Motivo: `infrastructure/sesame/sesame_api_client.py`
   es duplicación tolerada **gemela** con la de sv3 (CLAUDE.md, «límite de
   servicio»), y quien toca una copia debe tocar las dos. Ningún servicio
   necesita listar empleados: meterle el método al cliente obligaría a
   modificar sv3 por una herramienta de consola de sv4. El motivo está
   escrito en el docstring de la función para que no se «arregle» luego.
2. **Se usa el `SesameApiClient` en crudo, NO el `CalendarioProvider`.** La
   cascada de degradación del proveedor (F-003) es justo lo que aquí
   estorba: si un DNI no casa en Sesame, el proveedor cae al calendario por
   defecto y el informe diría que todo va bien. Con el cliente en crudo, ese
   404 sale como fila con error, que es el `acceptance` 2.
3. **Un fallo por trabajador es un dato, no una excepción.** `construir_fila`
   no lanza nunca: los fallos de `festivos` y de `jornada` se acumulan en la
   columna `error` (separados por `|`) y el barrido sigue. Se aborta solo si
   falla el **listado** (exit **1**) o la **configuración** (exit **2**):
   sin lista de empleados no hay informe que escribir.
4. **`n_festivos` distingue «cero festivos» de «no se pudo leer»** (campo
   `festivos_ok`): un cero falso en esta columna es exactamente el tipo de
   número que el humano validaría por bueno. Lo mismo con la jornada, que
   sale como `(desconocido)`.
5. **Salida en `services/partes-front/logs/`**, que está en el `.gitignore`
   del servicio (verificado: `git check-ignore -v` →
   `services/partes-front/.gitignore:197:logs/`). El informe lleva DNIs y no
   puede acabar versionado. La clave de API no se escribe **nunca** en el
   informe (hay un test que lo comprueba) ni en el log.
6. **CSV en UTF-8 con BOM y `;`**, según `docs/CONVENTIONS.md` (Excel
   español). El Markdown escapa las barras de los datos para no partir la
   tabla.
7. **Lógica pura separada de la E/S**: `resumir`, `celdas_de`, `render_csv`,
   `render_markdown`, `fmt_bool`, `fmt_festivos` no hacen E/S y se testean
   solas; `main(argv, *, transport=...)` es fino y permite ejercitar el
   recorrido completo, ficheros incluidos, contra `tmp_path`.
8. **Configuración por precedencia**: `--base-url`/`--api-key` > fichero
   `--env` > `SESAME_API_BASE_URL`/`SESAME_API_KEY` (los mismos nombres que
   `config/settings.py`) > `http://localhost:8006`. NO se usa `Settings()`
   de sv4: exigiría el resto de variables del portal para lanzar un script
   de diagnóstico.
9. **El log de `httpx` se baja a WARNING**: emite una línea por petición con
   el DNI en la query; con 200 trabajadores la consola se vuelve ilegible y
   el aviso útil se pierde entre el ruido.

## Fase RED (obligatoria en rigor estandar)

Los tests se escribieron **antes** que el script y se ejecutaron en rojo.

```
$ cd services/partes-front && python -m pytest tests/test_f013_informe_sesame.py -q --tb=short
=================================== ERRORS ====================================
_____________ ERROR collecting tests/test_f013_informe_sesame.py ______________
ImportError while importing test module 'C:\Users\pgris\PycharmProjects\partes\services\partes-front\tests\test_f013_informe_sesame.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_f013_informe_sesame.py:25: in <module>
    import validar_datos_sesame as vds
E   ModuleNotFoundError: No module named 'validar_datos_sesame'
=========================== short test summary info ===========================
ERROR tests/test_f013_informe_sesame.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.31s
```

Ese rojo está commiteado aparte, en `0e6a47f`, para que la fase RED se pueda
comprobar en el historial y no solo creer sobre mi palabra.

Primera ejecución tras escribir el script (commit `2b2d3f2`): **21 passed,
2 failed**. Los dos fallos eran aserciones mal escritas **del test**, no del
script — el literal de la cabecera (`"3 empleados"` vs el real
`"Empleados: 3 (0 con errores)"`) y el recuento de barras de la tabla (las
`\|` escapadas también son el carácter `|`). Se corrigieron los tests, no la
implementación; queda dicho porque es la diferencia entre ajustar el test al
código y ajustar el código al test.

## Verificación

### `bash harness/init.sh` (última ejecución, entera en verde)

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 450 avisos (deuda previa, no bloquea)
[OK] pytest en verde (con medición de cobertura)      # 6 tests de la raíz
[OK] servicio sv3-persistencia: pytest en verde (caché)
312 passed, 1 warning in 35.68s
[OK] servicio sv4-front (services/partes-front): pytest en verde
[OK] servicio sv5-transfer: pytest en verde (caché)
[OK] PUERTA COBERTURA: 96.0% de 877 líneas cambiadas cubiertas (842/877, umbral 80%, nivel estandar)
[OK] Rama actual: feature/F-013-informe-validacion-sesame
ENTORNO LISTO. Puedes trabajar.
```

Los 450 avisos de ruff son **deuda previa del repositorio**, no de esta
feature: sobre los dos ficheros nuevos, ruff sale limpio.

```
$ python -m ruff check services/partes-front/validar_datos_sesame.py services/partes-front/tests/test_f013_informe_sesame.py --output-format=concise
All checks passed!
```

Hay tres `# noqa` en el script, cada uno con su motivo escrito al lado:
`TRY004` (un contrato roto del servicio remoto no es un `TypeError` del
programa; `RuntimeError` es la señal de aborto de este módulo, igual que en
`SesameApiClient`), y `DTZ011`/`DTZ005` (hora **local** a propósito: el «año
en curso» y el sello del fichero son los del humano que lo lanza).

### Prueba manual del camino de aborto (sin sesame-api levantado)

```
$ cd services/partes-front && python validar_datos_sesame.py --base-url http://localhost:1 --api-key <clave> --ano 2026 --salida <tmp>
INFO validar_datos_sesame: [validar-sesame] sesame-api=http://localhost:1 ano=2026 solo_activos=True
ABORTADO: sesame-api no responde en http://localhost:1/api/v1/empleados: ConnectError('[WinError 10061] No se puede establecer una conexión ya que el equipo de destino denegó expresamente dicha conexión')
exit=1
```

### Muestra real del informe generado (3 empleados, uno con 404)

Generada con el `MockTransport` de la suite, para revisar a ojo que el
Markdown es legible antes de dárselo al humano:

```markdown
# Informe de validacion de datos Sesame

- Generado: 2026-08-17 21:43
- sesame-api: http://sesame.test
- Ano: 2026
- Ambito: solo activos
- Empleados: 3 (1 con errores)

## Calendario por defecto

2 festivos en 2026:

- 2026-01-06 Reyes
- 2026-12-25 Navidad

## Resumen

**Festivos por trabajador**

- 2 festivos: 2 trabajadores
...
**Trabajadores con error**

- `87654321X`: festivos: 404, Sesame no conoce ese DNI

## Trabajadores

| nombre | dni | estado | n_festivos | festivos | jornada_tipo | reducida | tipo_contrato | error |
|---|---|---|---|---|---|---|---|---|
| Pepe Perez | 12345678Z | active | 2 | 2026-01-01 Ano Nuevo \| 2026-05-15 San Isidro | Parcial | si | Indefinido |  |
| Ana Lopez | 87654321X | active | (desconocido) |  | Parcial | si | Indefinido | festivos: 404, Sesame no conoce ese DNI |
```

## Cobertura de los `acceptance`

| # | Criterio | Cómo queda cubierto |
|---|---|---|
| 1 | Genera el informe por trabajador (festivos, jornada, reducida) contra una instancia configurable, sin tocar BBDD | `test_f013_a1_*` (7 tests): dos ficheros, una fila por trabajador, todas las secciones, filtrado al año, `--base-url`/`--api-key`/entorno/`--env`, `--incluir-inactivos`. El script no importa nada de `infrastructure/database`. |
| 2 | Los errores por trabajador aparecen en el informe, no abortan el barrido | `test_f013_a2_*` (7 tests): 404 en festivos, 502 en jornada, los dos a la vez, empleado sin DNI, lista de DNIs con error en el resumen, calendario por defecto roto o ausente. |
| 3 | `bash harness/init.sh` en verde | Salida pegada arriba. |

## Evidencias

| Evidencia | Valor real |
|---|---|
| **Tests ejecutados** | **312 passed, 0 failed** en la suite de sv4 (40 de ellos nuevos, de F-013). Más 6 en la suite de la raíz y las de sv3/sv5 en verde por caché. |
| **Cobertura de las líneas cambiadas** | **99.6 % (256/257)**, midiendo solo el diff de F-013 (`python -m harness.cobertura --base da7293d`). Umbral: 80 %. La puerta de `init.sh` contra `dev` da **96.0 % (842/877)**, porque `dev` aún no tiene F-003 y el diff arrastra su código. La única línea sin cubrir es el guardián `if __name__ == "__main__":`. |
| **Mutantes generados y supervivientes** | **74 generados, 73 muertos, 1 superviviente, 0 timeouts** (294,5 s). Informe: `progress/mutacion_F-013.md`. |
| **Tiempo de ejecución de la suite** | sv4 completa: **35,68 s** (312 tests). Solo los tests de F-013: **0,71 s** (40 tests). |

### Análisis del superviviente

`validar_datos_sesame.py:374` — `httpx.HTTPTransport(retries=1)` →
`retries=2`.

**Mutante equivalente para esta suite, y a propósito.** Esa línea solo se
evalúa cuando NO se inyecta transporte (`transport or
httpx.HTTPTransport(...)`), es decir, en la ejecución real contra
`sesame-api`. Los 40 tests inyectan `httpx.MockTransport`, así que la rama
del transporte real nunca se construye. Cazar el mutante exigiría un test
que abriese una conexión de verdad y contase los reintentos, y
`docs/CONVENTIONS.md` lo prohíbe («los unit tests no tocan red ni BBDD»). El
número de reintentos, además, no cambia ningún resultado observable del
informe: solo cuántas veces se insiste antes de dar el error que el script ya
reporta y que sí está cubierto (`test_f013_r_sesame_api_inalcanzable_aborta`).
No hay hueco de test que tapar.

La primera campaña dio 22 supervivientes; se escribieron tests para 21 de
ellos (estado del empleado, `dni_norm` vacío con DNI válido, recuento de
festivos cuando no se pudo leer, «(sin datos)» del resumen, plurales,
frontera del HTTP 400, cuerpo sin campo `ok`, `.env` con comentarios y con
`=` en el valor, `base_url` del entorno realmente usada, creación de la
carpeta de salida anidada, recorte de cuerpos de error, inmutabilidad de las
estructuras, y los códigos de salida exactos 1 y 2). Dos de esos tests
destaparon comportamientos que **habrían sido bugs reales**: una variable
comentada con `=` dentro del `.env` se habría aplicado, y una clave en base64
terminada en `=` habría reventado el parseo.

## Verificaciones MANUAL pendientes (del humano)

1. **La validación de los números en sí**, que es el objeto de la feature:
   levantar `sesame-api` en local y ejecutar

   ```
   cd services/partes-front
   python validar_datos_sesame.py --base-url http://localhost:8006 --api-key <clave-de-sesame-api>
   ```

   (o, si ya tiene `SESAME_API_BASE_URL` y `SESAME_API_KEY` en un `.env`
   suyo: `python validar_datos_sesame.py --env <ruta-del-.env>`; también
   valen esas dos variables en el entorno, sin argumentos). El informe queda
   en
   `services/partes-front/logs/informe_sesame_<año>_<YYYYMMDD-HHMM>.{md,csv}`.
   Revisar contra la realidad: festivos por trabajador, quién sale con
   jornada reducida, y **qué DNIs no casan** en Sesame (la columna `error`).
2. Si el barrido tarda: son 2 peticiones por trabajador y no hay
   paralelismo. Con ~200 trabajadores y sesame-api local es cuestión de
   segundos; contra un sesame-api desplegado, más. No se paralelizó a
   propósito: no merece complejidad en una herramienta que se lanza a mano.

## Qué queda fuera (no es de esta feature)

- Desplegar `sesame-api` (petición P1 de F-003, en manos del humano) y
  encender F-003 en los servicios.
- Corregir los datos que el informe destape (DNIs que no casan, calendarios
  mal asignados): eso es trabajo en Sesame, no en este repositorio.
- Consumir el informe desde F-011 (jornada reducida por días) y F-012
  (candef 9h/viernes): esas features lo usarán como entrada, pero se
  especifican aparte.
- Que el script salga en el portal o en algún pipeline: es de consola, a
  mano, y así debe seguir.
- Una posible mejora anotada para quien la quiera: hoy el informe no dice
  **cuántos trabajadores de Sigrid** no aparecen en Sesame, porque el barrido
  parte de la lista de Sesame. El cruce con `emp`/`res` de Sigrid sería otra
  feature (y tocaría sigrid-api).
