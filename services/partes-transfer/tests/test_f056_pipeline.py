# tests/test_f056_pipeline.py
"""F-056 · `FranquiciaPipeline` de sv5 (R22-R33) y
`RegistroPipeline.asegurar_parte`.

Contra `SigridFake` (tests/dobles.py), que evalua el `INSERT` con la guarda
de parte abierto, el `UPDATE` optimista (`actualizar`) y el alta protegida
del parte. Recorre el guion de M2 (design §10): crear, repetir, recalcular
al alza, a 0 sin borrar; y los rechazos (parte cerrado, enlazada, sin
`HE*`, recurso de otra empresa), la relectura, el modo pruebas y el lock.

Enmienda 2026-10-27 (T10, DA1 = C): X ya no llega en la peticion; el
pipeline la lee del campo de `res` (`franquicias`, R1-R3, R38-R42). El
nombre de la columna de estos tests es INVENTADO (el campo aun no existe).

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
#: Nombre INVENTADO de la columna de `res` (el real aun no existe).
CAMPO = "FranqInventada"


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
    """Por defecto la columna existe (`decimal`) y el recurso tiene X = 8."""
    cli = _sigrid(lineas, partes, horas, **kw)
    cli.columnas_res = {CAMPO: "decimal"}
    cli.valores_res = {REC: 8.0}
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


def _pipe(cli, *, pruebas=False, campo=CAMPO):
    st = SettingsFake(obra_pruebas_forzar=pruebas,
                      franquicia_campo_res=campo)
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
    cli.valores_res[REC] = 0               # Administracion la quita
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


# ------------- T10: X leida del campo de `res` (enmienda, R1-R3) ------------- #

def test_f056_r3_franquicias_apagada_sin_leer_nada():
    cli = _cli()
    pipe = _pipe(cli, campo="")[0]
    e = pipe.franquicias([REC, 502])
    assert (e.estado, e.recursos) == ("apagada", {})
    assert isinstance(e, EstadoFranquicias)
    assert cli.tipos_leidos == [] and cli.valores_leidos == []


@pytest.mark.parametrize("campo", ["  ", "a];DROP TABLE res;--", "1x",
                                   "campo" + chr(10), "res.campo"])
def test_f056_r38_nombre_malo_es_no_disponible_sin_leer(campo, caplog):
    cli = _cli()
    with caplog.at_level(logging.WARNING):
        e = _pipe(cli, campo=campo)[0].franquicias([REC])
    assert (e.estado, e.recursos) == ("no_disponible", {})
    assert e.motivo and e.motivo.isascii()
    assert cli.tipos_leidos == [] and cli.valores_leidos == []
    assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_f056_r38_r39_columna_ausente_no_disponible_y_se_vuelve_a_mirar(
        caplog):
    cli = _cli()
    cli.columnas_res = {}
    pipe = _pipe(cli)[0]
    with caplog.at_level(logging.WARNING):
        e = pipe.franquicias([REC])
    assert e.estado == "no_disponible" and CAMPO in e.motivo
    assert cli.valores_leidos == []
    assert any(r.levelno == logging.WARNING for r in caplog.records)
    cli.columnas_res = {CAMPO: "numeric"}     # Administracion la crea
    assert pipe.franquicias([REC]).estado == "ok"
    assert cli.tipos_leidos == [CAMPO, CAMPO]


@pytest.mark.parametrize("tipo", ["varchar", "bigint", "bit", "datetime"])
def test_f056_r38_columna_no_numerica_no_disponible(tipo):
    cli = _cli()
    cli.columnas_res = {CAMPO: tipo}
    e = _pipe(cli)[0].franquicias([REC])
    assert e.estado == "no_disponible" and tipo in e.motivo
    assert cli.valores_leidos == []


def test_f056_r2_r40_franquicias_ok_por_recurso_y_cache_del_si():
    cli = _cli()
    cli.valores_res = {REC: 8.0, 502: None, 503: -1, 504: 0, 505: 7.126}
    pipe = _pipe(cli)[0]
    e = pipe.franquicias([REC, 502, 503, 504, 505, 506])
    assert (e.estado, e.motivo) == ("ok", None)
    assert {k: (v.estado, v.franquicia) for k, v in e.recursos.items()} == {
        REC: ("activa", 8.0), 502: ("inactiva", 0.0),
        503: ("invalida", None), 504: ("inactiva", 0.0),
        505: ("activa", 7.13), 506: ("invalida", None)}
    assert "no existe" in e.recursos[506].motivo
    assert cli.valores_leidos == [([REC, 502, 503, 504, 505, 506], CAMPO)]
    pipe.franquicias([REC])
    assert cli.tipos_leidos == [CAMPO]                # el «si» se recuerda


def test_f056_r39_fallo_de_valores_olvida_el_si(caplog):
    cli = _cli()
    pipe = _pipe(cli)[0]
    assert pipe.franquicias([REC]).estado == "ok"
    cli.fallo_valores_res = RuntimeError("Invalid column name")
    with caplog.at_level(logging.WARNING):
        e = pipe.franquicias([REC])
    assert e.estado == "no_disponible" and "Invalid column name" in e.motivo
    cli.fallo_valores_res = None
    assert pipe.franquicias([REC]).estado == "ok"
    assert cli.tipos_leidos == [CAMPO, CAMPO]         # se volvio a mirar


def test_f056_r40_fallo_al_leer_el_tipo_es_excepcion():
    """design §6: `/recursos` responde 502 si falla la lectura del tipo."""
    cli = _cli()
    cli.fallo_tipo_columna = RuntimeError("sigrid caido")
    with pytest.raises(RuntimeError, match="sigrid caido"):
        _pipe(cli)[0].franquicias([REC])


def test_f056_r40_franquicias_sin_recursos_no_lee_valores():
    cli = _cli()
    e = _pipe(cli)[0].franquicias([])
    assert (e.estado, e.recursos) == ("ok", {})
    assert cli.valores_leidos == []


@pytest.mark.parametrize("prep, prefijo, estado", [
    ({"campo": ""}, "franquicia_apagada", "apagada"),
    ({"columnas": {}}, "franquicia_no_disponible", "no_disponible"),
    ({"valor": -1}, "franquicia_invalida", "invalida"),
    ({"valor": 200.5}, "franquicia_invalida", "invalida"),
    ({"fallo_tipo": True}, "franquicia_no_disponible", "no_disponible"),
    ({"fallo_valores": True}, "franquicia_no_disponible", "no_disponible"),
])
def test_f056_r42_franquicia_desconocida_no_escribe(prep, prefijo, estado):
    """R42: «no se sabe» nunca es X = 0: ni crea ni toca la linea que ya
    existe; `comprobar` y `ejecutar` responden `no_editable`."""
    cli = _cli(lineas=[_extra(7001, 20261001, 10.0),
                       _extra(7009, DIA, -6.0, synckey=SK)])
    if "columnas" in prep:
        cli.columnas_res = prep["columnas"]
    if "valor" in prep:
        cli.valores_res[REC] = prep["valor"]
    if prep.get("fallo_tipo"):
        cli.fallo_tipo_columna = RuntimeError("sigrid caido")
    if prep.get("fallo_valores"):
        cli.fallo_valores_res = RuntimeError("sigrid caido")
    pipe, _lock = _pipe(cli, campo=prep.get("campo", CAMPO))
    for r in (pipe.comprobar(_pet()), pipe.ejecutar(_pet())):
        assert (r.ok, r.accion, r.escrita) == (False, fr.NO_EDITABLE, False)
        assert r.motivo.startswith(f"{prefijo}: ")
        assert (r.franquicia, r.franquicia_estado) == (None, estado)
    assert "escribir" not in cli.llamadas
    assert _ajuste(cli)[0]["can"] == -6.0


def test_f056_r3_apagada_comprobar_no_lee_el_campo():
    cli = _cli()
    _pipe(cli, campo="")[0].comprobar(_pet())
    assert cli.tipos_leidos == [] and cli.valores_leidos == []


def test_f056_r41_ejecutar_lee_x_bajo_el_lock_y_comprobar_sin_el():
    cli = _cli()
    pipe, lock = _pipe(cli)
    pipe.comprobar(_pet())
    assert not lock.locked() and lock.tomas == 0
    cli.vigilar_lock(lock)      # desde aqui, lecturas de estado bajo lock
    pipe.ejecutar(_pet())
    assert cli.valores_bajo_lock == [False, True]
    assert cli.valores_leidos == [([REC], CAMPO), ([REC], CAMPO)]


def test_f056_r41_da22_vale_la_x_de_sigrid_al_ejecutar():
    """DA22: si Administracion cambia X entre el aviso y el registro, el
    ajuste usa la X de ese momento (y la devuelve)."""
    cli = _cli()
    pipe = _pipe(cli)[0]
    r = pipe.comprobar(_pet())
    assert (r.franquicia, r.objetivo) == (8.0, -6.0)
    cli.valores_res[REC] = 2.5
    r = pipe.ejecutar(_pet())
    assert (r.ok, r.franquicia, r.franquicia_estado, r.objetivo) == (
        True, 2.5, "activa", -2.5)
    assert _ajuste(cli)[0]["can"] == -2.5


def test_f056_r42_inactiva_sin_linea_es_sin_ajuste():
    cli = _cli()
    cli.valores_res[REC] = None
    r = _pipe(cli)[0].ejecutar(_pet())
    assert (r.ok, r.accion, r.objetivo, r.escrita) == (
        True, fr.SIN_AJUSTE, 0.0, False)
    assert (r.franquicia, r.franquicia_estado) == (0.0, "inactiva")
    assert _ajuste(cli) == []

