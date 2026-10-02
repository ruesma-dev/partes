<!-- specs/F-025-incidencia-vs-extra/design.md -->
# F-025 · Diseño técnico

Requisitos en `requirements.md`; datos de Sigrid en
`progress/explore_F-025_sigrid.md`. Rama `feature/F-025-incidencia-vs-extra`.
Rigor **estándar** (DA10).

## 1. Servicios que toca y por qué (límite de servicio)

- **sv4 (partes-front)**, y nada más. Las tres cosas que pide la feature viven
  ya aquí: las vistas del día del trabajador (en la matriz, ese día se pinta
  hoy «+1 M» sin más), la creación y edición manual, y la aprobación, que es
  la única puerta hacia Sigrid.
- **sv3, no** (DA7): marcar `review_required` al conciliar exigiría duplicar
  tabla y detección (ampliar la lista cerrada de CLAUDE.md); sv3 no ve las
  ediciones del portal, no bloquea nada y el conflicto puede cruzar partes.
- **sv5, no**: ve una obra por petición y no tiene BBDD. **sv2, no**.
- **Duplicación**: ninguna; `orm_models.py` no cambia. **azure-apps**: no
  cambia lo que se expone ni lo que se consume (el preflight es interno).

## 2. Encaje y flujo

```
config/incidencias.yaml ──(arranque, R1-R2)──▶ TablaIncidencias (app.state)
                                                     │ por parámetro
  get_obra / get_worker ─── líneas activas ──▶ detectar() ──▶ nivel por línea
  lineas_para_registro ── + las del mismo día ─┘        (vistas, R15-R18)
        └─▶ bloqueo: excluida «incompatible» (R9) · aviso: avisos_incidencia (R11)
```

La tabla se carga UNA vez en `build_app` y viaja **por parámetro** al
repositorio (como `holiday_name` en `get_obra`). Sin ella (`None`), todo
como antes (R23): los tests con `ParteReviewRepository(fabrica)` siguen
valiendo.

## 3. Ficheros a crear

| Ruta | Qué |
|---|---|
| `services/partes-front/config/incidencias.yaml` | La tabla versionada (R1). Cabecera explicando las clases y quién la mantiene, y siete entradas `LETRA: {sigrid, nombre, clase}` |
| `services/partes-front/application/services/incidencias_horas.py` | Lógica pura: parseo, clase de una línea y detección (§5.1) |
| `services/partes-front/tests/test_f025_tabla.py` | R1–R3 y el cableado del arranque |
| `services/partes-front/tests/test_f025_deteccion.py` | R4–R8 (función pura, sin BBDD) |
| `services/partes-front/tests/test_f025_aprobacion.py` | R9–R14 y R23 (SQLite + `TestClient` + sv5 falso) |
| `services/partes-front/tests/test_f025_vistas.py` | R15–R19, R20 y R23 en las vistas (HTML renderizado y JS con node) |

## 4. Ficheros a modificar

| Ruta | Cambio |
|---|---|
| `services/partes-front/config/settings.py` | `incidencias_path: str = Field("config/incidencias.yaml", alias="INCIDENCIAS_PATH")`, mismo patrón que `EMPRESAS_MEMBRETE_PATH` de sv3 |
| `services/partes-front/interface_adapters/web/app.py` | `construir_tabla_incidencias(settings)` al principio de `build_app`, en `app.state`. Se pasa a `get_obra`, `get_worker` y `lineas_para_registro`; `dias_incompatibles` en la ruta del trabajador; `avisos_incidencia` en `_evaluar_grupo`; `incompatible` en `_motivo_sin_lineas` |
| `services/partes-front/infrastructure/database/parte_repository.py` | `RegistroView` y `ObraMatrixCell` ganan `incompat_nivel` e `incompat_motivo`. Parámetro `incidencias` en los tres métodos. Exclusión y avisos en `lineas_para_registro` (§5.2) |
| `services/partes-front/application/services/reparto_obras.py` | `GrupoObra.avisos_incidencia: list[dict] = field(default_factory=list)`. No entra en `_payload_grupo` (R14) |
| `services/partes-front/templates/obra_detail.html` | Clase y `title` en la celda (R15) e insignia en «Líneas del periodo» (R17) |
| `services/partes-front/templates/trabajador_detail.html` | Clase, marca y `title` en el día del calendario (R16) e insignia en la tabla de líneas (R17) |
| `services/partes-front/static/app.js` | `incompatiblesHtml(n)` y `avisosIncidenciaHtml(avisos)`, funciones puras con `esc()`, cableadas en el modal (R19) |
| `services/partes-front/static/styles.css` | `.mx-incompat`, `.mx-incompat-aviso`, `.cal-incompat`, `.cal-incompat-aviso` y `.badge.incompat`. Bloqueo en rojo y aviso en ámbar, distinto del `mx-warn` de jornada incompleta |
| `docs/ARCHITECTURE.md` | Semántica 14 (R24) |
| `docs/referencia/partes-proyecto.md` | §4.1: H = Huelga (CIH). §3.4: el aviso y la exclusión del preflight (R24) |

## 5. Clases y funciones

### 5.1 `application/services/incidencias_horas.py` (application, pura)

```python
CLASE_DIA_COMPLETO, CLASE_PARCIAL = "dia_completo", "parcial"
NIVEL_BLOQUEO, NIVEL_AVISO = "bloqueo", "aviso"
LETRAS_LEYENDA = ("V", "B", "AT", "FJ", "F", "H", "M")

@dataclass(frozen=True)
class ClaseIncidencia:  letra: str; sigrid: str; nombre: str; clase: str
@dataclass(frozen=True)
class TablaIncidencias:
    por_letra: dict[str, ClaseIncidencia]; por_sigrid: dict[str, ClaseIncidencia]
    def clase_de(self, incidencia_codigo: str | None,
                 hora_codigo: str | None) -> ClaseIncidencia | None   # R3
@dataclass(frozen=True)
class LineaDia:
    registro_id: int; persona: str; fecha_int: int; es_incidencia: bool
    incidencia_codigo: str | None; hora_codigo: str | None
    es_extra: bool; horas: float | None
@dataclass(frozen=True)
class Incompatibilidad:  nivel: str; motivo: str

def parsear_tabla(datos: object) -> TablaIncidencias          # ValueError (R2)
def detectar(lineas: Iterable[LineaDia],
             tabla: TablaIncidencias) -> dict[int, Incompatibilidad]  # R4-R8
def resumen_por_dia(
        items: Iterable[tuple[str, Incompatibilidad]]) -> dict[str, Incompatibilidad]
```

- `detectar` agrupa por `(persona, fecha_int)`; las líneas sin fecha no
  entran. Por grupo: `completas` = clases `dia_completo` de sus
  incidencias, `parciales` = las `parcial`, `horas` = líneas no incidencia
  con `abs(horas) > 1e-9`, `extra_pos` = las extra con `horas > 1e-9`. Si hay
  completas y horas, todas las líneas del grupo quedan en `bloqueo`. Si no,
  pero hay parciales y extra positiva, en `aviso`. En los demás casos, nada.
- Motivos (texto fijo, con el nombre de la tabla). Bloqueo: «{nombre}
  ({letra}) es de día completo y ese día hay {h} h de trabajo: deja solo una
  de las dos». Aviso: «{nombre} ({letra}) y {h} h extra el mismo día:
  comprueba que sean correctas». Con varias incidencias se nombran todas, en
  orden de letra.
- `resumen_por_dia`: peor nivel del día (gana `bloqueo`), para el calendario.
- `es_extra` = criterio de `_is_extra` (`tipo_hora == 'extra'` o
  `hora_ext == 1`); en Sigrid `ext` es 0 hasta en los `HE%` (exploración §1).

### 5.2 Repositorio (`parte_repository.py`, infrastructure)

- `persona_de(reg) -> str`: `"dni:" + DNI normalizado` o, sin DNI,
  `worker_key_for_registro(reg)` (DA11). `_linea_dia(reg) -> LineaDia`.
- `get_obra(..., incidencias=None)` y `get_worker(worker_key,
  incidencias=None)`: ya cargan **todas** las líneas activas antes de
  filtrar, así que se llama a `detectar` sobre esa lista completa, que cruza
  obras (R18), sin consultas nuevas. `_registro_view` recibe la
  incompatibilidad de la línea. En `get_obra` el `slot` de la celda guarda
  también los ids de sus incidencias, y la celda toma el peor nivel de sus
  líneas y el motivo de ese nivel.
- `lineas_para_registro(ids, *, incluir_borradas=False, incidencias=None)`:
  1. Igual que hoy hasta tener `regs`.
  2. Con `incidencias`, una consulta más: las líneas activas (sin borrar y
     de documento activo) con `fecha_int` en las fechas de `regs`, en lotes
     de `LOTE_IDS_CONSULTA`. Sobre ellas, `detectar`.
  3. En el bucle, **después** de las exclusiones de F-024 (R13): si la línea
     está en `bloqueo`, va a `excluidas["incompatible"]` y a
     `_excluida_detalle(r, "incompatible", motivo)`, y `continue`. Si está en
     `aviso`, es extra y `horas > 0`, se añade a
     `grupo["avisos_incidencia"]`.
  4. `excluidas["incompatible"]` **solo existe si es > 0**: no cambia las
     respuestas que los tests de F-022/F-024 comparan por igualdad.
- `_excluida_detalle` acepta un `motivo` opcional para el estado nuevo.

### 5.3 `app.py` (interface_adapters)

- `construir_tabla_incidencias(settings)`: `yaml.safe_load` + `parsear_tabla`.
  Un fallo tumba el arranque (R2), como la tabla del membrete de sv3. PyYAML
  llega con `uvicorn[standard]` (sin dependencia nueva). Log con las clases.
- Vista de trabajador: `dias_incompatibles = resumen_por_dia(...)` a partir de
  `detail.registros` del periodo, junto a `dias_incompletos`.
- `_evaluar_grupo`: `evaluado["avisos_incidencia"] = grupo.avisos_incidencia`.
- `_motivo_sin_lineas`: añade «N con una incidencia de día completo y horas
  el mismo día (corrige el día en el portal)».

### 5.4 Navegador (`app.js`)

`incompatiblesHtml(n)`: un bloque `ap-ctx ap-incompat`, fuera del
desplegable, con el texto «N línea(s) no se registran: tienen una incidencia
de día completo y horas el mismo día. Están en «Excluidas»; corrige el día y
vuelve a aprobar». `avisosIncidenciaHtml(avisos)` sigue el patrón de
`avisosCalendarioHtml`, pero escapando con `esc()` (F-027 trata las
heredadas). Se cablean en el modal y en `grupoHtml`.

## 6. SQL

Ninguno en Sigrid. En PostgreSQL, ni DDL ni columnas: solo la lectura de
§5.2.2 con el ORM. M1 (§9) es de solo lectura y la lanza el humano.

## 7. Ficheros que NO se tocan y fuera de alcance

- `congelacion.py`, `jornada_resolver.py`, `_rol_incidencia` (R22, DA8);
  `orm_models.py` (sv3 y sv4) y `ddl_complementario()`.
- sv2, sv3 (`recurso_conciliador.py`, `persist_parte_pipeline.py`) y sv5
  (`reglas_registro.py`) (R21).
- `crear_parte_manual`, `crear_extra_desde`, `update_registro`,
  `set_registro_hora` (R20, DA4); `parte_detail.html` y listado (DA5).
- Fuera de alcance: horas dentro de una racha y jornada con permiso (DA9).

## 8. Decisiones abiertas (recomendación en negrita)

1. **DA1 · Fuente de la clasificación.** Sigrid no la tiene (`auxhor` sin
   campo de clase, `tipincnom` = 0; `auxincfic` y `e_aus` vacías). **Tabla
   versionada propia, `config/incidencias.yaml` de sv4, que falla al arrancar
   si está mal.** Descartada una constante en código (CONVENTIONS).
2. **DA2 · Valores iniciales.** **Día completo: V, B, M y F. Parcial: AT (el
   único caso de Sigrid con horas: 2 h y el accidente), FJ (permisos por
   horas, médico) y H (paros parciales de huelga).** Lo que habría que
   confirmar con Administración: F (¿un retraso se apunta como F?) y H.
3. **DA3 · Qué se hace al detectarlo.** **En `bloqueo`, las líneas de ese
   día-trabajador salen de la aprobación como «Excluidas» con su motivo,
   sin excepción posible, y el resto de la petición sigue. En `aviso`, se
   muestra en el modal y no se bloquea.** Descartadas: (a) solo avisar, porque
   no limita y Juan pidió limitarlo; (b) bloquear la obra o el mes entero,
   porque castiga a toda la cuadrilla por un día; (c) excluir solo las horas,
   porque daría por buena la incidencia sin saberlo, y si la errónea era la
   incidencia mandaría a Sigrid una M falsa; (d) una casilla para forzar,
   porque contradice «no puede tener».
4. **DA4 · Edición y creación.** **No se bloquea nada al crear ni editar**:
   arreglar un día exige pasos intermedios (poner la incidencia, luego borrar
   las horas). Alternativa barata: 422 en «+ Nuevo» si el día ya tiene lo
   contrario.
5. **DA5 · Dónde se ve.** **Vista de obra (matriz y líneas) y vista de
   trabajador (calendario y líneas)**, que es desde donde se aprueba.
   `parte_detail` y el listado de partes quedan fuera: necesitarían otra
   consulta por fecha y no son puerta de aprobación.
6. **DA6 · Lo ya aprobado o registrado.** **Nada se reescribe ni se
   desaprueba; lo antiguo se ve marcado.** Si una línea ya está en Sigrid, la
   otra queda excluida; si la errónea es la registrada, se borra en Sigrid,
   F-024 la marca `borrado_sigrid` y se borra en el portal. M1 lo cuantifica.
7. **DA7 · Servicio.** **Solo sv4** (§1); sv3 + sv4 exigiría duplicar.
8. **DA8 · Rol de racha y extras por jornada sin cambios.** **No se tocan.**
   Riesgo aceptado: mientras haya un conflicto, aprobar días vecinos calcula
   el rol (inicio/fin) contando ese día como trabajado. Contar el día como
   incidencia sería decidir quién tiene razón.
9. **DA9 · Fuera de alcance (candidatas a feature).** **Horas dentro de una
   racha** («V……V» con trabajo en medio; en Sigrid 3–4 de 403 rachas de V, 4–6
   de 32 de permisos): los intermedios no tienen línea, no es «mismo día». Y
   **la jornada con permiso parcial** (2 h de permiso + 6 h ⇒ extra −2 h).
10. **DA10 · Rigor.** **Estándar**, como F-022: la feature solo quita líneas
    de lo que se envía, sin escritura nueva, sin schema y sin tocar sistemas
    compartidos.
11. **DA11 · Quién es la persona.** **El DNI normalizado; si no lo hay, la
    clave de trabajador del portal (`emp-<ide>` o `nom-<NOMBRE>`).**
    `_rol_incidencia` mira el DNI o `empleado_ide`. El respaldo por nombre
    sirve para no perder el conflicto dentro de un parte sin casar.
12. **DA12 · Despliegue.** **Solo sv4, sin variable de activación**;
    marcha atrás = revisión anterior.

## 9. Verificaciones manuales (humano)

- **M1 · antes de desplegar** (PostgreSQL `partes`, solo lectura, con
  firewall). Cuántos días-trabajador están ya en conflicto, por letra y
  estado:
  `SELECT i.incidencia_codigo, h.sigrid_estado, COUNT(DISTINCT
  (COALESCE(i.empleado_dni, i.empleado_ide::text), i.fecha_int)) FROM
  parte_registros i JOIN parte_registros h ON h.fecha_int = i.fecha_int AND
  COALESCE(h.empleado_dni, h.empleado_ide::text) = COALESCE(i.empleado_dni,
  i.empleado_ide::text) AND NOT h.es_incidencia AND ABS(COALESCE(h.horas,0))
  > 0 AND h.deleted_at_utc IS NULL WHERE i.es_incidencia AND
  i.deleted_at_utc IS NULL GROUP BY 1, 2 ORDER BY 1, 2;`
  Esperado: una cifra pequeña. Si sale grande, revisar DA2 antes de desplegar.
- **M2 · tras desplegar sv4** (navegador, modo pruebas, obra `0404`): con
  «+ Nuevo», un día M y otro con horas; al día M, una extra desde la celda.
  Esperado: celda roja con `title` e insignia en las líneas; al aprobar, el
  bloque «N línea(s) no se registran» y el motivo en «Excluidas»; el resto
  llega a Sigrid y las del día M no cambian.
- **M3**: FJ + 2 h extra ⇒ ámbar, aviso en el modal, se registra.
- **M4**: incidencia en la obra A y extra en la B el mismo día ⇒ las dos
  celdas marcadas y el día en rojo en la vista del trabajador.
- **M5 · Administración**: confirmar DA2 (F y H) y que el texto de los
  motivos se entiende.

## 10. Riesgos

- La lectura extra de `lineas_para_registro` trae las líneas de las fechas
  pedidas (miles en un mes, en lotes); `get_obra` ya carga más.
- Un `incidencias.yaml` mal editado tumba el arranque (a propósito, R2).
- DA8: roles de racha calculados con un día en conflicto si se aprueban días
  vecinos antes de arreglarlo.
