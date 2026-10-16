<!-- specs/F-048-solo-extras-en-laborable-como-jornada/requirements.md -->
# F-048 · Ordinarias + extras leídas en laborable siguen la regla de jornada — Requisitos

**sv3** (normalizador de la ingesta y su guardado) y **sv4** (copia gemela del ORM y la
traza en el portal). El conciliador de sv3, sv2 y sv5 no cambian. Una columna nueva en
`parte_registros` (base `partes`, las dos copias del ORM). Rigor **crítico**: horas que
acaban en nómina, coste de obra y Sigrid; esquema compartido sv3/sv4. Se implementa
**después de F-046 y F-047** (design §8). Decisiones: design §6.

Petición del humano (2026-10-15): «cuando sea laborable, aunque las horas sean extras se
usa la regla de 8+x». **Ampliación del mismo día**: también en las filas con ordinarias Y
extras leídas: se suman y el total se reparte con la jornada (J normales + exceso extra, o
extra negativa si no llega), en vez de respetar las extras leídas tal cual.

## Contexto (verificado en el código el 2026-10-15)

- `ParteNormalizer` (sv3) expande cada fila de sv2 en un registro `normal` (ordinarias
  > 0) y otro `extra` (extras ≠ 0). El reparto de jornada (F-015/F-045,
  `_reclasificar_extras_jornada`) solo actúa sobre las `normal`: las `extra` leídas se
  respetan siempre y un día laborable sin ordinarias no se normaliza (F-045 R8, R21).
- **Caso 1** (15/10/2026, obra 0678, parte d2141256…, pág. 2): fila con ordinarias nulas
  y 10 extras ⇒ UNA línea `extra` de 10 h. Lo esperado: 8 + 2.
- **Caso 2** (02/10/2026, obra 0686, parte 5fc3545d…, fila 3): 4 ordinarias + 5 extras
  ⇒ TRES líneas: `normal` 8 (`horas_orig` 4) + `extra_auto` −4 + `extra` 5. Total bien
  (9), pero lo esperado son DOS: 8 normales + 1 extra. Esa fila ya está en Sigrid.

## Glosario

- **Fila sumable**: fila de sv2 con `horas_extraordinarias` > 0 (con o sin ordinarias).
- **Trabajado de la fila** = ordinarias (si > 0) + extras leídas.
- **Registro sumado**: registro `normal` de una fila sumable.
- **`horas_extra_leidas`**: columna nueva (Float, nula) con las horas de ese registro que
  sv2 leyó como extra.
- **J**, **grupo**, **reparto** y **congelada**: los de F-015, F-045 y F-004/F-037.

## Ingesta (sv3, `parte_normalizer.py` y `save_parte`)

- **R1.** CUANDO una fila es sumable, el normalizador debe emitir su trabajado como
  registros `normal` (uno por partida, con el reparto entre partidas de hoy: ordinarias
  primero, luego extras) y **ningún** registro `extra` de esa fila.
- **R2.** Cada registro sumado debe llevar en `horas_extra_leidas` la parte que procede de
  extras según ese orden (nula si no tiene ninguna); su suma en la fila debe ser igual a
  las extras leídas.
- **R3.** Una fila con extras ≤ 0 o nulas debe expandirse exactamente como hoy (la extra
  negativa explícita sigue siendo un registro `extra`), con `horas_extra_leidas` nula.
- **R4.** El código propuesto de un registro sumado debe ser el `codigo_hora_ordinaria`
  leído (o ninguno), nunca el `codigo_hora_extra`.
- **R5.** Las incidencias de la fila, el `line_index` correlativo, la omisión de filas
  vacías y los demás campos no deben cambiar.
- **R6.** `save_parte` debe persistir `horas_extra_leidas` de cada registro.
- **R7.** El INFO `[parte-normalizer]` de cada parte debe añadir al final
  `filas_extra_sumadas=<n> horas_extra_sumadas=<h>`.

## Efecto en la conciliación (sv3, sin cambios de código: F-015/F-045 tal cual)

- **R8.** Un registro sumado debe repartirse como cualquier ordinaria: en laborable, J y
  exceso en `extra_auto` (negativa si no llega); en no laborable, todo a `extra_auto`.

## Casos de aceptación (candef 8 ⇒ J = 8 de lunes a viernes salvo que se diga)

Por la ingesta + `conciliar_todos` (repositorio real sobre SQLite). «a + b» = `normal` a
+ `extra_auto` b; sin `+` = sin split.

- **R9 · Caso 1.** Jueves, ordinarias nulas y 10 extras ⇒ **8 + 2**: dos líneas;
  la `normal` con `horas_orig` 10 y `horas_extra_leidas` 10.
- **R10 · Caso 2.** Viernes, 4 + 5 extras ⇒ **8 + 1**: dos líneas; la `normal` con
  `horas_orig` 9 y `horas_extra_leidas` 5. Ninguna `extra` explícita.
- **R11 · No llega.** 4 + 2 extras ⇒ **8 + (−2)**. Solo 6 extras ⇒ **8 + (−2)** (DA4).
- **R12 · Justo J.** 6 + 2 extras ⇒ **8**, sin split. Solo 8 extras ⇒ **8**.
- **R13 · Candef 9.** Viernes (J 6): 4 + 5 ⇒ **6 + 3**; solo 10 ⇒ **6 + 4**. Jueves
  (J 9): 4 + 5 ⇒ **9**; solo 10 ⇒ **9 + 1**. Viernes festivo: el jueves (J 6) como el
  viernes laborable, y en el festivo todo a extra.
- **R14 · Sábado.** 4 + 5 ⇒ **0 + 9** (hoy 0 + 4 + 5 explícita: mismos importes, una
  línea menos; DA3). Solo 10 ⇒ **0 + 10**.
- **R15 · Dos obras (F-045).** A fila 4 + 5 y B ordinarias 3 ⇒ pesos 9 y 3: A **6 + 3**;
  B **2 + 1** (hoy A 6 + (−2) + 5 explícita: mismos totales por obra).
- **R16 · Dos obras solo extras.** A solo 6 y B solo 4 ⇒ A **5 + 1**; B **3 + 1**.
- **R17 · Mixto.** A ordinarias 8 y B solo 2 extras ⇒ A **6,5 + 1,5**; B **1,5 + 0,5**
  (hoy A 8 y B `extra` 2; DA5).
- **R18 · Congeladas.** Una línea congelada del grupo se queda fija y el registro sumado
  recibe la jornada que quede (modo residual de F-045), como cualquier ordinaria.

## Lo que no cambia

- **R19.** No cambian `recurso_conciliador.py`, `reparto_ponderado.py`, `pareja_extra.py`,
  `jornada_resolver.py` (ni su gemelo), la regla de congelación (las dos copias), el
  prompt y el esquema de sv2, ni sv5. Ningún test existente cambia (design §5).
- **R20.** Las líneas ya guardadas no se tocan: la regla vale para ingestas nuevas
  (y reingestas) desde el despliegue (DA6). M1 cuenta las que quedan como hoy.

## sv4

- **R21.** `horas_extra_leidas` en la copia de sv4 de `orm_models.py` (byte-idéntica).
- **R22.** Las vistas de parte, obra y trabajador deben mostrar en un registro con
  `horas_extra_leidas` > 0 una etiqueta «incl. X h extra leídas» (con `title` que
  explique la regla), sin CSS nuevo. Sin la columna (nula o 0), nada nuevo.
- **R23.** Las ediciones de sv4 no tocan `horas_extra_leidas` (es lo que se leyó); el
  tipo y las horas los sigue decidiendo el humano como hoy (DA7).

## Esquema y documentación

- **R24.** `horas_extra_leidas` = `Float`, nula, sin defecto, en las dos copias;
  `ddl_complementario` la añade con `ADD COLUMN IF NOT EXISTS`.
- **R25.** `docs/ARCHITECTURE.md` (semántica 3), `docs/referencia/partes-proyecto.md`
  («Cómputo de extras») y `azure-apps/partes.md` (§3.3) deben describir la regla.

## Fuera de alcance

- Tratar las líneas ya guardadas: sin congelar, a mano o con M5 opcional; congeladas
  (como el caso 2, ya en Sigrid), feature aparte sobre F-046 (DA6: solo `UPDATE`, nunca
  borrar; una extra que queda a 0 se pone a 0).
- Cambiar sv2. Umbral «solo si llega a J» para filas solo extra (DA4, alternativa B).
