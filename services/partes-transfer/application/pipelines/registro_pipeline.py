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
     pruebas, ignorando la obra del parte) y SU EMPRESA: sin empresa no se
     escribe nada (F-023, R35).
  2. Agrupar las lineas por PERIODO (ano/mes de la fecha REAL de trabajo):
     el parte de Sigrid es por obra y mes natural, no por mes de nomina.
  2b. Completar el recurso de las lineas que llegan sin recurso_ide pero
     con DNI (creacion manual antigua): un UNICO recurso de alta de esa
     empresa a la fecha de la linea (R37).
  2c. Verificar el recurso de las demas: de la empresa de la obra, de alta
     a la fecha de la linea y de esa persona (R36). Si no, se omite.
  3. Cargar los tipos de hora de los recursos implicados (reshor).
  4. Aplicar las REGLAS de negocio -> accion por linea. F-019: con el
     interruptor MENSUALES_A_DEDICACION, las de un mensual (`M*`) salen
     como `dedicacion`: no se escriben, no abren parte, no piden cuenta ni
     entran en conflictos; viajan en `ResultadoRegistro.dedicacion`.
  4b. Resolver la CUENTA ANALITICA de cada accion `escribir` (F-021): la
     subcuenta de la ficha del recurso para el tipo de hora escrito (o su
     tipo por defecto) en el centro de la obra destino, con UNA lectura de
     cuentas por peticion. Sin cuenta, `caa_ide = 0` y se escribe igual;
     si la lectura falla, la peticion entera falla (nada se escribe).
     F-031 (R20-R26): si el recurso no da subcuenta, la de la PARTIDA de
     la linea si es de coste (`CI*`/`CD*`), con una lectura de partidas
     por peticion y solo si hace falta.
  5. Elegir el parte de cada periodo (F-031): se leen TODOS los partes de
     la obra y mes con su estado; sv5 solo escribe en uno En registro (el
     de mayor `ide`). Si el periodo tiene partes cerrados (Cerrado,
     Imputado...), el elegido es el COMPLEMENTARIO; si ninguno esta En
     registro, se propone uno nuevo con el codigo de siempre.
  6. Detectar lineas YA registradas por nosotros (synckey) -> idempotencia.
     Tambien las `dedicacion`: si ya viven en Sigrid, Sigrid manda (R5).
  7. Detectar CONFLICTOS en TODOS los partes del periodo (F-031): si la
     linea ya tiene horas ajenas de ese recurso, dia y tipo en un parte
     CERRADO, se omite (`parte_cerrado: ...`); si las tiene en uno En
     registro, hay que confirmar si se pisan.
  8. Crear los partes que falten (cabecera + extension) y releerlos: si el
     creado no sale En registro con su codigo, no se inserta nada.
  9. Borrar las lineas pisadas confirmadas e insertar las nuevas, solo en
     el parte elegido. sv5 no toca `con`/`hmo` de un parte existente ni
     escribe asientos (F-031, R5, R31).
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone

from application.services.coherencia_recurso import (
    elegir_por_dni,
    verificar_recurso,
)
from application.services.cuenta_analitica import (
    MOTIVO_CUENTA_AMBIGUA,
    MOTIVO_OBRA_SIN_CUENTA,
    MOTIVO_RECURSO_SIN_CUENTA,
    origen_subcuenta,
    resolver_cuenta,
    subcuenta_de_linea,
)
from application.services.estado_parte import (
    aviso_de_parte,
    elegir_parte,
    motivo_choque,
    nombre_estado,
)
from application.services.reglas_registro import ReglasRegistro
from domain.models.registro_models import (
    AccionLinea,
    Conflicto,
    ContextoRegistro,
    HoraRecurso,
    LineaEntrada,
    ObraEntrada,
    LineaSigrid,
    ParteDestino,
    ParteSigrid,
    Preflight,
    ResultadoRegistro,
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

    def _con_empresa(self, obra: ObraEntrada) -> tuple[ObraEntrada, bool]:
        """Paso 1 completo: la obra destino tiene que tener empresa (R35).

        La cabecera, el correlativo y la verificacion de recursos son de
        esa empresa: sin ella no hay nada seguro que escribir."""
        destino, forzada = self._obra_destino(obra)
        if destino.empresa is None:
            raise RuntimeError(
                f"la obra {destino.codigo} no tiene empresa en Sigrid: no se "
                f"escribe nada")
        return destino, forzada

    # ---------------------- FASE 1: PREPARAR ---------------------- #
    # Pasos 1-4. Solo datos maestros + reglas: paralelizable (R18).
    def preparar(self, *, obra: ObraEntrada,
                 lineas: list[LineaEntrada]) -> ContextoRegistro:
        destino, forzada = self._con_empresa(obra)
        empresa = int(destino.empresa)  # type: ignore[arg-type]
        # Lineas que se omiten ANTES de las reglas, con el motivo concreto
        # de la comprobacion que fallo (R36-R37).
        omisiones: dict[int, str] = {}
        con_recurso = [l for l in lineas if l.recurso_ide]

        # Paso 2b: lineas sin recurso pero con DNI -> un unico candidato de
        # la empresa de la obra a la fecha de la linea (R37).
        import re as _re
        sin_recurso = [l for l in lineas if not l.recurso_ide and l.dni]
        if sin_recurso:
            try:
                mapa = self._cli.recursos_por_dni(
                    {l.dni for l in sin_recurso})
            except Exception:  # noqa: BLE001
                logger.warning("[registro] fallo resolviendo recursos por "
                               "DNI; esas lineas se omitiran", exc_info=True)
                mapa = None
            if mapa is not None:
                for l in sin_recurso:
                    d = _re.sub(r"[^0-9A-Za-z]", "", l.dni or "").upper()
                    reside, motivo = elegir_por_dni(
                        mapa.get(d, []), empresa, l.fecha_int)
                    if reside is None:
                        omisiones[l.registro_id] = motivo  # type: ignore[assignment]
                    l.recurso_ide = reside
            logger.info("[registro] recursos resueltos por DNI: %s/%s",
                        sum(1 for l in sin_recurso if l.recurso_ide),
                        len(sin_recurso))

        # Paso 2c: el recurso que llega se verifica (R36). Si Sigrid no
        # responde, la peticion falla entera: nada se escribe sin verificar.
        if con_recurso:
            datos = self._cli.datos_recursos(
                [l.recurso_ide for l in con_recurso])
            for l in con_recurso:
                motivo = verificar_recurso(
                    datos.get(int(l.recurso_ide)), empresa, l.fecha_int,
                    l.dni)
                if motivo is not None:
                    omisiones[l.registro_id] = motivo
            if omisiones:
                logger.warning(
                    "[registro] obra=%s empresa=%s: %s linea(s) omitidas por "
                    "el recurso: %s", destino.codigo, empresa,
                    len(omisiones), omisiones)

        # Paso 3-4: reglas.
        roles_in = {l.registro_id: l.incidencia_rol
                    for l in lineas if l.es_incidencia}
        if roles_in:
            logger.info("[registro] roles de incidencia RECIBIDOS: %s "
                        "(vacio = el sv4 en ejecucion no calcula la racha)",
                        roles_in)
        horas = self._cli.horas_de_recursos(
            [l.recurso_ide for l in lineas if l.recurso_ide])
        # F-019 (DA8): un settings sin el ajuste (anterior a F-019) es
        # el interruptor apagado.
        reglas = ReglasRegistro(
            horas, omisiones=omisiones,
            mensuales_a_dedicacion=bool(getattr(
                self._st, "mensuales_a_dedicacion", False)))
        acciones: list[AccionLinea] = [reglas.decidir(l) for l in lineas]
        # Paso 4b: cuenta analitica (F-021). Datos maestros: fuera del lock.
        self._resolver_cuentas(destino, empresa, acciones, horas)
        return ContextoRegistro(
            obra_origen=obra, obra_destino=destino, forzada_pruebas=forzada,
            lineas=lineas, acciones=acciones)

    def _resolver_cuentas(self, destino: ObraEntrada, empresa: int,
                          acciones: list[AccionLinea],
                          horas: dict[int, list[HoraRecurso]]) -> None:
        """Paso 4b (F-021, R1-R13, R18): `caa_*` de cada accion `escribir`.

        Las demas se quedan con `caa_ide = 0` y sin motivo (R16). Las
        lecturas de partidas y de cuentas van SIN `try`: si fallan, la
        peticion falla y no se escribe nada (R11, DA7; F-031 R24); por cola
        sv4 marca las lineas en error hasta que se reaprueban. Escribir 0
        en silencio es justo el defecto que se corrige.

        F-031 (R20-R26): la subcuenta sale del recurso; solo si no da, de
        la partida de coste de la linea (`origen_subcuenta`). Las partidas
        se leen UNA vez y solo si alguna accion las necesita."""
        # Una accion `escribir` siempre trae recurso (las reglas omiten las
        # que no lo tienen).
        escribir = [a for a in acciones if a.accion == "escribir"]
        if not escribir:
            return

        def horas_de(a: AccionLinea) -> list[HoraRecurso]:
            return horas.get(int(a.recurso_ide), [])

        parides = {int(a.paride) for a in escribir
                   if a.paride and not subcuenta_de_linea(horas_de(a),
                                                          a.hora_ide)}
        partidas = self._cli.partidas_de_lineas(parides) if parides else {}
        origenes = {id(a): origen_subcuenta(
                        horas_de(a), a.hora_ide,
                        partidas.get(int(a.paride or 0)))
                    for a in escribir}
        cenide = int(getattr(destino, "cenide", 0) or 0)
        pedidas = {o.sub for o in origenes.values() if o.sub}
        cuentas = (self._cli.cuentas_de_centro(cenide, empresa, pedidas)
                   if pedidas and cenide else {})
        recuento = {None: 0, MOTIVO_RECURSO_SIN_CUENTA: 0,
                    MOTIVO_OBRA_SIN_CUENTA: 0, MOTIVO_CUENTA_AMBIGUA: 0}
        por_origen = {"recurso": 0, "partida": 0, None: 0}
        for a in escribir:
            o = origenes[id(a)]
            c = resolver_cuenta(o.sub, cuentas, destino.codigo)
            a.caa_ide, a.caa_cod = c.caa_ide, c.caa_cod
            a.caa_motivo, a.caa_aviso = c.motivo, c.aviso
            a.caa_origen, a.caa_nota = o.origen, o.nota
            recuento[c.motivo] += 1
            por_origen[o.origen] += 1
        logger.info(
            "[registro] cuentas obra=%s ok=%s recurso_sin_cuenta=%s "
            "obra_sin_cuenta=%s cuenta_ambigua=%s", destino.codigo,
            recuento[None], recuento[MOTIVO_RECURSO_SIN_CUENTA],
            recuento[MOTIVO_OBRA_SIN_CUENTA],
            recuento[MOTIVO_CUENTA_AMBIGUA])
        logger.info(
            "[registro] origen cuenta obra=%s recurso=%s partida=%s "
            "ninguna=%s", destino.codigo, por_origen["recurso"],
            por_origen["partida"], por_origen[None])

    # ---------------------- FASE 2a: EVALUAR ---------------------- #
    # Pasos 5-7. Leen estado que la escritura modifica: SIEMPRE dentro
    # del lock cuando se va a escribir (R20). `preflight` los usa sin
    # lock a proposito: no escribe y su respuesta es consultiva.
    def _evaluar(self, ctx: ContextoRegistro) -> Preflight:
        destino = ctx.obra_destino
        acciones = ctx.acciones
        escribir = [a for a in acciones if a.accion == "escribir"]

        # Paso 5: parte de cada periodo (ano/mes de la fecha real). F-031:
        # TODOS los partes del periodo con su estado, UNA lectura por
        # periodo (R1); el elegido es el de mayor `ide` En registro (R2).
        est_registro = self._est_registro()
        periodos = {(a.ano, a.mes) for a in escribir}
        partes: dict[tuple[int, int], ParteDestino] = {}
        for clave in sorted(periodos):
            p = elegir_parte(
                clave[0], clave[1],
                self._cli.partes_del_periodo(int(destino.ide), *clave),
                est_registro=est_registro)
            if not p.existe:
                p.cod = self._cli.siguiente_cod_pt(
                    p.ano, int(destino.empresa))  # type: ignore[arg-type]
            p.aviso = aviso_de_parte(p, {
                ps.cod: self._nombre_estado(ps.est) for ps in p.del_periodo
                if ps.est != est_registro})
            partes[clave] = p

        # Paso 6: idempotencia por synckey. F-019 (R5): una `dedicacion`
        # que ya esta en Sigrid es `ya_registrado` (nada se cuenta dos
        # veces).
        consultables = [a for a in acciones
                        if a.accion in ("escribir", "dedicacion")]
        ya = self._cli.lineas_por_synckey(
            [synckey_de(a.registro_id) for a in consultables])
        for a in consultables:
            hit = ya.get(synckey_de(a.registro_id))
            if hit is not None:
                a.accion = "ya_registrado"
                a.hmores_ide = hit.ide
                a.motivo = (f"ya registrada en Sigrid (linea {hit.ide}); "
                            f"no se duplica")

        # Paso 7: conflictos en TODOS los partes del periodo (F-031). Un
        # parte nuevo sin partes previos no puede tener conflicto.
        conflictos: list[Conflicto] = []
        pendientes = [a for a in acciones if a.accion == "escribir"]
        omitidas_cerrado: dict[tuple[int, int], int] = {}
        for clave, parte in sorted(partes.items()):
            grupo = [a for a in pendientes if (a.ano, a.mes) == clave]
            omitidas_cerrado[clave] = 0
            if not grupo or not parte.del_periodo:
                continue
            recursos = [a.recurso_ide for a in grupo]
            fechas = [a.fecha_int for a in grupo]
            existentes = [(ps, self._cli.lineas_existentes(
                int(ps.ide), recursos, fechas)) for ps in parte.del_periodo]
            mias = {synckey_de(a.registro_id) for a in grupo}
            # R11 (prevalece sobre R12): horas que ya constan en un parte
            # CERRADO -> esa linea no se registra.
            for a in grupo:
                cerrado = next(
                    (ps for ps, lineas in existentes
                     if ps.est != est_registro
                     and self._choques(lineas, a, mias)), None)
                if cerrado is not None:
                    self._omitir_por_cerrado(a, cerrado)
                    omitidas_cerrado[clave] += 1
            grupo = [a for a in grupo if a.accion == "escribir"]
            abiertas = [(ps, lineas) for ps, lineas in existentes
                        if ps.est == est_registro]
            conflictos.extend(self._conflictos(parte, grupo, abiertas, mias))

        for clave, parte in sorted(partes.items()):
            # R19: sin nombres ni DNIs.
            logger.info(
                "[registro] parte obra=%s periodo=%s/%02d elegido=%s "
                "estado=%s complementario=%s cerrados=%s "
                "omitidas_cerrado=%s", destino.codigo, clave[0], clave[1],
                parte.cod, parte.estado,
                "si" if parte.complementario else "no",
                len(parte.cerrados), omitidas_cerrado[clave])

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

    # ---------------- ayudas de los pasos 5-8 (F-031) ---------------- #
    def _est_registro(self) -> int:
        """R7: «En registro» sale de `EST_PARTE_ACTIVO` (un settings sin
        el ajuste, como los dobles antiguos, es el 1 de siempre)."""
        return int(getattr(self._st, "est_parte_activo", 1))

    def _nombre_estado(self, est: int | None) -> str:
        """R7: nombre de un estado cerrado para los textos (DA7)."""
        return nombre_estado(
            est, est_cerrado=int(getattr(self._st, "est_parte_cerrado", 3)),
            est_imputado=int(getattr(self._st, "est_parte_imputado", 10)))

    @staticmethod
    def _choques(lineas: list[LineaSigrid], a: AccionLinea,
                 mias: set[str]) -> list[LineaSigrid]:
        """Lineas AJENAS del mismo recurso, dia y CODIGO DE HORA: pisar las
        ordinarias de un dia NO debe tocar las extra de ese dia."""
        return [ls for ls in lineas
                if ls.reside == a.recurso_ide
                and ls.fecha_int == a.fecha_int
                and int(ls.horide or 0) == int(a.hora_ide or 0)
                and not (ls.synckey and ls.synckey in mias)]

    def _omitir_por_cerrado(self, a: AccionLinea, ps: ParteSigrid) -> None:
        """R11, R14: la linea no se registra y no lleva cuenta."""
        a.accion = "omitir"
        a.motivo = motivo_choque(ps.cod, self._nombre_estado(ps.est))
        a.caa_ide, a.caa_cod = 0, None
        a.caa_motivo = a.caa_aviso = a.caa_origen = a.caa_nota = None

    def _conflictos(
        self, parte: ParteDestino, grupo: list[AccionLinea],
        abiertas: list[tuple[ParteSigrid, list[LineaSigrid]]],
        mias: set[str],
    ) -> list[Conflicto]:
        """R12-R13: choques con lineas ajenas de partes En registro (el
        elegido u otro), confirmables como siempre. `parte_cod` es el del
        parte donde viven; solo estas lineas se pueden pisar."""
        por_clave: dict[str, Conflicto] = {}
        for a in grupo:
            k = a.clave_conflicto
            choques = [(ps, ls) for ps, lineas in abiertas
                       for ls in self._choques(lineas, a, mias)]
            if not choques:
                continue        # ese codigo esta libre: nada que pisar
            c = por_clave.get(k)
            if c is None:
                # Otras lineas del mismo recurso y dia con OTRO codigo:
                # solo informativas, NO se tocan.
                contexto = [
                    ls for _ps, lineas in abiertas for ls in lineas
                    if ls.reside == a.recurso_ide
                    and ls.fecha_int == a.fecha_int
                    and int(ls.horide or 0) != int(a.hora_ide or 0)
                ]
                c = Conflicto(
                    clave=k, recurso_ide=int(a.recurso_ide or 0),
                    fecha_int=a.fecha_int, ano=parte.ano, mes=parte.mes,
                    parte_cod=choques[0][0].cod, nombre=a.nombre,
                    horide=a.hora_ide, hora_codigo=a.hora_codigo,
                    lineas=[ls for _ps, ls in choques], contexto=contexto)
                por_clave[k] = c
            c.registros.append(a.registro_id)
            c.nuevas.append({
                "registro_id": a.registro_id, "can": a.can, "tot": a.tot,
                "hora_codigo": a.hora_codigo, "partida_cod": a.partida_cod,
            })
        return list(por_clave.values())

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
            # F-019 (R8): lo que va a dedicacion y no a Sigrid.
            dedicacion=[{"registro_id": a.registro_id,
                         "recurso_ide": a.recurso_ide,
                         "codigo_mes": a.codigo_mes}
                        for a in pf.acciones if a.accion == "dedicacion"],
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
            cod = p.cod or self._cli.siguiente_cod_pt(
                p.ano, int(destino.empresa))  # type: ignore[arg-type]
            self._cli.escribir(self._cli.stmts_crear_parte(
                obra=destino, ano=p.ano, mes=p.mes, cod=cod, desc=desc))
            # R9: se relee por codigo; si el creado no sale En registro,
            # no se inserta ninguna linea (ni de este ni de otro periodo).
            creado = next(
                (ps for ps in self._cli.partes_del_periodo(
                    int(destino.ide), *clave)
                 if ps.cod == cod and ps.est == self._est_registro()), None)
            if creado is None:
                raise RuntimeError(
                    f"no se pudo crear el parte {cod} en registro (la "
                    f"relectura no lo da): no se inserta ninguna linea")
            p.existe, p.ide, p.cod, p.creado = True, creado.ide, creado.cod, True
            p.estado = creado.est
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
                synckey=synckey_de(a.registro_id), tex=tex,
                caaide=int(a.caa_ide)))
            res.escritas.append({"registro_id": a.registro_id,
                                 "hmoide": hmoide, "parte_cod": p.cod,
                                 "hora_codigo": a.hora_codigo,
                                 "can": a.can, "tot": a.tot,
                                 "caa_cod": a.caa_cod})

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
