<!-- progress/review_F-062.md -->
Revisión completa (pasada 1) · `git diff a82f9c6...aad629c` (merge-base con `dev` .. HEAD de la rama)

# Review F-062 · CI* con su CIZ hermano el mismo día del inicio

**Veredicto: CHANGES_REQUESTED** (RECHAZADO, pasada 1 de 2). El código cumple la spec. Lo que
falla es el papeleo de la mutación (RM5) y que se ha roto una demostración de F-060 que estaba
versionada. Son tres cambios y ninguno toca producción.

**Nivel de rigor: `critico`** (declarado en `features.json`). Exige C1–C5, C3 bis y C4 bis con
fase RED, cobertura ≥ 80 % y mutación con cero supervivientes salvo los que acepte el humano.
Exige también RM1–RM6 (RM5 incluido, por ser `critico`) y las verificaciones MANUAL en
`current.md` con su comando exacto.

## Ejecución

- `bash harness/init.sh` tal cual: exit 0, `ENTORNO LISTO`. Raíz: 522 passed y 3 skipped.
  `PUERTA COBERTURA` [OK]: 100,0 % (135/135, umbral 80 %). `PUERTA TAMAÑO` [OK] (impl 218/220).
  Las suites de servicio salieron de la caché («árbol sin cambios»), así que las relancé sin caché:
  **sv5 1164 passed** y **sv4 2791 passed, 1 skipped** (486 s).
- Desde el SHA medido (37fca60) solo han cambiado tests y papeleo
  (`git diff --stat 37fca60..HEAD`). Ningún fichero del alcance se ha movido.

## Las 8 desviaciones del implementer

Las 8 aceptadas. (1) R7 da WARNING con `registro_id` en vez del INFO de R16: más nivel, mismo
dato, DA9. (2) El preflight filtra `fin_mismo_dia` (`app.py:221`): R17. (3) `_omitir` limpia el
hermano: R10. (4) Sin fecha no hay `LineaRol`. (5) Comprobada: en el paso 7, `es_incidencia ⇒
incidencia_en_sigrid`; nunca hay conflicto confirmable, y por eso el `INSERT` doble no necesita
`pisadas` (O2). (6) R11 no pide el estado del parte; la guarda del `INSERT` cubre el del CI*.
(7) R19 y DA4: `registro_de_synckey(':ciz')` da None; log `synckey=a->b`. (8) Los tres asertos
de F-060 llevan «F-062 (R18) enmienda R13».

## Comprobaciones de fondo

- **SQL (R13, R14)**, frente a `stmt_insert_linea`: mismas columnas, `ide` = `x.n + v.k` con
  `UPDLOCK, HOLDLOCK`, guarda F-034 en las dos filas, `NOT EXISTS` solo en `k = 1`. El test fija
  el texto exacto y los 22 parámetros en orden. Ningún `DELETE`.
- **sv4**: `racha_delante` cumple R1 (corta en el primer día que no es de la clave; papelera en
  (D, último]) e `inicios_con_ciz` cumple R2 (persona + clave + id, también con el `fin` en otra
  obra). `decidir`, `colapsar`, `aviso_desordenada` y `_rol_incidencia_anterior` sin diff (R5);
  apagado, `set()` (R4).
- **sv5**: una sola `lineas_de_racha` para fines e inicios (R11, R18); R10, R12, R15 y R19 en
  `_omitir`, `_ciz_ajeno`, `_confirmar_hermano` y `_log_ciz_movido`. El contrato solo crece y no
  hay esquema nuevo. Ninguna copia de la lista cerrada tocada; lo nuevo no tiene gemela.
- **Trazabilidad**: R1–R26 con `test_f062_rN_*` (181 tests nuevos). R27, documentación revisada
  contra §10 (+ `azure-apps` a9d3b5b, local). R28, MANUAL en `current.md`.

## Mutación (C4 bis, RM1–RM6)

- **Recálculo puro e independiente** (`harness.alcance` y `generar_mutantes`): 10 ficheros,
  **425 líneas, 84 mutantes**. Coincide con el informe. Los 9 supervivientes existen como
  mutantes reales, con el mismo operador y el mismo texto original→mutado.
- **Campaña no reejecutada**: según el informe tardó 4185 s (70 min). Me quedo en el recálculo
  puro más RM1–RM6.
- **RM1** [x] SHA medido 37fca60; el delta posterior no toca el alcance. **RM2** [x]
  84 × 49,8 ≈ 4185 s; media × 4 workers = 199 s/mutante frente a bases de ~578 s (sv4) y ~20 s
  (sv5): coherente, > 1 s. Sin «⚠ CAMPAÑA NO VÁLIDA», 0 «sin veredicto».
- **RM3** [x]. Ningún equivalente sale muerto. Los hermanos `and 0` de las líneas 262, 533 y 547
  sí cambian el comportamiento, así que es legítimo que mueran.
- **RM4**, sobre una copia de sv5 en el scratchpad y sin tocar el árbol. Apliqué los **6 huecos**
  (335, 344, 586, 817, `racha_ciz:102` y `sigrid_write_client:665`, este último con sus dos
  mutantes `entero`). Cada test nuevo **falla con el mutante y pasa sin él**: 6 de 6.
- **Los 3 equivalentes: el razonamiento es correcto en los tres.**
  - **#1** (`racha_incidencia.py:262`, `or 0→or 1`). La demostración es aún más fuerte que la
    del implementer. `viaja` solo corre si el tramo no está vacío, y para eso `hasta_delante(d)`
    tiene que haber construido un `date`, lo que obliga a d ≥ 10101. Así, 0 y 1 quedan fuera
    tanto de `tramo` como de `d < f`. **Lo reproduje yo** con un diferencial del original frente
    al mutante: 200.000 llamadas y 84.946 históricos con fechas `None`, 0 o 1, con resultado
    **0 distintos**. Como control, el mutante `and 0` de la misma línea sí se distingue (falla).
  - **#4 y #5** (`registro_pipeline.py:533` y `:547`). Toda acción `escribir` sale de una rama de
    `ReglasRegistro` que antes omite la línea sin recurso (`reglas_registro.py:154` y `:232`).
    `recurso_ide` solo se reasigna en el paso 2b, que va antes de las reglas (l.259), y el paso 4b
    ya hace `int(a.recurso_ide)` sin `or`. Por tanto, el operando nunca se evalúa.
    **#5 es literalmente el mutante #11 de F-060**: mismo texto, mismo operador y misma
    expresión. El humano ya lo aceptó el 2026-10-24 («acepto») y F-062 solo partió la línea. #4
    es el mismo argumento aplicado a la línea gemela de los `inicio`.
- **RM5** [ ]. Los tres equivalentes traen solo justificación escrita, sin demostración
  ejecutable versionada. Con rigor `critico` eso es un `[ ]`, igual que en la pasada 1 de F-060.
  Mi reproducción del #1 no la sustituye.
- **RM6** [x]. No se ha quitado ninguna guarda: se añadieron 6 tests y la producción quedó igual.
- **Cero supervivientes salvo aceptación del humano** [ ]. Los equivalentes 1, 4 y 5 están
  **pendientes de aceptación**. No los doy por aceptados: eso lo decide el humano.

## Checkpoints

- **C1** [x] `init.sh` exit 0 · [x] ficheros del arnés.
- **C2** [x] Solo F-062 está en `in_progress` · [x] la rama es la de la feature · [x]
  `current.md` lleva la sesión activa. Los bloques de F-063, F-058 y F-060 que siguen ahí son de
  features `done` con verificaciones manuales pendientes, que es la práctica del repositorio · [x]
  `history.md`: no aplica, porque la feature aún no está `done`.
- **C3** [x] Hexagonal: el dominio no importa infraestructura. Hay una salvedad, la obs. O1 · [x]
  primera línea con la ruta en los 3 tests nuevos · [x] sin `print`, TODOs, secretos ni
  dependencias nuevas · [x] las trampas: el recurso viaja en `reside`, las incidencias van con
  `can` 0 y sin días intermedios, y no cambia el esquema.
- **C3 bis** [x]. Aplica porque se toca `docs/referencia/partes-proyecto.md`: es una sección
  propia, no un documento nuevo, así que la cabecera no aplica. No hay PDF ni ofimática
  (`git log --diff-filter=A`). Barrido sobre el diff entero: correo, IPv4, GUID,
  `password|secret|token|apikey|AccountKey|SharedAccessSignature|x-functions-key` y DNI. Solo
  sale `$KEY` como variable, nunca un valor. Nada que redactar.
- **C4** [x] trazabilidad, todo en verde · [x] sin red ni BBDD (`SigridFake` y SQLite) · [x]
  M1–M6 con su comando exacto en `current.md`. M0 está hecha.
- **C4 bis** [x] rigor declarado · [x] fase RED con trazas reales de T1–T10 · [x] cobertura [OK]
  · [x] mutación recalculada · [x] muertos: «no reejecutada» lo digo arriba · [x] tiempo · [x]
  sin cabecera de campaña no válida · [x] RM1 · [x] RM2 · **[ ] RM5** · [x] RM6 · N/A campaña
  manual: no la hubo · [x] análisis completos, sin `PENDIENTE` · **[ ] aceptación del humano** ·
  **[ ] «Evidencias» sin el nº de workers** (el informe de mutación dice 4).
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] Hay un commit `F-062 Tn:` por tarea. **T13 sigue `[ ]` y está justificado**: es
  MANUAL del humano después del merge, por diseño (§9). Este N/A lo justifico aquí · [x] sin
  ficheros temporales · [x] `features.json` está en `in_progress`.

## Cambios requeridos

1. **RM5: demostración ejecutable de los 3 equivalentes.** Crear
   `progress/equivalentes_F-062.py` con el patrón de `progress/equivalentes_F-060.py`:
   para el #1, un diferencial de `racha_delante` con fechas `None`, 0 y 1; para el #4 y el #5,
   uno del pipeline con `MOVER_CIZ` encendido sobre `SigridFake`. Citarlo en `mutacion_F-062.md`
   con su salida («N mutantes, 0 distintos», exit 0) y anotar que el #5 es el #11 de F-060.
2. **Regresión de RM5 de F-060.** `progress/equivalentes_F-060.py` funciona en `dev` (843ff13:
   «4 mutantes, 0 distintos») y en esta rama **falla con exit 1 en sv4 y en sv5**: su `_mutar`
   (l.83) exige que el texto aparezca una vez. En sv4, `racha_delante` duplica
   `f = int(l.fecha_int or 0)`; en sv5, `registro_pipeline.py:547` ya no termina en
   `candidatas,`. Adaptar el script (localizar por la función que contiene la línea o actualizar
   el texto) y reejecutarlo en los dos servicios hasta 0 distintos.
3. **«Evidencias» de `impl_F-062.md`**: añadir «4 workers» a la fila de mutación. El informe va a
   218/220 líneas, así que hay que recortar en otra parte.
4. **Para el líder, no para el implementer**: llevar al humano los equivalentes 1, 4 y 5 para
   que los acepte o no, y registrar la aceptación literal antes de la pasada 2.

## Observaciones (no bloquean)

- **O1**. `racha_ciz.py` importa `SUFIJO_CIZ` de `infrastructure` (hay precedente con
  `synckey_de` en 4 módulos); encajaría mejor junto a `PREFIJO_PARTES` en `pisado.py`.
- **O2**. `stmt_insert_inicio_con_fin` no acepta `pisadas`. Es correcto por la desviación 5, pero
  conviene una línea en su docstring que explique por qué.

**Automejora (propuesta, no aplicada)**: añadir a C4 bis que el reviewer ejecute los
`progress/equivalentes_F-*.py` existentes cuando el diff toque sus ficheros. Así se habría visto
el cambio 2 sin buscarlo.
