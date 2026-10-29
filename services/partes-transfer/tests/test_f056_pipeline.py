# tests/test_f056_pipeline.py
"""F-056 · `FranquiciaPipeline` de sv5 (R22-R33) y
`RegistroPipeline.asegurar_parte`.

Contra `SigridFake` (tests/dobles.py), que evalua el `INSERT` con la guarda
de parte abierto, el `UPDATE` optimista (`actualizar`) y el alta protegida
del parte. Recorre el guion de M2 (design §10): crear, repetir, recalcular
al alza, a 0 sin borrar; y los rechazos (parte cerrado, enlazada, sin
`HE*`, recurso de otra empresa), la relectura, el modo pruebas y el lock.

Enmienda 2026-10-27 (T10, DA1 = C) y 2026-10-29 (T23, DA29-DA31): X ya no
llega en la peticion; el pipeline la lee del campo EXTENDIDO de recurso
(`defext` tip 33, `conext.valn`; `franquicias`, R1-R3, R38-R42, R47, R48)
con el `cod` del ajuste real (`10`).

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
    EstadoFranquicias,
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
#: `cod` del campo extendido «Franquicia Horas» (design §2 H7).
COD = "10"


def _def(ide=49, camtip=1) -> dict:
    """La definicion de `defext` del campo: tip 33 y ese `cod`."""
    return {"ide": ide, "tip": 33, "cod": COD, "camtip": camtip}


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
    """Por defecto la definicion existe (tip 33, `camtip` 1) y el recurso
    tiene X = 8 en `conext`."""
    cli = _sigrid(lineas, partes, horas, **kw)
    cli.defext = [_def()]
    cli.poner_franquicia(REC, 8, cod=COD)
    return cli


def _sigrid(lineas=None, partes=None, horas=None, **kw) -> SigridFake:
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


def _pipe(cli, *, pruebas=False, cod=COD):
    st = SettingsFake(obra_pruebas_forzar=pruebas,
                      franquicia_campo_ext=cod)
    lock = LockEspia()
    reg = RegistroPipeline(cliente=cli, settings=st, lock=lock)
    return FranquiciaPipeline(cliente=cli, settings=st, registro=reg), lock


def _pet(ajuste_id=5, pendientes=0.0, obra=None,
         fecha=DIA) -> PeticionFranquicia:
    return PeticionFranquicia(
        ajuste_id=ajuste_id, recurso_ide=REC,
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
    assert (r.franquicia, r.franquicia_estado) == (8.0, "activa")
    [linea] = _ajuste(cli)
    assert r.hmores_ide == linea["ide"] and r.hmoide == HMO
    assert r.parte_cod == "PT26/00314"
    assert {k: linea[k] for k in ("hmoide", "reside", "fec", "horide", "can",
                                  "pre", "tot", "paride", "ano", "mes",
                                  "caaide", "tex")} == {
        "hmoide": HMO, "reside": REC, "fec": DIA, "horide": HE,
        "can": -6.0, "pre": 25.0, "tot": -150.0, "paride": 33, "ano": 2026,
        "mes": 10, "caaide": 702,
        "tex": "Ajuste franquicia extras 2026-10"}
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
    cli.poner_franquicia(REC, 0, cod=COD)  # Administracion la quita
    r = pipe.ejecutar(_pet())
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
               in m and "franquicia=8.00" in m
               and "usuario=usuario-de-prueba" in m for m in msgs)
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


# ------- T10, T23: X leida del campo EXTENDIDO (R1-R3, R38-R42, R47, R48) ------- #

def test_f056_r3_franquicias_apagada_sin_leer_nada():
    cli = _cli()
    pipe = _pipe(cli, cod="")[0]
    e = pipe.franquicias([REC, 502])
    assert (e.estado, e.recursos) == ("apagada", {})
    assert e.motivo == "FRANQUICIA_CAMPO_EXT vacio"
    assert isinstance(e, EstadoFranquicias)
    assert cli.definiciones_leidas == [] and cli.valores_leidos == []


@pytest.mark.parametrize("cod", ["  ", "10;DROP TABLE res;--", "x" * 17,
                                 "10" + chr(10), "1 0", "'10'"])
def test_f056_r38_codigo_malo_es_no_disponible_sin_leer(cod, caplog):
    cli = _cli()
    with caplog.at_level(logging.WARNING):
        e = _pipe(cli, cod=cod)[0].franquicias([REC])
    assert (e.estado, e.recursos) == ("no_disponible", {})
    assert e.motivo and e.motivo.isascii()
    assert "FRANQUICIA_CAMPO_EXT" in e.motivo
    assert cli.definiciones_leidas == [] and cli.valores_leidos == []
    assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_f056_r38_r39_definicion_ausente_no_disponible_y_se_vuelve_a_mirar(
        caplog):
    cli = _cli()
    cli.defext = []
    pipe = _pipe(cli)[0]
    with caplog.at_level(logging.WARNING):
        e = pipe.franquicias([REC])
    assert e.estado == "no_disponible" and COD in e.motivo
    assert "no hay definicion" in e.motivo
    assert cli.valores_leidos == []
    assert any(r.levelno == logging.WARNING for r in caplog.records)
    cli.defext = [_def()]                     # Administracion la crea
    assert pipe.franquicias([REC]).estado == "ok"
    assert cli.definiciones_leidas == [COD, COD]


@pytest.mark.parametrize("defs, trozo", [
    ([{"ide": 49, "tip": 33, "cod": COD, "camtip": 6}], "camtip 6"),
    ([{"ide": 49, "tip": 33, "cod": COD, "camtip": 3}], "camtip 3"),
    ([{"ide": 49, "tip": 33, "cod": COD, "camtip": 1},
      {"ide": 50, "tip": 33, "cod": COD, "camtip": 1}], "2 definiciones"),
])
def test_f056_r38_definicion_doble_o_no_entera_no_disponible(defs, trozo):
    """R38, DA31: otro `camtip` (no `valn` entero) o dos definiciones de
    tip 33 => `no_disponible` sin leer valores."""
    cli = _cli()
    cli.defext = defs
    e = _pipe(cli)[0].franquicias([REC])
    assert e.estado == "no_disponible" and trozo in e.motivo
    assert cli.valores_leidos == []


def test_f056_r47_el_cod_10_de_tip_42_nunca_da_x():
    """R47, H8: el `cod` `10` tambien es «Administrativo de obra» de tip 42
    (`camtip` 6, filas en `conext` de contactos de tip 42). Ni su
    definicion cuenta (sin la de tip 33 => `no_disponible`) ni sus filas
    dan X a nadie, aunque se pida ese ide."""
    cli = _cli()
    cli.defext = [{"ide": 26, "tip": 42, "cod": COD, "camtip": 6}]
    pipe = _pipe(cli)[0]
    e = pipe.franquicias([REC])
    assert e.estado == "no_disponible" and "no hay definicion" in e.motivo
    cli.defext = [{"ide": 26, "tip": 42, "cod": COD, "camtip": 6}, _def()]
    cli.con_tipos[900] = 42
    cli.conext.append({"ide": 8800, "conide": 900, "cod": COD, "valn": 12})
    e = pipe.franquicias([REC, 900])
    assert e.estado == "ok"
    assert (e.recursos[REC].estado, e.recursos[REC].franquicia) == (
        "activa", 8.0)
    assert (e.recursos[900].estado, e.recursos[900].franquicia) == (
        "invalida", None)
    assert "no existe" in e.recursos[900].motivo


def test_f056_r48_mismo_dni_dos_empresas_usa_la_del_recurso_pedido():
    """R48, DA29 (el humano: «el mismo dni de recurso puede estar en 2
    empresas»): una persona con un recurso en cada empresa, X 8 y 20. Se
    lee por `res.ide` y solo cuenta la del recurso pedido (el de la
    empresa de la obra, `hmores.reside`); nunca se busca por DNI."""
    otro = 601
    mismos = [RecursoSigrid(REC, 1, None, "11111111H"),
              RecursoSigrid(otro, 2, None, "11111111H")]
    cli = _cli(recursos={r.reside: r for r in mismos},
               por_dni={"11111111H": mismos})
    cli.poner_franquicia(otro, 20, cod=COD)
    pipe = _pipe(cli)[0]
    e = pipe.franquicias([REC])
    assert list(e.recursos) == [REC]
    assert (e.recursos[REC].estado, e.recursos[REC].franquicia) == (
        "activa", 8.0)
    r = pipe.comprobar(_pet())
    assert (r.franquicia, r.objetivo) == (8.0, -6.0)
    r = pipe.ejecutar(_pet())
    assert (r.ok, r.franquicia, r.objetivo) == (True, 8.0, -6.0)
    assert cli.valores_leidos and all(
        ides == [REC] for ides, _ in cli.valores_leidos)
    assert "recursos_por_dni" not in cli.llamadas
    e = pipe.franquicias([otro])
    assert e.recursos[otro].franquicia == 20.0


def test_f056_r2_r40_franquicias_ok_por_recurso_y_cache_del_si():
    cli = _cli()
    cli.poner_franquicia(502, None, cod=COD)
    cli.poner_franquicia(503, -1, cod=COD)
    cli.poner_franquicia(504, 0, cod=COD)
    cli.poner_franquicia(505, cod=COD)                 # sin fila
    cli.poner_franquicia(507, 201, cod=COD)
    cli.con_tipos[508] = 33
    cli.conext += [{"ide": 8801, "conide": 508, "cod": COD, "valn": 8},
                   {"ide": 8802, "conide": 508, "cod": COD, "valn": 20}]
    pipe = _pipe(cli)[0]
    e = pipe.franquicias([REC, 502, 503, 504, 505, 506, 507, 508])
    assert (e.estado, e.motivo) == ("ok", None)
    assert {k: (v.estado, v.franquicia) for k, v in e.recursos.items()} == {
        REC: ("activa", 8.0), 502: ("inactiva", 0.0),
        503: ("invalida", None), 504: ("inactiva", 0.0),
        505: ("inactiva", 0.0), 506: ("invalida", None),
        507: ("invalida", None), 508: ("invalida", None)}
    assert "no existe" in e.recursos[506].motivo
    assert e.recursos[508].motivo == fr.MOTIVO_VARIAS_FILAS
    assert cli.valores_leidos == [
        ([REC, 502, 503, 504, 505, 506, 507, 508], COD)]
    pipe.franquicias([REC])
    assert cli.definiciones_leidas == [COD]           # el «si» se recuerda


def test_f056_r39_fallo_de_valores_olvida_el_si(caplog):
    cli = _cli()
    pipe = _pipe(cli)[0]
    assert pipe.franquicias([REC]).estado == "ok"
    cli.fallo_valores = RuntimeError("Invalid object name")
    with caplog.at_level(logging.WARNING):
        e = pipe.franquicias([REC])
    assert e.estado == "no_disponible" and "Invalid object name" in e.motivo
    assert COD in e.motivo
    cli.fallo_valores = None
    assert pipe.franquicias([REC]).estado == "ok"
    assert cli.definiciones_leidas == [COD, COD]      # se volvio a mirar


def test_f056_r39_otro_codigo_se_vuelve_a_mirar():
    """El «si» es del `cod` comprobado: si cambia el ajuste, se mira."""
    cli = _cli()
    cli.defext.append({"ide": 52, "tip": 33, "cod": "11", "camtip": 1})
    st = SettingsFake(franquicia_campo_ext=COD)
    reg = RegistroPipeline(cliente=cli, settings=st, lock=LockEspia())
    pipe = FranquiciaPipeline(cliente=cli, settings=st, registro=reg)
    pipe.franquicias([REC])
    st.franquicia_campo_ext = "11"
    pipe.franquicias([REC])
    assert cli.definiciones_leidas == [COD, "11"]


def test_f056_r40_fallo_al_leer_la_definicion_es_excepcion():
    """design §6: `/recursos` responde 502 si falla leer la definicion."""
    cli = _cli()
    cli.fallo_definicion = RuntimeError("sigrid caido")
    with pytest.raises(RuntimeError, match="sigrid caido"):
        _pipe(cli)[0].franquicias([REC])


def test_f056_r40_franquicias_sin_recursos_no_lee_valores():
    cli = _cli()
    e = _pipe(cli)[0].franquicias([])
    assert (e.estado, e.recursos) == ("ok", {})
    assert cli.valores_leidos == []


@pytest.mark.parametrize("prep, prefijo, estado", [
    ({"cod": ""}, "franquicia_apagada", "apagada"),
    ({"defs": []}, "franquicia_no_disponible", "no_disponible"),
    ({"valor": -1}, "franquicia_invalida", "invalida"),
    ({"valor": 201}, "franquicia_invalida", "invalida"),
    ({"dos_filas": True}, "franquicia_invalida", "invalida"),
    ({"fallo_def": True}, "franquicia_no_disponible", "no_disponible"),
    ({"fallo_valores": True}, "franquicia_no_disponible", "no_disponible"),
])
def test_f056_r42_franquicia_desconocida_no_escribe(prep, prefijo, estado):
    """R42: «no se sabe» nunca es X = 0: ni crea ni toca la linea que ya
    existe; `comprobar` y `ejecutar` responden `no_editable`."""
    cli = _cli(lineas=[_extra(7001, 20261001, 10.0),
                       _extra(7009, DIA, -6.0, synckey=SK)])
    if "defs" in prep:
        cli.defext = prep["defs"]
    if "valor" in prep:
        cli.poner_franquicia(REC, prep["valor"], cod=COD)
    if prep.get("dos_filas"):
        cli.conext.append({"ide": 8803, "conide": REC, "cod": COD,
                           "valn": 8})
    if prep.get("fallo_def"):
        cli.fallo_definicion = RuntimeError("sigrid caido")
    if prep.get("fallo_valores"):
        cli.fallo_valores = RuntimeError("sigrid caido")
    pipe, _lock = _pipe(cli, cod=prep.get("cod", COD))
    for r in (pipe.comprobar(_pet()), pipe.ejecutar(_pet())):
        assert (r.ok, r.accion, r.escrita) == (False, fr.NO_EDITABLE, False)
        assert r.motivo.startswith(f"{prefijo}: ")
        assert (r.franquicia, r.franquicia_estado) == (None, estado)
    assert "escribir" not in cli.llamadas
    assert _ajuste(cli)[0]["can"] == -6.0


def test_f056_r42_fallo_de_la_definicion_dice_el_campo_extendido():
    """`_franquicia_de`: un fallo al leer la definicion es `no_disponible`
    y su motivo dice que fue la definicion (no una columna)."""
    cli = _cli()
    cli.fallo_definicion = RuntimeError("sigrid caido")
    r = _pipe(cli)[0].comprobar(_pet())
    assert r.motivo.startswith("franquicia_no_disponible: ")
    assert "definicion del campo extendido" in r.motivo
    assert "columna" not in r.motivo


def test_f056_r3_apagada_comprobar_no_lee_el_campo():
    cli = _cli()
    _pipe(cli, cod="")[0].comprobar(_pet())
    assert cli.definiciones_leidas == [] and cli.valores_leidos == []


def test_f056_r41_ejecutar_lee_x_bajo_el_lock_y_comprobar_sin_el():
    cli = _cli()
    pipe, lock = _pipe(cli)
    pipe.comprobar(_pet())
    assert not lock.locked() and lock.tomas == 0
    cli.vigilar_lock(lock)      # desde aqui, lecturas de estado bajo lock
    pipe.ejecutar(_pet())
    assert cli.valores_bajo_lock == [False, True]
    assert cli.valores_leidos == [([REC], COD), ([REC], COD)]


def test_f056_r1_r41_da22_vale_la_x_de_sigrid_al_ejecutar():
    """R1 (X solo la lee sv5, del campo del recurso, con el valor de ese
    momento) y DA22: si Administracion cambia X entre el aviso y el
    registro, el ajuste usa la X de ese momento (y la devuelve)."""
    cli = _cli()
    pipe = _pipe(cli)[0]
    r = pipe.comprobar(_pet())
    assert (r.franquicia, r.objetivo) == (8.0, -6.0)
    cli.poner_franquicia(REC, 2, cod=COD)
    r = pipe.ejecutar(_pet())
    assert (r.ok, r.franquicia, r.franquicia_estado, r.objetivo) == (
        True, 2.0, "activa", -2.0)
    assert _ajuste(cli)[0]["can"] == -2.0


@pytest.mark.parametrize("sin_fila", [False, True])
def test_f056_r42_inactiva_sin_linea_es_sin_ajuste(sin_fila):
    """DA29: valor vacio o sin fila en `conext` => sin franquicia."""
    cli = _cli()
    if sin_fila:
        cli.poner_franquicia(REC, cod=COD)
    else:
        cli.poner_franquicia(REC, None, cod=COD)
    r = _pipe(cli)[0].ejecutar(_pet())
    assert (r.ok, r.accion, r.objetivo, r.escrita) == (
        True, fr.SIN_AJUSTE, 0.0, False)
    assert (r.franquicia, r.franquicia_estado) == (0.0, "inactiva")
    assert _ajuste(cli) == []


def test_f056_t23_el_pipeline_no_lee_columnas_de_res():
    """DA29: el pipeline ya no pide columnas de `res` y `SettingsFake` (como
    `Settings`) ya no tiene `franquicia_campo_res`."""
    cli = _cli()
    _pipe(cli)[0].franquicias([REC])
    assert not any("columna" in x or "campo_res" in x for x in cli.llamadas)
    assert "definicion_campo_ext" in cli.llamadas
    assert not hasattr(SettingsFake(), "franquicia_campo_res")


# ============ supervivientes de la campana de mutacion (2026-10-29) ============ #
# Cada test caza un mutante que la suite dejaba vivo (numero entre corchetes:
# el de `progress/mutacion_F-056.md`).

def test_f056_r22_comprobar_linea_sin_parte_no_inventa_el_parte():
    """[81] Una linea de ajuste sin `hmoide` sale sin parte (no el 1)."""
    cli = _cli(lineas=[_extra(7001, 20261001, 10.0),
                       _extra(7009, DIA, -6.0, synckey=SK, hmoide=None)])
    r = _pipe(cli)[0].comprobar(_pet())
    assert r.hmores_ide == 7009 and r.hmoide is None


def test_f056_r33_comprobar_registra_los_pendientes(caplog):
    """[82] El log de `comprobar` lleva las extras pendientes."""
    with caplog.at_level(logging.INFO):
        _pipe(_cli())[0].comprobar(_pet(pendientes=2.5))
    assert any("pendientes=2.50" in r.getMessage() for r in caplog.records
               if r.name.endswith("franquicia_pipeline"))


def test_f056_r22_ejecutar_con_ajuste_negativo_es_error():
    """[83] Un `ajuste_id` negativo no es una fila de sv4."""
    cli = _cli()
    with pytest.raises(ValueError):
        _pipe(cli)[0].ejecutar(_pet(ajuste_id=-1))
    assert cli.__dict__.get("grabadas", []) == []


def test_f056_r22_ejecutar_con_el_ajuste_1():
    """[85] La fila 1 de sv4 es un ajuste como otro cualquiera."""
    cli = _cli()
    r = _pipe(cli)[0].ejecutar(_pet(ajuste_id=1))
    assert (r.ok, r.accion, r.escrita) == (True, fr.CREAR, True)
    assert [x["synckey"] for x in cli.lineas
            if x.get("synckey", "").startswith("partes:franquicia:")] == [
        "partes:franquicia:1"]


def test_f056_r29_relectura_sin_parte_no_es_escrita_ni_en_el_parte_1(
        monkeypatch):
    """[88] R29: si la relectura no dice en que parte quedo la linea, no se
    da por escrita (tampoco si el parte elegido es el 1)."""
    cli = _cli(partes=[_parte(ide=1)])
    original = cli.escribir

    def sin_parte(statements):
        out = original(statements)
        for x in _ajuste(cli):
            x["hmoide"] = None
        return out

    monkeypatch.setattr(cli, "escribir", sin_parte)
    r = _pipe(cli)[0].ejecutar(_pet())
    assert (r.ok, r.accion, r.escrita) == (False, fr.CREAR, False)


def test_f056_r24_ajuste_sin_partida_va_con_partida_0():
    """[91] Sin partida, la linea de ajuste lleva `paride` 0 (sin partida),
    no la partida 1."""
    cli = _cli()
    p = _pet()
    p.partida_ide, p.partida_cod = None, None
    r = _pipe(cli)[0].ejecutar(p)
    assert (r.ok, r.escrita) == (True, True)
    [linea] = _ajuste(cli)
    assert linea["paride"] == 0
