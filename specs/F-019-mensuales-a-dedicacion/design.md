<!-- specs/F-019-mensuales-a-dedicacion/design.md -->
# F-019 · Diseño técnico

Requisitos en `requirements.md`. Rama `feature/F-019-mensuales-a-dedicacion`
(desde `dev` `b9b3b81`). Rigor **crítico**: cambia lo que se escribe en
Sigrid en producción (las incidencias de los mensuales dejan de ir, R1 de
`reglas_registro.py`). **DA1–DA8 aprobadas por el humano el 2026-10-02** (§8).

## 1. Servicios que toca y por qué (límite de servicio)

- **sv5 (partes-transfer)**: decide el destino de cada línea (DA7). Ya carga
  todos los códigos `reshor` del recurso al aprobar (`horas_de_recursos`,
  sin filtro de prefijo), así que el criterio `M*` no exige ninguna lectura
  nueva de Sigrid. Sigue **sin BBDD**: devuelve la decisión en su resultado.
- **sv4 (partes-front)**: escribe la bandeja al volcar ese resultado (DA2),
  pinta el estado, excluye y retira. Ya es quien escribe `sigrid_*`.
- **sv3 (partes-persistencia)**: solo la copia gemela de `orm_models.py` y
  `ESTADOS_CONGELADOS` (que la reconciliación no recalcule una línea ya
  publicada). Ninguna lógica nueva.
- **sv1, sv2: no.** **dedicación (repo `porcentajes`)**: fuera (§9).
- **Duplicación**: ninguna nueva. La regla `M*` vive solo en sv5; la clase de
  incidencia solo en `config/incidencias.yaml` de sv4. La copia de ORM y la
  congelación ya estaban en la lista cerrada de `CLAUDE.md`.
- **Límite de microservicio**: partes publica el dato del día y no calcula
  porcentajes, no conoce los periodos de dedicación ni lee su base.

## 2. Encaje y flujo

```
sv4 aprobar ──(q-transfer o HTTP, F-002/F-022)──▶ sv5 preparar
   ReglasRegistro: omitir | escribir | dedicacion (interruptor + M*)
   _evaluar paso 6: synckey ya en Sigrid ⇒ ya_registrado (R5)
sv5 resultado {escritas, omitidas, ya_registradas, dedicacion, ...}
   ──(q-transfer-result o respuesta HTTP)──▶ sv4 aplicar_resultado
       una transacción: sigrid_estado='dedicacion' + upsert dedicacion_bandeja
dedicacion-api ──(SELECT, rol de dedicación, solo esa tabla)──▶ base partes
```

Cada proyecto escribe solo en su base; no se abre ruta de red: dedicación
ya habla con `psql-albaranes-rs9k2` y solo abre una segunda conexión a otra
base del mismo servidor.

## 3. Ficheros a crear

| Ruta | Qué |
|---|---|
| `infra/sql/01_dedicacion_lectura.sql` | R25: `\set ON_ERROR_STOP on`; `GRANT CONNECT ON DATABASE partes`, `GRANT USAGE ON SCHEMA public`, `GRANT SELECT ON TABLE public.dedicacion_bandeja` a `:"rol"`; después `has_table_privilege` sobre la bandeja (true) y sobre `parte_registros` (false), `has_schema_privilege(...,'CREATE')` (debe ser false; si sale true se avisa, no se revoca) y `SELECT version()`. Cabecera con el comando exacto (§10, M2) |
| `services/partes-transfer/tests/test_f019_reglas.py` | R1 (caracterización), R2–R4 |
| `services/partes-transfer/tests/test_f019_pipeline.py` | R5–R8 con doble de `SigridWriteClient` |
| `services/partes-front/tests/test_f019_bandeja.py` | R9–R14 sobre SQLite |
| `services/partes-front/tests/test_f019_portal.py` | R15–R24 con `TestClient` y HTML |
| `services/partes-persistencia/tests/test_f019_congelado.py` | R15 en sv3 |
| `tests/test_f019_sql_lectura.py` | R26/R27: análisis estático del `.sql` y búsqueda de `GRANT` en `services/` |

## 4. Ficheros a modificar

**sv5**
- `config/settings.py`: `mensuales_a_dedicacion: bool = Field(False,
  alias="MENSUALES_A_DEDICACION")`.
- `domain/models/registro_models.py`: `HoraRecurso.es_mensual` (`cod`
  empieza por `M`); `AccionLinea.codigo_mes: Optional[str]`;
  `accion` admite `dedicacion`; `Preflight.n_dedicacion`;
  `ResultadoRegistro.dedicacion: list[dict]`.
- `application/services/reglas_registro.py`: constructor con
  `mensuales_a_dedicacion: bool = False`; en `decidir`, tras la omisión
  previa, el tipo no reconocido (solo no incidencias), sin recurso y sin
  horas (solo no incidencias) → `_decidir_mensual` (R2/R3); si devuelve
  `None`, sigue el flujo de hoy. Docstring: regla R0 nueva y R1–R3 «con el
  interruptor apagado».
- `application/pipelines/registro_pipeline.py`: pasar el ajuste a
  `ReglasRegistro`; paso 6 también para `dedicacion` (R5); `res.dedicacion`
  en `_registrar_bajo_lock` (R8). `_resolver_cuentas` ya ignora lo que no es
  `escribir` (R6).
- `interface_adapters/resultado_json.py`: clave `dedicacion`.
- `interface_adapters/queue/transfer_consumer.py`: `"dedicacion": []` en
  `_resultado_fallido`.
- `interface_adapters/api/app.py`: `resumen.dedicacion` en el preflight.

**sv4**
- `infrastructure/database/orm_models.py` (y la copia de sv3, byte a byte):
  `DedicacionBandejaOrm` (§5).
- `application/services/congelacion.py`: `ESTADO_DEDICACION`, en
  `ESTADOS_CONGELANTES`; `MOTIVO_LINEA_DEDICACION` y
  `MOTIVO_DOC_DEDICACION` (prioridad: encolado > registrado > dedicacion >
  aprobado); `vive_fuera(estado)` = registrado o dedicacion, usada por el
  bloqueo de borrado definitivo (R16) en lugar de `es_registrado`.
- `infrastructure/database/parte_repository.py`: `lineas_para_registro`
  excluye `dedicacion` (R17); `marcar_registros_sigrid(..., dedicacion=,
  prueba=, incidencias=)` con `_upsert_bandeja` (R9–R14); `retirar_de_
  dedicacion(ids, actor)` (R21/R22); papelera y hard-delete con `vive_fuera`.
- `infrastructure/transfer/resultado_sigrid.py`: `aplicar_resultado` pasa
  `dedicacion`, `forzada_pruebas` y la tabla de incidencias (parámetro
  opcional; sin ella, clase nula).
- `interface_adapters/workers/resultado_consumer.py` y `main.py`: la tabla
  de incidencias llega al consumidor (`construir_tabla_incidencias`).
- `interface_adapters/web/app.py`: `_trazar` con la tabla;
  `_motivo_sin_lineas` con `dedicacion`; ruta `POST /api/dedicacion/
  retirar` (reutiliza `_validar_ambito`, `_actor`).
- `application/services/reparto_obras.py`: `_estado` → `("dedicacion",
  motivo)` para la acción `dedicacion` (R18), fuera de `ESTADOS_ESCRITURA`.
- `templates/obra_detail.html`, `templates/trabajador_detail.html`: rama
  `dedicacion` (R19). `static/app.js`: botón «Retirar» (con `ambito`), etiqueta
  del listado y de `excluidas.dedicacion` (con `esc()`); `static/styles.css`
  si hace falta una clase.

**sv3**: `orm_models.py` (gemelo) y `ESTADOS_CONGELADOS` en
`application/services/recurso_conciliador.py`.

**Raíz**: `tests/test_f010_orm_models_gemelos.py` (`TABLAS` con
`dedicacion_bandeja` y su lista literal); `tests/test_f015_r29_guardian_
cinco_tablas.py` (asserción a seis tablas; se cambia la asserción, no se
relaja); `tests/test_f024_borrado_no_congela_gemelos.py` (`dedicacion` en
`ESTADOS`). Docs: `docs/ARCHITECTURE.md`, `docs/referencia/partes-proyecto.md`.
**Fuera del repo**: `azure-apps/partes.md` (R31), commit local en ese repo.

**Ficheros que NO se tocan**: sv1 y sv2 enteros; en sv5
`sigrid_write_client.py` (R5 usa `lineas_por_synckey`, que ya existe),
`cuenta_analitica.py`, `coherencia_recurso.py`, `comprobacion_lineas.py`
(F-024 sigue mirando solo `registrado`); en sv4 `incidencias_horas.py`,
`config/incidencias.yaml`, `jornada_resolver.py`, `_rol_incidencia` y el
cálculo de extras; en sv3 todo salvo lo dicho; `infra/*.ps1` (el
interruptor nace apagado por defecto en el código y se enciende con
`az containerapp update`, M3).

## 5. Esquema: `dedicacion_bandeja` (sv3 y sv4, base `partes`, `public`)

Tabla nueva: la crea `create_all` al arrancar sv3 o sv4; el DDL
complementario no tiene nada que añadir. Sin migración de datos. Sin FK a
`parte_registros` a propósito: es un contrato publicado y la retirada es
explícita (R16 impide borrar la línea mientras esté publicada).

| Columna | Tipo | Nota |
|---|---|---|
| `registro_id` | Integer PK | = `parte_registros.id`; una fila por línea |
| `version` | Integer NOT NULL | 1 al crear; +1 en cada cambio (R11–R13, R21) |
| `vigente` | Boolean NOT NULL | false = retirada |
| `recurso_ide` | Integer NOT NULL | `res.ide`: la clave del trabajador en dedicación |
| `codigo_mes` | String(16) NOT NULL | el `M*` del recurso |
| `fecha_int`, `anio`, `mes` | Integer NOT NULL | fecha real de trabajo |
| `obra_ide`, `obra_codigo`, `obra_empresa` | Integer / String(64) / Integer | de la línea y de `parte_documents.empresa` (F-023) |
| `partida_ide`, `partida_cod` | Integer / String(64) | nulos si no casó |
| `tipo` | String(16) NOT NULL | `normal` / `extra` / `incidencia` |
| `horas` | Float | tal cual |
| `incidencia_codigo`, `incidencia_clase` | String(8) / String(16) | clase `dia_completo`/`parcial` o nula |
| `prueba` | Boolean NOT NULL | `forzada_pruebas` del resultado |
| `enviado_por`, `enviado_at_utc` | String(255) / String(64) | último alta |
| `retirado_por`, `retirado_at_utc` | String(255) / String(64) | última retirada; nulos si vigente |
| `actualizado_at_utc` | String(64) NOT NULL | cambia con `version` |

Índice `ix_dedicacion_bandeja_periodo (anio, mes)`. «Mismo contenido» (R12) =
todas las columnas de datos iguales (`recurso_ide` … `prueba`). Volumen:
miles de filas al mes (195 mensuales × días con parte): megabytes al año.
Lectura de dedicación por periodo: `WHERE anio = ? AND mes = ?`; cambios por
`version`/`actualizado_at_utc`.

## 6. Clases y funciones (firma, capa)

- *domain* (sv5) `HoraRecurso.es_mensual -> bool`.
- *application* (sv5) `ReglasRegistro._decidir_mensual(linea, base) ->
  AccionLinea | None`: `None` si apagado, sin `M*` o caso R3.
- *application* (sv4) `congelacion.vive_fuera(estado: str | None) -> bool`.
- *infrastructure* (sv4) `ParteReviewRepository._upsert_bandeja(session,
  reg, *, codigo_mes, prueba, clase, actor, ahora) -> bool` (True si cambió);
  `retirar_de_dedicacion(registro_ids: list[int], actor: str) -> dict`
  (`{"retiradas": n, "no_aplica": m}`).

## 7. Riesgos

- **Hueco en producción** (incidencias de mensuales ni en Sigrid ni leídas
  por nadie): lo evita el interruptor apagado por defecto y la activación
  solo cuando la feature espejo lea (DA8, §10).
- **Contrato sv5→sv4**: un sv4 viejo ignoraría `dedicacion` y dejaría líneas
  en `encolado`. Orden: sv3 → sv4 → sv5, y aun así sv5 no lo emite hasta
  encender el interruptor.
- **Reentrega tardía** de `q-transfer-result` tras una retirada volvería a
  publicar la línea (R12/R13). Ventana de minutos (caída de sv4 entre
  aplicar y borrar el mensaje); se acepta y queda documentado. Se arregla
  retirando otra vez.
- **Privilegios de `public`**: en PostgreSQL < 15 cualquier rol puede crear
  en `public`. Afecta ya a toda base del servidor; el script lo comprueba y
  avisa, no lo cambia (decisión del humano, fuera de alcance).
- **Criterio `M*` compartido** con dedicación (P1): si allí cambia, aquí
  hay que seguirlo. Va en «qué se rompe» de `azure-apps/partes.md`.
- **Obras de otra empresa**: dedicación imputa solo a la empresa de las obras
  (su F-034); la bandeja publica `obra_empresa` y la decisión es suya.

## 8. Decisiones (APROBADAS por el humano el 2026-10-02)

Las ocho, tal cual se recomendaban, DA4 con la opción 2. Matiz del humano
sobre DA4, blindado en R3 bis: «ahora mismo funciona perfectamente el que no
registra en Sigrid los recursos correctos (con hora mes). eso no debe
perderse. cuando haya hora mes y HE debe registrar hora mes en porcentajes y
HE en sigrid con normalidad».

| DA | Punto | Alternativas | Aprobada (y por qué) | Riesgo |
|---|---|---|---|---|
| DA1 | (a) Canal | 1) bandeja de salida en la base `partes`; 2) bandeja de entrada en la base `dedicacion` escrita por partes; 3) HTTP a `dedicacion-api`; 4) cola o blob de Storage; 5) vista sobre `parte_registros` | **1**. Cada proyecto escribe solo en su base; dedicación ya llega al servidor. 2 da a partes credencial de escritura en base ajena y le hace depender de un esquema que no controla. 3: la api no tiene autenticación y su ingress interno es su control de acceso, en otro entorno. 4: dedicación no usa Storage por diseño, exige RBAC cruzado y una cola consumida no sirve para retirar. 5 expone la tabla interna, que cambia bajo los pies | dedicación necesita una segunda conexión (otra base del mismo servidor) |
| DA2 | Quién escribe la bandeja | sv4 al volcar el resultado / sv5 al aprobar (lo que proponía el líder) | **sv4**. `ARCHITECTURE.md` (F-002) fija que sv5 va sin BBDD para no crear una tercera copia del ORM (lo vigila `test_f002_r11_sin_postgresql.py`); sv4 ya escribe `sigrid_*` en la misma transacción | ninguno nuevo: el resultado ya viaja por los dos canales |
| DA3 | Rol de lectura | `GRANT SELECT` sobre la bandeja al rol de aplicación que dedicación ya tiene / rol nuevo de solo lectura | **El rol existente**. En PostgreSQL un rol es objeto del **servidor**, no de una base: «crear el rol dentro de la base partes» no es posible; con el existente no se crea nada a nivel de servidor ni hay contraseña nueva en el Key Vault de dedicación | si dedicación rota o renombra su rol, hay que repetir el `GRANT` (documentado) |
| DA4 | (b) Capataces `MCAP`+`HECAP` (32) | 1) todo a dedicación; 2) extras a Sigrid con `HECAP` como hoy, el resto a dedicación; 3) como 2 y además copia informativa de las extras en la bandeja | **2** (aprobada con el matiz citado arriba). No cambia lo que se paga hoy por extras; dedicación reparte por días y las extras no cambian el reparto | excepción a la decisión 2 aceptada por el humano; R3 bis impide cualquier otra diferencia |
| DA5 | (c) Desaprobar, retirar y reaprobar | 1) `dedicacion` congela; botón «Retirar de dedicación»; reaprobar = upsert por `registro_id` con `version`; 2) «Marcar pendiente» retira las líneas del parte; 3) no congela y editar retira solo | **1**. Mismo modelo que `registrado` (F-004/F-024), acción explícita y con autor; 2 mezcla el parte (documento) con líneas que se aprueban por selección; 3 retira en silencio | un botón y una ruta nuevos en sv4 |
| DA6 | (d) Periodo cerrado en dedicación | 1) partes publica igual y dedicación decide al leer; 2) partes lee el periodo de dedicación y avisa o bloquea; 3) dedicación escribe un acuse en partes | **1**. partes no tiene por qué conocer la base de dedicación; 2 y 3 abren el acceso en sentido contrario. El portal dice «enviada a dedicación», no «aplicada» | quien aprueba no ve si llegó tarde: lo resuelve la feature espejo (avisar en el cuadrante) |
| DA7 | (e) Dónde se decide | sv5 (`ReglasRegistro`, acción nueva) / sv4 antes de enviar / sv3 al conciliar | **sv5**: ya lee `reshor` al aprobar (dato fresco) y es donde viven R1–R5. sv4 duplicaría la lectura y la regla; sv3 decidiría con datos de días atrás | el contrato de sv5 crece (R8), compatible hacia atrás |
| DA8 | Despliegue y lo ya aprobado | interruptor en sv5 / sin interruptor; histórico: nada automático / reaprobar meses elegidos / migración por script | **Interruptor apagado por defecto** y activación por el humano cuando dedicación lea; **nada automático** con el histórico: lo `omitido` de los meses que el humano elija se reaprueba desde el portal; lo `registrado` se queda en Sigrid | olvidar encender o apagar: es un comando y está en §10 |

## 9. Fuera de este repositorio y de esta feature

- **La feature espejo en `porcentajes`** (la crea el humano allí): leer la
  bandeja por periodo, convertirla en **propuesta** del cuadrante (decisión
  6), el cálculo por días laborables con vacaciones como trabajadas y
  festivos despreciados (decisiones 3 y 4), el calendario de laborables, el
  periodo cerrado (DA6), las obras de otra empresa y actualizar
  `azure-apps/dedicacion.md` (pasa a consumir algo).
- Ejecutar el `GRANT` (M2) y desplegar: el humano.

## 10. Despliegue sin hueco y verificación MANUAL (humano)

Orden: **sv3 → sv4 → M1, M2 → sv5** (interruptor apagado: el código queda
inerte) → feature espejo leyendo → **M3** (encender). Rollback: apagar el
interruptor; lo ya publicado se retira y se reaprueba por las reglas de
siempre. Lo `encolado` al encender se procesa con las reglas nuevas.
Lectura de Sigrid del 2026-10-02: **ninguna línea de `hmores` con synckey
`partes:`**, así que hoy no vive en Sigrid ninguna incidencia de mensual
escrita por partes (M0 lo confirma en la base).

- **M0** (antes de desplegar, PG `partes`, firewall abierto): `SELECT
  sigrid_estado, left(fecha,7) AS mes, count(*) FROM parte_registros WHERE
  sigrid_motivo LIKE '%codigo mensual%' OR sigrid_motivo LIKE '%es mensual%'
  GROUP BY 1,2 ORDER BY 2;` → anotar en `progress/current.md`.
- **M1** (tras sv3 y sv4): `SELECT count(*) FROM dedicacion_bandeja;` → 0.
- **M2**: `psql "host=<servidor> dbname=partes user=<admin> sslmode=require"
  -v rol=<rol_app_dedicacion> -f infra/sql/01_dedicacion_lectura.sql` → las
  comprobaciones dan true/false/false.
- **M3** (tras sv5): `az containerapp update -n ca-sv5-transfer -g
  rg-partes-dev --set-env-vars MENSUALES_A_DEDICACION=true`; aprobar una
  línea de un mensual, ver «→ dedicación» y `SELECT registro_id, version,
  vigente, tipo, codigo_mes, prueba FROM dedicacion_bandeja ORDER BY
  actualizado_at_utc DESC LIMIT 5;`; «Retirar» (vigente false, versión 2) y
  reaprobar (vigente true, versión 3). Apagar: el mismo comando con `false`.
