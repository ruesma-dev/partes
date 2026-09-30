# tests/test_f020_pipeline_correo_adjunto.py
"""F-020 · Ingesta de los PDF de un correo adjunto y destino del correo.

R6, R14-R17, R19-R24. Pipeline con el troceador de PDF y el extractor MIME
REALES; buzon y sumidero en memoria (`dobles.py`). Sin red.
"""
from __future__ import annotations

import hashlib
import logging
from io import BytesIO

from pypdf import PdfReader

from dobles import (
    CARPETA_ERRORES,
    CARPETA_PROCESADOS,
    ODATA_ITEM,
    BuzonFalso,
    SumideroFalso,
    adjunto,
    construir_pipeline,
    ejecutar,
    mensaje,
)
from domain.models.email_models import (
    CorreoEmbebido,
    ExtraccionCorreoAdjunto,
    PdfEmbebido,
)
from eml_sinteticos import (
    Anidado,
    Fichero,
    a_bytes,
    correo,
    envolver,
    fichero_imagen,
    fichero_pdf,
    pdf_bytes,
)

LOGGER_PIPELINE = "application.pipelines.polling_pipeline"


def _sha(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


def _correo_adjunto(id="att-c", *, name="Attached Image", size=1000):
    return adjunto(id, name=name, content_type="message/rfc822",
                   odata_type=ODATA_ITEM, size=size)


def _montar(adjuntos, *, sumidero=None, extractor=None):
    buzon = BuzonFalso()
    sumidero = sumidero or SumideroFalso()
    buzon.anadir_mensaje(mensaje("msg-1"), adjuntos)
    if extractor is None:
        pipeline = construir_pipeline(buzon, sumidero)
    else:
        pipeline = construir_pipeline(buzon, sumidero, extractor=extractor)
    return buzon, sumidero, pipeline


def _correr(adjuntos, *, sumidero=None, max_bytes=None, extractor=None):
    buzon, sumidero, pipeline = _montar(adjuntos, sumidero=sumidero,
                                        extractor=extractor)
    ejecutar(pipeline, max_bytes=max_bytes)
    return buzon, sumidero


def _mensajes(caplog, nivel=None):
    return [r.getMessage() for r in caplog.records
            if nivel is None or r.levelno == nivel]


# --- R6 · ninguna llamada a Graph adicional ------------------------------ #
def test_f020_r6_un_correo_adjunto_solo_cuesta_su_descarga_de_value():
    valor = a_bytes(correo(adjuntos=[fichero_pdf("a.pdf")]))

    buzon, _ = _correr([(_correo_adjunto(), valor)])

    assert buzon.llamadas == [
        ("list_unread_with_attachments", "origen-id"),
        ("list_attachments", "msg-1"),
        ("download_attachment_value", "msg-1", "att-c"),
        ("move_message", "msg-1", CARPETA_PROCESADOS),
    ]


# --- R14 · cada PDF interior, troceado por paginas, en orden ------------- #
def test_f020_r14_varios_pdf_interiores_se_trocean_e_ingieren_en_orden():
    valor = a_bytes(correo(adjuntos=[fichero_pdf("tres.pdf", paginas=3),
                                     fichero_imagen(),
                                     fichero_pdf("uno.pdf", paginas=1)]))

    buzon, sumidero = _correr([(_correo_adjunto(), valor)])

    assert [e.filename for e in sumidero.encolados] == [
        "tres__page_001_of_003.pdf", "tres__page_002_of_003.pdf",
        "tres__page_003_of_003.pdf", "uno.pdf"]
    for e in sumidero.encolados:
        assert e.mime_type == "application/pdf"
        assert len(PdfReader(BytesIO(e.file_bytes)).pages) == 1
        assert e.context["document"]["sha256"] == _sha(e.file_bytes)
        assert e.context["transport"] == {"document_id": e.document_id,
                                          "source": "email-poller"}
    assert len({e.document_id for e in sumidero.encolados}) == 4
    assert buzon.destino("msg-1") == CARPETA_PROCESADOS


# --- R15 · PDF interior por encima del limite ---------------------------- #
def test_f020_r15_pdf_interior_mayor_que_el_limite_se_descarta(caplog):
    pequeno, grande = pdf_bytes(1), pdf_bytes(40)
    limite = (len(pequeno) + len(grande)) // 2
    assert len(pequeno) < limite < len(grande)
    valor = a_bytes(correo(adjuntos=[Fichero(grande, nombre="grande.pdf"),
                                     Fichero(pequeno, nombre="peq.pdf")]))

    with caplog.at_level(logging.INFO, logger=LOGGER_PIPELINE):
        buzon, sumidero = _correr([(_correo_adjunto(size=10), valor)],
                                  max_bytes=limite)

    assert [e.filename for e in sumidero.encolados] == ["peq.pdf"]
    assert buzon.destino("msg-1") == CARPETA_PROCESADOS
    assert any("grande.pdf" in m for m in _mensajes(caplog, logging.WARNING))


def test_f020_r15_si_solo_habia_un_pdf_grande_no_cuenta_como_encontrado(
        caplog):
    grande = pdf_bytes(40)
    valor = a_bytes(correo(adjuntos=[Fichero(grande, nombre="grande.pdf")]))

    with caplog.at_level(logging.INFO, logger=LOGGER_PIPELINE):
        buzon, sumidero = _correr([(_correo_adjunto(size=10), valor)],
                                  max_bytes=len(grande) - 1)

    assert sumidero.encolados == []
    assert buzon.destino("msg-1") == CARPETA_ERRORES
    avisos = _mensajes(caplog, logging.WARNING)
    assert any("msg-1" in m and "att-c" in m and "sin" in m for m in avisos)


# --- R16 · attachment y document.source_* describen el PDF interior ------ #
def test_f020_r16_contexto_describe_el_pdf_interior():
    datos = pdf_bytes(1)
    valor = a_bytes(correo(adjuntos=[Fichero(datos,
                                             nombre="C:\\scan\\Scan_7.pdf")]))

    _, sumidero = _correr([(_correo_adjunto(size=123_456), valor)])

    [e] = sumidero.encolados
    assert e.context["attachment"] == {
        "id": "att-c", "name": "Scan_7.pdf", "contentType": "application/pdf",
        "size": len(datos), "sha256": _sha(datos), "page_number": 1,
        "page_count": 1, "was_split": False,
    }
    assert e.context["document"] == {
        "filename": "Scan_7.pdf", "mime_type": "application/pdf",
        "sha256": _sha(datos), "page_number": 1, "page_count": 1,
        "was_split": False, "source_attachment_filename": "Scan_7.pdf",
        "source_attachment_mime_type": "application/pdf",
        "source_attachment_sha256": _sha(datos),
    }
    assert e.context["email"]["id"] == "msg-1"


# --- R17 · embedded_in: la cadena del exterior al interior --------------- #
def test_f020_r17_embedded_in_lleva_la_cadena_completa():
    interior = correo(subject="Reenvio", sender="Ana <ana@example.com>",
                      date="Tue, 29 Sep 2026 10:00:00 +0200",
                      adjuntos=[fichero_pdf("hondo.pdf")])
    valor = a_bytes(correo(adjuntos=[fichero_pdf("arriba.pdf"),
                                     Anidado(interior, nombre="fw.eml")]))

    _, sumidero = _correr([(_correo_adjunto(name="Attached Image"), valor)])

    nivel_1 = {"level": 1, "attachment_name": "Attached Image",
               "subject": "Attached Image", "sender": "escaner@example.com",
               "date": "Wed, 30 Sep 2026 08:16:00 +0200"}
    nivel_2 = {"level": 2, "attachment_name": "fw.eml", "subject": "Reenvio",
               "sender": "ana@example.com",
               "date": "Tue, 29 Sep 2026 10:00:00 +0200"}
    arriba, hondo = sumidero.encolados
    assert arriba.context["embedded_in"] == [nivel_1]
    assert hondo.context["embedded_in"] == [nivel_1, nivel_2]
    assert list(hondo.context) == ["transport", "email", "attachment",
                                   "document", "embedded_in"]


def test_f020_r17_embedded_in_en_cada_pagina_de_un_pdf_multipagina():
    valor = a_bytes(correo(adjuntos=[fichero_pdf("dos.pdf", paginas=2)]))

    _, sumidero = _correr([(_correo_adjunto(), valor)])

    assert len(sumidero.encolados) == 2
    for e in sumidero.encolados:
        assert [c["level"] for c in e.context["embedded_in"]] == [1]


# --- R19 · PDF directos y correos adjuntos en la misma pasada, en orden --- #
def test_f020_r19_mezcla_en_el_orden_de_graph_y_en_una_pasada():
    valor = a_bytes(correo(adjuntos=[fichero_pdf("interior.pdf")]))

    buzon, sumidero = _correr([
        (adjunto("att-1", name="primero.pdf"), pdf_bytes(1)),
        (_correo_adjunto("att-2"), valor),
        (adjunto("att-3", name="tercero.pdf"), pdf_bytes(1)),
    ])

    assert [e.filename for e in sumidero.encolados] == [
        "primero.pdf", "interior.pdf", "tercero.pdf"]
    assert [e.context["attachment"]["id"] for e in sumidero.encolados] == [
        "att-1", "att-2", "att-3"]
    assert "embedded_in" in sumidero.encolados[1].context
    assert "embedded_in" not in sumidero.encolados[0].context
    assert buzon.movidos == [("msg-1", CARPETA_PROCESADOS)]


# --- R20 · destino: Procesados sii todo bien y >= 1 documento ------------ #
def test_f020_r20_todo_bien_con_documentos_va_a_procesados():
    valor = a_bytes(correo(adjuntos=[fichero_pdf()]))

    buzon, _ = _correr([(_correo_adjunto(), valor)])

    assert buzon.movidos == [("msg-1", CARPETA_PROCESADOS)]


def test_f020_r20_fallo_de_ingesta_de_una_pagina_va_a_errores():
    valor = a_bytes(correo(adjuntos=[fichero_pdf(paginas=2)]))

    buzon, sumidero = _correr([(_correo_adjunto(), valor)],
                              sumidero=SumideroFalso(fallar_en=1))

    assert len(sumidero.encolados) == 1  # la otra pagina si entra
    assert buzon.movidos == [("msg-1", CARPETA_ERRORES)]


def test_f020_r20_pdf_interior_corrupto_va_a_errores(caplog):
    valor = a_bytes(correo(adjuntos=[Fichero(b"esto no es un pdf",
                                             nombre="roto.pdf")]))

    with caplog.at_level(logging.INFO, logger=LOGGER_PIPELINE):
        buzon, sumidero = _correr([(_correo_adjunto(), valor)])

    assert sumidero.encolados == []
    assert buzon.movidos == [("msg-1", CARPETA_ERRORES)]
    assert any("att-c" in m for m in _mensajes(caplog, logging.ERROR))


def test_f020_r20_tope_excedido_no_ingiere_nada_y_va_a_errores(caplog):
    # D3: todo o nada. arriba.pdf (nivel 1) tampoco entra.
    hondo = envolver(correo(adjuntos=[fichero_pdf("hondo.pdf")]), 5)
    valor = a_bytes(correo(adjuntos=[fichero_pdf("arriba.pdf"), hondo]))

    with caplog.at_level(logging.INFO, logger=LOGGER_PIPELINE):
        buzon, sumidero = _correr([
            (_correo_adjunto("att-hondo"), valor),
            (adjunto("att-directo", name="directo.pdf"), pdf_bytes(1)),
        ])

    assert [e.filename for e in sumidero.encolados] == ["directo.pdf"]
    assert buzon.movidos == [("msg-1", CARPETA_ERRORES)]
    errores = _mensajes(caplog, logging.ERROR)
    assert any("msg-1" in m and "att-hondo" in m and "5" in m
               for m in errores)


def test_f020_r20_sin_ningun_documento_ingerido_va_a_errores():
    valor = a_bytes(correo(cuerpo="solo texto"))

    buzon, sumidero = _correr([(_correo_adjunto(), valor)])

    assert sumidero.encolados == []
    assert buzon.movidos == [("msg-1", CARPETA_ERRORES)]


# --- R21 · correo adjunto sin PDF: WARNING; destino segun el resto (D2) --- #
def test_f020_r21_correo_adjunto_sin_pdf_junto_a_otro_documento_procesados(
        caplog):
    sin_pdf = a_bytes(correo(adjuntos=[fichero_imagen()]))

    with caplog.at_level(logging.INFO, logger=LOGGER_PIPELINE):
        buzon, sumidero = _correr([
            (_correo_adjunto("att-vacio"), sin_pdf),
            (adjunto("att-1", name="bueno.pdf"), pdf_bytes(1)),
        ])

    assert [e.filename for e in sumidero.encolados] == ["bueno.pdf"]
    assert buzon.movidos == [("msg-1", CARPETA_PROCESADOS)]
    assert any("msg-1" in m and "att-vacio" in m
               for m in _mensajes(caplog, logging.WARNING))


# --- R22 · descarga fallida o bytes ilegibles ---------------------------- #
def test_f020_r22_fallo_de_descarga_sigue_con_los_demas_y_va_a_errores(
        caplog):
    buzon, sumidero, pipeline = _montar([
        (_correo_adjunto("att-falla"), b"no importa"),
        (adjunto("att-1", name="bueno.pdf"), pdf_bytes(1)),
    ])
    buzon.fallo_descarga.add("att-falla")

    with caplog.at_level(logging.INFO, logger=LOGGER_PIPELINE):
        ejecutar(pipeline)

    assert [e.filename for e in sumidero.encolados] == ["bueno.pdf"]
    assert buzon.movidos == [("msg-1", CARPETA_ERRORES)]
    assert any("att-falla" in m for m in _mensajes(caplog, logging.ERROR))


def test_f020_r22_bytes_ilegibles_van_a_errores(caplog):
    with caplog.at_level(logging.INFO, logger=LOGGER_PIPELINE):
        buzon, sumidero = _correr([(_correo_adjunto("att-vacio"), b"")])

    assert sumidero.encolados == []
    assert buzon.movidos == [("msg-1", CARPETA_ERRORES)]
    assert any("att-vacio" in m for m in _mensajes(caplog, logging.ERROR))


# --- R23 · ni PDF directos ni correos adjuntos --------------------------- #
def test_f020_r23_sin_nada_elegible_va_a_errores_nombrando_ambos_casos(
        caplog):
    with caplog.at_level(logging.INFO, logger=LOGGER_PIPELINE):
        buzon, sumidero = _correr([
            (adjunto("att-doc", name="acta.docx",
                     content_type="application/msword"), b"doc"),
        ])

    assert sumidero.encolados == []
    assert buzon.movidos == [("msg-1", CARPETA_ERRORES)]
    avisos = [m for m in _mensajes(caplog, logging.WARNING) if "msg-1" in m]
    assert any("directos" in m and "correos adjuntos" in m for m in avisos)


# --- R24 · ningun log lleva bytes del PDF ni del MIME ------------------- #
def test_f020_r24_los_logs_no_llevan_bytes_ni_contenido(caplog):
    interior = correo(subject="ASUNTO-INTERIOR-MARCA",
                      adjuntos=[fichero_pdf("x.pdf", paginas=2)])
    valor = a_bytes(correo(cuerpo="CUERPO-MARCA",
                           adjuntos=[Anidado(interior, nombre="i.eml")]))

    with caplog.at_level(logging.DEBUG):
        _correr([(_correo_adjunto(), valor)])

    texto = "\n".join(r.getMessage() for r in caplog.records)
    assert "%PDF" not in texto
    assert "JVBER" not in texto  # "%PDF" en base64
    assert "CUERPO-MARCA" not in texto
    assert "ASUNTO-INTERIOR-MARCA" not in texto
    assert "Content-Type" not in texto


# --- El pipeline usa el extractor INYECTADO (R25, lado del pipeline) ----- #
class ExtractorFalso:
    nivel_maximo = 5

    def __init__(self) -> None:
        self.llamadas: list[tuple[bytes, str | None]] = []

    def extraer(self, *, raw_mime, nombre_adjunto):
        self.llamadas.append((raw_mime, nombre_adjunto))
        eslabon = CorreoEmbebido(level=1, attachment_name=nombre_adjunto,
                                 subject=None, sender=None, date=None)
        return ExtraccionCorreoAdjunto(
            pdfs=(PdfEmbebido(filename="falso.pdf", file_bytes=pdf_bytes(1),
                              cadena=(eslabon,)),),
            tope_excedido=False, partes_ignoradas=0)


def test_f020_r25_el_pipeline_usa_el_extractor_inyectado():
    extractor = ExtractorFalso()

    buzon, sumidero = _correr([(_correo_adjunto(), b"MIME-FALSO")],
                              extractor=extractor)

    assert extractor.llamadas == [(b"MIME-FALSO", "Attached Image")]
    assert [e.filename for e in sumidero.encolados] == ["falso.pdf"]
    assert buzon.movidos == [("msg-1", CARPETA_PROCESADOS)]
