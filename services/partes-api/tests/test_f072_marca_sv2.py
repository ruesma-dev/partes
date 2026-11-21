# tests/test_f072_marca_sv2.py
"""F-072 · sv2 con la marca de una obra agrupada (R12, R13, R43; DA3 = a).

- R13: si `leer_forma` (gemelo) reconoce una marca en el «Nº OBRA» leído,
  `ComprobadorObra` responde «no se sabe» sin llamar a sigrid-api, y la
  página no se relee por `obra_inexistente`.
- R12: el prompt pide copiar el «Nº OBRA» tal cual, con la marca, su posición
  y su separador, sin normalizar.
- R43: la marca solo sale de `cabecera.obra_numero`; una incidencia `V` de una
  fila de personal no interviene.

Sin red ni modelo de IA: dobles del puerto y de los clientes de IA de F-058.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pytest

from application.services.obra_sigrid import ComprobadorObra
from application.services.obras_agrupadas import Marcas
from application.services.relectura_cabecera import motivo_relectura
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository
from tests.f059_sdk_falsos import instalar_si_faltan
from tests.test_f058_relectura_cabecera import (
    PuertoObra,
    _correr,
    _montar,
    _parte,
)

instalar_si_faltan()

RUTA_PROMPTS = Path(__file__).resolve().parents[1] / "config" / "prompts.yaml"
MARCAS = Marcas(postventa=("POSTV2", "POSTVENTA", "POSTV", "POST"),
                var=("VAR", "V"))


def _comprobador(puerto, marcas=MARCAS):
    return ComprobadorObra(client=puerto, timeout_s=5.0, marcas=marcas)


# --------------------------------- R13 ---------------------------------- #

@pytest.mark.parametrize("leido", ["V-29", "post 578", "VAR", "POSTV2",
                                   "29 V", "Postventá 578"])
def test_f072_r13_con_marca_no_se_sabe_sin_llamar(leido, caplog):
    puerto = PuertoObra()
    with caplog.at_level(logging.INFO, logger="application.services.obra_sigrid"):
        consulta = _comprobador(puerto).consultar(leido, document_id="d1")
    assert consulta.existe is None and consulta.error_tipo is None
    assert consulta.ms == 0
    assert puerto.llamadas == []
    mensajes = [r.getMessage() for r in caplog.records]
    assert any("resultado=marca" in m and "document_id=d1" in m
               for m in mensajes), mensajes
    assert not any(leido in m for m in mensajes), "el código no va al log"


@pytest.mark.parametrize("leido", ["9999", "VALENCIA 3", "V", "POSTE"])
def test_f072_r13_sin_marca_consulta_como_siempre(leido):
    puerto = PuertoObra()
    consulta = _comprobador(puerto).consultar(leido, document_id="d")
    assert consulta.existe is False
    assert len(puerto.llamadas) == 1


def test_f072_r13_sin_marcas_configuradas_consulta_como_siempre():
    puerto = PuertoObra()
    _comprobador(puerto, Marcas(postventa=(), var=())).consultar(
        "V-29", document_id="d")
    sin_param = ComprobadorObra(client=puerto)
    sin_param.consultar("VAR 29", document_id="d")
    assert len(puerto.llamadas) == 2


def test_f072_r13_motivo_relectura_no_da_obra_inexistente_con_marca():
    puerto = PuertoObra()
    comp = _comprobador(puerto)
    data = {"cabecera": {"obra_numero": "V-29", "fecha": "6/4/26"},
            "firma": {}, "empleados": [{"nombre": "Fulano", "horas_ordinarias": 8}]}
    assert motivo_relectura(
        data, lambda c: comp.consultar(c, document_id="d").existe) is None
    assert puerto.llamadas == []


def test_f072_r13_el_pipeline_no_relee_una_pagina_con_marca():
    m = _montar(_parte(obra="V-29", fecha="6/4/26"))
    m.pipeline._obras = _comprobador(m.puerto)
    sobre = _correr(m)
    assert m.secundario.llamadas == []
    assert m.puerto.llamadas == []
    assert sobre["data"]["cabecera"]["obra_numero"] == "V-29"


def test_f072_r13_sin_marca_el_pipeline_sigue_releyendo():
    """Control: la misma página con una obra que no existe sí se relee."""
    m = _montar(_parte(obra="09999", fecha="6/4/26"))
    m.pipeline._obras = _comprobador(m.puerto)
    _correr(m)
    assert len(m.secundario.llamadas) == 1


# --------------------------------- R43 ---------------------------------- #

def test_f072_r43_la_incidencia_v_no_es_marca():
    """Una fila con incidencia `V` (vacaciones) y obra normal: se consulta la
    obra como siempre y `obra_numero` no cambia."""
    parte = _parte(obra="0672", fecha="6/4/26")
    parte["empleados"].append({"numero_linea": 2, "nombre": "Mengano",
                               "dni": "00000000T",
                               "incidencia": {"codigo": "V", "texto_leido": "V"}})
    m = _montar(parte, puerto=PuertoObra(existentes={"672"}))
    m.pipeline._obras = _comprobador(m.puerto)
    sobre = _correr(m)
    assert m.puerto.llamadas == ["672"]
    assert sobre["data"]["cabecera"]["obra_numero"] == "0672"


# --------------------------------- R12 ---------------------------------- #

@pytest.fixture(scope="module")
def vineta_obra() -> str:
    prompt = YamlPromptRepository(RUTA_PROMPTS).get("parte_trabajo_es")
    resto = prompt.task.split("- cabecera.obra_numero:", 1)[1]
    return " ".join(resto.split("- cabecera.obra_nombre:", 1)[0].split()).lower()


@pytest.mark.parametrize("frase", [
    "tal cual", "marca", "posicion", "separador", '"v-29"', '"post 578"',
    "no expandas", '"var"', '"postventa"', "no quites", "no añadas ceros",
])
def test_f072_r12_el_prompt_pide_el_n_obra_tal_cual(vineta_obra, frase):
    assert frase in vineta_obra, vineta_obra


def test_f072_r43_el_prompt_separa_la_incidencia_de_la_obra(vineta_obra):
    assert "empleados[].incidencia" in vineta_obra
    assert "vacaciones" in vineta_obra


# ------------------------------- cableado -------------------------------- #

def test_f072_r13_build_app_pasa_las_marcas_de_la_configuracion(monkeypatch):
    """`build_app` da a `ComprobadorObra` las marcas de los ajustes (R1)."""
    from interface_adapters.api.app import build_app
    from tests.test_f058_settings_wiring import SIGRID, VARIABLES, _settings

    for nombre in VARIABLES + ("POSTVENTA_OBRA_COD", "POSTVENTA_ALIAS",
                               "VAR_OBRA_COD", "VAR_ALIAS", "VAR_PARTIDA_DESDE"):
        monkeypatch.delenv(nombre, raising=False)
    st = _settings(POSTVENTA_OBRA_COD="POSTV2", POSTVENTA_ALIAS="POST",
                   VAR_OBRA_COD="VAR", VAR_ALIAS="V", VAR_PARTIDA_DESDE="29",
                   **SIGRID)
    obras = build_app(st).state.pipeline._obras
    assert obras._marcas == Marcas(postventa=("POSTV2", "POST"),
                                   var=("VAR", "V"))
