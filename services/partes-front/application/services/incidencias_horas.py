# application/services/incidencias_horas.py
"""F-025 · incidencia y horas el mismo dia (logica pura, sin BBDD).

Sigrid no clasifica sus incidencias: la clase de cada letra de la leyenda
(`dia_completo` o `parcial`) vive en la tabla versionada
`config/incidencias.yaml`, que `build_app` lee al arrancar y pasa por
parametro al repositorio. Aqui:

  - `parsear_tabla` (R1, R2): valida la tabla; ante cualquier problema
    lanza `ValueError` nombrandolo (sin valores por defecto en silencio).
  - `TablaIncidencias.clase_de` (R3): la clase de una linea de incidencia.
  - `detectar` (R4-R8): por dia-trabajador, `bloqueo` si hay una
    incidencia de dia completo y horas; `aviso` si hay una parcial y horas
    extra positivas.
  - `resumen_por_dia`: el peor nivel de cada dia, para el calendario.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

CLASE_DIA_COMPLETO = "dia_completo"
CLASE_PARCIAL = "parcial"
CLASES = (CLASE_DIA_COMPLETO, CLASE_PARCIAL)
NIVEL_BLOQUEO = "bloqueo"
NIVEL_AVISO = "aviso"

#: Las siete letras de la leyenda del parte (sv2 `parte_models.py`).
LETRAS_LEYENDA = ("V", "B", "AT", "FJ", "F", "H", "M")

#: Prefijo de los codigos de incidencia de `auxhor` en Sigrid.
PREFIJO_SIGRID = "CI"


def normalizar_codigo(valor: object) -> str:
    """Sin espacios (tampoco en medio) y en mayusculas; '' si no hay."""
    if valor is None:
        return ""
    return "".join(str(valor).split()).upper()


@dataclass(frozen=True)
class ClaseIncidencia:
    """Una letra de la leyenda con su codigo de Sigrid y su clase."""

    letra: str
    sigrid: str
    nombre: str
    clase: str


@dataclass(frozen=True)
class TablaIncidencias:
    """La tabla ya validada, indexada por letra y por codigo de Sigrid."""

    por_letra: dict[str, ClaseIncidencia]
    por_sigrid: dict[str, ClaseIncidencia]

    def clase_de(self, incidencia_codigo: str | None,
                 hora_codigo: str | None) -> ClaseIncidencia | None:
        """R3: por la letra; si no esta, por el codigo de hora; si
        tampoco (p. ej. `CIZ`), None: la linea no participa."""
        por_letra = self.por_letra.get(normalizar_codigo(incidencia_codigo))
        if por_letra is not None:
            return por_letra
        return self.por_sigrid.get(normalizar_codigo(hora_codigo))


def _entrada(letra: str, valor: object) -> ClaseIncidencia:
    if not isinstance(valor, dict):
        raise ValueError(
            f"incidencias: la letra {letra} tiene que ser un mapa con "
            "sigrid, nombre y clase")
    sigrid = normalizar_codigo(valor.get("sigrid"))
    if not sigrid.startswith(PREFIJO_SIGRID):
        raise ValueError(
            f"incidencias: la letra {letra} tiene el codigo de Sigrid "
            f"{valor.get('sigrid')!r}, que no empieza por {PREFIJO_SIGRID}")
    nombre = str(valor.get("nombre") or "").strip()
    if not nombre:
        raise ValueError(f"incidencias: la letra {letra} no tiene nombre")
    clase = str(valor.get("clase") or "").strip().lower()
    if clase not in CLASES:
        raise ValueError(
            f"incidencias: la letra {letra} tiene la clase "
            f"{valor.get('clase')!r}, desconocida (validas: "
            f"{', '.join(CLASES)})")
    return ClaseIncidencia(letra=letra, sigrid=sigrid, nombre=nombre,
                           clase=clase)


def parsear_tabla(datos: object) -> TablaIncidencias:
    """R1, R2: la tabla del YAML ya cargado, o `ValueError`."""
    if not isinstance(datos, dict):
        raise ValueError(
            "incidencias: la tabla tiene que ser un mapa LETRA -> "
            "{sigrid, nombre, clase}")
    por_letra: dict[str, ClaseIncidencia] = {}
    for clave, valor in datos.items():
        letra = normalizar_codigo(clave)
        por_letra[letra] = _entrada(letra, valor)
    faltan = [letra for letra in LETRAS_LEYENDA if letra not in por_letra]
    if faltan:
        raise ValueError(
            f"incidencias: faltan letras de la leyenda: {', '.join(faltan)}")
    por_sigrid: dict[str, ClaseIncidencia] = {}
    for clase in por_letra.values():
        if clase.sigrid in por_sigrid:
            raise ValueError(
                f"incidencias: el codigo {clase.sigrid} esta en "
                f"{por_sigrid[clase.sigrid].letra} y en {clase.letra}")
        por_sigrid[clase.sigrid] = clase
    return TablaIncidencias(por_letra=por_letra, por_sigrid=por_sigrid)
