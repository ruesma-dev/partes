# tests/test_f061_limpieza.py
"""F-061 · reglas puras del parte vacío y limpieza de los existentes.

- Funciones puras de `application/services/parte_vacio.py` (design §4.1).
- R14–R18: el script `limpiar_partes_vacios.py` y los métodos del
  repositorio que usa (`partes_vacios_activos`, `limpiar_vacios`).

Ni red ni PostgreSQL: SQLite en memoria con el ORM real. Datos
sintéticos.
"""
from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from dobles import FabricaSesionSqlite, sembrar_parte
from sqlalchemy import event, select

import limpiar_partes_vacios as script
from application.services.congelacion import CongeladoError
from application.services.parte_vacio import (
    MARCA_RETIRADO,
    MOTIVO_DUPLICADO_ACTIVO,
    PARTES_SIGRID_PROTEGIDOS,
    DuplicadoActivoError,
    categoria_vacio,
    empleados_leidos,
    es_retirado,
    marca_retirado,
    motivo_exclusion_limpieza,
)
from infrastructure.database.orm_models import (
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.database.parte_repository import ParteReviewRepository

# ========================= Funciones puras ============================ #

def test_f061_marca_retirado() -> None:
    assert MARCA_RETIRADO == "sin-lineas"
    assert marca_retirado(None) == "sin-lineas"
    assert marca_retirado("") == "sin-lineas"
    assert marca_retirado("ana") == "sin-lineas · ana"
    largo = marca_retirado("x" * 400)
    assert len(largo) == 255
    assert largo.startswith("sin-lineas · x")


@pytest.mark.parametrize("activo,borrado,por,esperado", [
    (False, None, "sin-lineas", True),
    (False, None, "sin-lineas · ana", True),
    (False, None, None, False),            # reemplazo de sv3 (DA7)
    (False, None, "ana", False),
    (False, "2026-10-26T00:00:00", "sin-lineas", False),   # papelera
    (True, None, "sin-lineas", False),
])
def test_f061_es_retirado(activo, borrado, por, esperado) -> None:
    assert es_retirado(is_active=activo, deleted_at_utc=borrado,
                       deleted_by=por) is esperado


def test_f061_partes_sigrid_protegidos_lista_cerrada() -> None:
    assert PARTES_SIGRID_PROTEGIDOS == frozenset(
        {"PT26/00373", "PT26/00375", "PT26/00376"})


def test_f061_duplicado_activo_error() -> None:
    error = DuplicadoActivoError()
    assert error.motivo == MOTIVO_DUPLICADO_ACTIVO
    assert str(error) == MOTIVO_DUPLICADO_ACTIVO
    assert not isinstance(error, CongeladoError)
    assert "elimínalo de la papelera" in MOTIVO_DUPLICADO_ACTIVO


@pytest.mark.parametrize("aprobado,estados,partes,esperado", [
    (False, [], [], None),
    (False, [None, "omitido", "error", "borrado_sigrid"], [None], None),
    (True, [], [], "aprobado"),
    (True, ["registrado"], ["PT26/00373"], "aprobado"),     # orden
    (False, ["registrado"], [], "vive_fuera"),
    (False, [" Dedicacion "], [], "vive_fuera"),
    (False, ["encolado"], [], "vive_fuera"),
    (False, ["ENCOLADO "], [], "vive_fuera"),
    (False, ["registrado"], ["PT26/00375"], "vive_fuera"),  # orden
    (False, [None], ["PT26/00376"], "protegido"),
    (False, [None], ["PT26/00374"], None),
])
def test_f061_motivo_exclusion_limpieza(aprobado, estados, partes,
                                        esperado) -> None:
    assert motivo_exclusion_limpieza(
        aprobado=aprobado, estados=estados, partes_sigrid=partes) == esperado


@pytest.mark.parametrize("filas,manual,leidos,esperado", [
    (3, False, 0, "todas_en_papelera"),
    (1, True, 5, "todas_en_papelera"),
    (0, True, 0, "sin_filas_manual"),
    (0, True, 4, "sin_filas_manual"),
    (0, False, 2, "sin_filas_leidos"),
    (0, False, 0, "sin_filas_nada_leido"),
])
def test_f061_r15_categoria_vacio(filas, manual, leidos, esperado) -> None:
    assert categoria_vacio(filas=filas, manual=manual,
                           empleados_leidos=leidos) == esperado


@pytest.mark.parametrize("raw,esperado", [
    (json.dumps({"data": {"empleados": [{}, {}, {}]}}), 3),
    (json.dumps({"data": {"empleados": []}}), 0),
    (json.dumps({"data": {"empleados": "no es lista"}}), 0),
    (json.dumps({"data": None}), 0),
    (json.dumps({"otra": 1}), 0),
    (json.dumps([1, 2]), 0),
    ("{no es json", 0),
    ("", 0),
    (None, 0),
])
def test_f061_empleados_leidos(raw, esperado) -> None:
    assert empleados_leidos(raw) == esperado


# ============================ R14–R18 ================================= #
# El script `limpiar_partes_vacios.py` (raíz de sv4) y los métodos del
# repositorio que usa. SQLite en memoria: el script recibe la fábrica de
# sesiones por parámetro (en producción la monta él, sin SessionFactory).

NOMBRE, DNI = "Pepe Perez", "12345678Z"     # los de `sembrar_parte`
CANDIDATOS = {"d-leidos", "d-nada", "d-manual", "d-papelera"}


def _marcar(fabrica, document_id: str, **campos) -> None:
    with fabrica.create_session() as s:
        doc = s.get(ParteDocumentOrm, document_id)
        for k, v in campos.items():
            setattr(doc, k, v)
        s.commit()


def _escenario() -> FabricaSesionSqlite:
    f = FabricaSesionSqlite()
    sembrar_parte(f, [], document_id="d-leidos")
    _marcar(f, "d-leidos", raw_extraction_json=json.dumps(
        {"data": {"empleados": [{"nombre": NOMBRE, "dni": DNI}]}}),
        encargado_nombre="Encargado Secreto")
    sembrar_parte(f, [], document_id="d-nada")
    sembrar_parte(f, [], document_id="d-manual")
    _marcar(f, "d-manual", source_mime_type="manual")
    sembrar_parte(f, [{"borrada": True}], document_id="d-papelera")
    sembrar_parte(f, [], document_id="d-aprobado", aprobado=True)
    sembrar_parte(f, [{"borrada": True, "estado": "registrado"}],
                  document_id="d-fuera")
    (rid,) = sembrar_parte(f, [{"borrada": True}], document_id="d-protegido")
    with f.create_session() as s:
        s.get(ParteRegistroOrm, rid).sigrid_parte_cod = "PT26/00375"
        s.commit()
    sembrar_parte(f, [{}], document_id="d-vivo")
    sembrar_parte(f, [], document_id="d-inactivo")
    _marcar(f, "d-inactivo", is_active=False)
    return f


def _estado(fabrica) -> dict:
    with fabrica.create_session() as s:
        docs = {d.id: (d.is_active, d.deleted_at_utc, d.deleted_by)
                for d in s.execute(select(ParteDocumentOrm)).scalars()}
        filas = len(s.execute(select(ParteRegistroOrm.id)).all())
    return {"docs": docs, "filas": filas}


def _main(fabrica, tmp_path, *argv):
    return script.main(list(argv), fabrica=fabrica, carpeta=tmp_path)


def test_f061_r14_r15_r16_informe() -> None:
    filas = {f["document_id"]: f
             for f in script.informe(ParteReviewRepository(_escenario()))}
    assert set(filas) == CANDIDATOS | {"d-aprobado", "d-fuera",
                                       "d-protegido"}
    esperado = {
        "d-leidos": ("sin_filas_leidos", "borrar", ""),
        "d-nada": ("sin_filas_nada_leido", "borrar", ""),
        "d-manual": ("sin_filas_manual", "borrar", ""),
        "d-papelera": ("todas_en_papelera", "retirar", ""),
        "d-aprobado": ("sin_filas_nada_leido", "borrar", "aprobado"),
        "d-fuera": ("todas_en_papelera", "retirar", "vive_fuera"),
        "d-protegido": ("todas_en_papelera", "retirar", "protegido"),
    }
    for did, (cat, accion, motivo) in esperado.items():
        f = filas[did]
        assert (f["categoria"], f["accion"], f["motivo_exclusion"]) == (
            cat, accion, motivo), did
        assert f["fecha"] == "2026-03-02" and f["obra_codigo"] == "0100"
        assert f["created_at_utc"]


def test_f061_r14_sin_argumentos_solo_lee_y_escribe_md_y_csv(
        tmp_path) -> None:
    fabrica = _escenario()
    antes = _estado(fabrica)
    escrituras: list[str] = []

    @event.listens_for(fabrica.engine, "before_cursor_execute")
    def _anota(_c, _cur, sql, *_a):
        if re.match(r"\s*(INSERT|UPDATE|DELETE)", sql, re.IGNORECASE):
            escrituras.append(sql)

    assert _main(fabrica, tmp_path) == 0
    assert escrituras == []
    assert _estado(fabrica) == antes
    (md,) = tmp_path.glob("limpieza_partes_vacios_*.md")
    (cv,) = tmp_path.glob("limpieza_partes_vacios_*.csv")
    assert re.fullmatch(r"limpieza_partes_vacios_\d{8}-\d{4}\.csv", cv.name)
    crudo = cv.read_bytes()
    assert crudo.startswith(b"\xef\xbb\xbf")                    # UTF-8 BOM
    lineas = list(csv.reader(io.StringIO(crudo.decode("utf-8-sig")),
                             delimiter=";"))
    assert lineas[0] == ["document_id", "fecha", "obra_codigo",
                         "created_at_utc", "categoria", "accion",
                         "motivo_exclusion"]
    assert len(lineas) == 1 + 7
    resumen = md.read_text(encoding="utf-8")
    texto = resumen + crudo.decode("utf-8-sig")
    for dato in (NOMBRE, DNI, "Encargado Secreto"):
        assert dato not in texto
    assert "Candidatos no excluidos: **4**" in resumen


def test_f061_r14_lectura_en_transaccion_read_only() -> None:
    hechas: list[str] = []
    pg = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"),
                         exec_driver_sql=hechas.append)
    script.solo_lectura(pg)
    assert hechas == ["SET TRANSACTION READ ONLY"]
    otra = SimpleNamespace(dialect=SimpleNamespace(name="sqlite"),
                           exec_driver_sql=hechas.append)
    script.solo_lectura(otra)
    assert hechas == ["SET TRANSACTION READ ONLY"]


def test_f061_r17_esperados_distinto_aborta_sin_escribir(tmp_path) -> None:
    fabrica = _escenario()
    antes = _estado(fabrica)
    assert _main(fabrica, tmp_path, "--ejecutar", "--esperados", "3") == 2
    assert _estado(fabrica) == antes


def test_f061_r17_ejecutar_sin_esperados_es_error_de_uso(tmp_path) -> None:
    with pytest.raises(SystemExit) as salida:
        _main(_escenario(), tmp_path, "--ejecutar")
    assert salida.value.code == 2


def test_f061_r17_ejecutar_aplica_la_regla(tmp_path) -> None:
    fabrica = _escenario()
    antes = _estado(fabrica)
    borrados_reg: list[str] = []

    @event.listens_for(fabrica.engine, "before_cursor_execute")
    def _anota(_c, _cur, sql, *_a):
        if re.match(r"\s*DELETE\s+FROM\s+parte_registros", sql, re.IGNORECASE):
            borrados_reg.append(sql)

    assert _main(fabrica, tmp_path, "--ejecutar", "--esperados", "4") == 0
    despues = _estado(fabrica)
    for did in ("d-leidos", "d-nada", "d-manual"):
        assert did not in despues["docs"], did
    assert despues["docs"]["d-papelera"] == (
        False, None, "sin-lineas · F-061-limpieza")
    for did in ("d-aprobado", "d-fuera", "d-protegido", "d-vivo",
                "d-inactivo"):
        assert despues["docs"][did] == antes["docs"][did], did
    assert despues["filas"] == antes["filas"]
    assert borrados_reg == []


def test_f061_r17_limpiar_vacios_recomprueba_bajo_bloqueo() -> None:
    fabrica = _escenario()
    repo = ParteReviewRepository(fabrica)
    res = repo.limpiar_vacios(
        ["d-vivo", "d-aprobado", "d-fuera", "d-protegido", "d-inactivo",
         "no-existe", "d-nada", "d-papelera"], by="F-061-limpieza")
    assert sorted(res["borrados"]) == ["d-nada"]
    assert sorted(res["retirados"]) == ["d-papelera"]
    assert sorted(res["saltados"]) == sorted(
        ["d-vivo", "d-aprobado", "d-fuera", "d-protegido", "d-inactivo",
         "no-existe"])
    assert _estado(fabrica)["docs"]["d-vivo"] == (True, None, None)


def test_f061_r18_sin_session_factory_ni_secretos() -> None:
    fuente = Path(script.__file__).read_text(encoding="utf-8")
    assert fuente.startswith("# limpiar_partes_vacios.py")
    assert not re.search(r"^\s*(from|import)\s.*SessionFactory", fuente,
                         re.MULTILINE)
    assert "SessionFactory(" not in fuente
    assert "settings.database_url" in fuente
    assert not re.search(r"password\s*=|postgresql\+psycopg://", fuente,
                         re.IGNORECASE)
    assert "PT26/00373" not in fuente      # la lista vive en parte_vacio


# ===================== Mutación (supervivientes) ====================== #

def test_f061_r18_fabrica_de_sesiones_del_script_funciona() -> None:
    """La fábrica propia del script (sin SessionFactory) abre sesiones de
    verdad; en lectura registra el `SET TRANSACTION READ ONLY` en `begin`.
    Mata `future=False` en `create_engine` y en `sessionmaker`, que en
    SQLAlchemy 2 son un `ArgumentError`."""
    from infrastructure.database.orm_models import Base
    for lectura in (True, False):
        fabrica = script.FabricaSesiones("sqlite://", lectura=lectura)
        assert event.contains(fabrica.engine, "begin",
                              script.solo_lectura) is lectura
        Base.metadata.create_all(fabrica.engine)
        repo = ParteReviewRepository(fabrica)
        assert repo.partes_vacios_activos() == []


def test_f061_r14_markdown_cuenta_categorias_y_acciones_de_candidatos(
        tmp_path) -> None:
    """Las tablas por categoría y por acción cuentan solo los candidatos
    no excluidos; la de exclusión, solo los excluidos."""
    assert _main(_escenario(), tmp_path) == 0
    (md,) = tmp_path.glob("limpieza_partes_vacios_*.md")
    texto = md.read_text(encoding="utf-8")

    def tabla(cabecera: str) -> list[str]:
        bloque = texto.split(cabecera, 1)[1].split("\n\n", 1)[0]
        return [ln for ln in bloque.splitlines() if ln.startswith("| `")]

    assert tabla("| Categoría (candidatos) | Partes |") == [
        "| `sin_filas_leidos` | 1 |", "| `sin_filas_manual` | 1 |",
        "| `sin_filas_nada_leido` | 1 |", "| `todas_en_papelera` | 1 |"]
    assert tabla("| Acción prevista (candidatos) | Partes |") == [
        "| `borrar` | 3 |", "| `retirar` | 1 |"]
    assert tabla("| Motivo de exclusión | Partes |") == [
        "| `aprobado` | 1 |", "| `protegido` | 1 |", "| `vive_fuera` | 1 |"]
