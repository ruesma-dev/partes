# tests/test_f085_inicio_movido.py
"""F-085 · parte B: el inicio de la racha se recoloca en Sigrid (sv5).

Hasta F-085, aprobar el día ANTERIOR al inicio ya registrado de una racha
escribía otro CI* y dejaba dos en la racha (F-060 DA7: solo un aviso).
Desde F-085, con `MOVER_INICIO` encendido, el `inicio` del día D busca en
las candidatas que ya lee el paso 6 bis el **inicio previo** (la primera
línea de la racha posterior a D, del mismo código, con synckey
`partes:<i>` y un CIZ de la racha en su día o después, D9) y lo **mueve**
a D con el `UPDATE` de F-060 en vez del `INSERT`.

  - Puro (`-k puro`): `inicio_previo`, `decidir_inicio` y sus motivos.
  - Pipeline con `SigridFake` (`-k pipeline`): R21-R27, R30, R31 y R32
    (los casos de F-083 R13-R17 y de F-062 con el interruptor encendido).

Sin red ni BBDD. Datos SINTÉTICOS (recurso 501, obra 0100, octubre 2026).
"""
from __future__ import annotations

import inspect
import logging
import unicodedata

import pytest
from application.pipelines import registro_pipeline
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services import racha_ciz
from application.services.pisado import motivo_linea_enlazada
from application.services.racha_ciz import (
    CREAR,
    ENLAZADA,
    LIMITE_MOTIVO,
    MOTIVO_INICIO_EN_PARTE_CERRADO,
    MOVER,
    PARTE_CERRADO,
    DecisionInicio,
    decidir_inicio,
    inicio_previo,
    motivo_inicio_en_parte_cerrado,
)
from domain.models.registro_models import LineaSigrid, ParteSigrid
from tests.dobles import SettingsFake
from tests.test_f062_ciz_mismo_dia import (
    H_CIV,
    H_CIZ,
    HMO_OCT,
    _acc,
    _cli,
    _espiar,
    _fila,
    _por_sk,
)
from tests.test_f062_ciz_mismo_dia import _fin as _linea_fin
from tests.test_f062_ciz_mismo_dia import _inicio as _linea_inicio
from tests.test_f062_ciz_mismo_dia import _obra
from tests.test_f060_pipeline_mover import _parte

RES = 501
D17, D18, D19, D25 = 20261017, 20261018, 20261019, 20261025
ABIERTO, CERRADO = 901, 905
PARTES = {ABIERTO: ParteSigrid(ide=ABIERTO, cod="PT26/00010", est=1),
          CERRADO: ParteSigrid(ide=CERRADO, cod="PT26/00008", est=3)}
MARCA = "PRUEBA-IA"


def _ls(ide: int, fec: int, *, rid: int | None = None, hora: str = "CIV",
        sk: str | None = None, reside: int = RES, can: float = 0.0,
        hmoide: int = ABIERTO, enlazada: bool = False,
        tex: str | None = None) -> LineaSigrid:
    return LineaSigrid(
        ide=ide, reside=reside, fecha_int=fec,
        horide=H_CIZ if hora == "CIZ" else H_CIV, hora_codigo=hora, can=can,
        tot=0.0, synckey=sk or f"partes:{rid if rid is not None else ide}",
        nuestra=True, hmoide=hmoide, enlazada=enlazada, tex=tex, pos=64)


def _nombre(est: int | None) -> str:
    return {3: "Cerrado"}.get(est, f"estado {est}")


def _decidir(candidatas, *, codigo="CIV", marca=None,
             fecha=D18) -> DecisionInicio:
    return decidir_inicio(fecha, RES, codigo, candidatas, partes=PARTES,
                          est_registro=1, marca_pruebas=marca,
                          nombre_estado=_nombre)


CIV19 = _ls(7019, D19, rid=19)
CIZ25 = _ls(7025, D25, rid=25, hora="CIZ")


# =============================== Puro =============================== #

def test_f085_puro_r21_inicio_previo_del_caso() -> None:
    previo, no_movido = inicio_previo(D18, RES, "CIV", [CIZ25, CIV19], None)
    assert previo is CIV19 and no_movido is None


def test_f085_puro_r21_mover() -> None:
    d = _decidir([CIV19, CIZ25])
    assert d == DecisionInicio(tipo=MOVER, linea=CIV19)


@pytest.mark.parametrize("codigo", ["civ", " CIV "])
def test_f085_puro_r21_codigo_normalizado(codigo) -> None:
    assert _decidir([CIV19, CIZ25], codigo=codigo).tipo == MOVER


def test_f085_puro_r21_ciz_el_mismo_dia_del_previo_cuenta() -> None:
    """D9: un CIZ de la racha en el día del inicio previo (su hermano)."""
    hermano = _ls(7020, D19, sk="partes:19:ciz", hora="CIZ")
    assert _decidir([CIV19, hermano]).tipo == MOVER


def test_f085_puro_r21_la_primera_por_fecha_e_ide() -> None:
    a = _ls(7030, D19 + 1, rid=20)
    b = _ls(7029, D19, rid=21)
    c = _ls(7031, D19, rid=22)
    d = _decidir([a, c, b, CIZ25])
    assert d.linea is b


@pytest.mark.parametrize("candidatas, no_movido", [
    ([], None),                                       # nada
    ([CIZ25], None),                                  # caso (b)
    ([CIV19], CIV19),                                 # sin CIZ detras
    ([CIV19, _ls(7010, D18 - 1, hora="CIZ")], CIV19),  # CIZ anterior
    ([_ls(7019, D19, rid=19, hora="CIA"), CIZ25], None),    # otro codigo
    ([_ls(7019, D19, sk="partes:19:ciz"), CIZ25],           # synckey :ciz
     _ls(7019, D19, sk="partes:19:ciz")),
    ([_ls(7019, D19, rid=19, hora="CIZ"),                    # primera CIZ
      _ls(7022, D19 + 3, rid=22), CIZ25],
     _ls(7022, D19 + 3, rid=22)),
])
def test_f085_puro_r23_no_es_inicio_previo(candidatas, no_movido) -> None:
    d = _decidir(candidatas)
    assert (d.tipo, d.linea, d.motivo) == (CREAR, None, None)
    assert d.no_movido == no_movido


@pytest.mark.parametrize("descarte", [
    _ls(7019, D19, rid=19, reside=RES + 1),      # otro recurso
    _ls(7019, D19, rid=19, can=8.0),             # con horas
    _ls(7019, D18, rid=19),                      # el mismo dia D
    _ls(7019, D17, rid=19),                      # anterior
])
def test_f085_puro_r21_lo_que_no_es_de_la_racha_no_cuenta(descarte) -> None:
    d = _decidir([descarte, CIZ25])
    assert d.tipo == CREAR and d.no_movido is None


def test_f085_puro_r21_en_pruebas_sin_marca_no_cuenta() -> None:
    con = _ls(7019, D19, rid=19, tex=MARCA)
    ciz = _ls(7025, D25, rid=25, hora="CIZ", tex=MARCA)
    assert _decidir([CIV19, ciz], marca=MARCA).tipo == CREAR
    assert _decidir([con, CIZ25], marca=MARCA).tipo == CREAR
    assert _decidir([con, ciz], marca=MARCA).tipo == MOVER


def test_f085_puro_r22_enlazada() -> None:
    linea = _ls(7019, D19, rid=19, enlazada=True)
    d = _decidir([linea, CIZ25])
    assert (d.tipo, d.linea) == (ENLAZADA, None)
    assert d.motivo == motivo_linea_enlazada([7019], "PT26/00010")


@pytest.mark.parametrize("hmoide, estado", [(CERRADO, "Cerrado"),
                                            (555, "estado None")])
def test_f085_puro_r22_parte_cerrado(hmoide, estado) -> None:
    linea = _ls(7019, D19, rid=19, hmoide=hmoide)
    d = _decidir([linea, CIZ25])
    assert (d.tipo, d.linea) == (PARTE_CERRADO, None)
    cod = "PT26/00008" if hmoide == CERRADO else None
    assert d.motivo == motivo_inicio_en_parte_cerrado(7019, cod, estado)


def test_f085_puro_r22_motivo_exacto_tildes_y_largo() -> None:
    assert MOTIVO_INICIO_EN_PARTE_CERRADO == "inicio_en_parte_cerrado"
    texto = motivo_inicio_en_parte_cerrado(416122, "PT26/00137", "Cerrado")
    assert texto == (
        "inicio_en_parte_cerrado: el inicio de la incidencia (linea 416122) "
        "esta en el parte PT26/00137 (Cerrado), que ya no esta En registro; "
        "no se mueve ni se escribe otro. Corrigelo en Sigrid")
    largo = motivo_inicio_en_parte_cerrado(1, "X" * 400, "Cerrado")
    for t in (texto, largo):
        assert t.isascii() and unicodedata.normalize("NFKD", t) == t
        assert len(t) <= LIMITE_MOTIVO
    assert "?" in motivo_inicio_en_parte_cerrado(1, None, "Cerrado")


def test_f085_puro_r21_acepta_un_iterador() -> None:
    assert _decidir(iter([CIV19, CIZ25])).tipo == MOVER


def test_f085_puro_r27_regla_pura_sin_delete() -> None:
    fuente = inspect.getsource(racha_ciz)
    for prohibido in ("httpx", "_read(", "escribir(", "DELETE", "import os",
                      "lineas_de_racha", "estados_de_partes"):
        assert prohibido not in fuente
    assert "DELETE" not in inspect.getsource(registro_pipeline).upper()


# ========================= Pipeline (R21-R32) ========================= #

def _st(*, inicio=True, mover=True, pruebas=False, sin_ajuste=False):
    st = SettingsFake(obra_pruebas_forzar=pruebas)
    st.mover_ciz = mover
    if not sin_ajuste:
        st.mover_inicio = inicio
    return st


def _pipe(cli, **kw) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=_st(**kw))


def _ejecutar(cli, lineas, **kw):
    return _pipe(cli, **kw).ejecutar(obra=_obra(), lineas=lineas)


RACHA_18 = [19, 20, 21, 22, 23, 24, 25]


def _caso(*, con_19=True, **kw_19):
    """Caso de origen (design §5.4): CIV el 19 y CIZ el 25."""
    filas = [_fila(7025, fec=D25, rid=25, horide=H_CIZ)]
    if con_19:
        filas.insert(0, _fila(7019, fec=D19, rid=19, horide=H_CIV, **kw_19))
    return _cli(*filas)


def _ops(enviadas) -> list[str]:
    return [s["op"] for s in enviadas]


# ------------------------------- R30 -------------------------------- #

def test_f085_pipeline_r30a_mueve_el_inicio(caplog) -> None:
    cli = _caso()
    enviadas = _espiar(cli)
    with caplog.at_level(logging.INFO):
        r = _ejecutar(cli, [_linea_inicio(18, D18, RACHA_18)])
    assert _ops(enviadas) == ["mover"]
    (s,) = enviadas
    assert (s["ide"], s["fec_antes"], s["synckey_antes"]) == (
        7019, D19, "partes:19")
    assert (s["set"]["fec"], s["set"]["synckey"], s["set"]["hmoide"]) == (
        D18, "partes:18", HMO_OCT)
    (e,) = r.escritas
    assert (e["registro_id"], e["hora_codigo"], e["movida_de"],
            e["hmores_ide"]) == (18, "CIV", 19, 7019)
    assert "ciz_hmores_ide" not in e
    filas = _por_sk(cli)
    assert sorted(filas) == ["partes:18", "partes:25"]
    assert (filas["partes:18"]["fec"], filas["partes:18"]["horide"]) == (
        D18, H_CIV)
    assert filas["partes:25"]["fec"] == D25
    # R24: el hermano se decidio antes, sin cambios: hay CIZ posterior.
    assert ("[registro] ciz_mismo_dia_omitido registro_id=18 "
            "motivo=posterior") in caplog.text


def test_f085_pipeline_r30b_sin_la_del_19_escribe_con_insert() -> None:
    cli = _caso(con_19=False)
    enviadas = _espiar(cli)
    r = _ejecutar(cli, [_linea_inicio(18, D18, RACHA_18)])
    assert _ops(enviadas) == ["insert"]
    assert enviadas[0]["fec"] == D18 and enviadas[0]["horide"] == H_CIV
    (e,) = r.escritas
    assert "movida_de" not in e and "ciz_hmores_ide" not in e
    assert sorted(_por_sk(cli)) == ["partes:18", "partes:25"]


# ------------------------------- R31 -------------------------------- #

def test_f085_pipeline_r31_dos_llegadas_hacia_atras() -> None:
    cli = _caso()
    _ejecutar(cli, [_linea_inicio(18, D18, RACHA_18)])
    enviadas = _espiar(cli)
    r = _ejecutar(cli, [_linea_inicio(17, D17, [18] + RACHA_18)])
    assert _ops(enviadas) == ["mover"]
    (e,) = r.escritas
    assert (e["registro_id"], e["movida_de"], e["hmores_ide"]) == (
        17, 18, 7019)
    filas = _por_sk(cli)
    assert sorted(filas) == ["partes:17", "partes:25"]
    civ = [f for f in cli.lineas if f["horide"] == H_CIV]
    assert [(f["ide"], f["fec"]) for f in civ] == [(7019, D17)]
    assert filas["partes:25"]["fec"] == D25 and \
        filas["partes:25"]["horide"] == H_CIZ


# ------------------------------- R21 -------------------------------- #

def test_f085_pipeline_r21_una_sola_lectura_de_racha_y_de_partes() -> None:
    cli = _caso()
    _ejecutar(cli, [_linea_inicio(18, D18, RACHA_18)])
    claves = sorted({k for i in RACHA_18
                     for k in (f"partes:{i}", f"partes:{i}:ciz")}
                    | {"partes:18:ciz"})
    assert cli.racha_leidas == [claves]
    assert cli.estados_leidos == [[HMO_OCT]]


def test_f085_pipeline_r21_inicio_sin_ciz_mismo_dia_tambien() -> None:
    """Un `inicio` que no lleva `ciz_mismo_dia` (su fin viaja en otra
    obra de la misma aprobación) también recoloca su inicio previo."""
    cli = _caso()
    enviadas = _espiar(cli)
    r = _ejecutar(cli, [_linea_inicio(18, D18, RACHA_18, ciz=False)])
    assert _ops(enviadas) == ["mover"]
    assert r.escritas[0]["movida_de"] == 19
    assert cli.racha_leidas == [sorted(
        k for i in RACHA_18 for k in (f"partes:{i}", f"partes:{i}:ciz"))]


def test_f085_pipeline_r21_sin_racha_no_lee() -> None:
    cli = _caso()
    _ejecutar(cli, [_linea_inicio(18, D18, [], ciz=False)])
    assert cli.racha_leidas == [] and cli.estados_leidos == []


def test_f085_pipeline_r21_un_fin_no_recoloca_nada() -> None:
    cli = _caso()
    enviadas = _espiar(cli)
    r = _ejecutar(cli, [_linea_fin(26, D25 + 1, RACHA_18)])
    assert _ops(enviadas) == ["mover"]
    assert enviadas[0]["synckey_antes"] == "partes:25"
    assert r.escritas[0]["movida_de"] == 25


# ------------------------------- R22 -------------------------------- #

def test_f085_pipeline_r22_enlazada_omite_sin_escribir(caplog) -> None:
    cli = _caso(enlazada=True)
    antes = [dict(f) for f in cli.lineas]
    enviadas = _espiar(cli)
    r = _ejecutar(cli, [_linea_inicio(18, D18, RACHA_18)])
    assert enviadas == [] and r.escritas == []
    assert r.omitidas == [{"registro_id": 18, "motivo":
                           motivo_linea_enlazada([7019], "PT26/00010")}]
    assert cli.lineas == antes


def test_f085_pipeline_r22_parte_cerrado_omite_sin_escribir() -> None:
    cli = _caso(hmoide=905)
    cli.partes.append(_parte(905, "PT26/00008", est=3))
    antes = [dict(f) for f in cli.lineas]
    enviadas = _espiar(cli)
    r = _ejecutar(cli, [_linea_inicio(18, D18, RACHA_18)])
    assert enviadas == [] and r.escritas == []
    (o,) = r.omitidas
    assert o["motivo"].startswith(
        "inicio_en_parte_cerrado: el inicio de la incidencia (linea 7019) "
        "esta en el parte PT26/00008 (Cerrado)")
    assert cli.lineas == antes


# ------------------------------- R23 -------------------------------- #

def test_f085_pipeline_r23_warning_si_no_se_mueve(caplog) -> None:
    """Caso de F-083 R15: un CIV posterior sin CIZ detras no es inicio
    previo: INSERT como hoy y WARNING sin nombres ni DNIs."""
    cli = _cli(_fila(7001, fec=D19, rid=19, horide=H_CIV))
    enviadas = _espiar(cli)
    with caplog.at_level(logging.INFO):
        r = _ejecutar(cli, [_linea_inicio(18, D18, [19])])
    assert _ops(enviadas) == ["insert"]
    assert "movida_de" not in r.escritas[0]
    avisos = [(x.levelname, x.getMessage()) for x in caplog.records
              if "racha_inicio_no_movido" in x.getMessage()]
    assert avisos == [("WARNING", "[registro] racha_inicio_no_movido "
                                  "registro_id=18 ide=7001")]
    assert "Persona" not in caplog.text


def test_f085_pipeline_r23_sin_nada_ni_warning(caplog) -> None:
    cli = _caso(con_19=False)
    with caplog.at_level(logging.INFO):
        _ejecutar(cli, [_linea_inicio(18, D18, RACHA_18)])
    assert "racha_inicio_no_movido" not in caplog.text


# ------------------------------- R25 -------------------------------- #

def test_f085_pipeline_r25_info_inicio_movido(caplog) -> None:
    cli = _caso()
    with caplog.at_level(logging.INFO):
        _ejecutar(cli, [_linea_inicio(18, D18, RACHA_18)])
    info = [(x.levelname, x.getMessage()) for x in caplog.records
            if "inicio_movido" in x.getMessage()]
    assert info == [("INFO", "[registro] inicio_movido ide=7019 "
                             f"hmoide={HMO_OCT}->{HMO_OCT} "
                             f"fecha={D19}->{D18} registro_id=19->18")]
    assert "ciz movido" not in caplog.text
    assert "Persona" not in caplog.text


def test_f085_pipeline_r25_el_ciz_movido_sigue_igual(caplog) -> None:
    cli = _caso()
    with caplog.at_level(logging.INFO):
        _ejecutar(cli, [_linea_fin(26, D25 + 1, RACHA_18)])
    assert "[registro] ciz movido ide=7025" in caplog.text
    assert "inicio_movido" not in caplog.text


# ------------------------------- R26 -------------------------------- #

def test_f085_pipeline_r26_preflight_consultivo() -> None:
    cli = _caso()
    antes = [dict(f) for f in cli.lineas]
    enviadas = _espiar(cli)
    pf = _pipe(cli).preflight(obra=_obra(),
                              lineas=[_linea_inicio(18, D18, RACHA_18)])
    a = _acc(pf, 18)
    assert a.accion == "escribir" and a.mover is not None
    assert a.mover.ide == 7019
    assert enviadas == [] and cli.lineas == antes


def test_f085_pipeline_r26_preflight_omite_en_parte_cerrado() -> None:
    cli = _caso(hmoide=905)
    cli.partes.append(_parte(905, "PT26/00008", est=3))
    pf = _pipe(cli).preflight(obra=_obra(),
                              lineas=[_linea_inicio(18, D18, RACHA_18)])
    a = _acc(pf, 18)
    assert a.accion == "omitir"
    assert a.motivo.startswith("inicio_en_parte_cerrado")


# ------------------------------- R27 -------------------------------- #

def _insert_18(pos=64) -> dict:
    return {"op": "insert", "hmoide": HMO_OCT, "reside": RES, "pos": pos,
            "fec": D18, "horide": H_CIV, "can": 0.0, "pre": 2.0, "tot": 0.0,
            "paride": 0, "ano": 2026, "mes": 10, "synckey": "partes:18",
            "tex": None, "caaide": 0, "guarda_hmoide": HMO_OCT,
            "pisadas": []}


@pytest.mark.parametrize("como", [{"inicio": False}, {"sin_ajuste": True}])
@pytest.mark.parametrize("ciz", [True, False])
def test_f085_pipeline_r27_apagado_como_la_base(como, ciz) -> None:
    """Base de la rama (ae0fac7): el inicio del 18 escribe su CIV con
    INSERT; con `ciz_mismo_dia` lee el tramo y su propia `:ciz` (y el CIZ
    del 25 le quita el hermano); sin el, no lee nada."""
    cli = _caso()
    enviadas = _espiar(cli)
    r = _ejecutar(cli, [_linea_inicio(18, D18, RACHA_18, ciz=ciz)], **como)
    assert enviadas == [_insert_18(pos=256)]
    assert "movida_de" not in r.escritas[0]
    if ciz:
        assert cli.racha_leidas == [sorted(
            {k for i in RACHA_18 for k in (f"partes:{i}", f"partes:{i}:ciz")}
            | {"partes:18:ciz"})]
    else:
        assert cli.racha_leidas == []
    assert cli.estados_leidos == []
    assert sorted(_por_sk(cli)) == ["partes:18", "partes:19", "partes:25"]


def test_f085_pipeline_r27_settings_real_apagado_por_defecto(
        monkeypatch, tmp_path) -> None:
    from config.settings import Settings
    from tests.test_f060_pipeline_mover import ENTORNO_MINIMO
    for k, v in ENTORNO_MINIMO.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("MOVER_INICIO", raising=False)
    monkeypatch.chdir(tmp_path)
    assert Settings().mover_inicio is False
    monkeypatch.setenv("MOVER_INICIO", "true")
    assert Settings().mover_inicio is True


def test_f085_pipeline_r27_sin_mover_ciz_no_hace_nada() -> None:
    """B usa el paso 6 bis de F-060: con `MOVER_CIZ` apagado no lee ni
    mueve nada aunque `MOVER_INICIO` este encendido."""
    cli = _caso()
    enviadas = _espiar(cli)
    _ejecutar(cli, [_linea_inicio(18, D18, RACHA_18)], mover=False)
    assert _ops(enviadas) == ["insert"]
    assert cli.racha_leidas == [] and cli.estados_leidos == []


# ------------------------------- R32 -------------------------------- #
# Los casos de F-083 R13-R17 y de F-062 dan lo mismo con `MOVER_INICIO`.

from tests.test_f083_ciz_solo_fin_de_racha import (  # noqa: E402
    D1,
    D2,
    D3,
    _a_mano_a_civ,
)


def _escenario_f083_r13(cli, ej):
    lineas = [_linea_inicio(1, D1, [2, 3], ciz=False), _linea_fin(2, D2),
              _linea_fin(3, D3, [1, 2])]
    lineas[1].incidencia_rol = "intermedio"
    ej(cli, lineas)
    _a_mano_a_civ(cli, "partes:3")
    return ej(cli, [_linea_fin(2, D2, [1, 3])])


def _escenario_f083_r15(cli, ej):
    cli.lineas.append(_fila(7001, fec=D3, rid=3, horide=H_CIV))
    return ej(cli, [_linea_inicio(1, D1, [2, 3])])


def _escenario_f083_r16(cli, ej):
    _escenario_f083_r13(cli, ej)
    return [ej(cli, [_linea_fin(2, D2, [1, 3])]) for _ in range(3)][-1]


def _escenario_f062_suelto(cli, ej):
    return ej(cli, [_linea_inicio(4, 20261004, [])])


def _escenario_f062_racha_dia_a_dia(cli, ej):
    ej(cli, [_linea_inicio(1, D1, [])])
    ej(cli, [_linea_fin(2, D2, [1])])
    return ej(cli, [_linea_fin(3, D3, [1, 2])])


def _escenario_f062_ciz_posterior(cli, ej):
    cli.lineas.append(_fila(7003, fec=D3, rid=3))
    return ej(cli, [_linea_inicio(1, D1, [2, 3])])


def _escenario_f062_reaprobar_inicio(cli, ej):
    ej(cli, [_linea_inicio(1, D1, [])])
    return ej(cli, [_linea_inicio(1, D1, [])])


ESCENARIOS = [_escenario_f083_r13, _escenario_f083_r15, _escenario_f083_r16,
              _escenario_f062_suelto, _escenario_f062_racha_dia_a_dia,
              _escenario_f062_ciz_posterior, _escenario_f062_reaprobar_inicio]


def _correr(escenario, *, inicio: bool):
    cli = _cli()
    enviadas = _espiar(cli)

    def ej(c, lineas):
        return _ejecutar(c, lineas, inicio=inicio)
    r = escenario(cli, ej)
    return (enviadas, sorted((e["registro_id"], e["hora_codigo"],
                              e.get("movida_de")) for e in r.escritas),
            r.omitidas, [(f["synckey"], f["fec"], f["horide"])
                         for f in cli.lineas])


@pytest.mark.parametrize("escenario", ESCENARIOS,
                         ids=[e.__name__ for e in ESCENARIOS])
def test_f085_pipeline_r32_mismos_resultados_encendido(escenario) -> None:
    assert _correr(escenario, inicio=True) == _correr(escenario, inicio=False)


def test_f085_pipeline_r32_preflight_f083_r17_encendido() -> None:
    cli = _cli()
    _escenario_f083_r13(cli, lambda c, l: _ejecutar(c, l, inicio=False))
    pf = _pipe(cli).preflight(obra=_obra(),
                              lineas=[_linea_fin(2, D2, [1, 3])])
    a = _acc(pf, 2)
    assert a.accion == "omitir" and a.mover is None
    assert "la racha sigue en Sigrid el dia 2026-10-03" in a.motivo


def test_f085_decision_inicio_inmutable() -> None:
    """Protege el diseño: `DecisionInicio` es un valor (frozen), como
    `DecisionFin`; el pipeline la lee y no la modifica. Mata el
    superviviente `@dataclass(frozen=True)` -> `frozen=False`."""
    import dataclasses
    d = _decidir([CIV19, CIZ25])
    with pytest.raises(dataclasses.FrozenInstanceError):
        d.tipo = CREAR
