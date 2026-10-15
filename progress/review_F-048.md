<!-- progress/review_F-048.md -->
Revisión completa (pasada 1) — `git diff dc03468...1bf221c` (HEAD de la rama). F-048.

**Veredicto: CHANGES_REQUESTED** (un único cambio, pequeño: residuo de coma flotante
en `horas_extra_leidas`, que incumple R2 y R22; ver «Cambios requeridos»).

**Rigor** `critico` (declarado en `features.json`): fase RED con traza, cobertura ≥ 80 %,
mutación completa con 0 supervivientes sin justificar y MANUAL con su comando.

## init.sh y suites (ejecutado por el reviewer, 2026-10-16)

- `bash harness/init.sh` ⇒ **ENTORNO LISTO**, exit 0. Raíz 487 passed / 3 skipped
  (169 s); sv1–sv5 en verde (por caché: árbol sin cambios). `PUERTA COBERTURA: 100.0%
  de 16 líneas cambiadas (16/16, umbral 80%, nivel critico)`. `PUERTA TAMAÑO` dentro de
  topes. Avisos previos ajenos (features `blocked`, 700 de ruff, `infra` sin tests).
- Como sv3/sv4 salieron por caché, se ejecutaron aparte sin caché: **sv3 completa 1447
  passed**; sv4 `test_f048_traza_portal.py` + los dos guardianes de sv4 ⇒ **53 passed**.

## Lo que se ha comprobado

- **Diff de producción** = los ficheros de design §3. Desviación documentada y correcta:
  el detalle de parte también pasa por `_registro_view` (basta un sitio).
- **R19 / design §4**: `git diff dc03468 --stat` sobre conciliador, `reparto_ponderado`,
  `pareja_extra`, `jornada_resolver` (x2), `congelacion`, `tipo_hora_resolver`,
  `persist_parte_pipeline`, sv1/sv2/sv5, `infra/` y `static/` ⇒ vacío.
- **Gemelo ORM**: `cmp` de las dos copias de `orm_models.py` ⇒ idénticas.
  `ddl_complementario` se genera del ORM: la columna entra sola (test R24).
- **Clones de `ParteRegistroOrm`** (3 en sv4, `apply_extras_splits` en sv3): enumeran
  campos a mano y ninguno copia `horas_extra_leidas` ⇒ nacen con NULL (R8, R23).
- **Los nueve guardianes 56→57** (opción A del humano): leídos uno a uno. Solo cambian
  `== 56`→`== 57`, la entrada `"horas_extra_leidas"` tras `"horas_orig"` en
  `COLUMNAS_PARTE_REGISTROS`, un mensaje y docstrings. Ningún comportamiento tocado.
- **Aclaración del humano sobre DA2** («por día solo hay una fila de extras y otra de
  ordinarias»): `test_f048_r9_r11_exactamente_dos_lineas_…[caso-1|caso-2|4+2]` (sin
  partidas) exige 2 líneas activas, una `normal` y una `extra_auto`, 0 `extra`
  explícitas, con 8+2, 8+1 y 8+(−2).
- **R25**: ARCHITECTURE, `partes-proyecto.md` y `azure-apps` `2cf42ec` (solo
  `partes.md`, sin push): correctas y coherentes con el código.

## Hallazgo bloqueante: residuo de coma flotante en `horas_extra_leidas`

`parte_normalizer.py:291-301` calcula `leidas = min(p_horas, acumulado - ord_leidas)`
sin redondeo ni tolerancia, y guarda `leidas if leidas > 0 else None`. Reproducido en
el worktree (normalizador puro):

| Fila (ord / extra / partidas) | `horas_extra_leidas` emitido | Esperado (R2) |
|---|---|---|
| 4,3 / 5 / P1 2,1 · P2 2,2 · P3 abierta | P1 None · **P2 8,88e-16** · P3 5,000000000000001 | None · **None** · 5 |
| 4,3 / 5 / — | 5,000000000000001 | 5 |
| 8,1 / 0,2 / — | 0,1999999999999993 | 0,2 |

Consecuencias: R2 («nula si no tiene ninguna») se incumple en P2, y con R22 el portal
pinta en esa línea **«incl. 0,00 h extra leídas»** (`_fmt_horas` da `0,00 h`); en el
caso sin partidas pinta «5,00 h» en vez de «5 h». El valor queda guardado para siempre
(es la traza de lo leído) y cualquier consulta `horas_extra_leidas > 0` (M4 o futuras)
lo cuenta. El conciliador no lo corrige: redondea `horas`/`extra_auto` a 2 decimales
(`reparto_ponderado.py:209,259`), pero no toca esta columna. El mismo fichero ya usa
tolerancia `1e-9` en el reparto por partidas: el criterio existe, falta aplicarlo aquí.

## Mutación (C4 bis)

- Informe generado por la herramienta; sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base
  rota)» = 0; línea base medida en los 6 worktrees (51,5–58,7 s).
- **Recálculo independiente (puro)** con `harness.alcance.alcance_de_feature("F-048")` y
  `harness.mutacion.generar_mutantes`: 6 ficheros, **45 líneas**, **11 mutantes**, todos
  en `parte_normalizer.py` ⇒ coincide con el informe.
- **Campaña no reejecutada: 235,4 s según el informe** (> 60 s): recálculo puro + RM1–RM6.
- Coste por mutante = 235,4 × 6 ÷ 11 ≈ 128 s (> 1 s). **RM2**: media 21,4 s × 6 workers
  ≈ 128 s frente a línea base ~55 s: coherente (los 6 compiten; el total incluye la base).
- **RM1**: SHA medido `8b616b3…`; de ahí a HEAD solo cambian `progress/` y `tasks.md`
  (`git diff --stat 8b616b3..HEAD`) ⇒ el alcance medido es el revisado. **Pero** el
  cambio requerido toca `parte_normalizer.py`: la campaña habrá que repetirla.
- **RM3**: ninguno de los 11 es equivalente. `extra_pos > 1` lo mata
  `test_f048_r7_info_con_decimales` (0,5 extras); `leidas > 1` lo mata la P2 con 1,0 de
  `test_f048_r2_la_extra_cae_donde_se_acaban_las_ordinarias`; `>= 0` en `suma` cambia
  `filas_extra_sumadas` (R7); `leidas >= 0` da 0,0 en vez de None (R3).
- **RM5** N/A: 0 supervivientes, ningún equivalente. **RM6** N/A: no se quitó ninguna guarda.

## Checkpoints

- **C1** [x] init.sh exit 0 (ver arriba) · [x] ficheros base del arnés presentes.
- **C2** [x] una sola `in_progress` en esta rama (F-048; F-046 vive en su worktree por
  excepción del humano anotada en `current.md`) · [x] rama `feature/F-048-…` ·
  [x] `current.md`: la sección F-048 es la sesión activa; los bloques de F-045 que
  siguen debajo vienen de `dev` dc03468 (no los introduce F-048), limpieza del líder
  al cerrar · [x] features `done` con su resumen en `history.md` (sin cambios aquí).
- **C3** [x] hexagonal: el dominio solo gana un campo `Optional[float]`; la lógica en
  `application/`, la persistencia en `infrastructure/` · [x] primera línea con ruta
  (los 4 tests nuevos, mismo formato que el resto del repo) · [x] sin prints, TODOs,
  secretos ni dependencias nuevas · [x] trampas: (1) empleado≠recurso no se toca;
  (2) incidencias intactas (R5, test con `AT`); (3) ORM duplicado cambiado en las dos
  copias, `cmp` idéntico, lectores listados (sv3 ingesta, sv4 vistas).
- **C3 bis** [x] cabecera con origen y fecha (`partes-proyecto.md`, documento propio,
  sin cambios de cabecera) · [x] sin originales PDF/ofimática (`git log --diff-filter=A`
  sobre la rama: ninguno) · [x] barrido sobre las líneas añadidas en `docs/referencia/`
  con patrones de correo, IPv4, GUID, `password|passwd|secret|token|api_key|AccountKey|
  SharedAccess|Bearer|-----BEGIN` ⇒ **0 coincidencias** · [x] nada redactado.
- **C4** [ ] **R2 y R22 no se cumplen en el caso de coma flotante** (hallazgo de arriba);
  el resto de requisitos, cubiertos (tabla abajo) · [x] tests sin red ni BBDD real
  (SQLite en memoria, `TestClient`) · [x] M1–M5 en `current.md` con su comando o el
  enlace a la SQL exacta de design §9.
- **C4 bis** [x] rigor declarado · [x] fase RED con traza real para T1–T4 (R1–R24) ·
  [x] cobertura 100 % (16/16) · [x] mutación verificada (arriba) · [x] sin cabecera de
  campaña no válida · [x] RM1 · [x] RM2 · [x] RM5 N/A justificado · [x] RM6 N/A
  justificado · [x] campaña manual N/A (la automática dio 11) · [x] 0 supervivientes ·
  [x] «Evidencias» con los cuatro números y los workers.
- **C4 ter** N/A: no hay `harness/rutas_sensibles.json` (solo el `.ejemplo`).
- **C5** [x] T1–T10 `[x]` con su commit `F-048 Tn:`; T0 aplazada por decisión del humano
  (anotada en `tasks.md` y `current.md`): riesgo de fusión conocido, no defecto, pero
  hay que hacerla y repasar init.sh antes de `done` · [x] árbol limpio ·
  [x] `features.json` en `in_progress`, coherente.

## Cobertura requisito → test

Todos los tests `test_f048_*` (68: 5 + 28 + 23 + 12) llevan el requisito en el nombre.
R1–R5, R7: `test_f048_normalizer.py` (tabla de design §7 entera); R6, R24:
`test_f048_esquema.py`; R8–R18: `test_f048_conciliar.py` (R9–R11 con el test de «dos
líneas exactas»); R22–R23: `test_f048_traza_portal.py`; R19: diff vacío + gemelos F-024,
F-015 R19, F-010; R20: por construcción + M1; R21: `test_f010_orm_models_gemelos.py`;
R25: lectura + `test_documentos_del_arnes.py`. **Hueco: R2 y R22 sin caso de coma
flotante** (cambio requerido 2).

## Cambios requeridos

1. `services/partes-persistencia/application/services/parte_normalizer.py:291-301`:
   que `horas_extra_leidas` no arrastre residuo de coma flotante. Propuesta: redondear
   `leidas` a 2 decimales (el criterio del conciliador, `reparto_ponderado.py:209,259`)
   y emitir `None` si el redondeado es ≤ 0. No tocar el cálculo de `horas` ni el bucle
   de partidas (R3/R5 deben seguir idénticos).
2. `services/partes-persistencia/tests/test_f048_normalizer.py`: test(s) de R2 con los
   tres casos de la tabla del hallazgo (P2 ⇒ `None`; 4,3+5 ⇒ `5.0` exacto; 8,1+0,2 ⇒
   `0.2` exacto), con su traza RED en `progress/impl_F-048.md`.
3. Repetir la campaña de mutación (el cambio toca el alcance: RM1) y `bash
   harness/init.sh`; actualizar «Evidencias».

La pasada 2 será incremental desde `1bf221c`.

**Automejora** (propuesta, no aplicada): que `specs/SPECS.md` pida fijar el redondeo de
todo campo `Float` derivado por resta o acumulado; aquí lo cazó la revisión, no la spec.
