# tests/test_f032_festivos_guardados_gemelos.py
"""Guardián de los dos `festivos_guardados.py` (F-032, R42, DA20).

La cascada de lectura de los festivos de cada trabajador (fila del DNI ⇒
fuente `sesame`; sin fila o sin DNI ⇒ `sin_fila` y el respaldo de cada
servicio) y el formato de `festivos_json` viven DUPLICADOS a propósito en
sv3 (cómputo de extras) y sv4 (portal), en la lista cerrada de `CLAUDE.md`.
Si divergieran, el portal enseñaría como festivo un día que sv3 paga como
laborable, o al revés.

Como el de `jornada_resolver` (F-015, R19), compara API pública y
comportamiento: mismas funciones, mismas firmas y mismos resultados sobre
una tabla de casos. Sin red ni BBDD: los módulos son puros y se cargan
por ruta.
"""
from __future__ import annotations

import importlib.util
import inspect
import sys
from dataclasses import fields, is_dataclass
from pathlib import Path
from types import ModuleType

import pytest

RAIZ = Path(__file__).resolve().parents[1]
RUTA_SV3 = (RAIZ / "services/partes-persistencia/application/services/"
            "festivos_guardados.py")
RUTA_SV4 = (RAIZ / "services/partes-front/application/services/"
            "festivos_guardados.py")

FUNCIONES: tuple[str, ...] = ("del_ano", "a_json", "fila_de", "elegir")
CONSTANTES: tuple[str, ...] = ("FUENTE_SESAME", "FUENTE_SIN_FILA")


def _cargar(ruta: Path, nombre: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    assert spec is not None and spec.loader is not None, f"no se pudo cargar {ruta}"
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


SV3 = _cargar(RUTA_SV3, "festivos_guardados_sv3")
SV4 = _cargar(RUTA_SV4, "festivos_guardados_sv4")


def _firma(modulo: ModuleType, nombre: str) -> str:
    return str(inspect.signature(getattr(modulo, nombre))).replace(
        modulo.__name__ + ".", "<modulo>.")


def _publico(modulo: ModuleType) -> set[str]:
    return {
        n for n, v in vars(modulo).items()
        if not n.startswith("_")
        and (inspect.isfunction(v) or inspect.isclass(v))
        and getattr(v, "__module__", None) == modulo.__name__
    }


# ------------------------------ API pública ----------------------------- #

@pytest.mark.parametrize("nombre", FUNCIONES)
def test_f032_r42_las_dos_copias_declaran_la_funcion_con_la_misma_firma(nombre):
    assert hasattr(SV3, nombre) and hasattr(SV4, nombre), nombre
    assert _firma(SV3, nombre) == _firma(SV4, nombre)


@pytest.mark.parametrize("nombre", CONSTANTES)
def test_f032_r42_mismas_constantes_de_fuente(nombre):
    assert getattr(SV3, nombre) == getattr(SV4, nombre)


def test_f032_r42_misma_dataclase_fila():
    c3, c4 = SV3.FilaFestivos, SV4.FilaFestivos
    assert is_dataclass(c3) and is_dataclass(c4)
    assert [(f.name, str(f.type)) for f in fields(c3)] == [
        (f.name, str(f.type)) for f in fields(c4)]


def test_f032_r42_ninguna_copia_expone_algo_que_la_otra_no():
    assert _publico(SV3) == _publico(SV4)


# ------------------------ tabla de comportamiento ----------------------- #

#: (id, función, argumentos). Las filas se construyen con la clase de cada
#: copia dentro del test.
PARES = (
    ("2026-01-01", "Año Nuevo"), ("2025-12-25", "Navidad"),
    ("2026-02-30", "imposible"), ("basura", None), (None, "x"),
    ("2026-05-01T00:00:00", " Trabajo "), ("2026-08-15", None),
    ("2026-08-16", "  "),
)

CASOS_DEL_ANO = (
    ("mezcla_2026", PARES, 2026),
    ("mezcla_2025", PARES, 2025),
    ("vacio", (), 2026),
)

CASOS_JSON = (
    ("ordena", {"2026-12-08": "Inmaculada", "2026-01-06": None}),
    ("vacio", {}),
    ("tildes", {"2026-03-19": "San José"}),
)

CASOS_FILA_DE = (
    ("buena", ("X1", 2026, '{"2026-03-19": "San Jose", "2026-01-06": null}', "t")),
    ("vacia", ("X1", 2026, "{}", "t")),
    ("no_json", ("X1", 2026, "no", "t")),
    ("lista", ("X1", 2026, "[]", "t")),
    ("otro_ano", ("X1", 2026, '{"2025-12-25": "Navidad"}', "t")),
    ("nombre_no_texto", ("X1", 2026, '{"2026-01-01": 7}', "t")),
    ("sin_dni", ("", 2026, "{}", "t")),
    ("ano_cero", ("X1", 0, "{}", "t")),
)


def _resultado(funcion, *args):
    try:
        return ("ok", funcion(*args))
    except ValueError:
        return ("ValueError", None)


@pytest.mark.parametrize("caso", CASOS_DEL_ANO, ids=[c[0] for c in CASOS_DEL_ANO])
def test_f032_r42_del_ano_igual(caso):
    _, pares, ano = caso
    assert SV3.del_ano(pares, ano) == SV4.del_ano(pares, ano)


@pytest.mark.parametrize("caso", CASOS_JSON, ids=[c[0] for c in CASOS_JSON])
def test_f032_r42_a_json_igual(caso):
    assert SV3.a_json(caso[1]) == SV4.a_json(caso[1])


@pytest.mark.parametrize("caso", CASOS_FILA_DE, ids=[c[0] for c in CASOS_FILA_DE])
def test_f032_r42_fila_de_igual(caso):
    r3 = _resultado(SV3.fila_de, *caso[1])
    r4 = _resultado(SV4.fila_de, *caso[1])
    assert r3[0] == r4[0]
    if r3[0] == "ok":
        f3, f4 = r3[1], r4[1]
        assert (f3.dni_norm, f3.ano, dict(f3.festivos), f3.leido_en_utc) == (
            f4.dni_norm, f4.ano, dict(f4.festivos), f4.leido_en_utc)


@pytest.mark.parametrize("dni,hay_fila", [
    ("X1", True), ("X1", False), ("", True), (None, True)])
def test_f032_r42_elegir_misma_fuente_y_festivos(dni, hay_fila):
    """La fuente y los festivos elegidos son los mismos en las dos copias."""
    def _con(modulo):
        fila = modulo.FilaFestivos(dni_norm="X1", ano=2026,
                                   festivos={"2026-03-19": "San Jose"},
                                   leido_en_utc="t")
        llamadas = []

        def leer(d, a):
            llamadas.append((d, a))
            return fila if hay_fila else None

        elegida, fuente = modulo.elegir(dni, 2026, leer)
        return (fuente, None if elegida is None else dict(elegida.festivos),
                llamadas)

    assert _con(SV3) == _con(SV4)


# --------------------------- el guardián muerde ------------------------- #

def test_f032_r42_el_guardian_caza_una_copia_alterada(tmp_path):
    """Una copia con la cascada cambiada (sin fila ⇒ `sesame`) da otra
    fuente: la tabla de casos lo detecta."""
    fuente = RUTA_SV4.read_text(encoding="utf-8")
    alterada = fuente.replace("return None, FUENTE_SIN_FILA",
                              "return None, FUENTE_SESAME")
    assert alterada != fuente, "el punto de alteración ya no existe"
    ruta = tmp_path / "festivos_guardados.py"
    ruta.write_text(alterada, encoding="utf-8")
    mala = _cargar(ruta, "festivos_guardados_alterada")
    assert mala.elegir("X1", 2026, lambda d, a: None) != SV3.elegir(
        "X1", 2026, lambda d, a: None)
