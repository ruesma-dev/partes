# application/pipelines/franquicia_pipeline.py
"""F-056 · Franquicia de extras: la linea de ajuste en Sigrid (sv5).

El ultimo laborable del mes de nomina de un trabajador con franquicia X,
sv4 pide a sv5 la linea `HE*` negativa que deja sus extras netas del
periodo E en `max(E - X, 0)` (A = `franquicia.ajuste_objetivo`). Dos
operaciones (R22):

  - `comprobar`: SOLO LECTURA y sin lock (el aviso del modal). Suma
    ademas `extras_pendientes` (las extras de esta aprobacion que aun no
    estan en Sigrid) para el A estimado. `ajuste_id` 0 = aun no hay fila
    en sv4: no se busca linea.
  - `ejecutar`: `preparar` la extra del recurso (datos maestros: obra
    destino y modo pruebas, verificacion F-023, reglas y cuenta F-021)
    FUERA del lock; dentro del MISMO lock que el registro, lee E y la
    linea por su synckey `partes:franquicia:<id>`, decide
    (`franquicia.veredicto`) y escribe UNA sentencia:

        crear       `INSERT` en el parte En registro de la obra y mes
                    natural del dia (el de mayor `ide`, F-031; si no hay,
                    alta protegida via `RegistroPipeline.asegurar_parte`),
                    con `tex` explicativo (la marca en modo pruebas, R32);
        actualizar  `UPDATE` de `can` y `tot` con `WHERE` optimista, guarda
                    de parte abierto y sin enlaces; A = 0 deja la linea a 0.

    Despues RELEE por synckey y responde por lo releido (R29): `ok` solo si
    la linea esta en el parte elegido con `can` = A.

[E] R26: ninguna sentencia de F-056 es un `DELETE` (solo `INSERT`, `UPDATE`
y el alta del parte). R33: logs con ids, horas y usuario; nunca nombres ni
DNIs.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from application.pipelines.registro_pipeline import RegistroPipeline
from application.services import franquicia as fr
from application.services.estado_parte import elegir_parte
from domain.models.registro_models import (
    AccionLinea,
    LineaEntrada,
    LineaSigrid,
    ObraEntrada,
    ParteDestino,
    PeticionFranquicia,
    ResultadoFranquicia,
    VeredictoFranquicia,
)
from infrastructure.sigrid.sigrid_write_client import synckey_franquicia

logger = logging.getLogger(__name__)

#: R29: la linea no esta en Sigrid como se pidio tras escribir.
MOTIVO_NO_CONFIRMADA = "Sigrid no confirmo la linea de ajuste"

#: Horas de la extra que se pasa a `preparar`: solo sirve para que las
#: reglas decidan codigo, precio y cuenta (una linea sin horas se omite);
#: la cantidad real es A, que se calcula dentro del lock.
_HORAS_PREPARAR = -1.0


@dataclass
class _Preparada:
    """Lo que `preparar` del registro decidio (datos maestros)."""
    accion: AccionLinea | None
    destino: ObraEntrada
    forzada: bool


@dataclass
class _Evaluacion:
    """Lo leido en Sigrid y lo decidido para una peticion."""
    extras: float
    objetivo: float
    linea: LineaSigrid | None
    parte_linea: dict
    elegido: ParteDestino
    veredicto: VeredictoFranquicia


class FranquiciaPipeline:
    def __init__(self, *, cliente, settings,
                 registro: RegistroPipeline) -> None:
        self._cli = cliente
        self._st = settings
        self._reg = registro

    @property
    def lock(self):
        """El MISMO lock que el registro (R22): una sola escritura a la vez
        en Sigrid, venga del registro, de la cola, del reajuste o de aqui."""
        return self._reg.lock

    # ------------------------------------------------------------- #
    def _est_registro(self) -> int:
        return int(getattr(self._st, "est_parte_activo", 1))

    def _preparar(self, p: PeticionFranquicia) -> _Preparada:
        """Una extra del recurso el dia de ajuste por `preparar` del
        registro: obra destino (modo pruebas), verificacion F-023, codigo
        `HE*` y precio de `reshor` y cuenta F-021 (R24, R30, R32)."""
        ctx = self._reg.preparar(obra=p.obra, lineas=[LineaEntrada(
            registro_id=int(p.ajuste_id), fecha_int=int(p.fecha_int),
            recurso_ide=int(p.recurso_ide), tipo_hora="extra",
            horas=_HORAS_PREPARAR, partida_ide=p.partida_ide,
            partida_cod=p.partida_cod)])
        accion = ctx.acciones[0] if ctx.acciones else None
        return _Preparada(accion, ctx.obra_destino, ctx.forzada_pruebas)

    def _evaluar(self, p: PeticionFranquicia, prep: _Preparada, *,
                 pendientes: float) -> _Evaluacion:
        """Lee E, la linea de ajuste y su parte, y los partes del mes del
        dia en la obra destino; decide con `franquicia.veredicto`."""
        sk = synckey_franquicia(p.ajuste_id)
        extras = float(self._cli.extras_del_periodo(
            int(p.recurso_ide), int(p.inicio), int(p.fin), sk))
        objetivo = fr.ajuste_objetivo(extras + float(pendientes or 0.0),
                                      p.franquicia)
        linea = (self._cli.lineas_para_reajuste([sk]).get(sk)
                 if p.ajuste_id else None)
        parte_linea: dict = {}
        if linea is not None:
            parte_linea = self._cli.estados_de_partes(
                [linea.hmoide]).get(int(linea.hmoide or 0), {})
        est = self._est_registro()
        elegido = elegir_parte(
            p.ano, p.mes,
            self._cli.partes_del_periodo(int(prep.destino.ide), p.ano,
                                         p.mes),
            est_registro=est)
        v = fr.veredicto(linea, parte_linea.get("est"), objetivo,
                         est_registro=est, accion=prep.accion,
                         parte_cod=parte_linea.get("cod"))
        return _Evaluacion(extras, objetivo, linea, parte_linea, elegido, v)

    def _resultado(self, ev: _Evaluacion, prep: _Preparada, *, ok: bool,
                   escrita: bool = False, motivo: str | None = None,
                   error: str | None = None) -> ResultadoFranquicia:
        a = prep.accion
        linea = ev.linea
        if linea is not None:
            hmoide = int(linea.hmoide or 0) or None
            parte_cod = ev.parte_linea.get("cod")
            parte_estado = ev.parte_linea.get("est")
        else:
            hmoide, parte_cod = ev.elegido.ide, ev.elegido.cod
            parte_estado = ev.elegido.estado
        return ResultadoFranquicia(
            ok=ok, accion=ev.veredicto.accion, extras=ev.extras,
            objetivo=ev.objetivo,
            actual=None if linea is None else float(linea.can or 0.0),
            hmores_ide=None if linea is None else linea.ide, hmoide=hmoide,
            parte_cod=parte_cod, parte_estado=parte_estado,
            complementario=ev.elegido.complementario,
            hora_codigo=None if a is None else a.hora_codigo,
            pre=None if a is None or a.pre is None else float(a.pre),
            motivo=motivo, escrita=escrita, forzada_pruebas=prep.forzada,
            error=error)

    # ----------------------------- comprobar ----------------------------- #
    def comprobar(self, p: PeticionFranquicia) -> ResultadoFranquicia:
        """R22, R23: solo lectura y sin lock. `ok` = se puede ajustar."""
        prep = self._preparar(p)
        ev = self._evaluar(p, prep, pendientes=p.extras_pendientes)
        ok = ev.veredicto.accion != fr.NO_EDITABLE
        logger.info(
            "[franquicia] comprobar ajuste=%s recurso=%s periodo=%s "
            "extras=%.2f pendientes=%.2f objetivo=%.2f accion=%s usuario=%s",
            p.ajuste_id, p.recurso_ide, p.periodo, ev.extras,
            float(p.extras_pendientes or 0.0), ev.objetivo,
            ev.veredicto.accion, p.usuario)
        return self._resultado(ev, prep, ok=ok, motivo=ev.veredicto.motivo)

    # ----------------------------- ejecutar ----------------------------- #
    def ejecutar(self, p: PeticionFranquicia,
                 usuario: str | None = None) -> ResultadoFranquicia:
        """R22-R30: `preparar` fuera del lock; leer, decidir, escribir y
        releer, dentro. `extras_pendientes` no cuenta: E es lo que ya esta
        en Sigrid."""
        if not p.ajuste_id or int(p.ajuste_id) <= 0:
            raise ValueError("ejecutar necesita el ajuste_id de la fila de "
                             "sv4 (el 0 solo vale para comprobar)")
        usuario = usuario if usuario is not None else p.usuario
        prep = self._preparar(p)
        with self.lock:
            return self._ejecutar_bajo_lock(p, prep, usuario)

    def _ejecutar_bajo_lock(self, p: PeticionFranquicia, prep: _Preparada,
                            usuario: str | None) -> ResultadoFranquicia:
        ev = self._evaluar(p, prep, pendientes=0.0)
        v = ev.veredicto
        if v.accion == fr.NO_EDITABLE:
            logger.warning(
                "[franquicia] no editable ajuste=%s recurso=%s periodo=%s "
                "objetivo=%.2f motivo=%s usuario=%s", p.ajuste_id,
                p.recurso_ide, p.periodo, ev.objetivo, v.motivo, usuario)
            return self._resultado(ev, prep, ok=False, motivo=v.motivo,
                                   error=v.motivo)
        if v.accion in (fr.YA_APLICADO, fr.SIN_AJUSTE):
            logger.info(
                "[franquicia] %s ajuste=%s recurso=%s periodo=%s "
                "extras=%.2f objetivo=%.2f usuario=%s", v.accion,
                p.ajuste_id, p.recurso_ide, p.periodo, ev.extras,
                ev.objetivo, usuario)
            return self._resultado(ev, prep, ok=True)

        sk = synckey_franquicia(p.ajuste_id)
        if v.accion == fr.CREAR:
            hmoide = self._parte_para_crear(ev, prep)
            sentencia = self._insert(p, prep, ev, sk, hmoide)
        else:
            assert ev.linea is not None                  # actualizar
            hmoide = int(ev.linea.hmoide or 0)
            sentencia = self._cli.stmt_actualizar_linea(
                ide=ev.linea.ide, synckey=sk,
                antes=float(ev.linea.can or 0.0), despues=ev.objetivo,
                est_registro=self._est_registro())
        fallo: str | None = None
        try:
            self._cli.escribir([sentencia])
        except Exception as exc:  # noqa: BLE001 - se decide releyendo
            fallo = f"Sigrid no confirmo la escritura: {exc}"

        # R29: se decide por lo que hay en Sigrid, no por la respuesta.
        tras = self._cli.lineas_para_reajuste([sk]).get(sk)
        if tras is not None:
            ev.linea = tras
            ev.parte_linea = self._cli.estados_de_partes(
                [tras.hmoide]).get(int(tras.hmoide or 0), {})
        escrita = (tras is not None and int(tras.hmoide or 0) == hmoide
                   and fr._igual(tras.can, ev.objetivo))
        if escrita:
            if fallo:
                logger.warning("[franquicia] escrito pese al aviso: %s",
                               fallo)
            logger.info(
                "[franquicia] %s ajuste=%s ide=%s hmoide=%s recurso=%s "
                "periodo=%s fecha=%s extras=%.2f franquicia=%.2f "
                "objetivo=%.2f usuario=%s", v.accion, p.ajuste_id, tras.ide,
                hmoide, p.recurso_ide, p.periodo, p.fecha_int, ev.extras,
                float(p.franquicia), ev.objetivo, usuario)
            return self._resultado(ev, prep, ok=True, escrita=True)
        motivo = fallo or (
            f"{MOTIVO_NO_CONFIRMADA} en el parte {hmoide} con "
            f"{ev.objetivo:.2f} h")
        logger.warning(
            "[franquicia] no escrita ajuste=%s recurso=%s periodo=%s "
            "objetivo=%.2f motivo=%s usuario=%s", p.ajuste_id, p.recurso_ide,
            p.periodo, ev.objetivo, motivo, usuario)
        return self._resultado(ev, prep, ok=False, motivo=motivo,
                               error=motivo)

    def _parte_para_crear(self, ev: _Evaluacion, prep: _Preparada) -> int:
        """R24: el parte En registro elegido o, si no hay, el alta
        protegida del registro (que relee y adopta el del otro servicio)."""
        p = ev.elegido
        if not (p.existe and p.ide):
            p.cod = self._cli.siguiente_cod_pt(
                p.ano, int(prep.destino.empresa))  # type: ignore[arg-type]
            self._reg.asegurar_parte(p, prep.destino)
        return int(p.ide)  # type: ignore[arg-type]

    def _insert(self, p: PeticionFranquicia, prep: _Preparada,
                ev: _Evaluacion, sk: str, hmoide: int) -> dict:
        """R24: la linea de ajuste, con las columnas del registro."""
        a = prep.accion
        assert a is not None                              # editable
        tex = (getattr(self._st, "marca_pruebas", None) if prep.forzada
               else fr.texto_ajuste(p.periodo, ev.objetivo, p.franquicia))
        pos = self._cli.max_pos(hmoide) + int(getattr(self._st, "paso_pos",
                                                      64))
        return self._cli.stmt_insert_linea(
            hmoide=hmoide, obra=prep.destino, reside=int(p.recurso_ide),
            pos=pos, fecha_int=int(p.fecha_int), horide=int(a.hora_ide),
            can=ev.objetivo, pre=float(a.pre or 0.0),
            paride=int(a.paride or 0), ano=p.ano, mes=p.mes, synckey=sk,
            tex=tex, caaide=int(a.caa_ide))
