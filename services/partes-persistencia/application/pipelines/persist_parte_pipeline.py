# application/pipelines/persist_parte_pipeline.py
"""Pipeline de persistencia de un parte de trabajo DIARIO (sv3).

Pasos:
  1. Lee el envelope ``{meta, data, debug}`` de sv2.
  2. Dedup por sha256 del documento (soft-delete consciente).
  3. Normaliza ``data`` -> ParteDocumento (expande empleados en registros).
  4. Casa contra Sigrid (si esta cableado), en el orden de F-023:
       - fecha de referencia (la del parte o, sin ella, hoy: R16),
       - empresa del membrete (R7-R8) y discriminantes por los recursos
         de alta de los trabajadores con DNI leido (R11),
       - obra a nivel de parte (R9-R14) y empresa del parte (R15),
       - por registro: empleado (DNI -> alias -> nombre, R17-R24) +
         codigo de hora ``auxhor`` (normal/extra por ext, o incidencia).
         F-030: quien no tiene ficha de empleado se casa con el MISMO
         proceso contra su «ficha de recurso» (`MO/` con `res.cif`): DNI
         -> `recurso_dni` antes del alias; en el nombre compiten las dos
         clases de ficha -> `recurso_nombre`. Sin `empleado_ide`.
  5. Calcula ``review_required`` (un casado por recurso no lo sube).
  6. Persiste documento + registros.
"""
from __future__ import annotations

import dataclasses
import json
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

from application.services import text_match as tm
from application.services.empleado_matcher import EmpleadoMatcher
from application.services.parte_normalizer import ParteNormalizer
from application.services.seleccion_sigrid import IndicePersonas
from application.services.sigrid_matcher_provider import (
    Matchers,
    SigridMatcherProvider,
)
from domain.models.parte_records import (
    EmpleadoMatch,
    ObraMatch,
    ParteDocumento,
    PersistParteResult,
    RegistroNormalizado,
)
from domain.models.sigrid_models import EmpleadoRow
from domain.ports.parte_repository import ParteRepository

logger = logging.getLogger(__name__)

#: Obras sin casar por F-023 que mandan el parte a revision (R10, R13, R14).
OBRA_A_REVISAR: frozenset[str] = frozenset(
    {"codigo_otra_empresa", "codigo_ambiguo", "nombre_ambiguo"}
)

#: F-030: metodos de un trabajador casado contra su «ficha de recurso» (sin
#: ficha de empleado): `empleado_ide` NULL y, aun asi, casado (R12-R13).
METODOS_RECURSO: frozenset[str] = frozenset({"recurso_dni", "recurso_nombre"})


def _de_recurso(ficha: EmpleadoRow, score: float, metodo: str) -> EmpleadoMatch:
    """F-030 (R12): el casado contra una ficha de recurso. Mismas columnas
    que con ficha, sin `ide` ni `codigo` de empleado: `dni` = `res.cif`,
    `nombre` = `con.res` y `reside` = `res.ide`."""
    return dataclasses.replace(
        EmpleadoMatcher.to_match(ficha, score, metodo), ide=None, codigo=None
    )


#: De donde sale la empresa del parte cuando la da la obra y no hubo
#: membrete (R15). Lo que no esta aqui (codigo, codigo_padded) es `obra`.
_ORIGEN_POR_METODO: dict[str, str] = {
    "codigo_trabajadores": "trabajadores",
    "codigo_nombre": "nombre",
    "nombre": "nombre",
}


def empresa_del_parte(
    obra: ObraMatch, empresa_membrete: int | None
) -> tuple[int | None, str | None]:
    """R15: la empresa de la obra casada; sin obra, la del membrete; si no,
    ninguna. Devuelve `(empresa, origen)`."""
    if obra.ide is not None:
        if obra.empresa is None:
            return None, None
        if empresa_membrete is not None:
            return obra.empresa, "membrete"
        return obra.empresa, _ORIGEN_POR_METODO.get(obra.method, "obra")
    if empresa_membrete is not None:
        return empresa_membrete, "membrete"
    return None, None


@dataclass(frozen=True)
class PersistParteRequest:
    filename: str
    mime_type: str
    file_bytes: bytes
    extraction_envelope: dict[str, Any]
    context: dict[str, Any]


class PersistPartePipeline:
    def __init__(
        self,
        *,
        repository: ParteRepository,
        normalizer: ParteNormalizer,
        matcher_provider: Optional[SigridMatcherProvider],
        sharepoint_uploader: Any = None,
        partida_conciliador: Any = None,
        recurso_conciliador: Any = None,
        hoy: Callable[[], date] = date.today,
    ) -> None:
        # F-023 (R16): de donde sale «hoy» cuando el parte no trae fecha.
        self._hoy = hoy
        self._repository = repository
        self._normalizer = normalizer
        self._matcher_provider = matcher_provider
        # Uploader best-effort (duck-typing: .upload_parte_pdf). Si es None o
        # falla, el parte se guarda igual sin URL de SharePoint.
        self._sharepoint = sharepoint_uploader
        # Conciliadores best-effort (tras guardar, recasan TODOS los partes):
        # partidas (presupuesto) y recurso/parte de trabajo. Si None, se omiten.
        self._partida_conciliador = partida_conciliador
        self._recurso_conciliador = recurso_conciliador

    def run(self, request: PersistParteRequest) -> PersistParteResult:
        envelope = request.extraction_envelope or {}
        meta = envelope.get("meta") or {}
        data = envelope.get("data") or {}
        if not isinstance(meta, dict):
            meta = {}
        if not isinstance(data, dict):
            data = {}

        context = request.context if isinstance(request.context, dict) else {}
        document_ctx = context.get("document") or {}
        sha256 = str(
            document_ctx.get("sha256") or meta.get("source_sha256") or ""
        ).strip()

        # ---- Dedup ---- #
        if sha256:
            existing = self._repository.get_by_sha256(sha256)
            if existing is not None:
                logger.info(
                    "[persist-parte] sha256=%s ya existe (document_id=%s). "
                    "Se omite reinsercion.",
                    sha256, existing.document_id,
                )
                return PersistParteResult(
                    ok=True,
                    document_id=existing.document_id,
                    already_existed=True,
                    fecha=None,
                    obra_codigo=None,
                    empleados_distintos=0,
                    registros_persistidos=existing.registros,
                    registros_con_hora=0,
                    firmado=False,
                )

        # ---- Normalizacion + expansion ---- #
        email_ctx = context.get("email") or {}
        email_text = " ".join(
            str(email_ctx.get(k) or "")
            for k in ("subject", "bodyPreview", "body")
        ).strip() or None
        parte = self._normalizer.normalize(data, email_text=email_text)

        # ---- Casado Sigrid ---- #
        if self._matcher_provider is not None:
            self._match(parte)
        else:
            logger.info(
                "[persist-parte] Sigrid NO cableado: se persiste sin casar."
            )

        review_required = self._compute_review_required(parte)

        # ---- Archivado en SharePoint (best-effort) ---- #
        self._archive_to_sharepoint(parte, request, sha256)

        # ---- Persistencia ---- #
        document_id = str(uuid.uuid4())
        self._repository.save_parte(
            document_id=document_id,
            parte=parte,
            meta=meta,
            context=context,
            raw_extraction_json=json.dumps(envelope, ensure_ascii=False),
            raw_context_json=json.dumps(context, ensure_ascii=False),
            review_required=review_required,
        )

        # ---- Conciliacion automatica (todos los partes): partida + recurso ----
        self._conciliar_partidas_safely()
        self._conciliar_recursos_safely()

        empleados = {
            r.empleado.ide or r.trabajador_nombre_leido
            for r in parte.registros
        }
        registros_con_hora = sum(
            1 for r in parte.registros if r.hora.ide is not None
        )
        return PersistParteResult(
            ok=True,
            document_id=document_id,
            already_existed=False,
            fecha=parte.fecha_iso,
            obra_codigo=parte.obra.codigo or parte.obra_numero_leido,
            empleados_distintos=len(empleados),
            registros_persistidos=len(parte.registros),
            registros_con_hora=registros_con_hora,
            firmado=parte.firmado,
        )

    # ----------------------------------------------------------------- #
    def _conciliar_partidas_safely(self) -> None:
        """Lanza la conciliacion de partidas sobre TODOS los partes activos.
        Best-effort: nunca rompe la persistencia del parte."""
        if self._partida_conciliador is None:
            return
        try:
            res = self._partida_conciliador.conciliar_todos()
            logger.info("[persist-parte] conciliacion de partidas: %s", res)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[persist-parte] conciliacion de partidas fallo "
                "(no bloquea el guardado): %r", exc
            )

    # ----------------------------------------------------------------- #
    def _conciliar_recursos_safely(self) -> None:
        """Lanza la conciliacion de recurso/parte sobre TODOS los partes
        activos. Best-effort: nunca rompe la persistencia."""
        if self._recurso_conciliador is None:
            return
        try:
            res = self._recurso_conciliador.conciliar_todos()
            logger.info("[persist-parte] conciliacion de recurso: %s", res)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[persist-parte] conciliacion de recurso fallo "
                "(no bloquea el guardado): %r", exc
            )

    # ----------------------------------------------------------------- #
    def _archive_to_sharepoint(
        self,
        parte: ParteDocumento,
        request: PersistParteRequest,
        sha256: str,
    ) -> None:
        if self._sharepoint is None or not request.file_bytes:
            return
        try:
            stored = self._sharepoint.upload_parte_pdf(
                filename=request.filename,
                file_bytes=request.file_bytes,
                source_sha256=sha256 or "",
            )
            parte.sharepoint_url = stored.share_url or stored.web_url
            parte.sharepoint_item_id = stored.item_id
            parte.sharepoint_drive_id = stored.drive_id
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[persist-parte] SharePoint fallo (se guarda sin URL): %r", exc
            )

    # ----------------------------------------------------------------- #
    def _match(self, parte: ParteDocumento) -> None:
        assert self._matcher_provider is not None
        matchers = self._matcher_provider.get()
        indice = matchers.indice

        # R16: fecha de referencia del parte.
        fecha = parte.fecha_int or int(self._hoy().strftime("%Y%m%d"))
        # R7-R8: empresa del membrete (None si no se reconoce; se loguea).
        empresa_m, _ = matchers.empresas.resolver(parte.empresa_membrete)
        # R11: por cada trabajador con DNI leido, las empresas donde tiene
        # recursos de alta a la fecha.
        dnis = sorted({
            tm.normalize_dni(r.trabajador_dni_leido) for r in parte.registros
        } - {""})
        discriminantes = [indice.empresas_con_recurso(d, fecha) for d in dnis]

        # Obra (nivel parte) y empresa del parte.
        parte.obra = matchers.obra.match(
            codigo=parte.obra_numero_leido,
            nombre=parte.obra_nombre_leido,
            empresa_membrete=empresa_m,
            discriminantes=discriminantes,
        )
        parte.empresa, parte.empresa_origen = empresa_del_parte(
            parte.obra, empresa_m
        )

        # Cache de casado de empleado por nombre (evita rematchear el mismo
        # trabajador en sus varias filas normal/extra/incidencia).
        emp_cache: dict[str, Any] = {}
        # Descripcion del codigo ordinario resuelto por empleado, para derivar
        # el codigo extra de la misma categoria si la extra (creada por la
        # resta >8h) no trae codigo propuesto.
        ord_desc_by_emp: dict[str, str | None] = {}

        for reg in parte.registros:
            nombre = reg.trabajador_nombre_leido or ""
            dni_leido = (reg.trabajador_dni_leido or "").strip()
            key = dni_leido.upper() + "|" + nombre.strip().lower()
            if key in emp_cache:
                reg.empleado = emp_cache[key]
            else:
                match = self._casar_trabajador(
                    reg, matchers, parte.empresa, fecha
                )
                emp_cache[key] = match
                reg.empleado = match

            if reg.es_incidencia:
                reg.hora = matchers.tipo_hora.resolve(
                    tipo_hora=reg.tipo_hora,
                    codigo_hora_leido=reg.codigo_hora_propuesto,
                    incidencia_codigo=reg.incidencia.codigo,
                )
            elif reg.tipo_hora == "extra":
                reg.hora = matchers.tipo_hora.resolve(
                    tipo_hora="extra",
                    codigo_hora_leido=reg.codigo_hora_propuesto,
                    categoria=reg.categoria,
                    categoria_ref_desc=ord_desc_by_emp.get(key),
                )
            else:
                reg.hora = matchers.tipo_hora.resolve(
                    tipo_hora=reg.tipo_hora,
                    codigo_hora_leido=reg.codigo_hora_propuesto,
                    categoria=reg.categoria,
                )
                if reg.hora.descripcion:
                    ord_desc_by_emp[key] = reg.hora.descripcion

    # ----------------------------------------------------------------- #
    def _casar_trabajador(
        self,
        reg: RegistroNormalizado,
        matchers: Matchers,
        empresa: int | None,
        fecha: int,
    ) -> EmpleadoMatch:
        """R17-R24: DNI leido -> alias aprendido -> similitud de nombre,
        siempre contra las fichas de alta a la fecha de la empresa del
        parte. Un DNI ambiguo, de baja o de otra empresa CIERRA la linea
        sin casar (R22): nunca se sigue al alias ni al nombre.

        F-030: si el DNI no tiene ficha de empleado, se busca entre las
        fichas de recurso (`recurso_dni`) antes del alias; en el nombre
        compiten las dos clases de ficha (`recurso_nombre`). El alias solo
        apunta a fichas de empleado (R8)."""
        indice = matchers.indice
        res = indice.elegir_ficha(reg.trabajador_dni_leido, empresa, fecha)
        if res.motivo == "ok":
            return matchers.empleado.to_match(
                indice.ficha(res.ide), 1.0, "dni"  # type: ignore[arg-type]
            )
        if res.motivo != "desconocido":
            return EmpleadoMatch(method=f"dni_{res.motivo}")
        # F-030 (R5-R6): sin ficha de empleado para el DNI, el MISMO
        # `elegir_ficha` contra las fichas de recurso, antes del alias y del
        # nombre. Si no da una, se sigue como siempre.
        if reg.trabajador_dni_leido:
            recursos = matchers.recursos
            res = recursos.elegir_ficha(
                reg.trabajador_dni_leido, empresa, fecha
            )
            if res.motivo == "ok":
                return _de_recurso(
                    recursos.ficha(res.ide), 1.0, "recurso_dni"  # type: ignore[arg-type]
                )
            if res.motivo != "desconocido":
                logger.info(
                    "[persist-parte] linea=%s: DNI leido con ficha de recurso "
                    "%s (empresa=%s fecha=%s); se sigue por alias y nombre.",
                    reg.line_index, res.motivo, empresa, fecha,
                )
        candidatas = indice.fichas_candidatas(empresa, fecha)
        alias = self._repository.find_empleado_alias(
            reg.trabajador_nombre_leido
        )
        if alias is not None:
            return self._casar_alias(
                alias, indice, matchers, candidatas, empresa, fecha
            )
        # F-030 (R9-R11): en el nombre compiten JUNTAS las fichas de empleado
        # y las de recurso candidatas (mismo umbral y ambiguedad); si gana
        # una de recurso, el casado es por recurso.
        recursos = matchers.recursos
        match = matchers.empleado.match_nombre_fichas(
            nombre=reg.trabajador_nombre_leido,
            candidatas=candidatas + recursos.fichas_candidatas(empresa, fecha),
        )
        ficha_recurso = recursos.ficha(match.ide)
        if ficha_recurso is not None:
            return _de_recurso(ficha_recurso, match.score, "recurso_nombre")
        return match

    @staticmethod
    def _casar_alias(
        alias: dict,
        indice: IndicePersonas,
        matchers: Matchers,
        candidatas: list,
        empresa: int | None,
        fecha: int,
    ) -> EmpleadoMatch:
        """R23: el alias vale si su ficha es candidata; si no, se re-resuelve
        por el DNI del alias. Sin DNI, o con uno que no esta en el maestro,
        el alias no es valido."""
        ficha = next((f for f in candidatas if f.ide == alias.get("ide")), None)
        if ficha is not None:
            return matchers.empleado.to_match(ficha, 1.0, "alias")
        res = indice.elegir_ficha(alias.get("dni"), empresa, fecha)
        if res.motivo == "ok":
            return matchers.empleado.to_match(
                indice.ficha(res.ide), 1.0, "alias"  # type: ignore[arg-type]
            )
        if res.motivo == "desconocido":
            return EmpleadoMatch(method="alias_no_valido")
        return EmpleadoMatch(method=f"dni_{res.motivo}")

    # ----------------------------------------------------------------- #
    @staticmethod
    def _compute_review_required(parte: ParteDocumento) -> bool:
        # Revision si: sin registros, o el parte no esta firmado, o algun
        # registro no caso el empleado, o un registro de HORAS (no
        # incidencia) no tiene codigo de hora resuelto.
        if not parte.registros:
            return True
        if not parte.firmado:
            return True
        # F-023: obra sin casar por empresa o por ambiguedad (R10, R13, R14).
        if parte.obra.method in OBRA_A_REVISAR:
            return True
        for reg in parte.registros:
            # F-030 (R13): casado por recurso cuenta como casado.
            if (
                reg.empleado.ide is None
                and reg.empleado.method not in METODOS_RECURSO
            ):
                return True
            if not reg.es_incidencia and reg.hora.ide is None:
                return True
        return False
