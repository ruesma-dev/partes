# tests/test_f032_recalculo.py
"""F-032 · R38 y R39: caracterizacion del recalculo con la tabla de festivos.

No hay codigo nuevo aqui: el `RecursoConciliador` (que no cambia, R17)
recalcula en cada pasada el reparto ordinaria/extra de TODAS las lineas
libres con el calendario que tenga. Con `TablaCalendarioLaboral`, en
cuanto aparece la fila de un trabajador (la escribe el refresco de su
primer parte tras encender), la pasada de esa ingesta reparte sus dias con
ella (R38); un dia que deja de ser festivo devuelve las horas a
ordinarias. Las congeladas no se recalculan; con `REPARTO_REAJUSTE`, un dia
mixto queda propuesto en `reparto_pendiente` sin tocar lo congelado (R39).

Repositorio de partes REAL sobre SQLite en memoria (mismo ORM) y
repositorio de festivos falso. Datos sinteticos.
"""
from __future__ import annotations

import json

from sqlalchemy import select

from application.services.festivos_guardados import FilaFestivos
from application.services.recurso_conciliador import RecursoConciliador
from infrastructure.calendario.json_calendario_laboral import (
    JsonCalendarioLaboral,
)
from infrastructure.calendario.tabla_calendario_laboral import (
    TablaCalendarioLaboral,
)
from infrastructure.database.orm_models import (
    ParteRegistroOrm,
    RepartoPendienteOrm,
)
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)
from tests.dobles import FabricaSesionSqlite, LookupFake, reshor_par, \
    sembrar_lineas
from tests.test_f045_conciliar import IndiceFijo

DNI = "12345678Z"            # el de `sembrar_lineas`
RECURSO = 501
MARTES = "2026-03-17"        # laborable en el JSON


class RepoFestivos:
    def __init__(self):
        self.filas: dict = {}

    def leer_todas(self):
        return dict(self.filas)

    def poner(self, *fechas):
        self.filas[(DNI, 2026)] = FilaFestivos(
            dni_norm=DNI, ano=2026, festivos={f: None for f in fechas},
            leido_en_utc="2026-11-17T10:00:00Z")


def _montar(*, reajuste=False):
    fabrica = FabricaSesionSqlite()
    festivos = RepoFestivos()
    cal = TablaCalendarioLaboral(
        repositorio=festivos,
        respaldo=JsonCalendarioLaboral(path="config/calendario_laboral.json"))
    conciliador = RecursoConciliador(
        repository=SqlAlchemyParteRepository(fabrica),
        lookup=LookupFake(reshor=reshor_par(RECURSO)),
        calendario=cal, indice_provider=lambda: IndiceFijo(),
        reajuste=reajuste)
    return fabrica, festivos, cal, conciliador


def _lineas(fabrica):
    with fabrica.create_session() as s:
        return {f.id: (f.document_id, f.tipo_hora, f.horas, f.horas_orig,
                       f.extra_auto)
                for f in s.execute(select(ParteRegistroOrm).order_by(
                    ParteRegistroOrm.id)).scalars()}


def _extras_auto(fabrica, documento):
    return [v[2] for v in _lineas(fabrica).values()
            if v[0] == documento and v[4]]


# --------------------------------- R38 ---------------------------------- #

def test_f032_r38_el_martes_pasa_a_festivo_y_vuelve():
    fabrica, festivos, cal, conciliador = _montar()
    (libre,) = sembrar_lineas(fabrica, [{"horas": 8.0,
                                         "recurso_ide": RECURSO}],
                              document_id="doc-libre", fecha=MARTES)
    conciliador.conciliar_todos()
    assert _lineas(fabrica)[libre][2:5] == (8.0, None, False)
    assert _extras_auto(fabrica, "doc-libre") == []

    festivos.poner(MARTES)                 # el refresco guarda la fila
    cal.olvidar()                          # ... e invalida la cache
    conciliador.conciliar_todos()
    assert _lineas(fabrica)[libre][2:4] == (0.0, 8.0)
    assert _extras_auto(fabrica, "doc-libre") == [8.0]

    festivos.poner()                       # Sesame lo quita
    cal.olvidar()
    conciliador.conciliar_todos()
    assert _lineas(fabrica)[libre][2:5] == (8.0, None, False)
    assert _extras_auto(fabrica, "doc-libre") == []


def test_f032_r38_sin_olvidar_la_cache_manda_hasta_60_s():
    """La pasada de la ingesta usa la fila porque el refresco llama a
    `olvidar`; sin esa llamada, la cache de la tabla aun no la ve."""
    fabrica, festivos, cal, conciliador = _montar()
    (libre,) = sembrar_lineas(fabrica, [{"horas": 8.0,
                                         "recurso_ide": RECURSO}],
                              document_id="doc-libre", fecha=MARTES)
    conciliador.conciliar_todos()
    festivos.poner(MARTES)
    conciliador.conciliar_todos()
    assert _lineas(fabrica)[libre][2] == 8.0


# --------------------------------- R39 ---------------------------------- #

def test_f032_r39_las_congeladas_quedan_intactas():
    fabrica, festivos, cal, conciliador = _montar()
    aprobado = sembrar_lineas(fabrica, [{"horas": 8.0,
                                         "recurso_ide": RECURSO}],
                              document_id="doc-aprobado", aprobado=True,
                              fecha="2026-03-16")
    registrado = sembrar_lineas(fabrica, [{"horas": 8.0,
                                           "estado": "registrado",
                                           "recurso_ide": RECURSO}],
                                document_id="doc-reg", fecha="2026-03-17")
    encolado = sembrar_lineas(fabrica, [{"horas": 8.0, "estado": "encolado",
                                         "recurso_ide": RECURSO}],
                              document_id="doc-enc", fecha="2026-03-18")
    dedicacion = sembrar_lineas(fabrica, [{"horas": 8.0,
                                           "estado": "dedicacion",
                                           "recurso_ide": RECURSO}],
                                document_id="doc-ded", fecha="2026-03-19")
    pareja = sembrar_lineas(fabrica, [
        {"horas": 6.0, "horas_orig": 7.0, "recurso_ide": RECURSO},
        {"horas": 1.0, "tipo": "extra", "extra_auto": True,
         "estado": "registrado", "line_index": 0, "recurso_ide": RECURSO}],
        document_id="doc-pareja", fecha="2026-03-20")
    antes = _lineas(fabrica)

    festivos.poner("2026-03-16", "2026-03-17", "2026-03-18", "2026-03-19",
                   "2026-03-20")
    cal.olvidar()
    conciliador.conciliar_todos()

    despues = _lineas(fabrica)
    for rid in aprobado + registrado + encolado + dedicacion + pareja:
        assert despues[rid] == antes[rid], rid
    assert set(despues) == set(antes)      # ni una extra nueva


def test_f032_r39_con_reajuste_el_dia_mixto_queda_propuesto():
    fabrica, festivos, cal, conciliador = _montar(reajuste=True)
    (reg,) = sembrar_lineas(fabrica, [{"horas": 4.0, "estado": "registrado",
                                       "recurso_ide": RECURSO}],
                            document_id="doc-reg", obra_ide=678,
                            fecha=MARTES)
    (libre,) = sembrar_lineas(fabrica, [{"horas": 4.0,
                                         "recurso_ide": RECURSO}],
                              document_id="doc-libre", obra_ide=704,
                              fecha=MARTES)
    conciliador.conciliar_todos()
    with fabrica.create_session() as s:
        assert s.execute(select(RepartoPendienteOrm)).scalars().all() == []

    festivos.poner(MARTES)
    cal.olvidar()
    res = conciliador.conciliar_todos()

    lineas = _lineas(fabrica)
    assert lineas[reg][2:5] == (4.0, None, False)      # en Sigrid: intacta
    with fabrica.create_session() as s:
        (rep,) = s.execute(select(RepartoPendienteOrm)).scalars().all()
        assert (rep.estado, rep.recurso_ide, rep.fecha_int) == (
            "pendiente", RECURSO, 20260317)
        cambios = json.loads(rep.cambios)["cambios"]
    assert any(c["registro_id"] == reg and c["despues"] == 0.0
               for c in cambios)
    assert res["repartos_propuestos"] == 1
    # La libre si va a su ideal: todo extra en el festivo.
    assert lineas[libre][2] == 0.0
