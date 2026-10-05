<!-- specs/F-030-recurso-sin-ficha/requirements.md -->
# F-030 · Trabajador con recurso en Sigrid pero sin ficha: casarlo contra la ficha de recurso

Humano, 2026-10-05. Rigor **crítico** (cambia qué recurso se escribe en Sigrid).
Caso real: partes de Porsan (empresa 28, obra 0724, membrete resuelto) con un
trabajador cuyo recurso `MO/` de alta tiene `res.cif` = su DNI pero no tiene
ficha `emp`: hoy sale `empleado_match_method='none'` y «Sin recurso». Datos
medidos (solo lectura, agregados): design §1. **DA1–DA9 aprobadas por el humano
el 2026-10-05** (design §8): «el proceso es el mismo que con empleado pero
contra la ficha de recurso cuando no está la de empleado». Toca sv3 y, al
mínimo, sv4; sv5 solo gana tests (design §2).

Glosario. **DNI canónico**: el DNI normalizado (`text_match.normalize_dni`) y,
si son de 1 a 7 dígitos y una letra, completado con ceros a la izquierda hasta
8 (Sigrid los guarda siempre con 8). **Ficha de recurso**: recurso de código
`MO/` con `res.cif` no vacío, sin ninguna ficha `emp` con ese DNI y cuyo
`res.conide` no es una ficha; se trata como una ficha de empleado más (DNI =
`res.cif`, nombre = `con.res`, empresa y baja las del recurso). **Persona**: una
ficha de empleado o una ficha de recurso, nunca las dos.

## A. DNI canónico (sv3)

- **R1.** El sistema debe calcular el DNI canónico así: `normalize_dni` y, SI
  el resultado casa con `^[0-9]{1,7}[A-Z]$`, ceros a la izquierda hasta 8
  dígitos; cualquier otra forma (8 dígitos, NIE, CIF, vacío) queda igual.
- **R2.** CUANDO sv3 normaliza un parte, el `trabajador_dni_leido` de cada
  registro debe ser el DNI canónico del leído, o None si no se leyó.
- **R3.** CUANDO el DNI leído es el de una ficha sin el cero inicial, el
  trabajador se debe casar por DNI (`dni`) con esa ficha (F-023 R18).

## B. Casado contra la ficha de recurso (sv3, ingesta)

- **R4.** sv3 debe construir las fichas de recurso (glosario) de todas las
  empresas a partir de los maestros que ya carga, leyendo además el código
  (`con.cod`) y el nombre (`con.res`) del recurso en la misma lectura paginada.
- **R5.** CUANDO `elegir_ficha` devuelve `desconocido` para el DNI leído, sv3
  debe aplicar la **misma** `elegir_ficha` (empresa del parte, alta a su fecha)
  sobre las fichas de recurso **antes** del alias y del nombre; con `ok`, el
  trabajador queda casado por recurso con método `recurso_dni`.
- **R6.** SI R5 no da ficha de recurso (`desconocido`, `solo_baja`,
  `otra_empresa` o `ambiguo`), ENTONCES el casado sigue como hoy (alias y
  nombre) y, salvo `desconocido`, se loguea INFO con el motivo, sin DNI ni
  nombre (DA5).
- **R7.** SI `elegir_ficha` da `ambiguo`, `solo_baja` u `otra_empresa` sobre las
  fichas de empleado, ENTONCES no se mira ninguna ficha de recurso: rige F-023
  R19–R22 sin cambios.
- **R8.** El alias aprendido (`empleado_alias`) solo apunta a fichas de
  empleado y se aplica como hoy (F-023 R23); no hay alias de recurso.
- **R9.** CUANDO se casa por nombre (sin DNI leído o sin casar por él, y sin
  alias), `EmpleadoMatcher.match_nombre` debe recibir **juntas** las fichas de
  empleado candidatas y las fichas de recurso candidatas (de alta a la fecha
  del parte y de la empresa del parte), con el mismo umbral
  (`EMPLEADO_MIN_SCORE`) y las mismas reglas de ambigüedad; si gana una ficha de
  recurso, método `recurso_nombre`.
- **R10.** SI la mejor puntuación de nombre empata entre dos personas (dos
  fichas de recurso, o una de recurso y una de empleado), ENTONCES el
  trabajador queda sin casar con `nombre_ambiguo` (F-023 R24).
- **R11.** El nombre del recurso en formato «APELLIDOS, NOMBRE» debe casar con
  el nombre leído en cualquier orden de nombre y apellidos.
- **R12.** SI se casa contra una ficha de recurso, ENTONCES `empleado_ide` y
  `empleado_codigo` quedan NULL, `empleado_dni` = `res.cif` tal como está en
  Sigrid, `empleado_nombre` = `con.res`, `empleado_reside` = `res.ide` y el
  método es `recurso_dni` o `recurso_nombre`; ninguna columna nueva.
- **R13.** `review_required` no debe subir por un trabajador casado por recurso;
  sigue subiendo por todo trabajador con `empleado_ide` NULL y otro método.

## C. Conciliación del recurso (sv3, sin cambio de código)

- **R14.** CUANDO el conciliador procesa una línea `recurso_dni` o
  `recurso_nombre` no congelada, debe asignarle el único candidato con
  `res.cif` = su `empleado_dni`, de alta a la fecha de la línea y de la empresa
  de su obra (F-023 R25–R29), dejar `parte_estado` `ok` o `sin_parte` y pisar
  categoría y hora con ese recurso: la línea se guarda en el recurso como
  siempre.
- **R15.** CUANDO esa línea entra en el reparto de extras por jornada, el
  `candef` sale de la ficha de horas del recurso y el calendario laboral se
  pide con su `empleado_dni`, igual que con ficha.

## D. Coherencia con sv5 (sin cambio de código; lista cerrada intacta)

- **R16.** F-030 no debe modificar `seleccion_sigrid.py` (sv3) ni
  `coherencia_recurso.py` (sv5); `tests/test_f023_de_alta_gemelos.py` sigue
  verde sin tocarlo.
- **R17.** CUANDO sv5 verifica un recurso de una ficha de recurso (`res.conide`
  0) y la línea trae `empleado_dni` = su `res.cif`, la verificación debe pasar
  (empresa, alta y persona).

## E. Portal (sv4, mínimo)

- **R18.** sv4 debe considerar casado un registro con `empleado_ide` o con
  método `recurso_dni`/`recurso_nombre`, decidido en un único helper que usan
  los cuatro cálculos de `matched`; se ve como cualquier trabajador casado.
- **R19.** La cola de conciliación (`list_unmatched_workers`) y su confirmación
  por nombre leído deben excluir los registros casados por recurso.
- **R20.** Catálogo, alta manual y reasignación no cambian: reasignar a una
  ficha una línea casada por recurso la casa con esa ficha y suelta su recurso
  (F-023 R42).

## F. Cuenta analítica en Porsan (sv5, sin cambio de código)

- **R21.** CUANDO sv5 prepara una línea `escribir` de un recurso sin cuenta en
  ninguna fila de `reshor` (todos los de la empresa 28 hoy), la cuenta debe
  ser `caa_ide = 0`, motivo `recurso_sin_cuenta` y sin aviso (F-021 R3; DA9).

## G. Documentación

- **R22.** `docs/ARCHITECTURE.md` (semántica 2 y 12), `partes-proyecto.md`
  (§4.6 y §7) y `azure-apps/partes.md` (Empleado/Recurso) deben describir el
  DNI canónico, la ficha de recurso y los métodos `recurso_dni`/`recurso_nombre`.

## Fuera de alcance (design §7)

Recursos sin `res.cif` o con `res.conide` a una ficha; alias de recurso;
guardar el DNI leído; re-casar en bloque lo ya ingerido (se reprocesa a mano,
DA8); alta manual o jornada de personas sin ficha en sv4; forzar la cuenta 0
por empresa (DA9).
