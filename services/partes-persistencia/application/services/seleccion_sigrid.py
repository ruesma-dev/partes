# application/services/seleccion_sigrid.py
"""Reglas puras de F-023 para elegir obra, ficha de empleado y recurso.

Todo lo que decide «con quien se casa» un parte vive aqui, sin red ni
base, para poder probarlo por tablas de casos:

  - `de_alta` (R1): un concepto esta de alta a la fecha D si su
    `con.fecbaj` es NULL, 0 o posterior a D. `emp.fecbaj` no cuenta (DA1).
  - `IndicePersonas`: fichas de empleado y recursos de TODAS las empresas,
    indexados por DNI normalizado y por ficha. Elige la ficha de un DNI en
    la empresa del parte (R17-R21) y el recurso de una linea (R25-R28).
    F-036: solo los recursos PERSONA (`res.cla = 1`, `CLA_PERSONA`) se
    proponen al casar o al elegir recurso; el casado de la ingesta elige
    RECURSO (`casar_por_dni`, `candidatos_nombre`).
  - `elegir_obra` (R9-R13): entre las obras que comparten el codigo leido
    (las «gemelas» de dos empresas), cual gana.

Nada se elige al azar: cuando la regla no deja un unico candidato, la
respuesta es «sin casar» con un motivo, y quien llama manda el parte a
revision.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from application.services import text_match as tm
from domain.models.sigrid_models import EmpleadoRow, ObraRow, RecursoRow


#: F-036 (R2, DA3): `res.cla` de un recurso de PERSONA (0 consumo, 2 medio),
#: el criterio de `porcentajes`. Esta en la lista cerrada de `CLAUDE.md`:
#: sv5 lo aplica en `recursos_por_dni` y lo vigila
#: `tests/test_f036_recurso_persona_gemelos.py`.
CLA_PERSONA = 1


def es_persona(r: RecursoRow) -> bool:
    """R2: el recurso es de persona (`res.cla = 1`)."""
    return r.cla == CLA_PERSONA


def de_alta(fecbaj: int | None, fecha: int) -> bool:
    """R1: `con.fecbaj` NULL, 0 o mayor que `fecha` (`YYYYMMDD`)."""
    return not fecbaj or fecbaj > fecha


@dataclass(frozen=True)
class Resolucion:
    """Resultado de una eleccion: el ide elegido o None, y por que.

    `motivo`: `ok` | `ambiguo` | `solo_baja` | `otra_empresa` |
    `desconocido` (el DNI o la persona no tienen nada en el maestro).
    """

    ide: int | None
    motivo: str


@dataclass(frozen=True)
class ResolucionRecurso(Resolucion):
    """`Resolucion` del recurso con los recursos de la persona que NO
    fueron candidatos (R28): por estar de baja a la fecha o por ser de
    otra empresa."""

    descartados_baja: int = 0
    descartados_otra_empresa: int = 0


class IndicePersonas:
    """Fichas (`emp`) y recursos (`res`) de todas las empresas.

    `obras` es opcional y solo sirve para `empresa_de_obra`: el
    conciliador de recursos necesita la empresa de la obra de cada linea.
    """

    def __init__(
        self,
        empleados: Iterable[EmpleadoRow],
        recursos: Iterable[RecursoRow],
        obras: Iterable[ObraRow] = (),
    ) -> None:
        self._fichas = list(empleados)
        self._recursos = list(recursos)
        self._ficha_por_ide = {f.ide: f for f in self._fichas}
        self._recurso_por_ide = {r.ide: r for r in self._recursos}
        self._empresa_obra = {o.ide: o.empresa for o in obras}
        self._fichas_por_dni: dict[str, list[EmpleadoRow]] = defaultdict(list)
        for f in self._fichas:
            dni = tm.normalize_dni(f.dni)
            if dni:
                self._fichas_por_dni[dni].append(f)
        self._recursos_por_conide: dict[int, list[RecursoRow]] = \
            defaultdict(list)
        self._recursos_por_cif: dict[str, list[RecursoRow]] = defaultdict(list)
        # R2: solo los recursos persona entran en los indices por DNI y por
        # ficha, asi que `_recursos_de` (y con el `elegir_recurso`,
        # `empresas_con_recurso` y el casado) no ve otros. `_recursos`,
        # `recurso()` y `recursos` siguen con TODOS.
        for r in filter(es_persona, self._recursos):
            if r.conide is not None:
                self._recursos_por_conide[r.conide].append(r)
            cif = tm.normalize_dni(r.cif)
            if cif:
                self._recursos_por_cif[cif].append(r)

    # ------------------------------------------------------------- #
    @property
    def recursos(self) -> list[RecursoRow]:
        return list(self._recursos)

    def ficha(self, ide: int | None) -> EmpleadoRow | None:
        return self._ficha_por_ide.get(ide)

    def recurso(self, ide: int | None) -> RecursoRow | None:
        return self._recurso_por_ide.get(ide)

    def empresa_de_obra(self, obra_ide: int | None) -> int | None:
        return self._empresa_obra.get(obra_ide)

    def ficha_enlazada(self, r: RecursoRow) -> EmpleadoRow | None:
        """F-036: la ficha `emp` del recurso (`res.conide`), si esta en el
        maestro."""
        return self._ficha_por_ide.get(r.conide)

    def dni_de_recurso(self, r: RecursoRow) -> str:
        """F-036 (DA1): el DNI de la ficha enlazada si no esta vacio; si
        no, `res.cif`. Normalizado; cadena vacia si no hay ninguno."""
        ficha = self.ficha_enlazada(r)
        dni = tm.normalize_dni(ficha.dni) if ficha is not None else ""
        return dni or tm.normalize_dni(r.cif)

    # ------------------------------------------------------------- #
    def _recursos_de(
        self, dni: str, fichas: Iterable[int]
    ) -> list[RecursoRow]:
        """Recursos de una persona: `conide` en sus fichas o `cif` = DNI,
        cada uno una sola vez y en orden de ide."""
        por_ide: dict[int, RecursoRow] = {}
        for ide in fichas:
            for r in self._recursos_por_conide.get(ide, ()):
                por_ide[r.ide] = r
        for r in self._recursos_por_cif.get(dni, ()):
            por_ide[r.ide] = r
        return [por_ide[i] for i in sorted(por_ide)]

    def _fichas_de(self, dni: str, empleado_ide: int | None) -> list[int]:
        """R25: las fichas con ese DNI o, si no hay, la ficha casada."""
        fichas = [f.ide for f in self._fichas_por_dni.get(dni, ())]
        if not fichas and empleado_ide is not None:
            fichas = [empleado_ide]
        return fichas

    def empresas_con_recurso(
        self, dni: str | None, fecha: int
    ) -> frozenset[int]:
        """Empresas donde la persona tiene algun recurso de alta a la fecha
        (entrada de los discriminantes de R11)."""
        dni_n = tm.normalize_dni(dni)
        recursos = self._recursos_de(dni_n, self._fichas_de(dni_n, None))
        return frozenset(
            r.empresa for r in recursos
            if r.empresa is not None and de_alta(r.fecbaj, fecha)
        )

    def candidatos_nombre(
        self, empresa: int | None, fecha: int
    ) -> list[RecursoRow]:
        """F-036 (R3, R10): recursos persona de alta a la fecha, de la
        empresa (o de todas si es None) y con DNI del recurso."""
        return [
            r for r in self._recursos
            if es_persona(r) and de_alta(r.fecbaj, fecha)
            and (empresa is None or r.empresa == empresa)
            and self.dni_de_recurso(r)
        ]

    def casar_por_dni(
        self, dni: str | None, empresa: int | None, fecha: int
    ) -> ResolucionRecurso:
        """F-036 (R4-R5): el recurso persona de un DNI en la empresa del
        parte a la fecha. Desempata como ingesta y conciliador juntos: con
        la ficha del DNI de alta en esa empresa, su `reside` y despues el
        unico enlazado a ella; sin esa ficha, solo un candidato unico."""
        ficha = self.elegir_ficha(dni, empresa, fecha)
        if ficha.motivo == "ok":
            reside = self._ficha_por_ide[ficha.ide].reside
            return self.elegir_recurso(dni, ficha.ide, reside, empresa, fecha)
        return self.elegir_recurso(dni, None, None, empresa, fecha)

    def elegir_ficha(
        self, dni: str | None, empresa: int | None, fecha: int
    ) -> Resolucion:
        """R17-R21: la ficha del DNI de alta a la fecha en la empresa."""
        fichas = self._fichas_por_dni.get(tm.normalize_dni(dni), [])
        if not fichas:
            return Resolucion(None, "desconocido")
        de_alta_ya = [f for f in fichas if de_alta(f.fecbaj, fecha)]
        en_empresa = [
            f for f in de_alta_ya if empresa is None or f.empresa == empresa
        ]
        if len(en_empresa) == 1:
            return Resolucion(en_empresa[0].ide, "ok")
        if en_empresa:
            return Resolucion(None, "ambiguo")
        if de_alta_ya:
            return Resolucion(None, "otra_empresa")
        return Resolucion(None, "solo_baja")

    def elegir_recurso(
        self,
        dni: str | None,
        empleado_ide: int | None,
        preferido: int | None,
        empresa: int | None,
        fecha: int,
    ) -> ResolucionRecurso:
        """R25-R28: el recurso de una linea.

        Candidatos: recursos de la persona de alta a `fecha` y de
        `empresa` (o de cualquiera si es None). Con uno, ese; con varios,
        el `preferido` (el `reside` de la ficha) si es candidato o, si no,
        el unico enlazado a la ficha casada. `preferido` NUNCA se devuelve
        si no es candidato (R27).
        """
        dni_n = tm.normalize_dni(dni)
        propios = self._recursos_de(dni_n, self._fichas_de(dni_n, empleado_ide))
        if not propios:
            return ResolucionRecurso(None, "desconocido")
        candidatos: list[RecursoRow] = []
        baja = otra = 0
        for r in propios:
            if not de_alta(r.fecbaj, fecha):
                baja += 1
            elif empresa is not None and r.empresa != empresa:
                otra += 1
            else:
                candidatos.append(r)
        if not candidatos:
            motivo = "otra_empresa" if otra else "solo_baja"
            return ResolucionRecurso(None, motivo, baja, otra)
        elegido = _desempatar(candidatos, preferido, empleado_ide)
        if elegido is None:
            return ResolucionRecurso(None, "ambiguo", baja, otra)
        return ResolucionRecurso(elegido, "ok", baja, otra)


def _desempatar(
    candidatos: list[RecursoRow],
    preferido: int | None,
    empleado_ide: int | None,
) -> int | None:
    """R26: uno solo; si no, el preferido; si no, el unico de la ficha."""
    if len(candidatos) == 1:
        return candidatos[0].ide
    ides = [r.ide for r in candidatos]
    if preferido in ides:
        return preferido
    de_la_ficha = [r.ide for r in candidatos if r.conide == empleado_ide]
    if len(de_la_ficha) == 1:
        return de_la_ficha[0]
    return None


def elegir_obra(
    candidatas: list[ObraRow],
    empresa_membrete: int | None,
    discriminantes: Iterable[frozenset[int]],
    nombre: str | None,
    min_score: float,
) -> tuple[ObraRow | None, str]:
    """R9-R13 sobre las obras que casan con el codigo leido.

    Devuelve la obra (o None) y el metodo: `codigo`, `codigo_membrete`,
    `codigo_trabajadores` o `codigo_nombre` al casar; `codigo_otra_empresa`
    o `codigo_ambiguo` al no hacerlo; `none` sin candidatas.
    """
    if not candidatas:
        return None, "none"
    if empresa_membrete is not None:
        # R9-R10: solo compiten las obras de la empresa del membrete.
        de_la_empresa = [o for o in candidatas if o.empresa == empresa_membrete]
        if not de_la_empresa:
            return None, "codigo_otra_empresa"
        if len(de_la_empresa) > 1:
            return None, "codigo_ambiguo"
        metodo = "codigo" if len(candidatas) == 1 else "codigo_membrete"
        return de_la_empresa[0], metodo
    if len(candidatas) == 1:
        return candidatas[0], "codigo"
    # R11: trabajadores cuyos recursos de alta estan en UNA de las empresas
    # de las gemelas.
    empresas = {o.empresa for o in candidatas}
    senaladas: set[int] = set()
    for suyas in discriminantes:
        comunes = suyas & empresas
        if len(comunes) == 1:
            senaladas |= comunes
    if senaladas:
        if len(senaladas) > 1:
            return None, "codigo_ambiguo"          # R13: discrepan
        (empresa,) = senaladas
        de_la_empresa = [o for o in candidatas if o.empresa == empresa]
        if len(de_la_empresa) == 1:
            return de_la_empresa[0], "codigo_trabajadores"
        return None, "codigo_ambiguo"
    # R12: sin discriminantes, el nombre, solo si gana con claridad.
    ganadora, _ = elegir_por_nombre(candidatas, nombre, min_score)
    if ganadora is not None:
        return ganadora, "codigo_nombre"
    return None, "codigo_ambiguo"


def elegir_por_nombre(
    obras: list[ObraRow], nombre: str | None, min_score: float
) -> tuple[ObraRow | None, str]:
    """La obra de mayor similitud de nombre si alcanza el umbral y supera
    ESTRICTAMENTE a las demas (R12, R14).

    Devuelve `(obra, "nombre")`, `(None, "nombre_ambiguo")` si la mejor
    puntuacion empata entre obras distintas, o `(None, "none")` si no hay
    nombre, no hay obras o ninguna llega al umbral.
    """
    if not obras or not tm.normalize(nombre):
        return None, "none"
    puntuadas = sorted(
        ((tm.name_similarity(nombre, o.nombre), o) for o in obras),
        key=lambda par: par[0], reverse=True,
    )
    mejor, obra = puntuadas[0]
    if mejor < min_score:
        return None, "none"
    if len(puntuadas) > 1 and puntuadas[1][0] >= mejor:
        return None, "nombre_ambiguo"
    return obra, "nombre"
