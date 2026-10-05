<!-- progress/review_F-030.md -->
Revisión completa (pasada 1) · `git diff dev...HEAD` (merge-base `28ea4ad`), HEAD `a4a308c`

# F-030 · Review

- **Veredicto: CHANGES_REQUESTED.** Un solo cambio: falta un test (§Cambios).
- **Nivel de rigor:** `critico` (declarado): fase RED, cobertura ≥ 80 %,
  mutación con 0 supervivientes y verificaciones MANUAL con comando.

## Lo que se verificó (resultado real)

- `bash harness/init.sh`: **ENTORNO LISTO** (raíz `445 passed, 1 skipped`,
  cobertura `100.0% (59/59)`, tamaño OK). Suites **sin caché**
  (`-p no:cacheprovider`): sv3 `754 passed`, sv4 `1657 passed`, sv5 `362 passed`.
- **(1) Decide igual: diferencial dev vs HEAD** en copias `git archive` del
  scratchpad, con el pipeline real (`_match` + `review_required`). 20.000
  partes sintéticos, 59.870 líneas: fichas con y sin DNI, duplicadas, de baja
  o de otra empresa; recursos `MO/`/`MQ/`/`mo/`/sin código, `cif` vacío o con
  guiones, `conide` a ficha, 0 o huérfano; obras gemelas, membrete, alias;
  DNIs con y sin cero, NIE, CIF, «-»; nombres en los dos órdenes y con coma.
  - **dev con el DNI ya canónico == HEAD sin fichas de recurso: 0 diferencias
    en 20.000 partes** (obra, empresa, review y las 9 columnas por línea). Solo
    cambia lo pedido: el DNI canónico y las fichas de recurso.
  - Con fichas de recurso, cada cambio va a `recurso_*` o a `nombre_ambiguo`
    por empate con una de ellas. Un **oráculo independiente** (reglas escritas
    desde la spec) coincide en las 59.870 líneas: 2.044 `recurso_dni`, 1.315
    `recurso_nombre`, 637 `nombre_ambiguo`, 0 discrepancias. En todo casado
    por recurso: `ide`/`codigo` None, `dni` = `cif` tal cual, `reside` = recurso.
- **(2) Lista cerrada:** diff vacío en `seleccion_sigrid.py`,
  `coherencia_recurso.py`, los dos `text_match.py` (idénticos),
  `orm_models.py`, `jornada_resolver.py`, `recurso_conciliador.py`,
  `empleado_matcher.py`, `sigrid_lookup_client.py`, sv1, sv2, plantillas y
  `app.js`. sv5 solo gana un test. Se reutilizan `elegir_ficha`,
  `fichas_candidatas` y `match_nombre`: no hay lógica copiada.
  `METODOS_RECURSO` en sv3 y sv4 es el contrato de valores de la columna
  (design §6.4) y lo fijan a literal tests de los dos servicios.
- **(3)** Los empates recurso↔empleado y recurso↔recurso dan `nombre_ambiguo`;
  «APELLIDOS, NOMBRE» casa en cualquier orden (R10, R11 y el diferencial).
  **(4)** DNI con y sin cero, con guion y en minúscula (R1–R3 y el diferencial).
- **(5)** sv5 sin código; R17 y R21 (`caaide` 0, sin aviso) en verde.
  **(6)** sv4 solo toca `parte_repository.py`. La cola y «Confirmar» de
  `/conciliacion` (`backfill_empleado`) excluyen al casado por recurso con el
  NULL bien tratado (`or_(IS NULL, NOT IN)`): no pueden soltarle el recurso.
  Reasignar a mano sí lo suelta (R20, como hoy).
- **(7)** DNIs de test secuenciales/sintéticos; nombres inventados. El
  barrido del diff (`password|secret|key=|AccountKey|Server=|tenant|GUID`)
  solo encuentra `clave-de-test`. Sin `print`. Docs y `azure-apps` (`1c7238c`,
  solo `partes.md`, árbol limpio) coherentes con la spec.
- **Roturas deliberadas en copias del scratchpad: 17. Las cazan los tests
  todas menos una** (§Cambios): regex de DNI corto, filtro `conide`, prefijo
  `MO` sin barra, R7 abierto a `solo_baja`, nombre que nunca convierte a
  recurso, R12 con `ide`, DNI en el log de R6, recursos solo sin fichas, cola
  `NOT IN` sin `IS NULL`, cola sin `recurso_nombre`, cada uno de los 4
  `matched=` sin `esta_casado`, y `backfill` y cola sin el filtro.

## Mutación (C4 bis, RM1–RM6)

- Recalculado con `harness.alcance` + `generar_mutantes`: **8 ficheros, 199
  líneas, 18 mutantes** = informe. Sin «campaña no válida»; 0 sin veredicto.
- **RM1:** SHA medido `551a1d8`. Hasta HEAD solo cambian `progress/` y `tasks.md`.
- **RM2:** 957,2 s × 6 workers / 18 = 319 s por mutante: no baja de la base
  de sv4 (312 s) y supera con mucho la de sv3 (9–19 s). Y `18 × 53,2 ≈ 957`. Coherente.
- Como el tiempo pasa de 60 s, **no se reejecutó la campaña completa**. En su
  lugar, **RM4 en la copia del scratchpad**: los 18 mutantes, uno a uno, con la
  suite entera de su servicio y `-x`. **18/18 muertos** por aserciones reales:
  sv3 con 16 fallos distintos; sv4 con `1 failed, 1638/1636 passed`.
  Una primera copia fuera de `services/` daba «1 failed» con cualquier
  mutante: los tests gemelos leen `../partes-front`. Se descartó y se repitió
  sobre la copia completa, con línea base `754 passed`.
- **RM3:** ningún mutante es equivalente. **RM5:** N/A, ni supervivientes ni
  equivalentes. **RM6:** no se quitó ninguna guarda. `conide in ides_ficha`
  sin guarda de None es correcto: `fetch_empleados` descarta las filas sin
  `ide` (`sigrid_api_client.py:222-224`).

## Checkpoints

- C1 [x] init.sh en verde · [x] ficheros del arnés. C2 [x] una sola `in_progress` · [x] rama de la feature · [x] `current.md` con
  F-030 arriba (debajo, MANUAL pendientes de features desplegadas, igual que en
  F-028 y F-029) · [x] las `done` están en history.
- C3 [x] hexagonal (`fichas_de_recurso` pura en application; SQL solo en
  infrastructure) · [x] cabeceras con ruta · [x] sin prints, TODOs, secretos ni
  dependencias nuevas · [x] trampas: empleado≠recurso (la línea se guarda en el
  recurso, R14); incidencias intactas; `orm_models.py` sin cambios.
- C3 bis N/A: `partes-proyecto.md` es documentación propia; no entra ningún
  documento de fuera (ni PDF ni ofimática).
- C4 [x] R1–R22 con `test_f030_rN_*` en verde · [x] sin red ni BBDD (Sigrid
  en memoria, `MockTransport`; sv4 en SQLite) · [x] M1–M4 en `current.md`.
- C4 bis [x] rigor · [x] RED pegada (R1–R5, R9–R13, R18, R19) · [x] cobertura
  · [x] mutación recalculada · [x] muertos comprobados (RM4) · [x] tiempos ·
  [x] informe válido · [x] RM1 · [x] RM2 · [x] RM5 (N/A justificado) · [x]
  RM6 · N/A campaña manual (hubo automática) · [x] 0 supervivientes · [x]
  «Evidencias» con workers · **[ ] tests de verdad: una rotura del cableado del
  proveedor pasa las 754 pruebas de sv3** (§Cambios 1).

## Cobertura requisito → test

| Req. | Tests (`services/<svc>/tests/…`) |
|---|---|
| R1–R3 | `test_f030_dni_canonico.py`: `r1_*`, `r2_*`, `r3_*` |
| R4–R13 | `test_f030_casado_recurso.py`: `r4_lectura_*`, `r4_fichas_de_recurso_*`, `r5_*`…`r13_*` |
| R14–R15 | `test_f030_conciliador_sin_ficha.py`: `r14_*` (5), `r15_*` (2) |
| R16 | `tests/test_f023_de_alta_gemelos.py` sin tocar + diff vacío |
| R17, R21 | `partes-transfer/…/test_f030_coherencia_sin_ficha.py`: `r17_*` (3), `r21_*` (2) |
| R18–R20 | `partes-front/…/test_f030_portal_recurso.py`: `r18_*` (6), `r19_*` (4), `r20_*` (2) |
| R22 | lectura: ARCHITECTURE §2 y §12, `partes-proyecto.md` §4.6 y §7, `azure-apps/partes.md` |

## Cambios requeridos

1. **Test del cableado de `Matchers.recursos`** (en
   `services/partes-persistencia/tests/test_f030_casado_recurso.py`, familia
   `proveedor`).
   - **Qué pasa hoy:** en `sigrid_matcher_provider.py:133`, cambiar
     `fichas_de_recurso(empleados, recursos)` por
     `fichas_de_recurso([], recursos)` deja **754/754 en verde**.
   - **Qué rompería:** en el diferencial, esa rotura pasa a `nombre_ambiguo`
     **1.255 de unos 6.000 casados por nombre (21 %)**. El recurso enlazado a
     una ficha competiría con su propia ficha (misma persona: `suyas > 1`). Y
     en Sigrid es el caso normal: los `MO/` con ficha llevan `res.cif` (design
     §1). La rotura mandaría a revisión casi todo casado por nombre de la
     empresa 1, justo lo que el humano pide que no cambie.
   - **Por qué no se ve:** los fixtures del proveedor (`REC_PG`, `REC_V`)
     tienen `cif=None`.
   - **Qué añadir:** un test que cargue por el `SigridMatcherProvider` real una
     ficha con su recurso `MO/` (`cif` = su DNI, `conide` = la ficha) y otro
     `MO/` con `cif` = el DNI de una ficha y `conide` None. Debe afirmar
     (a) que ninguno de los dos sale en
     `matchers.recursos.fichas_candidatas(None, HOY)` y (b) que ese empleado,
     leído solo por nombre, sigue casando `nombre` con su ficha.
   - **Cómo se da por bueno:** con la rotura de arriba, el test nuevo falla; la
     traza va en `impl_F-030.md`.

Producción correcta (0 discrepancias). Pasada 2: solo el delta desde `a4a308c`.

**Observaciones (no bloquean).** El DNI canónico alimenta también los
discriminantes de obra (F-023 R11): cambian 74 de 20.000 partes, como prevén
design §5 y DA7. `azure-apps/partes.md` dice «umbral 0.55» (anterior a F-030).

**Automejora (propuesta, no aplicada):** en `reviewer.md`, para `critico`,
**roturas de cableado** (`[]`/`None` por el argumento real donde se montan los
objetos). El mutador no muta argumentos; fue la única rotura superviviente.
