# tests/test_f017_punto_unico.py
"""F-017 · R10 y R11: la identidad se resuelve en UN solo sitio.

Un guardian de estructura, no de comportamiento. Lo que vigila es que
nadie vuelva a leer la identidad por su cuenta: ni `settings.default_reviewer`
suelto en una ruta, ni una cabecera `X-MS-CLIENT-PRINCIPAL*` fuera del
resolutor, ni el repositorio metiendose a averiguar quien pide las cosas.

Por que hace falta un test para esto. Antes de F-017 habia **once** lecturas
de `settings.default_reviewer` repartidas por `app.py`, cada una a un
parametro distinto. Ninguna estaba mal por si sola; el problema era que para
cambiar quien firma habia que encontrarlas todas — y F-016 encontro diez de
once. La regla «un solo punto» solo se sostiene si algo la comprueba.

Es tambien la base sobre la que F-008 (roles) y F-018 (log de auditoria) van
a construir: las dos preguntan «quien es este», y las dos deben preguntarselo
al mismo sitio.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

SV4 = Path(__file__).resolve().parents[1]
APP = SV4 / "interface_adapters" / "web" / "app.py"
IDENTIDAD = SV4 / "interface_adapters" / "web" / "identidad.py"


def _fuente(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


# ====================================================================== #
# R11 · una sola lectura de `settings.default_reviewer`
# ====================================================================== #

def test_f017_r11_una_sola_lectura_de_default_reviewer() -> None:
    """Exactamente UNA en todo `app.py`, y dentro del resolutor.

    Antes de esta feature habia doce (once en rutas + la de `_actor`).
    """
    fuente = _fuente(APP)
    assert fuente.count("settings.default_reviewer") == 1


def test_f017_r11_esa_lectura_esta_dentro_del_resolutor() -> None:
    """No basta con que haya una: tiene que estar en el sitio correcto."""
    fuente = _fuente(APP)
    resolutor = fuente.index("def _resolver_identidad(request: Request)")
    siguiente = fuente.index("def _actor(request: Request)")
    assert resolutor < siguiente, "el resolutor vive pegado a `_actor`"

    bloque = fuente[resolutor:siguiente]
    assert bloque.count("settings.default_reviewer") == 1


def test_f017_r11_ninguna_ruta_lee_default_reviewer() -> None:
    """Barrido por rutas: ningun `@app.<verbo>` la lee en su cuerpo."""
    fuente = _fuente(APP)
    rutas = [m.start() for m in re.finditer(r"@app\.(get|post|patch|delete)",
                                            fuente)]
    assert rutas, "no se han encontrado rutas: el guardian no vale nada"
    for inicio in rutas:
        fin = fuente.find("\n    @app.", inicio + 1)
        cuerpo = fuente[inicio:fin if fin != -1 else len(fuente)]
        assert "settings.default_reviewer" not in cuerpo


# ====================================================================== #
# R10 · nadie lee cabeceras de Easy Auth por su cuenta
# ====================================================================== #

#: El literal de una cabecera ENTRE COMILLAS es una lectura de verdad;
#: nombrarla en un docstring es documentacion, y esa no se persigue.
USO_LITERAL = ('"X-MS-CLIENT-PRINCIPAL', "'X-MS-CLIENT-PRINCIPAL")


def _usa_la_cabecera_como_codigo(fuente: str) -> bool:
    return any(uso in fuente for uso in USO_LITERAL)


def test_f017_r10_ninguna_ruta_lee_la_identidad_por_su_cuenta() -> None:
    """`app.py` no manipula ni una cabecera de Easy Auth como texto.

    Los tres nombres llegan importados de `identidad.py`; `/whoami` los
    usa para listar **nombres** de cabeceras presentes, nunca sus valores.
    Que el docstring de `_actor` las mencione es documentacion, no una
    lectura: por eso se busca el literal entrecomillado y no el nombre.
    """
    assert not _usa_la_cabecera_como_codigo(_fuente(APP))


def test_f017_r10_solo_identidad_py_conoce_las_cabeceras() -> None:
    """El literal de la cabecera vive en UN fichero de produccion."""
    fuente = _fuente(IDENTIDAD)
    assert 'CABECERA_NOMBRE = "X-MS-CLIENT-PRINCIPAL-NAME"' in fuente

    otros = [
        p for p in SV4.rglob("*.py")
        if "tests" not in p.parts
        and p.name != "identidad.py"
        and _usa_la_cabecera_como_codigo(p.read_text(encoding="utf-8"))
    ]
    assert otros == [], f"leen la cabecera por su cuenta: {otros}"


@pytest.mark.parametrize("capa", ["infrastructure", "application", "domain",
                                  "config"])
def test_f017_r10_las_capas_internas_no_saben_que_existe_easy_auth(
        capa: str) -> None:
    """Hexagonal: leer una cabecera HTTP es un detalle de transporte.

    Si el repositorio o un servicio de aplicacion empezara a mirar
    cabeceras, el diseño se habria torcido: el autor **se recibe por
    parametro** (`by=`, `usuario=`, `approved_by=`, `actor=`), no se
    averigua.
    """
    carpeta = SV4 / capa
    if not carpeta.exists():
        pytest.skip(f"sv4 no tiene capa {capa}")

    culpables = [
        p for p in carpeta.rglob("*.py")
        if "X-MS-CLIENT-PRINCIPAL" in p.read_text(encoding="utf-8")
        or "easy_auth" in p.read_text(encoding="utf-8").lower()
    ]
    assert culpables == [], f"{capa} mira la identidad: {culpables}"


def test_f017_r10_el_repositorio_no_importa_identidad() -> None:
    """El repositorio recibe el autor; no lo resuelve."""
    repositorio = (SV4 / "infrastructure" / "database"
                   / "parte_repository.py").read_text(encoding="utf-8")
    assert "identidad" not in repositorio
    assert "default_reviewer" not in repositorio


# ====================================================================== #
# La firma intangible (design.md §6)
# ====================================================================== #

def test_f017_la_firma_de_actor_sigue_siendo_la_de_f016() -> None:
    """F-016 prometio que solo cambiaria el INTERIOR de `_actor`.

    Este test y `test_f016_r13_la_identidad_se_resuelve_en_un_solo_sitio`
    dicen lo mismo desde dos features distintas, y es a proposito: es la
    promesa que permite que los cinco endpoints de jornadas no se hayan
    tocado.
    """
    fuente = _fuente(APP)
    assert fuente.count("def _actor(request: Request) -> str | None:") == 1


def test_f017_todos_los_puntos_de_escritura_usan_el_helper() -> None:
    """Catorce llamadas al helper: las cinco de F-016 y las nueve de F-017.

    Las nueve: aprobar documento, borrar documento, borrar linea, borrar
    obra, borrar trabajador, alta manual, preflight, aprobar sincrono y
    aprobar encolado. `_payload_registro` y `_trazar` no cuentan porque
    **reciben** el actor por parametro en vez de pedirlo — que es
    justamente lo que R10 quiere.

    El numero exacto importa menos que la propiedad: lo que no puede
    pasar es que aparezca una firma que no venga de `_actor`, y de eso se
    encargan los tests de R11.
    """
    fuente = _fuente(APP)
    assert fuente.count("_actor(request)") == 14
