<!-- progress/spec_F-031.md -->
# F-031 · Resumen de la spec para el humano (spec-author, 2026-10-05, v4)

Spec: `specs/F-031-asiento-analitico/` (requirements, design, tasks). Rama
`feature/F-031-asiento-analitico`. Estado: `spec_ready`. Rigor crítico.
Versión 4: aplica las dos decisiones del 2026-10-05 (complementario y
cuenta del recurso).

## En una frase

Sigrid ya genera el asiento analítico de cada parte al «Contabilizar». sv5
no escribe asientos; tiene que (1) **no meter líneas en un parte cerrado**,
sino en un **parte complementario** de la misma obra y mes, y (2) seguir
poniendo **la cuenta del recurso** (F-021), con la de la partida solo de
respaldo.

## Qué cambia respecto a la v3

- **DA1/DA2 → complementario** (antes: omitir hasta que Administración
  reabriera, y escribir en los Cerrados). sv5 escribe solo en un parte En
  registro de esa obra y mes: si existe, lo reutiliza; si no, crea uno nuevo
  como hoy (`PT..` de la empresa, En registro, `Parte <obra>`). El original
  no se toca. Duplicados y pisado se miran en todos los partes del mes; una
  línea que choca con horas de un parte cerrado se omite con motivo. El
  modal rotula «complementario» y explica a dónde van las líneas.
- **DA6 → la cuenta sale del recurso** (antes: la partida mandaba). F-021 no
  cambia. Nuevo solo el respaldo: si el recurso no tiene cuenta, la de la
  partida si es `CI..`/`CD..` (544 líneas en 2026, 478 llevaban esa). Se
  retiran R17–R19 de la v3, la nota por línea de partida sin cuenta y la
  pregunta DA6-e (ya no aplica).
- Sin cambios: DA3 (fuera; borrador a Juan hecho), DA4 (sv5 no contabiliza
  ni cambia estados), DA5, DA7, DA8. Ningún test de F-021 cambia.

## PARA CONFIRMAR: qué es un parte «cerrado» (interpretación del líder)

Tu frase: «juan ha dicho que si hay modificar un parte ya cerrado se hace
con complementario». La spec entiende **«cerrado» = cualquier parte del mes
que no esté En registro (Cerrado o Imputado)**. Consecuencia: en agosto
(38 partes Cerrados, ninguno contabilizado) las líneas nuevas irían a
complementarios. Si para Juan «cerrado» es solo **Imputado** (contabilizado)
y en un Cerrado se puede seguir escribiendo, dímelo: cambia un único
predicado (design §8) y R2/R3/R11.

## Riesgos y fuera de alcance

Carrera de segundos con un «Contabilizar» simultáneo (aceptado; la
herramienta lo detecta); complementarios de pocas líneas si se aprueba
tarde. Fuera: escribir asientos o cambiar estados; contrapartidas (DA3); los
31 asientos que no cuadran; recalcular líneas ya escritas; Porsan; sv1–sv3
y la base `partes`.

## Anexo · datos (solo lectura vía sigrid-api, base `ruesma`, 2026-10-05; agregados, sin nombres ni DNIs)

- **§D1 Tablas.** `asi` asientos contables (`con.tip` 20); `asa` asientos
  analíticos (`con.tip` 32, 5.771); `apu` apuntes contables; `apa`
  desglose/apuntes analíticos (`conide` → asiento, `cenide`, `cueide` →
  `caa`, `deb`, `hab`; 715.018); `salapa` saldos analíticos: 0 filas;
  `conest` estados; `log`. `hmores` no tiene campo de asiento.
- **§D2 Estados (`conest` tipo 35).** 1 REG «En registro»; 3 CER «Cerrado»
  (ADM, COS); 10 IMP «Imputado» (ADM, COS). Log: «Proceso de Cambio de
  estado (HMO Seleccionados: N): Contabilizar parte», lotes de 1–34; los
  más recientes 2026-03-02, 2026-09-02 y 2026-09-14.
- **§D3 Asiento por parte.** 2025–26: 497 asientos «Parte …» (todos empresa
  1): 497 casan con un `hmo` por empresa+resumen+fecha (495 también por
  centro). Debe = Σ `hmores.tot` con `caaide > 0`: 465 cuadran, 31 no, 1
  sin líneas. Ejemplo: obra 0696, PT26/00004 (Imputado, 308 líneas) ↔
  ANA26/00017: 15 cuentas de Debe idénticas al céntimo; Haber = Σ por
  `res.caaconide` (centro CP).
- **§D4 Cobertura.** Empresa 1, partes con asiento: 2025 441/441 Imputados
  (0 de los 14 no Imputados); 2026 58/58 Imputados. 2026 por estado: ene 33
  Imp/2 Cer/1 Reg; feb 17/17/0; mar–jun 1–2 Imp y 31–36 Cer; jul 1/39/2;
  ago 0/38/3; sep 0/0/29. Empresa 28 y 18: 0 asientos, 0 `caaide`.
- **§D5 sv5 hoy.** `partes_existentes` elige `ORDER BY hmo.ide DESC` sin
  `con.est`; `lineas_existentes` mira solo ese parte. Líneas con synckey
  `partes:` en Sigrid: 4 (empresa 28, 2026-09, sin cuenta). Varios partes
  por obra y mes: 3 casos en 2025–26, 35 desde 2015.
- **§D6 Debe de los asientos de partes 2025–26 por subcuenta.** CIMO 12,78
  M€, CICO 0,45 M€, CIMP 0,29 M€, CIMJ 0,06 M€, CIIN 3 k€; CD 0.
- **§D7 Contrapartida.** Empresa 1, 2026: 24.896 líneas, 24.607 con cuenta,
  206 con cuenta y sin contrapartida (12.169 €), de **2 recursos** (no
  personas: «consumos mensajería», 204 líneas; «cajas de obra», 2).
- **§D8 Obra de pruebas 0404 (empresa 1).** Un parte, PT26/00296 (jul 2026,
  En registro, 0 líneas); 23 asientos analíticos históricos en su centro.
- **§D9 Partida y árbol analítico.** Árbol `cag` de un centro (p. ej. 0696):
  `C` → `CD` {CDMA, CDQA, CDQC, CDQR, CDSB, CDSM, CDXA, CDXC}, `CI` {CICO,
  CIIN, CIMJ, CIMO, CIMP, CIOI, CISS, CITE}, `CP` {CP00}; `I` → `IN`
  {INGR}; `caa.padide` → grupo de nivel 3, su `padide` → rama de nivel 2.
  Cuentas empresa 1 por grupo en 540 centros: ningún grupo CD de mano de
  obra. Líneas `hmores` con cuenta CD en toda la historia: 0. Hojas del
  presupuesto de las 49 obras con horas en 2026: CD 39.449 (`INGR` 28.623,
  sin cuenta 10.826), CI 3.585 (con cuenta CI 3.136, sin 433, `INGR` 16),
  CP 604 (`CP00` 484). `obrparpar.tipcos` (partidas con horas de 2026):
  1 ⇔ capítulo CI, 2 ⇔ CP, 0 ⇔ CD, sin excepción; rama de su cuenta: CI
  509 (todas del centro de la obra), IN 30, CP 24. Líneas 2026 empresa 1
  (24.898) según su partida: CI con cuenta 18.621 (igual a la de la
  partida 17.481; mismo grupo y distinto número 743; otro grupo 396; sin
  cuenta 1), CI sin cuenta 2.811, CD 1.979 (467 k€), CP 562 (170 k€), sin
  partida 925; todas las CD y CP con cuenta CI del recurso. Discrepancias
  CI más frecuentes (línea ← partida): OFICIAL `CIMO09` ← MAQUINISTA
  `CIMO12` 433; VEHÍCULOS `CIMJ09` ← `CIMP09` 180; COMBUSTIBLES `CICO01` ←
  VEHÍCULOS `CIMP09` 92. Empresa 28: 207 de 5.178 líneas con partida, 0
  con cuenta.
- **§D10 Cuenta: partida frente a recurso (v4, medido por el líder).**
  Líneas 2026 empresa 1, cuenta de la partida solo si es `C[ID]`: partida
  y ficha del recurso coinciden 17.149 (6,88 M€); distintas 1.013 (0,57
  M€), la línea lleva siempre la del recurso (la de la partida, 0); partida
  sin cuenta 5.313 (línea = recurso 5.297, otra 16); recurso sin cuenta 544
  (línea = partida 478, otra 66); ninguno 39; línea sin cuenta 1.
- **§D11 Varios partes por obra y mes (2024–26, spec-author).** 7 periodos:
  Administración hace el complementario como un parte más (`PT..` propio,
  descripción `Parte <obra>` o similar, 1–44 líneas). Hoy, 2026-09: un
  periodo con dos partes En registro (51 y 2 líneas). `conest` tipo 35:
  REG «En registro», CER «Cerrado», IMP «Imputado» (sin otros estados).
