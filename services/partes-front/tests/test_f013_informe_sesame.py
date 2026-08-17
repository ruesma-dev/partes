# tests/test_f013_informe_sesame.py
"""F-013 · Informe de validacion de datos Sesame por trabajador.

Ejercita `validar_datos_sesame.py` SIN RED: todo el trafico HTTP va por un
`httpx.MockTransport` que sirve las cuatro rutas de sesame-api que toca el
script (`/api/v1/empleados`, `/api/v1/festivos`, `/api/v1/jornada`,
`/api/v1/calendarios-festivos`), con los cuerpos reales fijados en
`tests/fixtures_sesame.py`.

Trazabilidad con los `acceptance` de F-013 (harness/features.json):
  A1  el script genera el informe por trabajador contra una instancia
      configurable, sin tocar BBDD.
  A2  los errores por trabajador (DNI sin casar, upstream caido) aparecen
      EN el informe y no abortan el barrido.
  A3  bash harness/init.sh en verde (lo comprueba el portero, no un test).
"""
from __future__ import annotations

import csv
import io

import httpx
import pytest
import validar_datos_sesame as vds
from infrastructure.sesame.sesame_api_client import (
    FestivoDia,
    JornadaContrato,
)
from tests.fixtures_sesame import (
    CALENDARIOS,
    FESTIVOS_DNI,
    JORNADA,
    NO_ENCONTRADO,
    UPSTREAM_KO,
)

ANO = 2026
CLAVE = "clave-de-test"


# --------------------------------------------------------------- #
# Utilidades de la suite.
# --------------------------------------------------------------- #
def _empleado(dni: str, nombre: str, apellidos: str,
              estado: str = "active") -> dict:
    """Un empleado con la forma EXACTA que devuelve sesame-api."""
    return {
        "id": f"uuid-{dni}",
        "nombre": nombre,
        "apellidos": apellidos,
        "dni": dni,
        "dni_norm": dni,
        "codigo": 100,
        "email": f"{nombre.lower()}@ruesma.es",
        "estado": estado,
        "tipo_documento": "dni",
    }


EMPLEADOS_3 = [
    _empleado("12345678Z", "Pepe", "Perez"),
    _empleado("87654321X", "Ana", "Lopez"),
    _empleado("11111111H", "Luis", "Gomez"),
]


def _respuesta_empleados(empleados: list[dict]) -> dict:
    return {"ok": True, "total": len(empleados), "data": empleados}


def _mock_transport(
    *,
    empleados: list[dict] | None = None,
    empleados_status: int = 200,
    empleados_body: dict | None = None,
    festivos: dict[str, tuple[int, dict]] | None = None,
    jornada: dict[str, tuple[int, dict]] | None = None,
    calendarios_status: int = 200,
    calendarios_body: dict | None = None,
    peticiones: list[httpx.Request] | None = None,
) -> httpx.MockTransport:
    """Transporte que sirve las rutas de sesame-api que usa el script.

    `festivos` y `jornada` permiten forzar el estado/cuerpo de UN dni
    concreto; el resto recibe la respuesta buena de las fixtures.
    """
    cuerpo_empleados = (
        empleados_body
        if empleados_body is not None
        else _respuesta_empleados(empleados or [])
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if peticiones is not None:
            peticiones.append(request)
        assert request.headers.get("x-api-key") == CLAVE
        path = request.url.path
        if path == "/api/v1/empleados":
            return httpx.Response(empleados_status, json=cuerpo_empleados)
        dni = request.url.params.get("dni")
        if path == "/api/v1/festivos":
            estado, cuerpo = (festivos or {}).get(dni, (200, FESTIVOS_DNI))
            return httpx.Response(estado, json=cuerpo)
        if path == "/api/v1/jornada":
            estado, cuerpo = (jornada or {}).get(dni, (200, JORNADA))
            return httpx.Response(estado, json=cuerpo)
        if path == "/api/v1/calendarios-festivos":
            return httpx.Response(
                calendarios_status,
                json=CALENDARIOS if calendarios_body is None
                else calendarios_body,
            )
        return httpx.Response(404, json={"detail": f"ruta {path} desconocida"})

    return httpx.MockTransport(handler)


def _ejecutar(tmp_path, transport, *extra: str) -> int:
    argv = [
        "--base-url", "http://sesame.test",
        "--api-key", CLAVE,
        "--ano", str(ANO),
        "--salida", str(tmp_path),
        *extra,
    ]
    return vds.main(argv, transport=transport)


def _ficheros(tmp_path) -> tuple[list, list]:
    return (sorted(tmp_path.glob("*.md")), sorted(tmp_path.glob("*.csv")))


def _filas_csv(ruta) -> list[list[str]]:
    texto = ruta.read_text(encoding="utf-8-sig")
    return list(csv.reader(io.StringIO(texto), delimiter=";"))


def _fila(nombre: str, **kwargs) -> vds.FilaTrabajador:
    """FilaTrabajador de laboratorio para los tests de render puro."""
    base = {
        "nombre": nombre,
        "dni": "12345678Z",
        "estado": "active",
        "festivos": (FestivoDia(fecha="2026-01-01", nombre="Ano Nuevo"),),
        "festivos_ok": True,
        "jornada": JornadaContrato(
            tipo="Completa", reducida=False, tipo_contrato="Indefinido"),
        "error": "",
    }
    base.update(kwargs)
    return vds.FilaTrabajador(**base)


# --------------------------------------------------------------- #
# A1 · El informe se genera por trabajador.
# --------------------------------------------------------------- #
def test_f013_a1_genera_informe_md_y_csv_de_tres_trabajadores(tmp_path):
    """Barrido feliz: dos ficheros, una fila por trabajador, sin errores."""
    codigo = _ejecutar(tmp_path, _mock_transport(empleados=EMPLEADOS_3))

    assert codigo == 0
    mds, csvs = _ficheros(tmp_path)
    assert len(mds) == 1 and len(csvs) == 1
    assert mds[0].name.startswith(f"informe_sesame_{ANO}_")

    texto = mds[0].read_text(encoding="utf-8")
    for empleado in EMPLEADOS_3:
        assert empleado["nombre"] in texto
        assert empleado["dni"] in texto
    assert "Empleados: 3 (0 con errores)" in texto

    filas = _filas_csv(csvs[0])
    assert filas[0] == list(vds.COLUMNAS)
    assert len(filas) == 1 + len(EMPLEADOS_3)


def test_f013_a1_el_markdown_trae_todas_las_secciones(tmp_path):
    """Cabecera, calendario por defecto, resumen y tabla por trabajador."""
    _ejecutar(tmp_path, _mock_transport(empleados=EMPLEADOS_3))
    texto = _ficheros(tmp_path)[0][0].read_text(encoding="utf-8")

    assert "# Informe de validacion de datos Sesame" in texto
    assert "## Calendario por defecto" in texto
    assert "## Resumen" in texto
    assert "## Trabajadores" in texto
    # El calendario por defecto de la fixture es 'General' (2 festivos 2026).
    assert "2026-01-06" in texto and "Reyes" in texto
    # El de 2025 NO: el informe es de un ano concreto.
    assert "2025-12-25" not in texto


def test_f013_a1_la_clave_no_aparece_nunca_en_el_informe(tmp_path):
    """La cabecera lleva la base_url, jamas la x-api-key."""
    _ejecutar(tmp_path, _mock_transport(empleados=EMPLEADOS_3))
    mds, csvs = _ficheros(tmp_path)

    md = mds[0].read_text(encoding="utf-8")
    assert "http://sesame.test" in md
    assert CLAVE not in md
    assert CLAVE not in csvs[0].read_text(encoding="utf-8-sig")


def test_f013_a1_los_festivos_se_filtran_al_ano_pedido(tmp_path):
    """La fixture trae un festivo de 2027: no puede colarse en el de 2026."""
    _ejecutar(tmp_path, _mock_transport(empleados=EMPLEADOS_3[:1]))
    filas = _filas_csv(_ficheros(tmp_path)[1][0])

    fila = filas[1]
    columna = dict(zip(vds.COLUMNAS, fila))
    assert columna["n_festivos"] == "2"
    assert "2026-01-01" in columna["festivos"]
    assert "2026-05-15" in columna["festivos"]
    assert "2027" not in columna["festivos"]


def test_f013_a1_por_defecto_pide_solo_los_activos(tmp_path):
    """Sin flags, el listado se pide con solo_activos=true."""
    peticiones: list[httpx.Request] = []
    _ejecutar(tmp_path, _mock_transport(
        empleados=EMPLEADOS_3[:1], peticiones=peticiones))

    listado = [p for p in peticiones if p.url.path == "/api/v1/empleados"]
    assert len(listado) == 1
    assert listado[0].url.params.get("solo_activos") == "true"


def test_f013_a1_incluir_inactivos_pide_todos(tmp_path):
    """`--incluir-inactivos` levanta el filtro de estado."""
    peticiones: list[httpx.Request] = []
    _ejecutar(
        tmp_path,
        _mock_transport(empleados=EMPLEADOS_3[:1], peticiones=peticiones),
        "--incluir-inactivos",
    )

    listado = [p for p in peticiones if p.url.path == "/api/v1/empleados"]
    assert listado[0].url.params.get("solo_activos") == "false"


# --------------------------------------------------------------- #
# A2 · Los errores por trabajador NO abortan el barrido.
# --------------------------------------------------------------- #
def test_f013_a2_dni_sin_casar_en_festivos_es_una_fila_con_error(tmp_path):
    """404 en /festivos: fila con error y los otros dos trabajadores enteros."""
    transporte = _mock_transport(
        empleados=EMPLEADOS_3,
        festivos={"87654321X": (404, NO_ENCONTRADO)},
    )
    codigo = _ejecutar(tmp_path, transporte)

    assert codigo == 0
    filas = {f[1]: dict(zip(vds.COLUMNAS, f))
             for f in _filas_csv(_ficheros(tmp_path)[1][0])[1:]}
    assert len(filas) == 3
    assert filas["87654321X"]["error"] != ""
    assert "404" in filas["87654321X"]["error"]
    assert filas["12345678Z"]["error"] == ""
    assert filas["11111111H"]["n_festivos"] == "2"


def test_f013_a2_upstream_caido_en_jornada_es_una_fila_con_error(tmp_path):
    """502 en /jornada: se anota en la fila, el barrido sigue."""
    transporte = _mock_transport(
        empleados=EMPLEADOS_3,
        jornada={"11111111H": (502, UPSTREAM_KO)},
    )
    codigo = _ejecutar(tmp_path, transporte)

    assert codigo == 0
    filas = {f[1]: dict(zip(vds.COLUMNAS, f))
             for f in _filas_csv(_ficheros(tmp_path)[1][0])[1:]}
    assert "502" in filas["11111111H"]["error"]
    # Los festivos de ese mismo trabajador SI se pudieron leer.
    assert filas["11111111H"]["n_festivos"] == "2"
    assert filas["87654321X"]["error"] == ""


def test_f013_a2_empleado_sin_dni_es_una_fila_con_error(tmp_path):
    """Sin DNI no hay nada que preguntarle a Sesame: se dice y se sigue."""
    sin_dni = _empleado("", "Sin", "Documento")
    sin_dni["dni"] = None
    sin_dni["dni_norm"] = ""
    transporte = _mock_transport(empleados=[sin_dni, EMPLEADOS_3[0]])

    assert _ejecutar(tmp_path, transporte) == 0
    filas = _filas_csv(_ficheros(tmp_path)[1][0])[1:]
    errores = [f for f in filas if dict(zip(vds.COLUMNAS, f))["error"]]
    assert len(errores) == 1
    sin_datos = dict(zip(vds.COLUMNAS, errores[0]))
    assert "sin DNI" in sin_datos["error"]
    # No se le pregunto nada a Sesame: no puede figurar con cero festivos.
    assert sin_datos["n_festivos"] == vds.DESCONOCIDO


def test_f013_a2_el_resumen_lista_los_dnis_con_error(tmp_path):
    """El humano tiene que ver de un vistazo a quien hay que mirar."""
    transporte = _mock_transport(
        empleados=EMPLEADOS_3,
        festivos={"87654321X": (404, NO_ENCONTRADO)},
    )
    _ejecutar(tmp_path, transporte)
    texto = _ficheros(tmp_path)[0][0].read_text(encoding="utf-8")

    cabeza, _, resumen = texto.partition("## Resumen")
    assert "87654321X" in resumen.split("## Trabajadores")[0]
    assert "Empleados: 3 (1 con errores)" in cabeza


def test_f013_a2_los_dos_fallos_del_mismo_trabajador_se_acumulan(tmp_path):
    """Festivos caidos (502) Y jornada sin casar (404) en la misma fila."""
    transporte = _mock_transport(
        empleados=EMPLEADOS_3,
        festivos={"12345678Z": (502, UPSTREAM_KO)},
        jornada={"12345678Z": (404, NO_ENCONTRADO)},
    )
    codigo = _ejecutar(tmp_path, transporte)

    assert codigo == 0
    filas = {f[1]: dict(zip(vds.COLUMNAS, f))
             for f in _filas_csv(_ficheros(tmp_path)[1][0])[1:]}
    fila = filas["12345678Z"]
    assert "festivos: " in fila["error"] and "502" in fila["error"]
    assert "jornada: " in fila["error"] and "404" in fila["error"]
    # Sin festivos leidos, el recuento NO puede fingir un cero.
    assert fila["n_festivos"] == vds.DESCONOCIDO
    assert fila["jornada_tipo"] == vds.DESCONOCIDO
    assert filas["87654321X"]["error"] == ""


def test_f013_a2_ningun_calendario_por_defecto_se_dice_en_el_informe(tmp_path):
    """Sesame sin calendario `por_defecto`: no es un error, pero se avisa."""
    sin_defecto = {
        "ok": True, "total": 1,
        "data": [{"id": "cal-x", "nombre": "X", "por_defecto": False,
                  "festivos": []}],
    }
    transporte = _mock_transport(
        empleados=EMPLEADOS_3[:1], calendarios_body=sin_defecto)

    assert _ejecutar(tmp_path, transporte) == 0
    texto = _ficheros(tmp_path)[0][0].read_text(encoding="utf-8")
    assert "ningun calendario" in texto.lower()


def test_f013_a2_el_calendario_por_defecto_roto_no_tumba_el_informe(tmp_path):
    """Si /calendarios-festivos falla, esa seccion avisa y el resto sale."""
    transporte = _mock_transport(
        empleados=EMPLEADOS_3[:1], calendarios_status=502)
    codigo = _ejecutar(tmp_path, transporte)

    assert codigo == 0
    texto = _ficheros(tmp_path)[0][0].read_text(encoding="utf-8")
    assert "## Calendario por defecto" in texto
    assert "502" in texto
    assert "Pepe" in texto


# --------------------------------------------------------------- #
# Aborta SOLO si falla el listado o la configuracion.
# --------------------------------------------------------------- #
def test_f013_r_fallo_del_listado_aborta_con_codigo_1(tmp_path, capsys):
    """Sin lista de empleados no hay informe: exit 1, sin ficheros y con motivo.

    El mensaje tiene que traer lo que respondio sesame-api: "fallo el
    listado" a secas no le sirve a nadie para arreglarlo.
    """
    transporte = _mock_transport(
        empleados=EMPLEADOS_3, empleados_status=502, empleados_body=UPSTREAM_KO)

    assert _ejecutar(tmp_path, transporte) == 1
    assert _ficheros(tmp_path) == ([], [])
    error = capsys.readouterr().err
    assert "ABORTADO" in error
    assert "502" in error
    assert "Sesame respondio 429" in error   # el cuerpo real del upstream


def test_f013_r_listado_con_ok_false_aborta(tmp_path):
    """`ok=false` con HTTP 200 tambien es un fallo de listado."""
    transporte = _mock_transport(
        empleados=EMPLEADOS_3, empleados_body={"ok": False, "data": []})

    assert _ejecutar(tmp_path, transporte) == 1
    assert _ficheros(tmp_path) == ([], [])


def test_f013_r_listado_sin_el_campo_ok_aborta(tmp_path):
    """Si falta `ok`, NO se asume que todo fue bien: no es el contrato."""
    transporte = _mock_transport(
        empleados=EMPLEADOS_3, empleados_body={"total": 0, "data": []})

    assert _ejecutar(tmp_path, transporte) == 1
    assert _ficheros(tmp_path) == ([], [])


def test_f013_r_un_400_del_listado_tambien_aborta(tmp_path):
    """400 es el primer codigo de error: la frontera cuenta como fallo."""
    transporte = _mock_transport(
        empleados=EMPLEADOS_3, empleados_status=400,
        empleados_body={"detail": "peticion invalida"})

    assert _ejecutar(tmp_path, transporte) == 1
    assert _ficheros(tmp_path) == ([], [])


def test_f013_r_listado_con_data_que_no_es_lista_aborta(tmp_path):
    """Contrato roto de sesame-api: se dice, no se procesa medio informe."""
    transporte = _mock_transport(
        empleados=EMPLEADOS_3, empleados_body={"ok": True, "data": {"a": 1}})

    assert _ejecutar(tmp_path, transporte) != 0
    assert _ficheros(tmp_path) == ([], [])


def test_f013_r_listado_que_no_es_json_aborta(tmp_path):
    """Un proxy devolviendo HTML no puede pasar por una lista vacia."""
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>proxy</html>")

    assert _ejecutar(tmp_path, httpx.MockTransport(handler)) != 0
    assert _ficheros(tmp_path) == ([], [])


def test_f013_r_sesame_api_inalcanzable_aborta(tmp_path):
    """Sin conexion no hay barrido: mensaje claro y exit != 0."""
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("conexion rechazada", request=request)

    assert _ejecutar(tmp_path, httpx.MockTransport(handler)) != 0
    assert _ficheros(tmp_path) == ([], [])


def test_f013_r_el_fichero_env_alimenta_la_configuracion(tmp_path, monkeypatch):
    """`--env`: mismos nombres de variable que config/settings.py."""
    monkeypatch.delenv("SESAME_API_KEY", raising=False)
    monkeypatch.delenv("SESAME_API_BASE_URL", raising=False)
    env = tmp_path / "sesame.env"
    env.write_text(
        "# fichero de ejemplo\n"
        "#SESAME_API_BASE_URL=http://viejo.test\n"   # comentada: se ignora
        "\n"
        "SESAME_API_BASE_URL=http://sesame.test\n"
        f'SESAME_API_KEY="{CLAVE}"\n'
        "OTRA_COSA\n",
        encoding="utf-8",
    )

    codigo = vds.main(
        ["--env", str(env), "--ano", str(ANO), "--salida", str(tmp_path)],
        transport=_mock_transport(empleados=EMPLEADOS_3[:1]),
    )

    assert codigo == 0
    texto = _ficheros(tmp_path)[0][0].read_text(encoding="utf-8")
    assert "sesame-api: http://sesame.test" in texto
    assert "viejo.test" not in texto


def test_f013_r_leer_env_no_parte_el_valor_por_cada_igual(tmp_path):
    """Una clave en base64 acaba en `=`: solo se parte por el PRIMER `=`."""
    env = tmp_path / "sesame.env"
    env.write_text("SESAME_API_KEY=abc=def==\n", encoding="utf-8")

    assert vds.leer_env(env) == {"SESAME_API_KEY": "abc=def=="}


def test_f013_r_leer_env_ignora_comentarios_y_lineas_sueltas(tmp_path):
    """Una variable comentada NO se aplica aunque lleve `=`."""
    env = tmp_path / "sesame.env"
    env.write_text(
        "# comentario\n#SESAME_API_KEY=vieja\n\nOTRA_COSA\nA=1\n",
        encoding="utf-8",
    )

    assert vds.leer_env(env) == {"A": "1"}


def test_f013_r_env_inexistente_aborta(tmp_path):
    """Un `--env` mal escrito no puede degradar en silencio a los defectos."""
    codigo = vds.main(
        ["--env", str(tmp_path / "no-existe.env"), "--salida", str(tmp_path)],
        transport=None,
    )

    assert codigo == 2          # 2 = configuracion, 1 = fallo de sesame-api
    assert _ficheros(tmp_path) == ([], [])


def test_f013_r_sin_api_key_aborta_sin_llamar_a_nadie(tmp_path, monkeypatch):
    """Sin clave ni por CLI ni por entorno: mensaje claro y exit 2."""
    monkeypatch.delenv("SESAME_API_KEY", raising=False)
    monkeypatch.delenv("SESAME_API_BASE_URL", raising=False)

    codigo = vds.main(
        ["--ano", str(ANO), "--salida", str(tmp_path)], transport=None)

    assert codigo == 2
    assert _ficheros(tmp_path) == ([], [])


def test_f013_r_la_clave_del_entorno_sirve_de_respaldo(tmp_path, monkeypatch):
    """Sin `--api-key`, se leen SESAME_API_* (los nombres de settings.py)."""
    monkeypatch.setenv("SESAME_API_KEY", CLAVE)
    monkeypatch.setenv("SESAME_API_BASE_URL", "http://sesame.test")

    codigo = vds.main(
        ["--ano", str(ANO), "--salida", str(tmp_path)],
        transport=_mock_transport(empleados=EMPLEADOS_3[:1]),
    )

    assert codigo == 0
    mds = _ficheros(tmp_path)[0]
    assert len(mds) == 1
    # La base_url del entorno se USA, no se cae al localhost por defecto.
    assert "sesame-api: http://sesame.test" in mds[0].read_text(
        encoding="utf-8")


def test_f013_r_la_carpeta_de_salida_se_crea_con_sus_padres(tmp_path):
    """`--salida` a una ruta anidada que aun no existe: se crea entera."""
    destino = tmp_path / "informes" / "sesame" / "2026"

    codigo = vds.main(
        ["--base-url", "http://sesame.test", "--api-key", CLAVE,
         "--ano", str(ANO), "--salida", str(destino)],
        transport=_mock_transport(empleados=EMPLEADOS_3[:1]),
    )

    assert codigo == 0
    assert len(_ficheros(destino)[0]) == 1


def test_f013_r_el_estado_del_empleado_viaja_al_informe(tmp_path):
    """Saber si Sesame lo tiene de baja es parte de lo que se valida."""
    de_baja = _empleado("99999999R", "Eva", "Ruiz", estado="inactive")
    sin_estado = _empleado("88888888P", "Mar", "Diaz")
    sin_estado["estado"] = None
    transporte = _mock_transport(
        empleados=[EMPLEADOS_3[0], de_baja, sin_estado])

    assert _ejecutar(tmp_path, transporte, "--incluir-inactivos") == 0
    filas = {f[1]: dict(zip(vds.COLUMNAS, f))
             for f in _filas_csv(_ficheros(tmp_path)[1][0])[1:]}
    assert filas["12345678Z"]["estado"] == "active"
    assert filas["99999999R"]["estado"] == "inactive"
    assert filas["88888888P"]["estado"] == vds.DESCONOCIDO


def test_f013_r_sin_dni_norm_se_pregunta_con_el_dni_sin_normalizar(tmp_path):
    """`dni_norm` vacio no puede dejar fuera a un empleado que SI tiene DNI."""
    raro = _empleado("12345678Z", "Pepe", "Perez")
    raro["dni_norm"] = ""
    peticiones: list[httpx.Request] = []
    transporte = _mock_transport(empleados=[raro], peticiones=peticiones)

    assert _ejecutar(tmp_path, transporte) == 0
    consultados = {p.url.params.get("dni") for p in peticiones
                   if p.url.path == "/api/v1/festivos"}
    assert consultados == {"12345678Z"}
    fila = dict(zip(vds.COLUMNAS, _filas_csv(_ficheros(tmp_path)[1][0])[1]))
    assert fila["dni"] == "12345678Z"
    assert fila["error"] == ""


# --------------------------------------------------------------- #
# Logica pura: resumen y render.
# --------------------------------------------------------------- #
def test_f013_r_resumir_agrupa_festivos_jornada_y_errores():
    """El resumen cuenta lo que el humano compara contra la realidad."""
    filas = [
        _fila("A"),
        _fila("B"),
        _fila("C", jornada=JornadaContrato(
            tipo="Parcial", reducida=True, tipo_contrato="Temporal")),
        _fila("D", festivos=(), festivos_ok=False, jornada=None,
              error="festivos: 404"),
    ]

    resumen = vds.resumir(filas)

    assert resumen.total == 4
    assert resumen.con_error == 1
    assert resumen.dist_festivos == {1: 3}
    assert resumen.dist_tipo == {"Completa": 2, "Parcial": 1,
                                 vds.DESCONOCIDO: 1}
    assert resumen.dist_reducida == {"no": 2, "si": 1, vds.DESCONOCIDO: 1}
    assert [d for d, _ in resumen.dnis_con_error] == ["12345678Z"]


def test_f013_r_render_csv_usa_punto_y_coma_y_una_fila_por_trabajador():
    """CSV para Excel espanol (docs/CONVENTIONS.md): separador `;`."""
    texto = vds.render_csv([_fila("Pepe Perez"), _fila("Ana Lopez")])

    assert texto.splitlines()[0] == ";".join(vds.COLUMNAS)
    filas = list(csv.reader(io.StringIO(texto), delimiter=";"))
    assert len(filas) == 3
    assert filas[1][0] == "Pepe Perez"


def test_f013_r_render_csv_lista_los_festivos_en_una_celda():
    """Los festivos viajan como `fecha nombre | fecha nombre`."""
    fila = _fila("Pepe", festivos=(
        FestivoDia(fecha="2026-01-01", nombre="Ano Nuevo"),
        FestivoDia(fecha="2026-05-15", nombre=None),
    ))
    filas = list(csv.reader(io.StringIO(vds.render_csv([fila])),
                            delimiter=";"))

    celda = dict(zip(vds.COLUMNAS, filas[1]))["festivos"]
    assert celda == "2026-01-01 Ano Nuevo | 2026-05-15"


def test_f013_r_render_markdown_escapa_las_barras_de_la_tabla():
    """Una barra en un dato no puede partir la tabla Markdown."""
    fila = _fila("Perez | Gomez")
    texto = vds.render_markdown(
        meta=vds.MetaInforme(generado="2026-08-17 10:00", ano=ANO,
                             base_url="http://sesame.test", solo_activos=True),
        filas=[fila], resumen=vds.resumir([fila]),
        calendario=(), calendario_error="",
    )

    linea = next(x for x in texto.splitlines() if "Gomez" in x)
    assert r"Perez \| Gomez" in linea
    # Quitadas las barras escapadas, solo quedan las que delimitan columnas.
    assert linea.replace(r"\|", "").count("|") == len(vds.COLUMNAS) + 1


def test_f013_r_render_markdown_avisa_si_no_hay_calendario_por_defecto():
    """Ningun calendario marcado por defecto: se dice, no se calla."""
    texto = vds.render_markdown(
        meta=vds.MetaInforme(generado="2026-08-17 10:00", ano=ANO,
                             base_url="http://sesame.test", solo_activos=True),
        filas=[], resumen=vds.resumir([]),
        calendario=None, calendario_error="",
    )

    assert "## Calendario por defecto" in texto
    assert "ningun calendario" in texto.lower()
    # Sin trabajadores, el resumen lo dice en vez de mostrar listas vacias.
    assert "(sin datos)" in texto


def test_f013_r_render_markdown_cuenta_los_trabajadores_de_cada_grupo():
    """El resumen se lee solo: "2 festivos: 3 trabajadores"."""
    filas = [_fila("A"), _fila("B"), _fila("C", festivos=())]
    texto = vds.render_markdown(
        meta=vds.MetaInforme(generado="2026-08-17 10:00", ano=ANO,
                             base_url="http://sesame.test", solo_activos=True),
        filas=filas, resumen=vds.resumir(filas),
        calendario=(), calendario_error="",
    )

    assert "- 1 festivos: 2 trabajadores" in texto
    assert "- 0 festivos: 1 trabajador\n" in texto      # singular, sin "es"


def test_f013_r_recorta_los_cuerpos_de_error_kilometricos():
    """Una pagina de error de un proxy no puede inundar una celda del CSV."""
    recorte = vds._recorta(RuntimeError("x" * 500))

    assert len(recorte) == 300


def test_f013_r_las_estructuras_del_informe_son_inmutables():
    """Construida una fila, nadie la retoca por el camino hasta el fichero."""
    from dataclasses import FrozenInstanceError

    fila = _fila("Pepe")
    resumen = vds.resumir([fila])
    meta = vds.MetaInforme(generado="2026-08-17 10:00", ano=ANO,
                           base_url="http://sesame.test", solo_activos=True)

    for objeto, campo in ((fila, "nombre"), (resumen, "total"),
                          (meta, "base_url")):
        with pytest.raises(FrozenInstanceError):
            setattr(objeto, campo, "otra cosa")


@pytest.mark.parametrize("valor,esperado", [
    (True, "si"), (False, "no"), (None, vds.DESCONOCIDO),
])
def test_f013_r_formato_de_booleanos(valor, esperado):
    """`reducida` es tri-estado: si / no / desconocido."""
    assert vds.fmt_bool(valor) == esperado
