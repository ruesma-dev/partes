<!-- specs/F-046-reajuste-en-sigrid-al-aprobar/design.md -->
# F-046 · Reajuste en Sigrid al aprobar — Diseño

## 1. Encaje, límite de servicio y rigor

- **Dependencia**: F-045 fusionada en `dev` (`reparto_ponderado.py`: `repartir_dia`,
  `diferencias_ideal`, `LineaDia`, `Ajuste`). La rama se rebasa sobre ese `dev` antes de T1.
- **sv3** calcula la propuesta (el reparto solo lo calcula sv3) y la lleva a `partes` (dueño de
  `apply_extras_splits`). **sv5**, único que escribe en Sigrid, estrena el `UPDATE hmores`.
  **sv4** enseña el aviso, recoge la decisión y orquesta (HTTP síncrono a sv5, como pisar:
  destructivo, nunca por cola). Nada sale del límite de los servicios.
- **Esquema**: tabla `reparto_pendiente` en las dos copias de `orm_models.py` (ya en la lista
  cerrada); sus estados son constantes del propio ORM, así que no nace ningún gemelo nuevo y
  **la lista cerrada de `CLAUDE.md` no crece** (DA14).
- **Rigor crítico**: horas registradas en el ERP de producción (nómina, coste de obra), estado
  compartido en la base `partes` y concurrencia entre tres servicios.

## 2. La propuesta de F-045 §8 contra el código (2026-10-14)

Se mantienen DA11–DA14 de F-045, con estos hallazgos:

- **H1** · La extra nueva de una base registrada sin extra (R7) no existe en `partes` cuando
  sv5 necesita su synckey `partes:<registro_id>` ⇒ reserva por secuencia (DA5).
- **H2** · `sql/write` admite `UPDATE` con `WHERE` obligatorio y lote = una transacción
  (`sigrid_api.md` §7.3, §8.2); el valor real de `ALLOWED_WRITE_PREFIXES` no consta ⇒ M1.
- **H3** · §7.7: `user_rw` sin `DELETE` general ⇒ una línea que queda a 0 se actualiza (DA7).
- **H4** · `escribir` trocea en lotes de `SIGRID_MAX_STATEMENTS` (15), cada uno su transacción
  ⇒ el reajuste debe caber en uno (R27) y lleva guardia (DA6).
- **H5** · `hmores` enlaza con albarán, factura, dedicación y nómina (`dvaproide`, `dvfproide`,
  `hdereside`, `emprccide`, `empdpreide`, `empabside`) ⇒ enlazada = no editable (DA17).
- **H6** · `tot = round(can × pre, 2)` como `stmt_insert_linea`; el asiento (Σ `tot` por
  `caaide`) solo nace al Imputar y solo se editan partes En registro ⇒ coherente.
- **H7** · «Mantener» tras aplicar el ideal a lo libre exige una pasada antes de registrar, y
  aprobar el documento congelaría el ideal sin decidir (DA8, DA13).
- **H8** · sv3 nuevo con sv4 viejo registraría el ideal sin aviso ⇒ interruptor (DA2).
  **H9** · `LineaDia` de F-045 no lleva la pareja ⇒ campos con defecto (§4).

## 3. Flujo y estados (`reparto_pendiente.estado`)

```
sv3 ─► pendiente ─Aplicar(sv4,CAS)─► aplicando ─sv5 ok─► aplicado ─sv3─► materializado
          │                              └─ sv5 ko ─► pendiente (+error); timeout: sigue, se reintenta
          └─Mantener(sv4,CAS)─► rechazado ─sv3 residual─► mantenido
pendiente|rechazado|mantenido|materializado ─firma cambia (sv3)─► obsoleto (+ nuevo pendiente)
```

**sv3**, interruptor encendido, por grupo y bajo el candado (DA15): `aplicado` ⇒ materializar
(R15–R17) antes de repartir; `aplicando` ⇒ ni la fila ni lo congelado se tocan y lo libre se
reparte como la pasada anterior; `rechazado`/`mantenido` con firma vigente ⇒ residual y
`mantenido`; si no ⇒ `proponer_dia`: con cambios y ≥ 1 ordinaria libre, ajustes del ideal +
`pendiente`; sin cambios, residual y el reparto vivo pasa a `obsoleto`.

**Aplicar (sv4)**, por reparto y antes de registrar el lote: (1) transacción con `UPDATE …
SET estado='aplicando' WHERE id=? AND estado='pendiente'`, tras comprobar que cada línea
sigue con horas y estado «antes», que el grupo tiene los mismos ids activos y que ningún
documento suyo está en espera (F-043); reserva `nextval` de las extras nuevas en `resultado`;
(2) sv5 `/api/reajuste/ejecutar` con las `registrado` y las nuevas de base registrada (las
solo aprobadas no van, DA11); (3) `aplicado` + resultado, o `pendiente` + error; (4)
`_pedir_recalculo_seguido` (motivo `reajuste_reparto`) de sus documentos; (5) registro del lote.

## 4. Ficheros

### sv3 (`services/partes-persistencia`)

- **Modificar `application/services/reparto_ponderado.py`** (puro): `LineaDia` gana, con
  defecto neutro, `pareja: Hashable | None`, `extra_auto: bool` y `reajustable: bool` (si
  F-045 trae un equivalente, se usa y se anota); `CambioCongelada(registro_id: int | None,
  base_registro_id: int, tipo: str, antes: float, despues: float)` y `PropuestaDia(cuadra,
  paso, ajustes: tuple[Ajuste, ...], cambios: tuple[CambioCongelada, ...])`, frozen;
  `proponer_dia(lineas, jornada) -> PropuestaDia` (R1–R4): duras fijas, reajustables con peso
  `horas_orig or horas` y extra de pareja = trabajado − cuota, sobre `repartir`/`elegir_paso`.
  `repartir_dia` y `diferencias_ideal` no cambian.
- **Crear `application/services/reajuste_reparto.py`** (puro): `clase_linea(reg) -> str`
  (`libre | reajustable | dura`); `firma_grupo(regs) -> str` (sha256 de las tuplas ordenadas
  `registro_id, tipo_hora, extra_auto, horas, horas_orig, sigrid_estado, doc_approved`);
  `decidir_grupo(fila, firma, hay_libres) -> str` (`materializar | congelar |
  residual_mantener | proponer`, la máquina de §3); `cambios_a_json` / `json_a_cambios`.
- **Modificar `application/services/recurso_conciliador.py`**: constructor con `reajuste:
  bool = False`; `conciliar_todos` corre dentro de `self._repository.candado_pasada()`, llama
  a `materializar_repartos()` tras `revert_extras_auto` y a `guardar_repartos(...)` al final,
  con los contadores de R19. `_reclasificar_extras_jornada`: con el interruptor,
  `decidir_grupo` + `proponer_dia`; apagado, el camino de F-045 intacto (R10).
- **Modificar `infrastructure/database/sqlalchemy_parte_repository.py`**: `candado_pasada()`
  (conexión propia, `pg_try_advisory_lock(CLAVE)` con backoff hasta `candado_espera_s`, si no
  `TimeoutError`; libera en `finally`; no-op fuera de PostgreSQL); `repartos_vigentes() ->
  dict[(recurso, fecha), dict]`; `materializar_repartos() -> dict` (R15–R17: CAS a
  `materializado` en la transacción que escribe; R16 ⇒ nada y ERROR); `guardar_repartos(
  propuestas, mantenidos) -> dict` (`WHERE estado IN (...)`, nunca `aplicando`/`aplicado`);
  `fetch_registros_para_recurso` añade `horas_orig`, `extra_auto`, `clave_pareja`,
  `sigrid_hmores_ide` y `obra_codigo` (sin duplicar lo que añada F-045); `apply_extras_splits`
  admite `id` y `sigrid` opcionales por split (R15, R17).
- **`config/settings.py`**: `reparto_reajuste` (`REPARTO_REAJUSTE`, `False`) y
  `candado_espera_s` (`CANDADO_CONCILIAR_ESPERA_S`, 300). **`main_worker.py`**: pasa
  `reajuste=`. **`tests/dobles.py`**: `RepositorioFake` con los métodos nuevos.

### sv5 (`services/partes-transfer`)

- **Crear `application/services/reajuste_lineas.py`** (puro): `veredicto_existente(linea,
  est_parte, antes, despues, est_registro)` y `veredicto_nueva(...)` → `VeredictoReajuste`
  (R21, R22, R26); `MOTIVO_*` literales; `TOL = 0.001`.
- **Crear `application/pipelines/reajuste_pipeline.py`**: `ReajustePipeline(cliente,
  settings, registro: RegistroPipeline)`; `comprobar(lineas)` sin lock; `ejecutar(lineas,
  usuario)` con `with registro.lock:` relee, decide, arma guardia + `UPDATE` + `INSERT`,
  `escribir_lote` y relee los ides nuevos. Las nuevas pasan por `registro.preparar(...)` (obra
  destino, modo pruebas, reglas, cuenta F-021) y van al `hmoide` de su base.
- **`domain/models/registro_models.py`**: `OpReajuste`, `VeredictoReajuste`,
  `ResultadoReajuste`; `LineaSigrid` gana `pre`, `hmoide`, `enlazada` con defecto.
- **`infrastructure/sigrid/sigrid_write_client.py`** (solo métodos nuevos):
  `lineas_para_reajuste(claves)`, `estados_de_partes(hmoides)`, `stmt_guardia_reajuste(lineas)`,
  `stmt_actualizar_linea(*, ide, synckey, antes, despues, est_registro)` y
  `escribir_lote(statements) -> list[int]` (filas por sentencia; `ValueError` si no cabe en uno).
- **`interface_adapters/api/app.py`**: `LineaReajusteIn`, `ReajusteIn` (1–50),
  `POST /api/reajuste/comprobar` (`def`) y `/api/reajuste/ejecutar`; `build_app(...,
  reajuste=None)`. **`main.py`**: `ReajustePipeline` sobre el pipeline compartido (un lock).

### sv4 (`services/partes-front`)

- **Crear `application/services/reparto_aviso.py`** (puro): `bloque_repartos(filas,
  veredictos)` (R30, R31), `excluidas_por_reparto(filas, decisiones) -> dict[int, str]` (R32),
  `payload_reajuste(fila, reservas) -> dict` (R33).
- **`infrastructure/database/parte_repository.py`**: `repartos_de_registros(ids)`,
  `iniciar_aplicacion(reparto_id, *, actor)` (CAS + comprobaciones + `nextval`; si no,
  `RepartoCambiadoError` → 409), `cerrar_aplicacion(reparto_id, *, ok, resultado, error,
  actor)`, `rechazar_reparto(reparto_id, *, actor)`, `registros_con_reparto(ids)`;
  `lineas_para_registro(..., repartos_decididos=frozenset())` excluye `reparto_pendiente`;
  `approve_document` lanza `RepartoPendienteError` (R36).
- **`infrastructure/transfer/transfer_client.py`**: `reajuste_comprobar`, `reajuste_ejecutar`.
  **`infrastructure/persistencia/recalculo_publisher.py`**: `MOTIVO_REAJUSTE = "reajuste_reparto"`.
- **`interface_adapters/web/app.py`**: preflight con `repartos`; `ejecutar`/`encolar` procesan
  `repartos` ANTES de los grupos; `approve_document` captura `RepartoPendienteError`
  (redirección con motivo); vistas con `registros_con_reparto`; actor solo de `_actor(request)`.
- **`static/app.js`, `static/styles.css`** y plantillas de detalle de obra y de trabajador:
  aviso en el modal (antes → después, motivo), «Aplicar» / «Mantener lo registrado» y
  `data-reparto="pendiente"`.

### Raíz, documentación y lo que NO se toca

- `tests/test_f010_orm_models_gemelos.py` y `tests/test_f015_r29_guardian_cinco_tablas.py`:
  `TABLAS` a siete y `COLUMNAS_REPARTO_PENDIENTE` literal (únicas enmiendas). Docs: R42.
- **NO**: `congelacion.py`, `esta_congelado`/`ESTADOS_CONGELADOS`, `pareja_extra.py`,
  `jornada_resolver.py` (sv3 y sv4); `estado_parte.py`, `cuenta_analitica.py`,
  `stmts_crear_parte` (copias literales en `porcentajes`); `stmt_insert_linea`,
  `stmt_borrar_linea`, `lineas_por_synckey`, `RegistroPipeline`; contrato de `q-transfer`;
  `despacho.py`, `mensajes.py`; `undo_log`; sv1, sv2, `infra/`.

## 5. SQL (base `partes`, sin fichero `NN_*.sql`)

La crean `create_all` y `ddl_complementario()` al arrancar sv3 y sv4; toda `NOT NULL` lleva
`server_default` (como `dedicacion_bandeja`); sin nombres ni DNIs. `reparto_pendiente`:
`id` Integer PK; `recurso_ide`, `fecha_int` Integer NOT NULL `'0'` (índice
`ix_reparto_pendiente_grupo`); `estado` String(16) NOT NULL `'pendiente'` (índice
`ix_reparto_pendiente_estado`); `firma` String(64) NOT NULL `''`; `cambios` Text NOT NULL
`'{}'` (JSON `{ids_grupo, cambios[]}`, cada cambio con `registro_id`, `base_registro_id`,
`document_id`, `obra_ide`, `obra_codigo`, `tipo`, `extra_auto`, `sigrid_estado`, `hmores_ide`,
`antes`, `despues` y, si es nueva, `hora_ext`); `resultado` Text (reservas y respuesta de sv5);
`error` String(255); `decision` String(16), `decidido_por` String(120), `decidido_at_utc`;
`creado_at_utc`, `actualizado_at_utc` String(64) NOT NULL `''`; `materializado_at_utc`.
Constantes en el ORM: `ESTADOS_REPARTO` y una por estado.

## 6. Decisiones (DA, con recomendación)

- **DA1 · Una feature en tres bloques** (sv5 T2–T7 → sv3+ORM T8–T13 → sv4 T14–T19), con el
  interruptor apagado. Alternativa: F-046 (sv5, verificable sola en 0404) + F-047 (propuesta y
  decisión). *Recomendado una* (contrato y tabla van juntos); si falta contexto, cortar tras T7.
- **DA2 · Interruptor `REPARTO_REAJUSTE` en sv3, apagado** = F-045: rollback y despliegue
  sv5 → sv4 → sv3, encendido tras M3. *Recomendado.*
- **DA3 · Tabla nueva**, no columnas en `parte_registros` (no caben las extras nuevas; sus 56
  columnas están vigiladas). *Recomendado* (F-045 DA11).
- **DA4 · Materializa sv3** en su pasada: dueño del split, sin copiar lógica en sv4; la ventana
  hasta la pasada la pinta F-043 como espera. Alternativa: sv4 tras sv5 (inmediato, duplica la
  persistencia del split). *Recomendado sv3.*
- **DA5 · Reserva `nextval`** por sv4 al iniciar Aplicar, guardada para reintentos.
  Descartadas: fila provisional (visible; borrado físico prohibido) y synckey
  `partes:<base>:extra` (rompe synckey = `registro_id`, F-024). *Recomendado.*
- **DA6 · Atomicidad**: lote único con **sentencia guardia** primera (`UPDATE hmores SET can =
  can / 0 WHERE ide IN (…) AND NOT (<condiciones>)`): si alguna condición falla, error y la API
  revierte el lote; además `WHERE` optimista y `affected_rows` = 1 por sentencia. Si M3e la
  rechaza: sin guardia, y un descuadre queda `aplicando` con ERROR para comprobar y
  reintentar. *Recomendado guardia.*
- **DA7 · A 0 se actualiza, no se borra** (H3; F-024 sigue viendo la línea). *Recomendado.*
- **DA8 · Pendiente = lo libre con el ideal** (F-045 §8): «Aplicar» registra en el mismo
  clic. Coste: el día sobrecuenta en `partes` hasta decidir y «Mantener» necesita una pasada
  antes de registrar (dos pasos, con la espera de F-043). Alternativa: residual hasta decidir
  (sv4 tendría que escribir el ideal: copia del split). *Recomendado ideal.*
- **DA9 · Todo o nada por reparto** (recurso y día): una línea no editable deja solo
  «Mantener»; lo parcial exigiría recalcular en sv4. *Recomendado.*
- **DA10 · Cerrado o imputado, encolado, dedicación: no se editan** (F-045 DA13);
  regularizar en el complementario rompe synckey = `registro_id`. *Recomendado.*
- **DA11 · Aprobadas no registradas**: mismo aviso, sin sv5 (F-045 DA14). *Recomendado.*
- **DA12 · Solo propone con ≥ 1 ordinaria libre** (R12): «al aprobar el segundo», sin
  repropuestas perpetuas cuando todo está congelado. *Recomendado.*
- **DA13 · Aprobar el documento se bloquea** con reparto vivo (R36); alternativa: aviso
  también ahí (más UI). *Recomendado bloquear.*
- **DA14 · `CLAUDE.md` no cambia**: sin código gemelo nuevo y la regla de congelación igual;
  R15 es una escritura acotada de sv3. Si el humano la ve como parte de la regla, una frase en
  la lista cerrada. *Recomendado no tocar.*
- **DA15 · Candado consultivo de sesión** (`pg_try_advisory_lock`, clave constante, ≤ 300 s):
  PostgreSQL lo etiqueta con la base, no ve a otros proyectos del servidor compartido ni toca
  nada de servidor. sv4↔sv3 por CAS sobre `estado`. *Recomendado.*
- **DA16 · Sin deshacer**: fuera de `undo_log` (no hay deshacer en Sigrid); rastro en la fila
  (decisión, actor, sv5, materialización) y en los logs. *Recomendado.*
- **DA17 · Enlazada = no editable** (H5), lista conservadora; M2 confirma que nuestras líneas
  los tienen a 0. *Recomendado.*

## 7. Riesgos

- **R-a · Escritura nueva en producción.** Mitigan: interruptor, `comprobar` previo, guardia,
  CAS, M3 en 0404 antes de encender y una decisión humana por reajuste.
- **R-b · `ALLOWED_WRITE_PREFIXES` sin `UPDATE`**: todo «no editable»; abrirlo es
  configuración de **sigrid-api** (otro proyecto) y lo decide el humano.
- **R-c · Sobrecuenta temporal** mientras está pendiente (DA8). **R-d · sv3 caído tras sv5
  ok**: queda `aplicado` y se materializa en la pasada siguiente; R16 protege.
- **R-e · Despliegue sv5 → sv4 → sv3** (distinto del habitual) y encender después.
- **R-f · Imputación entre comprobar y ejecutar**: el `WHERE` exige En registro.
- **R-g · `porcentajes`**: ni alta ni copias literales; solo líneas con nuestra synckey.
- **R-h · Tamaño** (DA1); **sv4 a dos réplicas**: CAS en BBDD, nunca un lock de proceso.

## 8. Tests (sin red ni BBDD; sintéticos, sin nombres ni DNIs)

sv3: `test_f046_proponer_dia.py` (R1–R9; propiedades: suma = J, sin duras = F-045),
`test_f046_reajuste_reparto.py` (firma, clases, estados), `test_f046_conciliar.py` (R10–R19
con `RepositorioFake`; R10 = tests de F-045 intactos), `test_f046_candado.py` (R18, conexión
falsa). sv5: `test_f046_reajuste_lineas.py` (R21, R22, R26), `test_f046_reajuste_pipeline.py`
(R20, R23–R29, cliente falso), `test_f046_cliente_reajuste.py` (SQL), `…api_reajuste.py`. sv4:
`test_f046_reparto_aviso.py` (R30–R32), `test_f046_aplicar.py` (R33–R35, R38; SQLite de
`dobles.py`, CAS con dos llamadas), `test_f046_aprobar_documento.py` (R36),
`test_f046_marcas.py` (R37); `node --check`. Raíz: guardianes de tablas (R39), F-024 y F-042
intactos (R40) y `test_f046_contrato_reajuste.py` (lo que sv4 manda lo acepta `ReajusteIn`).
Cualquier otro test existente que falle ⇒ `blocked`.

## 9. Verificación MANUAL (humano)

- **M1** (lectura): `az functionapp config appsettings list -g rg-sigrid-dev-data-api -n
  func-sigridapi-dev-huyke --query "[?name=='ALLOWED_WRITE_PREFIXES'].value" -o tsv` ⇒ `UPDATE`.
- **M2** (lectura, `/api/sql/read`): `SELECT TOP 50 ide, dvaproide, dvfproide, hdereside,
  emprccide, empdpreide, empabside FROM hmores WHERE synckey LIKE 'partes:%' ORDER BY ide DESC` ⇒ 0/NULL.
- **M3** (escritura, sv5 local con `OBRA_PRUEBAS_FORZAR=true`, `registro_id` sintéticos
  ≥ 990000001, recurso de pruebas del script): (a) `/api/registro/ejecutar` 8 h y extra −4;
  (b) `comprobar` 8 → 2,5 y −4 → 1,5 ⇒ editables; (c) `ejecutar` ⇒ `can` 2,5/1,5 y `tot` =
  `can × pre` (`prueba_escritura_sigrid.py verificar`); (d) repetir ⇒ `ya_aplicada`; (e) una
  línea con «antes» falso y otra buena ⇒ nada escrito; (f) base 8 sin extra ⇒ 5,5 + extra
  nueva 2,5 con `PRUEBA-IA`; (g) extra a 0; (h) `limpiar`, `limpiar --ejecutar` y `verificar`
  ⇒ sin `PRUEBA-IA` (ANO/MES del script = mes de la prueba).
- **M4** tras desplegar sv5 → sv4 → sv3 (apagado): `SELECT count(*) FROM reparto_pendiente` ⇒ 0.
- **M5** con `REPARTO_REAJUSTE=true`: `SELECT estado, count(*) FROM reparto_pendiente GROUP
  BY estado`; Log Analytics de sv3 con `Log_s has 'reparto'`.
- **M6** (escritura en producción; la autoriza y la hace el humano en el portal): el 14/10
  (0678/0704) con «Aplicar» ⇒ R6 en Sigrid y en `partes`.
