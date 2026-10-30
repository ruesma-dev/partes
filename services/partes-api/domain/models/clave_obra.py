# domain/models/clave_obra.py
"""F-058 / F-063 · La clave con la que se compara un código de obra.

Regla de dominio pura, sin dependencias de otras capas: la usan application
(``ComprobadorObra``, la relectura de la cabecera) e infrastructure (el
filtro exacto de los candidatos de ``existe_obra``, F-063). Una sola función
a los dos lados: la clave del código leído y la de cada candidato se
calculan igual (F-063 R9). Movidas tal cual desde
``application/services/relectura_cabecera.py``, que las sigue exponiendo.
"""
from __future__ import annotations

import unicodedata


def es_vacio(valor: object) -> bool:
    """``None`` o una cadena con solo espacios (R5)."""
    return valor is None or (isinstance(valor, str) and not valor.strip())


def clave_obra(codigo: object) -> str:
    """Clave con la que se compara un código de obra.

    Sin acentos, en mayúsculas y sin espacios ni guiones; si queda solo de
    dígitos, sin ceros a la izquierda (``"00672"`` → ``"672"``, ``"000"`` →
    ``"0"``). ``""`` si el código es vacío.
    """
    if es_vacio(codigo):
        return ""
    texto = unicodedata.normalize("NFKD", str(codigo))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = "".join(texto.upper().split()).replace("-", "")
    if texto.isdigit():
        return texto.lstrip("0") or "0"
    return texto
