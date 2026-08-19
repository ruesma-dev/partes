# tests/test_f015_r31_revert_respeta_congelados.py
"""R31 · lo que ya viajo a Sigrid no se revierte (decision D7 de F-012).

Cada pasada de sv3 empieza deshaciendo las extras automaticas de la
anterior para recalcular el dia desde el desglose original del parte. Eso
esta bien mientras el parte solo viva en `partes`; en cuanto una linea se
ha encolado o registrado en Sigrid —o su parte se ha aprobado—, borrarla
y recrearla aqui la descuadra respecto al ERP, donde ya no se va a tocar.

Con F-015 el riesgo deja de ser teorico: cambiar el candef de un recurso
en Sigrid (F-014) haria que la siguiente pasada re-splitease meses de
partes ya registrados. La regla es la de F-004: `sigrid_estado` en
{`encolado`, `registrado`} o documento `approved` = CONGELADO.

SQLite en memoria con el ORM real: ni red ni PostgreSQL.
"""
from __future__ import annotations

from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests.dobles import FabricaSesionSqlite, estado_lineas, sembrar_lineas


def _repo(fabrica):
    return SqlAlchemyParteRepository(fabrica)


# --------------------------- lo no congelado ---------------------------- #

def test_f015_r31_lo_no_congelado_se_revierte_como_siempre() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_lineas(fabrica, [
        {"horas": 6.0, "horas_orig": 9.0},
        {"horas": 3.0, "tipo": "extra", "extra_auto": True},
    ])
    revertidos = _repo(fabrica).revert_extras_auto()
    estado = estado_lineas(fabrica, ids)
    assert revertidos == 1
    assert estado[ids[0]] == (True, 9.0, None, False)   # horas restauradas
    assert estado[ids[1]][0] is False                   # extra_auto borrada


# ------------------------- lineas ya en Sigrid -------------------------- #

def test_f015_r31_una_extra_auto_registrada_sobrevive() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_lineas(fabrica, [
        {"horas": 3.0, "tipo": "extra", "extra_auto": True,
         "estado": "registrado"},
    ])
    revertidos = _repo(fabrica).revert_extras_auto()
    assert revertidos == 0
    assert estado_lineas(fabrica, ids)[ids[0]] == (True, 3.0, None, True)


def test_f015_r31_una_extra_auto_encolada_sobrevive() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_lineas(fabrica, [
        {"horas": 3.0, "tipo": "extra", "extra_auto": True,
         "estado": "encolado"},
    ])
    assert _repo(fabrica).revert_extras_auto() == 0
    assert estado_lineas(fabrica, ids)[ids[0]][0] is True


def test_f015_r31_una_normal_recortada_y_registrada_conserva_sus_horas() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_lineas(fabrica, [
        {"horas": 6.0, "horas_orig": 9.0, "estado": "registrado"},
    ])
    _repo(fabrica).revert_extras_auto()
    assert estado_lineas(fabrica, ids)[ids[0]] == (True, 6.0, 9.0, False)


# --------------------------- parte aprobado ----------------------------- #

def test_f015_r31_un_parte_aprobado_no_se_recalcula() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_lineas(fabrica, [
        {"horas": 6.0, "horas_orig": 9.0},
        {"horas": 3.0, "tipo": "extra", "extra_auto": True},
    ], aprobado=True)
    revertidos = _repo(fabrica).revert_extras_auto()
    estado = estado_lineas(fabrica, ids)
    assert revertidos == 0
    assert estado[ids[0]] == (True, 6.0, 9.0, False)
    assert estado[ids[1]][0] is True


def test_f015_r31_un_estado_de_sigrid_no_congelante_no_protege() -> None:
    """`error` o `pendiente` no son "ya esta en Sigrid": se revierten."""
    fabrica = FabricaSesionSqlite()
    ids = sembrar_lineas(fabrica, [
        {"horas": 3.0, "tipo": "extra", "extra_auto": True,
         "estado": "error"},
    ])
    assert _repo(fabrica).revert_extras_auto() == 1
    assert estado_lineas(fabrica, ids)[ids[0]][0] is False


# ----------------------------- convivencia ------------------------------ #

def test_f015_r31_en_el_mismo_parte_conviven_congeladas_y_no(
) -> None:
    """Un parte con una obra ya registrada y otra pendiente."""
    fabrica = FabricaSesionSqlite()
    ids = sembrar_lineas(fabrica, [
        {"horas": 8.0, "horas_orig": 9.0, "estado": "registrado"},
        {"horas": 2.0, "horas_orig": 4.0},
        {"horas": 1.0, "tipo": "extra", "extra_auto": True,
         "estado": "registrado"},
        {"horas": 2.0, "tipo": "extra", "extra_auto": True},
    ])
    revertidos = _repo(fabrica).revert_extras_auto()
    estado = estado_lineas(fabrica, ids)
    assert revertidos == 1
    assert estado[ids[0]] == (True, 8.0, 9.0, False)    # congelada, intacta
    assert estado[ids[1]] == (True, 4.0, None, False)   # revertida
    assert estado[ids[2]][0] is True                    # congelada, viva
    assert estado[ids[3]][0] is False                   # borrada


def test_f015_r31_el_contador_solo_cuenta_lo_revertido_de_verdad() -> None:
    fabrica = FabricaSesionSqlite()
    sembrar_lineas(fabrica, [
        {"horas": 1.0, "tipo": "extra", "extra_auto": True,
         "estado": "registrado"},
        {"horas": 2.0, "tipo": "extra", "extra_auto": True,
         "estado": "encolado"},
        {"horas": 3.0, "tipo": "extra", "extra_auto": True},
    ])
    assert _repo(fabrica).revert_extras_auto() == 1


def test_f015_r31_revertir_dos_veces_da_lo_mismo() -> None:
    """Idempotencia: la pasada siguiente no puede deshacer mas."""
    fabrica = FabricaSesionSqlite()
    ids = sembrar_lineas(fabrica, [
        {"horas": 6.0, "horas_orig": 9.0, "estado": "registrado"},
        {"horas": 6.0, "horas_orig": 9.0},
    ])
    repo = _repo(fabrica)
    repo.revert_extras_auto()
    primero = estado_lineas(fabrica, ids)
    repo.revert_extras_auto()
    assert estado_lineas(fabrica, ids) == primero


# --------------------- la lectura trae lo que hace falta ---------------- #

def test_f015_r31_la_lectura_trae_el_estado_de_sigrid_y_el_aprobado() -> None:
    """Sin estos dos campos, el conciliador no puede saber que congelar."""
    fabrica = FabricaSesionSqlite()
    sembrar_lineas(fabrica, [
        {"horas": 8.0, "estado": "registrado"},
        {"horas": 2.0},
    ], aprobado=True)
    filas = _repo(fabrica).fetch_registros_para_recurso()
    assert {f["sigrid_estado"] for f in filas} == {"registrado", None}
    assert all(f["doc_approved"] is True for f in filas)


def test_f015_r31_un_parte_no_aprobado_lo_declara_asi() -> None:
    fabrica = FabricaSesionSqlite()
    sembrar_lineas(fabrica, [{"horas": 8.0}])
    filas = _repo(fabrica).fetch_registros_para_recurso()
    assert filas[0]["doc_approved"] is False
    assert filas[0]["sigrid_estado"] is None


# ================= refuerzo tras la campana de mutacion ================= #
# El contador de lineas congeladas respetadas no lo miraba nadie: es la
# unica pista en el log de que la reversion se ha dejado cosas por el
# camino a proposito.

def test_f015_r31_el_log_dice_cuantas_congeladas_se_respetaron(caplog) -> None:
    import logging

    fabrica = FabricaSesionSqlite()
    sembrar_lineas(fabrica, [
        {"horas": 8.0, "horas_orig": 9.0, "estado": "registrado"},
        {"horas": 1.0, "tipo": "extra", "extra_auto": True,
         "estado": "encolado"},
        {"horas": 2.0, "tipo": "extra", "extra_auto": True},
    ])
    with caplog.at_level(logging.INFO):
        _repo(fabrica).revert_extras_auto()
    avisos = [m for m in caplog.messages if "CONGELADAS" in m]
    assert len(avisos) == 1
    # Prefijo exacto: un contador con el signo cambiado ("-2 linea(s)")
    # colaria con un `in`.
    assert avisos[0].startswith("[repo] revert de extras: 2 linea(s)")


def test_f015_r31_sin_congeladas_no_se_dice_nada(caplog) -> None:
    import logging

    fabrica = FabricaSesionSqlite()
    sembrar_lineas(fabrica, [
        {"horas": 2.0, "tipo": "extra", "extra_auto": True},
    ])
    with caplog.at_level(logging.INFO):
        _repo(fabrica).revert_extras_auto()
    assert "CONGELADAS" not in caplog.text


def test_f015_r31_un_parte_sin_nada_que_revertir_no_dice_nada(caplog) -> None:
    import logging

    fabrica = FabricaSesionSqlite()
    sembrar_lineas(fabrica, [{"horas": 8.0}])
    with caplog.at_level(logging.INFO):
        assert _repo(fabrica).revert_extras_auto() == 0
    assert "CONGELADAS" not in caplog.text
