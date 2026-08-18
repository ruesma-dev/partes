# tests/test_f010_r7_initialize_sv3.py
"""El arranque de sv3 aplica el DDL GENERADO, no una lista a mano (F-010 R7).

`SqlAlchemyParteRepository.initialize()` es lo que se ejecuta contra el
PostgreSQL compartido cada vez que arranca el worker de persistencia. Lo
que importa comprobar es la SECUENCIA: primero `create_all` (crea las
tablas que falten) y despues, en UNA transaccion, las sentencias de
`ddl_complementario()` en su orden.

No se usa SQLite: no admite `ADD COLUMN IF NOT EXISTS`, asi que el doble
no seria el mismo DDL que va a produccion. Se usa un `engine` doble que
GRABA lo que se le manda (D7 del diseno); la ejecucion real contra
PostgreSQL es la verificacion MANUAL del humano.
"""

from __future__ import annotations

from typing import Self

import pytest
from infrastructure.database.orm_models import Base, ddl_complementario
from infrastructure.database.sqlalchemy_parte_repository import (
    SqlAlchemyParteRepository,
)

#: Fuente del repositorio, para comprobar que no queda DDL escrito a mano.
FUENTE_REPO = (
    __import__("pathlib").Path(__file__).resolve().parents[1]
    / "infrastructure" / "database" / "sqlalchemy_parte_repository.py"
)


class ConexionDoble:
    """Conexion que solo apunta lo que se le pide ejecutar."""

    def __init__(self, eventos: list) -> None:
        self._eventos = eventos

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_excepcion) -> bool:
        return False

    def execute(self, clausula) -> None:
        self._eventos.append(("ddl", str(clausula)))


class EngineDoble:
    """`engine` de mentira: ni driver, ni socket, ni BBDD."""

    def __init__(self, eventos: list) -> None:
        self._eventos = eventos

    def begin(self) -> ConexionDoble:
        self._eventos.append(("begin", None))
        return ConexionDoble(self._eventos)


class FabricaDoble:
    """`SessionFactory` reducida a lo unico que usa `initialize()`."""

    def __init__(self, engine: EngineDoble) -> None:
        self.engine = engine


@pytest.fixture()
def eventos(monkeypatch) -> list:
    """Traza ordenada de `create_all` + cada sentencia ejecutada."""
    registro: list = []

    def create_all_falso(bind=None, **_kwargs) -> None:
        registro.append(("create_all", bind))

    monkeypatch.setattr(Base.metadata, "create_all", create_all_falso)
    return registro


def test_f010_r7_initialize_crea_las_tablas_y_luego_completa_el_esquema(
    eventos: list,
) -> None:
    """`create_all` primero; despues el DDL complementario, en su orden."""
    engine = EngineDoble(eventos)
    SqlAlchemyParteRepository(FabricaDoble(engine)).initialize()

    assert eventos[0] == ("create_all", engine), (
        "create_all tiene que ir ANTES: el DDL complementario completa tablas "
        "que ya existen, no las crea"
    )
    ejecutadas = tuple(texto for tipo, texto in eventos if tipo == "ddl")
    assert ejecutadas == ddl_complementario()


def test_f010_r7_todo_el_ddl_va_en_una_sola_transaccion(eventos: list) -> None:
    """Un arranque a medias dejaria el esquema en un estado indefinido."""
    SqlAlchemyParteRepository(FabricaDoble(EngineDoble(eventos))).initialize()

    assert [tipo for tipo, _ in eventos].count("begin") == 1


def test_f010_r7_no_queda_ddl_escrito_a_mano_en_el_repositorio() -> None:
    """La lista a mano desaparece: es la que se quedo desincronizada.

    Propiedad negativa (misma idea que el guardian R11 de F-002): mientras
    exista una segunda declaracion del esquema, puede volver a divergir.
    """
    fuente = FUENTE_REPO.read_text(encoding="utf-8")

    for rastro in ("_DDL_ALTERS", "_DDL_PARTIAL_UNIQUE", "ADD COLUMN IF NOT EXISTS"):
        assert rastro not in fuente, (
            f"'{rastro}' sigue en sqlalchemy_parte_repository.py: el DDL debe "
            f"salir de ddl_complementario() (orm_models.py), que es la unica "
            f"declaracion del esquema"
        )
