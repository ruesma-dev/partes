<!-- progress/impl_F-059.md -->
# F-059 · La IA no lee bien el PDF con /Rotate: sv2 le manda la página ya derecha — informe del implementer

Rama `feature/F-059-pagina-como-imagen-derecha` (worktree `partes-wt-f059`), rigor `estandar`,
solo sv2. Aprobación del humano (2026-10-23), literal: a «¿A en las cuatro? Si me dices que sí,
lanzo el implementer» respondió «a» ⇒ DA1–DA4 = A, anotado en `design.md` §7 y en
`progress/current.md`.

**Estado: T1–T9 y T11 hechas; pasada 1 del reviewer (CHANGES_REQUESTED, C4) corregida: M4 con
comando exacto y observación 1 aplicada. Pendientes: T10 (M4 tras desplegar, humano), pasada 2.**

## Qué cambió

| Fichero | Cambio |
|---|---|
| `infra/manifests/sv2/requirements.txt` | `pypdf>=4.2` y `Pillow>=10.0` (R24) |
| `services/partes-api/domain/models/conversion_adjunto.py` (nuevo) | `ResultadoConversion`, valores de `conversion` y motivos cerrados |
| `services/partes-api/domain/ports/conversor_pagina.py` (nuevo) | puerto `ConversorPaginaImagen` |
| `services/partes-api/infrastructure/document/pagina_pdf_imagen.py` (nuevo) | `PaginaPdfImagenConversor`: algoritmo de `design.md` §5, pasos 1–7 (R1–R10) |
| `services/partes-api/application/pipelines/extract_parte_pipeline.py` | kwargs `conversor` y `proveedores_imagen`; `_preparar_para_ia`, `_traza`; `meta.adjunto_ia`; `meta.source_*` del original (R11–R19) |
| `services/partes-api/config/settings.py` | `PAGINA_COMO_IMAGEN` (true), `PAGINA_COMO_IMAGEN_PROVEEDORES` (`openai`), propiedad `proveedores_pagina_como_imagen`, validación de nombres, `OPENAI_IMAGE_DETAIL` (`high`) (R20, R21) |
| `services/partes-api/infrastructure/llm/openai_responses_client.py` | parámetro `image_detail`; `detail` solo en `input_image` y solo si hay valor (R22) |
| `services/partes-api/interface_adapters/api/app.py` | crea el conversor si el interruptor está encendido, pasa la lista y `image_detail`; log de wiring |
| `services/partes-api/tests/f059_pdf_sinteticos.py` (nuevo) | fábrica de PDF sintéticos (Pillow + pypdf, sin datos reales) |
| `services/partes-api/tests/f059_sdk_falsos.py` (nuevo) | dobles de `openai`/`anthropic`/`google.genai`, solo si el SDK real falta (ver desviación 2) |
| `services/partes-api/tests/test_f059_conversor.py` (nuevo) | 72 tests, R1–R10 y el lado del conversor de R13 (2 de T8) |
| `services/partes-api/tests/test_f059_pipeline.py` (nuevo) | 22 tests, R11–R19 y uno de extremo a extremo con el conversor real |
| `services/partes-api/tests/test_f059_config.py` (nuevo) | 22 tests, R20–R22, R24, el cableado de `build_app` y su INFO (2 de T8) |
| `docs/ARCHITECTURE.md` | semántica 19 |
| `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` | §3.2 (qué recibe la IA) y fila de sv2 de §5.6 (variables, dependencias); commit local **7cc2e66** en `master` de azure-apps, sin push |
| `harness/features.json`, `BACKLOG.md`, `progress/current.md`, `design.md` §7, `tasks.md` | `in_progress`, aprobación, tareas marcadas |

Commits (rama): aprobación df11667, T1 1d47909, T2 d58367c, T3 41c68fc, T4 5501447, T5 7bda70a,
T6 5ddacbf, T7 fd90dab, ajustes de ruff d1f3836. No tocados (R23): clientes de Gemini y Claude,
`prompts.yaml`, `parte_models.py`, `llm_attachment.py`, `parte_extraction_service.py`,
`main_worker.py`, sv1, sv3–sv5.

## Decisiones de diseño

- **Orden de `_preparar_para_ia`** = tabla de `design.md` §6: sin conversor ⇒ `apagada` /
  `interruptor`; proveedor fuera de la lista ⇒ `apagada` / `proveedor_fuera_de_lista`; `kind`
  imagen ⇒ `no_aplica` / `no_es_pdf`; luego el conversor. Las fotos con la conversión apagada
  llevan `apagada` (la conversión ni se plantea); con ella activa, `no_es_pdf`.
- **WARNING de R13** sin `exc_info` ni el mensaje de la excepción (podría llevar contenido del
  documento): solo `type(exc).__name__` y `sha256[:12]`. `except Exception` con `noqa: BLE001`
  justificado (R13: la conversión nunca tumba la extracción).
- **R17**: `_traza` describe el adjunto *enviado* sin `filename`; `convertida` añade giro y
  medidas. `meta.source_*` y `source_sha256` salen del original (R16). `debug` no cambia de
  forma: `_attachment_debug` recibe ya el adjunto enviado (R18).
- **Conversor**: el filtro admite nombre o lista de uno; `/Decode`, `/SMask`, `/Mask`, bits ≠ 8
  o `/Subtype` ≠ `/Image` ⇒ `imagen_no_jpeg`; espacio de color fuera de RGB/grises ⇒
  `color_no_soportado` (en ese orden, como §5 paso 3). CropBox = MediaBox comparadas exactas;
  `a`, `d`, `e`, `f` con ±1 pt; proporción con ≤ 2 %. El nombre del JPEG es `<stem>.jpg`
  (`pagina.jpg` si no hay nombre). Con giro 0 no se llama a `rotate`.
- **`OPENAI_IMAGE_DETAIL`**: el defecto `high` vive en `settings`; el cliente sin parámetro no
  manda `detail` (constructores de antes intactos). Vacío ⇒ sin `detail`.
- **Validación de la lista** en un `model_validator` propio: `ValueError` (pydantic lo envuelve
  en `ValidationError`, subclase de `ValueError`) que nombra los desconocidos; nombres en
  minúsculas y sin espacios; vacío ⇒ ninguno.

## Desviaciones respecto a la spec (justificadas)

1. **Interruptor apagado ⇒ `app.py` no crea el conversor** (además de pasar `frozenset()`, que es
   lo que dice §4 bis). Sin esto la traza diría `proveedor_fuera_de_lista` cuando el motivo real
   es el interruptor, y la tabla de §6 distingue los dos. Comportamiento idéntico (no se llama al
   conversor, R14).
2. **Dobles de los SDK de IA en los tests.** El `.venv` de la raíz (el que usa `init.sh` para sv2)
   no tiene `openai`, `anthropic` ni `google-genai`; la spec (§3) solo contaba con que faltaba
   Pillow. Sin ellos no se puede importar `openai_responses_client.py` ni `app.py`, y R22 y el
   cableado quedarían sin test. `tests/f059_sdk_falsos.py` registra un módulo falso **solo si el
   real no se puede importar** (con el SDK instalado no hace nada); los clientes solo tocan el
   SDK al construirse y al llamar, y los tests no llaman. **No se instaló nada salvo Pillow.** Si
   el líder prefiere instalar los SDK en el `.venv`, los dobles dejan de activarse solos.
3. ruff reordenó (I001) las importaciones de `pagina_pdf_imagen.py` y de los tests nuevos
   (incluido en el commit de T6) y d1f3836 cambia `Dict`/`Tuple` por `dict`/`tuple` en lo nuevo.
   Los ficheros nuevos quedan sin avisos; en los tocados, los mismos avisos que en `dev`.

## Fase RED (trazas reales)

**T2** — `cd services/partes-api && python -m pytest tests/test_f059_conversor.py` (sin el módulo):

```
collected 0 items / 1 error
________________ ERROR collecting tests/test_f059_conversor.py ________________
tests\test_f059_conversor.py:22: in <module>
    from domain.models.conversion_adjunto import (
E   ModuleNotFoundError: No module named 'domain.models.conversion_adjunto'
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
============================== 1 error in 0.45s ===============================
exit=2
```

**T3, RED de comportamiento** — mismo comando con `-q --tb=line`, con modelo y puerto ya creados
y el adaptador como esqueleto (`convertir` lanza `NotImplementedError`):

```
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF...   [100%]
E   NotImplementedError
C:\...\infrastructure\document\pagina_pdf_imagen.py:14: NotImplementedError
FAILED tests/test_f059_conversor.py::test_f059_r9_dentro_de_las_tolerancias_si_aplica[tolerancia-1pt]
FAILED tests/test_f059_conversor.py::test_f059_r10_giro_que_no_es_multiplo_de_90[45]
...
67 failed, 3 passed in 0.80s
```

Los 3 que pasan son los de R13 del conversor («lanza»): `NotImplementedError` también es una
excepción; después se afinaron a `PdfReadError`, `OSError` («truncated») y
`UnidentifiedImageError`. Tras el adaptador real: **1 fallo de test** (`proporcion-1.96pc-ancha`:
306/200 da exactamente el 2,0 % y por coma flotante quedaba fuera; era el test, se cambió a
305 px), luego `70 passed in 0.66s`.

**T4** — `python -m pytest tests/test_f059_pipeline.py -q --tb=line` (pipeline sin tocar):

```
E   TypeError: ExtractPartePipeline.__init__() got an unexpected keyword argument 'conversor'
C:\...\tests\test_f059_pipeline.py:97: TypeError: ...unexpected keyword argument 'conversor'
E   KeyError: 'adjunto_ia'
C:\...\tests\test_f059_pipeline.py:207: KeyError: 'adjunto_ia'
FAILED tests/test_f059_pipeline.py::test_f059_r11_activa_el_cliente_recibe_la_imagen
FAILED tests/test_f059_pipeline.py::test_f059_r13_fallo_manda_el_pdf_con_warning_sin_datos[ValueError]
FAILED tests/test_f059_pipeline.py::test_f059_r14_los_constructores_de_antes_siguen_valiendo
...
22 failed in 1.32s
```

(el de los constructores de antes falla por `KeyError: 'adjunto_ia'`: el pipeline viejo no deja
la traza). Tras T5: `python -m pytest tests/test_f059_pipeline.py tests/test_f023_empresa_membrete.py
tests/test_f051_esquema.py tests/test_f051_prompt.py -q` ⇒ `54 passed in 1.30s`.

**T6** — `python -m pytest tests/test_f059_config.py -q --tb=line` (con los dobles de SDK, sin
settings ni cliente nuevos). Primer intento sin dobles: `ModuleNotFoundError: No module named
'openai'` en la recogida (origen de la desviación 2). Con ellos:

```
E   TypeError: OpenAiResponsesVisionClient.__init__() got an unexpected keyword argument 'image_detail'
E   AttributeError: 'Settings' object has no attribute 'proveedores_pagina_como_imagen'
E   Failed: DID NOT RAISE ValueError
E   assert False
     +  where False = isinstance(None, PaginaPdfImagenConversor)
FAILED tests/test_f059_config.py::test_f059_r20_por_defecto_encendido_y_solo_openai
FAILED tests/test_f059_config.py::test_f059_r21_un_nombre_desconocido_tumba_el_arranque[mistral]
FAILED tests/test_f059_config.py::test_f059_r22_la_imagen_lleva_detail[high]
FAILED tests/test_f059_config.py::test_f059_r20_app_cablea_el_conversor_encendido
...
18 failed, 2 passed in 1.41s
```

Los 2 que pasan: R24 (T1 ya había añadido las dependencias) y «por defecto el cliente no manda
`detail`» (es lo de hoy, test de no regresión). Tras T6: `cd services/partes-api && python -m
pytest` ⇒ `144 passed in 2.25s`.

## Verificaciones hechas (resultado real)

- `python -c "import PIL, pypdf"` ⇒ Pillow 13.0.0, pypdf 6.19.0 (T1).
  `git diff dev -- infra/manifests/sv2/requirements.txt` ⇒ solo `+pypdf>=4.2` y `+Pillow>=10.0`.
- Prueba de humo (fuera de la suite, sintética, sin datos reales): página de 3507 × 2480 px a
  300 ppp (MediaBox 841,68 × 595,2, `cm 841.68 0 0 595.2 0 0`) con `/Rotate 270` ⇒
  `convertida`, giro 270, 2480 × 3507, 137 KB (blanca), 0,09 s.
- `python -m harness.tamano --feature F-059` ⇒ dentro de los topes (requirements 148/150,
  design 250/250, tras la pasada 1).
- `bash harness/init.sh` ⇒ **ENTORNO LISTO** (detalle en «Evidencias»).

## Verificaciones MANUAL pendientes (no son de esta tanda)

- **T9 (líder)**: M0–M3 en el banco con el código de la rama (`design.md` §9). Si no se cumplen,
  `blocked`.
- **T10 · M4 (humano)**: desplegar sv2 con `.\infra\redeploy_partes.ps1 -Solo sv2` (lo lanza el
  humano; con DA3 = A no hay cambio de entorno), anotar el instante UTC del despliegue y, en la
  base `partes`, solo lectura (`raw_extraction_json` es `Text` ⇒ `::jsonb`; `created_at_utc` es
  varchar ISO ⇒ se compara con una cadena ISO):
  `SELECT id, created_at_utc, raw_extraction_json::jsonb #>> '{meta,adjunto_ia,conversion}' AS
  conversion, raw_extraction_json::jsonb #>> '{meta,adjunto_ia,motivo}' AS motivo FROM
  parte_documents WHERE created_at_utc >= '<instante del despliegue, ISO UTC>' ORDER BY
  created_at_utc DESC LIMIT 20;` ⇒ páginas escaneadas `convertida`, **ningún `error`**. Vuelta
  atrás: `az containerapp update -n ca-sv2-extraccion -g rg-partes-dev --set-env-vars
  PAGINA_COMO_IMAGEN=false`.

## T8 · mutación (la lanzó el líder) y supervivientes

`python -m harness.mutacion --feature F-059` (nivel `estandar`, muestreo 20 de 49, semilla
20260820) ⇒ **20 evaluados, 17 muertos, 3 supervivientes, 0 timeouts**, 42,2 s. Análisis
completo en `progress/mutacion_F-059.md`; resumen:

| Mutante | Veredicto | Qué se hizo |
|---|---|---|
| [16] `pagina_pdf_imagen.py:146` `>` → `>=` | hueco real (nadie probaba el borde exacto de 1 pt) | 2 casos nuevos en `..._dentro_de_las_tolerancias_si_aplica`: `301 0 0 200 0 0` y `300 0 0 199 -1 1` |
| [19] `pagina_pdf_imagen.py:149` `<=` → `<` | **equivalente**: `abs(q-1)` es múltiplo de 2^-53 (Sterbenz) y el double 0.02 = impar/2^58 | sin test; demostración y ejemplo en el informe de mutación |
| [20] `app.py:144` `or` → `and` | hueco real (INFO de wiring, evidencia de DA3/T10) | 2 tests `caplog` en `test_f059_config.py` (encendido ⇒ `['openai']`, apagado ⇒ `(ninguno)`) |

Mutantes [16] y [20] aplicados a mano: `2 failed, 5 passed` (tolerancias) y `2 failed`
(wiring); revertidos, en verde. Sin cambios de código de producción. Campaña no relanzada.

**Observación 1 de la pasada 1**: `sha256[:12]` → `[:13]` (`extract_parte_pipeline.py:116`, fuera
de la muestra) sobrevivía porque R12/R13 buscaban el sha12 como subcadena; ahora fijan el final
(`f"sha256={SHA_PDF[:12]}:"`). Mutante aplicado a mano en `services/partes-api` (revertido con
`git checkout` ⇒ `python -m pytest -q`: 148 passed in 1.71s; caen R12 y las 4 de R13):
```
$ python -m pytest tests/test_f059_pipeline.py -q   # con sha256[:13]
FAILED tests/test_f059_pipeline.py::test_f059_r12_no_aplica_manda_el_pdf_byte_a_byte_e_info
FAILED tests/test_f059_pipeline.py::test_f059_r13_fallo_manda_el_pdf_con_warning_sin_datos[ValueError]
5 failed, 17 passed in 1.11s
```

## Fuera de alcance

Corte del escáner y sv1; render de PDF que no son página escaneada (DA2); EXIF de fotos del móvil
(F-026); `reasoning.effort`; `GEMINI_MEDIA_RESOLUTION`; F-058. Documentar en la sección «Acceso a
datos» de `ARCHITECTURE.md` que el proveedor de producción es OpenAI (dice Gemini) no es de F-059.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests de sv2 | **148 passed** (32 previos + 116 nuevos: 72 conversor, 22 pipeline, 22 config), 0 fallos, 2,13 s |
| Suite de la raíz (`init.sh`) | 498 passed, 3 skipped; sv1, sv3, sv4, sv5 en verde (caché) |
| Cobertura de líneas cambiadas | **99,4 %** (164/165, umbral 80 %); la única sin cubrir es el `raise NotImplementedError` del método abstracto del puerto (`conversor_pagina.py:16`) |
| Cobertura por fichero nuevo | `pagina_pdf_imagen.py` 100 %, `conversion_adjunto.py` 100 % |
| Mutantes generados / supervivientes | 49 generados, 20 evaluados: 17 muertos, 3 supervivientes (2 huecos cerrados con 4 tests, 1 equivalente demostrado), 0 timeouts; campaña lanzada con **4 workers** (42,2 s). Fuera de la muestra, `sha256[:13]` muere desde la pasada 1 (5 failed) |
| Tiempo de la suite de sv2 | 2,13 s sola; 21,1 s dentro de `init.sh` (bajo `coverage`); suite de la raíz 69,1 s (tras T8) |
| `bash harness/init.sh` | **ENTORNO LISTO**; PUERTA COBERTURA 99,4 %; PUERTA TAMAÑO en verde (impl 220/220, design 250/250; tras la pasada 1, 2026-10-23); ruff 772 avisos, los mismos que en `dev` (los ficheros nuevos, sin avisos) |
