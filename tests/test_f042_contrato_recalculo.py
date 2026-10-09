# tests/test_f042_contrato_recalculo.py
"""Contrato del mensaje «recalcular» de `q-persistencia` (F-042, R22).

Desde F-042 la cola `q-persistencia` tiene DOS productores:

  - sv2 (`services/partes-api/main_worker.py`): un parte nuevo que ingerir,
    `{"document_id", "filename", "mime_type", "context"}`, SIN `tipo`;
  - sv4 (`infrastructure/persistencia/recalculo_publisher.py`): se ha
    guardado o deshecho la fecha de un parte, `{"tipo": "recalcular", ...}`.

y un consumidor, sv3, que los distingue por `tipo`
(`interface_adapters/workers/mensajes.py::clasificar`). No hay libreria
compartida (`docs/ARCHITECTURE.md`): el formato vive en un modulo de cada
lado y este test los ata. Es contrato de transporte, no logica duplicada,
asi que no entra en la lista cerrada de `CLAUDE.md` (DA6).

Los dos modulos se cargan POR RUTA con nombres unicos (los paquetes de cada
servicio se llaman igual: `infrastructure`, `interface_adapters`), y por
eso los dos tienen que importar solo la biblioteca estandar.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

#: Raiz del repositorio: este fichero es `<raiz>/tests/test_f042_...py`.
RAIZ = Path(__file__).resolve().parents[1]

RUTA_SV4 = (RAIZ / "services/partes-front/infrastructure/persistencia/"
            "recalculo_publisher.py")
RUTA_SV3 = (RAIZ / "services/partes-persistencia/interface_adapters/workers/"
            "mensajes.py")
RUTA_SV2 = RAIZ / "services/partes-api/main_worker.py"

AHORA = datetime(2026, 10, 9, 10, 30, tzinfo=timezone.utc)


def _cargar(ruta: Path, nombre: str):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    assert spec is not None and spec.loader is not None, ruta
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def sv4():
    return _cargar(RUTA_SV4, "f042_contrato_sv4_recalculo_publisher")


@pytest.fixture(scope="module")
def sv3():
    return _cargar(RUTA_SV3, "f042_contrato_sv3_mensajes")


def _por_la_cola(mensaje: dict) -> object:
    """Lo que hace Storage Queue: JSON de ida y de vuelta."""
    return json.loads(json.dumps(mensaje, ensure_ascii=False))


# ================== lo que construye sv4 es un recalculo ================ #

def test_f042_r22_el_tipo_es_el_mismo_en_los_dos_lados(sv4, sv3) -> None:
    assert sv4.TIPO_RECALCULAR == sv3.TIPO_RECALCULAR == "recalcular"


@pytest.mark.parametrize("motivo", ["MOTIVO_CAMBIO_FECHA",
                                    "MOTIVO_DESHACER_FECHA"])
@pytest.mark.parametrize("por", ["revisora@ejemplo.es", None])
def test_f042_r22_sv3_clasifica_como_recalculo_lo_de_sv4(sv4, sv3, motivo,
                                                         por) -> None:
    mensaje = sv4.mensaje_recalculo(
        document_id="doc-1", motivo=getattr(sv4, motivo),
        solicitado_por=por, ahora=AHORA)
    assert sv3.clasificar(_por_la_cola(mensaje)) == sv3.CLASE_RECALCULO
    assert len(json.dumps(mensaje).encode("utf-8")) < 1024   # design §2


@pytest.mark.parametrize("motivo", ["MOTIVO_CAMBIO_FECHA",
                                    "MOTIVO_DESHACER_FECHA"])
def test_f042_r22_lo_que_publica_el_publisher_tambien(sv4, sv3,
                                                      motivo) -> None:
    """El camino completo de sv4: el payload que llega a `enviar`."""
    enviados: list[tuple[str, dict]] = []

    class Cola:
        def enviar(self, cola: str, payload: dict) -> None:
            enviados.append((cola, payload))

    sv4.RecalculoPublisher(cola=Cola(), cola_persistencia="q-persistencia",
                           reloj=lambda: AHORA).pedir(
        document_id="doc-1", motivo=getattr(sv4, motivo),
        solicitado_por=None)
    (cola, payload), = enviados
    assert cola == "q-persistencia"
    assert sv3.clasificar(_por_la_cola(payload)) == sv3.CLASE_RECALCULO


# ================== lo de sv2 sigue siendo una ingesta ================== #

def test_f042_r22_el_mensaje_con_la_forma_de_sv2_es_ingesta(sv3) -> None:
    mensaje = {"document_id": "doc-1", "filename": "parte.pdf",
               "mime_type": "application/pdf", "context": {"origen": "x"}}
    assert sv3.clasificar(_por_la_cola(mensaje)) == sv3.CLASE_INGESTA


def _dicts_enviados_por_sv2() -> list[ast.Dict]:
    """Los dict literales de `cola.enviar(COLA_SALIDA, {...})` de sv2."""
    arbol = ast.parse(RUTA_SV2.read_text(encoding="utf-8"))
    return [
        nodo.args[1] for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Attribute)
        and nodo.func.attr == "enviar"
        and len(nodo.args) == 2
        and isinstance(nodo.args[0], ast.Name)
        and nodo.args[0].id == "COLA_SALIDA"
        and isinstance(nodo.args[1], ast.Dict)
    ]


def test_f042_r22_el_productor_de_sv2_no_emite_tipo(sv3) -> None:
    dicts = _dicts_enviados_por_sv2()
    assert len(dicts) == 1, "sv2 debe publicar en q-persistencia un dict"
    claves = [k.value for k in dicts[0].keys
              if isinstance(k, ast.Constant)]
    # Todas las claves son literales (nada de `**otro` que cuele un tipo).
    assert len(claves) == len(dicts[0].keys)
    assert "tipo" not in claves
    assert set(claves) == {"document_id", "filename", "mime_type", "context"}
    assert sv3.clasificar({c: "x" for c in claves}) == sv3.CLASE_INGESTA


# ===================== solo la biblioteca estandar ====================== #

def _imports(ruta: Path) -> set[str]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    raices: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            raices.update(a.name.split(".")[0] for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            assert nodo.level == 0, f"{ruta}: import relativo"
            raices.add((nodo.module or "").split(".")[0])
    return raices


@pytest.mark.parametrize("ruta", [RUTA_SV4, RUTA_SV3],
                         ids=["sv4-publisher", "sv3-mensajes"])
def test_f042_r22_los_modulos_del_contrato_solo_usan_stdlib(ruta) -> None:
    raices = _imports(ruta)
    assert raices, f"{ruta}: no se ha leido ningun import"
    ajenos = {r for r in raices
              if r != "__future__" and r not in sys.stdlib_module_names}
    assert ajenos == set(), f"{ruta} importa fuera de la stdlib: {ajenos}"
