<!-- progress/spec_F-059.md -->
# spec-author · F-059 · La IA no lee bien el PDF con /Rotate: la página va ya derecha (2026-10-23)

Spec en `specs/F-059-pagina-como-imagen-derecha/` (rama
`feature/F-059-pagina-como-imagen-derecha` desde `dev` 2170f82, worktree
`C:\Users\pgris\PycharmProjects\partes-wt-f059`). Topes: requirements 148/150, design
248/250, tasks 11 tareas. `features.json`: F-059 `spec_ready`, prioridad 1, rigor
`estandar`; título y descripción reescritos con la precisión del humano (el fallo es de
lectura de la IA, no del escáner ni de sv1).

## Qué hace

- **Solo sv2.** El pipeline (`extract_parte_pipeline.py`) pide a un conversor (puerto
  `domain/ports/conversor_pagina.py`, adaptador `infrastructure/document/pagina_pdf_imagen.py`
  con pypdf + Pillow) la página derecha cuando el PDF es una sola imagen JPEG a página
  completa, y la manda como `kind="image"`. Si no aplica (motivo cerrado) o falla
  (WARNING con tipo de excepción y sha256[:12], sin nombre de fichero), va el PDF como hoy.
- `meta.adjunto_ia` traza lo enviado (`conversion`, `motivo`, `kind`, `mime_type`,
  `size_bytes`, giro y medidas); `meta.source_*` siguen siendo del original (dedup de sv3
  intacta). OpenAI manda `detail` en `input_image` (`OPENAI_IMAGE_DETAIL`, `high`).
- Dependencias nuevas en `infra/manifests/sv2/requirements.txt`: `pypdf>=4.2`, `Pillow>=10.0`
  (Dockerfile igual). El `.venv` raíz no tiene Pillow: lo instala T1.

## Hallazgos

1. Los 22 PDF del banco (6 sin cabecera, 2 de control, 14 de F-051) tienen la misma
   estructura: una página, contenido `q a 0 0 d 0 0 cm /Im0 Do Q`, JPEG DeviceRGB, sin
   CropBox propia, `/Rotate 270`. pypdf 6.19 devuelve con `get_data()` el JPEG íntegro.
2. El JPEG recodificado a calidad 90 pesa 0,65–1,1 MB (originales 0,35–0,44 MB).
3. El banco ponía `detail` parcheando la petición (`BENCH_DETAIL`); el cliente de sv2 no lo
   manda hoy: por eso DA4.
4. Los clientes de Gemini y Claude ya mandan las imágenes por su vía: no se tocan.
5. Pillow guarda un RGB como PDF con un único `DCTDecode` a página completa: los tests
   fabrican sus PDF con Pillow + pypdf, sin datos reales.

## Decisiones abiertas para el humano (`design.md` §7)

- **DA1** proveedores: A) solo OpenAI por defecto, lista configurable (recomendada).
- **DA2** conversión: A) imagen incrustada, sin render; resto como PDF (recomendada).
- **DA3** interruptor: A) encendido por defecto, sin cambio de entorno en Azure (recomendada).
- **DA4** `detail`: A) `high` para toda imagen, también fotos del móvil (recomendada).

Verificación manual: M0–M3 en el banco del líder antes de desplegar; M4 del humano tras
`redeploy_partes.ps1 -Solo sv2`. `bash harness/init.sh` en verde el 2026-10-23 (ENTORNO
LISTO; puerta de tamaño 148/150 y 248/250).
