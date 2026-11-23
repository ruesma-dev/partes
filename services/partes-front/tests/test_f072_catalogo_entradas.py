# tests/test_f072_catalogo_entradas.py
"""F-072 · R25: el catálogo de entradas de las obras agrupadas en sv4.

Por empresa: con UNA obra VAR, sus partidas del universo VAR (hoja activa,
número inicial ≥ `VAR_PARTIDA_DESDE`); con UNA obra de postventa, cada obra
no agrupada de la empresa que case con una hoja suya (R4-R6, por índice); con
varias o ninguna, nada. Caché con TTL; un fallo de lectura deja `[]` con
WARNING. Apagado, ni se lee.

Sin red: catálogo de obras y Sigrid en memoria. Datos FICTICIOS.
"""
from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from application.services.catalogo_entradas import CatalogoEntradas, Entrada
from application.services.obras_agrupadas import ajustes_de, casar_postventa
from application.services.partida_catalog import build_arbol_partidas
from infrastructure.sigrid.sigrid_lookup_client import ObraOption

LOGGER = "application.services.catalogo_entradas"
AJUSTES = ajustes_de(postventa_cod="POSTV2", var_cod="VAR", var_desde="29")
APAGADO = ajustes_de(postventa_cod=None, var_cod=None, var_desde=None)

O578 = ObraOption(578, "0578", "RESIDENCIAL 578", 1)
O654 = ObraOption(654, "0654", "NAVE 654", 1)
O656 = ObraOption(656, "0656", "SIN POSTVENTA", 1)
O100 = ObraOption(100, "0100", "OBRA CIEN", 1)
O400 = ObraOption(400, "0400", "OBRA DE PORSAN", 28)
PV1 = ObraOption(9001, "POSTV2", "POSTVENTA", 1)
PV28 = ObraOption(9028, "POSTV2", "POSTVENTA PORSAN", 28)
VAR1 = ObraOption(9101, "VAR", "OBRAS VARIAS", 1)
VAR28 = ObraOption(9128, "VAR", "OBRAS VARIAS PORSAN", 28)
OBRAS = [O578, O654, O656, O100, O400, PV1, PV28, VAR1, VAR28]


def _p(ide, cod, res, padide=None, tipdes=0):
    return SimpleNamespace(ide=ide, padide=padide, cod=cod, res=res, tex=None,
                           tipdes=tipdes, cosindide=None, unimed=None)


PRESUPUESTOS = {
    9001: [_p(90010, "CD", "COSTES DIRECTOS"),
           _p(90011, "0578B", "RESIDENCIAL 578", 90010),
           _p(90012, "0654-B", "NAVE 654", 90010),
           _p(90013, "0100", "OBRA CIEN", 90010),
           _p(90014, "0656", "DE BAJA", 90010, tipdes=1)],
    9028: [_p(90281, "0400", "PORSAN 400")],
    9101: [_p(91010, "CD", "COSTES DIRECTOS"),
           _p(91011, "28", "VARIOS 28", 91010),
           _p(91012, "29", "VARIOS 29", 91010),
           _p(91013, "030", "VARIOS 30", 91010),
           _p(91014, "31", "VARIOS 31", 91010, tipdes=1),
           _p(91015, "32", "CAPITULO 32", 91010),
           _p(91016, "32.1", "VARIOS 32.1", 91015)],
    9128: [_p(91281, "29", "PORSAN VARIOS 29")],
}


class Obras:
    def __init__(self, obras=OBRAS, error=None):
        self.obras, self.error = list(obras), error
        self.enabled = True

    def list(self):
        if self.error:
            raise self.error
        return list(self.obras)


class Sigrid:
    def __init__(self, error=None):
        self.error = error
        self.lecturas: list[int] = []

    def fetch_partidas_obra(self, obra_ide):
        self.lecturas.append(obra_ide)
        if self.error:
            raise self.error
        return PRESUPUESTOS.get(obra_ide, [])


def _cat(obras=None, sigrid=None, ajustes=AJUSTES, ttl=600):
    sigrid = sigrid or Sigrid()
    return CatalogoEntradas(obra_catalog=obras or Obras(), sigrid_client=sigrid,
                            ajustes=ajustes, ttl_seconds=ttl), sigrid


def _codigos(entradas):
    return sorted((e.empresa, e.codigo, e.obra_ide, e.partida_ide)
                  for e in entradas)


def test_f072_r25_var_y_postventa_por_empresa():
    cat, _s = _cat()
    assert _codigos(cat.entradas()) == [
        (1, "Postv-0100", 9001, 90013), (1, "Postv-0578B", 9001, 90011),
        (1, "Postv-0654-B", 9001, 90012),
        (1, "VAR-030", 9101, 91013), (1, "VAR-29", 9101, 91012),
        (1, "VAR-32.1", 9101, 91016),
        (28, "Postv-0400", 9028, 90281), (28, "VAR-29", 9128, 91281)]


def test_f072_r25_la_entrada_trae_obra_partida_y_rotulo():
    cat, _s = _cat()
    assert cat.entrada(9101, 91012) == Entrada(
        tipo="var", obra_ide=9101, obra_codigo="VAR", obra_nombre="OBRAS VARIAS",
        empresa=1, partida_ide=91012, partida_cod="29", partida_res="VARIOS 29",
        partida_capitulo="CD", codigo="VAR-29", nombre="VARIOS 29")
    e = cat.entrada(9001, 90011)
    assert (e.tipo, e.codigo, e.nombre) == (
        "postventa", "Postv-0578B", "RESIDENCIAL 578")
    assert cat.entrada(9101, 91011) is None      # 28 < desde
    assert cat.entrada(9101, 91015) is None      # capítulo
    assert cat.entrada(9001, 91012) is None      # partida de otra obra
    assert cat.entrada(None, None) is None


@pytest.mark.parametrize("extra", [ObraOption(9102, "VAR", "OTRA VAR", 1),
                                   ObraOption(9002, "postv2", "OTRA PV", 1)])
def test_f072_r25_varias_obras_agrupadas_en_la_empresa_no_dan_entradas(
        extra, caplog):
    cat, _s = _cat(Obras(OBRAS + [extra]))
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        entradas = cat.entradas()
    tipo = "var" if extra.codigo == "VAR" else "postventa"
    assert not [e for e in entradas if e.empresa == 1 and e.tipo == tipo]
    assert [e for e in entradas if e.empresa == 28 and e.tipo == tipo]
    assert any("varias" in r.getMessage() for r in caplog.records)


def test_f072_r25_sin_obra_agrupada_en_la_empresa_no_hay_entradas():
    cat, _s = _cat(Obras([O578, O400, PV28, VAR28]))
    assert {e.empresa for e in cat.entradas()} == {28}


def test_f072_r25_las_agrupadas_no_son_obras_de_postventa():
    cat, _s = _cat()
    assert not [e for e in cat.entradas() if e.tipo == "postventa"
                and e.partida_cod in ("POSTV2", "VAR")]


def test_f072_r25_cache_con_ttl():
    cat, s = _cat()
    cat.entradas()
    cat.entradas()
    assert sorted(s.lecturas) == [9001, 9028, 9101, 9128]
    cat0, s0 = _cat(ttl=0)
    cat0.entradas()
    cat0.entradas()
    assert len(s0.lecturas) == 8


def test_f072_r25_fallo_de_lectura_deja_vacio_con_warning(caplog):
    s = Sigrid(error=RuntimeError("sigrid-api truncated"))
    cat, _s = _cat(sigrid=s)
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        assert cat.entradas() == []
    assert any("truncated" in r.getMessage() for r in caplog.records)
    s.error = None                       # el fallo no se cachea
    assert cat.entradas() != []
    cat2, _ = _cat(Obras(error=RuntimeError("caido")))
    assert cat2.entradas() == []


def test_f072_r3_apagado_ni_lee():
    cat, s = _cat(ajustes=APAGADO)
    assert cat.entradas() == [] and s.lecturas == []
    sin_sigrid = CatalogoEntradas(obra_catalog=Obras(), sigrid_client=None,
                                  ajustes=AJUSTES)
    assert sin_sigrid.entradas() == []


@pytest.mark.parametrize("codigo", ["0578", "578", "0654", "0100", "100",
                                    "0656", "0578B", "05", "", "CD"])
def test_f072_r25_el_indice_casa_como_casar_postventa(codigo):
    hojas = build_arbol_partidas(PRESUPUESTOS[9001])
    cat, _s = _cat()
    esperado = casar_postventa(hojas, codigo)
    got = cat._indice_postventa(hojas).casar(codigo)
    assert (got.ide if got else None) == (esperado.ide if esperado else None)


# ---------------- review 1: categoría del capítulo y desempate ---------------- #

class SigridCon(Sigrid):
    def __init__(self, presupuestos):
        super().__init__()
        self.presupuestos = presupuestos

    def fetch_partidas_obra(self, obra_ide):
        self.lecturas.append(obra_ide)
        return self.presupuestos.get(obra_ide, [])


def test_f072_r25_partida_capitulo_es_la_categoria_como_en_sv3():
    """`partida_capitulo` guarda la CATEGORÍA (CD/CI/CP/OTRO, `String(8)`),
    como sv3 en `_casar_entrada`; no el código del capítulo, que puede pasar
    de 8 caracteres (`CD.POSTVENTA`). Sin capítulo CD/CI/CP, `OTRO`."""
    pres = {
        9001: [_p(90010, "CD", "COSTES DIRECTOS"),
               _p(90020, "CD.POSTVENTA", "POSTVENTA", 90010),
               _p(90021, "0578B", "RESIDENCIAL 578", 90020)],
        9101: [_p(91020, "29", "VARIOS SIN PADRE")],
    }
    cat, _s = _cat(sigrid=SigridCon(pres))
    pv, var = cat.entrada(9001, 90021), cat.entrada(9101, 91020)
    assert (pv.partida_capitulo, var.partida_capitulo) == ("CD", "OTRO")
    assert all(len(e.partida_capitulo) <= 8 for e in cat.entradas())


def _hojas_con_ide(*hojas):
    """Hojas `(ide, cod, tipdes)` colgando de `CD` (ide 1)."""
    filas = [_p(1, "CD", "COSTES DIRECTOS")]
    filas += [_p(ide, cod, f"P {cod}", 1, tipdes) for ide, cod, tipdes in hojas]
    return build_arbol_partidas(filas)


@pytest.mark.parametrize("hojas, codigo", [
    # Los casos de `tests/test_f072_equivalencia_porcentajes.py` (P5).
    ([(2, "0578AB", 0), (3, "0578C", 0)], "0578"),          # mas_corto
    ([(2, "0578-C", 0), (3, "0578B", 0)], "0578"),          # menor_normalizado
    ([(2, "0578B", 0), (3, "0578C", 0)], "0578"),           # orden_inverso
    ([(3, "0578C", 0), (2, "0578B", 0)], "0578"),           # orden_inverso, filas al revés
    ([(2, "0578B1", 0)], "0578"),                           # letra_digito
    ([(2, "0578 B.", 0)], "0578"),                          # letra_punto
    ([(2, "0578", 1), (3, "0578B", 0)], "0578"),            # de_baja
    # Dos exactas: gana el menor ide, vengan en el orden que vengan.
    ([(5, "0578", 0), (3, "05-78", 0)], "0578"),
    ([(3, "05-78", 0), (5, "0578", 0)], "0578"),
    # Una hoja sin código no casa ni estorba.
    ([(2, None, 0), (3, "0578B", 0)], "0578"),
    ([(2, "", 0)], "0578"),
    # Encargo T28 del reviewer: una exacta y una «con letras» activas a la
    # vez (la exacta gana: mata `casar` con los `get` intercambiados) y dos
    # «con letras» que normalizan igual (gana el menor `ide`: mata `_orden`
    # sin `h.ide`).
    ([(2, "0578", 0), (3, "0578B", 0)], "0578"),
    ([(3, "0578B", 0), (2, "0578-B", 0)], "0578"),
], ids=["mas_corto", "menor_normalizado", "orden_inverso",
        "orden_inverso_filas", "letra_digito", "letra_punto", "de_baja",
        "exactas_ide", "exactas_ide_inverso", "sin_codigo", "codigo_vacio",
        "exacta_y_con_letras", "con_letras_mismo_normalizado"])
def test_f072_r25_el_indice_desempata_como_casar_postventa(hojas, codigo):
    nodos = _hojas_con_ide(*hojas)
    cat, _s = _cat()
    esperado = casar_postventa(nodos, codigo)
    got = cat._indice_postventa(nodos).casar(codigo)
    assert (got.ide if got else None) == (esperado.ide if esperado else None)
