<!-- progress/review_F-078.md -->
Revisión completa (pasada 1, única del carril express) sobre `bd04bb6..87a8693`

# F-078 · Review (reviewer, 2026-11-20)

**Veredicto: APPROVED**

**Nivel:** `express` (declarado en `features.json`, `sdd: false`). Sin fase RED ni mutación;
la cobertura es informativa. Recorrido: C1, C2, C3, C5, un test por criterio `acceptance`.
C3 bis y C3 ter no aplican (no toca `docs/referencia/` ni registra conversaciones). C4 bis: N/A por nivel.
El diff no toca `harness/rigor.local.json`.

## Verificación ejecutada
- `ARNES_SIN_CACHE=1 bash harness/init.sh`: **EXIT 0**, ENTORNO LISTO, ninguna suite por caché.
  Raíz 2537 passed / 48 skipped (22:31); sv1 74, sv2 422, **sv3 2739 passed / 2 skipped**,
  sv4 3809, sv5 1628. `PUERTA CARRIL` 1/3 ficheros, 4/150 líneas, sin rutas sensibles;
  `PUERTA TAMAÑO` impl 40/40; `PUERTA COBERTURA` N/A con motivo (no cambia Python de producción);
  `CAPA E2E` N/A. **El timeout de `test_f019_r30` no se ha repetido**: la raíz sale en verde.
- Tests de F-078 y los dos de F-023 tocados, aparte: 40 passed.
- Choque de «DORSAN»: el maestro de proveedores (data mart, solo lectura) solo trae
  «TRADORSAN, S.L.». Probado con el `ResolutorEmpresa` real y la tabla real: «TRADORSAN, S.L.»,
  «Dorsal», «DORSANA SL» y «D0RSAN» dan `sin_alias`, y «Dorsán S.L.» da la 28. La regla de palabra
  completa (`f" {alias} " in f" {normal} "`) los protege. «Dorsan» no es una palabra del castellano.
  El riesgo que queda es un tercero que se llame exactamente «Dorsan», y hoy no existe ninguno.

## Checkpoints
- **C1** [x] init.sh sin caché en verde · [x] ficheros base presentes.
- **C2** [x] una sola activa (F-078 en `human_review`) · [x] cogida con OK del humano
  (`ok_humano_propuesta` 2026-11-19) · [x] rama `feature/F-078-alias-membrete-dorsan` ·
  [x] `current.md` con la entrada de F-078 (ver O1) · [x] `history.md` sin features done nuevas.
- **C3** [x] sin código de producción: el YAML es configuración de sv3 y va en la capa `config/`.
  La imagen lo incluye (`COPY . .` en `infra/manifests/sv3/Dockerfile`) ·
  [x] la primera línea con la ruta está en el YAML y en el test nuevo · [x] sin prints, secretos ni
  dependencias · [x] trampas del monorepo: no aplican. La tabla solo vive en sv3 y no es gemela de
  ningún otro servicio.
- **C5** [x] no hay `tasks.md` (`sdd: false`): validado contra los `acceptance`, con commits
  `F-078: …` · [x] árbol limpio, sin temporales · [x] `features.json` en `human_review`, coherente.

## Cobertura (acceptance → test)
| Criterio | Test |
|---|---|
| «Dorsan S.L. E HIJOS CONSTRUCCIONES» → 28 con el resolutor y la tabla reales | `test_f078_dorsan_y_porsan_son_la_empresa_28[Dorsan…]` |
| «Porsan …» sigue en la 28 | ídem, con `[Porsan…]` y `[PORSAN E HIJOS…]` |
| Los alias de la 1 siguen como estaban | `test_f078_ruesma_sigue_siendo_la_empresa_1` (ruΞsma, Ruesma), `test_f078_dorsan_no_es_alias_de_la_empresa_1`, `test_f078_ruesma_con_dorsan_da_varias`. La tabla entera queda fijada en `test_f023_r7_…` y `test_f023_da3_por_defecto_…` |
| init.sh en verde | ver Verificación |

**Los tests de F-023 tocados:** `test_f023_empresa_membrete.py::test_f023_r7` y
`test_f023_wiring_sv3.py` (`da3_por_defecto` y `r25`). Fijan la tabla versionada **por igualdad
exacta**, así que añadir un alias los obliga a cambiar. Solo se amplía el literal esperado a
`28: ["PORSAN", "DORSAN"]`, como hizo F-029. Siguen siendo de igualdad, con la 1 intacta, y no
se debilitan.

## Observaciones (no bloquean)
- **O1** (para el líder): la cabecera de `progress/current.md` todavía dice «Feature activa:
  ninguna». F-078 solo consta al final. Hay que corregirlo al cerrar.
- **O2**: `progress/impl_F-078.md` cita los dos tests de F-023 como `tests/…`. Viven en
  `services/partes-persistencia/tests/`.
- **Pendiente del humano:** redesplegar sv3. Los tres partes de la 0730 (11–13/11) ya guardados se
  corrigen desde el portal: el alias solo vale para las ingestas nuevas.

## Cambios requeridos
Ninguno.
