# tests/test_f002_r11_sin_postgresql.py
"""F-002 · R11: sv5 no tiene conexion ni credencial de PostgreSQL.

R11 es un requisito NEGATIVO, y por eso hasta ahora solo se sostenia por
inspeccion del reviewer: no hay camino de ejecucion que recorrer. Pero es
el que sostiene la decision central del design —no crear una TERCERA copia
de `orm_models.py`, porque sv3 y sv4 ya arrastran dos—, asi que conviene
que una regresion se vea sola en vez de descubrirse leyendo el diff.

Lo que se vigila son las dos puertas por las que entraria una BBDD:

1. **El codigo**: ningun modulo de sv5 importa un driver relacional. Se
   mira con `ast`, no con `grep`, para que una mencion en un comentario o
   en una cadena —como la lista `PROHIBIDOS` de este mismo fichero— no
   cuente como import.
2. **El manifiesto de despliegue**: `infra/manifests/sv5/requirements.txt`
   no declara ninguno. Un import sin paquete no arranca, pero un paquete
   sin import es la puerta abierta para el siguiente que pase por aqui.

Se anade la tercera puerta que menciona el propio enunciado del requisito
(«ni conexion ni CREDENCIAL»): la configuracion de sv5 no expone ningun
campo de PostgreSQL. sv5 recibe las lineas en el payload; su unica traza
de vuelta es `q-transfer-result`.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from config.settings import Settings

#: Raiz del servicio (esta carpeta es `<servicio>/tests`) y del repositorio.
RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
RAIZ_REPO = RAIZ_SERVICIO.parents[1]
MANIFIESTO = RAIZ_REPO / "infra" / "manifests" / "sv5" / "requirements.txt"

#: Raices de import y nombres de distribucion que delatan una BBDD
#: relacional. `psycopg` cubre tambien `psycopg2` y `psycopg-binary` por el
#: prefijo con el que se comparan los nombres del manifiesto.
PROHIBIDOS = ("sqlalchemy", "psycopg", "psycopg2", "asyncpg", "pg8000",
              "alembic")


def _modulos_de_sv5() -> list[Path]:
    """Todo el `.py` del servicio, tests incluidos: sv5 no toca BBDD por
    ningun lado, tampoco en sus dobles."""
    return sorted(ruta for ruta in RAIZ_SERVICIO.rglob("*.py")
                  if "__pycache__" not in ruta.parts)


def _raices_importadas(ruta: Path) -> set[str]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
    raices: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                raices.add(alias.name.split(".")[0].lower())
        elif (isinstance(nodo, ast.ImportFrom) and nodo.level == 0
                and nodo.module):
            raices.add(nodo.module.split(".")[0].lower())
    return raices


def _distribuciones_del_manifiesto() -> list[str]:
    """Nombre de cada paquete declarado, sin version ni extras."""
    nombres = []
    for linea in MANIFIESTO.read_text(encoding="utf-8").splitlines():
        linea = linea.split("#")[0].strip()
        if not linea:
            continue
        nombres.append(re.split(r"[<>=!~\[; ]", linea, maxsplit=1)[0]
                       .strip().lower())
    return nombres


def test_f002_r11_ningun_modulo_de_sv5_importa_una_bbdd_relacional():
    assert _modulos_de_sv5(), "no he encontrado ni un .py: revisa la ruta"

    culpables = {
        ruta.relative_to(RAIZ_SERVICIO).as_posix():
            sorted(_raices_importadas(ruta) & set(PROHIBIDOS))
        for ruta in _modulos_de_sv5()
        if _raices_importadas(ruta) & set(PROHIBIDOS)
    }

    assert culpables == {}, (
        "sv5 no debe tener BBDD (R11), pero estos modulos importan un "
        f"driver relacional: {culpables}. Si de verdad hace falta persistir "
        "algo en sv5, es una decision de arquitectura (seria la TERCERA "
        "copia de orm_models.py) y va al humano, no a un import.")


def test_f002_r11_el_manifiesto_de_sv5_no_declara_ninguna_bbdd():
    assert MANIFIESTO.is_file(), f"no encuentro el manifiesto: {MANIFIESTO}"
    declarados = _distribuciones_del_manifiesto()
    assert declarados, f"el manifiesto {MANIFIESTO} esta vacio"

    culpables = [nombre for nombre in declarados
                 if any(nombre.startswith(p) for p in PROHIBIDOS)]

    assert culpables == [], (
        f"{MANIFIESTO.name} de sv5 declara paquetes de BBDD: {culpables}. "
        "Un paquete instalado sin usar no rompe nada hoy, pero es la puerta "
        "por la que entra el import de manana (R11).")


def test_f002_r11_la_configuracion_de_sv5_no_expone_credenciales_de_bbdd():
    """R11 dice «ni conexion ni CREDENCIAL»: el settings tampoco."""
    sospechosos = sorted(
        campo for campo in Settings.model_fields
        if re.search(r"^(pg|postgres|db|database)_|_dsn$|password", campo,
                     re.IGNORECASE))

    assert sospechosos == [], (
        f"Settings de sv5 expone campos de BBDD: {sospechosos}. sv5 recibe "
        "las lineas en el payload y responde por q-transfer-result; no debe "
        "tener por donde conectarse a PostgreSQL.")
