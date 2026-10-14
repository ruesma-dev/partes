# tests/test_f046_candado.py
"""F-046 · R18: la pasada de `conciliar_todos` bajo un candado consultivo
de PostgreSQL (`pg_try_advisory_lock`, sesion propia, espera acotada).

Sin BBDD: el motor y la conexion son dobles que contestan lo que se les
pide y apuntan cada sentencia. El reloj y la espera tambien son dobles.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from infrastructure.database import sqlalchemy_parte_repository as modulo
from infrastructure.database.sqlalchemy_parte_repository import (
    CLAVE_CANDADO_CONCILIAR,
    SqlAlchemyParteRepository,
)


class ConexionFalsa:
    def __init__(self, respuestas, *, fallo_unlock=False):
        self.respuestas = list(respuestas)
        self.sentencias: list[tuple[str, dict]] = []
        self.opciones: dict = {}
        self.cerrada = False
        self.invalidada = False
        self.fallo_unlock = fallo_unlock

    def execution_options(self, **kw):
        self.opciones.update(kw)
        return self

    def execute(self, sentencia, params=None):
        sql = str(sentencia)
        self.sentencias.append((sql, dict(params or {})))
        if "pg_advisory_unlock" in sql:
            if self.fallo_unlock:
                raise RuntimeError("conexion perdida")
            return SimpleNamespace(scalar=lambda: True)
        valor = self.respuestas.pop(0)
        return SimpleNamespace(scalar=lambda: valor)

    def invalidate(self):
        self.invalidada = True

    def close(self):
        self.cerrada = True


class MotorFalso:
    def __init__(self, conexion, dialecto="postgresql"):
        self.dialect = SimpleNamespace(name=dialecto)
        self.conexion = conexion
        self.conexiones = 0

    def connect(self):
        self.conexiones += 1
        return self.conexion


class Reloj:
    def __init__(self):
        self.t = 0.0
        self.esperas: list[float] = []

    def ahora(self):
        return self.t

    def dormir(self, s):
        self.esperas.append(s)
        self.t += s


def _repo(monkeypatch, conexion, *, espera=300.0, dialecto="postgresql"):
    motor = MotorFalso(conexion, dialecto)
    reloj = Reloj()
    monkeypatch.setattr(modulo, "_reloj", reloj.ahora)
    monkeypatch.setattr(modulo, "_dormir", reloj.dormir)
    repo = SqlAlchemyParteRepository(SimpleNamespace(engine=motor),
                                     candado_espera_s=espera)
    return repo, motor, reloj


def test_f046_r18_toma_y_suelta_el_candado(monkeypatch):
    con = ConexionFalsa([True])
    repo, motor, _ = _repo(monkeypatch, con)
    dentro = []
    with repo.candado_pasada():
        dentro.append(len(con.sentencias))
    assert dentro == [1]
    (toma, _), (suelta, params) = con.sentencias
    assert "pg_try_advisory_lock(:k)" in toma
    assert "pg_advisory_unlock(:k)" in suelta
    assert params == {"k": CLAVE_CANDADO_CONCILIAR}
    assert con.opciones == {"isolation_level": "AUTOCOMMIT"}
    assert con.cerrada and not con.invalidada and motor.conexiones == 1


def test_f046_r18_espera_con_backoff_hasta_obtenerlo(monkeypatch):
    con = ConexionFalsa([False, False, False, True])
    repo, _, reloj = _repo(monkeypatch, con)
    with repo.candado_pasada():
        pass
    assert reloj.esperas == [0.5, 1.0, 2.0]


def test_f046_r18_sin_candado_a_tiempo_lanza_y_no_entra(monkeypatch):
    con = ConexionFalsa([False] * 100)
    repo, _, reloj = _repo(monkeypatch, con, espera=10.0)
    entro = []
    with pytest.raises(TimeoutError, match="candado"):
        with repo.candado_pasada():
            entro.append(True)
    assert entro == []
    assert sum(reloj.esperas) == pytest.approx(10.0)
    assert all(e <= 8.0 for e in reloj.esperas)
    assert not any("unlock" in s for s, _ in con.sentencias)
    assert con.cerrada


def test_f046_r18_suelta_aunque_la_pasada_falle(monkeypatch):
    con = ConexionFalsa([True])
    repo, _, _ = _repo(monkeypatch, con)
    with pytest.raises(ValueError):
        with repo.candado_pasada():
            raise ValueError("fallo de la pasada")
    assert any("pg_advisory_unlock" in s for s, _ in con.sentencias)
    assert con.cerrada


def test_f046_r18_si_no_puede_soltarlo_invalida_la_conexion(monkeypatch):
    """Una conexion devuelta al pool con el candado tomado lo retendria:
    se invalida para que PostgreSQL cierre la sesion y lo libere."""
    con = ConexionFalsa([True], fallo_unlock=True)
    repo, _, _ = _repo(monkeypatch, con)
    with repo.candado_pasada():
        pass
    assert con.invalidada and con.cerrada


def test_f046_r18_fuera_de_postgresql_no_hay_candado(monkeypatch):
    con = ConexionFalsa([])
    repo, motor, _ = _repo(monkeypatch, con, dialecto="sqlite")
    with repo.candado_pasada():
        pass
    assert motor.conexiones == 0 and con.sentencias == []


def test_f046_r18_espera_por_defecto_300_s():
    repo = SqlAlchemyParteRepository(SimpleNamespace(engine=None))
    assert repo.candado_espera_s == 300.0


def test_f046_r18_clave_constante_y_positiva():
    assert isinstance(CLAVE_CANDADO_CONCILIAR, int)
    assert 0 < CLAVE_CANDADO_CONCILIAR < 2 ** 63
