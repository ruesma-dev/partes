<!-- progress/spec_F-031.md -->
# F-031 · Resumen de la spec para el humano (spec-author, 2026-10-05, v2)

Spec: `specs/F-031-asiento-analitico/` (requirements, design, tasks). Rama
`feature/F-031-asiento-analitico`. Estado: `spec_ready`. Rigor crítico.
Versión 2: aplica tus respuestas a la tabla de decisiones del 2026-10-05.

## En una frase

Sigrid ya genera el asiento analítico de cada parte al «Contabilizar». sv5
no escribe asientos; tiene que (1) **no meter líneas en un parte ya
contabilizado** y (2) poner en cada línea **la cuenta analítica de su
partida** cuando la partida es de costes indirectos.

## Qué cambia respecto a la versión 1

1. **DA1 (reabrir), ya no hay parte complementario.** Si todos los partes
   del mes están Imputados, sv5 no crea nada: las líneas de ese mes salen
   como **omitidas** con el motivo «parte PTxx (MM/AAAA) contabilizado: pide
   a Administración que lo reabra en Sigrid y vuelve a aprobar». En el modal
   de aprobación el parte aparece con un aviso («N líneas no se registran
   hasta que Administración lo reabra»), y las líneas, en la lista de «No se
   registran». Cuando Administración deshace el «Contabilizar» en Sigrid y
   se vuelven a aprobar, entran normales. sv5 nunca cambia el estado del
   parte (DA4).
2. **DA2 (sí):** en partes Cerrados se escribe, con aviso. Sin cambios.
3. **DA3:** eran **2** recursos sin contrapartida, no 3 (206 líneas,
   12.169 €). Fuera de alcance hasta que Juan responda al borrador.
4. **DA6 (nuevo): la cuenta sale de la partida.** Hasta ahora (F-021) la
   cuenta salía de la ficha de horas del recurso (p. ej. `CIMO08 CAPATAZ`).
   Ahora, si la partida de la línea (la del portal o la automática) tiene
   cuenta y esa cuenta cuelga de **CI** en el árbol analítico de la obra,
   la línea lleva la cuenta de la partida. En los demás casos lleva la del
   recurso, como hoy, y el modal lo dice con una nota por línea («sin
   partida», «la partida X es de costes directos…», etc.). Esto **modifica
   F-021** (su regla R7 decía que la partida no intervenía), pero **ningún
   test de F-021 cambia**: ninguno usa partida.
5. Lo demás (DA5 omitir choques, DA7 estados como ajustes, DA8 herramienta
   de comprobación) igual que en la versión 1.

## Lo que he descubierto de la partida y el árbol analítico

- El árbol analítico de cada obra tiene **CD** (materiales, maquinaria,
  subcontratas, medios auxiliares), **CI** (consumos, infraestructura,
  maquinaria, **mano de obra indirecta CIMO**, otros…) y **CP**. **No hay
  ninguna cuenta CD para mano de obra propia.** Nunca, en ningún año, una
  línea de horas ha llevado una cuenta CD.
- Cada partida del presupuesto sabe si es CI, CD o CP por un campo propio
  de Sigrid (`tipcos`), y las partidas CI suelen tener su cuenta CI (p. ej.
  la partida «CAPATAZ» → `CIMO08`). Las CD llevan cuentas de **ingresos**
  (certificación) o ninguna; las CP, `CP00..`.
- En 2026, cuando la partida es CI con cuenta, Administración ha puesto la
  de la partida en 17.481 líneas y la del recurso en 1.139 (p. ej. un
  oficial imputado a la partida «maquinista»: 433 líneas). Las 1.979 líneas
  sobre partidas CD y las 562 sobre CP las ha puesto **todas en CI** (la
  del recurso).
- Conclusión: la regla para CI se deduce con seguridad; para CD y CP **no**
  hay cuenta destino que deducir. Hasta que Juan responda, esas líneas
  llevan la cuenta del recurso con una nota «pendiente de Administración».

## Preguntas para Juan Romero

1. **Partidas de costes directos.** El árbol de la obra no tiene cuenta CD
   de mano de obra propia (solo CDSB «subcontrata mano de obra»). Si un
   operario se imputa a una partida CD, ¿a qué cuenta va? ¿Hay que crear un
   grupo (p. ej. `CDMO`) en el árbol, o usar otra?
2. **Partidas de costes proporcionales** (p. ej. `CP.7 Costes estructura
   delegación`, cuenta `CP0007`): ¿la línea va a esa cuenta CP o a la CI del
   recurso, como se hace hoy?
3. **Partida frente a oficio.** Si la partida es CI pero de otro oficio que
   el trabajador (oficial en la partida «maquinista»), ¿manda la partida?
   Hoy, a mano, manda el recurso en esos casos (1.139 líneas en 2026).
4. **Contrapartidas** (DA3, ya en el borrador del líder): 2 recursos sin
   cuenta de contrapartida (206 líneas, 12.169 € en 2026).
5. Para su información: 31 asientos de 2025–26 ya no cuadran con su parte
   porque el parte se tocó después de contabilizar.

Si Juan responde 1–2 antes de que el implementer llegue a T6, se ajusta la
spec; si responde después, es una feature pequeña nueva (solo cambia una
función pura).

## Riesgos

Carrera de segundos con un «Contabilizar» simultáneo (aceptado; la
herramienta lo detectaría). Líneas retenidas si Administración contabiliza
antes de aprobar (es lo que pide DA1). La partida automática que asigna
sv3 pasa a decidir la cuenta: un error de partida es ahora un error
contable (se ve en el preflight).

## Fuera de alcance

Escribir asientos o cambiar estados; contrapartidas; los 31 asientos que no
cuadran; recalcular la cuenta de líneas ya escritas; la analítica de
Porsan; la cuenta CD/CP hasta que Juan responda; sv1–sv3 y la base
`partes`.

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
