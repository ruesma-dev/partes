# tests/test_f060_racha_ciz.py
"""F-060 · Regla pura del CIZ movil (R14-R19), `application/services/
racha_ciz.py`.

`decidir_fin` recibe las lineas de Sigrid leidas por las synckeys de la
racha (`racha_registro_ids` de sv4) y decide que hacer con el `fin` del
dia D:

  - filtra recurso, codigo `CIZ`, `can` nulo o 0 y, en modo pruebas, la
    marca en `tex` (R13, R19);
  - alguna posterior a D => `intermedio`, nombrando el dia del CIZ (R14);
  - la anterior de mayor (fecha, ide): enlazada => `enlazada` (R18), su
    parte no En registro => `parte_cerrado` (R17), si no => `mover` con
    los duplicados (R15);
  - nada => `crear` (R16).

Datos SINTETICOS.
"""
from __future__ import annotations

import inspect

import pytest
from application.services import racha_ciz
from application.services.pisado import MOTIVO_LINEA_ENLAZADA
from application.services.racha_ciz import (
    LIMITE_MOTIVO,
    MOTIVO_CIZ_EN_PARTE_CERRADO,
    DecisionFin,
    decidir_fin,
    motivo_ciz_en_parte_cerrado,
    motivo_intermedio_ciz,
    registro_de_synckey,
)
from application.services.reglas_registro import MOTIVO_INTERMEDIO
from domain.models.registro_models import LineaSigrid, ParteSigrid

RES, D, H_CIZ, H_CIV = 77, 20261004, 40, 30
ABIERTO, CERRADO = 900, 800
PARTES = {ABIERTO: ParteSigrid(ide=ABIERTO, cod="PT26/00010", est=1),
          CERRADO: ParteSigrid(ide=CERRADO, cod="PT26/00009", est=3)}


def _ls(ide: int, fec: int, *, reside: int = RES, hora: str | None = "CIZ",
        can: float | None = 0.0, hmoide: int = ABIERTO, enlazada=False,
        tex: str | None = None, sk: int | None = None) -> LineaSigrid:
    return LineaSigrid(
        ide=ide, reside=reside, fecha_int=fec,
        horide=H_CIZ if hora == "CIZ" else H_CIV, hora_codigo=hora,
        can=can, tot=0.0, synckey=f"partes:{sk or ide}", nuestra=True,
        hmoide=hmoide, enlazada=enlazada, tex=tex, pos=64)


def _nombre(est: int | None) -> str:
    return {3: "Cerrado", 10: "Imputado"}.get(est, f"estado {est}")


def _decidir(candidatas, *, partes=None, marca=None) -> DecisionFin:
    return decidir_fin(D, RES, candidatas,
                       partes=PARTES if partes is None else partes,
                       est_registro=1, marca_pruebas=marca,
                       nombre_estado=_nombre)


# ------------------------------- R16 ------------------------------- #

def test_f060_r16_sin_candidatas_crea() -> None:
    d = _decidir([])
    assert d == DecisionFin(tipo="crear")
    assert d.linea is None and d.motivo is None and d.duplicados == 0


@pytest.mark.parametrize("ajena", [
    _ls(1, 20261003, reside=78),          # otro recurso
    _ls(2, 20261003, hora="CIV"),         # el inicio, no el fin
    _ls(3, 20261003, hora=None),          # sin codigo de hora
    _ls(4, 20261003, can=8.0),            # con horas
    _ls(5, 20261003, can=-0.5),           # con horas negativas
])
def test_f060_r16_las_que_no_son_ciz_del_recurso_no_cuentan(ajena) -> None:
    assert _decidir([ajena]).tipo == "crear"
    # Tampoco cuentan como posteriores: no hacen `intermedio`.
    posterior = LineaSigrid(**{**ajena.__dict__, "fecha_int": 20261005})
    assert _decidir([posterior]).tipo == "crear"


def test_f060_r16_un_ciz_del_mismo_dia_no_es_anterior_ni_posterior() -> None:
    """El paso 7 lo trata (`incidencia_en_sigrid`): aqui no se mueve."""
    assert _decidir([_ls(1, D)]).tipo == "crear"


# ------------------------------- R15 ------------------------------- #

@pytest.mark.parametrize("can", [0.0, None, 0])
def test_f060_r15_mueve_la_anterior_con_can_nulo_o_cero(can) -> None:
    linea = _ls(7001, 20261003, can=can)
    d = _decidir([linea])
    assert d.tipo == "mover" and d.linea is linea
    assert d.duplicados == 0 and d.motivo is None


def test_f060_r15_codigo_ciz_sin_espacios_ni_mayusculas() -> None:
    assert _decidir([_ls(1, 20261003, hora=" ciz ")]).tipo == "mover"


def test_f060_r15_la_de_mayor_fecha_y_los_duplicados() -> None:
    a = _ls(10, 20261001)
    b = _ls(5, 20261003)
    c = _ls(9, 20261002)
    d = _decidir([a, b, c])
    assert d.tipo == "mover" and d.linea is b
    assert d.duplicados == 2


def test_f060_r15_empate_de_fecha_gana_el_mayor_ide() -> None:
    a = _ls(10, 20261003)
    b = _ls(11, 20261003)
    assert _decidir([b, a]).linea is b
    assert _decidir([a, b]).linea is b
    assert _decidir([a, b]).duplicados == 1


def test_f060_r15_los_duplicados_solo_cuentan_las_que_son_ciz() -> None:
    d = _decidir([_ls(1, 20261003), _ls(2, 20261002, hora="CIV"),
                  _ls(3, 20261001, reside=78)])
    assert d.tipo == "mover" and d.duplicados == 0


# ------------------------------- R14 ------------------------------- #

def test_f060_r14_una_posterior_hace_intermedio_y_nombra_el_dia() -> None:
    d = _decidir([_ls(7001, 20261006)])
    assert d.tipo == "intermedio" and d.linea is None
    assert d.motivo == motivo_intermedio_ciz(7001, 20261006)
    assert d.motivo.startswith(MOTIVO_INTERMEDIO)
    assert "2026-10-06" in d.motivo and "linea 7001" in d.motivo


def test_f060_r14_posterior_manda_sobre_anterior() -> None:
    d = _decidir([_ls(1, 20261002), _ls(2, 20261005)])
    assert d.tipo == "intermedio"
    assert "2026-10-05" in d.motivo


def test_f060_r14_varias_posteriores_nombra_la_ultima() -> None:
    d = _decidir([_ls(3, 20261006), _ls(4, 20261009), _ls(2, 20261005)])
    assert "2026-10-09" in d.motivo and "linea 4" in d.motivo
    d = _decidir([_ls(5, 20261009), _ls(4, 20261009)])
    assert "linea 5" in d.motivo


def test_f060_r14_posterior_ni_cerrada_ni_enlazada_importa() -> None:
    """R14 va antes que R17 y R18: lo posterior no se mira mas."""
    d = _decidir([_ls(1, 20261005, hmoide=CERRADO, enlazada=True)])
    assert d.tipo == "intermedio"


# ------------------------------- R17 ------------------------------- #

def test_f060_r17_parte_cerrado_no_se_mueve_ni_se_crea() -> None:
    d = _decidir([_ls(7001, 20261003, hmoide=CERRADO)])
    assert d.tipo == "parte_cerrado"
    assert d.motivo == motivo_ciz_en_parte_cerrado(7001, "PT26/00009",
                                                   "Cerrado")
    assert d.motivo.startswith(MOTIVO_CIZ_EN_PARTE_CERRADO + ":")
    assert "PT26/00009" in d.motivo and "Cerrado" in d.motivo


def test_f060_r17_parte_que_no_se_leyo_cuenta_como_cerrado() -> None:
    d = _decidir([_ls(7001, 20261003, hmoide=555)])
    assert d.tipo == "parte_cerrado"
    assert "parte ?" in d.motivo and "estado None" in d.motivo


def test_f060_r17_solo_mira_la_elegida() -> None:
    """La elegida esta en un parte abierto: un duplicado en uno cerrado
    no impide moverla."""
    d = _decidir([_ls(1, 20261003), _ls(2, 20261001, hmoide=CERRADO)])
    assert d.tipo == "mover" and d.linea.ide == 1 and d.duplicados == 1
    d = _decidir([_ls(1, 20261003, hmoide=CERRADO), _ls(2, 20261001)])
    assert d.tipo == "parte_cerrado"


# ------------------------------- R18 ------------------------------- #

def test_f060_r18_enlazada_no_se_mueve() -> None:
    d = _decidir([_ls(7001, 20261003, enlazada=True)])
    assert d.tipo == "enlazada"
    assert d.motivo.startswith(MOTIVO_LINEA_ENLAZADA + ":")
    assert "linea 7001" in d.motivo and "PT26/00010" in d.motivo


def test_f060_r18_enlazada_manda_sobre_parte_cerrado() -> None:
    d = _decidir([_ls(7001, 20261003, enlazada=True, hmoide=CERRADO)])
    assert d.tipo == "enlazada"
    assert "PT26/00009" in d.motivo


def test_f060_r18_enlazada_en_parte_no_leido() -> None:
    d = _decidir([_ls(7001, 20261003, enlazada=True, hmoide=555)])
    assert d.tipo == "enlazada" and "parte ?" in d.motivo


# ------------------------------- R19 ------------------------------- #

def test_f060_r19_en_pruebas_sin_marca_no_cuenta() -> None:
    sin = _ls(1, 20261003, tex=None)
    otra = _ls(2, 20261003, tex="manual")
    assert _decidir([sin, otra], marca="PRUEBA-IA").tipo == "crear"


def test_f060_r19_en_pruebas_con_marca_se_mueve() -> None:
    con = _ls(1, 20261002, tex="PRUEBA-IA")
    sin = _ls(2, 20261003, tex=None)
    d = _decidir([con, sin], marca="PRUEBA-IA")
    assert d.tipo == "mover" and d.linea is con and d.duplicados == 0
    # La marca puede ir dentro de un texto mas largo.
    larga = _ls(3, 20261002, tex="x PRUEBA-IA y")
    assert _decidir([larga], marca="PRUEBA-IA").linea is larga


def test_f060_r19_en_pruebas_una_posterior_sin_marca_no_cuenta() -> None:
    d = _decidir([_ls(1, 20261009, tex="manual"),
                  _ls(2, 20261002, tex="PRUEBA-IA")], marca="PRUEBA-IA")
    assert d.tipo == "mover" and d.linea.ide == 2


def test_f060_r19_fuera_de_pruebas_la_marca_no_se_mira() -> None:
    assert _decidir([_ls(1, 20261002, tex=None)], marca=None).tipo == "mover"
    assert _decidir([_ls(1, 20261002, tex=None)], marca="").tipo == "mover"


# ------------------------------ motivos ----------------------------- #

def test_f060_motivos_sin_tildes_y_acotados() -> None:
    largo = "PT26/" + "9" * 400
    for texto in (motivo_intermedio_ciz(7001, 20261006),
                  motivo_ciz_en_parte_cerrado(7001, largo, "Imputado"),
                  motivo_ciz_en_parte_cerrado(7001, None, "Cerrado")):
        assert texto.isascii()
        assert len(texto) <= LIMITE_MOTIVO
    assert len(motivo_ciz_en_parte_cerrado(7001, largo, "x")) == LIMITE_MOTIVO
    assert motivo_intermedio_ciz(7001, 20261006) == (
        "dia intermedio de la incidencia: solo se registran el inicio y el "
        "fin (el fin, CIZ linea 7001, ya esta el dia 2026-10-06)")
    assert motivo_ciz_en_parte_cerrado(7001, "PT26/00009", "Cerrado") == (
        "ciz_en_parte_cerrado: el fin de la incidencia (CIZ, linea 7001) "
        "esta en el parte PT26/00009 (Cerrado), que ya no esta En registro; "
        "no se mueve ni se escribe otro. Corrigelo en Sigrid")
    assert motivo_ciz_en_parte_cerrado(1, None, "Cerrado").count("parte ?") == 1


def test_f060_regla_pura_sin_lecturas_ni_escrituras() -> None:
    fuente = inspect.getsource(racha_ciz)
    for prohibido in ("httpx", "_read(", "escribir(", "DELETE", "import os"):
        assert prohibido not in fuente


@pytest.mark.parametrize("sk,esperado", [
    ("partes:3", 3), (" partes:120 ", 120), ("partes:x", None),
    ("porcentajes:3", None), ("", None), (None, None), ("partes:", None),
])
def test_f060_r23_registro_de_synckey(sk, esperado) -> None:
    assert registro_de_synckey(sk) == esperado


# ============ Mutacion (rigor critico): huecos que cerro la campaña ============ #

def test_f060_decision_inmutable() -> None:
    """`DecisionFin` es un valor: el pipeline la lee, no la cambia."""
    import dataclasses
    d = _decidir([_ls(1, 20261003)])
    with pytest.raises(dataclasses.FrozenInstanceError):
        d.tipo = "crear"  # type: ignore[misc]


def test_f060_motivo_recortado_a_255_exactos() -> None:
    """`parte_registro.sigrid_motivo` de sv4 es de 255: el motivo largo se
    corta justo ahi, ni un caracter mas."""
    largo = "PT26/" + "9" * 400
    texto = motivo_ciz_en_parte_cerrado(7001, largo, "Cerrado")
    assert len(texto) == 255
    assert texto == ("ciz_en_parte_cerrado: el fin de la incidencia (CIZ, "
                     f"linea 7001) esta en el parte {largo}")[:255]


def test_f060_r17_ciz_sin_parte_no_se_cruza_con_otro_parte() -> None:
    """Un CIZ sin `hmoide` no tiene parte leido: cuenta como cerrado
    (R17) aunque exista un parte En registro con ide 1."""
    partes = {1: ParteSigrid(ide=1, cod="PT26/00001", est=1)}
    d = _decidir([_ls(1, 20261003, hmoide=None)], partes=partes)
    assert d.tipo == "parte_cerrado" and d.linea is None
    assert "parte ?" in d.motivo
