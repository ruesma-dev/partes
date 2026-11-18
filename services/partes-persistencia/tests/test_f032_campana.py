# tests/test_f032_campana.py
"""F-032 · tests de la pasada de campaña: supervivientes de la mutación.

Cada test fija un comportamiento que la campaña de `progress/mutacion_F-032.md`
mostró sin comprobar (número de superviviente entre corchetes). Cada uno se
verificó a mano: con el mutante aplicado, el test cae. Sin red ni BBDD
real; datos sintéticos.
"""
from __future__ import annotations

import csv
import dataclasses
import io
import logging

import pytest

import contrastar_festivos_sesame as cfs
from application.services.festivos_guardados import del_ano
from application.services.refresco_festivos import (
    ResultadoRefresco,
    anos_de_semana,
)
from infrastructure.database.sqlalchemy_festivos_repository import (
    SqlAlchemyFestivosRepository,
)
from infrastructure.sesame.sesame_api_client import SesameApiClient
from tests.dobles import FabricaSesionSqlite
from tests.test_f032_contraste import (  # noqa: F401 (fixtures)
    ANO,
    CLAVE,
    CORTO,
    MADRID,
    VACIO,
    Sesame,
    _cal,
    _main,
    _nacionales_lv,
    _sin_env,
    respaldo,
    ruta_calendario,
)
from tests.test_f032_ingesta import _parte, _pipeline, _Refresco
from tests.test_f032_repositorio import _fila
from tests.test_f047_parte_nuevo_sv3 import _request

SIN_NOMBRE = _cal("cal-sin", None, _nacionales_lv())


# ---------------------- ingesta, refresco y tabla ----------------------- #

def test_f032_r8_una_sola_clave_sin_dato_ya_sube_a_revision() -> None:
    """[8] `sin_dato > 0`: basta UNA clave sin festivos."""
    eventos: list = []
    refresco = _Refresco(eventos, ResultadoRefresco(1, 0, 0, 1))
    pipeline, repo = _pipeline(eventos, _parte(), refresco)
    pipeline.run(_request())
    assert repo.guardados[0]["review_required"] is True


def test_f032_r8_el_resultado_del_refresco_es_inmutable() -> None:
    """[10] El recuento que decide la revisión no se puede reescribir."""
    res = ResultadoRefresco(1, 0, 0, 0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        res.sin_dato = 1  # type: ignore[misc]


@pytest.mark.parametrize("fecha, anos", [
    ("2023-12-27", {2023}),          # semana del 25 al 31: acaba en domingo
    ("2026-12-31", {2026, 2027}),    # semana del 28/12 al 3/1
    ("2027-01-01", {2026, 2027}),
])
def test_f032_r4_anos_de_la_semana_iso_lunes_a_domingo(fecha, anos) -> None:
    """[11] La semana ISO va de lunes a DOMINGO: el lunes siguiente no
    cuenta (el 31/12/2023 es domingo; el 1/1/2024, lunes de otra semana)."""
    assert anos_de_semana(fecha) == anos


def test_f032_r42_un_nombre_no_textual_se_guarda_como_texto() -> None:
    """[9] Solo `None` es «sin nombre»; otro valor se guarda como texto."""
    assert del_ano([("2026-01-01", 0), ("2026-01-06", None)], 2026) == {
        "2026-01-01": "0", "2026-01-06": None}


def test_f032_r11_leer_todas_cuenta_las_omitidas_desde_cero(caplog) -> None:
    """[30] El recuento de filas omitidas del log empieza en 0."""
    repo = SqlAlchemyFestivosRepository(FabricaSesionSqlite())
    repo.guardar(_fila())
    with caplog.at_level(logging.INFO):
        repo.leer_todas()
    assert any("1 fila(s) leidas, 0 omitida(s)" in r.getMessage()
               for r in caplog.records)


# ------------------------------- contraste ------------------------------ #

def _args(tmp_path, ruta_calendario, *extra):
    return ["--ano", "2026", "--base-url", "http://s:1", "--api-key", CLAVE,
            "--calendario", ruta_calendario, "--salida", str(tmp_path),
            *extra]


def test_f032_r31_cada_fallo_sale_con_su_codigo(
        tmp_path, monkeypatch, ruta_calendario) -> None:
    """[12, 13] 2 = configuración, 3 = listado, 4 = lectura de partes."""
    _sin_env(monkeypatch)

    class RepoRoto:
        def fetch_registros_para_recurso(self):
            raise OSError("sin base")

    assert _main(["--ano", "2026", "--calendario", ruta_calendario,
                  "--salida", str(tmp_path)], Sesame()) == 2
    assert _main(_args(tmp_path, ruta_calendario),
                 Sesame(listado_status=502)) == 3
    assert _main(_args(tmp_path, ruta_calendario, "--impacto"), Sesame(),
                 repositorio=RepoRoto()) == 4
    assert list(tmp_path.glob("contraste_*")) == []


def _filas_md(respaldo, calendarios):
    filas = [cfs.contrastar_calendario(c, ANO, respaldo, minimo=1)
             for c in calendarios]
    md = cfs.render_markdown(ANO, filas, None, momento="2026-11-17 09:05")
    return {linea.split(" (`")[0].lstrip("| "): linea
            for linea in md.splitlines() if " (`" in linea}


def test_f032_r30_cada_fila_del_markdown_lleva_sus_marcas(respaldo) -> None:
    """[14–17] Por fila: «—» si no hay días, la puerta solo donde toca,
    «por defecto» solo en el suyo y «ok» si no hay marcas."""
    filas = _filas_md(respaldo, (MADRID, CORTO, VACIO))
    madrid, corto, vacio = filas["Madrid"], filas["Corto"], filas["Vacio"]
    assert madrid.startswith("| Madrid (`cal-mad`) · por defecto | 10 | ")
    assert "2026-05-15" in madrid and "| — |" in madrid
    assert madrid.endswith("| ok |")
    assert "por defecto" not in corto and "por defecto" not in vacio
    assert corto.endswith("| **FALTAN DEL RESPALDO** |")
    assert "2026-03-19, 2026-12-25" in corto
    assert vacio.endswith("| **FALTAN DEL RESPALDO** **INCOMPLETO** |")


def test_f032_r31_el_csv_lleva_el_id_del_calendario(respaldo) -> None:
    """[18]"""
    filas = [cfs.contrastar_calendario(c, ANO, respaldo, minimo=1)
             for c in (MADRID, SIN_NOMBRE)]
    buf = io.StringIO()
    cfs.escribir_csv(buf, filas, None)
    leidas = list(csv.DictReader(io.StringIO(buf.getvalue()), delimiter=";"))
    assert [(f["tipo"], f["calendario_id"], f["calendario"])
            for f in leidas] == [("calendario", "cal-mad", "Madrid"),
                                 ("calendario", "cal-sin", "")]


def test_f032_r29_listar_calendarios_devuelve_los_de_sesame() -> None:
    """[19]"""
    cliente = SesameApiClient(base_url="http://s:1", api_key=CLAVE,
                              transport=Sesame().transport())
    assert [c["id"] for c in cfs.listar_calendarios(cliente)] == [
        "cal-mad", "cal-corto"]


def test_f032_r31_el_ano_es_obligatorio() -> None:
    """[20]"""
    with pytest.raises(SystemExit):
        cfs._argumentos(["--base-url", "http://s:1"])


def test_f032_r31_la_salida_se_crea_aunque_falten_carpetas(
        tmp_path, monkeypatch, ruta_calendario) -> None:
    """[22]"""
    _sin_env(monkeypatch)
    destino = tmp_path / "a" / "b"
    assert _main(_args(destino, ruta_calendario), Sesame()) == 0
    assert len(list(destino.glob("contraste_*"))) == 2


def test_f032_r30_la_consola_resume_cada_calendario(
        tmp_path, monkeypatch, ruta_calendario, capsys) -> None:
    """[23, 24] Nombre (o id si no lo tiene), recuento y marcas."""
    _sin_env(monkeypatch)
    assert _main(_args(tmp_path, ruta_calendario),
                 Sesame(calendarios=(MADRID, CORTO, SIN_NOMBRE))) == 0
    lineas = capsys.readouterr().out.splitlines()
    assert "Madrid: 10 festivos" in lineas
    assert "Corto: 6 festivos · FALTAN DEL RESPALDO" in lineas
    assert "cal-sin: 7 festivos · FALTAN DEL RESPALDO" in lineas
