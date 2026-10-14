# F-046 · Informe del implementer: reajuste en Sigrid al aprobar

Rama `feature/F-046-reajuste-en-sigrid-al-aprobar` (worktree `partes-wt-f046`), rigor
**crítico**. Toca sv5, sv3, sv4, las dos copias del ORM, docs y `azure-apps/partes.md`.
Interruptor `REPARTO_REAJUSTE` (sv3) **apagado por defecto**: apagado, sv3 es F-045 (R10).

## T1 · API real de F-045

`9c5b7a1` es ancestro de HEAD; `test_f045_*` (sv3): 211 passed. **H9**: `LineaDia` ya trae
`extra_auto` y `base_id` (enmienda A de F-045): se usan tal cual y solo se añade
`reajustable: bool = False`.

## Qué cambió (un commit por tarea, `git log dev..HEAD`)

| Bloque | Ficheros |
|---|---|
| sv5 T2–T5 | `application/services/reajuste_lineas.py` (nuevo, veredictos R21/R22/R26), `application/pipelines/reajuste_pipeline.py` (nuevo), `infrastructure/sigrid/sigrid_write_client.py` (solo métodos nuevos), `domain/models/registro_models.py` (`OpReajuste`, `VeredictoReajuste`, `ResultadoReajuste`; `LineaSigrid.pre/hmoide/enlazada` con defecto), `interface_adapters/api/app.py` (rutas), `main.py` (composición) |
| ORM T8 | `RepartoPendienteOrm` + `ESTADOS_REPARTO` en las DOS copias (byte-idénticas); guardianes a siete tablas con `COLUMNAS_REPARTO_PENDIENTE` |
| sv3 T9–T12 | `reparto_ponderado.py` (`proponer_dia`, `CambioCongelada`, `PropuestaDia`), `reajuste_reparto.py` (nuevo), `recurso_conciliador.py`, `sqlalchemy_parte_repository.py`, `config/settings.py`, `interface_adapters/api/app.py`, `tests/dobles.py` (`RepositorioFake` al día) |
| sv4 T14–T18 | `application/services/reparto_aviso.py` (nuevo), `parte_repository.py`, `transfer_client.py`, `recalculo_publisher.py` (`MOTIVO_REAJUSTE`), `interface_adapters/web/app.py`, `static/app.js`, `static/styles.css`, plantillas de obra y trabajador |
| Raíz/docs T16, T20, T21 | `tests/test_f046_contrato_reajuste.py`; `docs/ARCHITECTURE.md`; `docs/referencia/partes-proyecto.md`; `azure-apps/partes.md` (commit local `azure-apps`, solo ese fichero) |

**No tocados** (comprobado con `git diff dev --stat`): `estado_parte.py`, `cuenta_analitica.py`,
`interface_adapters/queue`, `registro_pipeline.py` (sv5); `congelacion.py`, `jornada_resolver.py`
(sv3 y sv4), `pareja_extra.py`; `esta_congelado`/`ESTADOS_CONGELADOS`/`_congelado`;
`test_f045_*`; `CLAUDE.md`. En `sigrid_write_client.py` y `registro_models.py` el diff solo añade.

## Decisiones y desviaciones (justificadas)

1. **Guardia (DA6)**: en vez de `can / 0`, `can = CONVERT(INT, 'reajuste-descuadrado-' + CAST(ide…))`.
   Con `ANSI_WARNINGS` apagado, dividir por 0 da NULL (dejaría `can` a NULL y confirmaría); el
   error de conversión salta siempre y nombra la línea. La guardia **cuenta** las líneas en su
   estado esperado (synckey, `can` = «antes», sin enlaces, parte En registro) y falla si no son
   todas o si alguna extra nueva ya existe. M3 (e bis) lo comprueba contra la API real.
2. **INSERT de la extra nueva condicionado** (`stmt_insertar_extra`, método nuevo): mismas columnas
   que `stmt_insert_linea` (que no se toca), pero solo entra si la base ya tiene «después» y su
   synckey no existe; `MAX(ide)+1` en subconsulta (la trampa del agregado con `WHERE` falso que
   ya evita `stmts_crear_parte`). Así una base borrada a mano entre leer y escribir no deja una
   extra huérfana.
3. **sv5 decide releyendo**: tras escribir (o si la escritura lanza) relee: todo con «después» =
   hecho; nada = rechazo `ok:false` (nada escrito); a medias = excepción → 502 → sv4 lo deja
   `aplicando` con ERROR (DA6). Un 5xx/timeout de sigrid-api no se toma por rechazo.
4. **R26 antes que el estado del parte**: una línea con «después» es `ya_aplicada` aunque luego
   cerraran el parte (el reintento de un timeout no debe quedar «no editable»).
5. **R22 · otra obra**: la extra nueva exige que el parte de su base sea de la obra destino de
   `preparar` (en modo pruebas, una base real con destino 0404 no es editable).
6. **`fetch_registros_para_recurso` sin claves nuevas**: design §4 pedía añadir
   `sigrid_hmores_ide` y `obra_codigo`, pero `test_f037_r9` fija el conjunto exacto de claves y la
   spec no prevé tocarlo. Esos dos datos los rellena `guardar_repartos` desde `parte_registros`
   al crear el pendiente (mismo resultado, ningún test existente tocado).
7. **`clase_linea(reg, *, congelada)`**: recibe la congelación hecha (`_congelado`) en vez de
   calcularla: importar `recurso_conciliador` desde `reajuste_reparto` sería circular.
8. **Wiring de sv3 en `interface_adapters/api/app.py`** (no en `main_worker.py`, que reutiliza
   `build_app`). `candado_espera_s` se asigna tras construir el repositorio: pasarlo al
   constructor rompía los dobles `_RepoDoble(fabrica)` de `test_f042`/`test_f043` (lo vi en T13
   y lo corregí en el código, sin tocar esos tests).
9. **Candado (R18)** siempre que el repositorio lo tenga (también con el interruptor apagado:
   R18 no depende de él); conexión propia en `AUTOCOMMIT`; si no puede soltarlo, invalida la
   conexión. Con un repositorio sin candado (dobles antiguos) la pasada corre sin él.
   *Nota*: `conciliar_todos` lanza `TimeoutError`; en el recálculo de la cola el mensaje se
   reintenta, en la ingesta el `try` best-effort existente de `persist_parte_pipeline` lo deja en
   WARNING y la pasada siguiente recalcula todo (fichero fuera del alcance de la spec).
10. **Máquina de estados**: `decidir_grupo` devuelve también `residual` (sin ordinarias libres,
    R12). `aplicando`/`aplicado`: la fila y lo congelado no se tocan; lo libre recibe el ideal
    calculado con el estado actual. Un reparto vivo cuyo grupo desaparece entero pasa a
    `obsoleto`; uno cuyo grupo existe pero la pasada no reparte (p. ej. recurso sin hora extra)
    no se toca. Con el interruptor encendido no se emite el WARNING de medición de F-045.
11. **sv4**: errores `RepartoCambiadoError`/`RepartoPendienteError` subclases de
    `CongeladoError` (409 por el manejador global). `iniciar_aplicacion` admite `aplicando`
    (reintento R34) y conserva las reservas; las extras automáticas de lo libre (sv3 las rehace
    con id nuevo) no cuentan como «líneas nuevas». Reserva: `nextval(pg_get_serial_sequence(
    'parte_registros','id'))`; en SQLite (tests) el siguiente al mayor id.
12. **Preflight**: evalúa las líneas del día como si se aplicara (consultivo) y trae
    `repartos`; la extra nueva aún sin reserva se comprueba en sv5 con id provisional
    `-base` (synckey `partes:-N`, que no existe). **Cliente sv4**: `reajuste_*` distinguen
    rechazo (`ok:false`, nada escrito; también sin conexión) de `sin_respuesta` (timeout, error
    a mitad, 5xx).
13. **Modal**: la aprobación puede ir en dos llamadas (síncrona y cola); cada decisión viaja en
    la llamada que lleva líneas de su día, una sola vez (`decisionesPara`), porque el servidor
    rechaza (409) la decisión de un reparto ajeno a la selección. Sin decisión → alerta.

## Fase RED (trazas reales; comando `python -m pytest -q <fichero>` desde cada servicio)

RED_AQUI

## MANUAL pendiente (humano) — también en `progress/current.md`

- **M2** (lectura): la SELECT de enlaces de design §9 por `/api/sql/read` ⇒ todo 0/NULL.
- **M3** (escritura en la 0404, sv5 local con `OBRA_PRUEBAS_FORZAR=true`): (a)–(h) de design §9
  más **(e bis)**: tocar a mano `can` entre `comprobar` y `ejecutar` ⇒ error de conversión
  `reajuste-descuadrado-<ide>` y nada escrito (confirma que sigrid-api revierte el lote).
- **Despliegue sv5 → sv4 → sv3** (interruptor apagado), **M4**, encender `REPARTO_REAJUSTE`,
  **M5** y **M6** (caso real del 14/10 con «Aplicar»): comandos en `progress/current.md`.
- Aceptar los mutantes equivalentes que declare `progress/mutacion_F-046.md` (si los hay).

## Fuera de alcance

- No se borra nada en Sigrid (R47); `persist_parte_pipeline` no cambia (nota 9).
- Repartos de recursos sin código de hora extra o en grupos que la pasada no reparte: no se
  proponen (como F-045).

## Evidencias

EVIDENCIAS_AQUI
