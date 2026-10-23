<!-- progress/spec_F-058.md -->
# F-058 · spec_ready (2026-10-23): relectura de la cabecera vacía con Gemini en sv2

Spec en `specs/F-058-relectura-cabecera-gemini/` (rama `feature/F-058-relectura-cabecera-gemini`,
worktree `partes-wt-f058`, desde `dev` 38f273a). Rigor **estándar**. Tamaños: requirements
125/150, design ~249/250, tasks 16 tareas.

## Qué propone

- **Solo sv2.** Si la lectura primaria (`gpt-6.1-sol`) trae `obra_numero` y `fecha` vacíos
  (null o blancos) con al menos una fila de empleados, el pipeline relee el mismo adjunto
  **una vez** con `RELECTURA_CABECERA_PROVIDER` (`gemini`; modelo `GEMINI_MODEL`, en Azure
  `gemini-4-argon`) con el mismo prompt, esquema y catálogo auxhor, y toma su **cabecera
  entera** si trae obra o fecha. Firma y empleados siguen siendo de la primaria.
- Si la relectura falla o sale vacía, se queda la primaria (sin propagar el error) y F-054
  la manda a revisión.
- Traza solo cuando se dispara: `meta.relectura_cabecera` (`motivo`, `provider`, `model`,
  `resultado` aplicada|vacia|error, `error_tipo`) y `debug.relectura_cabecera`
  (`cabecera_primaria` + petición/respuesta). `meta.provider/model` siguen siendo del primario.
  Queda en `raw_extraction_json` sin migración. Logs sin nombres, DNIs, valores de cabecera
  ni mensaje de excepción.
- Interruptor `RELECTURA_CABECERA` (encendido por defecto). Gemini **ya está habilitado y con
  clave** en `ca-sv2-extraccion` (`ENABLE_GEMINI=true`, `GEMINI_MODEL=gemini-4-argon`,
  `GEMINI_API_KEY` por secretref; según `infra/create_capps_partes.ps1` y
  `azure-apps/partes.md`): **sin cambios de entorno**; M0 lo confirma en solo lectura.
- sv1, sv3, sv4, sv5, ORM y `prompts.yaml` no cambian. Se actualizan `ARCHITECTURE.md`,
  `azure-apps/partes.md` (sv2 consume Gemini en producción) y un comentario de
  `create_capps_partes.ps1`.

## Decisiones abiertas para el humano (`design.md` §10)

| DA | Tema | Recomendación |
|---|---|---|
| DA1 | Qué es «cabecera vacía» | B: obra y fecha vacías, con ≥ 1 fila |
| DA2 | Qué se relee | A: página entera, mismo prompt y esquema (lo medido) |
| DA3 | Qué se toma | A: la cabecera entera si trae obra o fecha |
| DA4 | Relectura falla o vacía | A: se queda la primaria; F-054 a revisión |
| DA5 | Configuración | A: encendida por defecto, sin cambios de entorno (B: apagada y la enciende el humano) |
| DA6 | Trazabilidad | A: `meta`/`debug` del envelope, sin columna |
| DA7 | Coste y latencia | A: aceptar (~7 k tokens y ~8 s solo cuando se dispara) |
| DA8 | Los 6 ya guardados | A: corrección a mano en el portal tras F-054 M2; B (reproceso) solo con autorización |

## Hallazgos del spec-author que conviene saber

- El `.venv` del arnés no tiene `openai`, `anthropic` ni `google-genai`: los tests de
  cableado importan `app.py` con módulos falsos en `sys.modules` (`design.md` §7).
- Medido en la batería del líder: la relectura cuesta ~6,5 k tokens de entrada y ~0,4–0,6 k
  de salida y tarda 7–11 s (una de 32 s); las filas de Gemini coinciden con las de
  `gpt-6.1-sol` en las 6 páginas.
- Reprocesar los 6 no basta con reenviar: sv3 descarta por `source_sha256` de un documento
  activo; por eso la alternativa B desactiva antes (`design.md` §9 M3).
- Sin F-054 desplegada, una relectura `vacia`/`error` sigue guardándose sin revisión.
