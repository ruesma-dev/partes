# tests/test_f036_maestro.py
"""F-036 · R1-R3: el maestro de recursos de sv3 sabe que es «persona».

  - R1: `res.cla` se lee en la lectura paginada de recursos y llega a
    `RecursoRow.cla` (NULL -> None).
  - R2: solo `cla = 1` es recurso persona: el casado, `elegir_recurso` y
    `empresas_con_recurso` no proponen otro; `recurso()` y `recursos`
    siguen viendo todos (el conciliador pisa categoria y hora por ide).
  - R3: un recurso persona sin DNI del recurso no es candidato por nombre
    y el proveedor lo cuenta en un INFO.

Sin red: `_post_sql_read` parcheado. Todo SINTETICO.
"""
from __future__ import annotations

from domain.models.sigrid_models import RecursoRow
from infrastructure.sigrid.sigrid_api_client import SigridApiClient

COLS = ["ide", "cif", "conide", "restipide", "restip_cod", "restip_res",
        "horide_def", "empresa", "fecbaj", "codigo", "nombre", "cla"]


def _cliente(monkeypatch, filas: list[list]) -> tuple[SigridApiClient, list]:
    cliente = SigridApiClient(base_url="http://sigrid.invalid",
                              function_key="clave-de-test", database="bd")
    pedidos: list[dict] = []

    def falso(*, sql, parameters, label, max_rows=None):
        pedidos.append({"sql": sql, "parameters": parameters})
        return COLS, filas if parameters[-2] == 0 else []

    monkeypatch.setattr(cliente, "_post_sql_read", falso)
    return cliente, pedidos


# =============================== R1 ===================================== #

def test_f036_r1_el_sql_de_recursos_lee_res_cla(monkeypatch) -> None:
    cliente, pedidos = _cliente(monkeypatch, [])
    cliente.fetch_recursos()
    sql = " ".join(pedidos[0]["sql"].split())
    assert "res.cla AS cla" in sql


def test_f036_r1_fetch_recursos_mapea_cla(monkeypatch) -> None:
    cliente, _ = _cliente(monkeypatch, [
        [900, "00000001R", 10, 3, "OF1", "Oficial", 100, 1, 0, "MO/1", "P", 1],
        [901, None, None, None, None, None, None, 1, 0, "MAQ/1", "Grua", 2],
        [902, None, None, None, None, None, None, 1, 0, "X/1", "Nulo", None],
    ])
    recursos = cliente.fetch_recursos()
    assert [(r.ide, r.cla) for r in recursos] == \
        [(900, 1), (901, 2), (902, None)]


def test_f036_r1_recurso_row_cla_por_defecto_none() -> None:
    assert RecursoRow(ide=1, cif=None, conide=None).cla is None

