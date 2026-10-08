# medir_casado_recursos.py
"""F-036 · Medicion del impacto del casado contra recursos (SOLO LECTURA).

Antes de desplegar F-036 dice, con los datos de hoy:

  - por empresa, cuantos recursos persona (`res.cla = 1`) hay de alta, de
    ellos sin DNI, con DNI solo por su ficha y con `res.cif` distinto del
    DNI de la ficha (DA1), y cuantos `MO/` de alta NO son persona (los que
    el respaldo F-030 casaba y F-036 deja fuera) (R24) y, desde F-040 (R28),
    cuantos sin DNI tampoco tienen ficha (`sin_dni_sin_ficha`);
  - para las lineas activas no congeladas, que hara con su recurso la
    pasada del conciliador (`igual` / `cambia` / `pierde` / `gana`, R25) y
    que daria el casado nuevo con lo leido frente al guardado (`igual` /
    `otro_recurso` / `otra_persona` / `casado_nuevo` / `pierde_casado` y,
    desde F-040, `propone_sin_dni`; solo informativo: lo ingerido no se
    re-casa, DA2) (R26). Las congeladas se cuentan aparte. F-040 (R29): el
    alias se lee sin `recurso_ide` (antes del despliegue no existe).

Solo lee (R23): los maestros por `POST /api/sql/read` de sigrid-api (las
lecturas paginadas de siempre) y la base `partes` con SELECT dentro de una
transaccion `READ ONLY`, sin `SessionFactory` (que crea la base si falta).
El DNI leido de cada linea sale del JSON de extraccion guardado en el parte.
La salida no lleva nombres ni DNIs (R27): `logs/medicion_casado_<fecha>.md`
(resumen y tabla por empresa) y `.csv` (una fila por linea: ids, empresa y
las dos categorias), UTF-8 con BOM y `;`.

USO (desde services/partes-persistencia, con el .env de sv3):
  ../../.venv/Scripts/python.exe medir_casado_recursos.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Connection

from application.services import medicion_casado as mc
from application.services.empleado_matcher import EmpleadoMatcher
from application.services.parte_normalizer import ParteNormalizer
from application.services.recurso_conciliador import esta_congelado
from application.services.seleccion_sigrid import IndicePersonas
from config.settings import Settings
from infrastructure.database.orm_models import (
    EmpleadoAliasOrm,
    ParteDocumentOrm,
    ParteRegistroOrm,
)
from infrastructure.sigrid.sigrid_api_client import SigridApiClient

#: Carpeta de salida (ignorada por git), junto a este fichero.
CARPETA_LOGS = Path(__file__).resolve().parent / "logs"


def solo_lectura(conn: Connection) -> None:
    """Abre la transaccion en modo READ ONLY (PostgreSQL)."""
    if conn.dialect.name == "postgresql":
        conn.exec_driver_sql("SET TRANSACTION READ ONLY")


def _dnis_leidos(raw_json: str | None) -> dict[Any, str]:
    """DNI leido por numero de fila del parte y por nombre leido, a partir
    del JSON de extraccion guardado (el mismo normalizador de la ingesta)."""
    try:
        envelope = json.loads(raw_json or "{}")
        data = envelope.get("data") or {}
        parte = ParteNormalizer().normalize(data)
    except Exception:  # noqa: BLE001 - un JSON raro no para la medicion
        return {}
    out: dict[Any, str] = {}
    for reg in parte.registros:
        dni = reg.trabajador_dni_leido
        if not dni:
            continue
        if reg.empleado_line_no is not None:
            out.setdefault(("fila", reg.empleado_line_no), dni)
        out.setdefault(("nombre", reg.trabajador_nombre_leido), dni)
    return out


def leer_lineas(conn: Connection) -> list[mc.LineaMedida]:
    """Las lineas de los partes activos (las mismas que ve el conciliador)."""
    r, d = ParteRegistroOrm, ParteDocumentOrm
    filas = conn.execute(
        select(r.id, r.document_id, d.empresa, r.obra_ide, r.fecha_int,
               r.empleado_line_no, r.trabajador_nombre_leido, r.empleado_ide,
               r.empleado_dni, r.empleado_reside, r.empleado_match_method,
               r.recurso_ide, r.sigrid_estado, d.approved,
               d.raw_extraction_json)
        .join(d, r.document_id == d.id)
        .where(d.is_active.is_(True))
        .order_by(r.id)
    ).all()
    dnis_por_doc: dict[str, dict[Any, str]] = {}
    lineas = []
    for f in filas:
        if f.document_id not in dnis_por_doc:
            dnis_por_doc[f.document_id] = _dnis_leidos(f.raw_extraction_json)
        dnis = dnis_por_doc[f.document_id]
        dni = (dnis.get(("fila", f.empleado_line_no))
               or dnis.get(("nombre", f.trabajador_nombre_leido)))
        lineas.append(mc.LineaMedida(
            registro_id=f.id, document_id=f.document_id, empresa=f.empresa,
            obra_ide=f.obra_ide, fecha_int=f.fecha_int, dni_leido=dni,
            nombre_leido=f.trabajador_nombre_leido,
            empleado_ide=f.empleado_ide, empleado_dni=f.empleado_dni,
            empleado_reside=f.empleado_reside,
            empleado_match_method=f.empleado_match_method,
            recurso_ide=f.recurso_ide,
            congelada=esta_congelado(f.sigrid_estado, f.approved),
        ))
    return lineas


def leer_aliases(conn: Connection) -> dict[str, dict]:
    """`empleado_alias` como lo da `find_empleado_alias`, por nombre."""
    a = EmpleadoAliasOrm
    return {
        f.nombre_norm: {"ide": f.empleado_ide, "dni": f.empleado_dni}
        for f in conn.execute(
            select(a.nombre_norm, a.empleado_ide, a.empleado_dni)).all()
    }


def medir(
    conn: Connection, sigrid: Any, *, hoy: int, min_score: float
) -> tuple[list[dict], list[dict], dict[str, int]]:
    """Maestros de Sigrid + lineas y alias de `partes` -> el informe."""
    recursos = sigrid.fetch_recursos()
    indice = IndicePersonas(sigrid.fetch_empleados(), recursos,
                            sigrid.fetch_obras())
    solo_lectura(conn)
    lineas = leer_lineas(conn)
    aliases = leer_aliases(conn)
    conn.rollback()
    maestro = mc.medir_maestro(indice, recursos, hoy)
    filas = mc.medir_lineas(lineas, indice,
                            EmpleadoMatcher(min_score=min_score), aliases, hoy)
    return maestro, filas, mc.resumir(filas)


def escribir(
    carpeta: Path, sello: str, maestro: list[dict], filas: list[dict],
    resumen: dict[str, int], momento: str,
) -> tuple[Path, Path]:
    """El Markdown y el CSV del informe, UTF-8 con BOM."""
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta_md = carpeta / f"medicion_casado_{sello}.md"
    ruta_csv = carpeta / f"medicion_casado_{sello}.csv"
    ruta_md.write_text(mc.informe_markdown(maestro, resumen, momento),
                       encoding="utf-8-sig")
    ruta_csv.write_text(mc.csv_lineas(filas), encoding="utf-8-sig")
    return ruta_md, ruta_csv


def main() -> int:
    """Sin opciones: siempre todo y siempre solo lectura."""
    settings = Settings()
    if not settings.sigrid_credentials_present:
        print("Faltan SIGRID_API_* en el .env de sv3.", file=sys.stderr)
        return 2
    sigrid = SigridApiClient(
        base_url=settings.sigrid_api_base_url,        # type: ignore[arg-type]
        function_key=settings.sigrid_api_function_key,  # type: ignore[arg-type]
        database=settings.sigrid_api_database,        # type: ignore[arg-type]
        timeout_s=settings.sigrid_api_timeout_s,
        max_rows=settings.sigrid_api_max_rows,
    )
    ahora = datetime.now(timezone.utc).astimezone()   # hora local
    engine = create_engine(settings.database_url)
    try:
        with engine.connect() as conn:
            maestro, filas, resumen = medir(
                conn, sigrid, hoy=int(ahora.strftime("%Y%m%d")),
                min_score=settings.empleado_min_score)
    finally:
        engine.dispose()
    ruta_md, ruta_csv = escribir(
        CARPETA_LOGS, ahora.strftime("%Y%m%d-%H%M"), maestro, filas, resumen,
        ahora.strftime("%Y-%m-%d %H:%M"))
    for clave, valor in resumen.items():
        print(f"{clave}: {valor}")
    print(f"Informe: {ruta_md}\nCSV: {ruta_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
