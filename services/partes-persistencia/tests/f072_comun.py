# tests/f072_comun.py
"""Datos y dobles comunes de los tests de F-072 en sv3 (obras agrupadas).

Sigrid en memoria, con datos FICTICIOS que reproducen lo leído en Sigrid el
2026-11-20 (design §11): `POSTV2` y `VAR` en las empresas 1 y 28, la antigua
`POSTV` en la 1 y una obra `150702-V` que acaba en `-V`.
"""
from __future__ import annotations

from datetime import date

from application.pipelines.persist_parte_pipeline import PersistPartePipeline
from application.services.entrada_agrupada import ResolutorEntradas
from application.services.obras_agrupadas import ajustes_de
from application.services.parte_normalizer import ParteNormalizer
from application.services.sigrid_matcher_provider import SigridMatcherProvider
from domain.models.parte_records import ParteDocumento, RegistroNormalizado
from domain.models.sigrid_models import (
    EmpleadoRow,
    EmpresaRow,
    ObraRow,
    PartidaRow,
    TipoHoraRow,
)
from tests.dobles import recurso_persona

HOY = 20261116
DNI_A = "11111111H"      # empresa 1
DNI_B = "22222222J"      # empresa 28

O578 = ObraRow(ide=578, codigo="0578", nombre="Residencial Uno", empresa=1)
O654 = ObraRow(ide=654, codigo="0654", nombre="Nave Dos", empresa=1)
O100 = ObraRow(ide=100, codigo="0100", nombre="Colegio", empresa=1)
O400 = ObraRow(ide=400, codigo="0400", nombre="Puerto", empresa=28)
O150702V = ObraRow(ide=7001, codigo="150702-V", nombre="Obra con V", empresa=1)
PV1 = ObraRow(ide=9001, codigo="POSTV2", nombre="POSTVENTA", empresa=1)
PV28 = ObraRow(ide=9028, codigo="POSTV2", nombre="POSTVENTA", empresa=28)
VAR1 = ObraRow(ide=9101, codigo="VAR", nombre="OBRAS VARIAS", empresa=1)
VAR28 = ObraRow(ide=9128, codigo="VAR", nombre="OBRAS VARIAS", empresa=28)
POSTV_VIEJA = ObraRow(ide=9201, codigo="POSTV", nombre="POSTVENTA ANTIGUA",
                      empresa=1)
OBRAS = (O578, O654, O100, O400, O150702V, PV1, PV28, VAR1, VAR28, POSTV_VIEJA)


def _p(ide, padide, cod, tipdes=0, res=None) -> PartidaRow:
    return PartidaRow(ide=ide, padide=padide, cod=cod, res=res or f"P {cod}",
                      tex=None, tipdes=tipdes, cosindide=None, unimed=None)


PRESUPUESTOS: dict[int, list[PartidaRow]] = {
    PV1.ide: [_p(90010, 0, "CD", res="COSTES DIRECTOS"),
              _p(90011, 90010, "0578B", res="RESIDENCIAL UNO"),
              _p(90012, 90010, "0654-B", res="NAVE DOS"),
              _p(90013, 90010, "0100", res="COLEGIO"),
              _p(90014, 90010, "150702-V", res="OBRA CON V")],
    PV28.ide: [_p(90280, 0, "CD", res="COSTES DIRECTOS"),
               _p(90281, 90280, "0400", res="PUERTO")],
    VAR1.ide: [_p(91010, 0, "CD", res="COSTES DIRECTOS"),
               _p(91011, 91010, "28", res="VARIOS 28"),
               _p(91012, 91010, "29", res="VARIOS 29"),
               _p(91013, 91010, "030", res="VARIOS 30"),
               _p(91014, 91010, "31", tipdes=1, res="VARIOS 31 BAJA"),
               _p(91015, 91010, "32", res="CAPITULO 32"),
               _p(91016, 91015, "32.1", res="VARIOS 32.1")],
    VAR28.ide: [_p(91280, 0, "CD", res="COSTES DIRECTOS"),
                _p(91281, 91280, "29", res="VARIOS 29 PORSAN")],
}

FICHAS = [
    EmpleadoRow(ide=10, codigo="E10", nombre="ANA UNO", dni=DNI_A,
                reside=910, empresa=1, fecbaj=0),
    EmpleadoRow(ide=20, codigo="E20", nombre="BEA VEINTIOCHO", dni=DNI_B,
                reside=920, empresa=28, fecbaj=0),
]
RECURSOS = [
    recurso_persona(ide=910, cif=None, conide=10, empresa=1, fecbaj=0),
    recurso_persona(ide=920, cif=None, conide=20, empresa=28, fecbaj=0),
]
EMPRESAS = [EmpresaRow(numemp=1, nombre="UNO"),
            EmpresaRow(numemp=28, nombre="VEINTIOCHO")]
TIPOS = [
    TipoHoraRow(ide=1, codigo="HL01", descripcion="Hora laborable", ext=0,
                pre=None, prenom=None),
    TipoHoraRow(ide=2, codigo="HE01", descripcion="Hora extra", ext=1,
                pre=None, prenom=None),
]

AJUSTES = ajustes_de(postventa_cod="POSTV2",
                     postventa_alias="POSTVENTA,POSTV,POST",
                     var_cod="VAR", var_alias="V", var_desde="29")
APAGADO = ajustes_de(postventa_cod=None, var_cod=None, var_desde=None)


class LookupF072:
    """Los maestros y presupuestos de Sigrid, en memoria. `error` hace fallar
    la lectura de presupuestos; `llamadas` las cuenta."""

    def __init__(self, *, obras=OBRAS, presupuestos=None,
                 error: Exception | None = None) -> None:
        self.obras = list(obras)
        self.presupuestos = dict(PRESUPUESTOS if presupuestos is None
                                 else presupuestos)
        self.error = error
        self.llamadas: list[int] = []

    def fetch_empleados(self):
        return list(FICHAS)

    def fetch_obras(self):
        return list(self.obras)

    def fetch_tipos_hora(self):
        return list(TIPOS)

    def fetch_recursos(self):
        return list(RECURSOS)

    def fetch_empresas(self):
        return list(EMPRESAS)

    def fetch_partidas_obra(self, obra_ide: int):
        self.llamadas.append(obra_ide)
        if self.error is not None:
            raise self.error
        return list(self.presupuestos.get(obra_ide, []))


class RepoF072:
    def __init__(self) -> None:
        self.guardados: list[dict] = []

    def get_by_sha256(self, _sha):
        return None

    def find_empleado_alias(self, _nombre):
        return None

    def save_parte(self, **kwargs) -> None:
        self.guardados.append(kwargs)


def proveedor(lookup: LookupF072) -> SigridMatcherProvider:
    return SigridMatcherProvider(
        lookup=lookup, empleado_min_score=0.55, obra_min_score=0.55,
        default_hora_normal_cod="HL01", default_hora_extra_cod="HE01",
        alias_empresas={1: ["RUESMA"], 28: ["PORSAN"]})


def pipeline(lookup: LookupF072 | None = None, *, ajustes=AJUSTES,
             repo: RepoF072 | None = None, entradas=True):
    lookup = lookup or LookupF072()
    return PersistPartePipeline(
        repository=repo or RepoF072(), normalizer=ParteNormalizer(),
        matcher_provider=proveedor(lookup),
        entradas=(ResolutorEntradas(lookup=lookup, ajustes=ajustes)
                  if entradas else None),
        hoy=lambda: date(2026, 11, 16))


def parte(obra, *trabajadores, partidas=None, membrete=None,
          nombre_obra=None) -> ParteDocumento:
    """Un parte con un registro por trabajador (`(nombre, dni)`); `partidas`
    da la partida leída de cada registro, en orden."""
    trabajadores = trabajadores or (("ANA UNO", DNI_A),)
    partidas = list(partidas or [None] * len(trabajadores))
    registros = [
        RegistroNormalizado(line_index=i, trabajador_nombre_leido=n,
                            trabajador_dni_leido=d, tipo_hora="normal",
                            horas=8.0, partida=partidas[i])
        for i, (n, d) in enumerate(trabajadores)]
    return ParteDocumento(fecha_int=HOY, fecha_iso="2026-11-16",
                          obra_numero_leido=obra, obra_nombre_leido=nombre_obra,
                          empresa_membrete=membrete, firmado=True,
                          registros=registros)
