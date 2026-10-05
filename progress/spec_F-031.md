<!-- progress/spec_F-031.md -->
# F-031 · Resumen de la spec para el humano (spec-author, 2026-10-05, v3)

Spec: `specs/F-031-asiento-analitico/` (requirements, design, tasks). Rama
`feature/F-031-asiento-analitico`. Estado: `spec_ready`. Rigor crítico.
Versión 3: aplica tu aclaración sobre DA6 del 2026-10-05.

## En una frase

Sigrid ya genera el asiento analítico de cada parte al «Contabilizar». sv5
no escribe asientos; tiene que (1) **no meter líneas en un parte ya
contabilizado** y (2) poner en cada línea **la cuenta de la partida que la
línea tiene en el portal** (automática o corregida por el administrativo).

## Qué cambia respecto a la v2 (solo DA6)

- **Regla nueva (R17, R19):** la cuenta analítica de la línea es **siempre**
  la de su partida del portal, sea CI o CD (o CP si alguien la elige), sin
  mirar el tipo de coste ni el oficio del trabajador y sin nota. Desaparecen
  la rama CI/CD, la nota «pendiente de Administración» y el caso CP.
- **Preguntas a Juan 1–3** (CD, CP, partida frente a oficio): **retiradas**,
  las has respondido tú. Queda para Juan solo DA3 (contrapartidas).
- **Única excepción (R18, provisional):** si la línea no tiene partida, o
  su partida no tiene cuenta de coste, lleva la cuenta del recurso como
  hoy (F-021) y el modal lo dice con una nota por línea.
- La lectura de la partida ya no trae `tipcos`: solo su cuenta y la rama
  del árbol (para distinguir coste de ingreso).
- Sin cambios: DA1 (reabrir), DA2 (Cerrados con aviso), DA3 (fuera), DA4
  (sv5 no contabiliza), DA5, DA7, DA8. Ningún test de F-021 cambia.

## Comprobación hecha: ¿tiene la partida otra cuenta de coste? No (§D10)

He buscado en Sigrid una cuenta de **coste** de la partida distinta de
`obrparpar.caaide` (que en las partidas CD es de **ingresos** `INGR..` o
ninguna): la unidad de obra de la partida (`pro.gaside`), la partida de
coste relacionada (`parcoside`), el tipo de coste indirecto (`cosindide`),
los capítulos padre y la cuenta de gastos por defecto del centro. **Ninguna
existe** en las partidas con horas de 2026. Así que hay líneas cuya
partida no da cuenta de coste, y hace falta tu decisión:

## Pregunta para ti (DA6-e)

**¿Qué cuenta lleva una línea imputada a una partida que solo tiene cuenta
de ingresos o ninguna?** Cifras de 2026, empresa 1 (líneas tecleadas en
Sigrid):

| Partida de la línea | Líneas | Importe | Cuenta que puso Administración |
|---|---|---|---|
| CD sin cuenta | 1.404 | 362 k€ | CI del recurso (todas) |
| CD con solo `INGR..` (ingresos) | 575 | 105 k€ | CI del recurso (todas) |
| CI sin cuenta | 2.811 | 1.139 k€ | CI del recurso (todas) |

Lo provisional en la spec (R18) es **la cuenta del recurso, como hoy, con
una nota en el modal**, que es lo que hizo Administración a mano con esas
4.790 líneas. La alternativa sería dejarla sin cuenta (`caaide = 0`, con
aviso, como F-021 cuando no encuentra cuenta), pero entonces esa línea no
entra en el asiento analítico. Si eliges otra cosa, solo cambia una función
pura (`origen_subcuenta`).

Para tu información: en 2026 hay 562 líneas (170 k€) sobre partidas CP
(`CP00..`), todas tecleadas en Sigrid y puestas en la CI del recurso. Por
el portal no salen (sv3 y la sugerencia asignan CI/CD); si un administrativo
eligiera a mano una partida CP, con la regla nueva iría a su cuenta CP.

## Riesgos

Carrera de segundos con un «Contabilizar» simultáneo (aceptado; la
herramienta lo detectaría). Líneas retenidas si Administración contabiliza
antes de aprobar (es lo que pide DA1). La partida del portal pasa a decidir
la cuenta: un error de partida es ahora un error contable (se ve en el
preflight, en `caa_cod`).

## Fuera de alcance

Escribir asientos o cambiar estados; contrapartidas (DA3, Juan); los 31
asientos que no cuadran; recalcular la cuenta de líneas ya escritas; la
analítica de Porsan; sv1–sv3 y la base `partes`.

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
- **§D10 Cuenta de coste de la partida (v3).** Líneas 2026 empresa 1 con
  partida, por `tipcos` y rama de `obrparpar.caaide`: 1/CI 18.595 (7,47
  M€); 1/sin cuenta 2.811 (1,14 M€); 0/sin cuenta 1.404 (362 k€); 0/IN 575
  (105 k€); 2/CP 562 (170 k€); todas con cuenta CI en la línea salvo 1. En
  esas partidas: `proide` 0, `parcoside` 0, `cosindide` 0; capítulo padre y
  abuelo de las CD/CP: rama IN o sin cuenta; `cen.gaside` e `cen.ingide`
  vacíos en sus centros. Presupuesto de las obras con horas en 2026:
  partidas `tipcos` 0 con cuenta IN 33.394, sin cuenta 15.732, CI 1;
  `tipcos` 2 con CP 504, sin 163. Origen de la partida: sv3 asigna CI/CD,
  la sugerencia del portal solo CI, el selector manual cualquier hoja.
