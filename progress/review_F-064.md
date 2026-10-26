Revisión incremental desde 3ef08e9 (pasada 2) · delta `3ef08e9..750a92a` (pasada 1: completa, `f940e67..5778ad0`)

# F-064 · Review (reviewer)

**Veredicto final: APPROVED.** La pasada 1 aprobó con seis observaciones que no bloqueaban. A las
observaciones 1, 2 y 4 el humano respondió, literalmente, «arregla». Las tres están arregladas,
cada una con su prueba, y el delta no toca nada más. Las observaciones 3 y 5 quedan fuera por
decisión del humano, y la 6 la hace el líder al cerrar.

**Rigor:** `estandar`, declarado en `features.json`. Exige fase RED, cobertura y mutación
muestreada con los supervivientes analizados. RM5 es N/A por nivel.

## Pasada 2 · delta `3ef08e9..750a92a`

**Qué entra.** Fuera de `progress/`, el delta toca dos ficheros:
- `static/app.js`: 9 líneas dentro de `estadoVigente`;
- `tests/test_f064_filtros_js.py`: el renombre, dos tests nuevos y el soporte `~Nombre` del DOM
  falso.

No cambia Python de producción, así que el alcance de la mutación sigue siendo el mismo (4
mutantes) y **la campaña no se relanza**. Nada de lo aprobado queda invalidado: no cambian firmas
públicas, no se mueven ficheros y las huellas de R22/R23 siguen en verde.

- **Observación 1** (6be5c0b): se renombra a `test_f064_r4_r10_con_pantalla_pone_la_foto_con_su_t`.
  Solo cambia el nombre, y R4 ya tiene un test a su nombre.
- **Observación 2** (ec7297d): `test_f064_r11_columna_sin_filtro_delante_cuenta_por_cellindex`
  pone una columna con título y sin input delante de las filtrables. **Lo reproduje sobre una
  copia en el scratchpad**: el mutante `fila.children[filtrosDe(table).indexOf(input)]` da
  **1 failed, 91 passed**. Ahora muere.
- **Observación 4** (430274e): `estadoVigente` se queda solo con las pantallas que son objeto y
  tienen `t` numérico.
  - **RED reproducida sobre la copia.** Quité `est.pantallas = pantallas;` y el resultado fue
    **2 failed** (`…mal_formadas…` y `…pantalla_null_no_corta_el_init_de_f043`). Coincide con la
    traza del informe (`TypeError: Cannot read properties of null (reading 't')`).
  - **No descarta entradas válidas.** Toda pantalla que escribe el código pasa por
    `conPantalla`, que siempre pone `nueva.t = ahoraMs` (un número) sobre un objeto. Lo confirma
    un mutante de control: exigir además `p.query` da **7 failed**, porque los tests sí usan
    entradas válidas sin `query`.
  - `barrerCaducados` sigue mirando solo la cabecera (`v` y `t`), así que no cambia.
  - El test del init ejecuta las líneas **reales** del `DOMContentLoaded`, desde
    `restaurar(dias)` hasta `esperasDeLaPagina()`. Con una pantalla `null`, ahora corren
    `restaurarVista` y `esperasDeLaPagina`.
- **La copia sin mutar** dio 92 passed, que es la línea base.
- **`bash harness/init.sh`**, tal cual: ENTORNO LISTO. Raíz: 522 passed, 3 skipped. COBERTURA
  100 % (7/7). TAMAÑO `[OK]`. sv4 salió **de caché**, así que, como pide `reviewer.md` (755f5f6),
  la lancé entera sin caché: `python -m pytest -q -p no:cacheprovider` ⇒ **2987 passed, 1 skipped** (739 s; +3 tests nuevos frente a la pasada 1).
- **El informe del implementer** trae la sección «Arreglo de observaciones 1, 2 y 4», con la
  traza RED, el mutante a mano y los números de init. En «Evidencias», la mutación ya figura
  como 4/0.
- **Commits**: `F-064: observación N de la review, …`, con tildes. El árbol queda limpio.

**Checkpoints de la pasada 2.** Siguen los de la pasada 1, sin ningún `[ ]`. En C4, R4 pasa a
tener un test a su nombre. En C4 bis, la fase RED del arreglo es real y la mutación no cambia de
alcance.

## Pasada 1 (resumen) · completa `f940e67..5778ad0`

- **init y suite.** init.sh dio ENTORNO LISTO. La suite de sv4, lanzada a mano: 2984 passed,
  1 skipped. Los tests de F-064 eran 98 (9 de Python y 89 de node); node está instalado.
- **Mutación (Python).** El recálculo puro coincide con el informe: 2 ficheros, 32 líneas y 4
  mutantes en `identidad.py`, ninguno equivalente.
  - La campaña tardó 1874,7 s, más de 60 s, así que **no se reejecutó**.
  - RM1: se midió `ec1a689`, y desde ahí solo cambian `progress/` y `tasks.md`.
  - RM2: 468,7 × 4 workers, coherente. Sin «⚠ CAMPAÑA NO VÁLIDA» y con «Sin veredicto» = 0.
  - RM6: no se quitó código defensivo.
- **Mutación manual del JS (RM4, sobre una copia).** Hice 30 mutantes: 24 muertos y 6 vivos. Los
  vivos eran equivalentes, salvo el de la observación 2, ya cerrado. Mueren los centrales:
  - el borde de las 8 h, el `t` futuro, la poda a 50 y el barrido por `PREFIJO`;
  - la clave de tabla, que la foto conserve los días de otro periodo y la búsqueda ajena;
  - la redirección solo con `search === ""`, el aviso y `quitarTodo`;
  - la escritura única, los enganches y `seleccionar`.
- **Desviaciones.**
  - (1) Cambiar el ancla del test de F-043 es correcto: es el efecto obligado de R19 y las
    aserciones no cambian.
  - (2) Que la foto conserve los días de otro periodo y la búsqueda ante `?message=` es correcto
    y no hacía falta consultar: lo exige M1.2 del diseño aprobado, y R19 dice «ni guarda».
- **Solape con F-061.** No rompe nada: `partes_list.html` cambia solo en la l. 34, y la insignia
  «Sin líneas» y `_irTrasBorrar` no se tocan.
- **Privacidad.** El actor no queda en claro: lo que se guarda es un hash de 16 hex. Las claves
  de día con el nombre del trabajador son la forma aprobada en el diseño §5 (observación 3).

## Checkpoints

- **C1** [x] init en verde · [x] los ficheros base existen.
- **C2** [x] una sola `in_progress` · [x] la rama es la de la feature · [x] `current.md` está
  limpio de otras sesiones · [x] las `done` tienen historia.
- **C3** [x] hexagonal (`clave_filtros` es pura en `interface_adapters/web`) · [x] primera línea
  con la ruta · [x] sin prints, `console.log`, secretos ni dependencias nuevas · [x] trampas del
  dominio: no aplica.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] trazabilidad (tabla de abajo) · [x] sin red ni BBDD (SQLite y DOM falso) · [x] M1 y
  M2 en `current.md` y en el diseño §8.
- **C4 bis**
  - [x] rigor · [x] RED (T1, T4, T5 y el arreglo de la observación 4) · [x] cobertura `[OK]`;
  - [x] mutación verificada de forma independiente · [x] muertos no reejecutados (> 60 s) ·
    [x] coste por mutante > 1 s;
  - [x] campaña válida · [x] RM1 · [x] RM2 · N/A RM5 (`estandar`) · [x] RM6;
  - N/A campaña manual · [x] sin supervivientes · [x] «Evidencias».
- **C4 ter** N/A: no hay `rutas_sensibles.json`.
- **C5** [x] T0–T10 hechas con su commit. T11 (M1) y T12 (M2) son MANUAL y van después del
  review y del despliegue: N/A justificado · [x] árbol limpio · [x] `features.json` en
  `in_progress`.

## Cobertura: requisito → test

| R | Test(s) |
|---|---|
| R1–R3 | `test_f064_clave_usuario.py` (`r1_*`, `r2_*`, `r1_r3_*`); los de F-017 en verde sin tocarlos |
| R4 | `r4_r10_con_pantalla_pone_la_foto_con_su_t`, `r6_constantes_de_sesion` |
| R5, R9 | `r5_r9_clave_de_almacen_*`, `r5_sin_clave_*`, `r5_localstorage_que_lanza_*`, `r9_*` |
| R6, R8 | `r6_*` (borde de 8 h, inválidos, futuro, entradas mal formadas, pantalla `null`), `r6_r8_barre_*` |
| R7 | `r7_poda_a_las_50_*`, `r7_con_pantalla_no_muta_*` |
| R10, R14 | `r10_un_cambio_de_filtro_guarda_*`, `r10_r14_foto_vacia_*`, `r14_foto_vacia` |
| R11 | `r11_r15_r18_repone_por_tabla_y_columna_*`, `r11_columna_sin_filtro_delante_*`, `r11_tabla_sin_id_*` |
| R12, R13, R16 | `r12_*` (5), `r13_casilla_*`, `r16_*` (4) |
| R15, R17, R18 | `r11_r15_r18_*`, `r15_restaurar_va_justo_antes_*`, `r17_*` |
| R19, R20 | `r19_*` (7), `r19_r20_limpiar_*`, `r20_limpiar_apunta_*` |
| R21–R23 | `r21_*`, `r22_r23_funciones_intactas` (5 huellas), `r23_vista_clave_intacta` |
| R24 | `git diff --stat dev`: solo sv4, el doc, `specs/`, `progress/`, `features.json` y `BACKLOG.md` |
| R25 | revisado a mano: ARCHITECTURE, punto 11 |

## Observaciones que siguen abiertas (fuera por decisión del humano)

- **3.** Hasta 8 h quedan en el navegador los nombres normalizados de trabajador (claves de día
  de la matriz) y los textos tecleados. Lo caducado solo se barre en la siguiente carga del
  portal.
- **5.** Hay commits de la pasada 1 sin tildes: 8699741, 29e1f43 y 98a751a. No se reescribe la
  historia.
- **6.** En `current.md`, la sección de F-064 aún dice «Decisiones abiertas» aunque ya están
  aprobadas. La corrige el líder al cerrar.
