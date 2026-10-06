# application/services/estado_parte.py
"""F-031 · En que parte de Sigrid escribe sv5 (regla pura, design §7.1).

Sigrid genera el asiento analitico de un parte al «Contabilizar» (estado
Imputado). sv5 nunca escribe en un parte que no este En registro: para
Administracion, un parte Cerrado o Imputado se modifica con un parte
COMPLEMENTARIO de la misma obra y mes (humano, 2026-10-05; «cerrado» = todo
lo que no esta En registro, confirmado el 2026-10-06).

  - El parte elegido es el de mayor `ide` En registro del periodo (R2).
  - Si no hay ninguno, se propone uno nuevo (R3, R4); el pipeline le pone
    el codigo `PT<AA>/NNNNN` de la empresa como siempre.
  - Hay complementario cuando el periodo tiene algun parte cerrado: el
    elegido (reutilizado o nuevo) recibe las lineas y el cerrado no se toca.

El unico predicado de «cerrado» vive aqui: `est != est_registro`.

DEPENDENCIA CON `porcentajes` (F-031 v5, R48): este fichero es COPIA
LITERAL en el repositorio `porcentajes`
(`services/dedicacion-transfer/application/services/`, su F-037), que
escribe en el MISMO parte de Sigrid y tiene que decidir igual; su
`tests/test_f037_copias_partes.py` lo compara byte a byte. Cambiarlo, aunque
sea un comentario, obliga a avisar a `porcentajes` EN EL MISMO TRABAJO para
que recopie y mueva su `COMMIT_COPIADO`. No entra en la lista cerrada de
copias de `CLAUDE.md`: la dependencia es entre repositorios.
"""
from __future__ import annotations

from domain.models.registro_models import ParteDestino, ParteSigrid

#: Prefijo del motivo de una linea que choca con un parte cerrado (R11).
MOTIVO_PARTE_CERRADO = "parte_cerrado"


def elegir_parte(ano: int, mes: int, partes: list[ParteSigrid], *,
                 est_registro: int) -> ParteDestino:
    """R2-R4: el parte que recibe las lineas del periodo."""
    del_periodo = sorted(partes, key=lambda p: p.ide, reverse=True)
    cerrados = [p.cod for p in del_periodo if p.est != est_registro]
    elegido = next((p for p in del_periodo if p.est == est_registro), None)
    destino = ParteDestino(ano=ano, mes=mes, cerrados=cerrados,
                           del_periodo=del_periodo,
                           complementario=bool(cerrados))
    if elegido is not None:
        destino.existe = True
        destino.ide = elegido.ide
        destino.cod = elegido.cod
        destino.estado = elegido.est
    return destino


def nombre_estado(est: int | None, *, est_cerrado: int,
                  est_imputado: int) -> str:
    """R7: nombre de un estado de parte para los textos (DA7)."""
    if est == est_cerrado:
        return "Cerrado"
    if est == est_imputado:
        return "Imputado"
    return f"estado {est}"


def aviso_de_parte(p: ParteDestino, nombres: dict[str, str]) -> str | None:
    """R18: texto para el modal cuando las lineas van a un complementario.

    `nombres` da el nombre del estado de cada parte cerrado por su codigo."""
    if not p.complementario:
        return None
    lista = ", ".join(f"{cod} ({nombres.get(cod, 'estado ?')})"
                      for cod in p.cerrados)
    sujeto = (f"el parte {lista} de {p.mes:02d}/{p.ano} esta cerrado"
              if len(p.cerrados) == 1 else
              f"los partes {lista} de {p.mes:02d}/{p.ano} estan cerrados")
    destino = "ya existe, en registro" if p.existe else "se creara"
    return (f"{sujeto}: las lineas van al parte complementario {p.cod} "
            f"({destino})")


def motivo_choque(cod: str | None, estado: str) -> str:
    """R11: motivo de `omitir` de una linea cuyas horas ya constan en un
    parte cerrado del periodo (sin nombres de personas, DA5)."""
    return (f"{MOTIVO_PARTE_CERRADO}: ya hay horas de ese recurso, dia y "
            f"tipo en el parte {cod} ({estado}); no se registran")
