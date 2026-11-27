# tests/test_f084_rastro_reemplazo.py
"""F-084 · R1-R5: el reemplazo de sv3 deja rastro en el parte sustituido.

`save_parte` real sobre SQLite en memoria (mismo ORM). Cuando el parte
nuevo desactiva a otro del mismo dia, obra y trabajador, el viejo guarda
`sustituido_por_id` (el id del nuevo) y `sustituido_at_utc` en la misma
transaccion, sin pasar por la papelera (R1). Entre paginas del mismo
correo se sigue sustituyendo (R2, D2 (a)), pero con un WARNING (R3). La
regla de que se sustituye no cambia (R4). R5: el esquema declara las dos
columnas y `ddl_complementario()` las anade.

Sin red, sin PostgreSQL ni Sigrid. Datos sinteticos, sin DNIs.
"""
from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select

from domain.models.parte_records import (
    EmpleadoMatch,
    ObraMatch,
    ParteDocumento,
    RegistroNormalizado,
)
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ddl_complementario,
)
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests.dobles import FabricaSesionSqlite

VIEJO = "00000000-0000-4000-8000-000000000841"
NUEVO = "00000000-0000-4000-8000-000000000842"
OTRO = "00000000-0000-4000-8000-000000000843"


class _FabricaContadora(FabricaSesionSqlite):
    """La fabrica de SQLite que cuenta los `commit` de sus sesiones."""

    def __init__(self) -> None:
        super().__init__()
        self.commits = 0

    def create_session(self):
        sesion = super().create_session()
        original = sesion.commit

        def _commit() -> None:
            self.commits += 1
            original()

        sesion.commit = _commit  # type: ignore[method-assign]
        return sesion


def _parte(*, nombre: str = "ANA FICTICIA", obra: str = "0100",
           fecha_int: int = 20261123) -> ParteDocumento:
    f = str(fecha_int)
    return ParteDocumento(
        fecha_iso=f"{f[:4]}-{f[4:6]}-{f[6:]}", fecha_int=fecha_int,
        firmado=True, obra=ObraMatch(ide=10, codigo=obra, method="codigo"),
        registros=[RegistroNormalizado(
            line_index=0, empleado_line_no=1, tipo_hora="normal", horas=8.0,
            trabajador_nombre_leido=nombre,
            empleado=EmpleadoMatch(ide=None, nombre=nombre, method="nombre"))])


def _guardar(repo, document_id: str, *, email_id: str | None,
             parte: ParteDocumento | None = None) -> None:
    context: dict = {"document": {"sha256": "sha-" + document_id}}
    if email_id is not None:
        context["email"] = {"id": email_id, "subject": "Partes semana"}
    repo.save_parte(
        document_id=document_id, parte=parte or _parte(), meta={},
        context=context, raw_extraction_json="{}", raw_context_json="{}",
        review_required=False)


def _doc(fabrica, document_id: str) -> ParteDocumentOrm:
    with fabrica.create_session() as s:
        return s.execute(select(ParteDocumentOrm)
                         .where(ParteDocumentOrm.id == document_id)
                         ).scalar_one()


# ============================ R1 · el rastro ============================ #

def test_f084_r1_el_reemplazo_escribe_quien_y_cuando() -> None:
    fabrica = FabricaSesionSqlite()
    repo = SqlAlchemyParteRepository(fabrica)
    _guardar(repo, VIEJO, email_id="correo-a")
    _guardar(repo, NUEVO, email_id="correo-b")
    viejo = _doc(fabrica, VIEJO)
    assert viejo.is_active is False
    assert viejo.sustituido_por_id == NUEVO
    momento = datetime.fromisoformat(viejo.sustituido_at_utc)
    assert momento.utcoffset() is not None
    assert momento.utcoffset().total_seconds() == 0
    # No va a la papelera: ni hora ni autor de borrado.
    assert viejo.deleted_at_utc is None
    assert viejo.deleted_by is None
    nuevo = _doc(fabrica, NUEVO)
    assert nuevo.is_active is True
    assert nuevo.sustituido_por_id is None
    assert nuevo.sustituido_at_utc is None


def test_f084_r1_el_rastro_va_en_el_mismo_commit_que_el_nuevo() -> None:
    fabrica = _FabricaContadora()
    repo = SqlAlchemyParteRepository(fabrica)
    _guardar(repo, VIEJO, email_id="correo-a")
    antes = fabrica.commits
    _guardar(repo, NUEVO, email_id="correo-b")
    assert fabrica.commits - antes == 1
    assert _doc(fabrica, VIEJO).sustituido_por_id == NUEVO


def test_f084_r1_un_parte_que_no_se_sustituye_no_lleva_rastro() -> None:
    fabrica = FabricaSesionSqlite()
    repo = SqlAlchemyParteRepository(fabrica)
    _guardar(repo, VIEJO, email_id="correo-a")
    viejo = _doc(fabrica, VIEJO)
    assert viejo.is_active is True
    assert viejo.sustituido_por_id is None
    assert viejo.sustituido_at_utc is None


# ===================== R2 · mismo envio, se sustituye =================== #

def test_f084_r2_entre_paginas_del_mismo_envio_se_sigue_sustituyendo() -> None:
    fabrica = FabricaSesionSqlite()
    repo = SqlAlchemyParteRepository(fabrica)
    _guardar(repo, VIEJO, email_id="correo-mismo")
    _guardar(repo, NUEVO, email_id="correo-mismo")
    viejo = _doc(fabrica, VIEJO)
    assert viejo.is_active is False
    assert viejo.sustituido_por_id == NUEVO
    assert viejo.email_id == _doc(fabrica, NUEVO).email_id == "correo-mismo"
    assert _doc(fabrica, NUEVO).is_active is True


# ================== R3 · WARNING del mismo envio ======================== #

def _registros(caplog, nivel: int) -> list[str]:
    return [r.getMessage() for r in caplog.records
            if r.levelno == nivel and "[parte-repo] reemplazo" in
            r.getMessage()]


def test_f084_r3_mismo_envio_deja_un_warning_con_los_dos_ids(caplog) -> None:
    fabrica = FabricaSesionSqlite()
    repo = SqlAlchemyParteRepository(fabrica)
    _guardar(repo, VIEJO, email_id="correo-mismo")
    caplog.clear()
    with caplog.at_level(logging.INFO):
        _guardar(repo, NUEVO, email_id="correo-mismo")
    avisos = [m for m in _registros(caplog, logging.WARNING)
              if "mismo envio" in m]
    assert len(avisos) == 1
    aviso = avisos[0]
    assert aviso.startswith("[parte-repo] reemplazo del mismo envio")
    assert NUEVO in aviso and VIEJO in aviso
    assert aviso.index(NUEVO) < aviso.index(VIEJO)   # «nuevo sustituye a viejo»
    assert "fecha_int=20261123" in aviso
    assert "obra=0100" in aviso
    # Sin nombres de personas.
    assert "ANA" not in aviso and "FICTICIA" not in aviso


def test_f084_r3_otro_envio_sigue_con_el_info_de_hoy(caplog) -> None:
    fabrica = FabricaSesionSqlite()
    repo = SqlAlchemyParteRepository(fabrica)
    _guardar(repo, VIEJO, email_id="correo-a")
    caplog.clear()
    with caplog.at_level(logging.INFO):
        _guardar(repo, NUEVO, email_id="correo-b")
    assert not [m for m in _registros(caplog, logging.WARNING)]
    infos = _registros(caplog, logging.INFO)
    assert len(infos) == 1 and "desactivados 1 parte(s)" in infos[0]


def test_f084_r3_sin_correo_en_ninguno_no_es_mismo_envio(caplog) -> None:
    fabrica = FabricaSesionSqlite()
    repo = SqlAlchemyParteRepository(fabrica)
    _guardar(repo, VIEJO, email_id=None)
    caplog.clear()
    with caplog.at_level(logging.INFO):
        _guardar(repo, NUEVO, email_id=None)
    assert _doc(fabrica, VIEJO).sustituido_por_id == NUEVO
    assert not _registros(caplog, logging.WARNING)


def test_f084_r3_correo_vacio_no_es_mismo_envio(caplog) -> None:
    fabrica = FabricaSesionSqlite()
    repo = SqlAlchemyParteRepository(fabrica)
    _guardar(repo, VIEJO, email_id="")
    caplog.clear()
    with caplog.at_level(logging.INFO):
        _guardar(repo, NUEVO, email_id="")
    assert _doc(fabrica, VIEJO).is_active is False
    assert not _registros(caplog, logging.WARNING)


# ============ R4 · la regla de que se sustituye no cambia =============== #

def test_f084_r4_otro_trabajador_ni_se_sustituye_ni_lleva_rastro() -> None:
    fabrica = FabricaSesionSqlite()
    repo = SqlAlchemyParteRepository(fabrica)
    _guardar(repo, VIEJO, email_id="correo-mismo")
    _guardar(repo, NUEVO, email_id="correo-mismo",
             parte=_parte(nombre="LUIS INVENTADO"))
    viejo = _doc(fabrica, VIEJO)
    assert viejo.is_active is True
    assert viejo.sustituido_por_id is None


def test_f084_r4_otra_obra_u_otro_dia_no_se_sustituyen() -> None:
    fabrica = FabricaSesionSqlite()
    repo = SqlAlchemyParteRepository(fabrica)
    _guardar(repo, VIEJO, email_id="correo-mismo")
    _guardar(repo, NUEVO, email_id="correo-mismo", parte=_parte(obra="0200"))
    _guardar(repo, OTRO, email_id="correo-mismo",
             parte=_parte(fecha_int=20261124))
    viejo = _doc(fabrica, VIEJO)
    assert viejo.is_active is True
    assert viejo.sustituido_por_id is None


# ======================= R5 · esquema y DDL ============================== #

def test_f084_r5_el_orm_declara_las_dos_columnas_nullables() -> None:
    tabla = ParteDocumentOrm.__table__
    por_id = tabla.c.sustituido_por_id
    hora = tabla.c.sustituido_at_utc
    assert por_id.type.length == 36 and por_id.nullable
    assert hora.type.length == 64 and hora.nullable
    assert por_id.server_default is None and hora.server_default is None
    assert por_id.default is None and hora.default is None
    assert not por_id.index and not hora.index


def test_f084_r5_el_ddl_de_arranque_las_anade() -> None:
    sentencias = ddl_complementario()
    prefijo = "ALTER TABLE parte_documents ADD COLUMN IF NOT EXISTS "
    assert prefijo + "sustituido_por_id VARCHAR(36)" in sentencias
    assert prefijo + "sustituido_at_utc VARCHAR(64)" in sentencias
