# tests/test_f052_r14_r26_solo_lectura.py
"""F-052 en sv4: lo que `sincronizar` y `aplicar` NO hacen (R14 y R26).

- R14: el resultado es efímero (DA5). `sincronizar` solo LEE del
  repositorio (las líneas del ámbito, las registradas que comprobar y
  `donde_estan`); no guarda nada en la base `partes` y cada llamada
  vuelve a leer. En seco (DA18) tampoco llama a la comprobación de F-024
  (la única que escribe, `borrado_sigrid`).
- R26: ninguna de las 5 acciones de `aplicar`, en seco o fuera de él,
  llama a sv5 fuera de `sincronizar_leer` y `comprobar` (las dos lecturas):
  nada escribe en Sigrid.

Espías sobre los dobles de `test_f052_sincronizar_ambito.py`: apuntan
cualquier método que se use, también uno que hoy no exista. Sin red ni base.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest
from application.services.sincronizar_ambito import ACCIONES
from tests.test_f052_sincronizar_ambito import (
    AMBITO_OBRA,
    ComprobacionFalsa,
    P,
    RepoAcciones,
    S,
    Sv5Falso,
    _firmas,
    _pedir,
    _sync,
)

#: R14: lo único que `sincronizar` puede pedir al repositorio.
LECTURAS_REPO = {"lineas_para_sincronizar", "registrados_para_comprobar",
                 "donde_estan"}

#: R26: lo único que sv4 puede pedir a sv5 desde F-052 (las dos leen).
LECTURAS_SV5 = {"sincronizar_leer", "comprobar"}

FUENTE = (Path(__file__).resolve().parents[1] / "application" / "services"
          / "sincronizar_ambito.py")


class RepoEspia:
    """Envuelve un `RepoAcciones` y apunta el nombre de cada método que se
    pide, exista o no en el doble."""

    def __init__(self, real: RepoAcciones) -> None:
        self._real = real
        self.usados: list[str] = []

    def __getattr__(self, nombre):
        self.usados.append(nombre)
        return getattr(self._real, nombre)


class Sv5Espia(Sv5Falso):
    """`Sv5Falso` que, además, apunta (sin reventar) cualquier otro método:
    un `except` del código no puede tapar la llamada."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.otras: list[str] = []

    def __getattr__(self, nombre):
        if nombre.startswith("__"):
            raise AttributeError(nombre)
        self.otras.append(nombre)
        return lambda *a, **k: {"ok": True}


def _escenario_r14():
    """Una de cada: `registrado` que Sigrid borró (R10), pendiente,
    nuestra sin pareja en la papelera (R12), manual, igual y distinta."""
    portal = [P(1), P(2, ""), P(3), P(4)]
    sigrid = [S(9003, registro_id=3), S(9004, registro_id=4, can=6.0),
              S(9005, registro_id=5), S(9100, "manual")]
    return RepoAcciones(portal, donde={5: "papelera"}), sigrid


# --------------------------------- R14 ----------------------------------- #

def test_f052_r14_seco_sincronizar_solo_lee_el_repositorio() -> None:
    real, sigrid = _escenario_r14()
    repo = RepoEspia(real)
    comp = ComprobacionFalsa(borradas=[1])
    sv5 = Sv5Espia(sigrid, borradas={1})
    r = _sync(repo, sv5, comprobacion=comp, seco=True).sincronizar(
        AMBITO_OBRA)
    assert r.status == 200
    clases = {i["registro_id"]: i["clase"] for i in r.cuerpo["items"]}
    assert clases == {1: "borrada_en_sigrid", 2: "pendiente", 3: "igual",
                      4: "distinta", 5: "solo_sigrid_nuestra", None:
                      "solo_sigrid_manual"}
    assert set(repo.usados) == LECTURAS_REPO       # las tres, y nada más
    assert real.escrituras == []
    assert comp.llamadas == []                     # DA18: ni F-024
    assert sv5.otras == []


def test_f052_r14_fuera_de_seco_el_repositorio_tampoco_guarda_nada() -> None:
    """Fuera de seco la única escritura es la de R10, y la hace la
    comprobación de F-024; el resultado de la comparación no se guarda."""
    real, sigrid = _escenario_r14()
    repo = RepoEspia(real)
    comp = ComprobacionFalsa(borradas=[1])
    r = _sync(repo, Sv5Espia(sigrid), comprobacion=comp).sincronizar(
        AMBITO_OBRA)
    assert r.status == 200 and r.cuerpo["marcadas_borrado_sigrid"] == [1]
    assert set(repo.usados) <= LECTURAS_REPO
    assert real.escrituras == []
    assert [c[0] for c in comp.llamadas] == [[1]]


def test_f052_r14_cada_sincronizacion_vuelve_a_leer() -> None:
    """Efímero (DA5): nada se reutiliza de una sincronización a otra."""
    real, sigrid = _escenario_r14()
    repo = RepoEspia(real)
    sv5 = Sv5Espia(sigrid, borradas={1})
    sync = _sync(repo, sv5, seco=True)
    primera = sync.sincronizar(AMBITO_OBRA).cuerpo
    real.portal[1] = P(2, "error")                 # cambia entre medias
    segunda = sync.sincronizar(AMBITO_OBRA).cuerpo
    assert len(sv5.leer) == 2
    assert repo.usados.count("lineas_para_sincronizar") == 2
    firma_2 = [{i["registro_id"]: i["firma"] for i in c["items"]}[2]
               for c in (primera, segunda)]
    assert firma_2[0] != firma_2[1]               # ve la línea nueva
    assert real.escrituras == []


# --------------------------------- R26 ----------------------------------- #

#: Por acción: (portal, Sigrid, donde) con una línea a la que se aplica.
#: Todas llevan además la 2, `registrado` sin pareja: obliga a R10 (en
#: seco, el veredicto de sv5; fuera, `comprobar_ids`).
ESCENARIOS = {
    "marcar_registrada": ([P(1, "error")], [S(9001, registro_id=1)], {}),
    "traer_de_sigrid": ([P(1)], [S(9001, registro_id=1, can=6.0)], {}),
    "a_papelera": ([P(1, "borrado_sigrid")], [], {}),
    "reaprobar": ([P(1, "")], [], {}),
    "restaurar": ([], [S(9001, registro_id=1)], {1: "papelera"}),
}


def test_f052_r26_los_escenarios_cubren_todas_las_acciones() -> None:
    assert set(ESCENARIOS) == set(ACCIONES)


@pytest.mark.parametrize("seco", [True, False])
@pytest.mark.parametrize("accion", sorted(ESCENARIOS))
def test_f052_r26_aplicar_solo_lee_de_sv5(accion, seco) -> None:
    portal, sigrid, donde = ESCENARIOS[accion]
    repo = RepoAcciones(list(portal) + [P(2)], donde=donde)
    sv5 = Sv5Espia(list(sigrid), borradas={2})
    comp = ComprobacionFalsa(borradas=[2])
    sync = _sync(repo, sv5, comprobacion=comp, seco=seco)
    r = sync.aplicar(accion, AMBITO_OBRA, _pedir(_firmas(sync), 1),
                     actor="ana", recalcular=lambda ids, quien: ("pedido",
                                                                 "p-1"))
    assert r.status == 200 and r.cuerpo["aplicados"] == [1], r.cuerpo
    assert sv5.otras == []
    assert len(sv5.leer) == 2                     # sincronizar + re-sync
    if seco:
        assert sv5.comprobaciones and comp.llamadas == []
    else:
        assert sv5.comprobaciones == [] and comp.llamadas


def test_f052_r26_el_orquestador_solo_nombra_lecturas_de_sv5() -> None:
    """Guardia estática: en `sincronizar_ambito.py`, `self._sv5` solo se usa
    para `sincronizar_leer` y `comprobar` (tampoco por un alias)."""
    arbol = ast.parse(FUENTE.read_text(encoding="utf-8"))
    usos = {n.attr for n in ast.walk(arbol)
            if isinstance(n, ast.Attribute)
            and isinstance(n.value, ast.Attribute)
            and n.value.attr == "_sv5"}
    assert usos == LECTURAS_SV5
    alias = [n for n in ast.walk(arbol)
             if isinstance(n, ast.Assign)
             and isinstance(n.value, ast.Attribute)
             and n.value.attr == "_sv5"]
    assert alias == []
