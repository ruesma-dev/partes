# tests/test_f030_dni_canonico.py
"""F-030 · R1-R3: el DNI canonico del trabajador leido.

Sigrid guarda los DNI siempre con 8 digitos (215 + 43 fichas de alta
empiezan por `0`); el cero que falta es del PAPEL leido. sv3 completa con
ceros a la izquierda un DNI de 1 a 7 digitos y una letra, en un unico
punto (`parte_normalizer`), y asi casa por DNI con la ficha (F-023 R18).

Datos SINTETICOS. Sin red ni base.
"""
from __future__ import annotations

from datetime import date

import application.services.parte_normalizer as pn
import pytest
from application.pipelines.persist_parte_pipeline import PersistPartePipeline
from application.services.parte_normalizer import ParteNormalizer
from application.services.sigrid_matcher_provider import SigridMatcherProvider
from domain.models.sigrid_models import (
    EmpleadoRow,
    EmpresaRow,
    ObraRow,
    RecursoRow,
    TipoHoraRow,
)

# ============================== R1 ====================================== #


@pytest.mark.parametrize("leido, canonico", [
    ("9876543B", "09876543B"),          # 7 digitos: un cero
    ("1Z", "00000001Z"),                # 1 digito: siete ceros
    ("123456Z", "00123456Z"),           # 6 digitos
    (" 9.876.543-b ", "09876543B"),     # se normaliza antes
    ("09876543B", "09876543B"),         # ya tiene 8: igual
    ("12345678Z", "12345678Z"),
    ("X1234567L", "X1234567L"),         # NIE: igual
    ("B12345678", "B12345678"),         # CIF: igual
    ("123456789Z", "123456789Z"),       # 9 digitos: igual
    ("1234567", "1234567"),             # sin letra: igual
    ("1234567AB", "1234567AB"),         # dos letras: igual
    ("Z", "Z"),                         # sin digitos: igual
    ("", ""),
    (None, ""),
])
def test_f030_r1_dni_canonico(leido, canonico) -> None:
    assert pn.dni_canonico(leido) == canonico


def test_f030_r1_con_y_sin_cero_dan_lo_mismo() -> None:
    assert pn.dni_canonico("9876543B") == pn.dni_canonico("09876543b")


# ============================== R2 ====================================== #

def _normalizar(*dnis):
    datos = {"cabecera": {"fecha": "15/09/2026"},
             "empleados": [{"nombre": f"Persona {i}", "dni": d,
                            "horas_ordinarias": 8}
                           for i, d in enumerate(dnis)]}
    parte = ParteNormalizer().normalize(datos, email_text="septiembre 2026")
    return [r.trabajador_dni_leido for r in parte.registros]


def test_f030_r2_el_normalizador_guarda_el_dni_canonico() -> None:
    assert _normalizar("9876543-b", "12345678Z", "X1234567L") == \
        ["09876543B", "12345678Z", "X1234567L"]


@pytest.mark.parametrize("vacio", [None, "", "   ", "-", "."])
def test_f030_r2_sin_dni_leido_queda_none(vacio) -> None:
    assert _normalizar(vacio) == [None]


# ============================== R3 ====================================== #

FICHA = EmpleadoRow(ide=10, codigo="E10", nombre="ANA CERO", dni="01234567L",
                    reside=910, empresa=1, fecbaj=0)
OBRA = ObraRow(ide=300, codigo="0300", nombre="Colegio Este", empresa=1)


class _Lookup:
    def fetch_empleados(self):
        return [FICHA]

    def fetch_obras(self):
        return [OBRA]

    def fetch_tipos_hora(self):
        return [TipoHoraRow(ide=1, codigo="HL01", descripcion="Hora",
                            ext=0, pre=None, prenom=None)]

    def fetch_recursos(self):
        return [RecursoRow(ide=910, cif=None, conide=10, empresa=1,
                           fecbaj=0)]

    def fetch_empresas(self):
        return [EmpresaRow(numemp=1, nombre="UNO")]


class _Repo:
    def find_empleado_alias(self, _nombre):
        return None


def test_f030_r3_dni_leido_sin_el_cero_casa_por_dni_con_su_ficha() -> None:
    datos = {"cabecera": {"fecha": "15/09/2026", "obra_numero": "0300"},
             "empleados": [{"nombre": "Nombre Ilegible", "dni": "1234567-L",
                            "horas_ordinarias": 8}]}
    parte = ParteNormalizer().normalize(datos, email_text="septiembre 2026")
    proveedor = SigridMatcherProvider(
        lookup=_Lookup(), empleado_min_score=0.55, obra_min_score=0.55,
        default_hora_normal_cod="HL01", default_hora_extra_cod=None)
    PersistPartePipeline(
        repository=_Repo(), normalizer=ParteNormalizer(),  # type: ignore[arg-type]
        matcher_provider=proveedor, hoy=lambda: date(2026, 9, 15),
    )._match(parte)
    emp = parte.registros[0].empleado
    assert (emp.ide, emp.method, emp.dni, emp.reside) == \
        (10, "dni", "01234567L", 910)
