<!-- progress/impl_F-029.md -->
# F-029 · Informe del implementer

**Feature**: el logotipo de Ruesma (ruΞsma) se reconoce como empresa 1 en el
membrete. sdd=false, rigor `estandar`, solo sv3 (`services/partes-persistencia`).
Rama `feature/F-029-alias-logo-ruesma`. Fecha: 2026-10-05.

## Qué cambió

| Fichero | Cambio |
|---|---|
| `services/partes-persistencia/config/empresas_membrete.yaml` | Empresa 1: alias nuevo `RUΞSMA` (Xi griega), con un comentario de 4 líneas sobre el motivo (la normalización convierte la Xi en espacio: el alias queda «ru sma», igual que el logotipo «ruΞsma» y la variante «ru≡sma»). |
| `services/partes-persistencia/tests/test_f029_alias_logo.py` | Nuevo: 12 tests contra la tabla VERSIONADA real (`parsear_alias` + `ResolutorEmpresa` con empresas sintéticas válidas 1 y 28). |
| `services/partes-persistencia/tests/test_f023_empresa_membrete.py` | Desviación D1: 1 assert que fijaba el contenido literal de la tabla. |
| `services/partes-persistencia/tests/test_f023_wiring_sv3.py` | Desviación D1: 2 asserts que fijaban el contenido literal de la tabla. |
| `progress/current.md` | Entrada F-029 (en curso, M1 manual). |

**No se han tocado**: código de producción (`text_match.py`,
`empresa_membrete.py`), el prompt ni el esquema de sv2, ni los demás servicios.

Commits:
- `571a386` F-029 T1: tests del logotipo de Ruesma contra la tabla versionada (fase RED)
- `f1961c4` F-029 T2: alias del logotipo RUΞSMA para la empresa 1 en la tabla del membrete
- (este informe y `progress/current.md` van en el commit T3)

## Decisiones de diseño

- **Solo configuración**: es la solución que aprobó el humano. El alias
  se escribe con la Xi (`RUΞSMA`) en vez de con la forma ya normalizada
  (`RU SMA`) porque así queda claro en la tabla qué texto impreso se
  quiere reconocer; los dos normalizan igual (ver mutante M8, equivalente).
- `RUESMA` se mantiene el primero de la lista: se sigue reconociendo el
  nombre en texto («Construcciones Ruesma S.A.»).
- El YAML se lee con `encoding="utf-8"` (`interface_adapters/api/app.py`,
  `construir_alias_empresas`), así que la Xi no depende del locale del
  contenedor. Comprobado: el fichero se guarda como UTF-8.

## Desviaciones

- **D1**: tres asserts de F-023 comparaban la tabla versionada con un literal
  (`{1: ["RUESMA"], 28: ["PORSAN"]}`): uno en
  `test_f023_r7_la_tabla_versionada_trae_las_dos_empresas_activas` y dos en
  `test_f023_wiring_sv3.py` (`test_f023_da3_por_defecto_se_lee_la_tabla_versionada`,
  `test_f023_r25_el_conciliador_usa_el_indice_del_proveedor`). Ajuste
  mínimo: la 1 pasa a `["RUESMA", "RUΞSMA"]`, con un comentario `F-029`. Es
  inevitable: esos tests existen para fijar el contenido de la tabla, y F-029
  cambia el contenido. `test_f023_pipeline_match.py` usa sus propios alias en
  línea y no lee la tabla: no se toca.

## Qué garantiza la regla de palabras completas (documentado en el test)

El alias nuevo casa si el texto normalizado contiene **«ru» y «sma» como dos
palabras seguidas**. Comprobado que NO dispara con:
`Rusma Obras` (una sola palabra), `ru smart` («sma» no es palabra completa),
`Peru Smash`, `gru sma` («ru» no es palabra completa) y `ru obras sma` (no
seguidas): los cinco dan `(None, "sin_alias")`.

Lo que **no** protege: un texto que traiga literalmente las palabras «ru» y
«sma» juntas («RU SMA», «ru-sma») casaría con la 1. Se acepta: no hay otra
empresa ni otro texto de parte conocido que lo produzca.

## Fase RED

Test escrito antes del cambio en el YAML. Comando (desde
`services/partes-persistencia`):

```
python -m pytest tests/test_f029_alias_logo.py -q -p no:cacheprovider --tb=line
```

Salida real ANTES del alias (extracto, sin recortar las líneas de fallo):

```
C:\Users\pgris\PycharmProjects\partes\services\partes-persistencia\tests\test_f029_alias_logo.py:59: AssertionError: assert (None, 'sin_alias') == (1, 'membrete')
E   AssertionError: assert (28, 'membrete') == (None, 'varias')
      At index 0 diff: 28 != None
C:\Users\pgris\PycharmProjects\partes\services\partes-persistencia\tests\test_f029_alias_logo.py:68: AssertionError: assert (28, 'membrete') == (None, 'varias')
=========================== short test summary info ===========================
FAILED tests/test_f029_alias_logo.py::test_f029_el_logotipo_y_el_nombre_de_ruesma_son_la_empresa_1[ru\u039esma]
FAILED tests/test_f029_alias_logo.py::test_f029_el_logotipo_y_el_nombre_de_ruesma_son_la_empresa_1[RU\u039eSMA]
FAILED tests/test_f029_alias_logo.py::test_f029_el_logotipo_y_el_nombre_de_ruesma_son_la_empresa_1[ru\u2261sma]
FAILED tests/test_f029_alias_logo.py::test_f029_logotipo_de_ruesma_con_nombre_de_porsan_da_varias
4 failed, 8 passed in 0.78s
```

Lectura: los tres textos del logotipo daban `sin_alias` (el bug del
hallazgo) y el caso «logotipo + Porsan» resolvía **28** en vez de `varias`
(el logotipo no contaba, así que solo casaba Porsan: en una obra gemela el
parte se habría ido a Porsan por el membrete). Los 8 que ya pasaban son los
que deben pasar con o sin el alias: `RUESMA`, «Construcciones Ruesma S.A.»,
Porsan y los 5 controles de palabras completas.

Después del alias (mismo comando, más los dos ficheros de F-023 ajustados):

```
python -m pytest tests/test_f029_alias_logo.py tests/test_f023_empresa_membrete.py tests/test_f023_wiring_sv3.py -q -p no:cacheprovider
45 passed in 6.82s
```

## Mutación

`python -m harness.mutacion --feature F-029 --workers 6 --timeout 600`,
salida real:

```
ALCANCE VACÍO en F-029: ni una línea de producción que mutar (origen rama, 179010ac87f74bb6eca63a0bf847a7e739ed38e6..feature/F-029-alias-logo-ruesma). No se ha juzgado NADA.
F-029: 0 fichero(s), 0 línea(s) de producción (origen rama, ...)
```

Esperado: F-029 no cambia Python de producción, solo el YAML. No hay
`progress/mutacion_F-029.md` (la herramienta no lo escribe con alcance vacío).

**Campaña manual sobre el YAML** (script en el momento: muta la tabla, corre
`tests/test_f029_alias_logo.py`, restaura; `git status` limpio al acabar):

| Mutante | Original -> mutado | Resultado | Lo caza |
|---|---|---|---|
| M1 | quitar `- RUΞSMA` | muerto (4 fallos) | logotipo ×3 + varias |
| M2 | `RUΞSMA` -> `RUSMA` | muerto (5 fallos) | logotipo ×3 + varias + control `Rusma Obras` |
| M3 | `RUΞSMA` movido a la 28 | muerto (4 fallos) | logotipo ×3 (salen 28) + varias |
| M4 | `RUΞSMA` -> `RU` | muerto (2 fallos) | controles `ru smart` y `ru obras sma` |
| M5 | `RUΞSMA` -> `SMA` | muerto (2 fallos) | controles `gru sma` y `ru obras sma` |
| M6 | quitar `- RUESMA` | muerto (2 fallos) | `RUESMA`, «Construcciones Ruesma S.A.» |
| M7 | `PORSAN` -> `OTRA` | muerto (2 fallos) | Porsan -> 28 y el caso varias |
| M8 | `RUΞSMA` -> `RU-SMA` | **sobrevive** | equivalente |

**Superviviente M8**: equivalente. `RU-SMA` normaliza exactamente a «ru sma»,
igual que `RUΞSMA`: el comportamiento del resolutor es idéntico para
cualquier texto. Ningún test puede distinguirlos; no es un hueco.

## Documentación

`docs/ARCHITECTURE.md` (l. 192), `docs/referencia/partes-proyecto.md`
(l. 404 y 759) y `azure-apps/partes.md` (l. 198) citan la ruta de la tabla,
no los alias: no se tocan (como pedía la tarea). No cambia nada de lo que sv3
expone o consume.

## Verificaciones MANUAL pendientes

- **M1** (tras desplegar sv3, lo pide el humano): el primer parte de Ruesma
  con el logotipo «ruΞsma» en el membrete sale con empresa 1 y origen
  `membrete` (en lugar de empresa desconocida `sin_alias` en el log
  `[empresa-membrete]`).

## Qué queda fuera

- Normalizar letras griegas a latinas en `text_match.normalize` (cambiaría el
  casado de nombres y obras en sv3 y sv4; descartado por el humano).
- Cualquier cambio en el prompt de sv2 para que transcriba «RUESMA».
- Despliegue de sv3 (lo pide el humano).

## Avisos no bloqueantes

- ruff pasa de 589 a 590 avisos: es un `I001` (orden de imports) del test
  nuevo, el mismo que ya tienen `test_f023_empresa_membrete.py` y
  `test_f023_wiring_sv3.py` al lanzar ruff desde la raíz del monorepo (no
  reconoce `application`/`domain` como primer partido). Se mantiene el patrón
  de imports del resto de tests de sv3 en vez de reordenarlo.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de F-029 | 12 (12 passed; antes del alias: 4 failed, 8 passed) |
| Suite de sv3 completa | **666 passed** en 13.15 s (`python -m pytest -q`), 24.20 s dentro de `init.sh` |
| Suite raíz del monorepo (`init.sh`) | 445 passed, 1 skipped en 179.55 s |
| Resto de servicios (`init.sh`) | sv1, sv2, sv4, sv5 en verde (caché: árbol sin cambios) |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: N/A (F-029 no cambia líneas Python de producción frente a dev)` |
| Mutantes (harness) | alcance vacío: 0 generados (salida arriba) |
| Mutantes (manual, YAML) | 8 generados, 7 muertos, 1 superviviente equivalente (M8) |

`bash harness/init.sh` final, con este informe ya escrito: **ENTORNO LISTO**.
Raíz 445 passed, 1 skipped (172.58 s); sv1-sv5 en verde; `PUERTA COBERTURA:
N/A`; `PUERTA TAMAÑO: F-029 dentro de los topes (impl 176/220)`; rama
`feature/F-029-alias-logo-ruesma`. Únicos avisos: F-014 `blocked`, deuda
ruff (590), infra sin tests (todos previos salvo el +1 de ruff explicado).
