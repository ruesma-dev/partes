# tests/test_f016_validacion_jornada_admin.py
"""F-016 · Las reglas puras de la pantalla de `empleado_jornada`.

Aqui esta el riesgo real de la feature: una fila mal guardada cambia que
horas cuenta sv3 como extra y acaba en Sigrid. Por eso las validaciones
se prueban SIN app, SIN BBDD y SIN reloj: son funciones puras sobre
tipos del estandar.

Cubre R7 (ultimo dia incluido <-> `hasta` exclusivo), R8 (jornada
semanal o patron), R9 (horas del patron), R10 (rango de la semanal),
R11 (fechas), R12 (solape) y R18 (normalizacion del DNI).

DNIs sinteticos a proposito: en esta suite no aparece ningun DNI ni
nombre de persona real.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from application.services.jornada_admin import (
    EntradaJornada,
    JornadaInvalida,
    a_hasta_exclusivo,
    a_ultimo_dia_incluido,
    buscar_solape,
    describir_conflicto,
    entrada_desde_fila,
    normalizar_entrada,
    ultimo_dia_incluido_de_fila,
    validar_entrada,
)

DNI = "AAA1"
OTRO_DNI = "BBB2"


def _datos(**kw) -> dict:
    """Cuerpo minimo valido del formulario, con lo que se quiera pisar."""
    base = {
        "dni": DNI,
        "jornada_semanal": "40",
        "desde": "2026-07-01",
        "hasta_inclusivo": None,
        "nota": None,
    }
    base.update(kw)
    return base


def _patron(**kw) -> dict:
    dias = {"h_lun": "8", "h_mar": "8", "h_mie": "8", "h_jue": "8",
            "h_vie": "8", "h_sab": "0", "h_dom": "0"}
    dias.update(kw)
    return dias


def _fila(id: int, desde: str, hasta: str | None, *,
          dni: str = DNI, activa: bool = True) -> dict:
    """Fila de `empleado_jornada` tal como la devuelve el repositorio."""
    return {
        "id": id, "dni_norm": dni, "jornada_semanal": 40.0,
        "h_lun": None, "h_mar": None, "h_mie": None, "h_jue": None,
        "h_vie": None, "h_sab": None, "h_dom": None,
        "desde": desde, "hasta": hasta, "origen": "manual", "nota": None,
        "is_active": activa,
    }


# =================== R7 · el humano nunca ve `hasta` =================== #

def test_f016_r7_hasta_exclusivo() -> None:
    """El ultimo dia incluido se guarda como `hasta` = ese dia + 1."""
    # Alta con ultimo dia incluido 31/07 => en BBDD 2026-08-01.
    entrada = normalizar_entrada(_datos(hasta_inclusivo="2026-07-31"))
    assert entrada.hasta == "2026-08-01"
    # Y al releerla, el listado vuelve a pintar 31/07.
    assert a_ultimo_dia_incluido(entrada.hasta) == "2026-07-31"


def test_f016_r7_sin_fecha_de_fin_es_hasta_nulo() -> None:
    """«Sin fin» es `hasta = NULL` en los dos sentidos."""
    assert a_hasta_exclusivo(None) is None
    assert a_hasta_exclusivo("") is None
    assert a_hasta_exclusivo("   ") is None
    assert a_ultimo_dia_incluido(None) is None
    assert a_ultimo_dia_incluido("") is None
    assert normalizar_entrada(_datos(hasta_inclusivo="")).hasta is None


def test_f016_r7_el_ida_y_vuelta_es_estable_en_366_fechas_seguidas() -> None:
    """366 dias seguidos: cambio de mes, cambio de ano y 29 de febrero.

    Si alguien "optimizara" la conversion con aritmetica de cadenas, el
    31/12 o el 28/02 bisiesto la romperian aqui y no en produccion.
    """
    dia = date(2027, 12, 1)          # cruza 2027->2028 y el 29/02/2028
    for _ in range(366):
        iso = dia.isoformat()
        assert a_ultimo_dia_incluido(a_hasta_exclusivo(iso)) == iso
        dia += timedelta(days=1)
    # El bisiesto estaba dentro del barrido, y su vecino tambien.
    assert a_hasta_exclusivo("2028-02-28") == "2028-02-29"
    assert a_hasta_exclusivo("2028-02-29") == "2028-03-01"
    assert a_hasta_exclusivo("2027-12-31") == "2028-01-01"


def test_f016_r7_un_ultimo_dia_incluido_ilegible_se_rechaza() -> None:
    for malo in ("2026-02-30", "31/07/2026", "ayer"):
        with pytest.raises(JornadaInvalida) as err:
            a_hasta_exclusivo(malo)
        assert err.value.campo == "hasta_inclusivo"


# ================= R8 · o jornada semanal, o patron ==================== #

def test_f016_r8_semanal_o_patron() -> None:
    """Sin `S` y sin patron completo la fila no dice nada: 422."""
    with pytest.raises(JornadaInvalida):
        validar_entrada(normalizar_entrada(_datos(jornada_semanal="")))


def test_f016_r8_solo_semanal_o_solo_patron_valen() -> None:
    validar_entrada(normalizar_entrada(_datos()))                    # solo S
    solo_patron = _datos(jornada_semanal="", **_patron())
    validar_entrada(normalizar_entrada(solo_patron))                 # solo patron


def test_f016_r8_semanal_y_patron_a_la_vez_se_acepta() -> None:
    """F-015 R16 da prioridad al patron; esta pantalla no la cambia."""
    entrada = normalizar_entrada(_datos(**_patron()))
    validar_entrada(entrada)
    assert entrada.jornada_semanal == 40.0
    assert entrada.patron == (8.0, 8.0, 8.0, 8.0, 8.0, 0.0, 0.0)


# ===================== R9 · las horas del patron ======================= #

def test_f016_r9_horas_patron() -> None:
    """Patron a medias (uno a seis valores): 422 nombrando el dia vacio."""
    with pytest.raises(JornadaInvalida) as err:
        normalizar_entrada(_datos(**_patron(h_jue="")))
    assert err.value.campo == "h_jue"
    assert "jueves" in err.value.motivo


def test_f016_r9_una_hora_fuera_de_rango_se_rechaza() -> None:
    for dia, valor in (("h_mie", "25"), ("h_sab", "-1")):
        with pytest.raises(JornadaInvalida) as err:
            validar_entrada(normalizar_entrada(_datos(**_patron(**{dia: valor}))))
        assert err.value.campo == dia


def test_f016_r9_una_hora_no_numerica_se_rechaza() -> None:
    with pytest.raises(JornadaInvalida) as err:
        normalizar_entrada(_datos(**_patron(h_lun="ocho")))
    assert err.value.campo == "h_lun"


def test_f016_r9_domingo_a_cero_y_coma_decimal_son_validos() -> None:
    """Domingo sin jornada es el caso normal; «6,5» es el criterio ES."""
    entrada = normalizar_entrada(_datos(**_patron(h_vie="6,5", h_dom="0")))
    validar_entrada(entrada)
    assert entrada.patron == (8.0, 8.0, 8.0, 8.0, 6.5, 0.0, 0.0)


def test_f016_r9_las_veinticuatro_horas_son_el_limite_incluido() -> None:
    entrada = normalizar_entrada(_datos(**_patron(h_lun="24")))
    validar_entrada(entrada)
    assert entrada.patron[0] == 24.0


# ================= R10 · el rango de la jornada semanal ================ #

def test_f016_r10_semanal_rango() -> None:
    for malo in ("0", "-5", "169"):
        with pytest.raises(JornadaInvalida) as err:
            validar_entrada(normalizar_entrada(_datos(jornada_semanal=malo)))
        assert err.value.campo == "jornada_semanal"


def test_f016_r10_cuarenta_y_dos_con_coma_decimal_vale() -> None:
    entrada = normalizar_entrada(_datos(jornada_semanal="42,5"))
    validar_entrada(entrada)
    assert entrada.jornada_semanal == 42.5


def test_f016_r10_ciento_sesenta_y_ocho_es_el_limite_incluido() -> None:
    validar_entrada(normalizar_entrada(_datos(jornada_semanal="168")))


def test_f016_r10_una_semanal_no_numerica_se_rechaza() -> None:
    with pytest.raises(JornadaInvalida) as err:
        normalizar_entrada(_datos(jornada_semanal="cuarenta"))
    assert err.value.campo == "jornada_semanal"


# ============================ R11 · fechas ============================= #

def test_f016_r11_fechas() -> None:
    """`desde` obligatoria y en ISO; el fin no puede ser anterior."""
    for malo in ("", None, "2026-02-30", "31/07/2026"):
        with pytest.raises(JornadaInvalida) as err:
            validar_entrada(normalizar_entrada(_datos(desde=malo)))
        assert err.value.campo == "desde"
    # Ultimo dia incluido ANTERIOR a `desde`.
    with pytest.raises(JornadaInvalida) as err:
        validar_entrada(normalizar_entrada(
            _datos(desde="2026-07-01", hasta_inclusivo="2026-06-30")))
    assert err.value.campo == "hasta_inclusivo"


def test_f016_r11_una_vigencia_de_un_solo_dia_es_valida() -> None:
    """Ultimo dia incluido IGUAL a `desde`: vale, y `hasta` = desde + 1."""
    entrada = normalizar_entrada(
        _datos(desde="2026-07-01", hasta_inclusivo="2026-07-01"))
    validar_entrada(entrada)
    assert entrada.hasta == "2026-07-02"


# ============================ R12 · solape ============================= #

#: `A` es la fila activa contra la que se compara toda la tabla de §8.1
#: del diseno: [2026-07-01, 2026-08-01), es decir, todo julio.
A = _fila(1, "2026-07-01", "2026-08-01")


def _candidata(desde: str, hasta: str | None, *, dni: str = DNI) -> EntradaJornada:
    return EntradaJornada(dni_norm=dni, jornada_semanal=40.0, patron=None,
                          desde=desde, hasta=hasta, nota=None)


@pytest.mark.parametrize(
    "desde, hasta, solapa, por_que",
    [
        ("2026-08-01", None, False, "contigua: encadenar vigencias es lo normal"),
        ("2026-07-31", None, True, "comparten el 31/07"),
        ("2026-06-01", "2026-07-01", False, "termina justo cuando A empieza"),
        ("2026-06-01", "2026-07-02", True, "comparten el 01/07"),
        ("2026-07-10", "2026-07-12", True, "contenida en A"),
        ("2026-01-01", None, True, "contiene a A"),
    ],
)
def test_f016_r12_solape(desde, hasta, solapa, por_que) -> None:
    choque = buscar_solape(_candidata(desde, hasta), [A])
    assert (choque is not None) is solapa, por_que
    if solapa:
        assert choque["id"] == 1


def test_f016_r12_otro_dni_no_solapa() -> None:
    """El solape es por `dni_norm`: dos personas no chocan entre si."""
    assert buscar_solape(_candidata("2026-07-10", None, dni=OTRO_DNI), [A]) is None


def test_f016_r12_una_fila_inactiva_no_cuenta() -> None:
    """La papelera logica no reserva vigencia."""
    inactiva = _fila(1, "2026-07-01", "2026-08-01", activa=False)
    assert buscar_solape(_candidata("2026-07-10", None), [inactiva]) is None


def test_f016_r12_al_editar_la_propia_fila_se_excluye() -> None:
    """Guardar una fila sin cambios nunca choca consigo misma."""
    misma = _candidata("2026-07-01", "2026-08-01")
    assert buscar_solape(misma, [A]) is not None            # sin excluir, choca
    assert buscar_solape(misma, [A], excluir_id=1) is None   # excluida, no


def test_f016_r12_dos_vigencias_abiertas_del_mismo_dni_chocan() -> None:
    abierta = _fila(7, "2026-01-01", None)
    assert buscar_solape(_candidata("2026-09-01", None), [abierta]) is not None


def test_f016_r12_devuelve_la_primera_fila_en_conflicto() -> None:
    """Se nombra la de `desde` menor, para que el mensaje sea estable."""
    filas = [_fila(9, "2026-07-15", None), _fila(3, "2026-07-01", None)]
    choque = buscar_solape(_candidata("2026-07-20", None), filas)
    assert choque is not None and choque["id"] == 3


def test_f016_r12_una_fila_guardada_con_fecha_ilegible_no_bloquea() -> None:
    """Las filas viejas las cargo el humano por SQL (F-015): si una trae
    basura en `desde`, no se puede comparar y no debe impedir dar de alta
    una vigencia correcta."""
    rota = _fila(4, "no-es-fecha", None)
    assert buscar_solape(_candidata("2026-07-10", None), [rota]) is None


def test_f016_r12_reactivar_compara_la_fila_tal_como_esta_guardada() -> None:
    """`entrada_desde_fila` es lo que usa «Reactivar» (R6)."""
    guardada = _fila(5, "2026-07-10", "2026-07-20", activa=False)
    entrada = entrada_desde_fila(guardada)
    assert (entrada.desde, entrada.hasta) == ("2026-07-10", "2026-07-20")
    assert buscar_solape(entrada, [A], excluir_id=5) is not None


def test_f016_r12_el_conflicto_se_describe_en_ultimo_dia_incluido() -> None:
    """El 409 nombra la fila en conflicto SIN ensenar el valor exclusivo."""
    assert describir_conflicto(A) == {
        "id": 1, "desde": "2026-07-01", "hasta_inclusivo": "2026-07-31"}


def test_f016_r12_una_fila_con_hasta_ilegible_se_pinta_tal_cual() -> None:
    """Pintar el listado no puede romperse por una fila cargada a mano."""
    assert ultimo_dia_incluido_de_fila("basura") == "basura"
    assert ultimo_dia_incluido_de_fila(None) is None
    assert ultimo_dia_incluido_de_fila("2026-08-01") == "2026-07-31"


# ========================= R18 · el DNI, igual ========================= #

#: Escrituras del MISMO documento. Ninguna es un DNI real.
VARIANTES = (" 1234-abcd ", "1234ABCD", "1234.abcd", "1234 abcd", "1234-ABCD")

BATERIA = VARIANTES + ("", None, "  ", "x1y2-z3", "00000000t", "AB-12/34")


def test_f016_r18_dni_normalizado() -> None:
    """« 1234-abcd » se guarda como `1234ABCD`."""
    assert normalizar_entrada(_datos(dni=" 1234-abcd ")).dni_norm == "1234ABCD"


def test_f016_r18_todas_las_escrituras_dan_el_mismo_dni_norm() -> None:
    """Y por eso el control de solape de R12 las ve como el mismo DNI."""
    normalizados = {normalizar_entrada(_datos(dni=v)).dni_norm for v in VARIANTES}
    assert normalizados == {"1234ABCD"}


def test_f016_r18_la_pantalla_normaliza_igual_que_la_lectura_de_f015() -> None:
    """Si la pantalla y el proveedor de jornadas divergieran, una
    excepcion dada de alta aqui dejaria de casar con su trabajador en
    produccion y nadie se enteraria. Este test se pone rojo antes."""
    from application.services.jornada_provider import fila_desde_dict

    for entrada in BATERIA:
        por_la_lectura = fila_desde_dict({"dni_norm": entrada}).dni_norm
        if not por_la_lectura:
            # La pantalla ademas EXIGE DNI: un vacio no llega a guardarse.
            with pytest.raises(JornadaInvalida):
                normalizar_entrada(_datos(dni=entrada))
            continue
        assert normalizar_entrada(_datos(dni=entrada)).dni_norm == por_la_lectura


def test_f016_r18_un_dni_vacio_se_rechaza() -> None:
    for vacio in ("", "   ", None, "----"):
        with pytest.raises(JornadaInvalida) as err:
            normalizar_entrada(_datos(dni=vacio))
        assert err.value.campo == "dni"


def test_f016_r18_la_edicion_ignora_el_dni_del_cuerpo() -> None:
    """R4: cambiar de trabajador es cerrar una fila y crear otra."""
    entrada = normalizar_entrada(_datos(dni=OTRO_DNI), dni_fijo="1234ABCD")
    assert entrada.dni_norm == "1234ABCD"


# =========================== la nota, a 255 ============================ #

def test_f016_una_nota_larga_se_recorta_a_255() -> None:
    entrada = normalizar_entrada(_datos(nota="x" * 400))
    assert entrada.nota is not None and len(entrada.nota) == 255


def test_f016_una_nota_vacia_se_guarda_como_nula() -> None:
    assert normalizar_entrada(_datos(nota="   ")).nota is None
