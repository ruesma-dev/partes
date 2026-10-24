# tests/test_f060_aprobacion_racha.py
"""F-060 · La racha de incidencia en la aprobacion de sv4 (R1, R6, R9-R12,
R28-R30) y en el modal (R11).

  - `lineas_para_registro`: el rol de cada incidencia con el historico de
    la persona (UNA consulta por persona), `racha_registro_ids` en cada
    linea y `avisos_racha` en cada grupo.
  - `marcar_registros_sigrid`: `movida_de` deja la linea que tenia el CIZ
    en `omitido` con `fin_movido`, con CAS, idempotente por los dos
    canales de F-002 (`aplicar_resultado`).
  - `reparto_obras`: `agregar_ejecucion` conserva `movida_de`.

Sin red ni PostgreSQL: SQLite en memoria con el MISMO ORM (`dobles.py`).
Personas, DNIs, obras y partes SINTETICOS.
"""
from __future__ import annotations

import pytest
from sqlalchemy import event

from infrastructure.database.parte_repository import ParteReviewRepository
from tests.dobles import FabricaSesionSqlite
from tests.test_f025_aprobacion import DNI_A, DNI_B, OBRA_10, OBRA_20, sembrar
from tests.test_f025_deteccion import TABLA


def _dia(n: int, mes: int = 10) -> str:
    return f"2026-{mes:02d}-{n:02d}"


def _fabrica() -> FabricaSesionSqlite:
    return FabricaSesionSqlite()


def _v(fabrica, n, *, doc=None, estado=None, mes=10, letra="V", **kw):
    """Un parte de un dia con una V (u otra letra) de la persona A."""
    return sembrar(fabrica, [{"inc": letra, "estado": estado}],
                   doc=doc or f"v{mes}-{n}-{letra}-{kw.get('dni', 'A')}",
                   fecha=_dia(n, mes), **kw)[0]


def _t(fabrica, n, *, doc=None, horas=8.0, mes=10, estado=None, **kw):
    return sembrar(fabrica, [{"horas": horas, "estado": estado}],
                   doc=doc or f"t{mes}-{n}-{kw.get('dni', 'A')}",
                   fecha=_dia(n, mes), **kw)[0]


def _datos(fabrica, ids, tabla=TABLA) -> dict:
    return ParteReviewRepository(fabrica).lineas_para_registro(
        ids, incidencias=tabla)


def _linea(datos, rid) -> dict:
    return next(l for l in datos["lineas"] if l["registro_id"] == rid)


def _roles(datos) -> dict[int, str]:
    return {l["registro_id"]: l["incidencia_rol"] for l in datos["lineas"]
            if l["es_incidencia"]}


# ============================ R1-R9 · el rol ============================ #

def test_f060_r1_r9_fin_con_las_lineas_de_la_racha() -> None:
    f = _fabrica()
    d1 = _v(f, 1, estado="registrado")
    d2 = _v(f, 2, estado="registrado")
    d3 = _v(f, 3)
    l3 = _linea(_datos(f, [d3]), d3)
    assert l3["incidencia_rol"] == "fin"
    assert l3["racha_registro_ids"] == [d1, d2]


def test_f060_r1_cualquier_obra_y_estado() -> None:
    f = _fabrica()
    d1 = _v(f, 1, obra=OBRA_20, estado="omitido")
    d2 = _v(f, 2)
    assert _linea(_datos(f, [d2]), d2)["racha_registro_ids"] == [d1]


def test_f060_r2_r3_tras_un_dia_trabajado_es_inicio() -> None:
    f = _fabrica()
    _v(f, 1)
    _t(f, 2)
    d3 = _v(f, 3)
    l3 = _linea(_datos(f, [d3]), d3)
    assert (l3["incidencia_rol"], l3["racha_registro_ids"]) == ("inicio", [])


def test_f060_r2_fuera_de_la_ventana_es_inicio() -> None:
    f = _fabrica()
    _v(f, 31, mes=8)
    d = _v(f, 1)
    assert _roles(_datos(f, [d])) == {d: "inicio"}


def test_f060_r3_otra_letra_abre_racha() -> None:
    f = _fabrica()
    _v(f, 1)
    d2 = _v(f, 2, letra="B")
    assert _roles(_datos(f, [d2])) == {d2: "inicio"}


def test_f060_r3_sin_tabla_la_letra_sale_de_los_codigos() -> None:
    f = _fabrica()
    _v(f, 1)
    d2 = _v(f, 2)
    d3 = _v(f, 3, letra="B")
    assert _roles(_datos(f, [d2, d3], tabla=None)) == {d2: "fin",
                                                       d3: "inicio"}


def test_f060_r4_ejemplo_del_humano_dia_a_dia() -> None:
    """Dia 1 V => inicio; dia 2 => fin; 3 y 4 => fin (sv5 mueve); dia 5
    con horas => trabajo; dia 6 V => inicio de una racha nueva."""
    f = _fabrica()
    roles = []
    for n in (1, 2, 3, 4):
        rid = _v(f, n)
        roles.append(_roles(_datos(f, [rid]))[rid])
    _t(f, 5)
    rid = _v(f, 6)
    roles.append(_roles(_datos(f, [rid]))[rid])
    assert roles == ["inicio", "fin", "fin", "fin", "inicio"]


def test_f060_r5_la_papelera_no_cuenta() -> None:
    f = _fabrica()
    _v(f, 1)
    sembrar(f, [{"horas": 8.0}], doc="t2", fecha=_dia(2), doc_activo=False)
    sembrar(f, [{"horas": 8.0, "borrada": True}], doc="t2b", fecha=_dia(2))
    d3 = _v(f, 3)
    assert _roles(_datos(f, [d3])) == {d3: "fin"}


def test_f060_r9_papelera_registrada_entra_en_la_racha() -> None:
    f = _fabrica()
    d1 = _v(f, 1)
    (borrada,) = sembrar(f, [{"inc": "V", "estado": "registrado",
                              "borrada": True}], doc="vb", fecha=_dia(2))
    (otra,) = sembrar(f, [{"inc": "V", "estado": "omitido",
                           "borrada": True}], doc="vo", fecha=_dia(2))
    d2 = _v(f, 2)
    d3 = _v(f, 3)
    ids = _linea(_datos(f, [d3]), d3)["racha_registro_ids"]
    assert ids == sorted([d1, d2, borrada]) and otra not in ids


def test_f060_r9_hacia_delante_tambien() -> None:
    f = _fabrica()
    d1 = _v(f, 1)
    d3 = _v(f, 3, estado="registrado")
    d2 = _v(f, 2)
    assert _linea(_datos(f, [d2]), d2)["racha_registro_ids"] == [d1, d3]


def test_f060_r9_las_demas_lineas_van_con_lista_vacia() -> None:
    f = _fabrica()
    ids = sembrar(f, [{"inc": "V"}, {"tipo": "extra", "horas": 0.0}],
                  doc="d1", fecha=_dia(1))
    t = _t(f, 2)
    datos = _datos(f, ids + [t])
    assert all(l["racha_registro_ids"] == [] for l in datos["lineas"])


def test_f060_r6_sin_dni_por_la_clave_de_trabajador() -> None:
    f = _fabrica()
    d1 = _v(f, 1, dni=None, recurso_ide=501)
    _t(f, 1, dni=None, recurso_ide=502, doc="otro")     # otra persona
    _t(f, 2, dni=None, recurso_ide=502, doc="otro2")
    d2 = _v(f, 2, dni=None, recurso_ide=501)
    l2 = _linea(_datos(f, [d2]), d2)
    assert (l2["incidencia_rol"], l2["racha_registro_ids"]) == ("fin", [d1])


def _casar_por_recurso(fabrica, *ids) -> None:
    from infrastructure.database.orm_models import ParteRegistroOrm
    with fabrica.create_session() as s:
        for rid in ids:
            reg = s.get(ParteRegistroOrm, rid)
            reg.empleado_match_method = "recurso_manual"
            reg.recurso_ide, reg.empleado_reside = None, 501
        s.commit()


def test_f060_r6_sin_ficha_ni_dni_rec_del_recurso() -> None:
    """Casada sin ficha por su recurso (F-035): `rec-501`, tambien con el
    recurso en `empleado_reside`."""
    from infrastructure.database.parte_repository import persona_de
    from infrastructure.database.orm_models import ParteRegistroOrm
    f = _fabrica()
    d1 = _v(f, 1, dni=None, empleado_ide=None)
    d2 = _v(f, 2, dni=None, empleado_ide=None)
    _t(f, 1, dni=None, empleado_ide=None, recurso_ide=502, doc="t502")
    _casar_por_recurso(f, d1, d2)
    with f.create_session() as s:
        assert persona_de(s.get(ParteRegistroOrm, d2)) == "rec-501"
    assert _linea(_datos(f, [d2]), d2)["racha_registro_ids"] == [d1]


def test_f060_r6_sin_ficha_ni_casar_por_el_nombre_leido() -> None:
    f = _fabrica()
    d1 = _v(f, 1, dni=None, empleado_ide=None)
    d2 = _v(f, 2, dni=None, empleado_ide=None)
    _t(f, 1, dni=None, empleado_ide=None, nombre="Otra", doc="otra")
    assert _linea(_datos(f, [d2]), d2)["racha_registro_ids"] == [d1]


def test_f060_r6_el_dni_se_compara_normalizado() -> None:
    f = _fabrica()
    d1 = _v(f, 1, dni="1234-5678 z")
    _t(f, 1, dni=DNI_B, doc="b1")
    d2 = _v(f, 2, dni=DNI_A)
    assert _linea(_datos(f, [d2]), d2)["racha_registro_ids"] == [d1]


def test_f060_r6_otro_dni_no_cuenta() -> None:
    f = _fabrica()
    _v(f, 1, dni=DNI_B)
    d2 = _v(f, 2, dni=DNI_A)
    assert _roles(_datos(f, [d2])) == {d2: "inicio"}


def test_f060_r7_aprobar_la_racha_de_una_vez_en_dos_obras() -> None:
    f = _fabrica()
    d1 = _v(f, 1)
    d2 = _v(f, 2, obra=OBRA_20)
    d3 = _v(f, 3)
    d4 = _v(f, 4, obra=OBRA_20)
    datos = _datos(f, [d1, d2, d3, d4])
    assert _roles(datos) == {d1: "inicio", d2: "intermedio",
                             d3: "intermedio", d4: "fin"}
    assert _linea(datos, d4)["racha_registro_ids"] == [d1, d2, d3]
    assert _linea(datos, d2)["racha_registro_ids"] == []


def test_f060_r8_dos_inicios_del_mismo_dia() -> None:
    f = _fabrica()
    a = _v(f, 1)
    b = _v(f, 1, obra=OBRA_20, doc="v1b")
    assert _roles(_datos(f, [b, a])) == {a: "inicio", b: "intermedio"}


def test_f060_r1_sin_fecha_es_inicio() -> None:
    from infrastructure.database.orm_models import ParteRegistroOrm
    f = _fabrica()
    d = _v(f, 1)
    with f.create_session() as s:
        s.get(ParteRegistroOrm, d).fecha_int = None
        s.commit()
    l = _linea(_datos(f, [d]), d)
    assert (l["incidencia_rol"], l["racha_registro_ids"]) == ("inicio", [])


# ========================= R10 · avisos_racha ========================= #

def _avisos(datos) -> list[dict]:
    return [a for g in datos["grupos"] for a in g["avisos_racha"]]


def test_f060_r10_trabajo_antes_de_una_incidencia_registrada() -> None:
    f = _fabrica()
    _v(f, 5, estado="registrado")
    t = _t(f, 4)
    datos = _datos(f, [t])
    assert [l["registro_id"] for l in datos["lineas"]] == [t]   # viaja
    (aviso,) = _avisos(datos)
    assert aviso["registro_id"] == t and aviso["fecha"] == _dia(4)
    assert aviso["nombre"] == "Persona A"
    assert aviso["motivo"].startswith("racha_desordenada: el 2026-10-05")


def test_f060_r10_inicio_antes_de_una_incidencia_registrada() -> None:
    f = _fabrica()
    _v(f, 5, estado="registrado")
    d4 = _v(f, 4, letra="B")
    assert [a["registro_id"] for a in _avisos(_datos(f, [d4]))] == [d4]


def test_f060_r10_un_fin_no_avisa() -> None:
    f = _fabrica()
    _v(f, 3)
    _v(f, 5, estado="registrado")
    d4 = _v(f, 4)
    assert _avisos(_datos(f, [d4])) == []


@pytest.mark.parametrize("estado", [None, "omitido", "encolado"])
def test_f060_r10_sin_registrar_no_avisa(estado) -> None:
    f = _fabrica()
    _v(f, 5, estado=estado)
    assert _avisos(_datos(f, [_t(f, 4)])) == []


def test_f060_r10_trabajo_a_cero_no_avisa() -> None:
    f = _fabrica()
    _v(f, 5, estado="registrado")
    assert _avisos(_datos(f, [_t(f, 4, horas=0.0)])) == []


def test_f060_r10_cada_grupo_lleva_los_suyos() -> None:
    f = _fabrica()
    _v(f, 5, estado="registrado")
    a = _t(f, 4)
    b = _t(f, 4, obra=OBRA_20, doc="t4b")
    datos = _datos(f, [a, b])
    por_grupo = {g["clave"]: [x["registro_id"] for x in g["avisos_racha"]]
                 for g in datos["grupos"]}
    assert por_grupo == {"obr-10": [a], "obr-20": [b]}


# ================= R12 · una consulta por persona ================= #

def _contar_historicos(fabrica) -> list[str]:
    vistos: list[str] = []

    @event.listens_for(fabrica.engine, "before_cursor_execute")
    def _apuntar(conn, cursor, statement, params, context, many):
        if "BETWEEN" in statement:
            vistos.append(statement)
    return vistos


def test_f060_r12_una_consulta_por_persona_y_aprobacion() -> None:
    f = _fabrica()
    ids = [_v(f, n) for n in (1, 2, 3)] + [_t(f, 4)]
    ids += [_v(f, n, dni=DNI_B, doc=f"b{n}") for n in (1, 2)]
    vistos = _contar_historicos(f)
    _datos(f, ids)
    assert len(vistos) == 2


def test_f060_r12_sin_lineas_de_trabajo_ni_incidencia_no_consulta() -> None:
    f = _fabrica()
    t = _t(f, 4, horas=0.0)
    vistos = _contar_historicos(f)
    _datos(f, [t])
    assert vistos == []


# ================ R28-R29 · el dia que tenia el CIZ ================ #

from infrastructure.database.orm_models import ParteRegistroOrm  # noqa: E402
from infrastructure.transfer.resultado_sigrid import (  # noqa: E402
    aplicar_resultado,
)
from tests.dobles import estados_sigrid  # noqa: E402

MOTIVO_X = ("fin_movido: el fin de la incidencia (CIZ, linea 9000) paso al "
            "dia 2026-10-04")


def _con_ciz(fabrica, rid: int, ide: int = 9000) -> int:
    """La linea `rid` quedo `registrado` con su CIZ en la linea `ide`."""
    with fabrica.create_session() as s:
        reg = s.get(ParteRegistroOrm, rid)
        reg.sigrid_estado = "registrado"
        reg.sigrid_hmores_ide = ide
        s.commit()
    return rid


def _movido(fabrica):
    """X (dia 3) tenia el CIZ (linea 9000); D (dia 4) se aprueba."""
    x = _con_ciz(fabrica, _v(fabrica, 3))
    d = _v(fabrica, 4)
    return x, d


def _resultado(d, x, *, ide=9000, **extra) -> dict:
    e = {"registro_id": d, "hmoide": 901, "parte_cod": "PT26/00010",
         "hora_codigo": "CIZ", "can": 0.0, "tot": 0.0, "hmores_ide": ide,
         "movida_de": x}
    e.update(extra)
    return {"ok": True, "escritas": [e], "omitidas": [],
            "ya_registradas": [], "pendientes_confirmacion": [],
            "dedicacion": [], "forzada_pruebas": False}


def _marcar(fabrica, resultado, usuario="ana") -> int:
    return aplicar_resultado(ParteReviewRepository(fabrica), resultado,
                             registro_ids=None, usuario=usuario)


def test_f060_r28_movida_de_deja_el_dia_anterior_omitido() -> None:
    f = _fabrica()
    x, d = _movido(f)
    _marcar(f, _resultado(d, x))
    est = estados_sigrid(f, [x, d])
    assert est[d] == ("registrado", None, 901, 9000, "PT26/00010")
    assert est[x][0] == "omitido" and est[x][1] == MOTIVO_X
    # Las referencias de X se quedan como traza.
    assert est[x][3] == 9000
    with f.create_session() as s:
        rx = s.get(ParteRegistroOrm, x)
        assert rx.sigrid_registrado_by == "ana"
        assert rx.sigrid_registrado_at_utc > "2026-10-01"


def test_f060_r28_motivo_cabe_en_la_columna() -> None:
    f = _fabrica()
    x, d = _movido(f)
    _marcar(f, _resultado(d, x))
    assert len(estados_sigrid(f, [x])[x][1]) <= 255


@pytest.mark.parametrize("cambio", [
    {"sigrid_estado": "omitido", "sigrid_motivo": "otro motivo"},
    {"sigrid_estado": "borrado_sigrid"},
    {"sigrid_hmores_ide": 8888},
])
def test_f060_r28_sin_cas_no_toca_y_avisa(cambio, caplog) -> None:
    f = _fabrica()
    x, d = _movido(f)
    with f.create_session() as s:
        reg = s.get(ParteRegistroOrm, x)
        for k, v in cambio.items():
            setattr(reg, k, v)
        s.commit()
    antes = estados_sigrid(f, [x])
    with caplog.at_level("WARNING"):
        _marcar(f, _resultado(d, x))
    assert estados_sigrid(f, [x]) == antes
    assert estados_sigrid(f, [d])[d][0] == "registrado"
    avisos = [r.getMessage() for r in caplog.records
              if "fin_movido_sin_cas" in r.getMessage()]
    assert avisos == [f"[repo] fin_movido_sin_cas registro_id={d} "
                      f"movida_de={x} hmores_ide=9000"]
    assert "Persona" not in caplog.text


def test_f060_r28_movida_de_inexistente_avisa() -> None:
    f = _fabrica()
    _x, d = _movido(f)
    _marcar(f, _resultado(d, 999999))
    assert estados_sigrid(f, [d])[d][0] == "registrado"


def test_f060_r28_movida_de_a_si_misma_no_hace_nada(caplog) -> None:
    f = _fabrica()
    _x, d = _movido(f)
    with caplog.at_level("WARNING"):
        _marcar(f, _resultado(d, d))
    assert estados_sigrid(f, [d])[d][0] == "registrado"
    assert "fin_movido_sin_cas" not in caplog.text


def test_f060_r28_sin_movida_de_como_antes(caplog) -> None:
    f = _fabrica()
    x, d = _movido(f)
    r = _resultado(d, x)
    del r["escritas"][0]["movida_de"]
    with caplog.at_level("WARNING"):
        _marcar(f, r)
    assert estados_sigrid(f, [x])[x][0] == "registrado"
    assert "fin_movido" not in caplog.text


def test_f060_r28_movida_de_nula_como_antes() -> None:
    f = _fabrica()
    x, d = _movido(f)
    _marcar(f, _resultado(d, x, movida_de=None))
    assert estados_sigrid(f, [x])[x][0] == "registrado"


def test_f060_r28_en_la_misma_transaccion(monkeypatch) -> None:
    """Si el commit falla, ni D ni X cambian (y la cola reintenta)."""
    f = _fabrica()
    x, d = _movido(f)
    antes = estados_sigrid(f, [x, d])
    original = f.create_session

    def sesion_que_falla():
        s = original()

        def commit():
            raise RuntimeError("commit KO")
        s.commit = commit
        return s
    monkeypatch.setattr(f, "create_session", sesion_que_falla)
    with pytest.raises(RuntimeError, match="commit KO"):
        _marcar(f, _resultado(d, x))
    monkeypatch.setattr(f, "create_session", original)
    assert estados_sigrid(f, [x, d]) == antes


def test_f060_r29_aplicar_dos_veces_deja_lo_mismo(caplog) -> None:
    f = _fabrica()
    x, d = _movido(f)
    _marcar(f, _resultado(d, x))
    primero = estados_sigrid(f, [x, d])
    with caplog.at_level("WARNING"):
        _marcar(f, _resultado(d, x))
    assert estados_sigrid(f, [x, d]) == primero
    assert "fin_movido_sin_cas" not in caplog.text


def test_f060_r29_cadena_de_movimientos() -> None:
    """Dia 2 tenia el CIZ, paso al 3 y luego al 4: 2 y 3 quedan omitidos."""
    f = _fabrica()
    x2 = _con_ciz(f, _v(f, 2))
    d3 = _v(f, 3)
    d4 = _v(f, 4)
    _marcar(f, _resultado(d3, x2))
    _marcar(f, _resultado(d4, d3))
    est = estados_sigrid(f, [x2, d3, d4])
    assert [est[i][0] for i in (x2, d3, d4)] == ["omitido", "omitido",
                                                  "registrado"]
    assert est[x2][1].endswith("paso al dia 2026-10-03")
    assert est[d3][1].endswith("paso al dia 2026-10-04")


def test_f060_r29_por_el_consumidor_de_la_cola() -> None:
    """El canal de `q-transfer-result` usa el mismo `aplicar_resultado`."""
    from interface_adapters.workers import resultado_consumer
    import inspect
    assert "aplicar_resultado(" in inspect.getsource(resultado_consumer)


# ===================== R30 · reparto por obras ===================== #

def test_f060_r30_agregar_ejecucion_conserva_movida_de() -> None:
    from application.services.reparto_obras import agregar_ejecucion
    a = dict(_resultado(4, 3), clave="obr-10")
    b = {"ok": True, "clave": "obr-20", "escritas": [
        {"registro_id": 9, "hmoide": 902, "hmores_ide": 5}]}
    plano = agregar_ejecucion([a, b])
    assert [e.get("movida_de") for e in plano["escritas"]] == [3, None]
    assert agregar_ejecucion([a])["escritas"][0]["movida_de"] == 3


# ================== R10 · avisos_racha en el preflight ================== #

@pytest.fixture
def portal(monkeypatch):
    from config.settings import Settings
    from fastapi.testclient import TestClient
    from interface_adapters.web.app import build_app
    from tests.test_f022_aprobar_seleccion import (
        CalendarioFalso,
        PublisherFalso,
        Sv5Falso,
    )
    for clave, valor in {"PG_PASSWORD": "irrelevante-en-tests",
                         "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
                         "DEFAULT_REVIEWER": "ana",
                         "TRANSFER_BASE_URL": "http://sv5.interno"}.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.delenv("INCIDENCIAS_PATH", raising=False)

    def _levantar(fabrica):
        sv5 = Sv5Falso()
        app = build_app(Settings(_env_file=None),
                        repository=ParteReviewRepository(fabrica),
                        transfer_client=sv5, publisher=PublisherFalso(),
                        calendario_provider=CalendarioFalso())
        return TestClient(app), sv5
    return _levantar


def test_f060_r10_preflight_lleva_avisos_racha_por_grupo(portal) -> None:
    f = _fabrica()
    _v(f, 5, estado="registrado")
    t = _t(f, 4)
    cliente, sv5 = portal(f)
    r = cliente.post("/api/aprobar/preflight", json={"registro_ids": [t]})
    assert r.status_code == 200
    (grupo,) = r.json()["grupos"]
    assert [a["registro_id"] for a in grupo["avisos_racha"]] == [t]
    assert grupo["avisos_racha"][0]["motivo"].startswith("racha_desordenada")
    # Nunca al payload de sv5.
    (payload,) = sv5.preflights
    assert set(payload) == {"obra", "lineas", "pisar_claves", "usuario"}
    assert "avisos_racha" not in payload["lineas"][0]


def test_f060_r9_payload_de_sv5_lleva_la_racha(portal) -> None:
    f = _fabrica()
    d1 = _v(f, 1, estado="registrado")
    d2 = _v(f, 2)
    cliente, sv5 = portal(f)
    cliente.post("/api/aprobar/ejecutar", json={"registro_ids": [d2]})
    (payload,) = sv5.ejecutadas
    (linea,) = payload["lineas"]
    assert (linea["incidencia_rol"], linea["racha_registro_ids"]) == (
        "fin", [d1])


# ==================== R11 · avisos_racha en el modal ==================== #

import json  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402

from tests.test_f022_vistas_seleccion import (  # noqa: E402
    _ejecutar_js,
    _funcion,
    _js,
)

sin_node = pytest.mark.skipif(shutil.which("node") is None,
                              reason="node no instalado")


def test_f060_r11_js_cableado_en_el_modal() -> None:
    js = _js()
    aprobar = _funcion(js, "aprobar")
    # Todos los grupos, juntos y fuera del pliegue de cada obra, en su
    # propio bloque, aparte de los avisos de incidencia de F-025.
    assert "g.avisos_racha" in aprobar
    assert "avisosRachaHtml(avisosRacha)" in aprobar
    assert (aprobar.index("avisosIncidenciaHtml(")
            < aprobar.index("avisosRachaHtml(")
            < aprobar.index("grupoHtml(g, plegar)"))
    assert "innerHTML" not in _funcion(js, "avisosRachaHtml")


@sin_node
def test_f060_r11_js_avisos_de_racha_escapados() -> None:
    avisos = [{"registro_id": 7, "fecha": "2026-10-04",
               "nombre": "<script>x</script>",
               "motivo": "racha_desordenada: el 2026-10-05 & <i>y</i>"}]
    html = _ejecutar_js(["esc", "avisosRachaHtml"],
                        f"avisosRachaHtml({json.dumps(avisos)})")
    assert "ap-racha-avisos" in html and "ap-incid-avisos" not in html
    assert "<script>" not in html and "&lt;script&gt;x" in html
    assert "<i>" not in html and "&amp; &lt;i&gt;y" in html
    assert "<strong>1</strong>" in html
    texto = re.sub(r"<[^>]+>", "", html)
    assert texto.startswith(
        "Hay 1 linea(s) aprobadas antes de una incidencia ya registrada en "
        "Sigrid. Se registran, pero no mueven el inicio ni el fin de esa "
        "racha: revísala a mano:")
    assert "2026-10-04" in texto


@sin_node
@pytest.mark.parametrize("avisos", [[], None])
def test_f060_r11_js_sin_avisos_no_pinta_nada(avisos) -> None:
    assert _ejecutar_js(["esc", "avisosRachaHtml"],
                        f"avisosRachaHtml({json.dumps(avisos)})") == ""


# ============ Mutacion (rigor critico): huecos que cerro la campaña ============ #

def test_f060_r6_sin_dni_ni_recurso_por_la_ficha() -> None:
    """Sin DNI y sin recurso, la persona es la ficha (`emp-77`): el
    historico trae SUS lineas y no las de otra ficha (`emp-78`)."""
    from infrastructure.database.orm_models import ParteRegistroOrm
    from infrastructure.database.parte_repository import persona_de
    f = _fabrica()
    d1 = _v(f, 1, dni=None, recurso_ide=None)
    _v(f, 1, dni=None, recurso_ide=None, empleado_ide=78, doc="otra1")
    _t(f, 1, dni=None, recurso_ide=None, empleado_ide=78, doc="otra1t")
    d2 = _v(f, 2, dni=None, recurso_ide=None)
    with f.create_session() as s:
        assert persona_de(s.get(ParteRegistroOrm, d2)) == "emp-77"
    l2 = _linea(_datos(f, [d2]), d2)
    assert (l2["incidencia_rol"], l2["racha_registro_ids"]) == ("fin", [d1])


def test_f060_r10_trabajo_en_el_epsilon_no_avisa() -> None:
    """Una linea de trabajo con |horas| = 1e-9 es cero (como F-025): no
    pide historico ni lleva aviso `racha_desordenada`."""
    f = _fabrica()
    _v(f, 5, estado="registrado")
    vistos = _contar_historicos(f)
    assert _avisos(_datos(f, [_t(f, 4, horas=1e-9)])) == []
    assert vistos == []
