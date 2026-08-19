# application/services/recurso_conciliador.py
"""Conciliacion automatica del RECURSO / parte de trabajo para TODOS los
partes (sv3). Se lanza al persistir, junto al casado de partidas.

Por cada linea de parte (de un trabajador ya conciliado contra ``emp``):
  1. Localiza su RECURSO de Sigrid (``res``): por ``emp.reside`` (ya casado),
     y si falta, por ``res.conide = empleado`` o ``res.cif = DNI``.
  2. Localiza el PARTE DE TRABAJO (``hmo``) donde se imputarian las horas:
     por ``reside + obra + ano + mes`` (la fecha del registro da ano/mes).

Resultado por registro: ``recurso_ide`` / ``recurso_cif`` / ``hmo_ide`` /
``parte_estado`` (``ok`` = hay parte; ``sin_parte`` = recurso si pero sin
parte de ese mes/obra; ``sin_recurso`` = no se localizo el recurso).

NO escribe en Sigrid. Best-effort: si Sigrid falla para una obra, esos
registros NO se tocan (se reintentan en la siguiente persistencia).
"""
from __future__ import annotations

import logging
import re
import threading
import time
from collections import defaultdict
from datetime import date
from typing import Callable, Mapping

from application.services import text_match as tm
from application.services.jornada_resolver import (
    DetalleJornada,
    Excepcion,
    detalle_jornada_dia,
    jornada_efectiva,
    jornada_semanal_de,
)
from domain.models.sigrid_models import HmoRow, RecursoRow
from domain.ports.calendario_laboral_port import CalendarioLaboralPort
from domain.ports.jornada_empleado_port import (
    JornadaEmpleadoPort,
    JornadaEmpleadoRow,
)

logger = logging.getLogger(__name__)

#: Mapa candef -> jornada semanal por defecto (F-015). El de verdad llega
#: del cableado (`JORNADA_SEMANAL_POR_CANDEF`, espejo del de sv4); este
#: existe para que los conciliadores construidos sin el —todos los tests
#: anteriores a F-015— sigan calculando exactamente lo de siempre.
MAPA_SEMANAL_POR_DEFECTO: dict[float, float] = {8.0: 40.0, 9.0: 42.0}


def _ano_mes(fecha_int: int | None) -> tuple[int | None, int | None]:
    if not fecha_int:
        return None, None
    return fecha_int // 10000, (fecha_int // 100) % 100


_INCID_TIPOS = {"V", "B", "AT", "FJ", "F", "H", "M"}


def _tipo_inc(res: str | None) -> str | None:
    """Tipo de incidencia (V|B|AT|FJ|F|H|M) leido del parentesis final de la
    descripcion de un codigo de hora, p.ej. 'Vacaciones(V)' -> 'V',
    'Accidente/Enf. Profesional(AT)' -> 'AT'. None si no es una incidencia."""
    if not res:
        return None
    m = re.search(r"\(([A-Za-z]{1,3})\)\s*$", res)
    if not m:
        return None
    t = m.group(1).strip().upper()
    return t if t in _INCID_TIPOS else None


def _tipo(reg: dict) -> str:
    return (reg.get("tipo_hora") or "").strip().lower()


#: Estados de `sigrid_estado` que significan "esto ya viajo al ERP" (F-004).
ESTADOS_CONGELADOS: frozenset[str] = frozenset({"encolado", "registrado"})


def esta_congelado(sigrid_estado: str | None, doc_approved: object) -> bool:
    """True si esa linea NO se puede recalcular (F-004; F-015 R31/R32).

    Misma regla que el portal: linea encolada o registrada en Sigrid, o
    parte aprobado. Escrita UNA vez para que el conciliador y el
    repositorio no puedan discrepar: si uno congelase y el otro no, la
    reversion borraria lo que el calculo da por bueno.
    """
    if bool(doc_approved):
        return True
    return (sigrid_estado or "").strip().lower() in ESTADOS_CONGELADOS


def _congelado(reg: dict) -> bool:
    """`esta_congelado` sobre un registro tal como lo trae el repositorio."""
    return esta_congelado(reg.get("sigrid_estado"), reg.get("doc_approved"))


def _upd(registro_id, recurso_ide, recurso_cif, hmo_ide, estado) -> dict:
    return {
        "registro_id": registro_id, "recurso_ide": recurso_ide,
        "recurso_cif": recurso_cif, "hmo_ide": hmo_ide,
        "parte_estado": estado,
    }


class RecursoConciliador:
    def __init__(
        self,
        *,
        repository,
        lookup,
        calendario: CalendarioLaboralPort | None = None,
        jornada_ordinaria_horas: float = 8.0,
        candef_minimo: float = 2.0,
        ttl_seconds: int = 600,
        mapa_semanal: Mapping[float, float] | None = None,
        jornadas: JornadaEmpleadoPort | None = None,
        jornada_cache_ttl_s: int = 600,
    ) -> None:
        # repository: SqlAlchemyParteRepository. lookup: SigridLookupPort
        # (fetch_recursos, fetch_reshor, fetch_hmo_obra).
        self._repository = repository
        self._lookup = lookup
        # Calendario laboral (fin de semana + festivos). Si es None, no
        # se aplica la regla de no laborable (comportamiento anterior).
        self._calendario = calendario
        # Jornada ordinaria por defecto cuando el recurso no informa el
        # CanDefecto (candef vacio): se resta esta cantidad y el resto va
        # a extra.
        self._jornada = float(jornada_ordinaria_horas)
        # CanDefecto <= a este umbral se trata como no informado y se usa
        # la jornada por defecto (evita que un 0/1/2 mande todo a extra).
        self._candef_min = float(candef_minimo)
        self._ttl = int(ttl_seconds)
        self._lock = threading.RLock()
        # maestro de recursos: maps conide->ide, cif_norm->ide, ide->RecursoRow
        # (para la clasificacion/categoria y la hora por defecto) + timestamp.
        self._res_maps: tuple[
            float, dict[int, int], dict[str, int], dict[int, RecursoRow]
        ] | None = None
        # costes de horas por recurso: reside -> {ord, ext, candef} (+ ts).
        self._reshor_cache: tuple[float, dict[int, dict]] | None = None
        # hmo por obra: obra_ide -> (timestamp, {(reside,ano,mes): hmo_ide})
        self._hmo_cache: dict[int, tuple[float, dict[tuple, int]]] = {}
        # F-003 (R26): partes cuyo computo se hizo con calendario degradado
        # en la pasada EN CURSO. `conciliar_todos` lo vacia al empezar.
        self._docs_degradados: set[str] = set()
        # F-015: mapa candef -> jornada semanal (`JORNADA_SEMANAL_POR_CANDEF`)
        # y excepciones por trabajador (`empleado_jornada`). Los dos son
        # opcionales: sin ellos, la jornada del dia es el candef efectivo de
        # siempre.
        self._mapa_semanal: Mapping[float, float] = dict(
            MAPA_SEMANAL_POR_DEFECTO if mapa_semanal is None else mapa_semanal
        )
        self._jornadas = jornadas
        self._jornada_ttl = int(jornada_cache_ttl_s)
        # (timestamp, {dni_norm: [filas ordenadas por 'desde' descendente]}).
        self._jornadas_cache: tuple[
            float, dict[str, list[JornadaEmpleadoRow]]
        ] | None = None
        # Avisos de la pasada EN CURSO, que `conciliar_todos` vacia igual que
        # `_docs_degradados`: recursos con el candef fuera del mapa (R10) y si
        # ya se aviso de que `empleado_jornada` no se pudo leer (R17).
        self._avisados_mapa: set[int] = set()
        self._aviso_jornadas_fallo = False

    # ----- recursos (maestro) ----- #
    def _recurso_maps(
        self,
    ) -> tuple[dict[int, int], dict[str, int], dict[int, RecursoRow]]:
        now = time.time()
        with self._lock:
            if self._res_maps is not None and (now - self._res_maps[0]) < self._ttl:
                return self._res_maps[1], self._res_maps[2], self._res_maps[3]
        try:
            recursos: list[RecursoRow] = self._lookup.fetch_recursos()
        except Exception as exc:  # noqa: BLE001
            logger.warning("[recurso-concil] fallo leyendo recursos: %r", exc)
            return {}, {}, {}   # fallback: solo emp.reside
        by_conide: dict[int, int] = {}
        by_cif: dict[str, int] = {}
        by_ide: dict[int, RecursoRow] = {}
        for r in recursos:
            by_ide[r.ide] = r
            if r.conide is not None:
                by_conide.setdefault(r.conide, r.ide)
            cifn = tm.normalize_dni(r.cif)
            if cifn:
                by_cif.setdefault(cifn, r.ide)
        with self._lock:
            self._res_maps = (now, by_conide, by_cif, by_ide)
        logger.info(
            "[recurso-concil] recursos: por_empleado=%s por_dni=%s total=%s",
            len(by_conide), len(by_cif), len(by_ide),
        )
        return by_conide, by_cif, by_ide

    # ----- costes de horas por recurso (reshor) ----- #
    def _reshor_index(self, by_ide: dict[int, RecursoRow]) -> dict[int, dict]:
        """reside -> {'ord': ReshorRow|None, 'ext': ReshorRow|None,
        'candef': float|None}. ``ord`` es la hora LABORABLE (la hora por
        defecto del recurso, ``res.horide``; si falta, la primera ext=0);
        ``ext`` la primera hora extra; ``candef`` la cantidad por defecto de
        la hora laborable (jornada por defecto)."""
        now = time.time()
        with self._lock:
            if self._reshor_cache is not None and (
                now - self._reshor_cache[0]
            ) < self._ttl:
                return self._reshor_cache[1]
        try:
            filas = self._lookup.fetch_reshor()
        except Exception as exc:  # noqa: BLE001
            logger.warning("[recurso-concil] fallo leyendo reshor: %r", exc)
            return {}   # sin reshor: no se pisa la hora (solo categoria)
        por_reside: dict[int, list] = defaultdict(list)
        for f in filas:
            por_reside[f.reside].append(f)
        idx: dict[int, dict] = {}
        for reside, lst in por_reside.items():
            rec = by_ide.get(reside)
            horide_def = rec.horide_def if rec is not None else None
            # Separar el grupo del recurso en INCIDENCIAS (por el (TIPO) de la
            # descripcion) y horas de TRABAJO (el resto; los codigos de
            # incidencia CIx que no mapean a un tipo de parte, p.ej. CIZ, se
            # descartan).
            incidencias: dict[str, object] = {}
            trabajo: list = []
            for f in lst:
                t = _tipo_inc(f.res)
                cod = (f.cod or "").upper()
                if t:
                    incidencias.setdefault(t, f)
                elif cod.startswith("CI"):
                    continue
                else:
                    trabajo.append(f)
            # Ordinaria: hora por defecto del recurso; si falta, la primera
            # no-extra; si no, la primera de trabajo.
            ordinaria = None
            if horide_def is not None:
                ordinaria = next(
                    (f for f in trabajo if f.horide == horide_def), None
                )
            if ordinaria is None:
                ordinaria = next((f for f in trabajo if f.ext == 0), None)
            if ordinaria is None and trabajo:
                ordinaria = trabajo[0]
            # Extra: por el flag ext=1; si el flag no la marca (Sigrid no
            # siempre lo informa), por la palabra "extra" en la descripcion;
            # como ultimo recurso, la hora de trabajo distinta de la ordinaria.
            extra = next((f for f in trabajo if f.ext == 1), None)
            if extra is None:
                extra = next(
                    (f for f in trabajo
                     if "extra" in tm.normalize(f.res or "")), None
                )
            if extra is None and ordinaria is not None:
                extra = next(
                    (f for f in trabajo if f.horide != ordinaria.horide), None
                )
            idx[reside] = {
                "ord": ordinaria,
                "ext": extra,
                "candef": ordinaria.candef if ordinaria is not None else None,
                "incidencias": incidencias,
            }
        with self._lock:
            self._reshor_cache = (now, idx)
        logger.info("[recurso-concil] reshor: %s recursos con horas", len(idx))
        return idx

    # ----- pisado de categoria + codigo de hora desde el recurso ----- #
    def _overwrite(
        self,
        reg: dict,
        ride: int,
        by_ide: dict[int, RecursoRow],
        reshor_idx: dict[int, dict],
    ) -> dict:
        """Campos que el RECURSO impone sobre el registro al casar: categoria
        (clasificacion del recurso), codigo de hora (su hora laborable/extra)
        y la jornada por defecto (candef). Devuelve solo las claves a pisar;
        las incidencias NO pisan la hora (D2). Emite warning si el codigo de
        hora impuesto difiere del que ya tenia el registro."""
        out: dict = {}
        rec = by_ide.get(ride)
        if rec is not None and rec.restip_res:
            out["categoria"] = rec.restip_res
        hsel = reshor_idx.get(ride)
        if not hsel:
            return out
        if hsel.get("candef") is not None:
            out["hora_candef"] = hsel["candef"]
        ord_row = hsel.get("ord")
        if ord_row is not None and ord_row.pre is not None:
            out["recurso_precio_hora"] = ord_row.pre
        tipo = (reg.get("tipo_hora") or "").strip().lower()
        if tipo not in ("", "normal", "extra"):
            # Incidencia (V|B|AT|FJ|F|H|M): coge SU codigo del grupo del
            # recurso (reshor), nunca la ordinaria. Si el recurso no tiene ese
            # codigo de incidencia, no se pisa (se mantiene el resuelto).
            hora = (hsel.get("incidencias") or {}).get(tipo.upper())
        elif tipo == "extra":
            hora = hsel.get("ext") or hsel.get("ord")  # D3: sin extra -> normal
        else:
            hora = hsel.get("ord")
        if hora is None:
            return out
        prev_ide = reg.get("hora_ide")
        if prev_ide is not None and prev_ide != hora.horide:
            logger.warning(
                "[recurso-concil] DIFERENCIA codigo de hora en registro=%s "
                "recurso=%s: previo=%s/%s -> recurso=%s/%s "
                "(categoria leida=%r recurso=%r)",
                reg.get("registro_id"), ride, prev_ide, reg.get("hora_codigo"),
                hora.horide, hora.cod, reg.get("categoria"),
                out.get("categoria"),
            )
            metodo = "recurso_difiere"
        else:
            metodo = "recurso"
        out["hora_ide"] = hora.horide
        out["hora_codigo"] = hora.cod
        out["hora_descripcion"] = hora.res
        out["hora_ext"] = hora.ext
        out["hora_match_method"] = metodo
        return out


    # ----- hmo por obra ----- #
    def _hmo_index(self, obra_ide: int) -> dict[tuple, int] | None:
        now = time.time()
        with self._lock:
            hit = self._hmo_cache.get(obra_ide)
            if hit is not None and (now - hit[0]) < self._ttl:
                return hit[1]
        try:
            filas: list[HmoRow] = self._lookup.fetch_hmo_obra(obra_ide)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[recurso-concil] fallo leyendo hmo obra=%s: %r", obra_ide, exc
            )
            return None
        idx: dict[tuple, int] = {}
        for h in filas:
            if h.reside is None or h.ano is None or h.mes is None:
                continue
            idx.setdefault((h.reside, h.ano, h.mes), h.ide)
        with self._lock:
            self._hmo_cache[obra_ide] = (now, idx)
        logger.info(
            "[recurso-concil] obra=%s hmo=%s partes indexados", obra_ide, len(idx)
        )
        return idx

    def _resuelve_recurso(
        self, reg: dict, by_conide: dict[int, int], by_cif: dict[str, int]
    ) -> int | None:
        reside = reg.get("empleado_reside")
        if reside:
            return reside
        emp_ide = reg.get("empleado_ide")
        if emp_ide is not None and emp_ide in by_conide:
            return by_conide[emp_ide]
        dni = tm.normalize_dni(reg.get("empleado_dni"))
        if dni and dni in by_cif:
            return by_cif[dni]
        return None

    def conciliar_todos(self) -> dict:
        # Idempotencia: revertir las extras por jornada de pasadas anteriores
        # (restaurar horas originales y borrar los extra auto) para recalcular
        # el dia completo desde el estado original del parte.
        self._repository.revert_extras_auto()
        # Las marcas son de ESTE calculo, no un residuo del anterior.
        self._docs_degradados = set()
        self._avisados_mapa = set()
        self._aviso_jornadas_fallo = False
        self._jornadas_cache = None

        registros = self._repository.fetch_registros_para_recurso()
        by_conide, by_cif, by_ide = self._recurso_maps()
        reshor_idx = self._reshor_index(by_ide)

        por_obra: dict[int | None, list[dict]] = defaultdict(list)
        for r in registros:
            por_obra[r.get("obra_ide")].append(r)

        ride_por_reg: dict[int, int] = {}
        updates: list[dict] = []
        con_parte = 0
        pisados = 0
        for obra_ide, regs in por_obra.items():
            if not obra_ide:
                # Sin obra casada: no se puede localizar el parte, pero si el
                # recurso se resuelve igualmente se pisa categoria/hora.
                for r in regs:
                    ride = self._resuelve_recurso(r, by_conide, by_cif)
                    estado = "sin_parte" if ride else "sin_recurso"
                    u = _upd(r["registro_id"], ride, r.get("empleado_dni"),
                             None, estado)
                    if ride:
                        ride_por_reg[r["registro_id"]] = ride
                        ov = self._overwrite(r, ride, by_ide, reshor_idx)
                        if ov:
                            pisados += 1
                        u.update(ov)
                    updates.append(u)
                continue
            idx = self._hmo_index(obra_ide)
            if idx is None:
                continue  # Sigrid fallo: no tocar, se reintenta luego
            for r in regs:
                ride = self._resuelve_recurso(r, by_conide, by_cif)
                if not ride:
                    updates.append(
                        _upd(r["registro_id"], None, r.get("empleado_dni"),
                             None, "sin_recurso")
                    )
                    continue
                ride_por_reg[r["registro_id"]] = ride
                ano, mes = _ano_mes(r.get("fecha_int"))
                hmo_ide = idx.get((ride, ano, mes)) if ano and mes else None
                if hmo_ide:
                    con_parte += 1
                    estado = "ok"
                else:
                    estado = "sin_parte"
                u = _upd(r["registro_id"], ride, r.get("empleado_dni"),
                         hmo_ide, estado)
                ov = self._overwrite(r, ride, by_ide, reshor_idx)
                if ov:
                    pisados += 1
                u.update(ov)
                updates.append(u)

        actualizados = self._repository.apply_recurso_matches(updates)

        # Segunda pasada: pasar a extra el exceso de horas ORDINARIAS sobre
        # la JORNADA DEL DIA, por (recurso, dia) across obras.
        splits = self._reclasificar_extras_jornada(
            registros, ride_por_reg, reshor_idx
        )
        reclasificadas = self._repository.apply_extras_splits(splits)
        a_revisar = self._marcar_partes_degradados()
        logger.info(
            "[recurso-concil] registros=%s actualizados=%s con_parte=%s "
            "pisados=%s extras_reclasificadas=%s partes_a_revisar=%s",
            len(registros), actualizados, con_parte, pisados, reclasificadas,
            a_revisar,
        )
        return {
            "registros": len(registros),
            "actualizados": actualizados,
            "con_parte": con_parte,
            "pisados": pisados,
            "extras_reclasificadas": reclasificadas,
            "partes_a_revisar": a_revisar,
        }

    def _marcar_partes_degradados(self) -> int:
        """R26: los partes calculados a ciegas quedan para revisar.

        sv3 no puede bloquear nada (es un worker de cola y la
        persistencia es best-effort), pero un festivo mal resuelto en
        silencio cambia el reparto ordinaria/extra: al menos que se sepa.
        """
        docs = sorted(getattr(self, "_docs_degradados", set()))
        if not docs:
            return 0
        marcar = getattr(self._repository, "marcar_review_required", None)
        if marcar is None:
            logger.warning(
                "[recurso-concil] %s parte(s) calculados con el calendario "
                "degradado, pero el repositorio no sabe marcarlos.", len(docs),
            )
            return 0
        logger.warning(
            "[recurso-concil] calendario DEGRADADO en %s parte(s): se marcan "
            "para revision (%s).", len(docs), ", ".join(docs[:10]),
        )
        try:
            marcar(docs)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[recurso-concil] no se pudieron marcar los partes para "
                "revision: %r", exc,
            )
            return 0
        return len(docs)

    # ----- exceso de jornada -> extra (por recurso y dia, across obras) ----- #
    def _reclasificar_extras_jornada(
        self,
        registros: list[dict],
        ride_por_reg: dict[int, int],
        reshor_idx: dict[int, dict],
    ) -> list[dict]:
        """Normaliza el desglose ordinaria/extra por (recurso, dia) reuniendo
        TODAS las obras. Regla en DIA LABORABLE: se suman las horas normales
        Y las extras del dia y se comparan con la JORNADA DEL DIA (F-015);
        las ordinarias finales son esa jornada y la extra es LA RESTA
        (total - jornada), que puede salir NEGATIVA (viernes tipico: trabaja
        6 con jornada 8 -> ordinaria 8, extra -2).

        La jornada del dia ya NO es plana: es el CanDefecto efectivo salvo
        el ULTIMO dia laborable de la semana del trabajador, que recibe el
        resto de la jornada semanal (`max(0, S - 4c)`). Con candef 8 y
        S 40 el resto vale 8 y no cambia nada respecto a antes de F-015.

        - Si falta extra (total > candef + extras explicitas): se recorta lo
          ordinario a extra empezando por los registros de mayor id, como
          siempre.
        - Si sobra (extra negativa o extras explicitas por encima de la
          resta): se SUBE el registro ordinario de mayor id hasta cuadrar la
          jornada y se crea UNA extra automatica con horas NEGATIVAS (las
          extras explicitas del parte no se tocan; el neto queda correcto).
        - Dias laborables SIN horas ordinarias (solo extras explicitas o
          incidencias) no se normalizan: se respeta el desglose del parte.
        - Fin de semana / festivo: sin jornada ordinaria, TODO lo ordinario
          pasa a extra (igual que antes).
        - RECURSO SIN CODIGO DE HORA EXTRA (p.ej. mensuales tipo encargado):
          NO se normaliza nada. Se respetan las horas del parte tal cual
          (ordinarias y extras) y se emite un WARNING: esas extras no tienen
          codigo de hora extra en Sigrid, por lo que al traspasarlas se
          quedaran a CERO.

        Solo calcula los 'splits'; la BD la toca el repositorio (que antes
        revierte las extras automaticas previas, asi el calculo parte siempre
        del desglose original del parte)."""
        grupos: dict[tuple[int, int | None], list[dict]] = defaultdict(list)
        for r in registros:
            ride = ride_por_reg.get(r["registro_id"])
            if ride is None:
                continue
            grupos[(ride, r.get("fecha_int"))].append(r)

        splits: list[dict] = []
        for (ride, fecha_int), regs in grupos.items():
            hsel = reshor_idx.get(ride)
            if not hsel:
                continue
            hora_ext = hsel.get("ext")
            if hora_ext is None:
                # Recurso SIN codigo de hora extra en Sigrid (p.ej. mensuales
                # tipo encargado, codigo MENC): NO se calcula nada, se dejan
                # las horas del parte tal cual (ordinarias y extras). Aviso de
                # que esas extras se quedaran a CERO al traspasarlas, por no
                # existir un codigo de hora extra al que imputarlas.
                horas_extra_dia = sum(
                    (x.get("horas") or 0.0)
                    for x in regs if _tipo(x) == "extra"
                )
                if abs(horas_extra_dia) > 1e-9:
                    logger.warning(
                        "[recurso-concil] recurso=%s dia=%s SIN codigo de "
                        "hora extra: se respetan las horas del parte, pero "
                        "las %.2f h extra se traspasaran a CERO.",
                        ride, self._fecha_int_to_iso(fecha_int),
                        horas_extra_dia,
                    )
                continue

            # CanDefecto real del recurso (lo que dice Sigrid; puede ser
            # None/0/2...). Se PERSISTE tal cual para diagnostico; el
            # calculo usa el "efectivo".
            candef_real = hsel.get("candef")
            # CONGELADOS (F-015, R32): las lineas que ya viajaron a Sigrid
            # SUMAN en el total del dia —si no, un dia mixto le regalaria
            # al trabajador una segunda jornada— pero no son candidatas ni
            # a recorte ni a pivote.
            todas_ordinarias = [x for x in regs if _tipo(x) in ("", "normal")]
            ordinarios = [x for x in todas_ordinarias if not _congelado(x)]
            total_ord = sum((x.get("horas") or 0.0) for x in todas_ordinarias)
            total_ext = sum(
                (x.get("horas") or 0.0) for x in regs if _tipo(x) == "extra"
            )

            marca = ""
            if self._es_no_laborable(fecha_int, regs):
                # Fin de semana / festivo: NO hay jornada ordinaria, TODO
                # el trabajo ordinario pasa a extra (las extras explicitas
                # ya lo son).
                delta = total_ord
                if delta <= 1e-9:
                    continue
                logger.info(
                    "[recurso-concil] dia NO laborable %s (recurso=%s): "
                    "horas ordinarias -> extra.",
                    self._fecha_int_to_iso(fecha_int), ride,
                )
            else:
                # DIA LABORABLE: normales + extras comparadas con la jornada
                # DEL DIA. extra objetivo = total - jornada (puede ser
                # NEGATIVA). Sin ordinarias no se normaliza.
                if total_ord <= 1e-9:
                    continue
                # JORNADA DEL DIA (F-015). Sigue partiendo del CanDefecto
                # efectivo de F-003 —un 0/1/2 de Sigrid no puede mandar el
                # dia entero a extra—, pero ya no es plano: el ULTIMO dia
                # laborable de la semana recibe el resto de la jornada
                # semanal. El dia ya se sabe laborable, asi que se le pasa
                # al resolutor esa respuesta hecha para no preguntarla dos
                # veces al calendario.
                memo: dict[str, bool] = {}
                iso_dia = self._fecha_int_to_iso(fecha_int)
                if iso_dia is not None:
                    memo[iso_dia] = True
                detalle = self._detalle_jornada(
                    fecha_int, regs, candef_real, memo
                )
                self._avisar_candef_fuera_del_mapa(ride, detalle, candef_real)
                marca = self._marca_jornada(detalle)
                total = total_ord + total_ext
                objetivo_extra = total - detalle.horas
                # Lo que falta (o sobra) respecto a las extras explicitas.
                delta = objetivo_extra - total_ext
                if abs(delta) <= 1e-9:
                    continue

            orden = sorted(
                ordinarios, key=lambda z: z["registro_id"], reverse=True
            )
            # R32: si el dia no cuadra sin tocar una linea congelada, no se
            # genera NADA y se avisa. Ajustar la mitad seria peor: dejaria
            # el dia con un total distinto del que firmo el encargado.
            disponible = sum(max(0.0, x.get("horas") or 0.0) for x in orden)
            if (delta > 0 and disponible + 1e-9 < delta) or (
                delta < 0 and not orden
            ):
                logger.warning(
                    "[recurso-concil] dia %s (recurso=%s) NO se puede cuadrar "
                    "sin tocar lineas CONGELADAS (ya en Sigrid o parte "
                    "aprobado): faltan %.2f h ajustables y hay %.2f. No se "
                    "genera ningun split.",
                    self._fecha_int_to_iso(fecha_int), ride, abs(delta),
                    disponible,
                )
                continue
            if delta > 0:
                # Falta extra: recortar ordinarias empezando por las ultimas
                # horas del dia (registros creados despues = id mayor).
                restante = delta
                for x in orden:
                    if restante <= 1e-9:
                        break
                    h = x.get("horas") or 0.0
                    if h <= 0:
                        continue
                    porcion = h if h <= restante + 1e-9 else restante
                    splits.append({
                        "normal_id": x["registro_id"],
                        "horas_norm": round(h - porcion, 2),
                        "horas_orig": h,
                        "extra_horas": round(porcion, 2),
                        "hora_ext_ide": hora_ext.horide,
                        "hora_ext_cod": hora_ext.cod,
                        "hora_ext_desc": hora_ext.res,
                        "hora_ext_ext": hora_ext.ext,
                        "hora_candef": candef_real,
                    })
                    restante -= porcion
                if marca:
                    logger.info(
                        "[recurso-concil] recorte a extra %s (recurso=%s): "
                        "%.2f h.%s",
                        self._fecha_int_to_iso(fecha_int), ride, delta, marca,
                    )
            else:
                # Sobra: jornada incompleta (o extras explicitas por encima
                # de la resta). Se sube el ordinario de mayor id hasta
                # completar la jornada y se crea UNA extra NEGATIVA por la
                # diferencia; el total del dia se conserva.
                pivote = orden[0]
                h = pivote.get("horas") or 0.0
                splits.append({
                    "normal_id": pivote["registro_id"],
                    "horas_norm": round(h - delta, 2),   # delta<0 -> sube
                    "horas_orig": h,
                    "extra_horas": round(delta, 2),      # negativa
                    "hora_ext_ide": hora_ext.horide,
                    "hora_ext_cod": hora_ext.cod,
                    "hora_ext_desc": hora_ext.res,
                    "hora_ext_ext": hora_ext.ext,
                    "hora_candef": candef_real,
                })
                logger.info(
                    "[recurso-concil] jornada incompleta %s (recurso=%s): "
                    "ordinaria %+.2f, extra %.2f.%s",
                    self._fecha_int_to_iso(fecha_int), ride, -delta, delta,
                    marca,
                )
        return splits

    # ----- avisos y trazabilidad de la jornada del dia (F-015) ----- #
    def _avisar_candef_fuera_del_mapa(
        self, ride: int, detalle: DetalleJornada, candef_real
    ) -> None:
        """R10: un candef valido que el mapa no conoce cae a jornada PLANA.

        No es un error —el resultado es exactamente el de antes de F-015—,
        pero significa que hay un regimen sin mapear. Un aviso por recurso
        y pasada; uno por registro llenaria el log.
        """
        if detalle.origen != "plana" or ride in self._avisados_mapa:
            return
        self._avisados_mapa.add(ride)
        logger.warning(
            "[recurso-concil] recurso=%s con candef=%s fuera del mapa "
            "JORNADA_SEMANAL_POR_CANDEF: se aplica jornada plana "
            "(%.2f h/dia, %.2f h/semana). Si ese regimen tiene otra jornada "
            "semanal, anadelo al mapa.",
            ride, candef_real, detalle.candef_efectivo, detalle.semanal,
        )

    @staticmethod
    def _marca_jornada(detalle: DetalleJornada) -> str:
        """R28: traza de POR QUE la jornada de ese dia no fue el candef.

        Cadena vacia cuando la jornada del dia ES el candef efectivo, que
        es el caso normal (candef 8): un log que repite lo obvio en cada
        linea de cada parte no lo lee nadie.
        """
        if abs(detalle.horas - detalle.candef_efectivo) <= 1e-9:
            return ""
        return (
            f" jornada_dia={detalle.horas:.2f} "
            f"(semanal={detalle.semanal:.2f}, origen={detalle.origen}, "
            f"ultimo_laborable={'si' if detalle.ultimo_laborable else 'no'})"
        )

    # ----- jornada del dia (F-015) ----- #
    @staticmethod
    def _dni_grupo(regs: list[dict]) -> str | None:
        """El DNI del grupo: el primer `empleado_dni` no vacio.

        Mismo criterio que `_es_no_laborable` desde F-003, para que el
        calendario y la excepcion se resuelvan con el MISMO trabajador
        que decide si el dia es festivo.
        """
        for r in regs:
            dni = (r.get("empleado_dni") or "").strip()
            if dni:
                return dni
        return None

    def _es_laborable_para(
        self, dni: str | None, regs: list[dict], memo: dict[str, bool]
    ) -> Callable[[date], bool]:
        """`es_laborable(date) -> bool` del trabajador, para el resolutor.

        Envuelve el puerto con el MISMO `try/except` que `_es_no_laborable`
        (si el calendario falla, el dia se trata como laborable, que es el
        comportamiento de siempre) y recoge la senal de degradacion: si el
        dia que decide el ultimo laborable se resolvio a ciegas, el parte
        acaba marcado para revision igual que hoy (R23).

        Sin calendario cableado, todo dia es laborable (D11) y el ultimo
        laborable de la semana acaba siendo el viernes. `memo` evita
        preguntar dos veces por la misma fecha dentro del mismo grupo.
        """
        def _es_laborable(d: date) -> bool:
            iso = d.isoformat()
            if iso in memo:
                return memo[iso]
            if self._calendario is None:
                memo[iso] = True
                return True
            try:
                valor = not bool(self._calendario.es_no_laborable(iso, dni=dni))
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "[recurso-concil] calendario laboral fallo en %s: %r",
                    iso, exc,
                )
                valor = True
            else:
                self._recoger_degradacion(regs)
            memo[iso] = valor
            return valor

        return _es_laborable

    def _jornadas_index(self) -> dict[str, list[JornadaEmpleadoRow]]:
        """Toda `empleado_jornada` indexada por DNI, con cache TTL.

        Se lee entera una vez por pasada (DA8): son unidades de filas y un
        `SELECT` por trabajador y dia seria una consulta por celda. Si la
        lectura falla, se cachea el vacio para no reintentar en bucle y se
        avisa UNA vez (R17): la excepcion de jornada es un accesorio, no
        puede tumbar la conciliacion de un parte.
        """
        now = time.time()
        with self._lock:
            if (self._jornadas_cache is not None
                    and (now - self._jornadas_cache[0]) < self._jornada_ttl):
                return self._jornadas_cache[1]
        try:
            filas = self._jornadas.fetch_jornadas()  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001
            if not self._aviso_jornadas_fallo:
                self._aviso_jornadas_fallo = True
                logger.warning(
                    "[recurso-concil] no se pudo leer empleado_jornada (%r): "
                    "se sigue con la jornada derivada del candef.", exc,
                )
            filas = []
        indice: dict[str, list[JornadaEmpleadoRow]] = defaultdict(list)
        ignoradas = 0
        for fila in filas:
            clave = tm.normalize_dni(fila.dni_norm)
            if not clave:
                ignoradas += 1
                continue
            if not Excepcion(
                semanal=fila.jornada_semanal, patron=fila.patron,
                origen=fila.origen,
            ).valida():
                # Hasta F-016 las filas las carga el humano por SQL: una
                # mal formada se IGNORA en vez de repartir horas raras.
                ignoradas += 1
                continue
            indice[clave].append(fila)
        if ignoradas:
            logger.warning(
                "[recurso-concil] %s fila(s) de empleado_jornada ignoradas "
                "por venir mal formadas (sin DNI, patron incompleto u horas "
                "fuera de rango).", ignoradas,
            )
        # Vigencia mas reciente primero: si dos filas solapan (F-016 lo
        # impedira; hasta entonces las carga el humano a mano), gana la de
        # `desde` mayor, que es la que alguien anadio despues.
        for lista in indice.values():
            lista.sort(key=lambda f: (f.desde or ""), reverse=True)
        plano = dict(indice)
        with self._lock:
            self._jornadas_cache = (now, plano)
        return plano

    def _excepcion_para(
        self, dni: str | None, fecha_iso: str | None
    ) -> Excepcion | None:
        """Excepcion vigente de ese trabajador ese dia, o `None`.

        Vigencia `desde <= fecha < hasta` (`hasta` nulo = abierta). Sin
        puerto cableado, sin DNI o sin fecha no se consulta nada.
        """
        if self._jornadas is None or not fecha_iso:
            return None
        clave = tm.normalize_dni(dni)
        if not clave:
            return None
        for fila in self._jornadas_index().get(clave, ()):
            if fila.desde and fecha_iso < fila.desde:
                continue
            if fila.hasta and fecha_iso >= fila.hasta:
                continue
            return Excepcion(
                semanal=fila.jornada_semanal, patron=fila.patron,
                origen=fila.origen,
            )
        return None

    def _detalle_jornada(
        self,
        fecha_int: int | None,
        regs: list[dict],
        candef_real: float | None,
        memo: dict[str, bool] | None = None,
    ) -> DetalleJornada:
        """Jornada teorica del (recurso, dia) con su explicacion.

        Es el punto donde F-015 sustituye al `candef` plano: mismo candef
        efectivo de F-003, pero repartido en la semana segun el calendario
        del trabajador y su posible excepcion.
        """
        iso = self._fecha_int_to_iso(fecha_int)
        dni = self._dni_grupo(regs)
        if iso is None:
            # Sin fecha utilizable no hay semana que mirar: la jornada del
            # dia es el candef efectivo, que es lo que hacia sv3 antes de
            # F-015. La jornada SEMANAL se informa igual (sale del mapa, no
            # de la fecha) para que el log y el KPI no mientan.
            candef_efectivo = jornada_efectiva(
                candef_real, minimo=self._candef_min, por_defecto=self._jornada,
            )
            semanal, origen = jornada_semanal_de(
                candef_efectivo, mapa=self._mapa_semanal
            )
            return DetalleJornada(
                horas=candef_efectivo, candef_efectivo=candef_efectivo,
                semanal=semanal, origen=origen, ultimo_laborable=False,
            )
        return detalle_jornada_dia(
            date.fromisoformat(iso),
            candef=candef_real,
            minimo=self._candef_min,
            por_defecto=self._jornada,
            mapa=self._mapa_semanal,
            es_laborable=self._es_laborable_para(
                dni, regs, {} if memo is None else memo
            ),
            excepcion=self._excepcion_para(dni, iso),
        )

    # ----- calendario laboral (fin de semana / festivos) ----- #
    def _es_no_laborable(
        self, fecha_int: int | None, regs: list[dict]
    ) -> bool:
        """True si el dia es fin de semana o festivo segun el calendario.
        Sin calendario cableado o sin fecha valida, devuelve False.

        Ademas recoge la senal de degradacion del adaptador (F-003, R26):
        si la resolucion no salio de Sesame, los partes de este grupo
        quedan apuntados para marcarlos al final de la pasada. La senal
        se descubre por duck-typing: no forma parte del puerto y
        `JsonCalendarioLaboral` no la tiene.
        """
        if self._calendario is None:
            return False
        iso = self._fecha_int_to_iso(fecha_int)
        if iso is None:
            return False
        dni = next(
            (r.get("empleado_dni") for r in regs if r.get("empleado_dni")),
            None,
        )
        try:
            no_laborable = bool(self._calendario.es_no_laborable(iso, dni=dni))
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[recurso-concil] calendario laboral fallo en %s: %r",
                iso, exc,
            )
            return False
        self._recoger_degradacion(regs)
        return no_laborable

    def _recoger_degradacion(self, regs: list[dict]) -> None:
        consumir = getattr(self._calendario, "consumir_degradacion", None)
        if consumir is None:
            return
        try:
            degradado = bool(consumir())
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[recurso-concil] no se pudo leer la senal de degradacion "
                "del calendario: %r", exc,
            )
            return
        if not degradado:
            return
        docs = getattr(self, "_docs_degradados", None)
        if docs is None:
            return
        for r in regs:
            doc = r.get("document_id")
            if doc:
                docs.add(str(doc))

    @staticmethod
    def _fecha_int_to_iso(fecha_int: int | None) -> str | None:
        try:
            fi = int(fecha_int)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None
        if fi <= 0:
            return None
        y, m, d = fi // 10000, (fi // 100) % 100, fi % 100
        if not (1 <= m <= 12 and 1 <= d <= 31):
            return None
        return f"{y:04d}-{m:02d}-{d:02d}"
