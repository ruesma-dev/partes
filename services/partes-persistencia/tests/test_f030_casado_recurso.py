# tests/test_f030_casado_recurso.py
"""F-030 · R4-R13: casar al trabajador contra la «ficha de recurso».

Humano, 2026-10-05: «el proceso es el mismo que con empleado pero contra la
ficha de recurso cuando no esta la de empleado». Una ficha de recurso es un
recurso `MO/` con `res.cif`, sin ninguna ficha `emp` con ese DNI y cuyo
`res.conide` no es una ficha; se trata como una ficha de empleado mas
(DNI = `res.cif`, nombre = `con.res`, empresa y baja las del recurso) y se
casa con el MISMO codigo: `IndicePersonas.elegir_ficha`,
`fichas_candidatas` y `EmpleadoMatcher.match_nombre`.

Familias, por el nombre de los tests: `lectura` (el cliente de Sigrid),
`fichas_de_recurso` (la construccion), `proveedor` y los requisitos del
casado (`r5`...`r13`). Proveedor REAL sobre un Sigrid en memoria y
repositorio falso. Todo SINTETICO: ni DNIs, ni nombres, ni codigos reales.
"""
from __future__ import annotations

import json

import httpx

from domain.models.sigrid_models import RecursoRow
from infrastructure.sigrid import sigrid_api_client as modulo
from infrastructure.sigrid.sigrid_api_client import SigridApiClient

# ============================ lectura · R4 ============================== #


class SigridFalso:
    """sigrid-api en memoria con una sola pagina."""

    def __init__(self, columnas, filas) -> None:
        self.columnas = list(columnas)
        self.filas = [list(f) for f in filas]
        self.peticiones: list[dict] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.peticiones.append(json.loads(request.content))
        return httpx.Response(200, json={
            "ok": True, "columns": self.columnas, "rows": self.filas,
            "row_count": len(self.filas), "truncated": False})


COLS_RES = ["ide", "cif", "conide", "restipide", "restip_cod", "restip_res",
            "horide_def", "empresa", "fecbaj", "codigo", "nombre"]


def test_f030_r4_lectura_recursos_con_codigo_y_nombre(monkeypatch) -> None:
    falso = SigridFalso(COLS_RES, [
        [950, "09876543B", None, 3, "PE", "PEON", 100, 28, 0, "MO/0950",
         "APELLIDO OTRO, NOMBRE"],
        [951, None, 10, None, None, None, None, 1, None, None, None],
    ])
    transporte = httpx.MockTransport(falso)
    monkeypatch.setattr(modulo.httpx, "HTTPTransport",
                        lambda **_kw: transporte)
    cli = SigridApiClient(base_url="http://sigrid.invalid",
                          function_key="clave-de-test", database="bd")
    recursos = cli.fetch_recursos()
    assert recursos == [
        RecursoRow(ide=950, cif="09876543B", conide=None, restipide=3,
                   restip_cod="PE", restip_res="PEON", horide_def=100,
                   empresa=28, fecbaj=0, codigo="MO/0950",
                   nombre="APELLIDO OTRO, NOMBRE"),
        RecursoRow(ide=951, cif=None, conide=10, empresa=1),
    ]
    (peticion,) = falso.peticiones
    sql = " ".join(peticion["sql"].split())
    # En la MISMA lectura paginada: sin una segunda consulta.
    assert "rc.cod AS codigo" in sql and "rc.res AS nombre" in sql
    assert sql.endswith(
        "ORDER BY res.ide OFFSET ? ROWS FETCH NEXT ? ROWS ONLY")


def test_f030_r4_lectura_recurso_row_sin_codigo_ni_nombre_por_defecto(
) -> None:
    r = RecursoRow(ide=1, cif=None, conide=None)
    assert (r.codigo, r.nombre) == (None, None)


# ===================== fichas_de_recurso · R4 =========================== #

import application.services.fichas_de_recurso as fdr  # noqa: E402
from domain.models.sigrid_models import EmpleadoRow  # noqa: E402

CIF_P = "09876543B"     # persona SIN ficha de empleado (empresa 28)
CIF_Q = "08765432C"     # otra persona sin ficha (empresa 28)
DNI_E = "11111111H"     # persona CON ficha de empleado (empresa 28)

FICHA_E = EmpleadoRow(ide=10, codigo="E10", nombre="EVA FICHA", dni=DNI_E,
                      reside=900, empresa=28, fecbaj=0)


def _rec(ide, cif, *, codigo=None, conide=None, nombre="APELLIDOS, NOMBRE",
         empresa=28, fecbaj=0) -> RecursoRow:
    return RecursoRow(ide=ide, cif=cif, conide=conide, empresa=empresa,
                      fecbaj=fecbaj, codigo=codigo or f"MO/{ide}",
                      nombre=nombre)


def test_f030_r4_fichas_de_recurso_la_ficha_es_el_recurso() -> None:
    r = _rec(950, CIF_P, nombre="GOMEZ RUIZ, PEDRO", fecbaj=20261231)
    assert fdr.fichas_de_recurso([FICHA_E], [r]) == [EmpleadoRow(
        ide=950, codigo="MO/950", nombre="GOMEZ RUIZ, PEDRO", dni=CIF_P,
        reside=950, empresa=28, fecbaj=20261231)]


def test_f030_r4_fichas_de_recurso_el_dni_es_el_cif_tal_cual() -> None:
    (f,) = fdr.fichas_de_recurso([], [_rec(950, " 09876543-b ")])
    assert f.dni == " 09876543-b "


def test_f030_r4_fichas_de_recurso_solo_mano_de_obra() -> None:
    assert fdr.PREFIJO_MANO_DE_OBRA == "MO/"
    recursos = [_rec(950, CIF_P, codigo="MQ/950"),
                _rec(951, CIF_Q, codigo="XMO/951")]
    assert fdr.fichas_de_recurso([], recursos) == []
    sin_codigo = RecursoRow(ide=952, cif=CIF_P, conide=None, empresa=28)
    assert fdr.fichas_de_recurso([], [sin_codigo]) == []


def test_f030_r4_fichas_de_recurso_sin_cif_no_es_ficha() -> None:
    assert fdr.fichas_de_recurso([], [_rec(950, None), _rec(951, ""),
                                      _rec(952, " - ")]) == []


def test_f030_r4_fichas_de_recurso_con_ficha_por_dni_no_es_ficha() -> None:
    """Hay una ficha `emp` con ese DNI (normalizado, de cualquier empresa
    y de alta o de baja): esa persona casa por su ficha."""
    de_baja_otra = EmpleadoRow(ide=11, codigo="E11", nombre="X",
                               dni="08765432-c", reside=None, empresa=1,
                               fecbaj=20200101)
    recursos = [_rec(950, DNI_E), _rec(951, CIF_Q)]
    assert fdr.fichas_de_recurso([FICHA_E, de_baja_otra], recursos) == []


def test_f030_r4_fichas_de_recurso_con_conide_a_una_ficha_no_es_ficha(
) -> None:
    assert fdr.fichas_de_recurso([FICHA_E], [_rec(950, CIF_P,
                                                  conide=10)]) == []


def test_f030_r4_fichas_de_recurso_conide_que_no_es_ficha_si_es_ficha(
) -> None:
    (f,) = fdr.fichas_de_recurso([FICHA_E], [_rec(950, CIF_P, conide=999)])
    assert f.ide == 950


def test_f030_r4_fichas_de_recurso_de_baja_y_de_otra_empresa_tambien() -> None:
    """De todas las empresas y estados: `elegir_ficha` filtra alta y
    empresa y da los mismos motivos que con fichas de empleado."""
    recursos = [_rec(950, CIF_P, fecbaj=20200101),
                _rec(951, CIF_Q, empresa=1)]
    assert [f.ide for f in fdr.fichas_de_recurso([], recursos)] == [950, 951]


def test_f030_r4_fichas_de_recurso_ficha_sin_dni_no_tapa_nada() -> None:
    sin_dni = EmpleadoRow(ide=12, codigo="E12", nombre="Y", dni=None,
                          reside=None, empresa=28, fecbaj=0)
    assert [f.ide for f in fdr.fichas_de_recurso([sin_dni],
                                                 [_rec(950, CIF_P)])] == [950]


# ========================= el proveedor · T5 ============================ #

import logging  # noqa: E402
from datetime import date  # noqa: E402

import pytest  # noqa: E402

from application.pipelines.persist_parte_pipeline import (  # noqa: E402
    PersistPartePipeline,
)
from application.services.parte_normalizer import ParteNormalizer  # noqa: E402
from application.services.sigrid_matcher_provider import (  # noqa: E402
    SigridMatcherProvider,
)
from domain.models.parte_records import (  # noqa: E402
    EmpleadoMatch,
    ParteDocumento,
    RegistroNormalizado,
)
from domain.models.sigrid_models import (  # noqa: E402
    EmpresaRow,
    ObraRow,
    TipoHoraRow,
)

HOY = 20260925
CIF_V = "07654321D"     # persona sin ficha con el mismo nombre que FICHA_V
DNI_V = "33333333P"

O28 = ObraRow(ide=724, codigo="0724", nombre="Obra Porsan", empresa=28)
O1 = ObraRow(ide=300, codigo="0300", nombre="Obra Ruesma", empresa=1)

#: Fichas de empleado de la empresa 28.
FICHA_PG = EmpleadoRow(ide=10, codigo="E10", nombre="PEDRO GOMEZ", dni=DNI_E,
                       reside=900, empresa=28, fecbaj=0)
FICHA_V = EmpleadoRow(ide=20, codigo="E20", nombre="LUIS VEGA MORA",
                      dni=DNI_V, reside=920, empresa=28, fecbaj=0)
#: Recursos: los de las fichas y dos fichas de recurso (P y V').
REC_PG = _rec(900, None, conide=10, nombre="GOMEZ, PEDRO")
REC_V = _rec(920, None, conide=20, nombre="VEGA MORA, LUIS")
REC_P = _rec(950, CIF_P, nombre="GOMEZ RUIZ, PEDRO")
REC_VP = _rec(951, CIF_V, nombre="VEGA MORA, LUIS")

FICHAS = [FICHA_PG, FICHA_V]
RECURSOS = [REC_PG, REC_V, REC_P, REC_VP]


class Lookup:
    """Los maestros que carga el proveedor, en memoria."""

    def __init__(self, *, empleados=FICHAS, recursos=RECURSOS) -> None:
        self.empleados = list(empleados)
        self.recursos = list(recursos)

    def fetch_empleados(self):
        return list(self.empleados)

    def fetch_obras(self):
        return [O28, O1]

    def fetch_tipos_hora(self):
        return [TipoHoraRow(ide=1, codigo="HL01", descripcion="Hora",
                            ext=0, pre=None, prenom=None)]

    def fetch_recursos(self):
        return list(self.recursos)

    def fetch_empresas(self):
        return [EmpresaRow(numemp=1, nombre="UNO"),
                EmpresaRow(numemp=28, nombre="VEINTIOCHO")]


class Repo:
    def __init__(self, alias: dict | None = None) -> None:
        self.alias = alias or {}

    def find_empleado_alias(self, nombre):
        return self.alias.get((nombre or "").strip().upper())


def _proveedor(lookup=None, *, min_score=0.55) -> SigridMatcherProvider:
    return SigridMatcherProvider(
        lookup=lookup or Lookup(), empleado_min_score=min_score,
        obra_min_score=0.55, default_hora_normal_cod="HL01",
        default_hora_extra_cod=None)


def test_f030_proveedor_monta_las_fichas_de_recurso() -> None:
    matchers = _proveedor().get()
    recursos = matchers.recursos
    assert [f.ide for f in recursos.fichas_candidatas(None, HOY)] == \
        [950, 951]
    assert recursos.ficha(950).reside == 950
    assert recursos.elegir_ficha(CIF_P, 28, HOY).ide == 950
    # Las fichas de recurso no se mezclan con las de empleado ni el indice
    # de empleados cambia.
    assert matchers.indice.ficha(950) is None
    assert recursos.ficha(10) is None
    assert recursos.recursos == []
    assert [f.ide for f in matchers.indice.fichas_candidatas(None, HOY)] == \
        [10, 20]


def test_f030_proveedor_vacio_sin_fichas_de_recurso() -> None:
    class Caido(Lookup):
        def fetch_empresas(self):
            raise RuntimeError("sigrid-api caido")

    matchers = _proveedor(Caido()).get()
    assert matchers.recursos.fichas_candidatas(None, HOY) == []


# ======================= el casado: utilidades ========================== #

def _parte(*trabajadores, obra="0724", fecha=HOY) -> ParteDocumento:
    registros = [
        RegistroNormalizado(line_index=i, trabajador_nombre_leido=nombre,
                            trabajador_dni_leido=dni, tipo_hora="normal",
                            horas=8.0)
        for i, (nombre, dni) in enumerate(trabajadores)
    ]
    return ParteDocumento(fecha_int=fecha, obra_numero_leido=obra,
                          firmado=True, registros=registros)


def _pipeline(repo=None, lookup=None, **kw) -> PersistPartePipeline:
    return PersistPartePipeline(
        repository=repo or Repo(), normalizer=ParteNormalizer(),
        matcher_provider=_proveedor(lookup, **kw),
        hoy=lambda: date(2026, 9, 25))


def _casar(parte, repo=None, lookup=None, **kw) -> ParteDocumento:
    pipeline = _pipeline(repo, lookup, **kw)
    pipeline._match(parte)
    parte.review = PersistPartePipeline._compute_review_required(parte)  # type: ignore[attr-defined]
    return parte


def _emp(parte, i=0) -> EmpleadoMatch:
    return parte.registros[i].empleado


def _lookup_con(*recursos, empleados=FICHAS) -> Lookup:
    return Lookup(empleados=empleados, recursos=[REC_PG, REC_V, *recursos])


# ============================ R5 · por DNI ============================== #

def test_f030_r5_dni_de_una_ficha_de_recurso_casa_por_recurso() -> None:
    parte = _casar(_parte(("Nombre Ilegible", CIF_P)))
    emp = _emp(parte)
    assert (emp.method, emp.reside, emp.score) == ("recurso_dni", 950, 1.0)
    assert parte.empresa == 28


def test_f030_r5_dni_leido_sin_cero_por_el_normalizador() -> None:
    """R2 + R5: el papel dice 9876543-B y la ficha de recurso 09876543B."""
    datos = {"cabecera": {"fecha": "25/09/2026", "obra_numero": "0724"},
             "empleados": [{"nombre": "Nombre Ilegible", "dni": "9876543-B",
                            "horas_ordinarias": 8}]}
    parte = ParteNormalizer().normalize(datos, email_text="septiembre 2026")
    _pipeline()._match(parte)
    assert (_emp(parte).method, _emp(parte).reside) == ("recurso_dni", 950)


def test_f030_r5_el_dni_de_recurso_va_antes_que_el_alias() -> None:
    repo = Repo(alias={"PEDRO GOMEZ": {"ide": 10, "dni": DNI_E}})
    emp = _emp(_casar(_parte(("PEDRO GOMEZ", CIF_P)), repo=repo))
    assert (emp.method, emp.reside) == ("recurso_dni", 950)


def test_f030_r5_el_dni_de_recurso_va_antes_que_el_nombre() -> None:
    emp = _emp(_casar(_parte(("Pedro Gomez", CIF_P))))
    assert (emp.method, emp.reside) == ("recurso_dni", 950)


def test_f030_r5_sin_empresa_del_parte_compiten_todas() -> None:
    parte = _casar(_parte(("Nombre Ilegible", CIF_P), obra=None))
    assert parte.empresa is None
    assert (_emp(parte).method, _emp(parte).reside) == ("recurso_dni", 950)


def test_f030_r5_el_dni_de_una_ficha_de_empleado_sigue_casando_igual() -> None:
    emp = _emp(_casar(_parte(("Nombre Ilegible", DNI_E))))
    assert (emp.ide, emp.method, emp.reside) == (10, "dni", 900)


# ===================== R12 · lo que se guarda =========================== #

def test_f030_r12_el_casado_por_recurso_sin_ide_ni_codigo() -> None:
    cif_sigrid = "09876543-B"         # tal como esta en Sigrid
    lookup = _lookup_con(_rec(950, cif_sigrid, nombre="GOMEZ RUIZ, PEDRO"))
    emp = _emp(_casar(_parte(("Nombre Ilegible", CIF_P)), lookup=lookup))
    assert emp == EmpleadoMatch(ide=None, codigo=None,
                                nombre="GOMEZ RUIZ, PEDRO", dni=cif_sigrid,
                                reside=950, score=1.0, method="recurso_dni")


def test_f030_r12_se_guarda_en_las_columnas_de_siempre() -> None:
    """Por el repositorio real (SQLite en memoria): ninguna columna nueva."""
    from application.pipelines.persist_parte_pipeline import (
        PersistParteRequest,
    )
    from infrastructure.database.orm_models import ParteRegistroOrm
    from infrastructure.database.sqlalchemy_parte_repository import (
        SqlAlchemyParteRepository,
    )
    from tests.dobles import FabricaSesionSqlite

    fabrica = FabricaSesionSqlite()
    repo = SqlAlchemyParteRepository(fabrica)  # type: ignore[arg-type]
    datos = {"cabecera": {"fecha": "25/09/2026", "obra_numero": "0724"},
             "firma": {"firmado": True},
             "empleados": [{"nombre": "Nombre Ilegible", "dni": CIF_P,
                            "horas_ordinarias": 8}]}
    _pipeline(repo).run(PersistParteRequest(
        filename="p.pdf", mime_type="application/pdf", file_bytes=b"",
        extraction_envelope={"meta": {}, "data": datos},
        context={"document": {"sha256": "sha-f030"},
                 "email": {"subject": "septiembre 2026"}}))
    with fabrica.create_session() as s:
        (fila,) = s.query(ParteRegistroOrm).all()
        assert (fila.empleado_ide, fila.empleado_codigo, fila.empleado_dni,
                fila.empleado_nombre, fila.empleado_reside,
                fila.empleado_match_method, fila.empleado_match_score) == \
            (None, None, CIF_P, "GOMEZ RUIZ, PEDRO", 950, "recurso_dni", 1.0)


# ==================== R6 · ficha de recurso que no vale ================== #

def _lineas_r6(caplog) -> list[str]:
    return [m for m in caplog.messages if "ficha de recurso" in m]


def test_f030_r6_de_baja_sigue_por_el_nombre(caplog) -> None:
    lookup = _lookup_con(_rec(950, CIF_P, nombre="GOMEZ RUIZ, PEDRO",
                              fecbaj=20260901))
    with caplog.at_level(logging.INFO):
        emp = _emp(_casar(_parte(("Pedro Gomez", CIF_P)), lookup=lookup))
    assert (emp.ide, emp.method) == (10, "nombre")
    (linea,) = _lineas_r6(caplog)
    assert "solo_baja" in linea
    assert CIF_P not in caplog.text and "Pedro" not in caplog.text
    assert "GOMEZ" not in caplog.text


def test_f030_r6_de_otra_empresa_sigue_por_alias(caplog) -> None:
    repo = Repo(alias={"PEPE": {"ide": 11, "dni": "22222222J"}})
    ficha_1 = EmpleadoRow(ide=11, codigo="E11", nombre="JOSE UNO",
                          dni="22222222J", reside=None, empresa=1, fecbaj=0)
    lookup = Lookup(empleados=[*FICHAS, ficha_1])
    with caplog.at_level(logging.INFO):
        emp = _emp(_casar(_parte(("PEPE", CIF_P), obra="0300"), repo=repo,
                          lookup=lookup))
    assert (emp.ide, emp.method) == (11, "alias")
    (linea,) = _lineas_r6(caplog)
    assert "otra_empresa" in linea and CIF_P not in linea


def test_f030_r6_ambigua_sigue_y_se_loguea(caplog) -> None:
    lookup = _lookup_con(REC_P, _rec(952, CIF_P, nombre="GOMEZ RUIZ, PEDRO"))
    with caplog.at_level(logging.INFO):
        emp = _emp(_casar(_parte(("Pedro Gomez", CIF_P)), lookup=lookup))
    assert (emp.ide, emp.method) == (10, "nombre")
    (linea,) = _lineas_r6(caplog)
    assert "ambiguo" in linea


def test_f030_r6_desconocido_no_se_loguea(caplog) -> None:
    with caplog.at_level(logging.INFO):
        emp = _emp(_casar(_parte(("Pedro Gomez", "55555555K"))))
    assert (emp.ide, emp.method) == (10, "nombre")
    assert _lineas_r6(caplog) == []


def test_f030_r6_sin_dni_leido_no_se_mira_el_dni_de_recurso(caplog) -> None:
    with caplog.at_level(logging.INFO):
        emp = _emp(_casar(_parte(("Pedro Gomez", None))))
    assert (emp.ide, emp.method) == (10, "nombre")
    assert _lineas_r6(caplog) == []


# ============ R7 · DNI de ficha de empleado que no vale: igual ========== #

class _Prohibido:
    """Si el casado mira las fichas de recurso, el test lo dice."""

    def __getattr__(self, nombre):
        raise AssertionError(f"no se debe mirar recursos.{nombre}")


def _casar_sin_recursos(parte, lookup=None) -> ParteDocumento:
    pipeline = _pipeline(None, lookup)
    pipeline._matcher_provider.get().recursos = _Prohibido()  # type: ignore[union-attr]
    pipeline._match(parte)
    return parte


@pytest.mark.parametrize("obra, empleados, metodo", [
    # De baja a la fecha (y un `MO/` con su DNI que NO es ficha de recurso).
    ("0724", [EmpleadoRow(ide=10, codigo="E10", nombre="PEDRO GOMEZ",
                          dni=DNI_E, reside=900, empresa=28,
                          fecbaj=20260901)], "dni_solo_baja"),
    # De alta solo en otra empresa.
    ("0300", FICHAS, "dni_otra_empresa"),
    # Dos fichas de alta en la empresa del parte.
    ("0724", [FICHA_PG, EmpleadoRow(ide=12, codigo="E12", nombre="P G",
                                    dni=DNI_E, reside=None, empresa=28,
                                    fecbaj=0)], "dni_ambiguo"),
])
def test_f030_r7_no_se_mira_ninguna_ficha_de_recurso(obra, empleados,
                                                     metodo) -> None:
    lookup = Lookup(empleados=empleados,
                    recursos=[*RECURSOS, _rec(960, DNI_E)])
    parte = _casar_sin_recursos(_parte(("Pedro Gomez Ruiz", DNI_E),
                                       obra=obra), lookup)
    assert (_emp(parte).ide, _emp(parte).method) == (None, metodo)


# ======================= R8 · alias solo de fichas ====================== #

def test_f030_r8_el_alias_de_una_ficha_se_aplica_como_hoy() -> None:
    repo = Repo(alias={"PEPE": {"ide": 10, "dni": DNI_E}})
    emp = _emp(_casar(_parte(("PEPE", None)), repo=repo))
    assert (emp.ide, emp.method, emp.reside) == (10, "alias", 900)


def test_f030_r8_no_hay_alias_de_recurso() -> None:
    repo = Repo(alias={"PEPITO": {"ide": 950, "dni": CIF_P}})
    emp = _emp(_casar(_parte(("PEPITO", None)), repo=repo))
    assert (emp.ide, emp.reside, emp.method) == (None, None,
                                                 "alias_no_valido")


def test_f030_r8_el_alias_va_antes_que_el_nombre_del_recurso() -> None:
    repo = Repo(alias={"PEDRO GOMEZ RUIZ": {"ide": 10, "dni": DNI_E}})
    emp = _emp(_casar(_parte(("Pedro Gomez Ruiz", None)), repo=repo))
    assert (emp.ide, emp.method) == (10, "alias")
