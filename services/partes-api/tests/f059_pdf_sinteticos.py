# tests/f059_pdf_sinteticos.py
"""F-059 · Fábrica de PDF sintéticos para los tests del conversor.

Ningún dato real: una «página derecha» blanca de 300 × 200 píxeles con un
cuadrado negro arriba a la izquierda (la marca). Se guarda GIRADA
antihoraria ``rot`` grados y con ``/Rotate rot`` en la página, que es la
forma de las páginas que llegan del escáner: un visor la enseña derecha y el
conversor tiene que devolverla derecha.

Pillow escribe un único JPEG (``DCTDecode``) a página completa con el
contenido ``q w 0 0 h 0 0 cm /image Do Q``; pypdf retoca después lo que cada
variante necesita (giro, contenido, caja, flujo de la imagen).
"""
from __future__ import annotations

from io import BytesIO

from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    ContentStream,
    NameObject,
    NumberObject,
    RectangleObject,
)

#: Medidas de la página derecha (como la enseña el visor).
ANCHO_DERECHA = 300
ALTO_DERECHA = 200
#: Lado de la marca negra, arriba a la izquierda de la página derecha.
LADO_MARCA = 60


def pagina_derecha(modo: str = "RGB") -> Image.Image:
    """Página como la ve el visor: blanca con la marca arriba a la izquierda."""
    img = Image.new("RGB", (ANCHO_DERECHA, ALTO_DERECHA), (255, 255, 255))
    img.paste((0, 0, 0), (0, 0, LADO_MARCA, LADO_MARCA))
    return img if modo == "RGB" else img.convert(modo)


def _a_pdf(imagenes: list[Image.Image]) -> bytes:
    salida = BytesIO()
    primera, resto = imagenes[0], imagenes[1:]
    primera.save(salida, "PDF", save_all=bool(resto), append_images=resto)
    return salida.getvalue()


def _escritor(pdf: bytes) -> PdfWriter:
    return PdfWriter(clone_from=PdfReader(BytesIO(pdf)))


def _bytes(escritor: PdfWriter) -> bytes:
    salida = BytesIO()
    escritor.write(salida)
    return salida.getvalue()


def _imagen_xobject(escritor: PdfWriter):
    return escritor.pages[0]["/Resources"]["/XObject"]["/image"].get_object()


def pdf_escaneado(
    rot: int = 0,
    *,
    modo: str = "RGB",
    rotate_pdf: int | None = None,
    contenido: bytes | None = None,
    mediabox: tuple[float, float, float, float] | None = None,
    cropbox: tuple[float, float, float, float] | None = None,
    jpeg: bytes | None = None,
    imagen: Image.Image | None = None,
    entradas_imagen: dict | None = None,
    quitar_entradas_imagen: tuple[str, ...] = (),
) -> bytes:
    """PDF de una página escaneada guardada girada antihoraria ``rot`` grados.

    - ``rotate_pdf``: valor del ``/Rotate`` (por defecto, ``rot``).
    - ``contenido``: sustituye el flujo de contenido de la página.
    - ``mediabox`` / ``cropbox``: sustituyen las cajas de la página.
    - ``jpeg``: sustituye los bytes del flujo de la imagen.
    - ``imagen``: imagen guardada tal cual (sin girar) en lugar de la marca.
    - ``entradas_imagen`` / ``quitar_entradas_imagen``: retocan el
      diccionario de la imagen (``/Decode``, ``/SMask``, ``/Filter``...).
    """
    guardada = imagen if imagen is not None else (
        pagina_derecha(modo).rotate(rot, expand=True)
    )
    escritor = _escritor(_a_pdf([guardada]))
    pagina = escritor.pages[0]
    giro = rot if rotate_pdf is None else rotate_pdf
    if giro:
        pagina[NameObject("/Rotate")] = NumberObject(giro)
    if contenido is not None:
        flujo = ContentStream(None, escritor)
        flujo.set_data(contenido)
        pagina.replace_contents(flujo)
    if mediabox is not None:
        pagina.mediabox = RectangleObject(mediabox)
        if cropbox is None:
            pagina.cropbox = RectangleObject(mediabox)
    if cropbox is not None:
        pagina.cropbox = RectangleObject(cropbox)
    xobj = _imagen_xobject(escritor)
    if jpeg is not None:
        xobj._data = jpeg
        xobj[NameObject("/Length")] = NumberObject(len(jpeg))
    for clave in quitar_entradas_imagen:
        if clave in xobj:
            del xobj[clave]
    for clave, valor in (entradas_imagen or {}).items():
        xobj[NameObject(clave)] = valor
    return _bytes(escritor)


def pdf_dos_paginas() -> bytes:
    return _a_pdf([pagina_derecha(), pagina_derecha()])


def jpeg_de(img: Image.Image, **kwargs) -> bytes:
    salida = BytesIO()
    img.save(salida, "JPEG", **kwargs)
    return salida.getvalue()


def filtro_lista(*nombres: str) -> ArrayObject:
    return ArrayObject([NameObject(n) for n in nombres])
