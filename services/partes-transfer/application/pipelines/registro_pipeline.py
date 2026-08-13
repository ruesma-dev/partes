# application/pipelines/registro_pipeline.py
"""Pipeline de registro de partes en Sigrid.

Dos FASES (F-002), con el corte puesto donde esta la frontera real:

  - `preparar` (pasos 1-4) lee DATOS MAESTROS que sv5 nunca escribe —obra
    destino, recurso por DNI, tipos de hora del recurso (`reshor`)— y
    aplica las reglas de negocio. Es la parte lenta (llamadas a
    sigrid-api) y es segura en paralelo: nada de lo que lee lo cambia
    ninguna escritura nuestra.
  - `registrar` (pasos 5-9) corre BAJO EL LOCK. Los pasos 5-7 leen estado
    que la propia escritura modifica: si se evaluaran fuera, dos
    peticiones a la misma obra y mes propondrian el MISMO correlativo
    `PT<AA>/NNNNN` (dos cabeceras para el mismo parte) y no se verian
    mutuamente como conflicto (horas duplicadas en Sigrid). Por eso el
    lock lo adquiere `registrar` y no sus llamantes: nadie puede
    olvidarlo.

`preflight` y `ejecutar` conservan firma y comportamiento: son la
composicion de las dos fases (`preflight` no toma el lock porque no
escribe y su resultado siempre fue consultivo).

Pasos (patron Pipeline; el preflight ejecuta 1-7 y la escritura 1-9):

  1. Resolver la OBRA DESTINO (en modo pruebas se fuerza a la obra de
     pruebas, ignorando la obra del parte).
  2. Agrupar las lineas por PERIODO (ano/mes de la fecha REAL de trabajo):
     el parte de Sigrid es por obra y mes natural, no por mes de nomina.
  2b. Completar el recurso de las lineas que llegan sin recurso_ide pero
     con DNI (creacion manual antigua): DNI -> res.ide contra Sigrid.
  3. Cargar los tipos de hora de los recursos implicados (reshor).
  4. Aplicar las REGLAS de negocio -> accion por linea.
  5. Localizar el parte de cada periodo; proponer codigo si no existe.
  6. Detectar lineas YA registradas por nosotros (synckey) -> idempotencia.
  7. Detectar CONFLICTOS: ya hay linea(s) en Sigrid para ese parte +
     recurso + fecha -> hay que confirmar si se pisan.
  8. Crear los partes que falten (cabecera + extension).
  9. Borrar las lineas pisadas confirmadas e insertar las nuevas.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone

from application.services.reglas_registro import ReglasRegistro
from domain.models.registro_models import (
    AccionLinea, Conflicto, ContextoRegistro, LineaEntrada, ObraEntrada,
    ParteDestino, Preflight, ResultadoRegistro,
)
from infrastructure.sigrid.sigrid_write_client import synckey_de

logger = logging.getLogger(__name__)


class RegistroPipeline:
    def __init__(self, *, cliente, settings,
                 lock: threading.Lock | None = None) -> None:
        self._cli = cliente
        self._st = settings
        # El lock de escritura viaja por el constructor para que HTTP y
        # consumidores de cola compartan UNO solo dentro de la replica
        # (sv5 va con min=1/max=1: `MAX(ide)+1` exige serializar).
        self._lock = lock if lock is not None else threading.Lock()

    @property
    def lock(self) -> threading.Lock:
        """El lock que serializa la fase de escritura (R7/R19)."""
        return self._lock

    # ------------------------------------------------------------- #
    def _obra_destino(self, obra: ObraEntrada) -> tuple[ObraEntrada, bool]:
        """Paso 1. En pruebas, TODO va a la obra de pruebas."""
        if self._st.obra_pruebas_forzar:
            destino = self._cli.obra_por_codigo(self._st.obra_pruebas_cod)
            if destino is None:
                raise RuntimeError(
                    f"obra de pruebas {self._st.obra_pruebas_cod} no encontrada")
            logger.warning(
                "[registro] MODO PRUEBAS: la obra %s se ignora; se escribe en "
                "%s (%s)", obra.codigo, destino.codigo, destino.nombre)
            return destino, True
        if obra.ide:
            real = self._cli.obra_por_ide(int(obra.ide))
        elif obra.codigo:
            real = self._cli.obra_por_codigo(obra.codigo)
        else:
            real = None
        if real is None:
            raise RuntimeError(
                f"obra no encontrada en Sigrid (ide={obra.ide} "
                f"cod={obra.codigo})")
        return real, False

    # ---------------------- FASE 1: PREPARAR ---------------------- #
    # Pasos 1-4. Solo datos maestros + reglas: paralelizable (R18).
    def preparar(self, *, obra: ObraEntrada,
                 lineas: list[LineaEntrada]) -> ContextoRegistro:
        destino, forzada = self._obra_destino(obra)

        # Paso 2b: lineas sin recurso pero con DNI -> resolver contra
        # Sigrid (red de seguridad para creaciones manuales sin casar).
        import re as _re
        sin_recurso = [l for l in lineas if not l.recurso_ide and l.dni]
        if sin_recurso:
            try:
                mapa = self._cli.resides_por_dni(
                    {l.dni for l in sin_recurso})
            except Exception:  # noqa: BLE001
                logger.warning("[registro] fallo resolviendo recursos por "
                               "DNI; esas lineas se omitiran", exc_info=True)
                mapa = {}
            for l in sin_recurso:
                d = _re.sub(r"[^0-9A-Za-z]", "", l.dni or "").upper()
                if d in mapa:
                    l.recurso_ide = mapa[d]
            logger.info("[registro] recursos resueltos por DNI: %s/%s",
                        sum(1 for l in sin_recurso if l.recurso_ide),
                        len(sin_recurso))

        # Paso 3-4: reglas.
        roles_in = {l.registro_id: l.incidencia_rol
                    for l in lineas if l.es_incidencia}
        if roles_in:
            logger.info("[registro] roles de incidencia RECIBIDOS: %s "
                        "(vacio = el sv4 en ejecucion no calcula la racha)",
                        roles_in)
        horas = self._cli.horas_de_recursos(
            [l.recurso_ide for l in lineas if l.recurso_ide])
        reglas = ReglasRegistro(horas)
        acciones: list[AccionLinea] = [reglas.decidir(l) for l in lineas]
        return ContextoRegistro(
            obra_origen=obra, obra_destino=destino, forzada_pruebas=forzada,
            lineas=lineas, acciones=acciones)

    # ---------------------- FASE 2a: EVALUAR ---------------------- #
    # Pasos 5-7. Leen estado que la escritura modifica: SIEMPRE dentro
    # del lock cuando se va a escribir (R20). `preflight` los usa sin
    # lock a proposito: no escribe y su respuesta es consultiva.
    def _evaluar(self, ctx: ContextoRegistro) -> Preflight:
        destino = ctx.obra_destino
        acciones = ctx.acciones
        escribir = [a for a in acciones if a.accion == "escribir"]

        # Paso 5: parte de cada periodo (ano/mes de la fecha real).
        periodos = {(a.ano, a.mes) for a in escribir}
        partes = self._cli.partes_existentes(int(destino.ide), periodos) \
            if periodos else {}
        for clave in sorted(periodos):
            p = partes.get(clave) or ParteDestino(ano=clave[0], mes=clave[1])
            if not p.existe and not p.cod:
                p.cod = self._cli.siguiente_cod_pt(p.ano)
            partes[clave] = p

        # Paso 6: idempotencia por synckey.
        ya = self._cli.lineas_por_synckey(
            [synckey_de(a.registro_id) for a in escribir])
        for a in acciones:
            hit = ya.get(synckey_de(a.registro_id))
            if a.accion == "escribir" and hit is not None:
                a.accion = "ya_registrado"
                a.hmores_ide = hit.ide
                a.motivo = (f"ya registrada en Sigrid (linea {hit.ide}); "
                            f"no se duplica")

        # Paso 7: conflictos (parte + recurso + fecha ya con lineas).
        conflictos: list[Conflicto] = []
        pendientes = [a for a in acciones if a.accion == "escribir"]
        for clave, parte in sorted(partes.items()):
            if not parte.existe or not parte.ide:
                continue        # parte nuevo: no puede haber conflicto
            grupo = [a for a in pendientes if (a.ano, a.mes) == clave]
            if not grupo:
                continue
            existentes = self._cli.lineas_existentes(
                int(parte.ide), [a.recurso_ide for a in grupo],
                [a.fecha_int for a in grupo])
            mias = {synckey_de(a.registro_id) for a in grupo}
            # Un conflicto es por recurso + dia + CODIGO DE HORA: pisar las
            # ordinarias de un dia NO debe tocar las extra de ese dia.
            por_clave: dict[str, Conflicto] = {}
            for a in grupo:
                k = a.clave_conflicto
                choques = [
                    ls for ls in existentes
                    if ls.reside == a.recurso_ide
                    and ls.fecha_int == a.fecha_int
                    and int(ls.horide or 0) == int(a.hora_ide or 0)
                    and not (ls.synckey and ls.synckey in mias)
                ]
                if not choques:
                    continue        # ese codigo esta libre: nada que pisar
                c = por_clave.get(k)
                if c is None:
                    # Otras lineas del mismo recurso y dia con OTRO codigo:
                    # solo informativas, NO se tocan.
                    contexto = [
                        ls for ls in existentes
                        if ls.reside == a.recurso_ide
                        and ls.fecha_int == a.fecha_int
                        and int(ls.horide or 0) != int(a.hora_ide or 0)
                    ]
                    c = Conflicto(
                        clave=k, recurso_ide=int(a.recurso_ide or 0),
                        fecha_int=a.fecha_int, ano=parte.ano, mes=parte.mes,
                        parte_cod=parte.cod, nombre=a.nombre,
                        horide=a.hora_ide, hora_codigo=a.hora_codigo,
                        lineas=choques, contexto=contexto)
                    por_clave[k] = c
                c.registros.append(a.registro_id)
                c.nuevas.append({
                    "registro_id": a.registro_id, "can": a.can, "tot": a.tot,
                    "hora_codigo": a.hora_codigo, "partida_cod": a.partida_cod,
                })
            conflictos.extend(por_clave.values())

        pf = Preflight(
            obra_destino=destino, obra_origen=ctx.obra_origen,
            forzada_pruebas=ctx.forzada_pruebas,
            partes=[partes[k] for k in sorted(partes)], acciones=acciones,
            conflictos=conflictos)
        logger.info(
            "[registro] preflight obra=%s partes=%s escribir=%s omitir=%s "
            "ya=%s conflictos=%s", destino.codigo, len(pf.partes),
            pf.n_escribir, pf.n_omitir, pf.n_ya, len(conflictos))
        return pf

    # ------------------------------------------------------------- #
    def preflight(self, *, obra: ObraEntrada,
                  lineas: list[LineaEntrada]) -> Preflight:
        """Analisis consultivo: que se haria. No escribe, no toma lock."""
        return self._evaluar(self.preparar(obra=obra, lineas=lineas))

    # --------------------- FASE 2b: REGISTRAR --------------------- #
    def registrar(self, ctx: ContextoRegistro, *,
                  pisar_claves: set[str] | None = None,
                  usuario: str | None = None) -> ResultadoRegistro:
        """Evalua el estado escrito y escribe, todo bajo el MISMO lock.

        Que la evaluacion entre dentro del lock es lo que garantiza R20:
        entre que se lee el parte, el correlativo, las synckeys y los
        conflictos y se termina de escribir, ninguna otra escritura
        —de cola o de HTTP— toca Sigrid.
        """
        if ctx is None:
            raise ValueError(
                "registrar necesita el ContextoRegistro de preparar(...)")
        with self._lock:
            return self._registrar_bajo_lock(
                ctx, pisar_claves=pisar_claves, usuario=usuario)

    def _registrar_bajo_lock(self, ctx: ContextoRegistro, *,
                             pisar_claves: set[str] | None,
                             usuario: str | None) -> ResultadoRegistro:
        pisar = {str(k) for k in (pisar_claves or set())}
        pf = self._evaluar(ctx)
        destino = pf.obra_destino

        res = ResultadoRegistro(
            ok=True, obra_destino=destino, forzada_pruebas=pf.forzada_pruebas,
            partes=pf.partes,
            omitidas=[{"registro_id": a.registro_id, "motivo": a.motivo}
                      for a in pf.acciones if a.accion == "omitir"],
            ya_registradas=[a.registro_id for a in pf.acciones
                            if a.accion == "ya_registrado"],
        )

        # Conflictos NO confirmados -> esas lineas no se tocan.
        bloqueadas: set[int] = set()
        for c in pf.conflictos:
            if c.clave in pisar:
                res.pisadas.append(c.clave)
            else:
                res.pendientes_confirmacion.append(c)
                bloqueadas.update(c.registros)

        a_escribir = [a for a in pf.acciones
                      if a.accion == "escribir"
                      and a.registro_id not in bloqueadas]
        if not a_escribir:
            logger.info("[registro] nada que escribir (bloqueadas=%s)",
                        len(bloqueadas))
            return res

        # Paso 8: crear los partes que falten.
        por_periodo = {(p.ano, p.mes): p for p in pf.partes}
        for clave in sorted({(a.ano, a.mes) for a in a_escribir}):
            p = por_periodo[clave]
            if p.existe and p.ide:
                continue
            marca = (f" ({self._st.marca_pruebas})" if pf.forzada_pruebas
                     else "")
            desc = f"Parte {destino.nombre or destino.codigo}{marca}"
            cod = p.cod or self._cli.siguiente_cod_pt(p.ano)
            self._cli.escribir(self._cli.stmts_crear_parte(
                obra=destino, ano=p.ano, mes=p.mes, cod=cod, desc=desc))
            nuevos = self._cli.partes_existentes(int(destino.ide), [clave])
            creado = nuevos.get(clave)
            if creado is None or not creado.ide:
                raise RuntimeError(f"no se pudo crear el parte {cod}")
            p.existe, p.ide, p.cod, p.creado = True, creado.ide, creado.cod, True
            logger.info("[registro] parte creado %s (ide=%s) obra=%s %s/%s",
                        p.cod, p.ide, destino.codigo, p.ano, p.mes)

        # Paso 9: borrar pisadas + insertar.
        statements: list[dict] = []
        for c in pf.conflictos:
            if c.clave not in pisar:
                continue
            for ls in c.lineas:
                statements.append(self._cli.stmt_borrar_linea(ls.ide))
                res.borradas += 1

        pos_por_parte: dict[int, int] = {}
        tex = self._st.marca_pruebas if pf.forzada_pruebas else None
        for a in sorted(a_escribir, key=lambda x: (x.ano, x.mes, x.fecha_int,
                                                   x.registro_id)):
            p = por_periodo[(a.ano, a.mes)]
            hmoide = int(p.ide)
            if hmoide not in pos_por_parte:
                pos_por_parte[hmoide] = self._cli.max_pos(hmoide)
            pos_por_parte[hmoide] += int(self._st.paso_pos)
            statements.append(self._cli.stmt_insert_linea(
                hmoide=hmoide, obra=destino, reside=int(a.recurso_ide),
                pos=pos_por_parte[hmoide], fecha_int=a.fecha_int,
                horide=int(a.hora_ide), can=float(a.can), pre=float(a.pre),
                paride=int(a.paride or 0), ano=a.ano, mes=a.mes,
                synckey=synckey_de(a.registro_id), tex=tex))
            res.escritas.append({"registro_id": a.registro_id,
                                 "hmoide": hmoide, "parte_cod": p.cod,
                                 "hora_codigo": a.hora_codigo,
                                 "can": a.can, "tot": a.tot})

        afectadas = self._cli.escribir(statements)
        logger.info("[registro] escritas=%s borradas=%s filas=%s usuario=%s "
                    "ts=%s", len(res.escritas), res.borradas, afectadas,
                    usuario, datetime.now(timezone.utc).isoformat())

        # Devolver el ide real de cada linea creada (para trazabilidad).
        mapa = self._cli.lineas_por_synckey(
            [synckey_de(e["registro_id"]) for e in res.escritas])
        for e in res.escritas:
            hit = mapa.get(synckey_de(e["registro_id"]))
            if hit is not None:
                e["hmores_ide"] = hit.ide
        return res

    # ------------------------------------------------------------- #
    def ejecutar(self, *, obra: ObraEntrada, lineas: list[LineaEntrada],
                 pisar_claves: set[str] | None = None,
                 usuario: str | None = None) -> ResultadoRegistro:
        """Las dos fases seguidas (firma y comportamiento de siempre)."""
        ctx = self.preparar(obra=obra, lineas=lineas)
        return self.registrar(ctx, pisar_claves=pisar_claves, usuario=usuario)
