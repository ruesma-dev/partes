# tests/test_f072_obras_agrupadas_gemelos.py
"""Guardián del gemelo `obras_agrupadas.py` (F-072, R11, DA4).

Las reglas puras de las obras agrupadas (casado de postventa, universo VAR y
lectura de la marca del «Nº OBRA») viven DUPLICADAS a propósito en sv2, sv3,
sv4 y sv5, en la lista cerrada de `CLAUDE.md`: no hay librería compartida ni
canal entre servicios. Si divergieran, sv3 casaría una entrada que sv5 omite
o el portal ofrecería una que la ingesta no reconoce.

La regla es la más estricta posible: las cuatro copias son **byte a byte
idénticas** (sin contar el final de línea, que git puede convertir). Y,
como cinturón, la misma tabla de casos da lo mismo cargando cada copia.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

RAIZ = Path(__file__).resolve().parents[1]
RELATIVA = "application/services/obras_agrupadas.py"
SERVICIOS = ("partes-api", "partes-persistencia", "partes-front",
             "partes-transfer")
RUTAS = {s: RAIZ / "services" / s / RELATIVA for s in SERVICIOS}


def _bytes(ruta: Path) -> bytes:
    """Contenido sin la conversión de fin de línea de git."""
    return ruta.read_bytes().replace(b"\r\n", b"\n")


def _cargar(ruta: Path, nombre: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    assert spec is not None and spec.loader is not None, ruta
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def _diferentes(rutas: dict[str, Path]) -> list[str]:
    base = _bytes(rutas["partes-persistencia"])
    return [s for s, r in rutas.items() if _bytes(r) != base]


def test_f072_r11_las_cuatro_copias_existen():
    for servicio, ruta in RUTAS.items():
        assert ruta.is_file(), f"falta el gemelo en {servicio}: {ruta}"


def test_f072_r11_las_cuatro_copias_son_byte_identicas():
    assert _diferentes(RUTAS) == [], (
        "obras_agrupadas.py ha divergido; quien toque una copia cambia "
        "TODAS (lista cerrada de CLAUDE.md)")


def test_f072_r11_el_guardian_caza_un_byte_cambiado(tmp_path):
    """Con un solo byte distinto en una copia, el guardián da rojo."""
    original = RUTAS["partes-transfer"].read_bytes()
    alterada = tmp_path / "obras_agrupadas.py"
    alterada.write_bytes(original.replace(b"POSTVENTA = ", b"POSTVENTA =  ", 1))
    assert alterada.read_bytes() != original
    rutas = dict(RUTAS, **{"partes-transfer": alterada})
    assert _diferentes(rutas) == ["partes-transfer"]


def test_f072_r11_misma_tabla_de_casos_en_las_cuatro():
    modulos = [_cargar(r, f"obras_agrupadas_{s.replace('-', '_')}")
               for s, r in RUTAS.items()]

    def _resultados(m):
        marcas = m.Marcas(postventa=("POSTV2", "POST"), var=("VAR", "V"))
        hojas = [SimpleNamespace(ide=i, cod=c, es_hoja=True, activa=True)
                 for i, c in enumerate(("0578B", "029", "30", "0654-B"), 1)]
        return (
            [m.leer_forma(x, marcas) and (m.leer_forma(x, marcas).tipo,
                                          m.leer_forma(x, marcas).resto)
             for x in ("V29", "29 V", "POST-578", "POSTV2", "V", "POSTE")],
            [getattr(m.casar_postventa(hojas, c), "ide", None)
             for c in ("0578", "0654", "0656")],
            [getattr(m.casar_var(hojas, c), "ide", None)
             for c in ("29", "30", "31")],
            [m.es_partida_var(h, 29) for h in hojas],
        )

    primero = _resultados(modulos[0])
    assert all(_resultados(m) == primero for m in modulos[1:])


@pytest.mark.parametrize("servicio", SERVICIOS)
def test_f072_r11_solo_biblioteca_estandar(servicio):
    """Sin `text_match` ni nada del servicio: sv5 no lo tiene (design §2)."""
    texto = RUTAS[servicio].read_text(encoding="utf-8")
    assert "from application" not in texto and "import application" not in texto
