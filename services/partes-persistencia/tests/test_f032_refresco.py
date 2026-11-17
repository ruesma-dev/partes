# tests/test_f032_refresco.py
"""F-032 · R4–R8 y R3: `RefrescoFestivos`, el unico que pide festivos a Sesame.

Con cliente y repositorio falsos (sin red ni BBDD). Por (DNI, ano):
lista completa ⇒ upsert con `leido_en_utc` y `al_guardar()`; 404 ⇒
`sin_calendario`, sin escribir ni borrar; fallo o incompleto ⇒ con fila,
`conservadas`; sin fila, `sin_dato`. Nunca lanza y sus logs no llevan DNIs.
"""
from __future__ import annotations

import datetime as dt
import logging

import pytest

from application.services.festivos_guardados import FilaFestivos
from application.services.refresco_festivos import (
    RefrescoFestivos,
    ResultadoRefresco,
    anos_de_semana,
)
from infrastructure.sesame.sesame_api_client import FestivoDia

DNI = "12345678Z"
OTRO = "87654321X"
AHORA = dt.datetime(2026, 11, 17, 10, 30, 0, tzinfo=dt.timezone.utc)


class ClienteFake:
    """`festivos(dni, ano)` desde un dict; un valor Exception se lanza."""

    def __init__(self, respuestas):
        self.respuestas = respuestas
        self.llamadas: list[tuple[str, int]] = []

    def festivos(self, dni, ano):
        self.llamadas.append((dni, ano))
        valor = self.respuestas.get((dni, ano))
        if isinstance(valor, Exception):
            raise valor
        return valor

    def calendario_por_defecto(self, ano):  # pragma: no cover - no se llama
        raise AssertionError("el refresco no pide el calendario por defecto")


class RepoFake:
    def __init__(self, filas=None, *, fallo_lectura=None, fallo_guardar=None):
        self.filas = dict(filas or {})
        self.guardadas: list[FilaFestivos] = []
        self.fallo_lectura = fallo_lectura
        self.fallo_guardar = fallo_guardar
        self.lecturas = 0

    def leer_todas(self):
        self.lecturas += 1
        if self.fallo_lectura:
            raise self.fallo_lectura
        return dict(self.filas)

    def guardar(self, fila):
        if self.fallo_guardar:
            raise self.fallo_guardar
        self.guardadas.append(fila)
        self.filas[(fila.dni_norm, fila.ano)] = fila


def _lista(*fechas, ano=2026):
    return [FestivoDia(fecha=f, nombre=f"fiesta {f}") for f in fechas]


def _fila(dni=DNI, ano=2026):
    return FilaFestivos(dni_norm=dni, ano=ano, festivos={"2026-03-19": "x"},
                        leido_en_utc="2026-01-01T00:00:00Z")


def _refresco(cliente, repo, *, minimo=1, avisos=None):
    return RefrescoFestivos(
        cliente=cliente, repositorio=repo, minimo=minimo,
        ahora_utc=lambda: AHORA,
        al_guardar=(lambda: avisos.append(1)) if avisos is not None
        else (lambda: None))


# --------------------------------- R4 ----------------------------------- #

def test_f032_r4_pide_cada_dni_por_cada_ano_y_guarda_por_upsert():
    cliente = ClienteFake({
        (DNI, 2026): _lista("2026-01-01", "2026-03-19"),
        (DNI, 2027): _lista("2027-01-01", ano=2027),
        (OTRO, 2026): _lista("2026-01-01"),
        (OTRO, 2027): _lista("2027-01-06"),
    })
    repo = RepoFake()
    res = _refresco(cliente, repo).refrescar([DNI, OTRO, DNI], {2026, 2027})
    assert res == ResultadoRefresco(guardadas=4, conservadas=0,
                                    sin_calendario=0, sin_dato=0)
    assert sorted(cliente.llamadas) == [(DNI, 2026), (DNI, 2027),
                                        (OTRO, 2026), (OTRO, 2027)]
    fila = repo.filas[(DNI, 2026)]
    assert fila == FilaFestivos(
        dni_norm=DNI, ano=2026,
        festivos={"2026-01-01": "fiesta 2026-01-01",
                  "2026-03-19": "fiesta 2026-03-19"},
        leido_en_utc="2026-11-17T10:30:00Z")


def test_f032_r4_dnis_vacios_no_piden_nada():
    cliente = ClienteFake({})
    res = _refresco(cliente, RepoFake()).refrescar(["", None], {2026})
    assert cliente.llamadas == []
    assert res == ResultadoRefresco(0, 0, 0, 0)


def test_f032_r4_nunca_pide_el_calendario_por_defecto():
    """El doble revienta si se llama: un 404 tampoco lo pide (DA19 = B)."""
    cliente = ClienteFake({(DNI, 2026): None})
    res = _refresco(cliente, RepoFake()).refrescar([DNI], {2026})
    assert res.sin_calendario == 1


# --------------------------------- R5 ----------------------------------- #

def test_f032_r5_404_es_sin_calendario_y_no_escribe():
    repo = RepoFake()
    avisos: list = []
    res = _refresco(ClienteFake({(DNI, 2026): None}), repo,
                    avisos=avisos).refrescar([DNI], {2026})
    assert res == ResultadoRefresco(0, 0, 1, 0)
    assert repo.guardadas == [] and repo.filas == {}
    assert avisos == []


def test_f032_r5_404_con_fila_previa_no_la_toca():
    previa = _fila()
    repo = RepoFake({(DNI, 2026): previa})
    res = _refresco(ClienteFake({(DNI, 2026): None}), repo).refrescar(
        [DNI], {2026})
    assert res == ResultadoRefresco(0, 0, 1, 0)
    assert repo.filas == {(DNI, 2026): previa}
    assert repo.guardadas == []


# --------------------------------- R6 ----------------------------------- #

def test_f032_r6_incompleto_con_minimo_1_no_se_guarda_y_es_fallo():
    repo = RepoFake()
    res = _refresco(ClienteFake({(DNI, 2026): []}), repo).refrescar(
        [DNI], {2026})
    assert res == ResultadoRefresco(0, 0, 0, 1)
    assert repo.guardadas == []


def test_f032_r6_exactamente_el_minimo_pasa():
    repo = RepoFake()
    res = _refresco(ClienteFake({(DNI, 2026): _lista("2026-01-01",
                                                     "2026-01-06")}),
                    repo, minimo=2).refrescar([DNI], {2026})
    assert res.guardadas == 1 and res.sin_dato == 0


def test_f032_r6_uno_menos_que_el_minimo_falla():
    repo = RepoFake()
    res = _refresco(ClienteFake({(DNI, 2026): _lista("2026-01-01")}),
                    repo, minimo=2).refrescar([DNI], {2026})
    assert res == ResultadoRefresco(0, 0, 0, 1)


def test_f032_r6_los_dias_de_otro_ano_no_cuentan():
    repo = RepoFake()
    res = _refresco(ClienteFake({(DNI, 2026): _lista("2025-12-25",
                                                     "2027-01-01")}),
                    repo).refrescar([DNI], {2026})
    assert res == ResultadoRefresco(0, 0, 0, 1)


def test_f032_r6_minimo_0_no_controla():
    repo = RepoFake()
    res = _refresco(ClienteFake({(DNI, 2026): []}), repo,
                    minimo=0).refrescar([DNI], {2026})
    assert res == ResultadoRefresco(1, 0, 0, 0)
    assert repo.filas[(DNI, 2026)].festivos == {}


# ------------------------------- R7 y R8 -------------------------------- #

@pytest.mark.parametrize("fallo", [RuntimeError("sesame caido"),
                                   TimeoutError("plazo"), []],
                         ids=["excepcion", "plazo", "incompleto"])
def test_f032_r7_un_fallo_con_fila_la_conserva(fallo):
    previa = _fila()
    repo = RepoFake({(DNI, 2026): previa})
    res = _refresco(ClienteFake({(DNI, 2026): fallo}), repo).refrescar(
        [DNI], {2026})
    assert res == ResultadoRefresco(0, 1, 0, 0)
    assert repo.filas == {(DNI, 2026): previa} and repo.guardadas == []


@pytest.mark.parametrize("fallo", [RuntimeError("sesame caido"),
                                   TimeoutError("plazo"), []],
                         ids=["excepcion", "plazo", "incompleto"])
def test_f032_r8_un_fallo_sin_fila_es_sin_dato(fallo):
    repo = RepoFake({(OTRO, 2026): _fila(OTRO), (DNI, 2025): _fila(ano=2025)})
    res = _refresco(ClienteFake({(DNI, 2026): fallo}), repo).refrescar(
        [DNI], {2026})
    assert res == ResultadoRefresco(0, 0, 0, 1)


def test_f032_r8_mezcla_de_resultados():
    repo = RepoFake({(OTRO, 2026): _fila(OTRO)})
    cliente = ClienteFake({
        (DNI, 2026): _lista("2026-01-01"),
        (DNI, 2027): None,
        (OTRO, 2026): RuntimeError("x"),
        (OTRO, 2027): RuntimeError("x"),
    })
    res = _refresco(cliente, repo).refrescar([DNI, OTRO], [2026, 2027])
    assert res == ResultadoRefresco(guardadas=1, conservadas=1,
                                    sin_calendario=1, sin_dato=1)


def test_f032_r8_si_falla_leer_la_tabla_el_fallo_cuenta_como_sin_dato():
    repo = RepoFake(fallo_lectura=RuntimeError("bbdd"))
    res = _refresco(ClienteFake({(DNI, 2026): RuntimeError("x")}),
                    repo).refrescar([DNI], {2026})
    assert res == ResultadoRefresco(0, 0, 0, 1)


def test_f032_r8_si_falla_guardar_cuenta_como_fallo():
    previa = _fila()
    repo = RepoFake({(DNI, 2026): previa}, fallo_guardar=RuntimeError("bbdd"))
    avisos: list = []
    res = _refresco(ClienteFake({(DNI, 2026): _lista("2026-01-01")}), repo,
                    avisos=avisos).refrescar([DNI], {2026})
    assert res == ResultadoRefresco(0, 1, 0, 0)
    assert avisos == []


def test_f032_r7_solo_lee_la_tabla_si_hay_fallos():
    repo = RepoFake()
    _refresco(ClienteFake({(DNI, 2026): _lista("2026-01-01")}), repo
              ).refrescar([DNI], {2026})
    assert repo.lecturas == 0


# ------------------------------ al_guardar ------------------------------ #

def test_f032_r15_al_guardar_se_llama_por_cada_fila_guardada():
    avisos: list = []
    cliente = ClienteFake({(DNI, 2026): _lista("2026-01-01"),
                           (OTRO, 2026): None})
    _refresco(cliente, RepoFake(), avisos=avisos).refrescar([DNI, OTRO],
                                                             {2026})
    assert avisos == [1]


def test_f032_r9_un_al_guardar_que_falla_no_rompe_nada():
    def explota():
        raise RuntimeError("cache")
    repo = RepoFake()
    res = RefrescoFestivos(cliente=ClienteFake({(DNI, 2026): _lista(
        "2026-01-01")}), repositorio=repo, minimo=1, ahora_utc=lambda: AHORA,
        al_guardar=explota).refrescar([DNI], {2026})
    assert res.guardadas == 1


# ------------------------------ R9 y R3 --------------------------------- #

def test_f032_r9_nunca_lanza():
    class ClienteRaro:
        def festivos(self, dni, ano):
            raise ValueError("raro")

    res = _refresco(ClienteRaro(), RepoFake(fallo_lectura=OSError("x"),
                                            fallo_guardar=OSError("y"))
                    ).refrescar([DNI], {2026})
    assert res == ResultadoRefresco(0, 0, 0, 1)


def test_f032_r9_ahora_que_falla_no_lanza():
    def ahora():
        raise RuntimeError("reloj")
    repo = RepoFake()
    res = RefrescoFestivos(cliente=ClienteFake({(DNI, 2026): _lista(
        "2026-01-01")}), repositorio=repo, minimo=1, ahora_utc=ahora
    ).refrescar([DNI], {2026})
    assert res == ResultadoRefresco(0, 0, 0, 1)


def test_f032_r3_logs_sin_dnis_y_con_el_recuento(caplog):
    cliente = ClienteFake({
        (DNI, 2026): RuntimeError(f"sesame no conoce {DNI}"),
        (OTRO, 2026): _lista("2026-01-01"),
    })
    with caplog.at_level(logging.DEBUG):
        _refresco(cliente, RepoFake()).refrescar([DNI, OTRO], {2026})
    textos = [r.getMessage() for r in caplog.records]
    assert textos, "el refresco deja rastro"
    for t in textos:
        assert DNI not in t and OTRO not in t, t
    assert any("[festivos] refresco guardadas=1 conservadas=0 "
               "sin_calendario=0 sin_dato=1" in t for t in textos)


# ----------------------------- anos_de_semana --------------------------- #

@pytest.mark.parametrize("fecha,esperado", [
    (dt.date(2026, 3, 18), {2026}),
    ("2026-03-18", {2026}),
    (dt.date(2026, 12, 31), {2026, 2027}),     # jueves: domingo en 2027
    (dt.date(2027, 1, 1), {2026, 2027}),       # viernes: lunes en 2026
    (dt.date(2026, 12, 27), {2026}),           # domingo de la semana 52
    (dt.date(2026, 12, 28), {2026, 2027}),     # lunes de la semana 53
    ("2027-01-04T08:00:00", {2027}),
])
def test_f032_r4_anos_de_la_semana_iso(fecha, esperado):
    assert anos_de_semana(fecha) == esperado
