# infrastructure/sigrid/sigrid_write_client.py
"""Adaptador de Sigrid (lectura + ESCRITURA) via sigrid-api.

Encapsula el modelo de datos del parte de trabajo, confirmado contra datos
reales (25/07/2026):
  con    : emp, tip=35, est=1, cod='PT<aa>/<nnnnn>', res, fec=ultimo dia
           del mes del parte.
  hmo    : MISMO ide que con; cenide (centro de la obra), obride, ano, mes,
           reside=0 (es parte de obra, no de recurso).
  hmores : hmoide, reside, cenide, obride, paride, pos (de 64 en 64), fec
           (dia real), horide, can (=horas, puede ser negativa), pre, tot,
           ano, mes, fac=0, ortide=0 (NOT NULL sin default), caaide=0,
           tex, synckey (nuestra clave de idempotencia).
"""
from __future__ import annotations

import calendar
import logging
from typing import Any, Iterable

import httpx

from domain.models.registro_models import (
    HoraRecurso, LineaSigrid, ObraEntrada, ParteDestino,
)

logger = logging.getLogger(__name__)

PREFIJO_SYNCKEY = "partes:"


def synckey_de(registro_id: int) -> str:
    return f"{PREFIJO_SYNCKEY}{int(registro_id)}"


class SigridWriteClient:
    def __init__(
        self,
        *,
        base_url: str,
        function_key: str,
        database: str,
        empresa: int = 1,
        timeout_s: float = 60.0,
        max_statements: int = 15,
        tip_parte: int = 35,
        est_parte: int = 1,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._headers = {"x-functions-key": function_key,
                         "Content-Type": "application/json"}
        self._db = database
        self._empresa = int(empresa)
        self._timeout = float(timeout_s)
        self._max_st = int(max_statements)
        self._tip = int(tip_parte)
        self._est = int(est_parte)

    # ----------------------------- HTTP ----------------------------- #

    def _read(self, sql: str, params: list) -> list[dict]:
        r = httpx.post(f"{self._base}/api/sql/read", headers=self._headers,
                       timeout=self._timeout + 30, json={
                           "database": self._db, "sql": sql,
                           "parameters": params,
                           "timeout_seconds": int(self._timeout),
                           "max_rows": 1000})
        if r.status_code >= 400:
            raise RuntimeError(f"sigrid-api read HTTP {r.status_code}: "
                               f"{r.text[:400]}")
        body = r.json()
        if not body.get("ok"):
            raise RuntimeError(f"sigrid-api read ok=false: {str(body)[:400]}")
        cols = [c.lower() for c in body["columns"]]
        return [dict(zip(cols, row)) for row in body["rows"]]

    def escribir(self, statements: list[dict]) -> int:
        """Escribe por lotes (tope de sentencias de sigrid-api). Cada lote es
        una transaccion; devuelve el total de filas afectadas."""
        total = 0
        for i in range(0, len(statements), self._max_st):
            lote = statements[i:i + self._max_st]
            for st in lote:
                logger.info("[sigrid-write] %s | %s",
                            " ".join(st["sql"].split())[:150],
                            st["parameters"])
            r = httpx.post(f"{self._base}/api/sql/write", headers=self._headers,
                           timeout=self._timeout + 60,
                           json={"database": self._db, "statements": lote})
            if r.status_code >= 400:
                raise RuntimeError(f"sigrid-api write HTTP {r.status_code}: "
                                   f"{r.text[:500]}")
            body = r.json()
            if not body.get("ok") or not body.get("committed"):
                raise RuntimeError(f"escritura no confirmada: {str(body)[:400]}")
            total += int(body.get("total_affected_rows") or 0)
        return total

    # ----------------------------- lecturas ----------------------------- #

    def obra_por_codigo(self, cod: str) -> ObraEntrada | None:
        filas = self._read(
            "SELECT obr.ide AS ide, con.cod AS cod, con.res AS res, "
            "obr.cenide AS cenide FROM obr JOIN con ON con.ide = obr.ide "
            "WHERE con.cod = ?", [cod])
        if not filas:
            return None
        f = filas[0]
        o = ObraEntrada(ide=int(f["ide"]), codigo=f["cod"], nombre=f["res"])
        setattr(o, "cenide", int(f["cenide"] or 0))
        return o

    def obra_por_ide(self, ide: int) -> ObraEntrada | None:
        filas = self._read(
            "SELECT obr.ide AS ide, con.cod AS cod, con.res AS res, "
            "obr.cenide AS cenide FROM obr JOIN con ON con.ide = obr.ide "
            "WHERE obr.ide = ?", [int(ide)])
        if not filas:
            return None
        f = filas[0]
        o = ObraEntrada(ide=int(f["ide"]), codigo=f["cod"], nombre=f["res"])
        setattr(o, "cenide", int(f["cenide"] or 0))
        return o

    def resides_por_dni(self, dnis: Iterable[str]) -> dict[str, int]:
        """DNI normalizado -> res.ide del recurso del empleado.

        Red de seguridad para lineas creadas sin recurso casado (p. ej.
        creacion manual antigua): mismo doble camino que la exclusion de
        extras (emp.dni via res.conide, y res.cif). Si un DNI tiene varios
        recursos se toma el de ide mas alto (el mas reciente)."""
        import re as _re
        norm = {_re.sub(r"[^0-9A-Za-z]", "", d or "").upper()
                for d in dnis if d}
        norm.discard("")
        if not norm:
            return {}
        ks = sorted(norm)
        marcas = ",".join("?" for _ in ks)
        sql = (
            "SELECT dnin AS dni, MAX(reside) AS reside FROM ("
            "  SELECT REPLACE(REPLACE(UPPER(ISNULL(emp.dni,'')),'-',''),' ','')"
            "         AS dnin, res.ide AS reside"
            "  FROM res JOIN emp ON emp.ide = res.conide"
            f"  WHERE REPLACE(REPLACE(UPPER(ISNULL(emp.dni,'')),'-',''),' ','')"
            f"        IN ({marcas})"
            "  UNION ALL"
            "  SELECT REPLACE(REPLACE(UPPER(ISNULL(res.cif,'')),'-',''),' ','')"
            "         AS dnin, res.ide AS reside"
            "  FROM res"
            f"  WHERE REPLACE(REPLACE(UPPER(ISNULL(res.cif,'')),'-',''),' ','')"
            f"        IN ({marcas})"
            ") q GROUP BY dnin"
        )
        filas = self._read(sql, ks + ks)
        out: dict[str, int] = {}
        for f in filas:
            d = (f.get("dni") or "").strip()
            r = f.get("reside")
            if d and r:
                out[d] = int(r)
        logger.info("[sigrid-write] resides_por_dni: %s/%s resueltos",
                    len(out), len(ks))
        return out

    def horas_de_recursos(
        self, resides: Iterable[int]
    ) -> dict[int, list[HoraRecurso]]:
        ides = sorted({int(i) for i in resides if i})
        if not ides:
            return {}
        marcas = ",".join("?" for _ in ides)
        filas = self._read(
            "SELECT reshor.reside AS reside, reshor.horide AS horide, "
            "auxhor.cod AS cod, auxhor.res AS res, reshor.pre AS pre "
            "FROM reshor JOIN auxhor ON auxhor.ide = reshor.horide "
            f"WHERE reshor.reside IN ({marcas}) "
            "ORDER BY reshor.reside, auxhor.cod", ides)
        out: dict[int, list[HoraRecurso]] = {}
        for f in filas:
            out.setdefault(int(f["reside"]), []).append(HoraRecurso(
                horide=int(f["horide"]), cod=(f["cod"] or "").strip(),
                res=f["res"], pre=float(f["pre"] or 0.0)))
        return out

    def partes_existentes(
        self, obra_ide: int, periodos: Iterable[tuple[int, int]]
    ) -> dict[tuple[int, int], ParteDestino]:
        """Parte (hmo) de obra+mes SIN recurso (el parte de obra)."""
        out: dict[tuple[int, int], ParteDestino] = {}
        for ano, mes in sorted(set(periodos)):
            filas = self._read(
                "SELECT hmo.ide AS ide, con.cod AS cod FROM hmo "
                "JOIN con ON con.ide = hmo.ide "
                "WHERE hmo.obride = ? AND hmo.ano = ? AND hmo.mes = ? "
                "AND ISNULL(hmo.reside, 0) = 0 AND con.tip = ? "
                "ORDER BY hmo.ide DESC",
                [int(obra_ide), int(ano), int(mes), self._tip])
            if filas:
                out[(ano, mes)] = ParteDestino(
                    ano=ano, mes=mes, existe=True, ide=int(filas[0]["ide"]),
                    cod=filas[0]["cod"])
            else:
                out[(ano, mes)] = ParteDestino(ano=ano, mes=mes, existe=False)
        return out

    def siguiente_cod_pt(self, ano: int) -> str:
        yy = str(int(ano))[-2:]
        filas = self._read("SELECT MAX(cod) AS maxcod FROM con WHERE cod LIKE ?",
                           [f"PT{yy}/%"])
        maxcod = (filas[0]["maxcod"] or "") if filas else ""
        try:
            n = int(str(maxcod).split("/")[1]) + 1
        except (IndexError, ValueError):
            n = 1
        return f"PT{yy}/{n:05d}"

    def max_pos(self, hmoide: int) -> int:
        filas = self._read("SELECT ISNULL(MAX(pos),0) AS m FROM hmores "
                           "WHERE hmoide = ?", [int(hmoide)])
        return int((filas[0]["m"] if filas else 0) or 0)

    def lineas_existentes(
        self, hmoide: int, resides: Iterable[int], fechas: Iterable[int]
    ) -> list[LineaSigrid]:
        res = sorted({int(i) for i in resides if i})
        fec = sorted({int(f) for f in fechas if f})
        if not res or not fec:
            return []
        m_r = ",".join("?" for _ in res)
        m_f = ",".join("?" for _ in fec)
        filas = self._read(
            "SELECT hmores.ide AS ide, hmores.reside AS reside, "
            "hmores.fec AS fec, hmores.horide AS horide, "
            "auxhor.cod AS hora, hmores.can AS can, "
            "hmores.tot AS tot, hmores.synckey AS synckey FROM hmores "
            "LEFT JOIN auxhor ON auxhor.ide = hmores.horide "
            f"WHERE hmores.hmoide = ? AND hmores.reside IN ({m_r}) "
            f"AND hmores.fec IN ({m_f}) ORDER BY hmores.pos",
            [int(hmoide)] + res + fec)
        out: list[LineaSigrid] = []
        for f in filas:
            sk = (f["synckey"] or "").strip() or None
            out.append(LineaSigrid(
                ide=int(f["ide"]), reside=int(f["reside"] or 0),
                fecha_int=int(f["fec"] or 0),
                horide=int(f["horide"] or 0) or None,
                hora_codigo=f["hora"], can=f["can"], tot=f["tot"], synckey=sk,
                nuestra=bool(sk and sk.startswith(PREFIJO_SYNCKEY))))
        return out

    def lineas_por_synckey(self, claves: Iterable[str]) -> dict[str, LineaSigrid]:
        ks = sorted({k for k in claves if k})
        if not ks:
            return {}
        out: dict[str, LineaSigrid] = {}
        # Lotes por si son muchas claves.
        for i in range(0, len(ks), 200):
            trozo = ks[i:i + 200]
            marcas = ",".join("?" for _ in trozo)
            filas = self._read(
                "SELECT hmores.ide AS ide, hmores.hmoide AS hmoide, "
                "hmores.reside AS reside, hmores.fec AS fec, "
                "hmores.horide AS horide, "
                "auxhor.cod AS hora, hmores.can AS can, hmores.tot AS tot, "
                "hmores.synckey AS synckey FROM hmores "
                "LEFT JOIN auxhor ON auxhor.ide = hmores.horide "
                f"WHERE hmores.synckey IN ({marcas})", trozo)
            for f in filas:
                sk = (f["synckey"] or "").strip()
                ls = LineaSigrid(
                    ide=int(f["ide"]), reside=int(f["reside"] or 0),
                    fecha_int=int(f["fec"] or 0),
                    horide=int(f["horide"] or 0) or None,
                    hora_codigo=f["hora"], can=f["can"], tot=f["tot"],
                    synckey=sk, nuestra=True)
                setattr(ls, "hmoide", int(f["hmoide"] or 0))
                out[sk] = ls
        return out

    # -------------------------- sentencias -------------------------- #

    def stmts_crear_parte(
        self, *, obra: ObraEntrada, ano: int, mes: int, cod: str, desc: str
    ) -> list[dict]:
        """Cabecera (con) + extension (hmo) del parte de obra/mes."""
        ultimo = calendar.monthrange(int(ano), int(mes))[1]
        fec = int(f"{int(ano)}{int(mes):02d}{ultimo:02d}")
        cenide = int(getattr(obra, "cenide", 0) or 0)
        return [
            {"sql": ("INSERT INTO con (ide, emp, tip, est, cod, res, fec) "
                     "SELECT ISNULL(MAX(ide),0)+1, ?, ?, ?, ?, ?, ? "
                     "FROM con WITH (UPDLOCK, HOLDLOCK)"),
             "parameters": [self._empresa, self._tip, self._est,
                            cod, desc[:128], fec]},
            {"sql": ("INSERT INTO hmo (ide, cenide, obride, ano, mes, reside, "
                     "cenmul) SELECT ide, ?, ?, ?, ?, 0, 0 FROM con "
                     "WHERE cod = ? AND tip = ?"),
             "parameters": [cenide, int(obra.ide), int(ano), int(mes),
                            cod, self._tip]},
        ]

    def stmt_insert_linea(
        self, *, hmoide: int, obra: ObraEntrada, reside: int, pos: int,
        fecha_int: int, horide: int, can: float, pre: float, paride: int,
        ano: int, mes: int, synckey: str, tex: str | None,
    ) -> dict:
        cenide = int(getattr(obra, "cenide", 0) or 0)
        return {"sql": (
            "INSERT INTO hmores (ide, hmoide, reside, cenide, obride, paride, "
            "pos, fec, horide, can, pre, tot, ano, mes, fac, ortide, caaide, "
            "tex, synckey) SELECT ISNULL(MAX(ide),0)+1, ?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ? "
            "FROM hmores WITH (UPDLOCK, HOLDLOCK)"),
            "parameters": [int(hmoide), int(reside), cenide, int(obra.ide),
                           int(paride or 0), int(pos), int(fecha_int),
                           int(horide), float(can), float(pre),
                           round(float(can) * float(pre), 2), int(ano),
                           int(mes), (tex or ""), synckey]}

    @staticmethod
    def stmt_borrar_linea(ide: int) -> dict:
        return {"sql": "DELETE FROM hmores WHERE ide = ?",
                "parameters": [int(ide)]}
