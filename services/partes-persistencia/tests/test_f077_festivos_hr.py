# tests/test_f077_festivos_hr.py
"""F-077 · R10–R14 y R19: `FestivosSesameHr`, festivos de Sesame HR por DNI.

Es el `cliente` que recibe `RefrescoFestivos` (`festivos(dni, ano)`, el
contrato de F-032, R10). Por dentro: un indice DNI normalizado -> empleado
en memoria, con TTL (R11), todo o nada (R13) y un corte de 60 s tras un
fallo de disponibilidad (R14). Cliente REAL sobre `httpx.MockTransport`
(solo GET) y reloj falso: ni red ni esperas. Datos ficticios.
"""
from __future__ import annotations

import ast
import logging
from pathlib import Path

import httpx
import pytest

from infrastructure.sesame import festivos_sesame_hr as modulo
from infrastructure.sesame.festivos_sesame_hr import FestivosSesameHr
from infrastructure.sesame.sesame_hr_client import (
    RUTA_EMPLEADOS,
    RUTA_FESTIVOS,
    FestivoDia,
    SesameHrClient,
    SesameNoDisponible,
)
from tests.fixtures_sesame import (
    BASE_URL,
    DNI_A,
    DNI_AUSENTE,
    DNI_B,
    DNI_C,
    EMPLEADOS_P1,
    EMPLEADOS_P2,
    FESTIVOS_A_2026,
    ID_A,
    ID_B,
    ID_C,
    ID_C_INACTIVO,
    PERSONALES,
    TOKEN,
    Dormir,
    SesameHrFalso,
    empleado,
    fila_festivo,
    pagina,
)


class Reloj:
    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


def _adaptador(sesame: SesameHrFalso, reloj: Reloj | None = None,
               **kw) -> FestivosSesameHr:
    cliente = SesameHrClient(base_url=BASE_URL, token=TOKEN,
                             transport=sesame.transport(), dormir=Dormir())
    return FestivosSesameHr(cliente=cliente, reloj=reloj or Reloj(), **kw)


def _festivos_de(**por_id):
    return {k: pagina([fila_festivo(f, "F") for f in v])
            for k, v in por_id.items()}


# --------------------------------- R10 ---------------------------------- #

def test_f077_r10_dni_conocido_da_sus_festivos() -> None:
    sesame = SesameHrFalso(festivos={ID_A: FESTIVOS_A_2026})
    lista = _adaptador(sesame).festivos("12.345.678-z", 2026)
    assert lista == [FestivoDia("2026-01-01", "Ano Nuevo"),
                     FestivoDia("2026-05-15", "Fiesta local ficticia")]
    festivos = [r for r in sesame.peticiones if r.url.path == RUTA_FESTIVOS]
    assert [(r.url.params["employeeId"], r.url.params["year"])
            for r in festivos] == [(ID_A, "2026")]


@pytest.mark.parametrize("dni", [None, "", "  ", "-.-"])
def test_f077_r10_sin_dni_none_sin_red(dni) -> None:
    sesame = SesameHrFalso()
    assert _adaptador(sesame).festivos(dni, 2026) is None
    assert sesame.peticiones == []


def test_f077_r10_dni_ausente_del_indice_es_none() -> None:
    """DA6: no encontrado = sin fila y sin revision (como el 404 de F-032)."""
    sesame = SesameHrFalso()
    assert _adaptador(sesame).festivos(DNI_AUSENTE, 2026) is None
    assert RUTA_FESTIVOS not in sesame.rutas()


def test_f077_r10_lista_vacia_es_un_dato() -> None:
    sesame = SesameHrFalso(festivos={ID_B: pagina([])})
    assert _adaptador(sesame).festivos(DNI_B, 2026) == []


# --------------------------------- R11 ---------------------------------- #

def test_f077_r11_un_indice_para_todas_las_llamadas_del_ttl() -> None:
    reloj = Reloj()
    sesame = SesameHrFalso(festivos=_festivos_de(**{ID_A: ["2026-01-01"],
                                                    ID_B: ["2026-01-06"]}))
    adaptador = _adaptador(sesame, reloj)
    adaptador.festivos(DNI_A, 2026)
    reloj.t += 599
    adaptador.festivos(DNI_B, 2026)
    adaptador.festivos(DNI_AUSENTE, 2026)
    assert sesame.rutas().count(RUTA_EMPLEADOS) == 2        # dos paginas


def test_f077_r11_caducado_el_ttl_se_reconstruye() -> None:
    reloj = Reloj()
    sesame = SesameHrFalso(
        empleados=[EMPLEADOS_P1, EMPLEADOS_P2,
                   pagina([empleado("emp-nuevo", DNI_AUSENTE)])],
        festivos=_festivos_de(**{"emp-nuevo": ["2026-03-19"]}))
    adaptador = _adaptador(sesame, reloj)
    assert adaptador.festivos(DNI_AUSENTE, 2026) is None
    reloj.t += 600
    assert adaptador.festivos(DNI_AUSENTE, 2026) == [
        FestivoDia("2026-03-19", "F")]
    assert sesame.rutas().count(RUTA_EMPLEADOS) == 3


def test_f077_r11_ttl_configurable() -> None:
    reloj = Reloj()
    sesame = SesameHrFalso(empleados=[pagina([empleado(ID_B, DNI_B)])])
    adaptador = _adaptador(sesame, reloj, ttl_indice_s=5)
    adaptador.festivos(DNI_AUSENTE, 2026)
    reloj.t += 5
    adaptador.festivos(DNI_AUSENTE, 2026)
    assert sesame.rutas().count(RUTA_EMPLEADOS) == 2


def test_f077_r11_el_indice_guarda_solo_id_y_activo() -> None:
    adaptador = _adaptador(SesameHrFalso())
    adaptador.festivos(DNI_AUSENTE, 2026)
    indice = adaptador._indice[1]                           # noqa: SLF001
    assert set(indice) == {DNI_A, DNI_B, DNI_C}
    for dni, entrada in indice.items():
        assert (entrada.dni_norm == dni and isinstance(entrada.id, str)
                and isinstance(entrada.activo, bool))
        for personal in PERSONALES:
            assert personal not in repr(entrada)


# --------------------------------- R12 ---------------------------------- #

def test_f077_r12_duplicado_gana_el_activo() -> None:
    sesame = SesameHrFalso(festivos=_festivos_de(**{
        ID_C: ["2026-02-02"], ID_C_INACTIVO: ["2026-09-09"]}))
    assert _adaptador(sesame).festivos(DNI_C, 2026) == [
        FestivoDia("2026-02-02", "F")]


@pytest.mark.parametrize("activos, gana", [
    ((True, True), "primero"), ((False, False), "primero"),
    ((True, False), "primero"), ((False, True), "segundo")])
def test_f077_r12_a_igualdad_el_primero(activos, gana) -> None:
    sesame = SesameHrFalso(
        empleados=[pagina([empleado("primero", DNI_B, activo=activos[0]),
                           empleado("segundo", DNI_B, activo=activos[1])])],
        festivos=_festivos_de(primero=["2026-01-01"], segundo=["2026-01-02"]))
    lista = _adaptador(sesame).festivos(DNI_B, 2026)
    assert lista[0].fecha == ("2026-01-01" if gana == "primero"
                              else "2026-01-02")


def test_f077_r12_el_log_da_solo_recuentos(caplog) -> None:
    with caplog.at_level(logging.INFO):
        _adaptador(SesameHrFalso()).festivos(DNI_AUSENTE, 2026)
    lineas = [m for m in caplog.messages if "[sesame-hr] indice" in m]
    assert lineas == ["[sesame-hr] indice empleados=5 duplicados=1 "
                      "sin_dni=1 paginas=2"]
    for dni in (DNI_A, DNI_B, DNI_C, ID_A, ID_B, ID_C):
        assert dni not in caplog.text


# ------------------------------ R13 y R14 ------------------------------- #

@pytest.mark.parametrize("pagina2", [
    404, 500, 401, httpx.ConnectError("x"), pagina([], 2, 3),
    httpx.Response(200, text="no json")],
    ids=["404", "500", "401", "red", "vacia", "no-json"])
def test_f077_r13_indice_a_medias_es_fallo_y_no_se_guarda(pagina2) -> None:
    reloj = Reloj()
    sesame = SesameHrFalso(empleados=[EMPLEADOS_P1, pagina2])
    adaptador = _adaptador(sesame, reloj)
    with pytest.raises(SesameNoDisponible):
        adaptador.festivos(DNI_A, 2026)
    assert adaptador._indice is None                        # noqa: SLF001
    assert RUTA_FESTIVOS not in sesame.rutas()


def test_f077_r13_cero_empleados_es_fallo() -> None:
    sesame = SesameHrFalso(empleados=[pagina([])])
    adaptador = _adaptador(sesame)
    with pytest.raises(SesameNoDisponible):
        adaptador.festivos(DNI_A, 2026)
    assert adaptador._indice is None                        # noqa: SLF001


def test_f077_r13_solo_filas_sin_dni_cuentan_como_empleados() -> None:
    """Hay empleados, aunque ninguno con DNI: el indice vale (y vacio)."""
    sesame = SesameHrFalso(empleados=[pagina([empleado("e", None)])])
    assert _adaptador(sesame).festivos(DNI_A, 2026) is None


def test_f077_r14_tras_fallar_el_indice_60_s_sin_red() -> None:
    reloj = Reloj()
    # 500 en los tres intentos de la primera pagina; luego, bien.
    sesame = SesameHrFalso(
        empleados=[500, 500, 500, EMPLEADOS_P1, EMPLEADOS_P2],
        festivos={ID_A: FESTIVOS_A_2026})
    adaptador = _adaptador(sesame, reloj)
    with pytest.raises(SesameNoDisponible):
        adaptador.festivos(DNI_A, 2026)
    n = len(sesame.peticiones)
    reloj.t += 59.9
    for dni in (DNI_A, DNI_B, DNI_AUSENTE):
        with pytest.raises(SesameNoDisponible) as exc:
            adaptador.festivos(dni, 2026)
        assert str(exc.value) == "corte"
    assert len(sesame.peticiones) == n
    # Sin DNI no hay nada que pedir ni siquiera en corte.
    assert adaptador.festivos(None, 2026) is None
    reloj.t += 0.1                                          # 60 s justos
    assert len(adaptador.festivos(DNI_A, 2026)) == 2       # reintenta


def test_f077_r14_corte_configurable() -> None:
    reloj = Reloj()
    sesame = SesameHrFalso(empleados=[pagina([])])
    adaptador = _adaptador(sesame, reloj, corte_s=5)
    with pytest.raises(SesameNoDisponible):
        adaptador.festivos(DNI_A, 2026)
    reloj.t += 5
    with pytest.raises(SesameNoDisponible) as exc:
        adaptador.festivos(DNI_A, 2026)
    assert str(exc.value) != "corte"                        # volvio a pedir


def test_f077_r14_no_disponible_en_festivos_abre_el_corte() -> None:
    reloj = Reloj()
    sesame = SesameHrFalso(festivos={ID_A: 503, ID_B: FESTIVOS_A_2026})
    adaptador = _adaptador(sesame, reloj)
    with pytest.raises(SesameNoDisponible):
        adaptador.festivos(DNI_A, 2026)
    n = len(sesame.peticiones)
    with pytest.raises(SesameNoDisponible):
        adaptador.festivos(DNI_B, 2026)
    assert len(sesame.peticiones) == n


@pytest.mark.parametrize("respuesta", [404, httpx.Response(200, text="x")],
                         ids=["404", "no-json"])
def test_f077_r14_404_o_cuerpo_ilegible_no_abren_el_corte(respuesta) -> None:
    sesame = SesameHrFalso(festivos={ID_A: respuesta, ID_B: FESTIVOS_A_2026})
    adaptador = _adaptador(sesame)
    with pytest.raises(RuntimeError) as exc:
        adaptador.festivos(DNI_A, 2026)
    assert not isinstance(exc.value, SesameNoDisponible)
    assert len(adaptador.festivos(DNI_B, 2026)) == 2


def test_f077_r14_el_reloj_por_defecto_es_monotonic() -> None:
    import time
    cliente = SesameHrClient(base_url=BASE_URL, token=TOKEN)
    adaptador = FestivosSesameHr(cliente=cliente)
    assert adaptador._reloj is time.monotonic               # noqa: SLF001
    assert (adaptador._ttl_s, adaptador._corte_s) == (600, 60)  # noqa: SLF001


# --------------------------------- R19 ---------------------------------- #

def test_f077_r19_el_modulo_no_importa_nada_que_escriba_a_disco() -> None:
    arbol = ast.parse(Path(modulo.__file__).read_text(encoding="utf-8"))
    importados = set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            importados |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            importados.add((n.module or "").split(".")[0])
    assert not importados & {"sqlalchemy", "pickle", "shelve", "sqlite3",
                             "json", "pathlib", "os", "io", "tempfile",
                             "csv", "dbm"}
    nombres = {n.id for n in ast.walk(arbol) if isinstance(n, ast.Name)}
    assert "open" not in nombres
