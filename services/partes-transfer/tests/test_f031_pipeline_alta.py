# tests/test_f031_pipeline_alta.py
"""F-031 v5 · H: el alta del parte, protegida frente a `porcentajes`.

`porcentajes` (dedicacion-transfer) tambien da de alta partes de obra en
Sigrid. Toda alta de sv5 (primer parte del mes, R4, y complementario, R3)
pasa por UNA funcion del pipeline, con `con` y `hmo` en UNA llamada a
`escribir` (R40); la cabecera solo entra si el codigo esta libre y no hay
ya un parte En registro del periodo (R41-R42); despues sv5 relee y usa el
parte En registro que haya, suyo o del otro servicio (R43), reintenta una
vez con el siguiente codigo (R44) o falla sin insertar lineas (R45).

Primer bloque: caracterizacion EN VERDE contra el codigo anterior a v5
(R40). Segundo bloque: carreras con `SigridFake(alta_protegida=True)`.

Sin red: `SigridFake` de `tests/dobles.py`. Datos SINTETICOS.
"""
from __future__ import annotations

import logging

import pytest
from infrastructure.sigrid.sigrid_write_client import SigridWriteClient
from tests.dobles import SigridFake
from tests.test_f031_pipeline_estado import (
    CERRADO,
    HORAS,
    REGISTRO,
    _cli,
    _cli_sql,
    _lin,
    _obra,
    _parte,
    _pipeline,
)


def _llamadas_de_alta(cli) -> list[list[dict]]:
    """Cada llamada a `escribir` que lleva un alta, con sus sentencias."""
    return [lote for lote in cli.lotes
            if any(s["op"] == "crear_parte" for s in lote)]


class _ConLotes:
    """Apunta cada lote que recibe `escribir` (una llamada = un lote)."""

    @staticmethod
    def preparar(cli):
        cli.lotes = []
        original = cli.escribir

        def escribir(statements):
            cli.lotes.append([dict(s) for s in statements])
            return original(statements)

        cli.escribir = escribir
        return cli


# =============== Caracterizacion (verde ANTES de v5) =============== #

def test_f031_r40_primer_parte_del_mes_en_una_sola_escritura() -> None:
    cli = _ConLotes.preparar(_cli_sql())
    _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    (lote,) = _llamadas_de_alta(cli)
    # La alta va SOLA en su lote, con la cabecera y el `hmo` juntos.
    assert [s["op"] for s in lote] == ["crear_parte"]
    assert [q.split()[:3] for q in lote[0]["sqls"]] == \
        [["INSERT", "INTO", "con"], ["INSERT", "INTO", "hmo"]]


def test_f031_r40_complementario_en_una_sola_escritura() -> None:
    cli = _ConLotes.preparar(_cli_sql(
        partes=[_parte(800, "PT26/00004", est=CERRADO)]))
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    (lote,) = _llamadas_de_alta(cli)
    assert [s["op"] for s in lote] == ["crear_parte"]
    assert len(lote[0]["sqls"]) == 2
    assert r.partes[0].complementario and r.partes[0].creado


def test_f031_r40_una_alta_por_periodo() -> None:
    cli = _ConLotes.preparar(_cli_sql(
        partes=[_parte(800, "PT26/00004", est=CERRADO)]))
    _pipeline(cli).ejecutar(obra=_obra(), lineas=[
        _lin(1), _lin(2, fecha_int=20260303), _lin(3, fecha_int=20260415)])
    altas = _llamadas_de_alta(cli)
    assert [(lote[0]["ano"], lote[0]["mes"]) for lote in altas] == \
        [(2026, 3), (2026, 4)]


# ======================= Carreras con alta protegida ======================= #

def _protegido(**kw):
    return _cli(alta_protegida=True, **kw)


def _otro(cod, obride=10, est=REGISTRO, mes=3) -> dict:
    """Parte que «el otro servicio» (porcentajes) da de alta."""
    return {"obride": obride, "ano": 2026, "mes": mes, "cod": cod,
            "emp": 1, "est": est}


def _en_registro(cli, obride=10, ano=2026, mes=3) -> list[dict]:
    return [p for p in cli.partes if p["obride"] == obride
            and p["ano"] == ano and p["mes"] == mes
            and p.get("est", REGISTRO) == REGISTRO]


@pytest.mark.parametrize("cerrados", [
    [],                                              # primer parte del mes
    [_parte(800, "PT26/00004", est=CERRADO)],        # complementario
])
def test_f031_r43_r47_otro_servicio_crea_un_parte_en_registro(
        cerrados) -> None:
    cli = _protegido(partes=list(cerrados))
    cli.al_alta = [_otro("PT26/00007")]
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1), _lin(2)])
    (suyo,) = _en_registro(cli)
    assert suyo["cod"] == "PT26/00007"
    (p,) = r.partes
    assert (p.existe, p.creado, p.ide, p.cod, p.estado) == \
        (True, False, suyo["ide"], "PT26/00007", REGISTRO)
    assert [a["insertado"] for a in cli.altas] == [False]
    assert {l["hmoide"] for l in cli.lineas} == {suyo["ide"]}
    assert {e["parte_cod"] for e in r.escritas} == {"PT26/00007"}


def test_f031_r43_otro_servicio_con_el_mismo_codigo_y_periodo() -> None:
    cli = _protegido()
    cli.al_alta = [_otro("PT26/00001")]
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    (suyo,) = _en_registro(cli)
    assert (r.partes[0].cod, r.partes[0].creado) == ("PT26/00001", False)
    assert len(cli.altas) == 1
    assert [l["hmoide"] for l in cli.lineas] == [suyo["ide"]]


def test_f031_r43_alta_propia_es_creado() -> None:
    cli = _protegido()
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    (p,) = r.partes
    assert (p.creado, p.cod) == (True, "PT26/00001")
    assert [a["insertado"] for a in cli.altas] == [True]


def test_f031_r44_codigo_cogido_en_otra_obra_reintenta_con_el_siguiente(
) -> None:
    cli = _protegido(partes=[_parte(800, "PT26/00004", est=CERRADO)])
    cli.al_alta = [_otro("PT26/00005", obride=99)]
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    assert [(a["cod"], a["insertado"]) for a in cli.altas] == \
        [("PT26/00005", False), ("PT26/00006", True)]
    (suyo,) = _en_registro(cli)
    assert (r.partes[0].cod, r.partes[0].creado, r.partes[0].ide) == \
        ("PT26/00006", True, suyo["ide"])
    assert [l["hmoide"] for l in cli.lineas] == [suyo["ide"]]


def test_f031_r44_dos_meses_nuevos_no_comparten_codigo() -> None:
    cli = _protegido()
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[
        _lin(1), _lin(2, fecha_int=20260415)])
    assert sorted(p.cod for p in r.partes) == ["PT26/00001", "PT26/00002"]
    assert len({p["cod"] for p in cli.partes}) == 2


def _codigos_fijos(cli, *codigos):
    cola = list(codigos)
    cli.siguiente_cod_pt = lambda ano, empresa: cola.pop(0)


def test_f031_r45_dos_altas_bloqueadas_fallan_sin_lineas() -> None:
    cli = _protegido(partes=[_parte(800, "PT26/00004", est=CERRADO)])
    cli.al_alta = [_otro("PT26/00005", obride=99),
                   _otro("PT26/00006", obride=98)]
    _codigos_fijos(cli, "PT26/00005", "PT26/00006")
    with pytest.raises(RuntimeError) as exc:
        _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    texto = str(exc.value)
    assert "obra 0100" in texto and "2026/03" in texto
    assert "PT26/00006" in texto
    assert [a["cod"] for a in cli.altas] == ["PT26/00005", "PT26/00006"]
    assert cli.lineas == [] and _en_registro(cli) == []


def test_f031_r46_info_del_alta_sin_nombres(caplog) -> None:
    cli = _protegido(partes=[_parte(800, "PT26/00004", est=CERRADO)])
    cli.al_alta = [_otro("PT26/00005", obride=99)]
    with caplog.at_level(logging.INFO,
                         logger="application.pipelines.registro_pipeline"):
        _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    assert [r.getMessage() for r in caplog.records
            if r.getMessage().startswith("[registro] alta ")] == [
        "[registro] alta obra=0100 periodo=2026/03 cod=PT26/00006 "
        "intento=2 parte=propio"]
    cli = _protegido()
    cli.al_alta = [_otro("PT26/00007")]
    caplog.clear()
    with caplog.at_level(logging.INFO,
                         logger="application.pipelines.registro_pipeline"):
        _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    msgs = [r for r in caplog.records
            if r.getMessage().startswith("[registro] alta ")]
    assert [m.getMessage() for m in msgs] == [
        "[registro] alta obra=0100 periodo=2026/03 cod=PT26/00007 "
        "intento=1 parte=otro servicio"]
    assert all(m.levelno == logging.INFO for m in msgs)
    assert "Persona" not in caplog.text


# ============= R40 · una sola escritura con DOS sentencias reales ============= #

class SigridAltaEnDos(SigridFake):
    """Doble cuyo `stmts_crear_parte` devuelve DOS elementos, como el
    cliente real (`[con, hmo]` con su SQL de `SigridWriteClient`), para que
    se vea si el pipeline parte la lista, la reordena o le mezcla otras
    sentencias. Apunta cada lote que recibe `escribir`. El parte solo
    existe cuando llegan la cabecera y su `hmo` (en cualquier lote: asi el
    flujo sigue y el test mira la forma, no un fallo posterior)."""

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.real = SigridWriteClient(base_url="http://sigrid.invalid",
                                      function_key="clave-de-test",
                                      database="bd")
        self.lotes: list[list[dict]] = []
        self._cabeceras: dict[str, dict] = {}

    def stmts_crear_parte(self, **kw):
        (fila,) = super().stmts_crear_parte(**kw)
        con, hmo = self.real.stmts_crear_parte(**kw)
        return [dict(fila, op="alta_con", sql=con["sql"],
                     parameters=con["parameters"]),
                dict(fila, op="alta_hmo", sql=hmo["sql"],
                     parameters=hmo["parameters"])]

    def escribir(self, statements):
        self.lotes.append([dict(s) for s in statements])
        resto, filas = [], 0
        for s in statements:
            if s["op"] == "alta_con":
                self._cabeceras[s["cod"]] = s
            elif s["op"] == "alta_hmo" and s["cod"] in self._cabeceras:
                cab = self._cabeceras.pop(s["cod"])
                filas += super().escribir([dict(cab, op="crear_parte")])
            elif s["op"] not in ("alta_con", "alta_hmo"):
                resto.append(s)
        return filas + (super().escribir(resto) if resto else 0)


def _lotes_de_alta(cli) -> list[list[dict]]:
    return [lote for lote in cli.lotes
            if any(s["op"].startswith("alta_") for s in lote)]


@pytest.mark.parametrize("cerrados", [
    [],                                              # primer parte del mes
    [_parte(800, "PT26/00004", est=CERRADO)],        # complementario
])
def test_f031_r40_cabecera_y_hmo_en_una_sola_escritura_y_en_orden(
        cerrados) -> None:
    cli = SigridAltaEnDos(obras={"0100": _obra()}, horas=HORAS,
                          partes=list(cerrados))
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    (lote,) = _lotes_de_alta(cli)
    # UNA llamada a `escribir`, con exactamente [con, hmo] y nada mas.
    assert [s["op"] for s in lote] == ["alta_con", "alta_hmo"]
    assert [s["sql"].split()[:3] for s in lote] == \
        [["INSERT", "INTO", "con"], ["INSERT", "INTO", "hmo"]]
    assert lote[0]["cod"] == lote[1]["cod"] == r.partes[0].cod
    assert r.partes[0].creado is True
    # Las lineas van en OTRO lote, despues del alta.
    assert cli.lotes.index(lote) == 0
    assert all(s["op"] == "insert" for s in cli.lotes[1])
