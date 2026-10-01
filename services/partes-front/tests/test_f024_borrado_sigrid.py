# tests/test_f024_borrado_sigrid.py
"""F-024 · estado `borrado_sigrid` en el portal (R10-R16, R22-R24).

Sin red ni PostgreSQL: SQLite en memoria con el MISMO ORM (dobles.py) y
dobles del cliente de sv5. Codigos de parte, `ide` y recursos sinteticos.
"""
from __future__ import annotations

import pytest
from application.services.congelacion import (
    ESTADO_BORRADO_SIGRID,
    ESTADOS_CONGELANTES,
    MOTIVO_LINEA_REGISTRADA,
    es_registrado,
    motivo_congelacion_documento,
    motivo_congelacion_linea,
)
from infrastructure.database import parte_repository as repo_mod
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite, estados_sigrid, sembrar_parte

PARTE = "PT26/09001"
HMO = 7001


def _poner(fabrica, rid: int, **campos) -> None:
    with fabrica.create_session() as s:
        reg = s.get(ParteRegistroOrm, rid)
        for k, v in campos.items():
            setattr(reg, k, v)
        s.commit()


def _leer(fabrica, rid: int) -> ParteRegistroOrm:
    with fabrica.create_session() as s:
        reg = s.get(ParteRegistroOrm, rid)
        s.expunge(reg)
        return reg


def _montar(estados: list[str | None], **kw):
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, [{"estado": e} for e in estados], **kw)
    return ParteReviewRepository(fabrica), fabrica, ids


# ===================================================================== #
# T5 · congelacion (R13), ESTADOS_EN_VUELO (R15) y motivo (R16)
# ===================================================================== #

def test_f024_r10_congel_el_estado_cabe_en_la_columna() -> None:
    assert ESTADO_BORRADO_SIGRID == "borrado_sigrid"
    assert len(ESTADO_BORRADO_SIGRID) <= 16
    assert ParteRegistroOrm.__table__.c.sigrid_estado.type.length == 16


def test_f024_r13_congel_borrado_sigrid_no_congela_la_linea() -> None:
    for estado in (ESTADO_BORRADO_SIGRID, " Borrado_Sigrid "):
        assert motivo_congelacion_linea(
            doc_aprobado=False, sigrid_estado=estado) is None
    assert ESTADO_BORRADO_SIGRID not in ESTADOS_CONGELANTES
    assert tuple(ESTADOS_CONGELANTES) == ("encolado", "registrado")


def test_f024_r13_congel_borrado_sigrid_no_congela_el_documento() -> None:
    assert motivo_congelacion_documento(
        aprobado=False, estados_lineas=[ESTADO_BORRADO_SIGRID, None]) is None


def test_f024_r13_congel_el_parte_aprobado_sigue_mandando() -> None:
    """`borrado_sigrid` no descongela un parte aprobado (F-004 R1)."""
    assert motivo_congelacion_linea(
        doc_aprobado=True, sigrid_estado=ESTADO_BORRADO_SIGRID) is not None


def test_f024_r13_congel_borrado_sigrid_no_bloquea_el_borrado_definitivo() -> None:
    assert es_registrado(ESTADO_BORRADO_SIGRID) is False
    repo, fabrica, ids = _montar([ESTADO_BORRADO_SIGRID])
    assert repo.hard_delete_registro(registro_id=ids[0]) is True
    with fabrica.create_session() as s:
        assert s.get(ParteRegistroOrm, ids[0]) is None


def test_f024_r13_congel_la_linea_borrada_en_sigrid_se_puede_editar() -> None:
    repo, fabrica, ids = _montar([ESTADO_BORRADO_SIGRID])
    assert repo.update_registro(registro_id=ids[0], horas=6.0) is True
    assert _leer(fabrica, ids[0]).horas == 6.0


def test_f024_r13_congel_la_vista_no_pinta_candado() -> None:
    repo, _f, ids = _montar([ESTADO_BORRADO_SIGRID])
    detalle = repo.get_parte("doc-f004")
    assert detalle.congelado_doc is None


def test_f024_r15_vuelo_borrado_sigrid_no_es_veredicto_final() -> None:
    assert ESTADO_BORRADO_SIGRID in repo_mod.ESTADOS_EN_VUELO


def test_f024_r15_vuelo_ya_registrada_devuelve_la_linea_a_registrado() -> None:
    repo, fabrica, ids = _montar([ESTADO_BORRADO_SIGRID, "omitido"])
    repo.marcar_registros_sigrid(escritas=[], omitidas=[],
                                 ya_registradas=ids, usuario="ana")
    estados = estados_sigrid(fabrica, ids)
    assert estados[ids[0]][0] == "registrado"
    assert estados[ids[1]][0] == "omitido"     # veredicto final: se respeta


def test_f024_r16_motivo_explica_la_via_nueva() -> None:
    texto = MOTIVO_LINEA_REGISTRADA
    assert "Comprobar en Sigrid" in texto
    assert "borra" in texto.lower()
    assert "aprob" in texto.lower()
    assert motivo_congelacion_linea(
        doc_aprobado=False, sigrid_estado="registrado") == texto
