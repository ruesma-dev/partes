# validar_datos_sesame.py
"""Informe de VALIDACION de los datos de Sesame, trabajador a trabajador.

Herramienta de consola de SOLO LECTURA (F-013). No toca la BBDD `partes`,
ni Sigrid, ni el portal: solo pregunta a `sesame-api` y escribe dos
ficheros. Existe para que el humano compare contra la realidad lo que
F-003 va a usar en el cómputo de extras (sv3) y en los avisos de jornada
incompleta (sv4) ANTES de encender nada, y para alimentar F-011 (jornada
reducida por días) y F-012 (candef de 9h y viernes).

Qué hace:
  1. Pide a sesame-api la lista de empleados (`GET /api/v1/empleados`).
  2. Por cada uno, con el MISMO `SesameApiClient` que usa el portal:
     sus festivos del año y la jornada de su contrato.
  3. Consulta una vez el calendario por defecto (sección propia).
  4. Escribe `informe_sesame_<año>_<YYYYMMDD-HHMM>.md` y su `.csv`.

Se usa el cliente EN CRUDO, no el `CalendarioProvider`: la cascada de
respaldo del proveedor taparía justo lo que aquí interesa ver — un 404 es
"Sesame no casa ese DNI", y eso tiene que salir como una fila con error,
no disimularse con el calendario por defecto.

Un fallo de un trabajador (404, upstream caído, dato raro) se anota en su
fila y el barrido continúa. Solo se aborta si falla el listado inicial o
si falta configuración: sin lista de empleados no hay informe.

El informe lleva DNIs: por eso la carpeta de salida por defecto es
`services/partes-front/logs/`, que está en el `.gitignore`. NO se versiona.

USO:
  cd services/partes-front
  python validar_datos_sesame.py --api-key <clave>
  python validar_datos_sesame.py --base-url http://localhost:8006 \
      --api-key <clave> --ano 2026
  python validar_datos_sesame.py --incluir-inactivos --salida C:\\temp

Configuración (por orden de precedencia): argumento de línea de órdenes >
fichero pasado con `--env` > variables de entorno `SESAME_API_BASE_URL` /
`SESAME_API_KEY` (los mismos nombres que `config/settings.py`) > el valor
por defecto `http://localhost:8006`. La clave NUNCA se escribe en el
informe ni en el log.
"""
from __future__ import annotations

import argparse
import csv
import io
import logging
import os
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import httpx
from infrastructure.sesame.sesame_api_client import (
    FestivoDia,
    JornadaContrato,
    SesameApiClient,
)

logger = logging.getLogger("validar_datos_sesame")

_LOG_PREFIX = "[validar-sesame]"

#: Instancia local de sesame-api levantada a mano (ver su README).
BASE_URL_POR_DEFECTO = "http://localhost:8006"

#: Carpeta ignorada por git: el informe lleva DNIs y no se versiona.
SALIDA_POR_DEFECTO = Path(__file__).resolve().parent / "logs"

#: Marca de "Sesame no lo dice", distinta de un valor real.
DESCONOCIDO = "(desconocido)"

#: Etiqueta de los trabajadores cuyos festivos NO se pudieron leer. No es
#: un recuento de festivos: por eso no entra en el reparto como un numero.
ILEGIBLE = "(no se pudo leer)"

#: Orden de las columnas, compartido por el CSV y la tabla Markdown.
COLUMNAS: tuple[str, ...] = (
    "nombre",
    "dni",
    "estado",
    "n_festivos",
    "festivos",
    "jornada_tipo",
    "reducida",
    "tipo_contrato",
    "error",
)

#: Los cuerpos de error se recortan antes de anotarlos en una celda.
_MAX_CUERPO = 300


# ------------------------------------------------------------------ #
# Modelo del informe.
# ------------------------------------------------------------------ #
@dataclass(frozen=True)
class FilaTrabajador:
    """Lo que se sabe de UN trabajador tras preguntar a Sesame."""
    nombre: str
    dni: str
    estado: str
    festivos: tuple[FestivoDia, ...]
    #: False si los festivos no se pudieron leer (no es lo mismo que cero).
    festivos_ok: bool
    jornada: JornadaContrato | None
    #: Vacío si todo fue bien; si no, los fallos separados por " | ".
    error: str


@dataclass(frozen=True)
class Resumen:
    """Los agregados que el humano mira antes de bajar a la tabla."""
    total: int
    con_error: int
    #: Reparto de "cuantos festivos tiene" entre los que SI se pudieron leer.
    dist_festivos: dict[int, int]
    #: Los demas. Sin este contador, `dist_festivos` no suma `total` y el
    #: humano no sabe si faltan trabajadores o es que se contaron mal.
    festivos_ilegibles: int
    dist_tipo: dict[str, int]
    dist_reducida: dict[str, int]
    dnis_con_error: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class MetaInforme:
    """Cabecera del informe: de dónde salieron los datos y cuándo."""
    generado: str
    base_url: str
    ano: int
    solo_activos: bool


# ------------------------------------------------------------------ #
# Lógica pura: construir filas.
# ------------------------------------------------------------------ #
def fmt_bool(valor: bool | None) -> str:
    """`reducida` es tri-estado: sí, no, o Sesame no lo dice."""
    if valor is None:
        return DESCONOCIDO
    return "si" if valor else "no"


def fmt_festivos(festivos: Iterable[FestivoDia]) -> str:
    """`fecha nombre | fecha nombre`, en una sola celda."""
    partes = []
    for festivo in festivos:
        partes.append(
            f"{festivo.fecha} {festivo.nombre}" if festivo.nombre
            else festivo.fecha
        )
    return " | ".join(partes)


def dni_de(empleado: dict[str, Any]) -> str:
    """DNI con el que preguntar a Sesame: el normalizado manda."""
    for campo in ("dni_norm", "dni"):
        valor = empleado.get(campo)
        if valor is not None and str(valor).strip():
            return str(valor).strip()
    return ""


def nombre_de(empleado: dict[str, Any]) -> str:
    """Nombre completo, con el mismo criterio que el dominio de sesame-api."""
    trozos = [str(empleado.get(c) or "").strip() for c in ("nombre", "apellidos")]
    return " ".join(t for t in trozos if t)


def construir_fila(
    empleado: dict[str, Any], cliente: SesameApiClient, ano: int
) -> FilaTrabajador:
    """Pregunta festivos y jornada de UN empleado; nunca lanza.

    Todo lo que falle acaba en la columna `error` de su fila: el barrido
    tiene que llegar hasta el último trabajador aunque Sesame no conozca
    a la mitad (acceptance 2 de F-013).
    """
    dni = dni_de(empleado)
    nombre = nombre_de(empleado)
    estado = str(empleado.get("estado") or DESCONOCIDO)
    errores: list[str] = []

    if not dni:
        return FilaTrabajador(
            nombre=nombre, dni="", estado=estado, festivos=(),
            festivos_ok=False, jornada=None,
            error="empleado sin DNI en Sesame: no hay nada que consultar",
        )

    festivos: tuple[FestivoDia, ...] = ()
    festivos_ok = False
    try:
        leidos = cliente.festivos(dni, ano)
        if leidos is None:
            errores.append("festivos: 404, Sesame no conoce ese DNI")
        else:
            festivos = tuple(leidos)
            festivos_ok = True
    except Exception as exc:                      # noqa: BLE001 (diagnóstico)
        errores.append(f"festivos: {_recorta(exc)}")

    jornada: JornadaContrato | None = None
    try:
        jornada = cliente.jornada(dni)
        if jornada is None:
            errores.append("jornada: 404, Sesame no conoce ese DNI")
    except Exception as exc:                      # noqa: BLE001 (diagnóstico)
        errores.append(f"jornada: {_recorta(exc)}")

    if errores:
        logger.warning("%s %s (%s): %s", _LOG_PREFIX, nombre, dni,
                       " | ".join(errores))
    return FilaTrabajador(
        nombre=nombre, dni=dni, estado=estado, festivos=festivos,
        festivos_ok=festivos_ok, jornada=jornada, error=" | ".join(errores),
    )


def resumir(filas: Sequence[FilaTrabajador]) -> Resumen:
    """Agregados del barrido. Sin E/S: se testea sola."""
    dist_festivos: dict[int, int] = {}
    dist_tipo: dict[str, int] = {}
    dist_reducida: dict[str, int] = {}
    con_error: list[tuple[str, str]] = []
    ilegibles = 0

    for fila in filas:
        if fila.festivos_ok:
            clave = len(fila.festivos)
            dist_festivos[clave] = dist_festivos.get(clave, 0) + 1
        else:
            ilegibles += 1
        tipo = (fila.jornada.tipo if fila.jornada else None) or DESCONOCIDO
        dist_tipo[tipo] = dist_tipo.get(tipo, 0) + 1
        reducida = fmt_bool(fila.jornada.reducida if fila.jornada else None)
        dist_reducida[reducida] = dist_reducida.get(reducida, 0) + 1
        if fila.error:
            con_error.append((fila.dni, fila.error))

    return Resumen(
        total=len(filas),
        con_error=len(con_error),
        dist_festivos=dist_festivos,
        festivos_ilegibles=ilegibles,
        dist_tipo=dist_tipo,
        dist_reducida=dist_reducida,
        dnis_con_error=tuple(con_error),
    )


def celdas_de(fila: FilaTrabajador) -> list[str]:
    """La fila en el orden de `COLUMNAS`, ya como texto."""
    jornada = fila.jornada
    return [
        fila.nombre,
        fila.dni,
        fila.estado,
        str(len(fila.festivos)) if fila.festivos_ok else DESCONOCIDO,
        fmt_festivos(fila.festivos),
        (jornada.tipo if jornada else None) or DESCONOCIDO,
        fmt_bool(jornada.reducida if jornada else None),
        (jornada.tipo_contrato if jornada else None) or DESCONOCIDO,
        fila.error,
    ]


# ------------------------------------------------------------------ #
# Lógica pura: render.
# ------------------------------------------------------------------ #
def render_csv(filas: Sequence[FilaTrabajador]) -> str:
    """CSV con `;` (Excel español, docs/CONVENTIONS.md)."""
    buffer = io.StringIO()
    escritor = csv.writer(buffer, delimiter=";", lineterminator="\n")
    escritor.writerow(COLUMNAS)
    for fila in filas:
        escritor.writerow(celdas_de(fila))
    return buffer.getvalue()


def render_markdown(
    *,
    meta: MetaInforme,
    filas: Sequence[FilaTrabajador],
    resumen: Resumen,
    calendario: Sequence[FestivoDia] | None,
    calendario_error: str,
) -> str:
    """El informe legible. Nunca incluye la clave de API."""
    out: list[str] = [
        "# Informe de validacion de datos Sesame",
        "",
        f"- Generado: {meta.generado}",
        f"- sesame-api: {meta.base_url}",
        f"- Ano: {meta.ano}",
        f"- Ambito: {'solo activos' if meta.solo_activos else 'todos'}",
        f"- Empleados: {resumen.total} ({resumen.con_error} con errores)",
        "",
        "## Calendario por defecto",
        "",
    ]
    if calendario_error:
        out.append(f"No se pudo consultar: {calendario_error}")
    elif calendario is None:
        out.append("Ningun calendario esta marcado `por_defecto` en Sesame.")
    elif not calendario:
        out.append(f"El calendario por defecto no tiene festivos en {meta.ano}.")
    else:
        out.append(f"{len(calendario)} festivos en {meta.ano}:")
        out.append("")
        for festivo in calendario:
            out.append(f"- {festivo.fecha} {festivo.nombre or ''}".rstrip())

    out += ["", "## Resumen", ""]
    reparto_festivos = {f"{k} festivos": v
                        for k, v in sorted(resumen.dist_festivos.items())}
    if resumen.festivos_ilegibles:
        # Cierra la suma: con esta linea, la lista suma el total de la
        # cabecera y se ve de un vistazo que no falta nadie por el camino.
        reparto_festivos[ILEGIBLE] = resumen.festivos_ilegibles
    out += _lista_distribucion("Festivos por trabajador", reparto_festivos)
    out += _lista_distribucion("Tipo de jornada", resumen.dist_tipo)
    out += _lista_distribucion("Jornada reducida", resumen.dist_reducida)
    out += ["**Trabajadores con error**", ""]
    if resumen.dnis_con_error:
        for dni, error in resumen.dnis_con_error:
            out.append(f"- `{dni or '(sin dni)'}`: {error}")
    else:
        out.append("- ninguno")

    out += ["", "## Trabajadores", ""]
    out.append("| " + " | ".join(COLUMNAS) + " |")
    out.append("|" + "|".join(["---"] * len(COLUMNAS)) + "|")
    for fila in filas:
        out.append("| " + " | ".join(_celda(c) for c in celdas_de(fila)) + " |")

    out.append("")
    return "\n".join(out)


def _lista_distribucion(titulo: str, dist: dict[str, int]) -> list[str]:
    lineas = [f"**{titulo}**", ""]
    if not dist:
        lineas += ["- (sin datos)", ""]
        return lineas
    for clave, cuantos in dist.items():
        lineas.append(f"- {clave}: {cuantos} trabajador"
                      f"{'es' if cuantos != 1 else ''}")
    lineas.append("")
    return lineas


def _celda(texto: str) -> str:
    """Una barra en un dato partiría la tabla Markdown en dos."""
    return texto.replace("|", r"\|").replace("\n", " ")


def _recorta(exc: Exception) -> str:
    return str(exc)[:_MAX_CUERPO] or exc.__class__.__name__


# ------------------------------------------------------------------ #
# E/S: sesame-api y ficheros.
# ------------------------------------------------------------------ #
def listar_empleados(
    *,
    base_url: str,
    api_key: str,
    solo_activos: bool,
    timeout_s: float,
    transport: httpx.BaseTransport | None = None,
) -> list[dict[str, Any]]:
    """`GET /api/v1/empleados`. `RuntimeError` ante cualquier fallo.

    Deliberadamente NO vive en `infrastructure/sesame/sesame_api_client.py`:
    ese cliente es duplicación tolerada gemela con el de sv3 (CLAUDE.md), y
    ningún servicio necesita listar empleados. Añadirle un método obligaría
    a tocar las dos copias por una herramienta de consola.
    """
    url = f"{base_url.rstrip('/')}/api/v1/empleados"
    params = {"solo_activos": "true" if solo_activos else "false"}
    headers = {"x-api-key": api_key}
    transporte = transport or httpx.HTTPTransport(retries=1)
    try:
        with httpx.Client(timeout=timeout_s, transport=transporte) as cliente:
            respuesta = cliente.get(url, params=params, headers=headers)
    except httpx.HTTPError as exc:
        raise RuntimeError(
            f"sesame-api no responde en {url}: {exc!r}"
        ) from exc

    texto = (respuesta.text or "")[:_MAX_CUERPO]
    if respuesta.status_code >= 400:
        raise RuntimeError(
            f"sesame-api respondio {respuesta.status_code} al listar "
            f"empleados: {texto}"
        )
    try:
        cuerpo = respuesta.json()
    except ValueError as exc:
        raise RuntimeError(
            f"sesame-api: respuesta no JSON al listar empleados: {texto}"
        ) from exc
    if not isinstance(cuerpo, dict) or not cuerpo.get("ok", False):
        raise RuntimeError(
            f"sesame-api devolvio ok=false al listar empleados: {texto}"
        )
    datos = cuerpo.get("data")
    if not isinstance(datos, list):
        # TRY004 silenciada: un contrato roto del servicio remoto no es un
        # error de tipos del programa. RuntimeError es la senal de "aborta"
        # de este modulo, igual que en SesameApiClient.
        raise RuntimeError(  # noqa: TRY004
            f"sesame-api: 'data' no es una lista al listar empleados: {texto}"
        )
    return [item for item in datos if isinstance(item, dict)]


def calendario_por_defecto(
    cliente: SesameApiClient, ano: int
) -> tuple[tuple[FestivoDia, ...] | None, str]:
    """Sección propia del informe. Su fallo no tumba el barrido."""
    try:
        festivos = cliente.calendario_por_defecto(ano)
    except Exception as exc:                      # noqa: BLE001 (diagnóstico)
        logger.warning("%s calendario por defecto: %s", _LOG_PREFIX, exc)
        return None, _recorta(exc)
    if festivos is None:
        return None, ""
    return tuple(festivos), ""


def escribir_informe(
    *, salida: Path, ano: int, markdown: str, csv_texto: str, ahora: datetime
) -> tuple[Path, Path]:
    """Escribe los dos ficheros y devuelve sus rutas."""
    salida.mkdir(parents=True, exist_ok=True)
    base = f"informe_sesame_{ano}_{ahora.strftime('%Y%m%d-%H%M')}"
    ruta_md = salida / f"{base}.md"
    ruta_csv = salida / f"{base}.csv"
    ruta_md.write_text(markdown, encoding="utf-8")
    # utf-8-sig: Excel español no reconoce el UTF-8 sin BOM (CONVENTIONS).
    ruta_csv.write_text(csv_texto, encoding="utf-8-sig")
    return ruta_md, ruta_csv


def leer_env(ruta: Path) -> dict[str, str]:
    """Lector minimalista de `.env` (mismo patrón que los scripts de sv5)."""
    valores: dict[str, str] = {}
    if not ruta.exists():
        raise RuntimeError(f"no existe el fichero de entorno {ruta}")
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        valores[clave.strip()] = valor.strip().strip('"').strip("'")
    return valores


# ------------------------------------------------------------------ #
# Punto de entrada.
# ------------------------------------------------------------------ #
def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Informe de validacion de los datos de Sesame por "
                    "trabajador (solo lectura).",
    )
    parser.add_argument("--base-url", default=None,
                        help=f"URL de sesame-api (por defecto: "
                             f"{BASE_URL_POR_DEFECTO})")
    parser.add_argument("--api-key", default=None,
                        help="clave x-api-key de sesame-api")
    parser.add_argument("--env", default=None, type=Path,
                        help="fichero .env del que leer SESAME_API_*")
    # Hora LOCAL a proposito (aqui y en la marca de tiempo del fichero): el
    # "ano en curso" y el sello del informe son los del humano que lo lanza.
    parser.add_argument("--ano", type=int, default=date.today().year,  # noqa: DTZ011
                        help="ano de los festivos (por defecto, el actual)")
    parser.add_argument("--salida", type=Path, default=SALIDA_POR_DEFECTO,
                        help=f"carpeta del informe (por defecto: "
                             f"{SALIDA_POR_DEFECTO})")
    parser.add_argument("--timeout", type=float, default=10.0,
                        help="timeout por peticion, en segundos")
    ambito = parser.add_mutually_exclusive_group()
    ambito.add_argument("--solo-activos", action="store_true",
                        help="solo empleados activos (comportamiento normal)")
    ambito.add_argument("--incluir-inactivos", action="store_true",
                        help="incluir tambien a los empleados de baja")
    return parser.parse_args(list(argv) if argv is not None else None)


def _config(args: argparse.Namespace) -> tuple[str, str]:
    """base_url y api_key: CLI > fichero --env > entorno > por defecto."""
    del_env: dict[str, str] = leer_env(args.env) if args.env else {}
    base_url = (
        args.base_url
        or del_env.get("SESAME_API_BASE_URL")
        or os.environ.get("SESAME_API_BASE_URL")
        or BASE_URL_POR_DEFECTO
    )
    api_key = (
        args.api_key
        or del_env.get("SESAME_API_KEY")
        or os.environ.get("SESAME_API_KEY")
        or ""
    )
    return base_url.strip(), api_key.strip()


def main(
    argv: Sequence[str] | None = None,
    *,
    transport: httpx.BaseTransport | None = None,
) -> int:
    """Devuelve 0 si el informe se generó; distinto de 0 si se abortó."""
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.INFO, stream=sys.stderr,
        format="%(levelname)s %(name)s: %(message)s",
    )
    # httpx loguea una linea por peticion (con el DNI en la query): con 200
    # trabajadores la consola se vuelve ilegible y el aviso util se pierde.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    try:
        base_url, api_key = _config(args)
    except RuntimeError as exc:
        print(f"ABORTADO: {exc}", file=sys.stderr)
        return 2
    if not api_key:
        print(
            "ABORTADO: falta la clave de sesame-api. Pasala con --api-key, "
            "en SESAME_API_KEY o en el fichero de --env.",
            file=sys.stderr,
        )
        return 2

    solo_activos = not args.incluir_inactivos
    ano = int(args.ano)
    logger.info("%s sesame-api=%s ano=%s solo_activos=%s",
                _LOG_PREFIX, base_url, ano, solo_activos)

    try:
        empleados = listar_empleados(
            base_url=base_url, api_key=api_key, solo_activos=solo_activos,
            timeout_s=args.timeout, transport=transport,
        )
    except RuntimeError as exc:
        print(f"ABORTADO: {exc}", file=sys.stderr)
        return 1

    cliente = SesameApiClient(
        base_url=base_url, api_key=api_key, timeout_s=args.timeout,
        transport=transport,
    )
    filas = [construir_fila(empleado, cliente, ano) for empleado in empleados]
    calendario, calendario_error = calendario_por_defecto(cliente, ano)
    resumen = resumir(filas)
    ahora = datetime.now()  # noqa: DTZ005 (hora local: la del humano)
    meta = MetaInforme(
        generado=ahora.strftime("%Y-%m-%d %H:%M"), base_url=base_url,
        ano=ano, solo_activos=solo_activos,
    )

    ruta_md, ruta_csv = escribir_informe(
        salida=args.salida, ano=ano, ahora=ahora,
        markdown=render_markdown(
            meta=meta, filas=filas, resumen=resumen,
            calendario=calendario, calendario_error=calendario_error,
        ),
        csv_texto=render_csv(filas),
    )

    print(f"Empleados: {resumen.total} ({resumen.con_error} con errores)")
    print(f"Markdown: {ruta_md}")
    print(f"CSV     : {ruta_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
