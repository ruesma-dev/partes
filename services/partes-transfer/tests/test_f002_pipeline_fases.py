# tests/test_f002_pipeline_fases.py
"""F-002 · split del pipeline de registro en fases (ampliacion 1).

Dos familias de tests:

  - REGRESION: `preflight` y `ejecutar` conservan firma y resultado. El
    split mueve codigo, no cambia decisiones (`reglas_registro.py` no se
    toca). Estos tests se escribieron contra el pipeline ANTERIOR al
    refactor y pasaron con el: son la red que sujeta el movimiento.
  - FASES NUEVAS: `preparar` / `registrar`, el lock en el constructor y
    la garantia de que el estado que la escritura modifica se lee DENTRO
    del lock (R7, R19, R20).

Sin red: cliente de Sigrid en memoria (`SigridFake`) con latencias
simuladas y SIN sincronizacion propia, para que la ausencia de lock se
manifieste como fallo real y no como test verde por casualidad.
"""
from __future__ import annotations

import threading

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import (
    HoraRecurso,
    LineaEntrada,
    ObraEntrada,
)
from infrastructure.sigrid.sigrid_write_client import synckey_de
from tests.dobles import SettingsFake, SigridFake

OBRA = ObraEntrada(ide=10, codigo="0100", nombre="Obra Uno")

HORAS_COMPLETAS = [
    HoraRecurso(horide=1, cod="HL01", res=None, pre=10.0),
    HoraRecurso(horide=2, cod="HE01", res=None, pre=15.0),
]
#: Recurso mensual: tiene extra pero NO laborable (R3 -> omite ordinarias).
HORAS_MENSUAL = [HoraRecurso(horide=2, cod="HE01", res=None, pre=15.0)]


def _sigrid(**kwargs) -> SigridFake:
    return SigridFake(
        obras={"0100": OBRA, "0404": ObraEntrada(ide=99, codigo="0404",
                                                 nombre="Obra pruebas")},
        horas={501: HORAS_COMPLETAS, 502: HORAS_MENSUAL},
        **kwargs)


def _linea(registro_id: int, *, recurso_ide: int = 501,
           fecha_int: int = 20260302, tipo_hora: str = "normal",
           horas: float = 8.0) -> LineaEntrada:
    return LineaEntrada(registro_id=registro_id, fecha_int=fecha_int,
                        recurso_ide=recurso_ide, nombre=f"Trabajador {recurso_ide}",
                        tipo_hora=tipo_hora, horas=horas)


def _pipeline(cli, *, lock=None, **st) -> RegistroPipeline:
    return RegistroPipeline(cliente=cli, settings=SettingsFake(**st),
                            lock=lock)


# --------------------------------------------------------------------- #
# REGRESION: preflight/ejecutar no cambian
# --------------------------------------------------------------------- #

def test_f002_regresion_preflight_equivalente():
    """`preflight` conserva firma y veredicto por linea tras el split."""
    cli = _sigrid()
    pf = _pipeline(cli).preflight(
        obra=OBRA,
        lineas=[_linea(1), _linea(2, tipo_hora="extra", horas=2.0),
                _linea(3, recurso_ide=502)])

    assert pf.obra_destino is OBRA
    assert pf.forzada_pruebas is False
    assert (pf.n_escribir, pf.n_omitir, pf.n_ya) == (2, 1, 0)
    assert [a.hora_codigo for a in pf.acciones] == ["HL01", "HE01", None]
    # Parte inexistente: se propone correlativo, no se crea nada todavia.
    assert [(p.ano, p.mes, p.existe, p.cod) for p in pf.partes] \
        == [(2026, 3, False, "PT26/00001")]
    assert cli.partes == []


def test_f002_regresion_ejecutar_equivalente():
    """`ejecutar` crea el parte que falta y escribe las lineas decididas."""
    cli = _sigrid()
    r = _pipeline(cli).ejecutar(
        obra=OBRA,
        lineas=[_linea(1), _linea(2, tipo_hora="extra", horas=2.0),
                _linea(3, recurso_ide=502)],
        usuario="ana")

    assert r.ok is True
    assert [e["registro_id"] for e in r.escritas] == [1, 2]
    assert [o["registro_id"] for o in r.omitidas] == [3]
    assert r.ya_registradas == []
    assert r.pendientes_confirmacion == []
    assert [(p["cod"], p["ano"], p["mes"]) for p in cli.partes] \
        == [("PT26/00001", 2026, 3)]
    # Posiciones correlativas con el paso configurado y synckey por linea.
    assert [l["pos"] for l in cli.lineas] == [64, 128]
    assert [l["synckey"] for l in cli.lineas] == [synckey_de(1), synckey_de(2)]
    # El ide real de la linea vuelve en el resultado (trazabilidad).
    assert all(e.get("hmores_ide") for e in r.escritas)


def test_f002_r8_ejecutar_dos_veces_no_duplica():
    """R8: la reentrega no duplica; la segunda pasada ve las synckeys."""
    cli = _sigrid()
    pipeline = _pipeline(cli)
    lineas = [_linea(1), _linea(2, tipo_hora="extra", horas=2.0)]

    pipeline.ejecutar(obra=OBRA, lineas=lineas)
    escritas_tras_la_primera = len(cli.lineas)
    segunda = pipeline.ejecutar(
        obra=OBRA, lineas=[_linea(1), _linea(2, tipo_hora="extra", horas=2.0)])

    assert len(cli.lineas) == escritas_tras_la_primera == 2
    assert segunda.escritas == []
    assert sorted(segunda.ya_registradas) == [1, 2]


def test_f002_regresion_modo_pruebas_desvia_la_obra():
    """El modo pruebas sigue desviando a la obra de pruebas."""
    cli = _sigrid()
    pf = _pipeline(cli, obra_pruebas_forzar=True).preflight(
        obra=OBRA, lineas=[_linea(1)])
    assert pf.forzada_pruebas is True
    assert pf.obra_destino.codigo == "0404"


# --------------------------------------------------------------------- #
# FASES NUEVAS: preparar / registrar
# --------------------------------------------------------------------- #

def test_f002_preparar_devuelve_contexto_sin_tocar_estado_escrito():
    """`preparar` resuelve datos maestros y reglas; nada de partes."""
    cli = _sigrid()
    ctx = _pipeline(cli).preparar(obra=OBRA, lineas=[_linea(1), _linea(2)])

    assert ctx.obra_origen is OBRA
    assert ctx.obra_destino is OBRA
    assert ctx.forzada_pruebas is False
    assert [a.accion for a in ctx.acciones] == ["escribir", "escribir"]
    # Ni el parte, ni el correlativo, ni las synckeys: eso es fase de
    # escritura (R20).
    assert "partes_existentes" not in cli.llamadas
    assert "siguiente_cod_pt" not in cli.llamadas
    assert "lineas_por_synckey" not in cli.llamadas


def test_f002_r20_el_estado_escrito_se_lee_dentro_del_lock():
    """R20: partes, correlativo, synckeys y conflictos, bajo el lock."""
    cli = _sigrid()
    pipeline = _pipeline(cli)
    cli.vigilar_lock(pipeline.lock)      # falla si algo de eso sale fuera

    ctx = pipeline.preparar(obra=OBRA, lineas=[_linea(1)])
    r = pipeline.registrar(ctx, usuario="ana")

    assert [e["registro_id"] for e in r.escritas] == [1]
    assert {"partes_existentes", "siguiente_cod_pt", "lineas_por_synckey",
            "escribir"} <= set(cli.llamadas)


def test_f002_r7_el_lock_lo_adquiere_registrar_no_el_llamante():
    """R7: ningun llamante puede olvidar el lock; lo toma `registrar`."""
    cli = _sigrid()
    pipeline = _pipeline(cli)
    ctx = pipeline.preparar(obra=OBRA, lineas=[_linea(1)])

    pipeline.lock.acquire()
    try:
        hecho = threading.Event()
        threading.Thread(
            target=lambda: (pipeline.registrar(ctx), hecho.set()),
            daemon=True).start()
        # Con el lock tomado por otro, `registrar` NO puede progresar.
        assert not hecho.wait(0.3)
        assert cli.lineas == []
    finally:
        pipeline.lock.release()
    assert hecho.wait(2.0)
    assert len(cli.lineas) == 1


def test_f002_r19_preparar_no_espera_al_lock():
    """R19/R18: la preparacion es la fase paralela; no toca el lock."""
    cli = _sigrid()
    pipeline = _pipeline(cli)

    pipeline.lock.acquire()
    try:
        ctx = pipeline.preparar(obra=OBRA, lineas=[_linea(1)])
    finally:
        pipeline.lock.release()
    assert [a.accion for a in ctx.acciones] == ["escribir"]


def test_f002_r19_registrar_serializa_entre_peticiones():
    """R19: dos escrituras concurrentes nunca se solapan."""
    cli = _sigrid(latencia_escritura=0.05)
    pipeline = _pipeline(cli)
    cli.vigilar_lock(pipeline.lock)

    def _peticion(base: int, dia: int):
        # Cada peticion, su dia: asi las tres escriben de verdad y lo que
        # se mide es la serializacion, no el detector de conflictos.
        ctx = pipeline.preparar(
            obra=OBRA,
            lineas=[_linea(base, fecha_int=20260300 + dia),
                    _linea(base + 1, fecha_int=20260300 + dia,
                           tipo_hora="extra", horas=2.0)])
        pipeline.registrar(ctx)

    hilos = [threading.Thread(target=_peticion, args=(b, d))
             for b, d in ((100, 2), (200, 3), (300, 4))]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(10)

    assert cli.max_concurrencia.get("escribir") == 1
    assert len(cli.lineas) == 6


def test_f002_r20_dos_peticiones_misma_obra_y_mes_crean_un_solo_parte():
    """R20: el correlativo PT<AA>/NNNNN no se duplica.

    Si el parte y `siguiente_cod_pt` se evaluaran en la fase paralela,
    ambas peticiones propondrian PT26/00001 y crearian DOS cabeceras
    para la misma obra y mes.
    """
    cli = _sigrid(latencia_lectura=0.02, latencia_escritura=0.02)
    pipeline = _pipeline(cli)
    cli.vigilar_lock(pipeline.lock)
    errores: list[BaseException] = []

    def _peticion(base: int, dia: int):
        try:
            # Dias distintos del MISMO mes: un unico parte para los tres.
            ctx = pipeline.preparar(
                obra=OBRA, lineas=[_linea(base, fecha_int=20260300 + dia)])
            pipeline.registrar(ctx)
        except BaseException as exc:  # noqa: BLE001
            errores.append(exc)

    hilos = [threading.Thread(target=_peticion, args=(b, d))
             for b, d in ((100, 2), (200, 3), (300, 4))]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(10)

    assert errores == []
    assert len(cli.partes) == 1
    assert [p["cod"] for p in cli.partes] == ["PT26/00001"]
    assert len(cli.lineas) == 3
    assert len({l["pos"] for l in cli.lineas}) == 3   # sin posiciones repetidas


def test_f002_r19_el_lock_se_comparte_con_quien_lo_inyecta():
    """El lock viaja por el constructor: HTTP y colas comparten uno solo."""
    compartido = threading.Lock()
    cli = _sigrid()
    uno = _pipeline(cli, lock=compartido)
    otro = _pipeline(_sigrid(), lock=compartido)
    assert uno.lock is otro.lock is compartido


def test_f002_r10_conflictos_no_confirmados_no_se_escriben():
    """R10: sin `pisar_claves`, la linea en conflicto NO se escribe."""
    cli = _sigrid()
    cli.partes.append({"ide": 700, "obride": 10, "ano": 2026, "mes": 3,
                       "cod": "PT26/00007"})
    cli.lineas.append({"ide": 4000, "hmoide": 700, "reside": 501,
                       "fec": 20260302, "horide": 1, "hora_codigo": "HL01",
                       "can": 5.0, "tot": 50.0, "pos": 64, "synckey": None})
    pipeline = _pipeline(cli)
    ctx = pipeline.preparar(obra=OBRA, lineas=[_linea(1)])
    r = pipeline.registrar(ctx)

    assert r.escritas == []
    assert [c.clave for c in r.pendientes_confirmacion] == ["501|20260302|1"]
    assert [c.registros for c in r.pendientes_confirmacion] == [[1]]
    assert len(cli.lineas) == 1          # la existente sigue intacta


def test_f002_r10_pisar_confirmado_borra_e_inserta():
    """Con la clave confirmada, la linea anterior se borra y entra la nueva."""
    cli = _sigrid()
    cli.partes.append({"ide": 700, "obride": 10, "ano": 2026, "mes": 3,
                       "cod": "PT26/00007"})
    cli.lineas.append({"ide": 4000, "hmoide": 700, "reside": 501,
                       "fec": 20260302, "horide": 1, "hora_codigo": "HL01",
                       "can": 5.0, "tot": 50.0, "pos": 64, "synckey": None})
    pipeline = _pipeline(cli)
    ctx = pipeline.preparar(obra=OBRA, lineas=[_linea(1)])
    r = pipeline.registrar(ctx, pisar_claves={"501|20260302|1"})

    assert r.pisadas == ["501|20260302|1"]
    assert r.borradas == 1
    assert [l["ide"] for l in cli.lineas] == [5001]
    assert [e["registro_id"] for e in r.escritas] == [1]


def test_f002_registrar_exige_contexto():
    """`registrar` no acepta un contexto ausente: seria escribir a ciegas."""
    with pytest.raises(ValueError, match="ContextoRegistro"):
        _pipeline(_sigrid()).registrar(None)
