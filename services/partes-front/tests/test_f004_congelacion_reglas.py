# tests/test_f004_congelacion_reglas.py
"""R1 y R2 · la matriz de congelacion, en funciones PURAS.

Toda la feature F-004 cuelga de esta decision: si la regla se escribiera
dos veces (una para las guardas del repositorio y otra para pintar el
candado en la vista), un dia dirian cosas distintas y el portal ensenaria
como editable algo que el servidor rechaza. Aqui se fija la matriz
completa contra las dos funciones que TODO el resto del codigo usa.

Sin BBDD, sin FastAPI y sin red: son funciones puras.
"""
from __future__ import annotations

import pytest
from application.services.congelacion import (
    ESTADOS_CONGELANTES,
    CongeladoError,
    exigir_documento_editable,
    exigir_linea_editable,
    motivo_congelacion_documento,
    motivo_congelacion_linea,
)

#: Estados que NO congelan: son justo el camino de arreglo de una linea
#: que no llego a Sigrid (asignar codigo, corregir datos, resolver el
#: conflicto y reintentar).
ESTADOS_LIBRES = (None, "", "omitido", "error", "conflicto")


# --------------------------- R1 · linea -------------------------------- #

@pytest.mark.parametrize("estado", ESTADOS_LIBRES)
def test_f004_r1_linea_libre_en_parte_sin_aprobar_no_congela(estado) -> None:
    assert motivo_congelacion_linea(
        doc_aprobado=False, sigrid_estado=estado) is None


@pytest.mark.parametrize("estado", ESTADOS_LIBRES)
def test_f004_r1_documento_aprobado_congela_cualquier_linea(estado) -> None:
    motivo = motivo_congelacion_linea(doc_aprobado=True, sigrid_estado=estado)
    assert motivo is not None
    assert "aprobado" in motivo.lower()


def test_f004_r1_encolado_congela_aunque_el_parte_no_este_aprobado() -> None:
    """El flujo por obra x mes encola SIN aprobar el documento: si solo
    mirasemos `approved`, la linea en vuelo quedaria editable."""
    motivo = motivo_congelacion_linea(
        doc_aprobado=False, sigrid_estado="encolado")
    assert motivo is not None
    assert "encolada" in motivo.lower()


def test_f004_r1_registrado_congela_aunque_el_parte_no_este_aprobado() -> None:
    motivo = motivo_congelacion_linea(
        doc_aprobado=False, sigrid_estado="registrado")
    assert motivo is not None
    assert "sigrid" in motivo.lower()


def test_f004_r1_encolado_y_registrado_dan_motivos_distintos() -> None:
    """El motivo mas restrictivo/informativo manda, y no son el mismo
    texto: `encolado` es el unico que ademas bloquea la desaprobacion
    (R10), y quien lea el candado tiene que poder distinguirlos."""
    assert motivo_congelacion_linea(
        doc_aprobado=False, sigrid_estado="encolado",
    ) != motivo_congelacion_linea(
        doc_aprobado=False, sigrid_estado="registrado")


def test_f004_r1_registrado_tiene_prioridad_sobre_aprobado() -> None:
    """El candado de una linea ya escrita en Sigrid debe explicar ESO, no
    'desapruebalo': desaprobar no la libera (R11)."""
    motivo = motivo_congelacion_linea(
        doc_aprobado=True, sigrid_estado="registrado")
    assert motivo == motivo_congelacion_linea(
        doc_aprobado=False, sigrid_estado="registrado")


def test_f004_r1_el_estado_se_normaliza() -> None:
    """Los estados llegan de una columna de texto: espacios o mayusculas
    no pueden convertir una linea registrada en editable."""
    assert motivo_congelacion_linea(
        doc_aprobado=False, sigrid_estado=" Registrado ") is not None
    assert motivo_congelacion_linea(
        doc_aprobado=False, sigrid_estado="ENCOLADO") is not None


def test_f004_r1_los_estados_congelantes_son_exactamente_dos() -> None:
    assert tuple(ESTADOS_CONGELANTES) == ("encolado", "registrado")


# ------------------------- R2 · documento ------------------------------ #

def test_f004_r2_documento_aprobado_esta_congelado() -> None:
    motivo = motivo_congelacion_documento(aprobado=True, estados_lineas=[])
    assert motivo is not None
    assert "aprobado" in motivo.lower()


def test_f004_r2_documento_sin_aprobar_ni_lineas_en_sigrid_es_editable() -> None:
    assert motivo_congelacion_documento(
        aprobado=False, estados_lineas=ESTADOS_LIBRES) is None


@pytest.mark.parametrize("estado", ["encolado", "registrado"])
def test_f004_r2_una_sola_linea_en_sigrid_congela_el_documento(estado) -> None:
    """Editar la cabecera propaga fecha/obra a TODAS las lineas: basta
    una linea viva en Sigrid para que el cambio desincronice."""
    assert motivo_congelacion_documento(
        aprobado=False, estados_lineas=["omitido", estado, None],
    ) is not None


def test_f004_r2_el_motivo_del_documento_prioriza_el_encolado() -> None:
    con_encolado = motivo_congelacion_documento(
        aprobado=True, estados_lineas=["registrado", "encolado"])
    sin_encolado = motivo_congelacion_documento(
        aprobado=True, estados_lineas=["registrado", "omitido"])
    assert con_encolado != sin_encolado
    assert "encolada" in con_encolado.lower()


def test_f004_r2_el_estado_de_las_lineas_se_normaliza() -> None:
    assert motivo_congelacion_documento(
        aprobado=False, estados_lineas=[" Encolado "]) is not None


# ---------------------- guardas (CongeladoError) ------------------------ #

def test_f004_r1_la_guarda_de_linea_no_lanza_si_esta_libre() -> None:
    exigir_linea_editable(doc_aprobado=False, sigrid_estado="omitido")


def test_f004_r1_la_guarda_de_linea_lanza_con_el_motivo() -> None:
    with pytest.raises(CongeladoError) as exc:
        exigir_linea_editable(doc_aprobado=True, sigrid_estado=None)
    assert exc.value.motivo == motivo_congelacion_linea(
        doc_aprobado=True, sigrid_estado=None)
    assert str(exc.value) == exc.value.motivo


def test_f004_r2_la_guarda_de_documento_lanza_con_el_motivo() -> None:
    with pytest.raises(CongeladoError) as exc:
        exigir_documento_editable(aprobado=False,
                                  estados_lineas=["registrado"])
    assert "sigrid" in exc.value.motivo.lower()


def test_f004_r2_la_guarda_de_documento_no_lanza_si_esta_libre() -> None:
    exigir_documento_editable(aprobado=False, estados_lineas=[None, "error"])
