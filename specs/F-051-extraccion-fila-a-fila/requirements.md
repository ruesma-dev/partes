# F-051 · Extracción fila a fila: cada número a su fila — requisitos

> Pedida por el humano el 2026-10-19: «reforzar el prompt» de la extracción IA
> para que cada cifra manuscrita se asigne a la FILA en la que está escrita, no
> a la más cercana. Servicios: **sv2** (prompt y esquema, siempre) y **sv3**
> (red de seguridad, solo si la DA2 lo aprueba). sv1, sv4 y sv5 no se tocan.
> Diseño en `design.md`; DA1–DA3 (§7) resueltas por el humano el 2026-10-19:
> A, C y 3 de 3. Dato DA2: `tabla_dispersa` marcaría 8/108 laborables y 9/17 de finde.

## Caso real que lo motiva

PDF de 3 páginas de la obra 0686 (16, 17 y 18/10/2026), escaneado girado. Tabla
de personal con 5 filas impresas (nº 1–5, con DNI y nombre), subcolumnas «Ord.»
y «Extraord.». sv1 parte el PDF en 3 documentos de una página.

| Día | En el papel | Lo que devolvió Gemini (confianza 95) |
|---|---|---|
| 16/10 | todas las filas con horas en «Ord.» | correcto |
| 17/10 (sábado) | fila 2 = 12 extra, fila 3 = 10 extra; filas 1, 4, 5 vacías | fila 1 = 12, fila 2 = 10, fila 3 vacía |
| 18/10 (domingo) | fila 2 = 14 extra; resto vacío | fila 1 = 14, fila 2 vacía |

Patrón: **pocas cifras sueltas en una tabla casi vacía ⇒ cada cifra sube una
fila**. sv3 casó bien a cada persona por DNI: el error nace en la lectura (sv2),
y la confianza alta no lo delata.

## Glosario

- **Fila**: franja horizontal de la tabla de personal entre dos líneas impresas,
  identificada por su «Nº» impreso (1..14) y por el DNI/nombre de esa franja.
- **Autocomprobación**: campo nuevo `numero_linea_horas` de cada empleado (DA1):
  el «Nº» que el modelo lee en la franja donde está escrita la cifra de horas.
- **Lectura dudosa**: motivo por el que sv3 pone el parte en `review_required`
  por sospecha sobre la lectura (bloque C, condicionado a la DA2).

## A. Prompt `parte_trabajo_es` (sv2, `config/prompts.yaml`)

R1. El prompt debe ordenar que cada cifra manuscrita de una fila (horas «Ord.»,
horas «Extraord.», incidencia y horas de partidas) se asigne a la fila en cuya
franja horizontal está escrita, identificada por el «Nº» y el DNI/nombre
impresos en esa misma franja, y prohibir asignarla a la fila más cercana o a la
de arriba por defecto.

R2. El prompt debe ordenar un recorrido fila a fila: para cada «Nº» impreso,
seguir la línea de esa fila hasta las subcolumnas «Ord.» y «Extraord.» y leer
solo lo que hay entre las líneas que delimitan esa fila.

R3. El prompt debe ordenar que una celda vacía es `null`, que nunca se rellena
con la cifra de una fila vecina y que no se mueven cifras entre filas; y debe
advertir de que con pocas cifras sueltas (típico de fin de semana) lo normal es
que haya filas con trabajador y sin horas, y que ese es el caso en que más se
desplazan las cifras.

R4. El prompt debe advertir de los escaneos girados o inclinados (seguir las
líneas de la tabla, no el borde de la página) y de las cifras que invaden la
línea de la fila vecina: la cifra pertenece a la fila que contiene su centro.

R5. El prompt debe mantener que toda fila con trabajador (nombre o DNI) se
incluye en `empleados[]` con su `numero_linea`, también si no tiene horas (con
`horas_ordinarias` y `horas_extraordinarias` a `null`), en el orden del papel.

R6. DONDE la DA1 elija el campo por fila (opción A, recomendada), el prompt debe
pedir `numero_linea_horas`: el «Nº» impreso en la franja donde está escrita la
cifra de horas de ese objeto, leído desde la cifra hacia la columna «Nº»; `null`
si la fila no tiene horas; y que nunca se copie de `numero_linea` sin mirarlo.

R7. El `schema_hint` debe listar en `empleados` las claves `dni` (hoy falta,
aunque el esquema la tiene desde F-030) y, con la DA1 = A,
`numero_linea_horas`.

R8. El resto del prompt no debe cambiar: cabecera, firma, incidencias, partidas
y catálogo de códigos de hora quedan igual (los tests de F-023 pasan sin
tocarlos).

## B. Esquema `ParteTrabajo` (sv2, `domain/models/parte_models.py`)

R9. DONDE la DA1 = A, `EmpleadoParte` debe declarar
`numero_linea_horas: Optional[int] = None`, sin cotas `ge`/`le` (un valor fuera
de rango no debe tumbar el parseo de todo el parte).

R10. DONDE la DA1 = A, el JSON Schema que se envía al proveedor
(`ParteTrabajo.model_json_schema()`) debe llevar `numero_linea_horas` en
`EmpleadoParte` justo después de `numero_linea` y antes de `horas_ordinarias`,
para que el modelo lo escriba antes que las horas.

R11. SI la respuesta del proveedor no trae `numero_linea_horas`, ENTONCES el
parseo debe seguir siendo válido con el campo a `null`.

R12. El esquema debe seguir rechazando campos no declarados (`extra="forbid"`).

## C. Red de seguridad en sv3 (solo si la DA2 ≠ A)

R13. DONDE la DA2 = B o C, CUANDO sv3 normaliza un parte con alguna fila que
tiene horas (ordinarias o extra distintas de 0 y no nulas) y
`numero_linea_horas` no nulo y distinto de su `numero_linea` no nulo, el
sistema debe marcar la lectura como dudosa con el motivo
`autocomprobacion_fila`.

R14. DONDE la DA2 = C, CUANDO el parte tiene al menos una fila con horas y al
menos una fila con trabajador (nombre o DNI) sin horas ni incidencia, el
sistema debe marcar la lectura como dudosa con el motivo `tabla_dispersa`.

R15. CUANDO la lectura es dudosa, el parte debe quedar con
`review_required = true` y sv3 debe escribir un log WARNING con el motivo y los
`numero_linea` implicados (sin nombres ni DNIs).

R16. SI el payload no trae `numero_linea_horas` (partes anteriores a F-051 o un
proveedor que lo omita), ENTONCES R13 no debe dispararse.

R17. La comprobación debe ser pura sobre el payload de sv2: sin Sigrid, sin
BBDD y sin el calendario laboral. No debe cambiar ninguna otra condición de
`review_required` ni ninguna cifra, registro o casado del parte.

## D. Verificación manual con el PDF real (no se versiona)

R18. Con el PDF del caso real troceado en sus 3 páginas, sv2 en local con el
modelo de producción (`IA_PROVIDER=gemini`, `GEMINI_MODEL` de producción) debe
devolver, en el número de ejecuciones que fije la DA3: 16/10 igual que hoy;
17/10 fila 2 = 12 extra, fila 3 = 10 extra y filas 1, 4, 5 sin horas; 18/10
fila 2 = 14 extra y el resto sin horas.

R19. Un conjunto de partes que hoy se leen bien (al menos 5, laborables y con la
tabla llena, elegidos por el humano) debe dar las mismas horas por fila que los
valores aprobados en el portal.

R20. La verificación de R18 y R19 debe poder repetirse con otro proveedor o
modelo cambiando solo variables existentes del `.env` local de sv2
(`IA_PROVIDER`, `ENABLE_*`, `GEMINI_MODEL`, `ANTHROPIC_MODEL`, `OPENAI_MODEL`,
`GEMINI_MEDIA_RESOLUTION`), sin tocar código. La comparativa de modelos y
costes NO forma parte de esta feature.

## Fuera de alcance

- La comparativa de modelos y costes (la hace el líder aparte) y cualquier
  cambio de `IA_PROVIDER`, `GEMINI_MODEL` o `GEMINI_MEDIA_RESOLUTION` en Azure.
- Corregir los partes ya ingeridos de la 0686 (17 y 18/10): se arreglan a mano
  en el portal; F-051 solo afecta a las ingestas nuevas.
- Mostrar en el portal (sv4) el motivo de `review_required`.
- Una segunda lectura con otro modelo o recortes de imagen por fila (ver
  `design.md` §8, alternativas descartadas).

## Criterios de aceptación

- R1–R12 (y R13–R17 si la DA2 ≠ A) con tests `test_f051_rN_*` sin red ni BBDD.
- M1 (R18) y M2 (R19) hechas por el humano o el líder y anotadas en
  `progress/impl_F-051.md`.
- Los tests existentes de sv2 y sv3 pasan sin cambios.
- Mutación muestreada (rigor `estandar`) con supervivientes analizados.
- `bash harness/init.sh` en verde y APPROVED del reviewer.
