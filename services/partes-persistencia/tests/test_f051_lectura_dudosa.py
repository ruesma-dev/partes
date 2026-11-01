# tests/test_f051_lectura_dudosa.py
"""F-051 · R13-R17: red de seguridad de sv3 sobre la lectura de sv2 (DA2 = C).

Caso real que lo motiva (obra 0686, fin de semana): en una tabla casi vacia
el modelo subio cada cifra una fila con confianza 95. sv3 casa bien por DNI,
asi que el error no se ve en el casado: hay que mirar la LECTURA.

Dos motivos de lectura dudosa, los dos puros sobre el payload de sv2:

  - `autocomprobacion_fila` (R13): una fila con horas cuyo
    `numero_linea_horas` (el "Nº" que el modelo leyo desde la cifra) no
    coincide con su `numero_linea`. Sin el campo no salta (R16).
  - `tabla_dispersa` (R14, interruptor `REVISAR_TABLA_DISPERSA`): alguna
    fila con horas y alguna fila con trabajador sin horas ni incidencia.

Con cualquiera de los dos, el parte va a revision con un WARNING sin
nombres ni DNIs (R15). Nada mas cambia (R17). Datos SINTETICOS.
"""
from __future__ import annotations

import inspect
import json
import logging

import pytest
from application.pipelines.persist_parte_pipeline import (
    PersistPartePipeline,
    PersistParteRequest,
)
from application.services.lectura_dudosa import (
    MOTIVO_AUTOCOMPROBACION,
    MOTIVO_TABLA_DISPERSA,
    detectar_lectura_dudosa,
)
from application.services.parte_normalizer import ParteNormalizer
from config.settings import Settings
from domain.models.parte_records import (
    EmpleadoMatch,
    MotivoLectura,
    ObraMatch,
    ParteDocumento,
    RegistroNormalizado,
    TipoHoraMatch,
)
from interface_adapters.api import app as modulo_app

NOMBRES = ["TRABAJADOR UNO", "TRABAJADOR DOS", "TRABAJADOR TRES",
           "TRABAJADOR CUATRO", "TRABAJADOR CINCO"]
DNIS = ["11111111H", "22222222J", "33333333P", "44444444A", "55555555K"]


def _fila(n: int, *, ord_=None, extra=None, auto="ausente", incidencia=None,
          nombre: bool = True, dni: bool = True) -> dict:
    """Fila de `empleados[]` tal como la manda sv2 (sintetica)."""
    fila: dict = {
        "numero_linea": n,
        "nombre": NOMBRES[(n - 1) % 5] if nombre else None,
        "dni": DNIS[(n - 1) % 5] if dni else None,
        "horas_ordinarias": ord_,
        "horas_extraordinarias": extra,
        "incidencia": incidencia,
        "partidas": [],
    }
    if auto != "ausente":
        fila["numero_linea_horas"] = auto
    return fila


def _motivos(empleados, *, tabla_dispersa=True) -> dict[str, tuple]:
    return {m.motivo: m.filas
            for m in detectar_lectura_dudosa(empleados, tabla_dispersa=tabla_dispersa)}


# Caso 17/10 tal como lo leyo el modelo (cifras subidas una fila) y tal como
# es en el papel. En los dos hay filas con trabajador y sin horas.
CASO_17_LEIDO = [_fila(1, extra=12), _fila(2, extra=10), _fila(3), _fila(4), _fila(5)]
CASO_17_PAPEL = [_fila(1), _fila(2, extra=12), _fila(3, extra=10), _fila(4), _fila(5)]
# Un laborable con la tabla llena y la autocomprobacion coherente.
LLENO = [_fila(n, ord_=8, auto=n) for n in range(1, 6)]


# ============================ R13 · autocomprobacion ===================== #

def test_f051_r13_fila_con_horas_y_autocomprobacion_distinta_es_dudosa() -> None:
    motivos = detectar_lectura_dudosa(
        [_fila(1, extra=12, auto=2)], tabla_dispersa=False)
    assert motivos == [MotivoLectura(motivo="autocomprobacion_fila", filas=(1,))]
    assert MOTIVO_AUTOCOMPROBACION == "autocomprobacion_fila"


def test_f051_r13_tambien_con_horas_ordinarias() -> None:
    assert _motivos([_fila(4, ord_=8, auto=3)], tabla_dispersa=False) == {
        MOTIVO_AUTOCOMPROBACION: (4,)}


def test_f051_r13_extra_negativa_cuenta_como_horas() -> None:
    assert _motivos([_fila(2, extra=-1.5, auto=1)], tabla_dispersa=False) == {
        MOTIVO_AUTOCOMPROBACION: (2,)}


def test_f051_r13_varias_filas_ordenadas_y_un_solo_motivo() -> None:
    motivos = detectar_lectura_dudosa(
        [_fila(3, ord_=8, auto=2), _fila(1, extra=12, auto=2),
         _fila(2, ord_=8, auto=2)],
        tabla_dispersa=False)
    assert motivos == [MotivoLectura(MOTIVO_AUTOCOMPROBACION, (1, 3))]


def test_f051_r13_autocomprobacion_coherente_no_es_dudosa() -> None:
    assert _motivos(LLENO) == {}


@pytest.mark.parametrize("ord_,extra", [(0, None), (None, None), (0, 0), ("", None)])
def test_f051_r13_sin_horas_el_desajuste_no_cuenta(ord_, extra) -> None:
    assert _motivos([_fila(1, ord_=ord_, extra=extra, auto=2)],
                    tabla_dispersa=False) == {}


def test_f051_r13_sin_numero_linea_no_hay_con_que_comparar() -> None:
    fila = _fila(1, extra=12, auto=2)
    fila["numero_linea"] = None
    assert _motivos([fila], tabla_dispersa=False) == {}


def test_f051_r13_valores_como_texto_se_interpretan() -> None:
    fila = _fila(1, extra="12,5", auto="2")
    fila["numero_linea"] = "1"
    assert _motivos([fila], tabla_dispersa=False) == {MOTIVO_AUTOCOMPROBACION: (1,)}


def test_f051_r13_valores_ilegibles_no_disparan_nada() -> None:
    assert _motivos([_fila(1, extra="doce", auto=2)], tabla_dispersa=False) == {}
    assert _motivos([_fila(1, extra=12, auto="dos")], tabla_dispersa=False) == {}
    assert _motivos([_fila(1, extra=12, auto=[2])], tabla_dispersa=False) == {}


# ============================ R16 · sin el campo ========================= #

@pytest.mark.parametrize("auto", ["ausente", None, ""])
def test_f051_r16_sin_numero_linea_horas_no_salta(auto) -> None:
    assert _motivos([_fila(1, extra=12, auto=auto)], tabla_dispersa=False) == {}


# ============================ R14 · tabla dispersa ======================= #

def test_f051_r14_caso_17_tal_como_lo_leyo_el_modelo() -> None:
    assert _motivos(CASO_17_LEIDO) == {MOTIVO_TABLA_DISPERSA: (3, 4, 5)}
    assert MOTIVO_TABLA_DISPERSA == "tabla_dispersa"


def test_f051_r14_caso_17_tal_como_es_en_el_papel() -> None:
    assert _motivos(CASO_17_PAPEL) == {MOTIVO_TABLA_DISPERSA: (1, 4, 5)}


def test_f051_r14_fila_con_incidencia_y_sin_horas_no_cuenta_como_vacia() -> None:
    empleados = [_fila(1, ord_=8), _fila(2, incidencia={"codigo": "V"}),
                 _fila(3, incidencia={"codigo": None, "texto_leido": "vacaciones"})]
    assert _motivos(empleados) == {}


def test_f051_r14_incidencia_sin_codigo_ni_texto_no_es_incidencia() -> None:
    empleados = [_fila(1, ord_=8),
                 _fila(2, incidencia={"codigo": None, "texto_leido": " "}),
                 _fila(3, incidencia="V")]
    assert _motivos(empleados) == {MOTIVO_TABLA_DISPERSA: (2, 3)}


@pytest.mark.parametrize("nombre,dni", [(True, False), (False, True)])
def test_f051_r14_trabajador_es_nombre_o_dni(nombre, dni) -> None:
    empleados = [_fila(1, ord_=8), _fila(2, nombre=nombre, dni=dni)]
    assert _motivos(empleados) == {MOTIVO_TABLA_DISPERSA: (2,)}


def test_f051_r14_fila_sin_trabajador_ni_horas_no_cuenta() -> None:
    empleados = [_fila(1, ord_=8), _fila(2, nombre=False, dni=False)]
    empleados[1]["nombre"] = "  "
    assert _motivos(empleados) == {}


def test_f051_r14_tabla_llena_no_es_dispersa() -> None:
    assert _motivos([_fila(n, ord_=8) for n in range(1, 6)]) == {}


def test_f051_r14_sin_ninguna_fila_con_horas_no_es_dispersa() -> None:
    assert _motivos([_fila(1), _fila(2), _fila(3, ord_=0)]) == {}


def test_f051_r14_una_fila_cero_se_ordena_antes_que_la_uno() -> None:
    """Mutacion: la clave de orden no puede confundir la fila 0 con la 1."""
    assert _motivos([_fila(2, ord_=8), _fila(1), _fila(0)]) == {
        MOTIVO_TABLA_DISPERSA: (0, 1)}


def test_f051_r15_el_motivo_es_inmutable_y_hashable() -> None:
    """Mutacion: `MotivoLectura` es un valor (frozen), no un registro editable."""
    motivo = MotivoLectura(MOTIVO_TABLA_DISPERSA, (1,))
    with pytest.raises(AttributeError):
        motivo.filas = (2,)  # type: ignore[misc]
    assert len({motivo, MotivoLectura(MOTIVO_TABLA_DISPERSA, (1,))}) == 1


def test_f051_r14_fila_vacia_sin_numero_linea_va_al_final() -> None:
    sin_numero = _fila(2)
    sin_numero["numero_linea"] = None
    assert _motivos([_fila(1, ord_=8), sin_numero, _fila(3)]) == {
        MOTIVO_TABLA_DISPERSA: (3, None)}


def test_f051_r14_con_el_interruptor_apagado_no_hay_tabla_dispersa() -> None:
    assert _motivos(CASO_17_LEIDO, tabla_dispersa=False) == {}


def test_f051_r13_r14_los_dos_motivos_a_la_vez() -> None:
    empleados = [_fila(1, extra=12, auto=2), _fila(2), _fila(3)]
    motivos = detectar_lectura_dudosa(empleados, tabla_dispersa=True)
    assert motivos == [MotivoLectura(MOTIVO_AUTOCOMPROBACION, (1,)),
                       MotivoLectura(MOTIVO_TABLA_DISPERSA, (2, 3))]


def test_f051_r17_entradas_que_no_son_filas_se_ignoran() -> None:
    assert detectar_lectura_dudosa([], tabla_dispersa=True) == []
    assert _motivos([None, "fila", 3, _fila(1, ord_=8, auto=1)]) == {}


# ======================= R15 · normalizer y WARNING ====================== #

def _datos(empleados) -> dict:
    return {"cabecera": {"fecha": "17/10/2026", "obra_numero": "0999"},
            "firma": {"firmado": True}, "empleados": empleados}


def _normalizar(empleados, **kw) -> ParteDocumento:
    return ParteNormalizer(**kw).normalize(_datos(empleados),
                                           email_text="octubre 2026")


def test_f051_r15_el_normalizer_anota_la_lectura_dudosa_y_avisa(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        parte = _normalizar(CASO_17_LEIDO)
    assert parte.lectura_dudosa == [MotivoLectura(MOTIVO_TABLA_DISPERSA, (3, 4, 5))]
    avisos = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(avisos) == 1
    texto = avisos[0].getMessage()
    assert "tabla_dispersa" in texto and "3, 4, 5" in texto
    for dato_personal in NOMBRES + DNIS:
        assert dato_personal not in caplog.text


def test_f051_r15_el_aviso_lleva_los_dos_motivos(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        parte = _normalizar([_fila(1, extra=12, auto=2), _fila(2)])
    assert [m.motivo for m in parte.lectura_dudosa] == [
        MOTIVO_AUTOCOMPROBACION, MOTIVO_TABLA_DISPERSA]
    assert "autocomprobacion_fila" in caplog.text
    assert "tabla_dispersa" in caplog.text


def test_f051_r15_sin_lectura_dudosa_no_hay_aviso(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        parte = _normalizar(LLENO)
    assert parte.lectura_dudosa == []
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]


def test_f051_r14_el_normalizer_respeta_el_interruptor() -> None:
    assert _normalizar(CASO_17_LEIDO, revisar_tabla_dispersa=False).lectura_dudosa == []
    assert _normalizar(CASO_17_LEIDO).lectura_dudosa != []


def test_f051_r16_parte_anterior_sin_la_clave_por_defecto_vacio() -> None:
    assert ParteDocumento().lectura_dudosa == []
    sin_clave = [_fila(n, ord_=8) for n in range(1, 4)]
    assert _normalizar(sin_clave).lectura_dudosa == []


def test_f051_r17_los_registros_no_cambian() -> None:
    """La lectura dudosa solo anota: cifras, filas y registros, igual."""
    con = _normalizar([_fila(1, extra=12, auto=2), _fila(2), _fila(3, ord_=8, auto=3)])
    sin = _normalizar([_fila(1, extra=12), _fila(2), _fila(3, ord_=8)],
                      revisar_tabla_dispersa=False)
    assert con.lectura_dudosa and not sin.lectura_dudosa
    assert con.registros == sin.registros


# ===================== R15 / R17 · review_required ======================= #

def _parte_casado(lectura_dudosa=()) -> ParteDocumento:
    """Un parte que hoy NO va a revision: firmado, obra y trabajador casados."""
    registro = RegistroNormalizado(
        line_index=0, empleado_line_no=1, tipo_hora="normal", horas=8.0,
        empleado=EmpleadoMatch(ide=1, method="dni"),
        hora=TipoHoraMatch(ide=1, codigo="HL01"))
    return ParteDocumento(
        firmado=True, fecha_int=20261017, obra=ObraMatch(ide=1, method="codigo"),
        registros=[registro], lectura_dudosa=list(lectura_dudosa))


def test_f051_r15_lectura_dudosa_sube_review_required() -> None:
    for motivo in (MOTIVO_AUTOCOMPROBACION, MOTIVO_TABLA_DISPERSA):
        parte = _parte_casado([MotivoLectura(motivo, (1,))])
        assert PersistPartePipeline._compute_review_required(parte) is True


def test_f051_r17_sin_lectura_dudosa_review_required_como_hoy() -> None:
    assert PersistPartePipeline._compute_review_required(_parte_casado()) is False
    sin_firma = _parte_casado()
    sin_firma.firmado = False
    assert PersistPartePipeline._compute_review_required(sin_firma) is True
    sin_registros = _parte_casado()
    sin_registros.registros = []
    assert PersistPartePipeline._compute_review_required(sin_registros) is True


class _Repo:
    def __init__(self) -> None:
        self.guardados: list[dict] = []

    def get_by_sha256(self, _sha):
        return None

    def save_parte(self, **kwargs) -> None:
        self.guardados.append(kwargs)


def _ingerir(empleados, monkeypatch) -> dict:
    """Ingesta completa con un casado de mentira que lo casa todo."""
    repo = _Repo()
    pipeline = PersistPartePipeline(repository=repo, normalizer=ParteNormalizer(),
                                    matcher_provider=object())  # type: ignore[arg-type]

    def _casar_todo(parte: ParteDocumento) -> None:
        parte.obra = ObraMatch(ide=1, method="codigo")
        for reg in parte.registros:
            reg.empleado = EmpleadoMatch(ide=reg.empleado_line_no, method="dni")
            reg.hora = TipoHoraMatch(ide=1)

    monkeypatch.setattr(pipeline, "_match", _casar_todo)
    pipeline.run(PersistParteRequest(
        filename="p.pdf", mime_type="application/pdf", file_bytes=b"",
        extraction_envelope={"meta": {}, "data": _datos(empleados)},
        context={"document": {"sha256": "sha-f051"}}))
    return repo.guardados[0]


def test_f051_r15_la_ingesta_guarda_el_parte_disperso_para_revisar(monkeypatch) -> None:
    guardado = _ingerir(CASO_17_LEIDO, monkeypatch)
    assert guardado["review_required"] is True
    # El campo de sv2 viaja intacto en el JSON crudo (sin columna nueva).
    crudo = json.loads(guardado["raw_extraction_json"])
    assert crudo["data"]["empleados"][0] == CASO_17_LEIDO[0]


def test_f051_r15_la_ingesta_marca_la_autocomprobacion_incoherente(monkeypatch) -> None:
    lleno_con_error = [_fila(n, ord_=8, auto=n) for n in range(1, 5)]
    lleno_con_error[0]["numero_linea_horas"] = 2
    assert _ingerir(lleno_con_error, monkeypatch)["review_required"] is True


def test_f051_r17_la_ingesta_de_un_parte_lleno_y_coherente_no_va_a_revision(monkeypatch) -> None:
    assert _ingerir(LLENO, monkeypatch)["review_required"] is False


# ======================== interruptor y cableado ========================= #

@pytest.fixture
def entorno(monkeypatch):
    monkeypatch.setenv("PG_PASSWORD", "irrelevante-en-tests")
    monkeypatch.setenv("PG_ADMIN_PASSWORD", "irrelevante-en-tests")
    monkeypatch.delenv("REVISAR_TABLA_DISPERSA", raising=False)
    return monkeypatch


def test_f051_r14_interruptor_encendido_por_defecto(entorno) -> None:
    assert Settings(_env_file=None).revisar_tabla_dispersa is True


def test_f051_r14_interruptor_se_apaga_por_entorno(entorno) -> None:
    entorno.setenv("REVISAR_TABLA_DISPERSA", "false")
    assert Settings(_env_file=None).revisar_tabla_dispersa is False


def test_f051_r14_build_app_pasa_el_interruptor_al_normalizer() -> None:
    fuente = inspect.getsource(modulo_app.build_app)
    assert "revisar_tabla_dispersa=settings.revisar_tabla_dispersa" in fuente
