# F-051 · Extracción fila a fila — diseño técnico

## 1. Encaje y límite de servicio

- **sv2 (`services/partes-api/`)**, siempre: es quien lee el papel. El error nace
  aquí (el casado por DNI de sv3 fue correcto). Se tocan el prompt YAML y, con la
  DA1 = A, el esquema Pydantic `ParteTrabajo`, que es el JSON Schema que recibe
  el proveedor (`response_json_schema` en Gemini, `input_schema` en Claude).
- **sv3 (`services/partes-persistencia/`)**, solo si la DA2 ≠ A: `review_required`
  es suyo (`_compute_review_required`) y ya lee el payload de sv2 con `dict.get`.
  sv2 no conoce la revisión: meterle un juicio de negocio mezclaría extracción
  con decisión. Sin lógica duplicada: sv2 pide el dato y sv3 lo juzga.
- **Contrato sv2 → sv3**: una clave opcional por empleado (`numero_linea_horas`)
  que sv3 hoy ignora y guarda en `parte_documents.raw_extraction_json`; ningún
  esquema de BBDD cambia. **azure-apps** `partes.md` no describe los campos del
  sobre ni cambia lo expuesto o consumido: no se actualiza.

## 2. Ficheros a crear

| Ruta | Contenido |
|---|---|
| `services/partes-api/tests/test_f051_esquema.py` | R9–R12 (solo con DA1 = A) |
| `services/partes-api/tests/test_f051_prompt.py` | R1–R8 sobre el YAML real, como `test_f023_empresa_membrete.py` |
| `services/partes-persistencia/application/services/lectura_dudosa.py` | Detector puro (DA2 ≠ A) |
| `services/partes-persistencia/tests/test_f051_lectura_dudosa.py` | R13–R17 (DA2 ≠ A) |

## 3. Ficheros a modificar

| Ruta | Cambio |
|---|---|
| `services/partes-api/config/prompts.yaml` | Regla en `system`, bloque «LECTURA FILA A FILA» y viñeta `numero_linea_horas` en el punto 3 de `task`, claves en `schema_hint` (§5) |
| `services/partes-api/domain/models/parte_models.py` | Campo `numero_linea_horas` en `EmpleadoParte` tras `numero_linea` (DA1 = A) |
| `services/partes-persistencia/domain/models/parte_records.py` | `ParteDocumento.lectura_dudosa` (DA2 ≠ A) |
| `services/partes-persistencia/application/services/parte_normalizer.py` | Llama al detector y anota el parte (DA2 ≠ A) |
| `services/partes-persistencia/application/pipelines/persist_parte_pipeline.py` | `_compute_review_required`: `if parte.lectura_dudosa: return True` |
| `services/partes-persistencia/config/settings.py` | `revisar_tabla_dispersa: bool = Field(True, alias="REVISAR_TABLA_DISPERSA")` (solo DA2 = C) |
| `services/partes-persistencia/interface_adapters/api/app.py` | Pasa el flag al `ParteNormalizer` (solo DA2 = C) |
| `docs/ARCHITECTURE.md` | Una nota en sv2 (lectura fila a fila + autocomprobación) y, con DA2 ≠ A, la condición nueva de `review_required` |

## 4. Ficheros que NO se tocan

- sv2 fuera del YAML y `parte_models.py` (`application/**`, `infrastructure/llm/**`,
  `config/settings.py`): proveedor, modelo, resolución y reintentos no cambian;
  el enganche de R20 usa variables que ya existen.
- Las dos copias de `orm_models.py` (sin columna: el campo viaja en
  `raw_extraction_json`) y las gemelas de la lista cerrada de `CLAUDE.md`
  (`jornada_resolver`, `seleccion_sigrid`, `coherencia_recurso`, `congelacion`,
  `recurso_conciliador`): F-051 no toca casado, jornada ni congelación.
- `parte_normalizer.py` fuera de la llamada al detector (bucle de filas, salto
  de filas vacías, partidas y suma de extras de F-048), `medir_casado_recursos.py`.
- sv1, sv4, sv5 e `infra/` (el flag de DA2 = C nace a `true` y no necesita
  variable en Azure).

## 4 bis. Clases y funciones

- **domain (sv2)** `EmpleadoParte.numero_linea_horas: Optional[int] = None`,
  declarado entre `numero_linea` y `categoria`; comentario con su propósito.
- **application (sv3)** `lectura_dudosa.py`, sin dependencias de infraestructura:
  - `MOTIVO_AUTOCOMPROBACION = "autocomprobacion_fila"`,
    `MOTIVO_TABLA_DISPERSA = "tabla_dispersa"`.
  - `@dataclass(frozen=True) class MotivoLectura: motivo: str; filas: tuple[int | None, ...]`.
  - `def detectar_lectura_dudosa(empleados_raw: list[Any], *, tabla_dispersa: bool) -> list[MotivoLectura]`:
    recorre los dicts tal como llegan de sv2 (los no-dict se ignoran), «tiene
    horas» = ordinaria o extra no nula y ≠ 0, «trabajador» = `nombre` o `dni` no
    vacíos, «incidencia» = dict con `codigo` o `texto_leido`. Devuelve como mucho
    un motivo de cada tipo, con las filas implicadas (`numero_linea`) ordenadas.
- **domain (sv3)** `ParteDocumento.lectura_dudosa: list[MotivoLectura]`
  (`default_factory=list`). Para no importar application desde domain,
  `MotivoLectura` se declara en `domain/models/parte_records.py` y
  `lectura_dudosa.py` lo importa de ahí.
- **application (sv3)** `ParteNormalizer.__init__(..., revisar_tabla_dispersa: bool = True)`;
  `normalize` asigna `parte.lectura_dudosa` con el detector y, si no está vacía,
  escribe un `logger.warning` con motivo y filas.
- **application (sv3)** `PersistPartePipeline._compute_review_required`: `True`
  si `parte.lectura_dudosa`; el resto de condiciones, igual.

## 5. Prompt: texto propuesto (sv2)

Estilo del fichero: ASCII sin tildes, viñetas con `- `. El implementer puede
pulir la redacción, pero los tests (§6) fijan las palabras clave.

**`system`, al final de «Reglas absolutas»:**

```
      - Tabla de personal: cada cifra pertenece a la FILA en la que esta
        escrita. Identifica cada fila por su "Nº" y su DNI/nombre impresos;
        nunca asignes una cifra a la fila mas cercana ni a la de arriba.
```

**`task`, punto 3, tras el párrafo de entrada y antes de `- numero_linea`:**

```
       LECTURA FILA A FILA (MUY IMPORTANTE):
       - Recorre la tabla fila a fila por su "Nº" impreso (1, 2, 3...). Para
         cada fila, sigue SU linea desde el "Nº", el DNI y el nombre hasta las
         subcolumnas "Ord." y "Extraord." y lee SOLO lo que hay entre las dos
         lineas que delimitan esa fila. Igual para la incidencia y las horas
         de partidas de esa fila.
       - Una cifra pertenece a la fila que contiene su CENTRO, aunque el
         trazo invada la linea de la fila vecina.
       - Si el parte esta girado o inclinado, sigue las lineas de la tabla,
         no el borde de la pagina.
       - Celda vacia = null. NUNCA rellenes una fila con la cifra de la fila
         vecina ni muevas cifras de una fila a otra.
       - Con POCAS cifras sueltas (tipico de sabado o domingo) lo normal es
         que haya filas con trabajador y SIN horas: es justo el caso en que
         mas se desplazan las cifras. Antes de asignar una cifra, comprueba
         que el "Nº" y el DNI de SU franja son los de esa fila.
       - Incluye TODAS las filas con trabajador (nombre o DNI), tambien las
         que no tienen horas (horas a null), en el orden del papel.
```

**`task`, punto 3, viñeta nueva justo después de `- numero_linea` (DA1 = A):**

```
       - numero_linea_horas: el "Nº" impreso en la franja donde esta escrita
         la cifra de horas de esta fila, leido partiendo de la CIFRA hacia la
         columna "Nº". null si la fila no tiene horas. No lo copies de
         numero_linea sin mirarlo: sirve para comprobar que la cifra es de
         esta fila.
```

**`schema_hint`, objeto de `empleados`:** `{ "numero_linea", "numero_linea_horas",
"categoria", "nombre", "dni", "horas_ordinarias", ... }` (se añaden `dni`, que
faltaba, y `numero_linea_horas`); en «Reglas de tipo», una línea:
`numero_linea_horas es entero o null, nunca string`.

El resto del YAML (cabecera, firma, puntos 4–6) no cambia (R8).

## 6. Tests (sin red, sin modelo de IA, sin BBDD)

**`test_f051_prompt.py`** (fixture: `YamlPromptRepository(RUTA_PROMPTS).get("parte_trabajo_es")`,
texto normalizado con `" ".join(x.split()).lower()`):

- R1: `system` contiene «fila mas cercana» y «de arriba»; el bloque «lectura
  fila a fila» menciona `"nº"`, «dni» e «incidencia» y «partidas».
- R2: el bloque existe dentro del punto 3 (entre `3) EMPLEADOS` y
  `4) INCIDENCIA`) y contiene «fila a fila» y «ord.» y «extraord.».
- R3: contiene «celda vacia = null», «vecina», «pocas cifras».
- R4: contiene «girado», «inclinado» y «centro».
- R5: contiene «todas las filas con trabajador» y «horas a null».
- R6: hay viñeta `numero_linea_horas` en el punto 3, con «null» y «no lo copies».
- R7: el objeto de empleados del `schema_hint` contiene `"dni"` y
  `"numero_linea_horas"`.
- R8: sin test propio: los 8 tests de F-023 siguen pasando sin tocarlos y el
  reviewer comprueba con `git diff dev -- services/partes-api/config/prompts.yaml`
  que solo cambian `system` (una viñeta), el punto 3 y `schema_hint`.

**`test_f051_esquema.py`:** el campo admite entero y `null`; ausente ⇒ `None`
(R11); un 15 o un 0 no hacen fallar el parseo (R9, sin cotas); en
`model_json_schema()["$defs"]["EmpleadoParte"]["properties"]` el orden de claves
es `numero_linea`, `numero_linea_horas`, …, `horas_ordinarias` (R10); una clave
inventada sigue dando `ValidationError` (R12); un parte completo con el campo
hace `model_dump()` con la clave (llega a sv3).

**`test_f051_lectura_dudosa.py`** (DA2 ≠ A): tabla de casos sobre listas de
dicts como las de sv2: fila 1 con horas y `numero_linea_horas=2` ⇒ motivo
`autocomprobacion_fila` con fila 1 (R13); igual con valor nulo o ausente ⇒ nada
(R16); horas 0 o nulas con desajuste ⇒ nada; caso 17/10 tal como lo leyó Gemini
(filas 1–2 con horas, 3–5 con trabajador y sin horas) y tal como es en el papel ⇒
`tabla_dispersa` en los dos (R14); fila con incidencia y sin horas no cuenta como
vacía; parte con todas las filas con horas ⇒ nada; con el flag a `False` no hay
`tabla_dispersa`. Pipeline (con dobles, como `test_f003_r26_review_required.py`):
lectura dudosa ⇒ `review_required=True` y WARNING en `caplog` sin nombres ni DNIs
(R15); sin lectura dudosa, el resultado de `_compute_review_required` es el de
hoy (R17).

## 7. Decisiones abiertas (las valida el humano)

**DA1 · Forma de la autocomprobación.**
A) Campo por fila `numero_linea_horas`, antes de las horas (**recomendada**):
obliga al modelo a mirar el «Nº» desde la cifra y deja un dato comprobable;
coste: unos tokens por fila. B) Lista de cabecera `filas_con_horas` antes de
`empleados[]`: hace de «plan» y se contrasta con el conjunto de filas con horas;
cambia la raíz del esquema. C) Solo prompt, sin campo. Límite honesto de A y B:
si el modelo cree que la cifra está en la fila 1, puede escribir 1 en los dos
sitios; por eso la red de la DA2 no descansa solo en esto.

**DA2 · Red de seguridad (`review_required` por lectura dudosa), en sv3.**
A) Ninguna. B) Solo `autocomprobacion_fila` (R13): casi cero falsos positivos,
pero puede no saltar en el caso real. C) B + `tabla_dispersa` (R14) con el
interruptor `REVISAR_TABLA_DISPERSA` (por defecto `true`) (**recomendada**):
habría marcado los partes del 17 y 18/10; a cambio manda a revisión todo parte
con filas de trabajador sin horas, sobre todo los de fin de semana, que son
pocos y donde están las horas extra caras. Dato para decidir (solo lectura,
base `partes`, lo puede lanzar el líder antes de aprobar):

```sql
SELECT extract(isodow FROM d.fecha::date) >= 6 AS finde,
       count(*) AS partes,
       count(*) FILTER (WHERE con_horas > 0 AND vacias > 0) AS dispersos
FROM parte_documents d,
LATERAL (SELECT
   count(*) FILTER (WHERE coalesce((e->>'horas_ordinarias')::numeric, 0) <> 0
                       OR coalesce((e->>'horas_extraordinarias')::numeric, 0) <> 0) AS con_horas,
   count(*) FILTER (WHERE coalesce((e->>'horas_ordinarias')::numeric, 0) = 0
                      AND coalesce((e->>'horas_extraordinarias')::numeric, 0) = 0
                      AND coalesce(e->'incidencia', 'null'::jsonb) = 'null'::jsonb
                      AND (e->>'nombre' IS NOT NULL OR e->>'dni' IS NOT NULL)) AS vacias
 FROM jsonb_array_elements(d.raw_extraction_json::jsonb->'data'->'empleados') e) x
WHERE d.fecha >= '2026-06-01' GROUP BY 1;
```

(Orientativa: comprobar la forma del JSON guardado antes de fiarse del número.)
**DA3 · Criterio de aceptación de M1.** Propuesta: **3 de 3** ejecuciones
correctas por página (el modelo no es determinista). SI no se alcanza tras el
refuerzo, el implementer NO itera el prompt por su cuenta: marca `blocked` con
la tabla de resultados y el humano decide (otra vuelta de prompt, cambio de
modelo tras la comparativa, o aceptar con la red de la DA2).

## 8. Riesgos y alternativas descartadas

- **Regresión en partes que hoy se leen bien**: el texto nuevo podría vaciar
  filas llenas o retrasar cifras. Mitigación: M2 (R19) antes de desplegar.
- **Orden de generación**: Gemini genera en el orden del JSON Schema con
  `response_json_schema`; si el proveedor reordena, la autocomprobación pierde
  fuerza pero no rompe nada. Se observa en M1 con `IA_LOGGING_ENABLED=true`.
- **Más tokens** (un campo por fila, ~20 líneas de prompt): despreciable.
  **Falsos positivos de `tabla_dispersa`**: el interruptor lo apaga (DA2).
- Descartadas: **segunda lectura** con otro modelo y comparación (dobla coste y
  latencia; encaja mejor tras la comparativa de modelos); **recorte de la tabla
  por filas** antes de llamar al modelo (visión por computador sobre escaneos
  girados: frágil y grande); **bajar el umbral de confianza** (Gemini dio 95 en
  la lectura errónea: no discrimina); **few-shot con imágenes** (habría que
  versionar partes reales con datos personales).

## 9. Verificación manual (no versionada, la hace el humano o el líder)

**M1 (R18, R20).** Trocear el PDF del caso en 3 páginas (como sv1) fuera del
repo. En `services/partes-api` con el `.env` local (proveedor y modelo de
producción, `IA_LOGGING_ENABLED=true` opcional): `python main.py`; en otra
consola, por página y por ejecución:
`curl -s -F "file=@<ruta>/pagina_17.pdf;type=application/pdf" http://127.0.0.1:8010/v1/partes/extract`.
Anotar en `progress/impl_F-051.md` una tabla proveedor · modelo · página ·
ejecución · horas por fila · `numero_linea_horas` · correcto. Sin nombres ni DNIs.

**M2 (R19).** Igual con ≥ 5 partes laborables bien leídos hoy (los elige el
humano); comparar con las horas aprobadas en el portal. **Enganche (R20)**:
repetir M1/M2 cambiando solo `IA_PROVIDER`, `ENABLE_*`, `*_MODEL` y
`GEMINI_MEDIA_RESOLUTION` del `.env` local; la comparativa va aparte (líder).

## 10. Despliegue y rigor

- Sin orden obligado (sv3 ignora la clave nueva y el detector tolera su
  ausencia): sv2, y sv3 si DA2 ≠ A. Lo lanza el humano.
- Rigor propuesto: **`estandar`**. Cambia la lectura de horas que acaban en
  Sigrid, pero no escribe en ningún sistema compartido y la red solo puede
  subir `review_required`. La mutación cubre `parte_models.py` y
  `lectura_dudosa.py`; el texto del prompt no es mutable con sentido.
