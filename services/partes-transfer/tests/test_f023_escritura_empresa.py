# tests/test_f023_escritura_empresa.py
"""F-023 · R32-R37 y R4: sv5 escribe en la empresa de la obra y verifica.

sv5 es el ultimo punto antes de Sigrid. Hasta F-023 firmaba toda cabecera
con `SIGRID_EMPRESA=1`, numeraba `PT<AA>/NNNNN` mezclando empresas y
localizaba la cabecera recien creada solo por codigo y tipo (con un
correlativo por empresa, eso devuelve DOS filas). Ahora:

  - la cabecera lleva la empresa de la obra destino (R32), el correlativo
    se calcula en esa empresa (R33) y el `INSERT INTO hmo` la filtra (R34);
  - obra sin empresa, o codigo en varias empresas: no se escribe (R35);
  - cada recurso se VERIFICA (empresa, alta a la fecha de la linea y
    persona) antes de escribir (R36) y una linea sin recurso se resuelve
    por DNI solo con un unico candidato de esa empresa (R37);
  - `truncated: true` es una excepcion (R4).

Tres familias, por el nombre de los tests: `coherencia` (reglas puras),
`cliente` (SQL de `SigridWriteClient` con sigrid-api simulado) y
`pipeline` (preparar/registrar con el doble en memoria). Sin red. Datos
SINTETICOS.
"""
from __future__ import annotations

import pytest

from application.services.coherencia_recurso import (
    RecursoSigrid,
    de_alta,
    elegir_por_dni,
    verificar_recurso,
)
from application.services.reglas_registro import (
    MOTIVO_RECURSO_AMBIGUO,
    MOTIVO_RECURSO_BAJA,
    MOTIVO_RECURSO_NO_EXISTE,
    MOTIVO_RECURSO_OTRA_EMPRESA,
    MOTIVO_RECURSO_OTRA_PERSONA,
    MOTIVO_SIN_RECURSO_EMPRESA,
)

FECHA = 20260915
DNI = "12345678Z"


def _rec(reside=501, *, empresa=1, fecbaj=0, dni=DNI) -> RecursoSigrid:
    return RecursoSigrid(reside=reside, empresa=empresa, fecbaj=fecbaj,
                         dni=dni)


# ========================= coherencia · de_alta ========================= #

@pytest.mark.parametrize("fecbaj, esperado", [
    (None, True), (0, True), (FECHA + 1, True), (FECHA, False),
    (FECHA - 1, False),
])
def test_f023_r36_coherencia_de_alta(fecbaj, esperado) -> None:
    assert de_alta(fecbaj, FECHA) is esperado


# ====================== coherencia · R36 verificar ====================== #

def test_f023_r36_coherencia_recurso_correcto_no_da_motivo() -> None:
    assert verificar_recurso(_rec(), 1, FECHA, DNI) is None


def test_f023_r36_coherencia_otra_empresa() -> None:
    assert verificar_recurso(_rec(empresa=28), 1, FECHA, DNI) == \
        MOTIVO_RECURSO_OTRA_EMPRESA


def test_f023_r36_coherencia_recurso_sin_empresa_es_otra_empresa() -> None:
    assert verificar_recurso(_rec(empresa=None), 1, FECHA, DNI) == \
        MOTIVO_RECURSO_OTRA_EMPRESA


def test_f023_r36_coherencia_de_baja_a_la_fecha_de_la_linea() -> None:
    assert verificar_recurso(_rec(fecbaj=FECHA), 1, FECHA, DNI) == \
        MOTIVO_RECURSO_BAJA
    assert verificar_recurso(_rec(fecbaj=FECHA + 1), 1, FECHA, DNI) is None


def test_f023_r36_coherencia_la_empresa_se_comprueba_antes_que_la_baja() -> None:
    assert verificar_recurso(_rec(empresa=28, fecbaj=FECHA - 1), 1, FECHA,
                             DNI) == MOTIVO_RECURSO_OTRA_EMPRESA


def test_f023_r36_coherencia_dni_de_otra_persona() -> None:
    assert verificar_recurso(_rec(dni="87654321X"), 1, FECHA, DNI) == \
        MOTIVO_RECURSO_OTRA_PERSONA


def test_f023_r36_coherencia_recurso_sin_dni_con_linea_con_dni() -> None:
    """No se puede comprobar que sea de esa persona: no se escribe."""
    assert verificar_recurso(_rec(dni=None), 1, FECHA, DNI) == \
        MOTIVO_RECURSO_OTRA_PERSONA


def test_f023_r36_coherencia_el_dni_se_compara_normalizado() -> None:
    assert verificar_recurso(_rec(dni="12345678-z"), 1, FECHA,
                             " 12.345.678 Z ") is None


@pytest.mark.parametrize("dni_linea", [None, "", "  "])
def test_f023_r36_coherencia_linea_sin_dni_no_compara_persona(
        dni_linea) -> None:
    assert verificar_recurso(_rec(dni="87654321X"), 1, FECHA,
                             dni_linea) is None


def test_f023_r36_coherencia_recurso_inexistente() -> None:
    assert verificar_recurso(None, 1, FECHA, DNI) == MOTIVO_RECURSO_NO_EXISTE


def test_f023_r36_coherencia_los_motivos_dicen_que_fallo() -> None:
    """Cuatro motivos distintos, legibles para el portal."""
    motivos = {MOTIVO_RECURSO_NO_EXISTE, MOTIVO_RECURSO_OTRA_EMPRESA,
               MOTIVO_RECURSO_BAJA, MOTIVO_RECURSO_OTRA_PERSONA}
    assert len(motivos) == 4
    assert "empresa" in MOTIVO_RECURSO_OTRA_EMPRESA
    assert "baja" in MOTIVO_RECURSO_BAJA
    assert "DNI" in MOTIVO_RECURSO_OTRA_PERSONA


# ===================== coherencia · R37 por DNI ========================= #

def test_f023_r37_coherencia_un_unico_candidato() -> None:
    assert elegir_por_dni([_rec(501), _rec(502, empresa=28)], 1, FECHA) == \
        (501, None)


def test_f023_r37_coherencia_sin_candidatos() -> None:
    cands = [_rec(501, empresa=28), _rec(502, fecbaj=FECHA - 1)]
    assert elegir_por_dni(cands, 1, FECHA) == \
        (None, MOTIVO_SIN_RECURSO_EMPRESA)
    assert elegir_por_dni([], 1, FECHA) == (None, MOTIVO_SIN_RECURSO_EMPRESA)


def test_f023_r37_coherencia_varios_candidatos_es_ambiguo() -> None:
    assert elegir_por_dni([_rec(501), _rec(502)], 1, FECHA) == \
        (None, MOTIVO_RECURSO_AMBIGUO)


def test_f023_r37_coherencia_el_mismo_recurso_dos_veces_es_uno() -> None:
    """La lectura por DNI une `emp.dni` y `res.cif`: el mismo recurso puede
    llegar por los dos caminos."""
    assert elegir_por_dni([_rec(501), _rec(501)], 1, FECHA) == (501, None)


def test_f023_r37_coherencia_la_baja_a_la_fecha_de_la_linea() -> None:
    cands = [_rec(501, fecbaj=20260801), _rec(502, fecbaj=0)]
    assert elegir_por_dni(cands, 1, 20260731) == \
        (None, MOTIVO_RECURSO_AMBIGUO)
    assert elegir_por_dni(cands, 1, 20260801) == (502, None)
