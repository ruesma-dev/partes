<!-- specs/F-046-reajuste-en-sigrid-al-aprobar/requirements.md -->
# F-046 · Reajuste en Sigrid al aprobar — Requisitos

**Depende de F-045** (se implementa sobre `dev` con F-045 fusionada; usa su API pura
`reparto_ponderado.py`). Toca **sv3, sv4 y sv5** y el esquema (tabla nueva, las dos copias
del ORM): por qué cada uno, en design §1. Rigor **crítico**: edita horas ya registradas en
el ERP de producción (nómina y coste de obra) y añade estado compartido en la base `partes`.
Pedido por el humano el 2026-10-14: si el primer parte del día ya está aprobado o registrado
en Sigrid, se edita al aprobar el segundo, con aviso previo. Decisiones: design §6 (DA1–DA17).

> **Enmienda del humano (2026-10-14), marcada «[E]»**: Sigrid no se borra nunca, solo se
> editan líneas (R24, R47); y el viernes de candef 9 tiene otra jornada (R9a–R9c, R46).

## Glosario

- **Grupo**: líneas de un recurso en una fecha, de cualquier obra (como F-045).
- **Congelada reajustable**: congelada (F-004/F-037) en `registrado`, o solo por parte
  aprobado (sin estado, `omitido`, `error`, `conflicto`, `borrado_sigrid`). **Dura**: `encolado`,
  `dedicacion`, ordinaria con horas ≤ 0, pareja con más de una extra automática, o en papelera.
- **Ideal**: reparto F-045 del grupo con las duras fijas y las reajustables como ajustables
  (peso de una base = `horas_orig` si no es nulo; extra de su pareja = trabajado − cuota).
- **Reparto**: fila de `reparto_pendiente` con las líneas congeladas antes → después.
- **Interruptor**: `REPARTO_REAJUSTE` de sv3 (defecto `false`).

## Núcleo puro (sv3, `reparto_ponderado.py`)

- **R1.** `proponer_dia(lineas, jornada)` debe devolver los `Ajuste` de las líneas no
  congeladas y un `CambioCongelada(registro_id | None, base_registro_id, tipo, antes, despues)`
  por cada línea reajustable cuyo ideal difiere; `registro_id` None = extra nueva de una base.
- **R2.** Sin duras, sus cambios deben coincidir con `diferencias_ideal` de F-045.
- **R3.** Las duras y las extras explícitas no deben cambiar nunca; cuentan en el total.
- **R4.** SI con las duras fijas el día no cuadra (F-045 R23), ENTONCES sin cambios ni ajustes.
- **R5.** El módulo sigue sin importar `infrastructure/`, red ni BBDD.

## Casos de aceptación (J = 8, paso 0,5; «ord + extra»)

- **R6 · Caso real.** 0678 registrada 8 + (−4) (`horas_orig` 4) y 0704 nueva 8 h ⇒ 0704
  **5,5 + 2,5** aplicado; cambios 0678: ordinaria **8 → 2,5**, extra **−4 → 1,5**.
- **R7 · Extra nueva.** 0678 registrada 8 sin extra y 0704 nueva 4 h ⇒ 0704 **2,5 + 1,5**;
  0678 ordinaria **8 → 5,5** y extra nueva **2,5**.
- **R8 · Extra a cero.** 0678 registrada 8 + (−2) (`horas_orig` 6) y 0704 nueva 2 h ⇒ 0704
  **2 + 0**; 0678 ordinaria **8 → 6** y extra **−2 → 0**.
- **R9 · Dura.** El caso de R6 con la 0678 `encolado` ⇒ sin propuesta y 0704 **0 + 8** (F-045).

**[E] Candef 9** (F-015: 9 h de lunes a jueves; último laborable 42 − 4 × 9 = 6 h):

- **R9a · Viernes, J = 6.** A 5 h y B 4 h, sin congelar ⇒ A **3,5 + 1,5**; B **2,5 + 1,5**
  (cuotas 3,33 y 2,67 ⇒ suelos 3 y 2,5; el medio paso que falta va al mayor resto, A).
- **R9b · Jueves, J = 9.** Mismas horas ⇒ A **5 + 0**; B **4 + 0** (sin splits).
- **R9c · Reajuste en viernes.** A registrada sola **6 + (−1)** (`horas_orig` 5) y B nueva
  4 h ⇒ B **2,5 + 1,5**; cambios A: ordinaria **6 → 3,5**, extra **−1 → 1,5**.

## sv3: propuesta y materialización

- **R10.** MIENTRAS el interruptor esté apagado, sv3 debe comportarse exactamente como F-045
  (sus tests pasan sin tocarlos) y no debe leer ni escribir `reparto_pendiente`.
- **R11.** CUANDO el grupo tiene ≥ 1 ordinaria no congelada y el ideal cambia alguna
  reajustable, sv3 debe aplicar el ideal a las no congeladas y dejar el reparto `pendiente`
  con su firma y sus cambios (obra, documento, día, tipo, `sigrid_estado`, antes, después).
- **R12.** Sin ordinarias no congeladas en el grupo, no debe proponer nada (modo F-045).
- **R13.** CUANDO la firma del grupo (líneas, horas, `horas_orig`, estados) no cambia, la
  pasada no debe tocar el reparto; si cambia, el anterior pasa a `obsoleto` y, si procede, nace
  otro `pendiente`. Uno en `aplicando` o `aplicado` no pasa nunca a `obsoleto`.
- **R14.** CUANDO el reparto está `rechazado` (o `mantenido`) con la firma vigente, sv3 debe
  repartir en modo residual (F-045 R22) y pasarlo a `mantenido`.
- **R15.** CUANDO el reparto está `aplicado`, sv3 debe, ANTES de repartir el grupo, llevar
  a `partes` exactamente sus valores «después» (excepción acotada a la congelación, R33):
  horas de cada línea, `horas_orig` de la base si era nulo, y cada extra nueva con el
  `registro_id` reservado, clonada de su base como `apply_extras_splits`; y pasarlo a `materializado`.
- **R16.** SI una línea del reparto `aplicado` ya no tiene horas = «antes» ni «después»,
  ENTONCES no debe tocar ninguna línea de ese reparto, debe dejar ERROR y contarlo.
- **R17.** Una extra nueva cuya base está `registrado` debe nacer `registrado` con el
  `hmores_ide`, `hmoide`, `parte_cod` y firma que sv5 devolvió (guardados en el reparto).
- **R18.** `conciliar_todos` debe ejecutarse bajo un candado consultivo de PostgreSQL de la
  base `partes` (sesión propia, `pg_try_advisory_lock` con espera acotada); SI no lo obtiene a
  tiempo, ENTONCES debe lanzar (el mensaje se reintenta). Sin PostgreSQL, sin candado.
- **R19.** El resultado de `conciliar_todos` debe contar `repartos_propuestos`,
  `repartos_materializados`, `repartos_mantenidos` y `repartos_descuadrados`, con un INFO por
  reparto (fecha, recurso, ids, antes → después), sin nombres ni DNIs.

- **R46 · [E] Jornada de sv3.** `J` de cada grupo debe ser la que F-045 obtiene de
  `_detalle_jornada` (F-015, `jornada_resolver.py`); F-046 no calcula jornada por su cuenta.

## sv5: reajuste en Sigrid

- **R20.** `POST /api/reajuste/comprobar` (solo lectura, sin lock) debe dar por línea
  `editable` y motivo; `POST /api/reajuste/ejecutar` debe escribir bajo el MISMO lock que el
  registro. Entrada: líneas con `registro_id`, `antes`, `despues` y, si es nueva, su base,
  recurso, fecha, código de hora extra, partida y obra; tope de 50 líneas (422 si no).
- **R21.** Una línea existente es editable solo si: su synckey `partes:<registro_id>` existe,
  su parte (`hmo`) está En registro (`EST_PARTE_ACTIVO`), sus enlaces (`dvaproide`,
  `dvfproide`, `hdereside`, `emprccide`, `empdpreide`, `empabside`) son 0 o nulos y `can` vale
  «antes» (o «después»: ya aplicada) con tolerancia 0,001.
- **R22.** Una extra nueva es editable solo si su synckey no existe (o existe con «después»),
  su base lo es, el recurso pasa `preparar` (reglas y cuenta F-021) como `escribir` y no hay
  línea ajena del mismo recurso, día y código de hora en los partes En registro del periodo.
- **R23.** SI alguna línea no es editable, ENTONCES `ejecutar` no debe escribir nada y debe
  devolver `ok: false` con el veredicto de cada línea.
- **R24.** Debe escribir en UNA llamada a `sql/write` (un lote, una transacción): `UPDATE` de
  `can` y `tot = ROUND(can × pre, 2)` con el `pre` de la propia línea (nunca `caaide`, `paride`
  ni `horide`) y `INSERT` de cada extra nueva en el `hmoide` de su base (pos, cuenta, `tex`
  como el registro). **[E]** Una línea que queda a 0 se actualiza a `can = 0`, `tot = 0`.
- **R47 · [E] Sin borrados.** Los lotes de reajuste de sv5 no deben contener ningún `DELETE`
  ni pasar por `stmt_borrar_linea`: solo `UPDATE` de líneas existentes e `INSERT` de extras nuevas.
- **R25.** Cada sentencia debe llevar en su `WHERE` la condición optimista (synckey, `can` =
  «antes», parte En registro) y el lote debe abortar entero si alguna no se cumple (DA6).
- **R26.** Repetir `ejecutar` con lo ya aplicado debe ser `ya_aplicada` sin escribir.
- **R27.** SI el lote supera `SIGRID_MAX_STATEMENTS`, ENTONCES no editable («demasiadas líneas»).
- **R28.** En modo pruebas (`OBRA_PRUEBAS_FORZAR`), la extra nueva va a la 0404 con
  `PRUEBA-IA` en `tex`; las actualizaciones no cambian `tex`.
- **R29.** Log por línea (ide, antes, después, usuario) sin nombres ni DNIs.

## sv4: aviso y decisión

- **R30.** CUANDO el preflight de aprobar incluye líneas de un grupo con reparto `pendiente`,
  la respuesta debe traer `repartos`: por reparto, día y por línea obra, parte de Sigrid, tipo,
  horas antes → después y si es editable (sv5 `comprobar` para las `registrado`).
- **R31.** El modal debe avisar antes de aprobar y ofrecer «Aplicar» y «Mantener lo
  registrado»; si algún reparto no es editable, ese solo admite «Mantener» con su motivo.
- **R32.** `ejecutar` y `encolar` deben aceptar `repartos: [{id, decision}]`. Sin decisión, las
  líneas de un grupo con reparto `pendiente`, `aplicando` o `rechazado` no viajan
  (`excluidas.reparto_pendiente`, con motivo en `excluidas_detalle`).
- **R33.** «Aplicar» debe: (1) pasar el reparto de `pendiente` a `aplicando` solo si sus líneas
  siguen con las horas y estados «antes», el grupo no tiene líneas nuevas y ningún documento
  suyo está en espera (F-043); si no, 409 sin tocar nada; (2) reservar los `registro_id` de las
  extras nuevas (secuencia de `parte_registros`); (3) llamar a sv5 `ejecutar` (HTTP síncrono)
  con las `registrado`; (4) si va bien, `aplicado` con el resultado y pedir el recálculo
  seguido (F-043, motivo `reajuste_reparto`) de sus documentos; y (5) registrar el lote.
- **R34.** SI sv5 rechaza el reajuste, ENTONCES el reparto vuelve a `pendiente` con el error y
  las líneas del grupo no se registran; SI no hay respuesta (timeout), sigue `aplicando` y
  «Aplicar» se puede reintentar (R26 lo hace seguro).
- **R35.** «Mantener lo registrado» debe pasar el reparto a `rechazado` (CAS), pedir el
  recálculo seguido de los documentos de sus líneas no congeladas y no registrarlas en ese clic.
- **R36.** Aprobar un documento (`/documents/{id}/approve`) con líneas en un grupo con
  reparto `pendiente`, `aplicando` o `rechazado` debe rechazarse con un motivo que lo explique.
- **R37.** Las vistas de obra y trabajador deben marcar «reparto pendiente» en la matriz y en
  las líneas afectadas de todas las obras del grupo.
- **R38.** Toda decisión firma con `_actor(request)` recibido por parámetro (F-017) y queda en
  el reparto (`decidido_por`, `decidido_at_utc`, `decision`); no entra en `undo_log`.

## Esquema, congelación y lo que no cambia

- **R39.** Tabla `reparto_pendiente` en las dos copias de `orm_models.py` (byte-idénticas),
  sin nombres ni DNIs; los guardianes de tablas pasan a SIETE con su lista literal.
- **R40.** `esta_congelado`, `ESTADOS_CONGELADOS` y `motivo_congelacion_linea` no cambian (el
  gemelo de F-024 pasa sin tocarlo); la única escritura sobre congeladas es la de R15.
- **R41.** No cambian `estado_parte.py`, `cuenta_analitica.py`, el alta de partes, el contrato
  de `q-transfer`, `jornada_resolver.py` ni el registro normal de sv5.
- **R42.** `docs/ARCHITECTURE.md`, `docs/referencia/partes-proyecto.md` y
  `azure-apps/partes.md` deben describir el reajuste, la tabla y la escritura `UPDATE hmores`.
