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

from tests.test_f031_pipeline_estado import (
    CERRADO,
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
