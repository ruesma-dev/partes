# infrastructure/document/pagina_pdf_imagen.py
"""F-059 · Adaptador pypdf + Pillow: página escaneada -> imagen derecha.

Una «página escaneada» es un PDF de UNA página cuyo contenido es solo
``q <cm> /Nombre Do Q``: una imagen JPEG a página completa, sin giro en la
matriz. El ``/Rotate`` de la página la endereza en cualquier visor; aquí se
hace lo mismo que el visor: se gira la imagen incrustada en sentido horario
esos grados y se devuelve como JPEG.

Todo lo que no tenga esa forma es «no aplica», con un motivo cerrado
(``domain/models/conversion_adjunto.py``) y el pipeline manda el PDF como
hasta ahora. Las excepciones de pypdf o de Pillow (PDF roto, JPEG truncado,
imagen demasiado grande) NO se capturan aquí: suben al pipeline (R13).
"""
from __future__ import annotations

from io import BytesIO
from pathlib import PurePath
from typing import Any

from PIL import Image
from pypdf import PdfReader
from pypdf.generic import ContentStream

from domain.models.conversion_adjunto import (
    MOTIVO_COLOR_NO_SOPORTADO,
    MOTIVO_CONTENIDO_NO_ES_UNA_IMAGEN,
    MOTIVO_GIRO_NO_VALIDO,
    MOTIVO_IMAGEN_NO_CUBRE_PAGINA,
    MOTIVO_IMAGEN_NO_JPEG,
    MOTIVO_VARIAS_PAGINAS,
    ResultadoConversion,
)
from domain.models.llm_attachment import LlmAttachment
from domain.ports.conversor_pagina import ConversorPaginaImagen

#: Tolerancia, en puntos, entre la matriz ``cm`` y la MediaBox (R9).
TOLERANCIA_PT = 1.0
#: Diferencia relativa máxima entre la proporción en píxeles y la de la página.
TOLERANCIA_PROPORCION = 0.02
#: Espacios de color que Pillow decodifica sin sorpresas (CMYK de Adobe
#: invierte colores: no se arriesga).
COLORES_SOPORTADOS = ("/DeviceRGB", "/DeviceGray")
#: Operadores, en este orden, de una página que es solo una imagen (R7).
OPERADORES_PAGINA_IMAGEN = (b"q", b"cm", b"Do", b"Q")


def _no_aplica(motivo: str) -> ResultadoConversion:
    return ResultadoConversion(adjunto=None, motivo=motivo)


def _resuelto(valor: Any) -> Any:
    return valor.get_object() if hasattr(valor, "get_object") else valor


class PaginaPdfImagenConversor(ConversorPaginaImagen):
    def __init__(self, *, calidad_jpeg: int = 90) -> None:
        self._calidad_jpeg = calidad_jpeg

    def convertir(self, adjunto: LlmAttachment) -> ResultadoConversion:
        lector = PdfReader(BytesIO(adjunto.data))
        # 1. Una sola página.
        if len(lector.pages) != 1:
            return _no_aplica(MOTIVO_VARIAS_PAGINAS)
        pagina = lector.pages[0]

        # 2. Contenido: exactamente q, cm, Do, Q.
        operaciones = ContentStream(pagina.get_contents(), lector).operations
        if tuple(op for _, op in operaciones) != OPERADORES_PAGINA_IMAGEN:
            return _no_aplica(MOTIVO_CONTENIDO_NO_ES_UNA_IMAGEN)
        matriz = [float(v) for v in operaciones[1][0]]
        nombre = operaciones[2][0][0]
        xobj = pagina["/Resources"]["/XObject"][nombre].get_object()

        # 3. Imagen JPEG de 8 bits, sin máscaras ni /Decode, en RGB o grises.
        motivo = self._motivo_imagen(xobj)
        if motivo:
            return _no_aplica(motivo)

        # 4. La imagen cubre la MediaBox entera, sin giro en la matriz.
        if not self._cubre_la_pagina(pagina, matriz, xobj):
            return _no_aplica(MOTIVO_IMAGEN_NO_CUBRE_PAGINA)

        # 5. Giro de la página: múltiplo de 90, normalizado a 0..270.
        giro = int(_resuelto(pagina.get("/Rotate", 0)))
        if giro % 90 != 0:
            return _no_aplica(MOTIVO_GIRO_NO_VALIDO)
        giro %= 360

        # 6. pypdf no decodifica DCTDecode: get_data() es el JPEG íntegro.
        # Pillow gira antihorario con ángulo positivo: -giro es horario.
        imagen = Image.open(BytesIO(xobj.get_data()))
        if giro:
            imagen = imagen.rotate(-giro, expand=True)

        # 7. JPEG en RGB, sin EXIF (no se pasa ``exif`` al guardar).
        salida = BytesIO()
        imagen.convert("RGB").save(salida, "JPEG", quality=self._calidad_jpeg)
        ancho, alto = imagen.size
        return ResultadoConversion(
            adjunto=LlmAttachment(
                kind="image",
                filename=f"{PurePath(adjunto.filename or 'pagina').stem}.jpg",
                mime_type="image/jpeg",
                data=salida.getvalue(),
            ),
            motivo="",
            giro_grados=giro,
            ancho_px=ancho,
            alto_px=alto,
        )

    # ------------------------------------------------------------ #
    # Comprobaciones.
    # ------------------------------------------------------------ #
    @staticmethod
    def _motivo_imagen(xobj: Any) -> str:
        if xobj.get("/Subtype") != "/Image":
            return MOTIVO_IMAGEN_NO_JPEG
        filtro = _resuelto(xobj.get("/Filter"))
        if isinstance(filtro, list):
            filtro = filtro[0] if len(filtro) == 1 else None
        if filtro != "/DCTDecode":
            return MOTIVO_IMAGEN_NO_JPEG
        if _resuelto(xobj.get("/BitsPerComponent")) != 8:
            return MOTIVO_IMAGEN_NO_JPEG
        if any(clave in xobj for clave in ("/Decode", "/SMask", "/Mask")):
            return MOTIVO_IMAGEN_NO_JPEG
        if _resuelto(xobj.get("/ColorSpace")) not in COLORES_SOPORTADOS:
            return MOTIVO_COLOR_NO_SOPORTADO
        return ""

    @staticmethod
    def _cubre_la_pagina(pagina: Any, matriz: list[float], xobj: Any) -> bool:
        a, b, c, d, e, f = matriz
        caja = pagina.mediabox
        if b != 0 or c != 0:
            return False
        if [float(v) for v in pagina.cropbox] != [float(v) for v in caja]:
            return False
        ajustes = (
            (a, float(caja.width)),
            (d, float(caja.height)),
            (e, float(caja.left)),
            (f, float(caja.bottom)),
        )
        if any(abs(real - esperado) > TOLERANCIA_PT for real, esperado in ajustes):
            return False
        proporcion_px = int(xobj["/Width"]) / int(xobj["/Height"])
        return abs(proporcion_px / (a / d) - 1) <= TOLERANCIA_PROPORCION
