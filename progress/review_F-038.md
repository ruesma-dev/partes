<!-- progress/review_F-038.md -->
Revisión completa (pasada 1) · `git diff 0926857...6896bc9` (rama `feature/F-038-limite-filas-sigrid`)

# F-038 · Review del reviewer (pasada 1)

**Veredicto: CHANGES_REQUESTED** — el código, los tests y la campaña están bien; lo que falla es
papeleo de cierre (tres puntos de C4, C4 bis y C5), arreglable sin tocar producción.

**Nivel de rigor: `estandar`** (declarado en `harness/features.json`): C1–C5, C3 bis, C4 bis con
fase RED, cobertura de lo cambiado y mutación con supervivientes analizados.

## Checkpoints

- **C1** [x] `bash harness/init.sh` (este reviewer, sobre 6896bc9): exit 0, «ENTORNO LISTO» (raíz 522 passed + 3 skipped; sv2 170; sv3 2340; sv4 2609 + 1 skipped en 1.145 s; sv5 899; sv1 por caché) ·
  [x] existen los siete ficheros base.
- **C2** [x] una sola `in_progress` en la rama (F-038; F-060 en paralelo por excepción expresa del
  humano, registrada en `requirements.md`) · [x] rama `feature/F-038-limite-filas-sigrid` ·
  [x] `current.md` lleva F-038 activa y los pendientes de despliegue de F-059 (práctica del repo) ·
  [x] ninguna `done` nueva.
- **C3** [x] hexagonal: límites en `config/settings.py`, cliente en `infrastructure/sigrid/`,
  cableado en `interface_adapters/` y `main.py`; nada en `domain/` · [x] primera línea con ruta en
  los cinco ficheros nuevos · [x] sin `print`, sin TODO, sin dependencias nuevas · [x] sin secretos,
  nombres ni DNI: barrido del diff añadido (DNI `\d{8}[A-Z]`/NIE, `password|secret|key=`, GUID,
  IP `10.x`, correos, `AccountKey|sig=`): solo `CLAVE = "clave-de-test-f038"`, `function_key=CLAVE`
  y el DNI sintético `00000001R` de los tests · [x] trampas del dominio: no aplican (no toca
  registro, incidencias ni `orm_models.py`) · [x] LÍMITE DE SERVICIO: cada servicio cambia solo su
  settings y su cliente; la constante 500.000 es configuración por servicio (`design.md` §2), no
  lógica copiada; la regla común la vigila un guardián de raíz, no una copia.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] trazabilidad completa (tabla abajo), todo verde · [x] sin red ni BBDD (`httpx`
  sustituido; `.env` del script sustituido en memoria) · **[ ] MANUAL con comando exacto en
  `current.md`**: la M2 (humano, tras desplegar) solo aparece como «comandos exactos en
  `design.md` §9»; es el mismo defecto que rechazó la pasada 1 de F-059 (cambio 1).
- **C4 bis** [x] `rigor` declarado · [x] fase RED con trazas reales de T1, T2, T4, T5, T6 y T7 ·
  [x] cobertura: `PUERTA COBERTURA: 100.0% de 19 líneas cambiadas cubiertas (19/19, umbral 80%)` · [x] mutación verificada de forma independiente (abajo) · [x] campaña de
  2.820,9 s > 60 s: **no reejecutada**, recálculo puro + RM1–RM6 + RM4 · [x] coste por mutante
  2.820,9 × 1 ÷ 20 = 141 s, ≫ 1 s · [x] sin «⚠ CAMPAÑA NO VÁLIDA», «Sin veredicto» 0 ·
  [x] RM1 · [x] RM2 · N/A RM5 (nivel `estandar`; además ningún superviviente se declaró
  equivalente) · N/A RM6 (no se quitó código defensivo: se añadió un test) · N/A campaña manual
  (la automática dio 26 mutantes) · [x] los 3 supervivientes analizados, ninguno `PENDIENTE` ·
  **[ ] «Evidencias» sin el nº de workers** (el informe de mutación dice 1; el de impl no lo dice,
  y C4 bis lo exige ahí) · [x] ningún N/A sin motivo.
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5** **[ ] `tasks.md`**: T9 (mutación, commit `6896bc9 F-038 T9`) y T12 (`init.sh`, en verde
  según el informe y este reviewer) siguen en `[ ]`, y T12 no tiene commit `F-038 T12:`. T10 y T11
  en `[ ]` son legítimos (MANUAL; M0 hecha por el líder, M1 no bloquea, M2 tras desplegar) ·
  [x] sin temporales trackeados · [x] `features.json` `in_progress`, correcto hasta el cierre.

## Mutación: verificación independiente

- **Recálculo puro** (`harness.alcance.alcance_de_feature("F-038", base="0926857")` +
  `generar_mutantes` por fichero): **14 ficheros, 82 líneas, 26 mutantes** = informe. Muestreo
  reproducido con `random.Random(20260820).sample(·, 20)`: los 20 coinciden e incluyen los 3
  supervivientes `gt=0, le=200)` → `gt=1, le=200)` en sv4 l.57, sv3 l.72 y sv5 l.25 (mismo
  operador `entero`, mismo texto).
- **RM1**: SHA medido `45db3be`; `git diff --stat 45db3be 6896bc9` solo toca `progress/` y los
  cuatro `test_f038_sigrid_limite.py`: el alcance de producción no cambió.
- **RM2**: 20 × 141,0 = 2.820 s = «Tiempo total»; con 1 worker la media (141 s) cae entre la base
  más barata (12,3 s, sv2) y la más cara (542 s, sv4), coherente con la mezcla 3/5/6/6 de mutantes
  por servicio y `-x`. Sin salto de orden de magnitud.
- **RM3**: ninguno de los 17 muertos es equivalente: los `500_000 → 500001` los mata la igualdad
  exacta de R2/R10; `ge=1 → ge=2` el borde «1»; `le=500_000 → 500001` el «500001»;
  `le=200 → 201` el «200.5».
- **RM4** (tercera vía, sobre copia `git archive` en el scratchpad): sv5 y sv2 con `gt=1` ⇒
  `test_f038_r14_timeout_por_debajo_de_1_vale` da **2 failed, 5 passed** en los dos; el árbol de
  trabajo no se tocó. Confirma el cierre de los 3 supervivientes sin relanzar la campaña.

## Cobertura de requisitos (requisito → test)

| Req. | Tests |
|---|---|
| R1 | `test_f038_r1_*` en sv2 (`fetch_tipos_hora`), sv4 (sin paginar) y sv5 (17 lecturas, una por fila de §1); sv3 no tiene lectura sin paginar con llamador: lo cubre `test_f038_r2_*` vía `_post_sql_read` |
| R2 | `test_f038_r2_defecto_500000_en_settings_y_constructor` (×4) |
| R3 | `test_f038_r3_max_rows_fuera_de_rango_no_arranca` y `_en_los_bordes_vale` (×4) |
| R4 | `test_f038_r4_paginadas_piden_pagina_mas_una` (sv3, sv4) |
| R5 | `test_f038_r5_*_cablea_max_rows`: sv2 `build_app`, sv3 `app` + `medir_casado`, sv4 `build_app`, sv5 `app` + `main` + `comprobar_asiento` |
| R6 | `test_f038_r6_log_de_instanciacion_sin_la_clave` (×4) |
| R7 / R8 | sv2 `test_f038_r7_*` (×2), `test_f038_r8_*` (vacío + WARNING; caché anterior) |
| R9 | `test_f038_r9_*` en sv3 (todas + suelta), sv4 y sv5 (sin lote) |
| R10 | sv5 `test_f038_r10_script_truncated_termina_sin_filas` y `_sin_truncated_devuelve_filas` |
| R11–R13 | raíz `test_f038_r11_*`, `r12_*`, `r13_*` + pruebas de verdad con código sintético |
| R14 | `test_f038_r14_*` (fuera de rango, 200 vale, (0, 1] vale) ×4 |
| R15 | sv5 `test_f038_r15_timeout_200_plazo_http_230` |
| R16 | fichero borrado y línea de `ARCHITECTURE.md` quitada (comprobado); si reapareciera como lector lo caza `test_f038_r11_lectores_son_la_lista_cerrada` |
| R17 | revisado a mano: `ARCHITECTURE.md` «Acceso a datos» y `azure-apps/partes.md` §3.3 y §5.6 filas sv2–sv5 (commit local c581115), con 500.000, rango 1–500.000, (0, 200] y `truncated` = error |

Desviación aceptada: umbral del guardián R13 = 500.000 (no 200.000), coherente con DA1 = B.
Borrado de `consulta_reshor_recursos.py` sin purgar el historial: decisión del humano, no defecto.

## Cambios requeridos

1. `progress/current.md`, bloque F-038: añadir la **M2 con su comando exacto** (no un enlace a
   `design.md` §9): `az containerapp logs show -n ca-sv5-transfer -g rg-partes-dev --tail 80` y el
   mismo con `ca-sv4-front`, esperado `max_rows=500000` en la línea `Instanciado` (y `timeout_s`
   60/30). Copiar también los tres SQL de la M1 o dejarla marcada «no bloquea» con su comando.
   De paso, quitar la línea `[ ] **M0 · T10**` (contradice la `[x] M0 hecha` de encima) y
   actualizar la cabecera («pendiente: mutación del líder, M0, review» ya no es cierto).
2. `specs/F-038-limite-filas-sigrid/tasks.md`: marcar `[x]` T9 y T12, y hacer el commit de cierre
   como `F-038 T12: ...` (hoy no hay ninguno con ese prefijo). T10 y T11 se quedan `[ ]` (MANUAL).
3. `progress/impl_F-038.md`, «Evidencias»: añadir «workers: 1» a la fila de mutantes.

## Observaciones (no bloquean)

- `tasks.md` T11 y `design.md` §9 esperan `max_rows=200000` en la M2; con DA1 = B es **500000**
  (`current.md` ya lo dice bien). Lo cubre la nota de `requirements.md`, pero conviene que el
  comando de `current.md` lleve el valor correcto para que el humano no dude.
- Queda en el disco del worktree `services/partes-front/__pycache__/consulta_reshor_recursos.cpython-312.pyc`
  (ignorado por git, no versionado), compilado del script borrado: lleva sus DNI y nombres.
  Recomendado borrarlo a mano, aquí y en el árbol principal si existe.
- sv5 manda `timeout_seconds = int(timeout)`: con un timeout en (0, 1) mandaría 0. Preexistente y
  sin uso real (Azure: 60), fuera del alcance de F-038.

## Automejora (propuesta, no aplicada)

- `CHECKPOINTS.md` C4: decir explícitamente que «comando exacto en `current.md`» excluye remitir a
  `design.md`; es el segundo rechazo por lo mismo (F-059, F-038).

---
Revisión incremental desde c7aaa1e (pasada 2) · `git diff c7aaa1e..4ef9d3c` (HEAD 4ef9d3c)

# Pasada 2 · **Veredicto: APPROVED** (rigor `estandar`, declarado)

- **Delta solo Markdown**: `current.md`, `impl_F-038.md`, `design.md`, `tasks.md`; ni producción ni
  tests. Lo aprobado en la pasada 1 (código, tests, mutación con RM1–RM4) queda por bueno.
- **C1** [x] `bash harness/init.sh` reejecutado por este reviewer sobre 4ef9d3c: exit 0, «ENTORNO
  LISTO»; raíz 522 passed + 3 skipped; sv1–sv5 en verde por caché del arnés («árbol sin cambios desde
  el último verde», coherente con un delta solo Markdown); cobertura 19/19; tamaño review 116/140.
- **Cambio 1** [x] `current.md`: M2 con comando exacto (`az containerapp logs show` de sv5 y sv4),
  esperado `max_rows=500000` y `timeout_s` 60/30; M1 con su comando y los tres SQL, «NO BLOQUEA»;
  quitada la `[ ] M0` contradictoria; cabecera al día. Así queda resuelto C4 MANUAL.
- **Cambio 2** [x] `tasks.md` T9 y T12 en `[x]`; commit `4ef9d3c F-038 T12: ...`. T10 (M1) y T11
  (M2) siguen `[ ]`: son MANUAL del humano, legítimo. C5 resuelto.
- **Cambio 3** [x] «Evidencias» con «workers: 1». C4 bis resuelto.
- La observación de la pasada 1 también está resuelta: `design.md` §9 y T11 esperan ya `max_rows=500000`.
- `.pyc` del script con DNI: ya no está en el worktree. **Sigue en el árbol principal**
  (`partes/services/partes-front/__pycache__/consulta_reshor_recursos.cpython-312.pyc`, ignorado por
  git) junto al `.py`, que se va con el merge. El líder lo borra tras el merge (no bloquea).
- C2, C3, C3 bis, C4 ter: sin cambios desde la pasada 1. El `[AVISO]` de features `blocked` es ajeno a F-038.
- **Cambios requeridos**: ninguno. Pendiente fuera de review: merge, despliegue sv2–sv5, M2 y M1.
