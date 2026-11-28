<!-- progress/manual_F-085.md -->
# F-085 · Verificaciones manuales

## M0 · líder, 2026-11-27, solo lectura, antes de T1 (design §8)

Consultas tal cual las da design §8. Sigrid: base `ruesma`, `truncated: False`.

**(1) Líneas heredadas con CI\* sin ser incidencia (D7)**, base `partes`:

| sigrid_estado | código | líneas |
|---|---|---|
| registrado | CIA | 1 |

Es la propia 25012 del caso. No hay más líneas heredadas.

**(2) Líneas del recurso 2777451 del 17 al 30 de noviembre**, base `partes`:

| id | fecha | tipo_hora | es_incidencia | incidencia | código | horas | sigrid_estado | hmores |
|---|---|---|---|---|---|---|---|---|
| 25021 | 20261117 | normal | no | | HLOF | 8 | registrado | 416005 |
| 25026 | 20261117 | extra | no | | HEOF | 2 | registrado | 416010 |
| 25012 | 20261118 | normal | no | | CIA | 8 | registrado | 416574 |
| 25096 | 20261119 | AT | sí | AT | CIA | | borrado_sigrid | 416122 |
| 25413 | 20261120 | AT | sí | AT | CIA | 0 | omitido | |
| 25405 | 20261121 | AT | sí | AT | CIA | | (vacío) | |
| 25397 | 20261123 | AT | sí | AT | CIA | | omitido | |
| 25388 | 20261124 | AT | sí | AT | CIA | | omitido | |
| 25380 | 20261125 | AT | sí | AT | CIA | | registrado | 416563 |

**(3) `hmores` del recurso 2777451 del 17 al 30 de noviembre**, Sigrid:

| ide | fec | código | can | synckey |
|---|---|---|---|---|
| 416005 | 20261117 | HLOF | 8 | `partes:25021` |
| 416010 | 20261117 | HEOF | 2 | `partes:25026` |
| 416574 | 20261118 | HLOF | 8 | `partes:25012` |
| 416563 | 20261125 | CIZ | 0 | `partes:25380` |

**Resultado: coincide con lo esperado.** 416574 (18, HLOF, 8, `partes:25012`); 416563 (25, CIZ) con la
synckey de la línea AT activa del 25 (25380), que es de esa racha; nada de `partes:25016`. No hay
ningún CI\* de inicio en Sigrid para la racha. No se da la condición de PARADA.

## M1 y M2 · pendientes (modo pruebas, antes de desplegar)

## M4 · fuera de la feature

La reparación del caso 0678 la hace el humano a mano (D15, 2026-11-27). Ningún agente escribe en
producción ni en Sigrid para ello.
