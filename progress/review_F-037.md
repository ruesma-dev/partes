<!-- progress/review_F-037.md -->
Revisión completa (pasada 1): `git diff dev...eb941c8` (merge-base `6e56244`, rama `feature/F-037-extras-duplicadas-base-omitida`)

# F-037 · Review

**Veredicto: CHANGES_REQUESTED** (solo por las verificaciones MANUAL: el código, los tests y la mutación están bien)

**Rigor:** `critico` (declarado en `features.json`): fase RED, cobertura de lo cambiado ≥ 80 %, mutación con 0
supervivientes sin justificar, y verificaciones `MANUAL (humano)` listadas **con su comando exacto**.

## Qué se ejecutó (resultado real)

- `bash harness/init.sh` tal cual desde el worktree: **exit 0**. Raíz 443 passed, 3 skipped; sv1–sv5 en verde (caché);
  **PUERTA COBERTURA [OK] 100,0 % (83/83)**; PUERTA TAMAÑO OK. Avisos previos: blocked F-014/F-032, ruff 617, infra sin tests.
- sv3 salió por caché: suite sv3 **sin caché** (`-p no:cacheprovider`): **825 passed** en 35,9 s.
- **Fase RED reproducida por mí**: `git archive edc2aab` (T1, antes de producción) en el scratchpad con los tests finales
  `test_f037_dos_pasadas.py` + `test_f037_revert.py`: **34 failed, 7 passed**. Los 7 verdes son R16 (2) y las 5
  caracterizaciones de `revert` que declara el informe. Coincide con las trazas T3 (13), T4 (8) y T5 (13).
- **Mutación, recálculo puro**: `alcance_de_feature("F-037")` = 3 ficheros, **257 líneas** (122 + 14 + 121);
  `generar_mutantes` = **21** (16 + 1 + 4). Coinciden con el informe.
- **Campaña no reejecutada entera: 262,7 s según el informe** (> 60 s). En su lugar, **RM4** sobre una copia
  `git archive HEAD` en el scratchpad contra los tres `test_f037_*`: reproduje 9 de los 21 mutantes al pie de la letra y
  **los 9 caen**: `[:10]→[:11]` (1 fallo), l. 286 `and not→or not` (11) y `and not→and` (7), `_congelado` `or→and` (6),
  l. 104 `and→or` (26), l. 114 `n > 1→n >= 1` (6) y `n > 1→n > 2` (4), `frozen=True→False` en l. 51 (1) y l. 67 (1).
  Copias borradas; `git status` limpio.

## Alcance y decisiones del humano

- **Solo sv3** [x]: `git diff dev...HEAD --stat` de `services/partes-front`, `partes-transfer`, `partes-email`,
  `partes-api`, `orm_models.py`, `CLAUDE.md` y `tests/` (raíz): **vacío**. Fuera de sv3 solo docs, specs, progress,
  `features.json` y `BACKLOG.md` (generado).
- **Regla compartida intacta** (DA1, R18) [x]: el diff de `recurso_conciliador.py` empieza en `_congelado` (l. 111);
  `ESTADOS_CONGELADOS` y `esta_congelado` sin cambios; sv4 `congelacion.py` sin cambios; tests F-015/F-023/F-024 sin
  diff; guardián raíz `test_f024_borrado_no_congela_gemelos.py` verde (en los 443). La lista cerrada no crece.
- **DA2** [x] limpieza en la primera pasada con WARNING de ids (`_log_plan_revert`). **DA3** [x] solo se cuenta (M4).
- **Matiz «ni la tercera línea»** [x]: con la pareja congelada, `_congelado` excluye la base de candidatas y el día
  suma base + extra congelada (`delta = 0`): no se genera ningún split. R11–R14 lo vigilan con
  `extras_reclasificadas == 0` en **cada** pasada y filas idénticas; R13 borra el duplicado previo y no recrea nada.
  El borrado solo actúa sobre `extra_auto` no congeladas de una pareja con extra congelada (`plan_revert` paso 2).
- Lectura del código: `es_miembro` usa el mismo criterio de ordinaria que `_tipo` del cálculo (`"" / normal`,
  `strip().lower()`); `line_index` es único por registro en sv3 (`parte_normalizer`) y en el alta manual de sv4, y
  `crear_extra_desde` (sv4) crea `tipo_hora="extra"`, `extra_auto` falso: no miembro (R2). Caso negativo (base subida,
  extra −2 congelada) también da `delta = 0`. Riesgos R-b/R-c del diseño, aceptados y documentados.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base presentes.
- **C2** [x] una sola `in_progress` (campo `status`: F-037) · [x] rama `feature/F-037-…` · [x] `current.md` con F-037
  arriba; F-033 (verificación pendiente) y F-032 (`blocked`) siguen vigentes · [x] las `done` tienen su resumen.
- **C3** [x] hexagonal: `pareja_extra.py` puro en application (sin imports de infraestructura); el repositorio lo
  consume · [x] primera línea con ruta en los 3 ficheros nuevos y en los modificados · [x] sin prints, TODOs, secretos
  ni dependencias nuevas · [x] trampas: no toca recurso/empleado (hereda `recurso_ide`), ni incidencias (no miembros),
  ni `orm_models.py`.
- **C3 bis** [x] solo se **edita** `docs/referencia/partes-proyecto.md` (no entra documento externo; cabecera previa
  intacta) · [x] sin PDF/ofimática añadidos (`git log --diff-filter=A` vacío) · [x] barrido sobre las líneas añadidas
  de toda la rama con patrones de correo, IPv4, GUID, `password|secret|token|apikey|AccountKey|Bearer` y DNI
  `\d{8}[A-Z]`: solo `12345678Z`, el DNI sintético de los tests · N/A redacciones: no hubo nada que redactar.
- **C4** [x] R1–R20 con test `test_f037_rN_*` en verde (tabla abajo; R21 es MANUAL) · [x] sin red ni PostgreSQL:
  SQLite en memoria y dobles · **[ ] verificaciones MANUAL en `current.md` con su comando exacto**: ver cambio 1.
- **C4 bis**
  - [x] `rigor` declarado: `critico`.
  - [x] **Fase RED**: trazas reales en `impl` (T2–T5) y reproducidas por mí (arriba).
  - [x] **Cobertura**: `[OK]` 100,0 % (83/83).
  - [x] **Mutación**: `progress/mutacion_F-037.md` generado por la herramienta; totales recalculados (257 líneas, 21).
  - [x] **Muertos comprobados**: campaña > 60 s, no reejecutada entera; RM4 sobre 9 de 21, todos muertos.
  - [x] **Coste por mutante**: 262,7 × 6 ÷ 21 = 75 s, muy por encima de 1 s.
  - [x] Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0; línea base medida en 6 workers (46–51 s).
  - [x] **RM1**: SHA medido `a86fdaf…` ≠ HEAD `eb941c8`; desde entonces solo `BACKLOG.md`, `progress/` y `tasks.md`
    (`git diff a86fdaf HEAD --stat`): ningún fichero del alcance. La campaña vale.
  - [x] **RM2**: media 12,5 s × 6 = 75 s frente a línea base ~47 s: coherente (sin salto de orden de magnitud);
    `21 × 12,5 = 262,5` ≈ total.
  - [x] **RM3**: ningún muerto es equivalente (cambian logs contados, borrados, marcas o la inmutabilidad, que tiene test).
  - N/A **RM5**: rigor `critico`, pero no hay ningún superviviente declarado equivalente que muestrear.
  - [x] **RM6**: no se quitó ninguna guarda; los 2 supervivientes de la primera campaña se mataron con tests nuevos.
  - N/A campaña MANUAL: hubo campaña automática con 21 mutantes.
  - [x] 0 supervivientes; la historia de la primera campaña (2 `frozen=False`) está analizada en el informe.
  - [x] «Evidencias» con tests, cobertura, mutantes/supervivientes, tiempos y 6 workers.
  - [x] Ningún N/A sin motivo escrito.
- **C4 ter** N/A: `init.sh` no señaló rutas sensibles para esta rama.
- **C5** [x] `tasks.md` T1–T10 `[x]`, un commit `F-037 Tn:` por tarea (T8 en dos) · [x] árbol limpio, sin temporales ·
  [ ] `done`: no se pone hasta cerrar el cambio 1.

## Cobertura requisito → test

| R | Test(s) |
|---|---|
| R1 | `test_f037_r1_*` (4: orden, `None`, campo ausente, cada campo distingue) |
| R2 | `test_f037_r2_*` (5, incluida la extra explícita congelada que no congela) + `…_r9_extra_explicita_ni_marca…` |
| R3 | `test_f037_r3_*` (4: por base, por extra, nada, vecinas) |
| R4 | `test_f037_r4_*` en `revert` (5) y `…_r4_plan_base_protegida…` |
| R5 | `test_f037_r5_*` en `revert` (3) y `…_r5_plan_extra_protegida…` |
| R6 | `test_f037_r6_*` (WARNING con ids, tope de 10, sin aviso si no hay) y plan (2) |
| R7 | `test_f037_r7_*` en `revert` (2) y plan (4, incluido el orden y la cuenta) |
| R8 | `test_f037_r8_*` (5: libres como siempre, INFO de congeladas, sin INFO de pareja, explícita, idempotencia) |
| R9 | `test_f037_r9_*` (8, incluida la base sin `horas_orig` de R-b) |
| R10 | `test_f037_r10_*` (5: marca, no re-resuelve, suma sin recorte, no pivote, sin splits si solo queda ella) |
| R11–R15 | `test_f037_r11_…`, `r12_…`, `r13_…` (×2), `r14_…` (×2), `r15_…[True/False]` |
| R16 | `test_f037_r16_*` (2, caracterización) |
| R17–R18 | tests F-015/F-023/F-024 sin diff y en verde + guardián raíz F-024 |
| R19 | todo SQLite en memoria / `RepositorioFake`, DNI sintético |
| R20 | lectura: `ARCHITECTURE.md` semántica 3 y los dos párrafos de `partes-proyecto.md` dicen lo pedido |
| R21 | MANUAL (M2), pendiente del humano tras desplegar |

## Cambios requeridos

1. **`progress/current.md` (bloque «Despliegue y verificación MANUAL»): pegar el comando exacto de cada
   verificación**, no la referencia a `design.md` §8. En rigor `critico` C4 exige el comando en `current.md`, y hoy:
   - **M1 y M2**: copiar las dos consultas SQL completas (M1 con la línea descomentada).
   - **M1 debe usar la regla de congelación entera**: `AND (r.sigrid_estado IN ('encolado','registrado','dedicacion')
     OR d.approved)`. Sin `d.approved`, un duplicado sin estado en un parte **aprobado** no sale en M1, pero F-037 lo
     trata como congelado (lo congela la aprobación): no lo borra, salta el WARNING de R7 y M2 no llega a 0. Alinear
     también `design.md` §8.
   - **M3**: la consulta o el comando exacto de logs de `ca-sv3-persistencia` con las dos cadenas a buscar
     («DUPLICADA(S) borrada(s)» y «revisar a mano en Sigrid»).
   - **M4**: escribir la SQL, que hoy no existe en ningún sitio (solo prosa): bases `NOT extra_auto`, `tipo_hora`
     ordinaria, `horas_orig IS NOT NULL`, congeladas (`d.approved` o estado congelante), sin ninguna `extra_auto` de su
     clave (`NOT EXISTS` con `document_id`, `line_index` y `IS NOT DISTINCT FROM` en `empleado_line_no` y `fecha_int`).
   Las cuatro, con la nota «solo lectura, base `partes`, las lanza el humano».

La pasada 2 será incremental desde `eb941c8` y solo mirará ese delta (más `init.sh` entero).

## Automejora (propuesta, no aplicada)

- `.claude/agents/spec-author.md`: en rigor `critico`, cada verificación MANUAL de `design.md` debe traer su comando
  completo (SQL, consulta de logs) **y**, si filtra por «congelado», la regla entera de `esta_congelado`
  (estado **o** parte aprobado), no solo los estados.
