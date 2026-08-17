<!-- progress/review_F-013.md -->
# F-013 · Informe de validación de datos Sesame por trabajador — review

- **Veredicto: CHANGES_REQUESTED** — por UN solo punto, documental y de
  arreglo inmediato (ver «Cambios requeridos»). El código, los tests y las
  puertas de rigor están **todos en verde y verificados de forma
  independiente**: no hay nada que reimplementar.
- Rama revisada: `feature/F-013-informe-validacion-sesame`, HEAD `156130f`.
  Base de la feature: `da7293d` (punta de F-004). Se compara contra `da7293d`,
  no contra `dev`: `dev` (merge-base `43a35fe`) todavía no tiene F-003 ni
  F-004 y el diff contra ella arrastraría código ajeno a esta feature.
- sdd=false: mini-spec = `description` + `acceptance` de F-013 en
  `harness/features.json` + el plan confirmado por el humano en
  `progress/current.md`.
- Reviewer: 2026-08-17. Sin editar código, sin push.

## Nivel de rigor

Declarado `estandar` en `harness/features.json` (valor válido según
`harness/rigor.json`). Exige: C1–C3 + C3 bis + C5, tests trazables (C4),
**fase RED** en los requisitos centrales, **cobertura** de las líneas
cambiadas ≥ 80 %, y **campaña de mutación con los supervivientes
documentados y analizados**. NO exige cero supervivientes (eso es `critico`).

---

## Checkpoints

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina en verde. Ejecutado por mí, salida real:

  ```
  [OK] Arnés v1.4.0 (2026-08-13)
  [OK] compileall: sin errores de sintaxis
  [AVISO] ruff: 450 avisos (deuda previa, no bloquea)
  6 passed in 0.12s
  [OK] pytest en verde (con medición de cobertura)
  [OK] servicio sv3-persistencia: pytest en verde (caché)
  [OK] servicio sv4-front (services/partes-front): pytest en verde (caché)
  [OK] servicio sv5-transfer: pytest en verde (caché)
  [OK] PUERTA COBERTURA: 96.0% de 877 líneas cambiadas cubiertas
       (842/877, umbral 80%, nivel estandar)
  [OK] Rama actual: feature/F-013-informe-validacion-sesame
  ENTORNO LISTO. Puedes trabajar.
  ```

- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md` (init.sh los valida uno a uno).

### C2 — El estado es coherente

- [x] Una sola feature `in_progress` (`F-013`); init.sh lo valida.
- [x] Rama actual `feature/F-013-informe-validacion-sesame`, la declarada en
      `features.json`. Nunca se tocó `dev` ni `main`.
- [x] `progress/current.md` tiene la sección de la sesión activa (F-013) al
      frente. Ver observación NB-3: el bloque de F-004 que la acompaña es
      **anterior a esta rama** (viene en `da7293d`) y F-004 sigue viva a la
      espera de implementación, así que no es «resto de sesión anterior».
- [x] Toda feature `done` tiene su resumen en `progress/history.md` (F-003 y
      anteriores; F-013 aún no es `done`, correctamente).

### C3 — El código respeta arquitectura y convenciones

- [x] **Arquitectura hexagonal respetada.** `validar_datos_sesame.py` es un
      script de consola en la raíz del servicio (mismo patrón ya establecido
      por `services/partes-transfer/prueba_escritura_sigrid.py` y
      `services/partes-front/consulta_reshor_recursos.py`). Importa solo
      stdlib + `httpx` + `infrastructure.sesame.sesame_api_client`.
      Verificado por mí: **cero** imports de `infrastructure/database`,
      de Sigrid, de `application/`, de `interface_adapters/` o de `config/`.
- [x] Primera línea con la ruta: `# validar_datos_sesame.py`, relativa a la
      raíz del servicio — mismo criterio que el ejemplo de
      `docs/CONVENTIONS.md:10` (`# application/steps/mi_step.py`) y que el
      precedente `# prueba_escritura_sigrid.py`.
- [x] Sin `print()` de debug: los seis `print()` son la salida de usuario de
      una CLI (3 de `ABORTADO:` a `stderr`, 3 del resumen final). Sin TODOs
      sueltos. **Sin secretos hardcodeados** (barrido propio abajo). Sin
      dependencias nuevas: `httpx` ya estaba.
- [x] Reglas de dominio de `ARCHITECTURE.md`: las tres trampas del monorepo
      no aplican — el script no escribe en Sigrid (no hay `hmores.reside` ni
      recurso/empleado que confundir), no genera incidencias, y **no toca
      ningún `orm_models.py`** ni el schema.
- [x] **Regla de duplicación tolerada respetada.** `git diff --name-status
      da7293d...HEAD` no incluye
      `services/partes-front/infrastructure/sesame/sesame_api_client.py` ni
      su gemelo de sv3. El listado de empleados se implementó **en el propio
      script** (`listar_empleados`, línea 356) precisamente para no obligar a
      tocar las dos copias por una herramienta de consola; el motivo está
      escrito en el docstring de la función, donde el próximo lector lo verá.
      Decisión correcta y bien argumentada.

### C3 bis — Documentos que entran de fuera

**N/A justificado:** `git diff --name-only da7293d...HEAD -- docs/referencia/`
devuelve vacío. La feature no añade ni modifica ningún fichero en
`docs/referencia/`, así que el bloque no aplica por su propia cláusula de
cabecera. (Aun así ejecuté el barrido de secretos sobre los ficheros nuevos;
resultado abajo.)

### C4 — La verificación es real

- [x] Cada criterio `acceptance` tiene tests trazables y todos pasan (tabla
      de trazabilidad abajo). Ejecutado por mí:
      `cd services/partes-front && python -m pytest tests/test_f013_informe_sesame.py -q`
      → **40 passed in 0.41s**. Suite completa de sv4: **312 passed in 21.06s**.
- [x] **Los unit tests no tocan red ni BBDD.** Verificado: todos los caminos
      que llegan a HTTP inyectan `httpx.MockTransport`. Los tres `main(...,
      transport=None)` corresponden a abortos de **configuración** que
      retornan antes de abrir ninguna conexión (`--env` inexistente → 2, sin
      clave → 2). Cero BBDD, cero `create_engine`, cero sockets.
- [x] Verificación `MANUAL (humano)` listada en `progress/current.md` con su
      comando exacto: ejecutar el script contra `sesame-api` en
      `http://localhost:8006` y validar los números a mano. Es justamente el
      objeto de la feature y queda correctamente pendiente del humano.

### C4 bis — El rigor declarado se cumple

- [x] La feature declara `rigor: "estandar"`, valor válido.
- [x] **Fase RED: verificada en el historial, no creída.** El commit
      `0e6a47f` («F-013 T1: fase RED») añade **solo**
      `tests/test_f013_informe_sesame.py` (443 líneas, 1 fichero), y
      `git ls-tree -r 0e6a47f -- services/partes-front/validar_datos_sesame.py`
      devuelve **vacío**: el script no existía. El informe pega la traza real
      del rojo (`ModuleNotFoundError: No module named
      'validar_datos_sesame'`). El script aparece en `2b2d3f2` (T2). La fase
      RED es comprobable por un tercero, que es lo que exige el checkpoint.
      Se agradece además que el informe declare abiertamente que el primer
      verde fue «21 passed, 2 failed» y que se corrigieron **los tests**, no
      la implementación: eso es exactamente la distinción que el checkpoint
      quiere que no se oculte.
- [x] **Cobertura:** puerta de `init.sh` en `[OK]`, 96.0 % (842/877, umbral
      80 %). Medida solo sobre el diff de F-013 el implementer declara
      99.6 % (256/257); coherente con que la puerta, al medir contra `dev`,
      arrastre el código de F-003/F-004.
- [x] **Mutación: totales verificados de forma independiente.** No me fié del
      informe; recalculé con las herramientas del arnés (cálculo puro, sin
      ejecutar la suite):

      ```
      python -c "from harness.alcance import alcance_de_feature
                 from harness.mutacion import generar_mutantes ..."
      origen: rama  refs: ('da7293da005993dee235011b5ac2197b929d6a6d',
                           'feature/F-013-informe-validacion-sesame')
        services/partes-front/validar_datos_sesame.py   573
      total lineas: 573
      MUTANTES TOTALES: 74
      por operador: {'entero': 15, 'booleano': 9, 'logico': 20,
                     'not': 10, 'aritmetico': 17, 'comparacion': 3}
      ```

      **Cuadra exactamente** con `progress/mutacion_F-013.md`: 1 fichero de
      producción en alcance, 573 líneas, 74 mutantes generados. La campaña
      no es un informe escrito a mano.

      *Nota de método:* el informe usa base `da7293d` (opción `--base` de
      `harness.mutacion`), no la `dev` por defecto. Es lo correcto aquí —
      con `dev` el alcance se dispara a 19 ficheros de F-003/F-004 que esta
      feature no toca — y el informe lo declara explícitamente en su sección
      «Alcance». Recalculé con esa misma base y coincide.

      Muestreo del superviviente declarado (`:374`, operador `entero`):
      existe como mutante real con el mismo texto,
      `transporte = transport or httpx.HTTPTransport(retries=1)` →
      `retries=2`. El generador produce además un segundo mutante en esa
      misma línea (`logico`, `or`→`and`) que la campaña sí mató.
- [ ] **Cada superviviente tiene su sección de análisis completada (ninguna
      en `PENDIENTE`).** → **FALLA. Es el único checkbox vacío.**
      `progress/mutacion_F-013.md`, sección «Supervivientes → 1.», conserva
      la plantilla sin rellenar que genera la herramienta:

      ```
      #### Análisis (PENDIENTE del implementer)

      > Por qué ningún test lo caza: PENDIENTE.
      > Decisión: ¿test nuevo o mutante equivalente justificado?
      ```

      El análisis **existe y es correcto**, pero está escrito en otro fichero
      (`progress/impl_F-013.md`, «Análisis del superviviente»). Ver «Cambios
      requeridos».
- [x] El informe del implementer trae la sección **«Evidencias»** con los
      cuatro números: tests (312 passed / 40 nuevos), cobertura del diff
      (99.6 %), mutantes y supervivientes (74 / 1), y tiempo de suite
      (35,68 s sv4; 0,71 s los de F-013). Contrastados: mi ejecución da 312
      passed en 21,06 s y 40 passed en 0,41 s — más rápido que lo declarado,
      no más lento; sin discrepancia sustantiva.
- [ ] Ningún punto del bloque marcado N/A sin justificación → el punto que
      falla no es un N/A, es un checkbox vacío real.

### C4 ter — Rutas sensibles

**N/A sin nada que justificar:** no existe `harness/rutas_sensibles.json` en
el repositorio (`ls` → no such file). CHECKPOINTS §C4 ter dice literalmente
que sin esa declaración el bloque es N/A y no hay nada que justificar.

### C5 — La sesión se cerró bien

- [x] `tasks.md`: **N/A justificado** — F-013 es `sdd=false` y no tiene
      `specs/F-013-*/`, así que por la nota de cabecera de `CHECKPOINTS.md`
      lo que dependa de `tasks.md` es N/A. El formato mínimo de commit que
      esa nota exige (`F-XXX: <descripción>`) se cumple y se supera: hay un
      commit por tarea con el formato completo `F-013 Tn: ...`
      (`0e6a47f` T1 … `cdbdc00` T5), más los commits de las campañas de
      mutación y el del informe.
- [x] Sin ficheros temporales ni artefactos sin trackear: `git status
      --porcelain` **vacío**. La carpeta de salida del script está ignorada:
      `git check-ignore -v services/partes-front/logs/x.md` →
      `services/partes-front/.gitignore:197:logs/`.
- [x] `features.json` refleja el estado real: `in_progress` (correcto: pasa a
      `done` tras el APPROVED, no antes).

---

## Trazabilidad: criterio `acceptance` → test que lo cubre

| # | Criterio `acceptance` | Tests que lo cubren | Estado |
|---|---|---|---|
| 1 | Genera el informe por trabajador (festivos del año, jornada, reducida) contra una instancia de sesame-api configurable, **sin tocar BBDD** | `test_f013_a1_genera_informe_md_y_csv_de_tres_trabajadores`, `_el_markdown_trae_todas_las_secciones`, `_la_clave_no_aparece_nunca_en_el_informe`, `_los_festivos_se_filtran_al_ano_pedido`, `_por_defecto_pide_solo_los_activos`, `_incluir_inactivos_pide_todos`; configuración: `test_f013_r_el_fichero_env_alimenta_la_configuracion`, `_la_clave_del_entorno_sirve_de_respaldo`, `_leer_env_*` (3), `_env_inexistente_aborta`, `_sin_api_key_aborta_sin_llamar_a_nadie`, `_la_carpeta_de_salida_se_crea_con_sus_padres`; render: `_render_csv_*` (2), `_render_markdown_*` (3), `_resumir_agrupa_*`, `_formato_de_booleanos` (parametrizado) | PASA |
| 2 | Los errores por trabajador (DNI sin casar, etc.) **aparecen en el informe, no abortan el barrido** | `test_f013_a2_dni_sin_casar_en_festivos_es_una_fila_con_error`, `_upstream_caido_en_jornada_es_una_fila_con_error`, `_empleado_sin_dni_es_una_fila_con_error`, `_el_resumen_lista_los_dnis_con_error`, `_los_dos_fallos_del_mismo_trabajador_se_acumulan`, `_ningun_calendario_por_defecto_se_dice_en_el_informe`, `_el_calendario_por_defecto_roto_no_tumba_el_informe`. Y el contrapunto —qué SÍ aborta—: `test_f013_r_fallo_del_listado_aborta_con_codigo_1`, `_listado_con_ok_false_aborta`, `_listado_sin_el_campo_ok_aborta`, `_un_400_del_listado_tambien_aborta`, `_listado_con_data_que_no_es_lista_aborta`, `_listado_que_no_es_json_aborta`, `_sesame_api_inalcanzable_aborta` | PASA |
| 3 | `bash harness/init.sh` en verde | Ejecutado por el reviewer; salida pegada en C1 | PASA |

*Sobre la nomenclatura:* CHECKPOINTS pide `test_fXXX_rN_*`. Aquí se usa
`test_f013_a1_*` / `test_f013_a2_*` (a = `acceptance`, que es lo que hace de
requisito en una feature `sdd=false`) y `test_f013_r_*` para los de
robustez/regresión. Lo doy por **cumplido**: la trazabilidad al criterio es
inequívoca y `aN` es más honesto que `rN` cuando no hay requisitos EARS. Ver
propuesta de automejora AM-1.

---

## Verificaciones extra pedidas por el humano

Todas ejecutadas por mí, no leídas del informe del implementer.

**1. El script es de SOLO LECTURA y no invade capas.** Confirmado. Imports
totales del fichero: `argparse, csv, io, logging, os, sys, collections.abc,
dataclasses, datetime, pathlib, typing, httpx` y
`infrastructure.sesame.sesame_api_client`. Nada de BBDD, nada de Sigrid.
`git diff --name-status da7293d...HEAD` toca 7 ficheros y **ninguno** está en
`application/`, `interface_adapters/`, `config/`, ni es
`sesame_api_client.py` (ni el de sv4 ni el de sv3).

**2. La clave de API no se filtra.** Verificado por ejecución, no por
lectura: monté un `MockTransport` con una clave centinela
(`CLAVE-SECRETA-DEL-REVIEWER-12345`) y un `assert` en el handler de que la
cabecera `x-api-key` la lleva. Resultado: la petición **sí** la envía, y
`CLAVE in markdown` → `False`, `CLAVE in csv` → `False`. En el log solo
aparece `base_url`, `ano` y `solo_activos`. La carpeta de salida está
ignorada por git (comprobado con `git check-ignore -v`, arriba).

**3. Errores por trabajador vs. abortos.** Verificado con ejecución real
(3 empleados: uno correcto, uno con 404 en festivos **y** 502 en jornada, uno
sin DNI):

```
WARNING validar_datos_sesame: [validar-sesame] Ana Lopez (87654321X): festivos: 404, ... | jornada: sesame-api respondio 502 ...
Empleados: 3 (2 con errores)
exit = 0
```

Los tres trabajadores salen como filas; el barrido llega al final; exit 0.
Y el camino de aborto, también ejecutado:

```
$ python validar_datos_sesame.py --base-url http://localhost:1 --api-key <clave> --ano 2026 --salida <tmp>
ABORTADO: sesame-api no responde en http://localhost:1/api/v1/empleados: ConnectError('[WinError 10061] ...')
exit=1
```

Probé además un caso que el implementer no documenta, por si la captura de
excepciones era demasiado estrecha: `--base-url "://mal-formada"`. También
aborta limpio (`UnsupportedProtocol` es subclase de `httpx.HTTPError`), sin
traza de Python: `ABORTADO: ... Request URL is missing an 'http://' or
'https://' protocol.` → `exit=1`. Los abortos de configuración dan 2
(`--env` inexistente, falta de clave), como declara el informe.

**4. Contrato de `GET /api/v1/empleados`.** Contrastado contra el código real
de `sesame-api` (`interface_adapters/api/app.py:101-113` y
`domain/models/sesame_models.py:20-29`):

```python
@app.get("/api/v1/empleados", dependencies=[Auth])
async def listar_empleados(dni=..., solo_activos: bool = Query(default=False)):
    ...
    return {"ok": True, "total": len(datos), "data": [asdict(e) for e in datos]}
```

El script lo lee **bien**: exige `ok` verdadero, exige que `data` sea lista,
descarta los elementos que no sean `dict`, y de cada empleado usa `dni_norm`
(con respaldo a `dni`), `nombre`, `apellidos` y `estado` — todos campos
reales del dataclass `Empleado`. Preferir `dni_norm` es lo correcto: es la
«clave de casado» con la que `sesame-api` indexa, y es la que luego aceptan
`/festivos?dni=` y `/jornada?dni=`. El parámetro se manda como
`solo_activos=true|false`, que es lo que FastAPI espera para un `bool`.
Además el script no asume `total`, que el endpoint omite en la rama
`?dni=`: solo usa `data`. Correcto.

**5. Ruff.** Limpio en lo nuevo, verificado por mí:

```
$ python -m ruff check services/partes-front/validar_datos_sesame.py \
    services/partes-front/tests/test_f013_informe_sesame.py --output-format=concise
All checks passed!  (exit=0)
```

Los 450 avisos que reporta `init.sh` son deuda previa del repositorio, ajena
a esta rama. Los cinco `# noqa` del script están **todos justificados en la
misma línea o encima**: `TRY004` (un contrato roto del servicio remoto se
señala con `RuntimeError`, la señal de aborto del módulo, igual que en
`SesameApiClient` — de acuerdo), `DTZ011`/`DTZ005` (hora local a propósito:
el «año en curso» y el sello del fichero son los del humano que lo lanza — de
acuerdo) y dos `BLE001` en los `except Exception` de `construir_fila` y
`calendario_por_defecto`, que son precisamente el mecanismo del
`acceptance` 2: ahí capturar ancho **es** el requisito, no un descuido.

**6. Barrido de secretos sobre los ficheros nuevos.** Patrones usados:
`(api[_-]?key|secret|password|passwd|token|bearer|connectionstring|
subscription|tenant)\s*[:=]\s*["'][^"'{<$]{8,}` y
`([0-9]{1,3}\.){3}[0-9]{1,3}|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-` (IPs y GUID).
**Sin coincidencias.** La única constante parecida es
`CLAVE = "clave-de-test"` en el fichero de tests, que es un literal
evidentemente ficticio.

**7. Muestra real del Markdown y del CSV.** Generada por mí con
`MockTransport`, incluyendo a propósito un festivo cuyo nombre lleva una
barra (`"Ano Nuevo | raro"`) para atacar el escapado de la tabla. La tabla
Markdown **no se parte** (sale `Ano Nuevo \| raro`), el CSV entrecomilla
correctamente el campo con `;` y comillas internas, y el fichero `.csv`
empieza por BOM (`b"\xef\xbb\xbf"` → `True`), como exige `CONVENTIONS.md`
para el Excel español. El filtrado al año funciona: el festivo de
`2025-12-25` no aparece en el informe de 2026. `--incluir-inactivos`
funciona: cabecera `Ambito: todos` y el empleado `inactive` incluido.

---

## Cambios requeridos (bloqueantes)

**1. Completar el análisis del superviviente DENTRO de
`progress/mutacion_F-013.md`.**

- **Fichero y sitio:** `progress/mutacion_F-013.md`, líneas 36-40, sección
  `### 1. services/partes-front/validar_datos_sesame.py:374 [entero]` →
  `#### Análisis (PENDIENTE del implementer)`.
- **Qué falla:** conserva literalmente la plantilla que genera la
  herramienta, con `PENDIENTE` en las dos líneas. `CHECKPOINTS.md` §C4 bis
  exige «Cada superviviente de esa campaña tiene su sección de análisis
  **completada** (ninguna en `PENDIENTE`)», y `.claude/agents/reviewer.md`
  §4 repite «**ningún superviviente con su análisis en `PENDIENTE`**». Es un
  checkbox vacío en C1–C5, y eso es CHANGES_REQUESTED por protocolo.
- **Qué hay que hacer:** trasladar a esa sección el análisis que ya está
  escrito —y que doy por **correcto y suficiente**— en
  `progress/impl_F-013.md` §«Análisis del superviviente», y sustituir el
  título `(PENDIENTE del implementer)` por uno que no diga PENDIENTE.
  Contenido mínimo: que el mutante es **equivalente para esta suite** porque
  `transport or httpx.HTTPTransport(retries=1)` **cortocircuita** —con
  `MockTransport` inyectado el constructor nunca se evalúa—, que cazarlo
  exigiría abrir una conexión real y `CONVENTIONS.md` lo prohíbe, y que el
  número de reintentos no altera ningún resultado observable del informe
  (el error final ya está cubierto por
  `test_f013_r_sesame_api_inalcanzable_aborta`).
- **Por qué no lo perdono siendo un copiar-pegar:** `mutacion_F-013.md` es el
  artefacto de registro de la campaña y es el fichero que abrirá quien
  audite esto dentro de seis meses —o la próxima campaña de mutación—. Tal
  como está hoy, ese lector concluye que un superviviente se quedó sin
  analizar. La regla existe justo para que el análisis viva pegado al
  superviviente, no en otro documento.

No hay ningún otro cambio requerido. Confirmado el punto 1, el veredicto es
APPROVED sin más trabajo: no hace falta volver a tocar código ni tests, ni
relanzar la campaña (los totales ya están verificados en este informe).

## Hallazgos no bloqueantes

- **NB-1 · El «Resumen» de festivos puede leerse mal.** En
  `render_markdown`, la distribución «Festivos por trabajador» solo cuenta a
  quienes tienen `festivos_ok`. En mi muestra de 3 empleados salía
  «2 festivos: 1 trabajador» y los otros dos simplemente no aparecían en esa
  lista, sin decir por qué. La cabecera («Empleados: 3 (2 con errores)») y la
  lista de errores lo compensan, y la decisión de **no** contar un cero falso
  es acertada —es exactamente el número que el humano validaría por bueno—,
  pero una línea extra del tipo `- (no se pudo leer): 2 trabajadores`
  cerraría la suma a ojo. Sugerencia para cuando el humano use el informe de
  verdad; no bloquea.
- **NB-2 · `--solo-activos` es un argumento inerte.** En `_parse_args` se
  declara junto a `--incluir-inactivos` en un grupo mutuamente excluyente,
  pero `main` solo lee `args.incluir_inactivos` (`solo_activos = not
  args.incluir_inactivos`). Pasar `--solo-activos` no cambia nada respecto a
  no pasar nada. No es un bug —el comportamiento por defecto ya es ese, y el
  flag documenta la intención y bloquea la combinación contradictoria—, pero
  conviene saberlo antes de «arreglarlo» a ciegas.
- **NB-3 · `progress/current.md` arrastra una contradicción previa.** El
  bloque de F-004 dice «Estado: `pending`, spec ESCRITA … Falta la
  aprobación del humano (→ `spec_ready`)» y, más abajo, «Spec F-004
  APROBADA». Las dos frases no pueden ser ciertas a la vez. **No es de esta
  feature**: el diff de `current.md` en esta rama solo añade la sección de
  F-013 (+29 líneas), y esa contradicción viene de `da7293d`. Lo dejo
  anotado para que el líder la limpie al retomar F-004.
- **NB-4 · La suite de sv4 no cubre el arranque del script como `__main__`.**
  Es la única línea sin cubrir del diff (`if __name__ == "__main__":`,
  99.6 % de cobertura). Correctamente asumido; anotado solo para que conste
  que se revisó qué era ese 0.4 % y no es nada relevante.
- **NB-5 · Elogio, no queja.** Dos decisiones de diseño merecen quedar
  escritas porque son las que hacen útil esta herramienta y podrían
  «simplificarse» por error en el futuro: (a) usar el `SesameApiClient` **en
  crudo** y no el `CalendarioProvider`, porque la cascada de respaldo de
  F-003 taparía justo los 404 que el informe existe para destapar; y (b)
  `festivos_ok`, que distingue «cero festivos» de «no se pudo leer». Ambas
  están razonadas en el docstring del módulo y en el informe. Que el
  implementer detectara además, vía mutación, dos bugs reales del lector de
  `.env` (una variable comentada con `=` que se habría aplicado, y una clave
  en base64 terminada en `=` que habría reventado el parseo) es exactamente
  para lo que sirve la campaña.

## Propuestas de automejora del arnés (para que las apruebe el humano; NO aplicadas)

- **AM-1 · Nomenclatura de tests en features `sdd=false`.** `CHECKPOINTS.md`
  §C4 pide tests trazables «`test_fXXX_rN_*`», pero en una feature sin spec
  no hay requisitos EARS `RN`: hay criterios `acceptance`. F-013 ha resuelto
  esto solo, y bien, con `test_f013_a1_*` / `test_f013_a2_*`. Propongo
  añadir a la nota de cabecera de `CHECKPOINTS.md` (la de features
  `sdd=false`) una frase que oficialice el patrón `test_fXXX_aN_*` para
  criterios `acceptance`, de modo que el próximo implementer no tenga que
  elegir a ciegas ni el próximo reviewer que decidir si lo perdona.
  Aplicable a cualquier proyecto ⇒ si se acepta, va también a `arnes-base`.
- **AM-2 · La base del diff debería constar en `features.json`, no solo en
  la memoria del implementer.** `harness.alcance` usa `dev` por defecto.
  Cuando una feature se ramifica de otra aún no mergeada —como F-013 desde
  la punta de F-004— ese defecto infla el alcance a ficheros ajenos (aquí:
  19 ficheros de F-003/F-004 en vez de 1). El implementer lo resolvió bien
  pasando `--base da7293d`, y el informe lo declara, pero **nada lo obliga**:
  quien olvide el flag obtiene una campaña de mutación y una cobertura sobre
  código que no ha escrito, y el reviewer tiene que adivinar cuál era la
  base correcta. Propongo un campo opcional `base` en la entrada de la
  feature de `harness/features.json`, que `harness.alcance` lea antes de
  caer en `dev`, y que `init.sh` imprima en la línea de la puerta de
  cobertura. Genérico ⇒ `arnes-base`.
- **AM-3 · El protocolo del reviewer debería exigir comparar el `--base` de
  la campaña con el de la puerta.** Ligado a AM-2: hoy `.claude/agents/
  reviewer.md` §4 manda recalcular alcance y mutantes, pero no dice **con qué
  base**. Si el reviewer recalcula con la base por defecto y el informe usó
  otra, los números no cuadran y el falso positivo parece fraude (me ha
  pasado en esta review: el primer recálculo dio 19 ficheros y hubo que
  investigar). Bastaría añadir: «recalcula con la MISMA base que declara la
  sección *Alcance* del informe, y comprueba que esa base es la de la rama».
  Genérico ⇒ `arnes-base`.

---

## Resumen para el líder

Trabajo de calidad alta: alcance quirúrgico (1 fichero de producción, 573
líneas), fase RED demostrable en el historial, 40 tests sin red, 73 de 74
mutantes muertos con el único superviviente genuinamente equivalente, ruff
limpio, sin fugas de la clave, sin invadir capas ni tocar la duplicación
tolerada, y el contrato de `sesame-api` leído correctamente contra el código
real del otro repositorio. Todo verificado de forma independiente y con
ejecución propia, no leído del informe.

Se rechaza por **un** motivo formal y bien delimitado: el análisis del
superviviente está escrito en `impl_F-013.md` en vez de en
`mutacion_F-013.md`, que sigue diciendo `PENDIENTE`. Es un traslado de texto.
Hecho eso, esto pasa a APPROVED sin más verificaciones.
