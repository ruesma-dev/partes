<!-- progress/review_F-021.md -->
Revisión completa (pasada 1) · `3f672b6..a8e6823` (lo anterior es `dev`)

# F-021 · Review

**Veredicto: APPROVED.** Una observación NO bloqueante para el humano (O1,
premisa de DA7). M1–M4 siguen siendo MANUAL (humano).

**Rigor:** `critico` (declarado): RED, cobertura ≥ 80 %, mutación completa
con 0 supervivientes y MANUAL con comando exacto.

## Verificación ejecutada

- `bash harness/init.sh` tal cual: **exit 0**, «ENTORNO LISTO». Raíz 419
  passed / 1 skipped; sv1–sv5 verdes **por caché**; COBERTURA [OK] 100 %
  (75/75); TAMAÑO [OK].
- Suites relanzadas **sin caché**: sv5 **269 passed** (7,0 s); sv4 **1.230
  passed** (177,8 s, 0 skipped: los tests con `node` corrieron).
  `node --check app.js` OK. Árbol limpio.

## Lo que pidió el líder

1. **Centro y EMPRESA correctos.** `empresa = destino.empresa` (`con.emp` de
   la obra destino, F-023) y `cenide = obr.cenide` del mismo destino (en
   pruebas, la `0404`). `cuentas_de_centro` filtra `a.cenide = ? AND
   c.emp = ?`; de `reshor` solo se usa el TEXTO de la subcuenta, nunca su
   `ide`. Tests: `r4_la_cuenta_es_de_la_empresa_de_la_obra` (descarta la 709,
   mismo centro y subcuenta, empresa 28) y `modo_pruebas_usa_el_centro_…`.
   F-023 ya omite antes los recursos de otra empresa.
2. **Sin cuenta ⇒ 0 y aviso, sin bloquear**: R3 (sin aviso), R5 y R6 (con
   aviso) dan `caa_ide = 0` y la línea se escribe
   (`r8_sin_cuenta_la_linea_se_escribe_igual`). **Fallo de lectura ⇒ nada
   escrito**: llamada sin `try` en `preparar`, antes del lock y de cualquier
   `escribir` (`r11_fallo_al_leer_cuentas_no_escribe_nada`). `truncated` y
   HTTP ≥ 400 lanzan excepción (`r11_*` del cliente).
3. **Lo que no cambia**: el diff no toca `synckey_de`, el paso 6, F-024
   (borradas) ni `coherencia_recurso.py`. Tests: `r16_ya_registrada_no_se_
   reescribe…` y `r17` (clave de conflicto igual). Los JOIN nuevos de
   `horas_de_recursos` (`res`, `con`, por PK) no multiplican filas.
4. **Modal**: `avisosCuentaHtml` escapa nombre, fecha y aviso con `esc()`
   (test que ejecuta la función con `node`). Filtra `escribir`, sale de
   `pf.acciones` (preflight) y sin avisos devuelve `""` (R20).
5. **Límite de servicio**: solo sv5 y sv4 (`app.js`, sin Python). sv3, ORM,
   `reglas_registro`, `resultado_json`, `infra/` y `CLAUDE.md` intactos. La
   lista cerrada de duplicación no crece.
6. **Tests sin red ni BBDD**, datos sintéticos (`httpx.post` sustituido,
   `SigridFake`, SQLite en sv4). Sin secretos.

**D1–D5 y contraste T1: todos aceptados.** D2 sirve además de traza RED de
R14; D3 (infrastructure → application) apunta hacia dentro y tiene
precedente (`text_match`, `congelacion`); D4 mejora el modelo citado; D5 es
coherente con R18. El §0 del informe, verificado en el código.

## O1 · Observación no bloqueante (para el humano)

DA7 y el docstring de `_resolver_cuentas` (`registro_pipeline.py:210`) dicen
«la petición falla **y la cola reintenta**». **La cola no reintenta**:
`transfer_consumer.py` (l. 90-103) captura el fallo de negocio, publica
`ok=false` y sv4 marca las líneas en error hasta que alguien las reaprueba.
R11 (nada escrito) se cumple, igual que con `datos_recursos` (F-023); solo
es falsa la premisa del reintento automático. Propuesta: corregir el
docstring en un `F-021: ajuste` o en la próxima feature de sv5.

## Nivel de rigor (C4 bis)

- **RED**: trazas reales en T2, T5, T7, T8 y T10 para R1, R2, R4, R5, R6,
  R8, R11, R12, R14 y R16. La de R16 son los defaults de T4 más los mutantes
  del filtro: razonable, porque ya era el comportamiento previo.
- **Cobertura**: `[OK] 100.0%` de 75 líneas. `app.js` no lo mide la
  herramienta (solo Python); lo cubren 8 tests con `node`.
- **Mutación, recalculada a mano**: alcance (`alcance_de_feature`) 54 + 96 +
  13 + 46 + 6 = **215**; `generar_mutantes` = **33**. Las dos cifras
  coinciden con el informe. Revisé los 33: ninguno es equivalente (RM3 OK).
- **Reejecución**: el informe declara 82,4 s, por encima de 60 s. Aun así la
  **reejecuté entera**, por ser `critico` y barata: HEAD `a8e6823`, 4
  workers, salida en el scratchpad. Resultado: **33/33 muertos, 0
  supervivientes, 0 timeouts, 0 sin veredicto, 103,8 s**. `git status`
  limpio y sin worktrees colgados.
- **RM1**: midió en `fe3af66`; después solo cambian `progress/` y `tasks.md`,
  y mi reejecución sobre HEAD lo confirma.
- **RM2**: media × W = 2,5 × 6 = 15 s, frente a una línea base de 10,9 s
  (en la mía, 3,1 × 4 frente a 12 s). Coste por mutante ≈ 15 s (> 1 s).
- **RM5**: N/A, no hay ningún equivalente declarado.
- **RM6**: se **quitó** el `or 0` de `int(a.recurso_ide or 0)`. Invariante
  comprobado donde nace el dato: las tres ramas `accion="escribir"` de
  `reglas_registro.py` van tras `if not linea.recurso_ide: return omitir`, y
  `_evaluar` nunca convierte nada en `escribir`. El `INSERT` ya usaba
  `int(a.recurso_ide)` sin guarda. Si se rompiera, `int(None)` lanza en
  `preparar` sin escribir nada. Aceptado.
- Sin «CAMPAÑA NO VÁLIDA»; «Sin veredicto» = 0; «Evidencias» con workers (6).

## Checkpoints

- C1 [x] init.sh exit 0 · [x] ficheros base presentes.
- C2 [x] una sola `in_progress` · [x] rama de la feature · [x] `current.md`:
  F-021 activa. F-024 se queda como pendiente MANUAL vivo; la historia larga
  es deuda previa del líder, como ya se aceptó en las reviews de F-023 y
  F-024 · [x] toda `done` está en `history.md`.
- C3 [x] hexagonal (el dominio solo gana campos; regla pura en application;
  SQL en infrastructure) · [x] ruta en la primera línea de los 5 ficheros
  nuevos · [x] sin `print`, TODO, secretos ni dependencias nuevas · [x]
  trampas: `reside` sigue siendo el recurso; incidencias con `can=0` y
  CI*/CIZ con la cuenta del tipo por defecto; ORM intacto.
- C3 bis (modifica `docs/referencia/partes-proyecto.md`, paso 3b):
  [x] cabecera: N/A, el documento ya existía · [x] ni PDF ni ofimática
  (`git log --diff-filter=A`) · [x] barrido de las líneas añadidas (correo,
  IPv4, GUID, `password|secret|token|key=|Bearer|sig=|AccountKey`, base64 de
  32 caracteres o más, DNI `\d{8}[A-Z]`): **0 coincidencias** ·
  [x] redacciones: N/A.
- C4 [x] trazabilidad (tabla abajo), en verde · [x] sin red ni BBDD ·
  [x] M1–M4 en `current.md` con su SQL exacto.
- C4 bis [x] rigor · [x] RED · [x] cobertura · [x] mutación verificada ·
  [x] muertos comprobados (reejecución) · [x] coste por mutante · [x] sin «no
  válida» · [x] RM1 · [x] RM2 · [x] RM5 N/A (sin equivalentes) · [x] RM6 ·
  [x] campaña manual N/A (la automática dio 33) · [x] 0 supervivientes ·
  [x] «Evidencias» · [x] ningún N/A sin motivo.
- C4 ter N/A: no existe `harness/rutas_sensibles.json`.
- C5 [x] T1–T16 `[x]`, con sus commits `F-021 Tn:` · [x] árbol limpio ·
  [x] `features.json` `in_progress` (el `done` lo pone el líder).

## Cobertura requisito → test

| Req. | Test(s) |
|---|---|
| R1–R3 | `test_f021_r1_*`, `r2_*`, `r3_*` (pura); `r13_el_preflight_trae…` (ids 4 y 7) |
| R4 | `test_f021_r4_*`; `r4_la_cuenta_es_de_la_empresa_de_la_obra` |
| R5 / R6 / R7 | `test_f021_r5_*` (pura y sin centro) / `r6_varias_candidatas…` / `r7_otra_fila…` |
| R8 | `r8_toda_linea_sin_cuenta…`, `r8_sin_cuenta_la_linea_se_escribe_igual`, `r8_r14_…cero` |
| R9–R11 | `test_f021_r9_*`, `r10_*`, `r11_*` (cliente y pipeline) |
| R12–R15 | `test_f021_r12_*` (incluye fuera del lock), `r13_*`, `r14_*`, `r14_r15_insert…` |
| R16–R18 | `r16_ya_registrada…`, `r12_se_resuelve…` (omitir 0), `r17_al_pisar…`, `r18_log…` |
| R19–R21 | `test_f021_r19_*` (5), `r20_*` (5), `r21_el_preflight_reenvia…` |
| R22–R23 | Sin código: `test_f004_r11_*`/`r18_*` siguen en verde; nada en sv3 ni en el ORM |
| R24 | Lectura: ARCHITECTURE punto 13, partes-proyecto §3b y azure-apps `2fd1e92` (sin push) |

**Cambios requeridos:** ninguno. O1 queda a decisión del humano.

**Automejora (propuesta, no aplicada):** en `reviewer.md`, una suite
«(caché: …)» de `init.sh` no cuenta como ejecución; se relanza sin caché.
