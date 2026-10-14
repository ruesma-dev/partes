# application/services/reajuste_lineas.py
"""F-046 · ¿Se puede reajustar esta linea en Sigrid? (regla pura).

Al aprobar el segundo parte de un dia, el reparto ponderado (F-045) puede
cambiar lineas que ya estan en Sigrid. sv5 solo las edita si NADIE las ha
tocado desde que se escribieron y siguen donde se pueden editar:

  - existente (R21): su synckey `partes:<registro_id>` esta en `hmores`,
    su parte esta En registro, no la enlaza nada (albaran, factura,
    dedicacion, nomina: DA17) y `can` vale «antes» (tolerancia `TOL`).
  - nueva (R22): la extra que nace de una base registrada sin extra. Su
    synckey no existe, su base es editable, el registro la escribiria
    (`preparar` la decide `escribir`), va al parte de la misma obra que su
    base y no hay linea ajena del mismo recurso, dia y codigo de hora en
    los partes En registro del periodo.

R26: una linea que ya tiene «despues» es `ya_aplicada` (un `ejecutar`
anterior llego a escribir aunque su llamante no viera la respuesta). Se
mira ANTES que el estado del parte y los enlaces: lo ya escrito se
reconoce aunque luego cerraran el parte, y no se vuelve a escribir.

Nada de esto lee ni escribe: lo llama `ReajustePipeline` con lo leido.
Los motivos van sin nombres ni DNIs (R29).
"""
from __future__ import annotations

from collections.abc import Sequence

from domain.models.registro_models import (
    AccionLinea,
    LineaSigrid,
    OpReajuste,
    VeredictoReajuste,
)
from infrastructure.sigrid.sigrid_write_client import synckey_de

#: Tolerancia en horas al comparar `can` con «antes» o «despues» (R21).
TOL = 0.001

#: Ruido de coma flotante: `8.001 - 8` no es exactamente 0,001.
_RUIDO = 1e-9

MOTIVO_NO_EXISTE = "la linea no esta en Sigrid"
MOTIVO_PARTE_NO_EN_REGISTRO = "su parte de Sigrid no esta En registro"
MOTIVO_ENLAZADA = (
    "la linea esta enlazada en Sigrid (albaran, factura, dedicacion o "
    "nomina)")
MOTIVO_CAN_DISTINTA = "la linea cambio en Sigrid"
MOTIVO_NUEVA_DISTINTA = "la extra nueva ya existe en Sigrid con otras horas"
MOTIVO_BASE_NO_EDITABLE = "su linea base no es editable"
MOTIVO_PARCIAL = (
    "la base ya tiene las horas nuevas pero la extra nueva no esta en "
    "Sigrid")
MOTIVO_NO_REGISTRABLE = "el registro no escribiria la extra nueva"
MOTIVO_CHOQUE = (
    "ya hay horas de ese recurso, dia y codigo de hora en un parte En "
    "registro")
MOTIVO_OTRA_OBRA = "la base esta en el parte de otra obra"


def _igual(a: float | None, b: float | None) -> bool:
    """`can` nula cuenta como 0 (asi la lee Sigrid en sus sumas)."""
    return abs(float(a or 0.0) - float(b or 0.0)) <= TOL + _RUIDO


def _num(valor: float | None) -> str:
    return f"{float(valor or 0.0):g}"


def veredicto_existente(op: OpReajuste, linea: LineaSigrid | None,
                        est_parte: int | None, *,
                        est_registro: int) -> VeredictoReajuste:
    """R21 y R26 para una linea ya registrada."""
    rid = op.registro_id
    if linea is None:
        return VeredictoReajuste(
            rid, editable=False,
            motivo=f"{MOTIVO_NO_EXISTE} ({synckey_de(rid)})")
    if _igual(linea.can, op.despues):
        return VeredictoReajuste(rid, editable=True, ya_aplicada=True)
    if est_parte != est_registro:
        return VeredictoReajuste(
            rid, editable=False,
            motivo=f"{MOTIVO_PARTE_NO_EN_REGISTRO} (estado {est_parte})")
    if linea.enlazada:
        return VeredictoReajuste(
            rid, editable=False, motivo=f"{MOTIVO_ENLAZADA} (linea {linea.ide})")
    if not _igual(linea.can, op.antes):
        return VeredictoReajuste(
            rid, editable=False,
            motivo=(f"{MOTIVO_CAN_DISTINTA}: tiene {_num(linea.can)} h y se "
                    f"esperaban {_num(op.antes)} h (linea {linea.ide})"))
    return VeredictoReajuste(rid, editable=True)


def veredicto_nueva(op: OpReajuste, *, existente: LineaSigrid | None,
                    base: VeredictoReajuste, accion: AccionLinea | None,
                    choques: Sequence[LineaSigrid],
                    misma_obra: bool) -> VeredictoReajuste:
    """R22 y R26 para una extra nueva.

    `existente`: la fila de su synckey, si ya esta; `base`: el veredicto
    de su base; `accion`: lo que decidio `preparar`; `choques`: lineas
    ajenas del mismo recurso, dia y codigo en partes En registro del
    periodo; `misma_obra`: el parte de la base es de la obra destino.
    """
    rid = op.registro_id
    if existente is not None:
        if _igual(existente.can, op.despues):
            return VeredictoReajuste(rid, editable=True, ya_aplicada=True)
        return VeredictoReajuste(
            rid, editable=False,
            motivo=(f"{MOTIVO_NUEVA_DISTINTA}: tiene {_num(existente.can)} h "
                    f"(linea {existente.ide})"))
    if not base.editable:
        return VeredictoReajuste(
            rid, editable=False,
            motivo=f"{MOTIVO_BASE_NO_EDITABLE}: {base.motivo}")
    if base.ya_aplicada:
        return VeredictoReajuste(rid, editable=False, motivo=MOTIVO_PARCIAL)
    if accion is None or accion.accion != "escribir":
        detalle = "sin decision" if accion is None else (
            f"{accion.accion}: {accion.motivo}")
        return VeredictoReajuste(
            rid, editable=False, motivo=f"{MOTIVO_NO_REGISTRABLE} ({detalle})")
    if not misma_obra:
        return VeredictoReajuste(rid, editable=False, motivo=MOTIVO_OTRA_OBRA)
    if choques:
        ides = ", ".join(str(c.ide) for c in choques)
        return VeredictoReajuste(
            rid, editable=False, motivo=f"{MOTIVO_CHOQUE} (lineas {ides})")
    return VeredictoReajuste(rid, editable=True)
