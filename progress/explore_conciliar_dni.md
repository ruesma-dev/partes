# Exploración · Conciliar propone varios recursos aunque el parte trae DNI (2026-11-03)

Diagnóstico **solo lectura** pedido por el líder a raíz de la queja del humano
(2026-11-03): «me sale en conciliar varios recursos cuando vienen con dni en el
parte», y su dato posterior: **ahora todas las tarjetas de Conciliar tienen un
candidato claro, alguno al 100 %, y «esto antes no pasaba»**. Caso real:
candidato al 100 % el recurso **MO/0667** (`res.ide` 2364457, empresa 1,
ficha `emp` 2346204), los otros cuatro al 56 %.

No se ha cambiado código ni de rama. Sin nombres ni DNI reales: solo ides.

## 0. Conclusión corta

1. **Los «varios recursos» de Conciliar son el ranking por nombre de sv4, que
   no ve el DNI.** La tarjeta enseña hasta 5 recursos por parecido de nombre
   (`empleado_reconciler.py:46-62`, `app.py:1400-1401`). El DNI leído **no se
   guarda en la línea** (no hay columna: `orm_models.py:205-214`;
   `sqlalchemy_parte_repository.py:1030-1041`), así que sv4 no podría
   filtrar por él aunque quisiera. Los cuatro al 56 % son solo parecido de
   nombre.
2. **Con los maestros de hoy, sv3 casa la línea de MO/0667 sin problema**:
   reproducido con el código de sv3 contra Sigrid real (§3). Da `dni` (con
   DNI) o `nombre` a 1.0 (sin DNI), con empresa 1 y también sin empresa. La
   ficha está de alta desde 2024-06-10, el DNI de la ficha coincide con
   `res.cif`, hay una sola ficha y un solo recurso persona, y
   `ficha.reside = res.ide`. **Que esa línea esté en la cola significa que,
   cuando se ingirió, sv3 casó con un índice que no tenía a esa persona (o no
   le llegaron ni el DNI ni el nombre).** No es un fallo de la regla de
   casado.
3. **No hay cambios en la regla de casado desde el 2026-10-08** (F-040), ni en
   lo que sv2 lee del DNI y del nombre desde el 2026-10-19 (F-051) (§4).
   F-047, F-058/F-063, F-054 y F-038 no tocan el casado del trabajador.
4. **Hipótesis principal de la regresión** (sin cerrar: hace falta producción):
   **los maestros de Sigrid fallaron al cargar en el worker y sv3 casó con un
   índice vacío.** `SigridMatcherProvider.get` (`sigrid_matcher_provider.py:83-98`),
   si la carga falla y no hay caché, monta **matchers vacíos**
   (`_empty`, `:131-132`) **y los guarda 600 s como buenos** (`:96-97`). Con
   el worker KEDA a 0 réplicas, cada arranque en frío empieza sin caché: un
   fallo en la primera carga deja sin casar **todos** los partes de esa
   tanda (trabajador, obra y código de hora), y sin avisar en la línea. Encaja
   con «ahora todas las tarjetas tienen un candidato claro». Cómo confirmarlo:
   §6.
5. Recomendación (§7): primero lanzar las consultas de §6. Si se confirma,
   **arreglo en sv3**: que un fallo de los maestros no persista el parte sin
   casar (reintento del mensaje) y que el conciliador no pase con un índice
   vacío. Después, **en sv4**: guardar el DNI leído en la línea y que
   Conciliar ponga primero el recurso con ese DNI.

## 1. Recorrido de una línea con DNI

| Paso | Dónde | Qué pasa |
|---|---|---|
| sv2 lee el DNI | `services/partes-api/config/prompts.yaml:112-117` (instrucción), `:203-204` (`schema_hint` con `dni`, desde F-051 c5c9cf8, 2026-10-19); `services/partes-api/domain/models/parte_models.py:80-82` (`EmpleadoParte.dni`) | Copia el DNI tal cual o `null`. |
| sv2 → sv3 | La relectura de F-058 solo cambia la cabecera; `empleados` siguen siendo los de la primera lectura (`extract_parte_pipeline.py:205-208`) | El DNI y el nombre llegan intactos. |
| sv3 normaliza | `parte_normalizer.py:181-184` (`nombre`, `dni_canonico`), `:37-46` (ceros a la izquierda hasta 8 dígitos), `:230` | `RegistroNormalizado.trabajador_dni_leido` (`parte_records.py:86`). Contra el maestro de hoy, `dni_canonico` no altera ningún DNI (§3). |
| sv3 casa (antes de guardar) | `persist_parte_pipeline.py:189-195` → `_match` `:338-414` → `_casar_trabajador` `:417-441` → `casado_recurso.casar_trabajador` `casado_recurso.py:49-86` | Orden: DNI → alias → nombre. Caché por `DNI|nombre` dentro del parte (`persist_parte_pipeline.py:383-392`). |
| Empresa del parte | `persist_parte_pipeline.py:91-104` y `:361-363` | La de la obra casada; si no hay obra, la del membrete; si no, `None` (= todas las empresas). |
| Se guarda | `sqlalchemy_parte_repository.py:1030-1041` | Columnas `empleado_ide`, `empleado_codigo`, `empleado_nombre`, `empleado_dni` (**DNI del recurso casado, no el leído**), `empleado_reside`, `empleado_match_score`, `empleado_match_method` (`orm_models.py:205-214`). **`trabajador_dni_leido` no se guarda**: solo queda dentro de `parte_documents.raw_extraction_json` (`orm_models.py:183`). |
| Conciliador de recurso | `recurso_conciliador.py:411-438` | Usa `empleado_dni`/`empleado_ide`/`empleado_reside` **ya guardados**. En una línea sin casar son NULL, así que no puede rescatarla por el DNI leído. |

### 1.1 Cómo casa sv3 la ficha y el recurso por DNI

- Índice: fichas por DNI normalizado (`seleccion_sigrid.py:98-102`); recursos
  **persona** (`res.cla = 1`) por `conide` y por `res.cif` (`:113-118`).
- `casar_por_dni` (`seleccion_sigrid.py:226-237`): primero `elegir_ficha`
  (`:259-276`, la ficha de alta en la empresa del parte). Si sale `ok`, llama
  a `elegir_recurso` con preferido = `ficha.reside`; si no, sin ficha ni
  preferido.
- `elegir_recurso` (`:278-319`): los candidatos son los recursos de la persona
  de alta y de la empresa. Si no queda ninguno: `otra_empresa` o `solo_baja`.
  Si quedan varios, `_desempatar` (`:322-336`): el único, después el
  preferido, después el único enlazado a la ficha. Si con eso no hay uno
  solo: `ambiguo`.
- Resultado guardado (`casado_recurso.py:163-179`): con ficha enlazada
  `empleado_ide` = ficha y método `dni`, `alias` o `nombre`; sin ficha,
  `empleado_ide` NULL y método `recurso_dni` o `recurso_nombre` (estos cuentan
  como casados en sv4).

### 1.2 Casos en que una línea CON DNI acaba en la cola de Conciliar

La cola es `empleado_ide IS NULL` y método fuera de
`recurso_dni`/`recurso_nombre`/`recurso_manual` (`parte_repository.py:551-576`
de sv4).

| # | Situación | `empleado_match_method` | Código |
|---|---|---|---|
| a | DNI con varios recursos candidatos y sin desempate | `dni_ambiguo` | `casado_recurso.py:66-70`, `seleccion_sigrid.py:316-318` |
| b | Todos sus recursos de baja a la fecha del parte | `dni_solo_baja` | ídem, `seleccion_sigrid.py:313-315` |
| c | Recursos de alta, pero de otra empresa que la del parte | `dni_otra_empresa` | ídem |
| d | Sigrid conoce el DNI (ficha o recurso de cualquier clase) pero no tiene recurso persona | `dni_sin_recurso` | `casado_recurso.py:74-75`, `seleccion_sigrid.py:134-139` |
| e | DNI desconocido (mal leído o no está en el maestro) y luego un alias que no vale | `alias_no_valido` (o `dni_<motivo>` si el alias apunta a un DNI en a-c) | `casado_recurso.py:76-79`, `:89-129` |
| f | DNI desconocido, sin alias, y el nombre no supera el umbral o no hay candidatos | `none` | `casado_recurso.py:80-86`, `empleado_matcher.py:50-64` |
| g | DNI desconocido; por nombre empatan dos personas | `nombre_ambiguo` | `empleado_matcher.py:65-67` |
| h | DNI desconocido; gana por nombre una persona SIN DNI | `nombre_sin_dni` | `casado_recurso.py:153-156` |
| i | DNI desconocido; gana por nombre una persona cuyo DNI no resuelve | `nombre_ambiguo` | `casado_recurso.py:157-159` |
| j | **Maestros vacíos** (la carga de Sigrid falló y no había caché): todo DNI es «desconocido» | `alias_no_valido` (si hay alias) o `none`; además la obra y el código de hora sin casar | `sigrid_matcher_provider.py:83-98`, `:131-132` |
| k | Sigrid no cableado (faltan `SIGRID_API_*`) | NULL | `persist_parte_pipeline.py:190-195`, `interface_adapters/api/app.py:152-157` |

Detalle menor, no es la causa: en `_desempatar` con `empleado_ide = None`
(ficha no `ok`), la regla «el único de la ficha» compara `r.conide == None`
(`seleccion_sigrid.py:333`). Elegiría el único recurso sin ficha enlazada.
No es un error que se vea hoy.

## 2. Por qué Conciliar enseña varios recursos

- **Confirmado: ranking solo por nombre.** `GET /conciliacion`
  (`services/partes-front/interface_adapters/web/app.py:1383-1425`):
  candidatos = recursos activos de la empresa de los partes del nombre (o de
  todas si hay más de una o ninguna, `:1394-1399`), y `recon.classify` con
  `top_n=5` (`:1400-1401`). Puntúa con `name_similarity` y enseña todo lo que
  supera 0,55 (`empleado_reconciler.py:22-24`, `:46-62`). Los «56 %» son eso.
  El bucket «auto» (≥ 0,85 y 0,10 de margen, `:76-80`) solo cambia la
  etiqueta: los otros candidatos se siguen enseñando.
- **La cola agrupa por nombre leído y pierde el DNI** (`parte_repository.py:3021-3089`):
  la línea no tiene el DNI leído (§1) y el grupo no lleva DNI ni método.
- **La búsqueda manual tampoco busca por DNI**, aunque el campo lo promete:
  el placeholder dice «por nombre, código o DNI»
  (`templates/conciliacion.html:97`), pero `/api/conciliacion/buscar` compara
  nombre y código (`app.py:1519-1525`).
- **Otras causas, descartadas para MO/0667** (comprobado en §3):
  - Persona con varios recursos de alta en la misma empresa: no (uno solo).
  - DNI de la ficha distinto de `res.cif`: no (coinciden).
  - Formato del DNI: `dni_canonico` no lo cambia.
  - Empresa: un solo recurso, en la empresa 1, y casa también con empresa
    `None`.
  - Catálogo de sv4 sin DNI: no. `RecursoOption.dni` = `res.cif` o, si está
    vacío, el de la ficha (`sigrid_lookup_client.py:371-372`). Ojo: es la
    prioridad **inversa** a la de sv3, que usa primero el de la ficha y
    después `res.cif` (`seleccion_sigrid.py:146-151`, F-036 DA1). Hoy importa
    en 2 recursos de la empresa 1 (medición del 2026-10-08,
    `services/partes-persistencia/logs/medicion_casado_20261008-2342.md`).
    Hay que tenerlo en cuenta si sv4 va a comparar con el DNI leído.

## 3. Datos reales (Sigrid, solo lectura, 2026-11-03)

Script `diag_mo0667.py` en el scratchpad del líder. Usa el cliente y la regla
de sv3, solo `/api/sql/read`, y no imprime nombres ni DNI. Maestros: 1.357
fichas, 925 obras y 2.637 recursos. Cada lectura tarda unos 4,5 s desde local.

**MO/0667** (`res.ide` 2364457):

- `cla = 1` y de alta (`con.fecbaj = 0`), empresa 1.
- `conide` 2346204: la ficha está en el maestro, de alta, empresa 1, con
  `emp.fecalt = 20240610`.
- La ficha tiene DNI y `res.cif` es igual. Una sola ficha con ese DNI y un
  solo recurso persona. `ficha.reside = 2364457`.

| empresa | con DNI | nombre | resultado de `casar_trabajador` |
|---|---|---|---|
| 1 | sí | el del recurso o el de la ficha | `dni`, ide 2346204, reside 2364457, 1.0 |
| 1 | no | el del recurso o el de la ficha | `nombre`, ide 2346204, reside 2364457, 1.0 |
| None | sí / no | ídem | igual que con empresa 1 |

El resto de recursos de la empresa no pasa de 0,56 de parecido con su
nombre, igual que en la tarjeta.

**Agregados** (recursos persona de alta hoy):

- 283 recursos persona; 7 sin DNI; 267 DNI distintos.
- Pares (DNI, empresa) con más de un recurso persona de alta: **1** (empresa
  1). `casar_por_dni` en su empresa da `ok` 274 veces y `ambiguo` **1**.
- DNI con recursos de alta en más de una empresa: **8**. Con empresa `None`
  (parte sin obra ni membrete), `ambiguo` sale **7** veces.
- DNI que cambia `dni_canonico`: 0. Nombres repetidos dentro de una empresa:
  0.

⇒ La ambigüedad real por DNI es marginal (1 persona; 7 si el parte no tiene
empresa). No explica que «todas» las tarjetas tengan candidato claro.

**Base `partes` local** (`localhost`): **desfasada, no sirve**. 69 partes; el
último, del 2026-10-26. Del 2026-10-25 y 26 solo hay 28 líneas, todas con
`empleado_ide`. No llega al despliegue de F-047 (31/10). No se ha intentado
la base de producción.

## 4. Qué cambió en los despliegues recientes (`git log -p`)

- **Regla de casado de sv3** (`casado_recurso.py`, `seleccion_sigrid.py`,
  `empleado_matcher.py`, `sigrid_matcher_provider.py`, `text_match.py`): el
  último cambio es F-040 (0665eeb, 2026-10-08). En `parte_normalizer.py` solo
  han entrado F-048 (extras leídas) y F-051 T7 (detector de lectura dudosa,
  `parte_normalizer.py:157-172`), que no tocan nombre ni DNI
  (`:181-184` sin cambios).
- **F-047** (sv3 r20261031093921): el casado sigue **antes** de `save_parte`
  (`persist_parte_pipeline.py:189-195` frente a `:208`). F-047 solo añade el
  pedido en el mismo commit y la marca después de conciliar (bd2ee7a,
  521d93d). `save_parte` sigue escribiendo `empleado_*` (`:1035-1041`).
  **Descartado** como causa directa.
- **F-058/F-063** (sv2, 2026-10-26): la relectura sustituye solo `cabecera`
  (`extract_parte_pipeline.py:205-208`). Firma y empleados se quedan como en
  la primera lectura. **Descartado** que pierda el DNI o el nombre. Efecto
  indirecto posible: una cabecera releída cambia la obra o el membrete, y con
  ello `parte.empresa`. Si esa empresa es otra, la línea cae en
  `dni_otra_empresa` (caso c). Pero entonces Conciliar ofrecería recursos de
  esa otra empresa, no MO/0667 de la empresa 1, salvo que el nombre tenga
  partes de varias empresas.
- **F-051** (2026-10-19): añadió `dni` al `schema_hint` y la lectura fila a
  fila (c5c9cf8). El DNI por fila sigue saliendo.
- **F-054** (sv3, 2026-10-23): solo `review_required` y un WARNING
  (`persist_parte_pipeline.py:453-456`).
- **F-038** (sv3, 2026-10-24): `max_rows` 500.000 por defecto, pero todas las
  lecturas de sv3 son paginadas y no lo usan
  (`sigrid_api_client.py:220-401`, `_leer_paginado` `:422`). `timeout_s`
  sigue en 30 s, que ahora tiene tope de 200. Descartado.

Ningún cambio de código explica por sí solo la regresión. Lo que sí la
explicaría sin cambio de código es el caso **j**: un fallo de carga en un
arranque en frío del worker, por un timeout de 30 s contra sigrid-api, un
error de red o un 5xx. Las consecuencias:

- se guardan matchers vacíos durante 600 s (`sigrid_matcher_provider.py:95-97`);
- **todas** las líneas de esa tanda quedan sin casar;
- además, la pasada del conciliador con ese índice vacío
  (`recurso_conciliador.py:240-244`, `:497-528`) pone `recurso_ide = NULL` y
  `sin_recurso` en todas las líneas no congeladas, hasta la siguiente pasada
  buena.

## 5. Lo que no se puede cerrar sin producción

Para saber cuál de los casos a-k produce la cola hay que ver
`empleado_match_method`, la fecha de ingesta y si la obra y la hora también
quedaron sin casar. Las firmas son:

- **j** (maestros vacíos): `none`/`alias_no_valido` con `obra_ide` NULL y
  `hora_ide` NULL en todo el parte, y partes concentrados en ventanas de 10
  minutos.
- **k** (Sigrid no cableado): método NULL.
- **c** (empresa cambiada): `dni_otra_empresa`.

## 6. Consultas para el humano (solo lectura)

Base `partes` de producción, en sesión de solo lectura
(`PGOPTIONS='-c default_transaction_read_only=on'`):

```sql
-- Q1. La cola de Conciliar por día de ingesta y método, con las señales del caso j.
SELECT substr(d.created_at_utc, 1, 10)                       AS dia,
       r.empleado_match_method                                AS metodo,
       count(*)                                               AS lineas,
       count(DISTINCT d.id)                                   AS partes,
       count(*) FILTER (WHERE d.obra_ide IS NULL)             AS sin_obra,
       count(*) FILTER (WHERE r.hora_ide IS NULL
                          AND NOT r.es_incidencia)            AS sin_hora
FROM parte_registros r
JOIN parte_documents d ON d.id = r.document_id
WHERE d.is_active AND r.deleted_at_utc IS NULL
  AND r.empleado_ide IS NULL
  AND (r.empleado_match_method IS NULL
       OR r.empleado_match_method NOT IN ('recurso_dni','recurso_nombre','recurso_manual'))
GROUP BY 1, 2
ORDER BY 1, 2;

-- Q2. Tasa de casado de lo ingerido por sv3 (no manual) por día, desde el 15/10.
SELECT substr(d.created_at_utc, 1, 10) AS dia,
       count(*) AS lineas,
       count(*) FILTER (WHERE r.empleado_ide IS NOT NULL
             OR r.empleado_match_method IN ('recurso_dni','recurso_nombre')) AS casadas,
       count(*) FILTER (WHERE r.empleado_match_method = 'dni')    AS por_dni,
       count(*) FILTER (WHERE r.empleado_match_method = 'nombre') AS por_nombre,
       count(*) FILTER (WHERE d.obra_ide IS NULL)                 AS sin_obra
FROM parte_registros r
JOIN parte_documents d ON d.id = r.document_id
WHERE d.created_at_utc >= '2026-10-15' AND d.source_mime_type <> 'manual'
GROUP BY 1
ORDER BY 1;

-- Q3. Las líneas de la tarjeta de MO/0667: el humano pone el nombre leído
-- (no se escribe aquí). Dice cuándo entraron, con qué método y si la
-- extracción traía DNI en esa fila.
SELECT r.id, d.id AS document_id, d.created_at_utc, d.empresa, d.obra_ide,
       d.obra_match_method, r.empleado_match_method, r.recurso_ide,
       EXISTS (
         SELECT 1
         FROM jsonb_array_elements(d.raw_extraction_json::jsonb -> 'data' -> 'empleados') e
         WHERE e ->> 'numero_linea' = r.empleado_line_no::text
           AND coalesce(e ->> 'dni', '') <> ''
       ) AS dni_en_extraccion
FROM parte_registros r
JOIN parte_documents d ON d.id = r.document_id
WHERE d.is_active AND r.deleted_at_utc IS NULL AND r.empleado_ide IS NULL
  AND lower(trim(r.trabajador_nombre_leido)) = lower(trim(:nombre_leido))
ORDER BY d.created_at_utc;
```

Log Analytics de sv3, últimos 10 días (`ContainerAppConsoleLogs_CL`,
`ContainerAppName_s == "ca-sv3-persistencia"`, `Log_s has "[matcher-provider]"`):

- `fallo cargando maestros` sin un `se reutiliza el cache anterior` detrás
  ⇒ **caso j confirmado**.
- `maestros cargados: … recursos=N` con N muy por debajo de unos 2.600 ⇒
  maestro incompleto.
- `Sigrid NO cableado` ⇒ caso k.

## 7. Opciones de arreglo (sin implementar)

| # | Qué | Servicio | Gemelos | Valoración |
|---|---|---|---|---|
| 1 | **Fallo de maestros sin caché ⇒ no persistir sin casar.** `SigridMatcherProvider.get` lanza en vez de devolver `_empty()` (o al menos no lo guarda 600 s), y el mensaje de `q-persistencia` se reintenta. Con índice vacío, el conciliador no hace la pasada (no borra `recurso_ide`). | sv3 (`sigrid_matcher_provider.py:83-98`, `recurso_conciliador.py:240-244`) | No | **Recomendada si Q1 o los logs confirman el caso j.** Arregla la causa. Riesgo: un Sigrid caído deja mensajes en reintento o en la DLQ en vez de partes sin casar; hay que revisar el `maxDeliveryCount` de la cola. |
| 2 | **Guardar el DNI leído** en `parte_registros` (`trabajador_dni_leido`) para que sv4 y el conciliador lo vean. | sv3 + sv4 | **Sí**: `infrastructure/database/orm_models.py` (las dos copias) + DDL | Requisito de 3 y 4. Barato. Necesita backfill desde `raw_extraction_json`, como ya hace `medir_casado_recursos.py:64-81`. |
| 3 | **Conciliar por DNI**: la tarjeta lleva el DNI leído y pone primero (o solo) el recurso cuyo DNI coincide (`dni` de `RecursoOption`; ojo con la prioridad cif/ficha inversa, §2), con la etiqueta «DNI coincide». La búsqueda manual busca también por DNI. | sv4 (`app.py:1383-1425`, `:1505-1533`, `parte_repository.py:3021-3089`, `conciliacion.html`) | No (salvo 2) | Recomendada después de 1. Es lo que el humano pide literalmente. Agrupar por nombre **y** DNI evita mezclar a dos personas con el mismo nombre leído. |
| 4 | **Re-casar en la pasada del conciliador** las líneas en cola con DNI leído cuando el índice ya resuelve `ok`. | sv3 | No (con 2) | Repara solo las tandas malas, pero contradice F-036 DA2 («lo ingerido no se re-casa»): decisión del humano. Riesgo de pisar un casado manual: solo líneas sin casar y no congeladas. |
| 5 | Ordenar la prioridad del DNI de `RecursoOption` (ficha antes que `res.cif`) para que coincida con sv3. | sv4 (`sigrid_lookup_client.py:371-372`) | Toca el criterio de candidatos de F-035/F-036; no está en la lista cerrada, pero conviene vigilarlo como los demás | Menor; solo si se hace 3. |

**Recomendación:** antes de diseñar nada, lanzar Q1, Q2 y la consulta de logs.
Si sale el caso j, la feature es la opción 1 (sv3, sin gemelos) y, para
limpiar la cola actual, Conciliar con un clic o la opción 4. Después, 2 + 3
como mejora de Conciliar. Si en cambio Q1 da `dni_otra_empresa` o
`dni_ambiguo`, la causa es la empresa del parte (relectura de cabecera u obra
sin casar) y hay que mirar `d.empresa` y `obra_match_method` de esos partes.

## 8. Comprobaciones del líder (2026-11-03)

- **Caso j DESCARTADO.** Log Analytics de `ca-sv3-persistencia`, 14 días: ningún
  `fallo cargando maestros`. Todas las cargas traen `empleados=1356-1357 recursos=2636-2637`
  (revisiones r20261024215445 y r20261031093921). El índice vacío no explica la cola.
- **MO/0667 (res.ide 2364457) está limpio en Sigrid**: un único recurso con ese `cif`, `cla = 1`,
  empresa 1, sin baja; ficha `emp` 2346204 enlazada en los dos sentidos (`conide` y `reside`)
  y con el mismo DNI que el recurso. No es un alta reciente (los últimos `emp` y `res` son otros).
- sv3 no registra en el log el casado por línea, así que la causa solo se puede ver en la base
  `partes` de producción: Q1, Q2 y Q3 del §6. Hay que añadir a Q3 `d.source_mime_type`
  (`manual` = parte creado en el portal), para distinguir los partes ingeridos de los manuales.
