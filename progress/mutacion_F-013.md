<!-- progress/mutacion_F-013.md -->
# F-013 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-013` el 2026-08-18 00:11.

## Alcance

Origen del diff: **rama** (`da7293da005993dee235011b5ac2197b929d6a6d` .. `feature/F-013-informe-validacion-sesame`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/validar_datos_sesame.py` | 587 |
| **Total** | **587** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 77 |
| Mutantes evaluados | 77 |
| Muertos | 76 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Tiempo total | 389.1 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/validar_datos_sesame.py:388` [entero]

- Original: `transporte = transport or httpx.HTTPTransport(retries=1)`
- Mutado:   `transporte = transport or httpx.HTTPTransport(retries=2)`

#### Análisis (completado por el implementer, 2026-08-18)

**Decisión: mutante EQUIVALENTE para esta suite, justificado. No se añade
test.**

**Por qué ningún test lo caza.** La expresión es
`transporte = transport or httpx.HTTPTransport(retries=1)`, y el `or`
**cortocircuita**: cuando se inyecta un transporte —lo que hacen los 42
tests de `services/partes-front/tests/test_f013_informe_sesame.py`, todos
con `httpx.MockTransport`— el operando derecho **ni siquiera se evalúa**,
así que el constructor `httpx.HTTPTransport(retries=...)` no llega a
ejecutarse nunca bajo test. El mutante cambia un argumento de una llamada
que la suite no realiza; no hay forma de observarlo desde aquí. (El
generador produce un segundo mutante en esta misma línea, `or`→`and`, que
la campaña **sí** mata: la inyección del transporte está cubierta; lo que
no se puede cubrir es la rama del transporte real.)

**Por qué no se escribe un test que lo mate.** Habría que dejar
`transport=None` para que se construyera el transporte real y luego contar
los reintentos contra un servidor de verdad. `docs/CONVENTIONS.md` §Tests
lo prohíbe expresamente: «los unit tests no tocan red ni BBDD». Un test así
sería además lento e inestable, y cambiaría la naturaleza de la suite entera
por cubrir un parámetro de librería.

**Por qué no es un hueco real de verificación.** `retries` no altera ningún
resultado observable del informe: no cambia una sola celda del Markdown ni
del CSV, ni el código de salida, ni el mensaje. Solo decide cuántas veces
`httpx` reintenta a nivel de conexión antes de rendirse. El comportamiento
que sí importa —que, cuando `sesame-api` no responde, el script aborte con
mensaje claro y exit distinto de cero, sin escribir ficheros a medias— está
cubierto por `test_f013_r_sesame_api_inalcanzable_aborta` (y el mensaje, con
el cuerpo del error, por `test_f013_r_fallo_del_listado_aborta_con_codigo_1`).

**Contexto de las campañas.** La primera pasada dejó 22 supervivientes de 74;
se escribieron tests para 21 de ellos, y dos de esos tests destaparon
comportamientos que habrían sido bugs reales (una variable comentada con
`=` dentro de un `.env` se habría aplicado, y una clave en base64 terminada
en `=` habría reventado el parseo). Esta cuarta campaña, tras el cambio de
NB-1 (línea `(no se pudo leer)` en el resumen), genera **3 mutantes nuevos**
—74 → 77— y los mata **todos**. Este superviviente es el único que queda, y
queda por la razón de arriba, no por falta de intento.

