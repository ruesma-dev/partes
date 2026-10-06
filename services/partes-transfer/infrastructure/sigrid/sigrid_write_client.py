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
           ano, mes, fac=0, ortide=0 (NOT NULL sin default), caaide,
           tex, synckey (nuestra clave de idempotencia).

F-021: `hmores.caaide` es la cuenta analitica de la linea: la cuenta del
centro de la obra con la subcuenta de la ficha del recurso (regla en
`application/services/cuenta_analitica.py`), o 0 si no hay. Va como
parametro; `horas_de_recursos` trae la plantilla (`reshor.caaide`) y
`cuentas_de_centro` las cuentas candidatas del centro.

F-031: `partes_del_periodo` lee TODOS los partes de obra y mes con su
estado (`con.est`) para que el pipeline no escriba en uno cerrado, y
`partidas_de_lineas` la cuenta de cada partida (respaldo de la del
recurso). Solo lecturas; las sentencias de escritura no cambian.

F-023: la empresa de la cabecera (``con.emp``) es la de la OBRA destino,
no una variable de entorno; el correlativo ``PT<AA>/NNNNN`` es por empresa
y el ``INSERT INTO hmo`` localiza su cabecera por codigo, tipo y empresa.
Todas las lecturas son agregados o lotes acotados (sin paginar) y una
respuesta con ``truncated: true`` es una excepcion.
"""
from __future__ import annotations

import calendar
import logging
import re
from typing import Any, Iterable

import httpx

from application.services.cuenta_analitica import indexar_cuentas
from domain.models.registro_models import (
    HoraRecurso, LineaSigrid, ObraEntrada, ParteDestino, ParteSigrid,
    PartidaCuenta, RecursoSigrid,
)

logger = logging.getLogger(__name__)

PREFIJO_SYNCKEY = "partes:"

#: Recursos por lectura en `datos_recursos` (lote acotado, F-023).
LOTE_RECURSOS = 500

#: `ide` por lectura en la comprobacion de lineas (F-024, R7).
LOTE_COMPROBACION = 200

# DNI normalizado en SQL Server: mayusculas y sin guiones ni espacios.
_DNI_SQL = "REPLACE(REPLACE(UPPER(ISNULL({campo},'')),'-',''),' ','')"


def synckey_de(registro_id: int) -> str:
    return f"{PREFIJO_SYNCKEY}{int(registro_id)}"


class SigridWriteClient:
    def __init__(
        self,
        *,
        base_url: str,
        function_key: str,
        database: str,
        timeout_s: float = 60.0,
        max_statements: int = 15,
        tip_parte: int = 35,
        est_parte: int = 1,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._headers = {"x-functions-key": function_key,
                         "Content-Type": "application/json"}
        self._db = database
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
        if body.get("truncated"):
            # F-023 (R4): nunca se decide con filas parciales.
            raise RuntimeError("sigrid-api devolvio una respuesta truncada")
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

    _SQL_OBRA = (
        "SELECT obr.ide AS ide, con.cod AS cod, con.res AS res, "
        "obr.cenide AS cenide, con.emp AS emp "
        "FROM obr JOIN con ON con.ide = obr.ide "
    )

    @staticmethod
    def _a_obra(f: dict) -> ObraEntrada:
        o = ObraEntrada(ide=int(f["ide"]), codigo=f["cod"], nombre=f["res"],
                        empresa=int(f["emp"] or 0) or None)
        setattr(o, "cenide", int(f["cenide"] or 0))
        return o

    def obra_por_codigo(self, cod: str) -> ObraEntrada | None:
        """La obra de ese codigo. F-023 (R35): hay codigos en dos empresas;
        si hay varias obras, falla en vez de elegir una."""
        filas = self._read(self._SQL_OBRA + "WHERE con.cod = ?", [cod])
        if not filas:
            return None
        if len(filas) > 1:
            raise RuntimeError(
                f"la obra {cod} existe en varias empresas de Sigrid "
                f"({len(filas)} obras): no se elige ninguna")
        return self._a_obra(filas[0])

    def obra_por_ide(self, ide: int) -> ObraEntrada | None:
        filas = self._read(self._SQL_OBRA + "WHERE obr.ide = ?", [int(ide)])
        if not filas:
            return None
        return self._a_obra(filas[0])

    def recursos_por_dni(
        self, dnis: Iterable[str | None]
    ) -> dict[str, list[RecursoSigrid]]:
        """DNI normalizado -> TODOS sus recursos, con empresa y baja.

        Red de seguridad para lineas creadas sin recurso casado (p. ej.
        creacion manual antigua): mismo doble camino que la exclusion de
        extras (emp.dni via res.conide, y res.cif). F-023 (R37): ya no se
        elige aqui el de ide mas alto; elige `elegir_por_dni` con la
        empresa de la obra y la fecha de cada linea."""
        norm = {re.sub(r"[^0-9A-Za-z]", "", d or "").upper() for d in dnis}
        norm.discard("")
        if not norm:
            return {}
        ks = sorted(norm)
        marcas = ",".join("?" for _ in ks)
        dni_emp = _DNI_SQL.format(campo="emp.dni")
        dni_res = _DNI_SQL.format(campo="res.cif")
        sql = (
            "SELECT q.dnin AS dni, q.reside AS reside, rc.emp AS emp, "
            "rc.fecbaj AS fecbaj FROM ("
            f"  SELECT {dni_emp} AS dnin, res.ide AS reside"
            "  FROM res JOIN emp ON emp.ide = res.conide"
            f"  WHERE {dni_emp} IN ({marcas})"
            "  UNION ALL"
            f"  SELECT {dni_res} AS dnin, res.ide AS reside"
            "  FROM res"
            f"  WHERE {dni_res} IN ({marcas})"
            ") q JOIN con rc ON rc.ide = q.reside"
        )
        out: dict[str, list[RecursoSigrid]] = {}
        for f in self._read(sql, ks + ks):
            d = (f.get("dni") or "").strip()
            if d:
                out.setdefault(d, []).append(RecursoSigrid(
                    reside=int(f["reside"]), empresa=f.get("emp"),
                    fecbaj=f.get("fecbaj"), dni=d))
        logger.info("[sigrid-write] recursos_por_dni: %s/%s DNI con recurso",
                    len(out), len(ks))
        return out

    def datos_recursos(
        self, resides: Iterable[int | None]
    ) -> dict[int, RecursoSigrid]:
        """Empresa, baja y DNI de cada recurso, para verificarlo (R36).

        El DNI es `emp.dni` del empleado enlazado si no esta vacio y, si
        no, `res.cif`. En lotes de `LOTE_RECURSOS` (sin paginar)."""
        ides = sorted({int(i) for i in resides if i})
        out: dict[int, RecursoSigrid] = {}
        for i in range(0, len(ides), LOTE_RECURSOS):
            trozo = ides[i:i + LOTE_RECURSOS]
            marcas = ",".join("?" for _ in trozo)
            filas = self._read(
                "SELECT res.ide AS reside, rc.emp AS emp, rc.fecbaj AS fecbaj, "
                "CASE WHEN LTRIM(RTRIM(ISNULL(emp.dni,''))) <> '' "
                "THEN emp.dni ELSE res.cif END AS dni "
                "FROM res JOIN con rc ON rc.ide = res.ide "
                "LEFT JOIN emp ON emp.ide = res.conide "
                f"WHERE res.ide IN ({marcas})", trozo)
            for f in filas:
                out[int(f["reside"])] = RecursoSigrid(
                    reside=int(f["reside"]), empresa=f.get("emp"),
                    fecbaj=f.get("fecbaj"), dni=f.get("dni"))
        return out

    def horas_de_recursos(
        self, resides: Iterable[int]
    ) -> dict[int, list[HoraRecurso]]:
        ides = sorted({int(i) for i in resides if i})
        if not ides:
            return {}
        marcas = ",".join("?" for _ in ides)
        # F-021 (R9): en la MISMA consulta, el codigo de la cuenta de la
        # ficha (`reshor.caaide`, 0 = ninguna) y si es el tipo por defecto.
        filas = self._read(
            "SELECT reshor.reside AS reside, reshor.horide AS horide, "
            "auxhor.cod AS cod, auxhor.res AS res, reshor.pre AS pre, "
            "cc.cod AS caacod, "
            "CASE WHEN reshor.horide = res.horide THEN 1 ELSE 0 END "
            "AS defecto "
            "FROM reshor JOIN auxhor ON auxhor.ide = reshor.horide "
            "LEFT JOIN res ON res.ide = reshor.reside "
            "LEFT JOIN con cc ON cc.ide = reshor.caaide "
            "AND ISNULL(reshor.caaide, 0) <> 0 "
            f"WHERE reshor.reside IN ({marcas}) "
            "ORDER BY reshor.reside, auxhor.cod", ides)
        out: dict[int, list[HoraRecurso]] = {}
        for f in filas:
            out.setdefault(int(f["reside"]), []).append(HoraRecurso(
                horide=int(f["horide"]), cod=(f["cod"] or "").strip(),
                res=f["res"], pre=float(f["pre"] or 0.0),
                caa_cod=(f["caacod"] or "").strip() or None,
                defecto=bool(f["defecto"])))
        return out

    def cuentas_de_centro(
        self, cenide: int, empresa: int, subcuentas: Iterable[str | None]
    ) -> dict[str, list[tuple[int, str]]]:
        """Cuentas analiticas del centro, de esa empresa, con esas
        subcuentas (F-021, R10): UNA lectura, agrupada por subcuenta.

        El filtro SQL solo acota; la agrupacion la rehace `indexar_cuentas`
        con la misma `subcuenta()` del origen. Un fallo o un `truncated`
        sube como excepcion (R11)."""
        subs = sorted({s for s in subcuentas if s})
        if not subs:
            return {}
        marcas = ",".join("?" for _ in subs)
        filas = self._read(
            "SELECT a.ide AS caaide, c.cod AS cod FROM caa a "
            "JOIN con c ON c.ide = a.ide WHERE a.cenide = ? AND c.emp = ? "
            "AND LTRIM(RTRIM(SUBSTRING(c.cod, CHARINDEX('.', c.cod) + 1, "
            f"24))) IN ({marcas})", [int(cenide), int(empresa)] + subs)
        return indexar_cuentas((f["caaide"], f["cod"]) for f in filas)

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

    def partes_del_periodo(self, obra_ide: int, ano: int,
                           mes: int) -> list[ParteSigrid]:
        """F-031 (R1): TODOS los partes de obra (sin recurso) y mes, con su
        estado, por `ide` descendente. UNA lectura; un `truncated` sube
        como excepcion (R15)."""
        filas = self._read(
            "SELECT hmo.ide AS ide, con.cod AS cod, con.est AS est FROM hmo "
            "JOIN con ON con.ide = hmo.ide "
            "WHERE hmo.obride = ? AND hmo.ano = ? AND hmo.mes = ? "
            "AND ISNULL(hmo.reside, 0) = 0 AND con.tip = ? "
            "ORDER BY hmo.ide DESC",
            [int(obra_ide), int(ano), int(mes), self._tip])
        return [ParteSigrid(ide=int(f["ide"]), cod=f["cod"],
                            est=None if f["est"] is None else int(f["est"]))
                for f in filas]

    def partidas_de_lineas(
        self, parides: Iterable[int | None]
    ) -> dict[int, PartidaCuenta]:
        """F-031 (R24): partida -> su cuenta analitica (`obrparpar.caaide`,
        0 = ninguna), en UNA lectura. Sin partidas no se lee."""
        ides = sorted({int(i) for i in parides if i})
        if not ides:
            return {}
        marcas = ",".join("?" for _ in ides)
        filas = self._read(
            "SELECT p.ide AS ide, p.cod AS cod, pc.cod AS caacod "
            "FROM obrparpar p LEFT JOIN con pc ON pc.ide = p.caaide "
            "AND ISNULL(p.caaide, 0) <> 0 "
            f"WHERE p.ide IN ({marcas})", ides)
        out: dict[int, PartidaCuenta] = {}
        for f in filas:
            ide = int(f["ide"])
            out[ide] = PartidaCuenta(
                ide=ide, cod=(f["cod"] or "").strip() or None,
                caa_cod=(f["caacod"] or "").strip() or None)
        return out

    def siguiente_cod_pt(self, ano: int, empresa: int) -> str:
        """Siguiente `PT<AA>/NNNNN` de ESA empresa (F-023, R33): el
        correlativo es por empresa y los numeros se repiten entre ellas."""
        yy = str(int(ano))[-2:]
        filas = self._read(
            "SELECT MAX(cod) AS maxcod FROM con WHERE cod LIKE ? AND emp = ?",
            [f"PT{yy}/%", int(empresa)])
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

    # ------------------ comprobacion (F-024, solo lectura) ------------------ #

    def lineas_por_ide(self, ides: Iterable[int | None]) -> dict[int, LineaSigrid]:
        """Filas de `hmores` por `ide`, para el respaldo de R3 (F-024).

        Lotes de `LOTE_COMPROBACION` (R7); `_read` ya convierte un
        `truncated` en excepcion (R8). La base es la de escritura: una
        replica con retraso daria por borradas lineas recien escritas."""
        ks = sorted({int(i) for i in ides if i})
        out: dict[int, LineaSigrid] = {}
        for i in range(0, len(ks), LOTE_COMPROBACION):
            trozo = ks[i:i + LOTE_COMPROBACION]
            marcas = ",".join("?" for _ in trozo)
            filas = self._read(
                "SELECT ide, hmoide, reside, fec, horide, can, tot, synckey "
                f"FROM hmores WHERE ide IN ({marcas})", trozo)
            for f in filas:
                sk = (f["synckey"] or "").strip() or None
                ls = LineaSigrid(
                    ide=int(f["ide"]), reside=int(f["reside"] or 0),
                    fecha_int=int(f["fec"] or 0),
                    horide=int(f["horide"] or 0) or None, hora_codigo=None,
                    can=f["can"], tot=f["tot"], synckey=sk,
                    nuestra=bool(sk and sk.startswith(PREFIJO_SYNCKEY)))
                setattr(ls, "hmoide", int(f["hmoide"] or 0))
                out[ls.ide] = ls
        return out

    def partes_por_ide(self, hmoides: Iterable[int | None]) -> dict[int, str]:
        """`hmo.ide` -> `con.cod` de los partes que existen (F-024, R4/R5)."""
        ks = sorted({int(i) for i in hmoides if i})
        out: dict[int, str] = {}
        for i in range(0, len(ks), LOTE_COMPROBACION):
            trozo = ks[i:i + LOTE_COMPROBACION]
            marcas = ",".join("?" for _ in trozo)
            filas = self._read(
                "SELECT hmo.ide AS ide, con.cod AS cod FROM hmo "
                f"JOIN con ON con.ide = hmo.ide WHERE hmo.ide IN ({marcas})",
                trozo)
            for f in filas:
                out[int(f["ide"])] = f["cod"]
        return out

    # -------------------------- sentencias -------------------------- #

    def stmts_crear_parte(
        self, *, obra: ObraEntrada, ano: int, mes: int, cod: str, desc: str
    ) -> list[dict]:
        """Cabecera (con) + extension (hmo) del parte de obra/mes, en UNA
        transaccion (un solo lote de `escribir`).

        F-023: la cabecera es de la empresa de la obra (R32) y el `hmo` la
        busca por codigo, tipo y empresa (R34). Una obra sin empresa no
        genera sentencias (`TypeError`; el pipeline ya la rechaza antes,
        R35).

        F-031 v5 (R41-R42), ALTA PROTEGIDA, COMUN CON `porcentajes`: su
        `dedicacion-transfer` tambien da de alta partes de obra en Sigrid y
        este alta es texto y orden de parametros IDENTICOS al suyo (F-037,
        `stmts_crear_parte`; unica diferencia admitida: alli una obra sin
        empresa es `ValueError`). La cabecera solo entra si el codigo esta
        libre en la empresa y si el periodo NO tiene ya un parte En
        registro, comprobado con bloqueo y FUERA del agregado `MAX(ide)` (un
        `SELECT MAX(...) ... WHERE NOT EXISTS` devuelve fila aunque la
        condicion falle). El `hmo` se cuelga del `con` solo si aun no lo
        tiene. El pipeline relee el periodo despues. Cambiar este alta
        obliga a avisar a `porcentajes` en el mismo trabajo."""
        empresa = int(obra.empresa)  # type: ignore[arg-type]
        ultimo = calendar.monthrange(int(ano), int(mes))[1]
        fec = int(f"{int(ano)}{int(mes):02d}{ultimo:02d}")
        cenide = int(getattr(obra, "cenide", 0) or 0)
        return [
            {"sql": ("INSERT INTO con (ide, emp, tip, est, cod, res, fec) "
                     "SELECT x.n, ?, ?, ?, ?, ?, ? FROM "
                     "(SELECT ISNULL(MAX(ide),0)+1 AS n "
                     "FROM con WITH (UPDLOCK, HOLDLOCK)) x "
                     "WHERE NOT EXISTS (SELECT 1 FROM con c "
                     "WITH (UPDLOCK, HOLDLOCK) "
                     "WHERE c.cod = ? AND c.emp = ? AND c.tip = ?) "
                     "AND NOT EXISTS (SELECT 1 FROM hmo h "
                     "WITH (UPDLOCK, HOLDLOCK) JOIN con r "
                     "WITH (UPDLOCK, HOLDLOCK) ON r.ide = h.ide "
                     "WHERE h.obride = ? AND h.ano = ? AND h.mes = ? "
                     "AND ISNULL(h.reside, 0) = 0 AND r.tip = ? "
                     "AND r.est = ?)"),
             "parameters": [empresa, self._tip, self._est,
                            cod, desc[:128], fec,
                            cod, empresa, self._tip,
                            int(obra.ide), int(ano), int(mes), self._tip,
                            self._est]},
            {"sql": ("INSERT INTO hmo (ide, cenide, obride, ano, mes, reside, "
                     "cenmul) SELECT ide, ?, ?, ?, ?, 0, 0 FROM con "
                     "WHERE cod = ? AND tip = ? AND emp = ? "
                     "AND NOT EXISTS (SELECT 1 FROM hmo h "
                     "WHERE h.ide = con.ide)"),
             "parameters": [cenide, int(obra.ide), int(ano), int(mes),
                            cod, self._tip, empresa]},
        ]

    def stmt_insert_linea(
        self, *, hmoide: int, obra: ObraEntrada, reside: int, pos: int,
        fecha_int: int, horide: int, can: float, pre: float, paride: int,
        ano: int, mes: int, synckey: str, tex: str | None, caaide: int,
    ) -> dict:
        """Linea `hmores`. F-021 (R14): `caaide` es la cuenta analitica
        resuelta (0 = sin cuenta) y es OBLIGATORIO (DA9): un 0 por defecto
        esconderia una llamada que lo olvide."""
        cenide = int(getattr(obra, "cenide", 0) or 0)
        return {"sql": (
            "INSERT INTO hmores (ide, hmoide, reside, cenide, obride, paride, "
            "pos, fec, horide, can, pre, tot, ano, mes, fac, ortide, caaide, "
            "tex, synckey) SELECT ISNULL(MAX(ide),0)+1, ?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ? "
            "FROM hmores WITH (UPDLOCK, HOLDLOCK)"),
            "parameters": [int(hmoide), int(reside), cenide, int(obra.ide),
                           int(paride or 0), int(pos), int(fecha_int),
                           int(horide), float(can), float(pre),
                           round(float(can) * float(pre), 2), int(ano),
                           int(mes), int(caaide), (tex or ""), synckey]}

    @staticmethod
    def stmt_borrar_linea(ide: int) -> dict:
        return {"sql": "DELETE FROM hmores WHERE ide = ?",
                "parameters": [int(ide)]}
