# tests/test_f019_bandeja.py
"""F-019 · la bandeja de salida hacia dedicacion en sv4 (R9-R14, R29).

T4: la tabla `dedicacion_bandeja` del ORM (la copia de sv3 es byte a byte
la misma; lo vigila el guardian de raiz de F-010). Aqui se fija su DDL
COMPILADO a PostgreSQL entero, porque es un contrato publicado que lee
otra aplicacion: un tipo, un NOT NULL o una secuencia de mas lo cambian.

Sin BBDD real: SQLite en memoria con el MISMO ORM. Datos SINTETICOS.
"""
from __future__ import annotations

from infrastructure.database.orm_models import Base, DedicacionBandejaOrm
from sqlalchemy import inspect, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable
from tests.dobles import FabricaSesionSqlite

#: El DDL que crea `create_all` en PostgreSQL (R29), literal.
DDL_BANDEJA = """
CREATE TABLE dedicacion_bandeja (
\tregistro_id INTEGER NOT NULL, 
\tversion INTEGER DEFAULT '1' NOT NULL, 
\tvigente BOOLEAN DEFAULT 'true' NOT NULL, 
\trecurso_ide INTEGER DEFAULT '0' NOT NULL, 
\tcodigo_mes VARCHAR(16) DEFAULT '' NOT NULL, 
\tfecha_int INTEGER DEFAULT '0' NOT NULL, 
\tanio INTEGER DEFAULT '0' NOT NULL, 
\tmes INTEGER DEFAULT '0' NOT NULL, 
\tobra_ide INTEGER, 
\tobra_codigo VARCHAR(64), 
\tobra_empresa INTEGER, 
\tpartida_ide INTEGER, 
\tpartida_cod VARCHAR(64), 
\ttipo VARCHAR(16) DEFAULT '' NOT NULL, 
\thoras FLOAT, 
\tincidencia_codigo VARCHAR(8), 
\tincidencia_clase VARCHAR(16), 
\tprueba BOOLEAN DEFAULT 'false' NOT NULL, 
\tenviado_por VARCHAR(255), 
\tenviado_at_utc VARCHAR(64), 
\tretirado_por VARCHAR(255), 
\tretirado_at_utc VARCHAR(64), 
\tactualizado_at_utc VARCHAR(64) DEFAULT '' NOT NULL, 
\tPRIMARY KEY (registro_id)
)

"""


# ============================== T4 · el ORM (R29) ============================== #

def test_f019_r29_sv4_ddl_de_la_bandeja_literal() -> None:
    tabla = Base.metadata.tables["dedicacion_bandeja"]
    ddl = str(CreateTable(tabla).compile(dialect=postgresql.dialect()))
    assert ddl == DDL_BANDEJA


def test_f019_r29_sv4_indice_por_periodo_y_sin_fk() -> None:
    tabla = Base.metadata.tables["dedicacion_bandeja"]
    assert {(i.name, tuple(c.name for c in i.columns), i.unique)
            for i in tabla.indexes} == {
        ("ix_dedicacion_bandeja_periodo", ("anio", "mes"), False)}
    assert tabla.foreign_keys == set()


def test_f019_r29_sv4_create_all_crea_la_bandeja_y_admite_una_fila() -> None:
    fabrica = FabricaSesionSqlite()
    assert "dedicacion_bandeja" in inspect(fabrica.engine).get_table_names()
    with fabrica.create_session() as s:
        s.add(DedicacionBandejaOrm(
            registro_id=7, version=1, vigente=True, recurso_ide=602,
            codigo_mes="MENC", fecha_int=20260302, anio=2026, mes=3,
            tipo="normal", horas=-1.5, prueba=False,
            actualizado_at_utc="2026-03-02T08:00:00+00:00"))
        s.commit()
    with fabrica.create_session() as s:
        fila = s.execute(select(DedicacionBandejaOrm)).scalars().one()
    assert (fila.registro_id, fila.horas, fila.obra_ide) == (7, -1.5, None)


def test_f019_r29_sv4_parte_registros_sigue_con_56_columnas() -> None:
    assert len(Base.metadata.tables["parte_registros"].columns) == 56


# ===================== T6 · el repositorio escribe la bandeja ================== #

import pytest  # noqa: E402
from infrastructure.database.orm_models import (  # noqa: E402
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import (  # noqa: E402
    ParteReviewRepository,
)
from sqlalchemy import text  # noqa: E402
from tests.test_f025_deteccion import TABLA  # noqa: E402

AHORA = "2026-03-02T08:00:00+00:00"
NOMBRE = "Persona Sintetica"
DNI = "00000000T"


def sembrar_mensual(fabrica, *, doc: str = "d1",
                    estado: str | None = "encolado",
                    empresa: int | None = 1) -> list[int]:
    """Un parte de 2026-03-02 con tres lineas de un mensual (recurso 602):
    ordinaria con partida, extra negativa sin partida e incidencia V."""
    with fabrica.create_session() as s:
        s.add(ParteDocumentOrm(
            id=doc, source_filename="parte.pdf",
            source_mime_type="application/pdf", source_sha256="sha" + doc,
            fecha="2026-03-02", fecha_int=20260302, created_at_utc=AHORA,
            obra_ide=10, obra_codigo="0100", obra_nombre="Obra Uno",
            empresa=empresa))
        comun = dict(document_id=doc, empleado_line_no=1, fecha="2026-03-02",
                     fecha_int=20260302, obra_ide=10, obra_codigo="0100",
                     obra_nombre="Obra Uno", empleado_ide=77,
                     empleado_dni=DNI, empleado_nombre=NOMBRE,
                     trabajador_nombre_leido=NOMBRE, recurso_ide=602,
                     recurso_cif=DNI, sigrid_estado=estado)
        regs = [
            ParteRegistroOrm(line_index=0, tipo_hora="normal", horas=8.0,
                             partida_ide=4401, partida_cod="01.02",
                             hora_codigo="MENC", **comun),
            ParteRegistroOrm(line_index=1, tipo_hora="Extra", horas=-1.5,
                             hora_codigo="HE01", **comun),
            ParteRegistroOrm(line_index=2, tipo_hora="V", horas=0.0,
                             es_incidencia=True, incidencia_codigo="V",
                             hora_codigo="CIV", **comun),
        ]
        s.add_all(regs)
        s.commit()
        return [r.id for r in regs]


def _ded(ids, codigo="MENC", recurso=602) -> list[dict]:
    return [{"registro_id": i, "recurso_ide": recurso, "codigo_mes": codigo}
            for i in ids]


def _marcar(repo, ids, **kw):
    kw.setdefault("prueba", False)
    kw.setdefault("incidencias", TABLA)
    kw.setdefault("usuario", "ana")
    return repo.marcar_registros_sigrid(
        escritas=kw.pop("escritas", []), omitidas=[], ya_registradas=[],
        dedicacion=_ded(ids, kw.pop("codigo", "MENC")), **kw)


def _filas(fabrica) -> dict[int, dict]:
    tabla = Base.metadata.tables["dedicacion_bandeja"]
    with fabrica.create_session() as s:
        return {f.registro_id: {c.name: getattr(f, c.name)
                                for c in tabla.columns}
                for f in s.execute(select(DedicacionBandejaOrm)).scalars()}


def _linea(fabrica, rid) -> tuple:
    with fabrica.create_session() as s:
        r = s.get(ParteRegistroOrm, rid)
        return (r.sigrid_estado, r.sigrid_motivo, r.sigrid_registrado_by)


def test_f019_r9_la_linea_queda_en_dedicacion_y_tiene_su_fila() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_mensual(fabrica)
    n = _marcar(ParteReviewRepository(fabrica), ids)
    assert n == 3
    for rid in ids:
        assert _linea(fabrica, rid) == (
            "dedicacion", "enviada a dedicación (MENC)", "ana")
    assert sorted(_filas(fabrica)) == ids


def test_f019_r10_la_fila_lleva_los_datos_de_la_linea_y_del_resultado() -> None:
    fabrica = FabricaSesionSqlite()
    ordinaria, extra, incidencia = sembrar_mensual(fabrica)
    _marcar(ParteReviewRepository(fabrica), [ordinaria, extra, incidencia],
            prueba=True)
    filas = _filas(fabrica)
    f = filas[ordinaria]
    assert f["actualizado_at_utc"] == f["enviado_at_utc"] != ""
    assert {k: v for k, v in f.items()
            if k not in ("enviado_at_utc", "actualizado_at_utc")} == {
        "registro_id": ordinaria, "version": 1, "vigente": True,
        "recurso_ide": 602, "codigo_mes": "MENC", "fecha_int": 20260302,
        "anio": 2026, "mes": 3, "obra_ide": 10, "obra_codigo": "0100",
        "obra_empresa": 1, "partida_ide": 4401, "partida_cod": "01.02",
        "tipo": "normal", "horas": 8.0, "incidencia_codigo": None,
        "incidencia_clase": None, "prueba": True, "enviado_por": "ana",
        "retirado_por": None, "retirado_at_utc": None}
    assert (filas[extra]["tipo"], filas[extra]["horas"],
            filas[extra]["partida_ide"]) == ("extra", -1.5, None)
    assert (filas[incidencia]["tipo"], filas[incidencia]["horas"],
            filas[incidencia]["incidencia_codigo"],
            filas[incidencia]["incidencia_clase"]) == (
        "incidencia", 0.0, "V", "dia_completo")


def test_f019_r10_nunca_nombre_ni_dni() -> None:
    fabrica = FabricaSesionSqlite()
    _marcar(ParteReviewRepository(fabrica), sembrar_mensual(fabrica))
    for fila in _filas(fabrica).values():
        for valor in fila.values():
            assert NOMBRE not in str(valor) and DNI not in str(valor)


def test_f019_r10_sin_tabla_de_incidencias_la_clase_es_nula() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_mensual(fabrica)
    _marcar(ParteReviewRepository(fabrica), ids, incidencias=None)
    assert _filas(fabrica)[ids[2]]["incidencia_clase"] is None
    assert _filas(fabrica)[ids[2]]["incidencia_codigo"] == "V"


def test_f019_r10_el_recurso_del_resultado_manda_y_la_empresa_falta() -> None:
    """sv5 pudo resolver el recurso por DNI (linea sin `recurso_ide`)."""
    fabrica = FabricaSesionSqlite()
    ids = sembrar_mensual(fabrica, empresa=None)
    with fabrica.create_session() as s:
        s.get(ParteRegistroOrm, ids[0]).recurso_ide = None
        s.commit()
    ParteReviewRepository(fabrica).marcar_registros_sigrid(
        escritas=[], omitidas=[], ya_registradas=[], usuario="ana",
        dedicacion=[{"registro_id": ids[0], "recurso_ide": 777,
                     "codigo_mes": "MENC"}])
    fila = _filas(fabrica)[ids[0]]
    assert (fila["recurso_ide"], fila["obra_empresa"], fila["prueba"]) == (
        777, None, False)


def test_f019_r11_la_fila_nueva_nace_en_version_1_y_vigente() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_mensual(fabrica)
    _marcar(ParteReviewRepository(fabrica), ids)
    assert {(f["version"], f["vigente"]) for f in _filas(fabrica).values()} \
        == {(1, True)}


def test_f019_r12_reaplicar_el_mismo_resultado_no_cambia_la_fila() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_mensual(fabrica)
    repo = ParteReviewRepository(fabrica)
    _marcar(repo, ids)
    antes = _filas(fabrica)
    _marcar(repo, ids, usuario="otra")
    assert _filas(fabrica) == antes
    assert _linea(fabrica, ids[0])[0] == "dedicacion"


@pytest.mark.parametrize("cambio", ["codigo", "prueba", "horas", "partida",
                                    "obra"])
def test_f019_r13_otro_contenido_sube_la_version(cambio) -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_mensual(fabrica)
    repo = ParteReviewRepository(fabrica)
    _marcar(repo, ids)
    antes = _filas(fabrica)[ids[0]]
    kw = {}
    if cambio == "codigo":
        kw["codigo"] = "MCAP"
    elif cambio == "prueba":
        kw["prueba"] = True
    else:
        with fabrica.create_session() as s:
            r = s.get(ParteRegistroOrm, ids[0])
            if cambio == "horas":
                r.horas = 7.5
            elif cambio == "partida":
                r.partida_cod = "09.09"
            else:
                r.obra_codigo = "0200"
            s.commit()
    _marcar(repo, ids, usuario="eva", **kw)
    despues = _filas(fabrica)[ids[0]]
    assert (despues["version"], despues["vigente"], despues["enviado_por"]) \
        == (2, True, "eva")
    assert despues["actualizado_at_utc"] > antes["actualizado_at_utc"]
    assert despues["enviado_at_utc"] == despues["actualizado_at_utc"]
    assert _filas(fabrica)[ids[1]]["version"] == (2 if cambio in (
        "codigo", "prueba") else 1)


def test_f019_r13_una_fila_retirada_vuelve_a_vigente_y_sube_version() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_mensual(fabrica)
    repo = ParteReviewRepository(fabrica)
    _marcar(repo, ids)
    with fabrica.create_session() as s:
        fila = s.get(DedicacionBandejaOrm, ids[0])
        fila.vigente, fila.version = False, 2
        fila.retirado_por, fila.retirado_at_utc = "ana", AHORA
        s.commit()
    _marcar(repo, ids)
    f = _filas(fabrica)[ids[0]]
    assert (f["vigente"], f["version"], f["retirado_por"],
            f["retirado_at_utc"]) == (True, 3, None, None)


def test_f019_r14_si_falla_la_bandeja_nada_queda_marcado() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_mensual(fabrica)
    with fabrica.engine.begin() as con:
        con.execute(text("DROP TABLE dedicacion_bandeja"))
    repo = ParteReviewRepository(fabrica)
    with pytest.raises(Exception, match="dedicacion_bandeja"):
        _marcar(repo, ids[:2], escritas=[{"registro_id": ids[2],
                                          "hmoide": 1, "parte_cod": "PT"}])
    for rid in ids:
        assert _linea(fabrica, rid)[0] == "encolado"


def test_f019_r9_un_registro_inexistente_se_ignora() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_mensual(fabrica)
    n = _marcar(ParteReviewRepository(fabrica), [ids[0], 99999])
    assert n == 1
    assert sorted(_filas(fabrica)) == [ids[0]]


def test_f019_r9_el_error_global_no_publica_nada() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_mensual(fabrica)
    ParteReviewRepository(fabrica).marcar_registros_sigrid(
        escritas=[], omitidas=[], ya_registradas=[], usuario="ana",
        registro_ids=ids, error_global="boom", dedicacion=_ded(ids))
    assert _filas(fabrica) == {}
    assert _linea(fabrica, ids[0])[0] == "error"


def test_f019_r9_sin_dedicacion_el_marcado_es_el_de_siempre() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_mensual(fabrica)
    ParteReviewRepository(fabrica).marcar_registros_sigrid(
        escritas=[], omitidas=[{"registro_id": ids[0], "motivo": "x"}],
        ya_registradas=[], usuario="ana")
    assert _filas(fabrica) == {}
    assert _linea(fabrica, ids[0]) == ("omitido", "x", "ana")


def test_f019_r10_sin_recurso_en_el_resultado_vale_el_de_la_linea() -> None:
    fabrica = FabricaSesionSqlite()
    ids = sembrar_mensual(fabrica)
    ParteReviewRepository(fabrica).marcar_registros_sigrid(
        escritas=[], omitidas=[], ya_registradas=[], usuario="ana",
        dedicacion=[{"registro_id": ids[0], "codigo_mes": "MENC"},
                    {"registro_id": ids[1], "recurso_ide": None,
                     "codigo_mes": "MENC"}])
    assert [f["recurso_ide"] for f in _filas(fabrica).values()] == [602, 602]
