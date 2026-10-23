<!-- specs/F-059-pagina-como-imagen-derecha/design.md -->
# F-059 · La IA no lee bien el PDF con /Rotate: la página va ya derecha — diseño técnico

## 1. Encaje y límite de servicio

- El fallo es de **lectura**: el PDF está bien orientado (el `/Rotate` lo deja
  derecho en cualquier visor) y OpenAI no aplica ese `/Rotate` al leer el
  `input_file`. sv2 le hace el trabajo del visor: le manda la página derecha.
- **Solo sv2** (`services/partes-api`): es el único que llama a la IA. sv1 sigue
  guardando el PDF tal cual (el original que sv3 archiva y deduplica por
  sha256). sv3 lee `meta` con `.get` y guarda el envelope entero en
  `raw_extraction_json`: sin columna nueva ni ORM; sv4 y sv5 no lo ven.
- **Capa**: la decisión (convertir o no, qué hacer si falla, qué trazar) vive en
  `application/` (pipeline); la manipulación del PDF y la imagen (pypdf, Pillow)
  es un adaptador de `infrastructure/document/` detrás de un puerto de
  `domain/ports/`. Los clientes de proveedor no saben nada de la conversión:
  reciben un `LlmAttachment` de `kind="image"` como ya reciben las fotos.
- **No hay lógica copiada**: sv1 usa pypdf para trocear; sv2, para leer la
  estructura de una página. Fuera de la lista cerrada de duplicación.
- **F-058** (en su rama, no se toca): F-059 ataca la causa; F-058 queda como red
  de seguridad. Como la conversión va por proveedor (DA1), una relectura con
  Gemini seguiría con PDF, que es lo medido (6/6).

## 2. Ficheros a crear

| Ruta | Qué |
|---|---|
| `services/partes-api/domain/models/conversion_adjunto.py` | `ResultadoConversion` y constantes de motivo |
| `services/partes-api/domain/ports/conversor_pagina.py` | puerto `ConversorPaginaImagen` |
| `services/partes-api/infrastructure/document/pagina_pdf_imagen.py` | adaptador `PaginaPdfImagenConversor` (pypdf + Pillow) |
| `services/partes-api/tests/f059_pdf_sinteticos.py` | fábrica de PDF sintéticos para los tests (Pillow + pypdf, sin datos reales) |
| `services/partes-api/tests/test_f059_conversor.py` | R1–R10 |
| `services/partes-api/tests/test_f059_pipeline.py` | R11–R19 |
| `services/partes-api/tests/test_f059_config.py` | R20–R22, R24 |

`infrastructure/document/` es carpeta nueva; sin `__init__.py`, como
`infrastructure/llm/` (paquete de espacio de nombres).

## 3. Ficheros a modificar

| Ruta | Cambio |
|---|---|
| `services/partes-api/application/pipelines/extract_parte_pipeline.py` | kwargs nuevos `conversor` y `proveedores_imagen`; paso `_preparar_para_ia`; `meta.adjunto_ia` |
| `services/partes-api/config/settings.py` | `PAGINA_COMO_IMAGEN`, `PAGINA_COMO_IMAGEN_PROVEEDORES` (+ propiedad lista y validación), `OPENAI_IMAGE_DETAIL` |
| `services/partes-api/interface_adapters/api/app.py` | instancia el conversor y lo pasa al pipeline; `image_detail` al cliente OpenAI; log de wiring |
| `services/partes-api/infrastructure/llm/openai_responses_client.py` | parámetro `image_detail` y `detail` en `input_image` |
| `infra/manifests/sv2/requirements.txt` | `pypdf>=4.2` (mismo suelo que sv1) y `Pillow>=10.0` |
| `docs/ARCHITECTURE.md` | semántica 19 (página como imagen, sv2) |
| `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` | fila de sv2: lo que manda a la IA, variables nuevas, dependencias |

El `Dockerfile` no cambia (`python:3.12-slim` instala ambos por rueda; Pillow
trae libjpeg). El `.venv` de la raíz, que `init.sh` usa para todos los
servicios, tiene pypdf 6.19 y **no tiene Pillow**: lo instala T1.

## 4. Ficheros que NO se tocan

- `services/partes-email/**` (sv1 y su `pdf_page_splitter.py`).
- `services/partes-api/infrastructure/llm/gemini_genai_client.py` y
  `claude_messages_client.py`: ya mandan `kind="image"` por su vía de imagen.
- `services/partes-api/config/prompts.yaml`, `domain/models/parte_models.py`,
  `domain/models/llm_attachment.py`, `application/services/parte_extraction_service.py`
  (su `_attachment_debug` ya describe el adjunto que recibe: R18 sale gratis).
- `services/partes-api/main_worker.py` (pasa por el pipeline).
- sv3, sv4, sv5, ORM, colas, `infra/*.ps1`, la rama de F-058.

## 4 bis. Clases y funciones

```python
# domain/models/conversion_adjunto.py  (domain, sin dependencias)
CONVERTIDA, NO_APLICA, ERROR, APAGADA = "convertida", "no_aplica", "error", "apagada"
@dataclass(frozen=True)
class ResultadoConversion:
    adjunto: LlmAttachment | None   # None si no aplica
    motivo: str                     # "" si convertida; motivo cerrado de R6–R10
    giro_grados: int | None = None
    ancho_px: int | None = None
    alto_px: int | None = None

# domain/ports/conversor_pagina.py
class ConversorPaginaImagen(ABC):
    @abstractmethod
    def convertir(self, adjunto: LlmAttachment) -> ResultadoConversion:
        """Página escaneada -> imagen derecha. «No aplica» se devuelve; un
        fallo se lanza (lo recoge el pipeline)."""

# infrastructure/document/pagina_pdf_imagen.py
class PaginaPdfImagenConversor(ConversorPaginaImagen):
    def __init__(self, *, calidad_jpeg: int = 90) -> None: ...
    def convertir(self, adjunto: LlmAttachment) -> ResultadoConversion: ...

# application/pipelines/extract_parte_pipeline.py
ExtractPartePipeline.__init__(..., conversor: ConversorPaginaImagen | None = None,
                              proveedores_imagen: frozenset[str] = frozenset())
def _preparar_para_ia(self, original: LlmAttachment, sha256: str
                      ) -> tuple[LlmAttachment, dict[str, Any]]:
    """Devuelve (adjunto a enviar, meta.adjunto_ia)."""
```

Los defaults dejan intactos los constructores actuales (sin conversor =
`apagada`). Activa = `conversor is not None and self._provider in
proveedores_imagen`; con `PAGINA_COMO_IMAGEN=false`, `app.py` pasa `frozenset()`.

## 5. Algoritmo del conversor (DA2 = A)

Sobre `PdfReader(BytesIO(adjunto.data))`, en este orden (el primer fallo da el
motivo):

1. `len(pages) != 1` ⇒ `varias_paginas`.
2. Operaciones de `ContentStream(page.get_contents(), reader)`: exactamente
   `q`, `cm [a b c d e f]`, `Do /Nombre`, `Q` ⇒ si no, `contenido_no_es_una_imagen`.
   (Así quedan fuera texto, vectores y varias imágenes.)
3. El XObject `/Nombre` es `/Subtype /Image`; `/Filter` es `/DCTDecode` (nombre
   o lista de uno), `/BitsPerComponent 8`, sin `/Decode`, `/SMask` ni `/Mask`
   ⇒ si no, `imagen_no_jpeg`; `/ColorSpace` `/DeviceRGB` o `/DeviceGray` ⇒ si no,
   `color_no_soportado` (CMYK de Adobe invierte colores; no se arriesga).
4. `b == c == 0`, `|a − ancho_mediabox| ≤ 1`, `|d − alto_mediabox| ≤ 1`, `e`,`f`
   en el origen de la MediaBox (±1), CropBox = MediaBox, y
   `|(W/H) / (a/d) − 1| ≤ 0,02` con W×H los píxeles ⇒ si no, `imagen_no_cubre_pagina`.
5. `rot = page.get("/Rotate", 0)`; si no es múltiplo de 90 ⇒ `giro_no_valido`;
   `rot %= 360`.
6. `xobj.get_data()` (pypdf no decodifica `DCTDecode`: devuelve el JPEG
   íntegro, comprobado con pypdf 6.19 en el banco) ⇒ `Image.open` ⇒ girar
   **horario** `rot` grados: `img.rotate(-rot, expand=True)`, como `jpeg_derecho`
   del banco (Pillow gira antihorario con ángulo positivo; `transpose` vale).
7. `img.convert("RGB").save(out, "JPEG", quality=calidad_jpeg)` sin `exif` ⇒
   `LlmAttachment(kind="image", filename=<stem>.jpg, mime_type="image/jpeg")`.

Las excepciones de pypdf o Pillow (PDF roto, JPEG truncado,
`DecompressionBombError`) no se capturan aquí: suben al pipeline (R13).
Banco: los 22 PDF cumplen 1–5 (`q 841.680 0 0 595.200 0 0 cm /Im0 Do Q`,
DeviceRGB, sin CropBox propia); el JPEG sale de 0,65–1,1 MB (originales
0,35–0,44 MB), bajo los 5 MB por imagen de Claude; recodificar 8,7 Mpx cuesta
menos de un segundo frente a decenas de la llamada.

## 6. Pipeline, traza y logs

`run`: `original = _build_attachment_validated(...)` (MAX_FILE_MB sobre el
original, como hoy) → `sha256` del original → `enviado, traza =
_preparar_para_ia(original, sha256)` → `service.extract(attachment=enviado)` →
`_envelope(..., attachment=original, adjunto_ia=traza)`.

| Caso | `conversion` | `motivo` | Log |
|---|---|---|---|
| conversión no activa | `apagada` | `interruptor` o `proveedor_fuera_de_lista` | — |
| `kind="image"` de entrada | `no_aplica` | `no_es_pdf` | — |
| conversor «no aplica» | `no_aplica` | el de R6–R10 | INFO |
| conversor lanza | `error` | `type(exc).__name__` | WARNING |
| convertida | `convertida` | `""` | INFO con giro, ancho, alto, bytes |

WARNING de ejemplo: `[partes-sv2][imagen] conversión fallida (ValueError) en
sha256=1a2b3c4d5e6f: se manda el PDF`. Ni el nombre del fichero (puede llevar el
del adjunto del correo) ni nada del contenido.

`meta.adjunto_ia` = `{conversion, motivo, kind, mime_type, size_bytes}` del
adjunto enviado, más `giro_grados`, `ancho_px`, `alto_px` si `convertida`.
`meta.source_*` siguen saliendo de `original` (R16). `debug` no cambia de forma:
`_attachment_debug` ya recibe el adjunto enviado.

## 7. Decisiones abiertas (las valida el humano)

**DA1 · A qué proveedores se aplica.** A) solo OpenAI por defecto, lista
configurable (`PAGINA_COMO_IMAGEN_PROVEEDORES=openai`); B) todos; C) OpenAI y
Claude. **Recomendada A**: producción usa OpenAI y ahí se midieron el fallo y la
cura; Gemini ya lee bien estas páginas con PDF (6/6) y F-058 cuenta con él tal
cual; Claude no está en producción ni se midió. Ampliar es una variable de entorno.

**DA2 · Cómo se convierte.** A) imagen incrustada girada (Pillow + pypdf), solo
para la página escaneada de §5; el resto va como PDF, como hoy. B) renderizar
cualquier PDF (p. ej. pypdfium2, binario nativo) a ~300 ppp. C) A y, si no
aplica, B. **Recomendada A**: es lo medido, cubre las 22 páginas reales (lo que
entra hoy por el escáner), no remuestrea y no trae una biblioteca nativa. B y C
cubrirían PDF con texto o vectoriales que hoy no llegan ni se han medido; si
aparecen, el INFO `no_aplica` los cuenta en Log Analytics y se abre feature con
datos. Varias páginas no llegan por el buzón (sv1 trocea); por HTTP van como PDF.

**DA3 · Interruptor.** A) `PAGINA_COMO_IMAGEN` encendido por defecto en el
código: desplegar sv2 basta, sin tocar el entorno de Azure; volver atrás es
`az containerapp update -n ca-sv2-extraccion -g rg-partes-dev --set-env-vars
PAGINA_COMO_IMAGEN=false`. B) apagado por defecto y el humano lo enciende con
ese comando y `true` tras desplegar. **Recomendada A**: es la petición («pon la
primera arreglar esto»), M1–M3 se miden antes de desplegar y el fallo de
conversión ya cae al PDF.

**DA4 · `detail` de OpenAI.** A) `OPENAI_IMAGE_DETAIL=high` para toda imagen
(también las fotos del móvil, que hoy van con el `auto` implícito); B) `high`
solo para las páginas convertidas (otro campo en `LlmAttachment`). **Recomendada
A**: lo medido es `high`; un parte es letra manuscrita pequeña, donde `auto`
puede bajar resolución; y no obliga a tocar el modelo de dominio. Vacío lo apaga.

## 8. Tests (sin red, sin IA, sin BBDD)

`f059_pdf_sinteticos.py` fabrica los PDF en memoria: una «página derecha»
sintética (p. ej. 300 × 200 blanca con un cuadrado negro arriba a la izquierda),
guardada **girada antihoraria `rot`** (`derecha.rotate(rot, expand=True)`) como
PDF con Pillow (`save(..., "PDF")`: un único JPEG `DCTDecode` a página
completa, contenido `q w 0 0 h 0 0 cm /image Do Q`) y con `/Rotate rot` puesto
con pypdf. Así el visor la mostraría derecha y el conversor debe devolverla
derecha. Variantes: 2 páginas (`save_all`), CMYK, imagen no JPEG (modo `P`),
operador de texto añadido al contenido, `cm` a media página, `cm` con giro,
`/Rotate 45`, `/Rotate -90`, bytes de JPEG truncados, bytes que no son PDF.

| Fichero | Casos |
|---|---|
| `test_f059_conversor.py` | `test_f059_r1_…` a `r10_…`: para 0/90/180/270 la marca queda arriba a la izquierda (media de grises del cuadrante < umbral) y las medidas (R3, R4); −90 ⇒ 270 (R2); JPEG sin EXIF y modo RGB (R5); cada «no aplica» con su motivo exacto (R6–R10); JPEG truncado y no-PDF lanzan |
| `test_f059_pipeline.py` | cliente LLM falso que captura el adjunto; conversor falso. Activa ⇒ imagen al cliente (R11); no aplica ⇒ mismos bytes del PDF e INFO (R12, `caplog`); conversor que lanza ⇒ PDF, WARNING con tipo y sha12, sin el `filename` en el texto (R13); apagada por interruptor y por proveedor ⇒ conversor no llamado (R14); foto ⇒ conversor no llamado (R15); `meta.source_*` del original (R16); `meta.adjunto_ia` completo por caso (R17); `debug` con el sha256 de la imagen (R18); INFO de convertida (R19). Uno de extremo a extremo con el conversor real y un PDF sintético `/Rotate 270` |
| `test_f059_config.py` | defectos y lista (R20); nombre desconocido ⇒ `ValueError` que lo nombra, vacío ⇒ ninguno (R21); `_build_input` de OpenAI con imagen lleva `detail` y sin valor no, el PDF nunca (R22); `requirements.txt` de sv2 declara `pypdf` y `Pillow` (R24) |

R23 lo vigilan los tests de F-023 y F-051 sin cambios. Fase RED: cada test se ve
fallar antes de su implementación (traza en `progress/impl_F-059.md`).

## 9. Verificación manual (banco del líder, fuera del repo)

Banco: `…\scratchpad\bench` (`bateria.py`, `lanzar.ps1` con las claves del Key
Vault solo en ese proceso, `-Repo` apuntando a `partes-wt-f059`). El líder añade
un modo que convierte con `PaginaPdfImagenConversor` de la rama (en vez de
`jpeg_derecho`) y crea el cliente OpenAI con `image_detail="high"`. Sin
escrituras en ningún sistema.

- **M0** (sin IA): los 22 PDF ⇒ `convertida`; píxeles iguales a `jpeg_derecho`.
- **M1**: `paginas_sincab`, 2 pasadas, gpt-6.1-sol ⇒ obra y fecha 12/12, las de
  `sincab_gemini.jsonl`. **M2**: `paginas_control`, 2 pasadas ⇒ 4/4 como en PDF.
- **M3**: `paginas` (14) × 3 en imagen y en PDF, `corregir.py` contra
  `verdad.json` ⇒ aciertos por fila ≥ PDF y ninguna cabecera vacía nueva.
- **M4** (humano, tras desplegar): SELECT de solo lectura en la base `partes` sobre
  `raw_extraction_json` de las ingestas nuevas ⇒ `adjunto_ia.conversion = convertida`.

Resultados (tablas sin nombres ni DNIs) en `progress/banco_F-059.md`. Si M1–M3
no se cumplen, la feature queda `blocked` y se vuelve a proponer.

## 10. Riesgos y alternativas descartadas

- **La causa es inferida** (OpenAI no aplicaría el `/Rotate`); la cura está medida.
- **Subir el razonamiento** (`effort=high`): medido, 0/12. Descartado.
- **Convertir en sv1**: cambia el original archivado y el sha256. Descartado.
- **Regex sobre los bytes del PDF** (como el banco): frágil con objetos
  comprimidos o `/Rotate` en otro objeto; se usa pypdf.
- **EXIF**: PDF y visores lo ignoran, algunos proveedores no; al recodificar sin
  `exif` no viaja. Las fotos del móvil no pasan por aquí.
- **Variación del modelo**: M3 lo cubre con 3 pasadas; F-054 manda a revisión
  cualquier parte que aún llegue sin obra o sin fecha, y F-058 queda detrás.

## 11. Despliegue y rigor

Rigor `estandar`: fase RED, cobertura ≥ 80 % de líneas cambiadas, mutación
muestreada (20, semilla de `rigor.json`) sobre `pagina_pdf_imagen.py` y
`extract_parte_pipeline.py`, supervivientes analizados. Despliegue (lo pide y lo
lanza el humano): `redeploy_partes.ps1 -Solo sv2`. Con DA3 = A no hay cambio de
entorno en Azure; con DA3 = B, el `az containerapp update` de §7 tras desplegar.
