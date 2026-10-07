<!-- specs/F-033-columna-empresa/design.md -->
# F-033 · Portal: columna Empresa en el listado de obras — Diseño

## 1. Encaje

Solo sv4, solo presentación. `list_obras` ya carga todas las líneas
activas con su documento (`selectinload(ParteRegistroOrm.document)`), así
que la empresa sale de esos mismos objetos: ni consulta nueva, ni Sigrid,
ni schema. La BBDD `partes` no guarda la empresa del recurso en ninguna
columna propia (`parte_registros` solo tiene `recurso_ide`); el respaldo
de R4 la deduce de los partes con empresa donde aparece ese recurso. No se
copia lógica de sv3; la lista cerrada de duplicación no crece.

## 2. Ficheros

| Acción | Ruta (bajo `services/partes-front/`) | Cambio |
|---|---|---|
| Crear | `application/services/empresas.py` | `NOMBRES_EMPRESA`, `nombre_empresa`, `texto_empresas`, `empresas_de_fila` (§3) |
| Modificar | `infrastructure/database/parte_repository.py` | `ObraRow.empresas` y `ObraRow.empresa_texto`; cálculo y orden en `list_obras` (§3) |
| Modificar | `templates/obras_list.html` | Columna, filtro y celda (§3) |
| Crear | `tests/test_f033_columna_empresa.py` | R1–R8 |

**No se tocan**: `app.py`, `settings.py`, `orm_models.py`, `get_obra`,
`list_partes`, `get_parte`, las demás plantillas, `static/`, sv3, sv5,
`obra_catalog.py`, `azure-apps/`.

## 3. Detalle

`application/services/empresas.py` (puro, sin dependencias):

```python
NOMBRES_EMPRESA: dict[int, str] = {1: "Ruesma", 28: "Porsan"}

def nombre_empresa(numero: int) -> str        # o f"Empresa {numero}"
def texto_empresas(numeros: list[int]) -> str  # [] -> "—"; si no, " / ".join(nombres)
def empresas_de_fila(empresas_partes: set[int | None],
                     recursos: set[int | None],
                     empresa_por_recurso: dict[int, set[int]]) -> list[int]
```

`empresas_de_fila`: si `empresas_partes` sin `None` no está vacío,
devuelve ese conjunto ordenado; si no, la unión ordenada de
`empresa_por_recurso[r]` para los `r` no nulos de `recursos`.

`list_obras` (sin cambiar la consulta):

1. Antes del bucle de grupos, `empresa_por_recurso`: para cada `reg` con
   `recurso_ide` y `reg.document.empresa` no nulos, añadir la empresa al
   conjunto de ese recurso.
2. En cada grupo, `g["empresas_doc"]` (set de `reg.document.empresa`) y
   `g["recursos"]` (set de `reg.recurso_ide`).
3. `ObraRow(..., empresas=e, empresa_texto=texto_empresas(e))` con
   `e = empresas_de_fila(...)`. Campos nuevos al final del dataclass, con
   defecto (`field(default_factory=list)` y `"—"`).
4. Orden: `(_norm(codigo) or "~", _norm(nombre), e[0] if e else 10**9)`.

`obras_list.html`: `<th>Empresa</th>` tras `<th>Obra</th>`; en la fila de
filtros `<th><input class="col-filter" type="text" placeholder="Filtrar empresa…"></th>`
en la misma posición; celda `<td>{{ o.empresa_texto }}</td>`. El filtro es
el genérico (`wireColumnFilters`, por índice de columna): sin cambios en JS.

## 4. Tests (sin red ni PostgreSQL)

`FabricaSesionSqlite` (`tests/dobles.py`) + `ParteReviewRepository` real y,
para el HTML, `build_app(Settings(_env_file=None), repository=...)` con
`TestClient` (patrón de `test_f025_vistas.py`). Datos sintéticos: dos obras
`0678` con el mismo nombre, `obra_ide` 501 y 502, partes con empresa 1 y 28.

| Test | R |
|---|---|
| `test_f033_r1_columna_y_filtro_alineados` | R1 |
| `test_f033_r2_varias_empresas_unidas` | R2 |
| `test_f033_r3_gemelas_dos_filas_ruesma_porsan` (HTML) | R3 |
| `test_f033_r4_partes_null_usa_empresa_del_recurso` | R4 |
| `test_f033_r5_sin_empresa_guion` | R5 |
| `test_f033_r6_numero_desconocido_empresa_n` | R6 |
| `test_f033_r7_orden_gemelas` | R7 |
| `test_f033_r8_obra_key_y_totales_intactos` | R8 |

Fase RED con traza para R2–R7. Parseo Jinja2 de `obras_list.html`.

## 5. Riesgos y decisiones

- Respaldo por recurso (R4): un recurso de Sigrid es de una sola empresa
  (recurso y obra comparten empresa en el 100 % de las líneas de 2026,
  `progress/explore_F-023_sigrid.md` §2). Si ese recurso nunca aparece en
  un parte con empresa, sale «—».
- Una empresa nueva con actividad sale «Empresa N» hasta que se añada al
  dict (cambio de una línea).
- Descartado (por decisión del humano): catálogo de Sigrid, YAML de
  nombres, resto de vistas.
- Sin decisiones abiertas.
