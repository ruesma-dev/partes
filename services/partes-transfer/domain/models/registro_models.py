# domain/models/registro_models.py
"""Modelos de dominio del registro de partes en Sigrid."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ----------------------------- entrada ----------------------------- #

@dataclass
class LineaEntrada:
    """Una linea de nuestro sistema (registro de sv4) a registrar."""
    registro_id: int
    fecha_int: int                      # YYYYMMDD (fecha REAL de trabajo)
    recurso_ide: Optional[int] = None
    dni: Optional[str] = None
    nombre: Optional[str] = None
    tipo_hora: Optional[str] = None     # normal | extra | (incidencia)
    es_incidencia: bool = False
    horas: Optional[float] = None       # puede ser NEGATIVA (extra)
    hora_ide: Optional[int] = None      # codigo de hora resuelto por sv3
    hora_codigo: Optional[str] = None
    partida_ide: Optional[int] = None   # imputacion (obrparpar)
    partida_cod: Optional[str] = None
    candef: Optional[float] = None      # jornada por defecto del recurso
    incidencia_codigo: Optional[str] = None  # V, B, FJ, F, H, AT, M...
    incidencia_rol: Optional[str] = None     # inicio | fin (fin -> CIZ)

    @property
    def ano(self) -> int:
        return int(self.fecha_int) // 10000

    @property
    def mes(self) -> int:
        return (int(self.fecha_int) // 100) % 100


@dataclass
class ObraEntrada:
    ide: Optional[int] = None
    codigo: Optional[str] = None
    nombre: Optional[str] = None


# ----------------------------- salida ----------------------------- #

@dataclass
class HoraRecurso:
    """Tipo de hora dado de alta al recurso en reshor."""
    horide: int
    cod: str
    res: Optional[str]
    pre: float

    @property
    def es_extra(self) -> bool:
        return (self.cod or "").upper().startswith("HE")

    @property
    def es_laborable(self) -> bool:
        return (self.cod or "").upper().startswith("HL")

    @property
    def es_incidencia(self) -> bool:
        return (self.cod or "").upper().startswith("CI")


@dataclass
class ParteDestino:
    """Parte de trabajo (hmo) de una obra y mes."""
    ano: int
    mes: int
    existe: bool = False
    ide: Optional[int] = None
    cod: Optional[str] = None           # existente o propuesto
    creado: bool = False


@dataclass
class AccionLinea:
    """Que se hara con una linea de entrada."""
    registro_id: int
    accion: str                         # escribir | omitir | ya_registrado
    ano: int
    mes: int
    fecha_int: int
    nombre: Optional[str] = None
    motivo: Optional[str] = None
    recurso_ide: Optional[int] = None
    hora_ide: Optional[int] = None
    hora_codigo: Optional[str] = None
    can: Optional[float] = None
    pre: Optional[float] = None
    tot: Optional[float] = None
    paride: int = 0
    partida_cod: Optional[str] = None
    hmores_ide: Optional[int] = None     # si ya estaba registrada

    @property
    def clave_conflicto(self) -> str:
        """Identidad de la linea en el parte: recurso + dia + CODIGO DE HORA.

        El codigo forma parte de la clave: pisar las horas ordinarias de un
        dia NO debe tocar las extra de ese mismo dia (y al reves).
        """
        return f"{self.recurso_ide or 0}|{self.fecha_int}|{self.hora_ide or 0}"


@dataclass
class LineaSigrid:
    """Linea ya existente en Sigrid (para avisar de pisado)."""
    ide: int
    reside: int
    fecha_int: int
    horide: Optional[int]
    hora_codigo: Optional[str]
    can: Optional[float]
    tot: Optional[float]
    synckey: Optional[str]
    nuestra: bool = False               # la escribimos nosotros (synckey)


@dataclass
class Conflicto:
    """Ya hay linea(s) en Sigrid para ese parte + recurso + fecha + CODIGO.

    ``lineas`` son las que se BORRARIAN al pisar (mismo codigo de hora).
    ``contexto`` son otras lineas de ese recurso y dia con OTRO codigo: se
    muestran solo como informacion y NO se tocan.
    ``nuevas`` es lo que se escribiria en su lugar (para comparar).
    """
    clave: str
    recurso_ide: int
    nombre: Optional[str]
    fecha_int: int
    ano: int
    mes: int
    parte_cod: Optional[str]
    horide: Optional[int] = None
    hora_codigo: Optional[str] = None
    lineas: list[LineaSigrid] = field(default_factory=list)
    contexto: list[LineaSigrid] = field(default_factory=list)
    nuevas: list[dict] = field(default_factory=list)
    registros: list[int] = field(default_factory=list)

    @property
    def nueva_can(self) -> float:
        return round(sum(float(n.get("can") or 0.0) for n in self.nuevas), 2)

    @property
    def nueva_tot(self) -> float:
        return round(sum(float(n.get("tot") or 0.0) for n in self.nuevas), 2)


@dataclass
class ContextoRegistro:
    """Lo que la fase de PREPARACION deja listo para la de ESCRITURA.

    Solo contiene datos maestros que sv5 nunca escribe (obra destino,
    recursos resueltos, tipos de hora) y la decision por linea de las
    reglas de negocio. Nada del estado que la propia escritura modifica
    —parte `hmo`, correlativo, synckeys, conflictos—: eso se lee dentro
    del lock, en `registrar` (R20).

    Por eso preparar contextos de peticiones distintas EN PARALELO es
    seguro (R18): ninguno depende de lo que otro vaya a escribir.
    """
    obra_origen: ObraEntrada
    obra_destino: ObraEntrada
    forzada_pruebas: bool
    lineas: list[LineaEntrada] = field(default_factory=list)
    acciones: list[AccionLinea] = field(default_factory=list)


@dataclass
class Preflight:
    """Resultado del analisis previo: que se hara y que hay que confirmar."""
    obra_destino: ObraEntrada
    obra_origen: ObraEntrada
    forzada_pruebas: bool
    partes: list[ParteDestino] = field(default_factory=list)
    acciones: list[AccionLinea] = field(default_factory=list)
    conflictos: list[Conflicto] = field(default_factory=list)

    @property
    def n_escribir(self) -> int:
        return sum(1 for a in self.acciones if a.accion == "escribir")

    @property
    def n_omitir(self) -> int:
        return sum(1 for a in self.acciones if a.accion == "omitir")

    @property
    def n_ya(self) -> int:
        return sum(1 for a in self.acciones if a.accion == "ya_registrado")


@dataclass
class ResultadoRegistro:
    """Resultado de la escritura efectiva."""
    ok: bool
    obra_destino: ObraEntrada
    forzada_pruebas: bool
    partes: list[ParteDestino] = field(default_factory=list)
    escritas: list[dict] = field(default_factory=list)   # {registro_id, hmoide}
    omitidas: list[dict] = field(default_factory=list)   # {registro_id, motivo}
    ya_registradas: list[int] = field(default_factory=list)
    pisadas: list[str] = field(default_factory=list)     # claves pisadas
    borradas: int = 0
    pendientes_confirmacion: list[Conflicto] = field(default_factory=list)
    error: Optional[str] = None
