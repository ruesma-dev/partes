<!-- progress/review_F-063.md -->
Revisión completa (pasada 1) · `git diff dev...703b0db` (dev = bbc3172) + `azure-apps` a5f739e

# Review F-063 · Consulta de obra de sv2 que use el índice

**Veredicto: APPROVED** (pasada 1). Siete observaciones, ninguna bloqueante; la O1 conviene
arreglarla antes de fusionar (una línea de docstring).

**Nivel de rigor: `estandar`** (declarado en `features.json`): C1–C5, C3 bis, C4 bis con fase
RED, cobertura ≥ 80 % y mutación muestreada con los supervivientes analizados; RM5 N/A por nivel.

## Verificación ejecutada por mí

- `bash harness/init.sh` (tal cual): **ENTORNO LISTO**, exit 0. Raíz 522 passed / 3 skipped;
  `PUERTA COBERTURA` [OK] 100,0 % (43/43). Avisos previos y ajenos (F-032, ruff, infra).
- Sin caché: sv2 `python -m pytest` **422 passed**; guardián `tests/test_f038_lectores_sigrid.py`
  **24 passed** (`LECTORES_ESPERADOS` sin tocar). Árbol limpio después.
- Recálculo puro de la campaña (`alcance_de_feature("F-063")` + `generar_mutantes`): **4
  ficheros, 121 líneas, 23 mutantes**, igual que el informe. Los 4 supervivientes existen con el
  mismo operador y texto (`:70` ×2 entero, `:86` ×2 lógico).
- «Tiempo total» 191,2 s > 60 s ⇒ **campaña no reejecutada (3,2 min según el informe)**.
- **RM4** sobre una copia de sv2 (scratchpad), `tests/test_f063_consulta_obra.py`: mutante 1 ⇒ 91
  passed; 2, 3 y 4 ⇒ **1 failed / 90 passed** cada uno; sin mutar, 91 passed.

## El equivalente (`range(161, 0x0180)`): lo doy por bueno

Solo deja fuera U+00A0. `clave_obra("\xa0")` es `""` (`es_vacio`: `"\xa0".strip()` es vacío), así
que el original tampoco lo apunta (`len(base) == 1` falla). Calculé la tabla con los dos rangos:
**`_VARIANTES` idéntica**, y `_RANGO_VARIANTES` no se usa en ningún otro sitio (`grep`). No hay
entrada observable que lo distinga. Es un superviviente, no un muerto: RM3 no aplica. Lo acepta o no
el humano; recomiendo aceptarlo.

## Desviaciones del implementer

1. **Punto 20 de ARCHITECTURE en vez del 18**: correcta. El 18 es F-054 y la frase de F-058 vive en
   el 20; la spec citaba mal el número. El diff solo toca esa frase.
2. **Bases no ASCII en la tabla**: correcta y más fiel a R5 que el §5.2 («ASCII»). Las clases de las
   bases ASCII no cambian. Lo comprobé por fuerza bruta (U+0020–U+2FFFF): **ninguna clase lleva
   `^`, `-`, `]`, `[`, `%` ni `_` dentro**, ningún carácter de clave sale como especial sin escapar.
3. **Emulador de `LIKE` por programación dinámica**: aceptable. Independiente de `patron_like`,
   cubre `%`, `_`, `[...]`, `[^...]` y rangos, recurrencia correcta, tests propios y el corpus sabe
   fallar (con `%6%9%2%` sin clases cae).
4. **Docstring «TOP 1» de `test_f058_r7_existe_obra_pide_el_max_rows_del_cliente`**: ver O1.

## El patrón `LIKE`

- **Escapes `% _ [`**: `[%]`, `[_]`, `[[]` son los literales de T-SQL; `]`, `^` y `-` fuera de
  corchetes son literales (y `-` nunca llega: `clave_obra` lo quita). Tests R6 con `A_1`/`A%1`.
- **Clases sin `^ - ]`**: comprobado (desviación 2). Solo letras y dígitos, ordenados.
- **Falsos negativos por la intercalación**: no los hay para el universo real. Cada clase lleva la
  base, su minúscula y todas las variantes de U+00A0–U+017F, así que el superconjunto vale en CI/CS
  × AI/AS. Si `con.cod` es `varchar` CP1252, todas sus letras con clave de un carácter están en su
  clase (comprobado; `ƒ` entra como minúscula de `Ƒ`). Si sigrid-api tipara el parámetro como
  `varchar`, lo no representable pasa a `?` o a su letra base dentro de la clase: amplía, no
  recorta. Carácter de clave ignorable por la intercalación ⇒ patrón más ancho: inocuo. Y la M-EQ
  del líder lo confirma con la intercalación y el tipado reales: 924/924, trampa vuelve. Residuo
  documentado: O4.
- **Tope de `LIKE`**: la clase más larga es `U` (24 caracteres); 24 caracteres de clave dan **601**
  (1.202 bytes en `nvarchar`, frente a 8.000). Solo una clave de más de ~160 caracteres lo pasaría:
  ver O3; el fallo cae en «no se sabe», seguro.
- **`truncated`**: `_post_sql_read` sin cambios lanza ⇒ `ComprobadorObra` da «no se sabe» (no
  relee, la extracción sigue); tests R3 de F-063 y R9 de F-058. `max_rows` 500.000 frente a 822.

## `azure-apps` a5f739e

Solo `partes.md` (+6/−2), árbol limpio. Cuenta el `LIKE` parametrizado, sin funciones, candidatos
distintos y filtro exacto en sv2; dentro del párrafo de F-058 marcado «sin desplegar». Ver O5.

## Checkpoints

- **C1** [x] `init.sh` exit 0 · [x] ficheros del arnés.
- **C2** [x] solo F-063 `in_progress` · [x] rama `feature/F-063-consulta-obra-rapida` · [x]
  `current.md` con la sesión y las dos decisiones literales · [x] `history.md` sin cambios (no `done`).
- **C3** [x] hexagonal: `clave_obra` pura en `domain/models/` (test AST R12), infraestructura
  importa del dominio, nunca de application · [x] primera línea con ruta en los dos ficheros nuevos
  · [x] sin `print`, TODOs, secretos (barrido de las líneas añadidas aquí y en a5f739e: correos,
  IPv4, GUID, DNI, `password|secret|token|AccountKey|sig=`; solo la ruta del scratchpad y el nombre
  del Key Vault, ya en `dev`) ni dependencias nuevas · [x] trampas del monorepo: no aplican (sin
  registro en Sigrid ni schema). **Límite de servicio** [x]: solo sv2 (`git diff --stat dev`); la
  lista cerrada no crece; la clave no se copia a otro servicio.
- **C3 bis** N/A: no toca `docs/referencia/` (0 ficheros en el diff).
- **C4** [x] trazabilidad (tabla abajo), todo en verde · [x] sin red ni BBDD (`MockTransport`) ·
  [x] MANUAL: M-EQ y M-T hechas por el líder con resultado en `impl_F-063.md`; T12 (humano) en
  `current.md` y `tasks.md` con `redeploy_partes.ps1` y la KQL de F-058 `design.md` §10.
- **C4 bis**
  - [x] `rigor: estandar` declarado.
  - [x] Fase RED real: T1 (`ImportError`) y, antes de T4, **9 failed** por comportamiento en R1/R2,
    R7 y R8.
  - [x] `PUERTA COBERTURA` [OK] 100,0 %.
  - [x] Informe generado; totales recalculados · [x] > 60 s, no reejecutada (dicho arriba) · [x]
    coste por mutante 191,2 × 4 ÷ 20 = 38 s frente a ~26 s de base · [x] sin «NO VÁLIDA», base rota 0.
  - [x] **RM1**: mide `a00a501`; `a00a501..703b0db` solo toca el fichero de tests, `progress/` y la
    spec: el alcance de producción es el revisado. **RM2**: media 9,6 s × 4 workers = 38 s ≥ base;
    sin salto. **RM3**: ninguno de los 16 muertos es equivalente (los repasé: todos cambian una
    clase, el patrón o lanzan). **RM5** N/A (rigor `estandar`; basta la justificación escrita, que
    está). **RM6**: no se quitó ninguna guarda; solo se añadieron tests.
  - [x] Los 4 supervivientes analizados, ninguno en `PENDIENTE`.
  - [x] «Evidencias» con tests, cobertura, mutantes/supervivientes y tiempo; los **4 workers**
    constan en la fila «Workers» del informe generado, no en «Evidencias» (O6).
  - [x] Ningún N/A sin justificar.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T1–T11 `[x]` con commits `F-063 Tn:` (11aef31 … 22cea59); T6 en `azure-apps`
  (a5f739e); T12 `[ ]` legítimo (MANUAL del humano, tras fusionar) · [x] árbol limpio.

## Trazabilidad

| Req. | Tests |
|---|---|
| R1, R2 | `test_f063_r1_r2_un_like_parametrizado_sin_funciones`; `test_f058_r7_existe_obra_parametrizada` |
| R3 | `test_f063_r3_*` (max_rows, tope, truncada, 4xx/5xx); `test_f058_r9_existe_obra_ok_false_lanza` |
| R4 | `test_f063_r4_*` (R10, raros, corpus de 6.000 con semilla 63) |
| R5 | `test_f063_r5_*` (clases, tal cual, `µ`, invariante y completitud de la tabla) |
| R6, R7 | `test_f063_r6_*`; `test_f063_r7_clave_vacia_lanza`, `_no_consulta` |
| R8, R10 | `test_f063_r8_*`, `test_f063_r10_*` |
| R9, R12 | `test_f063_r9_*` (identidad de objeto, clave sin cambios), `test_f063_r12_*` (AST) + `git diff --stat dev` |
| R11 | tests de F-058 de `ComprobadorObra`, log y `fetch_tipos_hora` sin tocar y en verde; diff: puerto, pipeline y `Settings` intactos |
| R13 | revisión: ARCHITECTURE punto 20 y `azure-apps/partes.md` §3.2 |

## Observaciones (no bloquean)

1. **(Menor, conviene antes de fusionar)** `services/partes-api/tests/test_f058_obra_sigrid.py:209-210`:
   el docstring dice «el `TOP 1` acota la respuesta» y ya es falso. R12 limita a «las aserciones del
   texto SQL que esta feature sustituye»: su intención es no tocar el comportamiento de los tests de
   F-058, y un docstring no lo cambia. Recomiendo «… ningún lector fija un `max_rows` bajo.» (quitar
   la segunda frase). No exige otra pasada.
2. **(Doc)** «usa el índice (~0,1 s)»: con `%` inicial no hay búsqueda por índice, sino un
   recorrido sin funciones por fila. El tiempo es real; la frase, imprecisa. Opcional.
3. **(Robustez, fuera de spec)** Una clave de más de 24 caracteres nunca puede existir (`con.cod` es
   «Texto de 24») y aun así se consulta; por encima de ~160 caracteres el patrón podría pasar el tope
   de `LIKE` y daría «no se sabe» donde F-058 decía «inexistente». Inocuo; si la M4 enseña claves
   largas, cortocircuitar en otra feature.
4. **(Límite conocido, `design.md` §5.2)** Clave múltiple (`¼ ½ ¾ ™ ß`, todos en CP1252): falso
   negativo (relectura innecesaria). Hoy 0 (M-EQ), pero nada lo vigila después. Informativo.
5. **(Formato)** `azure-apps/partes.md`: la frase de F-063 no lleva su «(2026-10-26, sin
   desplegar)»; está dentro del párrafo de F-058 «sin desplegar», así que no engaña.
6. **(Papeleo)** Poner «4 workers» en la fila de mutación de «Evidencias» de `impl_F-063.md`.
7. **(Formato)** `docs/ARCHITECTURE.md:581`: línea de 103 caracteres que rompe el ajuste.

**Automejora (propuesta, no aplicada)**: en `CHECKPOINTS.md` C4 bis («Evidencias»), aceptar los
workers de la fila «Workers» del informe generado, más fiable que copiarlos a mano.
