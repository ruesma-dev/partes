# tests/f059_sdk_falsos.py
"""F-059 · Dobles de los SDK de IA para importar los clientes sin tenerlos.

El ``.venv`` de la raíz, con el que el arnés ejecuta la suite de sv2, no
tiene ``openai``, ``anthropic`` ni ``google-genai`` (van en la imagen de sv2,
``infra/manifests/sv2/requirements.txt``, no en el entorno de tests). Los
clientes de ``infrastructure/llm/`` solo tocan el SDK al construirse y al
llamar: importarlos y probar lo que hacen antes de llamar (``_build_input``,
el cableado de ``build_app``) no necesita el SDK real.

``instalar_si_faltan()`` registra un módulo falso SOLO si el real no se
puede importar; con el SDK instalado no cambia nada. Nada de red: el
cliente falso no tiene métodos que llamen a ningún sitio.
"""
from __future__ import annotations

import importlib
import sys
import types


class ClienteSdkFalso:
    """Sustituye a ``openai.OpenAI``, ``anthropic.Anthropic`` y ``genai.Client``."""

    def __init__(self, *args, **kwargs) -> None:
        self.responses = types.SimpleNamespace(parse=None, create=None)
        self.messages = types.SimpleNamespace(create=None)
        self.models = types.SimpleNamespace(generate_content=None)


def _importable(nombre: str) -> bool:
    try:
        importlib.import_module(nombre)
    except ImportError:
        return False
    return True


def _registrar(nombre: str, **atributos) -> types.ModuleType:
    modulo = sys.modules.get(nombre) or types.ModuleType(nombre)
    modulo.__dict__.update(atributos)
    sys.modules[nombre] = modulo
    return modulo


def instalar_si_faltan() -> None:
    if not _importable("openai"):
        _registrar("openai", OpenAI=ClienteSdkFalso)
    if not _importable("anthropic"):
        _registrar("anthropic", Anthropic=ClienteSdkFalso)
    if not _importable("google.genai"):
        tipos = _registrar("google.genai.types")
        genai = _registrar("google.genai", Client=ClienteSdkFalso, types=tipos)
        if not _importable("google"):
            _registrar("google", __path__=[])
        sys.modules["google"].genai = genai
