# tests/test_f020_extractor_mime.py
"""F-020 · Modelos de dominio del correo adjunto y extractor MIME (R7-R13, R17).

El modulo del extractor se importa dentro de las fixtures para que, en la
fase RED, cada test falle por su ausencia y no la suite entera al recogerla.
"""
from __future__ import annotations

import ast
import importlib
import sys
from email.message import EmailMessage as MensajeMime
from pathlib import Path

import pytest

from domain.models.email_models import CorreoEmbebido
from eml_sinteticos import (
    Anidado,
    Fichero,
    a_bytes,
    correo,
    envolver,
    fichero_imagen,
    fichero_pdf,
    fichero_texto,
    pdf_bytes,
)

MODULO_EXTRACTOR = "infrastructure.document.mime_pdf_extractor"


# --------------------------------------------------------------------- #
# R17 · forma de cada elemento de `embedded_in` (design §5).
# --------------------------------------------------------------------- #
def test_f020_r17_to_context_devuelve_exactamente_las_cinco_claves():
    correo_embebido = CorreoEmbebido(level=2, attachment_name="interior.eml",
                                     subject="Attached Image",
                                     sender="escaner@example.com",
                                     date="Wed, 30 Sep 2026 08:16:00 +0200")
    assert correo_embebido.to_context() == {
        "level": 2,
        "attachment_name": "interior.eml",
        "subject": "Attached Image",
        "sender": "escaner@example.com",
        "date": "Wed, 30 Sep 2026 08:16:00 +0200",
    }


def test_f020_r17_to_context_conserva_los_nulos():
    correo_embebido = CorreoEmbebido(level=1, attachment_name=None,
                                     subject=None, sender=None, date=None)
    assert correo_embebido.to_context() == {
        "level": 1, "attachment_name": None, "subject": None,
        "sender": None, "date": None}


# --------------------------------------------------------------------- #
# Extractor MIME (R7-R13).
# --------------------------------------------------------------------- #
@pytest.fixture
def modulo():
    return importlib.import_module(MODULO_EXTRACTOR)


@pytest.fixture
def extractor(modulo):
    return modulo.MimePdfExtractor()


def _extraer(extractor, msg, nombre="Attached Image"):
    return extractor.extraer(raw_mime=a_bytes(msg), nombre_adjunto=nombre)


# --- forma real del escaner (sonda) ------------------------------------ #
def test_f020_r7_forma_del_escaner_un_pdf_en_nivel_1(extractor):
    datos = pdf_bytes(3)
    msg = correo(adjuntos=[Fichero(datos=datos, nombre="Scan_0001.pdf")])

    resultado = _extraer(extractor, msg, nombre="Attached Image")

    assert resultado.tope_excedido is False
    assert len(resultado.pdfs) == 1
    pdf = resultado.pdfs[0]
    assert pdf.filename == "Scan_0001.pdf"
    assert pdf.file_bytes == datos
    assert [c.level for c in pdf.cadena] == [1]
    assert pdf.cadena[0].attachment_name == "Attached Image"
    assert pdf.cadena[0].subject == "Attached Image"
    assert pdf.cadena[0].sender == "escaner@example.com"
    assert pdf.cadena[0].date == "Wed, 30 Sep 2026 08:16:00 +0200"


# --- R7 · recorrido en profundidad y en orden de aparicion --------------- #
def test_f020_r7_orden_de_aparicion_y_cadena_por_nivel(extractor):
    interior = correo(subject="Interior",
                      sender="Otro <interior@example.com>",
                      adjuntos=[fichero_pdf("b.pdf")])
    msg = correo(cuerpo="hola", adjuntos=[
        fichero_pdf("a.pdf"),
        Anidado(interior, nombre="reenviado.eml"),
        fichero_pdf("c.pdf"),
    ])

    resultado = _extraer(extractor, msg)

    assert [p.filename for p in resultado.pdfs] == ["a.pdf", "b.pdf", "c.pdf"]
    assert [c.level for c in resultado.pdfs[0].cadena] == [1]
    cadena_b = resultado.pdfs[1].cadena
    assert [c.level for c in cadena_b] == [1, 2]
    assert cadena_b[1].attachment_name == "reenviado.eml"
    assert cadena_b[1].subject == "Interior"
    assert cadena_b[1].sender == "interior@example.com"
    assert [c.level for c in resultado.pdfs[2].cadena] == [1]


def test_f020_r7_rfc822_sin_nombre_da_attachment_name_nulo(extractor):
    interior = correo(adjuntos=[fichero_pdf("x.pdf")])
    msg = correo(adjuntos=[interior])

    resultado = _extraer(extractor, msg)

    assert resultado.pdfs[0].cadena[1].attachment_name is None


def test_f020_r7_rfc822_vacio_no_rompe(extractor):
    msg = correo(adjuntos=[fichero_pdf("a.pdf")])
    vacio = MensajeMime()
    vacio["Content-Type"] = "message/rfc822"
    msg.attach(vacio)

    resultado = _extraer(extractor, msg)

    assert [p.filename for p in resultado.pdfs] == ["a.pdf"]


# --- R8 · que es un PDF y sus bytes decodificados ------------------------ #
def test_f020_r8_pdf_por_tipo_sin_extension(extractor):
    datos = pdf_bytes(1)
    msg = correo(adjuntos=[Fichero(datos=datos, nombre="escaneo")])

    resultado = _extraer(extractor, msg)

    assert [p.file_bytes for p in resultado.pdfs] == [datos]
    assert resultado.pdfs[0].filename == "escaneo"


def test_f020_r8_pdf_por_extension_en_mayusculas_con_tipo_generico(extractor):
    datos = pdf_bytes(1)
    msg = correo(adjuntos=[Fichero(datos=datos, subtype="octet-stream",
                                   nombre="PARTE.PDF")])

    resultado = _extraer(extractor, msg)

    assert [p.filename for p in resultado.pdfs] == ["PARTE.PDF"]
    assert resultado.pdfs[0].file_bytes == datos


def test_f020_r8_quoted_printable_se_decodifica(extractor):
    datos = pdf_bytes(1)
    msg = correo(adjuntos=[Fichero(datos=datos, nombre="qp.pdf",
                                   cte="quoted-printable")])
    crudo = a_bytes(msg)
    assert b"quoted-printable" in crudo

    resultado = extractor.extraer(raw_mime=crudo, nombre_adjunto=None)

    assert resultado.pdfs[0].file_bytes == datos


# --- R9 · lo demas se ignora (tambien un PDF vacio) ---------------------- #
def test_f020_r9_imagenes_texto_y_pdf_vacio_se_ignoran(extractor):
    msg = correo(cuerpo="texto del cuerpo", adjuntos=[
        fichero_imagen(),
        fichero_texto(),
        Fichero(datos=b"", nombre="vacio.pdf"),
        fichero_pdf("bueno.pdf"),
    ])

    resultado = _extraer(extractor, msg)

    assert [p.filename for p in resultado.pdfs] == ["bueno.pdf"]
    # cuerpo + imagen + texto + PDF vacio
    assert resultado.partes_ignoradas == 4


def test_f020_r9_correo_sin_pdf_devuelve_lista_vacia(extractor):
    msg = correo(adjuntos=[fichero_imagen()])

    resultado = _extraer(extractor, msg)

    assert resultado.pdfs == ()
    assert resultado.tope_excedido is False
    assert resultado.partes_ignoradas == 1


# --- R10 · tope de 5 niveles --------------------------------------------- #
def test_f020_r10_pdf_en_nivel_5_se_extrae(extractor):
    msg = envolver(correo(adjuntos=[fichero_pdf("hondo.pdf")]), 4)

    resultado = _extraer(extractor, msg)

    assert resultado.tope_excedido is False
    assert [p.filename for p in resultado.pdfs] == ["hondo.pdf"]
    assert [c.level for c in resultado.pdfs[0].cadena] == [1, 2, 3, 4, 5]


def test_f020_r10_nivel_6_marca_tope_excedido(extractor):
    msg = envolver(correo(adjuntos=[fichero_pdf("demasiado.pdf")]), 5)

    resultado = _extraer(extractor, msg)

    assert resultado.tope_excedido is True
    assert resultado.pdfs == ()


def test_f020_r10_tope_excedido_aunque_haya_pdf_en_niveles_bajos(extractor):
    hondo = envolver(correo(adjuntos=[fichero_pdf("hondo.pdf")]), 5)
    msg = correo(adjuntos=[fichero_pdf("arriba.pdf"), hondo])

    resultado = _extraer(extractor, msg)

    assert resultado.tope_excedido is True


def test_f020_r10_constante_del_tope_es_5(modulo):
    assert modulo.NIVEL_MAXIMO_ANIDAMIENTO == 5
    msg = envolver(correo(adjuntos=[fichero_pdf("x.pdf")]), 5)
    # El constructor sin argumentos usa la constante.
    assert _extraer(modulo.MimePdfExtractor(), msg).tope_excedido is True


def test_f020_r10_tope_configurable_en_el_constructor(modulo):
    msg = envolver(correo(adjuntos=[fichero_pdf("x.pdf")]), 1)

    resultado = _extraer(modulo.MimePdfExtractor(nivel_maximo=1), msg)

    assert resultado.tope_excedido is True
    assert resultado.pdfs == ()


# --- R11 · nombre del PDF interior --------------------------------------- #
@pytest.mark.parametrize("nombre, esperado", [
    ("C:\\escaner\\salida\\parte.pdf", "parte.pdf"),
    ("carpeta/sub/parte.pdf", "parte.pdf"),
    ("parte.pdf", "parte.pdf"),
])
def test_f020_r11_nombre_base_sin_directorios(extractor, nombre, esperado):
    msg = correo(adjuntos=[fichero_pdf(nombre)])

    resultado = _extraer(extractor, msg)

    assert resultado.pdfs[0].filename == esperado


def test_f020_r11_sin_nombre_documento_n_por_orden_en_el_correo_adjunto(
        extractor):
    interior = correo(adjuntos=[fichero_pdf(None)])
    msg = correo(adjuntos=[fichero_pdf("uno.pdf"), fichero_pdf(None),
                           interior])

    resultado = _extraer(extractor, msg)

    assert [p.filename for p in resultado.pdfs] == [
        "uno.pdf", "documento_2.pdf", "documento_3.pdf"]


# --- R12 · cabeceras defensivas y truncadas ------------------------------ #
def test_f020_r12_cabeceras_ausentes_dan_nulo(extractor):
    msg = correo(subject=None, sender=None, date=None,
                 adjuntos=[fichero_pdf()])

    cadena = _extraer(extractor, msg, nombre=None).pdfs[0].cadena

    assert cadena[0].to_context() == {"level": 1, "attachment_name": None,
                                      "subject": None, "sender": None,
                                      "date": None}


def test_f020_r12_cabeceras_truncadas_a_200(extractor):
    largo = "x" * 150
    msg = correo(subject="S" * 500,
                 sender=f"{largo}{largo}@example.com",
                 date="D" * 300,
                 adjuntos=[fichero_pdf()])

    c = _extraer(extractor, msg, nombre="N" * 300).pdfs[0].cadena[0]

    assert c.subject == "S" * 200
    assert c.sender == ("x" * 200)
    assert c.date == "D" * 200
    assert c.attachment_name == "N" * 200


def test_f020_r12_cabecera_de_200_exactos_no_se_toca(extractor):
    msg = correo(subject="S" * 200, adjuntos=[fichero_pdf()])

    c = _extraer(extractor, msg).pdfs[0].cadena[0]

    assert c.subject == "S" * 200


def test_f020_r12_cabecera_ilegible_da_nulo_sin_excepcion(modulo):
    class MensajeRoto:
        def get(self, nombre, defecto=None):
            raise ValueError(f"cabecera {nombre} ilegible")

        def __getitem__(self, nombre):
            raise ValueError(f"cabecera {nombre} ilegible")

    c = modulo.MimePdfExtractor()._cabeceras(MensajeRoto(), 3, "x.eml")

    assert c.to_context() == {"level": 3, "attachment_name": "x.eml",
                              "subject": None, "sender": None, "date": None}


def test_f020_r12_from_sin_direccion_da_nulo(extractor):
    msg = correo(sender="Solo Un Nombre", adjuntos=[fichero_pdf()])

    c = _extraer(extractor, msg).pdfs[0].cadena[0]

    assert c.sender is None


# --- Ilegible (R22 del lado del extractor) ------------------------------- #
def test_f020_r22_bytes_vacios_son_ilegibles(extractor):
    from domain.ports.extractor_correo_adjunto import CorreoAdjuntoIlegible

    with pytest.raises(CorreoAdjuntoIlegible):
        extractor.extraer(raw_mime=b"", nombre_adjunto="x")


def test_f020_r22_fallo_del_parser_es_ilegible(modulo, monkeypatch):
    from domain.ports.extractor_correo_adjunto import CorreoAdjuntoIlegible

    def parser_roto(*args, **kwargs):
        raise ValueError("parser roto")

    monkeypatch.setattr(modulo, "message_from_bytes", parser_roto)
    with pytest.raises(CorreoAdjuntoIlegible):
        modulo.MimePdfExtractor().extraer(raw_mime=b"From: a\r\n\r\nx",
                                          nombre_adjunto="x")


# --- R13 · pureza: solo stdlib sin red ni disco + dominio ---------------- #
_PROHIBIDOS = {"socket", "ssl", "http", "urllib", "os", "shutil", "tempfile",
               "io", "subprocess", "requests", "httpx", "azure", "pypdf"}


def test_f020_r13_extractor_solo_importa_stdlib_pura_y_dominio():
    ruta = (Path(__file__).resolve().parents[1]
            / "infrastructure" / "document" / "mime_pdf_extractor.py")
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    raices = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            raices |= {a.name.split(".")[0] for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            raices.add(nodo.module.split(".")[0])

    assert "email" in raices
    for raiz in raices:
        assert raiz not in _PROHIBIDOS, raiz
        assert raiz == "domain" or raiz in sys.stdlib_module_names, raiz
