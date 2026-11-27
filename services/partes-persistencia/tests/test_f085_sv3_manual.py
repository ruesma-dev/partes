# tests/test_f085_sv3_manual.py
"""F-085 · sv3 no pisa el código de hora puesto a mano (R12, R15-R18).

Hasta F-085, `_overwrite` imponía en cada pasada el código del recurso
(`reshor`) aunque la línea lo tuviera elegido a mano en el portal: la CIA
que el revisor puso a la 25012 volvió a HLOF (caso 0678). Desde F-085, con
`hora_match_method = "manual"` solo se pisan la categoría, `hora_candef` y
`recurso_precio_hora` (R15, D8).

- R15, R16, R18: `_overwrite` con el índice de `reshor` hecho a mano.
- R17: `fetch_registros_para_recurso` sobre SQLite en memoria.
- R12: el plan de la pareja de F-037 con la base convertida en incidencia.

Sin red ni PostgreSQL. Datos SINTÉTICOS (recurso 501).
"""
from __future__ import annotations

import logging

import pytest
from application.services.pareja_extra import es_miembro
from application.services.recurso_conciliador import RecursoConciliador
from domain.models.sigrid_models import ReshorRow
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests.dobles import (
    FabricaSesionSqlite,
    LookupFake,
    RepositorioFake,
    recurso_persona,
    sembrar_lineas,
)

RES = 501
ORD = ReshorRow(reside=RES, horide=100, cod="HLOF", res="Hora laborable",
                ext=0, candef=8.0, pre=15.0)
EXT = ReshorRow(reside=RES, horide=200, cod="HEOF", res="Hora extra", ext=1,
                candef=None, pre=20.0)
CIA = ReshorRow(reside=RES, horide=300, cod="CIA", res="Accidente (AT)",
                ext=0, candef=None, pre=0.0)
BY_IDE = {RES: recurso_persona(ide=RES, cif="X", conide=None,
                               restip_res="OFICIAL 1A")}
IDX = {RES: {"ord": ORD, "ext": EXT, "candef": 8.0,
             "incidencias": {"AT": CIA}}}


def _conc() -> RecursoConciliador:
    return RecursoConciliador(repository=RepositorioFake([]),
                              lookup=LookupFake())


def _ov(reg: dict, idx=None) -> dict:
    return _conc()._overwrite(dict(reg, registro_id=reg.get("registro_id", 7)),
                              RES, BY_IDE, IDX if idx is None else idx)


COMUNES = {"categoria": "OFICIAL 1A", "hora_candef": 8.0,
           "recurso_precio_hora": 15.0}


# ------------------------------- R15 -------------------------------- #

@pytest.mark.parametrize("tipo, ide, cod", [
    ("normal", 7, "HEGR"), ("extra", 1, "HL01"), ("AT", 20, "CIA"),
    ("V", 21, "CIV"), ("normal", 100, "HLOF")])
def test_f085_r15_manual_solo_categoria_candef_precio(tipo, ide, cod) -> None:
    out = _ov({"tipo_hora": tipo, "hora_ide": ide, "hora_codigo": cod,
               "hora_match_method": "manual"})
    assert out == COMUNES


def test_f085_r15_manual_sin_reshor_solo_categoria() -> None:
    out = _ov({"tipo_hora": "normal", "hora_ide": 7, "hora_codigo": "HEGR",
               "hora_match_method": "manual"}, idx={})
    assert out == {"categoria": "OFICIAL 1A"}


def test_f085_r15_info_si_el_codigo_del_recurso_difiere(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="application.services."
                                              "recurso_conciliador"):
        _ov({"registro_id": 25012, "tipo_hora": "normal", "hora_ide": 20,
             "hora_codigo": "CIA", "hora_match_method": "manual",
             "empleado_dni": "12345678Z", "nombre": "Nadie"})
    mensajes = [(r.levelname, r.getMessage()) for r in caplog.records
                if "hora_manual_respetada" in r.getMessage()]
    assert mensajes == [(
        "INFO", "[recurso-concil] hora_manual_respetada registro=25012 "
                "recurso=501 manual=20/CIA recurso_propone=100/HLOF")]
    assert "12345678Z" not in caplog.text and "Nadie" not in caplog.text
    assert "DIFERENCIA" not in caplog.text


def test_f085_r15_sin_info_si_coincide(caplog) -> None:
    with caplog.at_level(logging.INFO):
        _ov({"tipo_hora": "normal", "hora_ide": 100, "hora_codigo": "HLOF",
             "hora_match_method": "manual"})
    assert "hora_manual_respetada" not in caplog.text


# ------------------------------- R16 -------------------------------- #

def test_f085_r16_incidencia_convertida_conserva_su_codigo() -> None:
    out = _ov({"tipo_hora": "AT", "hora_ide": 20, "hora_codigo": "CIA",
               "hora_match_method": "manual"})
    assert "hora_ide" not in out and "hora_match_method" not in out


def test_f085_r16_incidencia_sin_manual_toma_la_de_reshor() -> None:
    out = _ov({"tipo_hora": "AT", "hora_ide": 20, "hora_codigo": "CIA",
               "hora_match_method": "incidencia"})
    assert (out["hora_ide"], out["hora_codigo"], out["hora_match_method"]) \
        == (300, "CIA", "recurso_difiere")


# ------------------------------- R18 -------------------------------- #

#: Lo que `_overwrite` daba en la base de la rama (ae0fac7) para líneas
#: sin `manual` (casos de los tests de F-023/F-030 y de esta spec).
CASOS_R18 = [
    ({"tipo_hora": "normal", "hora_ide": None, "hora_codigo": None},
     dict(COMUNES, hora_ide=100, hora_codigo="HLOF",
          hora_descripcion="Hora laborable", hora_ext=0,
          hora_match_method="recurso")),
    ({"tipo_hora": "normal", "hora_ide": 100, "hora_codigo": "HLOF"},
     dict(COMUNES, hora_ide=100, hora_codigo="HLOF",
          hora_descripcion="Hora laborable", hora_ext=0,
          hora_match_method="recurso")),
    ({"tipo_hora": "normal", "hora_ide": 20, "hora_codigo": "CIA",
      "hora_match_method": "recurso"},
     dict(COMUNES, hora_ide=100, hora_codigo="HLOF",
          hora_descripcion="Hora laborable", hora_ext=0,
          hora_match_method="recurso_difiere")),
    ({"tipo_hora": "extra", "hora_ide": 1, "hora_codigo": "HL01",
      "hora_match_method": None},
     dict(COMUNES, hora_ide=200, hora_codigo="HEOF",
          hora_descripcion="Hora extra", hora_ext=1,
          hora_match_method="recurso_difiere")),
    ({"tipo_hora": "V", "hora_ide": 21, "hora_codigo": "CIV"},
     dict(COMUNES)),
    ({"tipo_hora": "", "hora_ide": 100},
     dict(COMUNES, hora_ide=100, hora_codigo="HLOF",
          hora_descripcion="Hora laborable", hora_ext=0,
          hora_match_method="recurso")),
    ({"tipo_hora": "normal", "hora_ide": 9, "hora_match_method": "MANUAL"},
     dict(COMUNES, hora_ide=100, hora_codigo="HLOF",
          hora_descripcion="Hora laborable", hora_ext=0,
          hora_match_method="recurso_difiere")),
]


@pytest.mark.parametrize("reg, esperado", CASOS_R18)
def test_f085_r18_sin_manual_como_la_base(reg, esperado) -> None:
    assert _ov(reg) == esperado


def test_f085_r18_sin_reshor_y_sin_manual() -> None:
    assert _ov({"tipo_hora": "normal", "hora_ide": 1}, idx={}) == {
        "categoria": "OFICIAL 1A"}


# ------------------------------- R17 -------------------------------- #

def test_f085_r17_fetch_trae_hora_match_method() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_lineas(fabrica, [{"horas": 8.0}, {"horas": 8.0}])
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, ids[0]).hora_match_method = "manual"
        s.commit()
    filas = {f["registro_id"]: f for f in
             SqlAlchemyParteRepository(fabrica).fetch_registros_para_recurso()}
    assert filas[ids[0]]["hora_match_method"] == "manual"
    assert filas[ids[1]]["hora_match_method"] is None


# ------------------------------- R12 -------------------------------- #
# La base convertida (AT, horas y `horas_orig` nulos) deja de ser miembro
# de la pareja: la pasada de siempre (`leer_pasada`, F-037/F-069) borra su
# extra automatica no congelada y ya no la restaura ni la vuelve a partir.

def _pareja(fabrica, *, estado_extra=None, explicita=False) -> list[int]:
    ids = sembrar_lineas(fabrica, [
        {"tipo": "normal", "horas": 8.0, "line_index": 0,
         "empleado_line_no": 1},
        {"tipo": "extra", "horas": 2.0, "extra_auto": not explicita,
         "estado": estado_extra, "line_index": 0, "empleado_line_no": 1}])
    with fabrica.create_session() as s:           # la conversion de sv4
        base = s.get(ParteRegistroOrm, ids[0])
        base.es_incidencia, base.tipo_hora = True, "AT"
        base.incidencia_codigo, base.horas, base.horas_orig = "AT", None, None
        base.hora_codigo, base.hora_match_method = "CIA", "manual"
        s.commit()
    return ids


def _vista(fabrica) -> dict[int, dict]:
    lectura = SqlAlchemyParteRepository(fabrica).leer_pasada()
    return {f["registro_id"]: f for f in lectura.registros}


def test_f085_r12_es_miembro_la_base_convertida_no() -> None:
    assert es_miembro(extra_auto=False, tipo_hora="AT") is False


def test_f085_r12_la_extra_automatica_de_la_base_convertida_se_borra() -> None:
    fabrica = FabricaSesionSqlite()
    base, extra = _pareja(fabrica)
    vista = _vista(fabrica)
    assert extra not in vista
    assert (vista[base]["tipo_hora"], vista[base]["horas"],
            vista[base]["horas_orig"]) == ("AT", None, None)


@pytest.mark.parametrize("kw", [{"explicita": True},
                                {"estado_extra": "registrado"}])
def test_f085_r12_extra_explicita_o_congelada_se_queda(kw) -> None:
    fabrica = FabricaSesionSqlite()
    base, extra = _pareja(fabrica, **kw)
    vista = _vista(fabrica)
    assert extra in vista and vista[extra]["horas"] == 2.0
    assert vista[base]["horas"] is None
