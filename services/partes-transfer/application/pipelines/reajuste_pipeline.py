# application/pipelines/reajuste_pipeline.py
"""F-046 · Reajuste en Sigrid de lineas ya registradas (sv5).

Cuando el reparto ponderado del dia (F-045) cambia lineas que ya estan en
Sigrid y el humano elige «Aplicar» en el portal, sv4 pide a sv5 que las
edite. Dos operaciones:

  - `comprobar` (R20): SOLO LECTURA y sin lock. Un veredicto por linea
    (`reajuste_lineas`): editable, ya aplicada o por que no.
  - `ejecutar` (R20, R23-R29): bajo el MISMO lock que el registro
    (`RegistroPipeline.lock`), relee, decide y, solo si TODAS las lineas
    son editables, escribe UN lote (una transaccion de sigrid-api):

        1. guardia: aborta el lote si algo cambio desde la lectura (DA6);
        2. `UPDATE` de cada linea existente: `can` y `tot = can x pre`
           con el `pre` de la propia linea, `WHERE` optimista (R24, R25);
        3. `INSERT` de cada extra nueva en el parte de su base, condicionado
           a que la base ya tenga «despues» (R24).

    Despues RELEE y decide por lo que hay en Sigrid, no por lo que dijo la
    respuesta: todo con «despues» = hecho (tambien si la respuesta fallo
    pero llego a escribir); nada = rechazado (`ok: false`, R23); a medias =
    excepcion (sv4 lo deja `aplicando` con ERROR para comprobarlo, DA6).

Las extras nuevas pasan por `RegistroPipeline.preparar` (obra destino y
modo pruebas, verificacion del recurso, reglas y cuenta analitica F-021),
fuera del lock como en el registro: son datos maestros. Van al parte
(`hmoide`) de su base; en modo pruebas llevan la marca en `tex` (R28).

[E] R47: el reajuste solo actualiza y anade lineas. Una linea que queda a
0 se queda con `can = 0` y `tot = 0`; ninguna se quita de Sigrid.

Logs sin nombres ni DNIs (R29): ids de registro y de linea, horas y
usuario.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from domain.models.registro_models import (
    AccionLinea,
    LineaEntrada,
    LineaSigrid,
    ObraEntrada,
    OpReajuste,
    ResultadoReajuste,
    VeredictoReajuste,
)
from infrastructure.sigrid.sigrid_write_client import synckey_de

from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.reajuste_lineas import (
    veredicto_existente,
    veredicto_nueva,
)

logger = logging.getLogger(__name__)

#: Motivo de R27 (el reajuste no cabe en un lote de sigrid-api).
MOTIVO_DEMASIADAS = "demasiadas lineas para un lote"

#: Motivo de una extra nueva cuya base no viene en la peticion.
MOTIVO_SIN_BASE = "su linea base no viene en el reajuste"


@dataclass
class _Preparada:
    """Lo que `preparar` decidio para una extra nueva (datos maestros)."""
    accion: AccionLinea | None
    destino: ObraEntrada | None


@dataclass
class _Evaluacion:
    """Lo leido y el veredicto de cada linea, en el orden de la peticion."""
    veredictos: list[VeredictoReajuste]
    lineas: dict[str, LineaSigrid]
    partes: dict[int, dict]


class ReajustePipeline:
    def __init__(self, *, cliente, settings,
                 registro: RegistroPipeline) -> None:
        self._cli = cliente
        self._st = settings
        self._reg = registro

    @property
    def lock(self):
        """El MISMO lock que el registro (R20): una sola escritura a la vez
        en Sigrid, venga del registro, de la cola o del reajuste."""
        return self._reg.lock

    # ------------------------------------------------------------- #
    def _est_registro(self) -> int:
        return int(getattr(self._st, "est_parte_activo", 1))

    def _max_sentencias(self) -> int:
        return int(getattr(self._st, "sigrid_max_statements", 15))

    def _forzada(self) -> bool:
        return bool(getattr(self._st, "obra_pruebas_forzar", False))

    # --------------------- extras nuevas: preparar --------------------- #
    def _preparar_nuevas(self, ops: Sequence[OpReajuste]
                         ) -> dict[int, _Preparada]:
        """R22: cada extra nueva por `preparar` del registro, una llamada
        por obra. Una nueva sin los datos que el registro necesita no se
        prepara (queda sin decision y no es editable)."""
        por_obra: dict[tuple, list[OpReajuste]] = defaultdict(list)
        out: dict[int, _Preparada] = {}
        for op in ops:
            if not op.es_nueva:
                continue
            if not (op.fecha_int and op.recurso_ide
                    and (op.obra_ide or op.obra_codigo)):
                out[op.registro_id] = _Preparada(None, None)
                continue
            por_obra[(op.obra_ide, op.obra_codigo)].append(op)
        for (obra_ide, obra_cod), grupo in por_obra.items():
            ctx = self._reg.preparar(
                obra=ObraEntrada(ide=obra_ide, codigo=obra_cod),
                lineas=[LineaEntrada(
                    registro_id=op.registro_id, fecha_int=int(op.fecha_int),
                    recurso_ide=op.recurso_ide, tipo_hora="extra",
                    horas=op.despues, hora_ide=op.hora_ide,
                    hora_codigo=op.hora_codigo, partida_ide=op.partida_ide,
                    partida_cod=op.partida_cod) for op in grupo])
            acciones = {a.registro_id: a for a in ctx.acciones}
            for op in grupo:
                out[op.registro_id] = _Preparada(
                    acciones.get(op.registro_id), ctx.obra_destino)
        return out

    def _choques(self, accion: AccionLinea, destino: ObraEntrada,
                 mias: set[str]) -> list[LineaSigrid]:
        """R22: lineas ajenas del mismo recurso, dia y codigo de hora en
        los partes En registro del periodo de la obra destino."""
        est = self._est_registro()
        out: list[LineaSigrid] = []
        for ps in self._cli.partes_del_periodo(int(destino.ide), accion.ano,
                                               accion.mes):
            if ps.est != est:
                continue
            for ls in self._cli.lineas_existentes(
                    int(ps.ide), [accion.recurso_ide], [accion.fecha_int]):
                if (int(ls.horide or 0) == int(accion.hora_ide or 0)
                        and not (ls.synckey and ls.synckey in mias)):
                    out.append(ls)
        return out

    # ----------------------------- evaluar ----------------------------- #
    def _evaluar(self, ops: Sequence[OpReajuste],
                 prep: dict[int, _Preparada]) -> _Evaluacion:
        claves = {synckey_de(op.registro_id) for op in ops}
        leidas = self._cli.lineas_para_reajuste(claves)
        partes = self._cli.estados_de_partes(
            [ls.hmoide for ls in leidas.values()])
        est = self._est_registro()
        por_rid: dict[int, VeredictoReajuste] = {}
        for op in ops:
            if op.es_nueva:
                continue
            ls = leidas.get(synckey_de(op.registro_id))
            est_parte = (partes.get(int(ls.hmoide or 0), {}).get("est")
                         if ls is not None else None)
            por_rid[op.registro_id] = veredicto_existente(
                op, ls, est_parte, est_registro=est)
        for op in ops:
            if not op.es_nueva:
                continue
            p = prep.get(op.registro_id) or _Preparada(None, None)
            base_rid = int(op.base_registro_id)  # type: ignore[arg-type]
            base_v = por_rid.get(base_rid) or VeredictoReajuste(
                base_rid, editable=False, motivo=MOTIVO_SIN_BASE)
            base_ls = leidas.get(synckey_de(base_rid))
            misma_obra = bool(
                base_ls is not None and p.destino is not None
                and partes.get(int(base_ls.hmoide or 0), {}).get("obride")
                == p.destino.ide)
            escribe = (p.accion is not None and p.destino is not None
                       and p.accion.accion == "escribir")
            choques = (self._choques(p.accion, p.destino, claves)  # type: ignore[arg-type]
                       if escribe else [])
            por_rid[op.registro_id] = veredicto_nueva(
                op, existente=leidas.get(synckey_de(op.registro_id)),
                base=base_v, accion=p.accion, choques=choques,
                misma_obra=misma_obra)
        veredictos = [por_rid[op.registro_id] for op in ops]
        a_escribir = sum(1 for v in veredictos if not v.ya_aplicada)
        sentencias = 1 + a_escribir
        if a_escribir and sentencias > self._max_sentencias():
            motivo = (f"{MOTIVO_DEMASIADAS}: {sentencias} sentencias y el "
                      f"tope es {self._max_sentencias()}")
            veredictos = [VeredictoReajuste(v.registro_id, editable=False,
                                            motivo=motivo)
                          for v in veredictos]
        return _Evaluacion(veredictos, leidas, partes)

    # ----------------------------- comprobar ----------------------------- #
    def comprobar(self, ops: Sequence[OpReajuste]) -> ResultadoReajuste:
        """R20: solo lectura, sin lock. `ok` = todas editables."""
        ev = self._evaluar(ops, self._preparar_nuevas(ops))
        ok = all(v.editable for v in ev.veredictos)
        return ResultadoReajuste(
            ok=ok, ya_aplicada=ok and all(v.ya_aplicada
                                          for v in ev.veredictos),
            veredictos=ev.veredictos, forzada_pruebas=self._forzada())

    # ----------------------------- ejecutar ----------------------------- #
    def ejecutar(self, ops: Sequence[OpReajuste],
                 usuario: str | None = None) -> ResultadoReajuste:
        """R20, R23-R29. `preparar` (datos maestros) fuera del lock; leer,
        decidir y escribir, dentro."""
        prep = self._preparar_nuevas(ops)
        with self.lock:
            return self._ejecutar_bajo_lock(ops, prep, usuario)

    def _ejecutar_bajo_lock(self, ops: Sequence[OpReajuste],
                            prep: dict[int, _Preparada],
                            usuario: str | None) -> ResultadoReajuste:
        ev = self._evaluar(ops, prep)
        if not all(v.editable for v in ev.veredictos):
            no = [v for v in ev.veredictos if not v.editable]
            logger.warning(
                "[reajuste] rechazado: %s de %s linea(s) no editables (%s) "
                "usuario=%s", len(no), len(ops),
                "; ".join(f"registro={v.registro_id}: {v.motivo}"
                          for v in no[:10]), usuario)
            return ResultadoReajuste(
                ok=False, veredictos=ev.veredictos,
                error="hay lineas que no se pueden reajustar",
                forzada_pruebas=self._forzada())
        pendientes = {v.registro_id for v in ev.veredictos
                      if not v.ya_aplicada}
        if not pendientes:
            logger.info("[reajuste] ya aplicado: %s linea(s) sin escribir "
                        "usuario=%s", len(ops), usuario)
            return self._resultado(ops, ev, pendientes=set(), ya=True)

        sentencias, esperadas = self._lote(ops, ev, prep, pendientes)
        fallo: str | None = None
        try:
            filas = self._cli.escribir_lote(sentencias)
            if filas != esperadas:
                fallo = (f"descuadre en Sigrid: filas {filas}, esperadas "
                         f"{esperadas}")
        except Exception as exc:  # noqa: BLE001 - se decide releyendo
            fallo = f"Sigrid no confirmo el reajuste: {exc}"

        # Se decide por lo que hay en Sigrid, no por la respuesta.
        tras = self._evaluar(ops, prep)
        hechas = {v.registro_id for v in tras.veredictos if v.ya_aplicada}
        if pendientes <= hechas:
            if fallo:
                logger.warning("[reajuste] escrito pese al aviso: %s", fallo)
            for op in ops:
                if op.registro_id in pendientes:
                    ls = tras.lineas.get(synckey_de(op.registro_id))
                    logger.info(
                        "[reajuste] linea registro=%s ide=%s antes=%s "
                        "despues=%.2f usuario=%s", op.registro_id,
                        ls.ide if ls else None,
                        "nueva" if op.es_nueva else f"{op.antes:.2f}",
                        op.despues, usuario)
            return self._resultado(ops, tras, pendientes=pendientes, ya=False)
        if not (pendientes & hechas):
            logger.warning("[reajuste] rechazado por Sigrid, nada escrito: "
                           "%s usuario=%s", fallo, usuario)
            return ResultadoReajuste(
                ok=False, veredictos=tras.veredictos,
                error=fallo or "Sigrid no aplico el reajuste",
                forzada_pruebas=self._forzada())
        logger.error(
            "[reajuste] A MEDIAS en Sigrid: escritas %s de %s (%s); revisar "
            "a mano. usuario=%s", sorted(pendientes & hechas),
            sorted(pendientes), fallo, usuario)
        raise RuntimeError(
            f"reajuste a medias en Sigrid: escritas "
            f"{sorted(pendientes & hechas)} de {sorted(pendientes)} ({fallo})")

    def _lote(self, ops: Sequence[OpReajuste], ev: _Evaluacion,
              prep: dict[int, _Preparada],
              pendientes: set[int]) -> tuple[list[dict], list[int]]:
        """Guardia + `UPDATE` + `INSERT` y las filas que debe afectar cada
        sentencia (0 la guardia, 1 las demas)."""
        est = self._est_registro()
        despues = {op.registro_id: float(op.despues) for op in ops}
        existentes = [op for op in ops
                      if op.registro_id in pendientes and not op.es_nueva]
        nuevas = [op for op in ops
                  if op.registro_id in pendientes and op.es_nueva]

        def linea(rid: int) -> LineaSigrid:
            return ev.lineas[synckey_de(rid)]

        sentencias = [self._cli.stmt_guardia_reajuste(
            [(linea(op.registro_id).ide, synckey_de(op.registro_id),
              float(op.antes or 0.0)) for op in existentes],
            nuevas=[synckey_de(op.registro_id) for op in nuevas])]
        for op in existentes:
            sentencias.append(self._cli.stmt_actualizar_linea(
                ide=linea(op.registro_id).ide,
                synckey=synckey_de(op.registro_id),
                antes=float(op.antes or 0.0), despues=float(op.despues),
                est_registro=est))
        pos: dict[int, int] = {}
        tex = (getattr(self._st, "marca_pruebas", None)
               if self._forzada() else None)
        for op in nuevas:
            base_rid = int(op.base_registro_id)  # type: ignore[arg-type]
            base = linea(base_rid)
            hmoide = int(base.hmoide or 0)
            if hmoide not in pos:
                pos[hmoide] = self._cli.max_pos(hmoide)
            pos[hmoide] += int(getattr(self._st, "paso_pos", 64))
            p = prep[op.registro_id]
            a = p.accion
            assert a is not None and p.destino is not None  # editable
            sentencias.append(self._cli.stmt_insertar_extra(
                hmoide=hmoide, obra=p.destino, reside=int(a.recurso_ide),
                pos=pos[hmoide], fecha_int=a.fecha_int,
                horide=int(a.hora_ide), can=float(op.despues),
                pre=float(a.pre or 0.0), paride=int(a.paride or 0),
                ano=a.ano, mes=a.mes, synckey=synckey_de(op.registro_id),
                tex=tex, caaide=int(a.caa_ide), base_ide=base.ide,
                base_synckey=synckey_de(base_rid),
                base_despues=despues[base_rid]))
        return sentencias, [0] + [1] * (len(sentencias) - 1)

    def _resultado(self, ops: Sequence[OpReajuste], ev: _Evaluacion, *,
                   pendientes: set[int], ya: bool) -> ResultadoReajuste:
        """`ok`: una entrada por linea pedida con sus ides de Sigrid (R17)."""
        lineas: list[dict] = []
        for op in ops:
            ls = ev.lineas.get(synckey_de(op.registro_id))
            hmoide = int(ls.hmoide or 0) if ls is not None else None
            lineas.append({
                "registro_id": op.registro_id,
                "hmores_ide": ls.ide if ls is not None else None,
                "hmoide": hmoide,
                "parte_cod": ev.partes.get(hmoide or 0, {}).get("cod"),
                "can": None if ls is None else ls.can,
                "nueva": op.es_nueva,
                "escrita": op.registro_id in pendientes,
            })
        return ResultadoReajuste(ok=True, ya_aplicada=ya,
                                 veredictos=ev.veredictos, lineas=lineas,
                                 forzada_pruebas=self._forzada())
