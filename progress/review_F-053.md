<!-- progress/review_F-053.md -->
Revisión completa (pasada 1) · `git diff dev...HEAD` (dev 12e1f23 .. HEAD 5947643)

# reviewer · F-053 · Pisar sin borrar (2026-10-21)

**Veredicto: APPROVED**

**Nivel de rigor: `critico`** (declarado en `harness/features.json`). Exige fase RED,
cobertura ≥ 80 % de lo cambiado, mutación COMPLETA con cero supervivientes y verificaciones
MANUAL con comando exacto en `progress/current.md`.

## Ejecución

- `bash harness/init.sh` → exit 0, **ENTORNO LISTO**. Avisos de siempre (feature `blocked`,
  ruff 741 de deuda previa, infra sin tests). `PUERTA COBERTURA` **[OK] 100,0 % de 86**;
  `PUERTA TAMAÑO` [OK]. Raíz: 493 passed, 3 skipped.
- Como `init.sh` tomó sv4/sv5 de la caché («árbol sin cambios»), los relancé enteros sin
  caché: sv5 **855 passed**; sv4 **2372 passed, 1 skipped** (482 s).

## Lo que se pidió mirar con cuidado

- **Ningún `DELETE` en ejecución de sv5.** `grep -i "delete"` en `services/partes-transfer`
  (sin `tests/`): solo `prueba_escritura_sigrid.py` l.469–478 (`limpiar`, DA9).
  `stmt_borrar_linea` no existe (lo fijan `test_f053_r4_fuente_*` y
  `test_f034_r7_el_cliente_no_tiene_ningun_delete`); ver observación 1.
- **`stmt_anular_linea`** (generada y leída): `UPDATE hmores SET can = 0, tot = 0 WHERE ide = ?
  AND reside = ? AND fec = ? AND ISNULL(horide, 0) = ? AND ABS(ISNULL(can, 0) - ?) <= 0.001`
  + los seis `AND ISNULL(<enlace>, 0) = 0` + `AND EXISTS (SELECT 1 FROM con c WITH (UPDLOCK,
  HOLDLOCK) WHERE c.ide = hmores.hmoide AND c.est = ?)`. 6 marcas `?`, 6 parámetros, todo
  parametrizado; `SET` solo `can` y `tot` (R3). Coincide con design §4 y DA12.
- **Choques** (`pisado.choques`): con horas salvo si la nueva es `CI*`; R8 en `_evaluar`:
  `parte_cerrado` → `incidencia_en_sigrid` → `linea_enlazada` → conflicto. La enlazada nunca
  llega a `stmt_anular_linea` (omisión en paso 7 + `_sin_enlaces()` en el SQL; si se enlaza
  en la ventana, `pisada_no_anulada`: `test_f053_r10_pisada_enlazada_en_la_ventana`). R4 de
  F-034 intacto (`NOT EXISTS … ISNULL(p.can, 0) <> 0` en `stmt_insert_linea`).
- **`anuladas`** en `resultado_a_dict` (HTTP), `_resultado_fallido` (cola), `reparto_obras`
  y `resultadoHtml`; ningún lector de `borradas` del resultado de sv5 queda en sv4 (los
  `borradas` que quedan son de la comprobación de F-024, otro contrato).
- **Desviación 1 (`transfer_consumer.py`)**: aceptada. Solo cambia la clave de
  `_resultado_fallido` y el docstring; R12/DA7 piden la clave en «los dos canales» y la
  enmienda de `test_f002_mutantes.py` l.157 que lista la propia spec prueba esa función. Sin
  cambio de lógica. Las otras 8 desviaciones, revisadas: justificadas y sin efecto fuera de
  la feature.
- **Tests enmendados, ninguno relajado** (11 ficheros, leídos uno a uno): todos pasan de
  «la fila desaparece» a «la fila sigue con `can = 0`, `tot = 0` y el resto intacto», y
  añaden `"borradas" not in …`. El único que pierde un camino es
  `test_f034_t12_pisada_con_can_nulo_no_esta_viva` (ahora ni choca, por R5); el criterio
  `can` NULL ⇒ sin horas sigue fijado por `test_f053_r5_tiene_horas[None]`.
- **sv4**: modal y resultado escapados con `esc` (también la pisada, que antes no lo
  estaba); ningún «se borra» afirmativo; `MOTIVO_LINEA_REGISTRADA` = texto de DA8, sin
  aconsejar borrar. Las plantillas «se borraron alli» describen a Administración (design §2).
- **Gemelos y límite de servicio**: `estado_parte.py`, `cuenta_analitica.py`,
  `comprobacion_lineas.py`, `recurso_conciliador.py` (sv3), reajuste y `prueba_escritura_*`
  fuera del diff. sv1–sv3 sin cambios. `CLAUDE.md` sin tocar: la lista cerrada no crece.
- **azure-apps 7b057b8**: solo `partes.md` (+26), árbol limpio, sin push. Paso 5 y «Qué se
  rompe» con la nota a `porcentajes` en sus tres puntos (design §10). Correcto.
- **MANUAL** en `progress/current.md`: M2 (escribe A y la pisa con B en 0404, antes de
  desplegar), M3 (A a 0 ya no choca; reaprobar A = `ya_registrado`; `limpiar` con DRY-RUN y
  «si sale otro ide, PARA») y M4 (textos tras desplegar), cada una con comando PowerShell
  exacto y resultado esperado; aviso explícito de **no usar 10/2026** (PT26/00373, 4 líneas
  `PRUEBA-IA` de F-046). M2 usa una línea del portal como pisada en vez de una manual: el
  propio documento lo dice («variante sin tocar Sigrid a mano») y la manual es el mismo
  `UPDATE` (origen solo cambia el INFO de R13).
- **Datos**: barrido del diff (`print(`, `TODO`, `password|secret|AccountKey|Bearer`,
  `@ruesma`, DNI `\d{8}[A-Z]`): 0. Motivos sin tildes (DA3 de F-034); docs con tildes.

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros del arnés.
**C2** [x] una sola `in_progress` (F-053) · [x] rama `feature/F-053-pisar-sin-borrar` ·
[x] `current.md`: F-053 activa; la sección de F-034 se conserva por sus M2–M4 pendientes de
desplegar (práctica vigente del repo) · [x] `done` con resumen en `history.md` (sin cambios).
**C3** [x] hexagonal: `pisado.py` (application) importa solo `domain`; SQL en
`infrastructure` · [x] primera línea con ruta en los 5 ficheros nuevos · [x] sin prints,
TODOs ni secretos; sin dependencias nuevas · [x] trampas: (1) recurso = `hmores.reside`, sin
cambio; (2) incidencias: no se duplican (R6) y no se tocan las intermedias; (3) ORM sin
cambios.
**C3 bis** N/A: la feature no toca `docs/referencia/` (`git diff --name-only` vacío).
**C4** [x] R1–R23 con tests (tabla abajo), en verde · [x] sin red ni BBDD (dobles y `httpx`
simulado; `node` solo ejecuta `app.js`) · [x] MANUAL M2–M4 con comando exacto.
**C4 bis** [x] rigor `critico` declarado · [x] fase RED con salida real para T1–T6, T9,
T10/T11 (R1, R2, R4–R12, R19–R22); R15–R18 de caracterización, como dice la spec ·
[x] cobertura [OK] 100 % · [x] mutación verificada aparte (abajo) · [x] muertos comprobados:
campaña **no reejecutada: 1.017,8 s según el informe** (> 60 s); recálculo puro + RM1–RM6 +
RM4 · [x] coste por mutante 1.017,8 × 4 ÷ 57 = 71,4 s (> 1 s) · [x] sin «CAMPAÑA NO VÁLIDA»,
«Sin veredicto (base rota)» = 0 y líneas base medidas · [x] RM1 · [x] RM2 · [x] RM5 N/A:
cero supervivientes, ningún «equivalente» que reproducir · [x] RM6 · [x] manual: N/A, la
campaña es automática con 57 mutantes · [x] cero supervivientes, ningún análisis pendiente ·
[x] «Evidencias» con los cuatro números y 4 workers · [x] ningún N/A sin motivo.
**C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
**C5** [x] T1–T13 y T15 `[x]` con commit `F-053 Tn:` cada una (T10 en dos); T14 es MANUAL
(humano) y queda `[ ]` a propósito · [x] árbol limpio · [x] `features.json`: `in_progress`
(pasa a `done` el líder tras este APPROVED).

## Mutación: verificación independiente

- **Recálculo puro** (`alcance_de_feature("F-053")` + `generar_mutantes`): 11 ficheros,
  **314 líneas, 57 mutantes**, mismo reparto por fichero que el informe (pipeline 11,
  `parte_abierto` 4, `pisado` 30, cliente 8, `reparto_obras` 2, `registro_models` 1,
  `transfer_consumer` 1, el resto 0).
- **RM1**: medido en `dcf427a`; de ahí a HEAD solo cambian `progress/` y `tasks.md`: el
  alcance no se movió (el recálculo en HEAD da los mismos 57).
- **RM2**: media 17,9 s × 4 workers = 71,6 s por mutante, coherente con 55 mutantes de sv5
  (base 9,6–24,4 s) y 2 de sv4 (base ~437 s) en paralelo, más la línea base de sv4.
- **RM3**: repasados los 57; ninguno equivalente (los `or 0 → or 1` y `[0] → [1]` cambian
  el valor o lanzan `IndexError`/`TypeError` con los datos de los tests).
- **RM4** (copia de sv5 en el scratchpad, árbol real intacto): `registro_pipeline.py` l.707
  `and → or` ⇒ 3 fallos; `pisado.py` l.48 `!= 0 → != 1` ⇒ 28 fallos. Base de la copia: 1
  fallo ajeno (`test_f002_r11_…manifiesto`, que lee `infra/` fuera de la copia).
- **RM6**: no se quitó ninguna guarda; `float(ls.can or 0) != 0` pasa a `tiene_horas`, que
  conserva la defensa de `None`.

## Cobertura requisito → test

| R | Test(s) |
|---|---|
| R1 | `test_f053_r1_ejemplo_1_…`, `…_r1_cada_pisada_con_lo_que_se_leyo`, `…_r1_todo_bajo_el_lock` |
| R2, R3 | `test_f053_cliente_anular.py::…_r2_*` (texto y parámetros exactos), `…_r3_anular_solo_cambia_can_y_tot`; doble `…_doble_anular_*` |
| R4 | `…_r4_fuente_cliente_sin_delete_ni_borrar`, `…_r4_fuente_pipeline_…`, `test_f034_r7_…ningun_delete` |
| R5 | `test_f053_pisado.py::…_r5_*`, `…_pipeline_pisado.py::…_r5_*` (ejemplo 2, parte cerrado a 0) |
| R6, R7, R8 | `…_r6_*`, `…_r7_*` (ejemplos 3 y 4), `…_r8_*` (cuatro precedencias) |
| R9 | `…_r9_lineas_existentes_sql_exacto`, `…_r9_reajuste_usa_la_misma_expresion` |
| R10 | `…_r10_*` (ejemplo 5, enlazada en la ventana, parte cerrado manda) |
| R11 | `…_r11_motivos_caben_en_255`, `…_r11_motivos_sin_tildes_ni_datos_personales`, textos exactos |
| R12 | `…_r12_*` (relectura, ausente, JSON de los dos canales) |
| R13, R14 | `…_r13_*` (`caplog`), `…_r14_falla_la_relectura_por_ide` |
| R15–R18 | `…_r15_…ya_registrado`, `…_r16_…presente_con_diferencia`, `…_r17_*`, `…_r18_*` |
| R19–R22 | `services/partes-front/tests/test_f053_textos_pisado.py` (node), `test_f053_r22_fuente_*` (sv5) |
| R23 | revisión manual de `docs/ARCHITECTURE.md` y `azure-apps/partes.md` (arriba) |

## Observaciones (no bloquean)

1. `services/partes-transfer/tests/dobles_reajuste.py` l.18 y l.49: la trampa
   `stmt_borrar_linea` ya no vigila nada (el método no existe); retirarla cuando se toque.
2. M2 es la única prueba del `UPDATE` contra SQL Server real: respetar su orden (local
   antes de `redeploy`).

## Cambios requeridos

Ninguno.
