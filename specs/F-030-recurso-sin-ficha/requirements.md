<!-- specs/F-030-recurso-sin-ficha/requirements.md -->
# F-030 · Trabajador con recurso en Sigrid pero sin ficha: casar el recurso por DNI

Humano, 2026-10-05. Rigor **crítico** (cambia qué recurso se escribe en Sigrid).
Caso real: partes de Porsan (empresa 28, obra 0724, membrete resuelto) con un
trabajador cuyo recurso `MO/` de alta tiene `res.cif` = su DNI pero no tiene
ficha `emp`: hoy sale `empleado_match_method='none'` y «Sin recurso». Datos
medidos (solo lectura, agregados): design §1. **DA1–DA9 a aprobar antes de
implementar** (design §8). Toca sv3 y sv4; sv5 solo gana tests (design §2).

Glosario. **DNI canónico**: el DNI normalizado (`text_match.normalize_dni`) y,
si son de 1 a 7 dígitos y una letra, completado con ceros a la izquierda hasta
8 dígitos (Sigrid los guarda siempre con 8). **Casado por recurso**: trabajador
identificado solo por un recurso (`res.cif`), sin ficha; método `recurso_dni`.
**Candidato** (F-023): recurso de alta a la fecha D y de la empresa E.

## A. DNI canónico (sv3)

- **R1.** El sistema debe calcular el DNI canónico así: `normalize_dni` y, SI
  el resultado casa con `^[0-9]{1,7}[A-Z]$`, ceros a la izquierda hasta 8
  dígitos; cualquier otra forma (8 dígitos, NIE, CIF, vacío) queda igual.
- **R2.** CUANDO sv3 normaliza un parte, el `trabajador_dni_leido` de cada
  registro debe ser el DNI canónico del leído, o None si no se leyó.
- **R3.** CUANDO el DNI leído es el de una ficha sin el cero inicial, el
  trabajador se debe casar por DNI (`dni`) con esa ficha (F-023 R18).

## B. Casado por recurso sin ficha (sv3, ingesta)

- **R4.** CUANDO `elegir_ficha` devuelve `desconocido` para el DNI leído (no hay
  ninguna ficha con ese DNI), sv3 debe buscar el recurso, **antes** del alias y
  del nombre, con `IndicePersonas.elegir_recurso(dni, None, None, empresa del
  parte, fecha del parte)`.
- **R5.** SI R4 da un recurso (`ok`), ENTONCES el trabajador queda casado por
  recurso: `empleado_ide`, `empleado_codigo` y `empleado_reside` NULL;
  `empleado_dni` = `res.cif` del recurso tal como está en Sigrid;
  `empleado_nombre` = nombre del recurso; score 1.0; método `recurso_dni`.
- **R6.** SI R4 no da recurso (`desconocido`, `solo_baja`, `otra_empresa` o
  `ambiguo`), ENTONCES el casado sigue como hoy (alias y después nombre) y,
  salvo `desconocido`, se loguea INFO con el motivo, sin DNI ni nombre (DA5).
- **R7.** SI `elegir_ficha` da `ambiguo`, `solo_baja` u `otra_empresa`,
  ENTONCES no se busca recurso: rige F-023 R19–R22 sin cambios.
- **R8.** Un trabajador sin DNI leído nunca se casa por recurso: el nombre no
  se compara con recursos (DA1).
- **R9.** sv3 debe leer el nombre del recurso (`con.res`) en la misma lectura
  paginada de recursos y exponerlo en `RecursoRow.nombre`.
- **R10.** `review_required` no debe subir por un trabajador casado por
  recurso; sigue subiendo por todo trabajador con `empleado_ide` NULL y otro
  método (DA3).

## C. Conciliación del recurso (sv3, sin cambio de código)

- **R11.** CUANDO el conciliador procesa una línea `recurso_dni` no congelada,
  debe asignarle el único candidato con `res.cif` = su `empleado_dni`, de alta
  a la fecha de la línea y de la empresa de su obra (F-023 R25–R29), dejar
  `parte_estado` `ok` o `sin_parte` y pisar categoría y hora con ese recurso.
- **R12.** CUANDO una línea `recurso_dni` entra en el reparto de extras por
  jornada, el `candef` sale de la ficha del recurso y el calendario laboral se
  pide con su `empleado_dni`, igual que con ficha.

## D. Coherencia con sv5 (sin cambio de código; lista cerrada intacta)

- **R13.** F-030 no debe modificar `de_alta` ni `IndicePersonas.elegir_recurso`
  (sv3), ni `de_alta`, `elegir_por_dni` ni `verificar_recurso` (sv5) (DA6);
  `tests/test_f023_de_alta_gemelos.py` sigue verde sin tocarlo.
- **R14.** CUANDO sv5 verifica un recurso elegido por R11 sin ficha enlazada
  (`res.conide` 0) y la línea trae `empleado_dni` = su `res.cif`, la
  verificación debe pasar (empresa, alta y persona).
- **R15.** SI el recurso tiene `res.conide` hacia una ficha con otro DNI no
  vacío, ENTONCES sv5 lo omite con el motivo de otra persona (F-023 R36, sin
  cambios): nunca se escribe a ciegas.

## E. Portal (sv4)

- **R16.** sv4 debe considerar casado un registro con `empleado_ide` o con
  método `recurso_dni`, decidido en un único helper que usan las vistas de
  parte, obra, lista de trabajadores y trabajador.
- **R17.** CUANDO una de esas vistas muestra un trabajador `recurso_dni`, debe
  mostrar «Casado por recurso (sin ficha)» en lugar de «Sin casar».
- **R18.** La cola de conciliación (`list_unmatched_workers`) y su
  confirmación por nombre leído deben excluir los registros `recurso_dni`.
- **R19.** Catálogo de empleados, alta manual y reasignación no cambian:
  reasignar a una ficha una línea `recurso_dni` la deja casada por ficha y
  suelta su recurso (F-023 R42).

## F. Cuenta analítica en Porsan (sv5, sin cambio de código)

- **R20.** CUANDO sv5 prepara una línea `escribir` de un recurso sin cuenta en
  ninguna fila de `reshor` (todos los de la empresa 28 hoy), la cuenta debe
  ser `caa_ide = 0`, motivo `recurso_sin_cuenta` y sin aviso (F-021 R3; DA9).

## G. Documentación

- **R21.** `docs/ARCHITECTURE.md` (semántica 2 y 12), `partes-proyecto.md`
  (§4.6 y §7) y `azure-apps/partes.md` (Empleado/Recurso) deben describir el
  DNI canónico, el casado por recurso sin ficha y el método `recurso_dni`.

## Fuera de alcance (design §7)

Casar por nombre contra recursos; rellenar `empleado_ide` desde `res.conide`;
guardar el DNI leído en `parte_registros`; re-casar en bloque los partes ya
ingeridos (se reprocesan a mano, DA8); alta manual o jornada de personas sin
ficha en sv4; forzar la cuenta 0 por empresa (DA9).
