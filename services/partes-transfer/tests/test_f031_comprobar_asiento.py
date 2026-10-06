# tests/test_f031_comprobar_asiento.py
"""F-031 · R35-R38: herramienta de comprobacion del asiento (SOLO LECTURA).

`comprobar_asiento_analitico.py` lista los partes de una obra y mes con su
estado y, para cada Imputado, compara el Debe de su asiento analitico por
cuenta con las lineas del parte por cuenta (`comparar`, pura). Solo lee
(`POST /api/sql/read`); la salida no lleva nombres, DNIs ni contrapartidas
por persona: cuentas del centro de la obra y el TOTAL del Haber.

Ni una llamada real: lector simulado y `httpx.post` sustituido. Datos
SINTETICOS.
"""
from __future__ import annotations

import httpx
import pytest

import comprobar_asiento_analitico as herramienta
from comprobar_asiento_analitico import (
    CUADRA,
    DESCUADRE,
    SIN_ASIENTO,
    VARIOS_ASIENTOS,
    comparar,
    comprobar,
)
from infrastructure.sigrid import sigrid_write_client as modulo_cliente


# ============================ comparar (pura) ============================ #

def test_f031_r36_cuadra_al_centimo_y_con_tolerancia() -> None:
    assert comparar({"0696.CIMO09": 100.0, "0696.CIMJ09": 50.5},
                    {"0696.CIMO09": 100.0, "0696.CIMJ09": 50.5}, 1) == CUADRA
    assert comparar({"0696.CIMO09": 100.0}, {"0696.CIMO09": 100.01},
                    1) == CUADRA
    assert comparar({"0696.CIMO09": 100.01}, {"0696.CIMO09": 100.0},
                    1) == CUADRA


@pytest.mark.parametrize("lineas, debe", [
    ({"0696.CIMO09": 100.0}, {"0696.CIMO09": 100.02}),     # > 0,01
    ({"0696.CIMO09": 100.0}, {"0696.CIMO09": 99.98}),
    ({"0696.CIMO09": 100.0}, {}),                           # falta en Debe
    ({}, {"0696.CIMO09": 0.5}),                             # sobra en Debe
    ({"0696.CIMO09": 100.0}, {"0696.CIMO12": 100.0}),       # otra cuenta
])
def test_f031_r36_descuadre(lineas, debe) -> None:
    assert comparar(lineas, debe, 1) == DESCUADRE


def test_f031_r36_sin_asiento_y_varios() -> None:
    assert comparar({"0696.CIMO09": 1.0}, {}, 0) == SIN_ASIENTO
    assert comparar({"0696.CIMO09": 1.0}, {"0696.CIMO09": 1.0}, 2) == \
        VARIOS_ASIENTOS
    assert (CUADRA, DESCUADRE, SIN_ASIENTO, VARIOS_ASIENTOS) == \
        ("cuadra", "descuadre", "sin_asiento", "varios_asientos")


def test_f031_r36_sin_lineas_con_cuenta_y_asiento_vacio_cuadra() -> None:
    assert comparar({}, {}, 1) == CUADRA


# ======================= comprobar con lector simulado ======================= #

class Lector:
    """Responde a cada SELECT segun su tabla; apunta lo pedido."""

    def __init__(self, *, obras, partes, lineas, asientos, apa) -> None:
        self.obras, self.partes, self.lineas = obras, partes, lineas
        self.asientos, self.apa = asientos, apa
        self.pedidas: list[tuple[str, list]] = []

    def __call__(self, sql: str, params: list) -> list[dict]:
        self.pedidas.append((sql, list(params)))
        texto = " ".join(sql.split())
        if texto.startswith("SELECT obr.ide"):
            return self.obras
        if "FROM hmores" in texto:
            return self.lineas
        if "FROM hmo " in texto:
            return self.partes
        if "FROM apa" in texto:
            return self.apa.get(params[0], [])
        if "FROM con" in texto:
            return self.asientos.get((params[1], params[2]), [])
        raise AssertionError(f"lectura inesperada: {texto}")


def _lector(**kw) -> Lector:
    base = dict(
        obras=[{"ide": 696, "cod": "0696"}],
        partes=[
            {"ide": 912, "cod": "PT26/00350", "est": 1,
             "res": "Parte Obra 0696", "fec": 20260131},
            {"ide": 905, "cod": "PT26/00004", "est": 10,
             "res": "Parte Obra 0696", "fec": 20260131},
            {"ide": 901, "cod": "PT26/00002", "est": 3,
             "res": "Parte Obra 0696 bis", "fec": 20260131},
        ],
        lineas=[
            {"hmoide": 905, "cuenta": "0696.CIMO09", "n": 300,
             "nuestras": 0, "importe": 12000.0},
            {"hmoide": 905, "cuenta": "0696.CIMJ09", "n": 7, "nuestras": 0,
             "importe": 345.5},
            {"hmoide": 905, "cuenta": None, "n": 1, "nuestras": 0,
             "importe": 10.0},
            {"hmoide": 912, "cuenta": "0696.CIMO09", "n": 2, "nuestras": 2,
             "importe": 160.0},
        ],
        asientos={("Parte Obra 0696", 20260131): [
            {"ide": 7001, "cod": "ANA26/00017"}]},
        apa={7001: [
            {"cuenta": "0696.CIMO09", "deb": 12000.0, "hab": 0.0},
            {"cuenta": "0696.CIMJ09", "deb": 345.5, "hab": 0.0},
            {"cuenta": "0696.CP00", "deb": 0.0, "hab": 12345.5},
        ]},
    )
    base.update(kw)
    return Lector(**base)


def _salida(lector, **kw) -> str:
    return "\n".join(comprobar(lector, empresa=1, obra="0696", ano=2026,
                               mes=1, **kw))


def test_f031_r35_lista_cada_parte_con_estado_lineas_y_nuestras() -> None:
    texto = _salida(_lector())
    assert "Obra 0696 · empresa 1 · 01/2026: 3 parte(s)" in texto
    assert ("PT26/00350 · En registro · 2 linea(s) (2 nuestras) · importe "
            "con cuenta 160.00") in texto
    assert ("PT26/00004 · Imputado · 308 linea(s) (0 nuestras) · importe "
            "con cuenta 12345.50") in texto
    assert ("PT26/00002 · Cerrado · 0 linea(s) (0 nuestras) · importe "
            "con cuenta 0.00") in texto


def test_f031_r36_el_imputado_cuadra_con_su_asiento() -> None:
    texto = _salida(_lector())
    assert ("  asiento ANA26/00017: cuadra (Debe 12345.50 en 2 cuenta(s); "
            "Haber total 12345.50)") in texto
    # Solo los Imputados se comparan.
    assert texto.count("asiento") == 1


def test_f031_r36_descuadre_lista_las_cuentas_que_difieren() -> None:
    apa = {7001: [{"cuenta": "0696.CIMO09", "deb": 11000.0, "hab": 0.0},
                  {"cuenta": "0696.CIMJ09", "deb": 345.5, "hab": 0.0},
                  {"cuenta": "0696.CP00", "deb": 0.0, "hab": 11345.5}]}
    texto = _salida(_lector(apa=apa))
    assert "asiento ANA26/00017: descuadre" in texto
    assert ("    0696.CIMO09: lineas 12000.00 · debe 11000.00 · diferencia "
            "1000.00") in texto
    assert "0696.CIMJ09: lineas" not in texto


def test_f031_r36_sin_asiento_y_varios_asientos() -> None:
    texto = _salida(_lector(asientos={}))
    assert "  sin_asiento (ningun asiento tipo 32 con ese resumen y fecha)" \
        in texto
    dos = {("Parte Obra 0696", 20260131): [
        {"ide": 7001, "cod": "ANA26/00017"},
        {"ide": 7002, "cod": "ANA26/00018"}]}
    texto = _salida(_lector(asientos=dos))
    assert "  varios_asientos: ANA26/00017, ANA26/00018" in texto


def test_f031_r36_lecturas_y_parametros() -> None:
    lector = _lector()
    _salida(lector)
    (obra_sql, obra_p), (partes_sql, partes_p), (lin_sql, lin_p), \
        (asi_sql, asi_p), (apa_sql, apa_p) = lector.pedidas
    assert obra_p == ["0696", 1]
    assert partes_p == [696, 2026, 1, 35, 1]
    assert "ORDER BY hmo.ide DESC" in partes_sql
    assert lin_p == ["partes:%", 912, 905, 901]
    assert "GROUP BY h.hmoide, c.cod" in " ".join(lin_sql.split())
    assert asi_p == [1, "Parte Obra 0696", 20260131, 32]
    assert apa_p == [7001]
    for sql, _ in lector.pedidas:
        assert " ".join(sql.split()).upper().startswith("SELECT ")


def test_f031_r35_obra_inexistente_o_sin_partes() -> None:
    assert _salida(_lector(obras=[])) == \
        "La obra 0696 no existe en la empresa 1"
    lector = _lector(partes=[])
    assert _salida(lector) == "Obra 0696 · empresa 1 · 01/2026: 0 parte(s)"
    assert len(lector.pedidas) == 2              # no lee lineas


def test_f031_r35_estado_desconocido_y_ajustes() -> None:
    partes = [{"ide": 905, "cod": "PT26/00004", "est": 4,
               "res": "Parte Obra 0696", "fec": 20260131}]
    texto = _salida(_lector(partes=partes), est_imputado=4)
    assert "PT26/00004 · Imputado" in texto and "asiento ANA26/00017" in texto
    texto = _salida(_lector(partes=partes))
    assert "PT26/00004 · estado 4" in texto and "asiento" not in texto


def test_f031_r37_sin_contrapartidas_ni_personas() -> None:
    texto = _salida(_lector())
    assert "0696.CP00" not in texto           # cuenta del Haber
    assert "Persona" not in texto
    assert "Haber total 12345.50" in texto


# ======================= R38 · main solo lee ======================= #

class SettingsFake:
    sigrid_api_base_url = "http://sigrid.invalid"
    sigrid_api_function_key = "clave-de-test"
    sigrid_api_database = "bd"
    sigrid_api_timeout_s = 5.0
    tip_parte_trabajo = 35
    est_parte_activo = 1
    est_parte_cerrado = 3
    est_parte_imputado = 10


def test_f031_r38_main_solo_usa_sql_read(monkeypatch, capsys) -> None:
    urls: list[str] = []

    def post(url, headers=None, timeout=None, json=None):
        urls.append(url)
        sql = " ".join(json["sql"].split())
        cols, filas = ["ide", "cod"], []
        if sql.startswith("SELECT obr.ide"):
            filas = [[696, "0696"]]
        elif "FROM hmores" in sql:
            cols = ["hmoide", "cuenta", "n", "nuestras", "importe"]
            filas = [[912, "0696.CIMO09", 2, 2, 160.0]]
        elif "FROM hmo " in sql:
            cols = ["ide", "cod", "est", "res", "fec"]
            filas = [[912, "PT26/00350", 1, "Parte Obra 0696", 20260131]]
        return httpx.Response(200, json={"ok": True, "columns": cols,
                                         "rows": filas, "truncated": False})

    monkeypatch.setattr(modulo_cliente.httpx, "post", post)
    codigo = herramienta.main(["--empresa", "1", "--obra", "0696", "--ano",
                               "2026", "--mes", "1"], settings=SettingsFake())
    assert codigo == 0
    assert urls and all(u == "http://sigrid.invalid/api/sql/read"
                        for u in urls)
    assert "PT26/00350 · En registro" in capsys.readouterr().out


def test_f031_r38_truncado_es_error(monkeypatch) -> None:
    def post(url, headers=None, timeout=None, json=None):
        return httpx.Response(200, json={"ok": True, "columns": ["ide"],
                                         "rows": [], "truncated": True})

    monkeypatch.setattr(modulo_cliente.httpx, "post", post)
    with pytest.raises(RuntimeError, match="truncada"):
        herramienta.main(["--empresa", "1", "--obra", "0696", "--ano",
                          "2026", "--mes", "1"], settings=SettingsFake())


def test_f031_r38_el_script_no_escribe() -> None:
    fuente = herramienta.__file__
    texto = open(fuente, encoding="utf-8").read()
    assert "/api/sql/write" not in texto
    assert ".escribir(" not in texto
    for verbo in ("INSERT ", "UPDATE ", "DELETE "):
        assert verbo not in texto.upper().replace("SOLO LECTURA", "")
