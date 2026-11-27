# application/services/partes_con_problemas.py
"""F-084 · Partes con problemas: motivos, sustituto y aviso.

Un parte tiene problemas si, ACTIVO, le falta la obra o la fecha, la fecha
es dudosa o no le queda ninguna linea viva (R6), o si es un SUSTITUIDO:
inactivo, fuera de la papelera y no retirado por F-061 (R7, R9). Del
sustituido se busca quien lo sustituyo (R8): el documento de
`sustituido_por_id` (rastro de sv3 desde F-084) o, para los anteriores, una
PISTA entre los activos de la misma fecha y obra creados despues. La pista
es para la pantalla, no la regla de reemplazo de sv3.

Modulo PURO (ni BBDD, ni ORM, ni FastAPI), como `parte_vacio.py`: el
repositorio le pasa `DocProblema` y pinta lo que devuelve `clasificar`.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from application.services.parte_vacio import es_retirado

MOTIVO_SIN_OBRA = "sin_obra"
MOTIVO_SIN_FECHA = "sin_fecha"
MOTIVO_FECHA_FUTURA = "fecha_futura"
MOTIVO_FECHA_POSTERIOR_CORREO = "fecha_posterior_al_correo"
MOTIVO_SIN_LINEAS = "sin_lineas"
MOTIVO_SUSTITUIDO_MISMO_ENVIO = "sustituido_mismo_envio"
MOTIVO_SUSTITUIDO = "sustituido"
MOTIVO_SIN_RASTRO = "desactivado_sin_rastro"

#: Orden de R6 y R7, con los que cuentan para el aviso primero.
ORDEN_MOTIVOS: tuple[str, ...] = (
    MOTIVO_SIN_OBRA,
    MOTIVO_SIN_FECHA,
    MOTIVO_FECHA_FUTURA,
    MOTIVO_FECHA_POSTERIOR_CORREO,
    MOTIVO_SIN_LINEAS,
    MOTIVO_SUSTITUIDO_MISMO_ENVIO,
    MOTIVO_SIN_RASTRO,
    MOTIVO_SUSTITUIDO,
)

#: Motivos que se listan pero no suman en el contador (R10, D3).
NO_CUENTAN = frozenset({MOTIVO_SUSTITUIDO})

#: Rotulo de cada motivo en la pantalla.
TEXTOS: dict[str, str] = {
    MOTIVO_SIN_OBRA: "Sin obra casada",
    MOTIVO_SIN_FECHA: "Sin fecha",
    MOTIVO_FECHA_FUTURA: "Fecha futura",
    MOTIVO_FECHA_POSTERIOR_CORREO: "Fecha posterior al correo",
    MOTIVO_SIN_LINEAS: "Sin líneas",
    MOTIVO_SUSTITUIDO_MISMO_ENVIO: "Sustituido por otra página del mismo correo",
    MOTIVO_SIN_RASTRO: "Desactivado sin sustituto",
    MOTIVO_SUSTITUIDO: "Sustituido por un reenvío",
}

#: Dias de margen entre la recepcion del correo y la fecha del parte (D5).
MARGEN_CORREO_DIAS = 1

MOTIVO_NO_REC_ACTIVO = "El parte ya está activo: no hay nada que recuperar."
MOTIVO_NO_REC_PAPELERA = (
    "El parte está en la papelera: restáuralo desde allí.")
MOTIVO_NO_REC_RETIRADO = (
    "El parte se retiró por quedarse sin líneas: restaura sus líneas.")
MOTIVO_CHOQUE = (
    "Ya hay otro parte activo del mismo día y obra con los mismos "
    "trabajadores. Corrige la fecha o descarta antes el otro parte.")


class NoRecuperableError(Exception):
    """El parte no es un sustituido: activo, en la papelera o retirado."""

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


class ChoqueRecuperarError(Exception):
    """Recuperarlo dejaria dos partes activos del mismo dia, obra y
    trabajador (R19, D6). `partes` = [{id, fecha, obra}] de los otros."""

    def __init__(self, partes: list[dict]) -> None:
        super().__init__(MOTIVO_CHOQUE)
        self.motivo = MOTIVO_CHOQUE
        self.partes = partes


@dataclass(frozen=True)
class DocProblema:
    """Lo que la clasificacion necesita de un documento."""

    id: str
    is_active: bool
    deleted_at_utc: str | None
    deleted_by: str | None
    fecha_int: int | None
    obra_ide: int | None
    obra_codigo: str | None
    obra_numero_leido: str | None
    email_id: str | None
    email_received_datetime: str | None
    created_at_utc: str
    sustituido_por_id: str | None
    lineas_vivas: int
    es_futuro: bool


@dataclass(frozen=True)
class Clasificado:
    """Un parte con problemas: sus motivos y, si es sustituido, su sustituto."""

    doc: DocProblema
    motivos: tuple[str, ...]
    sustituto: DocProblema | None

    @property
    def motivo(self) -> str:
        """El motivo por el que se agrupa en la pantalla (el primero)."""
        return self.motivos[0]

    @property
    def cuenta(self) -> bool:
        return cuenta_para_aviso(self.motivos)


def _texto(valor: str | None) -> str:
    return (valor or "").strip()


def _instante(iso: str | None) -> datetime | None:
    """ISO 8601 a `datetime` en UTC (sin zona = UTC); ilegible, None."""
    try:
        momento = datetime.fromisoformat(_texto(iso))
    except (TypeError, ValueError):
        return None
    if momento.tzinfo is None:
        return momento.replace(tzinfo=timezone.utc)
    return momento.astimezone(timezone.utc)


def _fecha_valida(fecha_int: int | None) -> bool:
    return fecha_int is not None and fecha_int > 0


def es_sustituido(d: DocProblema) -> bool:
    """Inactivo, fuera de la papelera y no retirado por F-061 (R7, R9)."""
    return (not d.is_active and not d.deleted_at_utc
            and not es_retirado(is_active=d.is_active,
                                deleted_at_utc=d.deleted_at_utc,
                                deleted_by=d.deleted_by))


def motivo_no_recuperable(d: DocProblema) -> str | None:
    """Por que no se puede recuperar (R22), o None si es un sustituido."""
    if d.is_active:
        return MOTIVO_NO_REC_ACTIVO
    if d.deleted_at_utc:
        return MOTIVO_NO_REC_PAPELERA
    if not es_sustituido(d):
        return MOTIVO_NO_REC_RETIRADO
    return None


def fecha_posterior_al_correo(fecha_int: int | None,
                              recibido_iso: str | None) -> bool:
    """La fecha del parte pasa del dia UTC del correo mas el margen (D5).

    Sin fecha, sin correo o con una hora ilegible, no salta."""
    if not _fecha_valida(fecha_int):
        return False
    recibido = _instante(recibido_iso)
    if recibido is None:
        return False
    limite: date = recibido.date() + timedelta(days=MARGEN_CORREO_DIAS)
    return fecha_int > int(limite.strftime("%Y%m%d"))


def motivos_activo(d: DocProblema) -> tuple[str, ...]:
    """Motivos de un parte ACTIVO, en el orden de R6."""
    motivos: list[str] = []
    if d.obra_ide is None:
        motivos.append(MOTIVO_SIN_OBRA)
    if not _fecha_valida(d.fecha_int):
        motivos.append(MOTIVO_SIN_FECHA)
    if d.es_futuro:
        motivos.append(MOTIVO_FECHA_FUTURA)
    if fecha_posterior_al_correo(d.fecha_int, d.email_received_datetime):
        motivos.append(MOTIVO_FECHA_POSTERIOR_CORREO)
    if d.lineas_vivas <= 0:
        motivos.append(MOTIVO_SIN_LINEAS)
    return tuple(motivos)


def mismo_envio(a: DocProblema, b: DocProblema) -> bool:
    """Los dos vienen del mismo correo: `email_id` igual y no vacio."""
    return bool(_texto(a.email_id)) and _texto(a.email_id) == _texto(b.email_id)


def _misma_obra(a: DocProblema, b: DocProblema) -> bool:
    """Por codigo casado; sin codigo, por el numero leido (como sv3)."""
    codigo = _texto(a.obra_codigo)
    if codigo:
        return _texto(b.obra_codigo) == codigo
    numero = _texto(a.obra_numero_leido)
    return (bool(numero) and not _texto(b.obra_codigo)
            and _texto(b.obra_numero_leido) == numero)


def _clave_antiguedad(d: DocProblema) -> datetime:
    return _instante(d.created_at_utc) or datetime.max.replace(
        tzinfo=timezone.utc)


def elegir_sustituto(d: DocProblema, por_id: Mapping[str, DocProblema],
                     activos: Iterable[DocProblema]) -> DocProblema | None:
    """El parte que sustituyo a `d` (R8).

    Con `sustituido_por_id`, ese documento (None si ya no existe). Sin el,
    la pista: activos de la misma fecha y obra creados despues; el del
    mismo envio si lo hay y, si no, el mas antiguo."""
    if _texto(d.sustituido_por_id):
        return por_id.get(_texto(d.sustituido_por_id))
    if not _fecha_valida(d.fecha_int):
        return None
    creado = _clave_antiguedad(d)
    candidatos = [
        c for c in activos
        if c.is_active and c.id != d.id and c.fecha_int == d.fecha_int
        and _misma_obra(d, c) and _clave_antiguedad(c) > creado
    ]
    if not candidatos:
        return None
    candidatos.sort(key=_clave_antiguedad)
    for c in candidatos:
        if mismo_envio(d, c):
            return c
    return candidatos[0]


def motivo_sustituido(d: DocProblema, sustituto: DocProblema | None) -> str:
    """El unico motivo de un sustituido (R7)."""
    if sustituto is None:
        return MOTIVO_SIN_RASTRO
    if mismo_envio(d, sustituto):
        return MOTIVO_SUSTITUIDO_MISMO_ENVIO
    return MOTIVO_SUSTITUIDO


def cuenta_para_aviso(motivos: Iterable[str]) -> bool:
    """Algun motivo que cuenta: todos menos `sustituido` (R10, D3)."""
    return any(m not in NO_CUENTAN for m in motivos)


def clasificar(docs: Iterable[DocProblema]) -> list[Clasificado]:
    """Los partes con problemas, por motivo (orden de `ORDEN_MOTIVOS`) y,
    dentro, por fecha descendente. Ni papelera ni retirados (R9)."""
    todos = list(docs)
    por_id = {d.id: d for d in todos}
    activos = [d for d in todos if d.is_active and not d.deleted_at_utc]
    filas: list[Clasificado] = []
    for d in todos:
        if d.deleted_at_utc:
            continue
        if d.is_active:
            motivos = motivos_activo(d)
            if motivos:
                filas.append(Clasificado(d, motivos, None))
        elif es_sustituido(d):
            sustituto = elegir_sustituto(d, por_id, activos)
            filas.append(Clasificado(
                d, (motivo_sustituido(d, sustituto),), sustituto))
    filas.sort(key=lambda f: (ORDEN_MOTIVOS.index(f.motivo),
                              -(f.doc.fecha_int or 0)))
    return filas


def resumen(filas: Iterable[Clasificado]) -> dict:
    """`{total, por_motivo}`: total de los que cuentan y cuantos partes
    tienen cada motivo (R10, R25)."""
    total = 0
    por_motivo: dict[str, int] = {}
    for f in filas:
        if f.cuenta:
            total += 1
        for m in f.motivos:
            por_motivo[m] = por_motivo.get(m, 0) + 1
    return {"total": total, "por_motivo": por_motivo}
