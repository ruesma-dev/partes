# tests/test_f040_elegir_sin_dni.py
"""F-040 · R9: `IndicePersonas.elegir_sin_dni`, por tabla de casos.

El recurso de una linea SIN DNI (ni leido ni de recurso) solo se acepta si
existe, es persona (`res.cla = 1`), no tiene DNI (ni el de su ficha ni
`res.cif`), esta de alta a la fecha (`de_alta`) y es de la empresa (o de
cualquiera si es None). El orden de los motivos es el de `design.md` §3:
`desconocido` -> `con_dni` -> `solo_baja` -> `otra_empresa`.

Todo SINTETICO.
"""
from __future__ import annotations

import pytest

from application.services.seleccion_sigrid import (
    IndicePersonas,
    ResolucionRecurso,
)
from domain.models.sigrid_models import EmpleadoRow, RecursoRow
from tests.dobles import recurso_persona

FECHA = 20260915
EMPRESA = 28
OTRA = 1

FICHAS = [
    EmpleadoRow(ide=10, codigo="E10", nombre="FICHA SIN DNI", dni=None,
                reside=960, empresa=EMPRESA, fecbaj=0),
    EmpleadoRow(ide=11, codigo="E11", nombre="FICHA CON DNI", dni="11111111H",
                reside=961, empresa=EMPRESA, fecbaj=0),
]
RECURSOS = [
    # 950: el caso bueno, sin ficha y sin cif.
    recurso_persona(ide=950, cif=None, conide=None, empresa=EMPRESA, fecbaj=0),
    # 951: cif con espacios solo: sin DNI tras normalizar.
    recurso_persona(ide=951, cif="  ", conide=None, empresa=EMPRESA,
                    fecbaj=None),
    # 952: con cif.
    recurso_persona(ide=952, cif="22222222J", conide=None, empresa=EMPRESA,
                    fecbaj=0),
    # 960: ficha enlazada sin DNI y sin cif: sin DNI.
    recurso_persona(ide=960, cif="", conide=10, empresa=EMPRESA, fecbaj=0),
    # 961: sin cif pero su ficha tiene DNI (F-036 DA1).
    recurso_persona(ide=961, cif=None, conide=11, empresa=EMPRESA, fecbaj=0),
    # 953: de baja justo el dia de la linea.
    recurso_persona(ide=953, cif=None, conide=None, empresa=EMPRESA,
                    fecbaj=FECHA),
    # 954: baja el dia siguiente: de alta.
    recurso_persona(ide=954, cif=None, conide=None, empresa=EMPRESA,
                    fecbaj=FECHA + 1),
    # 955: de otra empresa.
    recurso_persona(ide=955, cif=None, conide=None, empresa=OTRA, fecbaj=0),
    # 956: de baja Y de otra empresa: manda la baja.
    recurso_persona(ide=956, cif=None, conide=None, empresa=OTRA,
                    fecbaj=20210101),
    # 957: de baja Y con DNI: manda el DNI.
    recurso_persona(ide=957, cif="33333333P", conide=None, empresa=OTRA,
                    fecbaj=20210101),
    # 970 y 971: no son persona (consumo, medio), aun sin DNI.
    RecursoRow(ide=970, cif=None, conide=None, empresa=EMPRESA, fecbaj=0,
               cla=0),
    RecursoRow(ide=971, cif=None, conide=None, empresa=EMPRESA, fecbaj=0,
               cla=2),
    # 972: sin clase.
    RecursoRow(ide=972, cif=None, conide=None, empresa=EMPRESA, fecbaj=0),
]


def _indice() -> IndicePersonas:
    return IndicePersonas(FICHAS, RECURSOS)


@pytest.mark.parametrize("ide, empresa, esperado", [
    (950, EMPRESA, (950, "ok")),
    (950, None, (950, "ok")),
    (951, EMPRESA, (951, "ok")),
    (960, EMPRESA, (960, "ok")),
    (954, EMPRESA, (954, "ok")),
    (955, None, (955, "ok")),
    (None, EMPRESA, (None, "desconocido")),
    (999, EMPRESA, (None, "desconocido")),
    (970, EMPRESA, (None, "desconocido")),
    (971, None, (None, "desconocido")),
    (972, EMPRESA, (None, "desconocido")),
    (952, EMPRESA, (None, "con_dni")),
    (961, EMPRESA, (None, "con_dni")),
    (957, EMPRESA, (None, "con_dni")),
    (953, EMPRESA, (None, "solo_baja")),
    (956, EMPRESA, (None, "solo_baja")),
    (955, EMPRESA, (None, "otra_empresa")),
    (950, OTRA, (None, "otra_empresa")),
])
def test_f040_r9_elegir_sin_dni(ide, empresa, esperado) -> None:
    res = _indice().elegir_sin_dni(ide, empresa, FECHA)
    assert isinstance(res, ResolucionRecurso)
    assert (res.ide, res.motivo) == esperado
    assert (res.descartados_baja, res.descartados_otra_empresa) == (0, 0)


def test_f040_r9_la_fecha_es_la_de_la_linea() -> None:
    """953 causa baja el 15: el 14 aun esta de alta."""
    assert _indice().elegir_sin_dni(953, EMPRESA, FECHA - 1).motivo == "ok"
