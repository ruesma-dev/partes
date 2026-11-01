# application/services/fecha_linea.py
"""F-055 · Fecha valida de una linea a registrar en Sigrid (R1, R2).

Regla PURA: sv5 no escribe una linea cuya fecha no sea un dia real del
calendario entre `FECHA_MINIMA` y hoy + `DIAS_FUTURO` (ambos incluidos).
Sin ella, una linea sin fecha (sv4 manda `fecha_int = 0`) daria de alta el
parte `PT0/00001` del periodo 0/00, y un ano mal tecleado abriria un parte
de 2016 o de 2062; en Sigrid no se borra (F-053).

El motivo empieza por `fecha_no_valida` y no lleva otros dos puntos antes
del detalle: el modal de resultado de sv4 agrupa por lo que va antes de
los primeros dos puntos (F-034 R19). Sin tildes, como el resto de motivos.
"""
from __future__ import annotations

from datetime import date, timedelta

#: Prefijo del motivo (lo agrupa el modal de sv4, F-034 R19).
MOTIVO_FECHA_NO_VALIDA = "fecha_no_valida"
#: Primer dia que sv5 registra: sv3 da los partes de 2026 en adelante.
FECHA_MINIMA = 20260101
#: Dias por delante de hoy que se admiten (DA2, DA10): 31 de lineas
#: anotadas por adelantado + ~31 hasta el dia de ajuste de F-056.
DIAS_FUTURO = 62


def _a_fecha(valor: int) -> date:
    """`AAAAMMDD` -> `date`; `ValueError` si no es un dia del calendario."""
    return date(valor // 10000, (valor // 100) % 100, valor % 100)


def _texto(d: date) -> str:
    return f"{d.day:02d}/{d.month:02d}/{d.year:04d}"


def motivo_fecha_no_valida(fecha_int: object, *, hoy: date) -> str | None:
    """R1-R2: None si la fecha es valida; si no, el motivo entero."""
    if (not isinstance(fecha_int, int) or isinstance(fecha_int, bool)
            or fecha_int <= 0):
        detalle = "la linea no tiene fecha"
    else:
        try:
            dia = _a_fecha(fecha_int)
        except ValueError:
            detalle = f"{fecha_int} no es una fecha del calendario"
        else:
            minima = _a_fecha(FECHA_MINIMA)
            tope = hoy + timedelta(days=DIAS_FUTURO)
            if dia < minima:
                detalle = f"{_texto(dia)} es anterior al {_texto(minima)}"
            elif dia > tope:
                detalle = f"{_texto(dia)} es posterior al {_texto(tope)}"
            else:
                return None
    return (f"{MOTIVO_FECHA_NO_VALIDA}: {detalle}; corrige la fecha en el "
            f"portal y reaprueba")
