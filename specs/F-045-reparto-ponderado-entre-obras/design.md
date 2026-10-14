<!-- specs/F-045-reparto-ponderado-entre-obras/design.md -->
# F-045 · Reparto ponderado de la jornada entre obras — Diseño

## 1. Encaje, límite de servicio y rigor

- **Solo sv3.** El reparto ordinaria/extra ya es exclusivo de sv3
  (`conciliar_todos`, semántica 3); F-045 cambia **cómo** reparte, no quién ni
  cuándo. Ni sv4 ni sv5 calculan reparto: no hay lógica que duplicar.
- **Lista cerrada de `CLAUDE.md`: no crece.** `esta_congelado` /
  `ESTADOS_CONGELADOS` (gemela de `congelacion.py`, vigilada por
  `tests/test_f024_borrado_no_congela_gemelos.py`) y `jornada_resolver.py`
  (gemelo de sv4) **no** se tocan: se usan tal cual.
- **Sin esquema**: `orm_models.py` intacto (las dos copias). Despliegue: solo
  sv3. **Rigor crítico**: worker de producción y horas de nómina/coste.

## 2. Cómo reparte hoy (investigación, 2026-10-14)

`conciliar_todos`: `revert_extras_auto` (borra las `extra_auto` no congeladas y
restaura `horas = horas_orig`; F-037 respeta la pareja) → `fetch_registros_para_recurso`
→ casado de recurso → `_reclasificar_extras_jornada(registros, ride_por_reg,
reshor_idx)` → `apply_extras_splits`. En `_reclasificar_extras_jornada`, por
grupo (recurso, `fecha_int`) de todas las obras:

1. Recurso sin `reshor` o sin código extra (mensual MENC): nada (aviso).
2. No laborable: `delta` = todas las ordinarias. Laborable: sin ordinarias,
   nada; si no, `J` = `_detalle_jornada(...)` (F-015) y `delta` = (ord + ext − J) − ext.
3. «La primera» no existe como tal: manda el **`registro_id` mayor** (la línea
   insertada más tarde). `delta > 0`: recorte de mayor a menor id hasta cubrir;
   `delta < 0`: sube **solo** la ordinaria de id mayor y crea UNA `extra_auto`
   negativa (pivote). Por eso el Ejemplo 1 da A 8 + 2 y B 0 + 4.
4. Congeladas: suman en el total, nunca son recorte ni pivote; si no alcanza
   lo ajustable (`disponible < delta`, o `delta < 0` sin pivote), ningún split
   y WARNING. Con la 0678 congelada en 8 + (−4), la 0704 de 8 h da 0 + 8.
5. Las líneas en la papelera no se filtran (DA9).

## 3. Algoritmo nuevo

Por grupo (mismos casos 1–2 de §2; `J = 0` si no laborable):

```
fijas      = congeladas ∪ {ordinarias con horas <= 0}
             ∪ {ordinarias de obras con peso <= 0}; papelera: fuera del grupo
J'         = J - Σ horas(ordinarias fijas)
obras_aj   = obras con >= 1 ordinaria ajustable
peso(obra) = Σ horas(ordinarias y extras explícitas NO fijas de esa obra)
si J' < 0, o (J' != 0 y no hay obras_aj): WARNING de hoy, sin splits  (R23)
cuota_obra = repartir(J', [(obra, peso, min registro_id)], paso)
por obra:  cuota_lin = repartir(cuota_obra, [(id, horas, id)], paso')
           línea con cuota != horas  ->  split(horas_norm=cuota,
                                                extra_horas=horas-cuota)
```

`repartir` = mayor resto en **enteros de paso** (`round(x / paso)`, sin floats
acumulados). Sin fijas, `J' = J`: es el reparto ideal (R7). R4 se cumple por
construcción: con pesos y total múltiplos del paso, el suelo de una cuota
nunca baja de su peso cuando `total ≥ Σpesos`, y los `k` de mayor resto tienen
resto > 0, así que su techo nunca supera el peso cuando `total ≤ Σpesos`.

**Medición para F-046 (R25)**: si el grupo tiene congeladas, se calcula además
el **ideal** tratando todas sus líneas (salvo incidencias y papelera) como
ajustables, con peso de línea = `horas_orig` si no es nulo (base de una pareja
congelada: lo trabajado) y extra ideal de la pareja = trabajado − cuota. Si
difiere de lo congelado ⇒ WARNING y contador; **no** se aplica.

## 4. Ficheros

**Crear** `services/partes-persistencia/application/services/reparto_ponderado.py`
(application, puro; sin imports de `infrastructure/`):

- `PASOS: tuple[float, ...] = (0.5, 0.25, 0.01)`.
- `elegir_paso(total: float, pesos: Iterable[float]) -> float` (R3).
- `@dataclass(frozen=True) Participante(clave: Hashable, peso: float, llegada: int)`.
- `repartir(total: float, participantes: Sequence[Participante], paso: float)
  -> dict[Hashable, float]` (R1, R2, R4, R5).
- `@dataclass(frozen=True) LineaDia(registro_id, obra_ide, tipo: str, horas:
  float, horas_orig: float | None, fija: bool)` — `tipo` `'ordinaria'` o `'extra'`.
- `@dataclass(frozen=True) Ajuste(registro_id, horas_norm, extra_horas,
  horas_orig)`; `@dataclass(frozen=True) ResultadoDia(cuadra: bool, paso:
  float, ajustes: tuple[Ajuste, ...], n_obras: int, n_lineas: int)`.
- `repartir_dia(lineas: Sequence[LineaDia], jornada: float) -> ResultadoDia`
  (R7–R19, R22, R23): §3 sin medición.
- `diferencias_ideal(lineas, jornada) -> tuple[tuple[int, float, float], ...]`
  (R25): `(registro_id, antes, después)` de las congeladas que cambiarían.

**Modificar** `services/partes-persistencia/application/services/recurso_conciliador.py`:

- `_reclasificar_extras_jornada`: conserva el cribado (sin recurso, sin
  `reshor`, sin código extra con su aviso, no laborable, laborable sin
  ordinarias, `J` con `_detalle_jornada`, `_avisar_candef_fuera_del_mapa`,
  `_marca_jornada`) y sustituye el bloque de `orden`/`delta`/recorte/pivote por
  `repartir_dia`; convierte cada `Ajuste` al dict de split de hoy (R28) con
  `hora_ext` y `candef_real`. Mantiene el WARNING literal de R23 y los INFO de
  recorte/jornada incompleta pasan a uno de reparto (R30).
- Grupos: excluye las líneas con `deleted_at_utc` (R27); `fija` = `_congelado(r)`
  o ordinaria con horas ≤ 0.
- `conciliar_todos`: cuenta `repartos_con_congeladas` (R25) y lo añade al dict
  y al log final; se vacía al empezar, como `_docs_degradados`.
- El docstring de `_reclasificar_extras_jornada` se reescribe (sin «mayor id»).

**Modificar** `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py`:
`fetch_registros_para_recurso` añade al dict `horas_orig`, `extra_auto` (ya
leído) y `deleted_at_utc` (columna nueva en el `select`). Sin otro cambio:
`revert_extras_auto` y `apply_extras_splits` intactos.

**Modificar `tests/dobles.py`** (sv3): `registro(...)` acepta `horas_orig`,
`extra_auto`, `deleted_at_utc` y `congelada_por_pareja` con defecto neutro.

**Documentación**: `docs/ARCHITECTURE.md` semántica 3, `docs/referencia/partes-proyecto.md`
«Cómputo de extras», `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` §3.3
(una frase; commit local allí, sin push).

**NO se tocan**: `orm_models.py` (sv3 y sv4); `pareja_extra.py`;
`esta_congelado`/`ESTADOS_CONGELADOS`; `jornada_resolver.py` (sv3 y sv4);
`revert_extras_auto`, `apply_extras_splits`; `despacho.py`, `main_worker.py`,
`recalculo_seguimiento.py` (F-042/F-043); todo `services/partes-front`,
`services/partes-transfer`, `services/partes-api`, `services/partes-email`, `infra/`.

## 5. Tests

Nuevos (sv3, sin red ni BBDD, datos sintéticos): `tests/test_f045_reparto_puro.py`
(R1–R6, con propiedades sobre una rejilla fija de pesos y totales: suma exacta,
múltiplo del paso, R4, permutación de la entrada), `tests/test_f045_reparto_dia.py`
(R7–R23, R26, R27, R29 sobre `repartir_dia` y `_reclasificar_extras_jornada`),
`tests/test_f045_conciliar.py` (R24, R25, R28, R30 con `RepositorioFake`, `caplog`
y el dict de `conciliar_todos`). Raíz: R31 por `git diff` en tasks.

**Tests existentes que cambian de cifras** (los únicos permitidos; fijan el
recorte por id mayor o el pivote único con ≥ 2 ordinarias ajustables en el
grupo). Se reescribe solo el valor esperado, por el de §3, con la tabla
antes → después en `progress/impl_F-045.md`:
`test_f003_r15_splits_dorados.py` (`…recorta_desde_el_registro_de_mayor_id`,
`…desborda_al_siguiente_registro`, `…agrupa_por_recurso_y_dia_across_obras`),
`test_f015_r20_computo_ultimo_laborable.py` (las tres homónimas),
`test_f015_r32_congelados_cuentan_no_se_tocan.py` y
`test_f037_dos_pasadas.py::test_f037_r10_no_es_pivote_de_una_jornada_incompleta`
solo si sus grupos tienen ≥ 2 ajustables. **Cualquier otro test existente que
falle ⇒ `blocked`** y se consulta (no se toca).

## 6. Decisiones (DA, con recomendación)

- **DA1 · Partir en dos features.** F-045 = reparto ponderado en sv3 (sin
  Sigrid, sin esquema, sin portal). **F-046** = reajuste de lo congelado en
  Sigrid al aprobar, con aviso (§8). Motivo: F-046 estrena una escritura nueva
  en Sigrid (editar `hmores` ya escritas), una tabla y portal; F-045 es su
  prerrequisito (el algoritmo) y se despliega y mide solo. **Ojo**: el caso real
  (0678 ya registrada) **no** se arregla hasta F-046 (R24); F-045 arregla los
  días en que ningún parte está aprobado aún. *Recomendado.*
- **DA2 · Dos niveles: obra y línea.** Peso de obra = sus horas ordinarias +
  extras explícitas («las horas de cada parte»); dentro, las ordinarias por sus
  horas. Alternativas: por línea directa (las extras explícitas no tienen línea
  base a la que atribuirlas); por documento (Sigrid agrupa por obra, no por
  parte). *Recomendado.*
- **DA3 · Ámbito: todo grupo, también dentro de una obra.** Una regla única;
  las extras se reparten entre partidas en vez de caer en la última línea.
  Alternativa: solo entre obras y dentro de la obra el recorte por id mayor de
  hoy (dos reglas). *Recomendado.*
- **DA4 · Desempate**: mayor resto → mayor peso → el que llegó antes (menor
  `registro_id`). *Recomendado.*
- **DA5 · Paso 0,5 con respaldo 0,25 y 0,01.** Con horas o `J` que no son
  múltiplo de 0,5 (7,75; excepción de jornada), forzar 0,5 rompería la suma o
  daría extras de signo cruzado. Alternativa: 0,5 siempre y que la extra herede
  la fracción. *Recomendado.*
- **DA6 · Extras negativas: se mantienen** (pregunta abierta del humano).
  `T < J` sigue completando la jornada y la extra negativa se reparte en
  proporción (R14) en vez de caer entera en la última línea. Alternativa
  (b): sin extras negativas, ordinarias = trabajado (1 requisito más en el
  núcleo; cambia la nómina del viernes corto que F-015 resolvió). *Recomendado
  mantener.*
- **DA7 · Congeladas en fase 1: modo residual** (R22–R25). Base de datos
  siempre cuadrada; nada se registra suponiendo un reajuste que aún no ha
  ocurrido. El WARNING de R25 mide cuántos días tocaría F-046. *Recomendado.*
- **DA8 · Incidencias**: sin cambios (no participan ni restan jornada); día
  completo con horas ya lo bloquea F-025 al aprobar. *Recomendado.*
- **DA9 · Papelera fuera del reparto** (hallazgo): hoy una línea borrada del
  portal pesa en el día y su `extra_auto` nace activa. Filtro en memoria solo
  para el reparto (el casado de recurso no cambia). *Recomendado incluirlo.*
- **DA10 · Concurrencia**: no se arregla aquí (R-b de F-042). *Recomendado*;
  F-046 sí lo exige (DA14).

## 7. Riesgos

- **R-a · Redistribución al desplegar.** La primera pasada reparte de nuevo
  todo grupo no congelado con ≥ 2 ordinarias: cambian cifras de partes aún no
  aprobados que alguien pudo mirar. Se mide antes (M1).
- **R-b · Pasadas concurrentes** (preexistente): con más splits por grupo, una
  doble pasada puede duplicar `extra_auto` hasta la siguiente; igual que hoy.
- **R-c · Partes de otras obras cambian sin aviso**: una ingesta mueve las
  extras de partes ya revisados de otra obra (hoy también, pero solo en el
  último). Sin espera de F-043 (solo cambio de fecha). Si molesta, feature aparte.
- **R-d · Reingestas / duplicados**: un parte duplicado pesa doble, como hoy.
- **R-e · Deshacer**: sin cambios; el snapshot no incluye `extra_auto` y la
  siguiente pasada recalcula (F-042 DA1).
- **R-f · Descartado**: repartir en sv4 al aprobar (duplicaría el cómputo).

## 8. Fase 2 · F-046 propuesta (para validar la dirección; spec aparte)

**Qué permite hoy sv5** (código, 2026-10-14): idempotencia por `synckey`
(`partes:<registro_id>`): si existe, `ya_registrado`, **nunca** actualiza;
sabe borrar (`stmt_borrar_linea`, solo al pisar conflictos confirmados por HTTP)
e insertar; no tiene ningún `UPDATE hmores`. Solo escribe en partes **En
registro** (`con.est` 1, F-031); un parte Cerrado o Imputado ya tiene el
asiento analítico con Σ `tot`: editarlo lo descuadraría.

- **DA11 · Propuesta en tabla nueva** `reparto_pendiente` (las dos copias del
  ORM; 7.ª tabla y sus guardianes): una fila por grupo con firma del estado,
  líneas antes → después y estado (`pendiente`, `aceptada`, `aplicada`,
  `rechazada`). La escribe sv3 (en F-046 ya no residual: aplica el ideal a lo
  no congelado y propone lo congelado). *Recomendado* frente a columnas en
  `parte_registros` (no caben las extras que hay que crear).
- **DA12 · Un clic al aprobar el segundo parte**: sv4 detecta grupos con
  propuesta, muestra el aviso (obra, día, línea, horas antes → después) y, al
  confirmar, pide a sv5 por **HTTP síncrono** (destructivo, como pisar) el
  reajuste por obra: bajo el lock, por `synckey`, comprueba que el parte sigue
  En registro y que `can` es el «antes» (concurrencia optimista), y hace
  `UPDATE can/tot`, inserta la extra nueva o borra la que queda a 0. Si va bien,
  registra el segundo parte; sv4 marca `aceptada` y pide recálculo (F-042) y
  sv3 lleva lo reajustado a `partes` (excepción explícita a la congelación,
  solo con esos valores). Si falla, no se registra nada.
- **DA13 · Parte cerrado, línea encolada o en dedicación**: no se edita; el
  aviso ofrece «Mantener lo registrado» (`rechazada` ⇒ recálculo residual como
  F-045). *Recomendado* frente a regularizar en el complementario (rompe
  `synckey` = `registro_id`, F-024).
- **DA14 · Aprobadas no registradas**: sin Sigrid; las lleva sv3 como en DA12.
  **Concurrencia**: candado consultivo de PostgreSQL en `conciliar_todos`
  (base `partes`, nada de servidor). **Deshacer**: el reajuste no entra en
  `undo_log`. **Portal**: marca «reparto pendiente» en la matriz y las líneas
  afectadas de las dos obras; la espera de F-043 cubre el recálculo posterior.

## 9. Verificación MANUAL (humano; solo lectura salvo el despliegue)

- **M1 · antes de desplegar** (base `partes`): grupos que F-045 reparte de nuevo.

```sql
SELECT congeladas, count(*) AS grupos, sum(obras) AS obras
FROM (SELECT r.recurso_ide, r.fecha_int, count(DISTINCT r.obra_ide) AS obras,
        bool_or(d.approved OR coalesce(r.sigrid_estado, '')
                IN ('encolado', 'registrado', 'dedicacion')) AS congeladas
      FROM parte_registros r JOIN parte_documents d ON d.id = r.document_id
      WHERE d.is_active AND r.deleted_at_utc IS NULL AND NOT r.extra_auto
        AND coalesce(r.tipo_hora, '') IN ('', 'normal')
        AND r.recurso_ide IS NOT NULL
      GROUP BY r.recurso_ide, r.fecha_int HAVING count(*) >= 2) g
GROUP BY congeladas;
```

- **M2 · tras `.\redeploy_partes.ps1 -Solo sv3`** (lo pide el humano), en Log
  Analytics como en F-042 M2, filtrando `Log_s has 'reparto'`: INFO de reparto
  y, si los hay, WARNING de R25 (cuántos días tocaría F-046). Repetir la SQL
  de F-042 M1 sobre un día con dos obras sin aprobar: cifras de §3.
