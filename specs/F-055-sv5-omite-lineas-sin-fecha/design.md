<!-- specs/F-055-sv5-omite-lineas-sin-fecha/design.md -->
# F-055 · sv5 omite las líneas sin fecha válida — Diseño

## 1. Estado actual (`dev` 2bfeab7, leído para esta spec)

### 1.1 Cómo llega la fecha a sv5

- sv4 `lineas_para_registro` (`infrastructure/database/parte_repository.py` l. 1873) manda
  `"fecha_int": int(r.fecha_int or 0)`: una línea sin fecha viaja con `0`. No filtra por
  fecha (solo `registrado`, `borrado_sigrid`, `dedicacion`, reparto e incompatibles).
- sv5 HTTP: `LineaIn.fecha_int: int` (`interface_adapters/api/app.py`); `null` da 422 a la
  petición entera. Cola: `_a_dominio` (`interface_adapters/queue/transfer_consumer.py`) pasa
  el valor tal cual a `LineaEntrada`; con `null`, `LineaEntrada.ano` (`int(None)`) revienta
  en `ReglasRegistro.decidir` y la petición sale `ok: false`.
- En sv5 no hay ninguna guarda de fecha: ni en `preparar`, ni en las reglas, ni en el cliente.

### 1.2 Qué haría sv5 hoy (sonda con `SigridFake`, aplicada en el scratchpad, sin commit)

| `fecha_int` | `ejecutar` con una línea normal de 8 h |
|---|---|
| `0` | `ok`, alta de `PT0/00001` con `ano = 0`, `mes = 0`; línea con `fec = 0` |
| `20261340` | `ok`, alta de `PT26/00001` del periodo **2026/13**; línea con `fec = 20261340` |

Con el cliente real es igual: `siguiente_cod_pt(0, emp)` da `PT0/00001` y `stmts_crear_parte`
no valida el periodo. En Sigrid `0` es NULL (`sigrid_api.md`); en un año mal tecleado
(2016) con los partes cerrados, F-031 crearía un **complementario** en ese año. Y el paso 7
buscaría choques en el día `0`: podría ofrecer pisar líneas ajenas sin fecha. Como en Sigrid
no se borra (F-053), cualquiera de esas altas sería basura permanente.

### 1.3 Dónde se decide cada línea

`RegistroPipeline.preparar` (`application/pipelines/registro_pipeline.py`): 2b recursos por
DNI (`elegir_por_dni` a la fecha), 2c verificación (`verificar_recurso`, alta a la fecha), 3
`horas_de_recursos`, 4 `ReglasRegistro.decidir`, donde la omisión previa (`omisiones`) manda
sobre todo (F-023) y sobre `dedicacion` (F-019). `preflight`, `ejecutar`, la cola
(`preparar` + `registrar`) y las extras nuevas del reajuste (`ReajustePipeline.
_preparar_nuevas`) pasan **todos** por `preparar`. `_evaluar` (pasos 5-7) solo mira acciones
`escribir` (y `dedicacion` para synckey).

## 2. Límite de servicio y encaje

- **sv5**: es quien escribe y el último punto antes del ERP; ya verifica ahí el recurso
  (F-023) por la misma razón. La regla vive en una función pura de `application/services/`,
  como `coherencia_recurso.py` y `parte_abierto.py`; el pipeline la aplica en un paso nuevo
  **2a** de `preparar`, antes de cualquier lectura que use la fecha (DA1 A).
- Sin responsabilidades nuevas ni otro servicio. sv4 no cambia (DA3 A): lo omitido vuelve
  `omitido` con su motivo, que no congela (semántica 10) y se arregla poniendo la fecha
  (F-043) y reaprobando. F-054 ya manda a revisión el parte sin fecha.

## 3. Ficheros

### A crear (todo en `services/partes-transfer/`)

- `application/services/fecha_linea.py` — regla pura (§4.1).
- `tests/test_f055_fecha_linea.py` — R1, R2.
- `tests/test_f055_pipeline_fecha.py` — R3–R7, R10, R11 (con `SigridFake`).
- `tests/test_f055_canales.py` — R8, R9 (HTTP con `TestClient` y cola con los fakes).

### A modificar

- `application/pipelines/registro_pipeline.py`: paso 2a en `preparar` (§4.2), `_hoy()`
  estático (`date.today()`) y el paso 2a en el docstring de cabecera.
- `domain/models/registro_models.py`: `LineaEntrada.fecha_int: Optional[int] = None` (sigue
  en segunda posición) y `ano` / `mes` con `int(self.fecha_int or 0)` (R9).
- `interface_adapters/api/app.py`: `LineaIn.fecha_int: Optional[int] = None` (R9, DA4 B).
- `docs/ARCHITECTURE.md` semántica 6 (§10) y `C:\Users\pgris\PycharmProjects\azure-apps\
  partes.md` punto 6 de sv5 y nota a `porcentajes` (§10, DA7; commit en ese repositorio).

### Que NO se tocan

- `reglas_registro.py` (la omisión previa ya manda), `coherencia_recurso.py` (gemelo de sv3,
  lista cerrada), `parte_abierto.py`, `pisado.py`, `estado_parte.py` y `cuenta_analitica.py`
  (copias literales en `porcentajes`), `reajuste_pipeline.py`, `reajuste_lineas.py`,
  `comprobacion_lineas.py`, `sigrid_write_client.py`, `transfer_consumer.py`,
  `resultado_json.py`, `prueba_escritura_sigrid.py`.
- Todo sv4 (también `int(r.fecha_int or 0)`: DA3), sv3, sv1, sv2, `orm_models.py`, infra.

## 4. Funciones

### 4.1 `application/services/fecha_linea.py` (capa application, pura)

```python
#: Prefijo del motivo (lo agrupa el modal de sv4, F-034 R19).
MOTIVO_FECHA_NO_VALIDA = "fecha_no_valida"
#: Primer dia que sv5 registra: sv3 da los partes de 2026 en adelante.
FECHA_MINIMA = 20260101
#: Dias por delante de hoy que se admiten (incidencias anotadas antes).
DIAS_FUTURO = 31

def motivo_fecha_no_valida(fecha_int: object, *, hoy: date) -> str | None:
    """R1-R2: None si la fecha es valida; si no, el motivo entero."""
```

- Orden: no entero, booleano o `<= 0` ⇒ `la linea no tiene fecha`; `date(a, m, d)` lanza
  `ValueError` ⇒ `<valor> no es una fecha del calendario`; `< FECHA_MINIMA` ⇒ anterior;
  `> hoy + timedelta(days=DIAS_FUTURO)` ⇒ posterior. Plantilla:
  `f"{MOTIVO_FECHA_NO_VALIDA}: {detalle}; corrige la fecha en el portal y reaprueba"`.
- Constantes en código y no en `Settings` (DA6 A): sin manifiestos ni `.env`.

### 4.2 Paso 2a en `RegistroPipeline.preparar`

Justo después de `_con_empresa` (la obra se sigue resolviendo primero: sin obra, el error de
siempre):

```python
hoy = self._hoy()
omisiones = {l.registro_id: m for l in lineas
             if (m := motivo_fecha_no_valida(l.fecha_int, hoy=hoy))}
validas = [l for l in lineas if l.registro_id not in omisiones]
```

- `con_recurso`, `sin_recurso` y la lista de `horas_de_recursos` salen de `validas`, no de
  `lineas` (R5); los pasos 2b/2c **añaden** a `omisiones` sin pisar las de fecha (no las
  ven). `ReglasRegistro.decidir` sigue corriendo sobre **todas** las líneas: la omisión
  previa da `omitir` con el motivo de fecha (R3, R4), con `ano`/`mes` de la propia línea.
- El WARNING de 2c («omitidas por el recurso») debe seguir contando solo las del recurso: si
  `omisiones` ya trae las de fecha, se separan (p. ej. un dict propio de 2b/2c que se fusiona).
- WARNING (R11), si hay alguna: `"[registro] obra=%s lineas sin fecha valida=%s
  registro_ids=%s"` con `destino.codigo`, el número y los ids ordenados.
- `_evaluar` y `registrar` no cambian: una `omitir` no abre periodo ni se consulta (R3, R5);
  con nada que escribir, `registrar` vuelve antes de `escribir` (R7, ya hoy).

## 5. Relación con otras features

- **F-034** (`parte_abierto.py`, relectura): solo ve `escritas`; una línea omitida antes no
  llega. Sin cambios.
- **F-053** (pisado): el paso 7 solo cruza acciones `escribir`; ya no se buscan choques en el
  día 0 (§1.2). Sin cambios.
- **F-046** (reajuste): las existentes llevan la fecha de Sigrid; una extra nueva con
  `fecha_int` nulo o 0 ya no se prepara («sin decision», test de F-046 T22); con otro valor
  no válido, `preparar` la da `omitir` y `veredicto_nueva` responde `no registrable (omitir:
  fecha_no_valida: …)` (R10). **No hay reajuste que tocar**: lo cubre el paso 2a.
- **F-019**: un mensual sin fecha válida sale `omitir`, no `dedicacion` (R4): no llega a la
  bandeja de `porcentajes` una fila con `anio = 0`.
- **F-023 / F-031 / F-021**: con fecha válida, idénticos (R12).
- **F-024** (`/api/registro/comprobar`): solo lectura de líneas ya registradas; fuera.

## 6. Gemelos, `porcentajes` y lista cerrada

- `fecha_linea.py` no tiene gemelo: sv4 valida el calendario al editar la fecha
  (`_parse_fecha_to_iso_int`) y sv3 la resuelve (`fecha_resolver.py`), pero son reglas
  distintas (sin rango) y no se copian. La lista cerrada de `CLAUDE.md` no crece.
- No cambian `estado_parte.py`, `cuenta_analitica.py` ni `stmts_crear_parte` (copias de
  `porcentajes`): su `test_f037_copias_partes.py` sigue en verde. Nota informativa en
  `azure-apps/partes.md` (DA7): su `dedicacion-transfer` puede adoptar la misma guarda.

## 7. Riesgos y decisiones

- **Fecha legítima fuera de rango** (DA2): una línea de 2025 o con más de 31 días de
  adelanto saldría omitida. M1 lo mide antes de implementar; si aparece, se ajustan las
  constantes. El error contrario (escribir en 2016 o 2062) es irreversible.
- **`hoy` del contenedor en UTC**: el margen de 31 días absorbe la hora de diferencia.
- **Contrato**: `fecha_int` pasa a opcional en HTTP; ensancha (lo que hoy entra, entra
  igual). La respuesta tiene las mismas claves; solo aparece un motivo nuevo.
- Descartadas: validar en los adaptadores (DA1 B: 422 o petición fallida por una línea, y
  la cola no lo ve igual) y en `decidir` (DA1 C: 2b/2c ya habrían leído con fecha 0 y su
  omisión de recurso taparía la de fecha).

## 8. Tests (sin red ni BBDD)

Fijos: `hoy = date(2026, 10, 22)` en los puros; en el pipeline, fechas de 2026 ya pasadas
(siempre válidas) y `monkeypatch` de `RegistroPipeline._hoy` en los de límite superior.
Helpers de `tests/test_f002_pipeline_fases.py` (`_sigrid`, `_pipeline`, `_linea`, `OBRA`).

| Test | Caso | Esperado |
|---|---|---|
| `test_f055_r1_sin_fecha[…]` | `None`, `0`, `-1`, `True`, `"20261020"`, `20261020.0` | detalle `la linea no tiene fecha` |
| `test_f055_r1_no_calendario[…]` | `20261340`, `20260230`, `20260229`, `20261000`, `99999999` | `<valor> no es una fecha del calendario` |
| `test_f055_r1_limites` | `20251231` / `20260101`; hoy; hoy+31 / hoy+32 | anterior / `None`; `None`; `None` / posterior |
| `test_f055_r2_texto_del_motivo` | los cuatro detalles | plantilla exacta, prefijo antes del primer `:`, ASCII, ≤ 255 |
| `test_f055_r3_preflight_omite` | una línea `0` | `omitir`, motivo R2, `pf.partes == []`, `resumen` |
| `test_f055_r3_no_synckey_ni_conflictos` | `0` con una línea ajena `fec = 0` en un parte del fake; espía de `lineas_por_synckey` | su synckey no se pide, `conflictos == []`, la ajena intacta |
| `test_f055_r4_manda_sobre_recurso[…]` | `0` + recurso inexistente / otra empresa / baja / sin recurso ni DNI / sin horas | motivo de fecha |
| `test_f055_r4_mensual_no_va_a_dedicacion` | `0`, mensual, interruptor encendido | `omitir`, `dedicacion == []` |
| `test_f055_r5_no_lee_sigrid` | `0` con DNI sin recurso y `20261340` con recurso; espías de `recursos_por_dni` y `horas_de_recursos` | no se piden, ni salen en `recursos_leidos`; `periodos_leidos` sin `(…, 0, 0)` ni mes 13; `altas == []` |
| `test_f055_r6_mezcla` | válida + `0` + `20261340` | la válida igual que sola (acciones, `altas`, `escritas`) |
| `test_f055_r7_ejecutar_sin_validas` | dos líneas `0` | `ok`, `escritas == []`, 2 `omitidas`, ningún `escribir` |
| `test_f055_r10_reajuste_extra_nueva` | `_comprobar_nueva(fecha_int=20261340)` de F-046 T22 | no editable, `fecha_no_valida` en el motivo, nada escrito |
| `test_f055_r11_warning_sin_nombres` | `caplog` con nombre y DNI ficticios | un WARNING con obra, número e ids; sin nombre ni DNI |
| `test_f055_r8_tres_caminos` | preflight y ejecutar por `TestClient`, y la cola con `Montaje` de F-002 | mismo motivo en `acciones` / `omitidas` |
| `test_f055_r9_null_y_ausente` | HTTP `null` y sin la clave; cola `null` y sin la clave | 200 / resultado `ok`, motivo `la linea no tiene fecha`, la otra línea escrita |
| `test_f055_r9_ano_mes_con_none` | `LineaEntrada(1, None)` | `ano == mes == 0` |

R12: la suite de sv5 (hoy todas las fechas de sus tests son de 2026 y pasadas) sin tocar un
`assert`. R13: `git diff dev --stat -- services/partes-front services/partes-persistencia
services/partes-email services/partes-api infra` vacío.

## 9. Verificaciones manuales (humano o líder)

- **M1 · solo lectura, antes de implementar (decide DA2)**. Base `partes`, como la M1 de F-054
  (`PGOPTIONS` de solo lectura; `<servidor>`/`<usuario>` del Key Vault):
  `SELECT CASE WHEN r.fecha_int IS NULL OR r.fecha_int <= 0 THEN 'sin_fecha' WHEN r.fecha_int
  < 20260101 THEN 'anterior' ELSE 'posterior' END AS tipo, COALESCE(r.sigrid_estado, '') AS
  estado, COUNT(*) FROM parte_registros r JOIN parte_documents d ON d.id = r.document_id
  WHERE d.is_active AND r.deleted_at_utc IS NULL AND (r.fecha_int IS NULL OR r.fecha_int <
  20260101 OR r.fecha_int > <hoy + 31, AAAAMMDD>) GROUP BY 1, 2 ORDER BY 1, 2`. Sigrid (por
  sigrid-api `sql/read`, base `ruesma`): `SELECT COUNT(*) AS n FROM hmores WHERE synckey LIKE
  'partes:%' AND (fec < 20260101 OR mes NOT BETWEEN 1 AND 12)` y `SELECT COUNT(*) AS n FROM con
  WHERE tip = 35 AND cod LIKE 'PT0/%'`. **Esperado**: `sin_fecha` = las 25 de F-054, ninguna
  `anterior`/`posterior` y los dos `n = 0`. Si sale alguna `anterior`/`posterior` con estado
  vacío, se enseña al humano antes de fijar las constantes.
- **M2 · sv5 local en modo pruebas, sin escritura efectiva**: preparación de `progress/
  current.md` (F-053: `$env:OBRA_PRUEBAS_FORZAR = 'true'; python main.py`, `/health` con
  `modo_pruebas: True`, obra 0404, base `ruesma`; si no, PARA). Sin tocar 06, 08 ni 10/2026 ni
  usar `limpiar`. Con `registro_id` sintéticos 990000551–553 y el recurso de pruebas de F-053:
  ```powershell
  $l = @(@{ registro_id = 990000551; fecha_int = 0; recurso_ide = 2717792; tipo_hora = 'normal'; horas = 8 }, @{ registro_id = 990000552; fecha_int = 20261340; recurso_ide = 2717792; tipo_hora = 'normal'; horas = 8 }, @{ registro_id = 990000553; fecha_int = $null; recurso_ide = 2717792; tipo_hora = 'extra'; horas = 2 })
  $p = @{ obra = @{ codigo = '0404' }; lineas = $l; usuario = 'M2-F055' } | ConvertTo-Json -Depth 5
  Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/registro/preflight -ContentType 'application/json' -Body $p | ConvertTo-Json -Depth 6
  ```
  **Esperado**: `ok`, `forzada_pruebas: True`, las tres `omitir` con `fecha_no_valida: …`,
  `partes` vacío, `resumen.omitir = 3`. **Solo si es así**, el mismo `$p` a
  `/api/registro/ejecutar` ⇒ `ok: True`, `escritas` vacía, 3 `omitidas`; en la consola, el
  WARNING de R11 y «nada que escribir», **ningún `[sigrid-write]`**. Si alguna sale
  `escribir`, PARA y no ejecutes.
- **M3 · tras `redeploy_partes.ps1 -Solo sv5` (lo pide el humano)**: M1 otra vez unos días
  después ⇒ ninguna línea sin fecha válida en `registrado`, `encolado` o `dedicacion`; las que
  se aprueben salen `omitido` con `fecha_no_valida` (el modal agrupa «fecha_no_valida · n»).

## 10. Documentación (texto propuesto)

- `docs/ARCHITECTURE.md`, semántica 6, tras «(0=null)»: «sv5 no escribe una línea sin fecha
  válida (F-055): `fecha_int` nulo, 0, imposible, anterior al 01/01/2026 o a más de 31 días de
  hoy se omite con `fecha_no_valida: …` antes de leer nada de Sigrid (también la cola y las
  extras nuevas del reajuste).»
- `azure-apps/partes.md`, punto 6 de sv5: el motivo `fecha_no_valida` y que `fecha_int` admite
  `null`; y una nota a `porcentajes` (informativa, como la de F-034).

## 11. Decisiones abiertas (las aprueba el humano)

| DA | Pregunta | Alternativas | Recomendación |
|---|---|---|---|
| DA1 | Dónde va la guarda | **A**: paso 2a de `preparar`. B: en `LineaIn` y `_a_dominio` (rechazo). C: primera regla de `decidir` | **A**: un punto por el que pasan los cuatro caminos, antes de leer con la fecha; B tumba la petición entera; C llega tarde (§7) |
| DA2 | Qué es «fecha válida» | A: no nula, > 0 y del calendario. **B**: A + entre 01/01/2026 y hoy + 31 días. C: B + mismo mes que el documento | **B**: el año mal tecleado (2016, 2062) también abre partes irreversibles; C exige mandar la fecha del documento y choca con mover líneas (F-044) |
| DA3 | ¿Y sv4? | **A**: sin cambios. B: sv4 no envía las líneas sin fecha (`excluidas.sin_fecha`). C: sv4 manda `null` en vez de 0 | **A**: el que escribe se protege; F-054 ya da la señal; B y C son sv4 y otro despliegue para lo mismo |
| DA4 | `fecha_int` nulo | A: solo el dominio lo tolera (la cola), HTTP sigue con 422. **B**: A + `LineaIn` opcional. C: nada | **B**: los dos canales igual (como `resultado_json`), una línea no tumba la petición |
| DA5 | Líneas sin obra | **A**: fuera (hoy fallan cerradas, nada escrito). B: omitir por línea con motivo | **A**: ya no escribe; cambiar el error es otra feature |
| DA6 | Límites | **A**: constantes en `fecha_linea.py`. B: `Settings` y variables de entorno | **A**: sin manifiestos; cambiar el rango es un cambio de regla con su test |
| DA7 | `azure-apps` y `porcentajes` | **A**: motivo en `partes.md` + nota informativa a `porcentajes`. B: nada | **A**: cambia lo que sv5 devuelve (regla del dueño del documento) |
| DA8 | Sitio en la cola (hoy F-049 en curso → F-054 → F-047 → F-052) | **A**: prioridad 4, detrás de F-054 (desempata el id). B: 5, detrás de F-047. C: 6, detrás de F-052 | **A**: pequeña, solo sv5, y evita un daño irreversible con 15 líneas aprobables hoy |
| DA9 | Rigor | **A**: `critico`. B: `estandar` | **A**: decide qué escribe sv5 en Sigrid |
