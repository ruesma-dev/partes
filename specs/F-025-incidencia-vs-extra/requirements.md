<!-- specs/F-025-incidencia-vs-extra/requirements.md -->
# F-025 · Incidencia y horas el mismo día — Requisitos (EARS)

Origen: correo de Juan Romero (Dir. Admón. y Control de Costes, «RV:
CAPTURAS», 2026-09-30). Un parte llevaba una incidencia y, al lado, una hora
extra del mismo día: «si está de baja maternidad, no puede tener horas
extra». Exploración de Sigrid en `progress/explore_F-025_sigrid.md`: Sigrid
**no clasifica** sus incidencias, y lo que Administración teclea a mano casi
nunca junta incidencia y horas (el único caso legítimo es un accidente
después de 2 h de trabajo). Servicio: **solo sv4**. Diseño y decisiones en
`design.md`.

Vocabulario: «línea» = fila activa de `parte_registros` (no está en la
papelera y su documento está activo); «día-trabajador» = (persona, fecha);
«horas» = línea que no es incidencia, ordinaria o extra (incluidas las
`extra_auto`), con `|horas| > 0`. Tests: `test_f025_rN_*`, sin red ni BBDD
(SQLite en memoria con el ORM, `TestClient` y dobles de sv5).

## A · Clasificación versionada (DA1, DA2)

- **R1** (ubicuo). sv4 debe leer **al arrancar** la tabla versionada
  `config/incidencias.yaml`, que asigna a cada letra de la leyenda (V, B, AT,
  FJ, F, H, M) su código de Sigrid (`CI*`), su nombre y una clase:
  `dia_completo` o `parcial`. Valores iniciales: V, B, M y F, `dia_completo`;
  AT, FJ y H, `parcial`.
- **R2** (no deseado). SI el fichero no existe, no se puede parsear, le falta
  alguna de las siete letras, trae una clase desconocida o un código de Sigrid
  que no empieza por `CI`, ENTONCES el arranque de sv4 debe fallar con un
  error que nombre el problema. No hay valores por defecto en silencio.
- **R3** (ubicuo). La clase de una línea de incidencia sale de su
  `incidencia_codigo` (sin espacios y en mayúsculas). Si no está en la tabla,
  sale de su `hora_codigo` buscándolo entre los códigos de Sigrid de la
  tabla. Si tampoco está ahí (también `CIZ`), la línea queda sin clase y no
  participa en la regla.

## B · Detección (función pura)

- **R4** (ubicuo). La persona de una línea es su `empleado_dni` normalizado
  (sin espacios ni guiones y en mayúsculas). Si no tiene DNI, es su
  `worker_key_for_registro`. En un día-trabajador entran todas sus líneas,
  **de cualquier obra y en cualquier estado de Sigrid**, también
  `registrado`.
- **R5** (evento). CUANDO un día-trabajador tiene al menos una incidencia
  `dia_completo` y al menos una línea de horas, todas sus líneas deben quedar
  en nivel **`bloqueo`**, con un motivo que nombre la incidencia (p. ej.
  «Maternidad/Paternidad (M)») y diga que hay horas el mismo día.
- **R6** (evento). CUANDO un día-trabajador tiene una incidencia `parcial`,
  ninguna `dia_completo` y al menos una línea **extra** con `horas > 0`,
  todas sus líneas deben quedar en nivel **`aviso`**, con un motivo que nombre
  la incidencia.
- **R7** (ubicuo). No es incompatible, y la línea no lleva nivel, ninguna de
  estas combinaciones: incidencia `parcial` con solo ordinarias, o con una
  extra negativa; incidencia sin horas; horas sin incidencia; varias
  incidencias sin horas; líneas de horas con 0 o sin horas.
- **R8** (ubicuo). Si un día-trabajador cumple R5 y R6 a la vez, manda
  `bloqueo`.

## C · Aprobación (servidor de sv4)

- **R9** (evento). CUANDO `/api/aprobar/preflight`, `/ejecutar` o `/encolar`
  preparan las líneas pedidas, las de un día-trabajador en `bloqueo` **no
  deben viajar a sv5 ni cambiar de estado**. Cuentan en
  `excluidas.incompatible` y salen en `excluidas_detalle` con
  `estado: "incompatible"` y el motivo de R5. Para decidirlo se miran **todas**
  las líneas de esa persona en ese día, también las que no se pidieron
  aprobar y las de otras obras.
- **R10** (no deseado). SI tras R9 no queda ninguna línea que enviar,
  ENTONCES la respuesta debe ser 422, sin llamar a sv5, y el motivo debe
  nombrar las líneas incompatibles junto a las demás exclusiones.
- **R11** (evento). CUANDO una línea pedida está en `aviso`, debe viajar
  igual, y el grupo de su obra en el preflight debe llevar
  `avisos_incidencia`: una entrada por línea extra en aviso con
  `registro_id`, `fecha`, `nombre`, `horas` y `motivo`. Un grupo sin avisos
  lleva la lista vacía.
- **R12** (ubicuo). La exclusión de R9 **no tiene excepción**: ni
  `incluir_borradas`, ni `pisar_claves`, ni `forzar_sin_sesame` la levantan.
- **R13** (ubicuo). Una línea `registrado` o `borrado_sigrid` excluida por
  F-024 se cuenta **solo** en su estado, aunque además esté en `bloqueo`.
- **R14** (ubicuo). El payload que sv4 manda a sv5 no cambia de forma (R33 de
  F-022): cambia solo qué líneas viajan.

## D · Vistas del portal (DA5)

- **R15** (ubicuo). En la matriz de la vista de obra, una celda debe llevar
  la clase `mx-incompat` si alguna de sus líneas está en `bloqueo`, o
  `mx-incompat-aviso` si solo hay `aviso`, con el motivo en el `title`.
- **R16** (ubicuo). En el calendario de la vista de trabajador, un día del
  periodo debe llevar la clase `cal-incompat` o `cal-incompat-aviso` y una
  marca con el motivo en el `title`.
- **R17** (ubicuo). En las tablas de líneas de las vistas de obra y de
  trabajador, cada línea en `bloqueo` o en `aviso` debe llevar una insignia
  con su nivel y el motivo en el `title`.
- **R18** (ubicuo). R15–R17 se calculan como en R4: si la incidencia está en
  la obra A y las horas en la B, se marcan las celdas y las líneas de **las
  dos** obras.
- **R19** (evento). CUANDO el modal de aprobación recibe
  `excluidas.incompatible > 0`, debe mostrar fuera del desplegable de
  excluidas un aviso visible con el número de líneas que no se registran y el
  porqué. CUANDO un grupo trae `avisos_incidencia`, debe listarlos. Todo texto
  que venga del servidor se escapa (`esc`).

## E · Lo que no cambia

- **R20** (ubicuo). F-025 no rechaza ninguna creación ni edición: «+ Nuevo»,
  editar horas, crear extra, cambiar el código de hora o mover la fecha
  siguen funcionando igual con o sin conflicto (DA4).
- **R21** (ubicuo). sv2, sv3 y sv5 no cambian. No hay columnas, tablas ni DDL
  nuevos, y ningún dato existente se reescribe ni se desaprueba (DA6).
- **R22** (ubicuo). `congelacion.py`, `_rol_incidencia` y el cálculo de
  extras por jornada no cambian (DA8).
- **R23** (ubicuo). Sin la tabla de clases (repositorio construido sin ella,
  como en los tests anteriores a F-025), las vistas y la aprobación se
  comportan exactamente como antes: sin niveles, sin exclusiones nuevas y con
  `avisos_incidencia` vacío.

## F · Documentación

- **R24** (ubicuo). `docs/ARCHITECTURE.md` debe añadir la semántica 14
  (incidencia y horas el mismo día: tabla, niveles, dónde se aplica).
  `docs/referencia/partes-proyecto.md` §4.1 debe decir **H = Huelga (CIH)** y
  enlazar la tabla. El docstring de `parte_models.py` de sv2 ya lo dice y no
  se toca.
