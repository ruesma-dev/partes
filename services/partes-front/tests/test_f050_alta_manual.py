# tests/test_f050_alta_manual.py
"""F-050 · el alta manual («+ Añadir linea» y «Nuevo parte») cae en la fila
de la persona en ese parte (R16-R18).

SQLite en memoria (`tests/dobles.py`) con el ORM real. Ni red ni
PostgreSQL. Nombres, DNIs y recursos SINTETICOS.
"""
from __future__ import annotations

from types import SimpleNamespace

from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from sqlalchemy import select
from tests.dobles import FabricaSesionSqlite

AHORA = "2026-03-02T08:00:00+00:00"
OBRA = 10
DIA = "2026-03-02"
LEIDO_PAPEL = "Nombre Apellido"      # lo que leyo la IA en la fila 3
NOMBRE_SIGRID = "APELLIDO NOMBRE"   # lo que manda el alta manual


def _doc(s, doc_id: str, fecha: str = DIA) -> None:
    s.add(ParteDocumentOrm(
        id=doc_id, source_filename="parte.pdf",
        source_mime_type="application/pdf", source_sha256="sha" + doc_id,
        fecha=fecha, fecha_int=int(fecha.replace("-", "")),
        created_at_utc=AHORA, obra_ide=OBRA, obra_codigo="0010",
        obra_nombre="Obra Diez"))


def _reg(s, doc_id: str, line_index: int, line_no: int | None, *,
         fecha: str = DIA, tipo_hora: str = "normal", **campos) -> int:
    reg = ParteRegistroOrm(
        document_id=doc_id, line_index=line_index, empleado_line_no=line_no,
        fecha=fecha, fecha_int=int(fecha.replace("-", "")), obra_ide=OBRA,
        obra_codigo="0010", obra_nombre="Obra Diez", tipo_hora=tipo_hora,
        horas=8.0, **campos)
    s.add(reg)
    s.flush()
    return reg.id


def _persona_x(**extra) -> dict:
    """La persona del caso E1: sin ficha, casada por DNI al recurso 6001."""
    return dict(recurso_ide=6001, empleado_match_method="recurso_dni",
                empleado_dni="00000061A",
                trabajador_nombre_leido=LEIDO_PAPEL, **extra)


def _alta(repo, *, dias=(DIA,), ide=None, reside=6001, nombre=NOMBRE_SIGRID,
          ordinaria=8.0, extra=0.0, incidencia=None, **kw) -> dict:
    return repo.crear_parte_manual(
        obra_ide=OBRA, obra_codigo="0010", obra_nombre="Obra Diez",
        empleado_ide=ide, empleado_codigo=None, empleado_nombre=nombre,
        empleado_dni="00000061A", empleado_reside=reside, categoria="Oficial",
        dias=list(dias), horas_ordinaria=ordinaria, horas_extra=extra,
        incidencia_codigo=incidencia, **kw)


def _nuevas(fabrica, antes: set[int]) -> list[ParteRegistroOrm]:
    with fabrica.create_session() as s:
        regs = s.execute(select(ParteRegistroOrm).order_by(
            ParteRegistroOrm.id)).scalars().all()
        return [r for r in regs if r.id not in antes]


def _ids(fabrica) -> set[int]:
    with fabrica.create_session() as s:
        return set(s.execute(select(ParteRegistroOrm.id)).scalars().all())


# ===================================================================== #
# R16 · la persona ya esta en el parte: hereda su fila y su leido
# ===================================================================== #

def _parte_con_la_persona():
    """E6: la persona X en la fila 3 del papel (dos lineas); otra persona en
    la fila 1; y una linea de X en la papelera, con otra fila y otro leido
    y MENOR `line_index`, que no debe contar."""
    fabrica = FabricaSesionSqlite()
    with fabrica.create_session() as s:
        _doc(s, "d-e6")
        _reg(s, "d-e6", 0, 7, deleted_at_utc=AHORA,
             **{**_persona_x(), "trabajador_nombre_leido": "Borrada"})
        _reg(s, "d-e6", 1, 1, empleado_ide=10, recurso_ide=1001,
             trabajador_nombre_leido="Otra Persona")
        _reg(s, "d-e6", 2, 3, **_persona_x())
        _reg(s, "d-e6", 3, 3, tipo_hora="extra",
             **{**_persona_x(), "trabajador_nombre_leido": "N. APELLIDO"})
        s.commit()
    return ParteReviewRepository(fabrica), fabrica


def test_f050_r16_e6_hereda_fila_y_leido_de_la_de_menor_line_index() -> None:
    repo, fabrica = _parte_con_la_persona()
    antes = _ids(fabrica)
    assert _alta(repo, ordinaria=8.0, extra=2.0)["lineas"] == 2
    nuevas = _nuevas(fabrica, antes)
    assert [(r.empleado_line_no, r.trabajador_nombre_leido) for r in nuevas] \
        == [(3, LEIDO_PAPEL), (3, LEIDO_PAPEL)]
    assert {r.document_id for r in nuevas} == {"d-e6"}


def test_f050_r16_e6_cae_en_la_fila_de_la_persona() -> None:
    """Con la fila heredada, el detalle del parte la pinta en el bloque de
    la persona (R6) y el calendario en su fila (R5)."""
    repo, _fabrica = _parte_con_la_persona()
    _alta(repo, ordinaria=8.0)
    det = repo.get_parte("d-e6")
    assert [len(e.registros) for e in det.empleados] == [1, 3]
    filas = repo.get_obra(f"obr-{OBRA}", period_key="2026-03",
                          mode="natural").rows
    assert sorted(r.worker_key for r in filas) == ["rec-1001", "rec-6001"]


def test_f050_r16_con_ficha_hereda_de_su_clave() -> None:
    """Con ficha y sin recurso la clave es `emp-` (E12): hereda de la linea
    de esa ficha."""
    fabrica = FabricaSesionSqlite()
    with fabrica.create_session() as s:
        _doc(s, "d-f")
        _reg(s, "d-f", 0, 1, trabajador_nombre_leido="Sin Casar")
        _reg(s, "d-f", 1, 4, empleado_ide=55,
             trabajador_nombre_leido="Ficha Cincuenta")
        s.commit()
    repo = ParteReviewRepository(fabrica)
    antes = _ids(fabrica)
    _alta(repo, ide=55, reside=None, nombre="CINCUENTA, FICHA")
    (nueva,) = _nuevas(fabrica, antes)
    assert (nueva.empleado_line_no, nueva.trabajador_nombre_leido) == (
        4, "Ficha Cincuenta")


# ===================================================================== #
# R17 · la persona no esta: fila nueva al final
# ===================================================================== #

def test_f050_r17_e7_maximo_mas_uno_con_la_papelera() -> None:
    fabrica = FabricaSesionSqlite()
    with fabrica.create_session() as s:
        _doc(s, "d-e7")
        for i in range(4):
            _reg(s, "d-e7", i, i + 1, empleado_ide=20 + i,
                 recurso_ide=2000 + i)
        _reg(s, "d-e7", 4, 6, empleado_ide=30, recurso_ide=3000,
             deleted_at_utc=AHORA)
        _reg(s, "d-e7", 5, None, trabajador_nombre_leido="Sin Fila")
        s.commit()
    repo = ParteReviewRepository(fabrica)
    antes = _ids(fabrica)
    _alta(repo, ordinaria=8.0, extra=1.0)
    nuevas = _nuevas(fabrica, antes)
    assert [(r.empleado_line_no, r.trabajador_nombre_leido) for r in nuevas] \
        == [(7, NOMBRE_SIGRID), (7, NOMBRE_SIGRID)]


def test_f050_r17_la_misma_persona_solo_en_la_papelera_no_hereda() -> None:
    fabrica = FabricaSesionSqlite()
    with fabrica.create_session() as s:
        _doc(s, "d-pap")
        _reg(s, "d-pap", 0, 2, deleted_at_utc=AHORA, **_persona_x())
        s.commit()
    repo = ParteReviewRepository(fabrica)
    antes = _ids(fabrica)
    _alta(repo)
    (nueva,) = _nuevas(fabrica, antes)
    assert (nueva.empleado_line_no, nueva.trabajador_nombre_leido) == (
        3, NOMBRE_SIGRID)


def test_f050_r17_documento_nuevo_fila_uno() -> None:
    fabrica = FabricaSesionSqlite()
    repo = ParteReviewRepository(fabrica)
    _alta(repo, ordinaria=8.0, extra=-2.0)
    nuevas = _nuevas(fabrica, set())
    assert [(r.empleado_line_no, r.trabajador_nombre_leido) for r in nuevas] \
        == [(1, NOMBRE_SIGRID), (1, NOMBRE_SIGRID)]


def test_f050_r17_documento_sin_filas_numeradas_fila_uno() -> None:
    fabrica = FabricaSesionSqlite()
    with fabrica.create_session() as s:
        _doc(s, "d-nf")
        _reg(s, "d-nf", 0, None, trabajador_nombre_leido="Sin Fila")
        s.commit()
    repo = ParteReviewRepository(fabrica)
    antes = _ids(fabrica)
    _alta(repo)
    (nueva,) = _nuevas(fabrica, antes)
    assert nueva.empleado_line_no == 1


def test_f050_r17_incidencia_va_a_la_fila_de_la_persona() -> None:
    repo, fabrica = _parte_con_la_persona()
    antes = _ids(fabrica)
    _alta(repo, ordinaria=0.0, incidencia="V")
    (nueva,) = _nuevas(fabrica, antes)
    assert (nueva.es_incidencia, nueva.empleado_line_no,
            nueva.trabajador_nombre_leido) == (True, 3, LEIDO_PAPEL)


def test_f050_r17_incidencia_de_persona_nueva_al_final() -> None:
    repo, fabrica = _parte_con_la_persona()
    antes = _ids(fabrica)
    _alta(repo, reside=7777, ordinaria=0.0, incidencia="V")
    (nueva,) = _nuevas(fabrica, antes)
    assert (nueva.empleado_line_no, nueva.trabajador_nombre_leido) == (
        8, NOMBRE_SIGRID)


def test_f050_r16_r17_cada_dia_con_su_documento() -> None:
    """Dos dias: en uno la persona esta (hereda), en el otro no (al final)."""
    repo, fabrica = _parte_con_la_persona()
    with fabrica.create_session() as s:
        _doc(s, "d-otro", "2026-03-03")
        _reg(s, "d-otro", 0, 2, fecha="2026-03-03", empleado_ide=40,
             recurso_ide=4000)
        s.commit()
    antes = _ids(fabrica)
    _alta(repo, dias=(DIA, "2026-03-03"))
    nuevas = _nuevas(fabrica, antes)
    assert [(r.document_id, r.empleado_line_no, r.trabajador_nombre_leido)
            for r in nuevas] == [("d-e6", 3, LEIDO_PAPEL),
                                 ("d-otro", 3, NOMBRE_SIGRID)]


# ===================================================================== #
# R18 · lo demas, como hoy
# ===================================================================== #

def test_f050_r18_resto_de_campos_como_hoy() -> None:
    repo, fabrica = _parte_con_la_persona()
    antes = _ids(fabrica)
    hora = SimpleNamespace(ide=5, codigo="HL05", descripcion="Ordinaria",
                           ext=0, pre=20.0, prenom=15.0, method="manual")
    _alta(repo, ordinaria=8.0, extra=0.0, hora_normal=hora,
          partida_ide=900, partida_cod="P.900", partida_res="Partida",
          partida_capitulo="CI")
    (n,) = _nuevas(fabrica, antes)
    assert (n.line_index, n.empleado_ide, n.empleado_reside,
            n.empleado_match_method, n.recurso_ide, n.recurso_cif,
            n.empleado_nombre, n.tipo_hora, n.horas, n.hora_ide,
            n.hora_codigo, n.partida_ide, n.partida_cod,
            n.partida_match_method, n.partida_match_score) == (
        4, None, 6001, "recurso_manual", 6001, "00000061A", NOMBRE_SIGRID,
        "normal", 8.0, 5, "HL05", 900, "P.900", "manual", 1.0)
