<!-- progress/review_F-033.md -->
Revisión completa (pasada 1): `git diff dev...4336034` (rama `feature/F-033-columna-empresa`)

# F-033 · Review

**Veredicto: APPROVED**

**Rigor:** `estandar` (declarado en `features.json`): fase RED en los requisitos
centrales, cobertura de lo cambiado ≥ 80 % y campaña de mutación con los
supervivientes analizados. RM5 N/A por nivel.

## Qué se ejecutó (resultado real)

- `bash harness/init.sh` tal cual: **ENTORNO LISTO**, exit 0. Raíz 445 passed,
  1 skipped; sv1–sv5 en verde (caché); **PUERTA COBERTURA [OK] 100,0 % de 32
  líneas (32/32)**; PUERTA TAMAÑO OK. Avisos previos, no de F-033: F-032
  `blocked`, ruff 610 (deuda), infra sin tests.
- Como sv4 salió por caché, suite sv4 **sin caché** (`-p no:cacheprovider`):
  **1683 passed** en 126 s (1672 previos + 11 nuevos).
- **Fase RED reproducida por mí**: copia `git archive 381c872` (antes de T1) en
  el scratchpad con el test final de F-033: **9 failed, 2 passed** (fallan
  R1–R7; pasan R8 y el parseo, que fijan lo que no debe cambiar). Coincide
  con las dos trazas del informe (§4).
- **Mutación, recálculo puro**: `alcance_de_feature("F-033")` = 83 líneas
  (52 en `empresas.py`, 31 en `parte_repository.py`); `generar_mutantes` = 12.
  Coinciden con el informe. Los 2 supervivientes existen tal cual
  (`entero`, l. 1028, `10**9`→`11**9` y `10**9`→`10**10`).
- **Campaña no reejecutada entera: 1295,7 s según el informe** (> 60 s). En su
  lugar, **RM4 sobre los 12**: cada mutante aplicado en una copia `git archive
  HEAD` del scratchpad contra `test_f033_columna_empresa.py`: **10 caen**
  (entre 1 y 7 fallos cada uno) y **2 sobreviven**, exactamente los
  declarados. Copias borradas; `git status` limpio.

## Alcance pedido por el humano

- Solo columna «Empresa» con filtro en `/obras` de sv4: [x]. Plantilla con
  `<th>Empresa</th>` tras «Obra», filtro en la misma posición, celda
  `{{ o.empresa_texto }}`. El filtro es el genérico `wireColumnFilters` (por
  `cellIndex`): no hay índices fijos en `app.js` que se desplacen.
- Dato de `parte_documents.empresa` con respaldo por recurso dentro de la BBDD
  `partes`: [x], sobre las mismas líneas que `list_obras` ya cargaba (join
  interno con el documento, así que `reg.document` nunca es `None`).
- Nombres `{1: "Ruesma", 28: "Porsan"}`, si no «Empresa N»: [x].
- Ni Sigrid, ni ficheros de configuración, ni schema: [x].
- Ficheros fuera de `services/partes-front/`, `specs/`, `progress/`,
  `harness/`: solo `BACKLOG.md`, generado por `harness/backlog.py` desde
  `features.json` (no editable a mano). Aceptable.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base presentes.
- **C2** [x] una sola `in_progress` (F-033; la otra coincidencia de la cadena
  es la lista de estados válidos, l. 11) · [x] rama
  `feature/F-033-columna-empresa` · [x] `current.md` con F-033 arriba; la
  sección de F-032 es una feature `blocked` vigente · [x] las `done` tienen su
  resumen en `history.md` (el de F-033 lo mueve el líder al cerrar, ver O2).
- **C3** [x] hexagonal: regla pura en `application/services/empresas.py` sin
  dependencias; el repositorio (infraestructura) la consume; la plantilla es
  adaptador web · [x] primera línea con ruta en `empresas.py` y en el test
  (`obras_list.html` no la llevaba antes: deuda previa, no introducida) ·
  [x] sin prints, TODOs, secretos ni dependencias nuevas · [x] trampas:
  usa `recurso_ide` (no empleado) para el respaldo; no toca incidencias ni
  `orm_models.py`; la lista cerrada de duplicación no crece.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] cada R1–R8 con test `test_f033_rN_*`, todos verdes (tabla abajo)
  · [x] sin red ni BBDD real: SQLite en memoria (`FabricaSesionSqlite`) y
  `TestClient` · N/A MANUAL: la spec no declara verificaciones `MANUAL
  (humano)` (rigor `estandar`); la comprobación visual tras desplegar del
  informe §7 es recomendación, ver O2.
- **C4 bis**
  - [x] `rigor` declarado: `estandar`.
  - [x] **Fase RED**: trazas reales en el informe (§4) para R2, R4–R7 (T1) y
    R1, R3 (T2), y reproducidas por mí (arriba).
  - [x] **Cobertura**: `[OK]` 100,0 % (32/32).
  - [x] **Mutación**: `progress/mutacion_F-033.md` generado por la
    herramienta; totales verificados de forma independiente (83 líneas, 12).
  - [x] **Muertos comprobados**: campaña > 60 s, no reejecutada entera; sí
    RM4 sobre los 12 mutantes (10 muertos y 2 vivos, idéntico al informe).
  - [x] **Coste por mutante**: 1295,7 × 6 ÷ 12 = 648 s, muy por encima de 1 s.
  - [x] Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0; línea
    base medida en los 6 workers (302–305 s).
  - [x] **RM1**: SHA medido `ea0ba9e…` ≠ HEAD `4336034`. Desde entonces solo
    cambian el test (anotaciones `X | None` para ruff), `progress/` y
    `tasks.md`: ningún fichero del alcance. La campaña vale.
  - [x] **RM2**: media 108,0 s × 6 workers = 648 s frente a línea base ~303 s:
    sin salto de orden de magnitud; `12 × 108,0 = 1296` cuadra con el total.
  - [x] **RM3** (criterio): ningún muerto es equivalente; los 10 cambian
    resultados observables (nombres, orden, respaldo por recurso).
  - N/A **RM5**: rigor `estandar`; basta la justificación escrita, que existe.
  - [x] **RM6**: no se quitó ninguna guarda defensiva.
  - N/A campaña MANUAL: hubo campaña automática con 12 mutantes.
  - [x] Supervivientes con análisis completado (ninguno en `PENDIENTE`).
  - [x] «Evidencias» con tests, cobertura, mutantes/supervivientes, tiempos
    de la suite y 6 workers.
  - [x] Ningún N/A sin motivo escrito.
- **C4 ter** N/A: la puerta de `init.sh` no señaló rutas sensibles.
- **C5** [x] `tasks.md` T1–T4 `[x]`, un commit `F-033 Tn:` por tarea (más dos
  ajustes `F-033:`) · [x] sin temporales ni ficheros sin trackear ·
  [x] `features.json`: paso a `done` con este veredicto (ver O1).

## Cobertura requisito → test

| R | Test(s) |
|---|---|
| R1 | `test_f033_r1_columna_y_filtro_alineados` |
| R2 | `test_f033_r2_varias_empresas_unidas`, `test_f033_r2_texto_empresas_puro` |
| R3 | `test_f033_r3_gemelas_dos_filas_ruesma_porsan` |
| R4 | `test_f033_r4_partes_null_usa_empresa_del_recurso`, `test_f033_r4_empresas_de_fila_puro` |
| R5 | `test_f033_r5_sin_empresa_guion` |
| R6 | `test_f033_r6_numero_desconocido_empresa_n` |
| R7 | `test_f033_r7_orden_gemelas` |
| R8 | `test_f033_r8_obra_key_y_totales_intactos` + suite sv4 entera (1683) |

## Supervivientes (equivalentes aceptados)

`10**9`→`11**9` y `10**9`→`10**10` en la tercera clave de orden: cualquier
centinela mayor que los números de empresa reales da el mismo orden. Matiz sin
consecuencia: el análisis dice «para toda entrada posible», pero la columna
`empresa` es `Integer` (hasta 2^31−1 > 10**9); en Sigrid los códigos de
empresa son pequeños, así que la equivalencia es práctica, no del tipo. No
exige cambio.

## Observaciones (no bloquean)

- **O1.** El `title` y la `description` de F-033 en `features.json` siguen
  describiendo el alcance inicial rechazado («en las vistas de obra», detalle,
  borrado, demás vistas). La spec vigente es la mínima. Propongo al líder
  alinearlos al cerrar (no lo hago yo: el reviewer solo cambia el estado).
- **O2.** Al mover F-033 a `history.md`, el líder debería anotar la
  comprobación tras desplegar del informe §7 (abrir `/obras`, ver la 0678 en
  dos filas «Ruesma» / «Porsan», probar «Filtrar empresa…») como verificación
  pendiente del humano, como se hizo con F-025 y F-029.

## Cambios requeridos

Ninguno.

## Automejora (propuesta, no aplicada)

- `CHECKPOINTS.md` C2: aclarar que se cuenta el campo `status`, no la cadena `in_progress`.
