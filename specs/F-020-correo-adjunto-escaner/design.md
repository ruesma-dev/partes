<!-- specs/F-020-correo-adjunto-escaner/design.md -->
# F-020 · sv1: correos adjuntos encadenados hasta el PDF — Diseño

## 1. Límite de servicio

**Solo sv1** (`services/partes-email`). Abrir un correo adjunto es parte de
la *captura* (sv1 = «del buzón a `q-extraccion`», `docs/ARCHITECTURE.md`):
no pertenece a sv2 (extracción IA de un PDF ya aislado) ni a sv3. Ninguna
lógica se duplica entre servicios. sv2/sv3/sv4 no cambian (§7). Sin SQL, sin
schema, sin variables de entorno nuevas, sin cambios en `infra/` ni en los
manifests: el despliegue es solo `redeploy_partes.ps1 -Solo sv1` (humano).

## 2. Ficheros a crear

| Ruta (bajo `services/partes-email/`) | Capa | Qué |
|---|---|---|
| `domain/ports/extractor_correo_adjunto.py` | domain | Puerto `ExtractorCorreoAdjunto` (Protocol) + excepción `CorreoAdjuntoIlegible` |
| `infrastructure/document/mime_pdf_extractor.py` | infrastructure | `MimePdfExtractor`: recorrido MIME recursivo con la stdlib `email` |
| `tests/` (`conftest.py`, `eml_sinteticos.py`, `dobles.py`, `test_f020_*.py`) | tests | Ver §8; `conftest.py` con el patrón de sv4 (raíz del servicio en `sys.path`) |

## 3. Ficheros a modificar

| Ruta | Cambio |
|---|---|
| `domain/models/email_models.py` | + dataclasses `CorreoEmbebido`, `PdfEmbebido`, `ExtraccionCorreoAdjunto` (§6.1) |
| `domain/ports/mailbox_client.py` | **Solo docstring** de `download_attachment_value`: para un correo adjunto devuelve el MIME RFC 822. Sin cambio de firma |
| `application/pipelines/polling_pipeline.py` | Clasificación de adjuntos, rama de correo adjunto, contexto con `embedded_in`, regla de destino R20 (§6.3). Docstring de cabecera actualizado |
| `main.py` | Construye `MimePdfExtractor()` y lo inyecta (R25) |
| `docs/ARCHITECTURE.md` | Subsección breve «Ingesta de sv1: correos adjuntos (F-020)» con la regla de §6.3 y el tope de 5 niveles |

`harness/servicios.json` **no cambia**: `sv1-email` ya está declarado; hoy
`init.sh` avisa «sin directorio de tests» y, en cuanto exista `tests/`, la
ejecuta con el intérprete de la raíz (R26).

## 4. Ficheros que NO se tocan

- `infrastructure/graph/mail_client.py`: la sonda probó que
  `download_attachment_value` y `list_attachments` (su `$select` ya trae
  `@odata.type`) sirven tal cual. Ni `$expand` ni llamadas nuevas.
- `infrastructure/document/pdf_page_splitter.py`: se reutiliza sin cambios.
- `infrastructure/queue/*`, `infrastructure/azure/*`, `config/settings.py`,
  `.env*`, `requirements.txt` (la stdlib `email` no es dependencia nueva).
- Cualquier fichero de `services/partes-api`, `partes-persistencia`,
  `partes-front`, `partes-transfer`, `infra/`. Si parece necesario: `blocked`.
- `docs/referencia/` (evita C3 bis) y `azure-apps/` (no cambia lo que sv1
  expone ni consume: mismo buzón, mismos permisos Graph, misma cola).

## 5. Contrato del contexto (forma exacta)

PDF que sale de un correo adjunto (nombres de clave existentes intactos;
solo cambian los VALORES de `attachment` y `document.source_attachment_*`, y
se añade `embedded_in`):

```jsonc
{
  "transport": {"document_id": "<uuid hex>", "source": "email-poller"},   // igual que hoy
  "email": { /* el correo RECIBIDO, igual que hoy: id, subject, sender, receivedDateTime, bodyPreview */ },
  "attachment": {
    "id": "<id Graph del correo adjunto de nivel 1>",
    "name": "<nombre del PDF interior, R11>",
    "contentType": "application/pdf",
    "size": <len(bytes del PDF interior)>,
    "sha256": "<sha256 del PDF interior completo>",
    "page_number": n, "page_count": N, "was_split": bool                 // igual que hoy
  },
  "document": {
    "filename": "<nombre de página que da el splitter>", "mime_type": "application/pdf",
    "sha256": "<sha256 de la página>", "page_number": n, "page_count": N, "was_split": bool,
    "source_attachment_filename": "<= attachment.name>",
    "source_attachment_mime_type": "application/pdf",
    "source_attachment_sha256": "<= attachment.sha256>"
  },
  "embedded_in": [                                   // clave NUEVA, de primer nivel
    {"level": 1, "attachment_name": "<name Graph del adjunto>",
     "subject": "<Subject|null>", "sender": "<dirección de From|null>", "date": "<Date tal cual|null>"},
    {"level": 2, "attachment_name": "<filename de la parte message/rfc822|null>",
     "subject": "...", "sender": "...", "date": "..."}
  ]
}
```

`embedded_in` va del exterior al interior (≥ 1 elemento, `level` consecutivo
desde 1; el último contiene el PDF). `sender` = dirección de
`email.utils.parseaddr(From)` o `null`; `date` = cabecera `Date` sin
normalizar; los tres truncados a 200 (R12). **PDF directo**: sin
`embedded_in` y el resto idéntico a hoy (R18).

## 6. Clases y funciones

### 6.1 Dominio (`domain/models/email_models.py`)

Tres `@dataclass(frozen=True)`, sin dependencias:

- `CorreoEmbebido(level: int, attachment_name: Optional[str], subject:
  Optional[str], sender: Optional[str], date: Optional[str])` con
  `to_context() -> dict` que devuelve exactamente las 5 claves de §5.
- `PdfEmbebido(filename: str, file_bytes: bytes, cadena: tuple[CorreoEmbebido, ...])`
  — nombre de R11, bytes decodificados, cadena del nivel 1 al contenedor.
- `ExtraccionCorreoAdjunto(pdfs: tuple[PdfEmbebido, ...], tope_excedido: bool,
  partes_ignoradas: int)` — PDF en el orden de R7; el recuento es para el log.

### 6.2 Puerto e implementación

`domain/ports/extractor_correo_adjunto.py`:

```python
class CorreoAdjuntoIlegible(Exception): ...

class ExtractorCorreoAdjunto(Protocol):
    def extraer(self, *, raw_mime: bytes, nombre_adjunto: str | None) -> ExtraccionCorreoAdjunto:
        """Recorre el mensaje RFC 822 (nivel 1). Lanza CorreoAdjuntoIlegible si
        los bytes no se pueden interpretar como mensaje."""
```

`infrastructure/document/mime_pdf_extractor.py`:

- `NIVEL_MAXIMO_ANIDAMIENTO = 5` y `MimePdfExtractor(nivel_maximo: int = NIVEL_MAXIMO_ANIDAMIENTO)`.
- `extraer(...)`: `email.message_from_bytes(raw_mime, policy=email.policy.default)`;
  bytes vacíos o una excepción del parser ⇒ `CorreoAdjuntoIlegible`.
- `_recorrer(parte, nivel, cadena, acumulador)` — recursión **propia**, no
  `Message.walk()` (que baja a los `message/rfc822` sin decir el nivel):
  - `message/rfc822`: `get_payload()` → primer mensaje; si `nivel + 1 >
    nivel_maximo` ⇒ `tope_excedido = True` y no se baja; si no, se baja con
    la cadena ampliada con `_cabeceras(sub, nivel + 1, parte.get_filename())`.
  - `multipart/*`: cada subparte en orden, mismo nivel.
  - PDF (R8): `get_payload(decode=True)`; vacío ⇒ ignorado. Nombre por
    `_nombre_pdf(parte, n)` = `PurePath(filename.replace("\\", "/")).name`
    o `documento_<n>.pdf` (R11).
  - Resto ⇒ `partes_ignoradas += 1`.
- `_cabeceras(msg, nivel, nombre) -> CorreoEmbebido`: cada cabecera en su
  `try/except` (R12), `str(...)[:200]`.
- Sin logging de contenido, sin red, sin disco (R13, R24).

### 6.3 Pipeline (`application/pipelines/polling_pipeline.py`)

- Constructor: `+ extractor_correo: ExtractorCorreoAdjunto` (keyword,
  obligatorio). El tipo se importa del **puerto**, no de infraestructura.
- Constantes: `_ODATA_REFERENCE = "#microsoft.graph.referenceAttachment"`,
  `_CONTENT_TYPE_CORREO = "message/rfc822"`. `_NON_FILE_ODATA_TYPES` y
  `_is_eligible` se conservan para los ficheros.
- `@staticmethod _es_correo_adjunto(att, max_bytes) -> bool`: R1, R2, R4
  (el descarte de R3 lo sigue haciendo `_is_eligible`).
- `_process_message`: recorre `attachments` **una vez, en orden**; cada uno
  se clasifica primero como correo adjunto y, si no, como fichero. Lista
  vacía ⇒ `Errores` con log de R23. Cada adjunto devuelve un
  `_ResultadoAdjunto(ok: bool, documentos: int)` (NamedTuple privado).
  Destino: `Procesados` sii `all(ok) and sum(documentos) >= 1` (R20).
- `_process_attachment` (fichero): descarga como hoy y delega en
  `_ingerir_pdf(...)`; devuelve `_ResultadoAdjunto`.
- `_process_correo_adjunto(msg, attachment, mailbox, max_attachment_bytes)`:
  descarga (fallo ⇒ `(False, 0)`, R22) → `extraer` (`CorreoAdjuntoIlegible`
  ⇒ `(False, 0)`) → `tope_excedido` ⇒ log ERROR y `(False, 0)` (R10) →
  filtra PDF > límite (R15) → sin PDF ⇒ WARNING y `(True, 0)` (R21) → cada
  PDF por `_ingerir_pdf(..., embedded_in=[c.to_context() for c in pdf.cadena])`.
- `_ingerir_pdf(*, msg, attachment, nombre, content_type, size, file_bytes,
  embedded_in: list[dict] | None) -> _ResultadoAdjunto`: el cuerpo actual de
  `_process_attachment` desde el sha256 (troceo + `_ingest_page` por página).
  `documentos` = páginas ingeridas bien; `ok` = todas bien.
- `_build_context(...)` recibe `nombre`, `content_type`, `size` y
  `embedded_in`; con `embedded_in=None` produce **exactamente** el dict de
  hoy (R18); si no, añade la clave (R17).

### 6.4 Cableado (`main.py`)

`PollingPipeline(mailbox=…, sink=…, pdf_splitter=PdfPageSplitter(),
extractor_correo=MimePdfExtractor())`.

## 7. Impacto en sv2 y sv3 (verificado leyendo el código, 2026-09-30)

- **sv2** `main_worker.py`: usa `document_id`/`filename`/`mime_type` del
  mensaje y reenvía `context` **opaco** a `q-persistencia`. Sin efecto.
- **sv3** `persist_parte_pipeline.py`: `document.sha256` (dedup) y
  `email.subject/bodyPreview/body` (el correo recibido, que no cambia).
  `sqlalchemy_parte_repository.py`: `email.*`, `document.*`,
  `attachment.name` → `source_attachment_filename` (String 255, ahora el
  PDF interior: lo que se quiere), `attachment.sha256` (String 64) y el
  contexto entero en `raw_context_json` (Text): `embedded_in` solo acaba ahí.
  El archivo en SharePoint usa `request.filename`. Sin efecto.
- **sv4**: no lee `source_attachment_filename` ni `raw_context_json`.

**Conclusión: no hay que tocar sv2 ni sv3.** La dedup de sv3 por
`document.sha256` hace inocuo reprocesar a mano un correo ya ingerido.

## 8. Tests (sin red, sin BBDD; `.eml` construidos en el propio test)

- `eml_sinteticos.py`: `pdf_bytes(paginas: int)` con `pypdf.PdfWriter` y
  páginas en blanco; `correo(subject, sender, adjuntos)` con
  `email.message.EmailMessage` y `add_attachment` (PDF, imagen, texto);
  `envolver(interior, niveles)` anida con `add_attachment(<EmailMessage>)`
  (produce `message/rfc822`). Direcciones `@example.com`; ningún dato real.
- `dobles.py`: `BuzonFalso(MailboxClient)` con adjuntos y `$value` por id,
  fallo de descarga configurable y **registro de llamadas** (R6);
  `SumideroFalso` guarda `(document_id, filename, mime_type, context)` y
  puede fallar a la N-ésima llamada.
- Pipeline con `PdfPageSplitter` **real** (troceo verdadero) y
  `MimePdfExtractor` real.

| Fichero | Requisitos |
|---|---|
| `test_f020_extractor_mime.py` | R7, R8, R9, R10 (niveles 5 y 6), R11, R12, R13 (imports por `ast`) |
| `test_f020_clasificacion_adjuntos.py` | R1, R2, R3, R4, R5 |
| `test_f020_pipeline_correo_adjunto.py` | R6, R14, R15, R16, R17, R19, R20, R21, R22, R23, R24 (`caplog`) |
| `test_f020_contexto_pdf_directo.py` | R18: dict literal esperado del formato actual |
| `test_f020_wiring_main.py` | R25: `main.main()` con `Settings`, colas, blob y `PollingPipeline` sustituidos por dobles |

R26 se verifica con la salida de `bash harness/init.sh` («servicio sv1-email
… pytest en verde»). Fase RED obligatoria con traza para R1, R10, R17 y R20.

## 9. Riesgos y decisiones

- **DA1 · `$value` y no `$expand`**: `$expand=…/item` devuelve el mensaje en
  JSON y los adjuntos interiores exigen más llamadas; `$value` da todo el
  MIME en un GET (sonda). El `Content-Type` HTTP de esa respuesta es
  `text/plain`: se ignora.
- **DA2 · Extractor en `infrastructure/document/` tras un puerto**: interpretar
  un formato es adaptación (igual que el splitter). El pipeline depende del
  Protocol; así los tests pueden sustituirlo.
- **DA3 · Tope como constante (5), no variable de entorno**: evita tocar
  manifests e infra; cambiarlo es cambiar código y pasar por spec.
- **DA4 · `.msg` (Outlook binario) y `winmail.dat` (TNEF)** siguen fuera:
  no son `message/rfc822` y se descartan como hoy.
- **Riesgos**: `source_attachment_filename` es String(255) en sv3 (un nombre
  interior más largo fallaría su INSERT; mismo riesgo que hoy con un PDF
  directo, no se mitiga aquí). `embedded_in` añade ≤ 5 × ~650 bytes al
  mensaje de cola (R12 trunca), lejos de 64 KB. **`pypdf` no está en el
  `.venv` de la raíz** y `polling_pipeline.py` lo importa vía splitter: sin
  él la suite de sv1 no importa (D1).

Decisiones abiertas para el humano (también en `progress/current.md`):

- **D1** · Instalar la dependencia ya declarada de sv1 en el venv del arnés:
  `.venv/Scripts/python.exe -m pip install "pypdf>=4.2"`. Cambia el entorno
  local, no el repositorio.
- **D2** · Correo adjunto sin PDF junto a otros documentos ingeridos ⇒
  `Procesados` con WARNING (lectura de la decisión (2) a nivel de correo
  recibido). Alternativa: `Errores` siempre que un correo adjunto no traiga PDF.
- **D3** · Tope excedido ⇒ no se ingiere **nada** de ese correo adjunto
  (todo o nada). Alternativa: ingerir lo hallado hasta el nivel 5 y mandar
  igualmente a `Errores` (riesgo: reproceso manual parcial).
- **D4** · Un `.eml` adjuntado como **fichero** (`fileAttachment` con
  `message/rfc822`) también se abre: mismo formato, coste cero. Alternativa:
  solo `itemAttachment`.

## 10. Verificación manual (humano, tras desplegar)

Hay cuatro correos del escáner sin leer en `Errores` (sonda). Tras
`redeploy_partes.ps1 -Solo sv1`: mover **uno** a la carpeta origen, marcarlo
como no leído y comprobar en los logs de `ca-sv1-poller` la línea de
ingesta del PDF interior, el movimiento a `Procesados` y el parte en el
portal. Reprocesar los otros tres es manual y fuera de F-020.
