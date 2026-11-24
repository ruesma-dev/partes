<!-- progress/review_F-083.md -->
Revisión completa (pasada 1) · principal · `git diff 5b7ddce...7402199` (base `dev` 5b7ddce)

# Review F-083 · Una racha de incidencia solo lleva CIZ en su último día

**Veredicto: APPROVED** (pasada principal). **SHA aprobado: 7402199.** Mutación (T6), RM1–RM7 y
supervivientes: «pendiente: pasada de evidencias». MANUAL M1–M4: tras el merge (T7).

**Nivel de rigor: `critico`** (declarado; disparador 2: sv5 escribe en `hmores` de Sigrid de
producción). Exige C1–C5, C3 bis, C3 quater, C4 bis con fase RED, cobertura ≥ 90 % (del nivel),
mutación exigida (uno por línea, 60 % acotado a [100, 300]) con cero supervivientes sin
justificación aceptada por el humano, RM1–RM7 y MANUAL con comando exacto. El diff no toca
`harness/rigor.local.json`.

## Lo que ejecuté yo

- `ARNES_SIN_CACHE=1 bash harness/init.sh`: **exit 0, `ENTORNO LISTO`**, ninguna suite por caché.
  - Suites: raíz 2549 passed, 50 skipped (642 s); sv1 74; sv2 579; sv3 2954; **sv4 4017 passed,
    1 skipped (506 s)**; **sv5 1887 passed, 1 skipped (13 s)**.
  - `PUERTA COBERTURA: 100.0% de 31 líneas cambiadas (31/31, umbral 90% del nivel critico)`.
  - `PUERTA TAMAÑO` OK (144/150, 249/250, 173/220). `PUERTA CARRIL` N/A (crítico).
    `CAPA E2E: N/A (ningún servicio declara el bloque e2e)`.
- Copia de sv5 en mi scratchpad (`git archive HEAD`), nunca en el árbol de trabajo:
  - **RED sobre el código de `dev`** (`racha_ciz.py` y `registro_pipeline.py` restaurados):
    - el fichero de F-083 da `ImportError: cannot import name 'MOTIVO_POSTERIOR_SIN_CIZ'`;
    - su sección de pipeline, aislada, da **6 failed, 10 passed**. Caen R13, R15, R16, R17, R10
      y R11. R13 cae con `Left contains one more item: {'registro_id': 2, ... 'hora_codigo':
      'CIZ'}`: es el bug 0730 reproducido;
    - pasan R14, R12 (×2), los dos «sin WARNING» y los 4 de R18 (caracterización).
  - **8 mutaciones a mano** sobre HEAD, contra F-083 + F-060 + F-062 (249 tests; control sin
    mutar: exit 0, con `sys.executable`). Todas mueren; entre paréntesis, los fallos:
    - orden CIZ/otra en `decidir_fin` (20) · `>` por `>=` en `ultima_posterior` (5);
    - `sin_ciz=False` (15) · sin el WARNING del `fin` (1) · WARNING del `inicio` con cualquier
      motivo (2);
    - sin la rama nueva de `decidir_mismo_dia` (10) · `max` por `min` (4);
    - `es_linea_de_la_racha` sin el filtro de `can` (12).

## Los cuatro puntos del líder

1. **Desviación de R22: aceptada.** Es la consecuencia obligada de la regla aprobada.
   - `[fila1]` es un `inicio` con `ciz_mismo_dia` y tramo `[5]`, con un CIV del mismo recurso a
     0 h en D+1: literalmente R8/R15. Su aserción antigua (se escribe el hermano) los
     contradice. Es el gemelo de pipeline del subcaso puro que R22 sí nombra.
   - El cambio es mínimo: las otras tres filas (otro recurso, `can` 4, día anterior) quedan con
     una aserción equivalente a la original.
   - En F-060 solo cambian `ajena1` (CIV) y `ajena2` (sin código); otro recurso, `can` 8 y
     −0,5 siguen en `crear`. En el puro de F-062 solo cambia la fila CIV.
   - Ningún otro test cambió (`git diff --name-only`). sv4, sv1–sv3, `tests/` raíz e `infra/`
     tienen 0 líneas de diff.
2. **R18: la evidencia basta.** Para un «idéntico a la base», lo que toca es una caracterización,
   y esta se sostiene por cuatro lados:
   - pasa sobre `dev` (reproducido; 011bc2a y `dev` solo difieren en sv5 en un test de F-072)
     y sobre HEAD;
   - **no es hueca**: con `_mover_ciz` forzado a `True`, los 4 tests caen;
   - estructuralmente, `decidir_fin` y `decidir_mismo_dia` solo se llaman detrás de
     `if not self._mover_ciz(): return`;
   - las aserciones comparan las sentencias enteras, y `racha_leidas` y `estados_leidos` vacíos.
3. **Sin lecturas ni sentencias nuevas.**
   - `infrastructure/`, `config/` y `domain/` de sv5 tienen 0 líneas de diff.
   - R12 compara las listas exactas de lecturas y pasa también sobre la base.
   - F-083 solo convierte `crear`/`mover`/hermano en omisiones.
   - sv4 no cambia.
   - `azure-apps` 5078dc0 solo toca `partes.md` (3c y 3d) y coincide con design §11. `main` va
     1 commit por delante de `origin/main`: **sin push**.
4. **RED, cobertura y tamaño**: en verde, arriba. Las trazas RED del informe son reales y mi
   reproducción coincide. Mi sección de pipeline ya incluye R12 y R18: de ahí 10 passed y no 6.

## Checkpoints

- **C1** [x] `init.sh` sin caché, exit 0 · [x] ficheros del arnés presentes.
- **C2** [x] una sola activa (F-083) · [x] prioridad 1 · [x] rama `feature/F-083-…` ·
  [x] `current.md`, según la práctica del repositorio (O2) · [x] `history.md`: no aplica hasta
  `done`.
- **C3** [x] hexagonal: la regla pura en `application/services`, el log en el pipeline ·
  [x] primera línea con la ruta · [x] sin `print`, TODOs, secretos ni dependencias ·
  [x] `reside`, incidencias con `can` 0, sin esquema.
  - Ni `racha_ciz.py` ni `racha_incidencia.py` están en la lista cerrada de gemelos.
- **C3 bis** [x]: se modifican 3 líneas de `docs/referencia/partes-proyecto.md`, sin documento
  nuevo.
  - Barrido mío sobre todo el diff añadido: correo, IPv4, GUID,
    `password|secret|token|apikey|AccountKey|SharedAccessSignature|x-functions-key`, DNI/NIE.
    Solo sale `$KEY`, una variable sin valor de design §8. `git log --diff-filter=A` no da
    ningún `.pdf` ni ofimática.
- **C3 ter** [x] La petición del humano va literal y con fecha, D1–D8 constan como «humano
  2026-11-23», y el caso 0730 y M0 van atribuidos al líder.
- **C3 quater** [x] solo `partes.md` · [x] commit aparte 5078dc0, citado en `impl` · [x] sin
  push · [x] coincide con la Frontera.
- **C4** [x] R1–R22 con test trazable y en verde · [x] sin red ni BBDD · [x] dobles: F-083 no
  añade métodos, y `lineas_de_racha`, `estados_de_partes` y `escribir` existen en
  `SigridWriteClient` · [x] MANUAL: M0 hecha y anotada.
  - M1–M4 tienen comando exacto en design §8, al que remite T7 (O3).
- **C4 bis** [x] rigor declarado · [x] fase RED con trazas reales · [x] cobertura [OK] 100 % ·
  [x] «Evidencias» con los cuatro números y la capa e2e · [x] capa e2e N/A (`CAPA E2E: N/A`,
  sv4 sin tocar).
  - **Pendiente: pasada de evidencias**: totales de mutación, recálculo, RM1–RM7,
    supervivientes y workers.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] un commit `F-083 Tn:` por tarea (9a73523, c43d3be, 6fc7ccc, f170bc2, 10681ce,
  914b9e2) · T6 y T7 en `[ ]` **por el flujo** (la campaña va tras este APPROVED y la MANUAL
  tras el merge) · [x] `git status` limpio · [x] `in_review` (O1).

## Cobertura requisito → test (`tests/test_f083_ciz_solo_fin_de_racha.py`, 78 tests)

| R | Test(s) (prefijo `test_f083_`) |
|---|---|
| R1–R4 | `puro_r1_*` (2), `puro_r2_*` (CIV/None/HL01 + la última), `puro_r3_*` (×4 + duplicados), `puro_r4_*` (×3) |
| R5–R7 | `puro_r5_*` (5 descartes en `fin` y en `inicio`, marca), `puro_r6_*` + F-060 R15–R19, `puro_r7_*` |
| R8–R9 | `puro_r8_*` (×2, enlazada o cerrada), `puro_r9_orden` (×8, también con `iter`) |
| R10–R12 | `pipeline_r10_*` (con y sin WARNING), `pipeline_r11_*` (×3), `pipeline_r12_*` (`fin` e `inicio`) |
| R13–R17 | `pipeline_r13_caso_0730`, `_r14_regresion…`, `_r15_inicio_desordenado…`, `_r16_…`, `_r17_…` |
| R18 | `pipeline_r18_apagado_caso_0730_como_la_base` (×2), `…_inicio_como_la_base` (×2) |
| R19–R20 | `puro_r19_motivo_exacto`, `puro_r19_prefijo_tildes_y_largo`, `puro_r20_*` (×2) |
| R21 | sv4 sin tocar (4017 passed) · R22: enmiendas de F-060 y F-062 (punto 1) |

## Encargo para la campaña (T6)

1. **Superviviente probable, NO equivalente**: quitar `candidatas = list(candidatas)` de
   `decidir_fin`.
   - Lo probé: la suite de sv5 sigue igual (mismo único fallo de entorno que el control).
   - La firma promete `Iterable`, y antes de F-083 un iterador funcionaba.
   - Se mata con `decidir_fin(…, iter([CIZ anterior, CIV posterior]))` esperando
     `intermedio` + `sin_ciz`, como hace `puro_r9_orden` con `decidir_mismo_dia`.
2. **RM7**: a mi juicio, N/A justificable. El orden lectura → decisión → escritura viene de
   F-060 y no se mueve. R3 es un orden interno de una función pura, y la mutación «orden» lo caza
   con 20 fallos. Lo decide el reviewer de evidencias.

## Observaciones (no bloquean; para el líder)

- **O1** `features.json` (`spec`) y `BACKLOG.md` dicen «D1–D8 por decidir»: ya están decididas.
- **O2** La cabecera de `current.md` dice `in_progress`; la feature está en `in_review`.
- **O3** Antes de T7, copiar a `current.md` los comandos de M1–M4 (design §8), como en F-062.
- **O4** Tras desplegar sv5, quitar «sin desplegar» de `azure-apps/partes.md`. Hay líneas de
  más de 100 caracteres en `ARCHITECTURE.md` y `partes.md` (solo estética).
- **O5** Desplegar sv5 activa F-083 (`MOVER_CIZ` encendido, D7): M1–M3 van antes.

## Automejora (propuesta, no aplicada)

`spec-author.md` / `specs/SPECS.md`: los tests anteriores que una spec manda enmendar (tipo
R22) se sacan **ejecutando** la suite contra un prototipo de la regla, o buscando también los
gemelos de pipeline, no leyendo. F-083 nombró dos y eran tres.
