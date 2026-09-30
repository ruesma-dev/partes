<!-- progress/mutacion_F-020.md -->
# F-020 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-020` el 2026-09-30 13:43.

## Alcance

Origen del diff: **rama** (`566286ded60b809e141ff909de237c7265e3a5b1` .. `feature/F-020-correo-adjunto-escaner`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-email/application/pipelines/polling_pipeline.py` | 290 |
| `services/partes-email/domain/models/email_models.py` | 52 |
| `services/partes-email/domain/ports/extractor_correo_adjunto.py` | 36 |
| `services/partes-email/domain/ports/mailbox_client.py` | 8 |
| `services/partes-email/infrastructure/document/mime_pdf_extractor.py` | 205 |
| `services/partes-email/main.py` | 3 |
| **Total** | **594** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 76 |
| Mutantes evaluados | 20 |
| Muertos | 16 |
| Supervivientes | 4 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 271.1 s |
| SHA de HEAD medido | `739f5b72c9ae84dd4cec24fb7f777200bb88e17c` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-020_rb0hl8kb/wk_0/services/partes-email` | 63.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-020_rb0hl8kb/wk_1/services/partes-email` | 63.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-020_rb0hl8kb/wk_2/services/partes-email` | 61.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-020_rb0hl8kb/wk_3/services/partes-email` | 65.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-020_rb0hl8kb/wk_4/services/partes-email` | 61.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-020_rb0hl8kb/wk_5/services/partes-email` | 62.7 |
| Media por mutante evaluado (s) | 13.6 |
| Timeout efectivo por mutante (s) | 600 — fijado a mano con `--timeout`, sin derivar |
| Suelo configurado (s) | 600 |
| Workers | 6 |
| Muestreo | sí — 20 de 76 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-email/application/pipelines/polling_pipeline.py:306` [booleano]

- Original: `return _ResultadoAdjunto(ok=False, documentos=0)`
- Mutado:   `return _ResultadoAdjunto(ok=True, documentos=0)`

#### Análisis

> Por qué ningún test lo caza: ningún test hacía fallar la descarga de un
> PDF DIRECTO mientras otro adjunto sí ingería documentos; con un solo
> adjunto, `documentos=0` ya manda el correo a `Errores` por R20(c).
> Decisión: **hueco real → test nuevo**
> `test_f020_r20_fallo_de_descarga_de_pdf_directo_va_a_errores`. Mutante
> reaplicado a mano: MUERTO.

### 2. `services/partes-email/application/pipelines/polling_pipeline.py:363` [entero]

- Original: `return _ResultadoAdjunto(ok=False, documentos=0)`
- Mutado:   `return _ResultadoAdjunto(ok=False, documentos=1)`

#### Análisis

> Por qué ningún test lo caza: con `ok=False` el correo va a `Errores`
> sea cual sea `documentos` (R20: `all(ok) and sum >= 1`). El único
> efecto observable es el recuento del log final `documentos=%d`.
> Decisión: **equivalente respecto al contrato** (destino y lo encolado
> no cambian). No se añade un test que fije el texto de un log.

### 3. `services/partes-email/application/pipelines/polling_pipeline.py:618` [comparacion]

- Original: `if max_bytes > 0 and att.size > max_bytes:`
- Mutado:   `if max_bytes >= 0 and att.size > max_bytes:`

#### Análisis

> Por qué ningún test lo caza: ningún test usaba `MAX_ATTACHMENT_MB=0`,
> que en sv1 significa «sin límite» (misma guarda en `_is_eligible`).
> Decisión: **hueco real → test nuevo**
> `test_f020_r4_limite_cero_significa_sin_limite`. Mutante reaplicado a
> mano: MUERTO.

### 4. `services/partes-email/infrastructure/document/mime_pdf_extractor.py:149` [logico]

- Original: `if isinstance(contenido, list) and contenido:`
- Mutado:   `if isinstance(contenido, list) or contenido:`

#### Análisis

> Por qué ningún test lo caza: el caso «sin mensaje dentro» del test
> existente tenía payload `None`, no una lista vacía; con `or`, una lista
> vacía llega a `contenido[0]` → `IndexError` → todo el correo adjunto
> ilegible en vez de ignorar esa parte.
> Decisión: **hueco real → test nuevo**
> `test_f020_r7_rfc822_con_lista_de_mensajes_vacia_se_ignora`. Mutante
> reaplicado a mano: MUERTO.


## Nota

La campaña NO se relanza tras los tres tests nuevos (rigor `estandar`:
supervivientes analizados, no cero). Cada mutante se reaplicó a mano con
su test nuevo y los tres mueren.
