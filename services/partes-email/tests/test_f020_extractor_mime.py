# tests/test_f020_extractor_mime.py
"""F-020 · Modelos de dominio del correo adjunto y extractor MIME (R7-R13, R17)."""
from __future__ import annotations

from domain.models.email_models import CorreoEmbebido


# --------------------------------------------------------------------- #
# R17 · forma de cada elemento de `embedded_in` (design §5).
# --------------------------------------------------------------------- #
def test_f020_r17_to_context_devuelve_exactamente_las_cinco_claves():
    correo = CorreoEmbebido(level=2, attachment_name="interior.eml",
                            subject="Attached Image",
                            sender="escaner@example.com",
                            date="Wed, 30 Sep 2026 08:16:00 +0200")
    assert correo.to_context() == {
        "level": 2,
        "attachment_name": "interior.eml",
        "subject": "Attached Image",
        "sender": "escaner@example.com",
        "date": "Wed, 30 Sep 2026 08:16:00 +0200",
    }


def test_f020_r17_to_context_conserva_los_nulos():
    correo = CorreoEmbebido(level=1, attachment_name=None, subject=None,
                            sender=None, date=None)
    assert correo.to_context() == {"level": 1, "attachment_name": None,
                                   "subject": None, "sender": None,
                                   "date": None}
