# tests/test_f072_t28_mutantes.py
"""F-072 · T28: tests que matan supervivientes de la campaña de mutación de
sv3 (`progress/mutacion_F-072.md`). Cada test nombra el superviviente.

Las reglas del gemelo `obras_agrupadas.py` NO van aquí: van en
`tests/test_f072_obras_agrupadas.py`, que las otras tres copias ejecutan por
`test_f072_obras_agrupadas_copia.py`. Sin red ni BBDD. Datos FICTICIOS.
"""
from __future__ import annotations

import dataclasses
from types import SimpleNamespace

import pytest

from application.services import entrada_agrupada as ea
from application.services.entrada_agrupada import ResolutorEntradas, ResultadoEntrada
from application.services.obras_agrupadas import POSTVENTA, VAR, Forma, ajustes_de
from domain.models.parte_records import EntradaPartida, ObraMatch
from tests import f072_comun as c


class _Matcher:
    """`matchers.obra` mínimo: una obra fija para `match` y las de código."""

    def __init__(self, obra: ObraMatch, obras=c.OBRAS) -> None:
        self._obra, self._obras = obra, list(obras)

    def match(self, **_kw) -> ObraMatch:
        return dataclasses.replace(self._obra)

    def obras_de_codigo(self, codigo):
        return [o for o in self._obras if o.codigo == codigo]


def _resolver(forma, obra, *, lookup=None, ajustes=c.AJUSTES, obras=c.OBRAS):
    lookup = lookup or c.LookupF072()
    matchers = SimpleNamespace(obra=_Matcher(obra, obras))
    return ResolutorEntradas(lookup=lookup, ajustes=ajustes).resolver(
        forma, c.parte("x"), matchers, None, [])


# ---------------- entrada_agrupada.py:124 y :140 (`is None`) ---------------- #

def test_t28_var_un_ide_0_es_una_obra_solo_none_es_sin_obra():
    """`:124`: `obra.ide is None` es «sin obra»; un `ide` 0 no lo es."""
    lookup = c.LookupF072(presupuestos={0: c.PRESUPUESTOS[c.VAR1.ide]})
    res = _resolver(Forma(VAR, "29"), ObraMatch(ide=0, codigo="VAR", empresa=1),
                    lookup=lookup)
    assert (res.obra.ide, res.partida.ide, res.tipo) == (0, 91012, VAR)
    sin = _resolver(Forma(VAR, "29"), ObraMatch(ide=None))
    assert sin.obra.method == ea.AGRUPADA_SIN_OBRA


def test_t28_postventa_la_obra_x_con_ide_0_casa():
    """`:140`: la obra X con `ide` 0 es una obra; solo `None` no casa."""
    res = _resolver(Forma(POSTVENTA, "578"),
                    ObraMatch(ide=0, codigo="0578", empresa=1))
    assert (res.obra.ide, res.partida.ide, res.tipo) == (9001, 90011, POSTVENTA)
    sin = _resolver(Forma(POSTVENTA, "578"), ObraMatch(ide=None))
    assert sin.obra.method == ea.POSTVENTA_OBRA_NO_CASA


# ------------------- entrada_agrupada.py:126 (`or 0`) ------------------- #

def test_t28_var_desde_0_admite_la_partida_0():
    """`:126`: con `VAR_PARTIDA_DESDE=0` la partida de número 0 es del
    universo VAR (R2 admite el 0)."""
    pres = dict(c.PRESUPUESTOS)
    pres[c.VAR1.ide] = pres[c.VAR1.ide] + [c._p(91017, 91010, "0", res="CERO")]
    desde0 = ajustes_de(postventa_cod="POSTV2", var_cod="VAR", var_desde="0")
    res = _resolver(Forma(VAR, "0"), ObraMatch(ide=c.VAR1.ide, codigo="VAR",
                                               empresa=1),
                    lookup=c.LookupF072(presupuestos=pres), ajustes=desde0)
    assert (res.partida.ide, res.tipo) == (91017, VAR)


# ---------------- entrada_agrupada.py:160 (frontera del TTL) ---------------- #

def test_t28_el_presupuesto_caduca_justo_al_cumplir_el_ttl(monkeypatch):
    """`:160`: `< ttl`; a los `ttl` segundos justos se vuelve a leer."""
    reloj = [1000.0]
    monkeypatch.setattr(ea.time, "time", lambda: reloj[0])
    lookup = c.LookupF072()
    resolutor = ResolutorEntradas(lookup=lookup, ajustes=c.AJUSTES,
                                  ttl_seconds=600)
    resolutor._hojas(9101)
    reloj[0] = 1599.0
    resolutor._hojas(9101)
    assert lookup.llamadas == [9101]
    reloj[0] = 1600.0
    resolutor._hojas(9101)
    assert lookup.llamadas == [9101, 9101]


# ------------- dataclasses inmutables (`frozen=True`) de sv3 ------------- #

@pytest.mark.parametrize("valor, campo", [
    (ResultadoEntrada(obra=ObraMatch()), "tipo"),              # entrada_agrupada.py:58
    (EntradaPartida(ide=1, cod="29", res=None, capitulo="CD", tipo=VAR),
     "ide"),                                                   # parte_records.py:125
])
def test_t28_los_valores_de_la_entrada_son_inmutables(valor, campo):
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(valor, campo, None)

