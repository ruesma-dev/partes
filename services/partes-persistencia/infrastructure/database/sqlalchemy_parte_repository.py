# infrastructure/database/sqlalchemy_parte_repository.py
from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, text, update

from domain.models.parte_records import ExistingParte, ParteDocumento
from infrastructure.database.orm_models import (
    REPARTO_APLICADO,
    REPARTO_MANTENIDO,
    REPARTO_MATERIALIZADO,
    REPARTO_OBSOLETO,
    REPARTO_PENDIENTE,
    REPARTO_RECHAZADO,
    Base,
    EmpleadoAliasOrm,
    ParteDocumentOrm,
    ParteRegistroOrm,
    RepartoPendienteOrm,
    ddl_complementario,
)
from infrastructure.database.session_factory import SessionFactory
from application.services import text_match as tm
from application.services.pareja_extra import (
    FilaPareja,
    PlanRevert,
    clave_pareja,
    claves_congeladas,
    es_miembro,
    plan_revert,
)
from application.services.reajuste_reparto import (
    cambios_a_json,
    json_a_cambios,
)
from application.services.recurso_conciliador import esta_congelado

logger = logging.getLogger(__name__)

#: F-046 (R18, DA15): clave del candado consultivo de PostgreSQL que
#: serializa las pasadas de `conciliar_todos` entre replicas de sv3. Es de
#: SESION y PostgreSQL la etiqueta con la base (`partes`): no ve a los
#: otros proyectos del servidor compartido ni toca nada de servidor.
CLAVE_CANDADO_CONCILIAR = 460460001

#: Reloj y espera del candado (sustituibles en los tests).
_reloj = time.monotonic
_dormir = time.sleep


def _fila_pareja(*, registro_id: int, document_id, line_index,
                 empleado_line_no, fecha_int, extra_auto, tipo_hora,
                 sigrid_estado, aprobado) -> FilaPareja:
    """F-037: una fila de `parte_registros` tal como la ve `pareja_extra`.

    La congelacion por linea sale de `esta_congelado`, la regla compartida
    de siempre: la pareja solo la extiende.
    """
    return FilaPareja(
        registro_id=registro_id,
        clave=clave_pareja({
            "document_id": document_id, "line_index": line_index,
            "empleado_line_no": empleado_line_no, "fecha_int": fecha_int,
        }),
        extra_auto=bool(extra_auto),
        miembro=es_miembro(extra_auto=bool(extra_auto), tipo_hora=tipo_hora),
        congelada=esta_congelado(sigrid_estado, aprobado),
    )


def _log_plan_revert(plan: PlanRevert) -> None:
    """Los avisos de `revert_extras_auto` (F-015 R31; F-037 R6-R8).

    Sin nombres ni DNIs: ids de registro y claves de parte.
    """
    if plan.congeladas:
        logger.info(
            "[repo] revert de extras: %s linea(s) CONGELADAS respetadas "
            "(ya registradas/encoladas en Sigrid o en un parte aprobado).",
            plan.congeladas,
        )
    if plan.protegidas:
        logger.info(
            "[repo] revert de extras: %s linea(s) protegidas por su pareja "
            "congelada (F-037).",
            plan.protegidas,
        )
    if plan.duplicadas:
        logger.warning(
            "[repo] revert de extras: %s extra(s) automatica(s) "
            "DUPLICADA(S) borrada(s): su pareja ya tiene la extra congelada "
            "en Sigrid (F-037); ids: %s",
            len(plan.duplicadas),
            ", ".join(str(i) for i in plan.duplicadas[:10]),
        )
    for (document_id, line_index, _eln, _fecha), n in plan.dobles:
        logger.warning(
            "[repo] revert de extras: la pareja document_id=%s "
            "line_index=%s tiene %s extras automaticas CONGELADAS; no se "
            "borra ninguna, revisar a mano en Sigrid (F-037).",
            document_id, line_index, n,
        )


def _norm_txt(s: str | None) -> str:
    return " ".join((s or "").strip().lower().split())


def _norm_dni(s: str | None) -> str:
    return "".join(ch for ch in (s or "").upper() if ch.isalnum())


def _emp_signals(
    ide, dni, nombre_leido, nombre_emp
) -> set:
    """Senales que identifican a un trabajador: ide casado, DNI normalizado
    y/o nombre normalizado. Dos partes 'son del mismo trabajador' si comparten
    alguna senal."""
    sig: set = set()
    if ide is not None:
        sig.add(("ide", int(ide)))
    d = _norm_dni(dni)
    if d:
        sig.add(("dni", d))
    n = _norm_txt(nombre_leido) or _norm_txt(nombre_emp)
    if n:
        sig.add(("nom", n))
    return sig


class SqlAlchemyParteRepository:
    def __init__(self, session_factory: SessionFactory, *,
                 candado_espera_s: float = 300.0) -> None:
        self._session_factory = session_factory
        #: F-046 (R18): espera maxima por el candado de la pasada.
        self.candado_espera_s = float(candado_espera_s)

    def initialize(self) -> None:
        """Crea lo que falte del esquema y lo completa (idempotente).

        `create_all` no anade columnas ni indices a una tabla que ya
        existe: eso lo hace `ddl_complementario()`, GENERADO del ORM. Antes
        habia aqui una lista de ALTER escrita a mano que se quedo
        incompleta y distinta de la de sv4 (F-010).
        """
        engine = self._session_factory.engine
        Base.metadata.create_all(engine)
        sentencias = ddl_complementario()
        with engine.begin() as connection:
            for ddl in sentencias:
                connection.execute(text(ddl))
        logger.info(
            "[parte-repo] esquema inicializado (%s sentencias complementarias).",
            len(sentencias),
        )

    # ----------------------------------------------------------------- #
    # Conciliacion de PARTIDAS (la lanza sv3 al persistir; sv4 solo lee).
    # ----------------------------------------------------------------- #
    def fetch_registros_para_partida(self) -> list[dict]:
        """Registros de partes ACTIVOS con su obra/categoria/nombre, para
        casarlos contra las partidas del presupuesto. Devuelve dicts ligeros
        (no ORM, para no arrastrar sesiones)."""
        with self._session_factory.create_session() as session:
            stmt = (
                select(
                    ParteRegistroOrm.id,
                    ParteRegistroOrm.obra_ide,
                    ParteRegistroOrm.categoria,
                    ParteRegistroOrm.empleado_nombre,
                    ParteRegistroOrm.trabajador_nombre_leido,
                    ParteRegistroOrm.partida_match_method,
                    ParteRegistroOrm.partida,
                )
                .join(
                    ParteDocumentOrm,
                    ParteRegistroOrm.document_id == ParteDocumentOrm.id,
                )
                .where(ParteDocumentOrm.is_active.is_(True))
            )
            out: list[dict] = []
            for (rid, obra_ide, cat, emp_nom, leido, metodo,
                 partida_leida) in session.execute(stmt).all():
                out.append({
                    "registro_id": rid,
                    "obra_ide": obra_ide,
                    "categoria": cat,
                    "nombre": emp_nom or leido,
                    "partida_match_method": metodo,
                    "partida_leida": partida_leida,
                })
            return out

    def apply_partida_matches(self, updates: list[dict]) -> int:
        """Escribe el casado de partida por registro. Cada update:
        {registro_id, partida_ide, partida_cod, partida_res,
         partida_capitulo, partida_match_method, partida_match_score}.
        Devuelve el nº de registros actualizados."""
        if not updates:
            return 0
        n = 0
        with self._session_factory.create_session() as session:
            for u in updates:
                reg = session.get(ParteRegistroOrm, u.get("registro_id"))
                if reg is None:
                    continue
                reg.partida_ide = u.get("partida_ide")
                reg.partida_cod = u.get("partida_cod")
                reg.partida_res = u.get("partida_res")
                reg.partida_capitulo = u.get("partida_capitulo")
                reg.partida_match_method = u.get("partida_match_method")
                reg.partida_match_score = u.get("partida_match_score")
                n += 1
            session.commit()
        return n

    # ----------------------------------------------------------------- #
    # Conciliacion de RECURSO / parte de trabajo (Sigrid res + hmo).
    # ----------------------------------------------------------------- #
    def fetch_registros_para_recurso(self) -> list[dict]:
        """Registros de partes ACTIVOS con lo necesario para localizar el
        recurso y su parte de trabajo (empleado conciliado, obra y fecha) y
        para que el recurso pise categoria/hora: el tipo de hora de la linea
        y el codigo de hora/categoria ya resueltos (para detectar cambios).

        Desde F-015 trae ademas lo que hace falta para saber si la linea
        esta CONGELADA (R32): su `sigrid_estado` y si el parte del que sale
        esta aprobado. Esas lineas cuentan en el total del dia pero no se
        pueden recortar.

        F-037 (R9): cada fila lleva `congelada_por_pareja`, True si no esta
        congelada por si misma pero otro miembro de su pareja (base y
        extras automaticas de la misma clave) si. Se calcula sobre TODAS
        las filas leidas; el conciliador la trata como congelada.

        F-045 (R27): cada fila lleva ademas `horas_orig` (lo trabajado por
        la base de una pareja ya partida), `extra_auto`, `deleted_at_utc`
        (las de la papelera no entran en el reparto del dia, pero si en el
        casado de recurso) y la clave de pareja (`line_index`,
        `empleado_line_no`) para medir el reparto ideal de lo congelado."""
        with self._session_factory.create_session() as session:
            stmt = (
                select(
                    ParteRegistroOrm.id,
                    # F-003: el parte del que sale cada registro, para poder
                    # marcarlo si su computo se hizo con calendario dudoso.
                    ParteRegistroOrm.document_id,
                    ParteRegistroOrm.obra_ide,
                    ParteRegistroOrm.empleado_ide,
                    ParteRegistroOrm.empleado_reside,
                    ParteRegistroOrm.empleado_dni,
                    ParteRegistroOrm.fecha_int,
                    ParteRegistroOrm.tipo_hora,
                    ParteRegistroOrm.hora_ide,
                    ParteRegistroOrm.hora_codigo,
                    ParteRegistroOrm.categoria,
                    ParteRegistroOrm.horas,
                    # F-015 (R32): lo que congela una linea.
                    ParteRegistroOrm.sigrid_estado,
                    ParteDocumentOrm.approved,
                    # F-023: el recurso actual (una congelada lo conserva y
                    # cuenta con el en el dia, R30) y la empresa del parte
                    # (la de una linea sin obra, R25).
                    ParteRegistroOrm.recurso_ide,
                    ParteDocumentOrm.empresa,
                    # F-037: la clave de pareja (con document_id y
                    # fecha_int) y si la fila es una extra automatica.
                    ParteRegistroOrm.line_index,
                    ParteRegistroOrm.empleado_line_no,
                    ParteRegistroOrm.extra_auto,
                    # F-045: lo trabajado y la papelera.
                    ParteRegistroOrm.horas_orig,
                    ParteRegistroOrm.deleted_at_utc,
                )
                .join(
                    ParteDocumentOrm,
                    ParteRegistroOrm.document_id == ParteDocumentOrm.id,
                )
                .where(ParteDocumentOrm.is_active.is_(True))
            )
            out: list[dict] = []
            parejas: list[FilaPareja] = []
            for (rid, doc_id, obra_ide, emp_ide, reside, dni, fint, tipo_hora,
                 hora_ide, hora_codigo, categoria, horas, sigrid_estado,
                 aprobado, recurso_ide, empresa, line_index, eln,
                 extra_auto, horas_orig, borrada
                 ) in session.execute(stmt).all():
                parejas.append(_fila_pareja(
                    registro_id=rid, document_id=doc_id,
                    line_index=line_index, empleado_line_no=eln,
                    fecha_int=fint, extra_auto=extra_auto,
                    tipo_hora=tipo_hora, sigrid_estado=sigrid_estado,
                    aprobado=aprobado,
                ))
                out.append({
                    "registro_id": rid,
                    "document_id": doc_id,
                    "obra_ide": obra_ide,
                    "empleado_ide": emp_ide,
                    "empleado_reside": reside,
                    "empleado_dni": dni,
                    "fecha_int": fint,
                    "tipo_hora": tipo_hora,
                    "hora_ide": hora_ide,
                    "hora_codigo": hora_codigo,
                    "categoria": categoria,
                    "horas": horas,
                    "sigrid_estado": sigrid_estado,
                    "doc_approved": bool(aprobado),
                    "recurso_ide": recurso_ide,
                    "parte_empresa": empresa,
                    "horas_orig": horas_orig,
                    "extra_auto": bool(extra_auto),
                    "deleted_at_utc": borrada,
                    "line_index": line_index,
                    "empleado_line_no": eln,
                })
            congeladas = claves_congeladas(parejas)
            for fila, pareja in zip(out, parejas):
                fila["congelada_por_pareja"] = (
                    pareja.miembro and pareja.clave in congeladas
                    and not pareja.congelada
                )
            return out

    def marcar_review_required(self, document_ids) -> int:
        """Sube `review_required` a True en esos partes; nunca lo baja.

        La usa el conciliador cuando el computo de extras evaluo algun
        dia con el calendario degradado (F-003, R26): el parte se guarda
        igual —sv3 es best-effort— pero queda senalado para que alguien
        lo mire en el portal. Solo SUBE el flag: un parte marcado por
        otro motivo no se desmarca por esta via.
        """
        ids = sorted({str(d) for d in (document_ids or []) if d})
        if not ids:
            return 0
        n = 0
        with self._session_factory.create_session() as session:
            for doc_id in ids:
                doc = session.get(ParteDocumentOrm, doc_id)
                if doc is None or doc.review_required:
                    continue
                doc.review_required = True
                n += 1
            session.commit()
        if n:
            logger.warning(
                "[repo] %s parte(s) marcados para revision de %s solicitados.",
                n, len(ids),
            )
        return n

    # ----- extras por jornada (revert + split) ----- #
    def revert_extras_auto(self) -> int:
        """Deshace las extras por jornada de pasadas anteriores para poder
        recalcular el dia desde el estado original del parte: borra los
        registros extra_auto y restaura las horas originales de los normales
        recortados. Idempotente.

        NO toca lo CONGELADO (F-015, R31; decision D7 de F-012): una linea
        con `sigrid_estado` en {encolado, registrado} o cuyo parte esta
        `approved` ya viajo al ERP y alli no se va a recalcular. Borrarla y
        recrearla aqui la dejaria descuadrada respecto a Sigrid. El
        contador devuelto sigue siendo el de extras automaticas realmente
        borradas.

        F-037: la base y sus extras automaticas (misma clave de pareja) se
        congelan JUNTAS. Si un miembro esta congelado, la base no se
        restaura y sus extras no se borran (R4, R5): restaurar la base de
        una extra ya registrada hacia que el calculo la volviera a partir
        y creara otra extra en cada pasada. Las extras automaticas NO
        congeladas de una pareja cuya extra ya esta congelada son esos
        duplicados y se borran, con WARNING (R6). El plan lo decide
        `pareja_extra.plan_revert`.
        """
        with self._session_factory.create_session() as session:
            filas = session.execute(
                select(ParteRegistroOrm, ParteDocumentOrm.approved)
                .join(
                    ParteDocumentOrm,
                    ParteRegistroOrm.document_id == ParteDocumentOrm.id,
                )
                .where(
                    ParteRegistroOrm.extra_auto.is_(True)
                    | ParteRegistroOrm.horas_orig.isnot(None)
                )
            ).all()
            por_id = {reg.id: reg for reg, _ in filas}
            plan = plan_revert(
                _fila_pareja(
                    registro_id=reg.id,
                    document_id=reg.document_id,
                    line_index=reg.line_index,
                    empleado_line_no=reg.empleado_line_no,
                    fecha_int=reg.fecha_int,
                    extra_auto=reg.extra_auto,
                    tipo_hora=reg.tipo_hora,
                    sigrid_estado=reg.sigrid_estado,
                    aprobado=aprobado,
                )
                for reg, aprobado in filas
            )
            for rid in plan.borrar:
                session.delete(por_id[rid])
            for rid in plan.restaurar:
                reg = por_id[rid]
                reg.horas = reg.horas_orig
                reg.horas_orig = None
            session.commit()
        _log_plan_revert(plan)
        return len(plan.borrar)

    @staticmethod
    def _extra_de(normal: ParteRegistroOrm, s: dict) -> ParteRegistroOrm:
        """La extra automatica de un split, CLONADA de su ordinaria con la
        hora extra del recurso. F-046 (R15, R17): `id` opcional (el
        `registro_id` que reservo sv4 para la extra nueva) y `sigrid`
        opcional (los `sigrid_*` con que nace, si su base ya estaba en
        Sigrid)."""
        extra = ParteRegistroOrm(
            document_id=normal.document_id,
            line_index=normal.line_index,
            empleado_line_no=normal.empleado_line_no,
            categoria=normal.categoria,
            trabajador_nombre_leido=normal.trabajador_nombre_leido,
            empleado_ide=normal.empleado_ide,
            empleado_codigo=normal.empleado_codigo,
            empleado_nombre=normal.empleado_nombre,
            empleado_dni=normal.empleado_dni,
            empleado_reside=normal.empleado_reside,
            empleado_match_score=normal.empleado_match_score,
            empleado_match_method=normal.empleado_match_method,
            fecha=normal.fecha,
            fecha_int=normal.fecha_int,
            obra_codigo=normal.obra_codigo,
            obra_nombre=normal.obra_nombre,
            obra_ide=normal.obra_ide,
            tipo_hora="extra",
            es_incidencia=False,
            horas=s["extra_horas"],
            partida=normal.partida,
            partida_ide=normal.partida_ide,
            partida_cod=normal.partida_cod,
            partida_res=normal.partida_res,
            partida_capitulo=normal.partida_capitulo,
            partida_match_method=normal.partida_match_method,
            partida_match_score=normal.partida_match_score,
            recurso_ide=normal.recurso_ide,
            recurso_cif=normal.recurso_cif,
            hmo_ide=normal.hmo_ide,
            parte_estado=normal.parte_estado,
            hora_ide=s["hora_ext_ide"],
            hora_codigo=s["hora_ext_cod"],
            hora_descripcion=s["hora_ext_desc"],
            hora_ext=s["hora_ext_ext"],
            hora_candef=s["hora_candef"],
            hora_match_method="extra_jornada",
            extra_auto=True,
            confianza_pct=normal.confianza_pct,
        )
        if s.get("id") is not None:
            extra.id = int(s["id"])
        for campo, valor in (s.get("sigrid") or {}).items():
            if campo.startswith("sigrid_"):
                setattr(extra, campo, valor)
        return extra

    def apply_extras_splits(self, splits: list[dict]) -> int:
        """Aplica el paso de exceso de jornada a extra. Por cada split:
        recorta el registro normal (horas -> horas_norm, guardando horas_orig)
        e inserta un registro EXTRA (extra_auto) clonando el normal con la
        hora extra del recurso. Devuelve el numero de registros extra creados.

        F-046: cada split admite `id` y `sigrid` opcionales (`_extra_de`)."""
        if not splits:
            return 0
        n = 0
        with self._session_factory.create_session() as session:
            for s in splits:
                normal = session.get(ParteRegistroOrm, s["normal_id"])
                if normal is None:
                    continue
                if normal.horas_orig is None:
                    normal.horas_orig = s["horas_orig"]
                normal.horas = s["horas_norm"]
                session.add(self._extra_de(normal, s))
                n += 1
            session.commit()
        return n

    def apply_recurso_matches(self, updates: list[dict]) -> int:
        """Escribe el casado de recurso/parte por registro. Claves base:
        {registro_id, recurso_ide, recurso_cif, hmo_ide, parte_estado}.
        Si el recurso pisa categoria/hora, vienen ademas (solo entonces, para
        no borrar lo resuelto en lineas sin recurso o incidencias):
        categoria, hora_ide, hora_codigo, hora_descripcion, hora_ext,
        hora_candef, hora_match_method."""
        if not updates:
            return 0
        _PISA = (
            "categoria", "hora_ide", "hora_codigo", "hora_descripcion",
            "hora_ext", "hora_candef", "recurso_precio_hora",
            "hora_match_method",
        )
        n = 0
        with self._session_factory.create_session() as session:
            for u in updates:
                reg = session.get(ParteRegistroOrm, u.get("registro_id"))
                if reg is None:
                    continue
                reg.recurso_ide = u.get("recurso_ide")
                reg.recurso_cif = u.get("recurso_cif")
                reg.hmo_ide = u.get("hmo_ide")
                reg.parte_estado = u.get("parte_estado")
                for k in _PISA:
                    if k in u:
                        setattr(reg, k, u[k])
                n += 1
            session.commit()
        return n

    # ----------------------------------------------------------------- #
    # F-046: reajuste del reparto (candado, propuestas y materializacion).
    # ----------------------------------------------------------------- #
    @contextmanager
    def candado_pasada(self):
        """R18 (DA15): la pasada de `conciliar_todos` bajo un candado
        consultivo de SESION de PostgreSQL, en una conexion propia en
        autocommit (no deja ninguna transaccion abierta mientras dura).

        Lo intenta con `pg_try_advisory_lock` y espera con backoff (0,5 s,
        doblando hasta 8 s) hasta `candado_espera_s`; si no lo obtiene,
        `TimeoutError`. Lo suelta al salir pase lo que pase; si no puede
        soltarlo, invalida la conexion para que no vuelva al pool con el
        candado tomado. Fuera de PostgreSQL (SQLite de los tests) no hay
        candado."""
        motor = self._session_factory.engine
        if motor.dialect.name != "postgresql":
            yield
            return
        conexion = motor.connect().execution_options(
            isolation_level="AUTOCOMMIT")
        tomado = False
        try:
            inicio = _reloj()
            espera = 0.5
            while True:
                tomado = bool(conexion.execute(
                    text("SELECT pg_try_advisory_lock(:k)"),
                    {"k": CLAVE_CANDADO_CONCILIAR}).scalar())
                if tomado:
                    break
                pasado = _reloj() - inicio
                if pasado >= self.candado_espera_s:
                    raise TimeoutError(
                        f"no se obtuvo el candado de la pasada de "
                        f"conciliacion en {self.candado_espera_s:.0f} s")
                _dormir(min(espera, self.candado_espera_s - pasado))
                espera = min(espera * 2, 8.0)
            yield
        finally:
            if tomado:
                try:
                    conexion.execute(text("SELECT pg_advisory_unlock(:k)"),
                                     {"k": CLAVE_CANDADO_CONCILIAR})
                except Exception:  # noqa: BLE001
                    logger.warning("[repo] no se pudo soltar el candado de "
                                   "la pasada: se invalida la conexion.")
                    conexion.invalidate()
            conexion.close()

    def repartos_vigentes(self) -> dict[tuple[int, int], dict]:
        """(recurso, fecha) -> su reparto vivo (todo lo que no es
        `obsoleto`). Si hubiera dos, el de `id` mayor."""
        with self._session_factory.create_session() as session:
            filas = session.execute(
                select(RepartoPendienteOrm)
                .where(RepartoPendienteOrm.estado != REPARTO_OBSOLETO)
                .order_by(RepartoPendienteOrm.id)
            ).scalars().all()
            return {(f.recurso_ide, f.fecha_int): {
                "id": f.id, "estado": f.estado, "firma": f.firma,
                "recurso_ide": f.recurso_ide, "fecha_int": f.fecha_int,
                "cambios": f.cambios} for f in filas}

    @staticmethod
    def _ahora() -> str:
        return datetime.now(timezone.utc).isoformat()

    def materializar_repartos(self) -> dict:
        """R15-R17: lleva a `partes` los valores «despues» de cada reparto
        `aplicado` y lo pasa a `materializado`, todo en UNA transaccion por
        reparto (con CAS sobre `estado`).

        Es la unica escritura de sv3 sobre lineas congeladas (R40). Si una
        linea ya no tiene horas = «antes» ni «despues» (o falta la reserva
        o la respuesta de sv5 de una extra nueva), no toca NINGUNA linea de
        ese reparto: ERROR, `error` en la fila y se cuenta (R16)."""
        materializados = descuadrados = 0
        with self._session_factory.create_session() as session:
            ids = session.execute(
                select(RepartoPendienteOrm.id)
                .where(RepartoPendienteOrm.estado == REPARTO_APLICADO)
                .order_by(RepartoPendienteOrm.id)).scalars().all()
        for rid in ids:
            if self._materializar_uno(rid):
                materializados += 1
            else:
                descuadrados += 1
        return {"materializados": materializados,
                "descuadrados": descuadrados}

    def _materializar_uno(self, reparto_id: int) -> bool:
        with self._session_factory.create_session() as session:
            fila = session.get(RepartoPendienteOrm, reparto_id)
            if fila is None or fila.estado != REPARTO_APLICADO:
                return True
            datos = json_a_cambios(fila.cambios)
            try:
                resultado = json.loads(fila.resultado or "{}") or {}
            except ValueError:
                resultado = {}
            reservas = {str(k): int(v) for k, v in
                        (resultado.get("reservas") or {}).items()}
            sv5 = {int(x["registro_id"]): x for x in
                   ((resultado.get("sv5") or {}).get("lineas") or [])}
            plan, motivo = self._plan_materializar(session, datos, reservas,
                                                   sv5, fila)
            if motivo is not None:
                fila.error = f"descuadre al materializar: {motivo}"[:255]
                fila.actualizado_at_utc = self._ahora()
                session.commit()
                logger.error(
                    "[repo] reparto %s (recurso=%s fecha=%s) NO se "
                    "materializa: %s. No se toca ninguna linea.",
                    reparto_id, fila.recurso_ide, fila.fecha_int, motivo)
                return False
            for accion in plan:
                accion()
            ahora = self._ahora()
            cas = session.execute(
                update(RepartoPendienteOrm)
                .where(RepartoPendienteOrm.id == reparto_id,
                       RepartoPendienteOrm.estado == REPARTO_APLICADO)
                .values(estado=REPARTO_MATERIALIZADO,
                        materializado_at_utc=ahora, actualizado_at_utc=ahora,
                        error=None))
            if cas.rowcount != 1:
                session.rollback()
                return True
            session.commit()
            logger.info(
                "[repo] reparto %s materializado (recurso=%s fecha=%s): %s",
                reparto_id, fila.recurso_ide, fila.fecha_int,
                ", ".join(f"{c.get('tipo')} {c.get('registro_id') or 'nueva'} "
                          f"{c.get('antes')} -> {c.get('despues')}"
                          for c in datos["cambios"]))
            return True

    def _plan_materializar(self, session, datos: dict,
                           reservas: dict[str, int], sv5: dict[int, dict],
                           fila: RepartoPendienteOrm):
        """Lo que hay que escribir, o el motivo del descuadre (R16). No
        escribe nada: devuelve funciones que se ejecutan solo si TODO el
        reparto cuadra."""
        plan = []
        tol = 1e-6
        for c in datos["cambios"]:
            antes, despues = float(c["antes"]), float(c["despues"])
            if c.get("registro_id") is not None:
                reg = session.get(ParteRegistroOrm, int(c["registro_id"]))
                if reg is None:
                    return [], f"la linea {c['registro_id']} no existe"
                horas = float(reg.horas or 0.0)
                if abs(horas - despues) <= tol:
                    continue
                if abs(horas - antes) > tol:
                    return [], (f"la linea {reg.id} tiene {horas:g} h "
                                f"(ni {antes:g} ni {despues:g})")

                def _poner(reg=reg, c=c, antes=antes, despues=despues):
                    if (c.get("tipo") == "ordinaria"
                            and reg.horas_orig is None):
                        reg.horas_orig = antes
                    reg.horas = despues
                plan.append(_poner)
                continue
            base_rid = int(c["base_registro_id"])
            nueva_id = reservas.get(str(base_rid))
            if nueva_id is None:
                return [], f"sin id reservado para la extra de {base_rid}"
            hecha = session.get(ParteRegistroOrm, nueva_id)
            if hecha is not None:
                if abs(float(hecha.horas or 0.0) - despues) > tol:
                    return [], f"la extra {nueva_id} ya existe con otras horas"
                continue
            base = session.get(ParteRegistroOrm, base_rid)
            if base is None:
                return [], f"la base {base_rid} no existe"
            sigrid = None
            if (base.sigrid_estado or "").strip().lower() == "registrado":
                r = sv5.get(nueva_id)
                if r is None or not r.get("hmores_ide"):
                    return [], (f"sv5 no devolvio la linea de la extra "
                                f"{nueva_id}")
                sigrid = {
                    "sigrid_estado": "registrado",
                    "sigrid_hmores_ide": int(r["hmores_ide"]),
                    "sigrid_hmoide": r.get("hmoide"),
                    "sigrid_parte_cod": r.get("parte_cod"),
                    "sigrid_registrado_by": fila.decidido_por,
                    "sigrid_registrado_at_utc": fila.decidido_at_utc,
                }
            hora = c.get("hora_ext") or {}

            def _crear(base=base, nueva_id=nueva_id, despues=despues,
                       hora=hora, sigrid=sigrid):
                session.add(self._extra_de(base, {
                    "extra_horas": despues, "hora_ext_ide": hora.get("ide"),
                    "hora_ext_cod": hora.get("cod"),
                    "hora_ext_desc": hora.get("desc"),
                    "hora_ext_ext": hora.get("ext"),
                    "hora_candef": base.hora_candef, "id": nueva_id,
                    "sigrid": sigrid}))
            plan.append(_crear)
        return plan, None

    #: Estados de un reparto que la pasada puede pasar a `obsoleto` (R13):
    #: nunca `aplicando` ni `aplicado`.
    _VIVOS_OBSOLETABLES = (REPARTO_PENDIENTE, REPARTO_RECHAZADO,
                           REPARTO_MANTENIDO, REPARTO_MATERIALIZADO)

    def guardar_repartos(self, propuestas: list[dict],
                         mantenidos: list[int]) -> dict:
        """R11, R13, R14: deja la tabla como dice la pasada.

        `propuestas`: un dict por grupo evaluado en modo «proponer» o
        «residual» (`recurso_ide`, `fecha_int`, `firma`, `cambios` =
        `{ids_grupo, cambios[]}` o None si no hay propuesta). Los vivos del
        grupo con otra firma (y, sin propuesta, tambien el `pendiente` o
        `materializado` de la misma) pasan a `obsoleto` por CAS; si queda
        propuesta y no hay ya un `pendiente` con esa firma, nace otro. Nunca
        se toca un `aplicando`/`aplicado`, ni nace un pendiente mientras el
        grupo tenga uno de esos. `mantenidos`: ids `rechazado` que la pasada
        repartio en residual (R14)."""
        propuestos = obsoletos = n_mant = 0
        with self._session_factory.create_session() as session:
            for p in propuestas:
                filas = session.execute(
                    select(RepartoPendienteOrm)
                    .where(RepartoPendienteOrm.recurso_ide == p["recurso_ide"],
                           RepartoPendienteOrm.fecha_int == p["fecha_int"],
                           RepartoPendienteOrm.estado != REPARTO_OBSOLETO)
                ).scalars().all()
                cambios = p.get("cambios")
                if any(f.estado not in self._VIVOS_OBSOLETABLES
                       for f in filas):
                    continue          # aplicando/aplicado: no se toca nada
                quedan = []
                for f in filas:
                    misma = f.firma == p["firma"]
                    se_queda = misma and (
                        (cambios is not None
                         and f.estado == REPARTO_PENDIENTE)
                        or (cambios is None and f.estado in (
                            REPARTO_RECHAZADO, REPARTO_MANTENIDO)))
                    if se_queda or not self._cas(
                            session, f.id, self._VIVOS_OBSOLETABLES,
                            REPARTO_OBSOLETO):
                        quedan.append(f)
                    else:
                        obsoletos += 1
                if cambios is None or quedan:
                    continue
                ahora = self._ahora()
                session.add(RepartoPendienteOrm(
                    recurso_ide=int(p["recurso_ide"]),
                    fecha_int=int(p["fecha_int"]),
                    estado=REPARTO_PENDIENTE, firma=p["firma"],
                    cambios=cambios_a_json(self._enriquecer(session,
                                                            cambios)),
                    creado_at_utc=ahora, actualizado_at_utc=ahora))
                propuestos += 1
            for rid in mantenidos:
                if self._cas(session, int(rid), (REPARTO_RECHAZADO,),
                             REPARTO_MANTENIDO):
                    n_mant += 1
            session.commit()
        return {"propuestos": propuestos, "obsoletos": obsoletos,
                "mantenidos": n_mant}

    def _cas(self, session, reparto_id: int, desde: tuple[str, ...],
             hasta: str) -> bool:
        """`estado` de `desde` a `hasta` solo si sigue en `desde` (sv4
        tambien lo cambia: CAS, nunca un lock de proceso)."""
        res = session.execute(
            update(RepartoPendienteOrm)
            .where(RepartoPendienteOrm.id == reparto_id,
                   RepartoPendienteOrm.estado.in_(desde))
            .values(estado=hasta, actualizado_at_utc=self._ahora()))
        return res.rowcount == 1

    @staticmethod
    def _enriquecer(session, cambios: dict) -> dict:
        """Completa cada cambio con lo que sv4 ensena y sv5 necesita y no
        viaja en la lectura del conciliador: documento, obra (ide y codigo)
        y la linea de Sigrid (`hmores_ide`) de la linea o de su base."""
        out = []
        for c in cambios.get("cambios") or []:
            c = dict(c)
            rid = c.get("registro_id") or c.get("base_registro_id")
            reg = session.get(ParteRegistroOrm, int(rid)) if rid else None
            if reg is not None:
                c.setdefault("document_id", reg.document_id)
                c.setdefault("obra_ide", reg.obra_ide)
                c.setdefault("obra_codigo", reg.obra_codigo)
                if c.get("registro_id") is not None:
                    c.setdefault("hmores_ide", reg.sigrid_hmores_ide)
            out.append(c)
        return {"ids_grupo": list(cambios.get("ids_grupo") or []),
                "cambios": out}

    def find_empleado_alias(self, nombre_leido: str | None) -> dict | None:
        """Busca un alias aprendido (nombre LEIDO -> empleado). Devuelve los
        datos del empleado o None. Usado en ingesta antes de la similitud.
        F-040 (R6): tambien `recurso_ide` (el recurso elegido en el portal;
        `ide` es None si no tiene ficha)."""
        norm = tm.normalize(nombre_leido)
        if not norm:
            return None
        with self._session_factory.create_session() as session:
            row = session.get(EmpleadoAliasOrm, norm)
            if row is None:
                return None
            return {
                "ide": row.empleado_ide,
                "codigo": row.empleado_codigo,
                "nombre": row.empleado_nombre,
                "dni": row.empleado_dni,
                "recurso_ide": row.recurso_ide,
            }

    def get_by_sha256(self, source_sha256: str) -> ExistingParte | None:
        with self._session_factory.create_session() as session:
            stmt = (
                select(ParteDocumentOrm)
                .where(ParteDocumentOrm.source_sha256 == source_sha256)
                .where(ParteDocumentOrm.is_active.is_(True))
                .limit(1)
            )
            doc = session.execute(stmt).scalar_one_or_none()
            if doc is None:
                return None
            return ExistingParte(
                document_id=doc.id,
                source_sha256=doc.source_sha256,
                registros=len(doc.registros),
            )

    def _deactivate_same_day_obra(
        self, session, parte: ParteDocumento, exclude_id: str
    ) -> list[str]:
        """Desactiva (soft-delete) los partes ACTIVOS del MISMO dia, MISMA
        obra y MISMO trabajador. Asi reenviar el parte de un trabajador (mismo
        dia/obra) 'pisa' al anterior, pero los partes de OTROS trabajadores del
        mismo dia/obra NO se tocan (cada pagina/PDF suele ser un trabajador).

        Identidad de obra: por codigo casado si lo hay; si no, por el numero
        de obra leido. Identidad de trabajador: ide casado, DNI o nombre.
        Si no hay fecha, ni obra, ni trabajador identificable, NO se desactiva
        nada (mas seguro)."""
        fint = parte.fecha_int
        if not fint or fint <= 0:
            return []
        cod = ((parte.obra.codigo if parte.obra else None) or "").strip()
        num = (parte.obra_numero_leido or "").strip()
        if not cod and not num:
            return []
        stmt = (
            select(ParteDocumentOrm)
            .where(ParteDocumentOrm.is_active.is_(True))
            .where(ParteDocumentOrm.id != exclude_id)
            .where(ParteDocumentOrm.fecha_int == fint)
        )
        if cod:
            stmt = stmt.where(ParteDocumentOrm.obra_codigo == cod)
        else:
            stmt = stmt.where(
                ParteDocumentOrm.obra_codigo.is_(None),
                ParteDocumentOrm.obra_numero_leido == num,
            )
        # Senales de los trabajadores del parte NUEVO.
        nuevos: set = set()
        for r in parte.registros:
            emp = r.empleado
            nuevos |= _emp_signals(
                emp.ide, emp.dni, r.trabajador_nombre_leido, emp.nombre
            )
        if not nuevos:
            return []  # parte sin trabajador identificable: no pisa nada

        ids: list[str] = []
        for old in session.execute(stmt).scalars().all():
            viejos: set = set()
            for oreg in old.registros:
                viejos |= _emp_signals(
                    oreg.empleado_ide, oreg.empleado_dni,
                    oreg.trabajador_nombre_leido, oreg.empleado_nombre,
                )
            if nuevos & viejos:  # comparten trabajador -> es un reemplazo
                old.is_active = False
                ids.append(old.id)
        return ids

    def save_parte(
        self,
        *,
        document_id: str,
        parte: ParteDocumento,
        meta: dict[str, Any],
        context: dict[str, Any],
        raw_extraction_json: str,
        raw_context_json: str,
        review_required: bool,
    ) -> None:
        email = (context or {}).get("email") or {}
        attachment = (context or {}).get("attachment") or {}
        document = (context or {}).get("document") or {}
        now_iso = datetime.now(timezone.utc).isoformat()
        obra = parte.obra

        with self._session_factory.create_session() as session:
            # Reemplazo: un PDF distinto del mismo dia y obra pisa lo anterior.
            superseded = self._deactivate_same_day_obra(
                session, parte, document_id
            )
            if superseded:
                logger.info(
                    "[parte-repo] reemplazo: desactivados %s parte(s) previos "
                    "del mismo dia/obra (fecha_int=%s obra=%s): %s",
                    len(superseded), parte.fecha_int,
                    (parte.obra.codigo if parte.obra else None)
                    or parte.obra_numero_leido,
                    superseded,
                )
            doc = ParteDocumentOrm(
                id=document_id,
                source_filename=str(
                    document.get("filename")
                    or meta.get("source_filename")
                    or "document.bin"
                ),
                source_mime_type=str(
                    document.get("mime_type")
                    or meta.get("source_mime_type")
                    or "application/octet-stream"
                ),
                source_sha256=str(
                    document.get("sha256") or meta.get("source_sha256") or ""
                ),
                page_number=_as_int(document.get("page_number")),
                page_count=_as_int(document.get("page_count")),
                provider=_as_str(meta.get("provider")),
                model_name=_as_str(meta.get("model")),
                prompt_key=_as_str(meta.get("prompt_key")),
                schema_name=_as_str(meta.get("schema")),
                # Dia.
                fecha=parte.fecha_iso,
                fecha_int=parte.fecha_int,
                # Obra.
                obra_numero_leido=parte.obra_numero_leido,
                obra_nombre_leido=parte.obra_nombre_leido,
                obra_ide=obra.ide,
                obra_codigo=obra.codigo,
                obra_nombre=obra.nombre,
                obra_match_score=obra.score,
                obra_match_method=obra.method,
                # Empresa del parte (F-023, DA11).
                empresa_membrete=parte.empresa_membrete,
                empresa=parte.empresa,
                empresa_origen=parte.empresa_origen,
                # Responsables.
                encargado_nombre=parte.encargado_nombre,
                jefe_obra_nombre=parte.jefe_obra_nombre,
                # Firma.
                firmado=parte.firmado,
                firma_encargado=parte.firma_encargado,
                firma_jefe_obra=parte.firma_jefe_obra,
                firma_administracion=parte.firma_administracion,
                firmante_rol=parte.firmante_rol,
                firmante_nombre=parte.firmante_nombre,
                firma_confianza_pct=parte.firma_confianza_pct,
                # SharePoint.
                sharepoint_url=parte.sharepoint_url,
                sharepoint_item_id=parte.sharepoint_item_id,
                sharepoint_drive_id=parte.sharepoint_drive_id,
                # Email.
                email_id=_as_str(email.get("id")),
                email_subject=_as_str(email.get("subject")),
                email_sender=_as_str(email.get("sender")),
                email_received_datetime=_as_str(email.get("receivedDateTime")),
                source_attachment_filename=_as_str(attachment.get("name")),
                source_attachment_sha256=_as_str(attachment.get("sha256")),
                # Estado.
                review_required=review_required,
                approved=False,
                is_active=True,
                raw_extraction_json=raw_extraction_json,
                raw_context_json=raw_context_json,
                created_at_utc=now_iso,
            )

            for reg in parte.registros:
                emp = reg.empleado
                hora = reg.hora
                doc.registros.append(
                    ParteRegistroOrm(
                        line_index=reg.line_index,
                        empleado_line_no=reg.empleado_line_no,
                        categoria=reg.categoria,
                        trabajador_nombre_leido=reg.trabajador_nombre_leido,
                        empleado_ide=emp.ide,
                        empleado_codigo=emp.codigo,
                        empleado_nombre=emp.nombre,
                        empleado_dni=emp.dni,
                        empleado_reside=emp.reside,
                        empleado_match_score=emp.score,
                        empleado_match_method=emp.method,
                        fecha=parte.fecha_iso,
                        fecha_int=parte.fecha_int,
                        obra_codigo=obra.codigo,
                        obra_nombre=obra.nombre,
                        obra_ide=obra.ide,
                        tipo_hora=reg.tipo_hora,
                        es_incidencia=reg.es_incidencia,
                        incidencia_codigo=reg.incidencia.codigo,
                        incidencia_texto=reg.incidencia.texto_leido,
                        incidencia_dias=reg.incidencia.dias,
                        horas=reg.horas,
                        partida=reg.partida,
                        hora_ide=hora.ide,
                        hora_codigo=hora.codigo,
                        hora_descripcion=hora.descripcion,
                        hora_ext=hora.ext,
                        hora_precio_coste=hora.pre,
                        hora_precio_nomina=hora.prenom,
                        hora_match_method=hora.method,
                        confianza_pct=reg.confianza_pct,
                    )
                )

            session.add(doc)
            session.commit()

        logger.info(
            "[parte-repo] guardado document_id=%s fecha=%s registros=%s",
            document_id, parte.fecha_iso, len(parte.registros),
        )


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
