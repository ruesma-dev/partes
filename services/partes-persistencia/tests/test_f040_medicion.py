# tests/test_f040_medicion.py
"""F-040 · R28, R29: la medicion de impacto cuenta los recursos sin DNI.

  - R28: en el maestro, la columna `sin_dni_sin_ficha` (persona, sin DNI
    del recurso y sin ficha enlazada en el maestro); por linea, `casado` =
    `propone_sin_dni` cuando el casado nuevo es `nombre_sin_dni` (antes que
    cualquier otra categoria).
  - R29: sigue de solo lectura y sin nombres ni DNIs; `leer_aliases` NO lee
    `empleado_alias.recurso_ide` (antes del despliegue no existe).

Todo SINTETICO: ni red ni base real (SQLite en memoria).
"""
from __future__ import annotations

from sqlalchemy import event

import medir_casado_recursos as herramienta
from application.services import medicion_casado as mc
from application.services.empleado_matcher import EmpleadoMatcher
from application.services.seleccion_sigrid import IndicePersonas
from domain.models.sigrid_models import EmpleadoRow, ObraRow, RecursoRow
from infrastructure.database.orm_models import EmpleadoAliasOrm
from tests.dobles import FabricaSesionSqlite

HOY = 20261008
DNI_A = "11111111H"
NOMBRES = ("ANA UNO", "RITA SOLA", "LUIS SINDNI")


def _ficha(ide, nombre, dni, reside, empresa=28):
    return EmpleadoRow(ide=ide, codigo=f"E{ide}", nombre=nombre, dni=dni,
                       reside=reside, empresa=empresa, fecbaj=0)


def _rec(ide, *, cif=None, conide=None, empresa=28, fecbaj=0, cla=1,
         nombre=None):
    return RecursoRow(ide=ide, cif=cif, conide=conide, empresa=empresa,
                      fecbaj=fecbaj, codigo=f"MO/{ide}", nombre=nombre,
                      cla=cla)


# =============================== R28 · maestro ========================== #

def test_f040_r28_columna_sin_dni_sin_ficha() -> None:
    assert mc.COLUMNAS_MAESTRO[-1] == "sin_dni_sin_ficha"
    fichas = [_ficha(10, "ANA UNO", DNI_A, 910), _ficha(40, "X", None, 940)]
    recursos = [
        _rec(910, conide=10),               # con DNI (ficha)
        _rec(940, conide=40),               # sin DNI, CON ficha
        _rec(950),                          # sin DNI, sin ficha
        _rec(951, cif=" "),                 # sin DNI, sin ficha
        _rec(952, conide=77),               # ficha fuera del maestro: sin
        _rec(953, cla=2),                   # no es persona: no cuenta
        _rec(954, fecbaj=HOY),              # de baja: no cuenta
        _rec(960, empresa=1),               # sin DNI ni ficha en la 1
    ]
    filas = mc.medir_maestro(IndicePersonas(fichas, recursos), recursos, HOY)
    por_empresa = {f["empresa"]: f for f in filas}
    assert (por_empresa[28]["sin_dni"],
            por_empresa[28]["sin_dni_sin_ficha"]) == (4, 3)
    assert (por_empresa[1]["sin_dni"],
            por_empresa[1]["sin_dni_sin_ficha"]) == (1, 1)


def test_f040_r28_el_informe_lleva_la_columna() -> None:
    recursos = [_rec(950)]
    maestro = mc.medir_maestro(IndicePersonas([], recursos), recursos, HOY)
    md = mc.informe_markdown(maestro, mc.resumir([]), "2026-10-08 10:00")
    assert "| mo_no_persona | sin_dni_sin_ficha |" in md
    assert "| 28 | 1 | 1 | 0 | 0 | 0 | 1 |" in md


# =============================== R28 · lineas =========================== #

FICHAS = [_ficha(10, "ANA UNO", DNI_A, 910)]
RECURSOS = [_rec(910, conide=10, nombre="ANA UNO"),
            _rec(970, nombre="RITA SOLA")]
OBRAS = [ObraRow(ide=200, codigo="0200", nombre="P", empresa=28)]
INDICE = IndicePersonas(FICHAS, RECURSOS, OBRAS)


def _linea(rid=1, *, nombre=None, emp_ide=None, emp_dni=None, reside=None,
           metodo="none", recurso=None):
    return mc.LineaMedida(
        registro_id=rid, document_id="doc-1", empresa=28, obra_ide=200,
        fecha_int=20260915, dni_leido=None, nombre_leido=nombre,
        empleado_ide=emp_ide, empleado_dni=emp_dni, empleado_reside=reside,
        empleado_match_method=metodo, recurso_ide=recurso, congelada=False)


def _casado(linea, aliases=None) -> str:
    (fila,) = mc.medir_lineas([linea], INDICE,
                              EmpleadoMatcher(min_score=0.55),
                              aliases or {}, HOY)
    return fila["casado"]


def test_f040_r28_sin_casar_hoy_y_propone_sin_dni() -> None:
    assert _casado(_linea(nombre="Rita Sola")) == "propone_sin_dni"


def test_f040_r28_propone_sin_dni_va_antes_que_pierde_casado() -> None:
    """Casada hoy por nombre con otra persona; con F-040 se propondria."""
    linea = _linea(nombre="Rita Sola", emp_ide=10, emp_dni=DNI_A,
                   reside=910, metodo="nombre", recurso=910)
    assert _casado(linea) == "propone_sin_dni"


def test_f040_r28_las_demas_categorias_no_cambian() -> None:
    assert _casado(_linea(nombre="Nadie Nunca")) == "igual"
    assert _casado(_linea(nombre="Ana Uno")) == "casado_nuevo"


def test_f040_r28_resumir_cuenta_propone_sin_dni() -> None:
    filas = mc.medir_lineas(
        [_linea(1, nombre="Rita Sola"), _linea(2, nombre="Rita Sola")],
        INDICE, EmpleadoMatcher(min_score=0.55), {}, HOY)
    assert mc.resumir(filas)["casado_propone_sin_dni"] == 2


def test_f040_r29_sin_datos_personales() -> None:
    recursos = RECURSOS
    maestro = mc.medir_maestro(INDICE, recursos, HOY)
    filas = mc.medir_lineas([_linea(nombre="Rita Sola")], INDICE,
                            EmpleadoMatcher(min_score=0.55), {}, HOY)
    md = mc.informe_markdown(maestro, mc.resumir(filas), "x")
    csv = mc.csv_lineas(filas)
    for prohibido in (DNI_A, *NOMBRES):
        assert prohibido not in md and prohibido not in csv


# ============================ R29 · alias ============================== #

def test_f040_r29_leer_aliases_no_lee_recurso_ide() -> None:
    fabrica = FabricaSesionSqlite()
    with fabrica.create_session() as s:
        s.add(EmpleadoAliasOrm(nombre_norm="rita", empleado_ide=None,
                               empleado_dni=None, recurso_ide=970,
                               created_at_utc="2026-10-01T00:00:00Z"))
        s.commit()
    sentencias: list[str] = []
    event.listen(fabrica.engine, "before_cursor_execute",
                 lambda _c, _cur, sql, *_a: sentencias.append(sql))
    with fabrica.engine.connect() as conn:
        aliases = herramienta.leer_aliases(conn)
    assert aliases == {"rita": {"ide": None, "dni": None}}
    assert sentencias and all("recurso_ide" not in s for s in sentencias)
    assert all(s.lstrip().upper().startswith("SELECT") for s in sentencias)
