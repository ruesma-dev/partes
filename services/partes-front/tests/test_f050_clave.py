# tests/test_f050_clave.py
"""F-050 · clave de trabajador del portal (R1-R4, R11).

Funciones puras sobre registros del ORM sin sesion: ni red ni BBDD.
Nombres, DNIs y recursos SINTETICOS.

La clave nueva se importa dentro de cada test para que la fase RED falle
test a test (y no como un error de coleccion del modulo entero).
"""
from __future__ import annotations

import inspect
import unicodedata

import pytest
from infrastructure.database.orm_models import ParteRegistroOrm


def _linea(**campos) -> ParteRegistroOrm:
    """Registro transitorio con solo lo que mira la clave."""
    base = {
        "document_id": "doc-sintetico", "line_index": 0,
        "empleado_ide": None, "empleado_reside": None, "recurso_ide": None,
        "empleado_match_method": None, "trabajador_nombre_leido": None,
        "empleado_dni": None,
    }
    base.update(campos)
    return ParteRegistroOrm(**base)


# Copia LITERAL de `worker_key_for_registro` en `dc03468` (antes de F-050),
# con su `_norm`: R3 exige que las lineas no casadas den lo mismo que ella.
def _strip_accents_antes(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _norm_antes(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(_strip_accents_antes(str(text)).upper().split())


def _clave_antes(reg) -> str:
    if reg.empleado_ide is not None:
        return f"emp-{reg.empleado_ide}"
    nombre = _norm_antes(reg.trabajador_nombre_leido)
    if nombre:
        return "nom-" + nombre.replace(" ", "_")
    return "sin-trabajador"


# ===================================================================== #
# R1 · orden de la clave
# ===================================================================== #

def test_f050_r1_casada_sin_ficha_con_recurso_da_rec() -> None:
    """E1: la linea de la IA (sin ficha, `recurso_dni`) y la manual
    (`recurso_manual`) del mismo recurso dan la misma clave `rec-`,
    aunque sus leidos no se parezcan."""
    from infrastructure.database.parte_repository import (
        worker_key_for_registro,
    )
    ia = _linea(recurso_ide=6001, empleado_match_method="recurso_dni",
                trabajador_nombre_leido="Nombre Apellido")
    manual = _linea(recurso_ide=6001, empleado_reside=6001,
                    empleado_match_method="recurso_manual",
                    trabajador_nombre_leido="APELLIDO, NOMBRE")
    assert worker_key_for_registro(ia) == "rec-6001"
    assert worker_key_for_registro(manual) == "rec-6001"


def test_f050_r1_con_ficha_y_recurso_da_rec() -> None:
    """E2/E8: con ficha y recurso manda el recurso (DA1 opcion A)."""
    from infrastructure.database.parte_repository import (
        worker_key_for_registro,
    )
    con_ficha = _linea(empleado_ide=77, recurso_ide=501,
                       trabajador_nombre_leido="Persona Sintetica")
    sin_ficha = _linea(recurso_ide=501, empleado_match_method="recurso_nombre",
                       trabajador_nombre_leido="Otra Lectura")
    assert worker_key_for_registro(con_ficha) == "rec-501"
    assert worker_key_for_registro(sin_ficha) == "rec-501"


def test_f050_r1_recurso_ide_antes_que_empleado_reside() -> None:
    from infrastructure.database.parte_repository import (
        worker_key_for_registro,
    )
    reg = _linea(empleado_ide=77, recurso_ide=501, empleado_reside=999)
    assert worker_key_for_registro(reg) == "rec-501"


def test_f050_r1_sin_recurso_ide_usa_empleado_reside() -> None:
    from infrastructure.database.parte_repository import (
        worker_key_for_registro,
    )
    reg = _linea(empleado_ide=77, empleado_reside=999)
    assert worker_key_for_registro(reg) == "rec-999"
    manual = _linea(empleado_reside=998,
                    empleado_match_method="recurso_manual")
    assert worker_key_for_registro(manual) == "rec-998"


def test_f050_r1_ficha_sin_recurso_da_emp() -> None:
    """E12: ficha sin `recurso_ide` ni `empleado_reside` se queda en
    `emp-` (transitorio hasta que el conciliador de sv3 le pone recurso)."""
    from infrastructure.database.parte_repository import (
        worker_key_for_registro,
    )
    reg = _linea(empleado_ide=77, trabajador_nombre_leido="Persona Sintetica")
    assert worker_key_for_registro(reg) == "emp-77"


def test_f050_r1_sin_casar_con_leido_da_nom() -> None:
    from infrastructure.database.parte_repository import (
        worker_key_for_registro,
    )
    reg = _linea(trabajador_nombre_leido="  Pépe   Pérez ")
    assert worker_key_for_registro(reg) == "nom-PEPE_PEREZ"


def test_f050_r1_nada_da_sin_trabajador() -> None:
    from infrastructure.database.parte_repository import (
        worker_key_for_registro,
    )
    assert worker_key_for_registro(_linea()) == "sin-trabajador"
    assert worker_key_for_registro(
        _linea(trabajador_nombre_leido="   ")) == "sin-trabajador"


def test_f050_r1_funcion_pura_cada_rama() -> None:
    """`_clave_trabajador` es la regla; `worker_key_for_registro` delega."""
    from infrastructure.database.parte_repository import _clave_trabajador
    assert _clave_trabajador(casada=True, empleado_ide=7, recurso=5,
                             nombre_leido="X") == "rec-5"
    assert _clave_trabajador(casada=True, empleado_ide=7, recurso=None,
                             nombre_leido="X") == "emp-7"
    assert _clave_trabajador(casada=True, empleado_ide=None, recurso=None,
                             nombre_leido="Ana Sol") == "nom-ANA_SOL"
    assert _clave_trabajador(casada=False, empleado_ide=None, recurso=5,
                             nombre_leido="Ana Sol") == "nom-ANA_SOL"
    assert _clave_trabajador(casada=False, empleado_ide=None, recurso=5,
                             nombre_leido=None) == "sin-trabajador"
    # Ficha 0 y recurso 0 son valores, no ausencias.
    assert _clave_trabajador(casada=True, empleado_ide=0, recurso=None,
                             nombre_leido=None) == "emp-0"
    assert _clave_trabajador(casada=True, empleado_ide=None, recurso=0,
                             nombre_leido=None) == "rec-0"


# ===================================================================== #
# R2 · sin casar nunca es rec-
# ===================================================================== #

@pytest.mark.parametrize("metodo", [None, "nombre_sin_dni", "sin_match",
                                    "otro_metodo"])
def test_f050_r2_no_casada_con_recurso_no_da_rec(metodo) -> None:
    from infrastructure.database.parte_repository import (
        worker_key_for_registro,
    )
    reg = _linea(empleado_reside=6001, recurso_ide=6001,
                 empleado_match_method=metodo,
                 trabajador_nombre_leido="Ana Sol")
    assert worker_key_for_registro(reg) == "nom-ANA_SOL"
    reg2 = _linea(empleado_reside=6001, empleado_match_method=metodo)
    assert worker_key_for_registro(reg2) == "sin-trabajador"


# ===================================================================== #
# R3 · las no casadas, como antes
# ===================================================================== #

LEIDOS = [None, "", "   ", "Pepe Perez", "PEPE  PÉREZ", "pepe pérez",
          "José María Ñúñez", "  a  b  c ", "Ana-Sol O'Neil", "ÇÀÉ ü"]


@pytest.mark.parametrize("leido", LEIDOS)
@pytest.mark.parametrize("reside,recurso,metodo", [
    (None, None, None),
    (6001, None, None),
    (None, 6001, "nombre_sin_dni"),
    (6001, 6001, "sin_match"),
])
def test_f050_r3_no_casadas_igual_que_antes(leido, reside, recurso,
                                            metodo) -> None:
    from infrastructure.database.parte_repository import (
        worker_key_for_registro,
    )
    reg = _linea(trabajador_nombre_leido=leido, empleado_reside=reside,
                 recurso_ide=recurso, empleado_match_method=metodo)
    assert worker_key_for_registro(reg) == _clave_antes(reg)


# ===================================================================== #
# R11 · persona_de
# ===================================================================== #

def test_f050_r11_persona_de_con_dni_no_cambia() -> None:
    from infrastructure.database.parte_repository import persona_de
    reg = _linea(empleado_ide=77, recurso_ide=501,
                 empleado_dni=" 1234-5678 z ")
    assert persona_de(reg) == "dni:12345678Z"


def test_f050_r11_persona_de_sin_dni_es_la_clave_nueva() -> None:
    from infrastructure.database.parte_repository import persona_de
    assert persona_de(_linea(empleado_ide=77, recurso_ide=501)) == "rec-501"
    assert persona_de(_linea(empleado_ide=77)) == "emp-77"
    assert persona_de(
        _linea(trabajador_nombre_leido="Ana Sol")) == "nom-ANA_SOL"


def test_f050_r11_persona_de_sin_codigo_propio() -> None:
    """`persona_de` no cambia de codigo: sigue delegando sin DNI."""
    from infrastructure.database import parte_repository
    fuente = inspect.getsource(parte_repository.persona_de)
    assert "return worker_key_for_registro(reg)" in fuente
