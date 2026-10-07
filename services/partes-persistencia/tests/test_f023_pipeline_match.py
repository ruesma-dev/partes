# tests/test_f023_pipeline_match.py
"""F-023 · R6-R24: el casado de la ingesta en sv3 (`PersistPartePipeline`).

Orden del casado (design §5.3): fecha de referencia (R16) -> empresa del
membrete (R7-R8) -> discriminantes por los recursos de alta de los
trabajadores -> obra (R9-R14) -> empresa del parte (R15) -> trabajador
(R17-R24). `review_required` sube con la obra sin casar por empresa o por
ambiguedad y, como siempre, con cualquier trabajador sin casar (R22).

El proveedor de matchers es el REAL (`SigridMatcherProvider`) sobre un
Sigrid en memoria: se prueba tambien que carga recursos y empresas. Todo
son datos SINTETICOS.
"""
from __future__ import annotations

import logging
from datetime import date

import pytest

from application.pipelines.persist_parte_pipeline import (
    PersistPartePipeline,
    PersistParteRequest,
)
from application.services.parte_normalizer import ParteNormalizer
from application.services.sigrid_matcher_provider import SigridMatcherProvider
from domain.models.parte_records import ParteDocumento, RegistroNormalizado
from domain.models.sigrid_models import (
    EmpleadoRow,
    EmpresaRow,
    ObraRow,
    TipoHoraRow,
)
from tests.dobles import recurso_persona

HOY = 20260915
DNI_A = "11111111H"      # una ficha, empresa 1
DNI_B = "22222222J"      # una ficha, empresa 28
DNI_C = "33333333P"      # dos fichas: empresa 1 y empresa 28
DNI_D = "44444444A"      # ficha de baja

O1 = ObraRow(ide=100, codigo="0100", nombre="Residencial Norte", empresa=1)
O28 = ObraRow(ide=200, codigo="0100", nombre="Nave Sur", empresa=28)
OU = ObraRow(ide=300, codigo="0300", nombre="Colegio Este", empresa=1)
O4 = ObraRow(ide=400, codigo="0400", nombre="Puerto Oeste", empresa=28)

FICHAS = [
    EmpleadoRow(ide=10, codigo="E10", nombre="ANA UNO", dni=DNI_A,
                reside=910, empresa=1, fecbaj=0),
    EmpleadoRow(ide=20, codigo="E20", nombre="BEA VEINTIOCHO", dni=DNI_B,
                reside=920, empresa=28, fecbaj=0),
    EmpleadoRow(ide=30, codigo="E30", nombre="CARLOS DOS", dni=DNI_C,
                reside=930, empresa=1, fecbaj=0),
    EmpleadoRow(ide=31, codigo="E31", nombre="CARLOS DOS", dni=DNI_C,
                reside=931, empresa=28, fecbaj=0),
    EmpleadoRow(ide=40, codigo="E40", nombre="DIANA BAJA", dni=DNI_D,
                reside=None, empresa=1, fecbaj=20260920),
]
RECURSOS = [
    recurso_persona(ide=910, cif=None, conide=10, empresa=1, fecbaj=0),
    recurso_persona(ide=920, cif=None, conide=20, empresa=28, fecbaj=0),
    recurso_persona(ide=930, cif=None, conide=30, empresa=1, fecbaj=0),
    recurso_persona(ide=931, cif=None, conide=31, empresa=28, fecbaj=0),
]
EMPRESAS = [EmpresaRow(numemp=1, nombre="UNO"),
            EmpresaRow(numemp=28, nombre="VEINTIOCHO")]
TIPOS = [
    TipoHoraRow(ide=1, codigo="HL01", descripcion="Hora laborable", ext=0,
                pre=None, prenom=None),
    TipoHoraRow(ide=2, codigo="HE01", descripcion="Hora extra", ext=1,
                pre=None, prenom=None),
]


class LookupIngesta:
    """Los maestros que el proveedor carga, en memoria."""

    def __init__(self, *, empleados=FICHAS, obras=(O1, O28, OU, O4),
                 recursos=RECURSOS, empresas=EMPRESAS) -> None:
        self.empleados = list(empleados)
        self.obras = list(obras)
        self.recursos = list(recursos)
        self.empresas = list(empresas)

    def fetch_empleados(self):
        return list(self.empleados)

    def fetch_obras(self):
        return list(self.obras)

    def fetch_tipos_hora(self):
        return list(TIPOS)

    def fetch_recursos(self):
        return list(self.recursos)

    def fetch_empresas(self):
        return list(self.empresas)


class RepoIngesta:
    """Lo que la ingesta pide al repositorio."""

    def __init__(self, alias: dict | None = None) -> None:
        self.alias = alias or {}
        self.guardados: list[dict] = []

    def get_by_sha256(self, _sha):
        return None

    def find_empleado_alias(self, nombre):
        return self.alias.get((nombre or "").strip().upper())

    def save_parte(self, **kwargs) -> None:
        self.guardados.append(kwargs)


def _pipeline(repo=None, lookup=None, *, hoy=date(2026, 9, 15)):
    proveedor = SigridMatcherProvider(
        lookup=lookup or LookupIngesta(), empleado_min_score=0.55,
        obra_min_score=0.55, default_hora_normal_cod="HL01",
        default_hora_extra_cod="HE01",
        alias_empresas={1: ["RUESMA"], 28: ["PORSAN"]},
    )
    return PersistPartePipeline(
        repository=repo or RepoIngesta(), normalizer=ParteNormalizer(),
        matcher_provider=proveedor, hoy=lambda: hoy,
    )


def _parte(*trabajadores, obra="100", nombre_obra=None, membrete=None,
           fecha=HOY) -> ParteDocumento:
    registros = [
        RegistroNormalizado(line_index=i, trabajador_nombre_leido=nombre,
                            trabajador_dni_leido=dni, tipo_hora="normal",
                            horas=8.0)
        for i, (nombre, dni) in enumerate(trabajadores)
    ]
    return ParteDocumento(
        fecha_int=fecha, obra_numero_leido=obra,
        obra_nombre_leido=nombre_obra, empresa_membrete=membrete,
        firmado=True, registros=registros)


def _casar(parte, repo=None, lookup=None, **kw) -> ParteDocumento:
    pipeline = _pipeline(repo, lookup, **kw)
    pipeline._match(parte)
    parte.review = pipeline._compute_review_required(parte)   # type: ignore[attr-defined]
    return parte


# ====================== R9-R15 · obra y empresa del parte ================ #

def test_f023_r9_r15_el_membrete_elige_la_gemela_y_da_la_empresa() -> None:
    parte = _casar(_parte(("BEA VEINTIOCHO", DNI_B), membrete="PORSAN S.L."))
    assert (parte.obra.ide, parte.obra.method, parte.obra.empresa) == \
        (200, "codigo_membrete", 28)
    assert (parte.empresa, parte.empresa_origen) == (28, "membrete")
    assert parte.review is False


def test_f023_r10_membrete_de_otra_empresa_obra_sin_casar_y_revision() -> None:
    parte = _casar(_parte(("ANA UNO", DNI_A), obra="300", membrete="PORSAN"))
    assert parte.obra.ide is None
    assert parte.obra.method == "codigo_otra_empresa"
    # R15: sin obra, la empresa del parte es la del membrete.
    assert (parte.empresa, parte.empresa_origen) == (28, "membrete")
    assert parte.review is True


def test_f023_r11_r15_sin_membrete_deciden_los_trabajadores() -> None:
    parte = _casar(_parte(("BEA VEINTIOCHO", DNI_B)))
    assert (parte.obra.ide, parte.obra.method) == (200, "codigo_trabajadores")
    assert (parte.empresa, parte.empresa_origen) == (28, "trabajadores")
    assert parte.registros[0].empleado.ide == 20


def test_f023_r12_r15_quien_esta_en_las_dos_no_discrimina_y_decide_el_nombre(
) -> None:
    parte = _casar(_parte(("CARLOS DOS", DNI_C), nombre_obra="nave sur"))
    assert (parte.obra.ide, parte.obra.method) == (200, "codigo_nombre")
    assert (parte.empresa, parte.empresa_origen) == (28, "nombre")
    assert parte.registros[0].empleado.ide == 31


def test_f023_r13_discriminantes_que_discrepan_obra_ambigua() -> None:
    parte = _casar(_parte(("ANA UNO", DNI_A), ("BEA VEINTIOCHO", DNI_B),
                          nombre_obra="Nave Sur"))
    assert (parte.obra.ide, parte.obra.method) == (None, "codigo_ambiguo")
    assert (parte.empresa, parte.empresa_origen) == (None, None)
    assert parte.review is True


def test_f023_r15_obra_unica_da_su_empresa() -> None:
    parte = _casar(_parte(("ANA UNO", DNI_A), obra="0300"))
    assert (parte.obra.ide, parte.obra.method) == (300, "codigo")
    assert (parte.empresa, parte.empresa_origen) == (1, "obra")
    assert parte.review is False


def test_f023_r15_obra_con_membrete_que_la_confirma() -> None:
    parte = _casar(_parte(("ANA UNO", DNI_A), obra="0300", membrete="RUESMA"))
    assert (parte.obra.ide, parte.obra.method) == (300, "codigo")
    assert parte.obra.score == 1.0
    assert (parte.empresa, parte.empresa_origen) == (1, "membrete")


def test_f023_r15_obra_padded_da_su_empresa() -> None:
    parte = _casar(_parte(("ANA UNO", DNI_A), obra="0300"))
    assert parte.obra.method == "codigo"
    padded = _casar(_parte(("ANA UNO", DNI_A), obra="00300"))
    assert (padded.obra.ide, padded.obra.method) == (300, "codigo_padded")
    assert padded.obra.score == 0.98
    assert (padded.empresa, padded.empresa_origen) == (1, "obra")


def test_f023_r15_una_variante_sin_ceros_tambien_es_padded() -> None:
    """Sigrid '77' y el parte '077': la variante sin ceros (la segunda que
    se prueba) tambien cuenta como codigo con ceros."""
    corta = ObraRow(ide=700, codigo="77", nombre="Corta", empresa=1)
    parte = _casar(_parte(("ANA UNO", DNI_A), obra="077"),
                   lookup=LookupIngesta(obras=[corta]))
    assert (parte.obra.ide, parte.obra.method) == (700, "codigo_padded")


def test_f023_r15_obra_sin_empresa_en_sigrid_deja_la_empresa_vacia() -> None:
    sin_emp = ObraRow(ide=500, codigo="0500", nombre="Rara", empresa=None)
    parte = _casar(_parte(("ANA UNO", DNI_A), obra="500"),
                   lookup=LookupIngesta(obras=[sin_emp]))
    assert parte.obra.ide == 500
    assert (parte.empresa, parte.empresa_origen) == (None, None)


def test_f023_r14_sin_codigo_el_nombre_se_limita_a_la_empresa_del_membrete(
) -> None:
    parte = _casar(_parte(("ANA UNO", DNI_A), obra=None,
                          nombre_obra="Puerto Oeste", membrete="RUESMA"))
    assert (parte.obra.ide, parte.obra.method) == (None, "none")
    libre = _casar(_parte(("BEA VEINTIOCHO", DNI_B), obra=None,
                          nombre_obra="Puerto Oeste"))
    assert (libre.obra.ide, libre.obra.method) == (400, "nombre")
    assert (libre.empresa, libre.empresa_origen) == (28, "nombre")


def test_f023_r14_un_codigo_que_no_existe_cae_al_nombre() -> None:
    parte = _casar(_parte(("ANA UNO", DNI_A), obra="999",
                          nombre_obra="Colegio Este"))
    assert (parte.obra.ide, parte.obra.method) == (300, "nombre")


def test_f023_r14_empate_por_nombre_es_nombre_ambiguo_y_revision() -> None:
    iguales = [ObraRow(ide=100, codigo="0100", nombre="Mismo", empresa=1),
               ObraRow(ide=200, codigo="0200", nombre="Mismo", empresa=28)]
    parte = _casar(_parte(("ANA UNO", DNI_A), obra=None, nombre_obra="Mismo"),
                   lookup=LookupIngesta(obras=iguales))
    assert (parte.obra.ide, parte.obra.method) == (None, "nombre_ambiguo")
    assert parte.review is True


def test_f023_r8_membrete_desconocido_se_loguea_y_sigue_sin_el(caplog) -> None:
    with caplog.at_level(logging.INFO):
        parte = _casar(_parte(("ANA UNO", DNI_A), obra="300",
                              membrete="Logo irreconocible"))
    assert "Logo irreconocible" in caplog.text
    assert (parte.obra.ide, parte.empresa, parte.empresa_origen) == \
        (300, 1, "obra")


# ============================ R16 · fecha ============================== #

def test_f023_r16_la_fecha_de_referencia_es_la_del_parte() -> None:
    parte = _casar(_parte(("DIANA BAJA", DNI_D), obra="300"),
                   hoy=date(2026, 10, 1))
    assert parte.registros[0].empleado.ide == 40      # de alta el 15-09


def test_f023_r16_sin_fecha_valida_se_usa_hoy() -> None:
    parte = _casar(_parte(("DIANA BAJA", DNI_D), obra="300", fecha=None),
                   hoy=date(2026, 10, 1))
    assert parte.registros[0].empleado.method == "dni_solo_baja"
    antes = _casar(_parte(("DIANA BAJA", DNI_D), obra="300", fecha=0),
                   hoy=date(2026, 9, 1))
    assert antes.registros[0].empleado.ide == 40


# ================== R17-R22 · el trabajador por DNI ==================== #

def test_f023_r17_r18_una_ficha_de_alta_en_la_empresa_del_parte() -> None:
    parte = _casar(_parte(("carlos", DNI_C), membrete="PORSAN"))
    emp = parte.registros[0].empleado
    assert (emp.ide, emp.method, emp.reside, emp.dni) == (31, "dni", 931,
                                                           DNI_C)


def test_f023_r19_r22_dos_fichas_sin_empresa_dni_ambiguo_sin_seguir(
) -> None:
    """Sin empresa del parte compiten todas: dos fichas -> sin casar, y NO
    se sigue al alias ni al nombre aunque ambos casarian."""
    repo = RepoIngesta(alias={"CARLOS DOS": {
        "ide": 30, "codigo": "E30", "nombre": "CARLOS DOS", "dni": DNI_C}})
    parte = _casar(_parte(("CARLOS DOS", DNI_C), obra=None), repo=repo)
    assert parte.registros[0].empleado.ide is None
    assert parte.registros[0].empleado.method == "dni_ambiguo"
    assert parte.review is True


def test_f023_r20_solo_fichas_de_baja() -> None:
    parte = _casar(_parte(("DIANA BAJA", DNI_D), obra="300",
                          fecha=20260921))
    assert parte.registros[0].empleado.method == "dni_solo_baja"
    assert parte.registros[0].empleado.ide is None
    assert parte.review is True


def test_f023_r21_de_alta_solo_en_otra_empresa() -> None:
    parte = _casar(_parte(("BEA VEINTIOCHO", DNI_B), obra="300"))
    assert parte.registros[0].empleado.method == "dni_otra_empresa"
    assert parte.review is True


def test_f023_r22_el_mismo_trabajador_se_casa_una_vez_por_parte() -> None:
    parte = _parte(("ANA UNO", DNI_A), ("ANA UNO", DNI_A), obra="300")
    _casar(parte)
    assert parte.registros[0].empleado is parte.registros[1].empleado


# ======================= R23 · alias aprendidos ========================= #

def _alias(ide, dni):
    return {"ide": ide, "codigo": f"E{ide}", "nombre": "ALIAS", "dni": dni}


def test_f023_r23_alias_de_una_ficha_candidata_casa() -> None:
    repo = RepoIngesta(alias={"ANITA": _alias(10, DNI_A)})
    parte = _casar(_parte(("ANITA", None), obra="300"), repo=repo)
    emp = parte.registros[0].empleado
    assert (emp.ide, emp.method, emp.reside) == (10, "alias", 910)


def test_f023_r23_alias_fuera_de_r17_se_resuelve_por_su_dni() -> None:
    """El alias apunta a la ficha de la 1; el parte es de la 28: vale la
    ficha de la 28 de la misma persona."""
    repo = RepoIngesta(alias={"CARLITOS": _alias(30, DNI_C)})
    parte = _casar(_parte(("CARLITOS", None), membrete="PORSAN"), repo=repo)
    emp = parte.registros[0].empleado
    assert (emp.ide, emp.method) == (31, "alias")


def test_f023_r23_alias_fuera_de_r17_con_dni_de_otra_empresa() -> None:
    repo = RepoIngesta(alias={"BEITA": _alias(20, DNI_B)})
    parte = _casar(_parte(("BEITA", None), obra="300"), repo=repo)
    assert parte.registros[0].empleado.method == "dni_otra_empresa"


def test_f023_r23_alias_sin_dni_fuera_de_r17_no_es_valido() -> None:
    repo = RepoIngesta(alias={"BEITA": _alias(20, None)})
    parte = _casar(_parte(("BEITA", None), obra="300"), repo=repo)
    assert parte.registros[0].empleado.ide is None
    assert parte.registros[0].empleado.method == "alias_no_valido"
    assert parte.review is True


def test_f023_r23_alias_con_dni_desconocido_no_es_valido() -> None:
    repo = RepoIngesta(alias={"FANTASMA": _alias(99, "99999999R")})
    parte = _casar(_parte(("FANTASMA", None), obra="300"), repo=repo)
    assert parte.registros[0].empleado.method == "alias_no_valido"


def test_f023_r23_el_dni_leido_manda_sobre_el_alias() -> None:
    repo = RepoIngesta(alias={"ANA UNO": _alias(30, DNI_C)})
    parte = _casar(_parte(("ANA UNO", DNI_A), obra="300"), repo=repo)
    assert parte.registros[0].empleado.ide == 10


# ======================= R24 · similitud de nombre ====================== #

def test_f023_r24_el_nombre_casa_contra_las_fichas_de_r17() -> None:
    parte = _casar(_parte(("Ana Uno", None), obra="300"))
    emp = parte.registros[0].empleado
    assert (emp.ide, emp.method) == (10, "nombre")


def test_f023_r24_una_ficha_de_otra_empresa_no_compite() -> None:
    parte = _casar(_parte(("Bea Veintiocho", None), obra="300"))
    assert parte.registros[0].empleado.ide is None
    assert parte.registros[0].empleado.method == "none"


def test_f023_r24_la_mejor_es_de_un_dni_con_varias_fichas() -> None:
    parte = _casar(_parte(("Carlos Dos", None), obra=None))
    assert parte.registros[0].empleado.method == "nombre_ambiguo"
    assert parte.review is True


def test_f023_r24_empate_con_otra_persona() -> None:
    gemelos = [
        EmpleadoRow(ide=50, codigo="E50", nombre="PEPE IGUAL", dni="55555555K",
                    reside=None, empresa=1, fecbaj=0),
        EmpleadoRow(ide=60, codigo="E60", nombre="PEPE IGUAL", dni="66666666Q",
                    reside=None, empresa=1, fecbaj=0),
    ]
    parte = _casar(_parte(("Pepe Igual", None), obra="300"),
                   lookup=LookupIngesta(empleados=gemelos))
    assert parte.registros[0].empleado.method == "nombre_ambiguo"


def test_f023_r24_empate_entre_fichas_sin_dni_de_personas_distintas() -> None:
    sin_dni = [
        EmpleadoRow(ide=50, codigo="E50", nombre="PEPE IGUAL", dni=None,
                    reside=None, empresa=1, fecbaj=0),
        EmpleadoRow(ide=60, codigo="E60", nombre="PEPE IGUAL", dni=None,
                    reside=None, empresa=1, fecbaj=0),
    ]
    parte = _casar(_parte(("Pepe Igual", None), obra="300"),
                   lookup=LookupIngesta(empleados=sin_dni))
    assert parte.registros[0].empleado.method == "nombre_ambiguo"


def test_f023_r24_una_sola_ficha_sin_dni_casa_por_nombre() -> None:
    sin_dni = [EmpleadoRow(ide=50, codigo="E50", nombre="PEPE UNICO",
                           dni=None, reside=None, empresa=1, fecbaj=0)]
    parte = _casar(_parte(("Pepe Unico", None), obra="300"),
                   lookup=LookupIngesta(empleados=sin_dni))
    emp = parte.registros[0].empleado
    assert (emp.ide, emp.method) == (50, "nombre")


def test_f023_r24_por_debajo_del_umbral_no_casa() -> None:
    parte = _casar(_parte(("Xiomara Zeta", None), obra="300"))
    assert parte.registros[0].empleado.method == "none"


def test_f023_r24_el_umbral_se_alcanza_con_la_puntuacion_justa() -> None:
    """Nombre identico puntua 1.0: con umbral 1.0 casa (>=)."""
    proveedor = SigridMatcherProvider(
        lookup=LookupIngesta(), empleado_min_score=1.0, obra_min_score=0.55,
        default_hora_normal_cod="HL01", default_hora_extra_cod="HE01")
    pipeline = PersistPartePipeline(
        repository=RepoIngesta(), normalizer=ParteNormalizer(),
        matcher_provider=proveedor, hoy=lambda: date(2026, 9, 15))
    parte = _parte(("ANA UNO", None), obra="300")
    pipeline._match(parte)
    assert parte.registros[0].empleado.ide == 10


def test_f023_r24_sin_nombre_leido_no_casa() -> None:
    parte = _casar(_parte((None, None), obra="300"))
    assert parte.registros[0].empleado.method == "none"


# ====================== review_required y persistencia ================== #

@pytest.mark.parametrize("metodo, esperado", [
    ("codigo_otra_empresa", True), ("codigo_ambiguo", True),
    ("nombre_ambiguo", True), ("codigo", False), ("none", False),
])
def test_f023_review_required_por_la_obra(metodo, esperado) -> None:
    parte = _parte(("ANA UNO", DNI_A), obra="300")
    _pipeline()._match(parte)
    parte.obra.method = metodo
    assert PersistPartePipeline._compute_review_required(parte) is esperado


def test_f023_r6_r15_run_guarda_membrete_empresa_y_origen() -> None:
    repo = RepoIngesta()
    datos = {
        "cabecera": {"fecha": "15/09/2026", "obra_numero": "100",
                     "empresa_membrete": "PORSAN E HIJOS"},
        "firma": {"firmado": True},
        "empleados": [{"nombre": "BEA VEINTIOCHO", "dni": DNI_B,
                       "horas_ordinarias": 8}],
    }
    resultado = _pipeline(repo).run(PersistParteRequest(
        filename="p.pdf", mime_type="application/pdf", file_bytes=b"",
        extraction_envelope={"meta": {}, "data": datos},
        context={"document": {"sha256": "sha-f023"},
                 "email": {"subject": "parte septiembre 2026"}}))
    (guardado,) = repo.guardados
    parte = guardado["parte"]
    assert (parte.empresa_membrete, parte.empresa, parte.empresa_origen) == \
        ("PORSAN E HIJOS", 28, "membrete")
    assert parte.obra.ide == 200
    assert guardado["review_required"] is False
    assert resultado.obra_codigo == "0100"


# ============================ el proveedor ============================== #

def test_f023_el_proveedor_carga_indice_y_empresas() -> None:
    proveedor = SigridMatcherProvider(
        lookup=LookupIngesta(), empleado_min_score=0.55, obra_min_score=0.55,
        default_hora_normal_cod="HL01", default_hora_extra_cod="HE01",
        alias_empresas={28: ["PORSAN"]})
    matchers = proveedor.get()
    assert matchers.indice.empresas_con_recurso(DNI_C, HOY) == \
        frozenset({1, 28})
    assert matchers.indice.empresa_de_obra(200) == 28
    assert matchers.empresas.resolver("porsan") == (28, "membrete")
    assert proveedor.indice() is matchers.indice


def test_f023_el_proveedor_vacio_no_casa_nada() -> None:
    class Caido(LookupIngesta):
        def fetch_empresas(self):
            raise RuntimeError("sigrid-api caido")

    proveedor = SigridMatcherProvider(
        lookup=Caido(), empleado_min_score=0.55, obra_min_score=0.55,
        default_hora_normal_cod="HL01", default_hora_extra_cod="HE01",
        alias_empresas={28: ["PORSAN"]})
    matchers = proveedor.get()
    assert matchers.indice.recursos == []
    assert matchers.empresas.resolver("PORSAN") == (None, "empresa_no_valida")


def test_f023_r24_la_otra_ficha_del_mismo_dni_tambien_cuenta_aunque_puntue_menos(
) -> None:
    """R24: «la mejor es de un DNI con varias fichas en R17», aunque la otra
    ficha se llame distinto: la persona tiene dos fichas y no se elige."""
    dos_fichas = [
        EmpleadoRow(ide=30, codigo="E30", nombre="CARLOS DOS", dni=DNI_C,
                    reside=None, empresa=1, fecbaj=0),
        EmpleadoRow(ide=32, codigo="E32", nombre="NOMBRE DISTINTO", dni=DNI_C,
                    reside=None, empresa=1, fecbaj=0),
    ]
    parte = _casar(_parte(("Carlos Dos", None), obra="0300"),
                   lookup=LookupIngesta(empleados=dos_fichas))
    assert parte.registros[0].empleado.method == "nombre_ambiguo"


def test_f023_r24_sin_fichas_candidatas_no_casa() -> None:
    parte = _casar(_parte(("Ana Uno", None), obra="0300"),
                   lookup=LookupIngesta(empleados=[]))
    assert parte.registros[0].empleado.method == "none"
    assert parte.registros[0].empleado.ide is None
