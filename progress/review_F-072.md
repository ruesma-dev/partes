Revisión de evidencias desde af0cac9 · delta `af0cac9..7edc52f` · 2026-11-24

# F-072 · Review de evidencias (reviewer)

**Veredicto: APPROVED.**

**Principal** pasada 2 (`ffd6369..af0cac9`): APPROVED con encargo para T28; pasada 1: CHANGES_REQUESTED, resuelto.

**Nivel de rigor: `critico`**, declarado en `features.json`. Exige fase RED, cobertura ≥ 90 %,
mutación con cero supervivientes sin justificar, RM1–RM7 y MANUAL con su comando. El delta no
toca `rigor.local.json`.

## Ejecución

- `ARNES_SIN_CACHE=1 bash harness/init.sh`: **ENTORNO LISTO**, exit 0. Raíz 2551 (48 skip), sv1 74,
  sv2 579 (1), sv3 2954 (2), sv4 4018, sv5 1809 (1). COBERTURA [OK] 99,7 % (1070/1073); TAMAÑO
  [OK] (impl 215/220, review 140/140); CARRIL N/A; CAPA E2E N/A.
- Árbol limpio al empezar y al terminar; las mutaciones, en una copia (`git archive HEAD`, sin `.env`).

## Delta revisado

- **Producción intacta.** En `services/` el delta solo toca tests (`test_f072_t28_mutantes.py` de
  sv3/sv4/sv5, `test_f072_obras_agrupadas.py` sv3, `test_f072_catalogo_entradas.py` sv4). **T25
  vacío**: `git diff dev --stat -- '*/tests/test_f0[0-6]*'` no devuelve nada.
- **Encargo de la pasada 2, cumplido.** `exacta_y_con_letras` `[(2,"0578",0),(3,"0578B",0)]` y
  `con_letras_mismo_normalizado` `[(3,"0578B",0),(2,"0578-B",0)]` en
  `test_f072_r25_el_indice_desempata_como_casar_postventa`. En la copia, `casar` con los `get`
  intercambiados (`:87`) y `_orden` sin `h.ide` (`:92`) dan 1 fallo de 13 cada uno; control, 13 verdes.

## Mutación (C4 bis)

**Recálculo puro**, con `harness.alcance` + `generar_mutantes` + `seleccionar`, usando la regla
y la semilla del nivel (`_regla_configurada`):

| Concepto | Informe | Recalculado |
|---|---|---|
| Origen | rama `b1fb495..feature/F-072…` | igual |
| Ficheros / líneas | 31 / 2209 | 31 / 2209 (fichero a fichero, igual) |
| Mutantes generados | 604 | 604 |
| Candidatos (uno por línea) | 370 | 370 |
| Tope `critico` | 60 % → 222 en [100, 300], semilla 20261030 | 222 |
| Evaluados | 222 (178 muertos, 44 supervivientes) | **El conjunto sorteado coincide uno a uno con los `evaluados` del JSON** |

- **Cabecera.** No lleva «⚠ CAMPAÑA NO VÁLIDA». «Sin veredicto (base rota)» = 0; timeouts e
  indeterminados = 0. Declara la línea base de los 4 servicios en los 3 workers.
- **Tiempo.** 22 170,9 s (> 60 s): **campaña no reejecutada**; vale el recálculo puro más los
  controles de abajo. Coste por mutante 22 170,9 × 3 ÷ 222 = 299,6 s. **RM2**: la línea base
  ponderada por la muestra (81 sv4, 62 sv3, 52 sv5, 27 sv2) da ~296 s y la media juzgada 261,3 s;
  coherente (con `-x` el muerto corta antes), sin saltos de orden de magnitud.
- **RM1.** SHA medido: `afaf5e3f…`. De `af0cac9` a `afaf5e3` solo cambia `review_F-072.md`; de
  `afaf5e3` a HEAD, solo tests y papeleo. El alcance medido es el revisado.
- **Supervivientes muestreados**, reales con el mismo operador y texto: `obras_agrupadas.py:218`
  (`[:1]`→`[:2]`), `registro_pipeline.py:696` (`False`→`True`), `franquicia.py:246` (`or 0`→`or
  1`) y `entrada_agrupada.py:105` (veracidad).
- **Muertos con tests de T28.** Verificados por mí en la copia, siempre con un control sin
  mutante en verde, `sys.executable -m pytest`:

| Superviviente | Test | Sin mutante | Con mutante |
|---|---|---|---|
| sv3 `obras_agrupadas.py:218` | `-k t28_r41` (sv3) | 1 passed | 1 failed |
| sv5, copia del gemelo `:218` | `test_f072_obras_agrupadas_copia.py` | 114 passed | 1 failed |
| sv5 `registro_pipeline.py:696` | `-k choques_sin_por_partida` | 1 passed | 1 failed |
| sv4 `franquicia.py:246` | `-k sin_recurso_no_toma` | 1 passed | 1 failed |
| sv3 `entrada_agrupada.py:160` | `-k caduca_justo` | 1 passed | 1 failed |
| sv4 `catalogo_entradas.py:87` y `:92` | encargo (arriba) | 13 passed | 1 failed cada uno |

- **Equivalentes** (#1, 12–15, 19–21, 23, 26, 34, 36, 37): `progress/equivalentes_F-072.py` sale
  con **exit 0** en sv2 (#1), sv3 (#19–21, 23, 26, 34, 36), sv4 (#12–15) y sv5 (#37). **Registro
  fiel**: `mutacion_F-072.md` §«Aceptación del humano (2026-11-24)» copia literal «acepto los 13
  equivalentes de F-072» (commit fbfcfac). Supervivientes sin test ni aceptación: 0.
- **RM3.** Repasé los 9 muertos de veracidad y booleano: ninguno es equivalente (`:101 numero is
  not None` → `numero` cambia con el número 0; los `con_partida`/`por_partida` cambian qué choca).
- **RM5** (elegido por mí: el **#23**, que el encargo marcaba como sospechoso). `PartidaNodo`
  (`partida_catalog.py:26`) es un `@dataclass` sin `__bool__` ni `__len__` en su MRO (comprobado
  al importarlo), y `ResultadoEntrada.partida` solo toma `None` (`_sin`) o un nodo de
  `casar_var`/`casar_postventa` (`:133`, `:150`). Es equivalente.
- **RM6.** N/A: T28 no quita ninguna guarda; no cambia producción.
- **RM7** (R36: «omitir **antes de escribir**»). En la copia bajé la puerta un paso:
  `omisiones.update(por_partida)` pasa a ir detrás de `ReglasRegistro(...)`, así que las reglas
  deciden sin la omisión. Con los 181 tests F-072 de sv5, sin `-x`: **15 fallos**, todos de la
  feature (`test_f072_guarda.py::test_f072_r36_omite_en_var[…]`, …). El control da 181 verdes.

## Verificaciones manuales T29–T31 (`progress/manual_F-072.md`, 7edc52f)

Las ejecutó el implementer a petición del humano. Revisé las evidencias sin repetir escrituras
ni lecturas contra Sigrid o `partes`.

- **T29 (M0).** La consulta de la tarea, en conexión `read_only`, da **0 filas**. Hay 4 `VAR-30`
  inactivos. Sostiene DA1, DA2, DA9 y DA13.
- **T30 (M1).** `Counter` de `/api/sigrid/obras`: 88 postventa y 3 VAR. Postventa: conjuntos
  `(empresa, partida_ide)` **idénticos** (88 = 88); VAR idéntico. Los 3 rótulos que difieren
  (0578B, 0654-B, 0676-B casan con dos obras) son los de R24, no de universo. **No se comparó con
  el preview real de porcentajes**: la base `dedicacion` la denegaron los permisos y el universo
  se recalculó con las funciones del repo de porcentajes sobre Sigrid; que coincida con lo
  desplegado depende de que porcentajes despliegue su repo (consulta de cotejo para el humano).
- **T31 (M2).** sv5 local en modo pruebas (`/health`: `modo_pruebas: true`, 0404), sv4 hacia él,
  sin colas. **R28**: 422 «Es una obra agrupada…». **R36**: la línea POSTV2 sin marca, omitida con
  `partida_agrupada: sin entrada postventa: …`. PT26/00417: 4 `hmores` `PRUEBA-IA` con la `paride`
  de cada entrada (303927 `Postv-0342`, 417055 `VAR-29`; **R24**) y synckey `partes:<id>`.
  Limpieza de Sigrid (`limpiar --ejecutar` en una copia con mes 5; `verificar` → «No existe el
  parte del mes») y de `partes` (3 documentos inactivos; T29 vuelve a 0). **R37** y **R38** no se
  ejercitan a mano: los cubren `test_f072_guarda.py`, `test_f072_conflictos.py` y RM7.

## Checkpoints (cierre)

- **C1** [x] `init.sh` sin caché, arriba.
- **C2** [x] Una sola feature activa (`in_review`) y la rama es la correcta. Ver la O7.
- **C3** [x] El delta no trae prints, TODOs ni secretos; está en español. Los tests van con
  datos ficticios y sin red. Las trazas de la prueba manual no traen credenciales.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C3 ter** [x] Sin enmiendas nuevas en el delta.
- **C3 quater** [x] El delta no cambia lo expuesto ni lo consumido; el §3.5 de `azure-apps` ya
  estaba (pasada 2).
- **C4** [x] Los requisitos tienen su test (tabla de la pasada 2, sin cambios). Los MANUAL tienen
  comando y evidencia en `manual_F-072.md`.
- **C4 bis** [x] nivel, RED (pasada 2), cobertura (Ejecución), mutación recalculada, 31 con test +
  13 aceptados, muertos por muestreo (campaña > 60 s, no reejecutada), coste, cabecera, RM1–RM3,
  RM5, RM7. RM6 N/A (sin guardas quitadas). Capa e2e N/A (ningún servicio declara el bloque e2e).
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json`.
- **C5** [x] `tasks.md` T1–T33 en `[x]`, con commits `F-072 Tn:`. Árbol limpio.
  `features.json` en `in_review`: pasar a `human_review` o `done` es cosa del líder.

## Observaciones (sin bloqueo)

- **O7** `current.md` §«F-072 · T28» aún da los equivalentes por «pendientes» y no nombra
  T29–T31: que el líder lo ponga al día al cerrar.
- **O8** En `mutacion_F-072.md` la l. 97 y las 13 entradas siguen en «aceptación pendiente»; manda
  la sección final, pero leído por partes confunde.
- **O9** T31 pedía «cambiar un parte a `VAR-<n>`» y se hizo un alta manual con entrada (R30): el
  cambio de obra a una entrada (R27) no se probó a mano (lo cubren los tests de endpoints).
- **O10** Preview real de porcentajes sin cotejar (T30). **O11** La 0404 conserva 7 líneas
  `PRUEBA-IA` de sesiones anteriores (06, 08, 10), no tocadas por esta prueba.
- **O1**, **O2**, **O4** y **O6** de la pasada 2 siguen en pie (sin bloqueo).

## Automejora (propuesta, no aplicada)

- Las de la pasada 2 siguen en pie. **Nueva, RM4 de `reviewer.md`**: al reproducir un muerto, el
  mutante se aplica **por número de línea**, no por texto (`por_partida: bool = False` sale 3 veces
  en `registro_pipeline.py`: una sustitución por texto mutaría otra línea en silencio).
