Revisión completa (pasada 1, principal) · diff `b1fb495...ffd6369` · 2026-11-21

# F-072 · Review principal (reviewer)

**Veredicto: CHANGES_REQUESTED**: dos cambios pequeños en sv4 y uno de papeleo del líder. La
guarda de sv5, el gemelo, la equivalencia con porcentajes y el apagado están bien. Falla un
dato que sv4 escribe en la base `partes`, y falta una evidencia.

**Nivel de rigor: `critico`**, declarado en `features.json` (sv5 escribe en `ruesma`). Exige
fase RED, cobertura ≥ 90 %, mutación del nivel con cero supervivientes sin justificar y MANUAL
con comando y resultado. El diff no toca `rigor.local.json`.

## Ejecución

- `ARNES_SIN_CACHE=1 bash harness/init.sh`: **ENTORNO LISTO**, exit 0, sin caché. Raíz 2551/48
  skip; sv1 74; sv2 574/1; sv3 2943/2; sv4 3991; sv5 1796/1. Cobertura 99,3 %. R10 corre sin skip.
- Gemelo: md5 `2d57809…` idéntico en sv2–sv5.
- En porcentajes (`0cd2085`), `universo_postventa.py`, `universo_var.py` y
  `partida_resolver.py` no cambian desde `5381243`, el commit que leyó la spec.
- RM7 adelantado, en una copia del scratchpad: si la guarda (paso 2d) baja por debajo de
  `reglas.decidir`, cae `test_f072_guarda.py::…[sin-marca]`. El control sin mutante da 44 passed.

## Checkpoints

- **C1** [x] `init.sh` sin caché (arriba); los ficheros del arnés están.
- **C2** [x] Una sola feature activa (`in_review`), rama correcta, toda `done` con historia.
  Hay commits de papeleo ajenos en la rama: ae705ad (alta de F-079) y b91911f (M3 de F-077).
  `current.md`: ver el cambio 3.
- **C3** [x] Hexagonal (`EntradaPartida` y `PartidaHoja`, dominio puro; gemelo solo stdlib); los
  30 ficheros nuevos abren con su ruta; sin prints (salvo la salida del subproceso de R10), TODOs
  ni dependencias nuevas; las tres trampas ilesas (`test_f072_orm_sin_columna_nueva`).
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C3 ter** [x] DA1–DA13 con «humano 2026-11-21 «ok»». La enmienda (b), con fecha y cita
  («la b»). Las interpretaciones, aparte y etiquetadas.
- **C3 quater** [x] `azure-apps` cd58cab: solo `partes.md`, commit aparte, sin push (`main` ahead
  3, con dos ajenos), SHA en el informe; el contenido casa con design §12.
- **C4** [ ] Los 43 requisitos tienen su `test_f072_rN_*` en verde, sin red ni BBDD real.
  - Dobles cruzados a mano con su clase, misma firma: `ClienteF072.partidas_de_obra` y
    `lineas_existentes(con_partida)`, `LookupF072`, `RepoF072`, y `Obras` y `Sigrid` de sv4.
  - **[ ]** Las MANUAL T29–T31 no están en `current.md` con su comando: cambio 3.
- **C4 bis**
  - [x] Nivel declarado.
  - [x] RED con trazas reales en T1, T4, T6, T8, T10, T12, T14, (b), T16, T18, T20, T22 y T26.
    T2 vale con la traza de T1: es su implementación.
  - [x] Cobertura `[OK]` 99,3 % (1065/1072).
  - [x] «Evidencias» con los cuatro números.
  - **Pendiente, pasada de evidencias**: la mutación (totales, recálculo, tiempos, RM1–RM6 y
    supervivientes) y RM7 completo.
  - Capa e2e N/A: `CAPA E2E: N/A (ningún servicio declara el bloque e2e)`.
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`. El prompt de sv2 lo cubren R12 y R43.
- **C5** [x] T1–T27 y T32 en `[x]` con su commit `F-072 Tn:` (T25 y T27, dentro de T32 y T24).
  T28 (campaña) y T29–T31 (humano), pendientes a propósito. Árbol limpio, `features.json` al día.

## Puntos de especial atención (verificados)

- **Sin guarda no se escribe en una obra agrupada.** El paso 2d de `preparar` sirve al registro,
  al preflight, al reajuste (extras nuevas) y a la franquicia. Toda inserción sale de una acción
  `escribir`, y `franquicia.veredicto` la pide también para actualizar. La obra agrupada sale del
  código que lee sv5 (`obra_por_ide`), no del que manda sv4. Lectura fallida ⇒ nada (R37).
- **Equivalencia**: la tabla F-025/F-039 y el subproceso contra porcentajes. El desempate entre
  exactas está documentado.
- **Gemelo**: byte-idéntico, con guardián, `depende_de` y entrada en la lista cerrada de `CLAUDE.md`.
- **DA13**: `150702-V` gana por `obras_de_clave` con WARNING; `POSTV` exacto es forma base;
  `V`, `VALENCIA 3` y `POSTE` no llevan marca.
- **Vacío = apagado**: con `Ajustes.activo` falso no actúa nada en sv2–sv5; ningún código
  anterior escribe `postventa` ni `var` como método (`git grep` en b1fb495); ningún test tocado.
- **Encendido sv5 → sv3 → sv2 → sv4**: correcto. sv4 manda la marca y la clave `agr-` mirando el
  dato, no su configuración.

## Interpretaciones (i)–(x) y observación del implementer

- **Acepto** (i) design §5–§6; (iii) solo cambia la etiqueta; (iv) sin ella dos entradas del día
  se pisan; (v) el guardián F-038 va por fichero y `_read` comprueba `truncated`/`max_rows`; (vi)
  las agrupadas piden siempre `con_partida`; (vii) `None` y otro método omiten igual; (viii) un
  único constructor (`FranquiciaIn.a_dominio`) y sin él omite; (ix) sin base omite; (x) probado.
- **Decisión del humano**: (ii) es D1; `ReajustePipeline._choques` es D2.

## Cambios requeridos

1. **`partida_capitulo` con el código del capítulo en vez de la categoría.** Está en
   `services/partes-front/application/services/catalogo_entradas.py:196`
   (`partida_capitulo=h.capitulo_cod`).
   - La columna es `String(8)` y guarda CD/CI/CP/OTRO: `orm_models.py:248-253`,
     `parte_repository.py:368`, `app.py:2083/2303/4258` y el badge `cap-…`.
   - sv3 escribe `categoria` para la misma entrada (`_casar_entrada`).
   - `build_arbol_partidas` da `CD.POSTVENTA` (12) y `CI.07.05.03` (11). En PostgreSQL es un 500
     en `PATCH …/obra` y en `/api/partes/nuevo`. SQLite no impone la longitud y la suite pasa.
   - Sin capítulo CD/CI/CP sale `None`, donde sv3 pone `OTRO` (la hoja `29` de PORSAN del
     fixture), y la plantilla pinta «CI».
   - **Arreglo**: `h.categoria`, más tests con una hoja bajo `CD.POSTVENTA` y otra sin padre.
2. **El desempate de `IndicePostventa` (sv4) no tiene test** (`catalogo_entradas.py:80`,
   `:90-92`, sin cubrir según la puerta).
   - Reimplementa R5–R6 fuera del gemelo, y `test_f072_r25_el_indice_casa_como_casar_postventa`
     nunca tiene dos candidatas.
   - En 4.000 presupuestos aleatorios da 0 diferencias con `casar_postventa`: falta la
     evidencia, no la lógica.
   - **Arreglo**: añadir a ese parametrizado `mas_corto`, `menor_normalizado`, `orden_inverso`,
     `letra_digito`, `letra_punto` y `de_baja` de `tests/test_f072_equivalencia_porcentajes.py`,
     dos exactas con el `ide` invertido y una hoja sin código (`:71`).
3. **Líder, `progress/current.md`**: la línea 6 todavía dice `in_progress`, y la sección de F-072
   no lista T29–T31 con su comando ni enlaza a `tasks.md` / `impl_F-072.md` (C4).

## Decisiones del humano (no bloquean)

- **D1 · (ii).** Con R8 al pie de la letra, `29.3` (inexistente) casa con `29.1` si es la única
  que empieza por 29, `29A` con `29`, y `29` con `29.1` y `29.2` va a revisión. ¿Se confirma, o
  el segundo paso debe ser «el mismo código sin los ceros a la izquierda»?
- **D2 · reajuste.** En una obra agrupada, la extra nueva choca con la de otra entrada del mismo
  recurso, día y código, y queda como no editable: un falso conflicto, en la dirección segura.
  ¿Otra feature, o se amplía R38? Si se aplaza, hay que matizarlo en `azure-apps` §3.5.

## Observaciones (sin bloqueo)

- **O1** `app.js` ~2617: `open()` no resetea `addlineEntradaPartida`. Hoy no se alcanza (un botón
  por página, y el envío exige elegir obra).
- **O2** En la vista `agr-`, «Añadir línea» da 422 hasta que se elige la partida en el combo:
  mirarlo en M2.
- **O3** `CatalogoEntradas.ajustes` (l. 107-109) no se usa: es código muerto.
- **O4** La línea 1196 de `sqlalchemy_parte_repository.py`, sin cubrir: pista para la campaña.

## Cobertura requisito → test (todos en verde)

| Req. | Test |
|---|---|
| R1–R3 | `test_f072_r1/r2_*` en los 4 `test_f072_settings.py`; `r3_*` en sv3, sv4 y sv5; ningún test anterior tocado |
| R4–R9, R41 | sv3 `test_f072_obras_agrupadas.py`, más cada copia (`*_copia.py`) |
| R10, R11, R40 | raíz: `test_f072_equivalencia_porcentajes.py`, `test_f072_obras_agrupadas_gemelos.py`, `test_f072_documentacion.py` |
| R12, R13, R43 | sv2 `test_f072_marca_sv2.py` |
| R14–R19, R42 | sv3 `test_f072_entrada_agrupada.py`, `test_f072_pipeline.py` |
| R20–R22 | sv3 `test_f072_conciliacion.py` |
| R23–R35 | sv4 `test_f072_repositorio.py`, `test_f072_catalogo_entradas.py`, `test_f072_endpoints.py`; R33 también en sv5 por HTTP |
| R36–R39 | sv5 `test_f072_guarda.py`, `test_f072_conflictos.py`, `test_f072_guarda_reajuste_franquicia.py` (enmienda b) |

## Automejora (propuesta, no aplicada)

Añadir a C3 una trampa (4): «un campo del ORM gemelo se rellena con la misma semántica en sv3 y
sv4». Con un test genérico que valide las longitudes `String(n)` antes del `commit`, el cambio 1
no habría pasado en SQLite.
