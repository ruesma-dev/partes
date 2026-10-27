# limpiar_partes_vacios.py
"""F-061 · Limpieza de los partes ACTIVOS que ya están vacíos (DA4).

Antes de F-061, borrar la última línea de un parte lo dejaba activo y sin
líneas, y su sha256 bloqueaba la reingesta del mismo PDF en sv3. Este
script aplica a los que ya existen la misma regla que el portal aplica
desde F-061 («Lo mismo que la regla», decisión del humano 2026-10-26):

  - el parte vacío SIN filas se borra físicamente (`borrar`);
  - el parte vacío CON filas (todas en la papelera) se retira (`retirar`):
    inactivo, sin `deleted_at_utc` y `deleted_by` =
    `sin-lineas · F-061-limpieza`.

Excluye, y lista con su motivo (R16): el aprobado, el que tiene alguna
línea en un estado que vive fuera (`registrado`, `dedicacion`) o en vuelo
(`encolado`) y el que tiene alguna línea de los partes de Sigrid
protegidos (lista cerrada en `application/services/parte_vacio.py`).

Sin argumentos SOLO LEE (R14), en una transacción `READ ONLY`, y deja en
`logs/` un Markdown y un CSV (UTF-8 con BOM y `;`) sin nombres ni DNIs:
`limpieza_partes_vacios_<AAAAMMDD-HHMM>.md` y `.csv`.

Con `--ejecutar --esperados N` (R17): si los candidatos no excluidos no
son exactamente N, aborta sin escribir (código 2); si lo son, en una
transacción y recomprobando cada uno bajo bloqueo, aplica la regla.

La conexión se monta aquí con `settings.database_url` y nada más (R18): la
fábrica de sesiones del servicio crea la base si falta y entra en la de
administración del servidor COMPARTIDO, y esto no debe tocarlo. Ningún
secreto en el fichero: la URL sale del `.env` de sv4.

USO (desde services/partes-front, con el .env de sv4):
  ../../.venv/Scripts/python.exe limpiar_partes_vacios.py
  ../../.venv/Scripts/python.exe limpiar_partes_vacios.py --ejecutar --esperados <N>
"""
from __future__ import annotations

import argparse
import csv
import io
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from application.services.parte_vacio import (
    categoria_vacio,
    motivo_exclusion_limpieza,
)
from config.settings import Settings
from infrastructure.database.parte_repository import ParteReviewRepository

#: Carpeta de salida (ignorada por git), junto a este fichero.
CARPETA_LOGS = Path(__file__).resolve().parent / "logs"

#: Actor que firma la marca de los partes retirados por este script.
ACTOR_LIMPIEZA = "F-061-limpieza"

COLUMNAS = ("document_id", "fecha", "obra_codigo", "created_at_utc",
            "categoria", "accion", "motivo_exclusion")

#: Código de salida cuando los candidatos no son los esperados.
SALIDA_NO_COINCIDE = 2


def solo_lectura(conn) -> None:
    """Abre la transacción en modo READ ONLY (PostgreSQL)."""
    if conn.dialect.name == "postgresql":
        conn.exec_driver_sql("SET TRANSACTION READ ONLY")


class FabricaSesiones:
    """Lo mínimo que el repositorio necesita (`create_session`)."""

    def __init__(self, database_url: str, *, lectura: bool) -> None:
        self.engine = create_engine(database_url, future=True,
                                    pool_pre_ping=True)
        if lectura:
            event.listen(self.engine, "begin", solo_lectura)
        self._sessionmaker = sessionmaker(bind=self.engine,
                                          expire_on_commit=False, future=True)

    def create_session(self):
        return self._sessionmaker()


def informe(repo: ParteReviewRepository) -> list[dict]:
    """Una fila por parte activo vacío, con categoría, acción y motivo."""
    filas = []
    for p in repo.partes_vacios_activos():
        motivo = motivo_exclusion_limpieza(
            aprobado=p["approved"], estados=p["estados"],
            partes_sigrid=p["partes_sigrid"])
        filas.append({
            "document_id": p["document_id"],
            "fecha": p["fecha"] or "",
            "obra_codigo": p["obra_codigo"] or "",
            "created_at_utc": p["created_at_utc"] or "",
            "categoria": categoria_vacio(
                filas=p["filas"], manual=p["manual"],
                empleados_leidos=p["empleados_leidos"]),
            "accion": "retirar" if p["filas"] else "borrar",
            "motivo_exclusion": motivo or "",
        })
    filas.sort(key=lambda f: (f["fecha"], f["document_id"]))
    return filas


def candidatos(filas: list[dict]) -> list[str]:
    return [f["document_id"] for f in filas if not f["motivo_exclusion"]]


def _csv(filas: list[dict]) -> str:
    salida = io.StringIO()
    escritor = csv.writer(salida, delimiter=";", lineterminator="\r\n")
    escritor.writerow(COLUMNAS)
    for f in filas:
        escritor.writerow([f[c] for c in COLUMNAS])
    return salida.getvalue()


def _markdown(filas: list[dict], cuando: str) -> str:
    cand = candidatos(filas)
    por_cat = Counter(f["categoria"] for f in filas
                      if not f["motivo_exclusion"])
    por_accion = Counter(f["accion"] for f in filas
                         if not f["motivo_exclusion"])
    excl = Counter(f["motivo_exclusion"] for f in filas
                   if f["motivo_exclusion"])
    lineas = [
        "# F-061 · Partes activos vacíos", "",
        f"Generado: {cuando} (solo lectura).", "",
        f"- Partes activos vacíos: **{len(filas)}**",
        f"- Candidatos no excluidos: **{len(cand)}**",
        f"- Excluidos: **{sum(excl.values())}**", "",
        "| Categoría (candidatos) | Partes |", "|---|---|",
        *[f"| `{k}` | {v} |" for k, v in sorted(por_cat.items())], "",
        "| Acción prevista (candidatos) | Partes |", "|---|---|",
        *[f"| `{k}` | {v} |" for k, v in sorted(por_accion.items())], "",
        "| Motivo de exclusión | Partes |", "|---|---|",
        *[f"| `{k}` | {v} |" for k, v in sorted(excl.items())], "",
        "| document_id | fecha | obra | categoría | acción | exclusión |",
        "|---|---|---|---|---|---|",
        *[(f"| `{f['document_id']}` | {f['fecha']} | {f['obra_codigo']} | "
           f"{f['categoria']} | {f['accion']} | {f['motivo_exclusion']} |")
          for f in filas], "",
        ("Para aplicar: `limpiar_partes_vacios.py --ejecutar --esperados "
         f"{len(cand)}`"), "",
    ]
    return "\n".join(lineas)


def escribir_informe(filas: list[dict], carpeta: Path,
                     ahora: datetime) -> tuple[Path, Path]:
    carpeta.mkdir(parents=True, exist_ok=True)
    sello = ahora.strftime("%Y%m%d-%H%M")
    md = carpeta / f"limpieza_partes_vacios_{sello}.md"
    cv = carpeta / f"limpieza_partes_vacios_{sello}.csv"
    md.write_text(_markdown(filas, ahora.isoformat(timespec="seconds")),
                  encoding="utf-8")
    cv.write_bytes(_csv(filas).encode("utf-8-sig"))
    return md, cv


def _argumentos(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="F-061: informe (por defecto) o limpieza de los partes "
                    "activos vacíos.")
    parser.add_argument("--ejecutar", action="store_true",
                        help="aplica la regla (exige --esperados)")
    parser.add_argument("--esperados", type=int,
                        help="nº de candidatos no excluidos del informe")
    args = parser.parse_args(argv)
    if args.ejecutar and args.esperados is None:
        parser.error("--ejecutar exige --esperados N (el del informe)")
    return args


def main(argv: list[str] | None = None, *, fabrica=None,
         carpeta: Path = CARPETA_LOGS) -> int:
    args = _argumentos(argv)
    if fabrica is None:
        url = Settings().database_url
        lectura = FabricaSesiones(url, lectura=True)
        escritura = FabricaSesiones(url, lectura=False) if args.ejecutar \
            else None
    else:
        lectura = escritura = fabrica

    filas = informe(ParteReviewRepository(lectura))
    md, cv = escribir_informe(filas, carpeta, datetime.now(timezone.utc))
    cand = candidatos(filas)
    print(f"Partes activos vacíos: {len(filas)}; candidatos no excluidos: "
          f"{len(cand)}.")
    print(f"Informe: {md}")
    print(f"CSV:     {cv}")
    if not args.ejecutar:
        return 0

    if len(cand) != args.esperados:
        print(f"ABORTADO: hay {len(cand)} candidatos y se esperaban "
              f"{args.esperados}. No se ha escrito nada.")
        return SALIDA_NO_COINCIDE
    res = ParteReviewRepository(escritura).limpiar_vacios(
        cand, by=ACTOR_LIMPIEZA)
    print(f"Borrados: {len(res['borrados'])}; retirados: "
          f"{len(res['retirados'])}; saltados al recomprobar: "
          f"{len(res['saltados'])}.")
    for did in res["saltados"]:
        print(f"  saltado: {did}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
