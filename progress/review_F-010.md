<!-- progress/review_F-010.md -->
# F-010 · Saneamiento: resincronizar `orm_models.py` entre sv3 y sv4 — review

Rama `feature/F-010-resincronizar-orm-models` · HEAD `cd62e5b` · base `dev`
`716a4f7` · sdd=true · spec aprobada por el humano (D1–D5).

## Veredicto

**APPROVED**

Todo lo comprobado se ha verificado de forma independiente por el reviewer
(no leyendo el informe del implementer): suites completas de raíz/sv3/sv4/sv5
ejecutadas aquí, DDL generado recalculado, guardián probado a base de romperlo
en un worktree aislado, mutantes regenerados con `harness.mutacion` y tres
supervivientes candidatos comprobados uno a uno.

## Nivel de rigor

`rigor: "estandar"` declarado en `harness/features.json`. Exige C1–C3, C3 bis,
C5, tests trazables (C4), **fase RED** en los requisitos centrales,
**cobertura** de las líneas cambiadas ≥ 80 % y **campaña de mutación** con los
supervivientes analizados. Las tres puertas se cumplen sin ningún N/A.

## C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` ejecutado tal cual por el reviewer: `exit 0`,
      `ENTORNO LISTO`. Rama detectada `feature/F-010-resincronizar-orm-models`,
      `15 passed` en la raíz, sv3/sv4/sv5 en verde, `PUERTA COBERTURA` en
      `[OK] 100.0% de 60 líneas cambiadas cubiertas (60/60, umbral 80%, nivel
      estandar)`.
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md` (los valida el propio `init.sh`).

Avisos no bloqueantes que ya venían de antes: ruff con 430 avisos de deuda
previa (eran 450 en `dev`), sv1/sv2 sin directorio de tests, `infra` sin
comando de tests.

## C2 — El estado es coherente

- [x] Una sola feature `in_progress` (F-010); lo valida `init.sh`.
- [x] Rama actual = la de la feature; ningún commit en `dev` ni en `main`.
- [x] `progress/current.md` describe la sesión activa; el resto es la sección
      explícita «Notas de contexto para la próxima sesión», patrón ya usado y
      aceptado en F-004/F-012/F-013 (no son restos de trabajo a medias).
- [x] Las features `done` anteriores tienen su resumen en `history.md`
      (F-010 se anotará al cerrar).

## C3 — El código respeta arquitectura y convenciones

- [x] **Hexagonal**: todo lo tocado vive en `infrastructure/database/` de sv3
      y sv4, más tests y documentación. Ni `domain/`, ni `application/`, ni
      `interface_adapters/` cambian. `ddl_complementario()` es una función
      pura de infraestructura dentro del propio `orm_models.py` (no crea una
      pieza duplicada nueva fuera de la lista cerrada del `CLAUDE.md`).
- [x] **Primera línea con la ruta relativa** en los seis ficheros nuevos
      (`# tests/test_f010_...`, `# tests/dobles.py` como precedente) y en los
      dos `orm_models.py` (`# infrastructure/database/orm_models.py`, que es
      la misma ruta relativa al servicio en ambos: condición necesaria para
      que R1 pueda exigir igualdad byte a byte).
- [x] Sin `print()` de debug, sin TODO sin contexto, sin secretos, sin
      dependencias nuevas (todo es SQLAlchemy, ya presente). No se toca
      `.env`, ni manifiestos, ni `infra/`.
- [x] **Trampa 3 de C3 (schema duplicado)**: es justo lo que arregla la
      feature. Verificado por el reviewer:
      `sha256 = 33f1c033c81d27f92034f8db2bd9caa09892f568fee70b4fede776ee34233589`
      en las DOS copias; `cmp` sin diferencias.
- [x] Trampas 1 y 2 (empleado ≠ recurso; incidencias) no las toca esta
      feature: no cambia ningún lector ni escritor de columnas.
- [x] LÍMITE DE SERVICIO: la duplicación tolerada no crece; se hace
      verificable. Ningún cambio en sv1, sv2, sv5 ni `infra/`.
- [x] `ruff` sobre lo nuevo: **limpio** en los seis ficheros de test. En los
      ficheros de producción quedan 3 avisos, todos **deuda previa** ya
      presente en `dev` (comprobado ejecutando ruff sobre un worktree de
      `dev`): `UP037` en cada copia de `orm_models.py` e `I001` en
      `sqlalchemy_parte_repository.py`. Los 18 `ISC004` que `dev` tenía en
      `sqlalchemy_parte_repository.py` desaparecen (22 → 1 avisos en ese
      fichero); los 84 de `parte_repository.py` son idénticos a los de `dev`.

## C3 bis — Documentos de fuera

Aplica: la feature modifica `docs/referencia/partes-proyecto.md` (§5 y
cabecera). No añade ningún documento nuevo.

- [x] La cabecera lleva la constancia de la corrección con fecha, según D5:
      «**Corregido el 2026-08-18 por F-010**: §5 (esquema real de la base
      `partes`)», enumerando lo que decía mal la versión anterior.
- [x] Ningún original PDF/ofimática en el repositorio ni en el árbol:
      `git diff --diff-filter=A --name-only dev...HEAD` no añade ningún
      binario (los 11 ficheros añadidos son `.py` y `.md`), y
      `git ls-files docs/referencia/*` no devuelve ningún
      `.pdf/.docx/.xlsx/.pptx`.
- [x] **Barrido de datos sensibles ejecutado por el reviewer** sobre las
      líneas añadidas de `docs/referencia/partes-proyecto.md` y
      `docs/ARCHITECTURE.md` (59 líneas `+`), con estos patrones:
      - correos `[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}` → 0 coincidencias
      - IPv4 `\b([0-9]{1,3}\.){3}[0-9]{1,3}\b` → 0
      - GUID `[0-9a-f]{8}-[0-9a-f]{4}-...` → 0
      - credenciales `password|passwd|secret|token|api[_-]?key|bearer|pwd|`
        `connectionstring|AccountKey|sv=20|eyJ...` → 0
      - DNI `\b[0-9]{8}[A-Za-z]\b` → 0
      La corrección es puramente descriptiva del esquema; el `<ip-vpn-sigrid>`
      que ya estaba en la cabecera sigue redactado y no se toca.
- [x] Nada redactado nuevo que anotar (no se ha eliminado ningún dato: se han
      corregido descripciones).
- [x] `azure-apps/partes.md` §4: commit local `8f55505` («partes: F-010
      corrige el esquema de la BBDD…», 43 inserciones / 12 borrados),
      **sin push** y con el árbol limpio, como manda la memoria del proyecto
      (ese repositorio no tiene remoto).

## C4 — La verificación es real

- [x] Cada requisito EARS tiene al menos un test trazable y todos pasan
      (tabla más abajo).
- [x] **Ningún test toca red ni BBDD real.** Comprobado con grep sobre los
      seis ficheros nuevos: cero apariciones de `create_engine`, `psycopg`,
      `DATABASE_URL` o `postgres` fuera de `postgresql.dialect()` (compilación
      de tipos sin conexión). `initialize()` se prueba con un `engine` doble
      (D7); R11 usa SQLite en memoria vía `tests/dobles.py`. **Ningún agente
      ha ejecutado DDL contra el PostgreSQL compartido.**
- [x] Las verificaciones `MANUAL (humano)` M1–M3 están enumeradas con sus
      pasos y su SQL exacto en `progress/impl_F-010.md` §6 y en
      `tasks.md`, y `progress/current.md` las referencia como pendientes.
      Ver «MANUAL pendiente» al final.

### Suites ejecutadas por el reviewer (sin regresión)

| Suite | `dev` (worktree limpio) | rama | Δ |
|---|---|---|---|
| raíz `tests/` | 6 passed | **15 passed** | +9 |
| sv3 `partes-persistencia` | 95 passed | **112 passed** | +17 |
| sv4 `partes-front` | 448 passed, **5 warnings** | **462 passed, 1 warning** | +14 |
| sv5 `partes-transfer` | — | **87 passed** | sin cambios |
| **Total** | | **676 en verde, 0 fallos** | |

Los recuentos de la sección «Evidencias» del informe cuadran exactamente con
los medidos aquí. El único warning que queda en sv4 es el
`StarletteDeprecationWarning` de `fastapi.testclient`, ajeno a F-010.

**Dependencias F-002/F-003/F-004:** ninguna regresión. Los tests de F-004
(R12/R13/R18) **no se han tocado** (`git diff --name-only dev...HEAD | grep
f004` → vacío) y siguen en verde incluso con los avisos convertidos en error:
`python -m pytest tests -q -W error::sqlalchemy.exc.SAWarning -k "f004 or
f010"` → **148 passed**. La semántica de borrado se conserva: lo congelado se
sigue omitiendo (`test_f010_r11_lo_congelado_se_sigue_omitiendo_sin_avisos`
comprueba que el parte con línea `registrado` sobrevive a `vaciar_papelera`).

### Trazabilidad requisito → test (todos verdes)

| Req. | Test | Verificado por el reviewer |
|---|---|---|
| R1 copias byte-idénticas | `tests/test_f010_orm_models_gemelos.py::test_f010_r1_las_dos_copias_son_byte_identicas` | sha256 idéntico + `cmp` sin diferencias |
| R2 mismo schema declarado | `…::test_f010_r2_las_dos_copias_declaran_el_mismo_schema` | huellas iguales; roto a propósito, ver abajo |
| R3 el guardián muerde | `…::test_f010_r3_el_guardian_detecta_una_copia_alterada` (4 casos) + `…_el_arbol_real_no_se_toca` | reproducido a mano en worktree aislado |
| R4 contenido canónico | `…::test_f010_r4_el_orm_canonico_tiene_las_cuatro_tablas_y_56_columnas`, `…_los_atributos_de_las_columnas_reunidas` | 4 tablas y 56 columnas recontadas |
| R5 comentarios conservados | (documental, C3) | leído: comentarios de conciliación de sv3 + bloque de traza Sigrid, docstring «CUATRO tablas» |
| R6 generador determinista | `services/partes-persistencia/tests/test_f010_r6_ddl_complementario.py` (10 tests) + `services/partes-front/tests/test_f010_r6_ddl_complementario_sv4.py` (6) | DDL regenerado y comparado literalmente |
| R7 `initialize()` sv3 | `services/partes-persistencia/tests/test_f010_r7_initialize_sv3.py` (3) | leído: engine doble, sin BBDD |
| R8 `initialize()` sv4 | `services/partes-front/tests/test_f010_r8_initialize_sv4.py` (4) | leído: mismo doble + caso de fallo → `False` con `logger.exception` |
| R9 toda columna con su ALTER | `…test_f010_r9_toda_columna_tiene_su_alter` (sv3) y `…_r9_sv4_…` (sv4) | recalculado: 0 columnas sin `ALTER` |
| R10 solo aditivo | `…test_f010_r10_ddl_solo_aditivo`, `…_ninguna_tabla_se_crea_sin_if_not_exists` | recalculado: 0 sentencias no aditivas, 0 sin `IF NOT EXISTS` |
| R11 borrado sin SAWarning | `services/partes-front/tests/test_f010_r11_borrado_sin_sawarning.py` (4) | 148 tests f004+f010 con `-W error::SAWarning` |
| R12 documentación | (documental, C3/C3 bis) | diff leído y contrastado contra el ORM |

### Verificación independiente del DDL generado (R6/R9/R10)

Cargando las dos copias por ruta y llamando a `ddl_complementario()`:

- **Las dos copias generan exactamente la misma tupla** (`sv3 == sv4: True`).
- **118 sentencias = 113 columnas no PK + 4 índices + 1 `DDL_EXTRA_POSTGRES`**,
  el conteo exacto que exige R6(c).
- Columnas por tabla: `empleado_alias` 7, `parte_documents` 47,
  `parte_registros` **56**, `undo_log` 7 — la unión declarada en R4.
- Aserciones literales de R6(a) presentes tal cual:
  `ALTER TABLE parte_registros ADD COLUMN IF NOT EXISTS extra_auto BOOLEAN
  DEFAULT 'false' NOT NULL`, `… sigrid_estado VARCHAR(16)`,
  `… horas_orig FLOAT`, `ALTER TABLE undo_log ADD COLUMN IF NOT EXISTS actor
  VARCHAR(120)`, `CREATE INDEX IF NOT EXISTS ix_parte_registros_deleted_at_utc
  ON parte_registros (deleted_at_utc)` y el índice único parcial
  `ux_parte_documents_sha256_active … WHERE is_active` **al final**.
- R6(b): **ninguna** de las 4 claves primarias (`parte_documents.id`,
  `parte_registros.id`, `empleado_alias.nombre_norm`, `undo_log.id`) genera
  `ALTER`.
- R9: **0 columnas no primarias sin su `ADD COLUMN IF NOT EXISTS`**.
- R10: **0 sentencias** con `ALTER COLUMN`, `DROP `, `RENAME `, `TRUNCATE`,
  `DELETE ` o `UPDATE `; **las 118 llevan `IF NOT EXISTS`**. Sobre una BBDD
  que ya tiene las columnas es un no-op completo.
- R7/R8: los dos `initialize()` ejecutan **la misma** tupla (los tests la
  comparan contra `ddl_complementario()` de su propia copia, y las dos copias
  son byte-idénticas y generan lo mismo, comprobado arriba con doble carga por
  ruta), cada uno en **una sola transacción** (`begin()` una vez).

### Verificación independiente del guardián (R1/R2/R3)

Reproducido en un **worktree aislado** de la rama (nunca en el árbol real),
alterando SOLO la copia de sv4 y ejecutando la suite de la raíz:

| Alteración | Resultado |
|---|---|
| `sigrid_estado String(16)` → `String(17)` | R1 y R2 FALLAN; mensaje: `parte_registros.sigrid_estado.tipo: sv3='VARCHAR(16)' != sv4='VARCHAR(17)'` |
| quitar `index=True` de `deleted_at_utc` | R1 y R2 FALLAN; nombra `…deleted_at_utc.index: sv3=True != sv4=False` **y** `indice 'ix_parte_registros_deleted_at_utc' solo en sv3` |
| añadir un salto de línea al final (diferencia solo textual) | **R1 FALLA** y R2 pasa → confirma que R1 es la barrera final y R2 el diagnóstico |
| borrar la clase `UndoLogOrm` | R1 y R2 FALLAN; `tabla 'undo_log': solo en sv3` |

Worktree eliminado; árbol real intacto (`git status` limpio).

## C4 bis — El rigor declarado se cumple

- [x] `rigor` declarado y válido: `estandar`.
- [x] **Fase RED con traza real** en `progress/impl_F-010.md`, para los
      requisitos centrales y en commits comprobables del historial:
      - T1 `80a9cb3` («…(R1-R4) en ROJO»): traza del guardián fallando contra
        el árbol real, con el `unified diff` y la lista de columnas
        divergentes (`sigrid_*` solo en sv4, `horas_orig`/`extra_auto` solo en
        sv3, `tabla 'undo_log': solo en sv4`). Es la RED natural de la feature.
      - T2 `efc8452` («…en ROJO»): `ImportError: cannot import name
        'DDL_EXTRA_POSTGRES'`.
      - T4/T5/T6: trazas de los `AssertionError` de `_DDL_ALTERS` y
        `ADD COLUMN IF NOT EXISTS` aún presentes, y del `SAWarning: DELETE
        statement on table 'parte_registros' expected to delete 1 row(s); 0
        were matched`.
      Además, la parte cuyo entregable es el propio test (R3) demuestra su RED
      rompiendo copias en `tmp_path`, y el reviewer lo ha reproducido a mano
      (tabla anterior).
- [x] **Cobertura**: `PUERTA COBERTURA` de `bash harness/init.sh` en
      `[OK] 100.0%` de 60 líneas cambiadas (60/60), umbral 80 %.
- [x] **Mutación verificada de forma independiente**, no leída del informe:
      - `harness.alcance.alcance_de_feature("F-010")` reproduce el mismo
        alcance que declara `progress/mutacion_F-010.md`: origen `rama`
        `716a4f7..feature/F-010-resincronizar-orm-models`, y **257 líneas**
        repartidas exactamente igual (sv4 `orm_models.py` 113, sv4
        `parte_repository.py` 24, sv3 `orm_models.py` 106, sv3
        `sqlalchemy_parte_repository.py` 14).
      - `harness.mutacion.generar_mutantes` (cálculo puro) devuelve **23
        mutantes**, el mismo total del informe: 4 en la copia de sv4, 19 en la
        de sv3, 0 en los dos repositorios. No hay campaña de cero mutantes que
        justificar (la prueba de control no aplica).
      - **Muestreo de tres mutantes** aplicados a mano en el worktree aislado y
        ejecutando la suite del servicio correspondiente: `String(16)→String(17)`
        en `sigrid_estado` (sv3) → 2 tests rojos; `undone nullable=False→True`
        (sv3) → 1 test rojo; `CreateIndex(if_not_exists=True→False)` (sv4) →
        2 tests rojos. Los tres mueren, como afirma el informe.
- [x] **Cero supervivientes**, ninguna sección en `PENDIENTE`. El informe de
      mutación documenta además, con honestidad, la primera campaña (18
      supervivientes) y **no los cierra como equivalentes**: añade 11 tests que
      fijan el DDL literal de `undo_log` y de las siete `sigrid_*`, el
      autoincremento de las PK, los defaults de Python y el orden de los
      índices, más un fichero que ejercita **la copia de sv4** (que era una
      tautología: R8 comparaba el generador contra sí mismo). Buen trabajo:
      esto es exactamente para lo que sirve la puerta.
- [x] Sección **«Evidencias»** con los cuatro números: tests (676 verdes),
      cobertura de lo cambiado (100 %, 60/60), mutantes/supervivientes (23/0) y
      tiempo de la suite (≈ 76 s; medido aquí: raíz 2,0 s, sv3 1,7 s, sv4
      35,6 s, sv5 3,9 s).
- [x] Ningún punto marcado N/A.

## C4 ter — Rutas sensibles

**N/A justificado**: este repositorio no declara `harness/rutas_sensibles.json`
(no existe el fichero; solo está el `.ejemplo.json`). Según `CHECKPOINTS.md`,
sin declaración el bloque es N/A y no hay nada que justificar. Se anota igual
para que conste el motivo. (F-007 traerá esa declaración para el prompt de sv2.)

## C5 — La sesión se cerró bien

- [x] `tasks.md` con T1–T9 en `[x]` y un commit por tarea, con el formato
      exigido: `80a9cb3` T1, `efc8452` T2, `6719590` T3, `3a15064` T4,
      `f2ce6d1` T5, `6ede86c` T6, `4404348` T7, `121e6ee`+`6e7154a`+`cd62e5b`
      T8/T9. Todos con prefijo `F-010 Tn: …` y en español.
- [x] Árbol limpio: `git status --porcelain` vacío; ningún artefacto ni
      fichero temporal sin trackear. Los 11 ficheros añadidos son los cinco
      de test previstos, la spec, los dos informes de `progress/` — nada más.
- [x] `features.json` refleja el estado real (`in_progress`; pasa a `done`
      cuando el líder cierre con este APPROVED).
- [x] Solo se tocan los ficheros previstos en `design.md` §3 y §4. Las dos
      desviaciones están declaradas y son correctas: `key=lambda i: i.name or ""`
      (evita comparar `str` con `None` si algún día hay un índice sin nombre) y
      la retirada del import `delete` en `parte_repository.py`, que se quedó
      sin usos tras R11 (el propio diseño lo anticipaba).

## Observaciones (no bloquean el APPROVED)

1. **M1 solo mira los índices de `parte_registros`.** El generador emite
   también `CREATE INDEX IF NOT EXISTS ix_parte_documents_source_sha256 ON
   parte_documents (source_sha256)`, que el DDL a mano de sv3 nunca creaba. El
   diseño (§2.1) afirma —contra `pg_indexes` de la base real— que el único
   índice que falta es `ix_parte_registros_deleted_at_utc`, así que lo esperado
   es que este otro ya exista y la sentencia sea no-op. Aun así, **conviene
   ampliar el SQL de M1** a
   `WHERE schemaname='public' AND tablename IN ('parte_documents','parte_registros')`
   para que la comprobación manual cubra los dos únicos cambios físicos
   posibles, no uno. Es una mejora de la verificación manual, no un defecto del
   código.
2. **`progress/current.md` remite al informe** para el SQL exacto de M1–M3 en
   vez de inlinearlo. C4 pide «con su comando exacto»; los comandos están,
   completos, en `impl_F-010.md` §6 y en `tasks.md`, y `current.md` los
   referencia de forma explícita — mismo patrón aceptado en F-004 y F-013. Se
   acepta, pero pegar el `SELECT indexname …` en `current.md` ahorraría un salto
   al humano.
3. **`undo_log.undone` se genera sin `DEFAULT`** (`ALTER TABLE undo_log ADD
   COLUMN IF NOT EXISTS undone BOOLEAN NOT NULL`), porque el ORM describe la
   BBDD real, que no tiene `server_default` en esa columna (D1). Hoy es no-op.
   El docstring de `ddl_complementario()` ya avisa de que una columna `NOT NULL`
   sin default sobre una tabla con filas hará que PostgreSQL rechace el `ALTER`
   y el servicio no arranque, y lo declara deliberado («mejor fallar en voz
   alta»). Queda anotado para quien añada columnas en F-015.

## MANUAL pendiente (humano, requiere BBDD real)

Enumeradas con sus pasos exactos en `progress/impl_F-010.md` §6 y
`tasks.md`; el reviewer las ha revisado y son ejecutables tal cual:

- **M1 · el único cambio físico es el índice.** Arrancar sv3 o sv4 en local
  con el `.env` de desarrollo y ejecutar:
  `SELECT indexname FROM pg_indexes WHERE schemaname='public' AND tablename='parte_registros' ORDER BY 1;`
  → debe listar `ix_parte_registros_deleted_at_utc` (nuevo),
  `ix_parte_registros_document_id`, `ix_parte_registros_empleado_ide` y
  `parte_registros_pkey`. Y que no cambió el número de columnas:
  `SELECT table_name, count(*) FROM information_schema.columns WHERE table_schema='public' GROUP BY 1 ORDER BY 1;`
  → `empleado_alias 7`, `parte_documents 47`, `parte_registros 56`,
  `undo_log 7`. **Recomendación del reviewer** (observación 1): ampliar la
  primera consulta a `tablename IN ('parte_documents','parte_registros')`.
- **M2 · el arranque no revienta.** `python main.py` (o `main_worker.py`) en
  sv3 y `python main.py` en sv4 terminan sin excepción en `initialize()`; en
  el log, `[parte-repo] esquema inicializado (118 sentencias
  complementarias).` en sv3 y `[parte-repo-sv4] esquema inicializado (118
  sentencias complementarias).` en sv4 — **con el mismo número en los dos**,
  que el reviewer ha recalculado: **118**.
- **M3 · despliegue** (cuando el humano lo decida, `redeploy_partes.ps1`):
  orden habitual sv3 antes que sv4; el DDL es el mismo e idempotente, así que
  el orden no es crítico.

## Automejora del arnés (propuesta, NO aplicada)

Detectada por el implementer en la campaña de mutación y confirmada por el
reviewer al recalcularla. Es **genérica** (vale para cualquier monorepo con
arnés), así que si el humano la aprueba debe portarse también a `arnes-base`,
y encaja de lleno en el backlog de **F-009**:

1. **`harness/mutacion.py` solo ejecuta la suite del servicio dueño del
   fichero mutado.** Los guardianes que viven en la suite de la raíz —como el
   de F-010, que es una propiedad *entre* dos servicios— nunca matan un
   mutante, aunque `init.sh` sí lo cace. Resultado: supervivientes falsos que
   invitan a cerrarse como «equivalentes» y que tapan huecos reales (aquí
   taparon dos: sv3 no probaba lo que solo usa sv4, y sv4 no probaba su copia
   del generador). **Propuesta:** que la campaña ejecute, además de la suite
   del servicio, la suite de la raíz cuando exista; o, como mínimo, que el
   informe de mutación imprima qué suites se ejecutaron por cada mutante, para
   que el reviewer sepa qué no se estaba mirando.
2. **`CHECKPOINTS.md` C4 bis, matiz al muestreo de supervivientes.** Cuando
   una campaña declara **cero** supervivientes, el protocolo actual solo pide
   recalcular alcance y número de mutantes: eso no distingue una suite que mata
   de verdad de un informe optimista. **Propuesta:** exigir explícitamente lo
   que aquí se ha hecho de oficio — aplicar a mano dos o tres mutantes y
   comprobar que la suite se pone en rojo. Es la contrapartida natural de la
   regla que ya existe para el caso de cero mutantes.
