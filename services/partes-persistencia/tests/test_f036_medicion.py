# tests/test_f036_medicion.py
"""F-036 · R23-R28: la medicion del impacto antes de desplegar.

`application/services/medicion_casado.py` es el nucleo PURO (R28): recibe
lo que el script lee (maestros de Sigrid, lineas activas y alias) y
devuelve recuentos por empresa (R24) y, por linea, que pasara con su
recurso en la pasada del conciliador (R25) y con su casado si se casara
hoy (R26). Sin nombres ni DNIs en la salida (R27).

Todo SINTETICO: ni red ni base.
"""
from __future__ import annotations

import csv
import io

import pytest

from application.services import medicion_casado as mc
from application.services.empleado_matcher import EmpleadoMatcher
from application.services.seleccion_sigrid import IndicePersonas
from domain.models.sigrid_models import EmpleadoRow, ObraRow, RecursoRow

HOY = 20261007
DNI_A = "11111111H"
DNI_B = "22222222J"
DNI_E = "55555555K"
CIF_OTRO = "40404040G"
NOMBRES = ("ANA UNO", "BEA DOS", "EVA SINFICHA", "UNO, ANA")


def _ficha(ide, nombre, dni, reside, empresa=1):
    return EmpleadoRow(ide=ide, codigo=f"E{ide}", nombre=nombre, dni=dni,
                       reside=reside, empresa=empresa, fecbaj=0)


def _rec(ide, *, cif=None, conide=None, empresa=1, fecbaj=0, cla=1,
         codigo=None, nombre=None):
    return RecursoRow(ide=ide, cif=cif, conide=conide, empresa=empresa,
                      fecbaj=fecbaj, codigo=codigo or f"MO/{ide}",
                      nombre=nombre, cla=cla)


# =============================== R24 ===================================== #

def _maestro():
    fichas = [_ficha(10, "ANA UNO", DNI_A, 910),
              _ficha(11, "SIN DNI", None, None),
              _ficha(12, "CON DNI", DNI_B, 912, empresa=28)]
    recursos = [
        _rec(910, conide=10),                         # 1: persona, DNI ficha
        _rec(911, conide=11),                         # 1: persona sin DNI
        _rec(913, cif=DNI_E),                         # 1: persona, cif
        _rec(914, cif=CIF_OTRO, conide=10),           # 1: cif != ficha
        _rec(915, cif=DNI_A, conide=10),              # 1: cif == ficha
        _rec(916, cla=2, codigo="MO/916"),            # 1: MO/ no persona
        _rec(917, cla=None, codigo="MO/917"),         # 1: MO/ no persona
        _rec(918, cla=0, codigo="MAQ/918"),           # 1: ni persona ni MO/
        _rec(919, cif=DNI_E, fecbaj=HOY),             # 1: de baja hoy
        _rec(920, cla=2, codigo="MO/920", fecbaj=1),  # 1: de baja
        _rec(912, conide=12, empresa=28),             # 28: DNI solo ficha
        _rec(930, cif=" ", conide=None, empresa=28),  # 28: sin DNI
        _rec(931, cif=DNI_B, empresa=None),           # sin empresa
    ]
    return IndicePersonas(fichas, recursos), recursos


def test_f036_r24_recuentos_por_empresa() -> None:
    indice, recursos = _maestro()
    assert mc.medir_maestro(indice, recursos, HOY) == [
        {"empresa": 1, "persona": 5, "sin_dni": 1, "dni_solo_ficha": 1,
         "cif_distinto_ficha": 1, "mo_no_persona": 2},
        {"empresa": 28, "persona": 2, "sin_dni": 1, "dni_solo_ficha": 1,
         "cif_distinto_ficha": 0, "mo_no_persona": 0},
        {"empresa": None, "persona": 1, "sin_dni": 0, "dni_solo_ficha": 0,
         "cif_distinto_ficha": 0, "mo_no_persona": 0},
    ]


def test_f036_r24_dni_solo_ficha_exige_ficha_con_dni() -> None:
    """`cif` vacio y ficha SIN DNI no es «DNI solo por ficha» (es sin DNI)."""
    indice = IndicePersonas([_ficha(11, "X", None, None)],
                            [_rec(911, conide=11)])
    (fila,) = mc.medir_maestro(indice, indice.recursos, HOY)
    assert (fila["sin_dni"], fila["dni_solo_ficha"]) == (1, 0)


def test_f036_r24_cif_distinto_se_compara_normalizado() -> None:
    indice = IndicePersonas([_ficha(10, "X", DNI_A, 910)],
                            [_rec(910, cif=" 11111111-h", conide=10)])
    (fila,) = mc.medir_maestro(indice, indice.recursos, HOY)
    assert fila["cif_distinto_ficha"] == 0


def test_f036_r24_sin_recursos_no_hay_filas() -> None:
    assert mc.medir_maestro(IndicePersonas([], []), [], HOY) == []


# ============================ R25 y R26 ================================= #

FICHAS = [_ficha(10, "ANA UNO", DNI_A, 910), _ficha(20, "BEA DOS", DNI_B, 920)]
RECURSOS = [
    _rec(910, conide=10, nombre="UNO, ANA"),
    _rec(920, conide=20, nombre="DOS, BEA"),
    _rec(921, cla=2, conide=20, nombre="MAQUINA"),
    _rec(960, cif=DNI_E, empresa=28, nombre="EVA SINFICHA"),
]
OBRAS = [ObraRow(ide=100, codigo="0100", nombre="O", empresa=1),
         ObraRow(ide=200, codigo="0200", nombre="P", empresa=28)]
INDICE = IndicePersonas(FICHAS, RECURSOS, OBRAS)


def _linea(rid=1, *, empresa=1, obra_ide=100, fecha=20260915, dni=None,
           nombre=None, emp_ide=None, emp_dni=None, reside=None,
           metodo="none", recurso=None, congelada=False, doc="doc-1"):
    return mc.LineaMedida(
        registro_id=rid, document_id=doc, empresa=empresa, obra_ide=obra_ide,
        fecha_int=fecha, dni_leido=dni, nombre_leido=nombre,
        empleado_ide=emp_ide, empleado_dni=emp_dni, empleado_reside=reside,
        empleado_match_method=metodo, recurso_ide=recurso,
        congelada=congelada)


def _medir(*lineas, aliases=None):
    return mc.medir_lineas(list(lineas), INDICE,
                           EmpleadoMatcher(min_score=0.55), aliases or {},
                           HOY)


def _uno(linea, **kw):
    (fila,) = _medir(linea, **kw)
    return fila["recurso"], fila["casado"]


# ------------------------------- R25 ----------------------------------- #

def test_f036_r25_recurso_igual() -> None:
    linea = _linea(dni=DNI_A, emp_ide=10, emp_dni=DNI_A, reside=910,
                   metodo="dni", recurso=910)
    assert _uno(linea)[0] == "igual"


def test_f036_r25_recurso_cambia() -> None:
    linea = _linea(dni=DNI_A, emp_ide=10, emp_dni=DNI_A, reside=910,
                   metodo="dni", recurso=999)
    assert _uno(linea)[0] == "cambia"


def test_f036_r25_recurso_lo_pierde_por_r2() -> None:
    """Guardado el 921 (no es persona): con R2 la persona solo tiene el 920
    y el conciliador elige ese; con el 920 de baja, lo pierde."""
    linea = _linea(dni=DNI_B, emp_ide=20, emp_dni=DNI_B, reside=921,
                   metodo="dni", recurso=921)
    assert _uno(linea)[0] == "cambia"
    sin_920 = IndicePersonas(FICHAS, [r for r in RECURSOS if r.ide != 920],
                             OBRAS)
    (fila,) = mc.medir_lineas([linea], sin_920, EmpleadoMatcher(), {}, HOY)
    assert fila["recurso"] == "pierde"


def test_f036_r25_recurso_lo_gana() -> None:
    linea = _linea(dni=DNI_A, emp_ide=10, emp_dni=DNI_A, reside=910,
                   metodo="dni", recurso=None)
    assert _uno(linea)[0] == "gana"


def test_f036_r25_sin_recurso_antes_ni_despues_es_igual() -> None:
    assert _uno(_linea(nombre="Nadie"))[0] == "igual"


def test_f036_r25_la_empresa_es_la_de_la_obra_y_si_no_la_del_parte() -> None:
    """La obra 200 es de la 28: el recurso 960 vale aunque el parte diga 1;
    sin obra, cuenta la empresa del parte."""
    con_obra = _linea(obra_ide=200, empresa=1, emp_dni=DNI_E, reside=960,
                      metodo="recurso_dni", recurso=960)
    assert _uno(con_obra)[0] == "igual"
    sin_obra = _linea(obra_ide=None, empresa=1, emp_dni=DNI_E, reside=960,
                      metodo="recurso_dni", recurso=960)
    assert _uno(sin_obra)[0] == "pierde"
    sin_obra_28 = _linea(obra_ide=None, empresa=28, emp_dni=DNI_E,
                         reside=960, metodo="recurso_dni", recurso=960)
    assert _uno(sin_obra_28)[0] == "igual"


def test_f036_r25_sin_fecha_usa_hoy() -> None:
    baja = IndicePersonas(FICHAS, [_rec(910, conide=10, fecbaj=20261001)],
                          OBRAS)
    linea = _linea(fecha=None, emp_ide=10, emp_dni=DNI_A, reside=910,
                   metodo="dni", recurso=910)
    (fila,) = mc.medir_lineas([linea], baja, EmpleadoMatcher(), {}, HOY)
    assert fila["recurso"] == "pierde"
    con_fecha = _linea(fecha=20260915, emp_ide=10, emp_dni=DNI_A, reside=910,
                       metodo="dni", recurso=910)
    (fila,) = mc.medir_lineas([con_fecha], baja, EmpleadoMatcher(), {}, HOY)
    assert fila["recurso"] == "igual"


# ------------------------------- R26 ----------------------------------- #

def test_f036_r26_casado_igual() -> None:
    linea = _linea(dni=DNI_A, emp_ide=10, emp_dni=DNI_A, reside=910,
                   metodo="dni", recurso=910)
    assert _uno(linea)[1] == "igual"


def test_f036_r26_casado_igual_compara_el_dni_normalizado() -> None:
    linea = _linea(dni=DNI_A, emp_ide=10, emp_dni="11111111-h", reside=910,
                   metodo="dni", recurso=910)
    assert _uno(linea)[1] == "igual"


def test_f036_r26_sin_casar_antes_ni_ahora_es_igual() -> None:
    assert _uno(_linea(nombre="Xiomara Zeta"))[1] == "igual"


def test_f036_r26_otra_persona() -> None:
    linea = _linea(dni=DNI_A, emp_ide=20, emp_dni=DNI_B, reside=920,
                   metodo="nombre", recurso=920)
    assert _uno(linea)[1] == "otra_persona"


def test_f036_r26_misma_persona_otro_recurso() -> None:
    linea = _linea(dni=DNI_B, emp_ide=20, emp_dni=DNI_B, reside=921,
                   metodo="dni", recurso=921)
    assert _uno(linea)[1] == "otro_recurso"


def test_f036_r26_casado_nuevo_r7() -> None:
    """Hoy sin casar (`dni_otra_empresa`); con F-036 casa por el recurso."""
    linea = _linea(empresa=28, obra_ide=200, dni=DNI_E,
                   metodo="dni_otra_empresa")
    assert _uno(linea)[1] == "casado_nuevo"


def test_f036_r26_pierde_el_casado() -> None:
    linea = _linea(nombre="Nadie Nunca", emp_ide=10, emp_dni=DNI_A,
                   reside=910, metodo="nombre", recurso=910)
    assert _uno(linea)[1] == "pierde_casado"


def test_f036_r26_casado_por_recurso_cuenta_como_casado() -> None:
    linea = _linea(empresa=28, obra_ide=200, dni=DNI_E, emp_dni=DNI_E,
                   reside=960, metodo="recurso_dni", recurso=960)
    assert _uno(linea)[1] == "igual"


def test_f036_r26_el_alias_cuenta() -> None:
    aliases = {"anita": {"ide": 10, "dni": DNI_A}}
    linea = _linea(nombre="Anita", emp_ide=10, emp_dni=DNI_A, reside=910,
                   metodo="alias", recurso=910)
    assert _uno(linea, aliases=aliases)[1] == "igual"
    assert _uno(linea)[1] == "pierde_casado"


def test_f036_r26_las_congeladas_aparte() -> None:
    linea = _linea(dni=DNI_A, emp_ide=20, emp_dni=DNI_B, reside=999,
                   metodo="nombre", recurso=999, congelada=True)
    assert _uno(linea) == ("congelada", "congelada")


# ---------------------------- resumir ---------------------------------- #

def test_f036_r26_resumir_cuenta_por_categoria() -> None:
    filas = _medir(
        _linea(1, dni=DNI_A, emp_ide=10, emp_dni=DNI_A, reside=910,
               metodo="dni", recurso=910),
        _linea(2, dni=DNI_A, emp_ide=10, emp_dni=DNI_A, reside=910,
               metodo="dni", recurso=None),
        _linea(3, empresa=28, obra_ide=200, dni=DNI_E,
               metodo="dni_otra_empresa"),
        _linea(4, congelada=True),
    )
    assert mc.resumir(filas) == {
        "lineas": 4, "congeladas": 1,
        "recurso_igual": 2, "recurso_gana": 1,
        "casado_igual": 2, "casado_casado_nuevo": 1,
    }


def test_f036_r26_resumir_vacio() -> None:
    assert mc.resumir([]) == {"lineas": 0, "congeladas": 0}


# =============================== R27 ==================================== #

def _todo_el_informe():
    indice, recursos = _maestro()
    maestro = mc.medir_maestro(indice, recursos, HOY)
    filas = _medir(
        _linea(1, dni=DNI_A, nombre="ANA UNO", emp_ide=10, emp_dni=DNI_A,
               reside=910, metodo="dni", recurso=910, doc="doc-a"),
        _linea(2, empresa=28, obra_ide=200, dni=DNI_E, nombre="EVA SINFICHA",
               metodo="dni_otra_empresa", doc="doc-b"),
    )
    return maestro, filas


def test_f036_r27_las_filas_solo_llevan_ids_empresa_y_categorias() -> None:
    _, filas = _todo_el_informe()
    assert filas == [
        {"registro_id": 1, "document_id": "doc-a", "empresa": 1,
         "recurso": "igual", "casado": "igual"},
        {"registro_id": 2, "document_id": "doc-b", "empresa": 28,
         "recurso": "igual", "casado": "casado_nuevo"},
    ]


def test_f036_r27_csv_con_punto_y_coma_y_sin_datos_personales() -> None:
    _, filas = _todo_el_informe()
    texto = mc.csv_lineas(filas)
    assert texto.splitlines()[0] == \
        "registro_id;document_id;empresa;recurso;casado"
    leidas = list(csv.DictReader(io.StringIO(texto), delimiter=";"))
    assert [f["casado"] for f in leidas] == ["igual", "casado_nuevo"]
    for prohibido in (DNI_A, DNI_E, *NOMBRES):
        assert prohibido not in texto


def test_f036_r27_markdown_resumen_y_tabla_por_empresa() -> None:
    maestro, filas = _todo_el_informe()
    md = mc.informe_markdown(maestro, mc.resumir(filas), "2026-10-07 09:30")
    assert md.startswith("# Medicion del casado contra recursos (F-036)")
    assert "2026-10-07 09:30" in md
    assert ("| empresa | persona | sin_dni | dni_solo_ficha | "
            "cif_distinto_ficha | mo_no_persona |") in md
    assert "| 1 | 5 | 1 | 1 | 1 | 2 |" in md
    assert "| (sin empresa) | 1 | 0 | 0 | 0 | 0 |" in md
    assert "| casado_casado_nuevo | 1 |" in md
    assert "| lineas | 2 |" in md
    for prohibido in (DNI_A, DNI_E, *NOMBRES):
        assert prohibido not in md


@pytest.mark.parametrize("campo", ["dni_leido", "nombre_leido",
                                   "empleado_dni"])
def test_f036_r27_ningun_dato_personal_sale_en_las_filas(campo) -> None:
    _, filas = _todo_el_informe()
    assert all(campo not in f for f in filas)
