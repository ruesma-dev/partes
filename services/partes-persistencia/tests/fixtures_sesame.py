# tests/fixtures_sesame.py
"""Respuestas FICTICIAS de la API de Sesame HR y un Sesame falso (F-077).

Forma copiada del codigo de referencia del repositorio `sesame-api`
(`SesameHttpClient`, leido sin su `.env` el 2026-11-18): listados con
`data` y `meta.lastPage`; cada fila de `/schedule/v1/holidays` trae un
objeto `dayOff` (`date`, `name`); los calendarios de
`/schedule/v1/holiday-calendar` traen la lista `daysOff`.

TODO es inventado: ids, DNIs (de ejemplo, con letra valida), nombres,
emails y token. Las filas de empleados llevan nombre, apellidos, email y
codigo A PROPOSITO: los tests comprueban que no salen del cliente ni
llegan a ningun log (R6, R18).

`SesameHrFalso` es el servidor que montan los tests con
`httpx.MockTransport`: anota cada peticion y REVIENTA con cualquier metodo
distinto de GET (R9).
"""
from __future__ import annotations

from typing import Any, Callable

import httpx

BASE_URL = "https://sesame.ejemplo.test"
TOKEN = "token-ficticio-de-pruebas-0123456789"

RUTA_EMPLEADOS = "/core/v3/employees"
RUTA_FESTIVOS = "/schedule/v1/holidays"
RUTA_CALENDARIOS = "/schedule/v1/holiday-calendar"

DNI_A = "12345678Z"
DNI_B = "87654321X"
DNI_C = "11111111H"
DNI_AUSENTE = "22222222J"

ID_A = "emp-ficticio-000a"
ID_B = "emp-ficticio-000b"
ID_C = "emp-ficticio-000c"
ID_C_INACTIVO = "emp-ficticio-00c0"


def empleado(id_: str, nid: str | None, *, activo: bool = True,
             sufijo: str = "a") -> dict:
    """Una fila de `/core/v3/employees` con TODOS sus campos personales."""
    return {
        "id": id_,
        "firstName": f"Nombreficticio{sufijo}",
        "lastName": f"Apellidoficticio{sufijo}",
        "email": f"persona.{sufijo}@ejemplo.test",
        "nid": nid,
        "code": f"COD-{sufijo}",
        "identityNumberType": "dni",
        "status": "active" if activo else "inactive",
    }


#: Textos personales de las filas de arriba: no pueden salir del cliente.
PERSONALES = ("Nombreficticio", "Apellidoficticio", "@ejemplo.test", "COD-")


def pagina(data: Any, page: int = 1, last: int | None = 1) -> dict:
    """Un listado de Sesame; `last=None` omite `meta.lastPage`."""
    meta: dict = {"currentPage": page}
    if last is not None:
        meta["lastPage"] = last
    return {"data": data, "meta": meta}


#: El indice en DOS paginas: A con el DNI escrito «a mano», B, C inactivo
#: y C activo (duplicado) y una fila sin DNI.
EMPLEADOS_P1 = pagina([
    empleado(ID_A, "12.345.678-z", sufijo="a"),
    empleado(ID_B, DNI_B, sufijo="b"),
    empleado(ID_C_INACTIVO, DNI_C, activo=False, sufijo="c0"),
], 1, 2)
EMPLEADOS_P2 = pagina([
    empleado(ID_C, DNI_C, sufijo="c"),
    empleado("emp-ficticio-sin-dni", None, sufijo="x"),
], 2, 2)


def fila_festivo(fecha: str | None, nombre: str | None = None) -> dict:
    """Una fila de `/schedule/v1/holidays` (objeto `dayOff`)."""
    return {"id": f"h-{fecha}", "dayOff": {"date": fecha, "name": nombre,
                                           "calendarId": "cal-ficticio-1"}}


#: Festivos de A en 2026: desordenados, uno de 2027 y uno sin fecha.
FESTIVOS_A_2026 = pagina([
    fila_festivo("2026-05-15", "Fiesta local ficticia"),
    fila_festivo("2026-01-01", "Ano Nuevo"),
    fila_festivo("2027-01-01", "Del ano siguiente"),
    fila_festivo(None, "Sin fecha"),
])

#: El calendario por defecto y otro, en la forma de `/holiday-calendar`.
CALENDARIOS = pagina([
    {"id": "cal-ficticio-1", "name": "General", "default": True,
     "daysOff": [{"date": "2026-12-25", "name": "Navidad"},
                 {"date": "2026-01-06", "name": "Reyes"},
                 {"date": None, "name": "roto"}]},
    {"id": "cal-ficticio-2", "name": "Otro", "default": False,
     "daysOff": [{"date": "2026-05-15", "name": "Local"}]},
])


# ------------------------------------------------------------------ #
# Sesame falso.
# ------------------------------------------------------------------ #
Respuesta = Any   # dict | list | int | httpx.Response | BaseException | callable


def responder(valor: Respuesta, request: httpx.Request) -> httpx.Response:
    """Convierte un valor del guion en la respuesta (o el fallo) de httpx."""
    if callable(valor) and not isinstance(valor, type):
        valor = valor(request)
    if isinstance(valor, BaseException):
        raise valor
    if isinstance(valor, httpx.Response):
        return valor
    if isinstance(valor, int):
        return httpx.Response(valor, json={"error": "fallo ficticio"})
    return httpx.Response(200, json=valor)


class SesameHrFalso:
    """Sesame HR por `MockTransport`, con guion por ruta.

    `empleados` y `calendarios`: una respuesta por peticion, en orden; la
    ultima se repite. `festivos`: por `employeeId`, una respuesta o una
    lista (igual, en orden). Cualquier otra ruta, 500; cualquier metodo
    distinto de GET, `AssertionError` (R9).
    """

    def __init__(self, *, empleados: list | None = None,
                 festivos: dict | None = None,
                 calendarios: list | None = None) -> None:
        self.empleados = list(empleados or [EMPLEADOS_P1, EMPLEADOS_P2])
        self.festivos = {k: (list(v) if isinstance(v, list) else [v])
                         for k, v in (festivos or {}).items()}
        self.calendarios = list(calendarios or [CALENDARIOS])
        self.peticiones: list[httpx.Request] = []

    @staticmethod
    def _siguiente(cola: list) -> Respuesta:
        return cola.pop(0) if len(cola) > 1 else cola[0]

    def __call__(self, request: httpx.Request) -> httpx.Response:
        assert request.method == "GET", f"metodo prohibido: {request.method}"
        self.peticiones.append(request)
        ruta = request.url.path
        if ruta == RUTA_EMPLEADOS:
            return responder(self._siguiente(self.empleados), request)
        if ruta == RUTA_CALENDARIOS:
            return responder(self._siguiente(self.calendarios), request)
        if ruta == RUTA_FESTIVOS:
            cola = self.festivos.get(request.url.params.get("employeeId"))
            if cola is None:
                return httpx.Response(404, json={"error": "no existe"})
            return responder(self._siguiente(cola), request)
        return httpx.Response(500, json={"error": "ruta no prevista"})

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self)

    def rutas(self) -> list[str]:
        return [r.url.path for r in self.peticiones]


class Dormir:
    """Espera inyectada: anota los segundos y no duerme."""

    def __init__(self) -> None:
        self.esperas: list[float] = []

    def __call__(self, segundos: float) -> None:
        self.esperas.append(segundos)


def secuencia(*valores: Respuesta) -> Callable[[httpx.Request], httpx.Response]:
    """Una respuesta por llamada, en orden (la ultima se repite)."""
    cola = list(valores)

    def _uno(request: httpx.Request) -> httpx.Response:
        return responder(cola.pop(0) if len(cola) > 1 else cola[0], request)
    return _uno
