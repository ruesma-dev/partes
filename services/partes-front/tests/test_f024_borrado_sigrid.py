# tests/test_f024_borrado_sigrid.py
"""F-024 · estado `borrado_sigrid` en el portal (R10-R16, R22-R24).

Sin red ni PostgreSQL: SQLite en memoria con el MISMO ORM (dobles.py) y
dobles del cliente de sv5. Codigos de parte, `ide` y recursos sinteticos.
"""
from __future__ import annotations

import pytest
from application.services.congelacion import (
    ESTADO_BORRADO_SIGRID,
    ESTADOS_CONGELANTES,
    MOTIVO_LINEA_REGISTRADA,
    es_registrado,
    motivo_congelacion_documento,
    motivo_congelacion_linea,
)
from infrastructure.database import parte_repository as repo_mod
from infrastructure.database.orm_models import ParteRegistroOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite, estados_sigrid, sembrar_parte

PARTE = "PT26/09001"
HMO = 7001


def _poner(fabrica, rid: int, **campos) -> None:
    with fabrica.create_session() as s:
        reg = s.get(ParteRegistroOrm, rid)
        for k, v in campos.items():
            setattr(reg, k, v)
        s.commit()


def _leer(fabrica, rid: int) -> ParteRegistroOrm:
    with fabrica.create_session() as s:
        reg = s.get(ParteRegistroOrm, rid)
        s.expunge(reg)
        return reg


def _montar(estados: list[str | None], **kw):
    fabrica = FabricaSesionSqlite()
    ids = sembrar_parte(fabrica, [{"estado": e} for e in estados], **kw)
    return ParteReviewRepository(fabrica), fabrica, ids


# ===================================================================== #
# T5 · congelacion (R13), ESTADOS_EN_VUELO (R15) y motivo (R16)
# ===================================================================== #

def test_f024_r10_congel_el_estado_cabe_en_la_columna() -> None:
    assert ESTADO_BORRADO_SIGRID == "borrado_sigrid"
    assert len(ESTADO_BORRADO_SIGRID) <= 16
    assert ParteRegistroOrm.__table__.c.sigrid_estado.type.length == 16


def test_f024_r13_congel_borrado_sigrid_no_congela_la_linea() -> None:
    for estado in (ESTADO_BORRADO_SIGRID, " Borrado_Sigrid "):
        assert motivo_congelacion_linea(
            doc_aprobado=False, sigrid_estado=estado) is None
    assert ESTADO_BORRADO_SIGRID not in ESTADOS_CONGELANTES
    assert tuple(ESTADOS_CONGELANTES) == ("encolado", "registrado")


def test_f024_r13_congel_borrado_sigrid_no_congela_el_documento() -> None:
    assert motivo_congelacion_documento(
        aprobado=False, estados_lineas=[ESTADO_BORRADO_SIGRID, None]) is None


def test_f024_r13_congel_el_parte_aprobado_sigue_mandando() -> None:
    """`borrado_sigrid` no descongela un parte aprobado (F-004 R1)."""
    assert motivo_congelacion_linea(
        doc_aprobado=True, sigrid_estado=ESTADO_BORRADO_SIGRID) is not None


def test_f024_r13_congel_borrado_sigrid_no_bloquea_el_borrado_definitivo() -> None:
    assert es_registrado(ESTADO_BORRADO_SIGRID) is False
    repo, fabrica, ids = _montar([ESTADO_BORRADO_SIGRID])
    assert repo.hard_delete_registro(registro_id=ids[0]) is True
    with fabrica.create_session() as s:
        assert s.get(ParteRegistroOrm, ids[0]) is None


def test_f024_r13_congel_la_linea_borrada_en_sigrid_se_puede_editar() -> None:
    repo, fabrica, ids = _montar([ESTADO_BORRADO_SIGRID])
    assert repo.update_registro(registro_id=ids[0], horas=6.0) is True
    assert _leer(fabrica, ids[0]).horas == 6.0


def test_f024_r13_congel_la_vista_no_pinta_candado() -> None:
    repo, _f, ids = _montar([ESTADO_BORRADO_SIGRID])
    detalle = repo.get_parte("doc-f004")
    assert detalle.congelado_doc is None


def test_f024_r15_vuelo_borrado_sigrid_no_es_veredicto_final() -> None:
    assert ESTADO_BORRADO_SIGRID in repo_mod.ESTADOS_EN_VUELO


def test_f024_r15_vuelo_ya_registrada_devuelve_la_linea_a_registrado() -> None:
    repo, fabrica, ids = _montar([ESTADO_BORRADO_SIGRID, "omitido"])
    repo.marcar_registros_sigrid(escritas=[], omitidas=[],
                                 ya_registradas=ids, usuario="ana")
    estados = estados_sigrid(fabrica, ids)
    assert estados[ids[0]][0] == "registrado"
    assert estados[ids[1]][0] == "omitido"     # veredicto final: se respeta


def test_f024_r16_motivo_explica_la_via_nueva() -> None:
    texto = MOTIVO_LINEA_REGISTRADA
    assert "Comprobar en Sigrid" in texto
    assert "borra" in texto.lower()
    assert "aprob" in texto.lower()
    assert motivo_congelacion_linea(
        doc_aprobado=False, sigrid_estado="registrado") == texto



# ===================================================================== #
# T7 · repositorio: registrados_para_comprobar, aplicar_comprobacion_sigrid
# (R10-R12) y recuento_estados (R28)
# ===================================================================== #

AHORA = "2026-10-01T09:30:15.123456+00:00"


def _registrada(fabrica, rid: int, *, hmores: int | None, hmoide: int = HMO,
                parte: str = PARTE) -> None:
    _poner(fabrica, rid, sigrid_estado="registrado", sigrid_hmores_ide=hmores,
           sigrid_hmoide=hmoide, sigrid_parte_cod=parte,
           sigrid_registrado_at_utc="2026-09-30T10:42:08+00:00",
           sigrid_registrado_by="aprobador")


def _borrada(rid: int, **extra) -> dict:
    return dict({"registro_id": rid, "estado": "borrada", "hmores_ide": None,
                 "hmoide": HMO, "parte_cod": PARTE, "parte_existe": True,
                 "sin_synckey": False, "diferencias": [], "motivo": "x"},
                **extra)


def _presente(rid: int, **extra) -> dict:
    return dict({"registro_id": rid, "estado": "presente", "hmores_ide": None,
                 "hmoide": HMO, "parte_cod": PARTE, "parte_existe": True,
                 "sin_synckey": False, "diferencias": [], "motivo": None},
                **extra)


def test_f024_r17_repo_registrados_para_comprobar_solo_registrado() -> None:
    repo, fabrica, ids = _montar(
        ["registrado", None, ESTADO_BORRADO_SIGRID, " Registrado ",
         "registrado", "encolado"])
    _registrada(fabrica, ids[0], hmores=4001)
    _poner(fabrica, ids[3], sigrid_hmores_ide=4003)
    _poner(fabrica, ids[4], deleted_at_utc=AHORA)       # en la papelera
    _poner(fabrica, ids[0], es_incidencia=True, horas=None)
    filas = repo.registrados_para_comprobar(ids + [999999])
    assert sorted(f["registro_id"] for f in filas) == [ids[0], ids[3]]
    fila = next(f for f in filas if f["registro_id"] == ids[0])
    assert fila == {"registro_id": ids[0], "hmores_ide": 4001, "hmoide": HMO,
                    "recurso_ide": 501, "fecha_int": 20260302, "horas": None,
                    "es_incidencia": True}


def test_f024_r17_repo_registrados_para_comprobar_sin_ids_no_consulta() -> None:
    repo, _f, _ids = _montar(["registrado"])
    assert repo.registrados_para_comprobar([]) == []


def test_f024_r17_repo_registrados_para_comprobar_muchos_ids() -> None:
    """5000 ids (el tope de R17) no rompen la consulta."""
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    filas = repo.registrados_para_comprobar(list(range(ids[0], ids[0] + 5000)))
    assert [f["registro_id"] for f in filas] == [ids[0]]


def test_f024_r10_repo_borrada_pasa_a_borrado_sigrid_y_conserva_rastro() -> None:
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    out = repo.aplicar_comprobacion_sigrid(
        [_borrada(ids[0])], {ids[0]: 4001}, AHORA)
    assert out == {"borradas": [ids[0]], "actualizadas": []}
    reg = _leer(fabrica, ids[0])
    assert reg.sigrid_estado == "borrado_sigrid"
    assert reg.sigrid_motivo == (
        f"Borrada en Sigrid: la linea 4001 del parte {PARTE} ya no existe "
        "(comprobado 2026-10-01 09:30 UTC)")
    assert (reg.sigrid_parte_cod, reg.sigrid_hmoide, reg.sigrid_hmores_ide,
            reg.sigrid_registrado_at_utc, reg.sigrid_registrado_by) == (
        PARTE, HMO, 4001, "2026-09-30T10:42:08+00:00", "aprobador")


def test_f024_r10_repo_cabecera_borrada_tiene_su_motivo() -> None:
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    repo.aplicar_comprobacion_sigrid(
        [_borrada(ids[0], parte_existe=False, parte_cod=None)],
        {ids[0]: 4001}, AHORA)
    reg = _leer(fabrica, ids[0])
    assert reg.sigrid_estado == "borrado_sigrid"
    assert reg.sigrid_motivo == (
        f"Borrada en Sigrid: el parte {PARTE} ya no existe (linea 4001; "
        "comprobado 2026-10-01 09:30 UTC)")


def test_f024_r10_repo_el_motivo_cabe_en_la_columna() -> None:
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001, parte="P" * 300)
    repo.aplicar_comprobacion_sigrid([_borrada(ids[0])], {ids[0]: 4001}, AHORA)
    motivo = _leer(fabrica, ids[0]).sigrid_motivo
    assert len(motivo) == 255
    assert motivo.startswith("Borrada en Sigrid: la linea 4001 del parte PPP")


@pytest.mark.parametrize("estado_actual", ["encolado", "omitido",
                                           ESTADO_BORRADO_SIGRID, None])
def test_f024_r11_repo_si_ya_no_esta_registrada_no_se_toca(estado_actual) -> None:
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    _poner(fabrica, ids[0], sigrid_estado=estado_actual, sigrid_motivo="previo")
    out = repo.aplicar_comprobacion_sigrid(
        [_borrada(ids[0])], {ids[0]: 4001}, AHORA)
    assert out == {"borradas": [], "actualizadas": []}
    reg = _leer(fabrica, ids[0])
    assert (reg.sigrid_estado, reg.sigrid_motivo) == (estado_actual, "previo")


def test_f024_r11_repo_si_cambio_su_hmores_ide_no_se_toca() -> None:
    """Se reaprobo entre la lectura y el veredicto: hay otra linea."""
    repo, fabrica, ids = _montar(["registrado", "registrado"])
    _registrada(fabrica, ids[0], hmores=4999)
    _registrada(fabrica, ids[1], hmores=None)
    out = repo.aplicar_comprobacion_sigrid(
        [_borrada(ids[0]), _presente(ids[1], hmores_ide=4002)],
        {ids[0]: 4001, ids[1]: 4001}, AHORA)
    assert out == {"borradas": [], "actualizadas": []}
    assert _leer(fabrica, ids[0]).sigrid_estado == "registrado"
    assert _leer(fabrica, ids[1]).sigrid_hmores_ide is None


def test_f024_r11_repo_veredicto_no_enviado_o_desconocido_no_se_aplica() -> None:
    repo, fabrica, ids = _montar(["registrado", "registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    _registrada(fabrica, ids[1], hmores=4002)
    out = repo.aplicar_comprobacion_sigrid(
        [_borrada(ids[0]), _borrada(ids[1], estado="rara"), _borrada(999999)],
        {ids[1]: 4002, 999999: None}, AHORA)
    assert out == {"borradas": [], "actualizadas": []}
    assert {_leer(fabrica, i).sigrid_estado for i in ids} == {"registrado"}


def test_f024_r10_repo_estado_guardado_se_compara_normalizado() -> None:
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    _poner(fabrica, ids[0], sigrid_estado=" Registrado ")
    out = repo.aplicar_comprobacion_sigrid(
        [_borrada(ids[0])], {ids[0]: 4001}, AHORA)
    assert out["borradas"] == [ids[0]]


@pytest.mark.parametrize("campo, valor", [
    ("hmores_ide", 4999), ("hmoide", 7002), ("parte_cod", "PT26/09002")])
def test_f024_r12_repo_presente_con_referencias_nuevas_las_actualiza(
        campo, valor) -> None:
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    veredicto = _presente(ids[0], hmores_ide=4001)
    veredicto[campo] = valor
    out = repo.aplicar_comprobacion_sigrid([veredicto], {ids[0]: 4001}, AHORA)
    assert out == {"borradas": [], "actualizadas": [ids[0]]}
    reg = _leer(fabrica, ids[0])
    assert reg.sigrid_estado == "registrado"
    assert getattr(reg, {"hmores_ide": "sigrid_hmores_ide",
                         "hmoide": "sigrid_hmoide",
                         "parte_cod": "sigrid_parte_cod"}[campo]) == valor
    assert (reg.sigrid_registrado_at_utc, reg.sigrid_registrado_by) == (
        "2026-09-30T10:42:08+00:00", "aprobador")


def test_f024_r12_repo_presente_igual_no_cuenta_como_actualizada() -> None:
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    _poner(fabrica, ids[0], sigrid_motivo="[SIN-SESAME] previo")
    out = repo.aplicar_comprobacion_sigrid(
        [_presente(ids[0], hmores_ide=4001)], {ids[0]: 4001}, AHORA)
    assert out == {"borradas": [], "actualizadas": []}
    assert _leer(fabrica, ids[0]).sigrid_motivo == "[SIN-SESAME] previo"


def test_f024_r12_repo_presente_sin_dato_no_borra_lo_guardado() -> None:
    repo, fabrica, ids = _montar(["registrado"])
    _registrada(fabrica, ids[0], hmores=4001)
    out = repo.aplicar_comprobacion_sigrid(
        [_presente(ids[0], hmores_ide=None, hmoide=None, parte_cod=None)],
        {ids[0]: 4001}, AHORA)
    assert out["actualizadas"] == []
    reg = _leer(fabrica, ids[0])
    assert (reg.sigrid_hmores_ide, reg.sigrid_hmoide, reg.sigrid_parte_cod) \
        == (4001, HMO, PARTE)


def test_f024_r28_repo_recuento_estados() -> None:
    repo, fabrica, ids = _montar(
        ["encolado", "registrado", " Registrado ", "omitido", None,
         ESTADO_BORRADO_SIGRID, "ENCOLADO"])
    out = repo.recuento_estados(ids + [999999])
    assert out == {"total": 7, "pendientes": 2, "estados": {
        "encolado": 2, "registrado": 2, "omitido": 1, "sin_estado": 1,
        "borrado_sigrid": 1}}


def test_f024_r28_repo_recuento_sin_ids() -> None:
    repo, _f, _ids = _montar(["encolado"])
    assert repo.recuento_estados([]) == {"total": 0, "pendientes": 0,
                                         "estados": {}}
