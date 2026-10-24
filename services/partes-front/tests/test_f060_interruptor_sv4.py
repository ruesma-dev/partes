# tests/test_f060_interruptor_sv4.py
"""F-060 · Interruptor `MOVER_CIZ` de sv4 (R26 bis, DA12; `design.md` §3.1).

Con `MOVER_CIZ` apagado (el defecto), sv4 da a cada incidencia el rol del
`_rol_incidencia` de dev 0926857 tal cual, linea a linea (`intermedio`
si el siguiente dia ya ingerido es incidencia), sin R7/R8, con
`racha_registro_ids` vacia en toda linea y `avisos_racha` vacia en todo
grupo: con sv4 y sv5 apagados, en Sigrid queda lo mismo que en dev
0926857. Encendido, la regla nueva de F-060.

El escenario de la review pasada 1: V los dias 1-4 y 8 h el 5 ya
ingeridos, aprobando el 2, luego el 3 y luego el 4.

Sin red ni PostgreSQL: SQLite en memoria con el MISMO ORM (`dobles.py`).
Personas, DNIs, obras y partes SINTETICOS.
"""
from __future__ import annotations

import pytest

from infrastructure.database import parte_repository as repo_mod
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite
from tests.test_f025_aprobacion import OBRA_20, sembrar
from tests.test_f025_deteccion import TABLA


def _dia(n: int) -> str:
    return f"2026-10-{n:02d}"


def _v(fabrica, n, *, estado=None, **kw) -> int:
    return sembrar(fabrica, [{"inc": "V", "estado": estado}],
                   doc=kw.pop("doc", f"v{n}"), fecha=_dia(n), **kw)[0]


def _t(fabrica, n, **kw) -> int:
    return sembrar(fabrica, [{"horas": 8.0}], doc=kw.pop("doc", f"t{n}"),
                   fecha=_dia(n), **kw)[0]


def _datos(fabrica, ids, **kw) -> dict:
    return ParteReviewRepository(fabrica).lineas_para_registro(
        ids, incidencias=TABLA, **kw)


def _rol_y_racha(datos, rid) -> tuple[str, list[int]]:
    linea = next(l for l in datos["lineas"] if l["registro_id"] == rid)
    return linea["incidencia_rol"], linea["racha_registro_ids"]


def _avisos(datos) -> list[dict]:
    return [a for g in datos["grupos"] for a in g["avisos_racha"]]


def _racha_1_a_4_y_trabajo_el_5(fabrica) -> list[int]:
    ids = [_v(fabrica, n) for n in (1, 2, 3, 4)]
    _t(fabrica, 5)
    return ids


# ================== apagado = dev 0926857 (R26 bis) ================== #

def test_f060_r26bis_apagado_dia_a_dia_como_dev_0926857() -> None:
    """La divergencia de la review pasada 1: apagado, el 2 y el 3 son
    `intermedio` (el siguiente dia ya ingerido es V) y el 4 `fin`."""
    f = FabricaSesionSqlite()
    d1, d2, d3, d4 = _racha_1_a_4_y_trabajo_el_5(f)
    vistos = [_rol_y_racha(_datos(f, [d]), d) for d in (d2, d3, d4)]
    assert vistos == [("intermedio", []), ("intermedio", []), ("fin", [])]


def test_f060_r26bis_apagado_es_el_defecto_y_false_explicito() -> None:
    f = FabricaSesionSqlite()
    _d1, d2, _d3, _d4 = _racha_1_a_4_y_trabajo_el_5(f)
    assert _datos(f, [d2]) == _datos(f, [d2], mover_ciz=False)


def test_f060_r26bis_encendido_dia_a_dia_regla_nueva() -> None:
    f = FabricaSesionSqlite()
    d1, d2, d3, d4 = _racha_1_a_4_y_trabajo_el_5(f)
    vistos = [_rol_y_racha(_datos(f, [d], mover_ciz=True), d)
              for d in (d2, d3, d4)]
    assert vistos == [("fin", [d1, d3, d4]), ("fin", [d1, d2, d4]),
                      ("fin", [d1, d2, d3])]


def test_f060_r26bis_apagado_de_una_vez_sin_colapsar() -> None:
    f = FabricaSesionSqlite()
    d1, d2, d3, d4 = _racha_1_a_4_y_trabajo_el_5(f)
    datos = _datos(f, [d1, d2, d3, d4])
    assert [_rol_y_racha(datos, d) for d in (d1, d2, d3, d4)] == [
        ("inicio", []), ("intermedio", []), ("intermedio", []), ("fin", [])]


def test_f060_r26bis_apagado_sin_r8_dos_inicios_del_mismo_dia() -> None:
    """Sin `colapsar`: dos V del mismo dia sin nada antes son `inicio`
    las dos, como en dev 0926857 (encendido, la segunda `intermedio`)."""
    f = FabricaSesionSqlite()
    a = _v(f, 1)
    b = _v(f, 1, obra=OBRA_20, doc="v1b")
    apagado = _datos(f, [a, b])
    assert [_rol_y_racha(apagado, x)[0] for x in (a, b)] == ["inicio",
                                                            "inicio"]
    encendido = _datos(f, [a, b], mover_ciz=True)
    assert [_rol_y_racha(encendido, x)[0] for x in (a, b)] == [
        "inicio", "intermedio"]


def test_f060_r26bis_apagado_el_documento_inactivo_cuenta_como_antes() -> \
        None:
    """dev 0926857 no miraba `is_active` del documento: un dia trabajado
    en un documento inactivo cierra la racha (encendido se salta, R5)."""
    f = FabricaSesionSqlite()
    _v(f, 1)
    sembrar(f, [{"horas": 8.0}], doc="t2", fecha=_dia(2), doc_activo=False)
    d3 = _v(f, 3)
    assert _rol_y_racha(_datos(f, [d3]), d3) == ("inicio", [])
    assert _rol_y_racha(_datos(f, [d3], mover_ciz=True), d3)[0] == "fin"


def test_f060_r26bis_apagado_sin_avisos_racha() -> None:
    f = FabricaSesionSqlite()
    _v(f, 5, estado="registrado")
    t = _t(f, 4)
    assert _avisos(_datos(f, [t])) == []
    assert [a["registro_id"] for a in
            _avisos(_datos(f, [t], mover_ciz=True))] == [t]
    assert all(g["avisos_racha"] == [] for g in _datos(f, [t])["grupos"])


def test_f060_r26bis_apagado_no_usa_la_regla_nueva(monkeypatch) -> None:
    """Apagado no se llama a `_roles_de_racha`, `colapsar` ni
    `aviso_desordenada`."""
    def prohibido(*_a, **_k):
        raise AssertionError("regla nueva con MOVER_CIZ apagado")
    monkeypatch.setattr(ParteReviewRepository, "_roles_de_racha",
                        prohibido)
    monkeypatch.setattr(repo_mod, "colapsar", prohibido)
    monkeypatch.setattr(repo_mod, "aviso_desordenada", prohibido)
    f = FabricaSesionSqlite()
    d1, d2, d3, d4 = _racha_1_a_4_y_trabajo_el_5(f)
    datos = _datos(f, [d1, d2, d3, d4, _t(f, 6)])
    assert _rol_y_racha(datos, d4) == ("fin", [])


def test_f060_r26bis_rol_anterior_linea_a_linea() -> None:
    """`_rol_incidencia_anterior` es el `_rol_incidencia` de dev 0926857
    (staticmethod sobre la sesion y la linea)."""
    from infrastructure.database.orm_models import ParteRegistroOrm
    f = FabricaSesionSqlite()
    d1, d2, d3, d4 = _racha_1_a_4_y_trabajo_el_5(f)
    with f.create_session() as s:
        roles = [ParteReviewRepository._rol_incidencia_anterior(
            s, s.get(ParteRegistroOrm, d)) for d in (d1, d2, d3, d4)]
    assert roles == ["inicio", "intermedio", "intermedio", "fin"]


# ---- caracterizacion de `_rol_incidencia_anterior` (dev 0926857, T23) ---- #
# Copia LITERAL del rol de dev 0926857 (DA12): estos tests fijan su
# comportamiento tal cual, incluidos sus topes, no lo que deberia hacer.

def _rol_anterior(fabrica, rid) -> str:
    from infrastructure.database.orm_models import ParteRegistroOrm
    with fabrica.create_session() as s:
        return ParteReviewRepository._rol_incidencia_anterior(
            s, s.get(ParteRegistroOrm, rid))


def test_f060_r26bis_rol_anterior_sin_dia_posterior_es_fin() -> None:
    """Racha que viene de atras y nada despues de D: `fin` (sin
    siguientes, la racha termina aqui), no `intermedio`."""
    f = FabricaSesionSqlite()
    _v(f, 1)
    d2 = _v(f, 2)
    assert _rol_anterior(f, d2) == "fin"


def test_f060_r26bis_rol_anterior_sin_dni_solo_cuenta_su_empleado() -> None:
    """Sin DNI la identidad es `empleado_ide`: los dias trabajados de OTRO
    empleado (sin DNI) en la misma obra y fechas no cuentan; su V del 1 si."""
    f = FabricaSesionSqlite()
    _v(f, 1, dni=None, empleado_ide=77)
    _t(f, 1, dni=None, empleado_ide=88, doc="otro1", nombre="Persona B")
    _t(f, 3, dni=None, empleado_ide=88, doc="otro3", nombre="Persona B")
    d2 = _v(f, 2, dni=None, empleado_ide=77)
    assert _rol_anterior(f, d2) == "fin"


def _dia_de(fabrica, n, total: int, *, trabajo_primero: bool) -> None:
    """Un parte del dia `n` con `total` lineas de la persona: todas V
    salvo UNA de trabajo, la primera o la ultima en orden de insercion."""
    lineas = [{"inc": "V"} for _ in range(total - 1)]
    lineas.insert(0 if trabajo_primero else total - 1, {"horas": 8.0})
    sembrar(fabrica, lineas, doc=f"d{n}", fecha=_dia(n))


def test_f060_r26bis_rol_anterior_tope_de_50_filas_hacia_atras() -> None:
    """dev 0926857 lee como mucho 50 filas hacia atras. Con 50 lineas el
    dia anterior las ve todas: la de trabajo lo hace trabajado (`inicio`)
    este donde este. Con 51, una se queda fuera: segun el orden de las
    empatadas en fecha sera la primera o la ultima insertada, asi que al
    menos una de las dos colocaciones ve el dia solo con V (la racha
    viene de atras y no hay nada delante => `fin`)."""
    def rol(total: int, trabajo_primero: bool) -> str:
        f = FabricaSesionSqlite()
        _dia_de(f, 1, total, trabajo_primero=trabajo_primero)
        return _rol_anterior(f, _v(f, 2))
    assert {rol(50, p) for p in (True, False)} == {"inicio"}
    assert "fin" in {rol(51, p) for p in (True, False)}


def test_f060_r26bis_rol_anterior_tope_de_50_filas_hacia_delante() -> None:
    """Igual hacia delante: con 50 lineas el dia siguiente es trabajado
    (`fin`); con 51, al menos una colocacion lo ve solo con V
    (`intermedio`)."""
    def rol(total: int, trabajo_primero: bool) -> str:
        f = FabricaSesionSqlite()
        _v(f, 1)
        d2 = _v(f, 2)
        _dia_de(f, 3, total, trabajo_primero=trabajo_primero)
        return _rol_anterior(f, d2)
    assert {rol(50, p) for p in (True, False)} == {"fin"}
    assert "intermedio" in {rol(51, p) for p in (True, False)}


# ============== Settings y app.py (MOVER_CIZ de sv4) ============== #

@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {"PG_PASSWORD": "irrelevante-en-tests",
                         "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
                         "DEFAULT_REVIEWER": "ana",
                         "TRANSFER_BASE_URL": "http://sv5.interno"}.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.delenv("INCIDENCIAS_PATH", raising=False)
    monkeypatch.delenv("MOVER_CIZ", raising=False)
    return monkeypatch


def test_f060_r26bis_settings_mover_ciz_apagado_por_defecto(entorno) -> None:
    from config.settings import Settings
    assert Settings(_env_file=None).mover_ciz is False
    entorno.setenv("MOVER_CIZ", "true")
    assert Settings(_env_file=None).mover_ciz is True


def _portal(fabrica):
    from config.settings import Settings
    from fastapi.testclient import TestClient
    from interface_adapters.web.app import build_app
    from tests.test_f022_aprobar_seleccion import (
        CalendarioFalso,
        PublisherFalso,
        Sv5Falso,
    )
    sv5 = Sv5Falso()
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica),
                    transfer_client=sv5, publisher=PublisherFalso(),
                    calendario_provider=CalendarioFalso())
    return TestClient(app), sv5


@pytest.mark.parametrize("valor,esperado", [
    (None, ("intermedio", [])),
    ("false", ("intermedio", [])),
    ("true", "fin"),
])
def test_f060_r26bis_app_pasa_mover_ciz(entorno, valor, esperado) -> None:
    if valor is not None:
        entorno.setenv("MOVER_CIZ", valor)
    f = FabricaSesionSqlite()
    d1, d2, d3, d4 = _racha_1_a_4_y_trabajo_el_5(f)
    cliente, sv5 = _portal(f)
    cliente.post("/api/aprobar/ejecutar", json={"registro_ids": [d2]})
    (payload,) = sv5.ejecutadas
    (linea,) = payload["lineas"]
    visto = (linea["incidencia_rol"], linea["racha_registro_ids"])
    if esperado == "fin":
        assert visto == ("fin", [d1, d3, d4])
    else:
        assert visto == esperado


def test_f060_r26bis_preflight_apagado_sin_avisos_racha(entorno) -> None:
    f = FabricaSesionSqlite()
    _v(f, 5, estado="registrado")
    t = _t(f, 4)
    cliente, _sv5 = _portal(f)
    r = cliente.post("/api/aprobar/preflight", json={"registro_ids": [t]})
    assert r.status_code == 200
    (grupo,) = r.json()["grupos"]
    assert grupo["avisos_racha"] == []
