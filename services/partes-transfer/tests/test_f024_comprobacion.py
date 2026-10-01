# tests/test_f024_comprobacion.py
"""F-024 · comprobacion de solo lectura de las lineas de sv5 en Sigrid (R1-R9).

Tres capas, sin red ni Sigrid:

  - `clasificar` (pura): tablas de casos de R2-R6.
  - el cliente (`lineas_por_ide`, `partes_por_ide`) contra sigrid-api
    simulado con `httpx.post` sustituido (R7, R8).
  - `ComprobadorLineas` y el endpoint `POST /api/registro/comprobar` con un
    cliente en memoria (R1, R8, R9).

Todos los `ide`, recursos y codigos son sinteticos.
"""
from __future__ import annotations

import pytest
from application.services.comprobacion_lineas import (
    LineaComprobar,
    Veredicto,
    clasificar,
)
from domain.models.registro_models import LineaSigrid

HMO = 7001          # parte (hmo.ide) sintetico
HMO_OTRO = 7002
COD = "PT26/09001"
COD_OTRO = "PT26/09002"


def _ls(ide: int, *, reside: int = 501, fecha: int = 20260916,
        can: float | None = 8.0, synckey: str | None = None,
        hmoide: int = HMO) -> LineaSigrid:
    """Una fila de `hmores` como la devuelve el cliente."""
    ls = LineaSigrid(ide=ide, reside=reside, fecha_int=fecha, horide=1,
                     hora_codigo=None, can=can, tot=None, synckey=synckey,
                     nuestra=bool(synckey))
    setattr(ls, "hmoide", hmoide)
    return ls


def _linea(rid: int = 11, *, hmores_ide: int | None = 4001,
           hmoide: int | None = HMO, recurso: int | None = 501,
           fecha: int | None = 20260916, horas: float | None = 8.0,
           incidencia: bool = False) -> LineaComprobar:
    return LineaComprobar(registro_id=rid, hmores_ide=hmores_ide,
                          hmoide=hmoide, recurso_ide=recurso,
                          fecha_int=fecha, horas=horas,
                          es_incidencia=incidencia)


def _uno(linea, *, synckey=None, ide=None, partes=None) -> Veredicto:
    por_sk = synckey or {}
    por_ide = ide or {}
    out = clasificar([linea], por_sk, por_ide,
                     {HMO: COD} if partes is None else partes)
    assert len(out) == 1
    return out[0]


# ===================================================================== #
# clasificar · R2-R6
# ===================================================================== #

def test_f024_r2_clasificar_acierto_por_synckey_es_presente() -> None:
    v = _uno(_linea(11), synckey={"partes:11": _ls(4001, synckey="partes:11")})
    assert v.estado == "presente"
    assert v.registro_id == 11
    assert v.sin_synckey is False
    assert v.parte_existe is True
    assert v.diferencias == []
    assert v.motivo is None


def test_f024_r2_clasificar_la_synckey_es_la_del_pipeline() -> None:
    """La clave es `partes:<registro_id>` (la de la idempotencia): otra
    clave del mismo `ide` no cuenta como acierto."""
    v = _uno(_linea(11), synckey={"partes:12": _ls(4001, synckey="partes:12")})
    assert v.estado == "borrada"


def test_f024_r5_clasificar_presente_lleva_las_referencias_actuales() -> None:
    """La linea se movio de parte en Sigrid: el veredicto trae lo de hoy."""
    v = _uno(_linea(11, hmores_ide=4001, hmoide=HMO),
             synckey={"partes:11": _ls(4999, synckey="partes:11",
                                       hmoide=HMO_OTRO)},
             partes={HMO: COD, HMO_OTRO: COD_OTRO})
    assert (v.hmores_ide, v.hmoide, v.parte_cod) == (4999, HMO_OTRO, COD_OTRO)


def test_f024_r3_clasificar_respaldo_por_ide_sin_synckey() -> None:
    v = _uno(_linea(11), ide={4001: _ls(4001, synckey=None)})
    assert v.estado == "presente"
    assert v.sin_synckey is True
    assert (v.hmores_ide, v.hmoide, v.parte_cod) == (4001, HMO, COD)


def test_f024_r3_clasificar_respaldo_con_synckey_en_blanco() -> None:
    v = _uno(_linea(11), ide={4001: _ls(4001, synckey="   ")})
    assert v.estado == "presente" and v.sin_synckey is True


def test_f024_r3_clasificar_respaldo_sin_hmoide_enviado() -> None:
    """Sin `hmoide` en el portal, basta recurso y fecha (R3)."""
    v = _uno(_linea(11, hmoide=None), ide={4001: _ls(4001)})
    assert v.estado == "presente" and v.sin_synckey is True
    assert v.hmoide == HMO and v.parte_cod == COD


@pytest.mark.parametrize("fila", [
    pytest.param(_ls(4001, synckey="partes:99"), id="otra-synckey"),
    pytest.param(_ls(4001, synckey="ajena"), id="synckey-ajena"),
    pytest.param(_ls(4001, reside=502), id="otro-recurso"),
    pytest.param(_ls(4001, fecha=20260917), id="otra-fecha"),
    pytest.param(_ls(4001, hmoide=HMO_OTRO), id="otro-parte"),
])
def test_f024_r3_clasificar_ide_reutilizado_es_borrada(fila) -> None:
    v = _uno(_linea(11), ide={4001: fila}, partes={HMO: COD, HMO_OTRO: COD_OTRO})
    assert v.estado == "borrada"
    assert v.sin_synckey is False


def test_f024_r3_clasificar_linea_sin_recurso_no_casa_por_ide() -> None:
    v = _uno(_linea(11, recurso=None), ide={4001: _ls(4001)})
    assert v.estado == "borrada"


def test_f024_r4_clasificar_sin_nada_es_borrada_con_motivo() -> None:
    v = _uno(_linea(11, hmores_ide=4001))
    assert v.estado == "borrada"
    assert v.parte_existe is True
    assert v.hmores_ide == 4001 and v.hmoide == HMO and v.parte_cod == COD
    assert v.motivo == f"la linea 4001 del parte {COD} ya no existe en Sigrid"
    assert v.diferencias == []


def test_f024_r4_clasificar_cabecera_borrada() -> None:
    v = _uno(_linea(11, hmores_ide=4001, hmoide=HMO), partes={})
    assert v.estado == "borrada"
    assert v.parte_existe is False
    assert v.parte_cod is None
    assert v.motivo == f"el parte {HMO} ya no existe en Sigrid"


def test_f024_r4_clasificar_sin_hmoide_no_afirma_que_falte_el_parte() -> None:
    v = _uno(_linea(11, hmores_ide=None, hmoide=None), partes={})
    assert v.estado == "borrada"
    assert v.parte_existe is True
    assert v.motivo == "la linea ? ya no existe en Sigrid"


def test_f024_r4_clasificar_parte_sin_codigo_usa_su_ide() -> None:
    v = _uno(_linea(11, hmores_ide=4001, hmoide=HMO), partes={HMO: ""})
    assert v.parte_existe is True
    assert v.motivo == f"la linea 4001 del parte {HMO} ya no existe en Sigrid"


def test_f024_r6_clasificar_diferencias_de_recurso_fecha_y_horas() -> None:
    v = _uno(_linea(11, recurso=501, fecha=20260916, horas=8.0),
             synckey={"partes:11": _ls(4001, synckey="partes:11", reside=502,
                                       fecha=20260917, can=6.0)})
    assert v.estado == "presente"
    assert v.diferencias == [
        "recurso: portal 501, Sigrid 502",
        "fecha: portal 20260916, Sigrid 20260917",
        "horas: portal 8, Sigrid 6",
    ]


@pytest.mark.parametrize("can, hay", [
    (8.0, False), (8.004, False), (7.996, False), (8.006, True),
    (7.994, True), (None, True),
])
def test_f024_r6_clasificar_tolerancia_de_horas(can, hay) -> None:
    v = _uno(_linea(11, horas=8.0),
             synckey={"partes:11": _ls(4001, synckey="partes:11", can=can)})
    assert bool(v.diferencias) is hay


def test_f024_r6_clasificar_incidencia_no_compara_horas() -> None:
    """Las reglas ponen `can=0` a las incidencias."""
    v = _uno(_linea(11, horas=8.0, incidencia=True),
             synckey={"partes:11": _ls(4001, synckey="partes:11", can=0.0)})
    assert v.diferencias == []


def test_f024_r6_clasificar_sin_horas_en_el_portal_no_compara_horas() -> None:
    v = _uno(_linea(11, horas=None),
             synckey={"partes:11": _ls(4001, synckey="partes:11", can=3.0)})
    assert v.diferencias == []


def test_f024_r6_clasificar_sin_recurso_en_el_portal_no_compara_recurso() -> None:
    """sv5 resuelve el recurso por DNI si el portal no lo trae (F-023
    R37): eso no es una diferencia hecha a mano."""
    v = _uno(_linea(11, recurso=None),
             synckey={"partes:11": _ls(4001, synckey="partes:11", reside=777)})
    assert v.diferencias == []


def test_f024_r6_clasificar_respaldo_por_ide_tambien_compara_horas() -> None:
    v = _uno(_linea(11, horas=8.0), ide={4001: _ls(4001, can=4.5)})
    assert v.sin_synckey is True
    assert v.diferencias == ["horas: portal 8, Sigrid 4.5"]


def test_f024_r1_clasificar_un_veredicto_por_linea_y_en_orden() -> None:
    lineas = [_linea(3, hmores_ide=1), _linea(1, hmores_ide=2),
              _linea(2, hmores_ide=3)]
    out = clasificar(lineas, {"partes:1": _ls(2, synckey="partes:1")}, {},
                     {HMO: COD})
    assert [(v.registro_id, v.estado) for v in out] == [
        (3, "borrada"), (1, "presente"), (2, "borrada")]
