# tests/test_f021_cuenta_analitica.py
"""F-021 · R1-R8: de donde sale la cuenta analitica de una linea (pura).

La «cuenta analitica del recurso» es la de su ficha por tipo de hora
(`reshor.caaide`), una plantilla del centro `00000`. Lo que se escribe en
`hmores.caaide` es la cuenta del CENTRO DE LA OBRA con esa misma
SUBCUENTA (el texto tras el primer punto del codigo). Sin subcuenta, o si
la obra no la tiene, la linea va con `caaide = 0` (R8).

Datos SINTETICOS: codigos de centro y subcuentas inventados.
"""
from __future__ import annotations

import dataclasses

import pytest

from application.services.cuenta_analitica import (
    MOTIVO_CUENTA_AMBIGUA,
    MOTIVO_OBRA_SIN_CUENTA,
    MOTIVO_RECURSO_SIN_CUENTA,
    CuentaLinea,
    indexar_cuentas,
    resolver_cuenta,
    subcuenta,
    subcuenta_de_linea,
)
from domain.models.registro_models import HoraRecurso

HL, HE, CI, OTRA = 11, 12, 13, 14


def _h(horide, caa_cod=None, *, defecto=False, cod="HL01") -> HoraRecurso:
    return HoraRecurso(horide=horide, cod=cod, res=None, pre=10.0,
                       caa_cod=caa_cod, defecto=defecto)


# ============================== subcuenta ============================== #

@pytest.mark.parametrize("cod, esperado", [
    ("00000.CIMO09", "CIMO09"),          # forma normal <centro>.<subcuenta>
    ("0404.CIMO09", "CIMO09"),
    ("  00000 .  CIMO09  ", "CIMO09"),   # espacios a los lados: fuera
    ("00000.A.B", "A.B"),                # varios puntos: tras el PRIMERO
    ("00000..B", ".B"),
    (".X", "X"),                         # centro vacio: la subcuenta vale
    ("SINPUNTO", None),                  # sin punto: no tiene
    ("00000.", None),                    # vacia tras el punto
    ("00000.   ", None),
    ("", None),
    ("   ", None),
    (None, None),
])
def test_f021_r1_subcuenta_del_codigo(cod, esperado) -> None:
    assert subcuenta(cod) == esperado


# ======================== R1-R2 · subcuenta_de_linea ======================== #

def test_f021_r1_la_del_tipo_de_hora_que_se_escribe() -> None:
    horas = [_h(HL, "00000.LAB", defecto=True), _h(HE, "00000.EXT")]
    assert subcuenta_de_linea(horas, HE) == "EXT"
    assert subcuenta_de_linea(horas, HL) == "LAB"


def test_f021_r1_manda_el_tipo_escrito_aunque_el_defecto_tenga_otra() -> None:
    horas = [_h(HE, "00000.EXT"), _h(HL, "00000.LAB", defecto=True)]
    assert subcuenta_de_linea(horas, HE) == "EXT"


def test_f021_r2_sin_plantilla_del_tipo_va_la_del_tipo_por_defecto() -> None:
    """Las incidencias CI* no llevan cuenta en reshor: van con la de la
    hora por defecto del recurso (como hace el humano, §3)."""
    horas = [_h(HL, "00000.LAB", defecto=True), _h(CI, None, cod="CIV")]
    assert subcuenta_de_linea(horas, CI) == "LAB"


@pytest.mark.parametrize("cod_tipo", ["SINPUNTO", "00000.", "", "  "])
def test_f021_r2_plantilla_sin_subcuenta_tambien_cae_al_defecto(
        cod_tipo) -> None:
    horas = [_h(CI, cod_tipo, cod="CIV"), _h(HL, "00000.LAB", defecto=True)]
    assert subcuenta_de_linea(horas, CI) == "LAB"


def test_f021_r2_tipo_que_no_esta_en_la_ficha_cae_al_defecto() -> None:
    horas = [_h(HL, "00000.LAB", defecto=True)]
    assert subcuenta_de_linea(horas, 999) == "LAB"
    assert subcuenta_de_linea(horas, None) == "LAB"


def test_f021_r2_defecto_sin_subcuenta_salta_al_siguiente_defecto() -> None:
    """Defensivo: si hubiera dos filas marcadas por defecto, vale la que
    tenga subcuenta."""
    horas = [_h(HL, None, defecto=True), _h(HE, "00000.EXT", defecto=True)]
    assert subcuenta_de_linea(horas, CI) == "EXT"


def test_f021_r3_ni_tipo_ni_defecto_dan_subcuenta() -> None:
    horas = [_h(HL, None, defecto=True), _h(CI, None, cod="CIV")]
    assert subcuenta_de_linea(horas, CI) is None
    assert subcuenta_de_linea([], CI) is None


def test_f021_r7_otra_fila_con_cuenta_no_interviene() -> None:
    """Una fila de OTRO tipo de hora que no es el defecto no aporta nada,
    aunque tenga cuenta (no se «hereda» la de otra hora)."""
    horas = [_h(OTRA, "00000.OTRA"), _h(HL, None, defecto=True),
             _h(CI, None, cod="CIV")]
    assert subcuenta_de_linea(horas, CI) is None
    assert subcuenta_de_linea(horas, HL) is None


# ============================ indexar_cuentas ============================ #

def test_f021_r4_indexar_agrupa_por_subcuenta() -> None:
    filas = [(701, "0404.LAB"), (702, "0404.EXT"), (703, " 0404 .LAB "),
             (704, "SINPUNTO"), (705, "0404."), (706, None)]
    assert indexar_cuentas(filas) == {
        "LAB": [(701, "0404.LAB"), (703, "0404 .LAB")],
        "EXT": [(702, "0404.EXT")],
    }


def test_f021_r4_indexar_convierte_el_ide_a_entero() -> None:
    (cuenta,) = indexar_cuentas([("701", "0404.LAB")])["LAB"]
    assert cuenta == (701, "0404.LAB")
    assert isinstance(cuenta[0], int)


def test_f021_r4_indexar_sin_filas() -> None:
    assert indexar_cuentas([]) == {}


# ============================ resolver_cuenta ============================ #

CUENTAS = {"LAB": [(701, "0404.LAB")], "EXT": [(702, "0404.EXT")],
           "DOS": [(703, "0404.DOS"), (704, "0404. DOS")]}


def test_f021_r4_la_cuenta_del_centro_con_esa_subcuenta() -> None:
    assert resolver_cuenta("LAB", CUENTAS, "0404") == \
        CuentaLinea(caa_ide=701, caa_cod="0404.LAB", motivo=None, aviso=None)
    assert resolver_cuenta("EXT", CUENTAS, "0404").caa_ide == 702


def test_f021_r3_sin_subcuenta_va_sin_cuenta_y_sin_aviso() -> None:
    assert resolver_cuenta(None, CUENTAS, "0404") == CuentaLinea(
        caa_ide=0, caa_cod=None, motivo=MOTIVO_RECURSO_SIN_CUENTA,
        aviso=None)


def test_f021_r5_la_obra_no_tiene_esa_subcuenta() -> None:
    c = resolver_cuenta("NOHAY", CUENTAS, "0404")
    assert (c.caa_ide, c.caa_cod, c.motivo) == \
        (0, None, MOTIVO_OBRA_SIN_CUENTA)
    assert c.aviso == ("la obra 0404 no tiene la cuenta analitica .NOHAY: "
                       "la linea ira sin cuenta")


def test_f021_r5_obra_sin_centro_es_indice_vacio() -> None:
    c = resolver_cuenta("LAB", {}, "0404")
    assert (c.caa_ide, c.motivo) == (0, MOTIVO_OBRA_SIN_CUENTA)
    assert "0404" in c.aviso and ".LAB" in c.aviso


def test_f021_r6_varias_candidatas_no_se_elige_ninguna() -> None:
    c = resolver_cuenta("DOS", CUENTAS, "0404")
    assert (c.caa_ide, c.caa_cod, c.motivo) == \
        (0, None, MOTIVO_CUENTA_AMBIGUA)
    assert c.aviso == ("la obra 0404 tiene varias cuentas .DOS: la linea "
                       "ira sin cuenta")


def test_f021_r8_toda_linea_sin_cuenta_lleva_caa_ide_cero() -> None:
    """La falta de cuenta nunca es un None que rompa el INSERT."""
    for sub, cuentas in ((None, CUENTAS), ("NOHAY", CUENTAS),
                         ("DOS", CUENTAS), ("LAB", {})):
        c = resolver_cuenta(sub, cuentas, "0404")
        assert c.caa_ide == 0 and c.caa_cod is None


def test_f021_r4_motivos_distintos_y_estables() -> None:
    """Los motivos son el contrato con el log (R18) y el portal."""
    assert (MOTIVO_RECURSO_SIN_CUENTA, MOTIVO_OBRA_SIN_CUENTA,
            MOTIVO_CUENTA_AMBIGUA) == (
        "recurso_sin_cuenta", "obra_sin_cuenta", "cuenta_ambigua")


def test_f021_r4_cuenta_linea_es_inmutable() -> None:
    c = resolver_cuenta("LAB", CUENTAS, "0404")
    with pytest.raises(dataclasses.FrozenInstanceError):
        c.caa_ide = 1  # type: ignore[misc]
