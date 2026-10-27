# tests/test_f056_pipeline.py
"""F-056 · `FranquiciaPipeline` de sv5 (R22-R33) y
`RegistroPipeline.asegurar_parte`.

Contra `SigridFake` (tests/dobles.py), que evalua el `INSERT` con la guarda
de parte abierto, el `UPDATE` optimista (`actualizar`) y el alta protegida
del parte. Recorre el guion de M2 (design §10): crear, repetir, recalcular
al alza, a 0 sin borrar; y los rechazos (parte cerrado, enlazada, sin
`HE*`, recurso de otra empresa), la relectura, el modo pruebas y el lock.

Sin red ni Sigrid. Recursos, partes, obras e ides SINTETICOS.
"""
from __future__ import annotations

import logging
import threading

import pytest

from application.pipelines.franquicia_pipeline import FranquiciaPipeline
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services import franquicia as fr
from domain.models.registro_models import (
    HoraRecurso,
    LineaEntrada,
    ObraEntrada,
    ParteDestino,
    PeticionFranquicia,
    RecursoSigrid,
)
from tests.dobles import SettingsFake, SigridFake

REC = 501
HL, HE = 1, 2
OBRA, OBRA_PRUEBAS = 10, 404
HMO, HMO_PRUEBAS = 900, 940
DIA = 20261015
SK = "partes:franquicia:5"
OPS_PERMITIDAS = {"insert", "actualizar", "crear_parte"}


class LockEspia:
    """Un lock que cuenta cuantas veces se toma (y se puede vigilar)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.tomas = 0

    def __enter__(self):
        self._lock.acquire()
        self.tomas += 1
        return self

    def __exit__(self, *exc):
        self._lock.release()

    def locked(self) -> bool:
        return self._lock.locked()


def _obra(ide=OBRA, cod="0100") -> ObraEntrada:
    o = ObraEntrada(ide=ide, codigo=cod, nombre=f"Obra {cod}", empresa=1)
    o.cenide = 77
    return o


def _parte(ide=HMO, cod="PT26/00314", est=1, obride=OBRA, mes=10) -> dict:
    return {"ide": ide, "obride": obride, "ano": 2026, "mes": mes,
            "cod": cod, "emp": 1, "est": est}


def _extra(ide, fec, can, *, horide=HE, hmoide=HMO, synckey=None) -> dict:
    return {"ide": ide, "hmoide": hmoide, "reside": REC, "fec": fec,
            "horide": horide, "hora_codigo": None, "can": can, "pre": 25.0,
            "tot": round(can * 25.0, 2), "pos": 64, "synckey": synckey,
            "caaide": 0, "paride": 33, "tex": "", "enlazada": False}


def _cli(lineas=None, partes=None, horas=None, **kw) -> SigridFake:
    return SigridFake(
        obras={"0100": _obra(), "0404": _obra(OBRA_PRUEBAS, "0404")},
        horas=horas if horas is not None else {REC: [
            HoraRecurso(HL, "HL01", None, 15.0, defecto=True),
            HoraRecurso(HE, "HE01", None, 25.0)]},
        partes=partes if partes is not None else [_parte()],
        lineas=lineas if lineas is not None else [
            _extra(7001, 20261001, 3.0, synckey="partes:11"),
            _extra(7002, 20261008, 3.0, synckey="partes:12")],
        **kw)


def _pipe(cli, *, pruebas=False):
    st = SettingsFake(obra_pruebas_forzar=pruebas)
    lock = LockEspia()
    reg = RegistroPipeline(cliente=cli, settings=st, lock=lock)
    return FranquiciaPipeline(cliente=cli, settings=st, registro=reg), lock


def _pet(ajuste_id=5, franquicia=8.0, pendientes=0.0, obra=None,
         fecha=DIA) -> PeticionFranquicia:
    return PeticionFranquicia(
        ajuste_id=ajuste_id, recurso_ide=REC, franquicia=franquicia,
        periodo="2026-10", inicio=20260916, fin=20261015, fecha_int=fecha,
        obra=obra or ObraEntrada(ide=OBRA, codigo="0100"), partida_ide=33,
        partida_cod="01.01", extras_pendientes=pendientes,
        usuario="usuario-de-prueba")


def _ajuste(cli):
    return [l for l in cli.lineas if l.get("synckey") == SK]


def _ops(cli) -> set[str]:
    return {s["op"] for s in cli.grabadas}


@pytest.fixture(autouse=True)
def _grabar(monkeypatch):
    """Cada sentencia que llega a `escribir` queda en `cli.grabadas`. [E]
    R26: al terminar CADA test, ninguna es un borrado (solo `INSERT`,
    `UPDATE` y el alta del parte)."""
    original = SigridFake.escribir
    todas: list[dict] = []

    def escribir(self, statements):
        self.__dict__.setdefault("grabadas", []).extend(statements)
        todas.extend(statements)
        return original(self, statements)

    monkeypatch.setattr(SigridFake, "escribir", escribir)
    yield
    assert {s["op"] for s in todas} <= OPS_PERMITIDAS


# --------------------------------- comprobar -------------------------------- #

def test_f056_r22_comprobar_crear_sin_escribir_ni_lock():
    cli = _cli()
    pipe, lock = _pipe(cli)
    r = pipe.comprobar(_pet())
    assert (r.ok, r.accion, r.extras, r.objetivo, r.actual) == (
        True, fr.CREAR, 6.0, -6.0, None)
    assert (r.hora_codigo, r.pre, r.escrita) == ("HE01", 25.0, False)
    assert (r.parte_cod, r.parte_estado, r.complementario) == (
        "PT26/00314", 1, False)
    assert r.forzada_pruebas is False and r.error is None
    assert "escribir" not in cli.llamadas
    assert lock.tomas == 0
    assert cli.extras_leidas == [(REC, 20260916, 20261015, SK)]


def test_f056_r23_comprobar_suma_extras_pendientes():
    r = _pipe(_cli())[0].comprobar(_pet(pendientes=4.0))
    assert (r.extras, r.objetivo) == (6.0, -8.0)


def test_f056_r23_ejecutar_ignora_extras_pendientes():
    cli = _cli()
    r = _pipe(cli)[0].ejecutar(_pet(pendientes=4.0))
    assert (r.extras, r.objetivo) == (6.0, -6.0)
    assert _ajuste(cli)[0]["can"] == -6.0


def test_f056_r22_comprobar_centinela_no_busca_la_linea():
    cli = _cli()
    r = _pipe(cli)[0].comprobar(_pet(ajuste_id=0))
    assert (r.ok, r.accion, r.objetivo) == (True, fr.CREAR, -6.0)
    assert "lineas_para_reajuste" not in cli.llamadas


def test_f056_r22_ejecutar_con_centinela_es_error():
    with pytest.raises(ValueError, match="ajuste_id"):
        _pipe(_cli())[0].ejecutar(_pet(ajuste_id=0))


def test_f056_r22_comprobar_con_linea_existente_trae_actual_y_su_parte():
    cli = _cli(lineas=[_extra(7001, 20261001, 10.0),
                       _extra(7009, DIA, -6.0, synckey=SK)])
    r = _pipe(cli)[0].comprobar(_pet())
    assert (r.accion, r.extras, r.objetivo, r.actual) == (
        fr.ACTUALIZAR, 10.0, -8.0, -6.0)
    assert (r.hmores_ide, r.hmoide, r.parte_cod, r.parte_estado) == (
        7009, HMO, "PT26/00314", 1)
    assert _ajuste(cli)[0]["can"] == -6.0       # comprobar no escribe


# ----------------------------- ejecutar: guion M2 ---------------------------- #

def test_f056_r24_ejecutar_crea_la_linea_de_ajuste():
    cli = _cli()
    cli.cuentas = [(77, 1, 702, "0100.EXT")]
    cli.horas[REC][1].caa_cod = "00000.EXT"
    pipe, lock = _pipe(cli)
    cli.vigilar_lock(lock)
    r = pipe.ejecutar(_pet())
    assert (r.ok, r.accion, r.escrita, r.objetivo, r.actual) == (
        True, fr.CREAR, True, -6.0, -6.0)
    [linea] = _ajuste(cli)
    assert r.hmores_ide == linea["ide"] and r.hmoide == HMO
    assert r.parte_cod == "PT26/00314"
    assert {k: linea[k] for k in ("hmoide", "reside", "fec", "horide", "can",
                                  "pre", "tot", "paride", "ano", "mes",
                                  "caaide", "tex")} == {
        "hmoide": HMO, "reside": REC, "fec": DIA, "horide": HE,
        "can": -6.0, "pre": 25.0, "tot": -150.0, "paride": 33, "ano": 2026,
        "mes": 10, "caaide": 702,
        "tex": "Ajuste franquicia extras 2026-10: -6 h (franquicia 8 h)"}
    assert linea["pos"] == 64 + 64
    assert _ops(cli) == {"insert"}
    assert lock.tomas == 1


def test_f056_r28_repetir_es_ya_aplicado_sin_escribir():
    cli = _cli()
    pipe, _lock = _pipe(cli)
    pipe.ejecutar(_pet())
    n = len(cli.grabadas)
    r = pipe.ejecutar(_pet())
    assert (r.ok, r.accion, r.escrita, r.actual) == (
        True, fr.YA_APLICADO, False, -6.0)
    assert len(cli.grabadas) == n
    assert len(_ajuste(cli)) == 1


def test_f056_r25_r31_otra_extra_el_dia_de_ajuste_y_recalcular():
    """M2 (e)-(f): la extra de 4 h del dia de ajuste no choca con el
    ajuste (R31) y recalcular lo lleva a -8 con un UPDATE."""
    cli = _cli()
    pipe, _lock = _pipe(cli)
    pipe.ejecutar(_pet())
    reg = pipe._reg
    res = reg.ejecutar(obra=_obra(), lineas=[LineaEntrada(
        registro_id=13, fecha_int=DIA, recurso_ide=REC, tipo_hora="extra",
        horas=4.0, hora_ide=HE, hora_codigo="HE01", partida_ide=33)])
    assert [e["registro_id"] for e in res.escritas] == [13]
    assert res.pendientes_confirmacion == []
    r = pipe.ejecutar(_pet())
    assert (r.ok, r.accion, r.extras, r.objetivo, r.actual) == (
        True, fr.ACTUALIZAR, 10.0, -8.0, -8.0)
    [linea] = _ajuste(cli)
    assert (linea["can"], linea["tot"]) == (-8.0, -200.0)
    assert _ops(cli) == {"insert", "actualizar"}


def test_f056_r19_r25_franquicia_cero_deja_la_linea_a_cero_sin_borrar():
    cli = _cli()
    pipe, _lock = _pipe(cli)
    pipe.ejecutar(_pet())
    r = pipe.ejecutar(_pet(franquicia=0.0))
    assert (r.ok, r.accion, r.objetivo, r.actual) == (
        True, fr.ACTUALIZAR, 0.0, 0.0)
    [linea] = _ajuste(cli)
    assert (linea["can"], linea["tot"]) == (0.0, 0.0)
    assert _ops(cli) <= OPS_PERMITIDAS


def test_f056_r28_sin_linea_y_sin_extras_es_sin_ajuste():
    cli = _cli(lineas=[])
    r = _pipe(cli)[0].ejecutar(_pet())
    assert (r.ok, r.accion, r.escrita, r.extras, r.objetivo) == (
        True, fr.SIN_AJUSTE, False, 0.0, 0.0)
    assert cli.__dict__.get("grabadas", []) == []


def test_f056_r24_sin_parte_en_registro_lo_da_de_alta():
    cli = _cli(partes=[_parte(est=3, cod="PT26/00300")],
               alta_protegida=True)
    pipe, lock = _pipe(cli)
    cli.vigilar_lock(lock)
    r = pipe.ejecutar(_pet())
    assert (r.ok, r.accion, r.complementario) == (True, fr.CREAR, True)
    nuevo = [p for p in cli.partes if p["cod"] != "PT26/00300"]
    assert [p.get("est", 1) for p in nuevo] == [1]
    assert r.hmoide == nuevo[0]["ide"] and r.parte_cod == nuevo[0]["cod"]
    assert _ajuste(cli)[0]["hmoide"] == nuevo[0]["ide"]
    assert [s["op"] for s in cli.grabadas] == ["crear_parte", "insert"]
    assert cli.grabadas[0]["desc"] == "Parte Obra 0100"


# ------------------------------ rechazos (R27, R30) -------------------------- #

def test_f056_r27_linea_en_parte_cerrado_no_se_escribe():
    cli = _cli(partes=[_parte(est=3), _parte(ide=901, cod="PT26/00320")],
               lineas=[_extra(7001, 20261001, 10.0),
                       _extra(7009, DIA, -6.0, synckey=SK)])
    r = _pipe(cli)[0].ejecutar(_pet())
    assert (r.ok, r.accion, r.escrita) == (False, fr.NO_EDITABLE, False)
    assert r.motivo.startswith("parte_no_abierto: ")
    assert r.error == r.motivo
    assert cli.__dict__.get("grabadas", []) == []


def test_f056_r27_linea_enlazada_no_se_escribe():
    ajuste = _extra(7009, DIA, -6.0, synckey=SK)
    ajuste["enlazada"] = True
    cli = _cli(lineas=[_extra(7001, 20261001, 10.0), ajuste])
    r = _pipe(cli)[0].ejecutar(_pet())
    assert (r.ok, r.accion) == (False, fr.NO_EDITABLE)
    assert r.motivo.startswith("linea_enlazada: ")
    assert cli.__dict__.get("grabadas", []) == []


def test_f056_r30_recurso_sin_he_no_es_editable():
    cli = _cli(horas={REC: [HoraRecurso(HL, "HL01", None, 15.0,
                                        defecto=True)]})
    pipe, _lock = _pipe(cli)
    for r in (pipe.comprobar(_pet()), pipe.ejecutar(_pet())):
        assert (r.ok, r.accion) == (False, fr.NO_EDITABLE)
        assert r.motivo.startswith(fr.MOTIVO_NO_REGISTRABLE)
    assert cli.__dict__.get("grabadas", []) == []


def test_f056_r30_recurso_de_otra_empresa_no_es_editable():
    cli = _cli(recursos={REC: RecursoSigrid(REC, 2, None, None)})
    r = _pipe(cli)[0].ejecutar(_pet())
    assert (r.ok, r.accion) == (False, fr.NO_EDITABLE)
    assert "empresa" in r.motivo
    assert cli.__dict__.get("grabadas", []) == []


# ------------------------------ relectura (R29) ------------------------------ #

def test_f056_r29_si_la_guarda_no_deja_escribir_ok_false():
    """El parte se cierra entre la lectura y la escritura: la guarda deja
    el INSERT a 0 filas y la relectura no la encuentra."""
    cli = _cli()
    cli.cerrar_al_escribir = {HMO: 3}
    r = _pipe(cli)[0].ejecutar(_pet())
    assert (r.ok, r.accion, r.escrita) == (False, fr.CREAR, False)
    assert r.motivo and "no confirmo" in r.motivo
    assert _ajuste(cli) == []


def test_f056_r29_fallo_de_escritura_que_si_entro_es_ok(monkeypatch):
    cli = _cli()
    original = cli.escribir

    def escribir_y_fallar(statements):
        original(statements)
        raise RuntimeError("timeout de sigrid-api")

    monkeypatch.setattr(cli, "escribir", escribir_y_fallar)
    r = _pipe(cli)[0].ejecutar(_pet())
    assert (r.ok, r.escrita, r.actual) == (True, True, -6.0)


def test_f056_r29_fallo_de_escritura_sin_nada_escrito_es_ok_false(
        monkeypatch):
    cli = _cli()

    def falla(statements):
        raise RuntimeError("sigrid-api write HTTP 500")

    monkeypatch.setattr(cli, "escribir", falla)
    r = _pipe(cli)[0].ejecutar(_pet())
    assert (r.ok, r.escrita) == (False, False)
    assert "HTTP 500" in r.error


def test_f056_r29_actualizar_que_no_entra_ok_false(monkeypatch):
    """El `UPDATE` optimista no encuentra la fila como se leyo."""
    cli = _cli(lineas=[_extra(7001, 20261001, 10.0),
                       _extra(7009, DIA, -6.0, synckey=SK)])
    original = cli.escribir

    def tocar_antes(statements):
        _ajuste(cli)[0]["can"] = -5.0         # Administracion la toca
        return original(statements)

    monkeypatch.setattr(cli, "escribir", tocar_antes)
    r = _pipe(cli)[0].ejecutar(_pet())
    assert (r.ok, r.accion, r.escrita, r.actual) == (
        False, fr.ACTUALIZAR, False, -5.0)


def test_f056_r23_fallo_leyendo_extras_propaga():
    cli = _cli()
    cli.fallo_extras = RuntimeError("sigrid caido")
    with pytest.raises(RuntimeError, match="sigrid caido"):
        _pipe(cli)[0].ejecutar(_pet())


# --------------------------- modo pruebas (R32) --------------------------- #

def test_f056_r32_modo_pruebas_va_a_la_obra_de_pruebas_con_la_marca():
    cli = _cli(partes=[_parte(), _parte(HMO_PRUEBAS, "PT26/09404",
                                        obride=OBRA_PRUEBAS)])
    r = _pipe(cli, pruebas=True)[0].ejecutar(_pet())
    assert (r.ok, r.forzada_pruebas, r.hmoide) == (True, True, HMO_PRUEBAS)
    [linea] = _ajuste(cli)
    assert (linea["hmoide"], linea["tex"]) == (HMO_PRUEBAS, "PRUEBA-IA")


def test_f056_r32_modo_pruebas_alta_del_parte_con_marca():
    cli = _cli(partes=[_parte()], alta_protegida=True)
    _pipe(cli, pruebas=True)[0].ejecutar(_pet())
    assert cli.grabadas[0]["op"] == "crear_parte"
    assert cli.grabadas[0]["obride"] == OBRA_PRUEBAS
    assert cli.grabadas[0]["desc"] == "Parte Obra 0404 (PRUEBA-IA)"


# ----------------------------- lock y logs (R22, R33) ------------------------ #

def test_f056_r22_lock_es_el_del_registro():
    cli = _cli()
    pipe, lock = _pipe(cli)
    assert pipe.lock is lock is pipe._reg.lock


def test_f056_r22_preparar_fuera_del_lock_y_escritura_dentro():
    cli = _cli()
    cli.cuentas = [(77, 1, 702, "0100.EXT")]
    cli.horas[REC][1].caa_cod = "00000.EXT"
    pipe, lock = _pipe(cli)
    cli.vigilar_lock(lock)          # lecturas de estado y escritura: dentro
    pipe.ejecutar(_pet())
    # Las lecturas de datos maestros (cuentas) se hacen sin el lock.
    assert [c["bajo_lock"] for c in cli.cuentas_leidas] == [False]
    assert _ajuste(cli)[0]["caaide"] == 702


def test_f056_r33_logs_con_ids_y_horas_sin_nombres(caplog):
    cli = _cli()
    with caplog.at_level(logging.INFO):
        _pipe(cli)[0].ejecutar(_pet())
    msgs = [r.getMessage() for r in caplog.records
            if r.name.endswith("franquicia_pipeline")]
    assert any("ajuste=5" in m and "recurso=501" in m and "objetivo=-6.00"
               in m and "usuario=usuario-de-prueba" in m for m in msgs)
    assert not any("Obra 0100" in m for m in msgs)


# --------------------------- asegurar_parte (T5) --------------------------- #

def test_f056_asegurar_parte_delega_en_el_alta_protegida():
    cli = _cli(partes=[], alta_protegida=True)
    pipe, lock = _pipe(cli)
    p = ParteDestino(ano=2026, mes=10, cod="PT26/00001")
    with lock:
        pipe._reg.asegurar_parte(p, _obra())
    assert (p.existe, p.creado, p.cod) == (True, True, "PT26/00001")
    assert cli.altas == [{"cod": "PT26/00001", "obride": OBRA, "ano": 2026,
                          "mes": 10, "insertado": True}]
    assert cli.grabadas[0]["desc"] == "Parte Obra 0100"
