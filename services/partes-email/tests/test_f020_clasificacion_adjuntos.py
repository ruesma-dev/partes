# tests/test_f020_clasificacion_adjuntos.py
"""F-020 · Que adjuntos se abren como correo adjunto y cuales no (R1-R5).

Se prueba por comportamiento: el pipeline completo con el buzon falso y el
extractor MIME real. Abrir un correo adjunto = descargar su `$value` e
ingerir el PDF de dentro.
"""
from __future__ import annotations

import logging

import pytest

from dobles import (
    CARPETA_ERRORES,
    CARPETA_PROCESADOS,
    ODATA_FILE,
    ODATA_ITEM,
    ODATA_REFERENCE,
    BuzonFalso,
    SumideroFalso,
    adjunto,
    construir_pipeline,
    ejecutar,
    mensaje,
)
from eml_sinteticos import a_bytes, correo, fichero_pdf

LOGGER_PIPELINE = "application.pipelines.polling_pipeline"


def _escaner_bytes() -> bytes:
    """`$value` con la forma observada en la sonda: un PDF en el nivel 1."""
    return a_bytes(correo(adjuntos=[fichero_pdf("Scan_0001.pdf")]))


def _correr(att, valor, *, sender="escaner@example.com",
            subject="Attached Image", max_bytes=None):
    buzon = BuzonFalso()
    sumidero = SumideroFalso()
    buzon.anadir_mensaje(mensaje("msg-1", sender=sender, subject=subject),
                         [(att, valor)])
    ejecutar(construir_pipeline(buzon, sumidero), max_bytes=max_bytes)
    return buzon, sumidero


def _descargados(buzon: BuzonFalso) -> list[str]:
    return [ll[2] for ll in buzon.llamadas
            if ll[0] == "download_attachment_value"]


# --- R1 · message/rfc822 no inline se abre, sea cual sea el @odata.type -- #
@pytest.mark.parametrize("odata_type", [ODATA_ITEM, ODATA_FILE, None],
                         ids=["itemAttachment", "fileAttachment", "sin_odata"])
@pytest.mark.parametrize("content_type", ["message/rfc822", "Message/RFC822"])
def test_f020_r1_correo_adjunto_se_abre_e_ingiere_su_pdf(odata_type,
                                                         content_type):
    att = adjunto("att-c", name="Attached Image", content_type=content_type,
                  odata_type=odata_type)

    buzon, sumidero = _correr(att, _escaner_bytes())

    assert _descargados(buzon) == ["att-c"]
    assert [e.filename for e in sumidero.encolados] == ["Scan_0001.pdf"]
    assert buzon.destino("msg-1") == CARPETA_PROCESADOS


def test_f020_r1_correo_adjunto_inline_no_se_abre():
    att = adjunto("att-c", name="Attached Image",
                  content_type="message/rfc822", odata_type=ODATA_ITEM,
                  is_inline=True)

    buzon, sumidero = _correr(att, _escaner_bytes())

    assert _descargados(buzon) == []
    assert sumidero.encolados == []
    assert buzon.destino("msg-1") == CARPETA_ERRORES


# --- R2 · referenceAttachment: fuera siempre, con INFO ------------------- #
@pytest.mark.parametrize("content_type", ["message/rfc822",
                                          "application/pdf"])
def test_f020_r2_reference_attachment_se_descarta_con_info(caplog,
                                                           content_type):
    att = adjunto("att-ref", name="enlace.pdf", content_type=content_type,
                  odata_type=ODATA_REFERENCE)

    with caplog.at_level(logging.INFO, logger=LOGGER_PIPELINE):
        buzon, sumidero = _correr(att, _escaner_bytes())

    assert _descargados(buzon) == []
    assert sumidero.encolados == []
    assert any(r.levelno == logging.INFO and "att-ref" in r.getMessage()
               for r in caplog.records)


# --- R3 · itemAttachment que no es correo: fuera, con INFO --------------- #
@pytest.mark.parametrize("content_type", ["text/calendar",
                                          "application/vnd.ms-outlook", ""])
def test_f020_r3_item_attachment_no_correo_se_descarta_con_info(caplog,
                                                                content_type):
    att = adjunto("att-cita", name="Reunion", content_type=content_type,
                  odata_type=ODATA_ITEM)

    with caplog.at_level(logging.INFO, logger=LOGGER_PIPELINE):
        buzon, sumidero = _correr(att, _escaner_bytes())

    assert _descargados(buzon) == []
    assert sumidero.encolados == []
    assert buzon.destino("msg-1") == CARPETA_ERRORES
    assert any(r.levelno == logging.INFO and "att-cita" in r.getMessage()
               for r in caplog.records)


# --- R4 · limite de tamano sobre el size de Graph ------------------------ #
def test_f020_r4_correo_adjunto_mayor_que_el_limite_se_descarta(caplog):
    att = adjunto("att-grande", name="Attached Image",
                  content_type="message/rfc822", odata_type=ODATA_ITEM,
                  size=2001)

    with caplog.at_level(logging.INFO, logger=LOGGER_PIPELINE):
        buzon, sumidero = _correr(att, _escaner_bytes(), max_bytes=2000)

    assert _descargados(buzon) == []
    assert sumidero.encolados == []
    assert buzon.destino("msg-1") == CARPETA_ERRORES
    avisos = [r for r in caplog.records if "att-grande" in r.getMessage()]
    assert [r.levelno for r in avisos] == [logging.WARNING]


def test_f020_r4_correo_adjunto_justo_en_el_limite_se_abre():
    att = adjunto("att-justo", name="Attached Image",
                  content_type="message/rfc822", odata_type=ODATA_ITEM,
                  size=10_000_000)
    valor = _escaner_bytes()

    buzon, sumidero = _correr(att, valor, max_bytes=10_000_000)

    assert _descargados(buzon) == ["att-justo"]
    assert len(sumidero.encolados) == 1


# --- R5 · sin filtro por remitente ni asunto ----------------------------- #
@pytest.mark.parametrize("sender, subject", [
    ("escaner@example.com", "Attached Image"),
    ("encargado@example.com", "Parte de la obra"),
    ("desconocido@example.org", ""),
])
def test_f020_r5_se_abre_sea_cual_sea_el_remitente(sender, subject):
    att = adjunto("att-c", name="Reenviado", content_type="message/rfc822",
                  odata_type=ODATA_ITEM)

    buzon, sumidero = _correr(att, _escaner_bytes(), sender=sender,
                              subject=subject)

    assert len(sumidero.encolados) == 1
    assert buzon.destino("msg-1") == CARPETA_PROCESADOS
