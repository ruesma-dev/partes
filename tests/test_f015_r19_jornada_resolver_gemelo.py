# tests/test_f015_r19_jornada_resolver_gemelo.py
"""Guardián de los dos `jornada_resolver.py` (F-015, R19).

La regla de la jornada del día vive DUPLICADA a propósito en sv3
(`partes-persistencia`) y sv4 (`partes-front`): `docs/ARCHITECTURE.md`
prohíbe la librería compartida y los servicios solo se acoplan por
mensajes, HTTP y la BBDD. La duplicación viene de F-003, que ya comparaba
`jornada_efectiva` entre ambas copias; F-015 la amplía y necesita un
guardián a la altura, porque ahora lo duplicado no son diez líneas sino
la regla que decide cuántas horas de cada día son extra.

A diferencia del guardián de `orm_models.py` (F-010, byte a byte), aquí
se compara **API pública y comportamiento**, no bytes: cada copia tiene
su propio docstring, que explica a SUS llamantes (D6 del diseño). Si un
día divergen en comportamiento, el portal avisaría de jornadas
incompletas que sv3 no genera, o al revés.

Sin red, sin BBDD: los dos módulos son funciones puras y se cargan por
ruta como módulos independientes.
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
from dataclasses import fields, is_dataclass
from datetime import date, timedelta
from pathlib import Path
from types import ModuleType

import pytest

#: Raíz del repositorio: este fichero es `<raíz>/tests/test_f015_...py`.
RAIZ = Path(__file__).resolve().parents[1]

RUTA_SV3 = (
    RAIZ / "services/partes-persistencia/application/services/jornada_resolver.py"
)
RUTA_SV4 = (
    RAIZ / "services/partes-front/application/services/jornada_resolver.py"
)

#: Funciones que las DOS copias tienen que exponer con la misma firma.
FUNCIONES: tuple[str, ...] = (
    "candef_valido",
    "jornada_efectiva",
    "parsear_mapa_semanal",
    "jornada_semanal_de",
    "es_ultimo_laborable",
    "detalle_jornada_dia",
    "jornada_dia",
)

#: Dataclases que las dos copias tienen que declarar igual.
DATACLASES: tuple[str, ...] = ("Excepcion", "DetalleJornada")


def _cargar(ruta: Path, nombre: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    assert spec is not None and spec.loader is not None, f"no se pudo cargar {ruta}"
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


SV3 = _cargar(RUTA_SV3, "jornada_resolver_sv3")
SV4 = _cargar(RUTA_SV4, "jornada_resolver_sv4")


# ---------------------------- API pública ------------------------------- #


@pytest.mark.parametrize("nombre", FUNCIONES)
def test_f015_r19_las_dos_copias_declaran_la_misma_funcion(nombre: str) -> None:
    for etiqueta, modulo in (("sv3", SV3), ("sv4", SV4)):
        assert hasattr(modulo, nombre), (
            f"{etiqueta} no declara `{nombre}`: las dos copias del resolutor "
            f"tienen que exponer la misma API pública (CLAUDE.md, LÍMITE DE "
            f"SERVICIO)"
        )


def _firma(modulo: ModuleType, nombre: str) -> str:
    """Firma en texto, con el nombre del módulo neutralizado.

    Los dos resolutores se cargan con nombres de módulo distintos, así que
    una anotación a una clase propia (`Excepcion`, `DetalleJornada`) sale
    cualificada con ese nombre y las firmas nunca serían iguales tal cual.
    """
    return str(inspect.signature(getattr(modulo, nombre))).replace(
        modulo.__name__ + ".", "<resolutor>."
    )


@pytest.mark.parametrize("nombre", FUNCIONES)
def test_f015_r19_las_firmas_son_identicas(nombre: str) -> None:
    firma_sv3 = _firma(SV3, nombre)
    firma_sv4 = _firma(SV4, nombre)
    assert firma_sv3 == firma_sv4, (
        f"`{nombre}` tiene firmas distintas:\n  sv3: {firma_sv3}\n"
        f"  sv4: {firma_sv4}"
    )


@pytest.mark.parametrize("nombre", DATACLASES)
def test_f015_r19_las_dataclases_declaran_los_mismos_campos(nombre: str) -> None:
    clase_sv3 = getattr(SV3, nombre)
    clase_sv4 = getattr(SV4, nombre)
    assert is_dataclass(clase_sv3) and is_dataclass(clase_sv4)
    huella_sv3 = [(f.name, str(f.type)) for f in fields(clase_sv3)]
    huella_sv4 = [(f.name, str(f.type)) for f in fields(clase_sv4)]
    assert huella_sv3 == huella_sv4, (
        f"`{nombre}` declara campos distintos:\n  sv3: {huella_sv3}\n"
        f"  sv4: {huella_sv4}"
    )


def test_f015_r19_ninguna_copia_expone_algo_que_la_otra_no() -> None:
    """Nada público de más en una copia: sería regla que solo aplica a medias."""
    def _publico(modulo: ModuleType) -> set[str]:
        return {
            n for n, v in vars(modulo).items()
            if not n.startswith("_")
            and (inspect.isfunction(v) or inspect.isclass(v))
            and getattr(v, "__module__", None) == modulo.__name__
        }

    assert _publico(SV3) == _publico(SV4)


# ------------------------- tabla de comportamiento ---------------------- #

LUNES = date(2026, 3, 16)
MARTES = date(2026, 3, 17)
MIERCOLES = date(2026, 3, 18)
JUEVES = date(2026, 3, 19)
VIERNES = date(2026, 3, 20)
SABADO = date(2026, 3, 21)
DOMINGO = date(2026, 3, 22)

MAPA = {8.0: 40.0, 9.0: 42.0}

VIERNES_FESTIVO = {"2026-03-20"}
MIERCOLES_FESTIVO = {"2026-03-18"}
JUEVES_Y_VIERNES = {"2026-03-19", "2026-03-20"}
SEMANA_FESTIVA = {
    "2026-03-16", "2026-03-17", "2026-03-18", "2026-03-19", "2026-03-20",
}


def _es_laborable(no_laborables=(), *, finde_laborable: bool = False):
    fuera = set(no_laborables)

    def _f(d: date) -> bool:
        if not finde_laborable and d.weekday() >= 5:
            return False
        return d.isoformat() not in fuera

    return _f


#: (id, fecha, candef, mapa, no laborables, excepción-como-kwargs o None).
#: Cubre R13 (reparto y bordes), R14 (findes y semana festiva) y R16
#: (excepciones con `S` y con patrón). Son 26 casos.
CASOS: tuple[tuple, ...] = (
    ("c9_lunes", LUNES, 9.0, MAPA, (), None),
    ("c9_martes", MARTES, 9.0, MAPA, (), None),
    ("c9_miercoles", MIERCOLES, 9.0, MAPA, (), None),
    ("c9_jueves", JUEVES, 9.0, MAPA, (), None),
    ("c9_viernes", VIERNES, 9.0, MAPA, (), None),
    ("c9_sabado", SABADO, 9.0, MAPA, (), None),
    ("c9_domingo", DOMINGO, 9.0, MAPA, (), None),
    ("c9_viernes_festivo", VIERNES, 9.0, MAPA, VIERNES_FESTIVO, None),
    ("c9_jueves_con_viernes_festivo", JUEVES, 9.0, MAPA, VIERNES_FESTIVO, None),
    ("c9_miercoles_festivo", MIERCOLES, 9.0, MAPA, MIERCOLES_FESTIVO, None),
    ("c9_viernes_con_miercoles_festivo", VIERNES, 9.0, MAPA,
     MIERCOLES_FESTIVO, None),
    ("c9_miercoles_con_jue_y_vie_festivos", MIERCOLES, 9.0, MAPA,
     JUEVES_Y_VIERNES, None),
    ("c9_semana_festiva", MIERCOLES, 9.0, MAPA, SEMANA_FESTIVA, None),
    ("c8_lunes", LUNES, 8.0, MAPA, (), None),
    ("c8_viernes", VIERNES, 8.0, MAPA, (), None),
    ("c8_jueves_con_viernes_festivo", JUEVES, 8.0, MAPA, VIERNES_FESTIVO, None),
    ("candef_invalido_cero", VIERNES, 0.0, MAPA, (), None),
    ("candef_invalido_none", VIERNES, None, MAPA, (), None),
    ("candef_invalido_texto", VIERNES, "ocho", MAPA, (), None),
    ("c10_fuera_del_mapa", VIERNES, 10.0, MAPA, (), None),
    ("c9_mapa_corto", VIERNES, 9.0, {9.0: 40.0}, (), None),
    ("c9_mapa_negativo", VIERNES, 9.0, {9.0: 30.0}, (), None),
    ("exc_semanal_48", VIERNES, 10.0, MAPA, (), {"semanal": 48.0}),
    ("exc_semanal_48_lunes", LUNES, 10.0, MAPA, (), {"semanal": 48.0}),
    ("exc_patron", MIERCOLES, 9.0, MAPA, (),
     {"patron": (7.0, 7.0, 7.0, 7.0, 7.0, 0.0, 0.0)}),
    ("exc_patron_festivo", MIERCOLES, 9.0, MAPA, MIERCOLES_FESTIVO,
     {"patron": (7.0, 7.0, 7.0, 7.0, 7.0, 0.0, 0.0)}),
    ("exc_invalida_se_ignora", VIERNES, 9.0, MAPA, (),
     {"patron": (7.0, 7.0)}),
)


@pytest.mark.parametrize(
    "caso, dia, candef, mapa, no_laborables, exc",
    CASOS,
    ids=[c[0] for c in CASOS],
)
def test_f015_r19_las_dos_copias_dan_el_mismo_detalle(
    caso, dia, candef, mapa, no_laborables, exc
) -> None:
    """Mismo detalle (horas, `S`, origen y último laborable) en las dos."""
    def _detalle(modulo):
        excepcion = None if exc is None else modulo.Excepcion(**exc)
        return modulo.detalle_jornada_dia(
            dia, candef=candef, minimo=2.0, por_defecto=8.0, mapa=mapa,
            es_laborable=_es_laborable(no_laborables), excepcion=excepcion,
        )

    detalle_sv3 = _detalle(SV3)
    detalle_sv4 = _detalle(SV4)
    assert (
        detalle_sv3.horas, detalle_sv3.candef_efectivo, detalle_sv3.semanal,
        detalle_sv3.origen, detalle_sv3.ultimo_laborable,
    ) == (
        detalle_sv4.horas, detalle_sv4.candef_efectivo, detalle_sv4.semanal,
        detalle_sv4.origen, detalle_sv4.ultimo_laborable,
    ), f"las dos copias discrepan en el caso '{caso}'"


def test_f015_r19_hay_al_menos_veinte_casos() -> None:
    """R19 pide una tabla de >= 20 casos: que no se vacíe con el tiempo."""
    assert len(CASOS) >= 20


def test_f015_r19_una_semana_entera_dia_a_dia_coincide() -> None:
    """Barrido: 3 semanas x 7 días x 3 candef, sin excepción."""
    inicio = date(2026, 3, 16)
    for delta in range(21):
        d = inicio + timedelta(days=delta)
        for candef in (8.0, 9.0, 10.0):
            es_lab = _es_laborable()
            assert SV3.jornada_dia(
                d, candef=candef, minimo=2.0, por_defecto=8.0, mapa=MAPA,
                es_laborable=es_lab,
            ) == SV4.jornada_dia(
                d, candef=candef, minimo=2.0, por_defecto=8.0, mapa=MAPA,
                es_laborable=es_lab,
            )


def test_f015_r19_sin_calendario_cableado_el_sabado_vale_el_candef() -> None:
    """D11/DA4: la situación de los tests que corren con `calendario=None`."""
    for modulo in (SV3, SV4):
        assert modulo.jornada_dia(
            SABADO, candef=9.0, minimo=2.0, por_defecto=8.0, mapa=MAPA,
            es_laborable=_es_laborable(finde_laborable=True),
        ) == 9.0


# --------------------------- el mapa y sus errores ---------------------- #

@pytest.mark.parametrize("texto", ["8:40,9:42", "9:42", "7.5:37.5"])
def test_f015_r19_el_parseo_del_mapa_coincide(texto: str) -> None:
    assert SV3.parsear_mapa_semanal(texto) == SV4.parsear_mapa_semanal(texto)


@pytest.mark.parametrize("texto", ["", "8:40,9", "x:40", "8:40,8:41", "8:0"])
def test_f015_r19_las_dos_copias_rechazan_los_mismos_mapas(texto: str) -> None:
    for modulo in (SV3, SV4):
        with pytest.raises(ValueError):
            modulo.parsear_mapa_semanal(texto)


def test_f015_r19_jornada_efectiva_sigue_siendo_gemela() -> None:
    """La propiedad de F-003, intacta: F-015 se construye ENCIMA."""
    for c in (None, "", 0.0, 1.0, 2.0, 2.5, 7.5, 8.0, 12.0, "x", "7.5"):
        assert (SV3.jornada_efectiva(c, minimo=2.0, por_defecto=8.0)
                == SV4.jornada_efectiva(c, minimo=2.0, por_defecto=8.0))
        assert (SV3.candef_valido(c, minimo=2.0)
                == SV4.candef_valido(c, minimo=2.0))


# ------------------------- el guardián muerde --------------------------- #

def test_f015_r19_el_guardian_detecta_una_copia_alterada(tmp_path) -> None:
    """Sin esto, un guardián que compare siempre igual pasaría por bueno.

    Se altera una COPIA en `tmp_path` (el árbol real no se toca) cambiando
    el reparto del último laborable y se exige que la comparación lo cace.
    """
    original = RUTA_SV3.read_text(encoding="utf-8")
    alterada = original.replace(
        "    resto = max(0.0, semanal - 4.0 * c)",
        "    resto = max(0.0, semanal - 3.0 * c)",
        1,
    )
    assert alterada != original, (
        "la alteración no cambió nada: el fuente de referencia ha cambiado y "
        "el test estaría comprobando el vacío"
    )
    ruta = tmp_path / "resolutor_tocado.py"
    ruta.write_text(alterada, encoding="utf-8")
    tocado = _cargar(ruta, "jornada_resolver_tocado")

    intacto = SV4.jornada_dia(
        VIERNES, candef=9.0, minimo=2.0, por_defecto=8.0, mapa=MAPA,
        es_laborable=_es_laborable())
    roto = tocado.jornada_dia(
        VIERNES, candef=9.0, minimo=2.0, por_defecto=8.0, mapa=MAPA,
        es_laborable=_es_laborable())
    assert intacto != roto


def test_f015_r19_el_arbol_real_no_se_toca(tmp_path) -> None:
    antes = {r: r.read_bytes() for r in (RUTA_SV3, RUTA_SV4)}
    (tmp_path / "copia.py").write_text(
        RUTA_SV3.read_text(encoding="utf-8"), encoding="utf-8")
    assert {r: r.read_bytes() for r in (RUTA_SV3, RUTA_SV4)} == antes
