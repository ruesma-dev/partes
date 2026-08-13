# prueba_escritura_sigrid.py
"""Prueba de ESCRITURA de partes de trabajo (hmo/hmores) en Sigrid.

Proceso manual que replica (correo J. Romero 24/07/2026):
  1. El parte de trabajo (PT26/xxxxx) es UNO por obra y mes. Se crea una
     sola vez: cabecera en `con` + extension `hmo`.
  2. Las lineas (`hmores`) se anaden recurso a recurso, con la fecha REAL
     de trabajo, tipo de hora (horide) y cantidad (puede ser NEGATIVA).
  3. REGLAS de que se registra:
       - Ordinarias: SOLO si el recurso tiene hora laborable ('HL%').
         Los codigos MENSUALES (MENC, MCAP...) NO se registran nunca.
       - Extras: SOLO si el recurso tiene hora extra ('HE%').
       - Trabajador SIN ningun 'HE%': NO se registra NADA (encargados y
         demas mensuales; sus horas van por el mensual).
       - Capataz (MCAP + HECAP): sin 'HL%' -> ordinarias fuera; con 'HE%'
         -> SOLO sus extras (sale solo de las dos reglas anteriores).

Mapeo CONFIRMADO contra datos reales (fase 'inspeccionar', 25/07/2026):
  con    : emp=1, tip=35, est=1, cod='PT26/xxxxx', res='Parte <obra>',
           fec = ULTIMO DIA del mes del parte (no la fecha de creacion).
  hmo    : mismo ide que con; cenide (cen de la obra), obride, ano, mes;
           reside vacio (parte de obra, no de recurso).
  hmores : hmoide, reside, cenide, obride, pos (de 64 en 64), fec (dia
           real), horide, can = HORAS, pre (de reshor), tot = can*pre,
           ano, mes, fac=0, ortide=0 (NOT NULL sin default), paride=0,
           caaide=0 (las lineas diarias reales la llevan a 0).

TODAS las pruebas van contra la OBRA DE PRUEBAS (0404), diga lo que diga
el parte. Las lineas se marcan con tex='PRUEBA-IA' para poder limpiarlas.

USO (fases):
  python prueba_escritura_sigrid.py inspeccionar     # SOLO LECTURA
  python prueba_escritura_sigrid.py estado           # SOLO LECTURA
  python prueba_escritura_sigrid.py crear [--ejecutar]
  python prueba_escritura_sigrid.py lineas [--ejecutar]
  python prueba_escritura_sigrid.py verificar        # SOLO LECTURA
  python prueba_escritura_sigrid.py limpiar [--ejecutar]

Sin --ejecutar, 'crear', 'lineas' y 'limpiar' hacen DRY-RUN: imprimen el
SQL exacto y NO escriben.
"""
from __future__ import annotations

import calendar
import json
import sys
from pathlib import Path

import httpx

# ----------------------------- CONFIG ----------------------------- #
ENV_PATH = Path(r"C:\Users\pgris\PycharmProjects\partes-transfer\.env")

OBRA_COD_PRUEBAS = "0404"   # TODAS las escrituras van aqui
ANO, MES = 2026, 8

# Recursos de prueba (de las sesiones anteriores):
RECURSOS_PRUEBA = [
    # gruista: HLGR + HEGR -> registra ordinarias Y extras
    {"reside": 2717792, "nombre": "ROLDAN JIMENEZ, FRANCISCO J. (gruista)",
     "fecha": 20260719, "ord": 6.0, "extra": 9.0},
    # encargado: solo MENC (mensual) -> NO se registra nada
    {"reside": 2364457, "nombre": "GOMEZ GARCIA, JOSE (encargado)",
     "fecha": 20260719, "ord": 10.0, "extra": 0.0},
]

MARCA = "PRUEBA-IA"          # hmores.tex de las lineas, para limpiarlas
DB_WRITE = "ruesma"          # la escritura SOLO permite ruesma

# Constantes confirmadas en partes PT reales:
TIP_PARTE_TRABAJO = 35       # con.tip de un parte de trabajo
EST_ACTIVO = 1               # con.est (los cerrados de anos viejos: 10)
PASO_POS = 64                # hmores.pos va de 64 en 64 (64,128,192...)
# ------------------------------------------------------------------ #


def _leer_dotenv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        raise SystemExit(f"No existe {path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


CFG = _leer_dotenv(ENV_PATH)
BASE = CFG["SIGRID_API_BASE_URL"].rstrip("/")
KEY = CFG["SIGRID_API_FUNCTION_KEY"]
HEADERS = {"x-functions-key": KEY, "Content-Type": "application/json"}


def sql_read(sql: str, parameters: list, database: str = DB_WRITE) -> list[dict]:
    r = httpx.post(f"{BASE}/api/sql/read", headers=HEADERS, timeout=90, json={
        "database": database, "sql": sql, "parameters": parameters,
        "timeout_seconds": 60, "max_rows": 1000,
    })
    if r.status_code >= 400:
        raise SystemExit(f"sql/read HTTP {r.status_code}:\n{r.text[:600]}")
    body = r.json()
    if not body.get("ok"):
        raise SystemExit(f"sql/read ok=false: {json.dumps(body)[:600]}")
    cols = [c.lower() for c in body["columns"]]
    return [dict(zip(cols, row)) for row in body["rows"]]


def sql_write(statements: list[dict], *, ejecutar: bool) -> None:
    print(f"\n--- {'EJECUTANDO' if ejecutar else 'DRY-RUN (no escribe)'} "
          f"batch de {len(statements)} sentencia(s) en {DB_WRITE} ---")
    for st in statements:
        print("  SQL :", " ".join(st["sql"].split()))
        print("  PARM:", st["parameters"])
    if not ejecutar:
        print("--- fin DRY-RUN (anade --ejecutar para escribir) ---")
        return
    r = httpx.post(f"{BASE}/api/sql/write", headers=HEADERS, timeout=120, json={
        "database": DB_WRITE, "statements": statements,
    })
    if r.status_code >= 400:
        raise SystemExit(f"sql/write HTTP {r.status_code}:\n{r.text[:800]}")
    body = r.json()
    print("Respuesta:", json.dumps(body, ensure_ascii=False)[:400])
    if not body.get("ok") or not body.get("committed"):
        raise SystemExit("ESCRITURA NO CONFIRMADA (ok/committed false)")


# --------------------- esquema real (autodescubierto) --------------------- #

_COLS: dict[str, dict[str, dict]] = {}


def columnas(tabla: str) -> dict[str, dict]:
    """{columna: {tipo, nullable, default, maxlen}} leido de la propia BD."""
    if tabla not in _COLS:
        filas = sql_read(
            "SELECT COLUMN_NAME AS c, DATA_TYPE AS t, IS_NULLABLE AS n, "
            "COLUMN_DEFAULT AS d, CHARACTER_MAXIMUM_LENGTH AS ml "
            "FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ? "
            "ORDER BY ORDINAL_POSITION", [tabla],
        )
        _COLS[tabla] = {
            (f["c"] or "").lower(): {
                "tipo": (f["t"] or "").lower(), "nullable": f["n"] == "YES",
                "default": f["d"], "maxlen": f["ml"],
            } for f in filas
        }
        if not _COLS[tabla]:
            raise SystemExit(f"La tabla '{tabla}' no existe en {DB_WRITE}")
    return _COLS[tabla]


def obligatorias(tabla: str) -> list[str]:
    """NOT NULL y sin DEFAULT: hay que darles valor en el INSERT."""
    return [c for c, m in columnas(tabla).items()
            if not m["nullable"] and m["default"] is None and c != "ide"]


def filtrar(tabla: str, campos: dict) -> dict:
    """Descarta campos que no son columnas y trunca textos a su longitud."""
    cols = columnas(tabla)
    out, fuera = {}, []
    for k, v in campos.items():
        meta = cols.get(k.lower())
        if meta is None:
            fuera.append(k)
            continue
        ml = meta.get("maxlen")
        if isinstance(v, str) and ml and ml > 0 and len(v) > ml:
            print(f"  [aviso] {tabla}.{k}: texto truncado a {ml} caracteres")
            v = v[:ml]
        out[k] = v
    if fuera:
        print(f"  [aviso] {tabla}: columnas inexistentes descartadas -> "
              f"{', '.join(fuera)}")
    return out


def insert_max_ide(tabla: str, campos: dict) -> dict:
    """INSERT con ide = MAX(ide)+1 bloqueando la tabla (patron de la casa)."""
    campos = filtrar(tabla, campos)
    cols = list(campos.keys())
    marcas = ", ".join("?" for _ in cols)
    sql = (f"INSERT INTO {tabla} (ide, {', '.join(cols)}) "
           f"SELECT ISNULL(MAX(ide),0)+1, {marcas} "
           f"FROM {tabla} WITH (UPDLOCK, HOLDLOCK)")
    return {"sql": sql, "parameters": list(campos.values())}


def cond_marca(col: str = "tex") -> str:
    """Comparacion de la marca a prueba de columnas TEXT/NTEXT (en SQL
    Server no admiten '=' directo)."""
    tipo = columnas("hmores").get(col, {}).get("tipo", "")
    if tipo in ("text", "ntext", "image"):
        return f"CAST({col} AS NVARCHAR(200)) = ?"
    return f"{col} = ?"


def _no_vacio(d: dict) -> dict:
    """Solo los campos con valor real: para ver que rellena Sigrid."""
    return {k: v for k, v in d.items()
            if v not in (None, 0, 0.0, "", " ")}


# ------------------------- lecturas base ------------------------- #

def obra_pruebas() -> dict:
    filas = sql_read(
        "SELECT obr.ide AS ide, con.cod AS cod, con.res AS res, "
        "obr.cenide AS cenide "
        "FROM obr JOIN con ON con.ide = obr.ide WHERE con.cod = ?",
        [OBRA_COD_PRUEBAS],
    )
    if not filas:
        raise SystemExit(f"Obra {OBRA_COD_PRUEBAS} no encontrada")
    return filas[0]


def parte_mes(obra_ide: int) -> dict | None:
    filas = sql_read(
        "SELECT hmo.ide AS ide, con.cod AS cod, con.res AS res, "
        "hmo.ano AS ano, hmo.mes AS mes, hmo.cenide AS cenide, "
        "hmo.reside AS reside "
        "FROM hmo JOIN con ON con.ide = hmo.ide "
        "WHERE hmo.obride = ? AND hmo.ano = ? AND hmo.mes = ? "
        "AND ISNULL(hmo.reside, 0) = 0",
        [obra_ide, ANO, MES],
    )
    return filas[0] if filas else None


def horas_recurso(reside: int) -> dict[str, dict]:
    """Horas del recurso en reshor: {'HL': {...}, 'HE': {...}} (1a de cada)."""
    filas = sql_read(
        "SELECT reshor.horide AS horide, auxhor.cod AS cod, "
        "auxhor.res AS res, reshor.pre AS pre "
        "FROM reshor JOIN auxhor ON auxhor.ide = reshor.horide "
        "WHERE reshor.reside = ? ORDER BY auxhor.cod",
        [reside],
    )
    out: dict[str, dict] = {}
    for f in filas:
        cod = (f["cod"] or "").upper()
        if cod.startswith("HL") and "HL" not in out:
            out["HL"] = f
        elif cod.startswith("HE") and "HE" not in out:
            out["HE"] = f
    return out


# --------------------------- fases --------------------------- #

def fase_inspeccionar() -> None:
    """SOLO LECTURA. Esquema real + partes de la obra de pruebas + lineas
    DIARIAS (HL/HE) reales de cualquier obra (son el modelo vivo; la 0404
    no tiene partes recientes) + caaide + convenio de pos."""
    obra = obra_pruebas()
    print(f"Obra pruebas: ide={obra['ide']} cod={obra['cod']} "
          f"cenide={obra['cenide']} {obra['res']}\n")

    for tabla in ("con", "hmo", "hmores"):
        print(f"== {tabla}: {len(columnas(tabla))} columnas ==")
        print("  OBLIGATORIAS (NOT NULL sin default):",
              ", ".join(obligatorias(tabla)) or "(ninguna)")
    print()

    print(f"== Partes (hmo) de la obra {OBRA_COD_PRUEBAS} ==")
    mios = sql_read(
        "SELECT TOP 5 hmo.*, con.cod AS con_cod, con.res AS con_res, "
        "con.fec AS con_fec, con.tip AS con_tip, con.est AS con_est "
        "FROM hmo JOIN con ON con.ide = hmo.ide "
        "WHERE hmo.obride = ? ORDER BY hmo.ano DESC, hmo.mes DESC",
        [obra["ide"]],
    )
    if not mios:
        print("  (ninguno)")
    for f in mios:
        print(" ", json.dumps(_no_vacio(f), ensure_ascii=False, default=str))
        n = sql_read("SELECT COUNT(*) AS n FROM hmores WHERE hmoide = ?",
                     [f["ide"]])
        print(f"     lineas: {n[0]['n']}")

    print("\n== LINEAS DIARIAS reales (hora HL%/HE%), campos con valor ==")
    diarias = sql_read(
        "SELECT TOP 6 hmores.*, auxhor.cod AS hora_cod, auxhor.res AS hora_res "
        "FROM hmores JOIN auxhor ON auxhor.ide = hmores.horide "
        "WHERE (auxhor.cod LIKE 'HL%' OR auxhor.cod LIKE 'HE%') "
        "ORDER BY hmores.ide DESC", [],
    )
    for f in diarias:
        print(" ", json.dumps(_no_vacio(f), ensure_ascii=False, default=str))

    print("\n== Convenio de 'pos' ==")
    pp = sql_read(
        "SELECT TOP 1 hmoide, COUNT(*) AS n, MIN(pos) AS minpos, "
        "MAX(pos) AS maxpos FROM hmores GROUP BY hmoide "
        "HAVING COUNT(*) > 5 ORDER BY MAX(hmoide) DESC", [],
    )
    for f in pp:
        print(" ", json.dumps(f, ensure_ascii=False, default=str))

    print("\n== Siguiente codigo PT que propondriamos ==")
    print(" ", _siguiente_cod_pt(), "(Sigrid propuso PT26/00251 en el correo)")
    print("\n>>> Pega esta salida en el chat antes del primer --ejecutar.")


def fase_estado() -> None:
    obra = obra_pruebas()
    pt = parte_mes(obra["ide"])
    if pt:
        print(f"EXISTE parte {ANO}/{MES:02d} de obra {OBRA_COD_PRUEBAS}: "
              f"{pt['cod']} (ide={pt['ide']})")
        n = sql_read("SELECT COUNT(*) AS n FROM hmores WHERE hmoide = ?",
                     [pt["ide"]])
        print(f"  lineas actuales: {n[0]['n']}")
    else:
        print(f"NO existe parte {ANO}/{MES:02d} de obra {OBRA_COD_PRUEBAS}: "
              f"hay que crearlo ('crear')")


def _siguiente_cod_pt() -> str:
    yy = str(ANO)[-2:]
    filas = sql_read(
        "SELECT MAX(cod) AS maxcod FROM con WHERE cod LIKE ?",
        [f"PT{yy}/%"],
    )
    maxcod = (filas[0]["maxcod"] or "") if filas else ""
    try:
        n = int(maxcod.split("/")[1]) + 1
    except (IndexError, ValueError):
        n = 1
    return f"PT{yy}/{n:05d}"


def fase_crear(ejecutar: bool) -> None:
    obra = obra_pruebas()
    if parte_mes(obra["ide"]):
        print("Ya existe el parte del mes: nada que crear.")
        return
    cod = _siguiente_cod_pt()
    desc = f"Parte {obra['res']} ({MARCA})"
    # Los partes reales llevan fec = ULTIMO DIA del mes del parte
    # (PT26/00250 -> 20260731; los de la 0404 -> 20200930, 20200831...).
    ultimo = calendar.monthrange(ANO, MES)[1]
    fec = int(f"{ANO}{MES:02d}{ultimo:02d}")
    print(f"Se creara {cod} · '{desc}' · obra {obra['cod']} "
          f"(cen {obra['cenide']}) · {ANO}/{MES:02d} · fec={fec} "
          f"· tip={TIP_PARTE_TRABAJO} est={EST_ACTIVO}")

    st_con = insert_max_ide("con", {
        "emp": int(CFG.get("SIGRID_EMPRESA", "1")),
        "tip": TIP_PARTE_TRABAJO, "est": EST_ACTIVO,
        "cod": cod, "res": desc, "fec": fec,
    })
    # hmo comparte ide con con (extension 1:1).
    campos_hmo = filtrar("hmo", {
        "cenide": obra["cenide"], "obride": obra["ide"],
        "ano": ANO, "mes": MES, "reside": 0, "cenmul": 0,
    })
    cols = list(campos_hmo.keys())
    # El ide se toma de la cabecera recien creada. Se filtra TAMBIEN por
    # tip para que no pueda casar con otro documento del mismo codigo.
    st_hmo = {
        "sql": (f"INSERT INTO hmo (ide, {', '.join(cols)}) "
                f"SELECT ide, {', '.join('?' for _ in cols)} "
                f"FROM con WHERE cod = ? AND tip = ?"),
        "parameters": list(campos_hmo.values()) + [cod, TIP_PARTE_TRABAJO],
    }
    sql_write([st_con, st_hmo], ejecutar=ejecutar)
    if ejecutar:
        print("Verificacion:", parte_mes(obra["ide"]))
        print("Siguiente codigo libre ahora:", _siguiente_cod_pt())


def fase_lineas(ejecutar: bool) -> None:
    obra = obra_pruebas()
    pt = parte_mes(obra["ide"])
    if not pt:
        raise SystemExit("No existe el parte del mes: ejecuta antes 'crear'.")
    filas = sql_read("SELECT ISNULL(MAX(pos),0) AS maxpos FROM hmores "
                     "WHERE hmoide = ?", [pt["ide"]])
    pos = int(filas[0]["maxpos"] or 0)

    statements: list[dict] = []
    for rec in RECURSOS_PRUEBA:
        horas = horas_recurso(rec["reside"])
        print(f"\nRecurso {rec['reside']} · {rec['nombre']}: "
              f"HL={horas.get('HL', {}).get('cod')} "
              f"HE={horas.get('HE', {}).get('cod')}")
        if "HE" not in horas:
            print("  >>> SIN codigo HE%: NO SE REGISTRA NADA "
                  "(regla encargados/mensuales)")
            continue
        lineas: list[tuple[dict, float, str]] = []
        if rec["ord"] and "HL" in horas:
            lineas.append((horas["HL"], rec["ord"], "ordinaria"))
        elif rec["ord"]:
            print("  ordinarias omitidas: sin codigo HL% (mensual) "
                  "-> solo extras (regla capataz)")
        if rec["extra"]:
            lineas.append((horas["HE"], rec["extra"], "extra"))
        for hora, can, tipo in lineas:
            pos += PASO_POS
            pre = float(hora.get("pre") or 0.0)
            tot = round(can * pre, 2)
            print(f"  + pos={pos} {tipo}: {hora['cod']} can={can} pre={pre} "
                  f"tot={tot} fec={rec['fecha']}")
            # ortide es NOT NULL sin default -> 0 (las lineas reales lo
            # tienen a 0). paride y caaide van a 0 como las diarias reales.
            statements.append(insert_max_ide("hmores", {
                "hmoide": pt["ide"], "reside": rec["reside"],
                "cenide": pt["cenide"] or obra["cenide"],
                "obride": obra["ide"], "paride": 0, "pos": pos,
                "fec": rec["fecha"], "horide": hora["horide"],
                "can": can, "pre": pre, "tot": tot,
                "ano": ANO, "mes": MES, "fac": 0, "ortide": 0, "caaide": 0,
                "tex": MARCA,
            }))
    if not statements:
        print("\nNada que insertar.")
        return
    sql_write(statements, ejecutar=ejecutar)
    if ejecutar:
        print()
        fase_verificar()


def fase_verificar() -> None:
    obra = obra_pruebas()
    pt = parte_mes(obra["ide"])
    if not pt:
        print("No existe el parte del mes.")
        return
    print(f"Parte {pt['cod']} (ide={pt['ide']}) · lineas:")
    lin = sql_read(
        "SELECT hmores.pos AS pos, hmores.fec AS fec, auxhor.cod AS hora, "
        "auxhor.res AS hora_res, hmores.can AS can, hmores.pre AS pre, "
        "hmores.tot AS tot, con.res AS recurso "
        "FROM hmores "
        "JOIN auxhor ON auxhor.ide = hmores.horide "
        "JOIN con ON con.ide = hmores.reside "
        "WHERE hmores.hmoide = ? ORDER BY hmores.pos", [pt["ide"]],
    )
    for f in lin:
        print(" ", json.dumps(f, ensure_ascii=False, default=str))
    print(f"Total lineas: {len(lin)}  ·  horas: "
          f"{sum(float(f['can'] or 0) for f in lin)}  ·  importe: "
          f"{round(sum(float(f['tot'] or 0) for f in lin), 2)}")
    for rec in RECURSOS_PRUEBA:
        n = sum(1 for f in lin if rec["nombre"].split(",")[0] in (f["recurso"] or ""))
        print(f"  {rec['nombre']}: {n} linea(s)")


def fase_limpiar(ejecutar: bool) -> None:
    """Borra SOLO las lineas de prueba (tex=MARCA); si el parte lo creamos
    nosotros (MARCA en la descripcion) y quedo vacio, borra la cabecera."""
    obra = obra_pruebas()
    pt = parte_mes(obra["ide"])
    if not pt:
        print("No existe el parte del mes: nada que limpiar.")
        return
    statements = [{
        "sql": f"DELETE FROM hmores WHERE hmoide = ? AND {cond_marca()}",
        "parameters": [pt["ide"], MARCA],
    }]
    if MARCA in (pt.get("res") or ""):
        statements.append({
            "sql": ("DELETE FROM hmo WHERE ide = ? AND NOT EXISTS "
                    "(SELECT 1 FROM hmores WHERE hmoide = ?)"),
            "parameters": [pt["ide"], pt["ide"]]})
        statements.append({
            "sql": ("DELETE FROM con WHERE ide = ? AND NOT EXISTS "
                    "(SELECT 1 FROM hmo WHERE ide = ?)"),
            "parameters": [pt["ide"], pt["ide"]]})
    else:
        print("  (la cabecera NO la creamos nosotros: no se toca)")
    sql_write(statements, ejecutar=ejecutar)


def main() -> int:
    fases = {
        "inspeccionar": lambda: fase_inspeccionar(),
        "estado": lambda: fase_estado(),
        "crear": lambda: fase_crear("--ejecutar" in sys.argv),
        "lineas": lambda: fase_lineas("--ejecutar" in sys.argv),
        "verificar": lambda: fase_verificar(),
        "limpiar": lambda: fase_limpiar("--ejecutar" in sys.argv),
    }
    fase = sys.argv[1] if len(sys.argv) > 1 else ""
    if fase not in fases:
        print(__doc__)
        return 1
    print(f"== {fase.upper()} == obra={OBRA_COD_PRUEBAS} "
          f"periodo={ANO}/{MES:02d} db={DB_WRITE}\n")
    fases[fase]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
