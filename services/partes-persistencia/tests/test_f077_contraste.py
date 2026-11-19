# tests/test_f077_contraste.py
"""F-077 · R24–R26: `contrastar_festivos_sesame.py` contra Sesame HR.

  - R24: lista UNA vez los calendarios (`/schedule/v1/holiday-calendar`) y
    los contrasta con las puras de F-032, que no cambian.
  - R25: URL de `--base-url` o `SESAME_BASE_URL`, solo `https://`; token
    solo de `SESAME_TOKEN` (entorno o `.env` de sv3) o pedido por consola
    sin eco; no hay `--token` ni `--api-key`. Sin URL o con el token vacio,
    sale distinto de 0 sin escribir ni llamar.
  - R26: con `--impacto`, los festivos de cada DNI salen del adaptador
    `FestivosSesameHr` (no encontrado ⇒ respaldo; fallo ⇒ fila de error);
    ningun informe lleva nombres ni emails y el Markdown no lleva DNIs.
    Solo `GET`.

Sin red (`httpx.MockTransport`) ni base (repositorio falso). Ficticios.
"""
from __future__ import annotations

import functools
from types import SimpleNamespace

import httpx
import pytest

import contrastar_festivos_sesame as cfs
from infrastructure.sesame.festivos_sesame_hr import FestivosSesameHr
from infrastructure.sesame.sesame_hr_client import (
    RUTA_CALENDARIOS,
    RUTA_EMPLEADOS,
    RUTA_FESTIVOS,
    CalendarioSesame,
    FestivoDia,
    SesameHrClient,
)
from tests.test_f032_contraste import (  # noqa: F401 (fixtures)
    AHORA,
    CLAVE,
    DNI,
    FESTIVOS_DNI,
    MADRID,
    OTRO,
    ROTO,
    URL,
    RepoSoloLectura,
    Sesame,
    _reg,
    _sin_env,
    _sin_prompt,
    ruta_calendario,
)


def _args(tmp_path, ruta_calendario, *extra, url=URL):
    base = ["--ano", "2026", "--calendario", ruta_calendario,
            "--salida", str(tmp_path)]
    return base + (["--base-url", url] if url else []) + list(extra)


def _main(argv, sesame, *, pedir_token=lambda prompt: CLAVE,
          repositorio=None):
    return cfs.main(argv, ahora=AHORA, transport=sesame.transport(),
                    repositorio=repositorio, pedir_token=pedir_token)


def _informes(tmp_path) -> str:
    return "".join(p.read_text(encoding="utf-8-sig")
                   for p in sorted(tmp_path.glob("contraste_*")))


# --------------------------------- R24 ---------------------------------- #

def test_f077_r24_listar_calendarios_a_la_forma_de_f032() -> None:
    class Cliente:
        def calendarios_festivos(self):
            return [CalendarioSesame("c1", "General", True, (
                FestivoDia("2026-01-01", "Ano Nuevo"),
                FestivoDia("2026-01-06", None))),
                CalendarioSesame("c2", None, False, ())]

    assert cfs.listar_calendarios(Cliente()) == [
        {"id": "c1", "nombre": "General", "por_defecto": True,
         "festivos": [{"fecha": "2026-01-01", "nombre": "Ano Nuevo"},
                      {"fecha": "2026-01-06", "nombre": None}]},
        {"id": "c2", "nombre": None, "por_defecto": False, "festivos": []}]


def test_f077_r24_lista_una_vez_y_contrasta(tmp_path, monkeypatch,
                                            ruta_calendario, capsys) -> None:
    _sin_env(monkeypatch)
    sesame = Sesame()
    assert _main(_args(tmp_path, ruta_calendario), sesame) == 0
    assert [p[:2] for p in sesame.peticiones] == [("GET", RUTA_CALENDARIOS)]
    salida = capsys.readouterr().out
    assert "Madrid: 10 festivos" in salida
    assert "Corto: 6 festivos · FALTAN DEL RESPALDO" in salida


def test_f077_r24_listado_no_disponible_sale_3_sin_informe(
        tmp_path, monkeypatch, ruta_calendario) -> None:
    """503 agotado (SesameNoDisponible): esperas anuladas, sin dormir."""
    _sin_env(monkeypatch)
    monkeypatch.setattr(cfs, "SesameHrClient", functools.partial(
        SesameHrClient, dormir=lambda s: None))
    sesame = Sesame(listado_status=503)
    assert _main(_args(tmp_path, ruta_calendario), sesame) == 3
    assert len(sesame.peticiones) == 3
    assert list(tmp_path.glob("contraste_*")) == []


# --------------------------------- R25 ---------------------------------- #

@pytest.mark.parametrize("opcion", ["--api-key", "--token"])
def test_f077_r25_no_hay_opcion_de_token(opcion) -> None:
    with pytest.raises(SystemExit):
        cfs._argumentos(["--ano", "2026", opcion, CLAVE])


def test_f077_r25_url_del_entorno_si_no_hay_linea(
        tmp_path, monkeypatch, ruta_calendario) -> None:
    _sin_env(monkeypatch)
    monkeypatch.setenv("SESAME_BASE_URL", "https://del-entorno.test")
    vistas = []

    def anota(request):
        vistas.append(request.url.host)
        return Sesame()(request)

    assert cfs.main(_args(tmp_path, ruta_calendario, url=None), ahora=AHORA,
                    transport=httpx.MockTransport(anota),
                    pedir_token=lambda p: CLAVE) == 0
    assert vistas == ["del-entorno.test"]


@pytest.mark.parametrize("url", ["http://sesame.ejemplo.test",
                                 "sesame.ejemplo.test"])
def test_f077_r25_url_sin_https_sale_2_sin_llamar(
        tmp_path, monkeypatch, ruta_calendario, capsys, url) -> None:
    _sin_env(monkeypatch)
    sesame = Sesame()
    assert _main(_args(tmp_path, ruta_calendario, url=url), sesame,
                 pedir_token=_sin_prompt) == 2
    assert sesame.peticiones == []
    assert list(tmp_path.glob("contraste_*")) == []
    assert "https://" in capsys.readouterr().err


def test_f077_r25_sin_url_sale_2_sin_pedir_el_token(
        tmp_path, monkeypatch, ruta_calendario) -> None:
    _sin_env(monkeypatch)
    sesame = Sesame()
    assert _main(_args(tmp_path, ruta_calendario, url=None), sesame,
                 pedir_token=_sin_prompt) == 2
    assert sesame.peticiones == []


def test_f077_r25_token_del_entorno_sin_preguntar(
        tmp_path, monkeypatch, ruta_calendario) -> None:
    _sin_env(monkeypatch)
    monkeypatch.setenv("SESAME_TOKEN", "token-del-entorno")
    sesame = Sesame()
    assert _main(_args(tmp_path, ruta_calendario), sesame,
                 pedir_token=_sin_prompt) == 0
    assert sesame.peticiones[0][2]["authorization"] == \
        "Bearer token-del-entorno"


def test_f077_r25_los_settings_mandan_sobre_el_entorno(
        tmp_path, monkeypatch, ruta_calendario) -> None:
    _sin_env(monkeypatch)
    monkeypatch.setenv("SESAME_TOKEN", "token-del-entorno")
    monkeypatch.setenv("SESAME_BASE_URL", "https://del-entorno.test")
    monkeypatch.setattr(cfs, "_settings", lambda: SimpleNamespace(
        sesame_base_url="https://de-settings.test",
        sesame_token="token-de-settings", sesame_timeout_s=3.0,
        sesame_festivos_minimos=1, calendario_laboral_path=ruta_calendario))
    vistas = []

    def anota(request):
        vistas.append((request.url.host, request.headers["authorization"]))
        return Sesame()(request)

    assert cfs.main(_args(tmp_path, ruta_calendario, url=None), ahora=AHORA,
                    transport=httpx.MockTransport(anota),
                    pedir_token=_sin_prompt) == 0
    assert vistas == [("de-settings.test", "Bearer token-de-settings")]


def test_f077_r25_sin_token_lo_pide_por_consola(
        tmp_path, monkeypatch, ruta_calendario) -> None:
    _sin_env(monkeypatch)
    preguntas = []

    def pedir(prompt):
        preguntas.append(prompt)
        return "  token-tecleado  "

    sesame = Sesame()
    assert _main(_args(tmp_path, ruta_calendario), sesame,
                 pedir_token=pedir) == 0
    assert preguntas == ["Token de Sesame HR: "]
    assert sesame.peticiones[0][2]["authorization"] == "Bearer token-tecleado"


def test_f077_r25_por_defecto_pide_con_getpass() -> None:
    import getpass
    import inspect
    assert inspect.signature(cfs.main).parameters[
        "pedir_token"].default is getpass.getpass


@pytest.mark.parametrize("tecleado", ["", "   "])
def test_f077_r25_token_vacio_sale_2_sin_escribir(
        tmp_path, monkeypatch, ruta_calendario, tecleado) -> None:
    _sin_env(monkeypatch)
    sesame = Sesame()
    assert _main(_args(tmp_path, ruta_calendario), sesame,
                 pedir_token=lambda p: tecleado) == 2
    assert sesame.peticiones == []
    assert list(tmp_path.glob("contraste_*")) == []


def test_f077_r25_el_token_no_sale_por_ningun_lado(
        tmp_path, monkeypatch, ruta_calendario, capsys) -> None:
    _sin_env(monkeypatch)
    assert _main(_args(tmp_path, ruta_calendario), Sesame()) == 0
    salida = capsys.readouterr()
    assert CLAVE not in salida.out + salida.err
    assert CLAVE not in _informes(tmp_path)


# --------------------------------- R26 ---------------------------------- #

def test_f077_r26_impacto_con_el_adaptador(tmp_path, monkeypatch,
                                           ruta_calendario) -> None:
    _sin_env(monkeypatch)
    repo = RepoSoloLectura([_reg(1, "2026-05-15"),
                            _reg(2, "2026-05-15", dni=OTRO),
                            _reg(3, "2026-05-15", dni=ROTO)])
    sesame = Sesame(festivos={DNI: list(FESTIVOS_DNI), ROTO: 404})
    assert _main(_args(tmp_path, ruta_calendario, "--impacto"), sesame,
                 repositorio=repo) == 0
    rutas = [p[1] for p in sesame.peticiones]
    assert rutas.count(RUTA_EMPLEADOS) == 1
    assert rutas.count(RUTA_FESTIVOS) == 2
    assert {p[0] for p in sesame.peticiones} == {"GET"}
    csv_ = next(tmp_path.glob("*.csv")).read_text(encoding="utf-8-sig")
    lineas = [l for l in csv_.splitlines() if l.startswith("linea;")]
    errores = [l for l in csv_.splitlines() if l.startswith("error;")]
    assert len(lineas) == 1 and f";{DNI};" in lineas[0]      # el de DNI
    assert len(errores) == 1 and f";{ROTO};" in errores[0]   # el 404
    assert OTRO not in csv_                                  # respaldo


def test_f077_r26_festivos_por_dni_usa_el_adaptador() -> None:
    class Adaptador:
        def __init__(self):
            self.llamadas = []

        def festivos(self, dni, ano):
            self.llamadas.append((dni, ano))
            if dni == ROTO:
                raise RuntimeError("sesame HTTP 404 en /x")
            if dni == OTRO:
                return None
            return [FestivoDia("2026-05-15", "F")]

    adaptador = Adaptador()
    out = cfs._festivos_por_dni(adaptador, [DNI, OTRO, ROTO, DNI], 2026)
    assert adaptador.llamadas == [(ROTO, 2026), (DNI, 2026), (OTRO, 2026)]
    assert out[DNI] == {"2026-05-15": "F"}
    assert out[OTRO] is None
    assert isinstance(out[ROTO], RuntimeError)


def test_f077_r26_main_cablea_festivos_sesame_hr(
        tmp_path, monkeypatch, ruta_calendario) -> None:
    _sin_env(monkeypatch)
    vistos = []
    original = cfs._festivos_por_dni

    def espia(adaptador, dnis, ano):
        vistos.append(adaptador)
        return original(adaptador, dnis, ano)

    monkeypatch.setattr(cfs, "_festivos_por_dni", espia)
    assert _main(_args(tmp_path, ruta_calendario, "--impacto"),
                 Sesame(festivos={DNI: list(FESTIVOS_DNI)}),
                 repositorio=RepoSoloLectura([_reg(1, "2026-05-15")])) == 0
    assert len(vistos) == 1 and isinstance(vistos[0], FestivosSesameHr)


def test_f077_r26_ningun_informe_lleva_nombres_ni_emails(
        tmp_path, monkeypatch, ruta_calendario, capsys) -> None:
    _sin_env(monkeypatch)
    repo = RepoSoloLectura([_reg(1, "2026-05-15")])
    assert _main(_args(tmp_path, ruta_calendario, "--impacto"),
                 Sesame(festivos={DNI: list(FESTIVOS_DNI)}),
                 repositorio=repo) == 0
    texto = _informes(tmp_path) + capsys.readouterr().out
    for personal in ("Nombreficticio", "@ejemplo.test", "emp-0"):
        assert personal not in texto
    md = next(tmp_path.glob("*.md")).read_text(encoding="utf-8-sig")
    assert DNI not in md
    assert MADRID["nombre"] in md


def test_f077_r26_sin_escrituras_ni_pasarela_en_el_script() -> None:
    from pathlib import Path
    fuente = Path(cfs.__file__).read_text(encoding="utf-8")
    for prohibido in ("SqlAlchemyFestivosRepository", "guardar(",
                      "save_parte", ".commit(", "httpx.post", "client.post",
                      "sigrid_write", "festivos_trabajador", "x-api-key",
                      "/api/v1/", "--api-key", "SESAME_API_"):
        assert prohibido not in fuente, prohibido
