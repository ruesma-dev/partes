<!-- specs/F-033-columna-empresa/design.md -->
# F-033 · Portal: columna Empresa en las vistas de obra — Diseño

## 1. Encaje y límite de servicio

Solo **sv4** (`services/partes-front/`): es presentación. sv4 ya tiene
todo lo que hace falta:

- La empresa de cada ficha de obra: `ObraCatalog` (caché de 600 s sobre
  `SigridLookupClient.fetch_obras`, F-023) trae `ObraOption.empresa`
  (`con.emp`), una ficha por `ide`.
- La empresa de cada parte: `parte_documents.empresa` (F-023,
  semántica 12), nullable; NULL en los partes anteriores a F-023.

Lo único que falta es el **nombre corto** (Ruesma, Porsan), que no está en
Sigrid: `auxemp.res` es «CONSTRUCCIONES RUESMA» y «PORSAN E HIJOS
CONSTRUCCIONES SL» (`progress/explore_F-023_sigrid.md` §8.1). Vive en un
YAML versionado **de sv4** (DA1). No se copia lógica de sv3:
`config/empresas_membrete.yaml` de sv3 es una tabla de **alias para casar
membretes**, otro dato con otro fin; sv4 no la lee ni la replica. La lista
cerrada de duplicación de `CLAUDE.md` no crece.

No cambia lo que sv4 expone ni consume (el catálogo ya se lee):
`azure-apps/partes.md` no se toca. `EMPRESAS_PATH` tiene valor por
defecto: no hace falta configurarla en Azure.

## 2. Ficheros a crear

| Ruta | Contenido |
|---|---|
| `services/partes-front/config/empresas.yaml` | `1: Ruesma` y `28: Porsan`, con cabecera de ruta y comentario: «nombre corto por `numemp`; lo mantiene el humano» |
| `services/partes-front/application/services/empresas.py` | Tabla de nombres, texto y regla de la empresa de un grupo (§4) |
| `services/partes-front/tests/test_f033_nombres_empresa.py` | R1–R5 |
| `services/partes-front/tests/test_f033_vistas_empresa.py` | R6–R20 (repositorio + HTML con `TestClient`) |

## 3. Ficheros a modificar

| Ruta | Cambio |
|---|---|
| `config/settings.py` | `empresas_path: str = Field("config/empresas.yaml", alias="EMPRESAS_PATH")`, junto a `incidencias_path` y con el mismo estilo |
| `interface_adapters/web/app.py` | `construir_nombres_empresa(settings)` junto a `construir_tabla_incidencias` (mismo patrón: ruta relativa a `RAIZ_SERVICIO`, `ValueError` con ruta y motivo, log `[empresas][wiring]`); en `build_app`: se carga justo después de la tabla de incidencias, `app.state.nombres_empresa`, filtro Jinja `empresa`, y el resolutor `_empresa_de_ficha` pasado a `list_obras`, `get_obra`, `list_partes` y `get_parte` |
| `infrastructure/database/parte_repository.py` | Campos nuevos en los DTO y parámetro `empresa_de_ficha` en esos cuatro métodos (§5) |
| `templates/obras_list.html` | Columna, filtro y `data-label` (R6, R13) |
| `templates/obra_detail.html` | Línea «Empresa» en la cabecera y `data-label` del borrado (R15, R16) |
| `templates/partes_list.html` | Columna y filtro (R17) |
| `templates/parte_detail.html` | `info-item` «Empresa» tras «Obra» (R18) |
| `docs/ARCHITECTURE.md` | Una frase al final de la semántica 12 (R21) |

## 4. `application/services/empresas.py` (capa application, pura)

```python
@dataclass(frozen=True)
class NombresEmpresa:
    por_numero: dict[int, str]
    def nombre(self, numero: int) -> str          # o f"Empresa {numero}" (R4)
    def texto(self, numeros) -> str               # R5: int | None | Iterable[int]

def parsear_nombres_empresa(datos: object) -> NombresEmpresa   # ValueError (R2)

def empresas_de_grupo(obra_ide: int | None,
                      empresas_partes: Iterable[int | None],
                      empresa_de_ficha: Callable[[int], int | None] | None,
                      ) -> list[int]
```

- `parsear_nombres_empresa`: exige un mapa no vacío; clave convertible a
  `int` (YAML da `int`; un texto numérico también vale, `"abc"` no); valor
  `str` con `strip()` no vacío. Devuelve los nombres con `strip()`.
- `texto`: acepta `None` → «—», un `int` → `nombre`, una colección →
  quita `None` y repetidos, ordena y une con « / »; vacía → «—».
- `empresas_de_grupo` es **la regla del glosario, escrita una vez**: si
  `obra_ide` y `empresa_de_ficha` y esta devuelve un número → `[ese]`; si
  no, `sorted({e for e in empresas_partes if e is not None})`. La usan las
  cuatro consultas del repositorio (para un parte, el «grupo» es el propio
  documento: `empresas_partes = [doc.empresa]`).

El repositorio ya importa de `application/services/` (congelación,
incidencias): no se invierte ninguna dependencia nueva.

## 5. Repositorio (`infrastructure/database/parte_repository.py`)

DTO (campo nuevo al final, con valor por defecto para no romper a quien
los construye en tests):

- `ObraRow.empresas: list[int] = field(default_factory=list)`
- `ObraDetail.empresas: list[int] = field(default_factory=list)`
- `ParteRow.empresa: Optional[int] = None`
- `ParteDetail.empresa: Optional[int] = None`

Métodos (parámetro nuevo, opcional y solo por nombre; sin él la regla cae
a los partes, que es lo que ven los tests que no lo pasan):

- `list_obras(..., empresa_de_ficha=None)`: en el bucle de grupos se añade
  `g["empresas_doc"]` (set de `reg.document.empresa`; el documento ya
  viene con `selectinload`). Al construir cada `ObraRow`:
  `empresas=empresas_de_grupo(g["obra_ide"], g["empresas_doc"], empresa_de_ficha)`.
  Orden (R12): `(_norm(codigo) or "~", _norm(nombre), empresas[0] if empresas else 10**9)`.
- `get_obra(..., empresa_de_ficha=None)`: igual con
  `{r.document.empresa for r in regs}` dentro de la sesión; el campo se
  rellena en los **dos** `return ObraDetail(...)` (con y sin periodo).
- `list_partes(..., empresa_de_ficha=None)` y `get_parte(document_id, *,
  empresa_de_ficha=None)`: `empresa = (empresas_de_grupo(doc.obra_ide,
  [doc.empresa], empresa_de_ficha) or [None])[0]`.

Nada más cambia: `obra_key_for_registro`, agrupación, totales y `search`
quedan como están (R20).

## 6. `app.py` y plantillas

Resolutor (dentro de `build_app`, tras crear `obra_catalog`):

```python
def _empresa_de_ficha(ide: int) -> int | None:
    if not obra_catalog.enabled:
        return None
    opt = obra_catalog.get_by_ide(ide)
    return opt.empresa if opt is not None else None
```

`ObraCatalog._ensure_fresh` ya traga el fallo de Sigrid con WARNING y deja
la caché anterior (o vacía): R19 sale sin código nuevo. Una consulta por
fila es una búsqueda en diccionario; el refresco es uno cada 600 s.

Filtro Jinja: `templates.env.filters["empresa"] = nombres_empresa.texto`.

- `obras_list.html`: `<th>Empresa</th>` tras `<th>Obra</th>`; en la fila de
  filtros `<th><input class="col-filter" type="text" placeholder="Filtrar empresa…"></th>`;
  celda `<td>{{ o.empresas|empresa }}</td>`; `data-label` termina en
  `{% if o.empresas %} · {{ o.empresas|empresa }}{% endif %}`.
- `obra_detail.html`: bajo el `<h1>`,
  `<p class="obra-empresa">Empresa: <strong>{{ detail.empresas|empresa }}</strong></p>`
  (sin CSS nuevo: `<strong>` basta; si el reviewer lo pide, `.muted`); el
  `data-label` de «Borrar obra» como en el listado. `data-obra-label` del
  botón «+ Añadir línea» **no** cambia: el modal se abre desde la propia
  obra y viaja por `obra_ide`.
- `partes_list.html`: columna y filtro tras «Obra», celda
  `{{ p.empresa|empresa }}`.
- `parte_detail.html`: tras el `info-item` de «Obra»,
  `<div class="info-item"><span class="info-k">Empresa</span><span class="info-v">{{ parte.empresa|empresa }}</span></div>`.

Jinja autoescapa: los nombres del YAML no pueden inyectar HTML.

## 7. Tests (sin red ni PostgreSQL)

Patrón existente: `FabricaSesionSqlite` (`tests/dobles.py`) + repositorio
real; para el HTML, `build_app(Settings(_env_file=None), repository=...)` y
`TestClient`, con `SIGRID_API_*` de mentira y `SigridLookupClient`
sustituido por un falso con `fetch_obras` (como
`test_f004_endpoints_congelados.py`). Datos sintéticos: dos fichas con
código `0678` y el mismo nombre, ides 501 (empresa 1) y 502 (empresa 28).

| Test | R |
|---|---|
| `test_f033_r1_r3_fichero_versionado_ruesma_porsan` (carga el YAML real por `construir_nombres_empresa`) | R1, R3 |
| `test_f033_r2_*` parametrizado: ruta inexistente, YAML roto, mapa vacío, clave `abc`, nombre vacío → `ValueError` en `build_app` con la ruta | R2 |
| `test_f033_r4_numero_desconocido_empresa_n` | R4 |
| `test_f033_r5_texto_ninguna_una_varias` | R5 |
| `test_f033_r6_columna_y_filtro_alineados` (cuenta `<th>` de las dos filas de `thead`) | R6 |
| `test_f033_r7_gemelas_dos_filas_con_su_empresa` (HTML: dos filas `0678`, una «Ruesma», otra «Porsan») | R7 |
| `test_f033_r8_ficha_manda_sobre_parte_null_o_distinto` | R8 |
| `test_f033_r9_sin_ficha_sale_de_los_partes` (sin `obra_ide`, sin Sigrid, `ide` fuera del catálogo) | R9 |
| `test_f033_r10_sin_empresa_guion` | R10 |
| `test_f033_r11_varias_empresas_sin_ficha` | R11 |
| `test_f033_r12_orden_gemelas_estable` | R12 |
| `test_f033_r13_r16_data_label_con_empresa` (listado y detalle; sin empresa, igual que hoy) | R13, R16 |
| `test_f033_r14_filtro_generico_sin_cambios_js` (la columna lleva `col-filter` y `app.js` no cambia: `git diff` vacío lo comprueba el reviewer; el test verifica el marcado) | R14 |
| `test_f033_r15_cabecera_detalle_obra` | R15 |
| `test_f033_r17_columna_listado_partes` / `test_f033_r18_detalle_parte` | R17, R18 |
| `test_f033_r19_catalogo_caido_responde_200` (falso cuyo `fetch_obras` lanza) | R19 |
| `test_f033_r20_obra_key_y_totales_intactos` | R20 |

Además: parseo Jinja2 de las cuatro plantillas (convención de sv4). No hay
cambios en `app.js`, así que `node --check` no aplica.

## 8. Verificación manual (humano)

**M1** (tras el despliegue de sv4, que pide el humano, y Ctrl+F5; solo
lectura): en `/obras` filtrar «0678» → dos filas, «Ruesma» y «Porsan»;
abrir cada una → cabecera con su empresa; filtrar la columna Empresa por
«porsan» → solo obras de Porsan; en `/partes` la columna Empresa en los
partes de 0678.

## 9. Ficheros que NO se tocan

- `infrastructure/database/orm_models.py` (sv3 y sv4): sin schema nuevo.
- `services/partes-persistencia/` entero, incluido `config/empresas_membrete.yaml`.
- `services/partes-transfer/`, `partes-api`, `partes-email`.
- `static/app.js` y `static/styles.css`; `templates/trabajador_detail.html`,
  `conciliacion.html`, `papelera.html`, `nuevo_parte.html`.
- `application/services/obra_catalog.py` y `infrastructure/sigrid/sigrid_lookup_client.py`
  (ya dan `empresa`); `/api/sigrid/obras` y los combos.
- `update_parte_obra` / `patch_parte_obra` (DA7).
- `azure-apps/partes.md` e `infra/` (§1).

## 10. Decisiones abiertas (para el humano)

| DA | Recomendación | Alternativas descartadas |
|---|---|---|
| **DA1** Dónde vive número → nombre | YAML versionado de sv4 `config/empresas.yaml` (1 Ruesma, 28 Porsan; las dos únicas con actividad en 2026). Lo mantiene el humano | (a) `auxemp.res` vía sigrid-api: nombres largos («PORSAN E HIJOS CONSTRUCCIONES SL»), otra consulta y no es lo que se pidió. (b) Leer el YAML de alias de sv3: acopla servicios y sus alias son para casar texto («RUΞSMA»), no para mostrar |
| **DA2** Fuente de la empresa de una fila | Ficha de la obra primero (catálogo), partes después | Solo `parte_documents.empresa`: sin Sigrid, pero «—» en los grupos con partes anteriores a F-023 (NULL, nadie los re-casa, F-023 DA7) y dato viejo tras un cambio manual de obra (`update_parte_obra` no toca `empresa`) |
| **DA3** Vistas | Obras (listado, cabecera, borrado), más listado y detalle de parte: un parte de 0678 Ruesma y otro de Porsan del mismo día hoy son filas idénticas | Trabajador: recurso y obra comparten empresa en el 100 % de las líneas de 2026 (explore F-023 §2), no hay ambigüedad dentro de una persona. Conciliación: lista informativa. Papelera: restaurar no depende de la obra. Combos: ya llevan « · empresa N» (F-023); pasarlos a nombre exige tocar `/api/sigrid/obras` y `app.js` |
| **DA4** YAML ausente o mal formado | El portal no arranca (como `incidencias.yaml`): va en la imagen y R3 carga el real en cada `init.sh` | Arrancar con tabla vacía y «Empresa N» + WARNING: un error de edición pasaría en silencio |
| **DA5** Sin empresa / varias | «—» (como el resto de celdas vacías) / «Ruesma / Porsan» | Ocultar la celda; «Varias» (pierde cuáles) |
| **DA6** Rigor | Estándar: presentación, sin escritura ni datos compartidos | Documental (hay código) |
| **DA7** Partes antiguos y cambio manual de obra | Fuera: la ficha ya los cubre en pantalla (DA2). Si se quiere `parte_documents.empresa` correcto, feature aparte | Corregirlo aquí: toca escritura y `empresa_origen` |

## 11. Riesgos

- **Latencia**: `/obras` y `/partes` pueden disparar el refresco del
  catálogo (una lectura paginada a sigrid-api cada 600 s), como ya hacen
  los combos. Si Sigrid tarda, tarda esa carga; si falla, R19.
- **Empresa nueva con actividad** (p. ej. la 31): sale «Empresa 31» hasta
  que el humano la añada al YAML (R4).
- **Dos fuentes que discrepan** (ficha y parte): manda la ficha, que es la
  que identifica la obra de la fila; no se avisa (DA7).
