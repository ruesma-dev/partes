<!-- progress/review_F-029.md -->
Revisión completa (pasada 1) · `git diff dev..HEAD` hasta `c1685d0`

# F-029 · Review

**Veredicto: APPROVED**

**Nivel de rigor:** `estandar`, declarado en `harness/features.json`. Exige
fase RED, cobertura de lo cambiado y campaña de mutación con los
supervivientes analizados. `sdd=false`: se valida contra los `acceptance`.

## Qué se ha comprobado (con resultado real)

- `bash harness/init.sh`: **ENTORNO LISTO**. Raíz 445 passed, 1 skipped;
  sv1–sv5 en verde; `PUERTA COBERTURA: N/A (F-029 no cambia líneas Python de
  producción frente a dev)`; `PUERTA TAMAÑO` OK (impl 176/220).
- Suite de sv3 ejecutada a mano y sin caché (`python -m pytest -q -p
  no:cacheprovider` en `services/partes-persistencia`): **666 passed**.
- **Alcance del diff**: en `services/` solo cambian
  `config/empresas_membrete.yaml` (+5: alias `RUΞSMA` con comentario),
  `tests/test_f029_alias_logo.py` (nuevo) y los 3 asserts de D1. Ni código
  de producción ni otros servicios. El YAML es UTF-8 sin BOM y
  `construir_alias_empresas` lo lee con `encoding="utf-8"`.
- **Nadie más lee la tabla**: `grep empresas_membrete` en `*.py`, `*.yaml`,
  `*.ps1`, `*.toml` y Dockerfiles da solo sv3 (`settings.py`, `app.py`,
  `empresa_membrete.py` y tests). sv2 copia el membrete tal cual: no
  necesita cambio, y el explore muestra que hoy Gemini transcribe `ruesma`.
- **`parsear_alias` sobre el YAML real** devuelve
  `{1: ["RUESMA", "RUΞSMA"], 28: ["PORSAN"]}` (lo fija R7 de F-023).

### Falsos positivos y regla de «varias»

El alias normaliza a «ru sma» y casa como dos palabras completas seguidas
(`f" {alias} " in f" {normal} "`). Además de los 5 controles del test, he
probado contra la tabla real: `Grupo Rusma`, `ru3sma`, `Brus Masa`,
`Perú S.M.A.`, `RU S.M.A.`, `Cru Smart`, `Peru sma` → todos `sin_alias`.
Casan con la 1, y es lo esperable: `RUЕSMA` (E cirílica, otra lectura del
logotipo), `ruΞsma\nConstrucciones` y `ru' sma`. Lo que el implementer
declara que no protege («RU SMA», «ru-sma») es correcto y su riesgo es
asumible: ningún texto de parte conocido lo produce.
«Varias» intacta: `PORSAN E HIJOS ruΞsma` y
`Construcciones Ruesma, S.A. / PORSAN` → `(None, "varias")`.

### D1: no relaja la vigilancia de F-023

Los tres asserts siguen comparando la tabla **entera** con un literal, y
siguen fallando con cualquier cambio de contenido. Mi campaña lo confirma:
los 9 mutantes del YAML tumban los 3 tests de D1 (3 failed, 30 passed en
cada uno). Sigue habiendo guardián de que la tabla versionada carga
(`test_f023_r7`, `test_f023_da3_por_defecto...`) y llega al conciliador
(`test_f023_r25`). El de que resuelve 1 y 28 lo pone F-029 con la tabla real
(`test_f029_porsan_sigue_siendo_la_28` y el parametrizado de la 1).

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base presentes.
- **C2** [x] una sola `in_progress` (F-029) · [x] rama
  `feature/F-029-alias-logo-ruesma` · [x] `current.md` con F-029 arriba (las
  secciones de abajo son verificaciones manuales pendientes de features ya
  desplegadas, que estaban antes y no introduce F-029) · [x] las `done`
  tienen su resumen en `history.md` (F-029 no cambia ninguna `done`).
- **C3** [x] hexagonal: no hay código de producción y la config se queda en
  `config/` · [x] primera línea con ruta en el test y en el YAML · [x] sin
  prints, sin TODOs, sin secretos, sin dependencias nuevas · [x] trampas del
  dominio: no toca recursos, incidencias ni `orm_models.py`.
- **C3 bis** N/A: no toca `docs/referencia/` (los ficheros añadidos son el
  test, `impl_F-029.md` y `explore_F-029_membrete.md`; el explore no trae
  datos de personas ni secretos: la API key se leyó del Key Vault a una
  variable de proceso y no se escribió).
- **C4** [x] cada `acceptance` tiene test (tabla abajo) y pasan · [x] sin red
  ni BBDD: `EmpresaRow` sintéticos + YAML local · [x] M1 manual en
  `current.md`. Es observacional, sin comando; ver observación 2.
- **C4 bis**
  - [x] `rigor` declarado: `estandar`.
  - [x] **Fase RED** reproducida por mí sobre una copia aislada del commit
    T1 `571a386` (`git archive` al scratchpad): **4 failed, 8 passed**, las
    mismas 4 trazas que pega el informe (3× `sin_alias`, y el caso varias
    daba `(28, 'membrete')`).
  - [x] **Cobertura**: N/A con motivo impreso por `init.sh` (no hay líneas
    Python de producción cambiadas).
  - [x] **Mutación automática**: alcance vacío, que he recalculado con
    `harness.alcance.alcance_de_feature("F-029")`: `lineas={}`, origen
    `rama`, `179010a..feature/F-029-alias-logo-ruesma`. El cero es
    legítimo por diseño: el diff no trae ningún `.py` de producción. La
    prueba de control de `generar_mutantes` sin exclusión no aplica porque
    no hay Python que mutar (solo YAML y tests). No existe
    `mutacion_F-029.md` porque la herramienta no lo escribe con alcance
    vacío. Son N/A justificados: informe de la herramienta, tiempo y
    coste por mutante, cabecera «CAMPAÑA NO VÁLIDA», RM1 y RM2.
  - [x] **Campaña MANUAL sustituta** (8 filas, con el texto original →
    mutado y el nº de fallos). La he **reproducido entera** al pie de la
    letra en una copia aislada (script en el scratchpad, el árbol real queda
    intacto). Coincide fila a fila contra `test_f029_alias_logo.py`: M1 4,
    M2 5, M3 4, M4 2, M5 2, M6 2, M7 2 fallos; M8 (`RU-SMA`) sobrevive.
    He añadido M9 (`RUΞSMA`→`RU≡SMA`): sobrevive igual, por la misma razón.
  - [x] Superviviente M8 analizado: equivalente para el resolutor (los dos
    normalizan a «ru sma»). Con rigor `estandar` basta la justificación
    escrita. **RM3**: no sale muerto en el fichero de F-029; sí lo tumban los
    asserts literales de D1, porque cambia la salida de `parsear_alias`. Es
    otro observable (la tabla, no la resolución), así que no invalida nada.
  - [x] **RM5** N/A por nivel (`estandar`) · [x] **RM6** N/A: no se ha
    quitado ninguna guarda (no hay código de producción).
  - [x] La sección «Evidencias» trae tests, cobertura (N/A), mutantes
    (0 automáticos, 8 manuales con 1 equivalente) y tiempos de la suite.
    El dato de workers aplica solo a la campaña automática, que fue vacía.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] `tasks.md` N/A (`sdd=false`): commits `F-029 T1..T3` y
  `F-029: ...` · [x] árbol limpio (`git status` vacío antes de esta
  revisión; después solo aparece este informe; todo lo temporal está en el
  scratchpad) · [x] `features.json`
  dice `in_progress`, que es el estado real hasta que el líder cierre.

## Cobertura acceptance → test

| Criterio | Test |
|---|---|
| A1 `ruΞsma`, `RUΞSMA`, `ru≡sma`, `RUESMA`, «Construcciones Ruesma S.A.» → 1 | `test_f029_el_logotipo_y_el_nombre_de_ruesma_son_la_empresa_1` (5 casos) |
| A2 Porsan → 28 | `test_f029_porsan_sigue_siendo_la_28` |
| A3 logotipo + Porsan → `varias` | `test_f029_logotipo_de_ruesma_con_nombre_de_porsan_da_varias` |
| A4 suite de sv3 en verde | 666 passed (ejecución propia) |
| (extra) sin falsos positivos con «ru»/«sma» sueltos | `test_f029_el_alias_del_logotipo_no_dispara_con_ru_o_sma_sueltos` (5) |

## Observaciones (no bloquean)

1. La tabla manual de mutantes no trae la **línea** del YAML. No impide
   reproducirla porque cada literal aparece una sola vez en el fichero, pero
   el checkpoint pide «fichero y línea».
2. M1 manual sin comando: se podría concretar como «buscar
   `[empresa-membrete]` con `sin_alias` y texto `ru…sma` en los logs de sv3
   tras el despliegue». Según el explore, hoy Gemini transcribe `ruesma`, así
   que el alias es una red de seguridad y M1 quizá no se dé pronto.
3. Fuera de alcance (explore): PDF multipágina → una sola cabecera en sv2.

## Automejora (propuesta, no aplicada)

- En `CHECKPOINTS.md` C4 bis, campaña manual: cuando lo mutado sea
  configuración (YAML/JSON) en vez de Python, que cada mutante se ejecute
  contra **todos** los tests que leen ese fichero, no solo contra los de la
  feature. Así un «superviviente equivalente» que tumban otros tests
  (aquí M8 con D1) queda visible en la tabla y no solo en la review.
