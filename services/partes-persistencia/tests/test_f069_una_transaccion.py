# tests/test_f069_una_transaccion.py
"""F-069 · R7-R11, R16: la pasada lee una vez y escribe en UNA transaccion.

Antes de F-069, `_pasada` hacia commit del revert (borraba las extras
automaticas y restauraba las bases) y luego, en otras transacciones,
casaba recursos y creaba las extras nuevas. Entre medias un lector veia la
ordinaria entera y sin su extra (obra 0697, 12/11/2026).

`leer_pasada` calcula el revert EN MEMORIA (la «vista revertida») y no
escribe nada; `escribir_pasada` hace revert, casados y splits en un unico
commit. SQLite en memoria con el ORM real; datos sinteticos.
"""
from __future__ import annotations

from sqlalchemy import event

from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests.dobles import FabricaSesionSqlite
from tests.f069_comun import escenario, foto

K = lambda li: ("doc-1", li, 1, 20261001)  # noqa: E731


def _commits(fabrica) -> list[int]:
    """Cuenta los commits de sesion de esa fabrica."""
    cuenta: list[int] = []
    event.listen(fabrica._sessionmaker, "after_commit",
                 lambda _s: cuenta.append(1))
    return cuenta


def _ordenadas(filas: list[dict]) -> list[dict]:
    return sorted(filas, key=lambda f: f["registro_id"])


# ============================ leer_pasada ============================== #

def test_f069_r11_leer_da_lo_mismo_que_revert_y_lectura() -> None:
    hoy = FabricaSesionSqlite()
    escenario(hoy)
    repo_hoy = SqlAlchemyParteRepository(hoy)
    repo_hoy.revert_extras_auto()
    esperado = repo_hoy.fetch_registros_para_recurso()

    nueva = FabricaSesionSqlite()
    escenario(nueva)
    lectura = SqlAlchemyParteRepository(nueva).leer_pasada()

    assert _ordenadas(lectura.registros) == _ordenadas(esperado)


def test_f069_r11_leer_vista_revertida_de_cada_variante() -> None:
    fabrica = FabricaSesionSqlite()
    ids = escenario(fabrica)["doc-1"]
    regs = {f["registro_id"]: f for f in
            SqlAlchemyParteRepository(fabrica).leer_pasada().registros}
    # p0: base restaurada, su extra fuera, la explicita sigue.
    assert (regs[ids[0]]["horas"], regs[ids[0]]["horas_orig"]) == (10.0, None)
    assert ids[1] not in regs and ids[2] in regs
    # p1: intacta.
    assert regs[ids[3]]["horas"] == 6.0
    # p2: protegida por la base registrada.
    assert (regs[ids[4]]["horas"], regs[ids[4]]["horas_orig"]) == (8.0, 10.0)
    assert regs[ids[5]]["congelada_por_pareja"] is True
    # p3: la base respetada por su extra registrada; la duplicada fuera.
    assert regs[ids[6]]["congelada_por_pareja"] is True
    assert regs[ids[6]]["horas"] == 8.0
    assert ids[7] in regs and ids[8] not in regs
    # p4: la base sin horas_orig no protege a su extra (como el revert).
    assert ids[9] in regs and ids[10] not in regs
    assert regs[ids[9]]["congelada_por_pareja"] is False
    # p5: papelera, restaurada igual.
    assert regs[ids[11]]["horas"] == 10.0 and ids[12] not in regs
    # doc-2 inactivo: fuera de la lectura.
    assert all(f["document_id"] == "doc-1" for f in regs.values())


def test_f069_r13_leer_huellas_del_estado_crudo() -> None:
    fabrica = FabricaSesionSqlite()
    ids = escenario(fabrica)["doc-1"]
    huellas = SqlAlchemyParteRepository(fabrica).leer_pasada().huellas
    assert {h[0] for h in huellas[K(0)]} == {ids[0], ids[1]}
    base0 = next(h for h in huellas[K(0)] if h[0] == ids[0])
    assert base0[1:3] == (8.0, 10.0)
    assert {h[0] for h in huellas[K(3)]} == {ids[6], ids[7], ids[8]}
    assert all(k[0] == "doc-1" for k in huellas)


def test_f069_r7_leer_no_escribe_nada() -> None:
    fabrica = FabricaSesionSqlite()
    escenario(fabrica)
    antes = foto(fabrica)
    commits = _commits(fabrica)
    SqlAlchemyParteRepository(fabrica).leer_pasada()
    assert foto(fabrica) == antes
    assert commits == []


def test_f069_r18_fetch_sigue_siendo_la_lectura_cruda() -> None:
    """El contrato de F-037 R9 no cambia: sin revert, la extra sigue."""
    fabrica = FabricaSesionSqlite()
    ids = escenario(fabrica)["doc-1"]
    repo = SqlAlchemyParteRepository(fabrica)
    crudas = {f["registro_id"] for f in repo.fetch_registros_para_recurso()}
    assert ids[1] in crudas and ids[8] in crudas
    vista = {f["registro_id"] for f in repo.leer_pasada().registros}
    assert crudas - vista == {ids[1], ids[8], ids[10], ids[12]}


def test_f069_r18_leer_y_fetch_dan_las_mismas_claves() -> None:
    fabrica = FabricaSesionSqlite()
    escenario(fabrica)
    repo = SqlAlchemyParteRepository(fabrica)
    claves = {frozenset(f) for f in repo.fetch_registros_para_recurso()}
    assert {frozenset(f) for f in repo.leer_pasada().registros} == claves
    assert len(claves) == 1 and "doc_activo" not in next(iter(claves))


# =========================== escribir_pasada =========================== #

def _split(normal_id: int, **kw) -> dict:
    return dict({
        "normal_id": normal_id, "horas_norm": 8.0, "horas_orig": 10.0,
        "extra_horas": 2.0, "hora_ext_ide": 2, "hora_ext_cod": "HE01",
        "hora_ext_desc": "Hora extra", "hora_ext_ext": 1,
        "hora_candef": 8.0}, **kw)


def test_f069_r8_escribir_hace_un_unico_commit() -> None:
    fabrica = FabricaSesionSqlite()
    ids = escenario(fabrica)["doc-1"]
    repo = SqlAlchemyParteRepository(fabrica)
    lectura = repo.leer_pasada()
    commits = _commits(fabrica)
    updates = [{"registro_id": ids[3], "recurso_ide": 501,
                "recurso_cif": None, "hmo_ide": 7, "parte_estado": "ok"}]
    res = repo.escribir_pasada(lectura, updates, [_split(ids[0])])
    assert commits == [1]
    assert res.actualizados == 1 and res.aplicados == 1


def test_f069_r8_escribir_revert_casados_y_splits_juntos() -> None:
    fabrica = FabricaSesionSqlite()
    ids = escenario(fabrica)["doc-1"]
    repo = SqlAlchemyParteRepository(fabrica)
    updates = [{"registro_id": ids[0], "recurso_ide": 501,
                "recurso_cif": "B1", "hmo_ide": 7, "parte_estado": "ok"}]
    repo.escribir_pasada(repo.leer_pasada(), updates, [_split(ids[0])])
    from infrastructure.database.orm_models import ParteRegistroOrm
    with fabrica.create_session() as s:
        ex = s.get(ParteRegistroOrm, ids[1])
        # La extra reutilizada sale de la base YA casada (como `_extra_de`).
        assert (ex.hmo_ide, ex.recurso_cif, ex.horas) == (7, "B1", 2.0)
        # p5 (papelera) y doc-2 (inactivo) revertidos en la misma escritura.
        assert s.get(ParteRegistroOrm, ids[12]) is None
        assert s.get(ParteRegistroOrm, ids[11]).horas == 10.0


def test_f069_r16_escribir_que_lanza_no_deja_nada_a_medias() -> None:
    fabrica = FabricaSesionSqlite()
    ids = escenario(fabrica)["doc-1"]
    repo = SqlAlchemyParteRepository(fabrica)
    lectura = repo.leer_pasada()
    antes = foto(fabrica)
    roto = _split(ids[11])
    del roto["extra_horas"]
    try:
        repo.escribir_pasada(lectura, [], [_split(ids[0]), roto])
    except KeyError:
        pass
    else:  # pragma: no cover - el test exige que lance
        raise AssertionError("escribir_pasada debia lanzar")
    assert foto(fabrica) == antes
