# tests/test_f060_aprobacion_racha.py
"""F-060 · La racha de incidencia en la aprobacion de sv4 (R1, R6, R9-R12,
R28-R30) y en el modal (R11).

  - `lineas_para_registro`: el rol de cada incidencia con el historico de
    la persona (UNA consulta por persona), `racha_registro_ids` en cada
    linea y `avisos_racha` en cada grupo.
  - `marcar_registros_sigrid`: `movida_de` deja la linea que tenia el CIZ
    en `omitido` con `fin_movido`, con CAS, idempotente por los dos
    canales de F-002 (`aplicar_resultado`).
  - `reparto_obras`: `agregar_ejecucion` conserva `movida_de`.

Sin red ni PostgreSQL: SQLite en memoria con el MISMO ORM (`dobles.py`).
Personas, DNIs, obras y partes SINTETICOS.
"""
from __future__ import annotations

import pytest
from sqlalchemy import event

from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite
from tests.test_f025_aprobacion import DNI_A, DNI_B, OBRA_10, OBRA_20, sembrar
from tests.test_f025_deteccion import TABLA


def _dia(n: int, mes: int = 10) -> str:
    return f"2026-{mes:02d}-{n:02d}"


def _fabrica() -> FabricaSesionSqlite:
    return FabricaSesionSqlite()


def _v(fabrica, n, *, doc=None, estado=None, mes=10, letra="V", **kw):
    """Un parte de un dia con una V (u otra letra) de la persona A."""
    return sembrar(fabrica, [{"inc": letra, "estado": estado}],
                   doc=doc or f"v{mes}-{n}-{letra}-{kw.get('dni', 'A')}",
                   fecha=_dia(n, mes), **kw)[0]


def _t(fabrica, n, *, doc=None, horas=8.0, mes=10, estado=None, **kw):
    return sembrar(fabrica, [{"horas": horas, "estado": estado}],
                   doc=doc or f"t{mes}-{n}-{kw.get('dni', 'A')}",
                   fecha=_dia(n, mes), **kw)[0]


def _datos(fabrica, ids, tabla=TABLA) -> dict:
    return ParteReviewRepository(fabrica).lineas_para_registro(
        ids, incidencias=tabla)


def _linea(datos, rid) -> dict:
    return next(l for l in datos["lineas"] if l["registro_id"] == rid)


def _roles(datos) -> dict[int, str]:
    return {l["registro_id"]: l["incidencia_rol"] for l in datos["lineas"]
            if l["es_incidencia"]}


# ============================ R1-R9 · el rol ============================ #

def test_f060_r1_r9_fin_con_las_lineas_de_la_racha() -> None:
    f = _fabrica()
    d1 = _v(f, 1, estado="registrado")
    d2 = _v(f, 2, estado="registrado")
    d3 = _v(f, 3)
    l3 = _linea(_datos(f, [d3]), d3)
    assert l3["incidencia_rol"] == "fin"
    assert l3["racha_registro_ids"] == [d1, d2]


def test_f060_r1_cualquier_obra_y_estado() -> None:
    f = _fabrica()
    d1 = _v(f, 1, obra=OBRA_20, estado="omitido")
    d2 = _v(f, 2)
    assert _linea(_datos(f, [d2]), d2)["racha_registro_ids"] == [d1]


def test_f060_r2_r3_tras_un_dia_trabajado_es_inicio() -> None:
    f = _fabrica()
    _v(f, 1)
    _t(f, 2)
    d3 = _v(f, 3)
    l3 = _linea(_datos(f, [d3]), d3)
    assert (l3["incidencia_rol"], l3["racha_registro_ids"]) == ("inicio", [])


def test_f060_r2_fuera_de_la_ventana_es_inicio() -> None:
    f = _fabrica()
    _v(f, 31, mes=8)
    d = _v(f, 1)
    assert _roles(_datos(f, [d])) == {d: "inicio"}


def test_f060_r3_otra_letra_abre_racha() -> None:
    f = _fabrica()
    _v(f, 1)
    d2 = _v(f, 2, letra="B")
    assert _roles(_datos(f, [d2])) == {d2: "inicio"}


def test_f060_r3_sin_tabla_la_letra_sale_de_los_codigos() -> None:
    f = _fabrica()
    _v(f, 1)
    d2 = _v(f, 2)
    d3 = _v(f, 3, letra="B")
    assert _roles(_datos(f, [d2, d3], tabla=None)) == {d2: "fin",
                                                       d3: "inicio"}


def test_f060_r4_ejemplo_del_humano_dia_a_dia() -> None:
    """Dia 1 V => inicio; dia 2 => fin; 3 y 4 => fin (sv5 mueve); dia 5
    con horas => trabajo; dia 6 V => inicio de una racha nueva."""
    f = _fabrica()
    roles = []
    for n in (1, 2, 3, 4):
        rid = _v(f, n)
        roles.append(_roles(_datos(f, [rid]))[rid])
    _t(f, 5)
    rid = _v(f, 6)
    roles.append(_roles(_datos(f, [rid]))[rid])
    assert roles == ["inicio", "fin", "fin", "fin", "inicio"]


def test_f060_r5_la_papelera_no_cuenta() -> None:
    f = _fabrica()
    _v(f, 1)
    sembrar(f, [{"horas": 8.0}], doc="t2", fecha=_dia(2), doc_activo=False)
    sembrar(f, [{"horas": 8.0, "borrada": True}], doc="t2b", fecha=_dia(2))
    d3 = _v(f, 3)
    assert _roles(_datos(f, [d3])) == {d3: "fin"}


def test_f060_r9_papelera_registrada_entra_en_la_racha() -> None:
    f = _fabrica()
    d1 = _v(f, 1)
    (borrada,) = sembrar(f, [{"inc": "V", "estado": "registrado",
                              "borrada": True}], doc="vb", fecha=_dia(2))
    (otra,) = sembrar(f, [{"inc": "V", "estado": "omitido",
                           "borrada": True}], doc="vo", fecha=_dia(2))
    d2 = _v(f, 2)
    d3 = _v(f, 3)
    ids = _linea(_datos(f, [d3]), d3)["racha_registro_ids"]
    assert ids == sorted([d1, d2, borrada]) and otra not in ids


def test_f060_r9_hacia_delante_tambien() -> None:
    f = _fabrica()
    d1 = _v(f, 1)
    d3 = _v(f, 3, estado="registrado")
    d2 = _v(f, 2)
    assert _linea(_datos(f, [d2]), d2)["racha_registro_ids"] == [d1, d3]


def test_f060_r9_las_demas_lineas_van_con_lista_vacia() -> None:
    f = _fabrica()
    ids = sembrar(f, [{"inc": "V"}, {"tipo": "extra", "horas": 0.0}],
                  doc="d1", fecha=_dia(1))
    t = _t(f, 2)
    datos = _datos(f, ids + [t])
    assert all(l["racha_registro_ids"] == [] for l in datos["lineas"])


def test_f060_r6_sin_dni_por_la_clave_de_trabajador() -> None:
    f = _fabrica()
    d1 = _v(f, 1, dni=None, recurso_ide=501)
    _t(f, 1, dni=None, recurso_ide=502, doc="otro")     # otra persona
    _t(f, 2, dni=None, recurso_ide=502, doc="otro2")
    d2 = _v(f, 2, dni=None, recurso_ide=501)
    l2 = _linea(_datos(f, [d2]), d2)
    assert (l2["incidencia_rol"], l2["racha_registro_ids"]) == ("fin", [d1])


def _casar_por_recurso(fabrica, *ids) -> None:
    from infrastructure.database.orm_models import ParteRegistroOrm
    with fabrica.create_session() as s:
        for rid in ids:
            reg = s.get(ParteRegistroOrm, rid)
            reg.empleado_match_method = "recurso_manual"
            reg.recurso_ide, reg.empleado_reside = None, 501
        s.commit()


def test_f060_r6_sin_ficha_ni_dni_rec_del_recurso() -> None:
    """Casada sin ficha por su recurso (F-035): `rec-501`, tambien con el
    recurso en `empleado_reside`."""
    from infrastructure.database.parte_repository import persona_de
    from infrastructure.database.orm_models import ParteRegistroOrm
    f = _fabrica()
    d1 = _v(f, 1, dni=None, empleado_ide=None)
    d2 = _v(f, 2, dni=None, empleado_ide=None)
    _t(f, 1, dni=None, empleado_ide=None, recurso_ide=502, doc="t502")
    _casar_por_recurso(f, d1, d2)
    with f.create_session() as s:
        assert persona_de(s.get(ParteRegistroOrm, d2)) == "rec-501"
    assert _linea(_datos(f, [d2]), d2)["racha_registro_ids"] == [d1]


def test_f060_r6_sin_ficha_ni_casar_por_el_nombre_leido() -> None:
    f = _fabrica()
    d1 = _v(f, 1, dni=None, empleado_ide=None)
    d2 = _v(f, 2, dni=None, empleado_ide=None)
    _t(f, 1, dni=None, empleado_ide=None, nombre="Otra", doc="otra")
    assert _linea(_datos(f, [d2]), d2)["racha_registro_ids"] == [d1]


def test_f060_r6_el_dni_se_compara_normalizado() -> None:
    f = _fabrica()
    d1 = _v(f, 1, dni="1234-5678 z")
    _t(f, 1, dni=DNI_B, doc="b1")
    d2 = _v(f, 2, dni=DNI_A)
    assert _linea(_datos(f, [d2]), d2)["racha_registro_ids"] == [d1]


def test_f060_r6_otro_dni_no_cuenta() -> None:
    f = _fabrica()
    _v(f, 1, dni=DNI_B)
    d2 = _v(f, 2, dni=DNI_A)
    assert _roles(_datos(f, [d2])) == {d2: "inicio"}


def test_f060_r7_aprobar_la_racha_de_una_vez_en_dos_obras() -> None:
    f = _fabrica()
    d1 = _v(f, 1)
    d2 = _v(f, 2, obra=OBRA_20)
    d3 = _v(f, 3)
    d4 = _v(f, 4, obra=OBRA_20)
    datos = _datos(f, [d1, d2, d3, d4])
    assert _roles(datos) == {d1: "inicio", d2: "intermedio",
                             d3: "intermedio", d4: "fin"}
    assert _linea(datos, d4)["racha_registro_ids"] == [d1, d2, d3]
    assert _linea(datos, d2)["racha_registro_ids"] == []


def test_f060_r8_dos_inicios_del_mismo_dia() -> None:
    f = _fabrica()
    a = _v(f, 1)
    b = _v(f, 1, obra=OBRA_20, doc="v1b")
    assert _roles(_datos(f, [b, a])) == {a: "inicio", b: "intermedio"}


def test_f060_r1_sin_fecha_es_inicio() -> None:
    from infrastructure.database.orm_models import ParteRegistroOrm
    f = _fabrica()
    d = _v(f, 1)
    with f.create_session() as s:
        s.get(ParteRegistroOrm, d).fecha_int = None
        s.commit()
    l = _linea(_datos(f, [d]), d)
    assert (l["incidencia_rol"], l["racha_registro_ids"]) == ("inicio", [])


# ========================= R10 · avisos_racha ========================= #

def _avisos(datos) -> list[dict]:
    return [a for g in datos["grupos"] for a in g["avisos_racha"]]


def test_f060_r10_trabajo_antes_de_una_incidencia_registrada() -> None:
    f = _fabrica()
    _v(f, 5, estado="registrado")
    t = _t(f, 4)
    datos = _datos(f, [t])
    assert [l["registro_id"] for l in datos["lineas"]] == [t]   # viaja
    (aviso,) = _avisos(datos)
    assert aviso["registro_id"] == t and aviso["fecha"] == _dia(4)
    assert aviso["nombre"] == "Persona A"
    assert aviso["motivo"].startswith("racha_desordenada: el 2026-10-05")


def test_f060_r10_inicio_antes_de_una_incidencia_registrada() -> None:
    f = _fabrica()
    _v(f, 5, estado="registrado")
    d4 = _v(f, 4, letra="B")
    assert [a["registro_id"] for a in _avisos(_datos(f, [d4]))] == [d4]


def test_f060_r10_un_fin_no_avisa() -> None:
    f = _fabrica()
    _v(f, 3)
    _v(f, 5, estado="registrado")
    d4 = _v(f, 4)
    assert _avisos(_datos(f, [d4])) == []


@pytest.mark.parametrize("estado", [None, "omitido", "encolado"])
def test_f060_r10_sin_registrar_no_avisa(estado) -> None:
    f = _fabrica()
    _v(f, 5, estado=estado)
    assert _avisos(_datos(f, [_t(f, 4)])) == []


def test_f060_r10_trabajo_a_cero_no_avisa() -> None:
    f = _fabrica()
    _v(f, 5, estado="registrado")
    assert _avisos(_datos(f, [_t(f, 4, horas=0.0)])) == []


def test_f060_r10_cada_grupo_lleva_los_suyos() -> None:
    f = _fabrica()
    _v(f, 5, estado="registrado")
    a = _t(f, 4)
    b = _t(f, 4, obra=OBRA_20, doc="t4b")
    datos = _datos(f, [a, b])
    por_grupo = {g["clave"]: [x["registro_id"] for x in g["avisos_racha"]]
                 for g in datos["grupos"]}
    assert por_grupo == {"obr-10": [a], "obr-20": [b]}


# ================= R12 · una consulta por persona ================= #

def _contar_historicos(fabrica) -> list[str]:
    vistos: list[str] = []

    @event.listens_for(fabrica.engine, "before_cursor_execute")
    def _apuntar(conn, cursor, statement, params, context, many):
        if "BETWEEN" in statement:
            vistos.append(statement)
    return vistos


def test_f060_r12_una_consulta_por_persona_y_aprobacion() -> None:
    f = _fabrica()
    ids = [_v(f, n) for n in (1, 2, 3)] + [_t(f, 4)]
    ids += [_v(f, n, dni=DNI_B, doc=f"b{n}") for n in (1, 2)]
    vistos = _contar_historicos(f)
    _datos(f, ids)
    assert len(vistos) == 2


def test_f060_r12_sin_lineas_de_trabajo_ni_incidencia_no_consulta() -> None:
    f = _fabrica()
    t = _t(f, 4, horas=0.0)
    vistos = _contar_historicos(f)
    _datos(f, [t])
    assert vistos == []
