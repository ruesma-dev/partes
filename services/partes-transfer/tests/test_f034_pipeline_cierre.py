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


def test_f034_doble_borrar_solo_en_parte_abierto() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314", est=CERRADO),
                       _parte(905, "PT26/00400")],
               lineas=[_linea_sigrid(4001, HMO), _linea_sigrid(4002, 905)])
    assert cli.escribir([cli.stmt_borrar_linea(4001),
                         cli.stmt_borrar_linea(4002)]) == 1
    assert [l["ide"] for l in cli.lineas] == [4001]


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


# ============ Pisado confirmado: R4 y `borradas` por relectura (T6) ============ #

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
    ventana: su `DELETE` no entra y la linea nueva TAMPOCO (R4), aunque su
    parte (el elegido) siga En registro. Sin R4 habria horas duplicadas."""
    cli = _pisado(cerrar={HMO: CERRADO})
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)],
                                pisar_claves={CLAVE})
    assert r.pisadas == [CLAVE]
    assert [l["ide"] for l in cli.lineas] == [4001]       # la ajena sigue
    assert _sincronizadas(cli) == {}                      # la nueva no
    assert r.borradas == 0                                # R12


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
    assert [s["op"] for s in enviadas] == ["borrar", "insert", "insert"]


def test_f034_r12_borradas_cuenta_lo_que_ya_no_esta() -> None:
    """Sin cierre, el pisado borra la ajena: `borradas` = 1 por relectura."""
    cli = _pisado()
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)],
                                pisar_claves={CLAVE})
    assert r.borradas == 1
    assert _sincronizadas(cli) == {905: [1]}
    assert 4001 not in {l["ide"] for l in cli.lineas}
    assert cli.ides_leidos == [[4001]]


def test_f034_r12_borradas_cuenta_varias_pisadas_por_relectura() -> None:
    """Dos ajenas del mismo recurso, dia y tipo (en 900 y en 905): se
    pisan las dos; si 900 se cierra, solo cuenta la de 905."""
    lineas = [_linea_sigrid(4001, HMO), _linea_sigrid(4002, 905)]
    cli = _pisado(cerrar={HMO: CERRADO}, lineas=lineas)
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)],
                                pisar_claves={CLAVE})
    assert r.borradas == 1
    assert [l["ide"] for l in cli.lineas] == [4001]
    assert _sincronizadas(cli) == {}                  # R4: 4001 sigue viva
    assert cli.ides_leidos == [[4001, 4002]]


def test_f034_r12_pisada_que_queda_a_cero_cuenta_como_viva_no_borrada() -> None:
    """R12 cuenta las que YA NO ESTAN; una que siguiera con `can = 0` no se
    ha borrado (y, por R4, no bloquea la nueva)."""
    cli = _pisado()
    # Simula un pisado que deja la fila a 0 en vez de borrarla (F-053).
    cli.stmt_borrar_linea = lambda ide: {"op": "a_cero", "ide": ide}
    original = cli.escribir

    def escribir(sts):
        for s in sts:
            if s["op"] == "a_cero":
                next(l for l in cli.lineas if l["ide"] == s["ide"])["can"] = 0
        return original([s for s in sts if s["op"] != "a_cero"])
    cli.escribir = escribir
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)],
                                pisar_claves={CLAVE})
    assert r.borradas == 0
    assert _sincronizadas(cli) == {905: [1]}


def test_f034_r12_sin_pisadas_no_relee_por_ide() -> None:
    cli = _cli(partes=[_parte(HMO, "PT26/00314")])
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    assert r.borradas == 0 and cli.ides_leidos == []
    assert "lineas_por_ide" not in cli.llamadas


def test_f034_r12_conflicto_no_confirmado_no_cuenta_ni_se_relee() -> None:
    cli = _pisado()
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    assert [c.clave for c in r.pendientes_confirmacion] == [CLAVE]
    assert r.borradas == 0 and cli.ides_leidos == []
