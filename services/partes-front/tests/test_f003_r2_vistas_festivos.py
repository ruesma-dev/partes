# tests/test_f003_r2_vistas_festivos.py
"""R2, R3 y R22 · las vistas del portal usan el calendario del trabajador.

Hasta F-003 el portal marcaba festivos con un calendario GLOBAL (Madrid,
via libreria `holidays`): a un trabajador de otra provincia le contaba
como laborable un dia que para el era fiesta, y le salia un aviso de
jornada incompleta falso. Aqui se comprueba que cada trabajador se
evalua con SU calendario, y que una resolucion degradada enciende el
aviso visible de la UI en vez de pasar en silencio.

El proveedor entra por inyeccion (`build_app(..., calendario_provider=)`),
asi que no hay ni red ni Sesame.
"""
from __future__ import annotations

from datetime import date

import pytest
from application.services.calendario_provider import DiaCalendario
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_dias

#: 2026-05-15 (viernes) es festivo SOLO para el DNI de Pepe; 2026-05-14
#: (jueves) lo es solo en el calendario por defecto de la obra.
SAN_ISIDRO = "2026-05-15"
FIESTA_DEFECTO = "2026-05-14"


class ProveedorFake:
    """Doble del `CalendarioProvider`: festivos por DNI y fiabilidad."""

    def __init__(self, *, por_dni=None, por_defecto=(), fiable: bool = True,
                 jornada=None) -> None:
        self._por_dni = por_dni or {}
        self._por_defecto = set(por_defecto)
        self._fiable = fiable
        self._jornada = jornada
        self.activo = True
        self.consultas: list[tuple] = []

    def _festivos(self, dni: str | None) -> set[str]:
        if dni is None:
            return self._por_defecto
        return set(self._por_dni.get(_norm(dni), self._por_defecto))

    def holiday_name_para(self, dni):
        self.consultas.append(("holiday_name", dni))
        festivos = self._festivos(dni)

        def _nombre(d: date) -> str | None:
            return "Fiesta de prueba" if d.isoformat() in festivos else None
        return _nombre

    def dia(self, d: date, dni):
        nombre = self.holiday_name_para(dni)(d)
        finde = d.weekday() >= 5
        return DiaCalendario(
            fecha=d.isoformat(), laborable=not (finde or bool(nombre)),
            fin_de_semana=finde, festivo=bool(nombre),
            festivo_nombre=nombre, fiable=self._fiable,
        )

    def jornada_contrato(self, dni):
        return self._jornada

    def fiable_para(self, consultas):
        self.consultas.append(("fiable_para", sorted(
            (str(d), a) for d, a in consultas)))
        return self._fiable


def _norm(dni: str | None) -> str:
    import re
    return re.sub(r"[^0-9A-Za-z]", "", dni or "").upper()


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


def _monta(entorno, dias, proveedor, **kw):
    fabrica = FabricaSesionSqlite()
    sembrar_dias(fabrica, dias, **kw)
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica),
                    calendario_provider=proveedor)
    return TestClient(app)


# ------------------- R3 · calendario de la vista trabajador ------------- #

def test_f003_r3_el_calendario_marca_los_festivos_del_trabajador(
        entorno) -> None:
    proveedor = ProveedorFake(por_dni={"12345678Z": {SAN_ISIDRO}})
    cliente = _monta(entorno, [{"fecha": SAN_ISIDRO, "horas": 8.0,
                                "candef": 8.0}], proveedor)
    html = cliente.get("/trabajadores/emp-77?modo=natural").text
    assert "cal-fest" in html
    assert "Fiesta de prueba" in html


def test_f003_r3_pregunta_por_el_dni_del_trabajador(entorno) -> None:
    proveedor = ProveedorFake(por_dni={"12345678Z": {SAN_ISIDRO}})
    cliente = _monta(entorno, [{"fecha": SAN_ISIDRO, "horas": 8.0}],
                     proveedor)
    cliente.get("/trabajadores/emp-77?modo=natural")
    assert ("holiday_name", "12345678Z") in proveedor.consultas


def test_f003_r3_otro_trabajador_no_hereda_la_fiesta(entorno) -> None:
    """El mismo dia, para quien no tiene ese calendario, es laborable."""
    proveedor = ProveedorFake(por_dni={"11111111A": {SAN_ISIDRO}})
    cliente = _monta(entorno, [{"fecha": SAN_ISIDRO, "horas": 8.0}],
                     proveedor)
    assert "cal-fest" not in cliente.get(
        "/trabajadores/emp-77?modo=natural").text


# ---------------- R2 · avisos de jornada incompleta por DNI ------------- #

def test_f003_r2_el_festivo_del_trabajador_no_genera_aviso(entorno) -> None:
    """4 h en su festivo: no es jornada incompleta, es un dia de fiesta."""
    proveedor = ProveedorFake(por_dni={"12345678Z": {SAN_ISIDRO}})
    cliente = _monta(entorno, [{"fecha": SAN_ISIDRO, "horas": 4.0,
                                "candef": 8.0}], proveedor)
    assert "cal-warn" not in cliente.get(
        "/trabajadores/emp-77?modo=natural").text


def test_f003_r2_sin_ese_festivo_el_mismo_dia_si_avisa(entorno) -> None:
    proveedor = ProveedorFake(por_dni={"11111111A": {SAN_ISIDRO}})
    cliente = _monta(entorno, [{"fecha": SAN_ISIDRO, "horas": 4.0,
                                "candef": 8.0}], proveedor)
    assert "cal-warn" in cliente.get(
        "/trabajadores/emp-77?modo=natural").text


def test_f003_r2_la_matriz_de_obra_evalua_con_el_dni_de_la_fila(
        entorno) -> None:
    """La columna se tinta con el calendario por defecto (D6), pero el
    aviso de jornada incompleta usa el calendario de cada trabajador."""
    proveedor = ProveedorFake(por_dni={"12345678Z": {SAN_ISIDRO}},
                              por_defecto={FIESTA_DEFECTO})
    cliente = _monta(entorno, [{"fecha": SAN_ISIDRO, "horas": 4.0,
                                "candef": 8.0}], proveedor)
    html = cliente.get("/obras/obr-10?period=2026-05&modo=natural").text
    assert "mx-warn" not in html


def test_f003_r2_la_matriz_avisa_si_el_dia_no_es_su_festivo(entorno) -> None:
    proveedor = ProveedorFake(por_dni={"11111111A": {SAN_ISIDRO}},
                              por_defecto=set())
    cliente = _monta(entorno, [{"fecha": SAN_ISIDRO, "horas": 4.0,
                                "candef": 8.0}], proveedor)
    html = cliente.get("/obras/obr-10?period=2026-05&modo=natural").text
    assert "mx-warn" in html


def test_f003_r2_la_columna_de_la_matriz_usa_el_calendario_por_defecto(
        entorno) -> None:
    """D6: una consulta por columna, no una por fila x dia."""
    proveedor = ProveedorFake(por_dni={"12345678Z": {SAN_ISIDRO}},
                              por_defecto={FIESTA_DEFECTO})
    cliente = _monta(entorno, [{"fecha": SAN_ISIDRO, "horas": 8.0}],
                     proveedor)
    html = cliente.get("/obras/obr-10?period=2026-05&modo=natural").text
    assert "mx-hol" in html   # el 14, del calendario por defecto
    assert ("holiday_name", None) in proveedor.consultas


# --------------------- R22 · aviso visible de degradacion --------------- #

def test_f003_r22_la_vista_trabajador_avisa_si_la_resolucion_degrado(
        entorno) -> None:
    proveedor = ProveedorFake(por_dni={"12345678Z": set()}, fiable=False)
    cliente = _monta(entorno, [{"fecha": SAN_ISIDRO, "horas": 8.0}],
                     proveedor)
    html = cliente.get("/trabajadores/emp-77?modo=natural").text
    assert "sesame-degradado" in html
    assert "Sesame no disponible" in html


def test_f003_r22_la_matriz_de_obra_avisa_si_la_resolucion_degrado(
        entorno) -> None:
    proveedor = ProveedorFake(por_defecto=set(), fiable=False)
    cliente = _monta(entorno, [{"fecha": SAN_ISIDRO, "horas": 8.0}],
                     proveedor)
    html = cliente.get("/obras/obr-10?period=2026-05&modo=natural").text
    assert "sesame-degradado" in html


def test_f003_r22_sin_degradacion_no_hay_banner(entorno) -> None:
    proveedor = ProveedorFake(por_dni={"12345678Z": set()}, fiable=True)
    cliente = _monta(entorno, [{"fecha": SAN_ISIDRO, "horas": 8.0}],
                     proveedor)
    assert "sesame-degradado" not in cliente.get(
        "/trabajadores/emp-77?modo=natural").text
    assert "sesame-degradado" not in cliente.get(
        "/obras/obr-10?period=2026-05&modo=natural").text


def test_f003_r22_la_vista_se_sirve_igual_estando_degradada(entorno) -> None:
    """Nivel 1: informa, pero no se cae. Un portal caido por RRHH seria
    peor que un festivo sin refrescar."""
    proveedor = ProveedorFake(por_dni={"12345678Z": set()}, fiable=False)
    cliente = _monta(entorno, [{"fecha": SAN_ISIDRO, "horas": 8.0}],
                     proveedor)
    assert cliente.get("/trabajadores/emp-77?modo=natural").status_code == 200
    assert cliente.get(
        "/obras/obr-10?period=2026-05&modo=natural").status_code == 200


def test_f003_r22_la_consulta_de_fiabilidad_lleva_dni_y_ano(entorno) -> None:
    proveedor = ProveedorFake(por_dni={"12345678Z": set()})
    cliente = _monta(entorno, [{"fecha": SAN_ISIDRO, "horas": 8.0}],
                     proveedor)
    cliente.get("/trabajadores/emp-77?modo=natural")
    consultas = [c for c in proveedor.consultas if c[0] == "fiable_para"]
    assert consultas and consultas[0][1] == [("12345678Z", 2026)]


def test_f003_r22_solo_cuentan_los_dias_del_periodo(entorno) -> None:
    """La rejilla de enero arrastra dias de diciembre para cuadrar la
    semana. Esos NO son del periodo: si contaran, la vista consultaria
    (y podria declarar degradado) un ano que no esta mirando."""
    proveedor = ProveedorFake(por_dni={"12345678Z": set()})
    cliente = _monta(entorno, [{"fecha": "2026-01-05", "horas": 8.0}],
                     proveedor)
    cliente.get("/trabajadores/emp-77?period=2026-01&modo=natural")
    consultas = [c for c in proveedor.consultas if c[0] == "fiable_para"]
    assert consultas and consultas[0][1] == [("12345678Z", 2026)]


# ------------------------- el DNI de la fila (D6) ----------------------- #

def test_f003_r2_la_fila_de_la_matriz_lleva_el_dni(entorno) -> None:
    """Sin DNI en la fila, `incompletos` tendria que seguir agrupando por
    NOMBRE y no habria manera de evaluar el festivo de cada uno."""
    from infrastructure.database.parte_repository import ParteReviewRepository

    fabrica = FabricaSesionSqlite()
    sembrar_dias(fabrica, [{"fecha": SAN_ISIDRO, "horas": 8.0}])
    detalle = ParteReviewRepository(fabrica).get_obra(
        "obr-10", period_key="2026-05", mode="natural")
    assert detalle is not None
    assert [r.dni for r in detalle.rows] == ["12345678Z"]
