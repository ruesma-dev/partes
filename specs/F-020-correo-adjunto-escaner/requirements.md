<!-- specs/F-020-correo-adjunto-escaner/requirements.md -->
# F-020 · sv1: correos adjuntos (message/rfc822) encadenados hasta el PDF — Requisitos

> **Origen**: petición del humano del 2026-09-30. El escáner envía cada parte
> como un **correo adjunto** (`itemAttachment`, `contentType` `message/rfc822`)
> que contiene el PDF; hoy sv1 lo descarta y el correo acaba en `Errores` por
> «sin adjuntos elegibles». Decisiones (1)–(6) de `harness/features.json`
> **confirmadas**: no se reabren aquí.
>
> **Sonda previa HECHA** (`progress/explore_F-020_sonda.md`): `GET …/$value`
> sobre el itemAttachment devuelve el MIME RFC 822 completo con el PDF dentro.
> El método actual `download_attachment_value` sirve tal cual.
>
> **Servicio afectado: SOLO sv1** (`services/partes-email`). sv2 y sv3 no
> cambian (comprobado en `design.md` §7). Desplegar lo lanza el humano.

## Glosario

- **PDF directo**: adjunto de fichero del correo recibido, elegible como hoy.
- **Correo adjunto**: adjunto del correo recibido cuyo MIME es un mensaje RFC 822.
- **Nivel**: el correo adjunto descargado de Graph es el nivel 1; un mensaje
  `message/rfc822` dentro de un nivel N es el nivel N+1.
- **Cadena**: lista de correos atravesados desde el nivel 1 hasta el que
  contiene directamente el PDF.
- **Documento lógico**: una página de PDF ingerida (Blob + `q-extraccion`).

## Qué adjuntos se abren y cuáles no

R1. El sistema debe tratar como correo adjunto todo adjunto **no inline** cuyo
`contentType` sea `message/rfc822` (sin distinguir mayúsculas), tanto si su
`@odata.type` es `itemAttachment` como `fileAttachment` o viene ausente.

R2. SI un adjunto es `#microsoft.graph.referenceAttachment`, ENTONCES el
sistema debe descartarlo con log INFO, sea cual sea su `contentType`.

R3. SI un `itemAttachment` tiene un `contentType` distinto de
`message/rfc822` (cita de calendario, contacto, tarea…), ENTONCES el sistema
debe descartarlo con log INFO, como hoy.

R4. SI el `size` de Graph de un correo adjunto supera `MAX_ATTACHMENT_MB`,
ENTONCES el sistema debe descartarlo con log WARNING (misma regla que un PDF
directo).

R5. El sistema debe aplicar las reglas R1–R4 **sea cual sea el remitente**:
no hay filtro por remitente ni por asunto.

## Extracción del interior (recursiva)

R6. CUANDO un correo adjunto es elegible, el sistema debe descargarlo con
`download_attachment_value` e interpretar los bytes como un mensaje RFC 822
de nivel 1, sin ninguna llamada a Graph adicional a las que ya hace hoy.

R7. El sistema debe recorrer el mensaje en profundidad y en orden de
aparición: una parte `multipart/*` se recorre parte a parte en el mismo
nivel; una parte `message/rfc822` se abre como mensaje del nivel siguiente.

R8. El sistema debe considerar PDF toda parte no multipart cuyo tipo sea
`application/pdf` o cuyo nombre de fichero acabe en `.pdf` (sin distinguir
mayúsculas), y tomar sus bytes **decodificados** (base64 o quoted-printable).

R9. El sistema debe ignorar cualquier otra parte del interior (imágenes,
texto, HTML, otros ficheros) y una parte PDF sin bytes, con log DEBUG; las
imágenes interiores NO se ingieren.

R10. SI abrir una parte `message/rfc822` llevaría a un nivel mayor que **5**,
ENTONCES el sistema debe marcar ese correo adjunto como «tope excedido»,
**no ingerir ninguno** de sus PDF (tampoco los hallados en niveles ≤ 5),
registrar un log ERROR con el id del mensaje, el del adjunto y el tope, y el
correo recibido debe ir a `Errores`.

R11. El nombre de un PDF interior debe ser el **nombre base** (sin
directorios) del nombre de fichero MIME; SI la parte no trae nombre,
ENTONCES debe ser `documento_<n>.pdf`, con `n` el orden 1-based del PDF
dentro de su correo adjunto.

R12. Las cabeceras `Subject`, `From` y `Date` de cada correo de la cadena
deben leerse de forma defensiva: una cabecera ausente o ilegible da `null`
en su campo, nunca una excepción; y cada valor debe truncarse a **200**
caracteres (el contexto viaja en un mensaje de cola de tamaño limitado).

R13. La extracción del interior debe ser **pura**: sin red, sin disco y sin
más dependencias que la biblioteca estándar (`email`) y el dominio de sv1.

## Ingesta de lo encontrado

R14. CUANDO un correo adjunto contiene uno o varios PDF, el sistema debe
ingerir cada uno, en el orden de R7, por el camino de un PDF directo:
troceo por páginas (un documento lógico por página), sha256, Blob y
`q-extraccion`.

R15. SI un PDF interior supera `MAX_ATTACHMENT_MB`, ENTONCES el sistema debe
descartarlo con log WARNING, y no cuenta como PDF encontrado.

R16. El contexto de un documento lógico que sale de un correo adjunto debe
llevar, en `attachment` y en `document.source_attachment_*`, los datos del
**PDF interior** (nombre de R11, `application/pdf`, tamaño y sha256 de sus
bytes); `attachment.id` sigue siendo el id Graph del correo adjunto. Forma
exacta en `design.md` §5.

R17. El contexto de R16 debe llevar la clave nueva de primer nivel
`embedded_in`: la cadena del PDF, del nivel 1 al correo que lo contiene,
con la forma exacta de `design.md` §5.

R18. El contexto de un **PDF directo** NO debe llevar la clave `embedded_in`
y debe ser idéntico, clave a clave, al que genera sv1 antes de F-020.

## Destino del correo recibido

R19. Un correo con PDF directos y correos adjuntos debe procesarse entero en
la misma pasada, en el orden en que Graph lista los adjuntos.

R20. El correo recibido debe moverse a `Procesados` si y solo si (a) no ha
fallado ninguna descarga, extracción ni ingesta, (b) ningún correo adjunto
ha excedido el tope y (c) se ha ingerido al menos un documento lógico. En
cualquier otro caso debe moverse a `Errores`.

R21. SI un correo adjunto no contiene ningún PDF válido, ENTONCES el sistema
debe registrar un log WARNING con el id del mensaje y del adjunto. No cuenta
como fallo para R20(a): el correo recibido va a `Errores` solo si, por
R20(c), no se ha ingerido ningún documento en todo el correo (decisión
abierta D2, `design.md` §9).

R22. SI falla la descarga de un correo adjunto, o sus bytes no pueden
interpretarse como mensaje, ENTONCES el sistema debe registrar un log ERROR,
no ingerir nada de ese adjunto, seguir con los demás adjuntos y mover el
correo recibido a `Errores`.

R23. SI un correo no tiene ni PDF directos ni correos adjuntos elegibles,
ENTONCES el sistema debe moverlo a `Errores` como hoy, con un log que
nombre ambos casos.

R24. Ningún log debe contener bytes del PDF ni del MIME; solo ids, nombres,
tipos, tamaños, niveles y recuentos.

## Cableado y verificación

R25. `main.py` debe construir el extractor MIME e inyectarlo en
`PollingPipeline`; el pipeline no debe instanciarlo por su cuenta.

R26. sv1 debe tener su primera suite de tests en
`services/partes-email/tests/`, sin red ni BBDD, con los `.eml` construidos
dentro del propio test, y `bash harness/init.sh` debe ejecutarla como suite
del servicio `sv1-email` (ya declarado en `harness/servicios.json`).
