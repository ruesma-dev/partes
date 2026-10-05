# tests/test_f031_pipeline_estado.py
"""F-031 · A-C: el parte destino segun el estado de los partes del periodo.

sv5 nunca escribe en un parte que no este En registro («cerrado» = Cerrado
o Imputado, decision del humano del 2026-10-06): las lineas van a un parte
En registro de esa obra y mes (el complementario, reutilizado o nuevo);
duplicados y pisado se miran en TODOS los partes del periodo.

Primer bloque: caracterizacion EN VERDE contra el codigo anterior a F-031
(R4, R6, R10, R32, R33). Segundo bloque: lo nuevo (design §10).

Sin red: `SigridFake` de `tests/dobles.py`. Datos SINTETICOS (obras,
codigos y nombres inventados).
"""
from __future__ import annotations

from domain.models.registro_models import (
    HoraRecurso,
    LineaEntrada,
    ObraEntrada,
    RecursoSigrid,
)
from application.pipelines.registro_pipeline import RegistroPipeline
from infrastructure.sigrid.sigrid_write_client import synckey_de
from tests.dobles import SettingsFake, SigridFake

FECHA = 20260302
CEN_OBRA = 77
HL, HE, CIV, MENC = 1, 2, 3, 5
REGISTRO, CERRADO, IMPUTADO = 1, 3, 10


def _obra(ide=10, cod="0100", empresa=1, cenide=CEN_OBRA) -> ObraEntrada:
    o = ObraEntrada(ide=ide, codigo=cod, nombre=f"Obra {cod}",
                    empresa=empresa)
    o.cenide = cenide        # como lo deja el cliente real
    return o


def _h(horide, cod, caa=None, defecto=False, pre=10.0) -> HoraRecurso:
    return HoraRecurso(horide=horide, cod=cod, res=None, pre=pre,
                       caa_cod=caa, defecto=defecto)


HORAS = {
    501: [_h(HL, "HL01", "00000.CIMO01", True), _h(HE, "HE01"),
          _h(CIV, "CIV", pre=0.0)],
    # Solo extra: sus ordinarias se OMITEN (R3 de las reglas).
    502: [_h(HE, "HE01")],
    # Sin ninguna cuenta (como Porsan, empresa 28).
    503: [_h(HL, "HL01", None, True), _h(HE, "HE01")],
    # Mensual: con el interruptor de F-019 encendido va a dedicacion.
    602: [_h(MENC, "MENC", pre=0.0)],
}

CUENTAS = [(CEN_OBRA, 1, 701, "0100.CIMO01")]


def _parte(ide, cod, est=REGISTRO, obride=10, emp=1, ano=2026,
           mes=3) -> dict:
    return {"ide": ide, "obride": obride, "ano": ano, "mes": mes,
            "cod": cod, "emp": emp, "est": est}


def _linea_sigrid(ide, hmoide, reside=501, horide=HL, synckey=None,
                  fec=FECHA) -> dict:
    return {"ide": ide, "hmoide": hmoide, "reside": reside, "fec": fec,
            "horide": horide, "hora_codigo": None, "can": 8.0,
            "tot": 80.0, "pos": 64, "synckey": synckey, "caaide": 0}


def _cli(obra=None, **kw) -> SigridFake:
    obra = obra or _obra()
    kw.setdefault("cuentas", CUENTAS)
    return SigridFake(obras={obra.codigo: obra}, horas=HORAS, **kw)


def _lin(rid, recurso=501, tipo="normal", **kw) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=FECHA,
                        recurso_ide=recurso, nombre=f"Persona {rid}",
                        tipo_hora=tipo, horas=8.0, **kw)


def _pipeline(cli, **st) -> RegistroPipeline:
    settings = SettingsFake()
    for k, v in st.items():
        setattr(settings, k, v)
    return RegistroPipeline(cliente=cli, settings=settings)


def _inserts_por_parte(cli) -> dict[int, list[int]]:
    out: dict[int, list[int]] = {}
    for l in cli.lineas:
        if l.get("synckey"):
            out.setdefault(l["hmoide"], []).append(
                int(l["synckey"].split(":")[1]))
    return out


# =============== Caracterizacion (verde ANTES de F-031) =============== #

def test_f031_r4_periodo_sin_partes_crea_el_parte_como_hoy() -> None:
    cli = _cli()
    pf = _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1)])
    (p,) = pf.partes
    assert (p.existe, p.ide, p.cod, p.creado) == \
        (False, None, "PT26/00001", False)
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    (nuevo,) = cli.partes
    assert (nuevo["cod"], nuevo["obride"], nuevo["emp"]) == \
        ("PT26/00001", 10, 1)
    assert [e["parte_cod"] for e in r.escritas] == ["PT26/00001"]
    assert _inserts_por_parte(cli) == {nuevo["ide"]: [1]}


def test_f031_r6_un_parte_en_registro_se_reutiliza() -> None:
    cli = _cli(partes=[_parte(900, "PT26/00005")])
    pf = _pipeline(cli).preflight(obra=_obra(), lineas=[_lin(1)])
    (p,) = pf.partes
    assert (p.existe, p.ide, p.cod) == (True, 900, "PT26/00005")
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1), _lin(2)])
    assert len(cli.partes) == 1                       # no crea otro
    assert _inserts_por_parte(cli) == {900: [1, 2]}
    assert {e["parte_cod"] for e in r.escritas} == {"PT26/00005"}


def test_f031_r10_synckey_en_un_parte_cerrado_es_ya_registrado() -> None:
    previa = _linea_sigrid(4001, 900, synckey=synckey_de(1))
    cli = _cli(partes=[_parte(900, "PT26/00004", est=IMPUTADO)],
               lineas=[dict(previa)])
    r = _pipeline(cli).ejecutar(obra=_obra(), lineas=[_lin(1)])
    assert r.ya_registradas == [1] and r.escritas == []
    assert cli.lineas == [previa] and len(cli.partes) == 1
    assert "escribir" not in cli.llamadas


def _decisiones(cli, lineas, **st) -> dict:
    pf = _pipeline(cli, **st).preflight(obra=_obra(), lineas=lineas)
    return {a.registro_id: (a.accion, a.motivo, a.caa_ide)
            for a in pf.acciones}


def _lote_r32() -> list[LineaEntrada]:
    return [_lin(1, 502, partida_ide=300, partida_cod="01.02"),
            _lin(2, 602, partida_ide=300, partida_cod="01.02")]


def test_f031_r32_omitir_y_dedicacion_no_dependen_del_estado() -> None:
    sin_parte = _decisiones(_cli(), _lote_r32(),
                            mensuales_a_dedicacion=True)
    cerrado = _decisiones(
        _cli(partes=[_parte(900, "PT26/00004", est=CERRADO)],
             lineas=[_linea_sigrid(4000, 900, reside=502),
                     _linea_sigrid(4002, 900, reside=602, horide=MENC)]),
        _lote_r32(), mensuales_a_dedicacion=True)
    assert cerrado == sin_parte
    assert [d[0] for d in cerrado.values()] == ["omitir", "dedicacion"]


def test_f031_r32_ya_registrado_no_depende_del_estado() -> None:
    for est in (REGISTRO, CERRADO, IMPUTADO):
        cli = _cli(partes=[_parte(900, "PT26/00004", est=est)],
                   lineas=[_linea_sigrid(4001, 900,
                                         synckey=synckey_de(1))])
        assert _decisiones(cli, [_lin(1, partida_ide=300)])[1][0] == \
            "ya_registrado"


def test_f031_r33_empresa_28_sin_cerrados_ni_cuentas_como_hoy() -> None:
    obra = _obra(20, "0724", empresa=28, cenide=0)
    cli = _cli(obra=obra, cuentas=[],
               recursos={503: RecursoSigrid(503, 28, 0, None)},
               partes=[_parte(950, "PT26/00121", obride=20, emp=28)])
    r = _pipeline(cli).ejecutar(obra=obra, lineas=[_lin(1, 503)])
    assert _inserts_por_parte(cli) == {950: [1]}
    assert [l["caaide"] for l in cli.lineas] == [0]
    assert len(cli.partes) == 1 and r.pendientes_confirmacion == []
    assert cli.cuentas_leidas == []
