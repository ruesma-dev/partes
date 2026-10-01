<!-- specs/F-021-cuenta-analitica-sigrid/design.md -->
# F-021 · Diseño técnico

Datos: `progress/explore_F-021_sigrid.md` (§N). Requisitos: `requirements.md`.

## 1. La regla, con datos

| | Campo | Evidencia |
|---|---|---|
| **Origen** | `reshor.caaide` del par (recurso, tipo de hora escrito); si no, el del tipo por defecto `res.horide`. Se toma su **subcuenta** | `res.caaide` = 0 en todos (§2). Coincide con lo tecleado en el 99,64 % de la empresa 1 (§3) |
| **Destino** | `hmores.caaide` = la cuenta `caa` del **centro de la obra** con esa subcuenta y la empresa de la obra | La línea manual lleva siempre la cuenta de su centro; nunca el `ide` de la plantilla (§3) |
| **Sin cuenta** | `caaide = 0`, la línea se escribe | Es lo que hace el humano: empresa 28 entera (§2) y 279 líneas de la 1 cuya obra no tiene esa subcuenta (§3) |

Ejemplo: plantilla `00000.CIMO09` en la obra `0404` → cuenta `0404.CIMO09`
del centro de la `0404`. La partida, el empleado y `auxhor.caacod` no mandan
(§5: en 2.188 de 2.191 discrepancias con la partida gana el recurso).

## 2. Servicios que toca y por qué (límite de servicio)

| Servicio | Por qué | Qué no hace |
|---|---|---|
| sv5 | Único que escribe en Sigrid y el que ya lee `reshor` en `preparar` (`horas_de_recursos`) y verifica el recurso (`coherencia_recurso`). La cuenta depende del tipo de hora que **decide sv5** (`ReglasRegistro`) y de la obra **destino** (que en modo pruebas solo conoce sv5) | No toca la base `partes` |
| sv4 | Solo pinta en el modal del preflight el aviso que sv5 ya calcula (R19–R21) | No resuelve ni guarda cuentas |

**sv3 no se toca**: resolver la cuenta en la ingesta exigiría columnas nuevas
en las dos copias de `orm_models.py`, se quedaría rancia si Administración
cambia la ficha del recurso entre la ingesta y la aprobación, y no conocería
el tipo de hora final ni la obra de pruebas. Ninguna lógica se duplica: la
regla vive solo en sv5 y la lista cerrada de `CLAUDE.md` no crece.

## 3. Encaje en la arquitectura

La regla es una **función pura** en `application/services/` (tablas de casos,
mutación barata). Los adaptadores solo aportan campos. En `preparar`, que es
la fase de **datos maestros** fuera del lock (`reshor`, `res`, `caa` no los
escribe nunca sv5), tras las reglas:

`acciones` → subcuenta por acción `escribir` (R1–R2) → **una** lectura de
cuentas del centro (R10) → `CuentaLinea` por acción (R3–R6) → campos `caa_*`
de la acción (R13) → log por motivo (R18). `registrar` solo copia `caa_ide`
al `INSERT` (R14). `preflight` y `ejecutar` comparten `preparar` (R12).

## 4. Ficheros a crear

| Ruta | Contenido |
|---|---|
| `services/partes-transfer/application/services/cuenta_analitica.py` | Regla pura (§6.1) |
| `services/partes-transfer/tests/test_f021_cuenta_analitica.py` | R1–R8 por tablas |
| `services/partes-transfer/tests/test_f021_cliente_cuenta.py` | R9–R11, R14 con `httpx.post` sustituido (patrón de `test_f023_escritura_empresa.py`) |
| `services/partes-transfer/tests/test_f021_pipeline_cuenta.py` | R10–R13, R15–R18 con los dobles |
| `services/partes-front/tests/test_f021_preflight_cuenta.py` | R19–R21 |

## 5. Ficheros a modificar

**sv5** (`services/partes-transfer/`)
- `domain/models/registro_models.py`: `HoraRecurso` + `caa_cod: Optional[str]
  = None`, `defecto: bool = False`; `AccionLinea` + `caa_ide: int = 0`,
  `caa_cod`, `caa_motivo`, `caa_aviso: Optional[str] = None`. Con valores por
  defecto: los constructores existentes siguen valiendo.
- `infrastructure/sigrid/sigrid_write_client.py`: SQL de `horas_de_recursos`
  (§7), método nuevo `cuentas_de_centro` (§7), `stmt_insert_linea` con
  `caaide: int` **obligatorio** (sin valor por defecto, DA9) y `caaide` como
  `?` en el `INSERT`; docstring de cabecera (`caaide=0` deja de ser cierto).
- `application/pipelines/registro_pipeline.py`: `_resolver_cuentas(destino,
  empresa, acciones, horas)` llamado al final de `preparar`; en
  `_registrar_bajo_lock`, `caaide=int(a.caa_ide)` y `caa_cod` en `escritas`;
  docstring de pasos (paso 4b).
- `tests/dobles.py`: el cliente falso gana `cuentas_de_centro` (con registro
  de llamadas y fallo inyectable) y su `stmt_insert_linea` recibe y guarda
  `caaide`; `HoraRecurso` falsos con `caa_cod`/`defecto` donde haga falta.
- Tests existentes que llaman a `stmt_insert_linea` o comparan el SQL de
  `horas_de_recursos`: se **inventarían en T1** y se adaptan, nunca se borran.
- `prueba_escritura_sigrid.py`: **solo comentarios** (líneas 26 y 411 dicen
  que las líneas reales llevan `caaide` 0, y es falso: §3). Su comportamiento
  no cambia (DA11).

**sv4** (`services/partes-front/`)
- `static/app.js`: `avisosCuentaHtml(acciones)` (filtra `accion ===
  "escribir"` con `caa_aviso`; devuelve `""` si no hay) y su llamada al final
  de `resumenHtml(pf)`. Mismo estilo que `avisosCalendarioHtml` (`ap-ctx`).
  Ningún cambio en Python: `aprobar_preflight` ya reenvía la respuesta de sv5.

**Docs**: `docs/ARCHITECTURE.md` (punto 13 de semántica de dominio, ≤ 8
líneas), `docs/referencia/partes-proyecto.md` §3.5 (paso nuevo) y
`azure-apps/partes.md` §3.5 (commit local allí, sin push).

## 6. Clases y funciones

### 6.1 sv5 · `application/services/cuenta_analitica.py` (pura)

```python
MOTIVO_RECURSO_SIN_CUENTA = "recurso_sin_cuenta"   # R3 (sin aviso)
MOTIVO_OBRA_SIN_CUENTA = "obra_sin_cuenta"         # R5 (con aviso)
MOTIVO_CUENTA_AMBIGUA = "cuenta_ambigua"           # R6 (con aviso)

def subcuenta(cod: str | None) -> str | None
    # texto tras el PRIMER '.', strip(); None si vacío, sin punto o vacío tras él
def subcuenta_de_linea(horas: list[HoraRecurso], horide: int | None) -> str | None
    # R1: fila con horide == horide y subcuenta(caa_cod); si no, R2: fila defecto
@dataclass(frozen=True)
class CuentaLinea:
    caa_ide: int            # 0 si no hay
    caa_cod: str | None
    motivo: str | None      # None = ok
    aviso: str | None       # solo R5 y R6
def resolver_cuenta(sub: str | None, cuentas: dict[str, list[tuple[int, str]]],
                    obra_cod: str | None) -> CuentaLinea          # R3–R6
def indexar_cuentas(filas: list[tuple[int, str]]) -> dict[str, list[tuple[int, str]]]
    # agrupa (caaide, cod) por subcuenta(cod); descarta las que no tienen
```

Avisos (texto para el portal, sin datos personales):
`"la obra {obra_cod} no tiene la cuenta analitica .{sub}: la linea ira sin
cuenta"` y `"la obra {obra_cod} tiene varias cuentas .{sub}: la linea ira sin
cuenta"`.

### 6.2 sv5 · `RegistroPipeline._resolver_cuentas`

1. `subs = {id(a): subcuenta_de_linea(horas[a.recurso_ide], a.hora_ide)}`
   para cada acción `escribir` (las demás quedan `caa_ide = 0`, sin motivo).
2. `cenide = int(getattr(destino, "cenide", 0) or 0)`. Si hay alguna
   subcuenta y `cenide`: `cli.cuentas_de_centro(cenide, empresa, subs)` —
   **sin `try`**: un fallo sube y la petición no escribe (R11). Sin `cenide`,
   índice vacío ⇒ R5.
3. `resolver_cuenta(...)` por acción y copia a `caa_ide`, `caa_cod`,
   `caa_motivo`, `caa_aviso`.
4. `logger.info("[registro] cuentas obra=%s ok=%s recurso_sin_cuenta=%s
   obra_sin_cuenta=%s cuenta_ambigua=%s", …)` (R18).

## 7. SQL (solo lecturas de Sigrid nuevas; ningún SQL de PostgreSQL)

`horas_de_recursos` (misma llamada, mismo lote; R9):

```sql
SELECT reshor.reside AS reside, reshor.horide AS horide, auxhor.cod AS cod,
       auxhor.res AS res, reshor.pre AS pre, cc.cod AS caacod,
       CASE WHEN reshor.horide = res.horide THEN 1 ELSE 0 END AS defecto
FROM reshor JOIN auxhor ON auxhor.ide = reshor.horide
LEFT JOIN res ON res.ide = reshor.reside
LEFT JOIN con cc ON cc.ide = reshor.caaide AND ISNULL(reshor.caaide, 0) <> 0
WHERE reshor.reside IN (?, …) ORDER BY reshor.reside, auxhor.cod
```

`cuentas_de_centro(cenide, empresa, subcuentas) -> dict[str, list[tuple[int,
str]]]` (nueva; R10; lote acotado por las subcuentas, ≤ 27 hoy, §2):

```sql
SELECT a.ide AS caaide, c.cod AS cod FROM caa a JOIN con c ON c.ide = a.ide
WHERE a.cenide = ? AND c.emp = ?
  AND LTRIM(RTRIM(SUBSTRING(c.cod, CHARINDEX('.', c.cod) + 1, 24))) IN (?, …)
```

El filtro SQL solo acota; la agrupación la rehace `indexar_cuentas` en Python
con la misma `subcuenta()`, así que un código raro nunca entra por SQL y se
cuela en la regla. `_read` ya lanza con `truncated` (R11).

`INSERT INTO hmores`: la lista de columnas no cambia; el valor de `caaide`
pasa del literal `0` a `?`, con `int(caaide)` en su posición de parámetros
(R14). `fac` y `ortide` siguen a 0.

## 8. Decisiones abiertas (el humano aprueba o rebate)

| # | Propuesta (recomendación) | Por qué / alternativa |
|---|---|---|
| DA1 | **Origen = `reshor.caaide`** del recurso para el tipo de hora escrito; respaldo con su tipo por defecto (`res.horide`) | Es la «cuenta analítica del recurso» de su ficha: `res.caaide` está a 0 en todos (§2). Con el respaldo, 99,64 % igual que lo tecleado (§3). Sin respaldo, las incidencias `CI*` (1.132 líneas) irían sin cuenta |
| DA2 | **Destino = la cuenta del centro de la obra con la subcuenta del recurso**, no el `ide` de la plantilla | Las plantillas son del centro `00000`; la línea manual lleva siempre la de su centro (§3) |
| DA3 | **Sin cuenta: escribir `caaide = 0`** (como hoy) y **avisar** en el portal solo si se puede arreglar en la obra (R5, R6). **No bloquear** | Bloquear pararía todas las líneas de Porsan (0 % con cuenta, también a mano) y las 279 de obras sin la subcuenta. La hora es lo que paga; la cuenta se completa después. Alternativas: omitir la línea (pierde horas), avisar también R3 (ruido en cada parte de Porsan) |
| DA4 | **Portal**: bloque informativo en el modal del preflight (solo JS de sv4). No se lista la cuenta de cada línea | El modal no lista las líneas a escribir, solo recuentos y excepciones. Alternativa: no tocar sv4 (el aviso solo en el log de sv5) |
| DA5 | La **partida no interviene** | En 2.188 de 2.191 discrepancias manda el recurso (§5) |
| DA6 | **Sin reescritura**: lo ya registrado no se toca (synckey igual, R16) | Hoy hay **0** líneas de sv5 en Sigrid (§4). Si M1 encuentra alguna escrita antes de desplegar F-021, la completa Administración a mano o se abre una feature de relleno (escritura fuera del flujo normal) |
| DA7 | **Fallo al leer cuentas ⇒ la petición entera falla** y la cola reintenta | Escribir 0 en silencio es justo el defecto que se corrige. Es la regla de `datos_recursos` (F-023, R36) |
| DA8 | **Sin variable de activación** | Marcha atrás = revisión anterior de `ca-sv5-transfer`. Alternativa: `SIGRID_CUENTA_ANALITICA` (una variable más en Azure y un camino más que probar) |
| DA9 | `caaide` **obligatorio** en `stmt_insert_linea` (sin valor por defecto) | Un defecto `0` escondería otra llamada que lo olvide |
| DA10 | **`cuaide`** (cuenta financiera) sigue sin escribirse; las cuentas de baja (`con.fecbaj`) no se filtran | 0 líneas manuales llevan `cuaide`. 1 cuenta de baja de 184.234 y ninguna usada (§1) |
| DA11 | Corregir **solo los comentarios** de `prueba_escritura_sigrid.py` | Afirman que las líneas reales llevan `caaide` 0 (falso). Su escritura de pruebas queda igual. Alternativa: no tocarlo |
| DA12 | Una feature; **despliegue sv5 → sv4** | sv4 nuevo con sv5 viejo no pinta nada (R20); sv5 nuevo con sv4 viejo escribe la cuenta sin aviso. Cualquier orden es seguro |
| DA13 | **Porsan (28)**: nada que configurar en código. Si Administración quiere cuenta en sus horas, se rellena `reshor` en Sigrid y sv5 la arrastra sola | Hoy ninguna fila `reshor` de la 28 tiene cuenta (§2) |

## 9. Verificaciones manuales (humano)

- **M1 · antes de desplegar sv5 (lectura, sigrid-api, `ruesma`).** Líneas
  de sv5 sin cuenta ya en Sigrid: `SELECT h.ano, h.mes, COUNT(*) AS n,
  SUM(CASE WHEN ISNULL(h.caaide,0)=0 THEN 1 ELSE 0 END) AS sin_cuenta FROM
  hmores h WHERE h.synckey LIKE 'partes:%' GROUP BY h.ano, h.mes`. Esperado
  hoy: 0 filas. Si hay, decidir según DA6.
- **M2 · tras sv5 (modo pruebas, obra `0404`).** Aprobar un parte con
  ordinarias, extras y una incidencia de un recurso de la empresa 1 y leer:
  `SELECT h.synckey, ah.cod AS hora, c.cod AS cuenta, ca.cenide, o.cenide
  AS cen_obra FROM hmores h JOIN obr o ON o.ide = h.obride LEFT JOIN auxhor
  ah ON ah.ide = h.horide LEFT JOIN con c ON c.ide = h.caaide LEFT JOIN caa
  ca ON ca.ide = h.caaide WHERE h.synckey IN (…)`. Esperado: `cuenta` =
  `<código del centro de 0404>.<subcuenta del recurso>`, `ca.cenide =
  cen_obra`; las `CI*`/`CIZ` con la subcuenta del tipo por defecto. Limpiar
  con `prueba_escritura_sigrid.py`.
- **M3 · tras sv4.** Preflight de un recurso cuya subcuenta **no** tiene la
  `0404` (la única de las 25, §6): `SELECT DISTINCT LTRIM(RTRIM(SUBSTRING(
  c.cod, CHARINDEX('.',c.cod)+1, 24))) FROM reshor rh JOIN con c ON c.ide =
  rh.caaide JOIN con rc ON rc.ide = rh.reside WHERE rh.caaide <> 0 AND
  rc.emp = 1` menos las del centro de la `0404`. Esperado: el bloque de aviso
  en el modal (Ctrl+F5) y la línea escrita con `caaide = 0`.
- **M4 · Administración.** En la pantalla de Sigrid, la línea de M2 muestra
  la cuenta igual que una tecleada; y confirma DA3 y DA13 (Porsan sin cuenta).

## 10. Ficheros que NO se tocan y fuera de alcance

sv1, sv2, **sv3** entero, `orm_models.py` (las dos copias), `coherencia_recurso.py`,
`reglas_registro.py` (las reglas de qué se escribe no cambian),
`resultado_json.py` (`escritas` ya se serializa tal cual), `infra/`,
`CLAUDE.md`. **Fuera de alcance**: rellenar la cuenta de líneas ya
registradas (DA6), la cuenta financiera `cuaide` y la de la cabecera
`hmo.caaide` (0 en las 6.889 cabeceras), mostrar la cuenta en otras
pantallas de sv4 o en `parte_registros`.

## 11. Riesgos

- Si la ficha del recurso (`reshor`) está mal mantenida, sv5 arrastra la
  cuenta mal: es el mismo dato del que parte el humano, y M4 lo contrasta.
- 53 líneas de 2026 con el tipo por defecto llevan a mano otra cuenta (§3):
  sv5 pondrá la de la ficha. Es lo pedido («arrastrar la del recurso»).
- Una lectura más por petición (pequeña, por lote de subcuentas): si
  sigrid-api cae, falla la petición entera (DA7), igual que hoy con
  `datos_recursos`.
