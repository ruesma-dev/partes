# tests/test_f053_pipeline_pisado.py
"""F-053 · Pisar sin borrar en el pipeline de registro (R1, R5-R8, R10,
R12-R18) y en el doble `SigridFake` (design §7).

  - Doble: la op `anular` evalua el `UPDATE` de `stmt_anular_linea` como
    SQL Server (fila con esos valores, sin enlaces y con su parte En
    registro); no hay op `borrar`.
  - Pipeline: los ejemplos 1-6 de `requirements.md`, la precedencia de las
    omisiones (R8), `anuladas` por relectura (R12), el INFO de cada pisada
    (R13), la relectura que falla (R14) y la caracterizacion (R15-R18).

Sin red: `SigridFake` de `tests/dobles.py`. Datos SINTETICOS (obras,
codigos y personas inventados; ni nombres reales ni DNIs).
"""
from __future__ import annotations

import pytest
from domain.models.registro_models import HoraRecurso, ObraEntrada
from tests.dobles import SigridFake

FECHA = 20261015
REC = 501
HN, HE, CIV = 1, 2, 30
REGISTRO, CERRADO, IMPUTADO = 1, 3, 10
OBRA = 10
HMO = 900                     # PT26/00314


def _obra(ide=OBRA, cod="0100", empresa=1) -> ObraEntrada:
    o = ObraEntrada(ide=ide, codigo=cod, nombre=f"Obra {cod}",
                    empresa=empresa)
    o.cenide = 77
    return o


def _h(horide, cod, defecto=False, pre=15.0) -> HoraRecurso:
    return HoraRecurso(horide=horide, cod=cod, res=None, pre=pre,
                       caa_cod=None, defecto=defecto)


HORAS = {REC: [_h(HN, "HN", True), _h(HE, "HE1", pre=25.0),
               _h(CIV, "CIV", pre=0.0)]}


def _parte(ide, cod, est=REGISTRO, ano=2026, mes=10) -> dict:
    return {"ide": ide, "obride": OBRA, "ano": ano, "mes": mes, "cod": cod,
            "emp": 1, "est": est}


def _fila(ide, hmoide=HMO, *, reside=REC, horide=HN, synckey=None,
          fec=FECHA, can=8.0, enlazada=False, tex="manual") -> dict:
    return {"ide": ide, "hmoide": hmoide, "reside": reside, "fec": fec,
            "horide": horide, "hora_codigo": None, "can": can,
            "tot": None if can is None else can * 15.0, "pos": 64,
            "synckey": synckey, "caaide": 702, "paride": 33, "tex": tex,
            "enlazada": enlazada}


def _cli(**kw) -> SigridFake:
    return SigridFake(obras={"0100": _obra()}, horas=HORAS, **kw)


def _anular(cli, ide=9001, *, reside=REC, fecha_int=FECHA, horide=HN,
            antes=8.0) -> dict:
    return cli.stmt_anular_linea(ide=ide, reside=reside, fecha_int=fecha_int,
                                 horide=horide, antes=antes)


# ============================ Doble (T3, §7) ============================ #

def test_f053_doble_sin_op_borrar() -> None:
    assert not hasattr(SigridFake, "stmt_borrar_linea")
    cli = _cli(partes=[_parte(HMO, "PT26/00314")], lineas=[_fila(9001)])
    with pytest.raises(AssertionError, match="op desconocida: borrar"):
        cli.escribir([{"op": "borrar", "ide": 9001}])
    assert cli.lineas == [_fila(9001)]


def test_f053_doble_anular_sentencia() -> None:
    assert _anular(_cli(), "9001", horide=None, antes=None) == {
        "op": "anular", "ide": 9001, "reside": REC, "fec": FECHA,
        "horide": 0, "antes": 0.0}


def test_f053_doble_anular_pone_a_cero_y_no_toca_nada_mas() -> None:
    previa = _fila(9001, synckey="porcentajes:7")
    cli = _cli(partes=[_parte(HMO, "PT26/00314")], lineas=[dict(previa)])
    assert cli.escribir([_anular(cli)]) == 1
    assert cli.lineas == [dict(previa, can=0.0, tot=0.0)]


@pytest.mark.parametrize("cambio", [
    {"ide": 9002}, {"reside": REC + 1}, {"fecha_int": FECHA + 1},
    {"horide": HE}, {"antes": 8.0011}, {"antes": 7.998}],
    ids=["otro-ide", "otro-recurso", "otro-dia", "otro-codigo",
         "can-cambio-arriba", "can-cambio-abajo"])
def test_f053_doble_anular_where_optimista(cambio) -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")], lineas=[_fila(9001)])
    assert cli.escribir([_anular(cli, **cambio)]) == 0
    assert cli.lineas == [_fila(9001)]


def test_f053_doble_anular_tolerancia_de_0_001() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")], lineas=[_fila(9001)])
    assert cli.escribir([_anular(cli, antes=8.0009)]) == 1
    assert cli.lineas[0]["can"] == 0


def test_f053_doble_anular_horide_y_can_nulos_son_0() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")],
               lineas=[_fila(9001, horide=None, can=None)])
    assert cli.escribir([_anular(cli, horide=None, antes=None)]) == 1
    assert (cli.lineas[0]["can"], cli.lineas[0]["tot"]) == (0.0, 0.0)


def test_f053_doble_anular_no_toca_enlazadas_ni_partes_cerrados() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314"),
                       _parte(905, "PT26/00400", est=CERRADO)],
               lineas=[_fila(9001, enlazada=True), _fila(9002, 905)])
    assert cli.escribir([_anular(cli, 9001), _anular(cli, 9002),
                         _anular(cli, 9003)]) == 0
    assert [l["can"] for l in cli.lineas] == [8.0, 8.0]


def test_f053_doble_anular_dispara_el_cierre_de_la_ventana() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")], lineas=[_fila(9001)])
    cli.cerrar_al_escribir = {HMO: CERRADO}
    assert cli.escribir([_anular(cli)]) == 0
    assert cli.partes[0]["est"] == CERRADO and cli.lineas[0]["can"] == 8.0


def test_f053_doble_lineas_traen_enlazada() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")],
               lineas=[_fila(9001, enlazada=True), _fila(9002)])
    a, b = cli.lineas_existentes(HMO, [REC], [FECHA])
    assert (a.enlazada, b.enlazada) == (True, False)
    assert cli.lineas_por_ide([9001])[9001].enlazada is True
    sin_clave = _cli(lineas=[{k: v for k, v in _fila(9003).items()
                              if k != "enlazada"}])
    assert sin_clave.lineas_por_ide([9003])[9003].enlazada is False
