# tests/test_f034_pipeline_cierre.py
"""F-034 · El parte se cierra en la ventana: sv5 solo escribe en partes
abiertos (estado 1, En registro).

Primer bloque: CARACTERIZACION en verde contra el codigo anterior a F-034
(R15-R18): lo que ya hacia F-031/F-046 con partes cerrados y que no debe
cambiar. Los bloques siguientes (T6, T7) cubren lo nuevo: la guarda de
cada sentencia (que el doble `SigridFake` evalua como SQL Server), la
relectura tras escribir y el motivo `parte_no_abierto`.

Sin red: `SigridFake` de `tests/dobles.py`. Datos SINTETICOS (obras,
codigos y personas inventados; ni nombres reales ni DNIs).
"""
from __future__ import annotations

import threading

import pytest
from application.pipelines.reajuste_pipeline import ReajustePipeline
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.reajuste_lineas import MOTIVO_PARTE_NO_EN_REGISTRO
from domain.models.registro_models import (
    HoraRecurso,
    LineaEntrada,
    ObraEntrada,
    OpReajuste,
)
from infrastructure.sigrid.sigrid_write_client import synckey_de
from tests.dobles import SettingsFake, SigridFake
from tests.dobles_reajuste import SigridReajusteFake

FECHA = 20261014
CEN_OBRA = 77
HL, HE = 1, 2
REGISTRO, CERRADO, IMPUTADO = 1, 3, 10
OBRA = 10
HMO = 900                     # PT26/00314, el parte del ejemplo 1


def _obra(ide=OBRA, cod="0100", empresa=1) -> ObraEntrada:
    o = ObraEntrada(ide=ide, codigo=cod, nombre=f"Obra {cod}",
                    empresa=empresa)
    o.cenide = CEN_OBRA
    return o


def _h(horide, cod, defecto=False, pre=10.0) -> HoraRecurso:
    return HoraRecurso(horide=horide, cod=cod, res=None, pre=pre,
                       caa_cod=None, defecto=defecto)


HORAS = {501: [_h(HL, "HL01", True), _h(HE, "HE01", pre=25.0)]}


def _parte(ide, cod, est=REGISTRO, ano=2026, mes=10) -> dict:
    return {"ide": ide, "obride": OBRA, "ano": ano, "mes": mes, "cod": cod,
            "emp": 1, "est": est}


def _linea_sigrid(ide, hmoide, reside=501, horide=HL, synckey=None,
                  fec=FECHA, can=8.0) -> dict:
    return {"ide": ide, "hmoide": hmoide, "reside": reside, "fec": fec,
            "horide": horide, "hora_codigo": None, "can": can,
            "tot": can * 10.0, "pos": 64, "synckey": synckey, "caaide": 0}


def _cli(**kw) -> SigridFake:
    return SigridFake(obras={"0100": _obra()}, horas=HORAS, **kw)


def _lin(rid, recurso=501, fecha_int=FECHA, tipo="normal") -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=fecha_int,
                        recurso_ide=recurso, nombre=f"Persona {rid}",
                        tipo_hora=tipo, horas=8.0)


def _pipeline(cli, lock=None) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=SettingsFake(), lock=lock)


def _sincronizadas(cli) -> dict[int, list[int]]:
    out: dict[int, list[int]] = {}
    for fila in cli.lineas:
        if (fila.get("synckey") or "").startswith("partes:"):
            out.setdefault(fila["hmoide"], []).append(
                int(fila["synckey"].split(":")[1]))
    return out


# ============ Caracterizacion (verde ANTES de F-034, R15-R18) ============ #

def test_f034_r15_sin_parte_abierto_va_al_complementario() -> None:
    """F-031 R2-R4: con el unico parte del mes Cerrado, la linea va a un
    parte nuevo (el complementario), nunca al cerrado."""
    cli = _cli(partes=[_parte(HMO, "PT26/00314", est=CERRADO)],
               alta_protegida=True)
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    (nuevo,) = [p for p in cli.partes if p["ide"] != HMO]
    assert nuevo["cod"] == "PT26/00315"
    assert [(e["registro_id"], e["parte_cod"]) for e in r.escritas] == [
        (1, "PT26/00315")]
    assert _sincronizadas(cli) == {nuevo["ide"]: [1]}
    assert r.omitidas == []


def test_f034_r15_horas_ajenas_en_parte_cerrado_se_omiten() -> None:
    """F-031 R11: horas ajenas del mismo recurso, dia y tipo en el parte
    cerrado => `parte_cerrado`, sin escribir."""
    cli = _cli(partes=[_parte(HMO, "PT26/00314", est=CERRADO),
                       _parte(905, "PT26/00400")],
               lineas=[_linea_sigrid(4001, HMO)])
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    (om,) = r.omitidas
    assert om["registro_id"] == 1
    assert om["motivo"].startswith("parte_cerrado: ")
    assert "PT26/00314 (Cerrado)" in om["motivo"]
    assert r.escritas == [] and "escribir" not in cli.llamadas


def test_f034_r16_reaprobar_en_parte_cerrado_es_ya_registrado() -> None:
    """Ejemplo 3: la synckey ya esta en un parte Imputado => `ya_registrado`
    y CERO sentencias (ni siquiera una llamada a `escribir`)."""
    previa = _linea_sigrid(4001, HMO, synckey=synckey_de(1))
    cli = _cli(partes=[_parte(HMO, "PT26/00314", est=IMPUTADO)],
               lineas=[dict(previa)])
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    assert r.ya_registradas == [1]
    assert r.escritas == [] and r.omitidas == []
    assert "escribir" not in cli.llamadas
    assert cli.lineas == [previa]


def _reajuste(est):
    cli = SigridReajusteFake(
        obras={"0100": _obra()}, horas=HORAS,
        partes=[_parte(HMO, "PT26/00314", est=est)],
        lineas=[dict(_linea_sigrid(4001, HMO, synckey="partes:11"),
                     pre=10.0)])
    st = SettingsFake()
    reg = RegistroPipeline(cliente=cli, settings=st, lock=threading.Lock())
    return cli, ReajustePipeline(cliente=cli, settings=st, registro=reg)


def test_f034_r17_reajuste_en_parte_imputado_se_rechaza_sin_escribir() -> None:
    """Ejemplo 4 (F-046 R21, DA10): no editable, lote rechazado."""
    cli, pipe = _reajuste(IMPUTADO)
    r = pipe.ejecutar([OpReajuste(11, despues=5.5, antes=8.0)],
                      usuario="admin@test")
    (v,) = r.veredictos
    assert not r.ok and not v.editable
    assert v.motivo == f"{MOTIVO_PARTE_NO_EN_REGISTRO} (estado 10)"
    assert cli.lotes == []
    assert cli.lineas[0]["can"] == 8.0


def test_f034_r17_reajuste_ya_aplicado_en_parte_cerrado_se_reconoce() -> None:
    """F-046 R26: lo ya escrito se mira antes que el estado del parte."""
    cli, pipe = _reajuste(CERRADO)
    cli.lineas[0]["can"] = 5.5
    r = pipe.ejecutar([OpReajuste(11, despues=5.5, antes=8.0)],
                      usuario="admin@test")
    assert r.ok and r.ya_aplicada
    assert cli.lotes == []


def test_f034_r18_el_parte_que_crea_sv5_nace_en_registro_y_recibe() -> None:
    """El alta protegida no cambia: el parte nuevo nace En registro y la
    linea entra en el."""
    cli = _cli(alta_protegida=True)
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1), _lin(2, fecha_int=20261015)])
    (nuevo,) = cli.partes
    assert nuevo.get("est", REGISTRO) == REGISTRO
    assert [a["insertado"] for a in cli.altas] == [True]
    assert _sincronizadas(cli) == {nuevo["ide"]: [1, 2]}
    assert {e["parte_cod"] for e in r.escritas} == {nuevo["cod"]}
    assert all(e.get("hmores_ide") for e in r.escritas)
    assert r.omitidas == []


# ============ El doble cumple la semantica del SQL real (T5) ============ #
# El SQL lo fija `test_f034_cliente_guarda.py`; aqui, que `SigridFake` lo
# evalua igual, para que los tests del pipeline no prueben un doble falso.

def _st_insert(cli, rid, hmoide=HMO, pisadas=()):
    return cli.stmt_insert_linea(
        hmoide=hmoide, obra=_obra(), reside=501, pos=64, fecha_int=FECHA,
        horide=HL, can=8.0, pre=10.0, paride=0, ano=2026, mes=10,
        synckey=synckey_de(rid), tex=None, caaide=0, pisadas=pisadas)


def test_f034_doble_insert_en_parte_cerrado_no_entra() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314", est=CERRADO),
                       _parte(905, "PT26/00400")])
    assert cli.escribir([_st_insert(cli, 1), _st_insert(cli, 2, 905)]) == 1
    assert _sincronizadas(cli) == {905: [2]}
    (fila,) = cli.lineas
    assert "guarda_hmoide" not in fila and "pisadas" not in fila


def test_f034_doble_insert_en_parte_inexistente_no_entra() -> None:
    cli = _cli()
    assert cli.escribir([_st_insert(cli, 1, 999)]) == 0 and cli.lineas == []


def test_f034_doble_anular_solo_en_parte_abierto() -> None:
    """Enmienda de F-053: la pisada se pone a 0 (op `anular`) en vez de
    borrarse; la guarda de R3 sigue: solo en su parte abierto."""
    cli = _cli(partes=[_parte(HMO, "PT26/00314", est=CERRADO),
                       _parte(905, "PT26/00400")],
               lineas=[_linea_sigrid(4001, HMO), _linea_sigrid(4002, 905)])
    anular = [cli.stmt_anular_linea(ide=i, reside=501, fecha_int=FECHA,
                                    horide=HL, antes=8.0)
              for i in (4001, 4002)]
    assert cli.escribir(anular) == 1
    assert [(l["ide"], l["can"]) for l in cli.lineas] == [(4001, 8.0),
                                                          (4002, 0.0)]


def test_f034_doble_pisada_con_horas_bloquea_el_insert() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")],
               lineas=[_linea_sigrid(4001, HMO),
                       _linea_sigrid(4002, HMO, can=0.0)])
    assert cli.escribir([_st_insert(cli, 1, pisadas=[4001])]) == 0
    assert cli.escribir([_st_insert(cli, 2, pisadas=[4002])]) == 1
    assert _sincronizadas(cli) == {HMO: [2]}


def test_f034_doble_cierra_en_la_ventana_una_sola_vez() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")])
    cli.cerrar_al_escribir = {HMO: CERRADO}
    cli.cerrar_tras_sentencias = 1
    assert cli.escribir([_st_insert(cli, 1), _st_insert(cli, 2)]) == 1
    assert _sincronizadas(cli) == {HMO: [1]}
    assert cli.partes[0]["est"] == CERRADO and cli.cerrar_al_escribir == {}


def test_f034_doble_el_alta_no_dispara_el_cierre() -> None:
    cli = _cli()
    cli.cerrar_al_escribir = {HMO: CERRADO}
    cli.escribir(cli.stmts_crear_parte(obra=_obra(), ano=2026, mes=10,
                                       cod="PT26/00001", desc="Parte"))
    assert cli.cerrar_al_escribir == {HMO: CERRADO}


def test_f034_doble_lineas_por_ide_bajo_lock() -> None:
    cli = _cli(lineas=[_linea_sigrid(4001, HMO), _linea_sigrid(4002, HMO)])
    assert set(cli.lineas_por_ide([4002, None, 4003])) == {4002}
    assert cli.ides_leidos == [[4002, 4003]]
    cli.vigilar_lock(threading.Lock())
    try:
        cli.lineas_por_ide([4001])
    except AssertionError as err:
        assert "FUERA del lock" in str(err)
    else:
        raise AssertionError("lineas_por_ide no vigila el lock")


# ======= Pisado confirmado: R4 y `anuladas` por relectura (T6; F-053) ======= #

CLAVE = f"501|{FECHA}|{HL}"


def _pisado(cerrar=None, lineas=None):
    """Parte 900 (PT26/00314) con una linea AJENA de 501, dia y tipo, y el
    elegido 905 (PT26/00400), los dos En registro."""
    cli = _cli(partes=[_parte(HMO, "PT26/00314"), _parte(905, "PT26/00400")],
               lineas=lineas if lineas is not None
               else [_linea_sigrid(4001, HMO)])
    if cerrar:
        cli.cerrar_al_escribir = cerrar
    return cli


def test_f034_r4_pisada_en_parte_que_se_cierra_no_duplica_horas() -> None:
    """Ejemplo 2: Administracion cierra el parte de la pisada en la
    ventana: su puesta a 0 (F-053) no entra y la linea nueva TAMPOCO (R4),
    aunque su parte (el elegido) siga En registro. Sin R4 habria horas
    duplicadas."""
    cli = _pisado(cerrar={HMO: CERRADO})
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)],
                                pisar_claves={CLAVE})
    assert r.pisadas == [CLAVE]
    assert [(l["ide"], l["can"]) for l in cli.lineas] == [(4001, 8.0)]
    assert _sincronizadas(cli) == {}                      # la nueva no
    assert r.anuladas == 0                                # R12


def test_f034_r4_el_insert_lleva_las_pisadas_de_su_conflicto() -> None:
    cli = _pisado()
    enviadas = []
    original = cli.escribir
    cli.escribir = lambda sts: (enviadas.extend(sts), original(sts))[1]
    _pipeline(cli).ejecutar(obra=_obra(), lineas=[
        _lin(1), _lin(2, fecha_int=20261015)], pisar_claves={CLAVE})
    inserts = {s["synckey"]: s for s in enviadas if s["op"] == "insert"}
    assert inserts[synckey_de(1)]["pisadas"] == [4001]
    assert inserts[synckey_de(2)]["pisadas"] == []      # sin conflicto
    assert [s["op"] for s in enviadas] == ["anular", "insert", "insert"]


def test_f034_r12_anuladas_cuenta_lo_que_ya_no_tiene_horas() -> None:
    """Sin cierre, el pisado pone a 0 la ajena (F-053): `anuladas` = 1 por
    relectura; la ajena sigue en Sigrid."""
    cli = _pisado()
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)],
                                pisar_claves={CLAVE})
    assert r.anuladas == 1
    assert _sincronizadas(cli) == {905: [1]}
    assert next(l for l in cli.lineas if l["ide"] == 4001)["can"] == 0.0
    assert cli.ides_leidos == [[4001]]


def test_f034_r12_anuladas_cuenta_varias_pisadas_por_relectura() -> None:
    """Dos ajenas del mismo recurso, dia y tipo (en 900 y en 905): se
    pisan las dos; si 900 se cierra, solo cuenta la de 905."""
    lineas = [_linea_sigrid(4001, HMO), _linea_sigrid(4002, 905)]
    cli = _pisado(cerrar={HMO: CERRADO}, lineas=lineas)
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)],
                                pisar_claves={CLAVE})
    assert r.anuladas == 1
    assert [(l["ide"], l["can"]) for l in cli.lineas] == [(4001, 8.0),
                                                          (4002, 0.0)]
    assert _sincronizadas(cli) == {}                  # R4: 4001 sigue viva
    assert cli.ides_leidos == [[4001, 4002]]


def test_f034_r12_pisada_que_queda_a_cero_cuenta_como_anulada() -> None:
    """Enmienda de F-053 (R12): desde F-053 el pisado deja la fila a 0;
    `anuladas` cuenta las pisadas sin horas al releer (antes `borradas`
    contaba las que ya no estaban) y, por R4, no bloquean la nueva."""
    cli = _pisado()
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)],
                                pisar_claves={CLAVE})
    assert r.anuladas == 1
    assert _sincronizadas(cli) == {905: [1]}
    assert 4001 in {l["ide"] for l in cli.lineas}


def test_f034_r12_sin_pisadas_no_relee_por_ide() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")])
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    assert r.anuladas == 0 and cli.ides_leidos == []
    assert "lineas_por_ide" not in cli.llamadas


def test_f034_r12_conflicto_no_confirmado_no_cuenta_ni_se_relee() -> None:
    cli = _pisado()
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    assert [c.clave for c in r.pendientes_confirmacion] == [CLAVE]
    assert r.anuladas == 0 and cli.ides_leidos == []


# ======== Relectura tras escribir: lo que no entra (T7, R8-R11, R13-R14) ======== #

MOTIVO_314_CERRADO = (
    "parte_no_abierto: el parte PT26/00314 ya no esta En registro "
    "(Cerrado); no se registra. Reaprueba para llevarla al parte En "
    "registro del mes")


def _tres() -> list[LineaEntrada]:
    return [_lin(1), _lin(2, fecha_int=20261015), _lin(3, fecha_int=20261016)]


def test_f034_r9_r11_ejemplo_1_cierre_en_la_ventana() -> None:
    """Ejemplo 1: las 3 INSERT afectan 0 filas; ninguna sale `registrado`
    y las 3 son `omitidas` con el motivo de DA3."""
    cli = _cli(partes=[_parte(HMO, "PT26/00314")], alta_protegida=True)
    cli.cerrar_al_escribir = {HMO: CERRADO}
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=_tres())
    assert r.ok and r.escritas == []
    assert r.omitidas == [{"registro_id": i, "motivo": MOTIVO_314_CERRADO}
                          for i in (1, 2, 3)]
    assert _sincronizadas(cli) == {}
    # Al reaprobar, F-031 crea el complementario y las lineas entran.
    r2 = _pipeline(cli).ejecutar(obra=_obra(), lineas=_tres())
    (nuevo,) = [p for p in cli.partes if p["ide"] != HMO]
    assert nuevo["cod"] == "PT26/00315"
    assert [e["registro_id"] for e in r2.escritas] == [1, 2, 3]
    assert r2.omitidas == []
    assert _sincronizadas(cli) == {nuevo["ide"]: [1, 2, 3]}


def test_f034_r11_el_motivo_nombra_imputado() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")])
    cli.cerrar_al_escribir = {HMO: IMPUTADO}
    (om,) = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)]).omitidas
    assert om["motivo"] == MOTIVO_314_CERRADO.replace("Cerrado", "Imputado")


def test_f034_r11_el_motivo_nombra_otro_estado() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")])
    cli.cerrar_al_escribir = {HMO: 7}
    (om,) = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)]).omitidas
    assert "(estado 7)" in om["motivo"]


def test_f034_r11_ejemplo_2_la_nueva_sale_con_el_parte_de_su_pisada() -> None:
    """El elegido (PT26/00400) sigue abierto: lo impidio PT26/00314, el
    parte de la pisada que se cerro."""
    cli = _pisado(cerrar={HMO: CERRADO})
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)],
                                pisar_claves={CLAVE})
    assert r.escritas == [] and r.anuladas == 0
    assert r.omitidas == [{"registro_id": 1, "motivo": MOTIVO_314_CERRADO}]


def test_f034_r11_elegido_cerrado_y_pisada_abierta_nombra_el_elegido() -> None:
    cli = _pisado(cerrar={905: IMPUTADO})
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)],
                                pisar_claves={CLAVE})
    (om,) = r.omitidas
    assert om["motivo"].startswith(
        "parte_no_abierto: el parte PT26/00400 ya no esta En registro "
        "(Imputado)")
    assert r.anuladas == 1            # la pisada de 900 si se puso a 0


def test_f034_r9_dos_periodos_uno_cerrado() -> None:
    """Solo las lineas del periodo cerrado salen; la relectura de partes
    es UNA y solo de ese periodo (R10)."""
    cli = _cli(partes=[_parte(HMO, "PT26/00314"),
                       _parte(800, "PT26/00200", mes=9)])
    cli.cerrar_al_escribir = {800: CERRADO}
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[
        _lin(1), _lin(2, fecha_int=20260915), _lin(3, fecha_int=20260916)])
    assert [e["registro_id"] for e in r.escritas] == [1]
    assert [o["registro_id"] for o in r.omitidas] == [2, 3]
    assert all("PT26/00200" in o["motivo"] for o in r.omitidas)
    assert cli.periodos_leidos == [(OBRA, 2026, 9), (OBRA, 2026, 10),
                                   (OBRA, 2026, 9)]


def test_f034_r9_cierre_entre_lotes_decide_linea_a_linea() -> None:
    """Cierre tras 15 sentencias (entre dos lotes del cliente real): las
    15 primeras entran, las demas no; la relectura decide, no la
    respuesta de `escribir`."""
    lineas = [_lin(i, fecha_int=20261001 + i) for i in range(1, 21)]
    cli = _cli(partes=[_parte(HMO, "PT26/00314")])
    cli.cerrar_al_escribir = {HMO: CERRADO}
    cli.cerrar_tras_sentencias = 15
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=lineas)
    assert [e["registro_id"] for e in r.escritas] == list(range(1, 16))
    assert all(e["hmores_ide"] for e in r.escritas)
    assert [o["registro_id"] for o in r.omitidas] == list(range(16, 21))
    assert _sincronizadas(cli) == {HMO: list(range(1, 16))}


def test_f034_r10_sin_no_escritas_no_relee_los_partes() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")])
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=_tres())
    assert [e["registro_id"] for e in r.escritas] == [1, 2, 3]
    assert cli.periodos_leidos == [(OBRA, 2026, 10)]
    assert r.omitidas == []


def test_f034_r13_warning_sin_nombres(caplog) -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")])
    cli.cerrar_al_escribir = {HMO: CERRADO}
    with caplog.at_level("INFO"):
        _pipeline(cli).ejecutar(obra=_obra(), lineas=_tres())
    (w,) = [r for r in caplog.records
            if "no escritas por parte no abierto" in r.getMessage()]
    assert w.levelname == "WARNING"
    assert w.getMessage() == (
        "[registro] no escritas por parte no abierto obra=0100 "
        "periodo=2026/10 partes=PT26/00314 (Cerrado) registro_ids=[1, 2, 3]")
    assert not [r for r in caplog.records if r.levelname == "ERROR"]
    assert "Persona" not in caplog.text


def test_f034_r11_no_escrita_sin_parte_cerrado_es_error(caplog) -> None:
    """Sigrid no confirma la linea pero su parte sigue abierto: no deberia
    ocurrir; motivo `no_escrita` y un ERROR."""
    cli = _cli(partes=[_parte(HMO, "PT26/00314")])
    original = cli.escribir
    cli.escribir = lambda sts: original(
        [s for s in sts if s.get("synckey") != synckey_de(2)])
    with caplog.at_level("INFO"):
        r = _pipeline(cli).ejecutar(obra=_obra(), lineas=_tres())
    assert [e["registro_id"] for e in r.escritas] == [1, 3]
    assert r.omitidas == [{"registro_id": 2, "motivo": (
        "no_escrita: Sigrid no confirmo la linea en el parte PT26/00314; "
        "reaprueba")}]
    (e,) = [x for x in caplog.records if x.levelname == "ERROR"]
    assert e.getMessage() == (
        "[registro] no escritas sin parte cerrado que lo explique obra=0100 "
        "periodo=2026/10 parte=PT26/00314 registro_ids=[2]")
    assert not [x for x in caplog.records
                if "no escritas por parte no abierto" in x.getMessage()]
    assert "Persona" not in caplog.text


def _falla_en(cli, metodo: str, llamada: int):
    original = getattr(cli, metodo)
    n = {"v": 0}

    def envoltura(*a, **k):
        n["v"] += 1
        if n["v"] == llamada:
            raise RuntimeError(f"{metodo} caido")
        return original(*a, **k)
    setattr(cli, metodo, envoltura)


def test_f034_r14_falla_la_relectura_por_synckey() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")])
    _falla_en(cli, "lineas_por_synckey", 2)        # la primera es el paso 6
    with pytest.raises(RuntimeError, match="lineas_por_synckey caido"):
        _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])


def test_f034_r14_falla_la_relectura_de_partes() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")])
    cli.cerrar_al_escribir = {HMO: CERRADO}
    _falla_en(cli, "partes_del_periodo", 2)
    with pytest.raises(RuntimeError, match="partes_del_periodo caido"):
        _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])


def test_f034_r14_falla_la_relectura_por_ide() -> None:
    cli = _pisado()
    _falla_en(cli, "lineas_por_ide", 1)
    with pytest.raises(RuntimeError, match="lineas_por_ide caido"):
        _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)],
                                pisar_claves={CLAVE})


def test_f034_r8_todo_corre_bajo_el_lock() -> None:
    """`vigilar_lock`: elegir, escribir y releer (synckey, ide y partes),
    con el lock del pipeline tomado; si no, el doble lanza."""
    cli = _pisado(cerrar={HMO: CERRADO})
    lock = threading.Lock()
    cli.vigilar_lock(lock)
    r = _pipeline(cli, lock=lock).ejecutar(obra=_obra(), lineas=[_lin(1)],
                                           pisar_claves={CLAVE})
    assert [o["registro_id"] for o in r.omitidas] == [1]
    assert cli.llamadas.count("partes_del_periodo") == 2
    assert "lineas_por_ide" in cli.llamadas
    assert not lock.locked()


# ------- T12 · que pisada cuenta como «viva» (mutantes #4 y #5) ------- #

def test_f034_t12_pisada_con_can_nulo_no_esta_viva() -> None:
    """`can` NULL es 0, como `ISNULL(p.can, 0)` del SQL: esa pisada no
    explica nada; con los dos partes cerrados, lo impidio el elegido.
    Enmienda de F-053 (R5): sin horas ni siquiera choca (no hay pisado);
    el criterio de «viva» lo fija `test_f053_r5_tiene_horas`."""
    cli = _pisado(cerrar={HMO: CERRADO, 905: IMPUTADO},
                  lineas=[dict(_linea_sigrid(4001, HMO), can=None)])
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)],
                                pisar_claves={CLAVE})
    (om,) = r.omitidas
    assert om["motivo"].startswith(
        "parte_no_abierto: el parte PT26/00400 ya no esta En registro "
        "(Imputado)")
    assert r.anuladas == 0 and r.pisadas == []


def test_f034_t12_pisada_con_una_hora_si_esta_viva() -> None:
    """Una pisada con `can = 1` sigue con horas: es la que lo impidio."""
    cli = _pisado(cerrar={HMO: CERRADO},
                  lineas=[_linea_sigrid(4001, HMO, can=1.0)])
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)],
                                pisar_claves={CLAVE})
    assert r.omitidas == [{"registro_id": 1, "motivo": MOTIVO_314_CERRADO}]
    assert _sincronizadas(cli) == {}
