# tests/test_estructura_monorepo.py
"""Estructura del monorepo: la declaración de servicios contra el árbol real.

`harness/servicios.json` es el mapa que usa el arnés para saber qué zonas del
repositorio se comprueban por separado. Si el mapa y el territorio dejan de
coincidir —una carpeta que se renombra, un servicio que se declara y nunca se
crea— el portero sigue imprimiendo verde mientras un servicio entero queda sin
comprobar. Estos tests son el pegamento entre los dos.

Toda la comprobación es de sistema de ficheros del propio repositorio: ni red,
ni base de datos, ni credenciales. El parseo y la validación de la declaración
NO se reimplementan aquí: se reutiliza `harness.servicios`, que es quien manda.

Trazabilidad con los criterios `acceptance` de F-001 en `harness/features.json`:

- R1 `tests/test_estructura_monorepo.py pasa sin red ni BBDD`
- R2 `El test falla si se declara un servicio con ruta inexistente`
- R3 `bash harness/init.sh en verde` no tiene test: se cumple ejecutando el
  portero, que es quien ejecuta esta suite.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.servicios import cargar_servicios

#: Raíz del repositorio: este fichero es `<raíz>/tests/test_estructura_monorepo.py`.
RAIZ = Path(__file__).resolve().parents[1]

#: Ficheros que valen como punto de entrada de un servicio Python. Uno basta.
PUNTOS_DE_ENTRADA: tuple[str, ...] = ("main.py", "pyproject.toml")


def _servicios_declarados():
    """Los servicios de `harness/servicios.json`, leídos con la lógica del arnés."""
    return cargar_servicios(raiz=str(RAIZ))


def _escribir_declaracion(destino: Path, servicios: list[dict]) -> Path:
    """Escribe una declaración de servicios de mentira en `destino`.

    Sirve para probar el rechazo sin tocar `harness/servicios.json`: un test
    que modificara el fichero real dejaría el repositorio distinto según
    hubiera pasado o hubiera reventado a mitad.
    """
    fichero = destino / "servicios.json"
    fichero.write_text(
        json.dumps({"servicios": servicios}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return fichero


# --- R1: el mapa declarado existe de verdad en el árbol ----------------------


def test_f001_r1_la_declaracion_de_servicios_no_esta_vacia() -> None:
    """Sin servicios declarados, los demás tests de R1 pasarían en el vacío."""
    servicios = _servicios_declarados()
    assert servicios, (
        "harness/servicios.json no declara ningún servicio: los tests de "
        "estructura recorrerían una lista vacía y saldrían en verde sin "
        "haber comprobado nada"
    )


def test_f001_r1_cada_ruta_declarada_existe_y_es_un_directorio() -> None:
    """Cada `ruta` de la declaración apunta a un directorio real del repo."""
    for servicio in _servicios_declarados():
        directorio = RAIZ / servicio.ruta
        assert directorio.is_dir(), (
            f"servicio '{servicio.nombre}': la ruta declarada "
            f"'{servicio.ruta}' no existe en el repositorio, o existe y no es "
            f"un directorio"
        )


def test_f001_r1_cada_servicio_python_tiene_punto_de_entrada() -> None:
    """Un servicio declarado `python` tiene con qué arrancar o empaquetarse."""
    for servicio in _servicios_declarados():
        if servicio.lenguaje != "python":
            continue
        directorio = RAIZ / servicio.ruta
        encontrados = [
            nombre
            for nombre in PUNTOS_DE_ENTRADA
            if (directorio / nombre).is_file()
        ]
        assert encontrados, (
            f"servicio '{servicio.nombre}' ({servicio.ruta}): declarado "
            f"'python' y no tiene ninguno de {list(PUNTOS_DE_ENTRADA)}. O le "
            f"falta el punto de entrada, o el lenguaje declarado no es el suyo"
        )


# --- R2: la validación rechaza una ruta inexistente --------------------------


def test_f001_r2_una_ruta_inexistente_hace_fallar_la_validacion(
    tmp_path: Path,
) -> None:
    """Declarar un servicio cuya carpeta no existe es un error, no un aviso."""
    fichero = _escribir_declaracion(
        tmp_path,
        [{"nombre": "sv-fantasma", "ruta": "services/no-existe", "lenguaje": "python"}],
    )

    with pytest.raises(ValueError) as error:
        cargar_servicios(fichero, raiz=str(tmp_path))

    mensaje = str(error.value)
    assert "services/no-existe" in mensaje, (
        f"el error debe nombrar la ruta que falla para poder arreglarla, y "
        f"dice: {mensaje!r}"
    )
    assert "sv-fantasma" in mensaje, (
        f"el error debe nombrar el servicio que falla, y dice: {mensaje!r}"
    )


def test_f001_r2_la_misma_declaracion_con_la_ruta_creada_si_carga(
    tmp_path: Path,
) -> None:
    """Control del test anterior: lo que rechaza es la ruta, no la declaración.

    Misma declaración, palabra por palabra, con la única diferencia de que la
    carpeta existe. Sin este control, un validador que rechazase *todo* pasaría
    por bueno el test de arriba.
    """
    (tmp_path / "services" / "no-existe").mkdir(parents=True)
    fichero = _escribir_declaracion(
        tmp_path,
        [{"nombre": "sv-fantasma", "ruta": "services/no-existe", "lenguaje": "python"}],
    )

    servicios = cargar_servicios(fichero, raiz=str(tmp_path))

    assert [(s.nombre, s.ruta) for s in servicios] == [
        ("sv-fantasma", "services/no-existe")
    ]


def test_f001_r2_la_declaracion_real_del_repositorio_no_se_toca(
    tmp_path: Path,
) -> None:
    """Los tests de R2 trabajan sobre ficheros temporales, nunca sobre el real."""
    real = RAIZ / "harness" / "servicios.json"
    antes = real.read_bytes()

    _escribir_declaracion(
        tmp_path,
        [{"nombre": "sv-fantasma", "ruta": "services/no-existe", "lenguaje": "python"}],
    )

    assert real.read_bytes() == antes
