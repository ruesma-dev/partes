# F-052 · Revalidación de la spec contra el código actual (2026-11-01)

Spec-author, en `partes-wt-f052` (rama `feature/F-052-sincronizar-con-sigrid`,
`dev` 69af0f5 fusionado en 0be3ef7). Spec escrita el 2026-10-20 y nunca
aprobada; desde entonces entraron en `dev`, entre otras, F-034, F-038, F-043,
F-046, F-047, F-049, F-050, F-053, F-054, F-055, F-056, F-060–F-062 y F-064.
Resultado: **17 cambios mecánicos** y **7 decisiones abiertas nuevas
(DA11–DA17)**; DA9 superada. Sin código tocado. Sin lecturas de Sigrid ni de
producción (M1 sigue siendo del humano).

## 1. Lo que se ha contrastado y sigue igual

sv5 (`services/partes-transfer/`):
- `sigrid_write_client.py`: `_read` (truncated ⇒ `RuntimeError`, base de
  `SIGRID_API_DATABASE`, por defecto `ruesma`), `synckey_de`,
  `LOTE_COMPROBACION` = 200, `ENLACES_HMORES` y `_expr_enlazada()`,
  `lineas_por_synckey`, `lineas_por_ide`, `partes_por_ide`,
  `estados_de_partes`. Ninguna sentencia `DELETE` (F-053).
- `interface_adapters/api/app.py`: `POST /api/registro/comprobar` (`def`, sin
  lock, 422/502 como dice la spec): el patrón de la ruta nueva sigue valiendo.
- `config/settings.py`: pydantic con `Field(alias=…)`; `SIGRID_API_TIMEOUT_S`
  60 s por defecto (encaja con el umbral de 60 s de M1).
- `LineaSigrid` (`registro_models.py`) existe; `LineaSincronizar` sigue siendo
  nueva.
sv4 (`services/partes-front/`):
- `ComprobacionSigrid.comprobar_ids(ids, *, origen, forzar)`: `origen` solo se
  registra en el log; la lista `ORIGENES_COMPROBACION` (`vista-obra`,
  `vista-trabajador`, `boton`) solo filtra la ruta `/api/sigrid/comprobar`.
  Llamarla en proceso con `origen="sincronizar"` es válido (R10).
- `registro_ids_de_obra(clave, period_key, mode)`, `registro_ids_de_trabajador`
  (todos sus meses), `_actor(request)`, `_exigir_reg_editable`,
  `_exigir_sin_recalculo(doc)`, `registros_con_reparto(ids)`,
  `aplicar_comprobacion_sigrid` (CAS por `sigrid_hmores_ide`),
  `borrar_linea`, `restore_registro` (409 `DuplicadoActivoError`, F-061),
  `transfer_client._post` / `comprobar`.
- Vistas `/obras/{obra_key}` y `/trabajadores/{worker_key}` con `period` y
  `modo`; botón «Comprobar en Sigrid» en `obra_detail.html` (l. 28) y
  `trabajador_detail.html` (l. 37): el sitio del botón nuevo existe.
- `congelacion.py` y `recurso_conciliador.py` (gemelos): no se tocan (R28).
Raíz: `test_f038_lectores_sigrid.py` (lista cerrada: el cliente de sv5 ya
está), `test_f024_borrado_no_congela_gemelos.py`, `test_f010_orm_models_gemelos.py`.
Documentos: `azure-apps/partes.md` describe `/api/registro/comprobar` (l. 138
y 763): ahí irá el endpoint nuevo; `sigrid_api.md` §6.4 y §6.7 siguen.

## 2. Cambios mecánicos aplicados (17)

Lista completa en `tasks.md` «Revalidación 2026-11-01». Los de más peso:
1. F-050 ya está en `dev` (cabecera de requirements, T1).
2. R15: obra sin `obra_ide` = `cod-`, `nom-`, `sin-obra` (`obra_key_for_registro`).
3. R21: `_exigir_sin_recalculo` cubre ya el parte nuevo de F-047.
4. R24: el 409 de `restore_registro` (F-061) vuelve como descartado.
5. `_validar_ambito` es un cierre de `app.py` que exige 1–5000 ids y textos de
   aprobación: sirve a `/aplicar`, no a `/api/sincronizar` (sin ids).
6. `period_bounds(año, mes, modo)` + `parse_period_key`.
7. `enlazada` con `_expr_enlazada()` (la comparten reajuste, choques y racha).
8. `_read` sin `max_rows` por llamada: se añade opcional; el guardián F-038
   no cambia (`pagina + 1` es una operación, R13 de F-038).
9. Motivo de recálculo en `tests/test_f052_contrato_motivos.py` (precedente
   F-049) en vez de la parametrización de F-042.
10. Semántica nueva = 22 (la 18 es F-054).
11. H1 resuelto por F-053 (también `MOTIVO_LINEA_REGISTRADA`); H2 por F-038.
12. DA9 superada.

## 3. Decisiones abiertas nuevas (design §8)

- **DA11 · lectura paginada (F-038)**. sigrid-api sirve 500.000 filas; sv3 y
  sv4 paginan con `PAGINA_FILAS` = 5000 y `max_rows = PAGINA_FILAS + 1`. La
  spec ponía `SINCRONIZAR_PAGINA` = 1000 configurable. Rec. **A**: constante
  `PAGINA_FILAS` = 5000 también en sv5; sigue el tope `SINCRONIZAR_MAX_LINEAS`.
- **DA12 · synckeys `partes:<id>:ciz` (F-062) y `partes:franquicia:<id>`
  (F-056)**. Empiezan por `partes:`; `registro_de_synckey` (sv5,
  `racha_ciz.py`) devuelve None para las dos. Con la spec, el CIZ hermano
  saldría `solo_sigrid_nuestra` (con `restaurar`) o mal casado, y la línea de
  franquicia sin `registro_id`. Rec. **A**: orígenes `ciz` y `franquicia` en
  sv5 y una clase informativa `solo_sigrid_auxiliar` en sv4 (12 clases).
- **DA13 · líneas a 0 fuera del portal (F-053)**. Las ajenas/manuales pisadas
  ya no desaparecen: quedan `can = 0`. Rec. **A**: marca `a_cero` (no `CI*`),
  ocultas por defecto con contador.
- **DA14 · `omitido` sin pareja según motivo**. Motivos de sv5 hoy:
  `parte_no_abierto`, `pisada_no_anulada` (sv5 pide reaprobar),
  `fecha_no_valida` (F-055), `fin_movido`/`intermedio`/`ciz_en_parte_cerrado`
  (F-060), `incidencia_en_sigrid`, `linea_enlazada` (F-053), `parte_cerrado`
  (F-031). Rec. **A**: las dos reaprobables ⇒ `pendiente`; el resto
  `no_viaja` con nota.
- **DA15 · `traer_de_sigrid` frente a F-046/F-049**. La pasada de sv3 reparte
  por (recurso, día) entre obras: cambiar una congelada mueve el residual de
  otras obras (lo que motivó el pedido compartido de F-049). Y el registro
  bloquea con `ESTADOS_BLOQUEAN` (incluye `rechazado`), no solo los dos de R21.
  Rec. **A**: `_pedir_recalculo_compartido` + `ESTADOS_BLOQUEAN`.
- **DA16 · parte reemplazado por la reingesta de sv3** (`deleted_by` NULL):
  sus `partes:<id>` en Sigrid saldrían `no_existe`. Rec. **A**: `donde =
  parte_reemplazado`, informativo. El parte retirado de F-061 no necesita
  valor propio: sus líneas ya están en la papelera.
- **DA17 · partir**. Con DA11–DA16, design queda en 225/250 y requirements en
  128/150, con 30 requisitos, 12 clases, panel JS y una escritura sobre líneas
  congeladas en rigor crítico. Rec. **A**: F-052 = lectura + comparación +
  panel informativo (DA1 = B, rigor estándar); las acciones hacia el portal
  (R16–R25, DA3, DA15) en una feature crítica nueva, después de M2.

## 4. DA1–DA10 revisadas

- DA1: sigue; con DA17-A pasa a B en esta feature y A en la siguiente.
- DA2, DA4, DA5, DA6, DA7, DA10: siguen sin cambios (F-024 sigue siendo
  dueña del synckey en sv5; F-018 no ha llegado).
- DA3: sigue (solo horas); depende de DA17.
- DA8: crítico sigue valiendo para las acciones; con DA17-A la lectura sería
  estándar.
- DA9: **superada** (F-050 y F-049 en `dev`; el humano lanzó F-052).
- Clases de R8: las líneas anuladas por F-053 caben en `anulada_en_sigrid`
  (cambio mecánico de §3); partes cerrados de F-034 no cambian la
  clasificación (`parte_est` ya viaja, R2) y solo importarán a la feature que
  escriba en Sigrid; F-055 entra en DA14; `reparto_pendiente` y partes en
  espera en R21/DA15; la franquicia en DA12.

## 5. Verificaciones

- M1 no se ha hecho (solo lectura en Sigrid, la deja la spec al humano antes
  de implementar): dimensiona el tope y confirma DA11.
- Topes y portero: `bash harness/init.sh` en verde en el worktree.
