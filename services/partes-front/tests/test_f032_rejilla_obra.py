# tests/test_f032_rejilla_obra.py
"""F-032 · R26–R28: la rejilla de obra marca los festivos de cada persona.

Hasta F-032 la columna de un dia se teñía con el calendario por defecto
(D6 de F-003): una sola consulta, igual para todas las filas. Con los
festivos guardados por trabajador, cada CELDA se marca con el calendario
del DNI de su fila (`mx-hol`, nombre en el `title`); la cabecera solo
marca fin de semana y fecha futura (R27). Una fila sin DNI usa el
respaldo (R26). El aviso degradado se evalua sobre (DNI de fila x ano),
sin consultar `(None, ano)` por la cabecera, y dice «Los festivos
marcados en la rejilla y los avisos de jornada incompleta…» (R28).

SQLite en memoria y `ProveedorFake`; sin red. Datos sinteticos.
"""
from __future__ import annotations

import re
from datetime import date

import pytest
from fastapi.testclient import TestClient

from config.settings import Settings
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from tests.dobles import FabricaSesionSqlite, sembrar_parte
from tests.test_f003_r2_vistas_festivos import ProveedorFake

DNI_A = "12345678Z"
DNI_B = "87654321X"
SAN_ISIDRO = "2026-05-15"          # viernes: festivo solo para A
FIESTA_DEFECTO = "2026-05-14"      # jueves: solo del calendario por defecto
URL = "/obras/obr-10?period=2026-05&modo=natural"


@pytest.fixture
def entorno(monkeypatch):
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    return monkeypatch


def _sembrar(fabrica, *, sin_dni=False):
    for fecha in (FIESTA_DEFECTO, SAN_ISIDRO):
        sembrar_parte(fabrica, [{"horas": 8.0}], document_id=f"a-{fecha}",
                      fecha=fecha, empleado_ide=77, empleado_dni=DNI_A,
                      empleado_nombre="Persona A", recurso_ide=501)
        sembrar_parte(fabrica, [{"horas": 8.0}], document_id=f"b-{fecha}",
                      fecha=fecha, empleado_ide=88, empleado_dni=DNI_B,
                      empleado_nombre="Persona B", recurso_ide=502)
        if sin_dni:
            sembrar_parte(fabrica, [{"horas": 8.0}],
                          document_id=f"c-{fecha}", fecha=fecha,
                          empleado_ide=None, empleado_dni=None,
                          empleado_nombre="Persona C", recurso_ide=503)


def _montar(proveedor, *, sin_dni=False):
    fabrica = FabricaSesionSqlite()
    _sembrar(fabrica, sin_dni=sin_dni)
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica),
                    calendario_provider=proveedor)
    return TestClient(app), fabrica


def _proveedor(**kw):
    return ProveedorFake(por_dni={DNI_A: {SAN_ISIDRO}, DNI_B: set()},
                         por_defecto={FIESTA_DEFECTO}, **kw)


def _celda(html: str, nombre: str, fecha: str) -> str:
    """El `<td ...>` de la celda de esa fila y ese dia."""
    for m in re.finditer(r"<td class=\"mx-cell[^>]*>", html, re.S):
        td = m.group(0)
        if (f'data-fecha="{fecha}"' in td
                and f'data-trabajador="{nombre}"' in td):
            return td
    raise AssertionError(f"sin celda para {nombre} el {fecha}")


def _cabecera(html: str, fecha: str) -> str:
    for m in re.finditer(r"<th class=\"mx-day[^>]*>", html, re.S):
        if f'title="{fecha}' in m.group(0):
            return m.group(0)
    raise AssertionError(f"sin cabecera del {fecha}")


# --------------------------------- R26 ---------------------------------- #

def test_f032_r26_cada_fila_con_su_calendario(entorno) -> None:
    cliente, _f = _montar(_proveedor())
    html = cliente.get(URL).text
    a = _celda(html, "Persona A", SAN_ISIDRO)
    b = _celda(html, "Persona B", SAN_ISIDRO)
    assert "mx-hol" in a and "Fiesta de prueba" in a
    assert "mx-hol" not in b
    # El festivo del calendario por defecto no vale para quien tiene DNI.
    assert "mx-hol" not in _celda(html, "Persona A", FIESTA_DEFECTO)


def test_f032_r26_la_fila_sin_dni_usa_el_respaldo(entorno) -> None:
    proveedor = _proveedor()
    cliente, _f = _montar(proveedor, sin_dni=True)
    html = cliente.get(URL).text
    assert "mx-hol" in _celda(html, "Persona C", FIESTA_DEFECTO)
    assert "mx-hol" not in _celda(html, "Persona C", SAN_ISIDRO)
    assert ("holiday_name", None) in proveedor.consultas


def test_f032_r26_un_holiday_name_por_fila(entorno) -> None:
    proveedor = _proveedor()
    cliente, _f = _montar(proveedor)
    cliente.get(URL)
    pedidos = [c[1] for c in proveedor.consultas if c[0] == "holiday_name"]
    assert None not in pedidos
    assert set(pedidos) == {DNI_A, DNI_B}


# --------------------------------- R27 ---------------------------------- #

def test_f032_r27_la_cabecera_no_marca_festivos(entorno) -> None:
    cliente, _f = _montar(_proveedor())
    html = cliente.get(URL).text
    for fecha in (SAN_ISIDRO, FIESTA_DEFECTO):
        th = _cabecera(html, fecha)
        assert "mx-hol" not in th
        assert "Fiesta de prueba" not in th
    assert "mx-we" in _cabecera(html, "2026-05-16")       # sabado


# --------------------------------- R28 ---------------------------------- #

def test_f032_r28_nunca_se_pide_none_si_todas_las_filas_tienen_dni(
        entorno) -> None:
    proveedor = _proveedor()
    cliente, _f = _montar(proveedor)
    cliente.get(URL)
    [consulta] = [c[1] for c in proveedor.consultas if c[0] == "fiable_para"]
    assert ("None", 2026) not in consulta
    assert consulta == sorted([(DNI_A, 2026), (DNI_B, 2026)])


def test_f032_r28_con_todas_las_filas_fiables_no_hay_aviso(entorno) -> None:
    cliente, _f = _montar(_proveedor(fiable=True))
    assert "sesame-degradado" not in cliente.get(URL).text


def test_f032_r28_el_aviso_lleva_el_texto_nuevo(entorno) -> None:
    cliente, _f = _montar(_proveedor(fiable=False))
    html = cliente.get(URL).text
    i = html.index("sesame-degradado")
    aviso = html[i:html.index("</div>", i)]
    assert "Sin calendario de Sesame" in aviso
    assert ("Los festivos marcados en la rejilla y los avisos de jornada "
            "incompleta") in aviso


def test_f032_r28_el_teñido_y_la_jornada_incompleta_usan_el_mismo(
        entorno) -> None:
    """A trabaja 6 h el 15 (festivo para el): ni aviso de jornada
    incompleta ni celda laborable; B, 6 h el 15, si tiene aviso."""
    fabrica = FabricaSesionSqlite()
    for nombre, ide, dni, rec in (("Persona A", 77, DNI_A, 501),
                                  ("Persona B", 88, DNI_B, 502)):
        sembrar_parte(fabrica, [{"horas": 6.0}], document_id=f"d-{rec}",
                      fecha=SAN_ISIDRO, empleado_ide=ide, empleado_dni=dni,
                      empleado_nombre=nombre, recurso_ide=rec)
    app = build_app(Settings(_env_file=None),
                    repository=ParteReviewRepository(fabrica),
                    calendario_provider=_proveedor())
    html = TestClient(app).get(URL).text
    a = _celda(html, "Persona A", SAN_ISIDRO)
    b = _celda(html, "Persona B", SAN_ISIDRO)
    assert "mx-hol" in a and "mx-warn" not in a
    assert "mx-hol" not in b and "mx-warn" in b


# ------------------------- get_obra directo ----------------------------- #

def test_f032_r26_get_obra_con_holiday_name_de(entorno) -> None:
    fabrica = FabricaSesionSqlite()
    _sembrar(fabrica, sin_dni=True)
    pedidos = []

    def holiday_name_de(dni):
        pedidos.append(dni)
        festivos = {DNI_A: {SAN_ISIDRO}, DNI_B: set()}.get(
            dni, {FIESTA_DEFECTO})

        def _nombre(d: date):
            return f"Fiesta {dni}" if d.isoformat() in festivos else None
        return _nombre

    det = ParteReviewRepository(fabrica).get_obra(
        "obr-10", period_key="2026-05", mode="natural",
        holiday_name_de=holiday_name_de)
    assert sorted(pedidos, key=str) == sorted([DNI_A, DNI_B, None], key=str)
    filas = {r.nombre: r for r in det.rows}
    celda = {r: {c.date_iso: c for c in f.cells} for r, f in filas.items()}
    assert celda["Persona A"][SAN_ISIDRO].is_holiday is True
    assert celda["Persona A"][SAN_ISIDRO].holiday_name == f"Fiesta {DNI_A}"
    assert celda["Persona B"][SAN_ISIDRO].is_holiday is False
    assert celda["Persona B"][SAN_ISIDRO].holiday_name is None
    assert celda["Persona C"][FIESTA_DEFECTO].is_holiday is True
    assert not hasattr(det.days[0], "is_holiday")
    assert not hasattr(det.days[0], "holiday_name")


def test_f032_r26_get_obra_sin_resolutor_no_marca_festivos(entorno) -> None:
    fabrica = FabricaSesionSqlite()
    _sembrar(fabrica)
    det = ParteReviewRepository(fabrica).get_obra(
        "obr-10", period_key="2026-05", mode="natural")
    assert not any(c.is_holiday for r in det.rows for c in r.cells)
