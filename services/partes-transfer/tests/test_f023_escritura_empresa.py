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
    # F-031 v5 (DA10, humano 2026-10-06): el alta protegida anade los
    # parametros de sus NOT EXISTS; la fila son los seis primeros.
    assert con["parameters"][:6] == [28, 35, 1, "PT26/00007", "Parte Nave",
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
    # F-031 v5 (DA10): el `hmo` anade un NOT EXISTS detras del filtro.
    assert "FROM con WHERE cod = ? AND tip = ? AND emp = ?" in _sql(
        hmo["sql"])
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


# ===================================================================== #
# pipeline · preparar/registrar con el doble en memoria (R32-R37).
# ===================================================================== #

from application.pipelines.registro_pipeline import (  # noqa: E402
    RegistroPipeline,
)
from application.services.reglas_registro import (  # noqa: E402
    MOTIVO_SIN_RECURSO,
)
from domain.models.registro_models import (  # noqa: E402
    HoraRecurso,
    LineaEntrada,
)
from tests.dobles import SettingsFake, SigridFake  # noqa: E402

HORAS = [HoraRecurso(horide=1, cod="HL01", res=None, pre=10.0),
         HoraRecurso(horide=2, cod="HE01", res=None, pre=15.0)]
OBRA_UNO = ObraEntrada(ide=10, codigo="0100", nombre="Uno", empresa=1)
OBRA_VEINTIOCHO = ObraEntrada(ide=20, codigo="0200", nombre="Veintiocho",
                              empresa=28)
PRUEBAS = ObraEntrada(ide=99, codigo="0404", nombre="Pruebas", empresa=1)


def _sigrid_empresas(**kw) -> SigridFake:
    return SigridFake(
        obras={"0100": OBRA_UNO, "0200": OBRA_VEINTIOCHO, "0404": PRUEBAS},
        horas={i: HORAS for i in range(501, 510)}, **kw)


def _lin(rid, recurso=501, *, dni=None, fecha=FECHA) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=fecha, recurso_ide=recurso,
                        dni=dni, nombre=f"T{rid}", tipo_hora="normal",
                        horas=8.0)


def _pipeline(cli, **st) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=SettingsFake(**st))


def _motivos(resultado) -> dict:
    return {o["registro_id"]: o["motivo"] for o in resultado.omitidas}


def test_f023_r32_r33_pipeline_parte_nuevo_en_la_empresa_de_la_obra() -> None:
    cli = _sigrid_empresas(
        recursos={502: RecursoSigrid(502, 28, 0, None)},
        partes=[{"ide": 1, "obride": 10, "ano": 2025, "mes": 1,
                 "cod": "PT26/00338", "emp": 1},
                {"ide": 2, "obride": 20, "ano": 2025, "mes": 1,
                 "cod": "PT26/00121", "emp": 28}])
    r = _pipeline(cli).ejecutar(obra=OBRA_VEINTIOCHO, lineas=[_lin(1, 502)])
    assert [e["registro_id"] for e in r.escritas] == [1]
    nuevo = cli.partes[-1]
    assert (nuevo["cod"], nuevo["emp"], nuevo["obride"]) == \
        ("PT26/00122", 28, 20)


def test_f023_r33_pipeline_el_preflight_propone_el_correlativo_de_la_empresa(
) -> None:
    cli = _sigrid_empresas(partes=[
        {"ide": 1, "obride": 10, "ano": 2025, "mes": 1, "cod": "PT26/00338",
         "emp": 1}])
    pf = _pipeline(cli).preflight(obra=OBRA_UNO, lineas=[_lin(1)])
    assert [p.cod for p in pf.partes] == ["PT26/00339"]
    pf28 = _pipeline(_sigrid_empresas(
        recursos={502: RecursoSigrid(502, 28, 0, None)}, partes=[
            {"ide": 1, "obride": 10, "ano": 2025, "mes": 1,
             "cod": "PT26/00338", "emp": 1}])).preflight(
        obra=OBRA_VEINTIOCHO, lineas=[_lin(1, 502)])
    assert [p.cod for p in pf28.partes] == ["PT26/00001"]


def test_f023_r35_pipeline_obra_sin_empresa_no_escribe_nada() -> None:
    sin = ObraEntrada(ide=30, codigo="0300", nombre="Sin", empresa=None)
    cli = SigridFake(obras={"0300": sin}, horas={501: HORAS})
    with pytest.raises(RuntimeError, match="empresa"):
        _pipeline(cli).ejecutar(obra=sin, lineas=[_lin(1)])
    assert "escribir" not in cli.llamadas
    assert "horas_de_recursos" not in cli.llamadas


def test_f023_r35_pipeline_la_obra_de_pruebas_sin_empresa_tampoco() -> None:
    sin = ObraEntrada(ide=99, codigo="0404", nombre="Pruebas", empresa=None)
    cli = SigridFake(obras={"0100": OBRA_UNO, "0404": sin},
                     horas={501: HORAS})
    with pytest.raises(RuntimeError, match="empresa"):
        _pipeline(cli, obra_pruebas_forzar=True).ejecutar(
            obra=OBRA_UNO, lineas=[_lin(1)])
    assert "escribir" not in cli.llamadas


def test_f023_r36_pipeline_verifica_cada_recurso_antes_de_escribir() -> None:
    cli = _sigrid_empresas(recursos={
        501: RecursoSigrid(501, 1, 0, DNI),
        502: RecursoSigrid(502, 28, 0, DNI),
        503: RecursoSigrid(503, 1, FECHA, DNI),
        505: RecursoSigrid(505, 1, 0, "87654321X"),
    })
    r = _pipeline(cli).ejecutar(obra=OBRA_UNO, lineas=[
        _lin(1, 501, dni=DNI), _lin(2, 502, dni=DNI), _lin(3, 503, dni=DNI),
        _lin(4, 504, dni=DNI), _lin(5, 505, dni=DNI), _lin(6, 505)])
    assert [e["registro_id"] for e in r.escritas] == [1, 6]
    assert _motivos(r) == {
        2: MOTIVO_RECURSO_OTRA_EMPRESA, 3: MOTIVO_RECURSO_BAJA,
        4: MOTIVO_RECURSO_NO_EXISTE, 5: MOTIVO_RECURSO_OTRA_PERSONA}
    assert cli.recursos_leidos == [[501, 502, 503, 504, 505]]


def test_f023_r36_pipeline_si_no_se_puede_verificar_no_se_escribe() -> None:
    class Caido(SigridFake):
        def datos_recursos(self, resides):
            raise RuntimeError("sigrid-api caido")

    cli = Caido(obras={"0100": OBRA_UNO}, horas={501: HORAS})
    with pytest.raises(RuntimeError, match="caido"):
        _pipeline(cli).ejecutar(obra=OBRA_UNO, lineas=[_lin(1)])
    assert "escribir" not in cli.llamadas


def test_f023_r37_pipeline_sin_recurso_se_resuelve_por_dni_en_la_empresa(
) -> None:
    cli = _sigrid_empresas(por_dni={DNI: [
        RecursoSigrid(501, 1, 0, DNI), RecursoSigrid(502, 28, 0, DNI)]})
    r = _pipeline(cli).ejecutar(obra=OBRA_UNO,
                                lineas=[_lin(1, None, dni="12345678-z")])
    assert [e["registro_id"] for e in r.escritas] == [1]
    assert cli.lineas[0]["reside"] == 501
    # Lo resuelto por DNI ya es coherente: no se vuelve a verificar.
    assert cli.recursos_leidos == []


def test_f023_r37_pipeline_por_dni_cero_o_varios_se_omite_con_motivo(
) -> None:
    cli = _sigrid_empresas(por_dni={
        DNI: [RecursoSigrid(501, 1, 0, DNI), RecursoSigrid(503, 1, 0, DNI)],
        "87654321X": [RecursoSigrid(502, 28, 0, "87654321X")],
    })
    r = _pipeline(cli).ejecutar(obra=OBRA_UNO, lineas=[
        _lin(1, None, dni=DNI), _lin(2, None, dni="87654321X"),
        _lin(3, None, dni="11111111H")])
    assert r.escritas == []
    assert _motivos(r) == {1: MOTIVO_RECURSO_AMBIGUO,
                           2: MOTIVO_SIN_RECURSO_EMPRESA,
                           3: MOTIVO_SIN_RECURSO_EMPRESA}


def test_f023_r37_pipeline_la_fecha_de_cada_linea_cuenta() -> None:
    cli = _sigrid_empresas(por_dni={DNI: [
        RecursoSigrid(501, 1, 20260801, DNI), RecursoSigrid(502, 1, 0, DNI)]})
    r = _pipeline(cli).ejecutar(obra=OBRA_UNO, lineas=[
        _lin(1, None, dni=DNI, fecha=20260731),
        _lin(2, None, dni=DNI, fecha=20260915)])
    assert _motivos(r) == {1: MOTIVO_RECURSO_AMBIGUO}
    assert [e["registro_id"] for e in r.escritas] == [2]


def test_f023_r37_pipeline_si_falla_la_lectura_por_dni_queda_sin_recurso(
) -> None:
    class Caido(SigridFake):
        def recursos_por_dni(self, dnis):
            raise RuntimeError("sigrid-api caido")

    cli = Caido(obras={"0100": OBRA_UNO}, horas={501: HORAS})
    r = _pipeline(cli).ejecutar(obra=OBRA_UNO, lineas=[_lin(1, None, dni=DNI)])
    assert _motivos(r) == {1: MOTIVO_SIN_RECURSO}


def test_f023_r37_pipeline_sin_recurso_ni_dni_no_lee_por_dni() -> None:
    cli = _sigrid_empresas()
    r = _pipeline(cli).ejecutar(obra=OBRA_UNO, lineas=[_lin(1, None)])
    assert _motivos(r) == {1: MOTIVO_SIN_RECURSO}
    assert "recursos_por_dni" not in cli.llamadas


def test_f023_r36_pipeline_la_verificacion_manda_sobre_las_reglas() -> None:
    """Una incidencia intermedia con el recurso de otra empresa: el motivo
    es el de la verificacion (lo que hay que arreglar primero)."""
    cli = _sigrid_empresas(recursos={502: RecursoSigrid(502, 28, 0, None)})
    linea = _lin(1, 502)
    linea.es_incidencia, linea.incidencia_rol = True, "intermedio"
    r = _pipeline(cli).ejecutar(obra=OBRA_UNO, lineas=[linea])
    assert _motivos(r) == {1: MOTIVO_RECURSO_OTRA_EMPRESA}


def test_f023_da5_pipeline_settings_sin_sigrid_empresa(monkeypatch) -> None:
    from config.settings import Settings

    monkeypatch.setenv("SIGRID_API_BASE_URL", "http://sigrid.invalid")
    monkeypatch.setenv("SIGRID_API_FUNCTION_KEY", "clave-de-test")
    monkeypatch.setenv("SIGRID_EMPRESA", "1")
    assert not hasattr(Settings(_env_file=None), "sigrid_empresa")


# ============== refuerzo tras la campana de mutacion (T23) ============== #

def test_f023_r36_coherencia_lo_leido_de_sigrid_no_se_puede_alterar() -> None:
    """`RecursoSigrid` es inmutable: lo que se verifica es lo que Sigrid
    dijo, no algo que un paso posterior haya podido tocar."""
    import dataclasses

    r = _rec()
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.empresa = 28  # type: ignore[misc]
    assert {r, _rec()} == {r}


def test_f023_r33_pipeline_el_correlativo_se_pide_una_vez_por_parte_nuevo(
) -> None:
    """El `PT` propuesto en la evaluacion (bajo el lock) es el que se
    escribe: no se vuelve a pedir al crear la cabecera."""
    cli = _sigrid_empresas()
    _pipeline(cli).ejecutar(obra=OBRA_UNO, lineas=[_lin(1)])
    assert cli.llamadas.count("siguiente_cod_pt") == 1
    assert cli.partes[-1]["cod"] == "PT26/00001"
