<!-- progress/impl_F-019.md -->
# F-019 · Horas de los mensuales a dedicación — informe del implementer

Rama `feature/F-019-mensuales-a-dedicacion`, un commit local por tarea
(T1 `4783e62` … T14 `47c0b64`, más el informe). Rigor **crítico**. Spec
aprobada el 2026-10-02 (DA1–DA8, DA4 opción 2 con R3 bis). T16–T18 son
MANUAL: comandos exactos en `progress/current.md`.

## 1. Qué cambió (por servicio)

- **sv5** (`services/partes-transfer`): ajuste `MENSUALES_A_DEDICACION`
  (default `false`); `HoraRecurso.es_mensual`, `AccionLinea.codigo_mes`,
  `Preflight.n_dedicacion`, `ResultadoRegistro.dedicacion`;
  `ReglasRegistro(mensuales_a_dedicacion=)` con `_decidir_mensual` (regla
  R0, docstring R1–R5 «con el interruptor apagado»); pipeline: lee el
  ajuste con `getattr(..., False)`, paso 6 también para `dedicacion` (R5),
  `res.dedicacion` antes de la salida temprana; `resultado_a_dict` y
  `_resultado_fallido` con la clave; `resumen.dedicacion` en el preflight.
- **sv4** (`services/partes-front`): `DedicacionBandejaOrm` (23 columnas,
  sin FK, índice `(anio, mes)`); `congelacion.py` (`ESTADO_DEDICACION`,
  motivos de línea, documento y borrado definitivo, `vive_fuera`,
  `motivo_borrado_definitivo`); repositorio: `_datos_bandeja`,
  `_upsert_bandeja`, `marcar_registros_sigrid(dedicacion=, prueba=,
  incidencias=)`, exclusión en `lineas_para_registro`,
  `retirar_de_dedicacion`, papelera y hard-delete con `vive_fuera`;
  `aplicar_resultado(..., incidencias=)`; consumidor y `main.py` con la
  tabla de clases; `app.py`: `_trazar` con la tabla, `_motivo_sin_lineas`,
  `POST /api/dedicacion/retirar`; `reparto_obras._estado`; plantillas de
  obra y trabajador; `app.js` (etiqueta, avisos, botón «Retirar»).
- **sv3**: copia byte a byte de `orm_models.py` y `ESTADOS_CONGELADOS`.
- **Raíz/infra/docs**: `infra/sql/01_dedicacion_lectura.sql`; guardianes
  F-010, F-015 R29 y F-024; `docs/ARCHITECTURE.md` (semántica 15, seis
  tablas); `docs/referencia/partes-proyecto.md` (§3.5, §5, §5.5 bis, §6.6);
  `azure-apps/partes.md` (commit local `c7ad8e9`, sin push).
- sv1 y sv2 sin tocar; sin dependencias nuevas; sin GRANT, despliegue,
  push ni escrituras en Sigrid o en la base `partes`.

## 2. Desviaciones de la spec (numeradas)

1. **D1 — R2 frente a R3 bis.** En una ficha `M*`+`HL*`+`HE*` (hoy 0 en
   Sigrid) R2 mandaría la ordinaria a dedicación y R3 bis lo prohíbe (hoy
   se escribe y no es incidencia). Manda R3 bis (innegociable del humano).
   `_decidir_mensual` devuelve `None` para lo no-incidencia que hoy se
   escribe: extra con `HE*` o ordinaria con `HL*`+`HE*`. Test
   `test_f019_r3bis_mensual_con_hl_y_he_sigue_escribiendo_ordinarias`.
2. **D2 — `resumen.dedicacion` (R7) solo si hay alguna.** Siempre presente
   rompía `test_f002_r4_preflight_del_endpoint_no_escribe` (compara el
   resumen clave a clave). Apagado, el contrato de F-002 queda idéntico.
3. **D3 — `dedicacion` fuera de la tupla `ESTADOS_CONGELANTES`** (design §4
   la ponía dentro): dos tests ajenos (F-004, F-024) fijan la tupla literal.
   Ningún código de producción la usa; la congelación va en
   `motivo_congelacion_linea/documento`.
4. **D4 — guardián de F-017 tocado**: `test_f017_todos_los_puntos_de_
   escritura_usan_el_helper` cuenta literalmente `_actor(request)` (14); R24
   exige una llamada más ⇒ 15, con su docstring.
5. **D5 — guardián de F-017 tocado**: `test_f017_r22_no_hay_ficheros_sql_
   de_migracion` prohibía cualquier `.sql`; R25 exige uno. Se admite solo
   `infra/sql/01_dedicacion_lectura.sql`; cualquier otro sigue fallando.
6. **D6 — `excluidas["dedicacion"]` solo si > 0** (como `incompatible` de
   F-025): los tests de F-022/F-024/F-025 comparan `excluidas` literal.
   `agregar_ejecucion` (varias obras) no junta `dedicacion` (rompía un test
   de F-022 y no lo pide la spec): el modal lo lee de cada grupo.
7. **D7 — tests extra**: `services/partes-persistencia/tests/test_f019_orm_
   bandeja.py` (la copia de sv3 del ORM necesita tests propios para la
   mutación) y los de `main.py`/consumidor en `test_f019_bandeja.py`.
8. **Decisión — `recurso_ide` de la fila**: el del resultado de sv5 (pudo
   resolverlo por DNI) y, si no viene, el de la línea; 0 si ninguno.

**D3, D4 y D5 tocan (o se apartan del design por) tests ajenos (T12 solo
preveía los tres guardianes de raíz): necesitan el visto bueno del humano.**

## 3. Fase RED (trazas reales)

Desde la carpeta del servicio; líneas `E`/resumen tal cual las dio pytest.

**R1 (T1, caracterización, ANTES de tocar `reglas_registro.py`)** —
`python -m pytest tests/test_f019_reglas.py -q` contra el código de dev:
```
..........................                                               [100%]
26 passed in 0.27s
```
(verde a propósito: fijan lo de hoy; siguen verdes al final.)

**R2, R3, R3 bis, R4 (T2)** — mismo comando, con los tests nuevos y sin
código:
```
E       TypeError: ReglasRegistro.__init__() got an unexpected keyword argument 'mensuales_a_dedicacion'
E       AttributeError: 'HoraRecurso' object has no attribute 'es_mensual'
40 failed, 26 passed in 1.24s
```
Tras la primera implementación, R3 bis cazó un fallo real (D1):
```
E           AssertionError: (1141, 807, ['HE', 'HL', 'M'], 'normal', None, 8.0)
E           assert ('escribir' == 'omitir' ... or ('escribir' == 'escribir' and False))
FAILED tests/test_f019_reglas.py::test_f019_r3bis_encender_solo_cambia_lo_permitido
```

**R5, R8 (T3)** — `python -m pytest tests/test_f019_pipeline.py -q`:
```
E       AssertionError: assert [] == [{'registro_i...mes': 'MCAP'}]
E       AssertionError: assert 'omitir' == 'dedicacion'
E       KeyError: 'dedicacion'
13 failed, 3 passed, 1 warning in 5.19s
```

**R15 (T5)** — raíz `python -m pytest tests/test_f024_borrado_no_congela_gemelos.py -q`,
sv3 `tests/test_f019_congelado.py`, sv4 `tests/test_f019_portal.py`:
```
E           AssertionError: sv3
E           assert False is True
FAILED tests/test_f024_borrado_no_congela_gemelos.py::test_f019_r15_dedicacion_congela_en_sv3_y_en_sv4
E       AssertionError: assert False is True
E        +  where False = esta_congelado('dedicacion', False)
E   ImportError: cannot import name 'ESTADO_DEDICACION' from 'application.services.congelacion'
```

**R9, R12, R13, R14 (T6)** — sv4 `python -m pytest tests/test_f019_bandeja.py -q`:
```
     15 E       TypeError: ParteReviewRepository.marcar_registros_sigrid() got an unexpected keyword argument 'dedicacion'
      1 E       AssertionError: Regex pattern did not match.      (R14)
16 failed, 5 passed in 3.47s
```

**R9, dos canales (T7)** — `-k "aplicar or canales or cola or consumidor or main"`:
```
E       TypeError: aplicar_resultado() got an unexpected keyword argument 'incidencias'
E       TypeError: construir_handler_resultados() got an unexpected keyword argument 'incidencias'
E       KeyError: 'dedicacion'
7 failed, 1 passed, 22 deselected, 1 warning in 8.61s
```

**R17 (T8)** — `python -m pytest tests/test_f019_portal.py -q -k "r17 or r18"`:
```
E       assert 200 == 422          (x3: preflight, ejecutar, encolar)
E       assert [1, 2] == [2]
E       KeyError: 'dedicacion'
8 failed, 1 passed, 24 deselected, 1 warning in 8.16s
```

**R21, R22 (T9)** — `-k "r21 or r22 or r23 or r24"`:
```
E       assert 404 == 422
E       AssertionError: assert 404 == 200
E       AttributeError: 'ParteReviewRepository' object has no attribute 'retirar_de_dedicacion'
12 failed, 32 deselected, 1 warning in 15.09s
```

**R26 (T11)** — raíz `python -m pytest tests/test_f019_sql_lectura.py -q`:
```
E       FileNotFoundError: [Errno 2] No such file or directory: '...\infra\sql\01_dedicacion_lectura.sql'
20 failed, 2 passed in 6.08s
```

Tras cada implementación, el mismo comando en verde (cifras en §6).

## 4. Qué se verificó (resultado real)

- R1/R3 bis: los 26 casos de caracterización siguen en verde con el
  interruptor apagado (por defecto y explícito); el producto de R3 bis
  (16 fichas × 20 líneas + sin recurso = 340 líneas) solo admite
  `omitir`→`dedicacion` e incidencia `escribir`→`dedicacion`, y los dos
  cambios aparecen (no es trivial).
- Dos canales (HTTP `aprobar/ejecutar` y `q-transfer-result`) dejan el
  mismo estado y la misma fila (salvo autor y fechas).
- R14: con la tabla borrada, `marcar_registros_sigrid` lanza y ninguna
  línea cambia (ni las `escritas` del mismo resultado).
- `node --check services/partes-front/static/app.js` OK. Plantillas
  parseadas y renderizadas por los tests de vistas (R19).

## 5. Mutación (campaña completa)

`python -m harness.mutacion --feature F-019 --workers 6 --timeout 600`,
17 ficheros, 581 líneas en alcance, SHA `47c0b64`, 6794,5 s. Informe:
`progress/mutacion_F-019.md`.

| Generados | Muertos | Supervivientes | Timeouts |
|---|---|---|---|
| 126 | 125 | 1 → 0 sin resolver | 0 |

Superviviente 1 (`app.py`, `include_in_schema=False` → `True` en
`/api/dedicacion/retirar`): **hueco real**, ningún test miraba
`/openapi.json`. Cerrado con
`test_f019_r21_la_ruta_no_se_publica_en_el_esquema` y verificado aplicando
el mutante a mano: `1 failed` (`'/api/dedicacion/retirar' not in {...}`);
con el original `1 passed`. No se relanzó la campaña entera (≈1 h 53 min).

Antes se cerraron por test los mutantes previsibles (retorno de
`_upsert_bandeja`, centinelas a 0, DDL literal de la bandeja en sv4 y sv3).

## 6. Evidencias

| Evidencia | Valor (medido el 2026-10-02, `bash harness/init.sh`) |
|---|---|
| Tests raíz | 445 passed, 1 skipped (59,2 s) |
| sv3 / sv4 / sv5 | 654 passed (7,9 s) / 1636 passed (280,1 s) / 357 passed (7,7 s) |
| Tests nuevos F-019 | sv5 88 (reglas 71 + pipeline 17); sv4 `bandeja` 32 + `portal` 56; sv3 14; raíz 22 + 4 en guardianes |
| Cobertura líneas cambiadas | **100,0 %** (201/201, umbral 80 %, nivel crítico) |
| Mutantes | 126 generados, 125 muertos, 1 superviviente (cerrado con test), 0 timeouts |
| Tiempo de la suite | el de arriba; la línea base de sv4 en la campaña, con 6 workers, 1082–1091 s |
| `bash harness/init.sh` | **ENTORNO LISTO** (EXIT 0); PUERTA TAMAÑO OK |

ruff: 589 avisos (557 antes; no bloquea). Los nuevos son de estilo en
tests (`noqa: E402` de los imports del medio, orden de imports).

## 7. Fuera del alcance (spec §9) y MANUAL pendiente

- Fuera: la feature espejo en `porcentajes` (leer la bandeja, propuesta
  del cuadrante, laborables, periodo cerrado, obras de otra empresa) y
  `azure-apps/dedicacion.md`; ejecutar el `GRANT` y desplegar.
- MANUAL (humano), comandos exactos en `progress/current.md`:
  **T16** M0 (lectura en PG antes de desplegar); **T17** sv3 → sv4 (dos
  pasadas de `redeploy_partes.ps1 -Solo`), M1, M2 (`psql ... -f
  infra/sql/01_dedicacion_lectura.sql`), sv5 con el interruptor apagado;
  **T18** M3 (encender cuando dedicación lea; retirar y reaprobar; apagar
  si falla). El JS solo lo verifica M3 en navegador.

## 8. Qué falta para cerrar

Review contra `CHECKPOINTS.md` y **decisión del humano sobre D3, D4 y D5**
(tests ajenos). Nada desplegado; `azure-apps` con commit local `c7ad8e9`.
