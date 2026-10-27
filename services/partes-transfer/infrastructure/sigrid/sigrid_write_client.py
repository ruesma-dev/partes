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

F-034: toda sentencia que inserta o actualiza una fila de `hmores` lleva
la GUARDA DE PARTE ABIERTO (`_guarda_parte_abierto`): `EXISTS` sobre
`con` del parte de esa fila con `est = EST_PARTE_ACTIVO` y `UPDLOCK,
HOLDLOCK`, que retiene la fila de `con` hasta el `commit`. Si
Administracion cierra o contabiliza el parte en la ventana, la sentencia
afecta 0 filas y el pipeline lo descubre al releer (no por la respuesta).

F-053: en Sigrid no se borra. Pisar un conflicto confirmado pone la linea a
0 (`stmt_anular_linea`: `can = 0`, `tot = 0`, nada mas) y ninguna sentencia
de este cliente elimina filas; `lineas_existentes` dice si cada linea esta
enlazada (`_expr_enlazada`, la misma expresion que el reajuste).

F-060: el CIZ de una racha de incidencia se MUEVE al dia nuevo con
`stmt_mover_linea` (un `UPDATE` de fecha, synckey y parte de la misma
linea, con guarda en el parte de origen y en el de destino); lo localiza
`lineas_de_racha` por las synckeys de la racha que manda sv4.

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
from typing import Any, Iterable, Sequence

import httpx

from application.services.cuenta_analitica import indexar_cuentas
from domain.models.registro_models import (
    PREFIJO_FRANQUICIA, HoraRecurso, LineaSigrid, ObraEntrada, ParteDestino,
    ParteSigrid, PartidaCuenta, RecursoSigrid,
)

logger = logging.getLogger(__name__)

PREFIJO_SYNCKEY = "partes:"

#: Recursos por lectura en `datos_recursos` (lote acotado, F-023).
LOTE_RECURSOS = 500

#: `ide` por lectura en la comprobacion de lineas (F-024, R7).
LOTE_COMPROBACION = 200

#: F-038 (R2, DA1 = B): `max_rows` de toda lectura si no se pasa otro; el
#: tope de la instancia de sigrid-api. Igual que `SIGRID_API_MAX_ROWS`.
MAX_ROWS_DEFECTO = 500_000

#: F-046 (R21, DA17): enlaces de `hmores` con albaran, factura, dedicacion
#: y nomina. Una linea con alguno distinto de 0 no se reajusta.
ENLACES_HMORES: tuple[str, ...] = (
    "dvaproide", "dvfproide", "hdereside", "emprccide", "empdpreide",
    "empabside")

# DNI normalizado en SQL Server: mayusculas y sin guiones ni espacios.
_DNI_SQL = "REPLACE(REPLACE(UPPER(ISNULL({campo},'')),'-',''),' ','')"


#: F-062 (DA3): sufijo de la synckey del CIZ que el `inicio` escribe el
#: mismo dia que su CI* (el «hermano»): `partes:<id>:ciz`.
SUFIJO_CIZ = ":ciz"


def synckey_de(registro_id: int) -> str:
    return f"{PREFIJO_SYNCKEY}{int(registro_id)}"


def synckey_ciz_de(registro_id: int) -> str:
    """F-062 (R20): la synckey del CIZ hermano del inicio `registro_id`.
    Al moverse, el hermano pasa a la synckey del dia nuevo (`partes:<D>`)."""
    return f"{synckey_de(registro_id)}{SUFIJO_CIZ}"


def synckey_franquicia(ajuste_id: int) -> str:
    """F-056 (R31, DA14): la synckey de la linea de ajuste de la franquicia
    `ajuste_id` (`franquicia_ajuste.id` de sv4)."""
    return f"{PREFIJO_FRANQUICIA}{int(ajuste_id)}"


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
        max_rows: int = MAX_ROWS_DEFECTO,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._headers = {"x-functions-key": function_key,
                         "Content-Type": "application/json"}
        self._db = database
        self._timeout = float(timeout_s)
        self._max_st = int(max_statements)
        self._tip = int(tip_parte)
        self._est = int(est_parte)
        self._max_rows = int(max_rows)
        # F-038 (R6): limites efectivos, sin la clave.
        logger.info("[sigrid-write] Instanciado. database=%s timeout_s=%s "
                    "max_rows=%s", self._db, self._timeout, self._max_rows)

    # ----------------------------- HTTP ----------------------------- #

    def _read(self, sql: str, params: list) -> list[dict]:
        r = httpx.post(f"{self._base}/api/sql/read", headers=self._headers,
                       timeout=self._timeout + 30, json={
                           "database": self._db, "sql": sql,
                           "parameters": params,
                           "timeout_seconds": int(self._timeout),
                           "max_rows": self._max_rows})
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
        empresa de la obra y la fecha de cada linea. F-036 (R18): solo
        recursos PERSONA (`res.cla = 1`) en las dos ramas, los mismos
        candidatos que sv3 (`CLA_PERSONA` de `seleccion_sigrid`; lista
        cerrada de `CLAUDE.md`, guardian
        `tests/test_f036_recurso_persona_gemelos.py`)."""
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
            f"  WHERE {dni_emp} IN ({marcas}) AND res.cla = 1"
            "  UNION ALL"
            f"  SELECT {dni_res} AS dnin, res.ide AS reside"
            "  FROM res"
            f"  WHERE {dni_res} IN ({marcas}) AND res.cla = 1"
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
        """Lineas del parte `hmoide` de esos recursos y dias (choques del
        paso 7). F-053 (R9): con `enlazada` (la misma expresion que
        `lineas_para_reajuste`) y su `hmoide`, para el INFO de R13."""
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
            "hmores.tot AS tot, hmores.synckey AS synckey, "
            f"CASE WHEN {self._expr_enlazada()} THEN 1 ELSE 0 END "
            "AS enlazada FROM hmores "
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
                nuestra=bool(sk and sk.startswith(PREFIJO_SYNCKEY)),
                hmoide=int(hmoide), enlazada=bool(f["enlazada"])))
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

    def lineas_de_racha(
        self, claves: Iterable[str | None]
    ) -> dict[str, LineaSigrid]:
        """F-060 (R13): nuestras lineas por synckey con lo que el CIZ movil
        necesita: codigo de hora, `can`, `tex` (marca de pruebas, R19),
        `pos`, su parte y si esta enlazada (`_expr_enlazada`, la misma
        expresion que el reajuste y los choques). En lotes de
        `LOTE_COMPROBACION`; un `truncated` es una excepcion."""
        ks = sorted({k for k in claves if k})
        out: dict[str, LineaSigrid] = {}
        for i in range(0, len(ks), LOTE_COMPROBACION):
            trozo = ks[i:i + LOTE_COMPROBACION]
            marcas = ",".join("?" for _ in trozo)
            filas = self._read(
                "SELECT hmores.ide AS ide, hmores.hmoide AS hmoide, "
                "hmores.reside AS reside, hmores.fec AS fec, "
                "hmores.horide AS horide, auxhor.cod AS hora, "
                "hmores.can AS can, hmores.tot AS tot, "
                "hmores.synckey AS synckey, hmores.tex AS tex, "
                "hmores.pos AS pos, "
                f"CASE WHEN {self._expr_enlazada()} THEN 1 ELSE 0 END "
                "AS enlazada "
                "FROM hmores LEFT JOIN auxhor ON auxhor.ide = hmores.horide "
                f"WHERE hmores.synckey IN ({marcas})", trozo)
            for f in filas:
                sk = (f["synckey"] or "").strip()
                out[sk] = LineaSigrid(
                    ide=int(f["ide"]), reside=int(f["reside"] or 0),
                    fecha_int=int(f["fec"] or 0),
                    horide=int(f["horide"] or 0) or None,
                    hora_codigo=f["hora"], can=f["can"], tot=f["tot"],
                    synckey=sk, nuestra=True,
                    hmoide=int(f["hmoide"] or 0) or None,
                    enlazada=bool(f["enlazada"]), tex=f["tex"],
                    pos=None if f["pos"] is None else int(f["pos"]))
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

    def _guarda_parte_abierto(self, col: str) -> str:
        """F-034 (R1): la guarda de parte abierto sobre el parte `col` (un
        `?` o una columna como `hmores.hmoide`). El estado va como
        parametro (`EST_PARTE_ACTIVO`) y la lectura de `con` con `UPDLOCK,
        HOLDLOCK`: el cierre en Sigrid espera a nuestro `commit`, asi que
        comprobar y escribir es atomico."""
        return ("EXISTS (SELECT 1 FROM con c WITH (UPDLOCK, HOLDLOCK) "
                f"WHERE c.ide = {col} AND c.est = ?)")

    def stmt_insert_linea(
        self, *, hmoide: int, obra: ObraEntrada, reside: int, pos: int,
        fecha_int: int, horide: int, can: float, pre: float, paride: int,
        ano: int, mes: int, synckey: str, tex: str | None, caaide: int,
        pisadas: Sequence[int] = (),
    ) -> dict:
        """Linea `hmores`. F-021 (R14): `caaide` es la cuenta analitica
        resuelta (0 = sin cuenta) y es OBLIGATORIO (DA9): un 0 por defecto
        esconderia una llamada que lo olvide.

        F-034 (R2): el `ide` sale de la subconsulta `x` (un agregado con
        `WHERE` falso devolveria fila igualmente) y la linea solo entra si
        su parte sigue En registro. R4: con `pisadas` (las lineas de un
        conflicto confirmado), solo si ninguna sigue con horas: si su
        puesta a 0 no entro (F-053), la nueva no duplica horas."""
        cenide = int(getattr(obra, "cenide", 0) or 0)
        ides_pisadas = [int(i) for i in pisadas]
        sql = (
            "INSERT INTO hmores (ide, hmoide, reside, cenide, obride, paride, "
            "pos, fec, horide, can, pre, tot, ano, mes, fac, ortide, caaide, "
            "tex, synckey) SELECT x.n, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            "0, 0, ?, ?, ? FROM (SELECT ISNULL(MAX(ide),0)+1 AS n FROM hmores "
            "WITH (UPDLOCK, HOLDLOCK)) x "
            f"WHERE {self._guarda_parte_abierto('?')}")
        if ides_pisadas:
            sql += (" AND NOT EXISTS (SELECT 1 FROM hmores p WHERE p.ide IN "
                    f"({','.join('?' for _ in ides_pisadas)}) "
                    "AND ISNULL(p.can, 0) <> 0)")
        return {"sql": sql,
                "parameters": [int(hmoide), int(reside), cenide, int(obra.ide),
                               int(paride or 0), int(pos), int(fecha_int),
                               int(horide), float(can), float(pre),
                               round(float(can) * float(pre), 2), int(ano),
                               int(mes), int(caaide), (tex or ""), synckey,
                               int(hmoide), self._est, *ides_pisadas]}

    def stmt_insert_inicio_con_fin(
        self, *, hmoide: int, obra: ObraEntrada, reside: int, fecha_int: int,
        paride: int | None, ano: int, mes: int, tex: str | None,
        pos: int, horide: int, pre: float, caaide: int, synckey: str,
        pos_fin: int, horide_fin: int, pre_fin: float, caaide_fin: int,
        synckey_fin: str,
    ) -> dict:
        """F-062 (R13, DA2): el CI* del `inicio` y su CIZ hermano en UNA
        sentencia de dos filas, atomica en SQL Server (las dos o ninguna),
        sin depender del corte en lotes de `escribir`.

        Columnas y valores de `stmt_insert_linea`; `can` y `tot` literales
        0 (las incidencias van sin horas). La fila `k` = 0 es el CI* y la
        `k` = 1 el hermano (`horide`, `pre`, cuenta, `pos` y synckey
        propios; su `ide` es el siguiente al del CI*). La guarda de parte
        abierto de F-034 vale para las dos filas y, solo en la del hermano,
        que no exista ya una linea con su synckey (reentrega o carrera)."""
        cenide = int(getattr(obra, "cenide", 0) or 0)
        sql = (
            "INSERT INTO hmores (ide, hmoide, reside, cenide, obride, paride, "
            "pos, fec, horide, can, pre, tot, ano, mes, fac, ortide, caaide, "
            "tex, synckey) SELECT x.n + v.k, ?, ?, ?, ?, ?, v.pos, ?, "
            "v.horide, 0, v.pre, 0, ?, ?, 0, 0, v.caaide, ?, v.synckey "
            "FROM (SELECT ISNULL(MAX(ide),0)+1 AS n FROM hmores "
            "WITH (UPDLOCK, HOLDLOCK)) x "
            "CROSS JOIN (VALUES (0, ?, ?, ?, ?, ?), (1, ?, ?, ?, ?, ?)) "
            "v(k, pos, horide, pre, caaide, synckey) "
            f"WHERE {self._guarda_parte_abierto('?')} "
            "AND (v.k = 0 OR NOT EXISTS (SELECT 1 FROM hmores s "
            "WHERE s.synckey = ?))")
        return {"sql": sql,
                "parameters": [int(hmoide), int(reside), cenide, int(obra.ide),
                               int(paride or 0), int(fecha_int), int(ano),
                               int(mes), (tex or ""),
                               int(pos), int(horide), float(pre), int(caaide),
                               synckey,
                               int(pos_fin), int(horide_fin), float(pre_fin),
                               int(caaide_fin), synckey_fin,
                               int(hmoide), self._est, synckey_fin]}

    def stmt_anular_linea(self, *, ide: int, reside: int, fecha_int: int,
                          horide: int | None, antes: float | None) -> dict:
        """F-053 (R2, R3, DA12): pisar un conflicto confirmado pone la linea
        a 0 en vez de borrarla. Solo `can` y `tot` (`tot = 0` literal: no
        depende de un `pre` nulo); synckey, `tex`, cuenta y lo demas no se
        tocan. `WHERE` optimista con lo que la hizo chocar (`ide`, recurso,
        dia, codigo y `can` leido), sin enlaces y con la guarda de parte
        abierto de F-034: si algo cambio, afecta 0 filas."""
        return {"sql": (
            "UPDATE hmores SET can = 0, tot = 0 WHERE ide = ? AND reside = ? "
            "AND fec = ? AND ISNULL(horide, 0) = ? "
            "AND ABS(ISNULL(can, 0) - ?) <= 0.001 "
            + self._sin_enlaces() + " AND "
            + self._guarda_parte_abierto("hmores.hmoide")),
            "parameters": [int(ide), int(reside), int(fecha_int),
                           int(horide or 0), float(antes or 0), self._est]}

    def stmt_mover_linea(
        self, *, linea: LineaSigrid, destino: ObraEntrada, hmoide: int,
        pos: int, fecha_int: int, synckey: str, paride: int | None,
        caaide: int, ano: int, mes: int,
    ) -> dict:
        """F-060 (R20, R21, DA3): el CIZ de la racha pasa al dia D con UN
        `UPDATE` de esa misma linea (en Sigrid no se borra): fecha,
        synckey del registro de D y, del parte elegido para D (F-031), su
        `hmoide`, la obra y el centro de `destino` (como
        `stmt_insert_linea`), la partida y la cuenta de la accion de D, el
        periodo y la `pos`. `can`, `tot`, `pre`, `horide`, `reside`, `tex`
        y los enlaces no cambian.

        `WHERE` optimista con lo leido (`ide`, recurso, fecha, codigo y
        synckey), sin horas y sin enlaces, y la guarda de parte abierto de
        F-034 dos veces: SQL Server evalua el `WHERE` sobre la fila ANTES
        del `UPDATE`, asi que la primera mira el parte de ORIGEN
        (`hmores.hmoide`) y la segunda el de DESTINO (parametro). Si algo
        cambio, 0 filas: lo descubre la relectura por synckey (R23)."""
        cenide = int(getattr(destino, "cenide", 0) or 0)
        return {"sql": (
            "UPDATE hmores SET fec = ?, synckey = ?, hmoide = ?, obride = ?, "
            "cenide = ?, paride = ?, caaide = ?, ano = ?, mes = ?, pos = ? "
            "WHERE ide = ? AND reside = ? AND fec = ? "
            "AND ISNULL(horide, 0) = ? AND synckey = ? "
            "AND ISNULL(can, 0) = 0 "
            f"AND NOT ({self._expr_enlazada()}) "
            f"AND {self._guarda_parte_abierto('hmores.hmoide')} "
            f"AND {self._guarda_parte_abierto('?')}"),
            "parameters": [int(fecha_int), synckey, int(hmoide),
                           int(destino.ide), cenide, int(paride or 0),
                           int(caaide), int(ano), int(mes), int(pos),
                           int(linea.ide), int(linea.reside),
                           int(linea.fecha_int), int(linea.horide or 0),
                           linea.synckey, self._est, int(hmoide), self._est]}

    # ------------------ reajuste (F-046): lecturas ------------------ #

    @staticmethod
    def _expr_enlazada() -> str:
        """R21 de F-046 y R9 de F-053: alguno de `ENLACES_HMORES` distinto
        de 0. La comparten `lineas_para_reajuste` y `lineas_existentes`."""
        return " OR ".join(f"ISNULL(hmores.{c}, 0) <> 0"
                           for c in ENLACES_HMORES)

    def lineas_para_reajuste(
        self, claves: Iterable[str | None]
    ) -> dict[str, LineaSigrid]:
        """Nuestras lineas por synckey con lo que el reajuste mira (R21):
        `can`, `pre` (el `tot` se recalcula con el, R24), su parte
        (`hmoide`) y si algun enlace de `ENLACES_HMORES` no es 0. En lotes
        de `LOTE_COMPROBACION`; un `truncated` es una excepcion."""
        ks = sorted({k for k in claves if k})
        out: dict[str, LineaSigrid] = {}
        for i in range(0, len(ks), LOTE_COMPROBACION):
            trozo = ks[i:i + LOTE_COMPROBACION]
            marcas = ",".join("?" for _ in trozo)
            filas = self._read(
                "SELECT hmores.ide AS ide, hmores.hmoide AS hmoide, "
                "hmores.reside AS reside, hmores.fec AS fec, "
                "hmores.horide AS horide, auxhor.cod AS hora, "
                "hmores.can AS can, hmores.tot AS tot, hmores.pre AS pre, "
                "hmores.synckey AS synckey, "
                f"CASE WHEN {self._expr_enlazada()} THEN 1 ELSE 0 END "
                "AS enlazada "
                "FROM hmores LEFT JOIN auxhor ON auxhor.ide = hmores.horide "
                f"WHERE hmores.synckey IN ({marcas})", trozo)
            for f in filas:
                sk = (f["synckey"] or "").strip()
                out[sk] = LineaSigrid(
                    ide=int(f["ide"]), reside=int(f["reside"] or 0),
                    fecha_int=int(f["fec"] or 0),
                    horide=int(f["horide"] or 0) or None,
                    hora_codigo=f["hora"], can=f["can"], tot=f["tot"],
                    synckey=sk, nuestra=True,
                    pre=None if f["pre"] is None else float(f["pre"]),
                    hmoide=int(f["hmoide"] or 0) or None,
                    enlazada=bool(f["enlazada"]))
        return out

    def estados_de_partes(
        self, hmoides: Iterable[int | None]
    ) -> dict[int, dict]:
        """`hmo.ide` -> `{cod, est, obride}` de esos partes (R21, R22), en
        lotes de `LOTE_COMPROBACION`. Sin partes no se lee."""
        ks = sorted({int(i) for i in hmoides if i})
        out: dict[int, dict] = {}
        for i in range(0, len(ks), LOTE_COMPROBACION):
            trozo = ks[i:i + LOTE_COMPROBACION]
            marcas = ",".join("?" for _ in trozo)
            filas = self._read(
                "SELECT hmo.ide AS ide, hmo.obride AS obride, con.cod AS cod, "
                "con.est AS est FROM hmo JOIN con ON con.ide = hmo.ide "
                f"WHERE hmo.ide IN ({marcas})", trozo)
            for f in filas:
                out[int(f["ide"])] = {
                    "cod": f["cod"],
                    "est": None if f["est"] is None else int(f["est"]),
                    "obride": int(f["obride"] or 0) or None}
        return out

    # ------------------ reajuste (F-046): sentencias ------------------ #
    # [E] R47: el reajuste NUNCA borra en Sigrid. Solo `UPDATE` de lineas
    # existentes (a 0 si hace falta) e `INSERT` de extras nuevas. Desde
    # F-053 tampoco el pisado: el cliente no tiene sentencias de borrado.

    @staticmethod
    def _sin_enlaces(alias: str = "") -> str:
        pre = f"{alias}." if alias else ""
        return " ".join(f"AND ISNULL({pre}{c}, 0) = 0" for c in ENLACES_HMORES)

    def stmt_guardia_reajuste(
        self, lineas: list[tuple[int, str, float]],
        nuevas: Iterable[str] = (),
    ) -> dict:
        """Primera sentencia del lote (DA6): si alguna linea existente ya no
        esta como se leyo (synckey, `can` = «antes», sin enlaces, parte En
        registro) o alguna extra nueva ya existe, FALLA y la API revierte
        el lote entero. F-034 (R5): el parte se lee con la guarda de parte
        abierto (`UPDLOCK, HOLDLOCK`).

        Cuenta las lineas en su estado esperado y, si no son todas, intenta
        convertir a entero un texto: el error de conversion salta siempre
        (no depende de `ANSI_WARNINGS`, a diferencia de dividir por 0, que
        con ellos apagados dejaria `can` a NULL) y su mensaje nombra la
        linea. Si la condicion se cumple no toca ninguna fila."""
        if not lineas:
            raise ValueError("la guardia necesita al menos una linea")
        ides = [int(i) for i, _sk, _a in lineas]
        marcas = ",".join("?" for _ in ides)
        por_linea = " OR ".join(
            "(h.ide = ? AND h.synckey = ? AND ABS(ISNULL(h.can, 0) - ?) "
            "<= 0.001)" for _ in lineas)
        params: list[Any] = list(ides)
        for ide, sk, antes in lineas:
            params += [int(ide), sk, float(antes)]
        params += [self._est, len(lineas)]
        sql = (
            "UPDATE hmores SET can = CONVERT(INT, 'reajuste-descuadrado-' + "
            f"CAST(ide AS VARCHAR(20))) WHERE ide IN ({marcas}) AND (("
            f"SELECT COUNT(*) FROM hmores h WHERE ({por_linea}) "
            f"{self._sin_enlaces('h')} AND "
            f"{self._guarda_parte_abierto('h.hmoide')}) <> ?")
        claves = [sk for sk in nuevas if sk]
        if claves:
            sql += (" OR EXISTS (SELECT 1 FROM hmores n WHERE n.synckey IN "
                    f"({','.join('?' for _ in claves)}))")
            params += claves
        return {"sql": sql + ")", "parameters": params}

    def stmt_actualizar_linea(
        self, *, ide: int, synckey: str, antes: float, despues: float,
        est_registro: int,
    ) -> dict:
        """R24, R25: `can` = «despues» y `tot = ROUND(can x pre, 2)` con el
        `pre` de la PROPIA linea; cuenta, partida y codigo de hora no se
        tocan. El `WHERE` repite la condicion optimista: si la linea cambio
        afecta 0 filas. [E] A 0 es `can = 0` y `tot = 0`, nunca un borrado.
        F-034 (R5): el parte se lee con la guarda de parte abierto; el
        estado sigue siendo el parametro `est_registro`."""
        return {"sql": (
            "UPDATE hmores SET can = ?, tot = ROUND(? * ISNULL(pre, 0), 2) "
            "WHERE ide = ? AND synckey = ? AND ABS(ISNULL(can, 0) - ?) "
            "<= 0.001 AND "
            f"{self._guarda_parte_abierto('hmores.hmoide')} "
            + self._sin_enlaces()),
            "parameters": [float(despues), float(despues), int(ide), synckey,
                           float(antes), int(est_registro)]}

    def stmt_insertar_extra(
        self, *, hmoide: int, obra: ObraEntrada, reside: int, pos: int,
        fecha_int: int, horide: int, can: float, pre: float, paride: int,
        ano: int, mes: int, synckey: str, tex: str | None, caaide: int,
        base_ide: int, base_synckey: str, base_despues: float,
    ) -> dict:
        """R24: la extra nueva, con las mismas columnas que
        `stmt_insert_linea` (pos, cuenta y `tex` como el registro), pero
        CONDICIONADA: solo entra si su base ya tiene «despues» (el `UPDATE`
        de la base va antes en el mismo lote) y su synckey no existe. El
        `MAX(ide)+1` va en una subconsulta: un agregado con `WHERE` falso
        devolveria fila igualmente (la trampa que ya evita
        `stmts_crear_parte`). F-034 (R6): ademas, la guarda de parte abierto
        sobre su `hmoide` (antes solo la protegia, de forma indirecta, el
        `UPDATE` de su base)."""
        cenide = int(getattr(obra, "cenide", 0) or 0)
        return {"sql": (
            "INSERT INTO hmores (ide, hmoide, reside, cenide, obride, paride, "
            "pos, fec, horide, can, pre, tot, ano, mes, fac, ortide, caaide, "
            "tex, synckey) SELECT x.n, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            "0, 0, ?, ?, ? FROM (SELECT ISNULL(MAX(ide),0)+1 AS n FROM hmores "
            "WITH (UPDLOCK, HOLDLOCK)) x WHERE EXISTS (SELECT 1 FROM hmores b "
            "WHERE b.ide = ? AND b.synckey = ? AND ABS(ISNULL(b.can, 0) - ?) "
            "<= 0.001) AND NOT EXISTS (SELECT 1 FROM hmores s "
            "WHERE s.synckey = ?) "
            f"AND {self._guarda_parte_abierto('?')}"),
            "parameters": [int(hmoide), int(reside), cenide, int(obra.ide),
                           int(paride or 0), int(pos), int(fecha_int),
                           int(horide), float(can), float(pre),
                           round(float(can) * float(pre), 2), int(ano),
                           int(mes), int(caaide), (tex or ""), synckey,
                           int(base_ide), base_synckey, float(base_despues),
                           synckey, int(hmoide), self._est]}

    def escribir_lote(self, statements: list[dict]) -> list[int]:
        """R24, R27: el lote ENTERO en una sola llamada a `sql/write` (una
        transaccion). Devuelve las filas afectadas por sentencia; si no cabe
        en un lote, `ValueError` sin escribir nada."""
        if not statements:
            return []
        if len(statements) > self._max_st:
            raise ValueError(
                f"el reajuste no cabe en un lote: {len(statements)} "
                f"sentencias y el tope es {self._max_st}")
        for st in statements:
            logger.info("[sigrid-write] reajuste %s | %s",
                        " ".join(st["sql"].split())[:150], st["parameters"])
        r = httpx.post(f"{self._base}/api/sql/write", headers=self._headers,
                       timeout=self._timeout + 60,
                       json={"database": self._db, "statements": statements})
        if r.status_code >= 400:
            raise RuntimeError(f"sigrid-api write HTTP {r.status_code}: "
                               f"{r.text[:500]}")
        body = r.json()
        if not body.get("ok") or not body.get("committed"):
            raise RuntimeError(f"escritura no confirmada: {str(body)[:400]}")
        resultados = body.get("results")
        if (not isinstance(resultados, list)
                or len(resultados) != len(statements)):
            raise RuntimeError(
                "sigrid-api no devolvio las filas por sentencia: "
                f"{str(body)[:400]}")
        return [int(x.get("affected_rows") or 0) for x in resultados]

    # ------------------ franquicia de extras (F-056) ------------------ #

    #: R23, DA3: extras NETAS `HE*` del recurso en el periodo, de todas las
    #: obras y partes (cualquier estado), sin la propia linea de ajuste.
    _SQL_EXTRAS_PERIODO = (
        "SELECT ISNULL(SUM(h.can), 0) AS extras FROM hmores h "
        "JOIN auxhor a ON a.ide = h.horide WHERE h.reside = ? "
        "AND h.fec BETWEEN ? AND ? AND a.cod LIKE 'HE%' "
        "AND ISNULL(h.synckey, '') <> ?")

    @staticmethod
    def synckey_franquicia(ajuste_id: int) -> str:
        """La de `synckey_franquicia` del modulo, a mano del pipeline."""
        return synckey_franquicia(ajuste_id)

    def extras_del_periodo(self, reside: int, inicio: int, fin: int,
                           excluir: str) -> float:
        """R23: UNA lectura agregada; `inicio` y `fin` (`YYYYMMDD`)
        incluidos y `excluir` la synckey del ajuste. Un `truncated` o un
        fallo es una excepcion (nunca se decide con datos parciales)."""
        filas = self._read(self._SQL_EXTRAS_PERIODO,
                           [int(reside), int(inicio), int(fin), excluir])
        return float((filas[0]["extras"] if filas else 0) or 0.0)

    #: R39: el tipo de la columna del campo, con el nombre como PARAMETRO.
    _SQL_TIPO_COLUMNA_RES = (
        "SELECT DATA_TYPE AS tipo FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'res' "
        "AND COLUMN_NAME = ?")

    def tipo_columna_res(self, campo: str) -> str | None:
        """R39: `DATA_TYPE` de la columna `campo` de `dbo.res`, o None si no
        existe. Un fallo o un `truncated` es una excepcion."""
        filas = self._read(self._SQL_TIPO_COLUMNA_RES, [campo])
        return str(filas[0]["tipo"]) if filas else None

    def valores_campo_res(self, resides: Iterable[int],
                          campo: str) -> dict[int, Any]:
        """R1, R40: el valor crudo del campo de cada recurso que existe
        (`res.ide` -> valor; NULL es None), en lotes de `LOTE_RECURSOS`. El
        nombre va entre corchetes (un nombre de columna no se parametriza):
        si no casa `CAMPO_RE`, `ValueError` ANTES de leer (R38)."""
        # Import local: `franquicia` -> `pisado` -> este modulo (ciclo).
        from application.services.franquicia import CAMPO_RE

        if not isinstance(campo, str) or not CAMPO_RE.match(campo):
            raise ValueError(
                f"FRANQUICIA_CAMPO_RES no es un identificador: {campo!r}")
        ides = sorted({int(i) for i in resides if i})
        out: dict[int, Any] = {}
        for i in range(0, len(ides), LOTE_RECURSOS):
            trozo = ides[i:i + LOTE_RECURSOS]
            marcas = ",".join("?" for _ in trozo)
            filas = self._read(
                f"SELECT res.ide AS reside, res.[{campo}] AS valor FROM res "
                f"WHERE res.ide IN ({marcas})", trozo)
            for f in filas:
                out[int(f["reside"])] = f.get("valor")
        return out
