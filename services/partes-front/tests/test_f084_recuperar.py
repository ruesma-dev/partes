# tests/test_f084_recuperar.py
"""F-084 · repositorio de sv4: pestaña, contador, recuperar y deshacer.

`ParteReviewRepository` real sobre SQLite en memoria (`tests/dobles.py`,
mismo ORM). Cubre `list_partes_con_problemas` y `resumen_problemas` (R6-R11)
y `recuperar_parte` con sus guardas (R17, R19-R22, R24) y su deshacer (R23).
Ni red ni PostgreSQL. Datos sintéticos, sin DNIs ni nombres reales.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

import pytest
from dobles import FabricaSesionSqlite
from sqlalchemy import select

from application.services.congelacion import CongeladoError
from application.services.parte_vacio import (
    MARCA_RETIRADO,
    DuplicadoActivoError,
)
from application.services.partes_con_problemas import (
    MOTIVO_FECHA_FUTURA,
    MOTIVO_FECHA_POSTERIOR_CORREO,
    MOTIVO_SIN_FECHA,
    MOTIVO_SIN_LINEAS,
    MOTIVO_SIN_OBRA,
    MOTIVO_SIN_RASTRO,
    MOTIVO_SUSTITUIDO,
    MOTIVO_SUSTITUIDO_MISMO_ENVIO,
    ChoqueRecuperarError,
    NoRecuperableError,
)
from application.services.seguimiento_recalculo import RecalculandoError
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
    UndoLogOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository

AHORA = "2026-11-26T10:00:00+00:00"


def _sembrar(fabrica, id_: str, *, activo: bool = True,
             fecha: str | None = "2026-11-23", obra_ide: int | None = 10,
             obra_codigo: str | None = "0100",
             obra_numero_leido: str | None = "100",
             email_id: str | None = "correo-1",
             recibido: str | None = "2026-11-26T09:56:00Z",
             creado: str = AHORA, sustituido_por_id: str | None = None,
             sustituido_at: str | None = None,
             deleted_at: str | None = None, deleted_by: str | None = None,
             aprobado: bool = False, sha: str | None = None,
             pdf: bool = True, lineas: list[dict] | None = None,
             pedido: str | None = None, pedido_at: str | None = None
             ) -> list[int]:
    """Un parte con sus líneas. Cada línea admite `ide` (ficha), `nombre`,
    `horas`, `tipo`, `borrada` y `estado` (`sigrid_estado`)."""
    lineas = [{}] if lineas is None else lineas
    fint = int(fecha.replace("-", "")) if fecha else None
    with fabrica.create_session() as s:
        s.add(ParteDocumentOrm(
            id=id_, source_filename="parte.pdf",
            source_mime_type="application/pdf",
            source_sha256=sha or "sha-" + id_, fecha=fecha, fecha_int=fint,
            created_at_utc=creado, obra_ide=obra_ide, obra_codigo=obra_codigo,
            obra_nombre="Obra Uno" if obra_codigo else None,
            obra_numero_leido=obra_numero_leido,
            obra_nombre_leido="Obra leida", page_number=4, page_count=6,
            email_id=email_id, email_subject="Partes semana",
            email_received_datetime=recibido, approved=aprobado,
            is_active=activo, deleted_at_utc=deleted_at,
            deleted_by=deleted_by, sustituido_por_id=sustituido_por_id,
            sustituido_at_utc=sustituido_at,
            sharepoint_drive_id="drv" if pdf else None,
            sharepoint_item_id="itm" if pdf else None,
            recalculo_pedido_id=pedido, recalculo_pedido_at_utc=pedido_at))
        ids: list[int] = []
        for i, ln in enumerate(lineas):
            reg = ParteRegistroOrm(
                document_id=id_, line_index=i, empleado_line_no=i + 1,
                fecha=fecha, fecha_int=fint, obra_ide=obra_ide,
                obra_codigo=obra_codigo, empleado_ide=ln.get("ide", 77),
                trabajador_nombre_leido=ln.get("nombre", "Trabajador Uno"),
                empleado_nombre=ln.get("nombre", "Trabajador Uno"),
                tipo_hora=ln.get("tipo", "normal"),
                horas=ln.get("horas", 8.0), hora_ide=1, hora_codigo="HL01",
                sigrid_estado=ln.get("estado"),
                deleted_at_utc=AHORA if ln.get("borrada") else None)
            s.add(reg)
            s.flush()
            ids.append(reg.id)
        s.commit()
    return ids


def _doc(fabrica, id_: str) -> ParteDocumentOrm:
    with fabrica.create_session() as s:
        return s.get(ParteDocumentOrm, id_)


def _regs(fabrica, id_: str) -> list[ParteRegistroOrm]:
    with fabrica.create_session() as s:
        return list(s.execute(select(ParteRegistroOrm).where(
            ParteRegistroOrm.document_id == id_)).scalars().all())


def _undos(fabrica) -> list[UndoLogOrm]:
    with fabrica.create_session() as s:
        return list(s.execute(select(UndoLogOrm)).scalars().all())


def _montaje():
    fabrica = FabricaSesionSqlite()
    return fabrica, ParteReviewRepository(fabrica)


def _sustituido_basico(fabrica, **kw) -> None:
    """`viejo` sustituido por `nuevo` (otro correo) el mismo día y obra."""
    _sembrar(fabrica, "nuevo", email_id="correo-2",
             creado="2026-11-26T10:05:00+00:00")
    _sembrar(fabrica, "viejo", activo=False, sustituido_por_id="nuevo",
             sustituido_at="2026-11-26T10:05:00+00:00", **kw)


# =================== R6-R11 · list_partes_con_problemas ================== #

def test_f084_r11_lista_un_caso_de_cada_motivo() -> None:
    fabrica, repo = _montaje()
    _sembrar(fabrica, "sano")
    _sembrar(fabrica, "sin-obra", obra_ide=None, obra_codigo=None,
             fecha="2026-11-20")
    _sembrar(fabrica, "sin-fecha", fecha=None)
    _sembrar(fabrica, "futuro", fecha="2027-02-01",
             recibido="2027-02-01T08:00:00Z")
    _sembrar(fabrica, "posterior", fecha="2026-11-28")
    _sembrar(fabrica, "vacio", lineas=[{"borrada": True}])
    _sembrar(fabrica, "nuevo", email_id="correo-1", obra_codigo="0300",
             obra_ide=30, creado="2026-11-26T10:01:39+00:00",
             lineas=[{"ide": 88}])
    _sembrar(fabrica, "mismo", activo=False, obra_codigo="0300", obra_ide=30,
             sustituido_por_id="nuevo",
             sustituido_at="2026-11-26T10:01:39+00:00", lineas=[{"ide": 88}])
    _sembrar(fabrica, "reenvio", activo=False, obra_codigo="0300",
             obra_ide=30, email_id="correo-0", sustituido_por_id="nuevo")
    _sembrar(fabrica, "huerfano", activo=False, sustituido_por_id="borrado")
    _sembrar(fabrica, "papelera", activo=False, deleted_at=AHORA,
             deleted_by="ana")
    _sembrar(fabrica, "retirado", activo=False,
             deleted_by=MARCA_RETIRADO + " · ana")

    filas = repo.list_partes_con_problemas()
    por_id = {f["document_id"]: f for f in filas}
    assert set(por_id) == {"sin-obra", "sin-fecha", "futuro", "posterior",
                           "vacio", "mismo", "reenvio", "huerfano"}
    assert [f["motivo"] for f in filas] == [
        MOTIVO_SIN_OBRA, MOTIVO_SIN_FECHA, MOTIVO_FECHA_FUTURA,
        MOTIVO_FECHA_POSTERIOR_CORREO, MOTIVO_SIN_LINEAS,
        MOTIVO_SUSTITUIDO_MISMO_ENVIO, MOTIVO_SIN_RASTRO, MOTIVO_SUSTITUIDO]
    assert por_id["futuro"]["motivos"] == [MOTIVO_FECHA_FUTURA]
    assert por_id["reenvio"]["cuenta"] is False
    assert por_id["huerfano"]["cuenta"] is True
    assert por_id["huerfano"]["sustituto"] is None

    mismo = por_id["mismo"]
    assert mismo["is_active"] is False
    assert mismo["sustituido_at_utc"] == "2026-11-26T10:01:39+00:00"
    assert mismo["sustituto"] == {
        "id": "nuevo", "fecha": "2026-11-23", "obra_codigo": "0300",
        "obra_nombre": "Obra Uno", "activo": True}


def test_f084_r11_los_campos_de_cada_fila() -> None:
    fabrica, repo = _montaje()
    _sembrar(fabrica, "sin-obra", obra_ide=None, obra_codigo=None, lineas=[
        {"ide": 1, "horas": 8.0}, {"ide": 1, "horas": 2.0, "tipo": "extra"},
        {"ide": 2, "horas": 4.0}, {"ide": 3, "horas": 9.0, "borrada": True}])
    [fila] = repo.list_partes_con_problemas()
    assert fila["fecha"] == "2026-11-23"
    assert fila["obra_codigo"] == "100"            # la leída: sin casar
    assert fila["obra_nombre"] == "Obra leida"
    assert fila["page_number"] == 4 and fila["page_count"] == 6
    assert fila["email_subject"] == "Partes semana"
    assert fila["email_received_datetime"] == "2026-11-26T09:56:00Z"
    assert fila["num_trabajadores"] == 2            # solo líneas vivas
    assert fila["horas_normales"] == 12.0
    assert fila["horas_extra"] == 2.0
    assert fila["tiene_pdf"] is True
    assert fila["congelado"] is None
    assert fila["texto_motivo"] == "Sin obra casada"
    assert "dni" not in json.dumps(fila).lower()


def test_f084_r11_congelado_y_sin_pdf() -> None:
    fabrica, repo = _montaje()
    _sustituido_basico(fabrica, aprobado=True, pdf=False)
    _sembrar(fabrica, "en-sigrid", activo=False, obra_codigo="0900",
             obra_ide=90, lineas=[{"estado": "registrado"}])
    por_id = {f["document_id"]: f for f in repo.list_partes_con_problemas()}
    assert por_id["viejo"]["congelado"] == "aprobado"
    assert por_id["viejo"]["tiene_pdf"] is False
    assert por_id["en-sigrid"]["congelado"] == "sigrid"


def test_f084_r8_pista_retroactiva_en_el_repositorio() -> None:
    fabrica, repo = _montaje()
    _sembrar(fabrica, "viejo", activo=False, creado="2026-11-26T10:00:00Z")
    _sembrar(fabrica, "nuevo", creado="2026-11-26T10:01:39Z",
             lineas=[{"ide": 99}])
    [fila] = repo.list_partes_con_problemas()
    assert fila["document_id"] == "viejo"
    assert fila["motivo"] == MOTIVO_SUSTITUIDO_MISMO_ENVIO
    assert fila["sustituto"]["id"] == "nuevo"
    assert fila["sustituido_at_utc"] is None


def test_f084_r10_resumen_es_la_misma_lista() -> None:
    fabrica, repo = _montaje()
    _sembrar(fabrica, "sin-obra", obra_ide=None)
    _sustituido_basico(fabrica)                    # sustituido: no cuenta
    _sembrar(fabrica, "huerfano", activo=False, sustituido_por_id="x",
             obra_codigo="0500", obra_ide=50)
    assert repo.resumen_problemas() == {
        "total": 2, "por_motivo": {MOTIVO_SIN_OBRA: 1, MOTIVO_SUSTITUIDO: 1,
                                   MOTIVO_SIN_RASTRO: 1}}


def test_f084_r15_sin_problemas_lista_vacia_y_total_cero() -> None:
    fabrica, repo = _montaje()
    _sembrar(fabrica, "sano")
    assert repo.list_partes_con_problemas() == []
    assert repo.resumen_problemas() == {"total": 0, "por_motivo": {}}


# ======================= R17 · recuperar ================================ #

def test_f084_r17_recuperar_sin_fecha() -> None:
    fabrica, repo = _montaje()
    _sustituido_basico(fabrica, fecha="2026-11-24")
    res = repo.recuperar_parte(document_id="viejo", actor="ana")
    assert res == {"document_id": "viejo", "fecha": "2026-11-24"}
    doc = _doc(fabrica, "viejo")
    assert doc.is_active is True
    assert doc.sustituido_por_id == "nuevo"                 # se conserva
    assert doc.sustituido_at_utc == "2026-11-26T10:05:00+00:00"
    assert doc.deleted_at_utc is None
    [undo] = _undos(fabrica)
    assert undo.action == "parte_recuperar"
    assert undo.actor == "ana"
    payload = json.loads(undo.payload)
    assert payload["reactivados"] == ["viejo"]
    assert payload["documents"][0]["id"] == "viejo"


def test_f084_r17_recuperar_con_fecha_la_aplica_a_todas_las_lineas() -> None:
    fabrica, repo = _montaje()
    _sustituido_basico(fabrica, lineas=[{}, {"borrada": True, "ide": 5}])
    res = repo.recuperar_parte(document_id="viejo", fecha_iso="2026-11-25",
                               fecha_int=20261125, actor="ana")
    assert res == {"document_id": "viejo", "fecha": "2026-11-25"}
    doc = _doc(fabrica, "viejo")
    assert (doc.fecha, doc.fecha_int, doc.is_active) == (
        "2026-11-25", 20261125, True)
    assert {(r.fecha, r.fecha_int) for r in _regs(fabrica, "viejo")} == {
        ("2026-11-25", 20261125)}
    payload = json.loads(_undos(fabrica)[0].payload)
    assert payload["documents"][0]["fecha"] == "2026-11-23"
    assert {s["fecha"] for s in payload["registros"]} == {"2026-11-23"}


def test_f084_r24_recuperar_deja_un_info_sin_nombres(caplog) -> None:
    fabrica, repo = _montaje()
    _sustituido_basico(fabrica)
    with caplog.at_level(logging.INFO):
        repo.recuperar_parte(document_id="viejo", fecha_iso="2026-11-25",
                             fecha_int=20261125, actor="ana")
    [msg] = [r.getMessage() for r in caplog.records
             if r.levelno == logging.INFO and "recuperar" in r.getMessage()]
    assert "viejo" in msg and "2026-11-23" in msg and "2026-11-25" in msg
    assert "ana" in msg
    assert "Trabajador" not in msg


# ================ R19 · choque con otro parte activo ==================== #

def test_f084_r19_choque_con_el_sustituto_no_escribe() -> None:
    fabrica, repo = _montaje()
    _sustituido_basico(fabrica)
    with pytest.raises(ChoqueRecuperarError) as exc:
        repo.recuperar_parte(document_id="viejo", actor="ana")
    assert exc.value.partes == [
        {"id": "nuevo", "fecha": "2026-11-23", "obra": "0100"}]
    assert "Corrige la fecha o descarta antes el otro parte" in \
        exc.value.motivo
    assert _doc(fabrica, "viejo").is_active is False
    assert _undos(fabrica) == []


def test_f084_r19_con_otra_fecha_ya_no_choca() -> None:
    fabrica, repo = _montaje()
    _sustituido_basico(fabrica)
    repo.recuperar_parte(document_id="viejo", fecha_iso="2026-11-25",
                         fecha_int=20261125)
    assert _doc(fabrica, "viejo").is_active is True


def test_f084_r19_la_fecha_nueva_puede_chocar_con_otro() -> None:
    fabrica, repo = _montaje()
    _sembrar(fabrica, "viejo", activo=False)
    _sembrar(fabrica, "del-25", fecha="2026-11-25")
    with pytest.raises(ChoqueRecuperarError) as exc:
        repo.recuperar_parte(document_id="viejo", fecha_iso="2026-11-25",
                             fecha_int=20261125)
    assert [p["id"] for p in exc.value.partes] == ["del-25"]
    assert _doc(fabrica, "viejo").fecha == "2026-11-23"


@pytest.mark.parametrize("otro, choca", [
    ({"lineas": [{"ide": 78}]}, False),                 # otro trabajador
    ({"lineas": [{"borrada": True}]}, False),           # sus líneas, muertas
    ({"obra_ide": 20, "obra_codigo": "0200"}, False),   # otra obra
    ({"fecha": "2026-11-24"}, False),                   # otro día
    ({"activo": False}, False),                         # no activo
    ({"obra_ide": None}, True),                         # por código
    ({"obra_ide": None, "obra_codigo": None}, False),   # código vs nada
])
def test_f084_r19_que_es_chocar(otro, choca) -> None:
    fabrica, repo = _montaje()
    _sembrar(fabrica, "viejo", activo=False)
    _sembrar(fabrica, "otro", **otro)
    if choca:
        with pytest.raises(ChoqueRecuperarError):
            repo.recuperar_parte(document_id="viejo")
    else:
        repo.recuperar_parte(document_id="viejo")
        assert _doc(fabrica, "viejo").is_active is True


def test_f084_r19_sin_obra_casada_compara_el_numero_leido() -> None:
    fabrica, repo = _montaje()
    _sembrar(fabrica, "viejo", activo=False, obra_ide=None, obra_codigo=None)
    _sembrar(fabrica, "otro-num", obra_ide=None, obra_codigo=None,
             obra_numero_leido="101")
    repo.recuperar_parte(document_id="viejo")          # 100 ≠ 101
    fabrica2, repo2 = _montaje()
    _sembrar(fabrica2, "viejo", activo=False, obra_ide=None, obra_codigo=None)
    _sembrar(fabrica2, "mismo-num", obra_ide=None, obra_codigo=None)
    with pytest.raises(ChoqueRecuperarError):
        repo2.recuperar_parte(document_id="viejo")


def test_f084_r19_sin_lineas_vivas_no_choca() -> None:
    fabrica, repo = _montaje()
    _sustituido_basico(fabrica, lineas=[{"borrada": True}])
    repo.recuperar_parte(document_id="viejo")
    assert _doc(fabrica, "viejo").is_active is True


# ============== R20 · sha256 de otro parte activo ======================= #

def test_f084_r20_mismo_sha_que_otro_activo_no_escribe() -> None:
    fabrica, repo = _montaje()
    _sembrar(fabrica, "activo", sha="sha-comun", obra_codigo="0500",
             obra_ide=50)
    _sembrar(fabrica, "viejo", activo=False, sha="sha-comun")
    with pytest.raises(DuplicadoActivoError):
        repo.recuperar_parte(document_id="viejo")
    assert _doc(fabrica, "viejo").is_active is False
    assert _undos(fabrica) == []


# ======== R21 · congelado (con fecha) y en espera de recálculo ========== #

def test_f084_r21_congelado_con_fecha_no_escribe() -> None:
    fabrica, repo = _montaje()
    _sustituido_basico(fabrica, aprobado=True)
    with pytest.raises(CongeladoError):
        repo.recuperar_parte(document_id="viejo", fecha_iso="2026-11-25",
                             fecha_int=20261125)
    doc = _doc(fabrica, "viejo")
    assert (doc.is_active, doc.fecha) == (False, "2026-11-23")


def test_f084_r21_congelado_sin_fecha_se_recupera() -> None:
    fabrica, repo = _montaje()
    _sembrar(fabrica, "viejo", activo=False, aprobado=True,
             lineas=[{"estado": "registrado"}])
    repo.recuperar_parte(document_id="viejo")
    assert _doc(fabrica, "viejo").is_active is True


def test_f084_r21_en_espera_de_recalculo_no_escribe() -> None:
    fabrica, repo = _montaje()
    reciente = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
    _sembrar(fabrica, "viejo", activo=False, pedido="pedido-1",
             pedido_at=reciente)
    for kwargs in ({}, {"fecha_iso": "2026-11-25", "fecha_int": 20261125}):
        with pytest.raises(RecalculandoError):
            repo.recuperar_parte(document_id="viejo", **kwargs)
    assert _doc(fabrica, "viejo").is_active is False


# ===================== R22 · no recuperables ============================ #

def test_f084_r22_inexistente_devuelve_none() -> None:
    _fabrica, repo = _montaje()
    assert repo.recuperar_parte(document_id="no-existe") is None


@pytest.mark.parametrize("kwargs", [
    {"activo": True},
    {"activo": False, "deleted_at": AHORA, "deleted_by": "ana"},
    {"activo": False, "deleted_by": MARCA_RETIRADO},
])
def test_f084_r22_activo_papelera_o_retirado_no_se_recuperan(kwargs) -> None:
    fabrica, repo = _montaje()
    _sembrar(fabrica, "doc", **kwargs)
    antes = _doc(fabrica, "doc")
    with pytest.raises(NoRecuperableError) as exc:
        repo.recuperar_parte(document_id="doc", fecha_iso="2026-11-25",
                             fecha_int=20261125)
    assert exc.value.motivo
    despues = _doc(fabrica, "doc")
    assert (despues.is_active, despues.fecha, despues.deleted_by) == (
        antes.is_active, antes.fecha, antes.deleted_by)
    assert _undos(fabrica) == []


# ======================= R23 · deshacer ================================== #

def test_f084_r23_deshacer_recuperar_vuelve_a_inactivo_y_fecha() -> None:
    fabrica, repo = _montaje()
    _sustituido_basico(fabrica)
    repo.recuperar_parte(document_id="viejo", fecha_iso="2026-11-25",
                         fecha_int=20261125, actor="ana")
    res = repo.undo_last(actor="ana")
    assert res["ok"] is True
    assert res["action"] == "parte_recuperar"
    assert res["document_ids"] == ["viejo"]
    assert res["omitidos"] == 0
    doc = _doc(fabrica, "viejo")
    assert (doc.is_active, doc.fecha, doc.fecha_int) == (
        False, "2026-11-23", 20261123)
    assert doc.sustituido_por_id == "nuevo"
    assert doc.deleted_at_utc is None and doc.deleted_by is None
    assert {r.fecha for r in _regs(fabrica, "viejo")} == {"2026-11-23"}


def test_f084_r23_deshacer_sin_fecha_solo_desactiva() -> None:
    fabrica, repo = _montaje()
    _sembrar(fabrica, "viejo", activo=False)
    repo.recuperar_parte(document_id="viejo")
    repo.undo_last()
    assert _doc(fabrica, "viejo").is_active is False


def test_f084_r23_deshacer_omite_lo_hoy_congelado() -> None:
    fabrica, repo = _montaje()
    _sustituido_basico(fabrica)
    repo.recuperar_parte(document_id="viejo", fecha_iso="2026-11-25",
                         fecha_int=20261125)
    with fabrica.create_session() as s:
        s.get(ParteDocumentOrm, "viejo").approved = True
        s.commit()
    res = repo.undo_last()
    assert res["ok"] is True and res["omitidos"] >= 1
    doc = _doc(fabrica, "viejo")
    assert (doc.is_active, doc.fecha) == (True, "2026-11-25")


def test_f084_r23_deshacer_con_el_parte_ya_descartado_no_lo_toca() -> None:
    fabrica, repo = _montaje()
    _sembrar(fabrica, "viejo", activo=False)
    repo.recuperar_parte(document_id="viejo")
    repo.delete_document(document_id="viejo", deleted_by="ana")
    repo.undo_last()
    doc = _doc(fabrica, "viejo")
    assert doc.is_active is False and doc.deleted_at_utc is not None


def test_f084_r23_las_demas_acciones_no_ganan_reactivados_ni_actor() -> None:
    fabrica, repo = _montaje()
    _sembrar(fabrica, "activo")
    repo.update_parte_fecha(document_id="activo", fecha_iso="2026-11-24",
                            fecha_int=20261124)
    [undo] = _undos(fabrica)
    assert "reactivados" not in json.loads(undo.payload)
    assert undo.actor is None


# ================= T10 · supervivientes de la mutación =================== #

def test_f084_r5_ddl_declara_las_columnas_del_rastro() -> None:
    """R5: los tipos exactos llegan al `ADD COLUMN` de PostgreSQL
    (mutante 7; SQLite ignora la longitud)."""
    from infrastructure.database.orm_models import ddl_complementario
    ddl = ddl_complementario()
    assert ("ALTER TABLE parte_documents ADD COLUMN IF NOT EXISTS "
            "sustituido_por_id VARCHAR(36)") in ddl
    assert ("ALTER TABLE parte_documents ADD COLUMN IF NOT EXISTS "
            "sustituido_at_utc VARCHAR(64)") in ddl


def test_f084_r12_tiene_pdf_exige_drive_e_item() -> None:
    """Sin el `item_id` de SharePoint no hay PDF que abrir (mutante 9)."""
    fabrica, repo = _montaje()
    _sembrar(fabrica, "sin-obra", obra_ide=None, obra_codigo=None)
    with fabrica.create_session() as s:
        s.get(ParteDocumentOrm, "sin-obra").sharepoint_item_id = None
        s.commit()
    [fila] = repo.list_partes_con_problemas()
    assert fila["tiene_pdf"] is False


def test_f084_r19_obra_ide_cero_es_una_obra() -> None:
    """R19: con `obra_ide` en los dos (también 0) se compara por él y no
    por el código (mutante 10)."""
    fabrica, repo = _montaje()
    _sembrar(fabrica, "viejo", activo=False, obra_ide=0)
    _sembrar(fabrica, "otro", obra_ide=5)          # mismo código y persona
    repo.recuperar_parte(document_id="viejo")
    assert _doc(fabrica, "viejo").is_active is True


def test_f084_r23_la_descripcion_del_deshacer_lleva_la_obra() -> None:
    """El widget de deshacer nombra la obra casada (mutante 12)."""
    fabrica, repo = _montaje()
    _sembrar(fabrica, "viejo", activo=False)
    repo.recuperar_parte(document_id="viejo")
    [undo] = _undos(fabrica)
    assert undo.description.startswith("Recuperar parte 0100 (")
