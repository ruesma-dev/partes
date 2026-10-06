# comprobar_asiento_analitico.py
"""F-031 · Comprobacion del asiento analitico de los partes (SOLO LECTURA).

Sigrid genera el asiento analitico de un parte al «Contabilizar» (estado
Imputado): Debe = suma de `hmores.tot` por `hmores.caaide`. Esta
herramienta lista los partes de una obra y mes (el original y los
complementarios, cada uno con su estado) y, para cada Imputado, busca su
asiento (tipo 32, misma empresa, resumen y fecha) y compara el Debe por
cuenta con las lineas por cuenta (tolerancia 0,01 EUR): `cuadra`,
`descuadre`, `sin_asiento` o `varios_asientos`.

Solo lee, por `POST /api/sql/read` de sigrid-api (con `truncated`, falla).
La salida no lleva nombres, DNIs ni contrapartidas por persona: cuentas del
centro de la obra y el TOTAL del Haber.

USO (desde services/partes-transfer, con su .env):
  ../../.venv/Scripts/python.exe comprobar_asiento_analitico.py \\
      --empresa 1 --obra 0696 --ano 2026 --mes 1
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Callable

from application.services.estado_parte import nombre_estado
from infrastructure.sigrid.sigrid_write_client import (
    PREFIJO_SYNCKEY,
    SigridWriteClient,
)

CUADRA = "cuadra"
DESCUADRE = "descuadre"
SIN_ASIENTO = "sin_asiento"
VARIOS_ASIENTOS = "varios_asientos"

#: `con.tip` de un asiento analitico (`asa`).
TIP_ASIENTO_ANALITICO = 32
#: Diferencia maxima, en euros, para dar una cuenta por cuadrada.
TOLERANCIA = 0.01

Lector = Callable[[str, list], list[dict]]


def _diferencias(lineas: dict[str, float],
                 debe: dict[str, float]) -> dict[str, float]:
    """Cuentas cuya diferencia lineas - debe supera la tolerancia."""
    out: dict[str, float] = {}
    for cuenta in sorted(set(lineas) | set(debe)):
        dif = round(lineas.get(cuenta, 0.0) - debe.get(cuenta, 0.0), 6)
        if abs(dif) > TOLERANCIA:
            out[cuenta] = dif
    return out


def comparar(lineas_por_cuenta: dict[str, float],
             debe_por_cuenta: dict[str, float], n_asientos: int) -> str:
    """R36 (pura): veredicto de un parte Imputado frente a su asiento."""
    if n_asientos == 0:
        return SIN_ASIENTO
    if n_asientos > 1:
        return VARIOS_ASIENTOS
    if _diferencias(lineas_por_cuenta, debe_por_cuenta):
        return DESCUADRE
    return CUADRA


def comprobar(leer: Lector, *, empresa: int, obra: str, ano: int, mes: int,
              tip_parte: int = 35, est_registro: int = 1,
              est_cerrado: int = 3, est_imputado: int = 10) -> list[str]:
    """R35-R37: las lineas de texto del informe de una obra y mes."""
    obras = leer("SELECT obr.ide AS ide, con.cod AS cod FROM obr "
                 "JOIN con ON con.ide = obr.ide "
                 "WHERE con.cod = ? AND con.emp = ?", [obra, int(empresa)])
    if not obras:
        return [f"La obra {obra} no existe en la empresa {empresa}"]
    partes = leer(
        "SELECT hmo.ide AS ide, con.cod AS cod, con.est AS est, "
        "con.res AS res, con.fec AS fec FROM hmo "
        "JOIN con ON con.ide = hmo.ide "
        "WHERE hmo.obride = ? AND hmo.ano = ? AND hmo.mes = ? "
        "AND ISNULL(hmo.reside, 0) = 0 AND con.tip = ? AND con.emp = ? "
        "ORDER BY hmo.ide DESC",
        [int(obras[0]["ide"]), int(ano), int(mes), int(tip_parte),
         int(empresa)])
    salida = [f"Obra {obra} · empresa {empresa} · {int(mes):02d}/{ano}: "
              f"{len(partes)} parte(s)"]
    if not partes:
        return salida
    ides = [int(p["ide"]) for p in partes]
    marcas = ",".join("?" for _ in ides)
    filas = leer(
        "SELECT h.hmoide AS hmoide, c.cod AS cuenta, COUNT(*) AS n, "
        "SUM(CASE WHEN h.synckey LIKE ? THEN 1 ELSE 0 END) AS nuestras, "
        "SUM(h.tot) AS importe FROM hmores h "
        "LEFT JOIN con c ON c.ide = h.caaide AND ISNULL(h.caaide, 0) <> 0 "
        f"WHERE h.hmoide IN ({marcas}) GROUP BY h.hmoide, c.cod",
        [PREFIJO_SYNCKEY + "%"] + ides)

    def estado(est) -> str:
        if est == est_registro:
            return "En registro"
        return nombre_estado(est, est_cerrado=est_cerrado,
                             est_imputado=est_imputado)

    for p in partes:
        mias = [f for f in filas if int(f["hmoide"]) == int(p["ide"])]
        por_cuenta = {f["cuenta"].strip(): float(f["importe"] or 0.0)
                      for f in mias if f["cuenta"]}
        salida.append(
            f"{p['cod']} · {estado(p['est'])} · "
            f"{sum(int(f['n'] or 0) for f in mias)} linea(s) "
            f"({sum(int(f['nuestras'] or 0) for f in mias)} nuestras) · "
            f"importe con cuenta {sum(por_cuenta.values()):.2f}")
        if p["est"] == est_imputado:
            salida.extend(_asiento(leer, empresa, p, por_cuenta))
    return salida


def _asiento(leer: Lector, empresa: int, p: dict,
             por_cuenta: dict[str, float]) -> list[str]:
    """R36: el asiento del parte Imputado y su veredicto."""
    asientos = leer("SELECT con.ide AS ide, con.cod AS cod FROM con "
                    "WHERE con.emp = ? AND con.res = ? AND con.fec = ? "
                    "AND con.tip = ?",
                    [int(empresa), p["res"], p["fec"],
                     TIP_ASIENTO_ANALITICO])
    if len(asientos) != 1:
        veredicto = comparar(por_cuenta, {}, len(asientos))
        if veredicto == SIN_ASIENTO:
            return [f"  {SIN_ASIENTO} (ningun asiento tipo "
                    f"{TIP_ASIENTO_ANALITICO} con ese resumen y fecha)"]
        return [f"  {VARIOS_ASIENTOS}: "
                + ", ".join(str(a["cod"]) for a in asientos)]
    asiento = asientos[0]
    apuntes = leer("SELECT c.cod AS cuenta, SUM(a.deb) AS deb, "
                   "SUM(a.hab) AS hab FROM apa a "
                   "LEFT JOIN con c ON c.ide = a.cueide "
                   "WHERE a.conide = ? GROUP BY c.cod", [int(asiento["ide"])])
    debe = {(f["cuenta"] or "").strip(): float(f["deb"] or 0.0)
            for f in apuntes if float(f["deb"] or 0.0)}
    haber = sum(float(f["hab"] or 0.0) for f in apuntes)
    veredicto = comparar(por_cuenta, debe, 1)
    salida = [f"  asiento {asiento['cod']}: {veredicto} (Debe "
              f"{sum(debe.values()):.2f} en {len(debe)} cuenta(s); Haber "
              f"total {haber:.2f})"]
    for cuenta, dif in _diferencias(por_cuenta, debe).items():
        salida.append(f"    {cuenta}: lineas {por_cuenta.get(cuenta, 0.0):.2f}"
                      f" · debe {debe.get(cuenta, 0.0):.2f} · diferencia "
                      f"{dif:.2f}")
    return salida


def main(argv: list[str] | None = None, settings=None) -> int:
    ap = argparse.ArgumentParser(
        description="Comprueba el asiento analitico de los partes de una "
                    "obra y mes (solo lectura).")
    ap.add_argument("--empresa", type=int, required=True)
    ap.add_argument("--obra", required=True)
    ap.add_argument("--ano", type=int, required=True)
    ap.add_argument("--mes", type=int, required=True)
    args = ap.parse_args(argv)
    if settings is None:
        from config.settings import Settings
        settings = Settings()
    cliente = SigridWriteClient(
        base_url=settings.sigrid_api_base_url,
        function_key=settings.sigrid_api_function_key,
        database=settings.sigrid_api_database,
        timeout_s=settings.sigrid_api_timeout_s)
    for linea in comprobar(
            cliente._read, empresa=args.empresa, obra=args.obra,
            ano=args.ano, mes=args.mes,
            tip_parte=settings.tip_parte_trabajo,
            est_registro=settings.est_parte_activo,
            est_cerrado=settings.est_parte_cerrado,
            est_imputado=settings.est_parte_imputado):
        print(linea)
    return 0


if __name__ == "__main__":
    sys.exit(main())
