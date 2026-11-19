# tests/test_f077_cliente_hr.py
"""F-077 · R1–R9: `SesameHrClient`, el cliente de SOLO LECTURA de Sesame HR.

Todo el trafico va por `httpx.MockTransport` (`tests/fixtures_sesame.py`),
que revienta con cualquier metodo distinto de GET (R9). Las esperas de los
reintentos se inyectan (`dormir`): los tests no duermen. Datos ficticios.
"""
from __future__ import annotations

import dataclasses
import logging

import httpx
import pytest

from infrastructure.sesame.sesame_hr_client import (
    RUTA_CALENDARIOS,
    RUTA_EMPLEADOS,
    RUTA_FESTIVOS,
    CalendarioSesame,
    EmpleadoSesame,
    FestivoDia,
    SesameHrClient,
    SesameNoDisponible,
)
from tests.fixtures_sesame import (
    BASE_URL,
    CALENDARIOS,
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
    secuencia,
)


def _cliente(sesame: SesameHrFalso, dormir: Dormir | None = None,
             **kw) -> SesameHrClient:
    return SesameHrClient(base_url=BASE_URL, token=TOKEN,
                          transport=sesame.transport(),
                          dormir=dormir or Dormir(), **kw)


def _festivos(*respuestas, dormir=None, **kw):
    """Cliente cuyo `/holidays` de A responde la secuencia dada."""
    sesame = SesameHrFalso(festivos={ID_A: secuencia(*respuestas)})
    return sesame, _cliente(sesame, dormir, **kw)


# ---------------------------------- R1 ---------------------------------- #

def test_f077_r1_cabeceras_bearer_y_json_en_cada_peticion() -> None:
    sesame = SesameHrFalso()
    _cliente(sesame).empleados()
    assert len(sesame.peticiones) == 2
    for request in sesame.peticiones:
        assert request.method == "GET"
        assert request.headers["Authorization"] == f"Bearer {TOKEN}"
        assert request.headers["Accept"] == "application/json"
        assert str(request.url).startswith(f"{BASE_URL}{RUTA_EMPLEADOS}?")


def test_f077_r1_la_barra_final_de_la_url_no_duplica() -> None:
    sesame = SesameHrFalso()
    SesameHrClient(base_url=BASE_URL + "/", token=TOKEN,
                   transport=sesame.transport()).calendarios_festivos()
    assert str(sesame.peticiones[0].url).startswith(
        f"{BASE_URL}{RUTA_CALENDARIOS}?")


@pytest.mark.parametrize("base_url", [
    "http://sesame.ejemplo.test", "sesame.ejemplo.test", "", "ftp://x"])
def test_f077_r1_solo_https(base_url) -> None:
    with pytest.raises(ValueError):
        SesameHrClient(base_url=base_url, token=TOKEN)


@pytest.mark.parametrize("token", ["", "   ", None])
def test_f077_r1_token_en_blanco_no_construye(token) -> None:
    with pytest.raises(ValueError):
        SesameHrClient(base_url=BASE_URL, token=token)  # type: ignore[arg-type]


def test_f077_r1_log_de_instancia_sin_el_token(caplog) -> None:
    with caplog.at_level(logging.INFO):
        SesameHrClient(base_url=BASE_URL, token=TOKEN, timeout_s=7)
    mensajes = [m for m in caplog.messages if "[sesame-hr] Instanciado" in m]
    assert mensajes == [f"[sesame-hr] Instanciado base_url={BASE_URL} "
                        f"token_len={len(TOKEN)} timeout_s=7.0"]
    assert TOKEN not in caplog.text


def test_f077_r1_el_plazo_llega_a_httpx() -> None:
    vistos = []

    def anota(request):
        assert request.method == "GET"                 # solo lectura (R1)
        vistos.append(request.extensions["timeout"])
        return httpx.Response(200, json=pagina([]))

    SesameHrClient(base_url=BASE_URL, token=TOKEN, timeout_s=4,
                   transport=httpx.MockTransport(anota)).calendarios_festivos()
    assert vistos and vistos[0]["read"] == 4.0


# ---------------------------------- R2 ---------------------------------- #

def test_f077_r2_pagina_con_limit_y_page_hasta_last_page() -> None:
    sesame = SesameHrFalso(empleados=[EMPLEADOS_P1, EMPLEADOS_P2])
    _cliente(sesame).empleados()
    params = [dict(r.url.params) for r in sesame.peticiones]
    assert [(p["limit"], p["page"]) for p in params] == [("100", "1"),
                                                         ("100", "2")]


def test_f077_r2_el_tamano_de_pagina_es_configurable() -> None:
    sesame = SesameHrFalso(empleados=[pagina([], 1, 1)])
    _cliente(sesame, page_size=7).empleados()
    assert sesame.peticiones[0].url.params["limit"] == "7"


def test_f077_r2_sin_last_page_es_una_sola_pagina() -> None:
    sesame = SesameHrFalso(empleados=[pagina([empleado(ID_B, DNI_B)], 1,
                                             None), 500])
    assert [e.id for e in _cliente(sesame).empleados()] == [ID_B]
    assert len(sesame.peticiones) == 1


def test_f077_r2_un_data_objeto_cuenta_como_lista_de_uno() -> None:
    sesame = SesameHrFalso(empleados=[pagina(empleado(ID_B, DNI_B))])
    assert [e.id for e in _cliente(sesame).empleados()] == [ID_B]


def test_f077_r2_un_404_a_mitad_del_listado_es_fallo() -> None:
    sesame = SesameHrFalso(empleados=[EMPLEADOS_P1, 404])
    with pytest.raises(RuntimeError) as exc:
        _cliente(sesame).empleados()
    assert not isinstance(exc.value, SesameNoDisponible)
    assert str(exc.value) == f"sesame HTTP 404 en {RUTA_EMPLEADOS}"


def test_f077_r2_una_pagina_vacia_antes_de_la_ultima_es_fallo() -> None:
    sesame = SesameHrFalso(empleados=[EMPLEADOS_P1, pagina([], 2, 3)])
    with pytest.raises(RuntimeError) as exc:
        _cliente(sesame).empleados()
    assert "vacia" in str(exc.value)
    assert len(sesame.peticiones) == 2


def test_f077_r2_la_ultima_pagina_vacia_no_es_fallo() -> None:
    sesame = SesameHrFalso(empleados=[pagina([], 1, 1)])
    assert _cliente(sesame).empleados() == []


def test_f077_r2_superar_el_tope_de_filas_es_fallo() -> None:
    sesame = SesameHrFalso(empleados=[EMPLEADOS_P1, EMPLEADOS_P2])
    with pytest.raises(RuntimeError) as exc:
        _cliente(sesame, tope_filas=4).empleados()
    assert "tope" in str(exc.value)


def test_f077_r2_llegar_justo_al_tope_no_es_fallo() -> None:
    sesame = SesameHrFalso(empleados=[EMPLEADOS_P1, EMPLEADOS_P2])
    assert len(_cliente(sesame, tope_filas=5).empleados()) == 5


@pytest.mark.parametrize("cuerpo", [["no", "es", "objeto"],
                                    {"data": [], "meta": {"lastPage": "x"}}])
def test_f077_r2_un_cuerpo_sin_forma_de_listado_es_fallo(cuerpo) -> None:
    sesame = SesameHrFalso(calendarios=[cuerpo])
    with pytest.raises(RuntimeError) as exc:
        _cliente(sesame).calendarios_festivos()
    assert not isinstance(exc.value, SesameNoDisponible)


def test_f077_r2_cuenta_las_paginas_del_ultimo_listado() -> None:
    cliente = _cliente(SesameHrFalso())
    cliente.empleados()
    assert cliente.ultimas_paginas == 2


# ---------------------------------- R3 ---------------------------------- #

@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_f077_r3_reintenta_429_y_5xx(status) -> None:
    dormir = Dormir()
    sesame, cliente = _festivos(status, FESTIVOS_A_2026, dormir=dormir)
    assert [f.fecha for f in cliente.festivos_de_empleado(ID_A, 2026)] == [
        "2026-01-01", "2026-05-15"]
    assert len(sesame.peticiones) == 2
    assert dormir.esperas == [1.0]                  # 1 + intento 0


def test_f077_r3_respeta_retry_after_numerico() -> None:
    dormir = Dormir()
    _, cliente = _festivos(
        httpx.Response(429, headers={"Retry-After": "7"}),
        httpx.Response(429, headers={"Retry-After": "2.5"}),
        FESTIVOS_A_2026, dormir=dormir)
    cliente.festivos_de_empleado(ID_A, 2026)
    assert dormir.esperas == [7.0, 2.5]


def test_f077_r3_retry_after_con_tope_de_30_s() -> None:
    dormir = Dormir()
    _, cliente = _festivos(httpx.Response(503, headers={"Retry-After": "31"}),
                           FESTIVOS_A_2026, dormir=dormir)
    cliente.festivos_de_empleado(ID_A, 2026)
    assert dormir.esperas == [30.0]


@pytest.mark.parametrize("cabecera", [
    "Wed, 18 Nov 2026 10:00:00 GMT", "", "pronto"])
def test_f077_r3_retry_after_no_numerico_es_1_mas_intento(cabecera) -> None:
    dormir = Dormir()
    _, cliente = _festivos(
        httpx.Response(429, headers={"Retry-After": cabecera}),
        httpx.Response(429, headers={"Retry-After": cabecera}),
        FESTIVOS_A_2026, dormir=dormir)
    cliente.festivos_de_empleado(ID_A, 2026)
    assert dormir.esperas == [1.0, 2.0]


def test_f077_r3_agotados_los_reintentos_no_disponible() -> None:
    dormir = Dormir()
    sesame, cliente = _festivos(500, dormir=dormir)
    with pytest.raises(SesameNoDisponible) as exc:
        cliente.festivos_de_empleado(ID_A, 2026)
    assert len(sesame.peticiones) == 3              # 1 + max_reintentos (2)
    assert dormir.esperas == [1.0, 2.0]
    assert str(exc.value) == f"sesame HTTP 500 en {RUTA_FESTIVOS}"


def test_f077_r3_max_reintentos_configurable() -> None:
    sesame, cliente = _festivos(429, max_reintentos=0)
    with pytest.raises(SesameNoDisponible):
        cliente.festivos_de_empleado(ID_A, 2026)
    assert len(sesame.peticiones) == 1


@pytest.mark.parametrize("error", [httpx.ConnectError("sin ruta"),
                                   httpx.ReadTimeout("plazo")],
                         ids=["red", "plazo"])
def test_f077_r3_error_de_red_reintenta_y_agota(error) -> None:
    dormir = Dormir()
    sesame, cliente = _festivos(error, dormir=dormir)
    with pytest.raises(SesameNoDisponible) as exc:
        cliente.festivos_de_empleado(ID_A, 2026)
    assert dormir.esperas == [1.0, 2.0]             # 1 · (intento + 1)
    assert str(exc.value) == (f"sesame red en {RUTA_FESTIVOS}: "
                              f"{type(error).__name__}")


def test_f077_r3_error_de_red_y_luego_bien() -> None:
    dormir = Dormir()
    _, cliente = _festivos(httpx.ConnectError("x"), FESTIVOS_A_2026,
                           dormir=dormir)
    assert len(cliente.festivos_de_empleado(ID_A, 2026)) == 2
    assert dormir.esperas == [1.0]


def test_f077_r3_el_warning_de_reintento_da_ruta_estado_y_espera(
        caplog) -> None:
    _, cliente = _festivos(httpx.Response(429, headers={"Retry-After": "3"}),
                           FESTIVOS_A_2026)
    with caplog.at_level(logging.WARNING):
        cliente.festivos_de_empleado(ID_A, 2026)
    avisos = [r.getMessage() for r in caplog.records
              if r.levelno == logging.WARNING]
    assert avisos == [f"[sesame-hr] {RUTA_FESTIVOS} -> 429; reintento en "
                      "3.0 s"]


def test_f077_r3_por_defecto_duerme_con_time_sleep() -> None:
    import time
    cliente = SesameHrClient(base_url=BASE_URL, token=TOKEN)
    assert cliente._dormir is time.sleep            # noqa: SLF001


# ---------------------------------- R4 ---------------------------------- #

@pytest.mark.parametrize("status", [400, 401, 403, 409, 422])
def test_f077_r4_4xx_no_reintenta_y_no_disponible(status) -> None:
    dormir = Dormir()
    sesame, cliente = _festivos(status, dormir=dormir)
    with pytest.raises(SesameNoDisponible) as exc:
        cliente.festivos_de_empleado(ID_A, 2026)
    assert len(sesame.peticiones) == 1
    assert dormir.esperas == []
    assert str(exc.value) == f"sesame HTTP {status} en {RUTA_FESTIVOS}"


def test_f077_r4_cuerpo_no_json_es_runtime_error() -> None:
    _, cliente = _festivos(httpx.Response(200, text="<html>proxy</html>"))
    with pytest.raises(RuntimeError) as exc:
        cliente.festivos_de_empleado(ID_A, 2026)
    assert not isinstance(exc.value, SesameNoDisponible)
    assert "proxy" not in str(exc.value)


def test_f077_r4_no_disponible_es_runtime_error() -> None:
    assert issubclass(SesameNoDisponible, RuntimeError)


# ---------------------------------- R5 ---------------------------------- #

@pytest.mark.parametrize("respuesta", [
    httpx.Response(500, text=f"error con {ID_A} y {TOKEN}"),
    httpx.Response(401, json={"detail": f"token {TOKEN} invalido"}),
    httpx.Response(404, json={"detail": f"empleado {ID_A} no existe"}),
    httpx.Response(200, text=f"no json {ID_A}"),
    httpx.ConnectError(f"{BASE_URL}?employeeId={ID_A}"),
], ids=["500", "401", "404", "no-json", "red"])
def test_f077_r5_los_mensajes_no_llevan_cuerpo_query_url_ni_token(
        respuesta) -> None:
    sesame = SesameHrFalso(festivos={ID_A: lambda request: respuesta})
    with pytest.raises(RuntimeError) as exc:
        _cliente(sesame, max_reintentos=0).festivos_de_empleado(ID_A, 2026)
    texto = str(exc.value)
    for prohibido in (ID_A, TOKEN, BASE_URL, "sesame.ejemplo", "employeeId",
                      "year=", "?"):
        assert prohibido not in texto, (prohibido, texto)
    assert RUTA_FESTIVOS in texto
    # Sin encadenar el error de httpx (su texto lleva la URL con la query).
    assert exc.value.__cause__ is None
    assert exc.value.__context__ is None or exc.value.__suppress_context__


# ---------------------------------- R6 ---------------------------------- #

def test_f077_r6_empleados_activos_e_inactivos() -> None:
    sesame = SesameHrFalso()
    _cliente(sesame).empleados()
    assert sesame.peticiones[0].url.params["status[in]"] == "active,inactive"


def test_f077_r6_solo_id_dni_normalizado_y_activo() -> None:
    empleados = _cliente(SesameHrFalso()).empleados()
    assert [f.name for f in dataclasses.fields(EmpleadoSesame)] == [
        "id", "dni_norm", "activo"]
    assert [(e.id, e.dni_norm, e.activo) for e in empleados] == [
        (ID_A, "12345678Z", True), (ID_B, DNI_B, True),
        (ID_C_INACTIVO, DNI_C, False), (ID_C, DNI_C, True),
        ("emp-ficticio-sin-dni", "", True)]
    for e in empleados:
        assert isinstance(e, EmpleadoSesame)
        for personal in PERSONALES:
            assert personal not in repr(e)


def test_f077_r6_normaliza_con_la_regla_de_sv3() -> None:
    """DA5: `normalize_dni` de sv3, que tambien quita tildes."""
    sesame = SesameHrFalso(empleados=[pagina([empleado("e1", " x-1234567l ")])])
    assert _cliente(sesame).empleados()[0].dni_norm == "X1234567L"


def test_f077_r6_estado_desconocido_no_es_activo_y_sin_id_se_omite() -> None:
    raro = dict(empleado("e1", DNI_B), status="pending")
    sin_id = dict(empleado(None, DNI_B))   # type: ignore[arg-type]
    sesame = SesameHrFalso(empleados=[pagina([raro, sin_id, "basura"])])
    assert [(e.id, e.activo) for e in _cliente(sesame).empleados()] == [
        ("e1", False)]


def test_f077_r6_el_id_es_texto() -> None:
    sesame = SesameHrFalso(empleados=[pagina([empleado(123, DNI_B)])])  # type: ignore[arg-type]
    assert _cliente(sesame).empleados()[0].id == "123"


# ---------------------------------- R7 ---------------------------------- #

def test_f077_r7_festivos_por_empleado_y_ano() -> None:
    sesame = SesameHrFalso(festivos={ID_A: FESTIVOS_A_2026})
    lista = _cliente(sesame).festivos_de_empleado(ID_A, 2026)
    params = sesame.peticiones[0].url.params
    assert (params["employeeId"], params["year"]) == (ID_A, "2026")
    assert lista == [FestivoDia("2026-01-01", "Ano Nuevo"),
                     FestivoDia("2026-05-15", "Fiesta local ficticia")]


def test_f077_r7_dayoff_y_daysoff_y_sin_nombre() -> None:
    fila_lista = {"id": "h2", "daysOff": [
        {"date": "2026-08-15", "name": None},
        {"date": "2026-03-19", "name": "  "},
        {"date": "2025-12-31", "name": "otro ano"}, "basura"]}
    sesame = SesameHrFalso(festivos={ID_A: pagina([
        fila_festivo("2026-10-12", "Pilar"), fila_lista, "basura",
        {"id": "h3"}, {"id": "h4", "dayOff": "no-objeto"}])})
    lista = _cliente(sesame).festivos_de_empleado(ID_A, 2026)
    assert lista == [FestivoDia("2026-03-19", None),
                     FestivoDia("2026-08-15", None),
                     FestivoDia("2026-10-12", "Pilar")]


def test_f077_r7_paginado() -> None:
    sesame = SesameHrFalso(festivos={ID_A: [
        pagina([fila_festivo("2026-01-06", "Reyes")], 1, 2),
        pagina([fila_festivo("2026-01-01", "Ano Nuevo")], 2, 2)]})
    lista = _cliente(sesame).festivos_de_empleado(ID_A, 2026)
    assert [f.fecha for f in lista] == ["2026-01-01", "2026-01-06"]
    assert [r.url.params["page"] for r in sesame.peticiones] == ["1", "2"]


def test_f077_r7_un_404_es_fallo_y_no_no_encontrado() -> None:
    """DA6: el empleado esta en el indice; un 404 aqui no es «sin fila»."""
    sesame = SesameHrFalso(festivos={})
    with pytest.raises(RuntimeError) as exc:
        _cliente(sesame).festivos_de_empleado(ID_A, 2026)
    assert not isinstance(exc.value, SesameNoDisponible)


def test_f077_r7_lista_vacia_es_un_dato() -> None:
    sesame = SesameHrFalso(festivos={ID_B: pagina([])})
    assert _cliente(sesame).festivos_de_empleado(ID_B, 2026) == []


# ---------------------------------- R8 ---------------------------------- #

def test_f077_r8_calendarios_con_id_nombre_defecto_y_dias() -> None:
    sesame = SesameHrFalso(calendarios=[CALENDARIOS])
    cals = _cliente(sesame).calendarios_festivos()
    assert sesame.rutas() == [RUTA_CALENDARIOS]
    assert cals == [
        CalendarioSesame("cal-ficticio-1", "General", True, (
            FestivoDia("2026-01-06", "Reyes"),
            FestivoDia("2026-12-25", "Navidad"))),
        CalendarioSesame("cal-ficticio-2", "Otro", False, (
            FestivoDia("2026-05-15", "Local"),))]


def test_f077_r8_day_off_si_no_hay_days_off_y_sin_nombre() -> None:
    sesame = SesameHrFalso(calendarios=[pagina([
        {"id": 7, "dayOff": [{"date": "2026-01-01", "name": "A"}]},
        {"id": "c2", "name": "", "dayOff": {"date": "2026-02-02"}},
        {"id": "c3", "daysOff": None}, "basura"])])
    cals = _cliente(sesame).calendarios_festivos()
    assert [(c.id, c.nombre, c.por_defecto, c.festivos) for c in cals] == [
        ("7", None, False, (FestivoDia("2026-01-01", "A"),)),
        ("c2", None, False, (FestivoDia("2026-02-02", None),)),
        ("c3", None, False, ())]


# ---------------------------------- R9 ---------------------------------- #

def test_f077_r9_solo_tres_metodos_publicos() -> None:
    publicos = sorted(n for n in vars(SesameHrClient)
                      if not n.startswith("_"))
    assert publicos == ["calendarios_festivos", "empleados",
                        "festivos_de_empleado"]


def test_f077_r9_el_falso_rechaza_otros_metodos() -> None:
    sesame = SesameHrFalso()
    with pytest.raises(AssertionError):
        with httpx.Client(transport=sesame.transport()) as c:
            c.post(f"{BASE_URL}{RUTA_EMPLEADOS}")
