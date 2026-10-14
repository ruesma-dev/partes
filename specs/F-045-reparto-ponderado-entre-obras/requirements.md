<!-- specs/F-045-reparto-ponderado-entre-obras/requirements.md -->
# F-045 · Reparto ponderado de la jornada entre obras — Requisitos

**Solo sv3** (`services/partes-persistencia`): el cómputo de ordinarias y extras
de `conciliar_todos`. Sin cambios de esquema, ni en sv4 ni en sv5. Rigor
**crítico** (worker de producción; horas que acaban en nómina y en coste de
obra). Es la **fase 1** de lo pedido el 2026-10-14 (DA1): el reajuste en Sigrid de
lo ya registrado queda propuesto como **F-046** (design §8) y aquí solo se mide.

## Contexto (verificado en el código el 2026-10-14)

- `_reclasificar_extras_jornada` (sv3) agrupa por (recurso, día) **cruzando
  obras**: ordinarias finales = jornada del día `J`; extras = total − `J`.
- Si falta extra, **recorta** ordinarias empezando por el `registro_id` mayor
  (el último parte en llegar se queda las extras). Si sobra, **sube** solo la
  ordinaria de `registro_id` mayor y crea UNA extra negativa.
- Lo congelado (F-004, F-037 pareja) cuenta en el total y no se toca; si el día
  no cuadra sin tocarlo, no hay ningún split y sale un WARNING.
- Las líneas en la **papelera** (`parte_registros.deleted_at_utc`) entran hoy en
  el reparto: `fetch_registros_para_recurso` solo filtra el documento (DA9).

## Glosario

- **Grupo**: las líneas de un recurso en una fecha, de cualquier obra y parte.
- **Ordinaria / extra explícita**: `tipo_hora` `''`/`normal` o `extra`
  (incluida la `extra_auto` congelada). Las incidencias no participan.
- **Fija**: línea que el reparto no cambia: congelada (`_congelado`, con la
  pareja de F-037) u ordinaria con horas ≤ 0. La papelera queda fuera (DA9).
- **Ajustable**: ordinaria no fija. **Obra ajustable**: obra del grupo
  (`obra_ide`, `None` es una más) con ≥ 1 ordinaria ajustable y peso > 0; las
  ordinarias de una obra de peso ≤ 0 son fijas.
- **Peso de una obra**: horas de sus líneas ordinarias y extras explícitas NO
  fijas. **Peso de una línea**: sus horas.
- **`J'`** (jornada a repartir) = `J` − horas de las ordinarias fijas que cuentan.
- **Paso**: granularidad del reparto (R3). **Mayor resto**: R1–R2.

## Núcleo puro (`application/services/reparto_ponderado.py`)

- **R1.** `repartir(total, participantes, paso)` debe devolver una cuota por
  participante, múltiplo de `paso`, cuya suma sea **exactamente** `total`:
  suelo de `total × peso / Σpesos` al paso y, a los `k` de mayor resto, un paso
  más (`k` = lo que falta, en pasos).
- **R2.** El desempate debe ser determinista e independiente del orden de
  entrada: mayor resto; luego mayor peso; luego menor clave de llegada (la obra:
  su `registro_id` mínimo; la línea: su `registro_id`).
- **R3.** `elegir_paso(total, pesos)` debe devolver 0,5 si `total` y todos los
  pesos son múltiplos de 0,5; si no, 0,25 si lo son de 0,25; si no, 0,01 (DA5).
- **R4.** Con `total ≤ Σpesos` ninguna cuota debe superar su peso; con
  `total ≥ Σpesos` ninguna debe quedar por debajo (sin extras de signo cruzado).
- **R5.** CUANDO `total` es 0, todas las cuotas deben ser 0. SI no hay
  participantes con peso > 0, ENTONCES no debe repartir nada.
- **R6.** El módulo no debe importar nada de `infrastructure/` ni de red/BBDD.

## Reparto del día (día laborable con ordinarias)

- **R7.** CUANDO el grupo no tiene fijas, las ordinarias finales deben sumar
  `J`: cada obra ajustable recibe su cuota de `J` por R1 (pesos de obra) y,
  dentro de ella, sus ordinarias ajustables se reparten esa cuota por R1
  (pesos de línea). Cada línea con cuota ≠ horas genera un split: ordinaria =
  cuota, `extra_auto` = horas − cuota (puede ser negativa, DA6).
- **R8.** Las extras explícitas nunca cambian; una obra sin ordinarias
  ajustables no recibe ordinarias y sus extras quedan como están.
- **R9.** Una sola ordinaria en el grupo debe dar el mismo split que hoy
  (10 h ⇒ 8 + 2; 5 h ⇒ 8 + (−3); 8 h ⇒ ninguno).
- **R10.** El reparto debe hacerse también entre varias ordinarias de la
  **misma obra** el mismo día (DA3).

## Casos de aceptación (J = 8, paso 0,5; «ord + extra» por obra)

- **R11 · Ejemplo 1.** A 10 h y B 4 h ⇒ A **5,5 + 4,5**; B **2,5 + 1,5**
  (ordinarias 8, extras 6). Nunca A 8 + 2 y B 0 + 4.
- **R12 · Ejemplo 2.** A 5 h y B 4 h ⇒ A **4,5 + 0,5**; B **3,5 + 0,5**.
- **R13 · Caso real sin congelar.** 0678 4 h y 0704 8 h ⇒ 0678 **2,5 + 1,5**;
  0704 **5,5 + 2,5**.
- **R14 · Jornada incompleta en dos obras.** A 4 h y B 3 h ⇒ A **4,5 + (−0,5)**;
  B **3,5 + (−0,5)** (DA6).
- **R15 · Empate a tres.** A, B y C con 6 h cada una, en ese orden de llegada
  ⇒ A **3 + 3**; B y C **2,5 + 3,5**.
- **R16 · Línea pequeña.** A 9,5 h y B 0,5 h ⇒ A **7,5 + 2**; B **0,5 + 0**
  (sin split en B).
- **R17 · Una obra, dos líneas.** 6 h y 4 h en la misma obra ⇒ **5 + 1** y
  **3 + 1** (hoy 6 + 0 y 2 + 2).
- **R18 · Cuartos de hora.** A 7,75 h y B 2 h ⇒ paso 0,25: A **6,25 + 1,5**;
  B **1,75 + 0,25**.
- **R19 · Extra explícita.** A ordinaria 6 h; B ordinaria 4 h y extra
  explícita 2 h ⇒ pesos 6 y 6: A **4 + 2** (`extra_auto`); B ordinaria **4**,
  sin split, y su extra explícita 2 intacta.

## Lo que no cambia

- **R20.** Día no laborable (fin de semana o festivo del trabajador): todas las
  ordinarias ajustables pasan enteras a extra, como hoy.
- **R21.** Sin cambios: día laborable sin ordinarias; recurso sin código de
  hora extra (mensual MENC: aviso y nada); líneas sin recurso; incidencias, de
  día completo o parciales (no participan ni restan jornada); cálculo de `J`
  (F-015: `candef`, último laborable, excepciones, calendario degradado).

## Fijas (congeladas): modo residual

- **R22.** CUANDO el grupo tiene fijas, éstas no deben cambiar y sus
  ordinarias cuentan: se reparte `J'` entre las obras ajustables como en R7,
  con pesos de sus líneas no fijas (DA7).
- **R23.** SI `J' < 0`, o `J' ≠ 0` sin ninguna ordinaria ajustable, ENTONCES no
  debe generar ningún split del grupo y debe dejar el WARNING de hoy
  («NO se puede cuadrar sin tocar lineas CONGELADAS»).
- **R24 · Caso real (fase 1).** 0678 congelada con 8 + (−4) y 0704 8 h nueva
  ⇒ 0704 **0 + 8**: igual que hoy (lo arregla F-046).
- **R25.** CUANDO el reparto ideal del grupo (todas sus ordinarias y extras no
  incidencias como ajustables) cambiaría alguna línea congelada, debe dejar un
  WARNING con la fecha, el recurso, los `registro_id` y horas antes → después,
  sin nombres ni DNIs, y sumar 1 a `repartos_con_congeladas` en el resultado de
  `conciliar_todos`.
- **R26.** Una línea `congelada_por_pareja` (F-037) es fija a todos los efectos.
- **R27.** Una línea en la papelera no debe tener peso, ni contar en `J'`, ni
  recibir split; la lectura del repositorio debe traer `deleted_at_utc` (DA9).

## Integración y robustez

- **R28.** Los splits deben tener las mismas claves que hoy y `horas_norm` /
  `extra_horas` múltiplos del paso: `apply_extras_splits` no cambia.
- **R29.** Dos pasadas seguidas sobre el mismo estado deben dar los mismos
  splits, y el resultado no debe depender del orden de los registros.
- **R30.** Por grupo repartido con ≥ 2 obras o líneas, un INFO con fecha,
  recurso, `J`, paso y nº de obras y líneas; sin nombres ni DNIs.
- **R31.** Las dos copias de la regla de congelación, `jornada_resolver.py`,
  `orm_models.py`, sv4 y sv5 no deben cambiar (design §4).
- **R32.** `docs/ARCHITECTURE.md` (semántica 3), `docs/referencia/partes-proyecto.md`
  («Cómputo de extras») y `azure-apps/partes.md` (§3.3) deben describir el
  reparto ponderado y el modo residual.
