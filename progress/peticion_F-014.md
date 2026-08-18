<!-- progress/peticion_F-014.md -->
# Petición a RRHH / Administración · Corregir la jornada por defecto (`candef`) de 8 recursos en Sigrid

- **Feature**: F-014 · «Poner candef=9 en Sigrid a los recursos que registran
  jornada de 9 h».
- **Fecha de redacción**: 2026-08-19.
- **Línea base medida**: 2026-08-19, contra Sigrid (base `ruesma`) en **solo
  lectura**, a través de `sigrid-api`. Nadie ha modificado nada desde el
  estudio del 2026-08-18: los ocho recursos siguen exactamente como allí se
  describen.
- **Quién ejecuta el cambio**: **RRHH / Administración**, a mano, en Sigrid.
  Los sistemas de partes **no escriben** datos maestros en Sigrid: esta
  petición es la única vía.
- **Quién verifica**: el equipo de partes, por consulta de solo lectura, en
  cuanto RRHH avise (apartado 6).

---

## 1. Resumen en una línea

A siete oficiales hay que cambiar en Sigrid **la cantidad por defecto de su
hora de trabajo de 8 a 9**, y a un octavo hay que **rellenarle el DNI**.
Nada más.

## 2. Por qué (en lenguaje de negocio)

El portal de partes de trabajo va a empezar a calcular **la jornada semanal
de cada trabajador a partir de su jornada diaria** grabada en Sigrid:

| jornada diaria en Sigrid | jornada semanal que asume el portal |
|---|---|
| 8 h | 40 h |
| 9 h | 42 h |

Los ocho trabajadores de esta petición **no hacen 8 h al día**: hacen
**9 h de lunes a jueves y 6 h el viernes = 42 h a la semana** (es lo que
Administración lleva registrando en Sigrid desde mayo de 2026; antes hacían
10-10-10-10-8 = 48 h, y en julio y agosto están en jornada intensiva de 7 h).

En Sigrid, sin embargo, **siete de ellos figuran con 8 h**. Si no se corrige:

- el portal daría por buena una jornada semanal de 40 h en vez de 42;
- **marcaría sus viernes de 6 h como jornada incompleta** (esperaría 8 h);
- y les **generaría automáticamente horas extra que no existen**: +1 h cada
  día de lunes a jueves y −2 h el viernes, es decir **+2 h de extra falsa
  por trabajador y semana**. Con el régimen antiguo de 48 h serían +8 h por
  semana.

Esas horas extra inventadas acabarían en los partes que revisa
Administración y, si se aprueban, en Sigrid. Corregir el dato en Sigrid
evita el problema de raíz: **la ficha del trabajador es la fuente, y es ahí
donde debe estar bien**.

El octavo (`MO/0037`) **ya tiene los 9 h correctos**, pero **le falta el
DNI**, que es la clave con la que el portal cruza a cada trabajador con su
calendario laboral y sus festivos. Sin DNI, el sistema lo trata con el
calendario genérico.

> **Importante para la planificación**: este cambio debe estar hecho
> **antes** de que se active la nueva regla de jornada semanal en el portal.
> Si se activa antes, aparecerán las horas extra falsas descritas arriba.

## 3. Qué hay que cambiar, recurso a recurso

### 3.1 Aviso previo: hay códigos `MO/NNNN` repetidos

En Sigrid, el código de recurso `MO/NNNN` **no identifica una sola ficha**:
al buscar `MO/0006` aparecen **cinco** fichas de recurso distintas (cuatro
de ellas de alta), y algo parecido pasa con `MO/0007`, `MO/0008`, `MO/0031`
y `MO/0037`. Varias son de la misma categoría (OFIC. 1ª ALBAÑIL) y también
tienen 8 h por defecto, así que **es fácil corregir la ficha equivocada**.

Por eso cada fila de la tabla lleva, además del código, el
**identificador interno de la ficha de recurso** (`res.ide`, el número que
Sigrid asigna a esa ficha), **la categoría** y **la fecha del último parte
registrado**. La ficha correcta es, en los cinco casos con código repetido,
**la única que tiene partes registrados en 2026**; las demás no registran
nada desde 2013, 2019, 2024 o mayo de 2025.

**Si al abrir una ficha los tres datos (código, identificador y categoría)
no cuadran a la vez, no la toques y pregunta.**

### 3.2 Los siete a los que hay que poner 9 h

Para cada uno: en su **ficha de recurso**, en la tabla de **horas del
recurso**, localizar la línea del **código de hora por defecto del recurso**
—que en los ocho casos es **`HLOF`** (mano de obra, oficial)— y cambiar su
**cantidad por defecto de `8` a `9`**.

| # | Código | Ficha de recurso (`res.ide`) | Categoría | Hora por defecto | Cantidad por defecto HOY | Cantidad por defecto PEDIDA | Último parte registrado |
|---|---|---|---|---|---|---|---|
| 1 | `MO/0006` | 2146402 | OFIC. 1ª ALBAÑIL | `HLOF` | **8** | **9** | 2026-08-13 |
| 2 | `MO/0007` | 2146403 | OFIC. 1ª ALBAÑIL | `HLOF` | **8** | **9** | 2026-02-04 ⚠️ |
| 3 | `MO/0008` | 2146404 | OFIC. 1ª ALBAÑIL | `HLOF` | **8** | **9** | 2026-07-16 |
| 4 | `MO/0031` | 2714845 | OFIC. 1ª ALBAÑIL | `HLOF` | **8** | **9** | 2026-08-13 |
| 5 | `MO/0366` | 1336571 | OFIC. 1ª ALBAÑIL | `HLOF` | **8** | **9** | 2026-07-04 |
| 6 | `MO/0405` | 1392590 | OFIC. 1ª ALBAÑIL | `HLOF` | **8** | **9** | 2026-08-17 |
| 7 | `MO/0456` | 1555819 | OFIC. 1ª ALBAÑIL | `HLOF` | **8** | **9** | 2026-08-13 |

⚠️ **`MO/0007` (ficha 2146403) necesita una decisión de RRHH.** Está de alta
en Sigrid (sin fecha de baja), pero **no registra partes desde el 4 de
febrero de 2026** y, por tanto, **nunca llegó a hacer el régimen de 9 h**,
que empezó en mayo. Entró en la lista por su histórico de 2025 (10-10-10-10-8).
Dos opciones, las dos válidas:

- **Si sigue en plantilla y en la misma cuadrilla** → cambiarlo a 9 como los
  demás.
- **Si ya no está o cambió de cuadrilla** → **no tocar su jornada** y, si
  procede, **darle la fecha de baja** que le falte. Avisadnos de cuál de las
  dos ha sido, porque cambia el resultado esperado de la verificación.

### 3.3 El octavo: `MO/0037`, al que le falta el DNI

| Código | Ficha de recurso (`res.ide`) | Categoría | Cantidad por defecto HOY | ¿Hay que tocar la jornada? | Qué falta |
|---|---|---|---|---|---|
| `MO/0037` | 2798044 | OFIC. 2ª ALBAÑIL | **9** ✅ | **NO** | **Falta el DNI**: la ficha de recurso no está enlazada con una ficha de empleado con DNI |

Es un alta reciente (su primer parte es del 13 de julio de 2026). Su jornada
ya está bien puesta en 9 h. Lo único que hay que hacer es **enlazar la ficha
de recurso con su ficha de empleado y que ésta tenga el DNI grabado**.

> Ojo: el código `MO/0037` también devuelve una segunda ficha antigua
> (`res.ide` 592326, OFIC. 1ª ALBAÑIL, dada de baja el 2017-11-02). **No es
> esa.** La correcta es la 2798044, la que está de alta y ya tiene 9 h.

## 4. Qué NO hay que tocar

Para que no haya dudas, el cambio se limita a lo de arriba. En concreto:

- ❌ **No tocar ninguna otra línea de horas** de estos recursos. Cada uno
  tiene entre 2 y 10 líneas de horas (`CIA`, `CIE`, `CIF`, `CIH`, `CIM`,
  `CIP`, `CIV`, `CIZ`, `HEOF`, `HEGR`, `HECAP`, `HLGR`, `MCAP`…). **Solo se
  cambia la línea `HLOF` que es la hora por defecto del recurso.** El resto
  se quedan con la cantidad que tienen hoy (0, en general).
- ❌ **No tocar los códigos de hora** en sí (la tabla de tipos de hora de
  Sigrid, `auxhor`): no se crean, ni se renombran, ni se cambian sus
  propiedades. `HLOF` sigue siendo `HLOF` para todo el mundo.
- ❌ **No tocar ningún otro recurso.** Hay 106 recursos con 8 h por defecto
  en Sigrid; **solo cambian los 7 de la tabla**. Los otros 99 se quedan en 8.
- ❌ **No tocar las fichas homónimas** que comparten código `MO/NNNN` con las
  de la tabla y que están listadas en el apartado 3.1 como «las que no».
- ❌ **No cambiar la categoría, la obra, el tipo de recurso ni las fechas de
  alta/baja** de ninguno de los ocho (salvo la posible baja de `MO/0007`, si
  RRHH decide que procede, según 3.2).
- ❌ **No modificar partes ya registrados**: esto es un cambio de ficha
  maestra, no toca el histórico. Los partes de julio y agosto se quedan como
  están.

## 5. Resumen para quien ejecuta

1. Abrir la ficha de recurso, comprobando **código + identificador +
   categoría** de la tabla 3.2.
2. En sus horas, línea **`HLOF`** (la marcada como hora por defecto del
   recurso): cantidad por defecto **8 → 9**.
3. Repetir para los 7 (o 6, si `MO/0007` queda fuera por lo de 3.2).
4. En `MO/0037` (ficha 2798044): **no tocar la jornada**; rellenar el DNI.
5. **Avisar al equipo de partes** de que está hecho, indicando qué se
   decidió con `MO/0007`.

---

## 6. Verificación posterior (la hace el equipo de partes, en solo lectura)

En cuanto RRHH avise, se vuelven a lanzar **las mismas consultas de la línea
base**, sin escribir nada, contra la base `ruesma` a través de `sigrid-api`
(`POST /api/sql/read`). Son las consultas H1 y H2 del anexo A de
`specs/F-012-estudio-jornada-semanal/design.md`.

### V1 · Los recursos con jornada por defecto de 9 h

```sql
SELECT res.ide, con.cod, auxrestip.res AS restip,
       CASE WHEN emp.dni IS NULL OR LTRIM(RTRIM(emp.dni)) = ''
            THEN 'sin' ELSE 'si' END AS tiene_dni,
       (SELECT COUNT(*) FROM reshor r2 JOIN auxhor a2 ON a2.ide = r2.horide
         WHERE r2.reside = res.ide AND a2.cod LIKE 'HE%') AS n_he
FROM reshor JOIN res ON res.ide = reshor.reside JOIN con ON con.ide = res.ide
LEFT JOIN auxrestip ON auxrestip.ide = res.restipide
LEFT JOIN emp ON emp.ide = res.conide
WHERE reshor.horide = res.horide AND reshor.candef = 9
  AND (con.fecbaj IS NULL OR con.fecbaj = 0)
ORDER BY con.cod
```

**Resultado esperado: exactamente 8 filas**, una por cada `res.ide` de la
lista, y **todas con `tiene_dni = 'si'`**:

| `res.ide` | `con.cod` | `tiene_dni` esperado |
|---|---|---|
| 1336571 | `MO/0366` | si |
| 1392590 | `MO/0405` | si |
| 1555819 | `MO/0456` | si |
| 2146402 | `MO/0006` | si |
| 2146403 | `MO/0007` | si |
| 2146404 | `MO/0008` | si |
| 2714845 | `MO/0031` | si |
| 2798044 | `MO/0037` | **si** ← hoy es `sin`; es el cambio pedido en 3.3 |

**Excepción prevista**: si RRHH decide que `MO/0007` (2146403) no procede
(apartado 3.2), el resultado esperado son **7 filas**, sin la de 2146403.
Cualquier otra desviación —una fila de más, una de menos, un `tiene_dni`
que siga en `sin`— es un fallo de la ejecución y hay que volver sobre él.

### V2 · Que no se haya tocado nada más (control de daños)

```sql
SELECT reshor.candef, COUNT(*) AS n
FROM reshor JOIN res ON res.ide = reshor.reside JOIN con ON con.ide = res.ide
WHERE reshor.horide = res.horide AND (con.fecbaj IS NULL OR con.fecbaj = 0)
GROUP BY reshor.candef ORDER BY n DESC
```

| `candef` | recursos ANTES (2026-08-19) | recursos ESPERADOS DESPUÉS |
|---|---|---|
| 1.0 | 561 | **561** (sin cambios) |
| 0.0 | 199 | **199** (sin cambios) |
| 8.0 | 106 | **99** (= 106 − 7) |
| 9.0 | 1 | **8** (= 1 + 7) |

Si aparece cualquier otro valor de `candef` (7, 10, 40…) o si las filas de
1.0 y 0.0 se mueven, **se ha tocado algo que no tocaba**.

### V3 · Estado detallado de las ocho fichas

```sql
SELECT con.cod AS cod, res.ide AS reside, auxrestip.res AS restip,
       auxhor.cod AS hora_defecto,
       (SELECT MAX(r3.candef) FROM reshor r3
         WHERE r3.reside = res.ide AND r3.horide = res.horide) AS candef,
       CASE WHEN emp.dni IS NULL OR LTRIM(RTRIM(emp.dni)) = ''
            THEN 'sin' ELSE 'si' END AS tiene_dni,
       ISNULL(con.fecbaj, 0) AS fecbaj
FROM res JOIN con ON con.ide = res.ide
LEFT JOIN auxrestip ON auxrestip.ide = res.restipide
LEFT JOIN emp ON emp.ide = res.conide
LEFT JOIN auxhor ON auxhor.ide = res.horide
WHERE res.ide IN (1555819, 2146402, 2146404, 1392590, 1336571,
                  2146403, 2714845, 2798044)
ORDER BY con.cod
```

Esperado: 8 filas, todas con `hora_defecto = 'HLOF'`, `candef = 9.0`,
`tiene_dni = 'si'` y `fecbaj = 0` (con la excepción de `MO/0007` descrita en
V1, que además podría pasar a tener `fecbaj` distinto de 0 si RRHH le da la
baja).

### Cómo se lanzan

No hace falta código nuevo: las tres consultas van por `sigrid-api`, en
**solo lectura**, con las credenciales que ya usa sv3
(`SIGRID_API_BASE_URL`, `SIGRID_API_FUNCTION_KEY`, `SIGRID_API_DATABASE` de
`services/partes-persistencia/.env`; **no se copian a ningún fichero**).
Un script de usar y tirar, fuera del repositorio, basta:

```python
# scratchpad/verificar_f014.py  (NO versionado)
import httpx
from pathlib import Path

cfg = {}
for l in Path("services/partes-persistencia/.env").read_text("utf-8").splitlines():
    if l.strip() and not l.startswith("#") and "=" in l:
        k, v = l.split("=", 1)
        cfg[k.strip()] = v.strip().strip('"').strip("'")

r = httpx.post(
    cfg["SIGRID_API_BASE_URL"].rstrip("/") + "/api/sql/read",
    json={"database": cfg["SIGRID_API_DATABASE"], "sql": SQL,
          "parameters": [], "timeout_seconds": 90, "max_rows": 1000},
    headers={"x-functions-key": cfg["SIGRID_API_FUNCTION_KEY"]},
    timeout=120,
)
print(r.json()["columns"]); [print(x) for x in r.json()["rows"]]
```

Sustituyendo `SQL` por V1, V2 o V3. Recordatorio: `sigrid-api` es el **único**
acceso a Sigrid, sirve como máximo 1.000 filas por petición y estas consultas
**no escriben nada**.

Cuando las tres verificaciones salgan como se espera, se anota el resultado
en `progress/impl_F-014.md` y la feature puede cerrarse.

---

## 7. Texto para el correo (copiar y pegar)

> **Asunto:** Corrección en Sigrid: jornada por defecto de 7 oficiales (8 → 9 h) y un DNI
>
> Hola:
>
> Necesitamos una corrección de fichas maestras en Sigrid antes de activar
> una mejora en el portal de partes de trabajo.
>
> El portal va a deducir la jornada semanal de cada trabajador a partir de su
> jornada diaria grabada en Sigrid (8 h ⇒ 40 h/semana, 9 h ⇒ 42 h/semana).
> Hay una cuadrilla de oficiales que hace **9 h de lunes a jueves y 6 h el
> viernes (42 h)** —es lo que venís registrando desde mayo— pero que en
> Sigrid figura con 8 h. Si no se corrige, el sistema marcará sus viernes
> como jornada incompleta y les generará unas 2 horas extra falsas por
> semana.
>
> **Lo que hay que hacer**, en la ficha de recurso de cada uno, en su línea de
> horas `HLOF` (la hora por defecto del recurso): cambiar la **cantidad por
> defecto de 8 a 9**. Nada más: ni otras líneas de horas, ni otros recursos.
>
> | Código | Ficha (identificador) | Categoría |
> |---|---|---|
> | MO/0006 | 2146402 | OFIC. 1ª ALBAÑIL |
> | MO/0007 | 2146403 | OFIC. 1ª ALBAÑIL |
> | MO/0008 | 2146404 | OFIC. 1ª ALBAÑIL |
> | MO/0031 | 2714845 | OFIC. 1ª ALBAÑIL |
> | MO/0366 | 1336571 | OFIC. 1ª ALBAÑIL |
> | MO/0405 | 1392590 | OFIC. 1ª ALBAÑIL |
> | MO/0456 | 1555819 | OFIC. 1ª ALBAÑIL |
>
> **Aviso importante:** varios de esos códigos `MO/NNNN` devuelven **más de
> una ficha** en Sigrid (MO/0006 devuelve cinco), algunas de la misma
> categoría. Por eso va el identificador de ficha en la tabla: es el que
> manda. Si el código, el identificador y la categoría no cuadran a la vez,
> no la toquéis y nos preguntáis.
>
> **Dos cosas más:**
>
> 1. **MO/0007 (ficha 2146403)** figura de alta pero no registra partes desde
>    el 4 de febrero. Decidnos si sigue en la cuadrilla (entonces le ponéis
>    los 9 h como al resto) o si ya no está (entonces no le toquéis la
>    jornada y, si procede, le dais la baja que le falta).
> 2. **MO/0037 (ficha 2798044, OFIC. 2ª ALBAÑIL)** ya tiene bien sus 9 h: a
>    éste **no le toquéis la jornada**. Lo que le falta es el **DNI**: su
>    ficha de recurso no está enlazada a una ficha de empleado con DNI, y sin
>    DNI no podemos cruzarlo con su calendario laboral y sus festivos.
>
> Cuando esté hecho, avisadnos y lo comprobamos por nuestra parte (solo
> lectura, no tocamos nada en Sigrid). Contadnos también qué se decidió con
> MO/0007.
>
> Gracias.

---

## Anexo · Línea base medida el 2026-08-19 (antes del cambio)

Distribución de la cantidad por defecto entre los recursos de alta:

| `candef` | recursos |
|---|---|
| 1.0 | 561 |
| 0.0 | 199 |
| 8.0 | 106 |
| 9.0 | 1 |

Estado de las ocho fichas (todas de alta, `fecbaj = 0`, hora por defecto
`HLOF`, y todas con un código de hora extra `HE%` disponible):

| Código | `res.ide` | Categoría | `candef` | ¿DNI? | Último parte |
|---|---|---|---|---|---|
| `MO/0006` | 2146402 | OFIC. 1ª ALBAÑIL | 8.0 | sí | 2026-08-13 |
| `MO/0007` | 2146403 | OFIC. 1ª ALBAÑIL | 8.0 | sí | 2026-02-04 |
| `MO/0008` | 2146404 | OFIC. 1ª ALBAÑIL | 8.0 | sí | 2026-07-16 |
| `MO/0031` | 2714845 | OFIC. 1ª ALBAÑIL | 8.0 | sí | 2026-08-13 |
| `MO/0037` | 2798044 | OFIC. 2ª ALBAÑIL | **9.0** | **no** | 2026-08-19 |
| `MO/0366` | 1336571 | OFIC. 1ª ALBAÑIL | 8.0 | sí | 2026-07-04 |
| `MO/0405` | 1392590 | OFIC. 1ª ALBAÑIL | 8.0 | sí | 2026-08-17 |
| `MO/0456` | 1555819 | OFIC. 1ª ALBAÑIL | 8.0 | sí | 2026-08-13 |

Coincide punto por punto con el estudio de F-012 del 2026-08-18: **nadie ha
tocado nada** en el intervalo.
