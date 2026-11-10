# application/services/sincronizar_ambito.py
"""F-052 · Sincronizar con Sigrid una obra o una persona (design §2).

  boton -> POST /api/sincronizar {ambito} -> SincronizadorAmbito
     1. ambito -> obra_ide | recurso_ide y el periodo visible (desde, hasta)
     2. repositorio.lineas_para_sincronizar          (base `partes`, lectura)
     3. sv5 POST /api/sincronizar/leer               (Sigrid, lectura)
     4. sincronizacion.clasificar                    (puro)
     5. `registrado` sin pareja -> R10 (F-024)
     6. repositorio.donde_estan de las `solo_sigrid_nuestra` (R12)

El resultado es efimero (R14). La unica escritura posible es la de R10
(`ComprobacionSigrid.comprobar_ids`, que pasa a `borrado_sigrid` como
F-024) y SOLO fuera del modo seco (DA18): en seco se pide a sv5 el mismo
veredicto (`/api/registro/comprobar`, lectura) y se informa de lo que se
pasaria, sin tocar la base `partes`.
"""
from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from application.services.calendar_builder import (
    normalize_mode,
    parse_period_key,
    period_bounds,
)
from application.services.congelacion import CongeladoError
from application.services.parte_vacio import DuplicadoActivoError
from application.services.sincronizacion import (
    DESCARTE_CAMBIO,
    DESCARTE_NO_EXISTE,
    ItemSync,
    LineaSigridSync,
    acciones_de,
    clasificar,
    firma,
    item_a_dict,
    resumen,
)

logger = logging.getLogger(__name__)

#: Origen que se pone en el log de la comprobacion de F-024 (R10).
ORIGEN_COMPROBACION = "sincronizar"

#: Origenes que sv5 puede devolver (DA12).
ORIGENES = ("partes", "ciz", "franquicia", "ajena", "manual")

#: Vista -> (campo de la clave en el ambito, prefijo que lee Sigrid).
_VISTAS = {"obra": ("obra_key", "obr-"), "trabajador": ("worker_key", "rec-")}

_MOTIVOS = {
    "obra": "la obra no esta casada con una obra de Sigrid",
    "trabajador": "la persona no esta casada con un recurso de Sigrid",
}

#: R16/R18: las acciones de `POST /api/sincronizar/aplicar` (design §4).
ACCIONES = ("marcar_registrada", "traer_de_sigrid", "a_papelera",
            "reaprobar", "restaurar")

#: R24: `borrar_linea` responde `ok: False` (no existe o ya borrada).
DESCARTE_YA_EN_PAPELERA = "la línea ya no existe o ya está en la papelera"

NOTA_SECO = "modo seco: se pasaría a borrado_sigrid (no se ha escrito)"
NOTA_MARCADA = "pasada a borrado_sigrid (F-024)"


class AmbitoNoValido(ValueError):
    """R15: el ambito no permite leer Sigrid (422)."""


def _ide_de_clave(clave: Any, prefijo: str) -> int | None:
    if not isinstance(clave, str) or not clave.startswith(prefijo):
        return None
    resto = clave[len(prefijo):]
    if not resto.isdigit() or int(resto) <= 0:
        return None
    return int(resto)


def motivo_no_sincronizable(vista: str, clave: str | None) -> str | None:
    """R15: por que no se puede sincronizar esa vista y clave, o None.

    Solo `obr-{ide}` (obra) y `rec-{R}` (persona, F-050) llevan el ide
    que sv5 necesita; `cod-`, `nom-`, `sin-obra`, `emp-`, `nom-` y
    `sin-trabajador` no."""
    if vista not in _VISTAS:
        return "vista desconocida"
    if _ide_de_clave(clave, _VISTAS[vista][1]) is None:
        return _MOTIVOS[vista]
    return None


@dataclass(frozen=True)
class Ambito:
    vista: str
    clave: str
    period: str
    mode: str
    obra_ide: int | None
    recurso_ide: int | None
    desde: int
    hasta: int


def resolver_ambito(ambito: Any) -> Ambito:
    """El ambito del navegador -> ides y periodo (`period_bounds`)."""
    if not isinstance(ambito, dict):
        raise AmbitoNoValido("falta el ambito")
    vista = ambito.get("vista")
    if vista not in _VISTAS:
        raise AmbitoNoValido("vista desconocida")
    clave = ambito.get(_VISTAS[vista][0])
    motivo = motivo_no_sincronizable(vista, clave)
    if motivo is not None:
        raise AmbitoNoValido(motivo)
    periodo = parse_period_key(ambito.get("period"))
    if periodo is None:
        raise AmbitoNoValido("periodo no valido")
    mode = normalize_mode(ambito.get("mode"))
    inicio, fin = period_bounds(*periodo, mode)
    ide = _ide_de_clave(clave, _VISTAS[vista][1])
    return Ambito(
        vista=vista, clave=clave, period=ambito["period"], mode=mode,
        obra_ide=ide if vista == "obra" else None,
        recurso_ide=ide if vista == "trabajador" else None,
        desde=int(inicio.strftime("%Y%m%d")),
        hasta=int(fin.strftime("%Y%m%d")))


def _entero(valor: Any) -> int | None:
    return None if valor is None else int(valor)


def _real(valor: Any) -> float | None:
    return None if valor is None else float(valor)


def lineas_de_sv5(resp: dict) -> list[LineaSigridSync]:
    """Las lineas de la respuesta de sv5, con sus tipos; ValueError si no
    son lo que R2 dice (nunca se compara con datos a medias)."""
    lineas = resp.get("lineas")
    if not isinstance(lineas, list):
        raise TypeError("sv5 no devolvio lineas")
    out: list[LineaSigridSync] = []
    for d in lineas:
        if not isinstance(d, dict) or d.get("origen") not in ORIGENES:
            raise ValueError("linea de sv5 sin origen valido")
        s = LineaSigridSync.desde_dict(d)
        out.append(LineaSigridSync(
            hmores_ide=int(s.hmores_ide), hmoide=_entero(s.hmoide),
            parte_cod=s.parte_cod, parte_est=_entero(s.parte_est),
            obra_ide=_entero(s.obra_ide), obra_cod=s.obra_cod,
            recurso_ide=_entero(s.recurso_ide),
            fecha_int=_entero(s.fecha_int), hora_ide=_entero(s.hora_ide),
            hora_cod=s.hora_cod, hora_ext=_entero(s.hora_ext),
            partida_ide=_entero(s.partida_ide), partida_cod=s.partida_cod,
            can=_real(s.can), tot=_real(s.tot), enlazada=bool(s.enlazada),
            origen=s.origen, registro_id=_entero(s.registro_id),
            ajuste_id=_entero(s.ajuste_id)))
    return out


@dataclass
class ResultadoSync:
    status: int
    cuerpo: dict[str, Any]


def _error(status: int, texto: str) -> ResultadoSync:
    return ResultadoSync(status, {"ok": False, "error": texto})


def _ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


class SincronizadorAmbito:
    """Orquesta una sincronizacion (§2) y sus acciones (R18) con sus
    colaboradores inyectados.

    Candado por ambito (vista + clave) en el proceso (R29): una segunda
    sincronizacion (o accion) de la misma obra o persona mientras corre la
    primera es 409, tambien con otro periodo (tocarian las mismas lineas).
    `aplicar` lo toma durante la relectura Y la escritura."""

    def __init__(self, *, repository, transfer_client, comprobacion,
                 timeout_s: float, seco: bool, lote_comprobar: int,
                 timeout_comprobar_s: float,
                 max_items_accion: int = 500,
                 reloj_utc: Callable[[], datetime] = _ahora_utc) -> None:
        self._repo = repository
        self._sv5 = transfer_client
        self._comprobacion = comprobacion
        self._timeout = float(timeout_s)
        self._seco = bool(seco)
        self._lote = int(lote_comprobar)
        self._timeout_comprobar = float(timeout_comprobar_s)
        self._max_items = int(max_items_accion)
        self._reloj_utc = reloj_utc
        self._lock = threading.Lock()
        self._en_curso: set[tuple[str, str]] = set()

    @property
    def seco(self) -> bool:
        return self._seco

    def _con_candado(self, amb: Ambito,
                     trabajo: Callable[[], ResultadoSync]) -> ResultadoSync:
        llave = (amb.vista, amb.clave)
        with self._lock:
            if llave in self._en_curso:
                return _error(409, "ya se está sincronizando este ámbito")
            self._en_curso.add(llave)
        try:
            return trabajo()
        finally:
            with self._lock:
                self._en_curso.discard(llave)

    def sincronizar(self, ambito: Any) -> ResultadoSync:
        try:
            amb = resolver_ambito(ambito)
        except AmbitoNoValido as exc:
            return _error(422, str(exc))
        return self._con_candado(amb, lambda: self._sincronizar(amb))

    def _sincronizar(self, amb: Ambito) -> ResultadoSync:
        leido = self._leer(amb)
        if isinstance(leido, ResultadoSync):
            return leido
        items, confirmadas, n_portal, n_sigrid = leido
        cuerpo = {
            "ok": True, "seco": self._seco,
            "ambito": {"vista": amb.vista, "clave": amb.clave},
            "periodo": {"period": amb.period, "mode": amb.mode,
                        "desde": amb.desde, "hasta": amb.hasta},
            "leido_at": self._reloj_utc().isoformat(),
            "recuento": resumen(items),
            "items": [item_a_dict(it) for it in items],
            ("marcaria_borrado_sigrid" if self._seco
             else "marcadas_borrado_sigrid"): confirmadas,
        }
        logger.info(
            "[sincronizar] vista=%s clave=%s period=%s mode=%s seco=%s "
            "portal=%s sigrid=%s items=%s borrado_sigrid=%s por_clase=%s",
            amb.vista, amb.clave, amb.period, amb.mode, self._seco,
            n_portal, n_sigrid, len(items), len(confirmadas),
            {c: n for c, n in cuerpo["recuento"]["por_clase"].items() if n})
        return ResultadoSync(200, cuerpo)

    def _leer(self, amb: Ambito):
        """Pasos 2-6 de §2: `(items, confirmadas, n_portal, n_sigrid)` o el
        `ResultadoSync` del error (nunca una comparacion parcial, R13)."""
        portal = self._repo.lineas_para_sincronizar(
            obra_ide=amb.obra_ide, recurso_ide=amb.recurso_ide,
            desde=amb.desde, hasta=amb.hasta)
        payload: dict[str, Any] = (
            {"obra_ide": amb.obra_ide} if amb.obra_ide is not None
            else {"recurso_ide": amb.recurso_ide})
        payload.update(desde=amb.desde, hasta=amb.hasta,
                       registro_ids=[p.registro_id for p in portal])
        try:
            resp = self._sv5.sincronizar_leer(payload,
                                              timeout_s=self._timeout)
            if not resp.get("ok"):
                return _error(502, resp.get("error")
                              or "sv5 no respondio ok")
            sigrid = lineas_de_sv5(resp)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[sincronizar] lectura de sv5 fallida: %s", exc)
            return _error(502, f"error leyendo Sigrid (sv5): {exc}")
        items = clasificar(portal, sigrid)
        huerfanas = [it for it in items if it.por_confirmar]
        confirmadas: list[int] = []
        if huerfanas:
            ids = [int(it.registro_id) for it in huerfanas]
            borradas, error = self._confirmar(ids)
            if error is not None:
                return _error(502, error)
            no_cuadran = [i for i in ids if i not in borradas]
            if no_cuadran:
                return _error(409, (
                    f"Sigrid o el portal cambiaron mientras se leia "
                    f"({len(no_cuadran)} linea(s)): vuelve a sincronizar"))
            if not self._seco:
                self._releer_portal(amb, huerfanas)
            for it in huerfanas:
                it.por_confirmar = False
                it.notas.append(NOTA_SECO if self._seco else NOTA_MARCADA)
            confirmadas = sorted(ids)
        self._poner_donde(items)
        return items, confirmadas, len(portal), len(sigrid)

    def _releer_portal(self, amb: Ambito, items: list[ItemSync]) -> None:
        """Fuera de seco, R10 acaba de pasar esas lineas a `borrado_sigrid`:
        el item lleva la linea como quedo escrita (la que vera la siguiente
        lectura), para que su firma valga en `aplicar` (R18)."""
        ahora = {p.registro_id: p for p in self._repo.lineas_para_sincronizar(
            obra_ide=amb.obra_ide, recurso_ide=amb.recurso_ide,
            desde=amb.desde, hasta=amb.hasta)}
        for it in items:
            it.portal = ahora.get(it.registro_id, it.portal)

    def _confirmar(self, ids: list[int]) -> tuple[set[int], str | None]:
        """R10: los ids que F-024 da por borrados en Sigrid.

        Fuera de seco, `comprobar_ids` (forzar, origen `sincronizar`) los
        pasa a `borrado_sigrid`. En seco (DA18) se pide a sv5 el mismo
        veredicto por lotes, sin aplicar nada."""
        if not self._seco:
            res = self._comprobacion.comprobar_ids(
                ids, origen=ORIGEN_COMPROBACION, forzar=True)
            if not res.get("ok"):
                return set(), (res.get("error")
                               or "la comprobacion en Sigrid fallo")
            return {int(i) for i in res.get("borradas_ids") or []}, None
        lineas = self._repo.registrados_para_comprobar(ids)
        borradas: set[int] = set()
        for i in range(0, len(lineas), self._lote):
            trozo = lineas[i:i + self._lote]
            resp = self._sv5.comprobar({"lineas": trozo},
                                       timeout_s=self._timeout_comprobar)
            veredictos = resp.get("veredictos") if resp.get("ok") else None
            if not isinstance(veredictos, list):
                return set(), (resp.get("error")
                               or "la comprobacion en Sigrid fallo")
            por_id = {int(v["registro_id"]): v for v in veredictos
                      if isinstance(v, dict)
                      and v.get("registro_id") is not None}
            if any(int(l["registro_id"]) not in por_id for l in trozo):
                return set(), "sv5 no dio veredicto de todas las lineas"
            borradas |= {r for r, v in por_id.items()
                         if v.get("estado") == "borrada"}
        return borradas, None

    def _poner_donde(self, items: list[ItemSync]) -> None:
        """R12: donde esta en el portal la linea de cada nuestra sin
        pareja (una synckey repetida no se mira: su linea ya caso)."""
        nuestras = [it for it in items if it.clase == "solo_sigrid_nuestra"
                    and not it.repetida and it.registro_id is not None]
        if not nuestras:
            return
        donde = self._repo.donde_estan([it.registro_id for it in nuestras])
        for it in nuestras:
            it.donde = donde.get(int(it.registro_id), "no_existe")

    # ------------------------------------------------------------------ #
    # R18-R25 · acciones hacia el portal.
    # ------------------------------------------------------------------ #

    def validar_peticion(self, accion: Any, items: Any) -> str | None:
        """R18: por que la peticion no es valida (422), o None."""
        if accion not in ACCIONES:
            return f"acción desconocida: {accion!r}"
        if not isinstance(items, list) or not items:
            return "no hay líneas seleccionadas"
        if len(items) > self._max_items:
            return (f"demasiadas líneas en una acción ({len(items)}); el "
                    f"máximo es {self._max_items}")
        vistos: set[int] = set()
        for it in items:
            rid = it.get("registro_id") if isinstance(it, dict) else None
            if (not isinstance(rid, int) or isinstance(rid, bool)
                    or rid <= 0 or not isinstance(it.get("firma"), str)):
                return "líneas no válidas: cada una con registro_id y firma"
            if rid in vistos:
                return f"la línea {rid} viene repetida"
            vistos.add(rid)
        return None

    def aplicar(self, accion: Any, ambito: Any, items: Any, *,
                actor: str | None,
                recalcular: Callable[[list[str], str | None],
                                     tuple[str, str | None]] | None = None,
                ) -> ResultadoSync:
        """R18: valida, VUELVE A SINCRONIZAR el ambito y aplica `accion`
        solo a los items cuya clase y firma siguen iguales (los demas, en
        `descartados`). Un id que no sea de ningun item del ambito
        rechaza la peticion entera (422, como F-022) sin escribir.

        No depende de `SINCRONIZAR_SECO` (DA18): es una accion explicita y
        confirmada del usuario; el seco gobierna solo la escritura
        implicita de R10, tambien en la relectura de aqui."""
        motivo = self.validar_peticion(accion, items)
        if motivo is not None:
            return _error(422, motivo)
        try:
            amb = resolver_ambito(ambito)
        except AmbitoNoValido as exc:
            return _error(422, str(exc))
        return self._con_candado(amb, lambda: self._aplicar(
            accion, amb, items, actor, recalcular))

    def _aplicar(self, accion: str, amb: Ambito, pedidos: list[dict],
                 actor: str | None, recalcular) -> ResultadoSync:
        leido = self._leer(amb)
        if isinstance(leido, ResultadoSync):
            return leido
        items = leido[0]
        por_id: dict[int, list[ItemSync]] = {}
        for it in items:
            if it.registro_id is not None:
                por_id.setdefault(int(it.registro_id), []).append(it)
        ajenos = [p["registro_id"] for p in pedidos
                  if p["registro_id"] not in por_id]
        if ajenos:
            logger.warning("[sincronizar][aplicar] %s id(s) fuera del "
                           "ambito %s", len(ajenos), amb.clave)
            return _error(422, (
                f"{len(ajenos)} línea(s) no son de este ámbito (otra obra, "
                "persona o periodo): vuelve a sincronizar"))
        vigentes: list[ItemSync] = []
        descartados: list[dict] = []
        for p in pedidos:
            rid = p["registro_id"]
            it = next((x for x in por_id[rid] if firma(x) == p["firma"]),
                      None)
            if it is None:
                descartados.append({"registro_id": rid,
                                    "motivo": DESCARTE_CAMBIO})
            elif accion not in acciones_de(it):
                descartados.append({"registro_id": rid, "motivo": (
                    f"«{accion}» no aplica a una línea «{it.clase}»")})
            else:
                vigentes.append(it)
        ahora = self._reloj_utc().isoformat()
        hecho = self._ejecutar(accion, vigentes, actor, ahora, recalcular)
        cuerpo = {"ok": True, "accion": accion, "seco": self._seco,
                  "aplicados": hecho["aplicados"],
                  "descartados": descartados + hecho["descartados"],
                  "recalculo": hecho.get("recalculo")}
        if accion == "reaprobar":
            cuerpo["abrir_aprobar"] = bool(hecho["aplicados"])
            cuerpo["incluir_borradas"] = any(
                it.clase == "borrada_en_sigrid" for it in vigentes)
        logger.info(
            "[sincronizar][aplicar] accion=%s actor=%s vista=%s clave=%s "
            "pedidos=%s aplicados=%s descartados=%s ids=%s recalculo=%s",
            accion, actor, amb.vista, amb.clave, len(pedidos),
            len(cuerpo["aplicados"]), len(cuerpo["descartados"]),
            cuerpo["aplicados"], cuerpo["recalculo"])
        return ResultadoSync(200, cuerpo)

    def _ejecutar(self, accion: str, vigentes: list[ItemSync],
                  actor: str | None, ahora: str, recalcular) -> dict:
        """La escritura de cada accion: las nuevas (R19, R20) por los
        metodos del repositorio con CAS; las de R24 por los de siempre."""
        if not vigentes:
            return {"aplicados": [], "descartados": []}
        if accion == "marcar_registrada":
            return self._repo.aplicar_marcar_registrada([{
                "registro_id": it.registro_id,
                "estado_visto": it.portal.sigrid_estado,
                "hmores_ide_visto": it.portal.sigrid_hmores_ide,
                "hmores_ide": it.sigrid.hmores_ide,
                "hmoide": it.sigrid.hmoide,
                "parte_cod": it.sigrid.parte_cod} for it in vigentes],
                actor=actor, ahora_iso=ahora)
        if accion == "traer_de_sigrid":
            return self._traer(vigentes, actor, ahora, recalcular)
        if accion == "reaprobar":     # el modal de aprobar escribe (R24)
            return {"aplicados": [it.registro_id for it in vigentes],
                    "descartados": []}
        aplicados: list[int] = []
        descartados: list[dict] = []
        for it in vigentes:
            rid = int(it.registro_id)
            try:
                if accion == "a_papelera":
                    ok = self._repo.borrar_linea(registro_id=rid,
                                                 by=actor)["ok"]
                    motivo = DESCARTE_YA_EN_PAPELERA
                else:                     # restaurar
                    ok = self._repo.restore_registro(registro_id=rid)
                    motivo = DESCARTE_NO_EXISTE
            except CongeladoError as exc:
                ok, motivo = False, str(exc)
            except DuplicadoActivoError as exc:   # F-061 R7: el 409
                ok, motivo = False, exc.motivo
            if ok:
                aplicados.append(rid)
            else:
                descartados.append({"registro_id": rid, "motivo": motivo})
        return {"aplicados": aplicados, "descartados": descartados}

    def _traer(self, vigentes: list[ItemSync], actor: str | None, ahora: str,
               recalcular) -> dict:
        """R20 y R23: horas de Sigrid (0 si se anulo alli) y UN recalculo
        compartido de los partes tocados y los de su recurso y dia."""
        res = self._repo.aplicar_traer_de_sigrid([{
            "registro_id": it.registro_id,
            "horas_vistas": it.portal.horas,
            "horas_nuevas": (0.0 if it.clase == "anulada_en_sigrid"
                             else float(it.sigrid.can or 0.0)),
            "hmores_ide_visto": it.portal.sigrid_hmores_ide}
            for it in vigentes], actor=actor, ahora_iso=ahora)
        recalculo = None
        if res["aplicados"] and recalcular is not None:
            docs = list(dict.fromkeys(
                list(res["documentos"])
                + list(self._repo.documentos_de_los_dias(res["pares"]))))
            recalculo, _pedido = recalcular(docs, actor)
        return {"aplicados": res["aplicados"],
                "descartados": res["descartados"], "recalculo": recalculo}
