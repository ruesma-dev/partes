# tests/test_f024_comprobar_y_estado.py
"""F-024 · comprobacion en Sigrid desde el portal y sondeo del encolado.

R17-R21 (antimartilleo, servicio y endpoint de comprobacion), R26-R28 y
R30. Sin red ni PostgreSQL ni `sleep`: reloj inyectado, SQLite en memoria
y un doble del cliente de sv5.
"""
from __future__ import annotations

import threading

import pytest
from application.services.comprobacion_sigrid import RegistroComprobaciones


class Reloj:
    """Reloj monotono controlado por el test."""

    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


# ===================================================================== #
# T8 · RegistroComprobaciones (R19)
# ===================================================================== #

def test_f024_r19_recientes_dentro_del_ttl_no_repite() -> None:
    reloj = Reloj()
    reg = RegistroComprobaciones(ttl_s=120, reloj=reloj)
    assert reg.reservar([3, 1, 2], forzar=False) == [3, 1, 2]
    reloj.t += 119.9
    assert reg.reservar([1, 2, 4], forzar=False) == [4]


def test_f024_r19_recientes_pasado_el_ttl_vuelve_a_comprobar() -> None:
    reloj = Reloj()
    reg = RegistroComprobaciones(ttl_s=120, reloj=reloj)
    reg.reservar([1], forzar=False)
    reloj.t += 120
    assert reg.reservar([1], forzar=False) == [1]


def test_f024_r19_recientes_forzar_lo_salta_y_vuelve_a_sellar() -> None:
    reloj = Reloj()
    reg = RegistroComprobaciones(ttl_s=120, reloj=reloj)
    reg.reservar([1, 2], forzar=False)
    reloj.t += 100
    assert reg.reservar([1, 2], forzar=True) == [1, 2]
    reloj.t += 100      # 200 s desde el primer sello, 100 desde el forzado
    assert reg.reservar([1, 2], forzar=False) == []


def test_f024_r19_recientes_sella_al_reservar_aunque_el_lote_falle() -> None:
    """Un id en curso, o cuyo lote fallo, no se reenvia en cada recarga."""
    reloj = Reloj()
    reg = RegistroComprobaciones(ttl_s=120, reloj=reloj)
    reg.reservar([1, 2], forzar=False)
    # ...el lote falla (nadie avisa al registro)...
    assert reg.reservar([1, 2], forzar=False) == []


def test_f024_r19_recientes_deduplica_la_entrada() -> None:
    reg = RegistroComprobaciones(ttl_s=120, reloj=Reloj())
    assert reg.reservar([5, 5, 6, 5], forzar=False) == [5, 6]
    assert reg.reservar([7, 7], forzar=True) == [7]


def test_f024_r19_recientes_purga_las_caducadas() -> None:
    reloj = Reloj()
    reg = RegistroComprobaciones(ttl_s=120, reloj=reloj)
    reg.reservar(list(range(100)), forzar=False)
    reloj.t += 121
    reg.reservar([500], forzar=False)
    assert reg.vigentes() == 1


def test_f024_r19_recientes_ttl_cero_no_retiene_nada() -> None:
    reg = RegistroComprobaciones(ttl_s=0, reloj=Reloj())
    assert reg.reservar([1], forzar=False) == [1]
    assert reg.reservar([1], forzar=False) == [1]


def test_f024_r19_recientes_seguro_con_dos_hilos() -> None:
    """Dos vistas de la misma obra a la vez: cada id va a sv5 una vez."""
    reg = RegistroComprobaciones(ttl_s=120, reloj=Reloj())
    ids = list(range(2000))
    barrera = threading.Barrier(2)
    resultados: list[list[int]] = []

    def _reservar() -> None:
        barrera.wait()
        resultados.append(reg.reservar(ids, forzar=False))

    hilos = [threading.Thread(target=_reservar) for _ in range(2)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(timeout=10)
    assert len(resultados) == 2
    assert sorted(resultados[0] + resultados[1]) == ids


def test_f024_r19_recientes_usa_reloj_monotono_por_defecto() -> None:
    import time
    reg = RegistroComprobaciones(ttl_s=120)
    assert reg._reloj is time.monotonic          # noqa: SLF001
