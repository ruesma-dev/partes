<!-- specs/F-034-escribir-solo-en-partes-abiertos/requirements.md -->
# F-034 · sv5 solo escribe en partes de Sigrid abiertos (estado 1, En registro) — Requisitos

**Servicios tocados: sv5** (SQL de escritura, relectura tras escribir, motivo) **y sv4**
(solo el resumen del modal tras registrar, DA7). Sin schema, sin cambio de contrato
sv4↔sv5 (mismo JSON). Rigor **crítico**. Petición del humano (2026-10-07): «solo se puede
escribir en partes abiertos (1 REG)»; primera de la cola el 2026-10-20.

## Contexto (lo que hay hoy en `dev` 4bda57e; detalle en `design.md` §1)

Tras F-031, sv5 **elige** bien: lee `partes_del_periodo` **dentro del lock** y escribe en el
En registro de mayor `ide` o crea un complementario. Pero ninguna sentencia del registro
**comprueba** `con.est` al escribir: el lock de sv5 no detiene a Administración, que puede
cerrar o contabilizar el parte en Sigrid entre la lectura y el `sql/write` (y entre los
lotes de 15 sentencias, que son transacciones distintas). Caminos de escritura:

| Camino | Sentencia | ¿Comprueba `est` al escribir? |
|---|---|---|
| Alta de línea (registro, aprobar y cola) | `stmt_insert_linea` | **No** |
| Pisado de conflicto confirmado | `stmt_borrar_linea` (`DELETE`) | **No** (y borra, ver DA4) |
| Reaprobación / synckey existente | ninguna (`ya_registrado`) | no escribe |
| Alta de parte (F-031 v5, común con porcentajes) | `stmts_crear_parte` | crea `est = 1`; no es línea |
| Reajuste F-046: guardia y `UPDATE` | `stmt_guardia_reajuste`, `stmt_actualizar_linea` | Sí, sin bloqueo de `con` |
| Reajuste F-046: extra nueva | `stmt_insertar_extra` | Solo indirecto (por su base) |
| F-024, F-019, `comprobar_asiento_analitico.py` | ninguna | no escriben en Sigrid |

## Glosario

- **Parte abierto**: `con.est = EST_PARTE_ACTIVO` (1, En registro). Cerrado = cualquier
  otro (3 Cerrado, 10 Imputado...), como F-031.
- **Guarda de parte abierto**: `EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK)
  WHERE c.ide = <hmoide> AND c.est = ?)` dentro de la propia sentencia de escritura.
- **Ventana**: el tiempo entre la elección del parte (dentro del lock) y el `commit`.
- **No escrita**: línea que el registro mandó a escribir y que, releída por synckey tras
  escribir, no está en el parte elegido.

## Requisitos

### Guarda en cada sentencia que toca líneas (sv5, infraestructura)

- **R1.** Toda sentencia de sv5 que inserte, actualice o borre una fila de `hmores` debe
  llevar la guarda de parte abierto sobre el parte de esa fila, con el estado como
  parámetro (`EST_PARTE_ACTIVO`) y `WITH (UPDLOCK, HOLDLOCK)` en la lectura de `con`.
- **R2.** `stmt_insert_linea` debe tomar `ide` de una subconsulta (`SELECT x.n ... FROM
  (SELECT ISNULL(MAX(ide),0)+1 AS n FROM hmores WITH (UPDLOCK, HOLDLOCK)) x WHERE ...`),
  nunca de un agregado con `WHERE` (que devuelve fila aunque la condición falle), y llevar
  la guarda sobre su `hmoide`. SI el parte no está abierto, ENTONCES afecta 0 filas.
- **R3.** `stmt_borrar_linea` debe llevar la guarda sobre `hmores.hmoide` de la fila
  borrada (mientras exista el `DELETE`, DA4). SI el parte no está abierto, 0 filas.
- **R4.** La línea de un conflicto confirmado (pisado) debe insertarse solo si ninguna de
  sus líneas pisadas sigue con horas: `NOT EXISTS (SELECT 1 FROM hmores p WHERE p.ide IN
  (<pisadas>) AND ISNULL(p.can, 0) <> 0)`. Así, si la guarda impidió el pisado, la línea
  nueva no duplica horas. Sin pisadas, la condición no aparece.
- **R5.** `stmt_guardia_reajuste` y `stmt_actualizar_linea` (F-046) deben leer `con` con
  `WITH (UPDLOCK, HOLDLOCK)`; su condición y parámetros de estado no cambian.
- **R6.** `stmt_insertar_extra` (F-046) debe llevar además la guarda sobre su `hmoide`.
- **R7.** F-034 no debe añadir ningún `DELETE` nuevo ni ninguna escritura en `con`/`hmo`
  de un parte existente; `stmts_crear_parte` y `estado_parte.py` no cambian (DA6).

### Dentro del lock y justo antes de escribir (sv5, aplicación)

- **R8.** La elección del parte, la construcción de las sentencias y la llamada a
  `escribir`/`escribir_lote` deben seguir ocurriendo bajo `RegistroPipeline.lock` (el del
  reajuste es el mismo); la comprobación final del estado es la guarda de R1, evaluada por
  SQL Server en el mismo instante de la escritura.

### Lo que no entra (sv5, aplicación)

- **R9.** CUANDO termina `escribir`, el registro debe releer por synckey las líneas
  enviadas y dar por escritas solo las que estén en el `hmoide` elegido; las demás salen de
  `escritas` y van a `omitidas` con el motivo de R11 (DA2), nunca como `registrado`.
- **R10.** CUANDO hay no escritas, sv5 debe releer `partes_del_periodo` una vez por periodo
  afectado (dentro del lock) para nombrar el estado del parte; sin no escritas, no lee.
- **R11.** El motivo debe empezar por `parte_no_abierto`, nombrar el código del parte que
  lo impidió (el elegido o, si es el de sus pisadas, ese) y su estado (`nombre_estado`:
  Cerrado, Imputado o «estado N») y decir que se reaprueba; sin nombres ni DNIs y ≤ 255
  caracteres (texto en DA3). SI ninguno de esos partes está cerrado en la relectura,
  ENTONCES el motivo empieza por `no_escrita` y se registra un ERROR (no debería ocurrir).
- **R12.** `ResultadoRegistro.borradas` debe contar las pisadas que **ya no están** en
  Sigrid tras escribir (relectura por `ide`), no las sentencias enviadas.
- **R13.** CUANDO hay no escritas, sv5 debe registrar un WARNING `[registro] no escritas
  por parte no abierto` con obra, periodo, código, estado y `registro_id`, sin nombres.
- **R14.** SI la relectura de R9, R10 o R12 falla, ENTONCES la petición falla entera
  (excepción, como hoy): sv4 la marca `error` y reaprobar es seguro por synckey.

### Comportamiento que se conserva (caracterización)

- **R15.** MIENTRAS el periodo no tenga parte abierto, las líneas deben ir al
  complementario (F-031 R2–R4); una con horas ajenas en un parte cerrado se omite
  `parte_cerrado` (F-031 R11).
- **R16.** CUANDO se reaprueba una línea cuya synckey ya está en Sigrid, aunque su parte
  esté cerrado, sv5 debe devolverla `ya_registrado` sin enviar ninguna sentencia.
- **R17.** El reajuste F-046 de una línea en un parte cerrado sigue sin editarse: no
  editable, lote rechazado (F-046 R21, DA10); una ya aplicada se reconoce (R26).
- **R18.** El alta del parte (`_crear_parte`) no cambia: un parte que sv5 crea nace En
  registro y la guarda de R2 lo acepta.

### Portal (sv4)

- **R19.** CUANDO el modal pinta el resultado de un registro con omitidas, debe agruparlas
  por motivo (el texto antes de los primeros dos puntos, o el motivo entero si no los
  tiene, con su número) en vez de «(reglas)», escapado; el texto completo de cada motivo
  sigue en el `title` del badge `omitido` (DA7). Sin omitidas, el modal no cambia.
- **R20.** La línea no escrita debe quedar `omitido` con el motivo de sv5 y poder
  reaprobarse (`ESTADOS_REAPROBACION` ya lo incluye): sin cambio en el repositorio.

### Documentación

- **R21.** `docs/ARCHITECTURE.md` (semántica 16) y `azure-apps/partes.md` deben decir que
  toda escritura de línea de sv5 lleva la guarda de parte abierto y qué ve el usuario; la
  nota a `porcentajes` (DA6) queda en `azure-apps/partes.md`.

## Ejemplos (datos sintéticos)

1. Obra X, 10/2026, `PT26/00314` En registro. Se aprueban 3 líneas; antes del `commit`
   Administración lo pasa a Cerrado. Las 3 `INSERT` afectan 0 filas; sv5 devuelve
   `escritas=[]` y 3 `omitidas` «parte_no_abierto: el parte PT26/00314 ya no esta En
   registro (Cerrado)...». Al reaprobar, F-031 crea el complementario `PT26/00400`.
2. Pisado confirmado de una línea ajena en `PT26/00314`, que se cierra en la ventana: el
   `DELETE` afecta 0 filas, la ajena sigue con horas, la nueva no entra (R4), `borradas=0`
   y la nueva sale `parte_no_abierto`. Sin R4 quedarían horas duplicadas.
3. Reaprobar una línea ya escrita en `PT26/00314` (ahora Imputado): `ya_registrado`, 0
   sentencias (R16).
4. Reajuste F-046 de una línea en un parte Imputado: rechazado «su parte de Sigrid no esta
   En registro (estado 10)», sin escribir (R17).
