<!-- progress/explore_F-020_sonda.md -->
# F-020 · Sonda de solo lectura sobre Graph (2026-09-30)

**Veredicto: CONFIRMADO.** `GET /users/{buzón}/messages/{id}/attachments/{attId}/$value`
sobre un `itemAttachment` de tipo mensaje devuelve el **MIME completo (RFC 822)**
del correo adjunto, y dentro está el `application/pdf` en base64. La hipótesis
de la feature se sostiene: el cliente Graph actual de sv1
(`download_attachment_value`) ya sirve tal cual, sin llamadas nuevas.

## Cómo se hizo

- Script **fuera del repo** (scratchpad de la sesión), cargando la credencial
  a través de `config/settings.py` y `GraphTokenProvider` de sv1. No se abrió
  ni se imprimió el `.env`; ningún secreto ni id se ha escrito en ningún fichero.
- **Solo GET**: listar mensajes del remitente del escáner en todo el buzón,
  resolver el nombre de su carpeta, listar adjuntos y descargar `$value`.
  Nada movido, nada marcado como leído, nada modificado.
- Se registró **solo estructura** (árbol MIME, tipos, tamaños, extensión);
  ni contenido del PDF ni nombres de fichero ni datos personales.

## Lo observado

Cuatro correos del remitente del escáner, asunto `Attached Image`, **los
cuatro en la carpeta `Errores` y los cuatro sin leer** (recibidos el
2026-09-17 y tres el 2026-09-30). Los cuatro con la MISMA forma:

| Correo | Adjunto en Graph (`@odata.type` · `contentType` · `size`) | `$value` (HTTP · `Content-Type` de la respuesta · bytes) | Árbol MIME del `$value` | PDF interior (bytes · págs.≈) |
|---|---|---|---|---|
| 2026-09-30 08:49 | itemAttachment · message/rfc822 · 753 470 | 200 · `text/plain` · 1 006 611 | `multipart/mixed` → `application/pdf` (attachment, con nombre `.pdf`) | 712 457 · ≈8 |
| 2026-09-30 08:21 | itemAttachment · message/rfc822 · 117 874 | 200 · `text/plain` · 136 771 | ídem | 76 707 · 1 |
| 2026-09-30 08:16 | itemAttachment · message/rfc822 · 756 471 | 200 · `text/plain` · 1 010 674 | ídem | 715 355 · ≈8 |
| 2026-09-17 13:48 | itemAttachment · message/rfc822 · 131 884 | 200 · `text/plain` · 156 429 | ídem | 91 925 · 1 |

Árbol MIME exacto (idéntico en los cuatro), profundidad · content-type ·
extensión · disposición:

```
0  multipart/mixed      -     -           <- el propio correo adjunto (raíz del $value)
1    application/pdf    .pdf  attachment  <- el parte escaneado
```

Detalles que el diseño debe tener en cuenta:

1. **El `Content-Type` HTTP de la respuesta de `$value` es `text/plain`**, no
   `message/rfc822`: no sirve para decidir nada. Lo que identifica el correo
   adjunto es el `contentType` (`message/rfc822`) y el `@odata.type`
   (`#microsoft.graph.itemAttachment`) del **listado de adjuntos**.
2. El listado actual de sv1 (`$select=id,name,contentType,size,isInline`)
   **ya devuelve `@odata.type`**: no hace falta tocar la consulta.
3. La raíz del `$value` **es** el correo adjunto (nivel 1); no viene envuelta
   en otra parte `message/rfc822`. Un correo dentro de él aparecería como
   parte `message/rfc822` (nivel 2).
4. El correo interior del escáner **no tiene cuerpo de texto**: solo el PDF.
5. El `size` de Graph del itemAttachment (~753 KB) es menor que los bytes del
   `$value` (~1 MB, por el base64): el límite `MAX_ATTACHMENT_MB` sobre el
   `size` de Graph sigue siendo razonable (25 MB de margen de sobra).
6. El PDF viene **multipágina** en dos de los cuatro (≈8 páginas, recuento
   aproximado por patrón `/Type /Page`): el troceo existente por páginas es
   imprescindible también en este camino.
7. Los cuatro correos siguen **no leídos en `Errores`**: sv1 no los volverá a
   ver (solo sondea la carpeta origen). Reprocesarlos es manual y queda fuera
   de F-020 (moverlos a la carpeta origen tras desplegar).

## Qué NO se ha comprobado

- Anidamiento real de más de un nivel: ningún correo observado lo trae. Se
  cubre con `.eml` sintéticos en los tests de la feature.
- Cómo reporta Graph el `contentType` de un itemAttachment de **evento o
  contacto**: no hay ninguno en el buzón. El diseño no depende de ello (solo
  abre `message/rfc822`).
