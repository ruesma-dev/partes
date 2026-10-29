<!-- progress/review_F-056.md -->
Revisión completa (pasada 1) · rama `feature/F-056-franquicia-de-extras`, HEAD e3dff2f, diff `dev...HEAD` (base 39aef7b)
# F-056 · Franquicia de extras — revisión
**Veredicto: APROBADO (APPROVED)**, con observaciones que no tocan el comportamiento (al final).
**Rigor** `critico` (declarado): fase RED, cobertura ≥ 80 %, mutación completa sin supervivientes sin
justificar (equivalentes aceptados por el humano), RM5 y verificaciones MANUAL listadas.

## Ejecución

- `bash harness/init.sh` → **ENTORNO LISTO**: raíz 529 passed, 3 skipped (199 s); PUERTA COBERTURA
  **[OK] 99,0 %** (1045/1056); PUERTA TAMAÑO **[OK]** (150/150, 250/250, 218/220).
- sv3, sv4 y sv5 salieron de caché; los lancé a mano sin caché (`python -m pytest -q -p
  no:cacheprovider` desde cada ruta): sv5 **1485 passed** (58 s), sv3 **2345 passed** (52 s), sv4
  **3220 passed, 1 skipped** (1506 s).
- `node --check static/app.js` OK. Árbol limpio.

## Mutación (C4 bis, RM1–RM6)

- **Recálculo puro** (`parsear_diff` + `filtrar_produccion` + `generar_mutantes` sobre `git show`).
  Principal, 39aef7b..06065ea: **2294 líneas, 513 mutantes**. Enmienda, 3ba3403..56b5ca3: **156
  líneas, 23 mutantes**. Las dos coinciden fichero a fichero.
- **Supervivientes**: los **102** casan uno a uno (fichero, línea, operador, original→mutado) con
  mutantes reales. Ninguno en `PENDIENTE`. Sin cabecera NO VÁLIDA; «Sin veredicto (base rota)» = 0.
  **Campañas no reejecutadas**: 57 637 s (≈ 16 h) y 273 s, por encima de 60 s; recálculo puro y RM1–RM6.
- **RM1**: 06065ea..9ae3fa5 solo trae el informe y tests. La enmienda (medida en 56b5ca3) cubre toda
  la producción posterior (T23, T24). e3dff2f solo añade su informe.
- **RM2** (4 workers): principal 513 × 112,4 ≈ 57 637, media × W = 450 s frente a bases de 820 s
  (sv4) y 44 s (sv5); enmienda 23 × 11,9 ≈ 273, media × W = 47,6 s frente a 37 s. Coherentes con
  `-x`. Coste por mutante > 1 s. **RM3**: ningún equivalente sale muerto.
- **RM4**: reproducido en una copia de sv4 en el scratchpad. #1 (`frozen=True→False`) da 1 failed,
  63 passed; #4 (`or→and`) da 1 failed, 64 passed; #3 (equivalente) da 80 passed, igual que sin
  mutante. Las tres filas son idénticas al informe.
- **RM5**: el **#95** (`x < 0`→`x <= 0` en `leer_valor`), ejecutado frente al original en 20 626
  entradas (0, −0.0, "0", Decimal("0E+3"), 200/200,01, NaN/inf, no numéricos, 20 000 aleatorios y
  los enteros −300..300): **0 diferencias**. Razoné además el #31: el único no informativo con
  motivo es NUEVO con calendario no fiable; `_propuesta` da None sin llamar a sv5 y `_item`
  antepone el motivo del candidato, así que la salida es idéntica.
- **RM6**: 88 + 2 se matan con tests nuevos, sin tocar producción. Las guardas que quitó T23
  (`CAMPO_RE`, tipo de columna) las sustituyen `COD_EXT_RE` y `motivo_definicion`.
- **Aceptación humana de los 14 equivalentes (2026-10-29)**. El líder los presentó agrupados:
  - #79, #90, #92: defecto de `getattr` que `Settings` siempre define;
  - #3, #10, #17, #80, #86, #87: `or 0`→`or 1` sin vacío posible o con el mismo resultado;
  - #84, #89, #95, #31: condición ya descartada antes;
  - #19: lote 500→501 sobre un `set`.

  Pregunta: «¿Aceptas los 14?». Literal del humano: **«si»**. Revisados contra el código, **los 14
  son equivalentes** (`Settings` y `SettingsFake` definen `est_parte_activo`, `paso_pos` y
  `obra_pruebas_forzar`; `recurso_fechas_de` acumula en `set`). Quedan cero supervivientes sin
  justificación aceptada.

## Puntos de especial cuidado

- **Sigrid solo por sv5**. `ejecutar` toma `self._reg.lock` (el del registro); `preparar` va fuera,
  y X y E se leen dentro. INSERT y UPDATE van por las sentencias de F-046 sin cambios (`WHERE`
  optimista). Después se relee por synckey y se decide por lo releído (R29). No hay ningún `DELETE`
  en el diff, y el fixture autouse `_grabar` de `test_f056_pipeline.py` lo comprueba en cada test
  (R26). A = 0 ⇒ `UPDATE` a 0.
- **«No se sabe» ≠ X = 0**. `veredicto` corta primero todo lo que no sea `activa` ni `inactiva` ⇒
  `no_editable`. Un recurso ausente o con 2 filas es `invalida`; un fallo de la definición o de los
  valores es `no_disponible`. NaN e inf se rechazan con `isfinite`.
- **R47 y R48**. `defext.tip = 33 AND cod = ?` y `con LEFT JOIN conext … WHERE con.tip = 33`,
  parametrizados y sin `dni`. X se lee por `p.recurso_ide`, el mismo `reside` que se escribe. Tests
  r47 (tip 42) y r48 (un DNI, dos empresas, X 8/20).
- **Límite de servicio**. `CLAUDE.md` intacto: la lista cerrada no crece. Las dos copias de
  `orm_models.py` son byte-idénticas (`cmp`). sv1, sv2 e `infra/` no se tocan. Los guardianes de
  raíz pasan a **ocho tablas** con columnas literales.
- **`_actor(request)`**: 18 → 20 (`decidir`, `aplicar`); el guardián F-017 está en verde.
- **R45/R46**. `decidir` reutiliza `_plan_franquicia` y `decidir_ajuste` (CAS, índice único, 409)
  sin llamar a sv5; la vista encadena decidir y aplicar.
- **Documentación**. `ARCHITECTURE.md` (semánticas 7 y 21), `partes-proyecto.md` (§5, §5.5 quater,
  variables) y `azure-apps/partes.md` (58bce5e y e32f089, locales) son coherentes con el código y
  no mencionan `CAMPO_RES`.
- **06065ea (F-019)**: solo el test (reloj controlado), sin producción. **C4 ter** N/A: no hay
  `harness/rutas_sensibles.json`.

## Checkpoints

- **C1** [x] `init.sh` en exit 0 · [x] existen los ficheros del arnés.
- **C2** [x] una sola feature `in_progress` · [x] rama correcta · [x] `current.md`: la sección de
  F-056 describe la sesión; el resto es historial de otras features, práctica previa del repositorio
  que no introduce F-056 · [x] `history.md` sin cambios necesarios.
- **C3** [x] hexagonal: el dominio no importa infraestructura, y el pipeline importa la synckey del
  cliente igual que `reajuste_pipeline` · [x] primera línea con la ruta en todos los ficheros nuevos
  · [x] sin `print`, sin secretos y sin dependencias nuevas · [x] trampas: recurso ≠ empleado (R48),
  `registro_de_synckey` ignora la synckey nueva, schema en dos copias iguales.
- **C3 bis** (se modificó `partes-proyecto.md`)
  - [x] N/A cabecera: el documento no es nuevo ni llega de fuera. [x] Sin originales:
    `git log --diff-filter=A` no trae ningún pdf, doc, xls ni ppt.
  - [x] Barrido mío sobre el diff de `docs/` y de `azure-apps`: **0 coincidencias** (correo, IPv4,
    GUID, `password|contraseña|secret=|AccountKey|SharedAccessSignature|sig=|token|api_key|Bearer|BEGIN|DefaultEndpointsProtocol`
    y base64 de 40 o más caracteres). [x] N/A redacción: no hubo nada que redactar.
- **C4** [x] trazabilidad completa (abajo), todo en verde · [x] sin red ni BBDD (`SigridFake`,
  SQLite, sv5 falso) · [x] M2–M4 con su receta en `design.md` §10, referenciada desde `current.md`
  y T21.
- **C4 bis** — todos [x]:
  - fase RED con trazas reales (T12–T17b y T23 en el informe; T1–T11 en 6d777c4 y dd197b7; T18 y
    T24 justificados);
  - cobertura 99 %; mutación recalculada; RM1, RM2, RM5 y RM6; sin base rota ni `PENDIENTE`;
  - «Evidencias» presente, aunque sin el nº de workers (obs. 2; el informe de mutación trae 4);
  - ningún N/A sin motivo.
- **C5** [x] tareas y commits `F-056 Tn:`. T21 y T22 quedan fuera por encargo del líder. T20
  (3ba3403, 9ae3fa5, más la aceptación de hoy) y T26 (e3dff2f) están **hechas**; solo les falta la
  casilla (obs. 1) · [x] sin artefactos sin trackear · [x] `features.json` en `in_progress`, su
  estado real.

## Cobertura requisito → test

334 tests `test_f056_*` (sv3, sv4, sv5 y raíz). Cada R de R2–R34 y R36–R48 tiene al menos un test
`test_f056_r<N>_…` (o `…_r<M>_r<N>_…`) y todos pasan; los recuentos van de 1 (R4, R46) a 24 (R15).
Ejemplos: R31 `r31_pisado_choques_ignora_el_ajuste`, R42 `r42_franquicia_desconocida_no_escribe`,
R47 `r47_el_cod_10_de_tip_42_nunca_da_x`, R48 `r48_mismo_dni_dos_empresas_usa_la_del_recurso_pedido`.
Sin nombre propio, pero cubiertos: **R1** (`r41_ejecutar_lee_x_bajo_el_lock_y_comprobar_sin_el`,
`r48_…`, contrato `r41_sv4_no_manda_la_x`) y **R26** (fixture autouse `_grabar` de
`test_f056_pipeline.py`: ninguna sentencia es un borrado). **R35** es documental (revisado arriba) y
**R37**, de proceso (este informe).

## Observaciones (no bloquean; se arreglan al cerrar)

1. Marcar `[x]` T20 y T26 en `specs/F-056-franquicia-de-extras/tasks.md`.
2. `progress/impl_F-056.md`, sección «Evidencias», fila Mutación: añadir «4 workers» y cambiar
   «pendientes del humano» por «aceptados por el humano el 2026-10-29 («si»)».
3. Quedan del humano M2, M3 y M4 (`design.md` §10) y T21 y T22. M2 se hace antes de activar
   `FRANQUICIA_CAMPO_EXT=10` en producción.
4. Docstrings que aún dicen «campo de `res`»: `orm_models.py:32-33` en sv4 y sv3 (las dos copias a
   la vez) y `services/partes-transfer/domain/models/registro_models.py:477-478`
   (`LecturaFranquicia`). Deben decir «campo extendido de recurso (`defext`/`conext`)».
5. `partes-proyecto.md` y `azure-apps/partes.md` dicen «`10` en producción». Hasta M4 la variable
   está vacía: mejor «`10` al activarla (M4)».
6. Caso límite, seguro pero mejorable. Si la persona tiene horas ordinarias con OTRO recurso (otra
   empresa) el día de ajuste, `lineas_trabajador_periodo` las incluye por DNI y `elegir_obra` (R7)
   podría escoger esa obra. sv5 lo para con F-023 (`no_editable`, R30), así que nunca se escribe
   mal, pero ese trabajador se queda sin ajuste. Para una feature futura: elegir la obra solo con
   las líneas del `recurso_ide` del ajuste.
7. R1 no tiene un test con su nombre; lo cubren r41, r48 y el contrato. Se puede renombrar uno a
   `r1_…` en una pasada futura.

**Automejora (propuesta para `reviewer.md`, RM4)**: lanzar pytest con `sys.executable` en los
subprocesos. En este equipo `python` resolvía a otro intérprete sin pytest, daba exit 1 y parecía un
falso «MATA». Lo detecté y repetí la prueba.
