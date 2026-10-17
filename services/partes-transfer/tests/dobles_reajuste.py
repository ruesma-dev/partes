# tests/dobles_reajuste.py
"""F-046 · `SigridFake` con el reajuste: lecturas y sentencias nuevas.

Extiende el doble de siempre (`tests/dobles.py`, que no cambia) con lo que
usa `ReajustePipeline`, y EVALUA el lote como lo haria SQL Server con las
sentencias reales:

  - `guardia`: si alguna de sus lineas existe y no todas estan como se
    leyeron (synckey, `can` = «antes», sin enlaces, parte En registro), o
    alguna extra nueva ya existe, el lote FALLA y no queda nada escrito
    (la API revierte la transaccion).
  - `actualizar`: `can` = «despues» y `tot = round(can x pre, 2)` solo si
    la fila sigue con «antes», sin enlaces y en un parte En registro.
  - `insertar_extra`: solo si su base ya tiene «despues» y su synckey no
    existe.

[E] R47: cualquier `borrar` en un lote, o una llamada a
`stmt_borrar_linea`, es un `AssertionError`: el reajuste no borra nunca.
Cada lote queda grabado en `lotes`. Datos SINTETICOS.
"""
from __future__ import annotations

import copy

from tests.dobles import SigridFake

_TOL = 0.001 + 1e-9


def _igual(a, b) -> bool:
    return abs(float(a or 0.0) - float(b or 0.0)) <= _TOL


class SigridReajusteFake(SigridFake):
    def __init__(self, *args, max_statements: int = 15, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.max_statements = max_statements
        #: Cada lote recibido por `escribir_lote` (aunque luego falle).
        self.lotes: list[list[dict]] = []
        #: Hook opcional: se llama dentro de `escribir_lote` ANTES de
        #: evaluar el lote (simula a alguien tocando Sigrid entre la
        #: lectura y la escritura).
        self.antes_de_escribir = None
        #: Valor de `lock.locked()` en cada lectura del reajuste.
        self.lock_en_lecturas: list[bool] = []

    # -- R47 ----------------------------------------------------------------
    @staticmethod
    def stmt_borrar_linea(ide: int) -> dict:  # type: ignore[override]
        raise AssertionError(f"R47: el reajuste pidio borrar la linea {ide}")

    # -- lecturas ------------------------------------------------------------
    def _anotar_lock(self) -> None:
        lock = self._verificador_lock
        self.lock_en_lecturas.append(bool(lock is not None and lock.locked()))

    def lineas_para_reajuste(self, claves):
        self._anotar_lock()
        self._lectura("lineas_para_reajuste")
        ks = {k for k in claves if k}
        out = {}
        for fila in self.lineas:
            if fila.get("synckey") in ks:
                ls = self._a_linea_sigrid(fila)
                ls.pre = fila.get("pre")
                ls.enlazada = bool(fila.get("enlazada"))
                out[fila["synckey"]] = ls
        return out

    def estados_de_partes(self, hmoides):
        self._anotar_lock()
        self._lectura("estados_de_partes")
        ks = {int(i) for i in hmoides if i}
        return {p["ide"]: {"cod": p["cod"], "est": p.get("est", 1),
                           "obride": p["obride"]}
                for p in self.partes if p["ide"] in ks}

    def partes_del_periodo(self, obra_ide, ano, mes):
        self._anotar_lock()
        return super().partes_del_periodo(obra_ide, ano, mes)

    # -- sentencias (opacas para el pipeline) -------------------------------
    def stmt_guardia_reajuste(self, lineas, nuevas=()):
        if not lineas:
            raise ValueError("la guardia necesita al menos una linea")
        return {"op": "guardia",
                "lineas": [(int(i), sk, float(a)) for i, sk, a in lineas],
                "nuevas": [sk for sk in nuevas if sk]}

    @staticmethod
    def stmt_actualizar_linea(*, ide, synckey, antes, despues, est_registro):
        return {"op": "actualizar", "ide": int(ide), "synckey": synckey,
                "antes": float(antes), "despues": float(despues),
                "est_registro": int(est_registro)}

    @staticmethod
    def stmt_insertar_extra(*, hmoide, obra, reside, pos, fecha_int, horide,
                            can, pre, paride, ano, mes, synckey, tex, caaide,
                            base_ide, base_synckey, base_despues):
        return {"op": "insertar_extra", "hmoide": int(hmoide),
                "obride": int(obra.ide), "reside": int(reside),
                "pos": int(pos), "fec": int(fecha_int), "horide": int(horide),
                "can": float(can), "pre": float(pre),
                "tot": round(float(can) * float(pre), 2),
                "paride": int(paride or 0), "ano": int(ano), "mes": int(mes),
                "synckey": synckey, "tex": tex or "", "caaide": int(caaide),
                "base_ide": int(base_ide), "base_synckey": base_synckey,
                "base_despues": float(base_despues)}

    # -- escritura ------------------------------------------------------------
    def _est_parte(self, hmoide) -> int | None:
        for p in self.partes:
            if p["ide"] == hmoide:
                return p.get("est", 1)
        return None

    def _por_ide(self, ide):
        return next((f for f in self.lineas if f["ide"] == ide), None)

    def _guardia_salta(self, st: dict) -> bool:
        existen = [self._por_ide(i) for i, _sk, _a in st["lineas"]]
        if not any(existen):
            return False        # el UPDATE no encuentra filas: no salta
        bien = sum(
            1 for (_i, sk, antes), f in zip(st["lineas"], existen)
            if f is not None and f.get("synckey") == sk
            and _igual(f.get("can"), antes) and not f.get("enlazada")
            and self._est_parte(f["hmoide"]) == 1)
        nuevas = any(f.get("synckey") in st["nuevas"] for f in self.lineas)
        return bien != len(st["lineas"]) or nuevas

    def _aplicar(self, st: dict) -> int:
        op = st["op"]
        if op == "borrar":
            raise AssertionError("R47: un DELETE en un lote de reajuste")
        if op == "guardia":
            if self._guardia_salta(st):
                raise RuntimeError(
                    "sigrid-api write HTTP 400: Conversion failed when "
                    "converting the varchar value 'reajuste-descuadrado-...'")
            return 0
        if op == "actualizar":
            f = self._por_ide(st["ide"])
            if (f is None or f.get("synckey") != st["synckey"]
                    or not _igual(f.get("can"), st["antes"])
                    or f.get("enlazada")
                    or self._est_parte(f["hmoide"]) != st["est_registro"]):
                return 0
            f["can"] = st["despues"]
            f["tot"] = round(st["despues"] * float(f.get("pre") or 0.0), 2)
            return 1
        if op == "insertar_extra":
            base = self._por_ide(st["base_ide"])
            if (base is None or base.get("synckey") != st["base_synckey"]
                    or not _igual(base.get("can"), st["base_despues"])
                    or any(f.get("synckey") == st["synckey"]
                           for f in self.lineas)):
                return 0
            self._siguiente_hmores += 1
            fila = {k: v for k, v in st.items()
                    if k not in ("op", "base_ide", "base_synckey",
                                 "base_despues", "obride")}
            fila["ide"] = self._siguiente_hmores
            fila["hora_codigo"] = None
            self.lineas.append(fila)
            return 1
        raise AssertionError(f"sentencia inesperada en un reajuste: {op}")

    def escribir_lote(self, statements):
        self._comprobar_lock("escribir_lote")
        self._entrar("escribir_lote", self.latencia_escritura)
        try:
            self.lotes.append(copy.deepcopy(statements))
            if len(statements) > self.max_statements:
                raise ValueError("el reajuste no cabe en un lote")
            if self.antes_de_escribir is not None:
                self.antes_de_escribir(self)
            copia = copy.deepcopy(self.lineas)
            siguiente = self._siguiente_hmores
            try:
                return [self._aplicar(st) for st in statements]
            except Exception:
                self.lineas = copia        # la transaccion se revierte
                self._siguiente_hmores = siguiente
                raise
        finally:
            self._salir("escribir_lote")
