<!-- specs/F-055-sv5-omite-lineas-sin-fecha/design.md -->
# F-055 · sv5 omite las líneas sin fecha válida — Diseño

> Escrita sobre `dev` 2bfeab7 (2026-10-22), **refrescada sobre 14b3cd5 (2026-10-31)** tras
> F-038, F-056, F-060 y F-062 en sv5 (cambios: `progress/explore_F-055_refresco.md`).

## 1. Estado actual (`dev` 14b3cd5)

### 1.1 Cómo llega la fecha a sv5

- sv4 `lineas_para_registro` (`parte_repository.py` l. 2159) manda `int(r.fecha_int or 0)`
  (l. 2284): sin fecha viaja `0`. F-054 (done) manda el parte a revisión, no impide aprobarlo.
- sv5 HTTP: `LineaIn.fecha_int: int` (`app.py`): `null` da 422 a la petición entera. Cola:
  `_a_dominio` (`transfer_consumer.py`) lo pasa tal cual; con `null`, `LineaEntrada.ano`
  revienta en `decidir` y la petición sale `ok: false`. La única validación de fecha de sv5 es
  `FranquiciaIn._coherente` (F-056: `_fecha_valida` del calendario e `inicio <= fecha_int <=
  fin`), solo en `/api/franquicia/*`; ni `preparar`, ni las reglas, ni el cliente la miran.

### 1.2 Qué haría sv5 hoy (sonda con `SigridFake` sobre 14b3cd5, en el scratchpad, sin commit)

| `fecha_int` | `ejecutar` con una línea normal de 8 h |
|---|---|
| `0` | `ok`, alta de `PT0/00001` con `ano = 0`, `mes = 0`; línea escrita con `fec = 0` |
| `20261340` | `ok`, alta de `PT26/00001` del periodo **2026/13**; línea escrita |
| `20160315` | `ok`, alta de `PT16/00001` del periodo 2016/03; línea escrita |

Con el cliente real es igual (`stmts_crear_parte` no valida el periodo); con los partes
cerrados F-031 crearía un complementario. En Sigrid no se borra (F-053).

### 1.3 Dónde se decide cada línea: el paso 2a sigue siendo el punto único

`RegistroPipeline.preparar` (`application/pipelines/registro_pipeline.py` l. 231): 2b recursos
por DNI (`elegir_por_dni` a la fecha), 2c verificación (`verificar_recurso`), 3
`horas_de_recursos`, 4 `ReglasRegistro.decidir` (la omisión previa sigue mandando sobre todo,
también sobre el mensual F-019 y sobre el hermano `fin_mismo_dia` de F-062, que solo se calcula
tras ella), 4b cuentas (solo acciones `escribir`). Pasan **todos** por `preparar`:

| Camino | Entrada | Lecturas con la fecha fuera de `preparar` |
|---|---|---|
| `preflight` / `ejecutar` HTTP | `PeticionIn` | `_evaluar` y `registrar`: solo acciones `escribir` |
| Cola `q-transfer` | `_a_dominio` | igual (`preparar` + `registrar`) |
| Reajuste F-046, extras nuevas | `ReajustePipeline._preparar_nuevas` | `_choques` solo si el veredicto es editable |
| **Franquicia F-056** (nuevo) | `FranquiciaPipeline._preparar` (una extra el día de ajuste) | `_evaluar` lee E (`extras_del_periodo`) y `partes_del_periodo(p.ano, p.mes)` **antes** del veredicto (§5) |

- **F-060** (6 bis, `_ciz_de_racha`) y **F-062** (hermano, `_ciz_ajeno`): solo acciones
  `escribir`; el CIZ se busca por synckey, no por fecha, y se compara con `a.fecha_int` ya
  validada. **Ningún camino nuevo lee Sigrid con la fecha antes de `preparar`.**

## 2. Límite de servicio y encaje

- **sv5**: quien escribe y último punto antes del ERP (ya verifica el recurso, F-023). Función
  pura en `application/services/` y paso nuevo **2a** de `preparar` (DA1 A). Sin
  responsabilidades nuevas. sv4 no cambia (DA3 A): lo omitido vuelve `omitido` con su motivo,
  no congela (semántica 10) y se arregla poniendo la fecha y reaprobando.

## 3. Ficheros

### A crear (todo en `services/partes-transfer/`)

- `application/services/fecha_linea.py` — regla pura (§4.1).
- `tests/test_f055_fecha_linea.py` — R1, R2.
- `tests/test_f055_pipeline_fecha.py` — R3–R7, R10, R11, R15 (con `SigridFake`).
- `tests/test_f055_canales.py` — R8, R9 (HTTP con `TestClient` y cola con los fakes).

### A modificar

- `application/pipelines/registro_pipeline.py`: paso 2a (§4.2), `_hoy()` estático y el 2a
  en el docstring de cabecera.
- `domain/models/registro_models.py`: `LineaEntrada.fecha_int: Optional[int] = None` (sigue
  en segunda posición; detrás van los campos de F-060/F-062 con defecto) y `ano` / `mes` con
  `int(self.fecha_int or 0)` (R9).
- `interface_adapters/api/app.py`: `LineaIn.fecha_int: Optional[int] = None` (R9, DA4 B).
- `docs/ARCHITECTURE.md` semántica 6 y `azure-apps/partes.md` (§10, DA7).

### Que NO se tocan

- `reglas_registro.py`, `coherencia_recurso.py`, `parte_abierto.py`, `pisado.py`,
  `racha_ciz.py`, `franquicia.py`, `franquicia_pipeline.py` (DA11 A), `reajuste_*.py`,
  `comprobacion_lineas.py`, `estado_parte.py`, `cuenta_analitica.py`, `sigrid_write_client.py`,
  `transfer_consumer.py`, `resultado_json.py`, `FranquiciaIn`/`_fecha_valida`, `settings.py`.
- Todo sv4 (también `int(r.fecha_int or 0)`: DA3), sv3, sv1, sv2, `orm_models.py`, infra.

## 4. Funciones

### 4.1 `application/services/fecha_linea.py` (capa application, pura)

```python
#: Prefijo del motivo (lo agrupa el modal de sv4, F-034 R19).
MOTIVO_FECHA_NO_VALIDA = "fecha_no_valida"
#: Primer dia que sv5 registra: sv3 da los partes de 2026 en adelante.
FECHA_MINIMA = 20260101
#: Dias por delante de hoy que se admiten (DA2, DA10).
DIAS_FUTURO = 62

def motivo_fecha_no_valida(fecha_int: object, *, hoy: date) -> str | None:
    """R1-R2: None si la fecha es valida; si no, el motivo entero."""
```

- Orden: no entero, booleano o `<= 0` ⇒ `la linea no tiene fecha`; `date(a, m, d)` lanza
  `ValueError` ⇒ `<valor> no es una fecha del calendario`; `< FECHA_MINIMA` ⇒ anterior;
  `> hoy + timedelta(days=DIAS_FUTURO)` ⇒ posterior. Plantilla:
  `f"{MOTIVO_FECHA_NO_VALIDA}: {detalle}; corrige la fecha en el portal y reaprueba"`.
- Constantes en código (DA6 A). No reutiliza `_fecha_valida` de `app.py` (interfaz, sin rango).
- **`DIAS_FUTURO` = 62 (DA10 A, antes 31)**: 31 de líneas anotadas por adelantado + ~31 del
  periodo de nómina (16 → 15) hasta el día de ajuste de F-056 (§5).

### 4.2 Paso 2a en `RegistroPipeline.preparar`

Justo después de `_con_empresa` (sin obra, el error de siempre):

```python
hoy = self._hoy()
por_fecha = {l.registro_id: m for l in lineas
             if (m := motivo_fecha_no_valida(l.fecha_int, hoy=hoy))}
validas = [l for l in lineas if l.registro_id not in por_fecha]
```

- `con_recurso`, `sin_recurso` y `horas_de_recursos` salen de `validas` (R5); 2b/2c siguen con
  su `omisiones` (el WARNING de 2c cuenta solo las del recurso). `ReglasRegistro` recibe
  `{**omisiones, **por_fecha}` y `decidir` corre sobre **todas**: la omisión previa da `omitir`
  con el motivo de fecha (R3, R4) y sin hermano (`_fin_mismo_dia` no llega a llamarse).
- WARNING (R11), si hay alguna: `"[registro] obra=%s lineas sin fecha valida=%s
  registro_ids=%s"` con `destino.codigo`, el número y los ids ordenados.
- `_evaluar`, `_ciz_de_racha` y `registrar` no cambian: una `omitir` no abre periodo ni busca
  synckey, racha o conflictos (R3, R5); sin nada que escribir no se llama a `escribir` (R7).

## 5. Relación con otras features

- **F-056** (franquicia): `_preparar` pasa la extra del día de ajuste por `preparar`; con fecha
  no válida sale `omitir` y `veredicto` da `no_editable` («no registrable (omitir:
  fecha_no_valida: …)»): **nada se escribe ni se da de alta** (R15); sus lecturas de E y de
  partes siguen (consultivas, DA11). `FranquiciaIn` ya da 422 a `0`/`null`/imposibles: F-055
  añade el rango. El día de ajuste va hasta ~30 días por delante de la línea (DA10).
- **F-060/F-062** (`MOVER_CIZ` encendido): un `fin` omitido no mueve el CIZ (lo moverá el
  siguiente `fin` válido); un `inicio` omitido no escribe ni CI* ni hermano.
- **F-034** y **F-053**: solo ven acciones `escribir`; sin choques en el día 0. Sin cambios.
- **F-046** (reajuste): las existentes llevan la fecha de Sigrid; una extra nueva con
  `fecha_int` nulo o 0 ya no se prepara («sin decision»); con otro valor no válido, `preparar`
  la da `omitir` y `veredicto_nueva` responde `no registrable (omitir: fecha_no_valida: …)` (R10).
- **F-019**: un mensual sin fecha válida sale `omitir`, no `dedicacion` (R4).
- **F-023 / F-031 / F-021 / F-038** (límite de filas, solo el cliente): idénticos (R12).
  **F-024** (comprobar): fuera. **F-054**: F-055 es la guarda de su DA5.

## 6. Gemelos, `porcentajes` y lista cerrada

- Sin gemelo: sv4 (`_parse_fecha_to_iso_int`), sv3 (`fecha_resolver.py`) y `FranquiciaIn`
  validan el calendario sin rango; no se copian. La lista cerrada no crece. Las copias de
  `porcentajes` (`estado_parte.py`, `cuenta_analitica.py`, `stmts_crear_parte`) no cambian.

## 7. Riesgos

- **Fecha legítima fuera de rango** (DA2, DA10): una línea de 2025 o con más de 62 días de
  adelanto saldría omitida. M1 lo mide; si aparece, se ajustan las constantes. El error
  contrario (escribir en 2016 o 2062) es irreversible. El rango sigue parando el año mal
  tecleado, que es lo que importa.
- **`hoy` en UTC**: un día como mucho; lo absorbe el margen. **Contrato**: `fecha_int`
  opcional en `LineaIn` (ensancha); mismas claves, un motivo nuevo.

## 8. Tests (sin red ni BBDD)

Fijos: `hoy = date(2026, 10, 31)` en los puros; en el pipeline, fechas de 2026 ya pasadas
(siempre válidas) y `monkeypatch` de `RegistroPipeline._hoy` en los de límite superior.
Helpers: `test_f002_pipeline_fases.py` (`_sigrid`, `_pipeline`, `_linea`, `OBRA`),
`test_f002_transfer_consumer.py` (`Montaje`), `test_f046_t22_pipeline_bordes.py`
(`_comprobar_nueva`), `test_f056_pipeline.py` (`_pipe`, `_pet`, `_ops`), `test_f062_*`.

| Test | Caso | Esperado |
|---|---|---|
| `test_f055_r1_sin_fecha[…]` | `None`, `0`, `-1`, `True`, `"20261020"`, `20261020.0` | `la linea no tiene fecha` |
| `test_f055_r1_no_calendario[…]` | `20261340`, `20260230`, `20260229`, `20261000`, `99999999` | `<valor> no es una fecha del calendario` |
| `test_f055_r1_limites` | `20251231` / `20260101`; hoy; hoy+62 / hoy+63 | anterior / `None`; `None`; `None` / posterior |
| `test_f055_r2_texto_del_motivo` | los cuatro detalles | plantilla exacta, prefijo antes del primer `:`, ASCII, ≤ 255 |
| `test_f055_r3_preflight_omite` | una línea `0` | `omitir`, motivo R2, `pf.partes == []`, `resumen` |
| `test_f055_r3_no_synckey_ni_conflictos` | `0` con una ajena `fec = 0` en un parte del fake; espía de `lineas_por_synckey` | su synckey no se pide, `conflictos == []`, la ajena intacta |
| `test_f055_r3_racha_y_hermano` | `MOVER_CIZ`: un `fin` `0` con `racha_registro_ids` y un `inicio` `0` con `ciz_mismo_dia` | `omitir`; `lineas_de_racha` no se pide; ni `mover` ni `fin_mismo_dia` |
| `test_f055_r4_manda_sobre_recurso[…]` | `0` + recurso inexistente / otra empresa / baja / sin recurso ni DNI / sin horas | motivo de fecha |
| `test_f055_r4_mensual_no_va_a_dedicacion` | `0`, mensual, interruptor encendido | `omitir`, `dedicacion == []` |
| `test_f055_r5_no_lee_sigrid` | `0` con DNI sin recurso y `20261340` con recurso; espías de `recursos_por_dni`, `datos_recursos` y `horas_de_recursos` | no se piden; `periodos_leidos` sin `(…, 0, 0)` ni mes 13; `altas == []` |
| `test_f055_r6_mezcla` | válida + `0` + `20261340` | la válida igual que sola; el WARNING de 2c no cuenta las de fecha |
| `test_f055_r7_ejecutar_sin_validas` | dos líneas `0` | `ok`, `escritas == []`, 2 `omitidas`, ningún `escribir` |
| `test_f055_r10_reajuste_extra_nueva` | `_comprobar_nueva(fecha_int=20261340)` | no editable, `fecha_no_valida` en el motivo, nada escrito |
| `test_f055_r11_warning_sin_nombres` | `caplog` con nombre y DNI ficticios | un WARNING con obra, número e ids; sin nombre ni DNI |
| `test_f055_r15_franquicia[…]` | `comprobar`/`ejecutar`, franquicia `activa`, día de ajuste hoy+63 / hoy+30 | `no_editable` con `fecha_no_valida` y `_ops` vacío / se escribe como hoy (DA10) |
| `test_f055_r8_tres_caminos` | preflight y ejecutar por `TestClient`, y la cola con `Montaje` | mismo motivo en `acciones` / `omitidas` |
| `test_f055_r9_null_y_ausente` | HTTP `null` y sin la clave; cola `null` y sin la clave | 200 / `ok`, `la linea no tiene fecha`, la otra escrita |
| `test_f055_r9_ano_mes_con_none` | `LineaEntrada(1, None)` | `ano == mes == 0` |

R12: suite de sv5 sin tocar un `assert` (los `2025…`/`20210101` de `test_f056_franquicia.py` y
`test_f023_*` no pasan por `preparar`). R13: `git diff dev --stat` de sv1–sv4 e `infra` vacío.

## 9. Verificaciones manuales (humano o líder)

- **M1 · solo lectura, antes de implementar (decide DA2/DA10)**. Base `partes`, como la M1 de
  F-054 (`PGOPTIONS` de solo lectura; `<servidor>`/`<usuario>` del Key Vault):
  `SELECT CASE WHEN r.fecha_int IS NULL OR r.fecha_int <= 0 THEN 'sin_fecha' WHEN r.fecha_int
  < 20260101 THEN 'anterior' ELSE 'posterior' END AS tipo, COALESCE(r.sigrid_estado, '') AS
  estado, COUNT(*) FROM parte_registros r JOIN parte_documents d ON d.id = r.document_id
  WHERE d.is_active AND r.deleted_at_utc IS NULL AND (r.fecha_int IS NULL OR r.fecha_int <
  20260101 OR r.fecha_int > <hoy + 62, AAAAMMDD>) GROUP BY 1, 2 ORDER BY 1, 2`. Sigrid (por
  sigrid-api `sql/read`, base `ruesma`): `SELECT COUNT(*) AS n FROM hmores WHERE synckey LIKE
  'partes:%' AND (fec < 20260101 OR mes NOT BETWEEN 1 AND 12)` y `SELECT COUNT(*) AS n FROM con
  WHERE tip = 35 AND cod LIKE 'PT0/%'`. **Esperado**: `sin_fecha` ≈ las 25 de F-054 (M2
  descartada; F-058/F-059 pueden moverla), ninguna `anterior`/`posterior` y los dos `n = 0`
  (incluye `partes:franquicia:*`). Una `anterior`/`posterior` sin estado se enseña al humano.
- **M2 · sv5 local en modo pruebas, sin escritura efectiva**: preparación de `progress/
  current.md` (F-053: `$env:OBRA_PRUEBAS_FORZAR = 'true'; python main.py`, `/health` con
  `modo_pruebas: True`, obra 0404, base `ruesma`; si no, PARA). Sin tocar 06, 08 ni 10/2026 ni
  usar `limpiar`. `registro_id` 990000551–553 y el recurso 2717792 (también el gruista de F-056
  con campo 0: se omite todo antes de leer y nada se escribe; su E y su X no cambian):
  ```powershell
  $l = @(@{ registro_id = 990000551; fecha_int = 0; recurso_ide = 2717792; tipo_hora = 'normal'; horas = 8 }, @{ registro_id = 990000552; fecha_int = 20261340; recurso_ide = 2717792; tipo_hora = 'normal'; horas = 8 }, @{ registro_id = 990000553; fecha_int = $null; recurso_ide = 2717792; tipo_hora = 'extra'; horas = 2 })
  $p = @{ obra = @{ codigo = '0404' }; lineas = $l; usuario = 'M2-F055' } | ConvertTo-Json -Depth 5
  Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/registro/preflight -ContentType 'application/json' -Body $p | ConvertTo-Json -Depth 6
  ```
  **Esperado**: `ok`, `forzada_pruebas: True`, las tres `omitir` con `fecha_no_valida: …`,
  `partes` vacío, `resumen.omitir = 3`. **Solo si es así**, el mismo `$p` a
  `/api/registro/ejecutar` ⇒ `ok: True`, `escritas` vacía, 3 `omitidas`; en la consola, el
  WARNING de R11 y «nada que escribir», **ningún `[sigrid-write]`**. Si alguna sale
  `escribir`, PARA y no ejecutes. **M2b** (opcional, con `franquicia: configurada`
  en `/health`): `/api/franquicia/comprobar`, `ajuste_id = 0`, 2717792, obra `0404`, día de
  ajuste > hoy + 62 ⇒ `no_editable` con `fecha_no_valida`.
- **M3 · tras `redeploy_partes.ps1 -Solo sv5` (lo pide el humano)**: M1 otra vez unos días
  después ⇒ ninguna línea sin fecha válida en `registrado`, `encolado` o `dedicacion`; las que
  se aprueben salen `omitido` con `fecha_no_valida` (el modal agrupa «fecha_no_valida · n»).

## 10. Documentación (texto propuesto)

- `docs/ARCHITECTURE.md`, semántica 6, tras «(0=null)»: «sv5 no escribe una línea sin fecha
  válida (F-055): `fecha_int` nulo, 0, imposible, anterior al 01/01/2026 o a más de 62 días de
  hoy se omite con `fecha_no_valida: …` antes de leer nada de Sigrid (también la cola, las
  extras nuevas del reajuste y la línea de ajuste de la franquicia).»
- `azure-apps/partes.md`, punto 6 de sv5: motivo `fecha_no_valida`, `fecha_int` admite `null`,
  la franquicia puede salir `no_editable` por él; nota informativa a `porcentajes`.

## 11. Decisiones abiertas (las aprueba el humano)

| DA | Pregunta | Alternativas | Recomendación |
|---|---|---|---|
| DA1 | Dónde va la guarda | **A**: paso 2a de `preparar`. B: en `LineaIn` y `_a_dominio` (rechazo). C: primera regla de `decidir` | **A**: sigue siendo el punto por el que pasan los cinco caminos (§1.3), antes de leer con la fecha; B tumba la petición entera; C llega tarde |
| DA2 | Qué es «fecha válida» | A: no nula, > 0 y del calendario. **B**: A + entre 01/01/2026 y hoy + N días. C: B + mismo mes que el documento | **B** (N en DA10): el año mal tecleado también abre partes irreversibles; C choca con mover líneas (F-044) |
| DA3 | ¿Y sv4? | **A**: sin cambios. B: sv4 no envía las líneas sin fecha. C: sv4 manda `null` en vez de 0 | **A**: el que escribe se protege; F-054 ya da la señal |
| DA4 | `fecha_int` nulo | A: solo el dominio lo tolera (la cola). **B**: A + `LineaIn` opcional. C: nada | **B**: los dos canales igual; una línea no tumba la petición |
| DA5 | Líneas sin obra | **A**: fuera (hoy fallan cerradas). B: omitir por línea | **A**: ya no escribe; cambiar el error es otra feature |
| DA6 | Límites | **A**: constantes en `fecha_linea.py`. B: `Settings` | **A**: sin manifiestos; cambiar el rango es un cambio de regla con su test |
| DA7 | `azure-apps` y `porcentajes` | **A**: motivo en `partes.md` + nota a `porcentajes`. B: nada | **A**: cambia lo que sv5 devuelve |
| DA8 | Sitio en la cola | — | **Superada**: hoy F-055 es prioridad 4 y la siguiente de la cola (F-052 6, F-057 7) |
| DA9 | Rigor | **A**: `critico`. B: `estandar` | **A**: decide qué escribe sv5 en Sigrid |
| DA10 (nueva) | Margen futuro con la franquicia (F-056) | **A**: `DIAS_FUTURO` = 62. B: 31 (la franquicia de un periodo futuro sale `no_editable` hasta acercarse). C: 31 y la franquicia sin rango (otra entrada a `preparar` o una excepción) | **A**: el día de ajuste va hasta ~30 días por delante de la línea, que a su vez puede ir 31 por delante; 62 sigue parando 2062 y no abre una excepción |
| DA11 (nueva) | Franquicia con fecha no válida | **A**: le basta `preparar` (`no_editable`, nada escrito; sus lecturas de E y de partes siguen). B: validar también en `FranquiciaPipeline` antes de leer | **A**: R5 es «no escribir ni dar de alta»; leer es consultivo, `FranquiciaIn` ya filtra 0/`null`/imposibles y no se toca F-056 |
