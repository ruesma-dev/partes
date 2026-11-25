<!-- progress/spec_F-083.md -->
# F-083 · Spec para el humano (spec-author, 2026-11-23)

Spec: `specs/F-083-ciz-solo-fin-de-racha/` (requirements 144/150, design 249/250, tasks T1–T8).
Rama `feature/F-083-ciz-solo-fin-de-racha`, en la copia `partes-wt-f083`.

## Qué propone

Una sola idea en sv5 (`racha_ciz.py`): **el fin de la racha está más adelante si la racha tiene
CUALQUIER línea suya en Sigrid en un día posterior.** Una línea de la racha es una candidata que
`lineas_de_racha` ya lee hoy por las synckeys de la racha, del mismo recurso, a 0 h y, en
pruebas, con la marca.

- **`fin`**: con un CIZ posterior, todo sigue como hoy (`intermedio`). Con solo otro código
  posterior (el caso 0730), también es `intermedio`: ni se crea ni se mueve ningún CIZ, el
  motivo nombra la línea, y se registra un WARNING `racha_fin_no_ciz`.
- **`inicio`** con `ciz_mismo_dia`: con una línea posterior sin CIZ, no escribe su CIZ hermano
  (motivo `posterior_sin_ciz` y el mismo WARNING). El CI* se escribe igual.
- Sin la línea posterior, exactamente lo de hoy.

Además:
- no hay lecturas nuevas ni sentencias nuevas: F-083 solo convierte escrituras en omisiones;
- en Sigrid no se borra nada;
- sv4 no cambia;
- va bajo `MOVER_CIZ` (encendido en producción), así que desplegar sv5 lo activa. La vuelta
  atrás es la imagen anterior de sv5 y es segura.

## Decisiones (recomendación en negrita)

| D | Pregunta | Recomendado |
|---|---|---|
| D1 | ¿Solo sv5 o también sv4? | **(a) solo sv5**: la regla depende de lo que hay en Sigrid (un CIZ cambiado a mano solo se ve allí). Hacerla también en sv4 duplicaría lógica entre servicios. |
| D2 | Motivo en el portal | **(a)** el prefijo de siempre, «dia intermedio de la incidencia: …», más un detalle («la racha sigue en Sigrid el dia …, linea … con CIV, sin CIZ despues; no se escribe un fin en medio»). Se agrupa con los intermedios. (b) sería un prefijo nuevo `racha_sin_ciz:`. |
| D3 | ↻ en «omitido · intermedio» | **(a) se mantiene**: con F-083 reaprobar es inocuo, y hace falta si la racha cambió en `partes`. |
| D4 | Aviso `racha_desordenada` | **(a) sin cambios**: sigue siendo útil cuando delante hay un CI* de inicio. |
| D5 | Qué línea posterior cuenta | **(a) cualquier código** (a 0 h, mismo recurso, marca en pruebas). (b) sería solo los CI*. |
| D6 | Administración quitó el CIZ del último día | **(a) respetarlo**: la racha queda sin fin y lo avisan el WARNING y el motivo. (b) sería escribir un CIZ nuevo en el último día. |
| D7 | Interruptor | **(a) `MOVER_CIZ`, sin variable nueva**. |
| D8 | CIZ ya escritos en medio (416356) | **(a) nada retroactivo**: Administración ya lo pasó a CIV. |

## Riesgos y avisos

- **Racha sin CIZ**: si el CIZ se quitó a mano (D6), queda así a propósito.
- **Fuera de alcance**: un CI* escrito en medio de la racha. Pasa cuando un día posterior se
  aprobó como `inicio` antes de ingerirse los anteriores. F-083 solo gobierna el CIZ.
- **Dos tests de F-060 y F-062 se enmiendan (R22)**: en el subcaso «línea posterior de otro
  código» decían justo lo contrario de lo que pide el humano.
- **M1 y M3 piden que el humano edite a mano en Sigrid** una línea de pruebas (obra 0404,
  PRUEBA-IA) de CIZ a CIV, para reproducir el caso. Si no lo autoriza, quedan cubiertas por los
  tests con doble (R13, R15) y se hace M2. M0 y M4 son solo lectura en producción.
- **Base de la rama**: 011bc2a **no está en `dev`**: lleva los commits de F-072 (`in_review`,
  sin fusionar). Si F-072 no se fusiona antes que F-083, el merge de F-083 a `dev` arrastraría
  F-072. El líder debe decidir si rebasa F-083 sobre `dev` antes de implementar.
- **Frontera**: no cambia ningún contrato. Sí cambia qué escribe sv5 en `hmores` (menos CIZ), y
  se actualiza `azure-apps/partes.md` en un commit aparte, sin push.
