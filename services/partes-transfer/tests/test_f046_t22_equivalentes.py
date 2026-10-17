# tests/test_f046_t22_equivalentes.py
"""F-046 T22 · demostracion ejecutable de los mutantes EQUIVALENTES de sv5
(`progress/mutacion_F-046.md`, seccion «Equivalentes»; pendientes de que
el humano los acepte).

Un mutante equivalente no se puede matar: la linea mutada solo cambia el
resultado en una situacion que el codigo no alcanza. Cada test de aqui
fija ESA imposibilidad (pasa con el original y con el mutante, por
construccion), de modo que si un cambio futuro la hiciera alcanzable, el
test lo diria. Datos SINTETICOS.
"""
from __future__ import annotations

import pytest
from application.services.reajuste_lineas import (
    MOTIVO_BASE_NO_EDITABLE,
    MOTIVO_NO_REGISTRABLE,
    MOTIVO_OTRA_OBRA,
    MOTIVO_PARCIAL,
    MOTIVO_PARTE_NO_EN_REGISTRO,
    veredicto_nueva,
)
from application.services.reglas_registro import ReglasRegistro
from domain.models.registro_models import (
    AccionLinea,
    HoraRecurso,
    LineaEntrada,
    OpReajuste,
    VeredictoReajuste,
)
from tests.test_f046_reajuste_pipeline import (
    HE,
    HL,
    NUEVA,
    _linea,
    _nueva,
    _pipe,
    _sigrid,
)


# ---- reajuste_pipeline.py:182 y :316 (`hmoide or 0` -> `or 1`) ---- #

@pytest.mark.parametrize("can_base,motivo", [
    (8.0, f"{MOTIVO_BASE_NO_EDITABLE}: {MOTIVO_PARTE_NO_EN_REGISTRO}"),
    (5.5, MOTIVO_PARCIAL),
])
def test_f046_t22_eq_base_sin_parte_nunca_llega_a_misma_obra_ni_al_lote(
        can_base, motivo):
    """`misma_obra` (:182) solo decide si la base es editable y NO esta ya
    aplicada, y eso exige su parte En registro, o sea `hmoide` no nulo;
    `_lote` (:316) solo ve nuevas editables. Con la base sin parte la
    nueva se rechaza ANTES, sea cual sea `misma_obra`: el `or 0` de esas
    dos lineas nunca se evalua con `hmoide` nulo."""
    cli = _sigrid([_linea(4001, 11, can_base, hmoide=None)])
    pipe, _ = _pipe(cli)
    r = pipe.ejecutar([OpReajuste(11, despues=5.5, antes=8.0), _nueva()],
                      usuario="admin@test")
    v = next(v for v in r.veredictos if v.registro_id == NUEVA)
    assert not v.editable and v.motivo.startswith(motivo)
    assert cli.lotes == []


# ---- reajuste_pipeline.py:322 (`assert a and destino` -> `or`) ---- #

def _base_ok() -> VeredictoReajuste:
    return VeredictoReajuste(11, editable=True)


def test_f046_t22_eq_nueva_editable_exige_accion_escribir_y_misma_obra():
    """El `assert` de :322 documenta un invariante: una nueva solo es
    editable con accion `escribir` (no None) y `misma_obra`, que en
    `_evaluar` exige `p.destino is not None`. Con `and` o con `or` la
    condicion es siempre cierta en `_lote`."""
    op = _nueva()
    escribir = AccionLinea(registro_id=NUEVA, accion="escribir", ano=2026,
                           mes=10, fecha_int=20261014, hora_ide=HE)
    sin_accion = veredicto_nueva(op, existente=None, base=_base_ok(),
                                 accion=None, choques=[], misma_obra=True)
    otra_obra = veredicto_nueva(op, existente=None, base=_base_ok(),
                                accion=escribir, choques=[],
                                misma_obra=False)
    assert not sin_accion.editable
    assert sin_accion.motivo.startswith(MOTIVO_NO_REGISTRABLE)
    assert (otra_obra.editable, otra_obra.motivo) == (False,
                                                      MOTIVO_OTRA_OBRA)
    assert veredicto_nueva(op, existente=None, base=_base_ok(),
                           accion=escribir, choques=[],
                           misma_obra=True).editable


# ---- reajuste_pipeline.py:150 (`accion.hora_ide or 0` -> `or 1`) ---- #

def test_f046_t22_eq_toda_extra_escribible_lleva_codigo_de_hora():
    """`_choques` solo recibe acciones `escribir`; la de una extra lleva
    `hora_ide = HoraRecurso.horide` (el `auxhor.ide` de Sigrid, siempre
    >= 1). El `or 0` de `accion.hora_ide` nunca ve un valor nulo; sin
    codigo de hora extra la accion no es `escribir`."""
    linea = LineaEntrada(registro_id=NUEVA, fecha_int=20261014,
                         recurso_ide=501, tipo_hora="extra", horas=2.5)
    con = ReglasRegistro({501: [HoraRecurso(HL, "HL01", None, 20.0,
                                            defecto=True),
                                HoraRecurso(HE, "HE01", None, 25.0)]})
    sin = ReglasRegistro({501: [HoraRecurso(HL, "HL01", None, 20.0,
                                            defecto=True)]})
    a = con.decidir(linea)
    assert a.accion == "escribir" and a.hora_ide == HE
    assert sin.decidir(linea).accion != "escribir"

