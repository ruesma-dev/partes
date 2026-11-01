<!-- specs/F-059-pagina-como-imagen-derecha/requirements.md -->
# F-059 · La IA no lee bien el PDF con /Rotate: sv2 le manda la página ya derecha — requisitos

> Pedida por el humano el 2026-10-23 («pon la primera arreglar esto»; petición
> literal en `harness/features.json`). **Solo sv2** (`services/partes-api`): es
> quien llama a la IA. Diseño en `design.md`; DA1–DA4 en su §7.

## Caso real que lo motiva

Es un problema de **lectura de la IA**, no del escáner ni de sv1. El humano:
«el parte viene cortado del escaner pero viene bien orientado y la obra se lee
perfectamente. el problema no es del giro, es de lectura».

Las 6 páginas guardadas sin obra ni fecha (escaneos del 21/10 y 23/10) son PDF
de una página que sv1 copia tal cual: MediaBox 841,68 × 595,2, `/Rotate 270` y
un JPEG 3507 × 2480 a página completa, guardado de lado; el `/Rotate` lo
endereza y **cualquier visor la enseña derecha**. Todo apunta a que OpenAI, con
el PDF como `input_file`, no aplica el `/Rotate` y lee la imagen cruda de lado.
Banco del líder (2026-10-23, fuera del repo, código real de sv2):

| Envío a gpt-6.1-sol (2 pasadas) | Cabecera de las 6 | Control (2 páginas) |
|---|---|---|
| PDF tal cual (`input_file`, hoy) | vacía 12/12 | bien |
| PDF + `reasoning.effort = high` | vacía 12/12 | — |
| JPEG incrustado girado según `/Rotate`, `detail: high` | obra y fecha bien 12/12 (= gemini-4-argon) | bien 4/4 |

Los 22 PDF del banco (6 + 2 de control + 14 de la batería de F-051) tienen esa
estructura. El corte del escáner deja dentro la obra y la fecha: no es lo que falla.

## Glosario

- **Página escaneada**: PDF de una página cuyo contenido es solo una imagen JPEG
  a página completa, sin giro en la matriz (`design.md` §5).
- **Imagen derecha**: esa imagen girada según el `/Rotate`, como la enseña un visor.
- **Conversión activa**: `PAGINA_COMO_IMAGEN = true` y `IA_PROVIDER` está en
  `PAGINA_COMO_IMAGEN_PROVEEDORES`.

## A. Conversión de la página (adaptador de sv2)

R1. CUANDO llega una página escaneada, el conversor debe devolver un adjunto
`kind = "image"`, `mime_type = "image/jpeg"`, con la imagen incrustada girada
en sentido horario los grados del `/Rotate` de la página.

R2. El conversor debe normalizar el `/Rotate` a 0, 90, 180 o 270 (módulo 360,
negativos incluidos: −90 ⇒ 270); con 0 no gira.

R3. La imagen derecha debe verse como el visor muestra la página: lo que en la
página mostrada queda arriba a la izquierda queda arriba a la izquierda en la
imagen, para `/Rotate` 0, 90, 180 y 270 (test con una marca, no solo medidas).

R4. Con `/Rotate` 90 o 270 el ancho y el alto deben intercambiarse respecto a la
imagen incrustada; con 0 o 180, mantenerse. Sin recorte ni reescalado.

R5. La imagen enviada debe ser JPEG en RGB, calidad 90, sin EXIF.

R6. SI el PDF tiene más de una página, ENTONCES «no aplica», motivo `varias_paginas`.

R7. SI el contenido de la página tiene algo más que `q`, un `cm`, un `Do` de una
imagen y `Q` (texto, dibujos, varias imágenes), ENTONCES «no aplica» con motivo
`contenido_no_es_una_imagen`.

R8. SI la imagen no es JPEG (filtro único `DCTDecode`, 8 bits) o su espacio de
color no es `DeviceRGB` ni `DeviceGray`, o lleva `/Decode`, `/SMask` o `/Mask`,
ENTONCES «no aplica» con motivo `imagen_no_jpeg` o `color_no_soportado`.

R9. SI la matriz `cm` gira o inclina (b o c ≠ 0), no cubre la MediaBox
(tolerancia 1 pt), la CropBox difiere de la MediaBox o la proporción en píxeles
difiere de la de la página más de un 2 %, ENTONCES «no aplica» con motivo
`imagen_no_cubre_pagina`.

R10. SI el `/Rotate` no es múltiplo de 90, ENTONCES «no aplica» con motivo
`giro_no_valido`.

## B. Envío a la IA (pipeline de sv2)

R11. DONDE la conversión está activa, CUANDO el conversor devuelve la imagen, el
pipeline debe pasar esa imagen al cliente del proveedor en lugar del PDF.

R12. CUANDO el conversor responde «no aplica», el pipeline debe mandar el PDF
original byte a byte y registrar un INFO con el motivo.

R13. SI la conversión lanza una excepción (PDF ilegible, JPEG corrupto, imagen
demasiado grande para Pillow…), ENTONCES el pipeline debe mandar el PDF
original byte a byte, emitir un WARNING con el tipo de excepción y los 12
primeros caracteres del sha256 del documento —sin nombre de fichero, nombres
ni DNIs— y la extracción debe seguir sin fallar por la conversión.

R14. MIENTRAS la conversión no está activa, el pipeline no debe llamar al
conversor y debe mandar el PDF como hoy.

R15. CUANDO llega una imagen (foto del móvil: jpg, png, webp), el pipeline debe
mandarla como hoy, sin llamar al conversor.

R16. El pipeline debe mantener `meta.source_filename`, `meta.source_mime_type`
y `meta.source_sha256` del documento recibido (sha256 de los bytes originales),
se convierta o no: la deduplicación de sv3 no cambia.

R17. El envelope debe añadir `meta.adjunto_ia` con `conversion` (`convertida`,
`no_aplica`, `error` o `apagada`), `motivo`, `kind`, `mime_type` y
`size_bytes` del adjunto enviado, y con `convertida` además `giro_grados`,
`ancho_px` y `alto_px`. Sin nombre de fichero.

R18. `debug.<proveedor>_request.attachment` debe describir el adjunto enviado
(con el `sha256` de la imagen si se convirtió).

R19. CUANDO se convierte, el pipeline debe registrar un INFO con giro, ancho,
alto y tamaño en bytes.

## C. Configuración y proveedor OpenAI

R20. El sistema debe leer `PAGINA_COMO_IMAGEN` (bool, defecto según DA3:
`true`) y `PAGINA_COMO_IMAGEN_PROVEEDORES` (CSV, defecto según DA1: `openai`).

R21. SI `PAGINA_COMO_IMAGEN_PROVEEDORES` contiene un nombre distinto de
`gemini`, `claude` u `openai`, ENTONCES el arranque debe fallar con un
`ValueError` que lo nombre. Vacío equivale a ningún proveedor.

R22. CUANDO el adjunto es imagen, el cliente OpenAI debe añadir a `input_image`
`"detail": OPENAI_IMAGE_DETAIL` (defecto `high`, DA4); con el valor vacío no
manda `detail`. El PDF sigue yendo como `input_file`, sin `detail`.

R23. Los clientes de Gemini y Claude, el prompt `parte_trabajo_es` y el esquema
`ParteTrabajo` no deben cambiar: los tests de F-023 y F-051 pasan sin tocarlos.

R24. `infra/manifests/sv2/requirements.txt` debe declarar `pypdf` y `Pillow`.

## D. Verificación manual (banco del líder, no versionado)

R25. M0: los 22 PDF del banco deben dar `convertida`, con la imagen igual en
píxeles a la de `jpeg_derecho` del banco.

R26. M1: las 6 páginas con la cabecera vacía, 2 pasadas con gpt-6.1-sol por el
código de la rama ⇒ obra y fecha 12/12, iguales a las de gemini-4-argon.

R27. M2: las 2 de control, 2 pasadas ⇒ 4/4 con la obra, fecha y filas del PDF.

R28. M3: la batería de F-051 (14 × 3, `verdad.json`, `corregir.py`) en modo
imagen ⇒ ni menos aciertos por fila ni más cabeceras vacías que en modo PDF.

R29. M4 (humano, tras desplegar sv2): las ingestas nuevas de páginas escaneadas
llevan `meta.adjunto_ia.conversion = "convertida"` (SELECT de solo lectura).

## Fuera de alcance

- El corte del escáner y sv1 (su troceo copia la página bien, con su `/Rotate`).
- Renderizar PDF que no son página escaneada: siguen yendo como PDF (DA2).
- EXIF de las fotos del móvil y F-026; `reasoning.effort`; `GEMINI_MEDIA_RESOLUTION`.
- F-058 (relectura con Gemini): queda como red de seguridad, en su rama.
