# tests/test_f023_recurso_conciliador.py
"""F-023 · R25-R31: el recurso de cada linea en la conciliacion de sv3.

Antes, `_resuelve_recurso` tomaba `empleado_reside` (el `emp.reside` de la
ficha) ANTES que nada y nunca miraba la baja ni la empresa. El caso guia:
la ficha de alta apunta a un recurso de baja desde 2021 y la misma persona
tiene otro recurso de alta en la misma empresa; se imputaba el de baja.

Ahora los candidatos de una linea son los recursos de la persona casada,
de alta a la FECHA DE LA LINEA, de la empresa de su obra (sin obra, la del
parte; sin ninguna, cualquiera). `empleado_reside` solo desempata ENTRE
candidatos (R26-R27). Las lineas congeladas no cambian de recurso (R30) y
las demas se re-resuelven en cada pasada (R31).

Todo SINTETICO; el indice llega por `indice_provider`, como en produccion.
"""
from __future__ import annotations

import logging
from datetime import date

from application.services.recurso_conciliador import RecursoConciliador
from application.services.seleccion_sigrid import IndicePersonas
from domain.models.sigrid_models import (
    EmpleadoRow,
    HmoRow,
    ObraRow,
    RecursoRow,
)
from infrastructure.database.orm_models import ParteDocumentOrm
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests.dobles import (
    FabricaSesionSqlite,
    LookupFake,
    RepositorioFake,
    registro,
    reshor_par,
    sembrar_lineas,
)

DNI = "12345678Z"
FECHA = 20260915          # martes

FICHAS = [
    EmpleadoRow(ide=10, codigo="E10", nombre="P", dni=DNI, reside=900,
                empresa=1, fecbaj=0),
    EmpleadoRow(ide=11, codigo="E11", nombre="P", dni=DNI, reside=902,
                empresa=31, fecbaj=0),
]
BAJA_2021 = RecursoRow(ide=900, cif=None, conide=10, empresa=1,
                       fecbaj=20210126)
ALTA_1 = RecursoRow(ide=901, cif=DNI, conide=None, empresa=1, fecbaj=0)
ALTA_31 = RecursoRow(ide=902, cif=None, conide=11, empresa=31, fecbaj=0)
OBRAS = [ObraRow(ide=100, codigo="0100", nombre="Uno", empresa=1),
         ObraRow(ide=300, codigo="0300", nombre="Treintayuno", empresa=31)]


def _indice(recursos=(BAJA_2021, ALTA_1, ALTA_31), fichas=FICHAS,
            obras=OBRAS) -> IndicePersonas:
    return IndicePersonas(fichas, recursos, obras)


def _linea(rid=1, *, obra_ide=100, fecha=FECHA, reside=900, emp_ide=10,
           doc="doc-1", **extra) -> dict:
    r = registro(rid, fecha_int=fecha, horas=8.0, dni=DNI,
                 document_id=doc, obra_ide=obra_ide)
    r.update(empleado_reside=reside, empleado_ide=emp_ide, **extra)
    return r


def _conciliar(registros, indice=None, *, hmo=None, hoy=date(2026, 9, 15)):
    repo = RepositorioFake(registros)
    indice = indice or _indice()
    conciliador = RecursoConciliador(
        repository=repo,
        lookup=LookupFake(reshor=reshor_par(901) + reshor_par(902),
                          hmo=hmo or {}),
        indice_provider=lambda: indice,
        hoy=lambda: hoy,
    )
    resumen = conciliador.conciliar_todos()
    return repo, resumen


def _update(repo, rid) -> dict:
    return next(u for u in repo.matches if u["registro_id"] == rid)


# ======================= R25-R27 · el caso guia ======================== #

def test_f023_r25_r27_caso_guia_se_imputa_el_recurso_de_alta() -> None:
    hmo = {100: [HmoRow(ide=5000, reside=901, ano=2026, mes=9),
                 HmoRow(ide=4000, reside=900, ano=2026, mes=9)]}
    repo, resumen = _conciliar([_linea()], hmo=hmo)
    u = _update(repo, 1)
    assert (u["recurso_ide"], u["hmo_ide"], u["parte_estado"]) == \
        (901, 5000, "ok")
    assert repo.review_required == []
    assert resumen["con_parte"] == 1


def test_f023_r27_sin_recurso_de_alta_en_la_empresa_no_se_usa_el_reside(
        caplog) -> None:
    """Solo el de baja (900, el `reside` de la ficha) y el de la 31: la
    linea queda sin recurso, con WARNING y el parte a revision (R29)."""
    with caplog.at_level(logging.WARNING):
        repo, resumen = _conciliar(
            [_linea()], _indice(recursos=(BAJA_2021, ALTA_31)))
    u = _update(repo, 1)
    assert (u["recurso_ide"], u["parte_estado"]) == (None, "sin_recurso")
    assert repo.review_required == [["doc-1"]]
    assert resumen["partes_sin_recurso"] == 1
    assert "otra_empresa" in caplog.text


def test_f023_r29_solo_recursos_de_baja(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        repo, _ = _conciliar([_linea()], _indice(recursos=(BAJA_2021,)))
    assert _update(repo, 1)["parte_estado"] == "sin_recurso"
    assert repo.review_required == [["doc-1"]]
    assert "solo_baja" in caplog.text


def test_f023_r29_ambiguo_queda_sin_recurso_y_a_revision(caplog) -> None:
    otro = RecursoRow(ide=903, cif=DNI, conide=None, empresa=1, fecbaj=0)
    with caplog.at_level(logging.WARNING):
        repo, _ = _conciliar([_linea(reside=None, emp_ide=None)],
                             _indice(recursos=(ALTA_1, otro)))
    u = _update(repo, 1)
    assert (u["recurso_ide"], u["parte_estado"]) == (None, "sin_recurso")
    assert repo.review_required == [["doc-1"]]
    assert "ambiguo" in caplog.text


def test_f023_r29_persona_sin_recursos_no_va_a_revision() -> None:
    """Sin ningun recurso (antes tambien era `sin_recurso`): no es un caso
    de baja ni de otra empresa, asi que no sube `review_required`."""
    repo, resumen = _conciliar([_linea()], _indice(recursos=()))
    assert _update(repo, 1)["parte_estado"] == "sin_recurso"
    assert repo.review_required == []
    assert resumen["partes_sin_recurso"] == 0


def test_f023_r29_cada_parte_se_marca_una_vez() -> None:
    repo, _ = _conciliar(
        [_linea(1), _linea(2, doc="doc-2"), _linea(3)],
        _indice(recursos=(BAJA_2021,)))
    assert repo.review_required == [["doc-1", "doc-2"]]


def test_f023_r28_se_loguea_cuantos_recursos_se_descartaron(caplog) -> None:
    with caplog.at_level(logging.INFO):
        _conciliar([_linea()])
    linea = next(m for m in caplog.messages if "descartado" in m)
    assert "2 recurso(s) descartado(s)" in linea
    assert "baja=1" in linea and "otra empresa=1" in linea


def test_f023_r28_un_solo_descarte_tambien_se_loguea(caplog) -> None:
    with caplog.at_level(logging.INFO):
        _conciliar([_linea()], _indice(recursos=(BAJA_2021, ALTA_1)))
    linea = next(m for m in caplog.messages if "descartado" in m)
    assert "1 recurso(s) descartado(s)" in linea
    assert "baja=1" in linea and "otra empresa=0" in linea


def test_f023_r28_sin_descartes_no_hay_ese_log(caplog) -> None:
    with caplog.at_level(logging.INFO):
        _conciliar([_linea()], _indice(recursos=(ALTA_1,)))
    assert not [m for m in caplog.messages if "descartado" in m]


# ================ R25 · empresa y fecha de cada linea ================== #

def test_f023_r25_la_empresa_es_la_de_la_obra_de_la_linea() -> None:
    repo, _ = _conciliar([_linea(obra_ide=300)])
    assert _update(repo, 1)["recurso_ide"] == 902


def test_f023_r25_sin_obra_vale_la_empresa_del_parte() -> None:
    repo, _ = _conciliar([_linea(obra_ide=None, parte_empresa=31)])
    u = _update(repo, 1)
    assert (u["recurso_ide"], u["parte_estado"]) == (902, "sin_parte")


def test_f023_r25_obra_fuera_del_maestro_vale_la_empresa_del_parte() -> None:
    repo, _ = _conciliar([_linea(obra_ide=777, parte_empresa=31)])
    assert _update(repo, 1)["recurso_ide"] == 902


def test_f023_r25_sin_obra_ni_empresa_compiten_todas() -> None:
    repo, _ = _conciliar([_linea(obra_ide=None)],
                         _indice(recursos=(BAJA_2021, ALTA_31)))
    assert _update(repo, 1)["recurso_ide"] == 902


def test_f023_r25_la_baja_se_mira_a_la_fecha_de_la_linea() -> None:
    baja_agosto = RecursoRow(ide=901, cif=DNI, conide=None, empresa=1,
                             fecbaj=20260801)
    indice = _indice(recursos=(baja_agosto,))
    repo, _ = _conciliar([_linea(1, fecha=20260731),
                          _linea(2, fecha=20260801)], indice)
    assert _update(repo, 1)["recurso_ide"] == 901
    assert _update(repo, 2)["recurso_ide"] is None


def test_f023_r25_una_linea_sin_fecha_usa_hoy() -> None:
    baja_agosto = RecursoRow(ide=901, cif=DNI, conide=None, empresa=1,
                             fecbaj=20260801)
    indice = _indice(recursos=(baja_agosto,))
    repo, _ = _conciliar([_linea(fecha=None)], indice,
                         hoy=date(2026, 7, 1))
    assert _update(repo, 1)["recurso_ide"] == 901
    repo, _ = _conciliar([_linea(fecha=None)], indice,
                         hoy=date(2026, 9, 1))
    assert _update(repo, 1)["recurso_ide"] is None


def test_f023_r26_el_reside_desempata_entre_candidatos() -> None:
    otro = RecursoRow(ide=903, cif=DNI, conide=None, empresa=1, fecbaj=0)
    repo, _ = _conciliar([_linea(reside=903)],
                         _indice(recursos=(ALTA_1, otro)))
    assert _update(repo, 1)["recurso_ide"] == 903


# ========================= R30 · congeladas ============================ #

def test_f023_r30_una_linea_congelada_no_cambia_de_recurso() -> None:
    repo, _ = _conciliar([
        _linea(1, recurso_ide=900, sigrid_estado="registrado"),
        _linea(2, doc_approved=True, recurso_ide=900),
        _linea(3, sigrid_estado="encolado"),
        _linea(4, sigrid_estado="error"),          # no congela
    ])
    assert [u["registro_id"] for u in repo.matches] == [4]


def test_f023_r30_la_congelada_cuenta_con_su_recurso_en_el_dia() -> None:
    """6 h congeladas con el recurso 901 + 4 h libres del mismo dia: el
    dia suma 10 y la extra (2 h) sale de la libre. Si la congelada no
    contara con su recurso, saldria una extra NEGATIVA de 4 h."""
    congelada = _linea(1, recurso_ide=901, sigrid_estado="registrado")
    congelada["horas"] = 6.0
    libre = _linea(2, reside=901)
    libre["horas"] = 4.0
    repo, _ = _conciliar([congelada, libre], _indice(recursos=(ALTA_1,)))
    (split,) = repo.splits
    assert (split["normal_id"], split["extra_horas"]) == (2, 2.0)


def test_f023_r30_la_congelada_sin_recurso_no_entra_en_el_dia() -> None:
    congelada = _linea(1, recurso_ide=None, sigrid_estado="registrado")
    congelada["horas"] = 6.0
    libre = _linea(2, reside=901)
    libre["horas"] = 8.0
    repo, _ = _conciliar([congelada, libre], _indice(recursos=(ALTA_1,)))
    assert repo.splits == []


def test_f023_r30_congelada_sin_obra_tampoco_cambia() -> None:
    repo, _ = _conciliar([
        _linea(1, obra_ide=None, recurso_ide=900, sigrid_estado="registrado"),
        _linea(2, obra_ide=None),
    ])
    assert [u["registro_id"] for u in repo.matches] == [2]


# ===================== R31 · se re-resuelve cada pasada ================= #

def test_f023_r31_la_siguiente_pasada_re_resuelve_lo_pendiente() -> None:
    """Una linea pendiente ya casada con el recurso de baja pasa al de
    alta en la siguiente pasada; su empleado no se toca."""
    linea = _linea(recurso_ide=900, parte_estado="sin_parte")
    repo, _ = _conciliar([linea])
    u = _update(repo, 1)
    assert u["recurso_ide"] == 901
    assert "empleado_ide" not in u


# ================== sin proveedor: solo los recursos ==================== #

def test_f023_sin_proveedor_se_usan_los_recursos_del_lookup() -> None:
    repo = RepositorioFake([_linea(reside=900)])
    conciliador = RecursoConciliador(
        repository=repo, lookup=LookupFake(recursos=[BAJA_2021, ALTA_1]))
    conciliador.conciliar_todos()
    assert _update(repo, 1)["recurso_ide"] == 901


def test_f023_sin_proveedor_y_lookup_caido_nada_se_casa(caplog) -> None:
    class Caido(LookupFake):
        def fetch_recursos(self):
            raise RuntimeError("sigrid-api caido")

    repo = RepositorioFake([_linea()])
    with caplog.at_level(logging.WARNING):
        RecursoConciliador(repository=repo, lookup=Caido()).conciliar_todos()
    assert _update(repo, 1)["parte_estado"] == "sin_recurso"
    assert "fallo leyendo recursos" in caplog.text


# ======================== el repositorio real =========================== #

def test_f023_fetch_registros_trae_recurso_y_empresa_del_parte() -> None:
    fabrica = FabricaSesionSqlite()
    (rid,) = sembrar_lineas(fabrica, [{"horas": 8.0}])
    with fabrica.create_session() as s:
        s.get(ParteDocumentOrm, "doc-1").empresa = 28
        s.commit()
    SqlAlchemyParteRepository(fabrica).apply_recurso_matches(  # type: ignore[arg-type]
        [{"registro_id": rid, "recurso_ide": 901, "recurso_cif": None,
          "hmo_ide": None, "parte_estado": "sin_parte"}])
    (fila,) = SqlAlchemyParteRepository(
        fabrica).fetch_registros_para_recurso()  # type: ignore[arg-type]
    assert (fila["recurso_ide"], fila["parte_empresa"]) == (901, 28)
