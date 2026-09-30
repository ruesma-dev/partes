<!-- progress/impl_F-020.md -->
# F-020 · Informe del implementer

Rama `feature/F-020-correo-adjunto-escaner`. Rigor **estandar**. Spec aprobada
por el humano el 2026-09-30 con D1–D4 según la propuesta de design §9.
**Solo sv1** (`services/partes-email/`) más `docs/ARCHITECTURE.md`; nada de
sv2–sv5, `infra/`, `harness/servicios.json` ni `azure-apps/`. Sin red, sin
buzón, sin despliegue, sin push.

## Qué cambió

sv1 abre ahora los **correos adjuntos** (`message/rfc822`, sea item o
fileAttachment, D4), recorre su MIME hasta 5 niveles e ingiere cada PDF
interior por el mismo camino que un PDF directo, con la cadena de correos en
la clave nueva `embedded_in` del contexto.

| Fichero (bajo `services/partes-email/`) | Cambio |
|---|---|
| `domain/models/email_models.py` | + `CorreoEmbebido` (`to_context()`), `PdfEmbebido`, `ExtraccionCorreoAdjunto` |
| `domain/ports/extractor_correo_adjunto.py` | NUEVO: `ExtractorCorreoAdjunto` (Protocol) + `CorreoAdjuntoIlegible` |
| `domain/ports/mailbox_client.py` | Solo docstring de `download_attachment_value` |
| `infrastructure/document/mime_pdf_extractor.py` | NUEVO: `MimePdfExtractor`, recursión propia, `NIVEL_MAXIMO_ANIDAMIENTO = 5` |
| `application/pipelines/polling_pipeline.py` | Clasificación en una pasada, `_process_correo_adjunto`, `_ingerir_pdf`, `_ResultadoAdjunto`, contexto con `embedded_in`, destino R20 |
| `main.py` | Inyecta `extractor_correo=MimePdfExtractor()` (R25) |
| `tests/` | NUEVA primera suite de sv1: `conftest.py`, `eml_sinteticos.py`, `dobles.py` y 5 `test_f020_*.py` |
| `docs/ARCHITECTURE.md` (raíz) | Subsección «Ingesta de sv1: correos adjuntos (F-020)», 7 líneas |

Entorno (D1, autorizado): `pypdf` 6.19.0 instalado en el `.venv` de la raíz.
No cambia ningún fichero del repositorio (ya estaba en `requirements.txt`).

## Commits (locales)

```
5c70be2 F-020 T1: andamiaje de la primera suite de sv1
bfb9282 F-020 T2: modelos de dominio del correo adjunto y puerto
9164bcb F-020 T3: tests del extractor MIME (R7-R13) en rojo
9981cbb F-020 T4: MimePdfExtractor, recorrido MIME recursivo con tope de 5 niveles
cd83b7d F-020 T5: test de no regresion del contexto de PDF directo (R18)
171e7d7 F-020 T6: tests de clasificacion y de pipeline en rojo
a654df3 F-020 T7: el pipeline abre los correos adjuntos, embedded_in y R20
acd8b6e F-020 T8: main.py inyecta MimePdfExtractor (R25)
ff07408 F-020 T9: subseccion de ARCHITECTURE
739f5b7 F-020: anotaciones X | None y ClassVar (avisos de ruff)
21a6050 F-020 T10: campana de mutacion y tres tests que cierran huecos reales
5cb556a F-020 T11: verificacion MANUAL anotada en progress/current.md
cdf25ae F-020: quita del extractor una rama except inalcanzable
(+ el commit de T12 con este informe)
```

## Decisiones de diseño y desviaciones respecto a la spec

1. **Desviación pequeña: `nivel_maximo` en el puerto.** R10 exige que el log
   ERROR lleve el tope, pero el pipeline no puede importar la constante de
   infraestructura (DA2) y `ExtraccionCorreoAdjunto` no la trae (design §6.1).
   Añadí al Protocol una propiedad de solo lectura `nivel_maximo` que
   `MimePdfExtractor` expone. Ni cambia la firma de `extraer` ni los campos de
   los modelos.
2. **Clasificación sin logs duplicados.** El bucle es: `_es_correo_adjunto`
   (R1, R2, R4) → si el tipo es `message/rfc822` pero se descartó, `continue`
   (ya registrado) → si no, `_is_eligible` (ficheros). `_is_eligible` ahora
   registra con INFO los `itemAttachment`/`referenceAttachment` que descarta
   (R2/R3 piden INFO; antes callaba). Los PDF directos no cambian (R18).
3. **Límite 0 = sin límite** también para correos adjuntos y PDF interiores,
   igual que la guarda existente de `_is_eligible` (`max_bytes > 0 and …`).
4. **Cabeceras (R12).** Con `email.policy.default`, una `Date` que no se puede
   interpretar se lee como cadena vacía; se trata como ilegible → `null`. Una
   `Date` válida sale sin comentarios (`(hora de Madrid)` se pierde): es la
   lectura del parser, no se normaliza nada más. Cabecera vacía → `null`.
   `attachment_name` también se trunca a 200.
5. **R9, log DEBUG en el extractor.** Uso `logging` (stdlib) solo para el tipo
   y el nivel de la parte ignorada; ni bytes ni cabeceras (R24). El test de
   R13 admite stdlib salvo red/disco (`socket`, `http`, `urllib`, `os`, `io`…).
6. **Ilegible.** Bytes vacíos, excepción del parser **o del recorrido** ⇒
   `CorreoAdjuntoIlegible` con solo el tipo de la excepción en el mensaje.
7. **Orden de `documento_<n>.pdf`**: `n` cuenta los PDF de todo el correo
   adjunto (todos los niveles), no solo los del mensaje que lo contiene.

## Resultado de los tests

- Suite de sv1: **74 passed** (`cd services/partes-email && ../../.venv/Scripts/python.exe -m pytest -q` → `74 passed in 2.60s`).
- `bash harness/init.sh`: **ENTORNO LISTO**, con la línea exigida por R26:
  `[OK] servicio sv1-email (services/partes-email): pytest en verde`
  (`74 passed in 43.08s` con cobertura). Raíz: `402 passed, 1 skipped`.
  `PUERTA COBERTURA: 99.0% de 202 líneas cambiadas cubiertas (200/202)`.
  Salida de la ejecución final al pie de este informe.
- Ruff: el código nuevo solo deja `BLE001` (`except Exception` deliberados:
  lectura defensiva de cabeceras R12 y descarga de Graph, mismo patrón que la
  existente) y un `FLY002` en un test. El total del repo pasa de 496 a 502
  avisos (no bloquea).

| Fichero de test | Requisitos | Tests |
|---|---|---|
| `test_f020_extractor_mime.py` | R7–R13, R17 (`to_context`), R22 (ilegible) | 32 |
| `test_f020_clasificacion_adjuntos.py` | R1–R5 | 18 |
| `test_f020_pipeline_correo_adjunto.py` | R6, R14–R17, R19–R24, R25 (lado pipeline) | 20 |
| `test_f020_contexto_pdf_directo.py` | R18 (dict literal del formato previo, escrito en T5 sobre el pipeline SIN tocar) | 2 |
| `test_f020_wiring_main.py` | R25 | 2 |

## Fase RED (trazas reales)

**R10** — T3, antes de existir el extractor:
`cd services/partes-email && ../../.venv/Scripts/python.exe -m pytest tests/test_f020_extractor_mime.py -q -k r10 --tb=line`
```
E   ModuleNotFoundError: No module named 'infrastructure.document.mime_pdf_extractor'
ERROR tests/test_f020_extractor_mime.py::test_f020_r10_pdf_en_nivel_5_se_extrae
ERROR tests/test_f020_extractor_mime.py::test_f020_r10_nivel_6_marca_tope_excedido
ERROR tests/test_f020_extractor_mime.py::test_f020_r10_tope_excedido_aunque_haya_pdf_en_niveles_bajos
ERROR tests/test_f020_extractor_mime.py::test_f020_r10_constante_del_tope_es_5
ERROR tests/test_f020_extractor_mime.py::test_f020_r10_tope_configurable_en_el_constructor
23 deselected, 5 errors in 0.38s
```
Tras T4: `31 passed in 0.71s` (el fichero entero).

**R1** — T6, con el pipeline aún sin tocar:
`../../.venv/Scripts/python.exe -m pytest "tests/test_f020_clasificacion_adjuntos.py::test_f020_r1_correo_adjunto_se_abre_e_ingiere_su_pdf" -q --tb=line`
```
WARNING  application.pipelines.polling_pipeline:polling_pipeline.py:197 msg=msg-1 sin adjuntos elegibles (total=1) -> Errores
...\tests\test_f020_clasificacion_adjuntos.py:63: AssertionError: assert [] == ['att-c']
FAILED ...test_f020_r1_correo_adjunto_se_abre_e_ingiere_su_pdf[message/rfc822-itemAttachment]
FAILED ...[message/rfc822-fileAttachment]  FAILED ...[message/rfc822-sin_odata]
FAILED ...[Message/RFC822-itemAttachment]  FAILED ...[Message/RFC822-fileAttachment]
FAILED ...[Message/RFC822-sin_odata]
6 failed in 0.33s
```

**R17 y R20** — T6:
`../../.venv/Scripts/python.exe -m pytest tests/test_f020_pipeline_correo_adjunto.py -k "r17 or r20" -q --tb=line`
```
test_f020_pipeline_correo_adjunto.py:184: ValueError: not enough values to unpack (expected 2, got 0)
test_f020_pipeline_correo_adjunto.py:196: assert 0 == 2
test_f020_pipeline_correo_adjunto.py:226: AssertionError: assert [('msg-1', 'errores-id')] == [('msg-1', 'procesados-id')]
test_f020_pipeline_correo_adjunto.py:235: assert 0 == 1
test_f020_pipeline_correo_adjunto.py:248: assert False
test_f020_pipeline_correo_adjunto.py:263: AssertionError: assert [('msg-1', 'procesados-id')] == [('msg-1', 'errores-id')]
FAILED ...test_f020_r17_embedded_in_lleva_la_cadena_completa
FAILED ...test_f020_r17_embedded_in_en_cada_pagina_de_un_pdf_multipagina
FAILED ...test_f020_r20_todo_bien_con_documentos_va_a_procesados
FAILED ...test_f020_r20_fallo_de_ingesta_de_una_pagina_va_a_errores
FAILED ...test_f020_r20_pdf_interior_corrupto_va_a_errores
FAILED ...test_f020_r20_tope_excedido_no_ingiere_nada_y_va_a_errores
6 failed, 1 passed, 12 deselected in 0.35s
```
(El que pasa en rojo es `r20_sin_ningun_documento_ingerido_va_a_errores`: el
código viejo ya mandaba a `Errores` un correo sin nada elegible.) El de la
línea 263 muestra el hueco que cierra D3: el código viejo ingería el PDF
directo y mandaba a `Procesados` un correo con un correo adjunto sin abrir.
Tras T7: `69 passed in 1.23s` (suite entera de sv1 en ese momento).

**R25** — T8, antes de tocar `main.py`:
`KeyError: 'extractor_correo'` → `1 failed, 1 passed`; tras el cambio, verde.

## Verificaciones MANUAL pendientes (humano)

Anotada en `progress/current.md` (T11, design §10): tras
`redeploy_partes.ps1 -Solo sv1`, mover UNO de los cuatro correos del escáner
de `Errores` a la carpeta origen, marcarlo no leído y comprobar en
`ca-sv1-poller` las líneas `correo adjunto con 1 PDF interior(es)`,
`Documento logico INGERIDO` y `movido a Procesados`, y el parte en el portal.

## Fuera del alcance / qué falta

- Reprocesar los otros tres correos del escáner (manual, fuera de F-020).
- `.msg` binario y `winmail.dat` (DA4): siguen descartándose.
- Riesgo heredado (design §9): un nombre de PDF interior > 255 caracteres
  rompería el INSERT de sv3 (`source_attachment_filename`), igual que hoy
  con un PDF directo. No se mitiga aquí.
- Revisión (reviewer) y paso a `done`: no los hago yo.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados (sv1) | **74 passed**, 0 fallos (antes de F-020 sv1 no tenía suite) |
| Tests de la raíz | 402 passed, 1 skipped (sin cambios) |
| Cobertura de líneas cambiadas | **99.0 %** (200/202; umbral 80 %) — sin cubrir: la rama `except` de `_nombre_fichero` (cabecera de nombre de fichero ilegible), defensiva |
| Mutantes | **76 generados, 20 evaluados** (muestreo, semilla 20260820), **16 muertos, 4 supervivientes**, 0 timeouts, 271.1 s, `--workers 6 --timeout 600` |
| Supervivientes | 3 huecos reales → 3 tests nuevos (cada mutante reaplicado a mano: MUERTO); 1 equivalente respecto al contrato (solo cambia el recuento del log final). Análisis completo en `progress/mutacion_F-020.md`; campaña no relanzada (rigor estandar) |
| Tiempo de la suite de sv1 | 2.6 s sin cobertura; 43.1 s dentro de `init.sh` con cobertura (el grueso es importar `main` y los SDK de Azure) |

### Salida final de `bash harness/init.sh` (tras el último commit de código)

```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 502 avisos (deuda previa, no bloquea)
402 passed, 1 skipped in 63.53s (0:01:03)
[OK] pytest en verde (con medición de cobertura)
74 passed in 43.08s
[OK] servicio sv1-email (services/partes-email): pytest en verde
[AVISO] servicio sv2-extraccion (services/partes-api): sin directorio de tests
[OK] servicio sv3/sv4/sv5: pytest en verde (caché)
[OK] PUERTA COBERTURA: 99.0% de 202 líneas cambiadas cubiertas (200/202, umbral 80%, nivel estandar)
[OK] PUERTA TAMAÑO: F-020 dentro de los topes (requirements 143/150, design 250/250, impl 182/220)
[OK] Rama actual: feature/F-020-correo-adjunto-escaner
ENTORNO LISTO. Puedes trabajar.
```
