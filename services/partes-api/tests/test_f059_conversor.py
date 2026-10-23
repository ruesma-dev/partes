# tests/test_f059_conversor.py
"""F-059 · R1–R10: el conversor de página escaneada a imagen derecha.

La página escaneada (un PDF de una página cuyo contenido es solo una imagen
JPEG a página completa) se devuelve como imagen JPEG girada en sentido
horario los grados del ``/Rotate``: como la enseña un visor. Todo lo demás
es «no aplica», con un motivo cerrado; un PDF o un JPEG rotos se lanzan
(los recoge el pipeline, R13).

Sin red, sin IA y sin datos reales: los PDF se fabrican en memoria
(``f059_pdf_sinteticos``).
"""
from __future__ import annotations

from io import BytesIO

import pytest
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
from infrastructure.document.pagina_pdf_imagen import PaginaPdfImagenConversor
from PIL import Image, ImageStat, UnidentifiedImageError
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from pypdf.generic import ArrayObject, NameObject, NumberObject
from tests.f059_pdf_sinteticos import (
    ALTO_DERECHA,
    ANCHO_DERECHA,
    LADO_MARCA,
    filtro_lista,
    jpeg_de,
    pagina_derecha,
    pdf_dos_paginas,
    pdf_escaneado,
)

GIROS = (0, 90, 180, 270)
#: Contenido de una página derecha de 300 × 200 (Pillow escribe este).
CM_COMPLETO = f"{ANCHO_DERECHA} 0 0 {ALTO_DERECHA} 0 0 cm"


def _adjunto(pdf: bytes, filename: str = "PT_prueba.pdf") -> LlmAttachment:
    return LlmAttachment(
        kind="pdf", filename=filename, mime_type="application/pdf", data=pdf
    )


def _convertir(pdf: bytes, **kwargs) -> ResultadoConversion:
    return PaginaPdfImagenConversor(**kwargs).convertir(_adjunto(pdf))


def _imagen(resultado: ResultadoConversion) -> Image.Image:
    assert resultado.adjunto is not None, resultado.motivo
    img = Image.open(BytesIO(resultado.adjunto.data))
    img.load()
    return img


def _media(img: Image.Image, caja: tuple[int, int, int, int]) -> float:
    return ImageStat.Stat(img.convert("L").crop(caja)).mean[0]


def _incrustada(pdf: bytes) -> Image.Image:
    lector = PdfReader(BytesIO(pdf))
    xobj = lector.pages[0]["/Resources"]["/XObject"]["/image"].get_object()
    return Image.open(BytesIO(xobj.get_data()))


def _contenido(cm: str = CM_COMPLETO, extra: str = "") -> bytes:
    return f"q {cm} /image Do Q{extra}".encode("ascii")


def _no_aplica(resultado: ResultadoConversion, motivo: str) -> None:
    assert resultado.adjunto is None
    assert resultado.motivo == motivo
    assert resultado.giro_grados is None
    assert resultado.ancho_px is None and resultado.alto_px is None


# ----------------------------- R1 · imagen ------------------------------- #

@pytest.mark.parametrize("rot", GIROS)
def test_f059_r1_la_pagina_escaneada_sale_como_imagen_jpeg(rot: int) -> None:
    resultado = _convertir(pdf_escaneado(rot))
    adjunto = resultado.adjunto
    assert adjunto is not None
    assert adjunto.kind == "image"
    assert adjunto.mime_type == "image/jpeg"
    assert adjunto.filename == "PT_prueba.jpg"
    assert resultado.motivo == ""
    assert resultado.giro_grados == rot
    assert _imagen(resultado).format == "JPEG"


# ------------------------- R2 · normalizar giro -------------------------- #

@pytest.mark.parametrize(
    ("rotate_pdf", "esperado", "rot_guardado"),
    [(-90, 270, 270), (-270, 90, 90), (450, 90, 90), (360, 0, 0), (-180, 180, 180)],
)
def test_f059_r2_el_giro_se_normaliza_modulo_360(
    rotate_pdf: int, esperado: int, rot_guardado: int
) -> None:
    resultado = _convertir(pdf_escaneado(rot_guardado, rotate_pdf=rotate_pdf))
    assert resultado.giro_grados == esperado
    img = _imagen(resultado)
    assert img.size == (ANCHO_DERECHA, ALTO_DERECHA)
    assert _media(img, (0, 0, 40, 40)) < 60


# ---------------------- R3 · como la enseña el visor --------------------- #

@pytest.mark.parametrize("rot", GIROS)
def test_f059_r3_la_marca_queda_arriba_a_la_izquierda(rot: int) -> None:
    img = _imagen(_convertir(pdf_escaneado(rot)))
    w, h = img.size
    lado = LADO_MARCA * 2 // 3
    assert _media(img, (0, 0, lado, lado)) < 60, "falta la marca arriba a la izquierda"
    assert _media(img, (w - lado, 0, w, lado)) > 200
    assert _media(img, (0, h - lado, lado, h)) > 200
    assert _media(img, (w - lado, h - lado, w, h)) > 200


# ------------------------- R4 · medidas y escala ------------------------- #

@pytest.mark.parametrize("rot", GIROS)
def test_f059_r4_ancho_y_alto_se_intercambian_solo_con_90_y_270(rot: int) -> None:
    pdf = pdf_escaneado(rot)
    w0, h0 = _incrustada(pdf).size
    resultado = _convertir(pdf)
    img = _imagen(resultado)
    esperado = (h0, w0) if rot in (90, 270) else (w0, h0)
    assert img.size == esperado
    assert (resultado.ancho_px, resultado.alto_px) == esperado
    assert esperado == (ANCHO_DERECHA, ALTO_DERECHA)


# --------------------------- R5 · JPEG limpio ---------------------------- #

def test_f059_r5_jpeg_rgb_calidad_90_y_sin_exif() -> None:
    """El JPEG incrustado trae EXIF (con orientación): no debe viajar."""
    exif = Image.Exif()
    exif[0x0112] = 6        # Orientation: «gira 90 al mostrar»
    exif[0x010F] = "escaner-prueba"
    guardada = pagina_derecha().rotate(270, expand=True)
    pdf = pdf_escaneado(270, jpeg=jpeg_de(guardada, exif=exif.tobytes()))
    assert _incrustada(pdf).getexif(), "el sintético debe traer EXIF"

    resultado = _convertir(pdf)
    img = _imagen(resultado)
    assert img.mode == "RGB"
    assert "exif" not in img.info
    assert len(img.getexif()) == 0
    esperado = _incrustada(pdf).rotate(-270, expand=True).convert("RGB")
    assert resultado.adjunto.data == jpeg_de(esperado, quality=90)


def test_f059_r5_la_calidad_se_puede_configurar() -> None:
    pdf = pdf_escaneado(90)
    resultado = _convertir(pdf, calidad_jpeg=40)
    esperado = _incrustada(pdf).rotate(-90, expand=True).convert("RGB")
    assert resultado.adjunto.data == jpeg_de(esperado, quality=40)


def test_f059_r5_la_escala_de_grises_sale_en_rgb() -> None:
    img = _imagen(_convertir(pdf_escaneado(90, modo="L")))
    assert img.mode == "RGB"
    assert _media(img, (0, 0, 40, 40)) < 60


# ------------------------- R6 · varias páginas --------------------------- #

def test_f059_r6_varias_paginas_no_aplica() -> None:
    _no_aplica(_convertir(pdf_dos_paginas()), MOTIVO_VARIAS_PAGINAS)


# --------------------- R7 · contenido que no es imagen ------------------- #

@pytest.mark.parametrize(
    "contenido",
    [
        _contenido(extra=" BT /F1 12 Tf 10 10 Td (hola) Tj ET"),
        _contenido(extra=" 0 0 m 10 10 l S"),
        _contenido() + b" " + _contenido(),
        f"{CM_COMPLETO} /image Do".encode("ascii"),
        f"q {CM_COMPLETO} /image Do".encode("ascii"),
        "q /image Do Q".encode("ascii"),
        f"q {CM_COMPLETO} {CM_COMPLETO} /image Do Q".encode("ascii"),
        f"q {CM_COMPLETO} Q".encode("ascii"),
        b"",
    ],
    ids=["texto", "dibujo", "dos-imagenes", "sin-q", "sin-Q", "sin-cm",
         "dos-cm", "sin-Do", "vacio"],
)
def test_f059_r7_contenido_que_no_es_una_imagen(contenido: bytes) -> None:
    _no_aplica(
        _convertir(pdf_escaneado(0, contenido=contenido)),
        MOTIVO_CONTENIDO_NO_ES_UNA_IMAGEN,
    )


def test_f059_r7_el_orden_q_cm_do_q_es_obligatorio() -> None:
    contenido = f"q /image Do {CM_COMPLETO} Q".encode("ascii")
    _no_aplica(
        _convertir(pdf_escaneado(0, contenido=contenido)),
        MOTIVO_CONTENIDO_NO_ES_UNA_IMAGEN,
    )


# --------------------- R8 · solo JPEG en RGB o grises -------------------- #

@pytest.mark.parametrize(
    ("kwargs", "motivo"),
    [
        ({"modo": "P"}, MOTIVO_IMAGEN_NO_JPEG),
        ({"entradas_imagen": {"/Decode": ArrayObject(
            [NumberObject(1), NumberObject(0)] * 3)}}, MOTIVO_IMAGEN_NO_JPEG),
        ({"entradas_imagen": {"/SMask": NumberObject(0)}}, MOTIVO_IMAGEN_NO_JPEG),
        ({"entradas_imagen": {"/Mask": NumberObject(0)}}, MOTIVO_IMAGEN_NO_JPEG),
        ({"entradas_imagen": {"/BitsPerComponent": NumberObject(4)}},
         MOTIVO_IMAGEN_NO_JPEG),
        ({"entradas_imagen": {"/Filter": filtro_lista(
            "/FlateDecode", "/DCTDecode")}}, MOTIVO_IMAGEN_NO_JPEG),
        ({"entradas_imagen": {"/Filter": NameObject("/JPXDecode")}},
         MOTIVO_IMAGEN_NO_JPEG),
        ({"quitar_entradas_imagen": ("/Filter",)}, MOTIVO_IMAGEN_NO_JPEG),
        ({"entradas_imagen": {"/Subtype": NameObject("/Form")}},
         MOTIVO_IMAGEN_NO_JPEG),
        ({"modo": "CMYK", "quitar_entradas_imagen": ("/Decode",)},
         MOTIVO_COLOR_NO_SOPORTADO),
        ({"entradas_imagen": {"/ColorSpace": ArrayObject(
            [NameObject("/CalRGB")])}}, MOTIVO_COLOR_NO_SOPORTADO),
    ],
    ids=["paleta", "decode", "smask", "mask", "4-bits", "dos-filtros", "jpx",
         "sin-filtro", "no-es-imagen", "cmyk", "calrgb"],
)
def test_f059_r8_imagen_no_soportada_no_aplica(kwargs: dict, motivo: str) -> None:
    _no_aplica(_convertir(pdf_escaneado(0, **kwargs)), motivo)


def test_f059_r8_filtro_como_lista_de_uno_si_aplica() -> None:
    pdf = pdf_escaneado(
        90, entradas_imagen={"/Filter": filtro_lista("/DCTDecode")})
    assert _convertir(pdf).giro_grados == 90


def test_f059_r8_escala_de_grises_si_aplica() -> None:
    assert _convertir(pdf_escaneado(0, modo="L")).adjunto is not None


# ------------------ R9 · la imagen cubre la página entera ---------------- #

@pytest.mark.parametrize(
    "kwargs",
    [
        {"contenido": _contenido("150 0 0 100 0 0 cm")},
        {"contenido": _contenido("300 0 0 100 0 0 cm")},
        {"contenido": _contenido("0 200 -300 0 300 0 cm")},
        {"contenido": _contenido("300 0 5 200 0 0 cm")},
        {"contenido": _contenido("300 5 0 200 0 0 cm")},
        {"contenido": _contenido("300 0 0 200 5 0 cm")},
        {"contenido": _contenido("300 0 0 200 0 5 cm")},
        {"contenido": _contenido("302 0 0 200 0 0 cm")},
        {"contenido": _contenido("300 0 0 198 0 0 cm")},
        {"cropbox": (0, 0, 300, 150)},
        {"cropbox": (10, 0, 300, 200)},
        {"imagen": Image.new("RGB", (300, 300), "white"),
         "mediabox": (0, 0, 300, 200), "contenido": _contenido()},
        {"imagen": Image.new("RGB", (300, 205), "white"),
         "mediabox": (0, 0, 300, 200), "contenido": _contenido()},
        {"mediabox": (10, 10, 310, 210)},
    ],
    ids=["media-pagina", "medio-alto", "cm-girada", "cm-inclinada-c",
         "cm-inclinada-b", "desplazada-x", "desplazada-y", "ancha-2pt",
         "baja-2pt", "cropbox-menor", "cropbox-desplazada", "proporcion-1",
         "proporcion-2.4pc", "mediabox-desplazada"],
)
def test_f059_r9_imagen_que_no_cubre_la_pagina(kwargs: dict) -> None:
    _no_aplica(
        _convertir(pdf_escaneado(0, **kwargs)), MOTIVO_IMAGEN_NO_CUBRE_PAGINA)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"contenido": _contenido("300.9 0 0 199.1 0.9 -0.9 cm")},
        {"contenido": _contenido("299.1 0 0 200.9 -0.9 0.9 cm")},
        # T8: desvío de EXACTAMENTE 1 pt (entero: la resta es exacta en float);
        # «tolerancia 1 pt» incluye el borde (mata `>` -> `>=`).
        {"contenido": _contenido("301 0 0 200 0 0 cm")},
        {"contenido": _contenido("300 0 0 199 -1 1 cm")},
        {"mediabox": (10, 10, 310, 210),
         "contenido": _contenido("300 0 0 200 10 10 cm")},
        {"imagen": Image.new("RGB", (300, 204), "white"),
         "mediabox": (0, 0, 300, 200), "contenido": _contenido()},
        {"imagen": Image.new("RGB", (305, 200), "white"),
         "mediabox": (0, 0, 300, 200), "contenido": _contenido()},
    ],
    ids=["tolerancia-1pt", "tolerancia-1pt-al-reves", "tolerancia-1pt-exacta-ancho",
         "tolerancia-1pt-exacta-alto-y-origen", "mediabox-desplazada",
         "proporcion-1.96pc", "proporcion-1.7pc-ancha"],
)
def test_f059_r9_dentro_de_las_tolerancias_si_aplica(kwargs: dict) -> None:
    resultado = _convertir(pdf_escaneado(0, **kwargs))
    assert resultado.adjunto is not None, resultado.motivo


# --------------------------- R10 · giro válido --------------------------- #

@pytest.mark.parametrize("rotate_pdf", [45, 100, -30, 271])
def test_f059_r10_giro_que_no_es_multiplo_de_90(rotate_pdf: int) -> None:
    _no_aplica(
        _convertir(pdf_escaneado(0, rotate_pdf=rotate_pdf)), MOTIVO_GIRO_NO_VALIDO)


# ------------------ R13 (lado del conversor) · se lanza ------------------ #

def test_f059_r13_bytes_que_no_son_pdf_lanzan() -> None:
    with pytest.raises(PdfReadError):
        _convertir(b"esto no es un PDF")


def test_f059_r13_jpeg_truncado_lanza() -> None:
    entero = jpeg_de(pagina_derecha())
    with pytest.raises(OSError, match="truncated"):
        _convertir(pdf_escaneado(0, jpeg=entero[: len(entero) // 2]))


def test_f059_r13_bytes_de_imagen_que_no_son_jpeg_lanzan() -> None:
    with pytest.raises(UnidentifiedImageError):
        _convertir(pdf_escaneado(0, jpeg=b"no es un jpeg" * 10))
