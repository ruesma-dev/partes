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
    # F-060 (R9, R13): con el rol `fin`, los `registro_id` de las lineas de
    # la racha (sv4); sv5 busca entre sus synckeys el CIZ que mover. Vacia
    # en las demas y en un sv4 anterior a F-060 (R26).
    racha_registro_ids: list[int] = field(default_factory=list)
    # F-062 (R1-R3, R6): sv4 marca el `inicio` que escribe ademas su CIZ
    # el mismo dia (con `MOVER_CIZ`); en el, `racha_registro_ids` es el
    # tramo delante. Falso en las demas y en un sv4 anterior (R8).
    ciz_mismo_dia: bool = False

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
    # F-023: `con.emp` de la obra, leido de Sigrid (nunca del portal). La
    # cabecera del parte y su correlativo son de esta empresa (R32-R34).
    empresa: Optional[int] = None


@dataclass(frozen=True)
class RecursoSigrid:
    """Lo que sv5 lee de un recurso para verificarlo (F-023, R36-R37).

    `empresa` y `fecbaj` son `con.emp` y `con.fecbaj` del recurso; `dni`
    es `emp.dni` de su empleado (via `res.conide`) o, si esta vacio,
    `res.cif`.
    """
    reside: int
    empresa: Optional[int]
    fecbaj: Optional[int]
    dni: Optional[str]


# ----------------------------- salida ----------------------------- #

@dataclass
class HoraRecurso:
    """Tipo de hora dado de alta al recurso en reshor."""
    horide: int
    cod: str
    res: Optional[str]
    pre: float
    # F-021 (R9): codigo de la cuenta analitica de `reshor.caaide` (la
    # plantilla del recurso para este tipo de hora) y si este tipo es el
    # tipo por defecto del recurso (`reshor.horide = res.horide`).
    caa_cod: Optional[str] = None
    defecto: bool = False

    @property
    def es_extra(self) -> bool:
        return (self.cod or "").upper().startswith("HE")

    @property
    def es_laborable(self) -> bool:
        return (self.cod or "").upper().startswith("HL")

    @property
    def es_incidencia(self) -> bool:
        return (self.cod or "").upper().startswith("CI")

    @property
    def es_mensual(self) -> bool:
        """F-019 (decision 1, criterio P1 de dedicacion): codigo `M*`."""
        return (self.cod or "").upper().startswith("M")


@dataclass(frozen=True)
class ParteSigrid:
    """F-031 (R1): un parte (`hmo`) del periodo tal como esta en Sigrid,
    con su estado `con.est` (1 En registro, 3 Cerrado, 10 Imputado...)."""
    ide: int
    cod: Optional[str]
    est: Optional[int]


@dataclass(frozen=True)
class PartidaCuenta:
    """F-031 (R24): partida (`obrparpar`) y el codigo de su cuenta
    analitica (`con.cod` de `obrparpar.caaide`; None si no tiene)."""
    ide: int
    cod: Optional[str]
    caa_cod: Optional[str]


@dataclass
class ParteDestino:
    """Parte de trabajo (hmo) de una obra y mes."""
    ano: int
    mes: int
    existe: bool = False
    ide: Optional[int] = None
    cod: Optional[str] = None           # existente o propuesto
    creado: bool = False
    # F-031 (R17): estado del elegido (None si es nuevo), si es un
    # complementario (el periodo tiene partes cerrados), los codigos de los
    # cerrados, todos los partes del periodo y el aviso para el modal.
    estado: Optional[int] = None
    complementario: bool = False
    cerrados: list[str] = field(default_factory=list)
    del_periodo: list[ParteSigrid] = field(default_factory=list)
    aviso: Optional[str] = None


@dataclass
class FinMismoDia:
    """F-062 (R6, R9, DA1): el CIZ «hermano» que el `inicio` escribe el
    mismo dia que su CI*, en la misma sentencia. No es una accion propia
    (R17): viaja en `AccionLinea.fin_mismo_dia`. `horide` y `pre` son los
    del CIZ del recurso (`reshor`); la cuenta, la del codigo CIZ (DA10)."""
    horide: int
    hora_codigo: Optional[str]
    pre: float
    caa_ide: int = 0
    caa_cod: Optional[str] = None


@dataclass
class AccionLinea:
    """Que se hara con una linea de entrada."""
    registro_id: int
    # escribir | omitir | ya_registrado | dedicacion (F-019)
    accion: str
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
    # F-021 (R13): cuenta analitica que se escribira en `hmores.caaide`.
    # `caa_ide = 0` = sin cuenta (la linea se escribe igual, R8);
    # `caa_motivo` None = cuenta resuelta; `caa_aviso` solo si la obra
    # podria arreglarse (R5, R6).
    caa_ide: int = 0
    caa_cod: Optional[str] = None
    caa_motivo: Optional[str] = None
    caa_aviso: Optional[str] = None
    # F-031 (R23): de donde sale la subcuenta ("recurso" | "partida" |
    # None) y, si sale de la partida, la nota informativa para el modal.
    caa_origen: Optional[str] = None
    caa_nota: Optional[str] = None
    # F-019 (R2): el codigo `M*` del recurso de una accion `dedicacion`.
    codigo_mes: Optional[str] = None
    # F-060 (R15, R20): el CIZ de la racha que esta accion `escribir` mueve
    # al dia D con un `UPDATE` (None = `INSERT` de siempre).
    mover: Optional["LineaSigrid"] = None
    # F-062 (R6, R10-R13): el CIZ hermano de un `inicio` que se escribe con
    # su CI* en una sola sentencia (None = sin hermano).
    fin_mismo_dia: Optional[FinMismoDia] = None

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
    # F-046: lo que el reajuste necesita de la linea (con defecto: las
    # lecturas de siempre no lo traen). `pre` es el precio de la propia
    # linea (el `tot` se recalcula con el, R24), `hmoide` su parte y
    # `enlazada` si algun enlace de `hmores` (albaran, factura,
    # dedicacion, nomina) no es 0 (R21, DA17).
    pre: Optional[float] = None
    hmoide: Optional[int] = None
    enlazada: bool = False
    # F-060 (R19, R20): lo que el CIZ movil necesita de la linea que se
    # mueve: `tex` (la marca de pruebas) y `pos` (se conserva si no cambia
    # de parte). Solo los trae `lineas_de_racha`.
    tex: Optional[str] = None
    pos: Optional[int] = None


@dataclass
class Conflicto:
    """Ya hay linea(s) en Sigrid para ese parte + recurso + fecha + CODIGO.

    ``lineas`` son las que se PONDRIAN A 0 al pisar (mismo codigo de hora
    y con horas; F-053: en Sigrid no se borra, `stmt_anular_linea`).
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

    @property
    def n_dedicacion(self) -> int:
        """F-019 (R7): lineas que van a dedicacion y no a Sigrid."""
        return sum(1 for a in self.acciones if a.accion == "dedicacion")


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
    # F-053 (R12, DA7): pisadas que, releidas por `ide` tras escribir, ya
    # no tienen horas (puestas a 0; sustituye a `borradas`).
    anuladas: int = 0
    pendientes_confirmacion: list[Conflicto] = field(default_factory=list)
    error: Optional[str] = None
    # F-019 (R8): {registro_id, recurso_ide, codigo_mes} de cada linea que
    # va a dedicacion; vacia con el interruptor apagado.
    dedicacion: list[dict] = field(default_factory=list)


# ----------------------------- reajuste (F-046) ----------------------------- #

@dataclass
class OpReajuste:
    """Una linea del reajuste que pide sv4 (R20).

    Existente: `registro_id`, `antes` (las horas que DEBE tener hoy en
    Sigrid) y `despues`. Nueva (extra que nace de una base registrada sin
    extra, R7): `antes` None, `base_registro_id` y lo que el registro
    necesita para escribirla (recurso, fecha, codigo de hora extra,
    partida y obra). El `registro_id` de la nueva lo reservo sv4 (DA5).
    """
    registro_id: int
    despues: float
    antes: Optional[float] = None
    base_registro_id: Optional[int] = None
    recurso_ide: Optional[int] = None
    fecha_int: Optional[int] = None
    hora_ide: Optional[int] = None
    hora_codigo: Optional[str] = None
    partida_ide: Optional[int] = None
    partida_cod: Optional[str] = None
    obra_ide: Optional[int] = None
    obra_codigo: Optional[str] = None

    @property
    def es_nueva(self) -> bool:
        return self.base_registro_id is not None


@dataclass
class VeredictoReajuste:
    """R21, R22, R26: si esa linea se puede escribir.

    `ya_aplicada`: Sigrid ya tiene «despues» (un `ejecutar` anterior
    llego a escribir); se cuenta como editable y no se escribe."""
    registro_id: int
    editable: bool
    ya_aplicada: bool = False
    motivo: Optional[str] = None


@dataclass
class ResultadoReajuste:
    """Respuesta de `comprobar` y `ejecutar` (R20, R23, R26).

    `lineas` (solo si `ok`): una por linea pedida, escrita ahora o ya
    aplicada antes, con `registro_id`, `hmores_ide`, `hmoide`,
    `parte_cod`, `can`, `nueva` y `escrita`. sv4 las necesita tambien en
    un reintento: la extra nueva nace `registrado` con su `hmores_ide`
    (R17)."""
    ok: bool
    ya_aplicada: bool = False
    veredictos: list[VeredictoReajuste] = field(default_factory=list)
    lineas: list[dict] = field(default_factory=list)
    error: Optional[str] = None
    forzada_pruebas: bool = False


# ----------------------- franquicia de extras (F-056) ----------------------- #

#: R31, DA14: prefijo de la synckey de la linea de ajuste de una franquicia
#: (`partes:franquicia:<id de franquicia_ajuste>`). Vive en `domain` para que
#: `pisado` (que solo importa de aqui) y el reajuste la excluyan de los
#: choques sin depender del cliente.
PREFIJO_FRANQUICIA = "partes:franquicia:"


def es_synckey_franquicia(synckey: Optional[str]) -> bool:
    """R31: la linea es el ajuste de una franquicia (no choca con nada)."""
    return (synckey or "").strip().startswith(PREFIJO_FRANQUICIA)


@dataclass
class PeticionFranquicia:
    """Entrada de `/api/franquicia/comprobar` y `/ejecutar` (design §6).

    Fechas como `YYYYMMDD` (las de `hmores.fec`): `inicio` y `fin` son el
    periodo de nomina (16 -> 15) y `fecha_int` el dia de ajuste, que sv4
    calcula. `ajuste_id` 0 es el centinela del preflight (aun no hay fila):
    solo lo admite `comprobar`. `extras_pendientes` solo lo usa
    `comprobar` (las extras de esta aprobacion que aun no estan en Sigrid).
    F-056 enmienda (R41): no trae X; sv5 la lee del campo extendido.
    """
    ajuste_id: int
    recurso_ide: int
    periodo: str
    inicio: int
    fin: int
    fecha_int: int
    obra: ObraEntrada
    partida_ide: Optional[int]
    partida_cod: Optional[str]
    extras_pendientes: float = 0.0
    usuario: Optional[str] = None

    @property
    def ano(self) -> int:
        return int(self.fecha_int) // 10000

    @property
    def mes(self) -> int:
        return (int(self.fecha_int) // 100) % 100


@dataclass
class VeredictoFranquicia:
    """Que hara `ejecutar` con la linea de ajuste (R24-R30): `crear`,
    `actualizar`, `ya_aplicado`, `sin_ajuste` o `no_editable` (con
    `motivo`)."""
    accion: str
    motivo: Optional[str] = None


@dataclass
class ResultadoFranquicia:
    """Respuesta de `comprobar` y `ejecutar` (design §6). `extras` es E,
    `objetivo` A y `actual` el `can` de la linea en Sigrid (None si no
    existe). `escrita`: esta llamada escribio en Sigrid."""
    ok: bool
    accion: str
    extras: float = 0.0
    objetivo: float = 0.0
    actual: Optional[float] = None
    hmores_ide: Optional[int] = None
    hmoide: Optional[int] = None
    parte_cod: Optional[str] = None
    parte_estado: Optional[int] = None
    complementario: bool = False
    hora_codigo: Optional[str] = None
    pre: Optional[float] = None
    motivo: Optional[str] = None
    escrita: bool = False
    forzada_pruebas: bool = False
    error: Optional[str] = None
    # Enmienda (R41): la X que uso sv5 (None si no se pudo leer) y el
    # estado de la franquicia del recurso (`activa`, `inactiva`...).
    franquicia: Optional[float] = None
    franquicia_estado: Optional[str] = None


@dataclass
class LecturaFranquicia:
    """F-056 enmienda (R2): la franquicia de UN recurso leida de su campo
    extendido de recurso (`defext`/`conext`). `estado`: `activa` (X > 0),
    `inactiva` (sin fila, NULL o 0: X = 0), `invalida`, o el estado global
    si no se pudo leer (`apagada`, `no_disponible`); `franquicia` es X solo
    con `activa`/`inactiva`."""
    estado: str
    franquicia: Optional[float]
    motivo: Optional[str] = None


@dataclass
class EstadoFranquicias:
    """F-056 enmienda (R3, R38, R40): el estado global del campo (`apagada`
    | `no_disponible` | `ok`), su motivo y, con `ok`, la lectura de cada
    recurso pedido."""
    estado: str
    motivo: Optional[str] = None
    recursos: dict[int, LecturaFranquicia] = field(default_factory=dict)
