# application/services/congelacion.py
"""F-004 · La regla UNICA de congelacion de registros aprobados.

Una linea del portal esta CONGELADA cuando aceptar una edicion suya
dejaria la BBDD `partes` diciendo una cosa y Sigrid otra:

  - su parte esta **aprobado**: el contenido ya se dio por bueno y solo
    se toca desaprobandolo antes de forma explicita;
  - su `sigrid_estado` es **encolado**: hay una peticion en vuelo hacia
    sv5 y el resultado volvera a pisar las columnas `sigrid_*`;
  - su `sigrid_estado` es **registrado**: la hora ya vive en Sigrid. Y no
    se arregla reaprobando: el synckey es estable por `registro_id`, asi
    que sv5 la daria por `ya_registrado` y NO actualizaria valores. La
    divergencia seria permanente.

`omitido`, `error`, `conflicto` y el estado vacio NO congelan: editar es
precisamente el camino de arreglo de esas lineas (asignar el codigo de
hora que falta, corregir el dato que fallo, resolver el conflicto) y
bloquearlas dejaria el portal sin salida.

Este modulo es PURO a proposito (ni BBDD, ni FastAPI, ni ORM): lo usan
tanto las guardas del repositorio —que rechazan la mutacion con
`CongeladoError`— como las vistas —que pintan el candado—. Una sola
decision para las dos: si se escribiera dos veces, un dia el portal
ensenaria como editable algo que el servidor rechaza.
"""
from __future__ import annotations

from collections.abc import Iterable

#: Peticion en vuelo hacia sv5 (q-transfer); el resultado esta por llegar.
ESTADO_ENCOLADO = "encolado"
#: Veredicto final: la linea se escribio en Sigrid (`hmores`).
ESTADO_REGISTRADO = "registrado"

#: Los unicos estados de `parte_registros.sigrid_estado` que congelan por
#: si mismos, sin mirar si el documento esta aprobado.
ESTADOS_CONGELANTES: tuple[str, ...] = (ESTADO_ENCOLADO, ESTADO_REGISTRADO)

# --- Motivos (los lee el humano en el candado y en el 409) ------------- #
MOTIVO_LINEA_ENCOLADA = (
    "Linea encolada hacia Sigrid: la peticion esta en vuelo. Espera a que "
    "llegue el resultado para poder editarla."
)
MOTIVO_LINEA_REGISTRADA = (
    "Linea ya registrada en Sigrid: editarla aqui no la cambiaria alli "
    "(el synckey evita que se reescriba). Para corregirla hay que "
    "eliminar la linea en Sigrid y volver a aprobarla."
)
MOTIVO_LINEA_APROBADA = (
    "Parte aprobado: marcalo pendiente («Marcar pendiente») antes de "
    "editar sus lineas."
)
MOTIVO_DOC_ENCOLADO = (
    "El parte tiene lineas encoladas hacia Sigrid: la peticion esta en "
    "vuelo. Espera a que llegue el resultado."
)
MOTIVO_DOC_REGISTRADO = (
    "El parte tiene lineas ya registradas en Sigrid: cambiar su fecha u "
    "obra (o borrarlo) dejaria el portal y Sigrid diciendo cosas "
    "distintas."
)
MOTIVO_DOC_APROBADO = MOTIVO_LINEA_APROBADA
MOTIVO_UNAPPROVE_ENCOLADO = (
    "No se puede marcar pendiente: hay lineas encoladas hacia Sigrid. "
    "Editar mientras sv5 procesa la peticion produce una carrera; espera "
    "a que llegue el resultado."
)


class CongeladoError(Exception):
    """Mutacion de usuario rechazada por congelacion.

    La capa web la traduce a un 409 con el motivo; nunca es un 500: no es
    un fallo del sistema, es una regla de negocio diciendo que no.
    """

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


def _normaliza(estado: str | None) -> str:
    """`sigrid_estado` es texto libre en la columna: se compara normalizado
    para que un espacio o una mayuscula no descongele una linea."""
    return (estado or "").strip().lower()


def motivo_congelacion_linea(
    *, doc_aprobado: bool, sigrid_estado: str | None,
) -> str | None:
    """Motivo por el que la LINEA esta congelada, o None si es editable.

    Prioridad: encolado > registrado > aprobado, del mas restrictivo e
    informativo al menos: quien vea el candado de una linea registrada
    necesita saber que desaprobar el parte NO la libera (R11).
    """
    estado = _normaliza(sigrid_estado)
    if estado == ESTADO_ENCOLADO:
        return MOTIVO_LINEA_ENCOLADA
    if estado == ESTADO_REGISTRADO:
        return MOTIVO_LINEA_REGISTRADA
    if doc_aprobado:
        return MOTIVO_LINEA_APROBADA
    return None


def motivo_congelacion_documento(
    *, aprobado: bool, estados_lineas: Iterable[str | None],
) -> str | None:
    """Motivo por el que el DOCUMENTO esta congelado, o None.

    `estados_lineas` son los `sigrid_estado` de TODAS sus lineas, tambien
    las que estan en papelera: las ediciones de cabecera (fecha, obra)
    propagan a todas, y una linea borrada del portal puede seguir viva en
    Sigrid.
    """
    estados = {_normaliza(e) for e in estados_lineas}
    if ESTADO_ENCOLADO in estados:
        return MOTIVO_DOC_ENCOLADO
    if ESTADO_REGISTRADO in estados:
        return MOTIVO_DOC_REGISTRADO
    if aprobado:
        return MOTIVO_DOC_APROBADO
    return None


def exigir_linea_editable(
    *, doc_aprobado: bool, sigrid_estado: str | None,
) -> None:
    """Guarda de las mutaciones por linea. Lanza `CongeladoError`."""
    motivo = motivo_congelacion_linea(
        doc_aprobado=doc_aprobado, sigrid_estado=sigrid_estado)
    if motivo is not None:
        raise CongeladoError(motivo)


def exigir_documento_editable(
    *, aprobado: bool, estados_lineas: Iterable[str | None],
) -> None:
    """Guarda de las mutaciones de cabecera/documento."""
    motivo = motivo_congelacion_documento(
        aprobado=aprobado, estados_lineas=estados_lineas)
    if motivo is not None:
        raise CongeladoError(motivo)


def hay_linea_encolada(estados_lineas: Iterable[str | None]) -> bool:
    """R10: la desaprobacion se rechaza SOLO por lineas en vuelo.

    Con lineas ya `registrado` si se permite desaprobar (hace falta para
    corregir las que no llegaron a Sigrid); esas lineas siguen congeladas
    por `motivo_congelacion_linea`.
    """
    return any(_normaliza(e) == ESTADO_ENCOLADO for e in estados_lineas)
