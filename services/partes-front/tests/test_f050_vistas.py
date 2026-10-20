# tests/test_f050_vistas.py
"""F-050 · una fila por (obra, empresa, persona) en las vistas y acciones
del portal (R5-R10, R12, R13).

Casos de `requirements.md` (E1, E4a, E8-E11) sembrados en SQLite en
memoria (`tests/dobles.py`), con el ORM real. Ni red ni PostgreSQL.
Nombres, DNIs y recursos SINTETICOS.
"""
from __future__ import annotations

import inspect

from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite

AHORA = "2026-03-02T08:00:00+00:00"
MES = {"period_key": "2026-03", "mode": "natural"}

# Obras de cada caso (una por caso: los recuentos no se mezclan).
O_E1, O_E8, O_E9A, O_E9B, O_E10, O_E4A, O_E11 = 10, 20, 30, 40, 50, 60, 70


def _doc(s, doc_id: str, obra: int, *, fecha: str = "2026-03-02",
         empresa: int | None = None) -> None:
    s.add(ParteDocumentOrm(
        id=doc_id, source_filename="parte.pdf",
        source_mime_type="application/pdf", source_sha256="sha" + doc_id,
        fecha=fecha, fecha_int=int(fecha.replace("-", "")),
        created_at_utc=AHORA, obra_ide=obra, obra_codigo=f"0{obra}",
        obra_nombre=f"Obra {obra}", empresa=empresa))


def _reg(s, doc_id: str, obra: int, line_index: int, *,
         fecha: str = "2026-03-02", tipo: str = "normal",
         horas: float = 8.0, **campos) -> int:
    reg = ParteRegistroOrm(
        document_id=doc_id, line_index=line_index, fecha=fecha,
        fecha_int=int(fecha.replace("-", "")), obra_ide=obra,
        obra_codigo=f"0{obra}", obra_nombre=f"Obra {obra}",
        tipo_hora=tipo, horas=horas, hora_ide=1, hora_codigo="HL01",
        **campos)
    s.add(reg)
    s.flush()
    return reg.id


def _escenario():
    """Todos los casos a la vez; cada uno en su obra."""
    fabrica = FabricaSesionSqlite()
    ids: dict[str, int] = {}
    with fabrica.create_session() as s:
        # E1 (caso real): la IA leyo una extra de 2 sin ficha casada por
        # DNI al recurso 6001; el alta manual (otro leido: el de Sigrid)
        # anadio la ordinaria de 8 con el mismo recurso, en el mismo parte.
        _doc(s, "d-e1", O_E1)
        ids["e1_ia"] = _reg(
            s, "d-e1", O_E1, 0, tipo="extra", horas=2.0, empleado_line_no=3,
            recurso_ide=6001, empleado_match_method="recurso_dni",
            empleado_dni="00000061A", trabajador_nombre_leido="Nombre Apellido")
        ids["e1_manual"] = _reg(
            s, "d-e1", O_E1, 1, empleado_line_no=1, empleado_reside=6001,
            empleado_match_method="recurso_manual", empleado_dni="00000061A",
            empleado_nombre="APELLIDO NOMBRE",
            trabajador_nombre_leido="APELLIDO NOMBRE")
        # E8: con ficha 77 y recurso 501, y otra linea sin ficha del mismo
        # recurso (casada por nombre) el mismo dia. Y otra persona (502)
        # en la misma obra, que ninguna accion sobre rec-501 debe tocar.
        _doc(s, "d-e8", O_E8, fecha="2026-03-03")
        ids["e8_ficha"] = _reg(
            s, "d-e8", O_E8, 0, fecha="2026-03-03", empleado_line_no=1,
            empleado_ide=77, recurso_ide=501, empleado_dni="00000077A",
            empleado_nombre="Persona Ocho",
            trabajador_nombre_leido="Persona Ocho")
        ids["e8_sin_ficha"] = _reg(
            s, "d-e8", O_E8, 1, fecha="2026-03-03", tipo="extra", horas=1.0,
            empleado_line_no=2, recurso_ide=501,
            empleado_match_method="recurso_nombre",
            trabajador_nombre_leido="P. Ocho")
        ids["e8_otra"] = _reg(
            s, "d-e8", O_E8, 2, fecha="2026-03-03", empleado_line_no=3,
            empleado_ide=78, recurso_ide=502, empleado_dni="00000078A",
            empleado_nombre="Persona Otra",
            trabajador_nombre_leido="Persona Otra")
        # E9: el recurso 7001 en dos obras (con ficha en una, sin ella en
        # la otra).
        _doc(s, "d-e9a", O_E9A, fecha="2026-03-04")
        _doc(s, "d-e9b", O_E9B, fecha="2026-03-05")
        ids["e9_a"] = _reg(
            s, "d-e9a", O_E9A, 0, fecha="2026-03-04", empleado_line_no=1,
            empleado_ide=70, recurso_ide=7001, empleado_dni="00000070A",
            empleado_nombre="Persona Nueve",
            trabajador_nombre_leido="Persona Nueve")
        ids["e9_b"] = _reg(
            s, "d-e9b", O_E9B, 0, fecha="2026-03-05", empleado_line_no=1,
            recurso_ide=7001, empleado_match_method="recurso_dni",
            empleado_dni="00000070A", trabajador_nombre_leido="NUEVE P")
        # E10: la misma persona (mismo DNI y nombre) en dos empresas: ficha
        # y recurso distintos en cada una.
        _doc(s, "d-e10a", O_E10, fecha="2026-03-06", empresa=1)
        _doc(s, "d-e10b", O_E10, fecha="2026-03-09", empresa=28)
        ids["e10_a"] = _reg(
            s, "d-e10a", O_E10, 0, fecha="2026-03-06", empleado_line_no=1,
            empleado_ide=81, recurso_ide=8101, empleado_dni="00000080A",
            empleado_nombre="Persona Diez",
            trabajador_nombre_leido="Persona Diez")
        ids["e10_b"] = _reg(
            s, "d-e10b", O_E10, 0, fecha="2026-03-09", empleado_line_no=1,
            empleado_ide=82, recurso_ide=8201, empleado_dni="00000080A",
            empleado_nombre="Persona Diez",
            trabajador_nombre_leido="Persona Diez")
        # E4a: homonimos (mismo leido) sin ficha casados con recursos
        # distintos.
        _doc(s, "d-e4a", O_E4A, fecha="2026-03-10")
        ids["e4a_1"] = _reg(
            s, "d-e4a", O_E4A, 0, fecha="2026-03-10", empleado_line_no=1,
            recurso_ide=9101, empleado_match_method="recurso_dni",
            empleado_dni="00000091A", trabajador_nombre_leido="Juan Igual")
        ids["e4a_2"] = _reg(
            s, "d-e4a", O_E4A, 1, fecha="2026-03-10", empleado_line_no=2,
            recurso_ide=9102, empleado_match_method="recurso_dni",
            empleado_dni="00000092A", trabajador_nombre_leido="Juan Igual")
        # E11: un DNI con dos recursos de la misma empresa en una obra.
        _doc(s, "d-e11", O_E11, fecha="2026-03-11", empresa=1)
        ids["e11_1"] = _reg(
            s, "d-e11", O_E11, 0, fecha="2026-03-11", empleado_line_no=1,
            empleado_ide=93, recurso_ide=9201, empleado_dni="00000093A",
            empleado_nombre="Persona Once",
            trabajador_nombre_leido="Persona Once")
        ids["e11_2"] = _reg(
            s, "d-e11", O_E11, 1, fecha="2026-03-11", empleado_line_no=2,
            recurso_ide=9202, empleado_match_method="recurso_dni",
            empleado_dni="00000093A", trabajador_nombre_leido="Persona Once")
        s.commit()
    return ParteReviewRepository(fabrica), fabrica, ids


def _filas(repo, obra: int):
    det = repo.get_obra(f"obr-{obra}", **MES)
    return {r.worker_key: r for r in det.rows}


def _celda(fila, dia: str):
    return next(c for c in fila.cells if c.date_iso == dia)


def _vivas(fabrica, ids: list[int]) -> list[int]:
    with fabrica.create_session() as s:
        return [i for i in ids
                if s.get(ParteRegistroOrm, i).deleted_at_utc is None]


# ===================================================================== #
# R5 · calendario de obra
# ===================================================================== #

def test_f050_r5_e1_una_fila_8_mas_2() -> None:
    repo, _f, ids = _escenario()
    filas = _filas(repo, O_E1)
    assert list(filas) == ["rec-6001"]
    celda = _celda(filas["rec-6001"], "2026-03-02")
    assert celda.label == "8+2"
    assert celda.edit_normal_id == ids["e1_manual"]
    assert celda.edit_extra_id == ids["e1_ia"]


def test_f050_r5_e8_ficha_y_sin_ficha_del_mismo_recurso_una_fila() -> None:
    repo, _f, ids = _escenario()
    filas = _filas(repo, O_E8)
    assert set(filas) == {"rec-501", "rec-502"}
    celda = _celda(filas["rec-501"], "2026-03-03")
    assert (celda.edit_normal_id, celda.edit_extra_id) == (
        ids["e8_ficha"], ids["e8_sin_ficha"])


def test_f050_r5_e4a_homonimos_casados_con_recursos_distintos_dos_filas() -> None:
    repo, _f, _ids = _escenario()
    assert set(_filas(repo, O_E4A)) == {"rec-9101", "rec-9102"}


def test_f050_r5_e11_dos_recursos_del_mismo_dni_dos_filas() -> None:
    repo, _f, _ids = _escenario()
    assert set(_filas(repo, O_E11)) == {"rec-9201", "rec-9202"}


# ===================================================================== #
# R8 · recuento por obra y alcance del parte
# ===================================================================== #

def test_f050_r8_list_obras_cuenta_cada_persona_una_vez() -> None:
    repo, _f, _ids = _escenario()
    cuenta = {r.obra_ide: r.num_trabajadores for r in repo.list_obras()}
    assert cuenta[O_E1] == 1
    assert cuenta[O_E8] == 2
    assert cuenta[O_E4A] == 2


def test_f050_r8_alcance_parte_cuenta_cada_persona_una_vez() -> None:
    repo, _f, _ids = _escenario()
    assert repo.alcance_parte("d-e1")["trabajadores"] == 1
    assert repo.alcance_parte("d-e1")["lineas"] == 2
    assert repo.alcance_parte("d-e8")["trabajadores"] == 2


# ===================================================================== #
# R9 · lista «Por persona»
# ===================================================================== #

def test_f050_r9_e9_dos_obras_una_fila() -> None:
    repo, _f, _ids = _escenario()
    filas = [w for w in repo.list_workers() if w.worker_key == "rec-7001"]
    assert len(filas) == 1
    assert filas[0].num_partes == 2
    assert filas[0].num_registros == 2


def test_f050_r9_e10_dos_empresas_dos_filas() -> None:
    repo, _f, _ids = _escenario()
    claves = [w.worker_key for w in repo.list_workers()
              if w.nombre == "Persona Diez"]
    assert sorted(claves) == ["rec-8101", "rec-8201"]


def test_f050_r9_e1_y_e8_una_fila_cada_uno() -> None:
    repo, _f, _ids = _escenario()
    claves = [w.worker_key for w in repo.list_workers()]
    assert claves.count("rec-6001") == 1
    assert claves.count("rec-501") == 1
    assert len(claves) == len(set(claves))


# ===================================================================== #
# R10 · vista del trabajador
# ===================================================================== #

def test_f050_r10_e9_las_lineas_de_sus_dos_obras() -> None:
    repo, _f, ids = _escenario()
    det = repo.get_worker("rec-7001")
    assert sorted(v.id for v in det.registros) == sorted(
        [ids["e9_a"], ids["e9_b"]])
    assert {v.obra_codigo for v in det.registros} == {
        f"0{O_E9A}", f"0{O_E9B}"}


def test_f050_r10_e10_sin_las_lineas_de_la_otra_empresa() -> None:
    repo, _f, ids = _escenario()
    assert [v.id for v in repo.get_worker("rec-8101").registros] == [
        ids["e10_a"]]
    assert [v.id for v in repo.get_worker("rec-8201").registros] == [
        ids["e10_b"]]


def test_f050_r10_e8_con_y_sin_ficha_y_ninguna_otra() -> None:
    repo, _f, ids = _escenario()
    assert sorted(v.id for v in repo.get_worker("rec-501").registros) == \
        sorted([ids["e8_ficha"], ids["e8_sin_ficha"]])


# ===================================================================== #
# R12 · acciones por clave rec-
# ===================================================================== #

def test_f050_r12_registro_ids_de_trabajador() -> None:
    repo, _f, ids = _escenario()
    assert sorted(repo.registro_ids_de_trabajador("rec-501")) == sorted(
        [ids["e8_ficha"], ids["e8_sin_ficha"]])
    assert sorted(repo.registro_ids_de_trabajador("rec-6001")) == sorted(
        [ids["e1_ia"], ids["e1_manual"]])


def test_f050_r12_reasignar_por_clave_toca_con_y_sin_ficha() -> None:
    repo, fabrica, ids = _escenario()
    n, _leidos, congeladas = repo.reassign_empleado_by_worker_key(
        worker_key="rec-501", ide=99, codigo="E99", nombre="Otra Ficha",
        dni="00000099A", reside=9901)
    assert (n, congeladas) == (2, 0)
    with fabrica.create_session() as s:
        fichas = {i: s.get(ParteRegistroOrm, i).empleado_ide
                  for i in (ids["e8_ficha"], ids["e8_sin_ficha"],
                            ids["e8_otra"])}
    assert fichas == {ids["e8_ficha"]: 99, ids["e8_sin_ficha"]: 99,
                      ids["e8_otra"]: 78}


def test_f050_r12_papelera_por_clave_toca_con_y_sin_ficha() -> None:
    repo, fabrica, ids = _escenario()
    assert repo.soft_delete_worker(worker_key="rec-501", by="ana") == (2, 0)
    assert _vivas(fabrica, [ids["e8_ficha"], ids["e8_sin_ficha"],
                            ids["e8_otra"]]) == [ids["e8_otra"]]


def test_f050_r12_papelera_e10_no_toca_la_otra_empresa() -> None:
    repo, fabrica, ids = _escenario()
    assert repo.soft_delete_worker(worker_key="rec-8101") == (1, 0)
    assert _vivas(fabrica, [ids["e10_a"], ids["e10_b"]]) == [ids["e10_b"]]


# ===================================================================== #
# R13 · claves antiguas en las acciones: 0 lineas
# ===================================================================== #

CLAVES_ANTIGUAS = ["emp-77", "nom-NOMBRE_APELLIDO", "nom-APELLIDO_NOMBRE",
                   "emp-81"]


def test_f050_r13_claves_antiguas_actuan_sobre_cero_lineas() -> None:
    repo, fabrica, ids = _escenario()
    todas = list(ids.values())
    for clave in CLAVES_ANTIGUAS:
        assert repo.registro_ids_de_trabajador(clave) == []
        assert repo.reassign_empleado_by_worker_key(
            worker_key=clave, ide=99, codigo="E99", nombre="X",
            dni="00000099A") == (0, [], 0)
        assert repo.soft_delete_worker(worker_key=clave) == (0, 0)
        assert repo.get_worker(clave) is None
    assert _vivas(fabrica, todas) == todas


def test_f050_r13_las_acciones_usan_la_clave_unica() -> None:
    """Las tres acciones por clave comparan con `worker_key_for_registro`
    (o pasan por `get_worker`, que lo hace): no hay otra regla."""
    import infrastructure.database.parte_repository as pr
    repo = pr.ParteReviewRepository
    for metodo in (repo.reassign_empleado_by_worker_key,
                   repo.soft_delete_worker, repo.get_worker):
        assert "worker_key_for_registro(r) == worker_key" in \
            inspect.getsource(metodo)
    assert "self.get_worker(worker_key)" in inspect.getsource(
        repo.registro_ids_de_trabajador)
