# tests/test_f023_escritura_empresa.py
"""F-023 · R32-R37 y R4: sv5 escribe en la empresa de la obra y verifica.

sv5 es el ultimo punto antes de Sigrid. Hasta F-023 firmaba toda cabecera
con `SIGRID_EMPRESA=1`, numeraba `PT<AA>/NNNNN` mezclando empresas y
localizaba la cabecera recien creada solo por codigo y tipo (con un
correlativo por empresa, eso devuelve DOS filas). Ahora:

  - la cabecera lleva la empresa de la obra destino (R32), el correlativo
    se calcula en esa empresa (R33) y el `INSERT INTO hmo` la filtra (R34);
  - obra sin empresa, o codigo en varias empresas: no se escribe (R35);
  - cada recurso se VERIFICA (empresa, alta a la fecha de la linea y
    persona) antes de escribir (R36) y una linea sin recurso se resuelve
    por DNI solo con un unico candidato de esa empresa (R37);
  - `truncated: true` es una excepcion (R4).

Tres familias, por el nombre de los tests: `coherencia` (reglas puras),
`cliente` (SQL de `SigridWriteClient` con sigrid-api simulado) y
`pipeline` (preparar/registrar con el doble en memoria). Sin red. Datos
SINTETICOS.
"""
from __future__ import annotations

import pytest

from application.services.coherencia_recurso import (
    RecursoSigrid,
    de_alta,
    elegir_por_dni,
    verificar_recurso,
)
from application.services.reglas_registro import (
    MOTIVO_RECURSO_AMBIGUO,
    MOTIVO_RECURSO_BAJA,
    MOTIVO_RECURSO_NO_EXISTE,
    MOTIVO_RECURSO_OTRA_EMPRESA,
    MOTIVO_RECURSO_OTRA_PERSONA,
    MOTIVO_SIN_RECURSO_EMPRESA,
)

FECHA = 20260915
DNI = "12345678Z"


def _rec(reside=501, *, empresa=1, fecbaj=0, dni=DNI) -> RecursoSigrid:
    return RecursoSigrid(reside=reside, empresa=empresa, fecbaj=fecbaj,
                         dni=dni)


# ========================= coherencia · de_alta ========================= #

@pytest.mark.parametrize("fecbaj, esperado", [
    (None, True), (0, True), (FECHA + 1, True), (FECHA, False),
    (FECHA - 1, False),
])
def test_f023_r36_coherencia_de_alta(fecbaj, esperado) -> None:
    assert de_alta(fecbaj, FECHA) is esperado


# ====================== coherencia · R36 verificar ====================== #

def test_f023_r36_coherencia_recurso_correcto_no_da_motivo() -> None:
    assert verificar_recurso(_rec(), 1, FECHA, DNI) is None


def test_f023_r36_coherencia_otra_empresa() -> None:
    assert verificar_recurso(_rec(empresa=28), 1, FECHA, DNI) == \
        MOTIVO_RECURSO_OTRA_EMPRESA


def test_f023_r36_coherencia_recurso_sin_empresa_es_otra_empresa() -> None:
    assert verificar_recurso(_rec(empresa=None), 1, FECHA, DNI) == \
        MOTIVO_RECURSO_OTRA_EMPRESA


def test_f023_r36_coherencia_de_baja_a_la_fecha_de_la_linea() -> None:
    assert verificar_recurso(_rec(fecbaj=FECHA), 1, FECHA, DNI) == \
        MOTIVO_RECURSO_BAJA
    assert verificar_recurso(_rec(fecbaj=FECHA + 1), 1, FECHA, DNI) is None


def test_f023_r36_coherencia_la_empresa_se_comprueba_antes_que_la_baja() -> None:
    assert verificar_recurso(_rec(empresa=28, fecbaj=FECHA - 1), 1, FECHA,
                             DNI) == MOTIVO_RECURSO_OTRA_EMPRESA


def test_f023_r36_coherencia_dni_de_otra_persona() -> None:
    assert verificar_recurso(_rec(dni="87654321X"), 1, FECHA, DNI) == \
        MOTIVO_RECURSO_OTRA_PERSONA


def test_f023_r36_coherencia_recurso_sin_dni_con_linea_con_dni() -> None:
    """No se puede comprobar que sea de esa persona: no se escribe."""
    assert verificar_recurso(_rec(dni=None), 1, FECHA, DNI) == \
        MOTIVO_RECURSO_OTRA_PERSONA


def test_f023_r36_coherencia_el_dni_se_compara_normalizado() -> None:
    assert verificar_recurso(_rec(dni="12345678-z"), 1, FECHA,
                             " 12.345.678 Z ") is None


@pytest.mark.parametrize("dni_linea", [None, "", "  "])
def test_f023_r36_coherencia_linea_sin_dni_no_compara_persona(
        dni_linea) -> None:
    assert verificar_recurso(_rec(dni="87654321X"), 1, FECHA,
                             dni_linea) is None


def test_f023_r36_coherencia_recurso_inexistente() -> None:
    assert verificar_recurso(None, 1, FECHA, DNI) == MOTIVO_RECURSO_NO_EXISTE


def test_f023_r36_coherencia_los_motivos_dicen_que_fallo() -> None:
    """Cuatro motivos distintos, legibles para el portal."""
    motivos = {MOTIVO_RECURSO_NO_EXISTE, MOTIVO_RECURSO_OTRA_EMPRESA,
               MOTIVO_RECURSO_BAJA, MOTIVO_RECURSO_OTRA_PERSONA}
    assert len(motivos) == 4
    assert "empresa" in MOTIVO_RECURSO_OTRA_EMPRESA
    assert "baja" in MOTIVO_RECURSO_BAJA
    assert "DNI" in MOTIVO_RECURSO_OTRA_PERSONA


# ===================== coherencia · R37 por DNI ========================= #

def test_f023_r37_coherencia_un_unico_candidato() -> None:
    assert elegir_por_dni([_rec(501), _rec(502, empresa=28)], 1, FECHA) == \
        (501, None)


def test_f023_r37_coherencia_sin_candidatos() -> None:
    cands = [_rec(501, empresa=28), _rec(502, fecbaj=FECHA - 1)]
    assert elegir_por_dni(cands, 1, FECHA) == \
        (None, MOTIVO_SIN_RECURSO_EMPRESA)
    assert elegir_por_dni([], 1, FECHA) == (None, MOTIVO_SIN_RECURSO_EMPRESA)


def test_f023_r37_coherencia_varios_candidatos_es_ambiguo() -> None:
    assert elegir_por_dni([_rec(501), _rec(502)], 1, FECHA) == \
        (None, MOTIVO_RECURSO_AMBIGUO)


def test_f023_r37_coherencia_el_mismo_recurso_dos_veces_es_uno() -> None:
    """La lectura por DNI une `emp.dni` y `res.cif`: el mismo recurso puede
    llegar por los dos caminos."""
    assert elegir_por_dni([_rec(501), _rec(501)], 1, FECHA) == (501, None)


def test_f023_r37_coherencia_la_baja_a_la_fecha_de_la_linea() -> None:
    cands = [_rec(501, fecbaj=20260801), _rec(502, fecbaj=0)]
    assert elegir_por_dni(cands, 1, 20260731) == \
        (None, MOTIVO_RECURSO_AMBIGUO)
    assert elegir_por_dni(cands, 1, 20260801) == (502, None)


# ===================================================================== #
# cliente · SQL de SigridWriteClient contra sigrid-api simulado (R32-R35,
# R4). Ni una escritura real: `httpx.post` se sustituye por un doble.
# ===================================================================== #

import httpx  # noqa: E402

from domain.models.registro_models import ObraEntrada  # noqa: E402
from infrastructure.sigrid import sigrid_write_client as modulo  # noqa: E402
from infrastructure.sigrid.sigrid_write_client import (  # noqa: E402
    SigridWriteClient,
)


class SigridApiFalso:
    """sigrid-api en memoria: responde a cada lectura con lo que diga
    `respuestas` (una lista de filas por llamada) y apunta lo pedido."""

    def __init__(self, columnas, *respuestas, truncated=False) -> None:
        self.columnas = columnas
        self.respuestas = list(respuestas)
        self.truncated = truncated
        self.lecturas: list[dict] = []

    def __call__(self, url, headers=None, timeout=None, json=None):
        self.lecturas.append(json)
        filas = self.respuestas.pop(0) if self.respuestas else []
        return httpx.Response(200, json={
            "ok": True, "columns": self.columnas, "rows": filas,
            "truncated": self.truncated})


def _cliente(monkeypatch, falso) -> SigridWriteClient:
    monkeypatch.setattr(modulo.httpx, "post", falso)
    return SigridWriteClient(base_url="http://sigrid.invalid",
                             function_key="clave-de-test", database="bd")


def _sql(texto: str) -> str:
    return " ".join(texto.split())


OBRA_28 = ObraEntrada(ide=200, codigo="0100", nombre="Nave", empresa=28)


def test_f023_r32_cliente_la_cabecera_lleva_la_empresa_de_la_obra() -> None:
    cli = SigridWriteClient(base_url="http://x", function_key="k",
                            database="bd")
    con, _ = cli.stmts_crear_parte(obra=OBRA_28, ano=2026, mes=9,
                                   cod="PT26/00007", desc="Parte Nave")
    assert _sql(con["sql"]).startswith(
        "INSERT INTO con (ide, emp, tip, est, cod, res, fec)")
    assert con["parameters"] == [28, 35, 1, "PT26/00007", "Parte Nave",
                                 20260930]


def test_f023_r32_cliente_ya_no_acepta_empresa_en_el_constructor() -> None:
    with pytest.raises(TypeError):
        SigridWriteClient(base_url="http://x", function_key="k",
                          database="bd", empresa=1)  # type: ignore[call-arg]


def test_f023_r32_cliente_obra_sin_empresa_no_genera_sentencias() -> None:
    cli = SigridWriteClient(base_url="http://x", function_key="k",
                            database="bd")
    with pytest.raises(TypeError):
        cli.stmts_crear_parte(obra=ObraEntrada(ide=1, codigo="1"), ano=2026,
                              mes=9, cod="PT26/00001", desc="x")


def test_f023_r34_cliente_el_insert_de_hmo_filtra_por_empresa() -> None:
    cli = SigridWriteClient(base_url="http://x", function_key="k",
                            database="bd", tip_parte=35)
    _, hmo = cli.stmts_crear_parte(obra=OBRA_28, ano=2026, mes=9,
                                   cod="PT26/00007", desc="Parte Nave")
    assert _sql(hmo["sql"]).endswith(
        "FROM con WHERE cod = ? AND tip = ? AND emp = ?")
    assert hmo["parameters"][-3:] == ["PT26/00007", 35, 28]
    assert hmo["parameters"][:4] == [0, 200, 2026, 9]


def test_f023_r33_cliente_el_correlativo_es_de_la_empresa(monkeypatch) -> None:
    falso = SigridApiFalso(["maxcod"], [["PT26/00121"]])
    assert _cliente(monkeypatch, falso).siguiente_cod_pt(2026, 28) == \
        "PT26/00122"
    (lectura,) = falso.lecturas
    assert _sql(lectura["sql"]) == \
        "SELECT MAX(cod) AS maxcod FROM con WHERE cod LIKE ? AND emp = ?"
    assert lectura["parameters"] == ["PT26/%", 28]


def test_f023_r33_cliente_primer_parte_del_ano_en_la_empresa(
        monkeypatch) -> None:
    falso = SigridApiFalso(["maxcod"], [[None]])
    assert _cliente(monkeypatch, falso).siguiente_cod_pt(2027, 1) == \
        "PT27/00001"


def test_f023_r35_cliente_codigo_en_varias_empresas_falla(monkeypatch) -> None:
    falso = SigridApiFalso(["ide", "cod", "res", "cenide", "emp"],
                           [[100, "0100", "A", 3, 1], [200, "0100", "B", 4, 28]])
    with pytest.raises(RuntimeError, match="varias"):
        _cliente(monkeypatch, falso).obra_por_codigo("0100")


def test_f023_r35_cliente_obra_por_codigo_con_su_empresa(monkeypatch) -> None:
    falso = SigridApiFalso(["ide", "cod", "res", "cenide", "emp"],
                           [[200, "0100", "B", 4, 28]])
    obra = _cliente(monkeypatch, falso).obra_por_codigo("0100")
    assert (obra.ide, obra.empresa, obra.cenide) == (200, 28, 4)
    assert "con.emp AS emp" in _sql(falso.lecturas[0]["sql"])


def test_f023_r35_cliente_obra_inexistente_es_none(monkeypatch) -> None:
    falso = SigridApiFalso(["ide", "cod", "res", "cenide", "emp"], [])
    assert _cliente(monkeypatch, falso).obra_por_codigo("9999") is None
    assert _cliente(monkeypatch, falso).obra_por_ide(9999) is None


@pytest.mark.parametrize("emp", [None, 0])
def test_f023_r35_cliente_obra_por_ide_sin_empresa(monkeypatch, emp) -> None:
    falso = SigridApiFalso(["ide", "cod", "res", "cenide", "emp"],
                           [[200, "0100", "B", None, emp]])
    obra = _cliente(monkeypatch, falso).obra_por_ide(200)
    assert (obra.ide, obra.empresa, obra.cenide) == (200, None, 0)
    assert "con.emp AS emp" in _sql(falso.lecturas[0]["sql"])


def test_f023_r4_cliente_truncated_es_una_excepcion(monkeypatch) -> None:
    falso = SigridApiFalso(["ide", "cod", "res", "cenide", "emp"],
                           [[200, "0100", "B", 4, 28]], truncated=True)
    with pytest.raises(RuntimeError, match="truncada"):
        _cliente(monkeypatch, falso).obra_por_ide(200)


def test_f023_r37_cliente_recursos_por_dni_sin_agrupar(monkeypatch) -> None:
    falso = SigridApiFalso(
        ["dni", "reside", "emp", "fecbaj"],
        [[DNI, 501, 1, 0], [DNI, 502, 28, 20210101], ["", 999, 1, 0],
         ["87654321X", 503, 1, None]])
    mapa = _cliente(monkeypatch, falso).recursos_por_dni(
        ["12345678-z", "87654321X", None, ""])
    assert mapa == {
        DNI: [RecursoSigrid(501, 1, 0, DNI),
              RecursoSigrid(502, 28, 20210101, DNI)],
        "87654321X": [RecursoSigrid(503, 1, None, "87654321X")],
    }
    sql = _sql(falso.lecturas[0]["sql"])
    assert "MAX(" not in sql and "GROUP BY" not in sql
    assert "UNION ALL" in sql
    assert "JOIN con rc ON rc.ide = q.reside" in sql
    assert falso.lecturas[0]["parameters"] == ["12345678Z", "87654321X"] * 2


def test_f023_r37_cliente_recursos_por_dni_sin_dnis_no_lee(monkeypatch) -> None:
    falso = SigridApiFalso(["dni"])
    assert _cliente(monkeypatch, falso).recursos_por_dni([None, " "]) == {}
    assert falso.lecturas == []


def test_f023_r36_cliente_datos_recursos_por_lotes_de_500(monkeypatch) -> None:
    columnas = ["reside", "emp", "fecbaj", "dni"]
    falso = SigridApiFalso(columnas, [[1, 1, 0, DNI]], [[501, 28, None, None]])
    datos = _cliente(monkeypatch, falso).datos_recursos(range(1, 502))
    assert [len(lectura["parameters"]) for lectura in falso.lecturas] == \
        [500, 1]
    assert falso.lecturas[1]["parameters"] == [501]
    assert datos == {1: RecursoSigrid(1, 1, 0, DNI),
                     501: RecursoSigrid(501, 28, None, None)}
    sql = _sql(falso.lecturas[0]["sql"])
    assert "JOIN con rc ON rc.ide = res.ide" in sql
    assert "LEFT JOIN emp ON emp.ide = res.conide" in sql
    assert "ELSE res.cif END AS dni" in sql


def test_f023_r36_cliente_datos_recursos_sin_resides_no_lee(monkeypatch) -> None:
    falso = SigridApiFalso(["reside"])
    assert _cliente(monkeypatch, falso).datos_recursos([None, 0]) == {}
    assert falso.lecturas == []
