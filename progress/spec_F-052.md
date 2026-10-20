<!-- progress/spec_F-052.md -->
# F-052 · Sincronizar con Sigrid — Informe del spec-author

Fecha: 2026-10-20. Rama `feature/F-052-sincronizar-con-sigrid` desde `dev` (`ff2ed8e`),
worktree `C:\Users\pgris\PycharmProjects\partes-wt-f052`. Spec en
`specs/F-052-sincronizar-con-sigrid/` (requirements 125/150, design 209/250, tasks 15 tareas).
Entrada en `harness/features.json` (`spec_ready`, rigor `critico`, prioridad 2) y `BACKLOG.md`
regenerado. Sin push.

## ID

F-052: el siguiente libre. `dev` llega a F-051; las ramas abiertas añaden F-047, F-049 y F-050;
ninguna usa F-052.

## Qué se ha diseñado

- **sv5**: `POST /api/sincronizar/leer` (solo lectura, sin lock, base `ruesma`): `hmores` de la
  obra (`obride`) o del recurso (`reside`) en el periodo, paginado con `OFFSET/FETCH`, más las
  líneas de los synckeys del portal estén donde estén; devuelve `origen` (`partes`, `ajena`,
  `manual`) y `registro_id`, para que sv4 siga sin conocer el formato del synckey (F-024).
- **sv4**: botón «Sincronizar con Sigrid» en obra y persona, comparación pura en 11 clases,
  panel con filtros y selección en masa, y `POST /api/sincronizar/aplicar`, que revalida por
  firma (vuelve a leer Sigrid) antes de escribir.
- **Primera entrega (DA1 = A)**: acciones solo hacia el portal (`marcar_registrada`,
  `traer_de_sigrid` de horas, y `a_papelera` / `reaprobar` / `restaurar` sobre las rutas que ya
  existen). Escribir en Sigrid (`llevar_a_sigrid` con el reajuste F-046, poner a 0 las huérfanas,
  importar líneas manuales al portal) va en una feature posterior.

## Qué reutiliza y qué es nuevo

Reutiliza, sin cambiarla: la comprobación de F-024 (y su paso a `borrado_sigrid`), el ámbito de
F-022, el actor de F-017, el recálculo de F-042, las guardas de F-043/F-046, la papelera, el
restaurar, el modal de aprobar y `ENLACES_HMORES`. «Conciliar» (`/conciliacion`, F-039) no se
reutiliza porque es el casado de trabajadores, no de líneas; de ahí el nombre «Sincronizar».
Es nuevo: la lectura por ámbito de sv5, la clasificación, el panel y `traer_de_sigrid`, la única
escritura nueva sobre líneas congeladas (una excepción acotada, como la materialización de
F-046; `congelacion.py` y `esta_congelado` no cambian).

## Decisiones abiertas (design §8)

DA1 alcance · DA2 periodo · DA3 campos de `traer_de_sigrid` · DA4 qué se compara · DA5
resultado efímero frente a tabla · DA6 «marcar revisada» · DA7 traza del actor · DA8 rigor ·
DA9 sitio en la cola (recomendado F-050 → F-049 → F-052 → F-014 → F-047) · DA10 dónde se lee
`hmores`. Todas llevan alternativas y recomendación.

## Verificaciones manuales

M1 (antes de implementar, solo lectura): volumen y tiempo de `hmores` por obra grande y por
recurso, en mes natural y en periodo de nómina, con las dos formas del filtro; fija el tope, la
página y el `WHERE`. M2–M4 después (lectura real, modo pruebas en la 0404, producción).
Los conectores de datos de esta sesión no estaban disponibles, así que no se ha adelantado
ninguna cifra de M1.

## Hallazgos

- **H1**: la regla del humano «en Sigrid no se borra» choca con el pisado de conflictos de sv5
  (`stmt_borrar_linea`, `DELETE`, paso 9 de `registro_pipeline.py`) y con el texto del candado
  `MOTIVO_LINEA_REGISTRADA` («borra la línea en Sigrid»). Queda fuera de F-052; se propone una
  feature aparte.
- **H2**: `docs/ARCHITECTURE.md` dice «máx. 1.000 filas por petición» de sigrid-api, y la
  instancia desplegada admite 500.000 (`CLAUDE.md` raíz, `azure-apps/sigrid_api.md` §4.1). F-052
  pagina igual; F-038 es quien debe corregir ese dato.
