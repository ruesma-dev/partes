# tests/test_f032_campana.py
"""F-032 · tests de la pasada de campaña (superviviente 1 de
`progress/mutacion_F-032.md`), verificado a mano con el mutante aplicado.

La copia de sv4 de `festivos_guardados.py` es gemela de la de sv3: solo
`None` es «sin nombre»; cualquier otro valor se guarda como texto.
"""
from __future__ import annotations

from application.services.festivos_guardados import del_ano


def test_f032_r42_un_nombre_no_textual_se_guarda_como_texto() -> None:
    assert del_ano([("2026-01-01", 0), ("2026-01-06", None)], 2026) == {
        "2026-01-01": "0", "2026-01-06": None}
