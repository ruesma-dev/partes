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
  - `texto_ajuste` (DA13, DA26): el `tex` que vera Administracion en
    Sigrid, SIN cifras (no queda desfasado al recalcular) ni nombres.

Enmienda 2026-10-27 (DA1 = C) y 2026-10-29 (DA29-DA31): X es el campo
EXTENDIDO de recurso que rellena Administracion y que solo lee sv5: su
definicion en `defext` (tip 33, el `cod` del ajuste, `camtip` 1 = numero
entero) y su valor en `conext.valn` del `res.ide` del recurso (R47, R48).
Aqui viven su regla (`leer_valor`, R2: NULL o 0 inactiva, (0, 200] activa,
lo demas invalida; `lectura_de`: sin fila inactiva y mas de una invalida),
el filtro del codigo (`COD_EXT_RE`, R38), cuando vale la definicion
(`motivo_definicion`, R38, DA31) y que una franquicia desconocida nunca es
X = 0 (`veredicto`, R42).

No lee ni escribe; lo llama `FranquiciaPipeline` con lo leido. Motivos sin
tildes como el resto de sv5 y de `LIMITE_MOTIVO` caracteres como mucho.
"""
from __future__ import annotations

import math
import re
from decimal import Decimal, InvalidOperation

from application.services.parte_abierto import MOTIVO_PARTE_NO_ABIERTO
from application.services.pisado import LIMITE_MOTIVO, MOTIVO_LINEA_ENLAZADA
from domain.models.registro_models import (
    AccionLinea,
    LecturaFranquicia,
    LineaSigrid,
    VeredictoFranquicia,
)

#: Acciones del veredicto (respuesta `accion` de sv5, design §6).
CREAR = "crear"
ACTUALIZAR = "actualizar"
YA_APLICADO = "ya_aplicado"
SIN_AJUSTE = "sin_ajuste"
NO_EDITABLE = "no_editable"

#: R38, DA30: el `cod` del campo extendido (Texto 16 en `defext`). Va
#: SIEMPRE como parametro: el filtro solo detecta un ajuste mal puesto.
#: `\Z` y no `$`: en Python `$` admite un salto de linea final.
COD_EXT_RE = re.compile(r"^[A-Za-z0-9_.-]{1,16}\Z")

#: R47, H7: tipo de contacto de los recursos (`con.tip`, `defext.tip`). El
#: mismo `cod` existe en otros tipos (el `10` de tip 42) y nunca se lee.
TIP_RECURSO = 33

#: R38, DA31: `defext.camtip` de numero entero (el valor va en `valn`).
CAMTIP_NUMERO = 1

#: R2, DA29: un recurso con mas de una fila del campo (no se elige una).
MOTIVO_VARIAS_FILAS = "mas de una fila del campo para el recurso"

#: R2, DA24: tope de una franquicia valida, en horas por mes de nomina.
MAX_FRANQUICIA_H = 200.0

#: Estado global del campo (R3, R38, R40).
APAGADA = "apagada"
NO_DISPONIBLE = "no_disponible"
OK = "ok"

#: Estado de la franquicia de un recurso (R2).
ACTIVA = "activa"
INACTIVA = "inactiva"
INVALIDA = "invalida"

#: R42: prefijo de motivo de una franquicia que no se sabe.
MOTIVO_FRANQUICIA = "franquicia"

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


def motivo_definicion(filas: list[dict]) -> str | None:
    """R38, DA30, DA31: None si hay EXACTAMENTE una definicion de tip 33
    con ese `cod` y su `camtip` es 1 (numero entero); si no, el motivo de
    `no_disponible` (sin tildes, `LIMITE_MOTIVO` como mucho)."""
    if not filas:
        return f"no hay definicion de tipo {TIP_RECURSO} en defext"
    if len(filas) > 1:
        return (f"{len(filas)} definiciones de tipo {TIP_RECURSO} en "
                f"defext")[:LIMITE_MOTIVO]
    camtip = filas[0].get("camtip")
    try:
        numero = int(camtip) == CAMTIP_NUMERO
    except (TypeError, ValueError):
        numero = False
    if not numero:
        return (f"camtip {camtip}, no es numero entero "
                f"({CAMTIP_NUMERO})")[:LIMITE_MOTIVO]
    return None


def lectura_de(valores: list) -> LecturaFranquicia:
    """R2, DA29: la franquicia de un recurso a partir de los `valn` de sus
    filas del campo. Sin fila => `inactiva` (X = 0); mas de una =>
    `invalida` (no se elige una a ciegas y «no se sabe» no es X = 0, R42);
    una => `leer_valor`."""
    if not valores:
        return LecturaFranquicia(INACTIVA, 0.0)
    if len(valores) > 1:
        return LecturaFranquicia(INVALIDA, None, MOTIVO_VARIAS_FILAS)
    return leer_valor(valores[0])


def leer_valor(valor: object) -> LecturaFranquicia:
    """R2, DA24: el estado de la franquicia de un recurso a partir del valor
    de su campo. NULL o 0 => `inactiva` (X = 0); > 0 y <= 200 => `activa`
    (X a dos decimales); negativo, > 200 o no convertible => `invalida`."""
    if valor is None:
        return LecturaFranquicia(INACTIVA, 0.0)
    if isinstance(valor, bool) or not isinstance(
            valor, (int, float, Decimal, str)):
        return LecturaFranquicia(
            INVALIDA, None, f"valor no numerico ({type(valor).__name__})")
    try:
        x = float(Decimal(str(valor).strip()))
    except (InvalidOperation, ValueError):
        return LecturaFranquicia(INVALIDA, None, "valor no numerico")
    if not math.isfinite(x):
        return LecturaFranquicia(INVALIDA, None, "valor no numerico")
    if x == 0:
        return LecturaFranquicia(INACTIVA, 0.0)
    if x < 0 or x > MAX_FRANQUICIA_H:
        return LecturaFranquicia(
            INVALIDA, None,
            f"valor {x:g} fuera de 0..{MAX_FRANQUICIA_H:g} h"[:LIMITE_MOTIVO])
    return LecturaFranquicia(ACTIVA, _cero(round(x, 2)))


def _igual(a: float | None, b: float | None) -> bool:
    """`can` nula cuenta como 0 (asi la suma Sigrid)."""
    return abs(float(a or 0.0) - float(b or 0.0)) <= TOL + _RUIDO


def _es_extra(codigo: str | None) -> bool:
    return (codigo or "").strip().upper().startswith("HE")


def veredicto(linea: LineaSigrid | None, est_parte: int | None,
              objetivo: float, *, est_registro: int,
              franquicia: LecturaFranquicia | None,
              accion: AccionLinea | None,
              parte_cod: str | None = None) -> VeredictoFranquicia:
    """R24-R30 (orden en el docstring del modulo). `linea` es la de la
    synckey del ajuste (None si no existe), `est_parte` el `con.est` de su
    parte y `accion` lo que `preparar` decidio para una extra del recurso
    el dia de ajuste. R42: ANTES que nada, una franquicia que no es
    `activa` ni `inactiva` (o que no se leyo) no deja escribir."""
    if franquicia is None or franquicia.estado not in (ACTIVA, INACTIVA):
        estado = NO_DISPONIBLE if franquicia is None else franquicia.estado
        detalle = (franquicia.motivo if franquicia is not None
                   and franquicia.motivo else "sin lectura del campo")
        return VeredictoFranquicia(NO_EDITABLE, (
            f"{MOTIVO_FRANQUICIA}_{estado}: {detalle}; no se ajusta (no se "
            f"sabe la franquicia)")[:LIMITE_MOTIVO])
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


def texto_ajuste(periodo: str) -> str:
    """DA13, DA26: el `tex` de produccion de la linea de ajuste, sin cifras
    (la cifra es `can`; X esta en el propio recurso)."""
    return f"Ajuste franquicia extras {periodo}"
