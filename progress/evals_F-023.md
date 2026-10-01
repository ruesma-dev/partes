# Evals F-023 · M5: lectura del membrete (`cabecera.empresa_membrete`)

Fecha: 2026-10-01. Rama `dev`, con el código de F-023 ya integrado. Ejecución
local, solo lecturas. No se ha escrito nada en Azure, Blob, colas, PostgreSQL
ni Sigrid.

## Cómo se hizo

- **Fuente.** El contenedor Blob `input` de la cuenta de partes, leído con
  `--auth-mode login` tras concederse el humano «Storage Blob Data Reader».
  Tenía **12 documentos**, todos procesados en producción el 2026-09-30. Su
  envelope guardado (`envelopes/`) sirve de referencia. Dos de ellos
  (`46b6edf9` y `fd1b54a3`) son **la misma imagen** (mismo sha256, una JPEG
  guardada con extensión `.pdf`), así que hay **11 documentos distintos**.
  Las descargas se borraron al terminar.
- **sv2 en local.** `build_app(Settings()).state.pipeline.run(...)`, como en
  `main_worker.py`, desde un script en el scratchpad con
  `PYTHONPATH=services/partes-api`. Se lanzó con un venv temporal en el
  scratchpad (`infra/manifests/sv2/requirements.txt`, google-genai 2.26.0),
  porque el `.venv` de la raíz no trae `google-genai` ni `anthropic`. Como
  configuración, el `.env` local sin editar, más estas variables solo para
  el proceso:
  - `GEMINI_MODEL=gemini-3.7-flash`: es el `meta.model` de los 12 envelopes
    de producción y coincide con la Container App `ca-sv2-extraccion`.
  - `GEMINI_MEDIA_RESOLUTION=default`: la Container App no define esa
    variable, mientras que el `.env` local trae `high`. Se hizo además una
    segunda pasada con `high` como contraste.
  - `IA_LOGGING_ENABLED=false` y `LOG_DIR` en el scratchpad, para no dejar
    ficheros en el repo.

  A sv2 se le pasaron el mismo nombre y el mismo mime que recibió en
  producción (`meta.source_filename` y `meta.source_mime_type`). Primero se
  le mandaron como `application/pdf` y la JPEG dio 400 INVALID_ARGUMENT en
  Gemini: ese fallo era del script, no de F-023.
- **Empresa esperada (verdad de referencia).** Se decidió por la obra del
  parte en Sigrid: lectura por sigrid-api con `SigridApiClient` de sv3, base
  `ruesma`, `fetch_obras()` y `fetch_empresas()`. Los 12 partes son de la
  obra **0719**, que en Sigrid existe en **una sola empresa: la 1**
  (CONSTRUCCIONES RUESMA). La obra no es ambigua, así que no hizo falta
  mirar el membrete a mano.
- **Empresa resuelta.** `ResolutorEmpresa` de sv3, con
  `config/empresas_membrete.yaml` y las empresas reales de `auxemp` (39, la
  1 y la 28 válidas).
- **Comparación.** Cada extracción nueva se comparó con el envelope de
  producción del mismo documento:
  - **cabecera:** los 5 campos previos, `empresa_membrete` aparte;
  - **empleados:** emparejados por `numero_linea`, todos los campos menos
    `confianza_pct`;
  - **firma:** todos los campos menos `confianza_pct`.

## Resultado (modelo `gemini-3.7-flash`, media `default`, igual que producción)

| doc | sha256[:8] | tipo | empresa esperada | `empresa_membrete` leído | empresa resuelta | acierto | cab. con dif (de 5) | empleados guardado / nuevo | empleados con dif | campos dif en empleados | firma con dif |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 01f5c249 | 537247c9 | pdf | 1 | `ruesma` | 1 | sí | 1 (fecha, solo formato) | 3 / 3 | 0 | 0 | 0 |
| 28f19736 | f1e0883f | pdf | 1 | `ruesma` | 1 | sí | 0 | 3 / 3 | 0 | 0 | 1 (`firmante_rol`) |
| 46b6edf9 | 1e5cf423 | jpeg | 1 | `ruesma` | 1 | sí | 0 | 3 / 3 | 0 | 0 | 0 |
| 7df156eb | 0e74af7f | pdf | 1 | `ruesma` | 1 | sí | 0 | 3 / 3 | 1 | 1 (`horas_extraordinarias`) | 0 |
| 9ef823d2 | 2e080aa1 | pdf | 1 | `ruesma` | 1 | sí | 0 | 3 / 3 | 0 | 0 | 0 |
| c1bffa10 | c55fa4e6 | pdf | 1 | `ruesma` | 1 | sí | 0 | 3 / 3 | 0 | 0 | 0 |
| c996e211 | de1dd742 | pdf | 1 | `ruesma` | 1 | sí | 1 (fecha, solo formato) | 3 / 3 | 0 | 0 | 0 |
| da48e6bf | 2bc77871 | pdf | 1 | `ruesma` | 1 | sí | 0 | 3 / 3 | 0 | 0 | 1 (`firma_administracion`) |
| e0daed71 | 805812f9 | pdf | 1 | `ruesma` | 1 | sí | 0 | 3 / 3 | 0 | 0 | 1 (`firma_administracion`) |
| ee2e7742 | 9df141a3 | pdf | 1 | `ruesma` | 1 | sí | 0 | 3 / 3 | 0 | 0 | 0 |
| fd1b54a3 | 1e5cf423 | jpeg | 1 | `ruesma` | 1 | sí | 0 | 3 / 3 | 1 | 1 (`codigo_hora_ordinaria`) | 0 |
| fda32456 | 72972ffa | pdf | 1 | `ruesma` | 1 | sí | 1 (fecha, solo formato) | 3 / 3 | 0 | 0 | 0 |

**Totales.**

- **`empresa_membrete`:** 12/12 aciertos (11 documentos distintos), todos
  con `motivo=membrete`. No hubo ningún `sin_texto` ni `sin_alias`.
- **Cabecera:** las 3 diferencias son de `fecha` y solo de formato
  (`25/09/2026` frente a `25/9/2026`): es el mismo día.
  - `obra_numero`, `obra_nombre`, `encargado_nombre` y `jefe_obra_nombre`
    salen idénticos en los 12.
- **Empleados:** el recuento es idéntico en los 12 (36 líneas en total).
  - Dos líneas difieren en un campo cada una: una hora extra de más y el
    código `HENC` frente a `MENC`.
  - Nombres y DNIs salen idénticos en las 36.
- **Firma:** 3 diferencias en booleanos y rol de firma.

**Contraste con media `high`** (10 documentos, sin la JPEG duplicada):

- `empresa_membrete`: 10/10 `ruesma`, resuelta a 1.
- Cabecera: 3 fechas que difieren solo en formato.
- Empleados: mismo recuento. Hay 4 campos distintos en 2 líneas, todos de
  horas o código de hora.
- Firma: 3 diferencias.

**Variabilidad propia del modelo, sin relación con F-023.** La misma imagen
(`46b6edf9`/`fd1b54a3`) dio en local `HENC` en una pasada y `MENC` en la
otra. En producción, sus dos envelopes difieren entre sí en el formato de la
fecha. Las diferencias en horas, códigos y firma son de ese orden y no tocan
ningún campo afectado por el cambio del prompt.

## Limitaciones

- **No hay partes de PORSAN (28) en el Blob.** Los 12 son de una sola obra
  (0719) y de una sola empresa (1). No se cumple el «≥ 5 de cada empresa»
  de M5: la lectura del membrete de Porsan **no está evaluada**.
- Todo es un solo formato de parte, una obra y unos 10 días (16 al 28 de
  septiembre).
- El membrete se lee en minúscula (`ruesma`), seguramente porque así está
  el logotipo. El resolutor normaliza, así que no afecta.
- Esto no es un fallo, pero conviene saberlo. El alias `RUESMA` lo
  contienen también los nombres de otras empresas válidas de `auxemp`:
  - RUESMA SERVICIOS SL (18);
  - RUESMA-AVINTIA RIVAS UTE (15);
  - UTE VILLAS MASCARO RUESMA (27);
  - UTE RUESMA-INESCO TOLEDO (31);
  - PROPCO RUESMA SL (35);
  - RUESMA EKONS SYSTEM MADRID SL (39).

  Por diseño (DA3), un membrete con esos textos resolvería a la 1, porque
  la tabla de alias solo conoce la 1 y la 28. Si alguna de esas empresas
  llegara a emitir partes, habría que ampliar la tabla.

## Veredicto

- **CONSTRUCCIONES RUESMA (1): fiable.** Acierta 12 de 12 (11 documentos
  distintos) con la configuración de producción y 10 de 10 con media
  `high`, sin ningún falso «desconocido». Añadir el campo no ha degradado el
  resto de la extracción: cabecera y recuento de empleados idénticos, y las
  diferencias que quedan están dentro de la variabilidad normal del modelo.
- **PORSAN (28): sin evidencia.** No había ningún parte suyo en el Blob.
- **M5 queda cumplida a medias.**
  - Para cerrarla falta extraer al menos 5 partes de Porsan. Pueden venir de
    partes que entren en el Blob dentro de la ventana de 14 días o de PDFs
    que aporte el humano.
  - El riesgo de desplegar sv2 antes está acotado por el diseño (R9–R10,
    DA12). Un membrete de Porsan mal leído o no reconocido deja la obra sin
    casar y el parte en revisión: nunca escribe en otra empresa.
  - Decidir si se despliega antes de completarla le corresponde al humano.
