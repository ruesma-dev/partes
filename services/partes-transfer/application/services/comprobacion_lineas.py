# application/services/comprobacion_lineas.py
"""F-024 · ¿Sigue en Sigrid la linea que escribio sv5? (solo lectura).

Administracion puede borrar en Sigrid lineas que el portal da por
`registrado`. sv4 pregunta a sv5 —dueno del `synckey` y de su lectura— y
sv5 contesta con un veredicto por linea:

  - ``presente``: su `synckey` (`partes:<registro_id>`) aparece en
    `hmores`, con la MISMA lectura que la idempotencia del pipeline
    (`lineas_por_synckey`, paso 6). Asi ``borrada`` equivale a «reaprobarla
    la escribiria» (R2).
  - respaldo estricto (R3): sin `synckey`, la fila `hmores.ide` guardada
    con `synckey` vacia y el mismo recurso, fecha y (si vino) parte.
  - ``borrada``: todo lo demas (R4), con motivo propio si la cabecera
    `hmo` tampoco existe.

`clasificar` es pura; `ComprobadorLineas` hace las tres lecturas y la
llama. Nada aqui escribe ni toma el lock de escritura (R1).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterable, Optional

from domain.models.registro_models import LineaSigrid
from infrastructure.sigrid.sigrid_write_client import synckey_de

logger = logging.getLogger(__name__)

PRESENTE = "presente"
BORRADA = "borrada"

#: Diferencia de horas por debajo de la cual no se avisa (R6).
TOLERANCIA_HORAS = 0.005


@dataclass
class LineaComprobar:
    """Lo que sv4 sabe de una linea `registrado` (todo opcional salvo id)."""
    registro_id: int
    hmores_ide: Optional[int] = None
    hmoide: Optional[int] = None
    recurso_ide: Optional[int] = None
    fecha_int: Optional[int] = None
    horas: Optional[float] = None
    es_incidencia: bool = False


@dataclass
class Veredicto:
    """Respuesta por linea. Con ``presente``, las referencias son las de
    Sigrid HOY (R5); con ``borrada``, las que envio el portal."""
    registro_id: int
    estado: str
    hmores_ide: Optional[int] = None
    hmoide: Optional[int] = None
    parte_cod: Optional[str] = None
    parte_existe: bool = True
    sin_synckey: bool = False
    diferencias: list[str] = field(default_factory=list)
    motivo: Optional[str] = None


def _num(valor: float | None) -> str:
    return "sin dato" if valor is None else f"{float(valor):g}"


def _diferencias(linea: LineaComprobar, fila: LineaSigrid) -> list[str]:
    """R6: lo que Administracion cambio a mano. Solo informa.

    El recurso se compara si el portal lo trae (sin el, sv5 lo resolvio
    por DNI y no es un cambio manual). El codigo de hora NO se compara: las
    reglas pueden cambiarlo. Las horas, ni en incidencias (`can=0`) ni sin
    horas en el portal.
    """
    out: list[str] = []
    if linea.recurso_ide is not None and fila.reside != linea.recurso_ide:
        out.append(f"recurso: portal {linea.recurso_ide}, Sigrid {fila.reside}")
    if fila.fecha_int != linea.fecha_int:
        out.append(f"fecha: portal {linea.fecha_int}, Sigrid {fila.fecha_int}")
    if not linea.es_incidencia and linea.horas is not None:
        if fila.can is None or (
                abs(float(fila.can) - float(linea.horas)) > TOLERANCIA_HORAS):
            out.append(f"horas: portal {_num(linea.horas)}, "
                       f"Sigrid {_num(fila.can)}")
    return out


def _hmoide(fila: LineaSigrid) -> Optional[int]:
    return getattr(fila, "hmoide", None)


def _respaldo_valido(linea: LineaComprobar, fila: LineaSigrid | None) -> bool:
    """R3: la fila del `ide` guardado es la nuestra aunque perdiera la
    `synckey`. Con cualquier otro valor el `ide` se reutilizo."""
    if fila is None:
        return False
    if (fila.synckey or "").strip():
        return False
    if linea.recurso_ide is None or fila.reside != linea.recurso_ide:
        return False
    if fila.fecha_int != linea.fecha_int:
        return False
    return linea.hmoide is None or _hmoide(fila) == linea.hmoide


def clasificar(
    lineas: Iterable[LineaComprobar],
    por_synckey: dict[str, LineaSigrid],
    por_ide: dict[int, LineaSigrid],
    partes: dict[int, str],
) -> list[Veredicto]:
    """Un veredicto por linea, en el mismo orden (pura)."""
    out: list[Veredicto] = []
    for linea in lineas:
        fila = por_synckey.get(synckey_de(linea.registro_id))
        sin_synckey = False
        if fila is None and linea.hmores_ide is not None:
            candidata = por_ide.get(int(linea.hmores_ide))
            if _respaldo_valido(linea, candidata):
                fila, sin_synckey = candidata, True
        if fila is not None:
            hmoide = _hmoide(fila)
            out.append(Veredicto(
                registro_id=linea.registro_id, estado=PRESENTE,
                hmores_ide=fila.ide, hmoide=hmoide,
                parte_cod=partes.get(hmoide) if hmoide is not None else None,
                sin_synckey=sin_synckey,
                diferencias=_diferencias(linea, fila)))
            continue
        existe = linea.hmoide is None or linea.hmoide in partes
        cod = partes.get(linea.hmoide) if linea.hmoide is not None else None
        if existe:
            parte = cod or linea.hmoide
            motivo = (f"la linea {linea.hmores_ide or '?'}"
                      + (f" del parte {parte}" if parte else "")
                      + " ya no existe en Sigrid")
        else:
            motivo = f"el parte {linea.hmoide} ya no existe en Sigrid"
        out.append(Veredicto(
            registro_id=linea.registro_id, estado=BORRADA,
            hmores_ide=linea.hmores_ide, hmoide=linea.hmoide, parte_cod=cod,
            parte_existe=existe, motivo=motivo))
    return out


class ComprobadorLineas:
    """Las lecturas de R1-R5 sobre el cliente de Sigrid de sv5.

    Recibe el MISMO cliente que el pipeline (`main.py`), pero solo usa
    lecturas: ni `escribir` ni el lock.
    """

    def __init__(self, *, cliente) -> None:
        self._cli = cliente

    def comprobar(self, lineas: Iterable[LineaComprobar]) -> list[Veredicto]:
        unicas: dict[int, LineaComprobar] = {}
        for linea in lineas:
            unicas.setdefault(int(linea.registro_id), linea)
        todas = list(unicas.values())
        por_synckey = self._cli.lineas_por_synckey(
            [synckey_de(l.registro_id) for l in todas])
        fallos = [l for l in todas
                  if synckey_de(l.registro_id) not in por_synckey]
        ides = [l.hmores_ide for l in fallos if l.hmores_ide is not None]
        por_ide = self._cli.lineas_por_ide(ides) if ides else {}
        hmoides = {_hmoide(f) for f in por_synckey.values()}
        hmoides |= {_hmoide(f) for f in por_ide.values()}
        hmoides |= {l.hmoide for l in fallos}
        hmoides.discard(None)
        partes = self._cli.partes_por_ide(sorted(hmoides)) if hmoides else {}
        veredictos = clasificar(todas, por_synckey, por_ide, partes)
        logger.info(
            "[comprobar] lineas=%s presentes=%s borradas=%s sin_synckey=%s "
            "con_diferencias=%s", len(veredictos),
            sum(1 for v in veredictos if v.estado == PRESENTE),
            sum(1 for v in veredictos if v.estado == BORRADA),
            sum(1 for v in veredictos if v.sin_synckey),
            sum(1 for v in veredictos if v.diferencias))
        return veredictos
