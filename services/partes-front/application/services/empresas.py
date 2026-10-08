# application/services/empresas.py
"""F-033 · empresa de una fila del listado de obras del portal.

Reglas puras, sin dependencias: el repositorio les pasa lo que ya ha
cargado de la BBDD `partes` y aqui solo se decide que se muestra.

- La empresa de la fila es la de sus partes (`parte_documents.empresa`,
  F-023); si todos son NULL (partes anteriores a F-023), la de los
  recursos de sus lineas, deducida de otros partes con empresa donde
  aparece ese recurso (un recurso de Sigrid es de una sola empresa).
- El nombre corto sale de `NOMBRES_EMPRESA`; un numero que no este ahi se
  muestra «Empresa N» hasta que se anada (cambio de una linea).
"""
from __future__ import annotations

#: Nombre corto de cada empresa de Sigrid que el portal sabe pintar.
NOMBRES_EMPRESA: dict[int, str] = {1: "Ruesma", 28: "Porsan"}

#: Lo que se pinta cuando la fila no tiene empresa conocida.
SIN_EMPRESA = "—"


def nombre_empresa(numero: int) -> str:
    """Nombre corto de la empresa `numero`, o «Empresa N» si no se conoce."""
    return NOMBRES_EMPRESA.get(numero, f"Empresa {numero}")


def nombre_empresa_o_vacio(numero: int | None) -> str:
    """F-039 · `empresa_nombre` de un item del portal: el nombre corto de
    `numero` o `""` si el item no trae empresa (lo pinta `empresaSufijo`)."""
    if numero is None:
        return ""
    return nombre_empresa(numero)


def texto_empresas(numeros: list[int]) -> str:
    """Nombres unidos por « / » en el orden recibido; «—» si no hay."""
    if not numeros:
        return SIN_EMPRESA
    return " / ".join(nombre_empresa(n) for n in numeros)


def empresas_de_fila(
    empresas_partes: set[int | None],
    recursos: set[int | None],
    empresa_por_recurso: dict[int, set[int]],
) -> list[int]:
    """Empresas de una fila, ordenadas y sin repetir.

    Mandan las de sus partes; solo si ninguno la tiene se usa el respaldo
    por recurso (union de las empresas de sus recursos no nulos).
    """
    propias = {e for e in empresas_partes if e is not None}
    if propias:
        return sorted(propias)
    deducidas: set[int] = set()
    for recurso in recursos:
        if recurso is not None:
            deducidas |= empresa_por_recurso.get(recurso, set())
    return sorted(deducidas)
