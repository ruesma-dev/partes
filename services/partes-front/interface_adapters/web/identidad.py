# interface_adapters/web/identidad.py
"""F-017 · Quien firma las escrituras del portal: identidad de Easy Auth.

Traduce las cabeceras que el sidecar de autenticacion de Container Apps
inyecta en cada peticion a un **actor**: el texto que se sella en las siete
columnas de autor del portal (`approved_by`, `deleted_by`,
`sigrid_registrado_by`, `created_by`, `updated_by`, `undo_log.actor`).

Todo lo de aqui son **funciones puras**: entra un `Mapping` de cabeceras (o
del entorno) y sale un valor. Sin FastAPI, sin `Settings`, sin `os.environ`,
sin I/O. Quien las ata al mundo real es `_resolver_identidad` en `app.py`,
que es el PUNTO UNICO de identidad del portal (R10).

Va en `interface_adapters/web/` y no en `domain/` a proposito: leer una
cabecera HTTP es un detalle de transporte. El dominio de este proyecto son
partes, lineas, obras y jornadas; «quien manda la peticion» no es una regla
de negocio y el dominio no tiene por que saber que existe Azure.

Dos garantias que conviene tener presentes al leer el codigo:

1. **Nada de aqui puede tumbar una peticion.** Lo que hace este modulo es
   *anotar*, y el mecanismo de anotacion jamas puede hacer fallar la
   operacion anotada (R3, R7, R8). Por eso `actor_desde_token` se traga
   cualquier error y por eso siempre hay un actor no vacio.
2. **El espacio de nombres reservado no se puede fabricar desde fuera**
   (R6). `local:*` y `sin-identidad` solo puede producirlos este modulo, y
   la garantia es estructural: cualquier valor que llegue por cabecera
   invadiendolo se descarta. No depende de que un UPN «no parezca» un
   marcador.

`DEFAULT_REVIEWER` sigue existiendo pero **ya no significa «quien firma el
portal»**: es solo la etiqueta con la que se marca una sesion de desarrollo
local (`local:<DEFAULT_REVIEWER>`). Estando desplegado no firma nada.
"""
from __future__ import annotations

import base64
import binascii
import json
import logging
from collections.abc import Mapping
from typing import Any

logger = logging.getLogger(__name__)

CABECERA_NOMBRE = "X-MS-CLIENT-PRINCIPAL-NAME"
CABECERA_TOKEN = "X-MS-CLIENT-PRINCIPAL"
CABECERA_ID = "X-MS-CLIENT-PRINCIPAL-ID"     # solo para /whoami (R21)

PREFIJO_LOCAL = "local:"
ACTOR_LOCAL_SIN_NOMBRE = "local:sin-identidad"
ACTOR_SIN_IDENTIDAD = "sin-identidad"        # R5b: desplegado y sin cabecera
ACTOR_MAX_LEN = 120          # la columna mas estrecha: undo_log.actor

#: R5c, senal A. Variables que Azure Container Apps inyecta en todos sus
#: contenedores y que en un puesto local no existen. **Verificado en el
#: contenedor real** (`ca-sv4-front`, 2026-08-20, T0 de F-017): las cuatro
#: estan presentes. Deja de ser un supuesto de plataforma.
VARIABLES_DESPLIEGUE: tuple[str, ...] = (
    "CONTAINER_APP_NAME", "CONTAINER_APP_REVISION",
    "CONTAINER_APP_REPLICA_NAME", "CONTAINER_APP_HOSTNAME",
)

#: R2, en orden de preferencia. `preferred_username` primero porque es el
#: que Entra rellena con el UPN; `name` el ultimo porque es un nombre para
#: mostrar y puede repetirse entre personas distintas.
CLAIMS_PREFERIDOS: tuple[str, ...] = (
    "preferred_username", "upn", "email", "emails", "name",
)

SENAL_CABECERA_VISTA = "cabecera-vista"


def normalizar_actor(valor: str | None) -> str | None:
    """R4: quita caracteres de control, recorta, minusculas y trunca a 120.

    Devuelve `None` si no queda nada, para que el llamante distinga «no hay
    identidad» de «hay una identidad vacia».

    Las tres decisiones, por orden de importancia:

    * **Los caracteres de control se eliminan** (no se escapan): un `\\n` en
      un UPN partiria en dos una linea de log y permitiria escribir un
      WARNING falso en Log Analytics.
    * **Minusculas** (DA3): los UPN de Entra son insensibles a mayusculas,
      asi que `Ana@…` y `ana@…` son la misma persona. Sin esto, un
      `GROUP BY approved_by` devolveria dos personas donde hay una.
    * **120 caracteres** (R8): el ancho de la columna mas estrecha. Se
      trunca aqui, una vez y para los siete consumidores, en vez de dejar
      que una identidad larga haga fallar una escritura.
    """
    if not valor:
        return None
    limpio = "".join(c for c in str(valor) if c.isprintable() or c == " ")
    limpio = limpio.strip().lower()[:ACTOR_MAX_LEN].strip()
    return limpio or None


def es_actor_reservado(valor: str | None) -> bool:
    """R6: ¿invade el espacio de nombres que solo el resolutor puede usar?

    `local:*` (cualquier cosa) o exactamente `sin-identidad`. Normaliza por
    su cuenta para que la comprobacion no dependa de que el llamante se
    haya acordado de hacerlo: ` Sin-Identidad ` cuenta igual que
    `sin-identidad`.
    """
    normalizado = normalizar_actor(valor)
    if not normalizado:
        return False
    return (normalizado.startswith(PREFIJO_LOCAL)
            or normalizado == ACTOR_SIN_IDENTIDAD)


def _claims_del_token(token: str) -> dict[str, str]:
    """Los claims del token como mapa `typ -> val`. Nunca lanza."""
    try:
        crudo = base64.b64decode(token, validate=True)
    except (binascii.Error, ValueError, TypeError):
        return {}
    try:
        datos: Any = json.loads(crudo.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return {}
    if not isinstance(datos, dict):
        return {}
    lista = datos.get("claims")
    if not isinstance(lista, list):
        return {}
    mapa: dict[str, str] = {}
    for entrada in lista:
        # Una entrada con basura dentro no puede tumbar la peticion: se
        # ignora y se sigue con las demas.
        if not isinstance(entrada, dict):
            continue
        tipo, valor = entrada.get("typ"), entrada.get("val")
        if isinstance(tipo, str) and isinstance(valor, str):
            mapa.setdefault(tipo, valor)
    return mapa


def actor_desde_token(token: str | None) -> str | None:
    """R2/R3: base64 -> JSON -> primer claim preferido. **NUNCA lanza**.

    Es la via suplente: solo se usa cuando `X-MS-CLIENT-PRINCIPAL-NAME` no
    llega (DA1). Tiene cuatro formas de reventar —base64 invalido, JSON
    invalido, estructura distinta, claim ausente— y las cuatro terminan en
    `None`, que el llamante trata como «no llego la cabecera».
    """
    if not token:
        return None
    claims = _claims_del_token(token)
    for preferido in CLAIMS_PREFERIDOS:
        actor = normalizar_actor(claims.get(preferido))
        if actor:
            return actor
    return None


def senal_de_despliegue(
    entorno: Mapping[str, str], *, cabecera_vista: bool = False,
) -> str | None:
    """R5c: devuelve el NOMBRE de la senal que prueba el despliegue.

    El nombre de la variable encontrada (senal A), `'cabecera-vista'`
    (senal B) o `None` si no hay ninguna. Devolver el nombre y no un `bool`
    es lo que permite a R9 y a `/whoami` decir POR QUE se creyo desplegado
    — y es lo unico que hace diagnosticable el fallo grave de esta feature
    (creerse local estando desplegado).

    La senal A manda sobre la B porque A esta disponible desde el arranque
    y es identica en todas las replicas; B se aprende y depende del
    trafico. Una variable presente pero vacia no prueba nada: es
    indistinguible de que no exista.
    """
    for variable in VARIABLES_DESPLIEGUE:
        if (entorno.get(variable) or "").strip():
            return variable
    return SENAL_CABECERA_VISTA if cabecera_vista else None


def _leer_cabecera(cabeceras: Mapping[str, str], nombre: str) -> str | None:
    """Lee una cabecera sin depender de mayusculas ni del tipo de mapping.

    `request.headers` de Starlette ya es insensible a mayusculas, pero los
    tests le pasan diccionarios normales y las cabeceras HTTP son
    insensibles por definicion (RFC 9110).
    """
    valor = cabeceras.get(nombre)
    if valor:
        return valor
    valor = cabeceras.get(nombre.lower())
    if valor:
        return valor
    objetivo = nombre.lower()
    for clave, bruto in cabeceras.items():
        if str(clave).lower() == objetivo and bruto:
            return bruto
    return None


def _descartar_reservado(actor: str, origen: str) -> None:
    logger.warning(
        "[identidad] la cabecera %s traia un valor del espacio reservado "
        "(%r): se DESCARTA. Ningun valor de origen externo puede firmar "
        "como 'local:...' ni como '%s'.",
        origen, actor, ACTOR_SIN_IDENTIDAD,
    )


def actor_desde_cabeceras(
    cabeceras: Mapping[str, str], *, fallback: str | None,
    desplegado: bool,
) -> tuple[str, str]:
    """R1/R2/R5/R5b/R6/R7: devuelve `(actor, origen)`.

    `origen`: `'cabecera-name'` | `'cabecera-token'` | `'local'` |
    `'sin-identidad-desplegado'`. **El actor NUNCA es vacio ni `None`**: a
    partir de F-017, un `NULL` en una columna de autor significa
    exclusivamente «fila anterior al corte» (R7, R22).

    `fallback` es `DEFAULT_REVIEWER`, y solo se usa **sin desplegar**: es
    la etiqueta de la sesion local, no una firma. `desplegado` lo decide
    `senal_de_despliegue`, que se pregunta aparte para que esta funcion no
    tenga que leer el entorno del proceso.

    Un valor reservado que llegue por cabecera se descarta y se sigue el
    flujo **como si esa cabecera no existiera** (R6): un `-NAME`
    envenenado no impide que el token, si viene, identifique de verdad.
    """
    # 1) La via principal: el principal en claro (DA1).
    actor = normalizar_actor(_leer_cabecera(cabeceras, CABECERA_NOMBRE))
    if actor and es_actor_reservado(actor):
        _descartar_reservado(actor, CABECERA_NOMBRE)
        actor = None
    if actor:
        return actor, "cabecera-name"

    # 2) La suplente: el token base64 de claims.
    actor = actor_desde_token(_leer_cabecera(cabeceras, CABECERA_TOKEN))
    if actor and es_actor_reservado(actor):
        _descartar_reservado(actor, CABECERA_TOKEN)
        actor = None
    if actor:
        return actor, "cabecera-token"

    # 3) Sin identidad. Las DOS ramas del fallback (DA4, enmienda del
    #    humano del 2026-08-20): solo la de desarrollo lleva `local:`.
    #    Escribir `local:` estando desplegado seria AFIRMAR algo falso
    #    —que la fila vino de un puesto de desarrollo— y taparia una caida
    #    de la autenticacion en una columna, en silencio.
    if desplegado:
        return ACTOR_SIN_IDENTIDAD, "sin-identidad-desplegado"

    etiqueta = normalizar_actor(fallback)
    if not etiqueta or es_actor_reservado(etiqueta):
        return ACTOR_LOCAL_SIN_NOMBRE, "local"
    return (PREFIJO_LOCAL + etiqueta)[:ACTOR_MAX_LEN], "local"
