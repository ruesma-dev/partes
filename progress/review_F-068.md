<!-- progress/review_F-068.md -->
Revisión de evidencias desde f6ac5b5 (pasada de evidencias) · HEAD `94ecd18`, base `dev` `7e5f600`

# F-068 · Review del reviewer (evidencias)

- **Veredicto (evidencias):** APPROVED
- **Principal** (pasada 2, incremental desde `7f659dd`): APPROVED en `f6ac5b5`, tras resolver los
  3 cambios de la pasada 1 (RM7 en reasignar, R3 con `partes_recalculo` = 0 salvo `pedido`, T16).
  Detalle: `git show 5c84138:progress/review_F-068.md`.
- **Rigor:** `critico` (declarado). Exige fase RED, cobertura ≥ 90 %, mutación (uno por línea,
  60 % de los candidatos acotado a [100, 300]; con ≤ 100 candidatos, campaña completa),
  0 supervivientes sin justificar y RM1–RM7. e2e informativa.

## Lo que se ejecutó (salida real)

- `ARNES_SIN_CACHE=1 bash harness/init.sh` ⇒ **exit 0**, «ENTORNO LISTO»: raíz 2457 passed /
  50 skipped; sv1 74, sv2 422, sv3 2453 (2 skipped), sv4 3830 (1 skipped), sv5 1628.
  `PUERTA COBERTURA: 100.0% de 38 líneas (umbral 90 %, del nivel critico)`, `PUERTA TAMAÑO` OK,
  `CAPA E2E: N/A`. Capa local: solo `mutacion.timeout_por_mutante_s`; la rama no toca
  `harness/rigor.local.json` (sin aviso `CAPA LOCAL DE RIGOR`).
- Delta `git diff f6ac5b5..HEAD`: `progress/review_F-068.md` (5c84138); `progress/mutacion_F-068.md`,
  `progress/impl_F-068.md` (fila de mutantes y «Pendiente») y `tasks.md` (T14 `[x]`) en 94ecd18.
  **Ninguna línea de producción ni de tests**: lo aprobado sigue valiendo.
- Recálculo puro (script en mi scratchpad: `harness.alcance.alcance_de_feature` +
  `generar_mutantes` + `seleccionar` con la regla `critico` y la semilla 20261030) sobre HEAD:

| Fichero (sv4) | Líneas | Mutantes (informe / recalculado) |
|---|---|---|
| `infrastructure/database/parte_repository.py` | 43 | 9 / 9 |
| `infrastructure/persistencia/recalculo_publisher.py` | 5 | 0 / 0 |
| `interface_adapters/web/app.py` | 58 | 7 / 7 |
| **Total** | **106** | **16 / 16** → **10 candidatos**, tope 100, 10 elegidos |

  Los 10 elegidos recalculados son **exactamente** los 10 de `progress/mutacion_F-068.json`
  (misma clave fichero/línea/col/operador/original/mutado), todos con veredicto `muerto`.

## C4 bis · mutación (lo que la principal dejó pendiente)

- [x] **Informe de la herramienta** con totales reales: 16 generados, 10 evaluados, 10 muertos,
  0 supervivientes, 0 timeouts, 0 indeterminados, **0 sin veredicto (base rota)**, sin cabecera
  «⚠ CAMPAÑA NO VÁLIDA»; la línea base corrió en los 4 workers (885–894 s).
- [x] **Regla del nivel.** `critico`: tope = `min(300, max(100, ceil(0,6 × C)))` = 100 con C = 10.
  Como C ≤ tope, `seleccionar` no sortea: **campaña completa** de los candidatos, uno por línea.
  El rango [100, 300] acota la *muestra*; no es un mínimo de mutantes evaluados: `rigor.json` lo
  dice («con 100 candidatos o menos, campaña completa») y la GUÍA de la 1.10 lo repite. Un diff
  con 10 líneas mutables no puede dar más. **Cumple.** La fila «Muestreo» del informe coincide.
- [x] **Fichero sin mutantes** declarado, sin `PENDIENTE`. Sus 5 líneas en alcance (47–51) son dos
  comentarios `#:` y tres constantes de cadena (`MOTIVO_*`). **Prueba de control**:
  `generar_mutantes` sobre el fichero entero, sin exclusión de alcance ⇒ **3 mutantes** (en otras
  líneas): el generador funciona y el cero es legítimo. Los valores los fijan
  `test_f068_r20_constantes_de_motivo` y el contrato raíz de F-042 (+9 casos).
- [x] **Muertos comprobados.** «Tiempo total» 3071,3 s (> 60 s): **campaña no reejecutada: 51 min
  según el informe**; vale el recálculo puro y RM1–RM6. Coste por mutante = 3071,3 × 4 ÷ 10 ≈
  1228 s, muy por encima de 1 s.
- [x] **RM1.** SHA medido `5c84138c26b68a86556a28312ea74e5578393696` (completo). Entre `f6ac5b5` y
  él, y entre él y HEAD, solo hay papeleo (`progress/`, `tasks.md`): el alcance medido es el
  revisado, y mi recálculo sobre HEAD da el mismo (106 líneas, 16 mutantes). No hay que repetirla.
- [x] **RM2.** Línea base ~890 s, media por mutante evaluado 307,1 s (≈ 0,34× la base: sin salto
  de orden de magnitud); 10 × 307,1 = 3071 = «Tiempo total». La media con suite entera (523,7 s)
  queda bajo la base porque cada muerto aborta con `-x`; con 10/10 muertos es lo esperable (caso
  F-038). Corrió a la vez que la campaña de F-072 (declarado en el impl): solo la encarece.
- [x] **RM3.** Revisados los 10 muertos uno a uno: ninguno equivalente. Los dos de `veracidad`
  (`if documentos is not None:` → `if documentos:`, líneas 3432 y 3949 del repositorio) **no** lo
  son: la ruta pasa un colector `[]` vacío, que con el mutante no se llena. Los de `comparacion`,
  `not`, `entero` (0→1 en `partes_recalculo`) y `logico` (`and`→`or`) cambian lo observable.
- [x] **RM4.** No hizo falta: ningún veredicto dudoso.
- N/A **RM5**: ningún mutante declarado equivalente (0 supervivientes).
- N/A **RM6**: el delta no toca producción; no se quitó ninguna guarda para matar mutantes.
- [x] **RM7**: hecho en la principal sobre `f6ac5b5` (reasignar y conciliar, ambos ROJO con tests
  de la propia feature); el delta no toca código y sigue vigente.
- [x] **Supervivientes y su análisis**: ninguno; nada que reproducir.
- [x] **Evidencias**: la fila de mutantes del impl trae totales, 4 workers, línea base y SHA.
  Capa e2e: N/A (`CAPA E2E: N/A`, ningún servicio declara el bloque e2e).

## Checkpoints (estado final)

**C1** [x] init.sh sin caché exit 0 · [x] ficheros base.
**C2** [x] una sola activa (F-068 `in_review`) · [x] rama `feature/F-068-conciliar-pide-recalculo`.
**C3** [x] (principal; el delta no toca código) · **LÍMITE DE SERVICIO** [x] solo sv4 + test raíz
+ docs · **C3 bis** N/A: no toca `docs/referencia/` · **C3 ter** [x] · **C3 quater** N/A por la
spec (no cruza la frontera); `azure-apps` `ef721cd` revisado en la principal.
**C4** [x] R1–R22 con test (tabla abajo) y en verde · [x] sin red · [x] MANUAL M1 listada.
**C4 bis** [x] rigor · [x] fase RED · [x] cobertura 100 % · [x] mutación y RM1–RM7 (arriba) ·
[x] Evidencias · Capa e2e N/A (motivo arriba).
**C4 ter** N/A: la puerta no señala rutas sensibles.
**C5** [x] T1–T14 y T16 `[x]`, commits `F-068 Tn:` · T15 (M1, humano tras desplegar) pendiente
por protocolo · `features.json` = `in_review`.

## Cobertura requisito → test

| R | Test(s) |
|---|---|
| R1, E1, E2 | `test_f068_conciliar_e1_r1_*`, `_e2_r1_*`, `_r1_el_mensaje_sale_tras_el_casado_y_el_alias` |
| R2, E4 | `test_f068_conciliar_e4_r2_*` (×2) |
| R3 | `test_f068_conciliar_r3_*`, `_e5_*`, `_e6_*`, `test_f068_r17_reasignar_sin_cola_partes_cero` |
| R4, E3 | `test_f068_e3_r4_*`, `test_f068_e4_r4_*` (repo), `test_f068_conciliar_e3_r4_*` |
| R5, E5, E6 | `test_f068_conciliar_e5_r5_cola_caida`, `_e6_sin_cola` |
| R6 / R7 | `test_f068_conciliar_r6_*` (×2) / `_r7_*` (×4) |
| R8 | `test_f068_conciliar_r8_*` (×2), `test_f068_r17_reasignar_info_sin_nombres` |
| R9 / R10 | `test_f068_r9_*` (×3, caracterización) / `test_f068_conciliar_r10_*` |
| R11–R13, E7 | `test_f068_e7_r12_r13_*` (×3 endpoints de aprobar) |
| R14–R16 | `test_f068_conciliar_js.py` `r14`/`r15`/`r16` (node real) |
| R17 | `test_f068_r17_*` (repo ×4, ruta ×15, incluido el orden tras los alias) |
| R18 | `test_f068_r18_*` (×5, orden `alert` → `reload`) |
| R19 | `test_f068_r19_*` (repo ×5, ruta ×4) |
| R20 | `test_f068_r20_constantes_de_motivo`; raíz `test_f042_contrato_recalculo.py` (+9) |
| R21 / R22 | gemelos y suite en verde, diff sin ficheros vedados / `test_f068_r22_*` (×2) |

## Cambios requeridos

Ninguno.

## `progress/mutacion_F-068.json` (sin versionar): **se versiona**

Es el estado que deja toda campaña fiable (`escribir_estado`, F-058 de `arnes-base`) para
`--incremental`; su diseño lo llama «estado del proyecto, no papeleo», no está en `.gitignore` y
`arnes-base` versiona los suyos (`progress/mutacion_F-019.json`, `F-023`, `F-026`). Vive además en
un worktree que se borrará: sin commit se pierde. Es el primero de `partes` porque la 1.10.1 acaba
de entrar. Su contenido cuadra con el `.md` (verificado arriba). No lo commiteo yo (no es mi
artefacto): que lo haga el implementer o el líder, con ruta explícita, antes de integrar.

## Observaciones (no bloquean)

- Sigue la de la principal: si **marcar** el pedido lanza (R6) y publicar sale bien,
  `partes_recalculo` = N aunque esos partes no queden en espera; el docstring es más estricto.

## Automejora (propuesta, no aplicada)

- Sigue la de la principal (RM7 en la pasada principal en `critico`).
- `reviewer.md` y `CHECKPOINTS.md` (C4 bis): decir que `[min_mutantes, max_mutantes]` acota la
  **muestra** y que con C ≤ tope la campaña completa cumple aunque C < `min_mutantes`. Hoy
  «60 %, [100, 300]» se lee como un mínimo y obliga a ir a la GUÍA para descartarlo.
- `implementer.md`: decir que `progress/mutacion_F-XXX.json` se commitea junto al `.md`.
  Las tres valen para cualquier proyecto ⇒ `arnes-base` si el humano las aprueba.
