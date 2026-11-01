<!-- specs/F-056-franquicia-de-extras/design.md -->
# F-056 · Franquicia de extras — Diseño

> **Enmiendas** (literales en §7). 2026-10-27, DA1 = C: X sale de `partes` (caen `empleado_franquicia` y
> la pantalla de `/admin/jornadas`) y pasa a un campo de Sigrid que rellena Administración (DA21–DA27).
> 2026-10-27, DA28 = A: la vista decide por `POST /api/franquicia/decidir` y aplica (R45, R46). 2026-10-29,
> DA29–DA31 = A: el campo es EXTENDIDO (`defext`/`conext`, H7, H8) y T23 sustituye en sv5 lo hecho para una
> columna de `res` (§4). Versión del 2026-10-23: `git show 6d777c4:specs/F-056-franquicia-de-extras/design.md`.

## 1. Encaje, límite de servicio y rigor

- **sv5** es el único que escribe en Sigrid, el único que lee `hmores` y, con la enmienda, el **único
  que lee el campo de franquicia** (DA21): calcula E, X y A (la fórmula y la regla «activa» viven solo
  aquí, DA15), da de alta la línea de ajuste y la edita. **sv4** guarda la decisión humana, calcula
  periodo, día de ajuste y obra (necesita Sesame y las líneas de `partes`, que sv5 no tiene) y orquesta
  por HTTP síncrono (edita horas ya registradas: nunca por cola, como pisar y F-046).
- **sv3 no cambia**: el ajuste no es una fila de `parte_registros` (fuera del reparto F-045, de F-025,
  F-049 y de la congelación). Solo recibe la copia del ORM (la base es una, semántica 7).
- **Lista cerrada de `CLAUDE.md`: no crece** (DA18). El código del campo y la regla de R2 viven solo en
  sv5; sv4 no lee `res`, `defext` ni `conext` para esto, así que `_SQL_RECURSOS_ACTIVOS` (sv4), `IndicePersonas` (sv3) y
  `recursos_por_dni`/`datos_recursos` (sv5), gemelos de F-023/F-036, no se tocan.
- **Rigor crítico**: escritura nueva en el ERP de producción que cambia horas de nómina y coste.

## 2. Hallazgos (M1 del 2026-10-23 y revisión del 2026-10-27)

- **H1** · «Mes de nómina» ya existe en sv4 (`calendar_builder.MODE_NOMINA`, 16 → 15). El registro en
  Sigrid es por mes natural: el ajuste cae en el parte `hmo` del mes del día de ajuste.
- **H2** · Los choques (`pisado.choques`, `ReajustePipeline._choques`) son recurso + día + `horide`: sin
  R31 el ajuste chocaría con la extra real del día y el modal ofrecería pisarla a 0.
- **H3** · `stmt_insert_linea` y `stmt_actualizar_linea` (F-046) sirven tal cual; `lineas_para_reajuste`
  lee `can`, `pre`, `hmoide` y `enlazada`. **H4** · `RegistroPipeline.preparar` da obra destino, modo
  pruebas, verificación F-023, reglas y cuenta F-021; `_crear_parte` es la única alta.
- **H5** · M1 (agregados): 138 recursos persona con exactamente un `HE*`, ninguno con dos (DA5); las
  `HE*` se enlazan a nómina al procesarla (DA9); Administración ya mete `HE*` negativas «Ajuste…» a mano
  (días 15/16); nuestras 446 líneas `partes:%` en 14 partes En registro, ninguna enlazada.
- **H6** · `prueba_escritura_sigrid.py limpiar` borra por `tex = 'PRUEBA-IA'` ⇒ en pruebas el `tex` es la marca (R32).
- **H7** (2026-10-29, líder, solo lectura y agregados contra `ruesma`) · Ninguna columna con «fran» en
  `INFORMATION_SCHEMA`: el campo es EXTENDIDO. `defext` ide 49 = `tip` 33, `cod` `10`, «Franquicia Horas»,
  `camtip` 1; valores en `conext` (`conide` = `con.ide` = `res.ide`; `camtip` 1 ⇒ `valn`, Entero). Los
  2636 `res` son `con` de tip 33. Hoy 1 recurso con fila (valor 0), como mucho una por recurso: nadie tiene
  franquicia activa. Tablas: `azure-apps/sigrid_tablas.md` (`conext`, `defext`) y `sigrid_api.md` §9.8.
- **H8** · El `cod` `10` NO es único: también es «Administrativo de obra» de tip 42 (`defext` 26,
  `camtip` 6, `camtab` `emp`, 466 filas en `conext`) ⇒ todo se filtra SIEMPRE por tip 33 (R47).
- **H9** · `sql/read` admite cualquier `SELECT` de una sentencia con `?`: `cod` va como parámetro (no se
  interpola nada). Va aparte de `datos_recursos` (F-023): un campo mal definido no tumba el registro (DA23).
- **H10** · En `ARCHITECTURE.md` la semántica 18 ya es F-054 (llegan hasta la 20): F-056 será la 21.

## 3. Flujo y estados (`franquicia_ajuste.estado`)

```
preflight: sv5 /recursos (1 llamada) → candidatos → sv5 comprobar ──► modal: Ajustar | No ajustar | Recalcular | Mantener
ejecutar/encolar ─ajustar|recalcular─► decidido ─aplicar(sv5 ok)─► aplicado ─recalcular─► decidido
                 └no_ajustar─► rechazado ─Ajustar (vista)─► decidido    aplicar(ko)─► error ─aplicar─► …
```

- Las líneas de la aprobación viajan como siempre (DA12). El modal, al terminar el registro (síncrono:
  con la respuesta; asíncrono: cuando el sondeo de F-024 ya no ve `encolado`), llama a `aplicar` de cada
  fila decidida y pinta el resultado (con la X que usó sv5). Si se cierra antes, queda `decidido` y la
  vista de trabajador ofrece «Aplicar». Su «Ajustar»/«Recalcular» va por `decidir` y luego `aplicar` (DA28).
- sv5 `ejecutar`: `preparar` (fuera del lock) → bajo el lock: estado del campo y X del recurso, E y la
  línea por synckey → A → `crear` / `actualizar` / `ya_aplicado` / `sin_ajuste` / `no_editable` → una
  sentencia (el alta del parte, si falta, antes) → relectura.

## 4. Ficheros

### sv5 (`services/partes-transfer`) — T1–T11 hechos; T23 (DA29–DA31) los cambia así

- **`domain/models/registro_models.py`**, **`/api/franquicia/recursos`**, `FranquiciaIn`, `comprobar`,
  `ejecutar` y `_franquicia_de`: SIN cambios (R40–R42); solo docstrings que digan «columna de `res`».
- **`application/services/franquicia.py`** (puro): SE QUITAN `CAMPO_RE`, `TIPOS_NUMERICOS` y
  `es_tipo_numerico`. Entran `COD_EXT_RE = ^[A-Za-z0-9_.-]{1,16}\Z` (el `cod` es Texto 16 y va como
  parámetro: el filtro solo detecta un ajuste mal puesto), `TIP_RECURSO = 33`, `CAMTIP_NUMERO = 1`,
  `motivo_definicion(filas) -> str | None` (0 filas, más de una o `camtip` ≠ 1 ⇒ motivo, R38, DA31) y
  `lectura_de(valores: list) -> LecturaFranquicia` (sin fila ⇒ `inactiva`, X = 0; más de una ⇒
  `invalida` con `MOTIVO_VARIAS_FILAS`: no se elige una a ciegas y «no se sabe» no es X = 0, R42; una ⇒
  `leer_valor`). `leer_valor`, `MAX_FRANQUICIA_H`, estados, `veredicto` y `texto_ajuste` no cambian.
- **`config/settings.py`**: `franquicia_campo_res`/`FRANQUICIA_CAMPO_RES` pasa a `franquicia_campo_ext:
  str = Field("", alias="FRANQUICIA_CAMPO_EXT")`; vacío = apagada; SIN validador que impida arrancar (R38).
- **`infrastructure/sigrid/sigrid_write_client.py`**: SE QUITAN `tipo_columna_res`, `valores_campo_res` y
  su import local de `CAMPO_RE`. Entran `definicion_campo_ext(cod) -> list[dict]`: `SELECT defext.ide AS
  ide, defext.camtip AS camtip FROM defext WHERE defext.tip = 33 AND defext.cod = ?`, y
  `valores_campo_ext(ides, cod) -> dict[int, list]`: `SELECT con.ide AS reside, conext.ide AS extide,
  conext.valn AS valor FROM con LEFT JOIN conext ON conext.conide = con.ide AND conext.cod = ? WHERE
  con.tip = 33 AND con.ide IN (?, …)` en lotes de `LOTE_RECURSOS` (`reside` → `valn` de sus filas con
  `extide`; un `res.ide` sin `con` de tip 33 no sale: `LEFT JOIN` desde `con` y no `conext JOIN con`, para
  conservar «recurso que no existe ⇒ `invalida`», T10). `truncated` ⇒ excepción; sin `dni` (R48) ni otro `tip` (R47).
- **`application/pipelines/franquicia_pipeline.py`**: `franquicias(ides)` igual de forma (R3, R38–R40, caché
  del «sí» en `_campo_ok`), con `COD_EXT_RE` + `definicion_campo_ext` + `motivo_definicion` en lugar de
  `CAMPO_RE` + `tipo_columna_res` + `es_tipo_numerico` y `lectura_de` por recurso (ausente ⇒ `invalida`).
- **`interface_adapters/api/app.py`** (`/health` lee `franquicia_campo_ext`) y **`main.py`**
  (`_cableado_franquicia` con `COD_EXT_RE`: «campo extendido <cod>»). **`tests/dobles.py`**: `SigridFake`
  con `defext`, `con` y `conext` (incluidos el `cod` `10` de tip 42 y dos recursos de un mismo DNI).

### sv4 (`services/partes-front`)

- **Crear `application/services/franquicia.py`** (puro): `periodo_de(d) -> Periodo(clave, inicio, fin)`
  sobre `calendar_builder`; `dia_de_ajuste(periodo, jornada_de)` (R5); `elegir_obra(lineas_dia,
  lineas_periodo)` (R7); `candidatos(lineas, filas, franquicias: dict[int, dict] | None)` (R9–R12, con
  `motivo`; `None` = R44); `extras_pendientes(...)`; `bloque_franquicias(candidatos, veredictos, aviso)`;
  `validar_decisiones(crudo, claves_validas)`; `payload_franquicia(fila) -> dict`; `ESTADOS`,
  `DECISIONES`.
- **`infrastructure/database/orm_models.py`** y su copia de sv3: `FranquiciaAjusteOrm` (§5).
- **`infrastructure/database/parte_repository.py`**: `lineas_trabajador_periodo(recurso_ide, inicio,
  fin)`, `ajustes_de(claves)`, `decidir_ajuste(clave, decision, datos, *, actor)` (alta con el índice
  único o `UPDATE … WHERE id = ? AND estado = ?`; si no, 409), `encolados_de(...)` (R18),
  `cerrar_ajuste(id, *, ok, sv5, error, actor)` (guarda E, A, X usada).
- **`infrastructure/transfer/transfer_client.py`**: `franquicia_recursos`, `franquicia_comprobar`,
  `franquicia_ejecutar` (timeout de la comprobación de F-024; un fallo de `franquicia_recursos` = R44).
- **`interface_adapters/web/app.py`**: preflight con `franquicias` (R9–R14, R43, R44); `ejecutar` y `encolar`
  procesan `franquicias` ANTES de los grupos (R15, R16); `POST /api/franquicia/{id}/aplicar` (R17–R19);
  contexto del ajuste en la vista de trabajador (R20, X actual por `franquicia_recursos`). Actor solo de
  `_actor(request)`.
- **DA28 (T17b, hecho; R45, R46)** · `POST /api/franquicia/decidir`: 503 sin `TRANSFER_BASE_URL`; formato
  con `fq.decision_vista` (`_decision` compartida con `validar_decisiones`, `DECISIONES_VISTA`; 422);
  ámbito: alguna línea de `lineas_trabajador_periodo` con ese `recurso_ide` (422); propuesta con
  `_plan_franquicia` (extraído de `_planes_franquicia`, lo usan los dos); `decidir_ajuste` SIN cambios (CAS y
  transiciones de R16, 409); sin sv5; `{ok: true, ajuste}`; F-017 a 20 `_actor(request)`. Vista: botones
  `data-franquicia-decidir` y `decidirDesdeVista` (decidir → `/aplicar`, sin recarga nueva, F-043).
- **`templates/trabajador_detail.html`** (bloque), **`static/app.js`** (`franquiciasHtml`,
  `decisionesFranquicia`, `aplicarFranquicias` tras el resultado y el sondeo; «Registrar» deshabilitado
  sin decisión, R13; aviso de R44), **`static/styles.css`**.
- **T24 (solo textos)**: «campo de `res`» en sv4 (`franquicia.py`, `parte_repository.py`, `app.py`) y en
  `orm_models.py` (las DOS copias, byte-idénticas; `test_f056_orm.py`). Comprobado (R48): `/recursos` recibe
  el `recurso_ide` de las líneas (`parte_registros`, elegido por sv3 con la empresa de la obra), el que sv5
  escribe en `hmores.reside` sin cambiarlo (solo completa por DNI las líneas SIN recurso, fuera de `candidatos`).
- **T27 (DA32)** · `_propuesta` (`app.py`) da a `elegir_obra` solo las líneas del recurso (pura nueva
  `fq.lineas_del_recurso`); `_dia_ajuste` (persona, DA6), `varios_recursos` y el repositorio, con todas.

### Raíz y documentación

- `tests/test_f010_orm_models_gemelos.py` y `tests/test_f015_r29_guardian_cinco_tablas.py`: `TABLAS` a
  OCHO y columnas literales de `franquicia_ajuste`. Nuevo `tests/test_f056_contrato_franquicia.py` (R36).
  Docs de R35; `azure-apps/partes.md` con commit local, sin push.

### Lo que NO se toca

sv3 salvo la copia del ORM; en sv4 `jornada_admin.py`, `admin_jornadas.html`, `empleado_jornada` y
`sigrid_lookup_client.py`; en sv5 `recursos_por_dni`, `datos_recursos`, `horas_de_recursos`,
`stmt_insert_linea`, `stmt_actualizar_linea`, `stmt_anular_linea`, `ReglasRegistro`, `estado_parte.py`,
`cuenta_analitica.py`, `stmts_crear_parte`; `congelacion.py`, `esta_congelado`, `lineas_para_registro`,
`incidencias_horas.py`; el contrato de `q-transfer` y `resultado_consumer.py`; F-024; `undo_log`;
`dedicacion_bandeja`; `tests/test_f038_lectores_sigrid.py` (el lector es el mismo fichero); sv1, sv2,
`infra/` (el ajuste se pone fuera del manifiesto, como `MOVER_CIZ`), `CLAUDE.md`. F-056 no escribe en
`res`.

## 5. Esquema (base `partes`, sin fichero `NN_*.sql`)

Lo crean `create_all` y `ddl_complementario()` al arrancar sv3 y sv4. Toda `NOT NULL` con
`server_default`. **`franquicia_ajuste`** (sin nombres ni DNIs; el trabajador es su `recurso_ide`; se
mantiene, DA25): `id` PK (su synckey es `partes:franquicia:<id>`); `recurso_ide` Integer NOT NULL `'0'`;
`periodo` String(7) NOT NULL `''`; índice ÚNICO `ux_franquicia_ajuste_periodo (recurso_ide, periodo)`;
`fecha_int`, `obra_ide` Integer NOT NULL `'0'`; `obra_codigo`, `partida_cod` String(32); `partida_ide`
Integer; `franquicia` Float (X que usó sv5 en la última aplicación; null hasta aplicar); `extras` y
`ajuste` Float; `estado` String(16) NOT NULL `'decidido'` (índice); `decision` String(16); `hmores_ide`,
`hmoide` Integer; `parte_cod` String(32); `resultado` Text; `error` String(255); `decidido_por`,
`aplicado_por` String(120); `decidido_at_utc`, `aplicado_at_utc` String(64); `creado_at_utc`,
`actualizado_at_utc` String(64) NOT NULL `''`. Constantes en el ORM: `ESTADOS_FRANQUICIA` y una por estado.

## 6. Contrato sv4 → sv5

- **`/api/franquicia/recursos`** · entrada `{recurso_ides: [int]}`; respuesta `{estado, motivo,
  recursos: {"<ide>": {franquicia, estado}}}` (vacío si no es `ok`); 502 si falla la lectura de la definición.
- **`/api/franquicia/comprobar` y `/ejecutar`** · entrada (`FranquiciaIn`): `ajuste_id` (≥ 0),
  `recurso_ide` (≥ 1), `periodo` (`YYYY-MM`), `inicio`, `fin`, `fecha_int` (YYYYMMDD, inicio ≤ fecha ≤
  fin), `obra` `{ide, codigo}`, `partida_ide`, `partida_cod`, `extras_pendientes` (solo comprobar),
  `usuario`. Ya NO lleva `franquicia`. `ajuste_id` 0 solo en comprobar (ejecutar con 0 ⇒ 422).
- Respuesta: `ok`, `accion` (`crear` | `actualizar` | `ya_aplicado` | `sin_ajuste` | `no_editable`),
  `extras` (E), `objetivo` (A), `actual`, `hmores_ide`, `hmoide`, `parte_cod`, `parte_estado`,
  `complementario`, `hora_codigo`, `pre`, `motivo`, `escrita`, `forzada_pruebas`, `error` y, NUEVOS,
  `franquicia` (X) y `franquicia_estado`.

## 7. Decisiones

Literales anteriores. **Regla F-053**: «no se debe borrar en sigrid, así que solo editará líneas, por lo
que si una hora extra se queda a cero no se borrará sino se pondrá a cero.» **Aprobación 2026-10-23**: «a
a todo, actualzia backlog para que refleje lo que tien spec y estado real de todo» ⇒ DA1–DA20 = A.

**Sin cambios (= A, aprobadas)**: DA3 E = Σ neta `HE*` de Sigrid · DA4 una línea en la obra de más horas
· DA5 el `HE*` de las reglas y su `pre` · DA6 último día con `jornada_dia` > 0 · DA7 dispara el día de
ajuste o un ajuste existente, y la vista · DA8 línea viva: «Recalcular»/«Mantener» y `UPDATE` · DA9
parte cerrado o enlazada no se edita · DA10 aviso en el modal, se aplica al terminar el registro · DA11
«No ajustar» reversible · DA12 el servidor no excluye líneas · DA13 `HE*` negativa con `tex` · DA14
synckey propia y exclusión en choques · DA15 E y A en sv5 · DA16 varios recursos o sin `HE*`: no se
ajusta · DA18 la lista cerrada no crece.

| DA | Pregunta | Alternativas | Decisión / recomendación |
|---|---|---|---|
| DA1 | ¿Dónde se guarda X? | A tabla `empleado_franquicia`. B columna en `empleado_jornada`. **C campo nuevo de `res` en Sigrid**. D YAML. | **C, el humano 2026-10-27**, literal en dos mensajes: «para saber que trabajadores son franquiciados y cual es el valor de la franquicia habra que crear un campo en sigrid que lo defina» y «va a ir en recursos. la fecha no hace falta, se aplica en los partes que se registren si esta activo (valor distinto de 0 o null). el campo lo rellena adminen sigrid.» (el «campo» resultó extendido: DA29–DA31) |
| DA2 | ¿X por qué periodo? | **A** mes de nómina (16 → 15), X = valor del campo al leerlo (la vigencia cae con DA1 = C). B mes natural. C anual. | A, enmendada |
| DA17 | ¿Interruptor? | **A** `FRANQUICIA_CAMPO_EXT` vacío = apagado (y, con él puesto, nadie tiene franquicia hasta que Administración rellene el campo). B interruptor aparte. | A, enmendada |
| DA19 | Pantalla de configuración | — | **Cae** con DA1 = C (la configura Administración en Sigrid) |
| DA20 | ¿Una feature o dos? | **A** una: sv5 (T1–T11) y sv4 (T12–T18). B partir. | A, enmendada; corte natural tras T11 |
| DA21 | ¿Quién lee el campo? | **A** solo sv5: `/api/franquicia/recursos` (una llamada por preflight o vista) y relectura en `comprobar`/`ejecutar`. B sv4 con `sigrid_lookup_client.py` (nombre del campo y regla «activa» en dos servicios, la lista cerrada crece y sv4 lee `res` fuera de los gemelos de F-036). C los dos. | A (cero duplicación; sv5 ya es el dueño de E y A) |
| DA22 | X cambia entre el aviso y el registro, o tras aplicar | **A** vale la X de Sigrid al aplicar o recalcular (leída bajo el lock); se guarda en la fila y el modal o la vista enseñan si difiere de la del aviso; un periodo anterior que se recalcula usa la X actual («se aplica en los partes que se registren»). B 409 y pedir decisión nueva. C la del aviso (sv4 la manda). | A |
| DA23 | Ajuste vacío, código inválido, definición ausente o doble, `camtip` no numérico o lectura fallida (enmendada por DA30) | **A** no se aplica: `apagada` en silencio; lo demás `no_disponible` con aviso no bloqueante y WARNING; `ejecutar` no escribe (no es X = 0); sv5 arranca y registra igual. B sv5 no arranca con el campo mal (tumbaría el registro). | A |
| DA24 | Valores raros del campo | **A** negativo, > 200 h o no convertible ⇒ `invalida`: no se ajusta y se avisa; decimales a dos. B cualquier positivo vale. | A |
| DA25 | ¿Sigue `franquicia_ajuste`? | **A** sí: guarda la decisión (`rechazado` no se vuelve a preguntar; `decidido` pendiente en asíncrono), la autoría, la X usada y da el `id` de la synckey ya implementada. B quitarla con synckey `partes:franquicia:<reside>:<periodo>` (sin rechazo persistente ni autoría; rehace T1–T6). | A |
| DA26 | `tex` al recalcular (punto abierto del implementer) | **A** `tex` sin cifras `Ajuste franquicia extras <periodo>`: nunca queda desfasado, `stmt_actualizar_linea` (compartida con F-046/F-053) no cambia; la cifra es `can` y X está en el propio recurso. B `tex` con cifras y el `UPDATE` lo reescribe (parámetro nuevo en la sentencia compartida). C `tex` con cifras del alta (desfasa al recalcular). | A |
| DA27 | ¿Franquicia del recurso o de la persona? | **A** del recurso que lleva las extras (`hmores.reside`, el elegido por DNI en F-023/F-036: persona, alta, empresa de la obra); otro recurso de la misma persona no cuenta; varios con extras ⇒ DA16. B de la persona (elegir entre sus recursos: duplicaría la elección por DNI). | A |
| DA28 | ¿Cómo decide la vista «Ajustar»/«Recalcular» (R20 pedía los botones, pero solo había `/aplicar`, que exige `id`)? | **A** (tal como se le presentó) «Una llamada nueva, "decidir", con trabajador, periodo y decisión. Tiene las mismas comprobaciones que la decisión del modal (que ese trabajador tenga líneas en el periodo y que nadie lo haya cambiado entretanto) y después aplica.» Admite `ajustar` y `recalcular` (la vista no ofrece «No ajustar» ni «Mantener»); «después aplica» = la vista llama a `/aplicar` con el `id` devuelto, así R18 y la X de DA22 siguen en un solo sitio. B `aplicar` acepta `decision` opcional (mezcla decidir y aplicar; sin fila no hay `id`). C solo en el modal (cambia R20 y DA11). | **A, el humano 2026-10-27** (literal: «a») |
| DA29 | ¿De dónde sale X ahora que el campo es extendido? | **A** «Del valor numérico del campo extendido en `conext`, filtrando por recurso y por el tipo 33. Si no hay fila, el valor está vacío o vale 0, ese recurso no tiene franquicia. Sigue leyéndolo solo sv5.» Precisión del humano: el `conide` es SIEMPRE el `res.ide` del recurso de la obra, ya elegido por DNI con la empresa de la obra (F-023/F-036, DA27, `hmores.reside`); nunca se busca por DNI; una persona con recursos en dos empresas puede tener X distinta en cada uno y solo cuenta la del recurso de la empresa de la obra (R48). Más de una fila por recurso ⇒ `invalida` (no se elige a ciegas). | **A, el humano 2026-10-29**, literal: «da29, recuerda coger el ide del recurso filtrado por empresa, el mismo dni de recurso puede estar en 2 empresas. lo demas ok» |
| DA30 | ¿Qué nombra el ajuste? | **A** «El ajuste pasa a ser el código del campo extendido (`10`), en vez del nombre de una columna. Al leer, sv5 comprueba que existe la definición de tipo 33 y que el campo es numérico. Si no, la franquicia queda "no disponible", con aviso y sin bloquear el registro. Con el ajuste vacío sigue apagada.» B localizarlo por el nombre («Franquicia Horas»): descartada. | **A, el humano 2026-10-29** («lo demas ok») |
| DA31 | ¿Decimales? | **A** «Sigrid guarda el valor como entero, así que la franquicia va en horas completas. […] esa comprobación de tipo lo detectaría y dejaría la franquicia "no disponible".» (`camtip` 1 = `valn` entero; otro `camtip` ⇒ `no_disponible`). | **A, el humano 2026-10-29** («lo demas ok») |
| DA32 | ¿Con qué líneas se elige la obra del ajuste (observación 6 del reviewer: ordinarias de la persona con OTRO recurso, de otra empresa, el día de ajuste podían ganar la obra; sv5 lo paraba con F-023, R30, y el trabajador se quedaba sin ajuste)? | **A** (tal como se le presentó) «arreglarlo ya, eligiendo la obra solo con las líneas del recurso del ajuste. Es un cambio pequeño en sv4, con su test y la mutación de esas líneas. […]» B «cerrar ya y dejarlo como feature futura». Coherente con R48. El día de ajuste NO cambia: sigue siendo de la persona (DA6); recortarlo al recurso cambiaría el `candef` que toma `_dia_ajuste` (hoy el de la primera línea con `candef` de cualquier recurso) y podría mover el día: no se decide aquí. | **A, el humano 2026-10-29**, literal: «sobre la 6, la A» |

## 8. Riesgos

- **R-a · Escritura en producción** que baja horas de nómina: decisión humana por trabajador, `comprobar`
  previo, lock, `WHERE` optimista, relectura, M2 en la 0404 antes de activar el campo.
- **R-b · Choque con la extra del día** (H2): lo vigilan tests en los dos `_choques`.
- **R-c · Orden asíncrono**: R18 impide aplicar con líneas `encolado`; el aviso posterior recalcula.
- **R-d · Nómina procesada**: la línea queda enlazada y no se edita (DA9).
- **R-e · El campo no encaja: RESUELTO** (2026-10-29): era extendido; DA29–DA31 lo leen así (H7, H8).
- **R-i · Alguien cambia el `camtip` de la definición o reusa el `cod`**: otro `camtip` o una segunda
  definición de tip 33 ⇒ `no_disponible` (R38); un reuso en otro `tip` no afecta (R47); cambiarle el
  sentido sin cambiar el tipo no se detecta ⇒ consta en `azure-apps/partes.md` («qué se rompe»).
- **R-f · Retroactividad** (DA22): un cambio de X afecta a lo que se recalcule antes de la nómina (X usada y actual).
- **R-g · Despliegue**: sv5 → sv4 con el campo vacío; se activa al final (M4). sv4 nuevo con sv5 viejo:
  `/recursos` da 404 ⇒ aviso de R44, nada se escribe.
- **R-h · `porcentajes`**: no escribe `HE*` ni comparte la synckey.

## 9. Tests (sin red ni BBDD; sintéticos)

sv5: `test_f056_franquicia.py` (fórmula, veredictos, `leer_valor` en sus bordes 0, 0.001, 200, 200.01,
−1, texto, None; `COD_EXT_RE`; `motivo_definicion`; `lectura_de` con 0, 1 y 2 filas), `test_f056_pipeline.py`
(R1–R3, R38–R42, R47, R48 y R22–R33 con `SigridFake`: apagada sin lecturas; definición ausente, doble o
`camtip` ≠ 1 ⇒ `no_editable` sin escribir; caché del «sí» y su olvido; X bajo el lock; X = 0 con línea ⇒
`UPDATE` a 0; el `cod` `10` de tip 42 nunca da X; un DNI con dos recursos de dos empresas y X 8 y 20 ⇒ la
del recurso pedido, sin buscar por DNI), `test_f056_cliente.py` (SQL y parámetros exactos de las dos
lecturas, con `tip = 33` y sin `dni`), `test_f056_choques.py`, `test_f056_api.py` (R40,
422, 503, `/health`, cableado). sv4: `test_f056_franquicia.py`, `test_f056_decisiones.py` (R9–R19, R43, R44 con
SQLite de `dobles.py` y un sv5 falso: `/recursos` caído o `no_disponible` ⇒ aviso, CAS, 409; R48: a
`/recursos` solo van los `recurso_ide` de las líneas y el candidato lleva la X de su recurso),
`test_f056_vista.py` (R20; R45, R46: 422 de formato, decisión y sin líneas, 409 de CAS y transición, 503, actor,
botones y JS `decidir` → `aplicar`), `test_f056_orm.py`; `node --check`. Raíz: guardianes (R34) y contrato (R36).

## 10. Verificación MANUAL (humano)

- **M1 · HECHA** (2026-10-23, H5). **M1b · HECHA** en lo posible (2026-10-29, líder): H7, H8; el valor > 0, en M2.
- **M2** (escritura, sv5 local con `OBRA_PRUEBAS_FORZAR=true` y `FRANQUICIA_CAMPO_EXT=10`, recurso de
  pruebas de F-034 en la 0404, un mes sin partes; `ajuste_id` ≥ 990560001). Administración pone un valor
  entero > 0 (8) en el campo `10` de ese recurso (F-056 no escribe `conext`): (a) dos extras de 3 h; (b) `/recursos` ⇒ `activa`,
  8; `comprobar` ⇒ E = 6, A = −6, `crear`; (c) `ejecutar` ⇒ `HE*` −6, `tex` `PRUEBA-IA`; (d) repetir ⇒
  `ya_aplicado`; (e) otra extra de 4 h el día de ajuste, sin conflicto (R31); (f) `ejecutar` ⇒ E = 10,
  A = −8, `actualizar` sin `DELETE`; (g) Administración deja el campo a 0 ⇒ `can = 0`, `tot = 0`;
  (h) `prueba_escritura_sigrid.py limpiar`, `limpiar --ejecutar` y `verificar`.
- **M3** tras desplegar sv5 → sv4 (campo aún vacío): `/health` de sv5 ⇒ `franquicia: apagada`;
  `SELECT count(*) FROM franquicia_ajuste` ⇒ 0 (`PGOPTIONS='-c default_transaction_read_only=on'`).
- **M4** (producción, el humano): `az containerapp update` de sv5 con `FRANQUICIA_CAMPO_EXT=10`, primera
  franquicia real rellenada por Administración, aprobar su día de ajuste y mirar la línea en Sigrid.
