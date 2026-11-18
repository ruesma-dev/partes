Revisión de evidencias desde 0e0d2f8 (pasada 3, de evidencias): delta 0e0d2f8..ec915d2 (5edd220, ec915d2)

# F-032 · Review del reviewer: activar Sesame en producción (festivos por trabajador)

- **Pasada principal:** APPROVED en la pasada 2 (íntegra en `git show 0e0d2f8:progress/review_F-032.md`).
- **Veredicto de esta pasada: APPROVED, CONDICIONADO a que el humano acepte por escrito los 3
  equivalentes y los 11 «muertos fuera de la campaña»** (ver más abajo). Esa aceptación está
  **pendiente**: hasta que conste en `progress/` con su texto literal, F-032 **no pasa a `done`**
  (mismo criterio que en F-062). Si el humano rechaza alguno, vuelve al implementer.
- **Rigor:** `critico`, declarado en `features.json`. Exige mutación con uno por línea y el 60 %
  de los candidatos en [100, 300], semilla 20261030, cero supervivientes sin aceptar y RM1–RM7.

## Ejecución

- `ARNES_SIN_CACHE=1 bash harness/init.sh`: todas las suites en verde.
  - Raíz: 2517 passed / 48 skipped. sv1: 74. sv2: 422. sv3: 2586 / 2 skipped. sv4: 3890. sv5: 1628.
  - Cobertura: 95,9 % (592/617). CAPA E2E: N/A.
  - Único KO: `PUERTA TAMAÑO`, por este mismo informe a medio escribir (151 líneas).
- `bash harness/init.sh` tal cual, igual de verde salvo el tamaño (142); recortado: `ENTORNO LISTO`, exit 0.
- El delta solo toca tests y papeleo: `test_f032_campana.py` en sv3 (12 tests, 14 casos) y en sv4
  (1), más `mutacion_F-032.md` y `.json`, `impl` y `tasks.md`. No cambia ninguna línea de producción.

## Verificación independiente de la campaña

- **Recálculo puro** sobre HEAD (`harness.alcance`, `generar_mutantes`): 18 ficheros, 1438 líneas
  y 303 mutantes, iguales fichero a fichero; 185 candidatos y tope 111 (ceil(0,6 × 185), en
  [100, 300]); `seleccionar` con la semilla 20261030 da **exactamente** los 111 del `.json`.
- **El `.md` y el `.json` van commiteados juntos** (`5edd220`) y cuadran:
  78 muertos, 32 supervivientes y 1 indeterminado (111), con `sha` = `0e0d2f8…`, `fiable: true`.
  El log de la campaña (`--workers 3`) da los mismos totales.
- **Ficheros sin mutantes (4): prueba de control hecha.** Sin la exclusión de alcance salen 95,
  11, 8 y 11 mutantes. El cero es legítimo: el diff solo trae docstrings, comentarios, un `import`
  y un `setLevel`. Las cuatro declaraciones están completas.
- **Campaña no reejecutada: 8964 s según el informe.** Me quedo en el recálculo, RM1–RM7 y la
  reproducción de abajo.
- Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0; las seis líneas base están en verde.

## Supervivientes: reproducción en una copia desechable

Copia de HEAD (`git archive`) en mi scratchpad, con el árbol de trabajo intacto. Cada mutante sale
de la tupla exacta del `.json` y se corre con `sys.executable -m pytest`, sin y con él (RM4):

| Mutante | Test que cita el implementer | Sin / con mutante |
|---|---|---|
| sv3 `persist_parte_pipeline.py:297` `>0→>1` | `r8_una_sola_clave_sin_dato…` | 0 / 1 |
| sv3 `refresco_festivos.py:54` `days=6→7` | `r4_anos_de_la_semana_iso…` | 0 / 1 |
| sv3 `contrastar…:215` negación | `r30_cada_fila_del_markdown…` | 0 / 1 |
| sv3 `contrastar…:60` `2→3` | `r31_cada_fallo_sale_con_su_codigo` | 0 / 1 |
| sv3 `sqlalchemy_festivos_repository.py:45` `0→1` | `r11_leer_todas_cuenta…` | 0 / 1 |
| sv4 `festivos_guardados.py:55` veracidad | `r42_un_nombre_no_textual…` | 0 / 1 |
| sv4 `orm_models.py:692` `unique=False` | raíz `test_f032_contrato_festivos.py` | 0 / 1 |
| sv4 `orm_models.py:703` `nullable=True` | raíz `test_f032_contrato_festivos.py` | 0 / 1 |
| sv3 `orm_models.py:709` `String(41)` | raíz `test_f032_contrato_festivos.py` | 0 / 1 |
| sv3 `contrastar…:440` `__main__` (indeterminado) | `test_f032_contraste.py` | 0 / **3**, «no tests ran» |

Son 9 de los 29 «muertos» del implementer (6 de los 18 con test nuevo y 3 de los 11 de la raíz),
más el indeterminado. Los nueve caen. **RM4 sobre dos muertos de la campaña**, los dos que más
se parecían a un equivalente, también caen en la copia:
- sv4 `calendario_provider.py:88` (`ttl 60→61`): `1 failed`;
- sv3 `festivos_guardados.py:48` (`[:10]→[:11]`): `1 failed`.

**Indeterminado (`:440`):** importar el módulo ejecuta `sys.exit(main())` al recolectar y pytest
sale con 3. Lo acepto como **detectado**: la suite no arranca. Consta en la tabla «No muertos».

## Los 11 «muertos por la raíz»: hueco real del selector de la herramienta

`harness/mutacion.py::ejecutor_para` juzga un fichero de un servicio Python **solo con la suite
de ese servicio**; la raíz `tests/` solo juzga el código que no es de ningún servicio. Así, los
contratos transversales (`test_f032_contrato_festivos.py`: DDL, `nullable` y `UNIQUE` de las DOS
copias del ORM) y los guardianes de gemelos no juzgan nunca. Son falsos supervivientes, del lado
prudente. La justificación es correcta: reproducida en 3 de 11, y los otros 8 usan el mismo test.

## Equivalentes (RM5): opinión para el humano, NO aceptados

- **RM5, uno elegido por mí: `api/app.py:217`** (`calendario is not None` → `calendario`).
  `calendario` es `None`, `TablaCalendarioLaboral` o `JsonCalendarioLaboral`. Importados de verdad,
  ninguna clase de su MRO (`…, CalendarioLaboralPort, ABC, object`) define `__bool__` ni `__len__`,
  así que la veracidad es idéntica a `is not None` para todo valor posible. **Equivalente.**
- De paso miré los otros dos:
  - `api/app.py:87`: el MRO de `SqlAlchemyFestivosRepository` es solo `object`;
  - `contrastar…:353`: `Settings` de pydantic, sin `__bool__` ni `__len__`.
- **Recomiendo aceptar los 3**, y también los 11 de la raíz, que están muertos de verdad.

## Checkpoints C4 bis (los que quedaron pendientes en la principal)

- [x] **Mutación**: totales verificados de forma independiente; la regla del nivel cuadra.
  [x] **Supervivientes reproducidos a mano**: los de arriba y los del implementer.
- [x] **Muertos comprobados**: la campaña no se reejecuta (> 60 s), y hay RM4 sobre dos.
  [x] **Coste por mutante**: 8964 × 3 / 111 = 242 s. [x] Sin CAMPAÑA NO VÁLIDA ni base rota.
- [x] **RM1**: se midió `0e0d2f85…`. HEAD es `ec915d2`, pero el delta no toca ninguna línea de
  producción, y el recálculo sobre HEAD da el mismo alcance y la misma muestra.
- [x] **RM2**: media × W = 80,8 × 3 = 242 s, frente a líneas base de 1409 s (sv4) y 69–82 s (sv3).
  No hay salto de orden de magnitud. Con `-x`, los muertos de sv3 abortan pronto. Los 7
  supervivientes de sv4 (≈ 1400 s cada uno) explican la media de 134,7 s por juicio.
- [x] **RM3**: ningún equivalente sale muerto. Repasé los 78 muertos del log y ninguno es
  sospechoso. Los dos más dudosos los comprobé con RM4.
- [x] **RM5**: `api/app.py:217`, reproducido arriba.
- [x] **RM6**: N/A justificado: el delta no toca producción ni quita ninguna guarda.
- [x] **RM7**: hecho en la pasada 1. `persist_parte_pipeline.py` no ha cambiado desde entonces.
- [x] **Análisis de supervivientes completos**: los 32 tienen el suyo (ninguno en `PENDIENTE`), y
  18 están muertos con un test nuevo. **Los 3 equivalentes y los 11 de la raíz necesitan la
  aceptación escrita del humano antes de `done`**, como en F-046 y F-062. Esa es la condición del
  veredicto, y queda pendiente.
- [x] **«Evidencias»**: los cuatro números y la capa e2e. Los workers están en el informe, pero no
  en la tabla (ver «Observaciones»).
- [x] **C3 del delta**: los tests nuevos llevan la ruta en la primera línea, no tienen prints, usan
  datos sintéticos y no tocan red ni BBDD real (SQLite y `MockTransport`).
- **C5**: T27 en `[x]` con su commit (`5edd220`). Su verificación dice «cero supervivientes sin
  aceptar», y eso solo se cumple cuando el humano acepte.

## Cobertura: requisito → test

Sin cambios desde la pasada 2; `test_f032_campana.py` refuerza R4, R8, R11, R29–R31 y R42.

## Observaciones (no bloquean)

- La tabla «Evidencias» de `impl_F-032.md` debería llevar la fila «Workers: 3».
- `test_f032_campana.py` de sv3 importa fixtures y ayudantes de otros 4 módulos de test. Eso le
  cuesta 8 avisos de ruff: 7 F811 por los fixtures importados y 1 I001. Ruff pasa de 1063 a 1071.
  Si el patrón se repite, conviene mover esas piezas a `conftest.py`.

## Automejora (propuesta para `arnes-base`, no aplicada)

1. **Selector de `harness/mutacion.py`**: que el mutante de un fichero de servicio corra también
   los tests de la raíz que lo **referencian** (un `grep` de su ruta o su módulo en `tests/`), o una
   clave `suites_adicionales` en `servicios.json`; la raíz entera (1100–2000 s) no compensa. Hoy
   da falsos supervivientes en `critico`: 11 de 32 en F-032.
2. Que el informe distinga el **indeterminado por recolección abortada** (rc 2 o 3 con «no tests
   ran») y lo diga en su tabla. Ahora hay que deducirlo a mano.
