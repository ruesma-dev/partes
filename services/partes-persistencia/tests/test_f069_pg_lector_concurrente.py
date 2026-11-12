# tests/test_f069_pg_lector_concurrente.py
"""F-069 · M1 (R1, R9, R15) contra un PostgreSQL REAL y desechable.

Se SALTA sin la variable `F069_PG_URL` (la suite normal no toca BBDD). Con
ella, apunta a un PostgreSQL local de usar y tirar, nunca a Azure:

    docker run --rm -d --name pg-f069 -e POSTGRES_PASSWORD=<local> \\
        -p 55432:5432 postgres:16
    F069_PG_URL=postgresql+psycopg://postgres:<local>@localhost:55432/postgres
    python -m pytest tests/test_f069_pg_lector_concurrente.py -v
    docker stop pg-f069

El test BORRA y crea las tablas del ORM en esa base. Lo que vigila:
- R9: un hilo lector en READ COMMITTED consulta en bucle durante 20
  pasadas y nunca ve una base partida sin su extra, ni una extra sin su
  base partida, ni otros ids de extra que los de la primera pasada.
- R1: la secuencia de `parte_registros` no avanza en esas 20 pasadas.
- R15: mientras `escribir_pasada` tiene la transaccion abierta, un UPDATE
  de sv4 sobre una fila bloqueada espera (aqui, `lock_timeout` corto).
Datos sinteticos.
"""
from __future__ import annotations

import os
import threading
from collections import Counter

import pytest

PG_URL = os.environ.get("F069_PG_URL")

pytestmark = pytest.mark.skipif(
    not PG_URL, reason="M1 de F-069: sin F069_PG_URL (PostgreSQL desechable)")


class FabricaPg:
    """`SessionFactory` minima sobre el PostgreSQL desechable."""

    def __init__(self, url: str) -> None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from infrastructure.database.orm_models import Base

        self.engine = create_engine(url, future=True, pool_size=5)
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self._sessionmaker = sessionmaker(
            bind=self.engine, expire_on_commit=False, future=True)

    def create_session(self):
        return self._sessionmaker()


_PAREJAS = (
    "SELECT document_id, line_index, empleado_line_no, fecha_int, "
    "horas, horas_orig, extra_auto, id FROM parte_registros "
    "WHERE tipo_hora = 'normal' OR extra_auto ORDER BY id")


def _estado(conn) -> dict:
    """Por clave: (bases (id, horas, horas_orig), extras (id, horas))."""
    from sqlalchemy import text

    claves: dict = {}
    for d, li, eln, f, horas, orig, auto, rid in conn.execute(text(_PAREJAS)):
        bases, extras = claves.setdefault((d, li, eln, f), ([], []))
        if auto:
            extras.append((rid, horas))
        else:
            bases.append((rid, horas, orig))
    return {k: (tuple(b), tuple(e)) for k, (b, e) in claves.items()}


def _violaciones(estado: dict, inicial: dict) -> list[str]:
    """Nada cambia entre pasadas: toda lectura debe ver el estado inicial.

    Una base revertida sin su extra, una extra sin su base recortada o un
    id de extra distinto son, todos, una pareja distinta de la inicial.
    """
    malas: list[str] = []
    for clave in sorted(set(estado) | set(inicial), key=str):
        actual, antes = estado.get(clave), inicial.get(clave)
        if actual == antes:
            continue
        ids_a = {r for r, _ in (actual or ((), ()))[1]}
        ids_b = {r for r, _ in (antes or ((), ()))[1]}
        malas.append("pareja a medias" if ids_a != ids_b and not ids_a
                     else "id de extra distinto" if ids_a != ids_b
                     else "pareja distinta")
    return malas


@pytest.fixture()
def fabrica():
    f = FabricaPg(PG_URL)
    yield f
    f.engine.dispose()


def _sembrar(fabrica) -> None:
    from tests.f069_comun import base, sembrar

    for n in range(5):
        sembrar(fabrica, [base(10.0 + n), base(9.0, li=1)],
                document_id=f"doc-{n}", fecha=f"2026-10-0{1 + (n % 2)}")
    sembrar(fabrica, [base(4.0)], document_id="doc-s", fecha="2026-10-03")


def _secuencia(fabrica) -> int:
    from sqlalchemy import text

    with fabrica.engine.connect() as conn:
        return int(conn.execute(text(
            "SELECT last_value FROM parte_registros_id_seq")).scalar())


def test_f069_m1_lector_concurrente_nunca_ve_una_pareja_a_medias(fabrica):
    from tests.f069_comun import conciliador_f069

    _sembrar(fabrica)
    c = conciliador_f069(fabrica)
    c.conciliar_todos()
    with fabrica.engine.connect() as conn:
        inicial = _estado(conn)
    assert any(extras for _b, extras in inicial.values())
    secuencia = _secuencia(fabrica)

    parar = threading.Event()
    vistas: list[str] = []
    lecturas = [0]

    def _lector() -> None:
        while not parar.is_set():
            with fabrica.engine.connect() as conn:
                vistas.extend(_violaciones(_estado(conn), inicial))
            lecturas[0] += 1

    hilo = threading.Thread(target=_lector, daemon=True)
    hilo.start()
    try:
        for _ in range(20):
            c.conciliar_todos()
    finally:
        parar.set()
        hilo.join(timeout=30)
    assert lecturas[0] > 20, "el lector apenas leyo"
    assert Counter(vistas) == Counter()
    assert _secuencia(fabrica) == secuencia


def test_f069_m1_r15_escribir_bloquea_las_filas_de_la_pareja(fabrica):
    from sqlalchemy import text
    from sqlalchemy.exc import OperationalError

    from infrastructure.database import sqlalchemy_parte_repository as mod
    from tests.f069_comun import base, extra, sembrar

    b, _e = sembrar(fabrica, [base(8.0, 10.0), extra(2.0)])
    repo = mod.SqlAlchemyParteRepository(fabrica)
    lectura = repo.leer_pasada()
    bloqueado, seguir = threading.Event(), threading.Event()
    original = mod.SqlAlchemyParteRepository._bloquear_documentos

    def _bloquear_y_esperar(session, updates, splits):
        filas = original(session, updates, splits)
        bloqueado.set()
        seguir.wait(timeout=30)
        return filas

    split = {"normal_id": b, "horas_norm": 8.0, "horas_orig": 10.0,
             "extra_horas": 2.0, "hora_ext_ide": 2, "hora_ext_cod": "HE01",
             "hora_ext_desc": "Hora extra", "hora_ext_ext": 1,
             "hora_candef": 8.0}
    errores: list[BaseException] = []

    def _escribir() -> None:
        try:
            repo.escribir_pasada(lectura, [], [split])
        except BaseException as exc:  # pragma: no cover - se informa
            errores.append(exc)

    mod.SqlAlchemyParteRepository._bloquear_documentos = staticmethod(
        _bloquear_y_esperar)
    try:
        hilo = threading.Thread(target=_escribir, daemon=True)
        hilo.start()
        assert bloqueado.wait(timeout=30)
        with fabrica.engine.connect() as conn:
            conn.exec_driver_sql("SET lock_timeout = '300ms'")
            with pytest.raises(OperationalError):
                conn.execute(text(
                    "UPDATE parte_registros SET horas = 7 WHERE id = :i"),
                    {"i": b})
        seguir.set()
        hilo.join(timeout=30)
    finally:
        seguir.set()
        mod.SqlAlchemyParteRepository._bloquear_documentos = staticmethod(
            original)
    assert errores == []
