# tests/test_f010_r8_initialize_sv4.py
"""El arranque del portal aplica el MISMO DDL generado que sv3 (F-010 R8).

sv4 tenia ~80 lineas de DDL escrito a mano: los `ALTER` de las columnas
`sigrid_*` y del casado partida/recurso, un `CREATE TABLE IF NOT EXISTS`
de `empleado_alias` y otro de `undo_log` (que `create_all` ya hacia) y un
parche suelto para `undo_log.actor`. Esa lista no cubria `horas_orig` ni
`extra_auto`, que sv3 si declaraba: dos servicios completando la MISMA
base con dos listas distintas.

Ahora los dos ejecutan `ddl_complementario()` del ORM, en el mismo orden.
Lo que NO cambia es el contrato de arranque de sv4 (D6 del diseno): sigue
devolviendo `True`/`False` en vez de propagar, porque el portal arranca
igual y ensena "tablas no listas" en vez de no arrancar.

Mismo doble que R7 en sv3: un `engine` que graba lo que se le manda; ni
red, ni PostgreSQL, ni SQLite (que no admite `ADD COLUMN IF NOT EXISTS`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Self

import pytest
from infrastructure.database.orm_models import Base, ddl_complementario
from infrastructure.database.parte_repository import ParteReviewRepository

#: Fuente del repositorio del portal, para la propiedad negativa.
FUENTE_REPO = (
    Path(__file__).resolve().parents[1]
    / "infrastructure" / "database" / "parte_repository.py"
)


class ConexionDoble:
    def __init__(self, eventos: list) -> None:
        self._eventos = eventos

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_excepcion) -> bool:
        return False

    def execute(self, clausula) -> None:
        self._eventos.append(("ddl", str(clausula)))


class EngineDoble:
    """`engine` de mentira. Con `revienta`, `begin()` falla como fallaria
    un PostgreSQL caido o sin permisos."""

    def __init__(self, eventos: list, *, revienta: bool = False) -> None:
        self._eventos = eventos
        self._revienta = revienta

    def begin(self) -> ConexionDoble:
        if self._revienta:
            raise RuntimeError("no hay BBDD")
        self._eventos.append(("begin", None))
        return ConexionDoble(self._eventos)


class FabricaDoble:
    def __init__(self, engine: EngineDoble) -> None:
        self.engine = engine


@pytest.fixture()
def eventos(monkeypatch) -> list:
    registro: list = []

    def create_all_falso(bind=None, **_kwargs) -> None:
        registro.append(("create_all", bind))

    monkeypatch.setattr(Base.metadata, "create_all", create_all_falso)
    return registro


def test_f010_r8_initialize_ejecuta_el_mismo_generador_que_sv3(
    eventos: list,
) -> None:
    """create_all primero y despues el DDL complementario, en su orden."""
    engine = EngineDoble(eventos)

    assert ParteReviewRepository(FabricaDoble(engine)).initialize() is True

    assert eventos[0] == ("create_all", engine)
    ejecutadas = tuple(texto for tipo, texto in eventos if tipo == "ddl")
    assert ejecutadas == ddl_complementario()


def test_f010_r8_todo_el_ddl_va_en_una_sola_transaccion(eventos: list) -> None:
    ParteReviewRepository(FabricaDoble(EngineDoble(eventos))).initialize()

    assert [tipo for tipo, _ in eventos].count("begin") == 1


def test_f010_r8_si_la_bbdd_falla_devuelve_false_sin_propagar(
    eventos: list, caplog
) -> None:
    """Contrato de arranque de sv4 (D6): el portal arranca igual.

    sv3 propaga (un worker con el esquema roto no debe procesar nada); el
    portal prefiere levantarse y ensenar el error. F-010 no unifica eso.
    """
    engine = EngineDoble(eventos, revienta=True)

    with caplog.at_level("ERROR"):
        resultado = ParteReviewRepository(FabricaDoble(engine)).initialize()

    assert resultado is False
    assert caplog.records, "un fallo de esquema silencioso es indepurable"
    assert any(r.exc_info for r in caplog.records), (
        "el log tiene que llevar la traza (logger.exception), no solo un texto"
    )


def test_f010_r8_no_queda_ddl_escrito_a_mano_en_el_portal() -> None:
    """Ni ALTER, ni CREATE TABLE, ni el parche de `undo_log.actor`.

    Mientras exista una segunda declaracion del esquema puede volver a
    divergir de la de sv3: es justo lo que paso.
    """
    fuente = FUENTE_REPO.read_text(encoding="utf-8")

    for rastro in ("ADD COLUMN IF NOT EXISTS", "CREATE TABLE IF NOT EXISTS"):
        assert rastro not in fuente, (
            f"'{rastro}' sigue en parte_repository.py: el DDL de arranque debe "
            f"salir de ddl_complementario() (orm_models.py), igual que en sv3"
        )
