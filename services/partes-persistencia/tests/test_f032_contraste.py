# tests/test_f032_contraste.py
"""F-032 · R29–R33: `contrastar_festivos_sesame.py`, el contraste previo.

La herramienta de consola de sv3 que el humano corre ANTES de encender
(puerta DA12): compara cada calendario de Sesame con el JSON de respaldo,
marca `INCOMPLETO` y `FALTAN DEL RESPALDO` y, con `--impacto`, cuenta que
lineas de los partes activos cambiarian. Solo lee: Sesame por `GET`
(con `httpx.MockTransport`, sin red) y `partes` por
`fetch_registros_para_recurso` (aqui un repositorio falso que revienta si
se le pide escribir). Datos sinteticos; los DNIs, solo en el CSV.

F-077: el Sesame falso habla como la API de Sesame HR (calendarios en
`/schedule/v1/holiday-calendar`, indice de empleados y festivos por
empleado), el token va por `SESAME_TOKEN` o por consola (sin
`--api-key`) y la URL es `https://`.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from pathlib import Path

import httpx
import pytest

import contrastar_festivos_sesame as cfs
from infrastructure.calendario.json_calendario_laboral import (
    JsonCalendarioLaboral,
)
from infrastructure.sesame.sesame_hr_client import (
    RUTA_CALENDARIOS,
    RUTA_EMPLEADOS,
    RUTA_FESTIVOS,
)

ANO = 2026
DNI = "12345678Z"
OTRO = "87654321X"
ROTO = "11111111H"
AHORA = datetime(2026, 11, 17, 9, 5)
CLAVE = "clave-de-prueba-secreta"
URL = "https://sesame.ejemplo.test"

#: Respaldo minimo: nacionales + el 2026-03-19 (jueves) a mayores.
RESPALDO = {"sabado_no_laborable": True, "domingo_no_laborable": True,
            "festivos_nacionales": True,
            "festivos": [{"fecha": "2026-03-19"}]}


def _nacionales_lv() -> list[str]:
    """Los nacionales de 2026 que caen de lunes a viernes."""
    return ["2026-01-01", "2026-01-06", "2026-04-03", "2026-05-01",
            "2026-10-12", "2026-12-08", "2026-12-25"]


def _cal(id_, nombre, fechas, por_defecto=False):
    return {"id": id_, "nombre": nombre, "por_defecto": por_defecto,
            "festivos": [{"fecha": f, "nombre": f"F {f}"} for f in fechas]}


#: Madrid: todo el respaldo + San Isidro (viernes) + un sabado.
MADRID = _cal("cal-mad", "Madrid", _nacionales_lv() + [
    "2026-03-19", "2026-05-15", "2026-08-15", "2027-01-01"], True)
#: Corto: le faltan el 19 de marzo y la Navidad del respaldo.
CORTO = _cal("cal-corto", "Corto", [f for f in _nacionales_lv()
                                    if f != "2026-12-25"])
VACIO = _cal("cal-vacio", "Vacio", [])


@pytest.fixture
def respaldo(tmp_path) -> JsonCalendarioLaboral:
    ruta = tmp_path / "calendario.json"
    ruta.write_text(json.dumps(RESPALDO), encoding="utf-8")
    return JsonCalendarioLaboral(path=ruta)


@pytest.fixture
def ruta_calendario(tmp_path) -> str:
    ruta = tmp_path / "calendario.json"
    ruta.write_text(json.dumps(RESPALDO), encoding="utf-8")
    return str(ruta)


# ----------------------------- R29, R30 ------------------------------------ #

def test_f032_r29_contraste_de_un_calendario_completo(respaldo) -> None:
    fila = cfs.contrastar_calendario(MADRID, ANO, respaldo, minimo=1)
    assert (fila["id"], fila["nombre"], fila["por_defecto"]) == (
        "cal-mad", "Madrid", True)
    assert fila["n_festivos"] == 10               # sin el de 2027
    assert fila["solo_sesame"] == ["2026-05-15"]  # el sabado no cuenta
    assert fila["solo_respaldo"] == []
    assert fila["incompleto"] is False
    assert fila["faltan_del_respaldo"] is False


def test_f032_r30_faltan_del_respaldo(respaldo) -> None:
    fila = cfs.contrastar_calendario(CORTO, ANO, respaldo, minimo=1)
    assert fila["solo_respaldo"] == ["2026-03-19", "2026-12-25"]
    assert fila["solo_sesame"] == []
    assert fila["faltan_del_respaldo"] is True


@pytest.mark.parametrize("minimo,incompleto", [(1, True), (0, False)])
def test_f032_r30_incompleto_con_el_minimo(respaldo, minimo,
                                           incompleto) -> None:
    fila = cfs.contrastar_calendario(VACIO, ANO, respaldo, minimo=minimo)
    assert fila["n_festivos"] == 0
    assert fila["incompleto"] is incompleto


def test_f032_r30_minimo_por_defecto_es_1(respaldo) -> None:
    assert cfs.contrastar_calendario(VACIO, ANO, respaldo)["incompleto"] \
        is True
    corto = cfs.contrastar_calendario(CORTO, ANO, respaldo, minimo=7)
    assert corto["incompleto"] is True             # 6 < 7


def test_f032_r30_el_markdown_marca_las_puertas(respaldo) -> None:
    filas = [cfs.contrastar_calendario(c, ANO, respaldo, minimo=1)
             for c in (MADRID, CORTO, VACIO)]
    md = cfs.render_markdown(ANO, filas, None, momento="2026-11-17 09:05")
    assert "FALTAN DEL RESPALDO" in md
    assert "INCOMPLETO" in md
    assert "Madrid" in md and "por defecto" in md


# ------------------------------- R31 --------------------------------------- #

def _a_hr(cal: dict) -> dict:
    """Un calendario de los de arriba, en la forma de Sesame HR."""
    return {"id": cal["id"], "name": cal["nombre"],
            "default": cal["por_defecto"],
            "daysOff": [{"date": f["fecha"], "name": f["nombre"]}
                        for f in cal["festivos"]]}


class Sesame:
    """Sesame HR falso por `MockTransport`: anota metodo, ruta y cabeceras.

    `festivos`: DNI -> lista de fechas o estado HTTP. Los DNIs de
    `festivos` forman el indice de empleados (`emp-<n>`); cualquier otro
    DNI es «no encontrado». Revienta con cualquier metodo distinto de GET.
    """

    def __init__(self, calendarios=(MADRID, CORTO), festivos=None,
                 listado_status=200):
        self.peticiones: list[tuple[str, str, dict]] = []
        self.calendarios = list(calendarios)
        self.festivos = festivos or {}
        self.listado_status = listado_status
        self.ids = {f"emp-{i}": dni
                    for i, dni in enumerate(sorted(self.festivos))}

    def __call__(self, request: httpx.Request) -> httpx.Response:
        assert request.method == "GET", request.method
        self.peticiones.append((request.method, request.url.path,
                                dict(request.headers)))
        if request.url.path == RUTA_CALENDARIOS:
            if self.listado_status != 200:
                return httpx.Response(self.listado_status,
                                      json={"error": "caido"})
            return httpx.Response(200, json={
                "data": [_a_hr(c) for c in self.calendarios],
                "meta": {"lastPage": 1}})
        if request.url.path == RUTA_EMPLEADOS:
            return httpx.Response(200, json={"data": [
                {"id": i, "nid": dni, "status": "active",
                 "firstName": "Nombreficticio", "email": "x@ejemplo.test"}
                for i, dni in self.ids.items()], "meta": {"lastPage": 1}})
        if request.url.path == RUTA_FESTIVOS:
            r = self.festivos[self.ids[request.url.params["employeeId"]]]
            if isinstance(r, int):
                return httpx.Response(r, json={"error": "x"})
            return httpx.Response(200, json={"data": [
                {"dayOff": {"date": f, "name": None}} for f in r]})
        return httpx.Response(500)

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self)


def _sin_prompt(prompt):
    raise AssertionError("no deberia pedir el token por consola")


def _main(args, sesame, *, repositorio=None, monkeypatch=None,
          pedir_token=lambda prompt: CLAVE):
    return cfs.main(args, ahora=AHORA, transport=sesame.transport(),
                    repositorio=repositorio, pedir_token=pedir_token)


def _sin_env(monkeypatch):
    for v in ("SESAME_BASE_URL", "SESAME_TOKEN", "SESAME_TIMEOUT_S",
              "SESAME_FESTIVOS_MINIMOS", "PG_PASSWORD", "PG_ADMIN_PASSWORD"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr(cfs, "_settings", lambda: None)


def test_f032_r31_escribe_md_y_csv_y_sale_0(tmp_path, monkeypatch,
                                            ruta_calendario, capsys) -> None:
    _sin_env(monkeypatch)
    sesame = Sesame()
    rc = _main(["--ano", "2026", "--base-url", URL,
                "--calendario", ruta_calendario,
                "--salida", str(tmp_path)], sesame)
    assert rc == 0
    md = tmp_path / "contraste_festivos_2026_20261117-0905.md"
    cs = tmp_path / "contraste_festivos_2026_20261117-0905.csv"
    assert md.is_file() and cs.is_file()
    crudo = cs.read_bytes()
    assert crudo.startswith(b"\xef\xbb\xbf")
    cabecera = crudo.decode("utf-8-sig").splitlines()[0]
    assert ";" in cabecera and "," not in cabecera
    assert md.read_bytes().startswith(b"\xef\xbb\xbf")
    assert [p[:2] for p in sesame.peticiones] == [
        ("GET", RUTA_CALENDARIOS)]
    assert sesame.peticiones[0][2]["authorization"] == f"Bearer {CLAVE}"
    salida = capsys.readouterr().out
    assert CLAVE not in salida
    assert CLAVE not in md.read_text(encoding="utf-8-sig")


def test_f032_r31_la_linea_de_comandos_manda_sobre_el_entorno(
        tmp_path, monkeypatch, ruta_calendario) -> None:
    _sin_env(monkeypatch)
    monkeypatch.setenv("SESAME_BASE_URL", "https://del-entorno.test")
    monkeypatch.setenv("SESAME_TOKEN", "clave-del-entorno")
    vistas = []

    def anota(request):
        vistas.append((request.url.host, request.headers["authorization"]))
        return Sesame()(request)

    rc = cfs.main(["--ano", "2026", "--base-url", "https://de-la-linea.test",
                   "--calendario", ruta_calendario,
                   "--salida", str(tmp_path)],
                  ahora=AHORA, transport=httpx.MockTransport(anota),
                  pedir_token=_sin_prompt)
    assert rc == 0
    assert vistas == [("de-la-linea.test", "Bearer clave-del-entorno")]


def test_f032_r31_sin_linea_de_comandos_usa_el_entorno(
        tmp_path, monkeypatch, ruta_calendario) -> None:
    _sin_env(monkeypatch)
    monkeypatch.setenv("SESAME_BASE_URL", "https://del-entorno.test")
    monkeypatch.setenv("SESAME_TOKEN", "clave-del-entorno")
    vistas = []

    def anota(request):
        vistas.append((request.url.host, request.headers["authorization"]))
        return Sesame()(request)

    assert cfs.main(["--ano", "2026", "--calendario", ruta_calendario,
                     "--salida", str(tmp_path)], ahora=AHORA,
                    transport=httpx.MockTransport(anota),
                    pedir_token=_sin_prompt) == 0
    assert vistas == [("del-entorno.test", "Bearer clave-del-entorno")]


def test_f032_r31_minimo_del_entorno(tmp_path, monkeypatch,
                                     ruta_calendario) -> None:
    _sin_env(monkeypatch)
    monkeypatch.setenv("SESAME_FESTIVOS_MINIMOS", "7")
    assert _main(["--ano", "2026", "--base-url", URL,
                  "--calendario", ruta_calendario, "--salida",
                  str(tmp_path)], Sesame(calendarios=[CORTO])) == 0
    md = next(tmp_path.glob("*.md")).read_text(encoding="utf-8-sig")
    assert "INCOMPLETO" in md


def test_f032_r31_sin_configuracion_sale_distinto_de_0_sin_informe(
        tmp_path, monkeypatch, ruta_calendario, capsys) -> None:
    _sin_env(monkeypatch)
    sesame = Sesame()
    rc = _main(["--ano", "2026", "--calendario", ruta_calendario,
                "--salida", str(tmp_path)], sesame)
    assert rc != 0
    assert list(tmp_path.glob("contraste_*")) == []
    assert sesame.peticiones == []
    assert "SESAME_BASE_URL" in capsys.readouterr().err


def test_f032_r31_listado_fallido_sale_distinto_de_0_sin_informe(
        tmp_path, monkeypatch, ruta_calendario) -> None:
    _sin_env(monkeypatch)
    rc = _main(["--ano", "2026", "--base-url", URL,
                "--calendario", ruta_calendario, "--salida",
                str(tmp_path)], Sesame(listado_status=403))
    assert rc != 0
    assert list(tmp_path.glob("contraste_*")) == []


def test_f032_r31_impacto_sin_bbdd_configurada_sale_distinto_de_0(
        tmp_path, monkeypatch, ruta_calendario) -> None:
    _sin_env(monkeypatch)
    rc = _main(["--ano", "2026", "--base-url", URL,
                "--calendario", ruta_calendario, "--salida",
                str(tmp_path), "--impacto"], Sesame())
    assert rc != 0
    assert list(tmp_path.glob("contraste_*")) == []


# ------------------------------- R32 --------------------------------------- #

def _reg(rid, fecha, *, dni=DNI, horas=8.0, estado=None, aprobado=False,
         borrada=None, tipo="normal", obra=10, pareja=False, doc="d1"):
    return {"registro_id": rid, "document_id": doc, "obra_ide": obra,
            "empleado_dni": dni, "fecha_int": int(fecha.replace("-", "")),
            "tipo_hora": tipo, "horas": horas, "sigrid_estado": estado,
            "doc_approved": aprobado, "deleted_at_utc": borrada,
            "congelada_por_pareja": pareja, "extra_auto": False,
            "horas_orig": None}


#: Para DNI, Sesame da San Isidro (viernes 15-may) y QUITA el 19-mar del
#: respaldo (jueves).
FESTIVOS_DNI = {k: None for k in _nacionales_lv() + ["2026-05-15"]}


def test_f032_r32_clases_sentido_y_semana(respaldo) -> None:
    regs = [
        _reg(1, "2026-05-15"),                         # libre, a festivo
        _reg(2, "2026-05-15", estado="registrado"),    # reajustable
        _reg(3, "2026-05-15", estado="dedicacion"),    # dura
        _reg(4, "2026-03-19", aprobado=True),          # reajustable, a lab.
        _reg(5, "2026-05-13"),                         # misma semana ISO
        _reg(6, "2026-05-20"),                         # otra semana: fuera
        _reg(7, "2026-05-15", borrada="2026-06-01T00:00:00Z"),  # papelera
        _reg(8, "2026-05-15", horas=0.0),              # sin horas
        _reg(9, "2026-05-14", pareja=True),            # congelada por pareja
    ]
    imp = cfs.clasificar_impacto(regs, {DNI: FESTIVOS_DNI}, respaldo, ANO)
    por_id = {f["registro_id"]: f for f in imp["lineas"]}
    assert set(por_id) == {1, 2, 3, 4, 5, 9}
    assert (por_id[1]["clase"], por_id[1]["sentido"]) == ("libre",
                                                          "a_festivo")
    assert por_id[2]["clase"] == "reajustable"
    assert por_id[3]["clase"] == "dura"
    assert (por_id[4]["clase"], por_id[4]["sentido"]) == ("reajustable",
                                                          "a_laborable")
    assert (por_id[5]["clase"], por_id[5]["sentido"]) == ("libre", "semana")
    assert por_id[9]["clase"] == "reajustable"
    assert imp["por_clase"] == {"libre": 2, "reajustable": 3, "dura": 1}
    assert imp["por_sentido"] == {"a_festivo": 3, "a_laborable": 1,
                                  "semana": 2}
    assert imp["por_ano"] == {2026: 6}
    assert imp["por_obra_mes"] == {(10, "2026-03"): 1, (10, "2026-05"): 5}
    # El 15-may mezcla una libre con congeladas: dia mixto.
    assert imp["dias_mixtos"] == 1
    assert imp["errores"] == []


def test_f032_r32_un_404_es_el_respaldo_y_no_cambia_nada(respaldo) -> None:
    regs = [_reg(1, "2026-05-15", dni=OTRO), _reg(2, "2026-03-19", dni=OTRO)]
    imp = cfs.clasificar_impacto(regs, {OTRO: None}, respaldo, ANO)
    assert imp["lineas"] == [] and imp["errores"] == []


def test_f032_r32_sin_dni_no_cambia(respaldo) -> None:
    imp = cfs.clasificar_impacto([_reg(1, "2026-05-15", dni=None)], {},
                                 respaldo, ANO)
    assert imp["lineas"] == []


def test_f032_r32_un_dni_que_falla_es_una_fila_de_error(respaldo) -> None:
    regs = [_reg(1, "2026-05-15", dni=ROTO), _reg(2, "2026-05-15")]
    imp = cfs.clasificar_impacto(
        regs, {ROTO: RuntimeError("sesame 500"), DNI: FESTIVOS_DNI},
        respaldo, ANO)
    assert imp["errores"] == [{"dni": ROTO, "error": "RuntimeError"}]
    assert [f["registro_id"] for f in imp["lineas"]] == [2]


def test_f032_r32_otro_ano_no_entra(respaldo) -> None:
    imp = cfs.clasificar_impacto([_reg(1, "2025-05-15")], {DNI: FESTIVOS_DNI},
                                 respaldo, ANO)
    assert imp["lineas"] == []


def test_f032_r32_el_markdown_no_lleva_dnis_y_el_csv_si(respaldo) -> None:
    regs = [_reg(1, "2026-05-15"), _reg(2, "2026-05-15", dni=ROTO)]
    imp = cfs.clasificar_impacto(
        regs, {DNI: FESTIVOS_DNI, ROTO: RuntimeError("x")}, respaldo, ANO)
    filas = [cfs.contrastar_calendario(MADRID, ANO, respaldo)]
    md = cfs.render_markdown(ANO, filas, imp, momento="2026-11-17 09:05")
    assert DNI not in md and ROTO not in md
    assert "| libre | 1 |" in md
    buf = io.StringIO()
    cfs.escribir_csv(buf, filas, imp)
    filas_csv = list(csv.reader(io.StringIO(buf.getvalue()), delimiter=";"))
    texto = buf.getvalue()
    assert DNI in texto and ROTO in texto
    assert len({len(f) for f in filas_csv}) == 1      # todas las columnas


def test_f032_r32_main_con_impacto(tmp_path, monkeypatch,
                                   ruta_calendario) -> None:
    _sin_env(monkeypatch)
    repo = RepoSoloLectura([_reg(1, "2026-05-15"),
                            _reg(2, "2026-05-15", dni=OTRO),
                            _reg(3, "2026-05-15", dni=ROTO),
                            _reg(4, "2026-05-15", dni="12.345.678-z")])
    # F-077: un 404 de un empleado conocido es fallo (DA6) sin abrir el
    # corte; OTRO no esta en el indice (no encontrado: el respaldo).
    sesame = Sesame(festivos={DNI: list(FESTIVOS_DNI), ROTO: 404})
    rc = _main(["--ano", "2026", "--base-url", URL,
                "--calendario", ruta_calendario, "--salida",
                str(tmp_path), "--impacto"], sesame, repositorio=repo)
    assert rc == 0
    pedidos = sorted(p[1] for p in sesame.peticiones)
    assert pedidos.count(RUTA_FESTIVOS) == 2   # uno por DNI del indice
    assert pedidos.count(RUTA_EMPLEADOS) == 1  # el indice, una vez
    assert {p[0] for p in sesame.peticiones} == {"GET"}
    md = next(tmp_path.glob("*.md")).read_text(encoding="utf-8-sig")
    assert DNI not in md and ROTO not in md and OTRO not in md
    cs = next(tmp_path.glob("*.csv")).read_text(encoding="utf-8-sig")
    assert ROTO in cs


# ------------------------------- R33 --------------------------------------- #

class RepoSoloLectura:
    """Solo `fetch_registros_para_recurso`; cualquier otra cosa revienta."""

    def __init__(self, regs):
        self._regs = regs
        self.lecturas = 0

    def fetch_registros_para_recurso(self):
        self.lecturas += 1
        return list(self._regs)

    def __getattr__(self, nombre):
        raise AssertionError(f"el contraste no puede llamar a {nombre}")


def test_f032_r33_solo_get_y_ninguna_escritura(tmp_path, monkeypatch,
                                                ruta_calendario) -> None:
    _sin_env(monkeypatch)
    repo = RepoSoloLectura([_reg(1, "2026-05-15")])
    sesame = Sesame(festivos={DNI: list(FESTIVOS_DNI)})
    assert _main(["--ano", "2026", "--base-url", URL,
                  "--calendario", ruta_calendario, "--salida",
                  str(tmp_path), "--impacto"], sesame,
                 repositorio=repo) == 0
    assert {p[0] for p in sesame.peticiones} == {"GET"}
    assert repo.lecturas == 1


def test_f032_r33_el_script_no_importa_nada_que_escriba() -> None:
    fuente = Path(cfs.__file__).read_text(encoding="utf-8")
    for prohibido in ("SqlAlchemyFestivosRepository", "guardar(",
                      "save_parte", ".commit(", "httpx.post", "client.post",
                      "sigrid_write", "festivos_trabajador"):
        assert prohibido not in fuente, prohibido
