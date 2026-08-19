# application/services/jornada_admin.py
"""F-016 · Las reglas de la pantalla de `empleado_jornada`.

Esta pantalla edita el computo de nominas: una fila mal guardada cambia
que horas considera sv3 como extra y, por esa via, lo que se registra en
Sigrid. Por eso TODA validacion ocurre ANTES de escribir y, cuando
rechaza, la BBDD queda intacta.

Modulo PURO a proposito (ni BBDD, ni FastAPI, ni logging), como
`congelacion.py` hizo con F-004: la capa web solo traduce HTTP <-> estas
firmas, y las reglas se prueban sin levantar la app.

**El idioma de la pantalla y el de la tabla no son el mismo.** El humano
habla de «ultimo dia incluido»; la tabla guarda `hasta` EXCLUSIVO
(`desde <= dia < hasta`, semantica de F-015). La traduccion vive AQUI y
solo aqui (`a_hasta_exclusivo` / `a_ultimo_dia_incluido`), con aritmetica
de `date`, nunca de cadenas: asi el 31/12 y el 29/02 salen bien solos.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from application.services.text_match import normalize_dni

#: Columnas del patron en orden lunes..domingo, como las declara el ORM.
DIAS: tuple[str, ...] = (
    "h_lun", "h_mar", "h_mie", "h_jue", "h_vie", "h_sab", "h_dom",
)

#: Como se llama cada dia cuando hay que decirselo a un humano (R9).
NOMBRE_DIA: dict[str, str] = {
    "h_lun": "lunes", "h_mar": "martes", "h_mie": "miercoles",
    "h_jue": "jueves", "h_vie": "viernes", "h_sab": "sabado",
    "h_dom": "domingo",
}

#: Y como se llama en la cabecera de una columna estrecha del formulario.
ABREVIATURA_DIA: dict[str, str] = {
    "h_lun": "L", "h_mar": "M", "h_mie": "X", "h_jue": "J",
    "h_vie": "V", "h_sab": "S", "h_dom": "D",
}

#: Limites de la jornada semanal (R10): mas de 0 y hasta 168 (7 x 24).
SEMANAL_MINIMA = 0.0
SEMANAL_MAXIMA = 168.0
#: Limites de cada hora del patron (R9).
HORA_MINIMA = 0.0
HORA_MAXIMA = 24.0
#: Lo que admite la columna `nota`.
NOTA_MAXIMA = 255


class JornadaInvalida(ValueError):
    """Motivo en espanol, listo para el cuerpo JSON. `campo` situa el error.

    La capa web la traduce a un 422 con `{"ok": false, "error": motivo,
    "campo": campo}`, y el JS marca ese campo del formulario.
    """

    def __init__(self, motivo: str, *, campo: str | None = None) -> None:
        super().__init__(motivo)
        self.motivo = motivo
        self.campo = campo


@dataclass(frozen=True)
class EntradaJornada:
    """Una fila ya normalizada, lista para persistir.

    `hasta` YA ES EXCLUSIVO: la conversion desde el ultimo dia incluido
    ocurre en `normalizar_entrada`. Nadie mas la vuelve a hacer.
    """

    dni_norm: str
    jornada_semanal: float | None
    patron: tuple[float, ...] | None      # 7 valores L..D, o None
    desde: str                            # ISO 'YYYY-MM-DD', INCLUSIVO
    hasta: str | None                     # ISO, EXCLUSIVO; None = abierta
    nota: str | None


# ---------------------------- utilidades ------------------------------- #

def _texto(valor: Any) -> str:
    """Lo que venga del formulario, como texto recortado."""
    if valor is None:
        return ""
    return str(valor).strip()


def _fecha(iso: Any, *, campo: str) -> date:
    """Fecha ISO `YYYY-MM-DD` o `JornadaInvalida` nombrando el campo.

    No vale `date.fromisoformat` a secas: en Python 3.12 acepta formatos
    ISO que el `<input type="date">` nunca manda (`20260701`) y que aqui
    solo pueden venir de alguien trasteando con la API.
    """
    texto = _texto(iso)
    if len(texto) != 10 or texto[4] != "-" or texto[7] != "-":
        raise JornadaInvalida(
            f"La fecha «{texto}» no esta en formato AAAA-MM-DD.", campo=campo)
    try:
        return date.fromisoformat(texto)
    except ValueError:
        raise JornadaInvalida(
            f"La fecha «{texto}» no existe en el calendario.", campo=campo
        ) from None


def _numero(valor: Any, *, campo: str, etiqueta: str) -> float | None:
    """Numero con coma o punto decimal; `""` y `None` son ausencia."""
    texto = _texto(valor)
    if not texto:
        return None
    try:
        return float(texto.replace(",", "."))
    except ValueError:
        raise JornadaInvalida(
            f"{etiqueta}: «{texto}» no es un numero.", campo=campo) from None


def columnas_patron(patron: Sequence[float] | None) -> dict[str, float | None]:
    """Las siete columnas `h_*` a partir del patron (o los siete a NULL)."""
    valores: list[float | None] = list(patron) if patron else [None] * 7
    return dict(zip(DIAS, valores))


# -------------------- R7 · ultimo dia incluido <-> hasta ---------------- #

def a_hasta_exclusivo(ultimo_dia_incluido: str | None) -> str | None:
    """Lo que escribe el humano -> lo que guarda la tabla (`+ 1 dia`).

    «Sin fecha de fin» (vacio o nulo) es `hasta = NULL`: vigencia abierta.
    """
    texto = _texto(ultimo_dia_incluido)
    if not texto:
        return None
    return (_fecha(texto, campo="hasta_inclusivo") + timedelta(days=1)).isoformat()


def a_ultimo_dia_incluido(hasta: str | None) -> str | None:
    """Lo que guarda la tabla -> lo que se le ensena al humano (`- 1 dia`).

    La palabra «exclusivo» no aparece nunca en la pantalla.
    """
    texto = _texto(hasta)
    if not texto:
        return None
    return (_fecha(texto, campo="hasta") - timedelta(days=1)).isoformat()


# ---------------------------- normalizacion ---------------------------- #

def normalizar_entrada(datos: Mapping[str, Any], *,
                       dni_fijo: str | None = None) -> EntradaJornada:
    """Traduce el cuerpo del formulario a una `EntradaJornada`.

    `dni_fijo` es lo que usa la EDICION para ignorar el DNI que venga en
    el cuerpo (R4): cambiar de trabajador es cerrar una fila y crear
    otra, no editar.

    Rechaza aqui lo que no se puede ni representar (DNI vacio, numeros
    ilegibles, patron a medias, fecha de fin imposible); las reglas de
    negocio que necesitan ver el valor ya convertido son de
    `validar_entrada`.
    """
    dni_norm = (normalize_dni(dni_fijo) if dni_fijo is not None
                else normalize_dni(datos.get("dni")))
    if not dni_norm:
        raise JornadaInvalida(
            "Falta el trabajador: elige uno de la lista o escribe su DNI.",
            campo="dni")

    semanal = _numero(datos.get("jornada_semanal"),
                      campo="jornada_semanal", etiqueta="Jornada semanal")

    horas = {dia: _numero(datos.get(dia), campo=dia,
                          etiqueta=f"Horas del {NOMBRE_DIA[dia]}")
             for dia in DIAS}
    puestos = [dia for dia in DIAS if horas[dia] is not None]
    if puestos and len(puestos) < len(DIAS):
        falta = next(dia for dia in DIAS if horas[dia] is None)
        raise JornadaInvalida(
            f"El patron por dias esta a medias: falta el {NOMBRE_DIA[falta]}. "
            "O estan los siete dias, o no hay patron (pon 0 en los que no "
            "se trabaja).", campo=falta)
    patron = tuple(horas[dia] for dia in DIAS) if puestos else None

    nota = _texto(datos.get("nota"))[:NOTA_MAXIMA] or None

    return EntradaJornada(
        dni_norm=dni_norm,
        jornada_semanal=semanal,
        patron=patron,                                  # type: ignore[arg-type]
        desde=_texto(datos.get("desde")),
        hasta=a_hasta_exclusivo(datos.get("hasta_inclusivo")),
        nota=nota,
    )


def entrada_desde_fila(fila: Mapping[str, Any]) -> EntradaJornada:
    """La fila tal como esta guardada, como `EntradaJornada`.

    Lo usa «Reactivar» (R6): al volver a activarla hay que comprobar que
    su vigencia —la que ya tiene— no pisa a ninguna otra activa.
    """
    horas = [fila.get(dia) for dia in DIAS]
    patron = (tuple(float(h) for h in horas)
              if all(h is not None for h in horas) else None)
    semanal = fila.get("jornada_semanal")
    return EntradaJornada(
        dni_norm=normalize_dni(fila.get("dni_norm")),
        jornada_semanal=None if semanal is None else float(semanal),
        patron=patron,
        desde=_texto(fila.get("desde")),
        hasta=_texto(fila.get("hasta")) or None,
        nota=fila.get("nota"),
    )


# ---------------------------- validaciones ----------------------------- #

def validar_vigencia(desde: str | None, hasta: str | None) -> None:
    """R11 · `desde` ISO valida y, si hay `hasta`, `hasta > desde`.

    Se compara sobre `date`, no sobre cadenas: aunque el ISO ordena
    lexicograficamente, asi el error de formato sale donde debe.
    """
    dia_desde = _fecha(desde, campo="desde")
    if hasta is None:
        return
    dia_hasta = _fecha(hasta, campo="hasta_inclusivo")
    if dia_hasta <= dia_desde:
        raise JornadaInvalida(
            "El ultimo dia incluido no puede ser anterior al dia de inicio.",
            campo="hasta_inclusivo")


def validar_entrada(entrada: EntradaJornada) -> None:
    """R8, R9, R10 y R11 sobre una entrada ya normalizada.

    No devuelve nada: o pasa, o lanza `JornadaInvalida` con el motivo que
    va a leer el humano y el campo que hay que marcar en el formulario.
    """
    # R8 · una fila sin `S` y sin patron no dice nada.
    if entrada.jornada_semanal is None and entrada.patron is None:
        raise JornadaInvalida(
            "Indica la jornada semanal o el patron por dias completo: sin "
            "uno de los dos la excepcion no dice nada.",
            campo="jornada_semanal")

    # R10 · rango de la jornada semanal.
    if entrada.jornada_semanal is not None and not (
        SEMANAL_MINIMA < entrada.jornada_semanal <= SEMANAL_MAXIMA
    ):
        raise JornadaInvalida(
            f"La jornada semanal debe estar entre {SEMANAL_MINIMA:g} "
            f"(excluido) y {SEMANAL_MAXIMA:g} horas.",
            campo="jornada_semanal")

    # R9 · rango de cada hora del patron.
    if entrada.patron is not None:
        for dia, valor in zip(DIAS, entrada.patron):
            if not (HORA_MINIMA <= valor <= HORA_MAXIMA):
                raise JornadaInvalida(
                    f"Las horas del {NOMBRE_DIA[dia]} ({valor:g}) estan fuera "
                    f"de {HORA_MINIMA:g}-{HORA_MAXIMA:g}.", campo=dia)

    # R11 · fechas.
    validar_vigencia(entrada.desde, entrada.hasta)


# ------------------------------- R12 · solape --------------------------- #

def _dia_o_none(iso: Any) -> date | None:
    """Fecha de una fila YA GUARDADA, o `None` si no se puede leer.

    Hasta F-016 las filas las cargaba el humano por SQL (F-015), asi que
    puede haber alguna con basura en `desde`. Una fila que no se puede
    situar en el tiempo no se puede comparar: se deja pasar en vez de
    bloquear un alta correcta (el resolutor de F-015 la ignora igual).
    """
    texto = _texto(iso)
    if not texto:
        return None
    try:
        return date.fromisoformat(texto)
    except ValueError:
        return None


def _solapan(desde_a: date, hasta_a: date | None,
             desde_b: date, hasta_b: date | None) -> bool:
    """`[da, ha)` y `[db, hb)` con `None` = infinito.

    Solapan si y solo si `da < hb` y `db < ha`. De ahi sale gratis que
    dos vigencias CONTIGUAS (`hasta` de una = `desde` de la otra) no
    solapen, que es el caso normal de encadenar vigencias.
    """
    if hasta_b is not None and desde_a >= hasta_b:
        return False
    if hasta_a is not None and desde_b >= hasta_a:
        return False
    return True


def buscar_solape(entrada: EntradaJornada,
                  existentes: Sequence[Mapping[str, Any]],
                  *, excluir_id: int | None = None,
                  ) -> Mapping[str, Any] | None:
    """La primera fila ACTIVA del mismo DNI cuya vigencia pisa la entrada.

    Devuelve la de `desde` menor (para que el mensaje sea estable) o
    `None` si no hay conflicto. NUNCA ajusta nada: quien decide cual de
    las dos vigencias cierra es el humano (DA3).
    """
    desde_nueva = _dia_o_none(entrada.desde)
    if desde_nueva is None:
        return None                       # lo rechazara R11, no R12
    hasta_nueva = _dia_o_none(entrada.hasta)

    candidatas: list[tuple[date, Mapping[str, Any]]] = []
    for fila in existentes:
        if not fila.get("is_active"):
            continue
        if excluir_id is not None and fila.get("id") == excluir_id:
            continue
        if normalize_dni(fila.get("dni_norm")) != entrada.dni_norm:
            continue
        desde_fila = _dia_o_none(fila.get("desde"))
        if desde_fila is None:
            continue
        if _solapan(desde_nueva, hasta_nueva,
                    desde_fila, _dia_o_none(fila.get("hasta"))):
            candidatas.append((desde_fila, fila))

    if not candidatas:
        return None
    return min(candidatas, key=lambda par: par[0])[1]


def ultimo_dia_incluido_de_fila(hasta: Any) -> str | None:
    """Como `a_ultimo_dia_incluido`, pero para PINTAR filas ya guardadas.

    Una fila cargada a mano (F-015) puede traer basura en `hasta`. El
    listado la ensena TAL CUAL en vez de romper la pagina entera: asi se
    ve, y se corrige desde la propia pantalla.
    """
    dia = _dia_o_none(hasta)
    if dia is None:
        return _texto(hasta) or None
    return (dia - timedelta(days=1)).isoformat()


def describir_conflicto(fila: Mapping[str, Any]) -> dict[str, Any]:
    """La fila en conflicto, en el idioma del humano (R12).

    Sale tal cual en el cuerpo del 409, asi que `hasta` se traduce a
    ultimo dia incluido: la pantalla no ensena valores exclusivos.
    """
    return {
        "id": fila.get("id"),
        "desde": fila.get("desde"),
        "hasta_inclusivo": ultimo_dia_incluido_de_fila(fila.get("hasta")),
    }
