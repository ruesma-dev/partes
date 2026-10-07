<!-- specs/F-037-extras-duplicadas-base-omitida/design.md -->
# F-037 · sv3: no duplicar la extra automática de una base omitida — Diseño

## 1. Encaje y límite de servicio

- **Solo sv3.** El recálculo de extras (revertir → leer → calcular splits →
  aplicar) vive entero en sv3: `RecursoConciliador.conciliar_todos`
  (`application/services/recurso_conciliador.py`) y el repositorio
  (`infrastructure/database/sqlalchemy_parte_repository.py`). Lo llaman
  `persist_parte_pipeline.py` (cada mensaje) y la ruta manual de
  `interface_adapters/api/app.py`; ninguno cambia.
- **La regla compartida no cambia** (DA1). `esta_congelado` /
  `ESTADOS_CONGELADOS` (sv3) y `congelacion.py` (sv4) responden «¿se puede
  tocar ESTA línea?» y siguen dando lo mismo por estado (guardián F-024). La
  pareja refina **el recálculo**, que solo hace sv3: sv4 no reparte extras
  ni toca `horas_orig`/`extra_auto`, y sv5 escribe por `registro_id`. No
  crece la lista cerrada de `CLAUDE.md`.
- Una base `omitido` sigue editable en el portal (semántica 10: editarla es
  el camino de arreglo). Lo nuevo es que sv3 ya no la recalcula mientras su
  extra viva en Sigrid.
- **Convivencia con F-036** (también sv3): no toca `recurso_conciliador.py`,
  el repositorio ni `esta_congelado` (su R20 caracteriza que no cambian;
  F-037 tampoco). Solapes de merge triviales: `tests/dobles.py` (F-036 añade
  `recurso_persona` arriba; F-037 amplía `sembrar_lineas`) y las altas en
  `features.json` / `BACKLOG.md` / `progress/current.md`. Los tests de
  F-037 no construyen `RecursoRow` ni `IndicePersonas` (índice fijo, §6):
  inmunes al filtro `cla = 1` de F-036.

## 2. Ficheros

Bajo `services/partes-persistencia/` salvo indicación.

| Acción | Ruta | Cambio |
|---|---|---|
| Crear | `application/services/pareja_extra.py` | núcleo puro (§3) |
| Modificar | `infrastructure/database/sqlalchemy_parte_repository.py` | `revert_extras_auto` sobre `plan_revert`; `fetch_registros_para_recurso` lee 3 columnas más y añade `congelada_por_pareja` (§4) |
| Modificar | `application/services/recurso_conciliador.py` | solo `_congelado(reg)` (§5) y docstring de `conciliar_todos` |
| Modificar | `tests/dobles.py` | `sembrar_lineas` admite por línea `line_index`, `empleado_line_no`, `recurso_ide` (por defecto, lo de hoy) |
| Crear | `tests/test_f037_pareja.py` | R1–R3 |
| Crear | `tests/test_f037_revert.py` | R4–R9 (repositorio, SQLite) |
| Crear | `tests/test_f037_dos_pasadas.py` | R10–R16 (conciliador + repositorio real) |
| Modificar | `docs/ARCHITECTURE.md` (raíz), semántica 3 | R20 |
| Modificar | `docs/referencia/partes-proyecto.md`, los dos párrafos de «Cómputo de extras» | R20 |

**No se tocan**: `esta_congelado`, `ESTADOS_CONGELADOS`,
`_reclasificar_extras_jornada` (solo hereda `_congelado`),
`apply_extras_splits`, `apply_recurso_matches`, `orm_models.py` (sin
schema), `jornada_resolver.py`, `seleccion_sigrid.py`,
`persist_parte_pipeline.py`, sv4 (incluido `congelacion.py`), sv5, sv1,
sv2, `CLAUDE.md`, `azure-apps/partes.md`, los tests existentes.

## 3. Núcleo puro (`application/services/pareja_extra.py`, application)

```python
Clave = tuple[str | None, int | None, int | None, int | None]

def clave_pareja(fila: Mapping[str, Any]) -> Clave
    # (document_id, line_index, empleado_line_no, fecha_int)
def es_miembro(*, extra_auto: bool, tipo_hora: str | None) -> bool
    # extra_auto, o (tipo_hora or "").strip().lower() in ("", "normal")

@dataclass(frozen=True)
class FilaPareja:
    registro_id: int
    clave: Clave
    extra_auto: bool
    miembro: bool
    congelada: bool          # esta_congelado(...) de la propia fila

def claves_congeladas(filas: Iterable[FilaPareja]) -> set[Clave]   # R3

@dataclass(frozen=True)
class PlanRevert:
    borrar: tuple[int, ...]       # extra_auto a borrar (incluye duplicadas)
    restaurar: tuple[int, ...]    # bases: horas = horas_orig
    duplicadas: tuple[int, ...]   # subconjunto de borrar (R6)
    congeladas: int               # congeladas por sí mismas (log de hoy)
    protegidas: int               # respetadas por pareja (R8)
    dobles: tuple[Clave, ...]     # parejas con > 1 extra congelada (R7)

def plan_revert(filas: Iterable[FilaPareja]) -> PlanRevert
```

`plan_revert`, por fila en orden de `registro_id` (plan determinista):

1. `congelada` → nada; `congeladas += 1`.
2. `miembro` y clave en `claves_congeladas`: si `extra_auto` y la pareja
   tiene alguna extra congelada → `borrar` + `duplicadas` (R6); si no →
   nada, `protegidas += 1` (R4, R5).
3. Resto, como hoy: `extra_auto` → `borrar`; si no → `restaurar`.

`dobles` = claves con más de una `extra_auto` congelada (R7). El núcleo no
importa infraestructura: recibe `congelada` ya calculada con
`esta_congelado`, así la regla por línea sigue escrita una sola vez.

## 4. Repositorio (`sqlalchemy_parte_repository.py`, infrastructure)

`revert_extras_auto()`: misma consulta de hoy (`extra_auto OR horas_orig IS
NOT NULL`, con `ParteDocumentOrm.approved`). Un `FilaPareja` por fila,
`plan_revert`, y aplica en un solo `commit`: `session.delete` de `borrar`;
`horas = horas_orig; horas_orig = None` de `restaurar`. Logs:

- el INFO de hoy, idéntico (`"[repo] revert de extras: %s linea(s)
  CONGELADAS respetadas …"` con `plan.congeladas`; lo vigila F-015 R31);
- INFO si `protegidas`: `"[repo] revert de extras: %s linea(s) protegidas
  por su pareja congelada (F-037)."`;
- WARNING si `duplicadas` (R6): número y los 10 primeros ids;
- WARNING por clave de `dobles` (R7): `document_id`, `line_index`, número
  de extras congeladas y «revisar a mano en Sigrid».

Devuelve `len(plan.borrar)` (R8). La consulta solo ve bases con
`horas_orig` (las únicas que la reversión toca): una base congelada sin
`horas_orig` no protege desde aquí (§9, R-b).

`fetch_registros_para_recurso()`: añade `line_index`, `empleado_line_no` y
`extra_auto` al `select`, calcula `claves_congeladas` sobre todas las filas
leídas y añade a cada dict `"congelada_por_pareja": miembro and clave in
claves and not congelada`. Ninguna otra clave nueva en el dict.

## 5. Conciliador (`recurso_conciliador.py`, application)

```python
def _congelado(reg: dict) -> bool:
    return (esta_congelado(reg.get("sigrid_estado"), reg.get("doc_approved"))
            or bool(reg.get("congelada_por_pareja")))
```

`_congelado` ya es el único punto de `_fijar_congelada` (F-023 R30: no
re-resuelve recurso; su `recurso_ide` cuenta en el día) y de
`_reclasificar_extras_jornada` (F-015 R32: suma, no es candidata ni
pivote): R10 sin tocar el cálculo. Un dict sin la clave (los dobles de hoy)
se comporta igual.

Por qué basta: R11, tras la reversión la base sigue en 8 h y la extra
congelada en 2; el día suma 10, jornada 8, objetivo de extra 2, ya está:
`delta = 0`. R12, no laborable con base en 0 h: `total_ord = 0`, sin split.
R15, base y extra suman una vez y el exceso de la línea libre se recorta
solo de ella. Hoy, en cambio, la base vuelve a 10 y el día suma 12.

## 6. Tests

Sintéticos (DNI de prueba `12345678Z`, obra 10, recurso 501), SQLite en
memoria (`FabricaSesionSqlite`), sin red. Nombres `test_f037_rN_…`.

- `test_f037_pareja.py` (R1–R3): `clave_pareja` con `None`; extra
  explícita no miembro; pareja congelada por base o por extra; claves
  vecinas (otro `line_index`, fecha o documento) independientes;
  `plan_revert` caso a caso (incluidos `dobles` y el orden).
- `test_f037_revert.py` (R4–R9), con `sembrar_lineas` ampliado: base
  `omitido` 8/10 + extra `registrado` → nada cambia, `revert == 0`; más un
  duplicado sin estado → borrado solo él, `revert == 1`, WARNING con su id;
  base `registrado` 8/10 + extra sin estado o `error` → intactas; dos
  extras congeladas → ninguna borrada, WARNING R7; INFO de protegidas y el
  INFO «CONGELADAS» con la cifra de siempre; `fetch` marca bien base,
  extras, extra explícita y línea de otra clave.
- `test_f037_dos_pasadas.py` (R10–R16): `RecursoConciliador(repository=
  SqlAlchemyParteRepository(fabrica), lookup=LookupFake(reshor=
  reshor_par(501)), calendario=CalendarioFake(...), indice_provider=lambda:
  IndiceFijo())`. `IndiceFijo`, doble local: `recursos = []`,
  `empresa_de_obra() -> None`, `elegir_recurso(...) -> ResolucionRecurso(
  ide=501, motivo="ok")`. Dos `conciliar_todos()` y se comparan las filas
  de la pareja (`id`, `horas`, `horas_orig`, `extra_auto`,
  `sigrid_estado`): R11 (laborable 10→8 + 2), R12 (sábado no laborable,
  4→0 + 4), R13 (R11 y R12 con duplicado sin estado), R14 (base
  `registrado` + extra sin estado / `error`), R15 (pareja congelada + línea
  libre de 3 h el mismo día: un split de 3 h solo sobre la libre), R16
  (nada congelado: una extra tras cada pasada, mismas horas). Semillas con
  `recurso_ide = 501` (la extra hereda el recurso de su base).
- **Fase RED** (rigor crítico): R1–R15 fallan contra el código de hoy (en
  R11–R13 y R15 aparece una `extra_auto` nueva; en R14 desaparece la
  extra); traza en `progress/impl_F-037.md`. R16–R18 son de
  **caracterización**: verdes antes y después.

## 7. Documentación (R20)

`docs/ARCHITECTURE.md`, semántica 3, tras «Lo ya congelado … no se
recalcula»: «F-037: la base y sus extras automáticas (mismos
`document_id`, `line_index`, `empleado_line_no`, `fecha_int`) se congelan
juntas para el recálculo de sv3: si una está congelada, ninguna se revierte
ni se vuelve a partir, y las extras automáticas no congeladas de una pareja
cuya extra ya está congelada son duplicados y se borran. La regla por línea
(semántica 10) no cambia.» Una frase equivalente en los dos párrafos de
«Cómputo de extras» de `docs/referencia/partes-proyecto.md`.

## 8. Despliegue y verificación MANUAL (humano)

Solo sv3 (`infra/redeploy_partes.ps1 -Solo sv3`), cuando lo pida el humano.
Consultas de **solo lectura** sobre la base `partes`; las lanza el humano:

```sql
SELECT r.document_id, r.line_index, r.empleado_line_no, r.fecha_int, COUNT(*)
FROM parte_registros r JOIN parte_documents d ON d.id = r.document_id
WHERE d.is_active AND r.extra_auto
  -- M1: descomentar la línea siguiente
  -- AND r.sigrid_estado IN ('encolado', 'registrado', 'dedicacion')
GROUP BY 1, 2, 3, 4 HAVING COUNT(*) > 1;
```

- **M1 · antes de desplegar** (línea descomentada): 0 filas. Si sale
  alguna, un duplicado ya viajó; arreglo manual en Sigrid antes de nada (R7
  no lo toca).
- **M2 · tras desplegar y una pasada de sv3** (tal cual; R21): 0 filas
  (hoy, 7). Agrupar por `(document_id, empleado, fecha)` sirve de contraste
  pero puede listar casos legítimos: un recorte que no cabe en una línea
  reparte la extra entre varias bases del mismo día (una por base).
- **M3 · logs** de `ca-sv3-persistencia`: el WARNING de duplicados borrados
  sale en la primera pasada (7) y no vuelve; ningún WARNING R7.
- **M4 · caso inverso ya dañado** (informativo, DA3): bases congeladas
  (`d.approved` o estado congelante), no `extra_auto`, con `horas_orig`, sin
  ninguna `extra_auto` de su clave (`NOT EXISTS` con `IS NOT DISTINCT FROM`
  en `empleado_line_no` y `fecha_int`). Se espera 0.

## 9. Riesgos y alternativas

- **R-a · Borrado físico de los duplicados.** Es lo que la reversión ya hace
  con toda `extra_auto` no congelada en cada pasada; F-037 solo deja de
  recrearla. Una extra no congelada en una pareja con la extra congelada no
  puede ser legítima: el cálculo genera una por base y pasada, y la
  congelada ya es esa. M1 descarta antes que alguna esté en vuelo.
- **R-b · Corte a mitad de pasada heredado** (base restaurada sin
  `horas_orig` + extra congelada): `fetch` la marca congelada por pareja
  (mira todas las filas) y no se re-parte; el día sumaría de más sin
  duplicar nada en Sigrid. No visto en producción (las 7 bases tienen
  `horas_orig`); M2/M4 lo harían visible.
- **R-c · Edición en sv4 de una base protegida**: se guarda y sv3 ya no la
  pisa con `horas_orig` (hoy sí). Cambiar su trabajador no re-resuelve el
  recurso mientras su extra viva en Sigrid, como una línea congelada.
- **Descartada · ampliar `esta_congelado`** con la pareja: cambiaría la
  regla gemela (sv4 bloquearía editar una `omitido`, el camino de arreglo),
  obligaría a tocar sv4 y el guardián F-024, y chocaría con la R20 de F-036.
- **Descartada · arreglar solo el cálculo**: la base seguiría volviendo a
  10 h, el cálculo tendría que descontar la extra congelada de su pareja
  (más lógica en el sitio más delicado) y el caso inverso seguiría perdiendo
  la extra en la reversión.
- **Descartada · script de limpieza aparte**: la siguiente pasada de sv3 ya
  limpia; un SQL contra producción duplicaría la regla.

## 10. Decisiones abiertas (humano)

- **DA1 · Solo sv3, sin tocar la regla compartida** de congelación ni la
  lista cerrada de `CLAUDE.md`. *Recomendado* (§1, §9).
- **DA2 · Limpieza automática** de los duplicados en la primera pasada tras
  desplegar, con WARNING de ids y M1–M3, en vez de un script. *Recomendado*.
- **DA3 · Daño previo del caso inverso** (M4 > 0): F-037 solo lo cuenta; si
  hay alguno, se repone en una feature aparte con el dato en la mano.
  *Recomendado*.
