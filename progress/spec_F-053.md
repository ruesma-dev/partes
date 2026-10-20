<!-- progress/spec_F-053.md -->
# spec-author · F-053 · Pisar sin borrar (2026-10-20)

Spec en `specs/F-053-pisar-sin-borrar/` (rama `feature/F-053-pisar-sin-borrar` desde `dev`
4bda57e, worktree `partes-wt-f053`). `F-053` estaba libre en `dev` y en todas las ramas
locales (`git grep F-053` sobre cada una: sin resultados). Topes: requirements 130/150,
design 247/250. `features.json`: F-053 `spec_ready`, prioridad 2, rigor crítico; las no
terminadas con prioridad ≥ 2 suben 1 (F-014 3, F-049 4, F-047 5, F-052 6, F-038 7, F-032 8,
F-027 9, F-026 10, F-018 11, F-006 12, F-007 13, F-008 14, F-011 15); F-034 sigue en 1.

## Qué hace

- **sv5**: el pisado deja de hacer `DELETE` y pasa a `stmt_anular_linea` (`UPDATE hmores SET
  can = 0, tot = 0` con `WHERE` optimista —`ide`, recurso, fecha, código, `can` leído—, sin
  enlaces y con la guarda de parte abierto de F-034); `stmt_borrar_linea` desaparece y un
  test de fuente vigila que no vuelva. Nada más de la pisada cambia (synckey, `tex`, cuenta).
- **Choques**: una línea a 0 ya no choca (si no, cada pisada sería un conflicto eterno y un
  `parte_cerrado` sin horas); incidencia contra la misma incidencia ⇒ `omitido`
  `incidencia_en_sigrid` (ponerla a 0 no hace nada y F-034 R4 dejaría duplicarla); choque con
  una línea enlazada (albarán, factura, dedicación, nómina) ⇒ `omitido` `linea_enlazada`
  (hoy se borran). Pisada que cambió en la ventana ⇒ `pisada_no_anulada`.
- **Resultado**: `anuladas` sustituye a `borradas` en el JSON de los dos canales.
- **sv4**: textos del modal y del resultado («se pone a 0 en Sigrid, no se borra»),
  `reparto_obras` suma `anuladas`, `MOTIVO_LINEA_REGISTRADA` sin aconsejar borrar.

## Hallazgos

1. El único `DELETE` en ejecución de sv5 es `stmt_borrar_linea`; el otro es la fase
   `limpiar` de `prueba_escritura_sigrid.py` (solo `PRUEBA-IA` de la obra de pruebas; DA9
   recomienda mantenerlo).
2. Hoy se pueden pisar líneas manuales, ajenas (`porcentajes:`…) y **otras del portal**
   (`partes:<otro id>`), y también enlazadas: no se mira `can` ni enlaces.
3. F-024: una `partes:<id>` a 0 sigue `presente` con la diferencia de horas; ya no pasará a
   `borrado_sigrid`. F-052 la clasificará `anulada_en_sigrid` (con `traer_de_sigrid`).
4. `MOTIVO_LINEA_REGISTRADA` no describe el pisado: aconseja a Administración borrar a mano
   para luego reaprobar. Cambiarlo deja la vía sin sustituta hasta F-052 (DA8).
5. `porcentajes` (`dedicacion-transfer`) tiene el mismo `stmt_borrar_linea`: aviso en
   `azure-apps/partes.md`, sin tocar su repositorio.
6. Cuántas líneas se borraron al pisar **no es medible en Sigrid**; sí, opcionalmente, en
   los logs de sv5 (`[sigrid-write] DELETE FROM hmores`).

## Decisiones abiertas para el humano (`design.md` §12)

DA1 qué se pone a 0 (A `can`/`tot`) · DA2 synckey (A intacta) · DA3 cómo se reconoce (A por
los datos + log) · DA4 qué se pisa (A todo salvo enlazadas) · DA5 líneas a 0 no chocan (A) ·
DA6 incidencias (A `incidencia_en_sigrid`) · DA7 `anuladas` (A) · DA8 `MOTIVO_LINEA_REGISTRADA`
(A cambiarlo ya; B dejarlo a F-052) · DA9 `prueba_escritura_sigrid.py` (A mantener) · DA10
línea del portal pisada (A sin cambio en el portal) · DA11 rigor crítico · DA12 `WHERE`
optimista (A).

## Pendiente

- **Humano**: aprobar la spec y DA1–DA12.
- **Líder**: M1 de solo lectura (`design.md` §9) antes de implementar; decide DA1 y DA4/DA6.
- **Implementación**: solo con F-034 fusionada en `dev` (precondición de `tasks.md`).
- **Nota para F-052** (no se toca su rama): tras F-053 las pisadas quedan a 0, no borradas;
  `origen_linea` de `pisado.py` es candidata a reutilizarse en su `origen_de`.
