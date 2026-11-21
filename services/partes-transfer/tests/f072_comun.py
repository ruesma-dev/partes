# tests/f072_comun.py
"""Dobles comunes de los tests de F-072 en sv5 (obras agrupadas).

`ClienteF072` es el `SigridFake` de siempre más el presupuesto de las obras
agrupadas (`partidas_de_obra`) y la partida de cada línea existente
(`LineaSigrid.paride`). Datos FICTICIOS.
"""
from __future__ import annotations

from application.services.obras_agrupadas import ajustes_de
from domain.models.registro_models import (
    LineaEntrada,
    ObraEntrada,
    PartidaHoja,
)
from tests.dobles import SettingsFake, SigridFake

FECHA = 20261116
HL, HE = 1, 2
AJUSTES = ajustes_de(postventa_cod="POSTV2", var_cod="VAR", var_desde="29")


def obra(ide, cod, empresa=1) -> ObraEntrada:
    o = ObraEntrada(ide=ide, codigo=cod, nombre=f"Obra {cod}", empresa=empresa)
    o.cenide = 0
    return o


NORMAL = obra(10, "0100")
PV = obra(9001, "POSTV2")
VARO = obra(9101, "VAR")
PRUEBAS = obra(99, "0404")

PRESUPUESTOS = {
    PV.ide: [PartidaHoja(90010, "CD", "COSTES DIRECTOS", False, True),
             PartidaHoja(90011, "0578B", "RESIDENCIAL", True, True),
             PartidaHoja(90015, "0700", "DE BAJA", True, False)],
    VARO.ide: [PartidaHoja(91010, "CD", "COSTES DIRECTOS", False, True),
               PartidaHoja(91011, "28", "VARIOS 28", True, True),
               PartidaHoja(91012, "29", "VARIOS 29", True, True),
               PartidaHoja(91013, "030", "VARIOS 30", True, True),
               PartidaHoja(91014, "31", "VARIOS 31", True, False),
               PartidaHoja(91015, "32", "CAPITULO 32", False, True)],
}


class SettingsF072(SettingsFake):
    def __init__(self, *, ajustes=AJUSTES, **kw) -> None:
        super().__init__(**kw)
        self.obras_agrupadas = ajustes


class ClienteF072(SigridFake):
    def __init__(self, *, presupuestos=None, **kw) -> None:
        from domain.models.registro_models import HoraRecurso

        kw.setdefault("obras", {o.codigo: o for o in (NORMAL, PV, VARO, PRUEBAS)})
        kw.setdefault("horas", {501: [
            HoraRecurso(horide=HL, cod="HL01", res=None, pre=10.0, defecto=True),
            HoraRecurso(horide=HE, cod="HE01", res=None, pre=12.0)]})
        super().__init__(**kw)
        self.presupuestos = dict(PRESUPUESTOS if presupuestos is None
                                 else presupuestos)
        self.presupuestos_leidos: list[int] = []
        self.fallo_presupuesto: Exception | None = None

    def partidas_de_obra(self, obra_ide: int):
        self._lectura("partidas_de_obra")
        self.presupuestos_leidos.append(int(obra_ide))
        if self.fallo_presupuesto is not None:
            raise self.fallo_presupuesto
        return list(self.presupuestos.get(int(obra_ide), []))

    def _a_linea_sigrid(self, l: dict):
        ls = super()._a_linea_sigrid(l)
        ls.paride = l.get("paride")
        return ls


def linea(rid, partida=None, metodo=None, *, recurso=501, cod=None,
          tipo="normal", horas=8.0, fecha=FECHA) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=fecha, recurso_ide=recurso,
                        nombre=f"Persona {rid}", tipo_hora=tipo, horas=horas,
                        partida_ide=partida, partida_cod=cod,
                        partida_metodo=metodo)
