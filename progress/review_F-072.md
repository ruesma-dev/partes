Revisión incremental desde ffd6369 (pasada 2, principal) · delta `ffd6369..af0cac9` · 2026-11-23

# F-072 · Review principal (reviewer), pasada 2

**Veredicto: APPROVED** (pasada principal). El SHA aprobado es **af0cac9**: abre la campaña T28
(la capa e2e es N/A). Hay un **encargo para T28** (abajo): la pasada de evidencias lo comprueba.

**Pasada 1** (`b1fb495...ffd6369`, 2026-11-21): CHANGES_REQUESTED por tres puntos, hoy resueltos:
la categoría del capítulo en sv4, el desempate sin test y `current.md`.

**Nivel de rigor: `critico`**, declarado en `features.json`. Exige fase RED, cobertura ≥ 90 %,
mutación con cero supervivientes sin justificar y MANUAL con comando. El delta no toca
`rigor.local.json`. Lo aprobado en la pasada 1 hasta ffd6369 se da por bueno: el delta no
cambia firmas públicas ni mueve ficheros.

## Ejecución

- `ARNES_SIN_CACHE=1 bash harness/init.sh`: **ENTORNO LISTO**, exit 0. Raíz 2551 (48 skip),
  sv1 74, sv2 575 (1), sv3 2944 (2), sv4 4004, sv5 1800 (1). R10 corre sin skip. Puertas:
  TAMAÑO OK (impl 220/220), CARRIL N/A (critico), CAPA E2E N/A.
- Gemelo: md5 `62c13db…`, idéntico en sv2–sv5 (antes `2d57809…`: el cambio de D1).
- **Mutaciones a mano**, en una copia del scratchpad sin `.env`.
  - Se lanzan con `sys.executable -m pytest`. Antes, un control sin mutante, en verde.
  - Cada una se mata con un test de la propia feature.
  - **D2**, 6 de 6 muertas por `test_f072_conflictos.py`: `ctx.agrupada is not None` por `False`
    y por `True`, `==` → `!=` y sin comparar la partida, `con_partida=False`, y `_evaluar` sin
    pasar `p.por_partida`.
  - **D1**, 3 de 3 muertas por `test_f072_obras_agrupadas.py` (sv3): sin la guarda,
    `fullmatch` → `match` y sin `strip`.
  - **Cambio 1**: con `h.capitulo_cod` de vuelta, muere.
  - **Desempate de `IndicePostventa`** (195 tests F-072 de sv4): mueren 4 (el `ide` de las
    exactas, `<` → `>`, `_orden` sin código o sin longitud); sobreviven 4: ver el encargo.

## Delta revisado

- **Cambio 1** (013766e): `partida_capitulo=h.categoria`.
  - RED real en 20f91f6: `('CD.POSTVENTA', None) == ('CD', 'OTRO')`.
  - El test pone una hoja bajo `CD.POSTVENTA` y otra sin padre (`OTRO`), y comprueba ≤ 8 caracteres.
- **Cambio 2** (20f91f6): los 11 casos que pedí, contra `casar_postventa`.
  - Están en verde desde el principio, y es correcto: faltaba evidencia, no lógica.
  - Cubren las líneas 71, 80 y 90-92.
- **O3** (013766e): fuera `CatalogoEntradas.ajustes`. El import de `Ajustes` sigue en uso (`:97`).
- **Cambio 3** (2f4765e, líder): la línea 6 de `current.md` dice `in_review`, y la sección de
  F-072 lista T29–T31 con su comando y enlaza a `tasks.md` y a `impl_F-072.md`.
- **Enmienda D1 (c) / D2 (a)**, en este orden: spec 2319d70 (R8, R38, design §6 y T33, con fecha
  y cita «D1 c, D2 a»), RED 99fe8d5, código c3a8af8 e informe 1adb0d2.
- **D1, `casar_var`**: el segundo paso exige `_NUMERO.fullmatch(str(leido).strip())`.
  - Sale el `if numero is None` (el `fullmatch` ya garantiza un número). R10 y R11, en verde.
  - El test cubre `29.3`, `29A` y `29-B` → `None`; `" 29 "` → `29.1`; `0029` → `029`.
- **D2, `ReajustePipeline`**: `_Preparada.por_partida = ctx.agrupada is not None`.
  - Mismo criterio que el registro (`registro_pipeline.py:510`). `_choques` pide `con_partida=True`
    solo en una obra agrupada y compara `paride`; en una obra normal, como hoy (`[False]`).
  - La guarda (paso 2d) sigue delante: `escribe` exige la acción `escribir`.
- **Documentación**: el paso 2d dice «solo choca la misma partida» para registro, reajuste y
  franquicia, tanto en la semántica 24 de `docs/ARCHITECTURE.md` como en `azure-apps` §3.5.
  - Hasta D2 eso no era cierto para el reajuste; ahora lo es. Ninguno documenta el segundo paso
    de `casar_var`: no hay que tocar nada.
- **Informe del implementer** (220/220): conserva las trazas RED, «Evidencias», los MANUAL con su
  comando y (i)–(x). Las secciones condensadas no pierden nada necesario.

## Checkpoints

- **C1** [x] `init.sh` sin caché (arriba).
- **C2** [x] Una sola feature activa (`in_review`) y la rama es la correcta. `current.md`, al día.
- **C3** [x] En el delta no hay ficheros nuevos, prints ni TODOs; comentarios en español; el
  hexágono sigue intacto (D2 queda en `application/pipelines`).
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C3 ter** [x] La enmienda tiene fecha (2026-11-23) y la cita del humano en R8, R38, design y
  T33. `current.md` la registra.
- **C3 quater** [x] cd58cab ya está en `origin/main`. D1 y D2 no piden cambio
  en `partes.md`: el §3.5 ya nombraba el reajuste.
- **C4** [x] T29–T31 están en `current.md` con su comando. R8 y R38 enmendados tienen su test.
- **C4 bis**
  - [x] El nivel está declarado.
  - [x] RED real del cambio 1 y de T33: R8 (sv3, `1 failed`) y R38 (sv5, `-k d2a`, `1 failed,
    2 passed`). Cuadran con mis mutaciones del código anterior (1 fallo en cada caso).
  - [x] Cobertura `[OK]` 99,7 % (1070/1073). Las 3 sin cubrir son las que declara el informe:
    `obras_agrupadas.py:62` en sv2 y sv5, y la línea 1196 de sv3.
  - [x] «Evidencias»: sigue con los números del 2026-11-21, y T33 da los de sv3 y sv5.
  - **Pendiente, pasada de evidencias**: la mutación (totales, recálculo, tiempos, RM1–RM6 y
    supervivientes), RM7 y el encargo de abajo.
  - Capa e2e N/A: `CAPA E2E: N/A (ningún servicio declara el bloque e2e)`.
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5** [x] T33 en `[x]`, con sus commits `F-072 T33:`. Los de la review van como
  `F-072 review1:`: no son tareas. T28–T31 siguen pendientes a propósito. El árbol está limpio.

## Encargo para T28 (lo comprueba la pasada de evidencias)

`harness.mutacion` no genera estos mutantes: lo he comprobado con `generar_mutantes` sobre las
líneas 60-92. Por eso la campaña no los vería. Los dos primeros **no son equivalentes** y
sobreviven a los 195 tests F-072 de sv4
(`services/partes-front/application/services/catalogo_entradas.py`):

1. **`casar`** (`:87`), con los dos `get` intercambiados. Con `0578` y `0578B` activas, el gemelo
   da `0578` y el mutante, `0578B`.
   - Ningún caso tiene a la vez una exacta y una «con letras» activas: en `de_baja`, la exacta
     está de baja.
2. **`_orden` sin `h.ide`** (`:92`). Con `0578B` (ide 3) y `0578-B` (ide 2), en ese orden, el
   gemelo da el ide 2.
   - **Arreglo**: añadir `[(2,"0578",0),(3,"0578B",0)]` y `[(3,"0578B",0),(2,"0578-B",0)]`,
     los dos con código `0578`, a `test_f072_r25_el_indice_desempata_como_casar_postventa`.
   - Contra el código actual, el gemelo y el índice dan lo mismo en los dos (ide 2).
   - **Si la pasada de evidencias no los encuentra, es CHANGES_REQUESTED.**
3. **Equivalentes**, si la campaña los genera: `break` → `continue` (`:77`; los sufijos crecen
   anidados: si uno no es solo letras, los más largos tampoco); quitar `if not cod: continue`
   (`:70-71`; `casar` devuelve `None` con código vacío antes de mirar el índice); `<=` en `:73`
   y `:80` (dos hojas no comparten `ide`).

## Observaciones (sin bloqueo)

- **O5** El informe del implementer se quedó atrás en tres puntos: (ii) sigue diciendo «al pie
  de la letra» (hoy manda D1 (c)), cd58cab dice «sin push» y la tabla de la suite es del
  2026-11-21. Que lo refresque en T28.
- **O1**, **O2** y **O4**, como en la pasada 1: `open()` no resetea `addlineEntradaPartida`; el
  422 de «Añadir línea» en la vista `agr-` (mirarlo en M2); la línea 1196 de sv3 (pista).
- **O6** Con D1, un `29.` leído (con punto final) va a revisión. Es la letra de (c): si molesta,
  se verá en M2.

## Cobertura requisito → test (todos en verde)

| Req. | Test |
|---|---|
| R1–R3 | `test_f072_r1/r2_*` en los 4 `test_f072_settings.py`; `r3_*` en sv3, sv4 y sv5 |
| R4–R9, R41 | sv3 `test_f072_obras_agrupadas.py` (R8 con D1: `test_f072_r8_d1c_*`), más cada `*_copia.py` |
| R10, R11, R40 | raíz: `test_f072_equivalencia_porcentajes.py`, `…_gemelos.py`, `test_f072_documentacion.py` |
| R12, R13, R43 | sv2 `test_f072_marca_sv2.py` |
| R14–R19, R42 | sv3 `test_f072_entrada_agrupada.py`, `test_f072_pipeline.py` |
| R20–R22 | sv3 `test_f072_conciliacion.py` |
| R23–R35 | sv4 `test_f072_repositorio.py`, `test_f072_catalogo_entradas.py` (R25: `…_categoria_…`, `…_desempata_…`), `test_f072_endpoints.py`; R33 también en sv5 |
| R36–R39 | sv5 `test_f072_guarda.py`, `test_f072_conflictos.py` (R38 con D2: `test_f072_r38_d2a_*`), `test_f072_guarda_reajuste_franquicia.py` |

## Automejora (propuesta, no aplicada)

- La de la pasada 1 sigue en pie: una trampa C3 (4) sobre las longitudes `String(n)` del ORM gemelo.
- **Nueva, para `reviewer.md`, punto 4 de «Validación contra el nivel»**:
  - Cuando una feature reimplementa una regla del gemelo por rendimiento (aquí, un índice), la
    campaña no ve los cambios de precedencia entre dos búsquedas ni los de los campos de una
    clave de orden.
  - Propuesta: en `critico`, el reviewer aplica a mano, en una copia, el intercambio de
    precedencia y la retirada de cada campo del desempate, y exige que mueran.
