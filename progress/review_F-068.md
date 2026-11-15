<!-- progress/review_F-068.md -->
Revisión incremental desde 7f659dd (pasada 2, principal) · HEAD `f6ac5b5`, base `dev` `7e5f600`

# F-068 · Review del reviewer (principal)

- **Veredicto pasada 2:** APPROVED (SHA aprobado: `f6ac5b5`)
- **Pasada 1** (completa, HEAD `7f659dd`): CHANGES_REQUESTED por 3 cambios (RM7 en reasignar,
  R3 contra `partes_recalculo`, T16 sin marcar). Los tres, resueltos abajo.
- **Rigor:** `critico` (declarado): fase RED, cobertura ≥ 90 %, mutación exigida (uno por línea,
  60 %, [100, 300]) sin supervivientes sin justificar, RM1–RM7, MANUAL listadas; e2e informativa.

## Pasada 2 · lo que se ejecutó (salida real)

- `ARNES_SIN_CACHE=1 bash harness/init.sh` ⇒ **exit 0**, ninguna suite por caché: raíz 2457 passed
  / 50 skipped; sv1 74, sv2 422, sv3 2453 (2 skipped), **sv4 3830 passed / 1 skipped** (+3 tests
  nuevos), sv5 1628. `PUERTA COBERTURA: 100.0% de 38 líneas (umbral 90 %)`, `PUERTA TAMAÑO` OK
  (impl 220/220), `CAPA E2E: N/A`. Avisos previos: F-032 blocked, ruff 1013, infra sin tests.
- Delta `git diff 7f659dd..HEAD`: `app.py` (+7/−2), `test_f068_conciliar_recalculo.py` (+32),
  `test_f068_conciliar_js.py` (3 valores de entrada), `tasks.md` (T16), `impl_F-068.md`,
  `current.md`. No toca ficheros nuevos, firmas públicas ni el alcance medido: lo aprobado en la
  pasada 1 sigue valiendo.

## Verificación de los tres cambios

1. **RM7 · R17 (827e111).** Nuevo
   `test_f068_r17_el_mensaje_sale_tras_la_reasignacion_y_los_alias[nombre_leido|worker_key]`, con
   `cola.al_enviar` como el de R1. Reaplicada **mi misma mutación** (subir
   `_recalculo_de_trabajador` por encima del bucle de alias en `empleado_reasignar`) sobre una copia
   del HEAD `f6ac5b5` en mi scratchpad, nunca en el árbol:
   - copia sin mutar: tests F-068 **79 passed**;
   - mutante reasignar: **ROJO**, `2 failed, 77 passed` (las dos formas del test nuevo);
   - mutante conciliar (control): **ROJO**, `1 failed` (`..._r1_el_mensaje_sale_tras_el_casado_y_el_alias`).
   Ahora caen tests **de la propia feature**, sin necesitar una suite vecina. RM7 [x].
2. **Cambio 2 · R3, opción (a) decidida por el humano el 2026-11-15** (consta en `current.md` y en
   `impl_F-068.md` § «Review ciclo 1»; R3 no se enmienda). `_recalculo_de_trabajador` devuelve
   `partes_recalculo = len(documentos)` solo si `estado == ESTADO_PEDIDO`, y 0 con `sin_cola` y
   `fallo`. RED real en el informe (3676be9: `assert ('fallo', 1) == ('fallo', 0)`, `4 failed`).
   Tests: `e5_r5_cola_caida` y `e6_sin_cola` a 0, `r17_reasignar_cola_caida_200_fallo` afirma 0,
   nuevo `r17_reasignar_sin_cola_partes_cero`. El JS solo usa N con `pedido`: sus tres tests de
   `fallo`/`sin_cola` cambian solo el valor de entrada, no lo que afirman. `undo_apply` no devuelve
   `partes_recalculo` (como antes). [x]
3. **T16** `[x]` en `tasks.md` y frase «Sin desviaciones» corregida en el informe (ahora explica la
   discrepancia del ciclo 1 y la decisión del humano). [x]

*Observación menor (no bloquea):* si **marcar** el pedido lanza (R6) pero publicar sale bien,
`recalculo` es `pedido` y `partes_recalculo` = N aunque esos partes no queden en espera. El recálculo
sí se pidió, así que el texto «recalculando extras de N parte(s)» es cierto; el docstring nuevo
(«cuenta los partes en espera») es algo más estricto que el comportamiento en ese caso límite.

## Checkpoints (estado tras la pasada 2)

**C1** [x] init.sh sin caché exit 0 · [x] ficheros base.
**C2** [x] una sola activa (F-068 `in_review`; F-032 `blocked` previa) · [x] prioridad · [x] rama
· [x] `history.md` · [x] `current.md`: la sección F-068 es la sesión activa. *Observación:* el
fichero arrastra ~4.300 líneas de sesiones anteriores ya presentes en `dev`; es cosa del líder.
**C3** [x] hexagonal (`_documentos_de` en infraestructura, orquestación en la ruta como F-042/F-049)
· [x] primera línea con ruta · [x] sin `print`, secretos ni dependencias nuevas · [x] trampas de
dominio: no toca registro en Sigrid, incidencias ni esquema.
**LÍMITE DE SERVICIO** [x] solo sv4 + test raíz + docs. Ni sv3, ni sv5, ni `orm_models.py`, ni
`congelacion.py`, ni `esta_congelado`, ni gemelos de `CLAUDE.md`, ni
`_pedir_recalculo_compartido`/`_seguido`, `marcar_/anular_*`, `_exigir_sin_recalculo`,
`approve_document`, `lineas_para_registro`, `_validar_ambito`. Nada copiado entre servicios.
**C3 bis** N/A: no toca `docs/referencia/`.
**C3 ter** [x] decisiones del humano con fecha (D1–D6, las dos enmiendas y la opción (a) de R3).
**C3 quater** N/A por la spec («¿Cruza la frontera? No»); revisado igual `azure-apps` `ef721cd`:
solo `partes.md` (+13/−1), commit aparte, contenido coherente con design §1/§6. Que ya esté en
`origin/main` (push del 2026-11-15 00:50) lo pregunta el líder al humano; no bloquea.
**C4** [x] R1–R22 con test (tabla abajo), en verde · [x] sin red (SQLite, `ColaFake`, Sigrid falso)
· [x] MANUAL M1 en `requirements.md` y `current.md` (T15, interfaz tras desplegar) · [x] dobles:
el repositorio no tiene comprobador automático; cruce manual: los dobles nuevos son subclases del
repositorio real y sobrescriben métodos que existen; ningún doble previo afectado.
**C4 bis** [x] rigor declarado · [x] fase RED con trazas reales (T1, T3, T5, T8, T10, T11 y los dos
cambios del ciclo 1; T7 caracterización declarada) · [x] cobertura OK 100 % · [x] **RM7** (arriba)
· Mutación (totales, RM1–RM6, supervivientes, análisis, workers): **pendiente: pasada de
evidencias** · [x] «Evidencias» con tests, cobertura, suite y «Capa e2e» (fila de mutantes
pendiente de T14) · Capa e2e: N/A (`CAPA E2E: N/A`, ningún servicio la declara).
**C4 ter** N/A: la puerta no señala rutas sensibles.
**C5** [x] T1–T13 y T16 `[x]`, commits `F-068 Tn:` (T12 verificación sin commit, declarado) ·
T14 (campaña tras este APPROVED) y T15 (M1 del humano tras desplegar) pendientes por protocolo ·
[x] árbol limpio salvo este informe · [x] `features.json` = `in_review`.

## Lo pedido en especial (pasada 1, vigente)

- **El casado no se pierde si el pedido falla:** el colector solo se llena tras el `commit`;
  `_pedir_recalculo_compartido` y `pedir_recalculo` capturan marcar, publicar y anular. Tests E5,
  R6 ×2, R7 ×4, R17 cola caída, R19 cola caída.
- **Sin nombres ni DNIs:** barrido de líneas añadidas y mensajes de commit con `[0-9]{8}[A-Za-z]` y
  `[XYZ][0-9]{7}[A-Za-z]`: solo `99999999R`, sintético y ya de `SigridLookupClientFake` (F-004).
  El INFO lleva contadores, ids de parte y pedido (tests R8). El delta de la pasada 2 no añade datos.
- **Enmiendas a guardianes:** solo las dos autorizadas (F-017 21→23; F-047 `F068_CONCILIAR`). El
  test raíz de F-042 solo amplía `parametrize`. El delta de la pasada 2 no toca guardianes.

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

**Para la pasada de evidencias:** la campaña (T14) se mide sobre `f6ac5b5` o un descendiente que
no toque el alcance (RM1); RM7 ya está hecho en esta pasada y no hace falta repetirlo.

## Automejora (propuesta, no aplicada)

- En `.claude/agents/reviewer.md`, «Dos pasadas»: decir expresamente que **RM7 se aplica en la
  pasada principal** en `critico`. No depende de la campaña, cuesta minutos y, si sobrevive, obliga
  a cambiar tests: hacerlo después invalida la campaña (RM1) y se paga dos veces. Lo demuestra este
  ciclo. Vale para cualquier proyecto ⇒ portarlo a `arnes-base` si el humano lo aprueba.
