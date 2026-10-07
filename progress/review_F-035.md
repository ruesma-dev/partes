<!-- progress/review_F-035.md -->
Revisión incremental desde 163320d (pasada 2): `git diff 163320d..7c1ca7f` (rama `feature/F-035-selector-recursos-por-empresa`)

# F-035 · Review

**Veredicto: APPROVED**

**Rigor:** `estandar` (declarado): fase RED, cobertura ≥ 80 % y mutación con
supervivientes analizados. RM5 N/A por nivel.

Lo aprobado en la pasada 1 (`git diff dev...163320d`, todo salvo el bug de
«Nuevo parte» y los dos huecos de C4) queda dado por bueno; su detalle está en
la versión de este fichero del commit `cc3c82c`.

## Delta revisado (4 commits)

| Commit | Cambio | Ficheros |
|---|---|---|
| `1d5cbef` | Arreglo `e.` → `r.` en el callback de `"emp-combo"` (cambio 1) y tests que **ejecutan con node** los callbacks de Nuevo parte y del modal (cambio 2) | `static/app.js` (l. 1581-1584), `tests/test_f035_vistas.py` |
| `e43a954` | (obs. 2) `_poner_trabajador` quita `recurso_manual` al casar con ficha; (obs. 4) `RecursoCatalog.cargado` y `ok: false` en `/api/sigrid/recursos` si nunca cargó | `parte_repository.py`, `recurso_catalog.py`, `app.py`, 3 ficheros de test |
| `cc2949f` / `7c1ca7f` | T9 con comando exacto en `current.md` (cambio 3); informe y cierre | `progress/` |

Las dos observaciones atendidas eran opcionales; el implementer las hizo
dentro del alcance (solo sv4) y con test. No cambian firmas públicas ni
mueven ficheros. Sí tocan el alcance medido por la campaña (ver C4 bis).

## Qué se ejecutó (resultado real)

- `bash harness/init.sh` tal cual: **ENTORNO LISTO**, exit 0. Raíz 446 passed,
  1 skipped; sv1–sv5 verdes por caché; **COBERTURA [OK] 97,0 % (194/200)**;
  **TAMAÑO OK** (requirements 142/150, design 248/250, impl 217/220).
  Avisos: F-014/F-032 `blocked`, ruff, infra sin tests y «coverage no pudo
  escribir coverage.json» (la puerta salió igualmente en [OK] con su cifra).
- Suite sv4 **sin caché** (`-p no:cacheprovider`): **1774 passed** en 968,2 s
  (1764 de la pasada 1 + 10 nuevos), sin ningún test ajeno en rojo.
- **Cambio 1 verificado**: en `app.js` no queda `e.categoria` ni
  `e.jornada_sugerida`; el callback usa `r.` en las tres líneas.
- **Cambio 2, RED reproducido**: en una copia (`git archive HEAD`, scratchpad)
  devolví las tres líneas a `e.`:
  `test_f035_r17_r19_nuevo_parte_al_elegir_recurso_rellena_todo` → **1 failed**
  (el gemelo del modal pasa, como debe). El test aísla el `_comboSimple(...)`
  real de `app.js` y comprueba categoría, jornada, `reside`, recarga del
  calendario y `updateBtn()`. Sin node, `skip` con motivo. Cuadra con la
  traza del informe (`ReferenceError: e is not defined`).
- **Cambio 3**: `current.md` § T9 trae `python services/partes-front/main.py`,
  Ctrl+F5 y las tres comprobaciones, en solo lectura y sin «Crear».

## Mutación del delta (RM1 y RM4)

**RM1:** la campaña se midió en `35fcfe4`, y `e43a954` toca tres ficheros del
alcance (`recurso_catalog.py`, `parte_repository.py`, `app.py`). Recalculado:
el alcance pasa de 454 a **471 líneas** y de 69 a **74 mutantes**; los 5
nuevos son todos de las líneas del delta (las 6 de `recurso_catalog.py` son
una property y su docstring: ningún mutante). **Campaña no reejecutada**
(la anterior duró 5973,8 s). En su lugar, **RM4**: los 5 mutantes aplicados
uno a uno en una copia del scratchpad y juzgados con los 6 ficheros
`test_f035_*` + `test_f023_catalogo_empresa.py` (119 tests):

| Mutante (original → mutado) | Resultado |
|---|---|
| `parte_repository.py:777` `ide is not None and …` → `ide is None and …` | **muerto**, 6 failed |
| `parte_repository.py:777` `… and reg.empleado_match_method ==` → `… or …` | **muerto**, 11 failed |
| `parte_repository.py:777` `== METODO_RECURSO_MANUAL` → `!=` | **muerto**, 17 failed |
| `app.py:1718` `if not recurso_catalog.cargado:` → `if recurso_catalog.cargado:` | **muerto**, 3 failed |
| `app.py:1722` `{"ok": False, "items": [],` → `{"ok": True, …` | **muerto**, 1 failed |

Cero supervivientes en el delta; el informe de mutación de la pasada 1 sigue
valiendo para el resto del alcance, que no ha cambiado. Ningún equivalente
sale muerto (RM3). No se quitó código defensivo (RM6): se añade una guarda.

## Checkpoints (estado final)

- **C1** [x] init.sh exit 0 · [x] ficheros base.
- **C2** [x] una `in_progress` · [x] rama correcta · [x] `current.md` con F-035
  arriba (arrastra otras features: práctica del repo ya aceptada) · [x] las
  `done` tienen resumen en `history.md` (el de F-035 lo escribe el líder al
  cerrar, como en F-033/F-037).
- **C3** [x] hexagonal · [x] ruta en primera línea · [x] sin prints/TODOs/
  secretos/dependencias (los `import` a mitad de `test_f035_vistas.py` llevan
  `noqa: E402`, menor) · [x] reglas de dominio: el alta manual vuelve a
  guardar la categoría; empleado ≠ recurso respetado.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] cada R con test trazable y en verde; R17/R19 ahora con tests
  que ejecutan el JS · [x] sin red ni BBDD (node local, SQLite en memoria) ·
  [x] T9 MANUAL en `current.md` con su comando exacto.
- **C4 bis** [x] `rigor` declarado · [x] fase RED real (pasada 1 + traza del
  delta, reproducida por mí) · [x] cobertura [OK] 97,0 % · [x] totales
  recalculados (69 en la campaña, 74 hoy) · [x] muertos: campaña > 60 s →
  recálculo + RM4 (5 del delta y 2 de la pasada 1) · [x] coste por mutante
  ≈ 1792 s · [x] sin «NO VÁLIDA», base rota 0 · [x] **RM1** el delta toca el
  alcance: cubierto con RM4 sobre todos sus mutantes (arriba) · [x] **RM2**
  coherente · RM5 N/A (estándar) · [x] **RM6** · N/A campaña manual · [x]
  supervivientes analizados · [x] «Evidencias» actualizadas (1774 tests, 97,0 %).
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T1–T8 y T10 `[x]` con commit `F-035 Tn:`; T9 `[ ]` es la
  verificación MANUAL del humano (consta en `current.md`; aceptable, como en
  F-030/F-031) · [x] árbol limpio · [x] `features.json` → `done` en este commit.

## Choques previsibles al mergear con F-036 y `dev` (de la pasada 1, vigentes)

1. **Sobre `dev` (con F-037)**: conflicto solo en `BACKLOG.md` (regenerar con
   init.sh) y `progress/current.md`.
2. **`ARCHITECTURE.md` semántica 12: conflicto seguro** con F-036, que
   reescribe la frase F-030 que F-035 amplía. Dejar el texto de F-036 + la
   frase de F-035, con el DNI en el orden de F-036 (`emp.dni`, vacío `res.cif`).
3. **`CLAUDE.md`: choque semántico sin conflicto textual.**
   `_SQL_RECURSOS_ACTIVOS` de sv4 es una **tercera copia** de `res.cla = 1` que
   ni la entrada de F-036 en la lista cerrada ni
   `tests/test_f036_recurso_persona_gemelos.py` cubren: quien mergee segundo
   añade sv4 a la entrada y una comprobación al guardián.
4. `features.json`, `BACKLOG.md`, `current.md`: triviales.
5. Semántica compatible: F-036 no toca `METODOS_RECURSO` de sv3 y su
   conciliador confirma `empleado_reside`. El nuevo borrado de
   `recurso_manual` solo actúa sobre esa marca de sv4; las de sv3 no se tocan.

## Observaciones que siguen abiertas (no bloquean; líder/humano)

- **Orden del DNI ofrecido** (R2): el que se muestra y se busca es `res.cif`
  primero; el guardado con ficha es `emp.dni` primero (R12), como F-036.
  Unificarlo cambia R2: decisión del humano, mejor junto al merge con F-036.
- `azure-apps/partes.md` §3.3 enumera los métodos que el portal da por
  casados: valorar añadir `recurso_manual` (fuera de este repo).
- T9 (MANUAL) pendiente del humano antes de desplegar.
