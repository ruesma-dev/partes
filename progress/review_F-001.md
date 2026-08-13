<!-- progress/review_F-001.md -->
# F-001 · Test de estructura del monorepo (calentamiento) — informe de review

- **Veredicto: APPROVED**
- Rama revisada: `feature/F-001-test-estructura` (confirmada con
  `git branch --show-current`).
- Modo: `sdd=false` → se valida contra los `acceptance` de
  `harness/features.json`, no contra `specs/`.
- Fecha: 2026-08-13.

## Nivel de rigor

Declarado en `harness/features.json`: **`estandar`** (valor válido de
`harness/rigor.json`). Exige, además de C1–C3, C3 bis y C5: tests trazables
(C4), **fase RED** en los requisitos centrales, **cobertura** de las líneas
cambiadas y **campaña de mutación** con supervivientes analizados. No hay
omisión del campo, así que no se aplica el `critico` por defecto.

## Verificación independiente (ejecutada por el reviewer, no leída del informe)

| Comprobación | Comando | Resultado real |
|---|---|---|
| Portero del arnés | `bash harness/init.sh` (tal cual) | `ENTORNO LISTO. Puedes trabajar.` · **exit code 0** |
| Suite de la raíz | `./.venv/Scripts/python.exe -m pytest tests -q` | **6 passed in 0.06s** |
| Lint de lo nuevo | `python -m ruff check tests --output-format=concise` | `All checks passed!` |
| Diff de la rama | `git diff --name-status dev...HEAD` | 4 altas, 0 modificaciones, 0 bajas |
| Contador global de ruff | salida de `init.sh` | **444 avisos**, idéntico a la línea de partida del informe |

Diff completo frente a `dev` (no hay ningún fichero fuera del alcance
confirmado por el humano en `progress/current.md`):

```
A       progress/impl_F-001.md
A       progress/mutacion_F-001.md
A       tests/conftest.py
A       tests/test_estructura_monorepo.py
```

Los dos primeros son el rastro documental que el propio arnés exige; el
alcance de código es exactamente `tests/conftest.py` y
`tests/test_estructura_monorepo.py`. Nada en `services/`, nada de CI.

## Checkpoints

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit code 0. Ejecutado por el
      reviewer, no citado del informe.
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md` — el propio `init.sh` los verifica uno a uno y
      todos salen `[OK]`.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress` (`F-001`); `init.sh` lo confirma:
      «7 features, 7 abiertas, en curso: ['F-001'], bloqueadas: ninguna».
- [x] Rama actual `feature/F-001-test-estructura`, la declarada en
      `features.json`. No es `main` ni `dev`.
- [x] `progress/current.md` describe SOLO la sesión activa (F-001), sin
      restos de sesiones anteriores.
- [x] Ninguna feature está `done` todavía, así que no falta ningún resumen en
      `progress/history.md` (está en plantilla vacía, coherente).

### C3 — El código respeta arquitectura y convenciones

- [x] **Arquitectura hexagonal**: N/A **justificado** — la feature no añade
      dominio, aplicación ni infraestructura de ningún servicio. Los dos
      ficheros viven en `tests/` (raíz), que es exactamente la capa que
      `CLAUDE.md` reserva para «tests del monorepo como conjunto». Ningún
      servicio de `services/` se toca.
- [x] **Primera línea con la ruta relativa**: `# tests/conftest.py` y
      `# tests/test_estructura_monorepo.py`. Correctas ambas.
- [x] **Sin `print()`, sin TODO/FIXME, sin secretos**: barrido con
      `grep -nE "print\(|TODO|FIXME|password|passwd|secret|api_key|token|connectionstring" tests/*.py`
      → *sin coincidencias*. **Sin dependencias nuevas**: los imports son
      `json`, `pathlib`, `sys`, `pytest` y `harness.servicios`; `harness/servicios.py`
      a su vez solo importa `argparse`, `json`, `sys`, `dataclasses` y
      `pathlib`. Ni una librería de red ni un driver de BBDD en toda la
      cadena — esto es la prueba de que R1 («sin red ni BBDD») se cumple por
      construcción y no por promesa.
- [x] **Reglas de dominio de `docs/ARCHITECTURE.md`** y las tres trampas del
      monorepo: N/A **justificado**. (1) *empleado ≠ recurso*: no hay lógica
      de registro ni de líneas `hmores`; (2) *incidencias*: no se toca el
      cómputo de rachas CI*/CIZ; (3) *schema duplicado*: `orm_models.py` de
      sv3 y sv4 no aparece en el diff. La feature no escribe en Sigrid, ni en
      PostgreSQL, ni en colas.

### C3 bis — Documentos que entran de fuera

**N/A justificado**: el diff no añade ni modifica ningún fichero bajo
`docs/referencia/` (verificado en `git diff --name-status dev...HEAD`, que
solo trae `progress/` y `tests/`). No hay original ofimático ni PDF que
pudiera haber entrado, luego no hay barrido de datos sensibles que ejecutar
sobre documentos nuevos. El barrido de secretos sobre el código sí se hizo
(C3, tercer punto).

### C4 — La verificación es real

- [x] Cada criterio `acceptance` tiene ≥ 1 test trazable con el patrón
      `test_f001_rN_*`, y todos pasan (tabla de cobertura más abajo).
- [x] Los unit tests no tocan red ni BBDD: solo sistema de ficheros del
      propio repositorio y `tmp_path` de pytest. Sin mocks porque no hay nada
      externo que mockear. Verificado leyendo los imports de toda la cadena,
      no solo del test.
- [x] Verificaciones `MANUAL (humano)`: **ninguna**, y consta por escrito en
      `progress/impl_F-001.md` («La feature no toca Sigrid, ni PostgreSQL, ni
      Azure, ni el portal»). Comprobado contra el diff: es cierto. Al no
      haberlas, no hay nada que listar en `current.md`.

### C4 bis — El rigor declarado se cumple

- [x] La feature declara `rigor: "estandar"`, valor válido según
      `harness/rigor.json` (`init.sh`: «niveles: critico, documental,
      estandar; por defecto critico; umbral de cobertura 80%»).
- [x] **Fase RED — verificada por reproducción independiente.** El
      entregable de F-001 *es* el test, así que aplica el procedimiento
      específico de C4 bis: romper en copia aislada lo que el test vigila. El
      informe pega tres roturas; **el reviewer las ha reproducido él mismo**
      en una copia fuera del repositorio
      (`…/scratchpad/red-rev`, con `harness/` + `tests/` y un árbol de
      servicios de mentira), obteniendo salidas idénticas a las declaradas:

      - Espejo fiel de partida: `6 passed`.
      - **Rotura A** (se borra `services/partes-api`): `3 failed, 3 passed`,
        con `ValueError: servicio 'sv2-extraccion': la ruta
        'services/partes-api' no existe en el repositorio` desde
        `harness/servicios.py:133` — y `133` es, en efecto, la línea del
        `raise` en el árbol real.
      - **Rotura B** (`services/partes-transfer` sin `main.py`):
        `1 failed, 5 passed`, `AssertionError: servicio 'sv5-transfer' … no
        tiene ninguno de ['main.py', 'pyproject.toml']`.
      - **Rotura C** (se sustituye por `pass` el bloque `is_dir()` de
        `_comprobar_conjunto`): `1 failed, 5 passed`, con
        `Failed: DID NOT RAISE ValueError` en el test de R2 — que es la
        rotura que ataca directamente al criterio R2.

      Tras las tres reproducciones, `git status --short` en el repositorio
      real sigue mostrando únicamente ` M harness/features.json` y
      ` M progress/current.md`, los dos cambios del líder: **el árbol real no
      se tocó**, ni por el implementer ni por el reviewer. Las trazas del
      informe son reales, no redactadas a mano.

- [x] **Cobertura**: `init.sh` imprime
      `[OK] PUERTA COBERTURA: N/A (F-001 no cambia líneas Python de
      producción frente a dev)`. Es un **N/A con el motivo impreso por la
      herramienta**, que es exactamente la forma que CHECKPOINTS.md admite;
      no es una puerta omitida. El motivo es además verificable: el diff no
      contiene ni un fichero Python fuera de `tests/`.

- [x] **Mutación — totales recalculados de forma independiente.** Existe
      `progress/mutacion_F-001.md` generado por la herramienta, y declara 0
      mutantes / 0 supervivientes. Como una campaña en cero no distingue por
      sí sola entre «no había nada que mutar» y «el generador está roto o el
      informe es falso», se han hecho las dos comprobaciones que exige el
      protocolo:

      1. **Recálculo del alcance** con `harness.alcance.alcance_de_feature("F-001")`:
         `0 fichero(s), 0 línea(s) de producción (origen rama,
         165187f…..feature/F-001-test-estructura)`. Coincide con el informe,
         incluidas las referencias del diff.
      2. **Recálculo de mutantes** con `harness.mutacion.generar_mutantes`
         (cálculo puro, sin ejecutar la suite): **0**, igual que el informe.
      3. **Prueba de control** — mismo diff, **ignorando** la exclusión de
         alcance: el generador produce **9 mutantes** (2 en
         `tests/conftest.py`, 7 en `tests/test_estructura_monorepo.py`;
         operadores `entero`, `booleano` y `comparacion`, p. ej.
         `if servicio.lenguaje != "python":` → `== "python"`). **El generador
         funciona**: el cero de la campaña es legítimo y viene de la
         exclusión por diseño de `tests/` en `es_produccion()`, no de una
         herramienta rota ni de un informe inventado.

- [x] **Supervivientes**: cero, y ninguna sección en `PENDIENTE`. No hay
      materia mutable, según lo verificado arriba. (La exigencia adicional de
      «cero supervivientes» es de nivel `critico`; aquí se cumple de todas
      formas.)
- [x] El informe del implementer trae la sección **«Evidencias»** con los
      cuatro números: 6 tests / 6 passed, cobertura N/A con motivo impreso,
      0 mutantes y 0 supervivientes, y 0,25 s de suite (0,49 s bajo
      `coverage`). Contrastados uno a uno con las ejecuciones del reviewer.
- [x] Ningún punto de este bloque marcado N/A sin justificación escrita.

### C4 ter — Rutas sensibles

**N/A sin nada que justificar**, por la configuración explícita de
CHECKPOINTS.md: `harness/rutas_sensibles.json` **no existe** en este
repositorio (solo está el `.ejemplo.json`), comprobado por el reviewer. Sin
declaración, el bloque entero no aplica y la puerta de `init.sh` no señala
ninguna ruta tocada.

### C5 — La sesión se cerró bien

- [x] `tasks.md`: **N/A justificado** por la nota de cabecera de
      CHECKPOINTS.md para features `sdd=false` — no hay `specs/F-001-*/`. El
      formato mínimo de commit que esa nota exige (`F-XXX: <descripción>`) se
      cumple con creces: los tres commits usan el formato completo
      `F-001 Tn: …`, en español, uno por tarea.

      ```
      d682ed0 F-001 T1: conftest de la suite raiz para que pytest resuelva imports desde la raiz del repo
      c3aeb58 F-001 T2: test de estructura del monorepo (rutas declaradas, punto de entrada y rechazo de ruta inexistente)
      813121e F-001 T3: informe de implementacion con la fase RED en copia aislada y la campana de mutacion
      ```

- [x] Sin ficheros temporales ni artefactos sin trackear:
      `git status --porcelain --untracked-files=all` no devuelve ni una línea
      `??`. Los únicos cambios pendientes son ` M harness/features.json` y
      ` M progress/current.md`, ambos del líder y coherentes con una feature
      en curso. La copia aislada de la fase RED (tanto la del implementer
      como la del reviewer) vive fuera del repositorio.
- [x] `features.json` refleja el estado real: `F-001` en `in_progress`. El
      paso a `done` corresponde al líder tras este veredicto.

## Cobertura: criterio `acceptance` → test que lo cubre

| # | Criterio `acceptance` | Test que lo cubre | Estado |
|---|---|---|---|
| R1 | `tests/test_estructura_monorepo.py pasa sin red ni BBDD` | `test_f001_r1_la_declaracion_de_servicios_no_esta_vacia`, `test_f001_r1_cada_ruta_declarada_existe_y_es_un_directorio`, `test_f001_r1_cada_servicio_python_tiene_punto_de_entrada` | PASA · la ausencia de red/BBDD está verificada por la cadena de imports, no solo declarada |
| R2 | `El test falla si se declara un servicio con ruta inexistente` | `test_f001_r2_una_ruta_inexistente_hace_fallar_la_validacion`, con dos controles: `…_la_misma_declaracion_con_la_ruta_creada_si_carga` y `…_la_declaracion_real_del_repositorio_no_se_toca` | PASA · y la rotura C demuestra que el test cae si la validación desaparece |
| R3 | `bash harness/init.sh en verde` | Sin test propio, por construcción: `init.sh` es quien ejecuta esta suite | CUMPLIDO · exit code 0 verificado por el reviewer |

Dos cosas que elevan la calidad por encima del mínimo y conviene dejar
escritas, porque son justo lo que separa un test que pasa de un test que
sirve:

1. El **test de control** `…_la_misma_declaracion_con_la_ruta_creada_si_carga`
   usa la declaración palabra por palabra idéntica a la del test de R2,
   cambiando solo que la carpeta existe. Sin él, un validador que rechazara
   *todo* pasaría por bueno el test de R2. Es el antídoto correcto contra el
   `pytest.raises` complaciente.
2. El test de R2 **afirma sobre el contenido del mensaje** (nombre del
   servicio y ruta que falla), no solo sobre el tipo de excepción. Un
   `ValueError` mudo no arregla nada a las 3 de la mañana.

## Cambios requeridos

Ninguno. No hay nada que bloquee el cierre.

## Observaciones (no bloqueantes, para el humano)

1. **`pyproject.toml` como punto de entrada alternativo.** El test admite
   `main.py` **o** `pyproject.toml` (`PUNTOS_DE_ENTRADA`, línea 35 de
   `tests/test_estructura_monorepo.py`), mientras que `docs/ARCHITECTURE.md`
   dice «Puntos de entrada: `main.py` en todos» y la `description` de F-001
   habla de `main.py`. Hoy no hay divergencia práctica —los cinco servicios
   tienen `main.py`, y así lo comprueba el test contra el árbol real—, y el
   implementer documenta la decisión de forma razonada. Pero es una tolerancia
   un pelo más laxa que la norma escrita: si un servicio perdiera `main.py`
   quedándose solo con `pyproject.toml`, el test no lo cazaría y
   `ARCHITECTURE.md` sí lo prohibiría. Se aprueba tal cual; **cuando algún
   servicio se empaquete de verdad, que esa feature actualice
   `ARCHITECTURE.md` y este test a la vez**, en lugar de dejar que se separen
   en silencio.
2. **`test_f001_r2_la_declaracion_real_del_repositorio_no_se_toca` es un
   guardarraíl débil**, y conviene saberlo: solo demuestra que
   `_escribir_declaracion` sobre `tmp_path` no altera el fichero real, cosa
   que hoy es evidente por la firma de la función. Su valor es de
   documentación y de futuro (si alguien parametrizara el helper), no de
   detección. No sobra —cuesta cuatro líneas— pero no debe contarse como
   cobertura de R2: quien cubre R2 de verdad son los otros dos.
3. **Los seis `[AVISO]` de «NADIE está comprobando los tests de …»** (uno por
   servicio) siguen exactamente igual que antes de F-001, y así debe ser:
   crear las suites de cada servicio estaba explícitamente fuera del alcance
   confirmado. Queda anotado aquí para que no se pierda: el arnés está
   avisando de un hueco real de este monorepo, y merece feature propia.

## Automejora del protocolo (propuesta, no aplicada)

La prueba de control del cero de mutación —regenerar mutantes ignorando la
exclusión de alcance para distinguir «no hay nada que mutar» de «el generador
está roto»— funcionó exactamente como se pretendía y se resolvió en una sola
ejecución. Pero está descrita solo en `.claude/agents/reviewer.md`, no en
`CHECKPOINTS.md`. Sugerencia para el humano: **añadir a C4 bis una frase que
la exija explícitamente cuando la campaña declare cero mutantes**, para que
un reviewer que trabaje solo con `CHECKPOINTS.md` delante no la omita. Si se
acepta, es una mejora genérica y habría que portarla a `arnes-base` en el
mismo trabajo.

## Veredicto final

**APPROVED.** El circuito completo del arnés queda validado en este
repositorio: portero en verde, fase RED demostrada y reproducida de forma
independiente, campaña de mutación con sus totales recalculados y su cero
justificado por prueba de control, trazabilidad requisito→test completa y
ningún checkpoint vacío. Procede que el líder pase F-001 a `done` y anote su
resumen en `progress/history.md`.
