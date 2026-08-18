<!-- progress/impl_F-014.md -->
# F-014 · Poner `candef = 9` en Sigrid a los recursos que registran jornada de 9 h — implementación

- Rama: `feature/F-014-candef-9-sigrid`. Rigor **documental**. `sdd: false`:
  la mini-spec son los tres `acceptance` de F-014 en `harness/features.json`.
- Fecha: 2026-08-19. Sin `git push`, sin PR, sin tocar `dev` ni `main`.
- Origen del análisis: `specs/F-012-estudio-jornada-semanal/design.md`
  (H1, H2, H5, decisiones D1/D3/D4, riesgo §10.6 y el SQL del anexo A).

## Qué se ha hecho

F-014 **no lleva código**: es un cambio de **datos maestros en Sigrid** que
ejecuta RRHH/Administración a mano. Lo que entrega esta feature es (a) la
**línea base medida** en Sigrid antes del cambio, (b) la **petición
redactada** para que RRHH la ejecute sin conocer el proyecto y (c) la
**verificación posterior reproducible**, toda ella en **solo lectura**.

1. **Línea base (solo lectura)** contra Sigrid, base `ruesma`, vía
   `sigrid-api` `POST /api/sql/read`, el 2026-08-19: distribución de
   `candef` (H1 del anexo A), recursos con `candef = 9` (H2) y estado
   detallado de las 8 fichas de la petición (`candef` de la hora por defecto,
   categoría, si hay DNI en `emp` —**sin traer el DNI**—, `con.fecbaj`,
   códigos `HE%` y último parte registrado). Ni una sola escritura.
2. **`progress/peticion_F-014.md`**: la petición para RRHH, en lenguaje de
   negocio, con el porqué, la lista recurso a recurso, el campo exacto, lo
   que NO se toca, quién ejecuta, la verificación posterior con su SQL y su
   resultado esperado, y un bloque «texto para el correo» copiable.
3. **Este informe**, con la línea base y los hallazgos.

### Ficheros tocados

| Fichero | Qué |
|---|---|
| `progress/peticion_F-014.md` | **NUEVO**. La petición para RRHH/Administración + la verificación posterior. |
| `progress/impl_F-014.md` | **NUEVO**. Este informe. |

**Nada más.** No se ha tocado ningún fichero de `services/**`, ni
`orm_models.py`, ni tests, ni `harness/features.json`, ni
`progress/current.md`. Los scripts de consulta usados para medir la línea
base son de usar y tirar y viven **fuera del repositorio**, en el
scratchpad de la sesión (`linea_base_f014.py`, `linea_base_f014b.py`,
`linea_base_f014c.py`); no se versionan porque no aportan nada reutilizable
y el `acceptance` 2 pide SQL reproducible, que está escrito literal en la
petición.

### Commits

```
e04c575  F-014 T1: linea base en Sigrid (solo lectura) y peticion para RRHH
<este>   F-014 T2: informe del implementer
```

## Línea base medida (2026-08-19, antes del cambio)

Método: `POST /api/sql/read`, base `ruesma`, `max_rows` 1000 (ninguna
respuesta truncada). Credenciales leídas de
`services/partes-persistencia/.env` en memoria; **no se han copiado a ningún
fichero, informe ni mensaje**.

### H1 · Distribución de `candef` (hora por defecto de los recursos de alta)

| `candef` | recursos | igual que F-012 (2026-08-18) |
|---|---|---|
| 1.0 | 561 | ✅ 561 |
| 0.0 | 199 | ✅ 199 |
| 8.0 | 106 | ✅ 106 |
| 9.0 | 1 | ✅ 1 |

Idéntica, cifra por cifra, a la tabla H1 del estudio. **Nadie ha tocado
ningún `candef` en el intervalo.**

### H2 · Recursos con `candef = 9`

Una sola fila: `res.ide` 2798044, `con.cod` `MO/0037`, OFIC. 2ª ALBAÑIL,
`tiene_dni = sin`, `n_he = 1`. Coincide con H2 del estudio.

### Estado de las 8 fichas de la petición

Todas de alta (`fecbaj = 0`), todas con hora por defecto `HLOF`, todas con
exactamente **una** fila de `reshor` cuyo `horide = res.horide` (la
instrucción «la fila de `reshor` con `horide = res.horide`» es unívoca por
ficha), y todas con un código `HE%` disponible (`n_he = 1`).

| Código | `res.ide` | Categoría | `candef` hoy | ¿DNI en `emp`? | `fecbaj` | Últ. parte | Líneas 2026 |
|---|---|---|---|---|---|---|---|
| `MO/0006` | 2146402 | OFIC. 1ª ALBAÑIL | 8.0 | sí | 0 | 2026-08-13 | 159 |
| `MO/0007` | 2146403 | OFIC. 1ª ALBAÑIL | 8.0 | sí | 0 | **2026-02-04** | 22 |
| `MO/0008` | 2146404 | OFIC. 1ª ALBAÑIL | 8.0 | sí | 0 | 2026-07-16 | 138 |
| `MO/0031` | 2714845 | OFIC. 1ª ALBAÑIL | 8.0 | sí | 0 | 2026-08-13 | 120 |
| `MO/0037` | 2798044 | OFIC. 2ª ALBAÑIL | **9.0** | **no** | 0 | 2026-08-19 | 29 |
| `MO/0366` | 1336571 | OFIC. 1ª ALBAÑIL | 8.0 | sí | 0 | 2026-07-04 | 119 |
| `MO/0405` | 1392590 | OFIC. 1ª ALBAÑIL | 8.0 | sí | 0 | 2026-08-17 | 153 |
| `MO/0456` | 1555819 | OFIC. 1ª ALBAÑIL | 8.0 | sí | 0 | 2026-08-13 | 160 |

**Conclusión: la lista del estudio sigue vigente en su totalidad.** Ningún
recurso está ya corregido, ninguno está de baja, ningún `candef` difiere de
lo esperado. La petición se puede lanzar tal cual.

### Vigencia del patrón 9-9-9-9-6 (2026, por recurso)

Se midió además el patrón registrado en 2026 por día de semana, para
comprobar que la petición sigue describiendo lo que la gente hace:

| Código | ene–mar 2026 | abr 2026 | may–jun 2026 | jul–ago 2026 |
|---|---|---|---|---|
| `MO/0006` | 10-10-10-10-8 | transición 10→9 | **9-9-9-9-6** | 9→7 (intensiva) |
| `MO/0007` | 10-10-10-10-8 | — | — | — |
| `MO/0008` | 10-10-10-10-8 | transición | **9-9-9-9-6** | 9-9-9-9-6 (1 sem.) |
| `MO/0031` | 10-10-10-10-8 | transición | **9-9-9-9-6** | 9→7 (intensiva) |
| `MO/0366` | 10-10-10-10-8 | transición | **9-9-9-9-6** | — |
| `MO/0405` | 10-10-10-10-8 | transición | **9-9-9-9-6** | 9→7 (intensiva) |
| `MO/0456` | 10-10-10-10-8 | transición | **9-9-9-9-6** | 9→7 (intensiva) |
| `MO/0037` | — (alta en jul.) | — | — | 7-7-7-7-7 (intensiva) |

Confirma H5 del estudio: **seis de los siete** hicieron el régimen de 42 h
(9-9-9-9-6) de mayo a junio de 2026 y están hoy en intensiva de verano
(7 h). El séptimo es el hallazgo 2.

## Hallazgos

### Hallazgo 1 (importante) · El código `MO/NNNN` NO identifica una sola ficha de recurso

`con.cod` está **repetido** entre fichas de recurso distintas. Medido:

| Código | fichas `res` con ese código | de ellas, de alta |
|---|---|---|
| `MO/0006` | **5** | 4 |
| `MO/0007` | **5** | 4 |
| `MO/0008` | **4** | 3 |
| `MO/0031` | 2 | 2 |
| `MO/0037` | 2 | 1 |
| `MO/0366`, `MO/0405`, `MO/0456` | 1 | 1 |

Y no son confusiones improbables: bajo `MO/0006` hay **otra** ficha de alta
(`res.ide` 1335318) que también es OFIC. 1ª ALBAÑIL, también con hora por
defecto `HLOF` y también con `candef = 8`. Lo mismo bajo `MO/0007`
(1335319 y 1984734) y bajo `MO/0008` (1335320). **Si RRHH busca por código,
tiene cuatro maneras de corregir la ficha equivocada.**

**Consecuencia sobre el encargo.** El encargo pedía citar los recursos
«SOLO por código `MO/NNNN`». Cumplirlo al pie de la letra habría producido
una petición **ejecutable de forma incorrecta**, que es justo el riesgo que
F-014 existe para evitar. La petición cita, además del código, el
**identificador interno de la ficha de recurso (`res.ide`)**, la
**categoría** y la **fecha del último parte registrado** (la ficha correcta
es, en los cinco casos ambiguos, la única con partes en 2026; las homónimas
no registran nada desde 2013, 2019, 2024 o mayo de 2025).

`res.ide` es un **identificador técnico de fila**, no un dato personal: no
es un DNI, ni un nombre, ni permite identificar a nadie fuera de Sigrid. Y
ya está versionado en este repositorio: el anexo A de
`specs/F-012-estudio-jornada-semanal/design.md` lo publica en su cláusula
`IN (1555819, 2146402, …)`. **La restricción del encargo (no versionar DNIs
ni nombres de personas) se respeta íntegra**: en `peticion_F-014.md` y en
este informe no aparece ningún DNI ni ningún nombre.

### Hallazgo 2 · `MO/0007` (ficha 2146403) no registra partes desde 2026-02-04

Figura **de alta** (`fecbaj = 0`) pero su última línea en `hmores` es del
**4 de febrero de 2026**: 22 líneas en todo 2026, todas de enero y de los
dos primeros días de febrero, con el patrón antiguo 10-10-10-10-8.
**Nunca llegó a hacer el régimen de 9 h**, que arrancó en mayo. Entró en la
lista de H5 por su histórico de 2025.

Ponerle `candef = 9` sería, hoy, una suposición sobre alguien que no
registra. No es un dato que el equipo de partes pueda decidir, así que **la
petición lo marca y devuelve la decisión a RRHH**, con las dos salidas
escritas y su efecto sobre la verificación:

- sigue en la cuadrilla ⇒ `candef = 9` como el resto ⇒ V1 devuelve 8 filas;
- ya no está o cambió de cuadrilla ⇒ no se le toca la jornada (y, si
  procede, se le da la baja que le falta) ⇒ V1 devuelve 7 filas.

No invalida la petición ni el estudio: los otros seis sí están haciendo
9-9-9-9-6 hoy, y el riesgo §10.6 de F-012 (F-014 antes que F-015) sigue
igual de vigente para ellos.

### Hallazgo 3 (menor) · `MO/0037` tiene una homónima antigua

`MO/0037` devuelve dos fichas: la correcta (2798044, OFIC. 2ª ALBAÑIL, de
alta, `candef = 9`, sin DNI) y una antigua (592326, OFIC. 1ª ALBAÑIL, baja
el 2017-11-02, `candef = 8`). La petición lo dice explícitamente para que
nadie «corrija» la de 2017.

### Hallazgo 4 (menor) · `MO/0037` sigue sin DNI a día de hoy

Confirmado el 2026-08-19: `res.conide = 0`, es decir la ficha de recurso no
enlaza con ninguna ficha de empleado, luego no hay DNI que leer. Sigue
registrando partes (última línea del **2026-08-19**, hoy mismo), así que el
hueco es actual y afecta al cruce con calendario/festivos de F-003.

## Decisiones tomadas

1. **La petición vive en `progress/peticion_F-014.md`**, no en
   `docs/referencia/`. Decisión del humano recogida en el encargo:
   `docs/referencia/` es para documentación que llega **de fuera** convertida
   a Markdown, y esto es un documento **propio y efímero** (deja de tener
   valor en cuanto RRHH lo ejecute).
2. **Se añade `res.ide` a la identificación de cada recurso.** Justificado en
   el hallazgo 1. Es la única desviación respecto a la letra del encargo, y
   se toma porque cumplirla habría hecho la petición ambigua.
3. **`MO/0007` se incluye, pero marcado, con la decisión devuelta a RRHH.**
   Alternativa descartada: sacarlo de la lista por su cuenta. El equipo de
   partes no sabe si esa persona sigue en la cuadrilla; RRHH sí.
4. **La verificación posterior se escribe como SQL literal**, no como script
   versionado. La feature es documental y `docs/ARCHITECTURE.md` ya lista
   las herramientas de consola del monorepo; añadir una cuarta para tres
   `SELECT` de un solo uso no se sostiene. El documento incluye el SQL
   exacto, el resultado esperado fila a fila y el recorte de código con el
   que lanzarlo.
5. **Tres verificaciones, no una.** V1 comprueba lo que se pidió, V2 es un
   control de daños sobre la distribución global de `candef` (que ningún
   otro recurso se haya movido) y V3 detalla las ocho fichas. Un cambio
   manual de datos maestros puede fallar por exceso tanto como por defecto.

## Verificaciones ejecutadas

### `bash harness/init.sh`

```
[OK] Arnés v1.4.0 (2026-08-13)
[OK] features.json válido
     16 features, 9 abiertas, en curso: ['F-014'], bloqueadas: ninguna
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 430 avisos (deuda previa, no bloquea)
15 passed in 4.59s
[OK] pytest en verde (con medición de cobertura)
[OK] servicio sv3-persistencia: pytest en verde
[OK] servicio sv4-front: pytest en verde
[OK] servicio sv5-transfer: pytest en verde
[OK] PUERTA COBERTURA: N/A (F-014 es de nivel documental: no exige cobertura)
[OK] Rama actual: feature/F-014-candef-9-sigrid
ENTORNO LISTO. Puedes trabajar.
```

Ejecutado al empezar (entorno limpio antes de tocar nada) y al terminar.
Ningún cambio de esta feature toca código, así que los números de la suite
son idénticos en las dos pasadas.

### Consultas a Sigrid

Tres pasadas de solo lectura contra `sigrid-api` (base `ruesma`), todas con
respuesta `ok = true` y sin truncar. **Cero escrituras**: las cuatro
consultas son `SELECT` puros; no se ejecutó ningún `UPDATE`, `INSERT` ni
`DELETE`, ni se usó ninguna credencial de escritura (que es exclusiva de
sv5).

## Estado de los criterios de `acceptance`

| # | Criterio | Estado |
|---|---|---|
| 1 | Petición redactada (docs/referencia o progress) con la lista de los 8 recursos, el cambio pedido (candef=9 en la hora por defecto HLOF; DNI en emp para MO/0037) y quién lo ejecuta en Sigrid | ✅ `progress/peticion_F-014.md`, apartados 3.2 (los 7 a 9 h), 3.3 (`MO/0037` y su DNI), 4 (lo que no se toca) y 5 (quién ejecuta). |
| 2 | Verificación por sigrid-api en solo lectura tras el cambio: los 7 recursos con candef=9 y MO/0037 con DNI en emp (SQL reproducible del anexo A de specs/F-012 §H1/H2) | ✅ Apartado 6 de la petición: V1 (H2 del anexo A, ampliada con el `tiene_dni`), V2 (H1 del anexo A, con el antes/después numérico) y V3 (detalle de las 8 fichas), cada una con su resultado esperado y el modo de lanzarla. **Pendiente de ejecutar**: solo tiene sentido cuando RRHH avise. |
| 3 | `bash harness/init.sh` en verde | ✅ Verde (salida arriba). |

## Qué queda pendiente (no lo puede hacer un agente)

1. **El humano envía la petición** a RRHH/Administración (bloque «texto para
   el correo», apartado 7 de `peticion_F-014.md`).
2. **RRHH ejecuta el cambio en Sigrid**: `candef` 8 → 9 en la línea `HLOF`
   de las 7 fichas (o 6, según decidan sobre `MO/0007`) y el DNI de
   `MO/0037`.
3. **RRHH responde qué decidió con `MO/0007`** (hallazgo 2). Sin esa
   respuesta, el resultado esperado de V1 es ambiguo entre 7 y 8 filas.
4. **El equipo de partes ejecuta V1, V2 y V3** y anota el resultado real en
   este informe. Hasta entonces, **F-015 no debe mergearse**: es el riesgo
   §10.6 del estudio (con la cuadrilla aún a `candef = 8`, la regla nueva
   marcaría sus viernes de 6 h como incompletos y generaría +2 h/semana de
   extra automática falsa).

Los puntos 1, 2 y 3 son **verificaciones MANUALES** fuera del alcance de
cualquier agente: nadie del sistema de partes escribe datos maestros en
Sigrid.

## Evidencias

Nivel de rigor **documental** (`harness/rigor.json`): `fase_red: false`,
`cobertura: false`, `mutacion: false`. F-014 no añade ni modifica **ninguna
línea de código ni de SQL de producción**: el diff son dos ficheros
Markdown en `progress/`.

| Evidencia | Valor medido | Cómo se obtuvo |
|---|---|---|
| Tests ejecutados y resultado | **15 passed, 0 failed** (suite raíz) + sv3, sv4 y sv5 en verde (caché: árbol de servicios sin cambios) | salida de `bash harness/init.sh` |
| Cobertura de las líneas cambiadas | **N/A** — la propia puerta lo declara: `PUERTA COBERTURA: N/A (F-014 es de nivel documental: no exige cobertura)`. No hay líneas de código cambiadas que cubrir. | línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| Mutantes generados y supervivientes | **N/A** — el nivel documental no exige mutación y, además, el diff no contiene código Python: una campaña generaría 0 mutantes por ausencia de alcance, no por falta de tests. No se lanzó `python -m harness.mutacion`. | `harness/rigor.json`, nivel `documental` |
| Tiempo de ejecución de la suite | **4.59 s** en la pasada final (`15 passed in 4.59s`, suite raíz; 3.00 s en la inicial — misma suite, la diferencia es ruido de máquina) | salida de la propia suite |
| Fase RED | **N/A** — `fase_red: false` para el nivel documental. Sin código no hay test que pueda fallar antes. | `harness/rigor.json` |
| Consultas a Sigrid | **4 consultas** de solo lectura, `ok = true`, sin truncar, 0 escrituras | scripts de scratchpad, salida en este informe |
| Ficheros de producción tocados | **0** (`services/**`, `orm_models.py`, tests: intactos) | `git show --stat` de los commits de la rama |
