# tests/test_f037_revert.py
"""F-037 · R4-R9: la reversion y la lectura del repositorio con la pareja.

`revert_extras_auto` deshace las extras automaticas de la pasada anterior
antes de recalcular. Hasta F-037 miraba cada linea por separado: respetaba
la extra congelada, pero restauraba su base (`horas = horas_orig`) y el
calculo la volvia a partir, con otra `extra_auto` por pasada. Ahora la
pareja (misma `document_id`, `line_index`, `empleado_line_no`,
`fecha_int`) se congela entera.

SQLite en memoria con el ORM real: ni red ni PostgreSQL. Datos sinteticos.
"""
from __future__ import annotations

import logging

from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests.dobles import FabricaSesionSqlite, estado_lineas, sembrar_lineas

DNI = "12345678Z"
JUEVES = "2026-10-01"


def _repo(fabrica) -> SqlAlchemyParteRepository:
    return SqlAlchemyParteRepository(fabrica)


def _base(horas: float, horas_orig: float | None, estado=None, *,
          li: int = 0, eln: int | None = 1) -> dict:
    return {"horas": horas, "horas_orig": horas_orig, "estado": estado,
            "line_index": li, "empleado_line_no": eln, "recurso_ide": 501}


def _extra(horas: float, estado=None, *, li: int = 0,
           eln: int | None = 1) -> dict:
    return {"horas": horas, "tipo": "extra", "extra_auto": True,
            "estado": estado, "line_index": li, "empleado_line_no": eln,
            "recurso_ide": 501}


def _sembrar(fabrica, lineas, **kw) -> list[int]:
    return sembrar_lineas(fabrica, lineas, fecha=kw.pop("fecha", JUEVES), **kw)


# ================ R4 · la base de una extra congelada ================== #

def test_f037_r4_base_omitida_con_su_extra_registrada_no_se_toca() -> None:
    """El caso de la incidencia: mensual sin hora laborable, 10 -> 8 + 2."""
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, [_base(8.0, 10.0, "omitido"),
                             _extra(2.0, "registrado")])
    assert _repo(fabrica).revert_extras_auto() == 0
    estado = estado_lineas(fabrica, ids)
    assert estado[ids[0]] == (True, 8.0, 10.0, False)
    assert estado[ids[1]] == (True, 2.0, None, True)


def test_f037_r4_base_de_cero_horas_con_su_extra_registrada() -> None:
    """La otra variante: dia no laborable, base de 0 h «sin horas»."""
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, [_base(0.0, 4.0, "omitido"),
                             _extra(4.0, "registrado")], fecha="2026-10-03")
    assert _repo(fabrica).revert_extras_auto() == 0
    estado = estado_lineas(fabrica, ids)
    assert estado[ids[0]] == (True, 0.0, 4.0, False)
    assert estado[ids[1]] == (True, 4.0, None, True)


def test_f037_r4_con_la_extra_encolada_tampoco() -> None:
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, [_base(8.0, 10.0), _extra(2.0, "encolado")])
    assert _repo(fabrica).revert_extras_auto() == 0
    assert estado_lineas(fabrica, ids)[ids[0]] == (True, 8.0, 10.0, False)


def test_f037_r4_sin_empleado_line_no_tambien_es_pareja() -> None:
    """`None` es un valor mas de la clave (R1)."""
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, [_base(8.0, 10.0, "omitido", eln=None),
                             _extra(2.0, "registrado", eln=None)])
    assert _repo(fabrica).revert_extras_auto() == 0
    assert estado_lineas(fabrica, ids)[ids[0]] == (True, 8.0, 10.0, False)


def test_f037_r4_otro_trabajador_de_la_misma_linea_no_es_pareja() -> None:
    """Misma linea del parte, otro `empleado_line_no`: se revierte."""
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, [_base(8.0, 10.0, eln=2),
                             _extra(2.0, "registrado", eln=1)])
    assert _repo(fabrica).revert_extras_auto() == 0
    assert estado_lineas(fabrica, ids)[ids[0]] == (True, 10.0, None, False)


# ============ R5 · la extra no congelada de una base congelada ========== #

def test_f037_r5_base_registrada_conserva_su_extra_sin_estado() -> None:
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, [_base(8.0, 10.0, "registrado"), _extra(2.0)])
    assert _repo(fabrica).revert_extras_auto() == 0
    estado = estado_lineas(fabrica, ids)
    assert estado[ids[0]] == (True, 8.0, 10.0, False)
    assert estado[ids[1]] == (True, 2.0, None, True)


def test_f037_r5_base_registrada_conserva_su_extra_en_error() -> None:
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, [_base(8.0, 10.0, "registrado"),
                             _extra(2.0, "error")])
    assert _repo(fabrica).revert_extras_auto() == 0
    assert estado_lineas(fabrica, ids)[ids[1]] == (True, 2.0, None, True)


def test_f037_r5_parte_aprobado_conserva_todo() -> None:
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, [_base(8.0, 10.0), _extra(2.0)], aprobado=True)
    assert _repo(fabrica).revert_extras_auto() == 0
    assert estado_lineas(fabrica, ids)[ids[1]][0] is True


# ===================== R6 · los duplicados se borran ==================== #

def test_f037_r6_el_duplicado_sin_estado_se_borra_y_se_avisa(caplog) -> None:
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, [_base(8.0, 10.0, "omitido"),
                             _extra(2.0, "registrado"), _extra(2.0)])
    with caplog.at_level(logging.INFO):
        assert _repo(fabrica).revert_extras_auto() == 1
    estado = estado_lineas(fabrica, ids)
    assert estado[ids[0]] == (True, 8.0, 10.0, False)
    assert estado[ids[1]] == (True, 2.0, None, True)
    assert estado[ids[2]][0] is False
    avisos = [r for r in caplog.records
              if r.levelno == logging.WARNING and "DUPLICADA" in r.getMessage()]
    assert len(avisos) == 1
    msg = avisos[0].getMessage()
    assert msg.startswith("[repo] revert de extras: 1 extra(s) automatica(s) "
                          "DUPLICADA(S) borrada(s)")
    assert msg.endswith(f"ids: {ids[2]}")
    assert DNI not in caplog.text


def test_f037_r6_el_aviso_lista_como_mucho_diez_ids(caplog) -> None:
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, [_base(8.0, 10.0, "omitido"),
                             _extra(2.0, "registrado")]
                   + [_extra(2.0) for _ in range(12)])
    with caplog.at_level(logging.WARNING):
        assert _repo(fabrica).revert_extras_auto() == 12
    msg = next(m for m in caplog.messages if "DUPLICADA" in m)
    assert msg.startswith("[repo] revert de extras: 12 extra(s)")
    assert msg.endswith("ids: " + ", ".join(str(i) for i in ids[2:12]))


def test_f037_r6_sin_duplicados_no_hay_aviso(caplog) -> None:
    fabrica = FabricaSesionSqlite()
    _sembrar(fabrica, [_base(8.0, 10.0, "omitido"), _extra(2.0, "registrado"),
                       _base(6.0, 9.0, li=1), _extra(3.0, li=1)])
    with caplog.at_level(logging.INFO):
        assert _repo(fabrica).revert_extras_auto() == 1
    assert "DUPLICADA" not in caplog.text
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]


# ================= R7 · dos extras congeladas en una pareja ============= #

def test_f037_r7_dos_extras_congeladas_ninguna_se_borra(caplog) -> None:
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, [_base(8.0, 10.0, "omitido", li=3),
                             _extra(2.0, "registrado", li=3),
                             _extra(2.0, "encolado", li=3)],
                   document_id="doc-7")
    with caplog.at_level(logging.WARNING):
        assert _repo(fabrica).revert_extras_auto() == 0
    estado = estado_lineas(fabrica, ids)
    assert all(estado[i][0] for i in ids)
    assert estado[ids[0]] == (True, 8.0, 10.0, False)
    avisos = [m for m in caplog.messages if "revisar a mano" in m]
    assert avisos == [
        "[repo] revert de extras: la pareja document_id=doc-7 line_index=3 "
        "tiene 2 extras automaticas CONGELADAS; no se borra ninguna, "
        "revisar a mano en Sigrid (F-037)."
    ]


def test_f037_r7_una_por_pareja_con_dos_parejas_dobles(caplog) -> None:
    fabrica = FabricaSesionSqlite()
    _sembrar(fabrica, [_extra(1.0, "registrado", li=0),
                       _extra(1.0, "registrado", li=0),
                       _extra(1.0, "registrado", li=1),
                       _extra(1.0, "registrado", li=1),
                       _extra(1.0, "registrado", li=1)])
    with caplog.at_level(logging.WARNING):
        _repo(fabrica).revert_extras_auto()
    avisos = [m for m in caplog.messages if "revisar a mano" in m]
    assert len(avisos) == 2
    assert "line_index=0 tiene 2 extras" in avisos[0]
    assert "line_index=1 tiene 3 extras" in avisos[1]


# ================ R8 · lo demas como siempre, y los logs ================ #

def test_f037_r8_parejas_libres_se_revierten_como_siempre() -> None:
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, [_base(8.0, 10.0, "omitido"),
                             _extra(2.0, "registrado"),
                             _base(6.0, 9.0, li=1), _extra(3.0, li=1)])
    assert _repo(fabrica).revert_extras_auto() == 1
    estado = estado_lineas(fabrica, ids)
    assert estado[ids[0]] == (True, 8.0, 10.0, False)
    assert estado[ids[2]] == (True, 9.0, None, False)
    assert estado[ids[3]][0] is False


def test_f037_r8_el_info_de_congeladas_cuenta_solo_las_de_por_si(
        caplog) -> None:
    fabrica = FabricaSesionSqlite()
    _sembrar(fabrica, [_base(8.0, 10.0, "omitido"),
                       _extra(2.0, "registrado"),
                       _base(6.0, 9.0, "registrado", li=1),
                       _extra(3.0, li=1)])
    with caplog.at_level(logging.INFO):
        _repo(fabrica).revert_extras_auto()
    congeladas = [m for m in caplog.messages if "CONGELADAS" in m]
    assert len(congeladas) == 1
    assert congeladas[0].startswith("[repo] revert de extras: 2 linea(s) "
                                    "CONGELADAS respetadas")
    protegidas = [m for m in caplog.messages if "protegidas" in m]
    assert protegidas == [
        "[repo] revert de extras: 2 linea(s) protegidas por su pareja "
        "congelada (F-037)."
    ]


def test_f037_r8_sin_protegidas_no_hay_info_de_pareja(caplog) -> None:
    fabrica = FabricaSesionSqlite()
    _sembrar(fabrica, [_base(6.0, 9.0), _extra(3.0),
                       _extra(1.0, "registrado", li=1)])
    with caplog.at_level(logging.INFO):
        assert _repo(fabrica).revert_extras_auto() == 1
    assert "protegidas" not in caplog.text


def test_f037_r8_una_extra_explicita_no_es_de_la_pareja() -> None:
    """Una extra explicita (sv4, `crear_extra_desde`) registrada con la
    misma clave no protege la base ni hace duplicada a la automatica."""
    fabrica = FabricaSesionSqlite()
    explicita = {"horas": 1.0, "tipo": "extra", "estado": "registrado",
                 "line_index": 0, "empleado_line_no": 1, "horas_orig": 1.0}
    ids = _sembrar(fabrica, [_base(8.0, 10.0), _extra(2.0), explicita])
    assert _repo(fabrica).revert_extras_auto() == 1
    estado = estado_lineas(fabrica, ids)
    assert estado[ids[0]] == (True, 10.0, None, False)
    assert estado[ids[1]][0] is False
    assert estado[ids[2]] == (True, 1.0, 1.0, False)


def test_f037_r8_revertir_dos_veces_da_lo_mismo() -> None:
    fabrica = FabricaSesionSqlite()
    ids = _sembrar(fabrica, [_base(8.0, 10.0, "omitido"),
                             _extra(2.0, "registrado"), _extra(2.0)])
    repo = _repo(fabrica)
    assert repo.revert_extras_auto() == 1
    primero = estado_lineas(fabrica, ids)
    assert primero[ids[0]] == (True, 8.0, 10.0, False)
    assert repo.revert_extras_auto() == 0
    assert estado_lineas(fabrica, ids) == primero
