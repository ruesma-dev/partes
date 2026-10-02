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



#: Por debajo de esto, una cantidad de horas es cero.
_EPSILON = 1e-9


@dataclass(frozen=True)
class LineaDia:
    """Lo que la deteccion necesita de una linea activa del portal.

    `persona` la calcula quien llama (R4: DNI normalizado o, sin DNI, la
    clave de trabajador del portal); `es_extra` es el criterio de
    `_is_extra` del repositorio.
    """

    registro_id: int
    persona: str
    fecha_int: int | None
    es_incidencia: bool
    incidencia_codigo: str | None
    hora_codigo: str | None
    es_extra: bool
    horas: float | None


@dataclass(frozen=True)
class Incompatibilidad:
    """El nivel (`bloqueo` o `aviso`) de un dia-trabajador y su motivo."""

    nivel: str
    motivo: str


def _horas_texto(valor: float) -> str:
    """8.0 -> '8', 8.5 -> '8.5' (como las celdas de la matriz)."""
    redondeado = round(valor, 2)
    if float(redondeado).is_integer():
        return str(int(redondeado))
    return "%g" % redondeado


def _nombrar(clases: dict[str, ClaseIncidencia]) -> str:
    """'Nombre (L)' de cada incidencia, en orden de letra."""
    return " y ".join(f"{clases[letra].nombre} ({letra})"
                      for letra in sorted(clases))


def _evaluar_dia(grupo: list[LineaDia],
                 tabla: TablaIncidencias) -> Incompatibilidad | None:
    """R5-R8 sobre las lineas de UN dia-trabajador."""
    completas: dict[str, ClaseIncidencia] = {}
    parciales: dict[str, ClaseIncidencia] = {}
    horas = 0.0
    hay_horas = False
    extra_pos = 0.0
    for linea in grupo:
        if linea.es_incidencia:
            clase = tabla.clase_de(linea.incidencia_codigo, linea.hora_codigo)
            if clase is None:
                continue
            destino = (completas if clase.clase == CLASE_DIA_COMPLETO
                       else parciales)
            destino[clase.letra] = clase
            continue
        valor = float(linea.horas or 0.0)
        if abs(valor) > _EPSILON:
            hay_horas = True
            horas += valor
            if linea.es_extra and valor > _EPSILON:
                extra_pos += valor
    if completas and hay_horas:
        verbo = "es" if len(completas) == 1 else "son"
        return Incompatibilidad(NIVEL_BLOQUEO, (
            f"{_nombrar(completas)} {verbo} de día completo y ese día hay "
            f"{_horas_texto(horas)} h de trabajo: deja solo una de las dos"))
    if parciales and extra_pos > 0.0:
        return Incompatibilidad(NIVEL_AVISO, (
            f"{_nombrar(parciales)} y {_horas_texto(extra_pos)} h extra el "
            "mismo día: comprueba que sean correctas"))
    return None


def detectar(lineas: Iterable[LineaDia],
             tabla: TablaIncidencias) -> dict[int, Incompatibilidad]:
    """R4-R8: el nivel de cada linea, por `registro_id`.

    Agrupa por (persona, fecha); las lineas sin fecha no entran. Una linea
    que no aparece no esta en conflicto. Todas las lineas de un dia en
    conflicto llevan el mismo nivel y el mismo motivo.
    """
    por_dia: dict[tuple[str, int], list[LineaDia]] = {}
    for linea in lineas:
        if not linea.fecha_int:
            continue
        por_dia.setdefault((linea.persona, int(linea.fecha_int)),
                           []).append(linea)
    resultado: dict[int, Incompatibilidad] = {}
    for grupo in por_dia.values():
        nivel = _evaluar_dia(grupo, tabla)
        if nivel is None:
            continue
        for linea in grupo:
            resultado[linea.registro_id] = nivel
    return resultado


def resumen_por_dia(
        items: Iterable[tuple[str, Incompatibilidad]],
) -> dict[str, Incompatibilidad]:
    """El peor nivel de cada dia (gana `bloqueo`; a igualdad, el primero).
    Para el calendario de la vista de trabajador (R16)."""
    resumen: dict[str, Incompatibilidad] = {}
    for dia, incompat in items:
        previo = resumen.get(dia)
        if previo is None or (incompat.nivel == NIVEL_BLOQUEO
                              and previo.nivel != NIVEL_BLOQUEO):
            resumen[dia] = incompat
    return resumen
