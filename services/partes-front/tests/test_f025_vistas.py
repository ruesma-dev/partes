# tests/test_f025_vistas.py
"""F-025 · el conflicto se ve en las vistas de obra y de trabajador
(R15-R19), no se rechaza ninguna edicion (R20) y sin tabla todo sigue
como antes (R23).

Sin red ni PostgreSQL: SQLite en memoria con el ORM, `TestClient` sobre
el HTML renderizado y, con `node` instalado, las funciones puras de
`static/app.js`. Personas, DNIs y obras SINTETICOS.
"""
from __future__ import annotations

import pytest
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite
from tests.test_f025_aprobacion import DNI_B, OBRA_20, sembrar
from tests.test_f025_deteccion import TABLA

MARZO = "2026-03"


def _escenario(fabrica) -> dict[str, list[int]]:
    """Persona A (emp-77): dia 02 con M en la obra 20 y horas en la 10
    (bloqueo); dia 03 con FJ y 2 h extra en la 10 (aviso); dia 04 normal.
    Persona B (emp-88): dia 02 normal en la obra 10."""
    return {
        "inc_m": sembrar(fabrica, [{"inc": "M"}], doc="v-m", obra=OBRA_20),
        "bloq": sembrar(fabrica, [{"horas": 8.0},
                                  {"tipo": "extra", "horas": 1.0}],
                        doc="v-bloq"),
        "aviso": sembrar(fabrica, [{"inc": "FJ"}, {"horas": 6.0},
                                   {"tipo": "extra", "horas": 2.0}],
                         doc="v-aviso", fecha="2026-03-03"),
        "libre": sembrar(fabrica, [{"horas": 8.0}], doc="v-libre",
                         fecha="2026-03-04"),
        "otra": sembrar(fabrica, [{"horas": 8.0}], doc="v-otra", dni=DNI_B,
                        empleado_ide=88, nombre="Persona B"),
    }


def _repo():
    fabrica = FabricaSesionSqlite()
    ids = _escenario(fabrica)
    return ParteReviewRepository(fabrica), fabrica, ids


def _celda(detalle, worker_key: str, dia: str):
    fila = next(r for r in detalle.rows if r.worker_key == worker_key)
    return next(c for c in fila.cells if c.date_iso == dia)


def _niveles(registros) -> dict[int, str | None]:
    return {v.id: v.incompat_nivel for v in registros}


# ===================================================================== #
# T6 · repositorio de las vistas
# ===================================================================== #

def test_f025_r15_repo_celdas_de_la_matriz_de_obra() -> None:
    repo, _f, _ids = _repo()
    det = repo.get_obra("obr-10", period_key=MARZO, incidencias=TABLA)
    bloq = _celda(det, "emp-77", "2026-03-02")
    assert bloq.incompat_nivel == "bloqueo"
    assert "Maternidad/Paternidad (M) es de día completo" in \
        bloq.incompat_motivo
    aviso = _celda(det, "emp-77", "2026-03-03")
    assert aviso.incompat_nivel == "aviso"
    assert "(FJ) y 2 h extra" in aviso.incompat_motivo
    for wk, dia in (("emp-77", "2026-03-04"), ("emp-88", "2026-03-02"),
                    ("emp-77", "2026-03-05")):
        celda = _celda(det, wk, dia)
        assert (celda.incompat_nivel, celda.incompat_motivo) == (None, None)


def test_f025_r18_repo_la_incidencia_en_otra_obra_marca_las_dos() -> None:
    repo, _f, ids = _repo()
    det20 = repo.get_obra("obr-20", period_key=MARZO, incidencias=TABLA)
    assert _celda(det20, "emp-77", "2026-03-02").incompat_nivel == "bloqueo"
    assert _niveles(det20.registros) == {ids["inc_m"][0]: "bloqueo"}
    det10 = repo.get_obra("obr-10", period_key=MARZO, incidencias=TABLA)
    niveles = _niveles(det10.registros)
    assert [niveles[i] for i in ids["bloq"]] == ["bloqueo", "bloqueo"]


def test_f025_r17_repo_lineas_de_la_vista_de_obra() -> None:
    repo, _f, ids = _repo()
    det = repo.get_obra("obr-10", period_key=MARZO, incidencias=TABLA)
    niveles = _niveles(det.registros)
    assert [niveles[i] for i in ids["aviso"]] == ["aviso"] * 3
    assert niveles[ids["libre"][0]] is None
    assert niveles[ids["otra"][0]] is None
    motivos = {v.id: v.incompat_motivo for v in det.registros}
    assert "(M)" in motivos[ids["bloq"][0]]
    assert motivos[ids["libre"][0]] is None


def test_f025_r17_r18_repo_lineas_de_la_vista_de_trabajador() -> None:
    repo, _f, ids = _repo()
    det = repo.get_worker("emp-77", incidencias=TABLA)
    niveles = _niveles(det.registros)
    assert [niveles[i] for i in ids["inc_m"] + ids["bloq"]] == \
        ["bloqueo"] * 3
    assert [niveles[i] for i in ids["aviso"]] == ["aviso"] * 3
    assert niveles[ids["libre"][0]] is None
    otra = repo.get_worker("emp-88", incidencias=TABLA)
    assert _niveles(otra.registros) == {ids["otra"][0]: None}


def test_f025_r23_repo_vistas_sin_tabla_como_antes() -> None:
    repo, _f, _ids = _repo()
    det = repo.get_obra("obr-10", period_key=MARZO)
    assert {(c.incompat_nivel, c.incompat_motivo)
            for r in det.rows for c in r.cells} == {(None, None)}
    assert {v.incompat_nivel for v in det.registros} == {None}
    assert {v.incompat_nivel
            for v in repo.get_worker("emp-77").registros} == {None}
