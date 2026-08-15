<!-- progress/impl_F-003.md -->
# F-003 · Integración sesame-api: festivos y jornada reales — Informe de implementación

Rama `feature/F-003-sesame-festivos-jornada`. Rigor **critico**. 24 commits
(18 de tarea T1–T18 + los de refuerzo guiado por mutación, lint e
informes), ninguno sobre `dev` ni `main`, sin `push`. Los 27 requisitos
R1–R27 tienen al menos un test con nombre trazable `test_f003_rN_...`,
con tres excepciones declaradas en la propia spec: **R17** (rejilla y
confirmación de «+ Nuevo») y el modal de **R25** son verificación MANUAL;
**R21** es documental (`azure-apps/partes.md`); y **R19** («los tests no
tocan red ni BBDD») no es un test sino una propiedad de toda la suite —
la impone el fixture `sin_red`, que corta `httpx.HTTPTransport`, más
`httpx.MockTransport` en los clientes y SQLite en memoria en el resto.

## Resumen en una frase

sv3 y sv4 pasan a resolver los festivos con el calendario REAL de cada
trabajador (Sesame, vía sesame-api) en vez de con un calendario global,
con respaldo local si Sesame no está; **la feature va apagada** hasta que
sesame-api se despliegue, y apagada el comportamiento es idéntico al
anterior, verificado por tests.

## Lo que cambió, por tarea

| Tarea | Qué se hizo | Commit |
|---|---|---|
| T1 | `jornada_efectiva`/`candef_valido` en sv4 y los 3 usos delegando (KPI vista trabajador, avisos de la matriz, `jornada_sugerida`) | `868837b` |
| T2 | Se **inaugura** `services/partes-persistencia/tests/` (conftest + dobles) y el resolutor gemelo de sv3; `_reclasificar_extras_jornada` delega | `561a9ec` |
| T3 | `SesameApiClient` de sv4 con `transport` inyectable + fixtures del contrato real | `4645c3d` |
| T4 | `CalendarioProvider` de sv4: caché (DNI × año), cascada, `fuente` por resolución, `fiable_para` | `669f392` |
| T5 | `SESAME_*` en settings de sv4, `sesame_enabled`, wiring inyectable en `build_app`, `.env.example` | `2e35378` |
| T6 | Vistas de sv4 con el calendario de cada trabajador; `dni` en `ObraMatrixRow`; banner `sesame-degradado` | `52d813a` |
| T7 | Badge del tipo de jornada del contrato + aviso de divergencia (R13/R14) | `9650fba` |
| T8 | `GET /api/calendario` (rango ≤ 62 días, campo raíz `fiable`) | `d35c9af` |
| T9 | «+ Nuevo»: rejilla con festivos/domingos marcados y confirmación al crear; CSS | `db6cfbc` |
| T10 | Avisos de festivo/domingo en el preflight y en el modal | `7e2587c` |
| T11 | Cliente gemelo de sv3 + `SesameCalendarioLaboral` con `consumir_degradacion()` | `664d233` |
| T12 | `construir_calendario(settings)` en el wiring de sv3 + `.env.example` | `105c874` |
| T13 | `SESAME_*` en `infra/` (URL vacía a propósito, `SESAME-API-KEY` en Key Vault) | `81bad0c` |
| T14 | `azure-apps/partes.md`: consumo declarado (commit `5a95c03` en ESE repo) | — |
| T15 | Nivel 2 en sv4: bloqueo del registro, override `forzar_sin_sesame`, marca `[SIN-SESAME]` | `65e4aa8` |
| T16 | Señal de revisión en sv3: `document_id`, `marcar_review_required`, recogida por grupo | `76c35e0` |
| T17 | `CLAUDE.md`: los clientes `infrastructure/sesame/` entran en la duplicación tolerada | `a4a9a61` |
| T18 | `bash harness/init.sh` completo en verde | `6a0cf9d` |
| — | Refuerzo de tests guiado por la campaña de mutación (**incluye un bug real**) | `be42428`, `d0108e2` |

### Ficheros tocados

**Nuevos (sv4)**: `infrastructure/sesame/{__init__,sesame_api_client}.py`,
`application/services/{calendario_provider,jornada_resolver}.py`,
`tests/fixtures_sesame.py` y 6 ficheros `tests/test_f003_r*.py`.

**Nuevos (sv3)**: `infrastructure/sesame/{__init__,sesame_api_client}.py`,
`infrastructure/calendario/sesame_calendario_laboral.py`,
`application/services/jornada_resolver.py`, `tests/{conftest,dobles,
fixtures_sesame}.py` y 4 ficheros `tests/test_f003_r*.py`.

**Modificados**: sv4 `config/settings.py`,
`interface_adapters/web/app.py`, `infrastructure/database/parte_repository.py`,
`infrastructure/transfer/resultado_sigrid.py`, `tests/dobles.py`,
`static/{app.js,styles.css}`, `templates/{trabajador_detail,obra_detail,
nuevo_parte}.html`, `.env.example`; sv3 `config/settings.py`,
`application/services/recurso_conciliador.py`,
`domain/ports/parte_repository.py`,
`infrastructure/database/sqlalchemy_parte_repository.py`,
`interface_adapters/api/app.py`, `.env.example`; raíz `CLAUDE.md`,
`specs/.../tasks.md`; `infra/{00_vars_partes,add_secrets_partes,
create_capps_partes,create_sv4_front}.ps1`; y `azure-apps/partes.md`
(repositorio aparte).

**NO se tocó**: ninguna copia de `orm_models.py` (cero cambios de
schema), sv1, sv2, sv5, `sigrid-api`, el proyecto `sesame-api`.

## Decisiones de diseño (y las que se apartaron de la spec)

1. **`festivos()` y `calendario_por_defecto()` devuelven `None` en 404 /
   sin calendario por defecto**, no lista vacía. El design decía
   «404 → `None`/lista según método»; hacía falta que fuera `None` en
   ambos para poder distinguir «Sesame no conoce este DNI» (→ calendario
   por defecto, R4) de «este trabajador no tiene festivos» (dato bueno).
   Con lista vacía, un año entero saldría laborable en silencio.
2. **`marcar_registros_sigrid` recibe un `motivo_ok`** (desviación: el
   design decía «nada más» de `parte_repository.py` aparte del `dni`).
   La marca `[SIN-SESAME]` de R25 se escribe donde se escribe la traza, y
   ese punto está dentro del repositorio; `aplicar_resultado` no podía
   ponerla desde fuera. Es un parámetro opcional que por defecto deja el
   comportamiento anterior intacto. **Sin cambios de schema**: `sigrid_motivo`
   ya existía (`String(255)`).
3. **El reloj entra por parámetro** (`reloj=time.time`) en el proveedor de
   sv4 y en el adaptador de sv3, en vez de monkeypatchear `time` en los
   tests: el TTL se prueba sin dormir y sin parchear un módulo global.
4. **`construir_calendario(settings)` vive fuera de `build_app` en sv3**:
   `build_app` monta la `SessionFactory` contra PostgreSQL y no se puede
   levantar en la suite, pero el cableado sí tenía que quedar cubierto.
5. **`/api/calendario` tolera un ISO con hora** (recorta a 10 caracteres),
   igual que el resto del monorepo, y lo fija un test.
6. **La entrada de caché caducada NO se refresca** al reutilizarse
   (*stale-while-error*): así el siguiente intento vuelve a preguntar en
   cuanto Sesame se recupera, en vez de servir un dato viejo seis horas.
7. **Un festivo sin nombre se pinta como «Festivo»**: las vistas deciden
   `is_holiday` por el nombre y, devolviendo `None`, un festivo real
   desaparecería del calendario.
8. `_es_no_laborable` de sv3 **ya** extraía el DNI del grupo y lo pasaba
   al puerto (D7 estaba hecho); se le añadió el test que lo fija para que
   nadie lo quite por parecer inútil.

## Verificaciones (salida real)

### Fase RED — trazas del fallo ANTES del código

Cada tarea empezó por el test. Trazas reales, con el comando exacto:

**T1** — `cd services/partes-front && python -m pytest tests/test_f003_r12_jornada_resolver.py -q`
```
tests\test_f003_r12_jornada_resolver.py:14: in <module>
    from application.services.jornada_resolver import jornada_efectiva
E   ModuleNotFoundError: No module named 'application.services.jornada_resolver'
```

**T2** — `cd services/partes-persistencia && python -m pytest tests/test_f003_r11_jornada_resolver.py -q`
```
tests\test_f003_r11_jornada_resolver.py:14: in <module>
    from application.services.jornada_resolver import (
E   ModuleNotFoundError: No module named 'application.services.jornada_resolver'
```
Los 22 casos dorados de `test_f003_r15_splits_dorados.py` se escribieron
**contra el código vigente antes de tocarlo** y se ejecutaron en verde
como línea base (`22 passed`), precisamente para que el refactor no
pudiera mover un número. Uno de ellos falló al escribirlo porque mi
expectativa era errónea, no el código:
```
E       assert [(2, 0.0, 3.0)] == [(2, 0.0, 3.0), (1, 8.0, 0.0)]
E         Right contains one more item: (1, 8.0, 0.0)
```
(se corrigió el test al comportamiento real y se rehízo el caso con tres
registros para que sí ejercitara el desbordamiento).

**T3** — `cd services/partes-front && python -m pytest tests/test_f003_r1_sesame_client.py -q`
```
tests\test_f003_r1_sesame_client.py:14: in <module>
    from infrastructure.sesame.sesame_api_client import (
E   ModuleNotFoundError: No module named 'infrastructure.sesame'
```

**T4** — `cd services/partes-front && python -m pytest tests/test_f003_r4_calendario_provider.py -q`
```
tests\test_f003_r4_calendario_provider.py:20: in <module>
    from application.services.calendario_provider import CalendarioProvider
E   ModuleNotFoundError: No module named 'application.services.calendario_provider'
```

**T5** — `cd services/partes-front && python -m pytest tests/test_f003_r7_wiring.py -q`
```
>       return build_app(settings, repository=ParteReviewRepository(fabrica), **kw)
E       TypeError: build_app() got an unexpected keyword argument 'calendario_provider'
...
8 failed, 1 warning in 3.03s
```

**T6** — `cd services/partes-front && python -m pytest tests/test_f003_r2_vistas_festivos.py -q`
```
E       AttributeError: 'ObraMatrixRow' object has no attribute 'dni'
...
FAILED ...::test_f003_r3_el_calendario_marca_los_festivos_del_trabajador
FAILED ...::test_f003_r2_la_matriz_de_obra_evalua_con_el_dni_de_la_fila
FAILED ...::test_f003_r22_la_vista_trabajador_avisa_si_la_resolucion_degrado
10 failed, 4 passed, 1 warning in 5.55s
```

**T7** — `cd services/partes-front && python -m pytest tests/test_f003_r13_jornada_contrato.py -q`
```
FAILED ...::test_f003_r13_muestra_el_tipo_de_jornada_del_contrato
FAILED ...::test_f003_r14_contrato_reducido_con_jornada_de_8_avisa
FAILED ...::test_f003_r14_reducida_desconocida_no_avisa
FAILED ...::test_f003_r14_el_umbral_es_la_jornada_por_defecto
4 failed, 4 passed, 1 warning in 4.15s
```

**T8** — `cd services/partes-front && python -m pytest tests/test_f003_r16_api_calendario.py -q`
```
FAILED ...::test_f003_r16_rango_de_63_dias_da_422
FAILED ...::test_f003_r16_fiable_true_cuando_todo_sale_de_sesame
FAILED ...::test_f003_r16_fiable_false_si_alguna_resolucion_degrado
17 failed, 1 warning in 4.72s
```

**T10** — `cd services/partes-front && python -m pytest tests/test_f003_r18_preflight_festivos.py -q`
```
FAILED ...::test_f003_r18_avisa_de_las_horas_en_festivo
FAILED ...::test_f003_r18_avisa_de_las_horas_en_domingo
FAILED ...::test_f003_r18_el_festivo_se_evalua_con_el_dni_de_la_linea
6 failed, 3 passed, 1 warning in 3.98s
```

**T11** — `cd services/partes-persistencia && python -m pytest tests/test_f003_r8_sesame_calendario.py -q`
```
tests\test_f003_r8_sesame_calendario.py:20: in <module>
    from infrastructure.calendario.sesame_calendario_laboral import (
E   ModuleNotFoundError: No module named 'infrastructure.calendario.sesame_calendario_laboral'
```

**T12** — `cd services/partes-persistencia && python -m pytest tests/test_f003_r10_wiring_sv3.py -q`
```
tests\test_f003_r10_wiring_sv3.py:30: in <module>
    from interface_adapters.api.app import construir_calendario
E   ImportError: cannot import name 'construir_calendario' from 'interface_adapters.api.app'
```

**T15** — `cd services/partes-front && python -m pytest tests/test_f003_r23_bloqueo_registro.py -q`
```
FAILED ...::test_f003_r23_el_preflight_anexa_el_bloqueo
FAILED ...::test_f003_r24_ejecutar_sin_override_da_422
FAILED ...::test_f003_r24_encolar_sin_override_da_422
FAILED ...::test_f003_r25_el_override_marca_las_lineas
FAILED ...::test_f003_r25_el_override_no_vale_por_la_cola
8 failed, 10 passed, 1 warning in 5.26s
```

**T16** — `cd services/partes-persistencia && python -m pytest tests/test_f003_r26_review_required.py -q`
```
>       assert repositorio.marcar_review_required([]) == 0
E       AttributeError: 'SqlAlchemyParteRepository' object has no attribute 'marcar_review_required'
...
9 failed, 4 passed in 0.64s
```

### Un bug REAL que destapó la campaña de mutación

El mutante `[:10] → [:11]` en `SesameCalendarioLaboral.es_no_laborable`
sobrevivía. Al escribir el test que lo cazara apareció el fallo de
verdad: el método **normalizaba la fecha para calcular el fin de semana
pero buscaba en el mapa de festivos con la cadena cruda**, así que un ISO
con hora (`2026-05-15T00:00:00`) daba «laborable» en pleno festivo —y en
sv3 eso significa pagar como ordinarias unas horas que van a extra.

Traza del fallo, antes de arreglarlo:
```
>       assert cal.es_no_laborable("2026-05-15T00:00:00", dni="12345678Z") is True
E       AssertionError: assert False is True
E        +  where False = es_no_laborable('2026-05-15T00:00:00', dni='12345678Z')
```
Arreglado en `be42428`: a partir del parseo manda `d.isoformat()`, también
al llamar al respaldo.

El mismo repaso destapó un **test que se engañaba solo**: el de «el log de
wiring no lleva la clave» comprobaba `key_len=27` sobre `caplog.text`
entero, y esa cadena también la escribe el cliente al instanciarse, así
que habría pasado con el `key_len` del wiring mal calculado. Ahora se
comprueba sobre la línea de wiring concreta (en sv4 y en sv3).

### Suites, portero y estáticos

Última ejecución completa, sin `ARNES_SALTAR_SUITES`:
```
$ bash harness/init.sh
    10 features, 8 abiertas, en curso: ['F-003'], bloqueadas: ninguna
[AVISO] ruff: 451 avisos (deuda previa, no bloquea)
6 passed in 0.18s
[OK] pytest en verde (con medición de cobertura)
95 passed in 3.27s
[OK] servicio sv3-persistencia (services/partes-persistencia): pytest en verde
[OK] servicio sv4-front (services/partes-front): pytest en verde        272 passed
[OK] servicio sv5-transfer (services/partes-transfer): pytest en verde
[OK] PUERTA COBERTURA: 94.5% de 621 líneas cambiadas cubiertas (587/621, umbral 80%, nivel critico)
[OK] Rama actual: feature/F-003-sesame-festivos-jornada
ENTORNO LISTO. Puedes trabajar.
```
El aviso de `ruff` es **deuda previa y baja**: eran 442 antes de F-003 y
son 451 después, y ninguno de los 9 nuevos está en los ficheros de la
feature (se limpiaron `I001`, `F401` y `SIM117` en los tests, commit
`3292e8f`). Los módulos de producción conservan
`from typing import Callable` como sus vecinos (`calendar_builder.py`,
`app.py`): dos estilos conviviendo sería peor que el aviso.

```
$ node --check services/partes-front/static/app.js
JS OK
$ python  (parseo Jinja2 de las plantillas tocadas)
Jinja OK: nuevo_parte.html
Jinja OK: trabajador_detail.html
Jinja OK: obra_detail.html
```

Sintaxis de los `.ps1` tocados, con el parser de PowerShell:
```
OK sintaxis: infra\00_vars_partes.ps1
OK sintaxis: infra\add_secrets_partes.ps1
OK sintaxis: infra\create_sv4_front.ps1
OK sintaxis: infra\create_capps_partes.ps1
```
Encoding preservado fichero a fichero (sin BOM; `00_vars`, `add_secrets` y
`create_capps` en LF —como estaban—, `create_sv4_front` en CRLF).

## Lo que quedó FUERA del alcance (a propósito)

- **La jornada numérica del contrato NO sustituye al `candef`.**
  `GET /api/v1/jornada` de sesame-api no devuelve horas (petición **P1**).
  Queda el enchufe (`jornada_efectiva`, un resolutor por servicio) y los
  tests de regresión que garantizan que hoy el número es el mismo (R15).
- **La librería `holidays` no se retira** (D8): es el respaldo de sv4.
- **Nada se desplegó.** `infra/` deja las variables preparadas pero
  `SESAME_BASE_URL` vacía; el despliegue lo lanza el humano.
- **El documento `azure-apps/sesame-api.md` no se escribe desde aquí**
  (petición **P3**): el dueño de un documento es el proyecto que describe.
- Marcado de festivos **celda a celda** en la matriz de obra: descartado en
  el design (D6); la columna usa el calendario por defecto y la exactitud
  por trabajador vive en los avisos.

## Verificaciones MANUALES pendientes (para el humano)

1. **T9 · «+ Nuevo» en el navegador**: crear un parte seleccionando un
   domingo y comprobar que sale la confirmación («N día(s) son
   festivo/domingo — ¿continuar?») y que al aceptar el alta procede.
   Ctrl+F5 para recoger los estáticos.
2. **T15 · modal de override**: con Sesame activado y caído, comprobar que
   el modal enseña el bloqueo, que sin marcar la casilla no deja
   registrar, y que al marcarla las líneas salen con el badge
   `SIN-SESAME`. Hoy no se puede probar de verdad hasta P2.
3. **T13 · diff de `infra/`**: confirmar que no viaja ningún secreto y que
   el orden de los pasos para encender Sesame es el que espera.
4. **T14 · `azure-apps/partes.md`**: revisar el commit `5a95c03` de ese
   repositorio (queda **sin push**, como el resto).
5. **T17 · diff de `CLAUDE.md`**: es un fichero de instrucciones; la
   edición implementa la decisión D1 que el humano cerró el 2026-08-15,
   pero conviene que la lea él.
6. **Aviso de riesgo operativo**: encender `SESAME_*` contra una URL que
   no responda **bloquea las aprobaciones** (R23). Es deliberado, pero
   conviene saberlo antes de tocar las variables en Azure.

## Evidencias

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** | **373** en total, todos en verde: **6** en `tests/` (raíz), **95** en sv3 (suite **nueva**: antes de F-003 sv3 tenía 0 y el portero lo avisaba en cada arranque), **272** en sv4 (**128** antes de F-003 ⇒ **+144**). sv5 y los demás servicios, sin tocar. |
| **Cobertura de las líneas cambiadas** | **94,5 %** — 587 de 621 líneas Python de producción cubiertas; umbral del nivel `critico`, 80 %. Línea `PUERTA COBERTURA` de `bash harness/init.sh`. |
| **Mutantes generados y supervivientes** | **211 generados, 211 evaluados, 0 timeouts.** Campaña inicial: 154 muertos / **57 supervivientes** (73,0 %). Campaña final tras el refuerzo: **185 muertos / 26 supervivientes (87,7 %)**, y el nº 26 se cazó después con un test más (verificado a mano aplicando la mutación), así que quedan **25 supervivientes, todos analizados y equivalentes**. |
| **Tiempo de ejecución de la suite** | raíz **0,2 s** · sv3 **3,3 s** · sv4 **35,3 s** (medidos dentro de `init.sh`); el portero completo, con la caché de servicios sin cambios, ronda el minuto. La campaña de mutación completa: **402 s**. |

Notas sobre la mutación: campaña **completa, sin muestreo**, sobre las
1.533 líneas del alcance del diff. Los 25 supervivientes que quedan están
analizados **uno a uno** en `progress/mutacion_F-003.md` (cero secciones
en `PENDIENTE`) y se agrupan en: 10 mutaciones dentro de argumentos de
`logger.*` (cambian el texto de un log, no el comportamiento), 6
constantes de ajuste (TTL, tamaño de recorte de errores, reintentos), 2
truncados defensivos a 255 caracteres, 2 cortocircuitos que llegan al
mismo resultado por otro camino, 2 guardas redundantes de TTL, 1 epsilon
de coma flotante, 1 `include_in_schema` (solo afecta al OpenAPI) y 1
guarda de un WARNING. **Ninguno cambia comportamiento observable.**

Lo que más valor dio la mutación no fue el porcentaje: fue destapar **un
bug real** (la fecha cruda contra el mapa de festivos) y **un test que se
engañaba solo** (el `key_len` del log de wiring). Ambos, arreglados.
