# application/services/reglas_registro.py
"""Reglas de negocio de QUE se registra en Sigrid y con que codigo.

Reglas (definidas por Administracion; R1 actualizada el 25/07/2026):
  R1. Las INCIDENCIAS (V, B, AT, FJ, F, H, M...) SE REGISTRAN solo el
      dia de INICIO y el de FIN (los partes no marcan los intermedios):
      el inicio con su codigo CI* (CIV, CIE, CIP, CIH...) y el fin con
      CIZ (Fin de Incidencia). El rol lo determina sv4 mirando el
      historico del trabajador (dia anterior trabajado -> inicio; dia
      anterior en incidencia -> fin). Las incidencias van SIN HORAS
      (can=0): en Sigrid la linea marca el hecho, no una cantidad.
      Aplica a TODOS los trabajadores cuyo recurso tenga el codigo en su
      ficha (tambien mensuales: R2 no aplica aqui).
  R2. Un trabajador cuyo recurso NO tiene NINGUN codigo de hora extra
      ('HE%') en Sigrid NO se registra en absoluto: va por su codigo
      mensual (encargados, jefes de obra...).
  R3. Las horas ORDINARIAS solo se registran si el recurso tiene codigo de
      hora laborable ('HL%'). Un capataz con MCAP (mensual) + HECAP solo
      registra, por tanto, sus EXTRAS.
  R4. Las horas EXTRA se registran con el codigo 'HE%' del recurso. La
      cantidad puede ser NEGATIVA (ajuste a la baja).
  R5. El precio (pre) es el que tiene el recurso en reshor para ese
      codigo; el importe es can * pre.
"""
from __future__ import annotations

import logging

from domain.models.registro_models import AccionLinea, HoraRecurso, LineaEntrada

logger = logging.getLogger(__name__)

MOTIVO_SIN_CI = (
    "el recurso no tiene ese codigo de incidencia (CI*) en Sigrid"
)
MOTIVO_SIN_CIZ = (
    "el recurso no tiene el codigo CIZ (fin de incidencia) en Sigrid"
)
MOTIVO_INTERMEDIO = (
    "dia intermedio de la incidencia: solo se registran el inicio y el fin"
)
MOTIVO_SIN_RECURSO = "sin recurso casado en Sigrid"
MOTIVO_SIN_HORAS = "sin horas"
MOTIVO_SIN_EXTRA = (
    "el recurso no tiene codigo de hora extra en Sigrid: no se registra "
    "(sus horas van por el codigo mensual)"
)
MOTIVO_SIN_LABORABLE = (
    "el recurso no tiene codigo de hora laborable (es mensual): solo se "
    "registran sus horas extra"
)
MOTIVO_TIPO = "tipo de hora no reconocido"


class ReglasRegistro:
    """Decide, para cada linea, si se escribe y con que codigo/precio."""

    def __init__(self, horas_por_recurso: dict[int, list[HoraRecurso]]) -> None:
        self._horas = horas_por_recurso

    # ------------------------------------------------------------- #
    def decidir(self, linea: LineaEntrada) -> AccionLinea:
        base = dict(
            registro_id=linea.registro_id, ano=linea.ano, mes=linea.mes,
            fecha_int=linea.fecha_int, nombre=linea.nombre,
            recurso_ide=linea.recurso_ide,
            paride=int(linea.partida_ide or 0),
            partida_cod=linea.partida_cod,
        )

        def omitir(motivo: str) -> AccionLinea:
            return AccionLinea(accion="omitir", motivo=motivo, **base)

        if linea.es_incidencia:
            return self._decidir_incidencia(linea, base, omitir)
        tipo = (linea.tipo_hora or "").strip().lower()
        if tipo not in ("normal", "extra"):
            return omitir(f"{MOTIVO_TIPO}: {linea.tipo_hora!r}")
        if not linea.recurso_ide:
            return omitir(MOTIVO_SIN_RECURSO)
        if not linea.horas:
            return omitir(MOTIVO_SIN_HORAS)

        disponibles = self._horas.get(int(linea.recurso_ide), [])
        extras = [h for h in disponibles if h.es_extra]
        laborables = [h for h in disponibles if h.es_laborable]

        # R2: sin ningun HE% -> el trabajador entero fuera.
        if not extras:
            return omitir(MOTIVO_SIN_EXTRA)

        if tipo == "normal":
            # R3: ordinarias solo con HL%.
            if not laborables:
                return omitir(MOTIVO_SIN_LABORABLE)
            hora = self._elegir(laborables, linea.hora_ide)
        else:
            hora = self._elegir(extras, linea.hora_ide)

        can = float(linea.horas)
        pre = float(hora.pre or 0.0)
        return AccionLinea(
            accion="escribir", hora_ide=hora.horide, hora_codigo=hora.cod,
            can=can, pre=pre, tot=round(can * pre, 2), **base,
        )

    # ------------------------------------------------------------- #
    def _decidir_incidencia(self, linea: LineaEntrada, base: dict,
                            omitir) -> AccionLinea:
        """R1: la incidencia se registra con su codigo CI* del recurso.

        Prioridad del codigo: (1) el hora_ide que resolvio sv3 si es un
        CI del recurso; (2) el CI cuyo cod coincide con el hora_codigo de
        sv3; (3) si solo hay uno posible por la letra de la incidencia no
        se adivina: se omite con motivo claro. Cantidad: horas de la
        linea o, en su defecto, la jornada por defecto (candef)."""
        rol = (linea.incidencia_rol or "").strip().lower()
        # Dia INTERMEDIO de la racha: no se registra (solo inicio y fin).
        if rol == "intermedio":
            return omitir(MOTIVO_INTERMEDIO)
        if not linea.recurso_ide:
            return omitir(MOTIVO_SIN_RECURSO)
        disponibles = self._horas.get(int(linea.recurso_ide), [])
        cis = [h for h in disponibles if h.es_incidencia]
        if not cis:
            return omitir(MOTIVO_SIN_CI)
        # FIN de incidencia: se registra con CIZ, no con el codigo leido.
        if rol == "fin":
            ciz = next((h for h in cis
                        if (h.cod or "").upper() == "CIZ"), None)
            if ciz is None:
                return omitir(MOTIVO_SIN_CIZ)
            # Las incidencias van SIN horas (como en los partes reales).
            return AccionLinea(
                accion="escribir", hora_ide=ciz.horide, hora_codigo=ciz.cod,
                can=0.0, pre=float(ciz.pre or 0.0), tot=0.0, **base,
            )
        hora = None
        if linea.hora_ide:
            hora = next((h for h in cis
                         if h.horide == int(linea.hora_ide)), None)
        if hora is None and linea.hora_codigo:
            cod = (linea.hora_codigo or "").strip().upper()
            hora = next((h for h in cis
                         if (h.cod or "").upper() == cod), None)
        if hora is None:
            return omitir(
                f"{MOTIVO_SIN_CI} (codigo leido: "
                f"{linea.hora_codigo or linea.incidencia_codigo or '?'})")
        # Las incidencias van SIN horas (como en los partes reales: la
        # linea marca el hecho, no una cantidad).
        return AccionLinea(
            accion="escribir", hora_ide=hora.horide, hora_codigo=hora.cod,
            can=0.0, pre=float(hora.pre or 0.0), tot=0.0, **base,
        )

    # ------------------------------------------------------------- #
    @staticmethod
    def _elegir(candidatas: list[HoraRecurso],
                preferido_ide: int | None) -> HoraRecurso:
        """Respeta el codigo que resolvio sv3 si es del tipo correcto y esta
        dado de alta al recurso; si no, el primero por codigo."""
        if preferido_ide:
            for h in candidatas:
                if h.horide == int(preferido_ide):
                    return h
        return sorted(candidatas, key=lambda h: h.cod or "")[0]
