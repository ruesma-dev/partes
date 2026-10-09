# tests/test_f042_domingo_a_jueves.py
"""F-042 · R19-R21: un parte de domingo pasado a jueves, recalculado.

El caso que pidio la feature (obra 0694, 2026-10-09): la IA leyo «1/10/26»
como domingo 11, sv3 lo repartio como no laborable (bases a 0 con
`horas_orig` y todo a `extra_auto`) y el humano paso la fecha al jueves 1.
sv4 cambia la fecha del documento y de TODAS sus lineas (tambien las
`extra_auto`) y, desde F-042, pide un recalculo por `q-persistencia`.

Aqui se ejercita el ciclo completo con el repositorio REAL (SQLite en
memoria, mismo ORM), el `RecursoConciliador` real y el handler real del
worker. Solo los maestros de Sigrid son dobles: cada linea casa con el
recurso de su `empleado_reside` y todos tienen el par laborable/extra con
candef 8.

El oraculo de R19 no es una tabla escrita a mano: es el MISMO parte
sembrado ya en jueves en otra base y pasado una vez por el conciliador.

Todo SINTETICO (DNIs de prueba, obra 10, recursos 501-503).
"""
from __future__ import annotations

import pytest
from sqlalchemy import select, update

from application.services.recurso_conciliador import RecursoConciliador
from application.services.seleccion_sigrid import ResolucionRecurso
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from interface_adapters.workers.despacho import construir_handler
from tests.dobles import (
    CalendarioFake,
    FabricaSesionSqlite,
    LookupFake,
    reshor_par,
)

DOMINGO = "2026-10-11"
JUEVES = "2026-10-01"
#: Fines de semana de las dos semanas en juego: el jueves no es el ultimo
#: laborable de su semana (lo es el viernes), asi que su jornada es el
#: candef (8 h).
NO_LABORABLES = {"2026-10-03", "2026-10-04", "2026-10-10", DOMINGO}

#: (reside, DNI sintetico, horas) de cada linea del parte de la obra.
TRABAJADORES = [(501, "00000001R", 8.5), (502, "00000002W", 9.0),
                (503, "00000003A", 8.5)]

MENSAJE = {"tipo": "recalcular", "motivo": "cambio_fecha",
           "document_id": "doc-movido", "solicitado_por": "revisor@ejemplo",
           "solicitado_at_utc": "2026-10-09T10:00:00+00:00"}


class IndicePorReside:
    """Casa cada linea con el recurso de su `empleado_reside`."""

    recursos: list = []

    def empresa_de_obra(self, obra_ide):  # noqa: ARG002
        return None

    def elegir_recurso(self, dni, empleado_ide, reside, empresa,  # noqa: ARG002
                       fecha):  # noqa: ARG002
        return ResolucionRecurso(ide=reside, motivo="ok")


class NadaDeIngesta:
    """Blob y pipeline que revientan si el recalculo los tocase."""

    def descargar(self, *_a):
        raise AssertionError("un recalculo no descarga blobs")

    def run(self, *_a):
        raise AssertionError("un recalculo no ejecuta el pipeline")


def _conciliador(fabrica) -> RecursoConciliador:
    reshor = [f for reside, _dni, _h in TRABAJADORES
              for f in reshor_par(reside)]
    return RecursoConciliador(
        repository=SqlAlchemyParteRepository(fabrica),
        lookup=LookupFake(reshor=reshor),
        calendario=CalendarioFake(set(NO_LABORABLES)),
        indice_provider=lambda: IndicePorReside(),
    )


def _handler(conciliador: RecursoConciliador):
    nada = NadaDeIngesta()
    return construir_handler(
        blob=nada, pipeline=nada, recurso_conciliador=conciliador,
        contenedor_input="input", contenedor_envelopes="envelopes")


def _sembrar(fabrica, *, document_id: str, fecha: str,
             lineas: list[tuple[int, str, float]], aprobado: bool = False,
             estado: str | None = None, recurso: bool = False) -> None:
    """Un parte con una linea por trabajador (`line_index` = posicion)."""
    fint = int(fecha.replace("-", ""))
    with fabrica.create_session() as s:
        s.add(ParteDocumentOrm(
            id=document_id, source_filename="parte.pdf",
            source_mime_type="application/pdf",
            source_sha256="sha-" + document_id, fecha=fecha, fecha_int=fint,
            created_at_utc="2026-10-09T08:00:00+00:00", obra_ide=10,
            obra_codigo="0100", obra_nombre="Obra Uno", approved=aprobado))
        for i, (reside, dni, horas) in enumerate(lineas):
            s.add(ParteRegistroOrm(
                document_id=document_id, line_index=i, empleado_line_no=1,
                fecha=fecha, fecha_int=fint, obra_ide=10, obra_codigo="0100",
                obra_nombre="Obra Uno", empleado_dni=dni,
                empleado_reside=reside, recurso_ide=reside if recurso else None,
                tipo_hora="normal", horas=horas, sigrid_estado=estado,
                hora_ide=100, hora_codigo="HL01"))
        s.commit()


def _cambiar_fecha(fabrica, document_id: str, fecha: str) -> None:
    """Lo mismo que hace sv4 `update_parte_fecha`: documento y TODAS sus
    lineas, extras automaticas incluidas."""
    fint = int(fecha.replace("-", ""))
    with fabrica.create_session() as s:
        s.execute(update(ParteDocumentOrm)
                  .where(ParteDocumentOrm.id == document_id)
                  .values(fecha=fecha, fecha_int=fint))
        s.execute(update(ParteRegistroOrm)
                  .where(ParteRegistroOrm.document_id == document_id)
                  .values(fecha=fecha, fecha_int=fint))
        s.commit()


def _lineas(fabrica, document_id: str) -> list[tuple]:
    """(line_index, empleado_line_no, tipo_hora, extra_auto, horas,
    horas_orig) del parte, ordenadas."""
    with fabrica.create_session() as s:
        filas = s.execute(
            select(ParteRegistroOrm.line_index,
                   ParteRegistroOrm.empleado_line_no,
                   ParteRegistroOrm.tipo_hora, ParteRegistroOrm.extra_auto,
                   ParteRegistroOrm.horas, ParteRegistroOrm.horas_orig)
            .where(ParteRegistroOrm.document_id == document_id)
        ).all()
    return sorted(tuple(f) for f in filas)


def _todo(fabrica) -> list[tuple]:
    """Todas las columnas que importan de todas las filas (sin el id, que
    cambia al recrear las extras)."""
    with fabrica.create_session() as s:
        filas = s.execute(
            select(ParteRegistroOrm.document_id, ParteRegistroOrm.line_index,
                   ParteRegistroOrm.empleado_line_no,
                   ParteRegistroOrm.tipo_hora, ParteRegistroOrm.extra_auto,
                   ParteRegistroOrm.horas, ParteRegistroOrm.horas_orig,
                   ParteRegistroOrm.fecha_int, ParteRegistroOrm.recurso_ide,
                   ParteRegistroOrm.hora_codigo,
                   ParteRegistroOrm.sigrid_estado)
        ).all()
    return sorted(tuple(f) for f in filas)


def _domingo_movido_a_jueves(fabrica) -> RecursoConciliador:
    """Siembra el parte en domingo, lo reparte, y le cambia la fecha."""
    _sembrar(fabrica, document_id="doc-movido", fecha=DOMINGO,
             lineas=TRABAJADORES)
    conciliador = _conciliador(fabrica)
    conciliador.conciliar_todos()
    # Punto de partida: el reparto del domingo (todo a extra).
    assert _lineas(fabrica, "doc-movido") == [
        (0, 1, "extra", True, 8.5, None), (0, 1, "normal", False, 0.0, 8.5),
        (1, 1, "extra", True, 9.0, None), (1, 1, "normal", False, 0.0, 9.0),
        (2, 1, "extra", True, 8.5, None), (2, 1, "normal", False, 0.0, 8.5),
    ]
    _cambiar_fecha(fabrica, "doc-movido", JUEVES)
    return conciliador


# ===================== R19 · queda como si fuera jueves ================= #

def test_f042_r19_el_recalculo_deja_el_reparto_del_jueves() -> None:
    fabrica = FabricaSesionSqlite()
    conciliador = _domingo_movido_a_jueves(fabrica)

    _handler(conciliador)(MENSAJE)

    # Oraculo: el mismo parte ingerido ya en jueves, una pasada.
    oraculo = FabricaSesionSqlite()
    _sembrar(oraculo, document_id="doc-movido", fecha=JUEVES,
             lineas=TRABAJADORES)
    _conciliador(oraculo).conciliar_todos()

    assert _lineas(fabrica, "doc-movido") == _lineas(oraculo, "doc-movido")
    # Y el oraculo es el esperado: candef 8, el exceso a extra.
    assert _lineas(fabrica, "doc-movido") == [
        (0, 1, "extra", True, 0.5, None), (0, 1, "normal", False, 8.0, 8.5),
        (1, 1, "extra", True, 1.0, None), (1, 1, "normal", False, 8.0, 9.0),
        (2, 1, "extra", True, 0.5, None), (2, 1, "normal", False, 8.0, 8.5),
    ]


def test_f042_r19_sin_recalculo_el_reparto_del_domingo_se_queda() -> None:
    """Caracterizacion del defecto: sin el mensaje, nada cambia."""
    fabrica = FabricaSesionSqlite()
    _domingo_movido_a_jueves(fabrica)
    assert [f[4] for f in _lineas(fabrica, "doc-movido")] == [
        8.5, 0.0, 9.0, 0.0, 8.5, 0.0]


# ================ R20 · lo congelado ni cambia y si cuenta ============== #

@pytest.mark.parametrize("congelacion", [
    {"estado": "registrado"}, {"estado": "encolado"},
    {"estado": "dedicacion"}, {"aprobado": True},
])
def test_f042_r20_las_congeladas_no_cambian_y_cuentan(congelacion) -> None:
    fabrica = FabricaSesionSqlite()
    # Otro parte del jueves, del trabajador 501, con 8 h ya congeladas.
    _sembrar(fabrica, document_id="doc-congelado", fecha=JUEVES,
             lineas=[(501, "00000001R", 8.0)], recurso=True, **congelacion)
    conciliador = _domingo_movido_a_jueves(fabrica)
    congeladas_antes = _lineas(fabrica, "doc-congelado")

    _handler(conciliador)(MENSAJE)

    assert _lineas(fabrica, "doc-congelado") == congeladas_antes
    assert congeladas_antes == [(0, 1, "normal", False, 8.0, None)]
    # Las 8 h congeladas cuentan en el dia de 501: sus 8,5 h, enteras a
    # extra. Los otros dos trabajadores, como en R19.
    assert _lineas(fabrica, "doc-movido") == [
        (0, 1, "extra", True, 8.5, None), (0, 1, "normal", False, 0.0, 8.5),
        (1, 1, "extra", True, 1.0, None), (1, 1, "normal", False, 8.0, 9.0),
        (2, 1, "extra", True, 0.5, None), (2, 1, "normal", False, 8.0, 8.5),
    ]


# ===================== R21 · dos recalculos = uno ======================= #

def test_f042_r21_dos_recalculos_dejan_lo_mismo_que_uno() -> None:
    fabrica = FabricaSesionSqlite()
    _sembrar(fabrica, document_id="doc-congelado", fecha=JUEVES,
             lineas=[(502, "00000002W", 4.0)], recurso=True,
             estado="registrado")
    conciliador = _domingo_movido_a_jueves(fabrica)
    handler = _handler(conciliador)

    handler(MENSAJE)
    tras_uno = _todo(fabrica)
    handler(MENSAJE)
    tras_dos = _todo(fabrica)

    assert tras_dos == tras_uno
    extras = [f for f in tras_dos if f[4]]
    assert len(extras) == 3
    assert sorted(f[5] for f in extras) == [0.5, 0.5, 5.0]
