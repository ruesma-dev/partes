# tests/dobles.py
"""Dobles en memoria del SDK de Azure Storage para la suite de sv5.

Ningun test toca la red: estos fakes sustituyen a `QueueServiceClient` y
`BlobServiceClient` por monkeypatch del simbolo importado en el modulo
adaptador, de modo que el codigo de produccion no lleva ningun parametro
que exista solo para los tests.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from types import SimpleNamespace


class MensajeFake:
    """Equivalente al `QueueMessage` del SDK (solo lo que usamos)."""

    def __init__(self, content: str, *, dequeue_count: int = 1,
                 id: str = "m1") -> None:
        self.content = content
        self.dequeue_count = dequeue_count
        self.id = id
        self.pop_receipt = f"pr-{id}"


def mensaje_json(payload: dict, *, dequeue_count: int = 1,
                 id: str = "m1") -> MensajeFake:
    return MensajeFake(json.dumps(payload, ensure_ascii=False),
                       dequeue_count=dequeue_count, id=id)


class QueueClientFake:
    """Cola en memoria.

    `rondas` es la secuencia de lotes que devolvera `receive_messages`. Al
    agotarse llama a `on_agotado` (el test la usa para detener el bucle de
    consumo de forma determinista, sin dormir ni depender de relojes).
    """

    def __init__(self, nombre: str) -> None:
        self.nombre = nombre
        self.rondas: list[list[MensajeFake]] = []
        self.enviados: list[str] = []
        self.borrados: list[str] = []
        self.recibidos: list[str] = []
        self.on_agotado: Callable[[], None] | None = None
        self.fallo_delete = False
        self.fallo_send = False
        self.mensajes_aprox = 0

    # -- productor --
    def send_message(self, content: str):
        if self.fallo_send:
            raise RuntimeError(f"send KO en {self.nombre}")
        self.enviados.append(content)
        return SimpleNamespace(id=f"{self.nombre}-{len(self.enviados)}")

    # -- consumidor --
    def receive_messages(self, messages_per_page: int = 1,
                         visibility_timeout: int | None = None):
        if self.rondas:
            lote = self.rondas.pop(0)
            self.recibidos.extend(m.id for m in lote)
            return list(lote)
        if self.on_agotado is not None:
            self.on_agotado()
        return []

    def delete_message(self, msg, pop_receipt: str | None = None):
        if self.fallo_delete:
            raise RuntimeError(f"delete KO en {self.nombre}")
        self.borrados.append(getattr(msg, "id", str(msg)))

    def get_queue_properties(self):
        return SimpleNamespace(approximate_message_count=self.mensajes_aprox)

    # -- ayuda para los tests --
    @property
    def payloads_enviados(self) -> list[dict]:
        return [json.loads(c) for c in self.enviados]


class QueueServiceClientFake:
    def __init__(self) -> None:
        self.colas: dict[str, QueueClientFake] = {}
        self.creadas: list[str] = []

    def get_queue_client(self, nombre: str) -> QueueClientFake:
        return self.colas.setdefault(nombre, QueueClientFake(nombre))

    def create_queue(self, nombre: str) -> None:
        self.creadas.append(nombre)
        self.colas.setdefault(nombre, QueueClientFake(nombre))


class BlobClientFake:
    def __init__(self, almacen: dict, clave: tuple[str, str]) -> None:
        self._almacen = almacen
        self._clave = clave

    def upload_blob(self, data, overwrite: bool = False,
                    content_settings=None) -> None:
        self._almacen[self._clave] = data

    def download_blob(self):
        if self._clave not in self._almacen:
            # La misma excepcion que lanza el SDK real: asi los tests
            # pueden exigir un tipo concreto y no un `Exception` ciego.
            from azure.core.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError(f"blob inexistente: {self._clave}")
        datos = self._almacen[self._clave]
        return SimpleNamespace(readall=lambda: datos)


class BlobServiceClientFake:
    def __init__(self) -> None:
        self.almacen: dict[tuple[str, str], bytes] = {}
        self.contenedores: list[str] = []

    def get_blob_client(self, container: str, blob: str) -> BlobClientFake:
        return BlobClientFake(self.almacen, (container, blob))

    def create_container(self, nombre: str) -> None:
        self.contenedores.append(nombre)


class SettingsFake:
    """Lo minimo que el pipeline lee de la configuracion."""

    def __init__(self, *, obra_pruebas_forzar: bool = False,
                 obra_pruebas_cod: str = "0404",
                 marca_pruebas: str = "PRUEBA-IA",
                 paso_pos: int = 64,
                 cola_transfer: str = "q-transfer",
                 cola_transfer_result: str = "q-transfer-result",
                 blob_transfer: str = "transfer",
                 cola_visibility_s: int = 600,
                 cola_max_dequeue: int = 5,
                 transfer_workers: int = 3) -> None:
        self.obra_pruebas_forzar = obra_pruebas_forzar
        self.obra_pruebas_cod = obra_pruebas_cod
        self.marca_pruebas = marca_pruebas
        self.paso_pos = paso_pos
        self.cola_transfer = cola_transfer
        self.cola_transfer_result = cola_transfer_result
        self.blob_transfer = blob_transfer
        self.cola_visibility_s = cola_visibility_s
        self.cola_max_dequeue = cola_max_dequeue
        self.transfer_workers = transfer_workers


class SigridFake:
    """Sigrid en memoria: partes (hmo) y lineas (hmores) con estado real.

    NO se sincroniza a proposito: si el pipeline dejara de serializar su
    fase de escritura, dos peticiones concurrentes a la misma obra y mes
    verian ambas 'el parte no existe' y crearian dos cabeceras con el
    MISMO correlativo. Ese es justamente el fallo que el lock evita y que
    los tests de R19/R20 comprueban; un fake con lock propio los volveria
    vacios.

    Las latencias simulan las llamadas a sigrid-api y ensanchan la ventana
    de carrera lo bastante para que el fallo sea determinista.
    """

    def __init__(self, *, obras=None, horas=None, partes=None, lineas=None,
                 latencia_lectura: float = 0.0,
                 latencia_escritura: float = 0.0) -> None:
        from domain.models.registro_models import ObraEntrada, ParteDestino

        self._ObraEntrada = ObraEntrada
        self._ParteDestino = ParteDestino
        self.obras = obras or {}
        self.horas = horas or {}
        self.partes: list[dict] = list(partes or [])
        self.lineas: list[dict] = list(lineas or [])
        self.latencia_lectura = latencia_lectura
        self.latencia_escritura = latencia_escritura
        self._siguiente_hmoide = 900
        self._siguiente_hmores = 5000
        self.llamadas: list[str] = []
        # Concurrencia observada por metodo (para R18/R19).
        self.concurrencia: dict[str, int] = {}
        self.max_concurrencia: dict[str, int] = {}
        self._verificador_lock = None
        #: Barrera opcional en la fase de preparacion (R18).
        self.barrera = None
        #: Retardo extra por recurso, para forzar un orden (R21).
        self.retardo_por_recurso: dict[int, float] = {}

    # -- instrumentacion --------------------------------------------------
    def vigilar_lock(self, lock) -> None:
        """Comprueba que la fase de escritura corre con el lock tomado."""
        self._verificador_lock = lock

    def _entrar(self, nombre: str, latencia: float):
        import time
        self.llamadas.append(nombre)
        n = self.concurrencia.get(nombre, 0) + 1
        self.concurrencia[nombre] = n
        self.max_concurrencia[nombre] = max(
            self.max_concurrencia.get(nombre, 0), n)
        if latencia:
            time.sleep(latencia)

    def _salir(self, nombre: str) -> None:
        self.concurrencia[nombre] = self.concurrencia.get(nombre, 1) - 1

    def _lectura(self, nombre: str):
        self._entrar(nombre, self.latencia_lectura)
        self._salir(nombre)

    # -- datos maestros (fase preparar) -----------------------------------
    def obra_por_codigo(self, cod: str):
        self._lectura("obra_por_codigo")
        return self.obras.get(str(cod))

    def obra_por_ide(self, ide: int):
        self._lectura("obra_por_ide")
        for o in self.obras.values():
            if int(o.ide or 0) == int(ide):
                return o
        return None

    def resides_por_dni(self, dnis):
        self._lectura("resides_por_dni")
        return {}

    def horas_de_recursos(self, resides):
        # La llamada mas pesada del pipeline y la que mas crece con el
        # lote: es la que debe solaparse entre peticiones (R18).
        import time
        ides = [int(i) for i in resides if i]
        # El contador de concurrencia se abre ANTES de esperar: si no, los
        # hilos cruzarian la barrera y saldrian de uno en uno, y el maximo
        # observado seria 1 aunque hubieran solapado de verdad.
        self._entrar("horas_de_recursos", self.latencia_lectura)
        try:
            if self.barrera is not None:
                # Prueba DETERMINISTA de solapamiento: si las preparaciones
                # no coinciden en el tiempo, la barrera expira (y el test
                # falla con BrokenBarrierError).
                self.barrera.wait()
            for ide in ides:
                espera = self.retardo_por_recurso.get(ide)
                if espera:
                    time.sleep(espera)
            return {ide: list(self.horas.get(ide, [])) for ide in ides}
        finally:
            self._salir("horas_de_recursos")

    # -- estado escrito (fase registrar, bajo lock) -----------------------
    def _comprobar_lock(self, nombre: str) -> None:
        if self._verificador_lock is not None \
                and not self._verificador_lock.locked():
            raise AssertionError(
                f"{nombre} se ejecuto FUERA del lock de escritura")

    def partes_existentes(self, obra_ide: int, periodos):
        self._comprobar_lock("partes_existentes")
        self._entrar("partes_existentes", self.latencia_lectura)
        try:
            out = {}
            for ano, mes in sorted(set(periodos)):
                hit = next((p for p in self.partes
                            if p["obride"] == int(obra_ide)
                            and p["ano"] == ano and p["mes"] == mes), None)
                out[(ano, mes)] = (
                    self._ParteDestino(ano=ano, mes=mes, existe=True,
                                       ide=hit["ide"], cod=hit["cod"])
                    if hit else
                    self._ParteDestino(ano=ano, mes=mes, existe=False))
            return out
        finally:
            self._salir("partes_existentes")

    def siguiente_cod_pt(self, ano: int) -> str:
        self._comprobar_lock("siguiente_cod_pt")
        self._entrar("siguiente_cod_pt", self.latencia_lectura)
        try:
            yy = str(int(ano))[-2:]
            usados = [int(p["cod"].split("/")[1]) for p in self.partes
                      if p["cod"].startswith(f"PT{yy}/")]
            return f"PT{yy}/{(max(usados) + 1 if usados else 1):05d}"
        finally:
            self._salir("siguiente_cod_pt")

    def max_pos(self, hmoide: int) -> int:
        self._comprobar_lock("max_pos")
        self._lectura("max_pos")
        pos = [l["pos"] for l in self.lineas if l["hmoide"] == int(hmoide)]
        return max(pos) if pos else 0

    def lineas_existentes(self, hmoide: int, resides, fechas):
        self._comprobar_lock("lineas_existentes")
        self._lectura("lineas_existentes")
        res = {int(i) for i in resides if i}
        fec = {int(f) for f in fechas if f}
        if not res or not fec:
            return []
        return [self._a_linea_sigrid(l) for l in self.lineas
                if l["hmoide"] == int(hmoide) and l["reside"] in res
                and l["fec"] in fec]

    def lineas_por_synckey(self, claves):
        self._comprobar_lock("lineas_por_synckey")
        self._lectura("lineas_por_synckey")
        ks = {k for k in claves if k}
        out = {}
        for l in self.lineas:
            if l.get("synckey") in ks:
                out[l["synckey"]] = self._a_linea_sigrid(l)
        return out

    def _a_linea_sigrid(self, l: dict):
        from domain.models.registro_models import LineaSigrid
        ls = LineaSigrid(
            ide=l["ide"], reside=l["reside"], fecha_int=l["fec"],
            horide=l.get("horide"), hora_codigo=l.get("hora_codigo"),
            can=l.get("can"), tot=l.get("tot"), synckey=l.get("synckey"),
            nuestra=bool(l.get("synckey")))
        ls.hmoide = l["hmoide"]
        return ls

    # -- sentencias (opacas para el pipeline) -----------------------------
    def stmts_crear_parte(self, *, obra, ano: int, mes: int, cod: str,
                          desc: str) -> list[dict]:
        return [{"op": "crear_parte", "obride": int(obra.ide), "ano": int(ano),
                 "mes": int(mes), "cod": cod, "desc": desc}]

    def stmt_insert_linea(self, *, hmoide, obra, reside, pos, fecha_int,
                          horide, can, pre, paride, ano, mes, synckey,
                          tex) -> dict:
        return {"op": "insert", "hmoide": int(hmoide), "reside": int(reside),
                "pos": int(pos), "fec": int(fecha_int), "horide": int(horide),
                "can": float(can), "pre": float(pre),
                "tot": round(float(can) * float(pre), 2),
                "paride": int(paride or 0), "ano": int(ano), "mes": int(mes),
                "synckey": synckey, "tex": tex}

    @staticmethod
    def stmt_borrar_linea(ide: int) -> dict:
        return {"op": "borrar", "ide": int(ide)}

    def escribir(self, statements: list[dict]) -> int:
        self._comprobar_lock("escribir")
        self._entrar("escribir", self.latencia_escritura)
        try:
            n = 0
            for s in statements:
                if s["op"] == "crear_parte":
                    self._siguiente_hmoide += 1
                    self.partes.append({
                        "ide": self._siguiente_hmoide, "obride": s["obride"],
                        "ano": s["ano"], "mes": s["mes"], "cod": s["cod"]})
                elif s["op"] == "insert":
                    self._siguiente_hmores += 1
                    fila = dict(s)
                    fila.pop("op")
                    fila["ide"] = self._siguiente_hmores
                    fila["hora_codigo"] = None
                    self.lineas.append(fila)
                elif s["op"] == "borrar":
                    self.lineas = [l for l in self.lineas
                                   if l["ide"] != s["ide"]]
                n += 1
            return n
        finally:
            self._salir("escribir")


def parchear_colas(monkeypatch, modulo, servicio: QueueServiceClientFake):
    """Sustituye `QueueServiceClient` en el modulo adaptador indicado."""
    class _Factoria:
        @staticmethod
        def from_connection_string(_cs):
            return servicio

        def __new__(cls, *args, **kwargs):
            return servicio

    monkeypatch.setattr(modulo, "QueueServiceClient", _Factoria)
    return servicio


def parchear_blobs(monkeypatch, modulo, servicio: BlobServiceClientFake):
    """Sustituye `BlobServiceClient` en el modulo adaptador indicado."""
    class _Factoria:
        @staticmethod
        def from_connection_string(_cs):
            return servicio

        def __new__(cls, *args, **kwargs):
            return servicio

    monkeypatch.setattr(modulo, "BlobServiceClient", _Factoria)
    return servicio
