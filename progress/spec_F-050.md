<!-- progress/spec_F-050.md -->
# F-050 · Informe del spec-author

## Revisión del 2026-10-20 (segunda): DA10 aprobada y empresa visible

Decisión del humano del 2026-10-20, literal: «en la vista por persona, se juntan las obras.
lo que es importante es que en 2 empresas son 2 personas con vistas diferenciadas».

### Qué cambió en la spec (`specs/F-050-misma-fila-para-el-mismo-trabajador/`)

- **DA10 → APROBADA, opción (a)**: en «Por persona» (`list_workers`) una fila por clave =
  (empresa, persona) con todas sus obras. R9 reescrito; descartada (b).
- **Empresa en alcance (DA11, nueva, ABIERTA)**: requisitos nuevos **R23–R26** (columna
  «Empresa» con filtro en «Por persona», empresa en la cabecera de `/trabajadores/{clave}`,
  «—» cuando no se sabe, desempate de homónimos por empresa, sin Sigrid ni consultas
  nuevas). R10 ampliado: `/trabajadores/rec-R1` no trae líneas de R2 (E10).
- **Confirmado en el código**: con la clave `rec-` cada vista `/trabajadores/{clave}` solo
  tiene líneas de una empresa, porque agrupa por un recurso persona y un recurso de Sigrid
  es de una sola empresa (`rescon.emp`); sv3 (F-023) y el selector del portal (F-035) eligen
  el recurso entre los de la empresa de la obra. La única vía de mezcla es la persona fijada
  desde la vista del trabajador (DA6), que se vería como «A / B» en la columna y que sv5
  rechaza al aprobar (verifica empresa del recurso).
- Quitados R-d de riesgos (sustituido por el de «empresa no deducible») y la línea «Mostrar
  la empresa…» de «Fuera de alcance» (sustituida por «respaldo por obra»).
- Design: §1 nuevo punto «Empresa», §2 añade `templates/trabajadores_list.html` (sale de
  «no se tocan») y la cabecera de `trabajador_detail.html`, §3 `_empresa_por_recurso` y los
  campos `empresas`/`empresa_texto` de `WorkerRow`/`WorkerDetail`, §5 `test_f050_empresa.py`,
  §6 M6, §7 límite de servicio, §8 DA1 anotada, DA10 aprobada, DA11.
- Tasks: nueva **T8** (empresa); las siguientes pasan a T9–T13; T10 ya no exige que
  `trabajadores_list.html` quede intacto; T12 añade M6. El arranque exige el visto bueno a
  DA1, DA1b y DA11.
- **DA1 y DA1b siguen ABIERTAS**. En DA1 se anota que la regla de hoy («2 empresas son 2
  personas») es justo lo que garantiza la opción A.
- Topes: requirements 150/150, design 250/250 (`python -m harness.tamano --feature F-050`).

### Fuente de empresa elegida (DA11)

**La regla de F-033 sobre la base `partes`**, ya usada por «Por obra»
(`application/services/empresas.py`: `empresas_de_fila`, `texto_empresas`, sin cambios):

1. Empresas no nulas de los partes (`parte_documents.empresa`, F-023) de las líneas de la
   clave.
2. Si ninguno la tiene, la del recurso de la clave deducida de otros partes con empresa
   donde aparece (`empresa_por_recurso`, hoy un bucle dentro de `list_obras` que se extrae
   a `_empresa_por_recurso` sin cambiar su resultado; lo vigila
   `tests/test_f033_columna_empresa.py`).
3. Si tampoco: «—» en la lista y nada en la cabecera. Casos: persona solo en partes
   manuales (nacen sin `empresa`) o anteriores a F-023 cuyo recurso no aparece en ningún
   parte con empresa; `emp-` sin recurso en esos partes.
4. `nom-` y `sin-trabajador`: se pinta la empresa de sus partes (no de una persona); dos
   empresas («Ruesma / Porsan») avisan de homónimos o líneas por casar.

Por qué: fiable (la empresa del parte la fija sv3 y el recurso se elige en la empresa de la
obra), barata (`list_workers` y `get_worker` ya cargan líneas y partes: cero consultas
nuevas), sin Sigrid, solo sv4 y ya probada en producción en «Por obra».

Descartadas: catálogo de recursos de Sigrid (`RecursoCatalog` / `_SQL_RECURSOS_ACTIVOS`, que
sí trae `rescon.emp`, pero solo recursos de alta hoy, carga toda la tabla con TTL y queda
vacío si sigrid-api falla); Sigrid por fila; guardar la empresa en la línea (esquema,
migración y sv3); `recurso_cif` (es el DNI, no el CIF de la empresa); respaldo por la obra
(cambiaría `empresas_de_fila` de F-033; queda como posible feature si M6 da muchas «—»);
«—» fijo en `nom-`/`sin-trabajador`.

**Límite de servicio**: no se toca sv3 ni Sigrid, no hay duplicación nueva ni crece la
lista cerrada del `CLAUDE.md` (la regla de F-033 vive solo en sv4).

### Decisiones abiertas para el humano

- **DA1** (clave `rec-` primero), **DA1b** (dos recursos del mismo DNI en una empresa) y
  **DA11** (fuente de la empresa). M1 recomendada antes de implementar.

### Pendiente para el líder

- `harness/features.json` no se ha tocado (lo pedido): su `description` aún dice «abiertas
  DA1, DA1b y DA10» y los `acceptance` no recogen la empresa visible. Conviene alinearlo
  cuando el humano valide DA11 (lo regenera `BACKLOG.md`).
