<!-- progress/spec_F-031.md -->
# F-031 · Resumen de la spec para el humano (spec-author, 2026-10-05)

Spec: `specs/F-031-asiento-analitico/` (requirements, design, tasks). Rama
`feature/F-031-asiento-analitico`. Estado: `spec_ready`. Rigor crítico.

## En una frase

**Sigrid ya genera el asiento analítico de cada parte**, a partir de la
cuenta analítica de sus líneas (la que F-021 ya escribe). No hay que escribir
asientos. Lo que falta es que sv5 **no meta líneas en un parte que
Administración ya ha contabilizado**, porque esas líneas se quedarían fuera
de la analítica para siempre.

## Qué he descubierto sobre cómo contabiliza Sigrid

1. Un parte de trabajo pasa por tres estados: **En registro** → **Cerrado**
   → **Imputado**. Cerrar e imputar solo lo pueden hacer Administración y
   Control de Costes.
2. Administración lanza en Sigrid el proceso **«Contabilizar parte»** sobre
   lotes de partes (el último, el 14 de septiembre). Ese proceso pone el
   parte en Imputado y crea **un asiento analítico por parte** (código
   `ANA26/…`, mismo nombre «Parte <obra>» y misma fecha, fin de mes):
   - **Debe**: el importe de las líneas (`horas × precio`) agrupado por su
     cuenta analítica, que es la cuenta del centro de la obra (p. ej.
     `0696.CIMO08 CAPATAZ`). Las líneas sin cuenta no entran.
   - **Haber**: el mismo importe en la cuenta de contrapartida de cada
     trabajador (centro `CP`, una cuenta por persona).
3. Comprobado con datos: los 441 partes imputados de 2025 y los 58 de 2026
   tienen su asiento, y ninguno de los demás. 465 de 497 asientos cuadran al
   céntimo con las líneas de hoy; los otros 31 son partes que alguien tocó
   después de contabilizarlos (dato para Juan).
4. Administración va con retraso en 2026: enero y febrero contabilizados (en
   septiembre), marzo–agosto **cerrados pero sin contabilizar**, septiembre
   en registro. Porsan (empresa 28) no tiene ni un asiento analítico ni una
   línea con cuenta: no usa analítica.
5. La «cuenta de coste de la mano de obra» que preguntaba la feature es la de
   la ficha del recurso por categoría: todo el Debe de partes va a **CI·MO**
   (costes indirectos de mano de obra: jefe de obra, encargado, capataz,
   oficial, gruista…), más CICO/CIMP/CIMJ para teléfonos, vehículos y
   maquinaria. Nada a CD.
6. El ejemplo del correo de Juan (apunte 6260000000 con desglose analítico a
   `0702.CP0004 AVALES`) es un asiento **financiero** con desglose; los
   partes no van por ahí: generan un asiento **solo analítico**.

## El problema real (y lo que propone la spec)

Hoy sv5 escribe en el parte del mes **sin mirar su estado**. Si el parte ya
está Imputado, la línea entra en Sigrid pero no en su asiento, que ya está
hecho; y si sv5 pisa un conflicto ahí, borra una línea que el asiento sí
cuenta. Hoy no ha pasado (en Sigrid solo hay 4 líneas de sv5, de Porsan),
pero pasará en cuanto se aprueben horas atrasadas de meses contabilizados.

Propuesta (solo sv5, y una línea de texto en el portal):
- sv5 lee el estado de los partes del mes y **nunca escribe en uno Imputado**.
- Si todos los del mes están Imputados, abre un **parte complementario**
  nuevo (Administración lo contabilizará y tendrá su propio asiento).
- Si el parte está Cerrado, escribe como hoy y el portal avisa de que entrará
  en el asiento cuando Administración lo contabilice.
- Una línea que choca con horas de un parte ya contabilizado se **omite** con
  un motivo claro (vuelve al portal como `omitido`, editable).
- Una herramienta de consola de **solo lectura** comprueba, para una obra y
  mes, si el asiento analítico cuadra con las líneas (y cuántas son de sv5).

## Decisiones abiertas (detalle en design §8)

| DA | Pregunta | Recomendación |
|---|---|---|
| DA1 (Juan) | Todos los partes del mes contabilizados: ¿dónde van las líneas nuevas? | Parte complementario nuevo |
| DA2 (Juan) | Parte Cerrado (sin contabilizar): ¿se escribe? | Sí, con aviso |
| DA3 | 3 recursos sin contrapartida (206 líneas, 12.169 € en 2026): asiento descuadrado | Fuera: avisar a Administración |
| DA4 | ¿sv5 contabiliza o escribe asientos? | No: es de Administración |
| DA5 | Choque con línea de un parte contabilizado | Omitir con motivo |
| DA6 (Juan) | ¿Operarios a CD en vez de CI·MO? | No cambia código; lo decide Juan en las fichas |
| DA7 | Estados (10/3) como ajustes | Sí, con esos defectos |
| DA8 | Herramienta de comprobación | Incluirla |

**Preguntas para Juan Romero antes de implementar (M0):** (1) si un mes ya
está contabilizado y llegan horas de ese mes, ¿parte complementario, o
prefiere reabrir y recontabilizar el parte?; (2) ¿se puede deshacer
«Contabilizar»?; (3) ¿le vale un asiento fechado a fin del mes del trabajo
aunque ese mes ya esté cerrado?; (4) ¿escribir en partes Cerrados le parece
bien?; (5) ¿la mano de obra de operarios debe ir a CI·MO o a CD?; (6) los 31
asientos que ya no cuadran y los 3 recursos sin contrapartida.

## Riesgos

Carrera de segundos con un «Contabilizar» simultáneo (aceptado; la
herramienta lo detectaría). Muchos complementarios si Administración
contabiliza antes de aprobar (lo decide DA1). El parte y su asiento no
tienen clave común: se casan por empresa, nombre y fecha (497/497 hoy).

## Fuera de alcance

Escribir asientos o cambiar estados; contrapartidas; los 31 asientos que no
cuadran; la analítica de Porsan; apuntes financieros; sv1–sv3 y la base
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
  centro); 1 por centro y mes salvo un caso. Debe = Σ `hmores.tot` con
  `caaide > 0`: 465 cuadran, 31 no, 1 sin líneas. Ejemplo: obra 0696,
  PT26/00004 (Imputado, 308 líneas) ↔ ANA26/00017: 15 cuentas de Debe
  idénticas al céntimo; Haber idéntico a Σ por `res.caaconide` (26
  cuentas del centro CP); la línea con recurso sin contrapartida no tiene
  Haber.
- **§D4 Cobertura.** Empresa 1, partes con asiento: 2025 441/441 Imputados
  (0 de los 14 no Imputados); 2026 58/58 Imputados. 2026 por estado: ene 33
  Imp/2 Cer/1 Reg; feb 17/17/0; mar–jun 1–2 Imp y 31–36 Cer; jul 1/39/2;
  ago 0/38/3; sep 0/0/29. Empresa 28: 0 asientos, 0 `caaide`; empresa 18
  igual.
- **§D5 sv5 hoy.** `partes_existentes` elige `ORDER BY hmo.ide DESC` sin
  `con.est`; `lineas_existentes` mira solo ese parte. Líneas con synckey
  `partes:` en Sigrid: 4 (empresa 28, 2026-09, sin cuenta). Varios partes
  por obra y mes: 3 casos en 2025–26, 35 desde 2015.
- **§D6 Debe de los asientos de partes 2025–26 por subcuenta.** CIMO 12,78
  M€ (2.817 apuntes), CICO 0,45 M€, CIMP 0,29 M€, CIMJ 0,06 M€, CIIN 3 k€;
  CD 0.
- **§D7 Contrapartida.** Recursos con líneas en 2026: 722 de 725 con
  `res.caaconide` (centro CP 717, CM 5). Empresa 1, 2026: 24.896 líneas,
  24.607 con cuenta, 206 con cuenta y sin contrapartida (12.169 €).
- **§D8 Obra de pruebas 0404 (empresa 1).** Un parte, PT26/00296 (jul 2026,
  En registro, 0 líneas); 23 asientos analíticos históricos en su centro.
