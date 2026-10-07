# F-035 · Portal: elegir trabajador entre recursos activos de Sigrid, por empresa — Requisitos

**Servicio tocado: solo sv4** (`services/partes-front/`), más el guardián de la
raíz `tests/test_f023_de_alta_gemelos.py`. sv3 y sv5 **no cambian**: siguen
eligiendo el recurso por DNI y empresa de la obra. Sin cambio de schema.
Rigor **estándar** (justificación en design §7). Alcance mínimo pedido por el
humano el 2026-10-07.

## Contexto

Los selectores de trabajador del portal tiran del catálogo de **empleados**
(`emp`, `_SQL_EMPLEADOS`). Quien solo tiene **recurso** de mano de obra en
Sigrid (sin ficha `emp`, el caso de F-030) no aparece: en Conciliar no se le
puede casar ni elegir al crear un parte. Además no se puede elegir la empresa,
y en el detalle de una obra salen trabajadores de cualquier empresa aunque la
fila de obra es de una sola (la 0678 existe en Ruesma y en Porsan).

## Glosario

- **Recurso activo** (criterio de persona de `porcentajes`, decisión del
  humano 2026-10-07): fila de `res` de **clase persona** (`res.cla = 1`), una
  por recurso, cuyo concepto (`con` del recurso) está de alta **hoy** (regla
  F-023: `fecbaj` NULL, 0 o mayor que hoy) y que tiene **DNI**. Sin filtro por
  prefijo de código ni por ficha, y sin el filtro de hora mensual (propio de
  porcentajes). F-036 reutilizará este mismo criterio en sv3.
- **DNI del recurso**: `res.cif`; si está vacío, `emp.dni` de la ficha
  enlazada.
- **Ficha enlazada**: la fila `emp` con `emp.ide = res.conide` y
  `res.conide > 0`, si existe.
- **Empresa del recurso**: `con.emp` del recurso.
- **Selector de empresa**: `<select>` con «Todas» y las empresas de
  `NOMBRES_EMPRESA` (F-033: 1 Ruesma, 28 Porsan).

## Requisitos

### Fuente única de recursos activos

- **R1.** sv4 debe obtener los recursos activos con UNA consulta paginada a
  sigrid-api (`_SQL_RECURSOS_ACTIVOS`) que aplica la regla de alta F-023 a hoy
  sobre el concepto del recurso, y cachearlos con TTL (como `EmpleadoCatalog`).
- **R2.** Cada recurso ofrecido debe llevar: `ide` (`res.ide`), `codigo` (código
  del recurso), `nombre` (`con.res` del recurso), `dni` (DNI del recurso),
  `empresa`, y `empleado_ide`, `empleado_codigo`, `empleado_nombre` y
  `empleado_dni` de la ficha enlazada (nulos sin ficha), `categoria` y `candef`.
- **R3.** SI un recurso sigue sin DNI tras el respaldo de la ficha (ni
  `res.cif` ni `emp.dni`), ENTONCES no se ofrece (sv3 y sv5 identifican por
  DNI: la línea quedaría «sin recurso»).
- **R4.** SI un recurso no es de clase persona (`res.cla` distinto de 1:
  consumo, medio), ENTONCES no se ofrece.
- **R5.** `GET /api/sigrid/recursos?empresa=N` debe devolver solo los recursos
  de la empresa N; sin `empresa`, todos. Cada item añade `jornada_sugerida`
  (misma regla que `/api/sigrid/empleados`). Sin Sigrid configurado o con
  error, `ok: false` e `items: []`.
- **R6.** SI el refresco del catálogo falla, ENTONCES se sirve la última lista
  buena (vacía si nunca cargó) y se registra un WARNING.

### Conciliar

- **R7.** Los candidatos de cada tarjeta de Conciliar deben calcularse sobre
  los recursos activos de la empresa por defecto de la tarjeta (R8); un
  trabajador con recurso y sin ficha de empleado debe poder salir como
  candidato.
- **R8.** Cada tarjeta debe tener un selector de empresa cuyo valor inicial es
  la empresa de sus partes (`parte_documents.empresa`) si es una sola; con
  varias o ninguna, «Todas».
- **R9.** `/api/conciliacion/buscar` debe aceptar `empresa` y buscar solo entre
  los recursos activos de esa empresa (sin ella, entre todos).
- **R10.** Cada fila de candidato debe llevar `data-empresa` y el nombre de su
  empresa; CUANDO se cambia el selector, la tarjeta oculta los candidatos de
  otra empresa y la búsqueda manual usa la empresa nueva.

### Qué se guarda al elegir un recurso

- **R11.** `/api/conciliacion/confirmar` y `/api/empleado/reasignar` deben
  aceptar `recurso_ide` y resolverlo en el catálogo de recursos; SI no está,
  ENTONCES 404 sin tocar nada.
- **R12.** CUANDO el recurso tiene ficha enlazada, la línea debe quedar con
  `empleado_ide`, `empleado_codigo` y `empleado_nombre` de la ficha (como
  hoy), `empleado_dni` = `emp.dni` de la ficha si no está vacío y, si no, el
  DNI del recurso (el orden con que sv5 verifica, design §7), y
  `empleado_reside` = `res.ide`; el resto del recurso se suelta como en
  F-023 (R42).
- **R13.** CUANDO el recurso no tiene ficha enlazada, la línea debe quedar con
  `empleado_ide` NULL, `empleado_codigo`/`empleado_nombre` del recurso,
  `empleado_dni` = `res.cif`, `empleado_reside` = `res.ide` y
  `empleado_match_method` = `recurso_manual`; cuenta como casada (`esta_casado`)
  y sale de la cola de Conciliar.
- **R14.** CUANDO el recurso no tiene ficha enlazada, no se escribe alias
  (F-030: el alias es solo de fichas de empleado).
- **R15.** Una petición con `ide` y sin `recurso_ide` debe seguir el camino de
  empleados de siempre, sin cambios (compatibilidad con JS en caché).
- **R16.** Deshacer una asignación debe restaurar también `empleado_reside` y
  `empleado_match_method`; un snapshot antiguo sin esas claves no falla.

### Parte nuevo y añadir línea

- **R17.** El selector de trabajador de «Nuevo parte» y del modal «+ Añadir
  línea» debe listar los recursos activos (R5) de la empresa del selector de
  empresa (R18), mostrando código, nombre, DNI y empresa.
- **R18.** Ambos formularios deben tener un selector de empresa; CUANDO hay
  obra con empresa (elegida o fijada por la página), toma esa empresa y queda
  bloqueado (DA1); sin obra, es libre y empieza en «Todas».
- **R19.** Al crear, el payload debe llevar `empleado_reside` = `res.ide`
  (también desde el modal, que hoy no lo envía) y los `empleado_*` de R12/R13;
  el servidor guarda `recurso_ide` = `empleado_reside` (como hoy) y, si
  `empleado_ide` es nulo y `empleado_reside` no, `empleado_match_method` =
  `recurso_manual`.

### Detalle de obra

- **R20.** El combo de trabajador de cada línea del detalle de obra debe
  ofrecer solo recursos activos de la empresa de la ficha de obra
  (`obra_catalog` por `obra_ide`); SI no se conoce, todos.
- **R21.** Elegir en ese combo (y en «Reasignar a…» del listado de
  trabajadores, que comparte el combo y no filtra empresa) debe enviar
  `recurso_ide`.

### Compatibilidad y límites

- **R22.** `/api/sigrid/empleados`, `_SQL_EMPLEADOS`, `EmpleadoCatalog` y la
  pantalla de jornadas no cambian; tampoco el schema, sv3 ni sv5. La suite de
  sv4 sigue en verde sin tocar tests ajenos.
- **R23.** El guardián `tests/test_f023_de_alta_gemelos.py` debe vigilar
  también la regla de alta de `_SQL_RECURSOS_ACTIVOS` (DA2).
- **R24.** `docs/ARCHITECTURE.md` (semántica 12) y la lista cerrada de
  `CLAUDE.md` deben reflejar el nuevo SQL de sv4.

## Fuera de alcance

Cambios en sv3/sv5: el casado de sv3 contra recursos con este criterio es
F-036 (otra spec); aquí no se copia lógica a sv3. Alias de recursos,
filtro de empresa en el listado de trabajadores, jornada del día
(`jornada_dia`) en el nuevo endpoint, reprocesar líneas ya casadas.

## Trazabilidad

Cada R tiene al menos un test `test_f035_rN_...` (design §6); R10, R17, R18 y
la parte JS de R20–R21 se validan con atributos del HTML renderizado,
`node --check` y verificación manual (tasks T7).
