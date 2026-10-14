<!-- progress/review_F-045.md -->
Revisión completa (pasada 1) · `git diff dev...HEAD` hasta `7144932`

# F-045 · Review

- **Veredicto: CHANGES_REQUESTED**
- **Rigor:** `critico` (declarado). Exige C1–C5, C3 bis, RED, cobertura ≥ 80 %,
  mutación con 0 supervivientes sin resolver, RM1–RM6 y MANUAL.

## Ejecuciones propias (worktree `partes-wt-f045`, 2026-10-14)

- `bash harness/init.sh` → exit 0, **ENTORNO LISTO**. Raíz: 487 passed, 3 skipped.
  COBERTURA [OK] 100 % (162/162). TAMAÑO [OK].
- init.sh sirvió sv3 de caché: relancé la suite a mano, **1387 passed**.
- Propiedad propia (scratchpad), **16.172 días aleatorios que cuadran, 0 fallos**
  (pasos 0,5/0,25/0,01; J 0–9; con fijas y extras): ordinarias = J exacto, norma +
  extra = horas, cuotas múltiplo del paso, fijas intactas, permutar da lo mismo.
- Árbol limpio al terminar.

## Puntos pedidos por el coordinador

1. **Tests modificados:** solo `test_f003_r15` (×3), `test_f015_r20` (×3), `test_f037_r9`
   y `dobles.py` (design §4, T4). Solo el valor esperado y un comentario; recalculé las
   7 filas de antes → después y coinciden. `f015_r32` y `f037_dos_pasadas` intactos.
2. **Ejemplos del humano, exactos** (en pasos enteros): 10 + 4 ⇒ 5,5 + 4,5 / 2,5 + 1,5;
   5 + 4 ⇒ 4,5 + 0,5 / 3,5 + 0,5; viernes candef 9 (J 6) ⇒ 3,5 + 1,5 / 2,5 + 1,5;
   jueves (J 9) sin split; viernes festivo ⇒ jueves con J 6 (R33).
3. **Redondeo, totales y suma por obra:** correctos. El desempate es determinista, pero
   la escala que lo sostiene no tiene test (cambio requerido 1).
4. **Congeladas y R25:** sin ajuste y con el literal de R23; R25 avisa y cuenta, sin
   nombres ni DNIs. Falla el vínculo extra↔base de la medición (cambio 2).
5. **Papelera:** filtrada en memoria. Base borrada con su `extra_auto` activa: si no
   está congelada, `revert_extras_auto` la borra y no se recrea; si lo está, queda
   fija, como extra y fuera de `J'`, sin afectar a las demás obras.
6. **Intactos** (diff vacío): sv1, sv2, sv4, sv5, `infra/`, `CLAUDE.md`, `orm_models.py`,
   `pareja_extra.py` y los dos `jornada_resolver.py`. También `esta_congelado`,
   `ESTADOS_CONGELADOS` y `_congelado`. La lista cerrada no crece.
7. **Mutación:** un «equivalente» es falso, y quitar una guarda cambió el
   comportamiento (C4 bis).
8. **azure-apps:** commit local `b4df33e`, solo `partes.md` (+4 −1, §3.3), sin push.

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros base.

**C2** [x] una sola `in_progress` · [x] rama `feature/F-045-…` · [x] `current.md`
(F-045 más secciones con MANUAL pendientes, como en F-043) · [x] `history.md`.

**C3** [x] hexagonal (`reparto_ponderado.py` puro: solo `collections.abc` y
`dataclasses`) · [x] ruta en la primera línea · [x] sin prints, secretos ni
dependencias · [x] trampas (1)–(3) intactas, sin esquema.

**C3 bis** [N/A] cabecera: no hay documento nuevo · [x] sin PDF ni ofimática
(`--diff-filter=A`: vacío) · [x] barrido propio (35 líneas de `docs/` + azure-apps):
correo, IPv4, GUID, `password|secret|token|apikey|AccountKey|SharedAccess|sig=|Bearer|
-----BEGIN`, base64 ≥ 32, DNI `\d{8}[A-Z]` → **0 coincidencias** · [N/A] nada redactado.

**C4** [x] trazabilidad completa (tabla abajo), en verde · [x] sin red ni BBDD ·
[ ] **MANUAL con comando exacto:** el despliegue de `current.md` está corrupto (cambio 3).

**C4 bis**
- [x] `critico` declarado · [x] cobertura 100 % · [x] RED: trazas reales de T1, T2, T3
  y T5; R33 sin RED (añadido después a petición del humano, y declarado).
- [x] Recalculé el alcance y los mutantes: **399 líneas y 82 mutantes**, igual que el
  informe, en `cc3f910` y en HEAD. Los 9 supervivientes existen con el mismo operador y
  el mismo texto.
- [x] Total de 383,4 s, más de 60 s: **campaña no reejecutada** (6,4 min según el
  informe). Me quedo en el recálculo puro, RM1–RM6 y RM4.
- [x] Coste por mutante: 383,4 × 6 ÷ 82 = 28 s. Sin «NO VÁLIDA»; base rota = 0.
- [x] RM1: desde `cc3f910` solo cambian tests, `progress/` y spec (nada del alcance) ·
  [x] RM2: 4,7 s × 6 = 28 s frente a base 34–36 s; 82 × 4,7 cuadra con el total.
- [x] RM3: recorrí los 73 muertos y ninguno es equivalente. El de `:209` (contador 0→1
  en `__init__`) se observa fuera de `conciliar_todos`: muerte legítima.
- [x] RM4 (copia `git archive HEAD`): #2 y #5 sobreviven (1387 passed); los de control
  mueren: `+= 1 → += 2` (97 failed), `n_lineas >= 3` (2 failed).
- [ ] **RM5:** ningún equivalente trae demostración ejecutable, solo prosa. La muestra
  que elegí, **#2 `_RESOLUCION = 10001`, NO es equivalente** (cambio 1).
- [ ] **RM6:** se quitó la guarda `and tipo_linea == EXTRA` con un invariante que es
  falso en el origen (cambio 2).
- [N/A] Campaña manual: la automática dio 82 mutantes.
- [ ] Hay un superviviente mal analizado, así que no hay 0 sin resolver; la aceptación
  del humano sigue pendiente.
- [x] «Evidencias» completas, con los 6 workers.

**C4 ter** [N/A] el repo no tiene `rutas_sensibles.json`. **C5** [x] T1–T13 `[x]`, con 13 commits `F-045 T…` · [x] sin temporales ·
[x] `features.json` coherente.

## Cobertura requisito → test (`services/partes-persistencia/tests/test_f045_*`)

| Req. | Tests |
|---|---|
| R1–R6 | `r1_*` (6), `r2_*` (4 + permutaciones), `r3_*` (8), `r4_*`, `r5_*` (6), `r6_*` (AST) |
| R7–R19 | `r7_*` (3), `r8_*` (2), `r9`, `r10_r17_*`, `r11_*` (3), `r12`–`r16`, `r18`, `r19_*` (2) |
| R20–R24 | `r20_*` (3), `r21_*` (4), `r22_*` (9), `r23_*` (5), `r24_*` (2) |
| R25–R30 | `r25_*` (18), `r26_*` (2), `r27_*` (3), `r28_*` (3), `r29_*` (3), `r30_*` (3) |
| R31 · R32 · R33 | diff vacío (punto 6) · lectura de los docs y de `b4df33e` · `r33_*` (3) |

## Cambios requeridos

1. **Superviviente #2 (`reparto_ponderado.py:24`, `10_000 → 10001`): NO es
   equivalente.** El redondeo bancario de `round(peso × escala)` desplaza los pesos de
   forma desigual (1,5 → 15002; 2,5 → 25002) y le da la vuelta al desempate de R2.
   `repartir(2.0, [A 1,5 llegada 1, B 2,5 llegada 2], 0.5)`: original {A 0,5, B 1,5},
   mutante {A 1,0, B 1,0}. Día real: congelada 6 h + A 1,5 + B 2,5, J 8 ⇒ original
   A 0,5 + 1 y B 1,5 + 1; mutante A 1 + 0,5 y B 1 + 1,5.

   Hay que añadir ese caso como test (en `test_f045_reparto_puro.py` y a nivel de
   `repartir_dia`), corregir el análisis #2 de `progress/mutacion_F-045.md` y revisar
   con el mismo rigor los otros 8 equivalentes.
2. **RM6, guarda quitada en `recurso_conciliador.py` (`_lineas_dia`, `base_id`).**
   - Por qué falla: sv4 cambia `tipo_hora` de cualquier línea editable
     (`parte_repository.py:2185` y `:2222`). Una `extra_auto` reclasificada como normal
     se congela al aprobar y `revert_extras_auto` ya no la borra. Entonces
     `_lineas_dia` le asigna como base su propio id y `diferencias_ideal` la saca del
     ideal.
   - Lo medí con base 8 (`horas_orig` 10) más esa línea de 2 h, ambas congeladas, y la
     0704 con 4 h: sin la guarda, `(1, 8→5,5), (2, 2→0)`; con ella,
     `(1, 8→5,0), (2, 2→1,0)`. No era redundante.
   - Qué hacer: reponer la guarda (o tratar el caso de forma explícita) con un test, y
     anotarlo en el informe de mutación.
3. **`progress/current.md`.**
   - (a) La línea 24 dice `.<CR>edeploy_partes.ps1 -Solo sv3`: el `\r` se escribió como
     un byte de retorno de carro. Hay que restaurar el texto literal
     `.\redeploy_partes.ps1 -Solo sv3`.
   - (b) El commit `7144932` dejó el fichero en CRLF, cuando `dev` es LF: son 4.479
     líneas de ruido (`-w` deja 55). Hay que volver a LF.
4. **Relanzar la mutación** en la HEAD que salga de los cambios 1 y 2: el 2 toca el
   alcance, y así entran también los tests de R33. Cada equivalente que quede debe
   traer una demostración ejecutable (RM5): un fragmento o un test que enseñe que el
   original y el mutante coinciden en el dominio real de horas. Después se actualizan
   «Evidencias» y la nota de pendiente de aceptación del humano.

## Observaciones (no bloquean)

- Aceptar los equivalentes que queden le toca al humano. Con un J de más de dos
  decimales, el paso 0,01 deja las ordinarias a ±0,005 de J (hoy ningún candef lo da).

**Automejora (propuesta, no aplicada)** para `reviewer.md` y C4 bis: en un mutante de
constante de escala o de redondeo, exigir un caso con empate de restos y pesos de
fracciones distintas. Destapa el redondeo no uniforme.
