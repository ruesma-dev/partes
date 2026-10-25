# tests/test_f058_relectura_cabecera.py
"""F-058 · relectura de la cabecera con Gemini (sv2).

Si la lectura primaria trae trabajadores y su cabecera sale vacía (sin obra
ni fecha) o su obra no existe en Sigrid, sv2 relee el mismo documento una
vez con el proveedor de relectura y se queda con la cabecera releída si es
útil (``design.md`` §4).

Primera parte: las reglas puras de
``application/services/relectura_cabecera.py`` (R2–R5, R8). Sin red ni IA:
fixtures inventadas, obra ``"9999"``.
"""
from __future__ import annotations

import pytest
from application.services.relectura_cabecera import (
    MOTIVO_CABECERA_VACIA,
    MOTIVO_OBRA_INEXISTENTE,
    RESULTADO_APLICADA,
    RESULTADO_NO_CASA,
    RESULTADO_VACIA,
    cabecera_vacia,
    clave_obra,
    con_trabajadores,
    es_vacio,
    motivo_relectura,
    resultado_relectura,
)

FILA = {"numero_linea": 1, "nombre": "Fulano de Tal", "dni": "12345678Z",
        "horas_ordinarias": 8.0}


def _data(obra=None, fecha=None, empleados=(FILA,), **cabecera) -> dict:
    return {
        "cabecera": {"obra_numero": obra, "fecha": fecha, **cabecera},
        "firma": {"firmado": True},
        "empleados": list(empleados),
    }


class ExisteDoble:
    """``ExisteObra`` que apunta cada código consultado y da una respuesta fija
    (o por código)."""

    def __init__(self, respuesta: bool | None = True,
                 por_codigo: dict[str, bool | None] | None = None) -> None:
        self.respuesta = respuesta
        self.por_codigo = por_codigo or {}
        self.llamadas: list[str] = []

    def __call__(self, codigo: str) -> bool | None:
        self.llamadas.append(codigo)
        return self.por_codigo.get(codigo, self.respuesta)


# ------------------------------ R5 · vacío -------------------------------- #

@pytest.mark.parametrize("valor", [None, "", " ", "\t \n"])
def test_f058_r5_none_y_solo_espacios_son_vacio(valor) -> None:
    assert es_vacio(valor) is True


@pytest.mark.parametrize("valor", ["9999", " 9 ", "0", 0, False, []])
def test_f058_r5_lo_demas_no_es_vacio(valor) -> None:
    assert es_vacio(valor) is False


# ------------------------------ clave de obra ----------------------------- #

@pytest.mark.parametrize(("codigo", "clave"), [
    ("0672", "672"),
    ("672", "672"),
    ("00672", "672"),
    ("000", "0"),
    ("0", "0"),
    (" a-12 ", "A12"),
    ("Obra Ñ-é", "OBRANE"),
    ("12 34", "1234"),
    ("0A1", "0A1"),          # no es solo de dígitos: los ceros se quedan
    (672, "672"),
    (None, ""),
    ("   ", ""),
    (" - ", ""),
])
def test_f058_r7_clave_de_obra(codigo, clave: str) -> None:
    assert clave_obra(codigo) == clave


# ---------------------------- cabecera vacía ------------------------------ #

def test_f058_r2_cabecera_vacia_sin_obra_ni_fecha() -> None:
    assert cabecera_vacia(_data(obra=None, fecha="  ")) is True


def test_f058_r2_cabecera_vacia_aunque_traiga_otros_campos() -> None:
    assert cabecera_vacia(_data(obra_nombre="Calle Falsa",
                                encargado_nombre="Mengano")) is True


@pytest.mark.parametrize("data", [
    {"firma": {}, "empleados": [FILA]},
    {"cabecera": None, "firma": {}, "empleados": [FILA]},
    {"cabecera": "texto", "firma": {}, "empleados": [FILA]},
])
def test_f058_r2_sin_cabecera_es_cabecera_vacia(data) -> None:
    assert cabecera_vacia(data) is True


@pytest.mark.parametrize(("obra", "fecha"), [
    ("9999", None), (None, "6/4/26"), ("9999", "6/4/26")])
def test_f058_r2_con_obra_o_fecha_no_es_vacia(obra, fecha) -> None:
    assert cabecera_vacia(_data(obra=obra, fecha=fecha)) is False


# --------------------------- con trabajadores ----------------------------- #

def test_f058_r4_con_trabajadores() -> None:
    assert con_trabajadores(_data()) is True
    assert con_trabajadores(_data(empleados=())) is False
    assert con_trabajadores({"cabecera": {}}) is False
    assert con_trabajadores({"empleados": None}) is False
    assert con_trabajadores({"empleados": "fila"}) is False


# --------------------------- R2–R4 · el motivo ---------------------------- #

def test_f058_r2_cabecera_vacia_sin_consultar_sigrid() -> None:
    existe = ExisteDoble()
    assert motivo_relectura(_data(), existe) == MOTIVO_CABECERA_VACIA
    assert existe.llamadas == []


def test_f058_r2_obra_inexistente() -> None:
    existe = ExisteDoble(False)
    data = _data(obra="9999", fecha="6/4/26")
    assert motivo_relectura(data, existe) == MOTIVO_OBRA_INEXISTENTE
    assert existe.llamadas == ["9999"]


def test_f058_r2_obra_inexistente_tambien_sin_fecha() -> None:
    assert motivo_relectura(_data(obra="9999"), ExisteDoble(False)) == (
        MOTIVO_OBRA_INEXISTENTE)


def test_f058_r3_obra_que_existe_no_relee() -> None:
    existe = ExisteDoble(True)
    assert motivo_relectura(_data(obra="9999", fecha="6/4/26"), existe) is None
    assert existe.llamadas == ["9999"]


def test_f058_r3_fecha_sin_obra_no_relee_ni_consulta() -> None:
    existe = ExisteDoble(False)
    assert motivo_relectura(_data(obra="  ", fecha="6/4/26"), existe) is None
    assert existe.llamadas == []


def test_f058_r9_no_se_sabe_no_es_inexistente() -> None:
    assert motivo_relectura(_data(obra="9999"), ExisteDoble(None)) is None


@pytest.mark.parametrize("obra", [None, "9999"])
def test_f058_r4_sin_trabajadores_ni_relee_ni_consulta(obra) -> None:
    existe = ExisteDoble(False)
    assert motivo_relectura(_data(obra=obra, empleados=()), existe) is None
    assert existe.llamadas == []


# ---------------------- R8, R12–R13 · el resultado ------------------------ #

def test_f058_r12_cabecera_vacia_releida_con_obra_es_aplicada() -> None:
    existe = ExisteDoble(False)
    rel = _data(obra="9999")
    assert resultado_relectura(MOTIVO_CABECERA_VACIA, rel, existe, None) == (
        RESULTADO_APLICADA)
    assert existe.llamadas == []          # con cabecera_vacia no se consulta


def test_f058_r12_cabecera_vacia_releida_solo_con_fecha_es_aplicada() -> None:
    rel = _data(fecha="6/4/26")
    assert resultado_relectura(MOTIVO_CABECERA_VACIA, rel, ExisteDoble(), None) == (
        RESULTADO_APLICADA)


def test_f058_r13_cabecera_vacia_releida_vacia_es_vacia() -> None:
    rel = _data(fecha=" ", obra_nombre="Calle Falsa")
    assert resultado_relectura(MOTIVO_CABECERA_VACIA, rel, ExisteDoble(), None) == (
        RESULTADO_VACIA)


def test_f058_r12_obra_inexistente_releida_con_obra_que_existe() -> None:
    existe = ExisteDoble(por_codigo={"8888": True})
    rel = _data(obra="8888")
    assert resultado_relectura(
        MOTIVO_OBRA_INEXISTENTE, rel, existe, "9999") == RESULTADO_APLICADA
    assert existe.llamadas == ["8888"]


@pytest.mark.parametrize("respuesta", [False, None])
def test_f058_r8_obra_inexistente_releida_que_no_existe_o_no_se_sabe(
    respuesta,
) -> None:
    existe = ExisteDoble(respuesta)
    assert resultado_relectura(
        MOTIVO_OBRA_INEXISTENTE, _data(obra="8888"), existe, "9999") == (
        RESULTADO_NO_CASA)
    assert existe.llamadas == ["8888"]


@pytest.mark.parametrize("releida", ["9999", "09999", " 9999 ", "9-999"])
def test_f058_r8_misma_clave_que_la_primaria_no_casa_sin_consultar(
    releida: str,
) -> None:
    existe = ExisteDoble(True)
    assert resultado_relectura(
        MOTIVO_OBRA_INEXISTENTE, _data(obra=releida), existe, "9999") == (
        RESULTADO_NO_CASA)
    assert existe.llamadas == []


@pytest.mark.parametrize("obra", [None, "", "  "])
def test_f058_r16_obra_inexistente_releida_sin_obra_es_vacia(obra) -> None:
    existe = ExisteDoble(True)
    rel = _data(obra=obra, fecha="6/4/26")
    assert resultado_relectura(
        MOTIVO_OBRA_INEXISTENTE, rel, existe, "9999") == RESULTADO_VACIA
    assert existe.llamadas == []
