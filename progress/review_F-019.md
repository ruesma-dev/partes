<!-- progress/review_F-019.md -->
Revisión completa (pasada 1) · `git diff dev...HEAD` (merge-base `b9b3b81`, HEAD `e0fa83e`)

# F-019 · Mensuales a dedicación — Review

**Veredicto: APPROVED** (D3–D5 a decisión del humano, §4; ninguna bloquea).
**Rigor:** `critico` (declarado): RED, cobertura ≥ 80 %, mutación 0 superv., MANUAL.

## 1. Lo innegociable (código, tests y copia aislada)
- **Apagado = hoy.** `_decidir_mensual` devuelve `None` en su primera
  línea. Apagado, el paso 6 consulta las mismas synckeys en el mismo orden.
  **Comprobación propia**: el `ReglasRegistro` de `dev` contra el de HEAD
  apagado, `AccionLinea` completo, 730 líneas (el producto de R3 bis y
  los casos de R1, con y sin omisiones): **0 diferencias**.
- **R1**: los tests de T1 `4783e62` dan 26 passed contra `dev` (en una
  copia) y sus líneas 1–154 no cambian en HEAD. **R3 bis**: 16 fichas
  (M/HE/HL/CI) × 20 líneas + sin recurso; solo admite `omitir→dedicacion`
  e incidencia `escribir→dedicacion`, y exige que los dos aparezcan.
- **Roturas deliberadas** en el scratchpad (`git archive`, árbol real
  intacto), fallos que da sv5: B1 sin guarda R3, extras M+HE a dedicación
  9 · B2 sin interruptor 22 · B3 `dedicacion`→`escribir` 27 · B4 `M*`+`HL*`
  5 · B5 guarda R3 invertida 9 · B6 R0 antes de la omisión 1 · B7 sin
  guarda tipo/horas 3 · B8 intermedio fuera 2 · B9 el pipeline escribe
  `dedicacion` 7 · B10 sin R5 1 · B11 M+HL+HE a dedicación 2. **11 de 11.**
- **Ninguna ruta escribe `dedicacion` en Sigrid.** En sv5 los pasos 4b, 5,
  7, 8 y 9 filtran `== "escribir"`, y lo vigilan R6 y B9. sv4 no escribe
  en Sigrid. El único efecto nuevo es R5, aprobado en la spec: una
  `dedicacion` cuya synckey ya está en Sigrid sale `ya_registrado`, sin
  escribir nada.

## 2. sv4, sv3, SQL y docs

- **Transacción (R9/R14).** Una sola sesión con un solo `commit`.
  `r14` borra la tabla y comprueba que no se marca nada, ni siquiera las
  `escritas` del mismo resultado. Por HTTP, `_trazar` se traga el fallo,
  como ya hacía con cualquier fallo de la traza; el rollback se mantiene y
  la línea queda reaprobable.
- **Versiones.** R12 el mismo contenido no toca la fila · R13 otro o
  retirada `+1` · R21 retirar: `vigente=false`, `+1`, autor · R23 reaprobar:
  v3 vigente · retirar dos veces: `no_aplica`. **Congelación**: sv4
  (línea, documento, `vive_fuera`) y sv3; las compara el guardián F-024.
- **Duplicación.** `orm_models.py` byte-idéntico (`cmp` OK). No hay
  ninguna copia nueva: `M*` solo en sv5, la clase de incidencia solo en
  sv4. *Observación*: la pareja de congelación sv3/sv4 (de F-004/F-024,
  vigilada por un test de raíz) **no figura** en la lista cerrada de
  `CLAUDE.md`, aunque el design §1 dice lo contrario. No es nueva: que el
  humano decida si la añade.
- **`01_dedicacion_lectura.sql`.** `ON_ERROR_STOP` y tres `GRANT`
  idempotentes, todos dentro de la base `partes`: CONNECT, USAGE en
  `public` y SELECT solo sobre la bandeja. Nada de servidor (ni roles, ni
  `ALTER SYSTEM`, ni extensiones, ni `REVOKE`), sin host ni credenciales
  reales. Las comprobaciones son lecturas. Su test estático se prueba
  contra copias alteradas. R27: ningún servicio ejecuta `GRANT`.
- **Sin nombres, DNIs ni secretos.** La bandeja no tiene columnas de
  persona (`r10`); los tests usan «Persona N» y DNIs sintéticos. Barrido
  del diff de docs/infra/progress/specs (correo, IPv4, GUID,
  password|secret|token|AccountKey|SharedAccess|sig=|Bearer, `\d{8}[A-Z]`):
  solo `secretref`, que es benigno. **Docs**: ARCHITECTURE con la sem. 15
  y seis tablas; partes-proyecto §3.5 y §5; `azure-apps` `c7ad8e9` con
  §4.5 bis, §5.6 y «qué se rompe», sin push.

## 3. Mutación (RM1–RM6)

- **Recálculo puro** (`alcance_de_feature` `b9b3b81..47c0b64` y
  `generar_mutantes`): **581 líneas y 126 mutantes**, igual que el
  informe, fichero a fichero. **Campaña no reejecutada**: 6794,5 s según el
  informe (unos 113 min), por encima de los 60 s.
- **RM1.** `47c0b64..HEAD`: un test, `progress/` y `tasks.md`; sin producción.
- **RM2.** 53,9 s × 6 workers = 323 s por mutante. Líneas base: sv4
  1082–1091 s, sv3 unos 30, sv5 25–30, con 79/23/24 mutantes. Con la suite
  entera serían unos 14.600 s de reloj; 6.794 encaja con `-x`.
- **RM3.** Ninguno de los 30 mutantes de sv5, congelación, reparto y
  `resultado_sigrid` es equivalente. **RM5** N/A: no se declaran
  equivalentes. **RM6** N/A: no se quitó ninguna guarda.
- **Superviviente** `app.py:2329` (`include_in_schema` False→True): coincide
  con el generado (mismo operador y texto). En la copia, el test nuevo da
  1 passed con el original y **1 failed** con el mutante. Ni «NO VÁLIDA»
  ni «sin veredicto».

## 4. Desviaciones D1–D8 (mi criterio)

- **D1** (M+HL+HE: manda R3 bis): **correcta**, es el innegociable y
  tiene test (B11). **D2** (`resumen.dedicacion` solo si > 0): aceptable,
  apagado el contrato de F-002 queda idéntico.
- **D3** (`dedicacion` fuera de `ESTADOS_CONGELANTES`). **Aceptable**:
  ningún código de producción usa la tupla (grep); la congelación real va
  por `motivo_congelacion_*` y `vive_fuera`, y la compara F-024. Coste: una
  constante con nombre engañoso, avisado en un comentario. Recomiendo, en
  esta feature o en otra, meterla en la tupla y actualizar las dos
  aserciones de F-004/F-024.
- **D4** (`_actor(request)` pasa de 14 a 15). **Aceptable**: el guardián
  existe para que todo punto de escritura nuevo use el helper; subir el
  contador con la llamada nueva es su mantenimiento, no una relajación.
- **D5** (un `.sql` en lista blanca en F-017). **Aceptable**: va por ruta
  exacta, no hace DML (el test prohíbe INSERT/UPDATE/DELETE/DROP) y
  cualquier otro `.sql` sigue fallando. El fin del guardián (que no haya
  migraciones que reescriban la historia) se mantiene.
- **D6** (sin agregar en varias obras): cosmético, la bandeja va por grupo.
  **D7** (tests sv3): bien. **D8** (`recurso_ide` del resultado): más fiel.

## 5. Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base. **C2** [x] 1
  `in_progress` · [x] rama · [x] `current.md` con F-019 arriba (lo demás
  son MANUAL pendientes, criterio de F-025/F-028) · [x] history.
- **C3** [x] hexagonal (`es_mensual` en el dominio, regla en application,
  bandeja en infrastructure) · [x] primera línea con ruta · [x] sin
  `print`, TODO, secretos ni dependencias nuevas · [x] trampas: recurso ≠
  empleado (`recurso_ide`), incidencias intactas apagado, ORM gemelo a seis
  tablas.
- **C3 bis** [x] solo se modificó un documento propio · [x] sin
  PDF/ofimática (`git log --diff-filter=A`) · [x] barrido hecho por mí ·
  N/A redacciones: no hubo ninguna.
- **C4** [x] trazabilidad (abajo), todo verde · [x] sin red ni BBDD ·
  [x] T16–T18 (M0–M3) con su comando en `current.md`.
- **C4 bis** [x] rigor · [x] RED real de los 16 requisitos de §H · [x]
  cobertura 100 % (201/201) · [x] mutación recalculada · [x] más de 60 s,
  no reejecutada (dicho) · [x] 323 s/mutante, muy por encima de 1 s · [x]
  sin «NO VÁLIDA» · [x] RM1 · [x] RM2 · N/A RM5 y RM6 (§3) · N/A campaña
  manual: no la hubo · [x] superviviente cerrado con un test · [x]
  «Evidencias» con 6 workers.
- **tasks.md**: T1–T15 y T19 `[x]` con commits `F-019 Tn:`; T16–T18 MANUAL.

**Tests** (los lancé yo, sin caché): raíz 445 passed y 1 skipped, sv5 357,
sv3 654, sv4 1636.
R1–R4 y R3 bis → `test_f019_reglas.py` · R5–R8 → `test_f019_pipeline.py` ·
R9–R14 → `test_f019_bandeja.py` · R15–R24 → `test_f019_portal.py`, sv3
`test_f019_congelado.py` y el guardián F-024 · R25–R27 →
`tests/test_f019_sql_lectura.py` · R29 → guardianes F-010/F-015 y `r29_*` ·
R28 sin test propio: sv1/sv2 sin diff, `test_f002_r11_sin_postgresql`,
`r3bis_nada_de_un_recurso_sin_m` y la comparación dev/HEAD · R30 y R31
leídos por mí.

## Cambios requeridos

Ninguno. Pendiente del humano: aceptar D3–D5 y, si quiere, añadir la
congelación sv3/sv4 a la lista cerrada de `CLAUDE.md`.

**Automejora (propuesta, no aplicada):** `init.sh` dio sv1–sv5 por buenas
desde caché; en `critico`, que `reviewer.md` pida relanzarlas sin caché.
