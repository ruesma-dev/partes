# tests/test_f015_r33_variable_espejo.py
"""R33 · `JORNADA_SEMANAL_POR_CANDEF` es la MISMA en sv3 y en sv4.

sv3 decide cuántas horas de cada día son extra; sv4 decide de qué días
avisa como «jornada incompleta». Los dos usan el mismo mapa candef →
jornada semanal, y son procesos distintos con su propia configuración: si
un despliegue cambia el valor en uno y se olvida del otro, el portal marca
en rojo días que sv3 da por completos y el usuario deja de fiarse de los
avisos, sin que nada falle.

Ese descuadre no lo detecta ningún test de servicio —cada suite ve solo su
lado—, así que vive aquí, en la raíz del monorepo, junto al guardián de
las copias del ORM (F-010) y al de los dos resolutores (R19).

Sin red, sin BBDD: los dos `config/settings.py` se leen como texto, para no
tener que importar las dependencias de cada servicio.
"""

from __future__ import annotations

from pathlib import Path

import pytest

#: Raíz del repositorio: este fichero es `<raíz>/tests/test_f015_...py`.
RAIZ = Path(__file__).resolve().parents[1]

SETTINGS = {
    "sv3": RAIZ / "services/partes-persistencia/config/settings.py",
    "sv4": RAIZ / "services/partes-front/config/settings.py",
}

ENV_EXAMPLE = {
    "sv3": RAIZ / "services/partes-persistencia/.env.example",
    "sv4": RAIZ / "services/partes-front/.env.example",
}

#: Las variables espejo y su valor por defecto esperado.
ESPEJO: dict[str, str] = {
    "JORNADA_SEMANAL_POR_CANDEF": '"8:40,9:42"',
    "JORNADA_CACHE_TTL_S": "600",
}


def _default_declarado(fuente: str, alias: str) -> str | None:
    """El valor por defecto del `Field(...)` que declara ese alias.

    Se lee del texto y no importando el módulo a propósito: importar
    `config.settings` de un servicio arrastra sus dependencias y su
    `.env`, que es justo lo que un test de la raíz no debe tocar.
    """
    marca = f', alias="{alias}"'
    fin = fuente.find(marca)
    if fin < 0:
        return None
    inicio = fuente.rfind("Field(", 0, fin)
    if inicio < 0:
        return None
    # El valor por defecto puede llevar comas dentro ("8:40,9:42"), asi que
    # se recorta entre el `Field(` mas cercano y el `, alias=`, no por comas.
    return " ".join(fuente[inicio + len("Field("):fin].split())


@pytest.mark.parametrize("alias, esperado", sorted(ESPEJO.items()))
def test_f015_r33_las_dos_copias_declaran_el_mismo_default(
    alias: str, esperado: str
) -> None:
    valores = {
        servicio: _default_declarado(ruta.read_text(encoding="utf-8"), alias)
        for servicio, ruta in SETTINGS.items()
    }
    for servicio, valor in valores.items():
        assert valor is not None, (
            f"{servicio} no declara `{alias}` en su config/settings.py: la "
            f"variable es ESPEJO, tiene que estar en los dos"
        )
    assert valores["sv3"] == valores["sv4"] == esperado, (
        f"`{alias}` tiene defaults distintos: {valores}. sv3 repartiría las "
        f"horas con un mapa y sv4 avisaría con otro"
    )


def test_f015_r33_el_alias_es_el_mismo_nombre_de_variable() -> None:
    """Mismo nombre en el entorno: el script de provisión pone uno solo."""
    for alias in ESPEJO:
        for servicio, ruta in SETTINGS.items():
            assert f'alias="{alias}"' in ruta.read_text(encoding="utf-8"), (
                f"{servicio} no usa el alias `{alias}`"
            )


def test_f015_r33_ninguna_variable_nueva_es_un_secreto() -> None:
    """No viajan por Key Vault: van en el script de provisión versionado."""
    sospechosos = ("PASSWORD", "KEY", "SECRET", "TOKEN", "CONNECTION_STRING")
    for alias in ESPEJO:
        assert not any(s in alias for s in sospechosos)


@pytest.mark.parametrize("servicio", sorted(ENV_EXAMPLE))
def test_f015_r33_el_env_example_documenta_las_variables(servicio: str) -> None:
    """Documentación para quien monte el entorno local.

    Los `.env.example` de este repositorio NO están versionados (cada
    servicio los ignora con `*.example`), así que el test comprueba el
    contenido solo si el fichero existe en la copia de trabajo: en un
    clon limpio no hay nada que comprobar.
    """
    ruta = ENV_EXAMPLE[servicio]
    if not ruta.exists():
        pytest.skip(f"{servicio}: .env.example no versionado y ausente")
    texto = ruta.read_text(encoding="utf-8", errors="replace")
    assert "JORNADA_SEMANAL_POR_CANDEF=8:40,9:42" in texto
    assert "JORNADA_CACHE_TTL_S=600" in texto
