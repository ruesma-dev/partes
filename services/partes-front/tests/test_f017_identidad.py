# tests/test_f017_identidad.py
"""F-017 · La resolucion de la identidad de Easy Auth.

Cubre R1-R9 (menos R5c, que vive en `test_f017_entorno.py`), R20 y R21.

La mayor parte se prueba sobre las funciones PURAS de `identidad.py`: entra
un `Mapping` de cabeceras y una etiqueta de fallback, sale `(actor, origen)`.
Ni FastAPI, ni `Settings`, ni `os.environ`. Los pocos tests que necesitan la
app entera (el WARNING de R5b, la nota de arranque de R9, R20 y `/whoami`)
usan `TestClient` + SQLite en memoria: ni red, ni PostgreSQL, ni colas.

Dominio de pruebas `ejemplo.invalid` (RFC 2606): aqui no aparece el correo
real de ninguna persona.
"""
from __future__ import annotations

import base64
import json
import logging

import pytest
from config.settings import Settings
from fastapi.testclient import TestClient
from infrastructure.database.orm_models import ParteDocumentOrm
from infrastructure.database.parte_repository import ParteReviewRepository
from interface_adapters.web.app import build_app
from interface_adapters.web.identidad import (
    ACTOR_LOCAL_SIN_NOMBRE,
    ACTOR_MAX_LEN,
    ACTOR_SIN_IDENTIDAD,
    CABECERA_NOMBRE,
    CABECERA_TOKEN,
    PREFIJO_LOCAL,
    VARIABLES_DESPLIEGUE,
    actor_desde_cabeceras,
    actor_desde_token,
    es_actor_reservado,
    normalizar_actor,
)
from tests.dobles import FabricaSesionSqlite, sembrar_parte

USUARIO = "ana.ejemplo@ejemplo.invalid"
DOC = "doc-f017"


# ====================================================================== #
# Utilidades
# ====================================================================== #

def _token(**claims: str) -> str:
    """El `X-MS-CLIENT-PRINCIPAL` tal y como lo inyecta Easy Auth."""
    cuerpo = {"auth_typ": "aad",
              "claims": [{"typ": t, "val": v} for t, v in claims.items()]}
    return base64.b64encode(
        json.dumps(cuerpo).encode("utf-8")).decode("ascii")


@pytest.fixture(autouse=True)
def entorno(monkeypatch):
    """Sin `.env`, sin PostgreSQL y con el entorno de despliegue LIMPIO.

    Lo segundo importa: si la maquina que corre la suite tuviera una
    `CONTAINER_APP_*` exportada, los tests de la rama local pasarian a
    ejercitar la rama desplegada sin que nadie se enterase.
    """
    for clave, valor in {
        "PG_PASSWORD": "irrelevante-en-tests",
        "PG_ADMIN_PASSWORD": "irrelevante-en-tests",
    }.items():
        monkeypatch.setenv(clave, valor)
    for variable in VARIABLES_DESPLIEGUE:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.delenv("DEFAULT_REVIEWER", raising=False)
    return monkeypatch


def _settings(**kw) -> Settings:
    return Settings(_env_file=None, **kw)


def _montaje(*, settings=None, aprobado=False):
    """App entera sin colaboradores externos, con UN parte sembrado."""
    fabrica = FabricaSesionSqlite()
    sembrar_parte(fabrica, [{"horas": 8.0}], document_id=DOC,
                  aprobado=aprobado)
    repositorio = ParteReviewRepository(fabrica)
    app = build_app(settings or _settings(), repository=repositorio)
    return TestClient(app), fabrica


def _documento(fabrica) -> ParteDocumentOrm | None:
    with fabrica.create_session() as s:
        return s.get(ParteDocumentOrm, DOC)


def _aprobar(cliente, headers=None):
    return cliente.post(f"/documents/{DOC}/approve", headers=headers or {},
                        follow_redirects=False)


# ====================================================================== #
# R1 · manda la cabecera en claro
# ====================================================================== #

def test_f017_r1_manda_la_cabecera_name() -> None:
    """El principal en claro es la via principal (DA1)."""
    actor, origen = actor_desde_cabeceras(
        {CABECERA_NOMBRE: USUARIO}, fallback="da-igual", desplegado=False)
    assert (actor, origen) == (USUARIO, "cabecera-name")


def test_f017_r1_la_cabecera_name_gana_al_token() -> None:
    """Con las dos presentes, el token NI SIQUIERA se mira (DA1)."""
    actor, origen = actor_desde_cabeceras(
        {CABECERA_NOMBRE: USUARIO,
         CABECERA_TOKEN: _token(preferred_username="otro@ejemplo.invalid")},
        fallback=None, desplegado=True)
    assert (actor, origen) == (USUARIO, "cabecera-name")


def test_f017_r1_la_cabecera_name_es_insensible_a_mayusculas() -> None:
    """Starlette normaliza el nombre de la cabecera; el resolutor tambien."""
    actor, origen = actor_desde_cabeceras(
        {CABECERA_NOMBRE.lower(): USUARIO}, fallback=None, desplegado=False)
    assert (actor, origen) == (USUARIO, "cabecera-name")


@pytest.mark.parametrize("valor", ["", "   ", "\t\n"])
def test_f017_r1_name_vacia_es_como_ausente(valor: str) -> None:
    """R1 exige contenido NO vacio: en blanco cuenta como que no llego."""
    actor, origen = actor_desde_cabeceras(
        {CABECERA_NOMBRE: valor}, fallback="ana", desplegado=False)
    assert (actor, origen) == (f"{PREFIJO_LOCAL}ana", "local")


# ====================================================================== #
# R2 · el token base64, de suplente
# ====================================================================== #

@pytest.mark.parametrize("claim", [
    "preferred_username", "upn", "email", "emails", "name"])
def test_f017_r2_sin_name_se_lee_el_token(claim: str) -> None:
    """Los cinco claims de la lista de preferencia valen, uno a uno."""
    actor, origen = actor_desde_cabeceras(
        {CABECERA_TOKEN: _token(**{claim: USUARIO})},
        fallback="ana", desplegado=False)
    assert (actor, origen) == (USUARIO, "cabecera-token")


def test_f017_r2_se_respeta_el_orden_de_preferencia() -> None:
    """Con varios claims presentes gana `preferred_username`, el primero."""
    actor, _ = actor_desde_cabeceras(
        {CABECERA_TOKEN: _token(name="Nombre Apellido",
                                email="tercero@ejemplo.invalid",
                                upn="segundo@ejemplo.invalid",
                                preferred_username=USUARIO)},
        fallback=None, desplegado=False)
    assert actor == USUARIO


def test_f017_r2_un_claim_vacio_no_gana_al_siguiente() -> None:
    """Presente pero en blanco no es «el primer claim NO vacio»."""
    actor, _ = actor_desde_cabeceras(
        {CABECERA_TOKEN: _token(preferred_username="   ",
                                upn=USUARIO)},
        fallback=None, desplegado=False)
    assert actor == USUARIO


def test_f017_r2_el_token_tambien_se_normaliza() -> None:
    actor, _ = actor_desde_cabeceras(
        {CABECERA_TOKEN: _token(upn="  ANA.Ejemplo@Ejemplo.INVALID ")},
        fallback=None, desplegado=False)
    assert actor == USUARIO


# ====================================================================== #
# R3 · un token roto NUNCA tumba la peticion
# ====================================================================== #

@pytest.mark.parametrize("token, caso", [
    ("no-es-base64-!!!@@@", "no es base64"),
    (base64.b64encode(b"esto no es json").decode("ascii"), "no es JSON"),
    (base64.b64encode(b'{"auth_typ":"aad"}').decode("ascii"), "sin claims"),
    (base64.b64encode(b'{"claims":[]}').decode("ascii"), "claims vacios"),
    (base64.b64encode(b'{"claims":"no-es-lista"}').decode("ascii"),
     "claims no es lista"),
    (base64.b64encode(b'[1,2,3]').decode("ascii"), "JSON que no es objeto"),
    ("", "cabecera vacia"),
])
def test_f017_r3_token_corrupto_no_rompe(token: str, caso: str) -> None:
    """Las cuatro formas de reventar del design.md §2, y alguna mas."""
    assert actor_desde_token(token) is None, caso
    # Y el resolutor completo cae al fallback sin elevar nada.
    actor, origen = actor_desde_cabeceras(
        {CABECERA_TOKEN: token}, fallback="ana", desplegado=False)
    assert (actor, origen) == (f"{PREFIJO_LOCAL}ana", "local"), caso


def test_f017_r3_un_claim_desconocido_no_sirve_de_actor() -> None:
    """Solo los cinco claims de R2; `sub` o `roles` no firman nada."""
    assert actor_desde_token(_token(sub="guid", roles="admin")) is None


def test_f017_r3_una_entrada_de_claims_mal_formada_se_ignora() -> None:
    """Una lista de claims con basura dentro no puede lanzar."""
    cuerpo = {"claims": ["no-es-dict", {"sin": "typ"}, 42,
                         {"typ": "upn", "val": USUARIO}]}
    token = base64.b64encode(
        json.dumps(cuerpo).encode("utf-8")).decode("ascii")
    assert actor_desde_token(token) == USUARIO


@pytest.mark.parametrize("valor", [12345, None, True, ["a"], {"b": 1}])
def test_f017_r3_un_claim_con_valor_que_no_es_texto_no_firma(valor) -> None:
    """`typ` correcto pero `val` que no es una cadena: NO vale como actor.

    Sin esta comprobación, un claim `{"typ": "upn", "val": 12345}` acabaría
    firmando la fila como `"12345"` — un actor **fabricado** a partir de un
    dato que no era un nombre. Las dos mitades del claim tienen que ser
    texto, no una de las dos.
    """
    cuerpo = {"claims": [{"typ": "upn", "val": valor}]}
    token = base64.b64encode(
        json.dumps(cuerpo).encode("utf-8")).decode("ascii")
    assert actor_desde_token(token) is None


def test_f017_r3_un_claim_no_textual_no_tapa_al_siguiente_valido() -> None:
    """Y descartarlo no puede costar la identidad real que venía detrás."""
    cuerpo = {"claims": [{"typ": "preferred_username", "val": 999},
                         {"typ": "upn", "val": USUARIO}]}
    token = base64.b64encode(
        json.dumps(cuerpo).encode("utf-8")).decode("ascii")
    assert actor_desde_token(token) == USUARIO


# ====================================================================== #
# R4 · normalizacion
# ====================================================================== #

@pytest.mark.parametrize("entrada, esperado", [
    ("  ana@ejemplo.invalid  ", "ana@ejemplo.invalid"),
    ("ANA@EJEMPLO.INVALID", "ana@ejemplo.invalid"),
    ("ana@ejemplo.invalid\r\n", "ana@ejemplo.invalid"),
    ("an\ra@ejemplo\n.invalid", "ana@ejemplo.invalid"),
    ("ana\x00@ejemplo\x1b.invalid", "ana@ejemplo.invalid"),
    ("Ana.Apellido@Ejemplo.Invalid", "ana.apellido@ejemplo.invalid"),
    ("", None),
    ("   ", None),
    (None, None),
    ("\r\n\t", None),
])
def test_f017_r4_normalizacion(entrada, esperado) -> None:
    assert normalizar_actor(entrada) == esperado


def test_f017_r4_se_trunca_a_120() -> None:
    """El ancho lo manda la columna mas estrecha (`undo_log.actor`)."""
    assert ACTOR_MAX_LEN == 120
    largo = "a" * 200 + "@ejemplo.invalid"
    assert normalizar_actor(largo) == "a" * 120


def test_f017_r4_la_inyeccion_de_log_no_sobrevive() -> None:
    """Un salto de linea en el actor partiria una linea de log en dos."""
    sucio = "ana@ejemplo.invalid\nWARNING falso: la app ha caido"
    limpio = normalizar_actor(sucio)
    assert "\n" not in limpio and "\r" not in limpio


# ====================================================================== #
# R5 · sin desplegar, el actor lleva el prefijo `local:`
# ====================================================================== #

def test_f017_r5_fallback_local_sin_desplegar_con_default_reviewer() -> None:
    actor, origen = actor_desde_cabeceras(
        {}, fallback="ana", desplegado=False)
    assert (actor, origen) == ("local:ana", "local")


def test_f017_r5_fallback_local_sin_desplegar_sin_default_reviewer() -> None:
    actor, origen = actor_desde_cabeceras({}, fallback=None, desplegado=False)
    assert (actor, origen) == (ACTOR_LOCAL_SIN_NOMBRE, "local")
    assert actor == "local:sin-identidad"


def test_f017_r5_el_fallback_tambien_se_normaliza() -> None:
    """`DEFAULT_REVIEWER=' Ana '` no puede colar espacios en la columna."""
    actor, _ = actor_desde_cabeceras(
        {}, fallback="  ANA  ", desplegado=False)
    assert actor == "local:ana"


def test_f017_r5_un_default_reviewer_en_blanco_es_como_no_tenerlo() -> None:
    actor, _ = actor_desde_cabeceras({}, fallback="   ", desplegado=False)
    assert actor == ACTOR_LOCAL_SIN_NOMBRE


# ====================================================================== #
# R5b · desplegado y sin cabecera: `sin-identidad` + WARNING
# ====================================================================== #

def test_f017_r5b_desplegado_sin_cabecera_es_sin_identidad() -> None:
    """La enmienda del humano: en produccion NO se miente sobre el origen."""
    actor, origen = actor_desde_cabeceras(
        {}, fallback="ana", desplegado=True)
    assert (actor, origen) == (ACTOR_SIN_IDENTIDAD,
                               "sin-identidad-desplegado")
    assert actor == "sin-identidad"
    # Lo que la enmienda viene a evitar, comprobado por separado: no basta
    # con que el valor sea el correcto, tiene que NO ser el de la rama local.
    assert not actor.startswith(PREFIJO_LOCAL)


def test_f017_r5b_el_default_reviewer_no_contamina_el_caso_desplegado() -> None:
    """Estando desplegado, `DEFAULT_REVIEWER` es irrelevante: no firma."""
    actor, _ = actor_desde_cabeceras(
        {}, fallback="quien-sea", desplegado=True)
    assert actor == ACTOR_SIN_IDENTIDAD
    assert "quien-sea" not in actor


def test_f017_r5b_desplegado_sin_cabecera_avisa_y_la_escritura_se_completa(
        caplog) -> None:
    """WARNING por peticion, y el parte queda aprobado IGUALMENTE.

    Las tres cosas a la vez (design.md §10): el valor exacto, la ausencia
    del prefijo `local:` y que la operacion NO se pierde. No saber quien
    fue no es motivo para perder el cambio (principio heredado de F-016).
    """
    entorno_desplegado = {"CONTAINER_APP_NAME": "ca-sv4-front-test"}
    with pytest.MonkeyPatch.context() as mp:
        for clave, valor in entorno_desplegado.items():
            mp.setenv(clave, valor)
        mp.setenv("DEFAULT_REVIEWER", "no-deberia-usarse")
        cliente, fabrica = _montaje(settings=_settings())
        with caplog.at_level(logging.WARNING):
            respuesta = _aprobar(cliente)

    assert respuesta.status_code in (302, 303)
    documento = _documento(fabrica)
    assert documento.approved is True             # la operacion se completa
    assert documento.approved_by == ACTOR_SIN_IDENTIDAD
    assert not documento.approved_by.startswith(PREFIJO_LOCAL)
    assert "no-deberia-usarse" not in documento.approved_by

    avisos = [r for r in caplog.records
              if r.levelno == logging.WARNING and "identidad" in r.message]
    assert len(avisos) == 1, "un incidente de autenticacion tiene que verse"


def test_f017_r5b_el_aviso_se_repite_en_cada_peticion(caplog) -> None:
    """R9: el WARNING de R5b NO esta sujeto al «una vez por arranque»."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("CONTAINER_APP_NAME", "ca-sv4-front-test")
        cliente, _ = _montaje()
        with caplog.at_level(logging.WARNING):
            for _ in range(3):
                _aprobar(cliente)

    avisos = [r for r in caplog.records
              if r.levelno == logging.WARNING and "identidad" in r.message]
    assert len(avisos) == 3, "cada peticion sin identidad es un incidente"


# ====================================================================== #
# R6 · el espacio de nombres reservado no se puede fabricar desde fuera
# ====================================================================== #

@pytest.mark.parametrize("valor", [
    "local:x", "LOCAL:X", "local:sin-identidad", " Local:Ana ",
    "sin-identidad", "SIN-IDENTIDAD", " Sin-Identidad ", "local:",
])
@pytest.mark.parametrize("cabecera", [CABECERA_NOMBRE, "token"])
@pytest.mark.parametrize("desplegado", [False, True])
def test_f017_r6_espacio_reservado_por_cabecera_se_descarta(
        valor: str, cabecera: str, desplegado: bool) -> None:
    """Ningun valor de origen externo puede fabricar un actor reservado."""
    cabeceras = ({CABECERA_TOKEN: _token(upn=valor)} if cabecera == "token"
                 else {CABECERA_NOMBRE: valor})
    actor, origen = actor_desde_cabeceras(
        cabeceras, fallback="ana", desplegado=desplegado)

    if desplegado:
        assert (actor, origen) == (ACTOR_SIN_IDENTIDAD,
                                   "sin-identidad-desplegado")
    else:
        assert (actor, origen) == ("local:ana", "local")
    assert origen not in ("cabecera-name", "cabecera-token")


def test_f017_r6_el_descarte_avisa(caplog) -> None:
    """Alguien intentando firmar como reservado tiene que verse en el log."""
    with caplog.at_level(logging.WARNING):
        actor_desde_cabeceras({CABECERA_NOMBRE: "local:jefe"},
                              fallback=None, desplegado=False)
    assert [r for r in caplog.records if r.levelno == logging.WARNING]


@pytest.mark.parametrize("valor, reservado", [
    ("local:x", True),
    ("local:", True),
    ("sin-identidad", True),
    ("ana@ejemplo.invalid", False),
    ("sin-identidad@ejemplo.invalid", False),   # un UPN que EMPIEZA igual
    ("localista@ejemplo.invalid", False),       # empieza por «local» sin `:`
    (None, False),
    ("", False),
])
def test_f017_r6_que_cuenta_como_reservado(valor, reservado: bool) -> None:
    assert es_actor_reservado(valor) is reservado


# ====================================================================== #
# R7 · SIEMPRE hay actor
# ====================================================================== #

@pytest.mark.parametrize("cabeceras, esperado_origen", [
    ({}, None),
    ({CABECERA_NOMBRE: USUARIO}, "cabecera-name"),
    ({CABECERA_TOKEN: "irrelevante"}, None),
    ({CABECERA_NOMBRE: USUARIO, CABECERA_TOKEN: "irrelevante"},
     "cabecera-name"),
])
@pytest.mark.parametrize("desplegado", [False, True])
@pytest.mark.parametrize("fallback", [None, "ana", "", "   "])
def test_f017_r7_siempre_hay_actor(cabeceras, esperado_origen,
                                   desplegado: bool, fallback) -> None:
    """Barrido: cuatro combinaciones x dos entornos x cuatro fallbacks.

    A partir de F-017, un NULL en una columna de autor significa
    EXCLUSIVAMENTE «fila anterior al corte» — asi que el resolutor no
    puede devolver vacio ni `None` en ninguna combinacion.
    """
    actor, origen = actor_desde_cabeceras(
        cabeceras, fallback=fallback, desplegado=desplegado)

    assert isinstance(actor, str)
    assert actor.strip() != ""
    assert len(actor) <= ACTOR_MAX_LEN
    assert origen in ("cabecera-name", "cabecera-token", "local",
                      "sin-identidad-desplegado")
    if esperado_origen:
        assert origen == esperado_origen


# ====================================================================== #
# R8 · una identidad larga no puede tumbar una escritura
# ====================================================================== #

def test_f017_r8_upn_larguisimo_se_trunca_y_no_falla() -> None:
    largo = "b" * 500 + "@ejemplo.invalid"
    actor, origen = actor_desde_cabeceras(
        {CABECERA_NOMBRE: largo}, fallback=None, desplegado=True)
    assert origen == "cabecera-name"
    assert len(actor) == ACTOR_MAX_LEN


def test_f017_r8_el_actor_truncado_cabe_en_la_columna_mas_estrecha() -> None:
    """La comprobacion que evita un DataError en `undo_log.actor` (120)."""
    largo = "c" * 400
    cliente, fabrica = _montaje()
    respuesta = _aprobar(cliente, {CABECERA_NOMBRE: largo})
    assert respuesta.status_code in (302, 303)
    assert len(_documento(fabrica).approved_by) == ACTOR_MAX_LEN


# ====================================================================== #
# R9 · la nota de arranque, UNA sola vez
# ====================================================================== #

def test_f017_r9_aviso_una_sola_vez(caplog) -> None:
    """La nota de arranque dice si se cree desplegado y POR QUE senal."""
    cliente, _ = _montaje()
    with caplog.at_level(logging.INFO):
        for _ in range(3):
            _aprobar(cliente, {CABECERA_NOMBRE: USUARIO})

    notas = [r for r in caplog.records
             if "[identidad]" in r.message and r.levelno == logging.INFO]
    assert len(notas) == 1, "la nota de arranque es UNA por proceso"
    assert "senal" in notas[0].message


def test_f017_r9_la_nota_no_vuelca_el_token_ni_los_claims(caplog) -> None:
    secreto = "no-debe-aparecer@ejemplo.invalid"
    token = _token(upn=secreto)
    cliente, _ = _montaje()
    with caplog.at_level(logging.INFO):
        _aprobar(cliente, {CABECERA_TOKEN: token})

    texto = " ".join(r.getMessage() for r in caplog.records)
    assert token not in texto
    assert secreto not in texto


# ====================================================================== #
# R20 · cabeceras basura no cambian NINGUN codigo de estado
# ====================================================================== #

CABECERAS_BASURA = [
    {},
    {CABECERA_NOMBRE: ""},
    {CABECERA_NOMBRE: "   "},
    {CABECERA_TOKEN: "no-es-base64-!!!"},
    {CABECERA_TOKEN: base64.b64encode(b"no json").decode("ascii")},
    {CABECERA_NOMBRE: "", CABECERA_TOKEN: "roto"},
    {CABECERA_NOMBRE: "local:intruso"},
    {CABECERA_NOMBRE: "x" * 5000},
]


@pytest.mark.parametrize("cabeceras", CABECERAS_BASURA)
@pytest.mark.parametrize("metodo, ruta", [
    ("get", "/health"),
    ("post", f"/documents/{DOC}/approve"),
    ("post", f"/documents/{DOC}/delete"),
    ("post", "/api/registro/1/delete"),
    ("post", "/api/obra/0100/delete"),
    ("post", "/api/trabajador/nadie/delete"),
])
def test_f017_r20_cabeceras_basura_no_cambian_el_estado(
        cabeceras, metodo: str, ruta: str) -> None:
    """Anotar quien hizo algo JAMAS puede cambiar lo que responde la ruta."""
    cliente_limpio, _ = _montaje()
    cliente_sucio, _ = _montaje()

    limpio = getattr(cliente_limpio, metodo)(ruta, follow_redirects=False)
    sucio = getattr(cliente_sucio, metodo)(ruta, headers=cabeceras,
                                           follow_redirects=False)
    assert sucio.status_code == limpio.status_code


# ====================================================================== #
# R21 · /whoami
# ====================================================================== #

def test_f017_r21_whoami_con_la_cabecera_en_claro() -> None:
    cliente, _ = _montaje()
    datos = cliente.get("/whoami", headers={CABECERA_NOMBRE: USUARIO}).json()
    assert datos["actor"] == USUARIO
    assert datos["origen"] == "cabecera-name"
    assert datos["cabeceras_easy_auth"] == [CABECERA_NOMBRE]


def test_f017_r21_whoami_con_el_token() -> None:
    cliente, _ = _montaje()
    datos = cliente.get(
        "/whoami", headers={CABECERA_TOKEN: _token(upn=USUARIO)}).json()
    assert datos["actor"] == USUARIO
    assert datos["origen"] == "cabecera-token"


def test_f017_r21_whoami_en_local() -> None:
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("DEFAULT_REVIEWER", "ana")
        cliente, _ = _montaje(settings=_settings())
        datos = cliente.get("/whoami").json()
    assert datos == {
        "actor": "local:ana",
        "origen": "local",
        "entorno": "local",
        "senal_despliegue": None,
        "cabeceras_easy_auth": [],
    }


def test_f017_r21_whoami_desplegado_sin_cabecera() -> None:
    """La cuarta rama, la que M1 usa para detectar el incidente."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("CONTAINER_APP_NAME", "ca-sv4-front-test")
        cliente, _ = _montaje()
        datos = cliente.get("/whoami").json()
    assert datos["actor"] == ACTOR_SIN_IDENTIDAD
    assert datos["origen"] == "sin-identidad-desplegado"
    assert datos["entorno"] == "desplegado"
    assert datos["senal_despliegue"] == "CONTAINER_APP_NAME"


def test_f017_r21_whoami_no_revela_valores_ni_claims() -> None:
    """Devuelve la identidad de quien pregunta y NADA mas (design.md §7)."""
    token = _token(upn=USUARIO, sub="guid-secreto",
                   tid="tenant-secreto")
    cliente, _ = _montaje()
    respuesta = cliente.get("/whoami", headers={
        CABECERA_TOKEN: token,
        "X-MS-CLIENT-PRINCIPAL-ID": "oid-secreto",
    })
    crudo = respuesta.text
    datos = respuesta.json()

    assert token not in crudo
    assert "guid-secreto" not in crudo
    assert "tenant-secreto" not in crudo
    assert "oid-secreto" not in crudo
    # Los NOMBRES de las cabeceras presentes si, sus valores no.
    assert set(datos["cabeceras_easy_auth"]) == {
        CABECERA_TOKEN, "X-MS-CLIENT-PRINCIPAL-ID"}
    assert set(datos) == {"actor", "origen", "entorno", "senal_despliegue",
                          "cabeceras_easy_auth"}


def test_f017_r21_whoami_no_escribe_nada(caplog) -> None:
    """M1 tiene que poder comprobarse sin ensuciar una sola fila."""
    cliente, fabrica = _montaje()
    cliente.get("/whoami", headers={CABECERA_NOMBRE: USUARIO})
    documento = _documento(fabrica)
    assert documento.approved is False
    assert documento.approved_by is None
