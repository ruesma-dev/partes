# contrastar_festivos_sesame.py
"""F-032, F-077 · Contraste de los festivos de Sesame con el respaldo (SOLO LECTURA).

Herramienta de consola que el humano corre ANTES de encender Sesame en
produccion (puerta DA12, M2 y M3 de la guia de despliegue):

  - R29 (F-077, R24): pide UNA vez los calendarios de Sesame HR
    (``GET /schedule/v1/holiday-calendar``, paginado) y compara cada
    calendario con el JSON de respaldo de sv3 (consultado dia a dia): dias
    solo-Sesame y solo-respaldo de lunes a viernes, recuento y si es el
    calendario por defecto.
  - R30: marca ``INCOMPLETO`` (menos de ``--festivos-minimos`` festivos en
    el ano; por defecto el de settings o 1) y ``FALTAN DEL RESPALDO`` (le
    falta algun festivo del JSON). Con un ``FALTAN DEL RESPALDO`` no se
    enciende; con un ``INCOMPLETO``, a RRHH.
  - R32: con ``--impacto``, lee las lineas de los partes activos
    (``fetch_registros_para_recurso``), pide los festivos de cada DNI con
    el adaptador de la ingesta (``FestivosSesameHr``: DNI fuera del indice
    = el respaldo, F-077 R26) y clasifica cada linea con
    horas, fuera de la papelera, de un dia que cambia o de su semana ISO:
    ``libre``, ``reajustable`` o ``dura``. Un DNI que falla es una fila de
    error. Los DNIs van SOLO al CSV, nunca al Markdown ni a la consola.
  - R31: escribe ``contraste_festivos_<N>_<YYYYMMDD-HHMM>.md`` y ``.csv``
    (UTF-8 con BOM, ``;``) en ``logs/`` (o ``--salida``) y sale 0. Si falla
    la configuracion, el listado o la lectura de ``partes``, sale con otro
    codigo y no escribe nada.

R33: no escribe en ``partes`` ni en Sigrid y a Sesame solo le hace
``GET`` (el cliente no tiene otro verbo). La base se abre en ``READ ONLY``.

F-077 (R25): la URL sale de ``--base-url`` o de ``SESAME_BASE_URL`` y solo
vale ``https://``. El token, SOLO de ``SESAME_TOKEN`` (el ``.env`` de sv3 o
el entorno) o, si falta, pedido por consola sin eco: no hay opcion de linea
de comandos para el token (quedaria en el historial de la consola).

USO (desde services/partes-persistencia):
  ../../.venv/Scripts/python.exe contrastar_festivos_sesame.py --ano 2026 \\
      [--base-url https://<api de la region>] [--impacto]
"""
from __future__ import annotations

import argparse
import csv
import getpass
import io
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, TextIO

import httpx

from application.services import text_match as tm
from application.services.festivos_guardados import del_ano
from application.services.reajuste_reparto import LIBRE, clase_linea
from application.services.recurso_conciliador import _congelado
from infrastructure.calendario.json_calendario_laboral import (
    JsonCalendarioLaboral,
)
from infrastructure.sesame.festivos_sesame_hr import FestivosSesameHr
from infrastructure.sesame.sesame_hr_client import SesameHrClient

#: Carpeta de salida por defecto (ignorada por git), junto a este fichero.
CARPETA_LOGS = Path(__file__).resolve().parent / "logs"

#: Codigos de salida distintos de 0 (R31).
SALIDA_CONFIGURACION = 2
SALIDA_LISTADO = 3
SALIDA_IMPACTO = 4

COLUMNAS_CSV = (
    "tipo", "calendario_id", "calendario", "por_defecto", "n_festivos",
    "solo_sesame", "solo_respaldo", "incompleto", "faltan_del_respaldo",
    "dni", "registro_id", "document_id", "fecha", "obra_ide", "clase",
    "sentido", "error",
)


# ------------------------------------------------------------------ #
# Puras.
# ------------------------------------------------------------------ #
def _dias_del_ano(ano: int) -> Iterable[date]:
    d = date(ano, 1, 1)
    while d.year == ano:
        yield d
        d += timedelta(days=1)


def _respaldo_lv(respaldo: Any, ano: int) -> set[str]:
    """Los dias de lunes a viernes que el respaldo da por no laborables."""
    return {d.isoformat() for d in _dias_del_ano(ano)
            if d.weekday() < 5 and respaldo.es_no_laborable(d.isoformat())}


def contrastar_calendario(
    calendario: Mapping, ano: int, respaldo: Any, *, minimo: int = 1
) -> dict:
    """R29, R30: un calendario de Sesame frente al JSON de respaldo."""
    festivos = del_ano(
        ((f.get("fecha"), f.get("nombre"))
         for f in (calendario.get("festivos") or []) if isinstance(f, dict)),
        ano)
    sesame_lv = {f for f in festivos if date.fromisoformat(f).weekday() < 5}
    respaldo_lv = _respaldo_lv(respaldo, ano)
    solo_respaldo = sorted(respaldo_lv - sesame_lv)
    return {
        "id": calendario.get("id"),
        "nombre": calendario.get("nombre"),
        "por_defecto": bool(calendario.get("por_defecto")),
        "n_festivos": len(festivos),
        "solo_sesame": sorted(sesame_lv - respaldo_lv),
        "solo_respaldo": solo_respaldo,
        "incompleto": len(festivos) < minimo,
        "faltan_del_respaldo": bool(solo_respaldo),
    }


def _fecha_iso(fecha_int: Any) -> str | None:
    try:
        texto = f"{int(fecha_int):08d}"
        return date(int(texto[:4]), int(texto[4:6]), int(texto[6:])).isoformat()
    except (TypeError, ValueError):
        return None


def clasificar_impacto(
    registros: Iterable[Mapping], festivos_por_dni: Mapping[str, Any],
    respaldo: Any, ano: int,
) -> dict:
    """R32: que lineas de ``ano`` cambiarian con los festivos de Sesame.

    ``festivos_por_dni``: DNI normalizado -> ``{fecha ISO: nombre}`` (su
    calendario), ``None`` (404: sigue con el respaldo, no cambia nada) o la
    excepcion con la que fallo (una fila de error). Un dia CAMBIA si Sesame
    y el respaldo no coinciden en si es laborable; una linea entra si su
    dia cambia (``a_festivo``/``a_laborable``) o si otro de su semana ISO
    cambia (``semana``). Sin DNI tampoco cambia: va al respaldo igual.
    """
    errores: list[dict] = []
    cambios: dict[str, dict[str, str]] = {}      # dni -> {dia: sentido}
    for dni, festivos in sorted(festivos_por_dni.items()):
        if isinstance(festivos, BaseException):
            errores.append({"dni": dni, "error": type(festivos).__name__})
            continue
        if festivos is None:
            continue
        propios: dict[str, str] = {}
        for d in _dias_del_ano(ano):
            if d.weekday() >= 5:
                continue
            iso = d.isoformat()
            nuevo = iso in festivos
            viejo = bool(respaldo.es_no_laborable(iso, dni=dni))
            if nuevo != viejo:
                propios[iso] = "a_festivo" if nuevo else "a_laborable"
        cambios[dni] = propios

    lineas: list[dict] = []
    for reg in registros:
        dni = tm.normalize_dni(reg.get("empleado_dni"))
        iso = _fecha_iso(reg.get("fecha_int"))
        if (not dni or dni not in cambios or iso is None
                or not iso.startswith(f"{ano:04d}-")
                or reg.get("deleted_at_utc") or not (reg.get("horas") or 0)):
            continue
        propios = cambios[dni]
        dia = date.fromisoformat(iso)
        semana = dia.isocalendar()[:2]
        if iso in propios:
            sentido = propios[iso]
        elif any(date.fromisoformat(c).isocalendar()[:2] == semana
                 for c in propios):
            sentido = "semana"
        else:
            continue
        lineas.append({
            "dni": dni, "registro_id": reg.get("registro_id"),
            "document_id": reg.get("document_id"), "fecha": iso,
            "obra_ide": reg.get("obra_ide"),
            "clase": clase_linea(reg, congelada=_congelado(dict(reg))),
            "sentido": sentido,
        })

    def _contar(clave) -> dict:
        out: dict = {}
        for f in lineas:
            k = clave(f)
            out[k] = out.get(k, 0) + 1
        return out

    clases_por_dia: dict[tuple, set[bool]] = {}
    for f in lineas:
        clases_por_dia.setdefault((f["dni"], f["fecha"]), set()).add(
            f["clase"] == LIBRE)
    return {
        "lineas": lineas,
        "errores": errores,
        "por_ano": _contar(lambda f: int(f["fecha"][:4])),
        "por_obra_mes": _contar(lambda f: (f["obra_ide"], f["fecha"][:7])),
        "por_clase": _contar(lambda f: f["clase"]),
        "por_sentido": _contar(lambda f: f["sentido"]),
        "dias_mixtos": sum(1 for v in clases_por_dia.values() if len(v) == 2),
    }


def _lista(dias: list[str]) -> str:
    return ", ".join(dias) if dias else "—"


def render_markdown(
    ano: int, filas: list[dict], impacto: dict | None, *, momento: str
) -> str:
    """El informe para el humano. Sin DNIs (R32): solo recuentos."""
    out = [f"# Contraste de festivos Sesame / respaldo · {ano}", "",
           f"Generado: {momento}. Solo lectura.", "",
           "## Calendarios de Sesame", "",
           "| Calendario | Festivos | Solo Sesame (L-V) | Solo respaldo (L-V)"
           " | Puerta |",
           "|---|---|---|---|---|"]
    for f in filas:
        marcas = []
        if f["faltan_del_respaldo"]:
            marcas.append("**FALTAN DEL RESPALDO**")
        if f["incompleto"]:
            marcas.append("**INCOMPLETO**")
        nombre = f"{f['nombre'] or '?'} (`{f['id'] or '?'}`)"
        if f["por_defecto"]:
            nombre += " · por defecto"
        out.append(f"| {nombre} | {f['n_festivos']} | "
                   f"{_lista(f['solo_sesame'])} | "
                   f"{_lista(f['solo_respaldo'])} | "
                   f"{' '.join(marcas) or 'ok'} |")
    if not filas:
        out.append("| (ningun calendario) | 0 | — | — | — |")
    out += ["", "`FALTAN DEL RESPALDO`: no se enciende (DA12). "
                "`INCOMPLETO`: a RRHH antes de encender.", ""]
    if impacto is None:
        return "\n".join(out) + "\n"
    out += ["## Impacto en los partes activos", "",
            f"Lineas afectadas: {len(impacto['lineas'])}. "
            f"Dias mixtos (libres y congeladas el mismo dia): "
            f"{impacto['dias_mixtos']}. "
            f"DNIs que fallaron: {len(impacto['errores'])}.", ""]
    for titulo, clave in (("Por clase", "por_clase"),
                          ("Por sentido", "por_sentido"),
                          ("Por año", "por_ano")):
        out += [f"### {titulo}", "", "| | Lineas |", "|---|---|"]
        out += [f"| {k} | {v} |" for k, v in sorted(impacto[clave].items())]
        out.append("")
    out += ["### Por obra y mes", "", "| Obra | Mes | Lineas |", "|---|---|---|"]
    out += [f"| {obra} | {mes} | {n} |" for (obra, mes), n in sorted(
        impacto["por_obra_mes"].items(), key=lambda kv: (str(kv[0][0]),
                                                         kv[0][1]))]
    out.append("")
    return "\n".join(out) + "\n"


def escribir_csv(destino: TextIO, filas: list[dict],
                 impacto: dict | None) -> None:
    """Una fila por calendario, por linea afectada y por DNI fallido."""
    w = csv.writer(destino, delimiter=";", lineterminator="\n")
    w.writerow(COLUMNAS_CSV)
    vacio = dict.fromkeys(COLUMNAS_CSV, "")
    for f in filas:
        w.writerow(list(dict(
            vacio, tipo="calendario", calendario_id=f["id"] or "",
            calendario=f["nombre"] or "", por_defecto=int(f["por_defecto"]),
            n_festivos=f["n_festivos"], solo_sesame=" ".join(f["solo_sesame"]),
            solo_respaldo=" ".join(f["solo_respaldo"]),
            incompleto=int(f["incompleto"]),
            faltan_del_respaldo=int(f["faltan_del_respaldo"])).values()))
    for linea in (impacto or {}).get("lineas", []):
        w.writerow(list(dict(vacio, tipo="linea", **{
            k: "" if linea[k] is None else linea[k]
            for k in ("dni", "registro_id", "document_id", "fecha",
                      "obra_ide", "clase", "sentido")}).values()))
    for e in (impacto or {}).get("errores", []):
        w.writerow(list(dict(vacio, tipo="error", dni=e["dni"],
                             error=e["error"]).values()))


# ------------------------------------------------------------------ #
# Entrada/salida.
# ------------------------------------------------------------------ #
def _settings() -> Any:
    """Los settings de sv3, o None si el ``.env`` no esta (contraste
    sin base: basta con ``--base-url`` y el token por consola)."""
    try:
        from config.settings import Settings
        return Settings()
    except Exception:  # noqa: BLE001 - sin .env completo se sigue
        return None


def listar_calendarios(cliente: SesameHrClient) -> list[dict]:
    """Los calendarios de Sesame HR en la forma que consume
    ``contrastar_calendario`` (las puras de F-032 no cambian, R24)."""
    return [{"id": c.id, "nombre": c.nombre, "por_defecto": c.por_defecto,
             "festivos": [{"fecha": f.fecha, "nombre": f.nombre}
                          for f in c.festivos]}
            for c in cliente.calendarios_festivos()]


def _festivos_por_dni(adaptador: FestivosSesameHr, dnis: Iterable[str],
                      ano: int) -> dict[str, Any]:
    """R26: ``None`` (no encontrado: el respaldo), el mapa o el fallo."""
    out: dict[str, Any] = {}
    for dni in sorted(set(dnis)):
        try:
            lista = adaptador.festivos(dni, ano)
        except Exception as exc:  # noqa: BLE001 - R32: fila de error
            out[dni] = exc
            continue
        out[dni] = None if lista is None else del_ano(
            ((f.fecha, f.nombre) for f in lista), ano)
    return out


def _repositorio_solo_lectura(settings: Any) -> Any:
    """El repositorio de partes sobre un engine ``READ ONLY`` (R33)."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from infrastructure.database.sqlalchemy_parte_repository import (
        SqlAlchemyParteRepository,
    )

    engine = create_engine(settings.database_url).execution_options(
        postgresql_readonly=True)

    class _Fabrica:
        def create_session(self) -> Session:
            return Session(engine)

    return SqlAlchemyParteRepository(_Fabrica())


def _argumentos(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Contraste de festivos de Sesame con el respaldo "
                    "(solo lectura, F-032).")
    p.add_argument("--ano", type=int, required=True)
    p.add_argument("--base-url", help="https:// de la API de Sesame HR")
    p.add_argument("--calendario", help="JSON de respaldo de sv3")
    p.add_argument("--festivos-minimos", type=int)
    p.add_argument("--salida", help="carpeta del informe (por defecto logs/)")
    p.add_argument("--impacto", action="store_true",
                   help="cuenta las lineas de partes activos que cambian")
    return p.parse_args(argv)


def _minimo(args, settings) -> int:
    if args.festivos_minimos is not None:
        return args.festivos_minimos
    if settings is not None:
        return int(settings.sesame_festivos_minimos)
    try:
        return int(os.environ.get("SESAME_FESTIVOS_MINIMOS") or 1)
    except ValueError:
        return 1


def main(argv: list[str] | None = None, *, ahora: datetime | None = None,
         transport: httpx.BaseTransport | None = None,
         repositorio: Any = None,
         pedir_token: Callable[[str], str] = getpass.getpass) -> int:
    """``transport``, ``repositorio`` y ``pedir_token`` son para los tests
    (sin red, sin base y sin consola)."""
    args = _argumentos(argv)
    settings = _settings()
    base_url = (args.base_url
                or (settings and settings.sesame_base_url)
                or os.environ.get("SESAME_BASE_URL") or "").strip()
    if not base_url.startswith("https://"):
        print("Falta --base-url o SESAME_BASE_URL con una URL https:// "
              "de Sesame HR.", file=sys.stderr)
        return SALIDA_CONFIGURACION
    token = ((settings and settings.sesame_token)
             or os.environ.get("SESAME_TOKEN")
             or pedir_token("Token de Sesame HR: ") or "").strip()
    if not token:
        print("Falta el token de Sesame HR (SESAME_TOKEN o por consola).",
              file=sys.stderr)
        return SALIDA_CONFIGURACION
    if args.impacto and repositorio is None and settings is None:
        print("--impacto necesita el .env de sv3 (PG_*) para leer partes.",
              file=sys.stderr)
        return SALIDA_CONFIGURACION
    calendario = (args.calendario
                  or (settings and settings.calendario_laboral_path)
                  or "config/calendario_laboral.json")
    respaldo = JsonCalendarioLaboral(path=calendario)
    cliente = SesameHrClient(
        base_url=base_url, token=token,
        timeout_s=(settings.sesame_timeout_s if settings else 10.0),
        transport=transport)
    try:
        calendarios = listar_calendarios(cliente)
    except RuntimeError as exc:
        print(f"No se pudo listar los calendarios: {exc}", file=sys.stderr)
        return SALIDA_LISTADO
    minimo = _minimo(args, settings)
    filas = [contrastar_calendario(c, args.ano, respaldo, minimo=minimo)
             for c in calendarios]

    impacto = None
    if args.impacto:
        try:
            repo = repositorio or _repositorio_solo_lectura(settings)
            registros = repo.fetch_registros_para_recurso()
        except Exception as exc:  # noqa: BLE001 - R31: sin informe
            print(f"No se pudo leer partes: {type(exc).__name__}",
                  file=sys.stderr)
            return SALIDA_IMPACTO
        dnis = [tm.normalize_dni(r.get("empleado_dni")) for r in registros]
        impacto = clasificar_impacto(
            registros, _festivos_por_dni(FestivosSesameHr(cliente=cliente),
                                         [d for d in dnis if d], args.ano),
            respaldo, args.ano)

    ahora = ahora or datetime.now()
    carpeta = Path(args.salida) if args.salida else CARPETA_LOGS
    carpeta.mkdir(parents=True, exist_ok=True)
    base = f"contraste_festivos_{args.ano}_{ahora.strftime('%Y%m%d-%H%M')}"
    ruta_md, ruta_csv = carpeta / f"{base}.md", carpeta / f"{base}.csv"
    ruta_md.write_text(render_markdown(
        args.ano, filas, impacto, momento=ahora.strftime("%Y-%m-%d %H:%M")),
        encoding="utf-8-sig")
    buf = io.StringIO()
    escribir_csv(buf, filas, impacto)
    ruta_csv.write_text(buf.getvalue(), encoding="utf-8-sig")

    for f in filas:
        marcas = [m for m, si in (("FALTAN DEL RESPALDO",
                                   f["faltan_del_respaldo"]),
                                  ("INCOMPLETO", f["incompleto"])) if si]
        print(f"{f['nombre'] or f['id']}: {f['n_festivos']} festivos"
              + (f" · {' · '.join(marcas)}" if marcas else ""))
    if impacto is not None:
        print(f"lineas afectadas: {len(impacto['lineas'])} "
              f"{impacto['por_clase']}; dias mixtos: "
              f"{impacto['dias_mixtos']}; DNIs con error: "
              f"{len(impacto['errores'])}")
    print(f"Informe: {ruta_md}\nCSV: {ruta_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
