# application/services/parte_abierto.py
"""F-034 · Lo que no entra en Sigrid porque su parte ya no esta abierto
(regla pura, design §5).

sv5 solo escribe lineas en partes En registro (`con.est` =
`EST_PARTE_ACTIVO`). Cada sentencia que toca `hmores` lleva la guarda de
parte abierto (`SigridWriteClient._guarda_parte_abierto`): si
Administracion cierra o contabiliza el parte entre la eleccion (dentro del
lock) y el `commit`, la sentencia afecta 0 filas. Lo que decide si una
linea entro es la RELECTURA por synckey, no la respuesta de `escribir`
(los lotes son transacciones distintas, design §10):

  - `confirmar_escritas`: escrita = synckey releida y en el parte elegido.
  - `parte_que_impidio`: el parte cerrado que lo explica (el de una pisada
    que sigue viva primero, luego el elegido); None si ninguno lo esta.
  - `motivo_parte_no_abierto` / `motivo_no_escrita`: el texto de la
    omitida (DA3), sin tildes como el resto de motivos de sv5, sin nombres
    ni DNIs y de 255 caracteres como mucho (`sigrid_motivo` de sv4).
  - F-053 (R10): `pisadas_no_anuladas` / `motivo_pisada_no_anulada`: si
    ningun parte cerrado lo explica pero alguna pisada sigue con horas en
    un parte En registro (cambio antes de ponerla a 0), ese es el motivo.

No lee ni escribe: lo llama `RegistroPipeline` con lo releido. No toca
`estado_parte.py` (copia literal en `porcentajes`, DA6): el predicado de
«cerrado» es el mismo (`est != est_registro`) y se repite aqui a proposito.
"""
from __future__ import annotations

from collections.abc import Sequence

from application.services.pisado import nombrar_lineas
from domain.models.registro_models import LineaSigrid
from infrastructure.sigrid.sigrid_write_client import synckey_de

#: Prefijo del motivo de una linea cuyo parte se cerro en la ventana (R11).
MOTIVO_PARTE_NO_ABIERTO = "parte_no_abierto"

#: Prefijo del motivo de una linea que no entro sin parte cerrado que lo
#: explique (R11: no deberia ocurrir; el pipeline registra un ERROR).
MOTIVO_NO_ESCRITA = "no_escrita"

#: F-053 (R10): prefijo del motivo de una linea cuya pisada cambio antes
#: de ponerla a 0 (sigue con horas en un parte En registro).
MOTIVO_PISADA_NO_ANULADA = "pisada_no_anulada"

#: Largo maximo de un motivo (`parte_registro.sigrid_motivo` de sv4).
LIMITE_MOTIVO = 255


def motivo_parte_no_abierto(cod: str | None, estado: str) -> str:
    """R11: la linea no entro porque su parte `cod` ya no esta En registro
    (`estado` es el nombre de `nombre_estado`: Cerrado, Imputado...)."""
    return (f"{MOTIVO_PARTE_NO_ABIERTO}: el parte {cod or '?'} ya no esta "
            f"En registro ({estado}); no se registra. Reaprueba para "
            f"llevarla al parte En registro del mes")[:LIMITE_MOTIVO]


def motivo_no_escrita(cod: str | None) -> str:
    """R11: la linea no entro y ningun parte cerrado lo explica."""
    return (f"{MOTIVO_NO_ESCRITA}: Sigrid no confirmo la linea en el parte "
            f"{cod or '?'}; reaprueba")[:LIMITE_MOTIVO]


def motivo_pisada_no_anulada(ides: Sequence[int], cod: str | None) -> str:
    """F-053 (R10, R11): la linea no entro porque su pisada `ides` del
    parte `cod` cambio antes de ponerla a 0 (F-034 R4 lo impidio)."""
    lineas, plural = nombrar_lineas(ides)
    return (f"{MOTIVO_PISADA_NO_ANULADA}: {'las' if plural else 'la'} "
            f"{lineas} del parte {cod or '?'} "
            f"{'cambiaron' if plural else 'cambio'} antes de "
            f"{'ponerlas' if plural else 'ponerla'} a 0; no se registra. "
            f"Vuelve a aprobar para revisar el conflicto")[:LIMITE_MOTIVO]


def pisadas_no_anuladas(
    pisadas: Sequence[int], vivas: dict[int, LineaSigrid],
    estados: dict[int, int | None], *, est_registro: int,
) -> list[int]:
    """F-053 (R10): de las `pisadas` de una linea, las que siguen con horas
    (`vivas`, releidas por `ide`) en un parte En registro, en su orden. Un
    parte que no sale en la relectura (`estados`) no cuenta."""
    return [i for i in pisadas
            if i in vivas and vivas[i].hmoide in estados
            and estados[vivas[i].hmoide] == est_registro]


def confirmar_escritas(
    escritas: list[dict], leidas: dict[str, LineaSigrid]
) -> tuple[list[dict], list[dict]]:
    """R9: separa lo enviado en (confirmadas, no_escritas), en su orden.

    Confirmada = su synckey esta en `leidas` (relectura tras escribir) y en
    el parte elegido (`hmoide` de la escrita); se le rellena `hmores_ide`.
    Una synckey que vive en OTRO parte no la escribio esta peticion."""
    confirmadas: list[dict] = []
    no_escritas: list[dict] = []
    for e in escritas:
        hit = leidas.get(synckey_de(e["registro_id"]))
        if hit is not None and hit.hmoide == e["hmoide"]:
            confirmadas.append(dict(e, hmores_ide=hit.ide))
        else:
            no_escritas.append(e)
    return confirmadas, no_escritas


def parte_que_impidio(
    hmoide_elegido: int, hmoides_pisadas_vivas: Sequence[int],
    estados: dict[int, int | None], *, est_registro: int,
) -> int | None:
    """R11: el parte que impidio escribir la linea, o None.

    Primero el de una pisada que sigue con horas (su puesta a 0 no entro y,
    por R4, la linea nueva tampoco); despues el elegido. Un parte que no
    sale en la relectura (`estados`) no se puede nombrar: no cuenta."""
    for h in [*hmoides_pisadas_vivas, hmoide_elegido]:
        if h in estados and estados[h] != est_registro:
            return h
    return None
