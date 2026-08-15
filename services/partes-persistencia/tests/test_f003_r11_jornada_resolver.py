# tests/test_f003_r11_jornada_resolver.py
"""R11 · sv3 saca la jornada teorica de un resolutor unico e inyectable.

El computo de extras decidia el `candef` efectivo con la comparacion
escrita a mano dentro de `_reclasificar_extras_jornada`. Estos tests
fijan la regla ANTES de que Sesame pueda cambiarla: mientras sesame-api
no exponga la jornada del contrato en horas (peticion P1 del design), el
numero tiene que salir exactamente igual que hoy.
"""
from __future__ import annotations

import pytest
from application.services.jornada_resolver import (
    candef_valido,
    jornada_efectiva,
)


@pytest.mark.parametrize(
    "candef, esperado",
    [
        (None, 8.0),        # Sigrid no informa el CanDefecto
        (0.0, 8.0),         # 0 = no informado (no "trabaja cero horas")
        (1.0, 8.0),
        (2.0, 8.0),         # exactamente el minimo NO es valido
        (2.5, 2.5),
        (7.0, 7.0),
        (8.0, 8.0),
        (10.0, 10.0),
    ],
)
def test_f003_r11_regla_candef(candef, esperado) -> None:
    assert jornada_efectiva(candef, minimo=2.0, por_defecto=8.0) == esperado


def test_f003_r11_umbral_estricto() -> None:
    assert jornada_efectiva(2.0, minimo=2.0, por_defecto=8.0) == 8.0
    assert jornada_efectiva(2.01, minimo=2.0, por_defecto=8.0) == 2.01


def test_f003_r11_valores_no_numericos_son_no_informados() -> None:
    assert jornada_efectiva("", minimo=2.0, por_defecto=8.0) == 8.0
    assert jornada_efectiva("ocho", minimo=2.0, por_defecto=8.0) == 8.0
    assert jornada_efectiva("7,5", minimo=2.0, por_defecto=8.0) == 8.0


def test_f003_r11_parametros_no_cableados() -> None:
    assert jornada_efectiva(None, minimo=1.0, por_defecto=6.0) == 6.0
    assert jornada_efectiva(5.0, minimo=6.0, por_defecto=6.0) == 6.0


def test_f003_r11_candef_valido_es_la_misma_regla() -> None:
    """`candef_valido` y `jornada_efectiva` no pueden discrepar."""
    for c in (None, "", 0.0, 2.0, 2.5, 8.0, "x"):
        cae_al_defecto = (
            jornada_efectiva(c, minimo=2.0, por_defecto=999.0) == 999.0
        )
        assert cae_al_defecto is not candef_valido(c, minimo=2.0)


def test_f003_r11_gemelo_del_de_sv4() -> None:
    """sv3 y sv4 comparten regla: si divergen, los avisos del portal
    dejarian de coincidir con lo que sv3 calcula. La copia es deliberada
    (adaptadores por servicio), pero el comportamiento debe ser el mismo."""
    import importlib.util
    from pathlib import Path

    ruta = (Path(__file__).resolve().parents[2] / "partes-front"
            / "application" / "services" / "jornada_resolver.py")
    spec = importlib.util.spec_from_file_location("jornada_sv4", ruta)
    assert spec is not None and spec.loader is not None
    sv4 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sv4)

    for c in (None, "", 0.0, 1.0, 2.0, 2.5, 7.5, 8.0, 12.0, "x", "7.5"):
        assert (jornada_efectiva(c, minimo=2.0, por_defecto=8.0)
                == sv4.jornada_efectiva(c, minimo=2.0, por_defecto=8.0))
