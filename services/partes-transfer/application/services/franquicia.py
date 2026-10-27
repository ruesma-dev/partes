# application/services/franquicia.py
"""F-056 · Franquicia de extras: el ajuste y que hacer con su linea (regla
pura, design §4).

Hay trabajadores que solo cobran las horas extra que pasan de una
franquicia X por mes de nomina (16 -> 15). El ultimo laborable del periodo
se anade UNA linea `HE*` negativa que resta las extras hasta X:

  - `ajuste_objetivo` (A del glosario): `-min(E, X)` si las extras netas
    del periodo E son positivas; si no, 0. Dos decimales. Es la UNICA
    copia de la formula (DA15): sv4 solo pinta lo que responde sv5.
  - `veredicto` (R24-R30): con la linea de ajuste leida por su synckey
    (`partes:franquicia:<id>`), el estado de su parte y lo que `preparar`
    del registro decidio para una extra del recurso, que se hara:

        no_editable  el registro no escribiria una extra `HE*` de ese
                     recurso (R30: verificacion F-023, reglas, dedicacion
                     F-019), o la linea esta en un parte que no esta En
                     registro o enlazada (R27);
        sin_ajuste   no hay linea y A = 0 (R28): no se escribe nada;
        crear        no hay linea y A != 0 (R24): una linea nueva;
        ya_aplicado  la linea ya vale A (R28; se mira antes que el parte y
                     los enlaces: lo ya escrito se reconoce aunque despues
                     cerraran el parte);
        actualizar   la linea existe con otro `can` (R25), tambien si A = 0:
                     la linea queda a 0, nunca se borra (regla de F-053).
  - `texto_ajuste` (DA13): el `tex` que vera Administracion en Sigrid, sin
    nombres ni DNIs.

No lee ni escribe; lo llama `FranquiciaPipeline` con lo leido. Motivos sin
tildes como el resto de sv5 y de `LIMITE_MOTIVO` caracteres como mucho.
"""
from __future__ import annotations

from application.services.parte_abierto import MOTIVO_PARTE_NO_ABIERTO
from application.services.pisado import LIMITE_MOTIVO, MOTIVO_LINEA_ENLAZADA
from domain.models.registro_models import (
    AccionLinea,
    LineaSigrid,
    VeredictoFranquicia,
)

#: Acciones del veredicto (respuesta `accion` de sv5, design §6).
CREAR = "crear"
ACTUALIZAR = "actualizar"
YA_APLICADO = "ya_aplicado"
SIN_AJUSTE = "sin_ajuste"
NO_EDITABLE = "no_editable"

#: Tolerancia en horas al comparar `can` con A (como el reajuste, F-046).
TOL = 0.001

#: Ruido de coma flotante: `6.001 - 6` no es exactamente 0,001.
_RUIDO = 1e-9

#: R30: el registro no escribiria una extra de ese recurso.
MOTIVO_NO_REGISTRABLE = "no_editable: el registro no escribiria la extra"

#: R30: las reglas no dan al recurso un codigo de hora extra (`HE*`).
MOTIVO_SIN_HE = "no_editable: el recurso no tiene codigo de hora extra HE*"


def _cero(valor: float) -> float:
    """Sin «-0.0» (se veria en el modal y en el `tex`)."""
    return valor + 0.0


def ajuste_objetivo(extras: float, franquicia: float) -> float:
    """A: `-min(E, X)` si E > 0; si no, 0. Dos decimales."""
    e, x = float(extras or 0.0), float(franquicia or 0.0)
    if e <= 0:
        return 0.0
    return _cero(round(-min(e, x), 2))


def _igual(a: float | None, b: float | None) -> bool:
    """`can` nula cuenta como 0 (asi la suma Sigrid)."""
    return abs(float(a or 0.0) - float(b or 0.0)) <= TOL + _RUIDO


def _es_extra(codigo: str | None) -> bool:
    return (codigo or "").strip().upper().startswith("HE")


def veredicto(linea: LineaSigrid | None, est_parte: int | None,
              objetivo: float, *, est_registro: int,
              accion: AccionLinea | None,
              parte_cod: str | None = None) -> VeredictoFranquicia:
    """R24-R30 (orden en el docstring del modulo). `linea` es la de la
    synckey del ajuste (None si no existe), `est_parte` el `con.est` de su
    parte y `accion` lo que `preparar` decidio para una extra del recurso
    el dia de ajuste."""
    if accion is None or accion.accion != "escribir":
        detalle = "sin decision" if accion is None else (
            f"{accion.accion}: {accion.motivo}")
        return VeredictoFranquicia(
            NO_EDITABLE,
            f"{MOTIVO_NO_REGISTRABLE} ({detalle})"[:LIMITE_MOTIVO])
    if not _es_extra(accion.hora_codigo):
        return VeredictoFranquicia(
            NO_EDITABLE,
            f"{MOTIVO_SIN_HE} (codigo {accion.hora_codigo or '-'})")
    if linea is None:
        return VeredictoFranquicia(
            SIN_AJUSTE if _igual(objetivo, 0.0) else CREAR)
    if _igual(linea.can, objetivo):
        return VeredictoFranquicia(YA_APLICADO)
    if est_parte != est_registro:
        return VeredictoFranquicia(NO_EDITABLE, (
            f"{MOTIVO_PARTE_NO_ABIERTO}: la linea de ajuste {linea.ide} esta "
            f"en el parte {parte_cod or '?'} (estado {est_parte}), que no "
            f"esta En registro; regularizala en Sigrid")[:LIMITE_MOTIVO])
    if linea.enlazada:
        return VeredictoFranquicia(NO_EDITABLE, (
            f"{MOTIVO_LINEA_ENLAZADA}: la linea de ajuste {linea.ide} del "
            f"parte {parte_cod or '?'} esta enlazada (albaran, factura, "
            f"dedicacion o nomina); regularizala en Sigrid")[:LIMITE_MOTIVO])
    return VeredictoFranquicia(ACTUALIZAR)


def _horas(valor: float) -> str:
    """Horas con coma decimal y sin ceros sobrantes: -6, -7,5, -2,25."""
    texto = f"{_cero(round(float(valor or 0.0), 2)):.2f}".rstrip("0")
    return texto.rstrip(".").replace(".", ",")


def texto_ajuste(periodo: str, objetivo: float, franquicia: float) -> str:
    """DA13, design §6: el `tex` de produccion de la linea de ajuste."""
    return (f"Ajuste franquicia extras {periodo}: {_horas(objetivo)} h "
            f"(franquicia {_horas(franquicia)} h)")
