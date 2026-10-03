# tests/test_f019_reglas.py
"""F-019 · ReglasRegistro con el interruptor MENSUALES_A_DEDICACION.

T1 (R1): tests de CARACTERIZACION escritos contra el codigo anterior a
F-019. Fijan lo que `ReglasRegistro` decide hoy para un mensual sin HE*,
un capataz MCAP+HECAP, un trabajador por horas, incidencias de inicio,
intermedio y fin, lineas sin recurso, sin horas y de tipo raro. Tienen que
seguir en verde con el interruptor apagado (el valor por defecto).

Sin red: tipos de hora sinteticos en memoria (codigos y precios
inventados, sin nombres reales ni DNIs).
"""
from __future__ import annotations

import pytest
from application.services.reglas_registro import (
    MOTIVO_INTERMEDIO,
    MOTIVO_SIN_CI,
    MOTIVO_SIN_CIZ,
    MOTIVO_SIN_EXTRA,
    MOTIVO_SIN_HORAS,
    MOTIVO_SIN_LABORABLE,
    MOTIVO_SIN_RECURSO,
    MOTIVO_TIPO,
    ReglasRegistro,
)
from domain.models.registro_models import HoraRecurso, LineaEntrada

FECHA = 20260302

# Tipos de hora (horide sinteticos).
HL, HE, CIV, CIZ, MENC, MCAP, HECAP = 1, 2, 3, 4, 5, 6, 7


def _h(horide: int, cod: str, pre: float = 10.0) -> HoraRecurso:
    return HoraRecurso(horide=horide, cod=cod, res=None, pre=pre)


#: Recurso -> tipos de hora de su ficha (`reshor`).
HORAS = {
    # Trabajador por horas: HL + HE + incidencias.
    601: [_h(HL, "HL01", 12.0), _h(HE, "HE01", 15.0), _h(CIV, "CIV", 1.0),
          _h(CIZ, "CIZ", 2.0)],
    # Mensual sin HE* (encargado): solo su codigo mensual + incidencias.
    602: [_h(MENC, "MENC", 0.0), _h(CIV, "CIV", 1.0), _h(CIZ, "CIZ", 2.0)],
    # Capataz MCAP + HECAP: mensual que cobra sus extras.
    603: [_h(MCAP, "MCAP", 0.0), _h(HECAP, "HECAP", 18.0),
          _h(CIV, "CIV", 1.0), _h(CIZ, "CIZ", 2.0)],
    # Mensual sin codigos de incidencia.
    604: [_h(MENC, "MENC", 0.0)],
    # Mensual con incidencia de inicio pero sin CIZ.
    605: [_h(MENC, "MENC", 0.0), _h(CIV, "CIV", 1.0)],
}


def _lin(rid: int, recurso: int | None = 601, tipo: str | None = "normal",
         horas: float | None = 8.0, **kw) -> LineaEntrada:
    return LineaEntrada(registro_id=rid, fecha_int=FECHA,
                        recurso_ide=recurso, tipo_hora=tipo, horas=horas,
                        nombre=f"Persona {rid}", **kw)


def _inc(rid: int, recurso: int | None = 602, rol: str | None = "inicio",
         **kw) -> LineaEntrada:
    kw.setdefault("hora_ide", CIV)
    kw.setdefault("hora_codigo", "CIV")
    return LineaEntrada(registro_id=rid, fecha_int=FECHA,
                        recurso_ide=recurso, es_incidencia=True,
                        incidencia_rol=rol, incidencia_codigo="V",
                        nombre=f"Persona {rid}", **kw)


def _resumen(a) -> tuple:
    """Lo que decide la regla, sin los campos que copia de la linea."""
    return (a.accion, a.motivo, a.hora_ide, a.hora_codigo, a.can, a.pre,
            a.tot)


#: (caso, linea, decision de HOY). Es la caracterizacion de R1.
CASOS_HOY = [
    ("horas_ordinaria", _lin(1, 601, "normal", 8.0),
     ("escribir", None, HL, "HL01", 8.0, 12.0, 96.0)),
    ("horas_extra_negativa", _lin(2, 601, "extra", -1.5),
     ("escribir", None, HE, "HE01", -1.5, 15.0, -22.5)),
    ("horas_inc_inicio", _inc(3, 601, "inicio"),
     ("escribir", None, CIV, "CIV", 0.0, 1.0, 0.0)),
    ("mensual_ordinaria", _lin(10, 602, "normal", 8.0),
     ("omitir", MOTIVO_SIN_EXTRA, None, None, None, None, None)),
    ("mensual_extra", _lin(11, 602, "extra", 2.0),
     ("omitir", MOTIVO_SIN_EXTRA, None, None, None, None, None)),
    ("mensual_inc_inicio", _inc(12, 602, "inicio"),
     ("escribir", None, CIV, "CIV", 0.0, 1.0, 0.0)),
    ("mensual_inc_intermedio", _inc(13, 602, "intermedio"),
     ("omitir", MOTIVO_INTERMEDIO, None, None, None, None, None)),
    ("mensual_inc_fin", _inc(14, 602, "fin"),
     ("escribir", None, CIZ, "CIZ", 0.0, 2.0, 0.0)),
    ("mensual_inc_sin_rol", _inc(15, 602, None),
     ("escribir", None, CIV, "CIV", 0.0, 1.0, 0.0)),
    ("mensual_sin_ci", _inc(16, 604, "inicio"),
     ("omitir", MOTIVO_SIN_CI, None, None, None, None, None)),
    ("mensual_sin_ciz", _inc(17, 605, "fin"),
     ("omitir", MOTIVO_SIN_CIZ, None, None, None, None, None)),
    ("mensual_ci_no_casa", _inc(18, 602, "inicio", hora_ide=None,
                                hora_codigo="CIX"),
     ("omitir", f"{MOTIVO_SIN_CI} (codigo leido: CIX)", None, None, None,
      None, None)),
    ("capataz_ordinaria", _lin(20, 603, "normal", 8.0),
     ("omitir", MOTIVO_SIN_LABORABLE, None, None, None, None, None)),
    ("capataz_extra", _lin(21, 603, "extra", 2.0),
     ("escribir", None, HECAP, "HECAP", 2.0, 18.0, 36.0)),
    ("capataz_inc_inicio", _inc(22, 603, "inicio"),
     ("escribir", None, CIV, "CIV", 0.0, 1.0, 0.0)),
    ("capataz_inc_intermedio", _inc(23, 603, "intermedio"),
     ("omitir", MOTIVO_INTERMEDIO, None, None, None, None, None)),
    ("capataz_inc_fin", _inc(24, 603, "fin"),
     ("escribir", None, CIZ, "CIZ", 0.0, 2.0, 0.0)),
    ("sin_recurso", _lin(30, None, "normal", 8.0),
     ("omitir", MOTIVO_SIN_RECURSO, None, None, None, None, None)),
    ("sin_recurso_inc", _inc(31, None, "inicio"),
     ("omitir", MOTIVO_SIN_RECURSO, None, None, None, None, None)),
    ("sin_recurso_inc_intermedio", _inc(32, None, "intermedio"),
     ("omitir", MOTIVO_INTERMEDIO, None, None, None, None, None)),
    ("mensual_sin_horas", _lin(33, 602, "normal", 0.0),
     ("omitir", MOTIVO_SIN_HORAS, None, None, None, None, None)),
    ("mensual_horas_nulas", _lin(34, 602, "extra", None),
     ("omitir", MOTIVO_SIN_HORAS, None, None, None, None, None)),
    ("mensual_tipo_raro", _lin(35, 602, "nocturna", 8.0),
     ("omitir", f"{MOTIVO_TIPO}: 'nocturna'", None, None, None, None, None)),
    ("mensual_tipo_nulo", _lin(36, 602, None, 8.0),
     ("omitir", f"{MOTIVO_TIPO}: None", None, None, None, None, None)),
    ("mensual_tipo_mayusculas", _lin(37, 602, " Normal ", 8.0),
     ("omitir", MOTIVO_SIN_EXTRA, None, None, None, None, None)),
]


# ============================ R1 · caracterizacion ============================ #

@pytest.mark.parametrize("caso,linea,esperado", CASOS_HOY,
                         ids=[c[0] for c in CASOS_HOY])
def test_f019_r1_caracterizacion_decision_de_hoy(caso, linea,
                                                 esperado) -> None:
    accion = ReglasRegistro(HORAS).decidir(linea)
    assert _resumen(accion) == esperado, caso
    assert accion.registro_id == linea.registro_id
    assert accion.recurso_ide == linea.recurso_ide


def test_f019_r1_caracterizacion_la_omision_previa_manda() -> None:
    """F-023: la verificacion del recurso manda sobre cualquier regla."""
    reglas = ReglasRegistro(HORAS, omisiones={40: "recurso de baja",
                                              41: "recurso de baja"})
    for linea in (_lin(40, 601, "normal", 8.0), _inc(41, 602, "inicio")):
        assert _resumen(reglas.decidir(linea)) == (
            "omitir", "recurso de baja", None, None, None, None, None)


# ===================== T2 · interruptor encendido (R2-R4) ===================== #

def _on(horas=None, **kw) -> ReglasRegistro:
    return ReglasRegistro(HORAS if horas is None else horas,
                          mensuales_a_dedicacion=True, **kw)


def _dedicacion(a) -> tuple:
    return (a.accion, a.codigo_mes, a.hora_ide, a.hora_codigo, a.can,
            a.pre, a.tot)


def test_f019_r1_el_interruptor_nace_apagado() -> None:
    """Sin el argumento, ninguna linea sale a dedicacion (R1, DA8)."""
    reglas = ReglasRegistro(HORAS)
    for _caso, linea, _esperado in CASOS_HOY:
        accion = reglas.decidir(linea)
        assert accion.accion != "dedicacion"
        assert accion.codigo_mes is None


def test_f019_r1_apagado_explicito_decide_como_hoy() -> None:
    reglas = ReglasRegistro(HORAS, mensuales_a_dedicacion=False)
    for caso, linea, esperado in CASOS_HOY:
        assert _resumen(reglas.decidir(linea)) == esperado, caso


@pytest.mark.parametrize("linea", [
    _lin(50, 602, "normal", 8.0),          # ordinaria de un mensual
    _lin(51, 602, "extra", 2.0),           # extra de un mensual SIN HE*
    _lin(52, 602, "extra", -1.0),          # extra negativa, sin HE*
    _inc(53, 602, "inicio"),               # incidencia de inicio
    _inc(54, 602, "intermedio"),           # intermedio (decision 2)
    _inc(55, 602, "fin"),                  # fin
    _inc(56, 602, None),                   # sin rol
    _inc(57, 604, "inicio"),               # mensual sin CI*
    _inc(58, 605, "fin"),                  # mensual sin CIZ
], ids=["ordinaria", "extra_sin_he", "extra_negativa", "inc_inicio",
        "inc_intermedio", "inc_fin", "inc_sin_rol", "inc_sin_ci",
        "inc_sin_ciz"])
def test_f019_r2_mensual_va_a_dedicacion_con_su_codigo(linea) -> None:
    accion = _on().decidir(linea)
    assert _dedicacion(accion) == ("dedicacion", "MENC", None, None, None,
                                   None, None)
    assert accion.motivo == (
        "recurso mensual (MENC): sus horas van a dedicacion, no a Sigrid")
    assert (accion.registro_id, accion.recurso_ide) == (
        linea.registro_id, linea.recurso_ide)


@pytest.mark.parametrize("linea", [
    _lin(60, 603, "normal", 8.0), _inc(61, 603, "inicio"),
    _inc(62, 603, "intermedio"), _inc(63, 603, "fin"),
], ids=["ordinaria", "inc_inicio", "inc_intermedio", "inc_fin"])
def test_f019_r2_capataz_ordinarias_e_incidencias_a_dedicacion(linea) -> None:
    accion = _on().decidir(linea)
    assert (accion.accion, accion.codigo_mes) == ("dedicacion", "MCAP")


@pytest.mark.parametrize("cod", ["MCAP", "m01", "Menc"])
def test_f019_r2_es_mensual_por_el_prefijo_m(cod) -> None:
    assert HoraRecurso(horide=1, cod=cod, res=None, pre=0.0).es_mensual


@pytest.mark.parametrize("cod", ["HL01", "HE01", "CIV", "", None, "XM"])
def test_f019_r2_no_es_mensual_sin_el_prefijo(cod) -> None:
    assert not HoraRecurso(horide=1, cod=cod, res=None, pre=0.0).es_mensual


def test_f019_r2_con_dos_m_se_elige_el_primero_por_codigo() -> None:
    horas = {700: [_h(9, "MZZ"), _h(8, "MAA"), _h(7, "MKK")]}
    accion = _on(horas).decidir(_lin(70, 700, "normal", 8.0))
    assert (accion.accion, accion.codigo_mes) == ("dedicacion", "MAA")


def test_f019_r3_extra_de_capataz_sigue_a_sigrid_con_su_he() -> None:
    """DA4 opcion 2: la extra del MCAP+HECAP se escribe como hoy (R4)."""
    for horas in (2.0, -1.0):
        accion = _on().decidir(_lin(64, 603, "extra", horas))
        assert _resumen(accion) == (
            "escribir", None, HECAP, "HECAP", horas, 18.0,
            round(horas * 18.0, 2))
        assert accion.codigo_mes is None


CASOS_R4 = [
    ("tipo_raro", _lin(80, 602, "nocturna", 8.0),
     ("omitir", f"{MOTIVO_TIPO}: 'nocturna'")),
    ("tipo_nulo", _lin(81, 602, None, 8.0),
     ("omitir", f"{MOTIVO_TIPO}: None")),
    ("sin_recurso", _lin(82, None, "normal", 8.0),
     ("omitir", MOTIVO_SIN_RECURSO)),
    ("sin_recurso_inc", _inc(83, None, "inicio"),
     ("omitir", MOTIVO_SIN_RECURSO)),
    ("sin_recurso_intermedio", _inc(84, None, "intermedio"),
     ("omitir", MOTIVO_INTERMEDIO)),
    ("sin_horas", _lin(85, 602, "normal", 0.0),
     ("omitir", MOTIVO_SIN_HORAS)),
    ("horas_nulas", _lin(86, 603, "extra", None),
     ("omitir", MOTIVO_SIN_HORAS)),
]


@pytest.mark.parametrize("caso,linea,esperado", CASOS_R4,
                         ids=[c[0] for c in CASOS_R4])
def test_f019_r4_antes_que_r2_mandan_las_omisiones_de_siempre(
        caso, linea, esperado) -> None:
    accion = _on().decidir(linea)
    assert (accion.accion, accion.motivo) == esperado, caso
    assert accion.codigo_mes is None


def test_f019_r4_la_omision_previa_manda_sobre_dedicacion() -> None:
    reglas = _on(omisiones={90: "el recurso es de otra empresa",
                            91: "el recurso es de otra empresa"})
    for linea in (_lin(90, 602, "normal", 8.0), _inc(91, 602, "inicio")):
        accion = reglas.decidir(linea)
        assert (accion.accion, accion.motivo) == (
            "omitir", "el recurso es de otra empresa")


def test_f019_r4_una_incidencia_sin_horas_si_va_a_dedicacion() -> None:
    """`sin horas` solo omite lineas que NO son incidencia."""
    accion = _on().decidir(_inc(92, 602, "inicio", horas=0.0))
    assert accion.accion == "dedicacion"


def test_f019_r2_un_trabajador_por_horas_no_cambia() -> None:
    reglas = _on()
    assert _resumen(reglas.decidir(_lin(93, 601, "normal", 8.0))) == (
        "escribir", None, HL, "HL01", 8.0, 12.0, 96.0)
    assert _resumen(reglas.decidir(_inc(94, 601, "fin"))) == (
        "escribir", None, CIZ, "CIZ", 0.0, 2.0, 0.0)


# ================= R3 bis · producto de combinaciones (no regresion) ========== #

#: Codigos por familia; el recurso combina las que esten encendidas.
FAMILIAS = {"M": [_h(MENC, "MENC", 0.0)], "HE": [_h(HE, "HE01", 15.0)],
            "HL": [_h(HL, "HL01", 12.0)],
            "CI": [_h(CIV, "CIV", 1.0), _h(CIZ, "CIZ", 2.0)]}


def _combinaciones() -> dict[int, tuple[frozenset, list[HoraRecurso]]]:
    """Las 16 fichas posibles: con/sin M*, HE*, HL* y CI*."""
    out = {}
    nombres = list(FAMILIAS)
    for mascara in range(16):
        activas = frozenset(n for i, n in enumerate(nombres)
                            if mascara & (1 << i))
        out[800 + mascara] = (activas, [h for n in nombres if n in activas
                                        for h in FAMILIAS[n]])
    return out


def _lineas_producto(recursos: list[int | None]) -> list[LineaEntrada]:
    """Por recurso: ordinaria, extra y tipo raro con horas 8, 0, -2 y
    nulas; incidencias de inicio, intermedio, fin y sin rol, con 0 y 8."""
    lineas: list[LineaEntrada] = []
    rid = 1000
    for recurso in recursos:
        for tipo in ("normal", "extra", "raro"):
            for horas in (8.0, 0.0, -2.0, None):
                rid += 1
                lineas.append(_lin(rid, recurso, tipo, horas))
        for rol in ("inicio", "intermedio", "fin", None):
            for horas in (0.0, 8.0):
                rid += 1
                lineas.append(_inc(rid, recurso, rol, horas=horas))
    return lineas


def _reglas_producto():
    combos = _combinaciones()
    horas = {r: fila for r, (_f, fila) in combos.items()}
    return (combos, ReglasRegistro(horas),
            ReglasRegistro(horas, mensuales_a_dedicacion=True))


def test_f019_r3bis_encender_solo_cambia_lo_permitido() -> None:
    combos, apagado, encendido = _reglas_producto()
    lineas = _lineas_producto([*combos, None])
    cambios = {"omitir": 0, "escribir": 0}
    for linea in lineas:
        antes, ahora = apagado.decidir(linea), encendido.decidir(linea)
        familias = (combos[linea.recurso_ide][0] if linea.recurso_ide
                    else frozenset())
        clave = (linea.registro_id, linea.recurso_ide, sorted(familias),
                 linea.tipo_hora, linea.incidencia_rol, linea.horas)
        if _resumen(antes) + (antes.codigo_mes,) == \
                _resumen(ahora) + (ahora.codigo_mes,):
            continue
        # Lo unico que puede cambiar: ir a dedicacion, y solo un mensual.
        assert ahora.accion == "dedicacion", clave
        assert "M" in familias, clave
        assert ahora.codigo_mes == "MENC", clave
        # (i) omitir -> dedicacion; (ii) incidencia escribir -> dedicacion.
        assert antes.accion == "omitir" or (
            antes.accion == "escribir" and linea.es_incidencia), clave
        cambios[antes.accion] += 1
    # El producto no es trivial: los dos cambios permitidos aparecen.
    assert cambios["omitir"] > 0 and cambios["escribir"] > 0
    assert len(lineas) == 17 * 20


def test_f019_r3bis_las_extras_de_un_mensual_con_he_siguen_a_sigrid() -> None:
    combos, _apagado, encendido = _reglas_producto()
    vistas = 0
    for recurso, (familias, _fila) in combos.items():
        if not {"M", "HE"} <= familias:
            continue
        for h in (8.0, -2.0):
            accion = encendido.decidir(_lin(1, recurso, "extra", h))
            assert (accion.accion, accion.hora_codigo, accion.can) == (
                "escribir", "HE01", h)
            vistas += 1
    assert vistas == 8


def test_f019_r3bis_ninguna_omitida_pasa_a_escribir() -> None:
    combos, apagado, encendido = _reglas_producto()
    for linea in _lineas_producto([*combos, None]):
        if apagado.decidir(linea).accion == "omitir":
            assert encendido.decidir(linea).accion in ("omitir",
                                                       "dedicacion")


def test_f019_r3bis_nada_de_un_recurso_sin_m_cambia() -> None:
    combos, apagado, encendido = _reglas_producto()
    sin_m = [r for r, (f, _x) in combos.items() if "M" not in f]
    assert len(sin_m) == 8
    for linea in _lineas_producto([*sin_m, None]):
        assert _resumen(apagado.decidir(linea)) == \
            _resumen(encendido.decidir(linea))


def test_f019_r3bis_mensual_con_hl_y_he_sigue_escribiendo_ordinarias() -> None:
    """R2 frente a R3 bis en una ficha que hoy no existe (M*+HL*+HE*):
    manda R3 bis, lo que hoy se escribe y no es incidencia no cambia."""
    horas = {710: [_h(MENC, "MENC"), _h(HL, "HL01", 12.0),
                   _h(HE, "HE01", 15.0)],
             711: [_h(MENC, "MENC"), _h(HL, "HL01", 12.0)]}
    reglas = _on(horas)
    assert _resumen(reglas.decidir(_lin(71, 710, "normal", 8.0))) == (
        "escribir", None, HL, "HL01", 8.0, 12.0, 96.0)
    # Sin HE* hoy se omite entera: encendido va a dedicacion (R2).
    accion = reglas.decidir(_lin(72, 711, "normal", 8.0))
    assert (accion.accion, accion.codigo_mes) == ("dedicacion", "MENC")


# ============================ ajuste del interruptor =========================== #

@pytest.fixture
def entorno(monkeypatch, tmp_path):
    monkeypatch.setenv("SIGRID_API_BASE_URL", "http://sigrid.invalido")
    monkeypatch.setenv("SIGRID_API_FUNCTION_KEY", "clave-de-test")
    monkeypatch.delenv("MENSUALES_A_DEDICACION", raising=False)
    monkeypatch.chdir(tmp_path)          # que no se cuele un .env local
    return monkeypatch


def test_f019_r1_el_ajuste_nace_apagado(entorno) -> None:
    from config.settings import Settings
    assert Settings().mensuales_a_dedicacion is False


@pytest.mark.parametrize("valor,esperado", [("true", True), ("1", True),
                                            ("false", False)])
def test_f019_r2_el_ajuste_se_lee_del_entorno(entorno, valor,
                                              esperado) -> None:
    from config.settings import Settings
    entorno.setenv("MENSUALES_A_DEDICACION", valor)
    assert Settings().mensuales_a_dedicacion is esperado
