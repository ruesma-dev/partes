# tests/test_f069_concurrencia_sv4.py
"""F-069 · R13, R14: sv4 cambia una pareja entre la lectura y la escritura.

La pasada lee (`leer_pasada`), consulta Sigrid y calcula durante segundos,
y luego escribe (`escribir_pasada`). Si entre medias el portal edito una
pareja (horas, papelera, la encolo para Sigrid, aprobo el parte, borro o
anadio una fila), los splits calculados ya no valen para ella: esa pareja
no se toca en esta pasada y se recalcula en la siguiente. Las demas se
escriben como siempre.

SQLite en memoria con el ORM real; datos sinteticos.
"""
from __future__ import annotations

import logging

import pytest

from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests.dobles import FabricaSesionSqlite
from tests.f069_comun import base, extra, foto, sembrar


def _split(normal_id: int, ext: float = 2.5) -> dict:
    return {"normal_id": normal_id, "horas_norm": 10.0 - ext,
            "horas_orig": 10.0, "extra_horas": ext, "hora_ext_ide": 2,
            "hora_ext_cod": "HE01", "hora_ext_desc": "Hora extra",
            "hora_ext_ext": 1, "hora_candef": 8.0}


def _upd(rid: int) -> dict:
    return {"registro_id": rid, "recurso_ide": 501, "recurso_cif": "B9",
            "hmo_ide": 77, "parte_estado": "ok"}


def _cambiar_registro(_fila: int = 0, **campos):
    def _hacer(s, ids):
        r = s.get(ParteRegistroOrm, ids[_fila])
        for k, v in campos.items():
            setattr(r, k, v)
    return _hacer


def _aprobar(s, _ids):
    s.get(ParteDocumentOrm, "doc-1").approved = True


def _desactivar(s, _ids):
    s.get(ParteDocumentOrm, "doc-1").is_active = False


def _borrar_extra(s, ids):
    s.delete(s.get(ParteRegistroOrm, ids[1]))


def _miembro_nuevo(s, _ids):
    s.add(ParteRegistroOrm(
        document_id="doc-1", line_index=0, empleado_line_no=1,
        fecha_int=20261001, tipo_hora="extra", extra_auto=True, horas=1.0))


def _base_nueva(s, _ids):
    s.add(ParteRegistroOrm(
        document_id="doc-1", line_index=0, empleado_line_no=1,
        fecha_int=20261001, tipo_hora="normal", horas=1.0))


CAMBIOS = {
    "horas": _cambiar_registro(horas=7.0),
    "horas_orig": _cambiar_registro(horas_orig=11.0),
    "tipo_hora": _cambiar_registro(tipo_hora="V"),
    "extra_auto": _cambiar_registro(_fila=1, extra_auto=False),
    "encolado": _cambiar_registro(_fila=1, sigrid_estado="encolado"),
    "registrado_base": _cambiar_registro(sigrid_estado="registrado"),
    "error": _cambiar_registro(_fila=1, sigrid_estado="error"),
    "papelera": _cambiar_registro(deleted_at_utc="2026-11-12T09:21"),
    "parte_aprobado": _aprobar,
    "parte_inactivo": _desactivar,
    "fila_borrada": _borrar_extra,
    "miembro_nuevo": _miembro_nuevo,
    "base_nueva": _base_nueva,
}


def _preparar(fabrica):
    p0 = sembrar(fabrica, [base(8.0, 10.0), extra(2.0)], document_id="doc-1")
    p1 = sembrar(fabrica, [base(8.0, 10.0), extra(2.0)], document_id="doc-2")
    return p0, p1


@pytest.mark.parametrize("cambio", sorted(CAMBIOS))
def test_f069_r13_pareja_cambiada_no_se_toca(cambio, caplog) -> None:
    fabrica = FabricaSesionSqlite()
    p0, p1 = _preparar(fabrica)
    repo = SqlAlchemyParteRepository(fabrica)
    lectura = repo.leer_pasada()
    # sv4, entre la lectura y la escritura:
    with fabrica.create_session() as s:
        CAMBIOS[cambio](s, p0)
        s.commit()
    antes = [f for f in foto(fabrica) if f[1] == "doc-1"]

    with caplog.at_level(logging.WARNING):
        res = repo.escribir_pasada(lectura, [_upd(p0[0]), _upd(p1[0])],
                                   [_split(p0[0]), _split(p1[0])])

    # La pareja cambiada, tal como la dejo sv4 (ni revert, ni casado, ni
    # split); la otra, escrita.
    assert [f for f in foto(fabrica) if f[1] == "doc-1"] == antes
    assert res.parejas_cambiadas == 1
    assert (res.actualizados, res.aplicados, res.reutilizadas) == (1, 1, 1)
    with fabrica.create_session() as s:
        assert s.get(ParteRegistroOrm, p1[1]).horas == 2.5
        assert s.get(ParteRegistroOrm, p1[0]).hmo_ide == 77
    avisos = [r.getMessage() for r in caplog.records
              if "pareja cambiada" in r.getMessage()]
    assert len(avisos) == 1
    assert "documento=doc-1" in avisos[0] and "linea=0" in avisos[0]
    assert "12345678Z" not in caplog.text


def test_f069_r13_sin_cambios_no_hay_parejas_cambiadas(caplog) -> None:
    fabrica = FabricaSesionSqlite()
    p0, p1 = _preparar(fabrica)
    repo = SqlAlchemyParteRepository(fabrica)
    with caplog.at_level(logging.WARNING):
        res = repo.escribir_pasada(repo.leer_pasada(), [],
                                   [_split(p0[0]), _split(p1[0])])
    assert res.parejas_cambiadas == 0 and res.reutilizadas == 2
    assert "pareja cambiada" not in caplog.text


def test_f069_r13_cambio_en_un_campo_ajeno_a_la_huella_no_cuenta() -> None:
    fabrica = FabricaSesionSqlite()
    p0, _p1 = _preparar(fabrica)
    repo = SqlAlchemyParteRepository(fabrica)
    lectura = repo.leer_pasada()
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, p0[0]).partida = "otra partida"
        s.commit()
    res = repo.escribir_pasada(lectura, [], [_split(p0[0])])
    assert res.parejas_cambiadas == 0 and res.reutilizadas == 1


def test_f069_r13_float_de_ida_y_vuelta_no_es_un_cambio() -> None:
    fabrica = FabricaSesionSqlite()
    p0, _p1 = _preparar(fabrica)
    repo = SqlAlchemyParteRepository(fabrica)
    lectura = repo.leer_pasada()
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, p0[0]).horas = 8.0 + 1e-9
        s.commit()
    assert repo.escribir_pasada(lectura, [], [_split(p0[0])]
                                ).parejas_cambiadas == 0


def test_f069_r13_sin_lectura_no_se_comprueba_nada() -> None:
    fabrica = FabricaSesionSqlite()
    p0, _p1 = _preparar(fabrica)
    repo = SqlAlchemyParteRepository(fabrica)
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, p0[0]).horas = 7.0
        s.commit()
    res = repo.escribir_pasada(None, [], [_split(p0[0])])
    assert res.parejas_cambiadas == 0 and res.reutilizadas == 1


def test_f069_r14_congelada_al_leer_y_al_escribir_no_cuenta_como_cambio(
) -> None:
    """Congelada ya en la lectura: el plan la respeta y no es «cambiada»."""
    fabrica = FabricaSesionSqlite()
    sembrar(fabrica, [base(8.0, 10.0), extra(2.0, "registrado")],
            document_id="doc-1")
    repo = SqlAlchemyParteRepository(fabrica)
    antes = foto(fabrica)
    res = repo.escribir_pasada(repo.leer_pasada(), [], [])
    assert res.parejas_cambiadas == 0 and foto(fabrica) == antes
